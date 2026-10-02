from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_knowledge import GroundLiteral, ReasoningLimits, ReasoningRequest, ReasoningRuleSet
from amphora_knowledge.reasoning.profile import RuleProfile
from amphora_knowledge.reasoning.store import ReasoningStore
from amphora_knowledge.reasoning.workflow import ReasoningWorkflow
from amphora_knowledge.validation.review import ReferenceReviewer
from amphora_knowledge.validation.workflow import AuthoringWorkflow

from ..validation.conftest import records


@pytest.fixture
def reasoning_case(stored_graph):
    case = stored_graph
    principal = replace(case.principal, actions=case.principal.actions | {"reason_graph"})
    peer = records(case.proposal)
    reviewer = ReferenceReviewer(peer, peer)
    authoring = AuthoringWorkflow(case.ledger, reviewer)
    accepted = authoring.submit(principal, peer.proposal)
    assert accepted.decision.outcome == "accepted"
    claim = peer.proposal.operations[2].assertion
    literal = GroundLiteral(subject=claim.subject, predicate=claim.predicate, object=claim.object, polarity=claim.polarity)
    profile = RuleProfile(ReasoningRuleSet(wire_version="1", graph=peer.proposal.graph, rule_set_id="fixture", version="v1",
        authority="synthetic_logical_entailment", context=claim.applicability,
        limits=ReasoningLimits(depth=32, work=100_000, facts=8192), rules=()))
    request = ReasoningRequest(wire_version="1", request_id="reason", snapshot=accepted.decision.head.snapshot,
        rule_set=profile.reference, context=claim.applicability, subject=claim.applicability,
        purpose="fixture_support", targets=(literal,))
    store = ReasoningStore(case.engine)
    workflow = ReasoningWorkflow(store, (profile,), reviewer)
    return SimpleNamespace(case=case, principal=principal, peer=peer, authoring=authoring, reviewer=reviewer,
        profile=profile, request=request, store=store, workflow=workflow, head=accepted.decision.head)
