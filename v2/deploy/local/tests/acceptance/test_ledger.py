import hashlib
import json

import pytest
from amphora_deployment.acceptance import AcceptanceLedger, EvidenceError
from amphora_deployment.acceptance.policy import ASSERTIONS, GATES, LIMITATIONS, PROFILE


@pytest.fixture
def evidence_bundle(tmp_path):
    manifest = {'format': 'deployment-acceptance.v1', 'profile': PROFILE,
                'baseline': 'a' * 40, 'host': 'fixture-host', 'evidence': {},
                'limitations': list(LIMITATIONS)}
    for gate, (filename, status) in GATES.items():
        record = {'status': status}
        for path, expected in ASSERTIONS.get(gate, ()):
            target = record
            for part in path[:-1]:
                target = target.setdefault(part, {})
            target[path[-1]] = expected
        raw = json.dumps(record).encode()
        (tmp_path / filename).write_bytes(raw)
        manifest['evidence'][gate] = hashlib.sha256(raw).hexdigest()
    return tmp_path, manifest


def load(manifest):
    return AcceptanceLedger.from_bytes(json.dumps(manifest).encode())


def test_complete_inventory(evidence_bundle):
    directory, manifest = evidence_bundle
    report = load(manifest).verify(directory)
    assert report['status'] == 'verified'
    assert len(report['gates']) == 12
    assert report['services_started'] is False
    assert report['provider_calls'] == 0


@pytest.mark.parametrize('gate', list(GATES))
def test_cannot_omit_required_gate(evidence_bundle, gate):
    _, manifest = evidence_bundle
    del manifest['evidence'][gate]
    with pytest.raises(EvidenceError, match='required_gate_set_mismatch'):
        load(manifest)


@pytest.mark.parametrize('case', ['missing', 'changed', 'failed_rehashed', 'assertion_rehashed'])
def test_required_failures_are_not_optional(evidence_bundle, case):
    directory, manifest = evidence_bundle
    path = directory / 'Owner_Context_Campaign.json'
    if case == 'missing':
        path.unlink()
    elif case == 'changed':
        path.write_bytes(b'{}')
    else:
        record = json.loads(path.read_bytes())
        if case == 'failed_rehashed':
            record['status'] = 'failed'
        else:
            record['scientific']['evaluations'] = False
        raw = json.dumps(record).encode()
        path.write_bytes(raw)
        manifest['evidence']['live_context'] = hashlib.sha256(raw).hexdigest()
    report = load(manifest).verify(directory)
    assert report['status'] == 'rejected'
    row, = [row for row in report['gates'] if row['status'] == 'rejected']
    assert row['gate'] == 'live_context'


@pytest.mark.parametrize(('field', 'value', 'reason'), [
    ('format', 'future', 'unsupported_ledger'),
    ('profile', 'optional-gates', 'unsupported_ledger'),
    ('baseline', '../other', 'invalid_baseline'),
    ('host', '../private', 'invalid_host'),
    ('limitations', [], 'required_limitations_mismatch'),
    ('extra', True, 'invalid_ledger_fields'),
])
def test_strict_manifest(evidence_bundle, field, value, reason):
    _, manifest = evidence_bundle
    manifest[field] = value
    with pytest.raises(EvidenceError, match=reason):
        load(manifest)


@pytest.mark.parametrize(('raw', 'reason'), [
    (b'{"a":1,"a":2}', 'duplicate_key'),
    (b'{"a":NaN}', 'nonfinite_json'),
    (b'[]', 'object_required'),
    (b'\xff', 'invalid_json'),
    (b'{} trailing', 'invalid_json'),
])
def test_strict_json(raw, reason):
    with pytest.raises(EvidenceError, match=reason):
        AcceptanceLedger.from_bytes(raw)


def test_cli_rejection_contains_no_input_path(tmp_path, monkeypatch, capsys):
    from amphora_deployment.acceptance.__main__ import main
    monkeypatch.setattr('sys.argv', ['acceptance', '--ledger', str(tmp_path / 'secret-name'),
                                  '--evidence-directory', str(tmp_path)])
    assert main() == 2
    assert json.loads(capsys.readouterr().out) == {'status': 'rejected', 'reason': 'ledger_unavailable'}


def test_oversized_ledger():
    with pytest.raises(EvidenceError, match='document_too_large'):
        AcceptanceLedger.from_bytes(b' ' * (8 * 1024 * 1024 + 1))


def test_invalid_pin(evidence_bundle):
    _, manifest = evidence_bundle
    manifest['evidence']['host'] = '../other.json'
    with pytest.raises(EvidenceError, match='invalid_evidence_hash'):
        load(manifest)


def test_missing_model_assertion_even_when_status_passes(evidence_bundle):
    directory, manifest = evidence_bundle
    raw = b'{"status":"passed","scientific":{"successful_invocations":15,"evaluations":6}}'
    (directory / 'Owner_Context_Campaign.json').write_bytes(raw)
    manifest['evidence']['live_context'] = hashlib.sha256(raw).hexdigest()
    report = load(manifest).verify(directory)
    assert {'gate': 'live_context', 'status': 'rejected', 'reason': 'required_assertion_missing'} in report['gates']


@pytest.mark.parametrize('root_link', [True, False])
def test_link_rejected(evidence_bundle, monkeypatch, root_link):
    directory, manifest = evidence_bundle
    from pathlib import Path
    monkeypatch.setattr(Path, 'is_symlink', lambda path: path == (directory if root_link else directory / 'Selected_Local_Host.json'))
    ledger = load(manifest)
    if root_link:
        with pytest.raises(EvidenceError, match='linked_evidence'):
            ledger.verify(directory)
    else:
        assert {'gate': 'host', 'status': 'rejected', 'reason': 'linked_evidence'} in ledger.verify(directory)['gates']


def test_cli_success(evidence_bundle, monkeypatch, capsys):
    from amphora_deployment.acceptance.__main__ import main
    directory, manifest = evidence_bundle
    ledger = directory / 'ledger.json'
    ledger.write_text(json.dumps(manifest))
    monkeypatch.setattr('sys.argv', ['acceptance', '--ledger', str(ledger), '--evidence-directory', str(directory)])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'verified'
