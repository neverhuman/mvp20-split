"""Serve a qualified retained campaign for an internal demo; no workers or model calls."""

import argparse
import hashlib
import json
import time
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState

from local_numeric_configuration import write
from verify_local_browser import BrowserController


def present(qualification, root, output, duration, open_browser):
    evidence = json.loads((qualification / 'evidence.json').read_bytes())
    assert evidence['status'] == 'passed' and evidence['provider_calls'] == 0
    owners = json.loads((qualification / 'owners.json').read_bytes())
    gateway = json.loads((qualification / 'gateway.json').read_bytes())
    selected = json.loads((qualification / 'browser-input.json').read_bytes())
    assert gateway['context']['run_id'] == selected['run_id'] == evidence['run_id']
    assert gateway['context']['scope'] == evidence['scope']
    public = Path(gateway['public_directory'])
    for name, digest in evidence['assets'].items():
        assert name in ('index.html', 'app.js', 'app.css')
        assert hashlib.sha256((public / name).read_bytes()).hexdigest() == digest, 'Qualified assets changed'
    assert set(evidence['assets']) == {'index.html', 'app.js', 'app.css'}
    routes = Routes.load(root)
    origin = routes.endpoint('gateway')
    assert origin == selected['origin']
    assert urllib.parse.urlsplit(origin).hostname in ('127.0.0.1', 'localhost', '::1')
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'gateway.json', gateway)
    owners['owners']['gateway']['configuration'] = str(output / 'gateway.json')
    write(output / 'owners.json', owners)
    state = LocalState.snapshot(root)
    names = ['GATEWAY_SESSION_KEY']
    if 'registry' in owners['owners']:
        names.append('REGISTRY_OPERATOR_TOKEN')
    secrets = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(names)
    controller = BrowserController(root, output, routes, registry_token=secrets.get('REGISTRY_OPERATOR_TOKEN'))
    started = time.monotonic()
    try:
        controller.start()
        correction = (selected.get('successor') or {}).get('correction')
        graph = (correction['snapshot'] if correction else selected['records']['snapshot'])['reference']
        feedback = {'question': selected['records']['question']['reference'],
                    'need': selected['records']['need']['reference'], 'assessment': None,
                    'publication': None, 'proposal': None, 'corrections': None}
        fragment = urllib.parse.urlencode({'explore': json.dumps({'graph': graph, 'experiment': None, 'observations': []}),
                                           'feedback': json.dumps(feedback)})
        if open_browser:
            code, issued = controller.request(origin, '/launcher/ticket', token=secrets['GATEWAY_SESSION_KEY'], method='POST')
            assert code == 200 and type(issued.get('ticket')) is str
            # Ticket is one-time browser bootstrap, never written to evidence or terminal.
            assert webbrowser.open(origin + '/#' + fragment + '&launch=' + urllib.parse.quote(issued['ticket'], safe='')), 'Browser could not open'
        write(output / 'ready.json', {'status': 'ready', 'origin': origin, 'run_id': selected['run_id'],
              'retained_synthetic_campaign': True, 'workers_started': False, 'provider_calls': 0,
              'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        print('Demo ready: retained synthetic campaign. Close with Ctrl+C or create STOP in the session directory.', flush=True)
        try:
            deadline = time.monotonic() + duration
            while time.monotonic() < deadline and not (output / 'STOP').exists():
                assert controller.process.poll() is None, 'Demo supervisor stopped'
                time.sleep(.5)
        except KeyboardInterrupt:
            pass
        final = controller.drain()
        write(output / 'evidence.json', {'status': 'passed', 'run_id': selected['run_id'],
              'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              'elapsed_seconds': round(time.monotonic() - started, 3), 'final': final,
              'provider_calls': 0, 'workers_started': False, 'browser_open_requested': open_browser})
        print('Demo stopped; owners drained successfully.', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('qualification', 'root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--duration', type=int, default=7200)
    parser.add_argument('--open', action='store_true', dest='open_browser')
    args = parser.parse_args()
    if not 1 <= args.duration <= 86400:
        parser.error('duration must be between1 and86400 seconds')
    present(args.qualification.absolute(), args.root.absolute(), args.output.absolute(), args.duration, args.open_browser)
