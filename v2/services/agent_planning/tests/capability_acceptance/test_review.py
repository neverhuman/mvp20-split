import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from amphora_contracts_campaign_curation import CapabilityFulfillmentSpecification, RequestedCapabilityPort
from amphora_contracts_core import ArtifactRef
from amphora_agent_planning.capability_acceptance.collection import AcceptanceCollector
from amphora_agent_planning.capability_acceptance.review import AcceptanceReport, AcceptanceReview, ProcessedEvidence
from amphora_agent_planning.capability_acceptance.wire import acceptance_schema, schema_bytes
from amphora_agent_planning.capability_requests.projection import CurationCapabilities
from ..capability_requests.test_projection import view
from ..registry_access.test_discovery import record, Scripted


def case():
    original = view()
    release = record().model_copy(update={'scope': original.receipt.reference.scope})
    tool = release.descriptor.tool
    def ports(values):
        return tuple(RequestedCapabilityPort(name=row.name, representation=row.representation, schema_ref=row.schema_ref,
            description='Declared synthetic port', unit=row.unit) for row in values)
    gap = original.proposal.outcome.gaps[0].model_copy(update={'purpose': tool.purpose,
        'inputs': ports(tool.inputs), 'outputs': ports(tool.outputs), 'applicability': tool.applicability,
        'graph_gap': 'Use the declared synthetic tool in the future graph'})
    original = original.model_copy(update={'proposal': original.proposal.model_copy(update={
        'outcome': original.proposal.outcome.model_copy(update={'gaps': (gap,)})})})
    capability = CurationCapabilities.bind(original).requests[0]
    report = {'profile': 'planning.capability-acceptance.v1', 'authority': 'owner_reviewed_fulfillment_evidence',
        'scientific_authority': 'not_established', 'request': capability.reference.model_dump(mode='json'),
        'proposal_sha256': capability.proposal_sha256, 'gap_key': gap.gap_key,
        'release': release.lock.model_dump(mode='json'), 'requested_applicability': list(gap.applicability),
        'descriptor_applicability': list(tool.applicability), 'applicability_rationale': 'Synthetic engineering scope only',
        'criteria': [{'index': index, 'criterion': criterion, 'result': 'passed',
            'method': 'Compare retained input and output identity', 'observation': 'Original references preserved',
            'supporting_artifacts': []} for index, criterion in enumerate(gap.acceptance_criteria)]}
    return capability, release, report


def evidence(capability, release, raw):
    body = json.dumps(raw).encode() if isinstance(raw, dict) else raw
    reference = ArtifactRef(scope=capability.curation.scope, artifact_id='acceptance-report', media_type='application/json',
        size_bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), schema_ref=acceptance_schema())
    specification = CapabilityFulfillmentSpecification(request=capability.reference, release=release.lock, acceptance_evidence=(reference,))
    return specification, (ProcessedEvidence.bind(reference, reference, body),)


def test_exact_reviewed_report_matches_original_gap_release_ports_and_criteria():
    capability, release, report = case()
    specification, retained = evidence(capability, release, report)
    reviewed = AcceptanceReview.bind(capability, specification, release, retained)
    assert reviewed.release.document() == release and reviewed.report.document().scientific_authority == 'not_established'
    assert reviewed.report_reference == specification.acceptance_evidence[0]
    assert reviewed.report == AcceptanceReport.parse(retained[0].body)


@pytest.mark.parametrize('fault', ['request', 'proposal', 'gap', 'release', 'requested_applicability',
    'descriptor_applicability', 'duplicate_applicability', 'criterion', 'missing_criterion',
    'duplicate_criterion', 'failed', 'unknown', 'invented_support', 'self_authority'])
