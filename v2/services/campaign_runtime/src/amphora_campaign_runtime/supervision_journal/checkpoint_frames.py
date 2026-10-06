"""Explicit v2 retained frames, separate from the original v1 parser."""

from typing import Literal

from amphora_contracts_supervision import CheckpointRequest

from ..supervision_requests.binding import CheckpointRequestBinding
from ..supervision_scope import NodeObservation
from ..supervision_scope.checkpoints import CheckpointFootprint, CheckpointTarget
from ..supervision_scope.observations import require
from .frames import FrameRecord, RequestFrame, decode


class CheckpointFrameRecord(FrameRecord):
    profile: Literal['runtime-supervision-request-frame.v2']
    request: CheckpointRequest


class CheckpointFrame(RequestFrame):
    record_type = CheckpointFrameRecord
    binding_type = CheckpointRequestBinding
    profile = 'runtime-supervision-request-frame.v2'

    def footprint(self):
        record = self.document()
        snapshot = record.request.snapshot
        observations = tuple(NodeObservation(snapshot.cut.plan_sha256, item.node,
            decode(item.state), decode(item.outputs)) for item in record.observations)
        targets = tuple(CheckpointTarget(item.activation_id, item.kind, item.fields)
                        for item in snapshot.checkpoints)
        result = CheckpointFootprint(snapshot.cut, targets, observations)
        require(tuple(item.identity for item in result.observations) ==
                tuple(item.node.activation_id for item in record.observations), 'observation_order')
        return result
