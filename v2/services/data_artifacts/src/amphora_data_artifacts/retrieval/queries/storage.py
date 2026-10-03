"""Short query transactions; immutable intent and results with actor-scoped identity."""

from amphora_contracts_representations import RetrievalRecord, RetrieveRepresentations
from sqlalchemy import text

from ...persistence.evidence_records import SCOPE, _lock
from ...representations.bindings.records import published
from ..proof_records import publication
from ..records import key_for, load_plan
from ..validation import canonical, identifier, require
from .mapping import plan_from_request, record_from_wire, record_to_wire

QUERY = SCOPE + " AND actor_id=:actor AND retrieval_id=:retrieval"


def key_for_query(principal, retrieval_id):
    identifier(retrieval_id)
    return principal.bindings | {"retrieval": retrieval_id}


def lock_query(connection, principal, retrieval_id):
    _lock(connection, principal.scope, [("retrieval-query", principal.actor_id, retrieval_id)])
    return key_for_query(principal, retrieval_id)


def resolve(connection, principal, request):
    require(request.generation.scope == principal.scope, "retrieval_generation_missing")
    require(request.query.scope == principal.scope, "retrieval_binding_missing")
    generation = load_plan(connection, principal, request.generation.corpus_id, request.generation.generation_id)
    require(generation is not None, "retrieval_generation_missing")
    proof = publication(connection, key_for(principal, generation.corpus_id, generation.generation_id), generation)
    require(proof is not None, "retrieval_generation_unpublished")
    query = published(connection, principal, request.query.binding_id)
    require(query is not None, "retrieval_binding_missing")
    plan = plan_from_request(principal.actor_id, request, generation, query)
    return plan, proof


def intent(connection, key):
    return connection.execute(text("SELECT * FROM artifacts.retrieval_queries WHERE " + QUERY), key).mappings().one_or_none()


def require_intent(row, plan, request):
    retained = RetrieveRepresentations.model_validate_json(bytes(row["request_bytes"]))
    # Canonical filter set order, not incoming array order, defines replay identity.
    from .mapping import policy_from_wire
    require(
        retained.model_copy(update={"policy": request.policy}) == request
        and policy_from_wire(retained.policy) == plan.policy
        and row["query_sha256"] == plan.sha256,
        "retrieval_query_conflict",
    )


def admit(connection, key, plan, request):
    connection.execute(text("INSERT INTO artifacts.retrieval_queries "
        "(tenant_id,project_id,actor_id,retrieval_id,corpus_id,generation_id,generation_sha256,query_binding_id,query_sha256,request_bytes) "
        "VALUES (:tenant,:project,:actor,:retrieval,:corpus,:generation,:generation_sha,:binding,:query_sha,:body)"),
        key | {"corpus": plan.generation.corpus_id, "generation": plan.generation.generation_id,
            "generation_sha": plan.generation.reference.sha256, "binding": plan.query.reference.binding_id,
            "query_sha": plan.sha256, "body": canonical(request.model_dump(mode="json"))})


def result(connection, key, plan):
    row = connection.execute(text("SELECT * FROM artifacts.retrieval_results WHERE " + QUERY), key).mappings().one_or_none()
    if row is None:
        return None
    value = record_from_wire(plan.generation, RetrievalRecord.model_validate_json(bytes(row["canonical_bytes"])))
    require(value.plan == plan and value.plan.sha256 == row["query_sha256"]
        and value.sha256 == row["result_sha256"], "retrieval_result_conflict")
    return value


def save(connection, key, record, access):
    connection.execute(text("INSERT INTO artifacts.retrieval_results "
        "(tenant_id,project_id,actor_id,retrieval_id,query_sha256,result_sha256,canonical_bytes,access_bytes) "
        "VALUES (:tenant,:project,:actor,:retrieval,:query_sha,:result_sha,:body,:access)"),
        key | {"query_sha": record.plan.sha256, "result_sha": record.sha256,
            "body": canonical(record_to_wire(record).model_dump(mode="json")), "access": canonical(access.descriptor())})
