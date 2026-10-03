"""Actual installed Data/PG/Qdrant query authority and process reconstruction."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest
from amphora_data_artifacts.retrieval.intents import GenerationIntents
from amphora_data_artifacts.retrieval.publication import GenerationPublication
from amphora_data_artifacts.retrieval.qdrant.adapter import QdrantAdapter
from amphora_data_artifacts.retrieval.qdrant.configuration import QdrantConfiguration
from amphora_data_artifacts.source_rights.ledger import SourceRights
from sqlalchemy import text

from ..test_generation_publication import revoke, rows
from .test_broker import query as query

pytestmark = [pytest.mark.postgres, pytest.mark.skipif(os.environ.get("AMPHORA_TEST_QDRANT") != "1",
    reason="Explicit actual Qdrant fixture required")]


def probe(e, state, request, tmp_path, mode="retrieve", scope=None):
    body={"actor_id":e.p.actor_id,"scope":(scope or e.p.scope).model_dump(mode="json"),
        "actions":sorted(e.p.actions),"storage":str(e.ingestion.env.storage.root),
        "endpoint":state["endpoint"],"request":request.model_dump(mode="json"),"mode":mode}
    handoff=tmp_path/'query.json'
    handoff.write_text(json.dumps(body),encoding="utf-8")
    environment={name:os.environ[name] for name in ("PATH","SYSTEMROOT","TEMP","TMP") if name in os.environ}
    environment.update(PYTHONUTF8="1",AMPHORA_QUERY_DATABASE_URL=e.engine.url.render_as_string(hide_password=False),
        AMPHORA_QUERY_API_KEY=state["api_key"])
    python=os.environ.get("AMPHORA_TEST_QUERY_PYTHON",sys.executable)
    result=subprocess.run([python,"-I",str(Path(__file__).absolute().with_name("query_probe.py")),str(handoff)],
        cwd=tmp_path,env=environment,capture_output=True,text=True,timeout=45,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
    assert result.returncode==0,result.stderr[-3000:]
    return json.loads(result.stdout)


def test_actual_query_replacement_rights_and_backend_failure(query,tmp_path,monkeypatch):
    import qdrant_fixture as fixture

    e=query
    primary=fixture.owned_state()
    backend=QdrantAdapter(QdrantConfiguration(primary["endpoint"],primary["api_key"]))
    # New actual-backend corpus; the test-only generation is never relabeled as real.
    request=e.request.model_copy(update={"corpus_id":"actual-corpus","generation_id":"actual1",
        "expected_head":None,"bindings":(e.binding.reference,e.query_binding.reference)})
    intents=GenerationIntents(e.engine,backend.reference)
    intents.prepare(e.p,request)
    lease=e.leases.claim(e.p,"actual-corpus","actual1")
    publication=GenerationPublication(e.ingestion.reads,backend)
    publication.build_and_verify(e.p,lease)
    status=publication.publish(e.p,lease)
    query_request=e.query_request.model_copy(update={"generation":status.generation.reference})
    first=probe(e,primary,query_request,tmp_path)
    matches=first["record"]["matches"]
    expected=sorted((e.binding,e.query_binding),key=lambda b:(b.reference.binding_id,b.reference.sha256))
    assert [m["binding"] for m in matches]==[b.model_dump(mode="json") for b in expected]
    assert [m["score"] for m in matches]==[8.0,8.0]
    second=probe(e,primary,query_request,tmp_path,mode="read")
    assert first["pid"]!=second["pid"] and first["record"]==second["record"]
    with e.engine.connect() as c:
        original=bytes(c.execute(text("SELECT canonical_bytes FROM artifacts.retrieval_results "
            "WHERE tenant_id=:tenant AND project_id=:project AND retrieval_id='query1'"),e.p.bindings).scalar_one())

    with monkeypatch.context() as patch:
        patch.setattr(fixture,"STATE",fixture.ROOT/'.test-results/qdrant-replacement-fixture.json')
        fixture.resume() if fixture.STATE.exists() else fixture.start()
        replacement=fixture.owned_state()
    # Missing projection cannot rewrite the original selection; new query stays pending.
    historical=probe(e,replacement,query_request,tmp_path)
    assert historical["record"]==first["record"]
    missing_request=query_request.model_copy(update={"retrieval_id":"backend-missing"})
    missing=probe(e,replacement,missing_request,tmp_path)
    assert missing["error"]=="qdrant_http_404"
    assert rows(e,"retrieval_queries")==2 and rows(e,"retrieval_results")==1
    pending=probe(e,primary,missing_request,tmp_path,mode="read")
    assert pending["error"]=="retrieval_query_pending"
    recovered=probe(e,primary,missing_request,tmp_path)
    assert recovered["record"]["matches"]==matches

    revoke(e)
    denied=probe(e,primary,query_request,tmp_path,mode="read")
    assert denied["error"]=="rights_revoked" and "record" not in denied
    fresh=query_request.model_copy(update={"retrieval_id":"after-revocation"})
    filtered=probe(e,primary,fresh,tmp_path)
    assert filtered["record"]["matches"]==[{"binding":e.query_binding.model_dump(mode="json"),"score":8.0}]
    assert e.binding.reference.binding_id not in json.dumps(filtered)
    foreign=probe(e,primary,fresh,tmp_path,scope=e.p.scope.model_copy(update={"project_id":"foreign"}))
    assert foreign["error"]=="retrieval_generation_missing"
    rights=SourceRights(e.engine)
    old=rights.history(e.p,"query-rights",1)
    rights.publish(e.p,old.model_copy(update={"reference":old.reference.model_copy(update={"revision":2}),
        "supersedes":old.reference,"allowed_uses":("read",)}))
    readable=probe(e,primary,fresh,tmp_path,mode="read")
    assert readable["record"]==filtered["record"]
    processing=probe(e,primary,fresh.model_copy(update={"retrieval_id":"process-denied"}),tmp_path)
    assert processing["error"]=="rights_use_denied"
    with e.engine.connect() as c:
        retained=bytes(c.execute(text("SELECT canonical_bytes FROM artifacts.retrieval_results "
            "WHERE tenant_id=:tenant AND project_id=:project AND retrieval_id='query1'"),e.p.bindings).scalar_one())
    assert retained==original
    evidence={"timestamp_local":datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "generation":status.generation.reference.model_dump(mode="json"),"first":first,"reconstructed":second,
        "offline_replay":historical,"unavailable":missing,"pending":pending,"recovered":recovered,
        "revoked_read":denied,"filtered":filtered,"foreign":foreign,"read_only_replay":readable,
        "process_denied":processing,"original_bytes_unchanged":True}
    destination=Path(__file__).absolute().parents[5]/'.test-results/qdrant-query-replacement.json'
    destination.write_text(json.dumps(evidence,indent=2)+'\n',encoding="utf-8")
