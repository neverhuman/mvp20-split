"""Explicit serial owner CLI migrations against only the dedicated local database."""

from datetime import datetime
import os
from pathlib import Path
import socket
import subprocess
from urllib.parse import quote

from ..credentials import CredentialVault
from ..installation import OWNERS, OwnerInstallation
from ..profile import require
from ..scientific_workers.ownership import require_released
from .state import LocalState


def require_stopped(routes):
    require(type(routes) is dict and routes.get("host") == "127.0.0.1", "migration_routes_required")
    ports = routes.get("ports")
    require(type(ports) is dict and set(ports) == set(OWNERS) | {"gateway", "supervisor"}, "migration_routes_required")
    for port in ports.values():
        require(type(port) is int and 1024 <= port <= 65535, "migration_port")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(.25)
            require(probe.connect_ex(("127.0.0.1", port)) != 0, "migration_requires_stopped_services")


def migrate_owner(root, owner, directory, source_lock):
    require(owner in OWNERS, "migration_owner")
    installation = OwnerInstallation.from_directory(owner, directory, source_lock)
    recipe = OWNERS[owner]
    with LocalState(root) as state:
        require(state.record.get("phase") == "stores_ready", "migration_stores_required")
        require_stopped(state.record.get("routes"))
        require_released(state.root, state.identity)
        receipts = state.record.setdefault("migrations", {})
        prior = receipts.get(owner)
        if prior is not None:
            require(prior.get("installation_manifest_sha256") == installation.installation_manifest_sha256,
                    "migration_release_change_requires_forward_plan")
        pg = state.record["postgres"]
        require(pg["host"] == "127.0.0.1" and type(pg["port"]) is int and 1 <= pg["port"] <= 65535, "migration_database_scope")
        bundle = CredentialVault(state.root / "credentials.dpapi", state.identity).load()
        name = "PG_" + recipe.migration_role.upper() + "_PASSWORD"
        password = bundle.environment([name])[name]
        url = "postgresql+psycopg://" + recipe.migration_role + ":" + quote(password, safe="") + "@127.0.0.1:" + str(pg["port"]) + "/amphora_local?connect_timeout=5"
        environment = {key:value for key,value in os.environ.items() if key.upper() in {
            "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "USERPROFILE", "LOCALAPPDATA", "APPDATA"}}
        environment[recipe.migration_environment] = url
        receipt = {"owner":owner, "release":installation.release,
                   "installation_manifest_sha256":installation.installation_manifest_sha256,
                   "status":"running", "started_at":datetime.now().astimezone().isoformat(timespec="seconds")}
        receipts[owner] = receipt
        state.save()
        try:
            result = subprocess.run(recipe.migration_command(Path(directory) / "environment/Scripts/python.exe"),
                env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
            receipt.update(status="succeeded" if result.returncode == 0 else "failed", exit_code=result.returncode)
        except (OSError, subprocess.TimeoutExpired):
            receipt.update(status="failed", reason="migration_process_unavailable")
        receipt["finished_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        state.save()
        require(receipt["status"] == "succeeded", "migration_owner_failed_forward_repair_required")
        return dict(receipt)
