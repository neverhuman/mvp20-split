from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping

import numpy as np
import pandas as pd
from pandas import DataFrame

if TYPE_CHECKING:
    from pymatgen.core import Structure
else:
    try:
        from pymatgen.core import Structure
    except ImportError:  # Pure controller-contract tests do not require scientific extras.
        Structure = Any

from .novelty import numeric_signature


REQUIRED_INVARIANCES = (
    "translation",
    "rotation",
    "atom_permutation",
    "periodic_wrapping",
    "equivalent_cell",
)


@dataclass(frozen=True)
class ColumnRejection:
    column: str
    reason: str
    duplicate_of: str | None = None


@dataclass(frozen=True)
class QuarantineResult:
    train: DataFrame
    test: DataFrame
    accepted: tuple[str, ...]
    rejected: tuple[ColumnRejection, ...]
    signatures: dict[str, str]


class MatrixContractError(ValueError):
    pass


def _check_matrix_contract(
    train: DataFrame,
    test: DataFrame,
    rerun_train: DataFrame,
    rerun_test: DataFrame,
    expected_train_ids: Iterable[Any],
    expected_test_ids: Iterable[Any],
) -> list[str]:
    if "id" not in train or "id" not in test or "id" not in rerun_train or "id" not in rerun_test:
        raise MatrixContractError("all matrices must carry the controller-owned id column")
    if list(train.columns) != list(test.columns):
        raise MatrixContractError("train and test columns are not identical and ordered")
    if len(set(train.columns)) != len(train.columns):
        raise MatrixContractError("matrix columns contain duplicate IDs")
    if list(train.columns) != list(rerun_train.columns) or list(test.columns) != list(rerun_test.columns):
        raise MatrixContractError("rerun columns are not identical and ordered")
    if train["id"].tolist() != list(expected_train_ids):
        raise MatrixContractError("train row alignment differs from the frozen row IDs")
    if test["id"].tolist() != list(expected_test_ids):
        raise MatrixContractError("test row alignment differs from the frozen row IDs")
    if train["id"].duplicated().any() or test["id"].duplicated().any():
        raise MatrixContractError("row IDs must be unique within each split")
    if rerun_train["id"].tolist() != train["id"].tolist():
        raise MatrixContractError("rerun train row alignment differs")
    if rerun_test["id"].tolist() != test["id"].tolist():
        raise MatrixContractError("rerun test row alignment differs")
    return [column for column in train.columns if column != "id"]


def _invariance_passed(report: Mapping[str, Any], column: str) -> bool:
    for invariant in REQUIRED_INVARIANCES:
        value = report.get(invariant)
        if isinstance(value, Mapping):
            value = value.get(column)
        if value is not True:
            return False
    return True


