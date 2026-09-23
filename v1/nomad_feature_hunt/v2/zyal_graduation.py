"""Audit legacy ZYAL outputs and materialize bounded trusted-kernel candidates."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import time
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.feature_selection import mutual_info_regression

from nomad_crystal360.bakeoff import canonical_hash, verify_public_bundle
from nomad_crystal360.io import load_structures
from nomad_feature_hunt.ledger import sha256_file
from nomad_feature_hunt.schemas import extract_json_payload, validate_microfeature
from nomad_feature_hunt.security import static_check_generator

from .constants import DOMAIN_KERNELS, MAX_COLUMNS_PER_BASE_EQUATION
from .execution import invariant_structures
from .kernels import PrimitiveCache


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _parse_attempt(text: str) -> tuple[dict[str, Any] | None, bool, str | None]:
    try:
        value = json.loads(text)
        return (value if isinstance(value, dict) else None), True, None
    except json.JSONDecodeError as strict_error:
        try:
            value = extract_json_payload(text)
            return (
                value if isinstance(value, dict) else None,
                False,
                f"strict JSON: {strict_error}",
            )
        except (ValueError, json.JSONDecodeError) as legacy_error:
            return None, False, f"strict JSON: {strict_error}; legacy parse: {legacy_error}"


def _literal_generator_outputs(source: str) -> list[str]:
    patterns = (
        r"(?:out|feats|features)\s*\[\s*['\"]([^'\"]+)['\"]\s*\]",
        r"(?:out|feats|features)\.setdefault\(\s*['\"]([^'\"]+)['\"]",
    )
    values: set[str] = set()
    for pattern in patterns:
        values.update(re.findall(pattern, source))
    return sorted(values)


def _declared_expansion_width(expansion: Any) -> int:
    if not isinstance(expansion, list):
        return 0
    literal = len([value for value in expansion if str(value).strip(". ")])
    inferred = literal
    if any("..." in str(value) for value in expansion):
        numeric_suffixes = []
        for value in expansion:
            match = re.search(r"(\d+)(?!.*\d)", str(value))
            if match:
                numeric_suffixes.append(int(match.group(1)))
        if numeric_suffixes:
            largest = max(numeric_suffixes)
            inferred = max(inferred, largest + (1 if min(numeric_suffixes) == 0 else 0))
    return max(literal, inferred)


def audit_zyal_campaign(campaign_root: Path, output_path: Path) -> dict[str, Any]:
    """Inventory every immutable attempt; never execute or repair untrusted code."""

    database = campaign_root / "campaign.sqlite3"
    results_root = campaign_root / "queue/results"
    if not database.is_file() or not results_root.is_dir():
        raise FileNotFoundError("ZYAL campaign database or results tree is missing")
    attempts: list[dict[str, Any]] = []
    for path in sorted(results_root.glob("wave_*/attempt_*/*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        text = str(result.get("assistant_text", ""))
        payload, strict, parse_error = _parse_attempt(text)
        code = str(payload.get("generator_code", "")) if payload else ""
        microfeatures = payload.get("microfeatures", []) if payload else []
        if not isinstance(microfeatures, list):
            microfeatures = []
        schema_valid = sum(
            not validate_microfeature(feature)
            for feature in microfeatures
            if isinstance(feature, dict)
        )
        attempts.append(
            {
                "path": str(path.relative_to(campaign_root)),
                "role_id": str(result.get("id", path.stem)),
                "wave": path.parents[1].name,
                "attempt": path.parent.name,
                "router_success": result.get("success") is True,
                "strict_json": strict,
                "legacy_object_recovered": payload is not None and not strict,
                "parse_error": parse_error,
                "assistant_bytes": len(text.encode("utf-8")),
                "assistant_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "artifact_sha256": sha256_file(path),
                "declared_microfeatures": len(microfeatures),
                "schema_valid_microfeatures": schema_valid,
                "generator_bytes": len(code.encode("utf-8")),
                "literal_generator_outputs": _literal_generator_outputs(code),
                "static_generator_errors": static_check_generator(code) if code else [],
                "router_metadata": result.get("router_metadata"),
            }
        )

    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        concept_rows = connection.execute(
            "SELECT concept_id,domain,payload_json,payload_sha256 FROM concepts ORDER BY domain,concept_id"
        ).fetchall()
        matrix_count = int(connection.execute("SELECT COUNT(*) FROM matrices").fetchone()[0])
        microfeature_count = int(
            connection.execute("SELECT COUNT(*) FROM microfeatures").fetchone()[0]
        )
    concepts: list[dict[str, Any]] = []
    for row in concept_rows:
        payload = json.loads(row["payload_json"])
        expansion = payload.get("microfeature_expansion")
        inferred = _declared_expansion_width(expansion)
        concepts.append(
            {
                "concept_id": row["concept_id"],
                "domain": row["domain"],
                "name": payload.get("name"),
                "literal_expansion_entries": len(expansion) if isinstance(expansion, list) else 0,
                "declared_or_inferred_width": inferred,
                "bounded_width": min(inferred, MAX_COLUMNS_PER_BASE_EQUATION),
                "payload_sha256": row["payload_sha256"],
            }
        )

    implementers = [row for row in attempts if row["role_id"].startswith("implementer-")]
    summary = {
        "attempt_artifacts": len(attempts),
        "strict_json_attempts": sum(row["strict_json"] for row in attempts),
        "legacy_recovered_attempts": sum(row["legacy_object_recovered"] for row in attempts),
        "implementer_attempts": len(implementers),
        "implementer_declared_microfeatures": sum(
            row["declared_microfeatures"] for row in implementers
        ),
        "implementer_schema_valid_microfeatures": sum(
            row["schema_valid_microfeatures"] for row in implementers
        ),
        "implementer_literal_generator_outputs": len(
            {
                output
                for row in implementers
                for output in row["literal_generator_outputs"]
            }
        ),
        "accepted_concepts": len(concepts),
        "accepted_concepts_by_domain": dict(Counter(row["domain"] for row in concepts)),
        "literal_concept_expansions": sum(
            row["literal_expansion_entries"] for row in concepts
        ),
        "declared_or_inferred_concept_width": sum(
            row["declared_or_inferred_width"] for row in concepts
        ),
        "bounded_concept_width": sum(row["bounded_width"] for row in concepts),
        "controller_graduated_microfeatures": microfeature_count,
        "controller_graduated_matrices": matrix_count,
        "untrusted_code_executed": False,
        "test_labels_used": False,
    }
    report = {
        "summary": summary,
        "concepts": concepts,
        "attempts": attempts,
        "policy": {
            "legacy_parse_is_audit_only": True,
            "strict_json_required_for_graduation": True,
            "invalid_generators_are_negative_memory": True,
            "bounded_columns_per_base_equation": MAX_COLUMNS_PER_BASE_EQUATION,
        },
    }
    _atomic_json(output_path, report)
    return report


def _feature_signature(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values, dtype="<f4")
    missing = np.isnan(array)
    canonical = array.copy()
    canonical[missing] = 0.0
    digest = hashlib.sha256()
    digest.update(np.ascontiguousarray(missing).tobytes())
    digest.update(canonical.tobytes())
    return digest.hexdigest()


def _atlas_signatures(bundle: Path) -> dict[str, str]:
    train = np.load(bundle / "train.npy", mmap_mode="r", allow_pickle=False)
    test = np.load(bundle / "test.npy", mmap_mode="r", allow_pickle=False)
    columns = json.loads((bundle / "columns.json").read_text(encoding="utf-8"))
    signatures: dict[str, str] = {}
    for index, name in enumerate(columns):
        signature = _feature_signature(np.concatenate((train[:, index], test[:, index])))
        signatures.setdefault(signature, str(name))
    return signatures


def _unique_addition_names(
    train: pd.DataFrame,
    test: pd.DataFrame,
    names: list[str],
    seen_signatures: dict[str, str],
) -> tuple[list[str], list[dict[str, str]]]:
    accepted: list[str] = []
    rejected: list[dict[str, str]] = []
    for name in names:
        signature = _feature_signature(
            np.concatenate(
                (
                    train[name].to_numpy(dtype=np.float32),
                    test[name].to_numpy(dtype=np.float32),
                )
            )
        )
        duplicate = seen_signatures.get(signature)
        if duplicate is not None:
            rejected.append(
                {
                    "feature_id": name,
                    "reason": "exact_numeric_duplicate",
                    "duplicate_of": duplicate,
                }
            )
            continue
        seen_signatures[signature] = name
        accepted.append(name)
    return accepted, rejected


def _stage_public(source: Path, destination: Path) -> Path:
    if destination.exists():
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    shutil.copytree(source, temporary, copy_function=shutil.copy2)
    os.replace(temporary, destination)
    return destination


def _domain_schedule(domain: str) -> tuple[str, list[dict[str, Any]]]:
    # These controller-owned schedules were frozen by v2 before this graduation pass.
    from .controller import _approved_parameter_schedule, _required_output_schedule

    kernel = DOMAIN_KERNELS[domain]
    outputs = _required_output_schedule(kernel)
    schedule: list[dict[str, Any]] = []
    for slot in range(16):
        configurations = _approved_parameter_schedule(domain, slot)
        for output_index, output in enumerate(outputs):
            config_index = int(output["configuration_index"])
            operation = str(output["operation"])
            schedule.append(
                {
                    "feature_id": (
                        f"v2.{domain.lower()}.{kernel}.zyal-{slot:02d}."
                        f"c{config_index}.{output_index:02d}-{operation}"
                    ),
                    "slot": slot,
                    "configuration_index": config_index,
                    "configuration": configurations[config_index],
                    "operation": operation,
                }
            )
    if len(schedule) != 16 * 19 or len({row["feature_id"] for row in schedule}) != len(
        schedule
    ):
        raise AssertionError("trusted ZYAL schedule must contain 304 unique scalar attempts")
    return kernel, schedule


def _compute_domain(
    *,
    domain: str,
    structures: list[Any],
    schedule: list[dict[str, Any]],
    cache: PrimitiveCache,
    progress_label: str,
) -> np.ndarray:
    kernel = DOMAIN_KERNELS[domain]
    values = np.empty((len(structures), len(schedule)), dtype=np.float32)
    grouped: dict[tuple[int, int], list[tuple[int, str, dict[str, Any]]]] = {}
    for column, row in enumerate(schedule):
        key = (int(row["slot"]), int(row["configuration_index"]))
        grouped.setdefault(key, []).append(
            (column, str(row["operation"]), dict(row["configuration"]))
        )
    started = time.monotonic()
    for row_index, structure in enumerate(structures):
        for items in grouped.values():
            result = cache.compute(kernel, structure, items[0][2])
            for column, operation, _configuration in items:
                values[row_index, column] = result[operation]
        if (row_index + 1) % 100 == 0 or row_index + 1 == len(structures):
            elapsed = time.monotonic() - started
            print(
                json.dumps(
                    {
                        "event": "zyal-domain-progress",
                        "split": progress_label,
                        "domain": domain,
                        "rows": row_index + 1,
                        "total_rows": len(structures),
                        "elapsed_seconds": elapsed,
                    }
                ),
                flush=True,
            )
    return values


def _invariance_columns(
    *,
    domain: str,
    structures: list[Any],
    schedule: list[dict[str, Any]],
) -> dict[str, bool]:
    baseline_cache = PrimitiveCache()
    baseline = _compute_domain(
        domain=domain,
        structures=structures,
        schedule=schedule,
        cache=baseline_cache,
        progress_label="invariance-baseline",
    )
    passed = np.ones(len(schedule), dtype=bool)
    for invariant in (
        "translation",
        "rotation",
        "atom_permutation",
        "periodic_wrapping",
        "equivalent_cell",
    ):
        transformed = [invariant_structures(structure)[invariant] for structure in structures]
        candidate = _compute_domain(
            domain=domain,
            structures=transformed,
            schedule=schedule,
            cache=PrimitiveCache(),
            progress_label=f"invariance-{invariant}",
        )
        passed &= np.all(np.isclose(baseline, candidate, rtol=1e-6, atol=1e-8), axis=0)
    return {
        str(schedule[index]["feature_id"]): bool(value)
        for index, value in enumerate(passed)
    }


def materialize_zyal_concepts(
    *,
    campaign_root: Path,
    public_source: Path,
    atlas_bundle: Path,
    run_root: Path,
    domains: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Translate accepted ZYAL domains through trusted kernels and quarantine per scalar."""

    audit_path = run_root / "analysis/zyal-audit.json"
    audit = audit_zyal_campaign(campaign_root, audit_path)
    accepted_domains = tuple(sorted(audit["summary"]["accepted_concepts_by_domain"]))
    requested = domains or accepted_domains
    if any(domain not in accepted_domains for domain in requested):
        raise ValueError(
            "only domains with accepted ZYAL concepts may use the ZYAL graduation label"
        )
    public = _stage_public(public_source, run_root / "inputs/zyal-public")
    staged_atlas = _stage_public(atlas_bundle, run_root / "inputs/atlas")
    train_frame = pd.read_csv(public / "train.csv")
    test_frame = pd.read_csv(public / "test.csv")
    train_structures = load_structures(train_frame, public / "train_geometry")
    test_structures = load_structures(test_frame, public / "test_geometry")
    if len(train_structures) != 2_400 or len(test_structures) != 600:
        raise ValueError("ZYAL graduation requires exactly 2,400/600 structures")
    atlas_seen = _atlas_signatures(staged_atlas)
    v2_seen: dict[str, str] = {}
    concept_rows = audit["concepts"]
    receipts: dict[str, Any] = {}
    for domain in requested:
        output = run_root / f"matrices/zyal/{domain.lower()}"
        receipt_path = output / "receipt.json"
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if (
                sha256_file(output / "train.parquet") == receipt["train_sha256"]
                and sha256_file(output / "test.parquet") == receipt["test_sha256"]
            ):
                receipts[domain] = receipt
                v2_seen.update(receipt["accepted_signatures"])
                continue
            raise ValueError(f"existing {domain} ZYAL shard fails its receipt hashes")
        output.mkdir(parents=True, exist_ok=True)
        kernel, schedule = _domain_schedule(domain)
        cache = PrimitiveCache()
        started = time.monotonic()
        train_values = _compute_domain(
            domain=domain,
            structures=train_structures,
            schedule=schedule,
            cache=cache,
            progress_label="train",
        )
        test_values = _compute_domain(
            domain=domain,
            structures=test_structures,
            schedule=schedule,
            cache=cache,
            progress_label="test",
        )
        # A controller-private shuffled sample; no targets or test rows are involved.
        sample_positions = np.sort(
            np.random.default_rng(4219).choice(len(train_structures), size=64, replace=False)
        )
        invariance = _invariance_columns(
            domain=domain,
            structures=[train_structures[int(index)] for index in sample_positions],
            schedule=schedule,
        )
        rerun = _compute_domain(
            domain=domain,
            structures=[train_structures[int(index)] for index in sample_positions],
            schedule=schedule,
            cache=PrimitiveCache(),
            progress_label="deterministic-rerun",
        )
        deterministic = np.all(
            train_values[sample_positions] == rerun,
            axis=0,
        )
        accepted: list[int] = []
        rejected: list[dict[str, Any]] = []
        accepted_signatures: dict[str, str] = {}
        for index, row in enumerate(schedule):
            feature_id = str(row["feature_id"])
            values = np.concatenate((train_values[:, index], test_values[:, index]))
            if not np.isfinite(values).all():
                rejected.append({"feature_id": feature_id, "reason": "nonfinite"})
                continue
            if float(np.ptp(values)) == 0.0:
                rejected.append({"feature_id": feature_id, "reason": "constant"})
                continue
            if not bool(deterministic[index]):
                rejected.append({"feature_id": feature_id, "reason": "nondeterministic"})
                continue
            if not invariance[feature_id]:
                rejected.append({"feature_id": feature_id, "reason": "invariance_failure"})
                continue
            signature = _feature_signature(values)
            duplicate = atlas_seen.get(signature) or v2_seen.get(signature)
            if duplicate:
                rejected.append(
                    {
                        "feature_id": feature_id,
                        "reason": "exact_numeric_duplicate",
                        "duplicate_of": duplicate,
                    }
                )
                continue
            accepted.append(index)
            accepted_signatures[signature] = feature_id
            v2_seen[signature] = feature_id
        names = [str(schedule[index]["feature_id"]) for index in accepted]
        train_output = pd.DataFrame(train_values[:, accepted], columns=names)
        train_output.insert(0, "id", train_frame["id"].tolist())
        test_output = pd.DataFrame(test_values[:, accepted], columns=names)
        test_output.insert(0, "id", test_frame["id"].tolist())
        train_path = output / "train.parquet"
        test_path = output / "test.parquet"
        train_output.to_parquet(train_path, index=False)
        test_output.to_parquet(test_path, index=False)
        registry = [schedule[index] for index in accepted]
        _atomic_json(output / "registry.json", registry)
        receipt = {
            "domain": domain,
            "kernel": kernel,
            "source_concepts": [
                row["concept_id"] for row in concept_rows if row["domain"] == domain
            ],
            "translation": "accepted ZYAL concept domain to frozen v2 trusted-kernel schedule",
            "attempted_columns": len(schedule),
            "validated_columns": len(accepted),
            "quarantined_columns": len(rejected),
            "rejections": rejected,
            "invariance_structures": 64,
            "invariances": [
                "translation",
                "rotation",
                "atom_permutation",
                "periodic_wrapping",
                "equivalent_cell",
            ],
            "deterministic_rerun_structures": 64,
            "train_rows": len(train_output),
            "test_rows": len(test_output),
            "train_sha256": sha256_file(train_path),
            "test_sha256": sha256_file(test_path),
            "registry_sha256": sha256_file(output / "registry.json"),
            "accepted_signatures": accepted_signatures,
            "elapsed_seconds": time.monotonic() - started,
            "test_labels_used": False,
            "untrusted_generator_executed": False,
        }
        _atomic_json(receipt_path, receipt)
        receipts[domain] = receipt
    summary = {
        "domains": list(requested),
        "attempted_columns": sum(row["attempted_columns"] for row in receipts.values()),
        "validated_columns": sum(row["validated_columns"] for row in receipts.values()),
        "quarantined_columns": sum(row["quarantined_columns"] for row in receipts.values()),
        "receipts": receipts,
        "test_labels_used": False,
        "untrusted_generator_executed": False,
    }
    _atomic_json(run_root / "matrices/zyal/graduation-summary.json", summary)
    return summary


