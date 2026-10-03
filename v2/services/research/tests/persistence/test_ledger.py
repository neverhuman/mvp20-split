import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from amphora_contracts_research import (
    CandidateRevision,
    EvidenceNeed,
    MaterialStateRevisionRef,
    ResearchQuestion,
    SampleIdentity,
)
from amphora_research.identity.questions import ResearchIdentityError
from amphora_research.persistence.ledger import IdentityLedger
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def candidate(scope, revision=1, marker="initial"):
    ref = {"scope": scope.model_dump(), "candidate_id": "c", "revision": revision}
    raw = {"wire_version": "1", "reference": ref,
           "representation": {"artifact_id": marker, "scope": scope.model_dump(), "sha256": "b" * 64,
               "media_type": "application/json", "size_bytes": 2,
               "schema_ref": {"schema_id": "fixture", "version": "1", "sha256": "a" * 64}},
           "supersedes": None if revision == 1 else ref | {"revision": revision - 1}}
    return CandidateRevision.model_validate_json(json.dumps(raw))


def test_immutable_replay_and_historical_read_survive_ledger_replacement(ledger):
    store, scope = ledger
    first = candidate(scope)
    store.publish(scope, first)
    store.publish(scope, candidate(scope, 2))
    replacement = IdentityLedger(store.engine)
    assert replacement.publish(scope, first) == first
    assert replacement.read(scope, "candidate", "c", 1) == first
    with pytest.raises(ResearchIdentityError, match="immutable_revision_conflict"):
        replacement.publish(scope, candidate(scope, marker="changed"))
    with pytest.raises(ResearchIdentityError, match="revision_head_conflict"):
        replacement.publish(scope, candidate(scope, 4))
    assert replacement.read(scope, "candidate", "c", 4) is None


def test_two_writers_get_one_revision_and_one_conflict(ledger):
    store, scope = ledger
    store.publish(scope, candidate(scope))
    barrier = Barrier(2)

    def write(marker):
        barrier.wait(timeout=5)
        try:
            store.publish(scope, candidate(scope, 2, marker))
            return "published"
        except ResearchIdentityError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, ["left", "right"]))
    assert sorted(results) == ["immutable_revision_conflict", "published"]
    assert store.read(scope, "candidate", "c", 2).representation.artifact_id in {"left", "right"}


def test_unknown_candidate_rolls_back_sample_identity_and_head(ledger):
    store, scope = ledger
    c = candidate(scope)
    sample = SampleIdentity.model_validate_json(json.dumps({
        "wire_version": "1", "reference": {"scope": scope.model_dump(), "sample_id": "s", "revision": 1},
        "candidate": c.reference.model_dump(mode="json"), "material_state": None,
        "identity_evidence": c.representation.model_dump(mode="json"), "supersedes": None,
    }))
    with pytest.raises(ResearchIdentityError, match="unknown_candidate"):
        store.publish(scope, sample)
    assert store.read(scope, "sample", "s", 1) is None
    store.publish(scope, c)
    assert store.publish(scope, sample) == sample
    with pytest.raises(ResearchIdentityError, match="unknown_material_state"):
        store.publish(scope, sample.model_copy(update={"reference":sample.reference.model_copy(update={"sample_id":"unknown-state"}),
            "material_state": MaterialStateRevisionRef(scope=scope, material_state_id="unrecorded", revision=1)}))


def test_need_requires_persisted_question_and_known_criteria(ledger):
    store, scope = ledger
    c = candidate(scope)
    qref = {"scope": scope.model_dump(), "question_id": "q", "revision": 1}
    q = ResearchQuestion.model_validate_json(json.dumps({"wire_version": "1", "reference": qref,
        "objective": "Synthetic comparison", "applicability": c.representation.model_dump(mode="json"),
        "criteria": [{"criterion_id": "c1", "description": "Required context"}], "supersedes": None}))
    n = EvidenceNeed.model_validate_json(json.dumps({"wire_version": "1",
        "reference": {"scope": scope.model_dump(), "need_id": "n", "revision": 1}, "question": qref,
        "criterion_ids": ["c1"], "method": c.representation.schema_ref.model_dump(mode="json"),
        "required_context": c.representation.model_dump(mode="json"), "supersedes": None}))
    with pytest.raises(ResearchIdentityError, match="unknown_question"):
        store.publish(scope, n)
    store.publish(scope, q)
    with pytest.raises(ResearchIdentityError, match="unknown_criterion"):
        store.publish(scope, n.model_copy(update={"criterion_ids": ("missing",)}))
    assert store.read(scope, "need", "n", 1) is None
    assert store.publish(scope, n) == n
    foreign_question = n.question.model_copy(update={"scope": scope.model_copy(update={"project_id": "foreign"})})
    foreign_need = n.model_copy(update={"reference": n.reference.model_copy(update={"need_id": "foreign"}),
                                       "question": foreign_question})
    with pytest.raises(ResearchIdentityError, match="reference_scope_mismatch"):
        store.publish(scope, foreign_need)


def test_service_role_cannot_mutate_history_or_access_peer_state(ledger):
    store, scope = ledger
    store.publish(scope, candidate(scope))
    for statement in (
        "UPDATE research.identity_records SET canonical_bytes=decode('00','hex') WHERE false",
        "DELETE FROM research.identity_records WHERE false",
        "CREATE TABLE research.forbidden (id int)",
        "SELECT * FROM artifacts.commands LIMIT 0",
        "SELECT * FROM runtime.commands LIMIT 0",
    ):
        with pytest.raises(DBAPIError) as error, store.engine.begin() as connection:
            connection.execute(text(statement))
        assert error.value.orig.sqlstate == "42501"


def test_foreign_scope_is_neither_visible_nor_publishable(ledger):
    store, scope = ledger
    first = candidate(scope)
    store.publish(scope, first)
    foreign = scope.model_copy(update={"project_id": "foreign"})
    assert store.read(foreign, "candidate", "c", 1) is None
    with pytest.raises(ResearchIdentityError, match="record_scope_mismatch"):
        store.publish(foreign, first)
    with pytest.raises(ResearchIdentityError, match="unknown_record_kind"):
        store.read(scope, "arbitrary_table", "c", 1)


def test_sql_null_cannot_bypass_predecessor_constraint(ledger):
    store, scope = ledger
    with pytest.raises(DBAPIError) as error, store.engine.begin() as connection:
        connection.execute(text("INSERT INTO research.identity_records "
            "(tenant_id,project_id,kind,identity_id,revision,prior_revision,canonical_bytes) "
            "VALUES (:tenant,:project,'candidate','invalid',2,NULL,:body)"),
            {"tenant": scope.tenant_id, "project": scope.project_id, "body": b"{}"})
    assert error.value.orig.sqlstate == "23514"


def test_interruption_before_head_commit_rolls_back_record(ledger):
    store, scope = ledger

    def fail_head(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.startswith("INSERT INTO research.identity_heads"):
            raise RuntimeError("injected_before_head")

    event.listen(store.engine, "before_cursor_execute", fail_head)
    try:
        with pytest.raises(RuntimeError, match="injected_before_head"):
            store.publish(scope, candidate(scope))
    finally:
        event.remove(store.engine, "before_cursor_execute", fail_head)
    assert store.read(scope, "candidate", "c", 1) is None
    assert store.publish(scope, candidate(scope)) == candidate(scope)
