import hashlib
import json
from pathlib import Path

from amphora_contracts_search import (
    evaluation_observation_schema,
    evaluation_request_schema,
    search_checkpoint_schema,
    search_spec_schema,
)

from export_schemas import ROOT, artifacts


def test_additive_search_schemas_preserve_every_predecessor_byte():
    pins = json.loads((Path(__file__).parent / "fixtures/search_predecessor_schema_pins.json").read_bytes())
    assert pins["baseline"] == "3cd10a7d" and len(pins["schemas"]) == 556
    for name, digest in pins["schemas"].items():
        assert hashlib.sha256((ROOT / "contracts/schemas" / name).read_bytes()).hexdigest() == digest
    published = artifacts()
    names = [name for name in published if name.startswith("search.")]
    assert len(names) == 8
    for reference in (search_spec_schema(), search_checkpoint_schema(), evaluation_request_schema(), evaluation_observation_schema()):
        name = reference.schema_id + ".validation.json"
        assert hashlib.sha256(published[name]).hexdigest() == reference.sha256
        assert (ROOT / "contracts/schemas/v1" / name).read_bytes() == published[name]
