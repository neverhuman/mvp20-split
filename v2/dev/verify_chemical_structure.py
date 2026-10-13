"""Independent chemical-tool wheel tests; no owner mutation or scientific validity claim."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from install_owner_peer import install
from check_boundaries import ROOT


def verify(output):
    output=output.absolute(); output.mkdir(parents=True,exist_ok=False)
    python=install(output/"installed","amphora-chemical-structure",("amphora_research","amphora_campaign_runtime","amphora_agent_planning","amphora_data_artifacts","amphora_hansen_solvency","sqlalchemy"))
    tests=output/"tests"
    shutil.copytree(ROOT/"tools/chemical_structure/tests",tests,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    def run(args,input=None):
        result=subprocess.run([str(a) for a in args],input=input,capture_output=True,timeout=300)
        with (output/"verification.log").open("ab") as stream: stream.write(result.stdout+result.stderr)
        if result.returncode: raise RuntimeError("chemical_verification_failed; inspect bounded verification.log")
        return result.stdout
    run([ROOT/".venv/Scripts/uv.exe","pip","install","--python",python,"pytest==8.4.2"])
    args=[str(tests),"--confcutdir="+str(output),"--import-mode=importlib","-q","--tb=short"]
    run([python,"-I","-c","import pytest;raise SystemExit(pytest.main("+repr(args)+"))"])
    for kind,name in (("input","request"),("output","result")):
        actual=run([python,"-I","-m","amphora_chemical_structure","schema","--kind",kind])
        assert actual==(ROOT/"contracts/schemas/v1"/f"chemical-structure.{name}.validation.json").read_bytes()
    supplied=(ROOT/"contracts/chemical_structure/examples/supplied-request.json").read_bytes()
    output_bytes=run([python,"-I","-m","amphora_chemical_structure","compute"],supplied)
    assert output_bytes==run([python,"-I","-m","amphora_chemical_structure","compute"],supplied)
    result=json.loads(output_bytes)
    assert result["outcome"]["status"]=="derived" and result["outcome"]["formula"]["text"]=="C2H6O2"
    assert result["source_sha256"]==hashlib.sha256(supplied).hexdigest()
    (output/"supplied-request.json").write_bytes(supplied)
    (output/"derived-result.json").write_bytes(output_bytes)
    evidence={"status":"passed","python":str(python),"provider_calls":0,"source_sha256":result["source_sha256"],"result_sha256":hashlib.sha256(output_bytes).hexdigest(),"scope":"independent supplied structure tool; actual registered graph and Research acceptance remain P1.4"}
    (output/"evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print("Independent chemical tool checks passed",flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True)
    verify(parser.parse_args().output)
