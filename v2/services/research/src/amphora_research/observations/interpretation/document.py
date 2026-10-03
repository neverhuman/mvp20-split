"""Compute content-addressed projections from domain inputs, never caller-supplied verdicts."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_research import InterpretationRef, NormalizationProjection, ObservationUseProjection

from ...experiments import wire as experiment_wire
from .. import wire as observation_wire
from ..identity import identifier, require
from ..normalization.transform import NormalizationTargets, NormalizedMeasurement
from ..quality.batch import ObservationUseBatch
from .wire import normalization_to_wire, review_to_wire


def canonical(payload):
    body = json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
    require(len(body) <= 8388608,"interpretation_document_byte_limit")
    return body


@dataclass(frozen=True, slots=True)
class InterpretationDocument:
    record: NormalizationProjection | ObservationUseProjection
    canonical_bytes: bytes

    @classmethod
    def prepare(cls, profile, request, actor, observations, experiment=None, consumed=()):
        request = profile.bind(request)
        identifier(actor)
        require(type(observations) is tuple,"interpretation_observations_required")
        if profile.kind == "normalization":
            require(experiment is None and len(observations) == 1,"normalization_input_shape")
            original = observation_wire.to_wire(observations[0])
            require(original.reference == request.observation,"interpretation_observation_mismatch")
            targets = NormalizationTargets(request.targets.value_unit,request.targets.coordinate_unit)
            result = NormalizedMeasurement.evaluate(profile.policy,observations[0].value,targets)
            model = NormalizationProjection
            fields = {"observation":original,"result":normalization_to_wire(result)}
        else:
            require(experiment is not None,"interpretation_experiment_required")
            plan = experiment_wire.to_wire(experiment)
            require(plan.reference == request.experiment,"interpretation_experiment_mismatch")
            require(tuple(observation_wire.reference_to_wire(item.identity.reference) for item in observations) == request.observations,
                "interpretation_observation_mismatch")
            result = ObservationUseBatch.assess(profile.policy,experiment,observations)
            model = ObservationUseProjection
            fields = {"experiment":plan,"reviews":tuple(review_to_wire(item) for item in result.reviews),
                "usable":tuple(observation_wire.reference_to_wire(item) for item in result.usable),
                "focus":tuple(observation_wire.reference_to_wire(item) for item in result.focus),
                "missing_expectations":result.missing_expectations}
        sources = tuple(consumed)+tuple(item.source for item in observations)
        require(all(type(item) is ArtifactRef and item.scope == profile.scope for item in sources),"interpretation_source_scope")
        sources = tuple(sorted(set(sources),key=lambda item:item.artifact_id))
        require(len(sources) <= 128,"interpretation_source_limit")
        require(len({item.artifact_id for item in sources}) == len(sources),"interpretation_source_conflict")
        fields.update(wire_version="1",authority="policy_interpretation",kind=profile.kind,
            actor_id=actor,profile=profile.to_wire(),sources=sources)
        # The placeholder lets the DTO serialize nested records consistently. It is
        # removed before hashing; kind/scope/id remain explicit in the hash envelope.
        reference = InterpretationRef(scope=profile.scope,kind=profile.kind,
            interpretation_id=request.interpretation_id,sha256="0"*64)
        draft = model(reference=reference,**fields)
        payload = draft.model_dump(mode="json",exclude={"reference"})
        digest = hashlib.sha256(canonical({"format":"research.interpretation.v1",
            "scope":profile.scope.model_dump(mode="json"),"interpretation_id":request.interpretation_id,"projection":payload})).hexdigest()
        record = model(reference=reference.model_copy(update={"sha256":digest}),**fields)
        return cls(record,canonical(record.model_dump(mode="json")))
