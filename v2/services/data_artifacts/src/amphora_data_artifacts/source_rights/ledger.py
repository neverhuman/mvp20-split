"""Current rights and provenance-derived read fences, wholly within the artifact owner."""

import json

from amphora_contracts_evidence import RightsRevisionRef, SourceRightsRevision
from sqlalchemy import text

from ..persistence.evidence_records import SCOPE, _canonical, _lock
from .ancestry import identities
from .model import RightsError, RightsPolicy, RightsSnapshot


class SourceRights:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def lock(connection, principal):
        # One bounded active campaign: serialize policy/binding commits by scope.
        # No filesystem or peer I/O is performed while holding this lock.
        _lock(connection, principal.scope, [("source_rights",)])

    @staticmethod
    def _record(connection, key):
        return connection.execute(text("SELECT canonical_bytes FROM artifacts.source_rights_revisions WHERE "
            + SCOPE + " AND rights_id=:rights AND revision=:revision"), key).scalar_one_or_none()

    def publish(self, principal, record):
        principal.require("manage_source_rights")
        RightsPolicy(record)
        ref = record.reference
        if ref.scope != principal.scope:
            raise RightsError("rights_scope_mismatch")
        key = principal.bindings | {"rights": ref.rights_id, "revision": ref.revision}
        body = _canonical(record)
        with self.engine.begin() as connection:
            self.lock(connection, principal)
            previous = self._record(connection, key)
            if previous is not None:
                if bytes(previous) != body:
                    raise RightsError("rights_revision_conflict")
                return record
            head = connection.execute(text("SELECT revision FROM artifacts.source_rights_heads WHERE "
                + SCOPE + " AND rights_id=:rights"), key).scalar_one_or_none()
            if head != (None if record.supersedes is None else record.supersedes.revision):
                raise RightsError("rights_head_conflict")
            connection.execute(text("INSERT INTO artifacts.source_rights_revisions "
                "(tenant_id,project_id,rights_id,revision,canonical_bytes) VALUES (:tenant,:project,:rights,:revision,:body)"),
                key | {"body": body})
            connection.execute(text("INSERT INTO artifacts.source_rights_heads (tenant_id,project_id,rights_id,revision) "
                "VALUES (:tenant,:project,:rights,:revision) ON CONFLICT (tenant_id,project_id,rights_id) "
                "DO UPDATE SET revision=EXCLUDED.revision"), key)
        return record

    def history(self, principal, rights_id, revision):
        principal.require("source_history")
        with self.engine.connect() as connection:
            raw = self._record(connection, principal.bindings | {"rights": rights_id, "revision": revision})
        return None if raw is None else SourceRightsRevision.model_validate_json(bytes(raw))

    def authorize(self, connection, principal, artifacts=(), declared=(), use="read"):
        self.lock(connection, principal)
        if use not in {"read", "process"}:
            raise RightsError("rights_use_denied")
        if any(ref.scope != principal.scope for ref in declared):
            raise RightsError("rights_scope_mismatch")
        refs = {(ref.rights_id, ref.revision): ref for ref in declared}
        ancestors = identities(connection, principal, artifacts)
        if ancestors:
            rows = connection.execute(text("SELECT DISTINCT convert_from(canonical_bytes,'UTF8')::jsonb->'rights' "
                "FROM artifacts.source_revisions WHERE " + SCOPE + " AND raw_artifact_id=ANY(:artifacts) LIMIT 257"),
                principal.bindings | {"artifacts": list(ancestors)}).scalars()
            for raw in rows:
                ref = RightsRevisionRef.model_validate_json(json.dumps(raw))
                refs[(ref.rights_id, ref.revision)] = ref
        if len(refs) > 256:
            raise RightsError("rights_lineage_limit")
        heads = {}
        policies = []
        for ref in refs.values():
            if ref.scope != principal.scope:
                raise RightsError("rights_scope_mismatch")
            key = principal.bindings | {"rights": ref.rights_id, "revision": ref.revision}
            if self._record(connection, key) is None:
                raise RightsError("rights_unavailable")
            row = connection.execute(text("SELECT r.revision,r.canonical_bytes FROM artifacts.source_rights_heads h "
                "JOIN artifacts.source_rights_revisions r USING(tenant_id,project_id,rights_id,revision) "
                "WHERE h.tenant_id=:tenant AND h.project_id=:project AND h.rights_id=:rights"), key).mappings().one_or_none()
            if row is None:
                raise RightsError("rights_unavailable")
            policies.append(RightsPolicy(SourceRightsRevision.model_validate_json(bytes(row["canonical_bytes"]))))
            heads[ref.rights_id] = row["revision"]
        now = connection.execute(text("SELECT clock_timestamp()")).scalar_one()
        for policy in policies:
            policy.require(use, now)
        return RightsSnapshot(principal.scope, tuple(artifacts), tuple(declared), use, tuple(sorted(heads.items())))

    def capture(self, principal, artifacts=(), declared=(), use="read"):
        with self.engine.begin() as connection:
            return self.authorize(connection, principal, artifacts, declared, use)

    def fence(self, connection, principal, snapshot):
        if snapshot.scope != principal.scope:
            raise RightsError("rights_scope_mismatch")
        actual = self.authorize(connection, principal, snapshot.artifacts, snapshot.declared, snapshot.use)
        if actual.heads != snapshot.heads:
            raise RightsError("rights_epoch_changed")

    def recheck(self, principal, snapshot):
        with self.engine.begin() as connection:
            self.fence(connection, principal, snapshot)
