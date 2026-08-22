from __future__ import annotations

import hashlib
import math
import warnings
from collections import Counter, defaultdict
from itertools import combinations
from dataclasses import replace
from typing import Any, Iterable

import numpy as np
import pandas as pd
import spglib
from joblib import Parallel, delayed
from pymatgen.analysis.bond_valence import calculate_bv_sum
from pymatgen.analysis.local_env import CrystalNN, VoronoiNN
from pymatgen.core import Structure
from scipy.spatial import ConvexHull, QhullError

from .constants import (
    ANGLE_STATS,
    BRIDGE_TYPES,
    CATIONS,
    COVALENT_RADII_ANGSTROM,
    CUTOFF_ANGSTROM,
    ELEMENTS,
    EPS,
    OXIDATION_STATES,
    PAIR_PROFILE_STATS,
    PAIR_TYPES,
    POLYHEDRON_STATS,
    SYMPRECS,
    WEIGHT_THRESHOLD,
)
from .schema import (
    Crystal360Schema,
    FeatureDefinition,
    build_primary_definitions,
    build_reserve_definitions,
)


def _symbol(site: Any) -> str:
    return str(site.specie.symbol)


def _mean_std(values: Iterable[float]) -> tuple[float, float]:
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return math.nan, math.nan
    return float(array.mean()), float(array.std(ddof=0))


def _distribution(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return {
            name: math.nan
            for name in ("mean", "std", "min", "max", "q10", "q25", "median", "q75", "q90")
        }
    quantiles = np.quantile(array, [0.10, 0.25, 0.50, 0.75, 0.90])
    return {
        "mean": float(array.mean()),
        "std": float(array.std(ddof=0)),
        "min": float(array.min()),
        "max": float(array.max()),
        "q10": float(quantiles[0]),
        "q25": float(quantiles[1]),
        "median": float(quantiles[2]),
        "q75": float(quantiles[3]),
        "q90": float(quantiles[4]),
    }


def _angle_degrees(first: np.ndarray, second: np.ndarray) -> float:
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    if denominator <= EPS:
        return math.nan
    cosine = float(np.dot(first, second) / denominator)
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def _array_signature(values: np.ndarray) -> str:
    array = np.asarray(values, dtype=np.float64).copy()
    missing = np.isnan(array)
    array[missing] = 0.0
    digest = hashlib.sha256()
    digest.update(missing.tobytes())
    digest.update(array.tobytes())
    return digest.hexdigest()


def _pair_key(left: str, right: str) -> str:
    return f"{left}-{right}"


def _periodic_neighbor_data(structure: Structure) -> dict[str, Any]:
    centers, points, offsets, distances = structure.get_neighbor_list(
        CUTOFF_ANGSTROM,
        numerical_tol=1e-8,
        exclude_self=True,
    )
    symbols = np.asarray([_symbol(site) for site in structure], dtype=object)
    return {
        "centers": np.asarray(centers, dtype=int),
        "points": np.asarray(points, dtype=int),
        "offsets": np.asarray(offsets, dtype=int),
        "distances": np.asarray(distances, dtype=float),
        "symbols": symbols,
    }


def _pair_distances_from_neighbor_data(data: dict[str, Any]) -> dict[str, np.ndarray]:
    symbols = data["symbols"]
    center_symbols = symbols[data["centers"]]
    point_symbols = symbols[data["points"]]
    result: dict[str, np.ndarray] = {}
    for source, target in PAIR_TYPES:
        mask = (center_symbols == source) & (point_symbols == target)
        result[_pair_key(source, target)] = np.asarray(data["distances"][mask], dtype=float)
    return result


def _fit_structure_pair_distances(structure: Structure) -> dict[str, np.ndarray]:
    return _pair_distances_from_neighbor_data(_periodic_neighbor_data(structure))


def _nearest_two_by_source(
    structure: Structure,
    neighbor_data: dict[str, Any],
    source: str,
    target: str,
) -> tuple[np.ndarray, np.ndarray]:
    symbols = neighbor_data["symbols"]
    source_indices = np.flatnonzero(symbols == source)
    target_indices = np.flatnonzero(symbols == target)
    if source_indices.size == 0 or target_indices.size == 0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)

    centers = neighbor_data["centers"]
    points = neighbor_data["points"]
    distances = neighbor_data["distances"]
    target_mask = symbols[points] == target
    first: list[float] = []
    second: list[float] = []
    for source_index in source_indices:
        local = np.sort(distances[(centers == source_index) & target_mask])
        if local.size < 2:
            radius = max(CUTOFF_ANGSTROM, min(structure.lattice.lengths))
            expanded: list[float] = []
            for _ in range(5):
                expanded = sorted(
                    float(neighbor.nn_distance)
                    for neighbor in structure.get_neighbors(structure[source_index], radius)
                    if _symbol(neighbor) == target and float(neighbor.nn_distance) > 1e-8
                )
                if len(expanded) >= 2:
                    break
                radius *= 2.0
            local = np.asarray(expanded, dtype=float)
        if local.size:
            first.append(float(local[0]))
        if local.size >= 2:
            second.append(float(local[1]))
    return np.asarray(first, dtype=float), np.asarray(second, dtype=float)


