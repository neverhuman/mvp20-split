from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .constants import (
    ANGLE_STATS,
    BRIDGE_TYPES,
    CATIONS,
    CUTOFF_ANGSTROM,
    ELEMENTS,
    FAMILY_COUNTS,
    PAIR_PROFILE_STATS,
    PAIR_TYPES,
    POLYHEDRON_STATS,
    SYMPRECS,
    WEIGHT_THRESHOLD,
)


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    family: str
    physical_family: str
    formula: str
    unit: str
    neighbors: str
    interpretation: str
    reserve: bool = False


PAIR_NEIGHBORS = (
    "All source-to-periodic-target images at 0 < r <= 8 Å from pymatgen's "
    "lattice-sphere enumeration; the zero self-image is excluded."
)
VORONOI_NEIGHBORS = (
    "Periodic Voronoi neighbors whose solid-angle weight, normalized to the largest "
    "face at that center, is at least 0.1."
)
CRYSTALNN_NEIGHBORS = (
    "Periodic CrystalNN M-O edges with weighted-CN probability at least 0.1, using "
    "explicit Al3+, Ga3+, In3+, and O2- oxidation states."
)


def _definition(
    name: str,
    family: str,
    formula: str,
    unit: str,
    neighbors: str,
    interpretation: str,
    *,
    reserve: bool = False,
) -> FeatureDefinition:
    return FeatureDefinition(
        name, family, family, formula, unit, neighbors, interpretation, reserve
    )


