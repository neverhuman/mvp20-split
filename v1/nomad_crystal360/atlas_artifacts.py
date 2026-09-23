from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .artifacts import geometry_tree_hash, sha256_file
from .atlas import AtlasFeatureDefinition, build_atlas_definitions, featurize_structures
from .constants import TARGETS
from .io import load_structures


STRUCTURE_COLUMNS = (
    "id",
    "spacegroup",
    "number_of_total_atoms",
    "percent_atom_al",
    "percent_atom_ga",
    "percent_atom_in",
    "lattice_vector_1_ang",
    "lattice_vector_2_ang",
    "lattice_vector_3_ang",
    "lattice_angle_alpha_degree",
    "lattice_angle_beta_degree",
    "lattice_angle_gamma_degree",
)


def _hash_tree(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(path.relative_to(root)): {"sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _column_signature(values: np.ndarray) -> str:
    array = np.asarray(values, dtype="<f8")
    missing = np.isnan(array)
    canonical = array.copy()
    canonical[missing] = 0.0
    digest = hashlib.sha256()
    digest.update(missing.tobytes())
    digest.update(canonical.tobytes())
    return digest.hexdigest()


def _select_valid_columns(
    candidates: np.ndarray,
    definitions: list[AtlasFeatureDefinition],
    existing_train: pd.DataFrame,
    *,
    base_count: int,
    minimum: int,
) -> tuple[list[int], dict[str, Any]]:
    existing_signatures = {
        _column_signature(existing_train[column].to_numpy(dtype=float)): column
        for column in existing_train.columns
    }
    selected: list[int] = []
    selected_signatures: dict[str, str] = {}
    rejected: list[dict[str, str]] = []

    def consider(index: int) -> None:
        definition = definitions[index]
        values = candidates[:, index]
        if np.any(np.isinf(values)):
            rejected.append({"feature": definition.name, "reason": "infinite_value"})
            return
        finite = values[np.isfinite(values)]
        if finite.size == 0 or np.unique(finite).size <= 1:
            rejected.append({"feature": definition.name, "reason": "constant_or_all_missing"})
            return
        signature = _column_signature(values)
        if signature in existing_signatures:
            rejected.append(
                {
                    "feature": definition.name,
                    "reason": "duplicate_of_existing_809",
                    "duplicate": existing_signatures[signature],
                }
            )
            return
        if signature in selected_signatures:
            rejected.append(
                {
                    "feature": definition.name,
                    "reason": "duplicate_within_atlas",
                    "duplicate": selected_signatures[signature],
                }
            )
            return
        selected.append(index)
        selected_signatures[signature] = definition.name

    for index in range(base_count):
        consider(index)
    fallback_activated = len(selected) < minimum
    if fallback_activated:
        for index in range(base_count, len(definitions)):
            consider(index)
    if len(selected) < minimum:
        raise ValueError(
            f"Only {len(selected)} validated unique CrystalAtlas predictors; minimum is {minimum}"
        )
    return selected, {
        "candidate_count": len(definitions),
        "base_candidate_count": base_count,
        "selected_count": len(selected),
        "rejected_count": len(rejected),
        "fallback_0p05_rdf_activated": fallback_activated,
        "rejection_counts": dict(Counter(item["reason"] for item in rejected)),
        "rejections": rejected,
    }


def _legacy_definition(name: str, family: str, source_hash: str) -> dict[str, str]:
    distance_family = family in {"pair_distance", "nearest_neighbor"}
    coordinate_family = family == "coordinate"
    if family == "raw":
        formula = f"raw public NOMAD field {name}"
    else:
        formula = f"deterministic {family} operator for {name} in nomad_449_baseline.py"
    if "degree" in name or name.startswith(("alpha_", "beta_", "gamma_", "angle_")):
        unit = "degree"
    elif "density" in name:
        unit = "atoms angstrom^-3 or g cm^-3 as named"
    elif "volume" in name:
        unit = "angstrom^3"
    elif coordinate_family or distance_family or any(token in name for token in ("len_", "lattice_vector")):
        unit = "angstrom except dimensionless count/fraction/CV statistics"
    else:
        unit = "dimensionless or elemental-property unit encoded by the column name"
    neighbor_rule = (
        "Legacy direct unit-cell Cartesian element pairs; see the immutable baseline source."
        if distance_family
        else "No neighbor rule, or the immutable baseline operator named by the feature."
    )
    return {
        "name": name,
        "family": f"existing449_{family}",
        "formula": formula,
        "unit": unit,
        "neighbor_rule": neighbor_rule,
        "normalization": "Exactly as emitted by the unchanged 449-column baseline.",
        "interpretation": f"Frozen pre-existing baseline predictor {name}.",
        "invariance": "Legacy behavior retained unchanged; see baseline source for its invariance scope.",
        "provenance": f"nomad_449_baseline.py sha256={source_hash}",
        "block": f"existing449_{family}",
    }


def _combined_registry(
    existing_columns: list[str],
    selected_definitions: list[AtlasFeatureDefinition],
    *,
    baseline_source: Path,
    baseline_manifest: Path,
    crystal_units: Path,
    crystal_schema_hash: str,
) -> pd.DataFrame:
    baseline_payload = json.loads(baseline_manifest.read_text(encoding="utf-8"))
    baseline_columns = list(baseline_payload["feature_columns"])
    family_counts = baseline_payload["feature_family_counts"]
    family_by_column: dict[str, str] = {}
    offset = 0
    for family, count in family_counts.items():
        for name in baseline_columns[offset : offset + int(count)]:
            family_by_column[name] = family
        offset += int(count)
    baseline_hash = sha256_file(baseline_source)
    rows = [
        _legacy_definition(name, family_by_column[name], baseline_hash) for name in baseline_columns
    ]
    crystal = pd.read_csv(crystal_units).to_dict(orient="records")
    for item in crystal:
        rows.append(
            {
                "name": item["name"],
                "family": f"crystal360_{item['family']}",
                "formula": item["formula"],
                "unit": item["unit"],
                "neighbor_rule": item["neighbors"],
                "normalization": "Exactly as stated by the frozen Crystal360 formula and schema.",
                "interpretation": item["interpretation"],
                "invariance": "Crystal360 periodic geometric invariant; frozen behavior retained.",
                "provenance": f"Crystal360 schema sha256={crystal_schema_hash}",
                "block": f"crystal360_{item['family']}",
            }
        )
    if [item["name"] for item in rows] != existing_columns:
        raise ValueError("Existing 809-column order does not match the 449 and Crystal360 registries")
    rows.extend(item.to_dict() for item in selected_definitions)
    registry = pd.DataFrame(rows)
    required = (
        "name", "family", "formula", "unit", "neighbor_rule", "normalization",
        "interpretation", "invariance", "provenance", "block",
    )
    if registry[list(required)].isna().any().any() or (registry[list(required)] == "").any().any():
        raise ValueError("Combined predictor registry has an unregistered field")
    return registry


def _environment_identity(lock_path: Path) -> dict[str, Any]:
    packages = ("joblib", "numpy", "pandas", "pyarrow", "pymatgen", "scipy", "spglib")
    return {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "lock_path": str(lock_path.resolve()),
        "lock_sha256": sha256_file(lock_path),
        "packages": {package: importlib.metadata.version(package) for package in packages},
    }


def build_atlas_artifacts(
    *,
    train_csv: Path,
    test_csv: Path,
    train_geometry_root: Path,
    test_geometry_root: Path,
    existing_dir: Path,
    baseline_dir: Path,
    baseline_source: Path,
    output_dir: Path,
    lock_path: Path,
    n_jobs: int,
    minimum_predictors: int = 8_000,
) -> dict[str, Any]:
    started = time.monotonic()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    legacy_before = {
        "nomad_449_baseline": _hash_tree(baseline_dir),
        "nomad_crystal360": _hash_tree(existing_dir),
    }

    train_structure = pd.read_csv(train_csv, usecols=list(STRUCTURE_COLUMNS))
    test_structure = pd.read_csv(test_csv, usecols=list(STRUCTURE_COLUMNS))
    train_targets = pd.read_csv(train_csv, usecols=["id", *TARGETS])
    if train_targets["id"].astype(int).tolist() != train_structure["id"].astype(int).tolist():
        raise ValueError("Training target ids do not match structure ids")
    existing_train = pd.read_parquet(existing_dir / "train_predictors_809.parquet")
    existing_test = pd.read_parquet(existing_dir / "test_predictors_809.parquet")
    if list(existing_train.columns) != list(existing_test.columns):
        raise ValueError("Existing train/test predictor columns differ")
    if len(existing_train) != len(train_structure) or len(existing_test) != len(test_structure):
        raise ValueError("Existing predictor row counts do not match public structure rows")

    train_structures = load_structures(train_structure, train_geometry_root)
    test_structures = load_structures(test_structure, test_geometry_root)
    definitions = build_atlas_definitions(fine_rdf=True)
    base_count = len(build_atlas_definitions())
    train_candidates = featurize_structures(train_structures, n_jobs=n_jobs, fine_rdf=True)
    selected_indices, quality = _select_valid_columns(
        train_candidates,
        definitions,
        existing_train,
        base_count=base_count,
        minimum=minimum_predictors,
    )
    selected_definitions = [definitions[index] for index in selected_indices]
    test_candidates = featurize_structures(test_structures, n_jobs=n_jobs, fine_rdf=True)
    if train_candidates.shape[1] != test_candidates.shape[1]:
        raise AssertionError("Candidate train/test widths differ")

    atlas_columns = [item.name for item in selected_definitions]
    train_atlas = pd.DataFrame(
        train_candidates[:, selected_indices].astype(np.float32), columns=atlas_columns
    )
    test_atlas = pd.DataFrame(
        test_candidates[:, selected_indices].astype(np.float32), columns=atlas_columns
    )
    combined_train = pd.concat([existing_train.reset_index(drop=True), train_atlas], axis=1)
    combined_test = pd.concat([existing_test.reset_index(drop=True), test_atlas], axis=1)
    if list(combined_train.columns) != list(combined_test.columns):
        raise AssertionError("Combined train/test column order differs")

    paths: list[Path] = []
    for frame, name in (
        (train_atlas, "train_atlas.parquet"),
        (test_atlas, "test_atlas.parquet"),
        (combined_train, "train_predictors.parquet"),
        (combined_test, "test_predictors.parquet"),
        (train_targets, "training_targets.parquet"),
        (pd.DataFrame({"id": test_structure["id"].astype(int)}), "test_ids.parquet"),
    ):
        path = output_dir / name
        frame.to_parquet(path, index=False, compression="zstd")
        paths.append(path)

    schema_path = existing_dir / "crystal360_schema.json"
    registry = _combined_registry(
        list(existing_train.columns),
        selected_definitions,
        baseline_source=baseline_source,
        baseline_manifest=baseline_dir / "feature_manifest.json",
        crystal_units=existing_dir / "units_formulas.csv",
        crystal_schema_hash=sha256_file(schema_path),
    )
    registry_path = output_dir / "predictor_registry.csv"
    registry.to_csv(registry_path, index=False)
    paths.append(registry_path)
    quality_path = output_dir / "quality_report.json"
    quality_path.write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")
    paths.append(quality_path)

    legacy_after = {
        "nomad_449_baseline": _hash_tree(baseline_dir),
        "nomad_crystal360": _hash_tree(existing_dir),
    }
    if legacy_before != legacy_after:
        raise AssertionError("An existing 449 or Crystal360 artifact changed during Atlas build")
    legacy_hash_path = output_dir / "preserved_legacy_hashes.json"
    legacy_hash_path.write_text(json.dumps(legacy_before, indent=2) + "\n", encoding="utf-8")
    paths.append(legacy_hash_path)

    artifacts = {
        path.name: {"sha256": sha256_file(path), "bytes": os.path.getsize(path)} for path in paths
    }
    manifest = {
        "artifact_name": "Nomad CrystalAtlas public experiment bundle",
        "created_unix": int(time.time()),
        "elapsed_seconds": time.monotonic() - started,
        "train_rows": len(train_structure),
        "test_rows": len(test_structure),
        "existing_predictors": existing_train.shape[1],
        "new_candidate_predictors": len(definitions),
        "validated_new_predictors": len(selected_indices),
        "combined_predictors": combined_train.shape[1],
        "family_counts": dict(Counter(item.family for item in selected_definitions)),
        "quality": {key: value for key, value in quality.items() if key != "rejections"},
        "neighbor_cache": "one exact-PBC 12 angstrom cache per structure",
        "test_target_columns_read": False,
        "test_targets_written_or_staged": False,
        "selection_labels": "public training labels only (feature quality is label-free)",
        "train_csv_sha256": sha256_file(train_csv),
        "train_geometry_tree_sha256": geometry_tree_hash(train_structure, train_geometry_root),
        "test_structure_csv_sha256": hashlib.sha256(
            test_structure.to_csv(index=False).encode("utf-8")
        ).hexdigest(),
        "test_geometry_tree_sha256": geometry_tree_hash(test_structure, test_geometry_root),
        "environment": _environment_identity(lock_path),
        "artifacts": artifacts,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
