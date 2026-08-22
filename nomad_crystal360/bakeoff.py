"""Public-label feature-importance bake-off for CrystalAtlas and Hyperion.

The module keeps data validation and selection bookkeeping independent from the
GPU worker.  In particular, test targets are not accepted by the bundle builder
and fold-local rankings are the only rankings used by the two-fold cut search.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from .constants import TARGETS


ATLAS_WIDTH = 9_969
EXISTING_WIDTH = 809
HYPERION_CELLMAT_WIDTH = 449
HYPERION_EMBEDDING_WIDTH = 128
EXPECTED_WIDTH = ATLAS_WIDTH + HYPERION_CELLMAT_WIDTH + HYPERION_EMBEDDING_WIDTH
CHUNK_WIDTH = 300
SWEEP_SEEDS = (1_701, 2_909, 4_219)
SELECTION_FOLDS = 2
CONFIRMATION_FOLDS = 5
FOLD_SEED = 4_219
SCREEN_ITERATIONS = 150
CONFIRM_ITERATIONS = 400
IMPORTANCE_PERCENTILES = (
    0.0,
    20.0,
    40.0,
    50.0,
    60.0,
    70.0,
    75.0,
    80.0,
    85.0,
    90.0,
    92.5,
    95.0,
    96.0,
    97.0,
    98.0,
    98.5,
    99.0,
    99.25,
    99.5,
)
TARGET_HOSTS = {
    "formation_energy_ev_natom": "local",
    "bandgap_energy_ev": "xbabe1",
}
MODEL_PARAMETERS = {
    "loss_function": "RMSE",
    "depth": 7,
    "learning_rate": 0.05,
    "task_type": "GPU",
    "devices": "0",
    "allow_writing_files": False,
    "verbose": False,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _write_npy(path: Path, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.save(handle, values, allow_pickle=False)
    os.replace(temporary, path)


def _array_signature(train: np.ndarray, test: np.ndarray) -> str:
    digest = hashlib.sha256()
    for values in (train, test):
        array = np.ascontiguousarray(values, dtype="<f4")
        missing = np.isnan(array)
        canonical = array.copy()
        canonical[missing] = 0.0
        digest.update(missing.tobytes())
        digest.update(canonical.tobytes())
    return digest.hexdigest()


def _load_frame_or_array(path: Path) -> tuple[np.ndarray, np.ndarray | None]:
    """Load a numeric matrix and an optional in-file id column."""
    suffix = path.suffix.lower()
    ids: np.ndarray | None = None
    if suffix == ".npy":
        values = np.load(path, allow_pickle=False)
    elif suffix == ".npz":
        archive = np.load(path, allow_pickle=False)
        keys = list(archive.files)
        matrix_key = "data" if "data" in keys else "matrix" if "matrix" in keys else None
        if matrix_key is None:
            candidates = [key for key in keys if key not in {"id", "ids", "row_ids"}]
            if len(candidates) != 1:
                raise ValueError(f"Cannot identify one matrix array in {path}: {keys}")
            matrix_key = candidates[0]
        values = archive[matrix_key]
        for key in ("row_ids", "ids", "id"):
            if key in archive:
                ids = np.asarray(archive[key])
                break
    elif suffix in {".parquet", ".pq"}:
        frame = pd.read_parquet(path)
        id_column = next((name for name in ("id", "row_id") if name in frame), None)
        if id_column is not None:
            ids = frame.pop(id_column).to_numpy()
        values = frame.to_numpy()
    elif suffix in {".csv", ".txt"}:
        frame = pd.read_csv(path)
        id_column = next((name for name in ("id", "row_id") if name in frame), None)
        if id_column is not None:
            ids = frame.pop(id_column).to_numpy()
        values = frame.to_numpy()
    else:
        raise ValueError(f"Unsupported Hyperion matrix format: {path}")
    values = np.asarray(values)
    if values.ndim != 2:
        raise ValueError(f"Hyperion matrix must be two-dimensional: {path} has {values.shape}")
    if not np.issubdtype(values.dtype, np.number):
        raise ValueError(f"Hyperion matrix is not numeric: {path}")
    return values, ids


def _load_ids(path: Path) -> np.ndarray:
    suffix = path.suffix.lower()
    if suffix == ".npy":
        values = np.load(path, allow_pickle=False)
    elif suffix == ".npz":
        archive = np.load(path, allow_pickle=False)
        key = next((item for item in ("row_ids", "ids", "id") if item in archive), None)
        if key is None:
            if len(archive.files) != 1:
                raise ValueError(f"Cannot identify row ids in {path}")
            key = archive.files[0]
        values = archive[key]
    elif suffix in {".parquet", ".pq"}:
        frame = pd.read_parquet(path)
        key = next((item for item in ("id", "row_id") if item in frame), None)
        if key is None:
            if frame.shape[1] != 1:
                raise ValueError(f"Cannot identify row ids in {path}")
            key = frame.columns[0]
        values = frame[key].to_numpy()
    else:
        frame = pd.read_csv(path)
        key = next((item for item in ("id", "row_id") if item in frame), frame.columns[0])
        values = frame[key].to_numpy()
    values = np.asarray(values)
    if values.ndim != 1:
        raise ValueError(f"Row ids must be one-dimensional: {path}")
    return values


_ROLE_ALIASES = {
    "cellmat_train": "cellmat_train",
    "train_cellmat": "cellmat_train",
    "hyperion_cellmat_train": "cellmat_train",
    "cell_matrix_train": "cellmat_train",
    "cellmat_test": "cellmat_test",
    "test_cellmat": "cellmat_test",
    "hyperion_cellmat_test": "cellmat_test",
    "cell_matrix_test": "cellmat_test",
    "embedding_train": "embedding_train",
    "train_embedding": "embedding_train",
    "hyperion_embedding_train": "embedding_train",
    "embedding_test": "embedding_test",
    "test_embedding": "embedding_test",
    "hyperion_embedding_test": "embedding_test",
    "train_row_ids": "train_row_ids",
    "row_ids_train": "train_row_ids",
    "test_row_ids": "test_row_ids",
    "row_ids_test": "test_row_ids",
}


def _manifest_entries(manifest_path: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_files = payload.get("files")
    if not isinstance(raw_files, (dict, list)):
        raise ValueError("Hyperion manifest must contain a 'files' mapping or list")
    items: list[tuple[str, Any]]
    if isinstance(raw_files, dict):
        items = list(raw_files.items())
    else:
        items = [(str(index), value) for index, value in enumerate(raw_files)]
    entries: dict[str, dict[str, Any]] = {}
    ignored: list[dict[str, Any]] = []
    for key, raw in items:
        item = {"path": raw} if isinstance(raw, str) else dict(raw)
        role_text = str(item.get("role", key)).lower().replace("-", "_")
        path_value = item.get("path", item.get("file", key))
        path = Path(path_value)
        if not path.is_absolute():
            path = manifest_path.parent / path
        if not path.is_file():
            raise FileNotFoundError(f"Hyperion manifest file does not exist: {path}")
        expected_hash = item.get("sha256")
        if not expected_hash:
            raise ValueError(f"Hyperion manifest has no sha256 for {path_value}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"Hyperion hash mismatch for {path_value}: {actual_hash} != {expected_hash}"
            )
        item.update({"path": path, "sha256": actual_hash, "role": role_text})
        normalized_role = _ROLE_ALIASES.get(role_text)
        is_mean = bool(item.get("mean")) or "mean" in role_text or "mean" in path.name.lower()
        if is_mean:
            if path.suffix.lower() in {".npy", ".npz", ".parquet", ".pq", ".csv", ".txt"}:
                mean_values, _mean_ids = _load_frame_or_array(path)
                if mean_values.shape[0] != 1:
                    raise ValueError(f"Hyperion mean artifact must contain exactly one row: {path}")
            ignored.append({**item, "path": str(path), "reason": "one_row_mean_excluded"})
        elif normalized_role is None:
            ignored.append({**item, "path": str(path), "reason": "non_matrix_manifest_file"})
        elif normalized_role in entries:
            raise ValueError(f"Duplicate Hyperion manifest role: {normalized_role}")
        else:
            entries[normalized_role] = item

    row_ids = payload.get("row_ids", {})
    if isinstance(row_ids, dict):
        for split in ("train", "test"):
            if f"{split}_row_ids" in entries or split not in row_ids:
                continue
            raw = row_ids[split]
            item = {"path": raw} if isinstance(raw, str) else dict(raw)
            path = Path(item["path"])
            if not path.is_absolute():
                path = manifest_path.parent / path
            expected_hash = item.get("sha256")
            if not expected_hash:
                raise ValueError(f"Hyperion row-id manifest has no sha256 for {split}")
            actual_hash = sha256_file(path)
            if actual_hash != expected_hash:
                raise ValueError(f"Hyperion row-id hash mismatch for {split}")
            entries[f"{split}_row_ids"] = {
                **item,
                "path": path,
                "sha256": actual_hash,
                "role": f"{split}_row_ids",
            }
    return entries, ignored


def _validate_ids(label: str, actual: np.ndarray, expected: np.ndarray) -> None:
    actual_strings = np.asarray(actual).astype(str)
    expected_strings = np.asarray(expected).astype(str)
    if actual_strings.shape != expected_strings.shape or not np.array_equal(
        actual_strings, expected_strings
    ):
        raise ValueError(f"Hyperion {label} row ids do not match Atlas row order")


def _source_rows(atlas_columns: Sequence[str], atlas_definitions: Path | None) -> list[dict[str, Any]]:
    family_by_name: dict[str, str] = {}
    if atlas_definitions is not None and atlas_definitions.exists():
        definitions = json.loads(atlas_definitions.read_text(encoding="utf-8"))
        family_by_name = {item["name"]: item.get("family", "crystal_atlas") for item in definitions}
    rows: list[dict[str, Any]] = []
    for index, name in enumerate(atlas_columns):
        source = "existing_809" if index < EXISTING_WIDTH else "crystal_atlas"
        rows.append(
            {
                "index": index,
                "feature": name,
                "source_family": source,
                "feature_family": family_by_name.get(name, source),
                "original_index": index,
            }
        )
    return rows


def build_public_bundle(
    *,
    atlas_dir: Path,
    row_id_dir: Path,
    hyperion_manifest: Path | None,
    output_dir: Path,
    expected_atlas_width: int = ATLAS_WIDTH,
    expected_cellmat_width: int = HYPERION_CELLMAT_WIDTH,
    expected_embedding_width: int = HYPERION_EMBEDDING_WIDTH,
) -> dict[str, Any]:
    """Validate Atlas, optionally add Hyperion, and never read test labels."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty bundle directory: {output_dir}")

    atlas_train_path = atlas_dir / "train_predictors_atlas.parquet"
    atlas_test_path = atlas_dir / "test_predictors_atlas.parquet"
    target_path = atlas_dir / "public_targets.parquet"
    train_ids_path = row_id_dir / "train_row_ids.csv"
    test_ids_path = row_id_dir / "test_row_ids.csv"
    atlas_train = pd.read_parquet(atlas_train_path)
    atlas_test = pd.read_parquet(atlas_test_path)
    if list(atlas_train.columns) != list(atlas_test.columns):
        raise ValueError("Atlas train/test columns differ")
    if atlas_train.shape[1] != expected_atlas_width:
        raise ValueError(
            f"Expected {expected_atlas_width} Atlas columns, found {atlas_train.shape[1]}"
        )
    train_ids = _load_ids(train_ids_path)
    test_ids = _load_ids(test_ids_path)
    if len(atlas_train) != len(train_ids) or len(atlas_test) != len(test_ids):
        raise ValueError("Atlas matrix and row-id counts differ")

    atlas_only = hyperion_manifest is None
    entries: dict[str, dict[str, Any]] = {}
    ignored_files: list[dict[str, Any]] = []
    required: set[str] = set()
    if hyperion_manifest is not None:
        entries, ignored_files = _manifest_entries(hyperion_manifest)
        required = {"cellmat_train", "cellmat_test", "embedding_train", "embedding_test"}
        missing = required - entries.keys()
        if missing:
            raise ValueError(f"Hyperion manifest lacks required roles: {sorted(missing)}")

    matrices: dict[str, np.ndarray] = {}
    in_file_ids: dict[str, np.ndarray | None] = {}
    for role in sorted(required):
        matrix, ids = _load_frame_or_array(entries[role]["path"])
        matrices[role] = matrix
        in_file_ids[role] = ids
    expected_shapes = (
        {}
        if atlas_only
        else {
            "cellmat_train": (len(train_ids), expected_cellmat_width),
            "cellmat_test": (len(test_ids), expected_cellmat_width),
            "embedding_train": (len(train_ids), expected_embedding_width),
            "embedding_test": (len(test_ids), expected_embedding_width),
        }
    )
    for role, expected_shape in expected_shapes.items():
        if matrices[role].shape != expected_shape:
            raise ValueError(
                f"Expected Hyperion {role} shape {expected_shape}, found {matrices[role].shape}"
            )
        if not np.isfinite(matrices[role]).all():
            raise ValueError(f"Hyperion {role} contains a non-finite value")

    for split in (() if atlas_only else ("train", "test")):
        expected_ids = train_ids if split == "train" else test_ids
        sidecar = entries.get(f"{split}_row_ids")
        sidecar_ids = _load_ids(sidecar["path"]) if sidecar is not None else None
        in_file_checked: list[str] = []
        for family in ("cellmat", "embedding"):
            ids = in_file_ids[f"{family}_{split}"]
            if ids is not None:
                _validate_ids(f"{family} {split}", ids, expected_ids)
                in_file_checked.append(family)
        if sidecar_ids is not None:
            _validate_ids(split, sidecar_ids, expected_ids)
        elif set(in_file_checked) != {"cellmat", "embedding"}:
            raise ValueError(
                f"Hyperion {split} row alignment is unproven for every matrix; "
                "provide in-file ids or a hashed shared sidecar"
            )

    additions: list[tuple[str, str, int, np.ndarray, np.ndarray]] = []
    hyperion_families = () if atlas_only else (
        ("cellmat", expected_cellmat_width),
        ("embedding", expected_embedding_width),
    )
    for family, width in hyperion_families:
        train = np.asarray(matrices[f"{family}_train"], dtype=np.float32)
        test = np.asarray(matrices[f"{family}_test"], dtype=np.float32)
        prefix = "hyperion_cellmat" if family == "cellmat" else "hyperion_embedding"
        source = prefix
        for index in range(width):
            values = train[:, index]
            if np.unique(values).size <= 1 or float(np.var(values, dtype=np.float64)) <= 0.0:
                raise ValueError(f"Hyperion {prefix}_{index:03d} has zero training variance")
            additions.append((f"{prefix}_{index:03d}", source, index, values, test[:, index]))

    atlas_train_values = atlas_train.to_numpy(dtype=np.float32)
    atlas_test_values = atlas_test.to_numpy(dtype=np.float32)
    signatures = {
        _array_signature(atlas_train_values[:, index], atlas_test_values[:, index]): name
        for index, name in enumerate(atlas_train.columns)
    }
    kept: list[tuple[str, str, int, np.ndarray, np.ndarray]] = []
    duplicates: list[dict[str, str]] = []
    for name, source, original_index, train, test in additions:
        signature = _array_signature(train, test)
        if signature in signatures:
            duplicates.append({"feature": name, "duplicate_of": signatures[signature]})
            continue
        signatures[signature] = name
        kept.append((name, source, original_index, train, test))

    source_rows = _source_rows(
        list(atlas_train.columns), atlas_dir / "atlas_definitions.json"
    )
    for offset, (name, source, original_index, _train, _test) in enumerate(kept):
        source_rows.append(
            {
                "index": expected_atlas_width + offset,
                "feature": name,
                "source_family": source,
                "feature_family": source,
                "original_index": original_index,
            }
        )
    columns = [item["feature"] for item in source_rows]
    addition_train = (
        np.column_stack([item[3] for item in kept]).astype(np.float32)
        if kept
        else np.empty((len(train_ids), 0), dtype=np.float32)
    )
    addition_test = (
        np.column_stack([item[4] for item in kept]).astype(np.float32)
        if kept
        else np.empty((len(test_ids), 0), dtype=np.float32)
    )
    combined_train = np.column_stack([atlas_train_values, addition_train]).astype(np.float32)
    combined_test = np.column_stack([atlas_test_values, addition_test]).astype(np.float32)
    expected_validated_width = expected_atlas_width + len(additions) - len(duplicates)
    if combined_train.shape != (len(train_ids), expected_validated_width):
        raise AssertionError("Validated combined training width is inconsistent with deduplication")
    if combined_test.shape != (len(test_ids), expected_validated_width):
        raise AssertionError("Validated combined test width is inconsistent with deduplication")
    if len(columns) != combined_train.shape[1] or len(columns) != len(set(columns)):
        raise AssertionError("Combined feature registration is not one-to-one")

    targets_frame = pd.read_parquet(target_path)
    if list(targets_frame.columns) != list(TARGETS) or len(targets_frame) != len(train_ids):
        raise ValueError("Public training target schema or row count differs")
    targets = targets_frame.to_numpy(dtype=np.float64)
    if not np.isfinite(targets).all() or np.any(targets < 0.0):
        raise ValueError("Public targets must be finite and nonnegative for log1p training")
    selection = np.full(len(train_ids), -1, dtype=np.int8)
    for fold, (_, validation) in enumerate(
        KFold(SELECTION_FOLDS, shuffle=True, random_state=FOLD_SEED).split(train_ids)
    ):
        selection[validation] = fold
    confirmation = np.full(len(train_ids), -1, dtype=np.int8)
    for fold, (_, validation) in enumerate(
        KFold(CONFIRMATION_FOLDS, shuffle=True, random_state=FOLD_SEED).split(train_ids)
    ):
        confirmation[validation] = fold
    if np.any(selection < 0) or np.any(confirmation < 0):
        raise AssertionError("Fold construction left unassigned rows")

    output_files = {
        "train.npy": combined_train,
        "test.npy": combined_test,
        "targets.npy": targets,
        "train_ids.npy": np.asarray(train_ids),
        "test_ids.npy": np.asarray(test_ids),
        "selection_folds.npy": selection,
        "confirmation_folds.npy": confirmation,
    }
    for name, values in output_files.items():
        _write_npy(output_dir / name, values)
    _write_json(output_dir / "columns.json", columns)
    _write_json(output_dir / "targets.json", list(TARGETS))
    source_frame = pd.DataFrame(source_rows)
    source_frame.to_parquet(output_dir / "source_families.parquet", index=False)
    source_frame.to_csv(output_dir / "source_families.csv", index=False)

    quality = {
        "atlas_width": expected_atlas_width,
        "bundle_mode": "atlas_only" if atlas_only else "atlas_hyperion",
        "expected_pre_dedup_width": expected_atlas_width
        + (0 if atlas_only else expected_cellmat_width + expected_embedding_width),
        "validated_width": combined_train.shape[1],
        "duplicates_removed": duplicates,
        "ignored_manifest_files": ignored_files,
        "source_family_counts": dict(Counter(source_frame["source_family"])),
        "train_rows": len(train_ids),
        "test_rows": len(test_ids),
        "all_hyperion_values_finite": True,
        "all_hyperion_training_variances_positive": True,
        "train_test_columns_aligned": True,
        "row_ids_aligned": True,
    }
    _write_json(output_dir / "validation_report.json", quality)

    bundle_names = [
        *output_files,
        "columns.json",
        "targets.json",
        "source_families.parquet",
        "source_families.csv",
        "validation_report.json",
    ]
    files = {
        name: {
            "sha256": sha256_file(output_dir / name),
            "bytes": (output_dir / name).stat().st_size,
        }
        for name in bundle_names
    }
    identity_payload = {
        "files": files,
        "train_rows": len(train_ids),
        "test_rows": len(test_ids),
        "predictors": combined_train.shape[1],
        "targets": list(TARGETS),
        "selection_folds": SELECTION_FOLDS,
        "confirmation_folds": CONFIRMATION_FOLDS,
        "fold_seed": FOLD_SEED,
        "contains_test_targets": False,
    }
    input_hashes = {
        "atlas_train": sha256_file(atlas_train_path),
        "atlas_test": sha256_file(atlas_test_path),
        "public_targets": sha256_file(target_path),
        "train_row_ids": sha256_file(train_ids_path),
        "test_row_ids": sha256_file(test_ids_path),
    }
    if hyperion_manifest is not None:
        input_hashes["hyperion_manifest"] = sha256_file(hyperion_manifest)
    manifest = {
        **identity_payload,
        "bundle_sha256": canonical_hash(identity_payload),
        "bundle_mode": "atlas_only" if atlas_only else "atlas_hyperion",
        "input_hashes": input_hashes,
        "hyperion_manifest_files": {
            role: {"path": str(item["path"]), "sha256": item["sha256"]}
            for role, item in entries.items()
        },
        "test_labels_used": False,
    }
    _write_json(output_dir / "bundle_manifest.json", manifest)
    return manifest


