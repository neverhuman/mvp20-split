"""Independent authored failure oracles, never derived from compiler findings."""

import copy
import json

import pytest
from amphora_campaign_runtime.compiler import CompilationError, compile_campaign
from pydantic import ValidationError

from .conftest import FIXTURES, definition

CASES = json.loads((FIXTURES / "rejections.json").read_bytes())


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_named_rejection(compiler_env, case):
    env = compiler_env
    raw = copy.deepcopy(env.raw[case["base"]])
    for edit in case["edits"]:
        target = raw
        for key in edit["path"][:-1]:
            target = target[key]
        key = edit["path"][-1]
        if edit.get("remove"):
            del target[key]
        elif isinstance(target, list) and key == len(target):
            target.append(copy.deepcopy(edit["value"]))
        else:
            target[key] = copy.deepcopy(edit["value"])
    if case["code"] == "wire_validation":
        with pytest.raises(ValidationError):
            definition(raw)
        return
    with pytest.raises(CompilationError) as caught:
        compile_campaign(definition(raw), env.tools, env.schemas)
    assert caught.value.findings[0].code == case["code"]
    # A rejected compilation cannot poison the next compilation or mutate the golden input.
    assert compile_campaign(definition(env.raw[0]), env.tools, env.schemas).model_dump(mode="json") == env.expected
