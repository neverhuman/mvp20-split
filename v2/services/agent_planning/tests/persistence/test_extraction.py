import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_planning import ExtractionTraceRef
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


class Response:
    def __init__(self, raw):
        self.raw = raw

    def supports(self, model):
        return True

    def reply(self, binding):
        return ProviderReply((self.raw,), unknown_usage())


def inputs(stored):
    raw = json.loads((Path(__file__).parents[1] / "extraction/fixtures/extraction.json").read_bytes())
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {"tenant_id", "project_id"}:
                value.update(stored.principal.scope.model_dump())
            for child in value.values():
                rescope(child)
        elif isinstance(value, list):
            for child in value:
                rescope(child)
    rescope(raw)
    request = RequestSnapshot.from_bytes(json.dumps(raw["request"]).encode(),
                                         actor_id=stored.principal.actor_id, scope=stored.principal.scope)
    raw["task"]["request_sha256"] = request.sha256
    task = ExtractionSnapshot.from_bytes(json.dumps(raw["task"]).encode(), request)
    return task, json.dumps(raw["draft"]).encode()


def prepared(stored, output=None):
    task, raw = inputs(stored)
    stored.journal.register(stored.principal, task.request)
    journal = ExtractionJournal(stored.engine)
    registered = journal.register(stored.principal, task)
    binding = AttemptBinding(task.request, 1)
    stored.journal.begin_attempt(stored.principal, binding)
    observed = observe(binding, Response(raw if output is None else output))
    stored.journal.record(stored.principal, binding, observed)
    return journal, registered, binding, observed


def test_task_trace_exact_replay_and_replacement(stored):
    s = stored
    journal, task, binding, observed = prepared(s)
    task_id = task.snapshot.document().task_id
    first = journal.record(s.principal, task_id, binding.reference(), "trace")
    assert journal.register(s.principal, task.snapshot) == task
    assert journal.record(s.principal, task_id, binding.reference(), "trace") == first
    assert first.projection.document().outcome.capture_sha256 == observed.capture.sha256
    replacement = create_engine(s.engine.url)
    try:
        rebuilt = ExtractionJournal(replacement)
        assert rebuilt.read_task(s.principal, task_id) == task
        assert rebuilt.read_trace(s.principal, first.projection.reference()) == first
    finally:
        replacement.dispose()


def test_failed_attempt_and_repair_keep_distinct_durable_traces(stored):
    s = stored
    journal, task, binding, _ = prepared(s, b"{")
    task_id = task.snapshot.document().task_id
    failed = journal.record(s.principal, task_id, binding.reference(), "failed")
    _, raw = inputs(s)
    second = AttemptBinding(task.snapshot.request, 2)
    s.journal.begin_attempt(s.principal, second)
    s.journal.record(s.principal, second, observe(second, Response(raw)))
    repaired = journal.record(s.principal, task_id, second.reference(), "repaired", failed.projection.reference())
    assert failed.projection.document().outcome.status == "invalid"
    assert repaired.projection.document().outcome.status == "proposed"
    assert repaired.projection.document().repair_depth == 1
    assert repaired.projection.document().prior == failed.projection.reference()
    assert journal.read_trace(s.principal, repaired.projection.reference()) == repaired
    with pytest.raises(ValueError, match="extraction_trace_conflict"):
        journal.record(s.principal, task_id, second.reference(), "repaired")


def test_unregistered_task_unknown_and_pending_attempts_are_not_traced(stored):
    s = stored
    task, _ = inputs(s)
    journal = ExtractionJournal(s.engine)
    task_id = task.document().task_id
    binding = AttemptBinding(task.request, 1)
    assert journal.read_task(s.principal, task_id) is None
    assert journal.read_trace(s.principal, ExtractionTraceRef(scope=s.principal.scope,
                                                             trace_id="none", sha256="a" * 64)) is None
    with pytest.raises(ValueError, match="extraction_request_unknown"):
        journal.register(s.principal, task)
    with pytest.raises(ValueError, match="extraction_task_unknown"):
        journal.record(s.principal, task_id, binding.reference(), "trace")
    s.journal.register(s.principal, task.request)
    journal.register(s.principal, task)
    with pytest.raises(ValueError, match="extraction_attempt_unknown"):
        journal.record(s.principal, task_id, binding.reference(), "trace")
    s.journal.begin_attempt(s.principal, binding)
    with pytest.raises(ValueError, match="extraction_attempt_pending"):
        journal.record(s.principal, task_id, binding.reference(), "trace")


