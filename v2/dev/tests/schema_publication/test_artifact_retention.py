import hashlib
import json
from pathlib import Path

from export_schemas import ROOT, artifacts


def test_additive_retention_preserves_all744_predecessor_schema_bytes():
    pins = json.loads((Path(__file__).parent / "fixtures/artifact_retention_predecessor_schema_pins.json").read_bytes())
    assert pins["baseline"] == "744914cb" and len(pins["schemas"]) == 744
    for name, expected in pins["schemas"].items():
        assert hashlib.sha256((ROOT / "contracts/schemas" / name).read_bytes()).hexdigest() == expected


def test_explicit_retention_roots_publish_separately():
    roots = {name: raw for name, raw in artifacts().items() if name.startswith("artifact-retention.")}
    assert len(roots) == 4
    for name, raw in roots.items():
        assert (ROOT / "contracts/schemas/v1" / name).read_bytes() == raw
