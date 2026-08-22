from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .constants import (
    ARTIFACT_DIRS,
    ATLAS_TARGET_WINNERS,
    ATLAS_WIDTH,
    ATLAS_WINNER_MEAN,
    DEFAULT_INBOX_ROOT,
    DEFAULT_NOMAD_ROOT,
    DOMAINS,
    EXISTING_809_CONTROLS,
    EXISTING_809_MEAN,
    EXPECTED_JAILGUN_CONCEPTS,
    EXPECTED_JAILGUN_TABS,
    EXPECTED_JNOCCIO_ROLES,
    JNOCCIO_WORKERS,
    MAX_COST_USD,
    MAX_RETRIES,
    MAX_WALL_SECONDS,
    MIN_ATTEMPTED_FEATURES,
    MIN_VALIDATED_FEATURES,
    MIN_VALIDATED_PER_DOMAIN,
    TARGETS,
    TEST_ROWS,
    TRAIN_ROWS,
    role_specs,
)
from .ledger import (
    CampaignDB,
    HashChain,
    atomic_json,
    canonical_json,
    sha256_bytes,
    sha256_file,
    utc_now,
)
from .schemas import (
    extract_json_payload,
    formula_fingerprint,
    semantic_fingerprint,
    semantic_similarity,
    semantic_tokens,
    validate_concept,
    validate_role_payload,
)
from .scoring import (
    DualGPUExecutor,
    GPUFitJob,
    MatrixValidationError,
    score_batches,
    validate_matrix_pair,
)
from .security import docker_sandbox_command, safe_extract_tar_bytes, static_check_generator


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


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    inbox_root: Path
    nomad_root: Path
    run_id: str
    image: str = "nomad-feature-sandbox:2026-07-18"

    def __post_init__(self) -> None:
        run_root = (self.inbox_root / self.run_id).resolve()
        nomad_root = self.nomad_root.resolve()
        if not run_root.is_relative_to(nomad_root):
            raise CampaignError(
                f"campaign storage must remain below {nomad_root}, found {run_root}"
            )

    @property
    def run_root(self) -> Path:
        return self.inbox_root / self.run_id

    @property
    def db_path(self) -> Path:
        return self.run_root / "campaign.sqlite3"

    @property
    def events_path(self) -> Path:
        return self.run_root / "events.jsonl"


class CampaignError(RuntimeError):
    pass


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _validate_run_id(run_id: str) -> None:
    if not RUN_ID_RE.fullmatch(run_id):
        raise CampaignError("run_id must be 3-64 safe filename characters")


def _campaign(settings: Settings) -> tuple[CampaignDB, HashChain]:
    return CampaignDB(settings.db_path), HashChain(settings.events_path)


def _assert_inputs(settings: Settings) -> dict[str, Path]:
    paths = {
        "train_csv": settings.nomad_root / "train.csv",
        "test_csv": settings.nomad_root / "test.csv",
        "train_geometry": settings.nomad_root / "train",
        "test_geometry": settings.nomad_root / "test",
        "atlas_bundle": settings.repo_root / "artifacts/atlas_hyperion_bakeoff/bundle",
        "atlas_run": settings.repo_root / "artifacts/atlas_hyperion_bakeoff/run",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise CampaignError(f"required NOMAD inputs are missing: {missing}")
    manifest = json.loads((paths["atlas_bundle"] / "bundle_manifest.json").read_text())
    if manifest.get("train_rows") != TRAIN_ROWS or manifest.get("test_rows") != TEST_ROWS:
        raise CampaignError("Atlas bundle does not contain the required 2,400/600 structures")
    if manifest.get("predictors") != ATLAS_WIDTH:
        raise CampaignError("Atlas bundle is not the frozen 9,969-column control")
    if manifest.get("contains_test_targets") is not False or manifest.get("test_labels_used") is not False:
        raise CampaignError("Atlas bundle does not attest the no-test-label boundary")
    return paths


def _command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _registry_capacity() -> dict[str, Any]:
    registry_path = Path(
        os.environ.get(
            "JAILGUN_BROWSER_PROFILE_REGISTRY",
            str(Path.home() / ".jailgun/browser-profiles.json"),
        )
    )
    if not registry_path.exists():
        return {"path": str(registry_path), "ready": [], "capacity": 0}
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    ready = [account for account in registry.get("accounts", []) if account.get("status") == "ready"]
    return {
        "path": str(registry_path),
        "ready": [
            {
                "id": account.get("id"),
                "cdp_port": account.get("cdp_port"),
                "max_tabs": max(int(account.get("max_tabs", 1)), 1),
            }
            for account in ready
        ],
        "capacity": sum(max(int(account.get("max_tabs", 1)), 1) for account in ready),
    }


def _stage_public_inputs(settings: Settings, paths: dict[str, Path]) -> dict[str, Any]:
    destination = settings.run_root / "seed_evidence/public_inputs"
    destination.mkdir(parents=True, exist_ok=True)
    receipts: dict[str, Any] = {}
    for split, source in (("train", paths["train_csv"]), ("test", paths["test_csv"])):
        # usecols is deliberate: local test files may carry historical labels, but this lane never
        # parses or copies them.
        frame = pd.read_csv(source, usecols=list(PUBLIC_COLUMNS))
        expected = TRAIN_ROWS if split == "train" else TEST_ROWS
        if len(frame) != expected:
            raise CampaignError(f"{split} public fields contain {len(frame)} rows, expected {expected}")
        target = destination / f"{split}_public.csv"
        frame.to_csv(target, index=False)
        receipts[split] = {"path": str(target), "rows": len(frame), "sha256": sha256_file(target)}
    for split in ("train", "test"):
        mountpoint = destination / f"{split}_geometry"
        if mountpoint.is_symlink():
            mountpoint.unlink()
        mountpoint.mkdir(exist_ok=True)
    atomic_json(
        destination / "manifest.json",
        {
            "public_columns": list(PUBLIC_COLUMNS),
            "target_columns_excluded": list(TARGETS),
            "test_labels_read": False,
            "files": receipts,
        },
    )
    return receipts


def _image_identity(image: str) -> str | None:
    try:
        return subprocess.check_output(
            ["docker", "image", "inspect", "--format", "{{.Id}}", image],
            text=True,
            timeout=30,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _sandbox_security_smoke(settings: Settings, paths: dict[str, Path]) -> dict[str, Any]:
    image_id = _image_identity(settings.image)
    if image_id is None:
        raise CampaignError(f"sandbox image is not built: {settings.image}")
    receipt_path = settings.run_root / "sandbox_receipts/security_smoke/receipt.json"
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text())
        if existing.get("image_digest") == image_id and all(existing.get("checks", {}).values()):
            return existing
    output = receipt_path.parent
    output.mkdir(parents=True, exist_ok=True)
    output.chmod(0o777)
    probe = settings.repo_root / "ops/nomad-feature-hunt/fixtures/malicious_probe.py"
    public = settings.run_root / "seed_evidence/public_inputs"
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--user",
        "65532:65532",
        "--pids-limit",
        "64",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=64m",
        "--mount",
        f"type=bind,src={probe.resolve()},dst=/probe.py,readonly",
        "--mount",
        f"type=bind,src={public.resolve()},dst=/inputs,readonly",
        "--mount",
        f"type=bind,src={output.resolve()},dst=/output",
        settings.image,
        "python",
        "/probe.py",
    ]
    result = _run_command(settings, command, cwd=settings.repo_root, timeout=60)
    if result.returncode != 0 or not receipt_path.exists():
        raise CampaignError(f"sandbox malicious smoke failed: {result.stderr[-1000:]}")
    receipt = json.loads(receipt_path.read_text())
    receipt.update(
        {
            "image_digest": image_id,
            "command_sha256": sha256_bytes(canonical_json(command)),
            "probe_sha256": sha256_file(probe),
        }
    )
    if not all(receipt.get("checks", {}).values()):
        raise CampaignError(f"sandbox malicious checks failed: {receipt.get('checks')}")
    atomic_json(receipt_path, receipt)
    return receipt


