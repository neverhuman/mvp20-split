"""Leakage-safe genetic reduction of a frozen public feature bundle.

Evolution is restricted to the two discovery folds.  The best proxy genomes are
rescored with all three discovery seeds, frozen, and only then evaluated on the
five confirmation folds.  The worker never accepts or reads test labels.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd

from nomad_crystal360.bakeoff import (
    AppendOnlyEvents,
    ResultCache,
    canonical_hash,
    sha256_file,
    verify_public_bundle,
)
from nomad_crystal360.bakeoff_run import (
    DualGpuScheduler,
    Host,
    ProgressDisplay,
    _environment,
    stage_remote_bundle,
)

from .constants import (
    ATLAS_TARGET_WINNERS,
    CONFIRM_TREES,
    EXISTING_809_CONTROLS,
    EXISTING_WIDTH,
    SCREEN_SEEDS,
    SCREEN_TREES,
    TARGETS,
    TIE_BAND,
)


PROXY_SEED = SCREEN_SEEDS[-1]
DISCOVERY_FOLDS = 2
CONFIRMATION_FOLDS = 5
MAX_CONFIRMATION_VIEWS = 8


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


@dataclass(frozen=True)
class Genome:
    target: str
    columns: tuple[int, ...]
    generation: int
    origin: str
    parents: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.target not in TARGETS:
            raise ValueError(f"unsupported target: {self.target}")
        if not self.columns:
            raise ValueError("genome has no columns")
        if tuple(sorted(set(self.columns))) != self.columns:
            raise ValueError("genome columns must be unique and sorted")
        if self.columns[0] < 0:
            raise ValueError("genome contains a negative column")

    @property
    def genome_id(self) -> str:
        payload = {"target": self.target, "columns": self.columns}
        return f"g-{canonical_hash(payload)[:20]}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "target": self.target,
            "feature_count": len(self.columns),
            "columns": list(self.columns),
            "generation": self.generation,
            "origin": self.origin,
            "parents": list(self.parents),
        }


def _genome(
    target: str,
    columns: Iterable[int],
    generation: int,
    origin: str,
    parents: Sequence[str] = (),
) -> Genome:
    return Genome(
        target=target,
        columns=tuple(sorted(set(map(int, columns)))),
        generation=generation,
        origin=origin,
        parents=tuple(parents),
    )


def _top(frame: pd.DataFrame, count: int) -> list[int]:
    return frame["feature_index"].astype(int).head(max(1, count)).tolist()


def _weighted_sample(
    rng: np.random.Generator,
    ranked_indices: np.ndarray,
    count: int,
) -> np.ndarray:
    count = min(max(1, int(count)), len(ranked_indices))
    ranks = np.arange(1, len(ranked_indices) + 1, dtype=np.float64)
    weights = 1.0 / np.sqrt(ranks)
    weights /= weights.sum()
    return rng.choice(ranked_indices, size=count, replace=False, p=weights)


def initial_population(
    *,
    target: str,
    aggregate_ranking: pd.DataFrame,
    fold_rankings: Sequence[pd.DataFrame],
    selected_columns: Sequence[int],
    allowed_columns: Sequence[int] | None = None,
    graduated_groups: dict[str, Sequence[int]] | None = None,
    population_size: int,
    seed: int,
) -> list[Genome]:
    """Create diverse deterministic seeds, including all-feature and control views."""

    if population_size < 8:
        raise ValueError("population_size must be at least eight")
    width = len(aggregate_ranking)
    if width < EXISTING_WIDTH:
        raise ValueError("ranking is narrower than the existing-feature control")
    ranked_all = aggregate_ranking["feature_index"].astype(int).to_numpy()
    if sorted(ranked_all.tolist()) != list(range(width)):
        raise ValueError("aggregate ranking is not a permutation of bundle columns")
    allowed = set(range(width) if allowed_columns is None else map(int, allowed_columns))
    if not allowed or min(allowed) < 0 or max(allowed) >= width:
        raise ValueError("allowed columns are empty or out of range")
    ranked = np.asarray([index for index in ranked_all if index in allowed], dtype=np.int64)
    if len(fold_rankings) != DISCOVERY_FOLDS:
        raise ValueError("exactly two fold rankings are required")
    base_size = len(selected_columns)
    seeds: list[Genome] = [
        _genome(
            target,
            allowed,
            0,
            "all-features" if len(allowed) == width else "all-validated-features",
        ),
        _genome(target, range(EXISTING_WIDTH), 0, "existing-809-control"),
        _genome(target, selected_columns, 0, "atlas-winner"),
    ]
    if graduated_groups:
        all_graduated = {
            index for group in graduated_groups.values() for index in map(int, group)
        }
        seeds.append(
            _genome(target, set(selected_columns) | all_graduated, 0, "atlas-plus-all-zyal")
        )
        seeds.extend(
            _genome(
                target,
                set(selected_columns) | set(map(int, group)),
                0,
                f"atlas-plus-{name.lower()}",
            )
            for name, group in sorted(graduated_groups.items())
        )
    seeds.extend(
        (
            _genome(target, allowed, 0, "all-validated-features"),
            _genome(
                target,
                allowed & set(range(EXISTING_WIDTH)),
                0,
                "validated-existing-control",
            ),
            _genome(target, allowed & set(selected_columns), 0, "validated-atlas-winner"),
        )
    )
    for factor in (0.70, 0.85, 1.15, 1.35):
        count = min(len(ranked), max(64, round(base_size * factor)))
        seeds.append(_genome(target, ranked[:count], 0, f"aggregate-cut-{count}"))

    left = set(
        [
            index
            for index in fold_rankings[0]["feature_index"].astype(int)
            if index in allowed
        ][:base_size]
    )
    right = set(
        [
            index
            for index in fold_rankings[1]["feature_index"].astype(int)
            if index in allowed
        ][:base_size]
    )
    seeds.extend(
        (
            _genome(target, left & right, 0, "fold-consensus-intersection"),
            _genome(target, left | right, 0, "fold-consensus-union"),
        )
    )

    rng = np.random.default_rng(seed)
    pool = ranked[: min(width, max(1_500, base_size * 3))]
    attempts = 0
    while len({item.genome_id for item in seeds}) < population_size:
        attempts += 1
        if attempts > population_size * 100:
            raise RuntimeError("could not create a unique initial population")
        factor = float(rng.uniform(0.65, 1.45))
        count = min(len(pool), max(64, round(base_size * factor)))
        sample = _weighted_sample(rng, pool, count)
        seeds.append(_genome(target, sample, 0, f"rank-weighted-{attempts:03d}"))
    unique: dict[str, Genome] = {}
    for item in seeds:
        unique.setdefault(item.genome_id, item)
    return list(unique.values())[:population_size]


def _rank_weights(ranking: pd.DataFrame, allowed_columns: set[int]) -> np.ndarray:
    width = len(ranking)
    weights = np.empty(width, dtype=np.float64)
    ordered = ranking["feature_index"].astype(int).to_numpy()
    weights.fill(0.0)
    allowed_order = np.asarray([index for index in ordered if index in allowed_columns], dtype=int)
    weights[allowed_order] = 1.0 / np.sqrt(
        np.arange(1, len(allowed_order) + 1, dtype=np.float64)
    )
    return weights


def breed_population(
    *,
    target: str,
    ranked_results: Sequence[tuple[Genome, float]],
    aggregate_ranking: pd.DataFrame,
    population_size: int,
    generation: int,
    seed: int,
    seen_ids: set[str],
    allowed_columns: Sequence[int] | None = None,
) -> list[Genome]:
    """Elitist set crossover with rank-biased add/drop/swap mutation."""

    if len(ranked_results) < 4:
        raise ValueError("at least four scored genomes are required to breed")
    ordered = sorted(ranked_results, key=lambda item: (item[1], len(item[0].columns)))
    rng = np.random.default_rng(seed + generation * 10_007)
    width = len(aggregate_ranking)
    allowed = set(range(width) if allowed_columns is None else map(int, allowed_columns))
    rank_weights = _rank_weights(aggregate_ranking, allowed)
    candidates = np.asarray(sorted(allowed), dtype=np.int64)
    children: list[Genome] = []
    attempts = 0
    while len(children) < population_size:
        attempts += 1
        if attempts > population_size * 500:
            raise RuntimeError("genetic population exhausted unique mutations")
        tournament = rng.choice(len(ordered), size=min(4, len(ordered)), replace=False)
        first_index = min(tournament, key=lambda index: ordered[int(index)][1])
        tournament = rng.choice(len(ordered), size=min(4, len(ordered)), replace=False)
        second_index = min(tournament, key=lambda index: ordered[int(index)][1])
        first = ordered[int(first_index)][0]
        second = ordered[int(second_index)][0]
        first_set = set(first.columns) & allowed
        second_set = set(second.columns) & allowed
        common = first_set & second_set
        optional = np.asarray(sorted(first_set ^ second_set), dtype=np.int64)
        target_size = round((len(first_set) + len(second_set)) / 2 * rng.uniform(0.88, 1.12))
        target_size = min(len(allowed), max(64, target_size))
        keep_optional = min(len(optional), max(0, target_size - len(common)))
        inherited = set(common) & allowed
        if keep_optional:
            probabilities = rank_weights[optional]
            probabilities /= probabilities.sum()
            inherited.update(
                rng.choice(optional, size=keep_optional, replace=False, p=probabilities).tolist()
            )

        mutation_rate = float(rng.uniform(0.025, 0.12))
        remove_count = min(len(inherited) - 64, max(1, round(len(inherited) * mutation_rate)))
        if remove_count > 0:
            present = np.asarray(sorted(inherited), dtype=np.int64)
            inverse = 1.0 / np.maximum(rank_weights[present], 1e-12)
            inverse /= inverse.sum()
            inherited.difference_update(
                rng.choice(present, size=remove_count, replace=False, p=inverse).tolist()
            )
        absent = np.asarray(sorted(set(candidates.tolist()) - inherited), dtype=np.int64)
        size_drift = int(rng.integers(-max(1, remove_count // 2), max(2, remove_count // 2 + 1)))
        add_count = min(len(absent), max(1, remove_count + size_drift))
        if add_count:
            probabilities = rank_weights[absent]
            probabilities /= probabilities.sum()
            inherited.update(
                rng.choice(absent, size=add_count, replace=False, p=probabilities).tolist()
            )
        child = _genome(
            target,
            inherited,
            generation,
            "crossover-mutation",
            (first.genome_id, second.genome_id),
        )
        if child.genome_id not in seen_ids and all(
            child.genome_id != existing.genome_id for existing in children
        ):
            children.append(child)

    return children[:population_size]


def summarize_jobs(
    jobs_and_results: Sequence[tuple[dict[str, Any], dict[str, Any]]],
    genomes: dict[str, Genome],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for job, result in jobs_and_results:
        grouped[str(job["genome_id"])].append((job, result))
    rows: list[dict[str, Any]] = []
    for genome_id, pairs in grouped.items():
        genome = genomes[genome_id]
        expected = {(int(job["seed"]), int(job["fold"])) for job, _ in pairs}
        scores = [float(result["score"]) for _, result in pairs]
        rows.append(
            {
                **genome.as_dict(),
                "mean_rmsle": float(np.mean(scores)),
                "rmsle_std": float(np.std(scores, ddof=0)),
                "model_jobs": len(scores),
                "seed_fold_pairs": [list(item) for item in sorted(expected)],
                "job_ids": [str(job["job_id"]) for job, _ in pairs],
            }
        )
    return sorted(rows, key=lambda row: (row["target"], row["mean_rmsle"], row["feature_count"]))


def _make_jobs(
    genomes: Sequence[Genome],
    *,
    seeds: Sequence[int],
    folds: int,
    iterations: int,
    kind: str,
    stage: str,
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for genome in genomes:
        for seed in seeds:
            for fold in range(folds):
                values = {
                    "kind": kind,
                    "stage": stage,
                    "target": genome.target,
                    "genome_id": genome.genome_id,
                    "fold": fold,
                    "columns": list(genome.columns),
                    "iterations": iterations,
                    "seed": int(seed),
                    "cut": len(genome.columns),
                }
                values["job_id"] = canonical_hash(values)[:24]
                jobs.append(values)
    return jobs


def choose_confirmation_genomes(
    full_discovery_rows: Sequence[dict[str, Any]],
    genomes: dict[str, Genome],
    atlas_genomes: dict[str, Genome],
    *,
    limit: int = MAX_CONFIRMATION_VIEWS,
) -> dict[str, list[Genome]]:
    """Freeze diverse score/size finalists without reading confirmation results."""

    if not 2 <= limit <= MAX_CONFIRMATION_VIEWS:
        raise ValueError("confirmation limit must be between two and eight")
    result: dict[str, list[Genome]] = {}
    for target in TARGETS:
        target_rows = sorted(
            (row for row in full_discovery_rows if row["target"] == target),
            key=lambda row: (float(row["mean_rmsle"]), int(row["feature_count"])),
        )
        chosen: list[Genome] = [atlas_genomes[target]]
        chosen_ids = {chosen[0].genome_id}
        # First preserve the strongest distinct score/size tradeoffs.
        for row in target_rows:
            candidate = genomes[str(row["genome_id"])]
            if candidate.genome_id in chosen_ids:
                continue
            if any(
                abs(len(candidate.columns) - len(item.columns))
                < max(20, round(0.04 * len(item.columns)))
                for item in chosen[1:]
            ) and len(chosen) < limit - 2:
                continue
            chosen.append(candidate)
            chosen_ids.add(candidate.genome_id)
            if len(chosen) == limit:
                break
        for row in target_rows:
            candidate = genomes[str(row["genome_id"])]
            if candidate.genome_id not in chosen_ids:
                chosen.append(candidate)
                chosen_ids.add(candidate.genome_id)
            if len(chosen) == limit:
                break
        result[target] = chosen
    return result


def _stage_inputs(
    source_bundle: Path,
    ranking_dir: Path,
    selected_path: Path,
    run_root: Path,
) -> tuple[Path, Path, Path]:
    staged_bundle = run_root / "inputs/genetic-bundle"
    staged_rankings = run_root / "inputs/genetic-rankings"
    staged_selected = run_root / "inputs/selected_columns.json"
    if not staged_bundle.exists():
        verify_public_bundle(source_bundle)
        staged_bundle.mkdir(parents=True)
        manifest = json.loads((source_bundle / "bundle_manifest.json").read_text())
        for name in [*manifest["files"], "bundle_manifest.json"]:
            shutil.copy2(source_bundle / name, staged_bundle / name)
        verify_public_bundle(staged_bundle)
    staged_rankings.mkdir(parents=True, exist_ok=True)
    for target in TARGETS:
        for suffix in ("", "_selection_fold_0", "_selection_fold_1"):
            name = f"ranking_{target}{suffix}.parquet"
            destination = staged_rankings / name
            if not destination.exists():
                shutil.copy2(ranking_dir / name, destination)
    if not staged_selected.exists():
        shutil.copy2(selected_path, staged_selected)
    return staged_bundle, staged_rankings, staged_selected


def _load_inputs(
    bundle: Path, ranking_dir: Path, selected_path: Path
) -> tuple[
    list[str],
    dict[str, pd.DataFrame],
    dict[str, list[pd.DataFrame]],
    dict[str, list[int]],
]:
    manifest = verify_public_bundle(bundle)
    columns = json.loads((bundle / "columns.json").read_text())
    if len(columns) != int(manifest["predictors"]):
        raise ValueError("bundle column registry width differs")
    column_index = {name: index for index, name in enumerate(columns)}
    selected_names = json.loads(selected_path.read_text())
    if set(selected_names) != set(TARGETS):
        raise ValueError("selected controls do not cover both targets")
    aggregate: dict[str, pd.DataFrame] = {}
    folds: dict[str, list[pd.DataFrame]] = {}
    selected: dict[str, list[int]] = {}
    for target in TARGETS:
        aggregate[target] = pd.read_parquet(ranking_dir / f"ranking_{target}.parquet")
        folds[target] = [
            pd.read_parquet(ranking_dir / f"ranking_{target}_selection_fold_{fold}.parquet")
            for fold in range(DISCOVERY_FOLDS)
        ]
        selected[target] = [column_index[name] for name in selected_names[target]]
    return columns, aggregate, folds, selected


def analyze_feature_bundle(bundle: Path) -> tuple[list[int], dict[str, Any]]:
    """Test every scalar column and quarantine only irrecoverable failures.

    NaN is an intentional absent-species representation in the frozen Atlas and
    is handled by CatBoost's native missing-value routing.  Its exact mask is
    included in duplicate signatures.  Infinity, constants, and exact numeric
    duplicates are individually quarantined.
    """

    manifest = verify_public_bundle(bundle)
    train = np.load(bundle / "train.npy", mmap_mode="r", allow_pickle=False)
    test = np.load(bundle / "test.npy", mmap_mode="r", allow_pickle=False)
    columns = json.loads((bundle / "columns.json").read_text())
    if train.shape != (int(manifest["train_rows"]), len(columns)):
        raise ValueError("training matrix shape differs from the bundle contract")
    if test.shape != (int(manifest["test_rows"]), len(columns)):
        raise ValueError("test matrix shape differs from the bundle contract")
    accepted: list[int] = []
    rejected: list[dict[str, Any]] = []
    missing_columns: list[int] = []
    signatures: dict[str, int] = {}
    for index, name in enumerate(columns):
        train_values = np.asarray(train[:, index], dtype="<f4")
        test_values = np.asarray(test[:, index], dtype="<f4")
        values = np.concatenate((train_values, test_values))
        missing = np.isnan(values)
        if missing.any():
            missing_columns.append(index)
        if np.isinf(values).any():
            rejected.append({"index": index, "feature": name, "reason": "infinite"})
            continue
        finite = values[~missing]
        if not finite.size or float(np.ptp(finite)) == 0.0:
            rejected.append({"index": index, "feature": name, "reason": "constant"})
            continue
        canonical = values.copy()
        canonical[missing] = 0.0
        digest = hashlib.sha256()
        digest.update(np.ascontiguousarray(missing).tobytes())
        digest.update(np.ascontiguousarray(canonical).tobytes())
        signature = digest.hexdigest()
        if signature in signatures:
            duplicate = signatures[signature]
            rejected.append(
                {
                    "index": index,
                    "feature": name,
                    "reason": "exact_numeric_duplicate",
                    "duplicate_of_index": duplicate,
                    "duplicate_of": columns[duplicate],
                }
            )
            continue
        signatures[signature] = index
        accepted.append(index)
    report = {
        "attempted_columns": len(columns),
        "validated_columns": len(accepted),
        "quarantined_columns": len(rejected),
        "columns_with_declared_missingness": len(missing_columns),
        "missingness_handling": "CatBoost native missing-value routing",
        "train_shape": list(train.shape),
        "test_shape": list(test.shape),
        "train_test_columns_aligned": True,
        "row_alignment_valid": True,
        "rejections": rejected,
        "accepted_indices_sha256": hashlib.sha256(
            np.asarray(accepted, dtype="<i8").tobytes()
        ).hexdigest(),
        "test_labels_used": False,
    }
    return accepted, report


def _source_counts(columns: Sequence[str], source: pd.DataFrame, genome: Genome) -> dict[str, int]:
    indices = np.asarray(genome.columns, dtype=int)
    rows = source.iloc[indices]
    return {
        str(key): int(value)
        for key, value in rows["feature_family"].value_counts().sort_index().items()
    }


def _winner(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    best = min(float(row["mean_rmsle"]) for row in rows)
    tied = [row for row in rows if float(row["mean_rmsle"]) <= best + TIE_BAND]
    return min(tied, key=lambda row: (int(row["feature_count"]), row["genome_id"]))


def run_reduction(
    *,
    source_bundle: Path,
    ranking_dir: Path,
    selected_path: Path,
    run_root: Path,
    worker_source: Path,
    remote_host: str = "xbabe1",
    remote_bundle: Path = Path("/home/ubuntu/atlas-genetic-reduction/bundle"),
    population_size: int = 14,
    generations: int = 5,
    full_discovery_candidates: int = 12,
    seed: int = 20260718,
) -> dict[str, Any]:
    if generations < 1:
        raise ValueError("generations must be positive")
    if full_discovery_candidates < MAX_CONFIRMATION_VIEWS:
        raise ValueError("at least eight full-discovery candidates are required")
    run_root.mkdir(parents=True, exist_ok=True)
    marker = run_root / "confirmation/confirmation-opened.json"
    if marker.exists():
        raise FileExistsError("confirmation was already opened for this reduction run")

    bundle, staged_rankings, staged_selected = _stage_inputs(
        source_bundle, ranking_dir, selected_path, run_root
    )
    columns, aggregate, fold_rankings, selected = _load_inputs(
        bundle, staged_rankings, staged_selected
    )
    allowed_columns, feature_analysis = analyze_feature_bundle(bundle)
    _atomic_json(run_root / "analysis/feature_validation.json", feature_analysis)
    source = pd.read_parquet(bundle / "source_families.parquet")
    graduated_groups = {
        str(domain): rows["index"].astype(int).tolist()
        for domain, rows in source[
            source["source_family"] == "zyal-v1-trusted-graduation"
        ].groupby("feature_family")
    }
    controller = run_root / "inputs/controller"
    controller.mkdir(parents=True, exist_ok=True)
    worker = controller / "atlas_bakeoff_worker.py"
    reducer_snapshot = controller / "genetic_reduction.py"
    shutil.copy2(worker_source, worker)
    shutil.copy2(Path(__file__), reducer_snapshot)

    config = {
        "protocol": "v2-atlas-genetic-reduction",
        "population_size": population_size,
        "generations": generations,
        "proxy_seed": PROXY_SEED,
        "full_discovery_seeds": list(SCREEN_SEEDS),
        "discovery_folds": DISCOVERY_FOLDS,
        "screen_trees": SCREEN_TREES,
        "confirmation_folds": CONFIRMATION_FOLDS,
        "confirmation_trees": CONFIRM_TREES,
        "confirmation_view_limit": MAX_CONFIRMATION_VIEWS,
        "random_seed": seed,
        "test_labels_used": False,
        "automatic_merge": False,
        "bundle_sha256": verify_public_bundle(bundle)["bundle_sha256"],
        "worker_sha256": sha256_file(worker),
        "reducer_sha256": sha256_file(reducer_snapshot),
    }
    _atomic_json(run_root / "protocol.json", config)
    stage_remote_bundle(
        bundle=bundle,
        worker=worker,
        remote_host=remote_host,
        remote_bundle=remote_bundle,
    )
    hosts = {
        "local": Host("local", "/usr/bin/python3", bundle, worker),
        "xbabe1": Host(remote_host, "python3", remote_bundle, remote_bundle / "worker.py"),
    }
    environments = {name: _environment(host) for name, host in hosts.items()}
    for name, identity in environments.items():
        if identity["packages"].get("catboost") != "1.2.10":
            raise ValueError(f"{name} does not have pinned CatBoost 1.2.10")
    _atomic_json(run_root / "receipts/gpu-environments.json", environments)

    events = AppendOnlyEvents(run_root / "receipts/progress.jsonl")
    cache = ResultCache(run_root / "cache/model-results")
    proxy_job_count = len(TARGETS) * population_size * generations * DISCOVERY_FOLDS
    full_job_count = (
        len(TARGETS)
        * full_discovery_candidates
        * len(SCREEN_SEEDS)
        * DISCOVERY_FOLDS
    )
    confirmation_job_count = (
        len(TARGETS) * MAX_CONFIRMATION_VIEWS * CONFIRMATION_FOLDS
    )
    progress = ProgressDisplay(events, proxy_job_count + full_job_count + confirmation_job_count)
    all_genomes: dict[str, Genome] = {}
    proxy_rows: list[dict[str, Any]] = []
    population = {
        target: initial_population(
            target=target,
            aggregate_ranking=aggregate[target],
            fold_rankings=fold_rankings[target],
            selected_columns=selected[target],
            allowed_columns=allowed_columns,
            graduated_groups=graduated_groups,
            population_size=population_size,
            seed=seed + index,
        )
        for index, target in enumerate(TARGETS)
    }
    atlas_genomes = {
        target: _genome(target, selected[target], 0, "atlas-winner") for target in TARGETS
    }
    scheduler = DualGpuScheduler(
        hosts=hosts,
        environments=environments,
        bundle_hash=config["bundle_sha256"],
        runner_hash=config["worker_sha256"],
        cache=cache,
        events=events,
        progress=progress,
    )
    with progress:
        try:
            for generation in range(generations):
                members = [item for target in TARGETS for item in population[target]]
                all_genomes.update((item.genome_id, item) for item in members)
                jobs = _make_jobs(
                    members,
                    seeds=(PROXY_SEED,),
                    folds=DISCOVERY_FOLDS,
                    iterations=SCREEN_TREES,
                    kind="screen",
                    stage=f"genetic-proxy-{generation:02d}",
                )
                results = scheduler.run(f"genetic-proxy-{generation:02d}", jobs)
                generation_rows = summarize_jobs(results, all_genomes)
                proxy_rows.extend(generation_rows)
                _atomic_json(
                    run_root / f"discovery/generation-{generation:02d}.json",
                    {"generation": generation, "genomes": generation_rows},
                )
                if generation + 1 < generations:
                    next_population: dict[str, list[Genome]] = {}
                    for target_index, target in enumerate(TARGETS):
                        best_by_id: dict[str, dict[str, Any]] = {}
                        for row in proxy_rows:
                            if row["target"] == target:
                                current = best_by_id.get(str(row["genome_id"]))
                                if current is None or row["mean_rmsle"] < current["mean_rmsle"]:
                                    best_by_id[str(row["genome_id"])] = row
                        scored = [
                            (all_genomes[genome_id], float(row["mean_rmsle"]))
                            for genome_id, row in best_by_id.items()
                        ]
                        next_population[target] = breed_population(
                            target=target,
                            ranked_results=scored,
                            aggregate_ranking=aggregate[target],
                            population_size=population_size,
                            generation=generation + 1,
                            seed=seed + target_index,
                            seen_ids=set(all_genomes),
                            allowed_columns=allowed_columns,
                        )
                    population = next_population

            proxy_frame = pd.DataFrame(proxy_rows).drop(columns="columns")
            proxy_frame.to_parquet(run_root / "discovery/proxy_scores.parquet", index=False)
            proxy_frame.to_csv(run_root / "discovery/proxy_scores.csv", index=False)
            shortlisted: list[Genome] = []
            for target in TARGETS:
                target_rows = sorted(
                    (row for row in proxy_rows if row["target"] == target),
                    key=lambda row: (float(row["mean_rmsle"]), int(row["feature_count"])),
                )
                used: set[str] = set()
                for row in target_rows:
                    genome_id = str(row["genome_id"])
                    if genome_id not in used:
                        shortlisted.append(all_genomes[genome_id])
                        used.add(genome_id)
                    if len(used) == full_discovery_candidates:
                        break
            full_jobs = _make_jobs(
                shortlisted,
                seeds=SCREEN_SEEDS,
                folds=DISCOVERY_FOLDS,
                iterations=SCREEN_TREES,
                kind="screen",
                stage="full-discovery",
            )
            full_results = scheduler.run("full-discovery", full_jobs)
            full_rows = summarize_jobs(full_results, all_genomes)
            full_frame = pd.DataFrame(full_rows).drop(columns="columns")
            full_frame.to_parquet(run_root / "discovery/full_scores.parquet", index=False)
            full_frame.to_csv(run_root / "discovery/full_scores.csv", index=False)

            finalists = choose_confirmation_genomes(
                full_rows, all_genomes, atlas_genomes, limit=MAX_CONFIRMATION_VIEWS
            )
            preregistration = {
                target: [item.as_dict() for item in finalists[target]] for target in TARGETS
            }
            _atomic_json(run_root / "confirmation/preregistration.json", preregistration)
            _atomic_json(
                marker,
                {
                    "opened": True,
                    "after_adaptive_generation": True,
                    "views_per_target": {
                        target: len(items) for target, items in finalists.items()
                    },
                },
            )
            confirmation_members = [
                item for target in TARGETS for item in finalists[target]
            ]
            all_genomes.update((item.genome_id, item) for item in confirmation_members)
            confirmation_jobs = _make_jobs(
                confirmation_members,
                seeds=(SCREEN_SEEDS[-1],),
                folds=CONFIRMATION_FOLDS,
                iterations=CONFIRM_TREES,
                kind="confirm",
                stage="confirmation",
            )
            confirmation_results = scheduler.run("confirmation", confirmation_jobs)
        finally:
            scheduler.close()

    confirmation_rows = summarize_jobs(confirmation_results, all_genomes)
    for row in confirmation_rows:
        target = str(row["target"])
        row["atlas_lift"] = ATLAS_TARGET_WINNERS[target] - float(row["mean_rmsle"])
        row["existing_809_lift"] = EXISTING_809_CONTROLS[target] - float(row["mean_rmsle"])
        row["beats_both_controls"] = bool(
            row["atlas_lift"] > 0 and row["existing_809_lift"] > 0
        )
    winners = {
        target: _winner([row for row in confirmation_rows if row["target"] == target])
        for target in TARGETS
    }
    for target, row in winners.items():
        genome = all_genomes[str(row["genome_id"])]
        row["selected_columns"] = [columns[index] for index in genome.columns]
        row["feature_family_counts"] = _source_counts(columns, source, genome)
    mean_rmsle = float(np.mean([winners[target]["mean_rmsle"] for target in TARGETS]))
    baseline_mean = float(np.mean([ATLAS_TARGET_WINNERS[target] for target in TARGETS]))
    payload = {
        "protocol": config,
        "views": confirmation_rows,
        "winners": winners,
        "final_mean_rmsle": mean_rmsle,
        "atlas_winner_mean_rmsle": baseline_mean,
        "mean_lift_over_atlas": baseline_mean - mean_rmsle,
        "beats_atlas_each_target": all(winners[target]["atlas_lift"] > 0 for target in TARGETS),
        "beats_existing_809_each_target": all(
            winners[target]["existing_809_lift"] > 0 for target in TARGETS
        ),
        "test_labels_used": False,
        "automatic_merge": False,
    }
    _atomic_json(run_root / "confirmation/results.json", payload)
    hash_files = [
        run_root / "protocol.json",
        run_root / "analysis/feature_validation.json",
        run_root / "discovery/proxy_scores.parquet",
        run_root / "discovery/full_scores.parquet",
        run_root / "confirmation/preregistration.json",
        run_root / "confirmation/results.json",
    ]
    manifest = {
        "files": {
            str(path.relative_to(run_root)): sha256_file(path) for path in hash_files
        },
        "bundle_sha256": config["bundle_sha256"],
        "test_labels_used": False,
        "automatic_merge": False,
    }
    manifest["manifest_sha256"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    _atomic_json(run_root / "final_hashes/manifest.json", manifest)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--ranking-dir", type=Path, required=True)
    parser.add_argument("--selected-columns", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--worker", type=Path, default=Path("atlas_bakeoff_worker.py"))
    parser.add_argument("--remote-host", default="xbabe1")
    parser.add_argument(
        "--remote-bundle", type=Path, default=Path("/home/ubuntu/atlas-genetic-reduction/bundle")
    )
    parser.add_argument("--population", type=int, default=14)
    parser.add_argument("--generations", type=int, default=5)
    parser.add_argument("--full-discovery-candidates", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260718)
    args = parser.parse_args()
    result = run_reduction(
        source_bundle=args.bundle.resolve(),
        ranking_dir=args.ranking_dir.resolve(),
        selected_path=args.selected_columns.resolve(),
        run_root=args.run_root.resolve(),
        worker_source=args.worker.resolve(),
        remote_host=args.remote_host,
        remote_bundle=args.remote_bundle,
        population_size=args.population,
        generations=args.generations,
        full_discovery_candidates=args.full_discovery_candidates,
        seed=args.seed,
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
