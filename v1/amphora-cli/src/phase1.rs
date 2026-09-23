use amphora_core::{
    canonicalize, ModulePhase1BundleV1, ModulePhase1EvaluationReceiptV1,
    ModulePhase1MovementEventV1, ModulePhase1ReviewReceiptV1, Phase1ModuleStatusV1,
    Phase1PortfolioStatusV1, ScientificOutcomeV1, TrustStore, MODULE_PHASE1_BUNDLE_SCHEMA,
    MODULE_PHASE1_EVALUATION_RECEIPT_SCHEMA, MODULE_PHASE1_MOVEMENT_EVENT_SCHEMA,
};
use anyhow::{anyhow, bail, Context, Result};
use clap::{Args, Subcommand};
use ed25519_dalek::SigningKey;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
use std::path::{Component, Path, PathBuf};

const MANIFEST_PATH: &str = "module-manifest.json";
const PREREGISTRATION_PATH: &str = "config/program/coatings-90-day-preregistration.v2.json";
const TRUST_STORE_PATH: &str = "config/phase1-trust-store.v1.json";
const LOCK_NAMES: [&str; 9] = [
    "dataset",
    "split",
    "estimator",
    "metric",
    "baseline",
    "threshold",
    "uncertainty",
    "applicability",
    "stop-rule",
];

#[derive(Debug, Args)]
pub struct Phase1Args {
    #[command(subcommand)]
    command: Phase1Command,
}

