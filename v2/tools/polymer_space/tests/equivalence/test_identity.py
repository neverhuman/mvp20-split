import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_candidate_spaces import PolymerDesign
from amphora_polymer_space import (
    EQUIVALENCE,
    PROFILE,
    PolymerCanonical,
    PolymerDesignError,
)


def data():
    record = json.loads(
        (Path(__file__).parents[1] / "legality/request.json").read_bytes()
    )["source"]
    record["profile"] = PROFILE.model_dump(mode="json")
    return record


def identity(record):
    return PolymerCanonical(PolymerDesign.model_validate_json(json.dumps(record)))


@pytest.mark.parametrize("known", [False, True])
def test_declaration_permutation_and_bond_orientation_share_declared_identity(known):
    source = data()
    if known:
        source["composition"] = [
            {"unit_id": "A", "fraction": 0.5},
            {"unit_id": "B", "fraction": 0.5},
        ]
        source["metadata"]["end_groups"] = [
            {"site_id": "s0", "label": "left"},
            {"site_id": "s1", "label": "right"},
        ]
    shuffled = copy.deepcopy(source)
    shuffled["repeat_units"].reverse()
    shuffled["sites"].reverse()
    shuffled["bonds"] = [{"left": "s1", "right": "s0"}]
    if known:
        shuffled["composition"].reverse()
        shuffled["metadata"]["end_groups"].reverse()
    first, second = identity(source), identity(shuffled)
    expected = json.dumps(
        source, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    assert first.bytes == second.bytes == expected
    assert first.sha256 == second.sha256 == hashlib.sha256(expected).hexdigest()
    assert first.policy == EQUIVALENCE and first.policy != PROFILE
    assert shuffled["sites"][0]["site_id"] == "s1", (
        "Canonicalization must not mutate the source"
    )


@pytest.mark.parametrize(
    "change",
    [
        "tacticity",
        "distribution",
        "sequence",
        "degree",
        "ends",
        "branching",
        "bigsmiles",
        "scope",
        "label",
        "composition",
    ],
)
def test_unknown_and_specified_descriptors_never_collapse(change):
    source = data()
    first = identity(source).sha256
    if change == "tacticity":
        source["metadata"]["tacticity"] = "atactic"
    elif change == "distribution":
        source["metadata"]["distribution"] = {
            "number_average_dp": None,
            "weight_average_dp": None,
            "dispersity": None,
        }
    elif change == "sequence":
        source["metadata"]["sequence_arrangement"] = "random"
    elif change == "degree":
        source["metadata"]["degree_of_polymerization"] = 20
    elif change == "ends":
        source["metadata"]["end_groups"] = []
    elif change == "branching":
        source["metadata"]["branching"] = "linear"
    elif change == "bigsmiles":
        source["metadata"]["bigsmiles"] = "opaque"
    elif change == "scope":
        source["scope"]["project_id"] = "other"
    elif change == "label":
        source["repeat_units"][0]["label"] = "different-toy-unit"
    else:
        source["composition"] = [
            {"unit_id": "A", "fraction": 0.5},
            {"unit_id": "B", "fraction": 0.5},
        ]
    assert identity(source).sha256 != first


def test_site_renaming_is_not_claimed_graph_isomorphism():
    source = data()
    first = identity(source).sha256
    source["sites"][0]["site_id"] = "renamed"
    source["bonds"][0]["left"] = "renamed"
    assert identity(source).sha256 != first


def test_canonicalization_cannot_repair_illegal_connectivity():
    source = data()
    source["bonds"] = []
    with pytest.raises(PolymerDesignError, match="not_tree"):
        identity(source)
