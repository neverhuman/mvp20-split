"""Draft identity and optimistic revision policy, independent of storage and transport."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_campaigns import ExecutableCampaignV4
from amphora_contracts_graph_runtime import DraftHead, DraftRevision, SaveDraft


class DraftConflict(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DraftContent:
    title: str
    definition: ExecutableCampaignV4

    @classmethod
    def from_save(cls, request: SaveDraft):
        if not request.title.strip():
            raise ValueError("draft_title_empty")
        return cls(request.title, request.definition)

    @property
    def canonical_bytes(self):
        # Authored order is retained; compiler identity is a separate semantic profile.
        value = {"profile": "amphora-draft-content-v1", "title": self.title,
                 "definition": self.definition.model_dump(mode="json")}
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical_bytes).hexdigest()


@dataclass(frozen=True, slots=True)
class DraftVersion:
    draft_id: str
    revision: int
    content: DraftContent

    @classmethod
    def save(cls, request: SaveDraft, current: "DraftVersion | None"):
        actual = 0 if current is None else current.revision
        if request.expected_revision != actual:
            raise DraftConflict("draft_revision_conflict")
        content = DraftContent.from_save(request)
        if current is not None and (current.draft_id != request.draft_id or
            current.content.definition.scope != content.definition.scope or
            current.content.definition.campaign_id != content.definition.campaign_id):
            raise DraftConflict("draft_identity_conflict")
        if actual >= 9007199254740991:
            raise DraftConflict("draft_revision_exhausted")
        return cls(request.draft_id, actual + 1, content)

    def to_wire(self):
        return DraftRevision(scope=self.content.definition.scope,
            head=DraftHead(draft_id=self.draft_id, revision=self.revision, content_sha256=self.content.sha256,
                           title=self.content.title), parent_revision=self.revision - 1, definition=self.content.definition)

    @classmethod
    def from_wire(cls, record: DraftRevision):
        content = DraftContent(record.head.title, record.definition)
        if content.sha256 != record.head.content_sha256:
            raise ValueError("draft_content_mismatch")
        return cls(record.head.draft_id, record.head.revision, content)
