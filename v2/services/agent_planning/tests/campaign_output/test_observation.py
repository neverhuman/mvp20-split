"""Campaign parsing through the real capture and durable reconstruction paths."""

import json

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.persistence.records import verified_observation
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.capture import Observation
from amphora_agent_planning.providers.profiles import OutputProfiles
from amphora_agent_planning.providers.wire import observation_document

from ..providers.test_task_output import Response
from .test_output import output, parse, request


@pytest.mark.parametrize('name', ['future', 'adjustment', 'evidence', 'abstain'])
def test_campaign_capture_reconstructs_original_typed_proposal(name):
    snapshot = request(name)
    binding = AttemptBinding(snapshot, 1)
    raw = json.dumps(output(name), indent=2).encode()
    observed = observe(binding, Response(raw))
    wire = observed.document()
    assert wire.schema_version == '2'
    assert wire.status == ('abstained' if name == 'abstain' else 'proposed')
    assert observed.capture.content == raw and observed.capture.complete
    assert wire.proposal == parse(output(name), snapshot).proposal()
    assert observation_document(observed.canonical) == wire
    assert verified_observation(binding, observed) == observed


@pytest.mark.parametrize('field,value', [('payload_json', '{}'), ('payload_sha256', 'f' * 64),
                                      ('action', 'abstain'), ('rationale', 'forged')])
def test_model_candidate_cannot_rewrite_retained_capture(field, value):
    binding = AttemptBinding(request(), 1)
    observed = observe(binding, Response(json.dumps(output()).encode()))
    wire = observed.document().model_dump(mode='json')
    wire['proposal'][field] = value
    with pytest.raises(ValueError, match='proposal_capture_mismatch'):
        verified_observation(binding, Observation(observed.capture, json.dumps(wire).encode()))


@pytest.mark.parametrize('case,status,reason', [
    ('digest', 'policy_rejected', 'campaign_decision_scope'),
    ('scope', 'policy_rejected', 'campaign_output_scope'),
    ('cut', 'policy_rejected', 'campaign_adjustment_cut'),
    ('empty', 'invalid', 'campaign_missing_candidate'),
    ('malformed', 'invalid', 'invalid_output'),
    ('duplicate', 'invalid', 'duplicate_json_key'),
    ('oversize', 'invalid', 'output_size'),
])
def test_campaign_failure_statuses_remain_explicit(case, status, reason):
    name = 'adjustment' if case == 'cut' else 'future'
    binding = AttemptBinding(request(name), 1)
    value = output(name)
    if case == 'digest':
        value['decision_scope'] = '0' * 64
    elif case == 'scope':
        value['candidate']['definition']['scope']['project_id'] = 'foreign'
    elif case == 'cut':
        value['candidate']['cut']['revision'] += 1
    elif case == 'empty':
        value['candidate'] = None
    raw = {'malformed': b'{', 'duplicate': b'{"action":1,"action":2}',
           'oversize': b'x' * 65537}.get(case, json.dumps(value).encode())
    observed = observe(binding, Response(raw))
    assert observed.document().status == status
    assert observed.document().reason_code == reason
    assert observed.document().proposal is None
    assert verified_observation(binding, observed) == observed


def test_campaign_output_does_not_enter_extraction_attribution_parser():
    binding = AttemptBinding(request(), 1)
    with pytest.raises(ValueError, match='unsupported_output_profile'):
        OutputProfiles.draft_model(binding.request.document().context.output_schema)


def test_only_exact_campaign_profile_is_admitted_before_provider_call():
    from ..context.test_snapshot import bind
    value = request().document().model_dump(mode='json')
    value['context']['output_schema']['sha256'] = '0' * 64
    binding = AttemptBinding(bind(value), 1)
    provider = Response(json.dumps(output()).encode())
    observed = observe(binding, provider)
    assert provider.calls == 0
    assert observed.document().reason_code == 'provider_or_profile_mismatch'
