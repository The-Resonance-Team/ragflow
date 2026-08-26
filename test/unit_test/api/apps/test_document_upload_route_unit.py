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
"""In-process unit tests for the dataset upload route's conflict contract.

The route module is loaded in isolation with stubbed collaborators, following
the same pattern as test/testcases/test_web_api/test_document_app/conftest.py
but without requiring a live backend.
"""

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]


class _DummyManager:
    def route(self, *_args, **_kwargs):
        def decorator(func):
            return func

        return decorator


class _AwaitableValue:
    def __init__(self, value):
        self._value = value

    def __await__(self):
        async def _coro():
            return self._value

        return _coro().__await__()


class _DummyFiles(dict):
    def getlist(self, key):
        value = self.get(key, [])
        if isinstance(value, list):
            return value
        return [value]


class _DummyRequest:
    def __init__(self, form=None, args=None, files=None):
        self._form = form or {}
        self._args = args or {}
        self._files = _DummyFiles(files or {})

    @property
    def form(self):
        return _AwaitableValue(self._form)

    @property
    def files(self):
        return _AwaitableValue(self._files)

    @property
    def args(self):
        return self._args


def _run(coro):
    return asyncio.run(coro)


def _load_document_api_module(monkeypatch):
    """Load api/apps/restful_apis/document_api.py with stubbed collaborators."""
    common_pkg = ModuleType("common")
    common_pkg.__path__ = [str(REPO_ROOT / "common")]
    monkeypatch.setitem(sys.modules, "common", common_pkg)

    deepdoc_pkg = ModuleType("deepdoc")
    deepdoc_parser_pkg = ModuleType("deepdoc.parser")
    deepdoc_parser_pkg.__path__ = []

    class _StubAny:
        def __init__(self, *args, **kwargs):
            pass

    deepdoc_parser_pkg.__getattr__ = lambda attr: _StubAny
    deepdoc_pkg.__getattr__ = lambda attr: _StubAny
    deepdoc_pkg.parser = deepdoc_parser_pkg

    def _make_permissive_module(name):
        mod = ModuleType(name)
        mod.__getattr__ = lambda attr: _StubAny
        return mod
    monkeypatch.setitem(sys.modules, "deepdoc", deepdoc_pkg)
    monkeypatch.setitem(sys.modules, "deepdoc.parser", deepdoc_parser_pkg)

    class _StubLoader:
        def create_module(self, spec):
            return _make_permissive_module(spec.name)

        def exec_module(self, module):
            pass

    class _DeepdocStubFinder:
        """Fabricate empty modules for any unimported deepdoc submodule."""

        def find_spec(self, fullname, path=None, target=None):
            if fullname == "deepdoc" or fullname.startswith("deepdoc."):
                return importlib.util.spec_from_loader(fullname, _StubLoader())
            return None

    monkeypatch.setattr(sys, "meta_path", [_DeepdocStubFinder(), *sys.meta_path])
    monkeypatch.setitem(sys.modules, "xgboost", ModuleType("xgboost"))

    stub_apps = ModuleType("api.apps")
    stub_apps.__path__ = [str(REPO_ROOT / "api" / "apps")]
    stub_apps.current_user = SimpleNamespace(id="user-1")

    def _identity_decorator(*_args, **_kwargs):
        def decorator(func):
            return func

        if _args and callable(_args[0]):
            return _args[0]
        return decorator

    stub_apps.login_required = _identity_decorator
    stub_apps.AUTH_JWT = {}
    stub_apps.AUTH_API = {}
    stub_apps.AUTH_BETA = {}
    monkeypatch.setitem(sys.modules, "api.apps", stub_apps)

    stub_apps_services = ModuleType("api.apps.services")
    stub_apps_services.__path__ = [str(REPO_ROOT / "api" / "apps" / "services")]
    monkeypatch.setitem(sys.modules, "api.apps.services", stub_apps_services)

    document_api_service_mod = ModuleType("api.apps.services.document_api_service")

    def _map_doc_keys(doc):
        payload = doc.to_dict() if hasattr(doc, "to_dict") else doc
        if isinstance(payload, dict) and "run" in payload:
            mapped = {"0": "UNSTART", "1": "RUNNING", "2": "CANCEL", "3": "DONE", "4": "FAIL"}.get(str(payload["run"]), "UNSTART")
            return {**payload, "run": mapped}
        return payload

    def _map_doc_keys_with_run_status(doc, run_status="0"):
        payload = doc if isinstance(doc, dict) else doc.to_dict()
        mapped = {"0": "UNSTART", "1": "RUNNING", "2": "CANCEL", "3": "DONE", "4": "FAIL"}.get(str(run_status), "UNSTART")
        return {**payload, "run": mapped}

    document_api_service_mod.validate_document_update_fields = lambda *_args, **_kwargs: (None, None)
    document_api_service_mod.map_doc_keys = _map_doc_keys
    document_api_service_mod.map_doc_keys_with_run_status = _map_doc_keys_with_run_status
    document_api_service_mod.update_document_name_only = lambda *_args, **_kwargs: None
    document_api_service_mod.update_chunk_method = lambda *_args, **_kwargs: None
    document_api_service_mod.update_document_status_only = lambda *_args, **_kwargs: None
    document_api_service_mod.reset_document_for_reparse = lambda *_args, **_kwargs: None
    monkeypatch.setitem(sys.modules, "api.apps.services.document_api_service", document_api_service_mod)

    # canvas_service drags in agent/* -> scholar/LLM tooling; not needed here.
    canvas_stub = ModuleType("api.db.services.canvas_service")
    canvas_stub.UserCanvasService = type("UserCanvasService", (), {})
    monkeypatch.setitem(sys.modules, "api.db.services.canvas_service", canvas_stub)

    module_path = REPO_ROOT / "api" / "apps" / "restful_apis" / "document_api.py"
    spec = importlib.util.spec_from_file_location("test_document_upload_route_unit", module_path)
    module = importlib.util.module_from_spec(spec)
    module.manager = _DummyManager()
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def document_api(monkeypatch):
    return _load_document_api_module(monkeypatch)


