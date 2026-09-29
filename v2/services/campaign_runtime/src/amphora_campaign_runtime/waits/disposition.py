"""A wait's terminal meaning, separate from command delivery and worker outcomes."""

from dataclasses import dataclass

from amphora_contracts_graph_runtime import WaitClosure

from .model import ReceiptEvidence, WaitRecord, ensure, microseconds


@dataclass(frozen=True)
class WaitDisposition:
    wait: WaitRecord
    status: str
    reason_code: str | None = None
    evidence: ReceiptEvidence | None = None

    def __post_init__(self):
        if self.evidence is not None:
            self.wait.validate_receipt(self.evidence)
        if self.status == "accepted":
            ensure(self.evidence is not None and self.evidence.receipt.outcome.status == "accepted"
                   and self.reason_code is None, "wait_acceptance_evidence_required")
        else:
            ensure(self.status in {"blocked", "abstained", "cancelled"} and self.reason_code is not None,
                   "wait_terminal_reason_required")
            if self.evidence is not None:
                outcome = self.evidence.receipt.outcome
                ensure((outcome.status, self.status) in {("rejected", "blocked"), ("abstained", "abstained")}
                       and self.reason_code == outcome.reason_code, "wait_disposition_mismatch")
            elif self.status != "cancelled":
                ensure(self.reason_code == "wait_deadline_expired", "wait_timeout_reason_required")
        self.closure(1)  # Validate strict boundary fields before any persistence.

    @classmethod
    def received(cls, wait, evidence):
        wait.validate_receipt(evidence)
        outcome = evidence.receipt.outcome
        if outcome.status == "accepted":
            return cls(wait, "accepted", evidence=evidence)
        return cls(wait, "blocked" if outcome.status == "rejected" else "abstained", outcome.reason_code, evidence)

    @classmethod
    def timeout(cls, wait, now):
        ensure(microseconds(now) >= wait.expectation.deadline_us, "wait_timeout_not_due")
        return cls(wait, wait.expectation.on_timeout, "wait_deadline_expired")

    def closure(self, revision):
        expected = self.wait.expectation
        receipt = None if self.evidence is None else self.evidence.receipt.model_dump(mode="json")
        outcome = {"status": self.status, "receipt": receipt}
        if self.status != "accepted":
            outcome["reason_code"] = self.reason_code
        return WaitClosure.model_validate({"scope": expected.scope, "run_id": expected.run_id,
            "activation_id": expected.activation_id, "wait_revision": expected.wait_revision,
            "expectation_sha256": self.wait.sha256, "closure_revision": revision, "outcome": outcome})

    @property
    def output(self):
        return self.evidence.receipt.outcome.output if self.status == "accepted" else None

    @property
    def node_status(self):
        return {"accepted": "succeeded", "abstained": "failed", "blocked": "blocked", "cancelled": "skipped"}[self.status]
