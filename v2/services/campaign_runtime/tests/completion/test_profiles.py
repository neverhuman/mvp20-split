"""Run retention policy is immutable and explicit; no current-config inference."""

import pytest
from amphora_campaign_runtime.completion.profiles import KEY, RetentionProfile
from amphora_campaign_runtime.completion.closures import PROFILE
from amphora_campaign_runtime.lifecycle.model import TransitionError


def test_legacy_snapshot_preserves_default_and_profile_pin_is_additive():
    snapshot = {"tool:example": {"version": "1"}}
    assert RetentionProfile.from_snapshot(snapshot).name is None
    assert RetentionProfile().pin(snapshot) == snapshot
    pinned = RetentionProfile(PROFILE).pin(snapshot)
    assert RetentionProfile.from_snapshot(pinned).name == PROFILE
    assert KEY not in snapshot
    with pytest.raises(TransitionError, match="already_pinned"):
        RetentionProfile(PROFILE).pin(pinned)


@pytest.mark.parametrize("value", [None, True, {}, "unknown"])
def test_unknown_or_null_stored_profile_never_becomes_legacy(value):
    with pytest.raises(TransitionError, match="unsupported_artifact_retention_profile"):
        RetentionProfile.from_snapshot({KEY: value})
