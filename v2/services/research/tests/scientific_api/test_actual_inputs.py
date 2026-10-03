"""Independent Data authenticates synthetic inputs; Research retains useful qualified results."""
import hashlib
import json
import os
from pathlib import Path

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_research import (
    ScientificAssessmentRequest,
    SyntheticEligibilityReport,
    SyntheticSynthesisReport,
    synthetic_scientific_report_schema,
    synthetic_scientific_report_schema_document,
)
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentDataReader, AssessmentPeerUnavailable
from amphora_research.scientific_api.boundary import ConfiguredScientificInput, ScientificInputError
from amphora_research.scientific_api.profiles import ReviewedProfiles
from amphora_research.scientific_api.store import ScientificInputStore
from amphora_research.scientific_api.workflow import ScientificAssessmentWorkflow

from ..assessment.live_peers import Owner, owned_script
from ..assessment.test_actual_resolution import publish
from ..material_state.storage_fixtures import in_scope, publish_specimen
from .test_resolution import EXAMPLES, resolution_case

pytestmark = pytest.mark.postgres


def test_actual_published_inputs_and_offline_result_replay(ledger,tmp_path):
    identities,scope = ledger
    interpreter = os.environ.get("AMPHORA_TEST_DATA_PYTHON")
    if not interpreter:
        pytest.skip("Independent Data interpreter required")
    url = identities.engine.url
    environment = dict(os.environ,DATA_DB=url.set(username="artifact_service").render_as_string(hide_password=False),
        DATA_TOKEN="d"*32,READ_TOKEN="r"*32,PEER_MIGRATION=url.set(username="artifact_migrator").render_as_string(hide_password=False))
    owned_script(interpreter,"import os; from amphora_data_artifacts.persistence.migrate import upgrade; upgrade(os.environ['PEER_MIGRATION'])",environment)
    raw_schema = {"schema_id":"fixture.bytes","version":"1","sha256":hashlib.sha256(b'{"type":"string","contentEncoding":"base64"}').hexdigest()}
    profiles = [{"media_type":"application/octet-stream",**raw_schema}]
    for kind in ("eligibility","synthesis"):
        name = kind+".json"
        (tmp_path/name).write_bytes(synthetic_scientific_report_schema_document(kind))
        profiles.append({"media_type":"application/json",**synthetic_scientific_report_schema(kind).model_dump(mode="json"),"schema_path":name})
    (tmp_path/"bytes").mkdir()
    config = tmp_path/"data.json"
    config.write_text(json.dumps({"database_url_env":"DATA_DB","storage_root":str(tmp_path/"bytes"),"profiles":profiles,
        "principals":[{"token_env":"DATA_TOKEN","actor_id":"fixture","scope":scope.model_dump(mode="json"),
            "actions":["read","source_history","upload","finalize"]},
            {"token_env":"READ_TOKEN","actor_id":"research-science-reader","scope":scope.model_dump(mode="json"),"actions":["read","source_history"]}]}),encoding="utf-8")
    publish_specimen(identities,scope)
    data = Owner("amphora_data_artifacts",config,environment,"d"*32,interpreter)
    store = ScientificInputStore(identities.engine)
    completed = []
    try:
        for kind,model in (("eligibility",SyntheticEligibilityReport),("synthesis",SyntheticSynthesisReport)):
            template,_ = resolution_case(kind)
            report = in_scope(model.model_validate_json((EXAMPLES/("synthetic-"+kind+"-report.json")).read_bytes()),scope)
            configured_document = in_scope(template.configured.document,scope)
            references = {}
            def replace_refs(value, references=references, kind=kind):
                if isinstance(value,dict):
                    if "artifact_id" in value:
                        name = value["artifact_id"]
                        if name not in references:
                            references[name] = publish(data,scope.model_dump(mode="json"),(kind+" synthetic "+name).encode(),raw_schema)
                        return references[name]
                    return {key:replace_refs(item) for key,item in value.items()}
                if isinstance(value,list):
                    return [replace_refs(item) for item in value]
                return value
            configured = ConfiguredScientificInput(type(configured_document).model_validate_json(json.dumps(replace_refs(configured_document.model_dump(mode="json")))))
            report = model.model_validate_json(json.dumps(replace_refs(report.model_dump(mode="json"))))
            adapter = report.adapter
            method = {"transformation_id":adapter.schema_id,"version":adapter.version,"sha256":adapter.sha256}
            def publish_report(document, kind=kind, references=references, method=method):
                result = publish(data,scope.model_dump(mode="json"),document.model_dump_json().encode(),
                    synthetic_scientific_report_schema(kind).model_dump(mode="json"),inputs=list(references.values()),method=method)
                return ArtifactRef.model_validate_json(json.dumps(result))
            artifact = publish_report(report)
            request = ScientificAssessmentRequest(wire_version="1",decision_id=kind,profile=configured.reference,reports=(artifact,))
            def reader_factory(selected,token="r"*32,kind=kind,request=request):
                reader = AssessmentDataReader(data.endpoint,token,selected)
                original = reader.published
                def checked(*args):
                    assert identities.engine.pool.checkedout() == 0
                    assert store.read(scope,"fixture",kind,request.decision_id) is not None
                    return original(*args)
                reader.published = checked
                return reader
            workflow = ScientificAssessmentWorkflow(store,ReviewedProfiles((configured,)),reader_factory)
            result = workflow.submit(scope,"fixture",request)
            assert result.outcome.status == "assessed" and artifact in result.outcome.decision.sources
            if kind == "eligibility":
                assert result.outcome.decision.assessment.disposition == "eligible"
                assert result.outcome.decision.assessment.focus == ("accuracy",)
            else:
                assert result.outcome.decision.assessment.alternatives[0].disposition == "eligible"
            completed.append((request,result))
            forged = request.model_copy(update={"decision_id":kind+"-forged","reports":(publish_report(report.model_copy(update={"issuer":"forged"})),)})
            with pytest.raises(ScientificInputError,match="issuer_mismatch"):
                workflow.submit(scope,"fixture",forged)
            assert store.read(scope,"fixture",kind,forged.decision_id).decision is None
            denied = ScientificAssessmentWorkflow(store,ReviewedProfiles((configured,)),lambda s:reader_factory(s,"z"*32))
            with pytest.raises(AssessmentError,match="peer_access_denied"):
                denied.submit(scope,"fixture",request.model_copy(update={"decision_id":kind+"-denied"}))
        data.stop()
        offline = ScientificAssessmentWorkflow(ScientificInputStore(identities.engine),ReviewedProfiles(),
            lambda s:AssessmentDataReader(data.endpoint,"r"*32,s))
        for request,result in completed:
            assert offline.submit(scope,"fixture",request) == result
            assert offline.read(scope,"fixture",request.profile.kind,request.decision_id) == result
            with pytest.raises(AssessmentPeerUnavailable):
                offline.submit(scope,"fixture",request.model_copy(update={"decision_id":request.profile.kind+"-denied"}))
        target = os.environ.get("AMPHORA_SCIENTIFIC_INPUT_EVIDENCE")
        if target:
            Path(target).write_text(json.dumps({"scope":scope.model_dump(mode="json"),
                "results":[r.model_dump(mode="json") for _,r in completed],
                "cases":["actual_producer_authentication","forged_issuer_denied","unauthorized_source_denied",
                    "pending_keeps_original_profile","offline_completed_replay","optional_accuracy_focus",
                    "all_consumed_dependencies","no_owner_transaction_during_peer_IO"]},indent=2)+"\n",encoding="utf-8")
    finally:
        data.stop()
