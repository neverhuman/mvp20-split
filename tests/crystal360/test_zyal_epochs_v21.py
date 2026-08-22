from __future__ import annotations

import json
import hashlib
import re
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from nomad_feature_hunt.v2.zyal_epochs import (
    BASELINE_REGISTRY_COLUMNS,
    CAMPAIGN_VERSION,
    CONFIRMATION_FOLDS,
    CONFIRMATION_SEEDS,
    CONFIRMATION_TREES,
    CURRENT_CHAMPION_MEAN_RMSLE,
    DOMAINS,
    EPOCHS,
    EXPECTED_JNOCCIO_ROLES,
    GENETIC_GENERATIONS,
    GENETIC_POPULATION,
    MAX_JNOCCIO_ATTEMPTS,
    ROLE_COUNTS,
    TARGETS,
    BudgetError,
    CampaignError,
    CampaignStore,
    PhaseBackend,
    ReceiptError,
    Settings,
    assert_secret_free,
    build_epoch_prompt,
    build_top50_reports,
    campaign_phases,
    categorical_agent_feedback,
    controller_feature_id,
    discover_disk_profiles,
    dispatch_groups,
    dispatch_role_wave,
    dynamic_worker_count,
    epoch_role_specs,
    preflight,
    reconcile_router_pool,
    rank_discovery_families,
    rank_discovery_records,
    resume,
    role_specs,
    run,
    sanitize_router_metadata,
    seal_confirmation_folds,
    select_confirmed_winners,
    status,
    utilization_receipt,
    validate_epoch_role_payload,
    validate_confirmation_receipt,
    validate_discovery_protocol,
    validate_genetic_history,
    validate_receipt,
    verify_promotion_manifest,
    write_receipt,
)


def _health(slot_counts: dict[str, int] | None = None) -> dict[str, object]:
    slots = slot_counts or {
        "user_1": 42,
        "user_2": 28,
        "user_3": 28,
        "user_4": 18,
        "user_5": 28,
        "user_6": 22,
        "user_7": 22,
    }
    return {
        "ok": True,
        "provider": "jnoccio",
        "upstream_key_source": "users_pool",
        "visible_model": "jnoccio/jnoccio-fusion",
        "user_count": len(slots),
        "eligible_slot_count": sum(slots.values()),
        "keyed_models": 314,
        "available_models": 333,
        "per_user_slot_counts": slots,
        "per_provider_slot_counts": {"openrouter": 49},
    }


def _family_card(slug: str) -> dict[str, object]:
    return {
        "family_slug": slug,
        "domain": "D01",
        "physical_hypothesis": (
            f"The {slug} distribution of inequivalent orbit populations resolves local "
            "symmetry breaking that changes cohesive and electronic response."
        ),
        "target_affinity": "both",
        "kernel": "symmetry",
        "custom_plugin_required": False,
        "inputs": ["periodic_structure"],
        "citation_ids": ["source-1.claim-1"],
        "atlas_novelty_argument": (
            f"The {slug} joint distribution of orbit population, residual, and species "
            "conditioning is absent from the complete baseline registry."
        ),
        "invariances": [
            "translation",
            "rotation",
            "atom_permutation",
            "periodic_wrapping",
            "equivalent_cell",
        ],
        "falsifier": (
            "Randomize orbit membership while preserving composition and pair distances; "
            "the proposed signal should then disappear."
        ),
        "complexity": "O(N log N)",
    }


def _settings(tmp_path: Path) -> Settings:
    users = tmp_path / "users"
    for index in range(1, 8):
        directory = users / f"user_{index}"
        directory.mkdir(parents=True)
        (directory / "llm.env").write_text("fixture\n", encoding="utf-8")
    default = users / "user"
    default.mkdir()
    (default / "state.sqlite").write_bytes(b"")
    columns = tmp_path / "baseline-columns.json"
    columns.write_text(
        json.dumps([f"baseline-{index:05d}" for index in range(BASELINE_REGISTRY_COLUMNS)]),
        encoding="utf-8",
    )
    summary = tmp_path / "zyal-summary.json"
    summary.write_text(
        json.dumps(
            {
                "validated_columns": 831,
                "augmentation_rejections": [
                    {"feature_id": "rejected", "reason": "invariance_failure"}
                ],
            }
        ),
        encoding="utf-8",
    )
    nomad = tmp_path / "nomad"
    return Settings(
        repo_root=Path(__file__).resolve().parents[2],
        run_id="fixture-run",
        nomad_root=nomad,
        inbox_root=nomad / "artifacts/nomad_theory_feature_hunt/v2/inbox",
        users_root=users,
        synchronizer=tmp_path / "missing-sync.sh",
        baseline_columns_path=columns,
        zyal_summary_path=summary,
    )


