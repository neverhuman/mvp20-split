"""Immutable enrollment from owned tasks/policies and persisted parent traces."""

from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_planning import ExtractionTraceRef
from sqlalchemy import text

from ..context import AttemptBinding
from ..context.policy import require
from ..repair.binding import RepairRoot
from . import family_state
from .budget import BudgetLedger
from .extraction import ExtractionJournal
from .journal import KEY, PlanningJournal


@dataclass(frozen=True)
class RepairMembership:
    root: RepairRoot
    canonical: bytes
    registered_at: datetime


class RepairJournal:
    def __init__(self, engine):
        self.engine = engine
        self.journal = PlanningJournal(engine)
        self.extraction = ExtractionJournal(engine)

    def _root(self, connection, key, principal):
        row = connection.execute(text("SELECT * FROM planning.repair_families WHERE " + KEY), key).mappings().first()
        require(row is not None, "repair_root_unknown")
        task = self.extraction._task(connection, principal, row["task_id"])
        policy = BudgetLedger._policy(connection, key)
        require(task is not None and policy is not None, "stored_repair_root")
        root = RepairRoot.bind(task.snapshot, policy)
        require(root.engagement_id == key["engagement"] and root.task.request.sha256 == row["request_sha256"]
                and policy.sha256 == row["policy_sha256"] and root.canonical == bytes(row["canonical_bytes"]),
                "stored_repair_root")
        return root

    def _member(self, connection, key, principal):
        row = family_state.member(connection, key)
        if row is None:
            return None
        root = self._root(connection, {**key, "engagement": row["root_engagement_id"]}, principal)
        stored = self.extraction._task(connection, principal, row["task_id"])
        require(stored is not None and stored.snapshot.document().engagement.engagement_id == key["engagement"],
                "stored_repair_member")
        parent = None
        if key["engagement"] != root.engagement_id:
            root.validate_child(stored.snapshot)
            parent = ExtractionTraceRef(scope=principal.scope, trace_id=row["parent_trace_id"], sha256=row["parent_sha256"])
            trace = self.extraction._trace(connection, principal, parent)
            require(trace is not None, "stored_repair_parent")
            parent_key = self.journal._key(trace.projection.document().attempt.engagement)
            parent_member = family_state.member(connection, parent_key)
            require(parent_member is not None and parent_member["root_engagement_id"] == root.engagement_id,
                    "stored_repair_parent")
        canonical = root.member_bytes(stored.snapshot, parent)
        require(canonical == bytes(row["canonical_bytes"]), "stored_repair_member")
        return RepairMembership(root, canonical, row["registered_at"])

    def _insert_member(self, connection, key, principal, root, task, parent=None):
        connection.execute(text("INSERT INTO planning.repair_members "
            "(tenant_id,project_id,engagement_id,task_id,root_engagement_id,parent_trace_id,parent_sha256,canonical_bytes) "
            "VALUES (:tenant,:project,:engagement,:task,:root,:parent,:digest,:content) ON CONFLICT DO NOTHING"),
            {**key, "task": task.document().task_id, "root": root.engagement_id,
             "parent": None if parent is None else parent.trace_id,
             "digest": None if parent is None else parent.sha256, "content": root.member_bytes(task, parent)})
        result = self._member(connection, key, principal)
        require(result.canonical == root.member_bytes(task, parent), "repair_membership_conflict")
        return result

    def enroll_root(self, principal, task_id, reviewed_policy):
        principal.require("record_requests", principal.scope)
        principal.require("record_attempts", principal.scope)
        with self.engine.begin() as connection:
            family_state.lineage_lock(connection, self.extraction._scope(principal))
            task = self.extraction._task(connection, principal, task_id)
            require(task is not None, "extraction_task_unknown")
            root = RepairRoot.bind(task.snapshot, reviewed_policy)
            key = self.journal._key(task.snapshot.document().engagement)
            family_state.family_lock(connection, key, root.engagement_id)
            family_state.request_lock(connection, key)
            existing = self._member(connection, key, principal)
            if existing is not None:
                require(existing.root.canonical == root.canonical and existing.root.engagement_id == key["engagement"],
                        "repair_membership_conflict")
                return existing
            ledger = BudgetLedger(self.engine)
            policy = ledger._policy(connection, key)
            if policy is not None:
                require(policy.canonical == root.policy.canonical, "budget_policy_conflict")
            attempts = connection.execute(text("SELECT ordinal FROM planning.attempts WHERE " + KEY), key).scalars().all()
            for ordinal in attempts:
                binding = AttemptBinding(task.snapshot.request, ordinal)
                require(ledger._reservation(connection, {**key, "ordinal": ordinal}, binding, policy) is not None,
                        "unbudgeted_attempt_history")
            if policy is None:
                connection.execute(text("INSERT INTO planning.budget_policies "
                    "(tenant_id,project_id,engagement_id,request_sha256,policy_sha256,canonical_bytes) "
                    "VALUES (:tenant,:project,:engagement,:request,:policy,:content)"),
                    {**key, "request": task.snapshot.request.sha256, "policy": root.policy.sha256,
                     "content": root.policy.canonical})
            connection.execute(text("INSERT INTO planning.repair_families "
                "(tenant_id,project_id,engagement_id,task_id,request_sha256,policy_sha256,canonical_bytes) "
                "VALUES (:tenant,:project,:engagement,:task,:request,:policy,:content)"),
                {**key, "task": task_id, "request": task.snapshot.request.sha256,
                 "policy": root.policy.sha256, "content": root.canonical})
            return self._insert_member(connection, key, principal, root, task.snapshot)

    def enroll_child(self, principal, root_ref, task_id, parent):
        principal.require("record_requests", root_ref.scope)
        principal.require("record_attempts", root_ref.scope)
        parent = ExtractionTraceRef.model_validate_json(parent.model_dump_json(warnings=False))
        root_key = self.journal._key(root_ref)
        with self.engine.begin() as connection:
            family_state.lineage_lock(connection, root_key)
            family_state.family_lock(connection, root_key, root_ref.engagement_id)
            root = self._root(connection, root_key, principal)
            stored = self.extraction._task(connection, principal, task_id)
            require(stored is not None, "extraction_task_unknown")
            task = root.validate_child(stored.snapshot)
            key = self.journal._key(task.document().engagement)
            family_state.request_lock(connection, key)
            trace = self.extraction._trace(connection, principal, parent)
            require(trace is not None, "extraction_parent_unknown")
            parent_key = self.journal._key(trace.projection.document().attempt.engagement)
            parent_member = family_state.member(connection, parent_key)
            require(parent_member is not None and parent_member["root_engagement_id"] == root.engagement_id,
                    "repair_parent_membership")
            require(parent_key["engagement"] != key["engagement"], "repair_parent_identity")
            require(trace.projection.document().repair_depth < 16, "extraction_repair_depth")
            existing = self._member(connection, key, principal)
            if existing is not None:
                require(existing.canonical == root.member_bytes(task, parent), "repair_membership_conflict")
                return existing
            attempts = connection.execute(text("SELECT count(*) FROM planning.attempts WHERE " + KEY), key).scalar_one()
            require(attempts == 0, "repair_child_has_attempts")
            return self._insert_member(connection, key, principal, root, task, parent)

    def read(self, principal, reference):
        principal.require("read_attempts", reference.scope)
        with self.engine.connect() as connection:
            return self._member(connection, self.journal._key(reference), principal)