def build_primary_definitions() -> list[FeatureDefinition]:
    definitions: list[FeatureDefinition] = []

    quantile_formula = {
        "q10": "Q_0.10({r_ij,n})",
        "q25": "Q_0.25({r_ij,n})",
        "median": "Q_0.50({r_ij,n})",
        "q75": "Q_0.75({r_ij,n})",
        "q90": "Q_0.90({r_ij,n})",
    }
    for source, target in PAIR_TYPES:
        pair = f"{source}_{target}"
        for stat in PAIR_PROFILE_STATS:
            name = f"c360_pair_{pair}_{stat}"
            if stat == "min":
                formula = "min_{i in source,j,n}(r_ij,n)"
                meaning = "Shortest periodic separation for this element pair."
            elif stat == "nn_mean":
                formula = "mean_i(min_{j,n} r_ij,n)"
                meaning = "Mean nearest-target distance over source atoms."
            elif stat == "nn_std":
                formula = "std_i(min_{j,n} r_ij,n), population standard deviation"
                meaning = "Heterogeneity of nearest-target distances over source atoms."
            else:
                formula = quantile_formula[stat]
                meaning = f"{stat} of the periodic pair-distance population."
            definitions.append(
                _definition(
                    name,
                    "pbc_pair_distance_profiles",
                    formula,
                    "angstrom",
                    PAIR_NEIGHBORS,
                    meaning,
                )
            )

    for source, target in PAIR_TYPES:
        pair = f"{source}_{target}"
        for shell in range(1, 9):
            definitions.append(
                _definition(
                    f"c360_rdf_{pair}_shell_{shell}",
                    "partial_radial_distributions",
                    "N_shell / (N_source * (N_target/V) * (4*pi/3)*(r_hi^3-r_lo^3))",
                    "dimensionless",
                    PAIR_NEIGHBORS
                    + " Shell edges are pair-specific training-distance quantiles frozen in the schema.",
                    f"Partial radial population relative to a uniform target density in shell {shell}.",
                )
            )

    for source in ELEMENTS:
        for target in ELEMENTS:
            stem = f"c360_env_{source}_to_{target}"
            definitions.extend(
                [
                    _definition(
                        f"{stem}_nn_distance_mean",
                        "directed_local_environments",
                        "mean_i(min_{j,n; nonzero} r_ij,n)",
                        "angstrom",
                        "Exact closest periodic target for every source; the zero self-image is excluded.",
                        "Mean first-target separation in the directed chemical environment.",
                    ),
                    _definition(
                        f"{stem}_nn_distance_std",
                        "directed_local_environments",
                        "std_i(min_{j,n; nonzero} r_ij,n), population standard deviation",
                        "angstrom",
                        "Exact closest periodic target for every source; the zero self-image is excluded.",
                        "Site-to-site variation of the directed first-target separation.",
                    ),
                    _definition(
                        f"{stem}_voronoi_count_mean",
                        "directed_local_environments",
                        "mean_i(sum_j 1[element_j=target and w_ij>=0.1])",
                        "count",
                        VORONOI_NEIGHBORS,
                        "Mean number of robust Voronoi contacts to the target element.",
                    ),
                    _definition(
                        f"{stem}_voronoi_count_std",
                        "directed_local_environments",
                        "std_i(sum_j 1[element_j=target and w_ij>=0.1])",
                        "count",
                        VORONOI_NEIGHBORS,
                        "Heterogeneity of robust target-specific Voronoi coordination.",
                    ),
                ]
            )

    poly_formula = {
        "crystalnn_cn_mean": "mean_M(sum_{M-O edges} w_MO)",
        "crystalnn_cn_std": "std_M(sum_{M-O edges} w_MO)",
        "voronoi_cn_mean": "mean_M(N_Voronoi,O)",
        "voronoi_cn_std": "std_M(N_Voronoi,O)",
        "bond_length_mean": "mean_{M-O edges}(r_MO)",
        "bond_length_std": "std_{M-O edges}(r_MO)",
        "bond_length_min": "min_{M-O edges}(r_MO)",
        "bond_length_max": "max_{M-O edges}(r_MO)",
        "bond_length_median": "median_{M-O edges}(r_MO)",
        "bond_length_covalent_normalized_mean": "mean(r_MO/(R_cov,M+R_cov,O))",
        "bond_length_distortion_mean": "mean_M(mean_b(|r_b-mean_M(r)|/mean_M(r)))",
        "quadratic_elongation_mean": "mean_M(mean_b((r_b/mean_M(r))^2))",
        "bond_valence_sum_mean": "mean_M(sum_j exp((R_Mj-r_Mj)/0.31))",
        "formal_valence_abs_error_mean": "mean_M(|BVS_M-3|)",
        "formal_valence_abs_error_max": "max_M(|BVS_M-3|)",
        "oxygen_hull_volume_mean": "mean_M(volume(convex_hull(unwrapped O-neighbor coordinates)))",
    }
    poly_units = {
        "crystalnn_cn_mean": "effective_count",
        "crystalnn_cn_std": "effective_count",
        "voronoi_cn_mean": "count",
        "voronoi_cn_std": "count",
        "bond_length_mean": "angstrom",
        "bond_length_std": "angstrom",
        "bond_length_min": "angstrom",
        "bond_length_max": "angstrom",
        "bond_length_median": "angstrom",
        "bond_length_covalent_normalized_mean": "dimensionless",
        "bond_length_distortion_mean": "dimensionless",
        "quadratic_elongation_mean": "dimensionless",
        "bond_valence_sum_mean": "valence_units",
        "formal_valence_abs_error_mean": "valence_units",
        "formal_valence_abs_error_max": "valence_units",
        "oxygen_hull_volume_mean": "angstrom^3",
    }
    for metal in CATIONS:
        for stat in POLYHEDRON_STATS:
            neighbor_rule = VORONOI_NEIGHBORS if stat.startswith("voronoi") else CRYSTALNN_NEIGHBORS
            if "bond_valence" in stat or "formal_valence" in stat:
                neighbor_rule = "All unlike-element periodic neighbors within 4 Å; Brese-O'Keeffe bond-valence parameters."
            definitions.append(
                _definition(
                    f"c360_poly_{metal}_O_{stat}",
                    "metal_oxygen_polyhedra",
                    poly_formula[stat],
                    poly_units[stat],
                    neighbor_rule,
                    f"{metal}-oxygen local coordination or polyhedral distortion descriptor.",
                )
            )

    angle_formula = {
        "pair_count_mean": "mean_M(n_O(M)*(n_O(M)-1)/2)",
        "mean": "mean(theta_O-M-O)",
        "std": "std(theta_O-M-O)",
        "min": "min(theta_O-M-O)",
        "max": "max(theta_O-M-O)",
        "q10": "Q_0.10(theta_O-M-O)",
        "q25": "Q_0.25(theta_O-M-O)",
        "median": "Q_0.50(theta_O-M-O)",
        "q75": "Q_0.75(theta_O-M-O)",
        "q90": "Q_0.90(theta_O-M-O)",
    }
    for metal in CATIONS:
        for stat in ANGLE_STATS:
            definitions.append(
                _definition(
                    f"c360_angle_O_{metal}_O_{stat}",
                    "bond_angle_geometry",
                    angle_formula[stat],
                    "count" if stat == "pair_count_mean" else "degree",
                    CRYSTALNN_NEIGHBORS,
                    f"Distributional geometry of O-{metal}-O neighbor pairs.",
                )
            )
    for left, right in BRIDGE_TYPES:
        for stat in ("mean", "std"):
            definitions.append(
                _definition(
                    f"c360_angle_{left}_O_{right}_{stat}",
                    "bond_angle_geometry",
                    f"{stat}(theta_{left}-O-{right})",
                    "degree",
                    CRYSTALNN_NEIGHBORS
                    + " Edges are reversed and unwrapped about the shared oxygen.",
                    f"{stat} opening angle of {left}-O-{right} cation bridges.",
                )
            )

    lattice_specs = [
        ("face_area_min", "min(|bxc|,|cxa|,|axb|)", "angstrom^2", "Smallest cell face area."),
        ("face_area_mid", "median(|bxc|,|cxa|,|axb|)", "angstrom^2", "Middle cell face area."),
        ("face_area_max", "max(|bxc|,|cxa|,|axb|)", "angstrom^2", "Largest cell face area."),
        ("surface_area", "2*(|bxc|+|cxa|+|axb|)", "angstrom^2", "Parallelepiped surface area."),
        ("surface_volume_ratio", "surface_area/V", "angstrom^-1", "Surface-to-volume scale."),
        (
            "sphericity",
            "pi^(1/3)*(6V)^(2/3)/surface_area",
            "dimensionless",
            "Compactness relative to a sphere.",
        ),
        (
            "height_min",
            "min(V/|bxc|,V/|cxa|,V/|axb|)",
            "angstrom",
            "Smallest perpendicular cell height.",
        ),
        (
            "height_max",
            "max(V/|bxc|,V/|cxa|,V/|axb|)",
            "angstrom",
            "Largest perpendicular cell height.",
        ),
        (
            "height_anisotropy",
            "(height_max-height_min)/mean(heights)",
            "dimensionless",
            "Spread of perpendicular cell heights.",
        ),
        (
            "reciprocal_length_min",
            "min(|a*|,|b*|,|c*|)",
            "angstrom^-1",
            "Smallest crystallographic reciprocal length.",
        ),
        (
            "reciprocal_length_mid",
            "median(|a*|,|b*|,|c*|)",
            "angstrom^-1",
            "Middle crystallographic reciprocal length.",
        ),
        (
            "reciprocal_length_max",
            "max(|a*|,|b*|,|c*|)",
            "angstrom^-1",
            "Largest crystallographic reciprocal length.",
        ),
        (
            "reciprocal_anisotropy",
            "reciprocal_length_max/reciprocal_length_min",
            "dimensionless",
            "Reciprocal-axis aspect ratio.",
        ),
        (
            "reciprocal_volume",
            "|det([a*,b*,c*])|=1/V",
            "angstrom^-3",
            "Volume of the crystallographic reciprocal cell.",
        ),
        (
            "metric_eigenvalue_min",
            "min(eig(G))/V^(2/3)",
            "dimensionless",
            "Smallest volume-normalized squared principal cell scale.",
        ),
        (
            "metric_eigenvalue_mid",
            "median(eig(G))/V^(2/3)",
            "dimensionless",
            "Middle volume-normalized squared principal cell scale.",
        ),
        (
            "metric_eigenvalue_max",
            "max(eig(G))/V^(2/3)",
            "dimensionless",
            "Largest volume-normalized squared principal cell scale.",
        ),
        (
            "metric_condition_number",
            "lambda_max(G)/lambda_min(G)",
            "dimensionless",
            "Metric-tensor conditioning and shape elongation.",
        ),
        (
            "metric_eigenvalue_entropy",
            "-sum p_i ln(p_i), p_i=lambda_i/sum(lambda)",
            "nat",
            "Entropy of principal metric scales.",
        ),
        (
            "metric_frobenius_anisotropy",
            "||G-(tr(G)/3)I||_F/tr(G)",
            "dimensionless",
            "Rotation-invariant metric departure from isotropy.",
        ),
    ]
    for rank in range(1, 5):
        lattice_specs.append(
            (
                f"d_spacing_{rank}_normalized",
                f"{rank}th largest unique d_hkl/V^(1/3), h,k,l in [-3,3], not all zero",
                "dimensionless",
                f"Normalized {rank}th largest unique low-index interplanar spacing.",
            )
        )
    for name, formula, unit, meaning in lattice_specs:
        definitions.append(
            _definition(
                f"c360_lattice_{name}",
                "lattice_reciprocal_invariants",
                formula,
                unit,
                "Computed from the Niggli-reduced lattice; no atomic neighbors are used.",
                meaning,
            )
        )

    sym_names = (
        (
            "operation_count",
            "N_symmetry_operations",
            "count",
            "Magnitude of detected crystallographic symmetry.",
        ),
        (
            "orbit_count",
            "N_unique(equivalent_atoms)",
            "count",
            "Number of occupied equivalent-site orbits.",
        ),
        (
            "primitive_site_count",
            "N_sites(spglib primitive cell)",
            "count",
            "Atoms in the detected primitive cell.",
        ),
        (
            "primitive_conventional_volume_ratio",
            "V_primitive/V_conventional",
            "dimensionless",
            "Primitive fraction of the conventional cell.",
        ),
        (
            "wyckoff_letter_count",
            "N_unique(occupied Wyckoff letters)",
            "count",
            "Diversity of occupied Wyckoff letters.",
        ),
        (
            "largest_orbit_fraction",
            "max_k(N_orbit,k)/N_sites",
            "fraction",
            "Fraction of atoms in the largest occupied orbit.",
        ),
        (
            "general_position_site_fraction",
            "N_sites(site_symmetry=1)/N_sites",
            "fraction",
            "Fraction of atoms on general positions.",
        ),
    )
    for symprec in (0.01, 0.1):
        label = str(symprec).replace(".", "p")
        for name, formula, unit, meaning in sym_names:
            definitions.append(
                _definition(
                    f"c360_sym_s{label}_{name}",
                    "symmetry_wyckoff_topology",
                    formula,
                    unit,
                    f"spglib symmetry dataset with symprec={symprec} Å and angle_tolerance=-1.",
                    meaning,
                )
            )
    cross_sym = [
        (
            "spacegroup_distinct_count",
            "N_unique(SG(symprec))",
            "count",
            "Tolerance sensitivity of the detected space group.",
        ),
        (
            "spacegroup_modal_fraction",
            "max_s count(SG=s)/4",
            "fraction",
            "Stability of the modal detected space group.",
        ),
        (
            "supplied_spacegroup_match_count",
            "sum 1[SG(symprec)=SG_supplied]",
            "count",
            "Agreement with the supplied space-group label.",
        ),
        (
            "operation_count_cv",
            "std(N_ops)/mean(N_ops)",
            "dimensionless",
            "Relative tolerance sensitivity of symmetry magnitude.",
        ),
        (
            "orbit_count_range",
            "max(N_orbits)-min(N_orbits)",
            "count",
            "Tolerance sensitivity of orbit splitting.",
        ),
        (
            "wyckoff_orbit_entropy_total",
            "-sum_k p_k ln(p_k), all sites",
            "nat",
            "Entropy of all occupied 0.01 Å orbits.",
        ),
        (
            "wyckoff_orbit_entropy_cation",
            "-sum_k p_k ln(p_k), cation sites",
            "nat",
            "Entropy of occupied cation orbits at 0.01 Å.",
        ),
        (
            "wyckoff_orbit_entropy_oxygen",
            "-sum_k p_k ln(p_k), oxygen sites",
            "nat",
            "Entropy of occupied oxygen orbits at 0.01 Å.",
        ),
    ]
    for name, formula, unit, meaning in cross_sym:
        definitions.append(
            _definition(
                f"c360_sym_{name}",
                "symmetry_wyckoff_topology",
                formula,
                unit,
                f"spglib datasets across symprec={list(SYMPRECS)} Å; entropies use 0.01 Å.",
                meaning,
            )
        )

    if len(definitions) != 360:
        raise AssertionError(f"Primary schema has {len(definitions)} features, expected 360")
    counts: dict[str, int] = {}
    for definition in definitions:
        counts[definition.family] = counts.get(definition.family, 0) + 1
    if counts != FAMILY_COUNTS:
        raise AssertionError(f"Feature family counts drifted: {counts}")
    return definitions


