import json
import pytest
from curation_isolation.probe import body_for, prune, reserve, strip, MAX_CALLS


def test_prune_keeps_recursive_reachable_definitions_only():
    schema = {'$ref': '#/$defs/a', '$defs': {'a': {'$ref': '#/$defs/a'}, 'unused': {'type': 'string'}}}
    assert set(prune(schema)['$defs']) == {'a'}
    assert 'unused' in schema['$defs']


def test_strip_preserves_structure_without_mutating_original():
    schema = {'type': 'string', 'pattern': '^a$', 'minLength': 1}
    assert strip(schema, {'pattern'}) == {'type': 'string', 'minLength': 1}
    assert 'pattern' in schema


def test_strip_never_removes_fields_named_like_keywords():
    schema = {'type': 'object', 'properties': {'minimum': {'type': 'integer', 'minimum': 0}},
              'required': ['minimum'], 'additionalProperties': False}
    result = strip(schema, {'minimum'})
    assert result['properties'] == {'minimum': {'type': 'integer'}}
    assert result['required'] == ['minimum']


def test_reservations_never_reuse_or_exceed_bound(tmp_path):
    for index in range(MAX_CALLS): reserve(tmp_path, str(index), b'{}')
    with pytest.raises(AssertionError, match='isolation_allowance_exhausted'):
        reserve(tmp_path, 'overflow', b'{}')
    assert len(list(tmp_path.glob('*/reservation.json'))) == MAX_CALLS


def test_oversized_body_rejects_before_provider():
    with pytest.raises(AssertionError): body_for({'type': 'string', 'description': 'x' * 33000})
