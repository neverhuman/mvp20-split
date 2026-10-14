import hashlib
import json
from pathlib import Path

from amphora_contracts_population import population_specification_schema, membership_page_schema, membership_manifest_schema
from export_schemas import ROOT, artifacts


def test_population_publication_preserves_predecessor_bytes():
    pins = json.loads((Path(__file__).parent / "fixtures/population_predecessor_schema_pins.json").read_bytes())
    assert pins["baseline"] == "8b866781"
    for name, digest in pins["schemas"].items():
        assert hashlib.sha256((ROOT / "contracts/schemas" / name).read_bytes()).hexdigest() == digest
    published = artifacts()
    for reference in (population_specification_schema(), membership_page_schema(), membership_manifest_schema()):
        name = reference.schema_id + ".validation.json"
        assert hashlib.sha256(published[name]).hexdigest() == reference.sha256
        assert (ROOT / "contracts/schemas/v1" / name).read_bytes() == published[name]
