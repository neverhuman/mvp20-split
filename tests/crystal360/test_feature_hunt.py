from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import nomad_feature_hunt.controller as foundry_controller

from nomad_feature_hunt.constants import EXPECTED_JNOCCIO_ROLES, role_specs
from nomad_feature_hunt.controller import (
    CampaignError,
    Settings,
    _budget_guard,
    _campaign,
    _microfeature_deduplication_errors,
    _record_attempt_start,
    _run_command,
)
from nomad_feature_hunt.ledger import HashChain, utc_now
from nomad_feature_hunt.schemas import (
    extract_json_payload,
    formula_fingerprint,
    semantic_similarity,
    validate_base_equation_cap,
    validate_concept,
)
from nomad_feature_hunt.scoring import (
    DualGPUExecutor,
    GPUFitJob,
    GPUScoringError,
    MatrixValidationError,
    choose_with_tie_band,
    validate_matrix_pair,
)
from nomad_feature_hunt.security import docker_sandbox_command, safe_extract_tar_bytes, static_check_generator


def concept(domain: str = "D01", concept_id: str = "D01.test.001") -> dict[str, object]:
    return {
        "concept_id": concept_id,
        "domain": domain,
        "name": "test",
        "equation": "sum_i r_i / N",
        "symbols": {"r": "distance"},
        "inputs": ["structure"],
        "parameters": {"cutoff": 4.0},
        "units": "angstrom",
        "normalization": "per atom",
        "periodic_construction": "minimum image",
        "invariances": ["translation", "rotation", "permutation"],
        "missingness_policy": "zero when empty",
        "physical_interpretation": "mean bond scale",
        "citations_or_derivation": ["original derivation"],
        "target_hypothesis": "local strain changes both targets",
        "complexity": "O(N^2)",
        "leakage_assessment": "geometry only",
        "falsification_test": "shuffle species",
        "microfeature_expansion": ["mean"],
        "implementation_guidance": "use periodic neighbors",
    }


def test_exact_role_roster_and_waves() -> None:
    roles = role_specs()
    assert len(roles) == EXPECTED_JNOCCIO_ROLES == 70
    assert len({role["id"] for role in roles}) == 70
    counts = {kind: sum(role["class"] == kind for role in roles) for kind in {r["class"] for r in roles}}
    assert counts == {
        "literature_scout": 10,
        "theorist": 40,
        "feature_implementer": 10,
        "experimental_analyst": 4,
        "blind_judge": 4,
        "memory_curator": 2,
    }


def test_schema_prompt_parsing_and_equation_cap() -> None:
    value = concept()
    assert validate_concept(value) == []
    assert extract_json_payload(f"```json\n{json.dumps(value)}\n```") == value
    features = [{"base_equation_id": "eq", **value} for _ in range(26)]
    assert "limit 25" in validate_base_equation_cap(features)[0]
    numbered = {**value, "equation": "sum_i r_i / 2"}
    assert formula_fingerprint(numbered) == formula_fingerprint({**value, "equation": " sum_i r_i / 99 "})


def test_semantic_similarity_and_family_aware_deduplication(tmp_path: Path) -> None:
    shared = {
        **concept(),
        "physical_interpretation": (
            "periodic local atomic neighbor graph spectral density encodes coordination shell "
            "rigidity and connectivity"
        ),
        "target_hypothesis": "coordination shell rigidity changes formation energy and bandgap",
        "falsification_test": "shuffle atomic species while retaining periodic neighbor geometry",
        "periodic_construction": "minimum image periodic neighbor graph over translated cells",
    }
    left = {
        **shared,
        "feature_id": "D01.feature.left",
        "base_equation_id": "D01.eq.left",
    }
    right = {
        **shared,
        "feature_id": "D01.feature.right",
        "base_equation_id": "D01.eq.right",
        "equation": "trace(L^2)",
    }
    assert semantic_similarity(left, right) >= 0.9
    settings = Settings(tmp_path, tmp_path / "inbox", tmp_path, "dedup-test")
    db, _events = _campaign(settings)
    errors = _microfeature_deduplication_errors(db, [left, right])
    assert "semantically similar" in errors[0]
    same_family = {
        **right,
        "base_equation_id": left["base_equation_id"],
        "concept_id": left["concept_id"],
    }
    assert _microfeature_deduplication_errors(db, [left, same_family]) == []


