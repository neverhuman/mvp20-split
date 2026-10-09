"""Bounded owner interfaces; adapters use public peers and managed worker journals."""
from dataclasses import dataclass
from typing import Protocol

from amphora_contracts_graph_runtime import GraphRunPage
from amphora_contracts_runtime import CommandReceipt

from .intent import LaunchError, LaunchIntent
from .state import LaunchState


class PeerUnavailable(Exception):
    """Transient/ambiguous I/O: retry the same durable identity, never reject it."""


class PreflightRejected(Exception):
    """Definitive local/public preflight denial before admission is attempted."""


class PeerRecordMissing(Exception):
    """Public owner returned a well-formed, explicit not-found observation."""


@dataclass(frozen=True, slots=True)
class WorkerObservation:
    expected: int
    ready: int
    quiescent: bool
    faulted: bool = False

    def __post_init__(self):
        if (type(self.expected) is not int or type(self.ready) is not int
                or not 1 <= self.expected <= 64 or not 0 <= self.ready <= self.expected
                or type(self.quiescent) is not bool or type(self.faulted) is not bool
                or (self.quiescent and (self.ready or self.faulted))):
            raise LaunchError('launch_worker_observation_invalid')


class PreflightPort(Protocol):
    def check(self, intent: LaunchIntent) -> None:
        """Check exact public draft/inputs/tools and local capacity; no admission."""


class RuntimePort(Protocol):
    def receipt(self, intent: LaunchIntent) -> CommandReceipt | None:
        """None only for a verified missing receipt, never timeout/permission failure."""

    def admit(self, intent: LaunchIntent) -> CommandReceipt:
        """Submit the original canonical admission bytes without re-encoding."""

    def run(self, state: LaunchState) -> GraphRunPage:
        """Observe the original run through Runtime's public scoped route."""


class WorkersPort(Protocol):
    def prepare(self, state: LaunchState) -> WorkerObservation:
        """Durably pin/reconcile exact run bindings, without starting workers."""

    def engage(self, state: LaunchState) -> WorkerObservation:
        """Idempotently engage original bindings; ambiguous old turns are adopted."""

    def observe(self, state: LaunchState) -> WorkerObservation:
        """Read actual bound workers, including latched faults."""

    def drain(self, state: LaunchState) -> WorkerObservation:
        """Idempotently quiesce original bindings and reconcile their journals."""
