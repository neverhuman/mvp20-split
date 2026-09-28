"""Immutable registration and explicit lifecycle changes; no implicit promotion."""

import json

from amphora_contracts_tools import ChangeRelease, RegisterRelease
from sqlalchemy import text

from ..descriptors.identity import ReleaseDocument
from ..descriptors.validation import DescriptorValidator
from ..persistence.store import scope_bindings
from .model import RegistryDenied, ReleaseRecord

SELECT = ("SELECT r.*,s.status,s.revision FROM registry.releases r JOIN registry.release_states s "
          "USING(tenant_id,project_id,descriptor_sha256) WHERE r.tenant_id=:tenant AND r.project_id=:project ")


def read_release(connection, scope, digest):
    row = connection.execute(text(SELECT + "AND r.descriptor_sha256=:digest"),
                             {**scope_bindings(scope), "digest": digest}).mappings().one_or_none()
    if row is None:
        raise RegistryDenied("release_not_found")
    return ReleaseRecord.from_row(row)


class Releases:
    def register(self, connection, scope, raw, factory):
        payload = RegisterRelease.model_validate_json(json.dumps(raw))
        document = ReleaseDocument.from_descriptor(payload.descriptor)
        document.verify_lock(payload.expected_lock)
        if not DescriptorValidator().validate(payload.descriptor).valid:
            raise RegistryDenied("descriptor_invalid")
        identity = document.identity
        if len(identity.release) > 128:
            raise RegistryDenied("release_identity_too_long")
        values = {**scope_bindings(scope), "capability": identity.capability, "release": identity.release,
                  "contract": identity.contract_version, "digest": document.digest}
        existing = connection.execute(text(SELECT + "AND r.capability_id=:capability AND r.release=:release "
            "AND r.contract_version=:contract"), values).mappings().one_or_none()
        if existing is not None:
            record = ReleaseRecord.from_row(existing)
            record.document.require_identical_registration(document)
            return factory.accepted("existing", release=record.to_wire(scope))
        connection.execute(text("INSERT INTO registry.releases (tenant_id,project_id,capability_id,release,contract_version,"
            "descriptor_sha256,canonical_bytes,descriptor,lock_entry) VALUES "
            "(:tenant,:project,:capability,:release,:contract,:digest,:canonical,CAST(:descriptor AS jsonb),CAST(:lock AS jsonb))"),
            {**values, "canonical": document.canonical_bytes, "descriptor": payload.descriptor.model_dump_json(),
             "lock": document.to_lock().model_dump_json()})
        connection.execute(text("INSERT INTO registry.release_states (tenant_id,project_id,descriptor_sha256,revision,status) "
                                "VALUES (:tenant,:project,:digest,1,'registered')"), values)
        return factory.accepted("registered", release=read_release(connection, scope, document.digest).to_wire(scope))

    def change(self, connection, scope, action, raw, factory):
        payload = ChangeRelease.model_validate_json(json.dumps(raw))
        record = read_release(connection, scope, payload.release.descriptor_sha256)
        record.document.verify_lock(payload.release)
        lifecycle = record.lifecycle.changed(action, payload.expected_revision)
        # This profile can activate only synthetic pure tools; real scientific promotion is a later authority.
        if action == "activate" and (record.descriptor.authority_ceiling != "synthetic_only"
                                    or record.descriptor.tool.side_effects != "pure"
                                    or "synthetic-tests" not in record.descriptor.tool.applicability):
            raise RegistryDenied("activation_profile_denied")
        connection.execute(text("UPDATE registry.release_states SET status=:status,revision=:revision "
            "WHERE tenant_id=:tenant AND project_id=:project AND descriptor_sha256=:digest"),
            {**scope_bindings(scope), "digest": record.document.digest, "status": lifecycle.status, "revision": lifecycle.revision})
        return factory.accepted(lifecycle.status, release=read_release(connection, scope, record.document.digest).to_wire(scope))
