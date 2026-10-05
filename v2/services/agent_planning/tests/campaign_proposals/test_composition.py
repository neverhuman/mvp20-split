"""Tool names and similar descriptions cannot replace exact reviewed release locks."""

import copy
import hashlib
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_proposals import CompositionReview
from amphora_agent_planning.campaign_proposals.authored import AuthoredCampaign
from amphora_agent_planning.campaign_proposals.tools import (
    ConsumedRelease,
    RuntimeToolSelection,
    literal_dependencies,
    validate_invocation,
)
from amphora_agent_planning.registry_access import (
    DiscoveryQuery,
    ObservedRelease,
    RegistryReader,
)
from amphora_agent_planning.runtime_metadata import (
    ReviewedUniverse,
    RuntimeMetadataReader,
)
from amphora_agent_planning.runtime_metadata.universe import canonical
from amphora_contracts_graph_runtime import DefinitionUniverse
from amphora_contracts_planning import CampaignNodeAddress, FutureCampaignDraft
from amphora_contracts_tools import ReleasePage, ReleaseSnapshot

from ..campaign_output.test_output import output
from ..registry_access.test_discovery import Scripted
from ..registry_access.test_discovery import record as release_record
from ..runtime_metadata.test_reader import universe
from .test_evidence import inputs as research_inputs
from .test_evidence import prepared
from .test_prepared import source


def metadata(selected, *, inventory=True, exact=False, status='registered', runtime=True, reviewed=None):
    release = release_record(status=status)
    if inventory or exact:
        scan = RegistryReader(Scripted(ReleasePage(items=(release,) if inventory else (), next_after=None))).discover(
            DiscoveryQuery(selected.request, limit=100, max_pages=1))
        selected = selected.with_registry(scan, (ObservedRelease.bind(release, release.scope),) if exact else ())
    if runtime:
        observed = ReviewedUniverse.bind(universe() if reviewed is None else reviewed, selected.request)
        selected = selected.with_runtime(RuntimeMetadataReader(Scripted()).schemas(observed, ()))
    return selected


def documents(*, scientific=False, **kwargs):
    if scientific:
        selected, value = research_inputs()
    else:
        selected, value = source(), output()
        value['candidate']['expected_evidence'] = []
        value['unresolved'] = []
    selected = metadata(selected, **kwargs)
    release = release_record()
    port = release.descriptor.tool.inputs[0]
    result = release.descriptor.tool.outputs[0]

    def value_type(port):
        return {'kind': 'artifact', 'schema_ref': port.schema_ref.model_dump(mode='json'),
                'representation': port.representation, 'unit': port.unit, 'media_type': 'application/json'}

    value['candidate']['definition']['body'] = {
        'inputs': [{'name': 'value', 'value_type': value_type(port)}],
        'outputs': [{'name': 'result', 'value_type': value_type(result)}],
        'nodes': [{'kind': 'invoke', 'node_id': 'calculate', 'tool': release.lock.tool.model_dump(mode='json'),
                   'inputs': [{'port': port.name, 'source': {'kind': 'input', 'name': 'value'}}],
                   'checkpoint': None, 'timeout_seconds': 30},
                  {'kind': 'finish', 'node_id': 'finish', 'outputs': [
                      {'port': 'result', 'source': {'kind': 'output', 'node_id': 'calculate', 'port': result.name}}]}],
        'edges': [{'source': 'calculate', 'target': 'finish', 'route': 'next'}]}
    return selected, value


def review(**kwargs):
    selected, value = documents(**kwargs)
    return CompositionReview.bind(prepared(selected, value))


def revised_universe(change):
    raw = universe().model_dump(mode='json')
    change(raw)
    value = {'profile': 'amphora-authoring-universe-v1', 'compiler': 'amphora-deterministic-compiler-v3',
             'scope': raw['scope'], 'tools': sorted(raw['reviewed_tools'], key=canonical),
             'schemas': sorted(raw['schemas'], key=canonical)}
    raw['universe_sha256'] = hashlib.sha256(canonical(value)).hexdigest()
    return DefinitionUniverse.model_validate_json(json.dumps(raw))


def test_consumed_exact_release_and_runtime_review_are_separate_from_admission():
    result = review(exact=True)
    assert len(result.uses) == 1 and result.uses[0].release.lane == 'registry_exact'
    assert len(result.runtime.locks) == 1
    assert [entry.key.lane for entry in result.read_set.entries] == ['registry_exact']
    assert result.authored.resolve(CampaignNodeAddress(scope_path=(), node_id='calculate')).node.kind == 'invoke'
    assert not result.findings


