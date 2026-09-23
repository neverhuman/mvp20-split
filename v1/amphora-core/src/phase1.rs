use crate::{sign_dsse, stable_hash, verify_dsse, DsseEnvelope, ScientificOutcomeV1, TrustStore};
use ed25519_dalek::SigningKey;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;
use thiserror::Error;

pub const MODULE_PHASE1_BUNDLE_SCHEMA: &str = "amphora.module-phase1-bundle.v1";
pub const MODULE_PHASE1_EVALUATION_RECEIPT_SCHEMA: &str =
    "amphora.module-phase1-evaluation-receipt.v1";
pub const MODULE_PHASE1_REVIEW_RECEIPT_SCHEMA: &str = "amphora.module-phase1-review-receipt.v1";
pub const MODULE_PHASE1_MOVEMENT_EVENT_SCHEMA: &str = "amphora.module-phase1-movement-event.v1";
pub const MODULE_PHASE1_EVALUATION_PAYLOAD_TYPE: &str =
    "application/vnd.amphora.module-phase1-evaluation-receipt.v1+json";
pub const MODULE_PHASE1_REVIEW_PAYLOAD_TYPE: &str =
    "application/vnd.amphora.module-phase1-review-receipt.v1+json";
pub const PHASE1_REVIEW_METHOD: &str = "INDEPENDENT_EXTERNAL_SCIENTIFIC_REPLAY";
pub const PHASE1_INDEPENDENCE_SCOPE: &str =
    "DATA_SOURCE_ESTIMATOR_EXECUTION_ENVIRONMENT_AND_SIGNING_IDENTITY";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModulePhase1BundleV1 {
    pub schema: String,
    pub module_id: String,
    pub phase0_event_id: String,
    pub phase0_movement_hash: String,
    pub preregistration_hash: String,
    pub preregistration_countersigned_on: String,
    pub dataset_lock_hash: String,
    pub split_lock_hash: String,
    pub estimator_lock_hash: String,
    pub metric_lock_hash: String,
    pub baseline_lock_hash: String,
    pub threshold_lock_hash: String,
    pub uncertainty_lock_hash: String,
    pub applicability_lock_hash: String,
    pub stop_rule_lock_hash: String,
    pub parent_hashes: BTreeMap<String, String>,
    pub independent_external_evidence: bool,
    pub named_best_reproducible_baseline: String,
    pub pre_outcome_locked: bool,
    pub clean_environment_replay_count: u8,
    pub scientific_readiness_ceiling: String,
    pub decision_use_ceiling: String,
    pub ranking_eligible: bool,
    pub claim_locks: BTreeMap<String, bool>,
}

