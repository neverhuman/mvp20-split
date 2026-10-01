import hashlib

from amphora_contracts_evidence import prepared_schema
from export_schemas import artifacts


def test_packaged_preparation_profiles_match_published_validation_bytes():
    published = artifacts("1")
    for profile in ("document", "lab"):
        ref = prepared_schema(profile)
        assert ref.sha256 == hashlib.sha256(published[ref.schema_id + ".validation.json"]).hexdigest()
