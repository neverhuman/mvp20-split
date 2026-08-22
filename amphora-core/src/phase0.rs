use crate::{canonicalize, sign_dsse, stable_hash, verify_dsse, DsseEnvelope, TrustStore};
use ed25519_dalek::SigningKey;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::path::{Component, Path};
use thiserror::Error;

pub const MODULE_PHASE0_BUNDLE_SCHEMA: &str = "amphora.module-phase0-bundle.v1";
pub const MODULE_PHASE0_EVALUATION_RECEIPT_SCHEMA: &str =
    "amphora.module-phase0-evaluation-receipt.v1";
pub const MODULE_PHASE0_REVIEW_RECEIPT_SCHEMA: &str = "amphora.module-phase0-review-receipt.v1";
pub const MODULE_MOVEMENT_EVENT_SCHEMA: &str = "amphora.module-movement-event.v1";
pub const MODULE_CLAIM_CONTRACT_SCHEMA: &str = "amphora.module-claim-contract.v1";
pub const MODULE_PHASE0_SUPERSESSION_SCHEMA: &str = "amphora.module-phase0-supersession.v1";
pub const MODULE_PHASE0_PREPARATION_REVISION_SCHEMA: &str =
    "amphora.module-phase0-preparation-revision.v1";
pub const MODULE_PHASE0_PREPARATION_LEDGER_SCHEMA: &str =
    "amphora.module-phase0-preparation-ledger.v1";
pub const DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA: &str =
    "amphora.deterministic-control-diagnostic.v1";
pub const MODULE_REGISTRY_SUCCESSION_SCHEMA: &str = "amphora.module-registry-succession.v1";
pub const MODULE_REGISTRY_SUCCESSION_CHAIN_SCHEMA: &str =
    "amphora.module-registry-succession-chain.v1";
pub const MODULE_PHASE0_EVALUATION_PAYLOAD_TYPE: &str =
    "application/vnd.amphora.module-phase0-evaluation-receipt.v1+json";
pub const MODULE_PHASE0_REVIEW_PAYLOAD_TYPE: &str =
    "application/vnd.amphora.module-phase0-review-receipt.v1+json";
pub const PHASE0_REVIEW_METHOD: &str = "AUTOMATED_INDEPENDENT_REIMPLEMENTATION";
pub const PHASE0_INDEPENDENCE_SCOPE: &str = "CODE_PATH_AND_SIGNING_IDENTITY";

