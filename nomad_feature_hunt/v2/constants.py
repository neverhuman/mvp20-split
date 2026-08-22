from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


CAMPAIGN_VERSION = "2.0"
CAMPAIGN_PHASES = (
    "evidence",
    "design",
    "compilation",
    "execution",
    "discovery",
    "adaptive",
    "confirmation",
    "judging",
)


@dataclass(frozen=True)
class Domain:
    id: str
    slug: str
    title: str


DOMAINS: tuple[Domain, ...] = (
    Domain("D01", "symmetry", "Symmetry, Wyckoff orbits, and site symmetry"),
    Domain("D02", "reciprocal", "Structure factors and Patterson summaries"),
    Domain("D03", "orbital", "Orbital-conditioned local environments"),
    Domain("D04", "electrostatic", "Electrostatics, bond valence, and charge equilibration"),
    Domain("D05", "local-density", "SOAP, ACSF, MBTR, and local-density pooling"),
    Domain("D06", "graph", "Periodic graphs, spectra, motifs, and rigidity"),
    Domain("D07", "topology", "Persistent topology, voids, and Minkowski summaries"),
    Domain("D08", "thermodynamics", "Mixing, redox, and bond-mismatch thermodynamics"),
    Domain("D09", "mechanics", "Polyhedral strain, stiffness, density, and Debye proxies"),
    Domain("D10", "entropy-ot", "Multiscale entropy, transport, and physical couplings"),
)
DOMAIN_IDS = frozenset(domain.id for domain in DOMAINS)

TRUSTED_KERNELS = (
    "symmetry",
    "reciprocal",
    "orbital_local",
    "electrostatic",
    "local_density",
    "periodic_graph",
    "canonical_topology",
    "thermodynamics",
    "mechanics",
    "entropy_transport",
)
DOMAIN_KERNELS = {
    domain.id: kernel for domain, kernel in zip(DOMAINS, TRUSTED_KERNELS, strict=True)
}

TARGETS = ("formation_energy_ev_natom", "bandgap_energy_ev")
ATLAS_TARGET_WINNERS = {
    "formation_energy_ev_natom": 0.023375280001922384,
    "bandgap_energy_ev": 0.07769090852969567,
}
EXISTING_809_CONTROLS = {
    "formation_energy_ev_natom": 0.02417652672341617,
    "bandgap_energy_ev": 0.07906483437846143,
}

EXPECTED_JNOCCIO_ROLES = 180
EXPECTED_CANARY_ROLES = 10
EXPECTED_JAILGUN_TABS = 10
JNOCCIO_WORKERS = 20
MAX_ATTEMPTS_PER_ROLE = 2
MAX_JNOCCIO_ATTEMPTS = 360

PROMPT_LIMIT_BYTES = 12 * 1024
OUTPUT_LIMIT_BYTES = 20 * 1024
PLUGIN_LIMIT_BYTES = 20 * 1024
MAX_EVIDENCE_SOURCES_PER_PROMPT = 10
MIN_SPEC_OUTPUTS = 8
MAX_SPEC_OUTPUTS = 25
MAX_COLUMNS_PER_BASE_EQUATION = 25
CUSTOM_PLUGIN_OUTPUTS = tuple(f"custom-output-{index:02d}" for index in range(1, 26))

TRAIN_ROWS = 2_400
TEST_ROWS = 600
ATLAS_WIDTH = 9_969
ATLAS_DEFINITION_COUNT = 9_160
EXISTING_WIDTH = 809

MIN_RELEVANT_SOURCES = 250
MIN_SOURCES_PER_DOMAIN = 20
MIN_ATTEMPTED_FEATURES = 4_000
MIN_VALIDATED_FEATURES = 2_500
MIN_VALIDATED_PER_DOMAIN = 150
MIN_BASE_FAMILIES = 120
MIN_POSITIVE_FAMILIES_PER_TARGET = 10
MIN_POSITIVE_DOMAINS_PER_TARGET = 3

SCREEN_SEEDS = (1701, 2909, 4219)
DISCOVERY_FOLDS = 2
SCREEN_TREES = 150
CONFIRMATION_FOLDS = 5
CONFIRM_TREES = 400
MAX_CONFIRMATION_VIEWS_PER_TARGET = 8
TIE_BAND = 0.0001
STRETCH_LIFT = 0.0005

MAX_WALL_SECONDS = 72 * 60 * 60
MAX_COST_USD = 1_000.0
RESEARCH_RESERVE_USD = 50.0
JNOCCIO_MIN_DEBIT_USD = 2.5
JAILGUN_MIN_DEBIT_USD = 5.0

