"""Exploratory use, exact context and action-local prerequisites are independent dimensions."""
from dataclasses import replace

import pytest
from amphora_research.observations.quality.batch import ObservationUseBatch
from amphora_research.observations.quality.policy import ObservationUsePolicy, UseRequirements
from amphora_research.observations.records import ReportedQuality
from amphora_research.observations.values import MissingValue, NumericValue

from ...experiments.fixtures import experiment
from ...material_state.test_context import artifact, event, feature
from ..normalization.test_catalog import catalog, quantity
from ..test_matching import observation


def policy(strict=False, normalization=None):
    return ObservationUsePolicy("fixture.use","1","fixture.screening",UseRequirements(strict,strict,strict,()),normalization)


@pytest.mark.parametrize("controls,strict_disposition",[("failed","excluded"),("unknown","unresolved"),("passed","usable")])
def test_only_explicit_action_prerequisites_gate_weak_points(controls,strict_disposition):
    plan = experiment()
    row = replace(observation(plan),quality=ReportedQuality(controls,("questionable","low_accuracy")))
    exploratory,strict = policy().review(row,plan),policy(True).review(row,plan)
    assert exploratory.disposition == "usable" and strict.disposition == strict_disposition
    assert exploratory.observation is row and strict.observation is row
    assert "reported_quality_flags" in exploratory.focus
    assert row.quality.flags == ("questionable","low_accuracy")
    excluded = replace(policy(),requirements=UseRequirements(False,False,False,("low_accuracy",))).review(row,plan)
    assert excluded.disposition == "excluded" and excluded.blockers == ("reported_flag_excluded",)


def test_missing_values_are_return_coverage_but_not_invented_measurements():
    plan = experiment()
    row = observation(plan,MissingValue("not_measured"))
    result = ObservationUseBatch.assess(policy(True),plan,(row,))
    assert not result.missing_expectations and not result.usable
    assert result.reviews[0].disposition == "unresolved"
    assert "measurement_unavailable" in result.reviews[0].gaps
    exploratory = ObservationUseBatch.assess(policy(),plan,(row,))
    assert exploratory.usable == (row.identity.reference,) and exploratory.focus == (row.identity.reference,)
    assert type(exploratory.reviews[0].observation.value) is MissingValue


def test_unknown_material_context_remains_visible_without_inferring_equivalence():
    plan = experiment(False)
    row = observation(plan)
    assert policy().review(row,plan).disposition == "usable"
    assert "material_state_unknown" in policy(True).review(row,plan).gaps
    bound = experiment()
    review = policy().review(observation(bound),bound)
    assert review.match.state_known
    assert {"preparation_unknown","material_features_unreported"} <= set(review.focus)
    sample = bound.samples[0]
    template = feature()
    unknown = replace(template,value=MissingValue("unreported"),evidence=replace(template.evidence,basis="unknown",method=None,source=None))
    state = replace(sample.state,features=(unknown,))
    richer = replace(bound,samples=(replace(sample,state=state),))
    assert "material_feature_unknown" in policy().review(observation(richer),richer).focus


def test_only_explicit_normalization_can_reconcile_a_unit_mismatch():
    plan = experiment(unit="g")
    row = observation(plan,NumericValue(quantity("1.25","mg")))
    assert policy().review(row,plan).disposition == "quarantined"
    result = policy(normalization=catalog()).review(row,plan)
    assert result.raw_match.reasons == ("readout_unit_mismatch",) and result.match.reasons == ()
    assert result.disposition == "usable" and result.normalization.original is row.value
    assert result.observation.value.quantity.unit == "mg" and result.normalization.normalized.quantity.unit == "g"
    changed = replace(row,binding=replace(row.binding,measurement=replace(row.binding.measurement,context=artifact("other"))))
    rejected = policy(normalization=catalog()).review(changed,plan)
    assert rejected.disposition == "quarantined" and rejected.normalization is None
    assert "context_mismatch" in rejected.focus
    wrong = observation(plan,NumericValue(quantity("1.25","s")))
    unresolved = policy(normalization=catalog()).review(wrong,plan)
    assert unresolved.disposition == "quarantined" and unresolved.normalization.normalized is None
    assert "normalization_dimension_mismatch" in unresolved.focus


