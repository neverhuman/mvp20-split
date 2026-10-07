"""Install the independent evaluator, copy owned tests, then qualify its offline image."""

import argparse
import hashlib
import json
import shutil
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from build_numeric_images import ImageBuild
from check_boundaries import ROOT
from install_owner_peer import install

PACKAGE = "amphora-synthetic-objectives-rebuilt"
MODULE = "amphora_synthetic_objectives_rebuilt"
ABSENT = ("amphora_synthetic_objectives", "amphora_evolution_search", "amphora_campaign_runtime",
          "amphora_data_artifacts", "amphora_agent_planning", "sqlalchemy", "rdkit", "torch")


def verify(output, base):
    if not base.startswith("python@sha256:") or len(base.split(":")[-1]) != 64:
        raise ValueError("pinned_python_base_required")
    build = ImageBuild(output)
    output = build.output
    python = install(output / "installed", PACKAGE, ABSENT)
    installed = json.loads((output / "installed/manifest.json").read_bytes())
    tests = output / "owned-tests"
    project = ROOT / "tools/synthetic_objectives_rebuilt"
    shutil.copytree(project / "tests", tests, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    uv = ROOT / ".venv/Scripts/uv.exe"
    build.run([uv, "pip", "install", "--python", python, "pytest>=8,<9", "jsonschema>=4,<5"])
    xml = output / "tests.xml"
    arguments = [str(tests), "--confcutdir=" + str(output), "--import-mode=importlib", "-q", "--tb=short",
                 "--junitxml=" + str(xml)]
    build.run([python, "-I", "-c", "import pytest; raise SystemExit(pytest.main(" + repr(arguments) + "))"])
    suites = ET.parse(xml).getroot().findall("testsuite")
    assert suites and all(int(row.attrib[key]) == 0 for row in suites for key in ("failures", "errors", "skipped"))
    context = output / "image"
    context.mkdir()
    build.run([uv, "export", "--project", project, "--locked", "--no-dev", "--no-emit-local",
               "--output-file", context / "requirements.txt"])
    local = context / "local"
    local.mkdir()
    for name, expected in installed["wheels"].items():
        wheel = output / "installed/wheels" / name
        assert hashlib.sha256(wheel.read_bytes()).hexdigest() == expected
        shutil.copyfile(wheel, local / name)
    download = context / "Download.Dockerfile"
    download.write_text(f"FROM {base}\nCOPY requirements.txt /requirements.txt\n"
        "RUN python -m pip download --require-hashes --only-binary=:all: --dest /resolved -r /requirements.txt\n"
        "COPY local /resolved\n", encoding="utf-8")
    tag = "amphora/synthetic-objectives-rebuilt:bp09-" + uuid.uuid4().hex[:12]
    build.run(["docker", "buildx", "build", "--platform", "linux/amd64", "--load", "--provenance=false",
               "-f", download, "-t", tag + "-dependencies", context])
    container = build.run(["docker", "create", tag + "-dependencies"]).decode().strip()
    try:
        build.run(["docker", "cp", container + ":/resolved", context / "wheels"])
    finally:
        build.run(["docker", "rm", container])
    shutil.copyfile(project / "Dockerfile", context / "Dockerfile")
    metadata = context / "metadata.json"
    build.run(["docker", "buildx", "build", "--platform", "linux/amd64", "--load", "--provenance=false",
               "--build-arg", "PYTHON_BASE=" + base, "--metadata-file", metadata, "-t", tag, context])
    built = json.loads(metadata.read_bytes())
    digest = built["containerimage.digest"]
    inspected = json.loads(build.run(["docker", "image", "inspect", tag]))[0]
    assert digest == inspected.get("Descriptor", {}).get("digest") or any(
        item.endswith("@" + digest) for item in inspected.get("RepoDigests", []))
    assert inspected["Architecture"] == "amd64" and inspected["Os"] == "linux"
    image = digest.removeprefix("sha256:")
    run = ["docker", "run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL",
           "--security-opt", "no-new-privileges", tag]
    release = json.loads(build.run([*run, "describe", "--image-sha256", image]))
    schemas = {}
    for kind, port in (("input", release["tool"]["inputs"][0]), ("policy", release["tool"]["inputs"][1]),
                       ("output", release["tool"]["outputs"][0])):
        raw = build.run([*run, "schema", "--kind", kind])
        assert hashlib.sha256(raw).hexdigest() == port["schema_ref"]["sha256"]
        assert raw == build.run([python, "-I", "-m", MODULE, "schema", "--kind", kind])
        (output / (kind + "-schema.json")).write_bytes(raw)
        schemas[kind] = port["schema_ref"]
    policy = build.run([*run, "policy"])
    assert policy == build.run([python, "-I", "-m", MODULE, "policy"])
    policy_path = output / "policy.json"
    policy_path.write_bytes(policy)
    scope = {"tenant_id": "fixture", "project_id": "rebuilt-evaluator"}
    policy_ref = dict(artifact_id="actual-policy-fixture", scope=scope, sha256=hashlib.sha256(policy).hexdigest(),
                      size_bytes=len(policy), media_type="application/json", schema_ref=schemas["policy"])
    request = {"schema_version": "1", "scope": scope, "evaluation_id": "ev-" + "a" * 64,
        "specification_sha256": "f" * 64,
        "candidate": {"candidate_id": "a" * 64, "generation": 0, "ordinal": 0, "operator": "seed",
            "genes": [1.0, -2.0], "parents": [], "draws": {"start": 0, "end": 2},
            "disposition": "proposed", "reason_code": None, "duplicate_of": None},
        "objectives": [{"objective_id": name, "unit": "dimensionless", "direction": "minimize"}
                       for name in ("cost", "distance")],
        "evaluator": {"tool": release["tool"]["binding"], "constraints": policy_ref,
                      "context": [], "completion": "all_frozen_members_terminal"}}
    body = json.dumps(request).encode()
    expected = build.run([python, "-I", "-m", MODULE, "compute", "--image-sha256", image,
                          "--policy-file", policy_path], body)
    # NAS paths cannot be Docker bind mounts. Put the public fixture in bounded
    # ephemeral tmpfs while retaining the exact built image and read-only root.
    fixture = "import pathlib,runpy,sys; pathlib.Path('/tmp/policy.json').write_bytes(" + repr(policy) + "); "
    fixture += "sys.argv=['compute','compute','--image-sha256'," + repr(image) + ", '--policy-file','/tmp/policy.json']; "
    fixture += "runpy.run_module(" + repr(MODULE) + ",run_name='__main__')"
    actual = build.run(["docker", "run", "--rm", "-i", "--network", "none", "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=1m", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--entrypoint", "python", tag, "-I", "-c", fixture], body)
    assert actual == expected and not actual.endswith(b"\n")
    observation = json.loads(actual)
    assert [item["value"] for item in observation["outcome"]["objectives"]] == [5.0, 9.0]
    probe = "import os,importlib.util; assert os.geteuid()==65532; "
    probe += "assert all(importlib.util.find_spec(name) is None for name in " + repr(ABSENT) + ")"
    build.run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", tag, "-I", "-c", probe])
    evidence = {"profile": "rebuilt-evaluator-offline-v1", "status": "passed", "base": base,
        "installation": installed, "tests": sum(int(row.attrib["tests"]) for row in suites),
        "tag": tag, "image_manifest_digest": digest, "image_config_digest": built["containerimage.config.digest"],
        "descriptor": release, "schemas": schemas, "observation": observation,
        "observation_sha256": hashlib.sha256(actual).hexdigest(), "paid_calls": 0,
        "limits": ["Offline Linux/amd64 golden and installed tests only",
                   "Actual restored owner execution and between-campaign cutover remain separate gates"]}
    build.save(evidence)
    print("Independent evaluator installation and offline image passed: " + digest, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    verify(args.output, args.base)
