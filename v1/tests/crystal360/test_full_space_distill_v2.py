from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nomad_feature_hunt.v2.full_space_distill import (
    BANDGAP_TARGET,
    EPSILON,
    FORMATION_TARGET,
    GENERATIONS,
    POPULATION_SIZE,
    Settings,
    _parent_lock,
    breed_pair_population,
    derive_confirmation_seeds,
    epsilon_select,
    initial_pair_population,
    make_pair,
    mutate_target_mask,
    pareto_front,
    prepare,
    record_scq_terminal,
    run,
    union_count,
    verify,
    verify_parent_lock,
)
from nomad_feature_hunt.v2.full_space_sweep import (
    DISCOVERY_FOLD_SEED,
    SEALED_SEEDS,
    SWEEP_SEEDS,
    TARGETS,
    atomic_json,
    cache_identity,
    canonical_hash,
    sha256_file,
)


def test_union_accounting_epsilon_selection_and_tie_breaks() -> None:
    assert union_count(range(64), range(32, 96)) == 96
    rows = [
        {
            "pair_id": "best-large",
            "canonical_hash": "c",
            "mean_rmsle": 0.05,
            "union_count": 100,
            "summed_target_mask_size": 140,
        },
        {
            "pair_id": "epsilon-small",
            "canonical_hash": "b",
            "mean_rmsle": 0.05 + EPSILON,
            "union_count": 90,
            "summed_target_mask_size": 130,
        },
        {
            "pair_id": "outside",
            "canonical_hash": "a",
            "mean_rmsle": 0.05 + EPSILON + 1e-8,
            "union_count": 80,
            "summed_target_mask_size": 120,
        },
    ]
    assert epsilon_select(rows)["pair_id"] == "epsilon-small"
    tied = [
        {**rows[0], "pair_id": "sum-large", "canonical_hash": "a", "union_count": 90},
        {
            **rows[0],
            "pair_id": "sum-small",
            "canonical_hash": "z",
            "union_count": 90,
            "summed_target_mask_size": 120,
        },
    ]
    assert epsilon_select(tied)["pair_id"] == "sum-small"
    hash_tied = [
        {**tied[1], "pair_id": "hash-z"},
        {**tied[1], "pair_id": "hash-a", "canonical_hash": "a"},
    ]
    assert epsilon_select(hash_tied)["pair_id"] == "hash-a"


def test_pareto_and_deterministic_pair_generation() -> None:
    width = 180
    rankings = {target: np.arange(1, width + 1, dtype=float) for target in TARGETS}
    accuracy = make_pair(range(100), range(40, 120), origin="accuracy")
    compact = make_pair(range(90), range(45, 109), origin="compact")
    third = make_pair(range(110), range(10, 120), origin="third")
    front_rows = [
        {**accuracy.as_dict(), "mean_rmsle": 0.04},
        {**compact.as_dict(), "mean_rmsle": 0.04005},
        {**third.as_dict(), "mean_rmsle": 0.05},
    ]
    assert {row["pair_id"] for row in pareto_front(front_rows)} == {
        accuracy.pair_id,
        compact.pair_id,
    }
    first = initial_pair_population([accuracy, compact], [accuracy, compact], rankings)
    second = initial_pair_population([accuracy, compact], [accuracy, compact], rankings)
    assert [pair.pair_id for pair in first] == [pair.pair_id for pair in second]
    assert len(first) == POPULATION_SIZE == len({pair.pair_id for pair in first})
    archive = [(pair, 0.04 + index / 100_000) for index, pair in enumerate(first)]
    bred_first = breed_pair_population(archive, rankings, generation=1)
    bred_second = breed_pair_population(archive, rankings, generation=1)
    assert [pair.pair_id for pair in bred_first] == [pair.pair_id for pair in bred_second]
    assert all(len(mask) >= 64 for pair in bred_first for mask in pair.masks.values())


def test_overlap_aware_mutation_prefers_shared_adds_and_exclusive_drops() -> None:
    width = 200
    mask = tuple(range(64))
    opposite = tuple(range(50, 130))
    ranks = np.arange(1, width + 1, dtype=float)
    added = mutate_target_mask(
        mask,
        opposite,
        ranks,
        np.random.default_rng(7),
        operation="add",
        mutation_count=20,
    )
    additions = set(added) - set(mask)
    assert len(additions & set(opposite)) > len(additions - set(opposite))
    large = tuple(range(100))
    dropped = mutate_target_mask(
        large,
        opposite,
        ranks,
        np.random.default_rng(11),
        operation="drop",
        mutation_count=20,
    )
    removals = set(large) - set(dropped)
    shared = set(large) & set(opposite)
    assert len(removals - shared) > len(removals & shared)
    minimum = mutate_target_mask(
        mask,
        opposite,
        ranks,
        np.random.default_rng(3),
        operation="drop",
        mutation_count=20,
    )
    assert minimum == mask


