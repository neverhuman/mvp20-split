from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from nomad_crystal360.io import load_structures
from nomad_crystal360.artifacts import geometry_tree_hash

from nomad_feature_hunt.ledger import HashChain, atomic_json, sha256_bytes, sha256_file, utc_now

from .budget import BudgetAccount, BudgetError
from .compiler import TrustedCompiler
from .constants import (
    ARTIFACT_DIRS,
    ATLAS_WIDTH,
    CAMPAIGN_PHASES,
    CUSTOM_PLUGIN_OUTPUTS,
    DEFAULT_INBOX_ROOT,
    DEFAULT_NOMAD_ROOT,
    DOMAINS,
    JNOCCIO_WORKERS,
    MAX_ATTEMPTS_PER_ROLE,
    MAX_WALL_SECONDS,
    OUTPUT_LIMIT_BYTES,
    TARGETS,
    TRAIN_ROWS,
    TEST_ROWS,
    TRUSTED_KERNELS,
    role_specs,
)
from .evidence import (
    build_claim_pack,
    citation_registry,
    deduplicate_sources,
    import_v1_memory,
    validate_evidence_coverage,
)
from .novelty import numeric_signature, seed_atlas_registry, stage_frozen_atlas
from .execution import deterministic_real_sample, quarantine_columns, run_invariance_tests
from .kernels import KERNEL_OPERATIONS, PrimitiveCache, compute_kernel
from .prompts import build_retry_prompt, build_role_prompt
from .schemas import (
    SchemaError,
    expand_feature_spec,
    parse_strict_json,
    validate_role_payload,
)
from .security import (
    plugin_full_execution_command,
    plugin_sandbox_command,
    static_check_plugin,
)
from .scoring import (
    FamilyCandidate,
    build_confirmation_preregistration,
    categorical_discovery_feedback,
    public_adaptive_packet,
    score_confirmation,
    score_discovery,
    validate_confirmation_views,
)
from .state import (
    CampaignDB,
    mark_batch_submitted,
    prepare_job_batch,
    record_attempt_result,
)
from .verification import verify_campaign


RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,63}$")
PUBLIC_COLUMNS = (
    "id",
    "spacegroup",
    "number_of_total_atoms",
    "percent_atom_al",
    "percent_atom_ga",
    "percent_atom_in",
    "lattice_vector_1_ang",
    "lattice_vector_2_ang",
    "lattice_vector_3_ang",
    "lattice_angle_alpha_degree",
    "lattice_angle_beta_degree",
    "lattice_angle_gamma_degree",
)
PHASES = CAMPAIGN_PHASES


class CampaignError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    inbox_root: Path
    nomad_root: Path
    run_id: str
    image: str = "nomad-feature-sandbox:2026-07-18"

    def __post_init__(self) -> None:
        if not RUN_ID_RE.fullmatch(self.run_id):
            raise CampaignError("run_id must contain 3-64 safe filename characters")
        if not self.run_root.resolve().is_relative_to(self.nomad_root.resolve()):
            raise CampaignError("v2 campaign storage must remain below the NOMAD root")

    @property
    def run_root(self) -> Path:
        return self.inbox_root / self.run_id

    @property
    def db_path(self) -> Path:
        return self.run_root / "campaign.sqlite3"

    @property
    def budget_path(self) -> Path:
        return self.run_root / "budget.sqlite3"

    @property
    def events_path(self) -> Path:
        return self.run_root / "events.jsonl"

    @property
    def staged_atlas(self) -> Path:
        return self.run_root / "inputs/atlas"


def _verify_controller_snapshot(settings: Settings) -> dict[str, Any] | None:
    manifest_path = settings.run_root / "inputs/controller/manifest.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for logical_name, record in manifest.get("files", {}).items():
        source = Path(str(record["source"]))
        frozen = settings.run_root / "inputs/controller" / logical_name
        expected = str(record["sha256"])
        if (
            not source.exists()
            or not frozen.exists()
            or sha256_file(source) != expected
            or sha256_file(frozen) != expected
        ):
            raise CampaignError(
                f"trusted controller source changed after preflight: {logical_name}"
            )
    return manifest


def _stage_controller_snapshot(settings: Settings) -> dict[str, Any]:
    existing = _verify_controller_snapshot(settings)
    if existing is not None:
        return existing
    sources: dict[str, Path] = {
        f"v2/{path.name}": path
        for path in sorted((settings.repo_root / "nomad_feature_hunt/v2").glob("*.py"))
    }
    sources.update(
        {
            "plugin_runner.py": settings.repo_root
            / "ops/nomad-feature-hunt-v2/plugin_runner.py",
            "gpu_fit_worker.py": settings.repo_root
            / "nomad_feature_hunt/gpu_fit_worker.py",
            "shared/ledger.py": settings.repo_root / "nomad_feature_hunt/ledger.py",
            "shared/crystal_io.py": settings.repo_root / "nomad_crystal360/io.py",
            "shared/crystal_artifacts.py": settings.repo_root
            / "nomad_crystal360/artifacts.py",
            "shared/pyproject.toml": settings.repo_root / "pyproject.toml",
        }
    )
    destination = settings.run_root / "inputs/controller"
    files: dict[str, dict[str, str]] = {}
    for logical_name, source in sources.items():
        if not source.exists():
            raise CampaignError(f"trusted controller source is missing: {source}")
        target = destination / logical_name
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
        files[logical_name] = {"source": str(source.resolve()), "sha256": sha256_file(target)}
    manifest = {"frozen": True, "files": files, "test_labels_used": False}
    atomic_json(destination / "manifest.json", manifest)
    return manifest


def _campaign(settings: Settings) -> tuple[CampaignDB, BudgetAccount, HashChain]:
    _verify_controller_snapshot(settings)
    return (
        CampaignDB(settings.db_path),
        BudgetAccount(settings.budget_path),
        HashChain(settings.events_path),
    )


def _run_command(
    settings: Settings,
    command: list[str],
    *,
    timeout: int,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    _db, _budget, events = _campaign(settings)
    command_hash = sha256_bytes(json.dumps(command, separators=(",", ":")).encode())
    events.append("command_started", {"program": command[0], "argv_sha256": command_hash})
    temporary = settings.run_root / "runtime/tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["TMPDIR"] = str(temporary)
    result = subprocess.run(
        command,
        cwd=cwd or settings.repo_root,
        env=environment,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    events.append(
        "command_finished",
        {
            "argv_sha256": command_hash,
            "returncode": result.returncode,
            "stdout_sha256": sha256_bytes(result.stdout.encode()),
            "stderr_sha256": sha256_bytes(result.stderr.encode()),
        },
    )
    return result


def _copy_geometry_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        return
    shutil.copytree(source, destination, copy_function=shutil.copy2)


def _stage_public_inputs(settings: Settings) -> dict[str, Any]:
    destination = settings.run_root / "inputs/public"
    destination.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {"test_labels_used": False}
    for split, expected in (("train", TRAIN_ROWS), ("test", TEST_ROWS)):
        source = settings.nomad_root / f"{split}.csv"
        geometry = settings.nomad_root / split
        if not source.exists() or not geometry.is_dir():
            raise CampaignError(f"missing NOMAD {split} CSV or geometry tree")
        frame = pd.read_csv(source, usecols=list(PUBLIC_COLUMNS))
        if len(frame) != expected:
            raise CampaignError(f"{split} has {len(frame)} public rows, expected {expected}")
        target = destination / f"{split}.csv"
        frame.to_csv(target, index=False)
        geometry_target = destination / f"{split}_geometry"
        _copy_geometry_tree(geometry, geometry_target)
        receipt[split] = {
            "rows": len(frame),
            "csv": str(target),
            "csv_sha256": sha256_file(target),
            "geometry": str(geometry_target),
            "geometry_tree_sha256": geometry_tree_hash(frame, geometry_target),
        }
    atomic_json(destination / "staging_receipt.json", receipt)
    return receipt


def _dual_gpu_check(run_root: Path) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    local = subprocess.run(
        ["nvidia-smi", "-L"], text=True, capture_output=True, check=False, timeout=30
    )
    checks["local"] = {"returncode": local.returncode, "identity": local.stdout.strip()}
    remote = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "xbabe1", "nvidia-smi", "-L"],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    checks["xbabe1"] = {"returncode": remote.returncode, "identity": remote.stdout.strip()}
    local_catboost = subprocess.run(
        ["/usr/bin/python3", "-c", "import catboost"],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    remote_catboost = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "xbabe1", "/usr/bin/python3 -c 'import catboost'"],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    remote_runtime = run_root / "runtime/remote-gpu"
    remote_storage = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "xbabe1", "mkdir", "-p", str(remote_runtime)],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    checks["catboost"] = {
        "local_returncode": local_catboost.returncode,
        "xbabe1_returncode": remote_catboost.returncode,
        "remote_storage_returncode": remote_storage.returncode,
    }
    checks["ready"] = all(
        result.returncode == 0
        for result in (local, remote, local_catboost, remote_catboost, remote_storage)
    )
    return checks


def _sandbox_image_identity(image: str) -> str | None:
    result = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    identity = result.stdout.strip()
    return identity if result.returncode == 0 and identity.startswith("sha256:") else None


