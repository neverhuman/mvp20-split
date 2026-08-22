use super::{canonical_bytes, emit_jsonl, ensure_local_identity, persist_immutable};
use amphora_core::{
    load_rights_trust_store, stable_hash, verify_activation_authorization, AcquisitionUnitV2,
    AuthorizationOverlayRefV1, DataCatalogV2, DerivedRecordV1, EvidenceClass,
    ModuleDatasetActivationSetV1, ModuleDatasetActivationV1, ModuleDatasetAuthorizationLedgerV1,
    ModuleDatasetAuthorizationOverlayV1, ModuleDatasetLockV2, NormalizedDatasetManifestV2,
    NormalizedRecordV2, OrdExclusionReasonV1, OrdExclusionScopeV1, OrdExclusionV1,
    OrdGitLfsObjectV1, OrdGitLfsTreeV1, ParserKind, RightsClass, RightsDecisionV2,
    RightsReviewReceiptV1, ACTIVATION_SCHEMA, ACTIVATION_SET_SCHEMA, AUTHORIZATION_LEDGER_SCHEMA,
    AUTHORIZATION_OVERLAY_SCHEMA, DATASET_MANIFEST_V2_SCHEMA, MODULE_DATASET_LOCK_SCHEMA,
    ORD_EXCLUSION_SCHEMA,
};
use amphora_ord_codec::{
    classify_dataset_reactions, decode_gzip_dataset, decompress_gzip_bounded,
    descriptor_set_sha256, OrdCodecError, StructuralExclusionReason,
};
use anyhow::{anyhow, bail, Context, Result};
use base64::prelude::{Engine as _, BASE64_STANDARD};
use csv::{ReaderBuilder, StringRecord};
use ed25519_dalek::{Signature, Signer, Verifier, VerifyingKey};
use flate2::{read::GzDecoder, Compression, GzBuilder};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::fs::{self, File};
use std::io::{BufRead, BufReader, BufWriter, Read, Write};
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use zip::ZipArchive;

const CATALOG_FILE: &str = "catalog.json";
const SOURCE_SCHEMA: &str = "amphora.source-intent.v2";
const ACQUISITION_SCHEMA: &str = "amphora.acquisition-unit.v2";
const RIGHTS_SCHEMA: &str = "amphora.rights-decision.v2";
const DATASET_SCHEMA: &str = DATASET_MANIFEST_V2_SCHEMA;
const LOCK_SCHEMA: &str = MODULE_DATASET_LOCK_SCHEMA;
const ORD_DATA_COMMIT: &str = "ddb0d25770c80a0a6fcf9948c26e1c8f828cb8ad";
const ORD_DATA_COMMIT_TREE: &str = "7a276183e40540542fd7521b5b38cb2d880afa70";
const ORD_PROTOBUF_OBJECTS: u64 = 550;
const ORD_PARQUET_COMPANIONS: usize = 53;
const ORD_TOTAL_PROTOBUF_BYTES: u64 = 1_181_061_030;
const ORD_PARQUET_LOCK_PATH: &str = "config/ord/ord-data-v4-parquet-companions.txt";
const REQUIRED_SOURCE_INTENTS: [&str; 15] = [
    "bigsoldb",
    "neurips_open_polymer_prediction",
    "openpoly",
    "corr_data",
    "nist_materials_data_repository",
    "polyinfo",
    "pi1m",
    "omg",
    "polyuniverse",
    "polymer_genome",
    "point2",
    "polyomics",
    "polyverse",
    "radonpy",
    "nanomine",
];

