from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np


def _gpu_identity() -> dict[str, str]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,uuid,driver_version",
        "--format=csv,noheader",
    ]
    try:
        value = subprocess.check_output(command, text=True, timeout=15).strip()
    except (OSError, subprocess.SubprocessError):
        value = "unavailable"
    return {"nvidia_smi": value}


def run(input_path: Path, output_path: Path) -> None:
    from catboost import CatBoostRegressor, __version__ as catboost_version

    with np.load(input_path, allow_pickle=False) as job:
        train = job["train"]
        target = job["target"]
        training = job["training_mask"].astype(bool, copy=False)
        validation = job["validation_mask"].astype(bool, copy=False)
        iterations = int(job["iterations"])
        seed = int(job["seed"])
    if train.ndim != 2 or target.shape != (train.shape[0],):
        raise ValueError("invalid train or target shape")
    if training.shape != target.shape or validation.shape != target.shape:
        raise ValueError("invalid fold-mask shape")
    if np.any(training & validation) or not training.any() or not validation.any():
        raise ValueError("training and validation masks must be nonempty and disjoint")

    model = CatBoostRegressor(
        loss_function="RMSE",
        depth=7,
        learning_rate=0.05,
        task_type="GPU",
        devices="0",
        iterations=iterations,
        random_seed=seed,
        allow_writing_files=False,
        verbose=False,
    )
    model.fit(train[training], np.log1p(target[training]), verbose=False)
    prediction = np.clip(np.expm1(model.predict(train[validation])), 0.0, None)
    importance = np.asarray(model.get_feature_importance(type="PredictionValuesChange"))
    metadata = {
        "catboost_version": catboost_version,
        "numpy_version": np.__version__,
        **_gpu_identity(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        prediction=prediction,
        importance=importance,
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.input, arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
