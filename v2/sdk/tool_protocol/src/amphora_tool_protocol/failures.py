"""Execution failure policy, independent from scientific payload semantics."""

from dataclasses import dataclass

from .commands import CommandRejected, CommandUnresolved
from .transport import TransportLost


@dataclass(frozen=True, slots=True)
class ExecutionFailure:
    reason_code: str
    retryable: bool

    @classmethod
    def from_protocol(cls, error):
        if isinstance(error, CommandRejected):
            return cls(error.reason_code, error.reason_code == "capacity_exhausted")
        if isinstance(error, (TransportLost, CommandUnresolved)) or str(error) in {"stream_unavailable", "run_unavailable"}:
            return cls("tool_transport_failure", True)
        return cls("tool_protocol_violation", False)

    def to_wire(self):
        return {"status": "failed", "reason_code": self.reason_code, "retryable": self.retryable}
