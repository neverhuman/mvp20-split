"""Scoped catalog projection and verified content retrieval."""

from dataclasses import dataclass

from amphora_contracts_artifacts import ContentDescriptor
from amphora_contracts_core import ArtifactRef
from sqlalchemy import text

from .publication.model import UploadError
from .publication.uploads import SCOPE
from .source_rights.ledger import SourceRights


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    reference: ArtifactRef
    storage_key: str

    @property
    def content(self):
        return ContentDescriptor(**self.reference.model_dump(exclude={"artifact_id", "scope"}))


class ArtifactReads:
    def __init__(self, engine, storage, max_bytes):
        self.engine, self.storage, self.max_bytes = engine, storage, max_bytes
        self.rights = SourceRights(engine)

    def get(self, principal, artifact_id):
        principal.require("read")
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM artifacts.catalog WHERE " + SCOPE + " AND artifact_id=:artifact"),
                {**principal.bindings, "artifact": artifact_id}).mappings().one_or_none()
        if row is None:
            raise UploadError("artifact_unavailable")
        return StoredArtifact(ArtifactRef(artifact_id=row["artifact_id"], scope=principal.scope,
            sha256=row["content_sha256"], size_bytes=row["size_bytes"], media_type=row["media_type"],
            schema_ref=row["schema_ref"]), row["storage_key"])

    def content(self, principal, artifact_id):
        return self._content(principal, artifact_id, "read")

    def processing_content(self, principal, artifact_id):
        """Fresh process-purpose ancestry check, not a continuing rights lease."""
        return self._content(principal, artifact_id, "process")

    def _content(self, principal, artifact_id, use):
        stored = self.get(principal, artifact_id)
        if stored.reference.size_bytes > self.max_bytes:
            raise UploadError("artifact_read_limit")
        snapshot = self.rights.capture(principal, (artifact_id,), use=use)
        content = self.storage.verify(stored.storage_key, stored.content)
        self.rights.recheck(principal, snapshot)
        return stored, content
