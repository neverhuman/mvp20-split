"""Preserve the owner-approved future-campaign-only receipt correction boundary."""

import pytest
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.waits.disposition import WaitDisposition

from .test_identity import evidence, fixture


def test_notice_rejection_does_not_revoke_the_original_pinned_receipt():
    wait, original, _ = fixture()
    notice = original | {"receipt_id": "invalidation-notice", "outcome": {
        "status": "superseded", "replacement_revision": "revision-2", "reason_code": "corrected"}}
    with pytest.raises(TransitionError, match="wait_receipt_superseded"):
        WaitDisposition.received(wait, evidence(notice))
    # Shape validation has no issuer-currentness/invalidation input. This is not
    # a claim that a domain correction was persisted or a campaign committed.
    assert WaitDisposition.received(wait, evidence(original)).status == "accepted"
