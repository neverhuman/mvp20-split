"""Test fixture wire construction using only public contracts and documented canonical bytes."""

import hashlib
import json

from amphora_contracts_tools import LockEntry, ReleaseDescriptor


def release_lock(raw):
    descriptor = ReleaseDescriptor.model_validate_json(json.dumps(raw)).model_dump(mode="json")
    document = {"profile": "amphora-tool-release-v1", "descriptor": descriptor}
    digest = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    tool = descriptor["tool"]
    return LockEntry.model_validate_json(json.dumps({"tool": tool["binding"], "descriptor_sha256": digest,
        "input_schemas": [{"port": port["name"], "schema_ref": port["schema_ref"]} for port in tool["inputs"]],
        "output_schemas": [{"port": port["name"], "schema_ref": port["schema_ref"]} for port in tool["outputs"]],
        "checkpoint_schema": tool["checkpoint_schema"]})).model_dump(mode="json")
