"""Only exact prepared inputs and retained raw output can form a candidate."""

import base64
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_artifact_context import (
    ArtifactContextItem,
    ArtifactContextPlan,
    ArtifactContextProjection,
)
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from amphora_agent_planning.campaign_proposals import (
    ObservedInputs,
    PreparedCampaignProposal,
)
from amphora_agent_planning.campaign_proposals.observations import ObservationKey
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
from amphora_agent_planning.campaign_slice_plan.slices import ContextSlice, ordered
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.capture import Observation
from amphora_contracts_core import Scope
from amphora_contracts_planning import campaign_draft_schema

from ..campaign_context.test_selection import request
from ..campaign_output.test_output import output
from ..campaign_packet.test_assembly import plan
from ..providers.test_task_output import Response


def source(name='future', **kwargs):
    original = plan(**kwargs)
    value = original.request.document().model_dump(mode='json')
    value.update(decision_scope='d' * 64, purpose='supervision' if name == 'adjustment' else 'campaign_proposal',
                 runtime_cut=output('adjustment')['candidate']['cut'] if name == 'adjustment' else None)
    value['context']['output_schema'] = campaign_draft_schema().model_dump(mode='json')
    value['context']['allowed_actions'] = ['abstain', 'request_evidence', 'propose_campaign']
    return replace(original, request=request(value))


def record(selected=None):
    selected = source() if selected is None else selected
    return CampaignPreparation.bind(selected, prepare(selected).packet)


def proposal(name='future'):
    preparation = record(source(name))
    binding = AttemptBinding(preparation.packet.request, 1)
    observed = observe(binding, Response(json.dumps(output(name)).encode()))
    return PreparedCampaignProposal.bind(preparation, binding, observed)


@pytest.mark.parametrize('name', ['future', 'adjustment', 'evidence', 'abstain'])
def test_prepared_output_retains_exact_attempt_input_and_output_identity(name):
    value = proposal(name)
    assert value.output.document().action == output(name)['action']
    assert len(value.sha256) == 64
    assert PreparedCampaignProposal.bind(value.inputs.preparation, value.attempt, value.observation) == value
    assert value.inputs.preparation.packet.request == value.output.decision.request
    copied = value.inputs.preparation.packet.context()
    copied['slices'].clear()
    assert value.inputs.preparation.packet.context()['slices']


def test_request_and_physical_attempt_are_not_interchangeable():
    value = proposal()
    raw = value.attempt.request.document().model_dump(mode='json')
    raw['reference']['engagement_id'] = 'another'
    with pytest.raises(ValueError, match='campaign_proposal_request'):
        PreparedCampaignProposal.bind(value.inputs.preparation, AttemptBinding(request(raw), 1), value.observation)
    with pytest.raises(ValueError, match='attempt_binding_mismatch'):
        PreparedCampaignProposal.bind(value.inputs.preparation, AttemptBinding(value.attempt.request, 2), value.observation)


def test_unsuccessful_or_forged_output_does_not_gain_prepared_status():
    value = proposal()
    invalid = observe(value.attempt, Response(b'{'))
    with pytest.raises(ValueError, match='campaign_proposal_not_available'):
        PreparedCampaignProposal.bind(value.inputs.preparation, value.attempt, invalid)
    wire = value.observation.document().model_dump(mode='json')
    wire['proposal']['rationale'] = 'forged'
    with pytest.raises(ValueError, match='proposal_capture_mismatch'):
        PreparedCampaignProposal.bind(value.inputs.preparation, value.attempt,
            Observation(value.observation.capture, json.dumps(wire).encode()))


def test_forged_preparation_or_derived_values_cannot_be_fingerprinted():
    value = proposal()
    preparation = value.inputs.preparation
    broken = replace(preparation, packet=replace(preparation.packet, fit_bytes=b'{}'))
    with pytest.raises(ValueError, match='campaign_proposal_preparation'):
        PreparedCampaignProposal.bind(broken, value.attempt, value.observation)
    with pytest.raises(ValueError, match='campaign_proposal_binding'):
        _ = replace(value, inputs=replace(value.inputs, entries=())).sha256
    with pytest.raises(ValueError):
        PreparedCampaignProposal.bind(replace(preparation, canonical=b'{}'), value.attempt, value.observation)


