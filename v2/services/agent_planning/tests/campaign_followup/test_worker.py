"""Actual Planning SQL; scripted authenticated owner and deterministic model ports."""

import hashlib
import json

import pytest
from amphora_agent_planning.campaign_followup.source import FollowupResearch, FollowupSeed
from amphora_agent_planning.campaign_research_access import ResearchRecordReader
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.supervision_execution.worker import CheckpointWorker
from amphora_agent_planning.supervision_publication import CaptureOrigin
from amphora_agent_planning.supervision_publication.journal import CaptureJournal
from amphora_contracts_core import ArtifactRef
from amphora_contracts_planning import checkpoint_followup_draft_schema

from ..campaign_context.test_records import values, wire
from ..campaign_research_access.test_reader import Peer, PATHS
from ..supervision_execution.test_worker import setup

pytestmark = pytest.mark.postgres


class Provider:
    def __init__(self, variant='abstain'):
        self.variant, self.calls = variant, []

    def supports(self, model):
        return True

    def reply(self, binding, packet, *, deadline_unix_ms):
        self.calls.append(packet)
        rows = json.loads(packet)['untrusted_context']['slices']
        selection = next(row for row in rows if row['lane'] == 'research')['payload']['selection']
        points = selection['criteria']
        if self.variant == 'foreign':
            points[0]['criterion_id'] = 'foreign'
        value = {'schema_version': '3', 'authority': 'proposal_only', 'scientific_authority': 'not_established',
            'action': 'abstain', 'rationale': 'Synthetic fixture retains unresolved work.',
            'decision_scope': binding.request.document().decision_scope, 'candidate': None,
            'alternatives': [], 'targets': [], 'evidence_requests': [], 'focus_artifact': selection['focus_artifact'],
            'unresolved': [{'criterion': ref, 'posture': 'unknown', 'description': 'Another campaign is needed.'} for ref in points]}
        return ProviderReply((json.dumps(value).encode(),), unknown_usage())


def system(stored, variant='abstain'):
    science = values()
    def configure(original, data):
        original['context']['output_schema'] = checkpoint_followup_draft_schema().model_dump(mode='json')
        body = b'synthetic follow-up provenance'
        ref = dict(original['context']['objective'], artifact_id='followup-science',
            sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body))
        original['context']['entries'].append({'artifact': ref, 'role': 'source', 'required': True})
        data.bodies[ref['artifact_id']] = body
        def rebind(value):
            if isinstance(value, dict):
                if set(value) == set(ref):
                    value.clear(); value.update(json.loads(json.dumps(ref)))
                elif set(value) == {'tenant_id', 'project_id'}:
                    value.clear(); value.update(original['reference']['scope'])
                else:
                    for child in value.values(): rebind(child)
            elif isinstance(value, list):
                for child in value: rebind(child)
        rebind(science)
    worker, data, _, intake = setup(stored, configure_request=configure)
    peer = Peer()
    peer.values = {PATHS[kind]: wire(kind, science[kind]) for kind in ('question', 'need', 'assessment')}
    declaration = json.loads(data.bodies['checkpoint-context'])
    seed = FollowupSeed.model_validate_json(json.dumps({'budget_template': declaration['budget_policy'],
        'criteria': [{'question': science['question']['reference'], 'need': science['need']['reference'],
            'criterion_id': science['need']['criterion_ids'][0], 'assessment': None}], 'focus_artifact': None}))
    worker.followup = FollowupResearch.bind(ResearchRecordReader(peer), (seed,))
    provider = Provider(variant)
    worker.provider = provider
    return worker, data, peer, provider, intake


def test_actual_journal_capture_and_replacement_replay_keep_original_selection(stored):
    worker, data, peer, provider, intake = system(stored)
    engagement = intake.planning.document().reference.engagement_id
    first = worker.run(stored.principal, engagement)
    assert first.stop_reason == 'abstained' and len(provider.calls) == 1 and len(peer.calls) == 2
    preparation = worker.preparations.read(stored.principal, intake.planning.document().reference).record
    origin = CaptureOrigin.bind(intake, stored.principal, preparation, first.latest.observation)
    journal = CaptureJournal(stored.engine, 'followup-test')
    retained = journal.register(stored.principal, first.latest.binding.reference())
    assert retained.origin == origin and retained.payload is not None
    data.denied = True
    peer.values[PATHS['question']] = ValueError('research_access_denied')
    reads = (len(data.calls), len(peer.calls))
    replacement = CheckpointWorker(stored.engine, data, None, None, timeout_seconds=1)
    assert replacement.run(stored.principal, engagement) == first
    assert journal.read(stored.principal, retained.identity.publication_id) == retained
    assert reads == (len(data.calls), len(peer.calls)) and len(provider.calls) == 1
    # A caller can bypass the checkpoint adapter and construct a structurally
    # successful capture; publication must independently reject its foreign point.
    from amphora_agent_planning.providers import observe
    from ..providers.test_task_output import Response
    value = json.loads(first.latest.observation.capture.content)
    value['unresolved'][0]['criterion']['criterion_id'] = 'forged'
    forged = observe(first.latest.binding, Response(json.dumps(value).encode()))
    assert forged.document().status == 'abstained'
    with pytest.raises(ValueError, match='followup_output_unselected'):
        CaptureOrigin.bind(intake, stored.principal, preparation, forged)


def test_foreign_model_target_is_invalid_before_completion_and_only_diagnostic_is_retained(stored):
    worker, _, peer, provider, intake = system(stored, 'foreign')
    outcome = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    assert outcome.stop_reason == 'attempt_limit' and len(provider.calls) == 2
    assert provider.calls[0] == provider.calls[1] and len(peer.calls) == 2
    assert all(item.observation.document().status == 'invalid' for item in outcome.attempts)
    assert outcome.latest.observation.document().reason_code == 'followup_output_unselected'
    assert outcome.latest.observation.document().proposal is None


def test_missing_selected_record_stops_before_model_issuance(stored):
    worker, _, peer, provider, intake = system(stored)
    peer.values[PATHS['need']] = ValueError('research_access_denied')
    outcome = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    assert outcome.stop_reason == 'execution_processing_unavailable' and not outcome.attempts and not provider.calls
    assert worker.preparations.read(stored.principal, intake.planning.document().reference) is None
