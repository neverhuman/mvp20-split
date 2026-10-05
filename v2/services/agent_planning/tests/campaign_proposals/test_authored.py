"""Authored address bounds match documented Runtime structural ceilings."""

import copy
import json
from pathlib import Path

import pytest
from amphora_agent_planning.campaign_proposals.authored import AuthoredCampaign
from amphora_contracts_planning import CampaignNodeAddress, FutureCampaignDraft

FIXTURES = Path(__file__).parent / 'fixtures'


def candidate(name='iterate'):
    return {'kind': 'future_campaign', 'title': 'Synthetic authored addresses',
            'definition': json.loads((FIXTURES / (name + '.json')).read_bytes()), 'expected_evidence': []}


def bind(raw):
    return AuthoredCampaign.bind(FutureCampaignDraft.model_validate_json(json.dumps(raw)))


@pytest.mark.parametrize('name', ['iterate', 'scatter'])
def test_nested_scopes_have_explicit_stable_addresses(name):
    authored = bind(candidate(name))
    nested = [node for node in authored.nodes if node.address.scope_path]
    assert nested
    assert all(authored.resolve(node.address) == node for node in nested)
    with pytest.raises(ValueError, match='campaign_producer_unknown'):
        authored.resolve(CampaignNodeAddress(scope_path=('invented',), node_id=nested[0].address.node_id))


@pytest.mark.parametrize('case,code', [('depth', 'campaign_authored_scope_limit'),
                                    ('nodes', 'campaign_authored_node_limit'), ('scopes', 'campaign_authored_scope_limit')])
def test_whole_graph_bounds_apply_beyond_per_scope_wire_limits(case, code):
    raw = candidate()
    template = raw['definition']['body']['nodes'][0]
    finish = {'kind': 'finish', 'node_id': 'finish', 'outputs': []}
    template['body'] = {'nodes': [finish], 'inputs': [], 'outputs': [], 'edges': []}
    if case == 'depth':
        node = copy.deepcopy(template)
        for _ in range(17):
            parent = copy.deepcopy(template)
            parent['body']['nodes'] = [node]
            node = parent
        nodes = [node]
    elif case == 'nodes':
        nodes = []
        for index in range(16):
            node = copy.deepcopy(template)
            node['node_id'] = 'loop-' + str(index)
            node['body']['nodes'] = [dict(finish, node_id='finish-' + str(i)) for i in range(256)]
            nodes.append(node)
    else:
        nodes = []
        for index in range(4):
            node = copy.deepcopy(template)
            node['node_id'] = 'outer-' + str(index)
            node['body']['nodes'] = [dict(copy.deepcopy(template), node_id='inner-' + str(i)) for i in range(256)]
            nodes.append(node)
    raw['definition']['body']['nodes'] = nodes
    with pytest.raises(ValueError, match=code):
        bind(raw)
