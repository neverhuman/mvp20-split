import base64
import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from amphora_agent_planning.campaign_context.records import canonical
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from amphora_agent_planning.campaign_preparations.packet import PacketEvidence

from ..campaign_packet.replay_probe import source
from ..campaign_packet.test_assembly import plan

FIXTURE = Path(__file__).parents[1] / 'campaign_packet/fixtures/predecessor-v1.json'


def original():
    selected = source(json.loads(FIXTURE.read_bytes()))
    return CampaignPreparation.bind(selected, prepare(selected).packet)


def read(record, manifest=None, packet=None):
    return CampaignPreparation.from_bytes(record.packet.request, record.canonical if manifest is None else manifest,
        record.packet.canonical if packet is None else packet)


def test_exact_predecessor_roundtrip_has_bounded_metadata_without_omitted_raw_bodies():
    record = original()
    value = record.document()
    assert value.packet.sha256 == 'f137c66a058fa7e53a019534b804438c10f27be6b1bc0ca22ef8a3826b3c96b2'
    assert value.plan_sha256 == '3a917e2593f7303e114b03e47b3ce93b8fabe674ecf83facc95856489292ede3'
    assert value.authority == 'historical_input_only'
    assert read(record) == record and len(record.sha256) == 64
    omitted = next(row for row in value.candidates if not row.included)
    assert omitted.identity['artifact_id'] == 'large' and not omitted.observations
    assert base64.b64encode(b'x' * 16000) not in record.canonical
    assert len(record.canonical) < 20000
    copied = value.model_dump(mode='json')
    copied['candidates'].clear()
    assert record.document().candidates


@pytest.mark.parametrize('raw', [b'', b'[]', b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'{}\n', b'x' * 2097153],
    ids=['empty', 'array', 'duplicate', 'nonfinite', 'utf8', 'noncanonical', 'oversized'])
def test_strict_bounded_manifest_encoding(raw):
    with pytest.raises(ValueError):
        read(original(), manifest=raw)


@pytest.mark.parametrize('fault', ['profile', 'unknown', 'request', 'packet', 'fit', 'duplicate', 'required', 'observations', 'omission'])
def test_changed_manifest_cannot_relabel_request_fit_consumption_or_required_context(fault):
    record = original()
    value = json.loads(record.canonical)
    if fault == 'profile':
        value['profile'] = 'unknown'
    elif fault == 'unknown':
        value['injected'] = True
    elif fault == 'request':
        value['request_sha256'] = '0' * 64
    elif fault == 'packet':
        value['packet']['sha256'] = '0' * 64
    elif fault == 'fit':
        value['packet']['fit']['output_reserve'] = 0
    elif fault == 'duplicate':
        value['candidates'].append(copy.deepcopy(value['candidates'][0]))
    elif fault == 'required':
        value['candidates'][0]['included'] = False
    elif fault == 'observations':
        value['candidates'][0]['observations'].clear()
    else:
        next(row for row in value['candidates'] if not row['included'])['payload_sha256'] = '0' * 64
    with pytest.raises(ValueError):
        read(record, manifest=canonical(value))


@pytest.mark.parametrize('fault', ['profile', 'instruction', 'request', 'omissions', 'unknown', 'noncanonical', 'empty', 'oversized'])
def test_packet_profile_instruction_request_and_original_omissions_remain_bound(fault):
    record = original()
    value = json.loads(record.packet.canonical)
    if fault == 'profile':
        value['format'] = 'invented'
    elif fault == 'instruction':
        value['trusted_instructions'] = 'run arbitrary code'
    elif fault == 'request':
        value['untrusted_context']['request']['actor_id'] = 'foreign'
    elif fault == 'omissions':
        value['untrusted_context']['original_omissions'] = [{'reason': 'invented'}]
    elif fault == 'unknown':
        value['extra'] = 'ignored?'
    raw = canonical(value)
    if fault == 'noncanonical':
        raw += b'\n'
    elif fault == 'empty':
        raw = b''
    elif fault == 'oversized':
        raw = b'x' * 8388609
    with pytest.raises(ValueError):
        read(record, packet=raw)


def test_rehashed_packet_and_candidate_still_cannot_change_artifact_body():
    record = original()
    packet = json.loads(record.packet.canonical)
    row = packet['untrusted_context']['slices'][0]
    row['payload']['body_base64'] = base64.b64encode(b'corrupt').decode()
    raw = canonical(packet)
    manifest = json.loads(record.canonical)
    manifest['packet'] = PacketEvidence.bind(record.packet.request, raw).summary()
    manifest['candidates'][0]['payload_sha256'] = hashlib.sha256(canonical(row['payload'])).hexdigest()
    with pytest.raises(ValueError, match='artifact_context_bytes'):
        read(record, manifest=canonical(manifest), packet=raw)


def test_factory_rejects_forged_inclusion_and_preserves_prompt_additional_role():
    selected = plan(prompt_role=True)
    packet = prepare(selected).packet
    assert CampaignPreparation.bind(selected, packet).document().candidates
    with pytest.raises(ValueError, match='packet_binding'):
        CampaignPreparation.bind(selected, replace(packet, included=()))


def test_optional_unavailable_artifact_remains_an_observed_gap():
    from amphora_agent_planning.campaign_artifact_context import (
        ArtifactContextItem,
        ArtifactContextPlan,
        ArtifactContextProjection,
    )
    from amphora_agent_planning.campaign_packet.assembly import original_artifacts
    from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan

    selected = plan(extras=(('gap', b'unknown', False),))
    artifacts = original_artifacts(selected)
    items = (*artifacts.items[:-1], ArtifactContextItem.unavailable(artifacts.items[-1].planned, 'source_access_denied'))
    projection = ArtifactContextProjection.bind(ArtifactContextPlan.bind(selected.request), items)
    selected = CampaignSlicePlan.from_artifacts(projection)
    record = CampaignPreparation.bind(selected, prepare(selected).packet)
    assert read(record) == record
    assert json.loads(record.packet.canonical)['untrusted_context']['slices'][-1]['payload']['reason'] == 'source_access_denied'
