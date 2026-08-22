use anyhow::{anyhow, bail, Context, Result};
use base64::engine::general_purpose::STANDARD;
use base64::Engine;
use clap::Parser;
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use unicode_normalization::UnicodeNormalization;

const REVIEWED_MODULES: [&str; 29] = [
    "amphora-barrier-corrosion-score",
    "amphora-candidate-contract",
    "amphora-cro-protocol-packager",
    "amphora-cure-potlife-gate",
    "amphora-design-rule-score",
    "amphora-envelope-gates",
    "amphora-evidence-intake-validator",
    "amphora-formulation-arithmetic",
    "amphora-formulation-universe",
    "amphora-ingredient-library",
    "amphora-ip-fto-guard",
    "amphora-known-answer-benchmarks",
    "amphora-model-card-authority",
    "amphora-molecule-generator",
    "amphora-molecule-design-gate",
    "amphora-molecule-novelty",
    "amphora-molecule-property",
    "amphora-molecule-role-ranker",
    "amphora-optimizer-orchestrator",
    "amphora-process-qc-twin",
    "amphora-public-corrosion-benchmark",
    "amphora-redteam-audit",
    "amphora-report-packager",
    "amphora-run-provenance",
    "amphora-solvency-score",
    "amphora-source-ledger",
    "amphora-sourceability-ehs",
    "amphora-tolerance-robustness",
    "amphora-viscosity-score",
];
const FIRST_SUCCESSION_CONTROLS: [&str; 4] = [
    "amphora-evidence-intake-validator",
    "amphora-source-ledger",
    "amphora-redteam-audit",
    "amphora-report-packager",
];
const SECOND_SUCCESSION_CONTROLS: [&str; 5] = [
    "amphora-formulation-arithmetic",
    "amphora-formulation-universe",
    "amphora-envelope-gates",
    "amphora-cro-protocol-packager",
    "amphora-optimizer-orchestrator",
];
const THIRD_SUCCESSION_CONTROLS: [&str; 1] = ["amphora-solvency-score"];
const REGISTRY_SUCCESSION_PATH: &str = "registry/succession.v1.json";
const REGISTRY_SUCCESSION_CHAIN_PATH: &str = "registry/succession-chain.v1.json";
const REGISTRY_SUCCESSION_RECORDS_DIR: &str = "registry/succession";
const REVIEW_METHOD: &str = "AUTOMATED_INDEPENDENT_REIMPLEMENTATION";
const INDEPENDENCE_SCOPE: &str = "CODE_PATH_AND_SIGNING_IDENTITY";
const EVALUATION_PAYLOAD_TYPE: &str =
    "application/vnd.amphora.module-phase0-evaluation-receipt.v1+json";
const REVIEW_PAYLOAD_TYPE: &str = "application/vnd.amphora.module-phase0-review-receipt.v1+json";
const ZERO_AUTHORITY_LOCKS: [&str; 10] = [
    "no_ranking_authority",
    "no_optimizer_authority",
    "no_release_authority",
    "no_qualification_authority",
    "no_patentability_authority",
    "fto_not_performed",
    "no_procurement_authority",
    "no_regulatory_authority",
    "no_safety_authority",
    "no_product_performance_authority",
];

const RIGHTS_EXCLUSIONS: [&str; 9] = [
    "NO_RANKING_AUTHORITY",
    "NO_OPTIMIZER_AUTHORITY",
    "NO_RELEASE_AUTHORITY",
    "NO_PROCUREMENT_AUTHORITY",
    "NO_REGULATORY_AUTHORITY",
    "NO_SAFETY_AUTHORITY",
    "NO_PATENTABILITY_AUTHORITY",
    "NO_FTO_AUTHORITY",
    "NO_PRODUCT_PERFORMANCE_AUTHORITY",
];
const PROHIBITED_AUTHORITIES: [&str; 10] = [
    "RANKING",
    "OPTIMIZER_USE",
    "RELEASE",
    "QUALIFICATION",
    "PATENTABILITY",
    "FTO",
    "PROCUREMENT",
    "REGULATORY",
    "SAFETY",
    "PRODUCT_PERFORMANCE",
];
const REQUIRED_ATTACKS: [&str; 10] = [
    "SAME_SIGNER_REVIEW",
    "WRONG_ROLE_SIGNATURE",
    "FORGED_SIGNATURE",
    "REPOSITORY_LOCAL_PRIVATE_KEY",
    "STALE_PARENT",
    "CROSS_MODULE_PATH_SUBSTITUTION",
    "STRIPPED_CLAIM_LOCK",
    "AUTHORITY_ESCALATION",
    "ALTERED_BENCHMARK_OUTPUT",
    "FALSE_HUMAN_REVIEW_CLAIM",
];
const CURRENT_REQUIRED_ATTACKS: [&str; 6] = [
    "STRIPPED_MISSION_LOCKS",
    "FAILING_DETERMINISTIC_DIAGNOSTIC",
    "FALSE_BENCHMARK_EXECUTION_COMPLETE",
    "INCOMPLETE_REVIEW_POLICY",
    "UNKNOWN_REVIEWER_MODULE",
    "SUPERSESSION_ARCHIVE_SUBSTITUTION",
];
const REDTEAM_ATTACK_AXES: [&str; 24] = [
    "IDENTITY_OR_MODULE_SUBSTITUTION",
    "REGISTRY_TAMPERING",
    "REGISTRY_SUPERSESSION_TAMPERING",
    "FOLDER_CONFINEMENT_ESCAPE",
    "DSSE_FORGERY",
    "DSSE_WRONG_ROLE",
    "DSSE_LOCAL_SIGNER",
    "DSSE_REVOKED_SIGNER",
    "DSSE_SAME_SIGNER",
    "FALSE_HUMAN_REVIEW",
    "INCOMPLETE_POLICY",
    "ALTERED_DIAGNOSTIC",
    "NONDETERMINISTIC_DIAGNOSTIC",
    "FALSE_EXECUTION_COMPLETION",
    "UNEXECUTED_SCIENCE",
    "RIGHTS_LAUNDERING",
    "EVIDENCE_LAUNDERING",
    "SOURCE_DUPLICATE",
    "SOURCE_MISSING_FIELD",
    "SOURCE_WAIVER_LAUNDERING",
    "REPORT_SIGNATURE_DEFECT",
    "REPORT_ENVELOPE_BINDING_DEFECT",
    "REPORT_CLAIM_LOCK_DEFECT",
    "AUTHORITY_ESCALATION",
];

