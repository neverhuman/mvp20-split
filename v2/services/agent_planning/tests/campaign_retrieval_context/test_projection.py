import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_retrieval_context import RetrievalContext
from amphora_agent_planning.retrieval_access import RetrievalReader

from ..campaign_context.test_selection import request
from ..registry_access.test_discovery import Scripted
from ..retrieval_access.test_reader import record, selected


def observed(failure=None):
    return RetrievalReader(Scripted(record() if failure is None else ValueError(failure))).read(selected())


def test_full_retained_query_result_and_source_vector_provenance_are_unchanged():
    result = observed()
    projection = RetrievalContext.bind(request(), result)
    value = json.loads(projection.canonical)
    assert value['record'] == record().model_dump(mode='json') and value['query'] == selected().document().model_dump(mode='json')
    assert value['result_sha256'] == record().sha256 and value['authority'] == 'retained_selection_only'
    assert len(projection.sha256) == 64
    assert all(row['score'] == -2.0 for row in value['record']['matches'])


@pytest.mark.parametrize('reason', ['metadata_denied', 'metadata_missing', 'metadata_unavailable', 'metadata_deadline'])
def test_unavailability_is_explicit_without_inventing_empty_matches(reason):
    value = json.loads(RetrievalContext.bind(request(), observed(reason)).canonical)
    assert value['status'] == 'unavailable' and value['record'] is None and value['reason'] == reason


@pytest.mark.parametrize('fault,reason', [('request', 'request'), ('shape', 'shape'), ('selection', 'selection'), ('failure', 'failure')])
def test_mixed_requests_and_contradictory_observation_shapes_reject(fault, reason):
    result = observed()
    original = request()
    if fault == 'request':
        value = original.document().model_dump(mode='json')
        value['reference']['engagement_id'] = 'different'
        original = request(value)
    elif fault == 'shape':
        result = replace(result, failure='metadata_denied')
    elif fault == 'selection':
        result = replace(result, record=replace(result.record, selection=replace(result.selection, result_sha256='f' * 64)))
    else:
        result = replace(result, record=None, failure='secret arbitrary failure')
    with pytest.raises(ValueError, match='campaign_retrieval_' + reason):
        RetrievalContext.bind(original, result)
