"""Origin publication pins the additive read root, preserving old schema files."""

import hashlib
from amphora_contracts_planning import campaign_origin_schema
from export_schemas import ROOT, publish


def test_campaign_origin_publication():
    raw = (ROOT / 'contracts/schemas/v1/planning.campaign-origin.validation.json').read_bytes()
    assert campaign_origin_schema().sha256 == hashlib.sha256(raw).hexdigest()
    assert publish(ROOT / 'contracts/schemas/v1', check=True) == []
