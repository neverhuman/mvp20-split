"""Explicit catalog sidecar binds existing scientific slots; never registers tools."""

import hashlib
import json
from pathlib import Path

from ..profile import fields, label, require
from ..scientific_workers.profiles import content
from .availability import CapacityProbe, ExecutorBudget
from .credentials import worker_credential
from .dependencies import ToolDependencies
from .group import CatalogGroup
from .heartbeat import HeartbeatJournal, ReplicaBinding
from .reporter import CapacityReporter
from .target import CatalogTarget
from .transport import HeartbeatTransport


class Dependencies:
    def __init__(self, catalog, tools):
        self.catalog, self.tools = catalog, tools

    def __call__(self):
        return self.catalog() and self.tools()


def load_catalog(path, root, deployment_id, routes, supervisor):
    if path is None:
        return CatalogGroup()
    record = fields(json.loads(content(path, 65536)), 'profile scope worker_id replicas', 'catalog_manifest')
    require(record['profile'] == 'local-tool-catalog-v1', 'catalog_manifest_profile')
    scope = fields(record['scope'], 'tenant_id project_id', 'catalog_scope')
    label(record['worker_id'], 'catalog_worker')
    replicas = record['replicas']
    slots = supervisor.scientific.slots
    require(type(replicas) is dict and bool(replicas) and set(replicas) == set(slots), 'catalog_manifest_slots')
    require('registry' in supervisor.bindings and set(supervisor.access.bindings) == {'runtime', 'artifact'},
            'catalog_required_owners')
    registry = supervisor.bindings['registry']
    require(registry.port == routes.port('registry'), 'catalog_registry_route')
    token = worker_credential(root, deployment_id).environment(['WORKER_REGISTRY_TOKEN'])['WORKER_REGISTRY_TOKEN']
    budget, reporters, identities = ExecutorBudget(len(slots)), {}, set()
    for name, row in replicas.items():
        fields(row, 'deployment_id replica_id binding_sha256', 'catalog_replica')
        slot = slots[name]
        profile = slot.binding.profile
        require(row['binding_sha256'] == profile.fingerprint, 'catalog_binding_changed')
        replica = ReplicaBinding(deployment_id, scope['tenant_id'], scope['project_id'], record['worker_id'],
                                 row['deployment_id'], row['replica_id'])
        require((replica.deployment_id, replica.replica_id) not in identities, 'catalog_duplicate_replica')
        identities.add((replica.deployment_id, replica.replica_id))
        config = json.loads(content(profile.configuration, 65536))
        require(config['scope'] == scope and config['actor_id'] == replica.worker_id, 'catalog_worker_scope')
        catalog = CatalogTarget(replica, profile, registry.port, registry.environment['AMPHORA_REGISTRY_OPERATOR_TOKEN'])
        access = supervisor.access.bindings
        tools = ToolDependencies(profile.certificate, access['runtime'].port, access['artifact'].port,
                                 access['runtime'].route.upstream_port, access['artifact'].route.upstream_port)
        probe = CapacityProbe(slot, budget, Dependencies(catalog, tools))
        identity = json.dumps([deployment_id, scope, replica.worker_id, replica.deployment_id, replica.replica_id],
                              sort_keys=True, separators=(',', ':')).encode()
        path = Path(root) / 'tool-catalog' / (hashlib.sha256(identity).hexdigest() + '.json')
        journal = HeartbeatJournal(path, replica)
        journal.read()
        reporters[name] = CapacityReporter(probe, journal, HeartbeatTransport(registry.port, token))
    return CatalogGroup(reporters)