def verify_public_bundle(bundle: Path, *, verify_hashes: bool = True) -> dict[str, Any]:
    manifest_path = bundle / "bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contains_test_targets") is not False or manifest.get("test_labels_used") is not False:
        raise ValueError("Bake-off bundle must attest that test targets are absent and unused")
    forbidden = [name for name in manifest["files"] if "test_target" in name.lower()]
    if forbidden:
        raise ValueError(f"Test target files are forbidden in the public bundle: {forbidden}")
    if verify_hashes:
        for name, metadata in manifest["files"].items():
            actual = sha256_file(bundle / name)
            if actual != metadata["sha256"]:
                raise ValueError(f"Public bundle hash mismatch for {name}")
    identity_payload = {
        key: manifest[key]
        for key in (
            "files",
            "train_rows",
            "test_rows",
            "predictors",
            "targets",
            "selection_folds",
            "confirmation_folds",
            "fold_seed",
            "contains_test_targets",
        )
    }
    if canonical_hash(identity_payload) != manifest["bundle_sha256"]:
        raise ValueError("Public bundle identity hash is inconsistent")
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
    if feature_count < width:
        raise ValueError(f"Need at least {width} features for fixed-width importance chunks")
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
            raise AssertionError("Importance chunks must contain exactly 300 unique columns")
        chunks.append(
            ImportanceChunk(
                sweep=seed,
                chunk=chunk_index,
                columns=columns,
                primary_columns=tuple(primary),
                context_columns=tuple(context),
            )
        )
    primary_counts = Counter(item for chunk in chunks for item in chunk.primary_columns)
    if primary_counts != Counter({index: 1 for index in range(feature_count)}):
        raise AssertionError("Each feature must be primary exactly once per sweep")
    return chunks


