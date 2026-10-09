import json
from datetime import datetime, timezone

import pytest
from amphora_contracts_runtime import CommandReceipt
from amphora_deployment.campaign_launch.intent import LaunchIntent


@pytest.fixture
def make_intent():
    def make(request_id='launch-1', profile='d' * 64):
        identity = {'command_family': 'campaign.launch', 'command_id': request_id,
            'actor_id': 'researcher', 'scope': {'tenant_id': 'internal', 'project_id': 'demo'}}
        admission = {'identity': {**identity, 'command_family': 'graph.admit_draft'}, 'payload': {
            'plan_sha256': 'a' * 64, 'inputs': [], 'budget': {'limit': 8, 'max_attempts_per_activation': 2},
            'draft': {'draft_id': 'draft', 'revision': 1, 'content_sha256': 'b' * 64,
                'validation_id': 'validation', 'universe_sha256': 'c' * 64}}}
        return LaunchIntent.parse(json.dumps({'encoding': 'amphora-command-v2', 'identity': identity,
            'payload': {'profile': {'profile_id': 'scientific', 'version': '1', 'sha256': profile},
                'admission': admission}}).encode())
    return make


@pytest.fixture
def clock():
    return lambda: datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def admission_receipt():
    def make(intent, status='accepted', operation='operation-1', run='run-1'):
        outcome = {'status': status, 'binding': {'identity': intent.admission.identity.model_dump(),
            'request_sha256': intent.admission.sha256, 'operation_id': operation}}
        if status == 'accepted': outcome['committed'] = {'kind': 'run', 'object_id': run, 'revision': 0}
        if status == 'rejected': outcome['reason_code'] = 'draft_stale'
        return CommandReceipt.model_validate_json(json.dumps({'outcome': outcome}))
    return make
