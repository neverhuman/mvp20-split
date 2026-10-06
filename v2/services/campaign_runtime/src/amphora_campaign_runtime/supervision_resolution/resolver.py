"""One run transaction chooses a model winner or an attributable bounded disposition."""

from amphora_contracts_supervision import CheckpointFallback
from sqlalchemy import text

from ..supervision_journal.responses import RESPONSES, StoredResponse
from ..supervision_outcomes.reports import KEY, ReportJournal
from ..supervision_scope.observations import require
from ..supervision_winners import WinnerStore
from ..supervision_winners.storage import slot_for
from .disposition import RequestDisposition

REPAIR_REASONS = frozenset({'scalar_adjustment_outside_policy', 'selection_proposal_seed',
    'selection_multiple_occurrences', 'selection_target_occurrence', 'selection_field_not_permitted',
    'selection_field_order_or_duplicate', 'selection_prior_value', 'selection_current_original_mismatch',
    'selected_observation_changed', 'selection_target_kind'})


class OutcomeResolver:
    def __init__(self, reports):
        self.reports = reports
        self.winners = WinnerStore(reports.requests.engine)

    @staticmethod
    def responses(conn, params):
        rows = conn.execute(text(RESPONSES + ' AND s.run_id=:run AND s.decision_id=:decision '
            'AND s.request_sha256=:request ORDER BY s.sequence'), params).mappings().all()
        return tuple(StoredResponse.from_row(row) for row in rows)

    @staticmethod
    def matching(report, responses):
        expected = report.document().attempts[-1] if report.document().attempts else None
        for response in responses:
            if expected is None or response.bound.document().observation.attempt != expected.attempt:
                continue
            try:
                report.require_response(response.bound.document())
            except ValueError as error:
                if str(error) != 'execution_response_observation':
                    raise
                continue  # Late captures are diagnostic, never a substitute for the primary hash.
            return response
        return None

    @staticmethod
    def allowance(conn, params, slot):
        # Legacy manually prepared requests have no autonomous reservation authority.
        if slot.seed.policy.document().profile != 'runtime-supervision-policy.v2':
            return False
        rule = next(item for item in slot.seed.policy.document().checkpoints
                    if item.checkpoint_id == slot.seed.document().checkpoint_id)
        ceilings = slot.seed.policy.document().ceilings
        rows = conn.execute(text('SELECT decision_id,max_attempts FROM runtime.supervision_call_reservations '
            'WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run'), params).mappings().all()
        local = [row for row in rows if row['decision_id'] == params['decision']]
        return (len(local) < rule.max_requests and len(rows) < ceilings.max_requests and
                sum(row['max_attempts'] for row in local) < rule.max_model_calls and
                sum(row['max_attempts'] for row in rows) < ceilings.max_model_calls)

    def resolve(self, principal, reference, request_sha256):
        principal.require('supervise_accept')
        params = self.reports.params(principal, reference, request_sha256)
        def transaction(conn):
            winner = self.winners.resolve_locked(conn, params, reference)
            if winner is not None:
                return winner
            original = ReportJournal.source(conn, params)
            saved = ReportJournal.load(conn, params, original)
            if saved is None:
                return None
            report = saved.report
            responses = self.responses(conn, params)
            prior = conn.execute(text('SELECT * FROM runtime.supervision_request_dispositions WHERE ' + KEY),
                                 params).mappings().one_or_none()
            if prior is not None:
                return RequestDisposition.restore(prior, report, responses)
            latest = conn.execute(text('SELECT max(ordinal) FROM runtime.supervision_requests '
                'WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run AND decision_id=:decision'),
                params).scalar_one()
            require(original.frame.request.lineage.ordinal == latest, 'resolution_request_superseded')
            wire = report.document()
            response = self.matching(report, responses)
            reason, kind = 'checkpoint_' + wire.stop_reason, 'fallback'
            if wire.stop_reason in {'proposed', 'abstained'}:
                if response is None:
                    return None
                try:
                    return self.winners.resolve_locked(conn, params, reference,
                        response_id=response.bound.document().response_id)
                except ValueError as error:
                    if str(error) not in REPAIR_REASONS:
                        raise
                    reason, kind = str(error), 'repair'
            elif wire.stop_reason == 'policy_rejected' or (
                    wire.stop_reason == 'attempt_limit' and wire.attempts[-1].status == 'invalid'):
                if response is None:
                    return None
                reason, kind = 'checkpoint_output_rejected', 'repair'
                if response.bound.document().observation.reason_code == 'provider_or_profile_mismatch':
                    reason, kind = 'checkpoint_provider_profile_unavailable', 'fallback'
            slot = slot_for(conn, params)
            if kind == 'repair' and not self.allowance(conn, params, slot):
                reason, kind = 'checkpoint_request_allowance_exhausted', 'fallback'
            disposition = RequestDisposition.bind(report, kind, reason, response)
            conn.execute(text('INSERT INTO runtime.supervision_request_dispositions '
                '(tenant_id,project_id,run_id,decision_id,request_sha256,disposition_sha256,canonical_bytes) '
                'VALUES (:tenant,:project,:run,:decision,:request,:digest,:canonical)'),
                {**params, 'digest': disposition.sha256, 'canonical': disposition.canonical})
            if kind == 'repair':
                return disposition
            run = self.winners.leases._run(conn, params)
            rule = next(item for item in slot.seed.policy.document().checkpoints
                        if item.checkpoint_id == slot.seed.document().checkpoint_id)
            outcome = CheckpointFallback(kind='fallback', action=rule.fallback, reason_code=reason)
            return self.winners._commit(conn, params, run, slot, reference, outcome, None, None)
        return self.winners.leases.commands.transact(transaction)
