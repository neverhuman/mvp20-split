"""Immutable reservation identity and monotonic terminal decisions."""

from dataclasses import dataclass

from amphora_contracts_artifacts import CompletionIntentBinding, ReservationBinding, ReservationReceipt
from amphora_contracts_core import ArtifactRef

from ..publication.model import UploadError


@dataclass(frozen=True, slots=True)
class Reservation:
    binding: ReservationBinding
    status: str
    proof: dict | None

    @classmethod
    def from_row(cls, row, scope):
        artifact = ArtifactRef(artifact_id=row["artifact_id"], scope=scope,
            sha256=row["content_sha256"], size_bytes=row["size_bytes"],
            media_type=row["media_type"], schema_ref=row["schema_ref"])
        intent = CompletionIntentBinding(runtime_owner=row["runtime_owner"], intent_id=row["intent_id"],
            output_binding=row["output_binding"], semantic_completion_sha256=row["semantic_sha256"])
        return cls(ReservationBinding(reservation_id=row["reservation_id"], artifact=artifact, intent=intent),
                   row["status"], row["outcome_proof"])

    def receipt(self):
        outcome = {"status": self.status, "binding": self.binding.model_dump(mode="json")}
        if self.proof is not None:
            outcome["proof"] = self.proof
        return ReservationReceipt.model_validate({"outcome": outcome})

    def apply(self, outcome):
        if outcome.binding != self.binding:
            raise UploadError("runtime_binding_mismatch")
        proof = outcome.proof.model_dump(mode="json")
        target = {"committed": "confirmed", "aborted": "released"}.get(proof["status"])
        if target is None:
            return self
        if self.status != "reserved" and (self.status != target or self.proof != proof):
            raise UploadError("runtime_outcome_conflict")
        return Reservation(self.binding, target, proof)
