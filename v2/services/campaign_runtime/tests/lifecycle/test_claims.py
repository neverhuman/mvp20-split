"""Actual database claim, renewal and stale-fence oracles."""

import json
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_contracts_runtime import parse_command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


def command(env, family, payload, command_id=None, actor=None):
    return parse_command(family, json.dumps({"identity": {"command_family": family,
        "command_id": command_id or uuid.uuid4().hex, "actor_id": actor or env.principal.actor_id,
        "scope": env.principal.scope.model_dump()}, "payload": payload}))


def admitted(env):
    receipt = env.service.admit(env.principal, command(env, "runtime.admit_fixture", env.raw["payload"]))
    return receipt.outcome.committed.object_id


def claim(env, run, command_id=None):
    return RuntimeLeases(env.engine).claim(env.principal, command(env, "runtime.claim",
        {"run_id": run, "worker_id": env.principal.actor_id, "tool": env.raw["payload"]["invocations"][0]["tool"],
         "lease_seconds": 10}, command_id))


def renewal(env, invocation, command_id=None):
    return command(env, "runtime.renew", {"attempt": {"run_id": invocation.run_id,
        "invocation_id": invocation.invocation_id, "attempt_id": invocation.attempt_id, "fence": invocation.fence},
        "lease_seconds": 20}, command_id)


def run_row(env, run):
    with env.engine.connect() as conn:
        return conn.execute(text("SELECT * FROM runtime.runs WHERE run_id=:run"), {"run": run}).mappings().one()


def test_claim_replay_no_work_and_renewal_identity(fixture_env):
    e = fixture_env
    run = admitted(e)
    first = claim(e, run, "claim-1")
    assert first.outcome.status == "claimed"
    assert claim(e, run, "claim-1") == first
    assert claim(e, run).outcome.status == "no_eligible_work"
    invocation = first.outcome.invocation
    service = RuntimeLeases(e.engine)
    cmd = renewal(e, invocation)
    receipt = service.renew(e.principal, cmd)
    assert receipt.outcome.status == "accepted"
    assert receipt.outcome.committed.object_id == invocation.attempt_id
    assert service.renew(e.principal, cmd) == receipt
    state = run_row(e, run)
    assert (state["reserved"], state["spent"]) == (1, 0)


def test_expired_claim_requeues_with_new_fence_and_spends_once(fixture_env):
    e = fixture_env
    run = admitted(e)
    first = claim(e, run).outcome.invocation
    with e.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.attempts SET lease_expires_at=clock_timestamp()-interval '1 second' "
                          "WHERE run_id=:run AND attempt_id=:attempt"), {"run": run, "attempt": first.attempt_id})
    expired = RuntimeLeases(e.engine).renew(e.principal, renewal(e, first))
    assert expired.outcome.reason_code == "lease_expired"
    second = claim(e, run).outcome.invocation
    assert second.fence == first.fence + 1 and second.attempt_id != first.attempt_id
    stale = RuntimeLeases(e.engine).renew(e.principal, renewal(e, first))
    assert stale.outcome.reason_code == "stale_attempt"
    state = run_row(e, run)
    assert (state["reserved"], state["spent"]) == (1, 1)


def test_wrong_tool_has_no_work(fixture_env):
    e = fixture_env
    run = admitted(e)
    tool = {**e.raw["payload"]["invocations"][0]["tool"], "image_sha256": "d" * 64}
    response = RuntimeLeases(e.engine).claim(e.principal, command(e, "runtime.claim",
        {"run_id": run, "worker_id": e.principal.actor_id, "tool": tool}))
    assert response.outcome.status == "no_eligible_work"
    assert run_row(e, run)["reserved"] == 0


