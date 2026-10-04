"""One family-before-request lock order and conservative aggregate accounting."""

import json

from sqlalchemy import text

from ..budget.charge import BudgetCharge
from ..budget.policy import ReservationDemand
from ..context.policy import require
from ..providers.wire import observation_document

KEY = "tenant_id=:tenant AND project_id=:project AND engagement_id=:engagement"


def lineage_lock(connection, key):
    # Enrollment and trace linking serialize before family/request locks. Otherwise
    # a legacy parent could become a family root during an outsider's trace write.
    token = json.dumps(["planning.repair-lineage.v1", key["tenant"], key["project"]])
    connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:token,0))"), {"token": token})


def member(connection, key):
    return connection.execute(text("SELECT * FROM planning.repair_members WHERE " + KEY), key).mappings().first()


def family_lock(connection, key, root):
    token = json.dumps(["planning.repair-family.v1", key["tenant"], key["project"], root])
    connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:token,0))"), {"token": token})


def request_lock(connection, key):
    token = json.dumps(["planning.request.v1", key["tenant"], key["project"], key["engagement"]])
    connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:token,0))"), {"token": token})


def lock_request(connection, key):
    before = member(connection, key)
    root = None if before is None else before["root_engagement_id"]
    if root is not None:
        family_lock(connection, key, root)
    request_lock(connection, key)
    after = member(connection, key)
    # Never take a family lock while holding an earlier un-enrolled request lock.
    require(root == (None if after is None else after["root_engagement_id"]), "repair_membership_changed")
    return after


def totals(connection, key, root):
    parameters = {**key, "root": root}
    held = dict(connection.execute(text("SELECT count(*) AS attempts, "
        "COALESCE(SUM(GREATEST(s.input_tokens,r.input_tokens,l.input_tokens)+"
        "GREATEST(s.output_tokens,r.output_tokens,l.output_tokens)),0) AS tokens, "
        "COALESCE(SUM(GREATEST(s.accounting_units,r.accounting_units,l.accounting_units)),0) AS units, "
        "COALESCE(bool_or(s.overage OR l.overage),false) AS overage "
        "FROM planning.repair_members m JOIN planning.reservations r "
        "USING(tenant_id,project_id,engagement_id) LEFT JOIN planning.settlements s "
        "USING(tenant_id,project_id,engagement_id,ordinal) LEFT JOIN planning.late_observations l "
        "USING(tenant_id,project_id,engagement_id,ordinal) "
        "WHERE m.tenant_id=:tenant AND m.project_id=:project AND m.root_engagement_id=:root"),
        parameters).mappings().one())
    # A process may die after recording a reply but before its separate settlement.
    # Reconcile those known reports without inserting or changing historical rows.
    pending = connection.execute(text("SELECT r.*,o.canonical_bytes, "
        "GREATEST(r.input_tokens,l.input_tokens) AS held_input, "
        "GREATEST(r.output_tokens,l.output_tokens) AS held_output, "
        "GREATEST(r.accounting_units,l.accounting_units) AS held_units "
        "FROM planning.repair_members m JOIN planning.reservations r USING(tenant_id,project_id,engagement_id) "
        "JOIN planning.observations o USING(tenant_id,project_id,engagement_id,ordinal) "
        "LEFT JOIN planning.settlements s USING(tenant_id,project_id,engagement_id,ordinal) "
        "LEFT JOIN planning.late_observations l USING(tenant_id,project_id,engagement_id,ordinal) "
        "WHERE m.tenant_id=:tenant AND m.project_id=:project AND m.root_engagement_id=:root AND s.ordinal IS NULL"),
        parameters).mappings()
    for row in pending:
        wire = observation_document(bytes(row["canonical_bytes"]))
        require(wire.attempt.engagement.scope.tenant_id == row["tenant_id"] and
                wire.attempt.engagement.scope.project_id == row["project_id"] and
                wire.attempt.engagement.engagement_id == row["engagement_id"] and wire.attempt.ordinal == row["ordinal"],
                "stored_repair_observation")
        demand = ReservationDemand(wire.attempt, row["policy_sha256"], row["input_tokens"], row["output_tokens"], row["accounting_units"])
        charge = BudgetCharge.reconcile(demand, bytes(row["canonical_bytes"]))
        held["tokens"] += max(0, charge.input_tokens - row["held_input"]) + max(0, charge.output_tokens - row["held_output"])
        held["units"] += max(0, charge.accounting_units - row["held_units"])
        held["overage"] = held["overage"] or charge.overage
    return held


def require_budget(connection, key, membership, journal, principal, policy, demand):
    if membership is None:
        return
    root = membership["root_engagement_id"]
    root_key = {**key, "engagement": root}
    family = connection.execute(text("SELECT * FROM planning.repair_families WHERE " + KEY), root_key).mappings().one()
    require(family["policy_sha256"] == policy.sha256, "repair_policy_conflict")
    request = journal._request(connection, root_key, principal)
    require(request is not None and request.sha256 == family["request_sha256"], "stored_repair_root")
    held = totals(connection, key, root)
    limits = request.document().context.limits
    require(not held["overage"], "provider_usage_overage")
    require(held["attempts"] < limits.max_attempts, "repair_attempt_budget_exhausted")
    require(held["tokens"] + demand.tokens <= limits.total_tokens, "repair_token_budget_exhausted")
    require(held["units"] + demand.accounting_units <= limits.total_accounting_units,
            "repair_accounting_budget_exhausted")