#[derive(Debug, Subcommand)]
enum Phase1Command {
    Prepare {
        #[arg(long)]
        module: String,
    },
    Evaluate {
        #[arg(long)]
        module: String,
    },
    Review {
        #[arg(long)]
        module: String,
        #[arg(long)]
        review: PathBuf,
    },
    Verify {
        #[arg(long)]
        module: String,
    },
    Promote {
        #[arg(long)]
        module: String,
    },
    Status {
        #[arg(long)]
        all: bool,
        #[arg(long)]
        write_report: bool,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct TrustStoreFileV1 {
    schema: String,
    authorization_status: String,
    keys: Vec<TrustKeyV1>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct TrustKeyV1 {
    key_id: String,
    algorithm: String,
    role: String,
    public_key_hex: String,
    phase1_authorized: bool,
    development: bool,
    revoked: bool,
}

struct LoadedTrust {
    trust: TrustStore,
    roles: BTreeMap<String, String>,
}

pub fn run(root: &Path, args: Phase1Args) -> Result<()> {
    let value = match args.command {
        Phase1Command::Prepare { module } => prepare(root, &module)?,
        Phase1Command::Evaluate { module } => evaluate(root, &module)?,
        Phase1Command::Review { module, review } => import_review(root, &module, &review)?,
        Phase1Command::Verify { module } => serde_json::to_value(verify_module(root, &module)?)?,
        Phase1Command::Promote { module } => promote(root, &module)?,
        Phase1Command::Status { all, write_report } => {
            if !all {
                bail!("portfolio phase1 status requires --all");
            }
            let phase0 = crate::phase0::portfolio_status(root)?;
            let status = portfolio_status_from_phase0(root, &phase0)?;
            if write_report {
                write_json_generated(
                    &root.join("config/program/phase1-portfolio-status.v1.json"),
                    &serde_json::to_value(&status)?,
                )?;
                crate::dashboard::write(root, &phase0, &status)?;
            }
            serde_json::to_value(status)?
        }
    };
    println!("{}", serde_json::to_string(&value)?);
    Ok(())
}

fn prepare(root: &Path, module: &str) -> Result<Value> {
    let phase0 = current_phase0(root, module)?;
    let phase0_event_id = phase0
        .get("movement_event")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("a current valid Phase-0 movement is required"))?;
    let (phase0_path, phase0_hash) = phase0_movement(root, module, phase0_event_id)?;
    let prereg_path = root.join(PREREGISTRATION_PATH);
    let prereg = read_json(&prereg_path)?;
    let day_0 = prereg.get("day_0").and_then(Value::as_str).ok_or_else(|| {
        anyhow!("Phase-1 preregistration is not externally countersigned; day 0 is unset")
    })?;
    if prereg
        .get("counterparty_signature")
        .is_none_or(Value::is_null)
        || !prereg
            .get("phase1_attempt_modules")
            .and_then(Value::as_array)
            .is_some_and(|modules| modules.iter().any(|value| value.as_str() == Some(module)))
    {
        bail!("module is not covered by a countersigned Phase-1 preregistration");
    }
    let module_dir = checked_module(root, module)?;
    let locks_dir = module_dir.join("evidence/phase1/locks");
    let mut hashes = BTreeMap::new();
    let mut parents = BTreeMap::from([
        (
            format!("{module}/{}", phase0_path.to_string_lossy()),
            phase0_hash.clone(),
        ),
        (PREREGISTRATION_PATH.into(), file_hash(&prereg_path)?),
    ]);
    for name in LOCK_NAMES {
        let path = locks_dir.join(format!("{name}.v1.json"));
        let value = read_json(&path)
            .with_context(|| format!("Phase-1 pre-outcome lock is absent: {name}"))?;
        if value.get("pre_outcome_locked").and_then(Value::as_bool) != Some(true) {
            bail!("Phase-1 lock is not marked pre-outcome: {name}");
        }
        let hash = file_hash(&path)?;
        hashes.insert(name, hash.clone());
        parents.insert(format!("evidence/phase1/locks/{name}.v1.json"), hash);
    }
    let dataset = read_json(&locks_dir.join("dataset.v1.json"))?;
    let baseline = read_json(&locks_dir.join("baseline.v1.json"))?;
    let claim_locks = read_json(&module_dir.join("ip/claim-contract.v1.json"))?
        .get("claim_locks")
        .cloned()
        .and_then(|value| serde_json::from_value(value).ok())
        .ok_or_else(|| anyhow!("Phase-0 claim locks are absent"))?;
    let bundle = ModulePhase1BundleV1 {
        schema: MODULE_PHASE1_BUNDLE_SCHEMA.into(),
        module_id: module.into(),
        phase0_event_id: phase0_event_id.into(),
        phase0_movement_hash: phase0_hash,
        preregistration_hash: file_hash(&prereg_path)?,
        preregistration_countersigned_on: day_0.into(),
        dataset_lock_hash: hashes["dataset"].clone(),
        split_lock_hash: hashes["split"].clone(),
        estimator_lock_hash: hashes["estimator"].clone(),
        metric_lock_hash: hashes["metric"].clone(),
        baseline_lock_hash: hashes["baseline"].clone(),
        threshold_lock_hash: hashes["threshold"].clone(),
        uncertainty_lock_hash: hashes["uncertainty"].clone(),
        applicability_lock_hash: hashes["applicability"].clone(),
        stop_rule_lock_hash: hashes["stop-rule"].clone(),
        parent_hashes: parents,
        independent_external_evidence: dataset
            .get("independent_external_evidence")
            .and_then(Value::as_bool)
            == Some(true),
        named_best_reproducible_baseline: baseline
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .into(),
        pre_outcome_locked: true,
        clean_environment_replay_count: 2,
        scientific_readiness_ceiling: "INDEPENDENTLY_VALIDATED".into(),
        decision_use_ceiling: "AUDIT_ONLY".into(),
        ranking_eligible: false,
        claim_locks,
    };
    bundle.validate()?;
    let path = module_dir.join("evidence/phase1/bundle.v1.json");
    write_json_immutable(&path, &bundle)?;
    Ok(json!({
        "schema": "amphora.module-phase1-preparation-result.v1",
        "module_id": module,
        "bundle_hash": file_hash(&path)?,
        "day_0": day_0,
        "authority_change": false,
    }))
}

fn evaluate(root: &Path, module: &str) -> Result<Value> {
    let module_dir = checked_module(root, module)?;
    let bundle_path = module_dir.join("evidence/phase1/bundle.v1.json");
    let bundle: ModulePhase1BundleV1 = read_typed(&bundle_path)?;
    bundle.validate()?;
    verify_bundle_parents(root, &module_dir, &bundle)?;
    let key_id = std::env::var("AMPHORA_PHASE1_EVALUATOR_KEY_ID")
        .context("AMPHORA_PHASE1_EVALUATOR_KEY_ID is required")?;
    let key_path = std::env::var("AMPHORA_PHASE1_EVALUATOR_KEY")
        .context("AMPHORA_PHASE1_EVALUATOR_KEY must name an external 32-byte private key")?;
    let key = load_signing_key(root, Path::new(&key_path))?;
    let trust = load_trust(root)?;
    verify_signing_identity(&trust, &key_id, "PHASE1_EVALUATOR", &key)?;
    let replay_one = module_dir.join("evidence/phase1/evaluation/replay-1.json");
    let replay_two = module_dir.join("evidence/phase1/evaluation/replay-2.json");
    let replay_hashes = vec![file_hash(&replay_one)?, file_hash(&replay_two)?];
    let result: Value = read_json(&replay_one)?;
    if fs::read(&replay_one)? != fs::read(&replay_two)? {
        bail!("Phase-1 clean-environment replays are not byte-identical");
    }
    let outcome = match result.get("scientific_outcome").and_then(Value::as_str) {
        Some("PASSED") => ScientificOutcomeV1::Passed,
        Some("FAILED") => ScientificOutcomeV1::Failed,
        _ => bail!("Phase-1 result must report PASSED or FAILED"),
    };
    let gate = |name: &str| result.get(name).and_then(Value::as_bool) == Some(true);
    let failed_gates = result
        .get("failed_gates")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_str)
        .map(str::to_owned)
        .collect::<Vec<_>>();
    let retained = result
        .get("retained_failure_results")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_str)
        .map(str::to_owned)
        .collect::<Vec<_>>();
    let phase1_eligible = outcome == ScientificOutcomeV1::Passed
        && [
            "audit_execution_passed",
            "independent_external_evidence_verified",
            "baseline_reproduced",
            "uncertainty_intervals_complete",
            "subgroup_checks_complete",
            "coverage_checks_complete",
            "applicability_checks_complete",
            "stop_rule_preserved",
        ]
        .iter()
        .all(|name| gate(name))
        && failed_gates.is_empty();
    let mut receipt = ModulePhase1EvaluationReceiptV1 {
        schema: MODULE_PHASE1_EVALUATION_RECEIPT_SCHEMA.into(),
        receipt_id: format!("phase1-evaluation-{}", file_hash(&replay_one)?),
        module_id: module.into(),
        bundle_hash: file_hash(&bundle_path)?,
        evaluator_key_id: key_id.clone(),
        audit_execution_passed: gate("audit_execution_passed"),
        independent_external_evidence_verified: gate("independent_external_evidence_verified"),
        baseline_reproduced: gate("baseline_reproduced"),
        uncertainty_intervals_complete: gate("uncertainty_intervals_complete"),
        subgroup_checks_complete: gate("subgroup_checks_complete"),
        coverage_checks_complete: gate("coverage_checks_complete"),
        applicability_checks_complete: gate("applicability_checks_complete"),
        stop_rule_preserved: gate("stop_rule_preserved"),
        clean_environment_replay_hashes: replay_hashes,
        scientific_outcome: outcome,
        phase1_eligible,
        failed_gates,
        retained_failure_results: retained,
        metrics: result
            .get("metrics")
            .cloned()
            .and_then(|value| serde_json::from_value(value).ok())
            .unwrap_or_default(),
        signature: None,
    };
    receipt.sign(&key_id, &key)?;
    let output = module_dir.join("evidence/phase1/receipts/evaluation.v1.dsse.json");
    write_json_immutable(&output, &receipt)?;
    Ok(json!({
        "schema": "amphora.module-phase1-evaluation-result.v1",
        "module_id": module,
        "phase1_eligible": receipt.phase1_eligible,
        "scientific_outcome": receipt.scientific_outcome,
        "receipt_hash": file_hash(&output)?,
    }))
}

