from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from .constants import (
    ATLAS_TARGET_WINNERS,
    CONFIRM_TREES,
    EXISTING_809_CONTROLS,
    SCREEN_SEEDS,
    SCREEN_TREES,
    TARGETS,
    TEST_ROWS,
    TRAIN_ROWS,
)
from .ledger import HashChain, atomic_json, sha256_file, utc_now


class MatrixValidationError(ValueError):
    pass


class GPUScoringError(RuntimeError):
    pass


@dataclass(frozen=True)
class GPUFitJob:
    train: np.ndarray
    target: np.ndarray
    training_mask: np.ndarray
    validation_mask: np.ndarray
    iterations: int
    seed: int


class DualGPUExecutor:
    """Run at most one CatBoost process on each campaign GPU."""

    HOSTS = ("local", "xbabe1")
    REMOTE_TMP_ROOT = "/home/ubuntu/nomad/tmp"

    def __init__(self, receipt_dir: Path) -> None:
        self.receipt_dir = receipt_dir
        self.receipt_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir = self.receipt_dir / "work"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.events = HashChain(self.receipt_dir / "events.jsonl")
        self.worker = Path(__file__).with_name("gpu_fit_worker.py")
        self.worker_sha256 = sha256_file(self.worker)
        self.dispatcher_sha256 = sha256_file(Path(__file__))
        self._locks = {host: threading.Lock() for host in self.HOSTS}
        self._event_lock = threading.Lock()
        self._counter_lock = threading.Lock()
        self._counter = 0

    def _record(self, event: str, receipt: dict[str, Any]) -> None:
        with self._event_lock:
            self.events.append(event, receipt)

    def _next_job_id(self) -> str:
        with self._counter_lock:
            self._counter += 1
            return f"gpu-fit-{self._counter:06d}"

    def _execute(
        self, job_id: str, job: GPUFitJob, host: str, attempt: int
    ) -> tuple[np.ndarray, np.ndarray]:
        with self._locks[host], tempfile.TemporaryDirectory(
            prefix="nomad-gpu-fit-", dir=self.work_dir
        ) as temporary:
            temporary_path = Path(temporary)
            input_path = temporary_path / "input.npz"
            output_path = temporary_path / "output.npz"
            np.savez_compressed(
                input_path,
                train=np.asarray(job.train, dtype=np.float32),
                target=np.asarray(job.target, dtype=np.float64),
                training_mask=np.asarray(job.training_mask, dtype=bool),
                validation_mask=np.asarray(job.validation_mask, dtype=bool),
                iterations=np.asarray(job.iterations),
                seed=np.asarray(job.seed),
            )
            started_at = utc_now()
            remote_dir: str | None = None
            try:
                if host == "local":
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(self.worker),
                            "--input",
                            str(input_path),
                            "--output",
                            str(output_path),
                        ],
                        text=True,
                        capture_output=True,
                        timeout=7_200,
                        check=False,
                    )
                else:
                    remote_dir = (
                        f"{self.REMOTE_TMP_ROOT}/nomad-feature-hunt-{uuid.uuid4().hex}"
                    )
                    if not re.fullmatch(
                        r"/home/ubuntu/nomad/tmp/nomad-feature-hunt-[a-f0-9]{32}",
                        remote_dir,
                    ):
                        raise GPUScoringError("refusing unsafe remote staging path")
                    result = subprocess.run(
                        ["ssh", host, "mkdir", "-p", self.REMOTE_TMP_ROOT],
                        text=True,
                        capture_output=True,
                        timeout=60,
                        check=False,
                    )
                    if result.returncode == 0:
                        result = subprocess.run(
                            ["ssh", host, "mkdir", "-m", "700", remote_dir],
                            text=True,
                            capture_output=True,
                            timeout=60,
                            check=False,
                        )
                    if result.returncode == 0:
                        result = subprocess.run(
                            [
                                "scp",
                                str(self.worker),
                                str(input_path),
                                f"{host}:{remote_dir}/",
                            ],
                            text=True,
                            capture_output=True,
                            timeout=1_800,
                            check=False,
                        )
                    if result.returncode == 0:
                        result = subprocess.run(
                            [
                                "ssh",
                                host,
                                "/usr/bin/python3",
                                f"{remote_dir}/{self.worker.name}",
                                "--input",
                                f"{remote_dir}/input.npz",
                                "--output",
                                f"{remote_dir}/output.npz",
                            ],
                            text=True,
                            capture_output=True,
                            timeout=7_200,
                            check=False,
                        )
                    if result.returncode == 0:
                        result = subprocess.run(
                            [
                                "scp",
                                f"{host}:{remote_dir}/output.npz",
                                str(output_path),
                            ],
                            text=True,
                            capture_output=True,
                            timeout=1_800,
                            check=False,
                        )
                receipt: dict[str, Any] = {
                    "job_id": job_id,
                    "attempt": attempt,
                    "host": host,
                    "started_at": started_at,
                    "finished_at": utc_now(),
                    "returncode": result.returncode,
                    "input_sha256": sha256_file(input_path),
                    "worker_sha256": self.worker_sha256,
                    "dispatcher_sha256": self.dispatcher_sha256,
                    "cpu_fallback": False,
                }
                if result.returncode != 0 or not output_path.exists():
                    receipt["stderr_tail"] = result.stderr[-2_000:]
                    self._record("gpu_fit_failed", receipt)
                    raise GPUScoringError(
                        f"{job_id} failed on {host}: {result.stderr[-500:]}"
                    )
                with np.load(output_path, allow_pickle=False) as output:
                    prediction = np.asarray(output["prediction"], dtype=np.float64)
                    importance = np.asarray(output["importance"], dtype=np.float64)
                    receipt["environment"] = json.loads(str(output["metadata_json"]))
                receipt["output_sha256"] = sha256_file(output_path)
                self._record("gpu_fit_complete", receipt)
                return prediction, importance
            finally:
                if remote_dir is not None and re.fullmatch(
                    r"/home/ubuntu/nomad/tmp/nomad-feature-hunt-[a-f0-9]{32}",
                    remote_dir,
                ):
                    try:
                        subprocess.run(
                            ["ssh", host, "rm", "-rf", "--", remote_dir],
                            text=True,
                            capture_output=True,
                            timeout=60,
                            check=False,
                        )
                    except (OSError, subprocess.SubprocessError):
                        pass

    def fit(
        self, job: GPUFitJob, preferred_host: str
    ) -> tuple[np.ndarray, np.ndarray]:
        if preferred_host not in self.HOSTS:
            raise ValueError(f"unknown GPU host: {preferred_host}")
        job_id = self._next_job_id()
        alternate = next(host for host in self.HOSTS if host != preferred_host)
        errors: list[str] = []
        for attempt, host in enumerate((preferred_host, alternate), start=1):
            try:
                return self._execute(job_id, job, host, attempt)
            except (
                GPUScoringError,
                KeyError,
                OSError,
                ValueError,
                subprocess.SubprocessError,
            ) as error:
                errors.append(str(error))
                if not isinstance(error, GPUScoringError):
                    self._record(
                        "gpu_fit_failed",
                        {
                            "job_id": job_id,
                            "attempt": attempt,
                            "host": host,
                            "error": str(error),
                            "worker_sha256": self.worker_sha256,
                            "dispatcher_sha256": self.dispatcher_sha256,
                            "cpu_fallback": False,
                        },
                    )
        raise GPUScoringError(
            f"{job_id} failed on both GPU hosts; CPU fallback is forbidden: "
            + "; ".join(errors)
        )

    def fit_pair(
        self, first: GPUFitJob, second: GPUFitJob
    ) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
        with ThreadPoolExecutor(max_workers=2) as pool:
            local = pool.submit(self.fit, first, "local")
            remote = pool.submit(self.fit, second, "xbabe1")
            return local.result(), remote.result()


