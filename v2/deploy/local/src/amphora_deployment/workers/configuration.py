"""Explicit native worker sidecar; owner schemas remain validated by owner CLIs."""

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from ..profile import fields, require
from .recipes import NATIVE_RECIPES, WorkerScope


def read(path, maximum=65536):
    with Path(path).open('rb') as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, 'worker_configuration_size')
    return raw


@dataclass(frozen=True)
class ConfigurationPins:
    files: tuple

    @classmethod
    def bind(cls, name, path):
        path = Path(path)
        raw = read(path)
        record = json.loads(raw)
        require(type(record) is dict, 'worker_configuration_shape')
        references = []
        if name == 'planning-checkpoint':
            references += [entry['path'] for entry in record.get('templates', [])]
        elif name in {'runtime-coordinate', 'runtime-deliver'}:
            for graph in record.get('graphs', []):
                references += [graph['definition']]
                references += [entry['descriptor'] for entry in graph['releases']]
                references += [entry['path'] for entry in graph['schemas']]
            for kind in ('policies', 'recipes'):
                references += record.get('supervision_admission', {}).get(kind, [])
        require(len(references) <= 512, 'worker_configuration_references')
        pins = [(path, hashlib.sha256(raw).hexdigest())]
        total = len(raw)
        for reference in references:
            require(type(reference) is str and bool(reference) and not Path(reference).is_absolute()
                    and not Path(reference).anchor and '..' not in Path(reference).parts,
                    'worker_configuration_reference_path')
            target = path.parent / reference
            content = read(target, 1048576)
            total += len(content)
            require(total <= 16777216, 'worker_configuration_total_size')
            pins.append((target, hashlib.sha256(content).hexdigest()))
        return cls(tuple(pins))

    def verify(self):
        for path, expected in self.files:
            require(hashlib.sha256(read(path, 1048576)).hexdigest() == expected,
                    'worker_configuration_changed')


def load_workers(path, owners):
    # Import here keeps the pin object independent of the process implementation.
    from .native import NativeBinding

    record = fields(json.loads(read(path)), 'profile workers', 'worker_manifest')
    require(record['profile'] == 'local-native-workers-v1', 'worker_manifest_profile')
    workers = record['workers']
    require(type(workers) is dict and bool(workers) and set(workers) <= set(NATIVE_RECIPES), 'worker_manifest_names')
    result = {}
    for name, entry in workers.items():
        fields(entry, 'configuration source_lock scope', 'worker_binding')
        owner = NATIVE_RECIPES[name].owner
        require(owner in owners, 'worker_serving_owner_required')
        serving = owners[owner]
        scope = None
        if entry['scope'] is not None:
            selected = fields(entry['scope'], 'actor tenant project', 'worker_scope')
            scope = WorkerScope(**selected)
        environment = dict(serving.environment)
        if name == 'planning-checkpoint':
            settings = json.loads(read(entry['configuration']))
            if settings.get('provider') == 'openai_checkpoint_v1':
                live = settings.get('live', {})
                require(live.get('key_env') == 'AMPHORA_OPENAI_API_KEY' and
                        live.get('egress') == 'approved_synthetic_engineering_only', 'worker_live_policy')
                key = os.environ.get('AMPHORA_OPENAI_API_KEY')
                require(type(key) is str and bool(key), 'worker_live_key_missing')
                environment['AMPHORA_OPENAI_API_KEY'] = key
        binding = NativeBinding.pin(name, serving.directory, entry['source_lock'],
                                    entry['configuration'], environment, scope)
        require(binding.installation == serving.installation, 'worker_serving_installation_mismatch')
        result[name] = binding
    return result
