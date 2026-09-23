from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nomad_feature_hunt.ledger import HashChain, atomic_json, sha256_file, utc_now

from .budget import BudgetAccount
from .evidence import validate_evidence_coverage
from .constants import (
    ATLAS_TARGET_WINNERS,
    ATLAS_DEFINITION_COUNT,
    ATLAS_WIDTH,
    CAMPAIGN_PHASES,
    DOMAIN_IDS,
    EXISTING_809_CONTROLS,
    EXPECTED_CANARY_ROLES,
    EXPECTED_JNOCCIO_ROLES,
    MAX_COST_USD,
    MAX_ATTEMPTS_PER_ROLE,
    MAX_WALL_SECONDS,
    MIN_ATTEMPTED_FEATURES,
    MIN_BASE_FAMILIES,
    MIN_POSITIVE_DOMAINS_PER_TARGET,
    MIN_POSITIVE_FAMILIES_PER_TARGET,
    MIN_VALIDATED_FEATURES,
    MIN_VALIDATED_PER_DOMAIN,
    TARGETS,
)
from .scoring import choose_with_tie_band
from .state import CampaignDB


def _artifact_hashes(run_root: Path) -> dict[str, str]:
    excluded = {
        (run_root / "final_hashes/manifest.json").resolve(),
        (run_root / "campaign.sqlite3").resolve(),
    }
    files = [
        path
        for path in run_root.rglob("*")
        if path.is_file()
        and path.resolve() not in excluded
        and not path.name.endswith(("-wal", "-shm"))
    ]
    return {str(path.relative_to(run_root)): sha256_file(path) for path in sorted(files)}


def verify_hash_manifest(run_root: Path) -> tuple[bool, list[str]]:
    """Independently recompute every promoted manifest hash and artifact path."""

    path = run_root / "final_hashes/manifest.json"
    if not path.exists():
        return False, ["final hash manifest is missing"]
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return False, [f"final hash manifest is invalid JSON: {error}"]
    expected = manifest.get("files")
    if not isinstance(expected, dict):
        return False, ["final hash manifest has no files object"]
    actual = _artifact_hashes(run_root)
    errors: list[str] = []
    for relative_path, expected_hash in expected.items():
        if relative_path not in actual:
            errors.append(f"manifest artifact is missing: {relative_path}")
        elif actual[relative_path] != expected_hash:
            errors.append(f"artifact hash differs: {relative_path}")
    unexpected = sorted(set(actual) - set(expected))
    if unexpected:
        errors.append(f"unmanifested artifacts: {unexpected[:5]}")
    return not errors, errors


