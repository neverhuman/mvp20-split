"""Pinned fallback for pre-request failures and terminal owned delivery evidence."""

from amphora_contracts_supervision import CheckpointFallback
from sqlalchemy import text

from ..supervision_context.repair import RepairEvidence
from ..supervision_journal.delivery_values import DeliveryEvent
from ..supervision_journal.storage import SELECT, StoredRequest
from ..supervision_resolution import OutcomeResolver
from ..supervision_scope.observations import require
from ..supervision_winners import WinnerStore
from ..supervision_winners.current import current_seed
from ..supervision_winners.storage import slot_for

PREPARATION_FAILURES = frozenset({'planning_delegation_unavailable', 'binding_publication_rejected',
                                 'context_allowance_exhausted', 'context_original_fields_changed'})


class PinnedFallback:
    def __init__(self, requests):
        self.requests = requests
        self.winners = WinnerStore(requests.engine)

    def resolve(self, principal, reference, *, parent=None, preparation_reason=None, delivery_request=None):
        principal.require('supervise_accept')
        principal.require('supervise_prepare' if preparation_reason is not None else 'supervise_dispatch')
        require((preparation_reason in PREPARATION_FAILURES and delivery_request is None) or
                (preparation_reason is None and delivery_request is not None), 'loop_fallback_reason')
        params = self.winners.params(principal, reference)

        def transaction(conn):
            winner = self.winners.resolve_locked(conn, params, reference)
            if winner is not None:
                return winner
            rows = conn.execute(text(SELECT + ' ORDER BY r.ordinal'), params).mappings().all()
            previous = tuple(StoredRequest.from_row(row) for row in rows)
            require(all(item.frame.document().prepared_by == principal.actor_id for item in previous),
                    'loop_preparer_identity')
            latest = previous[-1].frame.request_sha256 if previous else None
            # An already-created successor beats a stale failure from its predecessor.
            if latest != (delivery_request if delivery_request is not None else parent):
                return None
            slot = slot_for(conn, params)
            if delivery_request is not None:
                row = conn.execute(text('SELECT * FROM runtime.supervision_delivery_events WHERE '
                    'tenant_id=:tenant AND project_id=:project AND run_id=:run AND decision_id=:decision '
                    'AND request_sha256=:request ORDER BY sequence DESC LIMIT 1'),
                    {**params, 'request': delivery_request}).mappings().one_or_none()
                event = None if row is None else DeliveryEvent.from_row(row)
                if event is None or event.kind not in {'rejected', 'failed', 'expired'}:
                    return None
                reason = 'checkpoint_delivery_' + event.kind
            else:
                if parent is not None:
                    require(RepairEvidence.load(conn, params, parent) is not None, 'loop_repair_intent_required')
                if preparation_reason == 'context_allowance_exhausted' and OutcomeResolver.allowance(conn, params, slot):
                    return None
                if preparation_reason == 'planning_delegation_unavailable':
                    key = (principal.scope.tenant_id, principal.scope.project_id, principal.actor_id)
                    if self.requests.planning_actors.get(key) is not None:
                        return None
                if preparation_reason == 'context_original_fields_changed':
                    current = current_seed(conn, params, self.winners.leases._run(conn, params), slot)
                    if current.document().original_fields == slot.seed.document().original_fields:
                        return None
                reason = 'checkpoint_' + preparation_reason
            rule = next(item for item in slot.seed.policy.document().checkpoints
                        if item.checkpoint_id == slot.seed.document().checkpoint_id)
            outcome = CheckpointFallback(kind='fallback', action=rule.fallback, reason_code=reason)
            run = self.winners.leases._run(conn, params)
            return self.winners._commit(conn, params, run, slot, reference, outcome, None, None)

        return self.winners.leases.commands.transact(transaction)
