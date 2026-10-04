"""Public fixture encoding and actual Qdrant generation, with no semantic-quality claim."""


def publish_representation(data, span):
    profiles = data.request('/v1/representations/available-profiles')
    profile = next(profile for profile in profiles if profile['version'] == '1' and profile['space']['normalization'] == 'none')
    reference = data.request('/v1/representations/profiles', profile)
    encoding = data.request('/v1/representations/encodings', {'wire_version': '1', 'encoding_id': 'baseline', 'profile': reference, 'source': span})
    binding = encoding['outcome']['binding']
    generation = data.request('/v1/retrieval/generations', {'wire_version': '1', 'corpus_id': 'feedback',
        'generation_id': 'baseline', 'profile': reference, 'bindings': [binding['reference']], 'expected_head': None})
    assert generation['state'] == 'published'
    query = {'wire_version': '1', 'retrieval_id': 'baseline', 'generation': generation['generation']['reference'],
        'query': binding['reference'], 'policy': {'format': 'data.exact-dot-ranking.v1', 'top_k': 1,
        'bindings': None, 'metric': 'dot', 'order': 'score_desc_binding_asc', 'quality_filter': 'none'}}
    result = data.request('/v1/retrieval/queries', query)
    assert len(result['matches']) == 1 and result['matches'][0]['binding'] == binding
    assert data.request('/v1/retrieval/queries/baseline') == result
    return {'profile': reference, 'generation': generation, 'binding': binding, 'query': result}
