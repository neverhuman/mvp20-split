import hashlib
import json
from pathlib import Path
from export_schemas import ROOT, artifacts

def test_chemical_structure_preserves_all_668_predecessors():
    pins=json.loads((Path(__file__).parent/"fixtures/chemical_structure_predecessor_schema_pins.json").read_bytes())
    assert pins["baseline"]=="155e2026" and len(pins["schemas"])==668
    for name,expected in pins["schemas"].items():
        assert hashlib.sha256((ROOT/"contracts/schemas"/name).read_bytes()).hexdigest()==expected, name
    new={name:raw for name,raw in artifacts().items() if name.startswith("chemical-structure.")}
    assert len(new)==4
    assert all((ROOT/"contracts/schemas/v1"/name).read_bytes()==raw for name,raw in new.items())

def test_example_pins_exact_semantic_profile():
    root=ROOT/"contracts/chemical_structure"
    example=json.loads((root/"examples/supplied-request.json").read_bytes())
    assert example["semantic_profile"]["sha256"] == hashlib.sha256((root/"profiles/finite-smiles-2d-v1.json").read_bytes()).hexdigest()
