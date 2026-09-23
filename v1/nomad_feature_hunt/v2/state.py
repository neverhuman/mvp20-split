from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from nomad_feature_hunt.ledger import sha256_bytes, sha256_file, utc_now

from .budget import BudgetAccount
from .constants import MAX_ATTEMPTS_PER_ROLE, PROMPT_LIMIT_BYTES


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS campaign (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    state TEXT NOT NULL,
    phase TEXT NOT NULL,
    started_at TEXT,
    error TEXT
);
CREATE TABLE IF NOT EXISTS roles (
    role_id TEXT PRIMARY KEY,
    role_class TEXT NOT NULL,
    domain TEXT NOT NULL,
    wave INTEGER NOT NULL,
    spec_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);
CREATE TABLE IF NOT EXISTS jobs (
    batch_id TEXT NOT NULL,
    role_id TEXT NOT NULL REFERENCES roles(role_id),
    attempt INTEGER NOT NULL,
    prompt_path TEXT NOT NULL,
    prompt_sha256 TEXT NOT NULL,
    job_file TEXT NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY(role_id,attempt)
);
CREATE TABLE IF NOT EXISTS leases (
    role_id TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    prepared_at TEXT NOT NULL,
    submitted_at TEXT,
    completed_at TEXT,
    status TEXT NOT NULL,
    PRIMARY KEY(role_id,attempt),
    FOREIGN KEY(role_id,attempt) REFERENCES jobs(role_id,attempt)
);
CREATE TABLE IF NOT EXISTS attempts (
    role_id TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    submitted_at TEXT NOT NULL,
    completed_at TEXT,
    valid INTEGER,
    provider TEXT,
    model TEXT,
    credential_user TEXT,
    router_metadata_present INTEGER,
    router_metadata_json TEXT,
    raw_result_path TEXT,
    raw_result_sha256 TEXT,
    prompt_sha256 TEXT NOT NULL,
    output_sha256 TEXT,
    error_json TEXT,
    PRIMARY KEY(role_id,attempt)
);
CREATE TABLE IF NOT EXISTS receipts (
    receipt_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    role_id TEXT,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    valid INTEGER NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phase_receipts (
    phase TEXT PRIMARY KEY,
    receipt_id TEXT NOT NULL REFERENCES receipts(receipt_id),
    completed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS families (
    family_id TEXT PRIMARY KEY,
    family_slug TEXT NOT NULL,
    domain TEXT NOT NULL,
    source_role_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feature_specs (
    spec_id TEXT PRIMARY KEY,
    family_slug TEXT NOT NULL,
    domain TEXT NOT NULL,
    source_role_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS columns (
    feature_id TEXT PRIMARY KEY,
    family_slug TEXT NOT NULL,
    domain TEXT NOT NULL,
    status TEXT NOT NULL,
    rejection_reason TEXT,
    registry_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS matrices (
    matrix_id TEXT PRIMARY KEY,
    family_slug TEXT NOT NULL,
    train_path TEXT NOT NULL,
    test_path TEXT NOT NULL,
    column_count INTEGER NOT NULL,
    valid INTEGER NOT NULL,
    receipt_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scores (
    score_id TEXT PRIMARY KEY,
    stage TEXT NOT NULL,
    target TEXT NOT NULL,
    family_slug TEXT,
    domain TEXT,
    discovery_positive INTEGER,
    nonoverlap_group TEXT,
    payload_json TEXT NOT NULL,
    receipt_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS judgments (
    judgment_id TEXT PRIMARY KEY,
    role_id TEXT NOT NULL,
    receipt_ids_json TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
"""


class CampaignDB:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA_SQL)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def one(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(query, params).fetchone()

    def all(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(query, params).fetchall()

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        with self.connect() as connection:
            connection.execute(query, params)


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def prepare_job_batch(
    db: CampaignDB,
    *,
    batch_id: str,
    jobs_path: Path,
    prompt_dir: Path,
    roles_and_prompts: list[tuple[dict[str, Any], str]],
    attempt: int,
) -> list[dict[str, Any]]:
    """Build every prompt and the job file before recording prepared leases."""

    if attempt not in range(MAX_ATTEMPTS_PER_ROLE):
        raise ValueError("only the first attempt and one retry are permitted")
    payload: list[dict[str, Any]] = []
    prepared: list[tuple[str, Path, str]] = []
    for role, prompt in roles_and_prompts:
        if len(prompt.encode("utf-8")) > PROMPT_LIMIT_BYTES:
            raise ValueError(f"prompt for {role['id']} exceeds 12 KB")
        prompt_path = prompt_dir / f"{role['id']}.attempt-{attempt}.json"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = prompt_path.with_name(f".{prompt_path.name}.{os.getpid()}.tmp")
        temporary.write_text(prompt, encoding="utf-8")
        os.replace(temporary, prompt_path)
        prompt_hash = sha256_file(prompt_path)
        payload.append({"id": role["id"], "prompt": prompt, "priority": 1000 - int(role["wave"])})
        prepared.append((str(role["id"]), prompt_path, prompt_hash))
    _atomic_json(jobs_path, payload)
    with db.connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        for role_id, prompt_path, prompt_hash in prepared:
            prior = connection.execute(
                "SELECT COUNT(*) n FROM attempts WHERE role_id=?", (role_id,)
            ).fetchone()["n"]
            if int(prior) > attempt:
                raise ValueError(f"role {role_id} already consumed attempt {attempt}")
            connection.execute(
                "INSERT INTO jobs VALUES(?,?,?,?,?,?,?) ON CONFLICT(role_id,attempt) DO UPDATE SET "
                "batch_id=excluded.batch_id,prompt_path=excluded.prompt_path,"
                "prompt_sha256=excluded.prompt_sha256,job_file=excluded.job_file,status='prepared'",
                (
                    batch_id,
                    role_id,
                    attempt,
                    str(prompt_path),
                    prompt_hash,
                    str(jobs_path),
                    "prepared",
                ),
            )
            connection.execute(
                "INSERT INTO leases VALUES(?,?,?,NULL,NULL,'prepared') "
                "ON CONFLICT(role_id,attempt) DO UPDATE SET status='prepared'",
                (role_id, attempt, utc_now()),
            )
    return payload


def mark_batch_submitted(
    db: CampaignDB, budget: BudgetAccount, batch_id: str
) -> list[tuple[str, int]]:
    jobs = db.all(
        "SELECT role_id,attempt,prompt_sha256 FROM jobs WHERE batch_id=? AND status='prepared' "
        "ORDER BY role_id",
        (batch_id,),
    )
    budget.reserve_batch(
        [
            (f"jnoccio:{job['role_id']}:{job['attempt']}", "jnoccio")
            for job in jobs
        ]
    )
    submitted_at = utc_now()
    with db.connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        for job in jobs:
            connection.execute(
                "INSERT INTO attempts(role_id,attempt,submitted_at,prompt_sha256) VALUES(?,?,?,?)",
                (job["role_id"], job["attempt"], submitted_at, job["prompt_sha256"]),
            )
            connection.execute(
                "UPDATE leases SET submitted_at=?,status='submitted' WHERE role_id=? AND attempt=?",
                (submitted_at, job["role_id"], job["attempt"]),
            )
            connection.execute(
                "UPDATE jobs SET status='submitted' WHERE role_id=? AND attempt=?",
                (job["role_id"], job["attempt"]),
            )
            connection.execute(
                "UPDATE roles SET status='running' WHERE role_id=?", (job["role_id"],)
            )
    return [(str(job["role_id"]), int(job["attempt"])) for job in jobs]


def record_attempt_result(
    db: CampaignDB,
    budget: BudgetAccount,
    *,
    role_id: str,
    attempt: int,
    result: dict[str, Any],
    raw_result_path: Path,
    valid: bool,
    errors: list[str],
) -> None:
    raw_result_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json(raw_result_path, result)
    assistant_text = str(result.get("assistant_text", ""))
    metadata_present = "router_metadata" in result
    metadata = result.get("router_metadata")
    reported_cost = None
    if isinstance(metadata, dict):
        for key in ("cost_usd", "total_cost_usd", "estimated_cost_usd"):
            if isinstance(metadata.get(key), (int, float)):
                reported_cost = float(metadata[key])
                break
    budget.settle(f"jnoccio:{role_id}:{attempt}", reported_cost)
    with db.connect() as connection:
        connection.execute(
            "UPDATE attempts SET completed_at=?,valid=?,provider=?,model=?,credential_user=?,"
            "router_metadata_present=?,router_metadata_json=?,raw_result_path=?,"
            "raw_result_sha256=?,output_sha256=?,error_json=? WHERE role_id=? AND attempt=?",
            (
                utc_now(),
                int(valid),
                result.get("provider_id"),
                result.get("model_id"),
                result.get("credential_user_id"),
                int(metadata_present),
                json.dumps(metadata, sort_keys=True),
                str(raw_result_path),
                sha256_file(raw_result_path),
                sha256_bytes(assistant_text.encode()),
                json.dumps(errors, sort_keys=True),
                role_id,
                attempt,
            ),
        )
        state = "complete" if valid else "failed"
        connection.execute(
            "UPDATE leases SET completed_at=?,status=? WHERE role_id=? AND attempt=?",
            (utc_now(), state, role_id, attempt),
        )
        connection.execute(
            "UPDATE jobs SET status=? WHERE role_id=? AND attempt=?",
            (state, role_id, attempt),
        )
        connection.execute("UPDATE roles SET status=? WHERE role_id=?", (state, role_id))
