"""Byte-owned original observations survive mutable Runtime projections."""

import base64
import hashlib
from dataclasses import dataclass
from typing import Annotated, Literal

from amphora_contracts_core import Identifier, WireModel
from amphora_contracts_graph_runtime import GraphNodeViewV3
from amphora_contracts_supervision import SupervisionRequest
from pydantic import Field

from ..supervision_requests import SupervisionRequestBinding
from ..supervision_requests.binding import encoded
from ..supervision_scope import DecisionFootprint, NodeObservation
from ..supervision_scope.observations import require


class StoredObservation(WireModel):
    node: GraphNodeViewV3
    state: str
    outputs: str


class FrameRecord(WireModel):
    profile: Literal['runtime-supervision-request-frame.v1']
    prepared_by: Identifier
    request: SupervisionRequest
    observations: Annotated[tuple[StoredObservation, ...], Field(min_length=1, max_length=256)]


def decode(value):
    raw = base64.b64decode(value, validate=True)
    require(base64.b64encode(raw).decode('ascii') == value, 'noncanonical_base64')
    return raw


@dataclass(frozen=True)
class RequestFrame:
    canonical: bytes

    def __post_init__(self):
        require(type(self.canonical) is bytes and len(self.canonical) <= 16777216, 'frame_size')
        record = FrameRecord.model_validate_json(self.canonical)
        # Exact reserialization also rejects duplicates, whitespace and alternate numeric spellings.
        require(encoded(record) == self.canonical, 'noncanonical_frame')
        footprint = self.footprint()
        SupervisionRequestBinding.bind(record.request, footprint,
                                      actor_id=record.request.planning_request.actor_id)

    @classmethod
    def capture(cls, request, footprint, *, prepared_by, planning_actor):
        bound = SupervisionRequestBinding.bind(request, footprint, actor_id=planning_actor)
        observations = tuple(StoredObservation(node=item.view,
            state=base64.b64encode(item.state_json).decode('ascii'),
            outputs=base64.b64encode(item.outputs_json).decode('ascii')) for item in footprint.observations)
        return cls(encoded(FrameRecord(profile='runtime-supervision-request-frame.v1',
            prepared_by=prepared_by, request=bound.document(), observations=observations)))

    @classmethod
    def from_bytes(cls, raw):
        return cls(raw)

    def document(self):
        return FrameRecord.model_validate_json(self.canonical)

    def footprint(self):
        record = self.document()
        snapshot = record.request.snapshot
        observations = tuple(NodeObservation(snapshot.cut.plan_sha256, item.node,
            decode(item.state), decode(item.outputs)) for item in record.observations)
        result = DecisionFootprint(snapshot.cut, snapshot.targets, observations)
        require(tuple(item.identity for item in result.observations) ==
                tuple(item.node.activation_id for item in record.observations), 'observation_order')
        return result

    @property
    def request(self):
        return self.document().request

    @property
    def request_sha256(self):
        return hashlib.sha256(encoded(self.request)).hexdigest()

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
