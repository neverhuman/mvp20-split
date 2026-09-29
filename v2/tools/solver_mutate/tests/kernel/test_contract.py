"""Exact published boundary and independent literal stage oracle."""

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from amphora_contracts_solver_fixture import ProposalBatch, Selection
from amphora_solver_mutate.kernel import compute
from amphora_solver_mutate.metadata import descriptor, schema_bytes


def golden():
    return json.loads((Path(__file__).parents[1] / "fixtures/golden.json").read_bytes())


def test_literal_golden_and_standalone_compute():
    case = golden()
    assert json.loads(compute(json.dumps(case["input"]))) == case["output"]
    result = subprocess.run([sys.executable, "-I", "-m", "amphora_solver_mutate", "compute"],
        input=json.dumps(case["input"]), capture_output=True, text=True, timeout=15)
    assert result.returncode == 0 and json.loads(result.stdout) == case["output"]


def test_schema_bytes_descriptor_and_synthetic_authority():
    for kind, model in (("input", Selection), ("output", ProposalBatch)):
        expected = (json.dumps(model.model_json_schema(mode="validation"), sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()
        assert schema_bytes(kind) == expected
    release = descriptor("c" * 64)  # Explicit non-deployable test identity.
    assert release.tool.binding.release == "0.1.0" and release.authority_ceiling == "synthetic_only"
    assert release.tool.inputs[0].schema_ref.sha256 == hashlib.sha256(schema_bytes("input")).hexdigest()


def test_changed_source_pin_is_rejected_before_stage_behavior():
    value = copy.deepcopy(golden()["input"])
    pins = value
    for key in ['state', 'config', 'source_pins']:
        pins = pins[key]
    pins["cli"] = "b" * 64
    with pytest.raises(ValueError, match="solver_source_hash_changed"):
        compute(json.dumps(value))
