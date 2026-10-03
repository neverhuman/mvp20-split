"""Actual Data publication/rights/HTTP against Research-owned experiment resolution."""
import hashlib
import json
import os
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_research import (
    LabReturnProfile,
    ObservationQuality,
    ReportedObservation,
    SyntheticLabReport,
    synthetic_lab_report_schema,
    synthetic_lab_report_schema_document,
)
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentDataReader, AssessmentPeerUnavailable
from amphora_research.experiments.store import ExperimentStore
from amphora_research.experiments.wire import from_wire, reference_to_wire, to_wire
from amphora_research.observations.identity import ObservationError
from amphora_research.observations.report_wire import to_resolution
from amphora_research.observations.reports import ConfiguredLabReturn
from amphora_research.observations.resolution import LabReportResolver

from ..assessment.live_peers import Owner, owned_script
from ..assessment.test_actual_resolution import publish
from ..material_state.storage_fixtures import publish_specimen

pytestmark = pytest.mark.postgres


def test_actual_data_lab_report_resolution_retains_partial_quality_and_denies_revoked_sources(ledger,tmp_path):
    identities,scope = ledger
    data_python = os.environ.get("AMPHORA_TEST_DATA_PYTHON")
    if not data_python:
        pytest.skip("Independent Data interpreter required")
    url = identities.engine.url
    environment = dict(os.environ,DATA_DB=url.set(username="artifact_service").render_as_string(hide_password=False),
        DATA_TOKEN="d"*32,READ_TOKEN="r"*32,PEER_MIGRATION=url.set(username="artifact_migrator").render_as_string(hide_password=False))
    owned_script(data_python,"import os; from amphora_data_artifacts.persistence.migrate import upgrade; upgrade(os.environ['PEER_MIGRATION'])",environment)
    raw_schema = {"schema_id":"fixture.bytes","version":"1","sha256":hashlib.sha256(b'{"type":"string","contentEncoding":"base64"}').hexdigest()}
    lab_schema = synthetic_lab_report_schema()
    (tmp_path / "lab-schema.json").write_bytes(synthetic_lab_report_schema_document())
    (tmp_path / "bytes").mkdir()
    config = tmp_path / "data.json"
    config.write_text(json.dumps({"database_url_env":"DATA_DB","storage_root":str(tmp_path / "bytes"),"acquisition":True,
        "profiles":[{"media_type":"application/octet-stream",**raw_schema},
                    {"media_type":"application/json",**lab_schema.model_dump(mode="json"),"schema_path":"lab-schema.json"}],
        "principals":[{"token_env":"DATA_TOKEN","actor_id":"fixture","scope":scope.model_dump(mode="json"),
                       "actions":["read","source_history","upload","finalize","acquire","manage_source_rights"]},
                      {"token_env":"READ_TOKEN","actor_id":"research-lab-reader","scope":scope.model_dump(mode="json"),"actions":["read","source_history"]}]}),encoding="utf-8")
    data = Owner("amphora_data_artifacts",config,environment,"d"*32,data_python)
    try:
        raw = publish(data,scope.model_dump(mode="json"),b"Synthetic laboratory report: 1.25 mg/L; controls failed.",raw_schema)
        context = publish(data,scope.model_dump(mode="json"),b"Synthetic protocol/applicability: fixture screening only.",raw_schema)
        rights = {"wire_version":"1","reference":{"scope":scope.model_dump(mode="json"),"rights_id":"lab-rights","revision":1},
                  "supersedes":None,"status":"granted","allowed_uses":["read","process"],"expires_at":None,"retention":"retain_audit_payload"}
        data.request("/v1/acquisition/rights",rights)
        source = {"wire_version":"1","reference":{"scope":scope.model_dump(mode="json"),"source_id":"raw-lab","revision_id":"1","raw":raw},
                  "delivery":{"issuer_id":"fixture","delivery_id":"lab-report"},
                  "method":{"connector_id":"fixture","connector_version":"1","configuration_sha256":"a"*64,"format":"utf8_document"},
                  "rights":rights["reference"],"supersedes":None,"completeness":"complete"}
        prepared = data.request("/v1/acquisition/prepare",source)
        converted = publish(data,scope.model_dump(mode="json"),prepared["content_json_utf8"].encode(),prepared["schema_ref"])
        data.request("/v1/acquisition/retain",{"wire_version":"1","source":source,"trace_id":"raw-lab-trace","output":converted})
        _,plan_record,reported = publish_specimen(identities,scope)
        plan = from_wire(plan_record)
        context_ref = ArtifactRef.model_validate_json(json.dumps(context))
        plan = replace(plan,protocol=replace(plan.protocol,applicability=context_ref,source=context_ref),
            expectations=plan.expectations+(replace(plan.expectations[0],expectation_id="second",
                replicate=replace(plan.expectations[0].replicate,replicate_id="replicate-2")),))
        experiments = ExperimentStore(identities.engine)
        experiments.publish(scope,"fixture",to_wire(plan))
        configured = ConfiguredLabReturn(LabReturnProfile(wire_version="1",authority="synthetic",profile_id="lab",version="1",
            experiment=reference_to_wire(plan.identity.reference),adapter=plan.protocol.method,publishers=("fixture",)))
        binding = reported.binding.model_copy(update={"measurement":reported.binding.measurement.model_copy(update={"context":context_ref})})
        first = ReportedObservation(reference=reported.reference,supersedes=None,binding=binding,value=reported.value,
                                    quality=ObservationQuality(controls="failed",flags=("questionable","low_accuracy")))
        wrong = first.model_copy(update={"reference":first.reference.model_copy(update={"observation_id":"unmatched"}),
            "binding":binding.model_copy(update={"specimen":binding.specimen.model_copy(update={
                "sample":binding.specimen.sample.model_copy(update={"sample_id":"wrong-vial"})})})})
        report = SyntheticLabReport(wire_version="1",authority="synthetic",issuer="fixture",adapter=configured.document.adapter,
            raw_report=ArtifactRef.model_validate_json(json.dumps(raw)),observations=(first,wrong))
        method = {"transformation_id":report.adapter.schema_id,"version":report.adapter.version,"sha256":report.adapter.sha256}
        def publish_report(document, transformation=method):
            result = publish(data,scope.model_dump(mode="json"),document.model_dump_json().encode(),lab_schema.model_dump(mode="json"),
                             inputs=[raw,context],method=transformation)
            return ArtifactRef.model_validate_json(json.dumps(result))
        artifact = publish_report(report)
        def resolve(reference=artifact,token="r"*32,profile=configured):
            reader = AssessmentDataReader(data.endpoint,token,scope)
            original = reader.published
            def checked(*args):
                assert identities.engine.pool.checkedout() == 0
                return original(*args)
            reader.published = checked
            return LabReportResolver(experiments,reader).resolve(profile,reference)
        resolved = resolve()
        outcome = to_resolution(resolved.report)
        assert outcome.disposition == "partial" and outcome.missing_expectations == ("second",)
        assert [item.disposition for item in outcome.matches] == ["matched","quarantined"]
        assert outcome.matches[1].reasons == ("sample_revision_mismatch",)
        assert outcome.observations[0].quality.controls == "failed"
        assert outcome.observations[0].quality.flags == ("questionable","low_accuracy")
        assert {item.artifact_id for item in resolved.inputs} == {artifact.artifact_id,raw["artifact_id"],context["artifact_id"]}
        with pytest.raises(AssessmentError,match="peer_access_denied"):
            resolve(token="z"*32)
        untrusted = ConfiguredLabReturn(configured.document.model_copy(update={"publishers":("other-publisher",)}))
        with pytest.raises(AssessmentError,match="untrusted_publisher"):
            resolve(profile=untrusted)
        with pytest.raises(ObservationError,match="lab_report_issuer_mismatch"):
            resolve(publish_report(report.model_copy(update={"issuer":"forged"})))
        with pytest.raises(ObservationError,match="lab_report_method_mismatch"):
            resolve(publish_report(report,method|{"version":"2"}))
        revoked = rights|{"reference":rights["reference"]|{"revision":2},"supersedes":rights["reference"],"status":"revoked","allowed_uses":[]}
        data.request("/v1/acquisition/rights",revoked)
        with pytest.raises(AssessmentError,match="peer_access_denied"):
            resolve()
        data.stop()
        with pytest.raises(AssessmentPeerUnavailable):
            resolve()
        assert identities.engine.pool.checkedout() == 0
        evidence = {"timestamp_local":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"scope":scope.model_dump(mode="json"),
            "research_python":sys.executable,"data_python":data_python,"resolution":outcome.model_dump(mode="json"),
            "consumed":[item.model_dump(mode="json") for item in resolved.inputs],
            "cases":["actual_Data_publication","partial_return","unmatched_sample","failed_controls_preserved","quality_flags_preserved",
                     "wrong_token_denied","untrusted_publisher_denied","forged_issuer_denied","wrong_adapter_denied",
                     "revoked_source_denied","outage_retryable","no_owner_transaction_during_peer_IO"],
            "limits":["Resolver runs in the Research test process; new public intake API remains B1.08",
                      "No durable intake decision yet; B1.07 owns atomic report/decision storage",
                      "Synthetic report adapter, no scientific validity or physical lab submission"]}
        target = Path(os.environ.get("AMPHORA_LAB_RESOLUTION_EVIDENCE",str(Path(__file__).absolute().parents[4]/".test-results/lab-resolution-live.json")))
        target.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    finally:
        data.stop()
