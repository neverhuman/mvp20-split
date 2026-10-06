"""Actual repair disposition supplies diagnostic context without changing admitted roots."""

import pytest
from amphora_contracts_supervision import (
    CheckpointContext,
    CheckpointRepairContext,
    checkpoint_repair_context_content_schema,
)
from sqlalchemy import text

from ..supervision_resolution.support import record_response, save_report, setup


def test_actual_owned_repair_reason_enters_dynamic_context_and_replays(graph_env):
    actor, ref, slot, preparer, first, resolver = setup(graph_env)
    response = record_response(actor, ref, slot, preparer, first, variant='invalid')
    saved = save_report(resolver, actor, first, response)
    disposition = resolver.resolve(actor, ref, first.frame.request_sha256)
    second = preparer.prepare(actor, ref, parent_request_sha256=first.frame.request_sha256)
    original, repaired = first.frame.request, second.frame.request
    declaration = repaired.planning_request.context.entries[-1].artifact
    body = preparer.publisher.artifacts.documents[declaration.artifact_id]
    context = CheckpointRepairContext.model_validate_json(body)
    assert declaration.schema_ref == checkpoint_repair_context_content_schema()
    assert context.repair.parent_request_sha256 == first.frame.request_sha256
    assert context.repair.execution_report_sha256 == saved.report.sha256
    assert context.repair.disposition_sha256 == disposition.sha256
    assert context.repair.response_sha256 == disposition.document().response_sha256
    assert context.repair.reason_code == 'checkpoint_output_rejected'
    assert context.repair.observation_reason_code == 'invalid_json'
    assert b'malformed' not in body
    with pytest.raises(ValueError):
        CheckpointContext.model_validate_json(body)
    for name in ('objective', 'prompt', 'policy', 'model', 'allowed_actions', 'limits'):
        assert getattr(repaired.planning_request.context, name) == getattr(original.planning_request.context, name)
    assert repaired.planning_request.context.entries[:-1] == original.planning_request.context.entries[:-1]
    assert repaired.deadline_unix_ms == original.deadline_unix_ms
    with graph_env.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), {'run': ref.run_id})
    calls = len(preparer.publisher.artifacts.calls)
    assert preparer.prepare(actor, ref, parent_request_sha256=first.frame.request_sha256) == second
    assert len(preparer.publisher.artifacts.calls) == calls