fn import_review(root: &Path, module: &str, supplied: &Path) -> Result<Value> {
    let module_dir = checked_module(root, module)?;
    let supplied = rooted(root, supplied)?;
    let review: ModulePhase1ReviewReceiptV1 = read_typed(&supplied)?;
    let trust = load_trust(root)?;
    let reviewer = review.verify_signature(&trust.trust)?;
    if trust.roles.get(&reviewer).map(String::as_str) != Some("PHASE1_INDEPENDENT_REVIEWER")
        || review.module_id != module
    {
        bail!("Phase-1 review signer role or module binding is invalid");
    }
    let bundle_path = module_dir.join("evidence/phase1/bundle.v1.json");
    let evaluation_path = module_dir.join("evidence/phase1/receipts/evaluation.v1.dsse.json");
    let evaluation: ModulePhase1EvaluationReceiptV1 = read_typed(&evaluation_path)?;
    let evaluator = evaluation.verify_signature(&trust.trust)?;
    if trust.roles.get(&evaluator).map(String::as_str) != Some("PHASE1_EVALUATOR")
        || review.evaluator_key_id != evaluator
        || review.bundle_hash != file_hash(&bundle_path)?
        || review.evaluation_receipt_hash != file_hash(&evaluation_path)?
        || !review.accepted_for_phase1
    {
        bail!("Phase-1 review does not bind and accept the current evaluation");
    }
    let destination = module_dir.join("evidence/phase1/receipts/independent-review.v1.dsse.json");
    write_bytes_immutable(&destination, &fs::read(supplied)?)?;
    Ok(json!({
        "schema": "amphora.module-phase1-review-import.v1",
        "module_id": module,
        "reviewer_key_id": reviewer,
        "review_hash": file_hash(&destination)?,
    }))
}

