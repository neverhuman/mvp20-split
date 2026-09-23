use crate::{canonicalize, sign_dsse, verify_dsse, DsseEnvelope, TrustStore, VerificationError};
use ed25519_dalek::SigningKey;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

pub const DATASET_MANIFEST_SCHEMA: &str = "amphora.dataset-manifest.v1";
pub const SPLIT_MANIFEST_SCHEMA: &str = "amphora.split-manifest.v1";
pub const BENCHMARK_LOCK_SCHEMA: &str = "amphora.benchmark-lock.v1";
pub const MODEL_ARTIFACT_SCHEMA: &str = "amphora.model-artifact.v1";
pub const SIGNED_MODEL_ARTIFACT_SCHEMA: &str = "amphora.signed-model-artifact.v1";
pub const EVALUATION_RECEIPT_SCHEMA: &str = "amphora.evaluation-receipt.v1";
pub const PROMOTION_POLICY_SCHEMA: &str = "amphora.promotion-policy.v1";
pub const EVALUATION_RECEIPT_PAYLOAD_TYPE: &str =
    "application/vnd.amphora.evaluation-receipt.v1+json";
pub const MODEL_ARTIFACT_PAYLOAD_TYPE: &str =
    "application/vnd.amphora.signed-model-artifact.v1+json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EvidenceTier {
    SyntheticDiagnostic,
    PublicRetrospective,
    IndependentExternal,
    ProspectiveReplicated,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DecisionUse {
    AuditOnly,
    Shadow,
    ConstraintOnly,
    Ranking,
}

impl DecisionUse {
    fn privilege(self) -> u8 {
        match self {
            Self::AuditOnly => 0,
            Self::Shadow => 1,
            Self::ConstraintOnly => 2,
            Self::Ranking => 3,
        }
    }

