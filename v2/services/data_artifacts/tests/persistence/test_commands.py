"""Opt-in integration tests against the labeled disposable PostgreSQL fixture."""

import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import psycopg
import pytest
from amphora_contracts_commands import CanonicalCommand
from amphora_contracts_core import WireModel
from amphora_data_artifacts.persistence.commands import (
    CommandConflict,
    CommandStore,
    TerminalDisposition,
)
from amphora_data_artifacts.persistence.migrate import upgrade
from postgres_fixture import owned_state
from sqlalchemy import URL, create_engine, text

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






class Payload(WireModel):
    value: int


def make_command(value=1, key=None):
    return CanonicalCommand.parse(json.dumps({"identity": {"schema_version":"1", "actor_id":"worker",
        "scope":{"tenant_id":"local","project_id":"command-probe"}, "command_family":"test.storage",
        "command_id":key or uuid.uuid4().hex}, "payload":{"value":value}}), Payload)


@pytest.fixture
def store(fixture_state):
    state=fixture_state
    host,port=state["endpoint"].split(":")
    url=URL.create("postgresql+psycopg",username="artifact_service",password=state["password"],
                   host=host,port=int(port),database=state["database"])
    engine=create_engine(url)
    try:
        yield CommandStore(engine)
    finally:
        engine.dispose()


def test_competing_identical_and_conflicting_commands(store,monkeypatch):
    barrier=Barrier(2,timeout=10)
    pids=[]
    original=CommandStore.transact
    def simultaneous(self,operation):
        def gated(connection):
            pids.append(connection.execute(text("SELECT pg_backend_pid()")).scalar_one())
            barrier.wait()
            return operation(connection)
        return original(self,gated)
    monkeypatch.setattr(CommandStore,"transact",simultaneous)
    command=make_command()
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts=list(pool.map(store.register,[command,command]))
    assert len(set(pids))==2
    assert receipts[0]==receipts[1]
    monkeypatch.setattr(CommandStore,"transact",original)
    with pytest.raises(CommandConflict,match="command_identity_conflict"):
        store.register(make_command(2,command.identity.command_id))


def test_receipt_and_domain_write_rollback_together(store):
    command=make_command()
    record=store.register(command)
    disposition=TerminalDisposition("rejected",b'{"reason_code":"fixture_rejected"}')
    with pytest.raises(RuntimeError,match="fault_after_receipt"):
        with store.engine.begin() as connection:
            store.finish(connection,command,disposition)
            raise RuntimeError("fault_after_receipt")
    assert store.register(command)==record
    with store.engine.begin() as connection:
        finished=store.finish(connection,command,disposition)
    assert store.register(command)==finished
    with store.engine.begin() as connection:
        assert store.finish(connection,command,TerminalDisposition("accepted",b'{}'))==finished
    with store.engine.connect() as connection:
        with pytest.raises(ValueError,match="Caller-owned"):
            store.finish(connection,command,disposition)


def test_registration_rolls_back_if_outer_primitive_fails(store):
    command=make_command()
    with pytest.raises(ValueError):
        store.transact(lambda connection: (_ for _ in ()).throw(ValueError("injected")))
    assert store.register(command).status=="pending"


def test_real_serialization_conflict_retries_whole_transaction(store,fixture_state):
    from postgres_fixture import sql
    sql(fixture_state,"GRANT UPDATE ON artifacts.fixture_probe TO artifact_service;",role="artifact_migrator")
    barrier=Barrier(2,timeout=10)
    retry_store=CommandStore(store.engine.execution_options(isolation_level="SERIALIZABLE"))
    counts=[0,0]
    def worker(index):
        def update(connection):
            counts[index]+=1
            old=connection.execute(text("SELECT id FROM artifacts.fixture_probe")).scalar_one()
            if counts[index]==1:
                barrier.wait()
            connection.execute(text("UPDATE artifacts.fixture_probe SET id=:new WHERE id=:old"),
                               {"new":old+1,"old":old})
        retry_store.transact(update)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(worker,[0,1]))
        assert sorted(counts)==[1,2]
        with store.engine.connect() as connection:
            assert connection.execute(text("SELECT id FROM artifacts.fixture_probe")).scalar_one()==3
    finally:
        with store.engine.begin() as connection:
            connection.execute(text("UPDATE artifacts.fixture_probe SET id=1"))


def test_retry_exhaustion_is_bounded_and_not_a_success_receipt(store):
    from sqlalchemy.exc import DBAPIError
    attempts=[]
    def fail(connection):
        attempts.append(1)
        connection.execute(text("DO $$ BEGIN RAISE EXCEPTION 'injected serialization failure' "
                                "USING ERRCODE='40001'; END $$"))
    with pytest.raises(DBAPIError):
        store.transact(fail)
    assert len(attempts)==3
