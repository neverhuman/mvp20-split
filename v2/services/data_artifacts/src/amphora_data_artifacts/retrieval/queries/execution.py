"""Bounded external reads and exact retained-vector comparison outside SQL locks."""

from amphora_contracts_representations import RepresentationVector

from ...representations.mapping import vector_from_wire
from ..manifest import point_id
from ..projection import ProjectionPoint
from ..validation import require
from .policy import BindingScore
from .records import QueryRecord


def vector(principal, profile, binding, reads):
    stored, raw = reads.content(principal, binding.vector.artifact_id)
    require(stored.reference == binding.vector, "retrieval_vector_artifact")
    encoded = vector_from_wire(principal.scope, profile, RepresentationVector.model_validate_json(raw))
    require(encoded.input_sha256 == binding.source.sha256, "retrieval_vector_input")
    return encoded.vector.values


def execute(principal, plan, proof, access, reads, backend):
    require(backend.reference == plan.generation.backend_profile, "retrieval_backend_profile")
    profile = plan.generation.manifest.profile
    query = vector(principal, profile, plan.query, reads)
    expected = {
        point_id(b): ProjectionPoint(point_id(b), b.profile, b.reference, vector(principal, profile, b, reads))
        for b in access.eligible
    }
    # An explicitly empty authorized selection needs no backend availability claim.
    observed = backend.query(proof.attempt.namespace, query, tuple(expected)) if expected else ()
    require(type(observed) is tuple and len(observed) <= 256, "retrieval_query_response")
    scores = []
    for item in observed:
        point = getattr(item, "point", None)
        require(type(point) is ProjectionPoint, "retrieval_query_point")
        require(expected.get(point.point_id) == point, "retrieval_query_content")
        scores.append(BindingScore(point.binding, getattr(item, "score", None)))
    return QueryRecord(plan, plan.policy.rank(access.eligible, tuple(scores)))
