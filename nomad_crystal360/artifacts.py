from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .constants import FAMILY_COUNTS, TARGETS
from .featurizer import Crystal360Featurizer, _array_signature
from .io import load_structures


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def geometry_tree_hash(frame: pd.DataFrame, geometry_root: Path) -> str:
    digest = hashlib.sha256()
    for structure_id in frame["id"].astype(int):
        path = geometry_root / str(structure_id) / "geometry.xyz"
        digest.update(str(structure_id).encode("ascii"))
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def _write_frame(frame: pd.DataFrame, stem: Path, *, csv: bool = True) -> list[Path]:
    paths: list[Path] = []
    if csv:
        csv_path = stem.with_suffix(".csv")
        frame.to_csv(csv_path, index=False)
        paths.append(csv_path)
    parquet_path = stem.with_suffix(".parquet")
    frame.to_parquet(parquet_path, index=False, compression="zstd")
    paths.append(parquet_path)
    return paths


def _load_baseline(path: Path, expected_ids: pd.Series) -> tuple[pd.DataFrame, str]:
    original_hash = sha256_file(path)
    frame = pd.read_csv(path)
    if "id" not in frame:
        raise ValueError(f"Baseline matrix has no id column: {path}")
    if frame.shape[1] != 450:
        raise ValueError(f"Expected id + 449 baseline columns in {path}, found {frame.shape[1]}")
    if frame["id"].astype(int).tolist() != expected_ids.astype(int).tolist():
        raise ValueError(f"Baseline id order does not match raw data: {path}")
    predictors = frame.drop(columns="id")
    if predictors.shape[1] != 449:
        raise AssertionError("Baseline predictor width drifted")
    return predictors, original_hash


def _quality_report(
    train: pd.DataFrame,
    test: pd.DataFrame,
    baseline_train: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    missingness = pd.DataFrame(
        {
            "feature": train.columns,
            "train_missing_count": train.isna().sum().to_numpy(dtype=int),
            "train_missing_fraction": train.isna().mean().to_numpy(dtype=float),
            "test_missing_count": test.isna().sum().to_numpy(dtype=int),
            "test_missing_fraction": test.isna().mean().to_numpy(dtype=float),
        }
    )
    variance_rows: list[dict[str, Any]] = []
    crystal_signatures: dict[str, str] = {}
    duplicate_within: list[dict[str, str]] = []
    baseline_signatures = {
        _array_signature(baseline_train[column].to_numpy(dtype=float)): column
        for column in baseline_train.columns
    }
    duplicate_baseline: list[dict[str, str]] = []
    constant: list[str] = []
    for column in train.columns:
        values = train[column].to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        unique_count = int(np.unique(finite).size)
        variance = float(np.var(finite)) if finite.size else math_nan()
        variance_rows.append(
            {
                "feature": column,
                "finite_count": int(finite.size),
                "unique_finite_count": unique_count,
                "train_variance": variance,
            }
        )
        if unique_count <= 1:
            constant.append(column)
        signature = _array_signature(values)
        if signature in crystal_signatures:
            duplicate_within.append(
                {"feature": column, "duplicates": crystal_signatures[signature]}
            )
        else:
            crystal_signatures[signature] = column
        if signature in baseline_signatures:
            duplicate_baseline.append(
                {"feature": column, "duplicates": baseline_signatures[signature]}
            )
    duplicate_report = {
        "comparison": "exact float64 values with identical NaN mask on pooled training rows",
        "constant_columns": constant,
        "duplicates_within_crystal360": duplicate_within,
        "duplicates_against_baseline_449": duplicate_baseline,
        "passed": not constant and not duplicate_within and not duplicate_baseline,
    }
    return missingness, pd.DataFrame(variance_rows), duplicate_report


def math_nan() -> float:
    return float("nan")


def _dependency_report(lock_path: Path) -> dict[str, Any]:
    packages = (
        "ase",
        "joblib",
        "numpy",
        "pandas",
        "pyarrow",
        "pymatgen",
        "pymatgen-core",
        "scikit-learn",
        "scipy",
        "spglib",
    )
    dependencies: dict[str, Any] = {}
    for package in packages:
        distribution = importlib.metadata.distribution(package)
        record = distribution.read_text("RECORD") or ""
        dependencies[package] = {
            "version": distribution.version,
            "record_sha256": hashlib.sha256(record.encode("utf-8")).hexdigest(),
        }
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "executable": sys.executable,
        "lock_file": str(lock_path.resolve()),
        "lock_sha256": sha256_file(lock_path),
        "dependencies": dependencies,
    }


