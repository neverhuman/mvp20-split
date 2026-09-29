"""Exact immutable wait/receipt identity and compatibility, without transitions or I/O."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import DomainReceipt, WaitExpectation

from ..compiler.catalog import canonical
from ..lifecycle.model import TransitionError
from ..wire import raw_fields

EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def ensure(condition, reason):
    if not condition:
        raise TransitionError(reason)


def microseconds(value):
    ensure(value.tzinfo is not None and value.utcoffset() is not None, "wait_naive_deadline")
    delta = value.astimezone(UTC) - EPOCH
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


@dataclass(frozen=True)
class WaitAddress:
    scope: Scope
    run_id: str
    activation_id: str
    plan_sha256: str
    revision: int = 1

    def record(self):
        return {"scope": self.scope.model_dump(mode="json"), "run_id": self.run_id,
                "activation_id": self.activation_id, "plan_sha256": self.plan_sha256, "wait_revision": self.revision}


@dataclass(frozen=True)
class WaitRecord:
    expectation: WaitExpectation

    def __post_init__(self):
        value = WaitExpectation.model_validate(raw_fields(self.expectation))
        ensure(value.subject.scope == value.scope, "wait_foreign_subject")
        object.__setattr__(self, "expectation", value)

    @classmethod
    def pin(cls, address, node, subject, *, opened_at, run_deadline):
        ensure(node.kind == "await", "wait_node_required")
        ensure(microseconds(opened_at) < microseconds(run_deadline), "wait_run_expired")
        deadline = min(opened_at + timedelta(seconds=node.timeout_seconds), run_deadline)
        return cls(WaitExpectation.model_validate_json(canonical({**address.record(),
            "issuer_id": node.issuer_id, "purpose": node.purpose, "expected_revision": node.expected_revision,
            "subject": subject.model_dump(mode="json"), "output_type": node.output.value_type.model_dump(mode="json"),
            "deadline_us": microseconds(deadline), "on_timeout": node.on_timeout})))

    @property
    def sha256(self):
        return hashlib.sha256(canonical({"profile": "amphora-wait-expectation-v1",
                                        "expectation": self.expectation.model_dump(mode="json")})).hexdigest()

    @property
    def deadline(self):
        return EPOCH + timedelta(microseconds=self.expectation.deadline_us)

    def validate_receipt(self, evidence):
        value, expected = evidence.receipt, self.expectation
        for field, actual, required in (
            ("issuer", value.issuer_id, expected.issuer_id), ("scope", value.scope, expected.scope),
            ("purpose", value.purpose, expected.purpose), ("revision", value.revision, expected.expected_revision),
            ("subject", value.subject, expected.subject),
        ):
            ensure(actual == required, "wait_receipt_" + field + "_mismatch")
        ensure(value.outcome.status != "superseded", "wait_receipt_superseded")
        if value.outcome.status == "accepted":
            output, declared = value.outcome.output, expected.output_type
            ensure(output.artifact.scope == expected.scope, "wait_foreign_output")
            ensure(output.artifact.schema_ref == declared.schema_ref and output.artifact.media_type == declared.media_type
                   and output.representation == declared.representation and output.unit == declared.unit,
                   "wait_output_type_mismatch")


@dataclass(frozen=True)
class ReceiptEvidence:
    receipt: DomainReceipt

    def __post_init__(self):
        value = DomainReceipt.model_validate(raw_fields(self.receipt))
        ensure(value.subject.scope == value.scope, "wait_foreign_subject")
        if value.outcome.status == "accepted":
            ensure(value.outcome.output.artifact.scope == value.scope, "wait_foreign_output")
        object.__setattr__(self, "receipt", value)

    @property
    def sha256(self):
        return hashlib.sha256(canonical({"profile": "amphora-domain-receipt-v1",
                                        "receipt": self.receipt.model_dump(mode="json")})).hexdigest()
