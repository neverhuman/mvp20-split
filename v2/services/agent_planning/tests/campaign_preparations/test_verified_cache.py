"""Exact historical bytes may reuse proof; changed inputs and DTOs cannot poison it."""
import json
from dataclasses import FrozenInstanceError, replace

import pytest
from amphora_agent_planning.campaign_context.records import canonical
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from amphora_agent_planning.campaign_preparations.packet import PacketEvidence
from amphora_agent_planning.context import RequestSnapshot
from .test_records import original, read


@pytest.fixture(autouse=True)
def clear_cache():
    CampaignPreparation._verified.cache_clear()
    yield
    CampaignPreparation._verified.cache_clear()


def test_exact_bytes_reuse_one_verified_immutable_record(monkeypatch):
    record = original()
    CampaignPreparation._verified.cache_clear()
    original_bind = PacketEvidence.bind
    calls = []

    def bind(request, raw):
        calls.append(raw)
        return original_bind(request, raw)

    monkeypatch.setattr(PacketEvidence, 'bind', bind)
    first = read(record)
    for _ in range(4):
        assert read(record) is first
    assert len(calls) == 1
    with pytest.raises(FrozenInstanceError):
        first.canonical = b'changed'
    with pytest.raises(FrozenInstanceError):
        first.packet.request.canonical = b'changed'
    projection = first.document().model_dump(mode='json')
    projection['candidates'].clear()
    context = first.packet.context()
    context['slices'].clear()
    assert read(record).document().candidates and read(record).packet.context()['slices']


def test_every_input_byte_is_part_of_the_key_and_failures_do_not_cache():
    record = original()
    assert read(record) == record
    for _ in range(2):
        with pytest.raises(ValueError):
            read(record, packet=record.packet.canonical + b'\n')
        with pytest.raises(ValueError):
            read(record, manifest=record.canonical + b'\n')
        with pytest.raises(ValueError):
            CampaignPreparation.from_bytes(replace(record.packet.request, canonical=b'{}'),
                                           record.canonical, record.packet.canonical)
    assert read(record) == record
    assert CampaignPreparation._verified.cache_info().currsize == 1


def test_single_entry_is_evicted_without_mixing_distinct_manifests():
    record = original()
    first = read(record)
    manifest = json.loads(record.canonical)
    # Plan SHA is retained history, not reconstructed from omitted plan bodies.
    manifest['plan_sha256'] = 'f' * 64
    second = read(record, manifest=canonical(manifest))
    assert second.document().plan_sha256 == 'f' * 64
    assert second != first
    assert CampaignPreparation._verified.cache_info().currsize == 1
    restored = read(record)
    assert restored == first and restored is not first


def test_another_valid_actor_request_cannot_reuse_historical_proof():
    record = original()
    value = json.loads(record.packet.request.canonical)
    value['actor_id'] = 'other-researcher'
    request = RequestSnapshot.from_bytes(canonical(value), actor_id='other-researcher',
                                         scope=record.packet.request.document().reference.scope)
    with pytest.raises(ValueError):
        CampaignPreparation.from_bytes(request, record.canonical, record.packet.canonical)
    assert read(record) == record


@pytest.mark.parametrize('raw', [bytearray(b'{}'), None, b'', b'x' * 8388609],
                         ids=['mutable-bytes', 'null', 'empty', 'oversized'])
def test_unhashable_or_oversized_packet_keeps_value_error_boundary(raw):
    record = original()
    with pytest.raises(ValueError, match='campaign_preparation_size'):
        CampaignPreparation.from_bytes(record.packet.request, record.canonical, raw)
