"""Knowledge owner transactions with synthetic public-protocol publication fixture."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_contracts_graph_runtime import ReceiptChainRef
from amphora_contracts_knowledge import CorrectReasoningReceipt, SelectReasoningReceipt
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.corrections.store import CorrectionStore
from amphora_knowledge.publication.workflow import PublicationWorkflow
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from ..publication.peer_fixture import PublicationPeer

pytestmark = pytest.mark.postgres


@pytest.fixture
def correction_case(publication_case):
    c = publication_case
    c.publishing = PublicationWorkflow(c.publications, c.reviewer, c.publisher, PublicationPeer())
    c.sources = {}
    for name in ("first", "second", "third"):
        request = c.publication.model_copy(update={"publication_id":name})
        assert c.publishing.submit(c.principal, request).outcome.status == "published"
        c.sources[name] = request
    c.correction_principal = replace(c.principal, actions=frozenset({"correct_reasoning_receipt"}))
    c.corrections = CorrectionStore(c.case.engine)
    chain = ReceiptChainRef(scope=c.principal.scope, issuer_id=c.publisher.issuer_id, chain_id="chain")
    c.command = CorrectReasoningReceipt(wire_version="1", chain=chain, change_id="create",
        source=c.sources["first"], reason_code="initial", expected_head=None)
    return c


def query(c, revision=None):
    return SelectReasoningReceipt(wire_version="1", chain=c.command.chain, revision=revision)


def test_correct_grant_restores_original_authority_without_publish_rights(correction_case):
    c = correction_case
    with pytest.raises(KnowledgeError, match="access_denied"):
        c.publishing.terminals.read(c.correction_principal, c.sources["first"])
    first = c.corrections.append(c.command, c.correction_principal)
    successor = c.command.model_copy(update={"change_id":"next", "source":c.sources["second"], "expected_head":first.reference})
    second = c.corrections.append(successor, c.correction_principal)
    replacement = CorrectionStore(c.case.engine)
    assert replacement.append(c.command, c.correction_principal) == first
    assert replacement.append(successor, c.correction_principal) == second
    assert replacement.select(query(c)) == second
    assert replacement.select(query(c, first.reference)) == first
    original = c.publishing.terminals.read(c.principal, c.sources["first"]).outcome.receipt
    assert first.record.source_receipt == original
    assert original.revision == "1" and original.outcome.status == "accepted"
    assert second.record.notice.revision == first.record.receipt.revision
    with pytest.raises(KnowledgeError, match="identity_conflict"):
        replacement.append(c.command.model_copy(update={"reason_code":"changed"}), c.correction_principal)
    with pytest.raises(KnowledgeError, match="access_denied"):
        replacement.append(c.command, replace(c.correction_principal, actor_id="other"))
    with c.case.engine.begin() as connection, pytest.raises(DBAPIError):
        connection.execute(text("UPDATE knowledge.receipt_corrections SET ordinal=ordinal"))


def test_competing_heads_and_exact_duplicate_replay(correction_case):
    c = correction_case
    barrier = Barrier(2)

    def create(_):
        barrier.wait(timeout=10)
        return c.corrections.append(c.command, c.correction_principal)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, duplicate = pool.map(create, range(2))
    assert first == duplicate
    barrier = Barrier(2)

    def successor(name):
        request = c.command.model_copy(update={"change_id":name,"source":c.sources[name],"expected_head":first.reference})
        barrier.wait(timeout=10)
        try:
            return c.corrections.append(request, c.correction_principal).record.ordinal
        except KnowledgeError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(successor, ("second", "third")))
    assert sorted(results,key=str) == [2,"correction_head_conflict"]


def test_rollback_leaves_no_partial_head(correction_case):
    c = correction_case

    def fail(_connection,_cursor,statement,_parameters,_context,_many):
        if statement.startswith("INSERT INTO knowledge.receipt_corrections"):
            raise RuntimeError("injected_after_insert")

    event.listen(c.case.engine,"after_cursor_execute",fail)
    try:
        with pytest.raises(RuntimeError,match="injected_after_insert"):
            c.corrections.append(c.command,c.correction_principal)
    finally:
        event.remove(c.case.engine,"after_cursor_execute",fail)
    assert c.corrections.select(query(c)) is None
    assert c.corrections.append(c.command,c.correction_principal).record.ordinal == 1


def test_source_graph_scope_and_original_publication_actor_remain_required(correction_case):
    c = correction_case
    foreign = c.command.source.graph.model_copy(update={"scope":c.principal.scope.model_copy(update={"project_id":"foreign"})})
    request = c.command.model_copy(update={"source":c.command.source.model_copy(update={"graph":foreign})})
    with pytest.raises(KnowledgeError,match="access_denied"):
        c.corrections.append(request,c.correction_principal)
    with pytest.raises(KnowledgeError,match="publication_identity_conflict"):
        c.corrections.append(c.command,replace(c.correction_principal,actor_id="other"))
    with pytest.raises(KnowledgeError,match="publication_pending"):
        c.corrections.append(c.command.model_copy(update={"source":c.command.source.model_copy(update={"publication_id":"missing"})}),c.correction_principal)


def test_exact_selection_rejects_wrong_hash_and_cross_chain(correction_case):
    c = correction_case
    first = c.corrections.append(c.command,c.correction_principal)
    wrong = first.reference.model_copy(update={"record_sha256":"a"*64})
    with pytest.raises(KnowledgeError,match="selection_conflict"):
        c.corrections.select(query(c,wrong))
    foreign = first.reference.model_copy(update={"chain":c.command.chain.model_copy(update={"chain_id":"other"})})
    with pytest.raises(KnowledgeError,match="selection_mismatch"):
        c.corrections.select(query(c,foreign))
    with pytest.raises(KnowledgeError,match="predecessor_mismatch"):
        c.corrections.append(c.command.model_copy(update={"change_id":"next","expected_head":foreign}),c.correction_principal)


def test_pending_owner_publication_is_not_a_correction_source(correction_case):
    c = correction_case
    pending = c.command.source.model_copy(update={"publication_id":"pending"})
    c.publications.begin(c.principal,pending,c.publisher)
    with pytest.raises(KnowledgeError,match="publication_pending"):
        c.corrections.append(c.command.model_copy(update={"source":pending}),c.correction_principal)
    assert c.corrections.select(query(c)) is None