def test_divergent_replicates_and_partial_coverage_are_not_averaged_or_collapsed():
    plan = experiment(unit="mg")
    first = plan.expectations[0]
    second = replace(first,expectation_id="second",replicate=replace(first.replicate,replicate_id="replicate-2"))
    plan = replace(plan,expectations=(first,second))
    one = observation(plan,NumericValue(quantity("1")))
    two = replace(one,identity=replace(one.identity,reference=replace(one.identity.reference,observation_id="second")),
        binding=replace(one.binding,target=replace(one.binding.target,expectation_id="second",replicate_id="replicate-2")),
        value=NumericValue(quantity("100")))
    partial = ObservationUseBatch.assess(policy(),plan,(one,))
    assert partial.missing_expectations == ("second",) and partial.usable == (one.identity.reference,)
    complete = ObservationUseBatch.assess(policy(),plan,(two,one))
    assert not complete.missing_expectations
    assert tuple(review.observation for review in complete.reviews) == (two,one)
    assert complete.usable == (two.identity.reference,one.identity.reference)
    empty = ObservationUseBatch.assess(policy(),plan,())
    assert empty.missing_expectations == ("readout","second") and empty.usable == ()
    with pytest.raises(ValueError,match="duplicate_observation"):
        ObservationUseBatch.assess(policy(),plan,(one,one))


def test_complete_profile_hash_and_explicit_requirements():
    original = policy()
    assert original.reference == policy().reference
    for changed in (replace(original,action="other"),replace(original,version="2"),policy(True),policy(normalization=catalog())):
        assert changed.reference != original.reference
    with pytest.raises(ValueError,match="explicit_use_requirement"):
        UseRequirements(1,False,False,())
    with pytest.raises(ValueError,match="duplicate_use_flag"):
        UseRequirements(False,False,False,("flag","flag"))


def test_excluded_points_still_expose_missing_prerequisites_and_focus():
    plan = experiment(False)
    row = replace(observation(plan,MissingValue("not_measured")),quality=ReportedQuality("failed",()))
    result = policy(True).review(row,plan)
    assert result.disposition == "excluded"
    assert result.blockers == ("controls_failed",)
    assert {"measurement_unavailable","material_state_unknown"} <= set(result.gaps)


def test_same_nominal_candidate_does_not_allow_another_state_or_sample():
    plan = experiment(unit="g")
    row = observation(plan,NumericValue(quantity("1","mg")))
    for field,changed in (("sample",row.binding.specimen.sample.model_copy(update={"revision":2})),
        ("material_state",row.binding.specimen.material_state.model_copy(update={"revision":2}))):
        mismatch = replace(row,binding=replace(row.binding,specimen=replace(row.binding.specimen,**{field:changed})))
        result = policy(normalization=catalog()).review(mismatch,plan)
        assert result.disposition == "quarantined" and result.normalization is None


def test_cross_scope_batch_cannot_project_foreign_records():
    plan = experiment()
    row = observation(plan)
    scope = row.identity.reference.scope.model_copy(update={"project_id":"other"})
    foreign = replace(row,identity=replace(row.identity,reference=replace(row.identity.reference,scope=scope)),
        source=row.source.model_copy(update={"scope":scope}))
    with pytest.raises(ValueError,match="scope_mismatch"):
        ObservationUseBatch.assess(policy(),plan,(foreign,))


def test_fully_reported_context_does_not_invent_quality_warnings():
    from amphora_research.material_state.preparation import PreparationHistory
    plan = experiment()
    sample = plan.samples[0]
    state = replace(sample.state,preparation=PreparationHistory((event(),)),features=(feature(),))
    plan = replace(plan,samples=(replace(sample,state=state),))
    row = replace(observation(plan),quality=ReportedQuality("passed",()))
    review = policy(True).review(row,plan)
    assert review.disposition == "usable" and review.focus == ()
    assert review.observation is row and not review.blockers and not review.gaps
