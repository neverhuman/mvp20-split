"""Captured evidence is exact, scoped, and still has no accepted execution authority."""

import hashlib
import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.supervision_responses import SupervisionResponseBinding
from amphora_contracts_supervision import SupervisionResponse

from .support import origin, replace_capture, response


def bind(record, raw, *, original=None):
    saved, footprint = origin()
    return SupervisionResponseBinding.bind(original or saved, footprint, record,
        actor_id=saved.document().planning_request.actor_id, capture_bytes=raw)


@pytest.mark.parametrize('name', ['abstain', 'evidence', 'adjustment', 'unknown'])
def test_literal_predecessor_outputs_bind_without_becoming_decisions(name):
    record, raw = response(name)
    result = bind(record, raw)
    assert result.document() == record
    assert result.sha256 == hashlib.sha256(result.canonical).hexdigest()
    assert bind(result.document(), raw).canonical == result.canonical
    assert 'outcome' not in type(result.document()).model_fields


@pytest.mark.parametrize('path,value,reason', [
    (('request_sha256',), 'f' * 64, 'response_request_mismatch'),
    (('reference', 'decision_id'), 'other', 'response_request_mismatch'),
    (('observation', 'attempt', 'request_sha256'), 'f' * 64, 'response_attempt_mismatch'),
    (('observation', 'attempt', 'engagement', 'engagement_id'), 'other', 'response_attempt_mismatch'),
    (('observation', 'attempt', 'ordinal'), 16, 'response_attempt_limit'),
    (('observation', 'usage', 'accounting_units'), None, 'incomplete_reported_usage'),
    (('observation', 'output_sha256'), 'f' * 64, 'capture_content_mismatch'),
    (('capture', 'sha256'), 'f' * 64, 'capture_artifact_mismatch'),
    (('capture', 'scope', 'project_id'), 'foreign', 'capture_artifact_mismatch'),
    (('capture',), None, 'capture_artifact_missing'),
    (('observation', 'output_complete'), False, 'successful_capture_incomplete'),
    (('observation', 'reason_code'), 'unexpected', 'successful_capture_incomplete'),
    (('observation', 'proposal', 'payload_sha256'), 'f' * 64, 'proposal_capture_mismatch'),
    (('observation', 'proposal', 'output_schema', 'sha256'), 'f' * 64, 'output_profile_mismatch'),
    (('observation', 'status'), 'proposed', 'observation_action_mismatch'),
    (('observation', 'status'), 'unknown', 'diagnostic_has_proposal'),
])
def test_reject_swapped_origin_capture_or_typed_claims(path, value, reason):
    record, raw = response()
    document = record.model_dump(mode='json')
    target = document
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError, match=reason):
        bind(SupervisionResponse.model_validate_json(json.dumps(document)), raw)


def test_empty_and_partial_diagnostics_preserve_unknown_usage():
    record, _ = response('unknown')
    assert bind(record, None).document().observation.usage.accounting_units is None
    partial, raw = response()
    document = partial.model_dump(mode='json')
    document['observation'].update(status='unknown', reason_code='response_interrupted',
        output_complete=False, proposal=None,
        usage={'input_tokens': None, 'output_tokens': None, 'accounting_units': None, 'certainty': 'unknown'})
    partial = SupervisionResponse.model_validate_json(json.dumps(document))
    partial = replace_capture(partial, raw[:30])
    assert bind(partial, raw[:30]).document().observation.output_complete is False


@pytest.mark.parametrize('raw', [b'{"action":"abstain","action":"abstain"}', b'{"x":NaN}',
                                  b'\xff', b'not-json', b'{"x":1e999}'])
def test_malformed_capture_cannot_become_a_success_even_with_matching_digest(raw):
    record, _ = response()
    record = replace_capture(record, raw)
    with pytest.raises(ValueError, match='invalid_campaign_capture'):
        bind(record, raw)


@pytest.mark.parametrize('name,path,value,reason', [
    ('abstain', ('decision_scope',), 'f' * 64, 'declaration_digest_mismatch'),
    ('abstain', ('unresolved', 0, 'question', 'scope', 'project_id'), 'foreign', 'candidate_scope_mismatch'),
    ('evidence', ('evidence_requests',), [], 'evidence_payload_mismatch'),
    ('adjustment', ('candidate',), None, 'campaign_candidate_missing'),
    ('adjustment', ('candidate', 'cut', 'revision'), 90, 'adjustment_cut_mismatch'),
])
def test_self_consistent_payload_still_requires_original_profile_context(name, path, value, reason):
    record, raw = response(name)
    document = json.loads(raw)
    target = document
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    raw = json.dumps(document).encode()
    record = replace_capture(record, raw, align_proposal=True)
    with pytest.raises(ValueError, match=reason):
        bind(record, raw)


def test_duplicate_adjustment_and_capture_byte_type_reject():
    record, raw = response('adjustment')
    document = json.loads(raw)
    document['candidate']['changes'] *= 2
    raw = json.dumps(document).encode()
    with pytest.raises(ValueError, match='duplicate_adjustment'):
        bind(replace_capture(record, raw, align_proposal=True), raw)
    with pytest.raises(ValueError, match='capture_bytes_required'):
        bind(record, bytearray(raw))
    unknown, _ = response('unknown')
    # An Artifact metadata reference without the actual fetched empty body is unavailable.
    artifact = record.capture.model_copy(update={'sha256': hashlib.sha256(b'').hexdigest(), 'size_bytes': 0})
    unknown = unknown.model_copy(update={'capture': artifact})
    with pytest.raises(ValueError, match='capture_unavailable'):
        bind(unknown, None)


def test_direct_original_bytes_are_revalidated_instead_of_trusting_factory_type():
    saved, _ = origin()
    record, raw = response()
    forged = replace(saved, canonical=json.dumps(json.loads(saved.canonical), indent=2).encode())
    with pytest.raises(ValueError, match='original_supervision_bytes_mismatch'):
        bind(record, raw, original=forged)
