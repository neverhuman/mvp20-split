"""Independent order, cut, missingness and isolation oracles."""

import hashlib
import json
from dataclasses import FrozenInstanceError, replace

import pytest
from amphora_campaign_runtime.aggregation import AggregateIdentity, MemberSnapshot, SnapshotCut
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_campaigns import IntegerConstant
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import GraphBinding, NumberValue
from pydantic import ValidationError


def identity():
    return AggregateIdentity(Scope(tenant_id="test", project_id="aggregate"), "run-1", "a" * 64)


def member(name="second", status="succeeded", revision=4):
    return MemberSnapshot(name, True, status, revision,
        NumberValue(kind="number", value="2.5") if status == "succeeded" else None,
        None if status == "succeeded" else "member_" + status)


def test_manual_record_digest_and_declared_order():
    owner = identity()
    cut = SnapshotCut(owner, 5, 6, "all_terminal", (member(), member("first", "abstained")))
    identity_record = {"profile": "amphora-aggregate-identity-v1",
                       "scope": {"tenant_id": "test", "project_id": "aggregate"},
                       "run_id": "run-1", "activation_id": "a" * 64}
    def encode(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    expected_id = hashlib.sha256(encode(identity_record)).hexdigest()
    expected = {"profile": "amphora-aggregate-cut-v1", "aggregate_id": expected_id,
                "scope": identity_record["scope"], "run_id": "run-1", "activation_id": "a" * 64,
                "observed_revision": 5, "closure_revision": 6, "trigger": "all_terminal", "members": [
                    {"member_id": "second", "required": True, "status": "succeeded", "observed_revision": 4,
                     "reason_code": None, "value": {"kind": "number", "value": "2.5", "unit": "1"}},
                    {"member_id": "first", "required": True, "status": "abstained", "observed_revision": 4,
                     "reason_code": "member_abstained", "value": None}]}
    assert cut.record() == expected
    assert cut.sha256 == hashlib.sha256(encode(expected)).hexdigest()
    reversed_cut = replace(cut, members=tuple(reversed(cut.members)))
    assert reversed_cut.identity.key == cut.identity.key and reversed_cut.sha256 != cut.sha256


def test_closed_cut_does_not_change_with_late_result_or_consumer_mutation():
    observations = [member("late", "pending")]
    cut = SnapshotCut(identity(), 5, 6, "deadline", observations)
    before = cut.sha256
    observations[0] = member("late")
    record = cut.record()
    record["members"][0]["status"] = "succeeded"
    assert cut.members[0].status == "pending" and cut.sha256 == before
    with pytest.raises(FrozenInstanceError):
        cut.trigger = "all_terminal"


@pytest.mark.parametrize("status", ["failed", "abstained", "skipped", "cancelled", "blocked"])
def test_unavailable_outcomes_keep_distinct_reasons(status):
    cut = SnapshotCut(identity(), 5, 6, "all_terminal", (member(status=status),))
    assert cut.record()["members"][0]["reason_code"] == "member_" + status


@pytest.mark.parametrize("changes,reason", [
    ({"members": (member(), member())}, "aggregate_duplicate_member"),
    ({"members": (member(revision=6),)}, "aggregate_future_member"),
    ({"members": (member(status="pending"),)}, "aggregate_pending_member"),
    ({"trigger": "first_arrival"}, "aggregate_cut_trigger"),
    ({"closure_revision": 5}, "aggregate_cut_revision"),
    ({"observed_revision": True}, "aggregate_cut_revision"),
    ({"closure_revision": 9007199254740992}, "aggregate_cut_revision"),
    ({"members": (member(),) * 10001}, "aggregate_member_bound"),
])
def test_invalid_cuts_rejected(changes, reason):
    with pytest.raises(TransitionError, match=reason):
        replace(SnapshotCut(identity(), 5, 6, "all_terminal", (member(),)), **changes)


@pytest.mark.parametrize("changes,reason", [
    ({"status": "reported"}, "aggregate_member_status"),
    ({"observed_revision": -1}, "aggregate_member_revision"),
    ({"observed_revision": True}, "aggregate_member_revision"),
    ({"required": 1}, "aggregate_member_required"),
    ({"value": None}, "aggregate_success_evidence"),
    ({"reason_code": "failed"}, "aggregate_success_evidence"),
    ({"status": "failed"}, "aggregate_missing_evidence"),
])
def test_invalid_member_evidence_rejected(changes, reason):
    with pytest.raises(TransitionError, match=reason):
        replace(member(), **changes)


def test_values_revalidated_and_nested_collections_rejected():
    with pytest.raises(ValidationError):
        replace(member(), value=NumberValue.model_construct(kind="number", value="NaN", unit="1"))
    with pytest.raises(ValidationError):
        replace(member(), value=IntegerConstant.model_construct(kind="integer", value=True))
    collection = GraphBinding.model_validate_json('{"port":"x","value":{"kind":"collection","items":[]}}').value
    with pytest.raises(TransitionError, match="aggregate_nested_collection"):
        replace(member(), value=collection)


def test_foreign_artifact_rejected_and_same_scope_retained():
    value = GraphBinding.model_validate_json(json.dumps({"port": "x", "value": {
        "kind": "artifact", "artifact": {"artifact_id": "a1", "scope": identity().scope.model_dump(),
        "sha256": "b" * 64, "media_type": "application/json", "size_bytes": 2,
        "schema_ref": {"schema_id": "fixture", "version": "1", "sha256": "c" * 64}},
        "representation": "synthetic", "unit": "1"}})).value
    cut = SnapshotCut(identity(), 5, 6, "all_terminal", (replace(member(), value=value),))
    assert cut.members[0].value == value
    with pytest.raises(TransitionError, match="aggregate_foreign_artifact"):
        replace(cut, identity=replace(identity(), scope=Scope(tenant_id="other", project_id="aggregate")))


def test_empty_cut_and_identity_boundaries():
    cut = SnapshotCut(identity(), 0, 1, "all_terminal", ())
    assert cut.record()["members"] == []
    assert replace(identity(), run_id="run-2").key != identity().key
    for changes in ({"run_id": "bad id"}, {"activation_id": "not-a-digest"}):
        with pytest.raises(ValidationError):
            replace(identity(), **changes)
