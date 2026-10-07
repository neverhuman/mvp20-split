"""Separate create-once heartbeat credential; never rotate the original deployment vault."""

import secrets
from pathlib import Path

from ..credentials import CredentialVault, SecretBundle
from ..persistence.state import LocalState
from ..profile import require

REFERENCE = 'WORKER_REGISTRY_TOKEN'


def worker_vault(root, deployment_id):
    return CredentialVault(Path(root) / 'tool-catalog.dpapi', deployment_id + '-tool-catalog')


def worker_credential(root, deployment_id):
    bundle = worker_vault(root, deployment_id).load()
    require(bundle.names == (REFERENCE,), 'tool_catalog_credential_scope')
    return bundle


def provision_worker_credential(root):
    with LocalState(root) as state:
        require(state.record.get('phase') == 'stores_ready', 'tool_catalog_stores_required')
        CredentialVault(state.root / 'credentials.dpapi', state.identity).load()
        vault = worker_vault(state.root, state.identity)
        if not vault.path.exists():
            vault.create(SecretBundle({REFERENCE: secrets.token_urlsafe(36)}))
        worker_credential(state.root, state.identity)
        return {'status': 'ready', 'reference': REFERENCE, 'original_vault_changed': False}
