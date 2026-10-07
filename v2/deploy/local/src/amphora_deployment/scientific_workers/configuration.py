"""Explicit synthetic worker composition; no public execution or eligibility authority."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from ..credentials import CredentialVault
from ..profile import fields, require
from .engine import ContainerEngine
from .journal import ContainerJournal
from .ownership import journal_path, require_configured_pending
from .profiles import PROFILES, ToolProfile, content
from .turn import ContainerTurn


@dataclass(frozen=True)
class ScientificBinding:
    profile: ToolProfile
    journal: ContainerJournal
    environment: object = field(repr=False)

    @classmethod
    def pin(cls, root, deployment_id, profile, environment):
        profile.verify()
        require(type(environment) is dict and set(environment) == {'AMPHORA_RUNTIME_TOKEN', 'AMPHORA_ARTIFACT_TOKEN'},
                'container_binding_environment')
        journal = ContainerJournal(journal_path(root, profile), deployment_id, profile.name, profile.fingerprint)
        journal.read()  # Existing identities cannot be reinterpreted by a replacement.
        return cls(profile, journal, MappingProxyType(dict(environment)))

    def turn(self):
        return ContainerTurn(self.journal, ContainerEngine(), self.profile, self.environment)


def load_scientific(path, root, deployment_id, access):
    if path is None:
        require_configured_pending(root, deployment_id, [])
        return {}
    record = fields(json.loads(content(path, 65536)), 'profile workers', 'container_manifest')
    require(record['profile'] == 'local-scientific-workers-v1', 'container_manifest_profile')
    workers = record['workers']
    require(type(workers) is dict and bool(workers) and set(workers) <= set(PROFILES), 'container_manifest_workers')
    require(set(access) == {'runtime', 'artifact'}, 'container_tls_routes_required')
    bundle = CredentialVault(Path(root) / 'credentials.dpapi', deployment_id).load()
    grants = bundle.environment(['WORKER_RUNTIME_TOKEN', 'WORKER_ARTIFACT_TOKEN'])
    environment = {'AMPHORA_RUNTIME_TOKEN': grants['WORKER_RUNTIME_TOKEN'],
                   'AMPHORA_ARTIFACT_TOKEN': grants['WORKER_ARTIFACT_TOKEN']}
    bindings = {}
    for name, entry in workers.items():
        fields(entry, 'image_id configuration certificate', 'container_manifest_binding')
        profile = ToolProfile.pin(name, entry['image_id'], entry['configuration'], entry['certificate'],
                                  access['runtime'].port, access['artifact'].port)
        require(all(profile.certificate_sha256 == binding.identity.certificate_sha256 for binding in access.values()),
                'container_tls_identity_mismatch')
        bindings[name] = ScientificBinding.pin(root, deployment_id, profile, environment)
    require_configured_pending(root, deployment_id, [binding.profile for binding in bindings.values()])
    return bindings