def _sandbox_harness_smoke(settings: Settings, paths: dict[str, Path]) -> dict[str, Any]:
    image_id = _image_identity(settings.image)
    if image_id is None:
        raise CampaignError(f"sandbox image is not built: {settings.image}")
    output = settings.run_root / "sandbox_receipts/harness_smoke"
    receipt_path = output / "receipt.json"
    generator = settings.repo_root / "ops/nomad-feature-hunt/fixtures/invariant_generator.py"
    harness = settings.repo_root / "ops/nomad-feature-hunt/sandbox_runner.py"
    generator_hash = sha256_file(generator)
    harness_hash = sha256_file(harness)
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text())
        if (
            existing.get("image_digest") == image_id
            and existing.get("generator_sha256") == generator_hash
            and existing.get("harness_sha256") == harness_hash
            and all(existing.get("invariances", {}).values())
        ):
            return existing
    output.mkdir(parents=True, exist_ok=True)
    output.chmod(0o777)
    command = docker_sandbox_command(
        image=settings.image,
        generator=generator,
        harness=harness,
        public_inputs=settings.run_root / "seed_evidence/public_inputs",
        train_geometry=paths["train_geometry"],
        test_geometry=paths["test_geometry"],
        output=output,
        real_sample_id=1,
    )
    result = _run_command(settings, command, cwd=settings.repo_root, timeout=300)
    required = [
        output / "train.parquet",
        output / "test.parquet",
        output / "rerun/train.parquet",
        output / "rerun/test.parquet",
        output / "invariance.json",
        output / "sandbox_security.json",
    ]
    if result.returncode != 0 or not all(path.exists() for path in required):
        raise CampaignError(f"sandbox harness smoke failed: {result.stderr[-1000:]}")
    train = pd.read_parquet(output / "train.parquet")
    test = pd.read_parquet(output / "test.parquet")
    rerun_train = pd.read_parquet(output / "rerun/train.parquet")
    rerun_test = pd.read_parquet(output / "rerun/test.parquet")
    invariances = json.loads((output / "invariance.json").read_text())
    security = json.loads((output / "sandbox_security.json").read_text())
    checks = {
        "train_rows_2400": len(train) == TRAIN_ROWS,
        "test_rows_600": len(test) == TEST_ROWS,
        "deterministic_train": train.equals(rerun_train),
        "deterministic_test": test.equals(rerun_test),
        "same_columns": train.columns.tolist() == test.columns.tolist(),
        "all_invariances": all(invariances.values()),
        "sandbox_security": all(security.values()),
    }
    if not all(checks.values()):
        raise CampaignError(f"sandbox harness smoke checks failed: {checks}")
    receipt = {
        "image_digest": image_id,
        "generator_sha256": generator_hash,
        "harness_sha256": harness_hash,
        "command_sha256": sha256_bytes(canonical_json(command)),
        "checks": checks,
        "invariances": invariances,
        "security": security,
        "matrix_hashes": {
            str(path.relative_to(output)): sha256_file(path)
            for path in required[:4]
        },
    }
    atomic_json(receipt_path, receipt)
    return receipt


def _gpu_dispatch_smoke(settings: Settings) -> dict[str, Any]:
    output = settings.run_root / "sandbox_receipts/gpu_dispatch_smoke"
    receipt_path = output / "receipt.json"
    worker = settings.repo_root / "nomad_feature_hunt/gpu_fit_worker.py"
    worker_hash = sha256_file(worker)
    dispatcher_hash = sha256_file(settings.repo_root / "nomad_feature_hunt/scoring.py")
    events_path = output / "events.jsonl"
    if receipt_path.exists() and events_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        chain = HashChain(events_path)
        if (
            existing.get("worker_sha256") == worker_hash
            and existing.get("dispatcher_sha256") == dispatcher_hash
            and existing.get("events_sha256") == sha256_file(events_path)
            and all(existing.get("checks", {}).values())
            and chain.verify()[0]
        ):
            return existing

    output.mkdir(parents=True, exist_ok=True)
    events_path.unlink(missing_ok=True)
    values = np.arange(400, dtype=np.float32).reshape(200, 2)
    target = np.linspace(0.1, 2.0, 200)
    training = np.arange(200) % 2 == 0
    job = GPUFitJob(values, target, training, ~training, iterations=2, seed=4219)
    executor = DualGPUExecutor(output)
    results = executor.fit_pair(job, job)
    events = executor.events.read()
    identities = {
        record["payload"]["host"]: record["payload"]["environment"]["nvidia_smi"]
        for record in events
        if record.get("event") == "gpu_fit_complete"
    }
    checks = {
        "hash_chain_valid": executor.events.verify()[0],
        "exactly_two_successes": len(events) == 2,
        "local_rtx_3090": "RTX 3090" in identities.get("local", ""),
        "xbabe1_rtx_4090": "RTX 4090" in identities.get("xbabe1", ""),
        "predictions_returned": [len(result[0]) for result in results] == [100, 100],
        "cpu_fallback_disabled": all(
            record["payload"].get("cpu_fallback") is False for record in events
        ),
    }
    if not all(checks.values()):
        raise CampaignError(f"dual-GPU dispatch smoke checks failed: {checks}")
    receipt = {
        "checks": checks,
        "identities": identities,
        "worker_sha256": worker_hash,
        "dispatcher_sha256": dispatcher_hash,
        "events_sha256": sha256_file(events_path),
    }
    atomic_json(receipt_path, receipt)
    return receipt


def _curated_sources(settings: Settings) -> list[Path]:
    relative = [
        Path("crystal360_schema.json"),
        Path("nomad_crystal360/schema.py"),
        Path("nomad_crystal360/constants.py"),
        Path("docs/atlas-hyperion-bakeoff.md"),
        Path("artifacts/atlas_hyperion_bakeoff/bundle/columns.json"),
        Path("artifacts/atlas_hyperion_bakeoff/bundle/source_families.csv"),
        Path("artifacts/atlas_hyperion_bakeoff/bundle/bundle_manifest.json"),
        Path("artifacts/atlas_hyperion_bakeoff/run/importance_observations.parquet"),
        Path("artifacts/atlas_hyperion_bakeoff/run/score_curve.csv"),
        Path("artifacts/atlas_hyperion_bakeoff/run/selected_columns.json"),
        Path("artifacts/atlas_hyperion_bakeoff/run/scores.json"),
        Path("artifacts/atlas_hyperion_bakeoff/run/freeze_manifest.json"),
    ]
    relative.extend(
        Path(f"artifacts/atlas_hyperion_bakeoff/run/ranking_{target}{suffix}.{extension}")
        for target in TARGETS
        for suffix in ("", "_selection_fold_0", "_selection_fold_1")
        for extension in ("csv", "parquet")
    )
    return [path for path in relative if (settings.repo_root / path).is_file()]


def _stage_jailgun_upload(settings: Settings) -> dict[str, Any]:
    upload = settings.run_root / "jailgun/upload"
    upload.mkdir(parents=True, exist_ok=True)
    selected: list[str] = []
    total = 0
    for relative in _curated_sources(settings):
        source = settings.repo_root / relative
        destination = upload / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        selected.append(relative.as_posix())
        total += destination.stat().st_size
    for index in range(1, EXPECTED_JAILGUN_TABS + 1):
        for extension, seed in (("md", "seed; replace with complete feature report\n"), ("json", "[]\n")):
            relative = Path(f"features/tab_{index:02d}.{extension}")
            _write_text(upload / relative, seed)
            selected.append(relative.as_posix())
            total += (upload / relative).stat().st_size
    manifest = upload / "include-manifest.txt"
    _write_text(manifest, "\n".join(selected) + "\n")
    task = upload / "task.txt"
    mapping = "\n".join(f"- tab {index}: {DOMAINS[index - 1].id} — {DOMAINS[index - 1].title}" for index in range(1, 11))
    _write_text(
        task,
        f"""This is a guarded NOMAD feature foundry. You are tab {{{{TAB_INDEX}}}} of {{{{TAB_COUNT}}}}.
Use only the domain assigned below. Study every supplied definition, formula, schema, ranking,
score curve, selected-column file, and manifest. Numeric row matrices and labels are intentionally absent.

{mapping}

Return exactly one source.tar.gz containing exactly these two nonempty files for your tab and no others:
features/tab_{{{{TAB_INDEX}}}}.md and features/tab_{{{{TAB_INDEX}}}}.json.
The JSON must be an array of exactly 50 genuinely distinct concepts. Each object must contain:
concept_id, domain, name, equation, symbols, inputs, parameters, units, normalization,
periodic_construction, invariances, missingness_policy, physical_interpretation,
citations_or_derivation, target_hypothesis, complexity, leakage_assessment,
falsification_test, microfeature_expansion, and implementation_guidance.
The Markdown must explain all 50 concepts, equations, executable microfeature expansions,
implementation guidance, and falsification plans. Do not use trivial powers, arbitrary bins, or
parameter padding; no base equation may yield more than 25 columns. Do not include labels, secrets,
credentials, browser state, prose outside the archive, patches, or edits to supplied evidence.
""",
    )
    config = upload / "jailgun.toml"
    _write_text(
        config,
        f"""[project]
name = "nomad-theory-feature-hunt"
repository = "local://nomad-theory-feature-hunt"

[browser]
chat_url = "https://chatgpt.com/"
model = "gpt-5.6"
tabs = 10
poll_interval_seconds = 5
completion_check_seconds = 15
submit_delay_seconds = 2
submit_jitter_seconds = 1
tar_wait_minutes = 360
profile_dir_env = "JAILGUN_CHROME_PROFILE_DIR"
state_dir_env = "JAILGUN_CHROME_STATE_DIR"
profile_registry_env = "JAILGUN_BROWSER_PROFILE_REGISTRY"

[paths]
artifacts_dir = "{(settings.run_root / 'jailgun/raw').as_posix()}"
downloads_dir_env = "JAILGUN_DOWNLOADS_DIR"

[source_archive]
enabled = true
repo_url_env = "JAILGUN_SOURCE_REPO_URL"
ref_name = "HEAD"
prefix = "source/"
archive_filename = "source.tar.gz"
delete_after_upload = true

[deploy]
enabled = false
dry_run = true
remote_host_env = "JAILGUN_REMOTE_HOST"
remote_dir_env = "JAILGUN_REMOTE_DIR"
remote_command_env = "JAILGUN_REMOTE_COMMAND"
remote_strip_components = 0
remote_cleanup_policy = "preserve-reset"
remote_status_poll_seconds = 30
remote_job_delay_seconds = 0
remote_job_jitter_seconds = 0

[prompt_policy]
deny_github_write_by_default = true
allow_info_prompts = true
allowed_repositories = []
""",
    )
    receipt = {
        "root": str(upload),
        "selected_files": selected,
        "selected_file_count": len(selected),
        "uncompressed_bytes": total,
        "manifest_sha256": sha256_file(manifest),
        "exclusions": ["numeric matrices", "row-level targets", "credentials", "browser state"],
    }
    atomic_json(settings.run_root / "jailgun/upload_receipt.json", receipt)
    return receipt


