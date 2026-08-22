from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import atlas_bakeoff_worker as worker
from nomad_crystal360.bakeoff import (
    AppendOnlyEvents,
    ResultCache,
    build_public_bundle,
    canonical_hash,
    importance_tables,
    make_importance_chunks,
    make_importance_jobs,
    normalize_importance,
    percentile_feature_sets,
    percentile_thresholds,
    refinement_counts,
    score_frozen_submission_once,
    select_confirmed_cut,
    select_confirmed_view,
    sha256_file,
    verify_public_bundle,
)
from nomad_crystal360.constants import TARGETS


def _save(path: Path, values: np.ndarray) -> str:
    np.save(path, values, allow_pickle=False)
    return sha256_file(path)


def _hyperion_fixture(tmp_path: Path, *, misaligned: bool = False) -> tuple[Path, Path, Path]:
    atlas = tmp_path / "atlas"
    ids = tmp_path / "ids"
    hyperion = tmp_path / "hyperion"
    atlas.mkdir()
    ids.mkdir()
    hyperion.mkdir()
    train_atlas = pd.DataFrame(
        {
            "atlas_0": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            "atlas_1": [2.0, 4.0, 8.0, 16.0, 32.0, 64.0],
            "atlas_2": [1.0, 4.0, 9.0, 16.0, 25.0, 36.0],
            "atlas_3": [3.0, 1.0, 4.0, 2.0, 5.0, 9.0],
        }
    )
    test_atlas = pd.DataFrame(
        {
            "atlas_0": [6.0, 7.0],
            "atlas_1": [128.0, 256.0],
            "atlas_2": [49.0, 64.0],
            "atlas_3": [6.0, 8.0],
        }
    )
    train_atlas.to_parquet(atlas / "train_predictors_atlas.parquet", index=False)
    test_atlas.to_parquet(atlas / "test_predictors_atlas.parquet", index=False)
    pd.DataFrame(
        {
            TARGETS[0]: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            TARGETS[1]: [1.1, 1.2, 1.3, 1.4, 1.5, 1.6],
        }
    ).to_parquet(atlas / "public_targets.parquet", index=False)
    pd.DataFrame({"id": [10, 11, 12, 13, 14, 15]}).to_csv(
        ids / "train_row_ids.csv", index=False
    )
    pd.DataFrame({"id": [20, 21]}).to_csv(ids / "test_row_ids.csv", index=False)

    cell_train = np.array(
        [[0, 5, 10], [1, 7, 20], [2, 9, 40], [3, 11, 80], [4, 13, 160], [5, 15, 320]],
        dtype=np.float32,
    )
    cell_test = np.array([[6, 17, 640], [7, 19, 1280]], dtype=np.float32)
    embedding_train = np.array(
        [[2, 3], [3, 5], [5, 8], [8, 13], [13, 21], [21, 34]], dtype=np.float32
    )
    embedding_test = np.array([[34, 55], [55, 89]], dtype=np.float32)
    files = {
        "cellmat_train": cell_train,
        "cellmat_test": cell_test,
        "embedding_train": embedding_train,
        "embedding_test": embedding_test,
        "cellmat_train_mean": cell_train.mean(axis=0, keepdims=True),
        "embedding_test_mean": embedding_test.mean(axis=0, keepdims=True),
    }
    manifest_files: dict[str, dict[str, str]] = {}
    for role, values in files.items():
        path = hyperion / f"{role}.npy"
        digest = _save(path, values)
        manifest_files[role] = {"path": path.name, "sha256": digest, "role": role}
    train_sidecar = hyperion / "train_ids.csv"
    test_sidecar = hyperion / "test_ids.csv"
    pd.DataFrame(
        {"id": [11, 10, 12, 13, 14, 15] if misaligned else [10, 11, 12, 13, 14, 15]}
    ).to_csv(train_sidecar, index=False)
    pd.DataFrame({"id": [20, 21]}).to_csv(test_sidecar, index=False)
    manifest = {
        "files": manifest_files,
        "row_ids": {
            "train": {"path": train_sidecar.name, "sha256": sha256_file(train_sidecar)},
            "test": {"path": test_sidecar.name, "sha256": sha256_file(test_sidecar)},
        },
    }
    manifest_path = hyperion / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return atlas, ids, manifest_path


def test_public_bundle_validates_hashes_alignment_quality_and_deduplicates(tmp_path: Path):
    atlas, ids, hyperion_manifest = _hyperion_fixture(tmp_path)
    output = tmp_path / "bundle"
    manifest = build_public_bundle(
        atlas_dir=atlas,
        row_id_dir=ids,
        hyperion_manifest=hyperion_manifest,
        output_dir=output,
        expected_atlas_width=4,
        expected_cellmat_width=3,
        expected_embedding_width=2,
    )

    assert manifest["predictors"] == 8
    assert manifest["contains_test_targets"] is False
    assert verify_public_bundle(output)["bundle_sha256"] == manifest["bundle_sha256"]
    report = json.loads((output / "validation_report.json").read_text())
    assert report["duplicates_removed"] == [
        {"duplicate_of": "atlas_0", "feature": "hyperion_cellmat_000"}
    ]
    assert len(report["ignored_manifest_files"]) == 2
    assert "hyperion_cellmat_001" in json.loads((output / "columns.json").read_text())
    assert np.load(output / "train.npy").shape == (6, 8)
    assert not any("test_target" in name for name in manifest["files"])