def test_hash_chain_detects_tampering(tmp_path: Path) -> None:
    chain = HashChain(tmp_path / "events.jsonl")
    chain.append("one", {"value": 1})
    chain.append("two", {"value": 2})
    assert chain.verify() == (True, None)
    lines = chain.path.read_text().splitlines()
    record = json.loads(lines[0])
    record["payload"]["value"] = 9
    lines[0] = json.dumps(record)
    chain.path.write_text("\n".join(lines) + "\n")
    assert chain.verify()[0] is False


def _tar(entries: dict[str, bytes], *, symlink: str | None = None) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, data in entries.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        if symlink:
            info = tarfile.TarInfo(symlink)
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            archive.addfile(info)
    return output.getvalue()


def test_safe_archive_rejects_traversal_and_links(tmp_path: Path) -> None:
    extracted = safe_extract_tar_bytes(_tar({"features/tab_01.json": b"[]"}), tmp_path / "ok")
    assert [path.name for path in extracted] == ["tab_01.json"]
    with pytest.raises(ValueError, match="unsafe archive path"):
        safe_extract_tar_bytes(_tar({"../escape": b"bad"}), tmp_path / "escape")
    with pytest.raises(ValueError, match="regular file"):
        safe_extract_tar_bytes(_tar({}, symlink="features/link"), tmp_path / "link")


def test_static_policy_and_docker_confinement(tmp_path: Path) -> None:
    safe = "import numpy as np\ndef featurize_structure(structure):\n    return {'x': float(len(structure))}\n"
    assert static_check_generator(safe) == []
    unsafe = "import socket\ndef featurize_structure(structure):\n    return {'x': 1.0}\n"
    assert "import is not allowed: socket" in static_check_generator(unsafe)
    paths = [tmp_path / name for name in ("generator.py", "runner.py", "inputs", "output")]
    for path in paths:
        path.mkdir() if path.suffix == "" else path.write_text("x")
    command = docker_sandbox_command(
        image="image@sha256:abc",
        generator=paths[0],
        harness=paths[1],
        public_inputs=paths[2],
        train_geometry=paths[2],
        test_geometry=paths[2],
        output=paths[3],
        real_sample_id=1,
    )
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command and "ALL" in command and "65532:65532" in command
    assert all("target" not in item for item in command)


def test_matrix_validation_and_tie_band(tmp_path: Path) -> None:
    train_ids = np.arange(1, 2401)
    test_ids = np.arange(1, 601)
    train = pd.DataFrame({"id": train_ids, "fresh": np.linspace(0, 1, 2400)})
    test = pd.DataFrame({"id": test_ids, "fresh": np.linspace(2, 3, 600)})
    paths = {}
    for name, frame in (("train", train), ("test", test), ("rerun_train", train), ("rerun_test", test)):
        path = tmp_path / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        paths[name] = path
    invariance = tmp_path / "invariance.json"
    invariance.write_text(json.dumps({
        "translation": True,
        "rotation": True,
        "atom_permutation": True,
        "periodic_wrapping": True,
        "equivalent_cell": True,
    }))
    validated = validate_matrix_pair(
        paths["train"],
        paths["test"],
        expected_train_ids=train_ids,
        expected_test_ids=test_ids,
        rerun_train_path=paths["rerun_train"],
        rerun_test_path=paths["rerun_test"],
        invariance_path=invariance,
    )
    assert validated.columns == ("fresh",)
    bad = train.assign(formation_energy_ev_natom=1.0)
    bad.to_parquet(paths["train"], index=False)
    with pytest.raises(MatrixValidationError, match="not identical"):
        validate_matrix_pair(
            paths["train"], paths["test"], expected_train_ids=train_ids, expected_test_ids=test_ids,
            rerun_train_path=paths["rerun_train"], rerun_test_path=paths["rerun_test"], invariance_path=invariance,
        )
    winner = choose_with_tie_band([
        {"batch_id": "large", "rmsle": 0.2, "feature_count": 100},
        {"batch_id": "small", "rmsle": 0.20005, "feature_count": 10},
    ])
    assert winner["batch_id"] == "small"


