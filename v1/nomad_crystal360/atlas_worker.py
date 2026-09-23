from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import numpy as np


MINIMUM_FREE_MIB = 20 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _native_distribution_hash(distribution_name: str) -> str:
    distribution = importlib.metadata.distribution(distribution_name)
    digest = hashlib.sha256()
    for item in sorted(distribution.files or [], key=str):
        if not str(item).endswith((".so", ".dll", ".dylib")):
            continue
        path = Path(distribution.locate_file(item))
        if path.is_file():
            digest.update(str(item).encode("utf-8"))
            digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def environment_identity() -> dict[str, Any]:
    packages = ("catboost", "xgboost", "lightgbm", "numpy", "pandas", "scikit-learn")
    identity = {
        "python": sys.version,
        "executable": sys.executable,
        "packages": {name: importlib.metadata.version(name) for name in packages},
        "native_hashes": {
            name: _native_distribution_hash(name) for name in ("catboost", "xgboost", "lightgbm")
        },
    }
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    identity["sha256"] = hashlib.sha256(payload).hexdigest()
    return identity


def _gpu_free_mib() -> int:
    completed = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=memory.free",
            "--format=csv,noheader,nounits",
            "--id=0",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return int(completed.stdout.strip().splitlines()[0])


@contextmanager
def gpu_lease(path: Path = Path("/tmp/nomad_crystalatlas_gpu0.lease")) -> Iterator[None]:
    token = f"{os.getpid()}:{uuid.uuid4().hex}"
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise RuntimeError(f"GPU 0 already has an exclusive CrystalAtlas lease: {path}") from error
    try:
        os.write(descriptor, token.encode("ascii"))
        os.close(descriptor)
        free_mib = _gpu_free_mib()
        if free_mib < MINIMUM_FREE_MIB:
            raise RuntimeError(
                f"GPU 0 has {free_mib} MiB free; at least {MINIMUM_FREE_MIB} MiB is required"
            )
        yield
    finally:
        try:
            if path.read_text(encoding="ascii") == token:
                path.unlink()
        except FileNotFoundError:
            pass


