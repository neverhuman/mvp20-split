"""Resumable full-union CatBoost importance sweep and genetic search.

The campaign is deliberately separate from the v2/v2.1 feature-generation
state.  It consumes only frozen public-training artifacts and never accepts a
test-label path.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from concurrent.futures import Future, ThreadPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time
from typing import Any, Callable, Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from nomad_crystal360.bakeoff import verify_public_bundle


TARGETS = ("formation_energy_ev_natom", "bandgap_energy_ev")
SWEEP_SEEDS = (1_701, 2_909, 4_219, 6_553, 12_289)
DISCOVERY_FOLD_SEED = 4_219
SEALED_SEEDS = (7_919, 104_729)
DISCOVERY_FOLDS = 5
CHUNK_WIDTH = 300
SCREEN_TREES = 150
CONFIRM_TREES = 400
PERCENTILES = (50.0, 70.0, 80.0, 90.0, 95.0, 97.5, 99.0)
POPULATION_SIZE = 24
GENERATIONS = 10
FINALIST_LIMIT = 8
FROZEN_REFERENCE = 0.0495014095
EXPECTED_BASELINE = 10_800
EXPECTED_RECENT = 6_234
EXPECTED_CELLMAT = 449
EXPECTED_EMBEDDING = 128
EXPECTED_UNION = EXPECTED_BASELINE + EXPECTED_RECENT + EXPECTED_CELLMAT + EXPECTED_EMBEDDING
CATBOOST_VERSION = "1.2.10"
DEFAULT_INBOX = Path("/home/ubuntu/nomad/artifacts/nomad_theory_feature_hunt/v2/inbox")
DEFAULT_BASELINE = DEFAULT_INBOX / "v2-genetic-reduction-20260718/inputs/augmented-bundle"
DEFAULT_RECENT = DEFAULT_INBOX / "zyal10-final-20260719-r3"
DEFAULT_HYPERION_MANIFEST = Path("/home/ubuntu/nomad/hyperion_vs_nomad_449_manifest.json")
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ATLAS_SELECTED = REPO_ROOT / "artifacts/atlas_hyperion_bakeoff/run/selected_columns.json"
DEFAULT_PRIOR_RESULTS = DEFAULT_INBOX / "v2-genetic-reduction-20260718/confirmation/results.json"
PHASES = ("prepare", "importance", "cutoffs", "genetic", "confirmation", "report")
MODEL_PARAMETERS = {
    "loss_function": "RMSE",
    "depth": 7,
    "learning_rate": 0.05,
    "task_type": "GPU",
    "allow_writing_files": False,
    "verbose": False,
}


class SweepError(RuntimeError):
    """A fail-closed full-space campaign contract violation."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def atomic_npy(path: Path, value: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as handle:
        np.save(handle, value, allow_pickle=False)
    os.replace(temporary, path)


