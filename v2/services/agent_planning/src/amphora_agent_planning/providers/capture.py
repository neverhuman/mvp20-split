"""Bounded diagnostic capture; provider text never becomes executable authority."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_planning import ProviderUsage

from ..context import AttemptBinding
from .port import ProviderPort, ProviderUnavailable
from .profiles import OutputProfiles
from .wire import observation_document

MAX_OUTPUT_BYTES = 65536
MAX_CHUNKS = 256


def unknown_usage() -> ProviderUsage:
    return ProviderUsage(input_tokens=None, output_tokens=None, accounting_units=None, certainty="unknown")


@dataclass(frozen=True)
class CapturedOutput:
    content: bytes
    complete: bool

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclass(frozen=True)
class Observation:
    capture: CapturedOutput
    canonical: bytes

    @classmethod
    def record(cls, attempt, capture, status, reason, usage, proposal=None):
        wire = OutputProfiles.observation_model(attempt)(attempt=attempt.reference(), status=status, reason_code=reason,
            output_sha256=capture.sha256, captured_bytes=len(capture.content), output_complete=capture.complete,
            usage=usage, proposal=proposal)
        return cls(capture, wire.model_dump_json().encode("utf-8"))

    def document(self):
        return observation_document(self.canonical)


def observe(attempt: AttemptBinding, provider: ProviderPort) -> Observation:
    context = attempt.request.document().context
    empty = CapturedOutput(b"", False)
    if not provider.supports(context.model) or not OutputProfiles.supported(attempt):
        return Observation.record(attempt, empty, "policy_rejected", "provider_or_profile_mismatch", unknown_usage())
    try:
        reply = provider.reply(attempt)
    except ProviderUnavailable:
        return Observation.record(attempt, empty, "unavailable", "provider_unavailable", unknown_usage())
    except Exception:  # noqa: BLE001 - unknown adapter failures must retain a bounded outcome
        return Observation.record(attempt, empty, "unknown", "dispatch_outcome_unknown", unknown_usage())
    # Revalidate even constructed/copied DTOs before using them as observations.
    try:
        usage = ProviderUsage.model_validate_json(reply.usage.model_dump_json(warnings=False))
    except (ValueError, AttributeError, TypeError):
        usage = unknown_usage()
    if usage.certainty == "reported" and None in (usage.input_tokens, usage.output_tokens, usage.accounting_units):
        usage = usage.model_copy(update={"certainty": "unknown"})
    captured = bytearray()
    try:
        for index, chunk in enumerate(reply.chunks):
            if index >= MAX_CHUNKS or type(chunk) is not bytes:
                return Observation.record(attempt, CapturedOutput(bytes(captured), False),
                    "invalid", "output_stream_limit", usage)
            remaining = MAX_OUTPUT_BYTES - len(captured)
            captured.extend(chunk[:remaining])
            if len(chunk) > remaining:
                return Observation.record(attempt, CapturedOutput(bytes(captured), False),
                    "invalid", "output_size", usage)
    except Exception:  # noqa: BLE001 - arbitrary iterator failures preserve partial capture
        return Observation.record(attempt, CapturedOutput(bytes(captured), False),
            "unknown", "response_interrupted", usage)
    capture = CapturedOutput(bytes(captured), True)
    try:
        proposal = OutputProfiles.parse(capture.content, attempt)
    except ValueError as exc:
        code = str(exc)
        policy = code in {"action_not_allowed", "proposal_scope_mismatch", "unselected_payload",
                         "campaign_output_purpose", "campaign_output_profile", "campaign_decision_scope",
                         "campaign_output_scope", "campaign_adjustment_purpose", "campaign_adjustment_cut"}
        return Observation.record(attempt, capture, "policy_rejected" if policy else "invalid", code, usage)
    return Observation.record(attempt, capture, "abstained" if proposal.action == "abstain" else "proposed",
                              None, usage, proposal)
