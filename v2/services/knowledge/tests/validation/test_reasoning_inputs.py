import pytest
from amphora_contracts_knowledge import DomainRevisionRef, GroundLiteral, ReasoningRequest, RuleSetRef
from amphora_knowledge.authoring.canonical import KnowledgeError, digest
from amphora_knowledge.authoring.references import ReferencedInputs
from amphora_knowledge.validation.review import ReferenceReviewer, _Review
from amphora_knowledge.validation.transport import ReadBudget


def request_for(peers, claim):
    graph = peers.proposal.graph
    return ReasoningRequest(wire_version="1", request_id="reason", snapshot=DomainRevisionRef(graph=graph, revision=1, sha256="a" * 64),
        rule_set=RuleSetRef(graph=graph, rule_set_id="fixture", version="1", sha256="b" * 64),
        context=claim.applicability, subject=claim.applicability, purpose="fixture_support",
        targets=(GroundLiteral(subject=claim.subject, predicate=claim.predicate, object=claim.object, polarity=claim.polarity),))


def test_reasoning_observation_retains_every_consumed_trace_and_research_artifact(peers, monkeypatch):
    raw = peers.source_record.reference.raw
    output = raw.model_copy(update={"artifact_id": "converted"})
    question_context = raw.model_copy(update={"artifact_id": "question-context"})
    need_context = raw.model_copy(update={"artifact_id": "need-context"})
    peers.trace_record = peers.trace_record.model_copy(update={"output": output})
    peers.question_record = peers.question_record.model_copy(update={"applicability": question_context})
    peers.need_record = peers.need_record.model_copy(update={"required_context": need_context})
    monkeypatch.setattr(peers, "artifact", lambda ref, budget: ref)
    claim = peers.proposal.operations[2].assertion
    trace = claim.grounding.conversion_traces[0].model_copy(update={"sha256": digest(peers.trace_record)})
    claim = claim.model_copy(update={"grounding": claim.grounding.model_copy(update={"conversion_traces": (trace,)})})
    request = request_for(peers, claim)
    direct = ReferencedInputs.collect_records(peers.proposal.graph, (request, claim))
    assert direct.artifacts == (raw,)
    observed = ReferenceReviewer(peers, peers).review_reasoning(request, (claim,))
    assert observed.artifacts == tuple(sorted((raw, output, question_context, need_context), key=lambda ref: ref.artifact_id))
    assert peers.calls.count("content") == 4
    assert claim.posture == "hypothesis"


@pytest.mark.parametrize("reasoning,maximum,code", [(True, 128, "reasoning_input_limit"), (False, 256, "expanded_reference_limit")])
def test_consumed_input_bound_precedes_extra_io_and_preserves_authoring_limit(peers, monkeypatch, reasoning, maximum, code):
    monkeypatch.setattr(peers, "artifact", lambda ref, budget: ref)
    raw = peers.source_record.reference.raw
    session = _Review(peers, peers, raw.scope, ReadBudget(), reasoning=reasoning)
    for index in range(maximum):
        session.artifact(raw.model_copy(update={"artifact_id": f"input-{index}"}))
    before = len(peers.calls)
    with pytest.raises(KnowledgeError, match=code):
        session.artifact(raw.model_copy(update={"artifact_id": "exceeds-bound"}))
    assert len(peers.calls) == before


def test_shared_expanded_inputs_count_once(peers):
    claim = peers.proposal.operations[2].assertion
    observed = ReferenceReviewer(peers, peers).review_reasoning(request_for(peers, claim), (claim,))
    assert observed.artifacts == (peers.source_record.reference.raw,)
    assert peers.calls.count("content") == 1