fn promote(root: &Path, module: &str) -> Result<Value> {
    let status = verify_module(root, module)?;
    if status.phase != "PHASE_0"
        || !status.prepared
        || !status.evaluation_signed
        || !status.review_signed
        || !status.failed_gates.is_empty()
    {
        bail!(
            "module is not promotable to Phase 1: {}",
            status.failed_gates.join("; ")
        );
    }
    let module_dir = checked_module(root, module)?;
    let bundle_path = module_dir.join("evidence/phase1/bundle.v1.json");
    let evaluation_path = module_dir.join("evidence/phase1/receipts/evaluation.v1.dsse.json");
    let review_path = module_dir.join("evidence/phase1/receipts/independent-review.v1.dsse.json");
    let bundle: ModulePhase1BundleV1 = read_typed(&bundle_path)?;
    let evaluation: ModulePhase1EvaluationReceiptV1 = read_typed(&evaluation_path)?;
    let review: ModulePhase1ReviewReceiptV1 = read_typed(&review_path)?;
    if !evaluation.phase1_eligible || !review.accepted_for_phase1 {
        bail!("failed Phase-1 attempt leaves Phase-0 authority unchanged");
    }
    let applicability = read_json(&module_dir.join("evidence/phase1/locks/applicability.v1.json"))?
        .get("domain")
        .cloned()
        .and_then(|value| serde_json::from_value(value).ok())
        .filter(|values: &Vec<String>| !values.is_empty())
        .ok_or_else(|| anyhow!("Phase-1 applicability domain is absent"))?;
    let bundle_hash = file_hash(&bundle_path)?;
    let evaluation_hash = file_hash(&evaluation_path)?;
    let review_hash = file_hash(&review_path)?;
    let mut event = ModulePhase1MovementEventV1 {
        schema: MODULE_PHASE1_MOVEMENT_EVENT_SCHEMA.into(),
        event_id: String::new(),
        module_id: module.into(),
        previous_phase: "PHASE_0".into(),
        current_phase: "PHASE_1".into(),
        effective_status_change: "PHASE_0->PHASE_1".into(),
        phase0_event_id: bundle.phase0_event_id.clone(),
        phase0_movement_hash: bundle.phase0_movement_hash.clone(),
        bundle_hash: bundle_hash.clone(),
        evaluation_receipt_hash: evaluation_hash.clone(),
        review_receipt_hash: review_hash.clone(),
        parent_hashes: BTreeMap::from([
            (
                "phase0_movement".into(),
                bundle.phase0_movement_hash.clone(),
            ),
            ("phase1_bundle".into(), bundle_hash),
            ("phase1_evaluation".into(), evaluation_hash),
            ("phase1_review".into(), review_hash),
        ]),
        evaluator_key_id: evaluation.evaluator_key_id,
        reviewer_key_id: review.reviewer_key_id,
        scientific_readiness: "INDEPENDENTLY_VALIDATED".into(),
        decision_use_ceiling: "AUDIT_ONLY".into(),
        ranking_eligible: false,
        applicability_domain: applicability,
        claim_locks: bundle.claim_locks,
    };
    event.bind_event_id()?;
    event.validate()?;
    let digest = event.event_id.trim_start_matches("phase1-movement-");
    let event_path = module_dir
        .join("movement/phase1/events")
        .join(format!("{digest}.json"));
    write_json_immutable(&event_path, &event)?;
    let ledger_path = module_dir.join("movement/phase1/ledger.v1.json");
    if ledger_path.exists() {
        bail!("exactly one Phase-1 movement is permitted; ledger already exists");
    }
    write_json_immutable(
        &ledger_path,
        &json!({
            "schema": "amphora.module-phase1-movement-ledger.v1",
            "module_id": module,
            "events": [{
                "event_id": event.event_id,
                "path": format!("events/{digest}.json"),
                "sha256": file_hash(&event_path)?,
            }],
        }),
    )?;
    Ok(json!({
        "schema": "amphora.module-phase1-promotion-result.v1",
        "module_id": module,
        "phase": "PHASE_1",
        "scientific_readiness": "INDEPENDENTLY_VALIDATED",
        "ranking_eligible": false,
        "event_id": event.event_id,
    }))
}