def _preflight(settings: Settings) -> dict[str, object]:
    return preflight(
        settings,
        health=_health(),
        jekko_profile_fetcher=lambda _settings: tuple(
            f"user_{index}" for index in range(1, 8)
        ),
        run_synchronizer=False,
        gpu_checker=lambda: {"ready": True, "local": {}, "remote": {}},
    )


def test_ten_epoch_roster_is_exact_and_largest_wave_is_dynamic() -> None:
    roles = role_specs()
    assert len(roles) == EXPECTED_JNOCCIO_ROLES == 360
    assert len({role["id"] for role in roles}) == 360
    assert Counter(role["class"] for role in epoch_role_specs(1)) == ROLE_COUNTS
    assert [len(group) for group in dispatch_groups(1)] == [24, 10, 2]
    assert len(campaign_phases()) == 54
    assert controller_feature_id(10, "D10", "Entropy OT", "Joint", "Slope") == (
        "v2.1.e10.d10.entropy-ot.joint.slope"
    )


def test_architect_rejects_generic_example_echo() -> None:
    role = epoch_role_specs(1)[0]
    cards = [_family_card(f"d01-novel-family-{index:02d}") for index in range(1, 4)]
    for card in cards:
        card["physical_hypothesis"] = (
            "A declared periodic structural population captures a distinct physical mechanism "
            "not represented by the baseline registry."
        )
    errors = validate_epoch_role_payload(role, {"family_cards": cards})
    assert any("forbidden generic family slug" in error for error in errors)
    assert any("physical hypotheses must be distinct" in error for error in errors)


