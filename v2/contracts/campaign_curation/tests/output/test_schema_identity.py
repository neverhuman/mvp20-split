"""Repeated reconstruction reuses fixed schema identity without mutable results."""
import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from amphora_contracts_campaign_curation import CampaignCurationDraft, campaign_curation_draft_schema


def test_repeated_identity_does_not_regenerate_schema_or_change_published_bytes(monkeypatch):
    campaign_curation_draft_schema.cache_clear()
    original = CampaignCurationDraft.model_json_schema
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(CampaignCurationDraft, 'model_json_schema', generate)
    try:
        first = campaign_curation_draft_schema()
        raw = (Path(__file__).resolve().parents[3] / 'schemas/v1/planning.campaign-curation-draft.validation.json').read_bytes()
        assert first.sha256 == hashlib.sha256(raw).hexdigest()
        for _ in range(100):
            assert campaign_curation_draft_schema() == first
        assert calls == [{'mode': 'validation'}]
        with pytest.raises(ValidationError, match='frozen'):
            first.sha256 = '0' * 64
        copied = first.model_dump()
        copied['sha256'] = '0' * 64
        assert campaign_curation_draft_schema().sha256 == hashlib.sha256(raw).hexdigest()
    finally:
        campaign_curation_draft_schema.cache_clear()
