import json

import pytest
from amphora_contracts_graph_runtime import DigestViewFilter, GraphViewCatalog, RadiusViewFilter
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from .test_observations import CUT


def test_catalog_root_roundtrip_and_filter_bounds():
    catalog = GraphViewCatalog.model_validate_json(json.dumps({"cut": CUT, "views": [{
        "view_id": "execution_topology", "result_schema": "graph-runtime.topology-page",
        "required_capability": "runtime.authored-topology.v1", "result_bound": 256,
        "filters": [{"kind": "digest", "name": "scope_key", "required": True}, {"kind": "integer"}]}]}))
    Draft202012Validator(GraphViewCatalog.model_json_schema(mode="serialization")).validate(catalog.model_dump(mode="json"))
    assert GraphViewCatalog.model_validate_json(catalog.model_dump_json()) == catalog
    with pytest.raises(ValidationError):
        DigestViewFilter(name="sql", required=True)
    with pytest.raises(ValidationError):
        RadiusViewFilter(maximum=3)
