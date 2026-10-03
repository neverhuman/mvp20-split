"""Experiment expectations bind exact specimens and context, not universal assay truth."""
from dataclasses import replace

import pytest
from amphora_research.experiments.identity import ExperimentError, ExperimentIdentity, ExperimentReference
from amphora_research.experiments.model import (
    ProtocolContext,
    ReadoutSpec,
    ReplicateRole,
    SampleContext,
)
from amphora_research.identity.samples import SampleDefinition
from amphora_research.observations.quantities import MeasurementError

from ..material_state.test_context import CANDIDATE, METHOD, OTHER, SCOPE, artifact
from .fixtures import experiment, specimen


def test_exact_context_lookup_and_unknown_state_are_separate():
    actual = experiment()
    assert actual.expectation("readout") is actual.expectations[0]
    assert actual.sample(actual.expectations[0].sample) is actual.samples[0]
    assert actual.expectation("not-recorded") is None and actual.sample(None) is None
    assert experiment(False).samples[0].state is None
    assert replace(actual.samples[0],state=None).sample.record.material_state is not None


def test_successor_preserves_original_and_control_roles():
    first = experiment()
    successor = replace(first,identity=ExperimentIdentity(replace(first.identity.reference,revision=2),first.identity.reference))
    assert first.identity.reference.revision == 1 and successor.identity.supersedes == first.identity.reference
    for role in ("sample","positive_control","negative_control","blank"):
        assert ReplicateRole("r",role).role == role
    assert experiment(kind="categorical",unit=None).expectations[0].readout.unit is None
    assert experiment(kind="series",x_unit="s").expectations[0].readout.x_unit == "s"


@pytest.mark.parametrize("factory,reason",[
    (lambda: ExperimentReference(None,"e",1),"experiment_scope_required"),
    (lambda: ExperimentReference(SCOPE,"",1),"invalid_experiment_identifier"),
    (lambda: ExperimentReference(SCOPE,"e",True),"experiment_revision_bound"),
    (lambda: ExperimentReference(SCOPE,"e",0),"experiment_revision_bound"),
    (lambda: ExperimentReference(SCOPE,"e",9007199254740992),"experiment_revision_bound"),
    (lambda: ExperimentIdentity(None,None),"experiment_reference_required"),
    (lambda: ExperimentIdentity(ExperimentReference(SCOPE,"e",2),None),"experiment_predecessor_required"),
    (lambda: ExperimentIdentity(ExperimentReference(SCOPE,"e",2),"e"),"experiment_predecessor_type"),
    (lambda: ExperimentIdentity(ExperimentReference(SCOPE,"e",3),ExperimentReference(SCOPE,"e",1)),"experiment_predecessor_mismatch"),
    (lambda: ExperimentIdentity(ExperimentReference(SCOPE,"e",2),ExperimentReference(OTHER,"e",1)),"experiment_predecessor_mismatch"),
    (lambda: ExperimentIdentity(ExperimentReference(SCOPE,"e",2),ExperimentReference(SCOPE,"other",1)),"experiment_predecessor_mismatch"),
    (lambda: SampleContext(None,None),"experiment_sample_required"),
    (lambda: replace(specimen(),state="state"),"experiment_state_type"),
    (lambda: replace(specimen(),sample=specimen(False).sample),"sample_state_mismatch"),
    (lambda: replace(specimen(),sample=SampleDefinition(specimen().sample.record.model_copy(update={"candidate":CANDIDATE.model_copy(update={"candidate_id":"different"})}))),"sample_state_candidate_mismatch"),
    (lambda: ProtocolContext(None,artifact(),artifact()),"experiment_method_required"),
    (lambda: ProtocolContext(METHOD,None,artifact()),"experiment_context_required"),
    (lambda: ProtocolContext(METHOD,artifact(scope=OTHER),artifact()),"experiment_context_scope_mismatch"),
    (lambda: ReadoutSpec("readout","unknown",None),"invalid_readout_kind"),
    (lambda: ReadoutSpec("readout","categorical","mg/L"),"categorical_readout_has_unit"),
    (lambda: ReadoutSpec("readout","numeric","mg/L","s"),"unexpected_readout_axis"),
    (lambda: ReplicateRole("r","unknown"),"invalid_replicate_role"),
    (lambda: replace(experiment().expectations[0],sample=None),"expectation_sample_required"),
    (lambda: replace(experiment().expectations[0],readout=None),"readout_spec_required"),
    (lambda: replace(experiment().expectations[0],replicate=None),"replicate_role_required"),
    (lambda: replace(experiment(),identity=None),"experiment_identity_required"),
    (lambda: replace(experiment(),protocol=None),"protocol_context_required"),
    (lambda: replace(experiment(),protocol=ProtocolContext(METHOD,artifact(scope=OTHER),artifact(scope=OTHER))),"experiment_protocol_scope_mismatch"),
    (lambda: replace(experiment(),samples=()),"experiment_sample_bound"),
    (lambda: replace(experiment(),samples=[specimen()]),"experiment_sample_bound"),
    (lambda: replace(experiment(),samples=(None,)),"sample_context_required"),
    (lambda: replace(experiment(),samples=(specimen(),)*257),"experiment_sample_bound"),
    (lambda: replace(experiment(),samples=(specimen(),)*2),"duplicate_experiment_sample"),
    (lambda: replace(experiment(),expectations=()),"expectation_bound"),
    (lambda: replace(experiment(),expectations=(experiment().expectations[0],)*1025),"expectation_bound"),
    (lambda: replace(experiment(),expectations=(None,)),"measurement_expectation_required"),
    (lambda: replace(experiment(),expectations=experiment().expectations*2),"duplicate_expectation"),
    (lambda: replace(experiment(),expectations=(replace(experiment().expectations[0],sample=experiment().expectations[0].sample.model_copy(update={"sample_id":"absent"})),)),"expectation_sample_unbound"),
])
def test_invalid_contexts_are_rejected(factory,reason):
    with pytest.raises(ExperimentError,match=reason):
        factory()


def test_missing_units_remain_invalid_for_numeric_and_series():
    for kind in ("numeric","series"):
        with pytest.raises(MeasurementError):
            ReadoutSpec("r",kind,None)


def test_foreign_sample_scope_is_rejected():
    sample = specimen(False).sample.record
    foreign = SampleDefinition(sample.model_copy(update={
        "reference":sample.reference.model_copy(update={"scope":OTHER}),
        "candidate":sample.candidate.model_copy(update={"scope":OTHER}),"identity_evidence":artifact(scope=OTHER)}))
    with pytest.raises(ExperimentError,match="experiment_sample_scope_mismatch"):
        replace(experiment(),samples=(SampleContext(foreign,None),))
