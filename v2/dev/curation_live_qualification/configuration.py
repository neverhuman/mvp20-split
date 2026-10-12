"""Dev orchestration inputs; secrets travel only to the owning child environment."""
import json
from pathlib import Path
from urllib.parse import quote

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.persistence.state import LocalState
from campaign_curation_fixture.verify import filtered_environment
from local_numeric_configuration import write


def worker_environment(root, api):
    state = LocalState.snapshot(root)
    vault = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load()
    password = vault.environment(['PG_PLANNING_SERVICE_PASSWORD'])['PG_PLANNING_SERVICE_PASSWORD']
    result = filtered_environment()
    result['CURATION_PLANNING_DATABASE'] = ('postgresql+psycopg://planning_service:' + quote(password, safe='') +
        '@127.0.0.1:' + str(state['postgres']['port']) + '/amphora_local?connect_timeout=5')
    for name in ('data', 'runtime', 'registry', 'knowledge', 'research'):
        result['CURATION_' + name.upper() + '_TOKEN'] = api.tokens['artifact' if name == 'data' else name]
    return result


def planning_python(serving):
    owners = json.loads((serving / 'owners.json').read_bytes())['owners']
    return Path(owners['planning']['installation']) / 'environment/Scripts/python.exe'


def freeze(path, value):
    if path.exists():
        assert json.loads(path.read_bytes()) == value, 'Qualification declaration changed'
        return path
    return write(path, value)
