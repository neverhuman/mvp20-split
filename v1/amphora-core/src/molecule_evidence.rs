use crate::{
    canonicalize, sign_dsse, stable_hash, verify_dsse, DecisionUse, DsseEnvelope,
    EvaluationReceiptV1, EvidenceTier, PromotionPolicyV1, RightsRecordV1, SignedModelArtifactV1,
    SplitManifestV1, TrustStore,
};
use ed25519_dalek::SigningKey;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

pub const ENGINE_EVIDENCE_CONTEXT_SCHEMA: &str = "amphora.engine-evidence-context.v1";
pub const ENGINE_EVIDENCE_CONTEXT_V2_SCHEMA: &str = "amphora.engine-evidence-context.v2";
pub const ENGINE_EVIDENCE_CONTEXT_V3_SCHEMA: &str = "amphora.engine-evidence-context.v3";
pub const VERIFIED_MOLECULE_MODEL_INPUT_SCHEMA: &str = "amphora.verified-molecule-model-input.v1";
pub const VERIFIED_AUDIT_MODULE_INPUT_SCHEMA: &str = "amphora.verified-audit-module-input.v1";
pub const INDEPENDENT_REVIEW_RECEIPT_SCHEMA: &str = "amphora.independent-review-receipt.v1";
pub const INDEPENDENT_REVIEW_RECEIPT_PAYLOAD_TYPE: &str =
    "application/vnd.amphora.independent-review-receipt.v1+json";

const ROLE_RANKER_ID: &str = "amphora-molecule-role-ranker";
const ROLE_MODEL_SCHEMA: &str = "amphora.molecule-role-logistic-model.v1";
const REQUIRED_ROLE_MODEL_SEED: u64 = 20_260_717;
const GENERATOR_ID: &str = "amphora-molecule-generator";
const NOVELTY_ID: &str = "amphora-molecule-novelty";
const PROCESS_QC_ID: &str = "amphora-process-qc-twin";
pub const SPC_AUDIT_TOOLKIT_VERSION: &str = "amphora-spc-audit.v1";

