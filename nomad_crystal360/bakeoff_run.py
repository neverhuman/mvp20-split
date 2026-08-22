"""Dual-host orchestration for the Atlas/Hyperion CatBoost bake-off."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import base64
import json
from pathlib import Path
import subprocess
import threading
import time
from typing import Any, Sequence

import numpy as np
import pandas as pd

from .bakeoff import (
    AppendOnlyEvents,
    CONFIRMATION_FOLDS,
    CONFIRM_ITERATIONS,
    EXISTING_WIDTH,
    FOLD_SEED,
    IMPORTANCE_PERCENTILES,
    ResultCache,
    SCREEN_ITERATIONS,
    SELECTION_FOLDS,
    TARGET_HOSTS,
    TARGETS,
    canonical_hash,
    family_representation,
    freeze_manifest,
    importance_tables,
    make_importance_jobs,
    model_cache_key,
    percentile_feature_sets,
    percentile_thresholds,
    selected_source_counts,
    select_confirmed_view,
    sha256_file,
    verify_public_bundle,
)


@dataclass(frozen=True)
class Host:
    name: str
    python: str
    bundle: Path
    worker: Path

    @property
    def remote(self) -> bool:
        return self.name != "local"


def _command(host: Host, arguments: Sequence[str]) -> list[str]:
    worker_command = [host.python, str(host.worker), *arguments]
    if not host.remote:
        return worker_command
    return ["ssh", "-o", "BatchMode=yes", host.name, *worker_command]


def _json_command(host: Host, arguments: Sequence[str], *, timeout: float | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        _command(host, arguments),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Worker failed on {host.name} with exit {completed.returncode}: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"Worker on {host.name} returned no JSON")
    return json.loads(lines[-1])


def stage_remote_bundle(
    *, bundle: Path, worker: Path, remote_host: str, remote_bundle: Path
) -> None:
    verify_public_bundle(bundle)
    subprocess.run(
        ["ssh", "-o", "BatchMode=yes", remote_host, "mkdir", "-p", str(remote_bundle)],
        check=True,
    )
    subprocess.run(
        ["rsync", "-a", "--checksum", f"{bundle}/", f"{remote_host}:{remote_bundle}/"],
        check=True,
    )
    subprocess.run(
        ["rsync", "-a", "--checksum", str(worker), f"{remote_host}:{remote_bundle}/worker.py"],
        check=True,
    )
    remote = Host(remote_host, "python3", remote_bundle, remote_bundle / "worker.py")
    _json_command(remote, ["--bundle", str(remote_bundle), "--verify-only"], timeout=300)


class ProgressDisplay:
    """Rich overall progress with a plain fallback and JSONL mirroring."""

    def __init__(self, events: AppendOnlyEvents, total: int):
        self.events = events
        self.total = total
        self.completed = 0
        self.started = time.monotonic()
        self.durations: list[float] = []
        self.best: dict[str, tuple[float, Any]] = {}
        self.gpus: dict[str, dict[str, Any]] = {}
        self.stage = "starting"
        self.stage_total = 0
        self.stage_completed = 0
        self.lock = threading.Lock()
        self.progress: Any | None = None
        self.task: Any | None = None
        try:
            from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn

            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
                TimeRemainingColumn(),
            )
        except ImportError:
            self.progress = None

    def __enter__(self) -> "ProgressDisplay":
        if self.progress is not None:
            self.progress.start()
            self.task = self.progress.add_task("starting", total=self.total)
        return self

    def __exit__(self, *_args: Any) -> None:
        if self.progress is not None:
            self.progress.stop()

    def add_total(self, count: int) -> None:
        with self.lock:
            self.total += count
            if self.progress is not None:
                self.progress.update(self.task, total=self.total)

    def begin_stage(self, stage: str, total: int) -> None:
        with self.lock:
            self.stage = stage
            self.stage_total = total
            self.stage_completed = 0
        self.events.append({"event": "stage_started", "stage": stage, "jobs": total})

    def gpu(self, host: str, status: dict[str, Any]) -> None:
        with self.lock:
            self.gpus[host] = status
        self.events.append({"event": "gpu_status", "host": host, "gpu": status})

    def job(
        self,
        *,
        stage: str,
        host: str,
        job: dict[str, Any],
        result: dict[str, Any],
        cache_hit: bool,
    ) -> None:
        duration = float(result.get("elapsed_seconds", 0.0))
        with self.lock:
            self.completed += 1
            self.stage_completed += 1
            if duration > 0.0:
                self.durations.append(duration)
                self.durations = self.durations[-30:]
            if "score" in result:
                candidate = (float(result["score"]), job.get("cut", job.get("view")))
                current = self.best.get(job["target"])
                if current is None or candidate[0] < current[0]:
                    self.best[job["target"]] = candidate
            rolling = float(np.mean(self.durations)) if self.durations else 0.0
            stage_fields = " ".join(
                f"{name}={job[name]}"
                for name in ("target", "sweep", "fold", "chunk", "cut")
                if name in job and job[name] is not None
            )
            gpu_fields = " ".join(
                f"{name}:{gpu.get('utilization_percent', '?')}%/"
                f"{gpu.get('used_mib', '?')}MiB"
                for name, gpu in sorted(self.gpus.items())
            )
            best_fields = " ".join(
                f"{target}={score:.6f}@{cut}" for target, (score, cut) in self.best.items()
            )
            remaining = max(0, self.total - self.completed)
            stage_remaining = max(0, self.stage_total - self.stage_completed)
            description = (
                f"{stage} {stage_fields} host={host} {gpu_fields} "
                f"rolling={rolling:.1f}s/job stage_eta={rolling * stage_remaining / 2:.0f}s "
                f"overall_eta={rolling * remaining / 2:.0f}s "
                f"best[{best_fields}]"
            )
            if self.progress is not None:
                self.progress.update(self.task, completed=self.completed, description=description)
            elif self.completed == 1 or self.completed % 10 == 0 or self.completed == self.total:
                print(f"[{self.completed}/{self.total}] {description}", flush=True)
        self.events.append(
            {
                "event": "cache_hit" if cache_hit else "job_completed",
                "stage": stage,
                "host": host,
                "job_id": job["job_id"],
                "job": job,
                "result": result,
                "completed": self.completed,
                "total": self.total,
            }
        )


class DualGpuScheduler:
    def __init__(
        self,
        *,
        hosts: dict[str, Host],
        environments: dict[str, dict[str, Any]],
        bundle_hash: str,
        runner_hash: str,
        cache: ResultCache,
        events: AppendOnlyEvents,
        progress: ProgressDisplay,
    ):
        self.hosts = hosts
        self.environments = environments
        self.bundle_hash = bundle_hash
        self.runner_hash = runner_hash
        self.cache = cache
        self.events = events
        self.progress = progress
        self.executors = {
            name: ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"gpu-{name}")
            for name in hosts
        }
        self.monitor_stop = threading.Event()
        self.monitor_threads = [
            threading.Thread(
                target=self._monitor_gpu,
                args=(name,),
                name=f"gpu-monitor-{name}",
                daemon=True,
            )
            for name in hosts
        ]
        for thread in self.monitor_threads:
            thread.start()

    def _monitor_gpu(self, host_name: str) -> None:
        while not self.monitor_stop.wait(10.0):
            try:
                identity = _environment(self.hosts[host_name])
                self.progress.gpu(host_name, identity["gpu"])
            except Exception as error:
                self.events.append(
                    {"event": "gpu_monitor_failed", "host": host_name, "error": repr(error)}
                )

    def close(self) -> None:
        self.monitor_stop.set()
        for thread in self.monitor_threads:
            thread.join(timeout=15)
        for executor in self.executors.values():
            executor.shutdown(wait=True)

    def _cache_key(self, host_name: str, job: dict[str, Any]) -> str:
        return model_cache_key(
            bundle_hash=self.bundle_hash,
            runner_hash=self.runner_hash,
            environment_hash=self.environments[host_name]["sha256"],
            job=job,
        )

    def _run_one(self, host_name: str, job: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        host = self.hosts[host_name]
        encoded = base64.b64encode(json.dumps(job, separators=(",", ":")).encode()).decode()
        result = _json_command(
            host,
            ["--bundle", str(host.bundle), "--job-base64", encoded],
            timeout=None,
        )
        if result.get("bundle_sha256") != self.bundle_hash:
            raise ValueError(f"Worker on {host_name} used the wrong public bundle")
        return host_name, result

    def run(self, stage: str, jobs: Sequence[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        self.progress.begin_stage(stage, len(jobs))
        results: dict[str, dict[str, Any]] = {}
        futures: dict[Future[tuple[str, dict[str, Any]]], tuple[dict[str, Any], str, bool]] = {}
        for job in jobs:
            preferred = TARGET_HOSTS[job["target"]]
            alternate = next(name for name in self.hosts if name != preferred)
            cached_host = next(
                (
                    name
                    for name in (preferred, alternate)
                    if self.cache.get(self._cache_key(name, job)) is not None
                ),
                None,
            )
            if cached_host is not None:
                cached = self.cache.get(self._cache_key(cached_host, job))
                assert cached is not None
                results[job["job_id"]] = cached
                self.progress.job(
                    stage=stage,
                    host=cached_host,
                    job=job,
                    result=cached,
                    cache_hit=True,
                )
                continue
            future = self.executors[preferred].submit(self._run_one, preferred, job)
            futures[future] = (job, preferred, False)

        while futures:
            completed_future = next(as_completed(futures))
            job, attempted_host, retried = futures.pop(completed_future)
            try:
                host_name, result = completed_future.result()
            except Exception as error:
                self.events.append(
                    {
                        "event": "job_failed",
                        "stage": stage,
                        "host": attempted_host,
                        "job_id": job["job_id"],
                        "job": job,
                        "error": repr(error),
                        "will_retry": not retried,
                    }
                )
                if retried:
                    raise RuntimeError(
                        f"Job {job['job_id']} failed once on each GPU; CPU fallback is forbidden"
                    ) from error
                alternate = next(name for name in self.hosts if name != attempted_host)
                retry_future = self.executors[alternate].submit(self._run_one, alternate, job)
                futures[retry_future] = (job, alternate, True)
                continue
            self.cache.put(self._cache_key(host_name, job), result)
            results[job["job_id"]] = result
            self.progress.job(
                stage=stage,
                host=host_name,
                job=job,
                result=result,
                cache_hit=False,
            )
        return [(job, results[job["job_id"]]) for job in jobs]


def _new_job(**values: Any) -> dict[str, Any]:
    job = dict(values)
    job["job_id"] = canonical_hash(job)[:24]
    return job


def _score_jobs(
    *,
    rankings: dict[tuple[str, int], pd.DataFrame],
    thresholds_by_target: dict[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for target in TARGETS:
        for fold in range(SELECTION_FOLDS):
            ranked_indices = rankings[(target, fold)]["feature_index"].astype(int).tolist()
            for threshold in thresholds_by_target[target].itertuples(index=False):
                cut = int(threshold.feature_count)
                jobs.append(
                    _new_job(
                        kind="screen",
                        stage="screen",
                        target=target,
                        fold=fold,
                        view=str(threshold.percentile_label),
                        percentile=float(threshold.percentile),
                        cut=cut,
                        control=None,
                        columns=ranked_indices[:cut],
                        iterations=SCREEN_ITERATIONS,
                        seed=FOLD_SEED,
                    )
                )
            jobs.append(
                _new_job(
                    kind="screen",
                    stage="screen",
                    target=target,
                    fold=fold,
                    view="existing_809",
                    percentile=None,
                    cut=EXISTING_WIDTH,
                    control="existing_809",
                    columns=list(range(EXISTING_WIDTH)),
                    iterations=SCREEN_ITERATIONS,
                    seed=FOLD_SEED,
                )
            )
    return jobs


def _score_summary(
    jobs_and_results: Sequence[tuple[dict[str, Any], dict[str, Any]]]
) -> pd.DataFrame:
    rows = [
        {
            "target": job["target"],
            "fold": job["fold"],
            "view": job["view"],
            "percentile": job.get("percentile"),
            "cut": job.get("cut"),
            "control": job.get("control"),
            "rmsle": result["score"],
            "elapsed_seconds": result["elapsed_seconds"],
            "job_id": job["job_id"],
        }
        for job, result in jobs_and_results
    ]
    return pd.DataFrame(rows)


def _confirmation_jobs(
    rankings: dict[str, pd.DataFrame], candidates_by_target: dict[str, pd.DataFrame]
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for target in TARGETS:
        indices = rankings[target]["feature_index"].astype(int).tolist()
        for fold in range(CONFIRMATION_FOLDS):
            for candidate in candidates_by_target[target].itertuples(index=False):
                cut = int(candidate.cut)
                jobs.append(
                    _new_job(
                        kind="confirm",
                        stage="confirmation",
                        target=target,
                        fold=fold,
                        view=str(candidate.view),
                        percentile=float(candidate.percentile),
                        cut=cut,
                        control=None,
                        columns=indices[:cut],
                        iterations=CONFIRM_ITERATIONS,
                        seed=FOLD_SEED,
                    )
                )
            jobs.append(
                _new_job(
                    kind="confirm",
                    stage="confirmation",
                    target=target,
                    fold=fold,
                    view="existing_809",
                    percentile=None,
                    cut=EXISTING_WIDTH,
                    control="existing_809",
                    columns=list(range(EXISTING_WIDTH)),
                    iterations=CONFIRM_ITERATIONS,
                    seed=FOLD_SEED,
                )
            )
    return jobs


def _final_jobs(
    selected_indices: dict[str, list[int]], selected_views: dict[str, str]
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for target in TARGETS:
        indices = selected_indices[target]
        for fold in range(CONFIRMATION_FOLDS):
            jobs.append(
                _new_job(
                    kind="final",
                    stage="final",
                    target=target,
                    fold=fold,
                    view=selected_views[target],
                    cut=len(indices),
                    control="existing_809" if selected_views[target] == "existing_809" else None,
                    columns=indices,
                    iterations=CONFIRM_ITERATIONS,
                    seed=FOLD_SEED,
                )
            )
    return jobs


def _environment(host: Host) -> dict[str, Any]:
    return _json_command(host, ["--identity"], timeout=60)


def _save_frame(frame: pd.DataFrame, stem: Path) -> list[Path]:
    csv_path = stem.with_suffix(".csv")
    parquet_path = stem.with_suffix(".parquet")
    frame.to_csv(csv_path, index=False)
    frame.to_parquet(parquet_path, index=False)
    return [csv_path, parquet_path]


def run_bakeoff(
    *,
    bundle: Path,
    output_dir: Path,
    worker: Path,
    remote_host: str = "xbabe1",
    remote_bundle: Path = Path("/home/ubuntu/atlas-hyperion-bakeoff/bundle"),
    local_python: str = "/usr/bin/python3",
    remote_python: str = "python3",
    stage_remote: bool = True,
) -> Path:
    manifest = verify_public_bundle(bundle)
    if (output_dir / "freeze_manifest.json").exists():
        raise FileExistsError("Bake-off is already frozen; refusing to alter its selection")
    output_dir.mkdir(parents=True, exist_ok=True)
    if stage_remote:
        stage_remote_bundle(
            bundle=bundle, worker=worker, remote_host=remote_host, remote_bundle=remote_bundle
        )
    hosts = {
        "local": Host("local", local_python, bundle, worker),
        "xbabe1": Host(remote_host, remote_python, remote_bundle, remote_bundle / "worker.py"),
    }
    environments = {name: _environment(host) for name, host in hosts.items()}
    for name, identity in environments.items():
        if identity["packages"].get("catboost") != "1.2.10":
            raise ValueError(f"{name} does not have pinned CatBoost 1.2.10")
    events = AppendOnlyEvents(output_dir / "progress.jsonl")
    cache = ResultCache(output_dir / "cache")
    source_families = pd.read_parquet(bundle / "source_families.parquet")
    columns = json.loads((bundle / "columns.json").read_text(encoding="utf-8"))
    feature_count = len(columns)
    importance_jobs = make_importance_jobs(feature_count)
    percentile_count = len(IMPORTANCE_PERCENTILES)
    screen_count = len(TARGETS) * SELECTION_FOLDS * (percentile_count + 1)
    estimated_total = len(importance_jobs) + screen_count

    artifacts: list[Path] = []
    score_manifest: dict[str, Any] = {}
    selected_indices: dict[str, list[int]] = {}
    selected_views: dict[str, str] = {}
    with ProgressDisplay(events, estimated_total) as progress:
        for name, identity in environments.items():
            progress.gpu(name, identity["gpu"])
        scheduler = DualGpuScheduler(
            hosts=hosts,
            environments=environments,
            bundle_hash=manifest["bundle_sha256"],
            runner_hash=sha256_file(worker),
            cache=cache,
            events=events,
            progress=progress,
        )
        try:
            importance_results = scheduler.run("importance", importance_jobs)
            rankings, fold_rankings, observations = importance_tables(
                importance_results, source_families
            )
            artifacts.extend(_save_frame(observations, output_dir / "importance_observations"))
            for target in TARGETS:
                artifacts.extend(_save_frame(rankings[target], output_dir / f"ranking_{target}"))
                artifacts.extend(
                    _save_frame(rankings[target].head(100), output_dir / f"top100_{target}")
                )
                for fold in range(SELECTION_FOLDS):
                    artifacts.extend(
                        _save_frame(
                            fold_rankings[(target, fold)],
                            output_dir / f"ranking_{target}_selection_fold_{fold}",
                        )
                    )

            thresholds_by_target: dict[str, pd.DataFrame] = {}
            threshold_frames: list[pd.DataFrame] = []
            for target in TARGETS:
                thresholds = percentile_thresholds(rankings[target])
                thresholds_by_target[target] = thresholds
                percentile_feature_sets(rankings[target])
                target_thresholds = thresholds.copy()
                target_thresholds.insert(0, "target", target)
                threshold_frames.append(target_thresholds)
                artifacts.extend(
                    _save_frame(
                        target_thresholds,
                        output_dir / f"percentile_thresholds_{target}",
                    )
                )
                representation = family_representation(
                    rankings[target], thresholds["feature_count"].astype(int).tolist()
                )
                representation = representation.merge(
                    thresholds[["percentile", "percentile_label", "feature_count"]],
                    left_on="cut",
                    right_on="feature_count",
                    how="left",
                    validate="many_to_one",
                ).drop(columns="feature_count")
                representation.insert(0, "target", target)
                artifacts.extend(
                    _save_frame(
                        representation, output_dir / f"source_representation_{target}"
                    )
                )
            artifacts.extend(
                _save_frame(
                    pd.concat(threshold_frames, ignore_index=True),
                    output_dir / "percentile_thresholds",
                )
            )

            screen_jobs = _score_jobs(
                rankings=fold_rankings, thresholds_by_target=thresholds_by_target
            )
            screen_results = scheduler.run("screen_percentiles", screen_jobs)
            screen_frame = _score_summary(screen_results)
            existing_means = (
                screen_frame[screen_frame["control"] == "existing_809"]
                .groupby("target")["rmsle"]
                .mean()
                .to_dict()
            )
            screen_frame["lift_over_existing_809"] = screen_frame.apply(
                lambda row: existing_means[row["target"]] - row["rmsle"], axis=1
            )
            artifacts.extend(_save_frame(screen_frame, output_dir / "screen_scores"))

            screen_curve = (
                screen_frame.groupby(
                    ["target", "view", "percentile", "cut", "control"],
                    dropna=False,
                    as_index=False,
                )
                .agg(
                    mean_rmsle=("rmsle", "mean"),
                    rmsle_std=("rmsle", lambda values: float(np.std(values, ddof=0))),
                    folds=("rmsle", "size"),
                )
            )
            screen_curve["existing_809_rmsle"] = screen_curve["target"].map(existing_means)
            screen_curve["lift_over_existing_809"] = (
                screen_curve["existing_809_rmsle"] - screen_curve["mean_rmsle"]
            )
            screen_curve.insert(0, "stage", "selection_2fold_150_tree")

            confirmation_candidates: dict[str, pd.DataFrame] = {}
            for target in TARGETS:
                candidates = screen_curve[
                    (screen_curve["target"] == target) & screen_curve["control"].isna()
                ].sort_values(
                    ["mean_rmsle", "cut", "view"],
                    ascending=[True, True, True],
                    kind="mergesort",
                )
                confirmation_candidates[target] = candidates.head(3)[
                    ["view", "percentile", "cut"]
                ].reset_index(drop=True)
            confirmation_jobs = _confirmation_jobs(rankings, confirmation_candidates)
            progress.add_total(len(confirmation_jobs))
            confirmation_results = scheduler.run("confirmation", confirmation_jobs)
            confirmation_frame = _score_summary(confirmation_results)
            confirmation_control_means = (
                confirmation_frame[confirmation_frame["control"] == "existing_809"]
                .groupby("target")["rmsle"]
                .mean()
                .to_dict()
            )
            confirmation_frame["lift_over_existing_809"] = confirmation_frame.apply(
                lambda row: confirmation_control_means[row["target"]] - row["rmsle"],
                axis=1,
            )
            artifacts.extend(
                _save_frame(confirmation_frame, output_dir / "confirmation_scores")
            )
            confirmation_curve = (
                confirmation_frame.groupby(
                    ["target", "view", "percentile", "cut", "control"],
                    dropna=False,
                    as_index=False,
                )
                .agg(
                    mean_rmsle=("rmsle", "mean"),
                    rmsle_std=("rmsle", lambda values: float(np.std(values, ddof=0))),
                    folds=("rmsle", "size"),
                )
            )
            confirmation_curve["existing_809_rmsle"] = confirmation_curve["target"].map(
                confirmation_control_means
            )
            confirmation_curve["lift_over_existing_809"] = (
                confirmation_curve["existing_809_rmsle"]
                - confirmation_curve["mean_rmsle"]
            )
            confirmation_curve.insert(0, "stage", "confirmation_5fold_400_tree")
            artifacts.extend(
                _save_frame(
                    pd.concat([screen_curve, confirmation_curve], ignore_index=True),
                    output_dir / "score_curve",
                )
            )

            for target in TARGETS:
                target_curve = confirmation_curve[confirmation_curve["target"] == target]
                scores = dict(
                    zip(target_curve["view"], target_curve["mean_rmsle"], strict=True)
                )
                counts = dict(zip(target_curve["view"], target_curve["cut"], strict=True))
                selected_view = select_confirmed_view(
                    {view: float(score) for view, score in scores.items()},
                    {view: int(count) for view, count in counts.items()},
                )
                selected_views[target] = selected_view
                selected_count = int(counts[selected_view])
                if selected_view == "existing_809":
                    selected_indices[target] = list(range(EXISTING_WIDTH))
                    selected_percentile: float | None = None
                else:
                    feature_sets = percentile_feature_sets(rankings[target])
                    selected_indices[target] = feature_sets[selected_view]
                    selected_percentile = float(
                        target_curve.loc[
                            target_curve["view"] == selected_view, "percentile"
                        ].iloc[0]
                    )
                control_score = float(confirmation_control_means[target])
                selected_score = float(scores[selected_view])
                lift = control_score - selected_score
                reduced = selected_view != "existing_809" and selected_count < feature_count
                score_manifest[target] = {
                    "screen_existing_809_rmsle": float(existing_means[target]),
                    "confirmed_percentile_views": confirmation_candidates[target][
                        "view"
                    ].tolist(),
                    "confirmation_candidates": {
                        str(row.view): {
                            "percentile": None
                            if pd.isna(row.percentile)
                            else float(row.percentile),
                            "feature_count": int(row.cut),
                            "five_fold_rmsle": float(row.mean_rmsle),
                        }
                        for row in target_curve.itertuples(index=False)
                    },
                    "five_fold_existing_809_rmsle": control_score,
                    "selected_view": selected_view,
                    "selected_percentile": selected_percentile,
                    "selected_feature_count": selected_count,
                    "selected_five_fold_rmsle": selected_score,
                    "five_fold_lift_over_existing_809": lift,
                    "positive_five_fold_lift": lift > 0.0,
                    "reduced_set_selected": reduced,
                    "reduced_set_beats_809_control": reduced and lift > 0.0,
                }

            final_jobs = _final_jobs(selected_indices, selected_views)
            progress.add_total(len(final_jobs))
            final_results = scheduler.run("final", final_jobs)
        finally:
            scheduler.close()

    selected_columns: dict[str, list[str]] = {}
    selected_counts: dict[str, dict[str, int]] = {}
    submission = pd.DataFrame({"id": np.load(bundle / "test_ids.npy", allow_pickle=False)})
    train_ids = np.load(bundle / "train_ids.npy", allow_pickle=False)
    test_ids = np.load(bundle / "test_ids.npy", allow_pickle=False)
    for target in TARGETS:
        indices = selected_indices[target]
        selected_columns[target] = [columns[index] for index in indices]
        selected_counts[target] = selected_source_counts(indices, source_families)
        target_results = [
            (job, result) for job, result in final_results if job["target"] == target
        ]
        oof = np.full(len(train_ids), np.nan, dtype=np.float64)
        fold_by_row = np.full(len(train_ids), -1, dtype=int)
        test_folds: list[np.ndarray] = []
        final_scores: list[float] = []
        for job, result in target_results:
            validation_indices = np.asarray(result["validation_indices"], dtype=int)
            oof[validation_indices] = np.asarray(result["validation_predictions"], dtype=float)
            fold_by_row[validation_indices] = int(job["fold"])
            test_folds.append(np.asarray(result["test_predictions"], dtype=float))
            final_scores.append(float(result["score"]))
        if not np.isfinite(oof).all() or np.any(fold_by_row < 0) or len(test_folds) != CONFIRMATION_FOLDS:
            raise AssertionError(f"Final fold predictions are incomplete for {target}")
        test_matrix = np.column_stack(test_folds)
        averaged = np.clip(test_matrix.mean(axis=1), 0.0, None)
        submission[target] = averaged
        score_manifest[target]["final_fold_rmsle"] = final_scores
        score_manifest[target]["final_mean_rmsle"] = float(np.mean(final_scores))
        oof_frame = pd.DataFrame(
            {"id": train_ids, "fold": fold_by_row, "prediction": oof}
        )
        test_frame = pd.DataFrame({"id": test_ids})
        for fold in range(CONFIRMATION_FOLDS):
            test_frame[f"fold_{fold}_prediction"] = test_matrix[:, fold]
        test_frame["prediction"] = averaged
        artifacts.extend(_save_frame(oof_frame, output_dir / f"oof_{target}"))
        artifacts.extend(_save_frame(test_frame, output_dir / f"test_fold_predictions_{target}"))

    submission_path = output_dir / "submission.csv"
    submission.to_csv(submission_path, index=False)
    scores_path = output_dir / "scores.json"
    scores_path.write_text(json.dumps(score_manifest, indent=2, sort_keys=True) + "\n")
    artifacts.append(scores_path)
    columns_path = output_dir / "selected_columns.json"
    columns_path.write_text(json.dumps(selected_columns, indent=2, sort_keys=True) + "\n")
    artifacts.append(columns_path)
    counts_path = output_dir / "selected_source_counts.json"
    counts_path.write_text(json.dumps(selected_counts, indent=2, sort_keys=True) + "\n")
    artifacts.append(counts_path)
    artifacts.append(events.path)

    return freeze_manifest(
        output_dir=output_dir,
        bundle_manifest=manifest,
        environment_identities=environments,
        runner_path=worker,
        selected_columns=selected_columns,
        selected_indices=selected_indices,
        selected_counts=selected_counts,
        scores=score_manifest,
        submission=submission_path,
        artifacts=artifacts,
    )
