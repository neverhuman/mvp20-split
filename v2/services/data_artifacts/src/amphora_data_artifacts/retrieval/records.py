"""Scoped immutable reconstruction and corpus serialization; no external I/O."""

from amphora_contracts_representations import IndexGeneration
from sqlalchemy import text

from ..persistence.evidence_records import SCOPE, _lock
from ..representations.storage.records import load_profile
from .lifecycle import GenerationPhase
from .mapping import plan_from_wire
from .validation import identifier, require

GENERATION = SCOPE + " AND corpus_id=:corpus AND generation_id=:generation"


def key_for(principal, corpus_id, generation_id):
    identifier(corpus_id)
    identifier(generation_id)
    return principal.bindings | {"corpus": corpus_id, "generation": generation_id}


def lock_corpus(connection, principal, corpus_id):
    identifier(corpus_id)
    _lock(connection, principal.scope, [("index-corpus", corpus_id)])


def load_plan(connection, principal, corpus_id, generation_id):
    key = key_for(principal, corpus_id, generation_id)
    row = connection.execute(text("SELECT * FROM artifacts.index_generations WHERE " + GENERATION), key).mappings().one_or_none()
    if row is None:
        return None
    require(row["actor_id"] == principal.actor_id, "retrieval_generation_missing")
    wire = IndexGeneration.model_validate_json(bytes(row["canonical_bytes"]))
    profile = load_profile(connection, principal, wire.manifest.profile)
    plan = plan_from_wire(profile, wire)
    require(plan.actor_id == principal.actor_id and plan.reference.scope == principal.scope
        and plan.corpus_id == corpus_id and plan.generation_id == generation_id
        and plan.reference.sha256 == row["generation_sha256"], "retrieval_generation_conflict")
    members = connection.execute(text("SELECT binding_id FROM artifacts.index_generation_bindings WHERE " + GENERATION + " ORDER BY ordinal"), key).scalars().all()
    require(tuple(members) == tuple(b.reference.binding_id for b in plan.manifest.bindings), "retrieval_membership_conflict")
    return plan


def cursor(connection, key):
    row = connection.execute(text("SELECT *,expires_at>clock_timestamp() AS live FROM artifacts.index_generation_cursors WHERE " + GENERATION), key).mappings().one_or_none()
    require(row is not None, "retrieval_cursor_missing")
    return row


def event(connection, key, phase, sequence, reason, token=None, fence=0):
    identifier(reason)
    require(type(phase) is GenerationPhase, "retrieval_phase_required")
    require(1 <= sequence <= 9007199254740991, "retrieval_sequence_exhausted")
    connection.execute(text("INSERT INTO artifacts.index_generation_events "
        "(tenant_id,project_id,corpus_id,generation_id,sequence,phase,reason,token,fence) "
        "VALUES (:tenant,:project,:corpus,:generation,:sequence,:phase,:reason,:token,:fence)"),
        key | {"sequence": sequence, "phase": phase.value, "reason": reason, "token": token, "fence": fence})


def transition(connection, key, row, target, reason):
    GenerationPhase(row["phase"]).require_successor(target)
    sequence = row["sequence"] + 1
    event(connection, key, target, sequence, reason, row["token"], row["fence"])
    connection.execute(text("UPDATE artifacts.index_generation_cursors SET phase=:phase,sequence=:sequence WHERE " + GENERATION), key | {"phase": target.value, "sequence": sequence})