#[derive(Debug, Parser)]
#[command(
    name = "amphora-phase0-reviewer",
    about = "Independent automated Phase-0 reviewer"
)]
struct Args {
    #[arg(long)]
    workspace: PathBuf,
    #[arg(long)]
    module: String,
    #[arg(long)]
    benchmark_executable: PathBuf,
    #[arg(long)]
    reviewer_key_id: String,
    #[arg(long)]
    reviewer_key: PathBuf,
    #[arg(long)]
    output: PathBuf,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct TrustStoreFile {
    schema: String,
    authorization_status: String,
    keys: Vec<TrustKey>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct TrustKey {
    key_id: String,
    algorithm: String,
    role: String,
    public_key_hex: String,
    phase0_authorized: bool,
    development: bool,
    revoked: bool,
}

#[derive(Debug)]
struct TrustedIdentity {
    role: String,
    key: VerifyingKey,
}

#[derive(Debug, PartialEq, Eq)]
struct BenchmarkReplay {
    raw_line: Vec<u8>,
    diagnostic: Value,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct DeterministicDiagnostic {
    schema: String,
    module_id: String,
    implementation_readiness: String,
    expected_fixture_outcomes: BTreeMap<String, String>,
    observed_fixture_outcomes: BTreeMap<String, String>,
    positive_control_count: u64,
    negative_control_count: u64,
    zero_authority_assertions: BTreeMap<String, bool>,
    details: BTreeMap<String, Value>,
    passed: bool,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceControlInput {
    case_id: String,
    primary_url: String,
    secondary_url: Option<String>,
    required_fields_complete: bool,
    waiver: Option<String>,
    source_authority: String,
    requested_authority: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct DsseEnvelope {
    payload_type: String,
    payload: String,
    signatures: Vec<DsseSignature>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct DsseSignature {
    keyid: String,
    sig: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct Bundle {
    schema: String,
    module_id: String,
    module_class: String,
    registry_manifest_hash: String,
    source_lock_hash: String,
    dataset_manifest_hash: String,
    split_manifest_hash: String,
    benchmark_lock_hash: String,
    promotion_policy_hash: String,
    claim_contract_hash: String,
    technical_dossier_hash: String,
    prior_art_hash: String,
    disclosure_log_hash: String,
    parents: BTreeMap<String, String>,
    toolkit_versions: BTreeMap<String, String>,
    applicability_domain: Vec<String>,
    claim_locks: BTreeMap<String, bool>,
    review_packet_blinded: bool,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct ClaimContract {
    schema: String,
    module_id: String,
    registry_manifest_hash: String,
    module_class: String,
    scientific_readiness_ceiling: String,
    decision_use_ceiling: String,
    applicability_domain: Vec<String>,
    abstain_outside_applicability: bool,
    claim_locks: BTreeMap<String, bool>,
    prohibited_authorities: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceLock {
    schema: String,
    module_id: String,
    canonical_home: String,
    sources: Vec<SourceEntry>,
    imported_locks: Vec<Value>,
    rights_gate_passed: bool,
    candidate_supplied_evidence_allowed: bool,
    legacy_amphora_receipt_authority: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceEntry {
    module_relative_path: String,
    observed_sha256: String,
    declared_sha256: Option<String>,
    hash_current: bool,
    rights_status: String,
    rights_evidence_path: Option<String>,
    license_present: bool,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceLockV2 {
    schema: String,
    module_id: String,
    canonical_home: String,
    eligible_sources: Vec<EligibleSourceV2>,
    excluded_sources: Vec<ExcludedSourceV2>,
    inventory_hash: String,
    rights_gate_passed: bool,
    candidate_supplied_evidence_allowed: bool,
    legacy_amphora_receipt_authority: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct EligibleSourceV2 {
    module_relative_path: String,
    observed_sha256: String,
    declared_sha256: String,
    hash_current: bool,
    rights_receipt_path: String,
    rights_receipt_sha256: String,
    authorization_overlay_path: String,
    authorization_overlay_sha256: String,
    authorization_overlay_id: String,
    rights_reviewer_key_id: String,
    independently_reviewed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ExcludedSourceV2 {
    module_relative_path: String,
    observed_sha256: String,
    reason: String,
    authority_ceiling: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct RightsTrustStoreFile {
    schema: String,
    authorization_status: String,
    keys: Vec<RightsTrustKey>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct RightsTrustKey {
    key_id: String,
    algorithm: String,
    role: String,
    public_key_hex: String,
    rights_review_authorized: bool,
    development: bool,
    revoked: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct RightsReviewReceipt {
    schema: String,
    receipt_id: String,
    module_id: String,
    snapshot_id: String,
    dataset_id: String,
    acquisition_unit_id: String,
    rights_decision_id: String,
    rights_decision_hash: String,
    artifact_path: String,
    artifact_sha256: String,
    rights_class: String,
    license: String,
    accepted: bool,
    authority_ceiling: String,
    exclusions: Vec<String>,
    reviewer_key_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    signature: Option<DsseEnvelope>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
struct AuthorizationOverlay {
    schema: String,
    overlay_id: String,
    parent_overlay_id: Option<String>,
    module_id: String,
    snapshot_id: String,
    dataset_id: String,
    acquisition_unit_id: String,
    activation_hash: String,
    artifact_path: String,
    artifact_sha256: String,
    rights_receipt_path: String,
    rights_receipt_sha256: String,
    rights_reviewer_key_id: String,
    authority_ceiling: String,
    scoring_authorized: bool,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct AuthorizationOverlayRef {
    overlay_id: String,
    path: String,
    sha256: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct AuthorizationLedger {
    schema: String,
    module_id: String,
    snapshot_id: String,
    head_overlay_id: String,
    overlays: Vec<AuthorizationOverlayRef>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct PromotionPolicy {
    schema: String,
    module_id: String,
    target_phase: String,
    target_scientific_readiness: String,
    decision_use_ceiling: String,
    required_distinct_roles: Vec<String>,
    required_review_method: String,
    required_independence_scope: String,
    human_review_performed: bool,
    local_development_keys_authorized: bool,
    scientific_success_required: bool,
    required_gates: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct BenchmarkLock {
    schema: String,
    module_id: String,
    dataset_manifest_sha256: String,
    split_manifest_sha256: String,
    runner: String,
    scientific_success_required_for_phase0: bool,
    negative_result_authority: String,
    attacks: Vec<String>,
    replay_count: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct EvaluationReceipt {
    schema: String,
    receipt_id: String,
    module_id: String,
    module_class: String,
    bundle_hash: String,
    bundle_parent_hashes: BTreeMap<String, String>,
    evaluator_key_id: String,
    audit_execution_passed: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    benchmark_execution_complete: Option<bool>,
    scientific_outcome: String,
    phase0_eligible: bool,
    scientific_readiness: String,
    decision_use_ceiling: String,
    claim_lock_hash: String,
    applicability_domain: Vec<String>,
    failed_gates: Vec<String>,
    retained_negative_results: Vec<String>,
    replay_hash: String,
    metrics: BTreeMap<String, Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    signature: Option<DsseEnvelope>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct Supersession {
    schema: String,
    supersession_id: String,
    module_id: String,
    reason: String,
    archive_root: String,
    archived_artifacts: BTreeMap<String, String>,
    unsigned_preparation_only: bool,
    authority_transferred: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct PreparationRevision {
    schema: String,
    revision_id: String,
    module_id: String,
    revision_number: u64,
    parent_revision_id: Option<String>,
    supersession_id: String,
    supersession_path: String,
    supersession_sha256: String,
    archived_bundle_sha256: String,
    unsigned_preparation_only: bool,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct PreparationRevisionRef {
    revision_id: String,
    path: String,
    sha256: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct PreparationLedger {
    schema: String,
    module_id: String,
    head_revision_id: Option<String>,
    revisions: Vec<PreparationRevisionRef>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
struct RegistryManifestRef {
    path: String,
    sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
struct RegistryEdit {
    module_id: String,
    field: String,
    old_value: Value,
    new_value: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
struct RegistrySuccession {
    schema: String,
    succession_id: String,
    predecessor: RegistryManifestRef,
    successor: RegistryManifestRef,
    edits: Vec<RegistryEdit>,
    no_scientific_change: bool,
    no_rights_change: bool,
    no_ranking_change: bool,
    no_solver_change: bool,
    no_authority_change: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
struct RegistrySuccessionRecordRef {
    record_sha256: String,
    succession_id: String,
    predecessor_sha256: String,
    successor_sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
struct RegistrySuccessionChain {
    schema: String,
    genesis_manifest_sha256: String,
    head_manifest_sha256: String,
    records: Vec<RegistrySuccessionRecordRef>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(deny_unknown_fields)]
struct ReviewReceipt {
    schema: String,
    review_id: String,
    module_id: String,
    bundle_hash: String,
    evaluation_receipt_hash: String,
    evaluator_key_id: String,
    reviewer_key_id: String,
    review_method: String,
    independence_scope: String,
    human_review_performed: bool,
    independent_reimplementation_passed: bool,
    parent_hashes_current: bool,
    claim_locks_preserved: bool,
    zero_authority_affirmed: bool,
    accepted_for_phase0: bool,
    findings: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    signature: Option<DsseEnvelope>,
}

fn main() -> Result<()> {
    let args = Args::parse();
    let result = review(&args)?;
    println!("{}", serde_json::to_string(&result)?);
    Ok(())
}

fn review(args: &Args) -> Result<Value> {
    verify_allowed_module(&args.module)?;
    let module = args.module.as_str();
    let root = args.workspace.canonicalize()?;
    let module_dir = confined_module_dir(&root, &args.module)?;
    let trust = load_trust(&root)?;
    let reviewer = require_role(&trust, &args.reviewer_key_id, "PHASE0_INTERNAL_REVIEWER")?;
    let signing_key = load_external_signing_key(&root, &args.reviewer_key)?;
    if signing_key.verifying_key() != reviewer.key {
        bail!("reviewer private key does not match its trusted public identity");
    }
    ensure_external_new_output(&root, &args.output)?;

    let bundle_path = module_dir.join("evidence/phase0/bundle.v1.json");
    let bundle: Bundle = read_typed(&bundle_path)?;
    verify_bundle(&root, &module_dir, module, &bundle)?;
    let contract: ClaimContract = read_typed(&module_dir.join("ip/claim-contract.v1.json"))?;
    verify_claim_contract(module, &bundle, &contract)?;
    let source_lock_path = bundle_source_lock_relative(&bundle)?;
    let source_lock: Value = read_typed(&module_dir.join(source_lock_path))?;
    verify_rights(module, &module_dir, &bundle, &source_lock, &trust)?;
    let policy: PromotionPolicy =
        read_typed(&module_dir.join("evidence/phase0/promotion/policy.v1.json"))?;
    verify_policy(module, &bundle, &policy)?;
    let benchmark_lock: BenchmarkLock =
        read_typed(&module_dir.join("evidence/phase0/benchmark/benchmark-lock.v1.json"))?;
    verify_benchmark_lock(module, &bundle, &benchmark_lock)?;

    let evaluation_path = module_dir.join("evidence/phase0/receipts/evaluation.v1.dsse.json");
    let evaluation: EvaluationReceipt = read_typed(&evaluation_path)?;
    verify_evaluation(
        &trust,
        module,
        &bundle,
        &bundle_path,
        &evaluation,
        &args.reviewer_key_id,
    )?;
    verify_recorded_benchmark(module, &module_dir, &bundle, &evaluation)?;

    let first = run_locked_benchmark(&root, &args.benchmark_executable, module, &bundle)?;
    let second = run_locked_benchmark(&root, &args.benchmark_executable, module, &bundle)?;
    if first != second {
        bail!("locked module diagnostic changed between reviewer replays");
    }
    let recorded: Value = read_typed(&module_dir.join("evidence/phase0/benchmark/result.v1.json"))?;
    if recorded.pointer("/first_replay/diagnostic_receipt") != Some(&first.diagnostic)
        || (module != "amphora-candidate-contract"
            && recorded
                .pointer("/first_replay/diagnostic_sha256")
                .and_then(Value::as_str)
                != Some(raw_hash(&first.raw_line).as_str()))
    {
        bail!("current locked benchmark output differs from the evaluated output");
    }

    let mut receipt = ReviewReceipt {
        schema: "amphora.module-phase0-review-receipt.v1".into(),
        review_id: String::new(),
        module_id: module.into(),
        bundle_hash: file_hash(&bundle_path)?,
        evaluation_receipt_hash: file_hash(&evaluation_path)?,
        evaluator_key_id: evaluation.evaluator_key_id,
        reviewer_key_id: args.reviewer_key_id.clone(),
        review_method: REVIEW_METHOD.into(),
        independence_scope: INDEPENDENCE_SCOPE.into(),
        human_review_performed: false,
        independent_reimplementation_passed: true,
        parent_hashes_current: true,
        claim_locks_preserved: true,
        zero_authority_affirmed: true,
        accepted_for_phase0: true,
        findings: vec![
            "automated code-path and signing-identity independence only".into(),
            "no human or organizational independence asserted".into(),
        ],
        signature: None,
    };
    validate_review(module, &receipt)?;
    receipt.review_id = format!(
        "phase0-review-{}",
        stable_hash(&serde_json::to_value(&receipt)?)
    );
    let payload = canonical_bytes(&receipt)?;
    receipt.signature = Some(sign_dsse(
        REVIEW_PAYLOAD_TYPE,
        &payload,
        &args.reviewer_key_id,
        &signing_key,
    ));
    write_new_json(&args.output, &receipt)?;
    Ok(json!({
        "schema": "amphora.phase0-independent-review-result.v1",
        "module_id": module,
        "review_id": receipt.review_id,
        "reviewer_key_id": args.reviewer_key_id,
        "review_method": REVIEW_METHOD,
        "independence_scope": INDEPENDENCE_SCOPE,
        "human_review_performed": false,
        "accepted_for_phase0": true,
        "review_receipt_sha256": file_hash(&args.output)?,
    }))
}

fn verify_allowed_module(module: &str) -> Result<()> {
    if !REVIEWED_MODULES.contains(&module) {
        bail!("module is not in the locked 29-module reviewer allowlist");
    }
    Ok(())
}

fn confined_module_dir(root: &Path, module: &str) -> Result<PathBuf> {
    let path = root.join(module).canonicalize()?;
    if !path.starts_with(root) || path.parent() != Some(root) || !path.is_dir() {
        bail!("reviewed module folder is not confined to the workspace");
    }
    Ok(path)
}

fn expected_readiness(bundle: &Bundle) -> Result<&'static str> {
    match bundle.module_class.as_str() {
        "DETERMINISTIC_CONTROL" => Ok("NOT_APPLICABLE"),
        "SCIENTIFIC_OR_EVIDENCE" => Ok("LOCKED_INTERNAL"),
        _ => bail!("unknown Phase-0 module class"),
    }
}

fn bundle_source_lock_relative(bundle: &Bundle) -> Result<&str> {
    let paths = bundle
        .parents
        .keys()
        .filter(|path| {
            matches!(
                path.as_str(),
                "evidence/phase0/sources/source-lock.v1.json"
                    | "evidence/phase0/sources/source-lock.v2.json"
            )
        })
        .map(String::as_str)
        .collect::<Vec<_>>();
    if paths.len() != 1 {
        bail!("bundle must bind exactly one supported Phase-0 source lock");
    }
    Ok(paths[0])
}

fn verify_bundle(root: &Path, module_dir: &Path, module: &str, bundle: &Bundle) -> Result<()> {
    if bundle.schema != "amphora.module-phase0-bundle.v1"
        || bundle.module_id != module
        || expected_readiness(bundle).is_err()
        || bundle.toolkit_versions.is_empty()
        || bundle.applicability_domain.is_empty()
        || !bundle.review_packet_blinded
    {
        bail!("bundle identity, class, registry, toolkit, domain, or blinding is invalid");
    }
    resolve_registry_manifest(root, &bundle.registry_manifest_hash)?;
    verify_hash("registry manifest", &bundle.registry_manifest_hash)?;
    let source_lock_relative = bundle_source_lock_relative(bundle)?;
    let required = [
        (source_lock_relative, &bundle.source_lock_hash),
        (
            "evidence/phase0/dataset/dataset-manifest.v1.json",
            &bundle.dataset_manifest_hash,
        ),
        (
            "evidence/phase0/split/split-manifest.v1.json",
            &bundle.split_manifest_hash,
        ),
        (
            "evidence/phase0/benchmark/benchmark-lock.v1.json",
            &bundle.benchmark_lock_hash,
        ),
        (
            "evidence/phase0/promotion/policy.v1.json",
            &bundle.promotion_policy_hash,
        ),
        ("ip/claim-contract.v1.json", &bundle.claim_contract_hash),
        (
            "ip/technical-dossier.v1.json",
            &bundle.technical_dossier_hash,
        ),
        ("ip/prior-art.v1.json", &bundle.prior_art_hash),
        ("ip/disclosure-log.v1.json", &bundle.disclosure_log_hash),
    ];
    if bundle.parents.is_empty() {
        bail!("bundle parent map is empty");
    }
    for (relative, declared) in &bundle.parents {
        verify_hash(relative, declared)?;
        let path = confined_file(module_dir, relative)?;
        if file_hash(&path)? != *declared {
            bail!("stale parent hash: {relative}");
        }
    }
    for (relative, declared) in required {
        verify_hash(relative, declared)?;
        if bundle.parents.get(relative) != Some(declared) {
            bail!("bundle does not bind the required parent {relative}");
        }
    }
    verify_supersession(module_dir, module, bundle)?;
    verify_preparation_ledger(module_dir, module, bundle)?;
    verify_module_registry_succession(root, module_dir, module, bundle)?;
    verify_zero_authority_locks(&bundle.claim_locks)
}

fn verify_module_registry_succession(
    root: &Path,
    module_dir: &Path,
    module: &str,
    bundle: &Bundle,
) -> Result<()> {
    let relative = "evidence/phase0/registry/succession.v1.json";
    let local = bundle.parents.get(relative);
    let central = registry_succession_for_module(root, module, &bundle.registry_manifest_hash)?;
    if let Some(central) = central {
        let declared =
            local.ok_or_else(|| anyhow!("module-local registry succession is absent"))?;
        let local_path = confined_file(module_dir, relative)?;
        let local_record: RegistrySuccession = read_typed(&local_path)?;
        let central_path = registry_succession_record_path(root, &central)?;
        if file_hash(&local_path)? != *declared
            || local_record != central
            || fs::read(&local_path)? != fs::read(central_path)?
        {
            bail!("module-local registry succession is altered or substituted");
        }
    } else if local.is_some() {
        bail!("historical or non-promoted bundle contains an unexpected registry succession");
    }
    Ok(())
}

fn resolve_registry_manifest(root: &Path, requested_hash: &str) -> Result<PathBuf> {
    let (chain, _) = verify_registry_succession_chain(root)?;
    let known = requested_hash == chain.genesis_manifest_sha256
        || chain
            .records
            .iter()
            .any(|record| record.successor_sha256 == requested_hash);
    if !known {
        bail!("bundle references missing or forked registry history");
    }
    let path = root.join(format!(
        "registry/archive/{requested_hash}/module-manifest.json"
    ));
    if file_hash(&path)? != requested_hash {
        bail!("hash-addressed registry archive is altered");
    }
    Ok(path)
}

fn registry_succession_record_path(
    root: &Path,
    succession: &RegistrySuccession,
) -> Result<PathBuf> {
    let (chain, _) = verify_registry_succession_chain(root)?;
    let reference = chain
        .records
        .iter()
        .find(|reference| reference.succession_id == succession.succession_id)
        .ok_or_else(|| anyhow!("registry succession record is absent from the chain"))?;
    Ok(root
        .join(REGISTRY_SUCCESSION_RECORDS_DIR)
        .join(format!("{}.json", reference.record_sha256)))
}

fn registry_succession_for_module(
    root: &Path,
    module: &str,
    manifest_hash: &str,
) -> Result<Option<RegistrySuccession>> {
    let (_, records) = verify_registry_succession_chain(root)?;
    Ok(records.into_iter().find(|record| {
        record.successor.sha256 == manifest_hash
            && record.edits.iter().any(|edit| edit.module_id == module)
    }))
}

fn verify_registry_succession_chain(
    root: &Path,
) -> Result<(RegistrySuccessionChain, Vec<RegistrySuccession>)> {
    const GENESIS: &str = "be6d3e8023c17a779d8503f3bfcfb15b0020d5ec5c768c9791013ff4134ed6b7";
    const FIRST_HEAD: &str = "bff63ed55151f6f9055312a3cd4026fc11edc320c0df61f3593be54d833c87fc";
    const FIRST_RECORD: &str = "0be2e86905ad249bfd908889e297ff4871221e4c71ed4cc4d313690738c9fe44";
    const SECOND_RECORD: &str = "4331b19bc615f9c559da753dc5a0d23a269f0b033f129350db8ba48e495f099a";
    let chain: RegistrySuccessionChain = read_typed(&root.join(REGISTRY_SUCCESSION_CHAIN_PATH))?;
    if chain.schema != "amphora.module-registry-succession-chain.v1"
        || chain.genesis_manifest_sha256 != GENESIS
        || chain.head_manifest_sha256 != file_hash(&root.join("module-manifest.json"))?
        || chain.records.len() != 3
        || chain.records[0].record_sha256 != FIRST_RECORD
        || chain.records[0].predecessor_sha256 != GENESIS
        || chain.records[0].successor_sha256 != FIRST_HEAD
        || chain.records[1].record_sha256 != SECOND_RECORD
        || chain.records[1].predecessor_sha256 != FIRST_HEAD
        || chain.records[2].predecessor_sha256 != chain.records[1].successor_sha256
        || chain.records[2].successor_sha256 != chain.head_manifest_sha256
    {
        bail!("registry succession chain continuity, genesis, or head is invalid");
    }
    let record_hashes = chain
        .records
        .iter()
        .map(|record| record.record_sha256.as_str())
        .collect::<BTreeSet<_>>();
    let succession_ids = chain
        .records
        .iter()
        .map(|record| record.succession_id.as_str())
        .collect::<BTreeSet<_>>();
    let manifests = std::iter::once(chain.genesis_manifest_sha256.as_str())
        .chain(
            chain
                .records
                .iter()
                .map(|record| record.successor_sha256.as_str()),
        )
        .collect::<BTreeSet<_>>();
    if record_hashes.len() != 3 || succession_ids.len() != 3 || manifests.len() != 4 {
        bail!("registry succession chain contains a duplicate, fork, or cycle");
    }
    let first_addressed = root
        .join(REGISTRY_SUCCESSION_RECORDS_DIR)
        .join(format!("{FIRST_RECORD}.json"));
    if file_hash(&first_addressed)? != FIRST_RECORD
        || fs::read(root.join(REGISTRY_SUCCESSION_PATH))? != fs::read(&first_addressed)?
    {
        bail!("immutable first succession record or hash-addressed copy changed");
    }
    let mut records = Vec::new();
    for reference in &chain.records {
        let path = root
            .join(REGISTRY_SUCCESSION_RECORDS_DIR)
            .join(format!("{}.json", reference.record_sha256));
        if file_hash(&path)? != reference.record_sha256 {
            bail!("hash-addressed registry succession record is altered");
        }
        let succession: RegistrySuccession = read_typed(&path)?;
        let expected_id = {
            let mut value = serde_json::to_value(&succession)?;
            value["succession_id"] = Value::String(String::new());
            format!("registry-succession-{}", stable_hash(&value))
        };
        if succession.schema != "amphora.module-registry-succession.v1"
            || succession.succession_id != expected_id
            || succession.succession_id != reference.succession_id
            || succession.predecessor.sha256 != reference.predecessor_sha256
            || succession.successor.sha256 != reference.successor_sha256
            || !succession.no_scientific_change
            || !succession.no_rights_change
            || !succession.no_ranking_change
            || !succession.no_solver_change
            || !succession.no_authority_change
            || succession.edits.is_empty()
        {
            bail!("registry succession identity or no-authority assertions are invalid");
        }
        for manifest in [&succession.predecessor, &succession.successor] {
            if manifest.path != format!("registry/archive/{}/module-manifest.json", manifest.sha256)
                || file_hash(&root.join(safe_relative(&manifest.path)?))? != manifest.sha256
            {
                bail!("registry succession archive reference is altered");
            }
        }
        let mut predecessor: Value = read_typed(&root.join(&succession.predecessor.path))?;
        let successor: Value = read_typed(&root.join(&succession.successor.path))?;
        let mut edited = BTreeSet::new();
        let mut changed = BTreeSet::new();
        for edit in &succession.edits {
            if !matches!(
                edit.field.as_str(),
                "readiness" | "operational_readiness" | "non_blocking_claim_locks"
            ) || !edited.insert((edit.module_id.clone(), edit.field.clone()))
            {
                bail!("registry succession contains a duplicate or disallowed edit");
            }
            let row = predecessor["modules"]
                .as_array_mut()
                .and_then(|rows| {
                    rows.iter_mut().find(|row| {
                        row.get("project").and_then(Value::as_str) == Some(&edit.module_id)
                    })
                })
                .ok_or_else(|| anyhow!("registry succession module is absent"))?;
            if row.get(&edit.field) != Some(&edit.old_value) {
                bail!("registry succession old value is false");
            }
            row[edit.field.as_str()] = edit.new_value.clone();
            changed.insert(edit.module_id.as_str());
        }
        if predecessor != successor {
            bail!("registry succession contains omitted, extra, or forked changes");
        }
        if records.is_empty() {
            if changed
                != FIRST_SUCCESSION_CONTROLS
                    .iter()
                    .copied()
                    .collect::<BTreeSet<_>>()
            {
                bail!("first registry succession cohort changed");
            }
        } else if records.len() == 1 {
            if changed
                != SECOND_SUCCESSION_CONTROLS
                    .iter()
                    .copied()
                    .collect::<BTreeSet<_>>()
                || edited.len() != 10
                || succession.edits.len() != 10
                || succession.edits.iter().any(|edit| {
                    !SECOND_SUCCESSION_CONTROLS.contains(&edit.module_id.as_str())
                        || !matches!(edit.field.as_str(), "readiness" | "operational_readiness")
                        || edit.new_value != Value::String("COMPLETE".into())
                })
            {
                bail!("second registry succession is not exactly the ten readiness edits");
            }
        } else if changed
            != THIRD_SUCCESSION_CONTROLS
                .iter()
                .copied()
                .collect::<BTreeSet<_>>()
            || edited.len() != 2
            || succession.edits.len() != 2
            || succession.edits.iter().any(|edit| {
                !THIRD_SUCCESSION_CONTROLS.contains(&edit.module_id.as_str())
                    || !matches!(edit.field.as_str(), "readiness" | "operational_readiness")
                    || edit.new_value != Value::String("READY".into())
            })
        {
            bail!("third registry succession is not exactly the two solvency readiness edits");
        }
        records.push(succession);
    }
    let head_archive = root.join(format!(
        "registry/archive/{}/module-manifest.json",
        chain.head_manifest_sha256
    ));
    if fs::read(head_archive)? != fs::read(root.join("module-manifest.json"))? {
        bail!("registry succession head differs from the live manifest");
    }
    Ok((chain, records))
}

fn verify_supersession(module_dir: &Path, module: &str, bundle: &Bundle) -> Result<()> {
    let parents = bundle
        .parents
        .keys()
        .filter(|path| path.ends_with("/supersession.v1.json"))
        .collect::<Vec<_>>();
    if bundle.module_class == "SCIENTIFIC_OR_EVIDENCE" {
        if parents.is_empty() {
            return Ok(());
        }
    }
    if module == "amphora-candidate-contract" {
        if !parents.is_empty() {
            bail!("candidate-contract issuance must not be retrofitted with supersession");
        }
        return Ok(());
    }
    if parents.len() != 1 {
        bail!("reissued deterministic control must bind exactly one supersession record");
    }
    let relative = parents[0];
    let record: Supersession = read_typed(&confined_file(module_dir, relative)?)?;
    let seed = json!({
        "module_id": record.module_id,
        "reason": record.reason,
        "archived_artifacts": record.archived_artifacts,
        "unsigned_preparation_only": record.unsigned_preparation_only,
        "authority_transferred": record.authority_transferred,
    });
    let expected_id = format!("supersession-{}", stable_hash(&seed));
    if record.schema != "amphora.module-phase0-supersession.v1"
        || record.module_id != module
        || record.reason != "STALE_UNSIGNED_PREPARATION_REISSUE"
        || !record.unsigned_preparation_only
        || record.authority_transferred
        || record.supersession_id != expected_id
        || record.archive_root != format!("evidence/superseded/{expected_id}")
        || relative != &format!("{}/supersession.v1.json", record.archive_root)
        || record.archived_artifacts.is_empty()
    {
        bail!("supersession identity, authority boundary, or archive root is invalid");
    }
    let archive = module_dir.join(&record.archive_root);
    let mut observed = BTreeMap::new();
    collect_archive_hashes(&archive.join("phase0"), Path::new("phase0"), &mut observed)?;
    collect_archive_hashes(&archive.join("ip"), Path::new("ip"), &mut observed)?;
    if observed != record.archived_artifacts {
        bail!("supersession archive is incomplete, altered, or cross-module substituted");
    }
    Ok(())
}

fn verify_preparation_ledger(module_dir: &Path, module: &str, bundle: &Bundle) -> Result<()> {
    let ledger_path = module_dir.join("evidence/preparation-revisions/ledger.v1.json");
    let events_dir = module_dir.join("evidence/preparation-revisions/events");
    if !ledger_path.is_file() {
        if events_dir.is_dir() && fs::read_dir(events_dir)?.next().is_some() {
            bail!("preparation revision events exist without a ledger");
        }
        return Ok(());
    }
    let ledger: PreparationLedger = read_typed(&ledger_path)?;
    if ledger.schema != "amphora.module-phase0-preparation-ledger.v1"
        || ledger.module_id != module
        || ledger.revisions.is_empty() != ledger.head_revision_id.is_none()
    {
        bail!("preparation revision ledger identity or head is invalid");
    }
    let mut previous = None;
    let mut referenced = BTreeSet::new();
    let mut revision_ids = BTreeSet::new();
    let mut last = None;
    for (index, reference) in ledger.revisions.iter().enumerate() {
        if !safe_relative_path(&reference.path)
            || !is_hash(&reference.sha256)
            || !referenced.insert(reference.path.clone())
            || !revision_ids.insert(reference.revision_id.clone())
        {
            bail!("preparation revision ledger contains an unsafe or replayed event");
        }
        let path = confined_file(module_dir, &reference.path)?;
        if file_hash(&path)? != reference.sha256 {
            bail!("preparation revision event hash is stale");
        }
        let revision: PreparationRevision = read_typed(&path)?;
        let mut id_seed = revision.clone();
        id_seed.revision_id.clear();
        let expected_id = format!(
            "preparation-revision-{}",
            stable_hash(&serde_json::to_value(id_seed)?)
        );
        if revision.schema != "amphora.module-phase0-preparation-revision.v1"
            || revision.revision_id != expected_id
            || revision.revision_id != reference.revision_id
            || revision.module_id != module
            || revision.revision_number != index as u64 + 1
            || revision.parent_revision_id != previous
            || !revision.unsigned_preparation_only
            || !is_hash(&revision.supersession_sha256)
            || !is_hash(&revision.archived_bundle_sha256)
        {
            bail!("preparation revision chain is mutated, forked, or cross-module");
        }
        verify_preparation_supersession(module_dir, module, &revision)?;
        previous = Some(revision.revision_id.clone());
        last = Some((reference, revision));
    }
    if previous != ledger.head_revision_id {
        bail!("preparation revision ledger has multiple heads");
    }
    let actual = fs::read_dir(&events_dir)?
        .filter_map(|entry| entry.ok().map(|entry| entry.path()))
        .filter(|path| path.extension().and_then(|value| value.to_str()) == Some("json"))
        .map(|path| {
            path.strip_prefix(module_dir)
                .map(|relative| relative.to_string_lossy().replace('\\', "/"))
                .map_err(|_| anyhow!("preparation revision event escapes module"))
        })
        .collect::<Result<BTreeSet<_>>>()?;
    if actual != referenced {
        bail!("preparation revision ledger has an untracked fork");
    }
    if let Some((reference, revision)) = last {
        if bundle.parents.get(&reference.path) != Some(&reference.sha256)
            || bundle.parents.get(&revision.supersession_path)
                != Some(&revision.supersession_sha256)
        {
            bail!("current bundle does not bind the sole preparation revision head");
        }
    }
    Ok(())
}

fn verify_preparation_supersession(
    module_dir: &Path,
    module: &str,
    revision: &PreparationRevision,
) -> Result<()> {
    let path = confined_file(module_dir, &revision.supersession_path)?;
    if file_hash(&path)? != revision.supersession_sha256 {
        bail!("preparation revision supersession hash is stale");
    }
    let record: Supersession = read_typed(&path)?;
    let seed = json!({
        "module_id": record.module_id,
        "reason": record.reason,
        "archived_artifacts": record.archived_artifacts,
        "unsigned_preparation_only": record.unsigned_preparation_only,
        "authority_transferred": record.authority_transferred,
    });
    let expected_id = format!("supersession-{}", stable_hash(&seed));
    if record.schema != "amphora.module-phase0-supersession.v1"
        || record.module_id != module
        || record.supersession_id != revision.supersession_id
        || record.supersession_id != expected_id
        || record.archive_root != format!("evidence/superseded/{expected_id}")
        || revision.supersession_path != format!("{}/supersession.v1.json", record.archive_root)
        || record.reason != "STALE_UNSIGNED_PREPARATION_REISSUE"
        || !record.unsigned_preparation_only
        || record.authority_transferred
        || record.archived_artifacts.keys().any(|path| {
            path == "phase0/benchmark/result.v1.json"
                || path.starts_with("phase0/receipts/") && path.ends_with(".dsse.json")
        })
    {
        bail!("preparation revision claims signed history was unsigned");
    }
    let archive = module_dir.join(&record.archive_root);
    let mut observed = BTreeMap::new();
    collect_archive_hashes(&archive.join("phase0"), Path::new("phase0"), &mut observed)?;
    collect_archive_hashes(&archive.join("ip"), Path::new("ip"), &mut observed)?;
    if observed != record.archived_artifacts
        || file_hash(&archive.join("phase0/bundle.v1.json"))? != revision.archived_bundle_sha256
    {
        bail!("preparation revision archive or archived bundle is altered");
    }
    Ok(())
}

fn collect_archive_hashes(
    directory: &Path,
    relative_root: &Path,
    output: &mut BTreeMap<String, String>,
) -> Result<()> {
    if !directory.is_dir() {
        bail!("supersession archive directory is absent");
    }
    let mut entries = fs::read_dir(directory)?
        .map(|entry| entry.map(|entry| entry.path()))
        .collect::<std::io::Result<Vec<_>>>()?;
    entries.sort();
    for path in entries {
        let metadata = fs::symlink_metadata(&path)?;
        if metadata.file_type().is_symlink() {
            bail!("supersession archive contains a symlink");
        }
        let relative = relative_root.join(
            path.file_name()
                .ok_or_else(|| anyhow!("archive path has no filename"))?,
        );
        if metadata.is_dir() {
            collect_archive_hashes(&path, &relative, output)?;
        } else if metadata.is_file() {
            let relative = relative
                .to_str()
                .ok_or_else(|| anyhow!("archive path is not UTF-8"))?
                .to_owned();
            verify_hash(&relative, &file_hash(&path)?)?;
            if output.insert(relative.clone(), file_hash(&path)?).is_some() {
                bail!("duplicate supersession archive path: {relative}");
            }
        } else {
            bail!("supersession archive contains a non-regular object");
        }
    }
    Ok(())
}

fn verify_claim_contract(module: &str, bundle: &Bundle, contract: &ClaimContract) -> Result<()> {
    let expected_readiness = expected_readiness(bundle)?;
    if contract.schema != "amphora.module-claim-contract.v1"
        || contract.module_id != module
        || contract.registry_manifest_hash != bundle.registry_manifest_hash
        || contract.module_class != bundle.module_class
        || contract.scientific_readiness_ceiling != expected_readiness
        || contract.decision_use_ceiling != "AUDIT_ONLY"
        || contract.applicability_domain != bundle.applicability_domain
        || !contract.abstain_outside_applicability
        || contract.claim_locks != bundle.claim_locks
    {
        bail!("claim contract is inconsistent with the locked Phase-0 bundle");
    }
    verify_zero_authority_locks(&contract.claim_locks)?;
    let prohibited: BTreeSet<_> = contract
        .prohibited_authorities
        .iter()
        .map(String::as_str)
        .collect();
    if PROHIBITED_AUTHORITIES
        .iter()
        .any(|authority| !prohibited.contains(authority))
    {
        bail!("claim contract omits a required authority prohibition");
    }
    Ok(())
}

fn verify_rights(
    module: &str,
    module_dir: &Path,
    bundle: &Bundle,
    value: &Value,
    phase0_trust: &BTreeMap<String, TrustedIdentity>,
) -> Result<()> {
    if value.get("schema").and_then(Value::as_str) == Some("amphora.phase0-source-lock.v2") {
        if bundle.module_class != "SCIENTIFIC_OR_EVIDENCE" {
            bail!("source-lock v2 is reserved for scientific/evidence preparations");
        }
        let lock: SourceLockV2 = serde_json::from_value(value.clone())?;
        let inventory_hash = stable_hash(&json!({
            "eligible_sources": &lock.eligible_sources,
            "excluded_sources": &lock.excluded_sources,
        }));
        if lock.schema != "amphora.phase0-source-lock.v2"
            || lock.module_id != module
            || lock.canonical_home != format!("{module}/evidence/phase0")
            || lock.eligible_sources.is_empty()
            || lock.inventory_hash != inventory_hash
            || !lock.rights_gate_passed
            || lock.candidate_supplied_evidence_allowed
            || lock.legacy_amphora_receipt_authority != "NONE"
        {
            bail!("scientific/evidence source-lock v2 policy is invalid");
        }
        let mut paths = BTreeSet::new();
        let rights_trust = load_rights_trust(
            module_dir
                .parent()
                .ok_or_else(|| anyhow!("reviewed module has no workspace parent"))?,
        )?;
        for source in &lock.eligible_sources {
            let path = confined_file(module_dir, &source.module_relative_path)?;
            let observed = file_hash(&path)?;
            let receipt_path = confined_file(module_dir, &source.rights_receipt_path)?;
            let receipt: RightsReviewReceipt = read_typed(&receipt_path)?;
            let overlay_path = confined_file(module_dir, &source.authorization_overlay_path)?;
            let overlay: AuthorizationOverlay = read_typed(&overlay_path)?;
            if !paths.insert(source.module_relative_path.as_str())
                || observed != source.observed_sha256
                || source.declared_sha256 != observed
                || !source.hash_current
                || file_hash(&receipt_path)? != source.rights_receipt_sha256
                || file_hash(&overlay_path)? != source.authorization_overlay_sha256
                || !source.independently_reviewed
                || overlay.overlay_id != source.authorization_overlay_id
                || overlay.rights_reviewer_key_id != source.rights_reviewer_key_id
                || overlay.module_id != module
                || overlay.artifact_sha256 != observed
                || overlay.authority_ceiling != "AUDIT_ONLY"
                || overlay.scoring_authorized
                || receipt.module_id != module
                || receipt.artifact_sha256 != observed
                || receipt.reviewer_key_id != source.rights_reviewer_key_id
                || phase0_trust.contains_key(&receipt.reviewer_key_id)
            {
                bail!("eligible source lacks a current independently signed rights receipt");
            }
            verify_rights_receipt(&receipt, &rights_trust)?;
            verify_authorization_overlay(
                module,
                module_dir,
                &overlay,
                &receipt,
                &source.authorization_overlay_path,
            )?;
        }
        for source in &lock.excluded_sources {
            let path = confined_file(module_dir, &source.module_relative_path)?;
            if !paths.insert(source.module_relative_path.as_str())
                || file_hash(&path)? != source.observed_sha256
                || source.reason.trim().is_empty()
                || source.authority_ceiling != "CONTEXT_ONLY"
            {
                bail!("excluded source inventory is incomplete or altered");
            }
        }
        return Ok(());
    }
    if bundle.module_class != "DETERMINISTIC_CONTROL" {
        bail!("new scientific/evidence review requires source-lock v2");
    }
    let lock: SourceLock = serde_json::from_value(value.clone())?;
    if lock.schema != "amphora.phase0-source-lock.v1"
        || lock.module_id != module
        || lock.canonical_home != format!("{module}/evidence/phase0")
        || !lock.rights_gate_passed
        || lock.candidate_supplied_evidence_allowed
        || lock.legacy_amphora_receipt_authority != "NONE"
    {
        bail!("deterministic-control rights policy is invalid");
    }
    for source in &lock.sources {
        let path = confined_file(module_dir, &source.module_relative_path)?;
        let observed = file_hash(&path)?;
        let hash_current = source.declared_sha256.as_deref() == Some(observed.as_str());
        if observed != source.observed_sha256 || source.hash_current != hash_current {
            bail!(
                "source hash claim is stale: {}",
                source.module_relative_path
            );
        }
        let license_present = match source.rights_evidence_path.as_deref() {
            Some(path) => path
                .strip_prefix(&format!("{module}/"))
                .and_then(|relative| confined_file(module_dir, relative).ok())
                .is_some(),
            None => false,
        };
        if source.license_present != license_present || source.rights_status.trim().is_empty() {
            bail!(
                "source rights binding is false: {}",
                source.module_relative_path
            );
        }
    }
    for imported in &lock.imported_locks {
        let relative = imported
            .get("module_relative_path")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("imported lock path is absent"))?;
        let declared = imported
            .get("sha256")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("imported lock hash is absent"))?;
        if file_hash(&confined_file(module_dir, relative)?)? != declared {
            bail!("imported lock is stale: {relative}");
        }
    }
    Ok(())
}

fn load_rights_trust(root: &Path) -> Result<BTreeMap<String, TrustedIdentity>> {
    let file: RightsTrustStoreFile =
        read_typed(&root.join("config/rights-review-trust-store.v1.json"))?;
    if file.schema != "amphora.rights-review-trust-store.v1"
        || file.authorization_status != "AUTHORIZED_RIGHTS_REVIEW_IDENTITIES"
        || file.keys.is_empty()
    {
        bail!("rights-review trust store has no authorized identity");
    }
    let mut identities = BTreeMap::new();
    let mut public_keys = BTreeSet::new();
    for row in file.keys {
        if row.algorithm != "Ed25519"
            || row.role != "RIGHTS_REVIEWER"
            || !row.rights_review_authorized
            || row.development
        {
            bail!("rights-review trust store authorizes a development or wrong-role key");
        }
        let bytes = decode_hex_32(&row.public_key_hex)?;
        if row.key_id != format!("rights-reviewer-{}", raw_hash(&bytes))
            || !public_keys.insert(bytes)
        {
            bail!("rights-review identity is duplicated or not hash-bound");
        }
        if row.revoked {
            continue;
        }
        if identities
            .insert(
                row.key_id,
                TrustedIdentity {
                    role: row.role,
                    key: VerifyingKey::from_bytes(&bytes)?,
                },
            )
            .is_some()
        {
            bail!("duplicate rights-review key ID");
        }
    }
    if identities.is_empty() {
        bail!("rights-review trust store has no active identity");
    }
    Ok(identities)
}


fn valid_snapshot_channel(value: &str) -> bool {
    let normalized: String = value.chars().map(|c| if c == '/' || c == '_' { '-' } else { c }).collect();
    normalized == "feedback-v2"
        || normalized.starts_with("feedback-v2-")
        || normalized == "feedback-v3"
        || normalized.starts_with("feedback-v3-")
        || normalized == "feedback-v4"
        || normalized.starts_with("feedback-v4-")
}


fn canonical_snapshot_directory(value: &str) -> Option<&'static str> {
    let normalized: String = value.chars().map(|c| if c == '/' || c == '_' { '-' } else { c }).collect();
    if normalized == "feedback-v2" || normalized.starts_with("feedback-v2-") {
        Some("feedback_v2")
    } else if normalized == "feedback-v3" || normalized.starts_with("feedback-v3-") {
        Some("feedback_v3")
    } else if normalized == "feedback-v4" || normalized.starts_with("feedback-v4-") {
        Some("feedback_v4")
    } else {
        None
    }
}

fn verify_rights_receipt(
    receipt: &RightsReviewReceipt,
    trust: &BTreeMap<String, TrustedIdentity>,
) -> Result<()> {
    let exclusions = receipt
        .exclusions
        .iter()
        .map(String::as_str)
        .collect::<BTreeSet<_>>();
    let mut id_seed = receipt.clone();
    id_seed.receipt_id.clear();
    id_seed.signature = None;
    let expected_id = format!(
        "rights-review-{}",
        stable_hash(&serde_json::to_value(&id_seed)?)
    );
    if receipt.schema != "amphora.rights-review-receipt.v1"
        || receipt.receipt_id != expected_id
        || !valid_snapshot_channel(&receipt.snapshot_id)
        || receipt.dataset_id.trim().is_empty()
        || receipt.acquisition_unit_id.trim().is_empty()
        || receipt.rights_decision_id.trim().is_empty()
        || !is_hash(&receipt.rights_decision_hash)
        || !safe_relative_path(&receipt.artifact_path)
        || !is_hash(&receipt.artifact_sha256)
        || receipt.rights_class != "DERIVATIVE_ALLOWED"
        || receipt.license.trim().is_empty()
        || !receipt.accepted
        || receipt.authority_ceiling != "AUDIT_ONLY"
        || exclusions.len() != receipt.exclusions.len()
        || RIGHTS_EXCLUSIONS
            .iter()
            .any(|required| !exclusions.contains(required))
    {
        bail!("rights-review receipt is malformed or strips an authority exclusion");
    }
    let identity = trust
        .get(&receipt.reviewer_key_id)
        .filter(|identity| identity.role == "RIGHTS_REVIEWER")
        .ok_or_else(|| {
            anyhow!("rights-review receipt uses an unknown, revoked, or wrong-role key")
        })?;
    let envelope = receipt
        .signature
        .as_ref()
        .ok_or_else(|| anyhow!("rights-review receipt is unsigned"))?;
    let mut unsigned = receipt.clone();
    unsigned.signature = None;
    verify_dsse(
        envelope,
        "application/vnd.amphora.rights-review-receipt.v1+json",
        &receipt.reviewer_key_id,
        &identity.key,
        &canonical_bytes(&unsigned)?,
    )
}

fn verify_authorization_overlay(
    module: &str,
    module_dir: &Path,
    overlay: &AuthorizationOverlay,
    receipt: &RightsReviewReceipt,
    overlay_module_relative: &str,
) -> Result<()> {
    let mut id_seed = overlay.clone();
    id_seed.overlay_id.clear();
    let expected_id = format!(
        "authorization-{}",
        stable_hash(&serde_json::to_value(&id_seed)?)
    );
    if overlay.schema != "amphora.module-dataset-authorization-overlay.v1"
        || overlay.overlay_id != expected_id
        || overlay.module_id != module
        || !valid_snapshot_channel(&overlay.snapshot_id)
        || !is_hash(&overlay.activation_hash)
        || !safe_relative_path(&overlay.artifact_path)
        || !is_hash(&overlay.artifact_sha256)
        || !safe_relative_path(&overlay.rights_receipt_path)
        || !is_hash(&overlay.rights_receipt_sha256)
        || overlay.authority_ceiling != "AUDIT_ONLY"
        || overlay.scoring_authorized
        || receipt.snapshot_id != overlay.snapshot_id
        || receipt.dataset_id != overlay.dataset_id
        || receipt.acquisition_unit_id != overlay.acquisition_unit_id
        || receipt.artifact_path != overlay.artifact_path
        || receipt.artifact_sha256 != overlay.artifact_sha256
        || receipt.reviewer_key_id != overlay.rights_reviewer_key_id
    {
        bail!("authorization overlay is stale, cross-module, or scoring-enabled");
    }
    let reference_root = module_dir.join("reference/mvp20").canonicalize()?;
    let artifact = confined_file(&reference_root, &overlay.artifact_path)?;
    let receipt_path = confined_file(&reference_root, &overlay.rights_receipt_path)?;
    if file_hash(&artifact)? != overlay.artifact_sha256
        || file_hash(&receipt_path)? != overlay.rights_receipt_sha256
    {
        bail!("authorization overlay artifact or receipt hash is stale");
    }
    let activation = find_activation_value(&reference_root, overlay)?;
    verify_activation_value(&reference_root, overlay, receipt, &activation)?;
    verify_authorization_ledger(
        &reference_root,
        overlay,
        overlay_module_relative
            .strip_prefix("reference/mvp20/")
            .ok_or_else(|| anyhow!("authorization overlay is outside reference/mvp20"))?,
    )
}

fn find_activation_value(reference_root: &Path, overlay: &AuthorizationOverlay) -> Result<Value> {
    let directory = canonical_snapshot_directory(&overlay.snapshot_id)
        .ok_or_else(|| anyhow!("authorization overlay snapshot_id has no canonical channel"))?;
    let set: Value = read_typed(
        &reference_root
            .join("data")
            .join(directory)
            .join("activation.v1.json"),
    )?;
    if set.get("schema").and_then(Value::as_str) != Some("amphora.module-dataset-activation-set.v1")
        || set.get("module_id").and_then(Value::as_str) != Some(overlay.module_id.as_str())
        || set.get("snapshot_id").and_then(Value::as_str) != Some(overlay.snapshot_id.as_str())
    {
        bail!("activation set identity is stale");
    }
    let matches = set
        .get("activations")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|activation| stable_hash(activation) == overlay.activation_hash)
        .cloned()
        .collect::<Vec<_>>();
    if matches.len() != 1 {
        bail!("authorization overlay has no sole current activation");
    }
    Ok(matches[0].clone())
}

fn verify_activation_value(
    reference_root: &Path,
    overlay: &AuthorizationOverlay,
    receipt: &RightsReviewReceipt,
    activation: &Value,
) -> Result<()> {
    let claim_locks = activation
        .get("claim_locks")
        .and_then(Value::as_object)
        .ok_or_else(|| anyhow!("activation claim locks are absent"))?;
    if activation.get("module_id").and_then(Value::as_str) != Some(overlay.module_id.as_str())
        || activation.get("snapshot_id").and_then(Value::as_str)
            != Some(overlay.snapshot_id.as_str())
        || activation.get("dataset_id").and_then(Value::as_str) != Some(overlay.dataset_id.as_str())
        || activation
            .get("acquisition_unit_id")
            .and_then(Value::as_str)
            != Some(overlay.acquisition_unit_id.as_str())
        || activation
            .get("normalized_object_path")
            .and_then(Value::as_str)
            != Some(overlay.artifact_path.as_str())
        || activation
            .get("normalized_object_sha256")
            .and_then(Value::as_str)
            != Some(overlay.artifact_sha256.as_str())
        || activation.get("rights_class").and_then(Value::as_str) != Some("DERIVATIVE_ALLOWED")
        || activation.get("scoring").and_then(Value::as_bool) != Some(false)
        || activation
            .get("authority_limit")
            .and_then(Value::as_str)
            .is_none_or(str::is_empty)
        || activation.get("zero_network").and_then(Value::as_bool) != Some(true)
        || activation
            .get("candidate_input_excluded")
            .and_then(Value::as_bool)
            != Some(true)
        || activation
            .get("quarantined_row_count")
            .and_then(Value::as_u64)
            != Some(0)
        || claim_locks
            .values()
            .any(|value| value.as_bool() != Some(true))
        || claim_locks
            .get("no_ranking_authority")
            .and_then(Value::as_bool)
            != Some(true)
        || claim_locks
            .get("no_optimizer_authority")
            .and_then(Value::as_bool)
            != Some(true)
    {
        bail!("activation violates rights, quarantine, candidate-path, or scoring policy");
    }
    let catalog_relative = activation
        .get("catalog_path")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("activation catalog path is absent"))?;
    let catalog_path = confined_file(reference_root, catalog_relative)?;
    if file_hash(&catalog_path)?
        != activation
            .get("catalog_sha256")
            .and_then(Value::as_str)
            .unwrap_or_default()
    {
        bail!("activation catalog binding is stale");
    }
    let catalog: Value = read_typed(&catalog_path)?;
    let unit = catalog
        .get("acquisition_units")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .find(|unit| {
            unit.get("acquisition_unit_id").and_then(Value::as_str)
                == Some(overlay.acquisition_unit_id.as_str())
        })
        .ok_or_else(|| anyhow!("activation acquisition unit is absent from catalog"))?;
    let decision_id = unit
        .get("rights_decision_id")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("catalog unit has no rights decision"))?;
    let decision = catalog
        .get("rights_decisions")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .find(|decision| {
            decision.get("rights_decision_id").and_then(Value::as_str) == Some(decision_id)
        })
        .ok_or_else(|| anyhow!("catalog rights decision is absent"))?;
    if decision.get("rights_class").and_then(Value::as_str) != Some("DERIVATIVE_ALLOWED")
        || receipt.rights_decision_id != decision_id
        || receipt.rights_decision_hash != stable_hash(decision)
        || decision.get("license").and_then(Value::as_str) != Some(receipt.license.as_str())
    {
        bail!("rights receipt is not bound to the exact catalog decision");
    }
    Ok(())
}

fn verify_authorization_ledger(
    reference_root: &Path,
    target: &AuthorizationOverlay,
    target_relative: &str,
) -> Result<()> {
    let data_directory = Path::new(target_relative)
        .parent()
        .and_then(Path::parent)
        .ok_or_else(|| anyhow!("authorization event path has no ledger parent"))?;
    let ledger: AuthorizationLedger =
        read_typed(&reference_root.join(data_directory).join("ledger.v1.json"))?;
    if ledger.schema != "amphora.module-dataset-authorization-ledger.v1"
        || ledger.module_id != target.module_id
        || ledger.snapshot_id != target.snapshot_id
        || ledger.overlays.is_empty()
    {
        bail!("authorization ledger identity is invalid");
    }
    let mut previous = None;
    let mut target_count = 0_usize;
    let mut referenced = BTreeSet::new();
    let mut activation_hashes = BTreeSet::new();
    let mut receipt_hashes = BTreeSet::new();
    for row in &ledger.overlays {
        if !safe_relative_path(&row.path)
            || !is_hash(&row.sha256)
            || !referenced.insert(row.path.clone())
        {
            bail!("authorization ledger contains an unsafe or replayed event");
        }
        let path = confined_file(reference_root, &row.path)?;
        if file_hash(&path)? != row.sha256 {
            bail!("authorization ledger event hash is stale");
        }
        let overlay: AuthorizationOverlay = read_typed(&path)?;
        let mut id_seed = overlay.clone();
        id_seed.overlay_id.clear();
        if overlay.overlay_id != row.overlay_id
            || overlay.overlay_id
                != format!(
                    "authorization-{}",
                    stable_hash(&serde_json::to_value(id_seed)?)
                )
            || overlay.module_id != ledger.module_id
            || overlay.snapshot_id != ledger.snapshot_id
            || overlay.parent_overlay_id != previous
            || !activation_hashes.insert(overlay.activation_hash.clone())
            || !receipt_hashes.insert(overlay.rights_receipt_sha256.clone())
        {
            bail!("authorization ledger is forked, replayed, or cross-module");
        }
        if overlay == *target && row.path == target_relative {
            target_count += 1;
        }
        previous = Some(overlay.overlay_id);
    }
    if previous.as_deref() != Some(ledger.head_overlay_id.as_str()) || target_count != 1 {
        bail!("authorization ledger has multiple heads or omits the current overlay");
    }
    let event_directory = reference_root.join(data_directory).join("events");
    let actual = fs::read_dir(event_directory)?
        .filter_map(|entry| entry.ok().map(|entry| entry.path()))
        .filter(|path| path.extension().and_then(|value| value.to_str()) == Some("json"))
        .map(|path| {
            path.strip_prefix(reference_root)
                .map(|relative| relative.to_string_lossy().replace('\\', "/"))
                .map_err(|_| anyhow!("authorization event escapes reference root"))
        })
        .collect::<Result<BTreeSet<_>>>()?;
    if actual != referenced {
        bail!("authorization ledger has an untracked event or fork");
    }
    Ok(())
}

fn safe_relative_path(value: &str) -> bool {
    let path = Path::new(value);
    !value.is_empty()
        && !path.is_absolute()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn is_hash(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn verify_policy(module: &str, bundle: &Bundle, policy: &PromotionPolicy) -> Result<()> {
    let expected_readiness = expected_readiness(bundle)?;
    let roles: BTreeSet<_> = policy
        .required_distinct_roles
        .iter()
        .map(String::as_str)
        .collect();
    let gates: BTreeSet<_> = policy.required_gates.iter().map(String::as_str).collect();
    if policy.schema != "amphora.module-phase0-promotion-policy.v1"
        || policy.module_id != module
        || policy.target_phase != "PHASE_0"
        || policy.target_scientific_readiness != expected_readiness
        || policy.decision_use_ceiling != "AUDIT_ONLY"
        || roles != BTreeSet::from(["PHASE0_EVALUATOR", "PHASE0_INTERNAL_REVIEWER"])
        || policy.required_review_method != REVIEW_METHOD
        || policy.required_independence_scope != INDEPENDENCE_SCOPE
        || policy.human_review_performed
        || policy.local_development_keys_authorized
        || policy.scientific_success_required
        || !gates.contains("INDEPENDENT_REVIEW_SIGNATURE")
        || !gates.contains("CLAIM_LOCKS")
        || !gates.contains("FOLDER_CONFINEMENT")
    {
        bail!("promotion policy weakens the automated dual-service Phase-0 gate");
    }
    if bundle
        .parents
        .contains_key("evidence/phase0/registry/succession.v1.json")
        && !gates.contains("REGISTRY_SUCCESSION")
    {
        bail!("successor-state promotion policy omits registry succession");
    }
    if bundle
        .parents
        .keys()
        .any(|path| path.contains("preparation-revisions/events/"))
        && !gates.contains("PREPARATION_REVISION_LEDGER")
    {
        bail!("promotion policy omits the append-only preparation revision ledger");
    }
    if bundle.module_class == "DETERMINISTIC_CONTROL"
        && module != "amphora-candidate-contract"
        && (!gates.contains("BENCHMARK_EXECUTION_COMPLETE")
            || !gates.contains("MODULE_INVARIANTS")
            || !gates.contains("SUPERSESSION_PROVENANCE")
            || !bundle
                .parents
                .keys()
                .any(|path| path.ends_with("/supersession.v1.json")))
    {
        bail!("current deterministic-control review policy or supersession gate is incomplete");
    }
    if bundle.module_class == "SCIENTIFIC_OR_EVIDENCE"
        && (!gates.contains("BENCHMARK_EXECUTION_COMPLETE")
            || !gates.contains("MODULE_INVARIANTS")
            || !gates.contains("RIGHTS")
            || !gates.contains("TWO_REPLAYS"))
    {
        bail!("scientific/evidence review policy omits a mandatory execution gate");
    }
    Ok(())
}

fn verify_benchmark_lock(module: &str, bundle: &Bundle, lock: &BenchmarkLock) -> Result<()> {
    let expected_runner = if bundle.module_class == "DETERMINISTIC_CONTROL" {
        "NATIVE_WORKSPACE_LOCKED"
    } else {
        "EXACT_LOCKED_MODULE_BENCHMARK"
    };
    let attacks: BTreeSet<_> = lock.attacks.iter().map(String::as_str).collect();
    let module_attacks: &[&str] = match module {
        "amphora-formulation-arithmetic" => &[
            "NUMERIC_TYPE_UNIT_CONFUSION",
            "CANONICAL_LEGACY_ALIAS_COLLISION",
            "FINITE_SUM_OVERFLOW",
            "MASS_ORDER_DRIFT",
            "CANDIDATE_PROPERTY_EVIDENCE_INJECTION",
        ],
        "amphora-formulation-universe" => &[
            "CARTESIAN_CANONICAL_DUPLICATION",
            "CARTESIAN_CARDINALITY_OVERFLOW",
            "INFEASIBLE_INDEX_LAUNDERING",
            "CANDIDATE_FEASIBILITY_CLAIM",
        ],
        "amphora-envelope-gates" => &[
            "ENVELOPE_POLICY_SUBSTITUTION",
            "TRUSTED_FEATURE_SUBSTITUTION",
            "ENVELOPE_BOUND_INVERSION",
            "INCLUSIVE_BOUNDARY_DRIFT",
            "CANDIDATE_GATE_PASS_INJECTION",
        ],
        "amphora-cro-protocol-packager" => &[
            "CRO_IDENTITY_HASH_SUBSTITUTION",
            "INCOMPLETE_PROTOCOL_SECTIONS",
            "CRO_PROSE_WAIVER",
            "CRO_SIGNATURE_DEFECT",
            "FALSE_CRO_EXECUTION",
            "BANNED_CRO_PERFORMANCE_CLAIM",
        ],
        "amphora-optimizer-orchestrator" => &[
            "OBJECTIVE_CONSTRAINT_INJECTION",
            "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
            "DUPLICATE_SCORE_ENVELOPE",
            "MISSING_OPTIMIZER_CLAIM_LOCK",
            "FAILED_OR_NO_AUTHORITY_SCORE",
            "SOLVER_RANKING_ESCALATION",
        ],
        _ => &[],
    };
    if lock.schema != "amphora.module-phase0-benchmark-lock.v1"
        || lock.module_id != module
        || lock.dataset_manifest_sha256 != bundle.dataset_manifest_hash
        || lock.split_manifest_sha256 != bundle.split_manifest_hash
        || lock.runner != expected_runner
        || lock.scientific_success_required_for_phase0
        || lock.negative_result_authority != "AUDIT_ONLY"
        || lock.replay_count != 2
        || REQUIRED_ATTACKS
            .iter()
            .any(|attack| !attacks.contains(attack))
        || (bundle.module_class == "DETERMINISTIC_CONTROL"
            && module != "amphora-candidate-contract"
            && CURRENT_REQUIRED_ATTACKS
                .iter()
                .any(|attack| !attacks.contains(attack)))
        || (module == "amphora-redteam-audit"
            && REDTEAM_ATTACK_AXES
                .iter()
                .any(|attack| !attacks.contains(attack)))
        || module_attacks
            .iter()
            .any(|attack| !attacks.contains(attack))
    {
        bail!("module benchmark lock is incomplete or altered");
    }
    Ok(())
}

fn verify_evaluation(
    trust: &BTreeMap<String, TrustedIdentity>,
    module: &str,
    bundle: &Bundle,
    bundle_path: &Path,
    receipt: &EvaluationReceipt,
    reviewer_key_id: &str,
) -> Result<()> {
    let deterministic = bundle.module_class == "DETERMINISTIC_CONTROL";
    let scientific_outcome_valid = if deterministic {
        receipt.scientific_outcome == "NOT_APPLICABLE"
            && receipt.retained_negative_results.is_empty()
    } else {
        matches!(receipt.scientific_outcome.as_str(), "PASSED" | "FAILED")
            && (receipt.scientific_outcome != "FAILED"
                || !receipt.retained_negative_results.is_empty())
    };
    require_role(trust, &receipt.evaluator_key_id, "PHASE0_EVALUATOR")?;
    if receipt.evaluator_key_id == reviewer_key_id {
        bail!("evaluator and reviewer signing identities are the same");
    }
    if receipt.schema != "amphora.module-phase0-evaluation-receipt.v1"
        || receipt.receipt_id.trim().is_empty()
        || receipt.module_id != module
        || receipt.module_class != bundle.module_class
        || receipt.bundle_hash != file_hash(bundle_path)?
        || receipt.bundle_parent_hashes != bundle.parents
        || !receipt.audit_execution_passed
        || !scientific_outcome_valid
        || !receipt.phase0_eligible
        || receipt.scientific_readiness != expected_readiness(bundle)?
        || receipt.decision_use_ceiling != "AUDIT_ONLY"
        || receipt.claim_lock_hash != stable_hash(&serde_json::to_value(&bundle.claim_locks)?)
        || receipt.applicability_domain != bundle.applicability_domain
        || !receipt.failed_gates.is_empty()
        || (deterministic && !receipt.retained_negative_results.is_empty())
        || (module != "amphora-candidate-contract"
            && receipt.benchmark_execution_complete != Some(true))
    {
        bail!("evaluation receipt does not preserve the Phase-0 zero-authority contract");
    }
    verify_hash("evaluation replay hash", &receipt.replay_hash)?;
    let envelope = receipt
        .signature
        .as_ref()
        .ok_or_else(|| anyhow!("evaluation receipt is unsigned"))?;
    let mut unsigned = receipt.clone();
    unsigned.signature = None;
    verify_dsse(
        envelope,
        EVALUATION_PAYLOAD_TYPE,
        &receipt.evaluator_key_id,
        &trust[&receipt.evaluator_key_id].key,
        &canonical_bytes(&unsigned)?,
    )
}

fn verify_recorded_benchmark(
    module: &str,
    module_dir: &Path,
    bundle: &Bundle,
    receipt: &EvaluationReceipt,
) -> Result<()> {
    let path = module_dir.join("evidence/phase0/benchmark/result.v1.json");
    let result: Value = read_typed(&path)?;
    let recorded_hash = file_hash(&path)?;
    if receipt
        .metrics
        .get("benchmark_result_sha256")
        .and_then(Value::as_str)
        != Some(recorded_hash.as_str())
        || receipt.metrics.get("rights_gate_passed") != Some(&Value::Bool(true))
        || receipt.metrics.get("replay_identical") != Some(&Value::Bool(true))
        || result.get("schema").and_then(Value::as_str)
            != Some("amphora.module-phase0-benchmark-result.v1")
        || result.get("module_id").and_then(Value::as_str) != Some(module)
        || result.get("bundle_sha256").and_then(Value::as_str) != Some(receipt.bundle_hash.as_str())
        || result.get("replay_identical") != Some(&Value::Bool(true))
        || result.get("scientific_outcome").and_then(Value::as_str)
            != Some(receipt.scientific_outcome.as_str())
    {
        bail!("recorded benchmark is not bound to the evaluation receipt");
    }
    let first = result
        .get("first_replay")
        .ok_or_else(|| anyhow!("first evaluated replay is absent"))?;
    let second = result
        .get("second_replay")
        .ok_or_else(|| anyhow!("second evaluated replay is absent"))?;
    if canonical_bytes(first)? != canonical_bytes(second)?
        || first.get("execution_passed") != Some(&Value::Bool(true))
        || first
            .pointer("/diagnostic_receipt/module_id")
            .and_then(Value::as_str)
            != Some(module)
        || first
            .pointer("/diagnostic_receipt/passed")
            .and_then(Value::as_bool)
            .is_none()
        || receipt.replay_hash != stable_hash(&json!({"first": first, "second": second}))
    {
        bail!("evaluated benchmark replays are altered, failing, or non-identical");
    }
    if module != "amphora-candidate-contract"
        && (result.get("benchmark_execution_complete") != Some(&Value::Bool(true))
            || first
                .get("diagnostic_sha256")
                .and_then(Value::as_str)
                .is_none())
    {
        bail!("evaluated benchmark does not prove complete byte-identical execution");
    }
    if bundle.module_class == "DETERMINISTIC_CONTROL" {
        if first.get("scientific_passed") != Some(&Value::Bool(true))
            || first.pointer("/diagnostic_receipt/passed") != Some(&Value::Bool(true))
        {
            bail!("deterministic benchmark replay did not pass");
        }
        verify_module_diagnostic(module, first)?;
    } else {
        let observed = first.get("scientific_passed").and_then(Value::as_bool);
        if observed != Some(receipt.scientific_outcome == "PASSED") {
            bail!("scientific outcome differs from the locked replay");
        }
    }
    Ok(())
}

fn verify_module_diagnostic(module: &str, replay: &Value) -> Result<()> {
    let diagnostic = replay
        .get("diagnostic_receipt")
        .ok_or_else(|| anyhow!("module diagnostic is absent"))?;
    if replay.get("execution_passed") != Some(&Value::Bool(true))
        || diagnostic.get("module_id").and_then(Value::as_str) != Some(module)
        || diagnostic.get("passed") != Some(&Value::Bool(true))
        || diagnostic.get("registry_owned_identity") != Some(&Value::Bool(true))
        || diagnostic.pointer("/metrics/details/artifact_hash_match") != Some(&Value::Bool(true))
        || diagnostic.pointer("/metrics/details/locked_gate_passed") != Some(&Value::Bool(true))
        || diagnostic.pointer("/metrics/details/ranking_quarantine_preserved")
            != Some(&Value::Bool(true))
        || diagnostic.pointer("/metrics/details/registry_identity_match")
            != Some(&Value::Bool(true))
    {
        bail!("module diagnostic fails registry, artifact, gate, or ranking quarantine checks");
    }
    let (readiness, required_locks): (&str, &[&str]) = match module {
        "amphora-candidate-contract" => ("COMPLETE", &[]),
        "amphora-model-card-authority" => (
            "COMPLETE",
            &["authority_registry_is_binding", "failed_cards_cannot_rank"],
        ),
        "amphora-molecule-design-gate" => (
            "READY",
            &[
                "does_not_establish_synthesis_feasibility",
                "does_not_establish_ehs_safety",
                "does_not_establish_procurement",
                "does_not_establish_qualification",
                "does_not_establish_product_performance",
            ],
        ),
        "amphora-run-provenance" => ("COMPLETE", &["run_hash_is_attestation_not_evidence"]),
        "amphora-evidence-intake-validator"
        | "amphora-source-ledger"
        | "amphora-redteam-audit"
        | "amphora-report-packager"
        | "amphora-formulation-arithmetic"
        | "amphora-formulation-universe"
        | "amphora-envelope-gates"
        | "amphora-cro-protocol-packager"
        | "amphora-optimizer-orchestrator" => ("COMPLETE", &[]),
        _ => bail!("unknown reviewer module"),
    };
    if diagnostic
        .pointer("/metrics/details/operational_readiness")
        .and_then(Value::as_str)
        != Some(readiness)
        || required_locks.iter().any(|lock| {
            diagnostic
                .get("claim_locks")
                .and_then(|locks| locks.get(*lock))
                != Some(&Value::Bool(true))
        })
    {
        bail!("module-specific operational readiness or claim lock is absent");
    }
    if FIRST_SUCCESSION_CONTROLS.contains(&module) || SECOND_SUCCESSION_CONTROLS.contains(&module) {
        let live: DeterministicDiagnostic = serde_json::from_value(
            diagnostic
                .pointer("/metrics/details/deterministic_control_diagnostic")
                .cloned()
                .ok_or_else(|| anyhow!("live deterministic diagnostic is absent"))?,
        )?;
        verify_live_diagnostic(module, &live)?;
    }
    Ok(())
}

fn verify_live_diagnostic(module: &str, diagnostic: &DeterministicDiagnostic) -> Result<()> {
    if diagnostic.schema != "amphora.deterministic-control-diagnostic.v1"
        || diagnostic.module_id != module
        || diagnostic.implementation_readiness != "COMPLETE"
        || diagnostic.expected_fixture_outcomes != diagnostic.observed_fixture_outcomes
        || diagnostic.positive_control_count == 0
        || diagnostic.negative_control_count == 0
        || diagnostic.details.is_empty()
        || !diagnostic.passed
    {
        bail!("strict deterministic-control diagnostic contract is invalid");
    }
    verify_zero_authority_locks(&diagnostic.zero_authority_assertions)?;
    if SECOND_SUCCESSION_CONTROLS.contains(&module) {
        verify_promoted_diagnostic_bindings(diagnostic)?;
    }
    match module {
        "amphora-evidence-intake-validator" => verify_evidence_inputs(diagnostic),
        "amphora-source-ledger" => verify_source_inputs(diagnostic),
        "amphora-redteam-audit" => verify_redteam_corpus(diagnostic),
        "amphora-report-packager" => verify_report_inputs(diagnostic),
        "amphora-formulation-arithmetic" => verify_formulation_arithmetic_inputs(diagnostic),
        "amphora-formulation-universe" => verify_formulation_universe_inputs(diagnostic),
        "amphora-envelope-gates" => verify_envelope_gate_inputs(diagnostic),
        "amphora-cro-protocol-packager" => verify_cro_protocol_inputs(diagnostic),
        "amphora-optimizer-orchestrator" => verify_optimizer_inputs(diagnostic),
        _ => bail!("unknown live deterministic control"),
    }
}

fn verify_promoted_diagnostic_bindings(diagnostic: &DeterministicDiagnostic) -> Result<()> {
    let mut details = diagnostic.details.clone();
    let result_digest = details
        .remove("result_digest")
        .and_then(|value| value.as_str().map(str::to_owned))
        .ok_or_else(|| anyhow!("promoted diagnostic result digest is absent"))?;
    let expected_digest = stable_hash(&json!({
        "module_id": diagnostic.module_id,
        "expected_fixture_outcomes": diagnostic.expected_fixture_outcomes,
        "observed_fixture_outcomes": diagnostic.observed_fixture_outcomes,
        "positive_control_count": diagnostic.positive_control_count,
        "negative_control_count": diagnostic.negative_control_count,
        "zero_authority_assertions": diagnostic.zero_authority_assertions,
        "details": details,
        "passed": diagnostic.passed,
    }));
    if result_digest != expected_digest {
        bail!("promoted diagnostic result digest is altered");
    }
    let declared = diagnostic
        .details
        .get("fixture_hashes")
        .and_then(Value::as_object)
        .ok_or_else(|| anyhow!("promoted diagnostic fixture hashes are absent"))?;
    let inputs = diagnostic
        .details
        .get("fixture_inputs")
        .ok_or_else(|| anyhow!("promoted diagnostic fixture inputs are absent"))?;
    let computed = if let Some(rows) = inputs.as_array() {
        rows.iter()
            .map(|row| {
                Ok((
                    row.get("case_id")
                        .and_then(Value::as_str)
                        .ok_or_else(|| anyhow!("fixture case_id is absent"))?
                        .to_owned(),
                    Value::String(stable_hash(row)),
                ))
            })
            .collect::<Result<Map<String, Value>>>()?
    } else if let Some(rows) = inputs.as_object() {
        rows.iter()
            .map(|(case_id, row)| (case_id.clone(), Value::String(stable_hash(row))))
            .collect()
    } else {
        bail!("promoted fixture inputs are not a structured collection");
    };
    if declared != &computed
        || diagnostic.details.get("objective_value_count") != Some(&json!(0))
        || diagnostic.details.get("candidate_created_evidence_count") != Some(&json!(0))
        || diagnostic.details.get("authority_upgrade_count") != Some(&json!(0))
    {
        bail!("fixture hashes or zero-authority output counts are altered");
    }
    Ok(())
}

fn verify_evidence_inputs(diagnostic: &DeterministicDiagnostic) -> Result<()> {
    let inputs = diagnostic
        .details
        .get("fixture_inputs")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("evidence fixture inputs are absent"))?;
    let mut observed = BTreeMap::new();
    for input in inputs {
        let id = input
            .get("package_id")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("evidence fixture ID is absent"))?;
        let checks = input
            .get("checks")
            .ok_or_else(|| anyhow!("evidence checks are absent"))?;
        let accepted = input.get("fixture_only") == Some(&Value::Bool(true))
            && input.get("non_candidate_fixture") == Some(&Value::Bool(true))
            && input.get("candidate_data_created") == Some(&Value::Bool(false))
            && input.get("candidate_evidence") == Some(&Value::Bool(false))
            && input.get("external_closure_claims_allowed") == Some(&Value::Bool(false))
            && input.get("claim_upgrade_allowed") == Some(&Value::Bool(false))
            && checks.get("has_manifest_hash") == Some(&Value::Bool(true))
            && checks.get("all_samples_linked") == Some(&Value::Bool(true))
            && checks.get("computed_values_claimed_measured") == Some(&Value::Bool(false))
            && checks.get("narrative_only") == Some(&Value::Bool(false))
            && checks.get("controls_valid") == Some(&Value::Bool(true))
            && checks.get("raw_file_present") == Some(&Value::Bool(true))
            && checks.get("calibration_present") == Some(&Value::Bool(true))
            && checks.get("ip_fto_claim_made") == Some(&Value::Bool(false))
            && checks.get("physical_validation_claim_made") == Some(&Value::Bool(false))
            && checks.get("supplier_closure_claim_made") == Some(&Value::Bool(false))
            && checks.get("authority_or_procurement_claim_made") == Some(&Value::Bool(false));
        observed.insert(
            id.to_owned(),
            if accepted { "ACCEPT" } else { "REJECT" }.into(),
        );
    }
    if observed != diagnostic.observed_fixture_outcomes
        || diagnostic.positive_control_count != 1
        || diagnostic.negative_control_count != 7
        || diagnostic.details.get("candidate_created_evidence_count") != Some(&json!(0))
        || diagnostic.details.get("authority_upgrade_count") != Some(&json!(0))
    {
        bail!("independent evidence-fixture replay differs from the evaluator");
    }
    Ok(())
}

fn verify_source_inputs(diagnostic: &DeterministicDiagnostic) -> Result<()> {
    let controls: Vec<SourceControlInput> = serde_json::from_value(
        diagnostic
            .details
            .get("control_inputs")
            .cloned()
            .ok_or_else(|| anyhow!("source control inputs are absent"))?,
    )?;
    let mut observed = BTreeMap::from([("current-ledger".into(), "REJECT".into())]);
    for input in controls {
        let accepted = !input.case_id.trim().is_empty()
            && !input.primary_url.trim().is_empty()
            && input.secondary_url.as_deref().is_some_and(|secondary| {
                !secondary.trim().is_empty() && secondary != input.primary_url
            })
            && input.required_fields_complete
            && input.waiver.as_deref().is_none_or(str::is_empty)
            && !(input.source_authority == "PUBLIC" && input.requested_authority != "PUBLIC_AUDIT");
        observed.insert(
            input.case_id,
            if accepted { "ACCEPT" } else { "REJECT" }.into(),
        );
    }
    let summary = diagnostic
        .details
        .get("current_ledger_summary")
        .ok_or_else(|| anyhow!("current source-ledger summary is absent"))?;
    if observed != diagnostic.observed_fixture_outcomes
        || diagnostic.positive_control_count != 1
        || diagnostic.negative_control_count != 5
        || summary.get("load_bearing_constant_count") != Some(&json!(23))
        || summary.get("distinct_dual_source_count") != Some(&json!(9))
        || summary.get("rejected_prose_waiver_count") != Some(&json!(14))
        || summary.get("missing_url_count") != Some(&json!(0))
        || summary.get("complete_source_record_count") != Some(&json!(162))
        || summary.get("incomplete_source_record_count") != Some(&json!(0))
        || summary.get("matches_locked_expected_negative") != Some(&Value::Bool(true))
    {
        bail!("independent source-ledger replay differs from the evaluator");
    }
    Ok(())
}

fn verify_redteam_corpus(diagnostic: &DeterministicDiagnostic) -> Result<()> {
    let mut masks = Vec::with_capacity(30_000);
    let mut unique = BTreeSet::new();
    for axis in 0..REDTEAM_ATTACK_AXES.len() {
        let mask = 1_u32 << axis;
        unique.insert(mask);
        masks.push(mask);
    }
    for left in 0..REDTEAM_ATTACK_AXES.len() {
        for right in (left + 1)..REDTEAM_ATTACK_AXES.len() {
            let mask = (1_u32 << left) | (1_u32 << right);
            unique.insert(mask);
            masks.push(mask);
        }
    }
    let mut mask = 1_u32;
    while masks.len() < 30_000 {
        if mask.count_ones() >= 3 && unique.insert(mask) {
            masks.push(mask);
        }
        mask = mask
            .checked_add(1)
            .ok_or_else(|| anyhow!("red-team mask overflow"))?;
    }
    let mut coverage = vec![false; REDTEAM_ATTACK_AXES.len()];
    let mut pairs = BTreeSet::new();
    let mut digest = Sha256::new();
    for (index, mask) in masks.iter().copied().enumerate() {
        for left in 0..REDTEAM_ATTACK_AXES.len() {
            if mask & (1_u32 << left) != 0 {
                coverage[left] = true;
                for right in (left + 1)..REDTEAM_ATTACK_AXES.len() {
                    if mask & (1_u32 << right) != 0 {
                        pairs.insert((left, right));
                    }
                }
            }
        }
        digest.update(format!("negative-{index:05}:{mask:08x}:REJECT:NONE\n"));
    }
    let corpus_hash = format!("{:x}", digest.finalize());
    if diagnostic.positive_control_count != 1
        || diagnostic.negative_control_count != 30_000
        || unique.len() != 30_000
        || !coverage.iter().all(|covered| *covered)
        || pairs.len() != 276
        || diagnostic.details.get("attack_axes") != Some(&json!(REDTEAM_ATTACK_AXES))
        || diagnostic.details.get("corpus_sha256") != Some(&json!(corpus_hash))
        || diagnostic.details.get("authority_granted_count") != Some(&json!(0))
        || diagnostic.details.get("all_negative_states_rejected") != Some(&Value::Bool(true))
    {
        bail!("independently regenerated red-team corpus differs from the evaluator");
    }
    Ok(())
}

fn verify_report_inputs(diagnostic: &DeterministicDiagnostic) -> Result<()> {
    let fixture = diagnostic
        .details
        .get("fixture_input")
        .ok_or_else(|| anyhow!("report fixture input is absent"))?;
    if !report_fixture_accepted(fixture)?
        || diagnostic.positive_control_count != 1
        || diagnostic.negative_control_count != 5
        || diagnostic.details.get("legacy_accepted_count") != Some(&json!(0))
        || diagnostic.details.get("legacy_signed_count") != Some(&json!(0))
        || diagnostic
            .details
            .get("legacy_documents")
            .and_then(Value::as_array)
            .is_none_or(|rows| {
                rows.len() != 4
                    || rows.iter().any(|row| {
                        row.get("accepted") != Some(&Value::Bool(false))
                            || row.get("signed") != Some(&Value::Bool(false))
                    })
            })
    {
        bail!("independent report fixture replay differs from the evaluator");
    }
    Ok(())
}

fn exact_keys(value: &Value, allowed: &[&str]) -> bool {
    let Some(object) = value.as_object() else {
        return false;
    };
    object.len() == allowed.len() && allowed.iter().all(|field| object.contains_key(*field))
}

fn independently_sum_arithmetic_fixture(input: &Value) -> Result<Option<(f64, f64)>, String> {
    if !exact_keys(
        input,
        &[
            "case_id",
            "part_A",
            "part_a",
            "part_B",
            "part_b",
            "candidate_claims",
        ],
    ) {
        return Err("arithmetic fixture contains unknown or missing fields".into());
    }
    if let Some(claims) = input
        .get("candidate_claims")
        .filter(|value| !value.is_null())
    {
        if !exact_keys(
            claims,
            &[
                "density",
                "eew",
                "ahew",
                "nonvolatile",
                "oil_absorption",
                "performance",
                "evidence",
                "feasibility",
            ],
        ) {
            return Err("candidate claims contain unknown fields".into());
        }
    }
    fn sum_part(input: &Value, canonical: &str, legacy: &str) -> Result<Option<f64>, String> {
        let canonical = input.get(canonical).filter(|value| !value.is_null());
        let legacy = input.get(legacy).filter(|value| !value.is_null());
        if canonical.is_some() && legacy.is_some() {
            return Err("canonical and legacy formulation aliases collide".into());
        }
        let Some(rows) = canonical.or(legacy) else {
            return Ok(None);
        };
        let rows = rows.as_array().ok_or("formulation part is not an array")?;
        let mut masses = BTreeMap::new();
        for row in rows {
            if !exact_keys(row, &["key", "ingredient_id", "mass_g"]) {
                return Err("ingredient fixture contains unknown or missing fields".into());
            }
            let key = row
                .get("key")
                .and_then(Value::as_str)
                .filter(|key| !key.is_empty())
                .ok_or("ingredient key is absent")?;
            if row.get("ingredient_id").and_then(Value::as_str) != Some(key) {
                return Err("ingredient identity mismatch".into());
            }
            let mass = row
                .get("mass_g")
                .and_then(Value::as_f64)
                .filter(|mass| mass.is_finite() && *mass >= 0.0)
                .ok_or("ingredient mass is invalid")?;
            if masses.insert(key, mass).is_some() {
                return Err("duplicate ingredient key".into());
            }
        }
        let positive = masses.values().copied().filter(|mass| *mass > 0.0);
        let mut total = 0.0;
        let mut count = 0;
        for mass in positive {
            total += mass;
            count += 1;
            if !total.is_finite() {
                return Err("finite-input mass sum overflow".into());
            }
        }
        Ok((count != 0).then_some(total))
    }
    let part_a = sum_part(input, "part_A", "part_a")?;
    let part_b = sum_part(input, "part_B", "part_b")?;
    Ok(part_a.zip(part_b))
}

fn verify_formulation_arithmetic_inputs(diagnostic: &DeterministicDiagnostic) -> Result<()> {
    let inputs = diagnostic
        .details
        .get("fixture_inputs")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("arithmetic fixture inputs are absent"))?;
    let results = diagnostic
        .details
        .get("fixture_results")
        .and_then(Value::as_object)
        .ok_or_else(|| anyhow!("arithmetic fixture results are absent"))?;
    let mut observed = BTreeMap::new();
    for input in inputs {
        let case_id = input["case_id"]
            .as_str()
            .ok_or_else(|| anyhow!("arithmetic fixture case_id is absent"))?;
        let recomputed = independently_sum_arithmetic_fixture(input);
        let accepted = matches!(recomputed, Ok(Some((part_a, part_b))) if (part_a + part_b - 150.0).abs() < f64::EPSILON);
        observed.insert(
            case_id.to_owned(),
            if accepted { "ACCEPT" } else { "REJECT" }.into(),
        );
        let recorded = results
            .get(case_id)
            .ok_or_else(|| anyhow!("arithmetic fixture result is absent"))?;
        match recomputed {
            Ok(Some((part_a, part_b))) => {
                if recorded.get("status").and_then(Value::as_str) != Some("UNVALIDATED")
                    || recorded.get("part_a_mass_g").and_then(Value::as_f64) != Some(part_a)
                    || recorded.get("part_b_mass_g").and_then(Value::as_f64) != Some(part_b)
                    || recorded.get("total_mass_g").and_then(Value::as_f64) != Some(part_a + part_b)
                    || recorded
                        .get("objective_values")
                        .and_then(Value::as_object)
                        .is_none_or(|values| !values.is_empty())
                    || recorded.get("ranking_eligible") != Some(&Value::Bool(false))
                    || recorded.get("usable_by_optimizer") != Some(&Value::Bool(false))
                    || recorded.get("unresolved_legacy_data_accessed") != Some(&Value::Bool(false))
                {
                    bail!("arithmetic fixture result differs from independent replay");
                }
            }
            Ok(None) => {
                if recorded.get("status").and_then(Value::as_str) != Some("ABSTAIN") {
                    bail!("missing formulation part did not remain an abstention");
                }
            }
            Err(_) => {
                if recorded.get("error").and_then(Value::as_str).is_none() {
                    bail!("invalid arithmetic fixture did not record rejection");
                }
            }
        }
    }
    if observed != diagnostic.observed_fixture_outcomes
        || diagnostic.positive_control_count != 2
        || diagnostic.negative_control_count != 7
        || diagnostic.details.get("unresolved_legacy_data_open_count") != Some(&json!(0))
    {
        bail!("independent formulation arithmetic replay differs from evaluator");
    }
    Ok(())
}

fn independently_account_universe(input: &Value) -> Result<Option<(u64, u64, u64)>, String> {
    if !exact_keys(input, &["case_id", "axes", "infeasible_indices", "claims"]) {
        return Err("universe fixture contains unknown or missing fields".into());
    }
    let axes = input.get("axes").filter(|value| !value.is_null());
    let indices = input
        .get("infeasible_indices")
        .filter(|value| !value.is_null());
    let Some(axes) = axes else {
        return if indices.is_some() {
            Err("indices require registered axes".into())
        } else {
            Ok(None)
        };
    };
    let axes = axes.as_object().ok_or("universe axes are not an object")?;
    if axes.is_empty() {
        return Err("universe axes are empty".into());
    }
    let mut total = 1_u64;
    for values in axes.values() {
        let values = values.as_array().ok_or("axis values are not an array")?;
        if values.is_empty() {
            return Err("axis values are empty".into());
        }
        let unique = values.iter().map(stable_hash).collect::<BTreeSet<_>>();
        if unique.len() != values.len() {
            return Err("axis values contain canonical duplicates".into());
        }
        total = total
            .checked_mul(values.len() as u64)
            .filter(|total| *total <= 10_000)
            .ok_or("universe cardinality overflow")?;
    }
    let mut infeasible = BTreeSet::new();
    if let Some(indices) = indices {
        for index in indices.as_array().ok_or("indices are not an array")? {
            let index = index.as_u64().ok_or("index is not unsigned")?;
            if index >= total || !infeasible.insert(index) {
                return Err("index is duplicate or out of range".into());
            }
        }
    }
    let infeasible = infeasible.len() as u64;
    Ok(Some((total - infeasible, infeasible, total)))
}

fn verify_formulation_universe_inputs(diagnostic: &DeterministicDiagnostic) -> Result<()> {
    let inputs = diagnostic
        .details
        .get("fixture_inputs")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("universe fixture inputs are absent"))?;
    let results = diagnostic
        .details
        .get("fixture_results")
        .and_then(Value::as_object)
        .ok_or_else(|| anyhow!("universe fixture results are absent"))?;
    let mut observed = BTreeMap::new();
    for input in inputs {
        let case_id = input["case_id"]
            .as_str()
            .ok_or_else(|| anyhow!("universe fixture case_id is absent"))?;
        let recomputed = independently_account_universe(input);
        let accepted = matches!(recomputed, Ok(Some((10, 2, 12))));
        observed.insert(
            case_id.to_owned(),
            if accepted { "ACCEPT" } else { "REJECT" }.into(),
        );
        let recorded = results
            .get(case_id)
            .ok_or_else(|| anyhow!("universe fixture result is absent"))?;
        match recomputed {
            Ok(Some((solved, infeasible, total))) => {
                if recorded.get("status").and_then(Value::as_str) != Some("UNVALIDATED")
                    || recorded.get("cartesian_total").and_then(Value::as_u64) != Some(total)
                    || recorded
                        .get("solved_candidate_count")
                        .and_then(Value::as_u64)
                        != Some(solved)
                    || recorded
                        .get("infeasible_candidate_count")
                        .and_then(Value::as_u64)
                        != Some(infeasible)
                    || recorded.get("feasibility_basis").and_then(Value::as_str)
                        != Some("DECLARATIVE_ACCOUNTING_ONLY")
                    || recorded.get("usable_by_optimizer") != Some(&Value::Bool(false))
                {
                    bail!("universe accounting differs from independent replay");
                }
            }
            Ok(None) => {
                if recorded.get("status").and_then(Value::as_str) != Some("ABSTAIN") {
                    bail!("missing universe axes did not remain an abstention");
                }
            }
            Err(_) => {
                if recorded.get("error").and_then(Value::as_str).is_none() {
                    bail!("invalid universe fixture did not record rejection");
                }
            }
        }
    }
    if observed != diagnostic.observed_fixture_outcomes
        || diagnostic.positive_control_count != 2
        || diagnostic.negative_control_count != 9
        || diagnostic.details.get("unresolved_legacy_data_open_count") != Some(&json!(0))
    {
        bail!("independent formulation universe replay differs from evaluator");
    }
    Ok(())
}

fn independently_evaluate_envelope(
    input: &Value,
) -> Result<(String, bool, BTreeMap<String, f64>), String> {
    if !exact_keys(
        input,
        &["case_id", "policy", "snapshot", "candidate_claims"],
    ) {
        return Err("envelope fixture contains unknown or missing fields".into());
    }
    if input
        .get("candidate_claims")
        .is_some_and(|claims| !claims.is_null())
    {
        return Err("candidate gate or authority claims are forbidden".into());
    }
    let policy = input.get("policy").filter(|value| !value.is_null());
    let snapshot = input.get("snapshot").filter(|value| !value.is_null());
    let (Some(policy), Some(snapshot)) = (policy, snapshot) else {
        return Ok(("ABSTAIN".into(), false, BTreeMap::new()));
    };
    if !exact_keys(
        policy,
        &[
            "schema",
            "policy_id",
            "fixture_only",
            "authoritative",
            "constraints",
        ],
    ) || policy.get("schema").and_then(Value::as_str)
        != Some("amphora.synthetic-envelope-policy.v1")
        || policy.get("fixture_only") != Some(&Value::Bool(true))
        || policy.get("authoritative") != Some(&Value::Bool(false))
        || !exact_keys(snapshot, &["schema", "trusted", "values"])
        || snapshot.get("schema").and_then(Value::as_str)
            != Some("amphora.trusted-arithmetic-snapshot.v1")
        || snapshot.get("trusted") != Some(&Value::Bool(true))
    {
        return Err("synthetic envelope policy or trusted snapshot is malformed".into());
    }
    let constraints = policy["constraints"]
        .as_array()
        .ok_or("envelope constraints are not an array")?;
    if constraints.is_empty() {
        return Err("envelope constraints are empty".into());
    }
    let values = snapshot["values"]
        .as_object()
        .ok_or("snapshot values are not an object")?;
    let known = BTreeSet::from(["mass.part_A_g", "mass.part_B_g", "mass.total_g"]);
    let mut seen = BTreeSet::new();
    let mut margins = BTreeMap::new();
    let mut passed = true;
    for constraint in constraints {
        if !exact_keys(
            constraint,
            &[
                "constraint_id",
                "feature_path",
                "unit",
                "lower_inclusive",
                "upper_inclusive",
            ],
        ) {
            return Err("envelope constraint fields are incomplete".into());
        }
        let id = constraint["constraint_id"]
            .as_str()
            .filter(|id| !id.is_empty())
            .ok_or("constraint ID is absent")?;
        let path = constraint["feature_path"]
            .as_str()
            .ok_or("constraint path is absent")?;
        if !seen.insert(id) || !known.contains(path) {
            return Err("constraint is duplicate or unknown".into());
        }
        let lower = constraint["lower_inclusive"]
            .as_f64()
            .filter(|value| value.is_finite())
            .ok_or("lower bound is invalid")?;
        let upper = constraint["upper_inclusive"]
            .as_f64()
            .filter(|value| value.is_finite())
            .ok_or("upper bound is invalid")?;
        if lower > upper {
            return Err("bounds are inverted".into());
        }
        let feature = values.get(path).ok_or("trusted feature is absent")?;
        if !exact_keys(feature, &["value", "unit"]) || feature.get("unit") != constraint.get("unit")
        {
            return Err("dimensioned feature unit mismatch".into());
        }
        let value = feature["value"]
            .as_f64()
            .filter(|value| value.is_finite())
            .ok_or("dimensioned feature is invalid")?;
        let margin = (value - lower).min(upper - value);
        passed &= margin >= 0.0;
        margins.insert(id.to_owned(), margin);
    }
    Ok((
        if passed {
            "UNVALIDATED"
        } else {
            "FAILED_GATES"
        }
        .into(),
        passed,
        margins,
    ))
}

fn verify_envelope_gate_inputs(diagnostic: &DeterministicDiagnostic) -> Result<()> {
    let inputs = diagnostic
        .details
        .get("fixture_inputs")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("envelope fixture inputs are absent"))?;
    let results = diagnostic
        .details
        .get("fixture_results")
        .and_then(Value::as_object)
        .ok_or_else(|| anyhow!("envelope fixture results are absent"))?;
    let mut observed = BTreeMap::new();
    for input in inputs {
        let case_id = input["case_id"]
            .as_str()
            .ok_or_else(|| anyhow!("envelope fixture case_id is absent"))?;
        let recomputed = independently_evaluate_envelope(input);
        let accepted = matches!(recomputed, Ok((ref status, true, _)) if status == "UNVALIDATED");
        observed.insert(
            case_id.to_owned(),
            if accepted { "ACCEPT" } else { "REJECT" }.into(),
        );
        let recorded = results
            .get(case_id)
            .ok_or_else(|| anyhow!("envelope fixture result is absent"))?;
        match recomputed {
            Ok((status, passed, margins)) => {
                let recorded_margins: BTreeMap<String, f64> = serde_json::from_value(
                    recorded
                        .get("margins")
                        .cloned()
                        .ok_or_else(|| anyhow!("envelope margins are absent"))?,
                )?;
                if recorded.get("status").and_then(Value::as_str) != Some(&status)
                    || recorded.get("pass_all_hard") != Some(&Value::Bool(passed))
                    || recorded_margins != margins
                    || recorded.get("wet_lab_evidence_created") != Some(&Value::Bool(false))
                    || recorded.get("qualification_evidence_created") != Some(&Value::Bool(false))
                    || recorded.get("release_evidence_created") != Some(&Value::Bool(false))
                    || recorded.get("product_evidence_created") != Some(&Value::Bool(false))
                    || recorded.get("usable_by_optimizer") != Some(&Value::Bool(false))
                {
                    bail!("envelope result differs from independent arithmetic replay");
                }
            }
            Err(_) => {
                if recorded.get("error").and_then(Value::as_str).is_none() {
                    bail!("invalid envelope fixture did not record rejection");
                }
            }
        }
    }
    if observed != diagnostic.observed_fixture_outcomes
        || diagnostic.positive_control_count != 2
        || diagnostic.negative_control_count != 9
        || diagnostic.details.get("synthetic_policy_authoritative") != Some(&Value::Bool(false))
        || diagnostic
            .details
            .get("runtime_without_trusted_inputs_abstains")
            != Some(&Value::Bool(true))
    {
        bail!("independent envelope-gate replay differs from evaluator");
    }
    Ok(())
}

fn reviewer_render_protocol(payload: &Value) -> Result<String> {
    let mut output =
        format!(
        "# Locked CRO fixture {}\n\nCandidate SHA-256: `{}`\nFormula SHA-256: `{}`\n\n## Recipe\n",
        payload["fixture_id"].as_str().ok_or_else(|| anyhow!("fixture ID absent"))?,
        payload["candidate_sha256"].as_str().ok_or_else(|| anyhow!("candidate hash absent"))?,
        payload["formula_sha256"].as_str().ok_or_else(|| anyhow!("formula hash absent"))?,
    );
    for step in payload["recipe_steps"]
        .as_array()
        .ok_or_else(|| anyhow!("recipe steps absent"))?
    {
        output.push_str(&format!(
            "{}. {} {} {} {} (tolerance -{}/+{})\n",
            step["sequence"]
                .as_u64()
                .ok_or_else(|| anyhow!("sequence absent"))?,
            step["action"]
                .as_str()
                .ok_or_else(|| anyhow!("action absent"))?,
            step["ingredient_id"]
                .as_str()
                .ok_or_else(|| anyhow!("ingredient absent"))?,
            step["amount"]
                .as_f64()
                .ok_or_else(|| anyhow!("amount absent"))?,
            step["unit"]
                .as_str()
                .ok_or_else(|| anyhow!("unit absent"))?,
            step["tolerance"]["minus"]
                .as_f64()
                .ok_or_else(|| anyhow!("minus tolerance absent"))?,
            step["tolerance"]["plus"]
                .as_f64()
                .ok_or_else(|| anyhow!("plus tolerance absent"))?,
        ));
    }
    output.push_str("\n## Controls\n");
    for control in payload["controls"]
        .as_array()
        .ok_or_else(|| anyhow!("controls absent"))?
    {
        output.push_str(&format!(
            "- {} [{}]: {}\n",
            control["control_id"]
                .as_str()
                .ok_or_else(|| anyhow!("control ID absent"))?,
            control["control_type"]
                .as_str()
                .ok_or_else(|| anyhow!("control type absent"))?,
            control["treatment"]
                .as_str()
                .ok_or_else(|| anyhow!("control treatment absent"))?,
        ));
    }
    for (heading, field) in [
        ("Decision rules", "decision_rules"),
        ("Early-kill rules", "early_kill_rules"),
    ] {
        output.push_str(&format!("\n## {heading}\n"));
        for rule in payload[field]
            .as_array()
            .ok_or_else(|| anyhow!("protocol rules absent"))?
        {
            output.push_str(&format!(
                "- {} {} {} {} => {}\n",
                rule["metric"]
                    .as_str()
                    .ok_or_else(|| anyhow!("rule metric absent"))?,
                rule["operator"]
                    .as_str()
                    .ok_or_else(|| anyhow!("rule operator absent"))?,
                rule["threshold"]
                    .as_f64()
                    .ok_or_else(|| anyhow!("rule threshold absent"))?,
                rule["unit"]
                    .as_str()
                    .ok_or_else(|| anyhow!("rule unit absent"))?,
                rule["outcome"]
                    .as_str()
                    .ok_or_else(|| anyhow!("rule outcome absent"))?,
            ));
        }
    }
    output.push_str("\n## Required outputs\n");
    for required in payload["required_outputs"]
        .as_array()
        .ok_or_else(|| anyhow!("outputs absent"))?
    {
        output.push_str(&format!(
            "- {}\n",
            required
                .as_str()
                .ok_or_else(|| anyhow!("output name invalid"))?
        ));
    }
    output.push_str("\n## Authority lock\n");
    let locks: BTreeMap<String, bool> = serde_json::from_value(payload["authority_lock"].clone())?;
    for (lock, enabled) in &locks {
        output.push_str(&format!("- {lock}: {enabled}\n"));
    }
    output.push_str(&format!(
        "\nScientific readiness: {}\nDecision use: {}\nRanking eligible: {}\nLab execution: {}\n",
        payload["scientific_readiness"]
            .as_str()
            .ok_or_else(|| anyhow!("readiness absent"))?,
        payload["decision_use_ceiling"]
            .as_str()
            .ok_or_else(|| anyhow!("decision use absent"))?,
        payload["ranking_eligible"]
            .as_bool()
            .ok_or_else(|| anyhow!("ranking flag absent"))?,
        payload["lab_execution_status"]
            .as_str()
            .ok_or_else(|| anyhow!("execution status absent"))?,
    ));
    Ok(output)
}

fn reviewer_protocol_fixture_accepted(fixture: &Value) -> Result<bool> {
    if !exact_keys(fixture, &["schema", "payload", "signature"])
        || fixture["schema"].as_str() != Some("amphora.cro-protocol-known-answer.v1")
    {
        return Ok(false);
    }
    let payload = &fixture["payload"];
    let payload_fields = [
        "fixture_id",
        "fixture_only",
        "authoritative",
        "candidate",
        "candidate_sha256",
        "formula_sha256",
        "recipe_steps",
        "controls",
        "randomization",
        "blinding",
        "custody",
        "power_analysis",
        "decision_rules",
        "early_kill_rules",
        "required_outputs",
        "narrative",
        "canonical_rendering",
        "authority_lock",
        "scientific_readiness",
        "decision_use_ceiling",
        "ranking_eligible",
        "lab_execution_status",
        "results",
    ];
    if !exact_keys(payload, &payload_fields)
        || payload["fixture_only"] != Value::Bool(true)
        || payload["authoritative"] != Value::Bool(false)
        || payload["candidate_sha256"].as_str() != Some(stable_hash(&payload["candidate"]).as_str())
        || payload["formula_sha256"].as_str()
            != Some(stable_hash(&payload["recipe_steps"]).as_str())
        || payload["scientific_readiness"].as_str() != Some("UNVALIDATED")
        || payload["decision_use_ceiling"].as_str() != Some("AUDIT_ONLY")
        || payload["ranking_eligible"] != Value::Bool(false)
        || payload["lab_execution_status"].as_str() != Some("NOT_EXECUTED")
        || !payload["results"].is_null()
    {
        return Ok(false);
    }
    let locks: BTreeMap<String, bool> = serde_json::from_value(payload["authority_lock"].clone())?;
    let rendered = match reviewer_render_protocol(payload) {
        Ok(text) => text,
        Err(_) => return Ok(false),
    };
    if verify_zero_authority_locks(&locks).is_err()
        || payload["canonical_rendering"].as_str() != Some(rendered.as_str())
        || payload["narrative"].as_array().is_none_or(|rows| {
            rows.iter()
                .any(|row| row.as_str().is_none_or(contains_banned_claim))
        })
    {
        return Ok(false);
    }
    let steps = payload["recipe_steps"]
        .as_array()
        .ok_or_else(|| anyhow!("recipe absent"))?;
    if steps.is_empty()
        || steps.iter().enumerate().any(|(index, step)| {
            !exact_keys(
                step,
                &[
                    "sequence",
                    "action",
                    "ingredient_id",
                    "amount",
                    "unit",
                    "tolerance",
                ],
            ) || step["sequence"].as_u64() != Some(index as u64 + 1)
                || step["action"].as_str().is_none_or(str::is_empty)
                || step["ingredient_id"].as_str().is_none_or(str::is_empty)
                || step["amount"]
                    .as_f64()
                    .is_none_or(|value| !value.is_finite() || value <= 0.0)
                || !matches!(step["unit"].as_str(), Some("g" | "mL" | "min" | "degC"))
                || !exact_keys(&step["tolerance"], &["minus", "plus"])
                || ["minus", "plus"].iter().any(|field| {
                    step["tolerance"][*field]
                        .as_f64()
                        .is_none_or(|value| !value.is_finite() || value < 0.0)
                })
        })
        || payload["controls"].as_array().is_none_or(Vec::is_empty)
        || !exact_keys(&payload["randomization"], &["method", "seed_source"])
        || payload["randomization"]["method"]
            .as_str()
            .is_none_or(str::is_empty)
        || payload["randomization"]["seed_source"]
            .as_str()
            .is_none_or(str::is_empty)
        || !exact_keys(&payload["blinding"], &["enabled", "masked_fields"])
        || payload["blinding"]["enabled"] != Value::Bool(true)
        || payload["blinding"]["masked_fields"]
            .as_array()
            .is_none_or(Vec::is_empty)
        || !exact_keys(
            &payload["custody"],
            &[
                "sample_ids_required",
                "handoffs",
                "tamper_evidence_required",
            ],
        )
        || payload["custody"]["sample_ids_required"] != Value::Bool(true)
        || payload["custody"]["tamper_evidence_required"] != Value::Bool(true)
        || payload["custody"]["handoffs"]
            .as_array()
            .is_none_or(Vec::is_empty)
        || !exact_keys(
            &payload["power_analysis"],
            &["effect_size", "alpha", "power", "replicates_per_arm"],
        )
        || payload["power_analysis"]["replicates_per_arm"]
            .as_u64()
            .is_none_or(|value| value == 0)
        || payload["power_analysis"]["power"]
            .as_f64()
            .is_none_or(|value| value < 0.8)
    {
        return Ok(false);
    }
    for field in ["decision_rules", "early_kill_rules"] {
        let Some(rules) = payload[field].as_array() else {
            return Ok(false);
        };
        if rules.is_empty()
            || rules.iter().any(|rule| {
                !exact_keys(
                    rule,
                    &["metric", "operator", "threshold", "unit", "outcome"],
                ) || rule["metric"].as_str().is_none_or(str::is_empty)
                    || !matches!(
                        rule["operator"].as_str(),
                        Some("==" | "!=" | ">=" | "<=" | ">" | "<")
                    )
                    || rule["threshold"]
                        .as_f64()
                        .is_none_or(|value| !value.is_finite())
                    || rule["unit"].as_str().is_none_or(str::is_empty)
                    || rule["outcome"].as_str().is_none_or(str::is_empty)
            })
        {
            return Ok(false);
        }
    }
    let signature = &fixture["signature"];
    if !exact_keys(
        signature,
        &[
            "algorithm",
            "key_id",
            "public_key_hex",
            "signature_hex",
            "candidate_supplied",
        ],
    ) || signature["algorithm"].as_str() != Some("Ed25519")
        || signature["candidate_supplied"] != Value::Bool(false)
    {
        return Ok(false);
    }
    let public = decode_hex_32(
        signature["public_key_hex"]
            .as_str()
            .ok_or_else(|| anyhow!("CRO public key absent"))?,
    )?;
    if signature["key_id"].as_str() != Some(format!("cro-fixture-{}", raw_hash(&public)).as_str()) {
        return Ok(false);
    }
    let signature_bytes = decode_hex_64(
        signature["signature_hex"]
            .as_str()
            .ok_or_else(|| anyhow!("CRO signature absent"))?,
    )?;
    let key = VerifyingKey::from_bytes(&public)?;
    Ok(key
        .verify(
            &serde_json::to_vec(&canonicalize(payload))?,
            &Signature::from_bytes(&signature_bytes),
        )
        .is_ok())
}

fn verify_cro_protocol_inputs(diagnostic: &DeterministicDiagnostic) -> Result<()> {
    let inputs = diagnostic
        .details
        .get("fixture_inputs")
        .and_then(Value::as_object)
        .ok_or_else(|| anyhow!("CRO fixture inputs are absent"))?;
    let observed = inputs
        .iter()
        .map(|(case_id, fixture)| {
            Ok((
                case_id.clone(),
                if reviewer_protocol_fixture_accepted(fixture)? {
                    "ACCEPT"
                } else {
                    "REJECT"
                }
                .into(),
            ))
        })
        .collect::<Result<BTreeMap<_, _>>>()?;
    let legacy = diagnostic
        .details
        .get("legacy_artifacts")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("legacy CRO artifacts are absent"))?;
    if observed != diagnostic.observed_fixture_outcomes
        || diagnostic.positive_control_count != 1
        || diagnostic.negative_control_count != 9
        || diagnostic.details.get("lab_execution_status") != Some(&json!("NOT_EXECUTED"))
        || diagnostic.details.get("legacy_accepted_count") != Some(&json!(0))
        || diagnostic.details.get("legacy_signed_count") != Some(&json!(0))
        || legacy.len() != 3
        || legacy.iter().any(|row| {
            row.get("accepted") != Some(&Value::Bool(false))
                || row.get("signed") != Some(&Value::Bool(false))
        })
    {
        bail!("independent CRO protocol replay differs from evaluator");
    }
    Ok(())
}

fn independent_optimizer_authorization(input: &Value) -> Result<Value, String> {
    if !exact_keys(input, &["case_id", "request", "envelopes", "policy"]) {
        return Err("optimizer fixture contains unknown or missing fields".into());
    }
    let expected_modules = BTreeSet::from([
        "amphora-barrier-corrosion-score",
        "amphora-candidate-contract",
        "amphora-cro-protocol-packager",
        "amphora-cure-potlife-gate",
        "amphora-design-rule-score",
        "amphora-envelope-gates",
        "amphora-evidence-intake-validator",
        "amphora-formulation-arithmetic",
        "amphora-formulation-universe",
        "amphora-ingredient-library",
        "amphora-ip-fto-guard",
        "amphora-known-answer-benchmarks",
        "amphora-model-card-authority",
        "amphora-molecule-design-gate",
        "amphora-molecule-generator",
        "amphora-molecule-novelty",
        "amphora-molecule-property",
        "amphora-molecule-role-ranker",
        "amphora-optimizer-orchestrator",
        "amphora-process-qc-twin",
        "amphora-public-corrosion-benchmark",
        "amphora-redteam-audit",
        "amphora-report-packager",
        "amphora-run-provenance",
        "amphora-solvency-score",
        "amphora-source-ledger",
        "amphora-sourceability-ehs",
        "amphora-tolerance-robustness",
        "amphora-viscosity-score",
    ]);
    let policy = &input["policy"];
    if !exact_keys(
        policy,
        &[
            "schema",
            "registered_modules",
            "ranking_enabled",
            "solver_enabled",
            "authority_expansion_allowed",
            "decision_use_ceiling",
            "required_claim_locks",
        ],
    ) || policy["schema"].as_str() != Some("amphora.optimizer-registry-policy.v1")
        || policy["ranking_enabled"] != Value::Bool(false)
        || policy["solver_enabled"] != Value::Bool(false)
        || policy["authority_expansion_allowed"] != Value::Bool(false)
        || policy["decision_use_ceiling"].as_str() != Some("AUDIT_ONLY")
    {
        return Err("optimizer registry policy is altered".into());
    }
    let registered_rows = policy["registered_modules"]
        .as_array()
        .ok_or("registered modules absent")?;
    let registered = registered_rows
        .iter()
        .filter_map(Value::as_str)
        .collect::<BTreeSet<_>>();
    if registered_rows.len() != 29 || registered != expected_modules {
        return Err("optimizer registry modules are unknown or duplicated".into());
    }
    let required_rows = policy["required_claim_locks"]
        .as_array()
        .ok_or("required locks absent")?;
    let required = required_rows
        .iter()
        .filter_map(Value::as_str)
        .collect::<BTreeSet<_>>();
    if required_rows.len() != ZERO_AUTHORITY_LOCKS.len()
        || required != ZERO_AUTHORITY_LOCKS.into_iter().collect()
    {
        return Err("optimizer registry locks are incomplete".into());
    }
    let request = &input["request"];
    if !exact_keys(
        request,
        &["schema", "request_source", "objectives", "hard_constraints"],
    ) || request["schema"].as_str() != Some("amphora.optimizer-authorization-request.v1")
        || !matches!(
            request["request_source"].as_str(),
            Some("POLICY" | "CANDIDATE")
        )
    {
        return Err("optimizer request is malformed".into());
    }
    let objectives = request["objectives"]
        .as_array()
        .ok_or("objectives absent")?;
    if request["request_source"].as_str() == Some("CANDIDATE") && !objectives.is_empty() {
        return Err("candidate objective injection".into());
    }
    let mut objective_ids = BTreeSet::new();
    for objective in objectives {
        if !exact_keys(objective, &["objective_id", "module_id", "section", "path"])
            || !objective["objective_id"]
                .as_str()
                .is_some_and(|id| objective_ids.insert(id))
            || !objective["module_id"]
                .as_str()
                .is_some_and(|module| registered.contains(module))
            || objective["section"].as_str() != Some("objective_values")
            || objective["path"].as_str().is_none_or(str::is_empty)
        {
            return Err("optimizer objective is malformed or unknown".into());
        }
    }
    let envelopes = input["envelopes"]
        .as_array()
        .ok_or("optimizer envelopes absent")?;
    let mut by_module = BTreeMap::new();
    for envelope in envelopes {
        if !exact_keys(
            envelope,
            &[
                "module_id",
                "status",
                "authority_tier",
                "solver_use_ceiling",
                "ranking_eligible",
                "usable_by_optimizer",
                "objective_values",
                "gates",
                "claim_locks",
            ],
        ) {
            return Err("optimizer envelope fields are incomplete".into());
        }
        let module = envelope["module_id"]
            .as_str()
            .ok_or("envelope module absent")?;
        if !registered.contains(module) || by_module.insert(module, envelope).is_some() {
            return Err("optimizer envelope module is unknown or duplicated".into());
        }
        let locks: BTreeMap<String, bool> = serde_json::from_value(envelope["claim_locks"].clone())
            .map_err(|error| error.to_string())?;
        if envelope["ranking_eligible"] != Value::Bool(false)
            || envelope["usable_by_optimizer"] != Value::Bool(false)
            || envelope["objective_values"]
                .as_object()
                .is_none_or(|values| !values.is_empty())
            || !matches!(
                envelope["solver_use_ceiling"].as_str(),
                Some("DISABLED" | "AUDIT_ONLY" | "CONSTRAINT_ONLY")
            )
            || matches!(
                envelope["authority_tier"].as_str(),
                None | Some("" | "RANKING" | "OPTIMIZER" | "PRODUCTION")
            )
            || required
                .iter()
                .any(|lock| locks.get(*lock).copied() != Some(true))
        {
            return Err("optimizer envelope escalates score, authority, solver, or locks".into());
        }
    }
    let constraints = request["hard_constraints"]
        .as_array()
        .ok_or("constraints absent")?;
    let mut constraint_ids = BTreeSet::new();
    for constraint in constraints {
        if !exact_keys(
            constraint,
            &[
                "constraint_id",
                "module_id",
                "section",
                "path",
                "operator",
                "expected",
            ],
        ) || !constraint["constraint_id"]
            .as_str()
            .is_some_and(|id| constraint_ids.insert(id))
            || !constraint["module_id"]
                .as_str()
                .is_some_and(|module| registered.contains(module))
            || constraint["section"].as_str() != Some("gates")
            || constraint["path"].as_str().is_none_or(str::is_empty)
            || !matches!(
                constraint["operator"].as_str(),
                Some("==" | "!=" | ">=" | "<=" | ">" | "<")
            )
        {
            return Err("optimizer constraint is malformed or unknown".into());
        }
        let module = constraint["module_id"].as_str().unwrap();
        let envelope = by_module.get(module).ok_or("constraint envelope absent")?;
        if envelope["status"].as_str() != Some("SCORED") {
            return Err("constraint envelope is not SCORED".into());
        }
        let mut actual = &envelope["gates"];
        for part in constraint["path"].as_str().unwrap().split('.') {
            actual = actual.get(part).ok_or("constraint path unknown")?;
        }
        let expected = &constraint["expected"];
        let pass = match constraint["operator"].as_str().unwrap() {
            "==" => actual == expected,
            "!=" => actual != expected,
            ">=" => actual
                .as_f64()
                .zip(expected.as_f64())
                .is_some_and(|(a, b)| a >= b),
            "<=" => actual
                .as_f64()
                .zip(expected.as_f64())
                .is_some_and(|(a, b)| a <= b),
            ">" => actual
                .as_f64()
                .zip(expected.as_f64())
                .is_some_and(|(a, b)| a > b),
            "<" => actual
                .as_f64()
                .zip(expected.as_f64())
                .is_some_and(|(a, b)| a < b),
            _ => false,
        };
        if !pass {
            return Err("hard constraint failed".into());
        }
    }
    Ok(json!({
        "status":"NO_ELIGIBLE_OBJECTIVES", "hard_constraints_passed":true,
        "eligible_objective_count":0, "objective_values":{}, "ranking_performed":false,
        "solver_invoked":false, "usable_by_optimizer":false, "authority_upgrade":false,
        "candidate_created_evidence":false,
    }))
}

fn verify_optimizer_inputs(diagnostic: &DeterministicDiagnostic) -> Result<()> {
    let inputs = diagnostic
        .details
        .get("fixture_inputs")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("optimizer fixture inputs are absent"))?;
    let results = diagnostic
        .details
        .get("fixture_results")
        .and_then(Value::as_object)
        .ok_or_else(|| anyhow!("optimizer fixture results are absent"))?;
    let mut observed = BTreeMap::new();
    for input in inputs {
        let case_id = input["case_id"]
            .as_str()
            .ok_or_else(|| anyhow!("optimizer case_id absent"))?;
        let recomputed = independent_optimizer_authorization(input);
        observed.insert(
            case_id.into(),
            if recomputed.is_ok() {
                "ACCEPT"
            } else {
                "REJECT"
            }
            .into(),
        );
        let recorded = results
            .get(case_id)
            .ok_or_else(|| anyhow!("optimizer fixture result absent"))?;
        match recomputed {
            Ok(value) if &value == recorded => {}
            Ok(_) => bail!("authorized optimizer result differs from independent replay"),
            Err(_) if recorded.get("error").and_then(Value::as_str).is_some() => {}
            Err(_) => bail!("invalid optimizer fixture did not record rejection"),
        }
    }
    if observed != diagnostic.observed_fixture_outcomes
        || diagnostic.positive_control_count != 2
        || diagnostic.negative_control_count != 10
        || diagnostic.details.get("scientific_objective_quarantine") != Some(&Value::Bool(true))
        || diagnostic.details.get("solver_invocation_count") != Some(&json!(0))
        || diagnostic.details.get("ranking_count") != Some(&json!(0))
    {
        bail!("independent optimizer authorization replay differs from evaluator");
    }
    Ok(())
}

fn report_fixture_accepted(fixture: &Value) -> Result<bool> {
    let payload = fixture
        .get("payload")
        .ok_or_else(|| anyhow!("report payload is absent"))?;
    let signature = fixture
        .get("signature")
        .ok_or_else(|| anyhow!("report signature is absent"))?;
    let locks: BTreeMap<String, bool> = serde_json::from_value(
        payload
            .get("authority_lock")
            .cloned()
            .ok_or_else(|| anyhow!("report authority lock is absent"))?,
    )?;
    verify_zero_authority_locks(&locks)?;
    let narratives = payload
        .get("narrative")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("report narrative is absent"))?;
    if fixture.get("schema").and_then(Value::as_str)
        != Some("amphora.report-package-known-answer.v1")
        || payload.get("fixture_only") != Some(&Value::Bool(true))
        || payload.get("authoritative") != Some(&Value::Bool(false))
        || payload.get("scientific_readiness").and_then(Value::as_str) != Some("UNVALIDATED")
        || payload.get("decision_use_ceiling").and_then(Value::as_str) != Some("AUDIT_ONLY")
        || payload.get("ranking_eligible") != Some(&Value::Bool(false))
        || narratives
            .iter()
            .any(|line| line.as_str().is_none_or(contains_banned_claim))
    {
        return Ok(false);
    }
    let envelopes = payload
        .get("score_envelopes")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("report score envelopes are absent"))?;
    let score_hash = stable_hash(&Value::Array(envelopes.clone()));
    let rendered = render_report(payload, &locks, &score_hash)?;
    if payload.get("score_envelope_sha256").and_then(Value::as_str) != Some(&score_hash)
        || payload.get("rendered_document").and_then(Value::as_str) != Some(&rendered)
        || payload
            .pointer("/canonical_hash_manifest/known-answer-report.md")
            .and_then(Value::as_str)
            != Some(raw_hash(rendered.as_bytes()).as_str())
        || signature.get("algorithm").and_then(Value::as_str) != Some("Ed25519")
    {
        return Ok(false);
    }
    let public = decode_hex_32(
        signature
            .get("public_key_hex")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("report fixture public key is absent"))?,
    )?;
    if signature.get("key_id").and_then(Value::as_str)
        != Some(format!("report-fixture-{}", raw_hash(&public)).as_str())
    {
        return Ok(false);
    }
    let signature_bytes = decode_hex_64(
        signature
            .get("signature_hex")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("report fixture signature is absent"))?,
    )?;
    let key = VerifyingKey::from_bytes(&public)?;
    Ok(key
        .verify(
            &serde_json::to_vec(&canonicalize(payload))?,
            &Signature::from_bytes(&signature_bytes),
        )
        .is_ok())
}

fn render_report(
    payload: &Value,
    locks: &BTreeMap<String, bool>,
    score_hash: &str,
) -> Result<String> {
    let mut output = format!(
        "# {}\n\n",
        payload
            .get("title")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("report title is absent"))?
    );
    for line in payload["narrative"].as_array().expect("narrative checked") {
        output.push_str(line.as_str().expect("narrative strings checked"));
        output.push('\n');
    }
    output.push_str(&format!(
        "\nScore envelope SHA-256: `{score_hash}`\n\n## Authority lock\n\n"
    ));
    for (lock, enabled) in locks {
        output.push_str(&format!("- `{lock}`: `{enabled}`\n"));
    }
    output.push_str(&format!(
        "\nScientific readiness: `{}`\nDecision use: `{}`\nRanking eligible: `{}`\n",
        payload["scientific_readiness"]
            .as_str()
            .expect("readiness checked"),
        payload["decision_use_ceiling"]
            .as_str()
            .expect("decision use checked"),
        payload["ranking_eligible"]
            .as_bool()
            .expect("ranking checked"),
    ));
    Ok(output)
}

fn contains_banned_claim(value: &str) -> bool {
    let normalized = value
        .nfkc()
        .flat_map(char::to_lowercase)
        .map(|character| {
            if character.is_alphanumeric() {
                character
            } else {
                ' '
            }
        })
        .collect::<String>()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ");
    [
        "phase 1",
        "procurement ready",
        "product qualified",
        "regulatory compliant",
        "fto complete",
        "patentable",
        "scientifically validated",
        "product performance proven",
    ]
    .iter()
    .any(|claim| normalized.contains(claim))
}

fn run_locked_benchmark(
    root: &Path,
    executable: &Path,
    module: &str,
    bundle: &Bundle,
) -> Result<BenchmarkReplay> {
    let executable = executable.canonicalize()?;
    if !executable.is_file() {
        bail!("benchmark executable is absent");
    }
    let output = Command::new(executable)
        .current_dir(root)
        .env("AMPHORA_READ_ONLY_COMMAND", "1")
        .args(["benchmark", "run", "--locked", "--all"])
        .output()?;
    if !output.status.success() {
        bail!("locked benchmark command failed");
    }
    let lines = output
        .stdout
        .split(|byte| *byte == b'\n')
        .filter_map(|line| {
            let row = serde_json::from_slice::<Value>(line).ok()?;
            (row.get("module_id").and_then(Value::as_str) == Some(module)).then(|| {
                BenchmarkReplay {
                    raw_line: line.to_vec(),
                    diagnostic: row,
                }
            })
        })
        .collect::<Vec<_>>();
    if lines.len() != 1
        || lines[0]
            .diagnostic
            .get("passed")
            .and_then(Value::as_bool)
            .is_none()
        || (bundle.module_class == "DETERMINISTIC_CONTROL"
            && lines[0].diagnostic.get("passed") != Some(&Value::Bool(true)))
    {
        bail!("locked benchmark did not emit one valid allowlisted module diagnostic");
    }
    Ok(lines.into_iter().next().expect("one line checked"))
}

fn validate_review(module: &str, receipt: &ReviewReceipt) -> Result<()> {
    let controls = receipt.independent_reimplementation_passed
        && receipt.parent_hashes_current
        && receipt.claim_locks_preserved
        && receipt.zero_authority_affirmed;
    if receipt.schema != "amphora.module-phase0-review-receipt.v1"
        || receipt.module_id != module
        || receipt.evaluator_key_id == receipt.reviewer_key_id
        || receipt.review_method != REVIEW_METHOD
        || receipt.independence_scope != INDEPENDENCE_SCOPE
        || receipt.human_review_performed
        || receipt.accepted_for_phase0 != controls
    {
        bail!("review receipt misstates its automated independence boundary or controls");
    }
    Ok(())
}

fn load_trust(root: &Path) -> Result<BTreeMap<String, TrustedIdentity>> {
    let file: TrustStoreFile = read_typed(&root.join("config/phase0-trust-store.v1.json"))?;
    if file.schema != "amphora.phase0-trust-store.v1"
        || file.authorization_status != "AUTHORIZED_PHASE0_SERVICE_IDENTITIES"
        || file.keys.len() != 2
    {
        bail!("trust store does not contain exactly two authorized service identities");
    }
    let mut identities = BTreeMap::new();
    let mut public_keys = BTreeSet::new();
    for row in file.keys {
        if row.algorithm != "Ed25519"
            || !row.phase0_authorized
            || row.development
            || row.revoked
            || !matches!(
                row.role.as_str(),
                "PHASE0_EVALUATOR" | "PHASE0_INTERNAL_REVIEWER"
            )
        {
            bail!("trust store contains an unauthorized, revoked, or development identity");
        }
        let bytes = decode_hex_32(&row.public_key_hex)?;
        if row.key_id != expected_key_id(&row.role, &bytes)? || !public_keys.insert(bytes) {
            bail!("trust identities are not distinct and hash-bound");
        }
        let key = VerifyingKey::from_bytes(&bytes)?;
        if identities
            .insert(
                row.key_id,
                TrustedIdentity {
                    role: row.role,
                    key,
                },
            )
            .is_some()
        {
            bail!("duplicate trusted key ID");
        }
    }
    require_unique_roles(&identities)?;
    Ok(identities)
}

fn require_unique_roles(identities: &BTreeMap<String, TrustedIdentity>) -> Result<()> {
    for role in ["PHASE0_EVALUATOR", "PHASE0_INTERNAL_REVIEWER"] {
        if identities
            .values()
            .filter(|identity| identity.role == role)
            .count()
            != 1
        {
            bail!("trust store must contain exactly one {role} identity");
        }
    }
    Ok(())
}

fn require_role<'a>(
    identities: &'a BTreeMap<String, TrustedIdentity>,
    key_id: &str,
    role: &str,
) -> Result<&'a TrustedIdentity> {
    identities
        .get(key_id)
        .filter(|identity| identity.role == role)
        .ok_or_else(|| anyhow!("key {key_id} is not authorized for role {role}"))
}

fn load_external_signing_key(root: &Path, path: &Path) -> Result<SigningKey> {
    let metadata = fs::symlink_metadata(path)?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        bail!("reviewer key must be a regular non-symlink file");
    }
    let canonical = path.canonicalize()?;
    // Canonicalize the root too: comparing against the raw path lets a key inside
    // the workspace pass whenever the workspace is reached through a symlink
    // (macOS /var -> /private/var, or any symlinked checkout). amphora-cli's
    // load_signing_key already does this; the reviewer must not be the weaker of
    // the two independent implementations.
    if canonical.starts_with(root.canonicalize()?) {
        bail!("repository-local Phase-0 private keys are forbidden");
    }
    if metadata.permissions().mode() & 0o777 != 0o600 {
        bail!("reviewer key mode must be 0600");
    }
    let parent = canonical
        .parent()
        .ok_or_else(|| anyhow!("reviewer key has no parent directory"))?;
    if fs::metadata(parent)?.permissions().mode() & 0o777 != 0o700 {
        bail!("reviewer key directory mode must be 0700");
    }
    let bytes: [u8; 32] = fs::read(canonical)?
        .try_into()
        .map_err(|_| anyhow!("reviewer Ed25519 seed must contain exactly 32 bytes"))?;
    Ok(SigningKey::from_bytes(&bytes))
}

fn ensure_external_new_output(root: &Path, path: &Path) -> Result<()> {
    if path.exists() {
        bail!("review output already exists; overwrite is forbidden");
    }
    let parent = path
        .parent()
        .ok_or_else(|| anyhow!("review output has no parent directory"))?
        .canonicalize()?;
    if parent.starts_with(root.canonicalize()?) {
        bail!("signed review return must be external to the repository");
    }
    Ok(())
}

fn verify_dsse(
    envelope: &DsseEnvelope,
    payload_type: &str,
    key_id: &str,
    key: &VerifyingKey,
    expected_payload: &[u8],
) -> Result<()> {
    if envelope.payload_type != payload_type
        || envelope.signatures.len() != 1
        || envelope.signatures[0].keyid != key_id
    {
        bail!("DSSE envelope type or signer is invalid");
    }
    let payload = STANDARD.decode(envelope.payload.as_bytes())?;
    if payload != expected_payload {
        bail!("DSSE payload is not bound to the receipt");
    }
    let signature =
        Signature::from_slice(&STANDARD.decode(envelope.signatures[0].sig.as_bytes())?)?;
    key.verify(&pae(payload_type, &payload), &signature)
        .map_err(|_| anyhow!("forged or invalid DSSE signature"))
}

fn sign_dsse(payload_type: &str, payload: &[u8], key_id: &str, key: &SigningKey) -> DsseEnvelope {
    let signature = key.sign(&pae(payload_type, payload));
    DsseEnvelope {
        payload_type: payload_type.into(),
        payload: STANDARD.encode(payload),
        signatures: vec![DsseSignature {
            keyid: key_id.into(),
            sig: STANDARD.encode(signature.to_bytes()),
        }],
    }
}

fn pae(payload_type: &str, payload: &[u8]) -> Vec<u8> {
    format!(
        "DSSEv1 {} {} {} ",
        payload_type.len(),
        payload_type,
        payload.len()
    )
    .into_bytes()
    .into_iter()
    .chain(payload.iter().copied())
    .collect()
}

fn verify_zero_authority_locks(locks: &BTreeMap<String, bool>) -> Result<()> {
    if locks.values().any(|enabled| !enabled)
        || ZERO_AUTHORITY_LOCKS
            .iter()
            .any(|required| locks.get(*required) != Some(&true))
    {
        bail!("a required zero-authority claim lock is absent or false");
    }
    Ok(())
}

fn confined_file(module_dir: &Path, relative: &str) -> Result<PathBuf> {
    let relative_path = Path::new(relative);
    if relative_path.is_absolute()
        || relative_path.components().any(|component| {
            !matches!(component, Component::Normal(_)) || component.as_os_str() == ".amphora"
        })
    {
        bail!("unsafe module-relative path: {relative}");
    }
    let path = module_dir.join(relative_path).canonicalize()?;
    if !path.starts_with(module_dir) || !path.is_file() {
        bail!("artifact escapes the reviewed module: {relative}");
    }
    Ok(path)
}

fn safe_relative(relative: &str) -> Result<&Path> {
    let path = Path::new(relative);
    if path.is_absolute()
        || path.components().any(|component| {
            !matches!(component, Component::Normal(_)) || component.as_os_str() == ".amphora"
        })
    {
        bail!("unsafe workspace-relative path: {relative}");
    }
    Ok(path)
}

fn expected_key_id(role: &str, public_key: &[u8; 32]) -> Result<String> {
    let prefix = match role {
        "PHASE0_EVALUATOR" => "phase0-evaluator",
        "PHASE0_INTERNAL_REVIEWER" => "phase0-internal-reviewer",
        _ => bail!("invalid Phase-0 role"),
    };
    Ok(format!("{prefix}-{}", raw_hash(public_key)))
}

fn decode_hex_32(value: &str) -> Result<[u8; 32]> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !(byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)))
    {
        bail!("Ed25519 public key must be 32-byte lowercase hex");
    }
    let mut bytes = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        bytes[index] = u8::from_str_radix(std::str::from_utf8(chunk)?, 16)?;
    }
    Ok(bytes)
}

fn decode_hex_64(value: &str) -> Result<[u8; 64]> {
    if value.len() != 128
        || value
            .bytes()
            .any(|byte| !(byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)))
    {
        bail!("Ed25519 signature must be 64-byte lowercase hex");
    }
    let mut bytes = [0_u8; 64];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        bytes[index] = u8::from_str_radix(std::str::from_utf8(chunk)?, 16)?;
    }
    Ok(bytes)
}

fn verify_hash(name: &str, value: &str) -> Result<()> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !(byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)))
    {
        bail!("{name} is not a lowercase SHA-256 digest");
    }
    Ok(())
}

fn read_typed<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
    let bytes = fs::read(path).with_context(|| format!("reading {}", path.display()))?;
    let mut deserializer = serde_json::Deserializer::from_slice(&bytes);
    let value = T::deserialize(&mut deserializer)?;
    deserializer.end()?;
    Ok(value)
}

fn canonicalize(value: &Value) -> Value {
    match value {
        Value::Object(object) => {
            let mut keys = object.keys().collect::<Vec<_>>();
            keys.sort();
            let mut ordered = Map::new();
            for key in keys {
                ordered.insert(key.clone(), canonicalize(&object[key]));
            }
            Value::Object(ordered)
        }
        Value::Array(values) => Value::Array(values.iter().map(canonicalize).collect()),
        other => other.clone(),
    }
}

fn canonical_bytes<T: Serialize>(value: &T) -> Result<Vec<u8>> {
    Ok(serde_json::to_vec(&canonicalize(&serde_json::to_value(
        value,
    )?))?)
}

fn stable_hash(value: &Value) -> String {
    raw_hash(&serde_json::to_vec(&canonicalize(value)).expect("JSON value serializes"))
}

fn file_hash(path: &Path) -> Result<String> {
    Ok(raw_hash(&fs::read(path)?))
}

fn raw_hash(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn write_new_json<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let mut bytes = serde_json::to_vec_pretty(&canonicalize(&serde_json::to_value(value)?))?;
    bytes.push(b'\n');
    let mut file = OpenOptions::new().create_new(true).write(true).open(path)?;
    file.write_all(&bytes)?;
    file.sync_all()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};