#[derive(Debug, Serialize)]
struct RejectionRecordV2 {
    schema: &'static str,
    acquisition_unit_id: String,
    raw_file_sha256: String,
    row_number: u64,
    archive_entry: Option<String>,
    reason: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct AcquisitionReceiptV2 {
    schema: String,
    acquisition_unit_id: String,
    source_intent_id: String,
    raw_object_path: String,
    sha256: String,
    bytes: u64,
    acquisition_method: String,
    source_url: Option<String>,
    credential_ref: Option<String>,
    rights_decision_id: String,
    quarantined: bool,
    signature: Option<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct RightsReviewRequestV1 {
    schema: String,
    request_id: String,
    module_id: String,
    snapshot_id: String,
    dataset_id: String,
    acquisition_unit_id: String,
    rights_decision_id: String,
    rights_decision_hash: String,
    artifact_path: String,
    artifact_sha256: String,
    rights_class: RightsClass,
    license: String,
    authority_ceiling: String,
    exclusions: Vec<String>,
}

impl RightsReviewRequestV1 {
    fn computed_id(&self) -> Result<String> {
        let mut unsigned = self.clone();
        unsigned.request_id.clear();
        Ok(format!(
            "rights-request-{}",
            stable_hash(&serde_json::to_value(unsigned)?)
        ))
    }

    fn validate(&self) -> Result<()> {
        if self.schema != "amphora.rights-review-request.v1"
            || self.request_id != self.computed_id()?
            || self.module_id.strip_prefix("amphora-").is_none()
            || self.snapshot_id.trim().is_empty()
            || self.dataset_id.trim().is_empty()
            || self.acquisition_unit_id.trim().is_empty()
            || self.rights_decision_id.trim().is_empty()
            || self.rights_decision_hash.len() != 64
            || self.artifact_sha256.len() != 64
            || self.artifact_path.trim().is_empty()
            || self.rights_class != RightsClass::DerivativeAllowed
            || self.license.trim().is_empty()
            || self.authority_ceiling != "AUDIT_ONLY"
            || self.exclusions.len() != 9
        {
            bail!("invalid offline rights-review request");
        }
        Ok(())
    }
}

const RIGHTS_REVIEW_EXCLUSIONS: [&str; 9] = [
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

struct NormalizeState {
    records: u64,
    rejections: u64,
    endpoint_counts: BTreeMap<String, u64>,
    identities: BTreeMap<String, Vec<String>>,
    duplicate_keys: BTreeMap<String, Vec<String>>,
}

struct ParsedFields {
    endpoint: String,
    value_number: Option<f64>,
    value_text: Option<String>,
    unit: Option<String>,
    conditions: BTreeMap<String, String>,
    citation: Option<String>,
    identity: Option<String>,
}

pub fn acquire(
    root: &Path,
    snapshot_arg: &Path,
    all: bool,
    requested_unit: Option<&str>,
    manual_import: Option<&Path>,
) -> Result<()> {
    require_selection(all, requested_unit)?;
    let snapshot = rooted(root, snapshot_arg)?;
    let catalog = read_catalog(&snapshot)?;
    validate_catalog(root, &snapshot, &catalog)?;
    let selected = select_units(&catalog, all, requested_unit)?;
    let rights = rights_by_unit(&catalog);
    let mut results = Vec::new();
    let mut failed = false;
    for unit in selected {
        let decision = rights
            .get(unit.acquisition_unit_id.as_str())
            .ok_or_else(|| anyhow!("missing rights decision for {}", unit.acquisition_unit_id))?;
        let authorized_manual_import = manual_import.is_some()
            && requested_unit == Some(unit.acquisition_unit_id.as_str())
            && decision.rights_class == RightsClass::ManualExport;
        if decision.rights_class.acquisition_prohibited()
            || unit.evidence_class == EvidenceClass::Prohibited
            || (unit.blocked_reason.is_some() && !authorized_manual_import)
        {
            results.push(json!({
                "acquisition_unit_id": unit.acquisition_unit_id,
                "status": "BLOCKED",
                "rights_class": decision.rights_class,
                "reason": unit.blocked_reason.as_deref().unwrap_or(&decision.basis),
            }));
            continue;
        }
        let import = if requested_unit == Some(unit.acquisition_unit_id.as_str()) {
            manual_import
        } else {
            None
        };
        match acquire_unit(root, &snapshot, unit, decision, import) {
            Ok(receipt) => results.push(json!({
                "acquisition_unit_id": unit.acquisition_unit_id,
                "status": "ACQUIRED",
                "sha256": receipt.sha256,
                "bytes": receipt.bytes,
                "quarantined": receipt.quarantined,
            })),
            Err(error) if all => {
                failed = true;
                results.push(json!({
                    "acquisition_unit_id": unit.acquisition_unit_id,
                    "status": "FAILED",
                    "reason": error.to_string(),
                }));
            }
            Err(error) => return Err(error),
        }
    }
    emit_jsonl(&json!({
        "schema": "amphora.data-acquisition-report.v2",
        "snapshot_id": catalog.snapshot_id,
        "results": results,
    }))?;
    if failed {
        bail!("one or more v2 acquisitions failed closed")
    }
    Ok(())
}

pub fn normalize(
    root: &Path,
    snapshot_arg: &Path,
    all: bool,
    requested_unit: Option<&str>,
) -> Result<()> {
    require_selection(all, requested_unit)?;
    let snapshot = rooted(root, snapshot_arg)?;
    let catalog = read_catalog(&snapshot)?;
    validate_catalog(root, &snapshot, &catalog)?;
    let selected = select_units(&catalog, all, requested_unit)?;
    let rights = rights_by_unit(&catalog);
    let mut results = Vec::new();
    let mut failed = false;
    for unit in selected {
        let decision = rights
            .get(unit.acquisition_unit_id.as_str())
            .ok_or_else(|| anyhow!("missing rights decision for {}", unit.acquisition_unit_id))?;
        let receipt_path = acquisition_receipt_path(&snapshot, &unit.acquisition_unit_id);
        if !receipt_path.is_file() {
            results.push(json!({
                "acquisition_unit_id": unit.acquisition_unit_id,
                "status": "NOT_ACQUIRED",
            }));
            continue;
        }
        match normalize_unit(root, &snapshot, unit, decision) {
            Ok(manifest) => results.push(json!({
                "acquisition_unit_id": unit.acquisition_unit_id,
                "status": "NORMALIZED",
                "dataset_id": manifest.dataset_id,
                "record_count": manifest.record_count,
                "rejection_count": manifest.rejection_count,
                "quarantined": manifest.quarantined,
            })),
            Err(error) if all => {
                failed = true;
                results.push(json!({
                    "acquisition_unit_id": unit.acquisition_unit_id,
                    "status": "FAILED",
                    "reason": error.to_string(),
                }));
            }
            Err(error) => return Err(error),
        }
    }
    emit_jsonl(&json!({
        "schema": "amphora.data-normalization-report.v2",
        "snapshot_id": catalog.snapshot_id,
        "results": results,
    }))?;
    if failed {
        bail!("one or more v2 normalizations failed closed")
    }
    Ok(())
}

pub fn consume(
    root: &Path,
    snapshot_arg: &Path,
    requested_module: Option<&str>,
    requested_dataset: Option<&str>,
    all_for_module: bool,
    all_modules: bool,
) -> Result<()> {
    let selection_valid = (all_modules
        && requested_module.is_none()
        && requested_dataset.is_none()
        && !all_for_module)
        || (!all_modules
            && requested_module.is_some()
            && ((all_for_module && requested_dataset.is_none())
                || (!all_for_module && requested_dataset.is_some())));
    if !selection_valid {
        bail!("select --all-modules, --module with --all, or --module with --dataset");
    }
    let snapshot = rooted(root, snapshot_arg)?;
    let catalog = read_catalog(&snapshot)?;
    validate_catalog(root, &snapshot, &catalog)?;
    let rights = rights_by_unit(&catalog);
    let mut activations = Vec::new();
    for unit in &catalog.acquisition_units {
        let manifest_path = dataset_manifest_path(&snapshot, &unit.acquisition_unit_id);
        if !manifest_path.is_file() {
            continue;
        }
        let manifest: NormalizedDatasetManifestV2 = read_json_typed(&manifest_path)?;
        let decision = rights
            .get(unit.acquisition_unit_id.as_str())
            .ok_or_else(|| anyhow!("missing rights decision for {}", unit.acquisition_unit_id))?;
        validate_manifest(&snapshot, unit, decision, &manifest)?;
        for consumer in &unit.consumers {
            if requested_module.is_some_and(|module| module != consumer.module_id) {
                continue;
            }
            if requested_dataset.is_some_and(|dataset| {
                dataset != manifest.dataset_id && dataset != unit.acquisition_unit_id
            }) {
                continue;
            }
            let central_lock_path = lock_path(&snapshot, &consumer.module_id, &manifest.dataset_id);
            let lock: ModuleDatasetLockV2 = read_json_typed(&central_lock_path)?;
            validate_lock(&snapshot, &lock)?;
            activations.push(materialize_binding(
                root, &snapshot, &catalog, unit, decision, &manifest, &lock,
            )?);
        }
    }
    if activations.is_empty() {
        bail!("no normalized dataset binding matched the requested selection");
    }
    let expected_binding_count = catalog
        .acquisition_units
        .iter()
        .filter(|unit| dataset_manifest_path(&snapshot, &unit.acquisition_unit_id).is_file())
        .map(|unit| unit.consumers.len())
        .sum::<usize>();
    if all_modules && activations.len() != expected_binding_count {
        bail!(
            "all-module materialization must resolve all {expected_binding_count} normalized bindings; observed {}",
            activations.len(),
        );
    }
    if all_modules
        && snapshot_channel(&catalog.snapshot_id)? == "feedback-v2"
        && expected_binding_count != 30
    {
        bail!("frozen feedback/v2 must retain exactly 30 normalized bindings");
    }
    activations.sort_by(|left, right| {
        (&left.module_id, &left.dataset_id).cmp(&(&right.module_id, &right.dataset_id))
    });
    emit_jsonl(&json!({
        "schema": "amphora.data-materialization-report.v1",
        "snapshot_id": catalog.snapshot_id,
        "materialized_binding_count": activations.len(),
        "expected_all_module_binding_count": expected_binding_count,
        "rights_reviewed_binding_count": activations.iter().filter(|row| row.rights_reviewed).count(),
        "quarantine_binding_count": activations.iter().filter(|row| row.quarantined_row_count > 0).count(),
        "scoring_binding_count": activations.iter().filter(|row| row.scoring).count(),
        "activations": activations,
    }))
}

pub fn request_rights_review(
    root: &Path,
    snapshot_arg: &Path,
    module: &str,
    dataset: &str,
    output_arg: &Path,
) -> Result<()> {
    let snapshot = rooted(root, snapshot_arg)?;
    let catalog = read_catalog(&snapshot)?;
    validate_catalog(root, &snapshot, &catalog)?;
    let reference = root.join(module).join("reference/mvp20");
    if !reference.is_dir() || module != safe_id(module) {
        bail!("rights request targets an unknown or unsafe module");
    }
    let data_directory = format!(
        "data/{}",
        snapshot_channel(&catalog.snapshot_id)?.replace('-', "_")
    );
    let activation_path = reference.join(&data_directory).join("activation.v1.json");
    let set: ModuleDatasetActivationSetV1 = read_json_typed(&activation_path)?;
    let activation = set
        .activations
        .iter()
        .find(|activation| activation.dataset_id == dataset)
        .ok_or_else(|| anyhow!("requested dataset is not a current module activation"))?;
    let unit = catalog
        .acquisition_units
        .iter()
        .find(|unit| unit.acquisition_unit_id == activation.acquisition_unit_id)
        .ok_or_else(|| anyhow!("activation acquisition unit is absent from the catalog"))?;
    let decision = catalog
        .rights_decisions
        .iter()
        .find(|decision| decision.rights_decision_id == unit.rights_decision_id)
        .ok_or_else(|| anyhow!("activation rights decision is absent from the catalog"))?;
    let artifact = safe_join(&reference, &activation.normalized_object_path)?;
    if decision.rights_class != RightsClass::DerivativeAllowed
        || !artifact.is_file()
        || file_sha256(&artifact)? != activation.normalized_object_sha256
    {
        bail!("rights request cannot bind an ineligible, absent, or stale artifact");
    }
    let mut request = RightsReviewRequestV1 {
        schema: "amphora.rights-review-request.v1".into(),
        request_id: String::new(),
        module_id: module.into(),
        snapshot_id: catalog.snapshot_id,
        dataset_id: activation.dataset_id.clone(),
        acquisition_unit_id: activation.acquisition_unit_id.clone(),
        rights_decision_id: decision.rights_decision_id.clone(),
        rights_decision_hash: stable_hash(&serde_json::to_value(decision)?),
        artifact_path: activation.normalized_object_path.clone(),
        artifact_sha256: activation.normalized_object_sha256.clone(),
        rights_class: decision.rights_class.clone(),
        license: decision.license.clone(),
        authority_ceiling: "AUDIT_ONLY".into(),
        exclusions: RIGHTS_REVIEW_EXCLUSIONS
            .into_iter()
            .map(str::to_owned)
            .collect(),
    };
    request.request_id = request.computed_id()?;
    request.validate()?;
    let output = rooted(root, output_arg)?;
    write_json_generated(&output, &serde_json::to_value(&request)?)?;
    emit_jsonl(&json!({
        "schema": "amphora.data-rights-request-result.v1",
        "request_id": request.request_id,
        "output": relative(root, &output),
        "authority_ceiling": "AUDIT_ONLY",
        "private_key_material_accessed": false,
    }))
}

pub fn sign_rights_review(
    root: &Path,
    request_arg: &Path,
    private_key_arg: &Path,
    output_arg: &Path,
) -> Result<()> {
    let request_path = rooted(root, request_arg)?;
    let private_key_path = rooted(root, private_key_arg)?;
    let canonical_root = fs::canonicalize(root)?;
    let canonical_key = fs::canonicalize(&private_key_path)?;
    if canonical_key.starts_with(&canonical_root) {
        bail!("rights-review private keys must remain outside the repository");
    }
    let request: RightsReviewRequestV1 = read_json_typed(&request_path)?;
    request.validate()?;
    let key_text = fs::read_to_string(&canonical_key)?;
    let key_bytes = decode_hex_32(key_text.trim())?;
    let signing_key = ed25519_dalek::SigningKey::from_bytes(&key_bytes);
    let reviewer_key_id = format!(
        "rights-reviewer-{}",
        bytes_sha256(&signing_key.verifying_key().to_bytes())
    );
    let trust = load_rights_trust_store(&root.join("config/rights-review-trust-store.v1.json"))?;
    trust.require_reviewer(&reviewer_key_id)?;
    let mut receipt = RightsReviewReceiptV1 {
        schema: amphora_core::RIGHTS_REVIEW_RECEIPT_SCHEMA.into(),
        receipt_id: String::new(),
        module_id: request.module_id.clone(),
        snapshot_id: request.snapshot_id.clone(),
        dataset_id: request.dataset_id.clone(),
        acquisition_unit_id: request.acquisition_unit_id.clone(),
        rights_decision_id: request.rights_decision_id.clone(),
        rights_decision_hash: request.rights_decision_hash.clone(),
        artifact_path: request.artifact_path.clone(),
        artifact_sha256: request.artifact_sha256.clone(),
        rights_class: request.rights_class.clone(),
        license: request.license.clone(),
        accepted: true,
        authority_ceiling: "AUDIT_ONLY".into(),
        exclusions: request.exclusions.clone(),
        reviewer_key_id: reviewer_key_id.clone(),
        signature: None,
    };
    receipt.bind_receipt_id()?;
    receipt.sign(&reviewer_key_id, &signing_key)?;
    receipt.verify_signature(&trust)?;
    let output = rooted(root, output_arg)?;
    write_json_generated(&output, &serde_json::to_value(&receipt)?)?;
    emit_jsonl(&json!({
        "schema": "amphora.data-rights-sign-result.v1",
        "request_id": request.request_id,
        "receipt_id": receipt.receipt_id,
        "reviewer_key_id": reviewer_key_id,
        "output": relative(root, &output),
        "private_key_persisted": false,
        "authority_ceiling": "AUDIT_ONLY",
    }))
}

pub fn import_rights_review(
    root: &Path,
    snapshot_arg: &Path,
    module: &str,
    receipt_arg: &Path,
) -> Result<()> {
    let snapshot = rooted(root, snapshot_arg)?;
    let catalog = read_catalog(&snapshot)?;
    validate_catalog(root, &snapshot, &catalog)?;
    let module_dir = root.join(module);
    if !module_dir.is_dir() || module != safe_id(module) {
        bail!("rights receipt targets an unknown or unsafe module");
    }
    let reference = module_dir.join("reference/mvp20");
    let data_directory = format!(
        "data/{}",
        snapshot_channel(&catalog.snapshot_id)?.replace('-', "_")
    );
    let activation_path = reference.join(&data_directory).join("activation.v1.json");
    let activations: ModuleDatasetActivationSetV1 = read_json_typed(&activation_path)?;
    if activations.schema != ACTIVATION_SET_SCHEMA
        || activations.module_id != module
        || activations.snapshot_id != catalog.snapshot_id
    {
        bail!("module activation set is not bound to the requested snapshot");
    }

    let receipt_source = rooted(root, receipt_arg)?;
    let receipt: RightsReviewReceiptV1 = read_json_typed(&receipt_source)?;
    let trust = load_rights_trust_store(&root.join("config/rights-review-trust-store.v1.json"))?;
    receipt.verify_signature(&trust)?;
    ensure_rights_signer_separation(root, &receipt.reviewer_key_id)?;
    if receipt.module_id != module || receipt.snapshot_id != catalog.snapshot_id {
        bail!("cross-module or cross-snapshot rights receipt rejected");
    }
    let activation = activations
        .activations
        .iter()
        .find(|activation| {
            activation.dataset_id == receipt.dataset_id
                && activation.acquisition_unit_id == receipt.acquisition_unit_id
        })
        .ok_or_else(|| anyhow!("rights receipt is not bound to a current module activation"))?;
    let unit = catalog
        .acquisition_units
        .iter()
        .find(|unit| unit.acquisition_unit_id == activation.acquisition_unit_id)
        .ok_or_else(|| anyhow!("activation acquisition unit is absent from the catalog"))?;
    let decision = catalog
        .rights_decisions
        .iter()
        .find(|decision| decision.rights_decision_id == unit.rights_decision_id)
        .ok_or_else(|| anyhow!("activation rights decision is absent from the catalog"))?;
    if decision.rights_class != RightsClass::DerivativeAllowed
        || receipt.rights_decision_id != decision.rights_decision_id
        || receipt.rights_decision_hash != stable_hash(&serde_json::to_value(decision)?)
        || receipt.rights_class != decision.rights_class
        || receipt.license != decision.license
        || receipt.artifact_path != activation.normalized_object_path
        || receipt.artifact_sha256 != activation.normalized_object_sha256
    {
        bail!("rights receipt does not exactly bind the catalog decision and activation artifact");
    }
    let artifact = safe_join(&reference, &receipt.artifact_path)?;
    if !artifact.is_file() || file_sha256(&artifact)? != receipt.artifact_sha256 {
        bail!("rights receipt artifact is absent or stale");
    }

    let authorization_directory = reference.join(&data_directory).join("authorizations");
    let receipt_destination = authorization_directory
        .join("receipts")
        .join(format!("{}.dsse.json", safe_id(&receipt.receipt_id)));
    install_file_immutable(&receipt_source, &receipt_destination)?;
    let receipt_relative = reference_relative(&reference, &receipt_destination)?;
    let ledger_path = authorization_directory.join("ledger.v1.json");
    let mut ledger = if ledger_path.is_file() {
        read_json_typed::<ModuleDatasetAuthorizationLedgerV1>(&ledger_path)?
    } else {
        ModuleDatasetAuthorizationLedgerV1 {
            schema: AUTHORIZATION_LEDGER_SCHEMA.into(),
            module_id: module.into(),
            snapshot_id: catalog.snapshot_id.clone(),
            head_overlay_id: String::new(),
            overlays: Vec::new(),
        }
    };
    validate_authorization_ledger_shape(&reference, &ledger)?;
    let activation_hash = stable_hash(&serde_json::to_value(activation)?);
    if ledger.overlays.iter().any(|reference_row| {
        let path = reference.join(&reference_row.path);
        read_json_typed::<ModuleDatasetAuthorizationOverlayV1>(&path).is_ok_and(|overlay| {
            overlay.activation_hash == activation_hash
                || overlay.rights_receipt_sha256
                    == file_sha256(&receipt_destination).unwrap_or_default()
        })
    }) {
        bail!("activation or signed rights receipt was already authorized");
    }
    let mut overlay = ModuleDatasetAuthorizationOverlayV1 {
        schema: AUTHORIZATION_OVERLAY_SCHEMA.into(),
        overlay_id: String::new(),
        parent_overlay_id: (!ledger.head_overlay_id.is_empty())
            .then(|| ledger.head_overlay_id.clone()),
        module_id: module.into(),
        snapshot_id: catalog.snapshot_id.clone(),
        dataset_id: activation.dataset_id.clone(),
        acquisition_unit_id: activation.acquisition_unit_id.clone(),
        activation_hash,
        artifact_path: activation.normalized_object_path.clone(),
        artifact_sha256: activation.normalized_object_sha256.clone(),
        rights_receipt_path: receipt_relative,
        rights_receipt_sha256: file_sha256(&receipt_destination)?,
        rights_reviewer_key_id: receipt.reviewer_key_id.clone(),
        authority_ceiling: "AUDIT_ONLY".into(),
        scoring_authorized: false,
    };
    overlay.bind_overlay_id()?;
    overlay.validate()?;
    let overlay_destination = authorization_directory
        .join("events")
        .join(format!("{}.json", overlay.overlay_id));
    persist_immutable(
        &overlay_destination,
        &canonical_bytes(&serde_json::to_value(&overlay)?)?,
    )?;
    let overlay_relative = reference_relative(&reference, &overlay_destination)?;
    ledger.head_overlay_id = overlay.overlay_id.clone();
    ledger.overlays.push(AuthorizationOverlayRefV1 {
        overlay_id: overlay.overlay_id.clone(),
        path: overlay_relative,
        sha256: file_sha256(&overlay_destination)?,
    });
    write_json_generated(&ledger_path, &serde_json::to_value(&ledger)?)?;
    verify_activation_authorization(&reference, activation, &catalog, &trust)?;
    emit_jsonl(&json!({
        "schema": "amphora.data-rights-import-result.v1",
        "module_id": module,
        "snapshot_id": catalog.snapshot_id,
        "dataset_id": activation.dataset_id,
        "rights_receipt_id": receipt.receipt_id,
        "authorization_overlay_id": overlay.overlay_id,
        "authority_ceiling": "AUDIT_ONLY",
        "scoring_authorized": false,
    }))
}

pub fn verify_rights(
    root: &Path,
    snapshot_arg: &Path,
    all: bool,
    requested_module: Option<&str>,
) -> Result<()> {
    if all == requested_module.is_some() {
        bail!("select exactly one of --all or --module");
    }
    let snapshot = rooted(root, snapshot_arg)?;
    let catalog = read_catalog(&snapshot)?;
    validate_catalog(root, &snapshot, &catalog)?;
    let trust = load_rights_trust_store(&root.join("config/rights-review-trust-store.v1.json"))?;
    let modules = catalog
        .acquisition_units
        .iter()
        .flat_map(|unit| {
            unit.consumers
                .iter()
                .map(|consumer| consumer.module_id.as_str())
        })
        .filter(|module| requested_module.is_none_or(|requested| requested == *module))
        .collect::<BTreeSet<_>>();
    if modules.is_empty() {
        bail!("no module activations match the requested rights verification");
    }
    let mut verified = Vec::new();
    let mut issues = Vec::new();
    let data_directory = format!(
        "data/{}",
        snapshot_channel(&catalog.snapshot_id)?.replace('-', "_")
    );
    for module in modules {
        let reference = root.join(module).join("reference/mvp20");
        let activation_path = reference.join(&data_directory).join("activation.v1.json");
        let set: ModuleDatasetActivationSetV1 = match read_json_typed(&activation_path) {
            Ok(set) => set,
            Err(error) => {
                issues.push(format!("{module}: {error}"));
                continue;
            }
        };
        for activation in &set.activations {
            match verify_activation_authorization(&reference, activation, &catalog, &trust) {
                Ok(overlay) => verified.push(json!({
                    "module_id": module,
                    "dataset_id": activation.dataset_id,
                    "authorization_overlay_id": overlay.overlay_id,
                    "rights_reviewer_key_id": overlay.rights_reviewer_key_id,
                })),
                Err(error) => issues.push(format!("{}:{}: {error}", module, activation.dataset_id)),
            }
        }
    }
    emit_jsonl(&json!({
        "schema": "amphora.data-rights-verification-report.v1",
        "snapshot_id": catalog.snapshot_id,
        "verified_binding_count": verified.len(),
        "issue_count": issues.len(),
        "verified": verified,
        "issues": issues,
        "authority_ceiling": "AUDIT_ONLY",
    }))?;
    if !issues.is_empty() {
        bail!("one or more module activations lack valid cryptographic rights authorization");
    }
    Ok(())
}

fn ensure_rights_signer_separation(root: &Path, rights_reviewer_key_id: &str) -> Result<()> {
    let phase0: Value = read_json_typed(&root.join("config/phase0-trust-store.v1.json"))?;
    if phase0
        .get("keys")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .any(|key| key.get("key_id").and_then(Value::as_str) == Some(rights_reviewer_key_id))
    {
        bail!("rights reviewer must be separate from Phase-0 evaluator and reviewer identities");
    }
    Ok(())
}

fn validate_authorization_ledger_shape(
    reference_root: &Path,
    ledger: &ModuleDatasetAuthorizationLedgerV1,
) -> Result<()> {
    if ledger.schema != AUTHORIZATION_LEDGER_SCHEMA
        || ledger.module_id.trim().is_empty()
        || ledger.snapshot_id.trim().is_empty()
        || (ledger.overlays.is_empty() != ledger.head_overlay_id.is_empty())
    {
        bail!("authorization ledger identity or head is invalid");
    }
    let mut previous = None;
    let mut paths = BTreeSet::new();
    let mut ids = BTreeSet::new();
    for row in &ledger.overlays {
        if !paths.insert(row.path.as_str()) || !ids.insert(row.overlay_id.as_str()) {
            bail!("authorization ledger contains a replayed event");
        }
        let path = safe_join(reference_root, &row.path)?;
        if !path.is_file() || file_sha256(&path)? != row.sha256 {
            bail!("authorization ledger event is absent or stale");
        }
        let overlay: ModuleDatasetAuthorizationOverlayV1 = read_json_typed(&path)?;
        overlay.validate()?;
        if overlay.overlay_id != row.overlay_id
            || overlay.module_id != ledger.module_id
            || overlay.snapshot_id != ledger.snapshot_id
            || overlay.parent_overlay_id != previous
        {
            bail!("authorization ledger chain is forked or cross-module");
        }
        previous = Some(overlay.overlay_id);
    }
    if previous.as_deref().unwrap_or("") != ledger.head_overlay_id {
        bail!("authorization ledger does not have exactly one current head");
    }
    Ok(())
}

fn materialize_binding(
    root: &Path,
    snapshot: &Path,
    catalog: &DataCatalogV2,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    manifest: &NormalizedDatasetManifestV2,
    lock: &ModuleDatasetLockV2,
) -> Result<ModuleDatasetActivationV1> {
    if lock.module_id != safe_id(&lock.module_id) || lock.scoring || lock.network_access {
        bail!("module data materialization is audit-only and requires a safe module ID");
    }
    let module_dir = root.join(&lock.module_id);
    if !module_dir.is_dir() {
        bail!("consumer module is absent: {}", lock.module_id);
    }
    let reference = module_dir.join("reference/mvp20");
    let channel = snapshot_channel(&catalog.snapshot_id)?;
    let snapshot_directory = channel.replace('-', "_");
    let data_root = reference.join("data").join(&snapshot_directory);
    let quarantine_root = reference.join("quarantine").join(&snapshot_directory);

    let catalog_destination = data_root.join("catalog.json");
    install_file_immutable(&snapshot.join(CATALOG_FILE), &catalog_destination)?;
    let catalog_relative = reference_relative(&reference, &catalog_destination)?;

    let manifest_source = dataset_manifest_path(snapshot, &unit.acquisition_unit_id);
    let manifest_destination = if channel == "feedback-v2" {
        reference
            .join("manifests")
            .join(format!("{}.json", safe_id(&unit.acquisition_unit_id)))
    } else {
        data_root
            .join("manifests")
            .join(format!("{}.json", safe_id(&unit.acquisition_unit_id)))
    };
    install_file_immutable(&manifest_source, &manifest_destination)?;
    let manifest_relative = reference_relative(&reference, &manifest_destination)?;

    let acquisition_source = acquisition_receipt_path(snapshot, &unit.acquisition_unit_id);
    let acquisition_destination = if channel == "feedback-v2" {
        reference.join("manifests").join(format!(
            "{}.acquisition-receipt.json",
            safe_id(&unit.acquisition_unit_id)
        ))
    } else {
        data_root.join("manifests").join(format!(
            "{}.acquisition-receipt.json",
            safe_id(&unit.acquisition_unit_id)
        ))
    };
    install_file_immutable(&acquisition_source, &acquisition_destination)?;
    let acquisition_relative = reference_relative(&reference, &acquisition_destination)?;

    let lock_source = lock_path(snapshot, &lock.module_id, &lock.dataset_id);
    let lock_destination = if channel == "feedback-v2" {
        reference
            .join("locks")
            .join(format!("{}.json", safe_id(&lock.dataset_id)))
    } else {
        data_root
            .join("locks")
            .join(format!("{}.json", safe_id(&lock.dataset_id)))
    };
    install_file_immutable(&lock_source, &lock_destination)?;

    let quarantined = manifest.quarantined;
    let rights_destination = if quarantined {
        quarantine_root
            .join("exclusions")
            .join(format!("{}.rights.json", safe_id(&manifest.dataset_id)))
    } else {
        data_root
            .join("rights")
            .join(format!("{}.json", safe_id(&decision.rights_decision_id)))
    };
    let rights_artifact = json!({
        "schema": "amphora.module-rights-decision.v1",
        "module_id": lock.module_id,
        "snapshot_id": catalog.snapshot_id,
        "dataset_id": manifest.dataset_id,
        "decision": decision,
        "promotion_eligible_unchanged_by_materialization": true,
    });
    persist_immutable(&rights_destination, &canonical_bytes(&rights_artifact)?)?;
    let rights_relative = reference_relative(&reference, &rights_destination)?;

    let normalized_source = safe_join(snapshot, &manifest.normalized_path)?;
    let object_destination = if quarantined {
        quarantine_root
            .join("objects")
            .join(format!("{}.jsonl.gz", manifest.normalized_sha256))
    } else {
        data_root
            .join("objects")
            .join(format!("{}.jsonl.gz", manifest.normalized_sha256))
    };
    install_file_immutable(&normalized_source, &object_destination)?;
    let object_relative = reference_relative(&reference, &object_destination)?;

    let derived_destination = if quarantined {
        quarantine_root
            .join("derived")
            .join(format!("{}.jsonl.gz", safe_id(&manifest.dataset_id)))
    } else {
        data_root
            .join("derived")
            .join(format!("{}.jsonl.gz", safe_id(&manifest.dataset_id)))
    };
    build_derived_view(&normalized_source, &derived_destination, manifest)?;
    let derived_relative = reference_relative(&reference, &derived_destination)?;

    let identity_source = safe_join(snapshot, &manifest.identity_index_path)?;
    let identity_destination = if quarantined {
        quarantine_root.join("exclusions").join(format!(
            "{}.canonical-identity.jsonl.gz",
            safe_id(&manifest.dataset_id)
        ))
    } else {
        data_root.join("splits").join(format!(
            "{}.canonical-identity.jsonl.gz",
            safe_id(&manifest.dataset_id)
        ))
    };
    install_file_immutable(&identity_source, &identity_destination)?;
    let identity_relative = reference_relative(&reference, &identity_destination)?;

    let leakage = read_json_typed::<Value>(&snapshot.join("reports/leakage-report.json"))
        .unwrap_or_else(|_| json!({}));
    let point2_overlap = leakage
        .get("point2_train_test_identity_overlap_count")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let cross_dataset_overlap = leakage
        .get("cross_dataset_canonical_identity_overlap_count")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let point2_split = matches!(
        unit.acquisition_unit_id.as_str(),
        "point2_train_split" | "point2_test_split"
    );
    let split_destination = if quarantined {
        quarantine_root
            .join("exclusions")
            .join(format!("{}.json", safe_id(&manifest.dataset_id)))
    } else {
        data_root
            .join("splits")
            .join(format!("{}.json", safe_id(&manifest.dataset_id)))
    };
    let split = json!({
        "schema": "amphora.module-dataset-split.v1",
        "module_id": lock.module_id,
        "snapshot_id": catalog.snapshot_id,
        "dataset_id": manifest.dataset_id,
        "partition": if quarantined { "QUARANTINE_EXCLUDED" } else { "REFERENCE_ONLY" },
        "assignment_method": "CANONICAL_IDENTITY_GROUP_SINGLE_PARTITION",
        "random_row_split_forbidden": true,
        "family_scaffold_source_site_lot_study_time_confinement_required": true,
        "canonical_identity_index_path": identity_relative,
        "canonical_identity_index_sha256": file_sha256(&identity_destination)?,
        "known_cross_dataset_identity_overlap_count": cross_dataset_overlap,
        "point2_train_test_identity_overlap_count": point2_overlap,
        "zero_leakage": !point2_split || point2_overlap == 0,
        "status": if point2_split && point2_overlap > 0 { "FAILED_REQUIRES_REGROUP_OR_EXCLUSION" } else if quarantined { "EXCLUDED_BY_RIGHTS" } else { "REFERENCE_ONLY_NO_BENCHMARK_SPLIT_CLAIM" },
    });
    persist_immutable(&split_destination, &canonical_bytes(&split)?)?;
    let split_relative = reference_relative(&reference, &split_destination)?;

    let report_destination = if quarantined {
        quarantine_root
            .join("exclusions")
            .join(format!("{}.report.json", safe_id(&manifest.dataset_id)))
    } else {
        data_root
            .join("reports")
            .join(format!("{}.json", safe_id(&manifest.dataset_id)))
    };
    if report_destination.is_file() {
        let report: Value = read_json_typed(&report_destination)?;
        if report.get("module_id").and_then(Value::as_str) != Some(lock.module_id.as_str())
            || report.get("dataset_id").and_then(Value::as_str) != Some(lock.dataset_id.as_str())
            || report.get("normalized_sha256").and_then(Value::as_str)
                != Some(lock.normalized_artifact_sha256.as_str())
            || report.get("rows_consumed").and_then(Value::as_u64) != Some(manifest.record_count)
        {
            bail!("immutable module consumer report conflicts with current activation");
        }
    } else {
        let report = consumer_report(snapshot, lock, manifest)?;
        persist_immutable(&report_destination, &canonical_bytes(&report)?)?;
    }

    let accepted_row_count = if quarantined {
        0
    } else {
        manifest.record_count
    };
    let activation = ModuleDatasetActivationV1 {
        schema: ACTIVATION_SCHEMA.into(),
        module_id: lock.module_id.clone(),
        snapshot_id: catalog.snapshot_id.clone(),
        dataset_id: manifest.dataset_id.clone(),
        acquisition_unit_id: unit.acquisition_unit_id.clone(),
        catalog_path: catalog_relative,
        catalog_sha256: file_sha256(&catalog_destination)?,
        acquisition_receipt_path: acquisition_relative,
        acquisition_receipt_sha256: file_sha256(&acquisition_destination)?,
        rights_receipt_path: rights_relative,
        rights_receipt_sha256: file_sha256(&rights_destination)?,
        // This legacy structural flag is deliberately non-authoritative. A
        // signed receipt plus append-only authorization overlay is required.
        rights_reviewed: false,
        dataset_manifest_path: manifest_relative,
        dataset_manifest_sha256: file_sha256(&manifest_destination)?,
        normalized_object_path: object_relative,
        normalized_object_sha256: file_sha256(&object_destination)?,
        derived_view_path: derived_relative,
        derived_view_sha256: file_sha256(&derived_destination)?,
        split_path: split_relative,
        split_sha256: file_sha256(&split_destination)?,
        accepted_row_count,
        rejected_row_count: manifest.rejection_count,
        excluded_row_count: if quarantined {
            manifest.record_count
        } else {
            0
        },
        quarantined_row_count: if quarantined {
            manifest.record_count
        } else {
            0
        },
        evidence_class: manifest.evidence_class.clone(),
        rights_class: manifest.rights_class.clone(),
        consumer: lock.consumer.clone(),
        scoring: false,
        authority_limit: lock.authority_limit.clone(),
        claim_locks: [
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
        ]
        .into_iter()
        .map(|name| (name.into(), true))
        .collect(),
        generator_version: env!("CARGO_PKG_VERSION").into(),
        deterministic_command: format!(
            "data consume --snapshot {} --module {} --dataset {}",
            channel.replace('-', "/"),
            lock.module_id,
            lock.dataset_id
        ),
        zero_network: true,
        candidate_input_excluded: true,
    };
    merge_activation(&data_root.join("activation.v1.json"), &activation)?;
    Ok(activation)
}

fn build_derived_view(
    normalized: &Path,
    destination: &Path,
    manifest: &NormalizedDatasetManifestV2,
) -> Result<()> {
    if destination.is_file() {
        return Ok(());
    }
    let temporary = temporary_path(destination);
    prepare_temporary(&temporary)?;
    let mut writer = deterministic_gzip(File::create(&temporary)?);
    let decoder = GzDecoder::new(File::open(normalized)?);
    let reader = BufReader::new(decoder);
    let mut count = 0_u64;
    for line in std::io::BufRead::lines(reader) {
        let line = line?;
        if line.is_empty() {
            continue;
        }
        let row: NormalizedRecordV2 = serde_json::from_str(&line)?;
        if row.dataset_id != manifest.dataset_id
            || row.acquisition_unit_id != manifest.acquisition_unit_id
            || row.evidence_class != manifest.evidence_class
            || row.rights_class != manifest.rights_class
        {
            bail!("normalized row cannot be bound to the requested module derived view");
        }
        write_json_line(&mut writer, &DerivedRecordV1::from(row))?;
        count += 1;
    }
    writer.finish()?;
    if count != manifest.record_count {
        fs::remove_file(&temporary)?;
        bail!("derived row count does not match normalized manifest");
    }
    install_generated(&temporary, destination)
}

fn merge_activation(path: &Path, activation: &ModuleDatasetActivationV1) -> Result<()> {
    let mut set = if path.is_file() {
        let existing: ModuleDatasetActivationSetV1 = read_json_typed(path)?;
        if existing.schema != ACTIVATION_SET_SCHEMA
            || existing.module_id != activation.module_id
            || existing.snapshot_id != activation.snapshot_id
        {
            bail!("existing module activation set has conflicting identity");
        }
        existing
    } else {
        ModuleDatasetActivationSetV1 {
            schema: ACTIVATION_SET_SCHEMA.into(),
            module_id: activation.module_id.clone(),
            snapshot_id: activation.snapshot_id.clone(),
            activations: Vec::new(),
        }
    };
    if let Some(existing) = set
        .activations
        .iter()
        .find(|row| row.dataset_id == activation.dataset_id)
    {
        if existing != activation {
            bail!("immutable module dataset activation conflicts with existing evidence revision");
        }
        return Ok(());
    }
    set.activations.push(activation.clone());
    set.activations
        .sort_by(|left, right| left.dataset_id.cmp(&right.dataset_id));
    write_json_generated(path, &serde_json::to_value(set)?)
}

fn install_file_immutable(source: &Path, destination: &Path) -> Result<()> {
    let expected_hash = file_sha256(source)?;
    if destination.exists() {
        if destination.is_file() && file_sha256(destination)? == expected_hash {
            return Ok(());
        }
        bail!(
            "immutable materialization destination differs: {}",
            destination.display()
        );
    }
    fs::create_dir_all(
        destination
            .parent()
            .ok_or_else(|| anyhow!("materialization destination has no parent"))?,
    )?;
    fs::copy(source, destination)?;
    if file_sha256(destination)? != expected_hash {
        bail!("materialized file failed post-copy hash verification");
    }
    Ok(())
}

fn reference_relative(reference: &Path, path: &Path) -> Result<String> {
    let relative = path
        .strip_prefix(reference)
        .context("data materialization escaped module reference/mvp20")?;
    if relative.components().any(|component| {
        matches!(component, Component::ParentDir | Component::RootDir)
            || component.as_os_str() == "evidence"
            || component.as_os_str() == "movement"
            || component.as_os_str() == "ip"
            || component.as_os_str() == "registry"
    }) {
        bail!("data materialization targeted a protected evidence path");
    }
    Ok(relative.to_string_lossy().replace('\\', "/"))
}

fn write_json_generated(path: &Path, value: &Value) -> Result<()> {
    let bytes = canonical_bytes(value)?;
    if path.is_file() && fs::read(path)? == bytes {
        return Ok(());
    }
    fs::create_dir_all(
        path.parent()
            .ok_or_else(|| anyhow!("generated JSON path has no parent"))?,
    )?;
    let temporary = temporary_path(path);
    prepare_temporary(&temporary)?;
    fs::write(&temporary, bytes)?;
    fs::rename(temporary, path)?;
    Ok(())
}

pub fn audit(root: &Path, snapshot_arg: &Path, write_reports: bool) -> Result<()> {
    let snapshot = rooted(root, snapshot_arg)?;
    let catalog = read_catalog(&snapshot)?;
    validate_catalog(root, &snapshot, &catalog)?;
    let rights = rights_by_unit(&catalog);
    let mut issues = Vec::new();
    let mut inventory = BTreeMap::from([(
        CATALOG_FILE.into(),
        file_sha256(&snapshot.join(CATALOG_FILE))?,
    )]);
    let mut utilization = Vec::new();
    let mut identity_first_unit = HashMap::new();
    let mut identity_overlap_pairs = BTreeMap::new();
    let mut normalized_count = 0_u64;
    let mut acquired_count = 0_u64;
    let mut rejection_count = 0_u64;
    let mut row_count = 0_u64;
    let mut pending_unit_count = 0_u64;
    let mut declared_blocked_unit_count = 0_u64;
    for unit in &catalog.acquisition_units {
        let receipt_path = acquisition_receipt_path(&snapshot, &unit.acquisition_unit_id);
        if !receipt_path.is_file() {
            if unit.blocked_reason.is_some() {
                declared_blocked_unit_count += 1;
            } else {
                pending_unit_count += 1;
            }
            continue;
        }
        acquired_count += 1;
        let receipt: AcquisitionReceiptV2 = read_json_typed(&receipt_path)?;
        inventory.insert(
            relative(&snapshot, &receipt_path),
            file_sha256(&receipt_path)?,
        );
        if let Err(error) = verify_acquisition_receipt(&receipt) {
            issues.push(format!(
                "invalid acquisition signature for {}: {error}",
                unit.acquisition_unit_id
            ));
            continue;
        }
        let raw = snapshot.join(&receipt.raw_object_path);
        if !raw.is_file()
            || file_sha256(&raw)? != receipt.sha256
            || raw.metadata()?.len() != receipt.bytes
        {
            issues.push(format!(
                "raw receipt mismatch: {}",
                unit.acquisition_unit_id
            ));
            continue;
        }
        if unit.parser == ParserKind::OrdGitLfsTree {
            if let Err(error) = verify_installed_ord_tree(&snapshot, unit, &receipt) {
                issues.push(format!(
                    "ORD tree verification failed for {}: {error}",
                    unit.acquisition_unit_id
                ));
                continue;
            }
        }
        inventory.insert(relative(&snapshot, &raw), receipt.sha256.clone());
        if unit.consumers.is_empty() {
            issues.push(format!(
                "acquired child has no executable consumer: {}",
                unit.acquisition_unit_id
            ));
            continue;
        }
        let manifest_path = dataset_manifest_path(&snapshot, &unit.acquisition_unit_id);
        if !manifest_path.is_file() {
            issues.push(format!(
                "acquired child is not normalized: {}",
                unit.acquisition_unit_id
            ));
            continue;
        }
        let manifest: NormalizedDatasetManifestV2 = read_json_typed(&manifest_path)?;
        if let Err(error) = validate_manifest(
            &snapshot,
            unit,
            rights[unit.acquisition_unit_id.as_str()],
            &manifest,
        ) {
            issues.push(format!("{}: {error}", unit.acquisition_unit_id));
            continue;
        }
        normalized_count += 1;
        row_count += manifest.record_count;
        rejection_count += manifest.rejection_count;
        inventory.insert(
            relative(&snapshot, &manifest_path),
            file_sha256(&manifest_path)?,
        );
        inventory.insert(
            manifest.normalized_path.clone(),
            manifest.normalized_sha256.clone(),
        );
        inventory.insert(
            manifest.rejection_path.clone(),
            manifest.rejection_sha256.clone(),
        );
        inventory.insert(
            manifest.identity_index_path.clone(),
            manifest.identity_index_sha256.clone(),
        );
        inventory.insert(
            manifest.duplicate_index_path.clone(),
            manifest.duplicate_index_sha256.clone(),
        );
        audit_identity_overlap(
            &snapshot.join(&manifest.identity_index_path),
            &unit.acquisition_unit_id,
            &mut identity_first_unit,
            &mut identity_overlap_pairs,
        )?;
        let mut dataset_report: Option<Value> = None;
        for consumer in &unit.consumers {
            let path = lock_path(&snapshot, &consumer.module_id, &manifest.dataset_id);
            if !path.is_file() {
                issues.push(format!(
                    "missing module source lock for {} -> {}",
                    unit.acquisition_unit_id, consumer.module_id
                ));
                continue;
            }
            let lock: ModuleDatasetLockV2 = read_json_typed(&path)?;
            inventory.insert(relative(&snapshot, &path), file_sha256(&path)?);
            if let Err(error) = validate_lock(&snapshot, &lock) {
                issues.push(format!(
                    "invalid module source lock {}: {error}",
                    path.display()
                ));
                continue;
            }
            let report = if let Some(mut report) = dataset_report.clone() {
                report["module_id"] = Value::String(lock.module_id.clone());
                report["consumer"] = serde_json::to_value(&lock.consumer)?;
                report["scoring"] = Value::Bool(lock.scoring);
                report["authority_limit"] = Value::String(lock.authority_limit.clone());
                Ok(report)
            } else {
                consumer_report(&snapshot, &lock, &manifest)
            };
            match report {
                Ok(report) => {
                    if dataset_report.is_none() {
                        dataset_report = Some(report.clone());
                    }
                    utilization.push(report)
                }
                Err(error) => issues.push(format!(
                    "consumer failed for {} -> {}: {error}",
                    unit.acquisition_unit_id, consumer.module_id
                )),
            }
        }
    }
    let activation_audit = audit_materialized_activations(root, &snapshot, &catalog)?;
    issues.extend(activation_audit.issues.clone());
    let rights_report = json!({
        "schema": "amphora.data-rights-report.v2",
        "snapshot_id": catalog.snapshot_id,
        "decisions": catalog.rights_decisions,
    });
    let utilization_report = json!({
        "schema": "amphora.source-module-utilization-report.v2",
        "snapshot_id": catalog.snapshot_id,
        "consumers": utilization,
    });
    let inventory_report = json!({
        "schema": "amphora.sha256-inventory.v2",
        "snapshot_id": catalog.snapshot_id,
        "files": inventory,
    });
    let cross_dataset_overlap_count = identity_overlap_pairs.values().sum::<u64>();
    let point2_split_overlap_count = identity_overlap_pairs
        .get("point2_test_split<->point2_train_split")
        .copied()
        .unwrap_or(0);
    let leakage_report = json!({
        "schema": "amphora.data-leakage-report.v2",
        "snapshot_id": catalog.snapshot_id,
        "promotion_scoring_locks": catalog.acquisition_units.iter().flat_map(|unit| unit.consumers.iter().map(move |consumer| (unit, consumer))).filter(|(_, consumer)| consumer.scoring).count(),
        "prohibited_scoring_locks": catalog.acquisition_units.iter().flat_map(|unit| unit.consumers.iter().map(move |consumer| (unit, consumer))).filter(|(unit, consumer)| consumer.scoring && (!rights[unit.acquisition_unit_id.as_str()].promotion_eligible || forbidden_promotion_evidence(&unit.evidence_class))).count(),
        "cross_dataset_canonical_identity_overlap_count": cross_dataset_overlap_count,
        "identity_overlap_pairs": identity_overlap_pairs,
        "point2_train_test_identity_overlap_count": point2_split_overlap_count,
        "family_scaffold_source_lot_and_time_split_status": "REQUIRES_SEPARATE_LOCKED_BENCHMARK_SPLIT; DATA_INGESTION_NEVER_ASSIGNS_PROMOTION_SPLITS",
        "status": if point2_split_overlap_count == 0 { "NO_KNOWN_SPLIT_ONLY_IDENTITY_OVERLAP" } else { "DIAGNOSTIC_OVERLAP_PRESENT_NO_SCORING_AUTHORITY" },
    });
    if write_reports {
        persist_report(&snapshot, "rights-report.json", &rights_report)?;
        persist_report(
            &snapshot,
            "source-module-utilization.json",
            &utilization_report,
        )?;
        persist_report(&snapshot, "sha256-inventory.json", &inventory_report)?;
        persist_report(&snapshot, "leakage-report.json", &leakage_report)?;
    }
    let status = if issues.is_empty() {
        "PASS"
    } else {
        "FAIL_CLOSED"
    };
    let report = json!({
        "schema": "amphora.data-audit-report.v2",
        "snapshot_id": catalog.snapshot_id,
        "status": status,
        "source_intent_count": catalog.source_intents.len(),
        "acquisition_unit_count": catalog.acquisition_units.len(),
        "acquired_unit_count": acquired_count,
        "normalized_unit_count": normalized_count,
        "pending_unit_count": pending_unit_count,
        "declared_blocked_unit_count": declared_blocked_unit_count,
        "normalized_row_count": row_count,
        "rejection_count": rejection_count,
        "materialized_binding_count": activation_audit.binding_count,
        "expected_materialized_binding_count": catalog.acquisition_units.iter().filter(|unit| dataset_manifest_path(&snapshot, &unit.acquisition_unit_id).is_file()).map(|unit| unit.consumers.len()).sum::<usize>(),
        "rights_reviewed_binding_count": activation_audit.rights_reviewed_count,
        "quarantine_binding_count": activation_audit.quarantine_count,
        "issues": issues,
        "v1_immutable": true,
    });
    if write_reports {
        persist_report(&snapshot, "audit-report.json", &report)?;
        if root.join("module-manifest.json").is_file()
            && root.join("amphora-candidate-contract").is_dir()
        {
            let phase0 = crate::phase0::portfolio_status(root)?;
            let phase1 = crate::phase1::portfolio_status_from_phase0(root, &phase0)?;
            crate::dashboard::write(root, &phase0, &phase1)?;
        }
    }
    emit_jsonl(&report)?;
    if status == "PASS" {
        Ok(())
    } else {
        bail!(
            "{} data audit failed closed",
            snapshot_channel(&catalog.snapshot_id)?
        )
    }
}

struct ActivationAudit {
    binding_count: usize,
    rights_reviewed_count: usize,
    quarantine_count: usize,
    issues: Vec<String>,
}

fn audit_materialized_activations(
    root: &Path,
    snapshot: &Path,
    catalog: &DataCatalogV2,
) -> Result<ActivationAudit> {
    let full_workspace = root.join("module-manifest.json").is_file();
    let mut expected = BTreeSet::new();
    let mut observed = BTreeSet::new();
    let mut rights_reviewed_count = 0;
    let mut quarantine_count = 0;
    let mut issues = Vec::new();
    for unit in &catalog.acquisition_units {
        if !snapshot
            .join("manifests")
            .join(format!("{}.json", safe_id(&unit.acquisition_unit_id)))
            .is_file()
        {
            continue;
        }
        for consumer in &unit.consumers {
            expected.insert((consumer.module_id.clone(), unit.acquisition_unit_id.clone()));
        }
    }
    for module in expected
        .iter()
        .map(|(module, _)| module)
        .collect::<BTreeSet<_>>()
    {
        let reference = root.join(module).join("reference/mvp20");
        let path = reference.join(format!(
            "data/{}/activation.v1.json",
            snapshot_channel(&catalog.snapshot_id)?.replace('-', "_")
        ));
        if !path.is_file() {
            if full_workspace {
                issues.push(format!("module activation set is absent: {module}"));
            }
            continue;
        }
        let set: ModuleDatasetActivationSetV1 = match read_json_typed(&path) {
            Ok(set) => set,
            Err(error) => {
                issues.push(format!("invalid module activation set {module}: {error}"));
                continue;
            }
        };
        if set.schema != ACTIVATION_SET_SCHEMA
            || set.module_id != *module
            || set.snapshot_id != catalog.snapshot_id
        {
            issues.push(format!("module activation set identity mismatch: {module}"));
            continue;
        }
        for activation in set.activations {
            let key = (
                activation.module_id.clone(),
                activation.acquisition_unit_id.clone(),
            );
            if !expected.contains(&key) || !observed.insert(key.clone()) {
                issues.push(format!(
                    "unexpected or duplicate module activation: {} -> {}",
                    key.1, key.0
                ));
                continue;
            }
            if activation.schema != ACTIVATION_SCHEMA
                || activation.module_id != *module
                || activation.snapshot_id != catalog.snapshot_id
                || activation.scoring
                || !activation.zero_network
                || !activation.candidate_input_excluded
            {
                issues.push(format!(
                    "activation policy mismatch: {} -> {}",
                    activation.acquisition_unit_id, module
                ));
                continue;
            }
            let mut artifact_valid = true;
            for (relative, expected_hash) in [
                (&activation.catalog_path, &activation.catalog_sha256),
                (
                    &activation.acquisition_receipt_path,
                    &activation.acquisition_receipt_sha256,
                ),
                (
                    &activation.rights_receipt_path,
                    &activation.rights_receipt_sha256,
                ),
                (
                    &activation.dataset_manifest_path,
                    &activation.dataset_manifest_sha256,
                ),
                (
                    &activation.normalized_object_path,
                    &activation.normalized_object_sha256,
                ),
                (
                    &activation.derived_view_path,
                    &activation.derived_view_sha256,
                ),
                (&activation.split_path, &activation.split_sha256),
            ] {
                let path = match safe_join(&reference, relative) {
                    Ok(path) => path,
                    Err(_) => {
                        artifact_valid = false;
                        break;
                    }
                };
                if !path.is_file() || file_sha256(&path).ok().as_ref() != Some(expected_hash) {
                    artifact_valid = false;
                    break;
                }
            }
            if !artifact_valid {
                issues.push(format!(
                    "activation artifact absent, escaped, or stale: {} -> {}",
                    activation.acquisition_unit_id, module
                ));
            }
            rights_reviewed_count += usize::from(activation.rights_reviewed);
            quarantine_count += usize::from(activation.quarantined_row_count > 0);
        }
    }
    if full_workspace {
        for (module, unit) in expected.difference(&observed) {
            issues.push(format!("missing materialized binding: {unit} -> {module}"));
        }
        if snapshot_channel(&catalog.snapshot_id)? == "feedback-v2" && expected.len() != 30 {
            issues.push(format!(
                "frozen feedback/v2 must resolve 30 bindings; observed {}",
                expected.len()
            ));
        }
    }
    Ok(ActivationAudit {
        binding_count: observed.len(),
        rights_reviewed_count,
        quarantine_count,
        issues,
    })
}

fn acquire_unit(
    root: &Path,
    snapshot: &Path,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    manual_import: Option<&Path>,
) -> Result<AcquisitionReceiptV2> {
    if decision.rights_class == RightsClass::Credentialed && unit.credential_ref.is_none() {
        bail!("credentialed acquisition lacks an opaque credential reference");
    }
    if decision.rights_class == RightsClass::ManualExport && manual_import.is_some() {
        let authorization = decision.decision_receipt.as_deref().ok_or_else(|| {
            anyhow!("manual export lacks a signed authorization receipt reference")
        })?;
        let authorization_path = rooted(root, Path::new(authorization))?;
        if !authorization_path.is_file() {
            bail!("manual export authorization receipt is absent");
        }
    }
    if unit.parser == ParserKind::OrdGitLfsTree {
        return acquire_ord_git_lfs_tree(root, snapshot, unit, decision, manual_import);
    }
    let receipt_path = acquisition_receipt_path(snapshot, &unit.acquisition_unit_id);
    if receipt_path.is_file() {
        let receipt: AcquisitionReceiptV2 = read_json_typed(&receipt_path)?;
        verify_acquisition_receipt(&receipt)?;
        let object = safe_join(snapshot, &receipt.raw_object_path)?;
        if receipt.acquisition_unit_id != unit.acquisition_unit_id
            || receipt.source_intent_id != unit.source_intent_id
            || receipt.rights_decision_id != decision.rights_decision_id
            || receipt.quarantined != decision.rights_class.quarantined()
            || unit
                .expected_sha256
                .as_ref()
                .is_some_and(|expected| expected != &receipt.sha256)
            || unit
                .expected_bytes
                .is_some_and(|expected| expected != receipt.bytes)
            || !object.is_file()
            || object.metadata()?.len() != receipt.bytes
            || file_sha256(&object)? != receipt.sha256
        {
            bail!("immutable acquisition receipt conflicts with current acquisition unit");
        }
        let staging = snapshot
            .join("staging")
            .join(format!("{}.part", safe_id(&unit.acquisition_unit_id)));
        cleanup_completed_download(snapshot, &staging)?;
        return Ok(receipt);
    }
    let source = if let Some(path) = manual_import {
        rooted(root, path)?
    } else if let Some(path) = &unit.cache_import_path {
        rooted(root, Path::new(path))?
    } else {
        download_to_staging(snapshot, unit)?
    };
    if !source.is_file() {
        bail!("acquisition source is absent: {}", source.display());
    }
    let observed_hash = file_sha256(&source)?;
    let observed_bytes = source.metadata()?.len();
    if let Some(expected) = &unit.expected_sha256 {
        if &observed_hash != expected {
            bail!("SHA-256 mismatch for {}", unit.acquisition_unit_id);
        }
    } else if manual_import.is_none() {
        bail!("non-manual acquisition has no expected SHA-256");
    }
    if let Some(expected) = unit.expected_bytes {
        if observed_bytes != expected {
            bail!(
                "content-length mismatch for {}: expected {expected}, observed {observed_bytes}",
                unit.acquisition_unit_id
            );
        }
    }
    let quarantine = decision.rights_class.quarantined();
    let object_relative = if quarantine {
        format!("quarantine/raw/objects/{observed_hash}")
    } else {
        format!("raw/objects/{observed_hash}")
    };
    let object = snapshot.join(&object_relative);
    install_content_object(&source, &object, &observed_hash, observed_bytes)?;
    let method = if manual_import.is_some() && decision.rights_class == RightsClass::ManualExport {
        "AUTHORIZED_MANUAL_EXPORT_IMPORT"
    } else if manual_import.is_some() {
        "VERIFIED_LOCAL_IMPORT"
    } else if unit.cache_import_path.is_some() {
        "VERIFIED_CACHE_IMPORT"
    } else if unit.credential_ref.is_some() {
        "RESUMABLE_CREDENTIALED_DOWNLOAD"
    } else {
        "RESUMABLE_DOWNLOAD"
    };
    if receipt_path.is_file() {
        let receipt: AcquisitionReceiptV2 = read_json_typed(&receipt_path)?;
        verify_acquisition_receipt(&receipt)?;
        if receipt.acquisition_unit_id != unit.acquisition_unit_id
            || receipt.source_intent_id != unit.source_intent_id
            || receipt.raw_object_path != object_relative
            || receipt.sha256 != observed_hash
            || receipt.bytes != observed_bytes
            || receipt.rights_decision_id != decision.rights_decision_id
            || receipt.quarantined != quarantine
        {
            bail!("immutable acquisition receipt conflicts with current acquisition");
        }
        cleanup_completed_download(snapshot, &source)?;
        return Ok(receipt);
    }
    let mut receipt = AcquisitionReceiptV2 {
        schema: "amphora.acquisition-receipt.v2".into(),
        acquisition_unit_id: unit.acquisition_unit_id.clone(),
        source_intent_id: unit.source_intent_id.clone(),
        raw_object_path: object_relative,
        sha256: observed_hash,
        bytes: observed_bytes,
        acquisition_method: method.into(),
        source_url: unit.source_url.clone(),
        credential_ref: unit.credential_ref.clone(),
        rights_decision_id: decision.rights_decision_id.clone(),
        quarantined: quarantine,
        signature: None,
    };
    sign_acquisition_receipt(root, &mut receipt)?;
    persist_immutable(
        &receipt_path,
        &canonical_bytes(&serde_json::to_value(&receipt)?)?,
    )?;
    cleanup_completed_download(snapshot, &source)?;
    Ok(receipt)
}

fn acquire_ord_git_lfs_tree(
    root: &Path,
    snapshot: &Path,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    manual_import: Option<&Path>,
) -> Result<AcquisitionReceiptV2> {
    let tree = unit
        .ord_git_lfs_tree
        .as_ref()
        .ok_or_else(|| anyhow!("ORD Git LFS object manifest is absent"))?;
    let receipt_path = acquisition_receipt_path(snapshot, &unit.acquisition_unit_id);
    if receipt_path.is_file() {
        let receipt: AcquisitionReceiptV2 = read_json_typed(&receipt_path)?;
        verify_acquisition_receipt(&receipt)?;
        if receipt.acquisition_unit_id != unit.acquisition_unit_id
            || receipt.source_intent_id != unit.source_intent_id
            || receipt.rights_decision_id != decision.rights_decision_id
            || !matches!(
                receipt.acquisition_method.as_str(),
                "ORD_GIT_LFS_TREE_VERIFIED_LOCAL_CHECKOUT" | "ORD_VERIFIED_MIRROR_DIRECTORY_IMPORT"
            )
            || receipt.quarantined != decision.rights_class.quarantined()
        {
            bail!("immutable ORD acquisition receipt conflicts with the catalog");
        }
        verify_installed_ord_tree(snapshot, unit, &receipt)?;
        return Ok(receipt);
    }

    let source = if let Some(path) = manual_import {
        rooted(root, path)?
    } else if let Some(path) = &unit.cache_import_path {
        rooted(root, Path::new(path))?
    } else {
        bail!("ORD_GIT_LFS_TREE requires --import or a cache_import_path checkout");
    };
    if !source.is_dir() {
        bail!("ORD acquisition source is not a directory");
    }
    let expected_paths = tree
        .objects
        .iter()
        .map(|object| object.path.clone())
        .collect::<BTreeSet<_>>();
    let excluded_parquet = locked_ord_parquet_paths(root)?;
    let is_checkout = source.join(".git").exists();
    let acquisition_method = if is_checkout {
        verify_ord_checkout(&source, tree, &expected_paths, &excluded_parquet)?;
        "ORD_GIT_LFS_TREE_VERIFIED_LOCAL_CHECKOUT"
    } else {
        "ORD_VERIFIED_MIRROR_DIRECTORY_IMPORT"
    };

    let mut verified_sources = Vec::with_capacity(tree.objects.len());
    for object in &tree.objects {
        let source_object = locate_ord_source_object(&source, object)?;
        let metadata = fs::symlink_metadata(&source_object)?;
        if metadata.file_type().is_symlink()
            || !metadata.is_file()
            || metadata.len() != object.bytes
            || file_sha256(&source_object)? != object.raw_sha256
        {
            bail!("ORD object failed LFS OID, size, or raw SHA-256 verification");
        }
        let mut prefix = [0_u8; 80];
        let prefix_len = File::open(&source_object)?.read(&mut prefix)?;
        if prefix[..prefix_len].starts_with(b"version https://git-lfs.github.com/spec/v1") {
            bail!("ORD object is an unresolved Git LFS pointer");
        }
        let compressed = fs::read(&source_object)?;
        let maximum_decompressed = object
            .bytes
            .saturating_mul(200)
            .clamp(16 * 1024 * 1024, 2 * 1024 * 1024 * 1024);
        decompress_gzip_bounded(&compressed, maximum_decompressed)
            .with_context(|| format!("validating gzip CRC/EOF for {}", object.path))?;
        verified_sources.push((source_object, object));
    }

    // Install only after all 550 catalog objects have independently passed
    // path/type, size, LFS SHA-256, pointer, and gzip validation.
    for (source_object, object) in &verified_sources {
        let installed = snapshot
            .join(if decision.rights_class.quarantined() {
                "quarantine/raw/ord/objects"
            } else {
                "raw/ord/objects"
            })
            .join(&object.raw_sha256);
        install_content_object(source_object, &installed, &object.raw_sha256, object.bytes)?;
    }

    let manifest = json!({
        "schema": "amphora.ord-git-lfs-tree-manifest.v1",
        "repository_url": tree.repository_url,
        "git_commit": tree.git_commit,
        "commit_tree": ORD_DATA_COMMIT_TREE,
        "tree_prefix": tree.tree_prefix,
        "object_manifest_sha256": tree.object_manifest_sha256,
        "object_count": tree.object_count,
        "total_bytes": tree.total_bytes,
        "gzip_crc_eof_validated_objects": tree.object_count,
        "excluded_parquet_companion_count": excluded_parquet.len(),
        "excluded_parquet_companions": excluded_parquet,
        "acquisition_method": acquisition_method,
        "objects": tree.objects,
    });
    let manifest_bytes = canonical_bytes(&manifest)?;
    let manifest_sha256 = bytes_sha256(&manifest_bytes);
    if unit
        .expected_sha256
        .as_ref()
        .is_some_and(|expected| expected != &manifest_sha256)
        || unit
            .expected_bytes
            .is_some_and(|expected| expected != manifest_bytes.len() as u64)
    {
        bail!("ORD complete object manifest hash or size is stale");
    }
    let object_relative = if decision.rights_class.quarantined() {
        format!("quarantine/raw/objects/{manifest_sha256}")
    } else {
        format!("raw/objects/{manifest_sha256}")
    };
    let manifest_object = snapshot.join(&object_relative);
    fs::create_dir_all(snapshot.join("staging"))?;
    let temporary = snapshot.join("staging").join(format!(
        "{}.manifest.part",
        safe_id(&unit.acquisition_unit_id)
    ));
    fs::write(&temporary, &manifest_bytes)?;
    install_content_object(
        &temporary,
        &manifest_object,
        &manifest_sha256,
        manifest_bytes.len() as u64,
    )?;
    fs::remove_file(temporary)?;

    let mut receipt = AcquisitionReceiptV2 {
        schema: "amphora.acquisition-receipt.v2".into(),
        acquisition_unit_id: unit.acquisition_unit_id.clone(),
        source_intent_id: unit.source_intent_id.clone(),
        raw_object_path: object_relative,
        sha256: manifest_sha256,
        bytes: manifest_bytes.len() as u64,
        acquisition_method: acquisition_method.into(),
        source_url: unit.source_url.clone(),
        credential_ref: None,
        rights_decision_id: decision.rights_decision_id.clone(),
        quarantined: decision.rights_class.quarantined(),
        signature: None,
    };
    sign_acquisition_receipt(root, &mut receipt)?;
    persist_immutable(
        &receipt_path,
        &canonical_bytes(&serde_json::to_value(&receipt)?)?,
    )?;
    let complete_tree_path = receipt_path.with_file_name(format!(
        "{}.complete-tree.v1.json",
        safe_id(&unit.acquisition_unit_id)
    ));
    persist_immutable(&complete_tree_path, &manifest_bytes)?;
    verify_installed_ord_tree(snapshot, unit, &receipt)?;
    Ok(receipt)
}

fn locked_ord_parquet_paths(root: &Path) -> Result<BTreeSet<String>> {
    let raw = fs::read_to_string(root.join(ORD_PARQUET_LOCK_PATH))?;
    let paths = raw
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(str::to_owned)
        .collect::<BTreeSet<_>>();
    if paths.len() != ORD_PARQUET_COMPANIONS
        || paths
            .iter()
            .any(|path| !path.starts_with("data/") || !path.ends_with(".parquet"))
    {
        bail!("pinned ORD Parquet exclusion list is invalid");
    }
    Ok(paths)
}

fn verify_ord_checkout(
    checkout: &Path,
    tree: &OrdGitLfsTreeV1,
    expected_protobufs: &BTreeSet<String>,
    excluded_parquet: &BTreeSet<String>,
) -> Result<()> {
    if tree.git_commit != ORD_DATA_COMMIT {
        bail!("ORD catalog commit is not the pinned data commit");
    }
    run_git_checked(checkout, &["fsck", "--strict", "--no-dangling"])?;
    let observed_commit = run_git_checked(checkout, &["rev-parse", "HEAD"])?;
    let observed_tree = run_git_checked(checkout, &["rev-parse", "HEAD^{tree}"])?;
    if observed_commit.trim() != ORD_DATA_COMMIT || observed_tree.trim() != ORD_DATA_COMMIT_TREE {
        bail!("ORD checkout commit or commit-tree identity is not pinned");
    }
    let tracked = run_git_checked(
        checkout,
        &["ls-tree", "-r", "--name-only", ORD_DATA_COMMIT, "data"],
    )?
    .lines()
    .filter(|line| !line.trim().is_empty())
    .map(str::to_owned)
    .collect::<BTreeSet<_>>();
    let expected = expected_protobufs
        .union(excluded_parquet)
        .cloned()
        .collect::<BTreeSet<_>>();
    if tracked != expected
        || expected_protobufs.len() as u64 != ORD_PROTOBUF_OBJECTS
        || excluded_parquet.len() != ORD_PARQUET_COMPANIONS
    {
        bail!("ORD tracked data tree is missing, extra, or differently classified");
    }
    let worktree_status = run_git_checked(
        checkout,
        &[
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            "data",
        ],
    )?;
    if !worktree_status.trim().is_empty() {
        bail!("ORD checkout data tree has untracked or modified paths");
    }
    Ok(())
}

fn run_git_checked(checkout: &Path, arguments: &[&str]) -> Result<String> {
    let output = Command::new("git")
        .arg("-C")
        .arg(checkout)
        .args(arguments)
        .output()
        .with_context(|| format!("running git {}", arguments.join(" ")))?;
    if !output.status.success() {
        bail!(
            "ORD Git verification failed: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        );
    }
    Ok(String::from_utf8(output.stdout)?)
}

fn locate_ord_source_object(source: &Path, object: &OrdGitLfsObjectV1) -> Result<PathBuf> {
    let path_candidate = safe_join(source, &object.path)?;
    if path_candidate.is_file() {
        return Ok(path_candidate);
    }
    let hash_candidate = safe_join(source, &object.raw_sha256)?;
    if hash_candidate.is_file() {
        return Ok(hash_candidate);
    }
    bail!("ORD mirror is missing catalog object {}", object.raw_sha256)
}

fn verify_installed_ord_tree(
    snapshot: &Path,
    unit: &AcquisitionUnitV2,
    receipt: &AcquisitionReceiptV2,
) -> Result<()> {
    let tree = unit
        .ord_git_lfs_tree
        .as_ref()
        .ok_or_else(|| anyhow!("ORD Git LFS object manifest is absent"))?;
    let manifest_path = safe_join(snapshot, &receipt.raw_object_path)?;
    let manifest: Value = read_json_typed(&manifest_path)?;
    if file_sha256(&manifest_path)? != receipt.sha256
        || manifest.get("git_commit").and_then(Value::as_str) != Some(tree.git_commit.as_str())
        || manifest.get("commit_tree").and_then(Value::as_str) != Some(ORD_DATA_COMMIT_TREE)
        || manifest
            .get("object_manifest_sha256")
            .and_then(Value::as_str)
            != Some(tree.object_manifest_sha256.as_str())
        || manifest
            .get("excluded_parquet_companion_count")
            .and_then(Value::as_u64)
            != Some(ORD_PARQUET_COMPANIONS as u64)
        || manifest
            .get("gzip_crc_eof_validated_objects")
            .and_then(Value::as_u64)
            != Some(ORD_PROTOBUF_OBJECTS)
        || manifest.get("objects") != Some(&serde_json::to_value(&tree.objects)?)
        || tree.object_count != ORD_PROTOBUF_OBJECTS
        || tree.total_bytes != ORD_TOTAL_PROTOBUF_BYTES
    {
        bail!("installed ORD object manifest is altered or partial");
    }
    let object_root = snapshot.join(if receipt.quarantined {
        "quarantine/raw/ord/objects"
    } else {
        "raw/ord/objects"
    });
    let installed = if object_root.is_dir() {
        let mut names = BTreeSet::new();
        for entry in fs::read_dir(&object_root)? {
            let entry = entry?;
            let metadata = fs::symlink_metadata(entry.path())?;
            if metadata.file_type().is_symlink() || !metadata.file_type().is_file() {
                bail!("installed ORD tree contains a symlink or non-regular object");
            }
            names.insert(entry.file_name().to_string_lossy().into_owned());
        }
        names
    } else {
        BTreeSet::new()
    };
    let expected = tree
        .objects
        .iter()
        .map(|object| object.raw_sha256.clone())
        .collect::<BTreeSet<_>>();
    if installed != expected {
        bail!("installed ORD content-addressed object set is partial or has unexpected files");
    }
    for object in &tree.objects {
        let path = object_root.join(&object.raw_sha256);
        if path.metadata()?.len() != object.bytes || file_sha256(&path)? != object.raw_sha256 {
            bail!("installed ORD object hash or size mismatch");
        }
        let compressed = fs::read(&path)?;
        let maximum_decompressed = object
            .bytes
            .saturating_mul(200)
            .clamp(16 * 1024 * 1024, 2 * 1024 * 1024 * 1024);
        decompress_gzip_bounded(&compressed, maximum_decompressed)
            .with_context(|| format!("revalidating gzip CRC/EOF for {}", object.path))?;
    }
    let complete_tree = snapshot.join("receipts/acquisition").join(format!(
        "{}.complete-tree.v1.json",
        safe_id(&unit.acquisition_unit_id)
    ));
    if !complete_tree.is_file() || file_sha256(&complete_tree)? != receipt.sha256 {
        bail!("ORD complete-tree sidecar is absent or altered");
    }
    Ok(())
}

fn cleanup_completed_download(snapshot: &Path, source: &Path) -> Result<()> {
    if source.starts_with(snapshot.join("staging")) && source.is_file() {
        fs::remove_file(source)?;
    }
    Ok(())
}

fn sign_acquisition_receipt(root: &Path, receipt: &mut AcquisitionReceiptV2) -> Result<()> {
    let identity = ensure_local_identity(root)?;
    let payload = canonical_bytes(&serde_json::to_value(&*receipt)?)?;
    let signature = identity.signing_key.sign(&payload);
    receipt.signature = Some(json!({
        "algorithm": "Ed25519",
        "key_id": identity.key_id,
        "authority": "LOCAL_ACQUISITION_AUDIT_ONLY",
        "source_genesis_hash": identity.genesis_hash,
        "public_key_hex": encode_hex(&identity.signing_key.verifying_key().to_bytes()),
        "signature_b64": BASE64_STANDARD.encode(signature.to_bytes()),
    }));
    Ok(())
}

fn verify_acquisition_receipt(receipt: &AcquisitionReceiptV2) -> Result<()> {
    let signature_value = receipt
        .signature
        .as_ref()
        .ok_or_else(|| anyhow!("acquisition receipt is unsigned"))?;
    if signature_value.get("algorithm").and_then(Value::as_str) != Some("Ed25519") {
        bail!("unsupported acquisition signature algorithm");
    }
    let key_id = signature_value
        .get("key_id")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("acquisition signature key ID is absent"))?;
    let public_hex = signature_value
        .get("public_key_hex")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("acquisition signature public key is absent"))?;
    let signature_b64 = signature_value
        .get("signature_b64")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("acquisition signature bytes are absent"))?;
    let public_bytes = decode_hex_32(public_hex)?;
    if key_id != format!("local-{}", &bytes_sha256(&public_bytes)[..16]) {
        bail!("acquisition signature key identity mismatch");
    }
    let verifying_key = VerifyingKey::from_bytes(&public_bytes)?;
    let signature = Signature::from_slice(&BASE64_STANDARD.decode(signature_b64)?)?;
    let unsigned = AcquisitionReceiptV2 {
        schema: receipt.schema.clone(),
        acquisition_unit_id: receipt.acquisition_unit_id.clone(),
        source_intent_id: receipt.source_intent_id.clone(),
        raw_object_path: receipt.raw_object_path.clone(),
        sha256: receipt.sha256.clone(),
        bytes: receipt.bytes,
        acquisition_method: receipt.acquisition_method.clone(),
        source_url: receipt.source_url.clone(),
        credential_ref: receipt.credential_ref.clone(),
        rights_decision_id: receipt.rights_decision_id.clone(),
        quarantined: receipt.quarantined,
        signature: None,
    };
    let payload = canonical_bytes(&serde_json::to_value(unsigned)?)?;
    verifying_key.verify(&payload, &signature)?;
    Ok(())
}

fn download_to_staging(snapshot: &Path, unit: &AcquisitionUnitV2) -> Result<PathBuf> {
    let url = unit
        .source_url
        .as_deref()
        .ok_or_else(|| anyhow!("acquisition has neither cache path nor source URL"))?;
    let staging = snapshot.join("staging");
    fs::create_dir_all(&staging)?;
    let output = staging.join(format!("{}.part", safe_id(&unit.acquisition_unit_id)));
    let status = Command::new("curl")
        .args(["--fail", "--location", "--retry", "3", "--continue-at", "-"])
        .arg("--output")
        .arg(&output)
        .arg(url)
        .status()
        .context("running resumable curl acquisition")?;
    if !status.success() {
        bail!("download failed for {}", unit.acquisition_unit_id);
    }
    Ok(output)
}

fn install_content_object(source: &Path, object: &Path, hash: &str, bytes: u64) -> Result<()> {
    if object.exists() {
        if object.metadata()?.len() == bytes && file_sha256(object)? == hash {
            break_hard_link_if_needed(source, object, hash, bytes)?;
            return Ok(());
        }
        bail!("content-addressed raw object conflicts with expected bytes");
    }
    fs::create_dir_all(object.parent().expect("raw object has parent"))?;
    fs::copy(source, object)?;
    if object.metadata()?.len() != bytes || file_sha256(object)? != hash {
        bail!("installed raw object failed post-copy verification");
    }
    Ok(())
}

#[cfg(unix)]
fn break_hard_link_if_needed(source: &Path, object: &Path, hash: &str, bytes: u64) -> Result<()> {
    use std::os::unix::fs::MetadataExt;
    if object.metadata()?.nlink() <= 1 {
        return Ok(());
    }
    let temporary = object.with_extension(format!("copy-{}", std::process::id()));
    if temporary.exists() {
        fs::remove_file(&temporary)?;
    }
    fs::copy(source, &temporary)?;
    if temporary.metadata()?.len() != bytes || file_sha256(&temporary)? != hash {
        fs::remove_file(&temporary)?;
        bail!("copied raw object failed hard-link separation verification");
    }
    fs::rename(temporary, object)?;
    Ok(())
}

#[cfg(not(unix))]
fn break_hard_link_if_needed(
    _source: &Path,
    _object: &Path,
    _hash: &str,
    _bytes: u64,
) -> Result<()> {
    Ok(())
}

fn normalize_unit(
    _root: &Path,
    snapshot: &Path,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
) -> Result<NormalizedDatasetManifestV2> {
    let receipt_path = acquisition_receipt_path(snapshot, &unit.acquisition_unit_id);
    let receipt: AcquisitionReceiptV2 = read_json_typed(&receipt_path)?;
    verify_acquisition_receipt(&receipt)?;
    if receipt.acquisition_unit_id != unit.acquisition_unit_id
        || receipt.rights_decision_id != decision.rights_decision_id
    {
        bail!("acquisition receipt identity mismatch");
    }
    let raw = snapshot.join(&receipt.raw_object_path);
    if file_sha256(&raw)? != receipt.sha256 || raw.metadata()?.len() != receipt.bytes {
        bail!("raw object no longer matches its signed receipt");
    }
    let dataset_id = format!("{}-{}", unit.acquisition_unit_id, &receipt.sha256[..16]);
    let base = if decision.rights_class.quarantined() {
        snapshot.join("quarantine")
    } else {
        snapshot.to_path_buf()
    };
    let normalized_path = base
        .join("normalized")
        .join(format!("{}.jsonl.gz", safe_id(&unit.acquisition_unit_id)));
    let rejection_path = base
        .join("rejections")
        .join(format!("{}.jsonl.gz", safe_id(&unit.acquisition_unit_id)));
    let identity_path = base.join("indexes").join(format!(
        "{}.canonical-identity.jsonl.gz",
        safe_id(&unit.acquisition_unit_id)
    ));
    let duplicate_path = base.join("indexes").join(format!(
        "{}.duplicate-groups.jsonl.gz",
        safe_id(&unit.acquisition_unit_id)
    ));
    let normalized_tmp = temporary_path(&normalized_path);
    let rejection_tmp = temporary_path(&rejection_path);
    prepare_temporary(&normalized_tmp)?;
    prepare_temporary(&rejection_tmp)?;
    let normalized_file = File::create(&normalized_tmp)?;
    let rejection_file = File::create(&rejection_tmp)?;
    let mut rows = deterministic_gzip(normalized_file);
    let mut rejects = deterministic_gzip(rejection_file);
    let mut state = NormalizeState {
        records: 0,
        rejections: 0,
        endpoint_counts: BTreeMap::new(),
        identities: BTreeMap::new(),
        duplicate_keys: BTreeMap::new(),
    };
    match unit.parser {
        ParserKind::OrdGitLfsTree => {
            verify_installed_ord_tree(snapshot, unit, &receipt)?;
            normalize_ord_git_lfs_tree(
                snapshot,
                unit,
                decision,
                &receipt,
                &dataset_id,
                &receipt.sha256,
                &mut rows,
                &mut rejects,
                &mut state,
            )?
        }
        ParserKind::MetadataOnly => normalize_metadata(
            unit,
            decision,
            &dataset_id,
            &receipt.sha256,
            receipt.bytes,
            &mut rows,
            &mut state,
        )?,
        ParserKind::NistCorrZip => normalize_nist_zip(
            &raw,
            unit,
            decision,
            &dataset_id,
            &receipt.sha256,
            &mut rows,
            &mut rejects,
            &mut state,
        )?,
        ParserKind::ZipCsvCorpus => normalize_zip_csv(
            &raw,
            unit,
            decision,
            &dataset_id,
            &receipt.sha256,
            &mut rows,
            &mut rejects,
            &mut state,
        )?,
        ParserKind::SecomZip => normalize_secom_zip(
            &raw,
            unit,
            decision,
            &dataset_id,
            &receipt.sha256,
            &mut rows,
            &mut state,
        )?,
        ParserKind::ProntoProcessZip => normalize_pronto_process_zip(
            &raw,
            unit,
            decision,
            &dataset_id,
            &receipt.sha256,
            &mut rows,
            &mut rejects,
            &mut state,
        )?,
        ParserKind::ChebiSdfGzip => normalize_chebi_sdf_gzip(
            &raw,
            unit,
            decision,
            &dataset_id,
            &receipt.sha256,
            &mut rows,
            &mut rejects,
            &mut state,
        )?,
        _ => {
            let file = File::open(&raw)?;
            normalize_csv(
                file,
                None,
                unit,
                decision,
                &dataset_id,
                &receipt.sha256,
                &mut rows,
                &mut rejects,
                &mut state,
            )?;
        }
    }
    rows.finish()?;
    rejects.finish()?;
    install_generated(&normalized_tmp, &normalized_path)?;
    install_generated(&rejection_tmp, &rejection_path)?;
    write_indexes(
        &identity_path,
        &duplicate_path,
        &unit.acquisition_unit_id,
        &state.identities,
        &state.duplicate_keys,
    )?;
    let manifest = NormalizedDatasetManifestV2 {
        schema: DATASET_SCHEMA.into(),
        dataset_id: dataset_id.clone(),
        acquisition_unit_id: unit.acquisition_unit_id.clone(),
        source_intent_id: unit.source_intent_id.clone(),
        raw_sha256: receipt.sha256,
        raw_bytes: receipt.bytes,
        normalized_path: relative(snapshot, &normalized_path),
        normalized_sha256: file_sha256(&normalized_path)?,
        rejection_path: relative(snapshot, &rejection_path),
        rejection_sha256: file_sha256(&rejection_path)?,
        identity_index_path: relative(snapshot, &identity_path),
        identity_index_sha256: file_sha256(&identity_path)?,
        duplicate_index_path: relative(snapshot, &duplicate_path),
        duplicate_index_sha256: file_sha256(&duplicate_path)?,
        record_count: state.records,
        rejection_count: state.rejections,
        endpoint_counts: state.endpoint_counts,
        evidence_class: unit.evidence_class.clone(),
        rights_class: decision.rights_class.clone(),
        quarantined: decision.rights_class.quarantined(),
        ordering: "archive_entry_then_source_row_number_ascending".into(),
        gzip_mtime: 0,
    };
    let manifest_path = dataset_manifest_path(snapshot, &unit.acquisition_unit_id);
    persist_immutable(
        &manifest_path,
        &canonical_bytes(&serde_json::to_value(&manifest)?)?,
    )?;
    let manifest_hash = file_sha256(&manifest_path)?;
    for consumer in &unit.consumers {
        if consumer.scoring
            && (!decision.promotion_eligible || forbidden_promotion_evidence(&unit.evidence_class))
        {
            bail!("forbidden evidence or rights class cannot enter a scoring consumer");
        }
        let lock = ModuleDatasetLockV2 {
            schema: LOCK_SCHEMA.into(),
            module_id: consumer.module_id.clone(),
            dataset_id: dataset_id.clone(),
            acquisition_unit_id: unit.acquisition_unit_id.clone(),
            dataset_manifest_path: relative(snapshot, &manifest_path),
            dataset_manifest_sha256: manifest_hash.clone(),
            normalized_artifact_sha256: manifest.normalized_sha256.clone(),
            consumer: consumer.consumer.clone(),
            scoring: consumer.scoring,
            authority_limit: consumer.authority_limit.clone(),
            rights_class: decision.rights_class.clone(),
            evidence_class: unit.evidence_class.clone(),
            network_access: false,
        };
        let path = lock_path(snapshot, &consumer.module_id, &dataset_id);
        persist_immutable(&path, &canonical_bytes(&serde_json::to_value(lock)?)?)?;
    }
    Ok(manifest)
}

fn normalize_ord_git_lfs_tree(
    snapshot: &Path,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    receipt: &AcquisitionReceiptV2,
    dataset_id: &str,
    manifest_sha256: &str,
    rows: &mut impl Write,
    rejects: &mut impl Write,
    state: &mut NormalizeState,
) -> Result<()> {
    let tree = unit
        .ord_git_lfs_tree
        .as_ref()
        .ok_or_else(|| anyhow!("ORD Git LFS object manifest is absent"))?;
    let object_root = snapshot.join(if receipt.quarantined {
        "quarantine/raw/ord/objects"
    } else {
        "raw/ord/objects"
    });
    for (object_index, object) in tree.objects.iter().enumerate() {
        let object_path = object_root.join(&object.raw_sha256);
        let compressed = fs::read(&object_path)
            .with_context(|| format!("reading installed ORD object {}", object.path))?;
        let maximum_decompressed = object
            .bytes
            .saturating_mul(200)
            .clamp(16 * 1024 * 1024, 2 * 1024 * 1024 * 1024);
        let decoded = match decode_gzip_dataset(&compressed, maximum_decompressed) {
            Ok(decoded) => decoded,
            Err(error) => {
                let exclusion = OrdExclusionV1 {
                    schema: ORD_EXCLUSION_SCHEMA.into(),
                    scope: OrdExclusionScopeV1::Dataset,
                    reason: dataset_exclusion_reason(&error),
                    source_object_path: object.path.clone(),
                    source_object_sha256: object.raw_sha256.clone(),
                    dataset_id: None,
                    reaction_id: None,
                    reaction_ordinal: None,
                    raw_reaction_message_sha256: None,
                    detail: format!("native ORD decode rejected the dataset: {error}"),
                };
                exclusion.validate()?;
                write_json_line(rejects, &exclusion)?;
                state.rejections += 1;
                continue;
            }
        };
        for classified in classify_dataset_reactions(&decoded) {
            match classified {
                Ok(candidate) => {
                    let row_number = state.records + 1;
                    let record_id = format!(
                        "{}:object:{:04}:reaction:{:012}",
                        unit.acquisition_unit_id, object_index, candidate.reaction_ordinal
                    );
                    let raw_row_sha256 = candidate.raw_reaction_message_sha256.clone();
                    write_json_line(
                        rows,
                        &NormalizedRecordV2 {
                            schema: "amphora.normalized-record.v2".into(),
                            dataset_id: dataset_id.into(),
                            record_id: record_id.clone(),
                            source_intent_id: unit.source_intent_id.clone(),
                            acquisition_unit_id: unit.acquisition_unit_id.clone(),
                            raw_file_sha256: object.raw_sha256.clone(),
                            raw_row_sha256: raw_row_sha256.clone(),
                            row_number,
                            archive_entry: Some(object.path.clone()),
                            evidence_class: unit.evidence_class.clone(),
                            rights_class: decision.rights_class.clone(),
                            endpoint: unit.endpoint.clone(),
                            value_number: None,
                            value_text: Some(candidate.mapped_reaction_identifier.clone()),
                            unit: None,
                            citation: unit.source_url.clone(),
                            // Authoritative chemical identity is assigned only after
                            // native RDKit canonicalization and map-removal agreement.
                            canonical_identity: None,
                            conditions: BTreeMap::from([
                                ("git_commit".into(), tree.git_commit.clone()),
                                (
                                    "normalization_state".into(),
                                    "ORD_STRUCTURALLY_DECODED_PENDING_RDKIT_VALIDATION".into(),
                                ),
                                (
                                    "object_manifest_sha256".into(),
                                    tree.object_manifest_sha256.clone(),
                                ),
                                ("snapshot_manifest_sha256".into(), manifest_sha256.into()),
                            ]),
                            raw_fields: BTreeMap::from([
                                ("source_object_path".into(), object.path.clone()),
                                ("source_object_sha256".into(), object.raw_sha256.clone()),
                                ("dataset_id".into(), candidate.dataset_id),
                                ("reaction_id".into(), candidate.reaction_id),
                                (
                                    "reaction_ordinal".into(),
                                    candidate.reaction_ordinal.to_string(),
                                ),
                                (
                                    "raw_reaction_message_sha256".into(),
                                    candidate.raw_reaction_message_sha256,
                                ),
                                (
                                    "mapped_reaction_identifier_kind".into(),
                                    candidate.mapped_reaction_identifier_kind,
                                ),
                                (
                                    "input_compounds_json".into(),
                                    serde_json::to_string(&candidate.input_compounds)?,
                                ),
                                (
                                    "product_compound_json".into(),
                                    serde_json::to_string(&candidate.product)?,
                                ),
                                (
                                    "ord_schema_version".into(),
                                    amphora_ord_codec::ORD_SCHEMA_VERSION.into(),
                                ),
                                (
                                    "ord_schema_source_commit".into(),
                                    amphora_ord_codec::ORD_SCHEMA_SOURCE_COMMIT.into(),
                                ),
                                ("ord_descriptor_set_sha256".into(), descriptor_set_sha256()),
                            ]),
                        },
                    )?;
                    state.records += 1;
                    *state
                        .endpoint_counts
                        .entry(unit.endpoint.clone())
                        .or_default() += 1;
                    state
                        .duplicate_keys
                        .entry(raw_row_sha256)
                        .or_default()
                        .push(record_id);
                }
                Err(excluded) => {
                    let exclusion = OrdExclusionV1 {
                        schema: ORD_EXCLUSION_SCHEMA.into(),
                        scope: OrdExclusionScopeV1::Reaction,
                        reason: reaction_exclusion_reason(excluded.reason),
                        source_object_path: object.path.clone(),
                        source_object_sha256: object.raw_sha256.clone(),
                        dataset_id: Some(excluded.dataset_id),
                        reaction_id: Some(excluded.reaction_id),
                        reaction_ordinal: Some(excluded.reaction_ordinal),
                        raw_reaction_message_sha256: Some(
                            excluded.raw_reaction_message_sha256,
                        ),
                        detail: "structured ORD reaction did not meet the locked authoritative extraction boundary".into(),
                    };
                    exclusion.validate()?;
                    write_json_line(rejects, &exclusion)?;
                    state.rejections += 1;
                }
            }
        }
    }
    Ok(())
}

fn dataset_exclusion_reason(error: &OrdCodecError) -> OrdExclusionReasonV1 {
    match error {
        OrdCodecError::ReactionScanMismatch => OrdExclusionReasonV1::RawReactionScanMismatch,
        OrdCodecError::MissingId => OrdExclusionReasonV1::MissingDatasetId,
        OrdCodecError::Protobuf(_)
        | OrdCodecError::WireFormat
        | OrdCodecError::DatasetReferencesOnly
        | OrdCodecError::DecompressionLimit
        | OrdCodecError::Gzip(_) => OrdExclusionReasonV1::ProtobufDecodeFailed,
    }
}

fn reaction_exclusion_reason(reason: StructuralExclusionReason) -> OrdExclusionReasonV1 {
    match reason {
        StructuralExclusionReason::MissingReactionId => OrdExclusionReasonV1::MissingReactionId,
        StructuralExclusionReason::MissingMappedReactionIdentifier => {
            OrdExclusionReasonV1::MissingMappedIdentifier
        }
        StructuralExclusionReason::AmbiguousMappedReactionIdentifier => {
            OrdExclusionReasonV1::AmbiguousMappedIdentifier
        }
        StructuralExclusionReason::CrudeInputUnsupported
        | StructuralExclusionReason::MissingInputStructure
        | StructuralExclusionReason::MultiComponentInput => {
            OrdExclusionReasonV1::UnsupportedReactant
        }
        StructuralExclusionReason::MissingProductStructure
        | StructuralExclusionReason::MultiComponentProduct => {
            OrdExclusionReasonV1::UnsupportedProduct
        }
        StructuralExclusionReason::AmbiguousProductOutcome => {
            OrdExclusionReasonV1::AmbiguousProductOutcome
        }
    }
}

fn normalize_secom_zip(
    raw: &Path,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    dataset_id: &str,
    raw_hash: &str,
    rows: &mut impl Write,
    state: &mut NormalizeState,
) -> Result<()> {
    let mut archive = ZipArchive::new(File::open(raw)?)?;
    let data = read_zip_text_suffix(&mut archive, "secom.data")?;
    let labels = read_zip_text_suffix(&mut archive, "secom_labels.data")?;
    let data_rows = data.lines().collect::<Vec<_>>();
    let label_rows = labels.lines().collect::<Vec<_>>();
    if data_rows.len() != 1_567 || label_rows.len() != data_rows.len() {
        bail!("SECOM archive must contain exactly 1,567 aligned data and label rows");
    }
    for (index, (features, label_row)) in data_rows.iter().zip(label_rows).enumerate() {
        let mut label_parts = label_row.splitn(2, char::is_whitespace);
        let label_text = label_parts.next().unwrap_or_default().trim();
        let timestamp = label_parts
            .next()
            .unwrap_or_default()
            .trim()
            .trim_matches('"');
        let label = label_text
            .parse::<f64>()
            .ok()
            .filter(|value| matches!(*value, -1.0 | 1.0))
            .ok_or_else(|| anyhow!("SECOM label row {} is malformed", index + 1))?;
        if timestamp.is_empty() {
            bail!("SECOM timestamp row {} is absent", index + 1);
        }
        let feature_values = features.split_whitespace().collect::<Vec<_>>();
        if feature_values.len() != 590 {
            bail!(
                "SECOM row {} has {} features rather than 590",
                index + 1,
                feature_values.len()
            );
        }
        let missing_count = feature_values
            .iter()
            .filter(|value| value.eq_ignore_ascii_case("nan"))
            .count();
        let row_number = index as u64 + 1;
        let record_id = format!("{}:row:{row_number:012}", unit.acquisition_unit_id);
        let row_hash = bytes_sha256(format!("{features}\n{label_row}").as_bytes());
        write_json_line(
            rows,
            &NormalizedRecordV2 {
                schema: "amphora.normalized-record.v2".into(),
                dataset_id: dataset_id.into(),
                record_id: record_id.clone(),
                source_intent_id: unit.source_intent_id.clone(),
                acquisition_unit_id: unit.acquisition_unit_id.clone(),
                raw_file_sha256: raw_hash.into(),
                raw_row_sha256: row_hash.clone(),
                row_number,
                archive_entry: Some("secom.data+secom_labels.data".into()),
                evidence_class: unit.evidence_class.clone(),
                rights_class: decision.rights_class.clone(),
                endpoint: unit.endpoint.clone(),
                value_number: Some(label),
                value_text: Some(if label > 0.0 { "FAIL" } else { "PASS" }.into()),
                unit: Some("binary_yield_label".into()),
                citation: unit.source_url.clone(),
                canonical_identity: Some(timestamp.into()),
                conditions: BTreeMap::from([
                    ("timestamp".into(), timestamp.into()),
                    ("feature_count".into(), feature_values.len().to_string()),
                    ("missing_feature_count".into(), missing_count.to_string()),
                ]),
                raw_fields: BTreeMap::from([
                    ("label".into(), label_text.into()),
                    ("timestamp".into(), timestamp.into()),
                    ("sensor_values".into(), (*features).into()),
                ]),
            },
        )?;
        state.records += 1;
        *state
            .endpoint_counts
            .entry(unit.endpoint.clone())
            .or_default() += 1;
        state
            .identities
            .entry(timestamp.into())
            .or_default()
            .push(record_id.clone());
        state
            .duplicate_keys
            .entry(row_hash)
            .or_default()
            .push(record_id);
    }
    Ok(())
}

fn read_zip_text_suffix(archive: &mut ZipArchive<File>, suffix: &str) -> Result<String> {
    let names = (0..archive.len())
        .filter_map(|index| {
            archive
                .by_index(index)
                .ok()
                .map(|entry| entry.name().to_owned())
        })
        .filter(|name| name.ends_with(suffix))
        .collect::<Vec<_>>();
    if names.len() != 1 {
        bail!("archive must contain exactly one {suffix} entry");
    }
    let mut text = String::new();
    archive.by_name(&names[0])?.read_to_string(&mut text)?;
    Ok(text)
}

#[allow(clippy::too_many_arguments)]
fn normalize_pronto_process_zip(
    raw: &Path,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    dataset_id: &str,
    raw_hash: &str,
    rows: &mut impl Write,
    rejects: &mut impl Write,
    state: &mut NormalizeState,
) -> Result<()> {
    let mut archive = ZipArchive::new(File::open(raw)?)?;
    let mut names = (0..archive.len())
        .filter_map(|index| archive.name_for_index(index).map(str::to_owned))
        .filter(|name| {
            name.contains("/Process Data/") && name.to_ascii_lowercase().ends_with(".csv")
        })
        .collect::<Vec<_>>();
    names.sort();
    if names.len() != 10 {
        bail!("PRONTO archive must contain exactly ten process-data CSV streams");
    }
    for name in names {
        let entry = archive.by_name(&name)?;
        let mut csv = ReaderBuilder::new()
            .has_headers(false)
            .flexible(true)
            .from_reader(entry);
        let records = csv.records();
        let mut previous_timestamp: Option<(&str, String)> = None;
        let mut time_segment = 1_u64;
        let mut sensor_count = None;
        for (index, result) in records.enumerate() {
            let source_row = index as u64 + 1;
            let record = match result {
                Ok(record) => record,
                Err(error) => {
                    write_rejection(
                        rejects,
                        state,
                        unit,
                        raw_hash,
                        source_row,
                        Some(&name),
                        error.to_string(),
                    )?;
                    continue;
                }
            };
            if source_row <= 3 {
                if source_row == 3 {
                    sensor_count = Some(record.len().saturating_sub(1));
                }
                continue;
            }
            let timestamp_text = record
                .get(0)
                .unwrap_or_default()
                .trim_start_matches('\u{feff}')
                .trim();
            let (timestamp_encoding, timestamp_order) = if let Some(number) = timestamp_text
                .parse::<f64>()
                .ok()
                .filter(|value| value.is_finite())
            {
                ("EXCEL_SERIAL", format!("{number:020.10}"))
            } else if valid_pronto_datetime(timestamp_text) {
                ("DATE_MINUTE", timestamp_text.to_owned())
            } else {
                write_rejection(
                    rejects,
                    state,
                    unit,
                    raw_hash,
                    source_row,
                    Some(&name),
                    "missing or malformed process timestamp".into(),
                )?;
                continue;
            };
            if let Some((previous_encoding, previous_order)) = previous_timestamp.as_ref() {
                if *previous_encoding == timestamp_encoding && timestamp_order < *previous_order {
                    bail!("PRONTO process timestamp decreases within an encoding segment: {name}");
                }
                if *previous_encoding != timestamp_encoding {
                    time_segment += 1;
                }
            }
            previous_timestamp = Some((timestamp_encoding, timestamp_order));
            let expected_sensors = sensor_count.unwrap_or_else(|| record.len().saturating_sub(1));
            let values = record.iter().skip(1).collect::<Vec<_>>();
            let missing = values
                .iter()
                .filter(|value| {
                    let value = value.trim();
                    value.is_empty()
                        || value
                            .parse::<f64>()
                            .ok()
                            .filter(|number| number.is_finite())
                            .is_none()
                })
                .count();
            let present = values.len().saturating_sub(missing);
            let missing_fraction = if expected_sensors == 0 {
                1.0
            } else {
                missing as f64 / expected_sensors as f64
            };
            let raw_values_hash = bytes_sha256(record.as_slice().as_bytes());
            let row_number = state.records + 1;
            let record_id = format!("{}:row:{row_number:012}", unit.acquisition_unit_id);
            let condition = name
                .split('/')
                .find(|part| {
                    part.starts_with('C') && part.chars().nth(1).is_some_and(|c| c.is_ascii_digit())
                })
                .unwrap_or("UNKNOWN");
            write_json_line(
                rows,
                &NormalizedRecordV2 {
                    schema: "amphora.normalized-record.v2".into(),
                    dataset_id: dataset_id.into(),
                    record_id: record_id.clone(),
                    source_intent_id: unit.source_intent_id.clone(),
                    acquisition_unit_id: unit.acquisition_unit_id.clone(),
                    raw_file_sha256: raw_hash.into(),
                    raw_row_sha256: raw_values_hash.clone(),
                    row_number,
                    archive_entry: Some(name.clone()),
                    evidence_class: unit.evidence_class.clone(),
                    rights_class: decision.rights_class.clone(),
                    endpoint: unit.endpoint.clone(),
                    value_number: Some(missing_fraction),
                    value_text: Some(format!("{missing}/{expected_sensors}")),
                    unit: Some("missing_sensor_fraction".into()),
                    citation: unit.source_url.clone(),
                    canonical_identity: Some(format!("{name}|{timestamp_text}|{source_row}")),
                    conditions: BTreeMap::from([
                        ("condition_family".into(), condition.into()),
                        ("source_timestamp".into(), timestamp_text.into()),
                        ("timestamp_encoding".into(), timestamp_encoding.into()),
                        ("time_segment".into(), time_segment.to_string()),
                        ("source_row_number".into(), source_row.to_string()),
                        ("sensor_count".into(), expected_sensors.to_string()),
                        ("present_sensor_count".into(), present.to_string()),
                        ("missing_sensor_count".into(), missing.to_string()),
                    ]),
                    raw_fields: BTreeMap::from([
                        ("archive_entry".into(), name.clone()),
                        ("source_timestamp".into(), timestamp_text.into()),
                        ("timestamp_encoding".into(), timestamp_encoding.into()),
                        ("time_segment".into(), time_segment.to_string()),
                        ("sensor_values_sha256".into(), raw_values_hash.clone()),
                    ]),
                },
            )?;
            state.records += 1;
            *state
                .endpoint_counts
                .entry(unit.endpoint.clone())
                .or_default() += 1;
            state
                .identities
                .entry(format!("{name}|{timestamp_text}|{source_row}"))
                .or_default()
                .push(record_id.clone());
            state
                .duplicate_keys
                .entry(raw_values_hash)
                .or_default()
                .push(record_id);
        }
    }
    if state.records == 0 {
        bail!("PRONTO process-data subset contains no valid time-ordered rows");
    }
    Ok(())
}

fn valid_pronto_datetime(value: &str) -> bool {
    let Some((date, time)) = value.split_once(char::is_whitespace) else {
        return false;
    };
    date.split('/').count() == 3
        && date.split('/').all(|part| part.parse::<u16>().is_ok())
        && time.split(':').count() >= 2
        && time.split(':').all(|part| part.parse::<u16>().is_ok())
}

#[allow(clippy::too_many_arguments)]
fn normalize_chebi_sdf_gzip(
    raw: &Path,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    dataset_id: &str,
    raw_hash: &str,
    rows: &mut impl Write,
    rejects: &mut impl Write,
    state: &mut NormalizeState,
) -> Result<()> {
    let decoder = GzDecoder::new(File::open(raw)?);
    let reader = BufReader::new(decoder);
    let mut block = Vec::new();
    let mut source_record = 0_u64;
    for line in reader.lines() {
        let line = line?;
        if line == "$$$$" {
            source_record += 1;
            normalize_chebi_block(
                &block,
                source_record,
                unit,
                decision,
                dataset_id,
                raw_hash,
                rows,
                rejects,
                state,
            )?;
            block.clear();
        } else {
            block.push(line);
        }
    }
    if !block.iter().all(|line| line.trim().is_empty()) {
        bail!("ChEBI SDF terminates without a record delimiter");
    }
    if state.records < 300 || state.identities.len() < 300 {
        bail!("ChEBI normalization requires at least 300 deduplicated structures");
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn normalize_chebi_block(
    block: &[String],
    source_record: u64,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    dataset_id: &str,
    raw_hash: &str,
    rows: &mut impl Write,
    rejects: &mut impl Write,
    state: &mut NormalizeState,
) -> Result<()> {
    let mut properties = BTreeMap::new();
    let mut index = 0;
    while index < block.len() {
        let line = block[index].trim();
        if let Some(name) = line
            .strip_prefix("> <")
            .and_then(|value| value.strip_suffix('>'))
        {
            index += 1;
            let mut values = Vec::new();
            while index < block.len() && !block[index].trim().is_empty() {
                values.push(block[index].trim().to_owned());
                index += 1;
            }
            properties
                .entry(name.to_owned())
                .or_insert_with(|| values.join(";"));
        }
        index += 1;
    }
    let required = |name: &str| {
        properties
            .get(name)
            .map(String::as_str)
            .filter(|value| !value.is_empty())
    };
    let chebi_id = required("ChEBI ID");
    let formula = required("FORMULA");
    let smiles = required("SMILES");
    let inchi = required("INCHI");
    let inchikey = required("INCHIKEY");
    let mass = required("MASS")
        .and_then(|value| value.parse::<f64>().ok())
        .filter(|value| value.is_finite() && *value > 0.0);
    if chebi_id.is_none()
        || formula.is_none()
        || mass.is_none()
        || (inchikey.is_none() && smiles.is_none() && inchi.is_none())
    {
        return write_rejection(
            rejects,
            state,
            unit,
            raw_hash,
            source_record,
            Some("chebi_3_stars.sdf"),
            "missing required identity, formula, or finite positive mass".into(),
        );
    }
    let chebi_id = chebi_id.expect("checked");
    let identity = inchikey
        .or(inchi)
        .or(smiles)
        .expect("checked")
        .to_ascii_lowercase();
    let smiles_value = smiles.unwrap_or_default();
    let raw_row_sha256 = bytes_sha256(block.join("\n").as_bytes());
    let record_id = format!("{}:{chebi_id}", unit.acquisition_unit_id);
    write_json_line(
        rows,
        &NormalizedRecordV2 {
            schema: "amphora.normalized-record.v2".into(),
            dataset_id: dataset_id.into(),
            record_id: record_id.clone(),
            source_intent_id: unit.source_intent_id.clone(),
            acquisition_unit_id: unit.acquisition_unit_id.clone(),
            raw_file_sha256: raw_hash.into(),
            raw_row_sha256: raw_row_sha256.clone(),
            row_number: source_record,
            archive_entry: Some("chebi_3_stars.sdf".into()),
            evidence_class: unit.evidence_class.clone(),
            rights_class: decision.rights_class.clone(),
            endpoint: unit.endpoint.clone(),
            value_number: mass,
            value_text: properties.get("ChEBI NAME").cloned(),
            unit: Some("Da".into()),
            citation: unit.source_url.clone(),
            canonical_identity: Some(identity.clone()),
            conditions: BTreeMap::from([
                ("formula".into(), formula.expect("checked").into()),
                (
                    "stereochemistry_declared".into(),
                    (smiles_value.contains('@') || inchi.is_some_and(|value| value.contains("/t")))
                        .to_string(),
                ),
                (
                    "fragmented_structure".into(),
                    smiles_value.contains('.').to_string(),
                ),
                (
                    "star_rating".into(),
                    properties.get("STAR").cloned().unwrap_or_default(),
                ),
            ]),
            raw_fields: properties,
        },
    )?;
    state.records += 1;
    *state
        .endpoint_counts
        .entry(unit.endpoint.clone())
        .or_default() += 1;
    state
        .identities
        .entry(identity)
        .or_default()
        .push(record_id.clone());
    state
        .duplicate_keys
        .entry(raw_row_sha256)
        .or_default()
        .push(record_id);
    Ok(())
}

fn normalize_metadata(
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    dataset_id: &str,
    raw_hash: &str,
    raw_bytes: u64,
    rows: &mut impl Write,
    state: &mut NormalizeState,
) -> Result<()> {
    let record_id = format!("{}:raw:{:012}", unit.acquisition_unit_id, 1);
    let endpoint = unit.endpoint.clone();
    write_json_line(
        rows,
        &NormalizedRecordV2 {
            schema: "amphora.normalized-record.v2".into(),
            dataset_id: dataset_id.into(),
            record_id,
            source_intent_id: unit.source_intent_id.clone(),
            acquisition_unit_id: unit.acquisition_unit_id.clone(),
            raw_file_sha256: raw_hash.into(),
            raw_row_sha256: raw_hash.into(),
            row_number: 1,
            archive_entry: None,
            evidence_class: unit.evidence_class.clone(),
            rights_class: decision.rights_class.clone(),
            endpoint: endpoint.clone(),
            value_number: Some(raw_bytes as f64),
            value_text: Some(raw_hash.into()),
            unit: Some("bytes_and_sha256".into()),
            citation: unit.source_url.clone(),
            canonical_identity: Some(unit.acquisition_unit_id.clone()),
            conditions: BTreeMap::new(),
            raw_fields: BTreeMap::from([
                ("filename".into(), unit.filename.clone()),
                ("sha256".into(), raw_hash.into()),
                ("bytes".into(), raw_bytes.to_string()),
            ]),
        },
    )?;
    state.records = 1;
    state.endpoint_counts.insert(endpoint, 1);
    state.identities.insert(
        unit.acquisition_unit_id.clone(),
        vec![format!("{}:raw:{:012}", unit.acquisition_unit_id, 1)],
    );
    state.duplicate_keys.insert(
        raw_hash.into(),
        vec![format!("{}:raw:{:012}", unit.acquisition_unit_id, 1)],
    );
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn normalize_csv<R: Read>(
    reader: R,
    archive_entry: Option<&str>,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    dataset_id: &str,
    raw_hash: &str,
    rows: &mut impl Write,
    rejects: &mut impl Write,
    state: &mut NormalizeState,
) -> Result<()> {
    let mut csv = ReaderBuilder::new().flexible(true).from_reader(reader);
    let headers = csv
        .headers()
        .context("reading CSV headers")?
        .iter()
        .map(clean_header)
        .collect::<Vec<_>>();
    for (index, result) in csv.records().enumerate() {
        let row_number = index as u64 + 2;
        let record = match result {
            Ok(record) => record,
            Err(error) => {
                write_rejection(
                    rejects,
                    state,
                    unit,
                    raw_hash,
                    row_number,
                    archive_entry,
                    error.to_string(),
                )?;
                continue;
            }
        };
        if record.len() != headers.len() {
            write_rejection(
                rejects,
                state,
                unit,
                raw_hash,
                row_number,
                archive_entry,
                format!(
                    "column count mismatch: expected {}, observed {}",
                    headers.len(),
                    record.len()
                ),
            )?;
            continue;
        }
        let raw_fields = field_map(&headers, &record);
        let parsed = parsed_fields(unit, &raw_fields);
        let raw_row_sha256 = hash_json(&record.iter().collect::<Vec<_>>())?;
        let record_id = format!(
            "{}:{}:{:012}",
            unit.acquisition_unit_id,
            archive_entry.unwrap_or("raw"),
            row_number
        );
        let normalized = NormalizedRecordV2 {
            schema: "amphora.normalized-record.v2".into(),
            dataset_id: dataset_id.into(),
            record_id: record_id.clone(),
            source_intent_id: unit.source_intent_id.clone(),
            acquisition_unit_id: unit.acquisition_unit_id.clone(),
            raw_file_sha256: raw_hash.into(),
            raw_row_sha256,
            row_number,
            archive_entry: archive_entry.map(str::to_owned),
            evidence_class: unit.evidence_class.clone(),
            rights_class: decision.rights_class.clone(),
            endpoint: parsed.endpoint.clone(),
            value_number: parsed.value_number,
            value_text: parsed.value_text,
            unit: parsed.unit,
            citation: parsed.citation,
            canonical_identity: parsed.identity.clone(),
            conditions: parsed.conditions,
            raw_fields,
        };
        write_json_line(rows, &normalized)?;
        state
            .duplicate_keys
            .entry(normalized.raw_row_sha256.clone())
            .or_default()
            .push(normalized.record_id.clone());
        state.records += 1;
        *state.endpoint_counts.entry(parsed.endpoint).or_default() += 1;
        if let Some(identity) = parsed.identity {
            state
                .identities
                .entry(identity)
                .or_default()
                .push(record_id);
        }
    }
    Ok(())
}

fn parsed_fields(unit: &AcquisitionUnitV2, fields: &BTreeMap<String, String>) -> ParsedFields {
    let mut endpoint = unit.endpoint.clone();
    let mut unit_name = unit.unit.clone();
    let mut conditions = selected_fields(fields, &unit.condition_columns);
    let mut value_text = unit
        .value_column
        .as_ref()
        .and_then(|column| nonempty(fields.get(column)));
    let mut value_number = value_text.as_deref().and_then(parse_number);
    let mut citation = unit
        .citation_column
        .as_ref()
        .and_then(|column| nonempty(fields.get(column)));
    let mut identity = canonical_identity(fields, &unit.identity_columns);
    match unit.parser {
        ParserKind::BigsoldbSolubility => {
            endpoint = "solubility_log_s".into();
            value_text = nonempty(fields.get("LogS(mol/L)"));
            value_number = value_text.as_deref().and_then(parse_number);
            unit_name = Some("log10(mol/L)".into());
            conditions = selected_fields(fields, &["Temperature_K".into(), "Solvent".into()]);
            conditions.insert(
                "solubility_mole_fraction".into(),
                fields
                    .get("Solubility(mole_fraction)")
                    .cloned()
                    .unwrap_or_default(),
            );
            conditions.insert(
                "solubility_mol_l".into(),
                fields.get("Solubility(mol/L)").cloned().unwrap_or_default(),
            );
            citation = nonempty(fields.get("Source"));
            identity = nonempty(fields.get("Solvent")).map(|value| value.to_ascii_lowercase());
        }
        ParserKind::BigsoldbDensity => {
            endpoint = "solvent_density".into();
            value_text = nonempty(fields.get("Density_g/cm^3"));
            value_number = value_text.as_deref().and_then(parse_number);
            unit_name = Some("g/cm^3".into());
            conditions = selected_fields(fields, &["Temperature_K".into()]);
            citation = nonempty(fields.get("Source"));
        }
        ParserKind::NistCorrZip => {
            endpoint = "corrosion_rate_or_rating".into();
            value_text = nonempty(fields.get("Rate (mm/yr) or Rating"));
            value_number = value_text.as_deref().and_then(parse_number);
            unit_name = Some("mm/year_or_rating".into());
            conditions = selected_fields(
                fields,
                &[
                    "Environment".into(),
                    "Localized Attack".into(),
                    "Condition/Comment".into(),
                    "Concentration (Vol %)".into(),
                    "Temperature (deg C)".into(),
                    "Duration".into(),
                ],
            );
            if let Some(raw) = &value_text {
                let (rating, qualifier) = corrosion_rating(raw);
                if let Some(rating) = rating {
                    conditions.insert("categorical_rating".into(), rating);
                }
                if let Some(qualifier) = qualifier {
                    conditions.insert("rate_qualifier".into(), qualifier);
                }
            }
            citation = nonempty(fields.get("Reference"));
        }
        ParserKind::SplitCsv => {
            conditions.insert("benchmark_split_only".into(), "true".into());
        }
        _ => {}
    }
    ParsedFields {
        endpoint,
        value_number,
        value_text,
        unit: unit_name,
        conditions,
        citation,
        identity,
    }
}

#[allow(clippy::too_many_arguments)]
fn normalize_nist_zip(
    raw: &Path,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    dataset_id: &str,
    raw_hash: &str,
    rows: &mut impl Write,
    rejects: &mut impl Write,
    state: &mut NormalizeState,
) -> Result<()> {
    let file = File::open(raw)?;
    let mut zip = ZipArchive::new(file)?;
    let mut entry = zip
        .by_name("CORR-DATA_Database.csv")
        .context("CORR-DATA archive lacks its database CSV")?;
    normalize_csv(
        &mut entry,
        Some("CORR-DATA_Database.csv"),
        unit,
        decision,
        dataset_id,
        raw_hash,
        rows,
        rejects,
        state,
    )
}

#[allow(clippy::too_many_arguments)]
fn normalize_zip_csv(
    raw: &Path,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    dataset_id: &str,
    raw_hash: &str,
    rows: &mut impl Write,
    rejects: &mut impl Write,
    state: &mut NormalizeState,
) -> Result<()> {
    let file = File::open(raw)?;
    let mut zip = ZipArchive::new(file)?;
    let mut names = (0..zip.len())
        .filter_map(|index| zip.name_for_index(index).map(str::to_owned))
        .filter(|name| name.to_ascii_lowercase().ends_with(".csv"))
        .collect::<Vec<_>>();
    names.sort();
    if names.is_empty() {
        bail!("ZIP corpus contains no CSV files");
    }
    for name in names {
        let mut entry = zip.by_name(&name)?;
        normalize_csv(
            &mut entry,
            Some(&name),
            unit,
            decision,
            dataset_id,
            raw_hash,
            rows,
            rejects,
            state,
        )?;
    }
    Ok(())
}

fn write_rejection(
    writer: &mut impl Write,
    state: &mut NormalizeState,
    unit: &AcquisitionUnitV2,
    raw_hash: &str,
    row_number: u64,
    archive_entry: Option<&str>,
    reason: String,
) -> Result<()> {
    write_json_line(
        writer,
        &RejectionRecordV2 {
            schema: "amphora.normalization-rejection.v2",
            acquisition_unit_id: unit.acquisition_unit_id.clone(),
            raw_file_sha256: raw_hash.into(),
            row_number,
            archive_entry: archive_entry.map(str::to_owned),
            reason,
        },
    )?;
    state.rejections += 1;
    Ok(())
}

fn write_indexes(
    identity_path: &Path,
    duplicate_path: &Path,
    unit_id: &str,
    identities: &BTreeMap<String, Vec<String>>,
    duplicate_keys: &BTreeMap<String, Vec<String>>,
) -> Result<()> {
    let identity_tmp = temporary_path(identity_path);
    let duplicate_tmp = temporary_path(duplicate_path);
    prepare_temporary(&identity_tmp)?;
    prepare_temporary(&duplicate_tmp)?;
    let mut identity_writer = deterministic_gzip(File::create(&identity_tmp)?);
    let mut duplicate_writer = deterministic_gzip(File::create(&duplicate_tmp)?);
    for (identity, records) in identities {
        write_json_line(
            &mut identity_writer,
            &json!({
                "schema": "amphora.canonical-identity-index-row.v2",
                "acquisition_unit_id": unit_id,
                "canonical_identity": identity,
                "record_ids": records,
            }),
        )?;
    }
    for (raw_row_sha256, records) in duplicate_keys {
        if records.len() > 1 {
            write_json_line(
                &mut duplicate_writer,
                &json!({
                    "schema": "amphora.duplicate-group-index-row.v2",
                    "acquisition_unit_id": unit_id,
                    "raw_row_sha256": raw_row_sha256,
                    "record_ids": records,
                    "observation_count": records.len(),
                    "rows_discarded": 0,
                }),
            )?;
        }
    }
    identity_writer.finish()?;
    duplicate_writer.finish()?;
    install_generated(&identity_tmp, identity_path)?;
    install_generated(&duplicate_tmp, duplicate_path)
}

fn consumer_report(
    snapshot: &Path,
    lock: &ModuleDatasetLockV2,
    manifest: &NormalizedDatasetManifestV2,
) -> Result<Value> {
    let path = snapshot.join(&manifest.normalized_path);
    let decoder = GzDecoder::new(File::open(path)?);
    let reader = BufReader::new(decoder);
    let mut rows = 0_u64;
    let mut numeric_values = 0_u64;
    let mut identities = BTreeSet::new();
    let mut endpoints = BTreeMap::<String, u64>::new();
    let mut nonempty_source_field_counts = BTreeMap::<String, u64>::new();
    for line in std::io::BufRead::lines(reader) {
        let line = line?;
        if line.is_empty() {
            continue;
        }
        let row: NormalizedRecordV2 = serde_json::from_str(&line)?;
        if row.dataset_id != manifest.dataset_id
            || row.acquisition_unit_id != manifest.acquisition_unit_id
        {
            bail!("normalized row lineage does not match module source lock");
        }
        rows += 1;
        numeric_values += u64::from(row.value_number.is_some());
        if let Some(identity) = row.canonical_identity {
            identities.insert(identity);
        }
        *endpoints.entry(row.endpoint).or_default() += 1;
        for (field, value) in row.raw_fields {
            if !value.trim().is_empty() {
                *nonempty_source_field_counts.entry(field).or_default() += 1;
            }
        }
    }
    if rows != manifest.record_count || endpoints != manifest.endpoint_counts {
        bail!("consumer row/endpoint reconciliation failed");
    }
    Ok(json!({
        "schema": "amphora.executable-dataset-consumer-report.v2",
        "module_id": lock.module_id,
        "dataset_id": lock.dataset_id,
        "consumer": lock.consumer,
        "scoring": lock.scoring,
        "network_access": false,
        "normalized_sha256": lock.normalized_artifact_sha256,
        "rows_consumed": rows,
        "numeric_value_count": numeric_values,
        "canonical_identity_count": identities.len(),
        "endpoint_counts": endpoints,
        "nonempty_source_field_counts": nonempty_source_field_counts,
        "mixed_endpoint_aggregate_error_computed": false,
        "authority_limit": lock.authority_limit,
    }))
}

fn audit_identity_overlap(
    identity_index: &Path,
    unit_id: &str,
    first_unit: &mut HashMap<String, String>,
    overlap_pairs: &mut BTreeMap<String, u64>,
) -> Result<()> {
    let decoder = GzDecoder::new(File::open(identity_index)?);
    let reader = BufReader::new(decoder);
    for line in std::io::BufRead::lines(reader) {
        let line = line?;
        if line.is_empty() {
            continue;
        }
        let row: Value = serde_json::from_str(&line)?;
        let identity = row
            .get("canonical_identity")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("canonical identity index row has no identity"))?;
        record_identity_overlap(identity, unit_id, first_unit, overlap_pairs);
    }
    Ok(())
}

fn record_identity_overlap(
    identity: &str,
    unit_id: &str,
    first_unit: &mut HashMap<String, String>,
    overlap_pairs: &mut BTreeMap<String, u64>,
) {
    let Some(previous) = first_unit.get(identity) else {
        first_unit.insert(identity.into(), unit_id.into());
        return;
    };
    if previous == unit_id {
        return;
    }
    let pair = if previous.as_str() < unit_id {
        format!("{previous}<->{unit_id}")
    } else {
        format!("{unit_id}<->{previous}")
    };
    *overlap_pairs.entry(pair).or_default() += 1;
}

fn validate_catalog(root: &Path, _snapshot: &Path, catalog: &DataCatalogV2) -> Result<()> {
    if catalog.schema != "amphora.data-catalog.v2" {
        bail!("invalid v2 data catalog identity");
    }
    let channel = snapshot_channel(&catalog.snapshot_id)?;
    if channel == "feedback-v2" {
        if catalog.parent_snapshot.is_some() || catalog.source_intents.len() != 15 {
            bail!("frozen v2 catalog must contain exactly 15 root source intents");
        }
    } else {
        let (expected_parent_channel, expected_parent_path) = match channel {
            "feedback-v3" => ("feedback-v2", "feedback/v2/catalog.json"),
            "feedback-v4" => ("feedback-v3", "feedback/v3/catalog.json"),
            _ => unreachable!("snapshot channel validated"),
        };
        let parent = catalog
            .parent_snapshot
            .as_ref()
            .ok_or_else(|| anyhow!("{channel} must bind its frozen parent snapshot"))?;
        if snapshot_channel(&parent.snapshot_id)? != expected_parent_channel
            || parent.catalog_path != expected_parent_path
            || !parent.immutable
        {
            bail!("{channel} parent snapshot binding is invalid");
        }
        let parent_path = root.join(&parent.catalog_path);
        let parent_catalog: DataCatalogV2 = read_json_typed(&parent_path)?;
        if file_sha256(&parent_path)? != parent.catalog_sha256
            || parent_catalog.snapshot_id != parent.snapshot_id
        {
            bail!("{channel} parent catalog hash is stale or forked");
        }
        validate_catalog(
            root,
            parent_path
                .parent()
                .ok_or_else(|| anyhow!("parent catalog has no snapshot directory"))?,
            &parent_catalog,
        )?;
        if catalog.source_intents.is_empty() {
            bail!("{channel} must contain at least one new source intent");
        }
    }
    let mut source_ids = BTreeSet::new();
    for source in &catalog.source_intents {
        if source.schema != SOURCE_SCHEMA || !source_ids.insert(source.source_intent_id.as_str()) {
            bail!(
                "invalid or duplicate source intent: {}",
                source.source_intent_id
            );
        }
    }
    if channel == "feedback-v2" {
        let required_ids = REQUIRED_SOURCE_INTENTS.into_iter().collect::<BTreeSet<_>>();
        if source_ids != required_ids {
            bail!("v2 catalog source intents do not exactly match the 15-item source list");
        }
        let bigsoldb = catalog
            .source_intents
            .iter()
            .find(|source| source.source_intent_id == "bigsoldb")
            .ok_or_else(|| anyhow!("BigSolDB source intent is absent"))?;
        if bigsoldb.canonical_label != "BigSolDB 2.0"
            || !bigsoldb.aliases.iter().any(|alias| alias == "BidSolDB 2.0")
        {
            bail!("BidSolDB alias correction is absent");
        }
        let point2 = catalog
            .source_intents
            .iter()
            .find(|source| source.source_intent_id == "point2")
            .ok_or_else(|| anyhow!("POINT2 source intent is absent"))?;
        if point2.canonical_label != "POINT2"
            || !point2.aliases.iter().any(|alias| alias == "PONT2")
        {
            bail!("PONT2 alias correction is absent");
        }
    }
    let mut unit_ids = BTreeSet::new();
    for unit in &catalog.acquisition_units {
        if unit.schema != ACQUISITION_SCHEMA
            || !unit_ids.insert(unit.acquisition_unit_id.as_str())
            || !source_ids.contains(unit.source_intent_id.as_str())
        {
            bail!(
                "invalid or duplicate acquisition unit: {}",
                unit.acquisition_unit_id
            );
        }
        if unit.blocked_reason.is_none() && unit.consumers.is_empty() {
            bail!(
                "unblocked acquisition unit has no executable consumer: {}",
                unit.acquisition_unit_id
            );
        }
        match (&unit.parser, &unit.ord_git_lfs_tree) {
            (ParserKind::OrdGitLfsTree, Some(tree)) => {
                let object_value = serde_json::to_value(&tree.objects)?;
                let mut paths = BTreeSet::new();
                let observed_bytes = tree.objects.iter().map(|object| object.bytes).sum::<u64>();
                if tree.repository_url != "https://github.com/open-reaction-database/ord-data"
                    || tree.git_commit != ORD_DATA_COMMIT
                    || tree.tree_prefix.trim().is_empty()
                    || tree.object_count != ORD_PROTOBUF_OBJECTS
                    || tree.total_bytes != ORD_TOTAL_PROTOBUF_BYTES
                    || tree.object_count != tree.objects.len() as u64
                    || tree.total_bytes != observed_bytes
                    || tree.object_manifest_sha256 != stable_hash(&object_value)
                    || tree.objects.is_empty()
                    || tree.objects.iter().any(|object| {
                        object.bytes == 0
                            || object.path.starts_with('/')
                            || object.path.contains("..")
                            || !object.path.ends_with(".pb.gz")
                            || object.lfs_oid_sha256 != object.raw_sha256
                            || object.raw_sha256.len() != 64
                            || !object
                                .raw_sha256
                                .bytes()
                                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
                            || !paths.insert(object.path.as_str())
                    })
                {
                    bail!("ORD Git LFS tree acquisition metadata is invalid");
                }
            }
            (ParserKind::OrdGitLfsTree, None) => {
                bail!("ORD Git LFS tree parser is missing its complete object manifest")
            }
            (_, Some(_)) => bail!("ORD Git LFS metadata is attached to a different parser"),
            (_, None) => {}
        }
        for consumer in &unit.consumers {
            if consumer.module_id.trim().is_empty()
                || consumer.authority_limit.trim().is_empty()
                || consumer.scoring
            {
                bail!("dataset consumer is not authority-bound");
            }
        }
    }
    for source_id in &source_ids {
        if !catalog
            .acquisition_units
            .iter()
            .any(|unit| unit.source_intent_id == *source_id)
        {
            bail!("source intent has no child acquisition unit: {source_id}");
        }
    }
    let mut decision_ids = BTreeSet::new();
    let mut decision_units = BTreeSet::new();
    for decision in &catalog.rights_decisions {
        if decision.schema != RIGHTS_SCHEMA
            || !decision_ids.insert(decision.rights_decision_id.as_str())
            || !unit_ids.contains(decision.acquisition_unit_id.as_str())
            || !decision_units.insert(decision.acquisition_unit_id.as_str())
        {
            bail!("invalid, duplicate, or orphaned rights decision");
        }
    }
    if decision_units.len() != unit_ids.len() {
        bail!("every acquisition unit must have exactly one rights decision");
    }
    for unit in &catalog.acquisition_units {
        let decision = catalog
            .rights_decisions
            .iter()
            .find(|decision| decision.rights_decision_id == unit.rights_decision_id)
            .ok_or_else(|| anyhow!("rights decision reference is absent"))?;
        if decision.acquisition_unit_id != unit.acquisition_unit_id {
            bail!("rights decision is bound to a different acquisition unit");
        }
        if decision.promotion_eligible {
            bail!("catalog rights metadata cannot itself authorize Phase-0 promotion");
        }
        if unit.consumers.iter().any(|consumer| consumer.scoring) && !decision.promotion_eligible {
            bail!("non-promotion dataset is attached to a scoring consumer");
        }
    }
    Ok(())
}

fn validate_manifest(
    snapshot: &Path,
    unit: &AcquisitionUnitV2,
    decision: &RightsDecisionV2,
    manifest: &NormalizedDatasetManifestV2,
) -> Result<()> {
    if manifest.schema != DATASET_SCHEMA
        || manifest.acquisition_unit_id != unit.acquisition_unit_id
        || manifest.source_intent_id != unit.source_intent_id
        || manifest.evidence_class != unit.evidence_class
        || manifest.rights_class != decision.rights_class
        || manifest.quarantined != decision.rights_class.quarantined()
        || manifest.gzip_mtime != 0
    {
        bail!("normalized dataset manifest metadata mismatch");
    }
    for (path, expected) in [
        (&manifest.normalized_path, &manifest.normalized_sha256),
        (&manifest.rejection_path, &manifest.rejection_sha256),
        (
            &manifest.identity_index_path,
            &manifest.identity_index_sha256,
        ),
        (
            &manifest.duplicate_index_path,
            &manifest.duplicate_index_sha256,
        ),
    ] {
        let resolved = safe_join(snapshot, path)?;
        if !resolved.is_file() || file_sha256(&resolved)? != *expected {
            bail!("normalized child artifact hash mismatch: {path}");
        }
        let quarantine_path = path.starts_with("quarantine/");
        if quarantine_path != manifest.quarantined {
            bail!("rights quarantine is not physically enforced");
        }
    }
    Ok(())
}

fn validate_lock(snapshot: &Path, lock: &ModuleDatasetLockV2) -> Result<()> {
    if lock.schema != LOCK_SCHEMA || lock.network_access {
        bail!("invalid module dataset lock or scoring network access enabled");
    }
    if lock.scoring
        && (lock.rights_class != RightsClass::DerivativeAllowed
            || forbidden_promotion_evidence(&lock.evidence_class))
    {
        bail!("forbidden dataset class is locked for scoring");
    }
    let manifest_path = safe_join(snapshot, &lock.dataset_manifest_path)?;
    if file_sha256(&manifest_path)? != lock.dataset_manifest_sha256 {
        bail!("module lock dataset manifest hash mismatch");
    }
    let manifest: NormalizedDatasetManifestV2 = read_json_typed(&manifest_path)?;
    if manifest.dataset_id != lock.dataset_id
        || manifest.acquisition_unit_id != lock.acquisition_unit_id
        || manifest.normalized_sha256 != lock.normalized_artifact_sha256
        || manifest.rights_class != lock.rights_class
        || manifest.evidence_class != lock.evidence_class
    {
        bail!("module lock lineage does not match normalized dataset manifest");
    }
    Ok(())
}

fn forbidden_promotion_evidence(class: &EvidenceClass) -> bool {
    matches!(
        class,
        EvidenceClass::Computed
            | EvidenceClass::Predicted
            | EvidenceClass::Generated
            | EvidenceClass::WeakLabel
            | EvidenceClass::MetadataOnly
            | EvidenceClass::Prohibited
    )
}

fn require_selection(all: bool, unit: Option<&str>) -> Result<()> {
    if all == unit.is_some() {
        bail!("select exactly one of --all or --unit");
    }
    Ok(())
}

fn select_units<'a>(
    catalog: &'a DataCatalogV2,
    all: bool,
    requested: Option<&str>,
) -> Result<Vec<&'a AcquisitionUnitV2>> {
    if all {
        return Ok(catalog.acquisition_units.iter().collect());
    }
    let requested = requested.expect("selection validated");
    let unit = catalog
        .acquisition_units
        .iter()
        .find(|unit| unit.acquisition_unit_id == requested)
        .ok_or_else(|| anyhow!("unknown acquisition unit: {requested}"))?;
    Ok(vec![unit])
}

fn rights_by_unit(catalog: &DataCatalogV2) -> BTreeMap<&str, &RightsDecisionV2> {
    catalog
        .rights_decisions
        .iter()
        .map(|decision| (decision.acquisition_unit_id.as_str(), decision))
        .collect()
}

fn read_catalog(snapshot: &Path) -> Result<DataCatalogV2> {
    read_json_typed(&snapshot.join(CATALOG_FILE))
}

fn read_json_typed<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
    let bytes = fs::read(path).with_context(|| format!("reading {}", path.display()))?;
    let value = amphora_core::parse_json_strict(&bytes)?;
    serde_json::from_value(value).with_context(|| format!("parsing {}", path.display()))
}

