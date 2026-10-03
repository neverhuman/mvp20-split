"""Publication reads have no writes; consumers require authenticated exact published lineage."""
from types import SimpleNamespace

import pytest
from amphora_contracts_research import (
    LabIntakeSelection,
    RegisterScientificConsumer,
    ScientificDecisionSelection,
    ScientificPublicationRequest,
)
from amphora_research.assessment.policy import AssessmentError
from amphora_research.scientific_api.boundary import ScientificInputError
from amphora_research.scientific_api.publications import ScientificPublications
from amphora_research.transport.access import AccessDenied, Principal
from sqlalchemy import event

from ..scientific_publication.test_publication import finalizing, publication, terminal

pytestmark = pytest.mark.postgres


def unavailable(*_):
    raise AssertionError("Read-only history must not call peers")


def selected(initial):
    return ScientificPublicationRequest(wire_version="1",target=ScientificDecisionSelection(kind="decision",reference=initial.artifact.document.reference))


def test_lookup_retains_publisher_without_writes_or_current_configuration(ledger):
    store,initial = publication(ledger)
    statements = []
    def record(connection,cursor,statement,parameters,context,many):
        statements.append(statement)
    event.listen(store.engine,"before_cursor_execute",record)
    try:
        assert store.lookup(initial.artifact) == initial
    finally:
        event.remove(store.engine,"before_cursor_execute",record)
    assert all(statement.startswith("SELECT") for statement in statements)
    operations = ScientificPublications(store.engine,unavailable,unavailable,"replacement-publisher",())
    principal = Principal("fixture",initial.scope,frozenset({"read_scientific_publication","publish_scientific_result"}))
    assert operations.read(principal,selected(initial)).outcome.status == "pending"
    lease = store.acquire(initial)
    progress = finalizing(store,lease)
    published = store.advance(lease,progress.position,"published",terminal(progress))
    store.release(lease)
    result = operations.read(principal,selected(initial))
    assert result.outcome.derivation == published.derivation
    assert operations.submit(principal,selected(initial)) == result
    assert result.actor_id == "fixture"
    with pytest.raises(AccessDenied):
        operations.read(Principal("other",initial.scope,principal.actions),selected(initial))


def test_consumer_registration_requires_exact_published_decision_lineage(ledger):
    store,initial = publication(ledger)
    principal = Principal("fixture",initial.scope,frozenset({"register_scientific_consumer"}))
    artifact = initial.artifact.document.sources[0].model_copy(update={"artifact_id":"consumer"})
    request = RegisterScientificConsumer(wire_version="1",decision=initial.artifact.document.reference,consumer=artifact)
    operations = ScientificPublications(store.engine,unavailable,unavailable,"publisher",("consumer-owner",))
    with pytest.raises(ScientificInputError,match="publication_pending"):
        operations.register_consumer(principal,request)
    lease = store.acquire(initial)
    progress = finalizing(store,lease)
    result = store.advance(lease,progress.position,"published",terminal(progress))
    store.release(lease)
    proof = result.derivation.model_copy(update={"artifact":artifact,"declaration":result.derivation.declaration.model_copy(update={"inputs":()})})
    def published(reference,publishers):
        assert reference == artifact and publishers == frozenset({"consumer-owner"})
        assert store.engine.pool.checkedout() == 0
        return b"fixture",proof
    reader = SimpleNamespace(consumed=(),published=published,read=lambda reference:None)
    operations.reader_factory = lambda _:reader
    with pytest.raises(AssessmentError,match="lineage_mismatch"):
        operations.register_consumer(principal,request)
    assert operations.index.consumers(initial.scope,request.decision).consumers == ()
    proof = proof.model_copy(update={"declaration":proof.declaration.model_copy(update={"inputs":(result.derivation.artifact,)})})
    assert operations.register_consumer(principal,request) == artifact
    assert operations.register_consumer(principal,request) == artifact
    assert operations.index.consumers(initial.scope,request.decision).consumers == (artifact,)
    with pytest.raises(ScientificInputError,match="consumer_scope"):
        operations.register_consumer(principal,request.model_copy(update={"consumer":artifact.model_copy(update={"scope":initial.scope.model_copy(update={"project_id":"other"})})}))


@pytest.mark.parametrize("kind",["eligibility","lab-intake"])
def test_pending_publication_uses_original_publisher_and_denial_is_operational(ledger,kind):
    store,initial = publication(ledger,kind)
    def denied(_):
        raise AssessmentError("peer_access_denied")
    reader = SimpleNamespace(scope=initial.scope,read=denied)
    operations = ScientificPublications(store.engine,lambda _:reader,lambda:None,"changed-publisher",())
    principal = Principal("fixture",initial.scope,frozenset({"read_scientific_publication","publish_scientific_result"}))
    request = selected(initial) if kind == "eligibility" else ScientificPublicationRequest(wire_version="1",
        target=LabIntakeSelection(kind="lab-intake",scope=initial.scope,intake_id=initial.artifact.record_id))
    result = operations.submit(principal,request)
    assert result.outcome.status == "failed" and result.outcome.code == "peer_access_denied"
    assert store.lookup(initial.artifact).publisher == "publisher"
    operations.reader_factory = unavailable
    assert operations.read(principal,request) == result
    assert operations.submit(principal,request) == result