def test_gpu_dispatch_retries_once_on_other_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executor = DualGPUExecutor(tmp_path / "gpu")
    calls: list[tuple[str, int]] = []

    def fake_execute(
        job_id: str, job: GPUFitJob, host: str, attempt: int
    ) -> tuple[np.ndarray, np.ndarray]:
        calls.append((host, attempt))
        if attempt == 1:
            raise GPUScoringError(f"{job_id} primary failed")
        return np.asarray([1.0]), np.asarray([2.0])

    monkeypatch.setattr(executor, "_execute", fake_execute)
    job = GPUFitJob(
        train=np.ones((2, 1)),
        target=np.ones(2),
        training_mask=np.asarray([True, False]),
        validation_mask=np.asarray([False, True]),
        iterations=1,
        seed=1,
    )
    prediction, importance = executor.fit(job, "local")
    assert calls == [("local", 1), ("xbabe1", 2)]
    assert prediction.tolist() == [1.0] and importance.tolist() == [2.0]


def test_attempt_leases_resume_and_budget_enforcement(tmp_path: Path) -> None:
    settings = Settings(tmp_path, tmp_path / "inbox", tmp_path, "controller-test")
    db, _events = _campaign(settings)
    db.execute(
        "INSERT INTO campaign(run_id,created_at,state,max_wall_seconds,max_cost_usd) "
        "VALUES(?,?,?,?,?)",
        (settings.run_id, utc_now(), "running", 172_800, 500.0),
    )
    role = role_specs()[0]
    db.execute(
        "INSERT INTO roles(role_id,role_class,domain,wave,spec_json) VALUES(?,?,?,?,?)",
        (role["id"], role["class"], role["domain"], role["wave"], json.dumps(role)),
    )
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("stable prompt", encoding="utf-8")
    _record_attempt_start(db, "job-1", role, 0, prompt)
    _record_attempt_start(db, "job-1", role, 1, prompt)
    assert db.one("SELECT attempts FROM jobs WHERE job_id='job-1'")["attempts"] == 2
    assert db.one("SELECT COUNT(*) n FROM leases WHERE job_id='job-1'")["n"] == 2
    _budget_guard(settings)
    db.execute(
        "UPDATE campaign SET measured_cost_usd=500 WHERE run_id=?", (settings.run_id,)
    )
    with pytest.raises(CampaignError, match="budget exhausted"):
        _budget_guard(settings)


def test_failed_identity_probe_prevents_both_paid_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(tmp_path, tmp_path / "inbox", tmp_path, "identity-gate")
    branch_calls: list[str] = []
    monkeypatch.setattr(
        foundry_controller, "preflight", lambda _settings: {"ready": True, "blockers": []}
    )

    def fail_probe(_settings: Settings, _phase: str) -> dict[str, object]:
        raise CampaignError("identity failure")

    monkeypatch.setattr(foundry_controller, "_probe_jailgun", fail_probe)
    monkeypatch.setattr(
        foundry_controller, "run_jnoccio", lambda _settings: branch_calls.append("jnoccio")
    )
    monkeypatch.setattr(
        foundry_controller, "run_jailgun", lambda _settings: branch_calls.append("jailgun")
    )
    with pytest.raises(CampaignError, match="identity failure"):
        foundry_controller.run_campaign(settings)
    assert branch_calls == []


