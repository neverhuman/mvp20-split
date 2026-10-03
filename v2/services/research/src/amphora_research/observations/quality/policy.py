"""Reviewed action prerequisites preserve exploratory weaknesses without global gating."""
import hashlib
import json
from dataclasses import dataclass, replace

from amphora_contracts_core import SchemaRef

from ...experiments.model import Experiment
from ..identity import identifier, require
from ..matching import ObservationMatch
from ..normalization.catalog import ConversionCatalog
from ..normalization.transform import NormalizationTargets, NormalizedMeasurement
from ..records import Observation
from .review import ObservationUseReview


@dataclass(frozen=True, slots=True)
class UseRequirements:
    available_value: bool
    passed_controls: bool
    bound_state: bool
    excluded_flags: tuple[str, ...]

    def __post_init__(self):
        require(all(type(value) is bool for value in (self.available_value,self.passed_controls,self.bound_state)),"explicit_use_requirement_required")
        require(type(self.excluded_flags) is tuple and len(self.excluded_flags) <= 64,"use_flag_bound")
        for flag in self.excluded_flags:
            identifier(flag)
        require(len(set(self.excluded_flags)) == len(self.excluded_flags),"duplicate_use_flag")

    def descriptor(self):
        return {"available_value":self.available_value,"passed_controls":self.passed_controls,
            "bound_state":self.bound_state,"excluded_flags":list(self.excluded_flags)}


@dataclass(frozen=True, slots=True)
class ObservationUsePolicy:
    profile_id: str
    version: str
    action: str
    requirements: UseRequirements
    normalization: ConversionCatalog | None = None

    def __post_init__(self):
        for name in (self.profile_id,self.version,self.action):
            identifier(name)
        require(type(self.requirements) is UseRequirements,"use_requirements_required")
        require(self.normalization is None or type(self.normalization) is ConversionCatalog,"use_normalization_catalog_required")

    @property
    def reference(self):
        descriptor = {"format":"research.observation-use.v1","profile_id":self.profile_id,"version":self.version,
            "action":self.action,"requirements":self.requirements.descriptor(),
            "normalization":None if self.normalization is None else self.normalization.reference.model_dump(mode="json")}
        body = json.dumps(descriptor,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
        return SchemaRef(schema_id="research.observation-use",version="1",sha256=hashlib.sha256(body).hexdigest())

    def review(self, observation, experiment):
        require(type(observation) is Observation and type(experiment) is Experiment,"observation_use_context_required")
        raw_match = ObservationMatch.reconcile(observation,experiment)
        match,normalization = raw_match,None
        if raw_match.reasons == ("readout_unit_mismatch",) and self.normalization is not None:
            expected = experiment.expectation(observation.binding.target.expectation_id)
            targets = NormalizationTargets(expected.readout.unit,expected.readout.x_unit)
            normalization = NormalizedMeasurement.evaluate(self.normalization,observation.value,targets)
            if normalization.normalized is not None:
                match = ObservationMatch.reconcile(replace(observation,value=normalization.normalized),experiment)
        requirements = self.requirements
        blockers,gaps,focus = [],[],[]
        quality = observation.quality
        if quality.controls != "passed":
            focus.append("controls_"+quality.controls)
            if requirements.passed_controls:
                (blockers if quality.controls == "failed" else gaps).append("controls_"+quality.controls)
        if quality.flags:
            focus.append("reported_quality_flags")
        if set(quality.flags) & set(requirements.excluded_flags):
            blockers.append("reported_flag_excluded")
        if not observation.value_available:
            focus.append("measurement_unavailable")
            if requirements.available_value:
                gaps.append("measurement_unavailable")
        if not match.state_known:
            focus.append("material_state_unknown")
            if requirements.bound_state:
                gaps.append("material_state_unknown")
        else:
            expected = experiment.expectation(observation.binding.target.expectation_id)
            state = experiment.sample(expected.sample).state
            if state.preparation.posture == "unknown":
                focus.append("preparation_unknown")
            if not state.features:
                focus.append("material_features_unreported")
            elif any(feature.evidence.basis == "unknown" for feature in state.features):
                focus.append("material_feature_unknown")
        if match.reasons:
            focus.extend(match.reasons)
        if normalization is not None and normalization.reason is not None:
            focus.append(normalization.reason)
        return ObservationUseReview(observation,raw_match,match,normalization,tuple(blockers),tuple(gaps),tuple(dict.fromkeys(focus)))
