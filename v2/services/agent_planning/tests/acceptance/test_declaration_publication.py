"""Actual installed Data publishes fixed declaration bytes before request binding."""

import hashlib
import json
import os
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener

import pytest
from amphora_agent_planning.campaign_artifact_context import (
    ArtifactContextItem,
    ArtifactContextPlan,
    ArtifactContextProjection,
)
from amphora_agent_planning.campaign_data_access import (
    ArtifactSelection,
    CampaignArtifactReader,
)
from amphora_agent_planning.campaign_decisions import (
    CampaignDecisionReview,
    DecisionDeclaration,
)
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.source_access import DataReader
from amphora_contracts_core import Scope

from ..campaign_decisions.test_policy import fixture
from ..campaign_output.test_output import output
from ..campaign_proposals.test_evidence import prepared
from ..campaign_proposals.test_prepared import source
from ..persistence.test_reservations import policy


@pytest.mark.skipif('DECLARATION_CASE' not in os.environ, reason='Actual Data publication opt-in')
def test_published_declaration_binds_original_consumed_bytes():
    case = json.loads(Path(os.environ['DECLARATION_CASE']).read_bytes())
    scope, roots = case['scope'], case['roots']
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}:
                value.update(scope)
            for item in value.values():
                rescope(item)
        elif isinstance(value, list):
            for item in value:
                rescope(item)
    def call(method, path, body):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        request = Request(os.environ['DECLARATION_DATA'] + path, raw, method=method,
                          headers={'Authorization': 'Bearer ' + os.environ['CTX_TOKEN'], 'Content-Type': 'application/json'})
        with build_opener(ProxyHandler({})).open(request, timeout=20) as response:
            payload = response.read(4194305)
            assert len(payload) <= 4194304
            return json.loads(payload)
    def command(family, payload):
        return {'identity': {'scope': scope, 'actor_id': 'fixture', 'command_family': family,
                             'command_id': 'declaration.' + family}, 'payload': payload}
    raw = source(maximum=200000).request.document().model_dump(mode='json')
    rescope(raw)
    for name in ('objective', 'policy', 'prompt'):
        raw['context'][name] = roots[name]
    raw['context']['model']['configuration'] = roots['configuration']
    document = fixture()[1].document().model_dump(mode='json')
    rescope(document)
    document.update(format='planning-campaign-decision.v2', engagement=raw['reference'],
                    objective=roots['objective'], policy=roots['policy'])
    document.pop('declaration_artifact_id')
    pins = [{'kind': kind, 'identity': roots[name]['artifact_id'], 'revision': '1', 'sha256': roots[name]['sha256']}
            for kind, name in [('source', 'objective'), ('policy', 'policy')]]
    document['future']['context'] = pins
    declaration = DecisionDeclaration.from_bytes(json.dumps(document).encode())
    content = {'sha256': declaration.sha256, 'size_bytes': len(declaration.canonical), 'media_type': 'text/plain',
               'schema_ref': roots['objective']['schema_ref']}
    upload = call('POST', '/v1/uploads', command('artifacts.begin_upload', {'content': content}))
    # Finalized replay has no new stream: retain original uploaded body.
    if case['stage'] == 'initial':
        call('PUT', '/v1/uploads/' + upload['upload_id'] + '/content', declaration.canonical)
    artifact = call('POST', '/v1/artifacts/finalize', command('artifacts.finalize',
        {'upload_id': upload['upload_id'], 'content': content}))['artifact']
    assert artifact['sha256'] == declaration.sha256
    rights = {'wire_version': '1', 'reference': {'scope': scope, 'rights_id': 'declaration', 'revision': 1},
              'supersedes': None, 'status': 'granted', 'allowed_uses': ['read', 'process'],
              'expires_at': None, 'retention': 'retain_audit_payload'}
    call('POST', '/v1/acquisition/rights', rights)
    call('POST', '/v1/acquisition/prepare', {'wire_version': '1',
        'reference': {'scope': scope, 'source_id': 'declaration', 'revision_id': 'r1', 'raw': artifact},
        'delivery': {'issuer_id': 'fixture', 'delivery_id': 'declaration'},
        'method': {'connector_id': 'fixture', 'connector_version': '1',
                   'configuration_sha256': hashlib.sha256(b'{}').hexdigest(), 'format': 'utf8_document'},
        'rights': rights['reference'], 'supersedes': None, 'completeness': 'unknown'})
    raw['decision_scope'] = declaration.sha256
    raw['context']['entries'] = [{'artifact': artifact, 'role': 'constraint', 'required': True}]
    raw['context']['omissions'] = []
    snapshot = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id='fixture', scope=Scope.model_validate(scope))
    plan = ArtifactContextPlan.bind(snapshot)
    read = CampaignArtifactReader(DataReader(os.environ['DECLARATION_DATA'], os.environ['CTX_TOKEN'])).read(
        ArtifactSelection.bind(snapshot, tuple(row.reference for row in plan.items)))
    assert not read.failures and len(read.records) == 5
    bodies = {row.reference.artifact_id: row.body for row in read.records}
    assert bodies[artifact['artifact_id']] == declaration.canonical
    projection = ArtifactContextProjection.bind(plan, tuple(
        ArtifactContextItem.available(row, bodies[row.reference.artifact_id]) for row in plan.items))
    selected = CampaignSlicePlan.from_artifacts(projection)
    value = output('future')
    rescope(value)
    value['decision_scope'] = declaration.sha256
    value['candidate']['definition']['context'] = pins
    value['candidate']['expected_evidence'], value['unresolved'] = [], []
    proposal = prepared(selected, value)
    review = CampaignDecisionReview.bind(proposal, declaration, policy(snapshot))
    assert review.next_step == 'compile_future_draft'
    assert json.loads(declaration.bind(proposal).identity) == artifact
    result = {'declaration_sha256': declaration.sha256, 'artifact': artifact, 'request_sha256': snapshot.sha256,
              'packet_sha256': proposal.inputs.preparation.packet.summary()['sha256'],
              'next_step': review.next_step}
    Path(os.environ['DECLARATION_RESULT']).write_text(json.dumps(result, indent=2))
