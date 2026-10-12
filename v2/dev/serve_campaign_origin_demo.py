"""Prepare/serve the approved provenance demo; browser alone launches the campaign."""
import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from campaign_launch_demo.controller import LaunchDemoController
from campaign_origin_demo.forward import migrate
from campaign_origin_demo.preparation import prepare, write
from campaign_origin_demo.publication import prepare_case


def serve(args):
    root, output = args.root.absolute(), args.output.absolute()
    prepared = json.loads((output / 'origin-prepared.json').read_bytes())
    installation = Path(prepared['installation'])
    state = LocalState.snapshot(root)
    bundle = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load()
    names = [name.upper() + '_OPERATOR_TOKEN' for name in ('artifact', 'registry', 'runtime', 'research', 'knowledge', 'planning')]
    tokens = bundle.environment(names)
    routes = Routes.load(root)
    controller = LaunchDemoController(root, output, routes)
    started = False
    try:
        controller.start_owners(tokens['REGISTRY_OPERATOR_TOKEN'])
        started = True
        for name in controller.control('/status')['scientific_workers']:
            controller.control('/scientific-workers/' + name + '/standby', 'POST')
        case = output / 'compiler-case.json'
        if not case.exists():
            case = prepare_case(controller, tokens, output, args.knowledge_records.absolute())
        if not (output / 'compiler-completed.json').exists():
            password = bundle.environment(['PG_PLANNING_SERVICE_PASSWORD'])['PG_PLANNING_SERVICE_PASSWORD']
            env = {key: value for key, value in os.environ.items() if key.upper() in {
                'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
            env.update(PYTHONUTF8='1', ORIGIN_PLANNING_DATABASE='postgresql+psycopg://planning_service:' +
                quote(password, safe='') + '@127.0.0.1:' + str(state['postgres']['port']) + '/amphora_local?connect_timeout=5')
            env.update({'ORIGIN_' + name + '_TOKEN': tokens[name + '_OPERATOR_TOKEN']
                        for name in ('ARTIFACT', 'REGISTRY', 'RUNTIME', 'RESEARCH', 'KNOWLEDGE')})
            with (output / 'compiler.log').open('ab') as log:
                result = subprocess.run([str(installation / 'planning/environment/Scripts/python.exe'), '-I',
                    str(Path(__file__).parent / 'campaign_origin_demo/compiler.py'), str(case)], env=env,
                    stdout=log, stderr=log, timeout=300, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            assert result.returncode == 0, 'Compiler qualification failed; inspect compiler.log'
        completed = json.loads((output / 'compiler-completed.json').read_bytes())
        draft = completed['draft']
        request = Request(routes.endpoint('planning') + '/v1/campaign-origins/' + draft['draft_id'] +
            '?revision=' + str(draft['revision']) + '&content_sha256=' + draft['content_sha256'],
            headers={'Authorization': 'Bearer ' + tokens['PLANNING_OPERATOR_TOKEN']})
        start = time.monotonic()
        # Match the Gateway/Studio read budget; the controller's 3s health budget
        # is too short for full original-proposal reconstruction.
        with controller.opener.open(request, timeout=15) as response:
            raw = response.read(262145)
            assert response.status == 200 and len(raw) <= 262144
            origin = json.loads(raw)
        assert origin['origin_sha256'] == completed['origin_sha256']
        write(output / 'origin-read-timing.json', {'elapsed_seconds': time.monotonic() - start,
            'response_bytes': len(raw), 'origin_sha256': origin['origin_sha256']})
        write(output / 'public-origin.json', origin)
        ready = {'status': 'ready', 'origin': routes.endpoint('gateway'), 'scope': prepared['scope'],
            'draft_id': draft['draft_id'], 'draft_revision': draft['revision'], 'draft_content_sha256': draft['content_sha256'], 'expect_origin': True,
            'origin_sha256': completed['origin_sha256'], 'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'scheduled_stop_local': (datetime.now() + timedelta(seconds=args.duration)).strftime('%Y-%m-%d %H:%M:%S'),
            'paid_provider_calls': 0, 'qualification': 'pending_actual_browser_campaign', 'launches_submitted_by_helper': 0}
        write(output / 'ready.json', ready)
        write(output / 'browser-input.json', {**ready, 'context_schema_id': 'demo.campaign-knowledge-context'})
        print('Campaign provenance demo ready: ' + ready['origin'], flush=True)
        deadline = time.monotonic() + args.duration
        while time.monotonic() < deadline and not (output / 'STOP').exists():
            assert controller.process.poll() is None, 'Supervisor exited'
            time.sleep(.5)
    finally:
        try:
            if started and controller.process.poll() is None:
                write(output / 'drain.json', {'status': 'drained', 'final': controller.drain()})
            elif not started:
                write(output / 'startup-failure.json', {'status': 'failed_before_owner_readiness',
                    'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'campaigns_launched': 0})
        finally:
            controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'migrate', 'serve'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--installation', type=Path)
    parser.add_argument('--predecessor', type=Path)
    parser.add_argument('--knowledge-records', type=Path)
    parser.add_argument('--duration', type=int, default=86400)
    args = parser.parse_args()
    if args.action == 'prepare':
        assert args.source and args.installation
        prepare(args.source.absolute(), args.output.absolute(), args.installation.absolute(),
                Path(__file__).absolute().parents[1] / 'studio/dist/local', Routes.load(args.root))
    elif args.action == 'migrate':
        assert args.installation and args.predecessor
        migrate(args.root.absolute(), args.installation.absolute() / 'planning', args.predecessor.absolute(), args.output.absolute())
    else:
        assert args.knowledge_records and 60 <= args.duration <= 172800
        serve(args)
