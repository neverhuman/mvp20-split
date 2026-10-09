import json
from types import SimpleNamespace
import pytest

from amphora_contracts_core import ArtifactRef
from amphora_contracts_graph_runtime import DraftRevision, DraftValidation
from amphora_contracts_tools import ToolBinding
from amphora_deployment.campaign_launch.ports import PeerRecordMissing, PreflightRejected
from amphora_deployment.campaign_launch.preflight import InstalledExecutor, LaunchPreflight


@pytest.fixture
def preflight_setup(make_intent):
    intent = make_intent()
    scope = intent.request.identity.scope.model_dump(mode='json')
    tool = {'capability_id': 'materials.hansen-solvency', 'release': '0.1.0',
            'contract_version': '1', 'image_sha256': 'e' * 64}
    artifact = {'artifact_id': 'input', 'scope': scope, 'sha256': 'f' * 64,
        'media_type': 'application/json', 'schema_ref': {'schema_id': 'inputs', 'version': '1', 'sha256': 'f' * 64},
        'size_bytes': 2}
    draft = {'scope': scope, 'head': {'draft_id': 'draft', 'revision': 1,
        'content_sha256': 'b' * 64, 'title': 'Reviewed campaign'}, 'parent_revision': 0,
        'definition': {'schema_version': '4', 'profile': 'deterministic-v3',
            'campaign_id': 'research', 'revision': 1, 'scope': scope, 'body': {'nodes': [
                {'kind': 'invoke', 'node_id': 'science', 'tool': tool, 'timeout_seconds': 60,
                 'inputs': [{'port': 'parameters', 'source': {'kind': 'artifact', 'artifact': artifact,
                    'representation': 'parameters', 'unit': '1'}}]},
                {'kind': 'finish', 'node_id': 'done', 'outputs': []}]}}}
    validation = {'scope': scope, 'validation_id': 'validation', 'draft_id': 'draft', 'revision': 1,
        'content_sha256': 'b' * 64, 'universe_sha256': 'c' * 64, 'structurally_valid': True,
        'plan_sha256': 'a' * 64, 'findings': [], 'pending_checks': []}
    binding = ToolBinding.model_validate_json(json.dumps(tool))
    lock = SimpleNamespace(tool=binding, descriptor_sha256='9' * 64)
    deployment = SimpleNamespace(scope=intent.request.identity.scope, status='active',
        deployment=SimpleNamespace(deployment_id='installed', release=lock,
            workers=('worker',), architecture='x86_64', operating_system='linux'))
    release = SimpleNamespace(scope=intent.request.identity.scope, status='active', lock=lock)
    records = {'draft': draft, 'validation': validation, 'artifact': artifact,
        'deployment': deployment, 'release': release}
    calls = []
    def read(path, model):
        calls.append(path)
        if '/definition-drafts/' in path: return DraftRevision.model_validate_json(json.dumps(records['draft']))
        if '/definition-validations/' in path: return DraftValidation.model_validate_json(json.dumps(records['validation']))
        if '/artifacts/' in path: return ArtifactRef.model_validate_json(json.dumps(records['artifact']))
        if '/deployments/' in path: return records['deployment']
        if '/releases/' in path: return records['release']
        raise AssertionError(path)
    peer = SimpleNamespace(read=read)
    policy = SimpleNamespace(check=lambda value: None, permits=lambda value: value == tool)
    preflight = LaunchPreflight(policy, peer, peer, peer, [InstalledExecutor(binding, 'installed', 'worker')],
        lambda value, tools: calls.append('local-capacity'))
    return preflight, intent, records, calls


def test_public_exact_draft_validation_tool_and_artifact_precede_capacity(preflight_setup):
    preflight, intent, records, calls = preflight_setup
    preflight.check(intent)
    assert calls == ['/v1/definition-drafts/draft?revision=1', '/v1/definition-validations/validation',
        '/v1/deployments/installed', '/v1/releases/' + '9' * 64, '/v1/artifacts/input', 'local-capacity']


@pytest.mark.parametrize('key,value', [('revision', 2), ('content_sha256', '1' * 64),
    ('universe_sha256', '1' * 64), ('plan_sha256', '1' * 64), ('validation_id', 'other')])
def test_mismatched_validation_cannot_reach_workers(preflight_setup, key, value):
    preflight, intent, records, calls = preflight_setup
    records['validation'][key] = value
    with pytest.raises(PreflightRejected): preflight.check(intent)
    assert len(calls) == 2


def test_revoked_deployment_does_not_allow_launch(preflight_setup):
    preflight, intent, records, calls = preflight_setup
    records['deployment'].status = 'revoked'
    with pytest.raises(PreflightRejected): preflight.check(intent)
    assert 'local-capacity' not in calls


def test_uninstalled_tool_cannot_be_smuggled_through_valid_draft(preflight_setup):
    preflight, intent, records, calls = preflight_setup
    records['draft']['definition']['body']['nodes'][0]['tool']['image_sha256'] = '8' * 64
    with pytest.raises(PreflightRejected): preflight.check(intent)
    assert 'local-capacity' not in calls


def test_data_hash_mismatch_blocks_admission(preflight_setup):
    preflight, intent, records, calls = preflight_setup
    records['artifact'] = {**records['artifact'], 'sha256': '8' * 64}
    with pytest.raises(PreflightRejected): preflight.check(intent)
    assert 'local-capacity' not in calls


def test_explicit_missing_draft_rejects_before_admission(preflight_setup):
    preflight, intent, records, calls = preflight_setup
    def missing(*args): raise PeerRecordMissing()
    preflight.runtime = SimpleNamespace(read=missing)
    with pytest.raises(PreflightRejected): preflight.check(intent)
    assert calls == []