@dataclass(frozen=True)
class ValidatedMatrix:
    train: pd.DataFrame
    test: pd.DataFrame
    columns: tuple[str, ...]
    receipt: dict[str, Any]


def _read_matrix(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise MatrixValidationError(f"unsupported matrix format: {path}")


def _numeric_signature(values: np.ndarray, indices: np.ndarray) -> str:
    selected = np.ascontiguousarray(values[indices], dtype=np.float64)
    return hashlib.sha256(selected.tobytes()).hexdigest()


def _baseline_signature_map(
    train: np.ndarray, test: np.ndarray, train_indices: np.ndarray, test_indices: np.ndarray
) -> dict[str, list[int]]:
    signatures: dict[str, list[int]] = {}
    for index in range(train.shape[1]):
        digest = hashlib.sha256()
        digest.update(np.ascontiguousarray(train[train_indices, index], dtype=np.float64).tobytes())
        digest.update(np.ascontiguousarray(test[test_indices, index], dtype=np.float64).tobytes())
        signatures.setdefault(digest.hexdigest(), []).append(index)
    return signatures


def validate_matrix_pair(
    train_path: Path,
    test_path: Path,
    *,
    expected_train_ids: Sequence[int],
    expected_test_ids: Sequence[int],
    rerun_train_path: Path | None = None,
    rerun_test_path: Path | None = None,
    invariance_path: Path | None = None,
    baseline_train: np.ndarray | None = None,
    baseline_test: np.ndarray | None = None,
) -> ValidatedMatrix:
    train = _read_matrix(train_path)
    test = _read_matrix(test_path)
    if train.shape[0] != TRAIN_ROWS or test.shape[0] != TEST_ROWS:
        raise MatrixValidationError(
            f"expected {TRAIN_ROWS}/{TEST_ROWS} rows, found {len(train)}/{len(test)}"
        )
    if "id" not in train or "id" not in test:
        raise MatrixValidationError("both matrices must contain an id column")
    if train["id"].astype(int).tolist() != list(map(int, expected_train_ids)):
        raise MatrixValidationError("training row IDs are not aligned")
    if test["id"].astype(int).tolist() != list(map(int, expected_test_ids)):
        raise MatrixValidationError("test row IDs are not aligned")
    columns = [column for column in train.columns if column != "id"]
    if not columns or [column for column in test.columns if column != "id"] != columns:
        raise MatrixValidationError("train/test columns are empty or not identical and ordered")
    forbidden = set(TARGETS).intersection(columns)
    if forbidden:
        raise MatrixValidationError(f"matrix contains target columns: {sorted(forbidden)}")
    train_values = train[columns].to_numpy(dtype=np.float64)
    test_values = test[columns].to_numpy(dtype=np.float64)
    if not np.isfinite(train_values).all() or not np.isfinite(test_values).all():
        raise MatrixValidationError("matrix contains NaN or infinite values")
    variances = np.var(train_values, axis=0)
    constant = [columns[index] for index in np.flatnonzero(variances <= 0.0)]
    if constant:
        raise MatrixValidationError(f"constant training columns: {constant[:10]}")

    combined_hashes: dict[str, str] = {}
    seen: dict[str, str] = {}
    for index, column in enumerate(columns):
        digest = hashlib.sha256()
        digest.update(np.ascontiguousarray(train_values[:, index]).tobytes())
        digest.update(np.ascontiguousarray(test_values[:, index]).tobytes())
        column_hash = digest.hexdigest()
        if column_hash in seen:
            raise MatrixValidationError(
                f"exact duplicate candidate columns: {seen[column_hash]} and {column}"
            )
        seen[column_hash] = column
        combined_hashes[column] = column_hash

    rng = np.random.default_rng(4219)
    train_indices = np.sort(rng.choice(TRAIN_ROWS, 64, replace=False))
    test_indices = np.sort(rng.choice(TEST_ROWS, 64, replace=False))
    numeric_signatures: dict[str, str] = {}
    if baseline_train is not None or baseline_test is not None:
        if baseline_train is None or baseline_test is None:
            raise MatrixValidationError("both baseline matrices are required for deduplication")
        baseline_signatures = _baseline_signature_map(
            baseline_train, baseline_test, train_indices, test_indices
        )
        for index, column in enumerate(columns):
            digest = hashlib.sha256()
            digest.update(
                np.ascontiguousarray(train_values[train_indices, index], dtype=np.float64).tobytes()
            )
            digest.update(
                np.ascontiguousarray(test_values[test_indices, index], dtype=np.float64).tobytes()
            )
            signature = digest.hexdigest()
            numeric_signatures[column] = signature
            for baseline_index in baseline_signatures.get(signature, []):
                if np.array_equal(train_values[:, index], baseline_train[:, baseline_index]) and np.array_equal(
                    test_values[:, index], baseline_test[:, baseline_index]
                ):
                    raise MatrixValidationError(
                        f"candidate column {column} exactly duplicates Atlas column {baseline_index}"
                    )

    deterministic = False
    if rerun_train_path is not None and rerun_test_path is not None:
        rerun_train = _read_matrix(rerun_train_path)
        rerun_test = _read_matrix(rerun_test_path)
        deterministic = train.equals(rerun_train) and test.equals(rerun_test)
        if not deterministic:
            raise MatrixValidationError("generator rerun is not deterministic")
    else:
        raise MatrixValidationError("deterministic rerun matrices are required")

    invariance: dict[str, Any] = {}
    required_invariances = {
        "translation",
        "rotation",
        "atom_permutation",
        "periodic_wrapping",
        "equivalent_cell",
    }
    if invariance_path is None or not invariance_path.exists():
        raise MatrixValidationError("trusted invariance receipt is required")
    invariance = json.loads(invariance_path.read_text(encoding="utf-8"))
    missing = sorted(name for name in required_invariances if invariance.get(name) is not True)
    if missing:
        raise MatrixValidationError(f"invariance tests did not pass: {missing}")

    receipt = {
        "train_path": str(train_path),
        "test_path": str(test_path),
        "train_sha256": sha256_file(train_path),
        "test_sha256": sha256_file(test_path),
        "rows": {"train": len(train), "test": len(test)},
        "columns": columns,
        "value_sha256": combined_hashes,
        "numeric_signatures_64": numeric_signatures,
        "deterministic_rerun": deterministic,
        "invariance": invariance,
        "no_targets_in_matrix": True,
        "finite": True,
        "nonconstant": True,
    }
    return ValidatedMatrix(train, test, tuple(columns), receipt)


def rmsle(target: np.ndarray, prediction: np.ndarray) -> float:
    prediction = np.clip(np.asarray(prediction, dtype=np.float64), 0.0, None)
    return float(
        np.sqrt(np.mean((np.log1p(target) - np.log1p(prediction)) ** 2))
    )


def _residual_statistics(
    candidate: np.ndarray, target: np.ndarray, baseline_prediction: np.ndarray
) -> dict[str, float]:
    from scipy.stats import pearsonr, spearmanr
    from sklearn.feature_selection import mutual_info_regression

    residual = target - baseline_prediction
    pearsons: list[float] = []
    spearmans: list[float] = []
    mis: list[float] = []
    for index in range(candidate.shape[1]):
        values = candidate[:, index]
        pearsons.append(abs(float(pearsonr(values, residual).statistic)))
        spearmans.append(abs(float(spearmanr(values, residual).statistic)))
        mis.append(float(mutual_info_regression(values[:, None], residual, random_state=4219)[0]))
    return {
        "max_abs_residual_pearson": max(pearsons, default=0.0),
        "max_abs_residual_spearman": max(spearmans, default=0.0),
        "max_residual_mutual_information": max(mis, default=0.0),
    }


def choose_with_tie_band(rows: list[dict[str, Any]], tolerance: float = 0.0001) -> dict[str, Any]:
    if not rows:
        raise ValueError("no score rows supplied")
    best = min(float(row["rmsle"]) for row in rows)
    eligible = [row for row in rows if float(row["rmsle"]) - best < tolerance]
    return min(eligible, key=lambda row: (int(row["feature_count"]), float(row["rmsle"]), str(row["batch_id"])))


def score_batches(
    *,
    atlas_bundle: Path,
    batches: dict[str, ValidatedMatrix],
    output_dir: Path,
) -> dict[str, Any]:
    """Run the fixed leakage-safe screen and confirmation protocol on GPU.

    This trusted process reads only the frozen public-training targets in the Atlas bundle. It never
    reads any test target source and emits no test predictions.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    atlas_train = np.load(atlas_bundle / "train.npy", mmap_mode="r", allow_pickle=False)
    targets = np.load(atlas_bundle / "targets.npy", mmap_mode="r", allow_pickle=False)
    target_names = json.loads((atlas_bundle / "targets.json").read_text())
    columns = json.loads((atlas_bundle / "columns.json").read_text())
    selected = json.loads(
        (atlas_bundle.parent / "run" / "selected_columns.json").read_text(encoding="utf-8")
    )
    selection_folds = np.load(atlas_bundle / "selection_folds.npy", allow_pickle=False)
    confirmation_folds = np.load(atlas_bundle / "confirmation_folds.npy", allow_pickle=False)
    column_index = {name: index for index, name in enumerate(columns)}
    screen_rows: list[dict[str, Any]] = []
    gpu = DualGPUExecutor(output_dir / "gpu_dispatch")

    for target_name in TARGETS:
        target = np.asarray(targets[:, target_names.index(target_name)], dtype=np.float64)
        base_indices = [column_index[name] for name in selected[target_name]]
        base = np.asarray(atlas_train[:, base_indices], dtype=np.float32)
        for batch_id, batch in batches.items():
            candidate = batch.train[list(batch.columns)].to_numpy(dtype=np.float32)
            combined = np.column_stack([base, candidate])
            per_fold: list[float] = []
            importances: list[float] = []
            stats: dict[str, float] | None = None
            for seed in SCREEN_SEEDS:
                for fold in range(2):
                    validation = selection_folds == fold
                    training = ~validation
                    (baseline_prediction, _), (prediction, importance) = gpu.fit_pair(
                        GPUFitJob(
                            base,
                            target,
                            training,
                            validation,
                            iterations=SCREEN_TREES,
                            seed=seed,
                        ),
                        GPUFitJob(
                            combined,
                            target,
                            training,
                            validation,
                            iterations=SCREEN_TREES,
                            seed=seed,
                        ),
                    )
                    per_fold.append(rmsle(target[validation], prediction))
                    importance_total = float(importance.sum())
                    importances.append(
                        float(importance[-candidate.shape[1] :].sum() / importance_total)
                        if importance_total > 0
                        else 0.0
                    )
                    if stats is None:
                        stats = _residual_statistics(
                            candidate[validation], target[validation], baseline_prediction
                        )
            score = float(np.mean(per_fold))
            screen_rows.append(
                {
                    "target": target_name,
                    "batch_id": batch_id,
                    "feature_count": candidate.shape[1],
                    "rmsle": score,
                    "atlas_lift": ATLAS_TARGET_WINNERS[target_name] - score,
                    "control_809_lift": EXISTING_809_CONTROLS[target_name] - score,
                    "normalized_importance": float(np.mean(importances)),
                    "compute_cost_columns": int(candidate.shape[1]),
                    **(stats or {}),
                }
            )

    confirmed: list[dict[str, Any]] = []
    for target_name in TARGETS:
        ranked = sorted(
            [row for row in screen_rows if row["target"] == target_name],
            key=lambda row: (-float(row["atlas_lift"]), int(row["feature_count"]), row["batch_id"]),
        )[:5]
        views = [(row["batch_id"], [row["batch_id"]]) for row in ranked]
        positive = [row["batch_id"] for row in ranked if row["atlas_lift"] > 0]
        if positive:
            views.append(("positive_lift_union", positive))
        target = np.asarray(targets[:, target_names.index(target_name)], dtype=np.float64)
        base_indices = [column_index[name] for name in selected[target_name]]
        base = np.asarray(atlas_train[:, base_indices], dtype=np.float32)
        for view_id, batch_ids in views:
            candidate_frames = [batches[batch_id].train[list(batches[batch_id].columns)] for batch_id in batch_ids]
            candidate = pd.concat(candidate_frames, axis=1)
            if candidate.columns.duplicated().any():
                raise MatrixValidationError(f"confirmation union {view_id} has duplicate names")
            matrix = np.column_stack([base, candidate.to_numpy(dtype=np.float32)])
            fold_scores: list[float] = []
            for fold in range(5):
                validation = confirmation_folds == fold
                prediction, _ = gpu.fit(
                    GPUFitJob(
                        matrix,
                        target,
                        ~validation,
                        validation,
                        iterations=CONFIRM_TREES,
                        seed=4219,
                    ),
                    preferred_host=DualGPUExecutor.HOSTS[fold % 2],
                )
                fold_scores.append(rmsle(target[validation], prediction))
            score = float(np.mean(fold_scores))
            confirmed.append(
                {
                    "target": target_name,
                    "batch_id": view_id,
                    "members": batch_ids,
                    "feature_count": int(candidate.shape[1]),
                    "rmsle": score,
                    "fold_rmsle": fold_scores,
                    "atlas_lift": ATLAS_TARGET_WINNERS[target_name] - score,
                    "control_809_lift": EXISTING_809_CONTROLS[target_name] - score,
                }
            )

    winners = {
        target: choose_with_tie_band([row for row in confirmed if row["target"] == target])
        for target in TARGETS
    }
    report = {
        "protocol": {
            "screen_seeds": list(SCREEN_SEEDS),
            "selection_folds": 2,
            "screen_trees": SCREEN_TREES,
            "confirmation_folds": 5,
            "confirmation_trees": CONFIRM_TREES,
            "task_type": "GPU",
            "gpu_hosts": {"local": "RTX 3090", "xbabe1": "RTX 4090"},
            "one_process_per_gpu": True,
            "failed_job_retry": "once_on_other_gpu_host",
            "cpu_fallback": False,
            "test_labels_used": False,
            "worker_sha256": gpu.worker_sha256,
            "dispatcher_sha256": gpu.dispatcher_sha256,
            "dispatch_events_sha256": sha256_file(gpu.events.path),
            "dispatch_hash_chain_valid": gpu.events.verify()[0],
        },
        "screen": screen_rows,
        "confirmation": confirmed,
        "winners": winners,
        "mean_rmsle": float(np.mean([winners[target]["rmsle"] for target in TARGETS])),
        "beats_atlas_winner_each_target": all(winners[t]["atlas_lift"] > 0 for t in TARGETS),
        "beats_existing_809_each_target": all(winners[t]["control_809_lift"] > 0 for t in TARGETS),
    }
    report["sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
    atomic_json(output_dir / "score_report.json", report)
    pd.DataFrame(screen_rows).to_csv(output_dir / "screen_scores.csv", index=False)
    pd.DataFrame(confirmed).to_json(output_dir / "confirmation_scores.json", orient="records", indent=2)
    return report
