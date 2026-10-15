import hashlib
import json
from pathlib import Path
from export_schemas import ROOT, artifacts


def test_node_inputs_preserves_all748_predecessor_bytes():
    pins = json.loads((Path(__file__).parent / "fixtures/node_inputs_predecessor_schema_pins.json").read_bytes())
    assert pins["baseline"] == "77d39f7a" and len(pins["schemas"]) == 748
    for name, digest in pins["schemas"].items():
        assert hashlib.sha256((ROOT / "contracts/schemas" / name).read_bytes()).hexdigest() == digest
    new = {name: raw for name, raw in artifacts().items() if name.startswith("node-inputs.")}
    assert len(new) == 2
    assert all((ROOT / "contracts/schemas/v1" / name).read_bytes() == raw for name, raw in new.items())