def quarantine_columns(
    train: DataFrame,
    test: DataFrame,
    *,
    expected_train_ids: Iterable[Any],
    expected_test_ids: Iterable[Any],
    rerun_train: DataFrame,
    rerun_test: DataFrame,
    invariance_report: Mapping[str, Any],
    atlas_numeric_signatures: Mapping[str, str] | set[str] = frozenset(),
    earlier_v2_signatures: Mapping[str, str] | set[str] = frozenset(),
) -> QuarantineResult:
    """Validate each scalar independently after enforcing matrix-level alignment."""

    columns = _check_matrix_contract(
        train, test, rerun_train, rerun_test, expected_train_ids, expected_test_ids
    )
    atlas_lookup = (
        dict(atlas_numeric_signatures)
        if isinstance(atlas_numeric_signatures, Mapping)
        else {signature: "atlas" for signature in atlas_numeric_signatures}
    )
    prior_lookup = (
        dict(earlier_v2_signatures)
        if isinstance(earlier_v2_signatures, Mapping)
        else {signature: "earlier-v2" for signature in earlier_v2_signatures}
    )
    accepted: list[str] = []
    rejected: list[ColumnRejection] = []
    signatures: dict[str, str] = {}
    seen = {**atlas_lookup, **prior_lookup}
    for column in columns:
        train_values = pd.to_numeric(train[column], errors="coerce").to_numpy(dtype=float)
        test_values = pd.to_numeric(test[column], errors="coerce").to_numpy(dtype=float)
        rerun_train_values = pd.to_numeric(rerun_train[column], errors="coerce").to_numpy(dtype=float)
        rerun_test_values = pd.to_numeric(rerun_test[column], errors="coerce").to_numpy(dtype=float)
        values = np.concatenate((train_values, test_values))
        if not np.isfinite(values).all():
            rejected.append(ColumnRejection(column, "nonfinite_or_undeclared_missingness"))
            continue
        if np.unique(values).size <= 1:
            rejected.append(ColumnRejection(column, "constant"))
            continue
        if not np.array_equal(train_values, rerun_train_values) or not np.array_equal(
            test_values, rerun_test_values
        ):
            rejected.append(ColumnRejection(column, "nondeterministic_rerun"))
            continue
        if not _invariance_passed(invariance_report, column):
            rejected.append(ColumnRejection(column, "invariance_failure"))
            continue
        signature = numeric_signature(values)
        if signature in seen:
            rejected.append(ColumnRejection(column, "exact_numeric_duplicate", seen[signature]))
            continue
        accepted.append(column)
        signatures[column] = signature
        seen[signature] = column
    return QuarantineResult(
        train=train[["id", *accepted]].copy(),
        test=test[["id", *accepted]].copy(),
        accepted=tuple(accepted),
        rejected=tuple(rejected),
        signatures=signatures,
    )


def invariant_structures(structure: Structure) -> dict[str, Structure]:
    frac = np.asarray(structure.frac_coords, dtype=float)
    rotation = np.asarray(
        [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]], dtype=float
    )
    translated = Structure(
        structure.lattice,
        structure.species,
        np.asarray(structure.cart_coords) + np.asarray([1.234, -0.456, 2.345]),
        coords_are_cartesian=True,
    )
    rotated = Structure(
        np.asarray(structure.lattice.matrix) @ rotation.T,
        structure.species,
        frac,
    )
    permutation = list(range(len(structure) - 1, -1, -1))
    permuted = Structure(
        structure.lattice,
        [structure.species[index] for index in permutation],
        frac[permutation],
    )
    offsets = np.arange(len(structure))[:, None] * np.asarray([[1.0, -1.0, 2.0]])
    wrapped = Structure(structure.lattice, structure.species, frac + offsets)
    equivalent = structure.copy()
    equivalent.make_supercell([2, 1, 1])
    return {
        "translation": translated,
        "rotation": rotated,
        "atom_permutation": permuted,
        "periodic_wrapping": wrapped,
        "equivalent_cell": equivalent,
    }


def run_invariance_tests(
    structures: Iterable[Structure],
    compute: Callable[[Structure], dict[str, float]],
    *,
    rtol: float = 1e-7,
    atol: float = 1e-9,
) -> dict[str, dict[str, bool]]:
    structures = list(structures)
    if not structures:
        raise ValueError("at least one structure is required")
    report: dict[str, dict[str, bool]] = {name: {} for name in REQUIRED_INVARIANCES}
    for structure in structures:
        baseline = compute(structure)
        for invariant, transformed in invariant_structures(structure).items():
            candidate = compute(transformed)
            for column in set(baseline) | set(candidate):
                passed = column in baseline and column in candidate and np.isclose(
                    baseline.get(column, np.nan), candidate.get(column, np.nan), rtol=rtol, atol=atol
                )
                report[invariant][column] = report[invariant].get(column, True) and bool(passed)
    return report


def deterministic_real_sample(ids: Iterable[Any], count: int, *, seed: int = 4219) -> list[Any]:
    values = list(ids)
    if count > len(values):
        raise ValueError("sample count exceeds the available real structures")
    generator = np.random.default_rng(seed)
    positions = np.sort(generator.choice(len(values), size=count, replace=False))
    return [values[int(position)] for position in positions]
