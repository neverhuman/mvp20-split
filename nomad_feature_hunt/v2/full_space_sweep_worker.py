#!/usr/bin/env python3
"""Pinned CatBoost GPU worker for the full-space feature sweep."""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Iterator, Sequence

import numpy as np
from sklearn.model_selection import KFold


CATBOOST_VERSION = "1.2.10"
MODEL_PARAMETERS = {
    "loss_function": "RMSE",
    "depth": 7,
    "learning_rate": 0.05,
    "task_type": "GPU",
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


def gpu_status(device: str) -> dict[str, Any]:
    command = [
        "nvidia-smi",
        "--query-gpu=index,name,uuid,driver_version,memory.total,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
        f"--id={device}",
    ]
    output = subprocess.check_output(command, text=True, timeout=15).strip().splitlines()[0]
    index, name, uuid, driver, total, used, utilization = (
        item.strip() for item in output.split(",")
    )
    return {
        "index": int(index),
        "name": name,
        "uuid": uuid,
        "driver": driver,
        "total_mib": int(float(total)),
        "used_mib": int(float(used)),
        "utilization_percent": int(float(utilization)),
    }


def environment_identity(device: str) -> dict[str, Any]:
    packages = ("catboost", "numpy", "pandas", "scikit-learn")
    gpu = gpu_status(device)
    identity = {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "packages": {name: importlib.metadata.version(name) for name in packages},
        "worker_sha256": sha256_file(Path(__file__)),
        "gpu": gpu,
    }
    stable = {
        **identity,
        "gpu": {key: gpu[key] for key in ("name", "uuid", "driver", "total_mib")},
    }
    identity["sha256"] = canonical_hash(stable)
    return identity


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
    marker = bundle / f".verified-{manifest['bundle_sha256']}.json"
    stats = {
        name: {
            "bytes": (bundle / name).stat().st_size,
            "mtime_ns": (bundle / name).stat().st_mtime_ns,
        }
        for name in manifest["files"]
    }
    if marker.exists():
        cached = json.loads(marker.read_text(encoding="utf-8"))
        if cached.get("stats") == stats:
            return manifest
    for name, metadata in manifest["files"].items():
        if sha256_file(bundle / name) != metadata["sha256"]:
            raise ValueError(f"bundle hash mismatch for {name}")
    temporary = marker.with_suffix(".tmp")
    temporary.write_text(json.dumps({"stats": stats}, sort_keys=True) + "\n")
    os.replace(temporary, marker)
    return manifest


@contextmanager
def gpu_lease(device: str) -> Iterator[None]:
    path = Path(f"/tmp/nomad-full-space-sweep-gpu{device}.lock")
    with path.open("a+", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(f"GPU {device} already has a full-space worker") from error
        yield


def normalize_importance(values: Sequence[float], expected_width: int) -> np.ndarray:
    importance = np.asarray(values, dtype=np.float64)
    if importance.shape != (expected_width,):
        raise ValueError(
            f"expected {expected_width} PredictionValuesChange values, found {importance.shape}"
        )
    if not np.isfinite(importance).all() or np.any(importance < 0.0):
        raise ValueError("PredictionValuesChange must be finite and nonnegative")
    total = float(importance.sum())
    if total <= 0.0:
        raise ValueError("PredictionValuesChange has zero total")
    importance /= total
    if not math.isclose(float(importance.sum()), 1.0, rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError("normalized importance does not sum to one")
    return importance


def rmsle(target: np.ndarray, prediction: np.ndarray) -> float:
    prediction = np.clip(np.asarray(prediction, dtype=np.float64), 0.0, None)
    truth = np.asarray(target, dtype=np.float64)
    return float(np.sqrt(np.mean((np.log1p(truth) - np.log1p(prediction)) ** 2)))


def fold_masks(rows: int, seed: int, fold: int) -> tuple[np.ndarray, np.ndarray]:
    if fold not in range(5):
        raise ValueError("fold must be in [0, 5)")
    validation_indices = list(KFold(5, shuffle=True, random_state=seed).split(np.arange(rows)))[
        fold
    ][1]
    validation = np.zeros(rows, dtype=bool)
    validation[validation_indices] = True
    return ~validation, validation


def _load_job(bundle: Path, job: dict[str, Any]) -> dict[str, Any]:
    train = np.load(bundle / "train.npy", mmap_mode="r", allow_pickle=False)
    targets = np.load(bundle / "targets.npy", mmap_mode="r", allow_pickle=False)
    target_names = json.loads((bundle / "targets.json").read_text(encoding="utf-8"))
    columns = np.asarray(job["columns"], dtype=np.int64)
    if columns.ndim != 1 or columns.size == 0 or len(np.unique(columns)) != len(columns):
        raise ValueError("job columns must be a nonempty unique vector")
    if int(columns.min()) < 0 or int(columns.max()) >= train.shape[1]:
        raise ValueError("job contains an out-of-range column")
    target_index = target_names.index(job["target"])
    target = np.asarray(targets[:, target_index], dtype=np.float64)
    training, validation = fold_masks(len(train), int(job["cv_seed"]), int(job["fold"]))
    return {
        "train": train,
        "columns": columns,
        "target": target,
        "training": training,
        "validation": validation,
    }


def _model(job: dict[str, Any], device: str):
    from catboost import CatBoostRegressor

    return CatBoostRegressor(
        **MODEL_PARAMETERS,
        devices=device,
        iterations=int(job["iterations"]),
        random_seed=int(job["model_seed"]),
    )


def execute_job(bundle: Path, job: dict[str, Any], device: str) -> dict[str, Any]:
    started = time.monotonic()
    manifest = verify_bundle(bundle)
    data = _load_job(bundle, job)
    columns = data["columns"]
    training = data["training"]
    validation = data["validation"]
    target = data["target"]
    x_training = np.asarray(data["train"][training][:, columns], dtype=np.float32)
    with gpu_lease(device):
        model = _model(job, device)
        model.fit(x_training, np.log1p(target[training]), verbose=False)
        if job["kind"] == "importance":
            expected_width = int(job["chunk_width"])
            if len(columns) != expected_width:
                raise ValueError("importance job does not have the fixed chunk width")
            importance = normalize_importance(
                model.get_feature_importance(type="PredictionValuesChange"), expected_width
            )
            result: dict[str, Any] = {
                "importance": importance.tolist(),
                "importance_sum": float(importance.sum()),
                "training_rows": int(training.sum()),
            }
        else:
            x_validation = np.asarray(
                data["train"][validation][:, columns], dtype=np.float32
            )
            prediction = np.clip(np.expm1(model.predict(x_validation)), 0.0, None)
            result = {
                "score": rmsle(target[validation], prediction),
                "training_rows": int(training.sum()),
                "validation_rows": int(validation.sum()),
            }
    result.update(
        {
            "status": "completed",
            "job_id": job["job_id"],
            "elapsed_seconds": time.monotonic() - started,
            "bundle_sha256": manifest["bundle_sha256"],
            "catboost_version": importlib.metadata.version("catboost"),
            "device": device,
        }
    )
    return result


def smoke(device: str) -> dict[str, Any]:
    from catboost import CatBoostRegressor

    if importlib.metadata.version("catboost") != CATBOOST_VERSION:
        raise ValueError(f"CatBoost {CATBOOST_VERSION} is required")
    rng = np.random.default_rng(4219)
    features = rng.normal(size=(64, 8)).astype(np.float32)
    target = rng.normal(size=64)
    with gpu_lease(device):
        model = CatBoostRegressor(
            **MODEL_PARAMETERS, devices=device, iterations=2, random_seed=4219
        )
        model.fit(features, target, verbose=False)
        prediction = model.predict(features[:4])
    if not np.isfinite(prediction).all():
        raise ValueError("GPU smoke produced nonfinite predictions")
    return {"ok": True, "catboost_version": CATBOOST_VERSION, "gpu": gpu_status(device)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--device", default="0")
    parser.add_argument("--identity", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--job-base64")
    args = parser.parse_args()
    if args.identity:
        print(json.dumps(environment_identity(args.device), separators=(",", ":")))
        return
    if args.smoke:
        print(json.dumps(smoke(args.device), separators=(",", ":")))
        return
    if args.bundle is None:
        parser.error("--bundle is required")
    if args.verify_only:
        print(json.dumps(verify_bundle(args.bundle), separators=(",", ":")))
        return
    if not args.job_base64:
        parser.error("--job-base64 is required")
    job = json.loads(base64.b64decode(args.job_base64).decode("utf-8"))
    print(
        json.dumps(
            execute_job(args.bundle, job, args.device),
            separators=(",", ":"),
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
