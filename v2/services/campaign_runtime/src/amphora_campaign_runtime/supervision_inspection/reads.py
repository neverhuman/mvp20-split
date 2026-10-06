"""Four bounded coherent metadata pages; no mutation, raw payload or peer I/O."""

from amphora_contracts_supervision import (
    CheckpointContextPage,
    CheckpointInspectionPage,
    CheckpointRequestPage,
    CheckpointResponsePage,
    IncludedCheckpointContext,
    OmittedCheckpointContext,
    SupervisionRef,
)
from sqlalchemy import text

from ..graph_inspection.policy import read_transaction, require
from ..lifecycle.claims import RUN
from ..supervision_journal.responses import RESPONSES, StoredResponse
from ..supervision_journal.storage import SELECT, StoredRequest
from ..supervision_winners.storage import WinnerStore, slot_for
from .projections import CheckpointProjection, RequestProjection, ResponseProjection
from .sources import original_request, request_details
from .window import InspectionWindow


def count(conn, table, params, predicate=RUN):
    return conn.execute(text('SELECT count(*) FROM runtime.' + table + ' WHERE ' + predicate), params).scalar_one()


class SupervisorInspection:
    def __init__(self, engine, cursors):
        self.engine, self.cursors = engine, cursors

    def checkpoints(self, principal, run_id, *, limit=10, cursor=None):
        with read_transaction(self.engine) as conn:
            window = InspectionWindow.load(conn, principal, run_id, self.cursors)
            position = window.page('supervisor-checkpoints.v1', run_id, cursor, limit)
            params = {**window.cut.params, 'offset': position.after[0], 'limit': limit}
            total = count(conn, 'supervision_checkpoints', params)
            rows = conn.execute(text('SELECT decision_id FROM runtime.supervision_checkpoints WHERE ' + RUN +
                ' ORDER BY ordinal,decision_id OFFSET :offset LIMIT :limit'), params).mappings().all()
            items = []
            for row in rows:
                selected = {**params, 'decision': row['decision_id']}
                slot = slot_for(conn, selected)
                winner = WinnerStore.load(conn, selected, slot)
                requests = count(conn, 'supervision_requests', selected, RUN + ' AND decision_id=:decision')
                items.append(CheckpointProjection(slot, winner, requests).to_wire())
            return CheckpointInspectionPage(snapshot=window.wire(position), total=total, items=tuple(items),
                                            next_cursor=window.next(position, len(items), total))

    def _window(self, conn, principal, run_id, decision_id, snapshot_token):
        require(isinstance(snapshot_token, str) and bool(snapshot_token), 'invalid_page_request')
        window = InspectionWindow.load(conn, principal, run_id, self.cursors, snapshot_token)
        params = {**window.cut.params, 'decision': decision_id}
        exists = conn.execute(text('SELECT 1 FROM runtime.supervision_checkpoints WHERE ' + RUN +
            ' AND decision_id=:decision'), params).first()
        require(exists is not None, 'supervision_checkpoint_unavailable')
        return window, params, SupervisionRef(scope=principal.scope, run_id=run_id, decision_id=decision_id)

    def requests(self, principal, run_id, decision_id, *, snapshot_token, limit=10, cursor=None):
        with read_transaction(self.engine) as conn:
            window, params, reference = self._window(conn, principal, run_id, decision_id, snapshot_token)
            position = window.page('supervisor-requests.v1', run_id + '/' + decision_id, cursor, limit)
            params.update(offset=position.after[0], limit=limit)
            predicate = RUN + ' AND decision_id=:decision'
            total = count(conn, 'supervision_requests', params, predicate)
            rows = conn.execute(text(SELECT + ' ORDER BY r.ordinal OFFSET :offset LIMIT :limit'), params).mappings().all()
            items = []
            for row in rows:
                original = StoredRequest.from_row(row)
                selected = {**params, 'request': original.frame.request_sha256}
                report, disposition = request_details(conn, selected, original)
                responses = count(conn, 'supervision_responses', selected, predicate + ' AND request_sha256=:request')
                items.append(RequestProjection(original, report, disposition, responses).to_wire())
            return CheckpointRequestPage(snapshot=window.wire(position), reference=reference,
                total=total, items=tuple(items), next_cursor=window.next(position, len(items), total))

    def context(self, principal, run_id, decision_id, request_sha256, *, snapshot_token, limit=10, cursor=None):
        with read_transaction(self.engine) as conn:
            window, params, reference = self._window(conn, principal, run_id, decision_id, snapshot_token)
            position = window.page('supervisor-context.v1', f'{run_id}/{decision_id}/{request_sha256}', cursor, limit)
            original = original_request(conn, {**params, 'request': request_sha256})
            context = original.frame.request.planning_request.context
            records = tuple(IncludedCheckpointContext(kind='included', entry=entry) for entry in context.entries) + tuple(
                OmittedCheckpointContext(kind='omitted', omission=item) for item in context.omissions)
            items = records[position.after[0]:position.after[0] + limit]
            return CheckpointContextPage(snapshot=window.wire(position), reference=reference,
                request_sha256=request_sha256, total=len(records), items=items,
                next_cursor=window.next(position, len(items), len(records)))

    def responses(self, principal, run_id, decision_id, request_sha256, *, snapshot_token, limit=10, cursor=None):
        with read_transaction(self.engine) as conn:
            window, params, reference = self._window(conn, principal, run_id, decision_id, snapshot_token)
            position = window.page('supervisor-responses.v1', f'{run_id}/{decision_id}/{request_sha256}', cursor, limit)
            params.update(request=request_sha256, offset=position.after[0], limit=limit)
            original_request(conn, params)
            slot = slot_for(conn, params)
            winner = WinnerStore.load(conn, params, slot)
            total = count(conn, 'supervision_responses', params, RUN + ' AND decision_id=:decision AND request_sha256=:request')
            rows = conn.execute(text(RESPONSES + ' AND s.run_id=:run AND s.decision_id=:decision '
                'AND s.request_sha256=:request ORDER BY s.sequence,s.response_id OFFSET :offset LIMIT :limit'),
                params).mappings().all()
            items = tuple(ResponseProjection(StoredResponse.from_row(row), winner).to_wire() for row in rows)
            return CheckpointResponsePage(snapshot=window.wire(position), reference=reference,
                request_sha256=request_sha256, total=total, items=items,
                next_cursor=window.next(position, len(items), total))
