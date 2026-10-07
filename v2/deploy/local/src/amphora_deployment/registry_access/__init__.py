"""Create-once Runtime-to-Registry identity, separate from operator credentials."""

import secrets
from pathlib import Path

from ..credentials import CredentialVault, SecretBundle
from ..persistence.state import LocalState
from ..profile import require

REFERENCE = 'RUNTIME_REGISTRY_TOKEN'


def registry_vault(root, deployment_id):
    return CredentialVault(Path(root) / 'runtime-registry.dpapi', deployment_id + '-runtime-registry')


def registry_credential(root, deployment_id):
    bundle = registry_vault(root, deployment_id).load()
    require(bundle.names == (REFERENCE,), 'runtime_registry_credential_scope')
    return bundle


def provision_registry_credential(root):
    with LocalState(root) as state:
        require(state.record.get('phase') == 'stores_ready', 'runtime_registry_stores_required')
        CredentialVault(state.root / 'credentials.dpapi', state.identity).load()
        vault = registry_vault(state.root, state.identity)
        if not vault.path.exists():
            vault.create(SecretBundle({REFERENCE: secrets.token_urlsafe(36)}))
        registry_credential(state.root, state.identity)
        return {'status': 'ready', 'reference': REFERENCE, 'original_vault_changed': False}
