"""Short run transactions around guarded context publication, then atomic request creation."""

import json

from amphora_contracts_supervision import SupervisionRef, parse_checkpoint_command
from sqlalchemy import text

from ..lifecycle.claims import RUN
from ..supervision_journal.current import verify_footprint
from ..supervision_journal.series import RequestSeries
from ..supervision_journal.storage import SELECT, RequestJournal, StoredRequest
from ..supervision_preparation import CallReservations, RequestCharge
from ..supervision_preparation.storage import RecipePins
from ..supervision_scope.observations import digest, require
from ..supervision_winners.current import current_seed
from ..supervision_winners.storage import slot_for
from .basis import ContextBasis
from .publication import ContextPublisher
from .session import ContextSession


class PreparedElsewhere(Exception):
    def __init__(self, original):
        self.original = original


def replay(previous, parent):
    if parent is None:
        return previous[0] if previous else None
    index = next((index for index, item in enumerate(previous) if item.frame.request_sha256 == parent), None)
    require(index is not None, 'context_parent_missing')
    return previous[index + 1] if index + 1 < len(previous) else None


class ContextPreparer:
    def __init__(self, engine, planning_actors, artifacts):
        self.journal = RequestJournal(engine, planning_actors)
        self.publisher = ContextPublisher(artifacts)

    def prepare(self, principal, reference, *, parent_request_sha256=None):
        principal.require('supervise_prepare')
        reference = SupervisionRef.model_validate_json(reference.model_dump_json())
        require(reference.scope == principal.scope, 'context_preparer_scope')
        if parent_request_sha256 is not None:
            digest(parent_request_sha256)
        key = (principal.scope.tenant_id, principal.scope.project_id, principal.actor_id)
        actor = self.journal.planning_actors.get(key)
        require(actor is not None, 'planning_delegation_unavailable')
        params = self.journal.params(principal, reference.run_id, reference.decision_id)

        def select(conn, expected=None):
            run = self.journal.leases._run(conn, params)
            rows = conn.execute(text(SELECT + ' ORDER BY r.ordinal'), params).mappings().all()
            previous = tuple(StoredRequest.from_row(row) for row in rows)
            if previous:
                RequestSeries(tuple(item.frame for item in previous))
                require(all(item.frame.document().prepared_by == principal.actor_id and
                            item.frame.request.planning_request.actor_id == actor for item in previous),
                        'context_preparer_identity')
            original = replay(previous, parent_request_sha256)
            if original is not None:
                return original
            slot = slot_for(conn, params)
            require(slot.seed.policy.document().profile == 'runtime-supervision-policy.v2', 'autonomous_recipe_required')
            require(slot.eligibility == 'requestable', 'context_checkpoint_ineligible')
            require(conn.execute(text('SELECT clock_timestamp() < :deadline'), {'deadline': slot.deadline}).scalar_one(),
                    'context_checkpoint_expired')
            require(conn.execute(text('SELECT 1 FROM runtime.supervision_winners WHERE ' + RUN +
                ' AND decision_id=:decision'), params).first() is None, 'context_terminal_winner')
            current = current_seed(conn, params, run, slot)
            require(current.document().original_fields == slot.seed.document().original_fields, 'context_original_fields_changed')
            if expected is not None:
                verify_footprint(conn, params, run, expected.basis.seed.footprint())
            recipe = RecipePins.load(conn, params, slot.seed.policy)
            charges = conn.execute(text('SELECT decision_id,request_sha256,max_attempts '
                'FROM runtime.supervision_call_reservations WHERE ' + RUN + ' ORDER BY decision_id,request_sha256'),
                params).mappings().all()
            history = CallReservations(tuple(RequestCharge(row['decision_id'], row['request_sha256'], row['max_attempts'])
                                             for row in charges))
            return ContextSession(ContextBasis(current, recipe, history, int(slot.deadline.timestamp() * 1000)),
                                  tuple(item.frame for item in previous), actor)

        selected = self.journal.leases.commands.transact(select)
        if isinstance(selected, StoredRequest):
            return selected

        def guard():
            result = self.journal.leases.commands.transact(lambda conn: select(conn, selected))
            if isinstance(result, StoredRequest):
                raise PreparedElsewhere(result)

        try:
            frame = self.publisher.prepare(selected, prepared_by=principal.actor_id, guard=guard)
            command = parse_checkpoint_command(json.dumps({'encoding': 'amphora-command-v2', 'identity': {
                'scope': principal.scope.model_dump(mode='json'), 'actor_id': actor,
                'command_family': 'planning.supervision.request.v2', 'command_id': frame.request_sha256},
                'payload': frame.request.model_dump(mode='json')}))
            try:
                return self.journal.prepare(principal, frame, command.canonical_bytes)
            except ValueError as error:
                if str(error) != 'request_identity_conflict':
                    raise
                original = self.journal.leases.commands.transact(select)
                require(isinstance(original, StoredRequest), 'context_race_without_original')
                return original
        except PreparedElsewhere as replayed:
            return replayed.original
