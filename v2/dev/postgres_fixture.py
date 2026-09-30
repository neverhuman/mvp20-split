"""Explicit local PostgreSQL fixture; owns only resources it creates and labels."""

import argparse
import json
import secrets
import subprocess
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
STATE = ROOT / ".test-results/postgres-fixture.json"
IMAGE = "postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f"
LABEL = "amphora.fixture"
DATABASE = "amphora_bp02_test"


def docker(*args, input_text=None, check=True):
    result = subprocess.run(["docker", *args], input=input_text, capture_output=True, text=True)
    if check and result.returncode:
        raise RuntimeError(f"Docker operation failed: {args[0]}: {result.stderr[-1200:]}")
    return result


def sql(state, statement, role="postgres", database=DATABASE, check=True):
    return docker("exec", "-i", state["container"], "psql", "-X", "-v", "ON_ERROR_STOP=1",
                  "-U", role, "-d", database, "-At", input_text=statement, check=check)


def owned_state():
    state = json.loads(STATE.read_text())
    for kind, name in [("container", state["container"]), ("volume", state["volume"])]:
        obj = json.loads(docker(kind, "inspect", name).stdout)[0]
        labels = obj["Config"].get("Labels", {}) if kind == "container" else obj.get("Labels", {})
        if labels.get(LABEL) != state["token"]:
            raise RuntimeError("Fixture ownership mismatch; refusing operation")
    return state


def registry_owner(state):
    """Add only the new registry owner to the existing labeled disposable fixture."""
    for role in ("registry_migrator", "registry_service"):
        if sql(state, f"SELECT 1 FROM pg_roles WHERE rolname='{role}';").stdout.strip() != "1":
            sql(state, f"CREATE ROLE {role} LOGIN PASSWORD '{state['password']}';")
    sql(state, "GRANT CONNECT ON DATABASE amphora_bp02_test TO registry_migrator,registry_service; "
        "CREATE SCHEMA IF NOT EXISTS registry AUTHORIZATION registry_migrator; "
        "GRANT USAGE ON SCHEMA registry TO registry_service;")


def research_owner(state):
    """Add Research roles/schema to the existing labeled fixture without resetting data."""
    for role in ("research_migrator", "research_service"):
        if sql(state, f"SELECT 1 FROM pg_roles WHERE rolname='{role}';").stdout.strip() != "1":
            sql(state, f"CREATE ROLE {role} LOGIN PASSWORD '{state['password']}';")
    sql(state, "GRANT CONNECT ON DATABASE amphora_bp02_test TO research_migrator,research_service; "
        "CREATE SCHEMA IF NOT EXISTS research AUTHORIZATION research_migrator; "
        "GRANT USAGE ON SCHEMA research TO research_service;")


def ready(state):
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if docker("exec", state["container"], "pg_isready", "-U", "postgres", check=False).returncode == 0:
            return
        time.sleep(0.25)
    raise RuntimeError("PostgreSQL fixture did not become ready")


