"""Bounded local gateway configuration; no owner package imports."""

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from .errors import GatewayError, require
from .listener import Listener


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "gateway_duplicate_field")
        result[key] = value
    return result


def secret(environment, name):
    require(type(name) is str and re.fullmatch(r"AMPHORA_[A-Z0-9_]+", name), "gateway_credential_reference")
    value = environment.get(name)
    require(type(value) is str and 32 <= len(value) <= 512 and all(33 <= ord(c) <= 126 for c in value), "gateway_credential_missing")
    return value


@dataclass(frozen=True)
class Peer:
    port: int
    token: str = field(repr=False)

    @classmethod
    def load(cls, value, environment):
        require(type(value) is dict and set(value) == {"endpoint", "token_env"}, "gateway_peer_shape")
        url = urlsplit(value["endpoint"])
        require(url.scheme == "http" and url.hostname == "127.0.0.1" and url.username is None and
                url.password is None and url.path in ("", "/") and not url.query and not url.fragment and
                url.port is not None and 1 <= url.port <= 65535, "gateway_peer_scope")
        return cls(url.port, secret(environment, value["token_env"]))


@dataclass(frozen=True)
class Configuration:
    public_directory: Path
    peers: dict[str, Peer]
    context: dict
    launcher_key: str = field(repr=False)
    listener: Listener = field(default_factory=Listener)

    @classmethod
    def load(cls, path, environment):
        with Path(path).open("rb") as stream:
            raw = stream.read(65537)
        require(len(raw) <= 65536, "gateway_configuration_size")
        value = json.loads(raw, object_pairs_hook=unique)
        require(type(value) is dict,'gateway_configuration_shape')
        lan=value.get('profile')=='lan-gateway-v1'
        require(set(value)=={'profile','public_directory','peers','context','launcher_key_env'}|({'listener'} if lan else set())
                and value['profile'] in ('local-gateway-v1','lan-gateway-v1'),'gateway_configuration_shape')
        require(type(value["peers"]) is dict and bool(value["peers"]) and
                set(value["peers"]) <= {"runtime", "artifact", "registry", "research", "knowledge", "planning"}, "gateway_peer_names")
        context = value["context"]
        require(type(context) is dict and set(context) == {"actor_id", "scope", "run_id", "synthetic"}, "gateway_context_shape")
        require(type(context["actor_id"]) is str and bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,128}",context["actor_id"])) and
                type(context["scope"]) is dict and set(context["scope"]) == {"tenant_id", "project_id"} and
                all(type(v) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}",v) for v in context["scope"].values()) and
                (context["run_id"] is None or type(context["run_id"]) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}",context["run_id"])) and
                type(context["synthetic"]) is bool, "gateway_context_values")
        directory = Path(value["public_directory"])
        require(directory.is_absolute() and directory.is_dir(), "gateway_public_directory")
        return cls(directory, {name:Peer.load(peer, environment) for name,peer in value["peers"].items()},
                   context, secret(environment, value["launcher_key_env"]),Listener.load(value['listener']) if lan else Listener())
