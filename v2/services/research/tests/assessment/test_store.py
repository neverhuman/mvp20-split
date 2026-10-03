import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_contracts_research import EvidenceAssessmentProfile
from amphora_research.assessment.boundary import ConfiguredAssessment
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.resolution import ResolvedAssessment
from amphora_research.assessment.store import AssessmentIntent, AssessmentStore, canonical
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from .test_boundary import configured
from .test_policy import SCOPE


@pytest.fixture
def assessment_store(ledger):
    identity, scope = ledger
    profile, request, *_ = configured()

    def rescope(value):
        if isinstance(value, dict):
            if value == SCOPE.model_dump(mode="json"):
                return scope.model_dump(mode="json")
            return {key: rescope(item) for key, item in value.items()}
        if isinstance(value, list):
            return [rescope(item) for item in value]
        return value

    profile = ConfiguredAssessment.from_wire(EvidenceAssessmentProfile.model_validate_json(
        json.dumps(rescope(profile.document.model_dump(mode="json")))))
    request = request.model_copy(update={"profile": profile.reference, "question": profile.document.question.reference,
                                        "answers": (), "receipts": ()})
    bound = profile.bind(request, "original-actor", scope)
    inputs = tuple({profile.document.subject, profile.document.question.applicability,
                    *(r.need.required_context for r in profile.document.requirements)})
    resolved = ResolvedAssessment(bound.evaluate((), ()), inputs)
    return AssessmentStore(identity.engine), bound, resolved


@pytest.mark.postgres
def test_pending_and_terminal_replay_survive_replacement(assessment_store):
    store, bound, resolved = assessment_store
    scope, ident = bound.request.profile.scope, bound.request.assessment_id
    assert store.read(scope, ident, bound.actor_id) is None
    intent = store.begin(bound)
    assert store.begin(bound) == intent
    assert AssessmentStore(store.engine).read(scope, ident, bound.actor_id).resolved is None
    terminal = store.complete(bound, resolved)
    assert store.complete(bound, replace(resolved, inputs=tuple(reversed(resolved.inputs)))) == terminal
    restored = AssessmentStore(store.engine).read(scope, ident, bound.actor_id)
    assert restored == terminal
    assert restored.intent.bound.configured.document == bound.configured.document
    assert restored.resolved.assessment == resolved.assessment
    assert set(restored.resolved.inputs) == set(resolved.inputs)
    assert store.read(scope.model_copy(update={"project_id": "other"}), ident, bound.actor_id) is None
    with pytest.raises(AssessmentError, match="actor_mismatch"):
        store.read(scope, ident, "other-actor")


@pytest.mark.postgres
def test_changed_actor_request_profile_and_result_cannot_replace_history(assessment_store):
    store, bound, resolved = assessment_store
    with pytest.raises(AssessmentError, match="intent_missing"):
        store.complete(bound, resolved)
    store.begin(bound)
    changed = replace(bound, actor_id="another")
    with pytest.raises(AssessmentError, match="identity_conflict"):
        store.begin(changed)
    with pytest.raises(AssessmentError, match="identity_conflict"):
        store.complete(changed, replace(resolved, assessment=resolved.assessment.model_copy(update={"actor_id": "another"})))
    changed = bound.configured.bind(bound.request.model_copy(update={"receipts": (resolved.inputs[0],)}),
                                     bound.actor_id, bound.request.profile.scope)
    with pytest.raises(AssessmentError, match="identity_conflict"):
        store.begin(changed)
    profile = ConfiguredAssessment.from_wire(bound.configured.document.model_copy(update={"purpose": "other"}))
    changed = profile.bind(bound.request.model_copy(update={"profile": profile.reference}), bound.actor_id,
                           bound.request.profile.scope)
    with pytest.raises(AssessmentError, match="identity_conflict"):
        store.begin(changed)
    original = store.complete(bound, resolved)
    extra = resolved.inputs[0].model_copy(update={"artifact_id": "another-input"})
    with pytest.raises(AssessmentError, match="decision_conflict"):
        store.complete(bound, replace(resolved, inputs=(*resolved.inputs, extra)))
    assert store.read(bound.request.profile.scope, bound.request.assessment_id, bound.actor_id) == original