@pytest.mark.parametrize('status', ['draining', 'revoked'])
def test_inactive_exact_release_cannot_be_promoted_by_discovery_or_name(status):
    with pytest.raises(ValueError, match='campaign_tool_lifecycle'):
        review(exact=True, status=status)


@pytest.mark.parametrize('case,code', [
    ('missing', 'campaign_tool_not_consumed_or_ambiguous'), ('image', 'campaign_tool_not_consumed_or_ambiguous'),
    ('runtime', 'campaign_tool_runtime_unavailable'), ('unreviewed', 'campaign_tool_not_reviewed'),
    ('lock', 'campaign_tool_reviewed_lock'), ('ports', 'campaign_tool_input_ports'),
    ('duplicate_input', 'campaign_tool_duplicate_input'), ('timeout', 'campaign_tool_timeout'),
    ('checkpoint', 'campaign_tool_checkpoint'), ('duplicate_node', 'campaign_authored_duplicate_node'),
])
def test_selected_release_and_basic_invocation_relationships(case, code):
    changed = None
    if case == 'unreviewed':
        changed = revised_universe(lambda raw: raw['reviewed_tools'].pop(0))
    elif case == 'lock':
        changed = revised_universe(lambda raw: raw['reviewed_tools'][0].update(descriptor_sha256='0' * 64))
    selected, value = documents(inventory=case != 'missing', runtime=case != 'runtime', reviewed=changed)
    body = value['candidate']['definition']['body']
    node = body['nodes'][0]
    if case == 'image':
        node['tool']['image_sha256'] = '0' * 64
    elif case == 'ports':
        node['inputs'][0]['port'] = 'invented'
    elif case == 'duplicate_input':
        node['inputs'] *= 2
    elif case == 'timeout':
        node['timeout_seconds'] = 31
    elif case == 'checkpoint':
        node['checkpoint'] = {'kind': 'input', 'name': 'value'}
    elif case == 'duplicate_node':
        body['nodes'].append(copy.deepcopy(node))
    with pytest.raises(ValueError, match=code):
        CompositionReview.bind(prepared(selected, value))


def test_producer_reference_resolves_in_authored_graph_not_model_text():
    selected, value = documents(scientific=True)
    value['candidate']['expected_evidence'][0]['producer'] = {'scope_path': [], 'node_id': 'calculate'}
    result = CompositionReview.bind(prepared(selected, value))
    assert not result.findings and len(result.read_set.entries) == 4
    value['candidate']['expected_evidence'][0]['producer']['node_id'] = 'invented'
    with pytest.raises(ValueError, match='campaign_producer_unknown'):
        CompositionReview.bind(prepared(selected, value))


def test_runtime_selection_ignores_unrelated_reviewed_tools_but_detects_selected_change():
    result = review()
    original = result.runtime
    unrelated = revised_universe(lambda raw: raw['reviewed_tools'].pop(1))
    assert not original.changes(ReviewedUniverse.bind(unrelated, original.universe.request))
    selected = revised_universe(lambda raw: raw['reviewed_tools'].pop(0))
    assert original.changes(ReviewedUniverse.bind(selected, original.universe.request)) == (original.locks[0].tool,)
    with pytest.raises(ValueError, match='campaign_tool_duplicate_selection'):
        RuntimeToolSelection.bind(original.universe, (original.locks[0].tool,) * 2)
    with pytest.raises(ValueError, match='campaign_runtime_selection_binding'):
        replace(original, locks=(original.locks[0].model_copy(update={'descriptor_sha256': '0' * 64}),)).changes(original.universe)


def test_unscoped_producer_and_adjustment_remain_explicit_runtime_work():
    selected, value = research_inputs()
    value.update(action='request_evidence', evidence_requests=value['candidate']['expected_evidence'], candidate=None)
    value['evidence_requests'][0]['producer'] = {'scope_path': [], 'node_id': 'unresolved-current-node'}
    result = CompositionReview.bind(prepared(selected, value))
    assert result.findings[0].code == 'runtime_producer_resolution_required'
    selected, value = source('adjustment'), output('adjustment')
    value['candidate']['expected_evidence'], value['unresolved'] = [], []
    result = CompositionReview.bind(prepared(selected, value))
    assert result.authored is None and not result.uses
    assert result.findings[0].code == 'runtime_adjustment_acceptance_required'


