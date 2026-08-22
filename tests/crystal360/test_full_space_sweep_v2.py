from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import pytest

from nomad_feature_hunt.v2.full_space_sweep import (
    DISCOVERY_FOLDS,
    GENERATIONS,
    POPULATION_SIZE,
    PERCENTILES,
    SWEEP_SEEDS,
    TARGETS,
    Settings,
    _complete_phase,
    _remote_gpu_idle,
    _run_confirmation,
    _run_cutoffs,
    _run_genetic,
    _run_importance,
    _run_report,
    atomic_json,
    build_full_space_bundle,
    cache_identity,
    canonical_hash,
    deterministic_ga_history,
    importance_tables,
    interpolation_counts,
    make_importance_chunks,
    make_importance_jobs,
    normalize_importance,
    percentile_feature_sets,
    percentile_thresholds,
    prohibit_test_labels,
    sha256_file,
    status,
    verify_full_space_bundle,
)


@pytest.mark.parametrize(
    ("inventory", "expected"),
    [
        ("NVIDIA GeForce RTX 3090, 1, 0\n", True),
        ("NVIDIA GeForce RTX 4090, 512, 9\n", True),
        ("NVIDIA A100-SXM4-80GB, 1, 0\n", False),
        ("NVIDIA GeForce RTX 3090, 1024, 0\n", False),
        ("NVIDIA GeForce RTX 4090, 1, 10\n", False),
    ],
)
def test_remote_gpu_idle_accepts_only_idle_supported_gpus(
    monkeypatch: pytest.MonkeyPatch, inventory: str, expected: bool
) -> None:
    monkeypatch.setattr(
        "nomad_feature_hunt.v2.full_space_sweep.subprocess.check_output",
        lambda *_args, **_kwargs: inventory,
    )
    assert _remote_gpu_idle("worker") is expected


def _write_npy(path: Path, values: np.ndarray) -> dict[str, object]:
    np.save(path, values, allow_pickle=False)
    return {"sha256": sha256_file(path), "bytes": path.stat().st_size}