fn rooted(root: &Path, path: &Path) -> Result<PathBuf> {
    if path.is_absolute() {
        return Ok(path.to_path_buf());
    }
    if path
        .components()
        .any(|part| matches!(part, Component::ParentDir | Component::RootDir))
    {
        bail!("relative path may not escape its workspace root");
    }
    Ok(root.join(path))
}

fn snapshot_channel(value: &str) -> Result<&'static str> {
    let normalized = value.replace('/', "-").replace('_', "-");
    if normalized == "feedback-v2" || normalized.starts_with("feedback-v2-") {
        Ok("feedback-v2")
    } else if normalized == "feedback-v3" || normalized.starts_with("feedback-v3-") {
        Ok("feedback-v3")
    } else if normalized == "feedback-v4" || normalized.starts_with("feedback-v4-") {
        Ok("feedback-v4")
    } else {
        bail!("invalid feedback snapshot identity: {value}")
    }
}

fn safe_join(root: &Path, relative_path: &str) -> Result<PathBuf> {
    let path = Path::new(relative_path);
    if path.is_absolute()
        || path
            .components()
            .any(|part| matches!(part, Component::ParentDir | Component::RootDir))
    {
        bail!("manifest path escapes the data snapshot");
    }
    Ok(root.join(path))
}

fn acquisition_receipt_path(snapshot: &Path, unit: &str) -> PathBuf {
    snapshot
        .join("receipts/acquisition")
        .join(format!("{}.json", safe_id(unit)))
}

