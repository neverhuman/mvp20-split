"""Graph revision alone does not capture newly received supervisor history."""

import hashlib
import json
from dataclasses import dataclass, replace

from amphora_contracts_supervision import SupervisionInspectionCut
from sqlalchemy import text

from ..graph_inspection.policy import ObservedCut, require
from ..inspection.cursors import CursorCodec, PagePosition
from ..lifecycle.claims import RUN
from ..supervision_requests.binding import encoded

TABLES = ('supervision_checkpoints', 'supervision_requests', 'supervision_responses',
          'supervision_execution_reports', 'supervision_request_dispositions', 'supervision_winners')
SNAPSHOT = 'supervisor-inspection-snapshot.v1'


@dataclass(frozen=True)
class InspectionWindow:
    cut: ObservedCut
    epoch: str
    snapshot: PagePosition
    cursors: CursorCodec

    @classmethod
    def load(cls, conn, principal, run_id, cursors, snapshot_token=None):
        cut = ObservedCut.load(conn, principal, run_id)
        counts = [conn.execute(text('SELECT count(*) FROM runtime.' + table + ' WHERE ' + RUN), cut.params).scalar_one()
                  for table in TABLES]
        epoch = hashlib.sha256(encoded(cut.to_wire()) + b'\n' +
                               json.dumps(counts, separators=(',', ':')).encode()).hexdigest()
        snapshot = cut.position(cursors, snapshot_token, SNAPSHOT, after=(0, 0, epoch))
        require(snapshot.after == (0, 0, epoch))
        return cls(cut, epoch, snapshot, cursors)

    def page(self, mode, resource, cursor, limit):
        require(type(limit) is int and 1 <= limit <= 10, 'invalid_page_request')
        position = (self.cursors.decode(cursor, mode=mode, scope=self.cut.scope, resource=resource) if cursor else
                    replace(self.snapshot, mode=mode, resource=resource, after=(0, 0, self.epoch)))
        require(position.revision == self.cut.revision and position.after[2] == self.epoch)
        require(position.after[0] >= 0 and position.after[1] == 0, 'invalid_cursor')
        return position

    def wire(self, position):
        snapshot = replace(self.snapshot, expires=min(self.snapshot.expires, position.expires))
        return SupervisionInspectionCut(cut=self.cut.to_wire(), epoch=self.epoch,
                                        snapshot_token=self.cursors.encode(snapshot))

    def next(self, position, visible, total):
        offset = position.after[0] + visible
        require(offset <= total, 'invalid_page_request')
        return None if offset == total else self.cursors.encode(position.advance((offset, 0, self.epoch)))
