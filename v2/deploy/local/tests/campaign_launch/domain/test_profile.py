import json

import pytest
from amphora_deployment.campaign_launch.intent import LaunchError, LaunchIntent
from amphora_deployment.campaign_launch.profile import LaunchProfilePolicy, profile_digest


def document():
    value = {'reference': {'profile_id': 'scientific', 'version': '1', 'sha256': '0' * 64},
        'scope': {'tenant_id': 'internal', 'project_id': 'demo'}, 'title': 'Reviewed science',
        'tools': [{'capability_id': 'materials.hansen-solvency', 'release': '0.1.0',
            'contract_version': '1', 'image_sha256': 'a' * 64}],
        'maximum_invocations': 8, 'maximum_deadline_seconds': 3600}
    value['reference']['sha256'] = profile_digest(value)
    return value


def test_profile_checks_exact_pin_budget_and_tool_image(make_intent):
    value = document()
    policy = LaunchProfilePolicy.from_bytes(json.dumps(value).encode())
    request = json.loads(make_intent().request.canonical_bytes); request['payload']['profile'] = value['reference']
    policy.check(LaunchIntent.parse(json.dumps(request).encode()))
    assert policy.permits(value['tools'][0])
    assert not policy.permits({**value['tools'][0], 'image_sha256': 'b' * 64})
    request['payload']['admission']['payload']['budget']['limit'] = 9
    with pytest.raises(LaunchError, match='launch_profile_limit'):
        policy.check(LaunchIntent.parse(json.dumps(request).encode()))


def test_profile_rejects_mutated_or_duplicate_configuration():
    value = document(); value['maximum_invocations'] = 99
    with pytest.raises(LaunchError): LaunchProfilePolicy.from_bytes(json.dumps(value).encode())
    with pytest.raises(LaunchError): LaunchProfilePolicy.from_bytes(b'{"reference":{},"reference":{}}')
