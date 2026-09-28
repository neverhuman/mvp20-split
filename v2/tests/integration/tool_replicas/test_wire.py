"""Fixture lock conformance against preserved independent public contract goldens."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("replica_wire_test", Path(__file__).with_name("wire.py"))
wire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wire)
CASES = json.loads((Path(__file__).parents[3] / "contracts/fixtures/v1/tool_releases.json").read_bytes())


@pytest.mark.parametrize("case", CASES, ids=lambda value: value["name"])
def test_preserved_release_lock(case):
    assert wire.release_lock(case["descriptor"]) == case["lock"]