fn verify_module(root: &Path, module: &str) -> Result<Phase1ModuleStatusV1> {
    let phase0 = current_phase0(root, module)?;
    verify_module_with_phase0(root, module, &phase0)
}

fn verify_module_with_phase0(
    root: &Path,
    module: &str,
    phase0: &Value,
) -> Result<Phase1ModuleStatusV1> {
    let phase0_phase = phase0
        .get("phase")
        .and_then(Value::as_str)
        .unwrap_or("PRE_PHASE_0");
    let phase0_event = phase0
        .get("movement_event")
        .and_then(Value::as_str)
        .map(str::to_owned);
    let mut status = Phase1ModuleStatusV1 {
        module_id: module.into(),
        phase: phase0_phase.into(),
        scientific_readiness: phase0
            .get("scientific_readiness")
            .and_then(Value::as_str)
            .unwrap_or("UNVALIDATED")
            .into(),
        decision_use_ceiling: "AUDIT_ONLY".into(),
        ranking_eligible: false,
        phase0_event_id: phase0_event.clone(),
        phase1_event_id: None,
        prepared: false,
        evaluation_signed: false,
        review_signed: false,
        failed_gates: Vec::new(),
    };
    if phase0_phase != "PHASE_0" {
        status
            .failed_gates
            .push("CURRENT_PHASE0_MOVEMENT_REQUIRED".into());
        return Ok(status);
    }
    let module_dir = checked_module(root, module)?;
    let bundle_path = module_dir.join("evidence/phase1/bundle.v1.json");
    if !bundle_path.is_file() {
        status.failed_gates.push("PHASE1_BUNDLE_ABSENT".into());
        return Ok(status);
    }
    let bundle: ModulePhase1BundleV1 = match read_typed(&bundle_path) {
        Ok(bundle) => bundle,
        Err(error) => {
            status
                .failed_gates
                .push(format!("INVALID_PHASE1_BUNDLE: {error}"));
            return Ok(status);
        }
    };
    if let Err(error) = bundle.validate().and_then(|_| {
        verify_bundle_parents(root, &module_dir, &bundle)
            .map_err(|_| amphora_core::Phase1ContractError::ParentBinding)
    }) {
        status
            .failed_gates
            .push(format!("STALE_PHASE1_PARENT: {error}"));
        return Ok(status);
    }
    if phase0_event.as_deref() != Some(bundle.phase0_event_id.as_str()) {
        status
            .failed_gates
            .push("PHASE0_MOVEMENT_REVERSED_OR_STALE".into());
        return Ok(status);
    }
    status.prepared = true;
    let trust = match load_trust(root) {
        Ok(trust) => trust,
        Err(error) => {
            status
                .failed_gates
                .push(format!("PHASE1_TRUST_UNAVAILABLE: {error}"));
            return Ok(status);
        }
    };
    let evaluation_path = module_dir.join("evidence/phase1/receipts/evaluation.v1.dsse.json");
    let evaluation: ModulePhase1EvaluationReceiptV1 = match read_typed(&evaluation_path) {
        Ok(receipt) => receipt,
        Err(_) => {
            status
                .failed_gates
                .push("PHASE1_EVALUATION_SIGNATURE_ABSENT".into());
            return Ok(status);
        }
    };
    let evaluator = match evaluation.verify_signature(&trust.trust) {
        Ok(key) => key,
        Err(error) => {
            status
                .failed_gates
                .push(format!("INVALID_PHASE1_EVALUATION: {error}"));
            return Ok(status);
        }
    };
    if trust.roles.get(&evaluator).map(String::as_str) != Some("PHASE1_EVALUATOR")
        || evaluation.bundle_hash != file_hash(&bundle_path)?
    {
        status
            .failed_gates
            .push("PHASE1_EVALUATION_BINDING_OR_ROLE_MISMATCH".into());
        return Ok(status);
    }
    status.evaluation_signed = true;
    if !evaluation.phase1_eligible {
        status.failed_gates.extend(evaluation.failed_gates);
        status
            .failed_gates
            .push("PHASE1_SCIENTIFIC_GATES_NOT_PASSED".into());
        return Ok(status);
    }
    let review_path = module_dir.join("evidence/phase1/receipts/independent-review.v1.dsse.json");
    let review: ModulePhase1ReviewReceiptV1 = match read_typed(&review_path) {
        Ok(receipt) => receipt,
        Err(_) => {
            status
                .failed_gates
                .push("PHASE1_INDEPENDENT_REVIEW_ABSENT".into());
            return Ok(status);
        }
    };
    let reviewer = match review.verify_signature(&trust.trust) {
        Ok(key) => key,
        Err(error) => {
            status
                .failed_gates
                .push(format!("INVALID_PHASE1_REVIEW: {error}"));
            return Ok(status);
        }
    };
    if trust.roles.get(&reviewer).map(String::as_str) != Some("PHASE1_INDEPENDENT_REVIEWER")
        || review.evaluator_key_id != evaluator
        || review.bundle_hash != file_hash(&bundle_path)?
        || review.evaluation_receipt_hash != file_hash(&evaluation_path)?
        || !review.accepted_for_phase1
    {
        status
            .failed_gates
            .push("PHASE1_REVIEW_BINDING_OR_ROLE_MISMATCH".into());
        return Ok(status);
    }
    status.review_signed = true;
    let ledger_path = module_dir.join("movement/phase1/ledger.v1.json");
    if !ledger_path.is_file() {
        return Ok(status);
    }
    let ledger = read_json(&ledger_path)?;
    let events = ledger
        .get("events")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("invalid Phase-1 ledger"))?;
    if events.len() != 1 {
        status
            .failed_gates
            .push("PHASE1_MOVEMENT_COUNT_NOT_EXACTLY_ONE".into());
        return Ok(status);
    }
    let event_ref = &events[0];
    let relative = event_ref
        .get("path")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("Phase-1 event path absent"))?;
    let event_path = module_dir
        .join("movement/phase1")
        .join(safe_relative(relative)?);
    if file_hash(&event_path)?
        != event_ref
            .get("sha256")
            .and_then(Value::as_str)
            .unwrap_or_default()
    {
        status.failed_gates.push("STALE_PHASE1_MOVEMENT".into());
        return Ok(status);
    }
    let event: ModulePhase1MovementEventV1 = read_typed(&event_path)?;
    if event.validate().is_err()
        || event.bundle_hash != file_hash(&bundle_path)?
        || event.evaluation_receipt_hash != file_hash(&evaluation_path)?
        || event.review_receipt_hash != file_hash(&review_path)?
        || event.phase0_event_id != bundle.phase0_event_id
    {
        status
            .failed_gates
            .push("INVALID_OR_STALE_PHASE1_MOVEMENT".into());
        return Ok(status);
    }
    status.phase = "PHASE_1".into();
    status.scientific_readiness = "INDEPENDENTLY_VALIDATED".into();
    status.phase1_event_id = Some(event.event_id);
    Ok(status)
}

