"""New explicit output and decision profiles preserve every predecessor byte."""

import hashlib
import json

from amphora_contracts_planning import checkpoint_draft_schema

from export_schemas import ROOT, publish


def test_checkpoint_output_publication_and_predecessor_identity():
    pins = json.loads((ROOT / 'contracts/supervision/tests/fixtures/effects_predecessor_schema_pins.json').read_bytes())
    assert len(pins['schemas']) == 538
    for name, digest in pins['schemas'].items():
        assert hashlib.sha256((ROOT / 'contracts/schemas' / name).read_bytes()).hexdigest() == digest
    for version in ('1', '2', '3', '4'):
        assert publish(ROOT / 'contracts/schemas' / ('v' + version), check=True, version=version) == []
    raw = (ROOT / 'contracts/schemas/v1/planning.checkpoint-draft.validation.json').read_bytes()
    assert checkpoint_draft_schema().sha256 == hashlib.sha256(raw).hexdigest()