def test_report_cannot_claim_unrelated_or_unproven_fulfillment(fault):
    capability, release, report = case()
    if fault == 'request': report['request']['request_id'] = 'foreign'
    if fault == 'proposal': report['proposal_sha256'] = 'f' * 64
    if fault == 'gap': report['gap_key'] = 'foreign'
    if fault == 'release': report['release']['tool']['image_sha256'] = 'f' * 64
    if fault == 'requested_applicability': report['requested_applicability'] = ['foreign']
    if fault == 'descriptor_applicability': report['descriptor_applicability'] = ['foreign']
    if fault == 'duplicate_applicability': report['descriptor_applicability'] *= 2
    if fault == 'criterion': report['criteria'][0]['criterion'] = 'Different criterion'
    if fault == 'missing_criterion': report['criteria'] = []
    if fault == 'duplicate_criterion': report['criteria'] *= 2
    if fault in {'failed', 'unknown'}: report['criteria'][0]['result'] = fault
    if fault == 'self_authority': report['scientific_authority'] = 'established'
    if fault == 'invented_support':
        ref = evidence(capability, release, report)[0].acceptance_evidence[0]
        report['criteria'][0]['supporting_artifacts'] = [ref.model_dump(mode='json')]
    specification, retained = evidence(capability, release, report)
    with pytest.raises(ValueError): AcceptanceReview.bind(capability, specification, release, retained)


@pytest.mark.parametrize('fault', ['retired', 'lock', 'port', 'representation', 'schema', 'unit', 'extra_required'])
def test_typed_release_compatibility_is_checked_independently_of_report_claims(fault):
    capability, release, report = case()
    specification, retained = evidence(capability, release, report)
    gap = capability.gap
    if fault == 'retired': release = release.model_copy(update={'status': 'retired'})
    elif fault == 'lock': specification = specification.model_copy(update={'release': release.lock.model_copy(update={'descriptor_sha256': 'f' * 64})})
    elif fault == 'extra_required': capability = replace(capability, gap=gap.model_copy(update={'inputs': ()}))
    else:
        port = gap.outputs[0]
        value = {'port': ('name', 'foreign'), 'representation': ('representation', 'foreign'),
            'schema': ('schema_ref', port.schema_ref.model_copy(update={'sha256': 'f' * 64})), 'unit': ('unit', 'foreign')}[fault]
        capability = replace(capability, gap=gap.model_copy(update={'outputs': (port.model_copy(update={value[0]: value[1]}),)}))
    with pytest.raises(ValueError): AcceptanceReview.bind(capability, specification, release, retained)


def test_unspecified_schema_or_unit_does_not_invent_a_conversion():
    capability, release, report = case()
    specification, retained = evidence(capability, release, report)
    gap = capability.gap.model_copy(update={'outputs': tuple(port.model_copy(update={'schema_ref': None, 'unit': None}) for port in capability.gap.outputs)})
    reviewed = AcceptanceReview.bind(replace(capability, gap=gap), specification, release, retained)
    assert reviewed.release.document().descriptor.tool.outputs == release.descriptor.tool.outputs


def test_closed_report_schema_has_frozen_version_one_identity():
    assert schema_bytes() == Path(__file__).with_name('acceptance-v1.schema.json').read_bytes()


def test_current_processing_and_exact_registry_read_are_bounded_and_required():
    capability, release, report = case()
    specification, retained = evidence(capability, release, report)
    class Data:
        calls = 0
        def artifact(self, ref, budget): budget.start(); self.calls += 1; return ref
        def content(self, ref, budget): budget.start(); self.calls += 1; budget.consume(len(retained[0].body)); return retained[0].body
    data, registry = Data(), Scripted(release)
    result = AcceptanceCollector(registry, data).collect(capability, specification)
    assert result.report_reference == specification.acceptance_evidence[0] and data.calls == 2
    assert registry.paths == ['/v1/releases/' + release.lock.descriptor_sha256]
    with pytest.raises(ValueError): ProcessedEvidence.bind(retained[0].reference, retained[0].reference, b'wrong bytes')
