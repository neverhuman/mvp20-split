from __future__ import annotations

ELEMENTS = ("Al", "Ga", "In", "O")
CATIONS = ("Al", "Ga", "In")
PAIR_TYPES = (
    ("Al", "Al"),
    ("Al", "Ga"),
    ("Al", "In"),
    ("Al", "O"),
    ("Ga", "Ga"),
    ("Ga", "In"),
    ("Ga", "O"),
    ("In", "In"),
    ("In", "O"),
    ("O", "O"),
)
BRIDGE_TYPES = (
    ("Al", "Al"),
    ("Al", "Ga"),
    ("Al", "In"),
    ("Ga", "Ga"),
    ("Ga", "In"),
    ("In", "In"),
)

PAIR_PROFILE_STATS = ("min", "nn_mean", "nn_std", "q10", "q25", "median", "q75", "q90")
ANGLE_STATS = ("pair_count_mean", "mean", "std", "min", "max", "q10", "q25", "median", "q75", "q90")
POLYHEDRON_STATS = (
    "crystalnn_cn_mean",
    "crystalnn_cn_std",
    "voronoi_cn_mean",
    "voronoi_cn_std",
    "bond_length_mean",
    "bond_length_std",
    "bond_length_min",
    "bond_length_max",
    "bond_length_median",
    "bond_length_covalent_normalized_mean",
    "bond_length_distortion_mean",
    "quadratic_elongation_mean",
    "bond_valence_sum_mean",
    "formal_valence_abs_error_mean",
    "formal_valence_abs_error_max",
    "oxygen_hull_volume_mean",
)

CUTOFF_ANGSTROM = 8.0
WEIGHT_THRESHOLD = 0.1
SYMPRECS = (0.001, 0.01, 0.05, 0.1)

OXIDATION_STATES = {"Al": 3, "Ga": 3, "In": 3, "O": -2}
COVALENT_RADII_ANGSTROM = {"Al": 1.21, "Ga": 1.22, "In": 1.42, "O": 0.66}

FAMILY_COUNTS = {
    "pbc_pair_distance_profiles": 80,
    "partial_radial_distributions": 80,
    "directed_local_environments": 64,
    "metal_oxygen_polyhedra": 48,
    "bond_angle_geometry": 42,
    "lattice_reciprocal_invariants": 24,
    "symmetry_wyckoff_topology": 22,
}

TARGETS = ("formation_energy_ev_natom", "bandgap_energy_ev")
EPS = 1e-12
