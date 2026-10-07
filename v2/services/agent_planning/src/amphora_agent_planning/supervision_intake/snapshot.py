"""Planning validates its original context; Runtime observations remain owner claims."""

import hashlib
import json
from dataclasses import dataclass
from typing import ClassVar

from amphora_contracts_planning import checkpoint_draft_schema, checkpoint_followup_draft_schema
from amphora_contracts_supervision import CheckpointRequest, SupervisionRequest

from ..context import RequestSnapshot
from ..context.policy import require


def encoded(model):
    return json.dumps(model.model_dump(mode='json'), sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


@dataclass(frozen=True)
class IntakeSnapshot:
    canonical: bytes
    planning: RequestSnapshot
    record_type: ClassVar = SupervisionRequest

    @staticmethod
    def targets(request):
        return request.snapshot.targets

    @classmethod
    def bind(cls, request, principal):
        request = cls.record_type.model_validate_json(request.model_dump_json())
        require(request.planning_request.context.output_schema not in (checkpoint_draft_schema(), checkpoint_followup_draft_schema()) or
                isinstance(request, CheckpointRequest), 'checkpoint_output_requires_checkpoint_request')
        original = RequestSnapshot.bind(request.planning_request, actor_id=principal.actor_id, scope=principal.scope)
        require(request.planning_request.purpose == 'supervision', 'supervision_purpose_mismatch')
        require(original.sha256 == request.planning_request_sha256, 'planning_request_digest_mismatch')
        require(request.reference.scope == principal.scope and request.snapshot.cut.scope == principal.scope,
                'supervision_scope_mismatch')
        require(request.reference.run_id == request.snapshot.cut.run_id and
                request.snapshot.cut == request.planning_request.runtime_cut, 'supervision_cut_mismatch')
        require(request.policy == request.planning_request.context.policy, 'supervision_policy_mismatch')
        reads, targets = request.snapshot.reads, cls.targets(request)
        ids = tuple(item.node.activation_id for item in reads)
        require(len(set(ids)) == len(ids) and len(set(targets)) == len(targets) and set(targets) <= set(ids),
                'supervision_read_set_mismatch')
        lineage = request.lineage
        if lineage.ordinal == 1:
            require(lineage.root_request_sha256 is None and lineage.parent_request_sha256 is None,
                    'supervision_root_mismatch')
        else:
            require(lineage.root_request_sha256 is not None and lineage.parent_request_sha256 is not None,
                    'supervision_parent_missing')
            if lineage.ordinal == 2:
                require(lineage.root_request_sha256 == lineage.parent_request_sha256, 'supervision_first_parent_mismatch')
        raw = encoded(request)
        require(len(raw) <= 262144, 'supervision_request_size')
        return cls(raw, original)

    @classmethod
    def from_bytes(cls, raw, principal):
        require(type(raw) is bytes and 0 < len(raw) <= 262144, 'supervision_request_size')
        result = cls.bind(cls.record_type.model_validate_json(raw), principal)
        require(result.canonical == raw, 'noncanonical_supervision_request')
        return result

    def document(self):
        return self.record_type.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()


class CheckpointIntakeSnapshot(IntakeSnapshot):
    record_type = CheckpointRequest

    @staticmethod
    def targets(request):
        reads = {item.node.activation_id: item.node for item in request.snapshot.reads}
        for item in request.snapshot.checkpoints:
            require(len(set(item.fields)) == len(item.fields), 'supervision_duplicate_field')
            require(item.activation_id in reads and reads[item.activation_id].kind == item.kind,
                    'supervision_target_kind_mismatch')
        return tuple(item.activation_id for item in request.snapshot.checkpoints)


def read_snapshot(raw, principal):
    require(type(raw) is bytes and 0 < len(raw) <= 262144, 'supervision_request_size')
    document = json.loads(raw)
    require(type(document) is dict, 'supervision_request_profile')
    model = {'1': IntakeSnapshot, '2': CheckpointIntakeSnapshot}.get(document.get('schema_version'))
    require(model is not None, 'supervision_request_profile')
    return model.from_bytes(raw, principal)
