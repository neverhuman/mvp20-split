"""Exact original request binding; no auth, lineage storage or execution grant."""

import hashlib
import json
from dataclasses import dataclass
from typing import ClassVar

from amphora_contracts_planning import checkpoint_draft_schema
from amphora_contracts_supervision import CheckpointRequest, SupervisionRequest

from ..supervision_scope.observations import require
from .projection import CheckpointExport, ScopeExport


def encoded(model):
    return json.dumps(model.model_dump(mode='json'), sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


@dataclass(frozen=True)
class SupervisionRequestBinding:
    canonical: bytes
    record_type: ClassVar = SupervisionRequest
    export_type: ClassVar = ScopeExport

    @classmethod
    def bind(cls, request, footprint, *, actor_id):
        record = cls.record_type.model_validate_json(request.model_dump_json())
        original, context, cut = record.planning_request, record.planning_request.context, footprint.cut
        require(context.output_schema != checkpoint_draft_schema() or isinstance(record, CheckpointRequest),
                'checkpoint_output_requires_checkpoint_request')
        require(record.snapshot == cls.export_type(footprint).document(), 'scope_snapshot_mismatch')
        require(record.reference.scope == cut.scope and record.reference.run_id == cut.run_id,
                'decision_reference_mismatch')
        require(original.actor_id == actor_id, 'planning_actor_mismatch')
        require(original.purpose == 'supervision', 'wrong_planning_purpose')
        require(original.runtime_cut == cut, 'planning_cut_mismatch')
        require(original.reference.scope == cut.scope and context.scope == cut.scope, 'planning_scope_mismatch')
        require(record.policy == context.policy, 'planning_policy_mismatch')
        artifacts = (context.objective, context.prompt, context.policy, context.model.configuration,
                     *(item.artifact for item in context.entries), *(item.artifact for item in context.omissions))
        require(all(item.scope == cut.scope for item in artifacts), 'context_artifact_scope_mismatch')
        raw = encoded(original)
        require(len(raw) <= 262144, 'planning_request_size')
        require(hashlib.sha256(raw).hexdigest() == record.planning_request_sha256, 'planning_request_digest_mismatch')
        lineage = record.lineage
        if lineage.ordinal == 1:
            require(lineage.root_request_sha256 is None and lineage.parent_request_sha256 is None,
                    'initial_lineage_mismatch')
        else:
            require(lineage.root_request_sha256 is not None and lineage.parent_request_sha256 is not None,
                    'successor_lineage_missing')
            if lineage.ordinal == 2:
                require(lineage.root_request_sha256 == lineage.parent_request_sha256, 'first_successor_parent_mismatch')
        result = encoded(record)
        require(len(result) <= 262144, 'supervision_request_size')
        return cls(result)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def document(self):
        return self.record_type.model_validate_json(self.canonical)


class CheckpointRequestBinding(SupervisionRequestBinding):
    record_type = CheckpointRequest
    export_type = CheckpointExport
