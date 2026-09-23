from __future__ import annotations

import math

import numpy as np
import pytest
from pymatgen.core import Lattice, Structure

from nomad_crystal360.constants import PAIR_TYPES
from nomad_crystal360.featurizer import (
    Crystal360Featurizer,
    _angle_degrees,
    _lattice_features,
    _pair_distances_from_neighbor_data,
    _periodic_neighbor_data,
    _voronoi_counts,
)


def linear_boundaries() -> dict[str, list[float]]:
    return {f"{left}-{right}": list(np.linspace(0.0, 8.0, 9)) for left, right in PAIR_TYPES}


def test_skew_cell_uses_exact_periodic_image_not_fractional_rounding() -> None:
    lattice = Lattice([[2.0, 0.0, 0.0], [1.8, 2.0, 0.0], [0.0, 0.0, 5.0]])
    structure = Structure(lattice, ["Al", "O"], [[0.0, 0.0, 0.0], [0.51, 0.51, 0.0]])
    distances = _pair_distances_from_neighbor_data(_periodic_neighbor_data(structure))["Al-O"]
    exact, _ = lattice.get_distance_and_image(structure[0].frac_coords, structure[1].frac_coords)
    rounded_delta = (
        structure[1].frac_coords
        - structure[0].frac_coords
        - np.round(structure[1].frac_coords - structure[0].frac_coords)
    )
    rounded_distance = np.linalg.norm(lattice.get_cartesian_coords(rounded_delta))

    assert float(distances.min()) == pytest.approx(exact)
    assert exact < rounded_distance - 0.5


def test_toy_coordination_angle_and_reciprocal_quantities() -> None:
    cubic = Structure(Lattice.cubic(4.0), ["Al"], [[0.0, 0.0, 0.0]])
    voronoi = _voronoi_counts(cubic)
    lattice = _lattice_features(cubic)

    assert voronoi["Al"]["Al"] == [6.0]
    assert _angle_degrees(np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])) == pytest.approx(
        90.0
    )
    assert lattice["c360_lattice_face_area_min"] == pytest.approx(16.0)
    assert lattice["c360_lattice_surface_area"] == pytest.approx(96.0)
    assert lattice["c360_lattice_height_min"] == pytest.approx(4.0)
    assert lattice["c360_lattice_reciprocal_length_min"] == pytest.approx(0.25)
    assert lattice["c360_lattice_reciprocal_volume"] == pytest.approx(1.0 / 64.0)
    assert lattice["c360_lattice_metric_eigenvalue_min"] == pytest.approx(1.0)
    assert lattice["c360_lattice_d_spacing_1_normalized"] == pytest.approx(1.0)


def test_absent_element_pair_is_nan_and_rdf_matches_shell_normalization() -> None:
    structure = Structure(
        Lattice.cubic(4.0),
        ["Al", "O"],
        [[0.0, 0.0, 0.0], [0.25, 0.0, 0.0]],
    )
    featurizer = Crystal360Featurizer()
    candidates, _ = featurizer.transform_candidates([structure], [1], linear_boundaries())
    row = candidates.iloc[0]
    assert math.isnan(row["c360_pair_Al_In_min"])
    assert math.isnan(row["c360_rdf_Al_In_shell_1"])
    assert math.isnan(row["c360_env_Al_to_In_nn_distance_mean"])

    distances = _pair_distances_from_neighbor_data(_periodic_neighbor_data(structure))["Al-O"]
    count = int(np.sum((distances >= 1.0) & (distances < 2.0)))
    shell_volume = 4.0 * math.pi / 3.0 * (2.0**3 - 1.0**3)
    expected = count / (1.0 * (1.0 / structure.volume) * shell_volume)
    assert row["c360_rdf_Al_O_shell_2"] == pytest.approx(expected)