    static TEST_ID: AtomicU64 = AtomicU64::new(0);

    fn temp_dir() -> PathBuf {
        let path = std::env::temp_dir().join(format!(
            "amphora-phase0-reviewer-test-{}-{}",
            std::process::id(),
            TEST_ID.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        fs::set_permissions(&path, fs::Permissions::from_mode(0o700)).unwrap();
        path
    }

    #[test]
    fn forged_signature_and_wrong_role_are_rejected() {
        let evaluator = SigningKey::from_bytes(&[1; 32]);
        let forger = SigningKey::from_bytes(&[2; 32]);
        let envelope = sign_dsse("test", b"payload", "evaluator", &forger);
        assert!(verify_dsse(
            &envelope,
            "test",
            "evaluator",
            &evaluator.verifying_key(),
            b"payload"
        )
        .is_err());

        let identities = BTreeMap::from([(
            "reviewer".into(),
            TrustedIdentity {
                role: "PHASE0_INTERNAL_REVIEWER".into(),
                key: evaluator.verifying_key(),
            },
        )]);
        assert!(require_role(&identities, "reviewer", "PHASE0_EVALUATOR").is_err());
    }

    #[test]
    fn repository_key_and_output_overwrite_are_rejected() {
        let root = temp_dir();
        let key = root.join("key.seed");
        fs::write(&key, [1_u8; 32]).unwrap();
        fs::set_permissions(&key, fs::Permissions::from_mode(0o600)).unwrap();
        assert!(load_external_signing_key(&root, &key).is_err());
        assert!(ensure_external_new_output(&root, &key).is_err());
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn cross_module_paths_and_stripped_locks_are_rejected() {
        let root = temp_dir();
        assert!(confined_file(&root, "../amphora-other/receipt.json").is_err());
        let mut locks = ZERO_AUTHORITY_LOCKS
            .iter()
            .map(|name| ((*name).into(), true))
            .collect::<BTreeMap<_, _>>();
        locks.remove("no_release_authority");
        assert!(verify_zero_authority_locks(&locks).is_err());
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn altered_benchmark_and_false_human_review_are_rejected() {
        let module = "amphora-candidate-contract";
        let original = json!({"passed": true, "module_id": module});
        let altered = json!({"passed": false, "module_id": module});
        assert_ne!(
            canonical_bytes(&original).unwrap(),
            canonical_bytes(&altered).unwrap()
        );

        let review = ReviewReceipt {
            schema: "amphora.module-phase0-review-receipt.v1".into(),
            review_id: "review".into(),
            module_id: module.into(),
            bundle_hash: "a".repeat(64),
            evaluation_receipt_hash: "b".repeat(64),
            evaluator_key_id: "evaluator".into(),
            reviewer_key_id: "reviewer".into(),
            review_method: REVIEW_METHOD.into(),
            independence_scope: INDEPENDENCE_SCOPE.into(),
            human_review_performed: true,
            independent_reimplementation_passed: true,
            parent_hashes_current: true,
            claim_locks_preserved: true,
            zero_authority_affirmed: true,
            accepted_for_phase0: true,
            findings: Vec::new(),
            signature: None,
        };
        assert!(validate_review(module, &review).is_err());
    }

    #[test]
    fn reviewer_allowlist_is_exact_and_rejects_unknown_modules() {
        assert_eq!(REVIEWED_MODULES.len(), 29);
        for module in REVIEWED_MODULES {
            verify_allowed_module(module).unwrap();
        }
        assert!(verify_allowed_module("amphora-unknown").is_err());
    }
}
