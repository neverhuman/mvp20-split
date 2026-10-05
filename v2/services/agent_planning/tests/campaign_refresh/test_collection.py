"""Actual owned readers over scripted peers; no source-rights lease is inferred."""

import base64
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_context import ResearchIdentity
from amphora_agent_planning.campaign_data_access import CampaignArtifactReader
from amphora_agent_planning.campaign_decisions import CampaignDecisionReview
from amphora_agent_planning.campaign_refresh import RefreshCollector, RefreshPlan
from amphora_agent_planning.campaign_refresh.collector import ExactReleaseWindow
from amphora_agent_planning.campaign_research_access import ResearchRecordReader
from amphora_agent_planning.registry_access import RegistryReader
from amphora_agent_planning.runtime_metadata import RuntimeMetadataReader

from ..campaign_decisions.test_policy import fixture
from ..campaign_proposals.test_composition import revised_universe
from ..registry_access.test_discovery import Scripted
from ..runtime_metadata.test_reader import universe


class Data:
    def __init__(self, plan):
        packet = plan.review.composition.evidence.proposal.inputs.preparation.packet
        trusted = json.loads(packet.canonical)['trusted_instructions'].encode()
        self.bodies = {row['identity']['artifact_id']: base64.b64decode(row['payload']['body_base64'])
                       if 'body_base64' in row['payload'] else trusted
                       for row in packet.context()['slices'] if row['lane'] == 'artifact' and row['payload']['status'] == 'available'}
        self.calls, self.denied, self.budgets = [], set(), []

    def artifact(self, reference, budget):
        budget.start()
        self.budgets.append(budget)
        self.calls.append(('metadata', reference.artifact_id))
        if reference.artifact_id in self.denied:
            raise ValueError('source_access_denied')
        return reference

    def content(self, reference, budget):
        budget.start()
        self.calls.append(('processing', reference.artifact_id))
        body = self.bodies[reference.artifact_id]
        budget.consume(len(body))
        return body


class Research:
    def __init__(self, plan):
        context = plan.review.composition.evidence.research
        self.records = {} if context is None else {row.identity: row.document() for row in context.context.records}
        self.calls = []

    def read(self, path, reference, window):
        window.start()
        kind = {'/v1/questions/read': 'question', '/v1/evidence-needs/read': 'need', '/v1/assessments/read': 'assessment'}[path]
        key = ResearchIdentity.bind(kind, reference)
        self.calls.append(key)
        if key not in self.records:
            raise ValueError('research_reference_unavailable')
        value = self.records[key]
        window.consume(len(value.model_dump_json().encode()))
        return value


def inputs(**kwargs):
    proposal, declaration, budget = fixture(**kwargs)
    plan = RefreshPlan.bind(CampaignDecisionReview.bind(proposal, declaration, budget), budget)
    data, research = Data(plan), Research(plan)
    registry = Scripted(*(row.document() for row in plan.releases))
    runtime = Scripted(universe())
    collector = RefreshCollector(artifacts=CampaignArtifactReader(data), research=ResearchRecordReader(research),
                                 registry=RegistryReader(registry), runtime=RuntimeMetadataReader(runtime))
    return plan, collector, data, research, registry, runtime


def test_fresh_processing_and_relevant_owner_reads_are_separate_from_latest_head():
    plan, collector, data, research, registry, runtime = inputs(tools=True, research={})
    result = collector.collect(plan)
    assert result.ready_for_preparation and not result.latest_research_head_verified
    assert set(result.processing_artifacts) == set(plan.artifacts)
    assert len(data.calls) == 2 * len(plan.artifacts) and len(research.calls) == 3
    assert len(registry.paths) == 1 and runtime.paths == ['/v1/definition-universe']
    assert plan.verify() == plan


def test_revoked_processing_prevents_new_preparation_without_rewriting_history():
    plan, collector, data, *_ = inputs()
    original = plan.review.composition.evidence.proposal.sha256
    assert collector.collect(plan).ready_for_preparation
    data.denied.add(plan.artifacts[0].artifact_id)
    result = collector.collect(plan)
    assert not result.ready_for_preparation and not result.changes
    assert result.failures[0].code == 'source_access_denied'
    assert plan.review.composition.evidence.proposal.sha256 == original