def build_artifacts(
    *,
    train_csv: Path,
    test_csv: Path,
    train_geometry_root: Path,
    test_geometry_root: Path,
    baseline_train_csv: Path,
    baseline_test_csv: Path,
    output_dir: Path,
    schema_path: Path,
    lock_path: Path,
    n_jobs: int,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    train_raw = pd.read_csv(train_csv)
    test_raw = pd.read_csv(test_csv)
    for label, frame in (("train", train_raw), ("test", test_raw)):
        missing_targets = [target for target in TARGETS if target not in frame]
        if missing_targets:
            raise ValueError(f"{label} input lacks target columns: {missing_targets}")

    baseline_train, baseline_train_hash = _load_baseline(baseline_train_csv, train_raw["id"])
    baseline_test, baseline_test_hash = _load_baseline(baseline_test_csv, test_raw["id"])
    if list(baseline_train.columns) != list(baseline_test.columns):
        raise ValueError("Baseline train/test predictor names or order differ")

    training_source = {
        "raw_train_csv": str(train_csv.resolve()),
        "raw_train_csv_sha256": sha256_file(train_csv),
        "train_geometry_root": str(train_geometry_root.resolve()),
        "train_geometry_tree_sha256": geometry_tree_hash(train_raw, train_geometry_root),
        "training_row_count": int(len(train_raw)),
        "radial_shell_labels_used": False,
        "test_rows_used_for_schema": False,
    }

    featurizer = Crystal360Featurizer(n_jobs=n_jobs)
    train_structures = load_structures(train_raw, train_geometry_root)
    shell_boundaries = featurizer.fit_shell_boundaries(train_structures)
    train_candidates, train_groups = featurizer.transform_candidates(
        train_structures,
        train_raw["spacegroup"],
        shell_boundaries,
    )
    schema = featurizer.select_schema(
        train_candidates,
        baseline_train,
        shell_boundaries,
        training_source,
    )
    train_crystal = featurizer.transform_selected(train_candidates, schema)

    # Freeze schema and validated views before any test geometry or test target is read downstream.
    schema.save(schema_path)
    schema.save(output_dir / "crystal360_schema.json")
    frozen_schema_hash = sha256_file(schema_path)
    validated_columns = {
        target: {
            "target": target,
            "selection_stage": "training-only structural quality gates",
            "labels_used_for_column_filtering": False,
            "predictor_count": 809,
            "columns": list(baseline_train.columns) + schema.columns,
            "schema_sha256": frozen_schema_hash,
        }
        for target in TARGETS
    }
    for target, payload in validated_columns.items():
        path = output_dir / f"validated_columns_{target}.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    del train_structures
    test_structures = load_structures(test_raw, test_geometry_root)
    test_candidates, test_groups = featurizer.transform_candidates(
        test_structures,
        test_raw["spacegroup"],
        shell_boundaries,
    )
    test_crystal = featurizer.transform_selected(test_candidates, schema)
    if list(train_crystal.columns) != list(test_crystal.columns):
        raise AssertionError("Crystal360 train/test column order differs")
    if train_crystal.shape[1] != 360:
        raise AssertionError(f"Expected 360 Crystal360 predictors, found {train_crystal.shape[1]}")

    combined_train = pd.concat(
        [baseline_train.reset_index(drop=True), train_crystal.reset_index(drop=True)], axis=1
    )
    combined_test = pd.concat(
        [baseline_test.reset_index(drop=True), test_crystal.reset_index(drop=True)], axis=1
    )
    if combined_train.shape[1] != 809 or combined_test.shape[1] != 809:
        raise AssertionError("Combined predictor matrices must contain exactly 809 columns")
    if list(combined_train.columns) != list(combined_test.columns):
        raise AssertionError("Combined train/test column order differs")

    missingness, variance, duplicates = _quality_report(train_crystal, test_crystal, baseline_train)
    if not duplicates["passed"]:
        raise AssertionError(f"Post-selection quality gates failed: {duplicates}")

    artifact_paths: list[Path] = []
    artifact_paths.extend(_write_frame(train_crystal, output_dir / "train_crystal360"))
    artifact_paths.extend(_write_frame(test_crystal, output_dir / "test_crystal360"))
    artifact_paths.extend(_write_frame(combined_train, output_dir / "train_predictors_809"))
    artifact_paths.extend(_write_frame(combined_test, output_dir / "test_predictors_809"))

    for target in TARGETS:
        train_target = combined_train.copy()
        train_target[target] = train_raw[target].to_numpy(dtype=float)
        test_target = combined_test.copy()
        test_target[target] = test_raw[target].to_numpy(dtype=float)
        if train_target.columns[-1] != target or test_target.columns[-1] != target:
            raise AssertionError("Target column is not last")
        artifact_paths.extend(_write_frame(train_target, output_dir / f"train_{target}_810"))
        artifact_paths.extend(_write_frame(test_target, output_dir / f"test_{target}_810"))

    family_columns: dict[str, list[str]] = {}
    selected_by_name = {item.name: item for item in schema.selected_features}
    for family in FAMILY_COUNTS:
        columns = [name for name in schema.columns if selected_by_name[name].family == family]
        family_columns[family] = columns
        additive_train = pd.concat([baseline_train, train_crystal[columns]], axis=1)
        additive_test = pd.concat([baseline_test, test_crystal[columns]], axis=1)
        artifact_paths.extend(
            _write_frame(additive_train, output_dir / f"ablation_{family}_train", csv=False)
        )
        artifact_paths.extend(
            _write_frame(additive_test, output_dir / f"ablation_{family}_test", csv=False)
        )
    (output_dir / "family_ablation_columns.json").write_text(
        json.dumps(family_columns, indent=2) + "\n", encoding="utf-8"
    )

    pd.DataFrame({"id": train_raw["id"].astype(int), "anonymous_prototype": train_groups}).to_csv(
        output_dir / "train_anonymous_prototypes.csv", index=False
    )
    pd.DataFrame({"id": test_raw["id"].astype(int), "anonymous_prototype": test_groups}).to_csv(
        output_dir / "test_anonymous_prototypes.csv", index=False
    )
    pd.DataFrame({"id": train_raw["id"].astype(int)}).to_csv(
        output_dir / "train_row_ids.csv", index=False
    )
    pd.DataFrame({"id": test_raw["id"].astype(int)}).to_csv(
        output_dir / "test_row_ids.csv", index=False
    )

    definitions = pd.DataFrame([item.__dict__ for item in schema.selected_features])
    definitions.to_csv(output_dir / "units_formulas.csv", index=False)
    missingness.to_csv(output_dir / "missingness.csv", index=False)
    variance.to_csv(output_dir / "variance.csv", index=False)
    (output_dir / "duplicate_checks.json").write_text(
        json.dumps(duplicates, indent=2) + "\n", encoding="utf-8"
    )
    dependency_report = _dependency_report(lock_path)
    (output_dir / "dependency_hashes.json").write_text(
        json.dumps(dependency_report, indent=2) + "\n", encoding="utf-8"
    )

    if sha256_file(schema_path) != frozen_schema_hash:
        raise AssertionError("Frozen schema changed during test transformation")
    if sha256_file(baseline_train_csv) != baseline_train_hash:
        raise AssertionError("Baseline training artifact was modified")
    if sha256_file(baseline_test_csv) != baseline_test_hash:
        raise AssertionError("Baseline test artifact was modified")

    tracked = (
        artifact_paths
        + [
            output_dir / "crystal360_schema.json",
            output_dir / "units_formulas.csv",
            output_dir / "missingness.csv",
            output_dir / "variance.csv",
            output_dir / "duplicate_checks.json",
            output_dir / "dependency_hashes.json",
            output_dir / "family_ablation_columns.json",
            output_dir / "train_anonymous_prototypes.csv",
            output_dir / "test_anonymous_prototypes.csv",
            output_dir / "train_row_ids.csv",
            output_dir / "test_row_ids.csv",
        ]
        + [output_dir / f"validated_columns_{target}.json" for target in TARGETS]
    )
    hashes = {
        path.name: {"sha256": sha256_file(path), "bytes": os.path.getsize(path)} for path in tracked
    }
    actual_family_counts = {family: len(columns) for family, columns in family_columns.items()}
    manifest = {
        "artifact_name": "Nomad Crystal360 Feature Pack",
        "schema_sha256": frozen_schema_hash,
        "train_rows": int(len(train_raw)),
        "test_rows": int(len(test_raw)),
        "crystal360_predictors": 360,
        "baseline_predictors": 449,
        "combined_predictors": 809,
        "target_matrix_columns": 810,
        "target_last": True,
        "train_test_columns_identical": True,
        "family_counts_requested": FAMILY_COUNTS,
        "family_counts_selected": actual_family_counts,
        "reserve_replacements": schema.replacements,
        "quality_gates": duplicates,
        "shell_fit_training_only": True,
        "test_targets_used_for_schema_or_promotion": False,
        "labeled_test_status": "historically reused; permitted only for final informational scoring",
        "baseline_artifacts": {
            "train": str(baseline_train_csv.resolve()),
            "train_sha256": baseline_train_hash,
            "test": str(baseline_test_csv.resolve()),
            "test_sha256": baseline_test_hash,
            "modified": False,
        },
        "artifact_hashes": hashes,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
