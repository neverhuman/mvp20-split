"""No payload/grant/write is needed to observe complete scoped catalog totals."""
from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.api import create_app
from amphora_data_artifacts.ancestry_footprints.inspection import AncestryFootprint,AncestryFootprints
from amphora_data_artifacts.retention_closures.model import ProtectedClosure
from amphora_data_artifacts.publication.model import UploadError
from ..retention_closures.test_membership import reference


def test_distinct_bytes_and_existing_digest():
    leaf,root=reference("leaf"),reference("root")
    closure=ProtectedClosure(root,(leaf,root))
    result=AncestryFootprint(closure).response()
    assert result.artifact==root and result.artifact_count==2 and result.content_bytes==8
    assert result.members_sha256==closure.digest


def test_exact_maximum_identities_and_safe_byte_sum():
    members=tuple(reference(f"item-{i:04}") for i in range(4096))
    assert AncestryFootprint(ProtectedClosure(members[0],members)).response().artifact_count==4096
    root=reference("root").model_copy(update={"size_bytes":9007199254740991})
    with pytest.raises(UploadError,match="bytes_limit"):
        AncestryFootprint(ProtectedClosure(root,(reference("leaf"),root))).response()


def test_read_only_diamond_totals_without_storage_or_retention(closure_env,monkeypatch):
    e=closure_env
    principal=replace(e.d.principal,actions=frozenset({"read"}))
    statements=[]
    def observe(_conn,_cursor,statement,_parameters,_context,_executemany):statements.append(statement)
    def forbidden(*args,**kwargs):raise AssertionError("payload access forbidden")
    monkeypatch.setattr(e.d.e.env.storage,"verify",forbidden)
    event.listen(e.engine,"before_cursor_execute",observe)
    try:
        result=AncestryFootprints(e.engine).get(principal,e.root.artifact_id)
    finally:event.remove(e.engine,"before_cursor_execute",observe)
    assert result.artifact_count==4 and result.content_bytes==17
    assert "REPEATABLE READ READ ONLY" in statements[0]
    assert all(sql.lstrip().upper().startswith(("SET ","SELECT ")) for sql in statements)


def test_http_scoped_read_grant_no_store_and_no_new_authority(closure_env):
    e=closure_env
    reader=replace(e.d.principal,actions=frozenset({"read"}))
    denied=replace(reader,actions=frozenset())
    foreign=replace(reader,scope=reader.scope.model_copy(update={"project_id":"foreign"}))
    credentials=Credentials([("r"*32,reader),("n"*32,denied),("f"*32,foreign)])
    path="/v1/artifacts/"+e.root.artifact_id+"/ancestry-footprint"
    with TestClient(create_app(e.uploads,e.d.e.env.storage,credentials)) as client:
        for token,status in (("r",200),("n",403),("f",404),(None,401)):
            response=client.get(path,headers={} if token is None else {"Authorization":"Bearer "+token*32})
            assert response.status_code==status,response.text
            assert response.headers["Cache-Control"]=="no-store"
        result=client.get(path,headers={"Authorization":"Bearer "+"r"*32}).json()
        assert set(result)=={"schema_version","profile","artifact","artifact_count","content_bytes","members_sha256"}
        denied_retention=client.get("/v1/retention-closures/missing",headers={"Authorization":"Bearer "+"r"*32})
        assert denied_retention.status_code==403


def test_conversion_ancestry_is_included(derived_env):
    d=derived_env
    source,output=d.linked_source()
    result=AncestryFootprints(d.e.env.engine).get(d.principal,output.artifact_id)
    assert result.artifact_count==2
    assert result.content_bytes==source.reference.raw.size_bytes+output.size_bytes


def test_later_conversion_changes_observation_without_granting_processing(derived_env):
    d=derived_env
    source=d.e.source()
    prepared=d.e.workflow.prepare(d.e.principal,source)
    output=d.e.publish(prepared.content,prepared.output_schema)
    service=AncestryFootprints(d.e.env.engine)
    before=service.get(d.principal,output.artifact_id)
    assert before.artifact_count==1
    d.e.workflow.retain(d.e.principal,source,"trace",output)
    after=service.get(d.principal,output.artifact_id)
    assert after.artifact_count==2 and after.members_sha256!=before.members_sha256
    d.revoke(source)
    assert service.get(d.principal,output.artifact_id)==after
    assert d.client.get("/v1/artifacts/"+output.artifact_id+"/content",headers=d.headers).status_code==403


def test_mixed_conversion_and_derivation_graph(derived_env):
    d=derived_env
    source,converted=d.linked_source()
    leaf=d.e.publish(b"leaf")
    final=d.stream(d.begin((leaf,converted),b"mixed"),b"mixed")
    response=d.client.post("/v1/artifacts/finalize",json=final,headers=d.headers)
    assert response.status_code==200,response.text
    result=AncestryFootprints(d.e.env.engine).get(d.principal,response.json()["artifact"]["artifact_id"])
    assert result.artifact_count==4
    assert result.content_bytes==source.reference.raw.size_bytes+converted.size_bytes+4+5


@pytest.mark.parametrize("reason",["artifact_unavailable","retention_lineage_cycle","retention_closure_limit"])
def test_invalid_ancestry_is409_not_a_partial_leaf(closure_env,monkeypatch,reason):
    from amphora_data_artifacts.ancestry_footprints import inspection
    def fail(*args):raise UploadError(reason)
    monkeypatch.setattr(inspection,"discover",fail)
    d=closure_env.d
    response=d.client.get("/v1/artifacts/"+closure_env.root.artifact_id+"/ancestry-footprint",headers=d.headers)
    assert response.status_code==409 and response.headers["Cache-Control"]=="no-store"
    assert "artifact_count" not in response.json()


def test_storage_failure_is503_no_store(closure_env,monkeypatch):
    def fail(*args):raise OSError("private filesystem detail")
    monkeypatch.setattr(AncestryFootprints,"get",fail)
    d=closure_env.d
    response=d.client.get("/v1/artifacts/"+closure_env.root.artifact_id+"/ancestry-footprint",headers=d.headers)
    assert response.status_code==503 and response.headers["Cache-Control"]=="no-store"
    assert response.json()=={"reason_code":"storage_unavailable"}