def test_public_bundle_rejects_unproven_row_alignment(tmp_path: Path):
    atlas, ids, hyperion_manifest = _hyperion_fixture(tmp_path, misaligned=True)
    with pytest.raises(ValueError, match="row ids do not match"):
        build_public_bundle(
            atlas_dir=atlas,
            row_id_dir=ids,
            hyperion_manifest=hyperion_manifest,
            output_dir=tmp_path / "bundle",
            expected_atlas_width=4,
            expected_cellmat_width=3,
            expected_embedding_width=2,
        )


def test_public_bundle_can_stage_atlas_only(tmp_path: Path):
    atlas, ids, _hyperion_manifest = _hyperion_fixture(tmp_path)
    output = tmp_path / "atlas_only_bundle"
    manifest = build_public_bundle(
        atlas_dir=atlas,
        row_id_dir=ids,
        hyperion_manifest=None,
        output_dir=output,
        expected_atlas_width=4,
    )

    assert manifest["bundle_mode"] == "atlas_only"
    assert manifest["predictors"] == 4
    assert "hyperion_manifest" not in manifest["input_hashes"]
    assert np.load(output / "train.npy").shape == (6, 4)
    assert json.loads((output / "validation_report.json").read_text())["validated_width"] == 4


def test_importance_chunks_have_fixed_width_primary_coverage_and_six_observations():
    feature_count = 607
    for seed in (1701, 2909, 4219):
        chunks = make_importance_chunks(feature_count, seed)
        primary = [index for chunk in chunks for index in chunk.primary_columns]
        assert sorted(primary) == list(range(feature_count))
        assert all(len(chunk.columns) == len(set(chunk.columns)) == 300 for chunk in chunks)
        assert len(chunks[-1].primary_columns) == 7
        assert len(chunks[-1].context_columns) == 293

    jobs = make_importance_jobs(feature_count)
    source = pd.DataFrame(
        {
            "index": np.arange(feature_count),
            "feature": [f"feature_{index:03d}" for index in range(feature_count)],
            "source_family": ["atlas"] * feature_count,
            "feature_family": ["atlas"] * feature_count,
        }
    )
    raw_importance = np.arange(1, 301, dtype=float)
    results = [(job, {"importance": raw_importance.tolist()}) for job in jobs]
    rankings, fold_rankings, observations = importance_tables(results, source)

    assert observations.groupby(["target", "feature_index"]).size().eq(6).all()
    assert "within_chunk_rank" in observations
    assert all(len(ranking) == feature_count for ranking in rankings.values())
    assert all(
        ranking["globally_normalized_importance_share"].sum()
        == pytest.approx(1.0, abs=1e-12)
        for ranking in rankings.values()
    )
    assert all("median_within_chunk_rank" in ranking for ranking in rankings.values())
    assert all(ranking["observations"].eq(3).all() for ranking in fold_rankings.values())
    repeated, _, _ = importance_tables(results, source)
    for target in TARGETS:
        assert repeated[target]["feature"].tolist() == rankings[target]["feature"].tolist()


def _worker_bundle(path: Path, validation_targets: np.ndarray) -> Path:
    path.mkdir()
    arrays = {
        "train.npy": np.arange(6 * 300, dtype=np.float32).reshape(6, 300),
        "targets.npy": np.column_stack(
            [validation_targets, np.linspace(0.1, 0.6, 6)]
        ).astype(np.float64),
        "selection_folds.npy": np.array([0, 0, 0, 1, 1, 1], dtype=np.int8),
    }
    for name, values in arrays.items():
        np.save(path / name, values, allow_pickle=False)
    (path / "targets.json").write_text(json.dumps(list(TARGETS)))
    files = {
        name: {"sha256": sha256_file(path / name), "bytes": (path / name).stat().st_size}
        for name in [*arrays, "targets.json"]
    }
    identity = {
        "files": files,
        "train_rows": 6,
        "test_rows": 2,
        "predictors": 300,
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
    (path / "bundle_manifest.json").write_text(json.dumps(manifest))
    return path


def test_importance_worker_never_fits_on_validation_labels(tmp_path: Path, monkeypatch):
    fit_targets: list[np.ndarray] = []

    class FakeModel:
        def fit(self, _features, target, verbose=False):
            assert verbose is False
            fit_targets.append(np.asarray(target).copy())

        def get_feature_importance(self, *, type):
            assert type == "PredictionValuesChange"
            return np.arange(1, 301, dtype=float)

    @contextmanager
    def no_lease(_device):
        yield

    monkeypatch.setattr(worker, "_model", lambda _job: FakeModel())
    monkeypatch.setattr(worker, "gpu_lease", no_lease)
    first = _worker_bundle(tmp_path / "first", np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6]))
    second = _worker_bundle(tmp_path / "second", np.array([9.1, 9.2, 9.3, 0.4, 0.5, 0.6]))
    job = {
        "job_id": "leak-check",
        "kind": "importance",
        "target": TARGETS[0],
        "fold": 0,
        "columns": list(range(300)),
        "iterations": 150,
        "seed": 1701,
    }
    first_result = worker.execute_job(first, job)
    second_result = worker.execute_job(second, job)

    assert np.array_equal(fit_targets[0], fit_targets[1])
    assert first_result["importance"] == second_result["importance"]
    assert first_result["importance_sum"] == pytest.approx(1.0, abs=1e-12)


