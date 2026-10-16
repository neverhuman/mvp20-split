"""Read-only HTTP probe using only the independently installed public contract."""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path

from amphora_contracts_artifact_ancestry import ArtifactAncestryFootprint
from amphora_contracts_core import ArtifactRef


def get(port,path,token):
    connection=http.client.HTTPConnection("127.0.0.1",port,timeout=20)
    try:
        connection.request("GET",path,headers={"Authorization":"Bearer "+token})
        response=connection.getresponse()
        raw=response.read(262145)
        assert len(raw)<=262144,"Unbounded inspection response"
        return response.status,response.getheader("Cache-Control"),raw
    finally:connection.close()


def verify(port,packet,output,use_search=False):
    token=os.environ["QUAL_ANCESTRY_TOKEN"]
    expected=json.loads(packet.read_bytes())
    result={}
    for name in ("root","leaf"):
        reference=ArtifactRef.model_validate_json(json.dumps(expected[name]))
        status,cache,raw=get(port,"/v1/artifacts/"+reference.artifact_id+"/ancestry-footprint",token)
        assert status==200 and cache=="no-store"
        observed=ArtifactAncestryFootprint.model_validate_json(raw)
        assert observed.artifact==reference and observed.content_bytes>=reference.size_bytes
        if name=="root":
            assert observed.artifact_count==expected["artifact_count"]
            assert observed.members_sha256==expected["members_sha256"]
        else:
            assert observed.artifact_count==1 and observed.content_bytes==reference.size_bytes
            body=json.dumps([reference.model_dump(mode="json")],sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
            assert observed.members_sha256==hashlib.sha256(b"amphora.artifact-retention/derived-closure-v1\0"+body).hexdigest()
        result[name]=observed.model_dump(mode="json")
    if use_search:
        from dataclasses import asdict
        from amphora_tool_protocol import ArtifactClient,HttpTransport,WorkerIdentity
        from amphora_evolution_search.composition.sources import SourceFootprints
        from amphora_evolution_search.composition.publications import PublicationBudget
        root=ArtifactRef.model_validate_json(json.dumps(expected["root"]))
        leaf=ArtifactRef.model_validate_json(json.dumps(expected["leaf"]))
        client=ArtifactClient(HttpTransport(f"http://127.0.0.1:{port}",token,timeout=20),
            WorkerIdentity("ancestry-reader",root.scope))
        footprints=SourceFootprints.load(client,(root,leaf,root))
        assessment=footprints.assess(PublicationBudget(5,15,15*262144))
        assert assessment.retained_artifacts_upper==expected["artifact_count"]+1+5
        footprints.unchanged(client)
        result["search_resource_assessment"]=asdict(assessment)
    status,_,_=get(port,"/v1/retention-closures/"+expected["reservation_id"],token)
    assert status==403,"Read-only caller unexpectedly has retention authority"
    output.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("Read-only isolated client verified complete ancestry totals; retention denied")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,required=True)
    parser.add_argument("--packet",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--search",action="store_true")
    args=parser.parse_args()
    verify(args.port,args.packet,args.output,args.search)