def _voronoi_counts(structure: Structure) -> dict[str, dict[str, list[float]]]:
    counts = {source: {target: [] for target in ELEMENTS} for source in ELEMENTS}
    voronoi = VoronoiNN(
        tol=0.0,
        cutoff=13.0,
        allow_pathological=True,
        weight="solid_angle",
        extra_nn_info=False,
        compute_adj_neighbors=False,
    )
    for index, site in enumerate(structure):
        source = _symbol(site)
        local = {target: 0.0 for target in ELEMENTS}
        try:
            neighbors = voronoi.get_nn_info(structure, index)
        except (RuntimeError, ValueError, QhullError):
            for target in ELEMENTS:
                counts[source][target].append(math.nan)
            continue
        for neighbor in neighbors:
            target = _symbol(neighbor["site"])
            if target in local and float(neighbor["weight"]) >= WEIGHT_THRESHOLD:
                local[target] += 1.0
        for target in ELEMENTS:
            counts[source][target].append(local[target])
    return counts


def _crystal_edges(structure: Structure) -> tuple[Structure, dict[int, list[dict[str, Any]]]]:
    oxidized = structure.copy()
    oxidized.add_oxidation_state_by_element(OXIDATION_STATES)
    crystal_nn = CrystalNN(
        weighted_cn=True,
        cation_anion=True,
        search_cutoff=CUTOFF_ANGSTROM,
    )
    edges: dict[int, list[dict[str, Any]]] = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for index, site in enumerate(oxidized):
            if _symbol(site) not in CATIONS:
                continue
            try:
                info = crystal_nn.get_nn_info(oxidized, index)
            except (RuntimeError, ValueError, QhullError):
                edges[index] = []
                continue
            edges[index] = [
                neighbor
                for neighbor in info
                if _symbol(neighbor["site"]) == "O"
                and float(neighbor["weight"]) >= WEIGHT_THRESHOLD
            ]
    return oxidized, edges


