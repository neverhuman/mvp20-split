import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_tool_context import RegistryContext
from amphora_agent_planning.registry_access import (
    DiscoveryQuery,
    ObservedRelease,
    RegistryReader,
)
from amphora_contracts_tools import ReleasePage

from ..campaign_context.test_selection import SCOPE, request
from ..registry_access.test_discovery import Scripted, record


def scan(*, complete=True, failure=None):
    row = record()
    transport = Scripted(ReleasePage(items=(row,), next_after=None if complete else row.lock.descriptor_sha256))
    return RegistryReader(transport).discover(DiscoveryQuery(request(), limit=1, max_pages=1))


def test_inventory_and_later_exact_lifecycle_observations_are_distinct():
    result = scan()
    exact = ObservedRelease.bind(record(status='revoked').model_copy(update={'revision': 2}), SCOPE)
    projection = RegistryContext.bind(result, (exact,))
    value = json.loads(projection.canonical)
    assert value['inventory'][0]['status'] == 'registered' and value['exact'][0]['status'] == 'revoked'
    assert value['complete'] and value['next_after'] is None and value['authority'] == 'observed_inventory_only'
    assert len(projection.sha256) == 64 and projection.request == request()


def test_incomplete_scan_and_later_page_failure_preserve_verified_inventory():
    result = scan(complete=False)
    bounded = json.loads(RegistryContext.bind(result).canonical)
    assert not bounded['complete'] and bounded['failure'] is None and bounded['next_after'] == record().lock.descriptor_sha256
    partial = replace(result, query=replace(result.query, max_pages=2), failure='metadata_unavailable')
    failed = json.loads(RegistryContext.bind(partial).canonical)
    assert failed['inventory'] == bounded['inventory'] and failed['failure'] == 'metadata_unavailable'
    empty = RegistryReader(Scripted(ValueError('metadata_denied'))).discover(DiscoveryQuery(request()))
    value = json.loads(RegistryContext.bind(empty).canonical)
    assert not value['inventory'] and value['failure'] == 'metadata_denied'


@pytest.mark.parametrize('fault,reason', [
    ('pages', 'scan_shape'), ('complete', 'completion'), ('cursor', 'completion'), ('incomplete', 'continuation'),
    ('unexplained', 'incomplete'), ('error', 'failure'), ('filter', 'filter'), ('duplicate', 'order'),
])
def test_forged_scan_summary_cannot_change_observed_meaning(fault, reason):
    result = scan()
    if fault == 'pages':
        result = replace(result, pages=True)
    elif fault == 'complete':
        result = replace(result, failure='metadata_denied')
    elif fault == 'cursor':
        result = replace(result, next_after='f' * 64)
    elif fault == 'incomplete':
        result = replace(result, complete=False)
    elif fault == 'unexplained':
        result = replace(scan(complete=False), query=replace(result.query, max_pages=2))
    elif fault == 'error':
        result = replace(result, failure='secret failure')
    elif fault == 'filter':
        result = replace(result, query=replace(result.query, capability_id='unrelated'))
    else:
        result = replace(result, records=(result.records[0], result.records[0]), query=replace(result.query, limit=2))
    with pytest.raises(ValueError, match='campaign_registry_' + reason):
        RegistryContext.bind(result)


def test_exact_duplicates_count_and_foreign_records_reject():
    result = scan()
    row = result.records[0]
    with pytest.raises(ValueError, match='campaign_registry_exact_duplicate'):
        RegistryContext.bind(result, (row, row))
    with pytest.raises(ValueError, match='campaign_registry_exact_count'):
        RegistryContext.bind(result, (row,) * 65)
    raw = json.loads(row.canonical)
    raw['scope']['project_id'] = 'foreign'
    with pytest.raises(ValueError, match='registry_scope'):
        RegistryContext.bind(result, (replace(row, canonical=json.dumps(raw).encode()),))


def test_failure_cannot_claim_an_extra_call_after_all_allowed_pages_succeeded():
    with pytest.raises(ValueError, match='campaign_registry_failure_position'):
        RegistryContext.bind(replace(scan(complete=False), failure='metadata_unavailable'))
