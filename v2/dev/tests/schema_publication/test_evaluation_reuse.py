import hashlib
import json
from pathlib import Path
from export_schemas import ROOT, artifacts


def test_evaluation_reuse_is_additive_to_608_predecessors():
    pins=json.loads((Path(__file__).parent/'fixtures/evaluation_reuse_predecessor_schema_pins.json').read_bytes())
    assert pins['baseline']=='0225865e' and len(pins['schemas'])==608
    for name,expected in pins['schemas'].items():
        assert hashlib.sha256((ROOT/'contracts/schemas'/name).read_bytes()).hexdigest()==expected
    new={name:raw for name,raw in artifacts().items() if name.startswith('evaluation-reuse.')}
    assert len(new)==14
    assert all((ROOT/'contracts/schemas/v1'/name).read_bytes()==raw for name,raw in new.items())
