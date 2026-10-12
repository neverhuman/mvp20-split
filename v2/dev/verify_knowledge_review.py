"""Run the served Knowledge browser probe with an environment-only launcher key."""
import argparse
import base64
import hashlib
import json
import os
import subprocess
from pathlib import Path
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.persistence.state import LocalState


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'session', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--tls', type=Path)
    parser.add_argument('--suite', choices=['knowledge', 'connected', 'launch', 'generations', 'reasoning'], default='knowledge')
    parser.add_argument('--launch-ready', type=Path, help='Prepared draft identity for the actual launch probe')
    parser.add_argument('--browser-recovery', type=Path, help='Original browser launch journal; never create another request')
    parser.add_argument('--review-only', action='store_true', help='Inspect original launch without a launch POST')
    args = parser.parse_args()
    state = LocalState.snapshot(args.root)
    token = CredentialVault(args.root / 'credentials.dpapi', state['deployment_id']).load().environment(['GATEWAY_SESSION_KEY'])
    env = dict(os.environ, AMPHORA_BROWSER_LAUNCH_KEY=token['GATEWAY_SESSION_KEY'])
    args.output.mkdir(parents=True, exist_ok=True)
    data = json.loads((args.session / 'browser-input.json').read_bytes())
    data['context_schema_id'] = 'demo.campaign-knowledge-context'
    if args.suite == 'launch':
        assert args.launch_ready, 'Launch probe requires the prepared public draft identity'
        prepared = json.loads(args.launch_ready.read_bytes())
        assert prepared['scope'] == data['scope']
        data['draft_id'] = prepared['draft_id']
        if prepared.get('expect_origin'):
            data.update({key: prepared[key] for key in ('expect_origin', 'draft_revision', 'draft_content_sha256', 'origin_sha256')})
            baseline = json.loads((args.launch_ready.parent / 'draft-save-command.json').read_bytes())
            data['manual_draft_id'] = baseline['payload']['draft_id']
    if args.tls:
        openssl = 'C:/Program Files/Git/usr/bin/openssl.exe'
        pem = subprocess.run([openssl, 'x509', '-in', str(args.tls / 'server.pem'), '-pubkey', '-noout'], check=True, capture_output=True).stdout
        der = subprocess.run([openssl, 'pkey', '-pubin', '-outform', 'DER'], input=pem, check=True, capture_output=True).stdout
        data['tls_spki'] = base64.b64encode(hashlib.sha256(der).digest()).decode()
        env['NODE_EXTRA_CA_CERTS'] = str((args.tls / 'amphora-demo-ca.pem').absolute())
    path = args.output / 'browser-input.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    script = {'knowledge': 'knowledge_review.mjs', 'connected': 'connected_flow.mjs',
              'launch': 'campaign_launch.mjs', 'generations': 'generation_comparison.mjs', 'reasoning': 'campaign_reasoning.mjs'}[args.suite]
    assert not args.review_only or args.browser_recovery and args.suite == 'launch'
    extra = [] if args.browser_recovery is None else [str(args.browser_recovery.absolute())]
    if args.review_only:
        extra.append('--review-only')
    result = subprocess.run(['node', 'tests/integration/' + script,
        str(path.absolute()), str(args.output.absolute()), *extra],
        cwd=Path(__file__).parents[1] / 'studio', env=env, timeout=720 if args.suite == 'launch' else 180)
    raise SystemExit(result.returncode)