def test_forged_authored_index_cannot_resolve_an_invented_address():
    _selected, value = documents()
    candidate = FutureCampaignDraft.model_validate_json(json.dumps(value['candidate']))
    authored = AuthoredCampaign.bind(candidate)
    with pytest.raises(ValueError, match='campaign_authored_binding'):
        replace(authored, nodes=()).resolve(authored.nodes[0].address)


def test_newer_exact_revocation_overrides_older_inventory_observation():
    selected, value = documents(inventory=False)
    old = release_record()
    current = release_record(status='revoked').model_copy(update={'revision': 2})
    scan = RegistryReader(Scripted(ReleasePage(items=(old,), next_after=None))).discover(DiscoveryQuery(selected.request))
    selected = selected.with_registry(scan, (ObservedRelease.bind(current, current.scope),))
    with pytest.raises(ValueError, match='campaign_tool_lifecycle'):
        CompositionReview.bind(prepared(selected, value))


def test_explicit_runtime_unavailability_does_not_look_like_empty_reviewed_universe():
    selected, value = documents(runtime=False)
    selected = selected.with_runtime_unavailable('metadata_denied')
    with pytest.raises(ValueError, match='campaign_tool_runtime_unavailable'):
        CompositionReview.bind(prepared(selected, value))


def test_literal_port_metadata_and_original_consumption_are_separate_checks():
    selected, value = documents()
    bound = prepared(selected, value)
    use = CompositionReview.bind(bound).uses[0]
    original = value['candidate']['definition']['body']['nodes'][0]
    artifact = selected.request.document().context.objective.model_dump(mode='json')
    port = use.release.record.document().descriptor.tool.inputs[0]
    supplied = {'kind': 'artifact', 'artifact': artifact, 'representation': port.representation, 'unit': port.unit}
    original['inputs'][0]['source'] = supplied
    node = FutureCampaignDraft.model_validate_json(json.dumps(value['candidate'])).definition.body.nodes[0]
    assert len(literal_dependencies(node, bound)) == 1
    with pytest.raises(ValueError, match='campaign_tool_literal_representation'):
        validate_invocation(node, use.release)
    supplied['artifact']['schema_ref'] = port.schema_ref.model_dump(mode='json')
    node = FutureCampaignDraft.model_validate_json(json.dumps(value['candidate'])).definition.body.nodes[0]
    validate_invocation(node, use.release)
    with pytest.raises(ValueError, match='campaign_tool_input_unconsumed'):
        literal_dependencies(node, bound)


def test_evidence_with_no_producer_needs_no_invented_address_resolution():
    selected, value = research_inputs()
    value.update(action='request_evidence', evidence_requests=value['candidate']['expected_evidence'], candidate=None)
    assert not CompositionReview.bind(prepared(selected, value)).findings


def test_declared_checkpoint_checks_schema_and_consumed_dependency():
    selected, value = documents()
    bound = prepared(selected, value)
    used = CompositionReview.bind(bound).uses[0].release
    artifact = selected.request.document().context.objective.model_dump(mode='json')
    raw = used.record.document().model_dump(mode='json')
    raw['descriptor']['tool']['checkpoint_schema'] = artifact['schema_ref']
    raw['descriptor']['checkpoint'] = {'mode': 'opaque_artifact', 'readable_schema_sha256': [artifact['schema_ref']['sha256']]}
    raw['lock']['checkpoint_schema'] = artifact['schema_ref']
    raw['lock']['descriptor_sha256'] = hashlib.sha256(canonical(
        {'profile': 'amphora-tool-release-v1', 'descriptor': raw['descriptor']})).hexdigest()
    updated = ObservedRelease.bind(ReleaseSnapshot.model_validate_json(json.dumps(raw)), selected.request.document().reference.scope)
    release = ConsumedRelease(used.lane, updated, used.key)
    checkpoint = {'kind': 'artifact', 'artifact': artifact, 'representation': 'opaque-checkpoint', 'unit': '1'}
    value['candidate']['definition']['body']['nodes'][0]['checkpoint'] = checkpoint
    node = FutureCampaignDraft.model_validate_json(json.dumps(value['candidate'])).definition.body.nodes[0]
    validate_invocation(node, release)
    assert len(literal_dependencies(node, bound)) == 1
    checkpoint['artifact']['schema_ref']['sha256'] = '0' * 64
    node = FutureCampaignDraft.model_validate_json(json.dumps(value['candidate'])).definition.body.nodes[0]
    with pytest.raises(ValueError, match='campaign_tool_checkpoint_schema'):
        validate_invocation(node, release)
