use crate::{sign_dsse, stable_hash, verify_dsse, DsseEnvelope, TrustStore};
use ed25519_dalek::SigningKey;
use flate2::read::GzDecoder;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File};
use std::io::{BufRead, BufReader, Read};
use std::path::{Component, Path, PathBuf};
use thiserror::Error;

pub const NORMALIZED_RECORD_SCHEMA: &str = "amphora.normalized-record.v2";
pub const DATASET_MANIFEST_V2_SCHEMA: &str = "amphora.normalized-dataset-manifest.v2";
pub const MODULE_DATASET_LOCK_SCHEMA: &str = "amphora.module-dataset-lock.v2";
pub const DERIVED_RECORD_SCHEMA: &str = "amphora.module-derived-record.v1";
pub const ACTIVATION_SCHEMA: &str = "amphora.module-dataset-activation.v1";
pub const ACTIVATION_SET_SCHEMA: &str = "amphora.module-dataset-activation-set.v1";
pub const PHASE0_SOURCE_LOCK_V2_SCHEMA: &str = "amphora.phase0-source-lock.v2";
pub const RIGHTS_REVIEW_RECEIPT_SCHEMA: &str = "amphora.rights-review-receipt.v1";
pub const RIGHTS_REVIEW_PAYLOAD_TYPE: &str =
    "application/vnd.amphora.rights-review-receipt.v1+json";
pub const RIGHTS_TRUST_STORE_SCHEMA: &str = "amphora.rights-review-trust-store.v1";
pub const AUTHORIZATION_OVERLAY_SCHEMA: &str = "amphora.module-dataset-authorization-overlay.v1";
pub const AUTHORIZATION_LEDGER_SCHEMA: &str = "amphora.module-dataset-authorization-ledger.v1";

