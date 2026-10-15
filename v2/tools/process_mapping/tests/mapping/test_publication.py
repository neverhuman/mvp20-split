"""Complete ancestry and source validation, independent of Runtime implementation."""
from types import SimpleNamespace

import pytest
from amphora_contracts_population import MaterialMappingItem,MaterialMappingPolicy,population_record_schema
from amphora_contracts_tools import ToolBinding
from amphora_process_mapping import canonical
from amphora_process_mapping.artifacts import ProcessArtifacts
from amphora_process_mapping.payloads import MaterialCollection,MapMaterialsRequest,schema_ref
from amphora_process_mapping.publication import MappingPublication


class Attempt:
    def __init__(self,invocation):self.invocation=invocation;self.active=True
    def check(self):
        if not self.active:raise RuntimeError("lease_lost")
    def refresh(self):self.check()


class Client:
    def __init__(self,scope):
        self.identity=SimpleNamespace(scope=scope)
        self.contents={};self.uploads={};self.declarations={}
    def read(self,ref):return self.contents[ref.artifact_id]
    def begin_derived(self,content,declaration,key,guard):
        guard();self.uploads[key]=(content,declaration)
        return SimpleNamespace(upload=key)
    def stream(self,upload,raw,guard):
        guard();self.contents[upload]=raw
    def finalize(self,upload,key,guard):
        guard();content,declaration=self.uploads[upload]
        from amphora_contracts_core import ArtifactRef
        ref=ArtifactRef(artifact_id=upload,scope=self.identity.scope,**content.model_dump())
        self.declarations[upload]=declaration
        return SimpleNamespace(artifact=ref)


def case(factory,count=2,mode="pairwise",right_count=None):
    context,_,_,artifact,material=factory
    right_count=count if right_count is None else right_count
    left_materials=tuple(material("left-"+str(i)) for i in range(count))
    right_materials=tuple(material("right-"+str(i)) for i in range(right_count))
    collection_schema=schema_ref(MaterialCollection,"process-worker.material-collection")
    def collection(name,materials):
        return artifact(name,collection_schema,MaterialCollection(schema_version="1",
            profile="synthetic-material-collection-v1",context=context,items=tuple(
                MaterialMappingItem(key=str(i),state=m.reference) for i,m in enumerate(materials))))
    left,right=collection("left",left_materials),collection("right",right_materials)
    request=MapMaterialsRequest(schema_version="1",profile="synthetic-map-materials-v1",context=context,
        policy=MaterialMappingPolicy(mode=mode,unmatched="retain_excluded" if mode=="keyed" else "reject",
            cartesian_opt_in=mode=="cartesian",maximum_outputs=1024),left=left.reference,right=right.reference)
    carrier=artifact("request",schema_ref(MapMaterialsRequest,"process-worker.map-materials"),request)
    client=Client(context.generation.scope)
    for source in (carrier,left,right,*left_materials,*right_materials):
        client.contents[source.reference.artifact_id]=source.content
    for source in (*left_materials,*right_materials):
        from amphora_contracts_population import MaterialState
        record=source.decode(MaterialState,population_record_schema("population.material-state"),context.generation.scope)
        for ref in (record.representation,record.conditions):client.contents[ref.artifact_id]=b"{}"
    invocation=SimpleNamespace(inputs=(SimpleNamespace(port="parameters",artifact=carrier.reference),),run_id=context.generation.run_id,
        checkpoint=None,invocation_id="invoke",activation_id="invoke",fence=1,
        attempt_id="attempt",tool=ToolBinding(capability_id="process.synthetic-map-materials",release="0.2.0",
            image_sha256="f"*64,contract_version="1"))
    attempt=Attempt(invocation)
    return request,ProcessArtifacts(client,attempt,"0.2.0","f"*64),client


@pytest.mark.parametrize("mode,expected",[("pairwise",2),("keyed",2),("cartesian",4)])
def test_published_pages_and_manifest_replay_and_retain_all_embedded_sources(material_factory,mode,expected):
    request,session,client=case(material_factory,mode=mode)
    publication=MappingPublication.load(request,session)
    root=publication.publish(session)
    pages=publication.mapping.pages()
    record=publication.mapping.verify_manifest(root,request.left,request.right,tuple(canonical(p) for p in pages))
    assert record.pair_count==expected
    page_parents=client.declarations[record.pages[0].artifact.artifact_id].inputs
    assert {ref.artifact_id for ref in publication.parents}|{"request"}=={ref.artifact_id for ref in page_parents}
    assert "conditions" in {ref.artifact_id for ref in page_parents}
    assert {"representation-left-0","representation-right-0"}<={ref.artifact_id for ref in page_parents}
    assert publication.publish(session)==root and len(client.uploads)==2


def test_keyed_exclusions_keep_the_unmatched_material_ancestry(material_factory):
    request,session,client=case(material_factory,mode="keyed",right_count=1)
    publication=MappingPublication.load(request,session)
    assert len(publication.mapping.excluded)==1
    publication.publish(session)
    assert "left-1" in {ref.artifact_id for declaration in client.declarations.values() for ref in declaration.inputs}


@pytest.mark.parametrize("damage",["context","metadata","parents","lease"])
def test_invalid_source_or_excess_ancestry_fails_before_any_upload(material_factory,damage):
    request,session,client=case(material_factory,count=32 if damage=="parents" else 2)
    if damage=="context":request=request.model_copy(update={"context":request.context.model_copy(update={"candidate_id":"e"*64})})
    if damage=="metadata":client.contents["conditions"]=b'{"corrupt":true}'
    if damage=="lease":session.attempt.active=False
    with pytest.raises((ValueError,RuntimeError)):
        MappingPublication.load(request,session).publish(session)
    assert client.uploads=={}


def test_publication_rejects_changed_bytes_for_a_reused_semantic_label(material_factory):
    request,session,client=case(material_factory)
    session.publish(request,schema_ref(MapMaterialsRequest,"process-worker.map-materials"),(request.left,),"same")
    changed=request.model_copy(update={"policy":request.policy.model_copy(update={"maximum_outputs":8})})
    with pytest.raises(ValueError,match="label_conflict"):
        session.publish(changed,schema_ref(MapMaterialsRequest,"process-worker.map-materials"),(request.left,),"same")
    assert len(client.uploads)==1
