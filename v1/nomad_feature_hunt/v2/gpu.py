from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from nomad_feature_hunt.ledger import HashChain, sha256_file, utc_now


class GPUScoringError(RuntimeError):
    pass


@dataclass(frozen=True)
class GPUFitJob:
    train: np.ndarray
    target: np.ndarray
    training_mask: np.ndarray
    validation_mask: np.ndarray
    iterations: int
    seed: int


class DualGPUExecutor:
    """Receipt-bound CatBoost dispatch with one process on each campaign GPU.

    The feature-foundry controller runs in its managed Python environment, while both GPU
    machines expose the audited CatBoost worker through ``/usr/bin/python3``.  Keeping that
    interpreter choice here avoids mutating the v1 dispatcher contract.
    """

    HOSTS = ("local", "xbabe1")
    GPU_PYTHON = "/usr/bin/python3"

    def __init__(
        self,
        receipt_dir: Path,
        *,
        worker_source: Path | None = None,
        run_root: Path | None = None,
    ) -> None:
        self.receipt_dir = receipt_dir
        self.receipt_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir = self.receipt_dir / "work"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.events = HashChain(self.receipt_dir / "events.jsonl")
        source_worker = worker_source or Path(__file__).parents[1] / "gpu_fit_worker.py"
        self.worker = self.receipt_dir / "gpu_fit_worker.py"
        frozen_dispatcher = self.receipt_dir / "gpu_dispatcher.py"
        if not self.worker.exists():
            shutil.copy2(source_worker, self.worker)
        if not frozen_dispatcher.exists():
            shutil.copy2(Path(__file__), frozen_dispatcher)
        if sha256_file(source_worker) != sha256_file(self.worker):
            raise GPUScoringError("frozen GPU worker differs from the preflighted source")
        if sha256_file(Path(__file__)) != sha256_file(frozen_dispatcher):
            raise GPUScoringError("frozen GPU dispatcher differs from the running source")
        self.worker_sha256 = sha256_file(self.worker)
        self.dispatcher_sha256 = sha256_file(frozen_dispatcher)
        campaign_root = (run_root or receipt_dir.parents[2]).resolve()
        if not re.fullmatch(
            r"/home/ubuntu/nomad/artifacts/nomad_theory_feature_hunt/v2/inbox/"
            r"[A-Za-z0-9][A-Za-z0-9_.-]{2,63}",
            str(campaign_root),
        ):
            raise GPUScoringError("remote GPU staging root is outside the v2 campaign inbox")
        self.remote_tmp_root = campaign_root / "runtime/remote-gpu"
        self._locks = {host: threading.Lock() for host in self.HOSTS}
        self._event_lock = threading.Lock()
        self._counter_lock = threading.Lock()
        self._counter = 0

    def _record(self, event: str, receipt: dict[str, object]) -> None:
        with self._event_lock:
            self.events.append(event, receipt)

    def _next_job_id(self) -> str:
        with self._counter_lock:
            self._counter += 1
            return f"v2-gpu-fit-{self._counter:06d}"

    def _safe_remote_dir(self, value: str) -> bool:
        path = Path(value)
        return path.parent == self.remote_tmp_root and re.fullmatch(
            r"nomad-v2-[a-f0-9]{32}", path.name
        ) is not None

    def _execute(
        self, job_id: str, job: GPUFitJob, host: str, attempt: int
    ) -> tuple[np.ndarray, np.ndarray]:
        with self._locks[host], tempfile.TemporaryDirectory(
            prefix="nomad-v2-gpu-fit-", dir=self.work_dir
        ) as temporary:
            temporary_path = Path(temporary)
            input_path = temporary_path / "input.npz"
            output_path = temporary_path / "output.npz"
            np.savez_compressed(
                input_path,
                train=np.asarray(job.train, dtype=np.float32),
                target=np.asarray(job.target, dtype=np.float64),
                training_mask=np.asarray(job.training_mask, dtype=bool),
                validation_mask=np.asarray(job.validation_mask, dtype=bool),
                iterations=np.asarray(job.iterations),
                seed=np.asarray(job.seed),
            )
            started_at = utc_now()
            remote_dir: str | None = None
            result: subprocess.CompletedProcess[str]
            try:
                if host == "local":
                    result = subprocess.run(
                        [
                            self.GPU_PYTHON,
                            str(self.worker),
                            "--input",
                            str(input_path),
                            "--output",
                            str(output_path),
                        ],
                        text=True,
                        capture_output=True,
                        timeout=7_200,
                        check=False,
                    )
                else:
                    remote_dir = f"{self.remote_tmp_root}/nomad-v2-{uuid.uuid4().hex}"
                    if not self._safe_remote_dir(remote_dir):
                        raise GPUScoringError("refusing unsafe remote staging path")
                    result = subprocess.run(
                        ["ssh", host, "mkdir", "-p", str(self.remote_tmp_root)],
                        text=True,
                        capture_output=True,
                        timeout=60,
                        check=False,
                    )
                    if result.returncode == 0:
                        result = subprocess.run(
                            ["ssh", host, "mkdir", "-m", "700", remote_dir],
                            text=True,
                            capture_output=True,
                            timeout=60,
                            check=False,
                        )
                    if result.returncode == 0:
                        result = subprocess.run(
                            [
                                "scp",
                                str(self.worker),
                                str(input_path),
                                f"{host}:{remote_dir}/",
                            ],
                            text=True,
                            capture_output=True,
                            timeout=1_800,
                            check=False,
                        )
                    if result.returncode == 0:
                        result = subprocess.run(
                            [
                                "ssh",
                                host,
                                self.GPU_PYTHON,
                                f"{remote_dir}/{self.worker.name}",
                                "--input",
                                f"{remote_dir}/input.npz",
                                "--output",
                                f"{remote_dir}/output.npz",
                            ],
                            text=True,
                            capture_output=True,
                            timeout=7_200,
                            check=False,
                        )
                    if result.returncode == 0:
                        result = subprocess.run(
                            ["scp", f"{host}:{remote_dir}/output.npz", str(output_path)],
                            text=True,
                            capture_output=True,
                            timeout=1_800,
                            check=False,
                        )
                receipt: dict[str, object] = {
                    "job_id": job_id,
                    "attempt": attempt,
                    "host": host,
                    "started_at": started_at,
                    "finished_at": utc_now(),
                    "returncode": result.returncode,
                    "input_sha256": sha256_file(input_path),
                    "worker_sha256": self.worker_sha256,
                    "dispatcher_sha256": self.dispatcher_sha256,
                    "cpu_fallback": False,
                }
                if result.returncode != 0 or not output_path.exists():
                    receipt["stderr_tail"] = result.stderr[-2_000:]
                    self._record("gpu_fit_failed", receipt)
                    raise GPUScoringError(
                        f"{job_id} failed on {host}: {result.stderr[-500:]}"
                    )
                with np.load(output_path, allow_pickle=False) as output:
                    prediction = np.asarray(output["prediction"], dtype=np.float64)
                    importance = np.asarray(output["importance"], dtype=np.float64)
                    receipt["environment"] = json.loads(str(output["metadata_json"]))
                receipt["output_sha256"] = sha256_file(output_path)
                self._record("gpu_fit_complete", receipt)
                return prediction, importance
            finally:
                if remote_dir is not None and self._safe_remote_dir(remote_dir):
                    try:
                        subprocess.run(
                            ["ssh", host, "rm", "-rf", "--", remote_dir],
                            text=True,
                            capture_output=True,
                            timeout=60,
                            check=False,
                        )
                    except (OSError, subprocess.SubprocessError):
                        pass

    def fit(
        self, job: GPUFitJob, preferred_host: str
    ) -> tuple[np.ndarray, np.ndarray]:
        if preferred_host not in self.HOSTS:
            raise ValueError(f"unknown GPU host: {preferred_host}")
        job_id = self._next_job_id()
        alternate = next(host for host in self.HOSTS if host != preferred_host)
        errors: list[str] = []
        for attempt, host in enumerate((preferred_host, alternate), start=1):
            try:
                return self._execute(job_id, job, host, attempt)
            except (
                GPUScoringError,
                KeyError,
                OSError,
                ValueError,
                subprocess.SubprocessError,
            ) as error:
                errors.append(str(error))
                if not isinstance(error, GPUScoringError):
                    self._record(
                        "gpu_fit_failed",
                        {
                            "job_id": job_id,
                            "attempt": attempt,
                            "host": host,
                            "error": str(error),
                            "worker_sha256": self.worker_sha256,
                            "dispatcher_sha256": self.dispatcher_sha256,
                            "cpu_fallback": False,
                        },
                    )
        raise GPUScoringError(
            f"{job_id} failed on both GPU hosts; CPU fallback is forbidden: "
            + "; ".join(errors)
        )

    def fit_pair(
        self, first: GPUFitJob, second: GPUFitJob
    ) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
        with ThreadPoolExecutor(max_workers=2) as pool:
            local = pool.submit(self.fit, first, "local")
            remote = pool.submit(self.fit, second, "xbabe1")
            return local.result(), remote.result()
