"""Independent deployment-package CLI replacement and selected-local-host proof."""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from check_boundaries import ROOT
from install_owner_peer import install
from verify_local_preflight import verify as preflight


def verify(output, baseline, storage, runtime):
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    forbidden = ["pydantic", "sqlalchemy", "amphora_campaign_runtime", "amphora_data_artifacts", "amphora_agent_planning"]
    python = install(output / "package", "amphora-deployment", forbidden)
    profile = baseline.absolute() / "profile.json"
    original = profile.read_bytes()
    replies = []
    for interpreter in (sys.executable, python):
        result = subprocess.run([str(interpreter), "-I", "-m", "amphora_deployment", "validate", "--profile", str(profile)],
                                capture_output=True, timeout=15, check=True)
        replies.append(json.loads(result.stdout))
    assert replies[0] == replies[1] and profile.read_bytes() == original
    preflight(output / "actual-host", storage, runtime, python)
    uv = ROOT / ".venv/Scripts/uv.exe"
    result = subprocess.run([str(uv), "pip", "install", "--python", str(python), "pytest>=8,<9"], capture_output=True, timeout=120)
    (output / "pytest-install.log").write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0
    tests = ROOT / "deploy/local/tests/preflight"
    result = subprocess.run([str(python), "-I", "-m", "pytest", str(tests), "--confcutdir=" + str(tests),
                             "--import-mode=importlib", "-q", "--junitxml=" + str(output / "tests.xml")],
                            cwd=output, capture_output=True, timeout=120)
    (output / "tests.log").write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, "Independent preflight tests failed; inspect tests.log"
    evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
        "installation": json.loads((output / "package/manifest.json").read_bytes()),
        "original_profile_sha256": hashlib.sha256(original).hexdigest(), "validation_before_after": replies,
        "actual_host": json.loads((output / "actual-host/evidence.json").read_bytes()),
        "tests_xml_sha256": hashlib.sha256((output / "tests.xml").read_bytes()).hexdigest(),
        "limits": ["No service deployment, migration, backup or paid provider call", "pytest is a test-only installation addition"], "paid_calls": 0}
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("Independent deployment package, CLI replacement and selected local preflight passed", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "baseline", "storage", "runtime"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.baseline, args.storage, args.runtime)
