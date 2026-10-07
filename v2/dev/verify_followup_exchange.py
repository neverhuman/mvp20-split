"""Actual isolated follow-up proposal, retained original and targeted draft successor."""

import argparse
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from check_boundaries import ROOT
from followup_acceptance.materials import write
from followup_acceptance.session import Session


def command(session, family, payload, path):
    record = {'identity': {'scope': session.scope, 'actor_id': 'operator',
        'command_id': uuid.uuid4().hex, 'command_family': family}, 'payload': payload}
    if family != 'definition.validate':
        record['encoding'] = 'amphora-command-v2'
    command_path = session.output / (family + '-command.json')
    if command_path.exists():
        previous = json.loads(command_path.read_bytes())
        assert previous['payload'] == payload and previous['identity']['scope'] == session.scope
        record = previous
    else:
        write(command_path, record)
    receipt = session.runtime.call('POST', path, record)
    assert receipt['outcome']['status'] == 'accepted', 'Public Runtime command rejected: ' + family
    write(session.output / (family + '-receipt.json'), receipt)
    return receipt


def inspect(session, run):
    base = '/v1/supervision/runs/' + run + '/checkpoints'
    checkpoints = session.runtime.call('GET', base + '?limit=10')
    assert checkpoints['total'] == 1
    selected = checkpoints['items'][0]
    query = '?' + urlencode({'limit': 10, 'snapshot_token': checkpoints['snapshot']['snapshot_token']})
    requests_path = base + '/' + selected['reference']['decision_id'] + '/requests'
    requests = session.runtime.call('GET', requests_path + query)
    assert requests['total'] == 1
    request = requests['items'][0]
    responses = session.runtime.call('GET', requests_path + '/' + request['request_sha256'] + '/responses' + query)
    assert responses['total'] == 1
    item = responses['items'][0]
    response = session.runtime.call('GET', '/v1/supervision/responses/' + item['response_id'])
    proposal = json.loads(response['observation']['proposal']['payload_json'])
    assert proposal['action'] == 'propose_campaign' and item['selected_by_winner']
    assert proposal['targets'][0]['criterion'] == session.records['criteria'][0]
    assert [point['criterion'] for point in proposal['unresolved']] == session.records['criteria']
    winner = session.runtime.call('GET', '/v1/supervision/decisions/' + run + '/' + selected['reference']['decision_id'])
    assert winner['outcome']['kind'] == 'model_accepted' and winner['outcome']['effect']['kind'] == 'future_campaign'
    write(session.output / 'proposal-readback.json', {'checkpoints': checkpoints, 'requests': requests,
        'responses': responses, 'response': response, 'winner': winner, 'proposal': proposal})
    return proposal


