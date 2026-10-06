from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentPeerUnavailable
from amphora_research.candidate_registration.profiles import CandidateRegistrationError
from amphora_research.candidate_registration.registration import CandidateReader
from amphora_research.transport.access import AccessDenied
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def metadata(registrar, scope):
    with registrar.ledger.engine.connect() as connection:
        return connection.execute(
            text(
                "SELECT actor_id,record_sha256,preexisting,registered_at "
                "FROM research.candidate_registrations WHERE tenant_id=:tenant AND project_id=:project "
                "AND identity_id='c' AND revision=1"
            ),
            {"tenant": scope.tenant_id, "project": scope.project_id},
        ).one_or_none()


@pytest.mark.parametrize("preexisting", [False, True])
def test_first_origin_and_historical_bytes_survive_replay_and_later_revision(
    candidate_registration, preexisting
):
    registrar, principal, record, reader = candidate_registration
    if preexisting:
        registrar.ledger.publish(principal.scope, record)
    assert registrar.register(principal, record) == record
    original = metadata(registrar, principal.scope)
    assert (
        original.actor_id == principal.actor_id and original.preexisting == preexisting
    )
    assert registrar.register(replace(principal, actor_id="later"), record) == record
    assert reader.calls == 2 and metadata(registrar, principal.scope) == original
    successor = record.model_copy(
        update={
            "reference": record.reference.model_copy(update={"revision": 2}),
            "supersedes": record.reference,
        }
    )
    registrar.register(principal, successor)
    reader.error = AssessmentError("peer_access_denied")
    with pytest.raises(CandidateRegistrationError, match="peer_access_denied"):
        registrar.register(principal, record)
    assert CandidateReader(registrar.ledger).read(principal, record.reference) == record
    assert metadata(registrar, principal.scope) == original


def test_peer_failure_and_registration_rollback_leave_no_identity(
    candidate_registration,
):
    registrar, principal, record, reader = candidate_registration
    reader.error = AssessmentPeerUnavailable("peer_unavailable")
    with pytest.raises(AssessmentPeerUnavailable):
        registrar.register(principal, record)
    reader.error = None

    def fail(_conn, _cursor, statement, _parameters, _context, _many):
        if statement.startswith("INSERT INTO research.candidate_registrations"):
            raise RuntimeError("injected")

    event.listen(registrar.ledger.engine, "before_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError, match="injected"):
            registrar.register(principal, record)
    finally:
        event.remove(registrar.ledger.engine, "before_cursor_execute", fail)
    assert metadata(registrar, principal.scope) is None
    assert CandidateReader(registrar.ledger).read(principal, record.reference) is None
    assert registrar.register(principal, record) == record


def test_conflict_and_stale_chain_remain_immutable(candidate_registration):
    registrar, principal, record, _ = candidate_registration
    registrar.register(principal, record)
    # A permitted different Artifact id with identical bytes is still a different declaration.
    changed = record.model_copy(
        update={
            "representation": record.representation.model_copy(
                update={"artifact_id": "other"}
            )
        }
    )

    class Reader:
        def read(self, ref):
            return original.read(record.representation)

    original = registrar.reader_factory(principal.scope)
    registrar.reader_factory = lambda scope: Reader()
    with pytest.raises(CandidateRegistrationError, match="immutable_revision_conflict"):
        registrar.register(principal, changed)
    stale = record.model_copy(
        update={
            "reference": record.reference.model_copy(update={"revision": 3}),
            "supersedes": record.reference.model_copy(update={"revision": 2}),
        }
    )
    with pytest.raises(CandidateRegistrationError, match="revision_head_conflict"):
        registrar.register(principal, stale)


def test_concurrent_identical_registration_keeps_one_origin(candidate_registration):
    registrar, principal, record, _ = candidate_registration
    barrier = Barrier(2)

    def register(actor):
        barrier.wait(timeout=5)
        return registrar.register(replace(principal, actor_id=actor), record)

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(register, ["left", "right"])) == [record, record]
    assert metadata(registrar, principal.scope).actor_id in {"left", "right"}


@pytest.mark.parametrize("which", ["grant", "scope", "schema", "size", "actor"])
def test_reject_before_peer_io(candidate_registration, which):
    registrar, principal, record, reader = candidate_registration
    if which == "grant":
        principal = replace(principal, actions=frozenset({"read_candidate"}))
    elif which == "scope":
        principal = replace(
            principal,
            scope=principal.scope.model_copy(update={"project_id": "foreign"}),
        )
    elif which == "actor":
        principal = replace(principal, actor_id="")
    else:
        ref = record.representation
        update = (
            {"size_bytes": 262145}
            if which == "size"
            else {"schema_ref": ref.schema_ref.model_copy(update={"sha256": "f" * 64})}
        )
        record = record.model_copy(
            update={"representation": ref.model_copy(update=update)}
        )
    with pytest.raises((AccessDenied, CandidateRegistrationError)):
        registrar.register(principal, record)
    assert reader.calls == 0


@pytest.mark.parametrize(
    "verb",
    [
        "UPDATE research.candidate_registrations SET actor_id='other'",
        "DELETE FROM research.candidate_registrations",
    ],
)
def test_registration_history_is_append_only(candidate_registration, verb):
    registrar, _, _, _ = candidate_registration
    with registrar.ledger.engine.begin() as connection, pytest.raises(DBAPIError):
        connection.execute(text(verb + " WHERE false"))


def test_registration_kind_and_read_grant_are_not_inferred(candidate_registration):
    registrar, principal, record, peer = candidate_registration
    with pytest.raises(CandidateRegistrationError, match="record_kind_invalid"):
        registrar.register(principal, record.reference)
    with pytest.raises(AccessDenied):
        CandidateReader(registrar.ledger).read(replace(principal, actions=frozenset({"declare_candidate"})), record.reference)
    assert peer.calls == 0