def test_still_missing_science_is_not_a_global_veto():
    plan, collector, *_ = inputs(research={'omitted': ('question', 'need', 'assessment')})
    result = collector.collect(plan)
    assert result.ready_for_preparation and not result.changes
    assert len(result.scientific_gaps) == 3
    assert {gap.code for gap in result.scientific_gaps} == {'unavailable'}


@pytest.mark.parametrize('relevant', [True, False])
def test_changed_record_content_only_invalidates_referenced_input(relevant):
    plan, collector, _, research, *_ = inputs(research={'additional_question': True})
    key = next(key for key in research.records if key.kind == 'question' and
               (json.loads(key.reference)['question_id'] == 'another-question') != relevant)
    value = research.records[key]
    research.records[key] = value.model_copy(update={'objective': 'Changed selected criteria context'})
    result = collector.collect(plan)
    assert result.ready_for_preparation is not relevant
    assert len(result.changes) == (1 if relevant else 0)


def test_previously_available_research_becoming_unavailable_is_a_relevant_change():
    plan, collector, _, research, *_ = inputs(research={})
    key = next(key for key in research.records if key.kind == 'question')
    del research.records[key]
    result = collector.collect(plan)
    assert not result.ready_for_preparation and len(result.changes) == 1
    assert result.changes[0].after_sha256 is None


@pytest.mark.parametrize('relevant', [True, False])
def test_runtime_comparison_ignores_unrelated_reviewed_tools(relevant):
    plan, collector, _, _, _, runtime = inputs(tools=True)
    def change(value):
        value['reviewed_tools'][0 if relevant else 1]['tool']['image_sha256'] = 'f' * 64
    runtime.responses = [revised_universe(change)]
    result = collector.collect(plan)
    assert result.ready_for_preparation is not relevant


def test_registry_lifecycle_change_is_retained_as_selected_change():
    plan, collector, _, _, registry, _ = inputs(tools=True)
    registry.responses = [plan.releases[0].document().model_copy(update={'status': 'revoked'})]
    result = collector.collect(plan)
    assert not result.ready_for_preparation and result.changes[0].key.lane == 'registry_inventory'


@pytest.mark.parametrize('owner', ['registry', 'runtime'])
def test_metadata_owner_failures_do_not_become_freshness(owner):
    plan, collector, _, _, registry, runtime = inputs(tools=True)
    (registry if owner == 'registry' else runtime).responses = [ValueError('metadata_denied')]
    result = collector.collect(plan)
    assert not result.ready_for_preparation
    assert result.failures[0].owner == owner and result.failures[0].code == 'metadata_denied'


def test_132_consumed_artifacts_share_one_budget_across_two_batches():
    extras = tuple(('extra-' + str(i), b'x', True) for i in range(127))
    plan, collector, data, *_ = inputs(extras=extras, maximum=600000)
    result = collector.collect(plan)
    assert result.ready_for_preparation and len(result.processing_artifacts) == 132
    assert len({id(budget) for budget in data.budgets}) == 1
    assert data.budgets[0].calls == 264


def test_exact_release_window_does_not_silently_stop_at_eight():
    window = ExactReleaseWindow()
    for _ in range(64):
        window.start()
    with pytest.raises(ValueError, match='metadata_call_limit'):
        window.start()


def test_forged_plan_cannot_skip_processing_inputs():
    plan, collector, data, *_ = inputs()
    with pytest.raises(ValueError, match='refresh_plan_binding'):
        collector.collect(replace(plan, artifacts=()))
    assert not data.calls


def test_omitted_optional_payload_is_not_fetched_during_refresh():
    plan, collector, data, *_ = inputs(extras=(('omitted', b'x' * 300000, False),))
    result = collector.collect(plan)
    assert result.ready_for_preparation
    assert 'omitted' not in {reference.artifact_id for reference in result.processing_artifacts}
    assert 'omitted' not in {name for _, name in data.calls}


def test_mismatched_artifact_bytes_remain_a_processing_failure():
    plan, collector, data, *_ = inputs()
    data.bodies[plan.artifacts[0].artifact_id] = b'not the retained input'
    result = collector.collect(plan)
    assert not result.ready_for_preparation and result.failures[0].code == 'source_artifact_bytes'


def test_bad_runtime_universe_digest_is_an_explicit_failure():
    plan, collector, _, _, _, runtime = inputs(tools=True)
    runtime.responses = [universe().model_copy(update={'universe_sha256': 'f' * 64})]
    result = collector.collect(plan)
    assert not result.ready_for_preparation
    assert result.failures[0].code == 'runtime_metadata_universe'
