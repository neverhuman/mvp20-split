"""Actual Data HTTP publication of a stored synthetic decision, with no DomainReceipt."""
import hashlib
import json
import os
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_research.assessment.reader import AssessmentDataReader
from amphora_research.eligibility.store import EligibilityStore
from amphora_research.scientific_publication.artifact import ScientificArtifact
from amphora_research.scientific_publication.store import ScientificPublicationStore
from amphora_research.scientific_publication.workflow import ScientificPublicationWorkflow
from amphora_tool_protocol import HttpTransport

from ..assessment.live_peers import Owner, owned_script
from ..assessment.test_actual_resolution import publish
from ..eligibility.test_store import prepared_case

pytestmark = pytest.mark.postgres


def test_actual_data_publishes_exact_scientific_result_and_replays_after_replacement(ledger,tmp_path):
    data_python = os.environ.get("AMPHORA_TEST_DATA_PYTHON")
    if not data_python:
        pytest.skip("Independent Data interpreter required")
    identities,scope = ledger
    store,configured,claims,_ = prepared_case(ledger)
    url = identities.engine.url
    env = dict(os.environ,DATA_DB=url.set(username="artifact_service").render_as_string(hide_password=False),
        DATA_TOKEN="d"*32,READ_TOKEN="r"*32,PUBLISH_TOKEN="p"*32,
        PEER_MIGRATION=url.set(username="artifact_migrator").render_as_string(hide_password=False))
    owned_script(data_python,"import os; from amphora_data_artifacts.persistence.migrate import upgrade; upgrade(os.environ['PEER_MIGRATION'])",env)
    raw_schema = {"schema_id":"fixture.bytes","version":"1","sha256":hashlib.sha256(b'{"type":"string","contentEncoding":"base64"}').hexdigest()}
    schema_body = ScientificArtifact.schema_document("eligibility")
    (tmp_path/"schema.json").write_bytes(schema_body)
    (tmp_path/"bytes").mkdir()
    config = {"database_url_env":"DATA_DB","storage_root":str(tmp_path/"bytes"),"acquisition":True,
        "profiles":[{"media_type":"application/octet-stream",**raw_schema},{"media_type":"application/json",
            "schema_id":"research.eligibility.payload","version":"1","sha256":hashlib.sha256(schema_body).hexdigest(),"schema_path":"schema.json"}],
        "principals":[{"token_env":token,"actor_id":actor,"scope":scope.model_dump(mode="json"),"actions":actions}
            for token,actor,actions in (("DATA_TOKEN","fixture",["read","source_history","upload","finalize"]),
                ("READ_TOKEN","reader",["read","source_history"]),("PUBLISH_TOKEN","science-publisher",["read","source_history","upload","finalize"]))]}
    (tmp_path/"data.json").write_text(json.dumps(config),encoding="utf-8")
    data = Owner("amphora_data_artifacts",tmp_path/"data.json",env,"d"*32,data_python)
    try:
        source = ArtifactRef.model_validate_json(json.dumps(publish(data,scope.model_dump(mode="json"),b"Synthetic model fixture only",raw_schema)))
        context = replace(configured.context,conditions=source)
        configured = replace(configured,context=context,requirements=(replace(configured.requirements[0],kind="model"),configured.requirements[1]))
        assertion = replace(claims[0],context=context,origin=replace(claims[0].origin,source=source,kind="model",observation=None))
        decision = store.assess(configured,(assertion,),"fixture","actual-publication")
        artifact = ScientificArtifact.from_decision(decision)
        journal = ScientificPublicationStore(identities.engine)
        reader = AssessmentDataReader(data.endpoint,"r"*32,scope)
        original = reader.read
        def checked(reference):
            assert identities.engine.pool.checkedout() == 0
            return original(reference)
        reader.read = checked
        transport = HttpTransport(data.endpoint,"p"*32)
        result = ScientificPublicationWorkflow(journal,reader,transport,"science-publisher").submit(artifact)
        assert result.stage == "published" and not hasattr(result,"receipt")
        output = result.derivation.artifact
        fresh_reader = AssessmentDataReader(data.endpoint,"r"*32,scope)
        content,proof = fresh_reader.published(output,frozenset({"science-publisher"}))
        assert content == artifact.body and proof == result.derivation
        assert proof.declaration.inputs == (source,)
        replacement = ScientificPublicationWorkflow(ScientificPublicationStore(identities.engine),fresh_reader,transport,"science-publisher")
        assert replacement.submit(ScientificArtifact.from_decision(EligibilityStore(identities.engine).read(scope,decision.reference))) == result
        assert json.loads(content)["assessment"]["focus"] == ["accuracy"]
        evidence = {"timestamp_local":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"research_python":sys.executable,
            "data_python":data_python,"decision":decision.reference.model_dump(mode="json"),"artifact":output.model_dump(mode="json"),
            "derivation":proof.model_dump(mode="json"),"cases":["actual_Data_typed_publication","exact_bytes_and_provenance",
                "weak_optional_focus_preserved","replacement_replay","no_DomainReceipt","no_SQL_during_peer_reads"],
            "limits":["Private trusted synthetic model assertion, not authenticated model input ingestion",
                      "Research workflow runs in test process; hosted API/process kill proof remains B1.08/B3/V1"]}
        target = Path(os.environ.get("AMPHORA_SCIENCE_PUBLICATION_EVIDENCE",str(Path(__file__).absolute().parents[4]/".test-results/science-publication-live.json")))
        target.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    finally:
        data.stop()