pub(crate) fn portfolio_status_from_phase0(
    root: &Path,
    phase0: &Value,
) -> Result<Phase1PortfolioStatusV1> {
    let rows = phase0
        .get("modules")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("Phase-0 portfolio status has no modules"))?;
    let mut modules = Vec::new();
    for row in rows {
        let module = row
            .get("module_id")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("Phase-0 status module ID is absent"))?;
        modules.push(verify_module_with_phase0(root, module, row)?);
    }
    Ok(Phase1PortfolioStatusV1 {
        schema: "amphora.phase1-portfolio-status.v1".into(),
        module_count: modules.len(),
        phase1_count: modules.iter().filter(|row| row.phase == "PHASE_1").count(),
        phase0_count: modules.iter().filter(|row| row.phase == "PHASE_0").count(),
        pre_phase0_count: modules
            .iter()
            .filter(|row| row.phase == "PRE_PHASE_0")
            .count(),
        ranking_enabled: false,
        modules,
    })
}

fn current_phase0(root: &Path, module: &str) -> Result<Value> {
    crate::phase0::portfolio_status(root)?
        .get("modules")
        .and_then(Value::as_array)
        .and_then(|rows| {
            rows.iter()
                .find(|row| row.get("module_id").and_then(Value::as_str) == Some(module))
        })
        .cloned()
        .ok_or_else(|| anyhow!("unknown registered module: {module}"))
}