def test_profile_discovery_ignores_empty_default_and_reconciles_seven(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    assert discover_disk_profiles(settings.users_root) == tuple(
        f"user_{index}" for index in range(1, 8)
    )
    pool = reconcile_router_pool(discover_disk_profiles(settings.users_root), _health())
    assert pool.valid
    assert pool.receipt["user_count"] == 7
    assert pool.receipt["eligible_slot_count"] == 188
    assert dynamic_worker_count(24, _health()) == 24
    assert dynamic_worker_count(24, _health({"user_1": 3})) == 3


def test_router_reconciliation_fails_disk_live_and_zero_slot_mismatches(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    profiles = discover_disk_profiles(settings.users_root)
    health = _health({"user_1": 1, "user_2": 0, "ghost": 1})
    pool = reconcile_router_pool(profiles, health)
    assert not pool.valid
    assert any("missing from Fusion" in error for error in pool.errors)
    assert any("missing from disk" in error for error in pool.errors)
    assert any("zero eligible" in error for error in pool.errors)


def test_secret_free_receipts_and_router_metadata_allowlist() -> None:
    with pytest.raises(ReceiptError, match="credential-like field"):
        assert_secret_free({"router": {"api_key": "not-serialized"}})
    with pytest.raises(ReceiptError, match="credential-like value"):
        assert_secret_free({"value": "Bearer abcdefghijklmnopqrstuvwxyz"})
    assert sanitize_router_metadata(
        {
            "cost_usd": 1.5,
            "rate_limited": True,
            "api_key": "must-drop",
            "credential_user_id": "user_3",
        }
    ) == {"cost_usd": 1.5, "rate_limited": True, "credential_user_id": "user_3"}


def test_preflight_indexes_baselines_and_keeps_legacy_runbook_unchanged(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    report = _preflight(settings)
    assert report["ready"], report["blockers"]
    assert report["checks"]["roles"] == 360
    assert report["checks"]["baseline"]["baseline_columns"] == 10_800
    assert report["checks"]["baseline"]["graduated_zyal_columns"] == 831
    legacy = (
        Path(__file__).resolve().parents[2]
        / "ops/nomad-feature-hunt/01-jnoccio-research-generation.zyal"
    )
    assert hashlib.sha256(legacy.read_bytes()).hexdigest() == (
        "646b3990c418c8a187acdcd2d499d44ddbc4c25501e8374b61fe4ad2d21201b9"
    )


def test_prepared_and_interrupted_leases_are_accounted_once(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = CampaignStore(settings)
    role = epoch_role_specs(1)[0]
    store.register_roles([role])
    prompt = settings.run_root / "prompts/fixture.json"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text("{}", encoding="utf-8")
    store.prepare_lease(role["id"], 0, prompt)
    assert store.budget_summary().attempts == 0
    store.submit_lease(role["id"], 0)
    assert store.budget_summary().attempts == 1
    assert store.recover_interrupted_leases() == 1
    assert store.budget_summary().debited_usd == 2.5
    with pytest.raises(BudgetError, match="consumed"):
        store.prepare_lease(role["id"], 0, prompt)
    store.prepare_lease(role["id"], 1, prompt)
    store.submit_lease(role["id"], 1)
    assert store.budget_summary().attempts == 2


def test_dispatch_retries_malformed_result_once_and_uses_live_cap(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = CampaignStore(settings)
    role = epoch_role_specs(1)[0]
    store.register_roles([role])
    prompt = build_epoch_prompt(role, {})
    calls: list[list[str]] = []

    def runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        result_dir = Path(command[command.index("--results-dir") + 1])
        result_dir.mkdir(parents=True, exist_ok=True)
        attempt = len(calls) - 1
        assistant = "not-json" if attempt == 0 else json.dumps(
            {"family_cards": [_family_card(f"family-{index}") for index in range(3)]}
        )
        result = {
            "success": True,
            "assistant_text": assistant,
            "provider_id": "jnoccio",
            "model_id": "jnoccio-router",
            "credential_user_id": f"user_{attempt + 1}",
        }
        if attempt == 0:
            result["router_metadata"] = {
                "cost_usd": 0.0,
                "rate_limited": True,
                "rebalanced": True,
            }
        (result_dir / f"{role['id']}.json").write_text(
            json.dumps(result),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    result = dispatch_role_wave(
        settings,
        store,
        [role],
        {role["id"]: prompt},
        epoch=1,
        wave_id="architects",
        health_fetcher=lambda _url: _health(),
        runner=runner,
    )
    assert result["valid"] == 1 and result["failed"] == []
    assert len(calls) == 2
    assert all(command[command.index("--workers") + 1] == "1" for command in calls)
    assert all(command[command.index("--model") + 1] == "jnoccio-router" for command in calls)
    assert store.budget_summary().attempts == 2
    assert store.budget_summary().reported_cost_usd == 0.0
    receipt = json.loads(
        (settings.run_root / "receipts/utilization/epoch-01-architects-attempt-0.json").read_text()
    )
    assert receipt["rate_limits"] == 1


def test_dispatch_resumes_at_the_only_remaining_attempt(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = CampaignStore(settings)
    role = epoch_role_specs(1)[0]
    store.register_roles([role])
    prompt = build_epoch_prompt(role, {})
    prompt_path = settings.run_root / "prompts/attempt-0.json"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")
    result_path = settings.run_root / "raw_responses/attempt-0.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps({"assistant_text": "not-json"}), encoding="utf-8")
    store.prepare_lease(role["id"], 0, prompt_path)
    store.submit_lease(role["id"], 0)
    store.finish_attempt(
        role["id"],
        0,
        result_path=result_path,
        valid=False,
        credential_user_id="user_1",
        router_metadata={"cost_usd": 0.0},
        errors=["strict JSON error"],
    )
    calls: list[list[str]] = []

    def runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        result_dir = Path(command[command.index("--results-dir") + 1])
        result_dir.mkdir(parents=True, exist_ok=True)
        result = {
            "success": True,
            "assistant_text": json.dumps(
                {"family_cards": [_family_card(f"family-{index}") for index in range(3)]}
            ),
            "credential_user_id": "user_2",
        }
        (result_dir / f"{role['id']}.json").write_text(json.dumps(result), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    result = dispatch_role_wave(
        settings,
        store,
        [role],
        {role["id"]: prompt},
        epoch=1,
        wave_id="architects-resumed",
        health_fetcher=lambda _url: _health(),
        runner=runner,
    )
    assert result["valid"] == 1 and result["failed"] == []
    assert len(calls) == 1
    assert store.budget_summary().attempts == 2


def test_epoch_one_coverage_receipt_counts_only_valid_routed_users() -> None:
    results = [
        {
            "success": True,
            "credential_user_id": f"user_{index}",
            "router_metadata": {"rate_limited": index == 1, "rebalanced": index == 1},
        }
        for index in range(1, 8)
    ]
    receipt = utilization_receipt(
        epoch=1,
        wave_id="coverage",
        requested_workers=7,
        pool=reconcile_router_pool(tuple(f"user_{i}" for i in range(1, 8)), _health()).receipt,
        results=results,
    )
    assert receipt["coverage_complete"] is True
    assert receipt["rate_limits"] == 1
    validate_receipt("per_user_utilization", receipt)


def _top_records() -> list[dict[str, object]]:
    records = []
    for target in TARGETS:
        for index in range(30):
            records.append(
                {
                    "feature_id": f"v2.1.{target}.{index}",
                    "target": target,
                    "equation": f"x_{index}",
                    "configuration": {"index": index},
                    "domain": f"D{index % 10 + 1:02d}",
                    "physical_rationale": "A physically declared periodic summary.",
                    "novelty_proof": {"baseline_match": False},
                    "validation_status": "valid",
                    "strength_components": {
                        "catboost_importance_percentile": 1 - index / 100,
                        "residual_correlation_percentile": 0.8,
                        "mutual_information_percentile": 0.7,
                    },
                }
            )
    return records


def test_top50_strength_report_is_exactly_25_per_target(tmp_path: Path) -> None:
    report = build_top50_reports(_top_records(), tmp_path)
    assert report["features"] == 50 and report["per_target"] == 25
    rows = json.loads((tmp_path / "top50_features.json").read_text())
    assert Counter(row["target"] for row in rows) == {target: 25 for target in TARGETS}
    assert rows[0]["strength"] == pytest.approx(0.905)


def test_discovery_ranking_uses_all_metrics_and_feedback_is_categorical() -> None:
    validate_discovery_protocol(
        {
            "seeds": [1701, 2909, 4219],
            "trees": 150,
            "task_type": "GPU",
            "confirmation_folds_accessed": False,
        }
    )
    records = []
    for target in TARGETS:
        for index in range(3):
            records.append(
                {
                    "feature_id": f"{target}-{index}",
                    "family_id": f"family-{index}",
                    "target": target,
                    "domain": f"D{index + 1:02d}",
                    "compute_seconds": 0.5 + index,
                    "redundancy": index / 10,
                    "oof_residual_correlation": 0.1 + index / 10,
                    "spearman_correlation": 0.2 + index / 10,
                    "mutual_information": 0.3 + index / 10,
                    "catboost_importance_by_seed": {
                        "1701": 0.4 + index,
                        "2909": 0.5 + index,
                        "4219": 0.6 + index,
                    },
                }
            )
    ranked = rank_discovery_records(records)
    assert all("strength_components" in row and "rank" in row for row in ranked)
    families = rank_discovery_families(ranked)
    assert len(families) == 6
    assert all("median_catboost_importance" in row and "rank" in row for row in families)
    packet = categorical_agent_feedback(ranked)
    assert packet["categorical_only"] is True
    assert all(
        isinstance(value, str)
        for feedback in packet["feature_feedback"].values()
        for value in feedback.values()
    )


def _confirmation(output_dir: Path) -> dict[str, object]:
    seal = seal_confirmation_folds(output_dir, list(range(2_400)))
    binding = {
        "seeds": list(CONFIRMATION_SEEDS),
        "folds": CONFIRMATION_FOLDS,
        "trees": CONFIRMATION_TREES,
        "fold_hashes": seal["fold_hashes"],
    }
    champion = {
        TARGETS[0]: 0.023,
        TARGETS[1]: 2 * CURRENT_CHAMPION_MEAN_RMSLE - 0.023,
    }
    controls = [
        {"target": target, "control": control, "mean_rmsle": score, **binding}
        for target in TARGETS
        for control, score in (
            ("current_champion", champion[target]),
            ("atlas_winner", champion[target] + 0.001),
            ("existing_809", champion[target] + 0.002),
        )
    ]
    views = []
    for target in TARGETS:
        views.extend(
            [
                {
                    "target": target,
                    "kind": "candidate",
                    "view_id": f"{target}-large",
                    "mean_rmsle": champion[target] - 0.0004,
                    "feature_count": 500,
                    "compact": False,
                    **binding,
                },
                {
                    "target": target,
                    "kind": "candidate",
                    "view_id": f"{target}-compact",
                    "mean_rmsle": champion[target] - 0.0002,
                    "feature_count": 50,
                    "compact": True,
                    **binding,
                },
            ]
        )
    selected = select_confirmed_winners(views)
    return {
        "schema_version": CAMPAIGN_VERSION,
        "receipt_type": "sealed_confirmation_result",
        "seeds": list(CONFIRMATION_SEEDS),
        "folds": CONFIRMATION_FOLDS,
        "trees": CONFIRMATION_TREES,
        "task_type": "GPU",
        "opened_once": True,
        "fold_hashes": seal["fold_hashes"],
        "controls": controls,
        "views": views,
        **selected,
    }


def test_confirmation_is_two_seed_sealed_and_error_wins_over_size(tmp_path: Path) -> None:
    receipt = _confirmation(tmp_path)
    validate_confirmation_receipt(receipt)
    assert all(row["feature_count"] == 500 for row in receipt["winners"].values())
    assert all(
        row["feature_count"] == 50
        for row in receipt["compact_alternative"]["targets"].values()
    )
    with pytest.raises(CampaignError, match="already opened"):
        seal_confirmation_folds(tmp_path, list(range(2_400)))
    assert seal_confirmation_folds(tmp_path, list(range(2_400)), resume=True) == json.loads(
        (tmp_path / "confirmation-opened.json").read_text()
    )


def test_genetic_history_requires_population_24_and_ten_generations() -> None:
    receipt = {
        "schema_version": CAMPAIGN_VERSION,
        "receipt_type": "genetic_reduction_history",
        "target": TARGETS[0],
        "population_size": GENETIC_POPULATION,
        "generations": GENETIC_GENERATIONS,
        "seed": 17,
        "history": [{"generation": index} for index in range(10)],
        "preregistered_views": [{"view_id": f"view-{index}"} for index in range(8)],
    }
    validate_genetic_history(receipt)
    with pytest.raises(ReceiptError, match="population"):
        validate_genetic_history({**receipt, "population_size": 23})


class _FakeBackend(PhaseBackend):
    def execute(self, _settings: Settings, phase: str) -> dict[str, object]:
        match = re.fullmatch(
            r"epoch-(\d{2})-(generation|compilation|execution|screening|reduction)", phase
        )
        if match is None:
            return {"phase": phase, "fake": True, "test_labels_used": False}
        epoch, name = int(match.group(1)), match.group(2)
        if name == "generation":
            return {
                "phase": phase,
                "epoch": epoch,
                "roles": 36,
                "max_retries_per_role": 1,
                "strict_json": True,
                "controller_generated_ids": True,
            }
        if name == "compilation":
            return {
                "phase": phase,
                "epoch": epoch,
                "static_checks_passed": True,
                "plugin_limit_bytes": 20 * 1024,
                "individual_column_quarantine": True,
            }
        if name == "execution":
            return {
                "phase": phase,
                "epoch": epoch,
                "smoke_structures": 16,
                "invariance_structures": 64,
                "train_rows": 2_400,
                "test_rows": 600,
                "all_five_invariances": True,
                "deterministic": True,
                "individual_column_quarantine": True,
                "test_labels_used": False,
            }
        if name == "screening":
            return {
                "phase": phase,
                "epoch": epoch,
                "protocol": {
                    "seeds": [1701, 2909, 4219],
                    "trees": 150,
                    "task_type": "GPU",
                    "confirmation_folds_accessed": False,
                },
                "ranking_metrics": [
                    "compute_cost",
                    "redundancy",
                    "oof_residual_correlation",
                    "spearman_correlation",
                    "mutual_information",
                    "catboost_importance",
                ],
                "adaptive_feedback": "categorical_only",
            }
        return {
            "phase": phase,
            "epoch": epoch,
            "population_size": 24,
            "generations": 10,
            "preregistered_views_per_target": {target: 8 for target in TARGETS},
            "confirmation_still_sealed": True,
        }


class _NoCallBackend(PhaseBackend):
    def execute(self, _settings: Settings, phase: str) -> dict[str, object]:
        raise AssertionError(f"completed phase was rerun: {phase}")


def _materialize_fake_success(settings: Settings) -> None:
    store = CampaignStore(settings)
    with store.connect() as connection:
        connection.execute("UPDATE roles SET status='complete'")
        for index in range(7_000):
            domain = DOMAINS[index % len(DOMAINS)].id
            connection.execute(
                "INSERT INTO columns VALUES(?,?,?,?,?,?,?,NULL)",
                (
                    f"new-{index:05d}",
                    index // 700 + 1,
                    domain,
                    f"family-{index % 160:03d}",
                    1,
                    1,
                    int(index < 3_000),
                ),
            )
        for index in range(160):
            connection.execute(
                "INSERT INTO families VALUES(?,?,?,1)",
                (f"family-{index:03d}", index // 16 + 1, DOMAINS[index % 10].id),
            )
    build_top50_reports(_top_records(), settings.run_root / "reports/top50")
    pool = reconcile_router_pool(
        discover_disk_profiles(settings.users_root), _health()
    ).receipt
    routed_results = [
        {
            "success": True,
            "credential_user_id": f"user_{index}",
            "router_metadata": {"cost_usd": 1.0},
        }
        for index in range(1, 8)
    ]
    for epoch in range(1, EPOCHS + 1):
        utilization = utilization_receipt(
            epoch=epoch,
            wave_id="fake",
            requested_workers=7,
            pool=pool,
            results=routed_results,
        )
        write_receipt(
            settings.run_root / f"receipts/utilization/epoch-{epoch:02d}-fake.json",
            "per_user_utilization",
            utilization,
        )
        write_receipt(
            settings.run_root / f"receipts/router_pool/epoch-{epoch:02d}-fake.json",
            "router_pool_snapshot",
            pool,
        )
        write_receipt(
            settings.run_root / f"receipts/epochs/epoch-{epoch:02d}.json",
            "epoch_result",
            {
                "epoch": epoch,
                "roles": 36,
                "attempts": 36,
                "new_executed_columns": 700,
                "novel_valid_columns": 300,
                "valid_by_domain": {domain.id: 30 for domain in DOMAINS},
                "base_families": 16,
                "phase_receipts": {},
            },
        )
        for judge in range(1, 3):
            path = (
                settings.run_root
                / f"judgments/epoch-{epoch:02d}/zyal10.e{epoch:02d}.blind-judge-{judge:02d}.blind.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"receipt_ids": ["fake"], "judgments": ["valid"]}))
    for target in TARGETS:
        write_receipt(
            settings.run_root / f"receipts/genetic/{target}.json",
            "genetic_reduction_history",
            {
                "target": target,
                "population_size": 24,
                "generations": 10,
                "seed": 20260719,
                "history": [{"generation": index} for index in range(10)],
                "preregistered_views": [{"view_id": f"{target}-view-{index}"} for index in range(8)],
            },
        )
    confirmation = _confirmation(settings.run_root / "confirmation/sealed")
    write_receipt(
        settings.run_root / "receipts/confirmation/sealed-results.json",
        "sealed_confirmation_result",
        confirmation,
    )


def test_fake_ten_epoch_campaign_resumes_verifies_and_promotes(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    report = _preflight(settings)
    assert report["ready"]
    _materialize_fake_success(settings)
    result = run(settings, backend=_FakeBackend())
    assert result["complete"], result["missing"]
    assert result["counts"]["roles"] == 360
    assert result["counts"]["new_executed_columns"] == 7_000
    assert result["counts"]["novel_valid_columns"] == 3_000
    manifest = settings.run_root / "promotion/final_manifest.json"
    assert verify_promotion_manifest(manifest, settings.run_root) == (True, [])
    assert (settings.run_root / "final_manifests/promotion_manifest.json").exists()
    assert status(settings)["state"] == "complete"
    assert resume(settings, backend=_NoCallBackend())["complete"]
    assert len(campaign_phases()) == 1 + EPOCHS * 5 + 3
    assert MAX_JNOCCIO_ATTEMPTS == 720
    manifest_payload = json.loads(manifest.read_text())
    referenced = settings.run_root / next(iter(manifest_payload["artifacts"]))
    referenced.write_bytes(referenced.read_bytes() + b"tampered")
    valid, errors = verify_promotion_manifest(manifest, settings.run_root)
    assert not valid and any("hash differs" in error for error in errors)
