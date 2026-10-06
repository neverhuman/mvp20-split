import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_candidate_spaces import PolymerDesign, PolymerMoveRequest
from amphora_polymer_space import (
    OPERATOR,
    PROFILE,
    PolymerDesignError,
    PolymerSpace,
    canonical,
)


def payload():
    data = json.loads(Path(__file__).with_name("request.json").read_bytes())
    data["source"]["profile"] = PROFILE.model_dump(mode="json")
    data["operator"] = OPERATOR.model_dump(mode="json")
    return data


def space(data):
    return PolymerSpace(PolymerDesign.model_validate_json(json.dumps(data)))


def test_unknown_metadata_stays_unknown_and_attempt_is_attributed():
    request = PolymerMoveRequest.model_validate_json(json.dumps(payload()))
    result = PolymerSpace(request.source).apply(request)
    assert [site.unit_id for site in result.result.sites] == ["A", "A"]
    assert all(value is None for value in result.result.metadata.model_dump().values())
    assert result.result.composition is None and request.source.sites[1].unit_id == "B"
    assert result.source_sha256 == hashlib.sha256(canonical(request.source)).hexdigest()


def test_known_composition_updates_and_descriptive_metadata_is_preserved():
    data = payload()
    data["source"]["composition"] = [
        {"unit_id": "A", "fraction": 0.5},
        {"unit_id": "B", "fraction": 0.5},
    ]
    data["source"]["metadata"].update(
        tacticity="atactic",
        sequence_arrangement="defined",
        branching="linear",
        end_groups=[{"site_id": "s0", "label": "cap"}],
        distribution={
            "number_average_dp": 10.0,
            "weight_average_dp": 20.0,
            "dispersity": 2.0,
        },
    )
    request = PolymerMoveRequest.model_validate_json(json.dumps(data))
    result = PolymerSpace(request.source).apply(request)
    assert [item.fraction for item in result.result.composition] == [1, 0]
    assert result.result.metadata == request.source.metadata


@pytest.mark.parametrize(
    "which,code",
    [
        ("duplicate-unit", "unit_declarations"),
        ("empty-label", "unit_declarations"),
        ("duplicate-site", "site_declarations"),
        ("unknown-unit", "site_declarations"),
        ("self-bond", "invalid_bond"),
        ("unknown-bond", "invalid_bond"),
        ("duplicate-bond", "duplicate_bond"),
        ("disconnected", "not_tree"),
        ("branching", "branching_mismatch"),
        ("end-missing", "end_groups"),
        ("end-duplicate", "end_groups"),
        ("end-empty", "end_groups"),
        ("composition-members", "composition_membership"),
        ("composition-value", "composition_mismatch"),
        ("distribution-order", "distribution_order"),
        ("distribution-ratio", "distribution_ratio"),
        ("alternating", "alternation_mismatch"),
        ("profile", "profile_mismatch"),
    ],
)
def test_domain_invalidity_rejects_without_repair(which, code):
    data = payload()["source"]
    if which == "duplicate-unit":
        data["repeat_units"].append(copy.deepcopy(data["repeat_units"][0]))
    elif which == "empty-label":
        data["repeat_units"][0]["label"] = " "
    elif which == "duplicate-site":
        data["sites"].append(copy.deepcopy(data["sites"][0]))
    elif which == "unknown-unit":
        data["sites"][0]["unit_id"] = "Z"
    elif which == "self-bond":
        data["bonds"][0]["right"] = "s0"
    elif which == "unknown-bond":
        data["bonds"][0]["right"] = "missing"
    elif which == "duplicate-bond":
        data["bonds"].append({"left": "s1", "right": "s0"})
    elif which == "disconnected":
        data["bonds"] = []
    elif which == "branching":
        data["metadata"]["branching"] = "branched"
    elif which == "end-missing":
        data["metadata"]["end_groups"] = [{"site_id": "missing", "label": "cap"}]
    elif which == "end-duplicate":
        data["metadata"]["end_groups"] = [{"site_id": "s0", "label": "cap"}] * 2
    elif which == "end-empty":
        data["metadata"]["end_groups"] = [{"site_id": "s0", "label": " "}]
    elif which == "composition-members":
        data["composition"] = [{"unit_id": "A", "fraction": 1.0}]
    elif which == "composition-value":
        data["composition"] = [
            {"unit_id": "A", "fraction": 1.0},
            {"unit_id": "B", "fraction": 0.0},
        ]
    elif which.startswith("distribution"):
        data["metadata"]["distribution"] = {
            "number_average_dp": 10.0,
            "weight_average_dp": 5.0 if which.endswith("order") else 20.0,
            "dispersity": 1.0,
        }
    elif which == "alternating":
        data["metadata"]["sequence_arrangement"] = "alternating"
        data["sites"][1]["unit_id"] = "A"
    else:
        data["profile"]["sha256"] = "f" * 64
    with pytest.raises(PolymerDesignError, match=code):
        space(data)


@pytest.mark.parametrize(
    "which", ["source", "operator", "site", "unit", "bigsmiles", "alternating"]
)
def test_proposed_move_must_preserve_source_constraints(which):
    data = payload()
    if which == "bigsmiles":
        data["source"]["metadata"]["bigsmiles"] = "opaque-placeholder"
    if which == "alternating":
        data["source"]["metadata"]["sequence_arrangement"] = "alternating"
    original = space(data["source"])
    if which == "source":
        data["source"]["scope"]["project_id"] = "other"
    elif which == "operator":
        data["operator"]["sha256"] = "f" * 64
    elif which == "site":
        data["move"]["site_id"] = "missing"
    elif which == "unit":
        data["move"]["unit_id"] = "missing"
    with pytest.raises(PolymerDesignError):
        original.apply(PolymerMoveRequest.model_validate_json(json.dumps(data)))


def test_single_site_and_partial_distribution_are_explicit():
    data = payload()["source"]
    data["sites"] = data["sites"][:1]
    data["bonds"] = []
    data["metadata"]["distribution"] = {
        "number_average_dp": None,
        "weight_average_dp": 20.0,
        "dispersity": None,
    }
    assert space(data).record.metadata.distribution.number_average_dp is None


def test_branched_tree_and_noop_opaque_encoding():
    data = payload()
    data["source"]["sites"] += [
        {"site_id": "s2", "unit_id": "A"},
        {"site_id": "s3", "unit_id": "B"},
    ]
    data["source"]["bonds"] += [
        {"left": "s0", "right": "s2"},
        {"left": "s0", "right": "s3"},
    ]
    data["source"]["metadata"].update(
        branching="branched", bigsmiles="opaque-placeholder"
    )
    data["move"]["unit_id"] = "B"
    request = PolymerMoveRequest.model_validate_json(json.dumps(data))
    assert PolymerSpace(request.source).apply(request).result == request.source


def test_connected_cycle_is_not_a_tree():
    data = payload()["source"]
    data["sites"].append({"site_id": "s2", "unit_id": "A"})
    data["bonds"] += [{"left": "s1", "right": "s2"}, {"left": "s2", "right": "s0"}]
    with pytest.raises(PolymerDesignError, match="not_tree"):
        space(data)


def test_known_averages_do_not_invent_unknown_dispersity():
    data = payload()["source"]
    data["metadata"]["distribution"] = {
        "number_average_dp": 10.0, "weight_average_dp": 20.0, "dispersity": None,
    }
    assert space(data).record.metadata.distribution.dispersity is None