def _metal_and_angle_features(
    structure: Structure,
    voronoi: dict[str, dict[str, list[float]]],
) -> dict[str, float]:
    features: dict[str, float] = {}
    oxidized, edges = _crystal_edges(structure)
    metal_site_offsets = {metal: 0 for metal in CATIONS}
    reverse_edges: dict[int, list[tuple[str, np.ndarray]]] = defaultdict(list)
    angle_values: dict[str, list[float]] = {metal: [] for metal in CATIONS}
    angle_pair_counts: dict[str, list[float]] = {metal: [] for metal in CATIONS}

    per_metal: dict[str, dict[str, list[float]]] = {metal: defaultdict(list) for metal in CATIONS}
    all_lengths: dict[str, list[float]] = {metal: [] for metal in CATIONS}

    for index, site in enumerate(oxidized):
        metal = _symbol(site)
        if metal not in CATIONS:
            continue
        local_edges = edges.get(index, [])
        local_lengths: list[float] = []
        oxygen_coords: list[np.ndarray] = []
        weighted_cn = 0.0
        for edge in local_edges:
            neighbor_coords = np.asarray(edge["site"].coords, dtype=float)
            distance = float(np.linalg.norm(neighbor_coords - site.coords))
            local_lengths.append(distance)
            all_lengths[metal].append(distance)
            oxygen_coords.append(neighbor_coords)
            weighted_cn += float(edge["weight"])

            oxygen_index = int(edge["site_index"])
            image = np.asarray(edge["image"], dtype=float)
            cation_about_original_oxygen = (
                np.asarray(site.coords) - image @ structure.lattice.matrix
            )
            reverse_edges[oxygen_index].append((metal, cation_about_original_oxygen))

        per_metal[metal]["crystalnn_cn"].append(weighted_cn)
        voronoi_index = metal_site_offsets[metal]
        voronoi_values = voronoi[metal]["O"]
        per_metal[metal]["voronoi_cn"].append(
            voronoi_values[voronoi_index] if voronoi_index < len(voronoi_values) else math.nan
        )
        metal_site_offsets[metal] += 1

        if local_lengths:
            lengths = np.asarray(local_lengths, dtype=float)
            mean_length = float(lengths.mean())
            per_metal[metal]["distortion"].append(
                float(np.mean(np.abs(lengths - mean_length) / mean_length))
            )
            per_metal[metal]["quadratic_elongation"].append(
                float(np.mean((lengths / mean_length) ** 2))
            )
        else:
            per_metal[metal]["distortion"].append(math.nan)
            per_metal[metal]["quadratic_elongation"].append(math.nan)

        if (
            len(oxygen_coords) >= 4
            and np.linalg.matrix_rank(np.asarray(oxygen_coords) - np.mean(oxygen_coords, axis=0))
            == 3
        ):
            try:
                volume = float(ConvexHull(np.asarray(oxygen_coords)).volume)
            except QhullError:
                volume = 0.0
        else:
            volume = 0.0
        per_metal[metal]["hull_volume"].append(volume)

        neighbors_for_bv = oxidized.get_neighbors(site, 4.0)
        bvs = float(calculate_bv_sum(site, neighbors_for_bv))
        per_metal[metal]["bvs"].append(bvs)
        per_metal[metal]["valence_error"].append(abs(bvs - 3.0))

        angle_pair_counts[metal].append(float(len(oxygen_coords) * (len(oxygen_coords) - 1) // 2))
        for first, second in combinations(oxygen_coords, 2):
            angle_values[metal].append(
                _angle_degrees(np.asarray(first) - site.coords, np.asarray(second) - site.coords)
            )

    for metal in CATIONS:
        cn_mean, cn_std = _mean_std(per_metal[metal]["crystalnn_cn"])
        vor_mean, vor_std = _mean_std(per_metal[metal]["voronoi_cn"])
        lengths = np.asarray(all_lengths[metal], dtype=float)
        length_distribution = _distribution(lengths)
        distortion_mean, _ = _mean_std(per_metal[metal]["distortion"])
        elongation_mean, _ = _mean_std(per_metal[metal]["quadratic_elongation"])
        bvs_mean, _ = _mean_std(per_metal[metal]["bvs"])
        error_mean, _ = _mean_std(per_metal[metal]["valence_error"])
        errors = np.asarray(per_metal[metal]["valence_error"], dtype=float)
        errors = errors[np.isfinite(errors)]
        hull_mean, _ = _mean_std(per_metal[metal]["hull_volume"])
        normalized = (
            float(
                np.mean(lengths / (COVALENT_RADII_ANGSTROM[metal] + COVALENT_RADII_ANGSTROM["O"]))
            )
            if lengths.size
            else math.nan
        )
        values = {
            "crystalnn_cn_mean": cn_mean,
            "crystalnn_cn_std": cn_std,
            "voronoi_cn_mean": vor_mean,
            "voronoi_cn_std": vor_std,
            "bond_length_mean": length_distribution["mean"],
            "bond_length_std": length_distribution["std"],
            "bond_length_min": length_distribution["min"],
            "bond_length_max": length_distribution["max"],
            "bond_length_median": length_distribution["median"],
            "bond_length_covalent_normalized_mean": normalized,
            "bond_length_distortion_mean": distortion_mean,
            "quadratic_elongation_mean": elongation_mean,
            "bond_valence_sum_mean": bvs_mean,
            "formal_valence_abs_error_mean": error_mean,
            "formal_valence_abs_error_max": float(errors.max()) if errors.size else math.nan,
            "oxygen_hull_volume_mean": hull_mean,
        }
        for stat in POLYHEDRON_STATS:
            features[f"c360_poly_{metal}_O_{stat}"] = values[stat]

        distribution = _distribution(angle_values[metal])
        pair_count_mean, _ = _mean_std(angle_pair_counts[metal])
        for stat in ANGLE_STATS:
            value = pair_count_mean if stat == "pair_count_mean" else distribution[stat]
            features[f"c360_angle_O_{metal}_O_{stat}"] = value
        angles = np.asarray(angle_values[metal], dtype=float)
        angles = angles[np.isfinite(angles)]
        if angles.size:
            q25, q75 = np.quantile(angles, [0.25, 0.75])
            std = float(angles.std(ddof=0))
            skewness = float(np.mean(((angles - angles.mean()) / std) ** 3)) if std > EPS else 0.0
            iqr = float(q75 - q25)
        else:
            iqr = skewness = math.nan
        features[f"c360_reserve_angle_O_{metal}_O_iqr"] = iqr
        features[f"c360_reserve_angle_O_{metal}_O_skewness"] = skewness

    bridge_angles: dict[tuple[str, str], list[float]] = {pair: [] for pair in BRIDGE_TYPES}
    for oxygen_index, neighbors in reverse_edges.items():
        oxygen = np.asarray(structure[oxygen_index].coords, dtype=float)
        for (left, left_coords), (right, right_coords) in combinations(neighbors, 2):
            pair = tuple(sorted((left, right)))
            if pair in bridge_angles:
                bridge_angles[pair].append(
                    _angle_degrees(left_coords - oxygen, right_coords - oxygen)
                )
    for left, right in BRIDGE_TYPES:
        mean, std = _mean_std(bridge_angles[(left, right)])
        features[f"c360_angle_{left}_O_{right}_mean"] = mean
        features[f"c360_angle_{left}_O_{right}_std"] = std
    return features


def _unique_d_spacings(structure: Structure) -> list[float]:
    lattice = structure.get_reduced_structure(reduction_algo="niggli").lattice
    values: list[float] = []
    for h in range(-3, 4):
        for k in range(-3, 4):
            for ell in range(-3, 4):
                if (h, k, ell) == (0, 0, 0):
                    continue
                first_nonzero = next(value for value in (h, k, ell) if value != 0)
                if first_nonzero < 0:
                    continue
                values.append(float(lattice.d_hkl((h, k, ell))))
    unique: list[float] = []
    for value in sorted(values, reverse=True):
        if not any(
            math.isclose(value, existing, rel_tol=1e-7, abs_tol=1e-9) for existing in unique
        ):
            unique.append(value)
    return unique


def _lattice_features(structure: Structure) -> dict[str, float]:
    lattice = structure.get_reduced_structure(reduction_algo="niggli").lattice
    matrix = np.asarray(lattice.matrix, dtype=float)
    volume = abs(float(np.linalg.det(matrix)))
    face_areas = np.sort(
        np.asarray(
            [
                np.linalg.norm(np.cross(matrix[1], matrix[2])),
                np.linalg.norm(np.cross(matrix[2], matrix[0])),
                np.linalg.norm(np.cross(matrix[0], matrix[1])),
            ],
            dtype=float,
        )
    )
    surface = float(2.0 * face_areas.sum())
    heights = volume / face_areas
    reciprocal = lattice.reciprocal_lattice_crystallographic
    reciprocal_lengths = np.sort(np.asarray(reciprocal.lengths, dtype=float))
    metric = matrix @ matrix.T
    eigenvalues = np.sort(np.linalg.eigvalsh(metric))
    normalized_eigenvalues = eigenvalues / (volume ** (2.0 / 3.0))
    probabilities = eigenvalues / eigenvalues.sum()
    mean_metric = float(np.trace(metric) / 3.0)
    d_values = _unique_d_spacings(structure)
    normalized_d = [value / (volume ** (1.0 / 3.0)) for value in d_values]

    features = {
        "c360_lattice_face_area_min": float(face_areas[0]),
        "c360_lattice_face_area_mid": float(face_areas[1]),
        "c360_lattice_face_area_max": float(face_areas[2]),
        "c360_lattice_surface_area": surface,
        "c360_lattice_surface_volume_ratio": surface / volume,
        "c360_lattice_sphericity": math.pi ** (1.0 / 3.0) * (6.0 * volume) ** (2.0 / 3.0) / surface,
        "c360_lattice_height_min": float(heights.min()),
        "c360_lattice_height_max": float(heights.max()),
        "c360_lattice_height_anisotropy": float((heights.max() - heights.min()) / heights.mean()),
        "c360_lattice_reciprocal_length_min": float(reciprocal_lengths[0]),
        "c360_lattice_reciprocal_length_mid": float(reciprocal_lengths[1]),
        "c360_lattice_reciprocal_length_max": float(reciprocal_lengths[2]),
        "c360_lattice_reciprocal_anisotropy": float(reciprocal_lengths[2] / reciprocal_lengths[0]),
        "c360_lattice_reciprocal_volume": abs(float(np.linalg.det(reciprocal.matrix))),
        "c360_lattice_metric_eigenvalue_min": float(normalized_eigenvalues[0]),
        "c360_lattice_metric_eigenvalue_mid": float(normalized_eigenvalues[1]),
        "c360_lattice_metric_eigenvalue_max": float(normalized_eigenvalues[2]),
        "c360_lattice_metric_condition_number": float(eigenvalues[2] / eigenvalues[0]),
        "c360_lattice_metric_eigenvalue_entropy": float(
            -np.sum(probabilities * np.log(probabilities))
        ),
        "c360_lattice_metric_frobenius_anisotropy": float(
            np.linalg.norm(metric - np.eye(3) * mean_metric, ord="fro") / np.trace(metric)
        ),
    }
    for rank in range(1, 13):
        prefix = "c360_lattice" if rank <= 4 else "c360_reserve_lattice"
        features[f"{prefix}_d_spacing_{rank}_normalized"] = (
            float(normalized_d[rank - 1]) if len(normalized_d) >= rank else math.nan
        )
    return features


def _spglib_cell(structure: Structure) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.asarray(structure.lattice.matrix, dtype=float),
        np.asarray(structure.frac_coords, dtype=float),
        np.asarray([site.specie.Z for site in structure], dtype=int),
    )


def _orbit_entropy(equivalent_atoms: np.ndarray, mask: np.ndarray) -> float:
    selected = np.asarray(equivalent_atoms, dtype=int)[mask]
    if selected.size == 0:
        return math.nan
    counts = np.asarray(list(Counter(selected.tolist()).values()), dtype=float)
    probabilities = counts / counts.sum()
    return float(-np.sum(probabilities * np.log(probabilities)))


def _symmetry_features(
    structure: Structure, supplied_spacegroup: int
) -> tuple[dict[str, float], str]:
    cell = _spglib_cell(structure)
    datasets: dict[float, Any] = {}
    summaries: dict[float, dict[str, float]] = {}
    for symprec in SYMPRECS:
        dataset = spglib.get_symmetry_dataset(cell, symprec=symprec, angle_tolerance=-1.0)
        if dataset is None:
            raise ValueError(f"spglib failed at symprec={symprec}")
        datasets[symprec] = dataset
        equivalent = np.asarray(dataset.equivalent_atoms, dtype=int)
        orbit_sizes = Counter(equivalent.tolist())
        primitive = spglib.standardize_cell(
            cell, to_primitive=True, no_idealize=False, symprec=symprec, angle_tolerance=-1.0
        )
        conventional = spglib.standardize_cell(
            cell, to_primitive=False, no_idealize=False, symprec=symprec, angle_tolerance=-1.0
        )
        primitive_count = float(len(primitive[1])) if primitive is not None else math.nan
        volume_ratio = math.nan
        if primitive is not None and conventional is not None:
            primitive_volume = abs(float(np.linalg.det(primitive[0])))
            conventional_volume = abs(float(np.linalg.det(conventional[0])))
            volume_ratio = primitive_volume / conventional_volume
        site_symmetries = [str(item).strip() for item in dataset.site_symmetry_symbols]
        summaries[symprec] = {
            "operation_count": float(len(dataset.rotations)),
            "orbit_count": float(len(orbit_sizes)),
            "primitive_site_count": primitive_count,
            "primitive_conventional_volume_ratio": volume_ratio,
            "wyckoff_letter_count": float(len(set(str(item) for item in dataset.wyckoffs))),
            "largest_orbit_fraction": float(max(orbit_sizes.values()) / len(structure)),
            "general_position_site_fraction": float(
                np.mean([item == "1" for item in site_symmetries])
            ),
        }

    features: dict[str, float] = {}
    for symprec in (0.01, 0.1):
        label = str(symprec).replace(".", "p")
        for name, value in summaries[symprec].items():
            features[f"c360_sym_s{label}_{name}"] = value

    spacegroups = [int(datasets[symprec].number) for symprec in SYMPRECS]
    operations = np.asarray([summaries[symprec]["operation_count"] for symprec in SYMPRECS])
    orbits = np.asarray([summaries[symprec]["orbit_count"] for symprec in SYMPRECS])
    modal_count = max(Counter(spacegroups).values())
    features.update(
        {
            "c360_sym_spacegroup_distinct_count": float(len(set(spacegroups))),
            "c360_sym_spacegroup_modal_fraction": float(modal_count / len(SYMPRECS)),
            "c360_sym_supplied_spacegroup_match_count": float(
                sum(spacegroup == int(supplied_spacegroup) for spacegroup in spacegroups)
            ),
            "c360_sym_operation_count_cv": float(operations.std(ddof=0) / operations.mean()),
            "c360_sym_orbit_count_range": float(orbits.max() - orbits.min()),
        }
    )
    dataset = datasets[0.01]
    equivalent = np.asarray(dataset.equivalent_atoms, dtype=int)
    symbols = np.asarray([_symbol(site) for site in structure], dtype=object)
    features["c360_sym_wyckoff_orbit_entropy_total"] = _orbit_entropy(
        equivalent, np.ones(len(structure), dtype=bool)
    )
    features["c360_sym_wyckoff_orbit_entropy_cation"] = _orbit_entropy(
        equivalent, np.isin(symbols, CATIONS)
    )
    features["c360_sym_wyckoff_orbit_entropy_oxygen"] = _orbit_entropy(equivalent, symbols == "O")

    orbit_sizes = sorted(Counter(equivalent.tolist()).values())
    counts = Counter(symbols.tolist())
    divisor = math.gcd(*counts.values())
    anonymous_stoichiometry = sorted(value // divisor for value in counts.values())
    prototype = (
        f"sg{int(dataset.number)}|orbits{','.join(map(str, orbit_sizes))}"
        f"|stoich{','.join(map(str, anonymous_stoichiometry))}"
    )
    return features, prototype


def _extract_structure(
    structure: Structure,
    supplied_spacegroup: int,
    shell_boundaries: dict[str, list[float]],
) -> tuple[dict[str, float], str]:
    features: dict[str, float] = {}
    neighbor_data = _periodic_neighbor_data(structure)
    pair_distances = _pair_distances_from_neighbor_data(neighbor_data)
    volume = float(structure.volume)
    symbols = neighbor_data["symbols"]

    for source, target in PAIR_TYPES:
        pair = _pair_key(source, target)
        distances = pair_distances[pair]
        first, _ = _nearest_two_by_source(structure, neighbor_data, source, target)
        distribution = _distribution(distances)
        nn_mean, nn_std = _mean_std(first)
        pair_values = {
            "min": distribution["min"],
            "nn_mean": nn_mean,
            "nn_std": nn_std,
            "q10": distribution["q10"],
            "q25": distribution["q25"],
            "median": distribution["median"],
            "q75": distribution["q75"],
            "q90": distribution["q90"],
        }
        for stat in PAIR_PROFILE_STATS:
            features[f"c360_pair_{source}_{target}_{stat}"] = pair_values[stat]
        if distances.size:
            features[f"c360_reserve_pair_{source}_{target}_q05"] = float(
                np.quantile(distances, 0.05)
            )
            features[f"c360_reserve_pair_{source}_{target}_q95"] = float(
                np.quantile(distances, 0.95)
            )
        else:
            features[f"c360_reserve_pair_{source}_{target}_q05"] = math.nan
            features[f"c360_reserve_pair_{source}_{target}_q95"] = math.nan

        source_count = int(np.sum(symbols == source))
        target_count = int(np.sum(symbols == target))
        edges = np.asarray(shell_boundaries[pair], dtype=float)
        if source_count == 0 or target_count == 0:
            rdf = np.full(8, np.nan)
        else:
            shell_counts, _ = np.histogram(distances, bins=edges)
            shell_volumes = (4.0 * math.pi / 3.0) * (edges[1:] ** 3 - edges[:-1] ** 3)
            target_density = target_count / volume
            denominators = source_count * target_density * shell_volumes
            rdf = np.divide(
                shell_counts,
                denominators,
                out=np.full(8, np.nan, dtype=float),
                where=denominators > EPS,
            )
        for shell, value in enumerate(rdf, start=1):
            features[f"c360_rdf_{source}_{target}_shell_{shell}"] = float(value)

    voronoi = _voronoi_counts(structure)
    for source in ELEMENTS:
        for target in ELEMENTS:
            first, second = _nearest_two_by_source(structure, neighbor_data, source, target)
            first_mean, first_std = _mean_std(first)
            second_mean, second_std = _mean_std(second)
            vor_mean, vor_std = _mean_std(voronoi[source][target])
            stem = f"c360_env_{source}_to_{target}"
            features[f"{stem}_nn_distance_mean"] = first_mean
            features[f"{stem}_nn_distance_std"] = first_std
            features[f"{stem}_voronoi_count_mean"] = vor_mean
            features[f"{stem}_voronoi_count_std"] = vor_std
            reserve_stem = f"c360_reserve_env_{source}_to_{target}_second_nn"
            features[f"{reserve_stem}_mean"] = second_mean
            features[f"{reserve_stem}_std"] = second_std

    features.update(_metal_and_angle_features(structure, voronoi))
    features.update(_lattice_features(structure))
    symmetry, prototype = _symmetry_features(structure, supplied_spacegroup)
    features.update(symmetry)
    return features, prototype


class Crystal360Featurizer:
    """Fit training-only radial shells and transform periodic structures."""

    def __init__(self, n_jobs: int = 1) -> None:
        self.n_jobs = n_jobs
        self.primary_definitions = build_primary_definitions()
        self.reserve_definitions = build_reserve_definitions()

    @property
    def candidate_columns(self) -> list[str]:
        return [item.name for item in self.primary_definitions + self.reserve_definitions]

    def fit_shell_boundaries(self, structures: list[Structure]) -> dict[str, list[float]]:
        rows = Parallel(n_jobs=self.n_jobs, prefer="processes", verbose=0)(
            delayed(_fit_structure_pair_distances)(structure) for structure in structures
        )
        boundaries: dict[str, list[float]] = {}
        for source, target in PAIR_TYPES:
            pair = _pair_key(source, target)
            arrays = [row[pair] for row in rows if row[pair].size]
            if arrays:
                pooled = np.concatenate(arrays)
                interior = np.quantile(pooled, np.arange(1, 8) / 8.0)
                edges = np.concatenate(
                    ([0.0], np.clip(interior, 0.0, CUTOFF_ANGSTROM), [CUTOFF_ANGSTROM])
                )
            else:
                edges = np.linspace(0.0, CUTOFF_ANGSTROM, 9)
            boundaries[pair] = [float(value) for value in edges]
        return boundaries

    def transform_candidates(
        self,
        structures: list[Structure],
        supplied_spacegroups: Iterable[int],
        shell_boundaries: dict[str, list[float]],
    ) -> tuple[pd.DataFrame, list[str]]:
        spacegroups = [int(value) for value in supplied_spacegroups]
        if len(spacegroups) != len(structures):
            raise ValueError("Structure and supplied-spacegroup counts differ")
        rows = Parallel(n_jobs=self.n_jobs, prefer="processes", verbose=0)(
            delayed(_extract_structure)(structure, spacegroup, shell_boundaries)
            for structure, spacegroup in zip(structures, spacegroups)
        )
        features = pd.DataFrame([row[0] for row in rows], columns=self.candidate_columns)
        return features, [row[1] for row in rows]

    def select_schema(
        self,
        train_candidates: pd.DataFrame,
        baseline_train: pd.DataFrame,
        shell_boundaries: dict[str, list[float]],
        training_source: dict[str, Any],
    ) -> Crystal360Schema:
        baseline_signatures = {
            _array_signature(baseline_train[column].to_numpy(dtype=float))
            for column in baseline_train.columns
        }
        selected_signatures: set[str] = set()
        selected: list[FeatureDefinition] = []
        replacements: list[dict[str, str]] = []
        reserve_index = 0

        def rejection_reason(definition: FeatureDefinition) -> str | None:
            values = train_candidates[definition.name].to_numpy(dtype=float)
            finite = values[np.isfinite(values)]
            if finite.size == 0 or np.unique(finite).size <= 1:
                return "constant_or_all_missing"
            signature = _array_signature(values)
            if signature in selected_signatures:
                return "duplicate_within_crystal360"
            if signature in baseline_signatures:
                return "duplicate_of_baseline_449"
            return None

        for primary in self.primary_definitions:
            choice = primary
            reason = rejection_reason(choice)
            while reason is not None:
                if reserve_index >= len(self.reserve_definitions):
                    raise ValueError(
                        f"Reserve bank exhausted while replacing {primary.name}: {reason}"
                    )
                candidate = self.reserve_definitions[reserve_index]
                reserve_index += 1
                candidate_reason = rejection_reason(candidate)
                if candidate_reason is not None:
                    continue
                choice = candidate
                choice = replace(
                    choice,
                    family=primary.family,
                    physical_family=candidate.family,
                )
                replacements.append(
                    {"replaced": primary.name, "replacement": choice.name, "reason": reason}
                )
                reason = None
            selected.append(choice)
            selected_signatures.add(
                _array_signature(train_candidates[choice.name].to_numpy(dtype=float))
            )

        schema = Crystal360Schema(
            shell_boundaries_angstrom=boundaries_with_hyphens(shell_boundaries),
            selected_features=selected,
            replacements=replacements,
            training_source=training_source,
        )
        schema.validate()
        return schema

    @staticmethod
    def transform_selected(candidates: pd.DataFrame, schema: Crystal360Schema) -> pd.DataFrame:
        missing = [column for column in schema.columns if column not in candidates]
        if missing:
            raise ValueError(f"Candidate table is missing selected columns: {missing}")
        return candidates.loc[:, schema.columns].copy()


def boundaries_with_hyphens(boundaries: dict[str, list[float]]) -> dict[str, list[float]]:
    result: dict[str, list[float]] = {}
    for source, target in PAIR_TYPES:
        canonical = _pair_key(source, target)
        result[canonical] = list(boundaries[canonical])
    return result
