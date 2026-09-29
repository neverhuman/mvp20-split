"""Separate external-wait protection identity; no fictional worker attempts or I/O."""

import hashlib
import uuid
from dataclasses import dataclass

from amphora_contracts_artifacts import ReserveArtifact
from amphora_contracts_core import Identifier
from pydantic import TypeAdapter

from ..compiler.catalog import canonical
from .model import ReceiptEvidence, WaitRecord, ensure


@dataclass(frozen=True)
class WaitRetentionIntent:
    wait: WaitRecord
    evidence: ReceiptEvidence
    operation_id: str
    runtime_owner: str

    def __post_init__(self):
        TypeAdapter(Identifier).validate_python(self.operation_id, strict=True)
        TypeAdapter(Identifier).validate_python(self.runtime_owner, strict=True)
        self.wait.validate_receipt(self.evidence)
        ensure(self.evidence.receipt.outcome.status == "accepted", "wait_retention_output_required")

    @property
    def intent_id(self):
        identity = canonical({"profile": "amphora-wait-intent-identity-v1",
            "scope": self.wait.expectation.scope.model_dump(mode="json"),
            "runtime_owner": self.runtime_owner, "operation_id": self.operation_id}).decode()
        return "wait:" + uuid.uuid5(uuid.NAMESPACE_URL, identity).hex

    @property
    def semantic_sha256(self):
        return hashlib.sha256(canonical({"profile": "amphora-wait-retention-v1",
            "expectation_sha256": self.wait.sha256, "receipt_sha256": self.evidence.sha256})).hexdigest()

    @property
    def reservation(self):
        return ReserveArtifact.model_validate({"artifact": self.evidence.receipt.outcome.output.artifact,
            "intent": {"runtime_owner": self.runtime_owner, "intent_id": self.intent_id,
                       "semantic_completion_sha256": self.semantic_sha256, "output_binding": "result"}})
