from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import root_mean_squared_log_error
from sklearn.model_selection import GroupKFold

from .artifacts import sha256_file
from .constants import FAMILY_COUNTS, TARGETS


def _model(max_iter: int, seed: int) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.06,
        max_iter=max_iter,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=1.0,
        early_stopping=False,
        random_state=seed,
    )


def _rmsle(y_true: np.ndarray, prediction: np.ndarray) -> float:
    return float(root_mean_squared_log_error(y_true, np.clip(prediction, 0.0, None)))


def _fit_predict(
    x_train: pd.DataFrame,
    y_train: np.ndarray,
    x_eval: pd.DataFrame,
    *,
    max_iter: int,
    seed: int,
) -> np.ndarray:
    model = _model(max_iter, seed)
    model.fit(x_train, np.log1p(y_train))
    return np.expm1(model.predict(x_eval))


def _matrix_catalog(artifact_dir: Path) -> dict[str, tuple[Path, Path]]:
    catalog = {
        "baseline_449": (
            artifact_dir / "_baseline_train.parquet",
            artifact_dir / "_baseline_test.parquet",
        ),
        "crystal360": (
            artifact_dir / "train_crystal360.parquet",
            artifact_dir / "test_crystal360.parquet",
        ),
        "combined_809": (
            artifact_dir / "train_predictors_809.parquet",
            artifact_dir / "test_predictors_809.parquet",
        ),
    }
    for family in FAMILY_COUNTS:
        catalog[f"baseline_plus_{family}"] = (
            artifact_dir / f"ablation_{family}_train.parquet",
            artifact_dir / f"ablation_{family}_test.parquet",
        )
    return catalog


def _materialize_baseline_views(artifact_dir: Path) -> None:
    combined_train = pd.read_parquet(artifact_dir / "train_predictors_809.parquet")
    combined_test = pd.read_parquet(artifact_dir / "test_predictors_809.parquet")
    combined_train.iloc[:, :449].to_parquet(
        artifact_dir / "_baseline_train.parquet", index=False, compression="zstd"
    )
    combined_test.iloc[:, :449].to_parquet(
        artifact_dir / "_baseline_test.parquet", index=False, compression="zstd"
    )


