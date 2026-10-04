"""LAB-REF01 public scope and immutable query-window acceptance."""
import copy
import json
import urllib.error


def rejected(owner, path, query, status, code=None):
    try:
        owner.request(path, query)
    except urllib.error.HTTPError as error:
        assert error.code == status
        result = json.load(error)
        if code:
            assert result['code'] == code
        return {'status': status, 'code': result.get('code')}
    raise AssertionError('Owner accepted an invalid exploration request')


def prove(scenario, records):
    knowledge, research = scenario.knowledge, scenario.research
    query = {'wire_version': '1', 'revision': records['head']['snapshot'], 'limit': 1}
    path = '/v1/graph-explore/entities'
    first = knowledge.request(path, query)
    assert first['total'] == 2 and len(first['entities']) == 1
    second = knowledge.request(path, {**query, 'position': first['next_position']})
    assert len(second['entities']) == 1 and second['next_position'] is None
    expected = {op['entity']['reference']['entity_id'] for op in records['proposal']['operations'] if op['operation'] == 'add_entity'}
    assert {row['reference']['entity_id'] for page in (first, second) for row in page['entities']} == expected
    graph_conflict = rejected(knowledge, path, {**query, 'text': 'changed', 'position': first['next_position']}, 409, 'explore_position_query')
    foreign = copy.deepcopy(query)
    foreign['revision']['graph']['scope']['project_id'] = 'unowned-project'
    graph_scope = rejected(knowledge, path, foreign, 403)
    specimen_query = {'wire_version': '1', 'experiment': records['specimens']['experiment-definition']['reference'], 'limit': 1}
    path = '/v1/research-explore/specimens'
    specimen_first = research.request(path, specimen_query)
    specimen_second = research.request(path, {**specimen_query, 'position': specimen_first['next_position']})
    assert specimen_first['total'] == 2 and len(specimen_first['rows']) == len(specimen_second['rows']) == 1
    assert specimen_second['next_position'] is None
    assert specimen_first['rows'][0]['sample']['reference'] != specimen_second['rows'][0]['sample']['reference']
    foreign = copy.deepcopy(specimen_query)
    foreign['experiment']['scope']['project_id'] = 'unowned-project'
    research_scope = rejected(research, path, foreign, 403)
    property_query = {**records['comparison']['properties']['request'], 'limit': 1, 'position': None}
    path = '/v1/research-explore/properties'
    property_first = research.request(path, property_query)
    property_second = research.request(path, {**property_query, 'position': property_first['next_position']})
    assert property_second['next_position'] is None
    assert [row['reference'] for page in (property_first, property_second) for row in page['rows']] == property_query['observations']
    assert [row['value'] for page in (property_first, property_second) for row in page['rows']] == [row['value'] for row in records['comparison']['properties']['rows']]
    property_conflict = rejected(research, path, {**property_query, 'observations': list(reversed(property_query['observations'])), 'position': property_first['next_position']}, 409, 'view_position_query')
    assert research.request(path, property_query) == property_first
    assert knowledge.request('/v1/graph-explore/entities', query) == first
    return {'graph_pages': [first, second], 'specimen_pages': [specimen_first, specimen_second],
            'property_pages': [property_first, property_second], 'scope_rejections': [graph_scope, research_scope],
            'cursor_rejections': [graph_conflict, property_conflict]}
