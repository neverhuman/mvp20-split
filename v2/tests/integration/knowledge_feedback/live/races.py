"""LAB-REF02: concurrent public correction writers during an immutable open wait."""
import copy
import json
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier


def compete(owner, path, requests):
    barrier = Barrier(2)
    def submit(request):
        barrier.wait(timeout=10)
        try:
            return {'http_status': 200, 'result': owner.request(path, request)}
        except urllib.error.HTTPError as error:
            return {'http_status': error.code, 'result': json.load(error)}
    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(submit, requests))


def prove(scenario, records, runtime):
    feedback = records['feedback']
    research, knowledge = scenario.research, scenario.knowledge
    chain = {**feedback['root']['reference']['chain'], 'chain_id': 'pending-correction-race'}
    root_request = {'wire_version': '1', 'chain': chain, 'change_id': 'race-initial',
        'assessment_id': 'original', 'reason_code': 'initial_evidence', 'expected_head': None}
    root = research.request('/v1/assessment-receipts/correct', root_request)
    correction_requests = [{**root_request, 'change_id': 'race-receipt-' + name, 'assessment_id': 'next',
        'reason_code': 'quality_review', 'expected_head': root['reference']} for name in ('left', 'right')]
    proposals = []
    source = feedback['proposal']['proposal']
    for name in ('left', 'right'):
        proposal = copy.deepcopy(source)
        prior = proposal['operations'][0]['replacement']
        replacement = copy.deepcopy(prior)
        replacement['reference']['revision'] += 1
        replacement['supersedes'] = prior['reference']
        replacement['statement'] = 'Synthetic next-iteration alternative ' + name + '; scientific review remains necessary.'
        proposal.update(change_id='race-' + name, base=feedback['proposal']['decision']['decision']['head'],
            description='Competing synthetic revision ' + name,
            operations=[{'operation': 'correct_assertion', 'prior': prior['reference'], 'replacement': replacement}])
        proposals.append(proposal)
    observed = {}
    def correct_while_open(active, opened):
        path = '/v1/graph-runs/' + opened['expectation']['run_id'] + '/waits/' + opened['expectation']['activation_id']
        assert active.owner.request(path) == opened and opened['closure'] is None
        proposals_result = compete(knowledge, '/v1/graph-proposals', proposals)
        assert all(item['http_status'] == 200 for item in proposals_result)
        assert sorted(item['result']['decision']['outcome'] for item in proposals_result) == ['accepted', 'conflict']
        for proposal, result in zip(proposals, proposals_result, strict=True):
            assert knowledge.request('/v1/graph-proposals', proposal) == result['result']
            stored = knowledge.request('/v1/graphs/' + proposal['graph']['graph_id'] + '/proposals/' + proposal['change_id'])
            assert stored['decision'] == result['result']
        corrections = compete(research, '/v1/assessment-receipts/correct', correction_requests)
        assert sorted(item['http_status'] for item in corrections) == [200, 409]
        winner_index = next(i for i, item in enumerate(corrections) if item['http_status'] == 200)
        winner = corrections[winner_index]['result']
        loser = corrections[1 - winner_index]['result']
        assert loser['code'] == 'correction_head_conflict'
        assert winner['record']['predecessor'] == root['reference']
        assert research.request('/v1/assessment-receipts/correct', correction_requests[winner_index]) == winner
        selection = {'wire_version': '1', 'chain': chain, 'revision': None}
        assert research.request('/v1/assessment-receipts/select', selection) == winner
        assert research.request('/v1/assessment-receipts/select', {**selection, 'revision': root['reference']}) == root
        assert active.owner.request(path) == opened
        rejections = []
        for receipt, reason in [(winner['record']['notice'], 'wait_receipt_superseded'),
                                (winner['record']['receipt'], 'wait_receipt_revision_mismatch')]:
            command = active.command('graph.submit_receipt', {'run_id': opened['expectation']['run_id'],
                'activation_id': opened['expectation']['activation_id'], 'wait_revision': opened['expectation']['wait_revision'],
                'expectation_sha256': opened['expectation_sha256'], 'receipt': receipt}, receipt['issuer_id'])
            rejected = active.owner.request('/v1/graph-receipts', command, token=active.environment['ISSUER_TOKEN'])
            assert rejected['outcome']['status'] == 'rejected' and rejected['outcome']['reason_code'] == reason
            assert active.owner.request(path) == opened
            rejections.append(rejected)
        observed.update(proposals=proposals_result, corrections=corrections, winner=winner)
        return {'barrier': 'open wait -> competing corrections committed -> reject notice/new pin -> original consumption',
                'expectation_sha256': opened['expectation_sha256'], 'rejections': rejections}
    old = runtime.consume(scenario.data, root['record']['receipt'], campaign_id='race-original',
        output_schema='assessment.json', before_receipt=correct_while_open)
    new = runtime.consume(scenario.data, observed['winner']['record']['receipt'], campaign_id='race-next', output_schema='assessment.json')
    expected = old['opened']['expectation']
    assert runtime.owner.request('/v1/graph-runs/' + expected['run_id'] + '/waits/' + expected['activation_id']) == old['closed']
    assert old['graph']['plan_sha256'] != new['graph']['plan_sha256']
    assert old['closed']['closure']['outcome']['receipt']['outcome']['output'] != new['closed']['closure']['outcome']['receipt']['outcome']['output']
    return {'root': root, **observed, 'old_run': old, 'new_run': new,
        'limits': ['Client release barriers; no internal database scheduling or throughput claim',
                   'Synthetic evidence authority; accepted alternative is not automatically adopted']}
