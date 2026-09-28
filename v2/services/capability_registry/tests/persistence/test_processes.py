"""Actual owner processes and PostgreSQL barriers; not installed HTTP evidence."""

import copy
import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time
import uuid
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path

import pytest
from amphora_capability_registry.descriptors.identity import ReleaseDocument
from amphora_contracts_tools import ReleaseDescriptor
from export_schemas import ROOT
from sqlalchemy import text

pytestmark = pytest.mark.postgres
SCRIPT = Path(__file__).absolute().parents[1] / "acceptance/owner_process.py"


class OwnerProcess:
    def __init__(self, env, action, payload, *, actor="admin", command_id=None, barrier=None):
        self.application = "registry-probe-"+uuid.uuid4().hex
        self.command = json.loads(env.raw(action, payload, actor, command_id))
        child_env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}}
        child_env["AMPHORA_REGISTRY_DATABASE_URL"] = env.engine.url.render_as_string(hide_password=False)
        self.child = subprocess.Popen([sys.executable, "-I", str(SCRIPT)], cwd=Path(os.environ["TEMP"]),
            env=child_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        actions = [action]
        self.send(json.dumps({"family": "registry."+action, "command": self.command, "actions": actions,
                              "application_name": self.application, "barrier": barrier}))

    def _read(self):
        for line in self.child.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def send(self, value="continue"):
        self.child.stdin.write(value+"\n")
        self.child.stdin.flush()

    def receive(self):
        line = self.lines.get(timeout=20)
        if line is None:
            raise AssertionError("Owner process exited before expected marker: "+self.child.stderr.read()[-1500:])
        return json.loads(line)

    def __enter__(self):
        try:
            self.ready = self.receive()
            assert self.ready["stage"] == "ready"
            return self
        except BaseException:
            self.__exit__()
            raise

    def __exit__(self, *_):
        self.closed = {"pid": self.child.pid, "killed": self.child.poll() is None,
                       "observed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        if self.child.poll() is None:
            self.child.kill()
        self.child.wait(timeout=10)
        self.reader.join(timeout=2)
        for stream in (self.child.stdin, self.child.stdout, self.child.stderr):
            stream.close()


def registration(env):
    return {"scope": env.scope.model_dump(), "descriptor": env.fixture["descriptor"], "expected_lock": env.fixture["lock"]}


def evidence(env, scenario, observations):
    sources = ROOT/"services/capability_registry/src"
    digest = hashlib.sha256()
    for path in sorted(sources.rglob("*")):
        if path.suffix in {".py", ".sql"}:
            digest.update(path.relative_to(sources).as_posix().encode()+b"\0"+path.read_bytes())
    value = {"scenario": scenario, "status": "passed", "scope": env.scope.model_dump(),
             "source_sha256": digest.hexdigest(), "descriptor_sha256": env.fixture["sha256"],
             "observations": observations, "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    destination = ROOT/".test-results/registry-processes"/env.scope.project_id
    destination.mkdir(parents=True, exist_ok=True)
    (destination/(scenario+".json")).write_text(json.dumps({"sha256": hashlib.sha256(body).hexdigest(), "evidence": value}, indent=2)+"\n", encoding="utf-8")


def wait_for_lock(env, child):
    deadline = time.monotonic()+8
    while time.monotonic() < deadline:
        with env.engine.connect() as connection:
            waiting = connection.execute(text("SELECT count(*) FROM pg_stat_activity WHERE application_name=:name "
                                              "AND wait_event='advisory'"), {"name": child.application}).scalar_one()
        if waiting:
            return
        time.sleep(0.03)
    raise AssertionError("Contending owner did not reach the actual PostgreSQL advisory lock")


@pytest.mark.parametrize("same_command", [False, True], ids=["separate-commands", "same-command"])
def test_duplicate_and_changed_registration_in_separate_processes(registry_env, same_command):
    env = registry_env
    payload = registration(env)
    with ExitStack() as stack:
        processes = [stack.enter_context(OwnerProcess(env, "register", payload,
                     command_id="same-command" if same_command else f"command-{index}")) for index in range(2)]
        for child in processes:
            child.send()
        receipts = [child.receive()["receipt"] for child in processes]
    if same_command:
        assert receipts[0] == receipts[1] and receipts[0]["reason_code"] == "registered"
    else:
        assert sorted(receipt["reason_code"] for receipt in receipts) == ["existing", "registered"]
        assert receipts[0]["release"] == receipts[1]["release"]
    changed = copy.deepcopy(payload)
    changed["descriptor"]["tool"]["purpose"] = "Changed descriptor"
    changed["expected_lock"] = ReleaseDocument.from_descriptor(ReleaseDescriptor.model_validate_json(json.dumps(changed["descriptor"]))).to_lock().model_dump(mode="json")
    with OwnerProcess(env, "register", changed) as child:
        child.send()
        conflict = child.receive()["receipt"]
        assert conflict["reason_code"] == "immutable_release_conflict"
    response = env.client.get("/v1/releases/"+payload["expected_lock"]["descriptor_sha256"], headers=env.headers)
    assert response.json() == receipts[0]["release"]
    with env.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM registry.releases WHERE tenant_id=:tenant AND project_id=:project"),
            {"tenant": env.scope.tenant_id, "project": env.scope.project_id}).scalar_one() == 1
    evidence(env, "REG-01-same" if same_command else "REG-01-distinct", [
        *[p.ready for p in processes], {"command_ids": [p.command["identity"]["command_id"] for p in processes],
        "operation_ids": [receipt["operation_id"] for receipt in receipts], "conflict_operation": conflict["operation_id"],
        "release_count": 1, "public_read_preserved": True}])


@pytest.mark.parametrize("barrier", ["prepared", "committed"])
def test_killed_owner_rolls_back_or_replays_one_original_receipt(registry_env, barrier):
    env = registry_env
    payload = registration(env)
    with OwnerProcess(env, "register", payload, command_id="interrupted", barrier=barrier) as child:
        child.send()
        marker = child.receive()
        assert marker["stage"] == barrier
        # Exiting kills the real process while the transaction/reply barrier remains held.
    with OwnerProcess(env, "register", payload, command_id="interrupted") as restarted:
        restarted.send()
        receipt = restarted.receive()["receipt"]
    assert receipt["reason_code"] == "registered"
    assert child.closed["killed"]
    assert (receipt["operation_id"] == marker["operation_id"]) is (barrier == "committed")
    assert env.execute("register", payload, command_id="interrupted").model_dump(mode="json") == receipt
    with env.engine.connect() as connection:
        values = {"tenant": env.scope.tenant_id, "project": env.scope.project_id}
        for table in ("commands", "releases", "release_states", "audit_events"):
            assert connection.execute(text(f"SELECT count(*) FROM registry.{table} WHERE tenant_id=:tenant AND project_id=:project"), values).scalar_one() == 1
    evidence(env, "REG-02-"+barrier, [child.ready, marker, child.closed, restarted.ready,
        {"command_id": "interrupted", "replayed_operation": receipt["operation_id"], "one_release_receipt_audit": True}])


@pytest.mark.parametrize("action", ["drain", "revoke"])
def test_heartbeat_and_resolution_wait_for_actual_lifecycle_transaction(registry_env, action):
    env = registry_env
    payload = registration(env)
    assert env.execute("register", payload).status == "accepted"
    lock = payload["expected_lock"]
    assert env.execute("activate", {"release": lock, "expected_revision": 1}).status == "accepted"
    assert env.execute("deploy", {"deployment_id": "d1", "release": lock, "architecture": "x86_64", "operating_system": "windows", "workers": ["worker"]}).status == "accepted"
    report = {"deployment_id": "d1", "replica_id": "r1", "expected_revision": 0, "free_slots": 1, "ttl_seconds": 30}
    assert env.execute("heartbeat", report, principal=env.worker).status == "accepted"
    tool = payload["descriptor"]["tool"]
    need = {"release": lock, "context": "synthetic-tests", "inputs": tool["inputs"], "outputs": tool["outputs"]}
    with ExitStack() as stack:
        changer = stack.enter_context(OwnerProcess(env, action, {"release": lock, "expected_revision": 2}, barrier="prepared"))
        changer.send()
        prepared = changer.receive()
        assert prepared["stage"] == "prepared"
        heartbeat = stack.enter_context(OwnerProcess(env, "heartbeat", {**report, "expected_revision": 1}, actor="worker"))
        resolver = stack.enter_context(OwnerProcess(env, "resolve", need))
        for child in (heartbeat, resolver):
            child.send()
            wait_for_lock(env, child)
        changer.send()
        assert changer.receive()["receipt"]["status"] == "accepted"
        assert heartbeat.receive()["receipt"]["reason_code"] == "deployment_not_active"
        assert resolver.receive()["receipt"]["reason_code"] == "release_not_active"
    evidence(env, "REG-03-"+action, [changer.ready, prepared, heartbeat.ready, resolver.ready,
        {"waiting_on_postgres_advisory_lock": [heartbeat.application, resolver.application],
         "command_ids": [p.command["identity"]["command_id"] for p in (changer, heartbeat, resolver)],
         "heartbeat": "deployment_not_active", "resolution": "release_not_active"}])
