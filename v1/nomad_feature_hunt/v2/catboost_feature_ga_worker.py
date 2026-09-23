#!/usr/bin/env python3
"""Parallel CatBoost CPU worker for CV-only feature-reduction batches."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import socket
import sys
import time
from typing import Any, Sequence

import numpy as np
from sklearn.model_selection import KFold


CATBOOST_VERSION = "1.2.10"
MODEL_PARAMETERS = {
    "loss_function": "RMSE",
    "depth": 7,
    "learning_rate": 0.05,
    "task_type": "CPU",
    "allow_writing_files": False,
    "verbose": False,
}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def verify_bundle(bundle: Path) -> dict[str, Any]:
    manifest = json.loads((bundle / "bundle_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("contains_test_targets") is not False:
        raise ValueError("bundle contains or does not exclude test targets")
    if manifest.get("test_labels_used") is not False:
        raise ValueError("bundle does not attest public-training-only selection")
    forbidden = [name for name in manifest.get("files", {}) if "test_target" in name.lower()]
    if forbidden:
        raise ValueError(f"bundle lists forbidden test target files: {forbidden}")
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
        raise ValueError("bundle identity hash is inconsistent")
    for name, metadata in manifest["files"].items():
        if sha256_file(bundle / name) != metadata["sha256"]:
            raise ValueError(f"bundle hash mismatch for {name}")
    return manifest


def environment_identity() -> dict[str, Any]:
    packages = ("catboost", "numpy", "pandas", "scikit-learn")
    identity = {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "cpu_count": os.cpu_count(),
        "packages": {name: importlib.metadata.version(name) for name in packages},
        "worker_sha256": sha256_file(Path(__file__)),
        "model_parameters": MODEL_PARAMETERS,
    }
    identity["sha256"] = canonical_hash(identity)
    return identity


def fold_masks(rows: int, seed: int, fold: int) -> tuple[np.ndarray, np.ndarray]:
    if fold not in range(5):
        raise ValueError("fold must be in [0, 5)")
    validation_indices = list(KFold(5, shuffle=True, random_state=seed).split(np.arange(rows)))[
        fold
    ][1]
    validation = np.zeros(rows, dtype=bool)
    validation[validation_indices] = True
    return ~validation, validation


def rmsle(target: np.ndarray, prediction: np.ndarray) -> float:
    prediction = np.clip(np.asarray(prediction, dtype=np.float64), 0.0, None)
    truth = np.asarray(target, dtype=np.float64)
    return float(np.sqrt(np.mean((np.log1p(truth) - np.log1p(prediction)) ** 2)))


def normalize_importance(values: Sequence[float], expected_width: int) -> np.ndarray:
    importance = np.asarray(values, dtype=np.float64)
    if importance.shape != (expected_width,):
        raise ValueError("CatBoost returned the wrong feature-importance width")
    if not np.isfinite(importance).all() or np.any(importance < 0.0):
        raise ValueError("feature importance must be finite and nonnegative")
    total = float(importance.sum())
    if total <= 0.0:
        return np.full(expected_width, 1.0 / expected_width, dtype=np.float64)
    return importance / total


def execute_job(
    bundle: Path, output: Path, job: dict[str, Any], threads_per_fit: int
) -> dict[str, Any]:
    from catboost import CatBoostRegressor

    started = time.monotonic()
    manifest = verify_bundle(bundle)
    train = np.load(bundle / "train.npy", mmap_mode="r", allow_pickle=False)
    targets = np.load(bundle / "targets.npy", mmap_mode="r", allow_pickle=False)
    target_names = json.loads((bundle / "targets.json").read_text(encoding="utf-8"))
    columns = np.asarray(job["columns"], dtype=np.int64)
    if columns.ndim != 1 or columns.size < 64 or len(np.unique(columns)) != len(columns):
        raise ValueError("job columns must contain at least 64 unique indices")
    if int(columns.min()) < 0 or int(columns.max()) >= train.shape[1]:
        raise ValueError("job contains an out-of-range column")
    target_index = target_names.index(job["target"])
    target = np.asarray(targets[:, target_index], dtype=np.float64)
    training, validation = fold_masks(len(train), int(job["cv_seed"]), int(job["fold"]))
    x_training = np.asarray(train[training][:, columns], dtype=np.float32)
    x_validation = np.asarray(train[validation][:, columns], dtype=np.float32)
    model = CatBoostRegressor(
        **MODEL_PARAMETERS,
        iterations=int(job["iterations"]),
        random_seed=int(job["model_seed"]),
        thread_count=threads_per_fit,
    )
    model.fit(x_training, np.log1p(target[training]), verbose=False)
    prediction = np.clip(np.expm1(model.predict(x_validation)), 0.0, None)
    importance = normalize_importance(
        model.get_feature_importance(type="PredictionValuesChange"), len(columns)
    )
    model_path = output / "models" / f"{job['job_id']}.cbm"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(model_path)
    result = {
        "status": "completed",
        "job_id": job["job_id"],
        "target": job["target"],
        "fold": int(job["fold"]),
        "cv_seed": int(job["cv_seed"]),
        "score": rmsle(target[validation], prediction),
        "columns": columns.tolist(),
        "feature_importance": importance.tolist(),
        "training_rows": int(training.sum()),
        "validation_rows": int(validation.sum()),
        "model_path": str(model_path),
        "model_sha256": sha256_file(model_path),
        "elapsed_seconds": time.monotonic() - started,
        "bundle_sha256": manifest["bundle_sha256"],
        "worker_sha256": sha256_file(Path(__file__)),
        "catboost_version": importlib.metadata.version("catboost"),
        "hostname": socket.gethostname(),
        "threads_per_fit": threads_per_fit,
        "test_labels_used": False,
    }
    atomic_json(output / "job-results" / f"{job['job_id']}.json", result)
    return result


def run_batch(
    bundle: Path,
    batch: Path,
    output: Path,
    *,
    workers: int,
    threads_per_fit: int,
) -> dict[str, Any]:
    if workers < 1 or threads_per_fit < 1:
        raise ValueError("workers and threads per fit must be positive")
    manifest = verify_bundle(bundle)
    payload = json.loads(batch.read_text(encoding="utf-8"))
    if payload.get("test_labels_used") is not False:
        raise ValueError("batch is missing the test-label prohibition")
    jobs = list(payload["jobs"])
    if len({job["job_id"] for job in jobs}) != len(jobs):
        raise ValueError("batch job IDs must be unique")
    results: dict[str, dict[str, Any]] = {}
    pending: list[dict[str, Any]] = []
    for job in jobs:
        result_path = output / "job-results" / f"{job['job_id']}.json"
        if result_path.exists():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            model_path = Path(result["model_path"])
            if model_path.exists() and sha256_file(model_path) == result["model_sha256"]:
                results[job["job_id"]] = result
                continue
        pending.append(job)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(execute_job, bundle, output, job, threads_per_fit): job
            for job in pending
        }
        for future in as_completed(futures):
            result = future.result()
            results[result["job_id"]] = result
    ordered = [results[job["job_id"]] for job in jobs]
    completed = {
        "schema": "CatBoostCPUBatchResults.v1",
        "batch_sha256": canonical_hash(payload),
        "bundle_sha256": manifest["bundle_sha256"],
        "worker_sha256": sha256_file(Path(__file__)),
        "hostname": socket.gethostname(),
        "workers": workers,
        "threads_per_fit": threads_per_fit,
        "results": ordered,
        "test_labels_used": False,
    }
    atomic_json(output / "results.json", completed)
    return completed


def smoke(threads: int) -> dict[str, Any]:
    from catboost import CatBoostRegressor

    if importlib.metadata.version("catboost") != CATBOOST_VERSION:
        raise ValueError(f"CatBoost {CATBOOST_VERSION} is required")
    rng = np.random.default_rng(4219)
    features = rng.normal(size=(64, 8)).astype(np.float32)
    target = rng.normal(size=64)
    model = CatBoostRegressor(
        **MODEL_PARAMETERS, iterations=2, random_seed=4219, thread_count=threads
    )
    model.fit(features, target, verbose=False)
    prediction = model.predict(features[:4])
    if not np.isfinite(prediction).all():
        raise ValueError("CPU smoke produced nonfinite predictions")
    return {"ok": True, "catboost_version": CATBOOST_VERSION, "threads": threads}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--batch", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--threads-per-fit", type=int, default=8)
    arguments = parser.parse_args()
    if arguments.identity:
        result = environment_identity()
    elif arguments.verify_only:
        if arguments.bundle is None:
            parser.error("--bundle is required for --verify-only")
        result = verify_bundle(arguments.bundle)
    elif arguments.smoke:
        result = smoke(arguments.threads_per_fit)
    else:
        if arguments.bundle is None or arguments.batch is None or arguments.output is None:
            parser.error("--bundle, --batch, and --output are required")
        completed = run_batch(
            arguments.bundle,
            arguments.batch,
            arguments.output,
            workers=arguments.workers,
            threads_per_fit=arguments.threads_per_fit,
        )
        result = {
            "schema": completed["schema"],
            "hostname": completed["hostname"],
            "completed_jobs": len(completed["results"]),
            "bundle_sha256": completed["bundle_sha256"],
            "worker_sha256": completed["worker_sha256"],
            "test_labels_used": False,
        }
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
