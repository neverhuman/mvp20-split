"""Actual owner restart, exact receipt replay and rejected successor acceptance."""
import argparse
import copy
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

from local_numeric_configuration import write
from .campaign import Campaign
from .session import session

CURATION = '/v1/campaign-curations'
SUCCESSOR = '/v1/campaign-successor-launches'


def read(path):
    return json.loads(path.read_bytes())


def receipt_query(receipt):
    return {key: receipt[key] for key in ('identity', 'request_sha256')}


def retained(api, output, evidence):
    attempt = output / 'curation-02'
    original = read(attempt / 'curation-original-receipt.json')
    command = read(attempt / 'curation-command.json')
    assert api.call('planning', CURATION, command, allowed=(200, 202)) == original
    assert api.call('planning', CURATION + '/receipts/query', receipt_query(original)) == original
    current = api.call('planning', CURATION + '/' + original['reference']['curation_id'])
    assert current == evidence['curation'] and current['receipt']['phase'] == 'ready'
    assert hashlib.sha256((attempt / 'synthetic-provider-response.json').read_bytes()).hexdigest() == current['provider']['output_sha256']
    for name in ('predecessor', 'successor'):
        run = evidence[name]
        assert api.call('runtime', '/v3/graph-runs/' + run['run_id']) == run
    assert api.call('runtime', '/v1/graph-runs/' + evidence['successor']['run_id'] + '/lineage') == evidence['lineage']
    launch = evidence['successor_launch']
    assert api.call('deployment', SUCCESSOR + '/' + launch['identity']['command_id']) == launch
    assert api.call('deployment', SUCCESSOR + '/receipts/query', receipt_query(launch)) == launch
    assert api.call('deployment', SUCCESSOR, read(output / 'successor-launch-v3-command.json'), allowed=(200, 202)) == launch
    # Legacy fresh-launch route remains readable and cannot expose a successor.
    first = read(output / 'original-launch-receipt.json')
    assert api.call('deployment', '/v1/campaign-launches/' + first['identity']['command_id']) == first
    api.call('deployment', '/v1/campaign-launches/' + launch['identity']['command_id'], allowed=(404,))
    failed = read(output / 'curation-original-receipt.json')
    failed_view = api.call('planning', CURATION + '/' + failed['reference']['curation_id'])
    assert failed_view['receipt']['phase'] == 'failed'
    assert failed_view['receipt']['reason_code'] == 'decision_tool_applicability'
    assert api.call('planning', CURATION + '/receipts/query', receipt_query(failed)) == failed
    return original, command, launch


def negative_requests(api, output, original, command, launch):
    changed = copy.deepcopy(command)
    changed['payload']['direction'] += ' Changed same identity must conflict.'
    api.call('planning', CURATION, changed, allowed=(409,))
    query = receipt_query(original) | {'request_sha256': '0' * 64}
    api.call('planning', CURATION + '/receipts/query', query, allowed=(409,))
    query = receipt_query(launch) | {'request_sha256': '0' * 64}
    api.call('deployment', SUCCESSOR + '/receipts/query', query, allowed=(409,))
    changed = read(output / 'successor-launch-v3-command.json')
    changed['payload']['admission']['payload']['budget']['limit'] = 3
    api.call('deployment', SUCCESSOR, changed, allowed=(409,))
    api.call('deployment', SUCCESSOR, read(output / 'original-launch-v3-command.json'), allowed=(422,))
    api.call('deployment', '/v1/campaign-launches', read(output / 'successor-launch-v3-command.json'), allowed=(422,))


def rejected_successor(api, output, evidence):
    campaign = Campaign(api, output, evidence['scope'])
    original = read(output / 'successor-admission-v3-command.json')
    payload = copy.deepcopy(original['payload'])
    payload['predecessor']['revision'] -= 1
    admission = campaign.original('stale-successor-admission', 'graph.admit_draft_successor', payload)
    command = campaign.original('stale-successor-launch', 'campaign.launch_successor', {
        'profile': evidence['successor_launch']['profile'], 'admission': admission},
        command_id=admission['identity']['command_id'])
    result = api.call('deployment', SUCCESSOR, command, allowed=(200, 202))
    deadline = time.monotonic() + 60
    while result['phase'] != 'rejected':
        assert result['run_id'] is None and time.monotonic() < deadline, result
        time.sleep(.25)
        result = api.call('deployment', SUCCESSOR + '/' + command['identity']['command_id'])
    assert result['run_id'] is None
    receipt = api.call('runtime', '/v1/commands/graph.admit_draft_successor/' +
                       admission['identity']['command_id'] + '?actor_id=admin')
    assert receipt['outcome']['status'] == 'rejected'
    return {'launch': result, 'runtime_receipt': receipt, 'command': command}


def verify(root, output):
    evidence = read(output / 'integrated-evidence.json')
    assert evidence['status'] == 'passed'
    captures = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in output.rglob('synthetic-provider-*.json')}
    with session(root, output) as api:
        original, command, launch = retained(api, output, evidence)
        negative_requests(api, output, original, command, launch)
        rejected = rejected_successor(api, output, evidence)
        retained(api, output, evidence)
        write(output / 'recovery-first-process.json', rejected)
    # A second independently launched owner process set must recover exact history.
    with session(root, output) as api:
        retained(api, output, evidence)
        assert rejected_successor(api, output, evidence) == rejected
        assert api.call('deployment', SUCCESSOR + '/receipts/query', receipt_query(rejected['launch'])) == rejected['launch']
        retained(api, output, evidence)
    assert {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in output.rglob('synthetic-provider-*.json')} == captures
    write(output / 'recovery-evidence.json', {'status': 'passed',
        'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'retained_predecessor': evidence['predecessor']['run_id'],
        'retained_successor': evidence['successor']['run_id'], 'rejected': rejected,
        'process_sets': 2, 'provider_calls': 0, 'new_successful_campaigns': 0,
        'checks': ['original queued/current ready separation', 'same-ID changes conflict',
            'exact receipt hash query', 'legacy route/family separation',
            'stale predecessor rejected by Runtime', 'exact rejected replay after restart',
            'unchanged completed runs, lineage and original captures']})
    print('Actual replacement/receipt/failure compatibility passed and drained', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.root.absolute(), args.output.absolute())
