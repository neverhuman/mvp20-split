"""Nonsecret local bindings resolve only owner-scoped serving credentials."""

import json
from pathlib import Path
import secrets
from urllib.parse import quote

from ..credentials import CredentialVault, SecretBundle
from ..installation import OWNERS, SERVING_HOSTS, OwnerInstallation
from ..persistence.state import LocalState
from ..profile import require
from .supervisor import OwnerBinding
from .planning_configuration import planning_environment
from ..curation_access import REFERENCES as CURATION_READERS, curation_credentials


def allowed_reference(owner, name):
    if name in CURATION_READERS:
        return owner in CURATION_READERS[name]
    if owner == "gateway":
        return name in {"GATEWAY_SESSION_KEY", "LAUNCH_GATEWAY_TOKEN"} or name in {key.upper() + "_OPERATOR_TOKEN" for key in OWNERS}
    if name == owner.upper() + "_OPERATOR_TOKEN":
        return True
    if name == "CURSOR_KEY":
        return owner == "runtime"
    if name == "QDRANT_API_KEY":
        return owner == "artifact"
    aliases = {owner.upper()} | ({"DATA"} if owner == "artifact" else set())
    return name.endswith("_TOKEN") and any(name.startswith(alias + "_") or name.endswith("_" + alias + "_TOKEN") for alias in aliases)


def control_vault(root, identity):
    return CredentialVault(Path(root) / "supervisor.dpapi", identity + "-supervisor")


def control_token(root, *, create=False):
    if not create:
        state = LocalState.snapshot(root)
        require(state.get("phase") == "stores_ready", "lifecycle_stores_required")
        identity = state["deployment_id"]
        CredentialVault(Path(root) / "credentials.dpapi", identity).load()
        return control_vault(root, identity).load().environment(["SUPERVISOR_CONTROL_TOKEN"])["SUPERVISOR_CONTROL_TOKEN"]
    with LocalState(root) as state:
        require(state.record.get("phase") == "stores_ready", "lifecycle_stores_required")
        # Authenticate the original deployment identity before creating any sidecar secret.
        CredentialVault(state.root / "credentials.dpapi", state.identity).load()
        vault = control_vault(state.root, state.identity)
        if create and not vault.path.exists():
            vault.create(SecretBundle({"SUPERVISOR_CONTROL_TOKEN": secrets.token_urlsafe(36)}))
        return vault.load().environment(["SUPERVISOR_CONTROL_TOKEN"])["SUPERVISOR_CONTROL_TOKEN"]


def load_bindings(root, manifest, routes):
    with Path(manifest).open("rb") as stream:
        raw = stream.read(65537)
    require(len(raw) <= 65536, "lifecycle_manifest_size")
    config = json.loads(raw)
    require(type(config) is dict and set(config) == {"profile", "owners"} and
            config["profile"] == "local-supervisor-v1", "lifecycle_manifest_shape")
    owners = config["owners"]
    require(type(owners) is dict and bool(owners) and set(owners) <= set(SERVING_HOSTS), "lifecycle_manifest_owners")
    state = LocalState.snapshot(root)
    require(state.get("phase") == "stores_ready", "lifecycle_stores_required")
    bundle = CredentialVault(Path(root) / "credentials.dpapi", state["deployment_id"]).load()
    pg = dict(state["postgres"])
    require(pg["host"] == "127.0.0.1" and type(pg["port"]) is int and 1 <= pg["port"] <= 65535, "lifecycle_database_scope")
    result = {}
    for owner, record in owners.items():
        require(type(record) is dict and set(record) == {"installation", "source_lock", "configuration", "secret_references"}, "lifecycle_binding_shape")
        require(all(type(record[key]) is str and Path(record[key]).is_absolute() for key in
                    ("installation", "source_lock", "configuration")), "lifecycle_binding_path")
        references = record["secret_references"]
        require(type(references) is list and len(references) <= 64 and all(type(name) is str and allowed_reference(owner, name) for name in references), "lifecycle_credential_scope")
        selected = [name for name in references if name not in {'WORKER_REGISTRY_TOKEN', 'RUNTIME_REGISTRY_TOKEN', 'LAUNCH_GATEWAY_TOKEN'} and name not in CURATION_READERS]
        values = bundle.environment(selected)
        readers = [name for name in references if name in CURATION_READERS]
        if readers:
            values.update(curation_credentials(root, state['deployment_id']).environment(readers))
        if 'LAUNCH_GATEWAY_TOKEN' in references:
            from ..campaign_launch.credentials import launch_credential
            require(owner == 'gateway', 'lifecycle_credential_scope')
            values.update(launch_credential(root, state['deployment_id']).environment(['LAUNCH_GATEWAY_TOKEN']))
        if 'RUNTIME_REGISTRY_TOKEN' in references:
            from ..registry_access import registry_credential
            require(owner in {'runtime', 'registry'}, 'lifecycle_credential_scope')
            values.update(registry_credential(root, state['deployment_id']).environment(['RUNTIME_REGISTRY_TOKEN']))
        if 'WORKER_REGISTRY_TOKEN' in references:
            from ..tool_catalog.credentials import worker_credential
            require(owner == 'registry', 'lifecycle_credential_scope')
            values.update(worker_credential(root, state['deployment_id']).environment(['WORKER_REGISTRY_TOKEN']))
        environment = {"AMPHORA_" + name:value for name,value in values.items()}
        recipe = SERVING_HOSTS[owner]
        if recipe.schema is not None:
            password = bundle.environment(["PG_" + recipe.service_role.upper() + "_PASSWORD"])["PG_" + recipe.service_role.upper() + "_PASSWORD"]
            environment[recipe.database_environment] = "postgresql+psycopg://" + recipe.service_role + ":" + quote(password, safe="") + "@127.0.0.1:" + str(pg["port"]) + "/amphora_local?connect_timeout=5"
        configuration = Path(record["configuration"])
        require(configuration.is_file(), "lifecycle_owner_configuration_missing")
        if owner == "planning":
            require(configuration.stat().st_size <= 65536, "lifecycle_planning_config_size")
            settings = json.loads(configuration.read_bytes())
            environment.update(planning_environment(settings, environment))
        installation = OwnerInstallation.from_directory(owner, record["installation"], record["source_lock"])
        result[owner] = OwnerBinding(installation, Path(record["installation"]), configuration, routes.port(owner), environment)
    return result
