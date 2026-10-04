"""Scripted public records isolate request/receipt binding, not actual owner contact."""

import hashlib
from dataclasses import replace
from datetime import datetime, timezone

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.extraction import TraceProjection
from amphora_agent_planning.owner_handoff.receipt import OwnerOutcome
from amphora_agent_planning.owner_handoff.request import OwnerRequest
from amphora_agent_planning.owner_handoff.selection import HandoffSelection
from amphora_agent_planning.proposals.validator import GraphCandidateValidator
from amphora_agent_planning.publication.records import encode
from amphora_contracts_knowledge import (
    AcceptedChangeContent,
    AcceptedChangeRef,
    AcceptedDecision,
    AcceptedGraphChange,
    DomainHead,
    DomainRevisionRef,
    FailedDecision,
    GraphChangeDecision,
    GraphProposalStatus,
    ReferenceValidation,
)

from ..proposals.support import Case
from ..research_proposals.support import ResearchCase


def request(kind="question", *, history=False):
    case = Case(history=history) if kind == "graph" else ResearchCase()
    bound = case.bind()
    principal = Principal("fixture", case.scope, frozenset({"read_attempts", "record_attempts"}))
    trace = TraceProjection(bound.publication.payload.artifact.body).reference()
    selection = HandoffSelection.bind(principal, trace, "publication", kind, "graph" if kind == "graph" else "q", "owner")
    if kind == "graph":
        record = GraphCandidateValidator().validate(bound.inputs).proposal()
    else:
        records = case.validate()
        record = records.questions[0].question if kind == "question" else records.evidence_needs[0].need
    return OwnerRequest.bind(selection, record), principal


def accepted_fixture(*, history=False):
    selected, principal = request("graph", history=history)
    proposal = selected.document()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    position = 1 if proposal.base is None else proposal.base.change.position + 1
    snapshot = DomainRevisionRef(graph=proposal.graph, revision=position, sha256="b"*64)
    validation = ReferenceValidation(checked_at=now, artifacts=(), sources=(), conversion_traces=(), questions=(), evidence_needs=())
    content = AcceptedChangeContent(proposal=proposal, actor_id=principal.actor_id, policy=proposal.policy,
        validation=validation, accepted_at=now, position=position, resulting_snapshot=snapshot, authority="structural_only")
    reference = AcceptedChangeRef(graph=proposal.graph, change_id=proposal.change_id, position=position,
        sha256=hashlib.sha256(encode(content.model_dump(mode="json"))).hexdigest())
    accepted = AcceptedGraphChange(wire_version="1", reference=reference, content=content)
    decision = GraphChangeDecision(wire_version="1", graph=proposal.graph, change_id=proposal.change_id,
        request_sha256=selected.sha256, decision=AcceptedDecision(outcome="accepted", head=DomainHead(snapshot=snapshot, change=reference)))
    status = GraphProposalStatus(wire_version="1", proposal=proposal, actor_id=principal.actor_id,
        request_sha256=selected.sha256, registered_at=now, decision=decision)
    return selected, status, accepted


@pytest.mark.parametrize("kind", ["question", "need", "graph"])
def test_exact_owner_request_and_configuration_share_stable_effect_slot(kind):
    value, principal = request(kind)
    selection = value.selection
    assert value.sha256 == hashlib.sha256(value.canonical).hexdigest()
    assert value.submit_path().startswith("/v1/")
    alternate = HandoffSelection.bind(principal, selection.trace(), "other-interpretation", kind,
        selection.document()["local_id"], "changed-owner")
    assert alternate.effect_id == selection.effect_id and alternate.sha256 != selection.sha256
    reader = replace(principal, actions=frozenset({"read_attempts"}))
    assert HandoffSelection.restore(selection.canonical, reader) == selection
    with pytest.raises(PermissionError):
        HandoffSelection.bind(reader, selection.trace(), "publication", kind, selection.document()["local_id"], "owner")
    with pytest.raises(ValueError, match="handoff_selection_canonical"):
        HandoffSelection.restore(selection.canonical + b" ", principal)


@pytest.mark.parametrize("kind", ["question", "need"])
def test_research_acknowledges_exact_presence_without_claiming_original_authorship(kind):
    value, _ = request(kind)
    result = OwnerOutcome.research(value, value.document())
    assert result.state == "acknowledged" and b'declaration_presence' in result.canonical
    assert b'original_actor' not in result.canonical
    record = value.document()
    changed = record.model_copy(update={"supersedes": record.reference})
    with pytest.raises(ValueError, match="handoff_record_mismatch"):
        OwnerOutcome.research(value, changed)