fn phase0_movement(root: &Path, module: &str, event_id: &str) -> Result<(PathBuf, String)> {
    let ledger = read_json(&root.join(module).join("movement/ledger.v1.json"))?;
    let row = ledger
        .get("events")
        .and_then(Value::as_array)
        .and_then(|events| {
            events
                .iter()
                .find(|row| row.get("event_id").and_then(Value::as_str) == Some(event_id))
        })
        .ok_or_else(|| anyhow!("current Phase-0 movement is absent from its ledger"))?;
    let relative = safe_relative(
        row.get("path")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("Phase-0 movement path is absent"))?,
    )?;
    let path = PathBuf::from("movement").join(relative);
    let full = root.join(module).join(&path);
    let hash = file_hash(&full)?;
    if row.get("sha256").and_then(Value::as_str) != Some(hash.as_str()) {
        bail!("Phase-0 movement ledger hash is stale");
    }
    Ok((path, hash))
}

fn verify_bundle_parents(
    root: &Path,
    module_dir: &Path,
    bundle: &ModulePhase1BundleV1,
) -> Result<()> {
    for (relative, expected) in &bundle.parent_hashes {
        let path = if relative == PREREGISTRATION_PATH {
            root.join(relative)
        } else if relative.starts_with(&format!("{}/movement/", bundle.module_id)) {
            root.join(relative)
        } else {
            module_dir.join(safe_relative(relative)?)
        };
        if !path.is_file() || file_hash(&path)? != *expected {
            bail!("stale Phase-1 parent: {relative}");
        }
    }
    Ok(())
}

fn load_trust(root: &Path) -> Result<LoadedTrust> {
    let file: TrustStoreFileV1 = read_typed(&root.join(TRUST_STORE_PATH))?;
    if file.schema != "amphora.phase1-trust-store.v1" {
        bail!("invalid Phase-1 trust-store schema");
    }
    let mut trust = TrustStore::default();
    let mut roles = BTreeMap::new();
    for key in file.keys {
        if key.algorithm != "Ed25519" || key.development || !key.phase1_authorized {
            continue;
        }
        let bytes = decode_hex_32(&key.public_key_hex)?;
        trust.insert(key.key_id.clone(), bytes)?;
        if key.revoked {
            trust.revoke(key.key_id.clone());
        }
        roles.insert(key.key_id, key.role);
    }
    Ok(LoadedTrust { trust, roles })
}

fn verify_signing_identity(
    trust: &LoadedTrust,
    key_id: &str,
    role: &str,
    key: &SigningKey,
) -> Result<()> {
    if trust.roles.get(key_id).map(String::as_str) != Some(role) {
        bail!("Phase-1 signing identity is not authorized for {role}");
    }
    let probe = amphora_core::sign_dsse(
        "application/vnd.amphora.identity-probe",
        b"phase1",
        key_id,
        key,
    );
    amphora_core::verify_dsse(&probe, &trust.trust)?;
    Ok(())
}

fn checked_module(root: &Path, module: &str) -> Result<PathBuf> {
    if !module.starts_with("amphora-")
        || !module
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-')
    {
        bail!("invalid module ID");
    }
    let manifest = read_json(&root.join(MANIFEST_PATH))?;
    if !manifest
        .get("modules")
        .and_then(Value::as_array)
        .is_some_and(|rows| {
            rows.iter()
                .any(|row| row.get("project").and_then(Value::as_str) == Some(module))
        })
    {
        bail!("unknown registered module: {module}");
    }
    let path = root.join(module);
    if !path.is_dir() {
        bail!("module folder is absent: {module}");
    }
    Ok(path)
}

