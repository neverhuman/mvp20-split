#!/usr/bin/env python3
"""Self-contained CatBoost GPU worker for the Atlas/Hyperion bake-off."""
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


MODEL_PARAMETERS = {
    "loss_function": "RMSE",
    "depth": 7,
    "learning_rate": 0.05,
    "task_type": "GPU",
    "devices": "0",
    "allow_writing_files": False,
    "verbose": False,
}
IMPORTANCE_TOLERANCE = 1e-12


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(data).hexdigest()


def gpu_status() -> dict[str, Any]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
        "--id=0",
    ]
    output = subprocess.check_output(command, text=True, timeout=15).strip().splitlines()[0]
    name, driver, total, used, free, utilization = [part.strip() for part in output.split(",")]
    return {
        "name": name,
        "driver": driver,
        "total_mib": int(float(total)),
        "used_mib": int(float(used)),
        "free_mib": int(float(free)),
        "utilization_percent": int(float(utilization)),
    }


def environment_identity() -> dict[str, Any]:
    packages = ("catboost", "numpy", "pandas", "scikit-learn")
    gpu = gpu_status()
    identity = {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "packages": {name: importlib.metadata.version(name) for name in packages},
        "worker_sha256": sha256_file(Path(__file__)),
        "gpu": gpu,
    }
    stable_identity = {
        **identity,
        "gpu": {
            key: gpu[key] for key in ("name", "driver", "total_mib")
        },
    }
    identity["sha256"] = canonical_hash(stable_identity)
    return identity


def verify_bundle(bundle: Path) -> dict[str, Any]:
    manifest_path = bundle / "bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contains_test_targets") is not False:
        raise ValueError("Worker bundle contains or does not exclude test targets")
    if manifest.get("test_labels_used") is not False:
        raise ValueError("Worker bundle does not attest public-only selection")
    forbidden = [name for name in manifest["files"] if "test_target" in name.lower()]
    if forbidden:
        raise ValueError(f"Worker bundle lists forbidden test targets: {forbidden}")
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
        raise ValueError("Worker bundle identity hash is inconsistent")
    marker = bundle / f".verified-{manifest['bundle_sha256']}.json"
    current_stats = {
        name: {
            "bytes": (bundle / name).stat().st_size,
            "mtime_ns": (bundle / name).stat().st_mtime_ns,
        }
        for name in manifest["files"]
    }
    if marker.exists():
        cached = json.loads(marker.read_text(encoding="utf-8"))
        if cached.get("stats") == current_stats:
            return manifest
    for name, metadata in manifest["files"].items():
        if sha256_file(bundle / name) != metadata["sha256"]:
            raise ValueError(f"Worker bundle hash mismatch for {name}")
    temporary = marker.with_suffix(".tmp")
    temporary.write_text(json.dumps({"stats": current_stats}, sort_keys=True) + "\n")
    os.replace(temporary, marker)
    return manifest