def build_reserve_definitions() -> list[FeatureDefinition]:
    definitions: list[FeatureDefinition] = []
    for source, target in PAIR_TYPES:
        for stat, quantile in (("q05", "0.05"), ("q95", "0.95")):
            definitions.append(
                _definition(
                    f"c360_reserve_pair_{source}_{target}_{stat}",
                    "pbc_pair_distance_profiles",
                    f"Q_{quantile}({{r_ij,n}})",
                    "angstrom",
                    PAIR_NEIGHBORS,
                    f"Reserve {stat} periodic separation for the element pair.",
                    reserve=True,
                )
            )
    for source in ELEMENTS:
        for target in ELEMENTS:
            for stat in ("mean", "std"):
                definitions.append(
                    _definition(
                        f"c360_reserve_env_{source}_to_{target}_second_nn_{stat}",
                        "directed_local_environments",
                        f"{stat}_i(second-min_{{j,n; nonzero}} r_ij,n)",
                        "angstrom",
                        "Second closest distinct periodic target image for every source; zero self-image excluded.",
                        "Reserve second-shell distance moment.",
                        reserve=True,
                    )
                )
    for metal in CATIONS:
        for stat, formula in (
            ("iqr", "Q_0.75(theta)-Q_0.25(theta)"),
            ("skewness", "mean((theta-mean(theta))^3)/std(theta)^3"),
        ):
            definitions.append(
                _definition(
                    f"c360_reserve_angle_O_{metal}_O_{stat}",
                    "bond_angle_geometry",
                    formula,
                    "degree" if stat == "iqr" else "dimensionless",
                    CRYSTALNN_NEIGHBORS,
                    f"Reserve O-{metal}-O angle {stat}.",
                    reserve=True,
                )
            )
    for rank in range(5, 13):
        definitions.append(
            _definition(
                f"c360_reserve_lattice_d_spacing_{rank}_normalized",
                "lattice_reciprocal_invariants",
                f"{rank}th largest unique d_hkl/V^(1/3), h,k,l in [-3,3], not all zero",
                "dimensionless",
                "Computed from the Niggli-reduced lattice; no atomic neighbors are used.",
                f"Reserve normalized low-index d-spacing rank {rank}.",
                reserve=True,
            )
        )
    return definitions