def _stub_dataset_access(document_api, monkeypatch, dataset_id="kb1"):
    kb = SimpleNamespace(id=dataset_id, tenant_id="tenant1", name="kb", parser_id="parser", pipeline_id=None, parser_config={})
    monkeypatch.setattr(document_api.KnowledgebaseService, "get_by_id", lambda _dataset_id: (True, kb))
    monkeypatch.setattr(document_api, "check_kb_team_permission", lambda *_args, **_kwargs: True)
    return kb


def _upload_request(files):
    file_entries = [SimpleNamespace(filename=name, read=lambda: b"x") for name in files]
    return _DummyRequest(form={}, args={}, files={"file": file_entries})


@pytest.fixture()
def upload_env(document_api, monkeypatch):
    state = SimpleNamespace(
        module=document_api,
        upload_result=([], [], [], []),
        upload_kwargs={},
        rerun_ids=[],
    )

    def fake_upload(kb, file_objs, user_id, **kwargs):
        state.upload_kwargs = kwargs
        return state.upload_result

    monkeypatch.setattr(document_api.FileService, "upload_document", classmethod(lambda cls, *args, **kwargs: fake_upload(*args, **kwargs)))
    monkeypatch.setattr(document_api, "_reset_and_parse_documents", lambda tenant_id, doc_ids, errors: state.rerun_ids.extend(doc_ids) or len(doc_ids))
    return state


def test_upload_response_splits_uploaded_replaced_and_conflicts(upload_env, monkeypatch):
    state = upload_env
    module = state.module
    _stub_dataset_access(module, monkeypatch)
    uploaded_doc = {"id": "doc-new", "name": "fresh.txt", "dataset_id": "kb1"}
    conflict = {"id": "doc-existing", "name": "dup.txt", "size": 5, "suffix": "txt", "content_hash": "h", "chunk_count": 0, "current_version_number": 1, "create_time": 1720000000}
    replaced = {"id": "doc-replaced", "name": "rep.txt", "run": "0"}
    state.upload_result = ([], [(dict(uploaded_doc), b"blob")], [conflict], [dict(replaced)])


    monkeypatch.setattr(module, "request", _upload_request(["fresh.txt"]))
    res = _run(module._upload_local_documents(SimpleNamespace(id="kb1"), "tenant1"))

    assert res["code"] == 0, res
    assert res["data"]["uploaded"] == [{**uploaded_doc, "run": "UNSTART"}], res
    assert res["data"]["conflicts"] == [conflict], res
    assert [d["id"] for d in res["data"]["replaced"]] == ["doc-replaced"], res
    # Replaced documents re-parse immediately: they were queued and report RUNNING.
    assert state.rerun_ids == ["doc-replaced"], res
    assert res["data"]["replaced"][0]["run"] == "RUNNING", res


def test_all_files_conflicting_returns_conflict_code(upload_env, monkeypatch):
    state = upload_env
    module = state.module
    _stub_dataset_access(module, monkeypatch)
    conflict = {"id": "doc-existing", "name": "dup.txt", "size": 5, "suffix": "txt", "content_hash": "h", "chunk_count": 0, "current_version_number": 1, "create_time": 1720000000}
    state.upload_result = ([], [], [conflict], [])

    monkeypatch.setattr(module, "request", _upload_request(["dup.txt"]))
    res = _run(module._upload_local_documents(SimpleNamespace(id="kb1"), "tenant1"))

    assert res["code"] == 409, res
    assert res["data"]["uploaded"] == []
    assert res["data"]["conflicts"] == [conflict]


