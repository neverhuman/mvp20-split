from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Domain:
    id: str
    title: str
    research_queries: tuple[str, ...]


DOMAINS: tuple[Domain, ...] = (
    Domain(
        "D01",
        "Space groups, Wyckoff structure, and group-theoretic invariants",
        ("crystal Wyckoff descriptors machine learning", "space group invariants materials"),
    ),
    Domain(
        "D02",
        "Reciprocal-space, diffraction, Fourier, and Patterson descriptors",
        ("diffraction descriptors crystal machine learning", "Patterson function descriptors"),
    ),
    Domain(
        "D03",
        "Tight-binding, orbital, electronic-structure, and bandgap proxies",
        ("tight binding descriptors band gap", "orbital field matrix crystal descriptors"),
    ),
    Domain(
        "D04",
        "Ewald electrostatics, multipoles, bond valence, and charge equilibration",
        ("Ewald energy descriptor machine learning", "bond valence charge equilibration crystal"),
    ),
    Domain(
        "D05",
        "SOAP/ACE/bispectrum, ACSF, MBTR, and local density bases",
        ("SOAP ACE MBTR crystal descriptors", "DScribe atomistic descriptors"),
    ),
    Domain(
        "D06",
        "Periodic graph spectra, walks, centrality, motifs, and rigidity",
        ("periodic crystal graph spectral descriptors", "rigidity motifs materials graph"),
    ),
    Domain(
        "D07",
        "Persistent homology, alpha complexes, void topology, and Minkowski measures",
        ("persistent homology crystal descriptor", "alpha complex void topology materials"),
    ),
    Domain(
        "D08",
        "Mixing thermodynamics, disorder, redox, and formation-energy proxies",
        ("mixing enthalpy disorder descriptors", "redox formation energy proxy crystal"),
    ),
    Domain(
        "D09",
        "Strain, elasticity, phonon, Debye, and lattice-mechanics proxies",
        ("elastic phonon Debye descriptors machine learning", "lattice strain crystal features"),
    ),
    Domain(
        "D10",
        "Multiscale information theory, optimal transport, renormalization, and cross-family couplings",
        ("optimal transport atomistic descriptor", "multiscale information crystal descriptor"),
    ),
)

THEORIST_KINDS = (
    "literature_translator",
    "first_principles_derivation",
    "multiscale_expansion",
    "cross_domain_inventor",
)
ANALYST_KINDS = (
    "screening_design",
    "invariance_and_falsification",
    "redundancy_and_statistics",
    "compute_and_reproducibility",
)
JUDGE_KINDS = (
    "physics",
    "novelty",
    "leakage_and_reproducibility",
    "statistical_value",
)

EXPECTED_JNOCCIO_ROLES = 70
EXPECTED_JAILGUN_TABS = 10
EXPECTED_JAILGUN_CONCEPTS = 500
MIN_ATTEMPTED_FEATURES = 1_500
MIN_VALIDATED_FEATURES = 1_000
MIN_VALIDATED_PER_DOMAIN = 50
MAX_COLUMNS_PER_BASE_EQUATION = 25
JNOCCIO_WORKERS = 20
MAX_RETRIES = 1
MAX_WALL_SECONDS = 48 * 60 * 60
MAX_COST_USD = 500.0
TRAIN_ROWS = 2_400
TEST_ROWS = 600
ATLAS_WIDTH = 9_969
TARGETS = ("formation_energy_ev_natom", "bandgap_energy_ev")
ATLAS_TARGET_WINNERS = {
    "formation_energy_ev_natom": 0.023375280001922384,
    "bandgap_energy_ev": 0.07769090852969567,
}
EXISTING_809_CONTROLS = {
    "formation_energy_ev_natom": 0.02417652672341617,
    "bandgap_energy_ev": 0.07906483437846143,
}
ATLAS_WINNER_MEAN = 0.05053309
EXISTING_809_MEAN = 0.05162068
SCREEN_SEEDS = (1701, 2909, 4219)
FOLD_SEED = 4219
SCREEN_TREES = 150
CONFIRM_TREES = 400

DEFAULT_INBOX_ROOT = Path(
    "/home/ubuntu/nomad/artifacts/nomad_theory_feature_hunt/inbox"
)
DEFAULT_NOMAD_ROOT = Path("/home/ubuntu/nomad")
ARTIFACT_DIRS = (
    "seed_evidence",
    "jailgun/raw",
    "jailgun/normalized",
    "research",
    "theories",
    "generators",
    "microfeature_matrices",
    "sandbox_receipts",
    "judgments",
    "promoted_features",
    "negative_memory",
    "final_hashes",
    "queue/results",
    "queue/jobs",
    "receipts/jnoccio",
    "receipts/jailgun",
    "scoring",
)


def role_specs() -> list[dict[str, str | int]]:
    roles: list[dict[str, str | int]] = []
    for domain in DOMAINS:
        roles.append(
            {
                "id": f"scout-{domain.id.lower()}",
                "class": "literature_scout",
                "domain": domain.id,
                "title": domain.title,
                "wave": 1,
            }
        )
    for domain in DOMAINS:
        for kind in THEORIST_KINDS:
            roles.append(
                {
                    "id": f"theorist-{domain.id.lower()}-{kind.replace('_', '-')}",
                    "class": "theorist",
                    "specialty": kind,
                    "domain": domain.id,
                    "title": domain.title,
                    "wave": 2,
                }
            )
    for domain in DOMAINS:
        roles.append(
            {
                "id": f"implementer-{domain.id.lower()}",
                "class": "feature_implementer",
                "domain": domain.id,
                "title": domain.title,
                "wave": 3,
            }
        )
    for kind in ANALYST_KINDS:
        roles.append(
            {
                "id": f"analyst-{kind.replace('_', '-')}",
                "class": "experimental_analyst",
                "specialty": kind,
                "domain": "ALL",
                "title": "cross-domain experimental analysis",
                "wave": 4,
            }
        )
    for kind in JUDGE_KINDS:
        roles.append(
            {
                "id": f"judge-{kind.replace('_', '-')}",
                "class": "blind_judge",
                "specialty": kind,
                "domain": "ALL",
                "title": "blind campaign judgment",
                "wave": 5,
            }
        )
    for index in range(1, 3):
        roles.append(
            {
                "id": f"memory-curator-{index:02d}",
                "class": "memory_curator",
                "domain": "ALL",
                "title": "negative and positive memory curation",
                "wave": 6,
            }
        )
    if len(roles) != EXPECTED_JNOCCIO_ROLES or len({r["id"] for r in roles}) != len(roles):
        raise AssertionError("role construction must produce exactly 70 distinct identities")
    return roles
