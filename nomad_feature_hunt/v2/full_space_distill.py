"""Joint, restartable distillation of a verified NOMAD full-space sweep.

The controller treats the parent sweep as immutable.  Candidates contain one
mask per target and are optimized on mean RMSLE and the size of their unique
extraction union.  Test labels are never an accepted input.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, replace
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import socket
import sqlite3
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from .full_space_sweep import (
    CATBOOST_VERSION,
    CONFIRM_TREES,
    DEFAULT_INBOX,
    DISCOVERY_FOLD_SEED,
    DISCOVERY_FOLDS,
    GENERATIONS,
    MODEL_PARAMETERS,
    POPULATION_SIZE,
    SCREEN_TREES,
    SEALED_SEEDS,
    SWEEP_SEEDS,
    TARGETS,
    CampaignScheduler,
    Host,
    SweepError,
    _json_command,
    _new_job,
    atomic_json,
    cache_identity,
    canonical_hash,
    prohibit_test_labels,
    save_frame,
    sha256_file,
    utc_now,
    verify_full_space_bundle,
)


FORMATION_TARGET = "formation_energy_ev_natom"
BANDGAP_TARGET = "bandgap_energy_ev"
EPSILON = 0.0001
FINALIST_LIMIT = 8
MINIMUM_TARGET_COLUMNS = 64
SEARCH_SEED = 20_260_720
PHASES = ("prepare", "search", "rescore", "confirmation", "report")
DEFAULT_PARENT_RUN = "20260719-r1"
DEFAULT_R3_ARCHIVE = Path("/home/ubuntu/jope-prime/ops/zyal/inbox/gp-feature-foundry-20260720-r3")
EXPECTED_ACCURACY_UNION = 1_799
EXPECTED_ACCURACY_MEAN = 0.04916535311859697
EXPECTED_COMPACT_UNION = 1_691
EXPECTED_COMPACT_MEAN = 0.049247548427025396
PARENT_CONTROLLER_SOURCE = Path(__file__).with_name("full_space_sweep.py")
SELECTION_RULE = {
    "metric": "mean of band-gap and formation-energy RMSLE",
    "direction": "minimize",
    "epsilon": EPSILON,
    "steps": [
        "find the lowest confirmed mean RMSLE",
        "retain candidates no more than epsilon worse",
        "choose the smallest unique union",
        "break ties by lower mean RMSLE, lower summed target-mask size, canonical hash",
    ],
    "fallback": (
        "if no newly searched candidate strictly beats the compact epsilon control, "
        "export that control unchanged"
    ),
}


class DistillError(SweepError):
    """A fail-closed feature-distillation contract violation."""


@dataclass(frozen=True)
class Settings:
    run_id: str
    parent_run: str = DEFAULT_PARENT_RUN
    inbox: Path = DEFAULT_INBOX

    def __post_init__(self) -> None:
        for label, value in (("run_id", self.run_id), ("parent_run", self.parent_run)):
            safe = value and all(character.isalnum() or character in "-_." for character in value)
            if not safe or len(value) > 64:
                raise DistillError(f"{label} must contain 1-64 safe filename characters")
        prohibit_test_labels([self.run_root, self.parent_root])
        if not self.run_root.resolve().is_relative_to(self.inbox.resolve()):
            raise DistillError("distillation artifacts must stay below the v2 inbox")
        if self.run_root.resolve() == self.parent_root.resolve():
            raise DistillError("distillation and parent roots must be separate")

    @property
    def run_root(self) -> Path:
        return self.inbox / f"fullspace-distill-{self.run_id}"

    @property
    def parent_root(self) -> Path:
        return self.inbox / f"fullspace-sweep-{self.parent_run}"

    @property
    def bundle(self) -> Path:
        return self.parent_root / "bundle"

    @property
    def worker(self) -> Path:
        return self.run_root / "worker.py"

    @property
    def state_path(self) -> Path:
        return self.run_root / "state.json"


@dataclass(frozen=True)
class PairGenome:
    bandgap_columns: tuple[int, ...]
    formation_columns: tuple[int, ...]
    generation: int = 0
    origin: str = "candidate"
    parents: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for target, columns in self.masks.items():
            if len(columns) < MINIMUM_TARGET_COLUMNS:
                raise ValueError(
                    f"{target} mask must contain at least {MINIMUM_TARGET_COLUMNS} columns"
                )
            if tuple(sorted(set(columns))) != columns or columns[0] < 0:
                raise ValueError(f"{target} mask must be sorted, unique, and nonnegative")

    @property
    def masks(self) -> dict[str, tuple[int, ...]]:
        return {
            BANDGAP_TARGET: self.bandgap_columns,
            FORMATION_TARGET: self.formation_columns,
        }

    @property
    def union(self) -> tuple[int, ...]:
        return tuple(sorted(set(self.bandgap_columns) | set(self.formation_columns)))

    @property
    def pair_id(self) -> str:
        return (
            "p-"
            + canonical_hash(
                {
                    BANDGAP_TARGET: self.bandgap_columns,
                    FORMATION_TARGET: self.formation_columns,
                }
            )[:20]
        )

    @property
    def canonical_hash(self) -> str:
        return canonical_hash(
            {
                BANDGAP_TARGET: self.bandgap_columns,
                FORMATION_TARGET: self.formation_columns,
            }
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "canonical_hash": self.canonical_hash,
            "generation": self.generation,
            "origin": self.origin,
            "parents": list(self.parents),
            "target_masks": {target: list(columns) for target, columns in self.masks.items()},
            "target_mask_counts": {target: len(columns) for target, columns in self.masks.items()},
            "summed_target_mask_size": len(self.bandgap_columns) + len(self.formation_columns),
            "union": list(self.union),
            "union_count": len(self.union),
            "test_labels_used": False,
        }


def make_pair(
    bandgap_columns: Iterable[int],
    formation_columns: Iterable[int],
    *,
    generation: int = 0,
    origin: str = "candidate",
    parents: Sequence[str] = (),
) -> PairGenome:
    return PairGenome(
        bandgap_columns=tuple(sorted(set(map(int, bandgap_columns)))),
        formation_columns=tuple(sorted(set(map(int, formation_columns)))),
        generation=generation,
        origin=origin,
        parents=tuple(map(str, parents)),
    )


def _pair_from_dict(value: Mapping[str, Any]) -> PairGenome:
    masks = value["target_masks"]
    return make_pair(
        masks[BANDGAP_TARGET],
        masks[FORMATION_TARGET],
        generation=int(value.get("generation", 0)),
        origin=str(value.get("origin", "candidate")),
        parents=value.get("parents", ()),
    )


def union_count(bandgap_columns: Iterable[int], formation_columns: Iterable[int]) -> int:
    return len(set(map(int, bandgap_columns)) | set(map(int, formation_columns)))


def pareto_front(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return the deterministic RMSLE/unique-union nondominated archive."""
    unique: dict[str, dict[str, Any]] = {}
    for value in rows:
        row = dict(value)
        identity = str(row.get("pair_id", row.get("canonical_hash", canonical_hash(row))))
        current = unique.get(identity)
        key = (float(row["mean_rmsle"]), int(row["union_count"]), identity)
        if current is None or key < (
            float(current["mean_rmsle"]),
            int(current["union_count"]),
            identity,
        ):
            unique[identity] = row
    values = list(unique.values())
    front = []
    for row in values:
        dominated = any(
            other is not row
            and float(other["mean_rmsle"]) <= float(row["mean_rmsle"])
            and int(other["union_count"]) <= int(row["union_count"])
            and (
                float(other["mean_rmsle"]) < float(row["mean_rmsle"])
                or int(other["union_count"]) < int(row["union_count"])
            )
            for other in values
        )
        if not dominated:
            front.append(row)
    return sorted(
        front,
        key=lambda row: (
            int(row["union_count"]),
            float(row["mean_rmsle"]),
            int(row.get("summed_target_mask_size", 0)),
            str(row.get("canonical_hash", row.get("pair_id", ""))),
        ),
    )


def epsilon_select(
    rows: Sequence[Mapping[str, Any]], *, epsilon: float = EPSILON
) -> dict[str, Any]:
    if not rows:
        raise ValueError("no confirmed candidates")
    best = min(float(row["mean_rmsle"]) for row in rows)
    feasible = [row for row in rows if float(row["mean_rmsle"]) <= best + epsilon + 1e-15]
    return dict(
        min(
            feasible,
            key=lambda row: (
                int(row["union_count"]),
                float(row["mean_rmsle"]),
                int(row["summed_target_mask_size"]),
                str(row["canonical_hash"]),
            ),
        )
    )


def derive_confirmation_seeds(
    parent_bundle_hash: str,
    run_id: str,
    *,
    count: int = 2,
    forbidden: Iterable[int] = (),
) -> tuple[int, ...]:
    """Derive fresh positive 31-bit seeds from the parent and run identity."""
    used = set(map(int, forbidden))
    seeds: list[int] = []
    for ordinal in range(count):
        attempt = 0
        while True:
            digest = hashlib.sha256(
                f"{parent_bundle_hash}:{run_id}:{ordinal}:{attempt}".encode("utf-8")
            ).digest()
            seed = int.from_bytes(digest[:8], "big") % (2**31 - 2) + 1
            if seed not in used:
                break
            attempt += 1
        seeds.append(seed)
        used.add(seed)
    return tuple(seeds)


