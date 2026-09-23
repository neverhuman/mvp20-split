from __future__ import annotations

import numpy as np
from pymatgen.core import Lattice, Structure

from nomad_crystal360.constants import PAIR_TYPES
from nomad_crystal360.featurizer import Crystal360Featurizer


def _toy_structure() -> Structure:
    return Structure(
        Lattice.from_parameters(5.2, 5.8, 6.3, 82.0, 96.0, 73.0),
        ["Al", "Ga", "In", "O", "O", "O", "O", "O", "O"],
        [
            [0.08, 0.11, 0.17],
            [0.47, 0.39, 0.28],
            [0.79, 0.71, 0.63],
            [0.18, 0.31, 0.42],
            [0.64, 0.19, 0.51],
            [0.35, 0.78, 0.12],
            [0.91, 0.45, 0.83],
            [0.52, 0.63, 0.74],
            [0.24, 0.88, 0.59],
        ],
    )


def _boundaries() -> dict[str, list[float]]:
    return {f"{left}-{right}": list(np.linspace(0.0, 8.0, 9)) for left, right in PAIR_TYPES}


def _variants(structure: Structure) -> list[Structure]:
    translated = Structure(
        structure.lattice,
        structure.species,
        (structure.frac_coords + np.array([0.23, -0.31, 0.44])) % 1.0,
    )
    order = np.arange(len(structure))[::-1]
    permuted = Structure(
        structure.lattice,
        [structure.species[index] for index in order],
        structure.frac_coords[order],
    )
    wrapped = Structure(
        structure.lattice,
        structure.species,
        structure.frac_coords + np.array([2.0, -3.0, 1.0]),
        to_unit_cell=True,
    )
    angle = np.deg2rad(37.0)
    rotation = np.array(
        [[np.cos(angle), -np.sin(angle), 0.0], [np.sin(angle), np.cos(angle), 0.0], [0.0, 0.0, 1.0]]
    )
    rotated = Structure(
        Lattice(structure.lattice.matrix @ rotation.T),
        structure.species,
        structure.frac_coords,
    )
    transform = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], dtype=int)
    transformed = Structure(
        Lattice(transform @ structure.lattice.matrix),
        structure.species,
        (structure.frac_coords @ np.linalg.inv(transform)) % 1.0,
    )
    return [translated, permuted, wrapped, rotated, transformed]


def test_translation_permutation_wrapping_rotation_and_cell_equivalence() -> None:
    original = _toy_structure()
    structures = [original, *_variants(original)]
    featurizer = Crystal360Featurizer(n_jobs=1)
    candidates, _ = featurizer.transform_candidates(
        structures, [1] * len(structures), _boundaries()
    )
    reference = candidates.iloc[0].to_numpy(dtype=float)
    for row in range(1, len(candidates)):
        np.testing.assert_allclose(
            candidates.iloc[row].to_numpy(dtype=float),
            reference,
            rtol=2e-6,
            atol=2e-6,
            equal_nan=True,
        )