@dataclass
class Crystal360Schema:
    shell_boundaries_angstrom: dict[str, list[float]]
    selected_features: list[FeatureDefinition]
    replacements: list[dict[str, str]]
    training_source: dict[str, Any]
    version: str = "1.0.0"

    @property
    def columns(self) -> list[str]:
        return [feature.name for feature in self.selected_features]

    def validate(self) -> None:
        if len(self.selected_features) != 360 or len(set(self.columns)) != 360:
            raise ValueError("Crystal360 schema must contain exactly 360 unique selected features")
        expected_pairs = {f"{left}-{right}" for left, right in PAIR_TYPES}
        if set(self.shell_boundaries_angstrom) != expected_pairs:
            raise ValueError("Schema radial-shell pair set is incomplete")
        for pair, edges in self.shell_boundaries_angstrom.items():
            if len(edges) != 9 or edges[0] != 0.0 or edges[-1] != CUTOFF_ANGSTROM:
                raise ValueError(f"Invalid radial-shell edges for {pair}: {edges}")
            if any(right < left for left, right in zip(edges, edges[1:])):
                raise ValueError(f"Non-monotonic radial-shell edges for {pair}: {edges}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        primary = build_primary_definitions()
        reserve = build_reserve_definitions()
        return {
            "schema_name": "Nomad Crystal360",
            "schema_version": self.version,
            "feature_count": 360,
            "cutoff_angstrom": CUTOFF_ANGSTROM,
            "neighbor_weight_threshold": WEIGHT_THRESHOLD,
            "family_counts_requested": FAMILY_COUNTS,
            "shell_fit": {
                "training_only": True,
                "labels_used": False,
                "quantiles": [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0],
                "boundaries_angstrom": self.shell_boundaries_angstrom,
            },
            "selected_columns": self.columns,
            "selected_features": [asdict(item) for item in self.selected_features],
            "primary_features": [asdict(item) for item in primary],
            "reserve_bank": [asdict(item) for item in reserve],
            "replacements": self.replacements,
            "training_source": self.training_source,
            "excluded_descriptor_classes": [
                "SOAP",
                "MBTR",
                "PCA components",
                "neural embeddings",
                "opaque learned coefficients",
            ],
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Crystal360Schema":
        payload = json.loads(path.read_text(encoding="utf-8"))
        schema = cls(
            shell_boundaries_angstrom=payload["shell_fit"]["boundaries_angstrom"],
            selected_features=[FeatureDefinition(**item) for item in payload["selected_features"]],
            replacements=payload.get("replacements", []),
            training_source=payload.get("training_source", {}),
            version=payload["schema_version"],
        )
        schema.validate()
        return schema
