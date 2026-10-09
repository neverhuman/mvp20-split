import http.client
import json
import threading

from amphora_deployment.campaign_launch.http import LaunchServer
from amphora_deployment.campaign_launch.journal import LaunchJournal
from amphora_deployment.campaign_launch.profile import LaunchProfilePolicy, profile_digest
from amphora_local_gateway.configuration import Configuration, Peer
from amphora_local_gateway.server import GatewayServer


def test_browser_session_reaches_only_scoped_idempotent_launch_surface(tmp_path):
    scope = {'tenant_id': 'internal', 'project_id': 'demo'}
    document = {'reference': {'profile_id': 'scientific', 'version': '1', 'sha256': '0' * 64},
        'scope': scope, 'title': 'Reviewed science', 'tools': [{'capability_id': 'materials.hansen-solvency',
            'release': '0.1.0', 'contract_version': '1', 'image_sha256': 'a' * 64}],
        'maximum_invocations': 8, 'maximum_deadline_seconds': 3600}
    document['reference']['sha256'] = profile_digest(document)
    policy = LaunchProfilePolicy.from_bytes(json.dumps(document).encode())
    launch_token = 'fixture-private-launch-token-000000000000'
    stop = threading.Event()
    journal = LaunchJournal(tmp_path / 'journal')
    launch = LaunchServer(0, launch_token, 'researcher', policy, journal, lambda: True, stop)
    public = tmp_path / 'public'; public.mkdir()
    for name in ('index.html', 'app.js', 'app.css'): (public / name).write_text('fixture')
    gateway = GatewayServer(Configuration(public, {'deployment': Peer(launch.server_port, launch_token)},
        {'actor_id': 'researcher', 'scope': scope, 'run_id': None, 'synthetic': True},
        'fixture-private-launcher-token-000000000'), 0)
    launch_thread = threading.Thread(target=launch.serve)
    gateway_thread = threading.Thread(target=lambda: gateway.serve_forever(poll_interval=.05))
    launch_thread.start(); gateway_thread.start()
    def request(path, method='GET', headers=None, body=None):
        connection = http.client.HTTPConnection('127.0.0.1', gateway.server_port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            raw = response.read()
            assert launch_token.encode() not in raw
            return response.status, dict(response.getheaders()), json.loads(raw)
        finally: connection.close()
    try:
        assert request('/api/deployment/v1/campaign-launch-profiles')[0] == 401
        code, _, ticket = request('/launcher/ticket', 'POST', {'Authorization': 'Bearer ' + gateway.configuration.launcher_key})
        assert code == 200
        code, headers, _ = request('/session', 'POST', {'Origin': gateway.origin, 'Content-Type': 'application/json'}, json.dumps(ticket))
        assert code == 200
        cookie = headers['Set-Cookie'].split(';')[0]
        headers = {'Cookie': cookie, 'Origin': gateway.origin, 'Content-Type': 'application/json',
                   'Authorization': 'Bearer browser-cannot-select-peer-credential'}
        code, _, catalog = request('/api/deployment/v1/campaign-launch-profiles', headers=headers)
        assert code == 200 and catalog['profiles'][0]['reference'] == document['reference']
        identity = {'command_family': 'campaign.launch', 'command_id': 'launch-1', 'actor_id': 'researcher', 'scope': scope}
        body = json.dumps({'encoding': 'amphora-command-v2', 'identity': identity,
            'payload': {'profile': document['reference'], 'admission': {
                'identity': {**identity, 'command_family': 'graph.admit_draft'}, 'payload': {
                    'plan_sha256': 'a' * 64, 'inputs': [], 'budget': {'limit': 8, 'max_attempts_per_activation': 2},
                    'draft': {'draft_id': 'draft', 'revision': 1, 'content_sha256': 'b' * 64,
                        'validation_id': 'validation', 'universe_sha256': 'c' * 64}}}}})
        assert request('/api/deployment/v1/campaign-launches', 'POST', {**headers, 'Origin': 'https://foreign.invalid'}, body)[0] == 403
        assert journal.active() is None
        code, _, first = request('/api/deployment/v1/campaign-launches', 'POST', headers, body)
        assert code == 202 and first['phase'] == 'preparing'
        assert request('/api/deployment/v1/campaign-launches', 'POST', headers, body)[2] == first
        assert request('/api/deployment/v1/campaign-launches/launch-1', headers=headers)[2] == first
        assert request('/api/deployment/v1/owners/runtime/start', 'POST', headers, b'{}')[0] == 403
        second = json.loads(body)
        second['identity']['command_id'] = second['payload']['admission']['identity']['command_id'] = 'second'
        assert request('/api/deployment/v1/campaign-launches', 'POST', headers, json.dumps(second))[2] == {'reason_code': 'launch_slot_busy'}
        assert journal.active().intent.request.identity.command_id == 'launch-1'
    finally:
        gateway.shutdown(); gateway.server_close(); gateway_thread.join(5)
        stop.set(); launch_thread.join(5)
        assert not gateway_thread.is_alive() and not launch_thread.is_alive()
