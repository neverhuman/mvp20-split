"""Explicit test-only tool identities; actual image acceptance belongs to V1."""

import hashlib
import json

from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    ResolvedTool,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
)
from amphora_contracts_tools import LockEntry
from amphora_solver_mutate import kernel as mutate_kernel
from amphora_solver_mutate import metadata as mutate
from amphora_solver_retain import kernel as retain_kernel
from amphora_solver_retain import metadata as retain
from amphora_solver_score import kernel as score_kernel
from amphora_solver_score import metadata as score
from amphora_solver_seed import kernel as seed_kernel
from amphora_solver_seed import metadata as seed
from amphora_solver_select import kernel as select_kernel
from amphora_solver_select import metadata as select

STAGES = {"seed": (seed, seed_kernel), "select": (select, select_kernel), "mutate": (mutate, mutate_kernel),
          "score": (score, score_kernel), "retain": (retain, retain_kernel)}


def catalog():
    tools, schemas, releases = [], {}, {}
    for stage, (metadata, _kernel) in STAGES.items():
        release = metadata.descriptor("c" * 64)  # Synthetic identity, never registered/deployed.
        releases[stage] = release.model_dump(mode="json")
        document = {"profile": "amphora-tool-release-v1", "descriptor": releases[stage]}
        digest = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"),
                                          ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        lock = LockEntry.model_validate_json(json.dumps({"tool": release.tool.binding.model_dump(mode="json"),
            "descriptor_sha256": digest,
            "input_schemas": [{"port": port.name, "schema_ref": port.schema_ref.model_dump(mode="json")} for port in release.tool.inputs],
            "output_schemas": [{"port": port.name, "schema_ref": port.schema_ref.model_dump(mode="json")} for port in release.tool.outputs],
            "checkpoint_schema": None}))
        tools.append(ResolvedTool(release, lock))
        for kind in ("input", "output"):
            identity = SchemaIdentity.from_wire(metadata.schema_ref(kind))
            body = metadata.schema_bytes(kind)
            if identity in schemas:
                assert schemas[identity]._body == body
            schemas[identity] = PinnedSchema(identity, body)
    return releases, ToolCatalog(tools), SchemaCatalog(schemas.values())