def test_accepted_decision_requires_original_status_and_exact_content_readback():
    value, status, accepted = accepted_fixture()
    assert OwnerOutcome.knowledge(value, status).state == "awaiting_accepted_readback"
    result = OwnerOutcome.knowledge(value, status, accepted)
    assert result.state == "acknowledged" and b'structural_only' in result.canonical
    assert OwnerOutcome.knowledge(value, status.model_copy(update={"decision": None})).state == "pending"
    with pytest.raises(ValueError, match="handoff_unexpected_acceptance"):
        OwnerOutcome.knowledge(value, status.model_copy(update={"decision": None}), accepted)


@pytest.mark.parametrize("fault", ["actor", "request", "proposal", "decision", "accepted_hash", "accepted_actor", "accepted_position"])
def test_forged_or_foreign_receipts_cannot_acknowledge_a_graph_effect(fault):
    value, status, accepted = accepted_fixture()
    if fault == "actor": status = status.model_copy(update={"actor_id": "foreign"})
    if fault == "request": status = status.model_copy(update={"request_sha256": "f"*64})
    if fault == "proposal": status = status.model_copy(update={"proposal": status.proposal.model_copy(update={"description": "Changed"})})
    if fault == "decision": status = status.model_copy(update={"decision": status.decision.model_copy(update={"change_id": "foreign"})})
    if fault == "accepted_hash": accepted = accepted.model_copy(update={"reference": accepted.reference.model_copy(update={"sha256": "f"*64})})
    if fault == "accepted_actor": accepted = accepted.model_copy(update={"content": accepted.content.model_copy(update={"actor_id": "foreign"})})
    if fault == "accepted_position": accepted = accepted.model_copy(update={"content": accepted.content.model_copy(update={"position": 2})})
    with pytest.raises(ValueError, match="handoff_(status|decision|accepted)_binding"):
        OwnerOutcome.knowledge(value, status, accepted)


@pytest.mark.parametrize("outcome", ["rejected", "conflict"])
def test_terminal_negative_decision_never_becomes_an_acceptance(outcome):
    from amphora_contracts_core import Finding
    value, status, accepted = accepted_fixture()
    decision = status.decision.model_copy(update={"decision": FailedDecision(outcome=outcome,
        findings=(Finding(code="stale_head", location="proposal", message="Not accepted"),))})
    status = status.model_copy(update={"decision": decision})
    assert OwnerOutcome.knowledge(value, status).state == outcome
    with pytest.raises(ValueError, match="handoff_unexpected_acceptance"):
        OwnerOutcome.knowledge(value, status, accepted)


def test_selection_restore_does_not_transfer_another_actor_or_scope():
    value, principal = request()
    with pytest.raises(ValueError, match="handoff_actor_binding"):
        HandoffSelection.restore(value.selection.canonical, replace(principal, actor_id="foreign"))
    with pytest.raises(PermissionError):
        HandoffSelection.restore(value.selection.canonical,
            replace(principal, scope=principal.scope.model_copy(update={"project_id": "foreign"})))


def test_request_kind_scope_and_single_graph_slot_are_enforced():
    value, principal = request()
    graph, _ = request("graph")
    with pytest.raises(ValueError, match="handoff_record_kind"):
        OwnerRequest.bind(value.selection, graph.document())
    record = value.document()
    ref = record.reference.model_copy(update={"scope": principal.scope.model_copy(update={"project_id": "foreign"})})
    with pytest.raises(ValueError, match="handoff_record_scope"):
        OwnerRequest.bind(value.selection, record.model_copy(update={"reference": ref}))
    with pytest.raises(ValueError, match="handoff_graph_slot"):
        HandoffSelection.bind(principal, value.selection.trace(), "publication", "graph", "another", "owner")


def test_accepted_revision_is_exact_successor_of_the_pinned_base():
    value, status, accepted = accepted_fixture(history=True)
    base = value.document().base
    assert base is not None and accepted.reference.position == base.change.position + 1
    assert OwnerOutcome.knowledge(value, status, accepted).state == "acknowledged"
    assert value.document().base == base
