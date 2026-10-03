"""Decision history includes full policy and rejected evidence, not only favorable claims."""
from dataclasses import replace

from amphora_research.eligibility.decision import prepare

from .test_policy import claim, policy


def test_digest_pins_policy_actor_and_optional_weak_points():
    configured = policy()
    claims = (claim(),replace(claim("accuracy","contradicted","weak"),flags=("low_accuracy",)))
    first = prepare(configured,claims,"fixture","decision")
    assert first.record.assessment.disposition == "eligible"
    assert first.record.assessment.focus == ("accuracy",)
    assert {ref.observation_id for ref in first.record.observations} == {"result","weak"}
    assert {ref.artifact_id for ref in first.record.sources} == {"conditions","result","weak"}
    assert prepare(configured,claims,"fixture","decision") == first
    assert prepare(configured,claims,"other","decision").record.reference != first.record.reference
    changed = replace(configured,requirements=(configured.requirements[0],replace(configured.requirements[1],required=True)))
    assert prepare(changed,claims,"fixture","decision").record.assessment.disposition == "ineligible"
    assert prepare(changed,claims,"fixture","decision").record.reference != first.record.reference


def test_rejected_evidence_remains_a_dependency_for_future_review():
    configured = policy()
    rejected = replace(claim(),origin=replace(claim().origin,authority="scientific"))
    result = prepare(configured,(rejected,),"fixture","decision").record
    assert result.assessment.disposition == "unknown"
    assert result.assessment.reviews[0].reasons == ("authority_mismatch",)
    assert result.observations[0].observation_id == "result"
