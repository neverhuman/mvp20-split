"""Closed operator manifest and startup composition under the existing writer lease."""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ..profile import fields, label, require
from ..scientific_workers.configuration import load_scientific_templates
from ..scientific_workers.ownership import require_configured_pending
from ..scientific_workers.profiles import content
from ..tool_catalog.configuration import load_catalog
from ..tool_catalog.target import CAPABILITIES
from .intent import LaunchError
from .journal import LaunchJournal
from .preflight import InstalledExecutor
from .profile import LaunchProfilePolicy
from .run_bindings import RunBindingStore, canonical_record, retain_exact


@dataclass(frozen=True, slots=True)
class LaunchManifest:
    actor_id: str
    policy_path: Path
    scientific_path: Path
    catalog_path: Path

    @classmethod
    def load(cls, path):
        record = fields(json.loads(content(path, 65536)),
            'profile actor_id launch_profile scientific_manifest catalog_manifest', 'launch_manifest')
        require(record['profile'] == 'local-campaign-launch-v1', 'launch_manifest_profile')
        actor = label(record['actor_id'], 'launch_actor')
        paths = [Path(record[key]) for key in ('launch_profile', 'scientific_manifest', 'catalog_manifest')]
        require(all(path.is_absolute() for path in paths), 'launch_manifest_paths')
        return cls(actor, *paths)


class LaunchInstallation:
    def __init__(self, root, deployment_id, manifest, access):
        self.root, self.deployment_id, self.manifest = Path(root), deployment_id, manifest
        self.policy = LaunchProfilePolicy.from_bytes(content(manifest.policy_path, 65536))
        self.templates = load_scientific_templates(manifest.scientific_path, root, deployment_id, access)
        require(1 <= len(self.templates) <= 5, 'launch_installed_tool_count')
        self.catalog_record = fields(json.loads(content(manifest.catalog_path, 65536)),
            'profile scope worker_id replicas', 'launch_catalog')
        require(self.catalog_record['profile'] == 'local-tool-catalog-v1'
            and self.catalog_record['scope'] == self.policy.view.scope.model_dump(mode='json')
            and set(self.catalog_record['replicas']) == set(self.templates), 'launch_catalog_scope')
        self.executors = []
        for name, binding in self.templates.items():
            config = json.loads(content(binding.profile.configuration, 65536))
            row = fields(self.catalog_record['replicas'][name], 'deployment_id replica_id binding_sha256', 'launch_replica')
            require(row['binding_sha256'] == binding.profile.fingerprint
                and config['scope'] == self.catalog_record['scope']
                and config['actor_id'] == self.catalog_record['worker_id'], 'launch_template_binding')
            label(row['deployment_id'], 'launch_deployment'); label(row['replica_id'], 'launch_replica')
            matches = [tool for tool in self.policy.view.tools if tool.capability_id == CAPABILITIES[name]
                       and tool.image_sha256 == binding.profile.image_id[7:]]
            require(len(matches) == 1, 'launch_template_tool_mismatch')
            self.executors.append(InstalledExecutor(matches[0], row['deployment_id'], config['actor_id']))
        require(len(self.executors) == len(self.policy.view.tools), 'launch_profile_tool_coverage')
        self.store = RunBindingStore(root, deployment_id, self.templates,
            runtime_port=access['runtime'].port, artifact_port=access['artifact'].port)
        self.journal = LaunchJournal(self.root / 'campaign-launches')
        self._pins = canonical_record({'actor_id': manifest.actor_id,
            'profile': self.policy.view.reference.model_dump(mode='json'),
            'templates': {name: binding.profile.fingerprint for name, binding in self.templates.items()},
            'catalog_sha256': hashlib.sha256(canonical_record(self.catalog_record)).hexdigest()})
        self._files = tuple((path, hashlib.sha256(content(path, 65536)).hexdigest()) for path in
                            (manifest.policy_path, manifest.scientific_path, manifest.catalog_path))

    def verify(self):
        for path, digest in self._files:
            if hashlib.sha256(content(path, 65536)).hexdigest() != digest:
                raise LaunchError('launch_installation_configuration_changed')
        for binding in self.templates.values():
            binding.profile.verify()

    def pin_intent(self, intent, *, required=False):
        self.verify()
        if intent.request.identity.actor_id != self.manifest.actor_id:
            raise LaunchError('launch_scope_denied')
        self.policy.check(intent)
        path = self.root / 'campaign-launches' / intent.request.sha256 / 'installation.json'
        if required and not path.exists():
            raise LaunchError('launch_installation_pin_missing')
        retain_exact(path, self._pins)

    def startup_bindings(self):
        state = self.journal.active()
        if state is not None:
            self.pin_intent(state.intent, required=state.phase != 'preparing')
        bindings = self.store.prepare(state) if state is not None and state.run_id else self.templates
        require_configured_pending(self.root, self.deployment_id, [b.profile for b in bindings.values()])
        return bindings

    def catalog(self, supervisor, bindings, routes):
        self.verify()
        fingerprints = {name: binding.profile.fingerprint for name, binding in bindings.items()}
        original = {name: binding.profile.fingerprint for name, binding in self.templates.items()}
        if fingerprints == original:
            path = self.manifest.catalog_path
        else:
            value = json.loads(canonical_record(self.catalog_record))
            for name, fingerprint in fingerprints.items():
                value['replicas'][name]['binding_sha256'] = fingerprint
            parents = {binding.profile.configuration.parent for binding in bindings.values()}
            require(len(parents) == 1, 'launch_binding_directory_mismatch')
            path = next(iter(parents)) / 'catalog.json'
            retain_exact(path, canonical_record(value))
        return load_catalog(path, self.root, self.deployment_id, routes, supervisor)
