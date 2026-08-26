#
#  Copyright 2026 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import importlib.util
import sys
import types
import warnings
from types import SimpleNamespace

import pytest

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
)


def _install_stubs_if_unavailable():
    try:
        importlib.import_module("cv2")
    except Exception:
        stub = types.ModuleType("cv2")

        def _missing(*_args, **_kwargs):
            raise RuntimeError("cv2 runtime call is unavailable in this test environment")

        def _module_getattr(name):
            if name.isupper():
                return 0
            return _missing

        stub.__getattr__ = _module_getattr
        sys.modules.setdefault("cv2", stub)
    if "xgboost" not in sys.modules and importlib.util.find_spec("xgboost") is None:
        sys.modules["xgboost"] = types.ModuleType("xgboost")


_install_stubs_if_unavailable()

from api.db.services.document_version_service import DocumentVersionService, version_blob_key


class _FakeStorage:
    def __init__(self):
        self.written = {}

    def obj_exist(self, _bucket, _location):
        return False

    def put(self, bucket, location, blob, *_args):
        self.written[(bucket, location)] = blob

    def get(self, bucket, location):
        return self.written.get((bucket, location))


class _VersionRow(SimpleNamespace):
    def to_dict(self):
        return dict(self.__dict__)


def _make_doc(**overrides):
    doc = SimpleNamespace(
        id="doc-1",
        kb_id="kb-1",
        name="report.pdf",
        location="report.pdf",
        size=10,
        suffix="pdf",
        chunk_num=3,
        token_num=30,
        content_hash="hash-v1",
        current_version_number=1,
        create_time=1720000000,
        run="3",
        progress=1.0,
        progress_msg="done",
        process_duration=5.0,
        process_begin_at=None,
    )
    doc.__dict__.update(overrides)

    def to_dict():
        return dict(doc.__dict__)

    doc.to_dict = to_dict
    return doc


@pytest.fixture()
def version_store(monkeypatch):
    """In-memory double for the version table plus collaborator stubs."""
    state = SimpleNamespace(rows=[], recorded=[], updated_docs=[], storage=_FakeStorage())

    def fake_query(cls, cols=None, reverse=None, order_by=None, **kwargs):
        doc_id = kwargs.get("document_id")
        rows = [row for row in state.rows if row.document_id == doc_id]
        if reverse and order_by == "version_number":
            rows = sorted(rows, key=lambda row: row.version_number, reverse=True)
        return rows

    def fake_insert(cls, **kwargs):
        row = _VersionRow(id=kwargs.get("id", f"ver-{len(state.recorded) + 1}"), create_time=1720000100, **kwargs)
        state.rows.append(row)
        state.recorded.append(row)
        return row

    def fake_update_by_id(cls, pid, data):
        state.updated_docs.append((pid, data))

    monkeypatch.setattr(DocumentVersionService, "query", classmethod(fake_query))
    monkeypatch.setattr(DocumentVersionService, "insert", classmethod(fake_insert))
    monkeypatch.setattr(DocumentVersionService, "update_by_id", classmethod(fake_update_by_id))
    monkeypatch.setattr(DocumentVersionService, "get_or_none", classmethod(lambda cls, **kwargs: next((r for r in state.rows if all(getattr(r, k) == v for k, v in kwargs.items())), None)))
    from api.db.services import document_version_service

    monkeypatch.setattr(document_version_service.DocumentService, "update_by_id", classmethod(fake_update_by_id))
    monkeypatch.setattr(document_version_service.settings, "STORAGE_IMPL", state.storage)
    return state


def _kb():
    return SimpleNamespace(id="kb-1", tenant_id="tenant-1")


def _call_replace(*args):
    """Invoke replace_document_version bypassing @DB.connection_context()."""
    return DocumentVersionService.replace_document_version.__func__.__wrapped__(DocumentVersionService, *args)


@pytest.mark.p2
def test_version_blob_key_layout():
    assert version_blob_key("doc-1", 2, "report.pdf") == "versions/doc-1/v2/report.pdf"


@pytest.mark.p2
def test_next_version_number_counts_existing_rows(version_store):
    version_store.rows.append(_VersionRow(id="v9", document_id="doc-1", version_number=9))
    assert DocumentVersionService.next_version_number("doc-1") == 10
    assert DocumentVersionService.next_version_number("missing-doc") == 1