def successor(session, original, proposal):
    sources = session.runtime.call('GET', '/v1/graph-runs/' + original['run_id'] + '/carry-sources')
    selected = sources['sources'][0]
    saved_path = session.output / 'definition.save-receipt.json'
    if saved_path.exists():
        draft_id = json.loads(saved_path.read_bytes())['outcome']['committed']['object_id']
    else:
        draft_id = 'followup-' + uuid.uuid4().hex
        command(session, 'definition.save', {'draft_id': draft_id, 'expected_revision': 0,
            'title': proposal['candidate']['title'], 'definition': proposal['candidate']['definition']}, '/v1/definition-drafts/save')
    draft = session.runtime.call('GET', '/v1/definition-drafts/' + draft_id + '?revision=1')
    saved = command(session, 'definition.validate', {'draft_id': draft_id, 'revision': 1,
        'content_sha256': draft['head']['content_sha256']}, '/v1/definition-drafts/validate')
    validation = session.runtime.call('GET', '/v1/definition-validations/' + saved['outcome']['committed']['object_id'])
    assert validation['structurally_valid'] and validation['scientific_acceptance'] == 'not_established'
    payload = {'plan_sha256': validation['plan_sha256'], 'inputs': [], 'budget': {'limit': 2},
        'predecessor': sources['predecessor'], 'carried': [{'target_port': 'previous_result',
            'source': selected['source'], 'expected_value_sha256': selected['value_sha256']}],
        'draft': {key: validation[key] for key in ('draft_id', 'revision', 'content_sha256', 'validation_id', 'universe_sha256')}}
    receipt = command(session, 'graph.admit_draft_successor', payload, '/v1/graph-runs/draft-successors')
    run = receipt['outcome']['committed']['object_id']
    result = None
    for _ in range(8):
        session.advance()
        result = session.runtime.call('GET', '/v3/graph-runs/' + run)
        if result['status'] != 'running':
            break
    assert result['status'] == 'completed'
    lineage = session.runtime.call('GET', '/v1/graph-runs/' + run + '/lineage')
    assert lineage['predecessor'] == sources['predecessor'] and lineage['carried'] == payload['carried']
    assert session.runtime.call('GET', '/v3/graph-runs/' + original['run_id']) == original
    write(session.output / 'successor-readback.json', {'draft': draft, 'validation': validation, 'receipt': receipt,
        'original': original, 'result': result, 'lineage': lineage, 'selected_target': proposal['targets'][0],
        'limits': ['Synthetic parameter changed from1 to2; no scientific improvement claim', 'Proposal adopted explicitly by test controller between campaigns']})
    return run


def verify(installation, records, output, resume=False):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1'
    output = output.absolute()
    if resume:
        session = Session.retained(installation.absolute(), records.absolute(), output)
        try:
            original = json.loads((output / 'original-run.json').read_bytes())
            retained = json.loads((output / 'proposal-readback.json').read_bytes())
            assert session.runtime.call('GET', '/v3/graph-runs/' + original['run_id']) == original
            child = successor(session, original, retained['proposal'])
            write(output / 'resume-evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'passed', 'original': original['run_id'], 'successor': child, 'new_provider_calls': 0,
                'steps': session.steps, 'limits': ['Resumed exact retained proposal and saved draft', 'Browser and independent replacement remain pending']})
            print('Retained proposal resumed into a completed draft successor; no new provider calls', flush=True)
        finally:
            session.close()
        return
    output.mkdir(parents=True, exist_ok=False)
    session = Session(installation.absolute(), records.absolute(), output)
    try:
        receipt = command(session, 'graph.admit_supervised', {'admission': {'plan_sha256': session.compiled['plan_sha256'],
            'inputs': [], 'budget': {'limit': 2}}, 'policy_sha256': session.compiled['policy_sha256']}, '/v1/graph-runs/supervised')
        run = receipt['outcome']['committed']['object_id']
        original = None
        for _ in range(14):
            session.command('runtime', ['-m', 'amphora_campaign_runtime.supervision_loop', 'run', '--config', session.runtime_worker,
                '--seconds', '0.2', '--interval', '0.05'])
            session.command('planning', [ROOT / 'services/agent_planning/tests/campaign_followup/owner_probe.py',
                session.planning_worker, output / 'candidate.json'])
            session.advance()
            original = session.runtime.call('GET', '/v3/graph-runs/' + run)
            if original['status'] != 'running':
                break
        write(output / 'rounds.json', session.steps)
        write(output / 'original-run.json', original)
        assert original['status'] == 'completed', 'Original did not complete within bounded rounds'
        proposal = inspect(session, run)
        child = successor(session, original, proposal)
        write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'scope': session.scope, 'original': run, 'successor': child,
            'criteria': len(session.records['criteria']), 'targets': len(proposal['targets']), 'unresolved': len(proposal['unresolved']),
            'paid_calls': 0, 'limits': ['Actual isolated owner software proof with deterministic model fixture',
                'Browser and independent Studio replacement remain pending', 'No scientific validity claim']})
        print('Actual targeted proposal and draft successor passed; original history preserved', flush=True)
    finally:
        session.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['installation', 'records', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    verify(args.installation, args.records, args.output, args.resume)
