"""Explicit verified wheel environments for test-only owner replacement."""

import hashlib
import json
import os
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path


@dataclass(frozen=True)
class Installations:
    supervisors: Path
    data: Path
    supervisor_manifest_sha256: str
    data_manifest_sha256: str

    @classmethod
    def configured(cls):
        path = os.environ.get('AMPHORA_TEST_SUPERVISOR_INSTALLATIONS')
        if path is None:
            return None
        supervisors = Path(path).absolute()
        data = Path(os.environ['AMPHORA_TEST_DATA_INSTALLATION']).absolute()
        raw, data_raw = (supervisors / 'manifest.json').read_bytes(), (data / 'manifest.json').read_bytes()
        proof, data_proof = json.loads(raw), json.loads(data_raw)
        assert proof['status'] == 'passed' and data_proof['status'] == 'installed'
        assert len(proof['schema_pins']) == 548 and proof['unchanged_predecessor_schemas'] == 546
        for owner, package in [('runtime', 'amphora-campaign-runtime'), ('planning', 'amphora-agent-planning')]:
            assert proof['owners'][owner]['version'] == version(package)
        assert data_proof['packages']['amphora-data-artifacts'] == version('amphora-data-artifacts')
        return cls(supervisors, data, hashlib.sha256(raw).hexdigest(), hashlib.sha256(data_raw).hexdigest())

    def python(self, module, label):
        assert label in {'initial', 'replacement'}
        if module == 'amphora_data_artifacts':
            result = self.data / 'environment/Scripts/python.exe'
        else:
            owner = next(owner for owner, prefix in [('runtime', 'amphora_campaign_runtime'),
                ('planning', 'amphora_agent_planning')] if module == prefix or module.startswith(prefix + '.'))
            result = self.supervisors / owner / label / 'Scripts/python.exe'
        assert result.is_file()
        return result