fn dataset_manifest_path(snapshot: &Path, unit: &str) -> PathBuf {
    snapshot
        .join("manifests")
        .join(format!("{}.json", safe_id(unit)))
}

fn lock_path(snapshot: &Path, module: &str, dataset: &str) -> PathBuf {
    snapshot
        .join("locks")
        .join(safe_id(module))
        .join(format!("{}.json", safe_id(dataset)))
}

fn persist_report(snapshot: &Path, name: &str, value: &Value) -> Result<()> {
    let path = snapshot.join("reports").join(name);
    let bytes = canonical_bytes(value)?;
    if path.exists() && fs::read(&path)? != bytes {
        fs::remove_file(&path)?;
    }
    persist_immutable(&path, &bytes)
}

fn deterministic_gzip(file: File) -> flate2::write::GzEncoder<BufWriter<File>> {
    GzBuilder::new()
        .mtime(0)
        .operating_system(255)
        .write(BufWriter::new(file), Compression::default())
}

fn prepare_temporary(path: &Path) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    if path.exists() {
        fs::remove_file(path)?;
    }
    Ok(())
}

fn temporary_path(path: &Path) -> PathBuf {
    path.with_extension(format!("tmp-{}", std::process::id()))
}

fn install_generated(temporary: &Path, destination: &Path) -> Result<()> {
    let generated_hash = file_sha256(temporary)?;
    if destination.exists() {
        if file_sha256(destination)? == generated_hash {
            fs::remove_file(temporary)?;
            return Ok(());
        }
        bail!(
            "immutable normalized artifact differs from clean rebuild: {}",
            destination.display()
        );
    }
    fs::rename(temporary, destination)?;
    Ok(())
}