pub const REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS: [&str; 10] = [
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

const REGISTRY_SUCCESSION_EDIT_FIELDS: [&str; 3] = [
    "readiness",
    "operational_readiness",
    "non_blocking_claim_locks",
];

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct DeterministicControlDiagnosticV1 {
    pub schema: String,
    pub module_id: String,
    pub implementation_readiness: String,
    pub expected_fixture_outcomes: BTreeMap<String, String>,
    pub observed_fixture_outcomes: BTreeMap<String, String>,
    pub positive_control_count: u64,
    pub negative_control_count: u64,
    pub zero_authority_assertions: BTreeMap<String, bool>,
    pub details: BTreeMap<String, Value>,
    pub passed: bool,
}

impl DeterministicControlDiagnosticV1 {
    pub fn validate(&self) -> Result<(), Phase0ContractError> {
        schema(&self.schema, DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA)?;
        module_id(&self.module_id)?;
        if self.implementation_readiness != "COMPLETE"
            || self.expected_fixture_outcomes.is_empty()
            || self.expected_fixture_outcomes != self.observed_fixture_outcomes
            || self.positive_control_count == 0
            || self.negative_control_count == 0
            || self.details.is_empty()
        {
            return Err(Phase0ContractError::InvalidDeterministicDiagnostic);
        }
        let positive = self
            .expected_fixture_outcomes
            .values()
            .filter(|outcome| outcome.as_str() == "ACCEPT")
            .count() as u64;
        let negative = self
            .expected_fixture_outcomes
            .values()
            .filter(|outcome| outcome.as_str() == "REJECT")
            .count() as u64;
        if positive == 0
            || negative == 0
            || positive > self.positive_control_count
            || negative > self.negative_control_count
            || positive + negative != self.expected_fixture_outcomes.len() as u64
            || !self.passed
        {
            return Err(Phase0ContractError::InvalidDeterministicDiagnostic);
        }
        if let Some(result_digest) = self.details.get("result_digest").and_then(Value::as_str) {
            hash("deterministic diagnostic result_digest", result_digest)?;
            let mut details = self.details.clone();
            details.remove("result_digest");
            let expected = stable_hash(&serde_json::json!({
                "module_id": self.module_id,
                "expected_fixture_outcomes": self.expected_fixture_outcomes,
                "observed_fixture_outcomes": self.observed_fixture_outcomes,
                "positive_control_count": self.positive_control_count,
                "negative_control_count": self.negative_control_count,
                "zero_authority_assertions": self.zero_authority_assertions,
                "details": details,
                "passed": self.passed,
            }));
            if result_digest != expected {
                return Err(Phase0ContractError::InvalidDeterministicDiagnostic);
            }
        }
        if let Some(fixture_hashes) = self.details.get("fixture_hashes") {
            let fixture_hashes = fixture_hashes
                .as_object()
                .ok_or(Phase0ContractError::InvalidDeterministicDiagnostic)?;
            if fixture_hashes.is_empty()
                || fixture_hashes.values().any(|digest| {
                    digest
                        .as_str()
                        .is_none_or(|digest| hash("fixture hash", digest).is_err())
                })
            {
                return Err(Phase0ContractError::InvalidDeterministicDiagnostic);
            }
        }
        claim_locks(&self.zero_authority_assertions)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct RegistryManifestRefV1 {
    pub path: String,
    pub sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct RegistrySuccessionEditV1 {
    pub module_id: String,
    pub field: String,
    pub old_value: Value,
    pub new_value: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModuleRegistrySuccessionV1 {
    pub schema: String,
    pub succession_id: String,
    pub predecessor: RegistryManifestRefV1,
    pub successor: RegistryManifestRefV1,
    pub edits: Vec<RegistrySuccessionEditV1>,
    pub no_scientific_change: bool,
    pub no_rights_change: bool,
    pub no_ranking_change: bool,
    pub no_solver_change: bool,
    pub no_authority_change: bool,
}

impl ModuleRegistrySuccessionV1 {
    pub fn validate(&self) -> Result<(), Phase0ContractError> {
        schema(&self.schema, MODULE_REGISTRY_SUCCESSION_SCHEMA)?;
        for manifest in [&self.predecessor, &self.successor] {
            hash("registry manifest", &manifest.sha256)?;
            if manifest.path != format!("registry/archive/{}/module-manifest.json", manifest.sha256)
            {
                return Err(Phase0ContractError::InvalidRegistrySuccession);
            }
        }
        if self.predecessor.sha256 == self.successor.sha256
            || self.edits.is_empty()
            || !self.no_scientific_change
            || !self.no_rights_change
            || !self.no_ranking_change
            || !self.no_solver_change
            || !self.no_authority_change
        {
            return Err(Phase0ContractError::InvalidRegistrySuccession);
        }
        let mut unique = BTreeSet::new();
        for edit in &self.edits {
            module_id(&edit.module_id)?;
            if !REGISTRY_SUCCESSION_EDIT_FIELDS.contains(&edit.field.as_str())
                || edit.old_value == edit.new_value
                || !unique.insert((edit.module_id.as_str(), edit.field.as_str()))
            {
                return Err(Phase0ContractError::InvalidRegistrySuccession);
            }
        }
        if self.succession_id != self.computed_succession_id()? {
            return Err(Phase0ContractError::InvalidRegistrySuccession);
        }
        Ok(())
    }

    pub fn computed_succession_id(&self) -> Result<String, Phase0ContractError> {
        let mut unsigned = self.clone();
        unsigned.succession_id.clear();
        Ok(format!(
            "registry-succession-{}",
            stable_hash(&serde_json::to_value(unsigned)?)
        ))
    }

    pub fn bind_succession_id(&mut self) -> Result<(), Phase0ContractError> {
        self.succession_id = self.computed_succession_id()?;
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct RegistrySuccessionRecordRefV1 {
    pub record_sha256: String,
    pub succession_id: String,
    pub predecessor_sha256: String,
    pub successor_sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModuleRegistrySuccessionChainV1 {
    pub schema: String,
    pub genesis_manifest_sha256: String,
    pub head_manifest_sha256: String,
    pub records: Vec<RegistrySuccessionRecordRefV1>,
}

impl ModuleRegistrySuccessionChainV1 {
    pub fn validate(&self) -> Result<(), Phase0ContractError> {
        schema(&self.schema, MODULE_REGISTRY_SUCCESSION_CHAIN_SCHEMA)?;
        hash("genesis manifest", &self.genesis_manifest_sha256)?;
        hash("head manifest", &self.head_manifest_sha256)?;
        if self.records.is_empty()
            || self.genesis_manifest_sha256 == self.head_manifest_sha256
            || self
                .records
                .first()
                .map(|record| record.predecessor_sha256.as_str())
                != Some(self.genesis_manifest_sha256.as_str())
            || self
                .records
                .last()
                .map(|record| record.successor_sha256.as_str())
                != Some(self.head_manifest_sha256.as_str())
        {
            return Err(Phase0ContractError::InvalidRegistrySuccession);
        }
        let mut record_hashes = BTreeSet::new();
        let mut succession_ids = BTreeSet::new();
        let mut manifests = BTreeSet::from([self.genesis_manifest_sha256.as_str()]);
        let mut previous = self.genesis_manifest_sha256.as_str();
        for record in &self.records {
            hash("succession record", &record.record_sha256)?;
            hash("succession predecessor", &record.predecessor_sha256)?;
            hash("succession successor", &record.successor_sha256)?;
            if !record.succession_id.starts_with("registry-succession-")
                || record.predecessor_sha256 != previous
                || record.predecessor_sha256 == record.successor_sha256
                || !record_hashes.insert(record.record_sha256.as_str())
                || !succession_ids.insert(record.succession_id.as_str())
                || !manifests.insert(record.successor_sha256.as_str())
            {
                return Err(Phase0ContractError::InvalidRegistrySuccession);
            }
            previous = record.successor_sha256.as_str();
        }
        Ok(())
    }
}

const REQUIRED_PROHIBITIONS: [&str; 10] = [
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

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ScientificOutcomeV1 {
    Passed,
    Failed,
    NotApplicable,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModuleClaimContractV1 {
    pub schema: String,
    pub module_id: String,
    pub registry_manifest_hash: String,
    pub module_class: String,
    pub scientific_readiness_ceiling: String,
    pub decision_use_ceiling: String,
    pub applicability_domain: Vec<String>,
    pub abstain_outside_applicability: bool,
    pub claim_locks: BTreeMap<String, bool>,
    pub prohibited_authorities: Vec<String>,
}

impl ModuleClaimContractV1 {
    pub fn validate(&self) -> Result<(), Phase0ContractError> {
        schema(&self.schema, MODULE_CLAIM_CONTRACT_SCHEMA)?;
        module_id(&self.module_id)?;
        hash("registry_manifest_hash", &self.registry_manifest_hash)?;
        module_class(&self.module_class)?;
        readiness(&self.module_class, &self.scientific_readiness_ceiling)?;
        audit_only(&self.decision_use_ceiling)?;
        nonempty_strings("applicability_domain", &self.applicability_domain)?;
        if !self.abstain_outside_applicability {
            return Err(Phase0ContractError::AbstentionRequired);
        }
        claim_locks(&self.claim_locks)?;
        let prohibited: BTreeSet<_> = self
            .prohibited_authorities
            .iter()
            .map(String::as_str)
            .collect();
        for required in REQUIRED_PROHIBITIONS {
            if !prohibited.contains(required) {
                return Err(Phase0ContractError::MissingAuthorityProhibition(
                    required.into(),
                ));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModulePhase0BundleV1 {
    pub schema: String,
    pub module_id: String,
    pub module_class: String,
    pub registry_manifest_hash: String,
    pub source_lock_hash: String,
    pub dataset_manifest_hash: String,
    pub split_manifest_hash: String,
    pub benchmark_lock_hash: String,
    pub promotion_policy_hash: String,
    pub claim_contract_hash: String,
    pub technical_dossier_hash: String,
    pub prior_art_hash: String,
    pub disclosure_log_hash: String,
    pub parents: BTreeMap<String, String>,
    pub toolkit_versions: BTreeMap<String, String>,
    pub applicability_domain: Vec<String>,
    pub claim_locks: BTreeMap<String, bool>,
    pub review_packet_blinded: bool,
}

impl ModulePhase0BundleV1 {
    pub fn validate(&self) -> Result<(), Phase0ContractError> {
        schema(&self.schema, MODULE_PHASE0_BUNDLE_SCHEMA)?;
        module_id(&self.module_id)?;
        module_class(&self.module_class)?;
        let hashes = [
            ("registry_manifest_hash", &self.registry_manifest_hash),
            ("source_lock_hash", &self.source_lock_hash),
            ("dataset_manifest_hash", &self.dataset_manifest_hash),
            ("split_manifest_hash", &self.split_manifest_hash),
            ("benchmark_lock_hash", &self.benchmark_lock_hash),
            ("promotion_policy_hash", &self.promotion_policy_hash),
            ("claim_contract_hash", &self.claim_contract_hash),
            ("technical_dossier_hash", &self.technical_dossier_hash),
            ("prior_art_hash", &self.prior_art_hash),
            ("disclosure_log_hash", &self.disclosure_log_hash),
        ];
        for (name, value) in hashes {
            hash(name, value)?;
        }
        parent_hashes(&self.parents)?;
        for required in [
            &self.source_lock_hash,
            &self.dataset_manifest_hash,
            &self.split_manifest_hash,
            &self.benchmark_lock_hash,
            &self.promotion_policy_hash,
            &self.claim_contract_hash,
            &self.technical_dossier_hash,
            &self.prior_art_hash,
            &self.disclosure_log_hash,
        ] {
            if !self
                .parents
                .values()
                .any(|observed| observed == required.as_str())
            {
                return Err(Phase0ContractError::MissingParentHash((*required).clone()));
            }
        }
        if self.toolkit_versions.is_empty()
            || self
                .toolkit_versions
                .iter()
                .any(|(tool, version)| tool.trim().is_empty() || version.trim().is_empty())
        {
            return Err(Phase0ContractError::Empty("toolkit_versions"));
        }
        nonempty_strings("applicability_domain", &self.applicability_domain)?;
        claim_locks(&self.claim_locks)?;
        if !self.review_packet_blinded {
            return Err(Phase0ContractError::ReviewPacketNotBlinded);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ModulePhase0EvaluationReceiptV1 {
    pub schema: String,
    pub receipt_id: String,
    pub module_id: String,
    pub module_class: String,
    pub bundle_hash: String,
    pub bundle_parent_hashes: BTreeMap<String, String>,
    pub evaluator_key_id: String,
    pub audit_execution_passed: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub benchmark_execution_complete: Option<bool>,
    pub scientific_outcome: ScientificOutcomeV1,
    pub phase0_eligible: bool,
    pub scientific_readiness: String,
    pub decision_use_ceiling: String,
    pub claim_lock_hash: String,
    pub applicability_domain: Vec<String>,
    pub failed_gates: Vec<String>,
    pub retained_negative_results: Vec<String>,
    pub replay_hash: String,
    pub metrics: BTreeMap<String, Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<DsseEnvelope>,
}

impl ModulePhase0EvaluationReceiptV1 {
    pub fn validate(&self) -> Result<(), Phase0ContractError> {
        schema(&self.schema, MODULE_PHASE0_EVALUATION_RECEIPT_SCHEMA)?;
        id("receipt_id", &self.receipt_id)?;
        module_id(&self.module_id)?;
        module_class(&self.module_class)?;
        signer(&self.evaluator_key_id)?;
        hash("bundle_hash", &self.bundle_hash)?;
        hash("claim_lock_hash", &self.claim_lock_hash)?;
        hash("replay_hash", &self.replay_hash)?;
        parent_hashes(&self.bundle_parent_hashes)?;
        audit_only(&self.decision_use_ceiling)?;
        readiness(&self.module_class, &self.scientific_readiness)?;
        nonempty_strings("applicability_domain", &self.applicability_domain)?;
        if self.phase0_eligible
            != (self.audit_execution_passed
                && self.benchmark_execution_complete.unwrap_or(true)
                && self.failed_gates.is_empty())
        {
            return Err(Phase0ContractError::EligibilityMismatch);
        }
        match (self.module_class.as_str(), self.scientific_outcome) {
            ("DETERMINISTIC_CONTROL", ScientificOutcomeV1::NotApplicable)
            | ("SCIENTIFIC_OR_EVIDENCE", ScientificOutcomeV1::Passed) => {}
            ("SCIENTIFIC_OR_EVIDENCE", ScientificOutcomeV1::Failed)
                if !self.retained_negative_results.is_empty() => {}
            ("SCIENTIFIC_OR_EVIDENCE", ScientificOutcomeV1::Failed) => {
                return Err(Phase0ContractError::NegativeResultNotRetained)
            }
            _ => return Err(Phase0ContractError::OutcomeClassMismatch),
        }
        Ok(())
    }

    fn unsigned_bytes(&self) -> Result<Vec<u8>, Phase0ContractError> {
        let mut unsigned = self.clone();
        unsigned.signature = None;
        canonical_bytes(&unsigned)
    }

    pub fn sign(&mut self, key_id: &str, key: &SigningKey) -> Result<(), Phase0ContractError> {
        if self.evaluator_key_id != key_id {
            return Err(Phase0ContractError::SignerIdentityMismatch);
        }
        self.validate()?;
        self.signature = Some(sign_dsse(
            MODULE_PHASE0_EVALUATION_PAYLOAD_TYPE,
            &self.unsigned_bytes()?,
            key_id,
            key,
        ));
        Ok(())
    }

    pub fn verify_signature(&self, trust: &TrustStore) -> Result<String, Phase0ContractError> {
        self.validate()?;
        let envelope = self
            .signature
            .as_ref()
            .ok_or(Phase0ContractError::Unsigned)?;
        if envelope.payload_type != MODULE_PHASE0_EVALUATION_PAYLOAD_TYPE {
            return Err(Phase0ContractError::SignaturePayload);
        }
        let verified = verify_dsse(envelope, trust)?;
        if verified.payload != self.unsigned_bytes()? || verified.key_id != self.evaluator_key_id {
            return Err(Phase0ContractError::SignaturePayload);
        }
        Ok(verified.key_id)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModulePhase0SupersessionV1 {
    pub schema: String,
    pub supersession_id: String,
    pub module_id: String,
    pub reason: String,
    pub archive_root: String,
    pub archived_artifacts: BTreeMap<String, String>,
    pub unsigned_preparation_only: bool,
    pub authority_transferred: bool,
}

impl ModulePhase0SupersessionV1 {
    pub fn validate(&self) -> Result<(), Phase0ContractError> {
        schema(&self.schema, MODULE_PHASE0_SUPERSESSION_SCHEMA)?;
        module_id(&self.module_id)?;
        if self.reason != "STALE_UNSIGNED_PREPARATION_REISSUE"
            || !self.unsigned_preparation_only
            || self.authority_transferred
            || self.archived_artifacts.is_empty()
        {
            return Err(Phase0ContractError::InvalidSupersession);
        }
        parent_hashes(&self.archived_artifacts)?;
        let expected_id = self.computed_supersession_id()?;
        if self.supersession_id != expected_id
            || self.archive_root != format!("evidence/superseded/{expected_id}")
        {
            return Err(Phase0ContractError::InvalidSupersession);
        }
        if self
            .archived_artifacts
            .keys()
            .any(|relative| !relative.starts_with("phase0/") && !relative.starts_with("ip/"))
        {
            return Err(Phase0ContractError::InvalidSupersession);
        }
        Ok(())
    }

    pub fn computed_supersession_id(&self) -> Result<String, Phase0ContractError> {
        let seed = serde_json::json!({
            "module_id": self.module_id,
            "reason": self.reason,
            "archived_artifacts": self.archived_artifacts,
            "unsigned_preparation_only": self.unsigned_preparation_only,
            "authority_transferred": self.authority_transferred,
        });
        Ok(format!("supersession-{}", stable_hash(&seed)))
    }

    pub fn bind_supersession_id(&mut self) -> Result<(), Phase0ContractError> {
        self.supersession_id = self.computed_supersession_id()?;
        self.archive_root = format!("evidence/superseded/{}", self.supersession_id);
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModulePhase0PreparationRevisionV1 {
    pub schema: String,
    pub revision_id: String,
    pub module_id: String,
    pub revision_number: u64,
    pub parent_revision_id: Option<String>,
    pub supersession_id: String,
    pub supersession_path: String,
    pub supersession_sha256: String,
    pub archived_bundle_sha256: String,
    pub unsigned_preparation_only: bool,
}

impl ModulePhase0PreparationRevisionV1 {
    pub fn bind_revision_id(&mut self) -> Result<(), Phase0ContractError> {
        self.revision_id = self.computed_revision_id()?;
        Ok(())
    }

    pub fn computed_revision_id(&self) -> Result<String, Phase0ContractError> {
        let mut value = self.clone();
        value.revision_id.clear();
        Ok(format!(
            "preparation-revision-{}",
            stable_hash(&serde_json::to_value(value)?)
        ))
    }

    pub fn validate(&self) -> Result<(), Phase0ContractError> {
        module_id(&self.module_id)?;
        hash("supersession_sha256", &self.supersession_sha256)?;
        hash("archived_bundle_sha256", &self.archived_bundle_sha256)?;
        if self.schema != MODULE_PHASE0_PREPARATION_REVISION_SCHEMA
            || self.revision_number == 0
            || !self.unsigned_preparation_only
            || !self.supersession_id.starts_with("supersession-")
            || self.supersession_path
                != format!(
                    "{}/supersession.v1.json",
                    self.supersession_id.replacen(
                        "supersession-",
                        "evidence/superseded/supersession-",
                        1
                    )
                )
            || self.parent_revision_id.as_ref().is_some_and(|parent| {
                !parent.starts_with("preparation-revision-") || parent.len() != 85
            })
            || self.revision_id != self.computed_revision_id()?
        {
            return Err(Phase0ContractError::InvalidPreparationRevision);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct PreparationRevisionRefV1 {
    pub revision_id: String,
    pub path: String,
    pub sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModulePhase0PreparationLedgerV1 {
    pub schema: String,
    pub module_id: String,
    pub head_revision_id: Option<String>,
    pub revisions: Vec<PreparationRevisionRefV1>,
}

impl ModulePhase0PreparationLedgerV1 {
    pub fn validate_shape(&self) -> Result<(), Phase0ContractError> {
        module_id(&self.module_id)?;
        if self.schema != MODULE_PHASE0_PREPARATION_LEDGER_SCHEMA
            || (self.revisions.is_empty() != self.head_revision_id.is_none())
            || self.revisions.iter().any(|revision| {
                !revision.revision_id.starts_with("preparation-revision-")
                    || !safe_parent_path(&revision.path)
                    || hash("revision_sha256", &revision.sha256).is_err()
            })
        {
            return Err(Phase0ContractError::InvalidPreparationRevision);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ModulePhase0ReviewReceiptV1 {
    pub schema: String,
    pub review_id: String,
    pub module_id: String,
    pub bundle_hash: String,
    pub evaluation_receipt_hash: String,
    pub evaluator_key_id: String,
    pub reviewer_key_id: String,
    pub review_method: String,
    pub independence_scope: String,
    pub human_review_performed: bool,
    pub independent_reimplementation_passed: bool,
    pub parent_hashes_current: bool,
    pub claim_locks_preserved: bool,
    pub zero_authority_affirmed: bool,
    pub accepted_for_phase0: bool,
    pub findings: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<DsseEnvelope>,
}

impl ModulePhase0ReviewReceiptV1 {
    pub fn validate(&self) -> Result<(), Phase0ContractError> {
        schema(&self.schema, MODULE_PHASE0_REVIEW_RECEIPT_SCHEMA)?;
        id("review_id", &self.review_id)?;
        module_id(&self.module_id)?;
        hash("bundle_hash", &self.bundle_hash)?;
        hash("evaluation_receipt_hash", &self.evaluation_receipt_hash)?;
        signer(&self.evaluator_key_id)?;
        signer(&self.reviewer_key_id)?;
        if self.evaluator_key_id == self.reviewer_key_id {
            return Err(Phase0ContractError::SameSigner);
        }
        automated_review_boundary(
            &self.review_method,
            &self.independence_scope,
            self.human_review_performed,
        )?;
        let controls_passed = self.independent_reimplementation_passed
            && self.parent_hashes_current
            && self.claim_locks_preserved
            && self.zero_authority_affirmed;
        if self.accepted_for_phase0 != controls_passed {
            return Err(Phase0ContractError::ReviewAcceptanceMismatch);
        }
        Ok(())
    }

    fn unsigned_bytes(&self) -> Result<Vec<u8>, Phase0ContractError> {
        let mut unsigned = self.clone();
        unsigned.signature = None;
        canonical_bytes(&unsigned)
    }

    pub fn sign(&mut self, key_id: &str, key: &SigningKey) -> Result<(), Phase0ContractError> {
        if self.reviewer_key_id != key_id {
            return Err(Phase0ContractError::SignerIdentityMismatch);
        }
        self.validate()?;
        self.signature = Some(sign_dsse(
            MODULE_PHASE0_REVIEW_PAYLOAD_TYPE,
            &self.unsigned_bytes()?,
            key_id,
            key,
        ));
        Ok(())
    }

    pub fn verify_signature(&self, trust: &TrustStore) -> Result<String, Phase0ContractError> {
        self.validate()?;
        let envelope = self
            .signature
            .as_ref()
            .ok_or(Phase0ContractError::Unsigned)?;
        if envelope.payload_type != MODULE_PHASE0_REVIEW_PAYLOAD_TYPE {
            return Err(Phase0ContractError::SignaturePayload);
        }
        let verified = verify_dsse(envelope, trust)?;
        if verified.payload != self.unsigned_bytes()? || verified.key_id != self.reviewer_key_id {
            return Err(Phase0ContractError::SignaturePayload);
        }
        Ok(verified.key_id)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ModuleMovementEventV1 {
    pub schema: String,
    pub event_id: String,
    pub module_id: String,
    pub previous_phase: String,
    pub current_phase: String,
    pub effective_status_change: String,
    pub bundle_hash: String,
    pub evaluation_receipt_hash: String,
    pub review_receipt_hash: String,
    pub parent_hashes: BTreeMap<String, String>,
    pub evaluator_key_id: String,
    pub reviewer_key_id: String,
    pub review_method: String,
    pub independence_scope: String,
    pub human_review_performed: bool,
    pub claim_lock_hash: String,
    pub scientific_outcome: ScientificOutcomeV1,
    pub scientific_readiness: String,
    pub decision_use_ceiling: String,
    pub applicability_limits: Vec<String>,
    pub retained_negative_results: Vec<String>,
}

impl ModuleMovementEventV1 {
    pub fn validate(&self) -> Result<(), Phase0ContractError> {
        schema(&self.schema, MODULE_MOVEMENT_EVENT_SCHEMA)?;
        module_id(&self.module_id)?;
        if self.previous_phase != "PRE_PHASE_0"
            || self.current_phase != "PHASE_0"
            || self.effective_status_change != "PRE_PHASE_0->PHASE_0"
        {
            return Err(Phase0ContractError::InvalidMovement);
        }
        for (name, value) in [
            ("bundle_hash", &self.bundle_hash),
            ("evaluation_receipt_hash", &self.evaluation_receipt_hash),
            ("review_receipt_hash", &self.review_receipt_hash),
            ("claim_lock_hash", &self.claim_lock_hash),
        ] {
            hash(name, value)?;
        }
        parent_hashes(&self.parent_hashes)?;
        signer(&self.evaluator_key_id)?;
        signer(&self.reviewer_key_id)?;
        if self.evaluator_key_id == self.reviewer_key_id {
            return Err(Phase0ContractError::SameSigner);
        }
        automated_review_boundary(
            &self.review_method,
            &self.independence_scope,
            self.human_review_performed,
        )?;
        audit_only(&self.decision_use_ceiling)?;
        if !matches!(
            self.scientific_readiness.as_str(),
            "LOCKED_INTERNAL" | "NOT_APPLICABLE"
        ) {
            return Err(Phase0ContractError::InvalidMovement);
        }
        nonempty_strings("applicability_limits", &self.applicability_limits)?;
        if self.scientific_outcome == ScientificOutcomeV1::Failed
            && self.retained_negative_results.is_empty()
        {
            return Err(Phase0ContractError::NegativeResultNotRetained);
        }
        if self.event_id != self.computed_event_id()? {
            return Err(Phase0ContractError::EventIdMismatch);
        }
        Ok(())
    }

    pub fn computed_event_id(&self) -> Result<String, Phase0ContractError> {
        let mut unsigned = self.clone();
        unsigned.event_id.clear();
        Ok(format!(
            "movement-{}",
            stable_hash(&serde_json::to_value(unsigned)?)
        ))
    }

    pub fn bind_event_id(&mut self) -> Result<(), Phase0ContractError> {
        self.event_id = self.computed_event_id()?;
        Ok(())
    }
}

#[derive(Debug, Error)]
pub enum Phase0ContractError {
    #[error("unexpected schema {actual}; expected {expected}")]
    Schema {
        actual: String,
        expected: &'static str,
    },
    #[error("{0} must not be empty")]
    Empty(&'static str),
    #[error("{0} is not a lowercase SHA-256 digest")]
    Hash(String),
    #[error("invalid module ID")]
    ModuleId,
    #[error("invalid module class")]
    ModuleClass,
    #[error("scientific readiness is inconsistent with module class")]
    Readiness,
    #[error("Phase-0 decision use must remain AUDIT_ONLY")]
    DecisionUse,
    #[error("abstention outside the applicability domain is mandatory")]
    AbstentionRequired,
    #[error("required claim lock is absent or false: {0}")]
    MissingClaimLock(String),
    #[error("required authority prohibition is absent: {0}")]
    MissingAuthorityProhibition(String),
    #[error("authoritative parent path is outside the module folder: {0}")]
    ParentPath(String),
    #[error("authoritative parent map is empty")]
    EmptyParents,
    #[error("bundle does not contain required parent hash {0}")]
    MissingParentHash(String),
    #[error("review packet must be blinded")]
    ReviewPacketNotBlinded,
    #[error("phase0_eligible does not match audit and failed-gate state")]
    EligibilityMismatch,
    #[error("scientific outcome is inconsistent with module class")]
    OutcomeClassMismatch,
    #[error("failed scientific result was not retained")]
    NegativeResultNotRetained,
    #[error("Phase-0 signing identities may not be local development identities")]
    LocalDevelopmentSigner,
    #[error("evaluator and reviewer identities must differ")]
    SameSigner,
    #[error("Phase-0 review method must be AUTOMATED_INDEPENDENT_REIMPLEMENTATION")]
    ReviewMethod,
    #[error("Phase-0 independence scope must be CODE_PATH_AND_SIGNING_IDENTITY")]
    IndependenceScope,
    #[error("automated Phase-0 review must not claim human review")]
    FalseHumanReviewClaim,
    #[error("review acceptance does not match review controls")]
    ReviewAcceptanceMismatch,
    #[error("signing key does not match the receipt identity")]
    SignerIdentityMismatch,
    #[error("receipt is unsigned")]
    Unsigned,
    #[error("signature payload is not bound to the receipt")]
    SignaturePayload,
    #[error("movement event does not represent an atomic Phase-0 promotion")]
    InvalidMovement,
    #[error("movement event ID is not hash-derived from its payload")]
    EventIdMismatch,
    #[error("Phase-0 supersession provenance is invalid")]
    InvalidSupersession,
    #[error("Phase-0 preparation revision ledger is invalid or forked")]
    InvalidPreparationRevision,
    #[error("deterministic-control diagnostic contract is invalid")]
    InvalidDeterministicDiagnostic,
    #[error("module registry succession contract is invalid")]
    InvalidRegistrySuccession,
    #[error(transparent)]
    Verification(#[from] crate::VerificationError),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
}

fn schema(actual: &str, expected: &'static str) -> Result<(), Phase0ContractError> {
    (actual == expected)
        .then_some(())
        .ok_or_else(|| Phase0ContractError::Schema {
            actual: actual.into(),
            expected,
        })
}

fn id(field: &'static str, value: &str) -> Result<(), Phase0ContractError> {
    (!value.trim().is_empty())
        .then_some(())
        .ok_or(Phase0ContractError::Empty(field))
}

fn module_id(value: &str) -> Result<(), Phase0ContractError> {
    let suffix = value
        .strip_prefix("amphora-")
        .ok_or(Phase0ContractError::ModuleId)?;
    (!suffix.is_empty()
        && suffix
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-'))
    .then_some(())
    .ok_or(Phase0ContractError::ModuleId)
}

fn hash(field: &str, value: &str) -> Result<(), Phase0ContractError> {
    (value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)))
    .then_some(())
    .ok_or_else(|| Phase0ContractError::Hash(field.into()))
}

fn module_class(value: &str) -> Result<(), Phase0ContractError> {
    matches!(value, "DETERMINISTIC_CONTROL" | "SCIENTIFIC_OR_EVIDENCE")
        .then_some(())
        .ok_or(Phase0ContractError::ModuleClass)
}

fn readiness(class: &str, value: &str) -> Result<(), Phase0ContractError> {
    matches!(
        (class, value),
        ("DETERMINISTIC_CONTROL", "NOT_APPLICABLE") | ("SCIENTIFIC_OR_EVIDENCE", "LOCKED_INTERNAL")
    )
    .then_some(())
    .ok_or(Phase0ContractError::Readiness)
}

fn audit_only(value: &str) -> Result<(), Phase0ContractError> {
    (value == "AUDIT_ONLY")
        .then_some(())
        .ok_or(Phase0ContractError::DecisionUse)
}

fn automated_review_boundary(
    review_method: &str,
    independence_scope: &str,
    human_review_performed: bool,
) -> Result<(), Phase0ContractError> {
    if review_method != PHASE0_REVIEW_METHOD {
        return Err(Phase0ContractError::ReviewMethod);
    }
    if independence_scope != PHASE0_INDEPENDENCE_SCOPE {
        return Err(Phase0ContractError::IndependenceScope);
    }
    if human_review_performed {
        return Err(Phase0ContractError::FalseHumanReviewClaim);
    }
    Ok(())
}

fn nonempty_strings(field: &'static str, values: &[String]) -> Result<(), Phase0ContractError> {
    (!values.is_empty() && values.iter().all(|value| !value.trim().is_empty()))
        .then_some(())
        .ok_or(Phase0ContractError::Empty(field))
}

fn claim_locks(locks: &BTreeMap<String, bool>) -> Result<(), Phase0ContractError> {
    for required in REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS {
        if locks.get(required) != Some(&true) {
            return Err(Phase0ContractError::MissingClaimLock(required.into()));
        }
    }
    if let Some((name, _)) = locks.iter().find(|(_, enabled)| !**enabled) {
        return Err(Phase0ContractError::MissingClaimLock(name.clone()));
    }
    Ok(())
}

fn parent_hashes(parents: &BTreeMap<String, String>) -> Result<(), Phase0ContractError> {
    if parents.is_empty() {
        return Err(Phase0ContractError::EmptyParents);
    }
    for (relative, digest) in parents {
        let path = Path::new(relative);
        if path.is_absolute()
            || path.components().any(|component| {
                !matches!(component, Component::Normal(_)) || component.as_os_str() == ".amphora"
            })
        {
            return Err(Phase0ContractError::ParentPath(relative.clone()));
        }
        hash(relative, digest)?;
    }
    Ok(())
}

fn safe_parent_path(value: &str) -> bool {
    let path = Path::new(value);
    !value.is_empty()
        && !path.is_absolute()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn signer(key_id: &str) -> Result<(), Phase0ContractError> {
    id("signer_key_id", key_id)?;
    if key_id.starts_with("local-") || key_id.starts_with("dev-") {
        Err(Phase0ContractError::LocalDevelopmentSigner)
    } else {
        Ok(())
    }
}

fn canonical_bytes<T: Serialize>(value: &T) -> Result<Vec<u8>, Phase0ContractError> {
    Ok(serde_json::to_vec(&canonicalize(&serde_json::to_value(
        value,
    )?))?)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn digest(byte: char) -> String {
        std::iter::repeat_n(byte, 64).collect()
    }

    fn evaluation(outcome: ScientificOutcomeV1) -> ModulePhase0EvaluationReceiptV1 {
        ModulePhase0EvaluationReceiptV1 {
            schema: MODULE_PHASE0_EVALUATION_RECEIPT_SCHEMA.into(),
            receipt_id: "evaluation-1".into(),
            module_id: "amphora-example".into(),
            module_class: "SCIENTIFIC_OR_EVIDENCE".into(),
            bundle_hash: digest('a'),
            bundle_parent_hashes: BTreeMap::from([(
                "evidence/phase0/source.json".into(),
                digest('b'),
            )]),
            evaluator_key_id: "phase0-evaluator".into(),
            audit_execution_passed: true,
            benchmark_execution_complete: Some(true),
            scientific_outcome: outcome,
            phase0_eligible: true,
            scientific_readiness: "LOCKED_INTERNAL".into(),
            decision_use_ceiling: "AUDIT_ONLY".into(),
            claim_lock_hash: digest('c'),
            applicability_domain: vec!["locked domain".into()],
            failed_gates: Vec::new(),
            retained_negative_results: vec!["no lift against locked baseline".into()],
            replay_hash: digest('d'),
            metrics: BTreeMap::new(),
            signature: None,
        }
    }

    fn claim_locks() -> BTreeMap<String, bool> {
        REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS
            .iter()
            .map(|lock| ((*lock).into(), true))
            .collect()
    }

    fn bundle() -> ModulePhase0BundleV1 {
        ModulePhase0BundleV1 {
            schema: MODULE_PHASE0_BUNDLE_SCHEMA.into(),
            module_id: "amphora-example".into(),
            module_class: "SCIENTIFIC_OR_EVIDENCE".into(),
            registry_manifest_hash: digest('9'),
            source_lock_hash: digest('a'),
            dataset_manifest_hash: digest('b'),
            split_manifest_hash: digest('c'),
            benchmark_lock_hash: digest('d'),
            promotion_policy_hash: digest('e'),
            claim_contract_hash: digest('f'),
            technical_dossier_hash: digest('0'),
            prior_art_hash: digest('1'),
            disclosure_log_hash: digest('2'),
            parents: BTreeMap::from([
                (
                    "evidence/phase0/sources/source-lock.v1.json".into(),
                    digest('a'),
                ),
                (
                    "evidence/phase0/dataset/dataset-manifest.v1.json".into(),
                    digest('b'),
                ),
                (
                    "evidence/phase0/split/split-manifest.v1.json".into(),
                    digest('c'),
                ),
                (
                    "evidence/phase0/benchmark/benchmark-lock.v1.json".into(),
                    digest('d'),
                ),
                (
                    "evidence/phase0/promotion/policy.v1.json".into(),
                    digest('e'),
                ),
                ("ip/claim-contract.v1.json".into(), digest('f')),
                ("ip/technical-dossier.v1.json".into(), digest('0')),
                ("ip/prior-art.v1.json".into(), digest('1')),
                ("ip/disclosure-log.v1.json".into(), digest('2')),
            ]),
            toolkit_versions: BTreeMap::from([("test-toolkit".into(), "1.0.0".into())]),
            applicability_domain: vec!["locked domain".into()],
            claim_locks: claim_locks(),
            review_packet_blinded: true,
        }
    }

    fn succession_chain() -> ModuleRegistrySuccessionChainV1 {
        ModuleRegistrySuccessionChainV1 {
            schema: MODULE_REGISTRY_SUCCESSION_CHAIN_SCHEMA.into(),
            genesis_manifest_sha256: digest('a'),
            head_manifest_sha256: digest('c'),
            records: vec![
                RegistrySuccessionRecordRefV1 {
                    record_sha256: digest('1'),
                    succession_id: "registry-succession-first".into(),
                    predecessor_sha256: digest('a'),
                    successor_sha256: digest('b'),
                },
                RegistrySuccessionRecordRefV1 {
                    record_sha256: digest('2'),
                    succession_id: "registry-succession-second".into(),
                    predecessor_sha256: digest('b'),
                    successor_sha256: digest('c'),
                },
            ],
        }
    }

    #[test]
    fn registry_succession_chain_rejects_gaps_forks_cycles_duplicates_and_reordering() {
        let chain = succession_chain();
        chain.validate().unwrap();

        let mut gap = chain.clone();
        gap.records[1].predecessor_sha256 = digest('d');
        assert!(gap.validate().is_err());

        let mut fork = chain.clone();
        fork.records.push(RegistrySuccessionRecordRefV1 {
            record_sha256: digest('3'),
            succession_id: "registry-succession-fork".into(),
            predecessor_sha256: digest('b'),
            successor_sha256: digest('c'),
        });
        assert!(fork.validate().is_err());

        let mut cycle = chain.clone();
        cycle.records[1].successor_sha256 = digest('a');
        cycle.head_manifest_sha256 = digest('a');
        assert!(cycle.validate().is_err());

        let mut duplicate = chain.clone();
        duplicate.records[1].record_sha256 = duplicate.records[0].record_sha256.clone();
        assert!(duplicate.validate().is_err());

        let mut reordered = chain;
        reordered.records.swap(0, 1);
        assert!(reordered.validate().is_err());
    }

    #[test]
    fn failed_science_can_be_eligible_but_stays_audit_only() {
        let receipt = evaluation(ScientificOutcomeV1::Failed);
        receipt.validate().unwrap();
        assert!(receipt.phase0_eligible);
        assert_eq!(receipt.scientific_readiness, "LOCKED_INTERNAL");
        assert_eq!(receipt.decision_use_ceiling, "AUDIT_ONLY");
    }

    #[test]
    fn failed_science_must_be_retained() {
        let mut receipt = evaluation(ScientificOutcomeV1::Failed);
        receipt.retained_negative_results.clear();
        assert!(matches!(
            receipt.validate(),
            Err(Phase0ContractError::NegativeResultNotRetained)
        ));
    }

    #[test]
    fn deterministic_science_outcome_is_not_applicable() {
        let mut receipt = evaluation(ScientificOutcomeV1::NotApplicable);
        receipt.module_class = "DETERMINISTIC_CONTROL".into();
        receipt.scientific_readiness = "NOT_APPLICABLE".into();
        receipt.validate().unwrap();
        receipt.scientific_outcome = ScientificOutcomeV1::Passed;
        assert!(matches!(
            receipt.validate(),
            Err(Phase0ContractError::OutcomeClassMismatch)
        ));
    }

    #[test]
    fn benchmark_execution_completion_is_distinct_from_scientific_outcome() {
        let mut receipt = evaluation(ScientificOutcomeV1::Failed);
        receipt.benchmark_execution_complete = Some(false);
        receipt.phase0_eligible = false;
        receipt.failed_gates = vec!["SCIENTIFIC_BENCHMARK_NOT_EXECUTED".into()];
        receipt.validate().unwrap();

        receipt.benchmark_execution_complete = Some(true);
        receipt.failed_gates.clear();
        assert!(matches!(
            receipt.validate(),
            Err(Phase0ContractError::EligibilityMismatch)
        ));
    }

    #[test]
    fn supersession_id_is_deterministic_and_module_bound() {
        let archived_artifacts = BTreeMap::from([
            ("phase0/bundle.v1.json".into(), digest('a')),
            ("ip/claim-contract.v1.json".into(), digest('b')),
        ]);
        let mut first = ModulePhase0SupersessionV1 {
            schema: MODULE_PHASE0_SUPERSESSION_SCHEMA.into(),
            supersession_id: String::new(),
            module_id: "amphora-example".into(),
            reason: "STALE_UNSIGNED_PREPARATION_REISSUE".into(),
            archive_root: String::new(),
            archived_artifacts: archived_artifacts.clone(),
            unsigned_preparation_only: true,
            authority_transferred: false,
        };
        first.bind_supersession_id().unwrap();
        first.validate().unwrap();
        let mut second = first.clone();
        second.supersession_id.clear();
        second.archive_root.clear();
        second.bind_supersession_id().unwrap();
        assert_eq!(first, second);

        second.module_id = "amphora-other".into();
        assert!(matches!(
            second.validate(),
            Err(Phase0ContractError::InvalidSupersession)
        ));
    }

    #[test]
    fn review_rejects_same_and_local_signers() {
        let mut review = ModulePhase0ReviewReceiptV1 {
            schema: MODULE_PHASE0_REVIEW_RECEIPT_SCHEMA.into(),
            review_id: "review-1".into(),
            module_id: "amphora-example".into(),
            bundle_hash: digest('a'),
            evaluation_receipt_hash: digest('b'),
            evaluator_key_id: "phase0-evaluator".into(),
            reviewer_key_id: "phase0-evaluator".into(),
            review_method: PHASE0_REVIEW_METHOD.into(),
            independence_scope: PHASE0_INDEPENDENCE_SCOPE.into(),
            human_review_performed: false,
            independent_reimplementation_passed: true,
            parent_hashes_current: true,
            claim_locks_preserved: true,
            zero_authority_affirmed: true,
            accepted_for_phase0: true,
            findings: Vec::new(),
            signature: None,
        };
        assert!(matches!(
            review.validate(),
            Err(Phase0ContractError::SameSigner)
        ));
        review.reviewer_key_id = "local-reviewer".into();
        assert!(matches!(
            review.validate(),
            Err(Phase0ContractError::LocalDevelopmentSigner)
        ));
    }

    #[test]
    fn movement_id_is_hash_derived() {
        let mut movement = ModuleMovementEventV1 {
            schema: MODULE_MOVEMENT_EVENT_SCHEMA.into(),
            event_id: String::new(),
            module_id: "amphora-example".into(),
            previous_phase: "PRE_PHASE_0".into(),
            current_phase: "PHASE_0".into(),
            effective_status_change: "PRE_PHASE_0->PHASE_0".into(),
            bundle_hash: digest('a'),
            evaluation_receipt_hash: digest('b'),
            review_receipt_hash: digest('c'),
            parent_hashes: BTreeMap::from([("evidence/phase0/bundle.v1.json".into(), digest('d'))]),
            evaluator_key_id: "phase0-evaluator".into(),
            reviewer_key_id: "phase0-reviewer".into(),
            review_method: PHASE0_REVIEW_METHOD.into(),
            independence_scope: PHASE0_INDEPENDENCE_SCOPE.into(),
            human_review_performed: false,
            claim_lock_hash: digest('e'),
            scientific_outcome: ScientificOutcomeV1::Failed,
            scientific_readiness: "LOCKED_INTERNAL".into(),
            decision_use_ceiling: "AUDIT_ONLY".into(),
            applicability_limits: vec!["locked domain".into()],
            retained_negative_results: vec!["locked no-lift result".into()],
        };
        movement.bind_event_id().unwrap();
        movement.validate().unwrap();
        movement.current_phase = "PHASE_1".into();
        assert!(movement.validate().is_err());
    }

    #[test]
    fn bundle_rejects_cross_module_and_legacy_receipt_laundering() {
        let mut cross_module = bundle();
        cross_module.parents.insert(
            "../amphora-other/evidence/phase0/source.json".into(),
            digest('3'),
        );
        assert!(matches!(
            cross_module.validate(),
            Err(Phase0ContractError::ParentPath(_))
        ));

        let mut legacy = bundle();
        legacy.parents.insert(
            "evidence/phase0/.amphora/legacy-receipt.json".into(),
            digest('3'),
        );
        assert!(matches!(
            legacy.validate(),
            Err(Phase0ContractError::ParentPath(_))
        ));
    }

    #[test]
    fn stripped_claim_lock_and_authority_escalation_fail_closed() {
        let mut stripped = bundle();
        stripped.claim_locks.remove("no_release_authority");
        assert!(matches!(
            stripped.validate(),
            Err(Phase0ContractError::MissingClaimLock(_))
        ));

        let mut escalated = evaluation(ScientificOutcomeV1::Failed);
        escalated.decision_use_ceiling = "OBJECTIVE".into();
        assert!(matches!(
            escalated.validate(),
            Err(Phase0ContractError::DecisionUse)
        ));
    }

    #[test]
    fn automated_review_cannot_claim_human_independence() {
        let mut review = ModulePhase0ReviewReceiptV1 {
            schema: MODULE_PHASE0_REVIEW_RECEIPT_SCHEMA.into(),
            review_id: "review-1".into(),
            module_id: "amphora-example".into(),
            bundle_hash: digest('a'),
            evaluation_receipt_hash: digest('b'),
            evaluator_key_id: "phase0-evaluator".into(),
            reviewer_key_id: "phase0-reviewer".into(),
            review_method: PHASE0_REVIEW_METHOD.into(),
            independence_scope: PHASE0_INDEPENDENCE_SCOPE.into(),
            human_review_performed: true,
            independent_reimplementation_passed: true,
            parent_hashes_current: true,
            claim_locks_preserved: true,
            zero_authority_affirmed: true,
            accepted_for_phase0: true,
            findings: Vec::new(),
            signature: None,
        };
        assert!(matches!(
            review.validate(),
            Err(Phase0ContractError::FalseHumanReviewClaim)
        ));
        review.human_review_performed = false;
        review.review_method = "HUMAN_REVIEW".into();
        assert!(matches!(
            review.validate(),
            Err(Phase0ContractError::ReviewMethod)
        ));
    }

    #[test]
    fn signed_evaluation_rejects_replay_drift() {
        let key = SigningKey::from_bytes(&[7_u8; 32]);
        let mut trust = TrustStore::default();
        trust
            .insert("phase0-evaluator", key.verifying_key().to_bytes())
            .unwrap();
        let mut receipt = evaluation(ScientificOutcomeV1::Failed);
        receipt.sign("phase0-evaluator", &key).unwrap();
        receipt.verify_signature(&trust).unwrap();
        receipt.replay_hash = digest('e');
        assert!(matches!(
            receipt.verify_signature(&trust),
            Err(Phase0ContractError::SignaturePayload)
        ));
    }

    #[test]
    fn preparation_revision_id_binds_unsigned_history() {
        let supersession_id = format!("supersession-{}", digest('a'));
        let mut revision = ModulePhase0PreparationRevisionV1 {
            schema: MODULE_PHASE0_PREPARATION_REVISION_SCHEMA.into(),
            revision_id: String::new(),
            module_id: "amphora-example".into(),
            revision_number: 1,
            parent_revision_id: None,
            supersession_id: supersession_id.clone(),
            supersession_path: format!(
                "evidence/superseded/{supersession_id}/supersession.v1.json"
            ),
            supersession_sha256: digest('b'),
            archived_bundle_sha256: digest('c'),
            unsigned_preparation_only: true,
        };
        revision.bind_revision_id().unwrap();
        revision.validate().unwrap();
        revision.archived_bundle_sha256 = digest('d');
        assert!(matches!(
            revision.validate(),
            Err(Phase0ContractError::InvalidPreparationRevision)
        ));
    }
}
