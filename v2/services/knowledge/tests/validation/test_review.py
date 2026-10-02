import pytest
from amphora_knowledge.authoring.canonical import KnowledgeError, digest
from amphora_knowledge.authoring.references import ReferencedInputs
from amphora_knowledge.validation.review import ReferenceReviewer


def test_exact_observation_checks_bytes_and_declarations_without_promoting(peers):
    result = ReferenceReviewer(peers, peers).review(peers.proposal)
    refs = ReferencedInputs.collect(peers.proposal)
    assert result.artifacts == refs.artifacts and result.sources == refs.sources
    assert result.conversion_traces == refs.traces and result.questions == refs.questions
    assert result.evidence_needs == refs.needs
    assert peers.calls.count("content") == 1
    assert peers.proposal.operations[2].assertion.posture == "hypothesis"


@pytest.mark.parametrize("kind,code", [
    ("bytes", "artifact_bytes_mismatch"), ("source", "source_binding_mismatch"),
    ("trace", "trace_binding_mismatch"), ("question", "question_binding_mismatch"),
    ("need", "need_binding_mismatch"), ("question_link", "need_question_mismatch"),
    ("criterion", "need_criterion_mismatch"), ("context", "reference_scope_mismatch"),
])
def test_substituted_peer_records_fail(peers, kind, code):
    if kind == "bytes":
        peers.raw = b"forged"
    elif kind == "source":
        peers.source_record = peers.source_record.model_copy(update={"reference":
            peers.source_record.reference.model_copy(update={"revision_id": "other"})})
    elif kind == "trace":
        peers.trace_record = peers.trace_record.model_copy(update={"converter_version": "other"})
    elif kind in {"question", "need"}:
        name = kind + "_record"
        record = getattr(peers, name)
        setattr(peers, name, record.model_copy(update={"reference": record.reference.model_copy(update={"revision": 2})}))
    elif kind == "question_link":
        peers.need_record = peers.need_record.model_copy(update={"question":
            peers.need_record.question.model_copy(update={"question_id": "another"})})
    elif kind == "criterion":
        peers.need_record = peers.need_record.model_copy(update={"criterion_ids": ("unknown",)})
    else:
        artifact = peers.question_record.applicability
        peers.question_record = peers.question_record.model_copy(update={"applicability": artifact.model_copy(update={
            "scope": artifact.scope.model_copy(update={"project_id": "foreign"})})})
    with pytest.raises(KnowledgeError, match=code):
        ReferenceReviewer(peers, peers).review(peers.proposal)


def test_span_hash_checked_on_actual_bytes(peers):
    grounding = peers.proposal.grounding
    bad = grounding.spans[0].model_copy(update={"sha256": "0"*64, "end": 2})
    proposal = peers.proposal.model_copy(update={"grounding": grounding.model_copy(update={"spans": (bad,)})})
    with pytest.raises(KnowledgeError, match="source_span_digest_mismatch"):
        ReferenceReviewer(peers, peers).review(proposal)


def test_cross_scope_rejected_before_any_peer_io(peers):
    grounding = peers.proposal.grounding
    ref = grounding.conversion_traces[0]
    ref = ref.model_copy(update={"scope": ref.scope.model_copy(update={"project_id": "foreign"})})
    proposal = peers.proposal.model_copy(update={"grounding": grounding.model_copy(update={"conversion_traces": (ref,)})})
    with pytest.raises(KnowledgeError, match="reference_scope_mismatch"):
        ReferenceReviewer(peers, peers).review(proposal)
    assert not peers.calls


def test_each_claim_requires_its_own_trace_source_binding(peers, monkeypatch):
    original = peers.proposal.grounding
    second = peers.trace_record.source.model_copy(update={"source_id": "second"})
    second_span = original.spans[0].model_copy(update={"source": second})
    field = peers.trace_record.fields[0].model_copy(update={"spans": (second_span,)})
    trace = peers.trace_record.model_copy(update={"trace_id": "second", "source": second, "fields": (field,)})
    ref = original.conversion_traces[0].model_copy(update={"trace_id": "second", "sha256": digest(trace)})
    # All sources/traces exist globally, but the claim's local trace cites the
    # other source. A flattened union check would wrongly accept this proposal.
    grounding = original.model_copy(update={"spans": (original.spans[0].model_copy(update={"source": second}),),
                                            "conversion_traces": (ref,)})
    assertion = peers.proposal.operations[2].assertion
    assertion = assertion.model_copy(update={"grounding": original.model_copy(update={"conversion_traces": (ref,)})})
    proposal = peers.proposal.model_copy(update={"grounding": grounding,
        "operations": (*peers.proposal.operations[:2], peers.proposal.operations[2].model_copy(update={"assertion": assertion}))})
    monkeypatch.setattr(peers, "source", lambda ref, budget: peers.source_record.model_copy(update={"reference": ref}))
    monkeypatch.setattr(peers, "trace", lambda ref, budget: trace)
    with pytest.raises(KnowledgeError, match="grounding_trace_mismatch"):
        ReferenceReviewer(peers, peers).review(proposal)