fn write_json_line(writer: &mut impl Write, value: &impl Serialize) -> Result<()> {
    let value = serde_json::to_value(value)?;
    writer.write_all(&canonical_bytes(&value)?)?;
    writer.write_all(b"\n")?;
    Ok(())
}

fn field_map(headers: &[String], row: &StringRecord) -> BTreeMap<String, String> {
    headers
        .iter()
        .zip(row.iter())
        .map(|(header, value)| (header.clone(), value.to_owned()))
        .collect()
}

fn clean_header(value: &str) -> String {
    value.trim_start_matches('\u{feff}').trim().to_owned()
}

fn selected_fields(
    fields: &BTreeMap<String, String>,
    columns: &[String],
) -> BTreeMap<String, String> {
    columns
        .iter()
        .filter_map(|column| {
            fields
                .get(column)
                .filter(|value| !value.trim().is_empty())
                .map(|value| (column.clone(), value.clone()))
        })
        .collect()
}

fn canonical_identity(fields: &BTreeMap<String, String>, columns: &[String]) -> Option<String> {
    let values = columns
        .iter()
        .filter_map(|column| nonempty(fields.get(column)))
        .map(|value| value.trim().to_ascii_lowercase())
        .collect::<Vec<_>>();
    if values.is_empty() {
        None
    } else {
        Some(values.join("|"))
    }
}