def _promotion_views(
    artifact_dir: Path,
    fold_scores: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    combined_train = pd.read_parquet(artifact_dir / "train_predictors_809.parquet")
    combined_test = pd.read_parquet(artifact_dir / "test_predictors_809.parquet")
    family_columns = json.loads(
        (artifact_dir / "family_ablation_columns.json").read_text(encoding="utf-8")
    )
    promotions: dict[str, dict[str, Any]] = {}
    for target in TARGETS:
        target_rows = fold_scores[fold_scores["target"] == target]
        baseline = target_rows[target_rows["matrix"] == "baseline_449"]
        baseline_by_repeat = baseline.groupby("repeat")["rmsle"].mean()
        selected_families: list[str] = []
        evidence: dict[str, Any] = {}
        for family in FAMILY_COUNTS:
            matrix_name = f"baseline_plus_{family}"
            family_rows = target_rows[target_rows["matrix"] == matrix_name]
            family_by_repeat = family_rows.groupby("repeat")["rmsle"].mean()
            deltas = family_by_repeat - baseline_by_repeat
            promote = bool(float(deltas.mean()) < 0.0 and int((deltas < 0.0).sum()) >= 2)
            if promote:
                selected_families.append(family)
            evidence[family] = {
                "mean_rmsle_delta_vs_449": float(deltas.mean()),
                "improved_repeat_count": int((deltas < 0.0).sum()),
                "promoted": promote,
            }
        selected_columns = list(combined_train.columns[:449])
        for family in selected_families:
            selected_columns.extend(family_columns[family])
        train_view = combined_train[selected_columns]
        test_view = combined_test[selected_columns]
        train_path = artifact_dir / f"validated_{target}_predictors_train.parquet"
        test_path = artifact_dir / f"validated_{target}_predictors_test.parquet"
        train_view.to_parquet(train_path, index=False, compression="zstd")
        test_view.to_parquet(test_path, index=False, compression="zstd")
        payload = {
            "target": target,
            "selection_data": "training targets only",
            "selection_protocol": (
                "Promote a family when its paired mean GroupKFold RMSLE delta is negative "
                "and it improves at least two of three repeats."
            ),
            "test_targets_used": False,
            "selected_families": selected_families,
            "predictor_count": len(selected_columns),
            "columns": selected_columns,
            "family_evidence": evidence,
            "train_view_sha256": sha256_file(train_path),
            "test_view_sha256": sha256_file(test_path),
        }
        view_path = artifact_dir / f"validated_columns_{target}.json"
        view_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        payload["view_manifest_sha256"] = sha256_file(view_path)
        promotions[target] = payload
    return promotions


def run_benchmark(
    artifact_dir: Path,
    *,
    max_iter: int = 120,
    seeds: tuple[int, int, int] = (1701, 2909, 4219),
) -> dict[str, Any]:
    schema_path = artifact_dir / "crystal360_schema.json"
    schema_hash = sha256_file(schema_path)
    _materialize_baseline_views(artifact_dir)
    catalog = _matrix_catalog(artifact_dir)
    groups = (
        pd.read_csv(artifact_dir / "train_anonymous_prototypes.csv")["anonymous_prototype"]
        .astype(str)
        .to_numpy()
    )
    if len(np.unique(groups)) < 5:
        raise ValueError("Anonymous-prototype grouping has fewer than five groups")

    target_frames = {
        target: pd.read_parquet(artifact_dir / f"train_{target}_810.parquet") for target in TARGETS
    }
    fold_rows: list[dict[str, Any]] = []
    for matrix_name, (train_path, _) in catalog.items():
        x_train = pd.read_parquet(train_path)
        for target in TARGETS:
            y_train = target_frames[target][target].to_numpy(dtype=float)
            for repeat, seed in enumerate(seeds, start=1):
                splitter = GroupKFold(n_splits=5, shuffle=True, random_state=seed)
                for fold, (fit_indices, validation_indices) in enumerate(
                    splitter.split(x_train, y_train, groups), start=1
                ):
                    prediction = _fit_predict(
                        x_train.iloc[fit_indices],
                        y_train[fit_indices],
                        x_train.iloc[validation_indices],
                        max_iter=max_iter,
                        seed=seed + fold,
                    )
                    fold_rows.append(
                        {
                            "matrix": matrix_name,
                            "target": target,
                            "repeat": repeat,
                            "fold": fold,
                            "seed": seed,
                            "train_rows": int(len(fit_indices)),
                            "validation_rows": int(len(validation_indices)),
                            "predictor_count": int(x_train.shape[1]),
                            "rmsle": _rmsle(y_train[validation_indices], prediction),
                        }
                    )
    fold_scores = pd.DataFrame(fold_rows)
    fold_scores.to_csv(artifact_dir / "benchmark_groupkfold_scores.csv", index=False)
    summary = (
        fold_scores.groupby(["matrix", "target", "predictor_count"], as_index=False)["rmsle"]
        .agg(["mean", "std", "min", "max"])
        .reset_index()
    )
    summary.to_csv(artifact_dir / "benchmark_groupkfold_summary.csv", index=False)

    promotions = _promotion_views(artifact_dir, fold_scores)
    frozen_view_hashes = {
        target: sha256_file(artifact_dir / f"validated_columns_{target}.json") for target in TARGETS
    }

    # Only now, after schemas and promoted views are frozen, use historically reused test targets.
    informational_rows: list[dict[str, Any]] = []
    test_target_frames = {
        target: pd.read_parquet(artifact_dir / f"test_{target}_810.parquet") for target in TARGETS
    }
    scored_catalog = dict(catalog)
    for target in TARGETS:
        scored_catalog[f"validated_view_{target}"] = (
            artifact_dir / f"validated_{target}_predictors_train.parquet",
            artifact_dir / f"validated_{target}_predictors_test.parquet",
        )
    for matrix_name, (train_path, test_path) in scored_catalog.items():
        x_train = pd.read_parquet(train_path)
        x_test = pd.read_parquet(test_path)
        for target in TARGETS:
            if (
                matrix_name.startswith("validated_view_")
                and matrix_name != f"validated_view_{target}"
            ):
                continue
            y_train = target_frames[target][target].to_numpy(dtype=float)
            y_test = test_target_frames[target][target].to_numpy(dtype=float)
            prediction = _fit_predict(
                x_train,
                y_train,
                x_test,
                max_iter=max_iter,
                seed=seeds[0],
            )
            informational_rows.append(
                {
                    "matrix": matrix_name,
                    "target": target,
                    "predictor_count": int(x_train.shape[1]),
                    "rmsle": _rmsle(y_test, prediction),
                    "status": "informational_only_historically_reused_test",
                }
            )
    informational = pd.DataFrame(informational_rows)
    informational.to_csv(artifact_dir / "benchmark_labeled_test_informational.csv", index=False)

    if sha256_file(schema_path) != schema_hash:
        raise AssertionError("Crystal360 schema changed during benchmarking")
    for target, frozen_hash in frozen_view_hashes.items():
        if sha256_file(artifact_dir / f"validated_columns_{target}.json") != frozen_hash:
            raise AssertionError(f"Validated view changed during test scoring for {target}")

    report = {
        "protocol": "three repeated five-fold anonymous-prototype GroupKFold",
        "repeats": 3,
        "folds": 5,
        "seeds": list(seeds),
        "model": "HistGradientBoostingRegressor fitted to log1p(target)",
        "max_iter": max_iter,
        "matrix_count": len(catalog),
        "cv_fit_count": len(fold_scores),
        "schema_sha256": schema_hash,
        "promotion_views": promotions,
        "labeled_test_status": "informational_only_historically_reused_test",
        "outputs": {
            "fold_scores": "benchmark_groupkfold_scores.csv",
            "summary": "benchmark_groupkfold_summary.csv",
            "informational_test": "benchmark_labeled_test_informational.csv",
        },
    }
    return finalize_benchmark_artifacts(artifact_dir, report)


def finalize_benchmark_artifacts(
    artifact_dir: Path, report: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Hash benchmark outputs and refresh the pack manifest after promotion."""
    benchmark_manifest = artifact_dir / "benchmark_manifest.json"
    if report is None:
        report = json.loads(benchmark_manifest.read_text(encoding="utf-8"))
    output_paths = [
        artifact_dir / "benchmark_groupkfold_scores.csv",
        artifact_dir / "benchmark_groupkfold_summary.csv",
        artifact_dir / "benchmark_labeled_test_informational.csv",
        artifact_dir / "_baseline_train.parquet",
        artifact_dir / "_baseline_test.parquet",
    ]
    for target in TARGETS:
        output_paths.extend(
            [
                artifact_dir / f"validated_columns_{target}.json",
                artifact_dir / f"validated_{target}_predictors_train.parquet",
                artifact_dir / f"validated_{target}_predictors_test.parquet",
            ]
        )
    report["output_hashes"] = {
        path.name: {"sha256": sha256_file(path), "bytes": os.path.getsize(path)}
        for path in output_paths
    }
    benchmark_manifest.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    pack_manifest_path = artifact_dir / "manifest.json"
    pack_manifest = json.loads(pack_manifest_path.read_text(encoding="utf-8"))
    final_paths = output_paths + [benchmark_manifest]
    for path in final_paths:
        pack_manifest["artifact_hashes"][path.name] = {
            "sha256": sha256_file(path),
            "bytes": os.path.getsize(path),
        }
    pack_manifest["benchmark"] = {
        "protocol": report["protocol"],
        "cv_fit_count": report["cv_fit_count"],
        "manifest": benchmark_manifest.name,
        "manifest_sha256": sha256_file(benchmark_manifest),
        "labeled_test_status": report["labeled_test_status"],
    }
    pack_manifest_path.write_text(
        json.dumps(pack_manifest, indent=2) + "\n", encoding="utf-8"
    )
    return report