def _verify_bundle(bundle: Path) -> dict[str, Any]:
    manifest = json.loads((bundle / "bundle_manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        path = bundle / name
        actual = sha256_file(path)
        if actual != expected["sha256"]:
            raise ValueError(f"Bundle hash mismatch for {name}: {actual} != {expected['sha256']}")
    if manifest.get("contains_test_targets") is not False:
        raise ValueError("Bundle must explicitly attest that it contains no test targets")
    return manifest


def _rmsle(y_true: np.ndarray, prediction: np.ndarray) -> float:
    prediction = np.clip(np.asarray(prediction, dtype=float), 0.0, None)
    return float(np.sqrt(np.mean((np.log1p(y_true) - np.log1p(prediction)) ** 2)))


def _load_job_data(bundle: Path, job: dict[str, Any]) -> dict[str, Any]:
    matrix = np.load(bundle / "train.npy", mmap_mode="r")
    columns = np.asarray(job["columns"], dtype=int)
    if columns.size == 0 or columns.min() < 0 or columns.max() >= matrix.shape[1]:
        raise ValueError("Job has an empty or out-of-range genome")
    target_names = json.loads((bundle / "targets.json").read_text(encoding="utf-8"))
    target_index = target_names.index(job["target"])
    targets = np.load(bundle / "targets.npy", mmap_mode="r")[:, target_index]
    folds = np.load(bundle / "folds.npz")
    assignment = folds[job["fold_scheme"]]
    validation = assignment == int(job["fold"])
    training = ~validation
    return {
        "matrix": matrix,
        "columns": columns,
        "targets": np.asarray(targets),
        "training": training,
        "validation": validation,
    }


def _catboost_job(bundle: Path, job: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    from catboost import CatBoostRegressor, Pool

    matrix, columns = data["matrix"], data["columns"]
    training, validation, target = data["training"], data["validation"], data["targets"]
    x_train = np.asarray(matrix[training][:, columns], dtype=np.float32)
    x_validation = np.asarray(matrix[validation][:, columns], dtype=np.float32)
    y_train = np.log1p(target[training])
    y_validation = np.log1p(target[validation])
    parameters = {
        "loss_function": "RMSE",
        "eval_metric": "RMSE",
        "iterations": int(job.get("iterations", 200)),
        "learning_rate": float(job.get("learning_rate", 0.05)),
        "depth": int(job.get("depth", 7)),
        "l2_leaf_reg": float(job.get("l2_leaf_reg", 5.0)),
        "random_seed": int(job.get("seed", 1701)),
        "task_type": "GPU",
        "devices": "0",
        "bootstrap_type": "Bayesian",
        "bagging_temperature": 0.5,
        "random_strength": 0.5,
        "allow_writing_files": False,
        "verbose": False,
    }
    model = CatBoostRegressor(**parameters)
    train_pool = Pool(x_train, y_train)
    validation_pool = Pool(x_validation, y_validation)
    model.fit(
        train_pool,
        eval_set=validation_pool,
        early_stopping_rounds=int(job.get("early_stopping_rounds", 50)),
        verbose=False,
    )
    validation_prediction = np.clip(np.expm1(model.predict(validation_pool)), 0.0, None)
    result: dict[str, Any] = {
        "score": _rmsle(target[validation], validation_prediction),
        "best_iteration": int(model.get_best_iteration()),
        "validation_rows": int(validation.sum()),
    }
    if job.get("return_importance"):
        result["importance"] = model.get_feature_importance(
            validation_pool, type="LossFunctionChange"
        ).astype(float).tolist()
    if job.get("predict"):
        test = np.load(bundle / "test.npy", mmap_mode="r")
        test_prediction = np.clip(
            np.expm1(model.predict(np.asarray(test[:, columns], dtype=np.float32))), 0.0, None
        )
        result["validation_indices"] = np.flatnonzero(validation).astype(int).tolist()
        result["validation_predictions"] = validation_prediction.astype(float).tolist()
        result["test_predictions"] = test_prediction.astype(float).tolist()
    return result


def _xgboost_job(bundle: Path, job: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    from xgboost import XGBRegressor

    matrix, columns = data["matrix"], data["columns"]
    training, validation, target = data["training"], data["validation"], data["targets"]
    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=int(job.get("iterations", 800)),
        learning_rate=float(job.get("learning_rate", 0.03)),
        max_depth=int(job.get("depth", 7)),
        min_child_weight=2.0,
        subsample=0.85,
        colsample_bytree=0.8,
        reg_lambda=float(job.get("l2_leaf_reg", 5.0)),
        tree_method="hist",
        device="cuda:0",
        random_state=int(job.get("seed", 1701)),
        early_stopping_rounds=int(job.get("early_stopping_rounds", 50)),
    )
    model.fit(
        np.asarray(matrix[training][:, columns], dtype=np.float32),
        np.log1p(target[training]),
        eval_set=[
            (
                np.asarray(matrix[validation][:, columns], dtype=np.float32),
                np.log1p(target[validation]),
            )
        ],
        verbose=False,
    )
    validation_prediction = np.clip(
        np.expm1(model.predict(np.asarray(matrix[validation][:, columns], dtype=np.float32))),
        0.0,
        None,
    )
    test = np.load(bundle / "test.npy", mmap_mode="r")
    test_prediction = np.clip(
        np.expm1(model.predict(np.asarray(test[:, columns], dtype=np.float32))), 0.0, None
    )
    return {
        "score": _rmsle(target[validation], validation_prediction),
        "best_iteration": int(getattr(model, "best_iteration", job.get("iterations", 800))),
        "validation_rows": int(validation.sum()),
        "validation_indices": np.flatnonzero(validation).astype(int).tolist(),
        "validation_predictions": validation_prediction.astype(float).tolist(),
        "test_predictions": test_prediction.astype(float).tolist(),
    }


def _lightgbm_job(bundle: Path, job: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    from lightgbm import LGBMRegressor, early_stopping

    matrix, columns = data["matrix"], data["columns"]
    training, validation, target = data["training"], data["validation"], data["targets"]
    model = LGBMRegressor(
        objective="regression",
        n_estimators=int(job.get("iterations", 800)),
        learning_rate=float(job.get("learning_rate", 0.03)),
        num_leaves=63,
        max_depth=int(job.get("depth", -1)),
        min_child_samples=15,
        subsample=0.85,
        colsample_bytree=0.8,
        reg_lambda=float(job.get("l2_leaf_reg", 5.0)),
        random_state=int(job.get("seed", 1701)),
        n_jobs=int(job.get("cpu_jobs", 24)),
        verbosity=-1,
    )
    model.fit(
        np.asarray(matrix[training][:, columns], dtype=np.float32),
        np.log1p(target[training]),
        eval_set=[
            (
                np.asarray(matrix[validation][:, columns], dtype=np.float32),
                np.log1p(target[validation]),
            )
        ],
        callbacks=[early_stopping(int(job.get("early_stopping_rounds", 50)), verbose=False)],
    )
    validation_prediction = np.clip(
        np.expm1(model.predict(np.asarray(matrix[validation][:, columns], dtype=np.float32))),
        0.0,
        None,
    )
    test = np.load(bundle / "test.npy", mmap_mode="r")
    test_prediction = np.clip(
        np.expm1(model.predict(np.asarray(test[:, columns], dtype=np.float32))), 0.0, None
    )
    return {
        "score": _rmsle(target[validation], validation_prediction),
        "best_iteration": int(model.best_iteration_),
        "validation_rows": int(validation.sum()),
        "validation_indices": np.flatnonzero(validation).astype(int).tolist(),
        "validation_predictions": validation_prediction.astype(float).tolist(),
        "test_predictions": test_prediction.astype(float).tolist(),
    }


def run_job(bundle: Path, job: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    bundle_manifest = _verify_bundle(bundle)
    data = _load_job_data(bundle, job)
    model_type = job.get("model", "catboost")
    if model_type == "lightgbm":
        result = _lightgbm_job(bundle, job, data)
    else:
        with gpu_lease():
            if model_type == "catboost":
                result = _catboost_job(bundle, job, data)
            elif model_type == "xgboost":
                result = _xgboost_job(bundle, job, data)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
    result.update(
        {
            "status": "completed",
            "elapsed_seconds": time.monotonic() - started,
            "bundle_sha256": bundle_manifest["bundle_sha256"],
            "environment_sha256": environment_identity()["sha256"],
        }
    )
    return result
