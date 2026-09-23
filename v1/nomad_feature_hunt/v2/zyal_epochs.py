"""NOMAD ZYAL v2.1 ten-epoch campaign controller.

This module is intentionally isolated from the v2.0 controller.  It owns the
ten-epoch roster, multi-user Fusion accounting, sealed confirmation protocol,
and promotion manifest, while reusing the trusted v2 kernels and validators.
It never reads a credential file: profile discovery is based only on the
presence of ``llm.env`` and Fusion is the sole credential router.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import urllib.request
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Protocol, Sequence

import numpy as np

from nomad_feature_hunt.ledger import HashChain, atomic_json, sha256_file, utc_now

from .constants import DOMAIN_KERNELS, DOMAINS, TARGETS
from .schemas import (
    FAMILY_FIELDS,
    OUTPUT_FIELDS,
    PARAMETER_FIELDS,
    SPEC_FIELDS,
    SchemaError,
    canonical_json,
    parse_strict_json,
    validate_family_card,
    validate_feature_spec,
)
from .security import static_check_plugin


CAMPAIGN_VERSION = "2.1"
EPOCHS = 10
ROLES_PER_EPOCH = 36
EXPECTED_JNOCCIO_ROLES = EPOCHS * ROLES_PER_EPOCH
MAX_ATTEMPTS_PER_ROLE = 2
MAX_JNOCCIO_ATTEMPTS = EXPECTED_JNOCCIO_ROLES * MAX_ATTEMPTS_PER_ROLE
MAX_COST_USD = 2_000.0
JNOCCIO_MIN_DEBIT_USD = 2.50

PROMPT_LIMIT_BYTES = 12 * 1024
OUTPUT_LIMIT_BYTES = 20 * 1024
PLUGIN_LIMIT_BYTES = 20 * 1024
TRAIN_ROWS = 2_400
TEST_ROWS = 600
BASELINE_REGISTRY_COLUMNS = 10_800
BASELINE_ZYAL_COLUMNS = 831
MIN_NEW_EXECUTED_COLUMNS = 7_000
MIN_NOVEL_VALID_COLUMNS = 3_000
MIN_VALID_PER_DOMAIN = 200
MIN_BASE_FAMILIES = 160
CURRENT_CHAMPION_MEAN_RMSLE = 0.0495014095
CONFIRMATION_SEEDS = (7_919, 104_729)
CONFIRMATION_FOLDS = 5
CONFIRMATION_TREES = 400
SCREEN_SEEDS = (1701, 2909, 4219)
SCREEN_TREES = 150
GENETIC_POPULATION = 24
GENETIC_GENERATIONS = 10
MAX_CONFIRMATION_VIEWS_PER_TARGET = 8

DEFAULT_NOMAD_ROOT = Path("/home/ubuntu/nomad")
DEFAULT_INBOX_ROOT = Path(
    "/home/ubuntu/nomad/artifacts/nomad_theory_feature_hunt/v2/inbox"
)
DEFAULT_USERS_ROOT = Path("/home/ubuntu/.jekko/users")
DEFAULT_SYNCHRONIZER = Path("/home/ubuntu/.jekko/bin/jnoccio-sync-users.sh")
DEFAULT_HEALTH_URL = "http://127.0.0.1:4317/health"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,63}$")

ARTIFACT_DIRS = (
    "inputs/baseline",
    "inputs/controller",
    "memory/negative",
    "novelty",
    "prompts",
    "queue/jobs",
    "raw_responses",
    "families",
    "specs",
    "plugins",
    "matrices/temporary",
    "matrices/validated",
    "score_curves",
    "reports/top50",
    "genetic/populations",
    "confirmation/sealed",
    "judgments",
    "receipts/router_pool",
    "receipts/utilization",
    "receipts/epochs",
    "receipts/features",
    "receipts/genetic",
    "receipts/confirmation",
    "promotion",
    "final_manifests",
)

ROLE_COUNTS = {
    "domain_architect": 10,
    "domain_spec_builder": 10,
    "target_exploiter": 6,
    "cross_family_synthesizer": 4,
    "bounded_plugin_writer": 2,
    "adversarial_tester": 2,
    "blind_judge": 2,
}

RECEIPT_TYPES = frozenset(
    {
        "router_pool_snapshot",
        "per_user_utilization",
        "epoch_result",
        "top_feature_record",
        "genetic_reduction_history",
        "sealed_confirmation_result",
    }
)

_SECRET_KEY_RE = re.compile(
    r"(?:^|_)(?:api_?key|access_?token|refresh_?token|authorization|password|"
    r"credential_?value|private_?key|developer_?key|secret)(?:$|_)",
    re.IGNORECASE,
)
_SECRET_VALUE_RE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bBearer\s+[A-Za-z0-9._~-]{12,}|"
    r"\bsk-[A-Za-z0-9_-]{16,})"
)
_ROUTER_METADATA_KEYS = frozenset(
    {
        "attempts",
        "cost_usd",
        "credential_user_id",
        "eligible_slots",
        "estimated_cost_usd",
        "fallback_count",
        "latency_ms",
        "model",
        "model_id",
        "provider",
        "provider_id",
        "rate_limit_count",
        "rate_limited",
        "rebalanced",
        "request_id",
        "route",
        "slot",
        "slot_count",
        "total_cost_usd",
        "user_id",
    }
)


class CampaignError(RuntimeError):
    """A fail-closed v2.1 campaign contract violation."""


class BudgetError(CampaignError):
    """A conservative attempt or dollar ceiling was exceeded."""


class ReceiptError(CampaignError):
    """A receipt was malformed or contained credential material."""


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    run_id: str
    nomad_root: Path = DEFAULT_NOMAD_ROOT
    inbox_root: Path = DEFAULT_INBOX_ROOT
    users_root: Path = DEFAULT_USERS_ROOT
    synchronizer: Path = DEFAULT_SYNCHRONIZER
    health_url: str = DEFAULT_HEALTH_URL
    baseline_columns_path: Path | None = None
    zyal_summary_path: Path | None = None
    image: str = "nomad-feature-sandbox:2026-07-18"

    def __post_init__(self) -> None:
        if not RUN_ID_RE.fullmatch(self.run_id):
            raise CampaignError("run_id must contain 3-64 safe filename characters")
        if not self.run_root.resolve().is_relative_to(self.nomad_root.resolve()):
            raise CampaignError("campaign storage must remain below the NOMAD root")

    @property
    def run_root(self) -> Path:
        return self.inbox_root / f"zyal10-final-{self.run_id}"

    @property
    def state_path(self) -> Path:
        return self.run_root / "campaign.sqlite3"

    @property
    def events_path(self) -> Path:
        return self.run_root / "events.jsonl"


@dataclass(frozen=True)
class PoolReconciliation:
    receipt: dict[str, Any]
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class BudgetSummary:
    ceiling_usd: float
    debited_usd: float
    reserved_usd: float
    available_usd: float
    attempts: int
    reported_cost_usd: float = 0.0


@dataclass(frozen=True)
class PhaseResult:
    receipt_type: str
    payload: dict[str, Any]
    receipt_path: Path | None = None


class PhaseBackend(Protocol):
    """Backend boundary for controller-owned scientific phase execution."""

    def execute(self, settings: Settings, phase: str) -> PhaseResult | dict[str, Any]: ...


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if not slug:
        raise ValueError("identifier has no safe slug characters")
    return slug


def epoch_role_specs(epoch: int) -> list[dict[str, Any]]:
    """Return one stable 36-role epoch roster.

    Dispatch group one has 24 dependency-ready jobs (architects, adaptive
    designers, plugin writers, and adversarial testers), matching the largest
    wave in the campaign.  Builders wait for current FamilyCards and blind
    judges wait for controller receipts.
    """

    if epoch not in range(1, EPOCHS + 1):
        raise ValueError("epoch must be between 1 and 10")
    prefix = f"zyal10.e{epoch:02d}"
    roles: list[dict[str, Any]] = []
    for domain in DOMAINS:
        roles.append(
            {
                "id": f"{prefix}.architect-{domain.id.casefold()}",
                "class": "domain_architect",
                "epoch": epoch,
                "domain": domain.id,
                "dispatch_group": 1,
                "returns": {"family_cards": 3},
            }
        )
    for index in range(6):
        target = TARGETS[index % len(TARGETS)]
        roles.append(
            {
                "id": f"{prefix}.exploiter-{index + 1:02d}",
                "class": "target_exploiter",
                "epoch": epoch,
                "domain": "ALL",
                "target": target,
                "dispatch_group": 1,
                "returns": {"feature_specs": 2},
                "feedback": "categorical_only",
            }
        )
    for index in range(4):
        roles.append(
            {
                "id": f"{prefix}.synthesizer-{index + 1:02d}",
                "class": "cross_family_synthesizer",
                "epoch": epoch,
                "domain": "ALL",
                "dispatch_group": 1,
                "returns": {"feature_specs": 2},
                "feedback": "categorical_only",
            }
        )
    for index in range(2):
        roles.append(
            {
                "id": f"{prefix}.plugin-writer-{index + 1:02d}",
                "class": "bounded_plugin_writer",
                "epoch": epoch,
                "domain": "ALL",
                "dispatch_group": 1,
                "returns": {"plugins": 1},
            }
        )
        roles.append(
            {
                "id": f"{prefix}.adversarial-tester-{index + 1:02d}",
                "class": "adversarial_tester",
                "epoch": epoch,
                "domain": "ALL",
                "dispatch_group": 1,
                "returns": {"test_reports": 1},
            }
        )
    for domain in DOMAINS:
        roles.append(
            {
                "id": f"{prefix}.spec-builder-{domain.id.casefold()}",
                "class": "domain_spec_builder",
                "epoch": epoch,
                "domain": domain.id,
                "dispatch_group": 2,
                "requires": "current_epoch_family_cards",
                "returns": {"feature_specs": 2},
            }
        )
    for index in range(2):
        roles.append(
            {
                "id": f"{prefix}.blind-judge-{index + 1:02d}",
                "class": "blind_judge",
                "epoch": epoch,
                "domain": "ALL",
                "dispatch_group": 3,
                "requires": "current_epoch_receipts",
                "returns": {"judgments": 1},
            }
        )
    counts = Counter(str(role["class"]) for role in roles)
    if len(roles) != ROLES_PER_EPOCH or counts != Counter(ROLE_COUNTS):
        raise AssertionError(f"invalid epoch roster: {len(roles)} roles, {counts}")
    if len({role["id"] for role in roles}) != len(roles):
        raise AssertionError("role IDs are not unique")
    return roles


def role_specs() -> list[dict[str, Any]]:
    roles = [role for epoch in range(1, EPOCHS + 1) for role in epoch_role_specs(epoch)]
    if len(roles) != EXPECTED_JNOCCIO_ROLES or len({role["id"] for role in roles}) != len(roles):
        raise AssertionError("ten-epoch role roster is not exactly 360 stable roles")
    return roles


def dispatch_groups(epoch: int) -> list[list[dict[str, Any]]]:
    roles = epoch_role_specs(epoch)
    return [
        [role for role in roles if role["dispatch_group"] == group]
        for group in (1, 2, 3)
    ]


def controller_feature_id(
    epoch: int, domain: str, family: str, spec: str, output: str
) -> str:
    if epoch not in range(1, EPOCHS + 1):
        raise SchemaError(["epoch must be between 1 and 10"])
    if domain not in {item.id for item in DOMAINS}:
        raise SchemaError(["domain must be D01..D10"])
    parts = [_safe_slug(value) for value in (family, spec, output)]
    return f"v2.1.e{epoch:02d}.{domain.casefold()}.{'.'.join(parts)}"


def discover_disk_profiles(users_root: Path) -> tuple[str, ...]:
    """Discover profile IDs without opening any credential file."""

    if not users_root.is_dir():
        return ()
    profiles = []
    for directory in sorted(users_root.iterdir(), key=lambda path: path.name):
        if not directory.is_dir() or not (directory / "llm.env").is_file():
            continue
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", directory.name):
            continue
        profiles.append(directory.name)
    return tuple(profiles)


def fetch_router_health(url: str = DEFAULT_HEALTH_URL, *, timeout: float = 5.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - fixed local URL
        payload = json.loads(response.read(256 * 1024).decode("utf-8"))
    if not isinstance(payload, dict):
        raise CampaignError("Fusion health response must be a JSON object")
    return payload


def fetch_jekko_profiles(settings: Settings) -> tuple[str, ...]:
    process = subprocess.run(
        ["jekko", "jnoccio", "status"],
        cwd=settings.repo_root,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise CampaignError("jekko jnoccio status failed")
    payload = json.loads(process.stdout)
    profiles = payload.get("jnoccio_user_key_users")
    if not isinstance(profiles, list) or not all(isinstance(item, str) for item in profiles):
        raise CampaignError("Jekko status did not report jnoccio_user_key_users")
    return tuple(sorted(set(profiles)))


def _positive_int_map(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, count in value.items():
        if isinstance(key, str) and isinstance(count, int) and not isinstance(count, bool):
            result[key] = count
    return dict(sorted(result.items()))


def sanitize_router_metadata(value: Any) -> dict[str, Any] | None:
    """Keep only routing/utilization metadata that cannot contain credentials."""

    if not isinstance(value, dict):
        return None
    clean: dict[str, Any] = {}
    for key, item in value.items():
        if key not in _ROUTER_METADATA_KEYS:
            continue
        if isinstance(item, (str, int, float, bool)) or item is None:
            clean[key] = item
        elif isinstance(item, list) and all(
            isinstance(member, (str, int, float, bool)) or member is None for member in item
        ):
            clean[key] = item
    assert_secret_free(clean)
    return clean


def sanitize_router_health(health: Mapping[str, Any]) -> dict[str, Any]:
    slots = _positive_int_map(health.get("per_user_slot_counts"))
    provider_slots = _positive_int_map(health.get("per_provider_slot_counts"))
    return {
        "provider": str(health.get("provider") or ""),
        "upstream_key_source": str(health.get("upstream_key_source") or ""),
        "visible_model": str(health.get("visible_model") or ""),
        "ok": health.get("ok") is True,
        "user_count": int(health.get("user_count") or 0),
        "eligible_slot_count": int(health.get("eligible_slot_count") or 0),
        "keyed_model_count": int(health.get("keyed_models") or 0),
        "available_model_count": int(health.get("available_models") or 0),
        "per_user_slot_counts": slots,
        "per_provider_slot_counts": provider_slots,
    }


def reconcile_router_pool(
    disk_profiles: Sequence[str],
    health: Mapping[str, Any],
    *,
    jekko_profiles: Sequence[str] | None = None,
) -> PoolReconciliation:
    clean = sanitize_router_health(health)
    disk = tuple(sorted(set(map(str, disk_profiles))))
    slot_counts = clean["per_user_slot_counts"]
    live = tuple(sorted(slot_counts))
    jekko = tuple(sorted(set(map(str, jekko_profiles if jekko_profiles is not None else disk))))
    missing_live = sorted(set(disk) - set(live))
    missing_disk = sorted(set(live) - set(disk))
    zero_slots = sorted(profile for profile in disk if slot_counts.get(profile, 0) <= 0)
    errors: list[str] = []
    if clean["ok"] is not True:
        errors.append("Fusion health is not OK")
    if clean["provider"] != "jnoccio":
        errors.append("Fusion provider is not jnoccio")
    if clean["upstream_key_source"] != "users_pool":
        errors.append("Fusion is not routing through the users pool")
    if not disk:
        errors.append("no credential-bearing disk profiles were discovered")
    if missing_live:
        errors.append(f"disk profiles missing from Fusion: {missing_live}")
    if missing_disk:
        errors.append(f"Fusion profiles missing from disk: {missing_disk}")
    if set(jekko) != set(disk):
        errors.append(
            "Jekko profile discovery differs from credential-bearing disk profiles: "
            f"disk_only={sorted(set(disk) - set(jekko))}, "
            f"jekko_only={sorted(set(jekko) - set(disk))}"
        )
    if zero_slots:
        errors.append(f"profiles have zero eligible slots: {zero_slots}")
    if clean["user_count"] != len(live):
        errors.append("Fusion user_count does not match per_user_slot_counts")
    if clean["eligible_slot_count"] != sum(max(0, count) for count in slot_counts.values()):
        errors.append("Fusion eligible_slot_count does not match the per-user total")
    receipt = {
        "schema_version": CAMPAIGN_VERSION,
        "receipt_type": "router_pool_snapshot",
        "captured_at": utc_now(),
        **clean,
        "disk_profile_ids": list(disk),
        "jekko_profile_ids": list(jekko),
        "live_profile_ids": list(live),
        "health_sha256": _sha256_json(clean),
        "valid": not errors,
        "errors": errors,
    }
    validate_receipt("router_pool_snapshot", receipt)
    return PoolReconciliation(receipt, tuple(errors))


def dynamic_worker_count(ready_jobs: int, health: Mapping[str, Any]) -> int:
    if ready_jobs < 0:
        raise ValueError("ready_jobs cannot be negative")
    eligible = sanitize_router_health(health)["eligible_slot_count"]
    if ready_jobs and eligible <= 0:
        raise CampaignError("no eligible Fusion slots for a ready dispatch")
    return min(ready_jobs, eligible)


def assert_secret_free(value: Any, *, path: str = "receipt") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if _SECRET_KEY_RE.search(key_text):
                raise ReceiptError(f"credential-like field is forbidden at {path}.{key_text}")
            assert_secret_free(item, path=f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_secret_free(item, path=f"{path}[{index}]")
    elif isinstance(value, str) and _SECRET_VALUE_RE.search(value):
        raise ReceiptError(f"credential-like value is forbidden at {path}")


def _require_fields(value: Mapping[str, Any], required: Iterable[str]) -> list[str]:
    return [f"missing field: {name}" for name in sorted(set(required) - set(value))]


def validate_receipt(receipt_type: str, value: Any) -> None:
    if receipt_type not in RECEIPT_TYPES:
        raise ReceiptError(f"unsupported receipt type: {receipt_type}")
    if not isinstance(value, dict):
        raise ReceiptError("receipt must be an object")
    errors = _require_fields(value, ("schema_version", "receipt_type"))
    if value.get("schema_version") != CAMPAIGN_VERSION:
        errors.append("schema_version must be 2.1")
    if value.get("receipt_type") != receipt_type:
        errors.append("receipt_type does not match its schema")
    required = {
        "router_pool_snapshot": {
            "captured_at",
            "provider",
            "upstream_key_source",
            "user_count",
            "eligible_slot_count",
            "disk_profile_ids",
            "jekko_profile_ids",
            "live_profile_ids",
            "per_user_slot_counts",
            "per_provider_slot_counts",
            "health_sha256",
            "valid",
            "errors",
        },
        "per_user_utilization": {
            "epoch",
            "wave_id",
            "requested_workers",
            "eligible_slots",
            "jobs",
            "successes",
            "failures",
            "rate_limits",
            "eligible_user_ids",
            "covered_user_ids",
            "per_user",
            "coverage_complete",
        },
        "epoch_result": {
            "epoch",
            "roles",
            "attempts",
            "new_executed_columns",
            "novel_valid_columns",
            "valid_by_domain",
            "base_families",
            "phase_receipts",
        },
        "top_feature_record": {
            "feature_id",
            "target",
            "equation",
            "configuration",
            "domain",
            "physical_rationale",
            "novelty_proof",
            "validation_status",
            "strength_components",
            "strength",
        },
        "genetic_reduction_history": {
            "target",
            "population_size",
            "generations",
            "seed",
            "history",
            "preregistered_views",
        },
        "sealed_confirmation_result": {
            "seeds",
            "folds",
            "trees",
            "task_type",
            "opened_once",
            "fold_hashes",
            "controls",
            "views",
            "winners",
            "confirmed_mean_rmsle",
            "compact_alternative",
        },
    }[receipt_type]
    errors.extend(_require_fields(value, required))
    if errors:
        raise ReceiptError("; ".join(errors))
    assert_secret_free(value)


def write_receipt(path: Path, receipt_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(payload)
    value.setdefault("schema_version", CAMPAIGN_VERSION)
    value.setdefault("receipt_type", receipt_type)
    validate_receipt(receipt_type, value)
    atomic_json(path, value)
    return value


STATE_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS campaign (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    state TEXT NOT NULL,
    phase TEXT NOT NULL,
    error TEXT
);
CREATE TABLE IF NOT EXISTS roles (
    role_id TEXT PRIMARY KEY,
    epoch INTEGER NOT NULL,
    role_class TEXT NOT NULL,
    domain TEXT NOT NULL,
    dispatch_group INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    spec_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phases (
    phase TEXT PRIMARY KEY,
    completed_at TEXT NOT NULL,
    receipt_path TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS leases (
    role_id TEXT NOT NULL REFERENCES roles(role_id),
    attempt INTEGER NOT NULL,
    state TEXT NOT NULL,
    prompt_path TEXT NOT NULL,
    prompt_sha256 TEXT NOT NULL,
    prepared_at TEXT NOT NULL,
    submitted_at TEXT,
    finished_at TEXT,
    PRIMARY KEY(role_id,attempt)
);
CREATE TABLE IF NOT EXISTS attempts (
    role_id TEXT NOT NULL REFERENCES roles(role_id),
    attempt INTEGER NOT NULL,
    state TEXT NOT NULL,
    reserved_usd REAL NOT NULL,
    debited_usd REAL,
    reported_cost_usd REAL,
    credential_user_id TEXT,
    router_metadata_json TEXT,
    result_path TEXT,
    valid INTEGER,
    error_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY(role_id,attempt),
    FOREIGN KEY(role_id,attempt) REFERENCES leases(role_id,attempt)
);
CREATE TABLE IF NOT EXISTS columns (
    feature_id TEXT PRIMARY KEY,
    epoch INTEGER NOT NULL,
    domain TEXT NOT NULL,
    family_id TEXT NOT NULL,
    executed INTEGER NOT NULL,
    novel INTEGER NOT NULL,
    valid INTEGER NOT NULL,
    rejection_reason TEXT
);
CREATE TABLE IF NOT EXISTS families (
    family_id TEXT PRIMARY KEY,
    epoch INTEGER NOT NULL,
    domain TEXT NOT NULL,
    valid INTEGER NOT NULL
);
"""


