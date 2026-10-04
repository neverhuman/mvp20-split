"""Compile the exact public definition in an independent owner install without SQL access."""

import json
import os
import sys
from pathlib import Path

from amphora_campaign_runtime.compiler import PinnedSchema, SchemaCatalog, SchemaIdentity, ToolCatalog
from amphora_campaign_runtime.coordinator import ReviewedPlan
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import SchemaRef

assert not any("DATABASE_URL" in key for key in os.environ)
path = Path(sys.argv[1])
config = json.loads(path.read_bytes())
plans = {}
for entry in config["graphs"]:
    assert not entry["releases"]
    schemas = [PinnedSchema(SchemaIdentity.from_wire(SchemaRef.model_validate_json(json.dumps(schema["schema_ref"]))),
        (path.parent / schema["path"]).read_bytes()) for schema in entry["schemas"]]
    definition = parse_executable_campaign((path.parent / entry["definition"]).read_bytes())
    plans[definition.campaign_id] = ReviewedPlan.compile(definition, ToolCatalog([]), SchemaCatalog(schemas)).plan.model_dump(mode="json")
print(json.dumps(plans))
