"""Fresh installed compiler consumer: only public Registry reads and supplied schema bytes."""

import base64
import hashlib
import importlib.util
import json
import os
import sys
from urllib.request import ProxyHandler, Request, build_opener

from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    ResolvedTool,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
    compile_campaign,
)
from amphora_contracts_campaigns import ExecutableCampaign, ExecutionPlan
from amphora_contracts_tools import ReleaseSnapshot


def main():
    assert not any("DATABASE" in key or "MIGRATION" in key for key in os.environ)
    for absent in ("amphora_capability_registry", "amphora_data_artifacts", "amphora_numeric_affine", "amphora_sequence_statistics"):
        assert importlib.util.find_spec(absent) is None
    request = json.loads(sys.stdin.read())
    schemas = [PinnedSchema(SchemaIdentity(value["schema_id"], value["version"], value["sha256"]),
                            base64.b64decode(value["body"], validate=True)) for value in request["schemas"]]
    releases = []
    for digest in request["releases"]:
        query = Request(request["endpoint"] + "/v1/releases/" + digest, headers={"Authorization": "Bearer " + request["token"]})
        with build_opener(ProxyHandler({})).open(query, timeout=10) as response:
            release = ReleaseSnapshot.model_validate_json(response.read())
        assert release.lock.descriptor_sha256 == digest
        assert release.scope.model_dump(mode="json") == request["scope"]
        releases.append(ResolvedTool(release.descriptor, release.lock))
    tools, schemas = ToolCatalog(releases), SchemaCatalog(schemas)
    plans = [compile_campaign(ExecutableCampaign.model_validate_json(json.dumps(raw)), tools, schemas).model_dump(mode="json")
             for raw in request["definitions"]]
    for raw in request.get("retained", []):
        plan = ExecutionPlan.model_validate_json(json.dumps(raw))
        document = json.dumps(plan.document.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                              ensure_ascii=True, allow_nan=False).encode()
        assert hashlib.sha256(document).hexdigest() == plan.sha256
        assert plan.model_dump(mode="json") == raw
    print(json.dumps(plans, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False))


if __name__ == "__main__":
    main()