class CampaignStore:
    """Transactional state for phase-safe resume and conservative attempts."""

    def __init__(self, settings: Settings):
        self.settings = settings
        settings.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(STATE_SCHEMA)
            connection.execute(
                "INSERT OR IGNORE INTO campaign VALUES(?,?,?,'preflight',NULL)",
                (settings.run_id, utc_now(), "created"),
            )

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.settings.state_path, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def register_roles(self, roles: Sequence[Mapping[str, Any]]) -> None:
        with self.connect() as connection:
            for role in roles:
                connection.execute(
                    "INSERT OR IGNORE INTO roles(role_id,epoch,role_class,domain,"
                    "dispatch_group,spec_json) VALUES(?,?,?,?,?,?)",
                    (
                        role["id"],
                        role["epoch"],
                        role["class"],
                        role["domain"],
                        role["dispatch_group"],
                        json.dumps(role, sort_keys=True, separators=(",", ":")),
                    ),
                )

    def prepare_lease(self, role_id: str, attempt: int, prompt_path: Path) -> None:
        if attempt not in range(MAX_ATTEMPTS_PER_ROLE):
            raise BudgetError("only an initial attempt and one retry are allowed")
        prompt_size = prompt_path.stat().st_size
        if prompt_size > PROMPT_LIMIT_BYTES:
            raise ValueError(f"prompt is {prompt_size} bytes; limit is {PROMPT_LIMIT_BYTES}")
        with self.connect() as connection:
            if connection.execute("SELECT 1 FROM roles WHERE role_id=?", (role_id,)).fetchone() is None:
                raise CampaignError(f"unknown role: {role_id}")
            prior = connection.execute(
                "SELECT COUNT(*) n FROM attempts WHERE role_id=?", (role_id,)
            ).fetchone()["n"]
            if int(prior) > attempt:
                raise BudgetError(f"role {role_id} already consumed attempt {attempt}")
            connection.execute(
                "INSERT INTO leases VALUES(?,?,?,?,?,?,NULL,NULL) "
                "ON CONFLICT(role_id,attempt) DO UPDATE SET state='prepared',"
                "prompt_path=excluded.prompt_path,prompt_sha256=excluded.prompt_sha256",
                (
                    role_id,
                    attempt,
                    "prepared",
                    str(prompt_path),
                    sha256_file(prompt_path),
                    utc_now(),
                ),
            )

    def submit_lease(self, role_id: str, attempt: int) -> None:
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            lease = connection.execute(
                "SELECT state FROM leases WHERE role_id=? AND attempt=?", (role_id, attempt)
            ).fetchone()
            if lease is None or lease["state"] != "prepared":
                raise CampaignError("only a prepared lease may be submitted")
            existing = connection.execute(
                "SELECT 1 FROM attempts WHERE role_id=? AND attempt=?", (role_id, attempt)
            ).fetchone()
            if existing is not None:
                raise BudgetError("an already consumed attempt cannot be resubmitted")
            attempts = int(connection.execute("SELECT COUNT(*) n FROM attempts").fetchone()["n"])
            if attempts >= MAX_JNOCCIO_ATTEMPTS:
                raise BudgetError("720-attempt Jnoccio exposure exhausted")
            total = float(
                connection.execute(
                    "SELECT COALESCE(SUM(COALESCE(debited_usd,reserved_usd)),0) total "
                    "FROM attempts"
                ).fetchone()["total"]
            )
            if total + JNOCCIO_MIN_DEBIT_USD > MAX_COST_USD:
                raise BudgetError("next reservation would exceed the $2,000 ceiling")
            now = utc_now()
            connection.execute(
                "INSERT INTO attempts(role_id,attempt,state,reserved_usd) VALUES(?,?,?,?)",
                (role_id, attempt, "submitted", JNOCCIO_MIN_DEBIT_USD),
            )
            connection.execute(
                "UPDATE leases SET state='submitted',submitted_at=? WHERE role_id=? AND attempt=?",
                (now, role_id, attempt),
            )
            connection.execute("UPDATE roles SET status='running' WHERE role_id=?", (role_id,))

    def finish_attempt(
        self,
        role_id: str,
        attempt: int,
        *,
        result_path: Path,
        valid: bool,
        credential_user_id: str | None,
        router_metadata: Mapping[str, Any] | None,
        errors: Sequence[str],
    ) -> float:
        clean_metadata = sanitize_router_metadata(router_metadata)
        reported: float | None = None
        if clean_metadata:
            for key in ("cost_usd", "total_cost_usd", "estimated_cost_usd"):
                value = clean_metadata.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    candidate = float(value)
                    if math.isfinite(candidate) and candidate >= 0:
                        reported = candidate
                        break
        debit = max(JNOCCIO_MIN_DEBIT_USD, reported or 0.0)
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT state,reserved_usd,debited_usd FROM attempts "
                "WHERE role_id=? AND attempt=?",
                (role_id, attempt),
            ).fetchone()
            if row is None:
                raise BudgetError("attempt was not reserved")
            if row["debited_usd"] is not None:
                return float(row["debited_usd"])
            other = float(
                connection.execute(
                    "SELECT COALESCE(SUM(COALESCE(debited_usd,reserved_usd)),0) total "
                    "FROM attempts WHERE NOT (role_id=? AND attempt=?)",
                    (role_id, attempt),
                ).fetchone()["total"]
            )
            if other + debit > MAX_COST_USD:
                raise BudgetError("reported cost would exceed the $2,000 ceiling")
            state = "complete" if valid else "failed"
            connection.execute(
                "UPDATE attempts SET state=?,debited_usd=?,reported_cost_usd=?,"
                "credential_user_id=?,router_metadata_json=?,result_path=?,valid=?,error_json=? "
                "WHERE role_id=? AND attempt=?",
                (
                    state,
                    debit,
                    reported,
                    credential_user_id,
                    json.dumps(clean_metadata, sort_keys=True),
                    str(result_path),
                    int(valid),
                    json.dumps(list(errors), sort_keys=True),
                    role_id,
                    attempt,
                ),
            )
            connection.execute(
                "UPDATE leases SET state=?,finished_at=? WHERE role_id=? AND attempt=?",
                (state, utc_now(), role_id, attempt),
            )
            connection.execute(
                "UPDATE roles SET status=? WHERE role_id=?",
                (
                    "complete"
                    if valid
                    else ("exhausted" if attempt + 1 >= MAX_ATTEMPTS_PER_ROLE else "pending"),
                    role_id,
                ),
            )
        return debit

    def recover_interrupted_leases(self) -> int:
        """Consume submitted attempts, but make their roles eligible for the sole retry."""

        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                "SELECT role_id,attempt FROM attempts WHERE state='submitted'"
            ).fetchall()
            for row in rows:
                connection.execute(
                    "UPDATE attempts SET state='interrupted',debited_usd=reserved_usd,valid=0,"
                    "error_json='[\"interrupted lease\"]' WHERE role_id=? AND attempt=?",
                    (row["role_id"], row["attempt"]),
                )
                connection.execute(
                    "UPDATE leases SET state='interrupted',finished_at=? "
                    "WHERE role_id=? AND attempt=?",
                    (utc_now(), row["role_id"], row["attempt"]),
                )
                status = "pending" if int(row["attempt"]) + 1 < MAX_ATTEMPTS_PER_ROLE else "exhausted"
                connection.execute(
                    "UPDATE roles SET status=? WHERE role_id=?", (status, row["role_id"])
                )
            return len(rows)

    def complete_phase(self, phase: str, receipt_path: Path) -> None:
        if not receipt_path.resolve().is_relative_to(self.settings.run_root.resolve()):
            raise CampaignError("phase receipts must remain below the campaign run root")
        with self.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO phases VALUES(?,?,?,?)",
                (phase, utc_now(), str(receipt_path), sha256_file(receipt_path)),
            )
            connection.execute(
                "UPDATE campaign SET state='running',phase=?,error=NULL WHERE run_id=?",
                (phase, self.settings.run_id),
            )

    def phase_complete(self, phase: str) -> bool:
        with self.connect() as connection:
            return connection.execute(
                "SELECT 1 FROM phases WHERE phase=?", (phase,)
            ).fetchone() is not None

    def phase_receipts(self) -> dict[str, str]:
        with self.connect() as connection:
            rows = connection.execute("SELECT phase,receipt_sha256 FROM phases ORDER BY phase").fetchall()
        return {str(row["phase"]): str(row["receipt_sha256"]) for row in rows}

    def budget_summary(self) -> BudgetSummary:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) attempts,"
                "COALESCE(SUM(CASE WHEN debited_usd IS NOT NULL THEN debited_usd ELSE 0 END),0) debited,"
                "COALESCE(SUM(CASE WHEN debited_usd IS NULL THEN reserved_usd ELSE 0 END),0) reserved,"
                "COALESCE(SUM(reported_cost_usd),0) reported "
                "FROM attempts"
            ).fetchone()
        debited, reserved = float(row["debited"]), float(row["reserved"])
        return BudgetSummary(
            MAX_COST_USD,
            debited,
            reserved,
            MAX_COST_USD - debited - reserved,
            int(row["attempts"]),
            float(row["reported"]),
        )

    def counters(self) -> dict[str, Any]:
        with self.connect() as connection:
            role = connection.execute(
                "SELECT COUNT(*) total,COALESCE(SUM(status='complete'),0) complete FROM roles"
            ).fetchone()
            columns = connection.execute(
                "SELECT COALESCE(SUM(executed),0) executed,"
                "COALESCE(SUM(novel AND valid),0) novel_valid FROM columns"
            ).fetchone()
            domains = connection.execute(
                "SELECT domain,COUNT(*) count FROM columns WHERE novel=1 AND valid=1 GROUP BY domain"
            ).fetchall()
            families = connection.execute(
                "SELECT COUNT(*) count FROM families WHERE valid=1"
            ).fetchone()["count"]
        return {
            "roles": int(role["total"]),
            "roles_complete": int(role["complete"]),
            "new_executed_columns": int(columns["executed"]),
            "novel_valid_columns": int(columns["novel_valid"]),
            "valid_by_domain": {str(row["domain"]): int(row["count"]) for row in domains},
            "base_families": int(families),
        }


