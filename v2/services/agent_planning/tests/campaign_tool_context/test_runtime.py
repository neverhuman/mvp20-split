import base64
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_tool_context import RuntimeContext
from amphora_agent_planning.runtime_metadata import RuntimeMetadataReader

from ..campaign_context.test_selection import request
from ..registry_access.test_discovery import Scripted
from ..runtime_metadata.test_reader import schema, selected


def observed(partial=False):
    universe = selected()
    return RuntimeMetadataReader(Scripted(ValueError('metadata_missing') if partial else schema(), schema(1))).schemas(
        universe, universe.document().schemas)


def test_exact_schema_bytes_and_partial_gaps_retain_original_selection_order():
    result = observed(True)
    projection = RuntimeContext.bind(result)
    value = json.loads(projection.canonical)
    assert value['universe'] == result.universe.document().model_dump(mode='json')
    assert value['schemas'][0]['status'] == 'unavailable' and value['schemas'][0]['reason'] == 'metadata_missing'
    assert base64.b64decode(value['schemas'][1]['record']['schema_bytes_base64']) == result.records[0].body
    assert value['authority'] == 'compiler_configuration_only' and len(projection.sha256) == 64


def test_missing_whole_universe_is_explicit_without_fake_empty_catalog():
    value = json.loads(RuntimeContext.unavailable(request(), 'metadata_denied').canonical)
    assert value['status'] == 'unavailable' and 'universe' not in value
    with pytest.raises(ValueError, match='campaign_runtime_failure'):
        RuntimeContext.unavailable(request(), 'secret error')


@pytest.mark.parametrize('fault,reason', [
    ('count', 'schema_count'), ('duplicate', 'schema_selection'), ('coverage', 'schema_coverage'),
    ('outcome', 'schema_outcome'), ('body', 'schema_bytes'), ('universe', 'schema_universe'), ('failure', 'failure'),
])
def test_complete_selected_schema_outcome_coverage_is_required(fault, reason):
    result = observed(fault == 'failure')
    if fault == 'count':
        result = replace(result, selected=result.selected * 129)
    elif fault == 'duplicate':
        result = replace(result, selected=(result.selected[0], result.selected[0]))
    elif fault == 'coverage':
        result = replace(result, records=result.records[:1])
    elif fault == 'outcome':
        result = replace(result, records=(result.records[0], result.records[0]))
    elif fault == 'body':
        result = replace(result, records=(replace(result.records[0], body=b'false'), result.records[1]))
    elif fault == 'universe':
        value = request().document().model_dump(mode='json')
        value['reference']['engagement_id'] = 'different'
        wrong = replace(result.universe, request=request(value))
        result = replace(result, records=(replace(result.records[0], universe=wrong), result.records[1]))
    else:
        result = replace(result, failures=(replace(result.failures[0], code='secret'),))
    with pytest.raises(ValueError, match='campaign_runtime_' + reason):
        RuntimeContext.bind(result)
