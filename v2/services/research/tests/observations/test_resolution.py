"""Scripted owner/reader projection tests; actual Data authentication is proved separately."""
import hashlib
from types import SimpleNamespace

import pytest
from amphora_contracts_artifacts import DerivationReceipt
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentPeerUnavailable
from amphora_research.experiments.wire import to_wire
from amphora_research.observations.identity import ObservationError
from amphora_research.observations.resolution import LabReportResolver

from ..material_state.test_context import OTHER
from .test_reports import report_case


class Reader:
    def __init__(self, configured, plan, source, report):
        self.scope = configured.document.experiment.scope
        self.contents = report.model_dump_json().encode()
        self.used = {}
        self.proof = DerivationReceipt.model_validate({"schema_version":"1","origin":{
            "schema_version":"1","command_family":"artifacts.begin_derived_upload","command_id":"fixture", "actor_id":"fixture","scope":self.scope},
            "request_sha256":"a"*64,"upload_id":"fixture","artifact":source,"declaration":{
                "schema_version":"1","transformation":{"transformation_id":report.adapter.schema_id,
                    "version":report.adapter.version,"sha256":report.adapter.sha256},
                "inputs":(report.raw_report,plan.protocol.applicability,plan.protocol.source)}})

    def published(self, source, allowed):
        assert self.proof.origin.actor_id in allowed
        self.used[source.artifact_id] = source
        return self.contents,self.proof

    def read(self, reference):
        self.used[reference.artifact_id] = reference
        return b"scripted"

    @property
    def consumed(self):
        return tuple(self.used[key] for key in sorted(self.used))


def case():
    configured,plan,source,report = report_case(True)
    reader = Reader(configured,plan,source,report)
    owner = SimpleNamespace(read=lambda scope,ref: to_wire(plan))
    return LabReportResolver(owner,reader),configured,source


def test_resolver_pins_consumed_sources_and_finishes_owner_reads_before_peer_access():
    resolver,configured,source = case()
    calls = []
    original = resolver.experiments.read
    resolver.experiments.read = lambda scope,ref: (calls.append("owner") or original(scope,ref))
    peer = resolver.reader.published
    resolver.reader.published = lambda *args: (calls.append("peer") or peer(*args))
    result = resolver.resolve(configured,source)
    assert calls == ["owner","peer"]
    assert result.report.disposition == "partial"
    assert {r.artifact_id for r in result.inputs} == {"parsed-report","raw","context","protocol"}


@pytest.mark.parametrize("mutation,reason",[
    (lambda r,c,s: (r,None,s),"lab_profile_required"),
    (lambda r,c,s: (r,c,None),"lab_report_source_required"),
    (lambda r,c,s: (r,c,s.model_copy(update={"scope":OTHER})),"lab_report_scope_mismatch"),
    (lambda r,c,s: (r,c,s.model_copy(update={"media_type":"text/plain"})),"lab_report_schema_mismatch"),
    (lambda r,c,s: (r,c,s.model_copy(update={"size_bytes":8*1024*1024+1})),"lab_report_byte_limit"),
])
def test_invalid_request_rejected_before_source_read(mutation,reason):
    resolver,configured,source = mutation(*case())
    with pytest.raises(ObservationError,match=reason):
        resolver.resolve(configured,source)
    assert not resolver.reader.used


def test_absent_experiment_does_not_consume_report():
    resolver,configured,source = case()
    resolver.experiments.read = lambda *_: None
    with pytest.raises(ObservationError,match="unknown_lab_experiment"):
        resolver.resolve(configured,source)
    assert not resolver.reader.used


@pytest.mark.parametrize("field,reason",[("actor","lab_report_issuer_mismatch"),("method","lab_report_method_mismatch"),("inputs","evidence_lineage_mismatch")])
def test_producer_identity_method_and_lineage_must_match(field,reason):
    resolver,configured,source = case()
    proof = resolver.reader.proof
    if field == "actor":
        content = resolver.reader.contents.replace(b'"issuer":"fixture"',b'"issuer":"other"')
        resolver.reader.contents = content
        source = source.model_copy(update={"sha256":hashlib.sha256(content).hexdigest(),"size_bytes":len(content)})
    elif field == "method":
        resolver.reader.proof = proof.model_copy(update={"declaration":proof.declaration.model_copy(update={
            "transformation":proof.declaration.transformation.model_copy(update={"version":"2"})})})
    else:
        resolver.reader.proof = proof.model_copy(update={"declaration":proof.declaration.model_copy(update={"inputs":proof.declaration.inputs[:1]})})
    with pytest.raises((ObservationError,AssessmentError),match=reason):
        resolver.resolve(configured,source)


def test_invalid_immutable_payload_is_not_an_outage_or_negative_finding():
    resolver,configured,source = case()
    resolver.reader.contents = b'{"wire_version":"1","wire_version":"1"}'
    with pytest.raises(AssessmentError,match="invalid_evidence_payload"):
        resolver.resolve(configured,source)


@pytest.mark.parametrize("error",[AssessmentError("peer_access_denied"),AssessmentPeerUnavailable("peer_unavailable")])
def test_current_source_denial_or_outage_propagates_without_a_resolution(error):
    resolver,configured,source = case()
    def unavailable(_):
        raise error
    resolver.reader.read = unavailable
    with pytest.raises(type(error),match=str(error)):
        resolver.resolve(configured,source)
