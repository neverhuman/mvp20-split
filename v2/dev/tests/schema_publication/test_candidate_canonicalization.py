import hashlib
import json
from pathlib import Path
from export_schemas import ROOT, artifacts


def test_canonical_receipt_is_additive_to_602_predecessors():
    pins=json.loads((Path(__file__).parent/'fixtures/canonical_candidate_predecessor_schema_pins.json').read_bytes())
    assert pins['baseline']=='de27948a' and len(pins['schemas'])==602
    for name,expected in pins['schemas'].items():
        assert hashlib.sha256((ROOT/'contracts/schemas'/name).read_bytes()).hexdigest()==expected
    new={name:raw for name,raw in artifacts().items() if name.startswith('candidate-canonicalization.')}
    assert len(new)==2
    assert all((ROOT/'contracts/schemas/v1'/name).read_bytes()==raw for name,raw in new.items())