fn nonempty(value: Option<&String>) -> Option<String> {
    value
        .map(|value| value.trim())
        .filter(|value| !value.is_empty())
        .map(str::to_owned)
}

fn parse_number(value: &str) -> Option<f64> {
    let first = value
        .trim()
        .trim_start_matches(['<', '>', '~'])
        .split(|character: char| character.is_whitespace() || character == ',')
        .next()?;
    first.parse::<f64>().ok().filter(|value| value.is_finite())
}

fn corrosion_rating(value: &str) -> (Option<String>, Option<String>) {
    let trimmed = value.trim();
    let uppercase = trimmed.to_ascii_uppercase();
    let rating = ['A', 'B', 'C', 'D'].into_iter().find(|letter| {
        uppercase.starts_with(*letter)
            && uppercase
                .chars()
                .nth(1)
                .is_some_and(|next| next == ' ' || next == '(')
    });
    let qualifier = if uppercase.contains("MAX") {
        Some("MAXIMUM")
    } else if uppercase.contains("MIN") {
        Some("MINIMUM")
    } else if uppercase.contains(" TO ") || uppercase.contains('-') {
        Some("RANGE")
    } else {
        None
    };
    (
        rating.map(|value| value.to_string()),
        qualifier.map(str::to_owned),
    )
}

