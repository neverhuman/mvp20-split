from dataclasses import replace
from fastapi.testclient import TestClient
from amphora_agent_planning.supervision_api.app import create_app
from amphora_agent_planning.supervision_api.credentials import Credentials
from amphora_agent_planning.supervision_intake import SupervisionIntake
from amphora_agent_planning.curation_jobs.journal import CurationJobs
from ..curation_intake.support import environment


def test_refresh_reads_progress_without_resubmitting_original(stored):
    principal, raw, journal = environment(stored)
    receipt = journal.receive(principal, raw)
    readonly = replace(principal, actions=frozenset({'read_curations'}))
    worker = replace(principal, actions=frozenset({'execute_curations'}))
    jobs = CurationJobs(stored.engine)
    lease = jobs.claim(worker, receipt.reference.curation_id, 'worker')
    final = jobs.fail(worker, lease, 'source_denied')
    credentials = Credentials([('r' * 40, readonly)])
    with TestClient(create_app(SupervisionIntake(stored.engine), credentials, curations=journal)) as client:
        headers = {'Authorization': 'Bearer ' + 'r' * 40}
        url = '/v1/campaign-curations/' + receipt.reference.curation_id
        first = client.get(url, headers=headers)
        second = client.get(url, headers=headers)
        assert first.status_code == 200 and first.content == second.content
        assert first.json() == final.model_dump(mode='json')
        query = {'identity': receipt.identity.model_dump(mode='json'), 'request_sha256': receipt.request_sha256}
        original = client.post('/v1/campaign-curations/receipts/query', json=query, headers=headers)
        assert original.status_code == 200 and original.json() == receipt.model_dump(mode='json')
        assert client.post('/v1/campaign-curations', content=raw, headers=headers).status_code == 403
