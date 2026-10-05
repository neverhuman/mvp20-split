import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from amphora_agent_planning.campaign_packet import prepare, reconstruct

from .replay_probe import check, source
from .test_assembly import plan

FIXTURE = Path(__file__).parent / 'fixtures/predecessor-v1.json'


def test_fixed_predecessor_bytes_fit_and_observations_reconstruct_in_fresh_process():
    expected = check(FIXTURE)
    assert expected == {'packet_sha256': 'f137c66a058fa7e53a019534b804438c10f27be6b1bc0ca22ef8a3826b3c96b2',
        'plan_sha256': '3a917e2593f7303e114b03e47b3ce93b8fabe674ecf83facc95856489292ede3',
        'bytes': 13108, 'input_tokens': 13108, 'output_reserve': 16}
    environment = {key: value for key, value in os.environ.items() if not key.startswith('AMPHORA_') and key != 'PYTHONPATH'}
    result = subprocess.run([sys.executable, '-I', str(Path(__file__).parent / 'replay_probe.py'), str(FIXTURE)],
        capture_output=True, text=True, timeout=30, env=environment, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == expected


@pytest.mark.parametrize('fault', ['plan', 'digest', 'bytes', 'empty', 'nonbytes', 'oversized'])
def test_replay_rejects_wrong_identity_noncanonical_bytes_and_limits(fault):
    value = json.loads(FIXTURE.read_bytes())
    original = source(value)
    raw = base64.b64decode(value['packet_base64'])
    plan_hash, packet_hash = value['plan_sha256'], value['packet_sha256']
    if fault == 'plan':
        plan_hash = '0' * 64
    elif fault == 'digest':
        packet_hash = '0' * 64
    elif fault == 'bytes':
        raw += b'\n'
        packet_hash = hashlib.sha256(raw).hexdigest()
    elif fault == 'empty':
        raw = b''
    elif fault == 'nonbytes':
        raw = 'not bytes'
    else:
        raw = b'x' * 8388609
    with pytest.raises(ValueError, match='campaign_packet_replay_'):
        reconstruct(original, raw, plan_sha256=plan_hash, packet_sha256=packet_hash)


def test_unavailable_original_plan_cannot_reconstruct_a_successful_packet():
    original = plan(missing=True)
    with pytest.raises(ValueError, match='replay_unavailable'):
        reconstruct(original, b'{}', plan_sha256=original.sha256, packet_sha256=hashlib.sha256(b'{}').hexdigest())


def test_all_132_manifest_identities_can_be_included_with_complete_observation_coverage():
    original = plan(maximum=2000000, extras=tuple((f'entry-{i}', b'uncertain', False) for i in range(128)))
    packet = prepare(original).packet
    value = json.loads(packet.canonical)['untrusted_context']
    assert len(value['slices']) == len(value['consumed_observations']) == 132
    assert not value['budget_omissions'] and packet.fit.fits
    assert reconstruct(original, packet.canonical, plan_sha256=original.sha256, packet_sha256=packet.sha256) == packet


def test_exact_input_limit_boundary_does_not_borrow_reserved_output():
    # Limits are serialized too: first stabilize their decimal width, then pin equality.
    maximum = 20000
    for _ in range(4):
        original = plan(maximum=maximum)
        packet = prepare(original).packet
        assert packet is not None
        measured = len(packet.canonical)
        if measured == maximum:
            break
        maximum = measured
    assert packet.fit.measurement.input_tokens == maximum
    assert packet.fit.document()['output_reserve'] == 16
    below = prepare(plan(maximum=maximum - 1))
    assert below.packet is None and below.failure == 'required_input_limit'
