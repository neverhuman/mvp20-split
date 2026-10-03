"""Closed scientific encoding rejects ambiguous or unbounded dependency identity."""
import pytest
from amphora_research.eligibility.wire import assess_to_wire
from amphora_research.persistence.decision_document import DecisionDocument, DecisionStoreError, canonical

from ..eligibility.test_policy import policy


@pytest.mark.parametrize("change,reason",[
    (lambda s:(),"scientific_decision_source_limit"),
    (lambda s:s+(s[0].model_copy(update={"sha256":"0"*64}),),"scientific_decision_source_conflict"),
    (lambda s:(s[0].model_copy(update={"scope":s[0].scope.model_copy(update={"project_id":"other"})}),),"scientific_decision_source_scope"),
    (lambda s:tuple(s[0].model_copy(update={"artifact_id":f"source-{i}"}) for i in range(129)),"scientific_decision_source_limit"),
])
def test_sources_must_be_bounded_exact_scoped_references(change,reason):
    configured = policy()
    assessment = assess_to_wire(configured,())
    with pytest.raises(DecisionStoreError,match=reason):
        DecisionDocument.prepare("eligibility",configured.context.subject.candidate.scope,"fixture","decision",assessment,
                                 change((configured.context.conditions,)))


def test_oversize_canonical_record_is_rejected_not_truncated():
    with pytest.raises(DecisionStoreError,match="scientific_decision_byte_limit"):
        canonical("x"*8388608)
