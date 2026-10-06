import hashlib
import json
from pathlib import Path

from export_schemas import ROOT, artifacts


def test_search_step_publication_preserves_all_564_predecessors():
    pins = json.loads((Path(__file__).parent / "fixtures/search_step_predecessor_schema_pins.json").read_bytes())
    assert pins["baseline"] == "6cd6189d" and len(pins["schemas"]) == 564
    for name, expected in pins["schemas"].items():
        assert hashlib.sha256((ROOT / "contracts/schemas" / name).read_bytes()).hexdigest() == expected
    expected = artifacts()
    steps = {name: raw for name, raw in expected.items() if name.startswith("search-step.")}
    assert len(steps) == 6
    assert all((ROOT / "contracts/schemas/v1" / name).read_bytes() == raw for name, raw in steps.items())