def verify_campaign(run_root: Path, run_id: str) -> dict[str, Any]:
    db = CampaignDB(run_root / "campaign.sqlite3")
    budget = BudgetAccount(run_root / "budget.sqlite3")
    missing: list[str] = []

    campaign = db.one("SELECT * FROM campaign WHERE run_id=?", (run_id,))
    if campaign is None:
        return {"run_id": run_id, "complete": False, "missing": ["campaign preflight"]}
    completed_phases = {
        str(row["phase"]) for row in db.all("SELECT phase FROM phase_receipts")
    }
    absent_phases = [phase for phase in CAMPAIGN_PHASES if phase not in completed_phases]
    if absent_phases:
        missing.append(f"complete phase receipt chain: {absent_phases}")
    damaged_receipts: list[str] = []
    for row in db.all("SELECT receipt_id,path,sha256 FROM receipts"):
        path = Path(str(row["path"]))
        if not path.exists() or sha256_file(path) != row["sha256"]:
            damaged_receipts.append(str(row["receipt_id"]))
    if damaged_receipts:
        missing.append(f"receipt file hashes: {damaged_receipts[:5]}")
    damaged_attempts: list[str] = []
    for row in db.all(
        "SELECT role_id,attempt,raw_result_path,raw_result_sha256 FROM attempts "
        "WHERE raw_result_path IS NOT NULL"
    ):
        path = Path(str(row["raw_result_path"]))
        if (
            not path.exists()
            or not row["raw_result_sha256"]
            or sha256_file(path) != row["raw_result_sha256"]
        ):
            damaged_attempts.append(f"{row['role_id']}:{row['attempt']}")
    if damaged_attempts:
        missing.append(f"raw Jnoccio result hashes: {damaged_attempts[:5]}")
    if campaign["started_at"]:
        started = datetime.fromisoformat(str(campaign["started_at"]).replace("Z", "+00:00"))
        if (datetime.now(timezone.utc) - started).total_seconds() > MAX_WALL_SECONDS:
            missing.append("campaign completed inside the 72-hour wall-clock ceiling")

    roles_total = int(db.one("SELECT COUNT(*) n FROM roles")["n"])
    roles_complete = int(db.one("SELECT COUNT(*) n FROM roles WHERE status='complete'")["n"])
    if roles_total != EXPECTED_JNOCCIO_ROLES or roles_complete != EXPECTED_JNOCCIO_ROLES:
        missing.append("exactly 180 stable, valid Jnoccio roles")
    valid_role_receipts = int(
        db.one(
            "SELECT COUNT(DISTINCT role_id) n FROM receipts "
            "WHERE kind='jnoccio' AND valid=1"
        )["n"]
    )
    if valid_role_receipts != EXPECTED_JNOCCIO_ROLES:
        missing.append("exactly 180 valid role provenance receipts")
    first_pass_canaries = int(
        db.one(
            "SELECT COUNT(*) n FROM attempts a JOIN roles r ON r.role_id=a.role_id "
            "WHERE r.role_class='evidence_curator' AND a.attempt=0 AND a.valid=1"
        )["n"]
    )
    complete_canaries = int(
        db.one(
            "SELECT COUNT(*) n FROM roles WHERE role_class='evidence_curator' AND status='complete'"
        )["n"]
    )
    if first_pass_canaries < 9 or complete_canaries != EXPECTED_CANARY_ROLES:
        missing.append("schema canary: at least 9/10 first-pass and all 10 after retry")

    missing_router = int(
        db.one(
            "SELECT COUNT(*) n FROM attempts WHERE valid=1 AND router_metadata_present<>1"
        )["n"]
    )
    if missing_router:
        missing.append("router metadata presence for every valid attempt")
    over_attempted = int(
        db.one(
            "SELECT COUNT(*) n FROM (SELECT role_id,COUNT(*) attempts FROM attempts "
            "GROUP BY role_id HAVING attempts>?)",
            (MAX_ATTEMPTS_PER_ROLE,),
        )["n"]
    )
    if over_attempted:
        missing.append("one initial Jnoccio attempt and at most one retry per role")

    attempted = int(
        db.one(
            "SELECT COUNT(*) n FROM columns WHERE status IN ('validated','quarantined')"
        )["n"]
    )
    validated = int(db.one("SELECT COUNT(*) n FROM columns WHERE status='validated'")["n"])
    if attempted < MIN_ATTEMPTED_FEATURES:
        missing.append("at least 4,000 actually attempted executable columns")
    if validated < MIN_VALIDATED_FEATURES:
        missing.append("at least 2,500 validated novel columns")
    domain_counts = {
        domain: int(
            db.one(
                "SELECT COUNT(*) n FROM columns WHERE domain=? AND status='validated'",
                (domain,),
            )["n"]
        )
        for domain in sorted(DOMAIN_IDS)
    }
    underrepresented = [
        domain for domain, count in domain_counts.items() if count < MIN_VALIDATED_PER_DOMAIN
    ]
    if underrepresented:
        missing.append(f"150 validated columns per domain: {underrepresented}")
    families = int(
        db.one(
            "SELECT COUNT(DISTINCT domain || ':' || family_slug) n "
            "FROM columns WHERE status='validated'"
        )["n"]
    )
    if families < MIN_BASE_FAMILIES:
        missing.append("at least 120 distinct validated base families")
    equation_counts: defaultdict[str, int] = defaultdict(int)
    for row in db.all(
        "SELECT registry_json FROM columns WHERE status IN ('validated','quarantined')"
    ):
        registry = json.loads(row["registry_json"])
        equation_counts[str(registry.get("base_equation_id", ""))] += 1
    overexpanded = [key for key, count in equation_counts.items() if count > 25]
    if overexpanded:
        missing.append(f"25-column base-equation expansion cap: {overexpanded[:3]}")

    atlas_receipt = run_root / "inputs/atlas/staging_receipt.json"
    novelty_receipt = run_root / "novelty/atlas_registry.receipt.json"
    controller_manifest_path = run_root / "inputs/controller/manifest.json"
    if not controller_manifest_path.exists():
        missing.append("frozen trusted controller and generator sources")
    else:
        controller_manifest = json.loads(
            controller_manifest_path.read_text(encoding="utf-8")
        )
        controller_hash_errors = [
            logical_name
            for logical_name, record in controller_manifest.get("files", {}).items()
            if not (run_root / "inputs/controller" / logical_name).exists()
            or sha256_file(run_root / "inputs/controller" / logical_name)
            != record.get("sha256")
        ]
        if controller_hash_errors:
            missing.append(
                f"frozen controller source hashes: {controller_hash_errors[:5]}"
            )
    if not atlas_receipt.exists() or not novelty_receipt.exists():
        missing.append("frozen Atlas staging and novelty-registry receipts")
    else:
        atlas_staging = json.loads(atlas_receipt.read_text(encoding="utf-8"))
        atlas_hash_errors = [
            name
            for name, digest in atlas_staging.get("files", {}).items()
            if not (run_root / "inputs/atlas" / name).exists()
            or sha256_file(run_root / "inputs/atlas" / name) != digest
        ]
        if atlas_hash_errors:
            missing.append(f"frozen Atlas file hashes: {atlas_hash_errors[:5]}")
        novelty = json.loads(novelty_receipt.read_text(encoding="utf-8"))
        if (
            novelty.get("columns") != ATLAS_WIDTH
            or novelty.get("definitions") != ATLAS_DEFINITION_COUNT
            or novelty.get("numeric_signatures") != ATLAS_WIDTH
            or novelty.get("formula_fingerprints") != ATLAS_WIDTH
            or novelty.get("semantic_fingerprints") != ATLAS_WIDTH
            or novelty.get("existing_809") != 809
        ):
            missing.append("complete 9,969-column/9,160-definition Atlas novelty seed")
    evidence_receipt = db.one(
        "SELECT payload_json FROM receipts WHERE receipt_id='phase:evidence' AND valid=1"
    )
    if evidence_receipt is None or json.loads(evidence_receipt["payload_json"]).get("sources", 0) < 250:
        missing.append("at least 250 relevant, coverage-validated evidence sources")
    evidence_path = run_root / "evidence/evidence.json"
    if not evidence_path.exists():
        missing.append("frozen deduplicated evidence artifact")
    else:
        evidence_errors = validate_evidence_coverage(
            json.loads(evidence_path.read_text(encoding="utf-8"))
        )
        if evidence_errors:
            missing.append("evidence domain coverage: " + "; ".join(evidence_errors))
    idea_seed_path = run_root / "memory/v1_seeds/idea_seeds.json"
    negative_memory_path = run_root / "memory/v1_seeds/negative_memory.json"
    if not idea_seed_path.exists() or not negative_memory_path.exists():
        missing.append("v1 idea-seed and negative-memory imports")
    else:
        idea_seeds = json.loads(idea_seed_path.read_text(encoding="utf-8"))
        negative_memory = json.loads(negative_memory_path.read_text(encoding="utf-8"))
        if (
            len(idea_seeds) != 74
            or not negative_memory
            or any(item.get("v2_status") != "unverified_idea_seed" for item in idea_seeds)
        ):
            missing.append("exactly 74 unverified v1 ideas plus invalid-output negative memory")
    smoke = run_root / "receipts/sandbox/precompile-gate.json"
    if not smoke.exists():
        missing.append("trusted-kernel and custom-plugin 16-structure precompile smoke gate")
    else:
        smoke_payload = json.loads(smoke.read_text(encoding="utf-8"))
        if (
            smoke_payload.get("trusted_toy_kernels") != 10
            or smoke_payload.get("trusted_structures") != 16
            or smoke_payload.get("trusted_invariances") is not True
            or smoke_payload.get("custom_toy") is not True
            or smoke_payload.get("custom_structures") != 16
            or smoke_payload.get("custom_invariances") is not True
        ):
            missing.append("toy plus trusted/custom 16-structure invariance smoke contract")

    discovery: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in db.all(
        "SELECT target,family_slug,domain,nonoverlap_group FROM scores "
        "WHERE stage='discovery' AND discovery_positive=1"
    ):
        discovery[str(row["target"])].append(dict(row))
    for target in TARGETS:
        rows = discovery[target]
        families_for_target = {
            f"{row['domain']}:{row['family_slug']}" for row in rows
        }
        groups = {str(row["nonoverlap_group"]) for row in rows}
        domains = {str(row["domain"]) for row in rows}
        if (
            len(families_for_target) < MIN_POSITIVE_FAMILIES_PER_TARGET
            or len(groups) < MIN_POSITIVE_FAMILIES_PER_TARGET
            or len(domains) < MIN_POSITIVE_DOMAINS_PER_TARGET
        ):
            missing.append(
                f"{target}: ten nonoverlapping discovery-positive families across three domains"
            )

    confirmation: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in db.all("SELECT target,payload_json FROM scores WHERE stage='confirmation'"):
        confirmation[str(row["target"])].append(json.loads(row["payload_json"]))
    winners: dict[str, dict[str, Any]] = {}
    for target in TARGETS:
        rows = confirmation[target]
        if not rows:
            missing.append(f"{target}: sealed shuffled five-fold confirmation receipt")
            continue
        winner = choose_with_tie_band(rows)
        winners[target] = winner
        rmsle = float(winner["rmsle"])
        if int(winner.get("folds", 0)) != 5 or int(winner.get("trees", 0)) != 400:
            missing.append(f"{target}: required 5-fold/400-tree confirmation protocol")
        if not (rmsle < ATLAS_TARGET_WINNERS[target] and rmsle < EXISTING_809_CONTROLS[target]):
            missing.append(f"{target}: positive RMSLE lift over both frozen controls")

    matrix_receipts = int(
        db.one("SELECT COUNT(*) n FROM receipts WHERE kind='matrix' AND valid=1")["n"]
    )
    score_receipts = int(
        db.one("SELECT COUNT(*) n FROM receipts WHERE kind='score' AND valid=1")["n"]
    )
    if not matrix_receipts or not score_receipts:
        missing.append("real matrix and score receipts before analysts and judges")
    score_artifact_errors: list[str] = []
    score_artifacts = {
        "score:discovery": {
            "controller_results_sha256": run_root
            / "scoring/discovery/controller_results.json",
            "adaptive_feedback_sha256": run_root
            / "scoring/discovery/adaptive_feedback.json",
        },
        "score:confirmation": {
            "preregistration_sha256": run_root
            / "scoring/confirmation/preregistration.json",
            "controller_results_sha256": run_root
            / "scoring/confirmation/controller_results.json",
        },
    }
    for receipt_id, artifacts in score_artifacts.items():
        row = db.one(
            "SELECT payload_json FROM receipts WHERE receipt_id=? AND valid=1",
            (receipt_id,),
        )
        if row is None:
            continue
        payload = json.loads(row["payload_json"])
        for key, path in artifacts.items():
            if not path.exists() or sha256_file(path) != payload.get(key):
                score_artifact_errors.append(f"{receipt_id}:{key}")
    if score_artifact_errors:
        missing.append(f"score artifact hashes: {score_artifact_errors}")
    damaged_matrices: list[str] = []
    for row in db.all(
        "SELECT m.matrix_id,m.train_path,m.test_path,r.payload_json FROM matrices m "
        "JOIN receipts r ON r.receipt_id=m.receipt_id WHERE m.valid=1"
    ):
        payload = json.loads(row["payload_json"])
        for key, path_key in (("train_sha256", "train_path"), ("test_sha256", "test_path")):
            if key not in payload:
                continue
            path = Path(str(row[path_key]))
            if not path.exists() or sha256_file(path) != payload[key]:
                damaged_matrices.append(f"{row['matrix_id']}:{path_key}")
    if damaged_matrices:
        missing.append(f"validated matrix hashes: {damaged_matrices[:5]}")
    matrix_ids = {str(row["matrix_id"]) for row in db.all("SELECT matrix_id FROM matrices")}
    unbound_columns: list[str] = []
    for row in db.all(
        "SELECT feature_id,registry_json FROM columns "
        "WHERE status IN ('validated','quarantined')"
    ):
        registry = json.loads(row["registry_json"])
        spec_id = str(registry.get("base_equation_id", "")).removeprefix("v2.")
        if spec_id not in matrix_ids:
            unbound_columns.append(str(row["feature_id"]))
    if unbound_columns:
        missing.append(f"executed columns bound to full matrix receipts: {unbound_columns[:5]}")
    blind_judgments = int(
        db.one(
            "SELECT COUNT(*) n FROM judgments j JOIN roles r ON r.role_id=j.role_id "
            "WHERE r.role_class='blind_judge'"
        )["n"]
    )
    if blind_judgments != 4:
        missing.append("four receipt-bound blind judgments")
    analyst_reports = int(
        db.one(
            "SELECT COUNT(*) n FROM judgments j JOIN roles r ON r.role_id=j.role_id "
            "WHERE r.role_class='experimental_analyst'"
        )["n"]
    )
    if analyst_reports != 4:
        missing.append("four receipt-bound experimental analyses")
    judgment_files = list((run_root / "judgments").glob("*.json"))
    if len(judgment_files) != 8:
        missing.append("frozen artifacts for all four analyses and four blind judgments")
    memory_curators = [
        row
        for row in db.all("SELECT role_id FROM roles WHERE role_class='memory_curator'")
        if (run_root / f"memory/{row['role_id']}.json").exists()
    ]
    if len(memory_curators) != 2:
        missing.append("two receipt-bound memory curator classifications")

    budget_summary = budget.summary()
    if budget_summary.debited_usd + budget_summary.reserved_usd > MAX_COST_USD:
        missing.append("conservative accounting below the $1,000 ceiling")

    chain = HashChain(run_root / "events.jsonl")
    chain_valid, chain_error = chain.verify()
    if not chain_valid:
        missing.append(f"valid hash-chained event ledger: {chain_error}")

    outside_paths: list[str] = []
    for table, columns in (
        ("receipts", ("path",)),
        ("matrices", ("train_path", "test_path")),
        ("attempts", ("raw_result_path",)),
    ):
        for column in columns:
            for row in db.all(f"SELECT {column} value FROM {table} WHERE {column} IS NOT NULL"):
                path = Path(str(row["value"])).resolve()
                if not path.is_relative_to(run_root.resolve()):
                    outside_paths.append(str(path))
    if outside_paths:
        missing.append(f"all feature artifacts below the v2 run inbox: {outside_paths[:3]}")

    report = {
        "run_id": run_id,
        "verified_at": utc_now(),
        "complete": not missing,
        "missing": missing,
        "counts": {
            "roles": roles_total,
            "valid_roles": roles_complete,
            "attempted_columns": attempted,
            "validated_columns": validated,
            "validated_families": families,
            "matrix_receipts": matrix_receipts,
            "score_receipts": score_receipts,
        },
        "validated_by_domain": domain_counts,
        "confirmation_winners": winners,
        "budget": budget_summary.__dict__,
        "hash_chain_valid": chain_valid,
        "declarations": {
            "labeled_test_access": False,
            "automatic_merge": False,
            "padding_counted": False,
            "uncomputed_features_counted": False,
            "jailgun_required": False,
        },
    }
    atomic_json(run_root / "verification.json", report)
    if report["complete"]:
        promotion = run_root / "promotion"
        promotion.mkdir(parents=True, exist_ok=True)
        promoted_paths = [
            path
            for directory in (
                "inputs/controller", "evidence", "novelty", "families", "specs",
                "plugins", "registry", "matrices/validated", "scoring", "judgments",
                "memory", "receipts",
            )
            for path in (run_root / directory).rglob("*")
            if path.is_file()
        ]
        artifact_manifest = {
            str(path.relative_to(run_root)): sha256_file(path) for path in sorted(promoted_paths)
        }
        atomic_json(
            promotion / "artifact_manifest.json",
            {"run_id": run_id, "artifacts": artifact_manifest},
        )
        integration = {
            "run_id": run_id,
            "delivery": "promotion-inbox-only",
            "nomad_crystal360_modified": False,
            "validated_columns": validated,
            "families": families,
            "confirmation_winners": winners,
            "test_labels_used": False,
        }
        atomic_json(promotion / "integration_manifest.json", integration)
        hashes = _artifact_hashes(run_root)
        atomic_json(run_root / "final_hashes/manifest.json", {"run_id": run_id, "files": hashes})
    return report