DEFAULT_NOMAD_ROOT = Path("/home/ubuntu/nomad")
DEFAULT_INBOX_ROOT = Path(
    "/home/ubuntu/nomad/artifacts/nomad_theory_feature_hunt/v2/inbox"
)

ARTIFACT_DIRS = (
    "inputs/atlas",
    "inputs/controller",
    "inputs/public",
    "evidence/raw",
    "evidence/claim_packs",
    "novelty",
    "memory/v1_seeds",
    "memory/negative",
    "prompts",
    "queue/jobs",
    "queue/results",
    "leases",
    "receipts/jnoccio",
    "receipts/jailgun",
    "receipts/sandbox",
    "families",
    "specs",
    "plugins",
    "registry",
    "cache/primitives",
    "matrices/temporary",
    "matrices/validated",
    "scoring/discovery",
    "scoring/confirmation",
    "judgments",
    "promotion",
    "final_hashes",
)

ARCHITECT_SPECIALTIES = (
    "physics",
    "literature-translation",
    "residual-gap",
    "cross-domain-invention",
)
ANALYST_SPECIALTIES = (
    "screening-design",
    "invariance-falsification",
    "redundancy-statistics",
    "compute-reproducibility",
)
JUDGE_SPECIALTIES = (
    "physics",
    "novelty",
    "leakage-reproducibility",
    "statistical-value",
)


def role_specs() -> list[dict[str, Any]]:
    """Return the immutable, exactly-180-role Jnoccio roster."""

    roles: list[dict[str, Any]] = []
    for index, domain in enumerate(DOMAINS, start=1):
        roles.append(
            {
                "id": f"curator-{domain.id.lower()}",
                "class": "evidence_curator",
                "domain": domain.id,
                "wave": 1,
                "canary": True,
                "ordinal": index,
            }
        )
    for domain in DOMAINS:
        for specialty in ARCHITECT_SPECIALTIES:
            roles.append(
                {
                    "id": f"architect-{domain.id.lower()}-{specialty}",
                    "class": "family_architect",
                    "domain": domain.id,
                    "specialty": specialty,
                    "wave": 2,
                }
            )
    for domain in DOMAINS:
        for index in range(1, 9):
            roles.append(
                {
                    "id": f"spec-builder-{domain.id.lower()}-{index:02d}",
                    "class": "spec_builder",
                    "domain": domain.id,
                    "wave": 3,
                }
            )
    for domain in DOMAINS:
        for index in range(1, 3):
            roles.append(
                {
                    "id": f"plugin-writer-{domain.id.lower()}-{index:02d}",
                    "class": "plugin_writer",
                    "domain": domain.id,
                    "wave": 4,
                }
            )
    for target_index, target in enumerate(TARGETS):
        for index in range(1, 6):
            roles.append(
                {
                    "id": f"exploiter-{target_index + 1}-{index:02d}",
                    "class": "target_exploiter",
                    "domain": "ALL",
                    "target": target,
                    "wave": 5,
                    "requires": "discovery",
                }
            )
    for index in range(1, 11):
        roles.append(
            {
                "id": f"synthesizer-{index:02d}",
                "class": "cross_family_synthesizer",
                "domain": "ALL",
                "wave": 5,
                "requires": "discovery",
            }
        )
    for specialty in ANALYST_SPECIALTIES:
        roles.append(
            {
                "id": f"analyst-{specialty}",
                "class": "experimental_analyst",
                "domain": "ALL",
                "specialty": specialty,
                "wave": 6,
                "requires": "matrix_and_score_receipts",
            }
        )
    for specialty in JUDGE_SPECIALTIES:
        roles.append(
            {
                "id": f"judge-{specialty}",
                "class": "blind_judge",
                "domain": "ALL",
                "specialty": specialty,
                "wave": 7,
                "requires": "matrix_and_score_receipts",
            }
        )
    for index in range(1, 3):
        roles.append(
            {
                "id": f"memory-curator-{index:02d}",
                "class": "memory_curator",
                "domain": "ALL",
                "wave": 8,
                "requires": "receipt_ids",
            }
        )
    if len(roles) != EXPECTED_JNOCCIO_ROLES:
        raise AssertionError(f"role construction produced {len(roles)}, expected 180")
    if len({role["id"] for role in roles}) != len(roles):
        raise AssertionError("role identities must be unique")
    return roles
