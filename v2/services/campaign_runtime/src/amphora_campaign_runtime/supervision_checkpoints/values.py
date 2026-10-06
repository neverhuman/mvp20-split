"""Versioned original scalar fields; neither an adjustment nor a schema bypass."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_graph_runtime import GraphBinding
from pydantic import Field

from ..compiler.catalog import canonical
from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require
from .seed import CheckpointSeed, SeedRecord


class ValueSeedRecord(SeedRecord):
    profile: Literal['runtime-supervision-checkpoint.v2'] = 'runtime-supervision-checkpoint.v2'
    original_fields: Annotated[tuple[GraphBinding, ...], Field(max_length=64)]


class ValueCheckpointSeed(CheckpointSeed):
    record_type = ValueSeedRecord

    def __post_init__(self):
        super().__post_init__()
        record = self.document()
        rule = next(item for item in self.policy.document().checkpoints if item.checkpoint_id == record.checkpoint_id)
        expected = {field.name: field.value_type for field in rule.fields}
        require(tuple(value.port for value in record.original_fields) == tuple(sorted(expected)), 'checkpoint_original_fields')
        for binding in record.original_fields:
            shape, value = expected[binding.port], binding.value
            require(value.kind in {'boolean', 'integer', 'number', 'string'} and
                    (value.kind == shape.scalar or (shape.scalar == 'number' and value.kind == 'integer')) and
                    getattr(value, 'unit', '1') == shape.unit, 'checkpoint_original_scalar_type')

    @classmethod
    def capture(cls, policy, footprint, original_fields):
        base = CheckpointSeed.capture(policy, footprint).document()
        record = ValueSeedRecord(profile='runtime-supervision-checkpoint.v2', policy_sha256=base.policy_sha256,
            checkpoint_id=base.checkpoint_id, snapshot=base.snapshot, observations=base.observations,
            original_fields=tuple(sorted(original_fields, key=lambda item: item.port)))
        return cls(encoded(record), policy)

    @property
    def original_fields_sha256(self):
        return hashlib.sha256(canonical([value.model_dump(mode='json') for value in self.document().original_fields])).hexdigest()


def read_seed(raw, policy):
    require(type(raw) is bytes and 0 < len(raw) <= 16777216, 'checkpoint_seed_size')
    record = json.loads(raw)
    require(type(record) is dict, 'checkpoint_seed_profile')
    model = {'runtime-supervision-checkpoint.v1': CheckpointSeed,
             'runtime-supervision-checkpoint.v2': ValueCheckpointSeed}.get(record.get('profile'))
    require(model is not None, 'checkpoint_seed_profile')
    return model(raw, policy)