def test_confirmation_seed_derivation_is_fresh_and_deterministic() -> None:
    forbidden = {*SWEEP_SEEDS, DISCOVERY_FOLD_SEED, *SEALED_SEEDS}
    first = derive_confirmation_seeds("a" * 64, "distill-r1", forbidden=forbidden)
    second = derive_confirmation_seeds("a" * 64, "distill-r1", forbidden=forbidden)
    assert first == second
    assert len(first) == len(set(first)) == 2
    assert not set(first) & forbidden
    assert first != derive_confirmation_seeds("a" * 64, "distill-r2", forbidden=forbidden)


def test_test_label_paths_are_rejected() -> None:
    with pytest.raises(Exception, match="test-label"):
        Settings("labeled_test", inbox=Path("/tmp/distill-fixture"))


def _write_npy(path: Path, values: np.ndarray) -> dict[str, object]:
    np.save(path, values, allow_pickle=False)
    return {"sha256": sha256_file(path), "bytes": path.stat().st_size}


def _parent_fixture(inbox: Path, parent_run: str = "parent") -> Path:
    root = inbox / f"fullspace-sweep-{parent_run}"
    bundle = root / "bundle"
    bundle.mkdir(parents=True)
    width = 180
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
    registry.to_parquet(bundle / "feature_registry.parquet", index=False)
    registry.to_csv(bundle / "feature_registry.csv", index=False)
    arrays = {
        "train.npy": np.zeros((20, width), dtype=np.float32),
        "test.npy": np.zeros((4, width), dtype=np.float32),
        "targets.npy": np.ones((20, 2), dtype=np.float64),
        "train_ids.npy": np.arange(20),
        "test_ids.npy": np.arange(20, 24),
        "discovery_folds.npy": np.arange(20, dtype=np.int8) % 5,
    }
    files = {name: _write_npy(bundle / name, values) for name, values in arrays.items()}
    json_files = {
        "columns.json": [f"feature-{index}" for index in range(width)],
        "targets.json": list(TARGETS),
        "duplicate_mappings.json": [],
        "quarantine.json": [],
        "source_maps.json": {"fixture": {str(index): index for index in range(width)}},
        "hyperion_positional_provenance.json": {"accepted": True},
    }
    for name, value in json_files.items():
        atomic_json(bundle / name, value)
    for name in [*json_files, "feature_registry.parquet", "feature_registry.csv"]:
        files[name] = {
            "sha256": sha256_file(bundle / name),
            "bytes": (bundle / name).stat().st_size,
        }
    identity = {
        "files": files,
        "train_rows": 20,
        "test_rows": 4,
        "predictors": width,
        "targets": list(TARGETS),
        "discovery_folds": 5,
        "discovery_fold_seed": DISCOVERY_FOLD_SEED,
        "contains_test_targets": False,
    }
    atomic_json(
        bundle / "bundle_manifest.json",
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
    root.mkdir(exist_ok=True)
    (root / "worker.py").write_text("fixture-worker", encoding="utf-8")
    atomic_json(
        root / "protocol.json",
        {
            "controller_sha256": "controller-fixture",
            "worker_sha256": sha256_file(root / "worker.py"),
            "sweep_seeds": list(SWEEP_SEEDS),
            "discovery_fold_seed": DISCOVERY_FOLD_SEED,
            "sealed_seeds": list(SEALED_SEEDS),
            "test_labels_used": False,
        },
    )
    atomic_json(
        root / "verification.json",
        {"complete": True, "test_labels_used": False},
    )
    for target in TARGETS:
        ranking = pd.DataFrame(
            {
                "rank": np.arange(1, width + 1),
                "feature_index": np.arange(width),
                "global_index": np.arange(width),
                "feature_id": [f"feature-{index}" for index in range(width)],
                "mean_relative_importance": np.linspace(1, 0.01, width),
            }
        )
        (root / "importance").mkdir(exist_ok=True)
        ranking.to_parquet(root / f"importance/ranking_{target}.parquet", index=False)
        for fold in range(5):
            ranking.to_parquet(
                root / f"importance/ranking_{target}_fold_{fold}.parquet", index=False
            )
    bandgap_views = [
        ("bg-good", tuple(range(100)), 0.0700),
        ("bg-small", tuple(range(64)), 0.0701),
    ]
    formation_views = [
        ("fe-good", tuple(range(40, 120)), 0.0200),
        ("fe-small", tuple(range(50, 114)), 0.0201),
    ]

    def view(target: str, value: tuple[str, tuple[int, ...], float]) -> dict[str, object]:
        view_id, columns, _score = value
        return {
            "genome_id": view_id,
            "target": target,
            "columns": list(columns),
            "feature_count": len(columns),
            "feature_set_hash": canonical_hash(columns),
            "generation": 0,
            "origin": "fixture",
            "parents": [],
        }

    prereg = {
        BANDGAP_TARGET: {
            "finalists": [view(BANDGAP_TARGET, item) for item in bandgap_views],
            "controls": [],
        },
        FORMATION_TARGET: {
            "finalists": [view(FORMATION_TARGET, item) for item in formation_views],
            "controls": [],
        },
        "test_labels_used": False,
    }
    (root / "confirmation").mkdir(exist_ok=True)
    atomic_json(root / "confirmation/preregistration.json", prereg)
    curve = pd.DataFrame(
        [
            {"target": target, "view": view_id, "mean_rmsle": score}
            for target, views in (
                (BANDGAP_TARGET, bandgap_views),
                (FORMATION_TARGET, formation_views),
            )
            for view_id, _columns, score in views
        ]
    )
    curve.to_parquet(root / "confirmation/score_curve.parquet", index=False)
    pd.DataFrame({"fixture": [1]}).to_parquet(
        root / "confirmation/fold_scores.parquet", index=False
    )
    atomic_json(
        root / "confirmation/results.json",
        {
            "winners": {
                BANDGAP_TARGET: {"genome_id": "bg-good"},
                FORMATION_TARGET: {"genome_id": "fe-good"},
            },
            "test_labels_used": False,
        },
    )
    (root / "genetic").mkdir(exist_ok=True)
    atomic_json(root / "genetic/genomes.json", {"fixture": True})
    atomic_json(root / "genetic/finalists.json", {"fixture": True})
    return root


class FakeCachingScheduler:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.calls = 0

    def run(self, _stage: str, jobs: list[dict[str, object]]):
        self.calls += len(jobs)
        protocol = json.loads((self.settings.run_root / "protocol.json").read_text())
        worker_hash = sha256_file(self.settings.worker)
        rows = []
        for job in jobs:
            target_base = 0.07 if job["target"] == BANDGAP_TARGET else 0.02
            score = (
                target_base
                + len(job["columns"]) / 10_000_000
                + int(job["fold"]) / 10_000_000
                + (int(job["cv_seed"]) % 97) / 1_000_000_000
            )
            result = {"score": score, "job_id": job["job_id"], "status": "completed"}
            key = cache_identity(
                bundle_hash=protocol["parent_bundle_sha256"],
                worker_hash=worker_hash,
                job=job,
            )
            atomic_json(self.settings.run_root / f"cache/model-results/{key}.json", result)
            rows.append((job, result))
        return rows


def _terminal() -> dict[str, object]:
    return {
        "job_id": "fake-scq-1",
        "state": "completed",
        "host": "xbabe2",
        "project": "xhyp3",
        "controller_exit_code": 0,
        "controller_exited_at": "2026-07-20T10:00:00Z",
        "terminal_at": "2026-07-20T10:00:01Z",
        "requested_gpus": 1,
        "assigned_gpus": 1,
        "foreground": True,
        "detached_children": False,
        "remote_gpu_use": False,
    }


def test_prepare_rejects_parent_and_controller_drift(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    _parent_fixture(inbox)
    settings = Settings("drift", parent_run="parent", inbox=inbox)
    protocol = prepare(settings, r3_archive=None)
    verify_parent_lock(settings, protocol)
    parent_protocol = settings.parent_root / "protocol.json"
    value = json.loads(parent_protocol.read_text())
    value["controller_sha256"] = "changed"
    atomic_json(parent_protocol, value)
    with pytest.raises(Exception, match="parent controller/artifact hash drift"):
        verify_parent_lock(settings, protocol)


def test_fake_scheduler_prepare_through_verification_and_cache_resume(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    _parent_fixture(inbox)
    settings = Settings("integration", parent_run="parent", inbox=inbox)
    prepare(settings, r3_archive=None)
    scheduler = FakeCachingScheduler(settings)
    report = run(settings, scheduler=scheduler)
    assert report["test_labels_used"] is False
    assert scheduler.calls > 0
    before = scheduler.calls
    run(settings, scheduler=scheduler)
    assert scheduler.calls == before
    record_scq_terminal(settings, _terminal())
    verification = verify(settings)
    assert verification["complete"], verification["missing"]
    masks = json.loads((settings.run_root / "exports/target_masks.json").read_text())
    union = set(masks["union"])
    assert all(set(mask).issubset(union) for mask in masks["target_masks"].values())
    assert len(pd.read_parquet(settings.run_root / "search/history.parquet")) == (
        POPULATION_SIZE * GENERATIONS
    )


def test_cache_schedule_identity_is_bound_to_parent_and_worker(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    _parent_fixture(inbox)
    settings = Settings("cache", parent_run="parent", inbox=inbox)
    protocol = prepare(settings, r3_archive=None)
    assert protocol["parent_files"] == _parent_lock(settings)
    job = {
        "kind": "screen",
        "target": BANDGAP_TARGET,
        "columns": list(range(64)),
        "fold": 0,
        "cv_seed": DISCOVERY_FOLD_SEED,
        "model_seed": DISCOVERY_FOLD_SEED,
        "iterations": 150,
    }
    first = cache_identity(
        bundle_hash=protocol["parent_bundle_sha256"],
        worker_hash=protocol["worker_sha256"],
        job=job,
    )
    second = cache_identity(
        bundle_hash="different",
        worker_hash=protocol["worker_sha256"],
        job=job,
    )
    assert first != second
