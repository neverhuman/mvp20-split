"""Additive curation and successor publication preserves every predecessor v1 byte."""
import hashlib
import json
from pathlib import Path

from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from export_schemas import ROOT, artifacts, publish


def test_all_predecessor_schema_bytes_preserved():
    pins = json.loads((Path(__file__).parent / 'fixtures/curation_predecessor_schema_pins.json').read_bytes())
    current = artifacts()
    for name, digest in pins['schemas'].items():
        assert hashlib.sha256(current[name]).hexdigest() == digest, name
    # Historical curation increment excludes independently published successor roots.
    historical = {name for name in current if name != 'manifest.json'
                  and not name.startswith(('chemical-structure.', 'population.', 'population-step.', 'campaign-resources.', 'artifact-retention.', 'node-inputs.', 'artifact-ancestry.'))}
    assert len(historical) == len(pins['schemas']) + 22


def test_output_identity_and_publication():
    raw = artifacts()['planning.campaign-curation-draft.validation.json']
    assert hashlib.sha256(raw).hexdigest() == campaign_curation_draft_schema().sha256
    assert publish(ROOT / 'contracts/schemas/v1', check=True) == []