def _write_npy(path: Path, values: np.ndarray) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as output:
        np.save(output, values, allow_pickle=False)
    os.replace(temporary, path)


def _rank_augmented_features(
    *,
    augmented_bundle: Path,
    atlas_ranking_dir: Path,
    output_dir: Path,
    atlas_width: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    train = np.load(augmented_bundle / "train.npy", mmap_mode="r", allow_pickle=False)
    targets = np.load(augmented_bundle / "targets.npy", mmap_mode="r", allow_pickle=False)
    columns = json.loads((augmented_bundle / "columns.json").read_text(encoding="utf-8"))
    source = pd.read_parquet(augmented_bundle / "source_families.parquet")
    folds = np.load(
        augmented_bundle / "selection_folds.npy", mmap_mode="r", allow_pickle=False
    )
    additions = np.asarray(train[:, atlas_width:], dtype=np.float64)
    target_names = json.loads(
        (augmented_bundle / "targets.json").read_text(encoding="utf-8")
    )
    for target_index, target in enumerate(target_names):
        schemes: list[tuple[str, np.ndarray]] = [("", np.ones(len(train), dtype=bool))]
        schemes.extend(
            (f"_selection_fold_{fold}", folds != fold) for fold in range(2)
        )
        for suffix, training_mask in schemes:
            values = additions[training_mask]
            label = np.asarray(targets[training_mask, target_index], dtype=np.float64)
            mi = np.nan_to_num(
                mutual_info_regression(values, label, random_state=4219),
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )
            correlations = np.empty(values.shape[1], dtype=np.float64)
            for index in range(values.shape[1]):
                column = values[:, index]
                if float(np.ptp(column)) == 0.0:
                    correlations[index] = 0.0
                    continue
                statistic = float(spearmanr(column, label).statistic)
                correlations[index] = abs(statistic) if np.isfinite(statistic) else 0.0
            mi_percentile = rankdata(mi, method="average") / len(mi)
            correlation_percentile = rankdata(correlations, method="average") / len(
                correlations
            )
            new_score = 0.5 * mi_percentile + 0.5 * correlation_percentile
            old = pd.read_parquet(atlas_ranking_dir / f"ranking_{target}{suffix}.parquet")
            old_rows = pd.DataFrame(
                {
                    "feature_index": old["feature_index"].astype(int),
                    "feature": old["feature"].astype(str),
                    "source_family": old["source_family"].astype(str),
                    "feature_family": old["feature_family"].astype(str),
                    "selection_score": old["empirical_importance_percentile"].astype(float)
                    / 100.0,
                    "selection_metric": "atlas-fold-local-importance",
                }
            )
            new_source = source.iloc[atlas_width:].reset_index(drop=True)
            new_rows = pd.DataFrame(
                {
                    "feature_index": np.arange(atlas_width, len(columns), dtype=int),
                    "feature": columns[atlas_width:],
                    "source_family": new_source["source_family"].astype(str),
                    "feature_family": new_source["feature_family"].astype(str),
                    "selection_score": new_score,
                    "selection_metric": "fold-local-mi-spearman",
                }
            )
            ranking = pd.concat((old_rows, new_rows), ignore_index=True).sort_values(
                ["selection_score", "feature_index"], ascending=[False, True]
            )
            ranking.insert(0, "rank", np.arange(1, len(ranking) + 1))
            ranking.to_parquet(output_dir / f"ranking_{target}{suffix}.parquet", index=False)
            ranking.to_csv(output_dir / f"ranking_{target}{suffix}.csv", index=False)


def build_augmented_bundle(
    *,
    atlas_bundle: Path,
    atlas_ranking_dir: Path,
    zyal_matrix_root: Path,
    output_dir: Path,
    ranking_output_dir: Path,
) -> dict[str, Any]:
    """Append only receipt-valid ZYAL matrices and build discovery-only rankings."""

    atlas_manifest = verify_public_bundle(atlas_bundle)
    if output_dir.exists() and any(output_dir.iterdir()):
        existing = verify_public_bundle(output_dir)
        return existing
    output_dir.mkdir(parents=True, exist_ok=True)
    atlas_train = np.load(atlas_bundle / "train.npy", mmap_mode="r", allow_pickle=False)
    atlas_test = np.load(atlas_bundle / "test.npy", mmap_mode="r", allow_pickle=False)
    atlas_columns = json.loads((atlas_bundle / "columns.json").read_text(encoding="utf-8"))
    source = pd.read_parquet(atlas_bundle / "source_families.parquet")
    train_additions: list[np.ndarray] = []
    test_additions: list[np.ndarray] = []
    new_columns: list[str] = []
    receipts: dict[str, dict[str, Any]] = {}
    source_rows: list[dict[str, Any]] = []
    seen_signatures = _atlas_signatures(atlas_bundle)
    augmentation_rejections: list[dict[str, str]] = []
    for domain_dir in sorted(path for path in zyal_matrix_root.iterdir() if path.is_dir()):
        receipt = json.loads((domain_dir / "receipt.json").read_text(encoding="utf-8"))
        if sha256_file(domain_dir / "train.parquet") != receipt["train_sha256"]:
            raise ValueError(f"{domain_dir.name} train matrix fails its receipt")
        if sha256_file(domain_dir / "test.parquet") != receipt["test_sha256"]:
            raise ValueError(f"{domain_dir.name} test matrix fails its receipt")
        train = pd.read_parquet(domain_dir / "train.parquet")
        test = pd.read_parquet(domain_dir / "test.parquet")
        if train["id"].tolist() != np.load(atlas_bundle / "train_ids.npy").tolist():
            raise ValueError(f"{domain_dir.name} train row IDs are misaligned")
        if test["id"].tolist() != np.load(atlas_bundle / "test_ids.npy").tolist():
            raise ValueError(f"{domain_dir.name} test row IDs are misaligned")
        names = [str(column) for column in train.columns if column != "id"]
        if names != [str(column) for column in test.columns if column != "id"]:
            raise ValueError(f"{domain_dir.name} train/test columns differ")
        accepted_names, new_rejections = _unique_addition_names(
            train, test, names, seen_signatures
        )
        augmentation_rejections.extend(new_rejections)
        train_additions.append(train[accepted_names].to_numpy(dtype=np.float32))
        test_additions.append(test[accepted_names].to_numpy(dtype=np.float32))
        offset = len(atlas_columns) + len(new_columns)
        for index, name in enumerate(accepted_names):
            source_rows.append(
                {
                    "index": offset + index,
                    "feature": name,
                    "source_family": "zyal-v1-trusted-graduation",
                    "feature_family": str(receipt["domain"]),
                    "original_index": index,
                }
            )
        new_columns.extend(accepted_names)
        receipts[str(receipt["domain"])] = receipt
    if not new_columns:
        raise ValueError("no receipt-valid ZYAL columns are available to augment")
    combined_train = np.column_stack((atlas_train, *train_additions)).astype(np.float32)
    combined_test = np.column_stack((atlas_test, *test_additions)).astype(np.float32)
    output_arrays = {
        "train.npy": combined_train,
        "test.npy": combined_test,
        "targets.npy": np.load(atlas_bundle / "targets.npy", allow_pickle=False),
        "train_ids.npy": np.load(atlas_bundle / "train_ids.npy", allow_pickle=False),
        "test_ids.npy": np.load(atlas_bundle / "test_ids.npy", allow_pickle=False),
        "selection_folds.npy": np.load(
            atlas_bundle / "selection_folds.npy", allow_pickle=False
        ),
        "confirmation_folds.npy": np.load(
            atlas_bundle / "confirmation_folds.npy", allow_pickle=False
        ),
    }
    for name, values in output_arrays.items():
        _write_npy(output_dir / name, values)
    columns = [*atlas_columns, *new_columns]
    _atomic_json(output_dir / "columns.json", columns)
    shutil.copy2(atlas_bundle / "targets.json", output_dir / "targets.json")
    combined_source = pd.concat((source, pd.DataFrame(source_rows)), ignore_index=True)
    combined_source.to_parquet(output_dir / "source_families.parquet", index=False)
    combined_source.to_csv(output_dir / "source_families.csv", index=False)
    validation = {
        "atlas_columns": len(atlas_columns),
        "zyal_attempted_columns": sum(
            receipt["attempted_columns"] for receipt in receipts.values()
        ),
        "zyal_receipt_validated_columns": sum(
            receipt["validated_columns"] for receipt in receipts.values()
        ),
        "zyal_validated_columns": len(new_columns),
        "zyal_augmentation_quarantined_columns": len(augmentation_rejections),
        "zyal_augmentation_rejections": augmentation_rejections,
        "validated_width": len(columns),
        "train_rows": len(combined_train),
        "test_rows": len(combined_test),
        "row_ids_aligned": True,
        "train_test_columns_aligned": True,
        "test_labels_used": False,
    }
    _atomic_json(output_dir / "validation_report.json", validation)
    names = [
        *output_arrays,
        "columns.json",
        "targets.json",
        "source_families.parquet",
        "source_families.csv",
        "validation_report.json",
    ]
    files = {
        name: {
            "sha256": sha256_file(output_dir / name),
            "bytes": (output_dir / name).stat().st_size,
        }
        for name in names
    }
    identity = {
        "files": files,
        "train_rows": len(combined_train),
        "test_rows": len(combined_test),
        "predictors": len(columns),
        "targets": json.loads((output_dir / "targets.json").read_text()),
        "selection_folds": 2,
        "confirmation_folds": 5,
        "fold_seed": 4219,
        "contains_test_targets": False,
    }
    manifest = {
        **identity,
        "bundle_sha256": canonical_hash(identity),
        "bundle_mode": "atlas-plus-zyal-v2",
        "input_hashes": {
            "atlas_bundle": atlas_manifest["bundle_sha256"],
            **{
                f"zyal_{domain}": receipt["registry_sha256"]
                for domain, receipt in receipts.items()
            },
        },
        "test_labels_used": False,
    }
    _atomic_json(output_dir / "bundle_manifest.json", manifest)
    verify_public_bundle(output_dir)
    _rank_augmented_features(
        augmented_bundle=output_dir,
        atlas_ranking_dir=atlas_ranking_dir,
        output_dir=ranking_output_dir,
        atlas_width=len(atlas_columns),
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--materialize", action="store_true")
    parser.add_argument("--public-root", type=Path)
    parser.add_argument("--atlas-bundle", type=Path)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--domains", nargs="*")
    parser.add_argument("--augment", action="store_true")
    parser.add_argument("--atlas-ranking-dir", type=Path)
    parser.add_argument("--zyal-matrix-root", type=Path)
    parser.add_argument("--augmented-output", type=Path)
    parser.add_argument("--ranking-output", type=Path)
    args = parser.parse_args()
    if args.augment:
        required = (
            args.atlas_bundle,
            args.atlas_ranking_dir,
            args.zyal_matrix_root,
            args.augmented_output,
            args.ranking_output,
        )
        if any(value is None for value in required):
            parser.error(
                "--augment requires --atlas-bundle, --atlas-ranking-dir, "
                "--zyal-matrix-root, --augmented-output, and --ranking-output"
            )
        report = build_augmented_bundle(
            atlas_bundle=args.atlas_bundle.resolve(),
            atlas_ranking_dir=args.atlas_ranking_dir.resolve(),
            zyal_matrix_root=args.zyal_matrix_root.resolve(),
            output_dir=args.augmented_output.resolve(),
            ranking_output_dir=args.ranking_output.resolve(),
        )
    elif args.materialize:
        if args.public_root is None or args.atlas_bundle is None or args.run_root is None:
            parser.error("--materialize requires --public-root, --atlas-bundle, and --run-root")
        report = materialize_zyal_concepts(
            campaign_root=args.campaign_root.resolve(),
            public_source=args.public_root.resolve(),
            atlas_bundle=args.atlas_bundle.resolve(),
            run_root=args.run_root.resolve(),
            domains=tuple(args.domains) if args.domains else None,
        )
    else:
        report = audit_zyal_campaign(args.campaign_root.resolve(), args.output.resolve())["summary"]
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