def save_frame(frame: pd.DataFrame, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for suffix in (".parquet", ".csv"):
        destination = stem.with_suffix(suffix)
        temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
        if suffix == ".parquet":
            frame.to_parquet(temporary, index=False)
        else:
            frame.to_csv(temporary, index=False)
        os.replace(temporary, destination)
        outputs.append(destination)
    return outputs


def prohibit_test_labels(paths: Iterable[Path | str]) -> None:
    forbidden = ("labeled_test", "test_label", "test_target", "target_test")
    bad = [str(path) for path in paths if any(token in str(path).lower() for token in forbidden)]
    if bad:
        raise SweepError(f"test-label inputs are forbidden: {bad}")


@dataclass(frozen=True)
class Settings:
    run_id: str
    inbox: Path = DEFAULT_INBOX

    def __post_init__(self) -> None:
        safe = self.run_id and all(character.isalnum() or character in "-_." for character in self.run_id)
        if not safe or len(self.run_id) > 64:
            raise SweepError("run_id must contain 1-64 safe filename characters")
        if not self.run_root.resolve().is_relative_to(self.inbox.resolve()):
            raise SweepError("campaign artifacts must stay under the v2 inbox")

    @property
    def run_root(self) -> Path:
        return self.inbox / f"fullspace-sweep-{self.run_id}"

    @property
    def bundle(self) -> Path:
        return self.run_root / "bundle"

    @property
    def state_path(self) -> Path:
        return self.run_root / "state.json"

    @property
    def worker(self) -> Path:
        return self.run_root / "worker.py"


def _state(settings: Settings) -> dict[str, Any]:
    if not settings.state_path.exists():
        return {
            "run_id": settings.run_id,
            "completed_phases": [],
            "created_at": utc_now(),
            "test_labels_used": False,
        }
    return json.loads(settings.state_path.read_text(encoding="utf-8"))


def _complete_phase(settings: Settings, phase: str, receipt: dict[str, Any]) -> None:
    if phase not in PHASES:
        raise SweepError(f"unknown phase: {phase}")
    receipt = {**receipt, "phase": phase, "completed_at": utc_now(), "test_labels_used": False}
    receipt_path = settings.run_root / f"receipts/{phase}.json"
    atomic_json(receipt_path, receipt)
    state = _state(settings)
    completed = list(state.get("completed_phases", []))
    if phase not in completed:
        completed.append(phase)
    state.update(
        {
            "completed_phases": completed,
            "last_phase": phase,
            "updated_at": utc_now(),
            "test_labels_used": False,
        }
    )
    atomic_json(settings.state_path, state)


def _column_signature(train: np.ndarray, test: np.ndarray) -> str:
    digest = hashlib.sha256()
    for values in (train, test):
        canonical = np.ascontiguousarray(values, dtype="<f4")
        digest.update(canonical.tobytes())
    return digest.hexdigest()


def _load_hyperion_matrix(path: Path, shape: tuple[int, int]) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        values = np.load(path, allow_pickle=False)
    elif path.suffix.lower() == ".npz":
        archive = np.load(path, allow_pickle=False)
        if len(archive.files) != 1:
            raise SweepError(f"cannot identify a single Hyperion matrix in {path}")
        values = archive[archive.files[0]]
    elif path.suffix.lower() in {".csv", ".txt", ".vs"}:
        values = np.loadtxt(path, delimiter=",", dtype=np.float32)
    elif path.suffix.lower() in {".parquet", ".pq"}:
        values = pd.read_parquet(path).to_numpy()
    else:
        raise SweepError(f"unsupported Hyperion matrix format: {path}")
    values = np.asarray(values, dtype=np.float32)
    if values.shape != shape:
        raise SweepError(f"Hyperion shape drift for {path}: {values.shape} != {shape}")
    return values


def _hyperion_sources(
    manifest_path: Path,
    *,
    train_rows: int,
    test_rows: int,
    cellmat_width: int,
    embedding_width: int,
) -> list[dict[str, Any]]:
    prohibit_test_labels([manifest_path])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = payload.get("files")
    if not isinstance(files, dict):
        raise SweepError("Hyperion manifest must contain a files mapping")
    staging = Path(str(payload.get("staging_dir", manifest_path.parent)))

    def identify(key: str, metadata: dict[str, Any]) -> str | None:
        role = str(metadata.get("role", key)).lower().replace("-", "_")
        aliases = {
            "train3.vs": "cellmat_train",
            "test3.vs": "cellmat_test",
            "hyperion3train.vs": "embedding_train",
            "hyperion3test.vs": "embedding_test",
        }
        if key.lower() in aliases:
            return aliases[key.lower()]
        if "128dim" in role or "mean" in role:
            return None
        for family in ("cellmat", "embedding"):
            if family in role:
                if "train" in role:
                    return f"{family}_train"
                if "test" in role:
                    return f"{family}_test"
        return None

    entries: dict[str, dict[str, Any]] = {}
    for key, raw in files.items():
        metadata = {"path": raw} if isinstance(raw, str) else dict(raw)
        role = identify(str(key), metadata)
        if role is None:
            continue
        path_value = metadata.get("path", metadata.get("file", key))
        candidates = [Path(str(path_value)), staging / str(path_value), manifest_path.parent / str(path_value)]
        path = next((candidate for candidate in candidates if candidate.is_file()), None)
        if path is None:
            raise SweepError(f"Hyperion manifest file is missing: {path_value}")
        expected_hash = metadata.get("sha256")
        actual_hash = sha256_file(path)
        if not expected_hash or actual_hash != expected_hash:
            raise SweepError(f"Hyperion hash drift for {path}")
        if role in entries:
            raise SweepError(f"duplicate Hyperion role: {role}")
        entries[role] = {**metadata, "path": path, "sha256": actual_hash}
    required = {"cellmat_train", "cellmat_test", "embedding_train", "embedding_test"}
    if set(entries) != required:
        raise SweepError(f"Hyperion manifest roles differ: {sorted(required - set(entries))}")
    shapes = {
        "cellmat_train": (train_rows, cellmat_width),
        "cellmat_test": (test_rows, cellmat_width),
        "embedding_train": (train_rows, embedding_width),
        "embedding_test": (test_rows, embedding_width),
    }
    matrices = {
        role: _load_hyperion_matrix(entries[role]["path"], shape)
        for role, shape in shapes.items()
    }
    sources: list[dict[str, Any]] = []
    for family, width in (("cellmat", cellmat_width), ("embedding", embedding_width)):
        train = matrices[f"{family}_train"]
        test = matrices[f"{family}_test"]
        for source_index in range(width):
            sources.append(
                {
                    "feature_id": f"hyperion_{family}_{source_index:03d}",
                    "source": f"hyperion_{family}",
                    "source_index": source_index,
                    "epoch": None,
                    "domain": "hyperion",
                    "family": family,
                    "train": train[:, source_index],
                    "test": test[:, source_index],
                    "source_hashes": {
                        "train": entries[f"{family}_train"]["sha256"],
                        "test": entries[f"{family}_test"]["sha256"],
                        "manifest": sha256_file(manifest_path),
                    },
                }
            )
    return sources


def _recent_sources(
    recent_root: Path,
    train_rows: int,
    test_rows: int,
    *,
    train_ids: np.ndarray | None = None,
    test_ids: np.ndarray | None = None,
) -> list[dict[str, Any]]:
    receipts = list((recent_root / "matrices/validated").glob("epoch-*/**/receipt.json"))
    parsed: list[tuple[tuple[int, str, str], Path, dict[str, Any]]] = []
    for receipt_path in receipts:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("test_labels_used") is not False:
            raise SweepError(f"recent receipt lacks the no-test-label attestation: {receipt_path}")
        epoch = int(receipt.get("epoch", -1))
        spec_id = str(receipt.get("spec_id", ""))
        parsed.append(((epoch, spec_id, str(receipt_path)), receipt_path, receipt))
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for _key, receipt_path, receipt in sorted(parsed, key=lambda item: item[0]):
        train_path = receipt_path.parent / "train.parquet"
        test_path = receipt_path.parent / "test.parquet"
        if not train_path.is_file() or not test_path.is_file():
            raise SweepError(f"recent accepted receipt lacks its matrices: {receipt_path}")
        if sha256_file(train_path) != receipt.get("train_sha256"):
            raise SweepError(f"recent train hash drift: {train_path}")
        if sha256_file(test_path) != receipt.get("test_sha256"):
            raise SweepError(f"recent test hash drift: {test_path}")
        train = pd.read_parquet(train_path)
        test = pd.read_parquet(test_path)
        accepted = [str(value) for value in receipt.get("accepted_columns", [])]
        if train.shape[0] != train_rows or test.shape[0] != test_rows:
            raise SweepError(f"recent row alignment drift: {receipt_path}")
        train_id_column = next((name for name in ("id", "row_id") if name in train), None)
        test_id_column = next((name for name in ("id", "row_id") if name in test), None)
        if (train_id_column is None) != (test_id_column is None):
            raise SweepError(f"recent train/test row-ID schema drift: {receipt_path}")
        if train_ids is not None or test_ids is not None:
            if train_id_column is None or train_ids is None or test_ids is None:
                raise SweepError(f"recent receipt has no row IDs for alignment: {receipt_path}")
            if not np.array_equal(
                train[train_id_column].to_numpy().astype(str), np.asarray(train_ids).astype(str)
            ) or not np.array_equal(
                test[test_id_column].to_numpy().astype(str), np.asarray(test_ids).astype(str)
            ):
                raise SweepError(f"recent row IDs do not match Atlas order: {receipt_path}")
        train_columns = [name for name in train.columns if name != train_id_column]
        test_columns = [name for name in test.columns if name != test_id_column]
        if train_columns != accepted or test_columns != accepted:
            raise SweepError(f"recent receipt/column alignment drift: {receipt_path}")
        signatures = receipt.get("numeric_signatures", {})
        if signatures and set(signatures) != set(accepted):
            raise SweepError(f"recent numeric-signature accounting drift: {receipt_path}")
        for source_index, feature_id in enumerate(accepted):
            if feature_id in seen:
                raise SweepError(f"recent feature appears in multiple receipts: {feature_id}")
            seen.add(feature_id)
            sources.append(
                {
                    "feature_id": feature_id,
                    "source": "recent-20260719-r3",
                    "source_index": len(sources),
                    "receipt_column_index": source_index,
                    "epoch": int(receipt["epoch"]),
                    "domain": str(receipt["domain"]),
                    "family": str(receipt["family_id"]),
                    "spec_id": str(receipt["spec_id"]),
                    "receipt": str(receipt_path.relative_to(recent_root)),
                    "train": train[feature_id].to_numpy(dtype=np.float32),
                    "test": test[feature_id].to_numpy(dtype=np.float32),
                    "source_hashes": {
                        "receipt": sha256_file(receipt_path),
                        "train": receipt["train_sha256"],
                        "test": receipt["test_sha256"],
                    },
                }
            )
    database = recent_root / "campaign.sqlite3"
    if database.exists():
        with sqlite3.connect(database) as connection:
            rows = connection.execute(
                "SELECT feature_id FROM columns WHERE novel=1 AND valid=1"
            ).fetchall()
        database_ids = {str(row[0]) for row in rows}
        if database_ids != seen:
            missing = sorted(database_ids - seen)[:5]
            extra = sorted(seen - database_ids)[:5]
            raise SweepError(f"recent receipt/database alignment drift: missing={missing} extra={extra}")
    return sources


def _baseline_sources(bundle: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest = verify_public_bundle(bundle)
    columns = json.loads((bundle / "columns.json").read_text(encoding="utf-8"))
    train = np.load(bundle / "train.npy", mmap_mode="r", allow_pickle=False)
    test = np.load(bundle / "test.npy", mmap_mode="r", allow_pickle=False)
    source_path = bundle / "source_families.parquet"
    source = (
        pd.read_parquet(source_path)
        if source_path.exists()
        else pd.read_csv(bundle / "source_families.csv")
    )
    index_column = "index" if "index" in source else "global_index"
    metadata = source.set_index(index_column).to_dict(orient="index")
    values: list[dict[str, Any]] = []
    for source_index, feature_id in enumerate(columns):
        row = metadata.get(source_index, {})
        family = str(row.get("feature_family", row.get("source_family", "baseline")))
        source_name = str(row.get("source_family", "baseline"))
        values.append(
            {
                "feature_id": str(feature_id),
                "source": "baseline",
                "source_partition": source_name,
                "source_index": source_index,
                "epoch": None,
                "domain": "baseline",
                "family": family,
                "train": np.asarray(train[:, source_index], dtype=np.float32),
                "test": np.asarray(test[:, source_index], dtype=np.float32),
                "source_hashes": {
                    "train": manifest["files"]["train.npy"]["sha256"],
                    "test": manifest["files"]["test.npy"]["sha256"],
                    "columns": manifest["files"]["columns.json"]["sha256"],
                },
            }
        )
    return values, manifest


def build_full_space_bundle(
    *,
    baseline_bundle: Path,
    recent_root: Path,
    hyperion_manifest: Path,
    output_dir: Path,
    expected_baseline: int = EXPECTED_BASELINE,
    expected_recent: int = EXPECTED_RECENT,
    expected_cellmat: int = EXPECTED_CELLMAT,
    expected_embedding: int = EXPECTED_EMBEDDING,
) -> dict[str, Any]:
    """Materialize and hash-bind the deterministic full executable union."""
    prohibit_test_labels([baseline_bundle, recent_root, hyperion_manifest, output_dir])
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty bundle: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline, baseline_manifest = _baseline_sources(baseline_bundle)
    train_rows = int(baseline_manifest["train_rows"])
    test_rows = int(baseline_manifest["test_rows"])
    if (train_rows, test_rows) != (2_400, 600):
        raise SweepError("full-space bundle requires the frozen 2,400/600 public split")
    train_ids = np.load(baseline_bundle / "train_ids.npy", allow_pickle=False)
    test_ids = np.load(baseline_bundle / "test_ids.npy", allow_pickle=False)
    recent = _recent_sources(
        recent_root,
        train_rows,
        test_rows,
        train_ids=train_ids,
        test_ids=test_ids,
    )
    hyperion = _hyperion_sources(
        hyperion_manifest,
        train_rows=train_rows,
        test_rows=test_rows,
        cellmat_width=expected_cellmat,
        embedding_width=expected_embedding,
    )
    if len(baseline) != expected_baseline:
        raise SweepError(f"baseline width drift: {len(baseline)} != {expected_baseline}")
    if len(recent) != expected_recent:
        raise SweepError(f"recent accepted width drift: {len(recent)} != {expected_recent}")
    if len(hyperion) != expected_cellmat + expected_embedding:
        raise SweepError("Hyperion width drift")
    ordered = [*baseline, *recent, *hyperion]
    seen_ids: set[str] = set()
    signatures: dict[str, tuple[int, str]] = {}
    registry: list[dict[str, Any]] = []
    duplicate_mappings: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    accepted_train: list[np.ndarray] = []
    accepted_test: list[np.ndarray] = []
    source_maps: dict[str, dict[str, int | None]] = defaultdict(dict)
    for item in ordered:
        feature_id = str(item["feature_id"])
        if feature_id in seen_ids:
            raise SweepError(f"feature ID collision in the full union: {feature_id}")
        seen_ids.add(feature_id)
        train = np.asarray(item.pop("train"), dtype=np.float32)
        test = np.asarray(item.pop("test"), dtype=np.float32)
        if train.shape != (train_rows,) or test.shape != (test_rows,):
            raise SweepError(f"column shape drift for {feature_id}")
        reason: str | None = None
        if not np.isfinite(train).all() or not np.isfinite(test).all():
            reason = "nonfinite"
        elif np.unique(train).size <= 1 or float(np.var(train, dtype=np.float64)) <= 0.0:
            reason = "constant"
        if reason is not None:
            quarantine.append(
                {
                    "feature_id": feature_id,
                    "source": item["source"],
                    "source_index": int(item["source_index"]),
                    "epoch": item.get("epoch"),
                    "domain": item.get("domain"),
                    "family": item.get("family"),
                    "spec_id": item.get("spec_id"),
                    "receipt": item.get("receipt"),
                    "reason": reason,
                    "source_hashes": item["source_hashes"],
                }
            )
            source_maps[str(item["source"])][str(item["source_index"])] = None
            continue
        signature = _column_signature(train, test)
        if signature in signatures:
            original_index, original_id = signatures[signature]
            duplicate_mappings.append(
                {
                    "feature_id": feature_id,
                    "source": item["source"],
                    "source_index": int(item["source_index"]),
                    "epoch": item.get("epoch"),
                    "domain": item.get("domain"),
                    "family": item.get("family"),
                    "spec_id": item.get("spec_id"),
                    "receipt": item.get("receipt"),
                    "source_hashes": item["source_hashes"],
                    "duplicate_of": original_id,
                    "duplicate_global_index": original_index,
                    "numeric_signature": signature,
                }
            )
            source_maps[str(item["source"])][str(item["source_index"])] = original_index
            continue
        global_index = len(registry)
        signatures[signature] = (global_index, feature_id)
        source_maps[str(item["source"])][str(item["source_index"])] = global_index
        registry.append(
            {
                "global_index": global_index,
                "feature_id": feature_id,
                "source": item["source"],
                "source_partition": item.get("source_partition", item["source"]),
                "source_index": int(item["source_index"]),
                "epoch": item.get("epoch"),
                "domain": item.get("domain"),
                "family": item.get("family"),
                "spec_id": item.get("spec_id"),
                "receipt": item.get("receipt"),
                "numeric_signature": signature,
                "source_hashes_json": json.dumps(item["source_hashes"], sort_keys=True),
            }
        )
        accepted_train.append(train)
        accepted_test.append(test)
    union_count = len(ordered)
    if len(registry) + len(duplicate_mappings) + len(quarantine) != union_count:
        raise AssertionError("full-union accounting is incomplete")
    train_matrix = np.column_stack(accepted_train).astype(np.float32)
    test_matrix = np.column_stack(accepted_test).astype(np.float32)
    baseline_targets = np.load(baseline_bundle / "targets.npy", allow_pickle=False)
    target_names = json.loads((baseline_bundle / "targets.json").read_text(encoding="utf-8"))
    if target_names != list(TARGETS) or baseline_targets.shape != (train_rows, len(TARGETS)):
        raise SweepError("public training target schema drift")
    if not np.isfinite(baseline_targets).all() or np.any(baseline_targets < 0.0):
        raise SweepError("public training targets must be finite and nonnegative")
    folds = np.full(train_rows, -1, dtype=np.int8)
    for fold, (_training, validation) in enumerate(
        KFold(DISCOVERY_FOLDS, shuffle=True, random_state=DISCOVERY_FOLD_SEED).split(train_ids)
    ):
        folds[validation] = fold
    outputs = {
        "train.npy": train_matrix,
        "test.npy": test_matrix,
        "targets.npy": np.asarray(baseline_targets, dtype=np.float64),
        "train_ids.npy": np.asarray(train_ids),
        "test_ids.npy": np.asarray(test_ids),
        "discovery_folds.npy": folds,
    }
    for name, values in outputs.items():
        atomic_npy(output_dir / name, values)
    columns = [str(row["feature_id"]) for row in registry]
    atomic_json(output_dir / "columns.json", columns)
    atomic_json(output_dir / "targets.json", list(TARGETS))
    atomic_json(output_dir / "duplicate_mappings.json", duplicate_mappings)
    atomic_json(output_dir / "quarantine.json", quarantine)
    atomic_json(output_dir / "source_maps.json", source_maps)
    registry_frame = pd.DataFrame(registry)
    save_frame(registry_frame, output_dir / "feature_registry")
    assumption = {
        "assumption": "Hyperion matrices use their documented positional row order",
        "accepted": True,
        "train_row_ids_sha256": sha256_file(output_dir / "train_ids.npy"),
        "test_row_ids_sha256": sha256_file(output_dir / "test_ids.npy"),
        "hyperion_manifest_sha256": sha256_file(hyperion_manifest),
        "test_labels_used": False,
    }
    atomic_json(output_dir / "hyperion_positional_provenance.json", assumption)
    file_names = [
        *outputs,
        "columns.json",
        "targets.json",
        "duplicate_mappings.json",
        "quarantine.json",
        "source_maps.json",
        "feature_registry.parquet",
        "feature_registry.csv",
        "hyperion_positional_provenance.json",
    ]
    files = {
        name: {"sha256": sha256_file(output_dir / name), "bytes": (output_dir / name).stat().st_size}
        for name in file_names
    }
    identity = {
        "files": files,
        "train_rows": train_rows,
        "test_rows": test_rows,
        "predictors": len(registry),
        "targets": list(TARGETS),
        "discovery_folds": DISCOVERY_FOLDS,
        "discovery_fold_seed": DISCOVERY_FOLD_SEED,
        "contains_test_targets": False,
    }
    manifest = {
        **identity,
        "bundle_sha256": canonical_hash(identity),
        "pre_dedup_union": union_count,
        "expected_union": expected_baseline + expected_recent + expected_cellmat + expected_embedding,
        "source_counts": {
            "baseline": len(baseline),
            "recent-20260719-r3": len(recent),
            "hyperion_cellmat": expected_cellmat,
            "hyperion_embedding": expected_embedding,
        },
        "duplicates_mapped": len(duplicate_mappings),
        "quarantined": len(quarantine),
        "input_hashes": {
            "baseline_bundle": baseline_manifest["bundle_sha256"],
            "recent_database": sha256_file(recent_root / "campaign.sqlite3")
            if (recent_root / "campaign.sqlite3").exists()
            else None,
            "hyperion_manifest": sha256_file(hyperion_manifest),
        },
        "hyperion_positional_provenance_accepted": True,
        "test_labels_used": False,
    }
    atomic_json(output_dir / "bundle_manifest.json", manifest)
    return manifest


def verify_full_space_bundle(bundle: Path, *, verify_hashes: bool = True) -> dict[str, Any]:
    manifest = json.loads((bundle / "bundle_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("contains_test_targets") is not False or manifest.get("test_labels_used") is not False:
        raise SweepError("bundle no-test-label attestation failed")
    if manifest.get("pre_dedup_union") != manifest.get("expected_union"):
        raise SweepError("bundle does not account for the complete valid union")
    if manifest.get("predictors", 0) + manifest.get("duplicates_mapped", 0) + manifest.get(
        "quarantined", 0
    ) != manifest.get("pre_dedup_union"):
        raise SweepError("bundle deduplication/quarantine accounting failed")
    if verify_hashes:
        for name, metadata in manifest["files"].items():
            if sha256_file(bundle / name) != metadata["sha256"]:
                raise SweepError(f"bundle artifact hash drift: {name}")
    identity = {
        key: manifest[key]
        for key in (
            "files",
            "train_rows",
            "test_rows",
            "predictors",
            "targets",
            "discovery_folds",
            "discovery_fold_seed",
            "contains_test_targets",
        )
    }
    if canonical_hash(identity) != manifest.get("bundle_sha256"):
        raise SweepError("bundle identity hash drift")
    return manifest


@dataclass(frozen=True)
class ImportanceChunk:
    sweep: int
    chunk: int
    columns: tuple[int, ...]
    primary_columns: tuple[int, ...]
    context_columns: tuple[int, ...]


def make_importance_chunks(
    feature_count: int, seed: int, *, width: int = CHUNK_WIDTH
) -> list[ImportanceChunk]:
    """Partition one complete permutation; context only pads the final chunk."""
    if feature_count < width:
        raise ValueError(f"need at least {width} features for fixed-width chunks")
    permutation = np.random.default_rng(seed).permutation(feature_count).astype(int).tolist()
    chunks: list[ImportanceChunk] = []
    for chunk_index, start in enumerate(range(0, feature_count, width)):
        primary = permutation[start : start + width]
        primary_set = set(primary)
        context: list[int] = []
        if len(primary) < width:
            for candidate in permutation:
                if candidate not in primary_set:
                    context.append(candidate)
                    if len(primary) + len(context) == width:
                        break
        columns = tuple(primary + context)
        if len(columns) != width or len(set(columns)) != width:
            raise AssertionError("importance chunks must have fixed unique width")
        chunks.append(
            ImportanceChunk(
                sweep=seed,
                chunk=chunk_index,
                columns=columns,
                primary_columns=tuple(primary),
                context_columns=tuple(context),
            )
        )
    counts = Counter(index for chunk in chunks for index in chunk.primary_columns)
    if counts != Counter({index: 1 for index in range(feature_count)}):
        raise AssertionError("each feature must be primary exactly once per sweep")
    return chunks


def _new_job(**values: Any) -> dict[str, Any]:
    job = dict(values)
    job["job_id"] = canonical_hash(job)[:24]
    return job


def make_importance_jobs(
    feature_count: int, targets: Iterable[str] = TARGETS
) -> list[dict[str, Any]]:
    chunks = {seed: make_importance_chunks(feature_count, seed) for seed in SWEEP_SEEDS}
    jobs: list[dict[str, Any]] = []
    for target in targets:
        for fold in range(DISCOVERY_FOLDS):
            for sweep in SWEEP_SEEDS:
                for chunk in chunks[sweep]:
                    jobs.append(
                        _new_job(
                            kind="importance",
                            stage="importance",
                            target=target,
                            fold=fold,
                            cv_seed=DISCOVERY_FOLD_SEED,
                            model_seed=sweep,
                            sweep=sweep,
                            chunk=chunk.chunk,
                            columns=list(chunk.columns),
                            primary_columns=list(chunk.primary_columns),
                            context_columns=list(chunk.context_columns),
                            chunk_width=CHUNK_WIDTH,
                            iterations=SCREEN_TREES,
                        )
                    )
    return jobs


def normalize_importance(
    values: Sequence[float], *, expected_width: int = CHUNK_WIDTH
) -> np.ndarray:
    importance = np.asarray(values, dtype=np.float64)
    if importance.shape != (expected_width,):
        raise ValueError(f"expected {expected_width} importances, found {importance.shape}")
    if not np.isfinite(importance).all() or np.any(importance < 0.0):
        raise ValueError("importance must be finite and nonnegative")
    total = float(importance.sum())
    if total <= 0.0:
        raise ValueError("importance has zero total")
    importance /= total
    if not math.isclose(float(importance.sum()), 1.0, rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError("importance normalization failed")
    return importance


def importance_tables(
    jobs_and_results: Sequence[tuple[dict[str, Any], dict[str, Any]]],
    registry: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], dict[tuple[str, int], pd.DataFrame], pd.DataFrame]:
    """Publish raw primary observations plus aggregate and fold-local rankings."""
    if sorted(registry["global_index"].astype(int).tolist()) != list(range(len(registry))):
        raise ValueError("feature registry global indices are not consecutive")
    metadata = registry.set_index("global_index").to_dict(orient="index")
    observations: list[dict[str, Any]] = []
    chunk_keys: set[tuple[str, int, int, int]] = set()
    for job, result in jobs_and_results:
        if job.get("kind") != "importance":
            continue
        importance = normalize_importance(result["importance"])
        columns = list(map(int, job["columns"]))
        primary = list(map(int, job["primary_columns"]))
        if len(columns) != CHUNK_WIDTH or len(set(columns)) != CHUNK_WIDTH:
            raise AssertionError("importance fit width differs from 300")
        if not set(primary).issubset(columns):
            raise AssertionError("primary columns are absent from their fit")
        key = (str(job["target"]), int(job["fold"]), int(job["sweep"]), int(job["chunk"]))
        if key in chunk_keys:
            raise ValueError(f"duplicate importance result: {key}")
        chunk_keys.add(key)
        positions = {index: position for position, index in enumerate(columns)}
        order = sorted(
            columns,
            key=lambda index: (
                -float(importance[positions[index]]),
                str(metadata[index]["feature_id"]),
            ),
        )
        within_rank = {index: rank for rank, index in enumerate(order, start=1)}
        for index in primary:
            row = metadata[index]
            observations.append(
                {
                    "target": str(job["target"]),
                    "feature_index": index,
                    "global_index": index,
                    "feature_id": row["feature_id"],
                    "source": row["source"],
                    "source_index": int(row["source_index"]),
                    "epoch": row.get("epoch"),
                    "domain": row.get("domain"),
                    "family": row.get("family"),
                    "fold": int(job["fold"]),
                    "sweep": int(job["sweep"]),
                    "chunk": int(job["chunk"]),
                    "relative_importance": float(importance[positions[index]]),
                    "within_chunk_rank": within_rank[index],
                }
            )
    frame = pd.DataFrame(observations)
    if frame.empty:
        raise ValueError("no importance observations supplied")
    targets = {str(job["target"]) for job, _result in jobs_and_results}
    expected_pairs = {(target, index) for target in targets for index in metadata}
    counts = frame.groupby(["target", "feature_index"]).size()
    if set(counts.index) != expected_pairs or not counts.eq(
        len(SWEEP_SEEDS) * DISCOVERY_FOLDS
    ).all():
        raise AssertionError("every feature must have exactly 25 target observations")

    group_columns = [
        "feature_index",
        "global_index",
        "feature_id",
        "source",
        "source_index",
        "epoch",
        "domain",
        "family",
    ]

    def aggregate(values: pd.DataFrame) -> pd.DataFrame:
        ranking = (
            values.groupby(group_columns, dropna=False, as_index=False)
            .agg(
                mean_relative_importance=("relative_importance", "mean"),
                importance_std=(
                    "relative_importance",
                    lambda series: float(np.std(series, ddof=0)),
                ),
                median_within_chunk_rank=("within_chunk_rank", "median"),
                observations=("relative_importance", "size"),
            )
            .sort_values(
                ["mean_relative_importance", "importance_std", "global_index"],
                ascending=[False, True, True],
                kind="mergesort",
            )
            .reset_index(drop=True)
        )
        ranking.insert(0, "rank", np.arange(1, len(ranking) + 1, dtype=int))
        total = float(ranking["mean_relative_importance"].sum())
        if total <= 0.0:
            raise AssertionError("aggregate importance is zero")
        ranking["globally_normalized_importance_share"] = (
            ranking["mean_relative_importance"] / total
        )
        if len(ranking) == 1:
            ranking["empirical_importance_percentile"] = 100.0
        else:
            ranking["empirical_importance_percentile"] = 100.0 * (
                len(ranking) - ranking["rank"]
            ) / (len(ranking) - 1)
        if not math.isclose(
            float(ranking["globally_normalized_importance_share"].sum()),
            1.0,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise AssertionError("global importance normalization failed")
        return ranking

    aggregate_rankings = {
        target: aggregate(values)
        for target, values in frame.groupby("target", sort=False)
    }
    fold_rankings = {
        (target, int(fold)): aggregate(values)
        for (target, fold), values in frame.groupby(["target", "fold"], sort=False)
    }
    for ranking in aggregate_rankings.values():
        if not ranking["observations"].eq(25).all():
            raise AssertionError("aggregate ranking observation count differs from 25")
    for ranking in fold_rankings.values():
        if not ranking["observations"].eq(5).all():
            raise AssertionError("fold-local ranking observation count differs from five")
    return aggregate_rankings, fold_rankings, frame


def percentile_label(percentile: float) -> str:
    return f"p{percentile:g}"


def percentile_feature_count(feature_count: int, percentile: float) -> int:
    if feature_count <= 0:
        raise ValueError("feature count must be positive")
    if percentile < 0.0 or percentile >= 100.0:
        raise ValueError("percentile must be in [0, 100)")
    return max(1, feature_count - math.floor(feature_count * percentile / 100.0))


def percentile_thresholds(ranking: pd.DataFrame) -> pd.DataFrame:
    if ranking.empty:
        raise ValueError("cannot threshold an empty ranking")
    if ranking["rank"].astype(int).tolist() != list(range(1, len(ranking) + 1)):
        raise ValueError("ranking must be consecutively ordered")
    values = ranking["mean_relative_importance"].to_numpy(dtype=np.float64)
    rows: list[dict[str, Any]] = []
    prior: set[int] | None = None
    for percentile in PERCENTILES:
        threshold = float(np.percentile(values, percentile, method="linear"))
        count = int(np.count_nonzero(values >= threshold))
        count = max(1, count)
        selected = set(ranking["feature_index"].astype(int).head(count))
        if prior is not None and not selected.issubset(prior):
            raise AssertionError("percentile sets are not nested")
        boundary = ranking.iloc[count - 1]
        rows.append(
            {
                "percentile": percentile,
                "percentile_label": percentile_label(percentile),
                "feature_count": count,
                "distribution_importance_threshold": threshold,
                "boundary_mean_relative_importance": float(
                    boundary["mean_relative_importance"]
                ),
                "boundary_feature_id": str(boundary["feature_id"]),
            }
        )
        prior = selected
    return pd.DataFrame(rows)


def percentile_feature_sets(ranking: pd.DataFrame) -> dict[str, list[int]]:
    thresholds = percentile_thresholds(ranking)
    indices = ranking["feature_index"].astype(int).tolist()
    return {
        str(row.percentile_label): indices[: int(row.feature_count)]
        for row in thresholds.itertuples(index=False)
    }


def interpolation_counts(
    cutoff_scores: pd.DataFrame | dict[int, float],
    *,
    feature_count: int,
) -> list[int]:
    """Fit the local log-count quadratic and return vertex offsets."""
    if isinstance(cutoff_scores, dict):
        points = sorted((int(count), float(score)) for count, score in cutoff_scores.items())
    else:
        required = {"feature_count", "mean_rmsle"}
        if not required.issubset(cutoff_scores):
            raise ValueError(f"cutoff score frame lacks {sorted(required)}")
        best_by_count: dict[int, float] = {}
        for row in cutoff_scores.itertuples(index=False):
            count, score = int(row.feature_count), float(row.mean_rmsle)
            best_by_count[count] = min(score, best_by_count.get(count, math.inf))
        points = sorted(best_by_count.items())
    if len(points) < 3:
        return []
    counts = [point[0] for point in points]
    best_index = min(range(len(points)), key=lambda index: (points[index][1], points[index][0]))
    if best_index == 0:
        neighborhood = points[:3]
    elif best_index == len(points) - 1:
        neighborhood = points[-3:]
    else:
        neighborhood = points[best_index - 1 : best_index + 2]
    x = np.log(np.asarray([point[0] for point in neighborhood], dtype=np.float64))
    y = np.asarray([point[1] for point in neighborhood], dtype=np.float64)
    quadratic, linear, _constant = np.polyfit(x, y, 2)
    if np.isfinite(quadratic) and np.isfinite(linear) and quadratic > 0.0:
        vertex_log = -linear / (2.0 * quadratic)
    else:
        vertex_log = math.log(points[best_index][0])
    vertex_log = float(np.clip(vertex_log, x.min(), x.max()))
    vertex = int(round(math.exp(vertex_log) / 10.0) * 10)
    candidates = {
        vertex + offset
        for offset in (-50, -25, 0, 25, 50)
        if 1 <= vertex + offset <= feature_count
    }
    return sorted(candidates - set(counts))


def select_lowest(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    candidates = list(rows)
    if not candidates:
        raise ValueError("no candidates to select")
    return min(
        candidates,
        key=lambda row: (
            float(row["mean_rmsle"]),
            float(row.get("rmsle_std", 0.0)),
            int(row["feature_count"]),
            str(row.get("feature_set_hash", row.get("genome_id", ""))),
        ),
    )


@dataclass(frozen=True)
class Genome:
    target: str
    columns: tuple[int, ...]
    generation: int
    origin: str
    parents: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.target not in TARGETS:
            raise ValueError(f"unsupported target: {self.target}")
        if not self.columns or tuple(sorted(set(self.columns))) != self.columns:
            raise ValueError("genome columns must be nonempty, sorted, and unique")
        if self.columns[0] < 0:
            raise ValueError("genome has a negative column")

    @property
    def genome_id(self) -> str:
        return f"g-{canonical_hash({'target': self.target, 'columns': self.columns})[:20]}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "target": self.target,
            "columns": list(self.columns),
            "feature_count": len(self.columns),
            "generation": self.generation,
            "origin": self.origin,
            "parents": list(self.parents),
            "feature_set_hash": canonical_hash(self.columns),
        }


def _genome(
    target: str,
    columns: Iterable[int],
    generation: int,
    origin: str,
    parents: Sequence[str] = (),
) -> Genome:
    return Genome(
        target=target,
        columns=tuple(sorted(set(map(int, columns)))),
        generation=generation,
        origin=origin,
        parents=tuple(parents),
    )


def _rank_weighted_sample(
    rng: np.random.Generator, ranked: np.ndarray, count: int
) -> np.ndarray:
    count = min(max(1, count), len(ranked))
    weights = 1.0 / np.sqrt(np.arange(1, len(ranked) + 1, dtype=np.float64))
    weights /= weights.sum()
    return rng.choice(ranked, size=count, replace=False, p=weights)


def initial_population(
    *,
    target: str,
    aggregate_ranking: pd.DataFrame,
    fold_rankings: Sequence[pd.DataFrame],
    named_sets: dict[str, Sequence[int]],
    population_size: int = POPULATION_SIZE,
    seed: int = 20_260_719,
) -> list[Genome]:
    """Build generation zero with all named protocol seeds and diversity fills."""
    if population_size < 8:
        raise ValueError("population size must be at least eight")
    width = len(aggregate_ranking)
    ranked = aggregate_ranking["feature_index"].astype(int).to_numpy()
    if sorted(ranked.tolist()) != list(range(width)):
        raise ValueError("aggregate ranking is not a full feature permutation")
    if len(fold_rankings) != DISCOVERY_FOLDS:
        raise ValueError("exactly five fold-local rankings are required")
    seeds: list[Genome] = []
    for name, columns in named_sets.items():
        if not columns:
            continue
        genome = _genome(target, columns, 0, name)
        if genome.columns[-1] >= width:
            raise ValueError(f"named set {name} contains an out-of-range column")
        if genome.genome_id not in {item.genome_id for item in seeds}:
            seeds.append(genome)
    if len(seeds) > population_size:
        raise ValueError("named protocol seeds exceed the generation-zero population")
    base_count = int(np.median([len(item.columns) for item in seeds])) if seeds else width // 2
    fold_sets = [
        set(ranking["feature_index"].astype(int).head(max(1, base_count)))
        for ranking in fold_rankings
    ]
    consensus = set.intersection(*fold_sets)
    union = set.union(*fold_sets)
    for name, columns in (
        ("fold-consensus-intersection", consensus),
        ("fold-consensus-union", union),
    ):
        if columns:
            candidate = _genome(target, columns, 0, name)
            if candidate.genome_id not in {item.genome_id for item in seeds}:
                seeds.append(candidate)
    if len(seeds) > population_size:
        raise ValueError("protocol and consensus seeds exceed the population")
    rng = np.random.default_rng(seed)
    attempts = 0
    while len(seeds) < population_size:
        attempts += 1
        if attempts > population_size * 500:
            raise RuntimeError("could not create a unique generation-zero population")
        factor = float(rng.uniform(0.55, 1.45))
        count = min(width, max(1, round(base_count * factor)))
        columns = _rank_weighted_sample(rng, ranked, count)
        candidate = _genome(target, columns, 0, f"rank-weighted-diversity-{attempts:03d}")
        if candidate.genome_id not in {item.genome_id for item in seeds}:
            seeds.append(candidate)
    return seeds


def breed_population(
    *,
    target: str,
    parent_archive: Sequence[tuple[Genome, float]],
    aggregate_ranking: pd.DataFrame,
    generation: int,
    seed: int,
    population_size: int = POPULATION_SIZE,
) -> list[Genome]:
    """Top-four elitism plus tournament set crossover and rank-biased mutation."""
    if generation <= 0:
        raise ValueError("bred generations must be positive")
    if len(parent_archive) < 4:
        raise ValueError("at least four archived scores are required")
    best_by_id: dict[str, tuple[Genome, float]] = {}
    for genome, score in parent_archive:
        current = best_by_id.get(genome.genome_id)
        if current is None or float(score) < current[1]:
            best_by_id[genome.genome_id] = (genome, float(score))
    ordered = sorted(
        best_by_id.values(),
        key=lambda item: (item[1], len(item[0].columns), item[0].genome_id),
    )
    width = len(aggregate_ranking)
    ranking = aggregate_ranking["feature_index"].astype(int).to_numpy()
    weights = np.zeros(width, dtype=np.float64)
    weights[ranking] = 1.0 / np.sqrt(np.arange(1, width + 1, dtype=np.float64))
    rng = np.random.default_rng(seed + generation * 10_007)
    children = [
        replace(genome, generation=generation, origin="elite", parents=(genome.genome_id,))
        for genome, _score in ordered[:4]
    ]
    used = {item.genome_id for item in children}
    seen_archive = set(best_by_id)
    attempts = 0
    minimum = min(64, width)
    while len(children) < population_size:
        attempts += 1
        if attempts > population_size * 2_000:
            raise RuntimeError("genetic search exhausted unique mutations")

        def tournament() -> Genome:
            choices = rng.choice(len(ordered), size=min(4, len(ordered)), replace=False)
            winner = min(
                (ordered[int(index)] for index in choices),
                key=lambda item: (item[1], len(item[0].columns), item[0].genome_id),
            )
            return winner[0]

        first = tournament()
        second = tournament()
        first_set = set(first.columns)
        second_set = set(second.columns)
        inherited = first_set & second_set
        optional = np.asarray(sorted(first_set ^ second_set), dtype=np.int64)
        target_size = min(
            width,
            max(minimum, round((len(first_set) + len(second_set)) / 2 * rng.uniform(0.9, 1.1))),
        )
        take = min(len(optional), max(0, target_size - len(inherited)))
        if take:
            probabilities = weights[optional]
            probabilities /= probabilities.sum()
            inherited.update(rng.choice(optional, size=take, replace=False, p=probabilities))
        mutation_rate = float(rng.uniform(0.025, 0.12))
        remove_count = min(
            max(0, len(inherited) - minimum), max(1, round(len(inherited) * mutation_rate))
        )
        if remove_count:
            present = np.asarray(sorted(inherited), dtype=np.int64)
            probabilities = 1.0 / np.maximum(weights[present], 1e-12)
            probabilities /= probabilities.sum()
            inherited.difference_update(
                rng.choice(present, size=remove_count, replace=False, p=probabilities).tolist()
            )
        absent = np.asarray(sorted(set(range(width)) - inherited), dtype=np.int64)
        drift = int(rng.integers(-max(1, remove_count // 2), max(2, remove_count // 2 + 1)))
        add_count = min(len(absent), max(1, remove_count + drift))
        if add_count:
            probabilities = weights[absent]
            probabilities /= probabilities.sum()
            inherited.update(
                rng.choice(absent, size=add_count, replace=False, p=probabilities).tolist()
            )
        child = _genome(
            target,
            inherited,
            generation,
            "tournament-crossover-mutation",
            (first.genome_id, second.genome_id),
        )
        if child.genome_id not in used and child.genome_id not in seen_archive:
            children.append(child)
            used.add(child.genome_id)
    return children


def deterministic_ga_history(
    *,
    target: str,
    aggregate_ranking: pd.DataFrame,
    fold_rankings: Sequence[pd.DataFrame],
    named_sets: dict[str, Sequence[int]],
    score: Callable[[Genome], float],
    seed: int = 20_260_719,
    population_size: int = POPULATION_SIZE,
    generations: int = GENERATIONS,
) -> list[dict[str, Any]]:
    """Pure deterministic evolution helper used by tests and dry simulations."""
    population = initial_population(
        target=target,
        aggregate_ranking=aggregate_ranking,
        fold_rankings=fold_rankings,
        named_sets=named_sets,
        population_size=population_size,
        seed=seed,
    )
    archive: list[tuple[Genome, float]] = []
    history: list[dict[str, Any]] = []
    for generation in range(generations):
        scored = [(genome, float(score(genome))) for genome in population]
        archive.extend(scored)
        history.extend({**genome.as_dict(), "mean_rmsle": value} for genome, value in scored)
        if generation + 1 < generations:
            population = breed_population(
                target=target,
                parent_archive=archive,
                aggregate_ranking=aggregate_ranking,
                generation=generation + 1,
                seed=seed,
                population_size=population_size,
            )
    counts = Counter(int(row["generation"]) for row in history)
    if counts != Counter({generation: population_size for generation in range(generations)}):
        raise AssertionError("genetic history is not a terminal population-by-generation grid")
    return history


def _jaccard_distance(left: Genome, right: Genome) -> float:
    left_set, right_set = set(left.columns), set(right.columns)
    return 1.0 - len(left_set & right_set) / len(left_set | right_set)


def choose_finalists(
    rows: Sequence[dict[str, Any]],
    genomes: dict[str, Genome],
    *,
    limit: int = FINALIST_LIMIT,
) -> list[Genome]:
    """Select score, compactness, and set-diversity confirmation finalists."""
    if not rows or limit < 1:
        return []
    ordered = sorted(
        rows,
        key=lambda row: (
            float(row["mean_rmsle"]),
            float(row.get("rmsle_std", 0.0)),
            int(row["feature_count"]),
            str(row["genome_id"]),
        ),
    )
    selected_ids: list[str] = []
    for row in ordered[: min(4, limit)]:
        if str(row["genome_id"]) not in selected_ids:
            selected_ids.append(str(row["genome_id"]))
    competitive = ordered[: max(limit * 4, 16)]
    for row in sorted(
        competitive,
        key=lambda item: (
            int(item["feature_count"]),
            float(item["mean_rmsle"]),
            str(item["genome_id"]),
        ),
    ):
        if len(selected_ids) >= min(limit, 6):
            break
        genome_id = str(row["genome_id"])
        if genome_id not in selected_ids:
            selected_ids.append(genome_id)
    while len(selected_ids) < min(limit, len({str(row['genome_id']) for row in ordered})):
        candidates = [
            genomes[str(row["genome_id"])]
            for row in competitive
            if str(row["genome_id"]) not in selected_ids
        ]
        if not candidates:
            break
        candidate = max(
            candidates,
            key=lambda genome: (
                min(_jaccard_distance(genome, genomes[item]) for item in selected_ids),
                -next(
                    float(row["mean_rmsle"])
                    for row in ordered
                    if str(row["genome_id"]) == genome.genome_id
                ),
                genome.genome_id,
            ),
        )
        selected_ids.append(candidate.genome_id)
    return [genomes[genome_id] for genome_id in selected_ids[:limit]]


class ResultCache:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict[str, Any] | None:
        path = self.root / f"{key}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def put(self, key: str, result: dict[str, Any]) -> Path:
        path = self.root / f"{key}.json"
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != result:
                raise SweepError(f"cache collision for {key}")
            return path
        atomic_json(path, result)
        return path


def cache_identity(*, bundle_hash: str, worker_hash: str, job: dict[str, Any]) -> str:
    """Bind a fit to its data, exact columns/fold/seeds, parameters, and worker."""
    fit = {
        "bundle_sha256": bundle_hash,
        "worker_sha256": worker_hash,
        "kind": job["kind"],
        "target": job["target"],
        "columns": job["columns"],
        "fold": job["fold"],
        "cv_seed": job["cv_seed"],
        "model_seed": job["model_seed"],
        "iterations": job["iterations"],
        "model_parameters": MODEL_PARAMETERS,
    }
    return canonical_hash(fit)


@dataclass(frozen=True)
class Host:
    name: str
    python: str
    bundle: Path
    worker: Path
    device: str = "0"
    remote: bool = False


def _host_command(host: Host, arguments: Sequence[str]) -> list[str]:
    command = [host.python, str(host.worker), "--device", host.device, *arguments]
    if not host.remote:
        return command
    return ["ssh", "-o", "BatchMode=yes", host.name, *command]


def _json_command(
    host: Host, arguments: Sequence[str], *, timeout: float | None = None
) -> dict[str, Any]:
    result = subprocess.run(
        _host_command(host, arguments),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise SweepError(
            f"worker failed on {host.name}: {result.stderr.strip() or result.stdout.strip()}"
        )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise SweepError(f"worker on {host.name} returned no JSON")
    return json.loads(lines[-1])


def _append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps({**event, "timestamp": utc_now()}, sort_keys=True, allow_nan=False)
            + "\n"
        )
        handle.flush()
        os.fsync(handle.fileno())


def _remote_gpu_idle(remote_host: str) -> bool:
    command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        remote_host,
        "nvidia-smi",
        "--query-gpu=name,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
        "--id=0",
    ]
    try:
        output = subprocess.check_output(command, text=True, timeout=15).strip().splitlines()[0]
        name, used, utilization = (item.strip() for item in output.split(","))
        supported = "3090" in name or "4090" in name
        return supported and float(used) < 1_024 and float(utilization) < 10
    except (OSError, subprocess.SubprocessError, IndexError, ValueError):
        return False


def stage_remote_bundle(
    *, settings: Settings, remote_host: str, remote_bundle: Path
) -> Host:
    verify_full_space_bundle(settings.bundle)
    subprocess.run(
        ["ssh", "-o", "BatchMode=yes", remote_host, "mkdir", "-p", str(remote_bundle)],
        check=True,
    )
    subprocess.run(
        ["rsync", "-a", "--checksum", f"{settings.bundle}/", f"{remote_host}:{remote_bundle}/"],
        check=True,
    )
    remote_worker = remote_bundle / "worker.py"
    subprocess.run(
        ["rsync", "-a", "--checksum", str(settings.worker), f"{remote_host}:{remote_worker}"],
        check=True,
    )
    host = Host(remote_host, "python3", remote_bundle, remote_worker, remote=True)
    identity = _json_command(host, ["--identity"], timeout=60)
    if identity.get("packages", {}).get("catboost") != CATBOOST_VERSION:
        raise SweepError(f"{remote_host} does not have CatBoost {CATBOOST_VERSION}")
    _json_command(host, ["--bundle", str(remote_bundle), "--verify-only"], timeout=300)
    _json_command(host, ["--smoke"], timeout=120)
    return host


class CampaignScheduler:
    """One subprocess per GPU, with non-preemptive late attachment of a remote GPU."""

    def __init__(
        self,
        settings: Settings,
        *,
        local_python: str = "/usr/bin/python3",
        remote_host: str | None = "xbabe1",
        remote_bundle: Path = Path("/home/ubuntu/fullspace-sweep/bundle"),
    ):
        self.settings = settings
        manifest = verify_full_space_bundle(settings.bundle)
        self.bundle_hash = str(manifest["bundle_sha256"])
        self.worker_hash = sha256_file(settings.worker)
        self.cache = ResultCache(settings.run_root / "cache/model-results")
        self.events = settings.run_root / "events.jsonl"
        self.remote_host = remote_host
        self.remote_bundle = remote_bundle
        self.hosts: dict[str, Host] = {
            "local": Host("local", local_python, settings.bundle, settings.worker)
        }
        local_identity = _json_command(self.hosts["local"], ["--identity"], timeout=60)
        if local_identity.get("packages", {}).get("catboost") != CATBOOST_VERSION:
            raise SweepError(f"local worker does not have CatBoost {CATBOOST_VERSION}")
        self.environments = {"local": local_identity}
        self._remote_checked_at = 0.0

    def _try_attach_remote(self) -> None:
        if self.remote_host is None or "remote" in self.hosts:
            return
        now = time.monotonic()
        if now - self._remote_checked_at < 15.0:
            return
        self._remote_checked_at = now
        if not _remote_gpu_idle(self.remote_host):
            return
        host = stage_remote_bundle(
            settings=self.settings,
            remote_host=self.remote_host,
            remote_bundle=self.remote_bundle,
        )
        self.hosts["remote"] = host
        self.environments["remote"] = _json_command(host, ["--identity"], timeout=60)
        _append_event(
            self.events,
            {"event": "gpu_attached", "host": self.remote_host, "gpu": "RTX 3090/4090"},
        )

    def _run_one(self, host_name: str, job: dict[str, Any]) -> dict[str, Any]:
        host = self.hosts[host_name]
        encoded = base64.b64encode(
            json.dumps(job, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")
        result = _json_command(
            host,
            ["--bundle", str(host.bundle), "--job-base64", encoded],
            timeout=None,
        )
        if result.get("bundle_sha256") != self.bundle_hash:
            raise SweepError(f"worker on {host.name} used the wrong bundle")
        return result

    def run(
        self, stage: str, jobs: Sequence[dict[str, Any]]
    ) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        results: dict[str, dict[str, Any]] = {}
        pending: list[dict[str, Any]] = []
        for job in jobs:
            key = cache_identity(
                bundle_hash=self.bundle_hash, worker_hash=self.worker_hash, job=job
            )
            cached = self.cache.get(key)
            if cached is None:
                pending.append(job)
            else:
                results[job["job_id"]] = cached
        _append_event(
            self.events,
            {
                "event": "stage_started",
                "stage": stage,
                "jobs": len(jobs),
                "cached": len(jobs) - len(pending),
            },
        )
        executors: dict[str, ThreadPoolExecutor] = {
            name: ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"gpu-{name}")
            for name in self.hosts
        }
        active: dict[Future[dict[str, Any]], tuple[str, dict[str, Any]]] = {}
        idle = set(executors)
        try:
            while pending or active:
                self._try_attach_remote()
                for name in self.hosts:
                    if name not in executors:
                        executors[name] = ThreadPoolExecutor(
                            max_workers=1, thread_name_prefix=f"gpu-{name}"
                        )
                        idle.add(name)
                while pending and idle:
                    host_name = sorted(idle)[0]
                    idle.remove(host_name)
                    job = pending.pop(0)
                    future = executors[host_name].submit(self._run_one, host_name, job)
                    active[future] = (host_name, job)
                if not active:
                    continue
                completed, _remaining = wait(
                    active, timeout=15.0, return_when=FIRST_COMPLETED
                )
                for future in completed:
                    host_name, job = active.pop(future)
                    result = future.result()
                    key = cache_identity(
                        bundle_hash=self.bundle_hash,
                        worker_hash=self.worker_hash,
                        job=job,
                    )
                    self.cache.put(key, result)
                    results[job["job_id"]] = result
                    idle.add(host_name)
                    _append_event(
                        self.events,
                        {
                            "event": "job_completed",
                            "stage": stage,
                            "host": host_name,
                            "job_id": job["job_id"],
                            "score": result.get("score"),
                        },
                    )
        finally:
            for executor in executors.values():
                executor.shutdown(wait=True)
        if set(results) != {str(job["job_id"]) for job in jobs}:
            raise AssertionError(f"stage {stage} did not complete every scheduled job")
        _append_event(
            self.events,
            {"event": "stage_completed", "stage": stage, "jobs": len(jobs)},
        )
        return [(job, results[str(job["job_id"])]) for job in jobs]


def prepare(
    settings: Settings,
    *,
    baseline_bundle: Path = DEFAULT_BASELINE,
    recent_root: Path = DEFAULT_RECENT,
    hyperion_manifest: Path = DEFAULT_HYPERION_MANIFEST,
    worker_source: Path | None = None,
    gpu_smoke: bool = True,
    expected_baseline: int = EXPECTED_BASELINE,
    expected_recent: int = EXPECTED_RECENT,
    expected_cellmat: int = EXPECTED_CELLMAT,
    expected_embedding: int = EXPECTED_EMBEDDING,
) -> dict[str, Any]:
    """Prepare a fresh campaign or verify an already prepared campaign."""
    state = _state(settings)
    if "prepare" in state.get("completed_phases", []):
        manifest = verify_full_space_bundle(settings.bundle)
        if sha256_file(settings.worker) != json.loads(
            (settings.run_root / "protocol.json").read_text(encoding="utf-8")
        )["worker_sha256"]:
            raise SweepError("prepared worker hash drift")
        return manifest
    settings.run_root.mkdir(parents=True, exist_ok=True)
    for directory in (
        "receipts",
        "cache/model-results",
        "importance",
        "cutoffs",
        "genetic",
        "confirmation",
        "reports",
        "final_hashes",
    ):
        (settings.run_root / directory).mkdir(parents=True, exist_ok=True)
    source = worker_source or Path(__file__).with_name("full_space_sweep_worker.py")
    if not source.is_file():
        raise SweepError(f"worker source is missing: {source}")
    temporary_worker = settings.worker.with_name(f".{settings.worker.name}.{os.getpid()}.tmp")
    shutil.copy2(source, temporary_worker)
    os.replace(temporary_worker, settings.worker)
    if settings.bundle.exists() and any(settings.bundle.iterdir()):
        raise SweepError("an incomplete nonempty bundle exists; choose a fresh run_id")
    temporary_bundle = settings.run_root / f".bundle-{os.getpid()}.tmp"
    manifest = build_full_space_bundle(
        baseline_bundle=baseline_bundle.resolve(),
        recent_root=recent_root.resolve(),
        hyperion_manifest=hyperion_manifest.resolve(),
        output_dir=temporary_bundle,
        expected_baseline=expected_baseline,
        expected_recent=expected_recent,
        expected_cellmat=expected_cellmat,
        expected_embedding=expected_embedding,
    )
    os.replace(temporary_bundle, settings.bundle)
    identity: dict[str, Any] | None = None
    smoke: dict[str, Any] | None = None
    if gpu_smoke:
        local = Host("local", "/usr/bin/python3", settings.bundle, settings.worker)
        identity = _json_command(local, ["--identity"], timeout=60)
        if identity.get("packages", {}).get("catboost") != CATBOOST_VERSION:
            raise SweepError(f"CatBoost {CATBOOST_VERSION} is required before GPU reservation")
        smoke = _json_command(local, ["--smoke"], timeout=120)
    protocol = {
        "protocol": "nomad-full-space-sweep-v1",
        "run_id": settings.run_id,
        "bundle_sha256": manifest["bundle_sha256"],
        "controller_sha256": sha256_file(Path(__file__)),
        "worker_sha256": sha256_file(settings.worker),
        "sweep_seeds": list(SWEEP_SEEDS),
        "discovery_folds": DISCOVERY_FOLDS,
        "discovery_fold_seed": DISCOVERY_FOLD_SEED,
        "chunk_width": CHUNK_WIDTH,
        "screen_trees": SCREEN_TREES,
        "percentiles": list(PERCENTILES),
        "population_size": POPULATION_SIZE,
        "generations": GENERATIONS,
        "sealed_seeds": list(SEALED_SEEDS),
        "confirmation_trees": CONFIRM_TREES,
        "frozen_reference_mean_rmsle": FROZEN_REFERENCE,
        "gpu_identity": identity,
        "gpu_smoke": smoke,
        "hyperion_positional_provenance_accepted": True,
        "test_labels_used": False,
    }
    atomic_json(settings.run_root / "protocol.json", protocol)
    _complete_phase(
        settings,
        "prepare",
        {
            "bundle_sha256": manifest["bundle_sha256"],
            "pre_dedup_union": manifest["pre_dedup_union"],
            "predictors": manifest["predictors"],
            "duplicates_mapped": manifest["duplicates_mapped"],
            "quarantined": manifest["quarantined"],
            "gpu_smoke_passed": smoke is not None if gpu_smoke else None,
        },
    )
    return manifest


def _record_schedule(
    settings: Settings,
    stage: str,
    jobs: Sequence[dict[str, Any]],
) -> None:
    bundle_hash = verify_full_space_bundle(settings.bundle, verify_hashes=False)["bundle_sha256"]
    worker_hash = sha256_file(settings.worker)
    payload = {
        "stage": stage,
        "job_count": len(jobs),
        "job_ids": [job["job_id"] for job in jobs],
        "cache_keys": [
            cache_identity(bundle_hash=bundle_hash, worker_hash=worker_hash, job=job)
            for job in jobs
        ],
        "schedule_sha256": canonical_hash(jobs),
        "test_labels_used": False,
    }
    atomic_json(settings.run_root / f"receipts/schedules/{stage}.json", payload)


def _load_ranking(settings: Settings, target: str, fold: int | None = None) -> pd.DataFrame:
    suffix = "" if fold is None else f"_fold_{fold}"
    return pd.read_parquet(settings.run_root / f"importance/ranking_{target}{suffix}.parquet")


def _run_importance(
    settings: Settings, scheduler: CampaignScheduler
) -> dict[str, Any]:
    manifest = verify_full_space_bundle(settings.bundle)
    registry = pd.read_parquet(settings.bundle / "feature_registry.parquet")
    jobs = make_importance_jobs(int(manifest["predictors"]))
    _record_schedule(settings, "importance", jobs)
    results = scheduler.run("importance", jobs)
    aggregate, fold_local, observations = importance_tables(results, registry)
    save_frame(observations, settings.run_root / "importance/observations")
    for target in TARGETS:
        save_frame(aggregate[target], settings.run_root / f"importance/ranking_{target}")
        hyperion = aggregate[target][
            aggregate[target]["source"].astype(str).str.startswith("hyperion_")
        ].copy()
        save_frame(hyperion, settings.run_root / f"importance/hyperion_{target}")
        family_summary = (
            aggregate[target]
            .groupby(["source", "domain", "family"], dropna=False, as_index=False)
            .agg(
                features=("feature_index", "size"),
                normalized_importance=("globally_normalized_importance_share", "sum"),
                best_rank=("rank", "min"),
                median_rank=("rank", "median"),
            )
            .sort_values(["normalized_importance", "source"], ascending=[False, True])
        )
        save_frame(family_summary, settings.run_root / f"importance/families_{target}")
        save_frame(
            percentile_thresholds(aggregate[target]),
            settings.run_root / f"importance/thresholds_{target}",
        )
        for fold in range(DISCOVERY_FOLDS):
            save_frame(
                fold_local[(target, fold)],
                settings.run_root / f"importance/ranking_{target}_fold_{fold}",
            )
    receipt = {
        "scheduled_fits": len(jobs),
        "features": int(manifest["predictors"]),
        "observations_per_target_feature": 25,
        "raw_observations": len(observations),
        "targets": list(TARGETS),
    }
    _complete_phase(settings, "importance", receipt)
    return receipt


def _score_rows(
    jobs_and_results: Sequence[tuple[dict[str, Any], dict[str, Any]]]
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "target": job["target"],
                "view": job["view"],
                "origin": job.get("origin", job["view"]),
                "fold": int(job["fold"]),
                "cv_seed": int(job["cv_seed"]),
                "model_seed": int(job["model_seed"]),
                "feature_count": int(job.get("feature_count", len(job["columns"]))),
                "fold_feature_count": len(job["columns"]),
                "feature_set_hash": str(job["feature_set_hash"]),
                "rmsle": float(result["score"]),
                "elapsed_seconds": float(result.get("elapsed_seconds", 0.0)),
                "job_id": job["job_id"],
            }
            for job, result in jobs_and_results
        ]
    )


def _score_curve(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(
            ["target", "view", "origin", "feature_count", "feature_set_hash"],
            as_index=False,
        )
        .agg(
            mean_rmsle=("rmsle", "mean"),
            rmsle_std=("rmsle", lambda values: float(np.std(values, ddof=0))),
            model_jobs=("rmsle", "size"),
            min_fold_features=("fold_feature_count", "min"),
            max_fold_features=("fold_feature_count", "max"),
        )
    )


def _cutoff_jobs(
    aggregate: dict[str, pd.DataFrame],
    fold_local: dict[tuple[str, int], pd.DataFrame],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, list[int]]]]:
    jobs: list[dict[str, Any]] = []
    feature_sets: dict[str, dict[str, list[int]]] = {}
    for target in TARGETS:
        feature_sets[target] = percentile_feature_sets(aggregate[target])
        for view, aggregate_columns in feature_sets[target].items():
            for fold in range(DISCOVERY_FOLDS):
                fold_columns = percentile_feature_sets(fold_local[(target, fold)])[view]
                jobs.append(
                    _new_job(
                        kind="screen",
                        stage="cutoff",
                        target=target,
                        view=view,
                        origin="percentile",
                        fold=fold,
                        cv_seed=DISCOVERY_FOLD_SEED,
                        model_seed=DISCOVERY_FOLD_SEED,
                        columns=fold_columns,
                        feature_count=len(aggregate_columns),
                        feature_set_hash=canonical_hash(aggregate_columns),
                        iterations=SCREEN_TREES,
                    )
                )
    return jobs, feature_sets


def _run_cutoffs(settings: Settings, scheduler: CampaignScheduler) -> dict[str, Any]:
    aggregate = {target: _load_ranking(settings, target) for target in TARGETS}
    fold_local = {
        (target, fold): _load_ranking(settings, target, fold)
        for target in TARGETS
        for fold in range(DISCOVERY_FOLDS)
    }
    initial_jobs, feature_sets = _cutoff_jobs(aggregate, fold_local)
    _record_schedule(settings, "cutoffs-initial", initial_jobs)
    initial_results = scheduler.run("cutoffs-initial", initial_jobs)
    initial_frame = _score_rows(initial_results)
    initial_curve = _score_curve(initial_frame)
    interpolation_jobs: list[dict[str, Any]] = []
    for target in TARGETS:
        counts = interpolation_counts(
            initial_curve[initial_curve["target"] == target],
            feature_count=len(aggregate[target]),
        )
        ranked = aggregate[target]["feature_index"].astype(int).tolist()
        for count in counts:
            view = f"i{count}"
            aggregate_columns = ranked[:count]
            feature_sets[target][view] = aggregate_columns
            for fold in range(DISCOVERY_FOLDS):
                fold_columns = fold_local[(target, fold)]["feature_index"].astype(int).head(count).tolist()
                interpolation_jobs.append(
                    _new_job(
                        kind="screen",
                        stage="interpolation",
                        target=target,
                        view=view,
                        origin="quadratic-interpolation",
                        fold=fold,
                        cv_seed=DISCOVERY_FOLD_SEED,
                        model_seed=DISCOVERY_FOLD_SEED,
                        columns=fold_columns,
                        feature_count=count,
                        feature_set_hash=canonical_hash(aggregate_columns),
                        iterations=SCREEN_TREES,
                    )
                )
    _record_schedule(settings, "cutoffs-interpolation", interpolation_jobs)
    interpolation_results = (
        scheduler.run("cutoffs-interpolation", interpolation_jobs)
        if interpolation_jobs
        else []
    )
    all_frame = pd.concat(
        [initial_frame, _score_rows(interpolation_results)], ignore_index=True
    )
    curve = _score_curve(all_frame)
    save_frame(all_frame, settings.run_root / "cutoffs/fold_scores")
    save_frame(curve, settings.run_root / "cutoffs/score_curve")
    selections: dict[str, Any] = {}
    for target in TARGETS:
        rows = curve[curve["target"] == target].to_dict(orient="records")
        selections[target] = select_lowest(rows)
    atomic_json(settings.run_root / "cutoffs/feature_sets.json", feature_sets)
    atomic_json(settings.run_root / "cutoffs/selections.json", selections)
    receipt = {
        "initial_cutoff_fits": len(initial_jobs),
        "interpolation_fits": len(interpolation_jobs),
        "cutoff_views_per_target": {target: 7 for target in TARGETS},
        "selected": selections,
    }
    _complete_phase(settings, "cutoffs", receipt)
    return receipt


def _columns_from_names(
    names: Sequence[str],
    name_to_index: dict[str, int],
    label: str,
    *,
    allow_unavailable: bool = False,
) -> list[int]:
    missing = [str(name) for name in names if str(name) not in name_to_index]
    if missing and not allow_unavailable:
        raise SweepError(f"{label} has columns outside the full bundle: {missing[:5]}")
    available = sorted(
        {name_to_index[str(name)] for name in names if str(name) in name_to_index}
    )
    if not available:
        raise SweepError(f"{label} has no available columns after quarantine")
    return available


def load_control_sets(
    settings: Settings,
    *,
    atlas_selected: Path = DEFAULT_ATLAS_SELECTED,
    prior_results: Path = DEFAULT_PRIOR_RESULTS,
) -> dict[str, dict[str, list[int]]]:
    """Resolve full, recent, existing-809, Atlas, and prior-v2 controls."""
    registry = pd.read_parquet(settings.bundle / "feature_registry.parquet")
    name_to_index = dict(
        zip(
            registry["feature_id"].astype(str),
            registry["global_index"].astype(int),
            strict=True,
        )
    )
    duplicate_mappings = json.loads(
        (settings.bundle / "duplicate_mappings.json").read_text(encoding="utf-8")
    )
    name_to_index.update(
        {
            str(row["feature_id"]): int(row["duplicate_global_index"])
            for row in duplicate_mappings
        }
    )
    source_maps = json.loads((settings.bundle / "source_maps.json").read_text(encoding="utf-8"))
    baseline_map = source_maps.get("baseline", {})
    existing = sorted(
        {
            int(baseline_map[str(index)])
            for index in range(809)
            if baseline_map.get(str(index)) is not None
        }
    )
    recent = registry.loc[
        registry["source"] == "recent-20260719-r3", "global_index"
    ].astype(int).tolist()
    full = registry["global_index"].astype(int).tolist()
    atlas_path = atlas_selected.resolve()
    if not atlas_path.is_file():
        raise SweepError(f"Atlas selected-column control is unavailable: {atlas_path}")
    atlas_payload = json.loads(atlas_path.read_text(encoding="utf-8"))
    prior_path = prior_results.resolve()
    if not prior_path.is_file():
        raise SweepError(f"prior-v2 winner control is unavailable: {prior_path}")
    prior_payload = json.loads(prior_path.read_text(encoding="utf-8"))
    controls: dict[str, dict[str, list[int]]] = {}
    availability: dict[str, Any] = {}
    for target in TARGETS:
        atlas_names = atlas_payload.get(target)
        if not isinstance(atlas_names, list):
            raise SweepError(f"Atlas control lacks {target}")
        prior = prior_payload.get("winners", {}).get(target, {})
        prior_names = prior.get("selected_columns")
        if isinstance(prior_names, list) and prior_names and isinstance(prior_names[0], str):
            prior_columns = _columns_from_names(
                prior_names,
                name_to_index,
                "prior-v2 control",
                allow_unavailable=True,
            )
            unavailable_prior = [
                str(name) for name in prior_names if str(name) not in name_to_index
            ]
        elif isinstance(prior.get("columns"), list):
            prior_columns = sorted(
                {
                    int(baseline_map[str(index)])
                    for index in prior["columns"]
                    if baseline_map.get(str(index)) is not None
                }
            )
            unavailable_prior = [
                int(index)
                for index in prior["columns"]
                if baseline_map.get(str(index)) is None
            ]
        else:
            raise SweepError(f"prior-v2 control lacks selected columns for {target}")
        atlas_columns = _columns_from_names(
            atlas_names,
            name_to_index,
            "Atlas control",
            allow_unavailable=True,
        )
        unavailable_atlas = [
            str(name) for name in atlas_names if str(name) not in name_to_index
        ]
        controls[target] = {
            "full-union": full,
            "recent-only-union": recent,
            "existing-809-control": existing,
            "atlas-winner-control": atlas_columns,
            "prior-v2-winner-control": prior_columns,
        }
        availability[target] = {
            "existing-809-control": {
                "requested": 809,
                "available": len(existing),
                "unavailable_after_quarantine_or_dedup": 809 - len(existing),
            },
            "atlas-winner-control": {
                "requested": len(atlas_names),
                "available": len(atlas_columns),
                "unavailable_feature_ids": unavailable_atlas,
            },
            "prior-v2-winner-control": {
                "requested": len(prior_names or prior.get("columns", [])),
                "available": len(prior_columns),
                "unavailable_feature_ids_or_indices": unavailable_prior,
            },
        }
    atomic_json(
        settings.run_root / "genetic/control_availability.json",
        {**availability, "test_labels_used": False},
    )
    return controls


def _genome_jobs(population: Sequence[Genome], generation: int) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for genome in population:
        for fold in range(DISCOVERY_FOLDS):
            jobs.append(
                _new_job(
                    kind="screen",
                    stage=f"genetic-{generation:02d}",
                    target=genome.target,
                    view=genome.genome_id,
                    origin=genome.origin,
                    fold=fold,
                    cv_seed=DISCOVERY_FOLD_SEED,
                    model_seed=DISCOVERY_FOLD_SEED,
                    columns=list(genome.columns),
                    feature_count=len(genome.columns),
                    feature_set_hash=canonical_hash(genome.columns),
                    generation=generation,
                    iterations=SCREEN_TREES,
                )
            )
    return jobs


def _run_genetic(settings: Settings, scheduler: CampaignScheduler) -> dict[str, Any]:
    aggregate = {target: _load_ranking(settings, target) for target in TARGETS}
    fold_local = {
        target: [_load_ranking(settings, target, fold) for fold in range(DISCOVERY_FOLDS)]
        for target in TARGETS
    }
    cutoff_sets = json.loads(
        (settings.run_root / "cutoffs/feature_sets.json").read_text(encoding="utf-8")
    )
    controls = load_control_sets(settings)
    atomic_json(settings.run_root / "genetic/control_sets.json", controls)
    populations: dict[str, list[Genome]] = {}
    for target_index, target in enumerate(TARGETS):
        named: dict[str, Sequence[int]] = {
            f"percentile-{name}" if name.startswith("p") else f"interpolation-{name}": columns
            for name, columns in cutoff_sets[target].items()
        }
        named.update(controls[target])
        populations[target] = initial_population(
            target=target,
            aggregate_ranking=aggregate[target],
            fold_rankings=fold_local[target],
            named_sets=named,
            seed=20_260_719 + target_index,
        )
    archives: dict[str, list[tuple[Genome, float]]] = {target: [] for target in TARGETS}
    all_genomes: dict[str, Genome] = {}
    history_rows: list[dict[str, Any]] = []
    scheduled_fits = 0
    for generation in range(GENERATIONS):
        members = [genome for target in TARGETS for genome in populations[target]]
        for genome in members:
            all_genomes.setdefault(genome.genome_id, genome)
        jobs = _genome_jobs(members, generation)
        scheduled_fits += len(jobs)
        _record_schedule(settings, f"genetic-{generation:02d}", jobs)
        results = scheduler.run(f"genetic-{generation:02d}", jobs)
        curve = _score_curve(_score_rows(results))
        row_by_id = {str(row["view"]): row for row in curve.to_dict(orient="records")}
        for genome in members:
            row = row_by_id[genome.genome_id]
            if int(row["model_jobs"]) != DISCOVERY_FOLDS:
                raise AssertionError("every genetic genome must have five discovery folds")
            archives[genome.target].append((genome, float(row["mean_rmsle"])))
            history_rows.append(
                {
                    **{key: value for key, value in genome.as_dict().items() if key != "columns"},
                    "mean_rmsle": float(row["mean_rmsle"]),
                    "rmsle_std": float(row["rmsle_std"]),
                    "model_jobs": int(row["model_jobs"]),
                }
            )
        atomic_json(
            settings.run_root / f"genetic/generation-{generation:02d}.json",
            {
                "generation": generation,
                "population": [
                    {
                        **{key: value for key, value in genome.as_dict().items() if key != "columns"},
                        "mean_rmsle": float(row_by_id[genome.genome_id]["mean_rmsle"]),
                        "rmsle_std": float(row_by_id[genome.genome_id]["rmsle_std"]),
                    }
                    for genome in members
                ],
                "population_per_target": POPULATION_SIZE,
                "test_labels_used": False,
            },
        )
        if generation + 1 < GENERATIONS:
            populations = {
                target: breed_population(
                    target=target,
                    parent_archive=archives[target],
                    aggregate_ranking=aggregate[target],
                    generation=generation + 1,
                    seed=20_260_719 + target_index,
                )
                for target_index, target in enumerate(TARGETS)
            }
    history = pd.DataFrame(history_rows)
    expected_history = len(TARGETS) * POPULATION_SIZE * GENERATIONS
    if len(history) != expected_history:
        raise AssertionError("genetic history is not 24x10 for both targets")
    grid = history.groupby(["target", "generation"]).size()
    if not grid.eq(POPULATION_SIZE).all() or len(grid) != len(TARGETS) * GENERATIONS:
        raise AssertionError("genetic terminal population grid is incomplete")
    save_frame(history, settings.run_root / "genetic/history")
    atomic_json(
        settings.run_root / "genetic/genomes.json",
        {genome_id: genome.as_dict() for genome_id, genome in sorted(all_genomes.items())},
    )
    finalists: dict[str, list[dict[str, Any]]] = {}
    for target in TARGETS:
        target_history = history[history["target"] == target]
        best_rows = (
            target_history.sort_values(
                ["mean_rmsle", "rmsle_std", "feature_count", "genome_id"],
                kind="mergesort",
            )
            .drop_duplicates("genome_id")
            .to_dict(orient="records")
        )
        selected = choose_finalists(best_rows, all_genomes)
        finalists[target] = [genome.as_dict() for genome in selected]
    atomic_json(settings.run_root / "genetic/finalists.json", finalists)
    receipt = {
        "population_size": POPULATION_SIZE,
        "generations": GENERATIONS,
        "history_rows": len(history),
        "scheduled_fits": scheduled_fits,
        "finalists_per_target": {target: len(finalists[target]) for target in TARGETS},
        "parent_archive_retained": True,
    }
    _complete_phase(settings, "genetic", receipt)
    return receipt


def _genome_from_dict(value: dict[str, Any]) -> Genome:
    return Genome(
        target=str(value["target"]),
        columns=tuple(map(int, value["columns"])),
        generation=int(value.get("generation", 0)),
        origin=str(value.get("origin", "fixture")),
        parents=tuple(map(str, value.get("parents", []))),
    )


def _confirmation_jobs(genomes: Sequence[Genome]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for genome in genomes:
        for sealed_seed in SEALED_SEEDS:
            for fold in range(DISCOVERY_FOLDS):
                jobs.append(
                    _new_job(
                        kind="confirm",
                        stage="sealed-confirmation",
                        target=genome.target,
                        view=genome.genome_id,
                        origin=genome.origin,
                        fold=fold,
                        cv_seed=sealed_seed,
                        model_seed=sealed_seed,
                        columns=list(genome.columns),
                        feature_count=len(genome.columns),
                        feature_set_hash=canonical_hash(genome.columns),
                        iterations=CONFIRM_TREES,
                    )
                )
    return jobs


def _selection_detail(
    genome: Genome, registry: pd.DataFrame, score: dict[str, Any]
) -> dict[str, Any]:
    selected = registry.set_index("global_index").loc[list(genome.columns)].reset_index()
    family = (
        selected.groupby(["source", "domain", "family"], dropna=False)
        .size()
        .reset_index(name="count")
        .to_dict(orient="records")
    )
    hyperion = selected[
        selected["source"].astype(str).str.startswith("hyperion_")
    ][["global_index", "source_index", "feature_id", "source", "family"]].to_dict(
        orient="records"
    )
    return {
        "genome_id": genome.genome_id,
        "origin": genome.origin,
        "feature_count": len(genome.columns),
        "feature_set_hash": canonical_hash(genome.columns),
        "sealed_mean_rmsle": float(score["mean_rmsle"]),
        "sealed_rmsle_std": float(score["rmsle_std"]),
        "model_jobs": int(score["model_jobs"]),
        "sealed_seed_means": score["sealed_seed_means"],
        "feature_ids": selected["feature_id"].astype(str).tolist(),
        "original_indices": selected["global_index"].astype(int).tolist(),
        "source_indices": selected[
            ["global_index", "source", "source_index"]
        ].to_dict(orient="records"),
        "composition": family,
        "hyperion_selections": hyperion,
    }


def _run_confirmation(settings: Settings, scheduler: CampaignScheduler) -> dict[str, Any]:
    finalists_payload = json.loads(
        (settings.run_root / "genetic/finalists.json").read_text(encoding="utf-8")
    )
    controls = json.loads(
        (settings.run_root / "genetic/control_sets.json").read_text(encoding="utf-8")
    )
    finalists: dict[str, list[Genome]] = {
        target: [_genome_from_dict(value) for value in finalists_payload[target]]
        for target in TARGETS
    }
    all_genomes: dict[str, Genome] = {}
    preregistration: dict[str, Any] = {}
    members: list[Genome] = []
    control_names = (
        "existing-809-control",
        "atlas-winner-control",
        "prior-v2-winner-control",
    )
    for target in TARGETS:
        target_members = list(finalists[target])
        target_controls = [
            _genome(target, controls[target][name], 0, name) for name in control_names
        ]
        unique: dict[str, Genome] = {}
        for genome in [*target_members, *target_controls]:
            unique.setdefault(genome.genome_id, genome)
            all_genomes.setdefault(genome.genome_id, genome)
        members.extend(unique.values())
        preregistration[target] = {
            "finalists": [genome.as_dict() for genome in target_members],
            "controls": [genome.as_dict() for genome in target_controls],
        }
    preregistration.update(
        {
            "registered_at": utc_now(),
            "adaptive_search_complete": True,
            "sealed_seeds": list(SEALED_SEEDS),
            "folds_per_seed": DISCOVERY_FOLDS,
            "trees": CONFIRM_TREES,
            "test_labels_used": False,
        }
    )
    atomic_json(settings.run_root / "confirmation/preregistration.json", preregistration)
    atomic_json(
        settings.run_root / "confirmation/sealed-opened.json",
        {
            "opened_at": utc_now(),
            "after_preregistration": True,
            "preregistration_sha256": sha256_file(
                settings.run_root / "confirmation/preregistration.json"
            ),
            "test_labels_used": False,
        },
    )
    jobs = _confirmation_jobs(members)
    _record_schedule(settings, "sealed-confirmation", jobs)
    results = scheduler.run("sealed-confirmation", jobs)
    fold_scores = _score_rows(results)
    save_frame(fold_scores, settings.run_root / "confirmation/fold_scores")
    curve = _score_curve(fold_scores)
    per_seed = fold_scores.groupby(
        ["target", "view", "cv_seed"], as_index=False
    )["rmsle"].mean()
    seed_means = {
        (str(target), str(view)): {
            str(int(row.cv_seed)): float(row.rmsle)
            for row in group.itertuples(index=False)
        }
        for (target, view), group in per_seed.groupby(["target", "view"], sort=False)
    }
    curve["sealed_seed_means_json"] = curve.apply(
        lambda row: json.dumps(seed_means[(row["target"], row["view"])], sort_keys=True),
        axis=1,
    )
    save_frame(curve, settings.run_root / "confirmation/score_curve")
    score_by_id: dict[tuple[str, str], dict[str, Any]] = {}
    for row in curve.to_dict(orient="records"):
        if int(row["model_jobs"]) != len(SEALED_SEEDS) * DISCOVERY_FOLDS:
            raise AssertionError("sealed candidate lacks the two-seed five-fold grid")
        row["sealed_seed_means"] = json.loads(row.pop("sealed_seed_means_json"))
        score_by_id[(str(row["target"]), str(row["view"]))] = row
    winners: dict[str, dict[str, Any]] = {}
    compact: dict[str, dict[str, Any] | None] = {}
    control_scores: dict[str, dict[str, float]] = {}
    registry = pd.read_parquet(settings.bundle / "feature_registry.parquet")
    for target in TARGETS:
        target_rows = [
            row for (row_target, _genome_id), row in score_by_id.items() if row_target == target
        ]
        winner_score = select_lowest(target_rows)
        winner_genome = all_genomes[str(winner_score["view"])]
        winners[target] = _selection_detail(winner_genome, registry, winner_score)
        smaller = [
            row
            for row in target_rows
            if int(row["feature_count"]) < len(winner_genome.columns)
        ]
        if smaller:
            compact_score = select_lowest(smaller)
            compact[target] = _selection_detail(
                all_genomes[str(compact_score["view"])], registry, compact_score
            )
        else:
            compact[target] = None
        control_scores[target] = {}
        for control_name in control_names:
            control_genome = _genome(target, controls[target][control_name], 0, control_name)
            score = score_by_id[(target, control_genome.genome_id)]
            control_scores[target][control_name] = float(score["mean_rmsle"])
            winners[target][f"lift_over_{control_name}"] = (
                float(score["mean_rmsle"]) - winners[target]["sealed_mean_rmsle"]
            )
    mean_rmsle = float(np.mean([winners[target]["sealed_mean_rmsle"] for target in TARGETS]))
    payload = {
        "winners": winners,
        "strongest_compact_alternative": compact,
        "same_fold_controls": control_scores,
        "final_mean_rmsle": mean_rmsle,
        "frozen_reference_mean_rmsle": FROZEN_REFERENCE,
        "lift_over_frozen_reference": FROZEN_REFERENCE - mean_rmsle,
        "sealed_seeds": list(SEALED_SEEDS),
        "folds_per_seed": DISCOVERY_FOLDS,
        "test_labels_used": False,
    }
    atomic_json(settings.run_root / "confirmation/results.json", payload)
    receipt = {
        "scheduled_fits": len(jobs),
        "views_per_target": {
            target: len(preregistration[target]["finalists"]) for target in TARGETS
        },
        "control_views_per_target": len(control_names),
        "sealed_seeds": list(SEALED_SEEDS),
        "folds_per_seed": DISCOVERY_FOLDS,
        "final_mean_rmsle": mean_rmsle,
    }
    _complete_phase(settings, "confirmation", receipt)
    return payload


def _run_report(settings: Settings) -> dict[str, Any]:
    results = json.loads(
        (settings.run_root / "confirmation/results.json").read_text(encoding="utf-8")
    )
    report = {
        "run_id": settings.run_id,
        "protocol": json.loads(
            (settings.run_root / "protocol.json").read_text(encoding="utf-8")
        ),
        **results,
        "reported_at": utc_now(),
        "reproducible": True,
        "test_labels_used": False,
    }
    atomic_json(settings.run_root / "reports/final.json", report)
    lines = [
        "# Full-Space Random Importance Sweep and Genetic Search",
        "",
        f"Sealed mean RMSLE: **{report['final_mean_rmsle']:.10f}**.",
        f"Frozen reference: **{FROZEN_REFERENCE:.10f}**; lift: "
        f"**{report['lift_over_frozen_reference']:+.10f}**.",
        "",
    ]
    for target in TARGETS:
        winner = report["winners"][target]
        lines.extend(
            [
                f"## {target}",
                "",
                f"RMSLE {winner['sealed_mean_rmsle']:.10f} ± "
                f"{winner['sealed_rmsle_std']:.10f}; {winner['feature_count']} features; "
                f"{len(winner['hyperion_selections'])} Hyperion features.",
                "",
            ]
        )
    report_path = settings.run_root / "reports/final.md"
    temporary = report_path.with_name(f".{report_path.name}.{os.getpid()}.tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temporary, report_path)
    artifacts: list[Path] = []
    for directory in ("bundle", "importance", "cutoffs", "genetic", "confirmation", "reports"):
        for path in sorted((settings.run_root / directory).rglob("*")):
            if path.is_file() and not path.name.startswith(".verified-"):
                artifacts.append(path)
    artifacts.extend([settings.run_root / "protocol.json"])
    files = {
        str(path.relative_to(settings.run_root)): sha256_file(path) for path in artifacts
    }
    manifest = {
        "files": files,
        "bundle_sha256": verify_full_space_bundle(settings.bundle)["bundle_sha256"],
        "report_sha256": sha256_file(settings.run_root / "reports/final.json"),
        "test_labels_used": False,
    }
    manifest["manifest_sha256"] = canonical_hash(manifest)
    atomic_json(settings.run_root / "final_hashes/manifest.json", manifest)
    _complete_phase(
        settings,
        "report",
        {
            "final_mean_rmsle": report["final_mean_rmsle"],
            "lift_over_frozen_reference": report["lift_over_frozen_reference"],
            "artifact_files": len(files),
            "manifest_sha256": manifest["manifest_sha256"],
        },
    )
    return report


def run(
    settings: Settings,
    *,
    remote_host: str | None = "xbabe1",
    remote_bundle: Path | None = None,
    scheduler: CampaignScheduler | None = None,
) -> dict[str, Any]:
    """Run every unfinished phase; cached fits make repeated calls resumable."""
    state = _state(settings)
    if "prepare" not in state.get("completed_phases", []):
        raise SweepError("prepare must complete before run")
    verify_full_space_bundle(settings.bundle)
    protocol = json.loads((settings.run_root / "protocol.json").read_text(encoding="utf-8"))
    if sha256_file(settings.worker) != protocol.get("worker_sha256"):
        raise SweepError("worker changed after prepare")
    if protocol.get("controller_sha256") and sha256_file(Path(__file__)) != protocol.get(
        "controller_sha256"
    ):
        raise SweepError("full-space controller changed after prepare")
    completed = set(state.get("completed_phases", []))
    compute_needed = any(
        phase not in completed for phase in ("importance", "cutoffs", "genetic", "confirmation")
    )
    active_scheduler = scheduler
    if compute_needed and active_scheduler is None:
        active_scheduler = CampaignScheduler(
            settings,
            remote_host=remote_host,
            remote_bundle=remote_bundle
            or Path(f"/home/ubuntu/fullspace-sweep-{settings.run_id}/bundle"),
        )
    if "importance" not in completed:
        assert active_scheduler is not None
        _run_importance(settings, active_scheduler)
        completed.add("importance")
    if "cutoffs" not in completed:
        assert active_scheduler is not None
        _run_cutoffs(settings, active_scheduler)
        completed.add("cutoffs")
    if "genetic" not in completed:
        assert active_scheduler is not None
        _run_genetic(settings, active_scheduler)
        completed.add("genetic")
    if "confirmation" not in completed:
        assert active_scheduler is not None
        _run_confirmation(settings, active_scheduler)
        completed.add("confirmation")
    if "report" not in completed:
        _run_report(settings)
    verification = verify(settings)
    if not verification["complete"]:
        raise SweepError("campaign verification failed: " + "; ".join(verification["missing"][:5]))
    return json.loads((settings.run_root / "reports/final.json").read_text(encoding="utf-8"))


def resume(
    settings: Settings,
    *,
    remote_host: str | None = "xbabe1",
    remote_bundle: Path | None = None,
    scheduler: CampaignScheduler | None = None,
) -> dict[str, Any]:
    return run(
        settings,
        remote_host=remote_host,
        remote_bundle=remote_bundle,
        scheduler=scheduler,
    )


def status(settings: Settings) -> dict[str, Any]:
    state = _state(settings)
    completed = list(state.get("completed_phases", []))
    cache_count = (
        len(list((settings.run_root / "cache/model-results").glob("*.json")))
        if settings.run_root.exists()
        else 0
    )
    next_phase = next((phase for phase in PHASES if phase not in completed), None)
    payload: dict[str, Any] = {
        "run_id": settings.run_id,
        "run_root": str(settings.run_root),
        "completed_phases": completed,
        "next_phase": next_phase,
        "cached_fits": cache_count,
        "complete": next_phase is None,
    }
    if (settings.run_root / "bundle/bundle_manifest.json").exists():
        manifest = json.loads(
            (settings.run_root / "bundle/bundle_manifest.json").read_text(encoding="utf-8")
        )
        payload["bundle"] = {
            key: manifest.get(key)
            for key in (
                "bundle_sha256",
                "pre_dedup_union",
                "predictors",
                "duplicates_mapped",
                "quarantined",
            )
        }
    if (settings.run_root / "reports/final.json").exists():
        report = json.loads(
            (settings.run_root / "reports/final.json").read_text(encoding="utf-8")
        )
        payload["final_mean_rmsle"] = report.get("final_mean_rmsle")
        payload["lift_over_frozen_reference"] = report.get("lift_over_frozen_reference")
    return payload


def verify(settings: Settings) -> dict[str, Any]:
    """Verify acceptance accounting, schedules, sealed scores, and final hashes."""
    missing: list[str] = []
    state = _state(settings)
    completed = set(state.get("completed_phases", []))
    for phase in PHASES:
        if phase not in completed:
            missing.append(f"phase: {phase}")
    manifest: dict[str, Any] | None = None
    try:
        manifest = verify_full_space_bundle(settings.bundle)
        if int(manifest["pre_dedup_union"]) != EXPECTED_UNION:
            missing.append("100% accounting of the 17,611-column valid union")
        if int(manifest["predictors"]) > EXPECTED_UNION:
            missing.append("at most 17,611 modeled predictors")
    except (OSError, ValueError, KeyError, SweepError) as error:
        missing.append(f"valid full-space bundle: {error}")
    observation_path = settings.run_root / "importance/observations.parquet"
    if observation_path.exists() and manifest is not None:
        observations = pd.read_parquet(observation_path)
        counts = observations.groupby(["target", "feature_index"]).size()
        expected_pairs = len(TARGETS) * int(manifest["predictors"])
        if len(counts) != expected_pairs or not counts.eq(25).all():
            missing.append("exactly 25 importance observations per target feature")
        for target in TARGETS:
            ranking_path = settings.run_root / f"importance/ranking_{target}.parquet"
            if not ranking_path.exists():
                missing.append(f"{target}: aggregate ranking")
                continue
            ranking = pd.read_parquet(ranking_path)
            if (
                sorted(ranking["global_index"].astype(int).tolist())
                != list(range(int(manifest["predictors"])))
                or not math.isclose(
                    float(ranking["globally_normalized_importance_share"].sum()),
                    1.0,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
            ):
                missing.append(f"{target}: normalized index-preserving aggregate ranking")
            for fold in range(DISCOVERY_FOLDS):
                if not (
                    settings.run_root / f"importance/ranking_{target}_fold_{fold}.parquet"
                ).exists():
                    missing.append(f"{target}: fold-local ranking {fold}")
    else:
        missing.append("raw importance observations")
    cutoff_path = settings.run_root / "cutoffs/score_curve.parquet"
    if cutoff_path.exists():
        curve = pd.read_parquet(cutoff_path)
        for target in TARGETS:
            percentiles = curve[
                (curve["target"] == target) & (curve["origin"] == "percentile")
            ]
            if len(percentiles) != len(PERCENTILES) or not percentiles["model_jobs"].eq(5).all():
                missing.append(f"{target}: seven five-fold cutoff scores")
    else:
        missing.append("cutoff score curve")
    history_path = settings.run_root / "genetic/history.parquet"
    if history_path.exists():
        history = pd.read_parquet(history_path)
        grid = history.groupby(["target", "generation"]).size()
        if (
            len(grid) != len(TARGETS) * GENERATIONS
            or not grid.eq(POPULATION_SIZE).all()
            or not history["model_jobs"].eq(DISCOVERY_FOLDS).all()
        ):
            missing.append("terminal 24x10 genetic histories for both targets")
    else:
        missing.append("genetic history")
    prereg_path = settings.run_root / "confirmation/preregistration.json"
    confirmation_path = settings.run_root / "confirmation/score_curve.parquet"
    if prereg_path.exists() and confirmation_path.exists():
        prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
        curve = pd.read_parquet(confirmation_path)
        for target in TARGETS:
            if not 1 <= len(prereg.get(target, {}).get("finalists", [])) <= FINALIST_LIMIT:
                missing.append(f"{target}: one to eight preregistered finalists")
            if len(prereg.get(target, {}).get("controls", [])) != 3:
                missing.append(f"{target}: existing-809, Atlas, and prior-v2 controls")
            target_curve = curve[curve["target"] == target]
            if target_curve.empty or not target_curve["model_jobs"].eq(
                len(SEALED_SEEDS) * DISCOVERY_FOLDS
            ).all():
                missing.append(f"{target}: sealed two-seed five-fold confirmation")
            for value in target_curve.get("sealed_seed_means_json", []):
                if set(map(int, json.loads(value))) != set(SEALED_SEEDS):
                    missing.append(f"{target}: both sealed seed summaries")
                    break
    else:
        missing.append("sealed preregistration and score curve")
    report_path = settings.run_root / "reports/final.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if set(report.get("winners", {})) != set(TARGETS):
            missing.append("independent final feature set for both targets")
        else:
            recalculated = float(
                np.mean(
                    [
                        report["winners"][target]["sealed_mean_rmsle"]
                        for target in TARGETS
                    ]
                )
            )
            if not math.isclose(
                recalculated,
                float(report.get("final_mean_rmsle", math.nan)),
                rel_tol=0.0,
                abs_tol=1e-15,
            ):
                missing.append("reproducible final mean RMSLE")
        if report.get("frozen_reference_mean_rmsle") != FROZEN_REFERENCE:
            missing.append("frozen 0.0495014095 comparison")
        if report.get("test_labels_used") is not False:
            missing.append("no test labels")
    else:
        missing.append("final mean RMSLE report")
    schedule_paths = sorted((settings.run_root / "receipts/schedules").glob("*.json"))
    cache_root = settings.run_root / "cache/model-results"
    for path in schedule_paths:
        schedule = json.loads(path.read_text(encoding="utf-8"))
        absent = [key for key in schedule.get("cache_keys", []) if not (cache_root / f"{key}.json").exists()]
        if absent:
            missing.append(f"all scheduled fits cached for {schedule.get('stage')}")
    hash_path = settings.run_root / "final_hashes/manifest.json"
    if hash_path.exists():
        hashes = json.loads(hash_path.read_text(encoding="utf-8"))
        expected_hash = hashes.pop("manifest_sha256", None)
        if canonical_hash(hashes) != expected_hash:
            missing.append("final hash-manifest identity")
        drift = [
            relative
            for relative, digest in hashes.get("files", {}).items()
            if not (settings.run_root / relative).is_file()
            or sha256_file(settings.run_root / relative) != digest
        ]
        if drift:
            missing.append(f"final artifact hashes: {drift[:5]}")
    else:
        missing.append("final artifact hash manifest")
    payload = {
        "run_id": settings.run_id,
        "complete": not missing,
        "missing": missing,
        "verified_at": utc_now(),
        "test_labels_used": False,
    }
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        payload["final_mean_rmsle"] = report.get("final_mean_rmsle")
        payload["lift_over_frozen_reference"] = report.get("lift_over_frozen_reference")
    atomic_json(settings.run_root / "verification.json", payload)
    return payload


def _settings_from_args(args: argparse.Namespace) -> Settings:
    return Settings(run_id=args.run_id, inbox=args.inbox.resolve())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("run_id")
    prepare_parser.add_argument("--baseline-bundle", type=Path, default=DEFAULT_BASELINE)
    prepare_parser.add_argument("--recent-root", type=Path, default=DEFAULT_RECENT)
    prepare_parser.add_argument(
        "--hyperion-manifest", type=Path, default=DEFAULT_HYPERION_MANIFEST
    )
    prepare_parser.add_argument("--skip-gpu-smoke", action="store_true")
    for command in ("run", "resume", "status", "verify"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("run_id")
        if command in {"run", "resume"}:
            command_parser.add_argument("--remote-host", default="xbabe1")
            command_parser.add_argument("--no-remote", action="store_true")
            command_parser.add_argument("--remote-bundle", type=Path)
    args = parser.parse_args(argv)
    settings = _settings_from_args(args)
    if args.command == "prepare":
        payload = prepare(
            settings,
            baseline_bundle=args.baseline_bundle,
            recent_root=args.recent_root,
            hyperion_manifest=args.hyperion_manifest,
            gpu_smoke=not args.skip_gpu_smoke,
        )
    elif args.command in {"run", "resume"}:
        payload = run(
            settings,
            remote_host=None if args.no_remote else args.remote_host,
            remote_bundle=args.remote_bundle,
        )
    elif args.command == "status":
        payload = status(settings)
    else:
        payload = verify(settings)
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    return 0 if args.command != "verify" or payload["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
