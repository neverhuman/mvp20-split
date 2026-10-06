import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from amphora_synthetic_digest.capability import DigestCapability

from ..kernel.test_evaluation import declaration


def test_descriptor_and_schemas_are_exact_published_contracts():
    capability = DigestCapability()
    root = Path(__file__).absolute().parents[4]
    descriptor = capability.descriptor('d' * 64)
    assert descriptor.authority_ceiling == 'synthetic_only'
    assert descriptor.tool.binding.capability_id == 'synthetic.digest-score'
    for direction in ('input', 'output'):
        raw = capability.schema_bytes(direction)
        assert raw == (root / 'contracts/schemas/v1' / (capability.schema_name(direction) + '.validation.json')).read_bytes()
        assert capability.schema_ref(direction).sha256 == hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError):
        capability.schema_bytes('unknown')


def test_cli_compute_discovery_and_safe_rejection():
    adapter, body = declaration()
    command = [sys.executable, '-m', 'amphora_synthetic_digest']
    raw = json.dumps(body).encode()
    result = subprocess.run(command + ['compute', '--image-sha256', 'd' * 64], input=raw, capture_output=True, timeout=20)
    assert result.returncode == 0 and result.stdout == adapter.execute(raw)
    for args in (['describe', '--image-sha256', 'd' * 64], ['schema', '--direction', 'input'], ['profiles']):
        result = subprocess.run(command + args, capture_output=True, timeout=20)
        assert result.returncode == 0
        assert isinstance(json.loads(result.stdout), dict)
    result = subprocess.run(command + ['compute', '--image-sha256', 'd' * 64], input=b'{"secret":"bad"}', capture_output=True, timeout=20)
    assert result.returncode == 2 and b'secret' not in result.stderr