def test_two_processes_waiting_on_same_run_cannot_double_claim(fixture_env):
    e = fixture_env
    run = admitted(e)
    children = []
    applications = []
    try:
        with e.engine.begin() as guard:
            guard.execute(text("SELECT run_id FROM runtime.runs WHERE run_id=:run FOR UPDATE"), {"run": run})
            for index in range(2):
                actor = f"worker-{index + 1}"
                application = "claim-probe-" + uuid.uuid4().hex
                applications.append(application)
                cmd = command(e, "runtime.claim", {"run_id": run, "worker_id": actor,
                    "tool": e.raw["payload"]["invocations"][0]["tool"], "lease_seconds": 10}, actor=actor)
                child = subprocess.Popen([sys.executable, "-I", str(Path(__file__).with_name("claim_probe.py"))],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                children.append(child)
                child.stdin.write(json.dumps({"url": e.engine.url.render_as_string(hide_password=False),
                    "application": application, "scope": e.principal.scope.model_dump(), "actor": actor,
                    "command": cmd.canonical_bytes.decode()}) + "\n")
                child.stdin.flush()
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(c.stdout.readline) for c in children]
                try:
                    assert [f.result(timeout=15).strip() for f in futures] == ["ready", "ready"]
                except BaseException:
                    for child in children:
                        child.kill()
                    raise
            for child in children:
                child.stdin.write("claim\n")
                child.stdin.flush()
            deadline = time.monotonic() + 15
            while True:
                # Fresh connection/transaction avoids a cached pg_stat_activity snapshot.
                with e.engine.connect() as observer:
                    waiting = observer.execute(text("SELECT count(*) FROM pg_stat_activity WHERE "
                        "application_name IN (:a,:b) AND wait_event_type='Lock'"),
                        {"a": applications[0], "b": applications[1]}).scalar_one()
                if waiting == 2:
                    break
                assert time.monotonic() < deadline, "Both worker processes must contend on the held run lock"
                time.sleep(0.05)
        results = []
        for child in children:
            stdout, stderr = child.communicate(timeout=15)
            assert child.returncode == 0, stderr
            results.append(json.loads(stdout))
        assert sorted(r["outcome"]["status"] for r in results) == ["claimed", "no_eligible_work"]
        assert (run_row(e, run)["reserved"], run_row(e, run)["spent"]) == (1, 0)
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=10)


def test_renewal_rechecks_clock_after_waiting_for_run_lock(fixture_env):
    e = fixture_env
    run = admitted(e)
    invocation = claim(e, run).outcome.invocation
    application = "renew-probe-" + uuid.uuid4().hex
    engine = create_engine(e.engine.url, connect_args={"application_name": application})
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            with e.engine.begin() as guard:
                guard.execute(text("SELECT run_id FROM runtime.runs WHERE run_id=:run FOR UPDATE"), {"run": run})
                future = pool.submit(RuntimeLeases(engine).renew, e.principal, renewal(e, invocation))
                deadline = time.monotonic() + 15
                while True:
                    with e.engine.connect() as observer:
                        waiting = observer.execute(text("SELECT count(*) FROM pg_stat_activity WHERE "
                            "application_name=:name AND wait_event_type='Lock'"), {"name": application}).scalar_one()
                    if waiting:
                        break
                    assert time.monotonic() < deadline
                    time.sleep(0.05)
                guard.execute(text("UPDATE runtime.attempts SET lease_expires_at=clock_timestamp()-interval '1 second' "
                    "WHERE run_id=:run AND attempt_id=:attempt"), {"run": run, "attempt": invocation.attempt_id})
            assert future.result(timeout=15).outcome.reason_code == "lease_expired"
    finally:
        engine.dispose()


def test_public_claim_and_renew_routes(fixture_env):
    e = fixture_env
    run = admitted(e)
    cmd = command(e, "runtime.claim", {"run_id": run, "worker_id": e.principal.actor_id,
                                      "tool": e.raw["payload"]["invocations"][0]["tool"], "lease_seconds": 10})
    with TestClient(create_app(e.service, e.credentials)) as client:
        assert client.post("/v1/invocations/claim", content=cmd.canonical_bytes).status_code == 401
        headers = {"Authorization": "Bearer " + "x" * 32}
        response = client.post("/v1/invocations/claim", content=cmd.canonical_bytes, headers=headers)
        assert response.status_code == 200
        assert response.json()["outcome"]["status"] == "claimed"
        invocation = response.json()["outcome"]["invocation"]
        renewal_command = command(e, "runtime.renew", {"attempt": {
            "run_id": run, "invocation_id": invocation["invocation_id"],
            "attempt_id": invocation["attempt_id"], "fence": invocation["fence"]}})
        response = client.post("/v1/attempts/renew", content=renewal_command.canonical_bytes, headers=headers)
        assert response.json()["outcome"]["status"] == "accepted"
