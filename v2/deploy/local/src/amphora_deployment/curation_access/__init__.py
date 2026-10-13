"""Optional create-once Planning reader identities; no peer permissions implied."""
import secrets
from pathlib import Path

from ..credentials import CredentialVault, SecretBundle
from ..persistence.state import LocalState
from ..profile import require

REFERENCES = {
    'PLANNING_KNOWLEDGE_TOKEN': frozenset({'planning', 'knowledge'}),
    'PLANNING_RESEARCH_TOKEN': frozenset({'planning', 'research'}),
}


def curation_vault(root, deployment_id):
    return CredentialVault(Path(root) / 'planning-readers.dpapi', deployment_id + '-planning-readers')


def curation_credentials(root, deployment_id):
    bundle = curation_vault(root, deployment_id).load()
    require(set(bundle.names) == set(REFERENCES), 'curation_reader_credential_scope')
    return bundle


def provision_curation_credentials(root):
    with LocalState(root) as state:
        require(state.record.get('phase') == 'stores_ready', 'curation_reader_stores_required')
        CredentialVault(state.root / 'credentials.dpapi', state.identity).load()
        vault = curation_vault(state.root, state.identity)
        if not vault.path.exists():
            vault.create(SecretBundle({name: secrets.token_urlsafe(36) for name in REFERENCES}))
        curation_credentials(state.root, state.identity)
        return {'status': 'ready', 'references': sorted(REFERENCES), 'original_vault_changed': False}