fn hash_json(value: &impl Serialize) -> Result<String> {
    Ok(bytes_sha256(&canonical_bytes(&serde_json::to_value(
        value,
    )?)?))
}

fn file_sha256(path: &Path) -> Result<String> {
    let mut reader =
        BufReader::new(File::open(path).with_context(|| format!("hashing {}", path.display()))?);
    let mut digest = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let count = reader.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        digest.update(&buffer[..count]);
    }
    Ok(format!("{:x}", digest.finalize()))
}

fn bytes_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn encode_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn decode_hex_32(value: &str) -> Result<[u8; 32]> {
    if value.len() != 64 {
        bail!("Ed25519 public key must contain 64 hexadecimal characters");
    }
    let mut output = [0_u8; 32];
    for (index, byte) in output.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)
            .context("decoding Ed25519 public key")?;
    }
    Ok(output)
}

fn relative(root: &Path, path: &Path) -> String {
    path.strip_prefix(root)
        .unwrap_or(path)
        .to_string_lossy()
        .replace('\\', "/")
}

fn safe_id(value: &str) -> String {
    value
        .chars()
        .map(|character| {
            if character.is_ascii_alphanumeric() || matches!(character, '-' | '_') {
                character
            } else {
                '-'
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};
    use zip::write::SimpleFileOptions;

    fn temporary_directory(label: &str) -> PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!(
            "amphora-data-v2-{label}-{}-{nonce}",
            std::process::id()
        ));
        fs::create_dir_all(&path).unwrap();
        path
    }

    fn tree_metadata(root: &Path) -> BTreeMap<String, (u64, u128)> {
        fn visit(root: &Path, path: &Path, output: &mut BTreeMap<String, (u64, u128)>) {
            for entry in fs::read_dir(path).unwrap() {
                let entry = entry.unwrap();
                let path = entry.path();
                let metadata = entry.metadata().unwrap();
                if metadata.is_dir() {
                    visit(root, &path, output);
                } else if metadata.is_file() {
                    let modified = metadata
                        .modified()
                        .unwrap()
                        .duration_since(UNIX_EPOCH)
                        .unwrap()
                        .as_nanos();
                    output.insert(relative(root, &path), (metadata.len(), modified));
                }
            }
        }
        let mut output = BTreeMap::new();
        visit(root, root, &mut output);
        output
    }

    fn test_unit(parser: ParserKind) -> AcquisitionUnitV2 {
        AcquisitionUnitV2 {
            schema: ACQUISITION_SCHEMA.into(),
            acquisition_unit_id: "fixture".into(),
            source_intent_id: "bigsoldb".into(),
            title: "fixture".into(),
            filename: "fixture.csv".into(),
            source_url: None,
            expected_sha256: None,
            expected_bytes: None,
            cache_import_path: None,
            credential_ref: None,
            parser,
            ord_git_lfs_tree: None,
            endpoint: "fixture".into(),
            unit: None,
            identity_columns: vec!["Solvent".into()],
            condition_columns: Vec::new(),
            citation_column: None,
            value_column: None,
            evidence_class: EvidenceClass::ExternalMeasured,
            rights_decision_id: "rights-fixture".into(),
            consumers: Vec::new(),
            blocked_reason: None,
        }
    }

    fn test_decision() -> RightsDecisionV2 {
        RightsDecisionV2 {
            schema: RIGHTS_SCHEMA.into(),
            rights_decision_id: "rights-fixture".into(),
            acquisition_unit_id: "fixture".into(),
            rights_class: RightsClass::DerivativeAllowed,
            license: "fixture".into(),
            basis: "fixture".into(),
            decision_receipt: None,
            promotion_eligible: false,
        }
    }

    #[test]
    fn bigsoldb_preserves_observations_and_density_identity_join() {
        let solubility = b"SMILES_Solute,Temperature_K,Solvent,SMILES_Solvent,Solubility(mole_fraction),Solubility(mol/L),LogS(mol/L),Compound_Name,CAS,PubChem_CID,FDA_Approved,Source\nCC,298.15,Ethanol,CCO,0.1,1.0,0.0,x,1,2,No,doi:a\n";
        let density = b"Solvent,Temperature_K,Density_g/cm^3,Source\nethanol,298.15,0.785,doi:b\n";
        let decision = test_decision();
        let mut identities = Vec::new();
        for (parser, bytes) in [
            (ParserKind::BigsoldbSolubility, solubility.as_slice()),
            (ParserKind::BigsoldbDensity, density.as_slice()),
        ] {
            let unit = test_unit(parser);
            let mut rows = Vec::new();
            let mut rejects = Vec::new();
            let mut state = NormalizeState {
                records: 0,
                rejections: 0,
                endpoint_counts: BTreeMap::new(),
                identities: BTreeMap::new(),
                duplicate_keys: BTreeMap::new(),
            };
            normalize_csv(
                bytes,
                None,
                &unit,
                &decision,
                "fixture-hash",
                &"a".repeat(64),
                &mut rows,
                &mut rejects,
                &mut state,
            )
            .unwrap();
            let row: NormalizedRecordV2 =
                serde_json::from_slice(rows.strip_suffix(b"\n").unwrap()).unwrap();
            identities.push(row.canonical_identity.unwrap());
            assert_eq!(state.records, 1);
            assert_eq!(state.rejections, 0);
            assert!(!row.raw_fields.is_empty());
        }
        assert_eq!(identities, vec!["ethanol", "ethanol"]);
    }

    #[test]
    fn nist_rating_is_preserved_beside_numeric_rate() {
        let (rating, qualifier) = corrosion_rating("D (Poor)");
        assert_eq!(rating.as_deref(), Some("D"));
        assert_eq!(qualifier, None);
        let (rating, qualifier) = corrosion_rating("0.05 max");
        assert_eq!(rating, None);
        assert_eq!(qualifier.as_deref(), Some("MAXIMUM"));
        assert_eq!(parse_number("0.05 max"), Some(0.05));
    }

    #[test]
    fn pronto_parser_selects_only_time_ordered_process_streams() {
        let root = temporary_directory("pronto");
        let path = root.join("pronto.zip");
        let mut archive = zip::ZipWriter::new(File::create(&path).unwrap());
        for index in 0..10 {
            archive
                .start_file(
                    format!("PRONTO/C{index} Condition/Test{index}/Process Data/test{index}.csv"),
                    SimpleFileOptions::default(),
                )
                .unwrap();
            archive
                .write_all(
                    b"Start Time,fixture\nTag,Sensor A,Sensor B\nTIMESTAMP,A,B\n09/12/2017 10:00,1.0,\n09/12/2017 10:00,2.0,error\n",
                )
                .unwrap();
            archive
                .start_file(
                    format!("PRONTO/C{index} Condition/Test{index}/Videos/ignored.csv"),
                    SimpleFileOptions::default(),
                )
                .unwrap();
            archive.write_all(b"not,process,data\n").unwrap();
        }
        archive.finish().unwrap();
        let unit = test_unit(ParserKind::ProntoProcessZip);
        let decision = test_decision();
        let mut rows = Vec::new();
        let mut rejects = Vec::new();
        let mut state = NormalizeState {
            records: 0,
            rejections: 0,
            endpoint_counts: BTreeMap::new(),
            identities: BTreeMap::new(),
            duplicate_keys: BTreeMap::new(),
        };
        normalize_pronto_process_zip(
            &path,
            &unit,
            &decision,
            "fixture-hash",
            &"a".repeat(64),
            &mut rows,
            &mut rejects,
            &mut state,
        )
        .unwrap();
        assert_eq!(state.records, 20);
        assert_eq!(state.rejections, 0);
        let first: NormalizedRecordV2 =
            serde_json::from_slice(rows.split(|byte| *byte == b'\n').next().unwrap()).unwrap();
        assert_eq!(first.value_number, Some(0.5));
        assert!(first
            .archive_entry
            .as_deref()
            .is_some_and(|name| name.contains("/Process Data/")));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn chebi_parser_requires_and_preserves_three_hundred_structures() {
        let root = temporary_directory("chebi");
        let path = root.join("chebi.sdf.gz");
        let mut gzip = deterministic_gzip(File::create(&path).unwrap());
        for index in 1..=300 {
            writeln!(
                gzip,
                "molecule {index}\n  fixture\n\n  0  0  0  0  0  0            999 V2000\nM  END\n> <ChEBI ID>\nCHEBI:{index}\n\n> <ChEBI NAME>\nfixture {index}\n\n> <STAR>\n3\n\n> <MASS>\n{}.0\n\n> <FORMULA>\nC{index}H2\n\n> <SMILES>\nC[C@H]({index})O\n\n> <INCHIKEY>\nFIXTURE{index:020}\n\n$$$$",
                index + 10
            )
            .unwrap();
        }
        gzip.finish().unwrap();
        let unit = test_unit(ParserKind::ChebiSdfGzip);
        let decision = test_decision();
        let mut rows = Vec::new();
        let mut rejects = Vec::new();
        let mut state = NormalizeState {
            records: 0,
            rejections: 0,
            endpoint_counts: BTreeMap::new(),
            identities: BTreeMap::new(),
            duplicate_keys: BTreeMap::new(),
        };
        normalize_chebi_sdf_gzip(
            &path,
            &unit,
            &decision,
            "fixture-hash",
            &"b".repeat(64),
            &mut rows,
            &mut rejects,
            &mut state,
        )
        .unwrap();
        assert_eq!(state.records, 300);
        assert_eq!(state.identities.len(), 300);
        assert_eq!(state.rejections, 0);
        let first: NormalizedRecordV2 =
            serde_json::from_slice(rows.split(|byte| *byte == b'\n').next().unwrap()).unwrap();
        assert_eq!(first.conditions["formula"], "C1H2");
        assert_eq!(first.conditions["stereochemistry_declared"], "true");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn fixed_gzip_header_and_sorted_indexes_are_reproducible() {
        let root = temporary_directory("gzip");
        let first = root.join("first.gz");
        let second = root.join("second.gz");
        for path in [&first, &second] {
            let mut writer = deterministic_gzip(File::create(path).unwrap());
            writer.write_all(b"{\"a\":1}\n").unwrap();
            writer.finish().unwrap();
        }
        assert_eq!(fs::read(&first).unwrap(), fs::read(&second).unwrap());
        assert_eq!(&fs::read(&first).unwrap()[4..8], &[0, 0, 0, 0]);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn forbidden_classes_cannot_be_promotion_evidence() {
        for class in [
            EvidenceClass::Computed,
            EvidenceClass::Predicted,
            EvidenceClass::Generated,
            EvidenceClass::WeakLabel,
            EvidenceClass::MetadataOnly,
            EvidenceClass::Prohibited,
        ] {
            assert!(forbidden_promotion_evidence(&class));
        }
        assert!(!forbidden_promotion_evidence(
            &EvidenceClass::ExternalMeasured
        ));
    }

    #[test]
    fn identity_overlap_is_reported_without_discarding_rows() {
        let mut first_unit = HashMap::new();
        let mut pairs = BTreeMap::new();
        record_identity_overlap("same", "train", &mut first_unit, &mut pairs);
        record_identity_overlap("same", "test", &mut first_unit, &mut pairs);
        record_identity_overlap("same", "test", &mut first_unit, &mut pairs);
        assert_eq!(pairs["test<->train"], 2);
        assert_eq!(first_unit["same"], "train");
    }

    #[test]
    fn acquire_normalize_consume_and_audit_are_reproducible_end_to_end() {
        let root = temporary_directory("integration");
        let snapshot = root.join("feedback/v2");
        fs::create_dir_all(&snapshot).unwrap();
        let workspace = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .to_path_buf();
        let mut catalog: DataCatalogV2 =
            read_json_typed(&workspace.join("feedback/v2/catalog.json")).unwrap();
        let fixture = root.join("density.csv");
        let bytes = b"Solvent,Temperature_K,Density_g/cm^3,Source\nethanol,298.15,0.785,doi:a\nwater,298.15,0.997,doi:b\n";
        fs::write(&fixture, bytes).unwrap();
        let mut unit = catalog
            .acquisition_units
            .iter()
            .find(|unit| unit.acquisition_unit_id == "bigsoldb_density")
            .unwrap()
            .clone();
        unit.expected_sha256 = Some(bytes_sha256(bytes));
        unit.expected_bytes = Some(bytes.len() as u64);
        unit.cache_import_path = Some(fixture.display().to_string());
        *catalog
            .acquisition_units
            .iter_mut()
            .find(|candidate| candidate.acquisition_unit_id == unit.acquisition_unit_id)
            .unwrap() = unit.clone();
        fs::write(
            snapshot.join(CATALOG_FILE),
            canonical_bytes(&serde_json::to_value(catalog).unwrap()).unwrap(),
        )
        .unwrap();

        acquire(
            &root,
            Path::new("feedback/v2"),
            false,
            Some("bigsoldb_density"),
            None,
        )
        .unwrap();
        normalize(
            &root,
            Path::new("feedback/v2"),
            false,
            Some("bigsoldb_density"),
        )
        .unwrap();
        let manifest: NormalizedDatasetManifestV2 =
            read_json_typed(&dataset_manifest_path(&snapshot, "bigsoldb_density")).unwrap();
        assert_eq!(manifest.record_count, 2);
        let first_hash = manifest.normalized_sha256.clone();
        normalize(
            &root,
            Path::new("feedback/v2"),
            false,
            Some("bigsoldb_density"),
        )
        .unwrap();
        let rebuilt: NormalizedDatasetManifestV2 =
            read_json_typed(&dataset_manifest_path(&snapshot, "bigsoldb_density")).unwrap();
        assert_eq!(rebuilt.normalized_sha256, first_hash);
        let module = root.join("amphora-ingredient-library");
        fs::create_dir(&module).unwrap();
        let signed_source_lock = module.join("evidence/phase0/sources/source-lock.v1.json");
        fs::create_dir_all(signed_source_lock.parent().unwrap()).unwrap();
        fs::write(&signed_source_lock, b"signed-history-must-not-change\n").unwrap();
        let signed_source_lock_hash = file_sha256(&signed_source_lock).unwrap();
        consume(
            &root,
            Path::new("feedback/v2"),
            Some("amphora-ingredient-library"),
            Some(&manifest.dataset_id),
            false,
            false,
        )
        .unwrap();
        assert_eq!(
            file_sha256(&signed_source_lock).unwrap(),
            signed_source_lock_hash
        );
        audit(&root, Path::new("feedback/v2"), true).unwrap();
        let report: Value = read_json_typed(&snapshot.join("reports/audit-report.json")).unwrap();
        assert_eq!(report["status"], "PASS");
        assert_eq!(report["normalized_row_count"], 2);
        let before = tree_metadata(&root);
        audit(&root, Path::new("feedback/v2"), false).unwrap();
        assert_eq!(tree_metadata(&root), before);
        fs::remove_dir_all(root).unwrap();
    }
}