def preflight(settings: Settings) -> dict[str, Any]:
    for directory in ARTIFACT_DIRS:
        (settings.run_root / directory).mkdir(parents=True, exist_ok=True)
    db, budget, events = _campaign(settings)
    now = utc_now()
    db.execute(
        "INSERT OR IGNORE INTO campaign VALUES(?,?,?,'preflight',NULL,NULL)",
        (settings.run_id, now, "preflight"),
    )
    roles = role_specs()
    with db.connect() as connection:
        for role in roles:
            connection.execute(
                "INSERT OR IGNORE INTO roles(role_id,role_class,domain,wave,spec_json) "
                "VALUES(?,?,?,?,?)",
                (
                    role["id"],
                    role["class"],
                    role["domain"],
                    role["wave"],
                    json.dumps(role, sort_keys=True),
                ),
            )
    atomic_json(settings.run_root / "roles.json", roles)
    budget.reserve("research-and-operations", "research")
    budget.settle("research-and-operations", None)
    controller_snapshot = _stage_controller_snapshot(settings)

    atlas_source = settings.repo_root / "artifacts/atlas_hyperion_bakeoff/bundle"
    atlas_selected = settings.repo_root / "artifacts/atlas_hyperion_bakeoff/run/selected_columns.json"
    definitions = settings.repo_root / "artifacts/nomad_crystal_atlas/atlas_definitions.json"
    blockers: list[str] = []
    atlas_receipt: dict[str, Any] | None = None
    public_receipt: dict[str, Any] | None = None
    try:
        if not (settings.staged_atlas / "staging_receipt.json").exists() or not (
            settings.staged_atlas / "selected_columns.json"
        ).exists():
            atlas_receipt = stage_frozen_atlas(
                atlas_source,
                definitions,
                settings.staged_atlas,
                selected_columns_source=atlas_selected,
            )
        else:
            atlas_receipt = json.loads(
                (settings.staged_atlas / "staging_receipt.json").read_text(encoding="utf-8")
            )
        registry = settings.run_root / "novelty/atlas_registry.jsonl"
        if not registry.exists():
            seed_atlas_registry(settings.staged_atlas, registry)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        blockers.append(f"Atlas staging: {error}")
    try:
        public_receipt = _stage_public_inputs(settings)
    except (OSError, ValueError) as error:
        blockers.append(f"public input staging: {error}")

    v1_root = settings.nomad_root / "artifacts/nomad_theory_feature_hunt/inbox/nomad-foundry-20260718"
    if not (settings.run_root / "memory/v1_seeds/idea_seeds.json").exists():
        memory_receipt = import_v1_memory(v1_root, settings.run_root / "memory/v1_seeds")
    else:
        memory_receipt = {
            "idea_seeds": len(
                json.loads(
                    (settings.run_root / "memory/v1_seeds/idea_seeds.json").read_text(
                        encoding="utf-8"
                    )
                )
            ),
            "negative_items": len(
                json.loads(
                    (settings.run_root / "memory/v1_seeds/negative_memory.json").read_text(
                        encoding="utf-8"
                    )
                )
            ),
            "features_counted": 0,
        }
    if memory_receipt["idea_seeds"] != 74 or memory_receipt["negative_items"] < 1:
        blockers.append("v1 memory import must contain 74 idea seeds and negative outputs")

    runbooks = sorted((settings.repo_root / "ops/nomad-feature-hunt-v2").glob("*.json"))
    if len(runbooks) != 5:
        blockers.append("exactly five v2 declarative runbooks are required")
    required_commands = {name: shutil.which(name) is not None for name in ("jekko", "docker", "nvidia-smi", "ssh")}
    blockers.extend(f"missing command: {name}" for name, present in required_commands.items() if not present)
    image_identity = _sandbox_image_identity(settings.image) if required_commands["docker"] else None
    if required_commands["docker"] and image_identity is None:
        blockers.append(f"sandbox image is not built: {settings.image}")
    gpu = (
        _dual_gpu_check(settings.run_root)
        if required_commands["nvidia-smi"] and required_commands["ssh"]
        else {"ready": False}
    )
    if not gpu.get("ready"):
        blockers.append("dual-GPU dispatch preflight failed")
    status = {
        "run_id": settings.run_id,
        "created_at": now,
        "ready": not blockers,
        "blockers": blockers,
        "checks": {
            "role_count": len(roles),
            "commands": required_commands,
            "sandbox_image_digest": image_identity,
            "dual_gpu": gpu,
            "atlas": atlas_receipt,
            "controller_snapshot": controller_snapshot,
            "v1_memory": memory_receipt,
            "public_inputs": public_receipt,
            "runbooks": [str(path) for path in runbooks],
            "jailgun_optional": True,
            "budgets": {"wall_seconds": MAX_WALL_SECONDS, "cost_usd": 1_000.0},
            "test_labels_used": False,
        },
    }
    atomic_json(settings.run_root / "preflight.json", status)
    db.execute(
        "UPDATE campaign SET state=?,error=? WHERE run_id=?",
        ("preflight" if status["ready"] else "blocked", "; ".join(blockers) or None, settings.run_id),
    )
    events.append("preflight", status)
    return status


