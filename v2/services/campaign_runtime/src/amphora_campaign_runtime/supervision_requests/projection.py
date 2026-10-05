"""Project owned byte observations, never infer ownership from received hashes."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_supervision import SupervisionNodeRead, SupervisionSnapshot

from ..supervision_scope import DecisionFootprint


@dataclass(frozen=True)
class ScopeExport:
    footprint: DecisionFootprint

    def document(self):
        reads = tuple(SupervisionNodeRead(node=item.view,
            state_sha256=hashlib.sha256(item.state_json).hexdigest(),
            outputs_sha256=hashlib.sha256(item.outputs_json).hexdigest())
            for item in self.footprint.observations)
        return SupervisionSnapshot(cut=self.footprint.cut, targets=self.footprint.targets, reads=reads,
            footprint_sha256=self.footprint.sha256, relevant_sha256=self.footprint.relevant_sha256)
