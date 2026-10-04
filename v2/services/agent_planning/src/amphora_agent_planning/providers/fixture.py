"""Deterministic adversarial adapter. No network, secret, tool or peer side effects."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, get_args

from amphora_contracts_planning import ModelBinding, ProviderUsage

from ..context import AttemptBinding
from .port import ProviderReply, ProviderUnavailable

Variant = Literal["abstain", "proposal", "invented_action", "oversized", "malformed", "unknown_usage",
                  "unavailable", "interrupted", "delayed"]


@dataclass(frozen=True)
class FixtureProvider:
    variant: Variant
    barrier: Callable[[], None] | None = None
    def __post_init__(self):
        if self.variant not in get_args(Variant):
            raise ValueError("unknown_fixture_variant")

    def supports(self, model: ModelBinding) -> bool:
        return (model.provider_id, model.model_id, model.model_revision) == (
            "deterministic", "adversarial-fixture", "1")

    def reply(self, attempt: AttemptBinding) -> ProviderReply:
        if self.variant == "unavailable":
            raise ProviderUnavailable()
        if self.variant == "delayed":
            if self.barrier is None:
                raise ValueError("missing_fixture_barrier")
            self.barrier()
        value = {"schema_version": "1", "action": "abstain", "rationale": "Synthetic fixture abstains.", "payload": None}
        if self.variant == "proposal":
            value.update(action="propose_knowledge_change",
                         payload=attempt.request.document().context.entries[0].artifact.model_dump(mode="json"))
        if self.variant == "invented_action":
            value["action"] = "execute_code"
        raw = json.dumps(value).encode("utf-8")
        if self.variant == "oversized":
            raw = b"x" * 65537
        elif self.variant == "malformed":
            raw = b"{"

        def chunks():
            yield raw[:7]
            if self.variant == "interrupted":
                raise TimeoutError("fixture transport interruption")
            yield raw[7:]

        usage = ProviderUsage(input_tokens=10, output_tokens=10, accounting_units=1, certainty="reported")
        if self.variant in {"unknown_usage", "interrupted"}:
            usage = ProviderUsage(input_tokens=None, output_tokens=None, accounting_units=None, certainty="unknown")
        return ProviderReply(chunks(), usage)
