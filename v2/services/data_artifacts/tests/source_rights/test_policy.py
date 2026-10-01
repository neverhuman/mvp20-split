import json
from datetime import UTC, datetime, timedelta

import pytest
from amphora_contracts_evidence import SourceRightsRevision
from amphora_data_artifacts.source_rights.model import RightsError, RightsPolicy


def record():
    return SourceRightsRevision.model_validate_json(json.dumps({"wire_version": "1",
        "reference": {"scope": {"tenant_id": "fixture", "project_id": "rights"}, "rights_id": "policy", "revision": 1},
        "supersedes": None, "status": "granted", "allowed_uses": ["read", "process"],
        "expires_at": None, "retention": "retain_audit_payload"}))


@pytest.mark.parametrize("patch,code", [
    ({"allowed_uses": ("read", "read")}, "rights_duplicate_use"),
    ({"allowed_uses": ()}, "rights_invalid_grant"),
    ({"allowed_uses": ("process",)}, "rights_process_requires_read"),
    ({"status": "revoked"}, "rights_invalid_grant"),
])
def test_invalid_policy_combinations_rejected(patch, code):
    with pytest.raises(RightsError, match=code):
        RightsPolicy(record().model_copy(update=patch))


def test_policy_revision_and_exact_expiry_boundary():
    first = record()
    second = first.model_copy(update={"reference": first.reference.model_copy(update={"revision": 2}),
                                      "supersedes": first.reference})
    RightsPolicy(second)
    for broken in (second.model_copy(update={"supersedes": None}),
                   first.model_copy(update={"supersedes": first.reference}),
                   second.model_copy(update={"supersedes": first.reference.model_copy(update={"rights_id": "other"})})):
        with pytest.raises(RightsError, match="rights_invalid_predecessor"):
            RightsPolicy(broken)
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    policy = RightsPolicy(first.model_copy(update={"expires_at": instant}))
    policy.require("read", instant - timedelta(microseconds=1))
    with pytest.raises(RightsError, match="rights_expired"):
        policy.require("read", instant)
