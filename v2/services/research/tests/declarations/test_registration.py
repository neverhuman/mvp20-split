from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_research.declarations.registration import (
    DeclarationError,
    DeclarationRegistrar,
)
from amphora_research.transport.access import AccessDenied
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def metadata(registrar, record):
    with registrar.ledger.engine.connect() as connection:
        return connection.execute(text("SELECT actor_id,record_sha256,preexisting,registered_at "
            "FROM research.declaration_registrations WHERE tenant_id=:tenant AND project_id=:project "
            "AND kind='question' AND identity_id='q' AND revision=1"),
            {"tenant": record.reference.scope.tenant_id, "project": record.reference.scope.project_id}).one_or_none()


@pytest.mark.parametrize("preexisting", [False, True])
def test_exact_replay_preserves_first_registration_and_legacy_origin(registration, preexisting):
    registrar, principal, question, need = registration
    if preexisting:
        registrar.ledger.publish(principal.scope, question)
    assert registrar.register(principal, question) == question
    first = metadata(registrar, question)
    assert first.actor_id == principal.actor_id and first.preexisting == preexisting
    replacement = DeclarationRegistrar(registrar.ledger)
    assert replacement.register(replace(principal, actor_id="later"), question) == question
    assert metadata(registrar, question) == first
    assert replacement.register(principal, need) == need
    successor = question.model_copy(update={"reference": question.reference.model_copy(update={"revision": 2}),
        "supersedes": question.reference, "objective": "Later declaration"})
    replacement.register(principal, successor)
    assert replacement.register(principal, question) == question
    assert metadata(registrar, question) == first


def test_binding_and_conflicts_do_not_create_partial_registration(registration):
    registrar, principal, question, need = registration
    with pytest.raises(DeclarationError, match="^unknown_question$"):
        registrar.register(principal, need)
    registrar.register(principal, question)
    with pytest.raises(DeclarationError, match="^unknown_criterion$"):
        registrar.register(principal, need.model_copy(update={"criterion_ids": ("absent",)}))
    assert registrar.ledger.read(principal.scope, "need", "n", 1) is None
    with pytest.raises(DeclarationError, match="^immutable_revision_conflict$"):
        registrar.register(principal, question.model_copy(update={"objective": "changed"}))
    stale = question.model_copy(update={"reference": question.reference.model_copy(update={"revision": 3}),
        "supersedes": question.reference.model_copy(update={"revision": 2})})
    with pytest.raises(DeclarationError, match="^revision_head_conflict$"):
        registrar.register(principal, stale)


def test_registration_failure_rolls_back_identity_and_head(registration):
    registrar, principal, question, _ = registration
    def fail(_conn, _cursor, statement, _parameters, _context, _many):
        if statement.startswith("INSERT INTO research.declaration_registrations"):
            raise RuntimeError("injected registration failure")
    event.listen(registrar.ledger.engine, "before_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError, match="injected"):
            registrar.register(principal, question)
    finally:
        event.remove(registrar.ledger.engine, "before_cursor_execute", fail)
    assert registrar.ledger.read(principal.scope, "question", "q", 1) is None
    assert metadata(registrar, question) is None
    assert registrar.register(principal, question) == question


def test_concurrent_conflicting_registration_has_one_origin(registration):
    registrar, principal, question, _ = registration
    barrier = Barrier(2)
    def write(actor):
        barrier.wait(timeout=5)
        try:
            registrar.register(replace(principal, actor_id=actor), question.model_copy(update={"objective": actor}))
            return actor
        except DeclarationError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(write, ["left", "right"]))
    assert outcomes.count("immutable_revision_conflict") == 1
    winner = next(value for value in outcomes if value != "immutable_revision_conflict")
    assert metadata(registrar, question).actor_id == winner
    assert registrar.ledger.read(principal.scope, "question", "q", 1).objective == winner


@pytest.mark.parametrize("mutation", [
    lambda p: replace(p, actions=frozenset({"read_declarations"})),
    lambda p: replace(p, scope=p.scope.model_copy(update={"project_id": "foreign"})),
])
def test_authority_failure_before_transaction(registration, monkeypatch, mutation):
    registrar, principal, question, _ = registration
    def fail():
        raise AssertionError("SQL was accessed")
    monkeypatch.setattr(registrar.ledger.engine, "begin", fail)
    with pytest.raises(AccessDenied):
        registrar.register(mutation(principal), question)


@pytest.mark.parametrize("verb", ["UPDATE research.declaration_registrations SET actor_id='other'",
                                  "DELETE FROM research.declaration_registrations"])
def test_service_cannot_rewrite_registration(registration, verb):
    registrar, principal, question, _ = registration
    registrar.register(principal, question)
    with registrar.ledger.engine.begin() as connection, pytest.raises(DBAPIError):
        connection.execute(text(verb + " WHERE false"))


def test_private_adapter_rejects_wrong_kind_actor_and_unvalidated_dto(registration):
    from pydantic import ValidationError

    registrar, principal, question, _ = registration
    with pytest.raises(DeclarationError, match="^declaration_kind_invalid$"):
        registrar.register(principal, question.reference)
    with pytest.raises(DeclarationError, match="^declaration_actor_invalid$"):
        registrar.register(replace(principal, actor_id=""), question)
    with pytest.raises(ValidationError):
        registrar.register(principal, question.model_copy(update={"objective": ""}))
    assert metadata(registrar, question) is None
