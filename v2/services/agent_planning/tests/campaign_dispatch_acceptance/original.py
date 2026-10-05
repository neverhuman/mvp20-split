"""Actual Data publication, processing reads and selected peer metadata before original hashing."""

import hashlib
import json
from urllib.request import ProxyHandler, Request, build_opener

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


def original(case, data_endpoint, token, registry, runtime):
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
        request = Request(data_endpoint + path, raw, method=method,
                          headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
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
    read = CampaignArtifactReader(DataReader(data_endpoint, token)).read(
        ArtifactSelection.bind(snapshot, tuple(row.reference for row in plan.items)))
    assert not read.failures and len(read.records) == 5
    bodies = {row.reference.artifact_id: row.body for row in read.records}
    assert bodies[artifact['artifact_id']] == declaration.canonical
    projection = ArtifactContextProjection.bind(plan, tuple(
        ArtifactContextItem.available(row, bodies[row.reference.artifact_id]) for row in plan.items))
    selected = CampaignSlicePlan.from_artifacts(projection)
    from amphora_agent_planning.registry_access import DiscoveryQuery
    scan = registry.discover(DiscoveryQuery(snapshot, limit=100, max_pages=1))
    assert scan.complete and len(scan.records) == 1
    selected = selected.with_registry(scan, ())
    universe = runtime.universe(snapshot)
    schemas = runtime.schemas(universe, universe.document().schemas)
    assert not schemas.failures
    selected = selected.with_runtime(schemas)
    release = scan.records[0].document()
    port, result_port = release.descriptor.tool.inputs[0], release.descriptor.tool.outputs[0]
    def value_type(value):
        return {'kind': 'artifact', 'schema_ref': value.schema_ref.model_dump(mode='json'),
                'representation': value.representation, 'unit': value.unit, 'media_type': 'application/json'}
    value = output('future')
    rescope(value)
    value['decision_scope'] = declaration.sha256
    value['candidate']['definition']['context'] = pins
    value['candidate']['expected_evidence'], value['unresolved'] = [], []
    value['candidate']['definition']['body'] = {
        'inputs': [{'name': 'value', 'value_type': value_type(port)}],
        'outputs': [{'name': 'result', 'value_type': value_type(result_port)}],
        'nodes': [{'kind': 'invoke', 'node_id': 'calculate', 'tool': release.lock.tool.model_dump(mode='json'),
                   'inputs': [{'port': port.name, 'source': {'kind': 'input', 'name': 'value'}}],
                   'checkpoint': None, 'timeout_seconds': 30},
                  {'kind': 'finish', 'node_id': 'finish', 'outputs': [
                      {'port': 'result', 'source': {'kind': 'output', 'node_id': 'calculate', 'port': result_port.name}}]}],
        'edges': [{'source': 'calculate', 'target': 'finish', 'route': 'next'}]}
    proposal = prepared(selected, value)
    review = CampaignDecisionReview.bind(proposal, declaration, policy(snapshot))
    assert review.next_step == 'compile_future_draft'
    assert json.loads(declaration.bind(proposal).identity) == artifact
    return review, policy(snapshot), selected
