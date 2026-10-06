"""Image closure matching and actual Registry API; capacity is synthetic metadata."""
import json
from pathlib import Path


class ImageCatalog:
    def __init__(self, config):
        self.entries, self.profiles, self.registrations, self.selections = {}, {}, [], []
        if config.get('images'):
            manifest = json.loads(Path(config['images']).read_bytes())
            assert manifest['profile'] == 'representation-images-v1' and manifest['golden']
            for image in manifest['tools']:
                kind = 'digest' if image['module'] == 'amphora_synthetic_digest' else image['module'].split('_')[1]
                assert kind not in self.entries
                self.entries[kind] = image
            assert set(self.entries) == {'numeric', 'polymer', 'sequence', 'digest'}

    def digest(self, kind):
        return self.entries[kind]['image_manifest_digest'].removeprefix('sha256:') if self.entries else 'c' * 64

    def verify(self, kind, descriptor, packages, operation=None):
        if self.entries:
            operation = operation or ('evaluate' if kind == 'digest' else 'canonicalize')
            assert descriptor == self.entries[kind]['descriptors'][operation]
            assert packages[kind]['wheels'] == self.entries[kind]['local_wheels'], 'Image/installed wheel closure mismatch'

    def register(self, e):
        if not self.entries:
            return
        e.registry = e.host('registry', 'amphora_capability_registry', {
            'database_url_env': 'DATABASE_URL',
            'principals': [e.principal('admin', ['register', 'activate', 'deploy', 'read', 'resolve']), e.principal('worker1', ['heartbeat'])],
            'resources': {'architecture': 'x86_64', 'operating_system': 'linux', 'cpu_millicores': 4000,
                'memory_mib': 4096, 'gpu_count': 0, 'timeout_seconds': 300, 'max_parallel_invocations': 8, 'max_batch_size': 128}},
            'AMPHORA_REGISTRY_DATABASE_URL')
        for kind, image in self.entries.items():
            for operation, descriptor in image['descriptors'].items():
                actual = json.loads(e.cli(kind, 'describe', '--image-sha256', self.digest(kind), operation=operation))
                self.verify(kind, actual, e.config['packages'], operation)
                lock = self.lock(descriptor)
                registered = e.registry_call('register', {'scope': e.scope, 'descriptor': descriptor, 'expected_lock': lock})
                assert registered['reason_code'] == 'registered' and registered['release']['lock'] == lock
                activated = e.registry_call('activate', {'release': lock, 'expected_revision': 1})
                assert activated['status'] == 'accepted' and activated['release']['status'] == 'active'
                deployment = 'fixture-' + kind + '-' + operation
                deployed = e.registry_call('deploy', {'deployment_id': deployment, 'release': lock,
                    'architecture': 'x86_64', 'operating_system': 'linux', 'workers': ['worker1']})
                assert deployed['status'] == 'accepted'
                self.profiles[(kind, operation)] = {'lock': lock, 'descriptor': descriptor, 'deployment': deployment, 'revision': 0}
                self.registrations.append({'kind': kind, 'operation': operation, 'registered': registered, 'activated': activated, 'deployed': deployed})
                self.select(e, kind, operation)
        assert len(self.profiles) == 7

    @staticmethod
    def lock(descriptor):
        import importlib.util
        path = Path(__file__).absolute().parents[5] / 'tests/integration/tool_replicas/wire.py'
        spec = importlib.util.spec_from_file_location('reuse_public_wire', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.release_lock(descriptor)

    def select(self, e, kind, operation=None):
        if not self.entries:
            return
        operation = operation or ('evaluate' if kind == 'digest' else 'canonicalize')
        profile = self.profiles[(kind, operation)]
        heartbeat = e.registry_call('heartbeat', {'deployment_id': profile['deployment'], 'replica_id': profile['deployment'] + '-worker1',
            'expected_revision': profile['revision'], 'free_slots': 1, 'ttl_seconds': 60}, 'worker1')
        assert heartbeat['status'] == 'accepted'
        profile['revision'] = heartbeat['heartbeat']['revision']
        tool = profile['descriptor']['tool']
        selected = e.registry_call('resolve', {'release': profile['lock'], 'context': 'synthetic-tests', 'inputs': tool['inputs'], 'outputs': tool['outputs']})
        assert selected['decision']['status'] == 'candidate', selected
        self.selections.append({'kind': kind, 'operation': operation, 'heartbeat': heartbeat, 'selected': selected})