@pytest.mark.postgres
def test_concurrent_decisions_have_one_winner(assessment_store):
    store, bound, resolved = assessment_store
    store.begin(bound)
    barrier = Barrier(2)

    def complete(label):
        extra = resolved.inputs[0].model_copy(update={"artifact_id": label})
        barrier.wait(timeout=5)
        try:
            store.complete(bound, replace(resolved, inputs=(*resolved.inputs, extra)))
            return "committed"
        except AssessmentError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(complete, ("left", "right"))) == ["assessment_decision_conflict", "committed"]


@pytest.mark.postgres
@pytest.mark.parametrize("terminal", [False, True])
def test_failure_after_insert_rolls_back_and_original_retry_succeeds(assessment_store, terminal):
    store, bound, resolved = assessment_store
    if terminal:
        store.begin(bound)
    table = "assessment_decisions" if terminal else "assessment_intents"

    def fail(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO research." + table):
            raise RuntimeError("injected after insert")

    event.listen(store.engine, "after_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError, match="injected"):
            store.complete(bound, resolved) if terminal else store.begin(bound)
    finally:
        event.remove(store.engine, "after_cursor_execute", fail)
    observed = store.read(bound.request.profile.scope, bound.request.assessment_id, bound.actor_id)
    assert (observed is not None and observed.resolved is None) if terminal else observed is None
    store.begin(bound)
    assert store.complete(bound, resolved).resolved.assessment == resolved.assessment


@pytest.mark.postgres
def test_service_role_denies_mutation_and_orphan_decision(assessment_store):
    store, bound, resolved = assessment_store
    intent = store.begin(bound)
    store.complete(bound, resolved)
    for table in ("assessment_intents", "assessment_decisions"):
        for command in (f"UPDATE research.{table} SET canonical_bytes=canonical_bytes", f"DELETE FROM research.{table}"):
            with pytest.raises(DBAPIError) as denied, store.engine.begin() as connection:
                connection.execute(text(command))
            assert denied.value.orig.sqlstate == "42501"
    with pytest.raises(DBAPIError) as orphan, store.engine.begin() as connection:
        store._insert(connection, intent.key | {"id": "orphan"}, b"{}", decision=True)
    assert orphan.value.orig.sqlstate == "23503"
    for decision, limit in ((False, 2097152), (True, 8388608)):
        with pytest.raises(DBAPIError) as oversized, store.engine.begin() as connection:
            store._insert(connection, intent.key | {"id": "oversized"}, b"x" * (limit + 1), decision=decision)
        assert oversized.value.orig.sqlstate == "23514"


def test_encoding_is_deterministic_bounded_and_finite():
    assert canonical({"b": 1, "a": "é"}, 100) == '{"a":"é","b":1}'.encode()
    with pytest.raises(AssessmentError, match="record_limit"):
        canonical({"a": "long"}, 2)
    with pytest.raises(ValueError):
        canonical({"a": float("nan")}, 100)


@pytest.mark.postgres
@pytest.mark.parametrize("mutation,code", [
    (lambda r: replace(r, assessment=r.assessment.model_copy(update={"actor_id": "another"})), "decision_mismatch"),
    (lambda r: replace(r, inputs=()), "input_limit"),
    (lambda r: replace(r, inputs=r.inputs * 129), "input_limit"),
    (lambda r: replace(r, inputs=r.inputs * 2), "input_duplicate"),
    (lambda r: replace(r, inputs=(r.inputs[0].model_copy(update={"scope": SCOPE}),)), "input_scope"),
    (lambda r: replace(r, inputs=(r.inputs[0].model_copy(update={"artifact_id": "unrelated"}),)), "input_missing"),
])
def test_invalid_snapshot_is_rejected_before_database_write(assessment_store, mutation, code):
    store, bound, resolved = assessment_store
    with pytest.raises(AssessmentError, match=code):
        store.complete(bound, mutation(resolved))
    assert store.read(bound.request.profile.scope, bound.request.assessment_id, bound.actor_id) is None


def test_unknown_persisted_format_is_not_silently_interpreted():
    with pytest.raises(AssessmentError, match="storage_format"):
        AssessmentIntent.restore(b'{"format":"unknown"}')
    with pytest.raises(AssessmentError, match="storage_format"):
        AssessmentStore._restore(None, b'{"format":"unknown"}')
