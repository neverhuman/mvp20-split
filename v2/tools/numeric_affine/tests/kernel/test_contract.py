"""Language-neutral payload publication and executable compatibility."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from amphora_numeric_affine.metadata import descriptor, schema_bytes
from amphora_numeric_affine.payloads import AffineInput, AffineOutput
from jsonschema import Draft202012Validator


def test_published_payload_schemas_match_tool_boundary():
    for kind, model in (("input", AffineInput), ("output", AffineOutput)):
        expected = (json.dumps(model.model_json_schema(mode="validation"), sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()
        assert schema_bytes(kind) == expected
    release = descriptor("c" * 64)  # Explicit test-only image identity, never deployment evidence.
    assert release.tool.binding.release == "0.3.0"
    assert release.tool.inputs[0].schema_ref.sha256 == hashlib.sha256(schema_bytes("input")).hexdigest()
    assert release.tool.outputs[0].schema_ref.sha256 == hashlib.sha256(schema_bytes("output")).hexdigest()
    assert release.authority_ceiling == "synthetic_only" and release.tool.side_effects == "pure"


def test_executable_against_independent_golden():
    golden = json.loads((Path(__file__).parent.parent / "fixtures/golden.json").read_bytes())
    for kind in ("input", "output"):
        Draft202012Validator(json.loads(schema_bytes(kind))).validate(golden[kind])
    result = subprocess.run([sys.executable, "-m", "amphora_numeric_affine", "compute"],
        input=json.dumps(golden["input"]), text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == golden["output"]
    invalid = subprocess.run([sys.executable, "-m", "amphora_numeric_affine", "compute"],
        input='{"private_payload":"invalid"}', text=True, capture_output=True, timeout=15)
    assert invalid.returncode == 2 and invalid.stdout == ""
    assert invalid.stderr.strip() == "invalid_tool_input_or_configuration"
