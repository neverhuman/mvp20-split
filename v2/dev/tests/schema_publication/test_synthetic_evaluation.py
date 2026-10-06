import hashlib
import json
from pathlib import Path
from export_schemas import ROOT, artifacts


def test_synthetic_evaluation_is_additive_to_606_predecessors():
    pins=json.loads((Path(__file__).parent/'fixtures/synthetic_evaluation_predecessor_schema_pins.json').read_bytes())
    assert pins['baseline']=='1db7821b' and len(pins['schemas'])==606
    for name,expected in pins['schemas'].items():
        assert hashlib.sha256((ROOT/'contracts/schemas'/name).read_bytes()).hexdigest()==expected
    new={name:raw for name,raw in artifacts().items() if name.startswith('synthetic-evaluation.')}
    assert len(new)==2
    assert all((ROOT/'contracts/schemas/v1'/name).read_bytes()==raw for name,raw in new.items())
