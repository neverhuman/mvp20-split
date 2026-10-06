import hashlib
import json
from pathlib import Path
from export_schemas import ROOT, artifacts


def test_fitness_is_additive_to_590_predecessors():
    pins = json.loads((Path(__file__).parent/'fixtures/fitness_predecessor_schema_pins.json').read_bytes())
    assert pins['baseline'] == '48629a29' and len(pins['schemas']) == 590
    for name,expected in pins['schemas'].items():
        assert hashlib.sha256((ROOT/'contracts/schemas'/name).read_bytes()).hexdigest() == expected
    new = {name:raw for name,raw in artifacts().items() if name.startswith('fitness.')}
    assert len(new) == 12
    assert all((ROOT/'contracts/schemas/v1'/name).read_bytes() == raw for name,raw in new.items())
