"""Generation constraints, original contract acceptance and exact version separation."""
import copy
import json

import pytest
from jsonschema import Draft202012Validator
from amphora_contracts_campaign_curation import CampaignCurationDraft
from amphora_agent_planning.curation_input.structured import GenerationSchema
from amphora_agent_planning.curation_input import CurationEnvelope
from amphora_agent_planning.campaign_packet import prepare
from .test_profile import curation_plan
from ..curation_output.test_output import output


@pytest.mark.parametrize('kind', ['propose_campaign', 'request_capabilities', 'abstain'])
def test_all_outcomes_with_explicit_defaults_satisfy_stronger_generation_schema(kind):
    document = CampaignCurationDraft.model_validate_json(json.dumps(output(kind)))
    generation = GenerationSchema.reviewed()
    schema = generation.format()['schema']
    Draft202012Validator.check_schema(schema)
    value = document.model_dump(mode='json')
    Draft202012Validator(schema).validate(value)
    assert CampaignCurationDraft.model_validate_json(json.dumps(value)) == document
    assert GenerationSchema.reviewed().canonical == generation.canonical
    assert generation.format()['strict'] is True


def test_misplaced_graph_fields_reject_without_repair():
    value = CampaignCurationDraft.model_validate_json(json.dumps(output('propose_campaign'))).model_dump(mode='json')
    value['outcome']['candidate']['definition']['expected_evidence'] = value['outcome']['candidate'].pop('expected_evidence')
    assert not Draft202012Validator(GenerationSchema.reviewed().format()['schema']).is_valid(value)
    with pytest.raises(ValueError): CampaignCurationDraft.model_validate_json(json.dumps(value))


@pytest.mark.parametrize('fault', ['open', 'keyword', 'reference', 'overlap', 'root'])
def test_unsupported_schema_rejects_before_provider(fault):
    schema = {'type': 'object', 'properties': {}, 'additionalProperties': False}
    if fault == 'open': schema['additionalProperties'] = True
    if fault == 'keyword': schema['if'] = {}
    if fault == 'reference': schema['properties']['x'] = {'$ref': 'https://example.invalid/schema'}
    if fault == 'overlap': schema['properties']['x'] = {'oneOf': [{'type': 'string'}, {'type': 'string'}]}
    if fault == 'root': schema['anyOf'] = [{'type': 'string'}]
    with pytest.raises(ValueError): GenerationSchema.bind(schema)


def test_nullable_and_default_fields_are_required_without_inventing_nulls():
    source = {'type': 'object', 'additionalProperties': False, 'properties': {
        'count': {'type': 'integer', 'default': 0},
        'label': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None}}}
    before = copy.deepcopy(source)
    validator = Draft202012Validator(GenerationSchema.bind(source).format()['schema'])
    assert source == before
    assert validator.is_valid({'count': 0, 'label': None})
    assert not validator.is_valid({'count': None, 'label': None})
    assert not validator.is_valid({'count': 0})


def test_v3_schema_is_in_complete_envelope_fit_and_replay():
    source = curation_plan(version='3')
    packet = prepare(source).packet
    envelope = CurationEnvelope.bind(source.request, packet.canonical)
    body = json.loads(envelope.body)
    assert body['text']['format'] == GenerationSchema.reviewed().format()
    assert packet.fit.document()['format'] == 'planning-campaign-packet-fit.v5'
    assert packet.fit.measurement.input_tokens == len(envelope.body) + 1024
    assert CurationEnvelope.bind(source.request, packet.canonical).body == envelope.body
    assert prepare(curation_plan(version='3', maximum=len(packet.canonical) + 100)).packet is None
    for version in ('1', '2'):
        old = curation_plan(version=version)
        old_packet = prepare(old).packet
        assert json.loads(CurationEnvelope.bind(old.request, old_packet.canonical).body)['text']['format'] == {'type': 'json_object'}


def test_v4_direct_generation_preserves_strict_schema_limits_and_old_effort():
    from amphora_agent_planning.curation_input import curation_tokenizer_reference
    from amphora_agent_planning.curation_budget.policy import CurationAllowance
    references = []
    for version in ('1', '2', '3', '4', '5'):
        source = curation_plan(version=version)
        packet = prepare(source).packet
        envelope = CurationEnvelope.bind(source.request, packet.canonical)
        body = json.loads(envelope.body)
        assert body['reasoning'] == {'effort': 'none' if version in {'4', '5'} else 'low'}
        assert body['max_output_tokens'] == source.request.document().context.limits.max_output_tokens
        assert CurationAllowance.applies(source.request)
        assert CurationEnvelope.bind(source.request, packet.canonical).body == envelope.body
        references.append(curation_tokenizer_reference(version).sha256)
        if version in {'4', '5'}:
            assert body['text']['format'] == GenerationSchema.reviewed().format()
            assert packet.fit.document()['format'] == ('planning-campaign-packet-fit.v6' if version == '4' else 'planning-campaign-packet-fit.v7')
            assert packet.fit.measurement.input_tokens == len(envelope.body) + 1024
    assert len(set(references)) == 5


@pytest.mark.parametrize('version,fit', [('6', '8'), ('7', '9')])
def test_compatible_profiles_keep_local_rejection(version, fit):
    from amphora_contracts_campaigns.executable.values import NumberConstant
    old = GenerationSchema.reviewed()
    expected = json.loads(old.canonical)
    value = expected['$defs']['NumberConstant']['properties']['value']
    del value['minimum']; del value['maximum']
    compatible = GenerationSchema.provider_compatible()
    assert json.loads(compatible.canonical) == expected
    assert GenerationSchema.reviewed().canonical == old.canonical
    assert compatible.sha256 != old.sha256
    for number in (-1e101, 1e101):
        with pytest.raises(ValueError): NumberConstant.model_validate_json(json.dumps({'kind': 'number', 'value': number}))
    for number in (-1e100, 0, 1e100):
        assert NumberConstant.model_validate_json(json.dumps({'kind': 'number', 'value': number})).value == number
    source = curation_plan(version=version)
    packet = prepare(source).packet
    envelope = CurationEnvelope.bind(source.request, packet.canonical)
    assert json.loads(envelope.body)['text']['format'] == compatible.format()
    assert packet.fit.document()['format'] == 'planning-campaign-packet-fit.v' + fit
    assert CurationEnvelope.bind(source.request, packet.canonical).body == envelope.body
