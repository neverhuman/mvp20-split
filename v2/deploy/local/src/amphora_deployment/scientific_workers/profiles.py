"""Closed synthetic Linux tool recipes and exact SDK configuration identities."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ..installation.inventory import digest
from ..profile import fields, label, require

PROFILES = {**{'evolution-' + operation: ('amphora_evolution_search', ('worker', '--operation', operation))
               for operation in ('seed', 'requests', 'collect', 'vary')},
            'synthetic-objectives': ('amphora_synthetic_objectives', ('worker',)),
            'synthetic-objectives-rebuilt': ('amphora_synthetic_objectives_rebuilt', ('worker',))}


def content(path, maximum):
    with Path(path).open('rb') as stream:
        raw = stream.read(maximum + 1)
    require(0 < len(raw) <= maximum, 'container_configuration_size')
    return raw


@dataclass(frozen=True)
class ToolProfile:
    name: str
    image_id: str
    configuration: Path
    certificate: Path
    configuration_sha256: str
    certificate_sha256: str

    @classmethod
    def pin(cls, name, image_id, configuration, certificate, runtime_port, artifact_port):
        require(name in PROFILES, 'container_tool_profile')
        require(type(image_id) is str and image_id.startswith('sha256:'), 'container_image_id')
        digest(image_id[7:], 'container_image_digest')
        configuration, certificate = Path(configuration), Path(certificate)
        require(configuration.is_absolute() and certificate.is_absolute(), 'container_absolute_paths')
        raw, trust = content(configuration, 65536), content(certificate, 16384)
        config = json.loads(raw)
        required = {'actor_id', 'scope', 'run_id', 'image_sha256', 'runtime', 'artifacts'}
        require(type(config) is dict and required <= set(config) and
                set(config) <= required | {'lease_seconds', 'max_clock_skew_seconds'}, 'container_sdk_configuration')
        label(config['actor_id'], 'container_actor')
        label(config['run_id'], 'container_run')
        scope = fields(config['scope'], 'tenant_id project_id', 'container_scope')
        for value in scope.values():
            label(value, 'container_scope_identity')
        require(config['image_sha256'] == image_id[7:], 'container_configuration_image')
        for key, port, token in (('runtime', runtime_port, 'AMPHORA_RUNTIME_TOKEN'),
                                 ('artifacts', artifact_port, 'AMPHORA_ARTIFACT_TOKEN')):
            require(type(port) is int and 1024 <= port <= 65535, 'container_tls_port')
            peer = fields(config[key], 'endpoint token_env', 'container_peer')
            require(peer == {'endpoint': 'https://host.docker.internal:' + str(port), 'token_env': token},
                    'container_peer_binding')
        lease, skew = config.get('lease_seconds', 30), config.get('max_clock_skew_seconds', 1)
        require(type(lease) is int and 10 <= lease <= 300 and type(skew) in {int, float} and 0 <= skew <= 5,
                'container_lease_policy')
        return cls(name, image_id, configuration, certificate, hashlib.sha256(raw).hexdigest(), hashlib.sha256(trust).hexdigest())

    def verify(self):
        require(hashlib.sha256(content(self.configuration, 65536)).hexdigest() == self.configuration_sha256 and
                hashlib.sha256(content(self.certificate, 16384)).hexdigest() == self.certificate_sha256,
                'container_configuration_changed')

    @property
    def fingerprint(self):
        values = [self.name, self.image_id, str(self.configuration), str(self.certificate),
                  self.configuration_sha256, self.certificate_sha256]
        return hashlib.sha256(json.dumps(values, separators=(',', ':')).encode()).hexdigest()

    @property
    def entrypoint(self):
        return ('python', '-m', PROFILES[self.name][0])

    @property
    def arguments(self):
        return PROFILES[self.name][1] + ('--config', '/amphora/worker.json')
