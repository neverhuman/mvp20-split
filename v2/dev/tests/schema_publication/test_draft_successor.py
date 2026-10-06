import hashlib
import json
from pathlib import Path

from export_schemas import ROOT, artifacts


def test_additive_draft_successor_preserves_all630_predecessor_schemas():
    pins = json.loads((Path(__file__).parent / "fixtures/draft_successor_predecessor_schema_pins.json").read_bytes())
    assert pins["baseline"] == "64a6db5c" and len(pins["schemas"]) == 630
    for name, expected in pins["schemas"].items():
        assert hashlib.sha256((ROOT / "contracts/schemas" / name).read_bytes()).hexdigest() == expected
    new = {name: raw for name, raw in artifacts().items() if "draft-successor-admission" in name}
    assert len(new) == 2
    for name, raw in new.items():
        assert (ROOT / "contracts/schemas/v1" / name).read_bytes() == raw
