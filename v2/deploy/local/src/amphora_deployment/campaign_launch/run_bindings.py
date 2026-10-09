"""Immutable per-launch files derived exclusively from installed tool templates."""
import json
import os
import uuid
from pathlib import Path

from ..scientific_workers.configuration import ScientificBinding
from ..scientific_workers.profiles import ToolProfile, content
from .intent import LaunchError


def canonical_record(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def retain_exact(path: Path, raw: bytes):
    """Installation lease serializes writers; replay must match every retained byte."""
    if path.exists():
        with path.open('rb') as stream:
            retained = stream.read(len(raw) + 1)
        if retained != raw:
            raise LaunchError('launch_worker_binding_changed')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.launch-' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class RunBindingStore:
    def __init__(self, root, deployment_id, templates, *, runtime_port, artifact_port):
        self.root, self.deployment_id = Path(root), deployment_id
        self.templates = dict(templates)
        self.runtime_port, self.artifact_port = runtime_port, artifact_port
        if not self.root.is_absolute() or not self.templates:
            raise LaunchError('launch_worker_templates_invalid')

    def directory(self, state):
        return self.root / 'campaign-launches' / state.intent.request.sha256

    def prepare(self, state):
        if state.run_id is None:
            raise LaunchError('launch_admission_required')
        directory = self.directory(state)
        scope = state.intent.request.identity.scope.model_dump(mode='json')
        bindings = {}
        entries = {}
        for name, template in sorted(self.templates.items()):
            template.profile.verify()
            configuration = json.loads(content(template.profile.configuration, 65536))
            if configuration['scope'] != scope or template.profile.name != name:
                raise LaunchError('launch_worker_scope_mismatch')
            configuration['run_id'] = state.run_id
            path = directory / (name + '.json')
            retain_exact(path, canonical_record(configuration))
            profile = ToolProfile.pin(name, template.profile.image_id, path, template.profile.certificate,
                                      self.runtime_port, self.artifact_port)
            bindings[name] = ScientificBinding.pin(self.root, self.deployment_id, profile,
                                                   dict(template.environment))
            entries[name] = {'binding_sha256': profile.fingerprint,
                'configuration_sha256': profile.configuration_sha256,
                'image_id': profile.image_id, 'certificate_sha256': profile.certificate_sha256}
        # Receipt identity precedes binding files; this final manifest precedes
        # adopting/engaging any worker. No credential is persisted here.
        retain_exact(directory / 'bindings.json', canonical_record({
            'profile': 'local-campaign-bindings-v1', 'request_sha256': state.intent.request.sha256,
            'launch_profile': state.intent.profile.model_dump(mode='json'),
            'run_id': state.run_id, 'scope': scope, 'workers': entries}))
        return bindings
