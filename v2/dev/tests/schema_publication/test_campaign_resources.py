import hashlib
import json
from pathlib import Path

from export_schemas import ROOT, artifacts


def test_bounded_admission_preserves_all740_predecessor_schemas():
    pins = json.loads((Path(__file__).parent / "fixtures/campaign_resources_predecessor_schema_pins.json").read_bytes())
    assert pins["baseline"] == "215fd356" and len(pins["schemas"]) == 740
    for name, expected in pins["schemas"].items():
        assert hashlib.sha256((ROOT / "contracts/schemas" / name).read_bytes()).hexdigest() == expected


def test_resource_schemas_are_published_separately():
    new = {name: raw for name, raw in artifacts().items() if name.startswith("campaign-resources.")}
    assert len(new) == 4
    for name, raw in new.items():
        assert (ROOT / "contracts/schemas/v1" / name).read_bytes() == raw
