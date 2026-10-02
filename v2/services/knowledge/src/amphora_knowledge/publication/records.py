"""Versioned private journal records, reconstructed through owner behavior."""

import hashlib
import json
from dataclasses import asdict, dataclass

from amphora_contracts_artifacts import DerivedUploadReceipt, UploadContentReceipt
from amphora_contracts_core import Identifier
from amphora_contracts_knowledge import ReferenceValidation
from pydantic import TypeAdapter

from ..authoring.canonical import KnowledgeError
from ..reasoning.profile import raw
from .attempt import AttemptIdentity, PublicationAttempt
from .payload import ReasoningArtifact


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def checked_bytes(row):
    body = bytes(row["canonical_bytes"])
    if hashlib.sha256(body).hexdigest() != row["sha256"]:
        raise KnowledgeError("publication_storage_mismatch")
    return body


@dataclass(frozen=True)
class PayloadRecord:
    artifact: ReasoningArtifact

    @property
    def body(self):
        artifact = self.artifact
        body = encoded({"format": "1", "result": artifact.result.model_dump(mode="json"),
            "observation": artifact.observation.model_dump(mode="json"),
            "content": artifact.content.model_dump(mode="json"), "declaration": artifact.declaration.model_dump(mode="json")})
        if len(body) > 20 * 1024 * 1024:
            raise KnowledgeError("publication_payload_size_limit")
        return body

    @classmethod
    def restore(cls, document, status, body):
        value = json.loads(body)
        observation = ReferenceValidation.model_validate_json(encoded(value["observation"]))
        record = cls(ReasoningArtifact.reviewed(document, status, observation))
        # Also rejects unknown fields, format changes, noncanonical encodings,
        # or result/descriptor/declaration substitutions in retained storage.
        if record.body != body:
            raise KnowledgeError("publication_storage_mismatch")
        return record


@dataclass(frozen=True)
class AttemptEvent:
    action: str
    body: bytes

    @classmethod
    def prepared(cls, attempt):
        return cls("prepared", encoded({"format": "1", "identity": asdict(attempt.identity)}))

    @classmethod
    def transition(cls, action, receipt=None):
        models = {"begun": DerivedUploadReceipt, "streamed": UploadContentReceipt}
        if action in models:
            record = models[action].model_validate(raw(receipt))
            value = {"format": "1", "receipt": record.model_dump(mode="json")}
        elif action in {"streaming", "abandoned", "finalizing"} and receipt is None:
            value = {"format": "1"}
            if action == "abandoned":
                value["reason"] = "stream_outcome_unknown"
        else:
            raise KnowledgeError("publication_event_invalid")
        return cls(action, encoded(value))

    def apply(self, previous, artifact):
        if len(self.body) > 262144:
            raise KnowledgeError("publication_event_size_limit")
        value = json.loads(self.body)
        if self.action == "prepared":
            identity = AttemptIdentity(**value["identity"])
            if (type(identity.ordinal) is not int or not 1 <= identity.ordinal <= 8
                    or identity.begin_id == identity.finalize_id):
                raise KnowledgeError("publication_storage_mismatch")
            for key in (identity.begin_id, identity.finalize_id):
                TypeAdapter(Identifier).validate_python(key, strict=True)
            if identity.ordinal != (1 if previous is None else previous.identity.ordinal + 1):
                raise KnowledgeError("publication_storage_mismatch")
            if previous is not None:
                previous._at("abandoned")
            next_attempt = PublicationAttempt(identity)
            expected = self.prepared(next_attempt)
        else:
            if previous is None:
                raise KnowledgeError("publication_storage_mismatch")
            models = {"begun": DerivedUploadReceipt, "streamed": UploadContentReceipt}
            receipt = models[self.action].model_validate_json(encoded(value["receipt"])) if self.action in models else None
            expected = self.transition(self.action, receipt)
            if self.action == "begun":
                next_attempt = previous.accepted_upload(artifact, receipt)
            elif self.action == "streamed":
                next_attempt = previous.streamed(receipt)
            elif self.action == "streaming":
                next_attempt = previous.start_stream()
            elif self.action == "abandoned":
                next_attempt = previous.abandon_stream()
            else:
                next_attempt = previous.start_finalize()
        if expected.body != self.body:
            raise KnowledgeError("publication_storage_mismatch")
        return next_attempt
