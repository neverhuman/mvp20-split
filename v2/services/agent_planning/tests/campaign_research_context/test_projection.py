import copy
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_context import ResearchContext, ResearchSelection
from amphora_agent_planning.campaign_research_context import CampaignResearchProjection
from amphora_agent_planning.research_view_access import ViewPage, ViewSelection
from amphora_agent_planning.research_view_access.reader import ViewReadResult

from ..campaign_context.test_records import context, selected, values, wire
from ..campaign_context.test_selection import request
from ..research_view_access.test_views import inputs, page_model


def result(view='specimens', failure=None):
    selection, raw, _ = inputs(view)
    page = None if failure else ViewPage.bind(selection, page_model(selection, raw))
    return ViewReadResult(selection, page, failure, 1, 0)


def test_scientific_posture_and_all_exact_named_fields_are_preserved():
    original = context()
    pages = tuple(result(view) for view in ('specimens', 'properties', 'observation_series'))
    projection = CampaignResearchProjection.bind(original, pages)
    value = json.loads(projection.canonical)
    assert value['research'] == json.loads(original.canonical)
    assert [row['page'] for row in value['views']] == [json.loads(page.page.canonical) for page in pages]
    assert value['authority'] == 'selected_metadata_only'
    assert [row['result_schema']['schema_id'] for row in value['views']] == [
        'research-views.specimen-view-page', 'research-views.property-view-page', 'research-views.observation-series-page']
    assert len(projection.sha256) == 64 and not projection.changes(CampaignResearchProjection.bind(original, pages))
    value['research']['records'].clear()
    assert len(json.loads(projection.canonical)['research']['records']) == 3


def test_caller_cannot_remove_dependency_findings_from_selected_gaps():
    original = context(omitted=('question',))
    assert original.findings
    projection = CampaignResearchProjection.bind(replace(original, findings=()))
    assert projection.context.findings == original.findings and projection.context.gaps == original.gaps
    assert len(projection.context.records) == 2


@pytest.mark.parametrize('status', ['pending', 'failed'])
def test_incomplete_assessment_remains_an_explicit_gap(status):
    data = values()
    data['assessment']['outcome'] = {'status': status, **({'code': 'fixture_unavailable'} if status == 'failed' else {})}
    original = context(data, selected())
    projection = CampaignResearchProjection.bind(original)
    assert projection.context.gaps[0].reason == status and len(projection.context.records) == 2


@pytest.mark.parametrize('reason', ['research_access_denied', 'research_reference_unavailable', 'research_read_expired', 'research_view_invalid'])
def test_unavailable_page_retains_useful_scientific_context_and_named_reason(reason):
    projection = CampaignResearchProjection.bind(context(), (result(failure=reason),))
    value = json.loads(projection.views[0].canonical)
    assert value['page'] is None and value['status'] == 'unavailable' and value['reason'] == reason
    assert len(projection.context.records) == 3
    assert [change.kind for change in projection.changes(CampaignResearchProjection.bind(context(), (result(),)))] == ['view']


def test_relevance_compares_original_pages_not_unrelated_added_views():
    original = CampaignResearchProjection.bind(context(), (result(),))
    future = CampaignResearchProjection.bind(context(), (result(), result('properties')))
    assert not original.changes(future)
    assert original.sha256 != future.sha256
    assert [row.kind for row in future.changes(original)] == ['view']
    other_request = request().document().model_dump(mode='json')
    other_request['reference']['engagement_id'] = 'future'
    old_page = result()
    rebound = ViewSelection.bind(old_page.selection.document(), request(other_request))
    # Full mixed-request projection is forbidden, even if page queries are identical.
    with pytest.raises(ValueError, match='campaign_research_view_request'):
        CampaignResearchProjection.bind(context(), (replace(old_page, selection=rebound),))


def test_duplicate_counts_and_contradictory_outcomes_fail():
    page = result()
    with pytest.raises(ValueError, match='campaign_research_duplicate_view'):
        CampaignResearchProjection.bind(context(), (page, page))
    with pytest.raises(ValueError, match='campaign_research_view_count'):
        CampaignResearchProjection.bind(context(), (page,) * 33)
    with pytest.raises(ValueError, match='campaign_research_view_shape'):
        CampaignResearchProjection.bind(context(), (replace(page, failure='research_access_denied'),))
    with pytest.raises(ValueError, match='campaign_research_view_reason'):
        CampaignResearchProjection.bind(context(), (replace(page, page=None, failure='secret error'),))


def test_tampered_page_and_hidden_different_selection_are_revalidated():
    page = result()
    raw = json.loads(page.page.canonical)
    raw['query_sha256'] = 'f' * 64
    with pytest.raises(ValueError, match='research_view_identity'):
        CampaignResearchProjection.bind(context(), (replace(page, page=replace(page.page, canonical=json.dumps(raw).encode())),))
    with pytest.raises(ValueError, match='campaign_research_view_selection'):
        CampaignResearchProjection.bind(context(), (replace(page, page=replace(page.page, selection=result('properties').selection)),))


def test_page_position_is_an_explicit_observation_and_never_implicitly_fetched():
    selection, raw, _ = inputs('observation_series')
    query = selection.document().model_copy(update={'limit': 1})
    first = ViewSelection.bind(query, selection.request)
    raw.update(request=first.document().model_dump(mode='json'), query_sha256=first.query_sha256, total=2,
               points=raw['points'][:1], next_position={'query_sha256': first.query_sha256, 'offset': 1})
    first_page = ViewPage.bind(first, page_model(first, raw))
    projection = CampaignResearchProjection.bind(context(), (ViewReadResult(first, first_page, None, 1, 0),))
    observed = json.loads(projection.views[0].canonical)
    assert observed['page']['next_position']['offset'] == 1 and len(observed['page']['points']) == 1
    assert len(projection.views) == 1


def test_individually_valid_large_records_and_pages_cannot_exceed_aggregate_cap():
    questions = []
    for n in range(50):
        row = copy.deepcopy(values()['question'])
        row['reference']['question_id'] = f'question-{n}'
        row['criteria'] = [{'criterion_id': f'criterion-{i}', 'description': 'x' * 2048} for i in range(32)]
        questions.append(wire('question', row))
    selection = selected().document().model_copy(update={'questions': tuple(row.reference for row in questions), 'needs': (), 'assessments': ()})
    research = ResearchContext.bind(ResearchSelection.from_bytes(selection.model_dump_json().encode(), request()), questions=tuple(questions))
    assert len(research.canonical) < 4194304
    chosen, template, _ = inputs('properties')
    pages = []
    for n in range(32):
        raw = copy.deepcopy(template)
        rows = []
        for i in range(16):
            row = copy.deepcopy(raw['rows'][0])
            row['reference']['observation_id'] = f'large-{n}-{i}'
            row['quality']['flags'] = [f'flag-{k}-'.ljust(128, 'x') for k in range(64)]
            rows.append(row)
        query = chosen.document().model_dump(mode='json')
        query.update(observations=[row['reference'] for row in rows], limit=16, position=None)
        selected_page = ViewSelection.bind(type(chosen.document()).model_validate_json(json.dumps(query)), request())
        raw.update(request=query, query_sha256=selected_page.query_sha256, total=16, rows=rows, next_position=None)
        page = ViewPage.bind(selected_page, page_model(selected_page, raw))
        pages.append(ViewReadResult(selected_page, page, None, 1, len(page.canonical)))
    assert sum(len(page.page.canonical) for page in pages) + len(research.canonical) > 8388608
    with pytest.raises(ValueError, match='campaign_research_projection_limit'):
        CampaignResearchProjection.bind(research, tuple(pages))
