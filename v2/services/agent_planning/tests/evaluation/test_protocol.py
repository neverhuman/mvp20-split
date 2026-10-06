"""Literal independently authored rubric; no provider-generated expected results."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.evaluation import EvaluationProtocol, EvaluationScorer
from amphora_agent_planning.evaluation.protocol import document, pointer_parts
from amphora_agent_planning.evaluation.records import ObservationRecord


def inputs():
    context = json.loads((Path(__file__).parents[1] / 'providers/fixtures/request.json').read_text())['context']
    corpus = {'schema_version': '1', 'cases': [{'case_id': 'inhibition', 'category': 'grounding',
        'input_sha256': 'a' * 64, 'allow_abstention': False, 'hard_authority': False, 'assertions': [
            {'assertion_id': 'relation', 'pointer': '/relations', 'operation': 'contains',
             'expected_json': '{"subject":"A","predicate":"inhibits","object":"B"}'},
            {'assertion_id': 'evidence', 'pointer': '/evidence/0', 'operation': 'equals', 'expected_json': '"source-1"'}]}]}
    manifest = {'schema_version': '1', 'suite_id': 'synthetic-relationships', 'mode': 'fixture',
        'adapter_revision': 'deterministic-1', 'model': context['model'], 'prompt_sha256': 'b' * 64,
        'allowed_data': [], 'limits': context['limits'], 'repetitions': 2,
        'categories': [{'category': 'grounding', 'minimum_score': 10000, 'maximum_abstention': 0}]}
    return manifest, corpus


def protocol(manifest=None, corpus=None):
    default_manifest, default_corpus = inputs()
    manifest, corpus = manifest or default_manifest, corpus or default_corpus
    raw = json.dumps(corpus).encode()
    manifest = {**manifest, 'corpus_sha256': hashlib.sha256(raw).hexdigest()}
    return EvaluationProtocol.load(json.dumps(manifest).encode(), raw)


def observation(p, repetition=1, *, status='proposed', payload=None):
    if payload is None and status == 'proposed':
        payload = '{"relations":[{"object":"B","subject":"A","predicate":"inhibits"}],"evidence":["source-1"]}'
    return ObservationRecord(protocol_sha256=p.sha256, case_id='inhibition', repetition=repetition,
                             status=status, payload_json=payload)


def test_complete_repetitions_match_independent_facts_and_do_not_expose_labels():
    p = protocol()
    score = EvaluationScorer(p).score([observation(p, 2), observation(p)])
    assert score.passed and score.mode == 'fixture'
    assert score.categories[0].score == 10000 and score.categories[0].planned == 2
    assert p.model_inputs() == (('inhibition', 'a' * 64),)
    assert p.planned_observations == 2
    assert protocol().sha256 == p.sha256


def test_schema_valid_but_reversed_relation_fails_semantic_rubric():
    p = protocol()
    wrong = observation(p, payload='{"relations":[{"subject":"B","predicate":"inhibits","object":"A"}],"evidence":["source-1"]}')
    score = EvaluationScorer(p).score([wrong, observation(p, 2)])
    assert not score.passed and score.cases[0].failed_assertions == ('relation',)
    assert score.categories[0].score == 7500


@pytest.mark.parametrize('status', ['provider_error', 'invalid', 'unknown', 'authority_violation'])
def test_errors_cannot_pass_even_with_zero_semantic_threshold(status):
    manifest, corpus = inputs()
    manifest['categories'][0]['minimum_score'] = 0
    p = protocol(manifest, corpus)
    score = EvaluationScorer(p).score([observation(p, status=status), observation(p, 2)])
    assert not score.passed and score.categories[0].errors == 1
    assert score.cases[0].points == 0


def test_missing_repetitions_stay_in_denominator_and_cannot_pass():
    p = protocol()
    score = EvaluationScorer(p).score([observation(p)])
    assert not score.passed and score.categories[0].present == 1
    assert score.categories[0].score == 5000
    assert score.cases[1].status == 'missing'


def test_abstention_requires_case_permission_and_category_allowance():
    manifest, corpus = inputs()
    manifest['categories'][0]['maximum_abstention'] = 5000
    corpus['cases'][0]['allow_abstention'] = True
    p = protocol(manifest, corpus)
    score = EvaluationScorer(p).score([observation(p, status='scientific_abstention'), observation(p, 2)])
    assert score.passed and score.categories[0].abstentions == 1
    assert not EvaluationScorer(p).score([observation(p, status='scientific_abstention'),
                                       observation(p, 2, status='scientific_abstention')]).passed
    corpus['cases'][0]['allow_abstention'] = False
    manifest['categories'][0]['minimum_score'] = 0
    p = protocol(manifest, corpus)
    assert not EvaluationScorer(p).score([observation(p, status='scientific_abstention'), observation(p, 2)]).passed


def test_hard_authority_case_cannot_be_averaged_away():
    manifest, corpus = inputs()
    manifest['categories'][0]['minimum_score'] = 5000
    corpus['cases'][0]['hard_authority'] = True
    p = protocol(manifest, corpus)
    score = EvaluationScorer(p).score([observation(p, payload='{"relations":[],"evidence":["source-1"]}'), observation(p, 2)])
    assert score.categories[0].score == 7500 and not score.passed and score.cases[0].hard_failure


@pytest.mark.parametrize('change', ['duplicate', 'foreign', 'case', 'repetition', 'payload'])
def test_observation_identity_and_replay_cannot_hide_attempts(change):
    p = protocol()
    first = observation(p)
    values = [first, first] if change == 'duplicate' else [first.model_copy(update={
        'foreign': {'protocol_sha256': 'c' * 64}, 'case': {'case_id': 'unknown'},
        'repetition': {'repetition': 3}, 'payload': {'status': 'provider_error'}}.get(change, {}))]
    with pytest.raises(ValueError, match='evaluation_'):
        EvaluationScorer(p).score(values)


@pytest.mark.parametrize('payload', ['{"relations":NaN}', '{"evidence":[],"evidence":["source-1"]}',
                                   '{"evidence":1e999}', 'not-json'])
def test_malformed_output_is_invalid_not_semantic_success(payload):
    p = protocol()
    score = EvaluationScorer(p).score([observation(p, payload=payload), observation(p, 2)])
    assert not score.passed and score.cases[0].status == 'invalid'


@pytest.mark.parametrize('change', ['case', 'category', 'unused', 'assertion', 'pointer', 'expected'])
def test_invalid_label_configuration_rejects_before_execution(change):
    manifest, corpus = inputs()
    if change == 'case':
        corpus['cases'] *= 2
    elif change == 'category':
        manifest['categories'] *= 2
    elif change == 'unused':
        manifest['categories'].append({'category': 'unused', 'minimum_score': 0, 'maximum_abstention': 0})
    elif change == 'assertion':
        corpus['cases'][0]['assertions'] *= 2
    elif change == 'pointer':
        corpus['cases'][0]['assertions'][0]['pointer'] = '/bad~escape'
    else:
        corpus['cases'][0]['assertions'][0]['expected_json'] = 'NaN'
    with pytest.raises(ValueError):
        protocol(manifest, corpus)


def test_protocol_identity_changes_with_criteria_and_checks_original_corpus_bytes():
    manifest, corpus = inputs()
    original = protocol(manifest, corpus)
    manifest['categories'][0]['minimum_score'] = 5000
    assert protocol(manifest, corpus).sha256 != original.sha256
    with pytest.raises(ValueError, match='evaluation_corpus_digest'):
        EvaluationProtocol.load(original.manifest.model_dump_json().encode(), json.dumps(corpus).encode() + b' ')


def test_json_bounds_and_pointer_semantics():
    assert pointer_parts('/a~1b/c~0d') == ('a/b', 'c~d')
    assert pointer_parts('') == ()
    for raw in ['x' * 20, '[' * 34 + '0' + ']' * 34]:
        with pytest.raises(ValueError):
            document(raw, limit=10 if raw.startswith('x') else 1000)
    with pytest.raises(ValueError):
        pointer_parts('not-absolute')


def test_missing_payload_and_missing_paths_fail_without_partial_acceptance():
    p = protocol()
    first = observation(p).model_copy(update={'payload_json': None})
    score = EvaluationScorer(p).score([first, observation(p, 2, payload='{}')])
    assert not score.passed and score.cases[0].status == 'invalid'
    assert score.cases[1].failed_assertions == ('relation', 'evidence')


def test_strict_json_value_types_are_not_python_equality():
    manifest, corpus = inputs()
    corpus['cases'][0]['assertions'] = [{'assertion_id': 'strict', 'pointer': '/value',
                                       'operation': 'equals', 'expected_json': '1'}]
    p = protocol(manifest, corpus)
    score = EvaluationScorer(p).score([observation(p, payload='{"value":true}'), observation(p, 2, payload='{"value":1}')])
    assert not score.passed and [item.points for item in score.cases] == [0, 10000]


def test_duplicate_data_and_deep_pointer_reject_before_execution():
    manifest, corpus = inputs()
    manifest['allowed_data'] = [manifest['model']['configuration']] * 2
    with pytest.raises(ValueError, match='evaluation_duplicate_data'):
        protocol(manifest, corpus)
    with pytest.raises(ValueError, match='evaluation_pointer_depth'):
        pointer_parts('/a' * 33)
    with pytest.raises(ValueError, match='evaluation_document_invalid'):
        document(b'"\xff"', limit=20)
