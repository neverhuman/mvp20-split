from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import spglib
from pymatgen.core import Structure
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.stats import wasserstein_distance

from .constants import TRUSTED_KERNELS


Kernel = Callable[[Structure, dict[str, Any]], dict[str, float]]
EPSILON = 1e-12


KERNEL_CONFIG_FIELDS: dict[str, set[str]] = {
    "symmetry": {"symprec"},
    "reciprocal": {"hmax", "weight", "debye_waller_b"},
    "orbital_local": {"cutoff"},
    "electrostatic": {
        "bond_valence_b",
        "screening_length",
        "charge_scale",
        "qeq_screening_length",
    },
    "local_density": {"cutoff", "radial_centers", "width"},
    "periodic_graph": {"cutoff"},
    "canonical_topology": {"grid", "void_threshold"},
    "thermodynamics": {"pair_cutoff", "redox_scale"},
    "mechanics": {"bond_cutoff", "stiffness_exponent"},
    "entropy_transport": {"cutoff"},
}


def validate_kernel_config(kernel: str, config: Any) -> list[str]:
    if kernel not in KERNEL_CONFIG_FIELDS:
        return [f"unsupported trusted kernel: {kernel}"]
    if not isinstance(config, dict):
        return ["kernel configuration must be an object"]
    errors = [
        f"unsupported {kernel} setting: {name}"
        for name in sorted(set(config) - KERNEL_CONFIG_FIELDS[kernel])
    ]

    def bounded(name: str, minimum: float, maximum: float, *, integer: bool = False) -> None:
        if name not in config:
            return
        value = config[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{kernel}.{name} must be numeric")
            return
        numeric = float(value)
        if not math.isfinite(numeric) or not minimum <= numeric <= maximum:
            errors.append(f"{kernel}.{name} must be in [{minimum}, {maximum}]")
        if integer and int(numeric) != numeric:
            errors.append(f"{kernel}.{name} must be an integer")

    if kernel == "symmetry":
        bounded("symprec", 1e-5, 0.1)
    elif kernel == "reciprocal":
        bounded("hmax", 1, 4, integer=True)
        bounded("debye_waller_b", 0.0, 3.0)
        if config.get("weight", "Z") not in {"Z", "atomic_mass", "X", "atomic_radius"}:
            errors.append("reciprocal.weight is not an approved species property")
    elif kernel in {"orbital_local", "periodic_graph", "entropy_transport"}:
        bounded("cutoff", 1.0, 12.0)
    elif kernel == "electrostatic":
        bounded("bond_valence_b", 0.1, 1.0)
        bounded("screening_length", 0.5, 20.0)
        bounded("charge_scale", 0.5, 1.5)
        bounded("qeq_screening_length", 0.5, 20.0)
    elif kernel == "local_density":
        bounded("cutoff", 1.0, 12.0)
        bounded("width", 0.05, 2.0)
        if "radial_centers" in config:
            centers = config["radial_centers"]
            if (
                not isinstance(centers, list)
                or not 1 <= len(centers) <= 12
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not 0.2 <= float(value) <= 12.0
                    for value in centers
                )
                or list(centers) != sorted(set(centers))
            ):
                errors.append(
                    "local_density.radial_centers must be 1..12 unique ascending values in [0.2, 12]"
                )
    elif kernel == "canonical_topology":
        bounded("grid", 3, 8, integer=True)
        bounded("void_threshold", 0.1, 5.0)
    elif kernel == "thermodynamics":
        bounded("pair_cutoff", 1.5, 12.0)
        bounded("redox_scale", 0.5, 1.5)
    elif kernel == "mechanics":
        bounded("bond_cutoff", 1.5, 8.0)
        bounded("stiffness_exponent", 2.0, 6.0)
    return errors


def canonical_structure(structure: Structure) -> Structure:
    """Wrap, primitive-reduce, and Niggli-reduce without changing chemistry."""

    if getattr(structure, "_nomad_v2_canonical", False) is True:
        return structure

    wrapped = Structure(
        structure.lattice,
        structure.species,
        np.asarray(structure.frac_coords, dtype=float) % 1.0,
        to_unit_cell=True,
    )
    try:
        wrapped = wrapped.get_primitive_structure(tolerance=1e-3)
    except Exception:
        pass
    try:
        wrapped = wrapped.get_reduced_structure(reduction_algo="niggli")
    except Exception:
        pass
    canonical = Structure(
        wrapped.lattice,
        wrapped.species,
        np.asarray(wrapped.frac_coords, dtype=float) % 1.0,
        to_unit_cell=True,
    )
    canonical._nomad_v2_canonical = True
    return canonical


