"""Run-locked recipe/request reservation boundary; no independent transaction or I/O."""

from sqlalchemy import text

from ..lifecycle.claims import RUN
from ..supervision_policy.records import read_policy
from ..supervision_scope.observations import require
from .reservations import CallReservations, RequestCharge
from .storage import RecipePins


class RequestReservation:
    @staticmethod
    def prepare(conn, params, frame):
        # Legacy/manual policies retain their existing request behavior.
        raw = conn.execute(text('SELECT canonical_policy FROM runtime.supervision_policies WHERE ' + RUN),
                           params).scalar_one_or_none()
        if raw is None or read_policy(bytes(raw)).profile == 'runtime-supervision-policy.v1':
            return None
        from ..supervision_winners.storage import slot_for
        slot = slot_for(conn, params)
        policy = slot.seed.policy
        request = frame.request
        require(request.schema_version == '2' and request.checkpoint_id == slot.seed.document().checkpoint_id and
                frame.footprint().sha256 == slot.seed.footprint().sha256, 'reservation_checkpoint_binding')
        require(request.policy.sha256 == policy.sha256, 'reservation_policy_binding')
        require(slot.eligibility == 'requestable' and request.deadline_unix_ms <= int(slot.deadline.timestamp() * 1000),
                'reservation_checkpoint_deadline')
        require(conn.execute(text('SELECT 1 FROM runtime.supervision_winners WHERE ' + RUN +
            ' AND decision_id=:decision'), params).first() is None, 'reservation_terminal_winner')
        recipe = RecipePins.load(conn, params, policy)
        recipe.require_context(request.planning_request.context, request.planning_request.decision_scope)
        rows = conn.execute(text('SELECT decision_id,request_sha256,max_attempts FROM runtime.supervision_call_reservations '
                                 'WHERE ' + RUN + ' ORDER BY decision_id,request_sha256'), params).mappings().all()
        # Never infer unrecorded historical reservations or silently undercount them.
        count = conn.execute(text('SELECT count(*) FROM runtime.supervision_requests WHERE ' + RUN), params).scalar_one()
        require(count == len(rows), 'reservation_history_incomplete')
        history = CallReservations(tuple(RequestCharge(row['decision_id'], row['request_sha256'], row['max_attempts'])
                                         for row in rows))
        charge = RequestCharge(request.reference.decision_id, frame.request_sha256, request.planning_request.context.limits.max_attempts)
        rule = next(item for item in policy.document().checkpoints if item.checkpoint_id == request.checkpoint_id)
        history.reserve(charge, rule=rule, ceilings=policy.document().ceilings)
        return charge

    @staticmethod
    def persist(conn, params, charge):
        if charge is None:
            return
        conn.execute(text('INSERT INTO runtime.supervision_call_reservations '
            '(tenant_id,project_id,run_id,decision_id,request_sha256,max_attempts) '
            'VALUES (:tenant,:project,:run,:decision,:request,:attempts)'),
            {**params, 'decision': charge.decision_id, 'request': charge.request_sha256, 'attempts': charge.max_attempts})
