"""TLS sidecar selects only local identity and fixed owner routes, never upstream URLs."""

import json
from pathlib import Path

from ..profile import fields, require
from .identity import TLSIdentity
from .managed import AccessBinding
from .proxy import OwnerRoute


def load_access(path, deployment_id, routes, owners):
    with Path(path).open('rb') as stream:
        raw = stream.read(8193)
    require(len(raw) <= 8192, 'tool_tls_configuration_size')
    record = fields(json.loads(raw), 'profile identity_directory ports', 'tool_tls_configuration')
    require(record['profile'] == 'local-tool-access-v1', 'tool_tls_configuration_profile')
    directory = record['identity_directory']
    require(type(directory) is str and Path(directory).is_absolute(), 'tool_tls_identity_path')
    identity = TLSIdentity.load(directory)
    require(identity.deployment_id == deployment_id, 'tool_tls_deployment_mismatch')
    ports = record['ports']
    require(type(ports) is dict and bool(ports) and set(ports) <= {'runtime', 'artifact'} and
            set(ports) <= set(owners), 'tool_tls_configuration_owners')
    require(all(type(port) is int and 1024 <= port <= 65535 for port in ports.values()) and
            len(set(ports.values())) == len(ports) and not set(ports.values()).intersection(dict(routes.ports).values()),
            'tool_tls_configuration_ports')
    return {name: AccessBinding(identity, OwnerRoute(name, routes.port(name)), port) for name, port in ports.items()}
