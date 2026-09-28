"""Exact pins, independent science and bounded inventory policy."""

import copy

import pytest

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("fault,reason", [("unit", "unit_incompatible"), ("representation", "representation_incompatible"),
    ("schema", "schema_incompatible"), ("science", "synthetic_profile_only"), ("lock", "release_lock_mismatch")])
def test_healthy_capacity_never_overrides_exact_contract_or_scientific_need(installed, fault, reason):
    case = installed
    assert case.heartbeat().status == "accepted"
    need = copy.deepcopy(case.need)
    if fault == "science":
        need["context"] = "biology"
    elif fault == "lock":
        need["release"]["tool"]["image_sha256"] = "e"*64
    elif fault == "schema":
        need["inputs"][0]["schema_ref"]["sha256"] = "e"*64
    else:
        need["inputs"][0][fault] = "different"
    result = case.env.execute("resolve", need)
    assert result.status == "rejected"
    if fault == "lock":
        assert result.reason_code == reason and result.decision is None
    else:
        assert result.decision.observations.capacity.status == "available"
        reasons = result.decision.observations.scientific.reason_codes if fault == "science" else result.decision.admission.reason_codes
        assert reason in reasons


def test_same_capability_versions_never_borrow_each_others_capacity(installed):
    case = installed
    assert case.heartbeat().status == "accepted"
    raw = copy.deepcopy(case.env.fixture["descriptor"])
    raw["tool"]["binding"]["release"] = "0.2.0"
    _, newer = case.register(raw)
    assert case.env.execute("activate", {"release": newer, "expected_revision": 1}).status == "accepted"
    result = case.env.execute("resolve", {**case.need, "release": newer})
    assert result.status == "rejected" and result.decision.observations.capacity.status == "unavailable"
    assert case.env.execute("resolve", case.need).decision.status == "candidate"


def test_bounded_replica_inventory_does_not_count_forged_extra_capacity(installed):
    case = installed
    for index in range(64):
        assert case.heartbeat(replica_id=f"r{index}").status == "accepted"
    assert case.heartbeat(replica_id="overflow").reason_code == "replica_limit"
    assert case.heartbeat(replica_id="r0", expected_revision=1).status == "accepted"


@pytest.mark.parametrize("fault,reason", [("unit", "descriptor_invalid"), ("release", "release_identity_too_long")])
def test_bad_registration_is_rejected_before_owner_insertion(installed, fault, reason):
    raw = copy.deepcopy(installed.env.fixture["descriptor"])
    raw["tool"]["binding"]["release"] = "0.2.0"
    if fault == "unit":
        raw["tool"]["inputs"][0]["unit"] = " "
    else:
        raw["tool"]["binding"]["release"] = "1"*130+".0.0"
    result, _ = installed.register(raw)
    assert result.reason_code == reason
