"""Opt-in integration tests against the labeled disposable PostgreSQL fixture."""

import os

import psycopg
import pytest
from amphora_data_artifacts.persistence.migrate import upgrade
from postgres_fixture import owned_state
from sqlalchemy import URL

pytestmark = [pytest.mark.postgres, pytest.mark.skipif(
    os.environ.get("AMPHORA_TEST_POSTGRES") != "1", reason="Explicit PostgreSQL fixture opt-in required")]


@pytest.fixture(scope="module")
def fixture_state():
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="artifact_migrator", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    upgrade(url.render_as_string(hide_password=False))
    upgrade(url.render_as_string(hide_password=False))
    return state


@pytest.fixture
def connection(fixture_state):
    state = fixture_state
    host, port = state["endpoint"].split(":")
    conn = psycopg.connect(host=host, port=int(port), dbname=state["database"],
                          user="artifact_service", password=state["password"], connect_timeout=5)
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


def seed_artifact(conn, artifact_id="artifact-1", storage_key="bytes_1"):
    conn.execute("INSERT INTO artifacts.catalog (tenant_id,project_id,artifact_id,content_sha256,"
                 "size_bytes,media_type,schema_ref,storage_key) VALUES "
                 "('local','test',%s,%s,10,'application/json','{}',%s)",
                 (artifact_id, "a" * 64, storage_key))


def test_reservation_scope_content_and_unique_output_binding(connection):
    seed_artifact(connection)
    seed_artifact(connection, "artifact-2", "bytes_2")
    statement = ("INSERT INTO artifacts.reservations (tenant_id,project_id,reservation_id,artifact_id,"
                 "content_sha256,runtime_owner,intent_id,output_binding,semantic_sha256) VALUES "
                 "('local',%s,%s,%s,%s,'runtime','intent-1','out',%s)")
    connection.execute(statement, ("test", "reserve-1", "artifact-1", "a" * 64, "b" * 64))
    with pytest.raises(psycopg.errors.UniqueViolation), connection.transaction():
        connection.execute(statement, ("test", "reserve-2", "artifact-2", "a" * 64, "b" * 64))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), connection.transaction():
        connection.execute(statement, ("other", "reserve-3", "artifact-1", "a" * 64, "b" * 64))
    with pytest.raises(psycopg.errors.CheckViolation), connection.transaction():
        connection.execute("UPDATE artifacts.reservations SET status='released'")


def test_catalog_immutable_and_other_owner_inaccessible(connection):
    seed_artifact(connection)
    for statement in ["UPDATE artifacts.catalog SET size_bytes=20", "DELETE FROM artifacts.catalog",
                      "UPDATE artifacts.reservations SET intent_id='different'",
                      "SELECT * FROM runtime.runs", "CREATE TABLE artifacts.forbidden (id int)"]:
        with pytest.raises(psycopg.errors.InsufficientPrivilege), connection.transaction():
            connection.execute(statement)


def test_generated_keys_and_byte_bounds(connection):
    for key in ["../outside", "/absolute", "a/b", "a\\b"]:
        with pytest.raises(psycopg.errors.CheckViolation), connection.transaction():
            seed_artifact(connection, storage_key=key)
    with pytest.raises(psycopg.errors.CheckViolation), connection.transaction():
        connection.execute("INSERT INTO artifacts.uploads (tenant_id,project_id,upload_id,"
                           "expected_descriptor,storage_key,bytes_received) VALUES "
                           "('local','test','upload-1','{}','tmp_1',-1)")


def test_rollback_does_not_publish_catalog_reference(connection):
    seed_artifact(connection)
    connection.rollback()
    assert connection.execute("SELECT count(*) FROM artifacts.catalog WHERE "
                              "tenant_id='local' AND project_id='test' AND artifact_id='artifact-1'").fetchone()[0] == 0
