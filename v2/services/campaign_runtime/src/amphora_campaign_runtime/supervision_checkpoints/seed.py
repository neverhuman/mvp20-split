"""Immutable concrete occurrence and selected observations before context preparation."""

import base64
import hashlib
from dataclasses import dataclass
from typing import Annotated, ClassVar, Literal

from amphora_contracts_core import Digest, Identifier, WireModel
from amphora_contracts_supervision import CheckpointSnapshot
from pydantic import Field

from ..compiler.addresses import ActivationAddress
from ..compiler.catalog import canonical
from ..supervision_journal.frames import StoredObservation, decode
from ..supervision_policy import ReviewedPolicy
from ..supervision_requests.binding import encoded
from ..supervision_requests.projection import CheckpointExport
from ..supervision_scope import NodeObservation
from ..supervision_scope.checkpoints import CheckpointFootprint, CheckpointTarget
from ..supervision_scope.observations import require


class SeedRecord(WireModel):
    profile: Literal['runtime-supervision-checkpoint.v1'] = 'runtime-supervision-checkpoint.v1'
    policy_sha256: Digest
    checkpoint_id: Identifier
    snapshot: CheckpointSnapshot
    observations: Annotated[tuple[StoredObservation, ...], Field(min_length=1, max_length=256)]


@dataclass(frozen=True)
class CheckpointSeed:
    canonical: bytes
    policy: ReviewedPolicy
    record_type: ClassVar = SeedRecord

    def __post_init__(self):
        require(type(self.canonical) is bytes and 0 < len(self.canonical) <= 16777216, 'checkpoint_seed_size')
        record = self.document()
        require(encoded(record) == self.canonical, 'noncanonical_checkpoint_seed')
        footprint = self.footprint()
        require(CheckpointExport(footprint).document() == record.snapshot, 'checkpoint_seed_snapshot')
        require(len(footprint.checkpoints) == 1, 'checkpoint_seed_target_count')
        policy = self.policy.document()
        require(record.policy_sha256 == self.policy.sha256 and footprint.cut.scope == policy.scope and
                footprint.cut.plan_sha256 == policy.plan_sha256, 'checkpoint_seed_policy')
        target = footprint.checkpoints[0]
        path = next(item.view.path for item in footprint.observations if item.identity == target.activation_id)
        rule = self.policy.rule_for(path)
        require(rule is not None and rule.checkpoint_id == record.checkpoint_id and rule.kind == target.kind and
                tuple(sorted(field.name for field in rule.fields)) == target.fields, 'checkpoint_seed_rule')
        reads = {ActivationAddress.for_plan(self.policy.plan, item).key for item in self.policy.read_paths(path)}
        require(reads == {item.identity for item in footprint.observations}, 'checkpoint_seed_reads')

    @classmethod
    def capture(cls, policy, footprint):
        require(len(footprint.checkpoints) == 1, 'checkpoint_seed_target_count')
        path = next(item.view.path for item in footprint.observations if item.identity == footprint.targets[0])
        rule = policy.rule_for(path)
        require(rule is not None, 'checkpoint_seed_rule')
        observations = tuple(StoredObservation(node=item.view,
            state=base64.b64encode(item.state_json).decode('ascii'),
            outputs=base64.b64encode(item.outputs_json).decode('ascii')) for item in footprint.observations)
        return cls(encoded(SeedRecord(policy_sha256=policy.sha256, checkpoint_id=rule.checkpoint_id,
            snapshot=CheckpointExport(footprint).document(), observations=observations)), policy)

    def document(self):
        return self.record_type.model_validate_json(self.canonical)

    def footprint(self):
        record = self.document()
        observations = tuple(NodeObservation(record.snapshot.cut.plan_sha256, item.node,
            decode(item.state), decode(item.outputs)) for item in record.observations)
        targets = tuple(CheckpointTarget(item.activation_id, item.kind, item.fields) for item in record.snapshot.checkpoints)
        footprint = CheckpointFootprint(record.snapshot.cut, targets, observations)
        require(tuple(item.identity for item in footprint.observations) ==
                tuple(item.node.activation_id for item in record.observations), 'checkpoint_seed_observation_order')
        return footprint

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    @property
    def decision_id(self):
        record = self.document()
        cut = record.snapshot.cut
        return hashlib.sha256(canonical({'profile': 'runtime-supervision-checkpoint-identity.v1',
            'scope': cut.scope.model_dump(mode='json'), 'run_id': cut.run_id, 'plan_sha256': cut.plan_sha256,
            'policy_sha256': record.policy_sha256, 'checkpoint_id': record.checkpoint_id,
            'activation_id': record.snapshot.checkpoints[0].activation_id})).hexdigest()