def test_campaign_storage_and_runtime_temporaries_stay_below_nomad(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nomad_root = tmp_path / "nomad"
    settings = Settings(
        tmp_path,
        nomad_root / "artifacts/nomad_theory_feature_hunt/inbox",
        nomad_root,
        "storage-boundary",
    )
    assert settings.run_root.resolve().is_relative_to(nomad_root.resolve())
    with pytest.raises(CampaignError, match="campaign storage must remain below"):
        Settings(tmp_path, tmp_path / "outside", nomad_root, "outside-run")

    executor = DualGPUExecutor(settings.run_root / "scoring/gpu_dispatch")
    assert executor.work_dir.resolve().is_relative_to(nomad_root.resolve())
    assert executor.REMOTE_TMP_ROOT == "/home/ubuntu/nomad/tmp"

    db, _events = _campaign(settings)
    db.execute(
        "INSERT INTO campaign(run_id,created_at,state,max_wall_seconds,max_cost_usd) "
        "VALUES(?,?,?,?,?)",
        (settings.run_id, utc_now(), "running", 172_800, 500.0),
    )
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> object:
        captured.update(kwargs)
        return foundry_controller.subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(foundry_controller.subprocess, "run", fake_run)
    downloads = settings.run_root / "jailgun/downloads"
    _run_command(
        settings,
        ["mock-command"],
        cwd=settings.run_root,
        timeout=1,
        env={"JAILGUN_DOWNLOADS_DIR": str(downloads)},
    )
    process_env = captured["env"]
    assert isinstance(process_env, dict)
    assert Path(process_env["TMPDIR"]).resolve().is_relative_to(nomad_root.resolve())
    assert Path(process_env["JAILGUN_DOWNLOADS_DIR"]).resolve().is_relative_to(
        nomad_root.resolve()
    )


def test_full_jnoccio_run_continues_after_incomplete_waves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(tmp_path, tmp_path / "inbox", tmp_path, "full-zyal")
    _campaign(settings)
    waves: list[int] = []
    monkeypatch.setattr(foundry_controller, "_run_research", lambda _settings: None)

    def fail_wave(_settings: Settings, wave: int) -> None:
        waves.append(wave)
        raise CampaignError(f"wave {wave} exhausted")

    monkeypatch.setattr(foundry_controller, "_run_wave", fail_wave)
    with pytest.raises(CampaignError, match="exactly 70"):
        foundry_controller.run_jnoccio(settings)
    assert waves == [1, 2, 3, 4, 5, 6]
    receipt = json.loads(
        (settings.run_root / "receipts/jnoccio_branch.json").read_text(encoding="utf-8")
    )
    assert len(receipt["wave_failures"]) == 6


def test_exhausted_jnoccio_role_is_never_submitted_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(tmp_path, tmp_path / "inbox", tmp_path, "retry-ceiling")
    db, _events = _campaign(settings)
    role = role_specs()[0]
    db.execute(
        "INSERT INTO roles(role_id,role_class,domain,wave,spec_json,status) "
        "VALUES(?,?,?,?,?,'failed')",
        (role["id"], role["class"], role["domain"], role["wave"], json.dumps(role)),
    )
    db.execute(
        "INSERT INTO jobs(job_id,role_id,wave,prompt_sha256,prompt_path,status,attempts) "
        "VALUES(?,?,?,?,?,'failed',2)",
        (role["id"], role["id"], role["wave"], "0" * 64, "prompt.txt"),
    )
    with db.connect() as connection:
        for attempt in (0, 1):
            connection.execute(
                "INSERT INTO attempts(job_id,attempt,started_at,prompt_sha256,success) "
                "VALUES(?,?,?,?,0)",
                (role["id"], attempt, utc_now(), "0" * 64),
            )
    monkeypatch.setattr(
        foundry_controller,
        "_run_command",
        lambda *_args, **_kwargs: pytest.fail("exhausted role was resubmitted"),
    )
    with pytest.raises(CampaignError, match="after one retry"):
        foundry_controller._run_wave(settings, role["wave"])