@pytest.mark.parametrize("change", ["identity", "target"])
def test_one_immutable_task_per_engagement(stored, change):
    s = stored
    journal, task, _, _ = prepared(s)
    raw = task.snapshot.document().model_dump(mode="json")
    if change == "identity":
        raw["task_id"] = "alternate"
    else:
        raw["target"]["graph"]["graph_id"] = "another"
    changed = ExtractionSnapshot.from_bytes(json.dumps(raw).encode(), task.snapshot.request)
    with pytest.raises(ValueError, match="extraction_task_conflict"):
        journal.register(s.principal, changed)


def test_binding_parent_digest_actor_and_permission_guards(stored):
    s = stored
    journal, task, binding, _ = prepared(s)
    task_id = task.snapshot.document().task_id
    ref = binding.reference()
    with pytest.raises(ValueError, match="extraction_attempt_binding"):
        journal.record(s.principal, task_id, ref.model_copy(update={"request_sha256": "a" * 64}), "trace")
    missing = ExtractionTraceRef(scope=s.principal.scope, trace_id="missing", sha256="a" * 64)
    with pytest.raises(ValueError, match="extraction_parent_unknown"):
        journal.record(s.principal, task_id, ref, "trace", missing)
    trace = journal.record(s.principal, task_id, ref, "trace")
    with pytest.raises(ValueError, match="extraction_trace_digest"):
        journal.read_trace(s.principal, trace.projection.reference().model_copy(update={"sha256": "a" * 64}))
    foreign = Principal("another", s.principal.scope, s.principal.actions)
    for call in [lambda: journal.read_task(foreign, task_id),
                 lambda: journal.read_trace(foreign, trace.projection.reference()),
                 lambda: journal.record(foreign, task_id, ref, "trace")]:
        with pytest.raises(ValueError, match="request_actor_mismatch"):
            call()
    denied = replace(s.principal, actions=frozenset())
    for call in [lambda: journal.register(denied, task.snapshot), lambda: journal.read_task(denied, task_id),
                 lambda: journal.record(denied, task_id, ref, "trace"),
                 lambda: journal.read_trace(denied, trace.projection.reference())]:
        with pytest.raises(PermissionError, match="planning_access_denied"):
            call()


@pytest.mark.parametrize("same_identity", [True, False])
def test_competing_trace_writers_commit_one_history(stored, same_identity):
    s = stored
    journal, task, binding, _ = prepared(s)
    barrier = Barrier(2)
    def write(identifier):
        barrier.wait(5)
        try:
            return journal.record(s.principal, task.snapshot.document().task_id, binding.reference(), identifier)
        except ValueError as exc:
            return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [f.result(10) for f in [pool.submit(write, "one"),
                                         pool.submit(write, "one" if same_identity else "two")]]
    if same_identity:
        assert results[0] == results[1]
    else:
        assert results.count("extraction_trace_conflict") == 1


def test_service_role_cannot_modify_extraction_history(stored):
    for table in ("extraction_tasks", "extraction_traces"):
        for statement in (f"DELETE FROM planning.{table} WHERE false",
                          f"UPDATE planning.{table} SET tenant_id=tenant_id WHERE false"):
            with pytest.raises(DBAPIError), stored.engine.begin() as connection:
                connection.execute(text(statement))


def test_constructed_attempt_is_revalidated_and_task_id_cannot_move_requests(stored):
    s = stored
    journal, task, binding, _ = prepared(s)
    with pytest.raises(ValueError):
        journal.record(s.principal, task.snapshot.document().task_id,
                       binding.reference().model_copy(update={"ordinal": True}), "forged")
    raw = task.snapshot.request.document().model_dump(mode="json")
    raw["reference"]["engagement_id"] = "different"
    request = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id=s.principal.actor_id,
                                         scope=s.principal.scope)
    s.journal.register(s.principal, request)
    changed = task.snapshot.document().model_dump(mode="json")
    changed.update(engagement=raw["reference"], request_sha256=request.sha256)
    with pytest.raises(ValueError, match="extraction_task_conflict"):
        journal.register(s.principal, ExtractionSnapshot.from_bytes(json.dumps(changed).encode(), request))