def test_on_conflict_directive_is_passed_through(upload_env, monkeypatch):
    state = upload_env
    module = state.module
    _stub_dataset_access(module, monkeypatch)
    state.upload_result = ([], [({"id": "doc-new", "name": "a.txt", "dataset_id": "kb1"}, b"blob")], [], [])

    monkeypatch.setattr(module, "request", _DummyRequest(form={"on_conflict": "replace"}, args={}, files={"file": [SimpleNamespace(filename="a.txt", read=lambda: b"x")]}))
    res = _run(module._upload_local_documents(SimpleNamespace(id="kb1"), "tenant1"))
    assert res["code"] == 0, res
    assert state.upload_kwargs["on_conflict"] == "replace"


def test_missing_on_conflict_reports_conflicts_to_caller(upload_env, monkeypatch):
    state = upload_env
    module = state.module
    _stub_dataset_access(module, monkeypatch)
    state.upload_result = ([], [], [], [])

    monkeypatch.setattr(module, "request", _upload_request(["a.txt"]))
    _run(module._upload_local_documents(SimpleNamespace(id="kb1"), "tenant1"))
    assert state.upload_kwargs["on_conflict"] is None


def test_invalid_on_conflict_is_rejected(upload_env, monkeypatch):
    state = upload_env
    module = state.module
    _stub_dataset_access(module, monkeypatch)

    monkeypatch.setattr(module, "request", _DummyRequest(form={"on_conflict": "explode"}, args={}, files={"file": [SimpleNamespace(filename="a.txt", read=lambda: b"x")]}))
    res = _run(module._upload_local_documents(SimpleNamespace(id="kb1"), "tenant1"))
    assert res["code"] == 101, res
    assert 'on_conflict' in res["message"]


# ---------------------------------------------------------------------------
# Version history surface
# ---------------------------------------------------------------------------


class _DocRecord(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc


def _stub_doc_access(module, monkeypatch, dataset_id="kb1", document_id="doc-1"):
    doc = _DocRecord(id=document_id, kb_id=dataset_id, name="report.pdf", tenant_id=None)
    monkeypatch.setattr(module.KnowledgebaseService, "accessible", classmethod(lambda cls, **_kwargs: True))
    monkeypatch.setattr(module.DocumentService, "accessible", classmethod(lambda cls, *_args, **_kwargs: True))
    monkeypatch.setattr(module.DocumentService, "query", classmethod(lambda cls, **kwargs: [doc]))
    return doc


def test_list_versions_returns_version_metadata(document_api, monkeypatch):
    module = document_api
    _stub_doc_access(module, monkeypatch)
    rows = [
        {"id": "ver-2", "version_number": 2, "location": "versions/doc-1/v2/report.pdf", "size": 20, "content_hash": "h2", "created_by": "user-2", "create_time": 1720000200},
        {"id": "ver-1", "version_number": 1, "location": "versions/doc-1/v1/report.pdf", "size": 10, "content_hash": "h1", "created_by": "user-1", "create_time": 1720000000},
    ]
    monkeypatch.setattr(module.DocumentVersionService, "list_versions", classmethod(lambda cls, document_id: rows))

    res = _run(module.list_document_versions("kb1", "doc-1"))

    assert res["code"] == 0, res
    versions = res["data"]
    assert [v["version_number"] for v in versions] == [2, 1], res
    assert versions[0]["id"] == "ver-2"
    assert versions[0]["location"] == "versions/doc-1/v2/report.pdf"
    assert versions[0]["size"] == 20
    assert versions[0]["content_hash"] == "h2"


def test_resolve_versioned_blob_returns_version_location(document_api, monkeypatch):
    module = document_api
    row = SimpleNamespace(id="ver-2", document_id="doc-1", version_number=2, location="versions/doc-1/v2/report.pdf")
    monkeypatch.setattr(module.DocumentVersionService, "get_version", classmethod(lambda cls, document_id, version_id: row if version_id == "ver-2" else None))

    bucket, location, err = module._resolve_versioned_blob("kb1", "doc-1", "ver-2")
    assert err is None
    assert (bucket, location) == ("kb1", "versions/doc-1/v2/report.pdf")

    bucket, location, err = module._resolve_versioned_blob("kb1", "doc-1", "missing")
    assert bucket is None and location is None
    assert "not found" in err

    # No version requested -> fall back to the current blob.
    assert module._resolve_versioned_blob("kb1", "doc-1", None) == (None, None, None)


def test_download_rejects_unknown_version_id(document_api, monkeypatch):
    module = document_api
    _stub_doc_access(module, monkeypatch)
    monkeypatch.setattr(module.DocumentVersionService, "get_version", classmethod(lambda cls, document_id, version_id: None))
    monkeypatch.setattr(module, "request", _DummyRequest(args={"version_id": "nope"}))

    res = _run(module.download("kb1", "doc-1"))

    assert res["code"] == 404, res