def ranking_positions(ranking: pd.DataFrame, width: int) -> np.ndarray:
    columns = ranking["feature_index"].astype(int).to_numpy()
    if sorted(columns.tolist()) != list(range(width)):
        raise DistillError("parent ranking is not a complete feature permutation")
    positions = np.empty(width, dtype=np.float64)
    positions[columns] = np.arange(1, width + 1, dtype=np.float64)
    return positions


def mutate_target_mask(
    mask: Sequence[int],
    opposite_mask: Sequence[int],
    rank_position: np.ndarray,
    rng: np.random.Generator,
    *,
    operation: str | None = None,
    mutation_count: int | None = None,
    minimum: int = MINIMUM_TARGET_COLUMNS,
) -> tuple[int, ...]:
    """Rank-guided mutation that rewards overlap and drops weak exclusives."""
    width = len(rank_position)
    present = set(map(int, mask))
    opposite = set(map(int, opposite_mask))
    if not present or min(present) < 0 or max(present) >= width:
        raise ValueError("mask contains an out-of-range column")
    if len(present) < minimum:
        raise ValueError("mask is below the target minimum")
    selected_operation = operation or str(rng.choice(["drop", "add", "swap"], p=[0.35, 0.2, 0.45]))
    if selected_operation not in {"drop", "add", "swap"}:
        raise ValueError(f"unknown mutation operation: {selected_operation}")
    count = mutation_count or min(32, max(1, round(len(present) * float(rng.uniform(0.01, 0.05)))))

    def drop_one() -> bool:
        if len(present) <= minimum:
            return False
        candidates = np.asarray(sorted(present), dtype=np.int64)
        weights = rank_position[candidates].astype(np.float64)
        weights *= np.where(np.isin(candidates, list(opposite)), 0.25, 3.0)
        weights /= weights.sum()
        present.remove(int(rng.choice(candidates, p=weights)))
        return True

    def add_one() -> bool:
        candidates = np.asarray(sorted(set(range(width)) - present), dtype=np.int64)
        if not len(candidates):
            return False
        weights = 1.0 / np.sqrt(rank_position[candidates])
        weights *= np.where(np.isin(candidates, list(opposite)), 4.0, 1.0)
        weights /= weights.sum()
        present.add(int(rng.choice(candidates, p=weights)))
        return True

    for _ in range(count):
        if selected_operation == "drop":
            drop_one()
        elif selected_operation == "add":
            add_one()
        else:
            removed = drop_one()
            if removed:
                add_one()
            else:
                add_one()
    return tuple(sorted(present))


def crossover_target_masks(
    left: Sequence[int],
    right: Sequence[int],
    opposite_mask: Sequence[int],
    rank_position: np.ndarray,
    rng: np.random.Generator,
    *,
    minimum: int = MINIMUM_TARGET_COLUMNS,
) -> tuple[int, ...]:
    """Crossover uses target rank and opposite-mask overlap for optional genes."""
    left_set, right_set = set(left), set(right)
    inherited = left_set & right_set
    optional = np.asarray(sorted(left_set ^ right_set), dtype=np.int64)
    target_size = max(
        minimum,
        round((len(left_set) + len(right_set)) / 2 * float(rng.uniform(0.92, 1.08))),
    )
    take = min(len(optional), max(0, target_size - len(inherited)))
    if take:
        weights = 1.0 / np.sqrt(rank_position[optional])
        weights *= np.where(np.isin(optional, list(opposite_mask)), 3.0, 1.0)
        weights /= weights.sum()
        inherited.update(rng.choice(optional, size=take, replace=False, p=weights).tolist())
    if len(inherited) < minimum:
        candidates = np.asarray(sorted((left_set | right_set) - inherited), dtype=np.int64)
        need = min(len(candidates), minimum - len(inherited))
        if need:
            weights = 1.0 / np.sqrt(rank_position[candidates])
            weights /= weights.sum()
            inherited.update(rng.choice(candidates, size=need, replace=False, p=weights).tolist())
    return tuple(sorted(inherited))


def mutate_pair(
    pair: PairGenome,
    rankings: Mapping[str, np.ndarray],
    rng: np.random.Generator,
    *,
    generation: int,
    operation: str | None = None,
) -> PairGenome:
    bandgap = mutate_target_mask(
        pair.bandgap_columns,
        pair.formation_columns,
        rankings[BANDGAP_TARGET],
        rng,
        operation=operation,
    )
    formation = mutate_target_mask(
        pair.formation_columns,
        bandgap,
        rankings[FORMATION_TARGET],
        rng,
        operation=operation,
    )
    return make_pair(
        bandgap,
        formation,
        generation=generation,
        origin="overlap-aware-rank-mutation",
        parents=(pair.pair_id,),
    )


def crossover_pair(
    left: PairGenome,
    right: PairGenome,
    rankings: Mapping[str, np.ndarray],
    rng: np.random.Generator,
    *,
    generation: int,
) -> PairGenome:
    provisional_formation = set(left.formation_columns) | set(right.formation_columns)
    bandgap = crossover_target_masks(
        left.bandgap_columns,
        right.bandgap_columns,
        provisional_formation,
        rankings[BANDGAP_TARGET],
        rng,
    )
    formation = crossover_target_masks(
        left.formation_columns,
        right.formation_columns,
        bandgap,
        rankings[FORMATION_TARGET],
        rng,
    )
    crossed = make_pair(
        bandgap,
        formation,
        generation=generation,
        origin="overlap-aware-crossover",
        parents=(left.pair_id, right.pair_id),
    )
    return mutate_pair(crossed, rankings, rng, generation=generation)


def initial_pair_population(
    pareto_seeds: Sequence[PairGenome],
    controls: Sequence[PairGenome],
    rankings: Mapping[str, np.ndarray],
    *,
    population_size: int = POPULATION_SIZE,
    seed: int = SEARCH_SEED,
) -> list[PairGenome]:
    """Seed generation zero with every confirmed Pareto pair and both controls."""
    unique: dict[str, PairGenome] = {}
    for pair in [*pareto_seeds, *controls]:
        unique.setdefault(pair.pair_id, replace(pair, generation=0))
    if len(unique) > population_size:
        raise DistillError("confirmed Pareto seeds exceed the 24-pair population")
    rng = np.random.default_rng(seed)
    population = list(unique.values())
    attempts = 0
    while len(population) < population_size:
        attempts += 1
        if attempts > population_size * 2_000:
            raise RuntimeError("could not create a unique paired generation-zero population")
        parent = population[int(rng.integers(0, len(population)))]
        candidate = mutate_pair(parent, rankings, rng, generation=0)
        if candidate.pair_id not in {item.pair_id for item in population}:
            population.append(candidate)
    return population


def breed_pair_population(
    archive: Sequence[tuple[PairGenome, float]],
    rankings: Mapping[str, np.ndarray],
    *,
    generation: int,
    population_size: int = POPULATION_SIZE,
    seed: int = SEARCH_SEED,
) -> list[PairGenome]:
    if generation <= 0 or len(archive) < 4:
        raise ValueError("pair breeding needs a positive generation and four archived pairs")
    best: dict[str, tuple[PairGenome, float]] = {}
    for pair, score in archive:
        current = best.get(pair.pair_id)
        if current is None or float(score) < current[1]:
            best[pair.pair_id] = (pair, float(score))
    rows = [
        {
            **pair.as_dict(),
            "mean_rmsle": score,
        }
        for pair, score in best.values()
    ]
    front_ids = {row["pair_id"] for row in pareto_front(rows)}
    ordered = sorted(
        best.values(),
        key=lambda item: (
            item[0].pair_id not in front_ids,
            item[1],
            len(item[0].union),
            item[0].pair_id,
        ),
    )
    rng = np.random.default_rng(seed + generation * 10_007)
    children = [
        replace(pair, generation=generation, origin="pareto-elite", parents=(pair.pair_id,))
        for pair, _score in ordered[:4]
    ]
    used = {pair.pair_id for pair in children}
    attempts = 0
    while len(children) < population_size:
        attempts += 1
        if attempts > population_size * 4_000:
            raise RuntimeError("paired search exhausted unique crossover mutations")

        def tournament() -> PairGenome:
            choices = rng.choice(len(ordered), size=min(4, len(ordered)), replace=False)
            return min(
                (ordered[int(index)] for index in choices),
                key=lambda item: (
                    item[0].pair_id not in front_ids,
                    item[1],
                    len(item[0].union),
                    item[0].pair_id,
                ),
            )[0]

        candidate = crossover_pair(tournament(), tournament(), rankings, rng, generation=generation)
        if candidate.pair_id not in used and candidate.pair_id not in best:
            children.append(candidate)
            used.add(candidate.pair_id)
    return children


def choose_nondominated_finalists(
    rows: Sequence[Mapping[str, Any]], *, limit: int = FINALIST_LIMIT
) -> list[dict[str, Any]]:
    front = pareto_front(rows)
    if len(front) <= limit:
        return front
    indices = np.linspace(0, len(front) - 1, num=limit)
    selected = sorted({int(round(value)) for value in indices})
    return [front[index] for index in selected[:limit]]


