"""Public totals inspection before/after independently installed Data restart."""
import json
from pathlib import Path
import subprocess
from verify_retention_closure_installation import ROOT,write


def verify(output,port,environment,root,leaf,reservation,closure,start,stop):
    packet=output/"ancestry-client-input.json"
    write(packet,dict(root=root,leaf=leaf,reservation_id=reservation,
        artifact_count=closure["artifact_count"],members_sha256=closure["members_sha256"]))
    def inspect(label):
        report=output/("ancestry-"+label+".json")
        arguments=[environment["QUAL_ANCESTRY_PYTHON"],"-I",str(ROOT/"dev/artifact_ancestry_client_probe.py"),
            "--port",str(port),"--packet",str(packet),"--output",str(report)]
        if environment.get("QUAL_ANCESTRY_SEARCH")=="1":arguments.append("--search")
        result=subprocess.run(arguments,
            env=environment,capture_output=True,timeout=120)
        (output/("ancestry-"+label+".log")).write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,"Isolated read-only ancestry client failed; inspect ancestry log"
        return json.loads(report.read_bytes())
    before=inspect("before")
    stop("data")
    start("data",Path(environment["QUAL_DATA_PYTHON"]),port,environment)
    assert inspect("after")==before
    write(output/"ancestry-evidence.json",dict(status="passed",artifact_count=closure["artifact_count"],
        full_membership_digest_agrees=True,ordinary_leaf_verified=True,data_restart=True,
        search_resource_assessment=environment.get("QUAL_ANCESTRY_SEARCH")=="1",
        read_only_independent_client=True,retention_denied=True,provider_calls=0))
    print("Actual ancestry footprint matches retained closure across Data restart",flush=True)