def _load_evidence(settings: Settings) -> list[dict[str, Any]]:
    path = settings.run_root / "evidence/evidence.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def run_evidence_phase(settings: Settings) -> dict[str, Any]:
    raw_directory = settings.run_root / "evidence/raw"
    if not list(raw_directory.glob("*.jsonl")):
        for round_number in range(1, 4):
            aspects_path = raw_directory / f"aspects-{round_number}.json"
            output_path = raw_directory / f"research-{round_number}.jsonl"
            aspects = {
                "aspects": [
                    {
                        "id": domain.id,
                        "title": domain.title,
                        "queries": [
                            f"{domain.title} crystal descriptor",
                            f"{domain.title} materials machine learning",
                            f"{domain.title} periodic invariant feature",
                        ],
                    }
                    for domain in DOMAINS
                ]
            }
            atomic_json(aspects_path, aspects)
            result = _run_command(
                settings,
                [
                    "jekko",
                    "research",
                    "--aspects",
                    str(aspects_path),
                    "--out",
                    str(output_path),
                    "--providers",
                    "openalex,crossref,arxiv",
                    "--queries-per-aspect",
                    "3",
                    "--per-query",
                    "10",
                ],
                timeout=3_600,
            )
            if result.returncode != 0:
                raise CampaignError(
                    f"research round {round_number} failed: {result.stderr[-1000:]}"
                )
    records: list[dict[str, Any]] = []
    for path in sorted(raw_directory.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    records = deduplicate_sources(records)
    for index, record in enumerate(records, start=1):
        record.setdefault("source_id", f"source-{index:04d}")
    errors = validate_evidence_coverage(records)
    if errors:
        raise CampaignError("; ".join(errors))
    atomic_json(settings.run_root / "evidence/evidence.json", records)
    citations = citation_registry(records)
    atomic_json(settings.run_root / "evidence/citations.json", citations)
    receipt = {
        "phase": "evidence",
        "sources": len(records),
        "citations": len(citations),
        "evidence_sha256": sha256_file(settings.run_root / "evidence/evidence.json"),
    }
    _record_phase_receipt(settings, "evidence", receipt)
    return receipt


def _family_map(db: CampaignDB, domain: str | None = None) -> dict[str, dict[str, Any]]:
    query = "SELECT payload_json FROM families"
    params: tuple[Any, ...] = ()
    if domain and domain != "ALL":
        query += " WHERE domain=?"
        params = (domain,)
    items = [json.loads(row["payload_json"]) for row in db.all(query, params)]
    if domain == "ALL":
        return {f"{item['domain']}:{item['family_slug']}": item for item in items}
    return {item["family_slug"]: item for item in items}


def _receipt_ids(db: CampaignDB) -> set[str]:
    return {str(row["receipt_id"]) for row in db.all("SELECT receipt_id FROM receipts WHERE valid=1")}


def _approved_parameter_schedule(domain: str, spec_slot: int) -> list[dict[str, Any]]:
    configurations: list[dict[str, Any]] = []
    weights = ("Z", "atomic_mass", "X", "atomic_radius")
    for offset in range(3):
        index = spec_slot * 3 + offset
        fraction = (index + 1) / 49.0
        if domain == "D01":
            configuration = {"symprec": 10 ** (-5.0 + 4.0 * fraction)}
        elif domain == "D02":
            configuration = {
                "hmax": 1 + index % 4,
                "weight": weights[(index // 4) % len(weights)],
                "debye_waller_b": round(3.0 * fraction, 8),
            }
        elif domain == "D03":
            configuration = {"cutoff": round(1.5 + 9.0 * fraction, 8)}
        elif domain == "D04":
            configuration = {
                "bond_valence_b": round(0.2 + 0.6 * fraction, 8),
                "screening_length": round(1.0 + 15.0 * fraction, 8),
                "charge_scale": round(0.6 + 0.8 * fraction, 8),
                "qeq_screening_length": round(1.0 + 12.0 * (1.0 - fraction), 8),
            }
        elif domain == "D05":
            configuration = {
                "cutoff": round(2.0 + 8.0 * fraction, 8),
                "width": round(0.15 + 0.75 * fraction, 8),
                "radial_centers": [1.0, 2.0, 3.0, 4.0],
            }
        elif domain == "D06":
            configuration = {"cutoff": round(1.5 + 6.0 * fraction, 8)}
        elif domain == "D07":
            configuration = {
                "grid": 3 + index % 6,
                "void_threshold": round(0.2 + 4.0 * fraction, 8),
            }
        elif domain == "D08":
            configuration = {
                "pair_cutoff": round(1.5 + 10.0 * fraction, 8),
                "redox_scale": round(0.5 + fraction, 8),
            }
        elif domain == "D09":
            configuration = {
                "bond_cutoff": round(1.5 + 6.0 * fraction, 8),
                "stiffness_exponent": round(2.0 + 4.0 * fraction, 8),
            }
        elif domain == "D10":
            configuration = {"cutoff": round(2.0 + 9.0 * fraction, 8)}
        else:
            raise CampaignError(f"no parameter schedule for domain {domain}")
        configurations.append(configuration)
    return configurations


def _required_output_schedule(kernel: str) -> list[dict[str, Any]]:
    sensitive = {
        "symmetry": (
            "normalized-residual-mean",
            "normalized-residual-max",
            "symmetry-confidence",
            "symmetry-residual-entropy",
        ),
        "reciprocal": (
            "structure-factor-mean",
            "structure-factor-std",
            "structure-factor-max",
            "structure-factor-entropy",
            "phase-coherence",
        ),
        "orbital_local": KERNEL_OPERATIONS["orbital_local"],
        "electrostatic": KERNEL_OPERATIONS["electrostatic"],
        "local_density": KERNEL_OPERATIONS["local_density"],
        "periodic_graph": KERNEL_OPERATIONS["periodic_graph"],
        "canonical_topology": (
            "void-radius-mean",
            "void-radius-max",
            "minkowski-volume-fraction",
            "minkowski-interface-proxy",
        ),
        "thermodynamics": (
            "electronegativity-mismatch",
            "radius-mismatch",
            "atomic-number-mismatch",
            "redox-imbalance",
            "redox-variance",
            "bond-mismatch-energy",
        ),
        "mechanics": tuple(
            operation
            for operation in KERNEL_OPERATIONS["mechanics"]
            if operation != "mass-density"
        ),
        "entropy_transport": (
            "radial-entropy-fine",
            "radial-entropy-medium",
            "radial-entropy-coarse",
            "entropy-scale-slope",
            "renyi-two",
        ),
        "custom": CUSTOM_PLUGIN_OUTPUTS,
    }[kernel]
    approved = (
        KERNEL_OPERATIONS[kernel] if kernel in KERNEL_OPERATIONS else CUSTOM_PLUGIN_OUTPUTS
    )
    pairs: list[tuple[str, int]] = []
    if kernel == "custom":
        pairs.extend((operation, index % 3) for index, operation in enumerate(sensitive))
    else:
        pairs.extend((operation, config_index) for operation in sensitive for config_index in range(3))
        pairs.extend(
            (operation, config_index)
            for operation in approved
            for config_index in range(3)
            if (operation, config_index) not in pairs
        )
    return [
        {"operation": operation, "configuration_index": config_index}
        for operation, config_index in pairs[:19]
    ]


def _ingest_role_result(
    settings: Settings,
    role: dict[str, Any],
    attempt: int,
    result: dict[str, Any],
) -> tuple[bool, list[str], str]:
    db, budget, _events = _campaign(settings)
    text = str(result.get("assistant_text", ""))
    errors: list[str] = []
    payload: Any = None
    if "router_metadata" not in result:
        errors.append("router_metadata field is missing from the router result")
    if result.get("success") is not True:
        errors.append(str(result.get("error") or "Jnoccio result was unsuccessful"))
    elif len(text.encode("utf-8")) > OUTPUT_LIMIT_BYTES:
        errors.append("assistant output exceeds the 20 KB ceiling")
    else:
        try:
            payload = parse_strict_json(text)
            citations_path = settings.run_root / "evidence/citations.json"
            citations = set(json.loads(citations_path.read_text())) if citations_path.exists() else None
            errors.extend(
                validate_role_payload(
                    role,
                    payload,
                    families=_family_map(db, str(role.get("domain"))),
                    citation_ids=citations,
                    available_receipt_ids=_receipt_ids(db),
                )
            )
            if role["class"] == "plugin_writer" and isinstance(payload, dict):
                errors.extend(static_check_plugin(str(payload.get("plugin_source", ""))))
                custom_families = sorted(
                    slug
                    for slug, card in _family_map(db, str(role["domain"])).items()
                    if card.get("custom_plugin_required") is True
                )
                ordinal = int(str(role["id"]).rsplit("-", 1)[-1]) - 1
                expected = custom_families[ordinal] if ordinal < len(custom_families) else None
                if payload.get("family_slug") != expected:
                    errors.append(f"plugin writer is assigned custom family: {expected}")
            if role["class"] == "spec_builder" and isinstance(payload, dict):
                cards = sorted(_family_map(db, str(role["domain"])))
                ordinal = int(str(role["id"]).rsplit("-", 1)[-1]) - 1
                expected = {
                    cards[index % len(cards)]
                    for index in (ordinal * 2, ordinal * 2 + 1)
                } if cards else set()
                actual = {
                    str(spec.get("family_slug"))
                    for spec in payload.get("feature_specs", [])
                    if isinstance(spec, dict)
                }
                if actual != expected:
                    errors.append(f"spec builder assigned family slugs: {sorted(expected)}")
                expected_schedules = {
                    cards[index % len(cards)]: _approved_parameter_schedule(
                        str(role["domain"]), index
                    )
                    for index in (ordinal * 2, ordinal * 2 + 1)
                } if cards else {}
                for spec in payload.get("feature_specs", []):
                    if not isinstance(spec, dict):
                        continue
                    family_slug = str(spec.get("family_slug"))
                    actual_configs = {
                        json.dumps(item.get("values"), sort_keys=True, separators=(",", ":"))
                        for item in spec.get("parameter_sets", [])
                        if isinstance(item, dict)
                    }
                    expected_configs = {
                        json.dumps(item, sort_keys=True, separators=(",", ":"))
                        for item in expected_schedules.get(family_slug, [])
                    }
                    if actual_configs != expected_configs:
                        errors.append(
                            f"{family_slug} must use its three approved physical configurations"
                        )
                    scheduled_configs = expected_schedules.get(family_slug, [])
                    config_index_by_id: dict[str, int] = {}
                    for parameter_set in spec.get("parameter_sets", []):
                        if not isinstance(parameter_set, dict):
                            continue
                        try:
                            config_index = scheduled_configs.index(parameter_set.get("values"))
                        except ValueError:
                            continue
                        config_index_by_id[str(parameter_set.get("id"))] = config_index
                    card = _family_map(db, str(role["domain"])).get(family_slug)
                    expected_outputs = {
                        (item["operation"], item["configuration_index"])
                        for item in _required_output_schedule(str(card["kernel"]))
                    } if card is not None else set()
                    actual_outputs = {
                        (
                            str(output.get("operation")),
                            config_index_by_id.get(str(output.get("parameter_set")), -1),
                        )
                        for output in spec.get("outputs", [])
                        if isinstance(output, dict)
                    }
                    if actual_outputs != expected_outputs:
                        errors.append(
                            f"{family_slug} outputs must match its 19 assigned operation/configuration pairs"
                        )
            if role["class"] in {"experimental_analyst", "blind_judge"} and isinstance(
                payload, dict
            ):
                for field, expected_kind in (
                    ("matrix_receipt_ids", "matrix"),
                    ("score_receipt_ids", "score"),
                ):
                    for receipt_id in payload.get(field, []):
                        receipt = db.one(
                            "SELECT kind,valid FROM receipts WHERE receipt_id=?",
                            (receipt_id,),
                        )
                        if (
                            receipt is None
                            or receipt["kind"] != expected_kind
                            or receipt["valid"] != 1
                        ):
                            errors.append(
                                f"{field} contains a non-{expected_kind} receipt: {receipt_id}"
                            )
            if role["class"] in {"target_exploiter", "cross_family_synthesizer"} and isinstance(
                payload, dict
            ):
                feedback_path = settings.run_root / "scoring/discovery/adaptive_feedback.json"
                feedback = json.loads(feedback_path.read_text(encoding="utf-8"))[
                    "family_feedback"
                ]
                items = sorted(feedback.items())
                family_cards = _family_map(db, "ALL")
                items = [
                    item
                    for item in items
                    if family_cards.get(item[0].split(":", 1)[-1], {}).get("kernel")
                    != "custom"
                ]
                if role.get("target"):
                    items = [
                        item for item in items if item[0].startswith(f"{role['target']}:")
                    ]
                positive = [
                    item for item in items if item[1].get("discovery_lift") == "positive"
                ]
                selected = (positive or items)[:12]
                allowed = sorted({item[0].split(":", 1)[-1] for item in selected})[:4]
                actual = {
                    f"{spec.get('domain')}:{spec.get('family_slug')}"
                    for spec in payload.get("feature_specs", [])
                    if isinstance(spec, dict)
                }
                if not actual.issubset(set(allowed)):
                    errors.append(f"adaptive specs must use assigned winner families: {allowed}")
                for spec in payload.get("feature_specs", []):
                    if not isinstance(spec, dict):
                        continue
                    card = _family_map(db, "ALL").get(
                        f"{spec.get('domain')}:{spec.get('family_slug')}"
                    )
                    if card is None or card.get("kernel") != "custom":
                        continue
                    approved_names: set[str] = set()
                    for row in db.all(
                        "SELECT payload_json FROM feature_specs WHERE domain=? "
                        "AND family_slug=? AND status='compiled'",
                        (spec.get("domain"), spec.get("family_slug")),
                    ):
                        prior_spec = json.loads(row["payload_json"])
                        approved_names.update(
                            str(output["name"]) for output in prior_spec["outputs"]
                        )
                    output_names = {
                        str(output.get("name"))
                        for output in spec.get("outputs", [])
                        if isinstance(output, dict)
                    }
                    if not output_names.issubset(approved_names):
                        errors.append(
                            "adaptive custom specs must reuse plugin-tested output names: "
                            f"{sorted(approved_names)}"
                        )
        except (SchemaError, json.JSONDecodeError, ValueError) as error:
            errors.append(str(error))

    if not errors and isinstance(payload, dict):
        try:
            _persist_role_payload(settings, db, role, payload)
        except (sqlite3.IntegrityError, KeyError, ValueError) as error:
            errors.append(str(error))
    valid = not errors
    raw_path = settings.run_root / f"queue/results/{role['id']}.attempt-{attempt}.json"
    record_attempt_result(
        db,
        budget,
        role_id=str(role["id"]),
        attempt=attempt,
        result=result,
        raw_result_path=raw_path,
        valid=valid,
        errors=errors,
    )
    receipt = {
        "receipt_id": f"jnoccio:{role['id']}:{attempt}",
        "role_id": role["id"],
        "attempt": attempt,
        "valid": valid,
        "errors": errors,
        "provider": result.get("provider_id"),
        "model": result.get("model_id"),
        "credential_user": result.get("credential_user_id"),
        "router_metadata_present": "router_metadata" in result,
        "router_metadata": result.get("router_metadata"),
        "prompt_sha256": db.one(
            "SELECT prompt_sha256 FROM jobs WHERE role_id=? AND attempt=?",
            (role["id"], attempt),
        )["prompt_sha256"],
        "output_sha256": sha256_bytes(text.encode()),
        "raw_result_sha256": sha256_file(raw_path),
        "test_labels_used": False,
    }
    receipt_path = settings.run_root / f"receipts/jnoccio/{role['id']}.attempt-{attempt}.json"
    atomic_json(receipt_path, receipt)
    db.execute(
        "INSERT OR REPLACE INTO receipts VALUES(?,?,?,?,?,?,?)",
        (
            receipt["receipt_id"],
            "jnoccio",
            role["id"],
            str(receipt_path),
            sha256_file(receipt_path),
            int(valid),
            json.dumps(receipt, sort_keys=True),
        ),
    )
    return valid, errors, text


def _persist_role_payload(
    settings: Settings, db: CampaignDB, role: dict[str, Any], payload: dict[str, Any]
) -> None:
    if role["class"] == "evidence_curator":
        atomic_json(settings.run_root / f"evidence/{role['id']}.json", payload)
    elif role["class"] == "family_architect":
        with db.connect() as connection:
            for card in payload["family_cards"]:
                family_id = f"{card['domain'].casefold()}.{card['family_slug']}"
                atomic_json(settings.run_root / f"families/{family_id}.json", card)
                connection.execute(
                    "INSERT INTO families VALUES(?,?,?,?,?,?)",
                    (
                        family_id,
                        card["family_slug"],
                        card["domain"],
                        role["id"],
                        json.dumps(card, sort_keys=True, separators=(",", ":")),
                        "designed",
                    ),
                )
    elif role["class"] in {"spec_builder", "target_exploiter", "cross_family_synthesizer"}:
        with db.connect() as connection:
            for spec in payload["feature_specs"]:
                spec_id = f"{spec['domain'].casefold()}.{spec['family_slug']}.{spec['spec_slug']}"
                atomic_json(settings.run_root / f"specs/{spec_id}.json", spec)
                connection.execute(
                    "INSERT INTO feature_specs VALUES(?,?,?,?,?,?)",
                    (
                        spec_id,
                        spec["family_slug"],
                        spec["domain"],
                        role["id"],
                        json.dumps(spec, sort_keys=True, separators=(",", ":")),
                        "designed",
                    ),
                )
    elif role["class"] == "plugin_writer":
        already_implemented = {
            json.loads(path.read_text(encoding="utf-8")).get("family_slug")
            for path in (settings.run_root / "plugins").glob("*.json")
        }
        if payload["family_slug"] in already_implemented:
            remaining = sorted(
                slug
                for slug, card in _family_map(db, str(role["domain"])).items()
                if card.get("custom_plugin_required") is True
                and slug not in already_implemented
            )
            raise ValueError(
                f"custom family already has a plugin; remaining assigned families: {remaining}"
            )
        plugin_path = settings.run_root / f"plugins/{role['id']}.py"
        plugin_path.write_text(payload["plugin_source"], encoding="utf-8")
        atomic_json(
            plugin_path.with_suffix(".json"),
            {
                "family_slug": payload["family_slug"],
                "source_role_id": role["id"],
                "plugin_sha256": sha256_file(plugin_path),
                "adversarial_tests": payload["adversarial_tests"],
            },
        )
    elif role["class"] in {"experimental_analyst", "blind_judge"}:
        atomic_json(settings.run_root / f"judgments/{role['id']}.json", payload)
        db.execute(
            "INSERT OR REPLACE INTO judgments VALUES(?,?,?,?)",
            (
                role["id"],
                role["id"],
                json.dumps(
                    payload["matrix_receipt_ids"] + payload["score_receipt_ids"],
                    sort_keys=True,
                ),
                json.dumps(payload, sort_keys=True),
            ),
        )
    elif role["class"] == "memory_curator":
        atomic_json(settings.run_root / f"memory/{role['id']}.json", payload)


def _run_role_group(
    settings: Settings,
    roles: list[dict[str, Any]],
    *,
    context: dict[str, Any] | None = None,
) -> tuple[int, list[str]]:
    db, budget, events = _campaign(settings)
    evidence = _load_evidence(settings)
    failures: list[str] = []
    valid_count = 0
    pending = [
        role
        for role in roles
        if db.one("SELECT status FROM roles WHERE role_id=?", (role["id"],))["status"]
        != "complete"
    ]
    invalid_artifacts: dict[str, tuple[str, list[str]]] = {}

    def role_context(role: dict[str, Any]) -> dict[str, Any] | None:
        if context is None:
            return None
        if isinstance(context.get("family_cards"), list):
            cards = sorted(
                (
                    card
                    for card in context["family_cards"]
                    if role["domain"] == "ALL" or card.get("domain") == role["domain"]
                ),
                key=lambda card: (str(card.get("domain")), str(card.get("family_slug"))),
            )
            if role["class"] == "plugin_writer":
                cards = [card for card in cards if card.get("custom_plugin_required") is True]
            try:
                ordinal = int(str(role["id"]).rsplit("-", 1)[-1]) - 1
            except ValueError:
                ordinal = 0
            if role["class"] == "plugin_writer":
                assigned = [cards[ordinal % len(cards)]] if cards else []
                assignment_indices = [ordinal]
            else:
                assignment_indices = [ordinal * 2, ordinal * 2 + 1]
                assigned = (
                    [cards[index % len(cards)] for index in assignment_indices]
                    if cards
                    else []
                )
            assigned_slugs = {str(card["family_slug"]) for card in assigned}
            assigned_specs = [
                spec
                for spec in context.get("feature_specs", [])
                if spec.get("family_slug") in assigned_slugs
            ]
            if role["class"] == "plugin_writer":
                assigned_specs = [
                    {
                        "spec_slug": spec["spec_slug"],
                        "family_slug": spec["family_slug"],
                        "parameter_sets": spec["parameter_sets"],
                        "outputs": [
                            {
                                "name": output["name"],
                                "operation": output["operation"],
                                "parameter_set": output["parameter_set"],
                            }
                            for output in spec["outputs"]
                        ],
                    }
                    for spec in assigned_specs
                ]
            response = {
                "assigned_family_cards": assigned,
                "assigned_feature_specs": assigned_specs,
                "approved_operations": {
                    card["family_slug"]: (
                        list(KERNEL_OPERATIONS[card["kernel"]])
                        if card.get("kernel") in KERNEL_OPERATIONS
                        else list(CUSTOM_PLUGIN_OUTPUTS)
                    )
                    for card in assigned
                },
            }
            if role["class"] == "spec_builder":
                response["approved_parameter_schedule"] = {
                    cards[index % len(cards)]["family_slug"]: _approved_parameter_schedule(
                        str(role["domain"]), index
                    )
                    for index in assignment_indices
                } if cards else {}
                response["required_output_schedule"] = {
                    card["family_slug"]: _required_output_schedule(str(card["kernel"]))
                    for card in assigned
                }
            return response
        if isinstance(context.get("family_feedback"), dict):
            items = list(sorted(context["family_feedback"].items()))
            cards = context.get("adaptive_family_cards", {})
            items = [
                item
                for item in items
                if cards.get(item[0].split(":", 1)[-1], {}).get("kernel") != "custom"
            ]
            target = role.get("target")
            if target:
                items = [item for item in items if item[0].startswith(f"{target}:")]
            positive = [item for item in items if item[1].get("discovery_lift") == "positive"]
            selected = (positive or items)[:12]
            keys = {item[0].split(":", 1)[-1] for item in selected}
            selected_cards = [cards[key] for key in sorted(keys) if key in cards][:4]
            approved_operations: dict[str, list[str]] = {}
            for card in selected_cards:
                family_key = f"{card['domain']}:{card['family_slug']}"
                if card.get("kernel") in KERNEL_OPERATIONS:
                    approved_operations[family_key] = list(
                        KERNEL_OPERATIONS[card["kernel"]]
                    )
                else:
                    names: set[str] = set()
                    for row in db.all(
                        "SELECT payload_json FROM feature_specs WHERE domain=? AND family_slug=?",
                        (card["domain"], card["family_slug"]),
                    ):
                        spec = json.loads(row["payload_json"])
                        names.update(str(output["name"]) for output in spec["outputs"])
                    approved_operations[family_key] = sorted(names)
            return {
                "family_feedback": dict(selected),
                "family_cards": selected_cards,
                "approved_operations": approved_operations,
                "campaign_columns_needed": int(context.get("campaign_columns_needed", 0)),
                "desired_columns_from_this_role": int(
                    context.get("desired_columns_from_this_role", 0)
                ),
            }
        if isinstance(context.get("available_receipt_ids"), list):
            return {"available_receipt_ids": context["available_receipt_ids"][:20]}
        if isinstance(context.get("curator_atlas_gaps"), dict):
            gaps = context["curator_atlas_gaps"].get(role.get("domain"), [])
            return {
                "curator_atlas_gaps": [str(item)[:300] for item in gaps[:5]],
                "v1_memory": context.get("v1_memory", {}).get(role.get("domain"), {}),
            }
        return context

    for attempt in range(MAX_ATTEMPTS_PER_ROLE):
        attempt_roles = [
            role
            for role in pending
            if int(
                db.one("SELECT COUNT(*) n FROM attempts WHERE role_id=?", (role["id"],))["n"]
            )
            <= attempt
        ]
        if not attempt_roles:
            continue
        prompts: list[tuple[dict[str, Any], str]] = []
        for role in attempt_roles:
            if attempt == 0:
                domain = role["domain"] if role["domain"] != "ALL" else DOMAINS[0].id
                evidence_roles = {
                    "evidence_curator",
                    "family_architect",
                    "spec_builder",
                }
                prompt = build_role_prompt(
                    role,
                    evidence=(
                        build_claim_pack(
                            evidence,
                            domain,
                            max_bytes=(
                                3 * 1024 if role["class"] == "spec_builder" else 6 * 1024
                            ),
                        )
                        if evidence and role["class"] in evidence_roles
                        else []
                    ),
                    novelty_summary={
                        "atlas_columns": ATLAS_WIDTH,
                        "registry_receipt": "novelty/atlas_registry.receipt.json",
                    },
                    controller_context=role_context(role),
                )
            else:
                invalid, prior_errors = invalid_artifacts[role["id"]]
                prompt = build_retry_prompt(role, invalid, prior_errors)
            prompts.append((role, prompt))
        batch_id = f"wave-{attempt_roles[0]['wave']}.attempt-{attempt}"
        jobs_path = settings.run_root / f"queue/jobs/{batch_id}.json"
        prepare_job_batch(
            db,
            batch_id=batch_id,
            jobs_path=jobs_path,
            prompt_dir=settings.run_root / "prompts",
            roles_and_prompts=prompts,
            attempt=attempt,
        )
        mark_batch_submitted(db, budget, batch_id)
        results_dir = settings.run_root / f"queue/results/{batch_id}"
        results_dir.mkdir(parents=True, exist_ok=True)
        command = [
            "jekko",
            "zyal-queue",
            "--provider",
            "jnoccio",
            "--model",
            "jnoccio-router",
            "--workers",
            str(JNOCCIO_WORKERS),
            "--jobs",
            str(jobs_path),
            "--results-dir",
            str(results_dir),
            "--run-id",
            f"{settings.run_id}-{batch_id}",
        ]
        process = _run_command(settings, command, timeout=7_300)
        failed_this_attempt: list[dict[str, Any]] = []
        for role in attempt_roles:
            result_path = results_dir / f"{role['id']}.json"
            if result_path.exists():
                result = json.loads(result_path.read_text(encoding="utf-8"))
            else:
                result = {
                    "success": False,
                    "error": "Jnoccio result file was not produced",
                    "assistant_text": "",
                    "provider_id": None,
                    "model_id": None,
                    "credential_user_id": None,
                    "router_metadata": None,
                }
            valid, errors, invalid = _ingest_role_result(settings, role, attempt, result)
            if valid:
                valid_count += 1
            else:
                invalid_artifacts[role["id"]] = (invalid, errors)
                failed_this_attempt.append(role)
        events.append(
            "jnoccio_batch",
            {
                "batch_id": batch_id,
                "roles": len(attempt_roles),
                "valid": len(attempt_roles) - len(failed_this_attempt),
                "returncode": process.returncode,
            },
        )
        pending = failed_this_attempt
        if not pending:
            break
    failures.extend(str(role["id"]) for role in pending)
    return valid_count, failures


def run_design_phase(settings: Settings) -> dict[str, Any]:
    roles = role_specs()
    canaries = [role for role in roles if role["class"] == "evidence_curator"]
    _valid, failed = _run_role_group(settings, canaries)
    db, _budget, _events = _campaign(settings)
    first_pass = int(
        db.one(
            "SELECT COUNT(*) n FROM attempts a JOIN roles r ON r.role_id=a.role_id "
            "WHERE r.role_class='evidence_curator' AND a.attempt=0 AND a.valid=1"
        )["n"]
    )
    if first_pass < 9 or failed:
        raise CampaignError(
            f"schema canary failed: {first_pass}/10 first-pass; exhausted={failed}"
        )
    curator_gaps = {
        role["domain"]: json.loads(
            (settings.run_root / f"evidence/{role['id']}.json").read_text(encoding="utf-8")
        ).get("atlas_gaps", [])[:5]
        for role in canaries
    }
    idea_seeds = json.loads(
        (settings.run_root / "memory/v1_seeds/idea_seeds.json").read_text(encoding="utf-8")
    )
    negative_memory = json.loads(
        (settings.run_root / "memory/v1_seeds/negative_memory.json").read_text(
            encoding="utf-8"
        )
    )
    v1_memory = {
        domain.id: {
            "unverified_idea_seeds": [
                json.dumps(item.get("payload", item), sort_keys=True)[:300]
                for item in idea_seeds
                if item.get("domain") == domain.id
            ][:2],
            "negative_examples": [
                json.dumps(item, sort_keys=True)[:300]
                for item in negative_memory
                if item.get("domain") in {None, domain.id}
            ][:2],
            "ideas_count_as_features": False,
        }
        for domain in DOMAINS
    }
    architects = [role for role in roles if role["class"] == "family_architect"]
    _valid, failed = _run_role_group(
        settings,
        architects,
        context={"curator_atlas_gaps": curator_gaps, "v1_memory": v1_memory},
    )
    if failed:
        raise CampaignError(f"family architect roles exhausted: {failed}")
    family_context = {
        "family_cards": [
            json.loads(row["payload_json"])
            for row in db.all("SELECT payload_json FROM families ORDER BY domain,family_slug")
        ]
    }
    spec_builders = [role for role in roles if role["class"] == "spec_builder"]
    _valid, failed = _run_role_group(settings, spec_builders, context=family_context)
    if failed:
        raise CampaignError(f"spec_builder roles exhausted: {failed}")
    plugin_context = {
        **family_context,
        "feature_specs": [
            json.loads(row["payload_json"])
            for row in db.all("SELECT payload_json FROM feature_specs ORDER BY spec_id")
        ],
    }
    plugin_writers = [role for role in roles if role["class"] == "plugin_writer"]
    _valid, failed = _run_role_group(settings, plugin_writers, context=plugin_context)
    if failed:
        raise CampaignError(f"plugin_writer roles exhausted: {failed}")
    receipt = {
        "phase": "design",
        "families": int(db.one("SELECT COUNT(*) n FROM families")["n"]),
        "specs": int(db.one("SELECT COUNT(*) n FROM feature_specs")["n"]),
        "plugins": len(list((settings.run_root / "plugins").glob("*.py"))),
        "canary_first_pass": first_pass,
    }
    _record_phase_receipt(settings, "design", receipt)
    return receipt


def _load_staged_structures(settings: Settings) -> tuple[pd.DataFrame, pd.DataFrame, list[Any], list[Any]]:
    public = settings.run_root / "inputs/public"
    train_frame = pd.read_csv(public / "train.csv")
    test_frame = pd.read_csv(public / "test.csv")
    train_structures = load_structures(train_frame, public / "train_geometry")
    test_structures = load_structures(test_frame, public / "test_geometry")
    return train_frame, test_frame, train_structures, test_structures


def _run_precompile_smoke(
    settings: Settings,
    compiler: TrustedCompiler,
    card: dict[str, Any],
    spec: dict[str, Any],
) -> dict[str, Any]:
    train_frame, _test_frame, structures, _test_structures = _load_staged_structures(settings)
    if len(structures) < 16:
        raise CampaignError("precompile smoke requires 16 real structures")
    from pymatgen.core import Lattice, Structure

    toy = Structure(
        Lattice.cubic(4.2),
        ["Al", "O", "O"],
        [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25]],
    )
    for kernel in TRUSTED_KERNELS:
        values = compute_kernel(kernel, toy, {})
        if not values or not all(math.isfinite(float(value)) for value in values.values()):
            raise CampaignError(f"trusted-kernel toy smoke is nonfinite: {kernel}")
        report = run_invariance_tests(
            [toy], lambda structure, name=kernel: compute_kernel(name, structure, {})
        )
        if not all(all(columns.values()) for columns in report.values()):
            raise CampaignError(f"trusted-kernel toy invariance failed: {kernel}")
    smoke_compiler = TrustedCompiler(compiler.cache)
    compiled = smoke_compiler.compile(card, spec, source_role_id="smoke-gate")
    sample_ids = deterministic_real_sample(train_frame["id"].tolist(), 16)
    by_id = dict(zip(train_frame["id"].tolist(), structures))
    sample = [by_id[identifier] for identifier in sample_ids]
    first = smoke_compiler.compute_matrix(compiled, sample, sample_ids)
    second = smoke_compiler.compute_matrix(compiled, sample, sample_ids)
    if not first.equals(second):
        raise CampaignError("trusted-kernel 16-structure smoke is nondeterministic")
    invariance = run_invariance_tests(
        sample, lambda structure: smoke_compiler.compute_family(compiled, structure)
    )
    if not all(all(columns.values()) for columns in invariance.values()):
        raise CampaignError("trusted-kernel 16-structure smoke failed invariance")

    plugins = sorted((settings.run_root / "plugins").glob("*.py"))
    if not plugins:
        raise CampaignError("precompile smoke requires one custom plugin")
    plugin = plugins[0]
    plugin_errors = static_check_plugin(plugin.read_text(encoding="utf-8"))
    if plugin_errors:
        raise CampaignError("custom-plugin smoke failed static checks: " + "; ".join(plugin_errors))
    # The executable sandbox receipt is produced by the networkless plugin harness.  It must
    # attest all 16 real structures and every required invariance before broad compilation.
    sandbox_receipt = settings.run_root / "receipts/sandbox/custom-smoke.json"
    if not sandbox_receipt.exists():
        output = settings.run_root / "receipts/sandbox/custom-smoke-output"
        output.mkdir(parents=True, exist_ok=True)
        output.chmod(0o777)
        command = plugin_sandbox_command(
            image=settings.image,
            plugin=plugin,
            harness=settings.run_root / "inputs/controller/plugin_runner.py",
            structures=settings.run_root / "inputs/public/train_geometry",
            output=output,
        )
        result = _run_command(settings, command, timeout=1_800)
        output.chmod(0o750)
        produced = output / "receipt.json"
        if result.returncode != 0 or not produced.exists():
            raise CampaignError("custom-plugin 16-structure sandbox smoke failed")
        shutil.copy2(produced, sandbox_receipt)
    custom = json.loads(sandbox_receipt.read_text(encoding="utf-8"))
    if (
        custom.get("structures") != 16
        or custom.get("toy") is not True
        or custom.get("network") != "none"
        or custom.get("deterministic") is not True
        or not all(custom.get("invariances", {}).get(name) is True for name in (
            "translation", "rotation", "atom_permutation", "periodic_wrapping", "equivalent_cell"
        ))
    ):
        raise CampaignError("custom-plugin 16-structure sandbox receipt is invalid")
    receipt = {
        "trusted_kernel": spec["kernel"],
        "trusted_toy_kernels": len(TRUSTED_KERNELS),
        "trusted_family": card["family_slug"],
        "trusted_structures": 16,
        "trusted_deterministic": True,
        "trusted_invariances": True,
        "custom_toy": True,
        "custom_structures": 16,
        "custom_invariances": True,
        "custom_plugin_sha256": sha256_file(plugin),
        "custom_receipt_sha256": sha256_file(sandbox_receipt),
    }
    atomic_json(settings.run_root / "receipts/sandbox/precompile-gate.json", receipt)
    return receipt


def _compile_designed_specs(
    settings: Settings, compiler: TrustedCompiler, *, run_smoke: bool
) -> list[dict[str, Any]]:
    db, _budget, _events = _campaign(settings)
    spec_rows = db.all(
        "SELECT * FROM feature_specs WHERE status='designed' ORDER BY spec_id"
    )
    if not spec_rows:
        return []
    if run_smoke:
        trusted_row = next(
            (
                row
                for row in spec_rows
                if json.loads(row["payload_json"])["kernel"] != "custom"
            ),
            None,
        )
        if trusted_row is None:
            raise CampaignError("precompile smoke requires a trusted-kernel FeatureSpec")
        trusted_spec = json.loads(trusted_row["payload_json"])
        family_row = db.one(
            "SELECT * FROM families WHERE domain=? AND family_slug=?",
            (trusted_spec["domain"], trusted_spec["family_slug"]),
        )
        _run_precompile_smoke(
            settings, compiler, json.loads(family_row["payload_json"]), trusted_spec
        )
    rows: list[dict[str, Any]] = []
    for spec_row in spec_rows:
        spec = json.loads(spec_row["payload_json"])
        family_row = db.one(
            "SELECT * FROM families WHERE domain=? AND family_slug=?",
            (spec["domain"], spec["family_slug"]),
        )
        if family_row is None:
            raise CampaignError(f"spec {spec_row['spec_id']} has no FamilyCard")
        card = json.loads(family_row["payload_json"])
        expanded = expand_feature_spec(card, spec, source_role_id=spec_row["source_role_id"])
        if spec["kernel"] == "custom":
            _plugin_for_family(settings, str(spec["family_slug"]))
        else:
            compiler.compile(card, spec, source_role_id=spec_row["source_role_id"])
        with db.connect() as connection:
            for column in expanded:
                connection.execute(
                    "INSERT INTO columns VALUES(?,?,?,?,?,?)",
                    (
                        column["feature_id"],
                        column["family_slug"],
                        column["domain"],
                        "attempted",
                        None,
                        json.dumps(column, sort_keys=True, separators=(",", ":")),
                    ),
                )
        rows.extend(expanded)
        db.execute("UPDATE feature_specs SET status='compiled' WHERE spec_id=?", (spec_row["spec_id"],))
    return rows


def _write_column_registry(settings: Settings) -> tuple[Path, int]:
    db, _budget, _events = _campaign(settings)
    registry_path = settings.run_root / "registry/columns.jsonl"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    rows = db.all("SELECT registry_json FROM columns ORDER BY feature_id")
    registry_path.write_text(
        "".join(str(row["registry_json"]) + "\n" for row in rows), encoding="utf-8"
    )
    return registry_path, len(rows)


def run_compilation_phase(settings: Settings) -> dict[str, Any]:
    compiler = TrustedCompiler(PrimitiveCache(settings.run_root / "cache/primitives"))
    _compile_designed_specs(settings, compiler, run_smoke=True)
    registry_path, attempted = _write_column_registry(settings)
    if attempted + 40 * 25 < 4_000:
        raise CampaignError(
            f"initial design attempted {attempted} columns and cannot reach 4,000 "
            "within the forty-spec adaptive cap"
        )
    receipt = {
        "phase": "compilation",
        "attempted_columns": attempted,
        "registry_sha256": sha256_file(registry_path),
        "controller_ids_unique": True,
    }
    _record_phase_receipt(settings, "compilation", receipt)
    return receipt


def _atlas_novelty_maps(settings: Settings) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {
        "name": {}, "numeric": {}, "formula": {}, "semantic": {}
    }
    path = settings.run_root / "novelty/atlas_registry.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        name = str(record["name"])
        result["name"][name] = name
        result["numeric"][str(record["numeric_signature"])] = name
        result["formula"][str(record["formula_fingerprint"])] = name
        result["semantic"][str(record["semantic_fingerprint"])] = name
    return result


def _plugin_for_family(settings: Settings, family_slug: str) -> Path:
    matches: list[Path] = []
    for metadata_path in sorted((settings.run_root / "plugins").glob("*.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("family_slug") == family_slug:
            matches.append(metadata_path.with_suffix(".py"))
    if len(matches) != 1 or not matches[0].exists():
        raise CampaignError(
            f"custom family {family_slug} requires exactly one statically accepted plugin"
        )
    return matches[0]


def _execute_custom_spec(
    settings: Settings,
    spec_id: str,
    spec: dict[str, Any],
    expanded: list[dict[str, Any]],
    train_ids: list[Any],
    test_ids: list[Any],
    invariance_ids: list[Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    plugin = _plugin_for_family(settings, str(spec["family_slug"]))
    errors = static_check_plugin(plugin.read_text(encoding="utf-8"))
    if errors:
        raise CampaignError("custom plugin failed static recheck: " + "; ".join(errors))
    runtime = settings.run_root / f"matrices/temporary/custom/{spec_id}"
    runtime.mkdir(parents=True, exist_ok=True)
    specification_path = runtime / "controller-specification.json"
    atomic_json(
        specification_path,
        {
            "train_ids": train_ids,
            "test_ids": test_ids,
            "invariance_ids": invariance_ids,
            "columns": [
                {
                    "feature_id": row["feature_id"],
                    "operation": row["operation"],
                    "plugin_key": row["output_name"],
                    "configuration": row["configuration"],
                }
                for row in expanded
            ],
        },
    )
    output = runtime / "sandbox-output"
    output.mkdir(parents=True, exist_ok=True)
    output.chmod(0o777)
    command = plugin_full_execution_command(
        image=settings.image,
        plugin=plugin,
        harness=settings.run_root / "inputs/controller/plugin_runner.py",
        train_structures=settings.run_root / "inputs/public/train_geometry",
        test_structures=settings.run_root / "inputs/public/test_geometry",
        specification=specification_path,
        output=output,
    )
    result = _run_command(settings, command, timeout=7_200)
    output.chmod(0o750)
    receipt_path = output / "receipt.json"
    if result.returncode != 0 or not receipt_path.exists():
        raise CampaignError(
            f"custom plugin full execution failed for {spec_id}: {result.stderr[-1000:]}"
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("mode") != "full"
        or receipt.get("train_rows") != TRAIN_ROWS
        or receipt.get("test_rows") != TEST_ROWS
        or receipt.get("invariance_structures") != 64
        or receipt.get("network") != "none"
        or receipt.get("deterministic") is not True
        or receipt.get("test_labels_used") is not False
    ):
        raise CampaignError(f"custom plugin full receipt is invalid for {spec_id}")
    for filename, expected_hash in receipt.get("files", {}).items():
        if sha256_file(output / filename) != expected_hash:
            raise CampaignError(f"custom plugin output hash mismatch: {filename}")

    def read(name: str) -> pd.DataFrame:
        return pd.read_json(output / name, lines=True, precise_float=True)

    invariance = json.loads((output / "invariance.json").read_text(encoding="utf-8"))
    return (
        read("train.jsonl"),
        read("test.jsonl"),
        read("rerun_train.jsonl"),
        read("rerun_test.jsonl"),
        invariance,
        {"plugin_sha256": sha256_file(plugin), "sandbox_receipt_sha256": sha256_file(receipt_path)},
    )


def run_execution_phase(settings: Settings) -> dict[str, Any]:
    """Execute trusted specs on 2,400/600 and quarantine scalar columns independently."""

    db, _budget, _events = _campaign(settings)
    completed_matrix_ids = {
        str(row["matrix_id"]) for row in db.all("SELECT matrix_id FROM matrices")
    }
    with db.connect() as connection:
        for row in connection.execute(
            "SELECT feature_id,registry_json FROM columns "
            "WHERE status IN ('validated','quarantined')"
        ):
            registry = json.loads(row["registry_json"])
            spec_id = str(registry.get("base_equation_id", "")).removeprefix("v2.")
            if spec_id not in completed_matrix_ids:
                connection.execute(
                    "UPDATE columns SET status='attempted',rejection_reason=NULL "
                    "WHERE feature_id=?",
                    (row["feature_id"],),
                )
    train_frame, test_frame, train_structures, test_structures = _load_staged_structures(settings)
    if len(train_structures) != TRAIN_ROWS or len(test_structures) != TEST_ROWS:
        raise CampaignError("full execution requires exactly 2,400/600 staged structures")
    atlas = _atlas_novelty_maps(settings)
    earlier_numeric: dict[str, str] = {}
    earlier_formula: dict[str, str] = {}
    earlier_semantic: dict[str, str] = {}
    for row in db.all("SELECT feature_id,registry_json FROM columns WHERE status='validated'"):
        registry = json.loads(row["registry_json"])
        earlier_formula[str(registry["formula_fingerprint"])] = str(row["feature_id"])
        earlier_semantic[str(registry["semantic_fingerprint"])] = str(row["feature_id"])
    for matrix_row in db.all("SELECT train_path,test_path FROM matrices WHERE valid=1"):
        prior_train = pd.read_parquet(matrix_row["train_path"])
        prior_test = pd.read_parquet(matrix_row["test_path"])
        for column in prior_train.columns:
            if column == "id":
                continue
            signature = numeric_signature(
                pd.concat((prior_train[column], prior_test[column]), ignore_index=True).to_numpy(
                    dtype=float
                )
            )
            earlier_numeric[signature] = column
    cache = PrimitiveCache(settings.run_root / "cache/primitives")
    compiler = TrustedCompiler(cache)
    rerun_compiler = TrustedCompiler(PrimitiveCache(settings.run_root / "cache/rerun"))
    matrices = 0
    accepted_total = 0
    rejected_total = 0
    sample_ids = deterministic_real_sample(train_frame["id"].tolist(), 64)
    by_id = dict(zip(train_frame["id"].tolist(), train_structures))
    invariant_sample = [by_id[identifier] for identifier in sample_ids]

    for spec_row in db.all(
        "SELECT * FROM feature_specs WHERE status='compiled' "
        "AND spec_id NOT IN (SELECT matrix_id FROM matrices) ORDER BY spec_id"
    ):
        spec = json.loads(spec_row["payload_json"])
        family_row = db.one(
            "SELECT * FROM families WHERE domain=? AND family_slug=?",
            (spec["domain"], spec["family_slug"]),
        )
        card = json.loads(family_row["payload_json"])
        started = time.perf_counter()
        sandbox: dict[str, Any] | None = None
        if spec["kernel"] == "custom":
            expanded = expand_feature_spec(
                card, spec, source_role_id=spec_row["source_role_id"]
            )
            train, test, rerun_train, rerun_test, invariance, sandbox = _execute_custom_spec(
                settings,
                str(spec_row["spec_id"]),
                spec,
                expanded,
                train_frame["id"].tolist(),
                test_frame["id"].tolist(),
                sample_ids,
            )
            metadata = {row["feature_id"]: row for row in expanded}
        else:
            compiled = compiler.compile(card, spec, source_role_id=spec_row["source_role_id"])
            rerun_compiled = rerun_compiler.compile(
                card, spec, source_role_id=spec_row["source_role_id"]
            )
            train = compiler.compute_matrix(compiled, train_structures, train_frame["id"])
            test = compiler.compute_matrix(compiled, test_structures, test_frame["id"])
            rerun_train = rerun_compiler.compute_matrix(
                rerun_compiled, train_structures, train_frame["id"]
            )
            rerun_test = rerun_compiler.compute_matrix(
                rerun_compiled, test_structures, test_frame["id"]
            )
            invariance = run_invariance_tests(
                invariant_sample,
                lambda structure, item=compiled: compiler.compute_family(item, structure),
            )
            metadata = {row["feature_id"]: row for row in compiled.columns}
        compute_seconds = time.perf_counter() - started

        # Exact name/formula/semantic collisions are marked per output before numeric checks.
        pre_rejected: dict[str, str] = {}
        formula_lookup = {**atlas["formula"], **earlier_formula}
        semantic_lookup = {**atlas["semantic"], **earlier_semantic}
        for feature_id, row in metadata.items():
            collisions = (
                ("name", feature_id, atlas["name"]),
                ("formula", row["formula_fingerprint"], formula_lookup),
                ("semantic", row["semantic_fingerprint"], semantic_lookup),
            )
            for kind, value, lookup in collisions:
                if value in lookup:
                    pre_rejected[feature_id] = f"exact_{kind}_duplicate_of:{lookup[value]}"
                    for invariant in invariance:
                        invariance[invariant][feature_id] = False
                    break
            if feature_id not in pre_rejected:
                formula_lookup[row["formula_fingerprint"]] = feature_id
                semantic_lookup[row["semantic_fingerprint"]] = feature_id
        quarantine = quarantine_columns(
            train,
            test,
            expected_train_ids=train_frame["id"].tolist(),
            expected_test_ids=test_frame["id"].tolist(),
            rerun_train=rerun_train,
            rerun_test=rerun_test,
            invariance_report=invariance,
            atlas_numeric_signatures=atlas["numeric"],
            earlier_v2_signatures=earlier_numeric,
        )
        accepted = list(quarantine.accepted)
        rejection_by_column = {item.column: item.reason for item in quarantine.rejected}
        rejection_by_column.update(pre_rejected)
        for feature_id in accepted:
            row = metadata[feature_id]
            earlier_numeric[quarantine.signatures[feature_id]] = feature_id
            earlier_formula[row["formula_fingerprint"]] = feature_id
            earlier_semantic[row["semantic_fingerprint"]] = feature_id
        with db.connect() as connection:
            for feature_id in metadata:
                if feature_id in accepted:
                    connection.execute(
                        "UPDATE columns SET status='validated',rejection_reason=NULL WHERE feature_id=?",
                        (feature_id,),
                    )
                else:
                    connection.execute(
                        "UPDATE columns SET status='quarantined',rejection_reason=? WHERE feature_id=?",
                        (rejection_by_column.get(feature_id, "validation_failure"), feature_id),
                    )

        matrix_id = str(spec_row["spec_id"])
        output = settings.run_root / f"matrices/validated/{matrix_id}"
        output.mkdir(parents=True, exist_ok=True)
        train_path = output / "train.parquet"
        test_path = output / "test.parquet"
        quarantine.train.to_parquet(train_path, index=False)
        quarantine.test.to_parquet(test_path, index=False)
        receipt = {
            "receipt_id": f"matrix:{matrix_id}",
            "matrix_id": matrix_id,
            "family_slug": spec["family_slug"],
            "domain": spec["domain"],
            "train_rows": len(quarantine.train),
            "test_rows": len(quarantine.test),
            "accepted_columns": accepted,
            "rejections": [item.__dict__ for item in quarantine.rejected],
            "pre_rejections": pre_rejected,
            "train_sha256": sha256_file(train_path),
            "test_sha256": sha256_file(test_path),
            "deterministic": True,
            "invariance_sample": 64,
            "compute_seconds": compute_seconds,
            "execution_lane": "custom_plugin" if spec["kernel"] == "custom" else "trusted_kernel",
            "sandbox": sandbox,
            "test_labels_used": False,
        }
        receipt_path = output / "receipt.json"
        atomic_json(receipt_path, receipt)
        with db.connect() as connection:
            connection.execute(
                "INSERT INTO matrices VALUES(?,?,?,?,?,?,?)",
                (
                    matrix_id,
                    spec["family_slug"],
                    str(train_path),
                    str(test_path),
                    len(accepted),
                    int(bool(accepted)),
                    receipt["receipt_id"],
                ),
            )
            connection.execute(
                "INSERT INTO receipts VALUES(?,?,?,?,?,?,?)",
                (
                    receipt["receipt_id"],
                    "matrix",
                    None,
                    str(receipt_path),
                    sha256_file(receipt_path),
                    int(bool(accepted)),
                    json.dumps(receipt, sort_keys=True),
                ),
            )
        matrices += 1
        accepted_total += len(accepted)
        rejected_total += len(metadata) - len(accepted)
    receipt = {
        "phase": "execution",
        "matrices": matrices,
        "validated_columns": accepted_total,
        "quarantined_columns": rejected_total,
        "train_rows": TRAIN_ROWS,
        "test_rows": TEST_ROWS,
        "test_labels_used": False,
    }
    _record_phase_receipt(settings, "execution", receipt)
    return receipt


def _validated_family_candidates(settings: Settings) -> dict[str, FamilyCandidate]:
    db, _budget, _events = _campaign(settings)
    grouped: dict[tuple[str, str], list[tuple[pd.DataFrame, float]]] = {}
    for row in db.all(
        "SELECT m.*,r.payload_json receipt_payload FROM matrices m "
        "JOIN receipts r ON r.receipt_id=m.receipt_id WHERE m.valid=1 ORDER BY m.matrix_id"
    ):
        frame = pd.read_parquet(row["train_path"])
        if "id" not in frame or len(frame) != TRAIN_ROWS or len(frame.columns) <= 1:
            raise CampaignError(f"validated matrix contract changed: {row['matrix_id']}")
        payload = json.loads(row["receipt_payload"])
        key = (str(payload["domain"]), str(row["family_slug"]))
        grouped.setdefault(key, []).append(
            (frame, float(payload.get("compute_seconds", 0.0)))
        )
    families: dict[str, FamilyCandidate] = {}
    for (domain, family_slug), matrices in grouped.items():
        identifiers = matrices[0][0]["id"].tolist()
        pieces: list[pd.DataFrame] = []
        for frame, _seconds in matrices:
            if frame["id"].tolist() != identifiers:
                raise CampaignError(f"family matrices are row-misaligned: {family_slug}")
            pieces.append(frame.drop(columns="id"))
        combined = pd.concat(pieces, axis=1)
        if combined.columns.duplicated().any():
            raise CampaignError(f"family matrices have duplicate columns: {family_slug}")
        family_row = db.one(
            "SELECT domain,payload_json FROM families WHERE domain=? AND family_slug=?",
            (domain, family_slug),
        )
        if family_row is None:
            raise CampaignError(f"matrix family has no FamilyCard: {family_slug}")
        card = json.loads(family_row["payload_json"])
        families[f"{domain}:{family_slug}"] = FamilyCandidate(
            family_slug=family_slug,
            domain=str(family_row["domain"]),
            train=pd.concat((matrices[0][0][["id"]], combined), axis=1),
            compute_seconds=sum(seconds for _frame, seconds in matrices),
            target_affinity=card.get("target_affinity", "both"),
        )
    return families


def run_discovery_phase(settings: Settings) -> dict[str, Any]:
    """Compute and validate private dual-GPU discovery; publish categories only."""

    db, _budget, _events = _campaign(settings)
    if not db.one("SELECT 1 FROM matrices WHERE valid=1"):
        raise CampaignError("discovery requires at least one real validated matrix receipt")
    path = settings.run_root / "scoring/discovery/controller_results.json"
    if not path.exists():
        score_discovery(
            atlas_bundle=settings.staged_atlas,
            families=_validated_family_candidates(settings),
            output_dir=path.parent,
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    protocol = payload.get("protocol", {})
    if (
        protocol.get("folds") != 2
        or protocol.get("trees") != 150
        or tuple(protocol.get("seeds", [])) != (1701, 2909, 4219)
        or protocol.get("gpu_processes") != 2
        or protocol.get("one_process_per_gpu") is not True
        or protocol.get("cpu_fallback") is not False
        or protocol.get("dispatch_hash_chain_valid") is not True
        or protocol.get("confirmation_folds_accessed") is not False
        or protocol.get("test_labels_used") is not False
    ):
        raise CampaignError("discovery protocol does not match the sealed two-fold GPU contract")
    feedback: dict[str, dict[str, str]] = {}
    rows = payload.get("families")
    if not isinstance(rows, list) or not rows:
        raise CampaignError("discovery has no family results")
    with db.connect() as connection:
        for index, row in enumerate(rows):
            target = str(row.get("target"))
            if target not in TARGETS:
                raise CampaignError(f"invalid discovery target: {target}")
            score_id = str(row.get("score_id") or f"discovery-{index:05d}")
            family = str(row["family_slug"])
            family_key = str(row.get("family_key") or f"{row['domain']}:{family}")
            categories = categorical_discovery_feedback(
                lift=float(row["lift"]),
                redundancy=float(row["redundancy"]),
                compute_seconds=float(row["compute_seconds"]),
                residual_correlation=float(row["residual_correlation"]),
            )
            feedback[f"{target}:{family_key}"] = categories
            connection.execute(
                "INSERT OR REPLACE INTO scores VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    score_id,
                    "discovery",
                    target,
                    family,
                    row["domain"],
                    int(float(row["lift"]) > 0),
                    str(row.get("nonoverlap_group") or family_key),
                    json.dumps(row, sort_keys=True),
                    "score:discovery",
                ),
            )
    public = public_adaptive_packet(feedback)
    public_path = settings.run_root / "scoring/discovery/adaptive_feedback.json"
    atomic_json(public_path, public)
    receipt = {
        "phase": "discovery",
        "receipt_id": "score:discovery",
        "families_scored": len(rows),
        "controller_results_sha256": sha256_file(path),
        "adaptive_feedback_sha256": sha256_file(public_path),
        "contains_exact_scores_for_agents": False,
        "confirmation_folds_accessed": False,
        "test_labels_used": False,
    }
    receipt_path = settings.run_root / "receipts/discovery-score.json"
    atomic_json(receipt_path, receipt)
    db.execute(
        "INSERT INTO receipts VALUES(?,?,?,?,?,?,?)",
        (
            receipt["receipt_id"], "score", None, str(receipt_path),
            sha256_file(receipt_path), 1, json.dumps(receipt, sort_keys=True),
        ),
    )
    _record_phase_receipt(settings, "discovery", receipt)
    return receipt


def run_adaptive_phase(settings: Settings) -> dict[str, Any]:
    db, _budget, _events = _campaign(settings)
    if db.one("SELECT 1 FROM phase_receipts WHERE phase='discovery'") is None:
        raise CampaignError("adaptive generation requires sealed discovery results")
    feedback_path = settings.run_root / "scoring/discovery/adaptive_feedback.json"
    feedback = json.loads(feedback_path.read_text(encoding="utf-8"))
    cards = {
        f"{row['domain']}:{row['family_slug']}": json.loads(row["payload_json"])
        for row in db.all("SELECT domain,family_slug,payload_json FROM families")
    }
    attempted_before = int(db.one("SELECT COUNT(*) n FROM columns")["n"])
    columns_needed = max(0, 4_000 - attempted_before)
    feedback.update(
        {
            "adaptive_family_cards": cards,
            "campaign_columns_needed": columns_needed,
            "desired_columns_from_this_role": (columns_needed + 19) // 20,
        }
    )
    roles = [
        role
        for role in role_specs()
        if role["class"] in {"target_exploiter", "cross_family_synthesizer"}
    ]
    _valid, failed = _run_role_group(settings, roles, context=feedback)
    if failed:
        raise CampaignError(f"adaptive roles exhausted: {failed}")
    designed_specs = int(
        db.one("SELECT COUNT(*) n FROM feature_specs WHERE status='designed'")["n"]
    )
    if designed_specs > 40:
        raise CampaignError("adaptive roles produced more than forty FeatureSpecs")
    new_columns = _compile_designed_specs(
        settings,
        TrustedCompiler(PrimitiveCache(settings.run_root / "cache/primitives")),
        run_smoke=False,
    )
    _write_column_registry(settings)
    attempted_after = int(db.one("SELECT COUNT(*) n FROM columns")["n"])
    if attempted_after < 4_000:
        raise CampaignError(
            f"adaptive generation stopped at {attempted_after} attempted columns; 4,000 required"
        )
    adaptive_execution = run_execution_phase(settings)
    marker = {
        "adaptive_generation_stopped": True,
        "roles": 20,
        "specs_maximum": 40,
        "specs": designed_specs,
        "new_columns": len(new_columns),
        "campaign_columns_needed_before_adaptive": columns_needed,
        "validated_adaptive_columns": adaptive_execution["validated_columns"],
        "stopped_at": utc_now(),
    }
    atomic_json(settings.run_root / "scoring/adaptive_frozen.json", marker)
    _record_phase_receipt(settings, "adaptive", {"phase": "adaptive", **marker})
    return marker


def run_confirmation_phase(settings: Settings) -> dict[str, Any]:
    db, _budget, _events = _campaign(settings)
    frozen = settings.run_root / "scoring/adaptive_frozen.json"
    if not frozen.exists() or json.loads(frozen.read_text()).get("adaptive_generation_stopped") is not True:
        raise CampaignError("confirmation remains sealed until adaptive generation stops")
    prereg_path = settings.run_root / "scoring/confirmation/preregistration.json"
    result_path = settings.run_root / "scoring/confirmation/controller_results.json"
    candidates = _validated_family_candidates(settings)
    if not prereg_path.exists():
        discovery_path = settings.run_root / "scoring/discovery/controller_results.json"
        if not discovery_path.exists():
            raise CampaignError("confirmation cannot preregister without discovery results")
        discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
        preregistration = build_confirmation_preregistration(
            discovery.get("families", []), candidates
        )
        atomic_json(prereg_path, preregistration)
    if not result_path.exists():
        preregistration = json.loads(prereg_path.read_text(encoding="utf-8"))
        score_confirmation(
            atlas_bundle=settings.staged_atlas,
            families=candidates,
            preregistration=preregistration,
            output_dir=result_path.parent,
        )
    preregistration = json.loads(prereg_path.read_text(encoding="utf-8"))
    for target in TARGETS:
        validate_confirmation_views(target, preregistration.get(target, []))
    results = json.loads(result_path.read_text(encoding="utf-8"))
    protocol = results.get("protocol", {})
    if (
        protocol.get("folds") != 5
        or protocol.get("trees") != 400
        or protocol.get("shuffled") is not True
        or protocol.get("gpu_processes") != 2
        or protocol.get("one_process_per_gpu") is not True
        or protocol.get("cpu_fallback") is not False
        or protocol.get("dispatch_hash_chain_valid") is not True
        or protocol.get("confirmation_runs") != 1
        or protocol.get("test_labels_used") is not False
    ):
        raise CampaignError("confirmation protocol is not the one-shot shuffled five-fold contract")
    rows = results.get("views")
    if not isinstance(rows, list) or not rows:
        raise CampaignError("confirmation has no scored views")
    registered = {
        (target, str(view["view_id"]))
        for target, views in preregistration.items()
        for view in views
    }
    with db.connect() as connection:
        for index, row in enumerate(rows):
            key = (str(row.get("target")), str(row.get("view_id")))
            if key not in registered:
                raise CampaignError(f"unregistered confirmation view: {key}")
            bound = {**row, "folds": 5, "trees": 400}
            connection.execute(
                "INSERT OR REPLACE INTO scores VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    str(row.get("score_id") or f"confirmation-{index:03d}"),
                    "confirmation",
                    key[0],
                    None,
                    None,
                    None,
                    None,
                    json.dumps(bound, sort_keys=True),
                    "score:confirmation",
                ),
            )
    receipt = {
        "phase": "confirmation",
        "receipt_id": "score:confirmation",
        "views": len(rows),
        "preregistration_sha256": sha256_file(prereg_path),
        "controller_results_sha256": sha256_file(result_path),
        "folds_unsealed_once": True,
        "test_labels_used": False,
    }
    receipt_path = settings.run_root / "receipts/confirmation-score.json"
    atomic_json(receipt_path, receipt)
    db.execute(
        "INSERT INTO receipts VALUES(?,?,?,?,?,?,?)",
        (
            receipt["receipt_id"], "score", None, str(receipt_path),
            sha256_file(receipt_path), 1, json.dumps(receipt, sort_keys=True),
        ),
    )
    _record_phase_receipt(settings, "confirmation", receipt)
    return receipt


def run_judging_phase(settings: Settings) -> dict[str, Any]:
    db, _budget, _events = _campaign(settings)
    if (
        db.one("SELECT 1 FROM receipts WHERE kind='matrix' AND valid=1") is None
        or db.one("SELECT 1 FROM receipts WHERE kind='score' AND valid=1") is None
    ):
        raise CampaignError("analysts and judges require real matrix and score receipts")
    for role_class in ("experimental_analyst", "blind_judge", "memory_curator"):
        roles = [role for role in role_specs() if role["class"] == role_class]
        matrix_ids = [
            str(row["receipt_id"])
            for row in db.all(
                "SELECT receipt_id FROM receipts WHERE kind='matrix' AND valid=1 "
                "ORDER BY receipt_id LIMIT 12"
            )
        ]
        score_ids = [
            str(row["receipt_id"])
            for row in db.all(
                "SELECT receipt_id FROM receipts WHERE kind='score' AND valid=1 "
                "ORDER BY receipt_id"
            )
        ]
        context = {"available_receipt_ids": [*score_ids, *matrix_ids]}
        _valid, failed = _run_role_group(settings, roles, context=context)
        if failed:
            raise CampaignError(f"{role_class} roles exhausted: {failed}")
    receipt = {
        "phase": "judging",
        "analysts": 4,
        "judges": 4,
        "memory_curators": 2,
        "receipt_bound": True,
    }
    _record_phase_receipt(settings, "judging", receipt)
    return receipt


def _record_phase_receipt(settings: Settings, phase: str, payload: dict[str, Any]) -> None:
    db, _budget, events = _campaign(settings)
    receipt_id = f"phase:{phase}"
    path = settings.run_root / f"receipts/{phase}.json"
    atomic_json(path, payload)
    db.execute(
        "INSERT OR REPLACE INTO receipts VALUES(?,?,?,?,?,?,?)",
        (
            receipt_id,
            "phase",
            None,
            str(path),
            sha256_file(path),
            1,
            json.dumps(payload, sort_keys=True),
        ),
    )
    db.execute(
        "INSERT OR REPLACE INTO phase_receipts VALUES(?,?,?)", (phase, receipt_id, utc_now())
    )
    db.execute("UPDATE campaign SET phase=? WHERE run_id=?", (phase, settings.run_id))
    events.append("phase_complete", {"phase": phase, "receipt_id": receipt_id})


def run_optional_jailgun(settings: Settings) -> dict[str, Any]:
    db, budget, events = _campaign(settings)
    receipt: dict[str, Any] = {"optional": True, "tabs": 0, "family_cards": 0}
    probe = settings.repo_root / "ops/nomad-feature-hunt/probe_chatgpt.mjs"
    if shutil.which("jailgun") is None or shutil.which("node") is None or not probe.exists():
        receipt.update({"status": "skipped", "reason": "Jailgun or visible identity probe unavailable"})
    else:
        result = _run_command(
            settings,
            ["node", str(probe), "--expected", "GPT-5.6", "--minimum-capacity", "10"],
            timeout=120,
        )
        try:
            identity = json.loads(result.stdout)
        except json.JSONDecodeError:
            identity = None
        if result.returncode != 0 or not isinstance(identity, dict) or identity.get("ready") is not True:
            receipt.update({"status": "skipped", "reason": "exact visible GPT-5.6 probe failed"})
        else:
            receipt.update({"status": "available", "identity": identity})
    path = settings.run_root / "receipts/jailgun/optional.json"
    atomic_json(path, receipt)
    db.execute(
        "INSERT OR REPLACE INTO receipts VALUES(?,?,?,?,?,?,?)",
        (
            "jailgun:optional",
            "jailgun",
            None,
            str(path),
            sha256_file(path),
            1,
            json.dumps(receipt, sort_keys=True),
        ),
    )
    events.append("jailgun_optional", receipt)
    return receipt


def status_campaign(settings: Settings) -> dict[str, Any]:
    if not settings.db_path.exists():
        return {"run_id": settings.run_id, "state": "not_preflighted"}
    db, budget, events = _campaign(settings)
    campaign = db.one("SELECT * FROM campaign WHERE run_id=?", (settings.run_id,))
    chain_valid, chain_error = events.verify()
    return {
        "run_id": settings.run_id,
        "state": campaign["state"] if campaign else "unknown",
        "phase": campaign["phase"] if campaign else None,
        "error": campaign["error"] if campaign else None,
        "counts": {
            "roles": int(db.one("SELECT COUNT(*) n FROM roles")["n"]),
            "roles_complete": int(db.one("SELECT COUNT(*) n FROM roles WHERE status='complete'")["n"]),
            "families": int(db.one("SELECT COUNT(*) n FROM families")["n"]),
            "specs": int(db.one("SELECT COUNT(*) n FROM feature_specs")["n"]),
            "columns_attempted": int(db.one("SELECT COUNT(*) n FROM columns")["n"]),
            "columns_validated": int(db.one("SELECT COUNT(*) n FROM columns WHERE status='validated'")["n"]),
        },
        "budget": budget.summary().__dict__,
        "hash_chain_valid": chain_valid,
        "hash_chain_error": chain_error,
    }


def run_campaign(settings: Settings, *, resume: bool = False) -> dict[str, Any]:
    status = preflight(settings)
    if not status["ready"]:
        raise CampaignError("preflight blockers: " + "; ".join(status["blockers"]))
    db, _budget, events = _campaign(settings)
    db.execute(
        "UPDATE campaign SET state='running',started_at=COALESCE(started_at,?),error=NULL "
        "WHERE run_id=?",
        (utc_now(), settings.run_id),
    )
    events.append("campaign_resumed" if resume else "campaign_started", {"run_id": settings.run_id})
    run_optional_jailgun(settings)
    completed = {str(row["phase"]) for row in db.all("SELECT phase FROM phase_receipts")}
    actions = {
        "evidence": run_evidence_phase,
        "design": run_design_phase,
        "compilation": run_compilation_phase,
        "execution": run_execution_phase,
        "discovery": run_discovery_phase,
        "adaptive": run_adaptive_phase,
        "confirmation": run_confirmation_phase,
        "judging": run_judging_phase,
    }
    for phase in PHASES:
        if phase in completed:
            continue
        action = actions.get(phase)
        if action is None:
            raise CampaignError(
                f"phase {phase} requires its controller-produced matrix/score artifacts before resume"
            )
        action(settings)
    report = verify_campaign(settings.run_root, settings.run_id)
    db.execute(
        "UPDATE campaign SET state=?,error=? WHERE run_id=?",
        ("complete" if report["complete"] else "incomplete", "; ".join(report["missing"]) or None, settings.run_id),
    )
    return report


def _settings_from_args(args: argparse.Namespace) -> Settings:
    return Settings(
        repo_root=Path(args.repo_root).resolve(),
        inbox_root=Path(args.inbox_root).resolve(),
        nomad_root=Path(args.nomad_root).resolve(),
        run_id=args.run_id,
        image=args.image,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NOMAD Feature Foundry v2")
    parser.add_argument(
        "command",
        choices=("preflight", "run", "resume", "status", "verify", *PHASES),
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--nomad-root", default=str(DEFAULT_NOMAD_ROOT))
    parser.add_argument("--inbox-root", default=str(DEFAULT_INBOX_ROOT))
    parser.add_argument("--image", default="nomad-feature-sandbox:2026-07-18")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = _settings_from_args(args)
    try:
        if args.command == "preflight":
            result = preflight(settings)
        elif args.command == "run":
            result = run_campaign(settings)
        elif args.command == "resume":
            result = run_campaign(settings, resume=True)
        elif args.command == "status":
            result = status_campaign(settings)
        elif args.command == "verify":
            result = verify_campaign(settings.run_root, settings.run_id)
        elif args.command == "evidence":
            result = run_evidence_phase(settings)
        elif args.command == "design":
            result = run_design_phase(settings)
        elif args.command == "compilation":
            result = run_compilation_phase(settings)
        elif args.command == "execution":
            result = run_execution_phase(settings)
        elif args.command == "discovery":
            result = run_discovery_phase(settings)
        elif args.command == "adaptive":
            result = run_adaptive_phase(settings)
        elif args.command == "confirmation":
            result = run_confirmation_phase(settings)
        elif args.command == "judging":
            result = run_judging_phase(settings)
        else:
            raise CampaignError(f"unsupported phase: {args.command}")
        print(json.dumps(result, indent=2, sort_keys=True))
        if args.command == "preflight" and not result.get("ready", False):
            return 2
        if args.command in {"run", "resume", "verify"} and not result.get("complete", False):
            return 2
        return 0
    except (BudgetError, CampaignError, OSError, SchemaError, ValueError) as error:
        print(json.dumps({"run_id": settings.run_id, "error": str(error)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
