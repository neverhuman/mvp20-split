"""Bind exact published Runtime context to authenticated immutable Planning intake."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_supervision import (
    CheckpointContext,
    CheckpointRepairContext,
    checkpoint_context_content_schema,
    checkpoint_repair_context_content_schema,
)

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..supervision_intake.snapshot import CheckpointIntakeSnapshot, read_snapshot


def context_model(reference):
    if reference.schema_ref == checkpoint_context_content_schema():
        return CheckpointContext
    require(reference.schema_ref == checkpoint_repair_context_content_schema(), 'execution_context_artifact')
    return CheckpointRepairContext


@dataclass(frozen=True)
class CheckpointContextBinding:
    canonical: bytes
    snapshot: CheckpointIntakeSnapshot
    reference: ArtifactRef

    @classmethod
    def bind(cls, intake, principal, reference, raw):
        snapshot = read_snapshot(intake.canonical, principal)
        require(isinstance(snapshot, CheckpointIntakeSnapshot), 'execution_checkpoint_request_required')
        reference = ArtifactRef.model_validate_json(reference.model_dump_json())
        request = snapshot.document()
        original = request.planning_request
        require(type(raw) is bytes and 0 < len(raw) <= 262144, 'execution_context_size')
        require(reference.sha256 == hashlib.sha256(raw).hexdigest() == original.decision_scope and
                reference.size_bytes == len(raw) and reference.scope == original.reference.scope and
                reference.media_type == 'application/json',
                'execution_context_artifact')
        declarations = tuple(item for item in original.context.entries if item.artifact.sha256 == original.decision_scope)
        require(len(declarations) == 1 and declarations[0].artifact == reference and declarations[0].required and
                declarations[0].role == 'constraint', 'execution_context_entry')
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        context = context_model(reference).model_validate_json(json.dumps(value, allow_nan=False))
        require(context.reference == request.reference and context.engagement == original.reference and
                context.lineage == request.lineage and context.checkpoint_id == request.checkpoint_id,
                'execution_context_request')
        if isinstance(context, CheckpointRepairContext):
            require(request.lineage.ordinal > 1 and
                    context.repair.parent_request_sha256 == request.lineage.parent_request_sha256,
                    'execution_repair_parent')
        require(context.objective == original.context.objective and context.policy == request.policy and
                context.budget_policy.scope == original.reference.scope, 'execution_context_roots')
        require(context.snapshot == request.snapshot and context.deadline_unix_ms == request.deadline_unix_ms,
                'execution_context_cut_deadline')
        require(len(set(context.allowed_actions)) == len(context.allowed_actions) and
                set(context.allowed_actions) == set(original.context.allowed_actions), 'execution_context_actions')
        require(len(context.snapshot.checkpoints) == 1, 'execution_context_target_count')
        checkpoint = context.snapshot.checkpoints[0]
        target = next(item.node for item in context.snapshot.reads if item.node.activation_id == checkpoint.activation_id)
        require(context.target == target.path, 'execution_context_target')
        names = tuple(item.name for item in context.fields)
        require(names == tuple(sorted(set(checkpoint.fields))), 'execution_context_fields')
        for field in context.fields:
            # Runtime's exact scalar fingerprint profile uses ASCII JSON escapes.
            encoded = json.dumps(field.original_value.model_dump(mode='json'), sort_keys=True, separators=(',', ':'),
                                 ensure_ascii=True, allow_nan=False).encode('utf-8')
            require(hashlib.sha256(encoded).hexdigest() == field.original_value_sha256, 'execution_context_scalar_digest')
        remaining, limits = context.remaining, original.context.limits
        require(min(remaining.slot_requests, remaining.campaign_requests) > 0 and
                limits.max_attempts <= min(remaining.slot_model_calls, remaining.campaign_model_calls),
                'execution_context_allowance')
        return cls(raw, snapshot, reference)

    def document(self):
        return context_model(self.reference).model_validate_json(self.canonical)

    def budget_policy(self, templates):
        template = templates.require(self.document().budget_policy)
        return template.bind(self.snapshot.planning)
