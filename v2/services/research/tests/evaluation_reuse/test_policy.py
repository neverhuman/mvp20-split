from dataclasses import replace

import pytest
from amphora_research.evaluation_reuse.errors import ReuseError
from amphora_research.evaluation_reuse.policy import ReuseQualification

from .policy_fixtures import bundle


def test_equivalent_encoding_returns_original_artifact_with_source_provenance():
    result=ReuseQualification.prepare(*bundle())
    assert result.status=='permitted' and not result.reasons
    assert result.reusable_artifact==result.evaluation.production.output
    assert result.source.record.representation.source!=result.target.record.representation.source
    assert result.subjects.source.reference!=result.subjects.target.reference
    assert result.subjects.synthesis_status=='unknown'
    assert 'synthesis.unknown' in result.subjects.focus and 'eligibility.accuracy' in result.subjects.focus


def test_matching_number_with_incompatible_context_is_a_cache_miss():
    result=ReuseQualification.prepare(*bundle(different_context=True))
    assert result.status=='miss' and result.reasons==('evaluation_context_mismatch',)
    assert result.reusable_artifact is None


@pytest.mark.parametrize('required,eligibility,synthesis,status',[
    (False,'supported','failed','permitted'),(True,'supported','failed','ineligible'),
    (True,'supported','unknown','ineligible'),(True,'supported','met','permitted'),
    (False,'unknown','met','ineligible'),(False,'contradicted','met','ineligible')])
def test_required_action_gates_do_not_turn_optional_weakness_into_global_veto(required,eligibility,synthesis,status):
    result=ReuseQualification.prepare(*bundle(required=required,eligibility_status=eligibility,synthesis_status=synthesis))
    assert result.status==status
    assert (result.reusable_artifact is not None)==(status=='permitted')


def test_policy_identity_binds_tool_release_and_explicit_synthesis_requirement():
    policy,*_=bundle()
    assert policy.reference==replace(policy).reference
    assert policy.reference!=replace(policy,synthesis_required=True).reference
    assert policy.reference!=replace(policy,canonicalizer=policy.canonicalizer.model_copy(update={'release':'0.5.0'})).reference
    with pytest.raises(ReuseError):replace(policy,synthesis_required=1)
    with pytest.raises(ReuseError):replace(policy,evaluation=policy.evaluation.model_copy(update={'purpose':'science'}))
    with pytest.raises(ReuseError):replace(policy,evaluation=policy.evaluation.model_copy(update={'required_context':()}))
    axis=policy.evaluation.objectives[0].model_copy(update={'unit':'kg'})
    with pytest.raises(ReuseError):replace(policy,evaluation=policy.evaluation.model_copy(update={'objectives':(axis,)}))


def test_relabeling_source_or_target_evidence_is_not_qualification():
    args=list(bundle());subjects=args[3]
    args[3]=replace(subjects,target=subjects.target.model_copy(update={'representation':subjects.source.representation}))
    with pytest.raises(ReuseError,match='candidate_source_mismatch'):ReuseQualification.prepare(*args)
    args=list(bundle());evidence=args[-1]
    args[-1]=replace(evidence,receipt=evidence.receipt.model_copy(update={'value':0}))
    with pytest.raises(ReuseError,match='evaluation_evidence_mismatch'):ReuseQualification.prepare(*args)
    args=list(bundle());args[4]=args[5]
    with pytest.raises(ReuseError,match='canonical_evidence_mismatch'):ReuseQualification.prepare(*args)


def test_specialized_sample_eligibility_cannot_be_used_for_candidate_wide_reuse():
    from ..experiments.fixtures import specimen
    args=list(bundle());subjects=args[3];decision=subjects.eligibility
    context=decision.assessment.policy.context
    changed=context.model_copy(update={'subject':context.subject.model_copy(update={'sample':specimen().sample.record.reference})})
    policy=decision.assessment.policy.model_copy(update={'context':changed})
    decision=decision.model_copy(update={'assessment':decision.assessment.model_copy(update={'policy':policy})})
    args[3]=replace(subjects,eligibility=decision)
    with pytest.raises(ReuseError,match='specialized_context_unsupported'):ReuseQualification.prepare(*args)


def test_focus_preserves_long_identifiers_and_can_be_empty_when_all_points_are_ready():
    import json
    from amphora_contracts_evaluation_reuse import ReuseProjection
    from pydantic import TypeAdapter
    subjects=bundle(synthesis_status='met')[3]
    assessment=subjects.eligibility.assessment.model_copy(update={'focus':('x'*128,)})
    subjects=replace(subjects,eligibility=subjects.eligibility.model_copy(update={'assessment':assessment}))
    assert subjects.focus==('eligibility.'+'x'*128,)
    TypeAdapter(ReuseProjection.model_fields['focus'].annotation).validate_json(json.dumps(subjects.focus))
    subjects=replace(subjects,eligibility=subjects.eligibility.model_copy(update={'assessment':assessment.model_copy(update={'focus':()})}))
    assert subjects.focus==()
