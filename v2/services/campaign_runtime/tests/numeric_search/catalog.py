"""Compile-only catalog from public tool CLIs; declared pins are not built images."""

import json
import subprocess
import sys
from functools import lru_cache
from hashlib import sha256

from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    ResolvedTool,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
)
from amphora_contracts_tools import LockEntry, ReleaseDescriptor

IMAGE = "c" * 64


def cli(module, *arguments):
    return subprocess.run([sys.executable, "-m", module, *arguments], check=True, capture_output=True).stdout


@lru_cache(maxsize=1)
def catalog():
    releases, tools, schemas = {}, [], {}
    for operation in ("seed", "requests", "collect", "vary", "evaluate"):
        numeric = operation != "evaluate"
        module = "amphora_evolution_search" if numeric else "amphora_synthetic_objectives"
        selector = ["--operation", operation] if numeric else []
        release = ReleaseDescriptor.model_validate_json(cli(module, "describe", *selector, "--image-sha256", IMAGE))
        releases[operation] = release.model_dump(mode="json")
        document = {"profile": "amphora-tool-release-v1", "descriptor": releases[operation]}
        digest = sha256(json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        lock = LockEntry.model_validate_json(json.dumps({"tool": release.tool.binding.model_dump(mode="json"),
            "descriptor_sha256": digest, "checkpoint_schema": None,
            **{direction + "_schemas": [{"port": port.name, "schema_ref": port.schema_ref.model_dump(mode="json")}
               for port in getattr(release.tool, direction + "s")] for direction in ("input", "output")}}))
        tools.append(ResolvedTool(release, lock))
        for kind in (("input", "output") if numeric else ("input", "output", "policy")):
            raw = cli(module, "schema", *selector, "--direction" if numeric else "--kind", kind)
            ports = release.tool.outputs if kind == "output" else release.tool.inputs
            port = next(port for port in ports if (port.name == "policy") == (kind == "policy"))
            identity = SchemaIdentity.from_wire(port.schema_ref)
            if identity in schemas:
                assert schemas[identity]._body == raw
            schemas[identity] = PinnedSchema(identity, raw)
    return releases, ToolCatalog(tools), SchemaCatalog(schemas.values())
