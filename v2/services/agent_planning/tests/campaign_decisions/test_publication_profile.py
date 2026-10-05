"""Publishable declarations retain original authority and literal v1 history."""

import base64
import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.campaign_decisions import (
    CampaignDecisionReview,
    DecisionDeclaration,
)

from .test_policy import fixture


def v2(document):
    document['format'] = 'planning-campaign-decision.v2'
    document.pop('declaration_artifact_id')


def test_literal_predecessor_profile_retains_bytes_and_digest():
    # Exported using independently installed Planning0.66, before profile v2.
    raw = Path(__file__).with_name('v1_declaration.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '7f8764ef7c4cb549d2b990d008c92d5de87c3d40ed4c9a72337ced2bc78be713'
    assert DecisionDeclaration.from_bytes(raw).canonical == raw
    assert fixture()[1].canonical == raw


def test_v2_binds_exact_consumed_artifact_without_self_identifier():
    proposal, declaration, budget = fixture(declaration_change=v2)
    review = CampaignDecisionReview.bind(proposal, declaration, budget)
    assert review.next_step == 'compile_future_draft'
    assert 'declaration_artifact_id' not in declaration.document().model_dump()
    identity = json.loads(declaration.bind(proposal).identity)
    assert identity['artifact_id'] == 'decision' and identity['sha256'] == declaration.sha256
    assert DecisionDeclaration.from_bytes(declaration.canonical) == declaration


@pytest.mark.parametrize('mutation', [
    {'role': 'source'}, {'required': False}, {'sha256': 'f' * 64},
    {'size_bytes': 1}, {'media_type': 'application/json'},
])
def test_v2_requires_exact_original_constraint_entry(mutation):
    proposal, declaration, _ = fixture(declaration_change=v2)
    original = proposal.attempt.request.document()
    entry = original.context.entries[-1]
    if 'role' in mutation or 'required' in mutation:
        entry = entry.model_copy(update=mutation)
    else:
        entry = entry.model_copy(update={'artifact': entry.artifact.model_copy(update=mutation)})
    context = original.context.model_copy(update={'entries': (*original.context.entries[:-1], entry)})
    changed = original.model_copy(update={'context': context})
    with pytest.raises(ValueError, match='decision_declaration_unique_entry'):
        declaration.original_entry(changed, declaration.document())


def test_v2_rejects_ambiguous_distinct_artifacts_with_identical_content():
    proposal, declaration, _ = fixture(declaration_change=v2)
    original = proposal.attempt.request.document()
    entry = original.context.entries[-1]
    another = entry.model_copy(update={'artifact': entry.artifact.model_copy(update={'artifact_id': 'duplicate-body'})})
    context = original.context.model_copy(update={'entries': (*original.context.entries, another)})
    with pytest.raises(ValueError, match='decision_declaration_unique_entry'):
        declaration.original_entry(original.model_copy(update={'context': context}), declaration.document())


@pytest.mark.parametrize('version', ['planning-campaign-decision.v2', 'planning-campaign-decision.v3'])
def test_new_profile_cannot_smuggle_a_self_identifier(version):
    raw = json.loads(Path(__file__).with_name('v1_declaration.json').read_bytes())
    raw['format'] = version
    with pytest.raises(ValueError, match='invalid_decision_declaration'):
        DecisionDeclaration.from_bytes(json.dumps(raw).encode())


@pytest.mark.parametrize('missing', [True, False])
def test_v2_rejects_missing_or_different_consumed_body(monkeypatch, missing):
    proposal, declaration, _ = fixture(declaration_change=v2)
    packet = proposal.inputs.preparation.packet
    context = packet.context()
    row = next(row for row in context['slices'] if row['lane'] == 'artifact' and row['identity']['artifact_id'] == 'decision')
    if missing:
        context['slices'].remove(row)
    else:
        row['payload']['body_base64'] = base64.b64encode(b'different declaration').decode()
    monkeypatch.setattr(type(packet), 'context', lambda self: context)
    with pytest.raises(ValueError, match='decision_declaration_unconsumed' if missing else 'decision_declaration_body'):
        declaration.bind(proposal)


def test_v2_rejects_foreign_scope_and_post_attempt_replacement():
    proposal, declaration, budget = fixture(declaration_change=v2)
    value = declaration.document().model_dump(mode='json')
    value['objective']['scope']['project_id'] = 'foreign'
    with pytest.raises(ValueError, match='decision_declaration_scope'):
        DecisionDeclaration.from_bytes(json.dumps(value).encode())
    value = declaration.document().model_dump(mode='json')
    value['future']['max_nodes'] = 100
    changed = DecisionDeclaration.from_bytes(json.dumps(value).encode())
    with pytest.raises(ValueError, match='decision_declaration_digest'):
        CampaignDecisionReview.bind(proposal, changed, budget)