def _baseline_bundle(path: Path) -> Path:
    path.mkdir()
    rows, test_rows, width = 2_400, 600, 4
    sequence = np.arange(rows + test_rows, dtype=np.float32)
    all_values = np.column_stack(
        [sequence, sequence**2, sequence, np.ones(rows + test_rows, dtype=np.float32)]
    ).astype(np.float32)
    arrays = {
        "train.npy": all_values[:rows],
        "test.npy": all_values[rows:],
        "targets.npy": np.column_stack(
            [np.linspace(0.1, 1.0, rows), np.linspace(0.2, 2.0, rows)]
        ),
        "train_ids.npy": np.arange(1, rows + 1),
        "test_ids.npy": np.arange(rows + 1, rows + test_rows + 1),
        "selection_folds.npy": np.arange(rows, dtype=np.int8) % 2,
        "confirmation_folds.npy": np.arange(rows, dtype=np.int8) % 5,
    }
    files = {name: _write_npy(path / name, values) for name, values in arrays.items()}
    columns = ["b0", "b1", "b0-copy", "b-constant"]
    (path / "columns.json").write_text(json.dumps(columns), encoding="utf-8")
    (path / "targets.json").write_text(json.dumps(list(TARGETS)), encoding="utf-8")
    source = pd.DataFrame(
        {
            "index": np.arange(width),
            "feature": columns,
            "source_family": ["existing_809"] * width,
            "feature_family": ["fixture"] * width,
            "original_index": np.arange(width),
        }
    )
    source.to_parquet(path / "source_families.parquet", index=False)
    source.to_csv(path / "source_families.csv", index=False)
    for name in ("columns.json", "targets.json", "source_families.parquet", "source_families.csv"):
        files[name] = {"sha256": sha256_file(path / name), "bytes": (path / name).stat().st_size}
    identity = {
        "files": files,
        "train_rows": rows,
        "test_rows": test_rows,
        "predictors": width,
        "targets": list(TARGETS),
        "selection_folds": 2,
        "confirmation_folds": 5,
        "fold_seed": 4219,
        "contains_test_targets": False,
    }
    manifest = {
        **identity,
        "bundle_sha256": canonical_hash(identity),
        "test_labels_used": False,
    }
    (path / "bundle_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _recent_campaign(
    path: Path, *, misaligned_columns: bool = False, misaligned_ids: bool = False
) -> Path:
    matrix = path / "matrices/validated/epoch-01/spec-a"
    matrix.mkdir(parents=True)
    train_values = pd.DataFrame(
        {
            "id": np.roll(np.arange(1, 2_401), 1)
            if misaligned_ids
            else np.arange(1, 2_401),
            "r0": np.sin(np.arange(2_400, dtype=np.float32) / 17),
            "r-constant": np.full(2_400, 3.0, dtype=np.float32),
        }
    )
    test_values = pd.DataFrame(
        {
            "id": np.arange(2_401, 3_001),
            "r0": np.sin(np.arange(2_400, 3_000, dtype=np.float32) / 17),
            "r-constant": np.full(600, 3.0, dtype=np.float32),
        }
    )
    train_values.to_parquet(matrix / "train.parquet", index=False)
    test_values.to_parquet(matrix / "test.parquet", index=False)
    accepted = (
        ["r-constant", "r0"] if misaligned_columns else ["r0", "r-constant"]
    )
    receipt = {
        "accepted_columns": accepted,
        "numeric_signatures": {name: f"signature-{name}" for name in accepted},
        "epoch": 1,
        "domain": "D01",
        "family_id": "fixture-family",
        "spec_id": "spec-a",
        "train_rows": 2_400,
        "test_rows": 600,
        "train_sha256": sha256_file(matrix / "train.parquet"),
        "test_sha256": sha256_file(matrix / "test.parquet"),
        "test_labels_used": False,
    }
    (matrix / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    with sqlite3.connect(path / "campaign.sqlite3") as connection:
        connection.execute(
            "CREATE TABLE columns (feature_id TEXT, novel INTEGER, valid INTEGER)"
        )
        connection.executemany(
            "INSERT INTO columns VALUES (?,1,1)", [("r0",), ("r-constant",)]
        )
    return path


def _hyperion_manifest(path: Path) -> Path:
    path.mkdir()
    recent_train = np.sin(np.arange(2_400, dtype=np.float32) / 17)
    recent_test = np.sin(np.arange(2_400, 3_000, dtype=np.float32) / 17)
    matrices = {
        "cellmat_train": np.column_stack(
            [recent_train, np.cos(np.arange(2_400, dtype=np.float32) / 13)]
        ),
        "cellmat_test": np.column_stack(
            [recent_test, np.cos(np.arange(2_400, 3_000, dtype=np.float32) / 13)]
        ),
        "embedding_train": np.sqrt(np.arange(2_400, dtype=np.float32) + 1)[:, None],
        "embedding_test": np.sqrt(np.arange(2_400, 3_000, dtype=np.float32) + 1)[:, None],
    }
    files = {}
    for role, values in matrices.items():
        matrix_path = path / f"{role}.npy"
        np.save(matrix_path, values.astype(np.float32), allow_pickle=False)
        files[role] = {
            "path": matrix_path.name,
            "role": role,
            "sha256": sha256_file(matrix_path),
            "shape": list(values.shape),
        }
    manifest = path / "manifest.json"
    manifest.write_text(json.dumps({"files": files}), encoding="utf-8")
    return manifest


def _ranking(width: int, shift: int = 0) -> pd.DataFrame:
    order = np.roll(np.arange(width), shift)
    values = np.linspace(1.0, 0.01, width)
    return pd.DataFrame(
        {
            "rank": np.arange(1, width + 1),
            "feature_index": order,
            "global_index": order,
            "feature_id": [f"f{index}" for index in order],
            "mean_relative_importance": values,
            "importance_std": np.zeros(width),
        }
    )


def _full_sweep_bundle(path: Path, width: int = 607) -> Path:
    path.mkdir(parents=True)
    registry = pd.DataFrame(
        {
            "global_index": np.arange(width),
            "feature_id": [f"feature-{index}" for index in range(width)],
            "source": ["fixture"] * width,
            "source_partition": ["fixture"] * width,
            "source_index": np.arange(width),
            "epoch": [None] * width,
            "domain": ["D01"] * width,
            "family": ["fixture-family"] * width,
            "spec_id": [None] * width,
            "receipt": [None] * width,
            "numeric_signature": [f"sig-{index}" for index in range(width)],
            "source_hashes_json": ["{}"] * width,
        }
    )
    registry.to_parquet(path / "feature_registry.parquet", index=False)
    registry.to_csv(path / "feature_registry.csv", index=False)
    arrays = {
        "train.npy": np.zeros((10, width), dtype=np.float32),
        "test.npy": np.zeros((2, width), dtype=np.float32),
        "targets.npy": np.ones((10, 2), dtype=np.float64),
        "train_ids.npy": np.arange(10),
        "test_ids.npy": np.arange(10, 12),
        "discovery_folds.npy": np.arange(10, dtype=np.int8) % 5,
    }
    files = {name: _write_npy(path / name, values) for name, values in arrays.items()}
    json_files = {
        "columns.json": [f"feature-{index}" for index in range(width)],
        "targets.json": list(TARGETS),
        "duplicate_mappings.json": [],
        "quarantine.json": [],
        "source_maps.json": {"fixture": {str(index): index for index in range(width)}},
        "hyperion_positional_provenance.json": {"accepted": True},
    }
    for name, value in json_files.items():
        atomic_json(path / name, value)
    for name in [*json_files, "feature_registry.parquet", "feature_registry.csv"]:
        files[name] = {"sha256": sha256_file(path / name), "bytes": (path / name).stat().st_size}
    identity = {
        "files": files,
        "train_rows": 10,
        "test_rows": 2,
        "predictors": width,
        "targets": list(TARGETS),
        "discovery_folds": 5,
        "discovery_fold_seed": 4219,
        "contains_test_targets": False,
    }
    atomic_json(
        path / "bundle_manifest.json",
        {
            **identity,
            "bundle_sha256": canonical_hash(identity),
            "pre_dedup_union": width,
            "expected_union": width,
            "duplicates_mapped": 0,
            "quarantined": 0,
            "test_labels_used": False,
        },
    )
    return path


def test_fixed_chunks_cover_once_and_only_final_chunk_has_context() -> None:
    for seed in SWEEP_SEEDS:
        chunks = make_importance_chunks(607, seed)
        primary = [index for chunk in chunks for index in chunk.primary_columns]
        assert sorted(primary) == list(range(607))
        assert all(len(chunk.columns) == len(set(chunk.columns)) == 300 for chunk in chunks)
        assert all(not chunk.context_columns for chunk in chunks[:-1])
        assert len(chunks[-1].primary_columns) == 7
        assert len(chunks[-1].context_columns) == 293


def test_importance_has_25_observations_normalizes_and_preserves_indices() -> None:
    width = 607
    jobs = make_importance_jobs(width, targets=(TARGETS[0],))
    assert len(jobs) == DISCOVERY_FOLDS * len(SWEEP_SEEDS) * 3
    results = [(job, {"importance": np.arange(1, 301).tolist()}) for job in jobs]
    registry = pd.DataFrame(
        {
            "global_index": np.arange(width),
            "feature_id": [f"f{index}" for index in range(width)],
            "source": ["fixture"] * width,
            "source_index": np.arange(width),
            "epoch": [None] * width,
            "domain": ["D01"] * width,
            "family": ["family"] * width,
        }
    )
    aggregate, folds, observations = importance_tables(results, registry)
    assert observations.groupby(["target", "feature_index"]).size().eq(25).all()
    assert set(aggregate[TARGETS[0]]["global_index"]) == set(range(width))
    assert aggregate[TARGETS[0]]["globally_normalized_importance_share"].sum() == pytest.approx(1)
    assert aggregate[TARGETS[0]].iloc[0]["empirical_importance_percentile"] == 100
    assert all(ranking["observations"].eq(5).all() for ranking in folds.values())
    assert normalize_importance(np.ones(300)).sum() == pytest.approx(1)


def test_percentiles_are_nested_include_boundary_ties_and_interpolation_is_bounded() -> None:
    ranking = _ranking(100)
    ranking.loc[48:52, "mean_relative_importance"] = ranking.loc[50, "mean_relative_importance"]
    thresholds = percentile_thresholds(ranking)
    assert thresholds["percentile_label"].tolist() == [f"p{value:g}" for value in PERCENTILES]
    sets = percentile_feature_sets(ranking)
    labels = list(sets)
    assert all(set(sets[right]).issubset(sets[left]) for left, right in zip(labels, labels[1:]))
    assert len(sets["p50"]) >= 50
    counts = interpolation_counts({10: 0.3, 30: 0.2, 70: 0.25}, feature_count=80)
    assert counts and all(1 <= count <= 80 for count in counts)
    edge = interpolation_counts({10: 0.1, 30: 0.2, 70: 0.3}, feature_count=80)
    assert all(1 <= count <= 80 for count in edge)


def test_ga_evolution_is_deterministic_and_terminal_24_by_10() -> None:
    aggregate = _ranking(160)
    folds = [_ranking(160, shift) for shift in (1, -2, 3, -4, 5)]
    named = {
        "full-union": list(range(160)),
        "recent-only-union": list(range(40, 160)),
        "existing-809-control": list(range(100)),
        "p90": list(range(16)),
    }

    def score(genome) -> float:
        return len(genome.columns) / 10_000 + sum(genome.columns[:8]) / 1_000_000

    first = deterministic_ga_history(
        target=TARGETS[0],
        aggregate_ranking=aggregate,
        fold_rankings=folds,
        named_sets=named,
        score=score,
        seed=31,
    )
    second = deterministic_ga_history(
        target=TARGETS[0],
        aggregate_ranking=aggregate,
        fold_rankings=folds,
        named_sets=named,
        score=score,
        seed=31,
    )
    assert [(row["genome_id"], row["generation"]) for row in first] == [
        (row["genome_id"], row["generation"]) for row in second
    ]
    assert len(first) == POPULATION_SIZE * GENERATIONS
    assert Counter(row["generation"] for row in first) == Counter(
        {generation: POPULATION_SIZE for generation in range(GENERATIONS)}
    )


def test_bundle_deduplicates_quarantines_and_accounts_for_hyperion(tmp_path: Path) -> None:
    baseline = _baseline_bundle(tmp_path / "baseline")
    recent = _recent_campaign(tmp_path / "recent")
    hyperion = _hyperion_manifest(tmp_path / "hyperion")
    output = tmp_path / "bundle"
    manifest = build_full_space_bundle(
        baseline_bundle=baseline,
        recent_root=recent,
        hyperion_manifest=hyperion,
        output_dir=output,
        expected_baseline=4,
        expected_recent=2,
        expected_cellmat=2,
        expected_embedding=1,
    )
    assert manifest["pre_dedup_union"] == 9
    assert manifest["predictors"] == 5
    assert manifest["duplicates_mapped"] == 2
    assert manifest["quarantined"] == 2
    assert verify_full_space_bundle(output)["bundle_sha256"] == manifest["bundle_sha256"]
    duplicates = json.loads((output / "duplicate_mappings.json").read_text())
    assert {row["feature_id"] for row in duplicates} == {"b0-copy", "hyperion_cellmat_000"}
    quarantine = json.loads((output / "quarantine.json").read_text())
    assert {row["reason"] for row in quarantine} == {"constant"}
    provenance = json.loads((output / "hyperion_positional_provenance.json").read_text())
    assert provenance["accepted"] is True
    assert np.load(output / "train.npy").shape == (2_400, 5)


def test_recent_receipt_hash_and_alignment_drift_are_rejected(tmp_path: Path) -> None:
    baseline = _baseline_bundle(tmp_path / "baseline")
    recent = _recent_campaign(tmp_path / "recent", misaligned_columns=True)
    hyperion = _hyperion_manifest(tmp_path / "hyperion")
    with pytest.raises(Exception, match="receipt/column alignment drift"):
        build_full_space_bundle(
            baseline_bundle=baseline,
            recent_root=recent,
            hyperion_manifest=hyperion,
            output_dir=tmp_path / "bundle",
            expected_baseline=4,
            expected_recent=2,
            expected_cellmat=2,
            expected_embedding=1,
        )


def test_recent_row_ids_and_hash_drift_are_rejected(tmp_path: Path) -> None:
    baseline = _baseline_bundle(tmp_path / "baseline")
    recent = _recent_campaign(tmp_path / "recent", misaligned_ids=True)
    hyperion = _hyperion_manifest(tmp_path / "hyperion")
    with pytest.raises(Exception, match="row IDs do not match Atlas order"):
        build_full_space_bundle(
            baseline_bundle=baseline,
            recent_root=recent,
            hyperion_manifest=hyperion,
            output_dir=tmp_path / "row-bundle",
            expected_baseline=4,
            expected_recent=2,
            expected_cellmat=2,
            expected_embedding=1,
        )
    receipt_path = next(recent.glob("matrices/validated/epoch-*/**/receipt.json"))
    receipt = json.loads(receipt_path.read_text())
    receipt["train_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(Exception, match="recent train hash drift"):
        build_full_space_bundle(
            baseline_bundle=baseline,
            recent_root=recent,
            hyperion_manifest=hyperion,
            output_dir=tmp_path / "hash-bundle",
            expected_baseline=4,
            expected_recent=2,
            expected_cellmat=2,
            expected_embedding=1,
        )


def test_test_label_inputs_cache_identity_and_phase_resume_bookkeeping(tmp_path: Path) -> None:
    with pytest.raises(Exception, match="test-label"):
        prohibit_test_labels([tmp_path / "labeled_test.csv"])
    job = {
        "kind": "screen",
        "target": TARGETS[0],
        "columns": [1, 2],
        "fold": 0,
        "cv_seed": 4219,
        "model_seed": 4219,
        "iterations": 150,
        "job_id": "first",
        "stage": "one",
    }
    same_fit = {**job, "job_id": "second", "stage": "two"}
    assert cache_identity(bundle_hash="bundle", worker_hash="worker", job=job) == cache_identity(
        bundle_hash="bundle", worker_hash="worker", job=same_fit
    )
    changed = {**job, "fold": 1}
    assert cache_identity(bundle_hash="bundle", worker_hash="worker", job=job) != cache_identity(
        bundle_hash="bundle", worker_hash="worker", job=changed
    )
    settings = Settings("fixture", inbox=tmp_path / "inbox")
    settings.run_root.mkdir(parents=True)
    _complete_phase(settings, "prepare", {"ok": True})
    _complete_phase(settings, "prepare", {"ok": True})
    assert status(settings)["completed_phases"] == ["prepare"]
    assert status(settings)["next_phase"] == "importance"


def test_all_resumable_phases_reach_a_reproducible_report_with_fake_fits(
    tmp_path: Path, monkeypatch
) -> None:
    settings = Settings("dry-run", inbox=tmp_path / "inbox")
    settings.run_root.mkdir(parents=True)
    _full_sweep_bundle(settings.bundle)
    settings.worker.write_text("fixture-worker", encoding="utf-8")
    atomic_json(
        settings.run_root / "protocol.json",
        {
            "bundle_sha256": verify_full_space_bundle(settings.bundle)["bundle_sha256"],
            "worker_sha256": sha256_file(settings.worker),
            "test_labels_used": False,
        },
    )
    _complete_phase(settings, "prepare", {"fixture": True})

    controls = {
        target: {
            "full-union": list(range(607)),
            "recent-only-union": list(range(200, 607)),
            "existing-809-control": list(range(120)),
            "atlas-winner-control": list(range(90)),
            "prior-v2-winner-control": list(range(140)),
        }
        for target in TARGETS
    }
    monkeypatch.setattr(
        "nomad_feature_hunt.v2.full_space_sweep.load_control_sets",
        lambda _settings: controls,
    )

    class FakeScheduler:
        def run(self, _stage, jobs):
            rows = []
            for job in jobs:
                if job["kind"] == "importance":
                    result = {"importance": np.arange(1, 301, dtype=float).tolist()}
                else:
                    stable = int(canonical_hash(job["columns"])[:6], 16) / 16**6
                    result = {
                        "score": 0.04
                        + len(job["columns"]) / 10_000_000
                        + int(job["fold"]) / 1_000_000
                        + stable / 10_000_000,
                        "elapsed_seconds": 0.0,
                    }
                rows.append((job, result))
            return rows

    scheduler = FakeScheduler()
    _run_importance(settings, scheduler)
    assert status(settings)["next_phase"] == "cutoffs"
    _run_cutoffs(settings, scheduler)
    assert status(settings)["next_phase"] == "genetic"
    _run_genetic(settings, scheduler)
    assert status(settings)["next_phase"] == "confirmation"
    confirmation = _run_confirmation(settings, scheduler)
    assert set(confirmation["winners"]) == set(TARGETS)
    report = _run_report(settings)
    assert report["final_mean_rmsle"] == pytest.approx(
        np.mean([report["winners"][target]["sealed_mean_rmsle"] for target in TARGETS])
    )
    assert status(settings)["next_phase"] is None