def _stage_research(settings: Settings) -> None:
    for round_number in range(1, 4):
        aspects = {
            "aspects": [
                {
                    "id": domain.id,
                    "title": domain.title,
                    "queries": list(domain.research_queries)
                    if round_number < 3
                    else [f"{domain.title} executable periodic crystal descriptors"],
                }
                for domain in DOMAINS
            ]
        }
        atomic_json(settings.run_root / f"research/aspects_round_{round_number}.json", aspects)


def preflight(settings: Settings) -> dict[str, Any]:
    _validate_run_id(settings.run_id)
    paths = _assert_inputs(settings)
    for directory in ARTIFACT_DIRS:
        (settings.run_root / directory).mkdir(parents=True, exist_ok=True)
    db, events = _campaign(settings)
    now = utc_now()
    db.execute(
        "INSERT OR IGNORE INTO campaign(run_id,created_at,state,max_wall_seconds,max_cost_usd) VALUES(?,?,?,?,?)",
        (settings.run_id, now, "preflight", MAX_WALL_SECONDS, MAX_COST_USD),
    )
    roles = role_specs()
    with db.connect() as connection:
        for role in roles:
            connection.execute(
                "INSERT OR IGNORE INTO roles(role_id,role_class,domain,wave,spec_json) VALUES(?,?,?,?,?)",
                (role["id"], role["class"], role["domain"], role["wave"], json.dumps(role, sort_keys=True)),
            )
    atomic_json(settings.run_root / "roles.json", roles)
    public = _stage_public_inputs(settings, paths)
    upload = _stage_jailgun_upload(settings)
    _stage_research(settings)
    registry = _registry_capacity()
    commands = {name: _command_exists(name) for name in ("jekko", "jailgun", "docker", "nvidia-smi", "ssh")}
    image_id = _image_identity(settings.image)
    sandbox_smoke = _sandbox_security_smoke(settings, paths) if image_id else None
    harness_smoke = _sandbox_harness_smoke(settings, paths) if image_id else None
    gpu_dispatch_smoke = (
        _gpu_dispatch_smoke(settings)
        if commands.get("nvidia-smi") and commands.get("ssh")
        else None
    )
    checks = {
        "commands": commands,
        "jailgun_registry": registry,
        "jnoccio_role_count": len(roles),
        "input_rows": {"train": TRAIN_ROWS, "test": TEST_ROWS},
        "atlas_columns": ATLAS_WIDTH,
        "public_inputs": public,
        "jailgun_upload": upload,
        "sandbox_image_digest": image_id,
        "sandbox_security_smoke": sandbox_smoke,
        "sandbox_harness_smoke": harness_smoke,
        "gpu_dispatch_smoke": gpu_dispatch_smoke,
        "budgets": {"wall_seconds": MAX_WALL_SECONDS, "cost_usd": MAX_COST_USD},
        "live_identity_probe_required_before_jailgun": True,
        "test_labels_used": False,
    }
    blockers: list[str] = []
    blockers.extend(f"missing command: {name}" for name, present in commands.items() if not present)
    if registry["capacity"] < EXPECTED_JAILGUN_TABS:
        blockers.append(
            f"Jailgun ready-account capacity {registry['capacity']} is below {EXPECTED_JAILGUN_TABS}"
        )
    if image_id is None:
        blockers.append(f"sandbox image is not built: {settings.image}")
    status = {"run_id": settings.run_id, "created_at": now, "checks": checks, "blockers": blockers, "ready": not blockers}
    atomic_json(settings.run_root / "preflight.json", status)
    events.append("preflight", status)
    if blockers:
        current = db.one("SELECT state,error FROM campaign WHERE run_id=?", (settings.run_id,))
        if current is None or current["state"] != "blocked" or not current["error"]:
            db.execute(
                "UPDATE campaign SET state=?,error=? WHERE run_id=?",
                ("blocked", "; ".join(blockers), settings.run_id),
            )
    return status


def _budget_guard(settings: Settings) -> None:
    db, _events = _campaign(settings)
    campaign = db.one("SELECT * FROM campaign WHERE run_id=?", (settings.run_id,))
    if campaign is None:
        raise CampaignError("campaign was not preflighted")
    budget_start = campaign["started_at"] or campaign["created_at"]
    started = pd.Timestamp(budget_start).timestamp()
    if time.time() - started >= int(campaign["max_wall_seconds"]):
        raise CampaignError("48-hour wall-clock budget exhausted")
    if float(campaign["measured_cost_usd"]) >= float(campaign["max_cost_usd"]):
        raise CampaignError("$500 measured-cost budget exhausted")