def make_importance_jobs(feature_count: int, targets: Iterable[str] = TARGETS) -> list[dict[str, Any]]:
    chunks = {
        seed: make_importance_chunks(feature_count, seed) for seed in SWEEP_SEEDS
    }
    jobs: list[dict[str, Any]] = []
    for target in targets:
        for fold in range(SELECTION_FOLDS):
            for seed in SWEEP_SEEDS:
                for chunk in chunks[seed]:
                    job = {
                        "kind": "importance",
                        "stage": "importance",
                        "target": target,
                        "fold": fold,
                        "sweep": seed,
                        "chunk": chunk.chunk,
                        "columns": list(chunk.columns),
                        "primary_columns": list(chunk.primary_columns),
                        "context_columns": list(chunk.context_columns),
                        "iterations": SCREEN_ITERATIONS,
                        "seed": seed,
                    }
                    job["job_id"] = canonical_hash(job)[:24]
                    jobs.append(job)
    return jobs


def normalize_importance(values: Sequence[float], *, expected_width: int = CHUNK_WIDTH) -> np.ndarray:
    importance = np.asarray(values, dtype=np.float64)
    if importance.shape != (expected_width,):
        raise ValueError(f"Expected {expected_width} importances, found {importance.shape}")
    if not np.isfinite(importance).all() or np.any(importance < 0.0):
        raise ValueError("Importance vector must be finite and nonnegative")
    total = float(importance.sum())
    if total <= 0.0:
        raise ValueError("Importance vector has zero total")
    importance /= total
    if not math.isclose(float(importance.sum()), 1.0, rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError("Normalized importance does not sum to one")
    return importance


def importance_tables(
    jobs_and_results: Sequence[tuple[dict[str, Any], dict[str, Any]]],
    source_families: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], dict[tuple[str, int], pd.DataFrame], pd.DataFrame]:
    """Build target-level and fold-local rankings from primary observations."""
    metadata = source_families.set_index("index").to_dict(orient="index")
    observations: list[dict[str, Any]] = []
    chunk_keys: set[tuple[str, int, int, int]] = set()
    for job, result in jobs_and_results:
        if job["kind"] != "importance":
            continue
        importance = normalize_importance(result["importance"])
        if not math.isclose(float(importance.sum()), 1.0, rel_tol=1e-12, abs_tol=1e-12):
            raise AssertionError("A chunk importance vector failed normalization")
        columns = list(job["columns"])
        if len(columns) != CHUNK_WIDTH or len(set(columns)) != CHUNK_WIDTH:
            raise AssertionError("Every ranking fit must contain exactly 300 unique columns")
        names = {index: metadata[index]["feature"] for index in columns}
        order = sorted(columns, key=lambda index: (-importance[columns.index(index)], names[index]))
        rank_by_index = {index: rank for rank, index in enumerate(order, start=1)}
        chunk_key = (job["target"], int(job["fold"]), int(job["sweep"]), int(job["chunk"]))
        if chunk_key in chunk_keys:
            raise ValueError(f"Duplicate importance result for chunk {chunk_key}")
        chunk_keys.add(chunk_key)
        for index in job["primary_columns"]:
            position = columns.index(index)
            row = metadata[index]
            observations.append(
                {
                    "target": job["target"],
                    "feature_index": index,
                    "feature": row["feature"],
                    "source_family": row["source_family"],
                    "feature_family": row["feature_family"],
                    "fold": int(job["fold"]),
                    "sweep": int(job["sweep"]),
                    "chunk": int(job["chunk"]),
                    "relative_importance": float(importance[position]),
                    "within_chunk_rank": rank_by_index[index],
                }
            )
    observation_frame = pd.DataFrame(observations)
    if observation_frame.empty:
        raise ValueError("No importance observations were supplied")
    expected_observations = len(SWEEP_SEEDS) * SELECTION_FOLDS
    counts = observation_frame.groupby(["target", "feature_index"]).size()
    observed_targets = {job["target"] for job, _result in jobs_and_results}
    expected_pairs = {
        (target, int(index)) for target in observed_targets for index in metadata
    }
    if set(counts.index.tolist()) != expected_pairs or not (counts == expected_observations).all():
        bad = counts[counts != expected_observations]
        missing = expected_pairs - set(counts.index.tolist())
        raise AssertionError(
            f"Features do not have six importance observations; bad={bad.to_dict()} "
            f"missing={sorted(missing)[:10]}"
        )

    def aggregate(frame: pd.DataFrame) -> pd.DataFrame:
        ranked = (
            frame.groupby(
                ["feature_index", "feature", "source_family", "feature_family"], as_index=False
            )
            .agg(
                mean_relative_importance=("relative_importance", "mean"),
                importance_std=("relative_importance", lambda values: float(np.std(values, ddof=0))),
                median_within_chunk_rank=("within_chunk_rank", "median"),
                observations=("relative_importance", "size"),
            )
            .sort_values(
                ["mean_relative_importance", "importance_std", "feature"],
                ascending=[False, True, True],
                kind="mergesort",
            )
            .reset_index(drop=True)
        )
        ranked.insert(0, "rank", np.arange(1, len(ranked) + 1, dtype=int))
        importance_total = float(ranked["mean_relative_importance"].sum())
        if importance_total <= 0.0:
            raise AssertionError("Aggregated feature importance has zero total")
        ranked["globally_normalized_importance_share"] = (
            ranked["mean_relative_importance"] / importance_total
        )
        ranked["empirical_importance_percentile"] = (
            100.0 * (len(ranked) - ranked["rank"] + 1) / len(ranked)
        )
        if not math.isclose(
            float(ranked["globally_normalized_importance_share"].sum()),
            1.0,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise AssertionError("Globally normalized importance shares do not sum to one")
        return ranked

    target_rankings = {
        target: aggregate(frame)
        for target, frame in observation_frame.groupby("target", sort=False)
    }
    fold_rankings = {
        (target, int(fold)): aggregate(frame)
        for (target, fold), frame in observation_frame.groupby(["target", "fold"], sort=False)
    }
    for ranking in fold_rankings.values():
        if not (ranking["observations"] == len(SWEEP_SEEDS)).all():
            raise AssertionError("Fold-local rankings must contain three observations per feature")
    return target_rankings, fold_rankings, observation_frame


def percentile_label(percentile: float) -> str:
    return f"p{percentile:g}"


def percentile_feature_count(feature_count: int, percentile: float) -> int:
    if feature_count <= 0:
        raise ValueError("Feature count must be positive")
    if percentile < 0.0 or percentile >= 100.0:
        raise ValueError("Importance percentile must be in [0, 100)")
    return feature_count - math.floor(feature_count * percentile / 100.0)


def percentile_thresholds(ranking: pd.DataFrame) -> pd.DataFrame:
    """Resolve fixed distribution percentiles to deterministic ranking prefixes."""
    if ranking.empty:
        raise ValueError("Cannot resolve percentiles for an empty ranking")
    expected_ranks = np.arange(1, len(ranking) + 1, dtype=int)
    if not np.array_equal(ranking["rank"].to_numpy(dtype=int), expected_ranks):
        raise ValueError("Ranking must be ordered and consecutively numbered")
    values = ranking["mean_relative_importance"].to_numpy(dtype=np.float64)
    rows: list[dict[str, Any]] = []
    prior_count = len(ranking) + 1
    for percentile in IMPORTANCE_PERCENTILES:
        count = percentile_feature_count(len(ranking), percentile)
        if count > prior_count:
            raise AssertionError("Percentile feature sets are not nested")
        boundary = ranking.iloc[count - 1]
        rows.append(
            {
                "percentile": percentile,
                "percentile_label": percentile_label(percentile),
                "feature_count": count,
                "distribution_importance_threshold": float(
                    np.percentile(values, percentile, method="linear")
                ),
                "boundary_mean_relative_importance": float(
                    boundary["mean_relative_importance"]
                ),
                "boundary_importance_std": float(boundary["importance_std"]),
                "boundary_feature": boundary["feature"],
                "boundary_empirical_importance_percentile": float(
                    boundary["empirical_importance_percentile"]
                ),
            }
        )
        prior_count = count
    return pd.DataFrame(rows)


def percentile_feature_sets(ranking: pd.DataFrame) -> dict[str, list[int]]:
    thresholds = percentile_thresholds(ranking)
    ranked_indices = ranking["feature_index"].astype(int).tolist()
    sets: dict[str, list[int]] = {}
    prior: set[int] | None = None
    for row in thresholds.itertuples(index=False):
        selected = ranked_indices[: int(row.feature_count)]
        selected_set = set(selected)
        if len(selected) != len(selected_set):
            raise AssertionError("A percentile feature set contains duplicates")
        if prior is not None and not selected_set.issubset(prior):
            raise AssertionError("Percentile feature sets are not nested")
        sets[str(row.percentile_label)] = selected
        prior = selected_set
    return sets


def initial_cut_counts(feature_count: int) -> list[int]:
    """Backward-compatible count view of the fixed percentile grid."""
    return [percentile_feature_count(feature_count, value) for value in IMPORTANCE_PERCENTILES]


def refinement_counts(initial_scores: dict[int, float]) -> list[int]:
    if len(initial_scores) < 2:
        return []
    tested = sorted(initial_scores)
    best = min(tested, key=lambda count: (initial_scores[count], count))
    best_index = tested.index(best)
    if best_index == 0:
        candidates = [best + 25, best + 50]
        lower, upper = best, tested[-1]
    elif best_index == len(tested) - 1:
        candidates = [best - 50, best - 25]
        lower, upper = tested[0], best
    else:
        neighborhood = tested[best_index - 1 : best_index + 2]
        x = np.log(np.asarray(neighborhood, dtype=np.float64))
        y = np.asarray([initial_scores[count] for count in neighborhood], dtype=np.float64)
        quadratic, linear, _constant = np.polyfit(x, y, 2)
        if quadratic > 0.0 and np.isfinite(quadratic) and np.isfinite(linear):
            vertex = -linear / (2.0 * quadratic)
            vertex = float(np.clip(vertex, x[0], x[-1]))
            center = int(round(math.exp(vertex) / 10.0) * 10)
        else:
            center = best
        candidates = [center - 50, center - 25, center, center + 25, center + 50]
        lower, upper = neighborhood[0], neighborhood[-1]
    return sorted({count for count in candidates if lower <= count <= upper and count not in tested})


def select_confirmed_cut(scores: dict[int, float], *, tolerance: float = 0.0001) -> int:
    if not scores:
        raise ValueError("No confirmed cut scores were supplied")
    best_score = min(scores.values())
    eligible = [count for count, score in scores.items() if score - best_score < tolerance]
    return min(eligible)


def select_confirmed_view(
    scores: dict[str, float], feature_counts: dict[str, int], *, tolerance: float = 0.0001
) -> str:
    if not scores or scores.keys() != feature_counts.keys():
        raise ValueError("Confirmed views need matching scores and feature counts")
    best_score = min(scores.values())
    eligible = [view for view, score in scores.items() if score - best_score < tolerance]
    return min(eligible, key=lambda view: (feature_counts[view], scores[view], view))


def rmsle(y_true: Sequence[float], prediction: Sequence[float]) -> float:
    y = np.asarray(y_true, dtype=np.float64)
    predicted = np.clip(np.asarray(prediction, dtype=np.float64), 0.0, None)
    if y.shape != predicted.shape:
        raise ValueError("RMSLE target and prediction shapes differ")
    return float(np.sqrt(np.mean((np.log1p(y) - np.log1p(predicted)) ** 2)))


def family_representation(
    ranking: pd.DataFrame, cuts: Iterable[int]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    families = sorted(ranking["source_family"].unique())
    for cut in sorted(set(cuts)):
        selected = ranking.head(cut)
        counts = selected["source_family"].value_counts()
        for family in families:
            count = int(counts.get(family, 0))
            rows.append(
                {
                    "cut": int(cut),
                    "source_family": family,
                    "count": count,
                    "fraction": float(count / len(selected)),
                }
            )
    return pd.DataFrame(rows)


class AppendOnlyEvents:
    """Append progress and cache events without rewriting prior history."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = path.with_suffix(path.suffix + ".lock")

    def append(self, event: dict[str, Any]) -> None:
        with self.lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            with self.path.open("a", encoding="utf-8") as output:
                output.write(json.dumps({"timestamp": time.time(), **event}, sort_keys=True) + "\n")
                output.flush()
                os.fsync(output.fileno())

    def completed_jobs(self) -> dict[str, dict[str, Any]]:
        completed: dict[str, dict[str, Any]] = {}
        if not self.path.exists():
            return completed
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            event = json.loads(line)
            if event.get("event") in {"job_completed", "cache_hit"} and "result" in event:
                completed[event["job_id"]] = event["result"]
        return completed


class ResultCache:
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)

    def path(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self.path(key)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def put(self, key: str, result: dict[str, Any]) -> Path:
        path = self.path(key)
        _write_json(path, result)
        return path


def model_cache_key(
    *, bundle_hash: str, runner_hash: str, environment_hash: str, job: dict[str, Any]
) -> str:
    return canonical_hash(
        {
            "bundle": bundle_hash,
            "runner": runner_hash,
            "environment": environment_hash,
            "job": job,
            "model_parameters": MODEL_PARAMETERS,
        }
    )


def selected_source_counts(columns: Sequence[int], source_families: pd.DataFrame) -> dict[str, int]:
    lookup = source_families.set_index("index")["source_family"]
    counts = Counter(lookup.loc[list(columns)].tolist())
    return {family: int(counts.get(family, 0)) for family in sorted(lookup.unique())}


def freeze_manifest(
    *,
    output_dir: Path,
    bundle_manifest: dict[str, Any],
    environment_identities: dict[str, Any],
    runner_path: Path,
    selected_columns: dict[str, list[str]],
    selected_indices: dict[str, list[int]],
    selected_counts: dict[str, dict[str, int]],
    scores: dict[str, Any],
    submission: Path,
    artifacts: Iterable[Path],
) -> Path:
    files = list(dict.fromkeys([submission, *artifacts]))
    manifest = {
        "frozen_at_unix": time.time(),
        "bundle_sha256": bundle_manifest["bundle_sha256"],
        "matrix_hashes": {
            name: bundle_manifest["files"][name]["sha256"] for name in ("train.npy", "test.npy")
        },
        "input_hashes": bundle_manifest["input_hashes"],
        "environment_identities": environment_identities,
        "runner_sha256": sha256_file(runner_path),
        "model_parameters": {
            **MODEL_PARAMETERS,
            "ranking_iterations": SCREEN_ITERATIONS,
            "screen_iterations": SCREEN_ITERATIONS,
            "confirmation_iterations": CONFIRM_ITERATIONS,
            "final_iterations": CONFIRM_ITERATIONS,
            "sweep_seeds": list(SWEEP_SEEDS),
            "fold_seed": FOLD_SEED,
        },
        "selected_columns": selected_columns,
        "selected_indices": selected_indices,
        "selected_source_counts": selected_counts,
        "scores": scores,
        "submission_sha256": sha256_file(submission),
        "artifacts": {
            str(path.relative_to(output_dir)): sha256_file(path)
            for path in files
            if path.exists()
        },
        "selection_uses_public_training_labels_only": True,
        "test_predictions_frozen": True,
        "test_labels_used_for_selection": False,
        "informational_test_scored": False,
    }
    path = output_dir / "freeze_manifest.json"
    _write_json(path, manifest)
    return path


def score_frozen_submission_once(
    *,
    output_dir: Path,
    labeled_test_dir: Path,
    benchmark_scores: Path | None = None,
) -> Path:
    """Score an already-frozen submission once without mutating its manifest."""
    freeze_path = output_dir / "freeze_manifest.json"
    submission_path = output_dir / "submission.csv"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if sha256_file(submission_path) != freeze["submission_sha256"]:
        raise ValueError("Submission changed after it was frozen")
    receipt = output_dir / "informational_test_score.json"
    descriptor = os.open(receipt, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        submission = pd.read_csv(submission_path)
        rows: list[dict[str, Any]] = []
        controls: dict[str, float] = {}
        if benchmark_scores is not None and benchmark_scores.exists():
            benchmark = pd.read_csv(benchmark_scores)
            control_rows = benchmark[benchmark["matrix"] == "combined_809"]
            controls = dict(zip(control_rows["target"], control_rows["rmsle"], strict=False))
        for target in TARGETS:
            label_path = labeled_test_dir / f"test_{target}_810.parquet"
            labels = pd.read_parquet(label_path, columns=[target])[target].to_numpy(dtype=float)
            score = rmsle(labels, submission[target].to_numpy(dtype=float))
            row = {
                "target": target,
                "rmsle": score,
                "status": "informational_only_historically_reused_test",
            }
            if target in controls:
                row["existing_809_rmsle"] = controls[target]
                row["lift_over_existing_809"] = controls[target] - score
            rows.append(row)
        payload = {
            "scored_at_unix": time.time(),
            "freeze_manifest_sha256": sha256_file(freeze_path),
            "submission_sha256": freeze["submission_sha256"],
            "scores": rows,
            "selection_changed_after_scoring": False,
            "informational_only": True,
        }
        os.write(descriptor, (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(descriptor)
    except Exception:
        os.close(descriptor)
        receipt.unlink(missing_ok=True)
        raise
    else:
        os.close(descriptor)
    return receipt
