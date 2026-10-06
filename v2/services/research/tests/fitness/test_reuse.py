import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_evaluation_identity import EvaluationIdentityInput
from amphora_research.fitness import EvaluationKey, EvaluationIdentityError


def fixture():
    return json.loads((Path(__file__).parent / 'fixtures/input.json').read_bytes())


def key(value):
    return EvaluationKey(EvaluationIdentityInput.model_validate_json(json.dumps(value)))


def changed(value, path, replacement):
    result = copy.deepcopy(value)
    node = result
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = replacement
    return result


@pytest.mark.parametrize('path,value', [
    (('representation','canonical_sha256'), 'e'*64),
    (('policy','purpose'), 'other-purpose'),
    (('policy','reference','sha256'), 'e'*64),
    (('policy','method','evaluator','image_sha256'), 'e'*64),
    (('policy','method','evaluator','release'), '0.2.0'),
    (('policy','method','method','sha256'), 'e'*64),
    (('policy','method','applicability','sha256'), 'e'*64),
    (('policy','synthesis_policy','sha256'), 'e'*64),
    (('policy','objectives',0,'unit'), 'mg'),
    (('policy','objectives',0,'direction'), 'maximize'),
    (('policy','objectives',0,'uncertainty_policy','sha256'), 'e'*64),
    (('context','material_state','revision'), 2),
    (('context','inputs',0,'artifact','sha256'), 'e'*64),
    (('context','inputs',1,'artifact','sha256'), 'e'*64),
])
def test_context_and_method_changes_never_share_identity(path, value):
    original = fixture()
    assert not key(original).same_declared_identity(key(changed(original, path, value)))


@pytest.mark.parametrize('field', ['semantic_profile', 'equivalence_profile'])
def test_representation_policy_pins_bind_identity(field):
    original = fixture()
    other = copy.deepcopy(original)
    for policy in [other['representation']['policy'], other['policy']['representation']]:
        policy[field]['sha256'] = 'e'*64
    assert key(original).to_wire().sha256 != key(other).to_wire().sha256


def test_named_context_order_is_irrelevant_but_objective_order_is_not():
    original = fixture()
    other = copy.deepcopy(original)
    other['context']['inputs'].reverse()
    other['policy']['required_context'].reverse()
    assert key(original).same_declared_identity(key(other))
    original['policy']['objectives'].append(dict(original['policy']['objectives'][0], objective_id='second'))
    other = copy.deepcopy(original)
    other['policy']['objectives'].reverse()
    assert not key(original).same_declared_identity(key(other))


def test_equivalent_source_claim_preserves_distinct_provenance_without_authority():
    original = fixture()
    other = copy.deepcopy(original)
    other['representation']['source'].update(artifact_id='other-encoding', sha256='e'*64, size_bytes=150)
    first, second = key(original), key(other)
    assert first.same_declared_identity(second)
    assert first.to_wire().source != second.to_wire().source
    assert first.to_wire().authority == 'identity_only'
    assert first.to_wire().sha256 == hashlib.sha256(first.bytes).hexdigest()


@pytest.mark.parametrize('path,value,error', [
    (('representation','scope','project_id'), 'foreign', 'scope_mismatch'),
    (('representation','source','scope','project_id'), 'foreign', 'scope_mismatch'),
    (('representation','policy','semantic_profile','sha256'), 'e'*64, 'policy_mismatch'),
    (('representation','source','media_type'), 'text/plain', 'encoding_mismatch'),
    (('representation','source','schema_ref','sha256'), 'e'*64, 'encoding_mismatch'),
    (('context','material_state','scope','project_id'), 'foreign', 'material_scope_mismatch'),
    (('context','material_state'), None, 'material_state_required'),
    (('policy','objectives',0,'unit'), '  ', 'objectives_invalid'),
    (('policy','required_context'), ['preparation','preparation'], 'context_incomplete'),
    (('context','inputs',0,'name'), 'distribution', 'context_incomplete'),
    (('context','inputs'), [], 'context_incomplete'),
    (('context','inputs',0,'artifact','scope','project_id'), 'foreign', 'context_scope_mismatch'),
])
def test_rejects_incomplete_or_inconsistent_claims(path, value, error):
    with pytest.raises(EvaluationIdentityError, match=error):
        key(changed(fixture(), path, value))


def test_duplicate_objective_and_conflicting_artifact_identity_reject():
    value = fixture()
    value['policy']['objectives'] *= 2
    with pytest.raises(EvaluationIdentityError, match='objectives_invalid'):
        key(value)
    value = fixture()
    value['context']['inputs'][1]['artifact'] = copy.deepcopy(value['context']['inputs'][0]['artifact'])
    key(value)  # Same Artifact may fulfill two explicitly named roles.
    value['context']['inputs'][1]['artifact']['sha256'] = 'e'*64
    with pytest.raises(EvaluationIdentityError, match='identity_conflict'):
        key(value)


def test_material_unknown_is_only_allowed_by_explicit_policy():
    value = fixture()
    value['policy']['material_state_required'] = False
    known = key(value)
    value['context']['material_state'] = None
    assert not known.same_declared_identity(key(value))


def test_revalidates_unchecked_model_copy():
    model = EvaluationIdentityInput.model_validate_json(json.dumps(fixture()))
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        EvaluationKey(model.model_copy(update={'wire_version':'unsupported'}))