@contextmanager
def gpu_lease(device: str = "0") -> Iterator[None]:
    path = Path(f"/tmp/atlas-hyperion-bakeoff-gpu{device}.lock")
    with path.open("a+", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(f"GPU {device} already has an exclusive bake-off worker") from error
        yield


def normalize_importance(values: Sequence[float]) -> np.ndarray:
    importance = np.asarray(values, dtype=np.float64)
    if importance.shape != (300,):
        raise ValueError(f"Expected 300 PredictionValuesChange values, found {importance.shape}")
    if not np.isfinite(importance).all() or np.any(importance < 0.0):
        raise ValueError("PredictionValuesChange must be finite and nonnegative")
    total = float(importance.sum())
    if total <= 0.0:
        raise ValueError("PredictionValuesChange has zero total")
    importance /= total
    if not math.isclose(
        float(importance.sum()), 1.0, rel_tol=IMPORTANCE_TOLERANCE, abs_tol=IMPORTANCE_TOLERANCE
    ):
        raise AssertionError("Normalized PredictionValuesChange does not sum to one")
    return importance


def rmsle(target: np.ndarray, prediction: np.ndarray) -> float:
    prediction = np.clip(np.asarray(prediction, dtype=np.float64), 0.0, None)
    return float(
        np.sqrt(np.mean((np.log1p(np.asarray(target, dtype=np.float64)) - np.log1p(prediction)) ** 2))
    )


def _load_data(bundle: Path, job: dict[str, Any]) -> dict[str, Any]:
    train = np.load(bundle / "train.npy", mmap_mode="r", allow_pickle=False)
    columns = np.asarray(job["columns"], dtype=np.int64)
    if columns.ndim != 1 or columns.size == 0:
        raise ValueError("Model job has no columns")
    if len(np.unique(columns)) != len(columns):
        raise ValueError("Model job contains duplicate columns")
    if int(columns.min()) < 0 or int(columns.max()) >= train.shape[1]:
        raise ValueError("Model job contains an out-of-range column")
    target_names = json.loads((bundle / "targets.json").read_text(encoding="utf-8"))
    target_index = target_names.index(job["target"])
    targets = np.load(bundle / "targets.npy", mmap_mode="r", allow_pickle=False)
    target = targets[:, target_index]
    fold_name = "selection_folds.npy" if job["kind"] in {"importance", "screen"} else "confirmation_folds.npy"
    folds = np.load(bundle / fold_name, mmap_mode="r", allow_pickle=False)
    validation = folds == int(job["fold"])
    training = ~validation
    if not training.any() or not validation.any():
        raise ValueError("Model job fold has empty training or validation rows")
    return {
        "train": train,
        "columns": columns,
        "target": target,
        "training": training,
        "validation": validation,
    }


def _model(job: dict[str, Any]):
    from catboost import CatBoostRegressor

    return CatBoostRegressor(
        **MODEL_PARAMETERS,
        iterations=int(job["iterations"]),
        random_seed=int(job["seed"]),
    )


def execute_job(bundle: Path, job: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    manifest = verify_bundle(bundle)
    data = _load_data(bundle, job)
    columns = data["columns"]
    training = data["training"]
    validation = data["validation"]
    target = data["target"]
    x_train = np.asarray(data["train"][training][:, columns], dtype=np.float32)
    y_train = np.log1p(np.asarray(target[training], dtype=np.float64))
    with gpu_lease(MODEL_PARAMETERS["devices"]):
        model = _model(job)
        # Fixed-tree fits intentionally have no eval_set or early stopping.
        model.fit(x_train, y_train, verbose=False)
        if job["kind"] == "importance":
            if len(columns) != 300:
                raise ValueError("Every importance fit must receive exactly 300 columns")
            importance = normalize_importance(
                model.get_feature_importance(type="PredictionValuesChange")
            )
            result: dict[str, Any] = {
                "importance": importance.tolist(),
                "importance_sum": float(importance.sum()),
                "training_rows": int(training.sum()),
            }
        else:
            x_validation = np.asarray(data["train"][validation][:, columns], dtype=np.float32)
            validation_prediction = np.clip(np.expm1(model.predict(x_validation)), 0.0, None)
            result = {
                "score": rmsle(target[validation], validation_prediction),
                "training_rows": int(training.sum()),
                "validation_rows": int(validation.sum()),
            }
            if job["kind"] == "final":
                test = np.load(bundle / "test.npy", mmap_mode="r", allow_pickle=False)
                test_prediction = np.clip(
                    np.expm1(model.predict(np.asarray(test[:, columns], dtype=np.float32))),
                    0.0,
                    None,
                )
                result.update(
                    {
                        "validation_indices": np.flatnonzero(validation).astype(int).tolist(),
                        "validation_predictions": validation_prediction.astype(float).tolist(),
                        "test_predictions": test_prediction.astype(float).tolist(),
                    }
                )
    result.update(
        {
            "status": "completed",
            "job_id": job["job_id"],
            "elapsed_seconds": time.monotonic() - started,
            "bundle_sha256": manifest["bundle_sha256"],
        }
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--job-base64")
    args = parser.parse_args()
    if args.identity:
        print(json.dumps(environment_identity(), separators=(",", ":"), allow_nan=False))
        return
    if args.bundle is None:
        parser.error("--bundle is required")
    if args.verify_only:
        print(json.dumps(verify_bundle(args.bundle), separators=(",", ":"), allow_nan=False))
        return
    if not args.job_base64:
        parser.error("--job-base64 is required for a model job")
    job = json.loads(base64.b64decode(args.job_base64).decode("utf-8"))
    print(json.dumps(execute_job(args.bundle, job), separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