def _state(settings: Settings) -> dict[str, Any]:
    if not settings.state_path.exists():
        return {
            "run_id": settings.run_id,
            "parent_run": settings.parent_run,
            "created_at": utc_now(),
            "completed_phases": [],
            "test_labels_used": False,
        }
    return json.loads(settings.state_path.read_text(encoding="utf-8"))


def _complete_phase(settings: Settings, phase: str, receipt: Mapping[str, Any]) -> None:
    if phase not in PHASES:
        raise DistillError(f"unknown phase: {phase}")
    payload = {
        **dict(receipt),
        "phase": phase,
        "completed_at": utc_now(),
        "test_labels_used": False,
    }
    atomic_json(settings.run_root / f"receipts/{phase}.json", payload)
    state = _state(settings)
    completed = list(state.get("completed_phases", []))
    if phase not in completed:
        completed.append(phase)
    state.update(
        {
            "completed_phases": completed,
            "last_phase": phase,
            "updated_at": utc_now(),
            "test_labels_used": False,
        }
    )
    atomic_json(settings.state_path, state)


def _parent_required_files(settings: Settings) -> list[Path]:
    relative = [
        "verification.json",
        "protocol.json",
        "worker.py",
        "bundle/bundle_manifest.json",
        "bundle/feature_registry.parquet",
        "bundle/feature_registry.csv",
        "genetic/genomes.json",
        "genetic/finalists.json",
        "confirmation/preregistration.json",
        "confirmation/results.json",
        "confirmation/score_curve.parquet",
        "confirmation/fold_scores.parquet",
    ]
    for target in TARGETS:
        relative.append(f"importance/ranking_{target}.parquet")
        relative.extend(
            f"importance/ranking_{target}_fold_{fold}.parquet" for fold in range(DISCOVERY_FOLDS)
        )
    return [settings.parent_root / item for item in relative]


def _parent_lock(settings: Settings) -> dict[str, str]:
    missing = [path for path in _parent_required_files(settings) if not path.is_file()]
    if missing:
        raise DistillError(f"parent artifacts are incomplete: {missing[:5]}")
    return {
        str(path.relative_to(settings.parent_root)): sha256_file(path)
        for path in _parent_required_files(settings)
    }


def verify_parent_lock(settings: Settings, protocol: Mapping[str, Any]) -> dict[str, Any]:
    parent_verification = json.loads(
        (settings.parent_root / "verification.json").read_text(encoding="utf-8")
    )
    if parent_verification.get("complete") is not True:
        raise DistillError("parent sweep is not verified complete")
    if parent_verification.get("test_labels_used") is not False:
        raise DistillError("parent verification does not exclude test labels")
    bundle = verify_full_space_bundle(settings.bundle)
    if bundle["bundle_sha256"] != protocol.get("parent_bundle_sha256"):
        raise DistillError("parent bundle identity drift")
    locked = protocol.get("parent_files", {})
    if locked != _parent_lock(settings):
        raise DistillError("parent controller/artifact hash drift")
    parent_protocol = json.loads(
        (settings.parent_root / "protocol.json").read_text(encoding="utf-8")
    )
    recorded_controller = parent_protocol.get("controller_sha256")
    if recorded_controller is not None:
        if recorded_controller != protocol.get("parent_controller_sha256"):
            raise DistillError("parent controller hash drift")
    elif sha256_file(PARENT_CONTROLLER_SOURCE) != protocol.get("parent_controller_sha256"):
        raise DistillError("hash-locked parent controller source drift")
    if parent_protocol.get("worker_sha256") != protocol.get("parent_worker_sha256"):
        raise DistillError("parent worker hash drift")
    return bundle


def verify_halted_r3_archive(root: Path = DEFAULT_R3_ARCHIVE) -> dict[str, Any]:
    """Read-only proof that r3 remains halted and historically unpriced."""
    halt_paths = sorted((root / "receipts/halts").glob("campaign-halt-*.json"))
    audit_paths = sorted((root / "receipts/cost-audits").glob("provider-cost-audit-*.json"))
    if not halt_paths or not audit_paths or not (root / "campaign.sqlite3").is_file():
        raise DistillError("r3 halt/cost archive is incomplete")
    halt_path = halt_paths[-1]
    halt = json.loads(halt_path.read_text(encoding="utf-8"))
    audits = [json.loads(path.read_text(encoding="utf-8")) for path in audit_paths]
    audit_pairs = [
        (path, value)
        for path, value in zip(audit_paths, audits)
        if value.get("historical_cost_verdict") == "unverified"
    ]
    if halt.get("new_state") != "halted_nonfree_route_unverified":
        raise DistillError("r3 halt receipt has the wrong state")
    if halt.get("workers") != [] or halt.get("shared_jnoccio_stopped") is not False:
        raise DistillError("r3 halt receipt does not preserve the shared Jnoccio service")
    if not audit_pairs:
        raise DistillError("r3 historical cost verdict is not unverified")
    audit_path, audit = audit_pairs[-1]
    if audit.get("actual_charges_usd") is not None:
        raise DistillError("r3 archive unexpectedly claims measured charges")
    summary = audit.get("summary", {})
    if summary.get("trace_rows") != 2_244 or summary.get("classifications") != {
        "unverifiable": 2_244
    }:
        raise DistillError("r3 trace audit is not the preserved 2,244-row unverifiable audit")
    with sqlite3.connect(f"file:{root / 'campaign.sqlite3'}?mode=ro", uri=True) as connection:
        row = connection.execute(
            "SELECT state FROM campaign WHERE run_id=?", ("gp-feature-foundry-20260720-r3",)
        ).fetchone()
    if row != ("halted_nonfree_route_unverified",):
        raise DistillError("r3 campaign database is not halted")
    live_workers = []
    proc = Path("/proc")
    for command_path in proc.glob("[0-9]*/cmdline"):
        try:
            command = (
                command_path.read_bytes().replace(b"\0", b" ").decode("utf-8", errors="replace")
            )
        except (OSError, PermissionError):
            continue
        if "gp-feature-foundry-20260720-r3" in command and "full_space_distill" not in command:
            live_workers.append(command_path.parent.name)
    if live_workers:
        raise DistillError(f"r3 campaign workers are still live: {live_workers[:5]}")
    return {
        "schema": "R3ContainmentProof.v1",
        "run_id": "gp-feature-foundry-20260720-r3",
        "campaign_state": row[0],
        "halt_receipt": str(halt_path),
        "halt_receipt_sha256": sha256_file(halt_path),
        "shared_jnoccio_stopped": False,
        "campaign_workers": [],
        "historical_cost_verdict": "unverified",
        "actual_charges_usd": None,
        "audited_traces": 2_244,
        "unverifiable_traces": 2_244,
        "cost_audit": str(audit_path),
        "cost_audit_sha256": sha256_file(audit_path),
        "checked_at": utc_now(),
    }


