"""One append-only winner, effective selection, audit and outbox in a run-locked transaction."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_campaigns import parse_execution_plan
from amphora_contracts_supervision import (
    CheckpointCancelled,
    CheckpointDecision,
    CheckpointFallback,
    SupervisionRef,
)
from sqlalchemy import text

from ..coordinator.storage import GraphStorage
from ..lifecycle.claims import RUN, RuntimeLeases
from ..lifecycle.model import RunBudget
from ..supervision_checkpoints.storage import StoredCheckpoint
from ..supervision_checkpoints.values import read_seed
from ..supervision_effects import ScalarSelection
from ..supervision_journal.checkpoint_frames import read_frame
from ..supervision_journal.responses import RESPONSES, StoredResponse
from ..supervision_policy.storage import PolicyPins
from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require
from .current import current_seed
from .model import ModelWinner

WINNER = 'SELECT * FROM runtime.supervision_winners WHERE ' + RUN + ' AND decision_id=:decision'


def slot_for(conn, params):
    graph = GraphStorage.graph(conn, params)
    raw = conn.execute(text('SELECT document FROM runtime.graph_plans WHERE tenant_id=:tenant AND project_id=:project '
        'AND plan_sha256=:plan'), {**params, 'plan': graph['plan_sha256']}).scalar_one()
    plan = parse_execution_plan(json.dumps(raw))
    policy = PolicyPins.load(conn, params, plan)
    require(policy is not None, 'supervised_run_required')
    row = conn.execute(text('SELECT * FROM runtime.supervision_checkpoints WHERE ' + RUN + ' AND decision_id=:decision'),
                       params).mappings().one_or_none()
    require(row is not None, 'winner_checkpoint_missing')
    slot = StoredCheckpoint.from_row(row, policy)
    require(slot.deadline <= graph['deadline'], 'winner_slot_deadline')
    return slot


@dataclass(frozen=True)
class StoredWinner:
    canonical: bytes
    selection: ScalarSelection | None
    operation_id: str
    created_at: datetime

    def document(self):
        return CheckpointDecision.model_validate_json(self.canonical)

    @classmethod
    def from_row(cls, row, slot):
        canonical = bytes(row['canonical_decision'])
        document = CheckpointDecision.model_validate_json(canonical)
        reference = document.reference
        require(encoded(document) == canonical and hashlib.sha256(canonical).hexdigest() == row['decision_sha256'],
                'stored_winner_bytes')
        require(reference.scope == slot.seed.footprint().cut.scope and reference.run_id == row['run_id'] and
                reference.decision_id == row['decision_id'] == slot.seed.decision_id and
                reference.scope.tenant_id == row['tenant_id'] and reference.scope.project_id == row['project_id'] and
                document.checkpoint_seed_sha256 == slot.seed.sha256 and document.outcome.kind == row['kind'],
                'stored_winner_identity')
        selection = None
        outcome = document.outcome
        if row['canonical_selection'] is not None:
            seed = read_seed(bytes(row['selection_seed']), slot.seed.policy)
            selection = ScalarSelection(bytes(row['canonical_selection']), seed)
            require(seed.decision_id == slot.seed.decision_id and outcome.kind == 'model_accepted' and
                    outcome.effect.kind == 'adjusted_materialization_fields', 'stored_winner_selection')
            effect, selected = outcome.effect, selection.document()
            require(effect.selection_sha256 == selection.sha256 and effect.target == selected.target and
                [(item.field_name, item.previous_value_sha256, item.value) for item in effect.changes] ==
                [(item.name, item.previous_value_sha256, item.value) for item in selected.changes], 'stored_winner_effect')
        else:
            require(row['selection_seed'] is None and (outcome.kind != 'model_accepted' or
                outcome.effect.kind != 'adjusted_materialization_fields'), 'stored_winner_selection_missing')
        require((outcome.kind == 'model_accepted') == (row['response_id'] is not None), 'stored_winner_source')
        if outcome.kind == 'fallback':
            rule = next(item for item in slot.seed.policy.document().checkpoints
                        if item.checkpoint_id == slot.seed.document().checkpoint_id)
            require(outcome.action == rule.fallback, 'stored_winner_fallback')
        return cls(canonical, selection, row['operation_id'], row['created_at'])


class WinnerStore:
    def __init__(self, engine):
        self.leases = RuntimeLeases(engine)

    @staticmethod
    def params(principal, reference):
        reference = SupervisionRef.model_validate_json(reference.model_dump_json())
        require(reference.scope == principal.scope, 'winner_scope_mismatch')
        return {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
                'run': reference.run_id, 'decision': reference.decision_id}

    @staticmethod
    def load(conn, params, slot):
        row = conn.execute(text(WINNER), params).mappings().one_or_none()
        if row is None:
            return None
        winner = StoredWinner.from_row(row, slot)
        if row['response_id'] is not None:
            response_row = conn.execute(text(RESPONSES + ' AND s.response_id=:response AND s.run_id=:run '
                'AND s.decision_id=:decision'), {**params, 'response': row['response_id']}).mappings().one()
            response = StoredResponse.from_row(response_row)
            outcome = winner.document().outcome
            require(outcome.response_sha256 == response.bound.sha256 and
                    outcome.request_sha256 == response.bound.document().request_sha256,
                    'stored_winner_response')
        return winner

    def read(self, principal, reference):
        principal.require('read')
        params = self.params(principal, reference)
        with self.leases.commands.engine.connect() as conn:
            return self.load(conn, params, slot_for(conn, params))

    def resolve(self, principal, reference, *, response_id=None):
        principal.require('supervise_accept')
        params = self.params(principal, reference)

        return self.leases.commands.transact(lambda conn: self.resolve_locked(
            conn, params, reference, response_id=response_id))

    def resolve_locked(self, conn, params, reference, *, response_id=None):
        """Owned transaction composition; caller must authorize the original principal."""
        run = self.leases._run(conn, params)
        slot = slot_for(conn, params)
        previous = self.load(conn, params, slot)
        if previous is not None:
            return previous
        selection = None
        selected_response = None
        if run['status'] != 'running':
            outcome = CheckpointCancelled(kind='cancelled', reason_code='run_' + run['status'])
        else:
            current = current_seed(conn, params, run, slot)
            now = conn.execute(text('SELECT clock_timestamp()')).scalar_one()
            reason = slot.reason_code or ('checkpoint_deadline_exhausted' if now >= slot.deadline else None)
            if reason:
                rule = next(item for item in slot.seed.policy.document().checkpoints
                            if item.checkpoint_id == slot.seed.document().checkpoint_id)
                outcome = CheckpointFallback(kind='fallback', action=rule.fallback, reason_code=reason)
            elif response_id is None:
                return None
            else:
                row = conn.execute(text(RESPONSES + ' AND s.response_id=:response AND s.run_id=:run '
                    'AND s.decision_id=:decision'), {**params, 'response': response_id}).mappings().one_or_none()
                require(row is not None, 'winner_response_missing')
                response = StoredResponse.from_row(row)
                candidate = ModelWinner.bind(conn, params, run, slot, current,
                    read_frame(bytes(row['canonical_frame'])), response)
                outcome, selection, selected_response = candidate.outcome, candidate.selection, response_id
        return self._commit(conn, params, run, slot, reference, outcome, selection, selected_response)

    def _commit(self, conn, params, run, slot, reference, outcome, selection, response_id):
        document = CheckpointDecision(reference=reference, revision=run['revision'] + 1,
                                      checkpoint_seed_sha256=slot.seed.sha256, outcome=outcome)
        canonical = encoded(document)
        operation = 'checkpoint:' + slot.seed.decision_id
        digest = hashlib.sha256(canonical).hexdigest()
        budget = RunBudget(run['budget_limit'], run['reserved'], run['spent'])
        self.leases._changed(conn, params, run, budget, operation,
            {'kind': 'supervision_checkpoint_decided', 'decision_id': slot.seed.decision_id, 'decision_sha256': digest,
             'outcome': outcome.model_dump(mode='json')})
        values = {**params, 'kind': outcome.kind, 'digest': digest, 'canonical': canonical,
            'response': response_id, 'seed': None if selection is None else selection.seed.canonical,
            'selection': None if selection is None else selection.canonical, 'operation': operation}
        row = conn.execute(text('INSERT INTO runtime.supervision_winners '
            '(tenant_id,project_id,run_id,decision_id,kind,decision_sha256,canonical_decision,response_id,'
            'selection_seed,canonical_selection,operation_id) VALUES '
            '(:tenant,:project,:run,:decision,:kind,:digest,:canonical,:response,:seed,:selection,:operation) RETURNING *'),
            values).mappings().one()
        return StoredWinner.from_row(row, slot)
