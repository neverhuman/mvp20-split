"""Scripted source boundary probes; actual Data proof is a distinct integration tier."""
import hashlib
from pathlib import Path

import pytest
from amphora_contracts_artifacts import (
    BeginDerivedUpload,
    ContentDescriptor,
    DerivationDeclaration,
    DerivationReceipt,
    TransformationDescriptor,
)
from amphora_contracts_research import (
    EligibilityInputProfile,
    ScientificAssessmentRequest,
    SynthesisInputProfile,
    SyntheticEligibilityReport,
    SyntheticSynthesisReport,
    synthetic_scientific_report_schema,
)
from amphora_research.assessment.policy import AssessmentError
from amphora_research.scientific_api.boundary import ConfiguredScientificInput, ScientificInputError
from amphora_research.scientific_api.resolution import ScientificInputResolver
from amphora_research.synthesis.decision import context_sources, option_sources
from amphora_tool_protocol import WorkerIdentity

EXAMPLES = Path(__file__).absolute().parents[4]/"contracts/research/examples"


class Reader:
    def __init__(self, scope, values, proof):
        self.scope,self.values,self.proof = scope,values,proof
        self.seen = {}
    @property
    def consumed(self):
        return tuple(self.seen.values())
    def read(self, reference):
        self.seen[reference.artifact_id] = reference
        return self.values[reference]
    def published(self, reference, publishers):
        if self.proof.origin.actor_id not in publishers:
            raise AssessmentError("untrusted_publisher")
        return self.read(reference),self.proof


def resolution_case(kind="eligibility", transform=None):
    profile_model = EligibilityInputProfile if kind == "eligibility" else SynthesisInputProfile
    report_model = SyntheticEligibilityReport if kind == "eligibility" else SyntheticSynthesisReport
    configured = ConfiguredScientificInput(profile_model.model_validate_json((EXAMPLES/(kind+"-input-profile.json")).read_bytes()))
    report = report_model.model_validate_json((EXAMPLES/("synthetic-"+kind+"-report.json")).read_bytes())
    if transform is not None:
        report = transform(report)
    required = [report.raw_report]
    if kind == "eligibility":
        required.extend(row.context.conditions for row in report.claims)
        required.extend(row.origin.source for row in report.claims if row.origin.source is not None)
        policy_sources = (configured.document.policy.context.conditions,)
    else:
        required.extend(source for option in report.options for source in option_sources(option))
        policy_sources = context_sources(configured.document.policy.context)
    body = report.model_dump_json().encode()
    source = report.raw_report.model_copy(update={"scope":configured.scope,"artifact_id":"scientific-report","schema_ref":synthetic_scientific_report_schema(kind),
        "sha256":hashlib.sha256(body).hexdigest(),"size_bytes":len(body),"media_type":"application/json"})
    adapter = configured.document.adapter
    declaration = DerivationDeclaration(transformation=TransformationDescriptor(transformation_id=adapter.schema_id,version=adapter.version,sha256=adapter.sha256),
        inputs=tuple(dict.fromkeys(required)))
    descriptor = ContentDescriptor(sha256=source.sha256,size_bytes=source.size_bytes,media_type=source.media_type,schema_ref=source.schema_ref)
    command = WorkerIdentity("fixture",source.scope).command("artifacts.begin_derived_upload","producer-command",
        BeginDerivedUpload(content=descriptor,declaration=declaration))
    proof = DerivationReceipt(origin=command.identity,request_sha256=command.sha256,upload_id="upload",artifact=source,declaration=declaration)
    values = {item:b"{}" for item in (*required,*policy_sources)}|{source:body}
    reader = Reader(source.scope,values,proof)
    request = ScientificAssessmentRequest(wire_version="1",decision_id="resolved-decision",profile=configured.reference,reports=(source,))
    return configured.bind(request,"fixture",source.scope),reader


