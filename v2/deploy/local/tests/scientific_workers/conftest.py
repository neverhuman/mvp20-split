import json

import pytest
from amphora_deployment.scientific_workers.profiles import ToolProfile


@pytest.fixture
def profile(tmp_path):
    config, cert = tmp_path / 'worker.json', tmp_path / 'certificate.pem'
    cert.write_bytes(b'certificate fixture')
    config.write_text(json.dumps({'actor_id': 'actor', 'scope': {'tenant_id': 't', 'project_id': 'p'},
        'run_id': 'run', 'image_sha256': 'a' * 64,
        'runtime': {'endpoint': 'https://host.docker.internal:23457', 'token_env': 'AMPHORA_RUNTIME_TOKEN'},
        'artifacts': {'endpoint': 'https://host.docker.internal:23458', 'token_env': 'AMPHORA_ARTIFACT_TOKEN'}}))
    return ToolProfile.pin('evolution-seed', 'sha256:' + 'a' * 64, config, cert, 23457, 23458)
