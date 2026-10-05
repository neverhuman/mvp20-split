"""Predeclared300-descriptor scan/packet oracles; no natural-language quality score."""

import json
import time

import pytest
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_proposals.tools import ConsumedTools
from amphora_agent_planning.registry_access import DiscoveryQuery
from amphora_agent_planning.runtime_metadata import ReviewedUniverse
from pydantic import ValidationError

from ..campaign_output.test_output import output
from ..campaign_proposals.test_composition import revised_universe
from ..campaign_proposals.test_evidence import prepared
from ..campaign_proposals.test_prepared import source
from .support import catalog, hosted


def test_300_descriptor_complete_scan_exact_target_and_budgeted_packet(record_property):
    target, records = catalog()
    selected = source(maximum=500000)
    with hosted(records) as (reader, calls):
        start = time.monotonic()
        scan = reader.discover(DiscoveryQuery(selected.request, limit=100, max_pages=4))
        discovery_seconds = time.monotonic() - start
        assert scan.complete and len(scan.records) == 300 and scan.pages == scan.calls == 3
        assert scan.failure is None and scan.next_after is None and discovery_seconds < 30
        exact = reader.exact(selected.request, target.lock)
        assert len(calls) == 4 and calls[-1] == '/v1/releases/' + target.lock.descriptor_sha256
    assert sum(row.document().lock.tool == target.lock.tool for row in scan.records) == 1
    assert len({row.document().descriptor.tool.purpose for row in scan.records}) == 1
    selected = selected.with_registry(scan, (exact,))
    start = time.monotonic()
    result = prepare(selected)
    prepare_seconds = time.monotonic() - start
    assert result.packet is not None and result.failure is None and prepare_seconds < 60
    packet = result.packet
    payload = json.loads(packet.canonical)['untrusted_context']
    included = [row for row in payload['slices'] if row['lane'] == 'registry_inventory']
    omitted = [row for row in payload['budget_omissions'] if row['lane'] == 'registry_inventory']
    assert included and omitted and len(included) + len(omitted) == 300
    assert len(packet.canonical) <= 500000 and packet.fit.document()['output_reserve'] == 16
    assert len([row for row in payload['slices'] if row['lane'] == 'registry_exact']) == 1
    observed = {json.dumps(row['identity'], sort_keys=True) for row in payload['consumed_observations']
                if row['lane'] == 'registry_inventory'}
    assert observed == {json.dumps(row['identity'], sort_keys=True) for row in included}
    assert not observed & {json.dumps(row['identity'], sort_keys=True) for row in omitted}
    start = time.monotonic()
    assert prepare(selected).packet == packet
    assert time.monotonic() - start < 60
    value = output('abstain')
    value['unresolved'] = []
    tools = ConsumedTools.from_proposal(prepared(selected, value))
    chosen = tools.release(target.lock.tool)
    assert chosen.lane == 'registry_exact' and chosen.record.document().lock == target.lock
    with pytest.raises(ValueError, match='campaign_tool_not_consumed_or_ambiguous'):
        tools.release(target.lock.tool.model_copy(update={'image_sha256': '0' * 64}))
    for key, measured in {'descriptors':300, 'matching_identities':1, 'false_identity_matches':0,
        'included_inventory':len(included), 'omitted_inventory':len(omitted), 'packet_bytes':len(packet.canonical),
        'scan_bytes':scan.bytes, 'discovery_seconds':discovery_seconds, 'prepare_seconds':prepare_seconds}.items():
        record_property(key, measured)


def test_300_descriptor_partial_scan_and_required_metadata_overflow(record_property):
    target, records = catalog()
    selected = source(maximum=10000)
    with hosted(records) as (reader, calls):
        scan = reader.discover(DiscoveryQuery(selected.request, limit=100, max_pages=2))
        assert not scan.complete and scan.failure is None and len(scan.records) == 200 and len(calls) == 2
        assert scan.next_after == records[199].lock.descriptor_sha256
        exact = reader.exact(selected.request, target.lock)
    selected = selected.with_registry(scan, (exact,))
    before = selected.canonical
    result = prepare(selected)
    assert result.packet is None and result.failure == 'required_input_limit'
    assert selected.canonical == before
    record_property('verified_partial_descriptors', 200)
    record_property('unread_descriptors', 100)


def test_large_inventory_does_not_expand_reviewed_compiler_tool_limit():
    _, records = catalog()
    selected = source(maximum=500000)
    def reviewed(count):
        return revised_universe(lambda value: value.update(
            reviewed_tools=[row.lock.model_dump(mode='json') for row in records[:count]]))
    accepted = ReviewedUniverse.bind(reviewed(64), selected.request)
    assert len(accepted.document().reviewed_tools) == 64
    with pytest.raises(ValidationError, match='reviewed_tools'):
        reviewed(65)