@pytest.mark.p2
def test_replace_records_new_version_and_repoints_location(version_store):
    doc = _make_doc()
    version_store.rows.append(_VersionRow(id="v1", document_id="doc-1", version_number=1, location="report.pdf"))
    new_blob = b"brand-new-bytes"

    updated, noop = _call_replace(_kb(), doc, new_blob, "user-1")

    assert noop is False
    expected_key = "versions/doc-1/v2/report.pdf"
    assert version_store.storage.written[("kb-1", expected_key)] == new_blob
    assert len(version_store.recorded) == 1
    recorded = version_store.recorded[0]
    assert recorded.version_number == 2
    assert recorded.location == expected_key
    assert recorded.created_by == "user-1"
    assert recorded.size == len(new_blob)
    # The document pointer moved to the new version and its parse state was reset.
    _, doc_updates = version_store.updated_docs[-1]
    assert doc_updates["location"] == expected_key
    assert doc_updates["current_version_number"] == 2
    assert doc_updates["content_hash"] == recorded.content_hash
    assert doc_updates["run"] == "0"
    assert doc_updates["progress"] == 0
    assert updated["location"] == expected_key


@pytest.mark.p2
def test_replace_preserves_old_blob_in_storage(version_store):
    """Spec requirement: previous version blob still present in storage."""
    doc = _make_doc(location="report.pdf")
    version_store.rows.append(_VersionRow(id="v1", document_id="doc-1", version_number=1, location="report.pdf"))
    old_blob = b"original-content"
    new_blob = b"replacement-content"
    # Pre-populate storage with the old blob at the old location
    version_store.storage.written[("kb-1", "report.pdf")] = old_blob

    _call_replace(_kb(), doc, new_blob, "user-1")

    # Old blob must still be retrievable at its original location
    assert version_store.storage.written[("kb-1", "report.pdf")] == old_blob
    # New blob is stored at the versioned key
    assert version_store.storage.written[("kb-1", "versions/doc-1/v2/report.pdf")] == new_blob


@pytest.mark.p2
def test_replace_with_identical_bytes_is_a_noop(version_store):
    import xxhash

    doc = _make_doc(content_hash=xxhash.xxh128(b"same").hexdigest())
    version_store.rows.append(_VersionRow(id="v1", document_id="doc-1", version_number=1, location="report.pdf"))

    updated, noop = _call_replace(_kb(), doc, b"same", "user-1")

    assert noop is True
    assert version_store.recorded == []
    assert version_store.storage.written == {}
    assert version_store.updated_docs == []
    assert updated["id"] == "doc-1"


@pytest.mark.p2
def test_replace_synthesizes_legacy_version_before_new_one(version_store):
    doc = _make_doc(content_hash="legacy-hash", size=42, current_version_number=None)

    updated, noop = _call_replace(_kb(), doc, b"new-content", "user-1")

    assert noop is False
    assert len(version_store.recorded) == 2
    legacy, fresh = version_store.recorded
    # The legacy bytes are captured exactly as they are before the pointer moves.
    assert legacy.version_number == 1
    assert legacy.location == "report.pdf"
    assert legacy.content_hash == "legacy-hash"
    assert legacy.size == 42
    assert fresh.version_number == 2
    assert fresh.location == "versions/doc-1/v2/report.pdf"
    assert updated["current_version_number"] == 2


@pytest.mark.p2
def test_replace_regenerates_thumbnail(version_store, monkeypatch):
    from api.db.services import document_version_service

    monkeypatch.setattr(document_version_service, "thumbnail_img", lambda _name, _blob: b"png-bytes")
    doc = _make_doc()

    _call_replace(_kb(), doc, b"new-content", "user-1")

    assert version_store.storage.written[("kb-1", "thumbnail_doc-1.png")] == b"png-bytes"
    _, doc_updates = version_store.updated_docs[-1]
    assert doc_updates["thumbnail"] == "thumbnail_doc-1.png"


@pytest.mark.p2
def test_ensure_current_version_recorded_is_idempotent(version_store):
    doc = _make_doc()

    DocumentVersionService.ensure_current_version_recorded(doc, "user-1")
    DocumentVersionService.ensure_current_version_recorded(doc, "user-1")

    assert len(version_store.recorded) == 1
    assert version_store.recorded[0].version_number == 1
    assert version_store.recorded[0].location == "report.pdf"


@pytest.mark.p2
def test_list_versions_orders_descending(version_store):
    for n in (1, 3, 2):
        version_store.rows.append(_VersionRow(id=f"v{n}", document_id="doc-1", version_number=n))
    version_store.rows.append(_VersionRow(id="vx", document_id="other-doc", version_number=7))

    versions = DocumentVersionService.list_versions("doc-1")

    assert [v["version_number"] for v in versions] == [3, 2, 1]


@pytest.mark.p2
def test_get_version_scopes_to_document(version_store):
    version_store.rows.append(_VersionRow(id="ver-a", document_id="doc-1", version_number=1))

    assert DocumentVersionService.get_version("doc-1", "ver-a") is not None
    assert DocumentVersionService.get_version("other-doc", "ver-a") is None
