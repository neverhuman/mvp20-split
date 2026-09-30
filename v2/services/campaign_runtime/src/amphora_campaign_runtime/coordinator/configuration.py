"""Trusted local graph allowlists compile from exact public descriptors and schema bytes."""

import json
from pathlib import Path

from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import SchemaRef
from amphora_contracts_tools import LockEntry, ReleaseDescriptor

from ..compiler import PinnedSchema, ResolvedTool, SchemaCatalog, SchemaIdentity, ToolCatalog
from .plans import PlanCatalog, ReviewedPlan


def _bytes(root, name, maximum):
    with (root / name).open("rb") as source:
        value = source.read(maximum + 1)
    if len(value) > maximum:
        raise ValueError("Graph configuration resource too large")
    return value


def load_materials(entry, root):
    """Load exact reviewed compiler inputs; shared with scoped draft validation."""
    if not isinstance(entry, dict) or set(entry) != {"definition", "releases", "schemas"}:
        raise ValueError("Invalid graph allowlist entry")
    if not isinstance(entry["releases"], list) or len(entry["releases"]) > 64 or not isinstance(entry["schemas"], list) or len(entry["schemas"]) > 256:
        raise ValueError("Graph configuration material bound")
    tools, schemas = [], []
    for tool in entry["releases"]:
        if set(tool) != {"descriptor", "lock"}:
            raise ValueError("Invalid graph release entry")
        tools.append(ResolvedTool(ReleaseDescriptor.model_validate_json(_bytes(Path(root), tool["descriptor"], 262144)),
                                  LockEntry.model_validate_json(json.dumps(tool["lock"]))))
    for schema in entry["schemas"]:
        if set(schema) != {"schema_ref", "path"}:
            raise ValueError("Invalid graph schema entry")
        reference = SchemaRef.model_validate_json(json.dumps(schema["schema_ref"]))
        schemas.append(PinnedSchema(SchemaIdentity.from_wire(reference), _bytes(Path(root), schema["path"], 65536)))
    return tuple(tools), tuple(schemas)


def load_graphs(entries, root):
    if not isinstance(entries, list) or not 1 <= len(entries) <= 64:
        raise ValueError("Explicit bounded graph allowlist required")
    result = []
    for entry in entries:
        tools, schemas = load_materials(entry, root)
        definition = parse_executable_campaign(_bytes(Path(root), entry["definition"], 1048576))
        result.append((ReviewedPlan.compile(definition, ToolCatalog(tools), SchemaCatalog(schemas)), tools, schemas))
    return tuple(result)


def load_catalog(entries, root):
    return PlanCatalog(item[0] for item in load_graphs(entries, root))
