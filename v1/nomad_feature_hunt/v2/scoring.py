from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.feature_selection import mutual_info_regression

from nomad_feature_hunt.ledger import atomic_json, sha256_file

from .constants import (
    ATLAS_TARGET_WINNERS,
    CONFIRM_TREES,
    CONFIRMATION_FOLDS,
    DISCOVERY_FOLDS,
    EXISTING_809_CONTROLS,
    MAX_CONFIRMATION_VIEWS_PER_TARGET,
    SCREEN_SEEDS,
    SCREEN_TREES,
    TARGETS,
    TIE_BAND,
)
from .gpu import DualGPUExecutor, GPUFitJob


@dataclass(frozen=True)
class FamilyCandidate:
    family_slug: str
    domain: str
    train: pd.DataFrame
    compute_seconds: float
    target_affinity: str | list[str] = "both"

    @property
    def feature_columns(self) -> tuple[str, ...]:
        return tuple(column for column in self.train.columns if column != "id")


def _maximum_absolute_correlation(matrix: np.ndarray) -> float:
    if matrix.shape[1] < 2:
        return 0.0
    correlation = np.corrcoef(matrix, rowvar=False)
    correlation = np.nan_to_num(correlation, nan=0.0)
    np.fill_diagonal(correlation, 0.0)
    return float(np.max(np.abs(correlation)))


def _maximum_reference_correlation(
    matrix: np.ndarray, reference: np.ndarray, *, sample_rows: int = 256
) -> float:
    if not matrix.size or not reference.size:
        return 0.0
    if matrix.shape[0] != reference.shape[0]:
        raise ValueError("redundancy reference has different rows")
    positions = np.linspace(
        0, matrix.shape[0] - 1, min(sample_rows, matrix.shape[0]), dtype=int
    )
    left = np.asarray(matrix[positions], dtype=np.float64)
    right = np.asarray(reference[positions], dtype=np.float64)
    left -= left.mean(axis=0)
    right -= right.mean(axis=0)
    left_scale = np.linalg.norm(left, axis=0)
    right_scale = np.linalg.norm(right, axis=0)
    left = left[:, left_scale > 0] / left_scale[left_scale > 0]
    right = right[:, right_scale > 0] / right_scale[right_scale > 0]
    if not left.size or not right.size:
        return 0.0
    return float(np.max(np.abs(left.T @ right)))


def rank_family(
    matrix: np.ndarray,
    target: np.ndarray,
    oof_residual: np.ndarray,
    *,
    compute_seconds: float,
    redundancy_reference: np.ndarray | None = None,
    random_state: int = 4219,
) -> dict[str, float]:
    """Controller-private pre-ranking metrics; never serialize these into agent prompts."""

    features = np.asarray(matrix, dtype=float)
    if features.ndim != 2 or features.shape[0] != len(target):
        raise ValueError("family matrix and target shapes differ")
    spearman_values = []
    residual_values = []
    for index in range(features.shape[1]):
        spearman_values.append(abs(float(spearmanr(features[:, index], target).statistic)))
        residual_values.append(abs(float(spearmanr(features[:, index], oof_residual).statistic)))
    mutual_information = mutual_info_regression(
        features, np.asarray(target, dtype=float), random_state=random_state
    )
    return {
        "compute_seconds": float(compute_seconds),
        "max_redundancy": max(
            _maximum_absolute_correlation(features),
            _maximum_reference_correlation(features, redundancy_reference)
            if redundancy_reference is not None
            else 0.0,
        ),
        "max_oof_residual_correlation": float(np.nanmax(residual_values, initial=0.0)),
        "max_spearman": float(np.nanmax(spearman_values, initial=0.0)),
        "max_mutual_information": float(np.nanmax(mutual_information, initial=0.0)),
    }


def _bucket(value: float, boundaries: tuple[float, float], labels: tuple[str, str, str]) -> str:
    if value < boundaries[0]:
        return labels[0]
    if value < boundaries[1]:
        return labels[1]
    return labels[2]


