"""Additive supervisor roots preserve every pre-existing public schema byte."""

import hashlib
import json

from export_schemas import ROOT, publish


def test_supervisor_request_publication_preserves_510_predecessors():
    pins = json.loads((ROOT / 'contracts/supervision/tests/fixtures/predecessor_schema_pins.json').read_bytes())
    assert pins['baseline'] == '975da46e' and len(pins['schemas']) == 510
    for name, digest in pins['schemas'].items():
        assert hashlib.sha256((ROOT / 'contracts/schemas' / name).read_bytes()).hexdigest() == digest
    for version in ('1', '2', '3', '4'):
        assert publish(ROOT / 'contracts/schemas' / ('v' + version), check=True, version=version) == []
