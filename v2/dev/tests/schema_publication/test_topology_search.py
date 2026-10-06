import hashlib
import json
from pathlib import Path
from export_schemas import ROOT, artifacts


def test_topology_transport_preserves_all_622_predecessors():
    pins=json.loads((Path(__file__).parent/'fixtures/topology_search_predecessor_schema_pins.json').read_bytes())
    assert pins['baseline']=='f3b98824' and len(pins['schemas'])==622
    for name,expected in pins['schemas'].items():
        assert hashlib.sha256((ROOT/'contracts/schemas'/name).read_bytes()).hexdigest()==expected
    new={name:raw for name,raw in artifacts().items() if name.startswith('topology-search.')}
    assert len(new)==8
    assert all((ROOT/'contracts/schemas/v1'/name).read_bytes()==raw for name,raw in new.items())
