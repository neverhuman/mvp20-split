"""Isolated public-kernel installation plus reconstructed adapter contract tests."""

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from check_boundaries import ROOT
from install_owner_peer import install


def verify(output):
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    forbidden = ["sqlalchemy", "amphora_campaign_runtime", "amphora_agent_planning", "amphora_data_artifacts", "amphora_research"]
    python = install(output / "numeric", "amphora-evolution-search", forbidden)
    uv = ROOT / (".venv/Scripts/uv.exe" if os.name == "nt" else ".venv/bin/uv")
    result = subprocess.run([str(uv), "pip", "install", "--python", str(python), "pytest>=8,<9"], capture_output=True, timeout=120)
    (output / "test-install.log").write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0
    tests = ROOT / "tests/integration/search_recovery"
    args = [str(tests / "test_rebuilt_adapter.py"), "--confcutdir=" + str(tests), "--import-mode=importlib", "-q", "--tb=short",
            "--junitxml=" + str(output / "tests.xml")]
    script = "import importlib.util; assert all(importlib.util.find_spec(m) is None for m in " + repr(forbidden) + "); import pytest; raise SystemExit(pytest.main(" + repr(args) + "))"
    env = {k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC"}}
    env["PYTHONUTF8"] = "1"
    result = subprocess.run([str(python), "-I", "-c", script], cwd=output, env=env, capture_output=True, timeout=180)
    (output / "verification.log").write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, "Reconstruction tests failed; inspect verification.log"
    evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
        "adapter_sha256": hashlib.sha256((tests / "rebuilt_adapter.py").read_bytes()).hexdigest(),
        "kernel_installation": json.loads((output / "numeric/manifest.json").read_bytes()), "tests_xml_sha256": hashlib.sha256((output / "tests.xml").read_bytes()).hexdigest(),
        "limits": ["Reconstructed adapter reuses reviewed public numeric domain exports; not an independent algorithm rewrite",
                   "Fixture descriptors and CLI compute; actual worker transport remains B1.03", "pytest is an additional test-only dependency"], "paid_calls": 0}
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("Isolated adapter reconstruction passed", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    verify(parser.parse_args().output)
