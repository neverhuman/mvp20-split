from __future__ import annotations

import json
from pathlib import Path

from nomad_feature_hunt.ledger import HashChain, atomic_json, sha256_file, utc_now

from .budget import BudgetAccount
from .constants import CAMPAIGN_PHASES, DOMAINS, TARGETS, role_specs
from .state import CampaignDB, mark_batch_submitted, prepare_job_batch, record_attempt_result
from .verification import verify_campaign


def _receipt(
    db: CampaignDB,
    run_root: Path,
    receipt_id: str,
    kind: str,
    payload: dict[str, object],
    *,
    role_id: str | None = None,
) -> Path:
    path = run_root / f"receipts/fake/{receipt_id.replace(':', '-')}.json"
    atomic_json(path, payload)
    db.execute(
        "INSERT OR REPLACE INTO receipts VALUES(?,?,?,?,?,?,?)",
        (
            receipt_id,
            kind,
            role_id,
            str(path),
            sha256_file(path),
            1,
            json.dumps(payload, sort_keys=True),
        ),
    )
    return path


def run_fake_180_campaign(run_root: Path, run_id: str = "fake-v2-campaign") -> dict[str, object]:
    """Exercise every controller state gate without external model or GPU calls."""

    run_root.mkdir(parents=True, exist_ok=True)
    db = CampaignDB(run_root / "campaign.sqlite3")
    budget = BudgetAccount(run_root / "budget.sqlite3")
    events = HashChain(run_root / "events.jsonl")
    now = utc_now()
    db.execute(
        "INSERT INTO campaign VALUES(?,?,?,'preflight',?,NULL)",
        (run_id, now, "running", now),
    )
    budget.reserve("research-and-operations", "research")
    budget.settle("research-and-operations", None)
    roles = role_specs()
    with db.connect() as connection:
        for role in roles:
            connection.execute(
                "INSERT INTO roles(role_id,role_class,domain,wave,spec_json) VALUES(?,?,?,?,?)",
                (
                    role["id"], role["class"], role["domain"], role["wave"],
                    json.dumps(role, sort_keys=True),
                ),
            )
    for batch_index in range(0, len(roles), 20):
        batch_roles = roles[batch_index : batch_index + 20]
        batch_id = f"fake-{batch_index // 20:02d}"
        prepare_job_batch(
            db,
            batch_id=batch_id,
            jobs_path=run_root / f"queue/jobs/{batch_id}.json",
            prompt_dir=run_root / "prompts",
            roles_and_prompts=[
                (role, json.dumps({"dry_run_role": role["id"]}, separators=(",", ":")))
                for role in batch_roles
            ],
            attempt=0,
        )
        mark_batch_submitted(db, budget, batch_id)
        for role in batch_roles:
            result = {
                "success": True,
                "assistant_text": "{}",
                "provider_id": "fake-jnoccio",
                "model_id": "jnoccio-router",
                "credential_user_id": None,
                "router_metadata": None,
            }
            record_attempt_result(
                db,
                budget,
                role_id=role["id"],
                attempt=0,
                result=result,
                raw_result_path=run_root / f"queue/results/{role['id']}.json",
                valid=True,
                errors=[],
            )
            _receipt(
                db,
                run_root,
                f"jnoccio:{role['id']}:0",
                "jnoccio",
                {"role_id": role["id"], "valid": True, "router_metadata": None},
                role_id=role["id"],
            )

    atlas = run_root / "inputs/atlas"
    atlas.mkdir(parents=True, exist_ok=True)
    controller = run_root / "inputs/controller"
    controller.mkdir(parents=True, exist_ok=True)
    frozen_controller = controller / "fake_controller.py"
    frozen_controller.write_text("# fake dry-run controller\n", encoding="utf-8")
    atomic_json(
        controller / "manifest.json",
        {
            "frozen": True,
            "files": {
                "fake_controller.py": {
                    "source": "fake-dry-run",
                    "sha256": sha256_file(frozen_controller),
                }
            },
            "test_labels_used": False,
        },
    )
    atomic_json(
        atlas / "staging_receipt.json",
        {"predictors": 9969, "definitions": 9160, "frozen": True, "test_labels_used": False},
    )
    novelty = run_root / "novelty"
    novelty.mkdir(parents=True, exist_ok=True)
    atomic_json(
        novelty / "atlas_registry.receipt.json",
        {
            "columns": 9969,
            "definitions": 9160,
            "numeric_signatures": 9969,
            "formula_fingerprints": 9969,
            "semantic_fingerprints": 9969,
            "existing_809": 809,
        },
    )
    evidence: list[dict[str, object]] = []
    for domain in DOMAINS:
        for index in range(25):
            evidence.append(
                {
                    "source_id": f"fake-{domain.id}-{index:02d}",
                    "title": f"Fake relevant source {domain.id} {index}",
                    "domains": [domain.id],
                    "relevant": True,
                }
            )
    atomic_json(run_root / "evidence/evidence.json", evidence)
    atomic_json(
        run_root / "memory/v1_seeds/idea_seeds.json",
        [
            {
                "v1_concept_id": f"fake-{index:03d}",
                "v2_status": "unverified_idea_seed",
            }
            for index in range(74)
        ],
    )
    atomic_json(
        run_root / "memory/v1_seeds/negative_memory.json",
        [{"v1_job_id": "fake-invalid", "v2_status": "invalid_output_negative_memory"}],
    )
    for role in roles:
        if role["class"] == "memory_curator":
            atomic_json(
                run_root / f"memory/{role['id']}.json",
                {"classifications": [], "receipt_ids": ["matrix:fake", "score:fake"]},
            )
    smoke = run_root / "receipts/sandbox/precompile-gate.json"
    atomic_json(
        smoke,
        {
            "trusted_toy_kernels": 10,
            "trusted_structures": 16,
            "trusted_invariances": True,
            "custom_toy": True,
            "custom_structures": 16,
            "custom_invariances": True,
        },
    )

    with db.connect() as connection:
        for domain in DOMAINS:
            for index in range(400):
                family = f"family-{index % 16:02d}"
                equation = f"v2.{domain.id.casefold()}.equation-{index // 25:02d}"
                feature_id = f"v2.{domain.id.casefold()}.{family}.spec-{index // 25:02d}.out-{index:03d}"
                registry = {
                    "feature_id": feature_id,
                    "base_equation_id": equation,
                    "status": "computed",
                }
                connection.execute(
                    "INSERT INTO columns VALUES(?,?,?,?,?,?)",
                    (
                        feature_id,
                        family,
                        domain.id,
                        "validated" if index < 250 else "quarantined",
                        None if index < 250 else "fake_negative_control",
                        json.dumps(registry, sort_keys=True),
                    ),
                )

    matrix_root = run_root / "matrices/validated/fake"
    matrix_root.mkdir(parents=True, exist_ok=True)
    train_path = matrix_root / "train.parquet"
    test_path = matrix_root / "test.parquet"
    train_path.write_bytes(b"fake-train-matrix")
    test_path.write_bytes(b"fake-test-matrix")
    matrix_receipt = _receipt(
        db,
        run_root,
        "matrix:fake",
        "matrix",
        {"rows": [2400, 600], "columns": 2500, "test_labels_used": False},
    )
    with db.connect() as connection:
        for domain in DOMAINS:
            for index in range(16):
                connection.execute(
                    "INSERT INTO matrices VALUES(?,?,?,?,?,?,?)",
                    (
                        f"{domain.id.casefold()}.equation-{index:02d}",
                        f"family-{index:02d}",
                        str(train_path),
                        str(test_path),
                        25,
                        1,
                        "matrix:fake",
                    ),
                )

    score_receipt = _receipt(
        db,
        run_root,
        "score:fake",
        "score",
        {"discovery_folds": 2, "confirmation_folds": 5, "test_labels_used": False},
    )
    with db.connect() as connection:
        for target in TARGETS:
            for index in range(10):
                connection.execute(
                    "INSERT INTO scores VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        f"discovery-{target}-{index}",
                        "discovery",
                        target,
                        f"family-{index:02d}",
                        DOMAINS[index % len(DOMAINS)].id,
                        1,
                        f"group-{index:02d}",
                        json.dumps({"categorical_feedback": "positive"}),
                        "score:fake",
                    ),
                )
            rmsle = 0.0230 if target.startswith("formation") else 0.0770
            confirmation = {
                "view_id": f"winner-{target}",
                "rmsle": rmsle,
                "feature_count": 100,
                "folds": 5,
                "trees": 400,
            }
            connection.execute(
                "INSERT INTO scores VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    f"confirmation-{target}", "confirmation", target, None, None, None, None,
                    json.dumps(confirmation, sort_keys=True), "score:fake",
                ),
            )
        judge_roles = [role for role in roles if role["class"] == "blind_judge"]
        for index, role in enumerate(judge_roles):
            atomic_json(
                run_root / f"judgments/{role['id']}.json",
                {"judgments": ["receipt-bound dry run"]},
            )
            connection.execute(
                "INSERT INTO judgments VALUES(?,?,?,?)",
                (
                    f"fake-judgment-{index}", role["id"],
                    json.dumps(["matrix:fake", "score:fake"]),
                    json.dumps({"accepted": True}),
                ),
            )
        analyst_roles = [role for role in roles if role["class"] == "experimental_analyst"]
        for index, role in enumerate(analyst_roles):
            atomic_json(
                run_root / f"judgments/{role['id']}.json",
                {"analysis": ["receipt-bound dry run"]},
            )
            connection.execute(
                "INSERT INTO judgments VALUES(?,?,?,?)",
                (
                    f"fake-analysis-{index}", role["id"],
                    json.dumps(["matrix:fake", "score:fake"]),
                    json.dumps({"analysis": ["receipt-bound dry run"]}),
                ),
            )

    for phase in CAMPAIGN_PHASES:
        payload: dict[str, object] = {"phase": phase, "dry_run": True}
        if phase == "evidence":
            payload["sources"] = 250
        _receipt(db, run_root, f"phase:{phase}", "phase", payload)
        db.execute(
            "INSERT INTO phase_receipts VALUES(?,?,?)",
            (phase, f"phase:{phase}", utc_now()),
        )
    events.append(
        "fake_campaign_complete",
        {
            "roles": 180,
            "attempted_columns": 4000,
            "validated_columns": 2500,
            "matrix_receipt_sha256": sha256_file(matrix_receipt),
            "score_receipt_sha256": sha256_file(score_receipt),
        },
    )
    return verify_campaign(run_root, run_id)
