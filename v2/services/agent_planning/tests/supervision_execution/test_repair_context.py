"""Planning validates exact parent lineage and explicit diagnostic content schema."""

import hashlib
import json

import pytest
from amphora_agent_planning.supervision_execution.context import (
    CheckpointContextBinding,
)
from amphora_agent_planning.supervision_intake.snapshot import CheckpointIntakeSnapshot
from amphora_contracts_supervision import (
    CheckpointRepairContext,
    CheckpointRequest,
    checkpoint_repair_context_content_schema,
)

from .test_context import encoded, prepared


def repair(*, wrong_parent=False, root=False):
    actor, intake, reference, raw, templates = prepared()
    context, request = json.loads(raw), intake.document().model_dump(mode='json')
    lineage = request['lineage'] if root else {'ordinal': 2, 'root_request_sha256': 'd' * 64, 'parent_request_sha256': 'd' * 64}
    context.update(profile='supervision-checkpoint-repair-context.v1', lineage=lineage, repair={
        'parent_request_sha256': 'e' * 64 if wrong_parent else 'd' * 64, 'execution_report_sha256': 'a' * 64,
        'disposition_sha256': 'b' * 64, 'response_sha256': 'c' * 64, 'reason_code': 'checkpoint_output_rejected',
        'observation_reason_code': 'invalid_json'})
    raw = encoded(context)
    updated = reference.model_copy(update={'schema_ref': checkpoint_repair_context_content_schema(),
        'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)})
    request['lineage'] = lineage
    original = request['planning_request']
    original['decision_scope'] = updated.sha256
    for entry in original['context']['entries']:
        if entry['artifact']['artifact_id'] == reference.artifact_id:
            entry['artifact'] = updated.model_dump(mode='json')
    request['planning_request_sha256'] = hashlib.sha256(encoded(original)).hexdigest()
    bound = CheckpointIntakeSnapshot.bind(CheckpointRequest.model_validate_json(json.dumps(request)), actor)
    return actor, bound, updated, raw, templates


def test_explicit_repair_context_retains_original_budget_and_parent():
    actor, intake, reference, raw, templates = repair()
    context = CheckpointContextBinding.bind(intake, actor, reference, raw)
    assert isinstance(context.document(), CheckpointRepairContext)
    assert context.document().repair.parent_request_sha256 == intake.document().lineage.parent_request_sha256
    assert context.budget_policy(templates).document().policy == intake.document().policy


@pytest.mark.parametrize('options', [{'wrong_parent': True}, {'root': True}])
def test_false_or_missing_parent_cannot_become_repair_context(options):
    actor, intake, reference, raw, _ = repair(**options)
    with pytest.raises(ValueError, match='execution_repair_parent'):
        CheckpointContextBinding.bind(intake, actor, reference, raw)
