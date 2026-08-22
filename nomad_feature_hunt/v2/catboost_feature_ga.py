"""Distributed, CV-only CatBoost genetic reduction of paired NOMAD masks."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from dataclasses import dataclass
import json
import os
from pathlib import Path
from queue import Empty, Queue
import shutil
import subprocess
import time
from typing import Any, Mapping, Sequence

import numpy as np

from .full_space_distill import (
    BANDGAP_TARGET,
    EPSILON,
    FORMATION_TARGET,
    MINIMUM_TARGET_COLUMNS,
    PairGenome,
    Settings as DistillSettings,
    _pair_from_dict,
    _rankings,
    atomic_json,
    canonical_hash,
    derive_confirmation_seeds,
    sha256_file,
    utc_now,
)
from .full_space_sweep import DEFAULT_INBOX, prohibit_test_labels, verify_full_space_bundle


NODES = ("xbabe1", "xbabe2", "xbabe3")
SCQ = Path("/home/ubuntu/remote_super/smart_cluster/target/release/scq")
WORKERS_PER_NODE = 16
THREADS_PER_FIT = 4
CPUS_PER_NODE = WORKERS_PER_NODE * THREADS_PER_FIT
POPULATION_SIZE = 24
GENERATIONS = 10
FOLDS = 5
ITERATIONS = 400
SEARCH_SEED = 20_260_720
MODEL_PARAMETERS = {
    "loss_function": "RMSE",
    "depth": 7,
    "learning_rate": 0.05,
    "task_type": "CPU",
    "iterations": ITERATIONS,
    "allow_writing_files": False,
    "verbose": False,
}
WORKER_SOURCE = Path(__file__).with_name("catboost_feature_ga_worker.py")


class FeatureGAError(RuntimeError):
    """A fail-closed distributed feature-GA contract violation."""


@dataclass(frozen=True)
class Settings:
    run_id: str
    source_run: str = "20260720-r1"
    inbox: Path = DEFAULT_INBOX

    def __post_init__(self) -> None:
        for label, value in (("run_id", self.run_id), ("source_run", self.source_run)):
            if (
                not value
                or len(value) > 64
                or not all(character.isalnum() or character in "-_." for character in value)
            ):
                raise FeatureGAError(f"{label} must contain 1-64 safe filename characters")
        prohibit_test_labels([self.run_root, self.source_root])

    @property
    def run_root(self) -> Path:
        return self.inbox / f"catboost-feature-ga-{self.run_id}"

    @property
    def source_root(self) -> Path:
        return self.inbox / f"fullspace-distill-{self.source_run}"

    @property
    def bundle(self) -> Path:
        protocol = json.loads((self.source_root / "protocol.json").read_text(encoding="utf-8"))
        return self.inbox / f"fullspace-sweep-{protocol['parent_run']}" / "bundle"

    @property
    def worker(self) -> Path:
        return self.run_root / "worker.py"

    @property
    def state_path(self) -> Path:
        return self.run_root / "state.json"

    @property
    def live_csv(self) -> Path:
        return self.run_root / "live/confirmed_mean_rmsle.csv"

    @property
    def live_jsonl(self) -> Path:
        return self.run_root / "live/confirmed_mean_rmsle.jsonl"


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _all_integers(value: Any) -> set[int]:
    if isinstance(value, bool):
        return set()
    if isinstance(value, int):
        return {value}
    if isinstance(value, dict):
        return set().union(*(_all_integers(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_integers(item) for item in value), set())
    return set()


def _source_pairs(settings: Settings) -> list[PairGenome]:
    results_path = settings.source_root / "expedited/results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    if results.get("test_labels_used") is not False:
        raise FeatureGAError("source results do not prohibit test labels")
    by_class = {row["candidate_class"]: row for row in results["candidates"]}
    required = (
        "accuracy-control",
        "compact-epsilon-control",
        "two-sided-reduced-candidate",
    )
    if set(required) - set(by_class):
        raise FeatureGAError("source confirmation is missing a required seed pair")
    return [_pair_from_dict(by_class[name]) for name in required]


def _rank_score(rank_positions: np.ndarray, column: int) -> float:
    return 1.0 / float(rank_positions[column])


def reduce_mask(
    mask: Sequence[int],
    opposite: Sequence[int],
    rank_positions: np.ndarray,
    *,
    fraction: float,
    rng: np.random.Generator,
    importance: Mapping[int, float] | None = None,
) -> tuple[int, ...]:
    """Drop weak target-exclusive features first; never add a feature."""
    if not 0.0 < fraction < 1.0:
        raise ValueError("drop fraction must be in (0, 1)")
    count = min(
        max(1, int(round(len(mask) * fraction))),
        len(mask) - MINIMUM_TARGET_COLUMNS,
    )
    if count <= 0:
        return tuple(mask)
    opposite_set = set(opposite)
    live = importance or {}
    jitter = {column: float(rng.random()) for column in mask}
    ordered = sorted(
        mask,
        key=lambda column: (
            column in opposite_set,
            float(live.get(column, _rank_score(rank_positions, column))),
            -float(rank_positions[column]),
            jitter[column],
            column,
        ),
    )
    removed = set(ordered[:count])
    return tuple(column for column in mask if column not in removed)


def crossover_mask(
    first: Sequence[int],
    second: Sequence[int],
    rank_positions: np.ndarray,
    first_importance: Mapping[int, float],
    second_importance: Mapping[int, float],
) -> tuple[int, ...]:
    """Recombine two masks without exceeding the smaller parent size."""
    size = min(len(first), len(second))
    universe = set(first) | set(second)
    scored = sorted(
        universe,
        key=lambda column: (
            -max(
                first_importance.get(column, 0.0),
                second_importance.get(column, 0.0),
                _rank_score(rank_positions, column),
            ),
            float(rank_positions[column]),
            column,
        ),
    )
    return tuple(sorted(scored[:size]))


def _rank_importance(rank_positions: np.ndarray, mask: Sequence[int]) -> dict[int, float]:
    values = {column: _rank_score(rank_positions, column) for column in mask}
    total = sum(values.values())
    return {column: value / total for column, value in values.items()}


def initial_population(
    seeds: Sequence[PairGenome], rankings: Mapping[str, np.ndarray]
) -> list[PairGenome]:
    if len(seeds) != 3:
        raise ValueError("the initial population requires exactly three confirmed seeds")
    population: dict[str, PairGenome] = {pair.pair_id: pair for pair in seeds}
    fractions = (0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.06, 0.08, 0.1)
    cursor = 0
    while len(population) < POPULATION_SIZE:
        parent = seeds[cursor % len(seeds)]
        fraction = fractions[(cursor // len(seeds)) % len(fractions)]
        rng = np.random.default_rng(SEARCH_SEED + cursor)
        bandgap = reduce_mask(
            parent.bandgap_columns,
            parent.formation_columns,
            rankings[BANDGAP_TARGET],
            fraction=fraction,
            rng=rng,
        )
        formation = reduce_mask(
            parent.formation_columns,
            parent.bandgap_columns,
            rankings[FORMATION_TARGET],
            fraction=fraction,
            rng=rng,
        )
        child = PairGenome(
            bandgap,
            formation,
            generation=0,
            origin="catboost-rank-reduction",
            parents=(parent.pair_id,),
        )
        population.setdefault(child.pair_id, child)
        cursor += 1
        if cursor > 500:
            raise AssertionError("could not construct a unique initial population")
    return list(population.values())[:POPULATION_SIZE]


def _importance_map(row: Mapping[str, Any], target: str) -> dict[int, float]:
    return {
        int(item["global_index"]): float(item["importance"])
        for item in row["target_importance"][target]
    }


def pareto_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    unique = {str(row["pair_id"]): dict(row) for row in rows}
    front = []
    for candidate in unique.values():
        dominated = any(
            (
                float(other["confirmed_mean_rmsle"]) <= float(candidate["confirmed_mean_rmsle"])
                and int(other["union_count"]) <= int(candidate["union_count"])
            )
            and (
                float(other["confirmed_mean_rmsle"]) < float(candidate["confirmed_mean_rmsle"])
                or int(other["union_count"]) < int(candidate["union_count"])
            )
            for other in unique.values()
            if other["pair_id"] != candidate["pair_id"]
        )
        if not dominated:
            front.append(candidate)
    return sorted(
        front,
        key=lambda row: (
            int(row["union_count"]),
            float(row["confirmed_mean_rmsle"]),
            str(row["pair_id"]),
        ),
    )


def breed_population(
    archive: Sequence[Mapping[str, Any]],
    rankings: Mapping[str, np.ndarray],
    *,
    generation: int,
) -> list[PairGenome]:
    if generation < 1:
        raise ValueError("breeding starts at generation one")
    front = pareto_rows(archive)
    if not front:
        raise ValueError("breeding requires a Pareto archive")
    parent_pool = list(front)
    for row in sorted(
        archive,
        key=lambda item: (
            float(item["confirmed_mean_rmsle"]),
            int(item["union_count"]),
            str(item["pair_id"]),
        ),
    ):
        if row["pair_id"] not in {item["pair_id"] for item in parent_pool}:
            parent_pool.append(dict(row))
        if len(parent_pool) >= 12:
            break
    by_score = sorted(
        front,
        key=lambda row: (
            float(row["confirmed_mean_rmsle"]),
            int(row["union_count"]),
            str(row["pair_id"]),
        ),
    )
    elite_rows: list[Mapping[str, Any]] = []
    for row in [*by_score[:2], *front[:2]]:
        if row["pair_id"] not in {item["pair_id"] for item in elite_rows}:
            elite_rows.append(row)
    population: dict[str, PairGenome] = {row["pair_id"]: _pair_from_dict(row) for row in elite_rows}
    fractions = (0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.06, 0.08)
    rng = np.random.default_rng(SEARCH_SEED + generation * 100_003)
    cursor = 0
    while len(population) < POPULATION_SIZE:
        first_row = parent_pool[cursor % len(parent_pool)]
        second_row = parent_pool[(cursor * 7 + generation) % len(parent_pool)]
        first = _pair_from_dict(first_row)
        second = _pair_from_dict(second_row)
        if cursor % 3 == 2 and first.pair_id != second.pair_id:
            bandgap_base = crossover_mask(
                first.bandgap_columns,
                second.bandgap_columns,
                rankings[BANDGAP_TARGET],
                _importance_map(first_row, BANDGAP_TARGET),
                _importance_map(second_row, BANDGAP_TARGET),
            )
            formation_base = crossover_mask(
                first.formation_columns,
                second.formation_columns,
                rankings[FORMATION_TARGET],
                _importance_map(first_row, FORMATION_TARGET),
                _importance_map(second_row, FORMATION_TARGET),
            )
            parents = (first.pair_id, second.pair_id)
            origin = "catboost-crossover-reduction"
            bandgap_importance = {
                **_importance_map(second_row, BANDGAP_TARGET),
                **_importance_map(first_row, BANDGAP_TARGET),
            }
            formation_importance = {
                **_importance_map(second_row, FORMATION_TARGET),
                **_importance_map(first_row, FORMATION_TARGET),
            }
        else:
            bandgap_base = first.bandgap_columns
            formation_base = first.formation_columns
            parents = (first.pair_id,)
            origin = "catboost-importance-reduction"
            bandgap_importance = _importance_map(first_row, BANDGAP_TARGET)
            formation_importance = _importance_map(first_row, FORMATION_TARGET)
        fraction = min(
            0.25,
            fractions[(cursor + generation) % len(fractions)] + 0.002 * (cursor // len(fractions)),
        )
        bandgap = reduce_mask(
            bandgap_base,
            formation_base,
            rankings[BANDGAP_TARGET],
            fraction=fraction,
            rng=rng,
            importance=bandgap_importance,
        )
        formation = reduce_mask(
            formation_base,
            bandgap_base,
            rankings[FORMATION_TARGET],
            fraction=fraction,
            rng=rng,
            importance=formation_importance,
        )
        child = PairGenome(
            bandgap,
            formation,
            generation=generation,
            origin=origin,
            parents=parents,
        )
        population.setdefault(child.pair_id, child)
        cursor += 1
        if cursor > 2_000:
            raise AssertionError("could not breed a unique population")
    return list(population.values())[:POPULATION_SIZE]


def _job_identity(job: Mapping[str, Any], bundle_hash: str, worker_hash: str) -> str:
    return canonical_hash(
        {
            "bundle_sha256": bundle_hash,
            "worker_sha256": worker_hash,
            "target": job["target"],
            "columns": job["columns"],
            "fold": job["fold"],
            "cv_seed": job["cv_seed"],
            "model_seed": job["model_seed"],
            "iterations": job["iterations"],
            "model_parameters": MODEL_PARAMETERS,
        }
    )


def jobs_for_population(
    population: Sequence[PairGenome],
    *,
    cv_seed: int,
    bundle_hash: str,
    worker_hash: str,
) -> list[dict[str, Any]]:
    jobs: dict[tuple[str, str, int], dict[str, Any]] = {}
    for pair in population:
        for target, columns in pair.masks.items():
            mask_hash = canonical_hash(columns)
            for fold in range(FOLDS):
                key = (target, mask_hash, fold)
                base = {
                    "target": target,
                    "columns": list(columns),
                    "feature_set_hash": mask_hash,
                    "fold": fold,
                    "cv_seed": cv_seed,
                    "model_seed": cv_seed,
                    "iterations": ITERATIONS,
                    "test_labels_used": False,
                }
                identity = _job_identity(base, bundle_hash, worker_hash)
                jobs.setdefault(
                    key, {**base, "job_id": f"cpu-{identity[:24]}", "cache_key": identity}
                )
    return list(jobs.values())


def score_population(
    population: Sequence[PairGenome], results: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    lookup = {
        (
            str(result["target"]),
            canonical_hash(result["columns"]),
            int(result["fold"]),
        ): result
        for result in results.values()
    }
    rows = []
    for pair in population:
        target_metrics: dict[str, Any] = {}
        target_importance: dict[str, Any] = {}
        model_results = []
        for target, columns in pair.masks.items():
            fold_results = [
                lookup[(target, canonical_hash(columns), fold)] for fold in range(FOLDS)
            ]
            scores = [float(result["score"]) for result in fold_results]
            importance = np.mean(
                np.asarray([result["feature_importance"] for result in fold_results]), axis=0
            )
            importance /= float(importance.sum())
            target_metrics[target] = {
                "mean_rmsle": float(np.mean(scores)),
                "rmsle_std": float(np.std(scores)),
                "fold_scores": scores,
                "mask_count": len(columns),
            }
            target_importance[target] = [
                {"global_index": int(column), "importance": float(value)}
                for column, value in zip(columns, importance, strict=True)
            ]
            model_results.extend(
                {
                    key: result[key]
                    for key in (
                        "job_id",
                        "target",
                        "fold",
                        "score",
                        "node",
                        "model_path",
                        "model_sha256",
                    )
                }
                for result in fold_results
            )
        rows.append(
            {
                **pair.as_dict(),
                "confirmed_mean_rmsle": float(
                    np.mean([target_metrics[target]["mean_rmsle"] for target in pair.masks])
                ),
                "target_metrics": target_metrics,
                "target_importance": target_importance,
                "model_results": model_results,
                "cv_folds": FOLDS,
                "test_labels_used": False,
            }
        )
    return rows


def select_final(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    best = min(float(row["confirmed_mean_rmsle"]) for row in rows)
    feasible = [row for row in rows if float(row["confirmed_mean_rmsle"]) <= best + EPSILON + 1e-15]
    return dict(
        min(
            feasible,
            key=lambda row: (
                int(row["union_count"]),
                float(row["confirmed_mean_rmsle"]),
                int(row["summed_target_mask_size"]),
                str(row["canonical_hash"]),
            ),
        )
    )


class DistributedSCQEvaluator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.protocol = json.loads(
            (settings.run_root / "protocol.json").read_text(encoding="utf-8")
        )
        self.bundle_hash = str(self.protocol["bundle_sha256"])
        self.worker_hash = str(self.protocol["worker_sha256"])
        self.remote_root = Path(self.protocol["remote_root"])
        self.cache_root = settings.run_root / "cache/model-results"
        self.cache_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _run(
        command: Sequence[str], *, timeout: float | None = None
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            list(command), capture_output=True, text=True, timeout=timeout, check=False
        )
        if result.returncode != 0:
            raise FeatureGAError(result.stderr.strip() or result.stdout.strip())
        return result

    def _stage_node(self, node: str) -> tuple[str, dict[str, Any]]:
        self._run(["ssh", "-o", "BatchMode=yes", node, "mkdir", "-p", str(self.remote_root)])
        self._run(
            [
                "rsync",
                "-a",
                "--checksum",
                f"{self.settings.bundle}/",
                f"{node}:{self.remote_root / 'bundle'}/",
            ]
        )
        self._run(
            [
                "rsync",
                "-a",
                "--checksum",
                str(self.settings.worker),
                f"{node}:{self.remote_root / 'worker.py'}",
            ]
        )
        identity_result = self._run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                node,
                "python3",
                str(self.remote_root / "worker.py"),
                "--identity",
            ],
            timeout=60,
        )
        identity = json.loads(identity_result.stdout.splitlines()[-1])
        if identity["packages"]["catboost"] != "1.2.10":
            raise FeatureGAError(f"{node} has the wrong CatBoost version")
        self._run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                node,
                "python3",
                str(self.remote_root / "worker.py"),
                "--bundle",
                str(self.remote_root / "bundle"),
                "--verify-only",
            ],
            timeout=300,
        )
        self._run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                node,
                "python3",
                str(self.remote_root / "worker.py"),
                "--smoke",
                "--threads-per-fit",
                "2",
            ],
            timeout=120,
        )
        return node, identity

    def stage(self) -> dict[str, Any]:
        receipt_path = self.settings.run_root / "receipts/environments.json"
        if receipt_path.exists():
            return json.loads(receipt_path.read_text(encoding="utf-8"))
        with ThreadPoolExecutor(max_workers=len(NODES)) as executor:
            environments = dict(executor.map(self._stage_node, NODES))
        receipt = {
            "schema": "CatBoostDistributedEnvironments.v1",
            "nodes": environments,
            "bundle_sha256": self.bundle_hash,
            "worker_sha256": self.worker_hash,
            "workers_per_node": WORKERS_PER_NODE,
            "threads_per_fit": THREADS_PER_FIT,
            "cpus_per_node": CPUS_PER_NODE,
            "test_labels_used": False,
        }
        atomic_json(receipt_path, receipt)
        return receipt

    def _cache_get(self, key: str) -> dict[str, Any] | None:
        path = self.cache_root / f"{key}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def _cache_put(self, key: str, result: Mapping[str, Any]) -> None:
        path = self.cache_root / f"{key}.json"
        payload = _json_ready(result)
        if path.exists() and json.loads(path.read_text(encoding="utf-8")) != payload:
            raise FeatureGAError(f"cache collision for {key}")
        atomic_json(path, payload)

    def _show(self, job_id: str) -> dict[str, Any] | None:
        result = self._run([str(SCQ), "show", "--json", job_id], timeout=30)
        return json.loads(result.stdout)["Job"]["job"]

    def _submit(self, job_id: str, node: str, generation: int) -> None:
        remote_batch = self.remote_root / f"dispatch/g{generation:02d}/{node}/batch.json"
        remote_output = self.remote_root / f"output/g{generation:02d}/{node}"
        command = [
            str(SCQ),
            "submit",
            "--json",
            "--id",
            job_id,
            "--project",
            "xhyp3",
            "--gpus",
            "0",
            "--cpus",
            str(CPUS_PER_NODE),
            "--ram",
            "24",
            "--node",
            node,
            "--workdir",
            str(self.remote_root),
            "--require-python-import",
            "catboost",
            "--",
            "python3",
            str(self.remote_root / "worker.py"),
            "--bundle",
            str(self.remote_root / "bundle"),
            "--batch",
            str(remote_batch),
            "--output",
            str(remote_output),
            "--workers",
            str(WORKERS_PER_NODE),
            "--threads-per-fit",
            str(THREADS_PER_FIT),
        ]
        self._run(command, timeout=60)

    def _dispatch_node(
        self, node: str, generation: int, jobs: Sequence[dict[str, Any]]
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        local = self.settings.run_root / f"dispatch/g{generation:02d}/{node}"
        local.mkdir(parents=True, exist_ok=True)
        batch = {
            "schema": "CatBoostCPUBatch.v1",
            "generation": generation,
            "node": node,
            "jobs": list(jobs),
            "test_labels_used": False,
        }
        atomic_json(local / "batch.json", batch)
        remote_dispatch = self.remote_root / f"dispatch/g{generation:02d}/{node}"
        self._run(["ssh", "-o", "BatchMode=yes", node, "mkdir", "-p", str(remote_dispatch)])
        self._run(
            [
                "rsync",
                "-a",
                "--checksum",
                str(local / "batch.json"),
                f"{node}:{remote_dispatch / 'batch.json'}",
            ]
        )
        base_id = f"cbga-{self.settings.run_id}-g{generation:02d}-{node}"
        job_id = base_id
        attempt = 0
        while True:
            state = self._show(job_id)
            if state is None:
                self._submit(job_id, node, generation)
                break
            if state["state"] in {"queued", "running"}:
                break
            if state["state"] == "completed" and int(state["exit_code"]) == 0:
                break
            attempt += 1
            job_id = f"{base_id}-r{attempt}"
        while True:
            state = self._show(job_id)
            if state is None or state["state"] in {"queued", "dispatching", "running"}:
                time.sleep(2)
                continue
            if state["state"] != "completed" or int(state["exit_code"]) != 0:
                raise FeatureGAError(f"SCQ job {job_id} failed: {state}")
            break
        remote_results = self.remote_root / f"output/g{generation:02d}/{node}/results.json"
        self._run(
            [
                "rsync",
                "-a",
                "--checksum",
                f"{node}:{remote_results}",
                str(local / "results.json"),
            ]
        )
        payload = json.loads((local / "results.json").read_text(encoding="utf-8"))
        if payload["bundle_sha256"] != self.bundle_hash:
            raise FeatureGAError(f"{node} used the wrong bundle")
        return node, payload, state

    def _recover_legacy_results(
        self, generation: int, jobs: Sequence[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Import fold/model results left by the original static dispatch."""
        recovered: dict[str, dict[str, Any]] = {}
        by_id = {job["job_id"]: job for job in jobs}
        for node in NODES:
            legacy_batch = self.settings.run_root / f"dispatch/g{generation:02d}/{node}/batch.json"
            if not legacy_batch.exists():
                continue
            local = (
                self.settings.run_root / f"dispatch/g{generation:02d}/recovered/{node}/job-results"
            )
            local.mkdir(parents=True, exist_ok=True)
            remote = self.remote_root / f"output/g{generation:02d}/{node}/job-results"
            result = subprocess.run(
                [
                    "rsync",
                    "-a",
                    "--checksum",
                    f"{node}:{remote}/",
                    f"{local}/",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                continue
            for path in sorted(local.glob("*.json")):
                payload = json.loads(path.read_text(encoding="utf-8"))
                job = by_id.get(str(payload["job_id"]))
                if job is None:
                    continue
                payload["node"] = node
                self._cache_put(job["cache_key"], payload)
                recovered[job["job_id"]] = payload
        return recovered

    def _submit_wave(
        self,
        job_id: str,
        node: str,
        remote_batch: Path,
        remote_output: Path,
    ) -> None:
        command = [
            str(SCQ),
            "submit",
            "--json",
            "--id",
            job_id,
            "--project",
            "xhyp3",
            "--gpus",
            "0",
            "--cpus",
            str(CPUS_PER_NODE),
            "--ram",
            "24",
            "--node",
            node,
            "--workdir",
            str(self.remote_root),
            "--require-python-import",
            "catboost",
            "--",
            "python3",
            str(self.remote_root / "worker.py"),
            "--bundle",
            str(self.remote_root / "bundle"),
            "--batch",
            str(remote_batch),
            "--output",
            str(remote_output),
            "--workers",
            str(WORKERS_PER_NODE),
            "--threads-per-fit",
            str(THREADS_PER_FIT),
        ]
        self._run(command, timeout=60)

    def _dispatch_wave(
        self,
        node: str,
        generation: int,
        wave: int,
        jobs: Sequence[dict[str, Any]],
    ) -> tuple[str, int, dict[str, Any], dict[str, Any]]:
        local = self.settings.run_root / f"dispatch/g{generation:02d}/waves/wave-{wave:03d}/{node}"
        local.mkdir(parents=True, exist_ok=True)
        batch = {
            "schema": "CatBoostCPUBatch.v1",
            "generation": generation,
            "wave": wave,
            "node": node,
            "jobs": list(jobs),
            "test_labels_used": False,
        }
        atomic_json(local / "batch.json", batch)
        remote_dispatch = (
            self.remote_root / f"dispatch/g{generation:02d}/waves/wave-{wave:03d}/{node}"
        )
        remote_output = self.remote_root / f"output/g{generation:02d}/waves/wave-{wave:03d}/{node}"
        self._run(["ssh", "-o", "BatchMode=yes", node, "mkdir", "-p", str(remote_dispatch)])
        self._run(
            [
                "rsync",
                "-a",
                "--checksum",
                str(local / "batch.json"),
                f"{node}:{remote_dispatch / 'batch.json'}",
            ]
        )
        base_id = f"cbga-{self.settings.run_id}-g{generation:02d}-w{wave:03d}-{node}"
        job_id = base_id
        attempt = 0
        while True:
            state = self._show(job_id)
            if state is None:
                self._submit_wave(job_id, node, remote_dispatch / "batch.json", remote_output)
                break
            if state["state"] in {"queued", "running"}:
                break
            if state["state"] == "completed" and int(state["exit_code"]) == 0:
                break
            attempt += 1
            job_id = f"{base_id}-r{attempt}"
        while True:
            state = self._show(job_id)
            if state is None or state["state"] in {"queued", "dispatching", "running"}:
                time.sleep(2)
                continue
            if state["state"] != "completed" or int(state["exit_code"]) != 0:
                raise FeatureGAError(f"SCQ job {job_id} failed: {state}")
            break
        self._run(
            [
                "rsync",
                "-a",
                "--checksum",
                f"{node}:{remote_output / 'results.json'}",
                str(local / "results.json"),
            ]
        )
        payload = json.loads((local / "results.json").read_text(encoding="utf-8"))
        if payload["bundle_sha256"] != self.bundle_hash:
            raise FeatureGAError(f"{node} used the wrong bundle")
        return node, wave, payload, state

    def evaluate(
        self, generation: int, jobs: Sequence[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        results = self._recover_legacy_results(generation, jobs)
        pending = []
        for job in jobs:
            cached = self._cache_get(job["cache_key"])
            if cached is None:
                pending.append(job)
            else:
                results[job["job_id"]] = cached
        ordered = sorted(pending, key=lambda item: (-len(item["columns"]), item["job_id"]))
        waves: Queue[tuple[int, list[dict[str, Any]]]] = Queue()
        # Resume-safe wave numbering: never reuse a remote output directory from
        # an interrupted controller, since SCQ workers may leave a completed
        # payload there with a different logical batch.
        existing_waves = list(
            (self.settings.run_root / "dispatch" / f"g{generation:02d}").glob("waves/wave-*")
        )
        wave_base = len(existing_waves)
        for wave, offset in enumerate(range(0, len(ordered), WORKERS_PER_NODE), start=wave_base):
            waves.put((wave, ordered[offset : offset + WORKERS_PER_NODE]))
        terminal: dict[str, list[dict[str, Any]]] = {node: [] for node in NODES}
        dispatched_jobs = {node: 0 for node in NODES}

        def consume(node: str) -> list[dict[str, Any]]:
            completed: list[dict[str, Any]] = []
            while True:
                try:
                    wave, batch = waves.get_nowait()
                except Empty:
                    break
                assigned_node, _wave, payload, state = self._dispatch_wave(
                    node, generation, wave, batch
                )
                terminal[assigned_node].append(state)
                dispatched_jobs[assigned_node] += len(batch)
                by_id = {job["job_id"]: job for job in batch}
                for result in payload["results"]:
                    result = {**result, "node": assigned_node}
                    job = by_id[result["job_id"]]
                    self._cache_put(job["cache_key"], result)
                    completed.append(result)
                waves.task_done()
            return completed

        if pending:
            with ThreadPoolExecutor(max_workers=len(NODES)) as executor:
                completed_by_node = list(executor.map(consume, NODES))
            for completed in completed_by_node:
                for result in completed:
                    results[result["job_id"]] = result
        if set(results) != {job["job_id"] for job in jobs}:
            raise AssertionError("distributed evaluator did not return every job")
        atomic_json(
            self.settings.run_root / f"receipts/dispatch-generation-{generation:02d}.json",
            {
                "generation": generation,
                "logical_jobs": len(jobs),
                "cached_jobs": len(jobs) - len(pending),
                "recovered_legacy_jobs": len(results) - len(pending),
                "dispatch_mode": "eight-fit-work-stealing-waves",
                "dispatched_jobs": dispatched_jobs,
                "scq_terminal": terminal,
                "test_labels_used": False,
            },
        )
        return results

    def copy_models(self, row: Mapping[str, Any], destination: Path) -> list[dict[str, Any]]:
        destination.mkdir(parents=True, exist_ok=True)
        copied = []
        for result in row["model_results"]:
            target_dir = destination / str(result["target"])
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"fold-{int(result['fold'])}.cbm"
            if not target.exists():
                self._run(
                    [
                        "rsync",
                        "-a",
                        "--checksum",
                        f"{result['node']}:{result['model_path']}",
                        str(target),
                    ]
                )
            if sha256_file(target) != result["model_sha256"]:
                raise FeatureGAError(f"checkpoint model hash mismatch: {target}")
            copied.append(
                {
                    "target": result["target"],
                    "fold": int(result["fold"]),
                    "path": str(target),
                    "sha256": result["model_sha256"],
                    "source_node": result["node"],
                }
            )
        return copied


def _append_live(settings: Settings, event: Mapping[str, Any]) -> None:
    settings.live_jsonl.parent.mkdir(parents=True, exist_ok=True)
    payload = {**_json_ready(event), "logged_at": utc_now(), "test_labels_used": False}
    with settings.live_jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    fields = (
        "logged_at",
        "generation",
        "pair_id",
        "bandgap_count",
        "formation_count",
        "union_count",
        "bandgap_mean_rmsle",
        "formation_mean_rmsle",
        "confirmed_mean_rmsle",
        "new_low",
        "checkpoint",
        "origin",
        "test_labels_used",
    )
    exists = settings.live_csv.exists()
    with settings.live_csv.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({field: payload.get(field, "") for field in fields})
        handle.flush()
        os.fsync(handle.fileno())


def _logged_keys(settings: Settings) -> set[tuple[int, str]]:
    if not settings.live_jsonl.exists():
        return set()
    return {
        (int(row["generation"]), str(row["pair_id"]))
        for row in (
            json.loads(line)
            for line in settings.live_jsonl.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def _checkpoint(
    settings: Settings,
    evaluator: Any,
    row: Mapping[str, Any],
    *,
    name: str,
) -> Path:
    destination = settings.run_root / "checkpoints" / name
    models = evaluator.copy_models(row, destination / "models")
    manifest = {
        "schema": "CatBoostFeatureGACheckpoint.v1",
        "created_at": utc_now(),
        "pair": {
            key: row[key]
            for key in (
                "pair_id",
                "canonical_hash",
                "generation",
                "origin",
                "target_masks",
                "target_mask_counts",
                "union",
                "union_count",
                "confirmed_mean_rmsle",
                "target_metrics",
            )
        },
        "models": models,
        "cv_seed": json.loads((settings.run_root / "protocol.json").read_text(encoding="utf-8"))[
            "cv_seed"
        ],
        "folds": FOLDS,
        "model_parameters": MODEL_PARAMETERS,
        "test_labels_used": False,
    }
    manifest["canonical_hash"] = canonical_hash(manifest)
    atomic_json(destination / "manifest.json", manifest)
    return destination


def prepare(settings: Settings) -> dict[str, Any]:
    if settings.run_root.exists():
        protocol_path = settings.run_root / "protocol.json"
        if protocol_path.exists():
            return json.loads(protocol_path.read_text(encoding="utf-8"))
        raise FeatureGAError("run root exists without a protocol")
    prohibit_test_labels([settings.bundle])
    bundle = verify_full_space_bundle(settings.bundle)
    source_results = settings.source_root / "expedited/results.json"
    source_prereg = settings.source_root / "expedited/preregistration.json"
    source_protocol = settings.source_root / "protocol.json"
    for path in (source_results, source_prereg, source_protocol, WORKER_SOURCE):
        if not path.exists():
            raise FeatureGAError(f"required source artifact is missing: {path}")
    settings.run_root.mkdir(parents=True)
    for name in (
        "generations",
        "dispatch",
        "cache/model-results",
        "checkpoints",
        "live",
        "receipts",
    ):
        (settings.run_root / name).mkdir(parents=True, exist_ok=True)
    shutil.copy2(WORKER_SOURCE, settings.worker)
    distill_settings = DistillSettings(settings.source_run)
    rankings = _rankings(distill_settings)
    np.savez_compressed(settings.run_root / "rankings.npz", **rankings)
    seeds = _source_pairs(settings)
    population = initial_population(seeds, rankings)
    atomic_json(
        settings.run_root / "generations/generation-00-population.json",
        {
            "generation": 0,
            "pairs": [pair.as_dict() for pair in population],
            "test_labels_used": False,
        },
    )
    forbidden = _all_integers(json.loads(source_protocol.read_text(encoding="utf-8")))
    parent_protocol = Path(distill_settings.parent_root / "protocol.json")
    if parent_protocol.exists():
        forbidden |= _all_integers(json.loads(parent_protocol.read_text(encoding="utf-8")))
    cv_seed = derive_confirmation_seeds(
        str(bundle["bundle_sha256"]),
        f"catboost-feature-ga-{settings.run_id}",
        count=1,
        forbidden=forbidden,
    )[0]
    protocol = {
        "schema": "CatBoostFeatureGAProtocol.v1",
        "run_id": settings.run_id,
        "source_run": settings.source_run,
        "source_root": str(settings.source_root),
        "bundle_root": str(settings.bundle),
        "bundle_sha256": bundle["bundle_sha256"],
        "source_results_sha256": sha256_file(source_results),
        "source_preregistration_sha256": sha256_file(source_prereg),
        "source_protocol_sha256": sha256_file(source_protocol),
        "runner_sha256": sha256_file(Path(__file__)),
        "worker_sha256": sha256_file(settings.worker),
        "rankings_sha256": sha256_file(settings.run_root / "rankings.npz"),
        "cv_seed": cv_seed,
        "cv_folds": FOLDS,
        "population_size": POPULATION_SIZE,
        "generations": GENERATIONS,
        "model_parameters": MODEL_PARAMETERS,
        "nodes": list(NODES),
        "workers_per_node": WORKERS_PER_NODE,
        "threads_per_fit": THREADS_PER_FIT,
        "cpus_per_node": CPUS_PER_NODE,
        "remote_root": f"/home/ubuntu/nomad-cpu-ga/{settings.run_id}",
        "selection_rule": {
            "metric": "five-fold mean of the two target RMSLE means",
            "epsilon": EPSILON,
            "order": ["smallest union within epsilon", "lower mean", "smaller mask sum", "hash"],
        },
        "feature_decisions_use_only_cv": True,
        "test_labels_used": False,
    }
    atomic_json(settings.run_root / "protocol.json", protocol)
    atomic_json(
        settings.state_path,
        {
            "status": "prepared",
            "next_generation": 0,
            "completed_generations": [],
            "best_confirmed_mean_rmsle": None,
            "new_low_count": 0,
            "test_labels_used": False,
        },
    )
    return protocol


def _load_rankings(settings: Settings) -> dict[str, np.ndarray]:
    with np.load(settings.run_root / "rankings.npz") as payload:
        return {target: payload[target] for target in (BANDGAP_TARGET, FORMATION_TARGET)}


def _load_archive(settings: Settings) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((settings.run_root / "generations").glob("generation-*-results.json")):
        rows.extend(json.loads(path.read_text(encoding="utf-8"))["pairs"])
    return rows


def run(settings: Settings, evaluator: Any | None = None) -> dict[str, Any]:
    protocol = json.loads((settings.run_root / "protocol.json").read_text(encoding="utf-8"))
    if sha256_file(Path(__file__)) != protocol["runner_sha256"]:
        raise FeatureGAError("controller changed after prepare")
    if sha256_file(settings.worker) != protocol["worker_sha256"]:
        raise FeatureGAError("worker changed after prepare")
    if (
        sha256_file(settings.source_root / "expedited/results.json")
        != protocol["source_results_sha256"]
    ):
        raise FeatureGAError("source confirmation changed after prepare")
    active = evaluator or DistributedSCQEvaluator(settings)
    if hasattr(active, "stage"):
        active.stage()
    rankings = _load_rankings(settings)
    state = json.loads(settings.state_path.read_text(encoding="utf-8"))
    logged = _logged_keys(settings)
    archive = _load_archive(settings)
    best = min((float(row["confirmed_mean_rmsle"]) for row in archive), default=float("inf"))
    low_count = (
        sum(
            1
            for line in settings.live_jsonl.read_text(encoding="utf-8").splitlines()
            if json.loads(line).get("new_low")
        )
        if settings.live_jsonl.exists()
        else 0
    )
    for generation in range(int(state["next_generation"]), GENERATIONS):
        population_payload = json.loads(
            (
                settings.run_root / f"generations/generation-{generation:02d}-population.json"
            ).read_text(encoding="utf-8")
        )
        population = [_pair_from_dict(row) for row in population_payload["pairs"]]
        if (
            len(population) != POPULATION_SIZE
            or len({pair.pair_id for pair in population}) != POPULATION_SIZE
        ):
            raise FeatureGAError("population is not 24 unique pairs")
        results_path = settings.run_root / f"generations/generation-{generation:02d}-results.json"
        if results_path.exists():
            rows = json.loads(results_path.read_text(encoding="utf-8"))["pairs"]
        else:
            jobs = jobs_for_population(
                population,
                cv_seed=int(protocol["cv_seed"]),
                bundle_hash=str(protocol["bundle_sha256"]),
                worker_hash=str(protocol["worker_sha256"]),
            )
            model_results = active.evaluate(generation, jobs)
            rows = score_population(population, model_results)
            atomic_json(
                results_path,
                {
                    "generation": generation,
                    "pairs": rows,
                    "logical_pairs": POPULATION_SIZE,
                    "unique_model_jobs": len(jobs),
                    "cv_seed": protocol["cv_seed"],
                    "folds": FOLDS,
                    "test_labels_used": False,
                },
            )
        for row in rows:
            key = (generation, str(row["pair_id"]))
            if key in logged:
                continue
            score = float(row["confirmed_mean_rmsle"])
            new_low = score < best - 1e-15
            checkpoint = ""
            if new_low:
                low_count += 1
                checkpoint_path = _checkpoint(
                    settings,
                    active,
                    row,
                    name=f"low-{low_count:03d}-g{generation:02d}-{row['pair_id']}",
                )
                checkpoint = str(checkpoint_path)
                best = score
            _append_live(
                settings,
                {
                    "generation": generation,
                    "pair_id": row["pair_id"],
                    "bandgap_count": row["target_mask_counts"][BANDGAP_TARGET],
                    "formation_count": row["target_mask_counts"][FORMATION_TARGET],
                    "union_count": row["union_count"],
                    "bandgap_mean_rmsle": row["target_metrics"][BANDGAP_TARGET]["mean_rmsle"],
                    "formation_mean_rmsle": row["target_metrics"][FORMATION_TARGET]["mean_rmsle"],
                    "confirmed_mean_rmsle": score,
                    "new_low": new_low,
                    "checkpoint": checkpoint,
                    "origin": row["origin"],
                },
            )
            logged.add(key)
        archive.extend(rows)
        completed = list(range(generation + 1))
        if generation + 1 < GENERATIONS:
            next_population = breed_population(archive, rankings, generation=generation + 1)
            atomic_json(
                settings.run_root / f"generations/generation-{generation + 1:02d}-population.json",
                {
                    "generation": generation + 1,
                    "pairs": [pair.as_dict() for pair in next_population],
                    "test_labels_used": False,
                },
            )
        state = {
            "status": "running" if generation + 1 < GENERATIONS else "search-complete",
            "next_generation": generation + 1,
            "completed_generations": completed,
            "best_confirmed_mean_rmsle": best,
            "new_low_count": low_count,
            "test_labels_used": False,
        }
        atomic_json(settings.state_path, state)
    archive = _load_archive(settings)
    selected = select_final(archive)
    final_checkpoint = settings.run_root / "checkpoints/final-selected"
    if not (final_checkpoint / "manifest.json").exists():
        _checkpoint(settings, active, selected, name="final-selected")
    best_row = min(archive, key=lambda row: float(row["confirmed_mean_rmsle"]))
    report = {
        "schema": "CatBoostFeatureGAFinal.v1",
        "run_id": settings.run_id,
        "selected": selected,
        "best_mean_candidate": best_row,
        "evaluated_pairs": len(archive),
        "generations": GENERATIONS,
        "population_size": POPULATION_SIZE,
        "cv_seed": protocol["cv_seed"],
        "cv_folds": FOLDS,
        "model_parameters": MODEL_PARAMETERS,
        "live_csv": str(settings.live_csv),
        "live_jsonl": str(settings.live_jsonl),
        "final_checkpoint": str(final_checkpoint),
        "feature_decisions_use_only_cv": True,
        "test_labels_used": False,
    }
    report["canonical_hash"] = canonical_hash(report)
    atomic_json(settings.run_root / "final.json", report)
    state["status"] = "complete"
    state["selected_pair_id"] = selected["pair_id"]
    state["selected_union_count"] = selected["union_count"]
    atomic_json(settings.state_path, state)
    return report


def status(settings: Settings) -> dict[str, Any]:
    if not settings.state_path.exists():
        return {"status": "not-prepared", "run_root": str(settings.run_root)}
    state = json.loads(settings.state_path.read_text(encoding="utf-8"))
    state.update(
        {
            "run_root": str(settings.run_root),
            "live_csv": str(settings.live_csv),
            "live_jsonl": str(settings.live_jsonl),
            "logged_pairs": len(_logged_keys(settings)),
        }
    )
    return state


def verify(settings: Settings) -> dict[str, Any]:
    protocol = json.loads((settings.run_root / "protocol.json").read_text(encoding="utf-8"))
    if sha256_file(Path(__file__)) != protocol["runner_sha256"]:
        raise FeatureGAError("controller drift")
    if sha256_file(settings.worker) != protocol["worker_sha256"]:
        raise FeatureGAError("worker drift")
    if (
        sha256_file(settings.source_root / "expedited/results.json")
        != protocol["source_results_sha256"]
    ):
        raise FeatureGAError("source confirmation drift")
    state = json.loads(settings.state_path.read_text(encoding="utf-8"))
    if state["status"] != "complete":
        raise FeatureGAError("run is not complete")
    archive = _load_archive(settings)
    if len(archive) != POPULATION_SIZE * GENERATIONS:
        raise FeatureGAError("the 24-by-10 pair grid is incomplete")
    for row in archive:
        if row.get("test_labels_used") is not False:
            raise FeatureGAError("a result lacks the test-label prohibition")
        target_means = []
        for target in (BANDGAP_TARGET, FORMATION_TARGET):
            scores = row["target_metrics"][target]["fold_scores"]
            if len(scores) != FOLDS:
                raise FeatureGAError("a target lacks five CV folds")
            target_means.append(float(np.mean(scores)))
        if not np.isclose(
            float(np.mean(target_means)),
            float(row["confirmed_mean_rmsle"]),
            rtol=0.0,
            atol=1e-15,
        ):
            raise FeatureGAError("a pair mean does not recompute")
    logged = _logged_keys(settings)
    if len(logged) != len(archive):
        raise FeatureGAError("live log does not contain every evaluated pair")
    nodes_used = set()
    for path in sorted((settings.run_root / "receipts").glob("dispatch-generation-*.json")):
        receipt = json.loads(path.read_text(encoding="utf-8"))
        nodes_used |= {node for node, count in receipt["dispatched_jobs"].items() if count}
    if nodes_used != set(NODES):
        raise FeatureGAError("the run did not use every requested node")
    for manifest_path in sorted((settings.run_root / "checkpoints").glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("test_labels_used") is not False or len(manifest["models"]) != 10:
            raise FeatureGAError("checkpoint is incomplete")
        for model in manifest["models"]:
            if sha256_file(Path(model["path"])) != model["sha256"]:
                raise FeatureGAError("checkpoint model hash mismatch")
    report = json.loads((settings.run_root / "final.json").read_text(encoding="utf-8"))
    selected = select_final(archive)
    if report["selected"]["pair_id"] != selected["pair_id"]:
        raise FeatureGAError("final epsilon selection does not recompute")
    verification = {
        "schema": "CatBoostFeatureGAVerification.v1",
        "verified_at": utc_now(),
        "evaluated_pairs": len(archive),
        "nodes_used": sorted(nodes_used),
        "selected_pair_id": selected["pair_id"],
        "selected_union_count": selected["union_count"],
        "selected_confirmed_mean_rmsle": selected["confirmed_mean_rmsle"],
        "model_checkpoints": len(list((settings.run_root / "checkpoints").glob("*/manifest.json"))),
        "feature_decisions_use_only_cv": True,
        "test_labels_used": False,
    }
    verification["canonical_hash"] = canonical_hash(verification)
    atomic_json(settings.run_root / "verification.json", verification)
    return verification


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run", "resume", "status", "verify"))
    parser.add_argument("run_id")
    parser.add_argument("--source-run", default="20260720-r1")
    arguments = parser.parse_args()
    settings = Settings(arguments.run_id, source_run=arguments.source_run)
    if arguments.command == "prepare":
        result = prepare(settings)
    elif arguments.command in {"run", "resume"}:
        result = run(settings)
    elif arguments.command == "status":
        result = status(settings)
    else:
        result = verify(settings)
    print(json.dumps(_json_ready(result), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
