"""Test-owned handoff of actual Knowledge output to the public Data SDK."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from amphora_contracts_knowledge import ReasoningResult


def profile(directory):
    # Self-contained configured payload profile: omit publication URN/base overrides.
    document = json.dumps(ReasoningResult.model_json_schema(), sort_keys=True, separators=(",", ":")).encode()
    path = directory / "reasoning-result.schema.json"
    path.write_bytes(document)
    return {"media_type": "application/json", "schema_id": "fixture.knowledge.reasoning-result", "version": "1",
            "sha256": hashlib.sha256(document).hexdigest(), "schema_path": path.name}


def probe(path, mode, environment):
    python = os.environ.get("AMPHORA_TEST_SDK_PYTHON", sys.executable)
    result = subprocess.run([python, "-I", str(Path(__file__).with_name("derived_probe.py")), str(path), mode],
                            env=environment, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, "Public derivation probe failed: " + result.stderr[-2000:]
    return json.loads(result.stdout)
