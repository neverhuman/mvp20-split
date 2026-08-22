from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from nomad_crystal360.constants import FAMILY_COUNTS, PAIR_TYPES
from nomad_crystal360.featurizer import Crystal360Featurizer
from nomad_crystal360.schema import build_primary_definitions, build_reserve_definitions


def test_primary_schema_has_exact_requested_family_counts() -> None:
    definitions = build_primary_definitions()
    assert len(definitions) == 360
    assert len({item.name for item in definitions}) == 360
    assert Counter(item.family for item in definitions) == FAMILY_COUNTS
    assert all(
        item.formula and item.unit and item.neighbors and item.interpretation
        for item in definitions
    )
    assert all(item.family == item.physical_family for item in definitions)
    assert all(not item.reserve for item in definitions)


def test_reserve_bank_order_and_deterministic_constant_replacement() -> None:
    featurizer = Crystal360Featurizer()
    rng = np.random.default_rng(7)
    candidates = pd.DataFrame(
        {column: rng.normal(size=12) for column in featurizer.candidate_columns}
    )
    first_primary = build_primary_definitions()[0].name
    first_reserve = build_reserve_definitions()[0].name
    candidates[first_primary] = 1.0
    baseline = pd.DataFrame({f"baseline_{index}": rng.normal(size=12) for index in range(449)})
    boundaries = {f"{left}-{right}": list(np.linspace(0.0, 8.0, 9)) for left, right in PAIR_TYPES}

    schema = featurizer.select_schema(candidates, baseline, boundaries, {"test": True})

    assert len(schema.columns) == 360
    assert first_primary not in schema.columns
    assert schema.columns[0] == first_reserve
    assert Counter(item.family for item in schema.selected_features) == FAMILY_COUNTS
    assert schema.selected_features[0].physical_family == "pbc_pair_distance_profiles"
    assert schema.replacements == [
        {
            "replaced": first_primary,
            "replacement": first_reserve,
            "reason": "constant_or_all_missing",
        }
    ]
