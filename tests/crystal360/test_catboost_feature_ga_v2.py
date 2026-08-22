from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from nomad_feature_hunt.v2.catboost_feature_ga import (
    BANDGAP_TARGET,
    EPSILON,
    FORMATION_TARGET,
    POPULATION_SIZE,
    PairGenome,
    Settings,
    _append_live,
    breed_population,
    initial_population,
    jobs_for_population,
    reduce_mask,
    score_population,
    select_final,
)


def _pair(start: int, generation: int = 0) -> PairGenome:
    return PairGenome(
        tuple(range(start, start + 100)),
        tuple(range(start + 20, start + 100)),
        generation=generation,
    )


def _rankings(width: int = 300) -> dict[str, np.ndarray]:
    positions = np.arange(1, width + 1, dtype=np.float64)
    return {BANDGAP_TARGET: positions, FORMATION_TARGET: positions.copy()}


def _archive_row(pair: PairGenome, score: float) -> dict:
    row = pair.as_dict()
    row.update(
        {
            "confirmed_mean_rmsle": score,
            "target_importance": {
                target: [
                    {"global_index": column, "importance": 1.0 / len(columns)} for column in columns
                ]
                for target, columns in pair.masks.items()
            },
            "test_labels_used": False,
        }
    )
    return row


def test_overlap_aware_reduction_is_strict_subset() -> None:
    mask = tuple(range(100))
    opposite = tuple(range(80))
    importance = {column: float(column + 1) for column in mask}
    reduced = reduce_mask(
        mask,
        opposite,
        np.arange(1, 101, dtype=np.float64),
        fraction=0.1,
        rng=np.random.default_rng(9),
        importance=importance,
    )
    assert set(reduced) < set(mask)
    assert len(reduced) == 90
    assert set(range(80, 90)).isdisjoint(reduced)


def test_initial_population_is_deterministic_and_reduces_both_targets() -> None:
    seeds = [_pair(0), _pair(30), _pair(60)]
    first = initial_population(seeds, _rankings())
    second = initial_population(seeds, _rankings())
    assert len(first) == POPULATION_SIZE
    assert [pair.pair_id for pair in first] == [pair.pair_id for pair in second]
    assert len({pair.pair_id for pair in first}) == POPULATION_SIZE
    for child in first[3:]:
        parent = next(pair for pair in seeds if pair.pair_id == child.parents[0])
        assert set(child.bandgap_columns) < set(parent.bandgap_columns)
        assert set(child.formation_columns) < set(parent.formation_columns)


def test_breeding_is_deterministic_and_never_expands_masks() -> None:
    parents = [_pair(0), _pair(30), _pair(60), _pair(90)]
    archive = [_archive_row(pair, 0.05 + index * 0.0001) for index, pair in enumerate(parents)]
    first = breed_population(archive, _rankings(400), generation=1)
    second = breed_population(archive, _rankings(400), generation=1)
    assert [pair.pair_id for pair in first] == [pair.pair_id for pair in second]
    assert len(first) == POPULATION_SIZE
    for child in first:
        if child.parents:
            parent_sizes = [
                (
                    len(
                        next(pair for pair in parents if pair.pair_id == parent_id).bandgap_columns
                    ),
                    len(
                        next(
                            pair for pair in parents if pair.pair_id == parent_id
                        ).formation_columns
                    ),
                )
                for parent_id in child.parents
            ]
            assert len(child.bandgap_columns) <= min(size[0] for size in parent_sizes)
            assert len(child.formation_columns) <= min(size[1] for size in parent_sizes)


def test_job_grid_deduplicates_shared_masks_and_has_five_folds() -> None:
    first = _pair(0)
    second = PairGenome(first.bandgap_columns, tuple(range(40, 120)))
    jobs = jobs_for_population([first, second], cv_seed=1234, bundle_hash="b", worker_hash="w")
    assert len(jobs) == 15
    assert {job["fold"] for job in jobs} == set(range(5))
    assert all(job["test_labels_used"] is False for job in jobs)


def test_scoring_uses_only_complete_five_fold_results() -> None:
    pair = _pair(0)
    jobs = jobs_for_population([pair], cv_seed=1234, bundle_hash="b", worker_hash="w")
    results = {}
    for job in jobs:
        score = 0.08 if job["target"] == BANDGAP_TARGET else 0.02
        results[job["job_id"]] = {
            **job,
            "score": score,
            "feature_importance": [1.0 / len(job["columns"])] * len(job["columns"]),
            "node": "xbabe1",
            "model_path": "/tmp/model.cbm",
            "model_sha256": "hash",
        }
    row = score_population([pair], results)[0]
    assert row["confirmed_mean_rmsle"] == pytest.approx(0.05)
    assert len(row["model_results"]) == 10
    assert row["test_labels_used"] is False


def test_epsilon_selection_prefers_smallest_union_then_mean() -> None:
    rows = [
        {
            **_pair(0).as_dict(),
            "confirmed_mean_rmsle": 0.05,
        },
        {
            **PairGenome(tuple(range(95)), tuple(range(20, 95))).as_dict(),
            "confirmed_mean_rmsle": 0.05 + EPSILON,
        },
    ]
    assert select_final(rows)["union_count"] == 95


def test_live_log_is_append_only_and_marks_no_test_use(tmp_path: Path) -> None:
    source = tmp_path / "fullspace-distill-source"
    source.mkdir()
    (source / "protocol.json").write_text(json.dumps({"parent_run": "parent"}))
    settings = Settings("run", source_run="source", inbox=tmp_path)
    event = {
        "generation": 0,
        "pair_id": "p-1",
        "bandgap_count": 100,
        "formation_count": 80,
        "union_count": 120,
        "bandgap_mean_rmsle": 0.08,
        "formation_mean_rmsle": 0.02,
        "confirmed_mean_rmsle": 0.05,
        "new_low": True,
        "checkpoint": "/tmp/checkpoint",
        "origin": "test",
    }
    _append_live(settings, event)
    _append_live(settings, {**event, "pair_id": "p-2", "new_low": False})
    assert len(settings.live_jsonl.read_text().splitlines()) == 2
    assert "test_labels_used" in settings.live_csv.read_text()
    assert all(
        row["test_labels_used"] is False
        for row in map(json.loads, settings.live_jsonl.read_text().splitlines())
    )


def test_test_label_path_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(Exception, match="test-label"):
        Settings("labeled_test", source_run="source", inbox=tmp_path)
