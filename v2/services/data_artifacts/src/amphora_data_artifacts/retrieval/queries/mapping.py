"""Explicit DTO projections and identity checks; owner lookup is a separate step."""

from amphora_contracts_representations import (
    RetrievalMatch,
    RetrievalPolicy,
    RetrievalRecord,
    RetrieveRepresentations,
)

from ...representations.mapping import _validated
from ..mapping import reference_to_wire
from ..validation import canonical, require
from .identity import QueryPlan
from .policy import BindingScore, QueryPolicy, binding_key
from .records import QueryRecord


def policy_to_wire(policy):
    require(type(policy) is QueryPolicy, "retrieval_policy_required")
    return RetrievalPolicy.model_validate_json(canonical(policy.descriptor()))


def policy_from_wire(policy):
    policy = _validated(policy, RetrievalPolicy)
    return QueryPolicy(policy.top_k, policy.bindings)


def plan_from_request(actor_id, request, generation, query):
    request = _validated(request, RetrieveRepresentations)
    require(request.generation == reference_to_wire(generation.reference), "retrieval_query_generation")
    require(request.query == query.reference, "retrieval_query_binding")
    return QueryPlan(request.retrieval_id, actor_id, generation, query, policy_from_wire(request.policy))


def record_to_wire(record):
    require(type(record) is QueryRecord, "retrieval_record_required")
    plan = record.plan
    members = {binding_key(b.reference): b for b in plan.generation.manifest.bindings}
    return RetrievalRecord(
        wire_version="1", retrieval_id=plan.retrieval_id, actor_id=plan.actor_id,
        generation=reference_to_wire(plan.generation.reference), query=plan.query,
        policy=policy_to_wire(plan.policy), query_sha256=plan.sha256,
        matches=tuple(RetrievalMatch(binding=members[binding_key(s.binding)], score=s.value) for s in record.matches),
        sha256=record.sha256,
    )


def record_from_wire(generation, value):
    value = _validated(value, RetrievalRecord)
    require(value.generation == reference_to_wire(generation.reference), "retrieval_query_generation")
    plan = QueryPlan(value.retrieval_id, value.actor_id, generation, value.query, policy_from_wire(value.policy))
    require(plan.sha256 == value.query_sha256, "retrieval_query_digest")
    result = QueryRecord(plan, tuple(BindingScore(m.binding.reference, m.score) for m in value.matches))
    require(result.sha256 == value.sha256, "retrieval_result_digest")
    require(record_to_wire(result) == value, "retrieval_result_projection")
    return result
