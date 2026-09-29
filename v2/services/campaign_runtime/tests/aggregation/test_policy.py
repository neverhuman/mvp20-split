"""Declared policy goldens, independent of scheduler and transport order."""

import hashlib
import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.aggregation import JoinAccumulator, SnapshotCut
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_campaigns import PartialCollectionPolicy
from pydantic import ValidationError

from .test_snapshot import identity, member


def close(policy, members=(), trigger="all_terminal"):
    return JoinAccumulator(policy).close(SnapshotCut(identity(), 5, 6, trigger, members))


def partial(minimum=1, deadline=False):
    return {"kind": "partial", "minimum": minimum, "close": "deadline" if deadline else "all_terminal",
            "deadline_seconds": 10 if deadline else None}


def test_partial_preserves_declared_slots_and_typed_missing_reasons():
    decision = close(partial(), (member("last"), member("first", "abstained"), member("middle", "failed")))
    assert decision.status == "succeeded" and decision.reason_code is None
    assert decision.collection.model_dump(mode="json") == {"kind": "collection", "items": [
        {"kind": "number", "value": "2.5", "unit": "1"},
        {"kind": "missing", "member_id": "first", "reason_code": "member_abstained"},
        {"kind": "missing", "member_id": "middle", "reason_code": "member_failed"}]}
    assert decision.record()["eligible_members"] == ["last"]


@pytest.mark.parametrize("status", ["failed", "abstained", "cancelled", "blocked", "skipped"])
def test_all_required_unavailable_blocks_without_exposing_partial_output(status):
    decision = close({"kind": "all", "skipped": "fail"}, (member(), member("bad", status)))
    assert decision.status == "blocked" and decision.reason_code == "graph_required_member_unavailable"
    assert decision.collection is None
    assert decision.record()["eligible_members"] == ["second"]


@pytest.mark.parametrize("status", ["failed", "abstained", "cancelled", "blocked", "skipped"])
def test_all_optional_unavailable_preserves_original_reason(status):
    missing = replace(member("optional", status), required=False, reason_code="source_specific_reason")
    decision = close({"kind": "all", "skipped": "fail"}, (member(), missing))
    assert decision.status == "succeeded"
    assert decision.collection.items[1].reason_code == "source_specific_reason"


def test_skip_exclusion_is_explicit_and_keeps_evidence():
    decision = close({"kind": "all"}, (member("unused", "skipped"), member("selected")))
    assert len(decision.collection.items) == 1
    assert decision.cut.members[0].status == "skipped"
    assert decision.record()["eligible_members"] == ["selected"]


@pytest.mark.parametrize("minimum,status", [(0, "succeeded"), (1, "succeeded"), (2, "blocked")])
def test_partial_minimum_counts_only_accepted_successes(minimum, status):
    decision = close(partial(minimum), (member(), member("missing", "skipped")))
    assert decision.status == status
    assert decision.reason_code == ("aggregate_minimum_unmet" if status == "blocked" else None)
    assert (decision.collection is None) == (status == "blocked")


def test_minimum_is_not_a_first_arrival_closure():
    with pytest.raises(TransitionError, match="aggregate_pending_member"):
        close(partial(), (member(), member("late", "pending")))
    decision = close(partial(deadline=True), (member(), member("late", "pending")), "deadline")
    assert decision.collection.items[1].reason_code == "member_pending"


@pytest.mark.parametrize("policy", [{"kind": "all"}, partial()])
def test_deadline_cut_requires_declared_deadline(policy):
    with pytest.raises(TransitionError, match="aggregate_deadline_not_declared"):
        close(policy, (), "deadline")


def test_deadline_policy_can_close_early_only_when_every_member_is_terminal():
    assert close(partial(deadline=True), (member(),)).status == "succeeded"


@pytest.mark.parametrize("policy", [{"kind": "all"}, partial(0), partial(1)])
def test_empty_membership_does_not_invent_successes(policy):
    decision = close(policy)
    assert decision.record()["eligible_members"] == []
    assert decision.status == ("blocked" if policy.get("minimum") == 1 else "succeeded")


@pytest.mark.parametrize("policy", [dict(partial(), deadline_seconds=10), dict(partial(deadline=True), deadline_seconds=None)])
def test_incoherent_deadline_policy_rejected(policy):
    with pytest.raises(TransitionError, match="aggregate_deadline_policy"):
        JoinAccumulator(policy)


def test_policy_revalidates_raw_constructed_values():
    with pytest.raises(ValidationError):
        JoinAccumulator(PartialCollectionPolicy.model_construct(**partial(True)))


def test_decision_digest_and_consumer_mutation():
    decision = close(partial(0), (member("missing", "abstained"),))
    expected = {"profile": "amphora-aggregate-decision-v1", "cut_sha256": decision.cut.sha256,
                "policy": partial(0), "status": "succeeded", "reason_code": None, "eligible_members": [],
                "collection": {"kind": "collection", "items": [
                    {"kind": "missing", "member_id": "missing", "reason_code": "member_abstained"}]}}
    assert decision.record() == expected
    digest = hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert decision.sha256 == digest
    mutated = decision.record()
    mutated["policy"]["minimum"] = 100
    mutated["collection"]["items"].clear()
    assert decision.sha256 == digest
