"""Independent operator/Runtime/Data/Research installations and public handoff."""

import argparse
import json
import os
import subprocess
from pathlib import Path

from sqlalchemy import URL

from check_boundaries import ROOT
from install_owner_peer import install
from postgres_fixture import owned_state


def verify(output, installations=None, registry_installation=None, studio=None, gateway_installation=None, lan_tls=None, hold_seconds=0):
    if not 0 <= hold_seconds <= 86400 or hold_seconds and (not studio or lan_tls):
        raise ValueError("Held example requires Studio, localhost only, and at most one day")
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit owned PostgreSQL fixture opt-in required")
    state = owned_state()
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    packages = {
        "runtime": "amphora-campaign-runtime",
        "artifact": "amphora-data-artifacts",
        "research": "amphora-research",
        "chemical": "amphora-chemical-structure",
        "registry": "amphora-capability-registry",
        "controller": "amphora-tool-protocol",
    }
    modules = {key: package.replace("-", "_") for key, package in packages.items() if key != "controller"}
    interpreters, evidence = {}, {}
    for key, package in packages.items():
        forbidden = tuple(module for name, module in modules.items() if name != key)
        if installations is None and not (key == "registry" and registry_installation):
            interpreters[key] = str(install(output / key, package, forbidden))
            evidence[key] = json.loads((output / key / "manifest.json").read_bytes())
        else:
            existing=registry_installation.absolute() if key == "registry" and registry_installation else installations.absolute()/key
            evidence[key]=json.loads((existing/"manifest.json").read_bytes())
            if evidence[key]["owner"]!=package or evidence[key]["status"]!="installed":
                raise ValueError("wrong_installed_owner")
            interpreters[key]=str(existing/"environment/Scripts/python.exe")
            if not Path(interpreters[key]).is_file(): raise ValueError("missing_installed_interpreter")
    config = {**interpreters, "packages": evidence, "evidence": str(output / "http")}
    if studio:
        if not gateway_installation:
            raise ValueError("Studio qualification requires an independent Gateway installation")
        config["studio"] = {"public_directory": str(studio.absolute()),
            "gateway_python": str(gateway_installation.absolute()/"environment/Scripts/python.exe"),
            "hold_seconds":hold_seconds}
        if lan_tls:
            config["studio"]["lan"]={"address":"192.168.1.70","subnet":"192.168.1.0/24",
                "certificate":str(lan_tls.absolute()/"server.pem"),"private_key":str(lan_tls.absolute()/"server.key"),
                "ca":str(lan_tls.absolute()/"amphora-demo-ca.pem")}
    path = output / "acceptance.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    host, port = state["endpoint"].split(":")
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}
    }
    for name, role in [
        ("RUNTIME", "runtime_service"),
        ("ARTIFACT", "artifact_service"),
        ("RESEARCH", "research_service"),
        ("REGISTRY", "registry_service"),
    ]:
        env["AMPHORA_" + name + "_DATABASE_URL"] = URL.create(
            "postgresql+psycopg",
            username=role,
            password=state["password"],
            host=host,
            port=int(port),
            database=state["database"],
        ).render_as_string(hide_password=False)
    probe = ROOT / "services/research/tests/candidate_registration/chemical_acceptance/probe.py"
    result = subprocess.run(
        [interpreters["controller"], "-I", str(probe), str(path)],
        cwd=output,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=600+hold_seconds,
    )
    (output / "probe.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Chemical candidate handoff failed; inspect " + str(output / "probe.log"))
    print(result.stdout, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--installations",type=Path)
    parser.add_argument("--registry-installation",type=Path)
    parser.add_argument("--studio",type=Path)
    parser.add_argument("--gateway-installation",type=Path)
    parser.add_argument("--lan-tls",type=Path)
    parser.add_argument("--hold-seconds",type=int,default=0)
    args=parser.parse_args()
    verify(args.output,args.installations,args.registry_installation,args.studio,args.gateway_installation,args.lan_tls,args.hold_seconds)
