"""Immutable complete projection; no hidden acceptance or promotion in serialization."""
from dataclasses import dataclass

from amphora_contracts_fitness import FitnessAxisRecord, FitnessEvidenceRecord, FitnessProjection, FitnessRef
from amphora_contracts_research import MeasurementQuantity

from .policy import require
from .reuse import canonical, digest


def bounded(value):
    body = canonical(value)
    require(len(body) <= 8388608, "fitness_document_limit")
    return body


@dataclass(frozen=True, slots=True)
class FitnessDocument:
    record: FitnessProjection
    content: bytes

    @classmethod
    def prepare(cls, configured, request, actor, assembly, sources):
        configured.bind(request)
        evidence = assembly.evidence
        axes = tuple(FitnessAxisRecord(objective_id=axis.specification.objective_id,
            status="unavailable" if axis.reasons else "available",
            value=None if axis.reasons else MeasurementQuantity(value=str(axis.amount), unit=axis.specification.unit),
            observations=tuple(row.observation.reference for row in axis.reviews), reasons=axis.reasons) for axis in assembly.axes)
        reference = FitnessRef(scope=configured.record.scope, fitness_id=request.fitness_id, sha256="0"*64)
        projection = FitnessProjection(wire_version="1", authority="synthetic_owner_projection", reuse_authority="none",
            reference=reference, actor_id=actor, profile=configured.record, request=request,
            declared_identity=assembly.key.record, identity=assembly.key.to_wire(),
            evidence=FitnessEvidenceRecord(candidate=evidence.candidate, interpretation=evidence.interpretation,
                eligibility=evidence.eligibility, synthesis=evidence.synthesis), axes=axes,
            disposition=assembly.disposition, synthesis_status=assembly.synthesis_status, focus=assembly.focus,
            sources=tuple(sorted(sources, key=lambda source:source.artifact_id)))
        payload = projection.model_dump(mode="json", exclude={"reference"})
        reference = reference.model_copy(update={"sha256":digest({"format":"research.fitness.v1",
            "scope":reference.scope.model_dump(mode="json"), "fitness_id":reference.fitness_id, "projection":payload})})
        projection = projection.model_copy(update={"reference":reference})
        return cls(projection, bounded(projection.model_dump(mode="json")))
