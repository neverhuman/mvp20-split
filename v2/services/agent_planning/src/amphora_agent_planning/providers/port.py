"""Attempt-bound provider port. Adapter owns actual transport deadlines."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from amphora_contracts_planning import ModelBinding, ProviderUsage

from ..context import AttemptBinding


@dataclass(frozen=True)
class ProviderReply:
    chunks: Iterable[bytes]
    usage: ProviderUsage


class ProviderUnavailable(Exception):
    """Known pre-response unavailability, not a free-call/refund assertion."""


class ProviderPort(Protocol):
    def supports(self, model: ModelBinding) -> bool: ...

    def reply(self, attempt: AttemptBinding) -> ProviderReply: ...