def test_importance_normalization_refinement_and_tolerant_cut_selection():
    assert normalize_importance(np.ones(300)).sum() == pytest.approx(1.0, abs=1e-12)
    with pytest.raises(ValueError, match="nonnegative"):
        normalize_importance([*np.ones(299), -1])
    assert refinement_counts({50: 0.1, 100: 0.2, 150: 0.3}) == [75]
    assert refinement_counts({50: 0.3, 100: 0.2, 150: 0.1}) == [125]
    assert select_confirmed_cut({100: 0.20005, 200: 0.2, 300: 0.21}) == 100
    assert select_confirmed_view(
        {"p99": 0.20005, "existing_809": 0.2},
        {"p99": 100, "existing_809": 809},
    ) == "p99"
    assert select_confirmed_view(
        {"p0": 0.19, "existing_809": 0.2},
        {"p0": 9969, "existing_809": 809},
    ) == "p0"


def test_percentile_thresholds_are_exact_deterministic_and_nested():
    feature_count = 9_969
    ranks = np.arange(1, feature_count + 1)
    ranking = pd.DataFrame(
        {
            "rank": ranks,
            "feature_index": ranks - 1,
            "feature": [f"feature_{index:05d}" for index in range(feature_count)],
            "mean_relative_importance": np.linspace(1.0, 0.001, feature_count),
            "importance_std": np.linspace(0.0, 0.1, feature_count),
            "empirical_importance_percentile": 100.0
            * (feature_count - ranks + 1)
            / feature_count,
        }
    )

    thresholds = percentile_thresholds(ranking)
    assert thresholds["percentile_label"].tolist() == [
        "p0", "p20", "p40", "p50", "p60", "p70", "p75", "p80", "p85",
        "p90", "p92.5", "p95", "p96", "p97", "p98", "p98.5", "p99",
        "p99.25", "p99.5",
    ]
    assert thresholds.iloc[0]["feature_count"] == feature_count
    assert thresholds.iloc[-1]["feature_count"] == 50
    assert thresholds["feature_count"].is_monotonic_decreasing
    sets = percentile_feature_sets(ranking)
    labels = thresholds["percentile_label"].tolist()
    assert all(set(sets[right]).issubset(sets[left]) for left, right in zip(labels, labels[1:]))
    assert percentile_thresholds(ranking).equals(thresholds)


def test_append_only_events_and_result_cache_are_idempotent(tmp_path: Path):
    events = AppendOnlyEvents(tmp_path / "events.jsonl")
    result = {"score": 0.1}
    events.append({"event": "job_completed", "job_id": "abc", "result": result})
    assert events.completed_jobs() == {"abc": result}
    cache = ResultCache(tmp_path / "cache")
    first_path = cache.put("key", result)
    first_hash = sha256_file(first_path)
    assert cache.get("key") == result
    second_path = cache.put("key", result)
    assert sha256_file(second_path) == first_hash


def test_frozen_submission_can_only_be_scored_once(tmp_path: Path):
    output = tmp_path / "run"
    labels = tmp_path / "labels"
    output.mkdir()
    labels.mkdir()
    submission = pd.DataFrame(
        {"id": [1, 2], TARGETS[0]: [0.1, 0.2], TARGETS[1]: [1.0, 2.0]}
    )
    submission.to_csv(output / "submission.csv", index=False)
    (output / "freeze_manifest.json").write_text(
        json.dumps({"submission_sha256": sha256_file(output / "submission.csv")})
    )
    pd.DataFrame({TARGETS[0]: [0.1, 0.2]}).to_parquet(
        labels / f"test_{TARGETS[0]}_810.parquet", index=False
    )
    pd.DataFrame({TARGETS[1]: [1.0, 2.0]}).to_parquet(
        labels / f"test_{TARGETS[1]}_810.parquet", index=False
    )
    receipt = score_frozen_submission_once(output_dir=output, labeled_test_dir=labels)
    assert json.loads(receipt.read_text())["selection_changed_after_scoring"] is False
    with pytest.raises(FileExistsError):
        score_frozen_submission_once(output_dir=output, labeled_test_dir=labels)
