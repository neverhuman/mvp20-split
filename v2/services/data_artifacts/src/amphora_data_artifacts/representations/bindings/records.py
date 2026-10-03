"""Binding row reconstruction and short owner-local locking primitives."""

import json
from dataclasses import dataclass

from amphora_contracts_representations import EncodeSourceRequest, RepresentationBinding
from sqlalchemy import text

from ...persistence.evidence_records import SCOPE, _lock
from ..identity import EncodingWorkIdentity
from ..storage.records import load_profile
from ..validation import require
from .identity import SourceBindingIdentity
from .receipts import validate_binding_projection

BINDING = SCOPE + " AND binding_id=:binding"


def lock_binding(connection, principal, binding_id):
    _lock(connection, principal.scope, [("encoding-binding", binding_id)])
    return principal.bindings | {"binding": binding_id}


@dataclass(frozen=True, slots=True)
class BindingJob:
    identity: SourceBindingIdentity
    work: EncodingWorkIdentity


def load_job(connection, principal, binding_id):
    row = (
        connection.execute(
            text("SELECT * FROM artifacts.encoding_binding_jobs WHERE " + BINDING + " AND actor_id=:actor"),
            principal.bindings | {"binding": binding_id},
        )
        .mappings()
        .one_or_none()
    )
    require(row is not None, "representation_binding_missing")
    request = EncodeSourceRequest.model_validate_json(bytes(row["canonical_bytes"]))
    identity = SourceBindingIdentity.prepare(principal, request)
    profile = load_profile(connection, principal, identity.profile)
    work = EncodingWorkIdentity(principal.scope, profile.reference, identity.source.sha256, None)
    require(
        identity.binding_id == binding_id and work.sha256 == row["work_sha256"],
        "representation_binding_conflict",
    )
    return BindingJob(identity, work)


def published(connection, principal, binding_id):
    row = connection.execute(
        text("SELECT canonical_bytes FROM artifacts.representation_bindings WHERE " + BINDING),
        principal.bindings | {"binding": binding_id},
    ).scalar_one_or_none()
    if row is None:
        return None
    result = RepresentationBinding.model_validate_json(bytes(row))
    require(
        result.reference.scope == principal.scope and result.reference.binding_id == binding_id,
        "representation_binding_conflict",
    )
    return validate_binding_projection(principal.scope, result)


def event_bytes(value):
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode()
    require(0 < len(raw) <= 65536, "representation_event_bound")
    return raw
