"""Pinned public golden material, separate from compiler algorithms and live peer proof."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    ResolvedTool,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
)
from amphora_contracts_campaigns import ExecutableCampaign
from amphora_contracts_tools import LockEntry, ReleaseDescriptor

ROOT = Path(__file__).absolute().parents[4]
FIXTURES = Path(__file__).parents[1] / "fixtures/compiler"
CASES = json.loads((ROOT / "contracts/fixtures/v2/executable_cases.json").read_bytes())


@pytest.fixture
def compiler_env():
    expected = next(case["payload"] for case in CASES if case["model"] == "campaigns.execution-plan" and case["valid"])
    lock = LockEntry.model_validate_json(json.dumps(expected["document"]["lock"]["tools"][0]))
    descriptor = ReleaseDescriptor.model_validate_json((FIXTURES / "numeric-release.json").read_bytes())
    tool = ResolvedTool(descriptor, lock)
    schemas = [PinnedSchema(SchemaIdentity.from_wire(getattr(lock, name + "_schemas")[0].schema_ref),
                            (FIXTURES / (name + ".json")).read_bytes()) for name in ("input", "output")]
    raw = [copy.deepcopy(case["payload"]) for case in CASES if case["model"] == "campaigns.definition" and case["valid"]]
    return SimpleNamespace(raw=raw, expected=expected, tool=tool, tools=ToolCatalog([tool]),
                           schemas=SchemaCatalog(schemas), schema_list=schemas)


def definition(raw):
    return ExecutableCampaign.model_validate_json(json.dumps(raw))
