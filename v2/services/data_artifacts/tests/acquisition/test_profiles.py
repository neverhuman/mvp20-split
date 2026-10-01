import hashlib
import json

import pytest
from amphora_contracts_artifacts import ContentDescriptor
from amphora_contracts_evidence import prepared_schema
from amphora_data_artifacts.acquisition.profiles import PreparedContentRule
from amphora_data_artifacts.publication.model import ContentPolicy, UploadError


@pytest.mark.parametrize("kind,value", [
    ("document", {"wire_version": "1", "text": "notes"}),
    ("lab", dict.fromkeys(["candidate_id", "candidate_revision", "sample_id", "sample_revision",
                          "method", "context", "value", "unit"]) | {"wire_version": "1"}),
])
def test_pinned_preparation_profiles_validate_actual_content(kind, value):
    rule = PreparedContentRule(kind)
    policy = ContentPolicy(frozenset({rule.identity}), rules=(rule,))

    def validate(body):
        raw = json.dumps(body).encode()
        descriptor = ContentDescriptor(sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw),
                                       media_type="application/json", schema_ref=prepared_schema(kind))
        policy.validate(descriptor, raw)

    validate(value)
    for invalid in (value | {"unexpected": True}, value | {"wire_version": "2"}, {}, [],
                    value | {"text" if kind == "document" else "unit": 12}):
        with pytest.raises(UploadError, match="content_schema_mismatch"):
            validate(invalid)


def test_unknown_preparation_profile_is_not_installed():
    with pytest.raises(ValueError, match="Unknown prepared content profile"):
        PreparedContentRule("unknown")
