"""Versioned concrete checkpoint targets; no admission or execution authority."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_core import Identifier
from amphora_contracts_graph_runtime import GraphReadCut
from pydantic import TypeAdapter

from ..compiler.catalog import canonical
from .footprint import ScopeComparison, indexed, run_key
from .observations import NodeObservation, digest, require

_IDENTIFIER = TypeAdapter(Identifier)


@dataclass(frozen=True)
class CheckpointTarget:
    activation_id: str
    kind: str
    fields: tuple[str, ...] = ()

    def __post_init__(self):
        digest(self.activation_id)
        require(self.kind in {'invoke', 'artifact_materialize'}, 'checkpoint_target_kind')
        require(type(self.fields) is tuple, 'checkpoint_fields_immutable')
        require(len(self.fields) <= 64, 'checkpoint_field_count')
        require(all(type(name) is str for name in self.fields), 'checkpoint_field_name')
        for name in self.fields:
            _IDENTIFIER.validate_python(name)
        require(len(set(self.fields)) == len(self.fields), 'duplicate_checkpoint_field')
        require(bool(self.fields) == (self.kind == 'artifact_materialize'), 'checkpoint_fields_for_kind')
        object.__setattr__(self, 'fields', tuple(sorted(self.fields)))

    @classmethod
    def review(cls, observation):
        return cls(observation.identity, 'invoke')

    @classmethod
    def materialize(cls, observation, fields):
        return cls(observation.identity, 'artifact_materialize', fields)

    @property
    def record(self):
        return {'activation_id': self.activation_id, 'kind': self.kind, 'fields': self.fields}

    def verify(self, observation):
        require(observation.identity == self.activation_id and observation.view.kind == self.kind,
                'checkpoint_target_mismatch')
        require(observation.view.status in {'waiting', 'ready'}, 'target_unavailable')


@dataclass(frozen=True)
class CheckpointFootprint:
    cut: GraphReadCut
    checkpoints: tuple[CheckpointTarget, ...]
    observations: tuple[NodeObservation, ...]

    def __post_init__(self):
        cut = GraphReadCut.model_validate_json(self.cut.model_dump_json())
        require(type(self.checkpoints) is tuple and 1 <= len(self.checkpoints) <= 64, 'target_count')
        require(all(type(item) is CheckpointTarget for item in self.checkpoints), 'checkpoint_target_type')
        records = indexed(self.observations, cut.plan_sha256)
        require(len(set(self.targets)) == len(self.checkpoints), 'duplicate_target')
        require(set(self.targets) <= records.keys(), 'target_observation_missing')
        for target in self.checkpoints:
            target.verify(records[target.activation_id])
        object.__setattr__(self, 'cut', cut)
        object.__setattr__(self, 'checkpoints', tuple(sorted(self.checkpoints, key=lambda item: item.activation_id)))
        object.__setattr__(self, 'observations', tuple(records[key] for key in sorted(records)))

    @property
    def targets(self):
        return tuple(item.activation_id for item in self.checkpoints)

    @property
    def record(self):
        return {'profile': 'runtime-supervision-footprint.v2', 'scope': self.cut.scope.model_dump(mode='json'),
                'run_id': self.cut.run_id, 'plan_sha256': self.cut.plan_sha256,
                'checkpoints': tuple(item.record for item in self.checkpoints),
                'reads': tuple(item.identity for item in self.observations)}

    @property
    def sha256(self):
        return hashlib.sha256(canonical(self.record)).hexdigest()

    @property
    def relevant_sha256(self):
        return hashlib.sha256(canonical({'profile': 'runtime-supervision-read-set.v2',
            'footprint_sha256': self.sha256, 'observations': [item.record for item in self.observations]})).hexdigest()

    def overlaps(self, other):
        if run_key(self.cut) != run_key(other.cut):
            return False
        require(self.cut.plan_sha256 == other.cut.plan_sha256, 'run_plan_mismatch')
        # A conversion freezes all fields together: disjoint fields on one node still conflict.
        return bool(set(self.targets).intersection(item.identity for item in other.observations) or
                    set(other.targets).intersection(item.identity for item in self.observations))

    def compare(self, current_cut, observations):
        current = GraphReadCut.model_validate_json(current_cut.model_dump_json())
        require(run_key(current) == run_key(self.cut) and current.plan_sha256 == self.cut.plan_sha256,
                'current_cut_mismatch')
        require(current.revision >= self.cut.revision and current.frontier_revision >= self.cut.frontier_revision,
                'older_current_cut')
        require(type(observations) is tuple, 'observation_count')
        records = indexed(observations, current.plan_sha256) if observations else {}
        return ScopeComparison(
            tuple(item.identity for item in self.observations if item.identity not in records),
            tuple(item.identity for item in self.observations
                  if item.identity in records and item.sha256 != records[item.identity].sha256))
