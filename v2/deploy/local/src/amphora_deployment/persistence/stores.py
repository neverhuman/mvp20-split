"""Create/resume separately owned loopback PostgreSQL/Qdrant; never delete data."""

import json
import secrets
import socket
import time
import urllib.error
import urllib.request

from ..credentials import CredentialVault, SecretBundle
from ..installation import OWNERS
from ..profile import ProfileError, require
from .docker import Docker
from .postgres import bootstrap
from .state import LABEL, LocalState


POSTGRES = "postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f"
QDRANT = "qdrant/qdrant@sha256:12364fe851b9f17356fc88189fc06d1b521262e04659ec7345975b00c9246a10"


def new_credentials():
    names = {"PG_ADMIN_PASSWORD", "QDRANT_API_KEY", "GATEWAY_SESSION_KEY", "CURSOR_KEY"}
    for recipe in OWNERS.values():
        names.update(("PG_" + recipe.migration_role.upper() + "_PASSWORD", "PG_" + recipe.service_role.upper() + "_PASSWORD",
                      recipe.name.upper() + "_OPERATOR_TOKEN"))
    names.update(source + "_" + target + "_TOKEN" for source, target in (
        ("WORKER", "RUNTIME"), ("WORKER", "ARTIFACT"), ("RUNTIME", "ARTIFACT"), ("ARTIFACT", "RUNTIME"),
        ("KNOWLEDGE", "DATA"), ("KNOWLEDGE", "RESEARCH"), ("PLANNING", "DATA"), ("PLANNING", "RUNTIME"),
        ("PLANNING", "REGISTRY"), ("RUNTIME", "PLANNING"), ("RESEARCH", "DATA")))
    return SecretBundle({name:secrets.token_urlsafe(36) for name in sorted(names)})


def owned(info, identity, *, container=False):
    require(type(info) is dict, "deployment_resource_unavailable")
    labels = info["Config"].get("Labels", {}) if container else info.get("Labels", {})
    require(labels.get(LABEL) == identity, "deployment_resource_owner_mismatch")


def ensure_store(docker, state, kind, image, container_port, mount_path, environment):
    allocations = state.record.setdefault("store_ports", {})
    if kind not in allocations:
        previous = state.record.get(kind, {}).get("port")
        if previous is None:
            with socket.socket() as reserve:
                reserve.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                reserve.bind(("127.0.0.1", 0))
                previous = reserve.getsockname()[1]
        require(type(previous) is int and 1024 <= previous <= 65535, "deployment_store_port")
        allocations[kind] = previous
        state.save()
    host_port = allocations[kind]
    require(type(host_port) is int and 1024 <= host_port <= 65535, "deployment_store_port")
    volume, container = state.name(kind + "-data"), state.name(kind)
    info = docker.inspect("volume", volume)
    if info is None:
        docker.run("volume", "create", "--label", LABEL + "=" + state.identity, volume)
        info = docker.inspect("volume", volume)
    owned(info, state.identity)
    info = docker.inspect("container", container)
    if info is None:
        args = ["create", "--name", container, "--label", LABEL + "=" + state.identity,
                "--publish", "127.0.0.1:" + str(host_port) + ":" + str(container_port), "--mount", "type=volume,source=" + volume + ",target=" + mount_path]
        for key in environment:
            args += ["--env", key]
        docker.run(*args, image, secrets=environment)
        info = docker.inspect("container", container)
    owned(info, state.identity, container=True)
    require(info["Config"]["Image"] == image, "deployment_image_mismatch")
    require(len(info["Mounts"]) == 1 and info["Mounts"][0].get("Name") == volume
            and info["Mounts"][0].get("Destination") == mount_path, "deployment_mount_mismatch")
    bindings = info["HostConfig"]["PortBindings"]
    require(set(bindings) == {str(container_port) + "/tcp"} and all(item["HostIp"] == "127.0.0.1" for item in bindings[str(container_port) + "/tcp"]), "deployment_network_scope")
    require(len(bindings[str(container_port) + "/tcp"]) == 1 and
            bindings[str(container_port) + "/tcp"][0].get("HostPort") == str(host_port), "deployment_fixed_port_repair_required")
    if not info["State"]["Running"]:
        docker.run("start", container)
    info = docker.inspect("container", container)
    actual = info["NetworkSettings"]["Ports"][str(container_port) + "/tcp"]
    require(len(actual) == 1 and actual[0]["HostIp"] == "127.0.0.1" and int(actual[0]["HostPort"]) == host_port, "deployment_published_scope")
    return {"container": container, "volume": volume, "image": image, "host": "127.0.0.1", "port": int(actual[0]["HostPort"])}


def qdrant_ready(endpoint, key):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(endpoint + "/collections", headers={"api-key": key})
    try:
        with opener.open(request, timeout=3) as response:
            value = json.loads(response.read(65537))
            return response.status == 200 and value.get("status") == "ok"
    except (OSError, ValueError):
        return False


def ensure_local_stores(root):
    docker = Docker()
    with LocalState(root) as state:
        vault = CredentialVault(state.root / "credentials.dpapi", state.identity)
        if not vault.path.exists():
            require(state.record["phase"] == "declared", "deployment_credentials_missing")
            require(all(docker.inspect("container", state.name(kind)) is None for kind in ("postgres", "qdrant")), "deployment_credentials_missing")
            require(all(docker.inspect("volume", state.name(kind + "-data")) is None for kind in ("postgres", "qdrant")), "deployment_credentials_missing")
            vault.create(new_credentials())
        bundle = vault.load()
        state.record["phase"] = "credentials_ready"
        state.save()
        pg = ensure_store(docker, state, "postgres", POSTGRES, 5432, "/var/lib/postgresql/data",
                          {"POSTGRES_PASSWORD": bundle.environment(["PG_ADMIN_PASSWORD"])["PG_ADMIN_PASSWORD"], "POSTGRES_DB": "amphora_local"})
        deadline = time.monotonic() + 45
        while docker.run("exec", pg["container"], "pg_isready", "-h", "127.0.0.1", "-U", "postgres", "-d", "amphora_local", allow_failure=True) is None:
            if time.monotonic() >= deadline:
                raise ProfileError("deployment_postgres_unavailable")
            time.sleep(0.25)
        bootstrap(docker, pg["container"], state.identity, bundle)
        state.record.update(postgres=pg, phase="postgres_bootstrapped")
        state.save()
        key = bundle.environment(["QDRANT_API_KEY"])["QDRANT_API_KEY"]
        qdrant = ensure_store(docker, state, "qdrant", QDRANT, 6333, "/qdrant/storage", {"QDRANT__SERVICE__API_KEY": key})
        deadline = time.monotonic() + 45
        while not qdrant_ready("http://127.0.0.1:" + str(qdrant["port"]), key):
            if time.monotonic() >= deadline:
                raise ProfileError("deployment_qdrant_unavailable")
            time.sleep(0.25)
        state.record.update(qdrant=qdrant, phase="stores_ready")
        state.save()
        return dict(state.record)
