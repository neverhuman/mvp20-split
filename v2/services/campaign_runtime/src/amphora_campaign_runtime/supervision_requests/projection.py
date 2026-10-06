"""Project owned byte observations, never infer ownership from received hashes."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_supervision import (
    CheckpointSnapshot,
    SupervisionNodeRead,
    SupervisionSnapshot,
)

from ..supervision_scope import DecisionFootprint
from ..supervision_scope.checkpoints import CheckpointFootprint
from ..supervision_scope.observations import require


@dataclass(frozen=True)
class ScopeExport:
    footprint: DecisionFootprint

    def document(self):
        require(type(self.footprint) is DecisionFootprint, 'scope_profile_mismatch')
        reads = tuple(SupervisionNodeRead(node=item.view,
            state_sha256=hashlib.sha256(item.state_json).hexdigest(),
            outputs_sha256=hashlib.sha256(item.outputs_json).hexdigest())
            for item in self.footprint.observations)
        return SupervisionSnapshot(cut=self.footprint.cut, targets=self.footprint.targets, reads=reads,
            footprint_sha256=self.footprint.sha256, relevant_sha256=self.footprint.relevant_sha256)


@dataclass(frozen=True)
class CheckpointExport:
    footprint: CheckpointFootprint

    def document(self):
        require(type(self.footprint) is CheckpointFootprint, 'scope_profile_mismatch')
        reads = tuple(SupervisionNodeRead(node=item.view,
            state_sha256=hashlib.sha256(item.state_json).hexdigest(),
            outputs_sha256=hashlib.sha256(item.outputs_json).hexdigest())
            for item in self.footprint.observations)
        return CheckpointSnapshot(cut=self.footprint.cut,
            checkpoints=tuple(item.record for item in self.footprint.checkpoints), reads=reads,
            footprint_sha256=self.footprint.sha256, relevant_sha256=self.footprint.relevant_sha256)