def _load_parent_pairs(settings: Settings) -> dict[str, Any]:
    prereg = json.loads(
        (settings.parent_root / "confirmation/preregistration.json").read_text(encoding="utf-8")
    )
    curve = pd.read_parquet(settings.parent_root / "confirmation/score_curve.parquet")
    views: dict[str, dict[str, dict[str, Any]]] = {}
    scores: dict[tuple[str, str], float] = {}
    for target in TARGETS:
        members = [*prereg[target]["finalists"], *prereg[target]["controls"]]
        views[target] = {str(value["genome_id"]): value for value in members}
        target_curve = curve[curve["target"] == target]
        scores.update(
            {
                (target, str(row["view"])): float(row["mean_rmsle"])
                for row in target_curve.to_dict(orient="records")
            }
        )
        if set(views[target]) != {
            view for candidate_target, view in scores if candidate_target == target
        }:
            raise DistillError(f"parent preregistration/confirmation drift for {target}")
    pairs: list[dict[str, Any]] = []
    pair_objects: dict[str, PairGenome] = {}
    for bandgap_id, bandgap in views[BANDGAP_TARGET].items():
        for formation_id, formation in views[FORMATION_TARGET].items():
            pair = make_pair(
                bandgap["columns"],
                formation["columns"],
                origin=f"parent-confirmed:{bandgap_id}+{formation_id}",
            )
            row = {
                **pair.as_dict(),
                "bandgap_parent_view": bandgap_id,
                "formation_parent_view": formation_id,
                "target_mean_rmsle": {
                    BANDGAP_TARGET: scores[(BANDGAP_TARGET, bandgap_id)],
                    FORMATION_TARGET: scores[(FORMATION_TARGET, formation_id)],
                },
                "mean_rmsle": float(
                    np.mean(
                        [
                            scores[(BANDGAP_TARGET, bandgap_id)],
                            scores[(FORMATION_TARGET, formation_id)],
                        ]
                    )
                ),
            }
            pairs.append(row)
            pair_objects[pair.pair_id] = pair
    results = json.loads(
        (settings.parent_root / "confirmation/results.json").read_text(encoding="utf-8")
    )
    winner_ids = {target: str(results["winners"][target]["genome_id"]) for target in TARGETS}
    accuracy = next(
        row
        for row in pairs
        if row["bandgap_parent_view"] == winner_ids[BANDGAP_TARGET]
        and row["formation_parent_view"] == winner_ids[FORMATION_TARGET]
    )
    compact = epsilon_select(pairs)
    controls = {
        "accuracy-control": accuracy,
        "compact-epsilon-control": compact,
    }
    bundle_manifest = json.loads(
        (settings.bundle / "bundle_manifest.json").read_text(encoding="utf-8")
    )
    if int(bundle_manifest.get("predictors", 0)) == 12_419:
        checks = (
            (accuracy, EXPECTED_ACCURACY_UNION, EXPECTED_ACCURACY_MEAN, "accuracy"),
            (compact, EXPECTED_COMPACT_UNION, EXPECTED_COMPACT_MEAN, "compact"),
        )
        for row, expected_union, expected_mean, label in checks:
            if int(row["union_count"]) != expected_union or not math.isclose(
                float(row["mean_rmsle"]), expected_mean, rel_tol=0.0, abs_tol=1e-15
            ):
                raise DistillError(f"parent {label} control drift")
    front = pareto_front(pairs)
    return {
        "pairs": pairs,
        "pair_objects": pair_objects,
        "pareto": front,
        "controls": controls,
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if pd.isna(value) else float(value)
    if pd.isna(value) if not isinstance(value, (str, bytes, bool)) else False:
        return None
    return value


def prepare(
    settings: Settings,
    *,
    worker_source: Path | None = None,
    gpu_smoke: bool = False,
    r3_archive: Path | None = DEFAULT_R3_ARCHIVE,
) -> dict[str, Any]:
    """Hash-lock the verified parent and create an isolated restartable run."""
    if "prepare" in _state(settings).get("completed_phases", []):
        protocol = json.loads((settings.run_root / "protocol.json").read_text(encoding="utf-8"))
        verify_parent_lock(settings, protocol)
        if sha256_file(settings.worker) != protocol.get("worker_sha256"):
            raise DistillError("prepared distillation worker drift")
        return protocol
    prohibit_test_labels([settings.run_root, settings.parent_root])
    parent_verification = json.loads(
        (settings.parent_root / "verification.json").read_text(encoding="utf-8")
    )
    if parent_verification.get("complete") is not True:
        raise DistillError("parent sweep verification is incomplete")
    bundle = verify_full_space_bundle(settings.bundle)
    parent_files = _parent_lock(settings)
    parent_protocol = json.loads(
        (settings.parent_root / "protocol.json").read_text(encoding="utf-8")
    )
    parent_controller_sha256 = parent_protocol.get("controller_sha256") or sha256_file(
        PARENT_CONTROLLER_SOURCE
    )
    settings.run_root.mkdir(parents=True, exist_ok=True)
    for directory in (
        "cache/model-results",
        "receipts/schedules",
        "search",
        "rescore",
        "confirmation",
        "exports",
        "reports",
        "final_hashes",
    ):
        (settings.run_root / directory).mkdir(parents=True, exist_ok=True)
    source = worker_source or Path(__file__).with_name("full_space_sweep_worker.py")
    if not source.is_file():
        raise DistillError(f"worker source is missing: {source}")
    temporary = settings.worker.with_name(f".{settings.worker.name}.{os.getpid()}.tmp")
    shutil.copy2(source, temporary)
    os.replace(temporary, settings.worker)
    parent_pairs = _load_parent_pairs(settings)
    atomic_json(
        settings.run_root / "search/parent_pareto_seeds.json",
        {
            "pairs": parent_pairs["pareto"],
            "test_labels_used": False,
        },
    )
    atomic_json(
        settings.run_root / "search/controls.json",
        {
            "controls": parent_pairs["controls"],
            "test_labels_used": False,
        },
    )
    forbidden = set(map(int, parent_protocol.get("sweep_seeds", SWEEP_SEEDS)))
    forbidden.add(int(parent_protocol.get("discovery_fold_seed", DISCOVERY_FOLD_SEED)))
    forbidden.update(map(int, parent_protocol.get("sealed_seeds", SEALED_SEEDS)))
    confirmation_seeds = derive_confirmation_seeds(
        str(bundle["bundle_sha256"]), settings.run_id, forbidden=forbidden
    )
    containment = None
    if r3_archive is not None and r3_archive.exists():
        containment = verify_halted_r3_archive(r3_archive)
        atomic_json(settings.run_root / "receipts/r3_containment.json", containment)
    identity = None
    smoke = None
    if gpu_smoke:
        host = Host("local", "/usr/bin/python3", settings.bundle, settings.worker)
        identity = _json_command(host, ["--identity"], timeout=60)
        if identity.get("packages", {}).get("catboost") != CATBOOST_VERSION:
            raise DistillError(f"CatBoost {CATBOOST_VERSION} is required")
        smoke = _json_command(host, ["--smoke"], timeout=120)
    protocol = {
        "protocol": "nomad-full-space-distill-v1",
        "run_id": settings.run_id,
        "parent_run": settings.parent_run,
        "parent_files": parent_files,
        "parent_verification_sha256": parent_files["verification.json"],
        "parent_bundle_sha256": bundle["bundle_sha256"],
        "parent_registry_sha256": parent_files["bundle/feature_registry.parquet"],
        "parent_controller_sha256": parent_controller_sha256,
        "parent_controller_hash_source": (
            "parent protocol"
            if parent_protocol.get("controller_sha256")
            else str(PARENT_CONTROLLER_SOURCE)
        ),
        "parent_worker_sha256": parent_protocol.get("worker_sha256"),
        "controller_sha256": sha256_file(Path(__file__)),
        "worker_sha256": sha256_file(settings.worker),
        "metric": "RMSLE after clipping predictions to nonnegative values",
        "selection_rule": SELECTION_RULE,
        "epsilon": EPSILON,
        "model_parameters": MODEL_PARAMETERS,
        "search_seed": SEARCH_SEED,
        "search_cv_seeds": [DISCOVERY_FOLD_SEED],
        "rescore_cv_seeds": list(SWEEP_SEEDS),
        "confirmation_seeds": list(confirmation_seeds),
        "parent_seed_exclusions": sorted(forbidden),
        "folds": DISCOVERY_FOLDS,
        "search_trees": SCREEN_TREES,
        "rescore_trees": SCREEN_TREES,
        "confirmation_trees": CONFIRM_TREES,
        "population_size": POPULATION_SIZE,
        "generations": GENERATIONS,
        "finalist_limit": FINALIST_LIMIT,
        "minimum_target_columns": MINIMUM_TARGET_COLUMNS,
        "execution_contract": {
            "scheduler": "SCQ",
            "project": "xhyp3",
            "gpus": 1,
            "foreground": True,
            "detached_children": False,
            "remote_gpu_use": False,
        },
        "gpu_identity": identity,
        "gpu_smoke": smoke,
        "r3_containment": containment,
        "test_labels_used": False,
    }
    atomic_json(settings.run_root / "protocol.json", protocol)
    _complete_phase(
        settings,
        "prepare",
        {
            "parent_bundle_sha256": bundle["bundle_sha256"],
            "parent_files_locked": len(parent_files),
            "parent_pareto_pairs": len(parent_pairs["pareto"]),
            "accuracy_control_union": parent_pairs["controls"]["accuracy-control"]["union_count"],
            "compact_control_union": parent_pairs["controls"]["compact-epsilon-control"][
                "union_count"
            ],
            "confirmation_seeds": list(confirmation_seeds),
            "r3_containment_verified": containment is not None,
            "gpu_smoke_passed": smoke is not None if gpu_smoke else None,
        },
    )
    return protocol


def _rankings(settings: Settings) -> dict[str, np.ndarray]:
    width = int(
        json.loads((settings.bundle / "bundle_manifest.json").read_text(encoding="utf-8"))[
            "predictors"
        ]
    )
    return {
        target: ranking_positions(
            pd.read_parquet(settings.parent_root / f"importance/ranking_{target}.parquet"),
            width,
        )
        for target in TARGETS
    }


def _jobs_for_pairs(
    pairs: Sequence[PairGenome],
    *,
    seeds: Sequence[int],
    iterations: int,
    stage: str,
) -> list[dict[str, Any]]:
    jobs: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for pair in pairs:
        for target, columns in pair.masks.items():
            mask_hash = canonical_hash(columns)
            for seed in seeds:
                for fold in range(DISCOVERY_FOLDS):
                    key = (target, mask_hash, int(seed), fold)
                    jobs.setdefault(
                        key,
                        _new_job(
                            kind="confirm" if iterations == CONFIRM_TREES else "screen",
                            stage=stage,
                            target=target,
                            view=f"m-{mask_hash[:20]}",
                            origin=pair.origin,
                            fold=fold,
                            cv_seed=int(seed),
                            model_seed=int(seed),
                            columns=list(columns),
                            feature_count=len(columns),
                            feature_set_hash=mask_hash,
                            iterations=iterations,
                        ),
                    )
    return list(jobs.values())


def _record_schedule(settings: Settings, stage: str, jobs: Sequence[dict[str, Any]]) -> None:
    protocol = json.loads((settings.run_root / "protocol.json").read_text(encoding="utf-8"))
    bundle_hash = str(protocol["parent_bundle_sha256"])
    worker_hash = sha256_file(settings.worker)
    payload = {
        "stage": stage,
        "job_count": len(jobs),
        "job_ids": [job["job_id"] for job in jobs],
        "cache_keys": [
            cache_identity(bundle_hash=bundle_hash, worker_hash=worker_hash, job=job)
            for job in jobs
        ],
        "schedule_sha256": canonical_hash(jobs),
        "test_labels_used": False,
    }
    atomic_json(settings.run_root / f"receipts/schedules/{stage}.json", payload)


def _score_pairs(
    settings: Settings,
    scheduler: Any,
    pairs: Sequence[PairGenome],
    *,
    seeds: Sequence[int],
    iterations: int,
    stage: str,
) -> tuple[list[dict[str, Any]], pd.DataFrame]:
    jobs = _jobs_for_pairs(pairs, seeds=seeds, iterations=iterations, stage=stage)
    _record_schedule(settings, stage, jobs)
    results = scheduler.run(stage, jobs)
    lookup = {
        (
            str(job["target"]),
            str(job["feature_set_hash"]),
            int(job["cv_seed"]),
            int(job["fold"]),
        ): (job, result)
        for job, result in results
    }
    summaries: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    for pair in pairs:
        target_metrics: dict[str, Any] = {}
        for target, columns in pair.masks.items():
            mask_hash = canonical_hash(columns)
            scores = []
            seed_means: dict[str, float] = {}
            for seed in seeds:
                seed_scores = []
                for fold in range(DISCOVERY_FOLDS):
                    job, result = lookup[(target, mask_hash, int(seed), fold)]
                    score = float(result["score"])
                    scores.append(score)
                    seed_scores.append(score)
                    ledger.append(
                        {
                            "stage": stage,
                            "pair_id": pair.pair_id,
                            "target": target,
                            "mask_hash": mask_hash,
                            "mask_count": len(columns),
                            "union_count": len(pair.union),
                            "cv_seed": int(seed),
                            "fold": fold,
                            "trees": iterations,
                            "rmsle": score,
                            "job_id": job["job_id"],
                            "test_labels_used": False,
                        }
                    )
                seed_means[str(seed)] = float(np.mean(seed_scores))
            target_metrics[target] = {
                "mean_rmsle": float(np.mean(scores)),
                "rmsle_std": float(np.std(scores)),
                "seed_means": seed_means,
                "model_jobs": len(scores),
                "mask_count": len(columns),
                "mask_hash": mask_hash,
            }
        summaries.append(
            {
                **pair.as_dict(),
                "target_metrics": target_metrics,
                "mean_rmsle": float(
                    np.mean([target_metrics[target]["mean_rmsle"] for target in TARGETS])
                ),
                "model_jobs": len(TARGETS) * len(seeds) * DISCOVERY_FOLDS,
            }
        )
    return summaries, pd.DataFrame(ledger)


def _run_search(settings: Settings, scheduler: Any) -> dict[str, Any]:
    seeds_payload = json.loads(
        (settings.run_root / "search/parent_pareto_seeds.json").read_text(encoding="utf-8")
    )
    controls_payload = json.loads(
        (settings.run_root / "search/controls.json").read_text(encoding="utf-8")
    )
    pareto_seeds = [_pair_from_dict(value) for value in seeds_payload["pairs"]]
    controls = [
        _pair_from_dict(controls_payload["controls"][name])
        for name in ("accuracy-control", "compact-epsilon-control")
    ]
    rankings = _rankings(settings)
    population = initial_pair_population(pareto_seeds, controls, rankings)
    archive: list[tuple[PairGenome, float]] = []
    history: list[dict[str, Any]] = []
    ledgers: list[pd.DataFrame] = []
    for generation in range(GENERATIONS):
        summaries, ledger = _score_pairs(
            settings,
            scheduler,
            population,
            seeds=(DISCOVERY_FOLD_SEED,),
            iterations=SCREEN_TREES,
            stage=f"search-{generation:02d}",
        )
        history.extend(summaries)
        ledgers.append(ledger)
        by_id = {pair.pair_id: pair for pair in population}
        archive.extend((by_id[str(row["pair_id"])], float(row["mean_rmsle"])) for row in summaries)
        atomic_json(
            settings.run_root / f"search/generation-{generation:02d}.json",
            {
                "generation": generation,
                "pairs": summaries,
                "pareto": pareto_front(history),
                "test_labels_used": False,
            },
        )
        if generation + 1 < GENERATIONS:
            population = breed_pair_population(archive, rankings, generation=generation + 1)
    grid = Counter(int(row["generation"]) for row in history)
    if grid != Counter({generation: POPULATION_SIZE for generation in range(GENERATIONS)}):
        raise AssertionError("paired search is not a terminal 24-by-10 grid")
    history_frame = pd.DataFrame(
        [
            {
                key: value
                for key, value in row.items()
                if key not in {"target_masks", "union", "target_metrics", "parents"}
            }
            | {
                "bandgap_count": row["target_mask_counts"][BANDGAP_TARGET],
                "formation_count": row["target_mask_counts"][FORMATION_TARGET],
                "target_metrics_json": json.dumps(row["target_metrics"], sort_keys=True),
                "test_labels_used": False,
            }
            for row in history
        ]
    )
    save_frame(history_frame, settings.run_root / "search/history")
    save_frame(pd.concat(ledgers, ignore_index=True), settings.run_root / "search/fold_scores")
    front = pareto_front(history)
    atomic_json(
        settings.run_root / "search/pareto_archive.json",
        {"pairs": front, "test_labels_used": False},
    )
    save_frame(
        pd.DataFrame(
            [
                {
                    key: value
                    for key, value in row.items()
                    if key not in {"target_masks", "union", "target_metrics", "parents"}
                }
                for row in front
            ]
        ),
        settings.run_root / "search/pareto_archive",
    )
    receipt = {
        "population_size": POPULATION_SIZE,
        "generations": GENERATIONS,
        "evaluated_pairs": len(history),
        "pareto_pairs": len(front),
        "minimum_target_columns": MINIMUM_TARGET_COLUMNS,
    }
    _complete_phase(settings, "search", receipt)
    return receipt


def _run_rescore(settings: Settings, scheduler: Any) -> dict[str, Any]:
    archive = json.loads(
        (settings.run_root / "search/pareto_archive.json").read_text(encoding="utf-8")
    )["pairs"]
    finalists_rows = choose_nondominated_finalists(archive)
    finalists = [_pair_from_dict(value) for value in finalists_rows]
    summaries, ledger = _score_pairs(
        settings,
        scheduler,
        finalists,
        seeds=SWEEP_SEEDS,
        iterations=SCREEN_TREES,
        stage="rescore-finalists",
    )
    save_frame(ledger, settings.run_root / "rescore/fold_scores")
    atomic_json(
        settings.run_root / "rescore/results.json",
        {"finalists": summaries, "test_labels_used": False},
    )
    controls_payload = json.loads(
        (settings.run_root / "search/controls.json").read_text(encoding="utf-8")
    )["controls"]
    protocol = json.loads((settings.run_root / "protocol.json").read_text(encoding="utf-8"))
    preregistration = {
        "schema": "DistillPreregistration.v1",
        "registered_at": utc_now(),
        "adaptive_search_complete": True,
        "finalists": [
            {
                **row,
                "rescore": next(value for value in summaries if value["pair_id"] == row["pair_id"]),
            }
            for row in finalists_rows
        ],
        "controls": controls_payload,
        "confirmation_seeds": protocol["confirmation_seeds"],
        "folds_per_seed": DISCOVERY_FOLDS,
        "trees": CONFIRM_TREES,
        "test_labels_used": False,
    }
    preregistration["canonical_hash"] = canonical_hash(preregistration)
    atomic_json(settings.run_root / "confirmation/preregistration.json", preregistration)
    receipt = {
        "nondominated_finalists": len(finalists),
        "rescore_seeds": list(SWEEP_SEEDS),
        "folds_per_seed": DISCOVERY_FOLDS,
        "preregistration_sha256": sha256_file(
            settings.run_root / "confirmation/preregistration.json"
        ),
    }
    _complete_phase(settings, "rescore", receipt)
    return receipt


def _select_confirmed(
    rows: Sequence[Mapping[str, Any]], control_ids: Mapping[str, str]
) -> tuple[dict[str, Any], bool]:
    compact = next(
        row for row in rows if str(row["pair_id"]) == control_ids["compact-epsilon-control"]
    )
    new_rows = [row for row in rows if str(row["pair_id"]) not in set(control_ids.values())]
    if not new_rows or min(float(row["mean_rmsle"]) for row in new_rows) >= float(
        compact["mean_rmsle"]
    ):
        return dict(compact), True
    return epsilon_select(rows), False


def _run_confirmation(settings: Settings, scheduler: Any) -> dict[str, Any]:
    prereg = json.loads(
        (settings.run_root / "confirmation/preregistration.json").read_text(encoding="utf-8")
    )
    finalists = [_pair_from_dict(value) for value in prereg["finalists"]]
    control_names = ("accuracy-control", "compact-epsilon-control")
    controls = {name: _pair_from_dict(prereg["controls"][name]) for name in control_names}
    unique: dict[str, PairGenome] = {}
    for pair in [*finalists, *controls.values()]:
        unique.setdefault(pair.pair_id, pair)
    seeds = tuple(map(int, prereg["confirmation_seeds"]))
    summaries, ledger = _score_pairs(
        settings,
        scheduler,
        list(unique.values()),
        seeds=seeds,
        iterations=CONFIRM_TREES,
        stage="confirmation",
    )
    save_frame(ledger, settings.run_root / "confirmation/fold_scores")
    control_ids = {name: pair.pair_id for name, pair in controls.items()}
    for row in summaries:
        row["candidate_class"] = next(
            (name for name, pair_id in control_ids.items() if row["pair_id"] == pair_id),
            "new-finalist",
        )
    selected, fallback = _select_confirmed(summaries, control_ids)
    best = min(float(row["mean_rmsle"]) for row in summaries)
    for row in summaries:
        row["epsilon_feasible"] = float(row["mean_rmsle"]) <= best + EPSILON + 1e-15
        row["selected"] = row["pair_id"] == selected["pair_id"]
    curve = pd.DataFrame(
        [
            {
                key: value
                for key, value in row.items()
                if key not in {"target_masks", "union", "target_metrics", "parents"}
            }
            | {
                "bandgap_count": row["target_mask_counts"][BANDGAP_TARGET],
                "formation_count": row["target_mask_counts"][FORMATION_TARGET],
                "target_metrics_json": json.dumps(row["target_metrics"], sort_keys=True),
                "test_labels_used": False,
            }
            for row in summaries
        ]
    )
    save_frame(curve, settings.run_root / "confirmation/score_curve")
    results = {
        "schema": "DistillConfirmationResults.v1",
        "candidates": summaries,
        "controls": control_ids,
        "best_confirmed_mean_rmsle": best,
        "selected": selected,
        "fallback_to_compact_control": fallback,
        "selection_rule": SELECTION_RULE,
        "confirmation_seeds": list(seeds),
        "folds_per_seed": DISCOVERY_FOLDS,
        "trees": CONFIRM_TREES,
        "test_labels_used": False,
    }
    results["canonical_hash"] = canonical_hash(results)
    atomic_json(settings.run_root / "confirmation/results.json", results)
    receipt = {
        "confirmed_candidates": len(summaries),
        "logical_model_results": len(ledger),
        "selected_pair_id": selected["pair_id"],
        "selected_union_count": selected["union_count"],
        "selected_mean_rmsle": selected["mean_rmsle"],
        "fallback_to_compact_control": fallback,
    }
    _complete_phase(settings, "confirmation", receipt)
    return receipt


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [_json_ready(row) for row in frame.to_dict(orient="records")]


def _run_report(settings: Settings) -> dict[str, Any]:
    confirmation = json.loads(
        (settings.run_root / "confirmation/results.json").read_text(encoding="utf-8")
    )
    selected = confirmation["selected"]
    pair = _pair_from_dict(selected)
    registry = pd.read_parquet(settings.bundle / "feature_registry.parquet").sort_values(
        "global_index"
    )
    expected = list(range(len(registry)))
    if registry["global_index"].astype(int).tolist() != expected:
        raise DistillError("frozen registry global indices are not exact and ordered")
    union_frame = registry.set_index("global_index").loc[list(pair.union)].reset_index()
    bandgap = set(pair.bandgap_columns)
    formation = set(pair.formation_columns)
    union_frame["used_by_bandgap"] = union_frame["global_index"].astype(int).isin(bandgap)
    union_frame["used_by_formation"] = union_frame["global_index"].astype(int).isin(formation)
    union_frame["test_labels_used"] = False
    union_csv = settings.run_root / "exports/distilled_union.csv"
    temporary = union_csv.with_name(f".{union_csv.name}.{os.getpid()}.tmp")
    union_frame.to_csv(temporary, index=False)
    os.replace(temporary, union_csv)
    masks = {
        "schema": "OrderedTargetMasks.v1",
        "target_masks": {target: list(columns) for target, columns in pair.masks.items()},
        "target_mask_hashes": {
            target: canonical_hash(columns) for target, columns in pair.masks.items()
        },
        "union": list(pair.union),
        "union_count": len(pair.union),
        "test_labels_used": False,
    }
    masks["canonical_hash"] = canonical_hash(masks)
    atomic_json(settings.run_root / "exports/target_masks.json", masks)
    confirmation_ledger = pd.read_parquet(settings.run_root / "confirmation/fold_scores.parquet")
    selected_folds = confirmation_ledger[confirmation_ledger["pair_id"] == pair.pair_id]
    protocol = json.loads((settings.run_root / "protocol.json").read_text(encoding="utf-8"))
    target_payload: dict[str, Any] = {}
    for target, columns in pair.masks.items():
        rows = union_frame[union_frame["global_index"].astype(int).isin(columns)]
        target_payload[target] = {
            "ordered_global_indices": list(columns),
            "ordered_feature_ids": rows.set_index("global_index")
            .loc[list(columns)]["feature_id"]
            .astype(str)
            .tolist(),
            "mask_count": len(columns),
            "mask_hash": canonical_hash(columns),
            "confirmed_metrics": selected["target_metrics"][target],
            "fold_results": _records(selected_folds[selected_folds["target"] == target]),
        }
    features = _records(union_frame)
    distilled = {
        "schema": "DistilledFeatureSet.v1",
        "run_id": settings.run_id,
        "parent_run": settings.parent_run,
        "parent_hashes": {
            "bundle_sha256": protocol["parent_bundle_sha256"],
            "verification_sha256": protocol["parent_verification_sha256"],
            "registry_sha256": protocol["parent_registry_sha256"],
            "controller_sha256": protocol["parent_controller_sha256"],
            "worker_sha256": protocol["parent_worker_sha256"],
        },
        "selection_rule": SELECTION_RULE,
        "selected_pair_id": pair.pair_id,
        "selected_pair_hash": pair.canonical_hash,
        "selected_mean_rmsle": selected["mean_rmsle"],
        "fallback_to_compact_control": confirmation["fallback_to_compact_control"],
        "target_masks": target_payload,
        "ordered_union_global_indices": list(pair.union),
        "ordered_union_feature_ids": union_frame["feature_id"].astype(str).tolist(),
        "union_count": len(pair.union),
        "features": features,
        "cv": {
            "search_seeds": protocol["search_cv_seeds"],
            "rescore_seeds": protocol["rescore_cv_seeds"],
            "confirmation_seeds": protocol["confirmation_seeds"],
            "folds": DISCOVERY_FOLDS,
        },
        "model_parameters": {
            "common": MODEL_PARAMETERS,
            "search_trees": SCREEN_TREES,
            "rescore_trees": SCREEN_TREES,
            "confirmation_trees": CONFIRM_TREES,
        },
        "canonical_hashes": {
            "bandgap_mask": canonical_hash(pair.bandgap_columns),
            "formation_mask": canonical_hash(pair.formation_columns),
            "union": canonical_hash(pair.union),
            "registry_rows": canonical_hash(features),
        },
        "test_labels_used": False,
    }
    distilled["canonical_hash"] = canonical_hash(distilled)
    atomic_json(settings.run_root / "exports/distilled_feature_set.json", distilled)

    search_history = pd.read_parquet(settings.run_root / "search/history.parquet").assign(
        curve_stage="search"
    )
    rescore = json.loads((settings.run_root / "rescore/results.json").read_text(encoding="utf-8"))[
        "finalists"
    ]
    rescore_frame = pd.DataFrame(
        [
            {
                "pair_id": row["pair_id"],
                "canonical_hash": row["canonical_hash"],
                "generation": row["generation"],
                "origin": row["origin"],
                "union_count": row["union_count"],
                "summed_target_mask_size": row["summed_target_mask_size"],
                "mean_rmsle": row["mean_rmsle"],
                "model_jobs": row["model_jobs"],
                "curve_stage": "rescore",
                "test_labels_used": False,
            }
            for row in rescore
        ]
    )
    confirmed_frame = pd.read_parquet(
        settings.run_root / "confirmation/score_curve.parquet"
    ).assign(curve_stage="confirmation")
    common = sorted(set(search_history) & set(rescore_frame) & set(confirmed_frame))
    pareto_curve = pd.concat(
        [
            search_history[common],
            rescore_frame[common],
            confirmed_frame[common],
        ],
        ignore_index=True,
    )
    pareto_curve["nondominated"] = False
    for stage in pareto_curve["curve_stage"].unique():
        stage_rows = pareto_curve[pareto_curve["curve_stage"] == stage]
        ids = {row["pair_id"] for row in pareto_front(stage_rows.to_dict(orient="records"))}
        pareto_curve.loc[
            (pareto_curve["curve_stage"] == stage) & pareto_curve["pair_id"].isin(ids),
            "nondominated",
        ] = True
    save_frame(pareto_curve, settings.run_root / "reports/pareto_curve")
    atomic_json(
        settings.run_root / "reports/pareto_curve.json",
        {"rows": _records(pareto_curve), "test_labels_used": False},
    )
    ledgers = []
    for path in (
        settings.run_root / "search/fold_scores.parquet",
        settings.run_root / "rescore/fold_scores.parquet",
        settings.run_root / "confirmation/fold_scores.parquet",
    ):
        ledgers.append(pd.read_parquet(path))
    save_frame(pd.concat(ledgers, ignore_index=True), settings.run_root / "reports/fold_ledger")
    controls = {
        name: next(
            row
            for row in confirmation["candidates"]
            if row["pair_id"] == confirmation["controls"][name]
        )
        for name in ("accuracy-control", "compact-epsilon-control")
    }
    report = {
        "schema": "FullSpaceDistillationReport.v1",
        "run_id": settings.run_id,
        "parent_run": settings.parent_run,
        "selected": {
            "pair_id": pair.pair_id,
            "mean_rmsle": selected["mean_rmsle"],
            "union_count": len(pair.union),
            "target_mask_counts": selected["target_mask_counts"],
        },
        "controls": {
            name: {
                "pair_id": row["pair_id"],
                "mean_rmsle": row["mean_rmsle"],
                "union_count": row["union_count"],
                "target_mask_counts": row["target_mask_counts"],
            }
            for name, row in controls.items()
        },
        "selection_rule": SELECTION_RULE,
        "fallback_to_compact_control": confirmation["fallback_to_compact_control"],
        "distilled_feature_set": "exports/distilled_feature_set.json",
        "union_csv": "exports/distilled_union.csv",
        "target_masks": "exports/target_masks.json",
        "pareto_curve": "reports/pareto_curve.parquet",
        "fold_ledger": "reports/fold_ledger.parquet",
        "test_labels_used": False,
    }
    report["canonical_hash"] = canonical_hash(report)
    atomic_json(settings.run_root / "reports/final.json", report)
    markdown = [
        "# NOMAD Full-Space Feature Distillation",
        "",
        f"Selected {len(pair.union):,} unique extraction columns at confirmed mean RMSLE "
        f"**{float(selected['mean_rmsle']):.10f}**.",
        "",
        "| Candidate | Unique union | Confirmed mean RMSLE |",
        "|---|---:|---:|",
        f"| Distilled selection | {len(pair.union):,} | {float(selected['mean_rmsle']):.10f} |",
        f"| Accuracy control | {int(controls['accuracy-control']['union_count']):,} | "
        f"{float(controls['accuracy-control']['mean_rmsle']):.10f} |",
        f"| Compact epsilon control | {int(controls['compact-epsilon-control']['union_count']):,} | "
        f"{float(controls['compact-epsilon-control']['mean_rmsle']):.10f} |",
        "",
        f"Compact-control fallback applied: `{confirmation['fallback_to_compact_control']}`.",
        "Test labels used: `false`.",
    ]
    report_md = settings.run_root / "reports/final.md"
    temporary_md = report_md.with_name(f".{report_md.name}.{os.getpid()}.tmp")
    temporary_md.write_text("\n".join(markdown) + "\n", encoding="utf-8")
    os.replace(temporary_md, report_md)
    artifact_paths = []
    for relative in ("worker.py", "protocol.json"):
        artifact_paths.append(settings.run_root / relative)
    for directory in ("search", "rescore", "confirmation", "exports", "reports"):
        artifact_paths.extend(
            path for path in sorted((settings.run_root / directory).rglob("*")) if path.is_file()
        )
    files = {str(path.relative_to(settings.run_root)): sha256_file(path) for path in artifact_paths}
    hashes = {
        "files": files,
        "parent_bundle_sha256": protocol["parent_bundle_sha256"],
        "distilled_feature_set_sha256": sha256_file(
            settings.run_root / "exports/distilled_feature_set.json"
        ),
        "report_sha256": sha256_file(settings.run_root / "reports/final.json"),
        "test_labels_used": False,
    }
    hashes["manifest_sha256"] = canonical_hash(hashes)
    atomic_json(settings.run_root / "final_hashes/manifest.json", hashes)
    receipt = {
        "selected_pair_id": pair.pair_id,
        "selected_union_count": len(pair.union),
        "selected_mean_rmsle": selected["mean_rmsle"],
        "artifact_files": len(files),
        "manifest_sha256": hashes["manifest_sha256"],
    }
    _complete_phase(settings, "report", receipt)
    return report


def _execution_assignment() -> dict[str, Any]:
    host = socket.gethostname()
    project = os.environ.get("NOMAD_DISTILL_SCQ_PROJECT", os.environ.get("SCQ_PROJECT"))
    job_id = next(
        (
            os.environ[name]
            for name in ("SCQ_JOB_ID", "JAIN_JOB_ID", "SMARTCLUSTER_JOB_ID")
            if os.environ.get(name)
        ),
        None,
    )
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if project != "xhyp3" or not job_id:
        raise DistillError("real distillation must run inside an xhyp3-project SCQ assignment")
    if visible is not None and len([item for item in visible.split(",") if item.strip()]) != 1:
        raise DistillError("SCQ distillation must expose exactly one GPU")
    return {
        "schema": "SCQForegroundAssignment.v1",
        "job_id": job_id,
        "host": host,
        "project": project,
        "visible_devices": visible,
        "gpus": 1,
        "foreground": True,
        "detached_children": False,
        "remote_gpu_use": False,
        "observed_at": utc_now(),
        "test_labels_used": False,
    }


def run(settings: Settings, *, scheduler: Any | None = None) -> dict[str, Any]:
    """Run every unfinished compute phase; model-result caches make this restartable."""
    state = _state(settings)
    if "prepare" not in state.get("completed_phases", []):
        raise DistillError("prepare must complete before run")
    protocol = json.loads((settings.run_root / "protocol.json").read_text(encoding="utf-8"))
    verify_parent_lock(settings, protocol)
    if sha256_file(Path(__file__)) != protocol.get("controller_sha256"):
        raise DistillError("distillation controller changed after prepare")
    if sha256_file(settings.worker) != protocol.get("worker_sha256"):
        raise DistillError("distillation worker changed after prepare")
    completed = set(state.get("completed_phases", []))
    compute_needed = any(phase not in completed for phase in ("search", "rescore", "confirmation"))
    active_scheduler = scheduler
    if compute_needed and active_scheduler is None:
        assignment = _execution_assignment()
        atomic_json(settings.run_root / "receipts/scq_assignment.json", assignment)
        host = Host("local", "/usr/bin/python3", settings.bundle, settings.worker)
        smoke = _json_command(host, ["--smoke"], timeout=120)
        atomic_json(
            settings.run_root / "receipts/gpu_smoke.json",
            {**smoke, "assignment": assignment, "test_labels_used": False},
        )
        active_scheduler = CampaignScheduler(settings, remote_host=None)
    if "search" not in completed:
        assert active_scheduler is not None
        _run_search(settings, active_scheduler)
        completed.add("search")
    if "rescore" not in completed:
        assert active_scheduler is not None
        _run_rescore(settings, active_scheduler)
        completed.add("rescore")
    if "confirmation" not in completed:
        assert active_scheduler is not None
        _run_confirmation(settings, active_scheduler)
        completed.add("confirmation")
    if "report" not in completed:
        _run_report(settings)
    return json.loads((settings.run_root / "reports/final.json").read_text(encoding="utf-8"))


def resume(settings: Settings, *, scheduler: Any | None = None) -> dict[str, Any]:
    return run(settings, scheduler=scheduler)


def record_scq_terminal(settings: Settings, receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Import the scheduler's post-controller terminal receipt for final verification."""
    payload = dict(receipt)
    required = {
        "state": "completed",
        "project": "xhyp3",
        "controller_exit_code": 0,
        "requested_gpus": 1,
        "assigned_gpus": 1,
        "foreground": True,
        "detached_children": False,
        "remote_gpu_use": False,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise DistillError(f"invalid SCQ terminal receipt field {key}: {payload.get(key)!r}")
    if (
        not payload.get("job_id")
        or not payload.get("controller_exited_at")
        or not payload.get("terminal_at")
    ):
        raise DistillError("SCQ terminal receipt lacks job/exit/terminal identity")
    payload.update(
        {
            "schema": "SCQTerminalReceipt.v1",
            "test_labels_used": False,
        }
    )
    atomic_json(settings.run_root / "receipts/scq_terminal.json", payload)
    return payload


def status(settings: Settings) -> dict[str, Any]:
    state = _state(settings)
    completed = list(state.get("completed_phases", []))
    next_phase = next((phase for phase in PHASES if phase not in completed), None)
    terminal = (settings.run_root / "receipts/scq_terminal.json").exists()
    payload: dict[str, Any] = {
        "run_id": settings.run_id,
        "parent_run": settings.parent_run,
        "run_root": str(settings.run_root),
        "completed_phases": completed,
        "next_phase": next_phase,
        "cached_fits": len(list((settings.run_root / "cache/model-results").glob("*.json")))
        if settings.run_root.exists()
        else 0,
        "controller_complete": next_phase is None,
        "scq_terminal_receipt": terminal,
        "complete": next_phase is None and terminal,
        "test_labels_used": False,
    }
    if (settings.run_root / "reports/final.json").exists():
        report = json.loads((settings.run_root / "reports/final.json").read_text(encoding="utf-8"))
        payload["selected"] = report.get("selected")
    return payload


def verify(settings: Settings) -> dict[str, Any]:
    """Recompute selection, registry identity, grids, caches, and artifact hashes."""
    missing: list[str] = []
    state = _state(settings)
    completed = set(state.get("completed_phases", []))
    for phase in PHASES:
        if phase not in completed:
            missing.append(f"phase: {phase}")
    protocol_path = settings.run_root / "protocol.json"
    protocol: dict[str, Any] = {}
    try:
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        verify_parent_lock(settings, protocol)
        constants = {
            "epsilon": EPSILON,
            "model_parameters": MODEL_PARAMETERS,
            "search_cv_seeds": [DISCOVERY_FOLD_SEED],
            "rescore_cv_seeds": list(SWEEP_SEEDS),
            "population_size": POPULATION_SIZE,
            "generations": GENERATIONS,
            "minimum_target_columns": MINIMUM_TARGET_COLUMNS,
        }
        for key, expected in constants.items():
            if protocol.get(key) != expected:
                missing.append(f"protocol lock: {key}")
        if sha256_file(Path(__file__)) != protocol.get("controller_sha256"):
            missing.append("controller hash")
        if sha256_file(settings.worker) != protocol.get("worker_sha256"):
            missing.append("worker hash")
        forbidden = set(map(int, protocol.get("parent_seed_exclusions", [])))
        seeds = tuple(map(int, protocol.get("confirmation_seeds", [])))
        if len(seeds) != 2 or len(set(seeds)) != 2 or forbidden.intersection(seeds):
            missing.append("two fresh confirmation seeds")
        elif seeds != derive_confirmation_seeds(
            str(protocol["parent_bundle_sha256"]),
            settings.run_id,
            forbidden=forbidden,
        ):
            missing.append("derived confirmation seed identity")
    except (OSError, ValueError, KeyError, DistillError) as error:
        missing.append(f"parent/protocol verification: {error}")
    history_path = settings.run_root / "search/history.parquet"
    if history_path.exists():
        history = pd.read_parquet(history_path)
        grid = history.groupby("generation").size()
        if len(grid) != GENERATIONS or not grid.eq(POPULATION_SIZE).all():
            missing.append("deterministic 24-pair, 10-generation search")
        if not history["model_jobs"].eq(len(TARGETS) * DISCOVERY_FOLDS).all():
            missing.append("five discovery folds per target mask")
    else:
        missing.append("paired search history")
    prereg_path = settings.run_root / "confirmation/preregistration.json"
    confirmation_path = settings.run_root / "confirmation/results.json"
    ledger_path = settings.run_root / "confirmation/fold_scores.parquet"
    if prereg_path.exists() and confirmation_path.exists() and ledger_path.exists():
        prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
        results = json.loads(confirmation_path.read_text(encoding="utf-8"))
        ledger = pd.read_parquet(ledger_path)
        if not 1 <= len(prereg.get("finalists", [])) <= FINALIST_LIMIT:
            missing.append("one to eight nondominated finalists")
        if set(prereg.get("controls", {})) != {
            "accuracy-control",
            "compact-epsilon-control",
        }:
            missing.append("both preregistered controls")
        expected_seeds = set(map(int, protocol.get("confirmation_seeds", [])))
        candidates = results.get("candidates", [])
        for row in candidates:
            pair_id = row["pair_id"]
            candidate_rows = ledger[ledger["pair_id"] == pair_id]
            expected_jobs = len(TARGETS) * len(expected_seeds) * DISCOVERY_FOLDS
            grid = candidate_rows.groupby(["target", "cv_seed", "fold"]).size()
            if len(grid) != expected_jobs or not grid.eq(1).all():
                missing.append(f"complete confirmation grid: {pair_id}")
                break
        control_ids = results.get("controls", {})
        try:
            expected_selected, expected_fallback = _select_confirmed(candidates, control_ids)
            selected = results["selected"]
            if selected["pair_id"] != expected_selected["pair_id"]:
                missing.append("smallest confirmed epsilon-feasible union")
            if bool(results.get("fallback_to_compact_control")) != expected_fallback:
                missing.append("compact-control nonregression fallback")
        except (KeyError, StopIteration, ValueError) as error:
            missing.append(f"confirmed selection: {error}")
    else:
        missing.append("preregistration and complete confirmation ledger")
    distilled_path = settings.run_root / "exports/distilled_feature_set.json"
    union_path = settings.run_root / "exports/distilled_union.csv"
    masks_path = settings.run_root / "exports/target_masks.json"
    if distilled_path.exists() and union_path.exists() and masks_path.exists():
        distilled = json.loads(distilled_path.read_text(encoding="utf-8"))
        union = pd.read_csv(union_path)
        masks = json.loads(masks_path.read_text(encoding="utf-8"))
        expected_hash = distilled.pop("canonical_hash", None)
        if canonical_hash(distilled) != expected_hash:
            missing.append("DistilledFeatureSet canonical hash")
        if distilled.get("schema") != "DistilledFeatureSet.v1":
            missing.append("DistilledFeatureSet.v1 schema")
        union_indices = union["global_index"].astype(int).tolist()
        if union_indices != sorted(set(union_indices)) or len(union_indices) != int(
            masks.get("union_count", -1)
        ):
            missing.append("ordered unique union accounting")
        for target, flag in (
            (BANDGAP_TARGET, "used_by_bandgap"),
            (FORMATION_TARGET, "used_by_formation"),
        ):
            target_mask = list(map(int, masks.get("target_masks", {}).get(target, [])))
            flagged = union.loc[union[flag].astype(bool), "global_index"].astype(int).tolist()
            if target_mask != flagged or not set(target_mask).issubset(union_indices):
                missing.append(f"{target}: exact subset of emitted union")
        registry = pd.read_parquet(settings.bundle / "feature_registry.parquet").set_index(
            "global_index"
        )
        resolved = registry.loc[union_indices]["feature_id"].astype(str).tolist()
        if resolved != union["feature_id"].astype(str).tolist():
            missing.append("all feature identities resolve to the frozen registry")
        if distilled.get("test_labels_used") is not False:
            missing.append("no test labels in distilled manifest")
    else:
        missing.append("distilled manifest, ordered masks, and union CSV")
    for schedule_path in sorted((settings.run_root / "receipts/schedules").glob("*.json")):
        schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
        absent = [
            key
            for key in schedule.get("cache_keys", [])
            if not (settings.run_root / f"cache/model-results/{key}.json").exists()
        ]
        if absent:
            missing.append(f"content-addressed cache completion: {schedule.get('stage')}")
            break
    terminal_path = settings.run_root / "receipts/scq_terminal.json"
    if terminal_path.exists():
        try:
            record_scq_terminal(settings, json.loads(terminal_path.read_text(encoding="utf-8")))
        except DistillError as error:
            missing.append(f"SCQ terminal completion: {error}")
    else:
        missing.append("SCQ terminal completion after controller exit")
    hashes_path = settings.run_root / "final_hashes/manifest.json"
    if hashes_path.exists():
        hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
        expected_hash = hashes.pop("manifest_sha256", None)
        if canonical_hash(hashes) != expected_hash:
            missing.append("final hash-manifest identity")
        drift = [
            relative
            for relative, digest in hashes.get("files", {}).items()
            if not (settings.run_root / relative).is_file()
            or sha256_file(settings.run_root / relative) != digest
        ]
        if drift:
            missing.append(f"final artifact hashes: {drift[:5]}")
    else:
        missing.append("final artifact hash manifest")
    try:
        prohibit_test_labels(path for path in settings.run_root.rglob("*") if path.is_file())
    except SweepError as error:
        missing.append(str(error))
    payload = {
        "run_id": settings.run_id,
        "parent_run": settings.parent_run,
        "complete": not missing,
        "missing": missing,
        "verified_at": utc_now(),
        "test_labels_used": False,
    }
    if distilled_path.exists():
        distilled = json.loads(distilled_path.read_text(encoding="utf-8"))
        payload["selected_mean_rmsle"] = distilled.get("selected_mean_rmsle")
        payload["selected_union_count"] = distilled.get("union_count")
    atomic_json(settings.run_root / "verification.json", payload)
    return payload


def _settings_from_args(args: argparse.Namespace) -> Settings:
    return Settings(
        run_id=args.run_id,
        parent_run=args.parent_run,
        inbox=args.inbox.resolve(),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "run", "resume", "status", "verify"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("run_id")
        command_parser.add_argument("--parent-run", default=DEFAULT_PARENT_RUN)
        if command == "prepare":
            command_parser.add_argument("--gpu-smoke", action="store_true")
            command_parser.add_argument("--skip-r3-check", action="store_true")
        if command == "verify":
            command_parser.add_argument("--scq-terminal-receipt", type=Path)
    args = parser.parse_args(argv)
    settings = _settings_from_args(args)
    if args.command == "prepare":
        payload = prepare(
            settings,
            gpu_smoke=args.gpu_smoke,
            r3_archive=None if args.skip_r3_check else DEFAULT_R3_ARCHIVE,
        )
    elif args.command in {"run", "resume"}:
        payload = run(settings)
    elif args.command == "status":
        payload = status(settings)
    else:
        if args.scq_terminal_receipt:
            record_scq_terminal(
                settings,
                json.loads(args.scq_terminal_receipt.read_text(encoding="utf-8")),
            )
        payload = verify(settings)
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    return 0 if args.command != "verify" or payload["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