def test_only_consumed_inputs_are_available_to_policy_selection():
    selected = source(maximum=20000, extras=(('omitted', b'x' * 30000, False), ('included', b'small', False)))
    observed = ObservedInputs.bind(record(selected))
    names = {json.loads(entry.key.identity)['artifact_id'] for entry in observed.entries}
    assert 'omitted' not in names and 'included' in names
    omitted = next(row for row in selected.slices if row.document()['identity']['artifact_id'] == 'omitted')
    key = ObservationKey('artifact', 'artifact', omitted.identity)
    with pytest.raises(ValueError, match='campaign_dependency_unconsumed'):
        observed.select([key])
    keys = [row.key for row in observed.entries]
    assert observed.select(keys).sha256 == observed.select(reversed(keys)).sha256
    assert observed.select([]).changes(observed) == ()
    with pytest.raises(ValueError, match='campaign_dependency_duplicate'):
        observed.select([keys[0], keys[0]])
    with pytest.raises(ValueError, match='campaign_observation_key'):
        observed.select(['model-provided-key'])


def metadata(entries):
    selected = source()
    rows = list(selected.slices)
    for lane, name, observations in entries:
        rows.append(ContextSlice._capture(lane, {'name': name}, {'synthetic': name},
            lane not in {'registry_inventory'}, observations))
    selected = replace(selected, slices=ordered(tuple(rows)))
    return ObservedInputs.bind(record(selected))


def observation(digest='a', name='selected'):
    return {'kind': 'release', 'identity': {'name': name}, 'sha256': digest * 64}


def test_equal_duplicates_coalesce_but_same_lane_conflicts_reject():
    scan = ('registry_scan', 'scan', [])
    inputs = metadata([scan, ('registry_exact', 'one', [observation(), observation()])])
    assert len([entry for entry in inputs.entries if entry.key.lane == 'registry_exact']) == 1
    with pytest.raises(ValueError, match='campaign_observation_conflict'):
        metadata([scan, ('registry_exact', 'one', [observation(), observation('b')])])


def test_inventory_and_exact_observations_keep_their_own_lane():
    inputs = metadata([('registry_scan', 'scan', []), ('registry_exact', 'one', [observation()]),
                       ('registry_inventory', 'one', [observation('b')])])
    values = [entry for entry in inputs.entries if entry.key.kind == 'release']
    assert len(values) == 2 and values[0].key != values[1].key


def test_relevant_only_comparison_reports_changed_or_missing_without_repinning():
    scan = ('registry_scan', 'scan', [])
    original = metadata([scan, ('registry_exact', 'one', [observation()]),
                         ('registry_inventory', 'unrelated', [observation('b', 'unrelated')])])
    key = next(entry.key for entry in original.entries if entry.key.lane == 'registry_exact')
    selected = original.select([key])
    fingerprint = selected.sha256
    current = metadata([scan, ('registry_exact', 'one', [observation()]),
                        ('registry_inventory', 'unrelated', [observation('c', 'unrelated')])])
    assert selected.changes(current) == ()
    changed = metadata([scan, ('registry_exact', 'one', [observation('d')])])
    change, = selected.changes(changed)
    assert change.before_sha256 == 'a' * 64 and change.after_sha256 == 'd' * 64
    missing, = selected.changes(metadata([scan]))
    assert missing.after_sha256 is None
    assert selected.sha256 == fingerprint


def test_caller_cannot_replace_observed_hash_or_readset_identity():
    inputs = ObservedInputs.bind(record())
    forged = replace(inputs, entries=(replace(inputs.entries[0], sha256='0' * 64), *inputs.entries[1:]))
    with pytest.raises(ValueError, match='campaign_observation_index'):
        forged.select([forged.entries[0].key])
    selection = inputs.select([inputs.entries[0].key])
    with pytest.raises(ValueError, match='campaign_observation_index'):
        selection.changes(forged)
    with pytest.raises(ValueError, match='campaign_read_set_binding'):
        _ = replace(inputs.select([entry.key for entry in inputs.entries]),
                    keys=tuple(reversed([entry.key for entry in inputs.entries]))).sha256


def test_comparison_cannot_substitute_another_projects_observations():
    selected = source()
    original = ObservedInputs.bind(record(selected))
    raw = selected.request.document().model_dump(mode='json')
    scope = Scope(tenant_id='planning-fixture', project_id='other')

    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}:
                value.update(scope.model_dump())
            for child in value.values():
                rescope(child)
        elif isinstance(value, list):
            for child in value:
                rescope(child)

    rescope(raw)
    request = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id='fixture', scope=scope)
    artifact_plan = ArtifactContextPlan.bind(request)
    bodies = {row.document()['identity']['artifact_id']: base64.b64decode(row.document()['payload']['body_base64'])
              for row in selected.slices}
    items = tuple(ArtifactContextItem.available(row, bodies[row.reference.artifact_id]) for row in artifact_plan.items)
    foreign = CampaignSlicePlan.from_artifacts(ArtifactContextProjection.bind(artifact_plan, items))
    with pytest.raises(ValueError, match='campaign_observation_scope'):
        original.select([original.entries[0].key]).changes(ObservedInputs.bind(record(foreign)))
