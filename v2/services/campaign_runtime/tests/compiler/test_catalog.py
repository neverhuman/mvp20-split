"""Exact public descriptor/lock compatibility and initial profile restrictions."""

import hashlib
import json

import pytest
from amphora_campaign_runtime.compiler import CompilationError, ResolvedTool, ToolCatalog, compile_campaign
from amphora_contracts_tools import LockEntry, ReleaseDescriptor

from .conftest import definition


def descriptor_pair(raw, lock):
    descriptor = ReleaseDescriptor.model_validate_json(json.dumps(raw))
    document = {"profile": "amphora-tool-release-v1", "descriptor": descriptor.model_dump(mode="json")}
    lock["descriptor_sha256"] = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"),
                                                        ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return descriptor, LockEntry.model_validate_json(json.dumps(lock))


@pytest.mark.parametrize("change,code", [
    ("digest", "descriptor_digest_mismatch"), ("tool", "tool_lock_mismatch"),
    ("input", "schema_lock_mismatch"), ("checkpoint", "checkpoint_lock_mismatch"),
])
def test_lock_tampering(compiler_env, change, code):
    env = compiler_env
    raw = env.tool.lock.model_dump(mode="json")
    if change == "digest":
        raw["descriptor_sha256"] = "0" * 64
    elif change == "tool":
        raw["tool"]["release"] = "9.9.9"
    elif change == "input":
        raw["input_schemas"][0]["schema_ref"] = raw["output_schemas"][0]["schema_ref"]
    else:
        raw["checkpoint_schema"] = raw["output_schemas"][0]["schema_ref"]
    with pytest.raises(CompilationError, match=code):
        ResolvedTool(env.tool.descriptor, LockEntry.model_validate_json(json.dumps(raw)))


@pytest.mark.parametrize("change,code", [
    ("authority", "unsupported_compiler_tool_profile"),
    ("optional-output", "unsupported_optional_tool_output"),
    ("duplicate-port", "duplicate_tool_port"),
])
def test_unsupported_descriptor_semantics(compiler_env, change, code):
    env = compiler_env
    raw, lock = env.tool.descriptor.model_dump(mode="json"), env.tool.lock.model_dump(mode="json")
    if change == "authority":
        raw["authority_ceiling"] = "evidence_proposal"
    elif change == "optional-output":
        raw["tool"]["outputs"][0]["required"] = False
    else:
        raw["tool"]["inputs"].append(raw["tool"]["inputs"][0])
        lock["input_schemas"].append(lock["input_schemas"][0])
    descriptor, lock = descriptor_pair(raw, lock)
    with pytest.raises(CompilationError, match=code):
        ResolvedTool(descriptor, lock)


def test_duplicate_catalog_pins(compiler_env):
    with pytest.raises(CompilationError, match="duplicate_tool_identity"):
        ToolCatalog([compiler_env.tool, compiler_env.tool])


def test_checkpoint_mapping_requires_exact_declared_schema(compiler_env):
    env = compiler_env
    descriptor, lock = env.tool.descriptor.model_dump(mode="json"), env.tool.lock.model_dump(mode="json")
    schema = descriptor["tool"]["inputs"][0]["schema_ref"]
    descriptor["tool"]["checkpoint_schema"] = lock["checkpoint_schema"] = schema
    descriptor["checkpoint"] = {"mode": "opaque_artifact", "readable_schema_sha256": [schema["sha256"]]}
    descriptor, lock = descriptor_pair(descriptor, lock)
    tools = ToolCatalog([ResolvedTool(descriptor, lock)])
    raw = env.raw[0]
    raw["body"]["nodes"][0]["checkpoint"] = {"kind": "input", "name": "parameters"}
    plan = compile_campaign(definition(raw), tools, env.schemas)
    assert plan.document.lock.tools[0].checkpoint_schema == lock.checkpoint_schema
    raw["body"]["inputs"].append({"name": "checkpoint", "value_type": raw["body"]["outputs"][0]["value_type"]})
    raw["body"]["nodes"][0]["checkpoint"]["name"] = "checkpoint"
    with pytest.raises(CompilationError, match="checkpoint_schema_mismatch"):
        compile_campaign(definition(raw), tools, env.schemas)