def start():
    if STATE.exists():
        raise RuntimeError("Fixture state exists; inspect/verify it instead of overwriting")
    token = uuid.uuid4().hex
    name = "amphora-bp02-" + token
    state = {"token": token, "container": name, "volume": name + "-data", "image": IMAGE,
             "database": DATABASE, "password": secrets.token_hex(24)}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    docker("volume", "create", "--label", f"{LABEL}={token}", state["volume"])
    docker("run", "--detach", "--name", name, "--label", f"{LABEL}={token}",
           "--restart", "no", "-e", "POSTGRES_PASSWORD=" + state["password"],
           "-p", "127.0.0.1::5432", "--mount",
           f"type=volume,source={state['volume']},target=/var/lib/postgresql/data", IMAGE)
    ready(state)
    sql(state, f"CREATE DATABASE {DATABASE};", database="postgres")
    # These names and passwords are fixture-generated constants, not user SQL.
    roles = ("runtime_migrator", "artifact_migrator", "runtime_service", "artifact_service")
    statements = [f"CREATE ROLE {role} LOGIN PASSWORD '{state['password']}';" for role in roles]
    statements += [
        "REVOKE ALL ON DATABASE amphora_bp02_test FROM PUBLIC;",
        "GRANT CONNECT ON DATABASE amphora_bp02_test TO " + ",".join(roles) + ";",
        "REVOKE CREATE ON SCHEMA public FROM PUBLIC;",
        "CREATE SCHEMA runtime AUTHORIZATION runtime_migrator;",
        "CREATE SCHEMA artifacts AUTHORIZATION artifact_migrator;",
        "GRANT USAGE ON SCHEMA runtime TO runtime_service;",
        "GRANT USAGE ON SCHEMA artifacts TO artifact_service;",
    ]
    sql(state, "\n".join(statements))
    print("Created labeled PostgreSQL fixture; connection state is in ignored .test-results.")


def verify():
    state = owned_state()
    ready(state)
    for schema, migrator, service in [("runtime", "runtime_migrator", "runtime_service"),
                                       ("artifacts", "artifact_migrator", "artifact_service")]:
        sql(state, f"CREATE TABLE IF NOT EXISTS {schema}.fixture_probe (id integer PRIMARY KEY); "
            f"GRANT SELECT, INSERT ON {schema}.fixture_probe TO {service};", role=migrator)
        sql(state, f"INSERT INTO {schema}.fixture_probe VALUES (1) ON CONFLICT DO NOTHING;", role=service)
        assert sql(state, f"SELECT count(*) FROM {schema}.fixture_probe;", role=service).stdout.strip() == "1"
        other = "artifacts" if schema == "runtime" else "runtime"
        for denied in [f"SELECT * FROM {other}.fixture_probe;", f"CREATE TABLE {schema}.forbidden (id int);",
                       f"CREATE SCHEMA forbidden_{schema};", "CREATE TEMP TABLE forbidden (id int);"]:
            result = sql(state, denied, role=service, check=False)
            if result.returncode == 0 or "permission denied" not in result.stderr:
                raise RuntimeError("Expected role isolation denial did not occur")
    docker("restart", state["container"])
    ready(state)
    for schema, role in [("runtime", "runtime_service"), ("artifacts", "artifact_service")]:
        assert sql(state, f"SELECT count(*) FROM {schema}.fixture_probe;", role=role).stdout.strip() == "1"
    version = sql(state, "SHOW server_version;").stdout.strip()
    port = docker("port", state["container"], "5432/tcp").stdout.strip()
    state["endpoint"] = port
    state["server_version"] = version
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Role isolation and restart persistence passed; PostgreSQL {version}; {port}.")


def stop():
    state = owned_state()
    docker("stop", state["container"])
    print("Fixture stopped; labeled volume and connection state retained.")


def resume():
    state = owned_state()
    docker("start", state["container"])
    verify()


def reset():
    """Explicitly reset only the two schemas in the labeled disposable fixture."""
    state = owned_state()
    if state["database"] != DATABASE:
        raise RuntimeError("Refusing reset outside the named test database")
    ready(state)
    sql(state, "DROP SCHEMA runtime CASCADE; DROP SCHEMA artifacts CASCADE; "
        "CREATE SCHEMA runtime AUTHORIZATION runtime_migrator; "
        "CREATE SCHEMA artifacts AUTHORIZATION artifact_migrator; "
        "GRANT USAGE ON SCHEMA runtime TO runtime_service; "
        "GRANT USAGE ON SCHEMA artifacts TO artifact_service;")
    verify()
    print("Disposable fixture schemas reset; migrations must run again.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "verify", "stop", "resume", "reset"])
    args = parser.parse_args()
    {"start": start, "verify": verify, "stop": stop, "resume": resume, "reset": reset}[args.action]()