def primitive_wrapped_structure(structure: Structure) -> Structure:
    """Primitive wrapped cell without orientation-sensitive Niggli basis selection."""

    wrapped = Structure(
        structure.lattice,
        structure.species,
        np.asarray(structure.frac_coords, dtype=float) % 1.0,
        to_unit_cell=True,
    )
    try:
        wrapped = wrapped.get_primitive_structure(tolerance=1e-3)
    except Exception:
        pass
    return Structure(
        wrapped.lattice,
        wrapped.species,
        np.asarray(wrapped.frac_coords, dtype=float) % 1.0,
        to_unit_cell=True,
    )


def structure_signature(structure: Structure) -> str:
    canonical = canonical_structure(structure)
    sites = sorted(
        (
            int(site.specie.Z),
            *(round(float(value) % 1.0, 10) for value in site.frac_coords),
        )
        for site in canonical
    )
    payload = {
        "lattice_metric": np.round(
            np.asarray(canonical.lattice.matrix) @ np.asarray(canonical.lattice.matrix).T, 10
        ).tolist(),
        "sites": sites,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _finite(result: dict[str, Any]) -> dict[str, float]:
    cleaned: dict[str, float] = {}
    for key, value in result.items():
        numeric = float(value)
        cleaned[key] = numeric if math.isfinite(numeric) else 0.0
    return cleaned


def _property(structure: Structure, name: str, default: float = 0.0) -> np.ndarray:
    values = []
    for site in structure:
        value = getattr(site.specie, name, None)
        try:
            values.append(float(value) if value is not None else default)
        except (TypeError, ValueError):
            values.append(default)
    return np.asarray(values, dtype=float)


def _pair_data(structure: Structure) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    distances = np.asarray(structure.distance_matrix, dtype=float)
    left, right = np.triu_indices(len(structure), k=1)
    return distances[left, right], left, right


def _entropy(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    total = float(values.sum())
    if total <= 0:
        return 0.0
    probabilities = values[values > 0] / total
    return float(-np.sum(probabilities * np.log(probabilities)))


def symmetry_kernel(structure: Structure, config: dict[str, Any]) -> dict[str, float]:
    crystal = canonical_structure(structure)
    symprec = float(config.get("symprec", 1e-3))
    cell = (
        np.asarray(crystal.lattice.matrix, dtype=float),
        np.asarray(crystal.frac_coords, dtype=float),
        np.asarray([site.specie.Z for site in crystal], dtype=int),
    )
    dataset = spglib.get_symmetry_dataset(cell, symprec=symprec)
    if dataset is None:
        return {name: 0.0 for name in KERNEL_OPERATIONS["symmetry"]}
    equivalent = np.asarray(dataset.equivalent_atoms, dtype=int)
    orbit_counts = np.asarray(list(Counter(equivalent.tolist()).values()), dtype=float)
    orbit_probabilities = orbit_counts / max(len(crystal), 1)
    rotations = np.asarray(dataset.rotations, dtype=int)
    translations = np.asarray(dataset.translations, dtype=float)
    inversion = np.any(np.all(rotations == -np.eye(3, dtype=int), axis=(1, 2)))
    fractional = np.asarray(crystal.frac_coords, dtype=float)
    atomic_numbers = np.asarray([site.specie.Z for site in crystal], dtype=int)
    residuals: list[float] = []
    for rotation, translation in list(zip(rotations, translations, strict=True))[:32]:
        transformed = (fractional @ rotation.T + translation) % 1.0
        rotation_residuals = np.empty(len(crystal), dtype=float)
        for atomic_number in np.unique(atomic_numbers):
            species_mask = atomic_numbers == atomic_number
            distances = crystal.lattice.get_all_distances(
                transformed[species_mask], fractional[species_mask]
            )
            rotation_residuals[species_mask] = np.min(distances, axis=1)
        residuals.extend(rotation_residuals.tolist())
    residual = np.asarray(residuals, dtype=float)
    normalized_residual = residual / max(symprec, EPSILON)
    residual_histogram = np.histogram(
        np.clip(normalized_residual, 0.0, 2.0), bins=8, range=(0.0, 2.0)
    )[0]
    return _finite(
        {
            "spacegroup-number": dataset.number,
            "orbit-fraction": len(orbit_counts) / max(len(crystal), 1),
            "orbit-entropy": _entropy(orbit_counts),
            "largest-orbit-fraction": float(orbit_probabilities.max(initial=0.0)),
            "wyckoff-fraction": len(set(dataset.wyckoffs)) / max(len(crystal), 1),
            "site-symmetry-fraction": len(set(dataset.site_symmetry_symbols))
            / max(len(crystal), 1),
            "symmetry-operations-per-site": len(rotations) / max(len(crystal), 1),
            "centrosymmetric": float(inversion),
            "symmetry-residual-mean": residual.mean() if residual.size else 0.0,
            "symmetry-residual-std": residual.std() if residual.size else 0.0,
            "symmetry-residual-max": residual.max(initial=0.0),
            "symmetry-residual-q90": (
                np.quantile(residual, 0.9) if residual.size else 0.0
            ),
            "normalized-residual-mean": (
                normalized_residual.mean() if normalized_residual.size else 0.0
            ),
            "normalized-residual-max": normalized_residual.max(initial=0.0),
            "symmetry-confidence": math.exp(
                -float(normalized_residual.mean()) if normalized_residual.size else 0.0
            ),
            "symmetry-residual-entropy": _entropy(residual_histogram),
        }
    )


def reciprocal_kernel(structure: Structure, config: dict[str, Any]) -> dict[str, float]:
    crystal = canonical_structure(structure)
    hmax = min(max(int(config.get("hmax", 2)), 1), 4)
    weights = _property(crystal, str(config.get("weight", "Z")), default=1.0)
    if np.allclose(weights, 0):
        weights = np.ones(len(crystal))
    debye_waller_b = float(config.get("debye_waller_b", 0.0))
    pair, left, right = _pair_data(crystal)
    q_step = 2.0 * np.pi / max(float(crystal.volume) ** (1.0 / 3.0), EPSILON)
    q = q_step * np.arange(1, 16 * hmax + 1, dtype=float)
    denominator = float(np.sum(np.abs(weights)) ** 2 + EPSILON)
    self_scattering = float(np.sum(weights**2))
    if pair.size:
        phase = np.sinc(q[:, None] * pair[None, :] / np.pi)
        cross = 2.0 * np.sum(
            weights[left][None, :] * weights[right][None, :] * phase,
            axis=1,
        )
    else:
        cross = np.zeros_like(q)
    intensity = np.maximum(self_scattering + cross, 0.0) / denominator
    intensity *= np.exp(-debye_waller_b * q**2)
    return _finite(
        {
            "structure-factor-mean": intensity.mean(),
            "structure-factor-std": intensity.std(),
            "structure-factor-max": intensity.max(initial=0.0),
            "structure-factor-entropy": _entropy(intensity),
            "reciprocal-q-mean": q.mean(),
            "reciprocal-q-std": q.std(),
            "patterson-pair-mean": pair.mean() if pair.size else 0.0,
            "phase-coherence": np.mean(np.sqrt(np.maximum(intensity, 0.0))),
        }
    )


def orbital_local_kernel(structure: Structure, config: dict[str, Any]) -> dict[str, float]:
    crystal = canonical_structure(structure)
    cutoff = float(config.get("cutoff", 4.0))
    z = _property(crystal, "Z")
    group = _property(crystal, "group")
    electronegativity = _property(crystal, "X")
    centers, others, _images, distances = crystal.get_neighbor_list(cutoff)
    keep = np.asarray(distances, dtype=float) > 1e-8
    centers = np.asarray(centers, dtype=int)[keep]
    others = np.asarray(others, dtype=int)[keep]
    distances = np.asarray(distances, dtype=float)[keep]
    coord = np.bincount(centers, minlength=len(crystal)).astype(float)
    weights = np.exp(-distances / max(cutoff, EPSILON))
    z_mismatch = np.abs(z[centers] - z[others]) * weights
    group_mismatch = np.abs(group[centers] - group[others]) * weights
    x_mismatch = np.abs(electronegativity[centers] - electronegativity[others]) * weights
    orbital_field = group[centers] * group[others] * weights
    return _finite(
        {
            "coordination-mean": coord.mean(),
            "coordination-std": coord.std(),
            "coordination-entropy": _entropy(np.bincount(coord.astype(int))),
            "atomic-number-mismatch": z_mismatch.mean() if z_mismatch.size else 0.0,
            "group-mismatch": group_mismatch.mean() if group_mismatch.size else 0.0,
            "electronegativity-mismatch": x_mismatch.mean() if x_mismatch.size else 0.0,
            "orbital-field-mean": orbital_field.mean() if orbital_field.size else 0.0,
            "orbital-field-std": orbital_field.std() if orbital_field.size else 0.0,
        }
    )


def _formal_charges(structure: Structure) -> np.ndarray:
    defaults = {"Al": 3.0, "Ga": 3.0, "In": 3.0, "O": -2.0}
    return np.asarray([defaults.get(site.specie.symbol, 0.0) for site in structure])


def electrostatic_kernel(structure: Structure, config: dict[str, Any]) -> dict[str, float]:
    crystal = canonical_structure(structure)
    distances, left, right = _pair_data(crystal)
    charges = _formal_charges(crystal) * float(config.get("charge_scale", 1.0))
    x = _property(crystal, "X")
    radii = _property(crystal, "atomic_radius", default=1.0)
    if not distances.size:
        pair_energy = potential = qeq = valence = np.zeros(1)
    else:
        pair_energy = (
            charges[left]
            * charges[right]
            / np.maximum(distances, EPSILON)
            * np.exp(-distances / float(config.get("screening_length", 8.0)))
        )
        potential = np.abs(pair_energy)
        qeq = (
            np.abs(x[left] - x[right])
            / np.maximum(distances, EPSILON)
            * np.exp(
                -distances / float(config.get("qeq_screening_length", 8.0))
            )
        )
        reference = radii[left] + radii[right]
        valence = np.exp((reference - distances) / float(config.get("bond_valence_b", 0.37)))
    site_potential = np.zeros(len(crystal), dtype=float)
    for value, i, j in zip(pair_energy, left, right):
        site_potential[i] += value
        site_potential[j] += value
    return _finite(
        {
            "ewald-pair-mean": pair_energy.mean(),
            "ewald-pair-absolute": potential.mean(),
            "formal-potential-std": site_potential.std(),
            "charge-neutrality": abs(charges.sum()) / max(len(crystal), 1),
            "bond-valence-mean": valence.mean(),
            "bond-valence-mismatch": np.mean(np.abs(valence - 1.0)),
            "charge-equilibration-mean": qeq.mean(),
            "charge-equilibration-max": qeq.max(initial=0.0),
        }
    )


def local_density_kernel(structure: Structure, config: dict[str, Any]) -> dict[str, float]:
    crystal = canonical_structure(structure)
    cutoff = float(config.get("cutoff", 6.0))
    centers = np.asarray(config.get("radial_centers", [1.5, 2.0, 2.5, 3.0]), dtype=float)
    width = float(config.get("width", 0.35))
    local_primitives = getattr(crystal, "_nomad_v2_local_primitives", None)
    cached_radius = float(local_primitives[0]) if local_primitives is not None else 0.0
    if local_primitives is None or cached_radius + EPSILON < cutoff:
        neighbor_radius = math.ceil(cutoff * 4.0) / 4.0
        neighbors_at_maximum = crystal.get_all_neighbors(neighbor_radius)
        site_primitives = []
        all_distances = []
        for site, maximum_neighbors in zip(crystal, neighbors_at_maximum, strict=True):
            ordered = sorted(
                (
                    neighbor
                    for neighbor in maximum_neighbors
                    if float(neighbor.nn_distance) > 1e-8
                ),
                key=lambda neighbor: float(neighbor.nn_distance),
            )
            distances = np.asarray(
                [float(neighbor.nn_distance) for neighbor in ordered], dtype=float
            )
            all_distances.extend(distances.tolist())
            angular_limit = (
                int(
                    np.searchsorted(
                        distances,
                        distances[min(7, len(distances) - 1)] + 1e-8,
                        side="right",
                    )
                )
                if distances.size
                else 0
            )
            vectors = [
                np.asarray(neighbor.coords) - np.asarray(site.coords)
                for neighbor in ordered[:angular_limit]
            ]
            pair_cosines: list[tuple[float, float]] = []
            for first in range(len(vectors)):
                for second in range(first + 1, len(vectors)):
                    denominator = np.linalg.norm(vectors[first]) * np.linalg.norm(vectors[second])
                    if denominator > EPSILON:
                        pair_cosines.append(
                            (
                                max(distances[first], distances[second]),
                                float(np.dot(vectors[first], vectors[second]) / denominator),
                            )
                        )
            site_primitives.append((distances, pair_cosines))
        local_primitives = (
            neighbor_radius,
            np.asarray(all_distances, dtype=float),
            site_primitives,
        )
        crystal._nomad_v2_local_primitives = local_primitives
    _, all_distances, site_primitives = local_primitives
    included_distances = all_distances[all_distances <= cutoff]
    radial = (
        np.sum(
            np.exp(-((included_distances[:, None] - centers[None, :]) / width) ** 2),
            axis=0,
        )
        if included_distances.size
        else np.zeros(len(centers), dtype=float)
    )
    angular: list[float] = []
    neighbor_counts: list[int] = []
    for distances, pair_cosines in site_primitives:
        count = int(np.searchsorted(distances, cutoff, side="right"))
        neighbor_counts.append(count)
        if count:
            shell_limit = distances[min(7, count - 1)] + 1e-8
            angular.extend(cosine for distance, cosine in pair_cosines if distance <= shell_limit)
    radial /= max(len(crystal), 1)
    counts = np.asarray(neighbor_counts, dtype=float)
    return _finite(
        {
            "soap-norm": np.linalg.norm(radial),
            "soap-entropy": _entropy(radial),
            "acsf-radial-mean": radial.mean(),
            "acsf-radial-std": radial.std(),
            "acsf-angular-mean": np.mean(angular) if angular else 0.0,
            "acsf-angular-std": np.std(angular) if angular else 0.0,
            "mbtr-inverse-distance": (
                np.mean(1.0 / included_distances) if included_distances.size else 0.0
            ),
            "local-density-cv": counts.std() / max(counts.mean(), EPSILON),
        }
    )


def periodic_graph_kernel(structure: Structure, config: dict[str, Any]) -> dict[str, float]:
    crystal = canonical_structure(structure)
    cutoff = float(config.get("cutoff", 3.2))
    distances = getattr(crystal, "_nomad_v2_distance_matrix", None)
    if distances is None:
        distances = np.asarray(crystal.distance_matrix, dtype=float)
        crystal._nomad_v2_distance_matrix = distances
    adjacency = ((distances > EPSILON) & (distances <= cutoff)).astype(float)
    degree = adjacency.sum(axis=1)
    laplacian = np.diag(degree) - adjacency
    eigenvalues = np.linalg.eigvalsh(laplacian) if len(crystal) else np.zeros(1)
    positive = eigenvalues[eigenvalues > 1e-9]
    normalized = positive / max(positive.sum(), EPSILON)
    triangles = np.trace(adjacency @ adjacency @ adjacency) / 6.0
    edges = adjacency.sum() / 2.0
    return _finite(
        {
            "degree-mean": degree.mean(),
            "degree-std": degree.std(),
            "algebraic-connectivity": positive.min() if positive.size else 0.0,
            "spectral-radius": eigenvalues.max(initial=0.0),
            "heat-trace-short": np.mean(np.exp(-0.1 * eigenvalues)),
            "heat-trace-long": np.mean(np.exp(-1.0 * eigenvalues)),
            "triangle-density": triangles / max(len(crystal), 1),
            "rigidity-excess": (edges - max(3 * len(crystal) - 6, 0)) / max(len(crystal), 1),
            "spectral-entropy": _entropy(normalized),
        }
    )


def canonical_topology_kernel(structure: Structure, config: dict[str, Any]) -> dict[str, float]:
    crystal = canonical_structure(structure)
    topology_base = getattr(crystal, "_nomad_v2_topology_base", None)
    if topology_base is None:
        pair, _, _ = _pair_data(crystal)
        distance_matrix = np.asarray(crystal.distance_matrix, dtype=float)
        mst = np.asarray(minimum_spanning_tree(distance_matrix).toarray(), dtype=float)
        topology_base = (pair, mst[mst > 0])
        crystal._nomad_v2_topology_base = topology_base
    pair, lifetimes = topology_base
    grid_n = min(max(int(config.get("grid", 4)), 3), 8)
    void_cache = getattr(crystal, "_nomad_v2_void_radii", None)
    if void_cache is None:
        void_cache = {}
        crystal._nomad_v2_void_radii = void_cache
    if grid_n not in void_cache:
        axis = (np.arange(grid_n, dtype=float) + 0.5) / grid_n
        base_grid = np.asarray(np.meshgrid(axis, axis, axis, indexing="ij")).reshape(
            3, -1
        ).T
        fractional = np.asarray(crystal.frac_coords)
        # Anchor at every site so the pooled grid is independent of the cell origin.
        anchors_per_chunk = max(1, 8192 // len(base_grid))
        void_cache[grid_n] = np.concatenate(
            [
                np.min(
                    crystal.lattice.get_all_distances(
                        (
                            base_grid[None, :, :]
                            + fractional[start : start + anchors_per_chunk, None, :]
                        ).reshape(-1, 3)
                        % 1.0,
                        fractional,
                    ),
                    axis=1,
                )
                for start in range(0, len(fractional), anchors_per_chunk)
            ]
        )
    void_radii = void_cache[grid_n]
    threshold = float(config.get("void_threshold", 1.0))
    occupied_fraction = float(np.mean(void_radii <= threshold))
    return _finite(
        {
            "persistence-lifetime-mean": lifetimes.mean() if lifetimes.size else 0.0,
            "persistence-lifetime-std": lifetimes.std() if lifetimes.size else 0.0,
            "persistence-lifetime-max": lifetimes.max(initial=0.0),
            "pair-distance-entropy": _entropy(np.histogram(pair, bins=8)[0]) if pair.size else 0.0,
            "void-radius-mean": void_radii.mean(),
            "void-radius-max": void_radii.max(initial=0.0),
            "minkowski-volume-fraction": occupied_fraction,
            "minkowski-interface-proxy": occupied_fraction * (1.0 - occupied_fraction),
        }
    )


def thermodynamics_kernel(structure: Structure, config: dict[str, Any]) -> dict[str, float]:
    crystal = canonical_structure(structure)
    counts = Counter(site.specie.symbol for site in crystal)
    fractions = np.asarray(list(counts.values()), dtype=float) / max(len(crystal), 1)
    x = _property(crystal, "X")
    z = _property(crystal, "Z")
    radii = _property(crystal, "atomic_radius", default=1.0)
    pair, left, right = _pair_data(crystal)
    included = pair <= float(config.get("pair_cutoff", 8.0))
    pair = pair[included]
    left = left[included]
    right = right[included]
    weights = np.ones_like(pair) / max(len(pair), 1)
    redox = _formal_charges(crystal) * float(config.get("redox_scale", 1.0))
    return _finite(
        {
            "mixing-entropy": _entropy(fractions),
            "mixing-gini": 1.0 - np.sum(fractions**2),
            "electronegativity-mismatch": np.sum(weights * np.abs(x[left] - x[right])),
            "radius-mismatch": np.sum(weights * np.abs(radii[left] - radii[right])),
            "atomic-number-mismatch": np.sum(weights * np.abs(z[left] - z[right])),
            "redox-imbalance": abs(redox.sum()) / max(len(crystal), 1),
            "redox-variance": redox.var(),
            "bond-mismatch-energy": np.mean((pair - (radii[left] + radii[right])) ** 2)
            if pair.size
            else 0.0,
        }
    )


def mechanics_kernel(structure: Structure, config: dict[str, Any]) -> dict[str, float]:
    crystal = canonical_structure(structure)
    pair, left, right = _pair_data(crystal)
    symbols = np.asarray([site.specie.symbol for site in crystal])
    metal_oxygen = (
        ((symbols[left] != "O") & (symbols[right] == "O"))
        | ((symbols[right] != "O") & (symbols[left] == "O"))
        if pair.size
        else np.zeros(0, dtype=bool)
    )
    bonds = pair[metal_oxygen]
    if not bonds.size:
        bonds = pair
    bonds = bonds[bonds <= float(config.get("bond_cutoff", 8.0))]
    mass = _property(crystal, "atomic_mass", default=1.0)
    exponent = float(config.get("stiffness_exponent", 3.0))
    stiffness = (
        np.power(np.maximum(bonds, EPSILON), -exponent) if bonds.size else np.zeros(1)
    )
    mean_bond = float(bonds.mean()) if bonds.size else 0.0
    strain = (bonds - mean_bond) / max(mean_bond, EPSILON) if bonds.size else np.zeros(1)
    density = float(crystal.density)
    debye = math.sqrt(max(float(stiffness.mean()), 0.0) / max(float(mass.mean()), EPSILON))
    debye *= max(density, EPSILON) ** (1.0 / 3.0)
    return _finite(
        {
            "polyhedral-bond-mean": mean_bond,
            "polyhedral-bond-std": bonds.std() if bonds.size else 0.0,
            "polyhedral-strain-mean": np.mean(np.abs(strain)),
            "polyhedral-strain-max": np.max(np.abs(strain)),
            "bond-stiffness-mean": stiffness.mean(),
            "bond-stiffness-std": stiffness.std(),
            "mass-density": density,
            "debye-proxy": debye,
        }
    )


def entropy_transport_kernel(structure: Structure, config: dict[str, Any]) -> dict[str, float]:
    crystal = canonical_structure(structure)
    pair, left, right = _pair_data(crystal)
    cutoff = float(config.get("cutoff", 8.0))
    histograms = []
    for scale in (0.5, 1.0, 2.0):
        bins = max(int(8 * scale), 2)
        histograms.append(np.histogram(pair, bins=bins, range=(0, cutoff))[0])
    symbols = np.asarray([site.specie.symbol for site in crystal])
    if pair.size:
        metal_oxygen = ((symbols[left] == "O") ^ (symbols[right] == "O"))
        oxygen_oxygen = (symbols[left] == "O") & (symbols[right] == "O")
        first = pair[metal_oxygen]
        second = pair[oxygen_oxygen]
    else:
        first = second = np.zeros(0)
    transport = (
        wasserstein_distance(first, second) if first.size and second.size else 0.0
    )
    charges = _formal_charges(crystal)
    composition_entropy = _entropy(np.asarray(list(Counter(symbols).values()), dtype=float))
    radial_entropy = [_entropy(histogram) for histogram in histograms]
    return _finite(
        {
            "radial-entropy-fine": radial_entropy[0],
            "radial-entropy-medium": radial_entropy[1],
            "radial-entropy-coarse": radial_entropy[2],
            "entropy-scale-slope": radial_entropy[2] - radial_entropy[0],
            "renyi-two": -math.log(max(np.sum((histograms[1] / max(histograms[1].sum(), 1)) ** 2), EPSILON)),
            "species-distance-transport": transport,
            "charge-entropy-coupling": composition_entropy * float(np.std(charges)),
            "transport-density-coupling": transport * len(crystal) / max(crystal.volume, EPSILON),
        }
    )


KERNELS: dict[str, Kernel] = {
    "symmetry": symmetry_kernel,
    "reciprocal": reciprocal_kernel,
    "orbital_local": orbital_local_kernel,
    "electrostatic": electrostatic_kernel,
    "local_density": local_density_kernel,
    "periodic_graph": periodic_graph_kernel,
    "canonical_topology": canonical_topology_kernel,
    "thermodynamics": thermodynamics_kernel,
    "mechanics": mechanics_kernel,
    "entropy_transport": entropy_transport_kernel,
}
KERNEL_OPERATIONS: dict[str, tuple[str, ...]] = {
    name: tuple(function.__name__.removesuffix("_kernel") for _ in ()) for name, function in KERNELS.items()
}
# Explicit operation registries are part of the trusted compiler contract.
KERNEL_OPERATIONS.update(
    {
        "symmetry": (
            "spacegroup-number", "orbit-fraction", "orbit-entropy", "largest-orbit-fraction",
            "wyckoff-fraction", "site-symmetry-fraction", "symmetry-operations-per-site",
            "centrosymmetric", "symmetry-residual-mean", "symmetry-residual-std",
            "symmetry-residual-max", "symmetry-residual-q90", "normalized-residual-mean",
            "normalized-residual-max", "symmetry-confidence", "symmetry-residual-entropy",
        ),
        "reciprocal": (
            "structure-factor-mean", "structure-factor-std", "structure-factor-max",
            "structure-factor-entropy", "reciprocal-q-mean", "reciprocal-q-std",
            "patterson-pair-mean", "phase-coherence",
        ),
        "orbital_local": (
            "coordination-mean", "coordination-std", "coordination-entropy",
            "atomic-number-mismatch", "group-mismatch", "electronegativity-mismatch",
            "orbital-field-mean", "orbital-field-std",
        ),
        "electrostatic": (
            "ewald-pair-mean", "ewald-pair-absolute", "formal-potential-std",
            "charge-neutrality", "bond-valence-mean", "bond-valence-mismatch",
            "charge-equilibration-mean", "charge-equilibration-max",
        ),
        "local_density": (
            "soap-norm", "soap-entropy", "acsf-radial-mean", "acsf-radial-std",
            "acsf-angular-mean", "acsf-angular-std", "mbtr-inverse-distance",
            "local-density-cv",
        ),
        "periodic_graph": (
            "degree-mean", "degree-std", "algebraic-connectivity", "spectral-radius",
            "heat-trace-short", "heat-trace-long", "triangle-density", "rigidity-excess",
            "spectral-entropy",
        ),
        "canonical_topology": (
            "persistence-lifetime-mean", "persistence-lifetime-std",
            "persistence-lifetime-max", "pair-distance-entropy", "void-radius-mean",
            "void-radius-max", "minkowski-volume-fraction", "minkowski-interface-proxy",
        ),
        "thermodynamics": (
            "mixing-entropy", "mixing-gini", "electronegativity-mismatch", "radius-mismatch",
            "atomic-number-mismatch", "redox-imbalance", "redox-variance",
            "bond-mismatch-energy",
        ),
        "mechanics": (
            "polyhedral-bond-mean", "polyhedral-bond-std", "polyhedral-strain-mean",
            "polyhedral-strain-max", "bond-stiffness-mean", "bond-stiffness-std",
            "mass-density", "debye-proxy",
        ),
        "entropy_transport": (
            "radial-entropy-fine", "radial-entropy-medium", "radial-entropy-coarse",
            "entropy-scale-slope", "renyi-two", "species-distance-transport",
            "charge-entropy-coupling", "transport-density-coupling",
        ),
    }
)


@dataclass
class PrimitiveCache:
    root: Path | None = None

    def __post_init__(self) -> None:
        self._memory: dict[str, dict[str, float]] = {}
        self._canonical_memory: dict[int, tuple[Structure, Structure]] = {}
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)

    def _canonical(self, structure: Structure) -> Structure:
        identity = id(structure)
        cached = self._canonical_memory.get(identity)
        if cached is not None and cached[0] is structure:
            return cached[1]
        canonical = canonical_structure(structure)
        self._canonical_memory[identity] = (structure, canonical)
        return canonical

    def compute(
        self, kernel: str, structure: Structure, config: dict[str, Any] | None = None
    ) -> dict[str, float]:
        if kernel not in TRUSTED_KERNELS or kernel not in KERNELS:
            raise ValueError(f"unsupported trusted kernel: {kernel}")
        configuration = config or {}
        config_errors = validate_kernel_config(kernel, configuration)
        if config_errors:
            raise ValueError("; ".join(config_errors))
        canonical = self._canonical(structure)
        key_payload = {
            "kernel": kernel,
            "structure": structure_signature(canonical),
            "config": configuration,
        }
        key = hashlib.sha256(
            json.dumps(key_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if key in self._memory:
            return dict(self._memory[key])
        path = self.root / f"{key}.json" if self.root is not None else None
        if path is not None and path.exists():
            result = json.loads(path.read_text(encoding="utf-8"))
        else:
            result = KERNELS[kernel](canonical, configuration)
            if set(result) != set(KERNEL_OPERATIONS[kernel]):
                missing = set(KERNEL_OPERATIONS[kernel]) - set(result)
                extra = set(result) - set(KERNEL_OPERATIONS[kernel])
                raise RuntimeError(f"kernel operation mismatch; missing={missing}, extra={extra}")
            if path is not None:
                temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
                temporary.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
                os.replace(temporary, path)
        self._memory[key] = {name: float(value) for name, value in result.items()}
        return dict(self._memory[key])


def compute_kernel(
    kernel: str, structure: Structure, config: dict[str, Any] | None = None
) -> dict[str, float]:
    return PrimitiveCache().compute(kernel, structure, config)
