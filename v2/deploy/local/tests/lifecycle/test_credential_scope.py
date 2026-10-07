import pytest

from amphora_deployment.lifecycle.configuration import allowed_reference


@pytest.mark.parametrize('owner,reference', [
    ('runtime','PG_RUNTIME_MIGRATOR_PASSWORD'), ('runtime','PG_ADMIN_PASSWORD'),
    ('artifact','GATEWAY_SESSION_KEY'), ('knowledge','PLANNING_OPERATOR_TOKEN'),
    ('planning','CURSOR_KEY'), ('registry','QDRANT_API_KEY'), ('runtime','SUPERVISOR_CONTROL_TOKEN'),
])
def test_owner_cannot_receive_other_authority_credentials(owner, reference):
    assert not allowed_reference(owner, reference)


@pytest.mark.parametrize('owner,reference', [
    ('runtime','RUNTIME_OPERATOR_TOKEN'), ('runtime','WORKER_RUNTIME_TOKEN'),
    ('artifact','KNOWLEDGE_DATA_TOKEN'), ('artifact','ARTIFACT_RUNTIME_TOKEN'),
    ('knowledge','KNOWLEDGE_DATA_TOKEN'), ('artifact','QDRANT_API_KEY'), ('runtime','CURSOR_KEY'),
])
def test_explicit_owner_peer_grants(owner, reference):
    assert allowed_reference(owner, reference)
