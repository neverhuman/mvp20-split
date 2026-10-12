"""Original gap outcome survives generic observation and compiler projection."""
import json
from dataclasses import replace
from pathlib import Path

import pytest
from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.curation_output import CurationOutput
from amphora_agent_planning.providers.profiles import OutputProfiles
from ..campaign_context.test_selection import request


def original():
    value = request().document().model_dump(mode='json')
    value['context']['output_schema'] = campaign_curation_draft_schema().model_dump(mode='json')
    value['context']['allowed_actions'] = ['propose_campaign', 'abstain']
    value['purpose'] = 'campaign_proposal'
    return request(value)


def output(kind='request_capabilities'):
    gap = {'gap_key': 'heat', 'purpose': 'Heat the combined material', 'inputs': [],
        'outputs': [{'name': 'material', 'representation': 'mixture', 'schema_ref': None,
                     'description': 'Heated mixture state', 'unit': None}],
        'applicability': ['Synthetic process demonstration'], 'evidence_need': 'Retained temperature history',
        'acceptance_criteria': ['Preserve input provenance'], 'graph_gap': 'Between convergence and addition'}
    outcome = {'kind': kind, 'gaps': [gap]}
    if kind == 'abstain': outcome = {'kind': kind, 'reason_code': 'insufficient_context'}
    if kind == 'propose_campaign':
        fixture = Path(__file__).parents[4] / 'contracts/planning/tests/campaign_output/fixtures/future.json'
        outcome['candidate'] = json.loads(fixture.read_bytes())['candidate']
    value = {'schema_version': '1', 'profile': 'planning.campaign-curation-draft.v1',
        'authority': 'proposal_only', 'scientific_authority': 'not_established',
        'decision_scope': original().document().decision_scope, 'rationale': 'A reviewed tool is needed',
        'outcome': outcome, 'unresolved': []}
    def scope(item):
        if isinstance(item, dict):
            if set(item) == {'tenant_id', 'project_id'}:
                item.update(original().document().reference.scope.model_dump())
            for child in item.values(): scope(child)
        elif isinstance(item, list):
            for child in item: scope(child)
    scope(value)
    return value


@pytest.mark.parametrize('kind', ['request_capabilities', 'propose_campaign', 'abstain'])
def test_original_typed_outcome_and_exact_graph_projection(kind):
    raw = json.dumps(output(kind)).encode()
    result = CurationOutput.parse(raw, original())
    proposal = OutputProfiles.parse(raw, AttemptBinding(original(), 1))
    assert proposal == result.proposal()
    assert json.loads(proposal.payload_json)['outcome']['kind'] == kind
    assert proposal.output_schema == campaign_curation_draft_schema()
    assert proposal.action == ('propose_campaign' if kind == 'propose_campaign' else 'abstain')
    projected = result.review_document()
    if kind == 'propose_campaign':
        assert projected.candidate == result.document().outcome.candidate
    else:
        assert projected.candidate is None
    assert CurationOutput.parse(result.canonical, original()) == result


@pytest.mark.parametrize('fault', ['decision', 'duplicate_gap', 'duplicate_port', 'extra', 'fulfill', 'purpose', 'action'])
def test_untrusted_output_cannot_change_authority(fault):
    value = output()
    request_value = original().document().model_dump(mode='json')
    if fault == 'decision': value['decision_scope'] = 'f' * 64
    if fault == 'duplicate_gap': value['outcome']['gaps'] *= 2
    if fault == 'duplicate_port': value['outcome']['gaps'][0]['outputs'] *= 2
    if fault == 'extra': value['handler'] = 'run()'
    if fault == 'fulfill': value['outcome']['gaps'][0]['status'] = 'fulfilled'
    if fault == 'purpose': request_value['purpose'] = 'knowledge_decomposition'
    if fault == 'action': request_value['context']['allowed_actions'] = ['propose_campaign']
    with pytest.raises(ValueError): CurationOutput.parse(json.dumps(value).encode(), request(request_value))


def test_forged_domain_object_cannot_bypass_revalidation():
    result = CurationOutput.parse(json.dumps(output()).encode(), original())
    with pytest.raises(ValueError): replace(result, canonical=b'{}').proposal()
    with pytest.raises(ValueError): CurationOutput.parse(b'{"outcome":{},"outcome":{}}', original())
    with pytest.raises(ValueError): CurationOutput.parse(b' ' * 65537, original())
