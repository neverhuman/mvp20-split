"""Reconstruct owned immutable journal records through their domain invariants."""

from dataclasses import dataclass

from ..context import AttemptBinding, RequestSnapshot
from ..context.policy import require
from ..providers.capture import CapturedOutput, Observation
from ..providers.profiles import OutputProfiles
from ..providers.wire import observation_document


def request_from_row(row, principal):
    require(row["actor_id"] == principal.actor_id, "request_actor_mismatch")
    result = RequestSnapshot.from_bytes(bytes(row["canonical_bytes"]), actor_id=principal.actor_id,
                                         scope=principal.scope)
    require(result.sha256 == row["request_sha256"], "stored_request_corrupt")
    require(result.document().reference.engagement_id == row["engagement_id"], "stored_request_identity")
    return result


def verified_observation(binding, observation):
    require(type(observation.capture.content) is bytes and len(observation.capture.content) <= 65536,
            "observation_size")
    wire = observation_document(observation.canonical)
    binding.validate(wire.attempt)
    require(wire.output_sha256 == observation.capture.sha256, "capture_digest_mismatch")
    require(wire.captured_bytes == len(observation.capture.content), "capture_size_mismatch")
    require(wire.output_complete == observation.capture.complete, "capture_completion_mismatch")
    successful = wire.status in {"proposed", "abstained"}
    require((wire.proposal is not None) == successful, "proposal_status_mismatch")
    if successful:
        require(OutputProfiles.supported(binding), "proposal_profile_mismatch")
        require(wire.output_complete, "incomplete_proposal")
        proposal = OutputProfiles.parse(observation.capture.content, binding)
        require(proposal == wire.proposal, "proposal_capture_mismatch")
        require((proposal.action == "abstain") == (wire.status == "abstained"), "proposal_status_mismatch")
        require(wire.reason_code is None, "successful_reason")
    return Observation(observation.capture, wire.model_dump_json().encode("utf-8"))


@dataclass(frozen=True)
class AttemptJournal:
    binding: AttemptBinding
    observation: Observation | None

    @classmethod
    def from_rows(cls, snapshot, attempt, observation):
        require(attempt["request_sha256"] == snapshot.sha256, "stored_attempt_binding")
        binding = AttemptBinding(snapshot, attempt["ordinal"])
        observed = None
        if observation is not None:
            wire = observation_document(bytes(observation["canonical_bytes"]))
            capture = CapturedOutput(bytes(observation["capture_bytes"]), wire.output_complete)
            observed = verified_observation(binding, Observation(capture, bytes(observation["canonical_bytes"])))
        return cls(binding, observed)
