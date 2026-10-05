"""New campaign draft publication cannot silently reinterpret an old wire root."""

import hashlib
import json

from amphora_contracts_planning import campaign_draft_schema

from export_schemas import ROOT, publish


def test_campaign_profile_preserves_all_508_predecessor_schema_bytes():
    pins = json.loads((ROOT / 'contracts/planning/tests/campaign_output/fixtures/predecessor_schema_pins.json').read_bytes())
    assert pins['baseline'] == '8308016a'
    assert len(pins['schemas']) == 508
    for name, digest in pins['schemas'].items():
        assert hashlib.sha256((ROOT / 'contracts/schemas' / name).read_bytes()).hexdigest() == digest
    for version in ('1', '2', '3', '4'):
        assert publish(ROOT / 'contracts/schemas' / ('v' + version), check=True, version=version) == []
    raw = (ROOT / 'contracts/schemas/v1/planning.campaign-draft.validation.json').read_bytes()
    assert campaign_draft_schema().sha256 == hashlib.sha256(raw).hexdigest()
