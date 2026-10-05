"""Actual root bodies and acquisition provenance through public Data routes."""

import hashlib

from amphora_agent_planning.campaign_packet_profiles import reviewed_instructions

from campaign_context_fixture.data import command


def text_profile():
    return {'media_type': 'text/plain', 'schema_id': 'fixture.text', 'version': '1',
            'sha256': hashlib.sha256(b'{"type":"string"}').hexdigest()}


def roots(owner, scope):
    profile = text_profile()
    rights = {'wire_version': '1', 'reference': {'scope': scope, 'rights_id': 'packet-roots', 'revision': 1},
        'supersedes': None, 'status': 'granted', 'allowed_uses': ['read', 'process'], 'expires_at': None, 'retention': 'retain_audit_payload'}
    owner.call('POST', '/v1/acquisition/rights', rights)
    result = {}
    for name, body in (('objective', b'Explore synthetic evidence; preserve unknown and conflicting findings.'),
                       ('policy', b'Synthetic demonstration only; no scientific authority.'),
                       ('configuration', b'{"fixture":"deterministic"}'), ('prompt', reviewed_instructions())):
        content = {'sha256': hashlib.sha256(body).hexdigest(), 'size_bytes': len(body), 'media_type': 'text/plain',
                   'schema_ref': {key: profile[key] for key in ('schema_id', 'version', 'sha256')}}
        upload = owner.call('POST', '/v1/uploads', command(scope, 'artifacts.begin_upload', name + '.begin', {'content': content}))
        owner.call('PUT', '/v1/uploads/' + upload['upload_id'] + '/content', body)
        artifact = owner.call('POST', '/v1/artifacts/finalize', command(scope, 'artifacts.finalize', name + '.finalize',
            {'upload_id': upload['upload_id'], 'content': content}))['artifact']
        source = {'wire_version': '1', 'reference': {'scope': scope, 'source_id': 'root-' + name, 'revision_id': 'r1', 'raw': artifact},
            'delivery': {'issuer_id': 'fixture', 'delivery_id': 'root-' + name},
            'method': {'connector_id': 'fixture', 'connector_version': '1', 'configuration_sha256': hashlib.sha256(b'{}').hexdigest(),
                       'format': 'utf8_document'}, 'rights': rights['reference'], 'supersedes': None, 'completeness': 'unknown'}
        owner.call('POST', '/v1/acquisition/prepare', source)
        result[name] = artifact
    return result
