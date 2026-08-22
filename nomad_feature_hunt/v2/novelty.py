from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from nomad_feature_hunt.ledger import atomic_json, sha256_file

from .constants import ATLAS_DEFINITION_COUNT, ATLAS_WIDTH, EXISTING_WIDTH, TEST_ROWS, TRAIN_ROWS
from .schemas import formula_fingerprint, semantic_fingerprint


REQUIRED_ATLAS_FILES = (
    "bundle_manifest.json",
    "columns.json",
    "train.npy",
    "test.npy",
    "train_ids.npy",
    "test_ids.npy",
    "targets.npy",
    "targets.json",
    "selection_folds.npy",
    "confirmation_folds.npy",
    "source_families.csv",
)


def _copy_atomic(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    shutil.copy2(source, temporary)
    os.replace(temporary, destination)


def stage_frozen_atlas(
    bundle_source: Path,
    definitions_source: Path,
    destination: Path,
    *,
    selected_columns_source: Path | None = None,
    expected_width: int = ATLAS_WIDTH,
    expected_definitions: int = ATLAS_DEFINITION_COUNT,
    expected_train_rows: int = TRAIN_ROWS,
    expected_test_rows: int = TEST_ROWS,
) -> dict[str, Any]:
    """Freeze all execution inputs below the campaign's NOMAD-owned inbox."""

    manifest_path = bundle_source / "bundle_manifest.json"
    if not manifest_path.exists():
        raise ValueError("Atlas bundle manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("predictors") != expected_width:
        raise ValueError("Atlas predictor count does not match the frozen control")
    if (
        manifest.get("train_rows") != expected_train_rows
        or manifest.get("test_rows") != expected_test_rows
    ):
        raise ValueError("Atlas row counts do not match the frozen control")
    if manifest.get("contains_test_targets") is not False or manifest.get("test_labels_used") is not False:
        raise ValueError("Atlas manifest does not prove the labeled-test boundary")
    missing = [name for name in REQUIRED_ATLAS_FILES if not (bundle_source / name).exists()]
    if missing:
        raise ValueError(f"Atlas bundle files are missing: {missing}")
    definitions = json.loads(definitions_source.read_text(encoding="utf-8"))
    if len(definitions) != expected_definitions:
        raise ValueError(
            f"Atlas definitions contain {len(definitions)}, expected {expected_definitions}"
        )
    destination.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_ATLAS_FILES:
        _copy_atomic(bundle_source / name, destination / name)
    _copy_atomic(definitions_source, destination / "atlas_definitions.json")
    if selected_columns_source is not None:
        selected = json.loads(selected_columns_source.read_text(encoding="utf-8"))
        columns = set(json.loads((bundle_source / "columns.json").read_text(encoding="utf-8")))
        if set(selected) != {"formation_energy_ev_natom", "bandgap_energy_ev"}:
            raise ValueError("Atlas selected controls do not cover the two fixed targets")
        unresolved = sorted(
            name for names in selected.values() for name in names if name not in columns
        )
        if unresolved:
            raise ValueError(f"Atlas selected controls contain unknown columns: {unresolved[:10]}")
        _copy_atomic(selected_columns_source, destination / "selected_columns.json")
    files = {
        name: sha256_file(destination / name)
        for name in (*REQUIRED_ATLAS_FILES, "atlas_definitions.json")
    }
    if selected_columns_source is not None:
        files["selected_columns.json"] = sha256_file(destination / "selected_columns.json")
    receipt = {
        "source_bundle_manifest_sha256": sha256_file(manifest_path),
        "destination": str(destination.resolve()),
        "files": files,
        "predictors": expected_width,
        "test_labels_used": False,
        "frozen": True,
    }
    atomic_json(destination / "staging_receipt.json", receipt)
    return receipt


def numeric_signature(values: np.ndarray) -> str:
    array = np.asarray(values, dtype="<f8")
    normalized = array.copy()
    normalized[np.isnan(normalized)] = np.nan
    normalized[normalized == 0.0] = 0.0
    digest = hashlib.sha256()
    digest.update(np.asarray(array.shape, dtype="<i8").tobytes())
    digest.update(np.isnan(array).tobytes())
    digest.update(normalized.tobytes(order="C"))
    return digest.hexdigest()


def seed_atlas_registry(
    staged_atlas: Path,
    output: Path,
    *,
    expected_width: int = ATLAS_WIDTH,
    expected_train_rows: int = TRAIN_ROWS,
    expected_test_rows: int = TEST_ROWS,
) -> dict[str, Any]:
    """Seed names, definitions, and exact numeric/formula/semantic fingerprints."""

    columns = json.loads((staged_atlas / "columns.json").read_text(encoding="utf-8"))
    definitions = json.loads(
        (staged_atlas / "atlas_definitions.json").read_text(encoding="utf-8")
    )
    if len(columns) != expected_width:
        raise ValueError(f"staged Atlas has {len(columns)} columns, expected {expected_width}")
    definition_by_name = {item["name"]: item for item in definitions}
    train = np.load(staged_atlas / "train.npy", mmap_mode="r", allow_pickle=False)
    test = np.load(staged_atlas / "test.npy", mmap_mode="r", allow_pickle=False)
    if train.shape != (expected_train_rows, expected_width) or test.shape != (
        expected_test_rows,
        expected_width,
    ):
        raise ValueError("staged Atlas matrices have invalid shapes")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    defined = 0
    with temporary.open("w", encoding="utf-8") as handle:
        for index, name in enumerate(columns):
            definition = definition_by_name.get(name)
            if definition is not None:
                defined += 1
            equation = str((definition or {}).get("formula") or f"frozen existing column {name}")
            interpretation = str(
                (definition or {}).get("interpretation") or f"frozen existing feature {name}"
            )
            combined = np.concatenate(
                (np.asarray(train[:, index], dtype=np.float64), np.asarray(test[:, index], dtype=np.float64))
            )
            record = {
                "name": name,
                "index": index,
                "source": "existing_809" if index < min(EXISTING_WIDTH, expected_width) else "atlas",
                "definition": definition,
                "numeric_signature": numeric_signature(combined),
                "formula_fingerprint": formula_fingerprint(equation),
                "semantic_fingerprint": semantic_fingerprint(interpretation, equation),
            }
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, output)
    receipt = {
        "columns": len(columns),
        "definitions": defined,
        "existing_809": min(EXISTING_WIDTH, expected_width),
        "numeric_signatures": len(columns),
        "formula_fingerprints": len(columns),
        "semantic_fingerprints": len(columns),
        "registry_sha256": sha256_file(output),
    }
    atomic_json(output.with_suffix(".receipt.json"), receipt)
    return receipt


def load_fingerprint_sets(records: Iterable[dict[str, Any]]) -> dict[str, set[str]]:
    result = {"names": set(), "numeric": set(), "formula": set(), "semantic": set()}
    for record in records:
        result["names"].add(str(record.get("name")))
        for key in ("numeric", "formula", "semantic"):
            value = record.get(f"{key}_signature" if key == "numeric" else f"{key}_fingerprint")
            if value:
                result[key].add(str(value))
    return result