@pytest.mark.parametrize("kind",["eligibility","synthesis"])
def test_all_consumed_sources_and_policy_results_are_retained(kind):
    bound,reader = resolution_case(kind)
    resolved = ScientificInputResolver(reader).resolve(bound)
    result = resolved.decision_document().record
    assert set(result.sources) == set(reader.consumed)
    assert bound.request.reports[0] in result.sources
    assert result.actor_id == bound.actor and result.reference.kind == kind
    if kind == "eligibility":
        assert result.assessment.disposition == "eligible" and result.assessment.focus == ("accuracy",)
        assert result.assessment.reviews[0].claim.origin.source == bound.request.reports[0]
    else:
        assert result.assessment.alternatives[0].disposition == "eligible"
    with pytest.raises(ScientificInputError,match="reader_reused"):
        ScientificInputResolver(reader).resolve(bound)


def test_original_external_evidence_does_not_hide_authenticated_producer_report():
    def external(report):
        row = report.claims[0]
        return report.model_copy(update={"claims":(row.model_copy(update={"origin":row.origin.model_copy(update={"source":report.raw_report})}),)})
    bound,reader = resolution_case(transform=external)
    result = ScientificInputResolver(reader).resolve(bound).decision_document().record
    assert result.assessment.reviews[0].claim.origin.source.artifact_id == "raw"
    assert {item.artifact_id for item in result.sources} == {"conditions","raw","scientific-report"}


@pytest.mark.parametrize("transform,reason",[
    (lambda r:r.model_copy(update={"issuer":"forged"}),"scientific_report_issuer_mismatch"),
    (lambda r:r.model_copy(update={"adapter":r.adapter.model_copy(update={"sha256":"0"*64})}),"scientific_report_adapter_mismatch"),
    (lambda r:r.model_copy(update={"raw_report":r.raw_report.model_copy(update={"scope":r.raw_report.scope.model_copy(update={"project_id":"other"})})}),"scientific_report_source_scope"),
])
def test_producer_context_mismatches_are_not_scientific_results(transform,reason):
    bound,reader = resolution_case(transform=transform)
    with pytest.raises(ScientificInputError,match=reason):
        ScientificInputResolver(reader).resolve(bound)


@pytest.mark.parametrize("fault,reason",[("method","scientific_report_method_mismatch"),("lineage","evidence_lineage_mismatch"),
    ("publisher","untrusted_publisher"),("payload","invalid_evidence_payload")])
def test_invalid_publication_proofs_and_payloads_fail_before_decision(fault,reason):
    bound,reader = resolution_case()
    if fault == "method":
        reader.proof = reader.proof.model_copy(update={"declaration":reader.proof.declaration.model_copy(update={
            "transformation":reader.proof.declaration.transformation.model_copy(update={"sha256":"0"*64})})})
    elif fault == "lineage":
        reader.proof = reader.proof.model_copy(update={"declaration":reader.proof.declaration.model_copy(update={"inputs":()})})
    elif fault == "publisher":
        reader.proof = reader.proof.model_copy(update={"origin":reader.proof.origin.model_copy(update={"actor_id":"untrusted"})})
    else:
        reader.values[bound.request.reports[0]] = b"{}"
    with pytest.raises((ScientificInputError,AssessmentError),match=reason):
        ScientificInputResolver(reader).resolve(bound)


@pytest.mark.parametrize("update,reason",[({"media_type":"application/octet-stream"},"schema_mismatch"),
    ({"size_bytes":8388609},"byte_limit")])
def test_invalid_report_descriptor_fails_before_any_peer_read(update,reason):
    bound,reader = resolution_case()
    changed = bound.request.model_copy(update={"reports":(bound.request.reports[0].model_copy(update=update),)})
    bound = bound.configured.bind(changed,bound.actor,bound.configured.scope)
    with pytest.raises(ScientificInputError,match=reason):
        ScientificInputResolver(reader).resolve(bound)
    assert not reader.consumed
