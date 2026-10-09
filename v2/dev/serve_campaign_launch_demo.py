"""Prepare or serve the real launch demo; the browser owns campaign launch."""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import time

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.registry_access import provision_registry_credential
from campaign_launch_demo.preparation import prepare
from campaign_launch_demo.controller import LaunchDemoController
from local_numeric_configuration import write


def serve(args):
    root, output = args.root.absolute(), args.output.absolute()
    prepared = json.loads((output / 'launch-prepared.json').read_bytes())
    original = LocalState.snapshot(root)
    provision_registry_credential(root)
    secrets = CredentialVault(root / 'credentials.dpapi', original['deployment_id']).load().environment(
        ['RUNTIME_OPERATOR_TOKEN', 'REGISTRY_OPERATOR_TOKEN'])
    routes = Routes.load(root)
    controller = LaunchDemoController(root, output, routes)
    try:
        controller.start_owners(secrets['REGISTRY_OPERATOR_TOKEN'])
        command = json.loads((output / 'draft-save-command.json').read_bytes())
        status, receipt = controller.request(routes.endpoint('runtime'), '/v1/definition-drafts/save',
            token=secrets['RUNTIME_OPERATOR_TOKEN'], body=command)
        write(output / 'draft-save-receipt.json', {'status': status, 'receipt': receipt})
        assert status == 200 and receipt['outcome']['status'] == 'accepted', 'Public draft save failed; inspect receipt'
        draft_id = command['payload']['draft_id']
        status, draft = controller.request(routes.endpoint('runtime'), '/v1/definition-drafts/' + draft_id + '?revision=1',
            token=secrets['RUNTIME_OPERATOR_TOKEN'])
        assert status == 200 and draft['scope'] == prepared['scope']
        write(output / 'draft-record.json', draft)
        ready = {'status': 'ready', 'origin': routes.endpoint('gateway'), 'scope': prepared['scope'],
            'baseline_run': prepared['baseline_run'], 'draft_id': draft_id, 'draft_revision': 1,
            'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'scheduled_stop_local': (datetime.now() + timedelta(seconds=args.duration)).strftime('%Y-%m-%d %H:%M:%S'),
            'provider_calls': 0, 'qualification': 'pending_actual_browser_campaign', 'launches_submitted_by_helper': 0}
        write(output / 'ready.json', ready)
        print('Campaign launch demo ready: ' + ready['origin'], flush=True)
        deadline = time.monotonic() + args.duration
        while time.monotonic() < deadline and not (output / 'STOP').exists():
            assert controller.process.poll() is None, 'Supervisor exited; retained launch needs reconciliation'
            time.sleep(.5)
        final = controller.drain()
        write(output / 'drain.json', {'status': 'drained', 'final': final})
    finally:
        controller.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'serve'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--installations', type=Path)
    parser.add_argument('--public', type=Path)
    parser.add_argument('--duration', type=int, default=86400)
    args = parser.parse_args()
    if args.action == 'prepare':
        assert args.source and args.installations and args.public
        prepare(args.root, args.source, args.installations, args.public, args.output)
        print('Launch configuration prepared; no owners or workers started')
    else:
        assert 60 <= args.duration <= 172800
        serve(args)


if __name__ == '__main__':
    main()
