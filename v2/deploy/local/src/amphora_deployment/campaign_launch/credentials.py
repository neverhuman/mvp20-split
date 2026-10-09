"""Dedicated launch-to-Gateway grant; original owner/operator vaults remain intact."""
import secrets
from pathlib import Path

from ..credentials import CredentialVault, SecretBundle
from ..persistence.state import LocalState
from ..profile import require

REFERENCE = 'LAUNCH_GATEWAY_TOKEN'


def launch_vault(root, deployment_id):
    return CredentialVault(Path(root) / 'campaign-launch-api.dpapi', deployment_id + '-campaign-launch-api')


def launch_credential(root, deployment_id):
    bundle = launch_vault(root, deployment_id).load()
    require(bundle.names == (REFERENCE,), 'launch_credential_scope')
    return bundle


def provision_launch_credential(root):
    with LocalState(root) as state:
        require(state.record.get('phase') == 'stores_ready', 'launch_stores_required')
        CredentialVault(state.root / 'credentials.dpapi', state.identity).load()
        vault = launch_vault(state.root, state.identity)
        if not vault.path.exists():
            vault.create(SecretBundle({REFERENCE: secrets.token_urlsafe(36)}))
        launch_credential(state.root, state.identity)
        return {'status': 'ready', 'reference': REFERENCE, 'original_vault_changed': False}
