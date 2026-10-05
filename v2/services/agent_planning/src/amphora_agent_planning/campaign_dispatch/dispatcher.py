"""One bounded effect step: original receipt first, fresh authority before POST."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from ..campaign_exchanges import (
    CompilerWindow,
    ExchangeAbsent,
    ExchangeConflict,
    ExchangeDenied,
    ExchangeUnavailable,
)
from ..context.policy import require
from .events import TERMINAL, CompilerEvent
from .observation import CompilerObservation
from .prerequisites import CompilerPrerequisites, DispatchPrerequisites
from .records import CompilerOperation


class CompilerFenceLost(RuntimeError):
    """Local authority ended; never classify this as a peer response."""


class CompilerPrerequisiteExpired(RuntimeError):
    """A previously observed candidate expired before transmission."""


@dataclass(frozen=True)
class DispatchStep:
    operation: CompilerOperation
    prerequisites: DispatchPrerequisites | None = None
    pause_reason: str | None = None


def peer_reason(error):
    if isinstance(error, ExchangeUnavailable) and str(error) in {'compiler_response_protocol', 'compiler_response_media'}:
        return 'owner_protocol'
    if isinstance(error, ExchangeDenied):
        return 'owner_access_denied'
    if isinstance(error, ExchangeConflict):
        return 'identity_conflict'
    if isinstance(error, ExchangeAbsent):
        return 'dependency_unavailable'
    return 'owner_unavailable' if isinstance(error, ExchangeUnavailable) else 'owner_protocol'


class CompilerDispatcher:
    def __init__(self, journal, refresh, runtime, registry):
        store, config = journal.store, journal.store.eligibility.document()
        require(runtime.owner_id == store.runtime_owner and runtime.actor_id == store.runtime_actor and
                registry.owner_id == config.owner_id and registry.actor_id == config.actor_id, 'compiler_dispatch_owners')
        self.journal, self.runtime, self.registry = journal, runtime, registry
        self.prerequisites = CompilerPrerequisites(journal, refresh)

    def _append(self, principal, lease, operation, action, data=None):
        event = CompilerEvent.record(operation.effect, operation.progress.position + 1, action, data)
        return self.journal.append(principal, lease, operation.effect.effect_id, operation.progress.position, event)

    def _blocked(self, principal, lease, operation, reason, prerequisites=None):
        if operation.progress.position >= 63:
            return DispatchStep(operation, prerequisites, 'event_limit')
        if operation.progress.state != 'blocked' or operation.progress.reason != reason:
            operation = self._append(principal, lease, operation, 'blocked', reason)
        return DispatchStep(operation, prerequisites, reason)

    def _observed(self, principal, lease, operation, receipt, readback=None):
        observation = CompilerObservation.bind(lease.selection, operation.effect, operation.request, receipt, readback)
        if operation.progress.observation == observation and operation.progress.state == observation.status:
            return operation
        if operation.progress.position >= 63 and observation.status not in TERMINAL:
            return operation
        return self._append(principal, lease, operation, 'observed', json.loads(observation.canonical))

    def _runtime_history(self, principal, lease, operation, window):
        retained = operation.progress.observation
        try:
            # An accepted historical receipt is immutable. Read its exact object
            # even if a subsequent receipt query would be absent or denied.
            if retained is not None and retained.outcome.receipt.outcome.status == 'accepted':
                outcome = retained.outcome
            else:
                outcome = self.runtime.receipt(operation.request, window)
        except ExchangeAbsent:
            return operation, None
        except ValueError as error:
            return operation, peer_reason(error)
        if outcome.receipt.outcome.status == 'accepted':
            try:
                outcome = self.runtime.readback(outcome, window)
            except ValueError as error:
                operation = self._observed(principal, lease, operation, outcome.receipt)
                return operation, peer_reason(error)
        operation = self._observed(principal, lease, operation, outcome.receipt, outcome.readback)
        return operation, None

    def step(self, principal, lease, effect_id, *, check_id=None):
        self.journal.store.guard(principal, lease)
        operation = self.journal.read(principal, lease.selection.effect_id, effect_id)
        require(operation is not None, 'compiler_effect_unknown')
        if operation.terminal:
            return DispatchStep(operation)
        registry = operation.effect.document().kind == 'resolve'
        window = CompilerWindow('registry' if registry else 'runtime')
        if not registry:
            operation, reason = self._runtime_history(principal, lease, operation, window)
            if operation.terminal:
                return DispatchStep(operation)
            if reason is not None:
                return self._blocked(principal, lease, operation, reason)
        prerequisites = self.prerequisites.check(principal, lease, operation, check_id)
        if prerequisites.status != 'ready_to_journal':
            return self._blocked(principal, lease, operation, prerequisites.status, prerequisites)
        # Leave space for dispatch plus a nonterminal response; slot64 remains
        # available for eventual terminal reconciliation, never another POST.
        if operation.progress.position > 61:
            return DispatchStep(operation, prerequisites, 'event_limit')
        operation = self._append(principal, lease, operation, 'dispatch')

        def guard():
            try:
                self.journal.store.guard(principal, lease)
            except (ValueError, PermissionError) as error:
                raise CompilerFenceLost('compiler_dispatch_fence_lost') from error
            if not registry:
                for observed in prerequisites.detail.observations:
                    try:
                        observed.require_fresh(datetime.now(UTC))
                    except ValueError as error:
                        raise CompilerPrerequisiteExpired('eligibility_expired') from error

        # Recovery reads and a new write each have a separate bounded window;
        # required current-input reads are not charged as peer idle time.
        window = CompilerWindow('registry' if registry else 'runtime')
        readback_reason = None
        try:
            if registry:
                receipt = self.registry.resolve(operation.effect.document().owner_id, operation.request.command,
                                                window, guard=guard)
                readback = None
            else:
                outcome = self.runtime.submit(operation.request, window, guard=guard)
                if outcome.receipt.outcome.status == 'accepted':
                    try:
                        outcome = self.runtime.readback(outcome, window)
                    except ValueError as error:
                        readback_reason = peer_reason(error)
                receipt, readback = outcome.receipt, outcome.readback
            # Bind before leaving the peer-error region; journal writes/fence
            # failures below must propagate rather than masquerade as peer I/O.
            observation = CompilerObservation.bind(lease.selection, operation.effect, operation.request, receipt, readback)
        except CompilerPrerequisiteExpired:
            return self._blocked(principal, lease, operation, 'eligibility_expired', prerequisites)
        except ExchangeUnavailable as error:
            operation = self._append(principal, lease, operation, 'uncertain')
            return DispatchStep(operation, prerequisites, peer_reason(error))
        except ValueError as error:
            return self._blocked(principal, lease, operation, peer_reason(error), prerequisites)
        operation = self._append(principal, lease, operation, 'observed', json.loads(observation.canonical))
        if readback_reason is not None:
            return self._blocked(principal, lease, operation, readback_reason, prerequisites)
        return DispatchStep(operation, prerequisites)
