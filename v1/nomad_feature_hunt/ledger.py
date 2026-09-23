from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


GENESIS_HASH = "0" * 64


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


class HashChain:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        records = self.read()
        body = {
            "sequence": len(records) + 1,
            "timestamp": utc_now(),
            "event": event,
            "payload": payload,
            "previous_sha256": records[-1]["sha256"] if records else GENESIS_HASH,
        }
        body["sha256"] = sha256_bytes(canonical_json(body))
        with self.path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n")
            output.flush()
            os.fsync(output.fileno())
        return body

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def verify(self) -> tuple[bool, str | None]:
        previous = GENESIS_HASH
        for index, record in enumerate(self.read(), start=1):
            if record.get("sequence") != index:
                return False, f"event {index} has an invalid sequence"
            if record.get("previous_sha256") != previous:
                return False, f"event {index} breaks the previous-hash chain"
            supplied = record.get("sha256")
            body = {key: value for key, value in record.items() if key != "sha256"}
            if supplied != sha256_bytes(canonical_json(body)):
                return False, f"event {index} has an invalid content hash"
            previous = supplied
        return True, None


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS campaign (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    started_at TEXT,
    state TEXT NOT NULL,
    max_wall_seconds INTEGER NOT NULL,
    max_cost_usd REAL NOT NULL,
    measured_cost_usd REAL NOT NULL DEFAULT 0,
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
    job_id TEXT PRIMARY KEY,
    role_id TEXT NOT NULL REFERENCES roles(role_id),
    wave INTEGER NOT NULL,
    prompt_sha256 TEXT NOT NULL,
    prompt_path TEXT NOT NULL,
    status TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS leases (
    lease_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(job_id),
    attempt INTEGER NOT NULL,
    leased_at TEXT NOT NULL,
    released_at TEXT,
    status TEXT NOT NULL,
    UNIQUE(job_id, attempt)
);
CREATE TABLE IF NOT EXISTS attempts (
    job_id TEXT NOT NULL REFERENCES jobs(job_id),
    attempt INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    success INTEGER,
    provider_id TEXT,
    model_id TEXT,
    credential_user_id TEXT,
    router_metadata_json TEXT,
    prompt_sha256 TEXT NOT NULL,
    output_sha256 TEXT,
    error TEXT,
    PRIMARY KEY(job_id, attempt)
);
CREATE TABLE IF NOT EXISTS role_receipts (
    role_id TEXT PRIMARY KEY REFERENCES roles(role_id),
    job_id TEXT NOT NULL,
    valid INTEGER NOT NULL,
    receipt_path TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS research_claims (
    claim_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    claim TEXT NOT NULL,
    citation_json TEXT NOT NULL,
    source_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS concepts (
    concept_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    domain TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    valid INTEGER NOT NULL,
    rejection_reason TEXT
);
CREATE TABLE IF NOT EXISTS microfeatures (
    feature_id TEXT PRIMARY KEY,
    concept_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    base_equation_id TEXT NOT NULL,
    formula_fingerprint TEXT NOT NULL,
    semantic_fingerprint TEXT NOT NULL,
    numeric_signature TEXT,
    value_sha256 TEXT,
    generator_sha256 TEXT,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL,
    rejection_reason TEXT
);
CREATE INDEX IF NOT EXISTS microfeatures_formula_idx ON microfeatures(formula_fingerprint);
CREATE INDEX IF NOT EXISTS microfeatures_semantic_idx ON microfeatures(semantic_fingerprint);
CREATE TABLE IF NOT EXISTS memory_items (
    memory_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    domain TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jailgun_tabs (
    tab_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    pre_identity_sha256 TEXT,
    post_identity_sha256 TEXT,
    archive_sha256 TEXT,
    concepts INTEGER NOT NULL DEFAULT 0,
    valid INTEGER NOT NULL DEFAULT 0,
    attempt INTEGER NOT NULL DEFAULT 0,
    receipt_path TEXT
);
CREATE TABLE IF NOT EXISTS matrices (
    batch_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    train_path TEXT NOT NULL,
    test_path TEXT NOT NULL,
    train_sha256 TEXT NOT NULL,
    test_sha256 TEXT NOT NULL,
    columns INTEGER NOT NULL,
    valid INTEGER NOT NULL,
    receipt_path TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    target TEXT NOT NULL,
    stage TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    feature_count INTEGER NOT NULL,
    rmsle REAL NOT NULL,
    atlas_lift REAL NOT NULL,
    control_809_lift REAL NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS judgments (
    judgment_id TEXT PRIMARY KEY,
    judge TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    accepted INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL
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
