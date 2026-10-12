"""Publish synthetic fixture bytes and explicit processing rights through Data."""
import hashlib
import uuid


class Publication:
    def __init__(self, api, scope):
        self.api, self.scope, self.tag = api, scope, uuid.uuid4().hex
        self.rights = {'scope': scope, 'rights_id': 'curation-fixture-' + self.tag, 'revision': 1}
        api.call('artifact', '/v1/acquisition/rights', {'wire_version': '1', 'reference': self.rights,
            'supersedes': None, 'status': 'granted', 'allowed_uses': ['read', 'process'],
            'expires_at': None, 'retention': 'retain_audit_payload'})

    def command(self, family, payload):
        return {'identity': {'scope': self.scope, 'actor_id': 'admin', 'command_id': uuid.uuid4().hex,
            'command_family': family}, 'payload': payload}

    def publish(self, body, schema, *, media_type='text/plain'):
        content = {'sha256': hashlib.sha256(body).hexdigest(), 'size_bytes': len(body),
                   'media_type': media_type, 'schema_ref': schema}
        upload = self.api.call('artifact', '/v1/uploads', self.command('artifacts.begin_upload', {'content': content}))
        self.api.call('artifact', '/v1/uploads/' + upload['upload_id'] + '/content', body, method='PUT')
        ref = self.api.call('artifact', '/v1/artifacts/finalize', self.command('artifacts.finalize',
            {'upload_id': upload['upload_id'], 'content': content}))['artifact']
        self.api.call('artifact', '/v1/acquisition/prepare', {'wire_version': '1',
            'reference': {'scope': self.scope, 'source_id': 'curation-' + self.tag + '-' + ref['artifact_id'],
                          'revision_id': 'r1', 'raw': ref},
            'delivery': {'issuer_id': 'curation-synthetic-fixture', 'delivery_id': self.tag + '-' + ref['artifact_id']},
            'method': {'connector_id': 'synthetic-engineering', 'connector_version': '1',
                'configuration_sha256': hashlib.sha256(b'{}').hexdigest(), 'format': 'utf8_document'},
            'rights': self.rights, 'supersedes': None, 'completeness': 'unknown'})
        return ref
