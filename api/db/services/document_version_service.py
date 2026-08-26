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
import logging

import xxhash

from api.db.db_models import DB, DocumentVersion
from api.db.services.common_service import CommonService
from api.db.services.document_service import DocumentService
from api.utils.file_utils import thumbnail_img
from common import settings
from common.constants import TaskStatus

logger = logging.getLogger(__name__)


def version_blob_key(document_id: str, version_number: int, filename: str) -> str:
    """Storage key of a document version's immutable blob.

    Version blobs are never mutated once written; replacing content always
    produces a new key under ``versions/{document_id}/``.
    """
    return f"versions/{document_id}/v{version_number}/{filename}"


class DocumentVersionService(CommonService):
    """Immutable versions of a document's stored bytes.

    Every upload records one version row (v1 at initial upload). Replacing a
    document appends v(n+1) and moves the document's pointer; previous blobs
    stay in storage untouched.
    """

    model = DocumentVersion

    @classmethod
    def next_version_number(cls, document_id):
        rows = cls.query(document_id=document_id)
        return max((row.version_number for row in rows), default=0) + 1

    @classmethod
    def record_version(cls, *, document_id, version_number, location, size, content_hash, created_by):
        return cls.insert(
            document_id=document_id,
            version_number=version_number,
            location=location,
            size=size,
            content_hash=content_hash or "",
            created_by=created_by,
        )

    @classmethod
    def list_versions(cls, document_id):
        rows = cls.query(reverse=True, order_by="version_number", document_id=document_id)
        return [row.to_dict() for row in rows]

    @classmethod
    def get_version(cls, document_id, version_id):
        return cls.get_or_none(document_id=document_id, id=version_id)

    @classmethod
    def ensure_current_version_recorded(cls, doc, user_id):
        """Synthesize a version row for a legacy document that has none.

        Called before a legacy document loses its blob pointer (or is reported
        as already-current), so its existing bytes become retrievable through
        the version history without a data migration.
        """
        if cls.query(document_id=doc.id):
            return
        logger.info("Synthesizing version 1 for legacy document %s", doc.id)
        cls.record_version(
            document_id=doc.id,
            version_number=1,
            location=doc.location,
            size=doc.size or 0,
            content_hash=doc.content_hash or "",
            created_by=user_id,
        )

    @classmethod
    @DB.connection_context()
    def replace_document_version(cls, kb, doc, blob, user_id):
        """Store ``blob`` as a new immutable version of ``doc`` and repoint it.

        Returns ``(updated_doc_dict, noop)``. A noop means the incoming bytes
        are identical to the current version: nothing was written and the
        pipeline must not re-run.
        """
        new_hash = xxhash.xxh128(blob).hexdigest()
        if doc.content_hash and doc.content_hash == new_hash:
            cls.ensure_current_version_recorded(doc, user_id)
            current = doc.to_dict()
            current["current_version_number"] = getattr(doc, "current_version_number", None) or cls.next_version_number(doc.id) - 1
            return current, True

        if not cls.query(document_id=doc.id):
            # Legacy document: capture its current bytes before they lose the pointer.
            cls.ensure_current_version_recorded(doc, user_id)

        next_n = cls.next_version_number(doc.id)
        key = version_blob_key(doc.id, next_n, doc.name)
        settings.STORAGE_IMPL.put(kb.id, key, blob, kb.tenant_id)

        updates = {
            "location": key,
            "size": len(blob),
            "content_hash": new_hash,
            "current_version_number": next_n,
            "progress": 0,
            "progress_msg": "",
            "process_begin_at": None,
            "process_duration": 0,
            "run": TaskStatus.UNSTART.value,
        }
        img = thumbnail_img(doc.name, blob)
        if img is not None:
            thumbnail_location = f"thumbnail_{doc.id}.png"
            settings.STORAGE_IMPL.put(kb.id, thumbnail_location, img)
            updates["thumbnail"] = thumbnail_location

        cls.record_version(
            document_id=doc.id,
            version_number=next_n,
            location=key,
            size=len(blob),
            content_hash=new_hash,
            created_by=user_id,
        )
        DocumentService.update_by_id(doc.id, updates)

        updated = doc.to_dict()
        updated.update(updates)
        return updated, False
