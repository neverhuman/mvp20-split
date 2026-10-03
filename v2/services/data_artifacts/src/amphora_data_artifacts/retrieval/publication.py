"""Owned backend comparison followed by atomic PostgreSQL generation selection."""

from amphora_contracts_core import SchemaRef
from sqlalchemy import text

from ..representations.storage.records import authorize
from ..source_rights.ledger import SourceRights
from .intents import authorize_plan
from .leases import GenerationLease, fenced
from .lifecycle import GenerationPhase
from .mapping import status_to_wire
from .projection import compare_projection, materialize
from .proof_records import head, publication, verification
from .records import cursor, key_for, load_plan, lock_corpus, transition
from .validation import canonical, record, require
from .verification import VerifiedProjection


class GenerationPublication:
    def __init__(self, reads, backend):
        record(backend.reference, SchemaRef)
        require(callable(backend.build) and callable(backend.inspect), "retrieval_backend_required")
        self.reads = reads
        self.engine = reads.engine
        self.backend = backend
        self.backend_reference = backend.reference

    def build_and_verify(self, principal, lease):
        authorize(principal, "representation_manage")
        principal.require("read")
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            plan, key, row = fenced(connection, principal, lease)
            require(
                plan.backend_profile == self.backend_reference == self.backend.reference,
                "retrieval_backend_profile",
            )
            authorize_plan(connection, principal, plan)
            if row["phase"] == "verified":
                proof = verification(connection, key, plan)
                require(proof.attempt == lease.attempt, "retrieval_verification_claim")
                return proof
        expected = materialize(principal, plan, self.reads)
        self.backend.build(lease.attempt.namespace, expected)
        observed = self.backend.inspect(lease.attempt.namespace)
        projection_sha = compare_projection(plan, expected, observed)
        proof = VerifiedProjection(
            lease.attempt, plan.manifest.watermark, projection_sha, len(expected.points)
        )
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            authorize_plan(connection, principal, plan)
            _, key, row = fenced(connection, principal, lease)
            if row["phase"] == "verified":
                require(verification(connection, key, plan) == proof, "retrieval_verification_conflict")
                return proof
            require(row["phase"] == "building", "retrieval_not_building")
            connection.execute(
                text(
                    "INSERT INTO artifacts.index_verifications "
                    "(tenant_id,project_id,corpus_id,generation_id,fence,canonical_bytes) VALUES "
                    "(:tenant,:project,:corpus,:generation,:fence,:body)"
                ),
                key | {"fence": lease.attempt.fence, "body": canonical(proof.descriptor())},
            )
            transition(connection, key, row, GenerationPhase.VERIFIED, "projection_verified")
        return proof

    def publish(self, principal, lease):
        authorize(principal, "representation_manage")
        require(type(lease) is GenerationLease, "retrieval_claim_required")
        ref = lease.attempt.generation
        require(ref.scope == principal.scope, "retrieval_claim_scope")
        key = key_for(principal, ref.corpus_id, ref.generation_id)
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            lock_corpus(connection, principal, ref.corpus_id)
            plan = load_plan(connection, principal, ref.corpus_id, ref.generation_id)
            require(plan is not None and plan.reference == ref, "retrieval_generation_conflict")
            done = publication(connection, key, plan)
            if done is not None:
                require(
                    done.attempt == lease.attempt and cursor(connection, key)["phase"] == "published",
                    "retrieval_publication_conflict",
                )
                return status_to_wire(plan, GenerationPhase.PUBLISHED)
            authorize_plan(connection, principal, plan)
            _, key, row = fenced(connection, principal, lease)
            require(row["phase"] == "verified", "retrieval_not_verified")
            proof = verification(connection, key, plan)
            require(proof.attempt == lease.attempt, "retrieval_verification_claim")
            require(
                head(connection, principal, plan.corpus_id) == plan.expected_head, "retrieval_head_conflict"
            )
            connection.execute(
                text(
                    "INSERT INTO artifacts.index_publications "
                    "(tenant_id,project_id,corpus_id,generation_id,generation_sha256,canonical_bytes) VALUES "
                    "(:tenant,:project,:corpus,:generation,:sha256,:body)"
                ),
                key | {"sha256": ref.sha256, "body": canonical(proof.descriptor())},
            )
            transition(connection, key, row, GenerationPhase.PUBLISHED, "generation_published")
            connection.execute(
                text(
                    "INSERT INTO artifacts.index_heads "
                    "(tenant_id,project_id,corpus_id,generation_id,generation_sha256) VALUES "
                    "(:tenant,:project,:corpus,:generation,:sha256) ON CONFLICT (tenant_id,project_id,corpus_id) "
                    "DO UPDATE SET generation_id=EXCLUDED.generation_id,generation_sha256=EXCLUDED.generation_sha256"
                ),
                key | {"sha256": ref.sha256},
            )
            return status_to_wire(plan, GenerationPhase.PUBLISHED)
