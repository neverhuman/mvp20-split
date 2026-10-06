import hashlib
import json
from pathlib import Path

import pytest
from amphora_synthetic_digest.adapter import DigestWorkerAdapter
from amphora_synthetic_digest.domain import DigestEvaluation
from amphora_synthetic_digest.profile import APPLICABILITY, METHOD, UNCERTAINTY
from amphora_tool_protocol import ToolInputRejected


def declaration():
    body = json.loads((Path(__file__).parent / 'input.json').read_bytes())
    adapter = DigestWorkerAdapter()
    binding = adapter.descriptor('d' * 64).tool.binding
    policy = body['policy']
    policy['purpose'] = 'synthetic-cache-qualification'
    policy['method'] = {'evaluator': binding.model_dump(mode='json'),
                        'method': METHOD.model_dump(mode='json'),
                        'applicability': APPLICABILITY.model_dump(mode='json')}
    policy['objectives'] = [{'objective_id': 'synthetic-digest-score', 'unit': '1',
        'direction': 'minimize', 'uncertainty_policy': UNCERTAINTY.model_dump(mode='json')}]
    return adapter, body


@pytest.mark.parametrize('prefix,expected', [('000000', 0), ('000001', 1), ('123456', 1193046), ('ffffff', 16777215)])
def test_independently_calculated_vectors_and_exact_input_provenance(prefix, expected):
    adapter, body = declaration()
    body['representation']['canonical_sha256'] = prefix + '0' * 58
    raw = json.dumps(body).encode()
    result = json.loads(adapter.execute(raw))
    assert result['value'] == expected
    assert result['authority'] == 'synthetic_evaluation'
    assert result['input_sha256'] == hashlib.sha256(raw).hexdigest()
    assert result['method'] == body['policy']['method']
    assert adapter.execute(raw) == adapter.execute(raw)
    spaced = json.dumps(body, indent=2).encode()
    assert json.loads(adapter.execute(spaced))['value'] == expected
    assert json.loads(adapter.execute(spaced))['input_sha256'] != result['input_sha256']


@pytest.mark.parametrize('path,value', [
    ('policy.purpose', 'science'),
    ('policy.method.evaluator.release', '0.2.0'),
    ('policy.method.method.sha256', '0' * 64),
    ('policy.method.applicability.sha256', '0' * 64),
    ('policy.objectives.0.objective_id', 'fitness'),
    ('policy.objectives.0.unit', 'kg'),
    ('policy.objectives.0.direction', 'maximize'),
    ('policy.objectives.0.uncertainty_policy.sha256', '0' * 64),
    ('representation.scope.project_id', 'other'),
    ('representation.source.scope.project_id', 'other'),
    ('representation.policy.kind', 'numeric'),
    ('context.material_state.scope.project_id', 'other'),
    ('context.inputs.0.artifact.scope.project_id', 'other'),
    ('context.material_state', None),
    ('context.inputs', []),
    ('policy.required_context', ['preparation', 'preparation']),
], ids=['purpose','release','method','applicability','objective','unit','direction','uncertainty',
         'scope','source-scope','representation','state-scope','context-scope','missing-state','missing-context','duplicate-required'])
def test_foreign_method_or_incoherent_context_is_rejected(path, value):
    adapter, body = declaration()
    steps = path.split('.')
    cursor = body
    for step in steps[:-1]:
        cursor = cursor[int(step)] if isinstance(cursor, list) else cursor[step]
    cursor[steps[-1]] = value
    with pytest.raises(ToolInputRejected, match='invalid_synthetic_digest_input'):
        adapter.execute(json.dumps(body).encode())


def test_multiple_objectives_and_duplicate_context_are_not_silently_collapsed():
    adapter, body = declaration()
    body['policy']['objectives'] *= 2
    with pytest.raises(ToolInputRejected):
        adapter.execute(json.dumps(body).encode())
    adapter, body = declaration()
    body['context']['inputs'].append(body['context']['inputs'][0])
    with pytest.raises(ToolInputRejected):
        adapter.execute(json.dumps(body).encode())


def test_equal_score_does_not_establish_equivalent_context():
    adapter, body = declaration()
    original = json.loads(adapter.execute(json.dumps(body).encode()))
    body['context']['inputs'][0]['artifact']['sha256'] = 'e' * 64
    changed = json.loads(adapter.execute(json.dumps(body).encode()))
    assert original['value'] == changed['value']
    assert original['input_sha256'] != changed['input_sha256']
    body['policy']['material_state_required'] = False
    body['context']['material_state'] = None
    assert json.loads(adapter.execute(json.dumps(body).encode()))['value'] == original['value']


@pytest.mark.parametrize('payload', [b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'[]',
    b' ' * 262145, b'[' * 2000, 'not bytes', b'{}'],
    ids=['duplicate','nonfinite','utf8','shape','capacity','deep','type','missing'])
def test_malformed_payloads_have_bounded_safe_failures(payload):
    adapter, _ = declaration()
    with pytest.raises(ToolInputRejected, match='invalid_synthetic_digest_input'):
        adapter.execute(payload)


def test_adapter_requires_binding_and_cannot_change_it():
    adapter = DigestWorkerAdapter()
    with pytest.raises(ToolInputRejected):
        adapter.execute(b'{}')
    original = adapter.descriptor('d' * 64)
    assert adapter.descriptor('d' * 64) == original
    with pytest.raises(ValueError, match='worker_image_changed'):
        adapter.descriptor('e' * 64)
