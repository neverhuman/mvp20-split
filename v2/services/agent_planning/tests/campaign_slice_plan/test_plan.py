import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_artifact_context import (
    ArtifactContextItem,
    ArtifactContextPlan,
    ArtifactContextProjection,
    CampaignArtifactContextReader,
)
from amphora_agent_planning.campaign_knowledge_access import CampaignKnowledgeReader
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
from amphora_agent_planning.campaign_slice_plan.slices import ContextSlice, ordered
from amphora_agent_planning.registry_access import ObservedRelease

from ..campaign_artifact_context.test_context import Data, entry, original
from ..campaign_context.test_records import context
from ..campaign_context.test_selection import SCOPE, request
from ..campaign_knowledge_access.test_reader import selected
from ..campaign_research_context.test_projection import result as view
from ..campaign_retrieval_context.test_projection import observed as retrieval
from ..campaign_tool_context.test_registry import scan
from ..campaign_tool_context.test_runtime import observed as runtime
from ..registry_access.test_discovery import record


def empty(original_request=None):
    plan = ArtifactContextPlan.bind(original_request or request())
    projection = ArtifactContextProjection.bind(plan, tuple(ArtifactContextItem.unavailable(row, 'source_access_denied') for row in plan.items))
    return CampaignSlicePlan.from_artifacts(projection)


def test_artifact_priority_required_failure_and_original_bytes_are_preserved():
    value = original((entry('optional'), entry('required', required=True)))
    data = Data()
    data.errors['required'] = 'source_reference_unavailable'
    projection = CampaignArtifactContextReader(data).read(request(value)).projection
    plan = CampaignSlicePlan.from_artifacts(projection)
    assert [row.required for row in plan.slices] == [True] * 5 + [False]
    assert plan.missing_required == ('required',)
    assert plan.slices[0].document()['payload']['body_base64'] == 'ZGF0YQ=='
    assert json.loads(plan.canonical)['authority'] == 'preparation_only'
    assert plan.sha256 == CampaignSlicePlan.from_artifacts(projection).sha256


def test_all_owner_lanes_keep_required_before_optional_and_do_not_overwrite_science():
    selection, peer = selected()
    graph = CampaignKnowledgeReader(peer).read(selection)
    exact = ObservedRelease.bind(record(status='revoked').model_copy(update={'revision': 2}), SCOPE)
    plan = (empty().with_research(context(omitted=('question',)), (view(),))
            .with_registry(scan(), (exact,)).with_runtime(runtime(True)).with_graph(graph).with_retrieval(retrieval()))
    rows = [row.document() for row in plan.slices]
    assert [row['required'] for row in rows] == sorted((row['required'] for row in rows), reverse=True)
    assert next(row for row in rows if row['lane'] == 'research')['payload']['findings']
    assert next(row for row in rows if row['lane'] == 'registry_inventory')['payload']['status'] == 'registered'
    assert next(row for row in rows if row['lane'] == 'registry_exact')['payload']['status'] == 'revoked'
    assert next(row for row in rows if row['lane'] == 'runtime_schema')['payload']['status'] == 'unavailable'
    assert next(row for row in rows if row['lane'] == 'graph')['payload']['observations']
    assert len(plan.missing_required) == len(empty().missing_required)
    assert len(plan.sha256) == 64
    # A caller's decoded copy cannot mutate prepared data.
    rows[-1]['payload'].clear()
    assert plan.slices[-1].document()['payload']


def test_unavailable_owner_results_are_explicit_data_not_scientific_vetoes():
    selection, peer = selected()
    graph = replace(CampaignKnowledgeReader(peer).read(selection), context=None, failure='knowledge_access_denied')
    plan = empty().with_graph(graph).with_runtime_unavailable('metadata_denied').with_retrieval(retrieval('metadata_missing'))
    for lane in ('graph', 'runtime', 'retrieval'):
        row = next(row for row in plan.slices if row.lane == lane)
        assert row.document()['payload']['status'] == 'unavailable'
    assert plan.missing_required == empty().missing_required


@pytest.mark.parametrize('family', ['research', 'registry', 'runtime', 'retrieval', 'graph'])
def test_different_original_request_cannot_be_mixed_even_in_same_scope(family):
    value = request().document().model_dump(mode='json')
    value['reference']['engagement_id'] = 'different'
    plan = empty(request(value))
    selection, peer = selected()
    operations = {'research': lambda: plan.with_research(context()), 'registry': lambda: plan.with_registry(scan()),
        'runtime': lambda: plan.with_runtime(runtime()), 'retrieval': lambda: plan.with_retrieval(retrieval()),
        'graph': lambda: plan.with_graph(CampaignKnowledgeReader(peer).read(selection))}
    with pytest.raises(ValueError, match='request'):
        operations[family]()


def test_duplicate_lane_selection_cannot_silently_replace_prior_results():
    plan = empty().with_registry(scan())
    with pytest.raises(ValueError, match='family_duplicate'):
        plan.with_registry(scan())
    assert plan.families == ('artifacts', 'registry')


def test_original_omissions_survive_without_becoming_candidates():
    value = original()
    value['context']['omissions'] = [{'artifact': entry('omitted')['artifact'], 'reason': 'not_relevant'}]
    bound = request(value)
    plan = empty(bound)
    assert json.loads(plan.canonical)['original_omissions'] == value['context']['omissions']
    assert not any(row.document()['identity']['artifact_id'] == 'omitted' for row in plan.slices)


def test_adapter_revalidates_artifact_projection_before_capturing_it():
    source = CampaignArtifactContextReader(Data()).read(request(original())).projection
    forged = replace(source, items=(replace(source.items[0], body=b'evil'), *source.items[1:]))
    with pytest.raises(ValueError, match='bytes'):
        CampaignSlicePlan.from_artifacts(forged)


def test_slice_count_duplicate_and_aggregate_limits_are_explicit_not_truncation():
    one = ContextSlice._capture('artifact', {'id': 'one'}, {'data': 'text'}, False)
    with pytest.raises(ValueError, match='count_or_duplicate'):
        ordered((one, one))
    rows = tuple(replace(one, identity=str(i).encode()) for i in range(901))
    with pytest.raises(ValueError, match='count_or_duplicate'):
        ordered(rows)
    # Reuse immutable bytes to exercise the aggregate ceiling without allocating 128MiB.
    large = b'x' * 1048576
    rows = tuple(replace(one, identity=str(i).encode(), payload=large) for i in range(129))
    with pytest.raises(ValueError, match='slice_total'):
        ordered(rows)
