from dataclasses import replace
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from amphora_contracts_campaign_curation import CurationReceiptQuery
from amphora_agent_planning.capability_requests.reader import CapabilityRequestReader
from amphora_agent_planning.curation_intake.journal import CurationJournal
from amphora_agent_planning.curation_result.journal import CurationResultJournal
from amphora_agent_planning.curation_output import CurationOutput
from amphora_agent_planning.supervision_api.app import create_app
from amphora_agent_planning.supervision_api.credentials import Credentials
from amphora_agent_planning.supervision_intake import SupervisionIntake
from ..curation_execution.test_executor import setup
from ..curation_output.test_output import output

pytestmark = pytest.mark.postgres


def recorded(stored):
    principal, lease, linked, executor, provider, data = setup(stored)
    raw = json.loads(provider.raw)
    raw['outcome'] = output()['outcome']
    provider.raw = json.dumps(raw).encode()
    executor.execute(principal, lease)
    progress = CurationResultJournal(stored.engine).record(principal, lease)
    intake = CurationJournal(stored.engine, ())  # Retired policy remains readable.
    original = intake.receipt(principal, CurationReceiptQuery(identity=progress.view.receipt.identity,
        request_sha256=progress.view.receipt.request_sha256))
    return principal, lease, intake, original, progress, provider


def counts(stored, principal):
    with stored.engine.connect() as conn:
        return tuple(conn.execute(text('SELECT count(*) FROM planning.' + table + ' WHERE project_id=:project'),
            {'project': principal.scope.project_id}).scalar_one()
            for table in ('curation_requests', 'curation_progress', 'attempts'))


def test_original_capture_projects_stable_requests_after_reader_replacement_without_writes(stored):
    principal, lease, intake, original, progress, provider = recorded(stored)
    visible = intake.read(principal, lease.curation_id)
    assert progress.view.capability_requests == () and len(visible.capability_requests) == 1
    request_id = visible.capability_requests[0].request_id
    reader = CapabilityRequestReader(stored.engine)
    scoped = replace(principal, actions=frozenset({'read_capabilities'}))
    before = counts(stored, principal)
    first = reader.read(scoped, request_id)
    outcome = CurationResultJournal(stored.engine).read(principal, lease.curation_id)
    assert first.proposal_sha256 == CurationOutput.parse(provider.raw, outcome.attempt.binding.request).sha256
    assert first == CapabilityRequestReader(stored.engine).read(scoped, request_id)
    assert first.gap == progress.view.proposal.outcome.gaps[0] and first.status == 'requested'
    assert intake.receipt(principal, CurationReceiptQuery(identity=original.identity, request_sha256=original.request_sha256)) == original
    assert CurationResultJournal(stored.engine).record(principal, lease) == progress
    assert counts(stored, principal) == before and provider.calls == 1


def test_public_capability_reads_require_their_own_grant_and_hide_other_owners(stored):
    principal, lease, intake, _, _, provider = recorded(stored)
    reference = intake.read(principal, lease.curation_id).capability_requests[0]
    reader = replace(principal, actions=frozenset({'read_capabilities'}))
    foreign = replace(reader, scope=reader.scope.model_copy(update={'project_id': 'foreign'}))
    other = replace(reader, actor_id='other')
    credentials = Credentials([('r' * 40, reader), ('f' * 40, foreign), ('o' * 40, other),
        ('n' * 40, replace(reader, actions=frozenset({'read_curations'})))])
    with TestClient(create_app(SupervisionIntake(stored.engine), credentials, curations=intake)) as client:
        path = '/v1/capability-requests/' + reference.request_id
        headers = {'Authorization': 'Bearer ' + 'r' * 40}
        assert client.get(path).status_code == 401
        first = client.get(path, headers=headers)
        assert first.status_code == 200 and first.json()['status'] == 'requested'
        assert first.content == client.get(path, headers=headers).content
        assert first.headers['cache-control'] == 'no-store'
        assert client.get('/v1/capability-requests/missing', headers=headers).status_code == 404
        assert client.get(path + '?latest=true', headers=headers).status_code == 422
        assert client.request('GET', path, content='{}', headers=headers).status_code == 422
        for token, status in [('f', 404), ('o', 404), ('n', 403)]:
            assert client.get(path, headers={'Authorization': 'Bearer ' + token * 40}).status_code == status
        assert client.get('/v1/campaign-curations/' + lease.curation_id, headers=headers).status_code == 403
    assert provider.calls == 1
