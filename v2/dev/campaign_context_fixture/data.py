"""Synthetic source/vector/query preparation through actual public Data APIs."""

import hashlib


def command(scope, family, key, payload):
    return {'identity': {'scope': scope, 'actor_id': 'fixture', 'command_family': family, 'command_id': key}, 'payload': payload}


def prepare(owner, scope, profile):
    content = {'sha256': hashlib.sha256(b'ABBA').hexdigest(), 'size_bytes': 4, 'media_type': profile['media_type'],
        'schema_ref': {key: profile[key] for key in ('schema_id', 'version', 'sha256')}}
    upload = owner.call('POST', '/v1/uploads', command(scope, 'artifacts.begin_upload', 'source.begin', {'content': content}))
    owner.call('PUT', '/v1/uploads/' + upload['upload_id'] + '/content', b'ABBA')
    artifact = owner.call('POST', '/v1/artifacts/finalize', command(scope, 'artifacts.finalize', 'source.finalize',
        {'upload_id': upload['upload_id'], 'content': content}))['artifact']
    rights = {'wire_version': '1', 'reference': {'scope': scope, 'rights_id': 'source', 'revision': 1},
        'supersedes': None, 'status': 'granted', 'allowed_uses': ['read', 'process'], 'expires_at': None, 'retention': 'retain_audit_payload'}
    owner.call('POST', '/v1/acquisition/rights', rights)
    source = {'wire_version': '1', 'reference': {'scope': scope, 'source_id': 'source', 'revision_id': 'r1', 'raw': artifact},
        'delivery': {'issuer_id': 'fixture', 'delivery_id': 'source-delivery'},
        'method': {'connector_id': 'fixture', 'connector_version': '1', 'configuration_sha256': hashlib.sha256(b'{}').hexdigest(),
                   'format': 'utf8_document'}, 'rights': rights['reference'], 'supersedes': None, 'completeness': 'unknown'}
    owner.call('POST', '/v1/acquisition/prepare', source)
    encoding_profile = owner.call('GET', '/v1/representations/available-profiles')[0]
    ref = owner.call('POST', '/v1/representations/profiles', encoding_profile)
    binding = owner.call('POST', '/v1/representations/encodings', {'wire_version': '1', 'encoding_id': 'encoding', 'profile': ref,
        'source': {'source': source['reference'], 'unit': 'byte', 'start': 0, 'end': 4, 'sha256': artifact['sha256']}})['outcome']['binding']
    generation = owner.call('POST', '/v1/retrieval/generations', {'wire_version': '1', 'corpus_id': 'corpus', 'generation_id': 'g1',
        'profile': binding['profile'], 'bindings': [binding['reference']], 'expected_head': None})
    assert generation['state'] == 'published'
    query = {'wire_version': '1', 'retrieval_id': 'q1', 'generation': generation['generation']['reference'], 'query': binding['reference'],
        'policy': {'format': 'data.exact-dot-ranking.v1', 'top_k': 1, 'bindings': None, 'metric': 'dot',
                   'order': 'score_desc_binding_asc', 'quality_filter': 'none'}}
    result = owner.call('POST', '/v1/retrieval/queries', query)
    assert result['matches'] == [{'binding': binding, 'score': 8.0}]
    return {'artifact': artifact, 'rights': rights, 'source': source, 'query': query, 'result': result}
