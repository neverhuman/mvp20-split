"""Bounded private row reconstruction; immutable identities are verified on every load."""

from amphora_contracts_core import Scope
from amphora_contracts_representations import EncodingProfile, EncodingProfileRef, RepresentationVector
from pydantic import ValidationError
from sqlalchemy import text

from ...persistence.evidence_records import SCOPE, _lock
from ..identity import EncodingWorkIdentity
from ..mapping import profile_from_wire, profile_reference, vector_from_wire
from ..validation import RepresentationError, identifier, record, require

WORK = SCOPE + " AND work_sha256=:work"


def authorize(principal, action):
    principal.require(action)
    record(principal.scope, Scope)
    identifier(principal.actor_id)


def reference(value, scope):
    require(type(value) is EncodingProfileRef, "representation_profile_reference")
    try:
        value = EncodingProfileRef.model_validate(value.model_dump(warnings=False), strict=True)
    except ValidationError as error:
        raise RepresentationError("representation_profile_reference") from error
    require(value.scope == scope, "representation_scope")
    return value


def load_profile(connection, principal, ref):
    ref = reference(ref, principal.scope)
    row = (
        connection.execute(
            text(
                "SELECT profile_sha256,canonical_bytes FROM artifacts.encoding_profiles WHERE "
                + SCOPE
                + " AND profile_id=:profile AND version=:version"
            ),
            principal.bindings | {"profile": ref.profile_id, "version": ref.version},
        )
        .mappings()
        .one_or_none()
    )
    require(row is not None, "representation_profile_missing")
    value = profile_from_wire(EncodingProfile.model_validate_json(bytes(row["canonical_bytes"])))
    require(
        profile_reference(principal.scope, value) == ref and row["profile_sha256"] == ref.sha256,
        "representation_profile_conflict",
    )
    return value


def lock_work(connection, principal, work):
    require(type(work) is EncodingWorkIdentity and work.scope == principal.scope, "representation_scope")
    _lock(connection, principal.scope, [("encoding-work", work.sha256)])
    return principal.bindings | {"work": work.sha256}


def load_work(connection, principal, work):
    require(type(work) is EncodingWorkIdentity and work.scope == principal.scope, "representation_scope")
    row = (
        connection.execute(
            text("SELECT * FROM artifacts.encoding_work WHERE " + WORK),
            principal.bindings | {"work": work.sha256},
        )
        .mappings()
        .one_or_none()
    )
    require(row is not None, "representation_work_missing")
    ref = EncodingProfileRef(
        scope=principal.scope,
        profile_id=row["profile_id"],
        version=row["version"],
        sha256=row["profile_sha256"],
    )
    profile = load_profile(connection, principal, ref)
    actual = EncodingWorkIdentity(
        principal.scope, profile.reference, row["input_sha256"], row["context_sha256"]
    )
    require(actual == work, "representation_work_conflict")
    return profile


def result_row(connection, principal, work):
    return (
        connection.execute(
            text("SELECT * FROM artifacts.encoding_results WHERE " + WORK),
            principal.bindings | {"work": work.sha256},
        )
        .mappings()
        .one_or_none()
    )


def decode_result(principal, work, profile, row):
    result = vector_from_wire(
        principal.scope, profile, RepresentationVector.model_validate_json(bytes(row["canonical_bytes"]))
    )
    require(
        (result.input_sha256, result.context_sha256) == (work.input_sha256, work.context_sha256),
        "representation_work_conflict",
    )
    return result