def _run_command(
    settings: Settings,
    command: list[str],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    _budget_guard(settings)
    _db, events = _campaign(settings)
    command_hash = sha256_bytes(canonical_json(command))
    events.append("command_started", {"argv_sha256": command_hash, "program": command[0], "cwd": str(cwd)})
    runtime_tmp = settings.nomad_root / "tmp/nomad_feature_hunt" / settings.run_id
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    process_env = os.environ.copy()
    process_env["TMPDIR"] = str(runtime_tmp)
    if env:
        process_env.update(env)
    result = subprocess.run(
        command,
        cwd=cwd,
        env=process_env,
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


def _run_research(settings: Settings) -> None:
    merged: dict[str, str] = {}
    db, events = _campaign(settings)
    for round_number in range(1, 4):
        output = settings.run_root / f"research/round_{round_number}.jsonl"
        if not output.exists():
            result = _run_command(
                settings,
                [
                    "jekko",
                    "research",
                    "--aspects",
                    str(settings.run_root / f"research/aspects_round_{round_number}.json"),
                    "--out",
                    str(output),
                    "--providers",
                    "openalex,crossref,arxiv",
                    "--queries-per-aspect",
                    "2",
                    "--per-query",
                    "3",
                ],
                cwd=settings.repo_root,
                timeout=3_600,
            )
            if result.returncode != 0:
                raise CampaignError(f"research round {round_number} failed: {result.stderr[-1000:]}")
        for line in output.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            digest = sha256_bytes(canonical_json(record))
            merged.setdefault(digest, json.dumps(record, sort_keys=True, separators=(",", ":")))
        events.append("research_round", {"round": round_number, "records_after_dedup": len(merged), "sha256": sha256_file(output)})
    evidence_path = settings.run_root / "research/evidence.jsonl"
    _write_text(evidence_path, "\n".join(merged.values()) + ("\n" if merged else ""))
    with db.connect() as connection:
        for index, (digest, line) in enumerate(sorted(merged.items()), start=1):
            record = json.loads(line)
            domain = str(record.get("aspect_id") or record.get("aspect") or "ALL")
            claim = str(record.get("title") or record.get("claim") or record.get("abstract") or "research evidence")
            connection.execute(
                "INSERT OR IGNORE INTO research_claims VALUES(?,?,?,?,?)",
                (f"research-{index:05d}", domain, claim, line, digest),
            )
    atomic_json(
        settings.run_root / "research/receipt.json",
        {"rounds": 3, "deduplicated_records": len(merged), "evidence_sha256": sha256_file(evidence_path)},
    )


def _memory_pack(db: CampaignDB, domain: str) -> dict[str, Any]:
    fingerprints = db.all(
        "SELECT formula_fingerprint,semantic_fingerprint,status,rejection_reason FROM microfeatures WHERE domain IN (?, 'ALL') LIMIT 500",
        (domain,),
    )
    failures = db.all(
        "SELECT memory_id,payload_json FROM memory_items WHERE kind='failure' AND domain IN (?, 'ALL') LIMIT 100",
        (domain,),
    )
    claims = db.all(
        "SELECT claim_id,claim,citation_json FROM research_claims WHERE domain IN (?, 'ALL') LIMIT 80",
        (domain,),
    )
    return {
        "existing_fingerprints": [dict(row) for row in fingerprints],
        "prior_failures": [{"memory_id": row["memory_id"], "payload": json.loads(row["payload_json"])} for row in failures],
        "research": [dict(row) for row in claims],
        "claimed_subdomains": [row["role_id"] for row in db.all("SELECT role_id FROM roles WHERE domain=? AND status IN ('running','complete')", (domain,))],
    }


def _role_prompt(role: dict[str, Any], memory: dict[str, Any]) -> str:
    common = f"""You are the stable Jnoccio role {role['id']} in a controller-owned NOMAD feature foundry.
Assigned class: {role['class']}; domain: {role['domain']} — {role['title']}.
Use the real 2,400-train/600-test Al-Ga-In oxide setting. The only targets are formation energy per
atom and bandgap; never request or use test labels. Existing fingerprints, claimed subdomains,
prior failures, and compact research are below. You may not overwrite memory or artifacts.
Return one JSON object and no prose. Every concept must carry: concept_id, domain, name, equation,
symbols, inputs, parameters, units, normalization, periodic_construction, invariances,
missingness_policy, physical_interpretation, citations_or_derivation, target_hypothesis,
complexity, leakage_assessment, falsification_test, microfeature_expansion, and
implementation_guidance. Ideas and equations are not validated features until executed.
Do not pad with powers, arbitrary bins, or near-duplicate parameter changes. A base equation may
expand to at most 25 scalar columns.
CONTROLLER_MEMORY={json.dumps(memory, sort_keys=True, separators=(',', ':'))}
"""
    role_class = role["class"]
    if role_class == "literature_scout":
        return common + "Produce a concepts array with at least 12 citation-grounded, implementable concepts and explicit claim-level citation metadata."
    if role_class == "theorist":
        return common + f"As the {role.get('specialty')}, derive a concepts array with at least 20 nontrivial NOMAD-specific concepts, equations, limits, and falsifiers."
    if role_class == "feature_implementer":
        return common + """Return {"generator_sha256":"000...000","generator_code":"...","microfeatures":[...]}. The generator must be deterministic Python, define featurize_structure(structure)->dict[str,float], and expose a CLI that writes train.parquet and test.parquet from public CSV and geometry roots. Use only numpy, pandas, scipy, networkx, pymatgen, spglib, dscribe, gudhi, matminer, ase, and the standard argparse/json/math/collections/pathlib/typing modules. Attempt at least 150 fully specified scalar microfeatures in this domain. Use 64 lowercase zeroes as the provisional generator_hash in every microfeature; the controller computes and binds the authoritative SHA-256 from the exact returned source. Include measured_results as {"status":"uncomputed"}; never invent scores."""
    if role_class == "experimental_analyst":
        return common + f"Return an analysis array of concrete, executable campaign tests from the {role.get('specialty')} perspective. Self-reported feature scores are forbidden."
    if role_class == "blind_judge":
        return common + f"Return a judgments array with accept/reject criteria and dissent from the blinded {role.get('specialty')} perspective. Do not infer statistical value without trusted scorer receipts."
    return common + "Return a memory_items array that separates reusable positive knowledge, negative results, unresolved conflicts, and exact fingerprints without changing controller memory."


def _record_attempt_start(db: CampaignDB, job_id: str, role: dict[str, Any], attempt: int, prompt_path: Path) -> None:
    prompt_hash = sha256_file(prompt_path)
    with db.connect() as connection:
        connection.execute(
            "INSERT INTO jobs(job_id,role_id,wave,prompt_sha256,prompt_path,status,attempts) "
            "VALUES(?,?,?,?,?,'running',?) ON CONFLICT(job_id) DO UPDATE SET "
            "prompt_sha256=excluded.prompt_sha256,prompt_path=excluded.prompt_path,"
            "status='running',attempts=excluded.attempts",
            (job_id, role["id"], role["wave"], prompt_hash, str(prompt_path), attempt + 1),
        )
        connection.execute(
            "INSERT OR REPLACE INTO attempts(job_id,attempt,started_at,prompt_sha256) VALUES(?,?,?,?)",
            (job_id, attempt, utc_now(), prompt_hash),
        )
        connection.execute(
            "INSERT OR REPLACE INTO leases(job_id,attempt,leased_at,status) VALUES(?,?,?,'leased')",
            (job_id, attempt, utc_now()),
        )
        connection.execute("UPDATE roles SET status='running' WHERE role_id=?", (role["id"],))


def _insert_concepts(db: CampaignDB, source: str, concepts: list[dict[str, Any]]) -> int:
    inserted = 0
    with db.connect() as connection:
        for concept in concepts:
            payload = json.dumps(concept, sort_keys=True, separators=(",", ":"))
            errors = validate_concept(concept)
            try:
                connection.execute(
                    "INSERT INTO concepts VALUES(?,?,?,?,?,?,?)",
                    (
                        concept.get("concept_id"),
                        source,
                        concept.get("domain"),
                        payload,
                        sha256_bytes(payload.encode()),
                        int(not errors),
                        "; ".join(errors) or None,
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                continue
    return inserted


def _router_cost(value: Any) -> float:
    if isinstance(value, dict):
        total = 0.0
        for key, item in value.items():
            if key in {"cost_usd", "total_cost_usd", "estimated_cost_usd"} and isinstance(
                item, (int, float)
            ):
                total += max(float(item), 0.0)
            elif isinstance(item, (dict, list)):
                total += _router_cost(item)
        return total
    if isinstance(value, list):
        return sum(_router_cost(item) for item in value)
    return 0.0


def _microfeature_deduplication_errors(
    db: CampaignDB, features: list[dict[str, Any]]
) -> list[str]:
    prior: list[dict[str, Any]] = []
    for row in db.all(
        "SELECT feature_id,payload_json FROM microfeatures ORDER BY feature_id"
    ):
        try:
            prior.append(json.loads(row["payload_json"]))
        except json.JSONDecodeError:
            return [f"stored microfeature {row['feature_id']} has invalid JSON"]

    errors: list[str] = []
    for feature in features:
        family = (
            feature.get("domain"),
            feature.get("concept_id"),
            feature.get("base_equation_id"),
        )
        fingerprint = formula_fingerprint(feature)
        tokens = semantic_tokens(feature)
        for other in prior:
            other_family = (
                other.get("domain"),
                other.get("concept_id"),
                other.get("base_equation_id"),
            )
            if family == other_family:
                continue
            if fingerprint == formula_fingerprint(other):
                errors.append(
                    f"{feature.get('feature_id')} repeats the canonical formula of "
                    f"{other.get('feature_id')}"
                )
                break
            other_tokens = semantic_tokens(other)
            similarity = semantic_similarity(feature, other)
            if min(len(tokens), len(other_tokens)) >= 8 and similarity >= 0.9:
                errors.append(
                    f"{feature.get('feature_id')} is semantically similar to "
                    f"{other.get('feature_id')} ({similarity:.3f})"
                )
                break
        prior.append(feature)
    return errors


def _ingest_role_result(
    settings: Settings,
    db: CampaignDB,
    role: dict[str, Any],
    job_id: str,
    attempt: int,
    result_path: Path,
) -> tuple[bool, list[str]]:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    text = str(result.get("assistant_text", ""))
    output_hash = sha256_bytes(text.encode())
    errors: list[str] = []
    payload: Any = None
    if not result.get("success"):
        errors.append(str(result.get("error") or "Jnoccio job failed"))
    else:
        try:
            payload = extract_json_payload(text)
            errors.extend(validate_role_payload(role["class"], payload, role["domain"]))
        except (ValueError, json.JSONDecodeError) as error:
            errors.append(str(error))

    if role["class"] == "feature_implementer" and isinstance(payload, dict):
        code = str(payload.get("generator_code", ""))
        code_hash = sha256_bytes(code.encode())
        errors.extend(static_check_generator(code))
        features = payload.get("microfeatures", []) if isinstance(payload.get("microfeatures"), list) else []
        feature_ids = [feature.get("feature_id") for feature in features if isinstance(feature, dict)]
        if len(feature_ids) != len(set(feature_ids)):
            errors.append("implementer payload contains duplicate feature IDs")
        existing_ids = {
            row["feature_id"]
            for row in db.all(
                f"SELECT feature_id FROM microfeatures WHERE feature_id IN ({','.join('?' for _ in feature_ids)})",
                tuple(feature_ids),
            )
        } if feature_ids else set()
        if existing_ids:
            errors.append(f"feature IDs already exist: {sorted(existing_ids)[:10]}")
        if not errors:
            errors.extend(_microfeature_deduplication_errors(db, features))
        if not errors:
            generator_path = settings.run_root / f"generators/{role['id']}.py"
            _write_text(generator_path, code)
            with db.connect() as connection:
                for feature in features:
                    feature = {**feature, "generator_hash": code_hash}
                    raw = json.dumps(feature, sort_keys=True, separators=(",", ":"))
                    connection.execute(
                        "INSERT INTO microfeatures(feature_id,concept_id,domain,base_equation_id,formula_fingerprint,semantic_fingerprint,generator_sha256,payload_json,status) VALUES(?,?,?,?,?,?,?,?,?)",
                        (
                            feature["feature_id"],
                            feature["concept_id"],
                            feature["domain"],
                            feature["base_equation_id"],
                            formula_fingerprint(feature),
                            semantic_fingerprint(feature),
                            code_hash,
                            raw,
                            "attempted",
                        ),
                    )
    elif isinstance(payload, dict) and isinstance(payload.get("concepts"), list) and not errors:
        concept_ids = [
            concept.get("concept_id")
            for concept in payload["concepts"]
            if isinstance(concept, dict)
        ]
        if len(concept_ids) != len(set(concept_ids)):
            errors.append("role payload contains duplicate concept IDs")
        elif concept_ids:
            placeholders = ",".join("?" for _ in concept_ids)
            if db.one(
                f"SELECT COUNT(*) n FROM concepts WHERE concept_id IN ({placeholders})",
                tuple(concept_ids),
            )["n"]:
                errors.append("one or more concept IDs already exist")
        if not errors and _insert_concepts(db, role["id"], payload["concepts"]) != len(
            payload["concepts"]
        ):
            errors.append("not all concepts were inserted")
    elif role["class"] == "blind_judge" and isinstance(payload, dict) and not errors:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        db.execute(
            "INSERT OR REPLACE INTO judgments VALUES(?,?,?,?,?,?)",
            (role["id"], role.get("specialty", role["id"]), "ALL", 0, raw, sha256_bytes(raw.encode())),
        )
    elif role["class"] == "memory_curator" and isinstance(payload, dict) and not errors:
        with db.connect() as connection:
            for index, item in enumerate(payload.get("memory_items", []), start=1):
                connection.execute(
                    "INSERT OR REPLACE INTO memory_items VALUES(?,?,?,?,?)",
                    (f"{role['id']}-{index:04d}", "curated", "ALL", json.dumps(item, sort_keys=True), utc_now()),
                )

    valid = not errors
    receipt = {
        "role_id": role["id"],
        "role_class": role["class"],
        "domain": role["domain"],
        "job_id": job_id,
        "attempt": attempt,
        "valid": valid,
        "errors": errors,
        "provider_id": result.get("provider_id"),
        "model_id": result.get("model_id"),
        "credential_user_id": result.get("credential_user_id"),
        "router_metadata": result.get("router_metadata"),
        "prompt_sha256": db.one("SELECT prompt_sha256 FROM jobs WHERE job_id=?", (job_id,))["prompt_sha256"],
        "output_sha256": output_hash,
        "result_sha256": sha256_file(result_path),
        "test_labels_used": False,
    }
    receipt_path = settings.run_root / f"receipts/jnoccio/{role['id']}.json"
    atomic_json(receipt_path, receipt)
    with db.connect() as connection:
        connection.execute(
            "UPDATE attempts SET finished_at=?,success=?,provider_id=?,model_id=?,credential_user_id=?,router_metadata_json=?,output_sha256=?,error=? WHERE job_id=? AND attempt=?",
            (
                utc_now(),
                int(valid),
                result.get("provider_id"),
                result.get("model_id"),
                result.get("credential_user_id"),
                json.dumps(result.get("router_metadata"), sort_keys=True),
                output_hash,
                "; ".join(errors) or None,
                job_id,
                attempt,
            ),
        )
        connection.execute(
            "UPDATE leases SET released_at=?,status=? WHERE job_id=? AND attempt=?",
            (utc_now(), "complete" if valid else "failed", job_id, attempt),
        )
        connection.execute(
            "UPDATE jobs SET status=? WHERE job_id=?", ("complete" if valid else "failed", job_id)
        )
        connection.execute(
            "UPDATE roles SET status=? WHERE role_id=?", ("complete" if valid else "failed", role["id"])
        )
        connection.execute(
            "INSERT OR REPLACE INTO role_receipts VALUES(?,?,?,?,?)",
            (role["id"], job_id, int(valid), str(receipt_path), sha256_file(receipt_path)),
        )
        cost = _router_cost(result.get("router_metadata"))
        if cost:
            connection.execute(
                "UPDATE campaign SET measured_cost_usd=measured_cost_usd+? WHERE run_id=?",
                (cost, settings.run_id),
            )
    if errors:
        memory_id = f"failure-{role['id']}-{attempt}"
        db.execute(
            "INSERT OR REPLACE INTO memory_items VALUES(?,?,?,?,?)",
            (memory_id, "failure", role["domain"], json.dumps({"errors": errors}), utc_now()),
        )
    return valid, errors


def _record_missing_result(db: CampaignDB, job_id: str, attempt: int) -> None:
    message = "Jnoccio result file was not produced"
    with db.connect() as connection:
        connection.execute(
            "UPDATE attempts SET finished_at=?,success=0,error=? WHERE job_id=? AND attempt=?",
            (utc_now(), message, job_id, attempt),
        )
        connection.execute(
            "UPDATE leases SET released_at=?,status='failed' WHERE job_id=? AND attempt=?",
            (utc_now(), job_id, attempt),
        )
        connection.execute("UPDATE jobs SET status='failed' WHERE job_id=?", (job_id,))


def _run_wave(settings: Settings, wave: int) -> None:
    db, events = _campaign(settings)
    roles = [json.loads(row["spec_json"]) for row in db.all("SELECT spec_json FROM roles WHERE wave=? ORDER BY role_id", (wave,))]
    statuses = {
        role["id"]: db.one(
            "SELECT status FROM roles WHERE role_id=?", (role["id"],)
        )["status"]
        for role in roles
    }

    def attempt_count(role: dict[str, Any]) -> int:
        return int(
            db.one("SELECT COUNT(*) n FROM attempts WHERE job_id=?", (role["id"],))["n"]
        )

    exhausted = [
        role
        for role in roles
        if statuses[role["id"]] != "complete" and attempt_count(role) >= MAX_RETRIES + 1
    ]
    pending = [
        role
        for role in roles
        if statuses[role["id"]] != "complete" and attempt_count(role) < MAX_RETRIES + 1
    ]
    if not pending:
        if exhausted:
            raise CampaignError(
                f"wave {wave} retains {len(exhausted)} invalid roles after one retry"
            )
        return
    for attempt in range(MAX_RETRIES + 1):
        attempt_roles = [role for role in pending if attempt_count(role) <= attempt]
        if not attempt_roles:
            continue
        job_payload: list[dict[str, Any]] = []
        attempt_dir = settings.run_root / f"queue/results/wave_{wave}/attempt_{attempt}"
        jobs_path = settings.run_root / f"queue/jobs/wave_{wave}_attempt_{attempt}.json"
        for role in attempt_roles:
            job_id = str(role["id"])
            prompt = _role_prompt(role, _memory_pack(db, str(role["domain"])))
            if attempt:
                prior_errors = [
                    row["error"]
                    for row in db.all(
                        "SELECT error FROM attempts WHERE job_id=? AND error IS NOT NULL "
                        "ORDER BY attempt",
                        (job_id,),
                    )
                ]
                prompt += (
                    "\nRETRY_VALIDATION_ERRORS="
                    + json.dumps(prior_errors, separators=(",", ":"))
                    + "\nCorrect every listed error. Return the full replacement JSON payload, "
                    "keep values concise, and do not omit required fields."
                )
            prompt_path = settings.run_root / f"queue/jobs/prompts/{job_id}_attempt_{attempt}.txt"
            _write_text(prompt_path, prompt)
            _record_attempt_start(db, job_id, role, attempt, prompt_path)
            job_payload.append({"id": job_id, "prompt": prompt, "priority": 1000 - wave})
        atomic_json(jobs_path, job_payload)
        result = _run_command(
            settings,
            [
                "jekko",
                "zyal-queue",
                "--provider",
                "jnoccio",
                "--model",
                "jnoccio-router",
                "--workers",
                str(JNOCCIO_WORKERS),
                "--lease-ttl-secs",
                "7200",
                "--run-id",
                f"{settings.run_id}-wave-{wave}-attempt-{attempt}",
                "--db",
                str(settings.db_path),
                "--jobs",
                str(jobs_path),
                "--results-dir",
                str(attempt_dir),
            ],
            cwd=settings.repo_root,
            timeout=7_300,
        )
        failed: list[dict[str, Any]] = []
        for role in attempt_roles:
            result_path = attempt_dir / f"{role['id']}.json"
            if not result_path.exists():
                _record_missing_result(db, str(role["id"]), attempt)
                failed.append(role)
                continue
            valid, _errors = _ingest_role_result(settings, db, role, str(role["id"]), attempt, result_path)
            if not valid:
                failed.append(role)
        events.append(
            "jnoccio_wave",
            {"wave": wave, "attempt": attempt, "roles": len(attempt_roles), "valid": len(attempt_roles) - len(failed), "command_returncode": result.returncode},
        )
        attempted_ids = {role["id"] for role in attempt_roles}
        pending = [role for role in pending if role["id"] not in attempted_ids] + failed
        if not pending:
            break
    retained = {role["id"] for role in exhausted + pending}
    if retained:
        raise CampaignError(
            f"wave {wave} retains {len(retained)} invalid roles after one retry"
        )


def run_jnoccio(settings: Settings) -> None:
    _run_research(settings)
    failures: list[str] = []
    db, events = _campaign(settings)
    for wave in range(1, 7):
        try:
            _run_wave(settings, wave)
        except CampaignError as error:
            failures.append(str(error))
            events.append("jnoccio_wave_incomplete", {"wave": wave, "error": str(error)})
    valid = db.one("SELECT COUNT(*) AS n FROM role_receipts WHERE valid=1")["n"]
    receipt = {
        "roles": int(valid),
        "expected": EXPECTED_JNOCCIO_ROLES,
        "complete": valid == EXPECTED_JNOCCIO_ROLES,
        "wave_failures": failures,
    }
    atomic_json(settings.run_root / "receipts/jnoccio_branch.json", receipt)
    events.append("jnoccio_branch_finished", receipt)
    if not receipt["complete"]:
        raise CampaignError(
            "Jnoccio branch did not produce exactly 70 valid role receipts: "
            + "; ".join(failures)
        )


def _probe_jailgun(settings: Settings, phase: str) -> dict[str, Any]:
    probe_script = settings.repo_root / "ops/nomad-feature-hunt/probe_chatgpt.mjs"
    path = settings.run_root / f"receipts/jailgun/{phase}_identity.json"
    result = _run_command(
        settings,
        ["node", str(probe_script), "--expected", "GPT-5.6", "--minimum-capacity", "10"],
        cwd=settings.repo_root,
        timeout=60,
    )
    if result.returncode != 0:
        atomic_json(path, {"phase": phase, "valid": False, "stderr": result.stderr[-2000:]})
        db, events = _campaign(settings)
        message = f"Jailgun {phase} visible GPT-5.6 identity probe failed"
        db.execute(
            "UPDATE campaign SET state='blocked',error=? WHERE run_id=?",
            (message, settings.run_id),
        )
        events.append("jailgun_identity_blocked", {"phase": phase, "stderr_sha256": sha256_bytes(result.stderr.encode())})
        raise CampaignError(message)
    try:
        probe = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise CampaignError(f"Jailgun {phase} identity probe returned invalid JSON") from error
    probe.update({"phase": phase, "valid": True, "receipt_sha256": sha256_bytes(canonical_json(probe))})
    atomic_json(path, probe)
    return probe


def _jailgun_archives(settings: Settings) -> list[Path]:
    root = settings.run_root / "jailgun/raw"
    return sorted(
        path for path in root.rglob("*.tar.gz") if path.is_file() and "source-manifest" not in path.name
    )


def _normalize_jailgun(settings: Settings, pre: dict[str, Any], post: dict[str, Any]) -> int:
    db, events = _campaign(settings)
    valid_tabs: set[int] = {
        int(str(row["tab_id"]).split("-")[-1])
        for row in db.all("SELECT tab_id FROM jailgun_tabs WHERE valid=1")
    }
    for archive in _jailgun_archives(settings):
        try:
            with tarfile.open(archive, "r:*") as handle:
                names = [member.name for member in handle.getmembers() if member.isfile()]
            tab_matches = {
                int(match.group(1))
                for name in names
                if (match := re.fullmatch(r"features/tab_(\d{2})\.(?:md|json)", name))
            }
            if len(tab_matches) != 1:
                continue
            tab = tab_matches.pop()
            expected = {f"features/tab_{tab:02d}.md", f"features/tab_{tab:02d}.json"}
            if set(names) != expected or not 1 <= tab <= 10 or tab in valid_tabs:
                continue
            destination = settings.run_root / f"jailgun/normalized/tab_{tab:02d}"
            extracted = safe_extract_tar_bytes(archive.read_bytes(), destination)
            json_path = destination / f"features/tab_{tab:02d}.json"
            markdown_path = destination / f"features/tab_{tab:02d}.md"
            concepts = json.loads(json_path.read_text(encoding="utf-8"))
            domain = DOMAINS[tab - 1].id
            if not isinstance(concepts, list) or len(concepts) != 50:
                continue
            errors = [error for concept in concepts for error in validate_concept(concept)]
            if any(concept.get("domain") != domain for concept in concepts) or errors:
                continue
            concept_ids = [concept["concept_id"] for concept in concepts]
            if len(concept_ids) != len(set(concept_ids)):
                continue
            placeholders = ",".join("?" for _ in concept_ids)
            if db.one(
                f"SELECT COUNT(*) n FROM concepts WHERE concept_id IN ({placeholders})",
                tuple(concept_ids),
            )["n"]:
                continue
            if not markdown_path.read_text(encoding="utf-8").strip():
                continue
            if _insert_concepts(db, f"jailgun-tab-{tab:02d}", concepts) != 50:
                continue
            archive_hash = sha256_file(archive)
            receipt = {
                "tab": tab,
                "domain": domain,
                "concepts": 50,
                "archive": str(archive),
                "archive_sha256": archive_hash,
                "files": {str(path.relative_to(destination)): sha256_file(path) for path in extracted},
                "pre_identity_sha256": pre["receipt_sha256"],
                "post_identity_sha256": post["receipt_sha256"],
                "fresh_conversation_id": post["fresh_conversation_ids"][tab - 1],
                "visible_model": "GPT-5.6",
                "fresh_conversation_required": True,
                "valid": True,
            }
            receipt_path = settings.run_root / f"receipts/jailgun/tab_{tab:02d}.json"
            atomic_json(receipt_path, receipt)
            db.execute(
                "INSERT OR REPLACE INTO jailgun_tabs VALUES(?,?,?,?,?,?,?,?,?)",
                (f"tab-{tab:02d}", domain, pre["receipt_sha256"], post["receipt_sha256"], archive_hash, 50, 1, 0, str(receipt_path)),
            )
            valid_tabs.add(tab)
        except (OSError, tarfile.TarError, ValueError, json.JSONDecodeError):
            continue
    events.append("jailgun_normalized", {"valid_tabs": sorted(valid_tabs), "valid_concepts": len(valid_tabs) * 50})
    return len(valid_tabs)


def run_jailgun(
    settings: Settings, pre_identity: dict[str, Any] | None = None
) -> None:
    pre = pre_identity if pre_identity is not None else _probe_jailgun(settings, "pre")
    upload = settings.run_root / "jailgun/upload"
    downloads = settings.run_root / "jailgun/downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    jailgun_env = {"JAILGUN_DOWNLOADS_DIR": str(downloads)}
    result = _run_command(
        settings,
        [
            "jailgun",
            "jailhard",
            "--tabs",
            "10",
            "--config",
            str(upload / "jailgun.toml"),
            "--task-file",
            str(upload / "task.txt"),
            "--include-manifest",
            str(upload / "include-manifest.txt"),
            "--max-bytes",
            str(20 * 1024 * 1024),
            "--no-apply",
            ".",
        ],
        cwd=upload,
        timeout=22_000,
        env=jailgun_env,
    )
    post = _probe_jailgun(settings, "post")
    fresh = sorted(set(post.get("conversation_ids", [])) - set(pre.get("conversation_ids", [])))
    post["fresh_conversation_ids"] = fresh
    post["receipt_sha256"] = sha256_bytes(canonical_json({key: value for key, value in post.items() if key != "receipt_sha256"}))
    atomic_json(settings.run_root / "receipts/jailgun/post_identity.json", post)
    if len(fresh) < EXPECTED_JAILGUN_TABS:
        raise CampaignError(f"Jailgun opened only {len(fresh)}/10 provably fresh conversations")
    tabs = _normalize_jailgun(settings, pre, post)
    if result.returncode != 0 or tabs != EXPECTED_JAILGUN_TABS:
        # Invalid tabs may be retried once, but never substituted with Jnoccio. The current Jailgun
        # CLI batches tabs, so a retry is another fresh batch and normalization keeps first valid tab.
        retry = _run_command(
            settings,
            [
                "jailgun",
                "jailhard",
                "--tabs",
                "10",
                "--config",
                str(upload / "jailgun.toml"),
                "--task-file",
                str(upload / "task.txt"),
                "--include-manifest",
                str(upload / "include-manifest.txt"),
                "--max-bytes",
                str(20 * 1024 * 1024),
                "--no-apply",
                ".",
            ],
            cwd=upload,
            timeout=22_000,
            env=jailgun_env,
        )
        post = _probe_jailgun(settings, "post_retry")
        fresh = sorted(set(post.get("conversation_ids", [])) - set(pre.get("conversation_ids", [])))
        post["fresh_conversation_ids"] = fresh
        post["receipt_sha256"] = sha256_bytes(canonical_json({key: value for key, value in post.items() if key != "receipt_sha256"}))
        atomic_json(settings.run_root / "receipts/jailgun/post_retry_identity.json", post)
        tabs = _normalize_jailgun(settings, pre, post)
        if retry.returncode != 0 or tabs != EXPECTED_JAILGUN_TABS:
            raise CampaignError(f"Jailgun produced {tabs}/10 valid tabs after one fresh retry")
    atomic_json(
        settings.run_root / "receipts/jailgun_branch.json",
        {"tabs": tabs, "concepts": tabs * 50, "complete": tabs == 10, "jnoccio_substitution": False},
    )


def _run_sandboxes(settings: Settings) -> dict[str, Any]:
    paths = _assert_inputs(settings)
    db, events = _campaign(settings)
    public_inputs = settings.run_root / "seed_evidence/public_inputs"
    harness = settings.repo_root / "ops/nomad-feature-hunt/sandbox_runner.py"
    baseline_train = np.load(paths["atlas_bundle"] / "train.npy", mmap_mode="r", allow_pickle=False)
    baseline_test = np.load(paths["atlas_bundle"] / "test.npy", mmap_mode="r", allow_pickle=False)
    train_ids = np.load(paths["atlas_bundle"] / "train_ids.npy", allow_pickle=False)
    test_ids = np.load(paths["atlas_bundle"] / "test_ids.npy", allow_pickle=False)
    batches: dict[str, Any] = {}
    for generator in sorted((settings.run_root / "generators").glob("*.py")):
        batch_id = generator.stem
        existing = db.one("SELECT valid FROM matrices WHERE batch_id=?", (batch_id,))
        if existing and existing["valid"]:
            continue
        receipt_path = settings.run_root / f"sandbox_receipts/{batch_id}.json"
        if receipt_path.exists():
            continue
        errors = static_check_generator(generator.read_text(encoding="utf-8"))
        if errors:
            atomic_json(
                receipt_path,
                {
                    "batch_id": batch_id,
                    "valid": False,
                    "errors": errors,
                    "generator_sha256": sha256_file(generator),
                    "container_executed": False,
                },
            )
            db.execute(
                "INSERT OR REPLACE INTO memory_items VALUES(?,?,?,?,?)",
                (f"sandbox-{batch_id}", "failure", "ALL", json.dumps({"errors": errors}), utc_now()),
            )
            continue
        output = settings.run_root / f"microfeature_matrices/{batch_id}"
        output.mkdir(parents=True, exist_ok=True)
        output.chmod(0o777)
        command = docker_sandbox_command(
            image=settings.image,
            generator=generator,
            harness=harness,
            public_inputs=public_inputs,
            train_geometry=paths["train_geometry"],
            test_geometry=paths["test_geometry"],
            output=output,
            real_sample_id=1,
        )
        result = _run_command(settings, command, cwd=settings.repo_root, timeout=7_200)
        if result.returncode != 0:
            errors.append(f"sandbox exited {result.returncode}: {result.stderr[-1000:]}")
            atomic_json(
                receipt_path,
                {
                    "batch_id": batch_id,
                    "valid": False,
                    "errors": errors,
                    "generator_sha256": sha256_file(generator),
                    "container_executed": True,
                },
            )
            db.execute(
                "INSERT OR REPLACE INTO memory_items VALUES(?,?,?,?,?)",
                (f"sandbox-{batch_id}", "failure", "ALL", json.dumps({"errors": errors}), utc_now()),
            )
            continue
        try:
            validated = validate_matrix_pair(
                output / "train.parquet",
                output / "test.parquet",
                expected_train_ids=train_ids,
                expected_test_ids=test_ids,
                rerun_train_path=output / "rerun/train.parquet",
                rerun_test_path=output / "rerun/test.parquet",
                invariance_path=output / "invariance.json",
                baseline_train=baseline_train,
                baseline_test=baseline_test,
            )
            feature_rows = db.all("SELECT feature_id FROM microfeatures WHERE generator_sha256=? AND status='attempted' ORDER BY feature_id", (sha256_file(generator),))
            declared = {row["feature_id"] for row in feature_rows}
            if declared == set(validated.columns):
                image_id = subprocess.check_output(
                    ["docker", "image", "inspect", "--format", "{{.Id}}", settings.image], text=True, timeout=30
                ).strip()
                atomic_json(
                    receipt_path,
                    {
                        "batch_id": batch_id,
                        "generator_sha256": sha256_file(generator),
                        "docker_image": settings.image,
                        "docker_image_digest": image_id,
                        "dependency_lock_sha256": sha256_file(settings.repo_root / "ops/nomad-feature-hunt/requirements.lock"),
                        "docker_command_sha256": sha256_bytes(canonical_json(command)),
                        **validated.receipt,
                    },
                )
                db.execute(
                    "INSERT OR REPLACE INTO matrices VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        batch_id,
                        next((d.id for d in DOMAINS if d.id.lower() in batch_id), "ALL"),
                        str(output / "train.parquet"),
                        str(output / "test.parquet"),
                        sha256_file(output / "train.parquet"),
                        sha256_file(output / "test.parquet"),
                        len(validated.columns),
                        1,
                        str(receipt_path),
                    ),
                )
                batches[batch_id] = validated
                with db.connect() as connection:
                    for column in validated.columns:
                        connection.execute(
                            "UPDATE microfeatures SET status='validated',numeric_signature=?,value_sha256=? WHERE feature_id=?",
                            (
                                validated.receipt["numeric_signatures_64"].get(column),
                                validated.receipt["value_sha256"][column],
                                column,
                            ),
                        )
            else:
                errors.append("declared microfeature IDs do not exactly match executable matrix columns")
        except (MatrixValidationError, FileNotFoundError, ValueError) as error:
            errors.append(str(error))
        if errors:
            atomic_json(receipt_path, {"batch_id": batch_id, "valid": False, "errors": errors, "generator_sha256": sha256_file(generator)})
            db.execute(
                "INSERT OR REPLACE INTO memory_items VALUES(?,?,?,?,?)",
                (f"sandbox-{batch_id}", "failure", "ALL", json.dumps({"errors": errors}), utc_now()),
            )
    events.append("sandboxes_finished", {"validated_batches": len(batches)})
    return batches


def run_fusion(settings: Settings) -> None:
    jnoccio = settings.run_root / "receipts/jnoccio_branch.json"
    jailgun = settings.run_root / "receipts/jailgun_branch.json"
    if not jnoccio.exists() or not jailgun.exists():
        raise CampaignError("fusion requires valid receipts from both concurrent branches")
    batches = _run_sandboxes(settings)
    if batches:
        report = score_batches(
            atlas_bundle=settings.repo_root / "artifacts/atlas_hyperion_bakeoff/bundle",
            batches=batches,
            output_dir=settings.run_root / "scoring",
        )
        db, events = _campaign(settings)
        with db.connect() as connection:
            for row in report["confirmation"]:
                identifier = f"{row['target']}:{row['batch_id']}"
                connection.execute(
                    "INSERT OR REPLACE INTO experiments VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        identifier,
                        row["target"],
                        "confirmation_5fold_400_tree",
                        row["batch_id"],
                        row["feature_count"],
                        row["rmsle"],
                        row["atlas_lift"],
                        row["control_809_lift"],
                        json.dumps(row, sort_keys=True),
                    ),
                )
        events.append("scoring_finished", {"score_report_sha256": sha256_file(settings.run_root / "scoring/score_report.json")})


def run_campaign(settings: Settings, *, resume: bool = False) -> None:
    status = preflight(settings)
    if not status["ready"]:
        raise CampaignError("preflight blockers: " + "; ".join(status["blockers"]))
    pre_identity = _probe_jailgun(settings, "pre")
    db, events = _campaign(settings)
    db.execute(
        "UPDATE campaign SET state='running',started_at=COALESCE(started_at,?),error=NULL WHERE run_id=?",
        (utc_now(), settings.run_id),
    )
    events.append("campaign_started" if not resume else "campaign_resumed", {"run_id": settings.run_id})
    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            pool.submit(run_jnoccio, settings): "jnoccio",
            pool.submit(run_jailgun, settings, pre_identity): "jailgun",
        }
        for future in concurrent.futures.as_completed(futures):
            branch = futures[future]
            try:
                future.result()
            except Exception as error:
                failures.append(f"{branch}: {error}")
    if failures:
        db.execute("UPDATE campaign SET state='incomplete',error=? WHERE run_id=?", ("; ".join(failures), settings.run_id))
        events.append("campaign_incomplete", {"failures": failures})
        raise CampaignError("; ".join(failures))
    run_fusion(settings)
    report = verify_campaign(settings)
    db.execute(
        "UPDATE campaign SET state=?,error=? WHERE run_id=?",
        ("complete" if report["complete"] else "incomplete", None if report["complete"] else "; ".join(report["missing"]), settings.run_id),
    )


def status_campaign(settings: Settings) -> dict[str, Any]:
    if not settings.db_path.exists():
        return {"run_id": settings.run_id, "state": "not_preflighted"}
    db, events = _campaign(settings)
    campaign = db.one("SELECT * FROM campaign WHERE run_id=?", (settings.run_id,))
    chain_valid, chain_error = events.verify()
    counts = {
        "roles_total": db.one("SELECT COUNT(*) n FROM roles")["n"],
        "role_receipts_valid": db.one("SELECT COUNT(*) n FROM role_receipts WHERE valid=1")["n"],
        "jailgun_tabs_valid": db.one("SELECT COUNT(*) n FROM jailgun_tabs WHERE valid=1")["n"],
        "jailgun_concepts": db.one("SELECT COALESCE(SUM(concepts),0) n FROM jailgun_tabs WHERE valid=1")["n"],
        "features_attempted": db.one("SELECT COUNT(*) n FROM microfeatures")["n"],
        "features_validated": db.one("SELECT COUNT(*) n FROM microfeatures WHERE status='validated'")["n"],
        "matrices_valid": db.one("SELECT COUNT(*) n FROM matrices WHERE valid=1")["n"],
        "experiments": db.one("SELECT COUNT(*) n FROM experiments")["n"],
    }
    return {
        "run_id": settings.run_id,
        "state": campaign["state"] if campaign else "unknown",
        "error": campaign["error"] if campaign else None,
        "counts": {key: int(value) for key, value in counts.items()},
        "hash_chain_valid": chain_valid,
        "hash_chain_error": chain_error,
    }


def _artifact_hashes(settings: Settings) -> dict[str, str]:
    excluded = {
        settings.db_path.resolve(),
        (settings.run_root / "final_hashes/manifest.json").resolve(),
    }
    files = [
        path
        for path in settings.run_root.rglob("*")
        if path.is_file() and path.resolve() not in excluded and not path.name.endswith("-wal") and not path.name.endswith("-shm")
    ]
    return {str(path.relative_to(settings.run_root)): sha256_file(path) for path in sorted(files)}


def verify_campaign(settings: Settings) -> dict[str, Any]:
    state = status_campaign(settings)
    if state["state"] == "not_preflighted":
        return {"run_id": settings.run_id, "complete": False, "missing": ["campaign preflight"]}
    db, events = _campaign(settings)
    missing: list[str] = []
    counts = state["counts"]
    if counts["roles_total"] != EXPECTED_JNOCCIO_ROLES or counts["role_receipts_valid"] != EXPECTED_JNOCCIO_ROLES:
        missing.append("exactly 70 distinct valid Jnoccio role receipts")
    if counts["jailgun_tabs_valid"] != EXPECTED_JAILGUN_TABS:
        missing.append("exactly 10 valid Jailgun tab receipts")
    if counts["jailgun_concepts"] != EXPECTED_JAILGUN_CONCEPTS:
        missing.append("exactly 500 schema-valid Jailgun concepts")
    if counts["features_attempted"] < MIN_ATTEMPTED_FEATURES:
        missing.append("at least 1,500 attempted executable microfeatures")
    if counts["features_validated"] < MIN_VALIDATED_FEATURES:
        missing.append("at least 1,000 validated novel executable columns")
    domain_counts = {
        domain.id: db.one("SELECT COUNT(*) n FROM microfeatures WHERE domain=? AND status='validated'", (domain.id,))["n"]
        for domain in DOMAINS
    }
    underrepresented = [domain for domain, count in domain_counts.items() if count < MIN_VALIDATED_PER_DOMAIN]
    if underrepresented:
        missing.append(f"at least 50 validated columns in every domain (missing: {underrepresented})")
    duplicate_formulas = db.all(
        "SELECT base_equation_id,COUNT(*) n FROM microfeatures WHERE status='validated' GROUP BY base_equation_id HAVING COUNT(*)>25"
    )
    if duplicate_formulas:
        missing.append("base-equation/canonical-formula expansion cap")
    chain_valid, chain_error = events.verify()
    if not chain_valid:
        missing.append(f"valid hash-chained JSONL: {chain_error}")
    score_path = settings.run_root / "scoring/score_report.json"
    score_report: dict[str, Any] | None = None
    if score_path.exists():
        score_report = json.loads(score_path.read_text())
        targets_present = set(score_report.get("winners", {}))
        if targets_present != set(TARGETS):
            missing.append("complete per-target RMSLE/lift table")
        if score_report.get("protocol", {}).get("test_labels_used") is not False:
            missing.append("proof that scoring never used test labels")
    else:
        missing.append("trusted GPU score report with per-target RMSLE and lift")
    matrix_receipts = db.all("SELECT receipt_path FROM matrices WHERE valid=1")
    if not matrix_receipts:
        missing.append("generator, environment, matrix, and invariance hashes")
    judgments = db.one("SELECT COUNT(*) n FROM judgments")["n"]
    if judgments < 4:
        missing.append("four complete blind-judgment hashes")
    hashes_before_report = _artifact_hashes(settings)
    verification_path = settings.run_root / "verification.json"
    artifact_hash_count = len(hashes_before_report) + int(not verification_path.exists())
    final_hashes = settings.run_root / "final_hashes/manifest.json"
    report = {
        "run_id": settings.run_id,
        "verified_at": utc_now(),
        "complete": not missing,
        "missing": missing,
        "counts": counts,
        "validated_by_domain": {key: int(value) for key, value in domain_counts.items()},
        "controls": {
            "atlas_target_winners": ATLAS_TARGET_WINNERS,
            "atlas_mean": ATLAS_WINNER_MEAN,
            "existing_809": EXISTING_809_CONTROLS,
            "existing_809_mean": EXISTING_809_MEAN,
        },
        "score_report": score_report,
        "declarations": {
            "new_features_beat_atlas": score_report.get("beats_atlas_winner_each_target") if score_report else None,
            "new_features_beat_existing_809": score_report.get("beats_existing_809_each_target") if score_report else None,
            "labeled_test_access": False,
            "hidden_label_scoring": False,
            "automatic_merge_into_nomad_crystal360": False,
        },
        "hash_chain_valid": chain_valid,
        "artifact_hash_count": artifact_hash_count,
    }
    atomic_json(verification_path, report)
    hashes = _artifact_hashes(settings)
    if len(hashes) != artifact_hash_count:
        raise CampaignError("artifact set changed while verification hashes were being frozen")
    # Write the hash manifest last; it is deliberately excluded from its own content.
    atomic_json(final_hashes, {"run_id": settings.run_id, "files": hashes})
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
    parser = argparse.ArgumentParser(description="NOMAD 70-agent theoretical feature foundry")
    parser.add_argument("command", choices=("preflight", "run", "resume", "status", "verify", "jnoccio", "jailgun", "fusion", "sandbox"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--inbox-root", default=str(DEFAULT_INBOX_ROOT))
    parser.add_argument("--nomad-root", default=str(DEFAULT_NOMAD_ROOT))
    parser.add_argument("--image", default="nomad-feature-sandbox:2026-07-18")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = _settings_from_args(args)
    try:
        if args.command == "preflight":
            result = preflight(settings)
        elif args.command == "run":
            run_campaign(settings)
            result = verify_campaign(settings)
        elif args.command == "resume":
            run_campaign(settings, resume=True)
            result = verify_campaign(settings)
        elif args.command == "status":
            result = status_campaign(settings)
        elif args.command == "verify":
            result = verify_campaign(settings)
        elif args.command == "jnoccio":
            run_jnoccio(settings)
            result = status_campaign(settings)
        elif args.command == "jailgun":
            run_jailgun(settings)
            result = status_campaign(settings)
        elif args.command == "fusion":
            run_fusion(settings)
            result = status_campaign(settings)
        else:
            result = {"validated_batches": len(_run_sandboxes(settings))}
        print(json.dumps(result, indent=2, sort_keys=True))
        if args.command in {"verify", "run", "resume"} and not result.get("complete", False):
            return 2
        if args.command == "preflight" and not result.get("ready", False):
            return 2
        return 0
    except (CampaignError, subprocess.TimeoutExpired, OSError, ValueError) as error:
        print(json.dumps({"run_id": settings.run_id, "error": str(error), "complete": False}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