def categorical_discovery_feedback(
    *,
    lift: float,
    redundancy: float,
    compute_seconds: float,
    residual_correlation: float,
) -> dict[str, str]:
    """Return categorical-only feedback suitable for adaptive agents."""

    if lift > 0.0001:
        lift_category = "positive"
    elif lift >= -0.0001:
        lift_category = "neutral"
    else:
        lift_category = "negative"
    return {
        "discovery_lift": lift_category,
        "redundancy": _bucket(redundancy, (0.6, 0.9), ("low", "medium", "high")),
        "compute_cost": _bucket(
            compute_seconds, (10.0, 120.0), ("low", "medium", "high")
        ),
        "residual_alignment": _bucket(
            abs(residual_correlation), (0.05, 0.2), ("low", "medium", "high")
        ),
    }


def choose_with_tie_band(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    candidates = list(rows)
    if not candidates:
        raise ValueError("at least one confirmation view is required")
    best_score = min(float(row["rmsle"]) for row in candidates)
    tied = [row for row in candidates if float(row["rmsle"]) <= best_score + TIE_BAND]
    return min(tied, key=lambda row: (int(row["feature_count"]), str(row.get("view_id", ""))))


def validate_confirmation_views(target: str, views: list[dict[str, Any]]) -> None:
    if target not in TARGETS:
        raise ValueError(f"unsupported target: {target}")
    if not 1 <= len(views) <= MAX_CONFIRMATION_VIEWS_PER_TARGET:
        raise ValueError("confirmation must pre-register one to eight views per target")
    view_ids = [str(view.get("view_id")) for view in views]
    if len(view_ids) != len(set(view_ids)):
        raise ValueError("confirmation view IDs must be unique")
    family_views = [view for view in views if view.get("kind") == "family"]
    if len(family_views) > 5:
        raise ValueError("at most five nonoverlapping family views may be registered")
    used: set[str] = set()
    for view in family_views:
        families = set(map(str, view.get("families", [])))
        overlap = used & families
        if overlap:
            raise ValueError(f"family confirmation views overlap: {sorted(overlap)}")
        used.update(families)
    allowed_kinds = {
        "family",
        "diversity_greedy_union",
        "positive_lift_union",
        "compact_challenger",
    }
    if any(view.get("kind") not in allowed_kinds for view in views):
        raise ValueError("confirmation view has an unsupported kind")


@dataclass
class ConfirmationGate:
    adaptive_frozen: bool = False
    confirmation_unsealed: bool = False

    def freeze_adaptive_generation(self) -> None:
        self.adaptive_frozen = True

    def unseal(self) -> None:
        if not self.adaptive_frozen:
            raise RuntimeError("confirmation folds remain sealed until adaptive generation stops")
        if self.confirmation_unsealed:
            raise RuntimeError("confirmation folds may be unsealed only once")
        self.confirmation_unsealed = True


def confirmation_lifts(target: str, rmsle: float) -> dict[str, float | bool]:
    atlas_lift = ATLAS_TARGET_WINNERS[target] - float(rmsle)
    control_lift = EXISTING_809_CONTROLS[target] - float(rmsle)
    return {
        "atlas_lift": atlas_lift,
        "existing_809_lift": control_lift,
        "beats_both_controls": atlas_lift > 0 and control_lift > 0,
    }


def public_adaptive_packet(
    family_feedback: Mapping[str, Mapping[str, str]]
) -> dict[str, Any]:
    allowed_values = {
        "positive", "neutral", "negative", "low", "medium", "high"
    }
    packet = {
        family: dict(categories) for family, categories in sorted(family_feedback.items())
    }
    for categories in packet.values():
        if any(value not in allowed_values for value in categories.values()):
            raise ValueError("adaptive packet contains noncategorical feedback")
    return {"family_feedback": packet, "contains_rows": False, "contains_exact_scores": False}


def rmsle(target: np.ndarray, prediction: np.ndarray) -> float:
    clipped = np.clip(np.asarray(prediction, dtype=np.float64), 0.0, None)
    return float(np.sqrt(np.mean((np.log1p(target) - np.log1p(clipped)) ** 2)))


def _load_atlas(atlas_bundle: Path) -> tuple[np.ndarray, np.ndarray, list[str], dict[str, list[str]]]:
    required = (
        "train.npy",
        "targets.npy",
        "targets.json",
        "columns.json",
        "selected_columns.json",
    )
    missing = [name for name in required if not (atlas_bundle / name).exists()]
    if missing:
        raise ValueError(f"staged Atlas scoring inputs are missing: {missing}")
    train = np.load(atlas_bundle / "train.npy", mmap_mode="r", allow_pickle=False)
    targets = np.load(atlas_bundle / "targets.npy", mmap_mode="r", allow_pickle=False)
    target_names = json.loads((atlas_bundle / "targets.json").read_text(encoding="utf-8"))
    columns = json.loads((atlas_bundle / "columns.json").read_text(encoding="utf-8"))
    selected = json.loads(
        (atlas_bundle / "selected_columns.json").read_text(encoding="utf-8")
    )
    if list(target_names) != list(TARGETS):
        raise ValueError("staged Atlas targets are not the fixed campaign targets")
    if set(selected) != set(TARGETS):
        raise ValueError("selected Atlas controls do not cover both targets")
    return train, targets, columns, selected


def _cross_validate(
    gpu: DualGPUExecutor,
    matrix: np.ndarray,
    target: np.ndarray,
    folds: np.ndarray,
    *,
    fold_count: int,
    seeds: tuple[int, ...],
    trees: int,
) -> tuple[list[float], np.ndarray, list[np.ndarray]]:
    if set(np.unique(folds).tolist()) != set(range(fold_count)):
        raise ValueError("fold assignments do not match the sealed protocol")
    jobs: list[tuple[int, GPUFitJob]] = []
    for seed in seeds:
        for fold in range(fold_count):
            validation = folds == fold
            jobs.append(
                (
                    fold,
                    GPUFitJob(
                        train=matrix,
                        target=target,
                        training_mask=~validation,
                        validation_mask=validation,
                        iterations=trees,
                        seed=seed,
                    ),
                )
            )
    predictions = np.zeros(len(target), dtype=np.float64)
    prediction_counts = np.zeros(len(target), dtype=np.int16)
    scores: list[float] = []
    importances: list[np.ndarray] = []
    index = 0
    while index < len(jobs):
        chunk = jobs[index : index + 2]
        if len(chunk) == 2:
            results = gpu.fit_pair(chunk[0][1], chunk[1][1])
        else:
            results = (gpu.fit(chunk[0][1], DualGPUExecutor.HOSTS[index % 2]),)
        for (fold, _job), (prediction, importance) in zip(chunk, results, strict=True):
            validation = folds == fold
            if prediction.shape != (int(validation.sum()),):
                raise ValueError("GPU worker returned a misaligned validation prediction")
            predictions[validation] += prediction
            prediction_counts[validation] += 1
            scores.append(rmsle(target[validation], prediction))
            importances.append(importance)
        index += len(chunk)
    if np.any(prediction_counts != len(seeds)):
        raise ValueError("cross-validation predictions do not cover every row and seed")
    return scores, predictions / prediction_counts, importances


def _affinity_matches(candidate: FamilyCandidate, target: str) -> bool:
    affinity = candidate.target_affinity
    if isinstance(affinity, list):
        return target in affinity
    return affinity in {"both", "none", target}


def _shortlist(
    candidates: list[tuple[FamilyCandidate, dict[str, float]]], *, limit: int = 40
) -> list[tuple[FamilyCandidate, dict[str, float]]]:
    def key(item: tuple[FamilyCandidate, dict[str, float]]) -> tuple[Any, ...]:
        candidate, metrics = item
        return (
            -metrics["max_oof_residual_correlation"],
            -metrics["max_mutual_information"],
            -metrics["max_spearman"],
            metrics["max_redundancy"],
            metrics["compute_seconds"],
            candidate.family_slug,
        )

    ranked = sorted(candidates, key=key)
    chosen: list[tuple[FamilyCandidate, dict[str, float]]] = []
    chosen_names: set[str] = set()
    domains = sorted({candidate.domain for candidate, _metrics in ranked})
    per_domain = max(1, limit // max(1, len(domains)))
    for domain in domains:
        for item in [item for item in ranked if item[0].domain == domain][:per_domain]:
            chosen.append(item)
            chosen_names.add(item[0].family_slug)
    for item in ranked:
        if len(chosen) >= limit:
            break
        if item[0].family_slug not in chosen_names:
            chosen.append(item)
            chosen_names.add(item[0].family_slug)
    return chosen[:limit]


def score_discovery(
    *,
    atlas_bundle: Path,
    families: Mapping[str, FamilyCandidate],
    output_dir: Path,
) -> dict[str, Any]:
    """Run ranking and the sealed two-fold, three-seed CatBoost family screen."""

    if not families:
        raise ValueError("discovery requires validated family matrices")
    output_dir.mkdir(parents=True, exist_ok=True)
    atlas_train, targets, columns, selected = _load_atlas(atlas_bundle)
    selection_folds = np.load(
        atlas_bundle / "selection_folds.npy", allow_pickle=False
    )
    column_index = {name: index for index, name in enumerate(columns)}
    gpu = DualGPUExecutor(
        output_dir / "gpu_dispatch",
        worker_source=atlas_bundle.parent / "controller/gpu_fit_worker.py",
        run_root=atlas_bundle.parents[1],
    )
    rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []

    for target_index, target_name in enumerate(TARGETS):
        target = np.asarray(targets[:, target_index], dtype=np.float64)
        try:
            base_indices = [column_index[name] for name in selected[target_name]]
        except KeyError as error:
            raise ValueError(f"Atlas selected control is not in the staged registry: {error}") from error
        base = np.asarray(atlas_train[:, base_indices], dtype=np.float32)
        baseline_scores, baseline_oof, _ = _cross_validate(
            gpu,
            base,
            target,
            selection_folds,
            fold_count=DISCOVERY_FOLDS,
            seeds=SCREEN_SEEDS,
            trees=SCREEN_TREES,
        )
        baseline_rmsle = float(np.mean(baseline_scores))
        residual = target - baseline_oof
        ranked: list[tuple[FamilyCandidate, dict[str, float]]] = []
        reference_columns = np.linspace(
            0, base.shape[1] - 1, min(384, base.shape[1]), dtype=int
        )
        redundancy_reference = base[:, reference_columns]
        for candidate in sorted(families.values(), key=lambda item: (item.domain, item.family_slug)):
            if not _affinity_matches(candidate, target_name) or not candidate.feature_columns:
                continue
            values = candidate.train[list(candidate.feature_columns)].to_numpy(
                dtype=np.float32
            )
            metrics = rank_family(
                values,
                target,
                residual,
                compute_seconds=candidate.compute_seconds,
                redundancy_reference=redundancy_reference,
            )
            ranked.append((candidate, metrics))
            ranking_rows.append(
                {
                    "target": target_name,
                    "family_slug": candidate.family_slug,
                    "domain": candidate.domain,
                    "feature_count": len(candidate.feature_columns),
                    **metrics,
                }
            )
            redundancy_reference = np.column_stack((redundancy_reference, values))
            if redundancy_reference.shape[1] > 512:
                keep = np.linspace(
                    0, redundancy_reference.shape[1] - 1, 512, dtype=int
                )
                redundancy_reference = redundancy_reference[:, keep]
        for candidate, metrics in _shortlist(ranked):
            started = time.perf_counter()
            candidate_values = candidate.train[list(candidate.feature_columns)].to_numpy(
                dtype=np.float32
            )
            combined = np.column_stack((base, candidate_values))
            scores, _oof, importances = _cross_validate(
                gpu,
                combined,
                target,
                selection_folds,
                fold_count=DISCOVERY_FOLDS,
                seeds=SCREEN_SEEDS,
                trees=SCREEN_TREES,
            )
            score = float(np.mean(scores))
            importance_shares: list[float] = []
            for importance in importances:
                total = float(np.sum(importance))
                importance_shares.append(
                    float(np.sum(importance[-len(candidate.feature_columns) :]) / total)
                    if total > 0
                    else 0.0
                )
            rows.append(
                {
                    "score_id": (
                        f"discovery:{target_name}:{candidate.domain}:{candidate.family_slug}"
                    ),
                    "target": target_name,
                    "family_slug": candidate.family_slug,
                    "family_key": f"{candidate.domain}:{candidate.family_slug}",
                    "domain": candidate.domain,
                    "feature_count": len(candidate.feature_columns),
                    "rmsle": score,
                    "baseline_rmsle": baseline_rmsle,
                    "lift": baseline_rmsle - score,
                    "fold_rmsle": scores,
                    "normalized_importance": float(np.mean(importance_shares)),
                    "redundancy": metrics["max_redundancy"],
                    "compute_seconds": candidate.compute_seconds
                    + (time.perf_counter() - started),
                    "residual_correlation": metrics[
                        "max_oof_residual_correlation"
                    ],
                    "rank_metrics": metrics,
                    "nonoverlap_group": f"{candidate.domain}:{candidate.family_slug}",
                }
            )
            atomic_json(
                output_dir / "controller_results.partial.json",
                {"families": rows, "complete": False},
            )

    chain_valid, chain_error = gpu.events.verify()
    payload = {
        "protocol": {
            "folds": DISCOVERY_FOLDS,
            "trees": SCREEN_TREES,
            "seeds": list(SCREEN_SEEDS),
            "gpu_processes": 2,
            "one_process_per_gpu": True,
            "cpu_fallback": False,
            "confirmation_folds_accessed": False,
            "test_labels_used": False,
            "worker_sha256": gpu.worker_sha256,
            "dispatcher_sha256": gpu.dispatcher_sha256,
            "dispatch_events_sha256": sha256_file(gpu.events.path),
            "dispatch_hash_chain_valid": chain_valid,
            "dispatch_hash_chain_error": chain_error,
        },
        "ranking": ranking_rows,
        "families": rows,
    }
    atomic_json(output_dir / "controller_results.json", payload)
    return payload


def build_confirmation_preregistration(
    discovery_rows: Iterable[Mapping[str, Any]],
    available_families: Mapping[str, FamilyCandidate],
) -> dict[str, list[dict[str, Any]]]:
    """Freeze at most eight physically diverse, controller-owned views per target."""

    result: dict[str, list[dict[str, Any]]] = {}
    for target in TARGETS:
        rows = [
            dict(row)
            for row in discovery_rows
            if row.get("target") == target
            and str(row.get("family_key") or row.get("family_slug")) in available_families
        ]
        rows.sort(
            key=lambda row: (
                -float(row.get("lift", 0.0)),
                int(row.get("feature_count", 0)),
                str(row.get("family_key") or row.get("family_slug")),
            )
        )
        positive = [row for row in rows if float(row.get("lift", 0.0)) > 0]
        ranked = positive or rows
        selected: list[dict[str, Any]] = []
        used_domains: set[str] = set()
        used_families: set[str] = set()
        for prefer_new_domain in (True, False):
            for row in ranked:
                family = str(row.get("family_key") or row["family_slug"])
                domain = str(row["domain"])
                if family in used_families or (
                    prefer_new_domain and domain in used_domains
                ):
                    continue
                selected.append(row)
                used_families.add(family)
                used_domains.add(domain)
                if len(selected) == 5:
                    break
            if len(selected) == 5:
                break
        views: list[dict[str, Any]] = [
            {
                "view_id": (
                    f"family-{index:02d}-"
                    f"{str(row.get('family_key') or row['family_slug']).replace(':', '-')}"
                ),
                "kind": "family",
                "families": [str(row.get("family_key") or row["family_slug"])],
            }
            for index, row in enumerate(selected, start=1)
        ]
        diverse_union = [
            str(row.get("family_key") or row["family_slug"]) for row in selected
        ]
        positive_union = [
            str(row.get("family_key") or row["family_slug"]) for row in positive[:20]
        ]
        compact = sorted(
            positive[:10] or rows[:10],
            key=lambda row: (
                int(row.get("feature_count", 0)),
                -float(row.get("lift", 0.0)),
            ),
        )[:3]
        union_specs = (
            ("diversity-greedy-union", "diversity_greedy_union", diverse_union),
            ("positive-lift-union", "positive_lift_union", positive_union),
            (
                "compact-challenger",
                "compact_challenger",
                [str(row.get("family_key") or row["family_slug"]) for row in compact],
            ),
        )
        for view_id, kind, family_names in union_specs:
            unique = list(dict.fromkeys(family_names))
            if unique:
                views.append({"view_id": view_id, "kind": kind, "families": unique})
        validate_confirmation_views(target, views)
        result[target] = views
    return result


def score_confirmation(
    *,
    atlas_bundle: Path,
    families: Mapping[str, FamilyCandidate],
    preregistration: Mapping[str, list[dict[str, Any]]],
    output_dir: Path,
) -> dict[str, Any]:
    """Open the frozen five folds once and score only preregistered views."""

    for target in TARGETS:
        validate_confirmation_views(target, preregistration.get(target, []))
    output_dir.mkdir(parents=True, exist_ok=True)
    marker = output_dir / "confirmation-opened.json"
    if marker.exists():
        raise ValueError("confirmation folds have already been opened for this run")
    atomic_json(marker, {"opened": True, "confirmation_runs": 1})
    atlas_train, targets, columns, selected = _load_atlas(atlas_bundle)
    confirmation_folds = np.load(
        atlas_bundle / "confirmation_folds.npy", allow_pickle=False
    )
    unique_folds, fold_counts = np.unique(confirmation_folds, return_counts=True)
    if (
        unique_folds.tolist() != list(range(CONFIRMATION_FOLDS))
        or len(set(fold_counts.tolist())) != 1
        or np.array_equal(
            confirmation_folds,
            np.arange(len(confirmation_folds)) % CONFIRMATION_FOLDS,
        )
        or np.array_equal(
            confirmation_folds,
            np.repeat(
                np.arange(CONFIRMATION_FOLDS),
                len(confirmation_folds) // CONFIRMATION_FOLDS,
            ),
        )
    ):
        raise ValueError("confirmation fold artifact is not the balanced shuffled five-fold seal")
    column_index = {name: index for index, name in enumerate(columns)}
    gpu = DualGPUExecutor(
        output_dir / "gpu_dispatch",
        worker_source=atlas_bundle.parent / "controller/gpu_fit_worker.py",
        run_root=atlas_bundle.parents[1],
    )
    rows: list[dict[str, Any]] = []
    for target_index, target_name in enumerate(TARGETS):
        target = np.asarray(targets[:, target_index], dtype=np.float64)
        base_indices = [column_index[name] for name in selected[target_name]]
        base = np.asarray(atlas_train[:, base_indices], dtype=np.float32)
        for view in preregistration[target_name]:
            family_names = list(map(str, view["families"]))
            unknown = sorted(set(family_names) - set(families))
            if unknown:
                raise ValueError(f"confirmation view references unknown families: {unknown}")
            frames = [
                families[family].train[list(families[family].feature_columns)]
                for family in family_names
            ]
            candidate = pd.concat(frames, axis=1)
            if candidate.columns.duplicated().any():
                raise ValueError(f"confirmation view {view['view_id']} has duplicate columns")
            matrix = np.column_stack((base, candidate.to_numpy(dtype=np.float32)))
            scores, _oof, _importance = _cross_validate(
                gpu,
                matrix,
                target,
                confirmation_folds,
                fold_count=CONFIRMATION_FOLDS,
                seeds=(4219,),
                trees=CONFIRM_TREES,
            )
            score = float(np.mean(scores))
            lifts = confirmation_lifts(target_name, score)
            rows.append(
                {
                    "score_id": f"confirmation:{target_name}:{view['view_id']}",
                    "target": target_name,
                    "view_id": view["view_id"],
                    "kind": view["kind"],
                    "families": family_names,
                    "feature_count": candidate.shape[1],
                    "rmsle": score,
                    "fold_rmsle": scores,
                    **lifts,
                }
            )
            atomic_json(
                output_dir / "controller_results.partial.json",
                {"views": rows, "complete": False},
            )
    winners = {
        target: choose_with_tie_band(
            row for row in rows if row["target"] == target
        )
        for target in TARGETS
    }
    chain_valid, chain_error = gpu.events.verify()
    payload = {
        "protocol": {
            "folds": CONFIRMATION_FOLDS,
            "trees": CONFIRM_TREES,
            "shuffled": True,
            "gpu_processes": 2,
            "one_process_per_gpu": True,
            "confirmation_runs": 1,
            "test_labels_used": False,
            "cpu_fallback": False,
            "worker_sha256": gpu.worker_sha256,
            "dispatcher_sha256": gpu.dispatcher_sha256,
            "dispatch_events_sha256": sha256_file(gpu.events.path),
            "dispatch_hash_chain_valid": chain_valid,
            "dispatch_hash_chain_error": chain_error,
        },
        "views": rows,
        "winners": winners,
        "beats_atlas_winner_each_target": all(
            bool(winners[target]["atlas_lift"] > 0) for target in TARGETS
        ),
        "beats_existing_809_each_target": all(
            bool(winners[target]["existing_809_lift"] > 0) for target in TARGETS
        ),
    }
    atomic_json(output_dir / "controller_results.json", payload)
    return payload
