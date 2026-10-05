"""Byte-owned observations of concrete Runtime nodes, separate from global cuts."""

import hashlib
import json
import re
from dataclasses import dataclass

from amphora_contracts_graph_runtime import GraphNodeViewV3

from ..compiler.addresses import ActivationAddress
from ..compiler.catalog import canonical


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None, 'invalid_digest')
    return value


def json_bytes(value):
    """Reject non-JSON keys/types before serialization can silently coerce them."""
    if isinstance(value, dict):
        require(all(type(key) is str for key in value), 'non_string_json_key')
        for item in value.values():
            json_bytes(item)
    elif isinstance(value, list):
        for item in value:
            json_bytes(item)
    else:
        require(value is None or type(value) in (str, int, float, bool), 'unsupported_json_value')
    return canonical(value)


@dataclass(frozen=True)
class NodeObservation:
    plan_sha256: str
    view: GraphNodeViewV3
    state_json: bytes
    outputs_json: bytes

    def __post_init__(self):
        digest(self.plan_sha256)
        view = GraphNodeViewV3.model_validate_json(self.view.model_dump_json())
        require(ActivationAddress(self.plan_sha256, view.path).key == view.activation_id,
                'activation_identity_mismatch')
        require(type(self.state_json) is bytes and type(self.outputs_json) is bytes, 'immutable_bytes_required')
        require(len(self.state_json) + len(self.outputs_json) <= 1048576, 'node_observation_limit')
        for raw in (self.state_json, self.outputs_json):
            require(json_bytes(json.loads(raw)) == raw, 'noncanonical_observation')
        object.__setattr__(self, 'view', view)

    @classmethod
    def capture(cls, plan_sha256, view, *, state, outputs):
        return cls(plan_sha256, view, json_bytes(state), json_bytes(outputs))

    @property
    def identity(self):
        return self.view.activation_id

    @property
    def record(self):
        return {'profile': 'runtime-supervision-node.v1', 'plan_sha256': self.plan_sha256,
                'node': self.view.model_dump(mode='json'),
                'state_sha256': hashlib.sha256(self.state_json).hexdigest(),
                'outputs_sha256': hashlib.sha256(self.outputs_json).hexdigest()}

    @property
    def sha256(self):
        return hashlib.sha256(canonical(self.record)).hexdigest()

    @property
    def target_available(self):
        # The owning transaction must additionally prove no materialized worker row.
        return self.view.kind == 'invoke' and self.view.status in {'waiting', 'ready'}
