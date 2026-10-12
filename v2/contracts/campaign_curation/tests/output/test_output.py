"""Typed gaps must survive without a graph and cannot claim fulfillment."""
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError
import amphora_contracts_planning as planning
from amphora_contracts_campaign_launch import LaunchRequest, LaunchReceipt
from amphora_contracts_campaign_curation.output import CampaignCurationDraft


def gap():
    return {'gap_key': 'combine', 'purpose': 'Combine selected materials', 'inputs': [],
            'outputs': [{'name': 'mixture', 'representation': 'mixture', 'schema_ref': None,
                         'description': 'Composition with material proportions', 'unit': None}],
            'applicability': ['Synthetic engineering demonstration'],
            'evidence_need': 'Qualified composition accounting',
            'acceptance_criteria': ['Preserve input mass and provenance'],
            'graph_gap': 'Converge branches before the next heating stage'}


def draft(kind='request_capabilities'):
    outcome = {'kind': kind, 'gaps': [gap()]}
    if kind == 'abstain':
        outcome = {'kind': kind, 'reason_code': 'insufficient_context'}
    elif kind == 'propose_campaign':
        fixture = Path(__file__).parents[3] / 'planning/tests/campaign_output/fixtures/future.json'
        outcome['candidate'] = json.loads(fixture.read_bytes())['candidate']
    return {'schema_version': '1', 'profile': 'planning.campaign-curation-draft.v1',
            'authority': 'proposal_only', 'scientific_authority': 'not_established',
            'decision_scope': 'a' * 64, 'rationale': 'The next stage requires a reviewed capability',
            'outcome': outcome, 'unresolved': []}


@pytest.mark.parametrize('kind', ['request_capabilities', 'propose_campaign', 'abstain'])
def test_portable_distinct_outcomes(kind):
    raw = draft(kind)
    parsed = CampaignCurationDraft.model_validate_json(json.dumps(raw))
    Draft202012Validator(CampaignCurationDraft.model_json_schema()).validate(raw)
    assert CampaignCurationDraft.model_validate_json(parsed.model_dump_json()) == parsed
    for old in (planning.CampaignDraft, planning.CheckpointDraft, planning.CheckpointFollowupDraft):
        with pytest.raises(ValidationError):
            old.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize('case', ['fulfilled', 'handler', 'empty_gaps', 'overflow', 'empty_outputs',
                                 'untyped', 'authority', 'long_rationale', 'missing_graph', 'extra_graph'])
def test_invalid_or_authoritative_claims_rejected(case):
    raw = draft('propose_campaign' if case == 'missing_graph' else 'request_capabilities')
    if case == 'fulfilled': raw['outcome']['gaps'][0]['status'] = 'fulfilled'
    if case == 'handler': raw['outcome']['gaps'][0]['handler'] = 'install()'
    if case == 'empty_gaps': raw['outcome']['gaps'] = []
    if case == 'overflow': raw['outcome']['gaps'] *= 17
    if case == 'empty_outputs': raw['outcome']['gaps'][0]['outputs'] = []
    if case == 'untyped': del raw['outcome']['gaps'][0]['outputs'][0]['representation']
    if case == 'authority': raw['authority'] = 'accepted'
    if case == 'long_rationale': raw['rationale'] = 'x' * 4097
    if case == 'missing_graph': del raw['outcome']['candidate']
    if case == 'extra_graph': raw['outcome']['candidate'] = {}
    with pytest.raises(ValidationError):
        CampaignCurationDraft.model_validate_json(json.dumps(raw))


def test_predecessor_schema_bytes_unchanged():
    pins = json.loads(Path(__file__).with_name('predecessor_schema_pins.json').read_bytes())
    for name, modes in pins.items():
        model = {'LaunchRequest': LaunchRequest, 'LaunchReceipt': LaunchReceipt}.get(name)
        if model is None: model = getattr(planning, name)
        for mode, expected in modes.items():
            raw = json.dumps(model.model_json_schema(mode=mode), sort_keys=True,
                             separators=(',', ':'), ensure_ascii=False).encode()
            assert hashlib.sha256(raw).hexdigest() == expected, (name, mode)