const REQUIRED_RIGHTS_EXCLUSIONS: [&str; 9] = [
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

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct DataCatalogV2 {
    pub schema: String,
    pub snapshot_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parent_snapshot: Option<DataSnapshotParentV1>,
    pub source_intents: Vec<SourceIntentV2>,
    pub acquisition_units: Vec<AcquisitionUnitV2>,
    pub rights_decisions: Vec<RightsDecisionV2>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct DataSnapshotParentV1 {
    pub snapshot_id: String,
    pub catalog_path: String,
    pub catalog_sha256: String,
    pub immutable: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SourceIntentV2 {
    pub schema: String,
    pub source_intent_id: String,
    pub original_label: String,
    pub canonical_label: String,
    #[serde(default)]
    pub aliases: Vec<String>,
    pub source_url: String,
    pub program_disposition: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct AcquisitionUnitV2 {
    pub schema: String,
    pub acquisition_unit_id: String,
    pub source_intent_id: String,
    pub title: String,
    pub filename: String,
    pub source_url: Option<String>,
    pub expected_sha256: Option<String>,
    pub expected_bytes: Option<u64>,
    pub cache_import_path: Option<String>,
    pub credential_ref: Option<String>,
    pub parser: ParserKind,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ord_git_lfs_tree: Option<OrdGitLfsTreeV1>,
    pub endpoint: String,
    pub unit: Option<String>,
    #[serde(default)]
    pub identity_columns: Vec<String>,
    #[serde(default)]
    pub condition_columns: Vec<String>,
    pub citation_column: Option<String>,
    pub value_column: Option<String>,
    pub evidence_class: EvidenceClass,
    pub rights_decision_id: String,
    #[serde(default)]
    pub consumers: Vec<DatasetConsumerV2>,
    pub blocked_reason: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct DatasetConsumerV2 {
    pub module_id: String,
    pub consumer: ConsumerKind,
    pub scoring: bool,
    pub authority_limit: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ConsumerKind {
    OfflineBenchmark,
    TrainingCorpus,
    RetrievalIndex,
    Diagnostic,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ParserKind {
    BigsoldbSolubility,
    BigsoldbDensity,
    NistCorrZip,
    Csv,
    ZipCsvCorpus,
    SplitCsv,
    MetadataOnly,
    SecomZip,
    ProntoProcessZip,
    ChebiSdfGzip,
    OrdGitLfsTree,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OrdGitLfsTreeV1 {
    pub repository_url: String,
    pub git_commit: String,
    pub tree_prefix: String,
    pub object_manifest_sha256: String,
    pub object_count: u64,
    pub total_bytes: u64,
    pub objects: Vec<OrdGitLfsObjectV1>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OrdGitLfsObjectV1 {
    pub path: String,
    pub lfs_oid_sha256: String,
    pub bytes: u64,
    pub raw_sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EvidenceClass {
    OwnedMeasured,
    ExternalMeasured,
    Computed,
    Predicted,
    Generated,
    WeakLabel,
    MetadataOnly,
    Prohibited,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum RightsClass {
    DerivativeAllowed,
    ContextOnly,
    Credentialed,
    ManualExport,
    Unresolved,
    ProhibitedBulk,
}

impl RightsClass {
    pub fn quarantined(&self) -> bool {
        !matches!(self, Self::DerivativeAllowed)
    }

    pub fn acquisition_prohibited(&self) -> bool {
        matches!(self, Self::ProhibitedBulk | Self::Unresolved)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct RightsDecisionV2 {
    pub schema: String,
    pub rights_decision_id: String,
    pub acquisition_unit_id: String,
    pub rights_class: RightsClass,
    pub license: String,
    pub basis: String,
    pub decision_receipt: Option<String>,
    pub promotion_eligible: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RightsReviewReceiptV1 {
    pub schema: String,
    pub receipt_id: String,
    pub module_id: String,
    pub snapshot_id: String,
    pub dataset_id: String,
    pub acquisition_unit_id: String,
    pub rights_decision_id: String,
    pub rights_decision_hash: String,
    pub artifact_path: String,
    pub artifact_sha256: String,
    pub rights_class: RightsClass,
    pub license: String,
    pub accepted: bool,
    pub authority_ceiling: String,
    pub exclusions: Vec<String>,
    pub reviewer_key_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<DsseEnvelope>,
}

impl RightsReviewReceiptV1 {
    pub fn bind_receipt_id(&mut self) -> Result<(), DataV2Error> {
        self.receipt_id = self.computed_receipt_id()?;
        Ok(())
    }

    pub fn computed_receipt_id(&self) -> Result<String, DataV2Error> {
        let mut unsigned = self.clone();
        unsigned.receipt_id.clear();
        unsigned.signature = None;
        Ok(format!(
            "rights-review-{}",
            stable_hash(&serde_json::to_value(unsigned)?)
        ))
    }

    pub fn validate(&self) -> Result<(), DataV2Error> {
        let exclusions = self
            .exclusions
            .iter()
            .map(String::as_str)
            .collect::<BTreeSet<_>>();
        if self.schema != RIGHTS_REVIEW_RECEIPT_SCHEMA
            || self.receipt_id != self.computed_receipt_id()?
            || self.module_id.strip_prefix("amphora-").is_none()
            || !valid_snapshot_id(&self.snapshot_id)
            || self.dataset_id.trim().is_empty()
            || self.acquisition_unit_id.trim().is_empty()
            || self.rights_decision_id.trim().is_empty()
            || !is_hash(&self.rights_decision_hash)
            || !safe_relative(&self.artifact_path)
            || !is_hash(&self.artifact_sha256)
            || self.rights_class != RightsClass::DerivativeAllowed
            || self.license.trim().is_empty()
            || !self.accepted
            || self.authority_ceiling != "AUDIT_ONLY"
            || self.reviewer_key_id.trim().is_empty()
            || exclusions.len() != self.exclusions.len()
            || REQUIRED_RIGHTS_EXCLUSIONS
                .iter()
                .any(|required| !exclusions.contains(required))
        {
            return Err(DataV2Error::InvalidRightsReceipt);
        }
        Ok(())
    }

    fn unsigned_bytes(&self) -> Result<Vec<u8>, DataV2Error> {
        let mut unsigned = self.clone();
        unsigned.signature = None;
        let value = crate::canonicalize(&serde_json::to_value(unsigned)?);
        Ok(serde_json::to_vec(&value)?)
    }

    pub fn sign(&mut self, key_id: &str, key: &SigningKey) -> Result<(), DataV2Error> {
        if self.reviewer_key_id != key_id {
            return Err(DataV2Error::RightsRole);
        }
        self.validate()?;
        self.signature = Some(sign_dsse(
            RIGHTS_REVIEW_PAYLOAD_TYPE,
            &self.unsigned_bytes()?,
            key_id,
            key,
        ));
        Ok(())
    }

    pub fn verify_signature(&self, trust: &LoadedRightsTrust) -> Result<String, DataV2Error> {
        self.validate()?;
        trust.require_reviewer(&self.reviewer_key_id)?;
        let envelope = self
            .signature
            .as_ref()
            .ok_or(DataV2Error::UnsignedRightsReceipt)?;
        if envelope.payload_type != RIGHTS_REVIEW_PAYLOAD_TYPE {
            return Err(DataV2Error::InvalidRightsSignature);
        }
        let verified = verify_dsse(envelope, &trust.trust)?;
        if verified.key_id != self.reviewer_key_id || verified.payload != self.unsigned_bytes()? {
            return Err(DataV2Error::InvalidRightsSignature);
        }
        Ok(verified.key_id)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RightsTrustStoreV1 {
    pub schema: String,
    pub authorization_status: String,
    pub keys: Vec<RightsTrustKeyV1>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RightsTrustKeyV1 {
    pub key_id: String,
    pub algorithm: String,
    pub role: String,
    pub public_key_hex: String,
    pub rights_review_authorized: bool,
    pub development: bool,
    pub revoked: bool,
}

#[derive(Debug, Clone)]
pub struct LoadedRightsTrust {
    trust: TrustStore,
    roles: BTreeMap<String, String>,
}

impl LoadedRightsTrust {
    pub fn require_reviewer(&self, key_id: &str) -> Result<(), DataV2Error> {
        if self.roles.get(key_id).map(String::as_str) != Some("RIGHTS_REVIEWER") {
            return Err(DataV2Error::RightsRole);
        }
        Ok(())
    }
}

pub fn load_rights_trust_store(path: &Path) -> Result<LoadedRightsTrust, DataV2Error> {
    let file: RightsTrustStoreV1 = read_json(path)?;
    if file.schema != RIGHTS_TRUST_STORE_SCHEMA
        || file.authorization_status != "AUTHORIZED_RIGHTS_REVIEW_IDENTITIES"
        || file.keys.is_empty()
    {
        return Err(DataV2Error::InvalidRightsTrustStore);
    }
    let mut trust = TrustStore::default();
    let mut roles = BTreeMap::new();
    let mut public_keys = BTreeSet::new();
    let mut active_reviewers = 0_usize;
    for key in file.keys {
        if key.algorithm != "Ed25519"
            || key.role != "RIGHTS_REVIEWER"
            || !key.rights_review_authorized
            || key.development
        {
            return Err(DataV2Error::InvalidRightsTrustStore);
        }
        let bytes = decode_hex_32(&key.public_key_hex)?;
        let expected_id = format!("rights-reviewer-{}", sha256_bytes(&bytes));
        if key.key_id != expected_id || !public_keys.insert(bytes) {
            return Err(DataV2Error::InvalidRightsTrustStore);
        }
        trust.insert(key.key_id.clone(), bytes)?;
        if key.revoked {
            trust.revoke(key.key_id.clone());
        } else {
            active_reviewers += 1;
            if roles.insert(key.key_id.clone(), key.role.clone()).is_some() {
                return Err(DataV2Error::InvalidRightsTrustStore);
            }
        }
    }
    if active_reviewers == 0 {
        return Err(DataV2Error::InvalidRightsTrustStore);
    }
    Ok(LoadedRightsTrust { trust, roles })
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModuleDatasetAuthorizationOverlayV1 {
    pub schema: String,
    pub overlay_id: String,
    pub parent_overlay_id: Option<String>,
    pub module_id: String,
    pub snapshot_id: String,
    pub dataset_id: String,
    pub acquisition_unit_id: String,
    pub activation_hash: String,
    pub artifact_path: String,
    pub artifact_sha256: String,
    pub rights_receipt_path: String,
    pub rights_receipt_sha256: String,
    pub rights_reviewer_key_id: String,
    pub authority_ceiling: String,
    pub scoring_authorized: bool,
}

impl ModuleDatasetAuthorizationOverlayV1 {
    pub fn bind_overlay_id(&mut self) -> Result<(), DataV2Error> {
        self.overlay_id = self.computed_overlay_id()?;
        Ok(())
    }

    pub fn computed_overlay_id(&self) -> Result<String, DataV2Error> {
        let mut value = self.clone();
        value.overlay_id.clear();
        Ok(format!(
            "authorization-{}",
            stable_hash(&serde_json::to_value(value)?)
        ))
    }

    pub fn validate(&self) -> Result<(), DataV2Error> {
        if self.schema != AUTHORIZATION_OVERLAY_SCHEMA
            || self.overlay_id != self.computed_overlay_id()?
            || self.module_id.strip_prefix("amphora-").is_none()
            || !valid_snapshot_id(&self.snapshot_id)
            || self.dataset_id.trim().is_empty()
            || self.acquisition_unit_id.trim().is_empty()
            || !is_hash(&self.activation_hash)
            || !safe_relative(&self.artifact_path)
            || !is_hash(&self.artifact_sha256)
            || !safe_relative(&self.rights_receipt_path)
            || !is_hash(&self.rights_receipt_sha256)
            || self.rights_reviewer_key_id.trim().is_empty()
            || self.authority_ceiling != "AUDIT_ONLY"
            || self.scoring_authorized
            || self
                .parent_overlay_id
                .as_ref()
                .is_some_and(|parent| !parent.starts_with("authorization-") || parent.len() != 78)
        {
            return Err(DataV2Error::InvalidAuthorizationOverlay);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct AuthorizationOverlayRefV1 {
    pub overlay_id: String,
    pub path: String,
    pub sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModuleDatasetAuthorizationLedgerV1 {
    pub schema: String,
    pub module_id: String,
    pub snapshot_id: String,
    pub head_overlay_id: String,
    pub overlays: Vec<AuthorizationOverlayRefV1>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct NormalizedDatasetManifestV2 {
    pub schema: String,
    pub dataset_id: String,
    pub acquisition_unit_id: String,
    pub source_intent_id: String,
    pub raw_sha256: String,
    pub raw_bytes: u64,
    pub normalized_path: String,
    pub normalized_sha256: String,
    pub rejection_path: String,
    pub rejection_sha256: String,
    pub identity_index_path: String,
    pub identity_index_sha256: String,
    pub duplicate_index_path: String,
    pub duplicate_index_sha256: String,
    pub record_count: u64,
    pub rejection_count: u64,
    pub endpoint_counts: BTreeMap<String, u64>,
    pub evidence_class: EvidenceClass,
    pub rights_class: RightsClass,
    pub quarantined: bool,
    pub ordering: String,
    pub gzip_mtime: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModuleDatasetLockV2 {
    pub schema: String,
    pub module_id: String,
    pub dataset_id: String,
    pub acquisition_unit_id: String,
    pub dataset_manifest_path: String,
    pub dataset_manifest_sha256: String,
    pub normalized_artifact_sha256: String,
    pub consumer: ConsumerKind,
    pub scoring: bool,
    pub authority_limit: String,
    pub rights_class: RightsClass,
    pub evidence_class: EvidenceClass,
    pub network_access: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct NormalizedRecordV2 {
    pub schema: String,
    pub dataset_id: String,
    pub record_id: String,
    pub source_intent_id: String,
    pub acquisition_unit_id: String,
    pub raw_file_sha256: String,
    pub raw_row_sha256: String,
    pub row_number: u64,
    pub archive_entry: Option<String>,
    pub evidence_class: EvidenceClass,
    pub rights_class: RightsClass,
    pub endpoint: String,
    pub value_number: Option<f64>,
    pub value_text: Option<String>,
    pub unit: Option<String>,
    pub citation: Option<String>,
    pub canonical_identity: Option<String>,
    pub conditions: BTreeMap<String, String>,
    pub raw_fields: BTreeMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct DerivedRecordV1 {
    pub schema: String,
    pub dataset_id: String,
    pub record_id: String,
    pub source_intent_id: String,
    pub acquisition_unit_id: String,
    pub raw_row_sha256: String,
    pub row_number: u64,
    pub evidence_class: EvidenceClass,
    pub rights_class: RightsClass,
    pub endpoint: String,
    pub value_number: Option<f64>,
    pub value_text: Option<String>,
    pub unit: Option<String>,
    pub citation: Option<String>,
    pub canonical_identity: Option<String>,
    pub conditions: BTreeMap<String, String>,
}

impl From<NormalizedRecordV2> for DerivedRecordV1 {
    fn from(row: NormalizedRecordV2) -> Self {
        Self {
            schema: DERIVED_RECORD_SCHEMA.into(),
            dataset_id: row.dataset_id,
            record_id: row.record_id,
            source_intent_id: row.source_intent_id,
            acquisition_unit_id: row.acquisition_unit_id,
            raw_row_sha256: row.raw_row_sha256,
            row_number: row.row_number,
            evidence_class: row.evidence_class,
            rights_class: row.rights_class,
            endpoint: row.endpoint,
            value_number: row.value_number,
            value_text: row.value_text,
            unit: row.unit,
            citation: row.citation,
            canonical_identity: row.canonical_identity,
            conditions: row.conditions,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModuleDatasetActivationV1 {
    pub schema: String,
    pub module_id: String,
    pub snapshot_id: String,
    pub dataset_id: String,
    pub acquisition_unit_id: String,
    pub catalog_path: String,
    pub catalog_sha256: String,
    pub acquisition_receipt_path: String,
    pub acquisition_receipt_sha256: String,
    pub rights_receipt_path: String,
    pub rights_receipt_sha256: String,
    pub rights_reviewed: bool,
    pub dataset_manifest_path: String,
    pub dataset_manifest_sha256: String,
    pub normalized_object_path: String,
    pub normalized_object_sha256: String,
    pub derived_view_path: String,
    pub derived_view_sha256: String,
    pub split_path: String,
    pub split_sha256: String,
    pub accepted_row_count: u64,
    pub rejected_row_count: u64,
    pub excluded_row_count: u64,
    pub quarantined_row_count: u64,
    pub evidence_class: EvidenceClass,
    pub rights_class: RightsClass,
    pub consumer: ConsumerKind,
    pub scoring: bool,
    pub authority_limit: String,
    pub claim_locks: BTreeMap<String, bool>,
    pub generator_version: String,
    pub deterministic_command: String,
    pub zero_network: bool,
    pub candidate_input_excluded: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModuleDatasetActivationSetV1 {
    pub schema: String,
    pub module_id: String,
    pub snapshot_id: String,
    pub activations: Vec<ModuleDatasetActivationV1>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Phase0SourceRefV2 {
    pub module_relative_path: String,
    pub observed_sha256: String,
    pub declared_sha256: String,
    pub hash_current: bool,
    pub rights_receipt_path: String,
    pub rights_receipt_sha256: String,
    pub authorization_overlay_path: String,
    pub authorization_overlay_sha256: String,
    pub authorization_overlay_id: String,
    pub rights_reviewer_key_id: String,
    pub independently_reviewed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Phase0ExcludedSourceV2 {
    pub module_relative_path: String,
    pub observed_sha256: String,
    pub reason: String,
    pub authority_ceiling: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Phase0SourceLockV2 {
    pub schema: String,
    pub module_id: String,
    pub canonical_home: String,
    pub eligible_sources: Vec<Phase0SourceRefV2>,
    pub excluded_sources: Vec<Phase0ExcludedSourceV2>,
    pub inventory_hash: String,
    pub rights_gate_passed: bool,
    pub candidate_supplied_evidence_allowed: bool,
    pub legacy_amphora_receipt_authority: String,
}

impl Phase0SourceLockV2 {
    pub fn bind_inventory_hash(&mut self) {
        self.inventory_hash = stable_hash(&serde_json::json!({
            "eligible_sources": self.eligible_sources,
            "excluded_sources": self.excluded_sources,
        }));
        self.rights_gate_passed = !self.eligible_sources.is_empty()
            && self.eligible_sources.iter().all(|source| {
                source.hash_current
                    && source.observed_sha256 == source.declared_sha256
                    && source.independently_reviewed
                    && is_hash(&source.rights_receipt_sha256)
                    && is_hash(&source.authorization_overlay_sha256)
            });
    }

    pub fn validate(&self) -> Result<(), DataV2Error> {
        if self.schema != PHASE0_SOURCE_LOCK_V2_SCHEMA
            || self.module_id.trim().is_empty()
            || self.canonical_home != format!("{}/evidence/phase0", self.module_id)
            || self.candidate_supplied_evidence_allowed
            || self.legacy_amphora_receipt_authority != "NONE"
        {
            return Err(DataV2Error::InvalidSourceLock);
        }
        let mut paths = BTreeSet::new();
        for source in &self.eligible_sources {
            if !safe_relative(&source.module_relative_path)
                || !safe_relative(&source.rights_receipt_path)
                || !safe_relative(&source.authorization_overlay_path)
                || !is_hash(&source.observed_sha256)
                || !is_hash(&source.declared_sha256)
                || !is_hash(&source.rights_receipt_sha256)
                || !is_hash(&source.authorization_overlay_sha256)
                || !source
                    .authorization_overlay_id
                    .starts_with("authorization-")
                || source.rights_reviewer_key_id.trim().is_empty()
                || !paths.insert(source.module_relative_path.as_str())
            {
                return Err(DataV2Error::InvalidSourceLock);
            }
        }
        for source in &self.excluded_sources {
            if !safe_relative(&source.module_relative_path)
                || !is_hash(&source.observed_sha256)
                || source.reason.trim().is_empty()
                || source.authority_ceiling != "CONTEXT_ONLY"
                || !paths.insert(source.module_relative_path.as_str())
            {
                return Err(DataV2Error::InvalidSourceLock);
            }
        }
        let expected_inventory = stable_hash(&serde_json::json!({
            "eligible_sources": self.eligible_sources,
            "excluded_sources": self.excluded_sources,
        }));
        let expected_rights = !self.eligible_sources.is_empty()
            && self.eligible_sources.iter().all(|source| {
                source.hash_current
                    && source.observed_sha256 == source.declared_sha256
                    && source.independently_reviewed
            });
        if self.inventory_hash != expected_inventory || self.rights_gate_passed != expected_rights {
            return Err(DataV2Error::InvalidSourceLock);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct VerifiedModuleDatasetV1 {
    pub activation: ModuleDatasetActivationV1,
    pub rows: Vec<DerivedRecordV1>,
}

pub fn load_verified_module_dataset(
    module_root: &Path,
    snapshot_id: &str,
    dataset_id: &str,
) -> Result<VerifiedModuleDatasetV1, DataV2Error> {
    let snapshot_channel = canonical_snapshot_channel(snapshot_id)?;
    let reference_root = module_root.join("reference/mvp20");
    let activation_path = reference_root
        .join("data")
        .join(snapshot_channel.replace('-', "_"))
        .join("activation.v1.json");
    let set: ModuleDatasetActivationSetV1 = read_json(&activation_path)?;
    let module_id = module_root
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or(DataV2Error::ActivationIdentity)?;
    if set.schema != ACTIVATION_SET_SCHEMA
        || set.module_id != module_id
        || canonical_snapshot_channel(&set.snapshot_id)? != snapshot_channel
    {
        return Err(DataV2Error::ActivationIdentity);
    }
    let activation = set
        .activations
        .into_iter()
        .find(|row| row.dataset_id == dataset_id)
        .ok_or(DataV2Error::ActivationAbsent)?;
    validate_activation(&activation, module_id, &set.snapshot_id)?;
    for (path, expected_hash) in [
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
        let resolved = confined_file(&reference_root, path)?;
        if file_sha256(&resolved)? != *expected_hash {
            return Err(DataV2Error::HashMismatch(path.clone()));
        }
    }
    let catalog_path = confined_file(&reference_root, &activation.catalog_path)?;
    let catalog: DataCatalogV2 = read_json(&catalog_path)?;
    if catalog.snapshot_id != set.snapshot_id {
        return Err(DataV2Error::ActivationIdentity);
    }
    let workspace_root = module_root
        .parent()
        .ok_or(DataV2Error::ActivationIdentity)?;
    let trust =
        load_rights_trust_store(&workspace_root.join("config/rights-review-trust-store.v1.json"))?;
    verify_activation_authorization(&reference_root, &activation, &catalog, &trust)?;
    let derived = confined_file(&reference_root, &activation.derived_view_path)?;
    let decoder = GzDecoder::new(File::open(derived)?);
    let mut rows = Vec::new();
    for line in BufReader::new(decoder).lines() {
        let row: DerivedRecordV1 = serde_json::from_str(&line?)?;
        if row.schema != DERIVED_RECORD_SCHEMA
            || row.dataset_id != activation.dataset_id
            || row.acquisition_unit_id != activation.acquisition_unit_id
            || row.evidence_class != activation.evidence_class
            || row.rights_class != activation.rights_class
        {
            return Err(DataV2Error::RowBinding);
        }
        rows.push(row);
    }
    if rows.len() as u64 != activation.accepted_row_count {
        return Err(DataV2Error::RowCount);
    }
    Ok(VerifiedModuleDatasetV1 { activation, rows })
}

pub fn verify_activation_authorization(
    reference_root: &Path,
    activation: &ModuleDatasetActivationV1,
    catalog: &DataCatalogV2,
    trust: &LoadedRightsTrust,
) -> Result<ModuleDatasetAuthorizationOverlayV1, DataV2Error> {
    validate_activation(activation, &activation.module_id, &activation.snapshot_id)?;
    let data_directory = Path::new(&activation.catalog_path)
        .parent()
        .filter(|path| safe_relative_path(path))
        .ok_or(DataV2Error::InvalidAuthorizationLedger)?;
    let authorization_directory = data_directory.join("authorizations");
    let ledger_path = authorization_directory.join("ledger.v1.json");
    let ledger: ModuleDatasetAuthorizationLedgerV1 =
        read_json(&confined_file_path(reference_root, &ledger_path)?)?;
    if ledger.schema != AUTHORIZATION_LEDGER_SCHEMA
        || ledger.module_id != activation.module_id
        || ledger.snapshot_id != activation.snapshot_id
        || ledger.overlays.is_empty()
    {
        return Err(DataV2Error::InvalidAuthorizationLedger);
    }

    let events_directory = authorization_directory.join("events");
    let confined_events = reference_root.join(&events_directory);
    let mut actual_event_paths = BTreeSet::new();
    if confined_events.is_dir() {
        for entry in fs::read_dir(&confined_events)? {
            let path = entry?.path();
            if path.extension().and_then(|extension| extension.to_str()) == Some("json") {
                let relative = path
                    .strip_prefix(reference_root)
                    .map_err(|_| DataV2Error::InvalidAuthorizationLedger)?
                    .to_string_lossy()
                    .replace('\\', "/");
                actual_event_paths.insert(relative);
            }
        }
    }

    let mut referenced_event_paths = BTreeSet::new();
    let mut overlay_ids = BTreeSet::new();
    let mut activation_hashes = BTreeSet::new();
    let mut receipt_hashes = BTreeSet::new();
    let mut previous: Option<String> = None;
    let mut target = None;
    let expected_activation_hash = stable_hash(&serde_json::to_value(activation)?);
    for reference in &ledger.overlays {
        if !safe_relative(&reference.path)
            || !is_hash(&reference.sha256)
            || !reference.path.starts_with(&format!(
                "{}/events/",
                authorization_directory.to_string_lossy().replace('\\', "/")
            ))
            || !referenced_event_paths.insert(reference.path.clone())
            || !overlay_ids.insert(reference.overlay_id.clone())
        {
            return Err(DataV2Error::InvalidAuthorizationLedger);
        }
        let path = confined_file(reference_root, &reference.path)?;
        if file_sha256(&path)? != reference.sha256 {
            return Err(DataV2Error::HashMismatch(reference.path.clone()));
        }
        let overlay: ModuleDatasetAuthorizationOverlayV1 = read_json(&path)?;
        overlay.validate()?;
        if overlay.overlay_id != reference.overlay_id
            || overlay.module_id != ledger.module_id
            || overlay.snapshot_id != ledger.snapshot_id
            || overlay.parent_overlay_id != previous
            || !activation_hashes.insert(overlay.activation_hash.clone())
            || !receipt_hashes.insert(overlay.rights_receipt_sha256.clone())
        {
            return Err(DataV2Error::InvalidAuthorizationLedger);
        }
        previous = Some(overlay.overlay_id.clone());
        if overlay.activation_hash == expected_activation_hash
            && overlay.dataset_id == activation.dataset_id
            && overlay.acquisition_unit_id == activation.acquisition_unit_id
        {
            if target.replace(overlay).is_some() {
                return Err(DataV2Error::AuthorizationReplay);
            }
        }
    }
    if previous.as_deref() != Some(ledger.head_overlay_id.as_str())
        || actual_event_paths != referenced_event_paths
    {
        return Err(DataV2Error::InvalidAuthorizationLedger);
    }
    let overlay = target.ok_or(DataV2Error::AuthorizationAbsent)?;
    if overlay.artifact_path != activation.normalized_object_path
        || overlay.artifact_sha256 != activation.normalized_object_sha256
    {
        return Err(DataV2Error::StaleAuthorization);
    }
    let artifact = confined_file(reference_root, &overlay.artifact_path)?;
    if file_sha256(&artifact)? != overlay.artifact_sha256 {
        return Err(DataV2Error::StaleAuthorization);
    }
    let receipt_path = confined_file(reference_root, &overlay.rights_receipt_path)?;
    if file_sha256(&receipt_path)? != overlay.rights_receipt_sha256 {
        return Err(DataV2Error::StaleAuthorization);
    }
    let receipt: RightsReviewReceiptV1 = read_json(&receipt_path)?;
    let decision = catalog
        .rights_decisions
        .iter()
        .find(|decision| {
            decision.rights_decision_id == activation_rights_decision_id(catalog, activation)
        })
        .ok_or(DataV2Error::InvalidRightsReceipt)?;
    let decision_hash = stable_hash(&serde_json::to_value(decision)?);
    if receipt.module_id != activation.module_id
        || receipt.snapshot_id != activation.snapshot_id
        || receipt.dataset_id != activation.dataset_id
        || receipt.acquisition_unit_id != activation.acquisition_unit_id
        || receipt.rights_decision_id != decision.rights_decision_id
        || receipt.rights_decision_hash != decision_hash
        || receipt.artifact_path != overlay.artifact_path
        || receipt.artifact_sha256 != overlay.artifact_sha256
        || receipt.rights_class != activation.rights_class
        || receipt.license != decision.license
        || receipt.reviewer_key_id != overlay.rights_reviewer_key_id
    {
        return Err(DataV2Error::StaleAuthorization);
    }
    receipt.verify_signature(trust)?;
    Ok(overlay)
}

fn activation_rights_decision_id<'a>(
    catalog: &'a DataCatalogV2,
    activation: &ModuleDatasetActivationV1,
) -> &'a str {
    catalog
        .acquisition_units
        .iter()
        .find(|unit| unit.acquisition_unit_id == activation.acquisition_unit_id)
        .map(|unit| unit.rights_decision_id.as_str())
        .unwrap_or("")
}

fn canonical_snapshot_channel(value: &str) -> Result<String, DataV2Error> {
    let normalized = value.replace('/', "-").replace('_', "-");
    if normalized == "feedback-v2" || normalized.starts_with("feedback-v2-") {
        Ok("feedback-v2".into())
    } else if normalized == "feedback-v3" || normalized.starts_with("feedback-v3-") {
        Ok("feedback-v3".into())
    } else if normalized == "feedback-v4" || normalized.starts_with("feedback-v4-") {
        Ok("feedback-v4".into())
    } else {
        Err(DataV2Error::ActivationIdentity)
    }
}

fn valid_snapshot_id(value: &str) -> bool {
    canonical_snapshot_channel(value).is_ok()
}

fn validate_activation(
    row: &ModuleDatasetActivationV1,
    module_id: &str,
    snapshot_id: &str,
) -> Result<(), DataV2Error> {
    if row.schema != ACTIVATION_SCHEMA
        || row.module_id != module_id
        || row.snapshot_id != snapshot_id
        || row.dataset_id.trim().is_empty()
        || row.scoring
        || row.authority_limit.trim().is_empty()
        || authority_limit_escalates(&row.authority_limit)
        || !row.zero_network
        || !row.candidate_input_excluded
        || row.rights_class != RightsClass::DerivativeAllowed
        || row.quarantined_row_count != 0
        || row.claim_locks.get("no_ranking_authority") != Some(&true)
        || row.claim_locks.get("no_optimizer_authority") != Some(&true)
        || row.claim_locks.values().any(|enabled| !enabled)
    {
        return Err(DataV2Error::ActivationPolicy);
    }
    Ok(())
}

fn authority_limit_escalates(value: &str) -> bool {
    matches!(
        value.trim().to_ascii_uppercase().as_str(),
        "RANKING"
            | "OPTIMIZER"
            | "OBJECTIVE"
            | "RELEASE"
            | "PROCUREMENT"
            | "REGULATORY"
            | "SAFETY"
            | "PATENTABILITY"
            | "FTO"
            | "PRODUCT_PERFORMANCE"
    )
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T, DataV2Error> {
    let bytes = fs::read(path)?;
    Ok(serde_json::from_slice(&bytes)?)
}

fn confined_file(root: &Path, relative: &str) -> Result<PathBuf, DataV2Error> {
    if !safe_relative(relative) {
        return Err(DataV2Error::PathEscape(relative.into()));
    }
    let canonical_root = root.canonicalize()?;
    let candidate = root.join(relative).canonicalize()?;
    if !candidate.starts_with(&canonical_root) || !candidate.is_file() {
        return Err(DataV2Error::PathEscape(relative.into()));
    }
    Ok(candidate)
}

fn confined_file_path(root: &Path, relative: &Path) -> Result<PathBuf, DataV2Error> {
    let value = relative
        .to_str()
        .ok_or_else(|| DataV2Error::PathEscape(relative.display().to_string()))?;
    confined_file(root, value)
}

fn safe_relative(value: &str) -> bool {
    let path = Path::new(value);
    !value.is_empty()
        && !path.is_absolute()
        && path
            .components()
            .all(|part| matches!(part, Component::Normal(_)))
}

fn safe_relative_path(path: &Path) -> bool {
    !path.as_os_str().is_empty()
        && !path.is_absolute()
        && path
            .components()
            .all(|part| matches!(part, Component::Normal(_)))
}

fn is_hash(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn file_sha256(path: &Path) -> Result<String, DataV2Error> {
    let mut reader = BufReader::new(File::open(path)?);
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

fn sha256_bytes(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn decode_hex_32(value: &str) -> Result<[u8; 32], DataV2Error> {
    if value.len() != 64 {
        return Err(DataV2Error::InvalidRightsTrustStore);
    }
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text = std::str::from_utf8(chunk).map_err(|_| DataV2Error::InvalidRightsTrustStore)?;
        if text
            .bytes()
            .any(|byte| !(byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)))
        {
            return Err(DataV2Error::InvalidRightsTrustStore);
        }
        output[index] =
            u8::from_str_radix(text, 16).map_err(|_| DataV2Error::InvalidRightsTrustStore)?;
    }
    Ok(output)
}

#[derive(Debug, Error)]
pub enum DataV2Error {
    #[error("module activation identity is invalid")]
    ActivationIdentity,
    #[error("requested module dataset activation is absent")]
    ActivationAbsent,
    #[error(
        "module activation violates audit-only, rights, quarantine, or candidate-input policy"
    )]
    ActivationPolicy,
    #[error("module activation artifact path escapes reference/mvp20: {0}")]
    PathEscape(String),
    #[error("module activation artifact hash mismatch: {0}")]
    HashMismatch(String),
    #[error("derived row does not match its activation")]
    RowBinding,
    #[error("derived row count does not match its activation")]
    RowCount,
    #[error("Phase-0 source-lock v2 is invalid")]
    InvalidSourceLock,
    #[error("rights-review receipt is malformed or exceeds audit-only authority")]
    InvalidRightsReceipt,
    #[error("rights-review receipt is unsigned")]
    UnsignedRightsReceipt,
    #[error("rights-review receipt signature is invalid or not payload-bound")]
    InvalidRightsSignature,
    #[error("rights-review signing identity has the wrong role")]
    RightsRole,
    #[error("rights-review trust store is invalid, development-only, or has no active reviewer")]
    InvalidRightsTrustStore,
    #[error("module activation authorization overlay is invalid")]
    InvalidAuthorizationOverlay,
    #[error("module activation authorization ledger is invalid or has multiple heads")]
    InvalidAuthorizationLedger,
    #[error("module activation has no cryptographic authorization overlay")]
    AuthorizationAbsent,
    #[error("rights receipt or authorization overlay was replayed")]
    AuthorizationReplay,
    #[error("module activation authorization is stale or bound to another artifact")]
    StaleAuthorization,
    #[error(transparent)]
    Verification(#[from] crate::VerificationError),
    #[error(transparent)]
    Io(#[from] std::io::Error),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
}

#[cfg(test)]
mod tests {
    use super::*;

    fn activation() -> ModuleDatasetActivationV1 {
        ModuleDatasetActivationV1 {
            schema: ACTIVATION_SCHEMA.into(),
            module_id: "amphora-example".into(),
            snapshot_id: "feedback-v2".into(),
            dataset_id: "dataset-hash".into(),
            acquisition_unit_id: "dataset".into(),
            catalog_path: "data/feedback_v2/catalog.json".into(),
            catalog_sha256: "a".repeat(64),
            acquisition_receipt_path: "manifests/dataset.acquisition-receipt.json".into(),
            acquisition_receipt_sha256: "b".repeat(64),
            rights_receipt_path: "data/feedback_v2/rights/rights.json".into(),
            rights_receipt_sha256: "c".repeat(64),
            rights_reviewed: true,
            dataset_manifest_path: "manifests/dataset.json".into(),
            dataset_manifest_sha256: "d".repeat(64),
            normalized_object_path: "data/feedback_v2/objects/hash.jsonl.gz".into(),
            normalized_object_sha256: "e".repeat(64),
            derived_view_path: "data/feedback_v2/derived/dataset.jsonl.gz".into(),
            derived_view_sha256: "f".repeat(64),
            split_path: "data/feedback_v2/splits/dataset.json".into(),
            split_sha256: "1".repeat(64),
            accepted_row_count: 1,
            rejected_row_count: 0,
            excluded_row_count: 0,
            quarantined_row_count: 0,
            evidence_class: EvidenceClass::ExternalMeasured,
            rights_class: RightsClass::DerivativeAllowed,
            consumer: ConsumerKind::OfflineBenchmark,
            scoring: false,
            authority_limit: "AUDIT_ONLY".into(),
            claim_locks: BTreeMap::from([
                ("no_ranking_authority".into(), true),
                ("no_optimizer_authority".into(), true),
            ]),
            generator_version: "1".into(),
            deterministic_command: "data consume".into(),
            zero_network: true,
            candidate_input_excluded: true,
        }
    }

    #[test]
    fn excluded_source_cannot_satisfy_rights_gate() {
        let mut lock = Phase0SourceLockV2 {
            schema: PHASE0_SOURCE_LOCK_V2_SCHEMA.into(),
            module_id: "amphora-example".into(),
            canonical_home: "amphora-example/evidence/phase0".into(),
            eligible_sources: Vec::new(),
            excluded_sources: vec![Phase0ExcludedSourceV2 {
                module_relative_path: "reference/context.json".into(),
                observed_sha256: "a".repeat(64),
                reason: "CONTEXT_ONLY_RIGHTS".into(),
                authority_ceiling: "CONTEXT_ONLY".into(),
            }],
            inventory_hash: String::new(),
            rights_gate_passed: true,
            candidate_supplied_evidence_allowed: false,
            legacy_amphora_receipt_authority: "NONE".into(),
        };
        lock.bind_inventory_hash();
        assert!(!lock.rights_gate_passed);
        assert!(lock.validate().is_ok());
    }

    #[test]
    fn relabeling_excluded_source_requires_independent_rights_receipt() {
        let mut lock = Phase0SourceLockV2 {
            schema: PHASE0_SOURCE_LOCK_V2_SCHEMA.into(),
            module_id: "amphora-example".into(),
            canonical_home: "amphora-example/evidence/phase0".into(),
            eligible_sources: vec![Phase0SourceRefV2 {
                module_relative_path: "reference/data.json".into(),
                observed_sha256: "a".repeat(64),
                declared_sha256: "a".repeat(64),
                hash_current: true,
                rights_receipt_path: "reference/rights.json".into(),
                rights_receipt_sha256: "b".repeat(64),
                authorization_overlay_path: "reference/authorization.json".into(),
                authorization_overlay_sha256: "c".repeat(64),
                authorization_overlay_id: format!("authorization-{}", "d".repeat(64)),
                rights_reviewer_key_id: format!("rights-reviewer-{}", "e".repeat(64)),
                independently_reviewed: false,
            }],
            excluded_sources: Vec::new(),
            inventory_hash: String::new(),
            rights_gate_passed: true,
            candidate_supplied_evidence_allowed: false,
            legacy_amphora_receipt_authority: "NONE".into(),
        };
        lock.bind_inventory_hash();
        assert!(!lock.rights_gate_passed);
        assert!(lock.validate().is_ok());
    }

    #[test]
    fn loader_policy_rejects_quarantine_scoring_and_authority_escalation() {
        let mut row = activation();
        assert!(validate_activation(&row, "amphora-example", "feedback-v2").is_ok());
        row.quarantined_row_count = 1;
        assert!(validate_activation(&row, "amphora-example", "feedback-v2").is_err());
        row.quarantined_row_count = 0;
        row.scoring = true;
        assert!(validate_activation(&row, "amphora-example", "feedback-v2").is_err());
        row.scoring = false;
        row.authority_limit = "RANKING".into();
        assert!(validate_activation(&row, "amphora-example", "feedback-v2").is_err());
    }

    fn rights_receipt(key_id: &str, key: &SigningKey) -> RightsReviewReceiptV1 {
        let mut receipt = RightsReviewReceiptV1 {
            schema: RIGHTS_REVIEW_RECEIPT_SCHEMA.into(),
            receipt_id: String::new(),
            module_id: "amphora-example".into(),
            snapshot_id: "feedback-v3".into(),
            dataset_id: "dataset-hash".into(),
            acquisition_unit_id: "dataset".into(),
            rights_decision_id: "rights-dataset".into(),
            rights_decision_hash: "a".repeat(64),
            artifact_path: "data/feedback_v3/objects/data.jsonl.gz".into(),
            artifact_sha256: "b".repeat(64),
            rights_class: RightsClass::DerivativeAllowed,
            license: "CC-BY-4.0".into(),
            accepted: true,
            authority_ceiling: "AUDIT_ONLY".into(),
            exclusions: REQUIRED_RIGHTS_EXCLUSIONS.map(str::to_owned).to_vec(),
            reviewer_key_id: key_id.into(),
            signature: None,
        };
        receipt.bind_receipt_id().unwrap();
        receipt.sign(key_id, key).unwrap();
        receipt
    }

    fn rights_trust(key_id: &str, key: &SigningKey) -> LoadedRightsTrust {
        let mut trust = TrustStore::default();
        trust
            .insert(key_id, key.verifying_key().to_bytes())
            .unwrap();
        LoadedRightsTrust {
            trust,
            roles: BTreeMap::from([(key_id.into(), "RIGHTS_REVIEWER".into())]),
        }
    }

    #[test]
    fn rights_receipt_rejects_forgery_revocation_wrong_role_and_stripped_exclusions() {
        let key = SigningKey::from_bytes(&[41; 32]);
        let key_id = format!(
            "rights-reviewer-{}",
            sha256_bytes(&key.verifying_key().to_bytes())
        );
        let receipt = rights_receipt(&key_id, &key);
        let trust = rights_trust(&key_id, &key);
        assert_eq!(receipt.verify_signature(&trust).unwrap(), key_id);

        let mut forged = receipt.clone();
        forged.artifact_sha256 = "c".repeat(64);
        assert!(forged.verify_signature(&trust).is_err());

        let mut cross_module = receipt.clone();
        cross_module.module_id = "amphora-other".into();
        assert!(cross_module.verify_signature(&trust).is_err());

        let mut stripped = receipt.clone();
        stripped.exclusions.pop();
        stripped.bind_receipt_id().unwrap();
        assert!(matches!(
            stripped.validate(),
            Err(DataV2Error::InvalidRightsReceipt)
        ));

        let mut wrong_role = rights_trust(&key_id, &key);
        wrong_role
            .roles
            .insert(key_id.clone(), "PHASE0_EVALUATOR".into());
        assert!(matches!(
            receipt.verify_signature(&wrong_role),
            Err(DataV2Error::RightsRole)
        ));

        let mut revoked = rights_trust(&key_id, &key);
        revoked.trust.revoke(key_id.clone());
        assert!(receipt.verify_signature(&revoked).is_err());
    }

    #[test]
    fn rights_trust_store_rejects_development_identity() {
        let key = SigningKey::from_bytes(&[42; 32]);
        let public_key = key.verifying_key().to_bytes();
        let key_id = format!("rights-reviewer-{}", sha256_bytes(&public_key));
        let directory =
            std::env::temp_dir().join(format!("amphora-rights-trust-test-{}", std::process::id()));
        fs::create_dir_all(&directory).unwrap();
        let path = directory.join("trust.json");
        fs::write(
            &path,
            serde_json::to_vec(&serde_json::json!({
                "schema": RIGHTS_TRUST_STORE_SCHEMA,
                "authorization_status": "AUTHORIZED_RIGHTS_REVIEW_IDENTITIES",
                "keys": [{
                    "key_id": key_id,
                    "algorithm": "Ed25519",
                    "role": "RIGHTS_REVIEWER",
                    "public_key_hex": public_key.iter().map(|byte| format!("{byte:02x}")).collect::<String>(),
                    "rights_review_authorized": true,
                    "development": true,
                    "revoked": false
                }]
            }))
            .unwrap(),
        )
        .unwrap();
        assert!(matches!(
            load_rights_trust_store(&path),
            Err(DataV2Error::InvalidRightsTrustStore)
        ));
        fs::remove_file(path).unwrap();
        fs::remove_dir(directory).unwrap();
    }

    #[test]
    fn candidate_supplied_paths_cannot_escape_reference_root() {
        assert!(!safe_relative("../candidate/result.json"));
        assert!(!safe_relative("/tmp/candidate/result.json"));
        assert!(safe_relative("data/feedback_v2/derived/dataset.jsonl.gz"));
    }
}