    pub fn minimum(self, other: Self) -> Self {
        if self.privilege() <= other.privilege() {
            self
        } else {
            other
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct RightsRecordV1 {
    pub source_id: String,
    pub license: String,
    pub status: String,
    pub source_url: String,
    #[serde(default)]
    pub restrictions: Vec<String>,
    pub eligible_for_derivatives: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct RowProvenanceV1 {
    pub row_id: String,
    pub source_id: String,
    pub raw_artifact: String,
    pub source_row: u64,
    #[serde(default)]
    pub transformations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct DatasetManifestV1 {
    pub schema: String,
    pub dataset_id: String,
    pub raw_hashes: BTreeMap<String, String>,
    pub rights: Vec<RightsRecordV1>,
    #[serde(default)]
    pub row_provenance: Vec<RowProvenanceV1>,
    #[serde(default)]
    pub units: BTreeMap<String, String>,
    #[serde(default)]
    pub methods: Vec<String>,
    #[serde(default)]
    pub conditions: BTreeMap<String, String>,
    pub builder_hash: String,
    pub schema_hash: String,
    pub row_count: u64,
}

impl DatasetManifestV1 {
    pub fn validate(&self) -> Result<(), ArtifactError> {
        require_schema(&self.schema, DATASET_MANIFEST_SCHEMA)?;
        require_id("dataset_id", &self.dataset_id)?;
        require_hash("builder_hash", &self.builder_hash)?;
        require_hash("schema_hash", &self.schema_hash)?;
        require_hash_map("raw_hashes", &self.raw_hashes)?;
        if self.raw_hashes.is_empty() {
            return Err(ArtifactError::Empty("raw_hashes"));
        }
        let rights: BTreeMap<_, _> = self
            .rights
            .iter()
            .map(|row| (row.source_id.as_str(), row))
            .collect();
        if rights.len() != self.rights.len() {
            return Err(ArtifactError::Duplicate("rights.source_id"));
        }
        for row in &self.rights {
            require_id("rights.source_id", &row.source_id)?;
            require_id("rights.status", &row.status)?;
            if row.eligible_for_derivatives
                && (row.license.trim().is_empty() || row.source_url.trim().is_empty())
            {
                return Err(ArtifactError::Rights(row.source_id.clone()));
            }
        }
        for row in &self.row_provenance {
            require_id("row_provenance.row_id", &row.row_id)?;
            if !rights
                .get(row.source_id.as_str())
                .is_some_and(|rights| rights.eligible_for_derivatives)
            {
                return Err(ArtifactError::Rights(row.source_id.clone()));
            }
            if !self.raw_hashes.contains_key(&row.raw_artifact) {
                return Err(ArtifactError::UnknownParent(row.raw_artifact.clone()));
            }
        }
        if !self.row_provenance.is_empty() && self.row_count != self.row_provenance.len() as u64 {
            return Err(ArtifactError::Count {
                declared: self.row_count,
                observed: self.row_provenance.len() as u64,
            });
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SplitAssignmentV1 {
    pub row_id: String,
    pub split: String,
    pub source: String,
    pub family: String,
    pub scaffold: String,
    pub time: String,
    pub lot: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SplitManifestV1 {
    pub schema: String,
    pub split_id: String,
    pub dataset_hash: String,
    pub assignment_method: String,
    pub assignments: Vec<SplitAssignmentV1>,
}

impl SplitManifestV1 {
    pub fn validate(&self) -> Result<(), ArtifactError> {
        require_schema(&self.schema, SPLIT_MANIFEST_SCHEMA)?;
        require_id("split_id", &self.split_id)?;
        require_hash("dataset_hash", &self.dataset_hash)?;
        require_id("assignment_method", &self.assignment_method)?;
        let mut rows = BTreeSet::new();
        for row in &self.assignments {
            require_id("assignments.row_id", &row.row_id)?;
            require_id("assignments.split", &row.split)?;
            if !rows.insert(&row.row_id) {
                return Err(ArtifactError::Duplicate("assignments.row_id"));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct MetricLockV1 {
    pub metric: String,
    pub direction: String,
    pub unit: String,
    pub threshold: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct BenchmarkLockV1 {
    pub schema: String,
    pub benchmark_id: String,
    pub module_id: String,
    pub endpoints: Vec<String>,
    pub baselines: Vec<String>,
    pub metrics: Vec<MetricLockV1>,
    pub uncertainty_method: String,
    pub thresholds: BTreeMap<String, f64>,
    #[serde(default)]
    pub exclusions: Vec<String>,
    pub dataset_hashes: BTreeMap<String, String>,
    pub split_hash: String,
}

impl BenchmarkLockV1 {
    pub fn validate(&self) -> Result<(), ArtifactError> {
        require_schema(&self.schema, BENCHMARK_LOCK_SCHEMA)?;
        require_id("benchmark_id", &self.benchmark_id)?;
        require_id("module_id", &self.module_id)?;
        require_nonempty("endpoints", &self.endpoints)?;
        require_nonempty("baselines", &self.baselines)?;
        if self.metrics.is_empty() {
            return Err(ArtifactError::Empty("metrics"));
        }
        for metric in &self.metrics {
            require_id("metrics.metric", &metric.metric)?;
            require_id("metrics.direction", &metric.direction)?;
            require_id("metrics.unit", &metric.unit)?;
            if metric.threshold.is_some_and(|value| !value.is_finite()) {
                return Err(ArtifactError::NonFinite("metrics.threshold"));
            }
        }
        if self.thresholds.values().any(|value| !value.is_finite()) {
            return Err(ArtifactError::NonFinite("thresholds"));
        }
        require_hash_map("dataset_hashes", &self.dataset_hashes)?;
        require_hash("split_hash", &self.split_hash)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ModelArtifactV1 {
    pub schema: String,
    pub model_id: String,
    pub feature_order: Vec<String>,
    pub transformations: Vec<String>,
    pub coefficients: Vec<f64>,
    #[serde(default)]
    pub calibration: BTreeMap<String, f64>,
    pub applicability_domain: Value,
    pub parent_hashes: BTreeMap<String, String>,
}

impl ModelArtifactV1 {
    pub fn validate(&self) -> Result<(), ArtifactError> {
        require_schema(&self.schema, MODEL_ARTIFACT_SCHEMA)?;
        require_id("model_id", &self.model_id)?;
        if self.feature_order.is_empty() {
            return Err(ArtifactError::Empty("feature_order"));
        }
        if self.feature_order.len() != self.coefficients.len() {
            return Err(ArtifactError::DimensionMismatch);
        }
        if self.coefficients.iter().any(|value| !value.is_finite())
            || self.calibration.values().any(|value| !value.is_finite())
        {
            return Err(ArtifactError::NonFinite("model parameters"));
        }
        require_hash_map("parent_hashes", &self.parent_hashes)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SignedModelArtifactV1 {
    pub schema: String,
    pub module_id: String,
    pub artifact_sha256: String,
    pub artifact: Value,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<DsseEnvelope>,
}

impl SignedModelArtifactV1 {
    pub fn validate(&self) -> Result<(), ArtifactError> {
        require_schema(&self.schema, SIGNED_MODEL_ARTIFACT_SCHEMA)?;
        require_id("module_id", &self.module_id)?;
        require_hash("artifact_sha256", &self.artifact_sha256)?;
        if crate::stable_hash(&self.artifact) != self.artifact_sha256
            || self.artifact.get("module_id").and_then(Value::as_str)
                != Some(self.module_id.as_str())
        {
            return Err(ArtifactError::SignaturePayload);
        }
        Ok(())
    }

    fn unsigned_bytes(&self) -> Result<Vec<u8>, ArtifactError> {
        let mut unsigned = self.clone();
        unsigned.signature = None;
        Ok(serde_json::to_vec(&canonicalize(&serde_json::to_value(
            unsigned,
        )?))?)
    }

    pub fn sign(&mut self, key_id: &str, key: &SigningKey) -> Result<(), ArtifactError> {
        self.validate()?;
        self.signature = Some(sign_dsse(
            MODEL_ARTIFACT_PAYLOAD_TYPE,
            &self.unsigned_bytes()?,
            key_id,
            key,
        ));
        Ok(())
    }

    pub fn verify_signature(&self, trust_store: &TrustStore) -> Result<String, ArtifactError> {
        self.validate()?;
        let envelope = self.signature.as_ref().ok_or(ArtifactError::Unsigned)?;
        if envelope.payload_type != MODEL_ARTIFACT_PAYLOAD_TYPE {
            return Err(ArtifactError::SignaturePayload);
        }
        let verified = verify_dsse(envelope, trust_store)?;
        if verified.payload != self.unsigned_bytes()? {
            return Err(ArtifactError::SignaturePayload);
        }
        Ok(verified.key_id)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ConfidenceIntervalV1 {
    pub lower: f64,
    pub upper: f64,
    pub confidence: f64,
    pub method: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EvaluationReceiptV1 {
    pub schema: String,
    pub receipt_id: String,
    pub module_id: String,
    pub registry_manifest_hash: String,
    pub registry_owned_identity: bool,
    pub artifact_hashes: BTreeMap<String, String>,
    pub benchmark_lock_hash: String,
    pub metrics: BTreeMap<String, Value>,
    #[serde(default)]
    pub confidence_intervals: BTreeMap<String, ConfidenceIntervalV1>,
    pub evidence_tier: EvidenceTier,
    pub decision_use_ceiling: DecisionUse,
    pub passed: bool,
    pub claim_locks: BTreeMap<String, bool>,
    #[serde(default)]
    pub applicability_limits: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<DsseEnvelope>,
}

impl EvaluationReceiptV1 {
    pub fn validate(&self) -> Result<(), ArtifactError> {
        require_schema(&self.schema, EVALUATION_RECEIPT_SCHEMA)?;
        require_id("receipt_id", &self.receipt_id)?;
        require_id("module_id", &self.module_id)?;
        if !self.registry_owned_identity {
            return Err(ArtifactError::SelfGrantedIdentity);
        }
        require_hash("registry_manifest_hash", &self.registry_manifest_hash)?;
        require_hash("benchmark_lock_hash", &self.benchmark_lock_hash)?;
        require_hash_map("artifact_hashes", &self.artifact_hashes)?;
        for interval in self.confidence_intervals.values() {
            if !interval.lower.is_finite()
                || !interval.upper.is_finite()
                || !interval.confidence.is_finite()
                || interval.lower > interval.upper
                || !(0.0..=1.0).contains(&interval.confidence)
            {
                return Err(ArtifactError::InvalidInterval);
            }
        }
        if self.passed && self.claim_locks.is_empty() {
            return Err(ArtifactError::Empty("claim_locks"));
        }
        if matches!(
            self.evidence_tier,
            EvidenceTier::SyntheticDiagnostic | EvidenceTier::PublicRetrospective
        ) && self.decision_use_ceiling == DecisionUse::Ranking
        {
            return Err(ArtifactError::EvidenceCeiling);
        }
        Ok(())
    }

    fn unsigned_bytes(&self) -> Result<Vec<u8>, ArtifactError> {
        let mut unsigned = self.clone();
        unsigned.signature = None;
        let value = serde_json::to_value(unsigned)?;
        Ok(serde_json::to_vec(&canonicalize(&value))?)
    }

    pub fn sign(&mut self, key_id: &str, key: &SigningKey) -> Result<(), ArtifactError> {
        self.validate()?;
        self.signature = Some(sign_dsse(
            EVALUATION_RECEIPT_PAYLOAD_TYPE,
            &self.unsigned_bytes()?,
            key_id,
            key,
        ));
        Ok(())
    }

    pub fn verify_signature(&self, trust_store: &TrustStore) -> Result<String, ArtifactError> {
        self.validate()?;
        let envelope = self.signature.as_ref().ok_or(ArtifactError::Unsigned)?;
        if envelope.payload_type != EVALUATION_RECEIPT_PAYLOAD_TYPE {
            return Err(ArtifactError::SignaturePayload);
        }
        let verified = verify_dsse(envelope, trust_store)?;
        if verified.payload != self.unsigned_bytes()? {
            return Err(ArtifactError::SignaturePayload);
        }
        Ok(verified.key_id)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct PromotionRuleV1 {
    pub module_id: String,
    pub receipt_hash: String,
    pub maximum_use: DecisionUse,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct PromotionPolicyV1 {
    pub schema: String,
    pub policy_id: String,
    pub registry_manifest_hash: String,
    pub default_use: DecisionUse,
    pub rules: Vec<PromotionRuleV1>,
}

impl PromotionPolicyV1 {
    pub fn validate(&self) -> Result<(), ArtifactError> {
        require_schema(&self.schema, PROMOTION_POLICY_SCHEMA)?;
        require_id("policy_id", &self.policy_id)?;
        require_hash("registry_manifest_hash", &self.registry_manifest_hash)?;
        let mut modules = BTreeSet::new();
        for rule in &self.rules {
            require_id("rules.module_id", &rule.module_id)?;
            require_hash("rules.receipt_hash", &rule.receipt_hash)?;
            if !modules.insert(&rule.module_id) {
                return Err(ArtifactError::Duplicate("rules.module_id"));
            }
        }
        Ok(())
    }

    pub fn authority_for(
        &self,
        receipt: &EvaluationReceiptV1,
        receipt_hash: &str,
    ) -> Result<DecisionUse, ArtifactError> {
        self.validate()?;
        receipt.validate()?;
        require_hash("receipt_hash", receipt_hash)?;
        if receipt.registry_manifest_hash != self.registry_manifest_hash {
            return Err(ArtifactError::RegistryMismatch);
        }
        let policy_ceiling = self
            .rules
            .iter()
            .find(|rule| rule.module_id == receipt.module_id && rule.receipt_hash == receipt_hash)
            .map_or(self.default_use, |rule| rule.maximum_use);
        if !receipt.passed {
            return Ok(DecisionUse::AuditOnly);
        }
        Ok(policy_ceiling.minimum(receipt.decision_use_ceiling))
    }
}

#[derive(Debug, Error)]
pub enum ArtifactError {
    #[error("unexpected schema {actual}; expected {expected}")]
    Schema {
        actual: String,
        expected: &'static str,
    },
    #[error("{0} must not be empty")]
    Empty(&'static str),
    #[error("{0} is not a lowercase SHA-256 digest")]
    Hash(String),
    #[error("duplicate value in {0}")]
    Duplicate(&'static str),
    #[error("source {0} is not eligible for derived use")]
    Rights(String),
    #[error("unknown parent artifact {0}")]
    UnknownParent(String),
    #[error("declared row count {declared} does not equal observed provenance rows {observed}")]
    Count { declared: u64, observed: u64 },
    #[error("model feature and coefficient dimensions differ")]
    DimensionMismatch,
    #[error("{0} contains a non-finite value")]
    NonFinite(&'static str),
    #[error("confidence interval is invalid")]
    InvalidInterval,
    #[error("receipt module identity was not assigned by the registry")]
    SelfGrantedIdentity,
    #[error("evidence tier cannot grant the requested decision use")]
    EvidenceCeiling,
    #[error("evaluation receipt is unsigned")]
    Unsigned,
    #[error("evaluation receipt signature payload is not bound to the receipt")]
    SignaturePayload,
    #[error("receipt and promotion policy registry hashes differ")]
    RegistryMismatch,
    #[error("artifact JSON: {0}")]
    Json(#[from] serde_json::Error),
    #[error("artifact signature: {0}")]
    Signature(#[from] VerificationError),
}

fn require_schema(actual: &str, expected: &'static str) -> Result<(), ArtifactError> {
    if actual == expected {
        Ok(())
    } else {
        Err(ArtifactError::Schema {
            actual: actual.to_owned(),
            expected,
        })
    }
}

fn require_id(field: &'static str, value: &str) -> Result<(), ArtifactError> {
    if value.trim().is_empty() {
        Err(ArtifactError::Empty(field))
    } else {
        Ok(())
    }
}

fn require_nonempty(field: &'static str, values: &[String]) -> Result<(), ArtifactError> {
    if values.is_empty() || values.iter().any(|value| value.trim().is_empty()) {
        Err(ArtifactError::Empty(field))
    } else {
        Ok(())
    }
}

fn require_hash(field: &str, value: &str) -> Result<(), ArtifactError> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(ArtifactError::Hash(field.to_owned()))
    }
}

fn require_hash_map(
    field: &'static str,
    values: &BTreeMap<String, String>,
) -> Result<(), ArtifactError> {
    for (name, hash) in values {
        require_id(field, name)?;
        require_hash(field, hash)?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::stable_hash;

    fn digest(label: &str) -> String {
        stable_hash(&Value::String(label.into()))
    }

    fn receipt(tier: EvidenceTier, use_ceiling: DecisionUse) -> EvaluationReceiptV1 {
        EvaluationReceiptV1 {
            schema: EVALUATION_RECEIPT_SCHEMA.into(),
            receipt_id: "receipt-1".into(),
            module_id: "module-1".into(),
            registry_manifest_hash: digest("registry"),
            registry_owned_identity: true,
            artifact_hashes: BTreeMap::from([("data".into(), digest("data"))]),
            benchmark_lock_hash: digest("lock"),
            metrics: BTreeMap::new(),
            confidence_intervals: BTreeMap::new(),
            evidence_tier: tier,
            decision_use_ceiling: use_ceiling,
            passed: true,
            claim_locks: BTreeMap::from([("no_product_claim".into(), true)]),
            applicability_limits: vec!["test only".into()],
            signature: None,
        }
    }

    #[test]
    fn public_receipt_cannot_grant_ranking() {
        let row = receipt(EvidenceTier::PublicRetrospective, DecisionUse::Ranking);
        assert!(matches!(
            row.validate(),
            Err(ArtifactError::EvidenceCeiling)
        ));
    }

    #[test]
    fn rights_quarantine_blocks_row_provenance() {
        let manifest = DatasetManifestV1 {
            schema: DATASET_MANIFEST_SCHEMA.into(),
            dataset_id: "dataset-1".into(),
            raw_hashes: BTreeMap::from([("raw.csv".into(), digest("raw"))]),
            rights: vec![RightsRecordV1 {
                source_id: "restricted".into(),
                license: "unknown".into(),
                status: "QUARANTINED".into(),
                source_url: "https://example.invalid".into(),
                restrictions: Vec::new(),
                eligible_for_derivatives: false,
            }],
            row_provenance: vec![RowProvenanceV1 {
                row_id: "1".into(),
                source_id: "restricted".into(),
                raw_artifact: "raw.csv".into(),
                source_row: 1,
                transformations: Vec::new(),
            }],
            units: BTreeMap::new(),
            methods: vec!["test".into()],
            conditions: BTreeMap::new(),
            builder_hash: digest("builder"),
            schema_hash: digest("schema"),
            row_count: 1,
        };
        assert!(matches!(manifest.validate(), Err(ArtifactError::Rights(_))));
    }

    #[test]
    fn receipt_signature_is_bound_and_policy_only_reduces_privilege() {
        let signing = SigningKey::from_bytes(&[17; 32]);
        let mut row = receipt(EvidenceTier::IndependentExternal, DecisionUse::Ranking);
        row.sign("test-key", &signing).unwrap();
        let mut trust = TrustStore::default();
        trust
            .insert("test-key", signing.verifying_key().to_bytes())
            .unwrap();
        assert_eq!(row.verify_signature(&trust).unwrap(), "test-key");

        let receipt_hash = stable_hash(&serde_json::to_value(&row).unwrap());
        let policy = PromotionPolicyV1 {
            schema: PROMOTION_POLICY_SCHEMA.into(),
            policy_id: "policy-1".into(),
            registry_manifest_hash: row.registry_manifest_hash.clone(),
            default_use: DecisionUse::AuditOnly,
            rules: vec![PromotionRuleV1 {
                module_id: row.module_id.clone(),
                receipt_hash: receipt_hash.clone(),
                maximum_use: DecisionUse::Shadow,
            }],
        };
        assert_eq!(
            policy.authority_for(&row, &receipt_hash).unwrap(),
            DecisionUse::Shadow
        );
    }

    #[test]
    fn signed_model_artifact_binds_module_and_payload_bytes() {
        let signing = SigningKey::from_bytes(&[23; 32]);
        let artifact = serde_json::json!({
            "schema": "amphora.viscosity-model-artifact.v1",
            "module_id": "amphora-viscosity-score",
            "model_id": "model-1"
        });
        let mut signed = SignedModelArtifactV1 {
            schema: SIGNED_MODEL_ARTIFACT_SCHEMA.into(),
            module_id: "amphora-viscosity-score".into(),
            artifact_sha256: stable_hash(&artifact),
            artifact,
            signature: None,
        };
        signed.sign("model-key", &signing).unwrap();
        let mut trust = TrustStore::default();
        trust
            .insert("model-key", signing.verifying_key().to_bytes())
            .unwrap();
        assert_eq!(signed.verify_signature(&trust).unwrap(), "model-key");

        signed.artifact["model_id"] = Value::String("tampered".into());
        assert!(matches!(
            signed.verify_signature(&trust),
            Err(ArtifactError::SignaturePayload)
        ));
    }
}
