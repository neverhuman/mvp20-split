"""Reconstruct immutable verification/publication against retained attempt authority."""

import json

from sqlalchemy import text

from .identity import BuildAttempt, GenerationReference
from .records import GENERATION
from .validation import canonical, require
from .verification import VerifiedProjection


def verification(connection, key, plan):
    row = (
        connection.execute(
            text("SELECT fence,canonical_bytes FROM artifacts.index_verifications WHERE " + GENERATION), key
        )
        .mappings()
        .one_or_none()
    )
    require(row is not None, "retrieval_verification_missing")
    body = json.loads(bytes(row["canonical_bytes"]))
    attempt = BuildAttempt(plan.reference, body["token"], body["fence"])
    proof = VerifiedProjection(
        attempt, body["manifest_sha256"], body["projection_sha256"], body["point_count"]
    )
    require(
        body == proof.descriptor()
        and canonical(body) == bytes(row["canonical_bytes"])
        and proof.manifest_sha256 == plan.manifest.watermark
        and proof.point_count == len(plan.manifest.bindings)
        and row["fence"] == attempt.fence,
        "retrieval_verification_conflict",
    )
    retained = (
        connection.execute(
            text(
                "SELECT token,namespace FROM artifacts.index_build_attempts WHERE "
                + GENERATION
                + " AND fence=:fence"
            ),
            key | {"fence": attempt.fence},
        )
        .mappings()
        .one_or_none()
    )
    require(
        retained is not None
        and retained["token"] == attempt.token
        and retained["namespace"] == attempt.namespace,
        "retrieval_attempt_conflict",
    )
    return proof


def publication(connection, key, plan):
    raw = connection.execute(
        text("SELECT canonical_bytes FROM artifacts.index_publications WHERE " + GENERATION), key
    ).scalar_one_or_none()
    if raw is None:
        return None
    proof = verification(connection, key, plan)
    require(bytes(raw) == canonical(proof.descriptor()), "retrieval_publication_conflict")
    return proof


def head(connection, principal, corpus_id):
    row = (
        connection.execute(
            text(
                "SELECT generation_id,generation_sha256 FROM artifacts.index_heads "
                "WHERE tenant_id=:tenant AND project_id=:project AND corpus_id=:corpus"
            ),
            principal.bindings | {"corpus": corpus_id},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return None
    return GenerationReference(principal.scope, corpus_id, row["generation_id"], row["generation_sha256"])
