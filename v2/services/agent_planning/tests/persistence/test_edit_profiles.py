"""Actual PostgreSQL v2 task/observation/trace replay, with unchanged storage caps."""

import json

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.providers import observe
from sqlalchemy import create_engine

from ..extraction.test_edits import documents
from ..providers.test_task_output import Response

pytestmark = pytest.mark.postgres


def test_v2_task_edit_observation_and_trace_survive_replacement_without_reencoding(stored):
    s = stored
    task, value = documents(s.principal.scope)
    journal = ExtractionJournal(s.engine)
    s.journal.register(s.principal, task.request)
    original = journal.register(s.principal, task)
    binding = AttemptBinding(task.request, 1)
    s.journal.begin_attempt(s.principal, binding)
    observed = observe(binding, Response(json.dumps(value['draft']).encode()))
    assert observed.document().status == 'proposed'
    s.journal.record(s.principal, binding, observed)
    trace = journal.record(s.principal, task.document().task_id, binding.reference(), 'edit-trace')
    assert len([field for field in trace.projection.document().fields if field.target_path.startswith('/edits/')]) == 4
    replacement = create_engine(s.engine.url)
    try:
        rebuilt = ExtractionJournal(replacement)
        restored = rebuilt.read_task(s.principal, task.document().task_id)
        assert restored == original and restored.snapshot.document().schema_version == '2'
        assert restored.snapshot.document().existing_assertions == task.document().existing_assertions
        assert rebuilt.read_trace(s.principal, trace.projection.reference()) == trace
        assert rebuilt.record(s.principal, task.document().task_id, binding.reference(), 'edit-trace') == trace
    finally:
        replacement.dispose()


def test_failed_edit_attempt_and_repair_keep_typed_provenance(stored):
    s = stored
    task, value = documents(s.principal.scope)
    journal = ExtractionJournal(s.engine)
    s.journal.register(s.principal, task.request)
    journal.register(s.principal, task)
    records = []
    for ordinal, payload in ((1, b'{'), (2, json.dumps(value['draft']).encode())):
        binding = AttemptBinding(task.request, ordinal)
        s.journal.begin_attempt(s.principal, binding)
        observed = observe(binding, Response(payload))
        s.journal.record(s.principal, binding, observed)
        record = journal.record(s.principal, task.document().task_id, binding.reference(), 'edit-' + str(ordinal),
                                None if not records else records[-1].projection.reference())
        records.append(record)
    assert [record.projection.document().outcome.status for record in records] == ['invalid', 'proposed']
    assert records[1].projection.document().prior == records[0].projection.reference()
    assert journal.read_trace(s.principal, records[1].projection.reference()) == records[1]