def _default_baseline_paths(settings: Settings) -> tuple[Path, Path]:
    columns = settings.baseline_columns_path or (
        settings.nomad_root
        / "artifacts/nomad_theory_feature_hunt/v2/inbox/v2-genetic-reduction-20260718"
        / "inputs/augmented-bundle/columns.json"
    )
    summary = settings.zyal_summary_path or (
        settings.nomad_root
        / "artifacts/nomad_theory_feature_hunt/v2/inbox/v2-genetic-reduction-20260718"
        / "matrices/zyal/graduation-summary.json"
    )
    return columns, summary


def reindex_baseline(settings: Settings) -> dict[str, Any]:
    """Freeze all 10,800 executable baseline IDs and prior ZYAL negative memory."""

    columns_path, summary_path = _default_baseline_paths(settings)
    if not columns_path.exists() or not summary_path.exists():
        raise CampaignError("10,800-column baseline or ZYAL graduation summary is missing")
    columns = json.loads(columns_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not isinstance(columns, list) or not all(isinstance(item, str) for item in columns):
        raise CampaignError("baseline columns artifact must be a string list")
    if len(columns) != BASELINE_REGISTRY_COLUMNS or len(set(columns)) != len(columns):
        raise CampaignError("baseline registry must contain exactly 10,800 unique columns")
    if int(summary.get("validated_columns", -1)) != BASELINE_ZYAL_COLUMNS:
        raise CampaignError("prior ZYAL graduation must contain exactly 831 validated columns")
    destination = settings.run_root / "inputs/baseline"
    atomic_json(destination / "columns.json", columns)
    negative = []
    for item in summary.get("augmentation_rejections", summary.get("quarantined", [])):
        if isinstance(item, dict):
            negative.append(
                {
                    "feature_id": item.get("feature_id"),
                    "reason": item.get("reason", "prior_rejection"),
                    "executable": False,
                }
            )
    atomic_json(settings.run_root / "memory/negative/prior_rejections.json", negative)
    rows = []
    for index, feature_id in enumerate(columns):
        source = "existing-809" if index < 809 else "atlas"
        if index >= BASELINE_REGISTRY_COLUMNS - BASELINE_ZYAL_COLUMNS:
            source = "zyal-v1-graduated"
        rows.append({"feature_id": feature_id, "source": source, "executable": True})
    registry = settings.run_root / "novelty/baseline_registry.jsonl"
    registry.parent.mkdir(parents=True, exist_ok=True)
    temporary = registry.with_name(f".{registry.name}.{os.getpid()}.tmp")
    temporary.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    os.replace(temporary, registry)
    inventory_paths = {
        "atlas": settings.repo_root / "artifacts/atlas_hyperion_bakeoff/bundle/columns.json",
        "v1": settings.nomad_root
        / "artifacts/nomad_theory_feature_hunt/inbox/nomad-foundry-20260718/final_hashes/manifest.json",
        "v2": columns_path,
        "zyal": summary_path,
    }
    staged_inventory: dict[str, dict[str, Any]] = {}
    for name, source in inventory_paths.items():
        if not source.is_file():
            staged_inventory[name] = {"path": None, "sha256": None, "present": False}
            continue
        suffix = "".join(source.suffixes) or ".artifact"
        staged = destination / "sources" / f"{name}{suffix}"
        staged.parent.mkdir(parents=True, exist_ok=True)
        temporary_source = staged.with_name(f".{staged.name}.{os.getpid()}.tmp")
        shutil.copy2(source, temporary_source)
        os.replace(temporary_source, staged)
        staged_inventory[name] = {
            "path": str(staged.relative_to(settings.run_root)),
            "sha256": sha256_file(staged),
            "present": True,
        }
    receipt = {
        "schema_version": CAMPAIGN_VERSION,
        "baseline_columns": len(columns),
        "existing_809_columns": 809,
        "atlas_and_existing_columns": BASELINE_REGISTRY_COLUMNS - BASELINE_ZYAL_COLUMNS,
        "graduated_zyal_columns": BASELINE_ZYAL_COLUMNS,
        "negative_memory_items": len(negative),
        "source_hashes": {
            "columns": sha256_file(columns_path),
            "zyal_summary": sha256_file(summary_path),
        },
        "reindexed_sources": staged_inventory,
        "registry_partitions": {
            "existing_809_sha256": _sha256_json(columns[:809]),
            "atlas_sha256": _sha256_json(
                columns[809 : BASELINE_REGISTRY_COLUMNS - BASELINE_ZYAL_COLUMNS]
            ),
            "zyal_sha256": _sha256_json(columns[-BASELINE_ZYAL_COLUMNS:]),
        },
        "registry_sha256": sha256_file(registry),
        "current_champion_mean_rmsle": CURRENT_CHAMPION_MEAN_RMSLE,
    }
    atomic_json(settings.run_root / "receipts/baseline-index.json", receipt)
    return receipt


def _run_synchronizer(
    settings: Settings,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    if not settings.synchronizer.is_file():
        return {"ran": False, "returncode": None, "script_sha256": None}
    process = runner(
        [str(settings.synchronizer)],
        cwd=settings.repo_root,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=60,
        check=False,
    )
    return {
        "ran": True,
        "returncode": int(process.returncode),
        "script_sha256": sha256_file(settings.synchronizer),
    }


def dual_gpu_preflight() -> dict[str, Any]:
    commands = {
        "local": ["nvidia-smi", "-L"],
        "remote": ["ssh", "-o", "BatchMode=yes", "xbabe1", "nvidia-smi", "-L"],
    }
    results: dict[str, Any] = {}
    for name, command in commands.items():
        try:
            process = subprocess.run(
                command, text=True, capture_output=True, timeout=30, check=False
            )
            results[name] = {
                "returncode": process.returncode,
                "identity_sha256": hashlib.sha256(process.stdout.encode()).hexdigest(),
            }
        except (OSError, subprocess.TimeoutExpired) as error:
            results[name] = {"returncode": -1, "error": type(error).__name__}
    results["ready"] = all(item.get("returncode") == 0 for item in results.values())
    return results


def _tree_identity(root: Path) -> str:
    files = sorted(path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def _controller_sources(settings: Settings) -> dict[str, Path]:
    schema_root = settings.repo_root / "ops/nomad-feature-hunt/schemas/v2.1"
    sources = {
        "zyal_epochs.py": Path(__file__),
        "01-jnoccio-research-generation-v2.zyal": settings.repo_root
        / "ops/nomad-feature-hunt/01-jnoccio-research-generation-v2.zyal",
    }
    sources.update(
        {f"schemas/{path.name}": path for path in sorted(schema_root.glob("*.json"))}
    )
    return sources


def stage_controller_snapshot(settings: Settings) -> dict[str, Any]:
    destination = settings.run_root / "inputs/controller"
    manifest_path = destination / "manifest.json"
    sources = _controller_sources(settings)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for logical_name, source in sources.items():
            frozen = destination / logical_name
            expected = manifest.get("files", {}).get(logical_name, {}).get("sha256")
            if (
                expected is None
                or not source.exists()
                or not frozen.exists()
                or sha256_file(source) != expected
                or sha256_file(frozen) != expected
            ):
                raise CampaignError(f"controller snapshot changed after preflight: {logical_name}")
        return manifest
    files: dict[str, dict[str, str]] = {}
    for logical_name, source in sources.items():
        if not source.exists():
            raise CampaignError(f"controller source is missing: {source}")
        frozen = destination / logical_name
        frozen.parent.mkdir(parents=True, exist_ok=True)
        temporary = frozen.with_name(f".{frozen.name}.{os.getpid()}.tmp")
        shutil.copy2(source, temporary)
        os.replace(temporary, frozen)
        files[logical_name] = {
            "source": str(source.resolve()),
            "sha256": sha256_file(frozen),
        }
    manifest = {"frozen": True, "files": files, "credential_values_serialized": False}
    atomic_json(manifest_path, manifest)
    return manifest


def preflight(
    settings: Settings,
    *,
    health: Mapping[str, Any] | None = None,
    health_fetcher: Callable[[str], dict[str, Any]] = fetch_router_health,
    jekko_profile_fetcher: Callable[[Settings], Sequence[str]] = fetch_jekko_profiles,
    synchronizer_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    gpu_checker: Callable[[], dict[str, Any]] = dual_gpu_preflight,
    run_synchronizer: bool = True,
) -> dict[str, Any]:
    for directory in ARTIFACT_DIRS:
        (settings.run_root / directory).mkdir(parents=True, exist_ok=True)
    store = CampaignStore(settings)
    roles = role_specs()
    store.register_roles(roles)
    atomic_json(settings.run_root / "roles.json", roles)
    blockers: list[str] = []
    try:
        sync = (
            _run_synchronizer(settings, synchronizer_runner)
            if run_synchronizer
            else {"ran": False, "returncode": None, "script_sha256": None}
        )
    except (OSError, subprocess.SubprocessError) as error:
        sync = {
            "ran": True,
            "returncode": None,
            "script_sha256": (
                sha256_file(settings.synchronizer) if settings.synchronizer.is_file() else None
            ),
            "error": type(error).__name__,
        }
    if run_synchronizer and not sync["ran"]:
        blockers.append("Jnoccio user synchronizer is missing")
    elif sync["ran"] and sync["returncode"] != 0:
        blockers.append("Jnoccio user synchronizer failed")
    try:
        live_health = dict(health) if health is not None else health_fetcher(settings.health_url)
        jekko_profiles = tuple(jekko_profile_fetcher(settings))
        pool = reconcile_router_pool(
            discover_disk_profiles(settings.users_root),
            live_health,
            jekko_profiles=jekko_profiles,
        )
        blockers.extend(pool.errors)
        write_receipt(
            settings.run_root / "receipts/router_pool/preflight.json",
            "router_pool_snapshot",
            pool.receipt,
        )
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        CampaignError,
        subprocess.SubprocessError,
    ) as error:
        pool = None
        blockers.append(f"router pool: {error}")
    try:
        baseline = reindex_baseline(settings)
    except (OSError, ValueError, json.JSONDecodeError, CampaignError) as error:
        baseline = None
        blockers.append(f"baseline reindex: {error}")
    gpu = gpu_checker()
    if gpu.get("ready") is not True:
        blockers.append("dual-GPU preflight failed")
    crystal_root = settings.repo_root / "nomad_crystal360"
    try:
        snapshot = stage_controller_snapshot(settings)
    except (CampaignError, OSError, json.JSONDecodeError) as error:
        snapshot = None
        blockers.append(f"controller snapshot: {error}")
    identity_path = settings.run_root / "inputs/controller/identity.json"
    current_crystal_identity = _tree_identity(crystal_root) if crystal_root.is_dir() else None
    if identity_path.exists():
        controller_identity = json.loads(identity_path.read_text(encoding="utf-8"))
        if controller_identity.get("nomad_crystal360_sha256") != current_crystal_identity:
            blockers.append("nomad_crystal360 changed after campaign isolation")
    else:
        controller_identity = {
            "nomad_crystal360_sha256": current_crystal_identity,
            "zyal_epochs_sha256": sha256_file(Path(__file__)),
        }
        atomic_json(identity_path, controller_identity)
    status = {
        "run_id": settings.run_id,
        "campaign_version": CAMPAIGN_VERSION,
        "run_root": str(settings.run_root),
        "ready": not blockers,
        "blockers": blockers,
        "checks": {
            "roles": len(roles),
            "roles_per_epoch": ROLES_PER_EPOCH,
            "largest_ready_wave": max(len(group) for group in dispatch_groups(1)),
            "synchronizer": sync,
            "router_pool": pool.receipt if pool else None,
            "baseline": baseline,
            "dual_gpu": gpu,
            "budget": {"cost_usd": MAX_COST_USD, "attempts": MAX_JNOCCIO_ATTEMPTS},
            "controller_identity": controller_identity,
            "controller_snapshot": snapshot,
        },
    }
    atomic_json(settings.run_root / "preflight.json", status)
    with store.connect() as connection:
        connection.execute(
            "UPDATE campaign SET state=?,phase='preflight',error=? WHERE run_id=?",
            ("preflight" if status["ready"] else "blocked", "; ".join(blockers) or None, settings.run_id),
        )
    HashChain(settings.events_path).append("preflight", status)
    return status


def _family_card_contract(role: Mapping[str, Any]) -> dict[str, Any]:
    domain = str(role["domain"])
    kernel = DOMAIN_KERNELS[domain]
    domain_title = next(item.title for item in DOMAINS if item.id == domain)
    return {
        "exact_top_level_keys": ["family_cards"],
        "family_card_count": 3,
        "family_card_exact_fields": sorted(FAMILY_FIELDS),
        "assigned_domain": domain,
        "assigned_domain_research_area": domain_title,
        "required_kernel": kernel,
        "required_custom_plugin_required": False,
        "allowed_target_affinity": ["both", *TARGETS],
        "required_invariances_exactly_once": [
            "translation",
            "rotation",
            "atom_permutation",
            "periodic_wrapping",
            "equivalent_cell",
        ],
        "family_slugs_must_be_unique": True,
        "content_requirements": {
            "family_slug": (
                "invent a unique lowercase kebab-case name for the concrete mechanism; generic "
                "names such as d01-novel-family-01 are forbidden"
            ),
            "physical_hypothesis": (
                "at least 80 characters; name a concrete domain-specific structural observable "
                "and the physical mechanism linking it to the declared target affinity"
            ),
            "inputs": (
                "a nonempty list of structure-derived inputs only; periodic_structure is allowed"
            ),
            "citation_ids": (
                "a nonempty list; use baseline-registry when no narrower controller citation "
                "is supplied"
            ),
            "atlas_novelty_argument": (
                "at least 80 characters; identify the specific joint construction absent from "
                "the 10,800-column registry"
            ),
            "falsifier": (
                "at least 40 characters; state a structure-preserving intervention that would "
                "disprove the mechanism"
            ),
            "complexity": "a nonempty asymptotic complexity string such as O(N log N)",
        },
        "all_three_cards_must_propose_different_mechanisms": True,
        "no_example_content_is_supplied": "invent the scientific content; do not emit placeholders",
    }


def _role_output_contract(role: Mapping[str, Any]) -> dict[str, Any]:
    role_class = str(role["class"])
    if role_class == "domain_architect":
        return _family_card_contract(role)
    if role_class in {"domain_spec_builder", "target_exploiter", "cross_family_synthesizer"}:
        contract: dict[str, Any] = {
            "exact_top_level_keys": ["feature_specs"],
            "feature_spec_count": 2,
            "feature_spec_exact_fields": sorted(SPEC_FIELDS),
            "parameter_set_exact_fields": sorted(PARAMETER_FIELDS),
            "output_exact_fields": sorted(OUTPUT_FIELDS),
            "scalar_outputs_per_spec": "8..25",
        }
        if role_class == "domain_spec_builder":
            domain = str(role["domain"])
            contract["assigned_domain"] = domain
            contract["required_kernel"] = DOMAIN_KERNELS[domain]
        return contract
    if role_class == "bounded_plugin_writer":
        return {
            "exact_top_level_keys": ["family_slug", "plugin_source", "adversarial_tests"],
            "plugin_source_limit_bytes": PLUGIN_LIMIT_BYTES,
        }
    if role_class == "adversarial_tester":
        return {"exact_top_level_keys": ["tested_artifact_ids", "attacks", "findings"]}
    return {"exact_top_level_keys": ["receipt_ids", "judgments"]}


def build_epoch_prompt(role: Mapping[str, Any], context: Mapping[str, Any]) -> str:
    """Build a compact role prompt; adaptive roles receive categorical data only."""

    role_class = str(role["class"])
    safe_context = dict(context)
    if role_class in {"target_exploiter", "cross_family_synthesizer"}:
        allowed = {"positive", "neutral", "negative", "low", "medium", "high", "fast", "slow"}
        feedback = safe_context.get("family_feedback", {})
        if not isinstance(feedback, dict):
            raise ValueError("adaptive family_feedback must be an object")
        for family, values in feedback.items():
            if not isinstance(family, str) or not isinstance(values, dict):
                raise ValueError("adaptive feedback must be categorical by family")
            if any(not isinstance(value, str) or value not in allowed for value in values.values()):
                raise ValueError("adaptive roles may receive only categorical feedback")
        safe_context = {"family_feedback": feedback, "family_cards": safe_context.get("family_cards", {})}
    contracts = {
        "domain_architect": "Return exactly three FamilyCards in family_cards.",
        "domain_spec_builder": "Return exactly two FeatureSpecs in feature_specs.",
        "target_exploiter": "Return exactly two FeatureSpecs in feature_specs.",
        "cross_family_synthesizer": "Return exactly two FeatureSpecs in feature_specs.",
        "bounded_plugin_writer": "Return family_slug, plugin_source, and adversarial_tests.",
        "adversarial_tester": "Return tested_artifact_ids, attacks, and findings.",
        "blind_judge": "Return receipt_ids and judgments without exact score inference.",
    }
    payload = {
        "role": dict(role),
        "contract": contracts[role_class],
        "rules": [
            "Return one strict JSON object and no markdown or prose.",
            "The first non-whitespace character must be { and the last must be }.",
            "Do not wrap JSON in ```json fences.",
            "Do not add router_metadata or any key not explicitly allowed by output_contract.",
            "Never use labels, target rows, labeled test data, credentials, or network access.",
            "Controller-generated IDs replace all proposed IDs after validation.",
            "Plugin source is limited to 20 KB and must define compute_family(structure, config).",
            "Each FeatureSpec must describe executable finite scalar outputs.",
        ],
        "schema": {
            "FamilyCard_fields": sorted(FAMILY_FIELDS),
            "FeatureSpec_fields": sorted(SPEC_FIELDS),
            "parameter_set_fields": sorted(PARAMETER_FIELDS),
            "output_fields": sorted(OUTPUT_FIELDS),
            "feature_spec_output_count": "8..25",
        },
        "output_contract": _role_output_contract(role),
        "context": safe_context,
    }
    prompt = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if len(prompt.encode("utf-8")) > PROMPT_LIMIT_BYTES:
        raise ValueError("role prompt exceeds 12 KB")
    return prompt


def build_schema_retry_prompt(role: Mapping[str, Any], invalid: str, errors: Sequence[str]) -> str:
    if len(invalid.encode("utf-8")) > OUTPUT_LIMIT_BYTES:
        invalid = invalid.encode("utf-8")[:8192].decode("utf-8", errors="ignore")
    payload = {
        "role_id": role["id"],
        "role_class": role["class"],
        "instruction": (
            "Return one complete strict JSON replacement correcting every listed error. The first "
            "character must be { and the last character must be }; emit no markdown fences or prose."
        ),
        "output_contract": _role_output_contract(role),
        "schema_errors": [str(error)[:512] for error in errors[:30]],
        "invalid_artifact": invalid,
    }
    prompt = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    while len(prompt.encode("utf-8")) > PROMPT_LIMIT_BYTES and len(payload["invalid_artifact"]) > 512:
        payload["invalid_artifact"] = payload["invalid_artifact"][: len(payload["invalid_artifact"]) // 2]
        prompt = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if len(prompt.encode("utf-8")) > PROMPT_LIMIT_BYTES:
        raise ValueError("schema retry prompt exceeds 12 KB")
    return prompt


def validate_epoch_role_payload(
    role: Mapping[str, Any],
    payload: Any,
    *,
    families: Mapping[str, dict[str, Any]] | None = None,
    available_receipt_ids: set[str] | None = None,
) -> list[str]:
    if not isinstance(payload, dict):
        return ["role payload must be an object"]
    role_class = role["class"]
    if role_class == "domain_architect":
        items = payload.get("family_cards")
        if set(payload) != {"family_cards"} or not isinstance(items, list) or len(items) != 3:
            return ["domain architect must return exactly three family_cards"]
        errors = []
        family_slugs: list[str] = []
        hypotheses: list[str] = []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"family_cards[{index}] must be an object")
                continue
            errors.extend(
                f"family_cards[{index}]: {error}" for error in validate_family_card(item)
            )
            if isinstance(item.get("family_slug"), str):
                family_slugs.append(str(item["family_slug"]))
            if isinstance(item.get("physical_hypothesis"), str):
                hypotheses.append(str(item["physical_hypothesis"]).strip().casefold())
            if item.get("domain") != role["domain"]:
                errors.append(f"family_cards[{index}] is outside the assigned domain")
            if re.fullmatch(r"d(?:0[1-9]|10)-novel-family-\d+", str(item.get("family_slug", ""))):
                errors.append(f"family_cards[{index}] uses a forbidden generic family slug")
            for field, minimum in (
                ("physical_hypothesis", 80),
                ("atlas_novelty_argument", 80),
                ("falsifier", 40),
            ):
                value = item.get(field)
                if isinstance(value, str) and len(value.strip()) < minimum:
                    errors.append(f"family_cards[{index}].{field} must be at least {minimum} characters")
        if len(family_slugs) != len(set(family_slugs)):
            errors.append("family card slugs must be unique within a role payload")
        if len(hypotheses) != len(set(hypotheses)):
            errors.append("family card physical hypotheses must be distinct within a role payload")
        return errors
    if role_class in {"domain_spec_builder", "target_exploiter", "cross_family_synthesizer"}:
        items = payload.get("feature_specs")
        if set(payload) != {"feature_specs"} or not isinstance(items, list) or len(items) != 2:
            return ["spec role must return exactly two feature_specs"]
        errors = [
            f"feature_specs[{index}] must be an object"
            for index, item in enumerate(items)
            if not isinstance(item, dict)
        ]
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            errors.extend(
                f"feature_specs[{index}]: {error}"
                for error in validate_feature_spec(
                    item, families=dict(families) if families is not None else None
                )
            )
            if role_class == "domain_spec_builder" and item.get("domain") != role["domain"]:
                errors.append(f"feature_specs[{index}] is outside the assigned domain")
        return errors
    if role_class == "bounded_plugin_writer":
        required = {"family_slug", "plugin_source", "adversarial_tests"}
        errors = [] if set(payload) == required else [f"plugin fields must be {sorted(required)}"]
        source = payload.get("plugin_source")
        if not isinstance(source, str) or not source:
            errors.append("plugin_source must be nonempty")
        elif len(source.encode("utf-8")) > PLUGIN_LIMIT_BYTES:
            errors.append("plugin_source exceeds 20 KB")
        else:
            errors.extend(static_check_plugin(source))
        if not isinstance(payload.get("adversarial_tests"), list):
            errors.append("adversarial_tests must be a list")
        return errors
    if role_class == "adversarial_tester":
        required = {"tested_artifact_ids", "attacks", "findings"}
        if set(payload) != required:
            return [f"adversarial tester fields must be {sorted(required)}"]
        return (
            []
            if all(isinstance(payload.get(key), list) and payload.get(key) for key in required)
            else ["adversarial tester fields must be nonempty lists"]
        )
    if role_class == "blind_judge":
        required = {"receipt_ids", "judgments"}
        if set(payload) != required:
            return [f"blind judge fields must be {sorted(required)}"]
        errors = (
            []
            if all(isinstance(payload.get(key), list) and payload.get(key) for key in required)
            else ["blind judge fields must be nonempty lists"]
        )
        if available_receipt_ids is not None and isinstance(payload.get("receipt_ids"), list):
            unknown = sorted(set(map(str, payload["receipt_ids"])) - available_receipt_ids)
            if unknown:
                errors.append(f"blind judge references unknown receipts: {unknown}")
        return errors
    return [f"unsupported role class: {role_class}"]


def parse_epoch_result(role: Mapping[str, Any], text: str) -> tuple[dict[str, Any] | None, list[str]]:
    if len(text.encode("utf-8")) > OUTPUT_LIMIT_BYTES:
        return None, ["assistant output exceeds 20 KB"]
    try:
        payload = parse_strict_json(text, max_bytes=OUTPUT_LIMIT_BYTES)
    except SchemaError as error:
        return None, list(error.errors)
    errors = validate_epoch_role_payload(role, payload)
    try:
        assert_secret_free(payload)
    except ReceiptError as error:
        errors.append(str(error))
    return (payload if not errors and isinstance(payload, dict) else None), errors


def safe_raw_response(result: Mapping[str, Any]) -> dict[str, Any]:
    """Drop unrecognized provider fields before persisting a raw response."""

    safe = {
        "success": result.get("success") is True,
        "assistant_text": str(result.get("assistant_text") or ""),
        "error": str(result.get("error") or "") if result.get("error") else None,
        "provider_id": result.get("provider_id"),
        "model_id": result.get("model_id"),
        "credential_user_id": result.get("credential_user_id"),
        "router_metadata": sanitize_router_metadata(result.get("router_metadata")),
    }
    for key in ("provider_id", "model_id", "credential_user_id"):
        if safe[key] is not None and not isinstance(safe[key], str):
            safe[key] = str(safe[key])
    assert_secret_free({key: value for key, value in safe.items() if key != "assistant_text"})
    return safe


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _persist_role_payload(
    settings: Settings,
    role: Mapping[str, Any],
    attempt: int,
    payload: Mapping[str, Any],
) -> list[Path]:
    """Persist validated data with controller-owned stable IDs."""

    epoch = int(role["epoch"])
    role_id = str(role["id"])
    written: list[Path] = []
    role_class = role["class"]
    if role_class == "domain_architect":
        for index, source in enumerate(payload["family_cards"], start=1):
            card = dict(source)
            slug = _safe_slug(str(card.get("family_slug") or f"family-{index:02d}"))
            family_id = f"v2.1.e{epoch:02d}.{str(role['domain']).casefold()}.{slug}"
            card["family_id"] = family_id
            card["source_role_id"] = role_id
            path = settings.run_root / f"families/epoch-{epoch:02d}/{family_id}.json"
            atomic_json(path, card)
            written.append(path)
    elif role_class in {
        "domain_spec_builder",
        "target_exploiter",
        "cross_family_synthesizer",
    }:
        for index, source in enumerate(payload["feature_specs"], start=1):
            spec = dict(source)
            domain = str(spec.get("domain") or role.get("domain") or "ALL")
            family = _safe_slug(str(spec.get("family_slug") or f"family-{index:02d}"))
            slug = _safe_slug(str(spec.get("spec_slug") or f"spec-{index:02d}"))
            spec_id = f"v2.1.e{epoch:02d}.{domain.casefold()}.{family}.{slug}"
            spec["spec_id"] = spec_id
            spec["source_role_id"] = role_id
            outputs = spec.get("outputs")
            if isinstance(outputs, list):
                for output_index, output in enumerate(outputs, start=1):
                    if not isinstance(output, dict):
                        continue
                    name = str(output.get("name") or f"output-{output_index:02d}")
                    output["feature_id"] = controller_feature_id(
                        epoch, domain, family, slug, name
                    )
            path = settings.run_root / f"specs/epoch-{epoch:02d}/{spec_id}.json"
            atomic_json(path, spec)
            written.append(path)
    elif role_class == "bounded_plugin_writer":
        family = _safe_slug(str(payload["family_slug"]))
        path = settings.run_root / f"plugins/epoch-{epoch:02d}/{role_id}.{family}.py"
        _atomic_text(path, str(payload["plugin_source"]))
        written.append(path)
        tests = path.with_suffix(".tests.json")
        atomic_json(
            tests,
            {
                "plugin_id": f"{role_id}.{family}",
                "source_role_id": role_id,
                "adversarial_tests": payload["adversarial_tests"],
                "plugin_sha256": sha256_file(path),
            },
        )
        written.append(tests)
    elif role_class == "adversarial_tester":
        path = settings.run_root / f"judgments/epoch-{epoch:02d}/{role_id}.adversarial.json"
        atomic_json(path, {**payload, "source_role_id": role_id})
        written.append(path)
    elif role_class == "blind_judge":
        path = settings.run_root / f"judgments/epoch-{epoch:02d}/{role_id}.blind.json"
        atomic_json(path, {**payload, "source_role_id": role_id})
        written.append(path)
    receipt_path = (
        settings.run_root
        / f"receipts/role_payloads/epoch-{epoch:02d}/{role_id}.attempt-{attempt}.json"
    )
    atomic_json(
        receipt_path,
        {
            "role_id": role_id,
            "attempt": attempt,
            "artifacts": {
                str(path.relative_to(settings.run_root)): sha256_file(path) for path in written
            },
        },
    )
    return [*written, receipt_path]


def dispatch_role_wave(
    settings: Settings,
    store: CampaignStore,
    roles: Sequence[Mapping[str, Any]],
    prompts: Mapping[str, str],
    *,
    epoch: int,
    wave_id: str,
    health_fetcher: Callable[[str], dict[str, Any]] = fetch_router_health,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Dispatch one dependency-ready wave through Fusion with one retry.

    The queue is always invoked as ``jnoccio``/``jnoccio-router``.  Fusion,
    rather than this controller, owns selection and rotation of credentials.
    """

    if not roles:
        return {"epoch": epoch, "wave_id": wave_id, "roles": 0, "valid": 0, "failed": []}
    if any(int(role.get("epoch", 0)) != epoch for role in roles):
        raise CampaignError("a dispatch wave may contain roles from only one epoch")
    pending = [dict(role) for role in roles]
    invalid_outputs: dict[str, tuple[str, list[str]]] = {}
    next_attempt_by_role: dict[str, int] = {}
    utilization_paths: list[Path] = []
    valid_role_ids: set[str] = set()
    with store.connect() as connection:
        for role in pending:
            role_id = str(role["id"])
            attempts = connection.execute(
                "SELECT attempt,state,result_path,valid,error_json FROM attempts "
                "WHERE role_id=? ORDER BY attempt",
                (role_id,),
            ).fetchall()
            if any(bool(row["valid"]) for row in attempts):
                valid_role_ids.add(role_id)
                next_attempt_by_role[role_id] = MAX_ATTEMPTS_PER_ROLE
                continue
            next_attempt_by_role[role_id] = len(attempts)
            if len(attempts) == 1:
                row = attempts[0]
                invalid_text = ""
                result_path = row["result_path"]
                if result_path and Path(str(result_path)).is_file():
                    try:
                        result = json.loads(Path(str(result_path)).read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        result = {}
                    if isinstance(result, dict):
                        invalid_text = str(result.get("assistant_text") or "")
                try:
                    stored_errors = json.loads(str(row["error_json"] or "[]"))
                except json.JSONDecodeError:
                    stored_errors = [str(row["error_json"])]
                invalid_outputs[role_id] = (
                    invalid_text,
                    [str(error) for error in stored_errors]
                    if isinstance(stored_errors, list)
                    else [str(stored_errors)],
                )
    for attempt in range(MAX_ATTEMPTS_PER_ROLE):
        attempt_roles = [
            role
            for role in pending
            if role["id"] not in valid_role_ids
            and next_attempt_by_role[str(role["id"])] == attempt
        ]
        if not attempt_roles:
            continue
        health = health_fetcher(settings.health_url)
        pool = reconcile_router_pool(discover_disk_profiles(settings.users_root), health)
        if not pool.valid:
            raise CampaignError("router pool mismatch before wave: " + "; ".join(pool.errors))
        pool_path = (
            settings.run_root
            / f"receipts/router_pool/epoch-{epoch:02d}-{wave_id}-attempt-{attempt}.json"
        )
        write_receipt(pool_path, "router_pool_snapshot", pool.receipt)
        workers = dynamic_worker_count(len(attempt_roles), health)
        jobs: list[dict[str, Any]] = []
        for role in attempt_roles:
            role_id = str(role["id"])
            if attempt == 0:
                if role_id not in prompts:
                    raise CampaignError(f"missing prompt for role {role_id}")
                prompt = str(prompts[role_id])
            else:
                invalid, errors = invalid_outputs[role_id]
                prompt = build_schema_retry_prompt(role, invalid, errors)
            if len(prompt.encode("utf-8")) > PROMPT_LIMIT_BYTES:
                raise CampaignError(f"prompt for {role_id} exceeds 12 KB")
            prompt_path = (
                settings.run_root
                / f"prompts/epoch-{epoch:02d}/{role_id}.attempt-{attempt}.json"
            )
            _atomic_text(prompt_path, prompt)
            store.prepare_lease(role_id, attempt, prompt_path)
            jobs.append({"id": role_id, "prompt": prompt, "priority": 1000 - attempt})
        jobs_path = (
            settings.run_root
            / f"queue/jobs/epoch-{epoch:02d}-{wave_id}.attempt-{attempt}.json"
        )
        atomic_json(jobs_path, jobs)
        for role in attempt_roles:
            store.submit_lease(str(role["id"]), attempt)
        results_dir = (
            settings.run_root
            / f"raw_responses/epoch-{epoch:02d}/{wave_id}.attempt-{attempt}"
        )
        results_dir.mkdir(parents=True, exist_ok=True)
        process = runner(
            [
                "jekko",
                "zyal-queue",
                "--db",
                str(settings.run_root / "queue/zyal.sqlite3"),
                "--run-id",
                f"{settings.run_id}-e{epoch:02d}-{wave_id}-a{attempt}",
                "--jobs",
                str(jobs_path),
                "--workers",
                str(workers),
                "--provider",
                "jnoccio",
                "--model",
                "jnoccio-router",
                "--results-dir",
                str(results_dir),
            ],
            cwd=settings.repo_root,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=7_300,
            check=False,
        )
        accounted_results: list[dict[str, Any]] = []
        next_pending: list[dict[str, Any]] = []
        for role in attempt_roles:
            role_id = str(role["id"])
            produced = results_dir / f"{role_id}.json"
            if produced.exists():
                try:
                    raw = json.loads(produced.read_text(encoding="utf-8"))
                except json.JSONDecodeError as error:
                    raw = {
                        "success": False,
                        "assistant_text": "",
                        "error": f"invalid queue result JSON: {error}",
                    }
            else:
                raw = {
                    "success": False,
                    "assistant_text": "",
                    "error": f"queue returned {process.returncode} without a result file",
                }
            if not isinstance(raw, dict):
                raw = {"success": False, "assistant_text": "", "error": "result is not an object"}
            safe = safe_raw_response(raw)
            text = str(safe["assistant_text"])
            errors: list[str] = []
            if _SECRET_VALUE_RE.search(text):
                errors.append("assistant output contained credential-like material")
                safe["assistant_text"] = "[credential-like output blocked]"
                text = ""
            if not isinstance(raw.get("credential_user_id"), str):
                errors.append("credential_user_id is required")
            payload = None
            if raw.get("success") is not True:
                errors.append(str(raw.get("error") or "Jnoccio result was unsuccessful"))
            else:
                payload, schema_errors = parse_epoch_result(role, text)
                errors.extend(schema_errors)
            valid = not errors and payload is not None
            persisted = produced
            atomic_json(persisted, safe)
            store.finish_attempt(
                role_id,
                attempt,
                result_path=persisted,
                valid=valid,
                credential_user_id=(
                    str(raw["credential_user_id"])
                    if isinstance(raw.get("credential_user_id"), str)
                    else None
                ),
                router_metadata=(
                    raw.get("router_metadata") if isinstance(raw.get("router_metadata"), dict) else None
                ),
                errors=errors,
            )
            accounted = dict(raw)
            accounted["success"] = valid
            accounted_results.append(accounted)
            if valid and payload is not None:
                _persist_role_payload(settings, role, attempt, payload)
                valid_role_ids.add(role_id)
            else:
                invalid_outputs[role_id] = (text, errors)
                next_attempt_by_role[role_id] = attempt + 1
                next_pending.append(role)
        utilization = utilization_receipt(
            epoch=epoch,
            wave_id=f"{wave_id}.attempt-{attempt}",
            requested_workers=workers,
            pool=pool.receipt,
            results=accounted_results,
        )
        utilization_path = (
            settings.run_root
            / f"receipts/utilization/epoch-{epoch:02d}-{wave_id}-attempt-{attempt}.json"
        )
        write_receipt(utilization_path, "per_user_utilization", utilization)
        utilization_paths.append(utilization_path)
        HashChain(settings.events_path).append(
            "jnoccio_wave",
            {
                "epoch": epoch,
                "wave_id": wave_id,
                "attempt": attempt,
                "requested_workers": workers,
                "eligible_slots": pool.receipt["eligible_slot_count"],
                "roles": len(attempt_roles),
                "valid": len(attempt_roles) - len(next_pending),
                "returncode": int(process.returncode),
                "results_missing_router_metadata": sum(
                    result.get("router_metadata") is None for result in accounted_results
                ),
                "utilization_sha256": sha256_file(utilization_path),
            },
        )
    failed = sorted(str(role["id"]) for role in pending if role["id"] not in valid_role_ids)
    return {
        "epoch": epoch,
        "wave_id": wave_id,
        "roles": len(roles),
        "valid": len(valid_role_ids),
        "failed": failed,
        "utilization_receipts": {
            str(path.relative_to(settings.run_root)): sha256_file(path)
            for path in utilization_paths
        },
    }


def utilization_receipt(
    *,
    epoch: int,
    wave_id: str,
    requested_workers: int,
    pool: Mapping[str, Any],
    results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    eligible = sorted(_positive_int_map(pool.get("per_user_slot_counts")))
    per_user: dict[str, dict[str, int]] = {
        user: {"jobs": 0, "successes": 0, "failures": 0, "rate_limits": 0}
        for user in eligible
    }
    successes = failures = rate_limits = 0
    covered: set[str] = set()
    for result in results:
        user = result.get("credential_user_id")
        metadata = sanitize_router_metadata(result.get("router_metadata")) or {}
        rate_limited = bool(metadata.get("rate_limited")) or int(
            metadata.get("rate_limit_count") or 0
        ) > 0
        successful = result.get("success") is True
        successes += int(successful)
        failures += int(not successful)
        rate_limits += int(rate_limited)
        if isinstance(user, str) and user in per_user:
            covered.add(user)
            per_user[user]["jobs"] += 1
            per_user[user]["successes"] += int(successful)
            per_user[user]["failures"] += int(not successful)
            per_user[user]["rate_limits"] += int(rate_limited)
    receipt = {
        "schema_version": CAMPAIGN_VERSION,
        "receipt_type": "per_user_utilization",
        "epoch": epoch,
        "wave_id": wave_id,
        "requested_workers": requested_workers,
        "eligible_slots": int(pool.get("eligible_slot_count") or 0),
        "jobs": len(results),
        "successes": successes,
        "failures": failures,
        "rate_limits": rate_limits,
        "eligible_user_ids": eligible,
        "covered_user_ids": sorted(covered),
        "per_user": per_user,
        "coverage_complete": set(eligible).issubset(covered),
    }
    validate_receipt("per_user_utilization", receipt)
    return receipt


def require_epoch_one_coverage(receipts: Sequence[Mapping[str, Any]]) -> None:
    eligible: set[str] = set()
    covered: set[str] = set()
    for receipt in receipts:
        if int(receipt.get("epoch", 0)) != 1:
            continue
        eligible.update(map(str, receipt.get("eligible_user_ids", [])))
        covered.update(map(str, receipt.get("covered_user_ids", [])))
    missing = sorted(eligible - covered)
    if not eligible or missing:
        raise CampaignError(
            "epoch-one router coverage is incomplete; stop before epoch two: " + str(missing)
        )


def strength_score(
    importance_percentile: float,
    residual_correlation_percentile: float,
    mutual_information_percentile: float,
) -> float:
    values = (importance_percentile, residual_correlation_percentile, mutual_information_percentile)
    if any(not 0.0 <= float(value) <= 1.0 for value in values):
        raise ValueError("strength percentiles must be within [0,1]")
    return float(0.60 * values[0] + 0.25 * values[1] + 0.15 * values[2])


def _percentiles(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    order = sorted(range(len(values)), key=lambda index: (values[index], index))
    result = [0.0] * len(values)
    if len(values) == 1:
        return [1.0]
    for rank, index in enumerate(order):
        result[index] = rank / (len(values) - 1)
    return result


def validate_discovery_protocol(protocol: Mapping[str, Any]) -> None:
    if tuple(protocol.get("seeds", ())) != SCREEN_SEEDS:
        raise CampaignError("discovery screening must use all three sealed seeds")
    if protocol.get("trees") != SCREEN_TREES:
        raise CampaignError("discovery screening must use 150-tree CatBoost")
    if protocol.get("task_type") != "GPU":
        raise CampaignError("discovery screening must use GPU CatBoost")
    if protocol.get("confirmation_folds_accessed") is not False:
        raise CampaignError("discovery may not access sealed confirmation folds")


def rank_discovery_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Rank columns with every preregistered screening and redundancy component."""

    ranked: list[dict[str, Any]] = []
    required = {
        "feature_id",
        "family_id",
        "target",
        "domain",
        "compute_seconds",
        "redundancy",
        "oof_residual_correlation",
        "spearman_correlation",
        "mutual_information",
        "catboost_importance_by_seed",
    }
    for target in TARGETS:
        target_rows = [dict(row) for row in records if row.get("target") == target]
        if not target_rows:
            continue
        importance_values: list[float] = []
        residual_values: list[float] = []
        mutual_information_values: list[float] = []
        for row in target_rows:
            missing = required - set(row)
            if missing:
                raise ValueError(f"discovery record missing fields: {sorted(missing)}")
            if row["domain"] not in {domain.id for domain in DOMAINS}:
                raise ValueError("discovery record has an invalid domain")
            by_seed = row["catboost_importance_by_seed"]
            if not isinstance(by_seed, dict) or {int(seed) for seed in by_seed} != set(SCREEN_SEEDS):
                raise ValueError("CatBoost importance must contain exactly the three screen seeds")
            importance_values.append(float(np.median([float(value) for value in by_seed.values()])))
            residual_values.append(abs(float(row["oof_residual_correlation"])))
            mutual_information_values.append(float(row["mutual_information"]))
            for field_name in ("compute_seconds", "redundancy", "spearman_correlation"):
                value = float(row[field_name])
                if not math.isfinite(value):
                    raise ValueError(f"discovery {field_name} must be finite")
        importance_percentiles = _percentiles(importance_values)
        residual_percentiles = _percentiles(residual_values)
        mi_percentiles = _percentiles(mutual_information_values)
        for index, row in enumerate(target_rows):
            components = {
                "catboost_importance_percentile": importance_percentiles[index],
                "residual_correlation_percentile": residual_percentiles[index],
                "mutual_information_percentile": mi_percentiles[index],
            }
            row["median_catboost_importance"] = importance_values[index]
            row["strength_components"] = components
            row["strength"] = strength_score(*components.values())
            ranked.append(row)
    ranked.sort(
        key=lambda row: (
            str(row["target"]),
            -float(row["strength"]),
            float(row["compute_seconds"]),
            float(row["redundancy"]),
            abs(float(row["spearman_correlation"])),
            str(row["feature_id"]),
        )
    )
    for target in TARGETS:
        for rank, row in enumerate(
            (item for item in ranked if item["target"] == target), start=1
        ):
            row["rank"] = rank
    return ranked


def categorical_agent_feedback(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Remove exact scores before any adaptive role can receive screening output."""

    packet: dict[str, dict[str, str]] = {}
    for row in records:
        rank = int(row["rank"])
        strength = float(row["strength"])
        packet[str(row["feature_id"])] = {
            "rank_band": "high" if rank <= 10 else ("medium" if rank <= 50 else "low"),
            "strength": "high" if strength >= 0.67 else ("medium" if strength >= 0.34 else "low"),
            "compute": "fast" if float(row["compute_seconds"]) <= 1.0 else "slow",
            "redundancy": "low" if float(row["redundancy"]) <= 0.25 else "high",
        }
    return {"categorical_only": True, "feature_feedback": packet}


def rank_discovery_families(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate validated column rankings without discarding cost or correlation evidence."""

    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        groups[(str(row["target"]), str(row["family_id"]))].append(row)
    families = []
    for (target, family_id), rows in groups.items():
        families.append(
            {
                "target": target,
                "family_id": family_id,
                "domain": str(rows[0]["domain"]),
                "valid_columns": len(rows),
                "strength": float(np.median([float(row["strength"]) for row in rows])),
                "compute_seconds": float(sum(float(row["compute_seconds"]) for row in rows)),
                "redundancy": float(np.mean([float(row["redundancy"]) for row in rows])),
                "oof_residual_correlation": float(
                    np.max([abs(float(row["oof_residual_correlation"])) for row in rows])
                ),
                "spearman_correlation": float(
                    np.mean([abs(float(row["spearman_correlation"])) for row in rows])
                ),
                "mutual_information": float(
                    np.max([float(row["mutual_information"]) for row in rows])
                ),
                "median_catboost_importance": float(
                    np.median([float(row["median_catboost_importance"]) for row in rows])
                ),
            }
        )
    families.sort(
        key=lambda row: (
            row["target"],
            -row["strength"],
            row["compute_seconds"],
            row["redundancy"],
            row["family_id"],
        )
    )
    for target in TARGETS:
        for rank, row in enumerate(
            (item for item in families if item["target"] == target), start=1
        ):
            row["rank"] = rank
    return families


def build_top50_reports(records: Sequence[Mapping[str, Any]], output_dir: Path) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    for target in TARGETS:
        target_rows = []
        for source in records:
            if source.get("target") != target:
                continue
            row = dict(source)
            components = row.get("strength_components")
            if not isinstance(components, dict):
                raise ValueError("top feature lacks strength_components")
            row["strength"] = strength_score(
                float(components["catboost_importance_percentile"]),
                float(components["residual_correlation_percentile"]),
                float(components["mutual_information_percentile"]),
            )
            row.setdefault("schema_version", CAMPAIGN_VERSION)
            row.setdefault("receipt_type", "top_feature_record")
            validate_receipt("top_feature_record", row)
            target_rows.append(row)
        target_rows.sort(key=lambda row: (-float(row["strength"]), str(row["feature_id"])))
        if len(target_rows) < 25:
            raise CampaignError(f"{target} has only {len(target_rows)} top-feature candidates")
        selected.extend(target_rows[:25])
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "top50_features.json"
    atomic_json(json_path, selected)
    lines = ["# Top 50 Features", ""]
    for target in TARGETS:
        lines.extend([f"## {target}", ""])
        for row in (item for item in selected if item["target"] == target):
            lines.append(
                f"- `{row['feature_id']}` — {row['domain']} — strength "
                f"{float(row['strength']):.6f}: {row['physical_rationale']}"
            )
        lines.append("")
    md_path = output_dir / "top50_features.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "features": len(selected),
        "per_target": 25,
        "json_sha256": sha256_file(json_path),
        "markdown_sha256": sha256_file(md_path),
    }


def validate_genetic_history(receipt: Mapping[str, Any]) -> None:
    validate_receipt("genetic_reduction_history", receipt)
    if receipt["population_size"] != GENETIC_POPULATION:
        raise ReceiptError("genetic population must be 24")
    if receipt["generations"] != GENETIC_GENERATIONS:
        raise ReceiptError("genetic reduction must run ten generations")
    history = receipt["history"]
    if not isinstance(history, list) or len(history) != GENETIC_GENERATIONS:
        raise ReceiptError("genetic history must contain ten generations")
    views = receipt["preregistered_views"]
    if not isinstance(views, list) or not 1 <= len(views) <= MAX_CONFIRMATION_VIEWS_PER_TARGET:
        raise ReceiptError("one to eight confirmation views must be preregistered")
    ids = [str(view.get("view_id")) for view in views if isinstance(view, dict)]
    if len(ids) != len(set(ids)):
        raise ReceiptError("genetic confirmation view IDs must be unique")
    seen_families: set[str] = set()
    for view in views:
        if not isinstance(view, dict):
            raise ReceiptError("genetic confirmation views must be objects")
        families = set(map(str, view.get("families", [])))
        if families & seen_families and view.get("diversity_aware") is not True:
            raise ReceiptError("overlapping confirmation views must be diversity-aware")
        seen_families.update(families)


def seal_confirmation_folds(
    output_dir: Path,
    train_row_ids: Sequence[Any],
    *,
    resume: bool = False,
) -> dict[str, Any]:
    """Create the two fresh shuffled five-fold assignments exactly once."""

    if len(train_row_ids) != TRAIN_ROWS or len(set(map(str, train_row_ids))) != TRAIN_ROWS:
        raise ValueError("confirmation sealing requires 2,400 unique training row IDs")
    marker = output_dir / "confirmation-opened.json"
    if marker.exists():
        if not resume:
            raise CampaignError("confirmation folds were already opened")
        existing = json.loads(marker.read_text(encoding="utf-8"))
        for seed, expected in zip(CONFIRMATION_SEEDS, existing["fold_hashes"], strict=True):
            path = output_dir / f"folds-seed-{seed}.npy"
            if not path.exists() or sha256_file(path) != expected:
                raise CampaignError("sealed confirmation fold hash changed during resume")
        return existing
    output_dir.mkdir(parents=True, exist_ok=True)
    fold_hashes = []
    for seed in CONFIRMATION_SEEDS:
        rng = np.random.default_rng(seed)
        order = rng.permutation(len(train_row_ids))
        folds = np.empty(len(train_row_ids), dtype=np.int8)
        folds[order] = np.arange(len(train_row_ids), dtype=np.int64) % CONFIRMATION_FOLDS
        path = output_dir / f"folds-seed-{seed}.npy"
        np.save(path, folds, allow_pickle=False)
        unique, counts = np.unique(folds, return_counts=True)
        if unique.tolist() != list(range(CONFIRMATION_FOLDS)) or counts.tolist() != [480] * 5:
            raise AssertionError("confirmation fold seal is not balanced")
        fold_hashes.append(sha256_file(path))
    marker_payload = {
        "opened_once": True,
        "opened_at": utc_now(),
        "seeds": list(CONFIRMATION_SEEDS),
        "folds": CONFIRMATION_FOLDS,
        "fold_hashes": fold_hashes,
        "row_id_sha256": _sha256_json(list(map(str, train_row_ids))),
    }
    atomic_json(marker, marker_payload)
    return marker_payload


def select_confirmed_winners(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Choose each target independently by error; feature count is never a tie-break."""

    winners: dict[str, dict[str, Any]] = {}
    compact: dict[str, dict[str, Any]] = {}
    for target in TARGETS:
        candidates = [dict(row) for row in rows if row.get("target") == target and row.get("kind") == "candidate"]
        if not candidates:
            raise CampaignError(f"confirmation has no candidate for {target}")
        winners[target] = min(candidates, key=lambda row: (float(row["mean_rmsle"]), str(row["view_id"])))
        compact_candidates = [row for row in candidates if row.get("compact") is True]
        if not compact_candidates:
            smallest = min(int(row["feature_count"]) for row in candidates)
            compact_candidates = [row for row in candidates if int(row["feature_count"]) == smallest]
        compact[target] = min(
            compact_candidates,
            key=lambda row: (float(row["mean_rmsle"]), str(row["view_id"])),
        )
    return {
        "winners": winners,
        "confirmed_mean_rmsle": float(np.mean([winners[target]["mean_rmsle"] for target in TARGETS])),
        "compact_alternative": {
            "targets": compact,
            "mean_rmsle": float(np.mean([compact[target]["mean_rmsle"] for target in TARGETS])),
        },
    }


def validate_confirmation_receipt(receipt: Mapping[str, Any]) -> None:
    validate_receipt("sealed_confirmation_result", receipt)
    if tuple(receipt["seeds"]) != CONFIRMATION_SEEDS:
        raise ReceiptError("confirmation seeds differ from the two sealed seeds")
    if receipt["folds"] != CONFIRMATION_FOLDS or receipt["trees"] != CONFIRMATION_TREES:
        raise ReceiptError("confirmation must use shuffled five-fold/400-tree CatBoost")
    if receipt["task_type"] != "GPU" or receipt["opened_once"] is not True:
        raise ReceiptError("confirmation must be a one-shot GPU run")
    controls = receipt["controls"]
    if not isinstance(controls, list):
        raise ReceiptError("confirmation controls must be a list")
    required = {
        (target, control)
        for target in TARGETS
        for control in ("current_champion", "atlas_winner", "existing_809")
    }
    observed = {
        (str(row.get("target")), str(row.get("control")))
        for row in controls
        if isinstance(row, dict)
    }
    if not required.issubset(observed):
        raise ReceiptError("current champion, Atlas, and existing-809 controls must be rerun")
    rows = receipt["views"]
    for row in [*controls, *rows]:
        if not isinstance(row, dict):
            raise ReceiptError("confirmation controls and views must be objects")
        if (
            row.get("fold_hashes") != receipt["fold_hashes"]
            or tuple(row.get("seeds", ())) != CONFIRMATION_SEEDS
            or row.get("folds") != CONFIRMATION_FOLDS
            or row.get("trees") != CONFIRMATION_TREES
        ):
            raise ReceiptError("every confirmation score must use the exact same sealed folds")
    selected = select_confirmed_winners(rows)
    if selected["winners"] != receipt["winners"]:
        raise ReceiptError("confirmation winners were not independently lowest per target")
    if not math.isclose(
        float(selected["confirmed_mean_rmsle"]),
        float(receipt["confirmed_mean_rmsle"]),
        rel_tol=0,
        abs_tol=1e-12,
    ):
        raise ReceiptError("confirmed mean does not match the independently selected pair")
    if selected["compact_alternative"] != receipt["compact_alternative"]:
        raise ReceiptError("compact alternative does not match the strongest compact pair")


def campaign_phases() -> tuple[str, ...]:
    phases = ["indexing"]
    for epoch in range(1, EPOCHS + 1):
        phases.extend(
            f"epoch-{epoch:02d}-{name}"
            for name in ("generation", "compilation", "execution", "screening", "reduction")
        )
    phases.extend(("confirmation", "judging", "promotion"))
    return tuple(phases)


def _run_single_phase(settings: Settings, phase: str, backend: PhaseBackend) -> dict[str, Any]:
    if phase not in campaign_phases():
        raise ValueError(f"unsupported campaign phase: {phase}")
    store = CampaignStore(settings)
    if store.phase_complete(phase):
        path = settings.run_root / "receipts/phases" / f"{phase}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
            "phase": phase,
            "resumed": True,
        }
    result = backend.execute(settings, phase)
    if isinstance(result, PhaseResult):
        payload, path = result.payload, result.receipt_path
    elif isinstance(result, dict):
        payload, path = result, None
    else:
        raise CampaignError(f"backend returned an invalid result for {phase}")
    if path is None:
        path = _phase_receipt_path(settings, phase)
        assert_secret_free(payload)
        atomic_json(path, payload)
    store.complete_phase(phase, path)
    HashChain(settings.events_path).append(
        "phase_complete", {"phase": phase, "receipt_sha256": sha256_file(path)}
    )
    return payload


def run_epoch_phase(settings: Settings, epoch: int, backend: PhaseBackend) -> dict[str, Any]:
    """Run all dependency-ordered internal phases for one epoch."""

    if epoch not in range(1, EPOCHS + 1):
        raise ValueError("epoch must be between 1 and 10")
    results = {}
    for name in ("generation", "compilation", "execution", "screening", "reduction"):
        phase = f"epoch-{epoch:02d}-{name}"
        results[name] = _run_single_phase(settings, phase, backend)
    return {"epoch": epoch, "phases": results}


def run_compilation_phase(settings: Settings, epoch: int, backend: PhaseBackend) -> dict[str, Any]:
    return _run_single_phase(settings, f"epoch-{epoch:02d}-compilation", backend)


def run_execution_phase(settings: Settings, epoch: int, backend: PhaseBackend) -> dict[str, Any]:
    return _run_single_phase(settings, f"epoch-{epoch:02d}-execution", backend)


def run_screening_phase(settings: Settings, epoch: int, backend: PhaseBackend) -> dict[str, Any]:
    return _run_single_phase(settings, f"epoch-{epoch:02d}-screening", backend)


def run_reduction_phase(settings: Settings, epoch: int, backend: PhaseBackend) -> dict[str, Any]:
    return _run_single_phase(settings, f"epoch-{epoch:02d}-reduction", backend)


def run_confirmation_phase(settings: Settings, backend: PhaseBackend) -> dict[str, Any]:
    return _run_single_phase(settings, "confirmation", backend)


def run_judging_phase(settings: Settings, backend: PhaseBackend) -> dict[str, Any]:
    return _run_single_phase(settings, "judging", backend)


def run_promotion_phase(settings: Settings, backend: PhaseBackend) -> dict[str, Any]:
    return _run_single_phase(settings, "promotion", backend)


class FilesystemPhaseBackend:
    """Adopt only already materialized controller receipts, failing closed otherwise."""

    def execute(self, settings: Settings, phase: str) -> PhaseResult:
        path = settings.run_root / "receipts/phases" / f"{phase}.json"
        if not path.exists():
            raise CampaignError(
                f"phase {phase} requires its controller-produced receipt at {path}"
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise CampaignError(f"phase {phase} receipt must be an object")
        assert_secret_free(payload)
        return PhaseResult(str(payload.get("receipt_type") or "phase"), payload, path)


def _phase_receipt_path(settings: Settings, phase: str) -> Path:
    return settings.run_root / "receipts/phases" / f"{phase}.json"


def _execute_campaign(settings: Settings, backend: PhaseBackend, *, resume_run: bool) -> dict[str, Any]:
    preflight_path = settings.run_root / "preflight.json"
    if not preflight_path.exists():
        status = preflight(settings)
    else:
        status = json.loads(preflight_path.read_text(encoding="utf-8"))
    if status.get("ready") is not True:
        raise CampaignError("preflight blockers: " + "; ".join(status.get("blockers", [])))
    stage_controller_snapshot(settings)
    store = CampaignStore(settings)
    if resume_run:
        recovered = store.recover_interrupted_leases()
        HashChain(settings.events_path).append("campaign_resumed", {"recovered_leases": recovered})
    else:
        HashChain(settings.events_path).append("campaign_started", {"run_id": settings.run_id})
    for phase in campaign_phases():
        if store.phase_complete(phase):
            continue
        result = backend.execute(settings, phase)
        if isinstance(result, PhaseResult):
            payload, path = result.payload, result.receipt_path
        elif isinstance(result, dict):
            payload, path = result, None
        else:
            raise CampaignError(f"backend returned an invalid result for {phase}")
        if path is None:
            path = _phase_receipt_path(settings, phase)
            assert_secret_free(payload)
            atomic_json(path, payload)
        store.complete_phase(phase, path)
        HashChain(settings.events_path).append(
            "phase_complete", {"phase": phase, "receipt_sha256": sha256_file(path)}
        )
        if phase == "epoch-01-reduction":
            utilization = [
                json.loads(item.read_text(encoding="utf-8"))
                for item in sorted((settings.run_root / "receipts/utilization").glob("epoch-01-*.json"))
            ]
            require_epoch_one_coverage(utilization)
    return verify(settings)


def run(settings: Settings, *, backend: PhaseBackend | None = None) -> dict[str, Any]:
    return _execute_campaign(settings, backend or FilesystemPhaseBackend(), resume_run=False)


def resume(settings: Settings, *, backend: PhaseBackend | None = None) -> dict[str, Any]:
    return _execute_campaign(settings, backend or FilesystemPhaseBackend(), resume_run=True)


def status(settings: Settings) -> dict[str, Any]:
    if not settings.state_path.exists():
        return {"run_id": settings.run_id, "state": "not_preflighted"}
    store = CampaignStore(settings)
    with store.connect() as connection:
        campaign = connection.execute(
            "SELECT * FROM campaign WHERE run_id=?", (settings.run_id,)
        ).fetchone()
    chain_valid, chain_error = HashChain(settings.events_path).verify()
    return {
        "run_id": settings.run_id,
        "state": campaign["state"] if campaign else "unknown",
        "phase": campaign["phase"] if campaign else None,
        "error": campaign["error"] if campaign else None,
        "counts": store.counters(),
        "budget": store.budget_summary().__dict__,
        "completed_phases": len(store.phase_receipts()),
        "total_phases": len(campaign_phases()),
        "hash_chain_valid": chain_valid,
        "hash_chain_error": chain_error,
    }


def _artifact_hashes(run_root: Path, paths: Iterable[Path]) -> dict[str, str]:
    result = {}
    for path in sorted({item.resolve() for item in paths}):
        if not path.is_file() or not path.is_relative_to(run_root.resolve()):
            raise CampaignError(f"promotion artifact is missing or outside the run root: {path}")
        result[str(path.relative_to(run_root.resolve()))] = sha256_file(path)
    return result


def write_promotion_manifest(settings: Settings, paths: Iterable[Path], report: Mapping[str, Any]) -> Path:
    manifest = {
        "schema_version": CAMPAIGN_VERSION,
        "run_id": settings.run_id,
        "delivery": "promotion-inbox-only",
        "automatic_merge": False,
        "automatic_submit": False,
        "nomad_crystal360_modified": False,
        "artifacts": _artifact_hashes(settings.run_root, paths),
        "winner": report.get("winner"),
        "compact_alternative": report.get("compact_alternative"),
    }
    manifest["manifest_sha256"] = _sha256_json(manifest)
    path = settings.run_root / "promotion/final_manifest.json"
    atomic_json(path, manifest)
    atomic_json(settings.run_root / "final_manifests/promotion_manifest.json", manifest)
    return path


def verify_promotion_manifest(path: Path, run_root: Path | None = None) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not path.exists():
        return False, ["promotion manifest is missing"]
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return False, [f"promotion manifest is invalid JSON: {error}"]
    root = (run_root or path.parent.parent).resolve()
    supplied = manifest.get("manifest_sha256")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if supplied != _sha256_json(body):
        errors.append("promotion manifest content hash differs")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("promotion artifact map is missing")
        return False, errors
    for relative, expected in artifacts.items():
        candidate = (root / str(relative)).resolve()
        if not candidate.is_relative_to(root):
            errors.append(f"artifact escapes run root: {relative}")
        elif not candidate.is_file():
            errors.append(f"artifact is missing: {relative}")
        elif sha256_file(candidate) != expected:
            errors.append(f"artifact hash differs: {relative}")
    return not errors, errors


def verify(settings: Settings) -> dict[str, Any]:
    missing: list[str] = []
    if not settings.state_path.exists():
        return {"run_id": settings.run_id, "complete": False, "missing": ["campaign state"]}
    store = CampaignStore(settings)
    counts = store.counters()
    if counts["roles"] != EXPECTED_JNOCCIO_ROLES:
        missing.append("exactly 360 stable roles")
    if counts["roles_complete"] != EXPECTED_JNOCCIO_ROLES:
        missing.append("all 360 roles complete")
    budget = store.budget_summary()
    if budget.attempts > MAX_JNOCCIO_ATTEMPTS:
        missing.append("at most 720 Jnoccio attempts")
    if budget.debited_usd + budget.reserved_usd > MAX_COST_USD:
        missing.append("conservative cost at or below $2,000")
    if counts["new_executed_columns"] < MIN_NEW_EXECUTED_COLUMNS:
        missing.append("at least 7,000 newly executed columns")
    if counts["novel_valid_columns"] < MIN_NOVEL_VALID_COLUMNS:
        missing.append("at least 3,000 novel valid columns")
    for domain in DOMAINS:
        if counts["valid_by_domain"].get(domain.id, 0) < MIN_VALID_PER_DOMAIN:
            missing.append(f"{domain.id}: at least 200 novel valid columns")
    if counts["base_families"] < MIN_BASE_FAMILIES:
        missing.append("at least 160 valid base families")
    completed = store.phase_receipts()
    for phase in campaign_phases():
        if phase not in completed:
            missing.append(f"phase receipt: {phase}")
    required_metrics = {
        "compute_cost",
        "redundancy",
        "oof_residual_correlation",
        "spearman_correlation",
        "mutual_information",
        "catboost_importance",
    }
    for epoch in range(1, EPOCHS + 1):
        phase_payloads: dict[str, dict[str, Any]] = {}
        for name in ("generation", "compilation", "execution", "screening", "reduction"):
            path = _phase_receipt_path(settings, f"epoch-{epoch:02d}-{name}")
            if not path.exists():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("receipt is not an object")
                assert_secret_free(payload)
                phase_payloads[name] = payload
            except (json.JSONDecodeError, ReceiptError, ValueError) as error:
                missing.append(f"epoch {epoch} {name} phase contract: {error}")
        generation = phase_payloads.get("generation", {})
        if not (
            generation.get("epoch") == epoch
            and generation.get("roles") == ROLES_PER_EPOCH
            and generation.get("max_retries_per_role") == 1
            and generation.get("strict_json") is True
            and generation.get("controller_generated_ids") is True
        ):
            missing.append(f"epoch {epoch}: strict 36-role generation contract")
        compilation = phase_payloads.get("compilation", {})
        if not (
            compilation.get("epoch") == epoch
            and compilation.get("static_checks_passed") is True
            and compilation.get("plugin_limit_bytes") == PLUGIN_LIMIT_BYTES
            and compilation.get("individual_column_quarantine") is True
        ):
            missing.append(f"epoch {epoch}: compilation/static-check contract")
        execution = phase_payloads.get("execution", {})
        if not (
            execution.get("epoch") == epoch
            and execution.get("smoke_structures") == 16
            and execution.get("invariance_structures") == 64
            and execution.get("train_rows") == TRAIN_ROWS
            and execution.get("test_rows") == TEST_ROWS
            and execution.get("all_five_invariances") is True
            and execution.get("deterministic") is True
            and execution.get("individual_column_quarantine") is True
            and execution.get("test_labels_used") is False
        ):
            missing.append(f"epoch {epoch}: 16/64/2400/600 execution contract")
        screening = phase_payloads.get("screening", {})
        try:
            validate_discovery_protocol(screening.get("protocol", {}))
        except CampaignError:
            missing.append(f"epoch {epoch}: three-seed CatBoost screening protocol")
        if set(screening.get("ranking_metrics", [])) != required_metrics:
            missing.append(f"epoch {epoch}: complete discovery ranking metrics")
        if screening.get("adaptive_feedback") != "categorical_only":
            missing.append(f"epoch {epoch}: categorical-only adaptive feedback")
        reduction = phase_payloads.get("reduction", {})
        views = reduction.get("preregistered_views_per_target", {})
        if not (
            reduction.get("population_size") == GENETIC_POPULATION
            and reduction.get("generations") == GENETIC_GENERATIONS
            and isinstance(views, dict)
            and set(views) == set(TARGETS)
            and all(1 <= int(value) <= MAX_CONFIRMATION_VIEWS_PER_TARGET for value in views.values())
            and reduction.get("confirmation_still_sealed") is True
        ):
            missing.append(f"epoch {epoch}: family-aware 24x10 genetic reduction contract")
    for plugin in (settings.run_root / "plugins").rglob("*.py"):
        source = plugin.read_text(encoding="utf-8")
        plugin_errors = static_check_plugin(source)
        if plugin_errors:
            missing.append(f"sandboxed plugin contract {plugin.name}: {plugin_errors[:3]}")
    baseline_path = settings.run_root / "receipts/baseline-index.json"
    if not baseline_path.exists():
        missing.append("10,800-column baseline index receipt")
    else:
        try:
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            if (
                baseline.get("baseline_columns") != BASELINE_REGISTRY_COLUMNS
                or baseline.get("graduated_zyal_columns") != BASELINE_ZYAL_COLUMNS
                or baseline.get("current_champion_mean_rmsle")
                != CURRENT_CHAMPION_MEAN_RMSLE
            ):
                missing.append("preserved registry, ZYAL, and champion baselines")
        except json.JSONDecodeError as error:
            missing.append(f"valid baseline index receipt: {error}")
    router_paths = sorted((settings.run_root / "receipts/router_pool").glob("*.json"))
    utilization_all = sorted((settings.run_root / "receipts/utilization").glob("*.json"))
    if not router_paths:
        missing.append("router-pool snapshot receipts")
    for path in router_paths:
        try:
            validate_receipt(
                "router_pool_snapshot", json.loads(path.read_text(encoding="utf-8"))
            )
        except (json.JSONDecodeError, ReceiptError) as error:
            missing.append(f"valid router-pool receipt {path.name}: {error}")
    if len(router_paths) < len(utilization_all) + 1:
        missing.append("router pool was re-queried before every utilization wave")
    utilization_epochs: set[int] = set()
    for path in utilization_all:
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
            validate_receipt("per_user_utilization", receipt)
            utilization_epochs.add(int(receipt["epoch"]))
        except (json.JSONDecodeError, ReceiptError, TypeError, ValueError) as error:
            missing.append(f"valid utilization receipt {path.name}: {error}")
    if utilization_epochs != set(range(1, EPOCHS + 1)):
        missing.append("per-user utilization receipts for all ten epochs")
    epoch_paths = sorted((settings.run_root / "receipts/epochs").glob("epoch-*.json"))
    epoch_numbers: set[int] = set()
    for path in epoch_paths:
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
            validate_receipt("epoch_result", receipt)
            epoch_numbers.add(int(receipt["epoch"]))
        except (json.JSONDecodeError, ReceiptError, TypeError, ValueError) as error:
            missing.append(f"valid epoch receipt {path.name}: {error}")
    if epoch_numbers != set(range(1, EPOCHS + 1)):
        missing.append("epoch result receipts for all ten epochs")
    top_json = settings.run_root / "reports/top50/top50_features.json"
    if not top_json.exists() or not (settings.run_root / "reports/top50/top50_features.md").exists():
        missing.append("top-50 JSON and Markdown reports")
    else:
        try:
            top = json.loads(top_json.read_text(encoding="utf-8"))
            if len(top) != 50 or Counter(row.get("target") for row in top) != Counter(
                {target: 25 for target in TARGETS}
            ):
                missing.append("exactly 25 top features per target")
            for row in top:
                validate_receipt("top_feature_record", row)
        except (json.JSONDecodeError, ReceiptError, TypeError) as error:
            missing.append(f"valid top-feature records: {error}")
    genetic_paths = sorted((settings.run_root / "receipts/genetic").glob("*.json"))
    if len(genetic_paths) < len(TARGETS):
        missing.append("genetic reduction history for both targets")
    for path in genetic_paths:
        try:
            validate_genetic_history(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, ReceiptError) as error:
            missing.append(f"valid genetic receipt {path.name}: {error}")
    confirmation_path = settings.run_root / "receipts/confirmation/sealed-results.json"
    confirmation: dict[str, Any] | None = None
    if not confirmation_path.exists():
        missing.append("sealed two-seed confirmation receipt")
    else:
        try:
            confirmation = json.loads(confirmation_path.read_text(encoding="utf-8"))
            validate_confirmation_receipt(confirmation)
            seal_path = settings.run_root / "confirmation/sealed/confirmation-opened.json"
            if not seal_path.exists():
                missing.append("sealed confirmation fold marker")
            else:
                seal = json.loads(seal_path.read_text(encoding="utf-8"))
                if seal.get("fold_hashes") != confirmation.get("fold_hashes"):
                    missing.append("confirmation receipt is not bound to sealed fold hashes")
                for seed, expected in zip(
                    CONFIRMATION_SEEDS, confirmation.get("fold_hashes", []), strict=True
                ):
                    fold_path = settings.run_root / f"confirmation/sealed/folds-seed-{seed}.npy"
                    if not fold_path.exists() or sha256_file(fold_path) != expected:
                        missing.append(f"sealed confirmation folds for seed {seed}")
            controls = {
                (row["target"], row["control"]): float(row["mean_rmsle"])
                for row in confirmation["controls"]
            }
            for target in TARGETS:
                winner = float(confirmation["winners"][target]["mean_rmsle"])
                if winner > controls[(target, "current_champion")]:
                    missing.append(f"{target}: no target regression against same-fold champion")
            if float(confirmation["confirmed_mean_rmsle"]) >= float(
                np.mean([controls[(target, "current_champion")] for target in TARGETS])
            ):
                missing.append("confirmed mean below the same-fold current champion")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, ReceiptError) as error:
            missing.append(f"valid sealed confirmation: {error}")
    utilization_paths = sorted((settings.run_root / "receipts/utilization").glob("epoch-01-*.json"))
    try:
        require_epoch_one_coverage(
            [json.loads(path.read_text(encoding="utf-8")) for path in utilization_paths]
        )
    except (json.JSONDecodeError, CampaignError) as error:
        missing.append(f"epoch-one multi-user coverage: {error}")
    blind_judgments = list((settings.run_root / "judgments").glob("epoch-*/*.blind.json"))
    if len(blind_judgments) != EPOCHS * ROLE_COUNTS["blind_judge"]:
        missing.append("two receipt-bound blind judgments per epoch")
    identity_path = settings.run_root / "inputs/controller/identity.json"
    try:
        stage_controller_snapshot(settings)
    except (CampaignError, OSError, json.JSONDecodeError) as error:
        missing.append(f"frozen controller snapshot: {error}")
    if identity_path.exists():
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        current = _tree_identity(settings.repo_root / "nomad_crystal360")
        if current != identity.get("nomad_crystal360_sha256"):
            missing.append("nomad_crystal360 remained unchanged")
    chain_valid, chain_error = HashChain(settings.events_path).verify()
    if not chain_valid:
        missing.append(f"valid event hash chain: {chain_error}")
    promotion = settings.run_root / "promotion/final_manifest.json"
    if promotion.exists():
        valid, errors = verify_promotion_manifest(promotion, settings.run_root)
        if not valid:
            missing.extend(f"promotion: {error}" for error in errors)
    report = {
        "run_id": settings.run_id,
        "campaign_version": CAMPAIGN_VERSION,
        "verified_at": utc_now(),
        "complete": not missing,
        "missing": missing,
        "counts": counts,
        "budget": budget.__dict__,
        "winner": confirmation.get("winners") if confirmation else None,
        "confirmed_mean_rmsle": confirmation.get("confirmed_mean_rmsle") if confirmation else None,
        "compact_alternative": confirmation.get("compact_alternative") if confirmation else None,
        "delivery": "promotion-inbox-only",
        "automatic_merge": False,
        "automatic_submit": False,
        "nomad_crystal360_modified": False,
        "hash_chain_valid": chain_valid,
    }
    atomic_json(settings.run_root / "verification.json", report)
    if report["complete"] and not promotion.exists():
        promotion_inputs = [
            path
            for directory in (
                "families",
                "specs",
                "plugins",
                "matrices/validated",
                "score_curves",
                "reports/top50",
                "genetic",
                "confirmation",
                "judgments",
                "receipts",
            )
            for path in (settings.run_root / directory).rglob("*")
            if path.is_file()
        ]
        write_promotion_manifest(settings, promotion_inputs, report)
        valid, errors = verify_promotion_manifest(
            settings.run_root / "promotion/final_manifest.json", settings.run_root
        )
        if not valid:
            report["complete"] = False
            report["missing"].extend(f"promotion: {error}" for error in errors)
            atomic_json(settings.run_root / "verification.json", report)
    with store.connect() as connection:
        connection.execute(
            "UPDATE campaign SET state=?,error=? WHERE run_id=?",
            (
                "complete" if report["complete"] else "incomplete",
                "; ".join(report["missing"]) or None,
                settings.run_id,
            ),
        )
    return report


def _settings_from_args(args: argparse.Namespace) -> Settings:
    return Settings(
        repo_root=Path(args.repo_root).resolve(),
        run_id=args.run_id,
        nomad_root=Path(args.nomad_root).resolve(),
        inbox_root=Path(args.inbox_root).resolve(),
        users_root=Path(args.users_root).resolve(),
        synchronizer=Path(args.synchronizer).resolve(),
        health_url=args.health_url,
        baseline_columns_path=(
            Path(args.baseline_columns).resolve() if args.baseline_columns else None
        ),
        zyal_summary_path=(Path(args.zyal_summary).resolve() if args.zyal_summary else None),
        image=args.image,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NOMAD ZYAL v2.1 ten-epoch foundry")
    parser.add_argument("command", choices=("preflight", "run", "resume", "status", "verify"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--nomad-root", default=str(DEFAULT_NOMAD_ROOT))
    parser.add_argument("--inbox-root", default=str(DEFAULT_INBOX_ROOT))
    parser.add_argument("--users-root", default=str(DEFAULT_USERS_ROOT))
    parser.add_argument("--synchronizer", default=str(DEFAULT_SYNCHRONIZER))
    parser.add_argument("--health-url", default=DEFAULT_HEALTH_URL)
    parser.add_argument("--baseline-columns")
    parser.add_argument("--zyal-summary")
    parser.add_argument("--image", default="nomad-feature-sandbox:2026-07-18")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = _settings_from_args(args)
    try:
        if args.command == "preflight":
            result = preflight(settings)
        elif args.command == "run":
            result = run(settings)
        elif args.command == "resume":
            result = resume(settings)
        elif args.command == "status":
            result = status(settings)
        else:
            result = verify(settings)
        print(json.dumps(result, indent=2, sort_keys=True))
        if args.command == "preflight" and result.get("ready") is not True:
            return 2
        if args.command in {"run", "resume", "verify"} and result.get("complete") is not True:
            return 2
        return 0
    except (BudgetError, CampaignError, OSError, SchemaError, ValueError) as error:
        print(json.dumps({"run_id": settings.run_id, "error": str(error)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