impl ModulePhase1BundleV1 {
    pub fn validate(&self) -> Result<(), Phase1ContractError> {
        schema(&self.schema, MODULE_PHASE1_BUNDLE_SCHEMA)?;
        module_id(&self.module_id)?;
        if !self.phase0_event_id.starts_with("movement-") {
            return Err(Phase1ContractError::Phase0Required);
        }
        let hashes = [
            &self.phase0_movement_hash,
            &self.preregistration_hash,
            &self.dataset_lock_hash,
            &self.split_lock_hash,
            &self.estimator_lock_hash,
            &self.metric_lock_hash,
            &self.baseline_lock_hash,
            &self.threshold_lock_hash,
            &self.uncertainty_lock_hash,
            &self.applicability_lock_hash,
            &self.stop_rule_lock_hash,
        ];
        if hashes.iter().any(|digest| !is_hash(digest))
            || self.parent_hashes.is_empty()
            || hashes.iter().any(|required| {
                !self
                    .parent_hashes
                    .values()
                    .any(|observed| observed == *required)
            })
        {
            return Err(Phase1ContractError::ParentBinding);
        }
        if self.preregistration_countersigned_on.trim().is_empty()
            || !self.independent_external_evidence
            || self.named_best_reproducible_baseline.trim().is_empty()
            || !self.pre_outcome_locked
            || self.clean_environment_replay_count != 2
            || self.scientific_readiness_ceiling != "INDEPENDENTLY_VALIDATED"
            || self.decision_use_ceiling != "AUDIT_ONLY"
            || self.ranking_eligible
            || self.claim_locks.get("no_ranking_authority") != Some(&true)
            || self.claim_locks.get("no_optimizer_authority") != Some(&true)
        {
            return Err(Phase1ContractError::AuthorityOrEvidencePolicy);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ModulePhase1EvaluationReceiptV1 {
    pub schema: String,
    pub receipt_id: String,
    pub module_id: String,
    pub bundle_hash: String,
    pub evaluator_key_id: String,
    pub audit_execution_passed: bool,
    pub independent_external_evidence_verified: bool,
    pub baseline_reproduced: bool,
    pub uncertainty_intervals_complete: bool,
    pub subgroup_checks_complete: bool,
    pub coverage_checks_complete: bool,
    pub applicability_checks_complete: bool,
    pub stop_rule_preserved: bool,
    pub clean_environment_replay_hashes: Vec<String>,
    pub scientific_outcome: ScientificOutcomeV1,
    pub phase1_eligible: bool,
    pub failed_gates: Vec<String>,
    pub retained_failure_results: Vec<String>,
    pub metrics: BTreeMap<String, Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<DsseEnvelope>,
}

impl ModulePhase1EvaluationReceiptV1 {
    pub fn validate(&self) -> Result<(), Phase1ContractError> {
        schema(&self.schema, MODULE_PHASE1_EVALUATION_RECEIPT_SCHEMA)?;
        module_id(&self.module_id)?;
        if self.receipt_id.trim().is_empty()
            || self.evaluator_key_id.trim().is_empty()
            || !is_hash(&self.bundle_hash)
            || self.clean_environment_replay_hashes.len() != 2
            || self
                .clean_environment_replay_hashes
                .iter()
                .any(|digest| !is_hash(digest))
            || self.clean_environment_replay_hashes[0] != self.clean_environment_replay_hashes[1]
        {
            return Err(Phase1ContractError::EvaluationCompleteness);
        }
        let gates_pass = self.audit_execution_passed
            && self.independent_external_evidence_verified
            && self.baseline_reproduced
            && self.uncertainty_intervals_complete
            && self.subgroup_checks_complete
            && self.coverage_checks_complete
            && self.applicability_checks_complete
            && self.stop_rule_preserved
            && self.failed_gates.is_empty()
            && self.scientific_outcome == ScientificOutcomeV1::Passed;
        if self.phase1_eligible != gates_pass {
            return Err(Phase1ContractError::EligibilityMismatch);
        }
        if self.scientific_outcome == ScientificOutcomeV1::Failed
            && self.retained_failure_results.is_empty()
        {
            return Err(Phase1ContractError::FailureNotRetained);
        }
        Ok(())
    }

    fn unsigned_bytes(&self) -> Result<Vec<u8>, Phase1ContractError> {
        let mut unsigned = self.clone();
        unsigned.signature = None;
        canonical_bytes(&unsigned)
    }

    pub fn sign(&mut self, key_id: &str, key: &SigningKey) -> Result<(), Phase1ContractError> {
        if self.evaluator_key_id != key_id {
            return Err(Phase1ContractError::SignerIdentity);
        }
        self.validate()?;
        self.signature = Some(sign_dsse(
            MODULE_PHASE1_EVALUATION_PAYLOAD_TYPE,
            &self.unsigned_bytes()?,
            key_id,
            key,
        ));
        Ok(())
    }

    pub fn verify_signature(&self, trust: &TrustStore) -> Result<String, Phase1ContractError> {
        self.validate()?;
        let envelope = self
            .signature
            .as_ref()
            .ok_or(Phase1ContractError::Unsigned)?;
        if envelope.payload_type != MODULE_PHASE1_EVALUATION_PAYLOAD_TYPE {
            return Err(Phase1ContractError::SignaturePayload);
        }
        let verified = verify_dsse(envelope, trust)?;
        if verified.key_id != self.evaluator_key_id || verified.payload != self.unsigned_bytes()? {
            return Err(Phase1ContractError::SignaturePayload);
        }
        Ok(verified.key_id)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ModulePhase1ReviewReceiptV1 {
    pub schema: String,
    pub review_id: String,
    pub module_id: String,
    pub bundle_hash: String,
    pub evaluation_receipt_hash: String,
    pub evaluator_key_id: String,
    pub reviewer_key_id: String,
    pub review_method: String,
    pub independence_scope: String,
    pub parent_hashes_current: bool,
    pub preregistration_unchanged: bool,
    pub estimator_and_split_unchanged: bool,
    pub independent_replays_identical: bool,
    pub uncertainty_and_subgroups_verified: bool,
    pub claim_locks_preserved: bool,
    pub accepted_for_phase1: bool,
    pub findings: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<DsseEnvelope>,
}

impl ModulePhase1ReviewReceiptV1 {
    pub fn validate(&self) -> Result<(), Phase1ContractError> {
        schema(&self.schema, MODULE_PHASE1_REVIEW_RECEIPT_SCHEMA)?;
        module_id(&self.module_id)?;
        if self.review_id.trim().is_empty()
            || !is_hash(&self.bundle_hash)
            || !is_hash(&self.evaluation_receipt_hash)
            || self.evaluator_key_id.trim().is_empty()
            || self.reviewer_key_id.trim().is_empty()
            || self.evaluator_key_id == self.reviewer_key_id
        {
            return Err(Phase1ContractError::SameOrInvalidSigner);
        }
        if self.review_method != PHASE1_REVIEW_METHOD
            || self.independence_scope != PHASE1_INDEPENDENCE_SCOPE
        {
            return Err(Phase1ContractError::ReviewBoundary);
        }
        let controls = self.parent_hashes_current
            && self.preregistration_unchanged
            && self.estimator_and_split_unchanged
            && self.independent_replays_identical
            && self.uncertainty_and_subgroups_verified
            && self.claim_locks_preserved;
        if self.accepted_for_phase1 != controls {
            return Err(Phase1ContractError::ReviewAcceptance);
        }
        Ok(())
    }

    fn unsigned_bytes(&self) -> Result<Vec<u8>, Phase1ContractError> {
        let mut unsigned = self.clone();
        unsigned.signature = None;
        canonical_bytes(&unsigned)
    }

    pub fn sign(&mut self, key_id: &str, key: &SigningKey) -> Result<(), Phase1ContractError> {
        if self.reviewer_key_id != key_id {
            return Err(Phase1ContractError::SignerIdentity);
        }
        self.validate()?;
        self.signature = Some(sign_dsse(
            MODULE_PHASE1_REVIEW_PAYLOAD_TYPE,
            &self.unsigned_bytes()?,
            key_id,
            key,
        ));
        Ok(())
    }

    pub fn verify_signature(&self, trust: &TrustStore) -> Result<String, Phase1ContractError> {
        self.validate()?;
        let envelope = self
            .signature
            .as_ref()
            .ok_or(Phase1ContractError::Unsigned)?;
        if envelope.payload_type != MODULE_PHASE1_REVIEW_PAYLOAD_TYPE {
            return Err(Phase1ContractError::SignaturePayload);
        }
        let verified = verify_dsse(envelope, trust)?;
        if verified.key_id != self.reviewer_key_id || verified.payload != self.unsigned_bytes()? {
            return Err(Phase1ContractError::SignaturePayload);
        }
        Ok(verified.key_id)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModulePhase1MovementEventV1 {
    pub schema: String,
    pub event_id: String,
    pub module_id: String,
    pub previous_phase: String,
    pub current_phase: String,
    pub effective_status_change: String,
    pub phase0_event_id: String,
    pub phase0_movement_hash: String,
    pub bundle_hash: String,
    pub evaluation_receipt_hash: String,
    pub review_receipt_hash: String,
    pub parent_hashes: BTreeMap<String, String>,
    pub evaluator_key_id: String,
    pub reviewer_key_id: String,
    pub scientific_readiness: String,
    pub decision_use_ceiling: String,
    pub ranking_eligible: bool,
    pub applicability_domain: Vec<String>,
    pub claim_locks: BTreeMap<String, bool>,
}

impl ModulePhase1MovementEventV1 {
    pub fn validate(&self) -> Result<(), Phase1ContractError> {
        schema(&self.schema, MODULE_PHASE1_MOVEMENT_EVENT_SCHEMA)?;
        module_id(&self.module_id)?;
        if self.previous_phase != "PHASE_0"
            || self.current_phase != "PHASE_1"
            || self.effective_status_change != "PHASE_0->PHASE_1"
            || !self.phase0_event_id.starts_with("movement-")
            || self.scientific_readiness != "INDEPENDENTLY_VALIDATED"
            || self.decision_use_ceiling != "AUDIT_ONLY"
            || self.ranking_eligible
            || self.applicability_domain.is_empty()
            || self.claim_locks.get("no_ranking_authority") != Some(&true)
            || self.claim_locks.get("no_optimizer_authority") != Some(&true)
            || self.evaluator_key_id == self.reviewer_key_id
        {
            return Err(Phase1ContractError::InvalidMovement);
        }
        for digest in [
            &self.phase0_movement_hash,
            &self.bundle_hash,
            &self.evaluation_receipt_hash,
            &self.review_receipt_hash,
        ] {
            if !is_hash(digest) {
                return Err(Phase1ContractError::ParentBinding);
            }
        }
        let required = [
            &self.phase0_movement_hash,
            &self.bundle_hash,
            &self.evaluation_receipt_hash,
            &self.review_receipt_hash,
        ];
        if self.parent_hashes.is_empty()
            || required.iter().any(|digest| {
                !self
                    .parent_hashes
                    .values()
                    .any(|observed| observed == *digest)
            })
            || self.event_id != self.computed_event_id()?
        {
            return Err(Phase1ContractError::InvalidMovement);
        }
        Ok(())
    }

    pub fn computed_event_id(&self) -> Result<String, Phase1ContractError> {
        let mut unsigned = self.clone();
        unsigned.event_id.clear();
        Ok(format!(
            "phase1-movement-{}",
            stable_hash(&serde_json::to_value(unsigned)?)
        ))
    }

    pub fn bind_event_id(&mut self) -> Result<(), Phase1ContractError> {
        self.event_id = self.computed_event_id()?;
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Phase1ModuleStatusV1 {
    pub module_id: String,
    pub phase: String,
    pub scientific_readiness: String,
    pub decision_use_ceiling: String,
    pub ranking_eligible: bool,
    pub phase0_event_id: Option<String>,
    pub phase1_event_id: Option<String>,
    pub prepared: bool,
    pub evaluation_signed: bool,
    pub review_signed: bool,
    pub failed_gates: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Phase1PortfolioStatusV1 {
    pub schema: String,
    pub module_count: usize,
    pub phase1_count: usize,
    pub phase0_count: usize,
    pub pre_phase0_count: usize,
    pub ranking_enabled: bool,
    pub modules: Vec<Phase1ModuleStatusV1>,
}

fn canonical_bytes<T: Serialize>(value: &T) -> Result<Vec<u8>, Phase1ContractError> {
    Ok(serde_json::to_vec(&crate::canonicalize(
        &serde_json::to_value(value)?,
    ))?)
}

fn schema(actual: &str, expected: &'static str) -> Result<(), Phase1ContractError> {
    if actual == expected {
        Ok(())
    } else {
        Err(Phase1ContractError::Schema {
            actual: actual.into(),
            expected,
        })
    }
}

fn module_id(value: &str) -> Result<(), Phase1ContractError> {
    if value.starts_with("amphora-")
        && value
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-')
    {
        Ok(())
    } else {
        Err(Phase1ContractError::ModuleId)
    }
}

fn is_hash(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

#[derive(Debug, Error)]
pub enum Phase1ContractError {
    #[error("unexpected schema {actual}; expected {expected}")]
    Schema {
        actual: String,
        expected: &'static str,
    },
    #[error("invalid module ID")]
    ModuleId,
    #[error("a current Phase-0 movement is required")]
    Phase0Required,
    #[error("Phase-1 parent hashes are incomplete or invalid")]
    ParentBinding,
    #[error("Phase-1 independent-evidence or zero-authority policy is invalid")]
    AuthorityOrEvidencePolicy,
    #[error("Phase-1 evaluation is incomplete or its two replays differ")]
    EvaluationCompleteness,
    #[error("Phase-1 eligibility does not match all locked gates")]
    EligibilityMismatch,
    #[error("failed Phase-1 result was not retained")]
    FailureNotRetained,
    #[error("evaluator and reviewer must be distinct valid identities")]
    SameOrInvalidSigner,
    #[error("Phase-1 independent review boundary is invalid")]
    ReviewBoundary,
    #[error("Phase-1 review acceptance does not match review controls")]
    ReviewAcceptance,
    #[error("signing key does not match receipt identity")]
    SignerIdentity,
    #[error("signed Phase-1 receipt is absent")]
    Unsigned,
    #[error("Phase-1 signature payload binding is invalid")]
    SignaturePayload,
    #[error("Phase-1 movement is not exactly PHASE_0->PHASE_1")]
    InvalidMovement,
    #[error(transparent)]
    Verification(#[from] crate::VerificationError),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
}

#[cfg(test)]
mod tests {
    use super::*;

    fn evaluation() -> ModulePhase1EvaluationReceiptV1 {
        ModulePhase1EvaluationReceiptV1 {
            schema: MODULE_PHASE1_EVALUATION_RECEIPT_SCHEMA.into(),
            receipt_id: "receipt-1".into(),
            module_id: "amphora-example".into(),
            bundle_hash: "a".repeat(64),
            evaluator_key_id: "external-evaluator".into(),
            audit_execution_passed: true,
            independent_external_evidence_verified: true,
            baseline_reproduced: true,
            uncertainty_intervals_complete: true,
            subgroup_checks_complete: true,
            coverage_checks_complete: true,
            applicability_checks_complete: true,
            stop_rule_preserved: true,
            clean_environment_replay_hashes: vec!["b".repeat(64), "b".repeat(64)],
            scientific_outcome: ScientificOutcomeV1::Passed,
            phase1_eligible: true,
            failed_gates: Vec::new(),
            retained_failure_results: Vec::new(),
            metrics: BTreeMap::new(),
            signature: None,
        }
    }

    #[test]
    fn altered_replay_fails() {
        let mut receipt = evaluation();
        receipt.clean_environment_replay_hashes[1] = "c".repeat(64);
        assert!(receipt.validate().is_err());
    }

    #[test]
    fn failed_confidence_gate_cannot_be_phase1_eligible() {
        let mut receipt = evaluation();
        receipt.uncertainty_intervals_complete = false;
        assert!(receipt.validate().is_err());
        receipt.phase1_eligible = false;
        assert!(receipt.validate().is_ok());
    }

    #[test]
    fn failed_science_is_retained_without_authority_change() {
        let mut receipt = evaluation();
        receipt.scientific_outcome = ScientificOutcomeV1::Failed;
        receipt.phase1_eligible = false;
        assert!(receipt.validate().is_err());
        receipt
            .retained_failure_results
            .push("locked-result.json".into());
        assert!(receipt.validate().is_ok());
    }
}
