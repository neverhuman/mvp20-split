"""Test-only owner compiler probe in an independent Runtime install, with no SQL credentials."""

import json
import os
import sys
from pathlib import Path

from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    ResolvedTool,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
)
from amphora_campaign_runtime.coordinator import ReviewedPlan
from amphora_contracts_campaigns import ExecutableCampaign
from amphora_contracts_core import SchemaRef
from amphora_contracts_tools import LockEntry, ReleaseDescriptor


def main():
    assert not any("DATABASE_URL" in key for key in os.environ)
    path = Path(sys.argv[1])
    config = json.loads(path.read_bytes())
    result = {}
    for entry in config["graphs"]:
        tools = [ResolvedTool(ReleaseDescriptor.model_validate_json((path.parent / tool["descriptor"]).read_bytes()),
                              LockEntry.model_validate_json(json.dumps(tool["lock"]))) for tool in entry["releases"]]
        schemas = [PinnedSchema(SchemaIdentity.from_wire(SchemaRef.model_validate_json(json.dumps(schema["schema_ref"]))),
                                (path.parent / schema["path"]).read_bytes()) for schema in entry["schemas"]]
        definition = ExecutableCampaign.model_validate_json((path.parent / entry["definition"]).read_bytes())
        plan = ReviewedPlan.compile(definition, ToolCatalog(tools), SchemaCatalog(schemas)).plan
        result[definition.campaign_id] = plan.model_dump(mode="json")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
