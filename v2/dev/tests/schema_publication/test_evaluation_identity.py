import hashlib
import json
from pathlib import Path
from export_schemas import ROOT, artifacts


def test_evaluation_identity_additive_to_584_predecessors():
    pins = json.loads((Path(__file__).parent / 'fixtures/evaluation_identity_predecessor_schema_pins.json').read_bytes())
    assert pins['baseline'] == 'a86f0c6e' and len(pins['schemas']) == 584
    for name, expected in pins['schemas'].items():
        assert hashlib.sha256((ROOT / 'contracts/schemas' / name).read_bytes()).hexdigest() == expected
    new = {name: raw for name, raw in artifacts().items() if name.startswith('evaluation-identity.')}
    assert len(new) == 6
    assert all((ROOT / 'contracts/schemas/v1' / name).read_bytes() == raw for name, raw in new.items())
