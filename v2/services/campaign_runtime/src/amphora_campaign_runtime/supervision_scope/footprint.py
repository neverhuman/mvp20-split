"""Read/write interference and selected-node staleness without execution authority."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_graph_runtime import GraphReadCut

from ..compiler.catalog import canonical
from .observations import NodeObservation, digest, require


def indexed(observations, plan):
    require(type(observations) is tuple and 1 <= len(observations) <= 256, 'observation_count')
    require(all(isinstance(item, NodeObservation) for item in observations), 'observation_type')
    require(all(item.plan_sha256 == plan for item in observations), 'observation_plan_mismatch')
    result = {item.identity: item for item in observations}
    require(len(result) == len(observations), 'duplicate_observation')
    require(sum(len(item.state_json) + len(item.outputs_json) for item in observations) <= 8388608,
            'scope_observation_limit')
    return result


def run_key(cut):
    return cut.scope.tenant_id, cut.scope.project_id, cut.run_id


@dataclass(frozen=True)
class ScopeComparison:
    missing: tuple[str, ...]
    changed: tuple[str, ...]

    @property
    def stale(self):
        return bool(self.missing or self.changed)


@dataclass(frozen=True)
class DecisionFootprint:
    cut: GraphReadCut
    targets: tuple[str, ...]
    observations: tuple[NodeObservation, ...]

    def __post_init__(self):
        cut = GraphReadCut.model_validate_json(self.cut.model_dump_json())
        require(type(self.targets) is tuple and 1 <= len(self.targets) <= 64, 'target_count')
        for target in self.targets:
            digest(target)
        require(len(set(self.targets)) == len(self.targets), 'duplicate_target')
        records = indexed(self.observations, cut.plan_sha256)
        require(set(self.targets) <= records.keys(), 'target_observation_missing')
        require(all(records[target].target_available for target in self.targets), 'target_unavailable')
        object.__setattr__(self, 'cut', cut)
        object.__setattr__(self, 'targets', tuple(sorted(self.targets)))
        object.__setattr__(self, 'observations', tuple(records[key] for key in sorted(records)))

    @property
    def record(self):
        return {'profile': 'runtime-supervision-footprint.v1', 'scope': self.cut.scope.model_dump(mode='json'),
                'run_id': self.cut.run_id, 'plan_sha256': self.cut.plan_sha256,
                'targets': self.targets, 'reads': tuple(item.identity for item in self.observations)}

    @property
    def sha256(self):
        """Conflict identity; distinct from Planning's reviewed declaration digest."""
        return hashlib.sha256(canonical(self.record)).hexdigest()

    @property
    def relevant_sha256(self):
        return hashlib.sha256(canonical({'profile': 'runtime-supervision-read-set.v1',
            'footprint_sha256': self.sha256, 'observations': [item.record for item in self.observations]})).hexdigest()

    def overlaps(self, other):
        if run_key(self.cut) != run_key(other.cut):
            return False
        require(self.cut.plan_sha256 == other.cut.plan_sha256, 'run_plan_mismatch')
        ours, theirs = set(self.targets), set(other.targets)
        return bool(ours.intersection(item.identity for item in other.observations) or
                    theirs.intersection(item.identity for item in self.observations))

    def compare(self, current_cut, observations):
        current = GraphReadCut.model_validate_json(current_cut.model_dump_json())
        require(run_key(current) == run_key(self.cut) and current.plan_sha256 == self.cut.plan_sha256,
                'current_cut_mismatch')
        require(current.revision >= self.cut.revision and current.frontier_revision >= self.cut.frontier_revision,
                'older_current_cut')
        # An empty projection is meaningful: every selected record is now missing.
        require(type(observations) is tuple, 'observation_count')
        records = indexed(observations, current.plan_sha256) if observations else {}
        missing = tuple(item.identity for item in self.observations if item.identity not in records)
        changed = tuple(item.identity for item in self.observations
                        if item.identity in records and item.sha256 != records[item.identity].sha256)
        return ScopeComparison(missing, changed)
