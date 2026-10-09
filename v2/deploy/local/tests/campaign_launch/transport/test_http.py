import json
import threading
import urllib.error
import urllib.request
import pytest

from amphora_deployment.campaign_launch.http import LaunchServer
from amphora_deployment.campaign_launch.journal import LaunchJournal
from amphora_deployment.campaign_launch.profile import LaunchProfilePolicy, profile_digest


@pytest.fixture
def launch_api(tmp_path, make_intent):
    document = {'reference': {'profile_id': 'scientific', 'version': '1', 'sha256': '0' * 64},
        'scope': {'tenant_id': 'internal', 'project_id': 'demo'}, 'title': 'Installed science',
        'tools': [{'capability_id': 'materials.hansen-solvency', 'release': '0.1.0',
            'contract_version': '1', 'image_sha256': 'a' * 64}],
        'maximum_invocations': 8, 'maximum_deadline_seconds': 3600}
    document['reference']['sha256'] = profile_digest(document)
    policy = LaunchProfilePolicy.from_bytes(json.dumps(document).encode())
    stop, available = threading.Event(), [True]
    token = 'synthetic-launch-token-00000000000000000'
    journal = LaunchJournal(tmp_path)
    server = LaunchServer(0, token, 'researcher', policy, journal, lambda: available[0], stop)
    thread = threading.Thread(target=server.serve); thread.start()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(path, body=None, *, authenticated=True, declared_length=None):
        headers = {'Authorization': 'Bearer ' + token} if authenticated else {}
        if body is not None: headers['Content-Type'] = 'application/json'
        if declared_length is not None: headers['Content-Length'] = str(declared_length)
        req = urllib.request.Request('http://127.0.0.1:' + str(server.server_port) + path,
            data=body, headers=headers, method='POST' if body is not None else 'GET')
        try: response = opener.open(req, timeout=5)
        except urllib.error.HTTPError as error: response = error
        with response:
            return response.status, json.loads(response.read())
    intent = make_intent(profile=policy.view.reference.sha256)
    try: yield request, intent, journal, available, make_intent
    finally:
        stop.set(); thread.join(5); assert not thread.is_alive()


def test_launch_api_is_authenticated_scoped_and_replayable(launch_api):
    request, intent, journal, _, _ = launch_api
    assert request('/v1/campaign-launch-profiles', authenticated=False)[0] == 401
    assert request('/v1/campaign-launches', intent.request.canonical_bytes, authenticated=False)[0] == 401
    assert journal.active() is None
    status, profiles = request('/v1/campaign-launch-profiles')
    assert status == 200 and profiles['scope'] == intent.request.identity.scope.model_dump()
    first = request('/v1/campaign-launches', intent.request.canonical_bytes)
    assert first[0] == 202 and first[1]['phase'] == 'preparing'
    assert request('/v1/campaign-launches', intent.request.canonical_bytes) == first
    assert request('/v1/campaign-launches/launch-1') == (200, first[1])


def test_busy_and_changed_request_do_not_change_original(launch_api):
    request, intent, journal, _, make_intent = launch_api
    request('/v1/campaign-launches', intent.request.canonical_bytes)
    original = journal.active()
    second = make_intent('second', intent.profile.sha256)
    assert request('/v1/campaign-launches', second.request.canonical_bytes) == (409, {'reason_code': 'launch_slot_busy'})
    changed = make_intent(profile='e' * 64)
    assert request('/v1/campaign-launches', changed.request.canonical_bytes) == (409, {'reason_code': 'launch_request_conflict'})
    assert journal.active() == original


def test_foreign_actor_and_supervisor_routes_are_denied(launch_api):
    request, intent, journal, _, _ = launch_api
    value = json.loads(intent.request.canonical_bytes)
    value['identity']['actor_id'] = value['payload']['admission']['identity']['actor_id'] = 'foreign'
    assert request('/v1/campaign-launches', json.dumps(value).encode())[0] == 403
    assert request('/owners/runtime/start', b'{}')[0] == 404
    assert request('/v1/campaign-launches/missing')[0] == 404
    assert journal.active() is None


def test_stopping_host_rejects_new_launches_but_keeps_receipts_readable(launch_api):
    request, intent, journal, available, _ = launch_api
    request('/v1/campaign-launches', intent.request.canonical_bytes)
    available[0] = False
    assert request('/v1/campaign-launches', intent.request.canonical_bytes)[0] == 503
    assert request('/v1/campaign-launches/launch-1')[0] == 200


def test_invalid_payload_and_query_do_not_create_work(launch_api):
    request, intent, journal, _, _ = launch_api
    assert request('/v1/campaign-launches', b'{"command":"docker run"}')[0] == 422
    assert request('/v1/campaign-launch-profiles?project=foreign')[0] == 404
    # Refuse an oversized declaration before reading any body. Sending a rejected
    # full body races Windows' unread-data socket reset with receipt delivery.
    assert request('/v1/campaign-launches', b'', declared_length=262145)[0] == 422
    assert journal.active() is None
