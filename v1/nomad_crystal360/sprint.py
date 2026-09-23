"""Deadline-safe dual-host execution primitives for the CrystalAtlas sprint."""
from __future__ import annotations

from dataclasses import dataclass, asdict
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Callable, Iterable


SPRINT_SECONDS = 7_200
MIN_FREE_VRAM_MIB = 20_000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class Deadline:
    started: float
    seconds: float = SPRINT_SECONDS

    @classmethod
    def start(cls, seconds: float = SPRINT_SECONDS) -> "Deadline":
        return cls(time.monotonic(), float(seconds))

    @property
    def elapsed(self) -> float:
        return max(0.0, time.monotonic() - self.started)

    @property
    def remaining(self) -> float:
        return max(0.0, self.seconds - self.elapsed)

    def expired(self, reserve: float = 0.0) -> bool:
        return self.remaining <= reserve

    def require(self, reserve: float = 0.0) -> None:
        if self.expired(reserve):
            raise TimeoutError(f"CrystalAtlas sprint deadline reached ({self.seconds:.0f}s)")


@dataclass(frozen=True)
class Job:
    target: str
    genome: tuple[str, ...]
    fold: int
    seed: int
    fidelity: int
    preferred_host: str
    job_id: str = ""

    def with_id(self) -> "Job":
        return Job(**{**asdict(self), "job_id": canonical_hash(asdict(self))[:24]})


class AppendOnlyQueue:
    """JSONL event log; claim/retry/finalize never overwrite history."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = path.with_suffix(path.suffix + ".lock")

    def _event(self, event: dict[str, Any]) -> None:
        with self.lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            with self.path.open("a", encoding="utf-8") as out:
                out.write(json.dumps({"ts": time.time(), **event}, sort_keys=True) + "\n")
                out.flush(); os.fsync(out.fileno())

    def add(self, jobs: Iterable[Job]) -> None:
        for job in jobs:
            item = job.with_id()
            self._event({"event": "queued", "job": asdict(item)})

    def state(self) -> dict[str, str]:
        current: dict[str, str] = {}
        if not self.path.exists(): return current
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line: continue
            event = json.loads(line); job = event.get("job", {}); jid = job.get("job_id")
            if jid: current[jid] = event["event"]
        return current

    def claim(self, host: str) -> Job | None:
        selected: Job | None = None
        with self.lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            events = [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines()] if self.path.exists() else []
            statuses = {e.get("job", {}).get("job_id"): e["event"] for e in events if e.get("job", {}).get("job_id")}
            for event in events:
                job = event.get("job", {}); jid = job.get("job_id")
                if event.get("event") == "queued" and statuses.get(jid) == "queued" and job.get("preferred_host") in (host, "any"):
                    selected = Job(**job)
                    break
        if selected is not None: self._event({"event": "claimed", "host": host, "job": asdict(selected)})
        return selected

    def finish(self, job: Job, host: str, result: dict[str, Any]) -> None:
        self._event({"event": "finished", "host": host, "job": asdict(job), "result": result})

    def fail(self, job: Job, host: str, error: str, retry: bool = True) -> None:
        self._event({"event": "failed", "host": host, "job": asdict(job), "error": error, "retry": retry})
        if retry:
            retry_job = Job(**{**asdict(job), "preferred_host": "any"})
            self._event({"event": "queued", "job": asdict(retry_job), "retry_of": host})


def gpu_info(host: str = "local", ssh_bin: str = "ssh") -> dict[str, Any]:
    command = ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"]
    if host != "local": command = [ssh_bin, "-o", "BatchMode=yes", host, *command]
    try:
        text = subprocess.check_output(command, text=True, stderr=subprocess.STDOUT, timeout=15).strip().splitlines()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"GPU probe failed for {host}: {exc}") from exc
    if not text: raise RuntimeError(f"No GPU reported by {host}")
    name, total, free = [p.strip() for p in text[0].split(",")[:3]]
    result = {"host": host, "name": name, "total_mib": int(float(total)), "free_mib": int(float(free))}
    if result["free_mib"] < MIN_FREE_VRAM_MIB: raise RuntimeError(f"Insufficient free VRAM on {host}: {result['free_mib']} MiB")
    return result


def cache_key(environment_hash: str, matrix_hash: str, job: Job, params: dict[str, Any]) -> str:
    return canonical_hash({"environment": environment_hash, "matrix": matrix_hash, "job": asdict(job), "params": params})


class ResultCache:
    def __init__(self, directory: Path): self.directory = directory; directory.mkdir(parents=True, exist_ok=True)
    def path(self, key: str) -> Path: return self.directory / f"{key}.json"
    def get(self, key: str) -> dict[str, Any] | None:
        path=self.path(key); return json.loads(path.read_text()) if path.exists() else None
    def put(self, key: str, result: dict[str, Any]) -> Path:
        path=self.path(key); tmp=path.with_suffix(".tmp"); tmp.write_text(json.dumps(result, sort_keys=True)+"\n"); os.replace(tmp,path); return path


def validate_public_bundle(train_matrix: Path, test_matrix: Path, targets: Path, folds: Path, *, test_target_columns: Iterable[str] = ()) -> dict[str, Any]:
    import pandas as pd
    train = pd.read_parquet(train_matrix); test = pd.read_parquet(test_matrix); y = pd.read_parquet(targets); split = pd.read_parquet(folds)
    if list(train.columns) != list(test.columns): raise ValueError("train/test predictor columns differ")
    if len(train) != len(y) or len(train) != len(split): raise ValueError("bundle row counts differ")
    forbidden = set(test_target_columns) & set(test.columns)
    if forbidden: raise ValueError(f"test-target columns present in synchronized bundle: {sorted(forbidden)}")
    return {"train_rows":len(train),"test_rows":len(test),"predictors":len(train.columns),"targets":list(y.columns),"fold_columns":list(split.columns),"train_sha256":sha256_file(train_matrix),"test_sha256":sha256_file(test_matrix),"targets_sha256":sha256_file(targets),"folds_sha256":sha256_file(folds)}


def freeze_run(output_dir: Path, *, selected_columns: dict[str, list[str]], model_files: Iterable[Path], oof_files: Iterable[Path], blend_weights: dict[str, list[float]], ledger: Path, environment: dict[str, Any], submission: Path, deadline: Deadline) -> Path:
    deadline.require(0)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = [ledger, submission, *model_files, *oof_files]
    manifest = {"frozen_at_unix":time.time(),"deadline_elapsed_seconds":deadline.elapsed,"selected_columns":selected_columns,"blend_weights":blend_weights,"environment":environment,"artifacts":{str(p):sha256_file(p) for p in files if p.exists()},"submission_sha256":sha256_file(submission) if submission.exists() else None,"private_grade_used":False}
    path=output_dir/"freeze_manifest.json"; path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n"); return path


def run_worker(queue: AppendOnlyQueue, host: str, deadline: Deadline, runner: Callable[[Job], dict[str, Any]], *, probe_gpu: bool = True) -> int:
    if probe_gpu: gpu_info(host)
    completed=0
    while not deadline.expired(1.0):
        job=queue.claim(host)
        if job is None: break
        try:
            deadline.require(1.0); result=runner(job); queue.finish(job,host,result); completed+=1
        except Exception as exc:
            queue.fail(job,host,repr(exc),retry=not deadline.expired(1.0))
    return completed