#[derive(Debug, Error)]
pub enum MoleculeEvidenceError {
    #[error("unexpected evidence schema: {0}")]
    Schema(String),
    #[error("required evidence field is empty: {0}")]
    Empty(&'static str),
    #[error("invalid evidence SHA-256: {0}")]
    Hash(&'static str),
    #[error("evidence content or parent hash does not match")]
    ParentBinding,
    #[error("evidence receipt is missing a required claim lock")]
    ClaimLocks,
    #[error("evidence rights are absent or ineligible")]
    Rights,
    #[error("evaluation or independent-review receipt is not promotion-complete")]
    Receipt,
    #[error("evaluation and independent review are not independently signed")]
    Independence,
    #[error("promotion policy does not authorize the signed evaluation receipt")]
    PromotionPolicy,
    #[error("model applicability domain is malformed or unbound")]
    ApplicabilityDomain,
    #[error("molecule model does not use the preregistered fixed estimator")]
    FixedEstimator,
    #[error("molecule evidence split or expert-label protocol is invalid")]
    SplitProtocol,
    #[error("required toolkit version does not match the current host toolkit")]
    Toolkit,
    #[error("audit module is outside the closed Phase-0 audit-module allowlist")]
    AuditModule,
    #[error("audit module attempts to exceed AUDIT_ONLY authority")]
    AuditAuthority,
    #[error("evidence JSON: {0}")]
    Json(#[from] serde_json::Error),
    #[error("evidence artifact: {0}")]
    Artifact(#[from] crate::ArtifactError),
    #[error("evidence signature: {0}")]
    Signature(#[from] crate::VerificationError),
}

/// A complete host-owned evidence grant for a Phase-0/Phase-1 audit module.
///
/// This type is serializable only as host configuration. Candidate inputs are
/// never deserialized into it. The signed artifact owns executable grammar or
/// detector configuration; the remaining values bind corpus, data, split,
/// benchmark, rights, applicability, and claim-lock parents.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct VerifiedAuditModuleInputV1 {
    pub schema: String,
    pub module_id: String,
    pub module_artifact_sha256: String,
    pub corpus_sha256: String,
    pub dataset_sha256: String,
    pub split_sha256: String,
    pub benchmark_lock_sha256: String,
    pub raw_data_manifest_sha256: String,
    pub rights_manifest_sha256: String,
    pub claim_locks_sha256: String,
    pub promotion_policy_sha256: String,
    pub required_toolkit_version: String,
    pub applicability_domain: Value,
    pub claim_locks: BTreeMap<String, bool>,
    pub module_artifact: SignedModelArtifactV1,
    pub corpus: Value,
    pub dataset: Value,
    pub split: Value,
    pub benchmark_lock: Value,
    pub raw_data_hashes: BTreeMap<String, String>,
    pub rights: Vec<RightsRecordV1>,
    pub evaluation_receipt: EvaluationReceiptV1,
    pub independent_review_receipt: IndependentReviewReceiptV1,
}

impl VerifiedAuditModuleInputV1 {
    fn verify(
        &self,
        trust_store: &TrustStore,
        policy: &PromotionPolicyV1,
        registry_manifest_sha256: &str,
        current_rdkit_version: &str,
    ) -> Result<ValidatedAuditModuleInputV1, MoleculeEvidenceError> {
        if self.schema != VERIFIED_AUDIT_MODULE_INPUT_SCHEMA {
            return Err(MoleculeEvidenceError::Schema(self.schema.clone()));
        }
        if !matches!(
            self.module_id.as_str(),
            GENERATOR_ID | NOVELTY_ID | PROCESS_QC_ID
        ) {
            return Err(MoleculeEvidenceError::AuditModule);
        }
        require_text("module_id", &self.module_id)?;
        for (field, value) in [
            (
                "module_artifact_sha256",
                self.module_artifact_sha256.as_str(),
            ),
            ("corpus_sha256", self.corpus_sha256.as_str()),
            ("dataset_sha256", self.dataset_sha256.as_str()),
            ("split_sha256", self.split_sha256.as_str()),
            ("benchmark_lock_sha256", self.benchmark_lock_sha256.as_str()),
            (
                "raw_data_manifest_sha256",
                self.raw_data_manifest_sha256.as_str(),
            ),
            (
                "rights_manifest_sha256",
                self.rights_manifest_sha256.as_str(),
            ),
            ("claim_locks_sha256", self.claim_locks_sha256.as_str()),
            (
                "promotion_policy_sha256",
                self.promotion_policy_sha256.as_str(),
            ),
        ] {
            require_hash(field, value)?;
        }

        let artifact_value = serde_json::to_value(&self.module_artifact)?;
        let raw_value = serde_json::to_value(&self.raw_data_hashes)?;
        let rights_value = serde_json::to_value(&self.rights)?;
        let locks_value = serde_json::to_value(&self.claim_locks)?;
        for (content, expected) in [
            (&artifact_value, &self.module_artifact_sha256),
            (&self.corpus, &self.corpus_sha256),
            (&self.dataset, &self.dataset_sha256),
            (&self.split, &self.split_sha256),
            (&self.benchmark_lock, &self.benchmark_lock_sha256),
            (&raw_value, &self.raw_data_manifest_sha256),
            (&rights_value, &self.rights_manifest_sha256),
            (&locks_value, &self.claim_locks_sha256),
        ] {
            if stable_hash(content) != *expected {
                return Err(MoleculeEvidenceError::ParentBinding);
            }
        }
        if self.raw_data_hashes.is_empty() {
            return Err(MoleculeEvidenceError::Empty("raw_data_hashes"));
        }
        for (path, hash) in &self.raw_data_hashes {
            require_text("raw_data_hashes.path", path)?;
            require_hash("raw_data_hashes.sha256", hash)?;
        }
        if self.rights.is_empty()
            || self.rights.iter().any(|rights| {
                rights.source_id.trim().is_empty()
                    || rights.license.trim().is_empty()
                    || rights.source_url.trim().is_empty()
                    || rights.status != "ACCEPTED"
                    || !rights.eligible_for_derivatives
            })
        {
            return Err(MoleculeEvidenceError::Rights);
        }
        validate_claim_locks(&self.claim_locks)?;
        for required in required_audit_claim_locks(&self.module_id)? {
            if self.claim_locks.get(*required) != Some(&true) {
                return Err(MoleculeEvidenceError::ClaimLocks);
            }
        }

        self.module_artifact.validate()?;
        if self.module_artifact.module_id != self.module_id
            || self.evaluation_receipt.module_id != self.module_id
            || self.independent_review_receipt.module_id != self.module_id
        {
            return Err(MoleculeEvidenceError::ParentBinding);
        }
        let model_signer = self.module_artifact.verify_signature(trust_store)?;
        let evaluation_signer = self.evaluation_receipt.verify_signature(trust_store)?;
        let review_signer = self
            .independent_review_receipt
            .verify_signature(trust_store)?;
        if evaluation_signer == review_signer {
            return Err(MoleculeEvidenceError::Independence);
        }

        let receipt = &self.evaluation_receipt;
        receipt.validate()?;
        if !receipt.passed
            || receipt.decision_use_ceiling != DecisionUse::AuditOnly
            || receipt.registry_manifest_hash != registry_manifest_sha256
            || receipt.benchmark_lock_hash != self.benchmark_lock_sha256
            || receipt.claim_locks != self.claim_locks
        {
            return Err(MoleculeEvidenceError::AuditAuthority);
        }
        for (name, expected) in [
            ("module_artifact", self.module_artifact_sha256.as_str()),
            ("corpus", self.corpus_sha256.as_str()),
            ("dataset", self.dataset_sha256.as_str()),
            ("split", self.split_sha256.as_str()),
            ("raw_data_manifest", self.raw_data_manifest_sha256.as_str()),
            ("rights_manifest", self.rights_manifest_sha256.as_str()),
            ("claim_locks", self.claim_locks_sha256.as_str()),
        ] {
            if receipt.artifact_hashes.get(name).map(String::as_str) != Some(expected) {
                return Err(MoleculeEvidenceError::ParentBinding);
            }
        }

        let evaluation_receipt_sha256 = stable_hash(&serde_json::to_value(receipt)?);
        let review = &self.independent_review_receipt;
        if review.registry_manifest_hash != registry_manifest_sha256
            || review.evaluation_receipt_sha256 != evaluation_receipt_sha256
            || review.model_artifact_sha256 != self.module_artifact_sha256
            || review.benchmark_lock_sha256 != self.benchmark_lock_sha256
            || review.claim_locks != self.claim_locks
        {
            return Err(MoleculeEvidenceError::Receipt);
        }

        policy.validate()?;
        if stable_hash(&serde_json::to_value(policy)?) != self.promotion_policy_sha256
            || policy.registry_manifest_hash != registry_manifest_sha256
            || policy.authority_for(receipt, &evaluation_receipt_sha256)? != DecisionUse::AuditOnly
        {
            return Err(MoleculeEvidenceError::PromotionPolicy);
        }
        let expected_toolkit = if self.module_id == PROCESS_QC_ID {
            SPC_AUDIT_TOOLKIT_VERSION
        } else {
            current_rdkit_version
        };
        if self.required_toolkit_version != expected_toolkit {
            return Err(MoleculeEvidenceError::Toolkit);
        }
        if self.applicability_domain.as_object().is_none()
            || self.applicability_domain
                != self
                    .module_artifact
                    .artifact
                    .get("applicability_domain")
                    .cloned()
                    .unwrap_or(Value::Null)
        {
            return Err(MoleculeEvidenceError::ApplicabilityDomain);
        }
        verify_audit_parents(self)?;

        Ok(ValidatedAuditModuleInputV1 {
            input: self.clone(),
            evidence_package_sha256: stable_hash(&serde_json::to_value(self)?),
            model_signer,
            evaluation_signer,
            review_signer,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct IndependentReviewReceiptV1 {
    pub schema: String,
    pub receipt_id: String,
    pub module_id: String,
    pub registry_manifest_hash: String,
    pub evaluation_receipt_sha256: String,
    pub model_artifact_sha256: String,
    pub benchmark_lock_sha256: String,
    pub reviewer_id: String,
    pub reviewer_independent: bool,
    pub independent_transfer_passed: bool,
    pub primary_improvement_confirmed: bool,
    pub verifier_reversed_primary: bool,
    pub claim_locks: BTreeMap<String, bool>,
    #[serde(default)]
    pub applicability_limits: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<DsseEnvelope>,
}

impl IndependentReviewReceiptV1 {
    pub fn validate(&self) -> Result<(), MoleculeEvidenceError> {
        if self.schema != INDEPENDENT_REVIEW_RECEIPT_SCHEMA {
            return Err(MoleculeEvidenceError::Schema(self.schema.clone()));
        }
        for (field, value) in [
            ("receipt_id", self.receipt_id.as_str()),
            ("module_id", self.module_id.as_str()),
            ("reviewer_id", self.reviewer_id.as_str()),
        ] {
            require_text(field, value)?;
        }
        for (field, value) in [
            (
                "registry_manifest_hash",
                self.registry_manifest_hash.as_str(),
            ),
            (
                "evaluation_receipt_sha256",
                self.evaluation_receipt_sha256.as_str(),
            ),
            ("model_artifact_sha256", self.model_artifact_sha256.as_str()),
            ("benchmark_lock_sha256", self.benchmark_lock_sha256.as_str()),
        ] {
            require_hash(field, value)?;
        }
        if !self.reviewer_independent
            || !self.independent_transfer_passed
            || !self.primary_improvement_confirmed
            || self.verifier_reversed_primary
        {
            return Err(MoleculeEvidenceError::Receipt);
        }
        validate_claim_locks(&self.claim_locks)?;
        if self.applicability_limits.is_empty()
            || self
                .applicability_limits
                .iter()
                .any(|limit| limit.trim().is_empty())
        {
            return Err(MoleculeEvidenceError::ApplicabilityDomain);
        }
        Ok(())
    }

    fn unsigned_bytes(&self) -> Result<Vec<u8>, MoleculeEvidenceError> {
        let mut unsigned = self.clone();
        unsigned.signature = None;
        Ok(serde_json::to_vec(&canonicalize(&serde_json::to_value(
            unsigned,
        )?))?)
    }

    pub fn sign(
        &mut self,
        key_id: &str,
        signing_key: &SigningKey,
    ) -> Result<(), MoleculeEvidenceError> {
        self.validate()?;
        self.signature = Some(sign_dsse(
            INDEPENDENT_REVIEW_RECEIPT_PAYLOAD_TYPE,
            &self.unsigned_bytes()?,
            key_id,
            signing_key,
        ));
        Ok(())
    }

    pub fn verify_signature(
        &self,
        trust_store: &TrustStore,
    ) -> Result<String, MoleculeEvidenceError> {
        self.validate()?;
        let envelope = self
            .signature
            .as_ref()
            .ok_or(MoleculeEvidenceError::Receipt)?;
        if envelope.payload_type != INDEPENDENT_REVIEW_RECEIPT_PAYLOAD_TYPE {
            return Err(MoleculeEvidenceError::Receipt);
        }
        let verified = verify_dsse(envelope, trust_store)?;
        if verified.payload != self.unsigned_bytes()? {
            return Err(MoleculeEvidenceError::ParentBinding);
        }
        Ok(verified.key_id)
    }
}

/// A complete, signed, model-wide molecule evidence grant.
///
/// Candidate JSON is never deserialized into this type by the engine. The host
/// loads it from its configured evidence root, verifies every parent and
/// signature, then derives a candidate-bound `AuthorizedMoleculeModelInputV1`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct VerifiedMoleculeModelInputV1 {
    pub schema: String,
    pub module_id: String,
    pub model_artifact_sha256: String,
    pub corpus_sha256: String,
    pub dataset_sha256: String,
    pub split_sha256: String,
    pub benchmark_lock_sha256: String,
    pub raw_data_manifest_sha256: String,
    pub rights_manifest_sha256: String,
    pub promotion_policy_sha256: String,
    pub required_toolkit_version: String,
    pub applicability_domain: Value,
    pub model_artifact: SignedModelArtifactV1,
    pub corpus: Value,
    pub dataset: Value,
    pub split: Value,
    pub benchmark_lock: Value,
    pub raw_data_hashes: BTreeMap<String, String>,
    pub rights: Vec<RightsRecordV1>,
    pub evaluation_receipt: EvaluationReceiptV1,
    pub independent_review_receipt: IndependentReviewReceiptV1,
}

impl VerifiedMoleculeModelInputV1 {
    fn verify(
        &self,
        trust_store: &TrustStore,
        policy: &PromotionPolicyV1,
        registry_manifest_sha256: &str,
        current_toolkit_version: &str,
    ) -> Result<ValidatedMoleculeModelInputV1, MoleculeEvidenceError> {
        if self.schema != VERIFIED_MOLECULE_MODEL_INPUT_SCHEMA {
            return Err(MoleculeEvidenceError::Schema(self.schema.clone()));
        }
        require_text("module_id", &self.module_id)?;
        for (field, value) in [
            ("model_artifact_sha256", self.model_artifact_sha256.as_str()),
            ("corpus_sha256", self.corpus_sha256.as_str()),
            ("dataset_sha256", self.dataset_sha256.as_str()),
            ("split_sha256", self.split_sha256.as_str()),
            ("benchmark_lock_sha256", self.benchmark_lock_sha256.as_str()),
            (
                "raw_data_manifest_sha256",
                self.raw_data_manifest_sha256.as_str(),
            ),
            (
                "rights_manifest_sha256",
                self.rights_manifest_sha256.as_str(),
            ),
            (
                "promotion_policy_sha256",
                self.promotion_policy_sha256.as_str(),
            ),
        ] {
            require_hash(field, value)?;
        }

        let model_value = serde_json::to_value(&self.model_artifact)?;
        let raw_value = serde_json::to_value(&self.raw_data_hashes)?;
        let rights_value = serde_json::to_value(&self.rights)?;
        for (content, expected) in [
            (&model_value, &self.model_artifact_sha256),
            (&self.corpus, &self.corpus_sha256),
            (&self.dataset, &self.dataset_sha256),
            (&self.split, &self.split_sha256),
            (&self.benchmark_lock, &self.benchmark_lock_sha256),
            (&raw_value, &self.raw_data_manifest_sha256),
            (&rights_value, &self.rights_manifest_sha256),
        ] {
            if stable_hash(content) != *expected {
                return Err(MoleculeEvidenceError::ParentBinding);
            }
        }
        if self.raw_data_hashes.is_empty() {
            return Err(MoleculeEvidenceError::Empty("raw_data_hashes"));
        }
        for (path, hash) in &self.raw_data_hashes {
            require_text("raw_data_hashes.path", path)?;
            require_hash("raw_data_hashes.sha256", hash)?;
        }
        if self.rights.is_empty()
            || self.rights.iter().any(|rights| {
                rights.source_id.trim().is_empty()
                    || rights.license.trim().is_empty()
                    || rights.source_url.trim().is_empty()
                    || !rights.eligible_for_derivatives
            })
        {
            return Err(MoleculeEvidenceError::Rights);
        }

        self.model_artifact.validate()?;
        if self.model_artifact.module_id != self.module_id
            || self
                .model_artifact
                .artifact
                .get("module_id")
                .and_then(Value::as_str)
                != Some(self.module_id.as_str())
            || self.evaluation_receipt.module_id != self.module_id
            || self.independent_review_receipt.module_id != self.module_id
        {
            return Err(MoleculeEvidenceError::ParentBinding);
        }
        let model_signer = self.model_artifact.verify_signature(trust_store)?;
        let evaluation_signer = self.evaluation_receipt.verify_signature(trust_store)?;
        let review_signer = self
            .independent_review_receipt
            .verify_signature(trust_store)?;
        if evaluation_signer == review_signer {
            return Err(MoleculeEvidenceError::Independence);
        }

        let receipt = &self.evaluation_receipt;
        receipt.validate()?;
        validate_claim_locks(&receipt.claim_locks)?;
        if !receipt.passed
            || !matches!(
                receipt.evidence_tier,
                EvidenceTier::IndependentExternal | EvidenceTier::ProspectiveReplicated
            )
            || receipt.decision_use_ceiling != DecisionUse::Ranking
            || receipt.registry_manifest_hash != registry_manifest_sha256
            || receipt.benchmark_lock_hash != self.benchmark_lock_sha256
        {
            return Err(MoleculeEvidenceError::Receipt);
        }
        for (name, expected) in [
            ("model_artifact", self.model_artifact_sha256.as_str()),
            ("corpus", self.corpus_sha256.as_str()),
            ("dataset", self.dataset_sha256.as_str()),
            ("split", self.split_sha256.as_str()),
            ("raw_data_manifest", self.raw_data_manifest_sha256.as_str()),
            ("rights_manifest", self.rights_manifest_sha256.as_str()),
        ] {
            if receipt.artifact_hashes.get(name).map(String::as_str) != Some(expected) {
                return Err(MoleculeEvidenceError::ParentBinding);
            }
        }

        let evaluation_receipt_sha256 = stable_hash(&serde_json::to_value(receipt)?);
        let review = &self.independent_review_receipt;
        if review.registry_manifest_hash != registry_manifest_sha256
            || review.evaluation_receipt_sha256 != evaluation_receipt_sha256
            || review.model_artifact_sha256 != self.model_artifact_sha256
            || review.benchmark_lock_sha256 != self.benchmark_lock_sha256
        {
            return Err(MoleculeEvidenceError::Receipt);
        }

        policy.validate()?;
        if stable_hash(&serde_json::to_value(policy)?) != self.promotion_policy_sha256
            || policy.registry_manifest_hash != registry_manifest_sha256
            || policy.authority_for(receipt, &evaluation_receipt_sha256)? != DecisionUse::Ranking
        {
            return Err(MoleculeEvidenceError::PromotionPolicy);
        }
        if self.required_toolkit_version != current_toolkit_version {
            return Err(MoleculeEvidenceError::Toolkit);
        }
        if self.applicability_domain.as_object().is_none()
            || self.applicability_domain
                != self
                    .model_artifact
                    .artifact
                    .get("applicability_domain")
                    .cloned()
                    .unwrap_or(Value::Null)
        {
            return Err(MoleculeEvidenceError::ApplicabilityDomain);
        }
        verify_model_parents(self)?;
        if self.module_id == ROLE_RANKER_ID {
            verify_fixed_role_model(&self.model_artifact.artifact)?;
            verify_role_evidence_protocol(self)?;
        }

        Ok(ValidatedMoleculeModelInputV1 {
            input: self.clone(),
            evidence_package_sha256: stable_hash(&serde_json::to_value(self)?),
            model_signer,
            evaluation_signer,
            review_signer,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EngineEvidenceContextV1 {
    pub schema: String,
    pub registry_manifest_sha256: String,
    pub promotion_policy_sha256: String,
    pub promotion_policy: PromotionPolicyV1,
    pub molecule_models: BTreeMap<String, VerifiedMoleculeModelInputV1>,
}

impl EngineEvidenceContextV1 {
    pub fn verify(
        &self,
        trust_store: &TrustStore,
        current_registry_manifest_sha256: &str,
        current_toolkit_version: &str,
    ) -> Result<ValidatedEngineEvidenceContextV1, MoleculeEvidenceError> {
        if self.schema != ENGINE_EVIDENCE_CONTEXT_SCHEMA {
            return Err(MoleculeEvidenceError::Schema(self.schema.clone()));
        }
        require_hash("registry_manifest_sha256", &self.registry_manifest_sha256)?;
        require_hash("promotion_policy_sha256", &self.promotion_policy_sha256)?;
        if self.registry_manifest_sha256 != current_registry_manifest_sha256
            || stable_hash(&serde_json::to_value(&self.promotion_policy)?)
                != self.promotion_policy_sha256
            || self.promotion_policy.registry_manifest_hash != self.registry_manifest_sha256
        {
            return Err(MoleculeEvidenceError::ParentBinding);
        }
        let mut models = BTreeMap::new();
        for (module_id, input) in &self.molecule_models {
            if module_id != &input.module_id
                || input.promotion_policy_sha256 != self.promotion_policy_sha256
                || models
                    .insert(
                        module_id.clone(),
                        input.verify(
                            trust_store,
                            &self.promotion_policy,
                            &self.registry_manifest_sha256,
                            current_toolkit_version,
                        )?,
                    )
                    .is_some()
            {
                return Err(MoleculeEvidenceError::ParentBinding);
            }
        }
        Ok(ValidatedEngineEvidenceContextV1 {
            context_sha256: stable_hash(&serde_json::to_value(self)?),
            models,
        })
    }
}

#[derive(Debug, Clone)]
pub struct ValidatedEngineEvidenceContextV1 {
    context_sha256: String,
    models: BTreeMap<String, ValidatedMoleculeModelInputV1>,
}

impl ValidatedEngineEvidenceContextV1 {
    pub fn context_sha256(&self) -> &str {
        &self.context_sha256
    }

    pub fn authorize(
        &self,
        module_id: &str,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
        molecule_facts_sha256: &str,
    ) -> Option<AuthorizedMoleculeModelInputV1> {
        let model = self.models.get(module_id)?;
        Some(AuthorizedMoleculeModelInputV1 {
            candidate_id: candidate_id.to_owned(),
            candidate_contract_hash_v1: candidate_contract_hash_v1.to_owned(),
            molecule_facts_sha256: molecule_facts_sha256.to_owned(),
            evidence_context_sha256: self.context_sha256.clone(),
            model: model.clone(),
        })
    }
}

#[derive(Debug, Clone)]
struct ValidatedMoleculeModelInputV1 {
    input: VerifiedMoleculeModelInputV1,
    evidence_package_sha256: String,
    model_signer: String,
    evaluation_signer: String,
    review_signer: String,
}

/// Non-serializable, candidate-bound authorization produced only after the
/// host has verified the complete evidence context.
#[derive(Debug, Clone)]
pub struct AuthorizedMoleculeModelInputV1 {
    candidate_id: String,
    candidate_contract_hash_v1: String,
    molecule_facts_sha256: String,
    evidence_context_sha256: String,
    model: ValidatedMoleculeModelInputV1,
}

impl AuthorizedMoleculeModelInputV1 {
    pub fn validate_binding(
        &self,
        module_id: &str,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
        molecule_facts_sha256: &str,
    ) -> bool {
        self.model.input.module_id == module_id
            && self.candidate_id == candidate_id
            && self.candidate_contract_hash_v1 == candidate_contract_hash_v1
            && self.molecule_facts_sha256 == molecule_facts_sha256
    }

    pub fn model_artifact(&self) -> &Value {
        &self.model.input.model_artifact.artifact
    }

    pub fn applicability_domain(&self) -> &Value {
        &self.model.input.applicability_domain
    }

    pub fn evidence_context_sha256(&self) -> &str {
        &self.evidence_context_sha256
    }

    pub fn evidence_package_sha256(&self) -> &str {
        &self.model.evidence_package_sha256
    }

    pub fn signer_ids(&self) -> (&str, &str, &str) {
        (
            &self.model.model_signer,
            &self.model.evaluation_signer,
            &self.model.review_signer,
        )
    }
}

/// V2 retains the complete V1 molecule-model map and adds the three
/// separately authorized audit-only modules.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EngineEvidenceContextV2 {
    pub schema: String,
    pub registry_manifest_sha256: String,
    pub promotion_policy_sha256: String,
    pub promotion_policy: PromotionPolicyV1,
    #[serde(default)]
    pub molecule_models: BTreeMap<String, VerifiedMoleculeModelInputV1>,
    pub audit_modules: BTreeMap<String, VerifiedAuditModuleInputV1>,
}

impl EngineEvidenceContextV2 {
    pub fn verify(
        &self,
        trust_store: &TrustStore,
        current_registry_manifest_sha256: &str,
        current_rdkit_version: &str,
    ) -> Result<ValidatedEngineEvidenceContextV2, MoleculeEvidenceError> {
        if self.schema != ENGINE_EVIDENCE_CONTEXT_V2_SCHEMA {
            return Err(MoleculeEvidenceError::Schema(self.schema.clone()));
        }
        require_hash("registry_manifest_sha256", &self.registry_manifest_sha256)?;
        require_hash("promotion_policy_sha256", &self.promotion_policy_sha256)?;
        if self.registry_manifest_sha256 != current_registry_manifest_sha256
            || stable_hash(&serde_json::to_value(&self.promotion_policy)?)
                != self.promotion_policy_sha256
            || self.promotion_policy.registry_manifest_hash != self.registry_manifest_sha256
        {
            return Err(MoleculeEvidenceError::ParentBinding);
        }

        let mut models = BTreeMap::new();
        for (module_id, input) in &self.molecule_models {
            if module_id != &input.module_id
                || input.promotion_policy_sha256 != self.promotion_policy_sha256
                || models
                    .insert(
                        module_id.clone(),
                        input.verify(
                            trust_store,
                            &self.promotion_policy,
                            &self.registry_manifest_sha256,
                            current_rdkit_version,
                        )?,
                    )
                    .is_some()
            {
                return Err(MoleculeEvidenceError::ParentBinding);
            }
        }

        let mut audit_modules = BTreeMap::new();
        for (module_id, input) in &self.audit_modules {
            if module_id != &input.module_id
                || input.promotion_policy_sha256 != self.promotion_policy_sha256
                || audit_modules
                    .insert(
                        module_id.clone(),
                        input.verify(
                            trust_store,
                            &self.promotion_policy,
                            &self.registry_manifest_sha256,
                            current_rdkit_version,
                        )?,
                    )
                    .is_some()
            {
                return Err(MoleculeEvidenceError::ParentBinding);
            }
        }
        if audit_modules.len() != 3
            || ![GENERATOR_ID, NOVELTY_ID, PROCESS_QC_ID]
                .iter()
                .all(|module_id| audit_modules.contains_key(*module_id))
        {
            return Err(MoleculeEvidenceError::AuditModule);
        }

        Ok(ValidatedEngineEvidenceContextV2 {
            context_sha256: stable_hash(&serde_json::to_value(self)?),
            models,
            audit_modules,
        })
    }
}

#[derive(Debug, Clone)]
pub struct ValidatedEngineEvidenceContextV2 {
    context_sha256: String,
    models: BTreeMap<String, ValidatedMoleculeModelInputV1>,
    audit_modules: BTreeMap<String, ValidatedAuditModuleInputV1>,
}

impl ValidatedEngineEvidenceContextV2 {
    pub fn context_sha256(&self) -> &str {
        &self.context_sha256
    }

    pub fn authorize_molecule_model(
        &self,
        module_id: &str,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
        molecule_facts_sha256: &str,
    ) -> Option<AuthorizedMoleculeModelInputV1> {
        let model = self.models.get(module_id)?;
        Some(AuthorizedMoleculeModelInputV1 {
            candidate_id: candidate_id.to_owned(),
            candidate_contract_hash_v1: candidate_contract_hash_v1.to_owned(),
            molecule_facts_sha256: molecule_facts_sha256.to_owned(),
            evidence_context_sha256: self.context_sha256.clone(),
            model: model.clone(),
        })
    }

    pub fn authorize_audit_module(
        &self,
        module_id: &str,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
        binding_kind: AuditInputBindingKindV1,
        normalized_input_sha256: &str,
    ) -> Option<AuthorizedAuditModuleInputV1> {
        if require_hash("normalized_input_sha256", normalized_input_sha256).is_err() {
            return None;
        }
        let module = self.audit_modules.get(module_id)?;
        match binding_kind {
            AuditInputBindingKindV1::MoleculeFacts
                if !matches!(module_id, GENERATOR_ID | NOVELTY_ID) =>
            {
                return None;
            }
            AuditInputBindingKindV1::ProcessQcSeries if module_id != PROCESS_QC_ID => return None,
            AuditInputBindingKindV1::ProcessQcSeries => {
                let trusted_series = module
                    .input
                    .dataset
                    .get("process_qc_series")
                    .unwrap_or(&module.input.dataset);
                if stable_hash(trusted_series) != normalized_input_sha256 {
                    return None;
                }
            }
            AuditInputBindingKindV1::MoleculeFacts => {}
        }
        Some(AuthorizedAuditModuleInputV1 {
            candidate_id: candidate_id.to_owned(),
            candidate_contract_hash_v1: candidate_contract_hash_v1.to_owned(),
            binding_kind,
            normalized_input_sha256: normalized_input_sha256.to_owned(),
            evidence_context_sha256: self.context_sha256.clone(),
            module: module.clone(),
        })
    }
}

/// V3 makes audit-only Phase-0 runtime grants independently activatable.
/// In particular, a generator grant does not require unrelated novelty or
/// process-QC grants to be present.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EngineEvidenceContextV3 {
    pub schema: String,
    pub registry_manifest_sha256: String,
    pub promotion_policy_sha256: String,
    pub promotion_policy: PromotionPolicyV1,
    #[serde(default)]
    pub molecule_models: BTreeMap<String, VerifiedMoleculeModelInputV1>,
    #[serde(default)]
    pub phase0_runtime_grants: BTreeMap<String, VerifiedAuditModuleInputV1>,
}

impl EngineEvidenceContextV3 {
    pub fn verify(
        &self,
        trust_store: &TrustStore,
        current_registry_manifest_sha256: &str,
        current_rdkit_version: &str,
    ) -> Result<ValidatedEngineEvidenceContextV3, MoleculeEvidenceError> {
        if self.schema != ENGINE_EVIDENCE_CONTEXT_V3_SCHEMA {
            return Err(MoleculeEvidenceError::Schema(self.schema.clone()));
        }
        require_hash("registry_manifest_sha256", &self.registry_manifest_sha256)?;
        require_hash("promotion_policy_sha256", &self.promotion_policy_sha256)?;
        if self.registry_manifest_sha256 != current_registry_manifest_sha256
            || stable_hash(&serde_json::to_value(&self.promotion_policy)?)
                != self.promotion_policy_sha256
            || self.promotion_policy.registry_manifest_hash != self.registry_manifest_sha256
        {
            return Err(MoleculeEvidenceError::ParentBinding);
        }

        let mut models = BTreeMap::new();
        for (module_id, input) in &self.molecule_models {
            if module_id != &input.module_id
                || input.promotion_policy_sha256 != self.promotion_policy_sha256
                || models
                    .insert(
                        module_id.clone(),
                        input.verify(
                            trust_store,
                            &self.promotion_policy,
                            &self.registry_manifest_sha256,
                            current_rdkit_version,
                        )?,
                    )
                    .is_some()
            {
                return Err(MoleculeEvidenceError::ParentBinding);
            }
        }

        let mut runtime_grants = BTreeMap::new();
        for (module_id, input) in &self.phase0_runtime_grants {
            if module_id != &input.module_id
                || input.promotion_policy_sha256 != self.promotion_policy_sha256
            {
                return Err(MoleculeEvidenceError::ParentBinding);
            }
            let validated = input.verify(
                trust_store,
                &self.promotion_policy,
                &self.registry_manifest_sha256,
                current_rdkit_version,
            )?;
            if BTreeSet::from([
                validated.model_signer.as_str(),
                validated.evaluation_signer.as_str(),
                validated.review_signer.as_str(),
            ])
            .len()
                != 3
                || runtime_grants
                    .insert(module_id.clone(), validated)
                    .is_some()
            {
                return Err(MoleculeEvidenceError::Independence);
            }
        }

        Ok(ValidatedEngineEvidenceContextV3 {
            context_sha256: stable_hash(&serde_json::to_value(self)?),
            models,
            runtime_grants,
        })
    }
}

#[derive(Debug, Clone)]
pub struct ValidatedEngineEvidenceContextV3 {
    context_sha256: String,
    models: BTreeMap<String, ValidatedMoleculeModelInputV1>,
    runtime_grants: BTreeMap<String, ValidatedAuditModuleInputV1>,
}

impl ValidatedEngineEvidenceContextV3 {
    pub fn context_sha256(&self) -> &str {
        &self.context_sha256
    }

    pub fn authorize_molecule_model(
        &self,
        module_id: &str,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
        molecule_facts_sha256: &str,
    ) -> Option<AuthorizedMoleculeModelInputV1> {
        let model = self.models.get(module_id)?;
        Some(AuthorizedMoleculeModelInputV1 {
            candidate_id: candidate_id.to_owned(),
            candidate_contract_hash_v1: candidate_contract_hash_v1.to_owned(),
            molecule_facts_sha256: molecule_facts_sha256.to_owned(),
            evidence_context_sha256: self.context_sha256.clone(),
            model: model.clone(),
        })
    }

    pub fn authorize_runtime_grant(
        &self,
        module_id: &str,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
        binding_kind: AuditInputBindingKindV1,
        normalized_input_sha256: &str,
    ) -> Option<AuthorizedAuditModuleInputV1> {
        if require_hash("normalized_input_sha256", normalized_input_sha256).is_err() {
            return None;
        }
        let module = self.runtime_grants.get(module_id)?;
        match binding_kind {
            AuditInputBindingKindV1::MoleculeFacts
                if !matches!(module_id, GENERATOR_ID | NOVELTY_ID) =>
            {
                return None;
            }
            AuditInputBindingKindV1::ProcessQcSeries if module_id != PROCESS_QC_ID => return None,
            AuditInputBindingKindV1::ProcessQcSeries => {
                let trusted_series = module
                    .input
                    .dataset
                    .get("process_qc_series")
                    .unwrap_or(&module.input.dataset);
                if stable_hash(trusted_series) != normalized_input_sha256 {
                    return None;
                }
            }
            AuditInputBindingKindV1::MoleculeFacts => {}
        }
        Some(AuthorizedAuditModuleInputV1 {
            candidate_id: candidate_id.to_owned(),
            candidate_contract_hash_v1: candidate_contract_hash_v1.to_owned(),
            binding_kind,
            normalized_input_sha256: normalized_input_sha256.to_owned(),
            evidence_context_sha256: self.context_sha256.clone(),
            module: module.clone(),
        })
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AuditInputBindingKindV1 {
    MoleculeFacts,
    ProcessQcSeries,
}

#[derive(Debug, Clone)]
struct ValidatedAuditModuleInputV1 {
    input: VerifiedAuditModuleInputV1,
    evidence_package_sha256: String,
    model_signer: String,
    evaluation_signer: String,
    review_signer: String,
}

/// Candidate-bound, deliberately non-serializable authorization. It can only
/// be constructed by a verified V2 host context.
#[derive(Debug, Clone)]
pub struct AuthorizedAuditModuleInputV1 {
    candidate_id: String,
    candidate_contract_hash_v1: String,
    binding_kind: AuditInputBindingKindV1,
    normalized_input_sha256: String,
    evidence_context_sha256: String,
    module: ValidatedAuditModuleInputV1,
}

impl AuthorizedAuditModuleInputV1 {
    pub fn validate_binding(
        &self,
        module_id: &str,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
        binding_kind: AuditInputBindingKindV1,
        normalized_input_sha256: &str,
    ) -> bool {
        self.module.input.module_id == module_id
            && self.candidate_id == candidate_id
            && self.candidate_contract_hash_v1 == candidate_contract_hash_v1
            && self.binding_kind == binding_kind
            && self.normalized_input_sha256 == normalized_input_sha256
    }

    pub fn module_artifact(&self) -> &Value {
        &self.module.input.module_artifact.artifact
    }

    pub fn corpus(&self) -> &Value {
        &self.module.input.corpus
    }

    pub fn dataset(&self) -> &Value {
        &self.module.input.dataset
    }

    pub fn benchmark_lock(&self) -> &Value {
        &self.module.input.benchmark_lock
    }

    pub fn applicability_domain(&self) -> &Value {
        &self.module.input.applicability_domain
    }

    pub fn claim_locks(&self) -> &BTreeMap<String, bool> {
        &self.module.input.claim_locks
    }

    pub fn evidence_context_sha256(&self) -> &str {
        &self.evidence_context_sha256
    }

    pub fn evidence_package_sha256(&self) -> &str {
        &self.module.evidence_package_sha256
    }

    pub fn evidence_status(&self) -> &'static str {
        if matches!(
            self.module.input.evaluation_receipt.evidence_tier,
            EvidenceTier::IndependentExternal | EvidenceTier::ProspectiveReplicated
        ) {
            "INDEPENDENTLY_VALIDATED"
        } else {
            "LOCKED_INTERNAL"
        }
    }

    pub fn signer_ids(&self) -> (&str, &str, &str) {
        (
            &self.module.model_signer,
            &self.module.evaluation_signer,
            &self.module.review_signer,
        )
    }
}

fn required_audit_claim_locks(
    module_id: &str,
) -> Result<&'static [&'static str], MoleculeEvidenceError> {
    match module_id {
        GENERATOR_ID => Ok(&[
            "audit_only",
            "generated_molecules_unmade_unvalidated",
            "no_optimizer_authority",
            "not_a_synthesis_recommendation",
        ]),
        NOVELTY_ID => Ok(&[
            "audit_only",
            "automated_patent_extraction_only",
            "no_optimizer_authority",
            "not_patentability_or_fto",
        ]),
        PROCESS_QC_ID => Ok(&[
            "alert_means_investigate_only",
            "audit_only",
            "control_limits_are_not_specification_limits",
            "no_batch_release_authority",
        ]),
        _ => Err(MoleculeEvidenceError::AuditModule),
    }
}

fn verify_audit_parents(input: &VerifiedAuditModuleInputV1) -> Result<(), MoleculeEvidenceError> {
    let parents = input
        .module_artifact
        .artifact
        .get("parent_hashes")
        .and_then(Value::as_object)
        .ok_or(MoleculeEvidenceError::ParentBinding)?;
    for (name, expected) in [
        ("corpus", input.corpus_sha256.as_str()),
        ("dataset", input.dataset_sha256.as_str()),
        ("split", input.split_sha256.as_str()),
        ("benchmark_lock", input.benchmark_lock_sha256.as_str()),
        ("raw_data_manifest", input.raw_data_manifest_sha256.as_str()),
        ("rights_manifest", input.rights_manifest_sha256.as_str()),
        ("claim_locks", input.claim_locks_sha256.as_str()),
    ] {
        if parents.get(name).and_then(Value::as_str) != Some(expected) {
            return Err(MoleculeEvidenceError::ParentBinding);
        }
    }
    Ok(())
}

fn verify_model_parents(input: &VerifiedMoleculeModelInputV1) -> Result<(), MoleculeEvidenceError> {
    let parents = input
        .model_artifact
        .artifact
        .get("parent_hashes")
        .and_then(Value::as_object)
        .ok_or(MoleculeEvidenceError::ParentBinding)?;
    for (name, expected) in [
        ("corpus", input.corpus_sha256.as_str()),
        ("dataset", input.dataset_sha256.as_str()),
        ("split", input.split_sha256.as_str()),
        ("benchmark_lock", input.benchmark_lock_sha256.as_str()),
        ("raw_data_manifest", input.raw_data_manifest_sha256.as_str()),
        ("rights_manifest", input.rights_manifest_sha256.as_str()),
    ] {
        if parents.get(name).and_then(Value::as_str) != Some(expected) {
            return Err(MoleculeEvidenceError::ParentBinding);
        }
    }
    Ok(())
}

fn verify_fixed_role_model(artifact: &Value) -> Result<(), MoleculeEvidenceError> {
    let contract = artifact
        .get("training_contract")
        .ok_or(MoleculeEvidenceError::FixedEstimator)?;
    let features = artifact
        .get("feature_order")
        .and_then(Value::as_array)
        .ok_or(MoleculeEvidenceError::FixedEstimator)?;
    let coefficients = artifact
        .get("coefficients")
        .and_then(Value::as_array)
        .ok_or(MoleculeEvidenceError::FixedEstimator)?;
    let means = artifact
        .pointer("/standardization/means")
        .and_then(Value::as_object)
        .ok_or(MoleculeEvidenceError::FixedEstimator)?;
    let scales = artifact
        .pointer("/standardization/scales")
        .and_then(Value::as_object)
        .ok_or(MoleculeEvidenceError::FixedEstimator)?;
    if artifact.get("schema").and_then(Value::as_str) != Some(ROLE_MODEL_SCHEMA)
        || features.is_empty()
        || features.len() != coefficients.len()
        || coefficients
            .iter()
            .any(|coefficient| coefficient.as_f64().is_none_or(|value| !value.is_finite()))
        || contract.get("family").and_then(Value::as_str) != Some("STANDARDIZED_LOGISTIC")
        || contract.get("l2_penalty").and_then(Value::as_f64) != Some(1.0)
        || contract.get("seed").and_then(Value::as_u64) != Some(REQUIRED_ROLE_MODEL_SEED)
        || contract
            .get("training_only_scaling")
            .and_then(Value::as_bool)
            != Some(true)
        || contract
            .get("post_outcome_feature_search")
            .and_then(Value::as_bool)
            != Some(false)
    {
        return Err(MoleculeEvidenceError::FixedEstimator);
    }
    for feature in features.iter().filter_map(Value::as_str) {
        if feature == "intercept" {
            continue;
        }
        if means
            .get(feature)
            .and_then(Value::as_f64)
            .is_none_or(|value| !value.is_finite())
            || scales
                .get(feature)
                .and_then(Value::as_f64)
                .is_none_or(|value| !value.is_finite() || value <= 0.0)
        {
            return Err(MoleculeEvidenceError::FixedEstimator);
        }
    }
    Ok(())
}

fn verify_role_evidence_protocol(
    input: &VerifiedMoleculeModelInputV1,
) -> Result<(), MoleculeEvidenceError> {
    let corpus_count = input
        .corpus
        .get("record_count")
        .and_then(Value::as_u64)
        .ok_or(MoleculeEvidenceError::SplitProtocol)?;
    let dataset_count = input
        .dataset
        .get("record_count")
        .and_then(Value::as_u64)
        .ok_or(MoleculeEvidenceError::SplitProtocol)?;
    let controls: BTreeSet<_> = input
        .benchmark_lock
        .get("controls")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_str)
        .collect();
    if corpus_count < 300
        || dataset_count < 300
        || corpus_count != dataset_count
        || input
            .dataset
            .pointer("/label_policy/independent_labelers")
            .and_then(Value::as_u64)
            != Some(2)
        || input
            .dataset
            .pointer("/label_policy/adjudication_predeclared")
            .and_then(Value::as_bool)
            != Some(true)
        || input
            .dataset
            .pointer("/label_policy/ambiguous_labels_retained")
            .and_then(Value::as_bool)
            != Some(true)
        || ![
            "AMBIGUOUS_LABELS",
            "OUT_OF_DOMAIN",
            "CALIBRATION",
            "EXPERT_NONINFERIORITY",
        ]
        .iter()
        .all(|control| controls.contains(control))
    {
        return Err(MoleculeEvidenceError::SplitProtocol);
    }

    let split: SplitManifestV1 = serde_json::from_value(input.split.clone())
        .map_err(|_| MoleculeEvidenceError::SplitProtocol)?;
    split
        .validate()
        .map_err(|_| MoleculeEvidenceError::SplitProtocol)?;
    if split.dataset_hash != input.dataset_sha256 || split.assignments.len() as u64 != dataset_count
    {
        return Err(MoleculeEvidenceError::SplitProtocol);
    }
    let mut split_names = BTreeSet::new();
    let mut families = BTreeMap::<String, String>::new();
    let mut scaffolds = BTreeMap::<String, String>::new();
    for assignment in &split.assignments {
        if assignment.family.trim().is_empty()
            || assignment.scaffold.trim().is_empty()
            || assignment.split.trim().is_empty()
        {
            return Err(MoleculeEvidenceError::SplitProtocol);
        }
        split_names.insert(assignment.split.as_str());
        if families
            .insert(assignment.family.clone(), assignment.split.clone())
            .is_some_and(|prior| prior != assignment.split)
            || scaffolds
                .insert(assignment.scaffold.clone(), assignment.split.clone())
                .is_some_and(|prior| prior != assignment.split)
        {
            return Err(MoleculeEvidenceError::SplitProtocol);
        }
    }
    if split_names.len() < 2
        || !split_names
            .iter()
            .any(|name| name.contains("HOLDOUT") || name.contains("EXTERNAL"))
    {
        return Err(MoleculeEvidenceError::SplitProtocol);
    }
    Ok(())
}

fn validate_claim_locks(locks: &BTreeMap<String, bool>) -> Result<(), MoleculeEvidenceError> {
    if locks.is_empty() || locks.values().any(|locked| !locked) {
        Err(MoleculeEvidenceError::ClaimLocks)
    } else {
        Ok(())
    }
}

fn require_text(field: &'static str, value: &str) -> Result<(), MoleculeEvidenceError> {
    if value.trim().is_empty() {
        Err(MoleculeEvidenceError::Empty(field))
    } else {
        Ok(())
    }
}

fn require_hash(field: &'static str, value: &str) -> Result<(), MoleculeEvidenceError> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(MoleculeEvidenceError::Hash(field))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{
        EvaluationReceiptV1, PromotionRuleV1, SplitAssignmentV1, EVALUATION_RECEIPT_SCHEMA,
        PROMOTION_POLICY_SCHEMA, SIGNED_MODEL_ARTIFACT_SCHEMA, SPLIT_MANIFEST_SCHEMA,
    };

    struct Fixture {
        context: EngineEvidenceContextV1,
        trust_store: TrustStore,
        registry_hash: String,
    }

    fn digest(label: &str) -> String {
        stable_hash(&Value::String(label.into()))
    }

    fn fixture() -> Fixture {
        let registry_hash = digest("registry");
        let corpus = serde_json::json!({
            "schema": "corpus.v1",
            "record_count": 300,
            "structure_rights_bound": true
        });
        let dataset = serde_json::json!({
            "schema": "dataset.v1",
            "record_count": 300,
            "label_policy": {
                "independent_labelers": 2,
                "adjudication_predeclared": true,
                "ambiguous_labels_retained": true
            }
        });
        let dataset_sha256 = stable_hash(&dataset);
        let assignments = (0..300)
            .map(|index| {
                let group = index / 10;
                SplitAssignmentV1 {
                    row_id: format!("row-{index:03}"),
                    split: if group < 15 {
                        "TRAIN".into()
                    } else {
                        "EXTERNAL_HOLDOUT".into()
                    },
                    source: "chebi-release".into(),
                    family: format!("family-{group:02}"),
                    scaffold: format!("scaffold-{group:02}"),
                    time: "release-2026".into(),
                    lot: "not-applicable".into(),
                }
            })
            .collect();
        let split = serde_json::to_value(SplitManifestV1 {
            schema: SPLIT_MANIFEST_SCHEMA.into(),
            split_id: "role-family-scaffold-held-v1".into(),
            dataset_hash: dataset_sha256.clone(),
            assignment_method: "FAMILY_AND_SCAFFOLD_HELD_SEED_20260717".into(),
            assignments,
        })
        .unwrap();
        let benchmark_lock = serde_json::json!({
            "schema": "lock.v1",
            "dataset_sha256": dataset_sha256,
            "split_sha256": stable_hash(&split),
            "model": "STANDARDIZED_LOGISTIC",
            "controls": [
                "AMBIGUOUS_LABELS",
                "OUT_OF_DOMAIN",
                "CALIBRATION",
                "EXPERT_NONINFERIORITY"
            ]
        });
        let raw_data_hashes = BTreeMap::from([("raw.sdf".into(), digest("raw"))]);
        let rights = vec![RightsRecordV1 {
            source_id: "source".into(),
            license: "CC-BY-4.0".into(),
            status: "ACCEPTED".into(),
            source_url: "https://example.invalid/source".into(),
            restrictions: vec!["named endpoint only".into()],
            eligible_for_derivatives: true,
        }];
        let corpus_sha256 = stable_hash(&corpus);
        let dataset_sha256 = stable_hash(&dataset);
        let split_sha256 = stable_hash(&split);
        let benchmark_lock_sha256 = stable_hash(&benchmark_lock);
        let raw_data_manifest_sha256 =
            stable_hash(&serde_json::to_value(&raw_data_hashes).unwrap());
        let rights_manifest_sha256 = stable_hash(&serde_json::to_value(&rights).unwrap());
        let applicability_domain = serde_json::json!({
            "allowed_roles": ["resin", "hardener"],
            "exclude_dual_role": true,
            "molecular_weight_g_mol": {"min": 30.0, "max": 1000.0}
        });
        let artifact = serde_json::json!({
            "schema": ROLE_MODEL_SCHEMA,
            "module_id": ROLE_RANKER_ID,
            "model_id": "role-logistic-v1",
            "feature_order": ["intercept", "oxirane_ring_count", "reactive_amine_hydrogen_count"],
            "coefficients": [0.0, 2.0, -2.0],
            "standardization": {
                "means": {"oxirane_ring_count": 1.0, "reactive_amine_hydrogen_count": 2.0},
                "scales": {"oxirane_ring_count": 1.0, "reactive_amine_hydrogen_count": 2.0}
            },
            "training_contract": {
                "family": "STANDARDIZED_LOGISTIC",
                "l2_penalty": 1.0,
                "seed": REQUIRED_ROLE_MODEL_SEED,
                "training_only_scaling": true,
                "post_outcome_feature_search": false
            },
            "applicability_domain": applicability_domain,
            "parent_hashes": {
                "corpus": corpus_sha256,
                "dataset": dataset_sha256,
                "split": split_sha256,
                "benchmark_lock": benchmark_lock_sha256,
                "raw_data_manifest": raw_data_manifest_sha256,
                "rights_manifest": rights_manifest_sha256
            }
        });
        let model_key = SigningKey::from_bytes(&[31; 32]);
        let evaluation_key = SigningKey::from_bytes(&[32; 32]);
        let review_key = SigningKey::from_bytes(&[33; 32]);
        let mut model_artifact = SignedModelArtifactV1 {
            schema: SIGNED_MODEL_ARTIFACT_SCHEMA.into(),
            module_id: ROLE_RANKER_ID.into(),
            artifact_sha256: stable_hash(&artifact),
            artifact,
            signature: None,
        };
        model_artifact.sign("model", &model_key).unwrap();
        let model_artifact_sha256 = stable_hash(&serde_json::to_value(&model_artifact).unwrap());

        let mut evaluation_receipt = EvaluationReceiptV1 {
            schema: EVALUATION_RECEIPT_SCHEMA.into(),
            receipt_id: "evaluation".into(),
            module_id: ROLE_RANKER_ID.into(),
            registry_manifest_hash: registry_hash.clone(),
            registry_owned_identity: true,
            artifact_hashes: BTreeMap::from([
                ("model_artifact".into(), model_artifact_sha256.clone()),
                ("corpus".into(), corpus_sha256.clone()),
                ("dataset".into(), dataset_sha256.clone()),
                ("split".into(), split_sha256.clone()),
                ("raw_data_manifest".into(), raw_data_manifest_sha256.clone()),
                ("rights_manifest".into(), rights_manifest_sha256.clone()),
            ]),
            benchmark_lock_hash: benchmark_lock_sha256.clone(),
            metrics: BTreeMap::from([("balanced_accuracy".into(), serde_json::json!(0.91))]),
            confidence_intervals: BTreeMap::new(),
            evidence_tier: EvidenceTier::IndependentExternal,
            decision_use_ceiling: DecisionUse::Ranking,
            passed: true,
            claim_locks: BTreeMap::from([("no_qualification_claim".into(), true)]),
            applicability_limits: vec!["defined single-component structures".into()],
            signature: None,
        };
        evaluation_receipt
            .sign("evaluation", &evaluation_key)
            .unwrap();
        let evaluation_receipt_sha256 =
            stable_hash(&serde_json::to_value(&evaluation_receipt).unwrap());

        let mut review_receipt = IndependentReviewReceiptV1 {
            schema: INDEPENDENT_REVIEW_RECEIPT_SCHEMA.into(),
            receipt_id: "review".into(),
            module_id: ROLE_RANKER_ID.into(),
            registry_manifest_hash: registry_hash.clone(),
            evaluation_receipt_sha256: evaluation_receipt_sha256.clone(),
            model_artifact_sha256: model_artifact_sha256.clone(),
            benchmark_lock_sha256: benchmark_lock_sha256.clone(),
            reviewer_id: "independent-reviewer".into(),
            reviewer_independent: true,
            independent_transfer_passed: true,
            primary_improvement_confirmed: true,
            verifier_reversed_primary: false,
            claim_locks: BTreeMap::from([("no_qualification_claim".into(), true)]),
            applicability_limits: vec!["defined single-component structures".into()],
            signature: None,
        };
        review_receipt.sign("review", &review_key).unwrap();

        let promotion_policy = PromotionPolicyV1 {
            schema: PROMOTION_POLICY_SCHEMA.into(),
            policy_id: "phase-1-policy".into(),
            registry_manifest_hash: registry_hash.clone(),
            default_use: DecisionUse::AuditOnly,
            rules: vec![PromotionRuleV1 {
                module_id: ROLE_RANKER_ID.into(),
                receipt_hash: evaluation_receipt_sha256,
                maximum_use: DecisionUse::Ranking,
            }],
        };
        let promotion_policy_sha256 =
            stable_hash(&serde_json::to_value(&promotion_policy).unwrap());
        let input = VerifiedMoleculeModelInputV1 {
            schema: VERIFIED_MOLECULE_MODEL_INPUT_SCHEMA.into(),
            module_id: ROLE_RANKER_ID.into(),
            model_artifact_sha256,
            corpus_sha256,
            dataset_sha256,
            split_sha256,
            benchmark_lock_sha256,
            raw_data_manifest_sha256,
            rights_manifest_sha256,
            promotion_policy_sha256: promotion_policy_sha256.clone(),
            required_toolkit_version: "2026.03.2".into(),
            applicability_domain,
            model_artifact,
            corpus,
            dataset,
            split,
            benchmark_lock,
            raw_data_hashes,
            rights,
            evaluation_receipt,
            independent_review_receipt: review_receipt,
        };
        let context = EngineEvidenceContextV1 {
            schema: ENGINE_EVIDENCE_CONTEXT_SCHEMA.into(),
            registry_manifest_sha256: registry_hash.clone(),
            promotion_policy_sha256,
            promotion_policy,
            molecule_models: BTreeMap::from([(ROLE_RANKER_ID.into(), input)]),
        };
        let mut trust_store = TrustStore::default();
        for (id, key) in [
            ("model", model_key),
            ("evaluation", evaluation_key),
            ("review", review_key),
        ] {
            trust_store
                .insert(id, key.verifying_key().to_bytes())
                .unwrap();
        }
        Fixture {
            context,
            trust_store,
            registry_hash,
        }
    }

    #[test]
    fn verifies_complete_context_and_binds_candidate_prediction() {
        let fixture = fixture();
        let validated = fixture
            .context
            .verify(&fixture.trust_store, &fixture.registry_hash, "2026.03.2")
            .unwrap();
        let authorization = validated
            .authorize(
                ROLE_RANKER_ID,
                "candidate",
                &digest("candidate"),
                &digest("facts"),
            )
            .unwrap();
        assert!(authorization.validate_binding(
            ROLE_RANKER_ID,
            "candidate",
            &digest("candidate"),
            &digest("facts")
        ));
        assert!(!authorization.validate_binding(
            ROLE_RANKER_ID,
            "other",
            &digest("candidate"),
            &digest("facts")
        ));
        assert_ne!(authorization.signer_ids().1, authorization.signer_ids().2);
    }

    #[test]
    fn rejects_signature_parent_policy_rights_and_claim_lock_tampering() {
        let mutations: Vec<Box<dyn Fn(&mut EngineEvidenceContextV1)>> = vec![
            Box::new(|context| {
                context
                    .molecule_models
                    .get_mut(ROLE_RANKER_ID)
                    .unwrap()
                    .dataset["rows"] = serde_json::json!([9]);
            }),
            Box::new(|context| {
                context
                    .molecule_models
                    .get_mut(ROLE_RANKER_ID)
                    .unwrap()
                    .evaluation_receipt
                    .metrics
                    .insert("tampered".into(), Value::Bool(true));
            }),
            Box::new(|context| {
                context
                    .molecule_models
                    .get_mut(ROLE_RANKER_ID)
                    .unwrap()
                    .rights[0]
                    .eligible_for_derivatives = false;
            }),
            Box::new(|context| {
                context
                    .molecule_models
                    .get_mut(ROLE_RANKER_ID)
                    .unwrap()
                    .evaluation_receipt
                    .claim_locks
                    .clear();
            }),
            Box::new(|context| {
                context.promotion_policy.rules[0].maximum_use = DecisionUse::AuditOnly;
            }),
        ];
        for mutate in mutations {
            let fixture = fixture();
            let mut context = fixture.context;
            mutate(&mut context);
            assert!(context
                .verify(&fixture.trust_store, &fixture.registry_hash, "2026.03.2")
                .is_err());
        }
    }

    #[test]
    fn rejects_toolkit_mismatch_and_revoked_review_key() {
        let fixture = fixture();
        assert!(matches!(
            fixture
                .context
                .verify(&fixture.trust_store, &fixture.registry_hash, "2026.03.1"),
            Err(MoleculeEvidenceError::Toolkit)
        ));
        let mut revoked = fixture.trust_store;
        revoked.revoke("review");
        assert!(fixture
            .context
            .verify(&revoked, &fixture.registry_hash, "2026.03.2")
            .is_err());
    }

    #[test]
    fn rejects_family_or_scaffold_overlap_and_incomplete_label_protocol() {
        let mut overlap_fixture = fixture();
        let input = overlap_fixture
            .context
            .molecule_models
            .get_mut(ROLE_RANKER_ID)
            .unwrap();
        input.split["assignments"][150]["family"] = Value::String("family-00".into());
        assert!(matches!(
            verify_role_evidence_protocol(input),
            Err(MoleculeEvidenceError::SplitProtocol)
        ));

        let mut label_fixture = fixture();
        let input = label_fixture
            .context
            .molecule_models
            .get_mut(ROLE_RANKER_ID)
            .unwrap();
        input.dataset["label_policy"]["independent_labelers"] = serde_json::json!(1);
        assert!(matches!(
            verify_role_evidence_protocol(input),
            Err(MoleculeEvidenceError::SplitProtocol)
        ));
    }
}
