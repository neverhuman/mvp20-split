"""Actual owner admission and historical actor-owned generation reads."""

from amphora_contracts_core import SchemaRef
from amphora_contracts_representations import BuildIndexGeneration
from sqlalchemy import text

from ..representations.bindings.records import published
from ..representations.mapping import _validated
from ..representations.storage.records import authorize, load_profile
from ..source_rights.ledger import SourceRights
from .lifecycle import GenerationPhase
from .mapping import plan_from_request, plan_to_wire, status_to_wire
from .records import cursor, event, key_for, load_plan, lock_corpus
from .validation import canonical, record, require


def authorize_plan(connection, principal, plan):
    artifacts = tuple(b.vector.artifact_id for b in plan.manifest.bindings)
    return SourceRights(None).authorize(connection, principal, artifacts, use="process")


class GenerationIntents:
    def __init__(self, engine, backend_profile):
        record(backend_profile, SchemaRef)
        self.engine = engine
        self.backend_profile = backend_profile

    def prepare(self, principal, request):
        authorize(principal, "representation_manage")
        request = _validated(request, BuildIndexGeneration)
        key = key_for(principal, request.corpus_id, request.generation_id)
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            lock_corpus(connection, principal, request.corpus_id)
            existing = load_plan(connection, principal, request.corpus_id, request.generation_id)
            if existing is not None:
                proposed = plan_from_request(principal.scope, principal.actor_id, request,
                    existing.manifest.profile, existing.manifest.bindings, self.backend_profile)
                require(proposed == existing, "retrieval_generation_conflict")
                return status_to_wire(existing, GenerationPhase(cursor(connection, key)["phase"]))
            profile = load_profile(connection, principal, request.profile)
            bindings = tuple(published(connection, principal, ref.binding_id) for ref in request.bindings)
            require(all(b is not None for b in bindings), "retrieval_binding_missing")
            plan = plan_from_request(principal.scope, principal.actor_id, request, profile, bindings, self.backend_profile)
            authorize_plan(connection, principal, plan)
            ref = plan.manifest.profile_reference
            connection.execute(text("INSERT INTO artifacts.index_generations "
                "(tenant_id,project_id,corpus_id,generation_id,generation_sha256,actor_id,profile_id,version,profile_sha256,canonical_bytes) "
                "VALUES (:tenant,:project,:corpus,:generation,:sha256,:actor,:profile,:version,:profile_sha,:body)"),
                key | {"sha256": plan.reference.sha256, "profile": ref.profile_id, "version": ref.version,
                    "profile_sha": ref.sha256, "body": canonical(plan_to_wire(plan).model_dump(mode="json"))})
            connection.execute(text("INSERT INTO artifacts.index_generation_bindings "
                "(tenant_id,project_id,corpus_id,generation_id,ordinal,binding_id) VALUES "
                "(:tenant,:project,:corpus,:generation,:ordinal,:binding)"),
                [key | {"ordinal": i, "binding": b.reference.binding_id} for i,b in enumerate(bindings)])
            connection.execute(text("INSERT INTO artifacts.index_generation_cursors "
                "(tenant_id,project_id,corpus_id,generation_id,phase,sequence) VALUES "
                "(:tenant,:project,:corpus,:generation,'prepared',1)"), key)
            event(connection, key, GenerationPhase.PREPARED, 1, "admitted")
            return status_to_wire(plan, GenerationPhase.PREPARED)

    def read(self, principal, corpus_id, generation_id):
        authorize(principal, "representation_read")
        with self.engine.connect() as connection:
            plan = load_plan(connection, principal, corpus_id, generation_id)
            require(plan is not None, "retrieval_generation_missing")
            return status_to_wire(plan, GenerationPhase(cursor(connection, key_for(principal, corpus_id, generation_id))["phase"]))