fn safe_relative(value: &str) -> Result<PathBuf> {
    let path = Path::new(value);
    if path.is_absolute()
        || path
            .components()
            .any(|part| !matches!(part, Component::Normal(_)))
    {
        bail!("path escapes its authoritative root");
    }
    Ok(path.to_path_buf())
}

fn rooted(root: &Path, path: &Path) -> Result<PathBuf> {
    if path.is_absolute() {
        return Ok(path.to_path_buf());
    }
    Ok(root.join(safe_relative(&path.to_string_lossy())?))
}

fn read_json(path: &Path) -> Result<Value> {
    let bytes = fs::read(path).with_context(|| format!("reading {}", path.display()))?;
    Ok(amphora_core::parse_json_strict(&bytes)?)
}

fn read_typed<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
    Ok(serde_json::from_value(read_json(path)?)?)
}

fn file_hash(path: &Path) -> Result<String> {
    let bytes = fs::read(path).with_context(|| format!("hashing {}", path.display()))?;
    let mut digest = Sha256::new();
    digest.update(bytes);
    Ok(format!("{:x}", digest.finalize()))
}

fn canonical_bytes(value: &impl Serialize) -> Result<Vec<u8>> {
    Ok(serde_json::to_vec(&canonicalize(&serde_json::to_value(
        value,
    )?))?)
}

fn write_json_immutable(path: &Path, value: &impl Serialize) -> Result<()> {
    write_bytes_immutable(path, &canonical_bytes(value)?)
}

fn write_bytes_immutable(path: &Path, bytes: &[u8]) -> Result<()> {
    if path.exists() {
        if path.is_file() && fs::read(path)? == bytes {
            return Ok(());
        }
        bail!("immutable Phase-1 artifact differs: {}", path.display());
    }
    fs::create_dir_all(
        path.parent()
            .ok_or_else(|| anyhow!("artifact has no parent"))?,
    )?;
    let mut file = OpenOptions::new().create_new(true).write(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn write_json_generated(path: &Path, value: &Value) -> Result<()> {
    let bytes = canonical_bytes(value)?;
    if path.is_file() && fs::read(path)? == bytes {
        return Ok(());
    }
    fs::create_dir_all(
        path.parent()
            .ok_or_else(|| anyhow!("report has no parent"))?,
    )?;
    let temporary = path.with_extension(format!("tmp-{}", std::process::id()));
    if temporary.exists() {
        fs::remove_file(&temporary)?;
    }
    fs::write(&temporary, bytes)?;
    fs::rename(temporary, path)?;
    Ok(())
}

fn load_signing_key(root: &Path, path: &Path) -> Result<SigningKey> {
    let path = rooted(root, path)?;
    if path.starts_with(root) {
        bail!("Phase-1 private key must remain outside the repository");
    }
    let metadata = fs::metadata(&path)?;
    if metadata.permissions().mode() & 0o077 != 0 {
        bail!("Phase-1 private key permissions must be 0600 or stricter");
    }
    let bytes = fs::read(path)?;
    let bytes: [u8; 32] = bytes
        .try_into()
        .map_err(|_| anyhow!("Phase-1 private key must contain exactly 32 bytes"))?;
    Ok(SigningKey::from_bytes(&bytes))
}

fn decode_hex_32(value: &str) -> Result<[u8; 32]> {
    if value.len() != 64 {
        bail!("Ed25519 public key must contain 64 lowercase hexadecimal characters");
    }
    let mut output = [0_u8; 32];
    for (index, byte) in output.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)?;
    }
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn candidate_and_cross_module_paths_are_rejected() {
        assert!(safe_relative("evidence/phase1/locks/dataset.v1.json").is_ok());
        assert!(safe_relative("../amphora-other/evidence/phase1/bundle.v1.json").is_err());
        assert!(safe_relative("/tmp/candidate-result.json").is_err());
    }

    #[test]
    fn empty_phase1_trust_store_authorizes_no_signers() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .to_path_buf();
        let trust = load_trust(&root).unwrap();
        assert!(trust.roles.is_empty());
    }
}
