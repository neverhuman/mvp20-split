"""Opt-in integration tests against the labeled disposable PostgreSQL fixture."""

import os

import psycopg
import pytest
from amphora_campaign_runtime.persistence.migrate import upgrade
from postgres_fixture import owned_state
from sqlalchemy import URL

pytestmark = [pytest.mark.postgres, pytest.mark.skipif(
    os.environ.get("AMPHORA_TEST_POSTGRES") != "1", reason="Explicit PostgreSQL fixture opt-in required")]


@pytest.fixture(scope="module")
def fixture_state():
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="runtime_migrator", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    upgrade(url.render_as_string(hide_password=False))
    upgrade(url.render_as_string(hide_password=False))
    return state


@pytest.fixture
def connection(fixture_state):
    state = fixture_state
    host, port = state["endpoint"].split(":")
    conn = psycopg.connect(host=host, port=int(port), dbname=state["database"],
                          user="runtime_service", password=state["password"], connect_timeout=5)
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


def seed_run(conn, run_id="run-1", project="test"):
    conn.execute("INSERT INTO runtime.runs (tenant_id,project_id,run_id,fixture_id,plan_sha256,"
                 "input_snapshot,status,budget_limit) VALUES ('local',%s,%s,'fixture',%s,'{}','running',2)",
                 (project, run_id, "a" * 64))


def seed_activation(conn):
    conn.execute("INSERT INTO runtime.activations (tenant_id,project_id,run_id,activation_id,invocation_id,"
                 "specification,status) VALUES ('local','test','run-1','activation-1','inv-1','{}','queued')")


def test_global_admission_scope_and_budget_constraints(connection):
    seed_run(connection)
    with pytest.raises(psycopg.errors.UniqueViolation), connection.transaction():
        seed_run(connection, "run-2", "other")
    with pytest.raises(psycopg.errors.CheckViolation), connection.transaction():
        connection.execute("UPDATE runtime.runs SET reserved=2, spent=1")
    with pytest.raises(psycopg.errors.ForeignKeyViolation), connection.transaction():
        connection.execute("INSERT INTO runtime.activations (tenant_id,project_id,run_id,activation_id,"
                           "invocation_id,specification,status) VALUES "
                           "('local','other','run-1','a','i','{}','queued')")


def test_attempt_uniqueness_and_scope(connection):
    seed_run(connection)
    seed_activation(connection)
    statement = ("INSERT INTO runtime.attempts (tenant_id,project_id,run_id,activation_id,attempt_id,"
                 "fence,worker_id,lease_expires_at,status) VALUES "
                 "('local',%s,'run-1','activation-1',%s,1,'worker',now() + interval '30 seconds','leased')")
    connection.execute(statement, ("test", "attempt-1"))
    with pytest.raises(psycopg.errors.UniqueViolation), connection.transaction():
        connection.execute(statement, ("test", "attempt-2"))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), connection.transaction():
        connection.execute(statement, ("other", "attempt-3"))


def test_identity_and_cross_owner_permissions(connection):
    seed_run(connection)
    for statement in ["UPDATE runtime.runs SET plan_sha256='b'",
                      "DELETE FROM runtime.runs",
                      "CREATE TABLE runtime.forbidden (id int)",
                      "SELECT * FROM artifacts.fixture_probe",
                      "SELECT * FROM runtime.alembic_version"]:
        with pytest.raises(psycopg.errors.InsufficientPrivilege), connection.transaction():
            connection.execute(statement)


def test_command_receipt_requires_terminal_evidence(connection):
    connection.execute("INSERT INTO runtime.commands (tenant_id,project_id,actor_id,family,command_id,"
                       "operation_id,profile,request_sha256,canonical_bytes) VALUES "
                       "('local','test','actor','cancel','cmd','op','v1',%s,%s)", ("a" * 64, b"{}"))
    with pytest.raises(psycopg.errors.CheckViolation), connection.transaction():
        connection.execute("UPDATE runtime.commands SET status='accepted'")
    with pytest.raises(psycopg.errors.InsufficientPrivilege), connection.transaction():
        connection.execute("UPDATE runtime.commands SET request_sha256=%s", ("b" * 64,))
    connection.execute("UPDATE runtime.commands SET status='rejected', receipt='{}', terminal_at=now()")
    assert connection.execute("SELECT status FROM runtime.commands WHERE tenant_id='local' AND project_id='test'").fetchone() == ("rejected",)


def test_rollback_removes_transition_and_audit(connection):
    seed_run(connection)
    connection.execute("INSERT INTO runtime.audit_events (event_id,tenant_id,project_id,run_id,revision,"
                       "ordinal,payload) VALUES ('event-1','local','test','run-1',0,0,'{}')")
    connection.rollback()
    assert connection.execute("SELECT count(*) FROM runtime.runs").fetchone()[0] == 0
    assert connection.execute("SELECT count(*) FROM runtime.audit_events").fetchone()[0] == 0


def test_accepted_result_is_unique_and_bound_to_exact_attempt(connection):
    seed_run(connection)
    seed_activation(connection)
    connection.execute("INSERT INTO runtime.attempts (tenant_id,project_id,run_id,activation_id,attempt_id,"
                       "fence,worker_id,lease_expires_at,status) VALUES "
                       "('local','test','run-1','activation-1','attempt-1',1,'worker',now(),'leased')")
    connection.execute("INSERT INTO runtime.commands (tenant_id,project_id,actor_id,family,command_id,"
                       "operation_id,profile,request_sha256,canonical_bytes) VALUES "
                       "('local','test','actor','complete','cmd','op','v1',%s,%s)", ("a" * 64, b"{}"))
    connection.execute("INSERT INTO runtime.completion_intents (tenant_id,project_id,intent_id,run_id,"
                       "activation_id,attempt_id,fence,operation_id,semantic_sha256,output_bindings,status) "
                       "VALUES ('local','test','intent-1','run-1','activation-1','attempt-1',1,'op',%s,'{}','prepared')",
                       ("b" * 64,))
    statement = ("INSERT INTO runtime.accepted_completions (tenant_id,project_id,completion_id,intent_id,"
                 "run_id,activation_id,attempt_id,fence,result,reservations) VALUES "
                 "('local','test',%s,'intent-1','run-1','activation-1',%s,1,'{}','[]')")
    with pytest.raises(psycopg.errors.ForeignKeyViolation), connection.transaction():
        connection.execute(statement, ("bad", "other-attempt"))
    connection.execute(statement, ("completion-1", "attempt-1"))
    with pytest.raises(psycopg.errors.UniqueViolation), connection.transaction():
        connection.execute(statement, ("completion-2", "attempt-1"))
    with pytest.raises(psycopg.errors.InsufficientPrivilege), connection.transaction():
        connection.execute("UPDATE runtime.accepted_completions SET result='{}'")
