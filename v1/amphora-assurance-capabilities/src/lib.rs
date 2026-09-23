#![forbid(unsafe_code)]

mod diagnostics;

pub use diagnostics::{deterministic_control_diagnostic, REDTEAM_ATTACK_AXES};

use amphora_core::{
    canonicalize, sign_dsse, stable_hash, verify_dsse, CandidateEnvelope, Capability,
    CapabilityError, DsseEnvelope, ExecutionContext, FeatureSnapshot, ModuleDescriptor,
    ModuleResult, TrustStore,
};
use amphora_formulation_capabilities::EquivalentBalanceV1;
use ed25519_dalek::SigningKey;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::sync::OnceLock;

pub const HOST_VERIFIED_RECEIPT_FEATURE: &str = "evidence_intake.host_verified_receipt";
pub const HOST_VERIFIED_RECEIPT_SCHEMA: &str = "amphora.host-verified-evidence-receipt.v1";

const EVIDENCE_INTAKE: &str = "amphora-evidence-intake-validator";
const SOURCE_LEDGER: &str = "amphora-source-ledger";
const KNOWN_ANSWERS: &str = "amphora-known-answer-benchmarks";
const SOURCEABILITY_EHS: &str = "amphora-sourceability-ehs";
const CRO_PACKAGER: &str = "amphora-cro-protocol-packager";
const IP_FTO_GUARD: &str = "amphora-ip-fto-guard";
const REPORT_PACKAGER: &str = "amphora-report-packager";
const REDTEAM_AUDIT: &str = "amphora-redteam-audit";

pub const CRO_PROTOCOL_PACKAGE_V2_SCHEMA: &str = "amphora.cro-protocol-package.v2";
pub const CRO_PROTOCOL_PACKAGE_V2_PAYLOAD_TYPE: &str =
    "application/vnd.amphora.cro-protocol-package.v2+json";

const REQUIRED_CRO_CLAIM_LOCKS: [&str; 8] = [
    "NO_EXECUTION_AUTHORITY",
    "NO_PROCUREMENT_AUTHORITY",
    "NO_SAFETY_CLAIM",
    "NO_SYNTHESIS_CLAIM",
    "NO_PERFORMANCE_CLAIM",
    "NO_QUALIFICATION_CLAIM",
    "NO_RANKING_AUTHORITY",
    "UNMADE_DIGITAL_PROPOSAL",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CroProtocolPackageV2 {
    pub schema: String,
    pub packet_id: String,
    pub campaign_id: String,
    pub candidate_binding: Value,
    pub candidate_sha256: String,
    pub formula_sha256: String,
    pub equivalent_balance: EquivalentBalanceV1,
    pub status: String,
    pub sample_blinding_code: String,
    pub custody_requirements: Vec<String>,
    pub controls: Vec<String>,
    pub required_outputs: Vec<String>,
    pub safety_review_status: String,
    pub material_availability_status: String,
    pub chemist_review_status: String,
    pub cro_acceptance_status: String,
    pub execution_authorized: bool,
    pub authority_ceiling: String,
    pub ranking_eligible: bool,
    pub protocol_lock_sha256: Option<String>,
    #[serde(default)]
    pub locked_numeric_thresholds: BTreeMap<String, f64>,
    pub claim_locks: BTreeMap<String, bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<DsseEnvelope>,
}

#[derive(Debug, thiserror::Error)]
pub enum CroProtocolPackageError {
    #[error("CRO feasibility package metadata or review holds are invalid")]
    InvalidPackage,
    #[error("CRO feasibility package hash binding is invalid")]
    Binding,
    #[error("CRO feasibility package signature is absent or invalid")]
    Signature,
    #[error("CRO feasibility package JSON: {0}")]
    Json(#[from] serde_json::Error),
    #[error("CRO feasibility package signature: {0}")]
    Verification(#[from] amphora_core::VerificationError),
}

impl CroProtocolPackageV2 {
    pub fn draft(
        campaign_id: &str,
        candidate: &Value,
        equivalent_balance: EquivalentBalanceV1,
        sample_blinding_code: String,
    ) -> Result<Self, CroProtocolPackageError> {
        let candidate_sha256 = stable_hash(candidate);
        let formula_sha256 = stable_hash(&serde_json::to_value(&equivalent_balance)?);
        let mut packet = Self {
            schema: CRO_PROTOCOL_PACKAGE_V2_SCHEMA.into(),
            packet_id: String::new(),
            campaign_id: campaign_id.into(),
            candidate_binding: candidate.clone(),
            candidate_sha256,
            formula_sha256,
            equivalent_balance,
            status: "DRAFT_FOR_CRO_FEASIBILITY_REVIEW".into(),
            sample_blinding_code,
            custody_requirements: vec![
                "CRO-assigned sample identifiers".into(),
                "documented custody handoffs".into(),
                "tamper-evident receipt record".into(),
            ],
            controls: vec![
                "chemist-approved resin control".into(),
                "chemist-approved hardener control".into(),
                "vehicle blank".into(),
            ],
            required_outputs: vec![
                "feasibility disposition with exclusions".into(),
                "raw instrument files if execution is separately authorized".into(),
                "chain-of-custody return".into(),
                "negative and failed results".into(),
            ],
            safety_review_status: "UNRESOLVED_REQUIRES_EHS_REVIEW".into(),
            material_availability_status: "UNRESOLVED_REQUIRES_VERIFICATION".into(),
            chemist_review_status: "REQUIRED_NOT_COMPLETED".into(),
            cro_acceptance_status: "REQUIRED_NOT_COMPLETED".into(),
            execution_authorized: false,
            authority_ceiling: "AUDIT_ONLY".into(),
            ranking_eligible: false,
            protocol_lock_sha256: None,
            locked_numeric_thresholds: BTreeMap::new(),
            claim_locks: REQUIRED_CRO_CLAIM_LOCKS
                .into_iter()
                .map(|lock| (lock.into(), true))
                .collect(),
            signature: None,
        };
        packet.packet_id = packet.computed_packet_id()?;
        packet.validate()?;
        Ok(packet)
    }

    pub fn computed_packet_id(&self) -> Result<String, CroProtocolPackageError> {
        let mut unsigned = self.clone();
        unsigned.packet_id.clear();
        unsigned.signature = None;
        Ok(format!(
            "cro-feasibility-{}",
            stable_hash(&serde_json::to_value(unsigned)?)
        ))
    }

    pub fn validate(&self) -> Result<(), CroProtocolPackageError> {
        let valid_hash = |value: &str| {
            value.len() == 64
                && value
                    .bytes()
                    .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        };
        if self.schema != CRO_PROTOCOL_PACKAGE_V2_SCHEMA
            || self.packet_id != self.computed_packet_id()?
            || self.campaign_id.trim().is_empty()
            || self.candidate_sha256 != stable_hash(&self.candidate_binding)
            || !valid_hash(&self.candidate_sha256)
            || !valid_hash(&self.formula_sha256)
            || self.formula_sha256 != stable_hash(&serde_json::to_value(&self.equivalent_balance)?)
            || self.status != "DRAFT_FOR_CRO_FEASIBILITY_REVIEW"
            || self.sample_blinding_code.trim().is_empty()
            || self.custody_requirements.is_empty()
            || self.controls.is_empty()
            || self.required_outputs.is_empty()
            || self.safety_review_status != "UNRESOLVED_REQUIRES_EHS_REVIEW"
            || self.material_availability_status != "UNRESOLVED_REQUIRES_VERIFICATION"
            || self.chemist_review_status != "REQUIRED_NOT_COMPLETED"
            || self.cro_acceptance_status != "REQUIRED_NOT_COMPLETED"
            || self.execution_authorized
            || self.authority_ceiling != "AUDIT_ONLY"
            || self.ranking_eligible
            || REQUIRED_CRO_CLAIM_LOCKS
                .iter()
                .any(|lock| self.claim_locks.get(*lock) != Some(&true))
            || self.claim_locks.values().any(|enabled| !enabled)
            || self
                .locked_numeric_thresholds
                .values()
                .any(|value| !value.is_finite())
        {
            return Err(CroProtocolPackageError::InvalidPackage);
        }
        match &self.protocol_lock_sha256 {
            Some(hash)
                if valid_hash(hash)
                    && !self.locked_numeric_thresholds.is_empty()
                    && *hash == self.computed_protocol_lock_sha256()? => {}
            None if self.locked_numeric_thresholds.is_empty() => {}
            _ => return Err(CroProtocolPackageError::Binding),
        }
        // Blueprint-citation content-binding (CF-PACKET repair): a packet
        // that locks numeric thresholds must cite, by path+sha256, every
        // blueprint artifact those thresholds are claimed to derive from --
        // structural shape only here (no disk I/O in `validate()`, matching
        // the CompoundV2/MethodRegistry convention of a pure `validate()`
        // plus a separate disk-bound `verify_*` gate). Citations live in
        // `candidate_binding.blueprint_citations` (the only free-form field
        // CroProtocolPackageV2 exposes; the struct is
        // `#[serde(deny_unknown_fields)]` so this avoids a signature-shape
        // change that would invalidate previously-signed packets).
        let citations = self.blueprint_citation_entries()?;
        if !self.locked_numeric_thresholds.is_empty() && citations.is_empty() {
            return Err(CroProtocolPackageError::Binding);
        }
        Ok(())
    }

    /// Parses and structurally validates `candidate_binding.blueprint_citations`
    /// (absent -> no citations). Each entry must be `{"path": <non-empty
    /// string>, "sha256": <64 lowercase hex chars>}`; any other shape is
    /// `InvalidPackage`.
    fn blueprint_citation_entries(&self) -> Result<Vec<(String, String)>, CroProtocolPackageError> {
        let valid_hash = |value: &str| {
            value.len() == 64
                && value
                    .bytes()
                    .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        };
        match self.candidate_binding.get("blueprint_citations") {
            None => Ok(Vec::new()),
            Some(Value::Array(items)) => {
                let mut parsed = Vec::with_capacity(items.len());
                for item in items {
                    let path = item.get("path").and_then(Value::as_str);
                    let sha256 = item.get("sha256").and_then(Value::as_str);
                    match (path, sha256) {
                        (Some(p), Some(h)) if !p.trim().is_empty() && valid_hash(h) => {
                            parsed.push((p.to_string(), h.to_string()));
                        }
                        _ => return Err(CroProtocolPackageError::InvalidPackage),
                    }
                }
                Ok(parsed)
            }
            Some(_) => Err(CroProtocolPackageError::InvalidPackage),
        }
    }

    /// Disk-bound counterpart to `validate()` (CF-PACKET repair): re-derives
    /// the sha256 of every cited blueprint artifact from its real bytes at
    /// `root`-relative `path` and rejects the packet if any cited hash does
    /// not match. `validate()`/`sign()`/`verify_signature()` intentionally
    /// stay disk-independent (mirrors `CompoundV2::verify_files(root)` /
    /// `MethodRegistry::verify_files(root)` in amphora-core::compound_v2);
    /// callers assembling a "final assembly" packet MUST additionally call
    /// this before treating locked_numeric_thresholds as content-bound to
    /// the blueprint they claim to derive from.
    pub fn verify_blueprint_citations(
        &self,
        root: &std::path::Path,
    ) -> Result<(), CroProtocolPackageError> {
        self.validate()?;
        for (path, cited_sha256) in self.blueprint_citation_entries()? {
            let bytes =
                std::fs::read(root.join(&path)).map_err(|_| CroProtocolPackageError::Binding)?;
            let mut hasher = Sha256::new();
            hasher.update(&bytes);
            let observed = format!("{:x}", hasher.finalize());
            if observed != cited_sha256 {
                return Err(CroProtocolPackageError::Binding);
            }
        }
        Ok(())
    }

    /// Content binding for `protocol_lock_sha256`: a packet-authored threshold
    /// must be locked by a hash actually derived from the thresholds it locks,
    /// not merely a format-valid hex string (T-02 refutation).
    pub fn computed_protocol_lock_sha256(&self) -> Result<String, CroProtocolPackageError> {
        Ok(stable_hash(&serde_json::to_value(
            &self.locked_numeric_thresholds,
        )?))
    }

    fn unsigned_bytes(&self) -> Result<Vec<u8>, CroProtocolPackageError> {
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
    ) -> Result<(), CroProtocolPackageError> {
        self.validate()?;
        self.signature = Some(sign_dsse(
            CRO_PROTOCOL_PACKAGE_V2_PAYLOAD_TYPE,
            &self.unsigned_bytes()?,
            key_id,
            signing_key,
        ));
        Ok(())
    }

    pub fn verify_signature(
        &self,
        trust_store: &TrustStore,
    ) -> Result<String, CroProtocolPackageError> {
        self.validate()?;
        let signature = self
            .signature
            .as_ref()
            .ok_or(CroProtocolPackageError::Signature)?;
        if signature.payload_type != CRO_PROTOCOL_PACKAGE_V2_PAYLOAD_TYPE {
            return Err(CroProtocolPackageError::Signature);
        }
        let verified = verify_dsse(signature, trust_store)?;
        if verified.payload != self.unsigned_bytes()? {
            return Err(CroProtocolPackageError::Binding);
        }
        Ok(verified.key_id)
    }
}

const SOURCE_FACTS_PATH: &str = "amphora-source-ledger/reference/mvp20/data/facts.json";
const SOURCE_FACTS: &[u8] =
    include_bytes!("../../amphora-source-ledger/reference/mvp20/data/facts.json");
const SOURCE_RECORDS_PATH: &str = "amphora-source-ledger/reference/mvp20/data/source_records.json";
const SOURCE_RECORDS: &[u8] =
    include_bytes!("../../amphora-source-ledger/reference/mvp20/data/source_records.json");
const ARITHMETIC_AUDIT_PATH: &str =
    "amphora-known-answer-benchmarks/reference/mvp20/out/arithmetic_audit.json";
const ARITHMETIC_AUDIT: &[u8] = include_bytes!(
    "../../amphora-known-answer-benchmarks/reference/mvp20/out/arithmetic_audit.json"
);
const KNOWN_CARDS_PATH: &str =
    "amphora-known-answer-benchmarks/reference/mvp20/out/known_reference_cards.json";
const KNOWN_CARDS: &[u8] = include_bytes!(
    "../../amphora-known-answer-benchmarks/reference/mvp20/out/known_reference_cards.json"
);
const CONTROL_RECEIPT_PATH: &str =
    "amphora-known-answer-benchmarks/reference/mvp20/out/control_by_control_receipt.v1.json";
const CONTROL_RECEIPT: &[u8] = include_bytes!(
    "../../amphora-known-answer-benchmarks/reference/mvp20/out/control_by_control_receipt.v1.json"
);
const SOURCEABILITY_PATH: &str = "amphora-sourceability-ehs/reference/mvp20/out/v5_epoch30_public_bom_sourceability_manifest.json";
const SOURCEABILITY: &[u8] = include_bytes!("../../amphora-sourceability-ehs/reference/mvp20/out/v5_epoch30_public_bom_sourceability_manifest.json");
const PATENT_LANDSCAPE_PATH: &str =
    "amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json";
const PATENT_LANDSCAPE: &[u8] =
    include_bytes!("../../amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json");
const REPORT_ARTIFACTS: [(&str, &[u8]); 4] = [
    (
        "amphora-report-packager/reference/mvp20/out/CUSTOMER_FACING.tex",
        include_bytes!("../../amphora-report-packager/reference/mvp20/out/CUSTOMER_FACING.tex"),
    ),
    (
        "amphora-report-packager/reference/mvp20/out/FOUNDER_FACING.tex",
        include_bytes!("../../amphora-report-packager/reference/mvp20/out/FOUNDER_FACING.tex"),
    ),
    (
        "amphora-report-packager/reference/mvp20/out/blueprint.md",
        include_bytes!("../../amphora-report-packager/reference/mvp20/out/blueprint.md"),
    ),
    (
        "amphora-report-packager/reference/mvp20/out/f718_style_datasheet.md",
        include_bytes!("../../amphora-report-packager/reference/mvp20/out/f718_style_datasheet.md"),
    ),
];

pub const SUPPORTED_MODULE_IDS: [&str; 8] = [
    EVIDENCE_INTAKE,
    SOURCE_LEDGER,
    KNOWN_ANSWERS,
    SOURCEABILITY_EHS,
    CRO_PACKAGER,
    IP_FTO_GUARD,
    REPORT_PACKAGER,
    REDTEAM_AUDIT,
];

#[derive(Debug, Clone, Copy)]
pub struct AssuranceCapability {
    descriptor: &'static ModuleDescriptor,
}

impl AssuranceCapability {
    pub fn new(module_id: &str) -> Result<Self, CapabilityError> {
        let descriptor = descriptor_for(module_id).ok_or_else(|| {
            CapabilityError::InvalidInput(format!(
                "unsupported assurance capability module ID: {module_id}"
            ))
        })?;
        Ok(Self { descriptor })
    }

    pub fn from_descriptor(descriptor: &'static ModuleDescriptor) -> Result<Self, CapabilityError> {
        if !SUPPORTED_MODULE_IDS.contains(&descriptor.project.as_str()) {
            return Err(CapabilityError::InvalidInput(format!(
                "unsupported assurance capability module ID: {}",
                descriptor.project
            )));
        }
        Ok(Self { descriptor })
    }
}

impl Capability for AssuranceCapability {
    fn descriptor(&self) -> &'static ModuleDescriptor {
        self.descriptor
    }

    fn evaluate(
        &self,
        candidate: &CandidateEnvelope,
        features: &FeatureSnapshot,
        _context: &ExecutionContext,
    ) -> Result<ModuleResult, CapabilityError> {
        if !self
            .descriptor
            .candidate_types
            .iter()
            .any(|candidate_type| candidate_type == candidate.candidate_type())
        {
            return Err(CapabilityError::CandidateType);
        }

        let result = match self.descriptor.project.as_str() {
            EVIDENCE_INTAKE => evaluate_evidence_intake(candidate, features),
            SOURCE_LEDGER => evaluate_source_ledger(),
            KNOWN_ANSWERS => evaluate_known_answers(),
            SOURCEABILITY_EHS => evaluate_sourceability(),
            CRO_PACKAGER => evaluate_cro_packager(),
            IP_FTO_GUARD => evaluate_ip_fto_guard(candidate),
            REPORT_PACKAGER => evaluate_report_packager(),
            REDTEAM_AUDIT => evaluate_redteam_audit(),
            _ => {
                return Err(CapabilityError::InvalidInput(
                    "unsupported assurance descriptor".into(),
                ))
            }
        };

        debug_assert!(result.objective_values.is_empty());
        Ok(result)
    }
}

fn descriptor_for(module_id: &str) -> Option<&'static ModuleDescriptor> {
    match module_id {
        EVIDENCE_INTAKE => Some(evidence_intake_descriptor()),
        SOURCE_LEDGER => Some(source_ledger_descriptor()),
        KNOWN_ANSWERS => Some(known_answers_descriptor()),
        SOURCEABILITY_EHS => Some(sourceability_descriptor()),
        CRO_PACKAGER => Some(cro_packager_descriptor()),
        IP_FTO_GUARD => Some(ip_fto_descriptor()),
        REPORT_PACKAGER => Some(report_packager_descriptor()),
        REDTEAM_AUDIT => Some(redteam_audit_descriptor()),
        _ => None,
    }
}

fn make_descriptor(
    project: &str,
    authority_ceiling: &str,
    candidate_type: &str,
    locks: &[&str],
    readiness: &str,
) -> ModuleDescriptor {
    ModuleDescriptor {
        project: project.into(),
        authority_ceiling: authority_ceiling.into(),
        solver_use_ceiling: "DISABLED".into(),
        model_readiness_ceiling: "MODEL_READINESS_ONLY".into(),
        ranking_eligible: false,
        candidate_types: vec![candidate_type.into()],
        non_blocking_claim_locks: locks.iter().map(|lock| (*lock).into()).collect(),
        readiness: readiness.into(),
    }
}

fn evidence_intake_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: OnceLock<ModuleDescriptor> = OnceLock::new();
    DESCRIPTOR.get_or_init(|| {
        make_descriptor(
            EVIDENCE_INTAKE,
            "EVIDENCE_ONLY",
            "evidence_package",
            &[
                "computed_as_measured_rejected",
                "external_closure_claims_not_created_by_validator",
            ],
            "GATED",
        )
    })
}

fn source_ledger_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: OnceLock<ModuleDescriptor> = OnceLock::new();
    DESCRIPTOR.get_or_init(|| {
        make_descriptor(
            SOURCE_LEDGER,
            "RULE_CITED",
            "evidence_package",
            &[
                "feedback_v1_public_data_is_audited_not_owned_evidence",
                "no_uncited_constants",
                "public_sources_do_not_create_owned_evidence",
            ],
            "GATED",
        )
    })
}

fn known_answers_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: OnceLock<ModuleDescriptor> = OnceLock::new();
    DESCRIPTOR.get_or_init(|| {
        make_descriptor(
            KNOWN_ANSWERS,
            "LIMITED_SANITY",
            "formulation",
            &[
                "feedback_v1_benchmarks_do_not_validate_candidate_performance",
                "known_answers_do_not_validate_candidate_performance",
                "negative_controls_must_reject",
            ],
            "BLOCKED",
        )
    })
}

fn sourceability_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: OnceLock<ModuleDescriptor> = OnceLock::new();
    DESCRIPTOR.get_or_init(|| {
        make_descriptor(
            SOURCEABILITY_EHS,
            "EVIDENCE_ONLY",
            "formulation",
            &[
                "no_pfas_free_claim",
                "no_procurement_ready_claim",
                "no_taa_domestic_claim",
                "no_tsca_compliant_claim",
            ],
            "GATED",
        )
    })
}

fn cro_packager_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: OnceLock<ModuleDescriptor> = OnceLock::new();
    DESCRIPTOR.get_or_init(|| {
        make_descriptor(
            CRO_PACKAGER,
            "CRO_GATED",
            "formulation",
            &[
                "cro_execution_required",
                "protocol_packet_is_not_test_result",
            ],
            "GATED",
        )
    })
}

fn ip_fto_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: OnceLock<ModuleDescriptor> = OnceLock::new();
    DESCRIPTOR.get_or_init(|| {
        make_descriptor(
            IP_FTO_GUARD,
            "EVIDENCE_ONLY",
            "formulation",
            &[
                "counsel_required_for_legal_conclusions",
                "fto_not_performed",
                "not_legal_advice",
            ],
            "GATED",
        )
    })
}

fn report_packager_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: OnceLock<ModuleDescriptor> = OnceLock::new();
    DESCRIPTOR.get_or_init(|| {
        make_descriptor(
            REPORT_PACKAGER,
            "EVIDENCE_ONLY",
            "evidence_package",
            &[
                "banned_claim_lint_required",
                "human_deliverables_downstream_only",
            ],
            "GATED",
        )
    })
}

fn redteam_audit_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: OnceLock<ModuleDescriptor> = OnceLock::new();
    DESCRIPTOR.get_or_init(|| {
        make_descriptor(
            REDTEAM_AUDIT,
            "EVIDENCE_ONLY",
            "evidence_package",
            &[
                "artifact_vs_evidence_separation",
                "no_current_claim_upgrade_allowed",
            ],
            "COMPLETE",
        )
    })
}

fn base_result(status: &str, score_0_1: Option<f64>, evidence_scope: &str) -> ModuleResult {
    ModuleResult {
        status: status.into(),
        score_0_1,
        objective_values: BTreeMap::new(),
        metrics: BTreeMap::from([
            (
                "scientific_applicability".into(),
                Value::String("UNVALIDATED".into()),
            ),
            ("ranking_quarantine".into(), Value::Bool(true)),
        ]),
        gates: BTreeMap::new(),
        uncertainty: BTreeMap::new(),
        missing_inputs: Vec::new(),
        explanations: Vec::new(),
        source_refs: Vec::new(),
        evidence_scope: evidence_scope.into(),
    }
}

fn raw_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn embedded_json(bytes: &[u8]) -> Value {
    amphora_core::parse_json_strict(bytes)
        .expect("embedded evidence artifact must remain strict JSON")
}

fn bind_artifacts(result: &mut ModuleResult, artifacts: &[(&str, &[u8])]) {
    let hashes: BTreeMap<String, Value> = artifacts
        .iter()
        .map(|(path, bytes)| ((*path).into(), Value::String(raw_sha256(bytes))))
        .collect();
    result.metrics.insert(
        "artifact_hashes".into(),
        Value::Object(hashes.into_iter().collect()),
    );
    result.source_refs.extend(
        artifacts
            .iter()
            .map(|(path, bytes)| format!("{path}#sha256={}", raw_sha256(bytes))),
    );
}

fn evaluate_evidence_intake(
    candidate: &CandidateEnvelope,
    features: &FeatureSnapshot,
) -> ModuleResult {
    let package = candidate
        .value()
        .get("evidence_refs")
        .and_then(|refs| refs.get("evidence_package"));
    let package_sha256 = package.map(stable_hash);
    let verified = package_sha256
        .as_deref()
        .is_some_and(|package_sha256| host_receipt_valid(candidate, features, package_sha256));

    let mut result = base_result(
        if verified { "SCORED" } else { "FAILED_GATES" },
        Some(if verified { 1.0 } else { 0.0 }),
        "evidence_intake",
    );
    result.metrics.insert(
        "signature_verification".into(),
        Value::String(
            if verified {
                "HOST_VERIFIED_ED25519"
            } else {
                "HOST_VERIFIED_RECEIPT_REQUIRED"
            }
            .into(),
        ),
    );
    if let Some(package_sha256) = package_sha256 {
        result
            .metrics
            .insert("package_sha256".into(), Value::String(package_sha256));
    }
    result.gates.insert(
        "host_verified_signature_receipt".into(),
        Value::Bool(verified),
    );
    result
        .gates
        .insert("evidence_package_accepted".into(), Value::Bool(verified));
    if verified {
        result.explanations.push(
            "Evidence intake relies only on a host-verified, candidate- and package-bound Ed25519 receipt."
                .into(),
        );
    } else {
        let reason = format!(
            "missing or invalid host receipt in FeatureSnapshot key {HOST_VERIFIED_RECEIPT_FEATURE}"
        );
        result.missing_inputs.push(reason.clone());
        result.explanations.push(reason);
    }
    result
}

fn host_receipt_valid(
    candidate: &CandidateEnvelope,
    features: &FeatureSnapshot,
    package_sha256: &str,
) -> bool {
    let Some(receipt) = features
        .values
        .get(HOST_VERIFIED_RECEIPT_FEATURE)
        .and_then(Value::as_object)
    else {
        return false;
    };

    receipt.len() == 11
        && receipt.get("schema").and_then(Value::as_str) == Some(HOST_VERIFIED_RECEIPT_SCHEMA)
        && receipt.get("accepted").and_then(Value::as_bool) == Some(true)
        && receipt.get("signature_verified").and_then(Value::as_bool) == Some(true)
        && receipt.get("revocation_checked").and_then(Value::as_bool) == Some(true)
        && receipt.get("fresh").and_then(Value::as_bool) == Some(true)
        && receipt.get("signature_algorithm").and_then(Value::as_str) == Some("Ed25519")
        && receipt.get("trust_store_status").and_then(Value::as_str) == Some("TRUSTED")
        && receipt.get("candidate_id").and_then(Value::as_str) == Some(candidate.candidate_id())
        && receipt
            .get("candidate_contract_hash_v1")
            .and_then(Value::as_str)
            == Some(candidate.contract_hash_v1())
        && receipt.get("package_sha256").and_then(Value::as_str) == Some(package_sha256)
        && receipt
            .get("verifier_id")
            .and_then(Value::as_str)
            .is_some_and(|verifier| !verifier.is_empty())
}

fn evaluate_source_ledger() -> ModuleResult {
    let facts = embedded_json(SOURCE_FACTS);
    let entries = facts
        .get("entries")
        .and_then(Value::as_object)
        .expect("facts entries must be an object");
    let records = embedded_json(SOURCE_RECORDS);
    let source_records = records
        .get("records")
        .and_then(Value::as_array)
        .expect("source records must be an array");
    let required_fields = records
        .get("required_record_fields")
        .and_then(Value::as_array)
        .expect("required source fields must be an array");
    let load_bearing = entries
        .values()
        .filter(|row| row.get("load_bearing").and_then(Value::as_bool) == Some(true))
        .collect::<Vec<_>>();
    let corroborated = load_bearing
        .iter()
        .filter(|row| {
            row.get("second_url")
                .and_then(Value::as_str)
                .is_some_and(|value| !value.trim().is_empty())
        })
        .count();
    let prose_waivers = load_bearing
        .iter()
        .filter(|row| {
            row.get("single_source_waiver")
                .and_then(Value::as_str)
                .is_some_and(|value| !value.trim().is_empty())
        })
        .count();
    let missing_url = entries
        .values()
        .filter(|row| {
            row.get("url")
                .and_then(Value::as_str)
                .is_none_or(|value| value.trim().is_empty())
        })
        .count();
    let incomplete_records = source_records
        .iter()
        .filter(|row| {
            required_fields.iter().any(|field| {
                field
                    .as_str()
                    .is_some_and(|field| row.get(field).is_none_or(Value::is_null))
            })
        })
        .count();
    let evidence_complete = corroborated == load_bearing.len()
        && prose_waivers == 0
        && missing_url == 0
        && incomplete_records == 0;
    let mut result = base_result(
        if evidence_complete {
            "SCORED"
        } else {
            "FAILED_GATES"
        },
        Some(if evidence_complete { 1.0 } else { 0.0 }),
        "source_ledger",
    );
    result.metrics.extend(BTreeMap::from([
        ("cited_constant_count".into(), json!(entries.len())),
        (
            "load_bearing_constant_count".into(),
            json!(load_bearing.len()),
        ),
        ("two_source_count".into(), json!(corroborated)),
        ("prose_waiver_count".into(), json!(prose_waivers)),
        ("missing_url_count".into(), json!(missing_url)),
        ("source_record_count".into(), json!(source_records.len())),
        (
            "incomplete_source_record_count".into(),
            json!(incomplete_records),
        ),
    ]));
    result.gates.extend(BTreeMap::from([
        (
            "uncited_constants_rejected".into(),
            Value::Bool(missing_url == 0),
        ),
        (
            "load_bearing_two_source".into(),
            Value::Bool(corroborated == load_bearing.len()),
        ),
        (
            "load_bearing_two_source_or_waiver".into(),
            Value::Bool(corroborated == load_bearing.len() && prose_waivers == 0),
        ),
        (
            "prose_waivers_rejected".into(),
            Value::Bool(prose_waivers == 0),
        ),
    ]));
    if corroborated != load_bearing.len() {
        result.missing_inputs.push(format!(
            "{} load-bearing constants lack a second controlled source",
            load_bearing.len() - corroborated
        ));
    }
    if prose_waivers != 0 {
        result.missing_inputs.push(format!(
            "{prose_waivers} prose waivers require controlled evidence or removal"
        ));
    }
    if incomplete_records != 0 {
        result.missing_inputs.push(format!(
            "{incomplete_records} source records omit at least one required field"
        ));
    }
    result.explanations.push(
        "The current source ledger remains audit-only and fails its load-bearing evidence gate."
            .into(),
    );
    bind_artifacts(
        &mut result,
        &[
            (SOURCE_FACTS_PATH, SOURCE_FACTS),
            (SOURCE_RECORDS_PATH, SOURCE_RECORDS),
        ],
    );
    result
}

fn evaluate_known_answers() -> ModuleResult {
    let receipt = embedded_json(CONTROL_RECEIPT);
    let controls = receipt
        .get("controls")
        .and_then(Value::as_array)
        .expect("control receipt must list controls");
    let unique_ids = controls
        .iter()
        .filter_map(|row| row.get("control_id").and_then(Value::as_str))
        .collect::<BTreeSet<_>>();
    let verified_pass = controls
        .iter()
        .filter(|row| row.get("status").and_then(Value::as_str) == Some("VERIFIED_PASS"))
        .count();
    let verified_fail = controls
        .iter()
        .filter(|row| row.get("status").and_then(Value::as_str) == Some("VERIFIED_FAIL"))
        .count();
    let unverified = controls
        .iter()
        .filter(|row| row.get("status").and_then(Value::as_str) == Some("UNVERIFIED"))
        .count();
    let receipt_complete = receipt.get("schema").and_then(Value::as_str)
        == Some("amphora.known-answer-control-receipt.v1")
        && controls.len() == 14
        && unique_ids.len() == controls.len()
        && receipt.get("control_count").and_then(Value::as_u64) == Some(controls.len() as u64)
        && receipt.get("verified_pass_count").and_then(Value::as_u64) == Some(verified_pass as u64)
        && receipt.get("verified_fail_count").and_then(Value::as_u64) == Some(verified_fail as u64)
        && receipt.get("unverified_count").and_then(Value::as_u64) == Some(unverified as u64)
        && controls.iter().all(|row| {
            row.get("expected").is_some()
                && row.get("actual").is_some()
                && row.get("tolerance").is_some()
                && row
                    .get("source_artifact_sha256")
                    .and_then(Value::as_str)
                    .is_some_and(is_sha256)
        });
    let audit_pass = receipt_complete && verified_pass == controls.len();
    let pass_rate = verified_pass as f64 / controls.len() as f64;
    let mut result = base_result(
        if audit_pass { "SCORED" } else { "FAILED_GATES" },
        Some(pass_rate),
        "known_answer_audit",
    );
    result.metrics.extend(BTreeMap::from([
        ("control_count".into(), json!(controls.len())),
        ("verified_pass_count".into(), json!(verified_pass)),
        ("verified_fail_count".into(), json!(verified_fail)),
        ("unverified_count".into(), json!(unverified)),
        ("arithmetic_subset_checks".into(), json!(6)),
        ("arithmetic_subset_pass".into(), json!(6)),
        ("audit_pass_rate".into(), json!(pass_rate)),
    ]));
    result.gates.extend(BTreeMap::from([
        (
            "control_receipt_well_formed".into(),
            Value::Bool(receipt_complete),
        ),
        (
            "all_14_controls_verified".into(),
            Value::Bool(unverified == 0),
        ),
        ("known_answer_audit_passed".into(), Value::Bool(audit_pass)),
    ]));
    if unverified != 0 {
        result.missing_inputs.push(format!(
            "{unverified} control remains UNVERIFIED; 6/6 arithmetic is only a subset"
        ));
    }
    result.explanations.push(
        "The control-by-control receipt preserves 13 verified passes and one UNVERIFIED historical control; the 6/6 arithmetic subset is never represented as 14/14 and does not validate candidate performance.".into(),
    );
    bind_artifacts(
        &mut result,
        &[
            (ARITHMETIC_AUDIT_PATH, ARITHMETIC_AUDIT),
            (KNOWN_CARDS_PATH, KNOWN_CARDS),
            (CONTROL_RECEIPT_PATH, CONTROL_RECEIPT),
        ],
    );
    result
}

fn evaluate_sourceability() -> ModuleResult {
    let artifact = embedded_json(SOURCEABILITY);
    let source_records = artifact
        .get("source_records")
        .and_then(Value::as_array)
        .map_or(0, Vec::len);
    let hashes_verified = artifact
        .pointer("/summary/all_sources_have_sha256")
        .and_then(Value::as_bool)
        == Some(true);
    let mut result = base_result("FAILED_GATES", Some(0.0), "sourceability_ehs_prescreen");
    result.metrics.extend(BTreeMap::from([
        ("sourceability_status".into(), json!("UNRESOLVED")),
        ("public_source_record_count".into(), json!(source_records)),
        ("supply_probability".into(), Value::Null),
        ("public_corpus_rights".into(), json!("QUARANTINED")),
    ]));
    result.gates.extend(BTreeMap::from([
        ("exact_grade_source_present".into(), Value::Bool(false)),
        ("current_document_present".into(), Value::Bool(false)),
        ("signed_declaration_present".into(), Value::Bool(false)),
        (
            "source_hashes_verified".into(),
            Value::Bool(hashes_verified),
        ),
        ("procurement_ready".into(), Value::Bool(false)),
    ]));
    result
        .missing_inputs
        .push("candidate-, formula-, issuer-, grade-, and lot-bound supplier evidence".into());
    result.explanations.push(
        "Public sourceability material is quarantined prescreen evidence and cannot close procurement or regulatory claims."
            .into(),
    );
    bind_artifacts(&mut result, &[(SOURCEABILITY_PATH, SOURCEABILITY)]);
    result
}

fn evaluate_cro_packager() -> ModuleResult {
    let packet_complete = diagnostics::embedded_cro_protocol_valid();
    let mut result = base_result("INSUFFICIENT_INPUT", None, "cro_protocol_packet");
    result.metrics.extend(BTreeMap::from([
        (
            "packet_status".into(),
            json!(if packet_complete {
                "VALIDATED_RENDERER_FIXTURE"
            } else {
                "FAILED_FIXTURE"
            }),
        ),
        ("lab_execution_status".into(), json!("NOT_EXECUTED")),
        ("legacy_protocol_accepted".into(), Value::Bool(false)),
        (
            "legacy_capture_template_accepted".into(),
            Value::Bool(false),
        ),
        (
            "legacy_falsification_protocol_accepted".into(),
            Value::Bool(false),
        ),
        ("objective_value_count".into(), json!(0)),
    ]));
    result.gates.extend(BTreeMap::from([
        (
            "protocol_packet_complete".into(),
            Value::Bool(packet_complete),
        ),
        ("lab_results_present".into(), Value::Bool(false)),
        ("usable_by_optimizer".into(), Value::Bool(false)),
    ]));
    result.missing_inputs.push(
        "actual CRO execution, chain-of-custody return, raw outputs, and signed result receipt"
            .into(),
    );
    result.explanations.push(
        "The signed known-answer packet validates deterministic packaging only; it is not a laboratory result and cannot create physical-validation evidence."
            .into(),
    );
    result
}

/// Canonical counsel-assertion key names, in post-normalization ASCII-squashed
/// skeleton form (see [`normalized_key_skeleton`]). Detection is deliberately
/// broad: `boolean_counsel_assertion_ignored` is a defensive lock, so a match
/// only ever RECORDS that a candidate-supplied counsel-signoff assertion was
/// ignored - it can never elevate authority. Broader detection is therefore a
/// strictly stronger, fail-closed lock (repair R-B01 for
/// evidence/audit/counsel-assertion-detection-completeness-v1).
const COUNSEL_ASSERTION_CANONICAL_KEYS: [&str; 2] = ["signedbycounsel", "counselfto"];

/// Fold lowercase Unicode confusables/homoglyphs (Cyrillic and Greek
/// lookalikes) onto their ASCII skeleton so spoofed key spellings such as
/// `ѕigned_by_counѕel` (CYRILLIC DZE) cannot evade the counsel-assertion
/// reference monitor. Applied after NFKC normalization and lowercasing.
fn fold_confusable(ch: char) -> char {
    match ch {
        'а' => 'a', // U+0430 CYRILLIC SMALL LETTER A
        'с' => 'c', // U+0441 CYRILLIC SMALL LETTER ES
        'ԁ' => 'd', // U+0501 CYRILLIC SMALL LETTER KOMI DE
        'е' => 'e', // U+0435 CYRILLIC SMALL LETTER IE
        'і' => 'i', // U+0456 CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I
        'ј' => 'j', // U+0458 CYRILLIC SMALL LETTER JE
        'о' => 'o', // U+043E CYRILLIC SMALL LETTER O
        'р' => 'p', // U+0440 CYRILLIC SMALL LETTER ER
        'ѕ' => 's', // U+0455 CYRILLIC SMALL LETTER DZE
        'у' => 'y', // U+0443 CYRILLIC SMALL LETTER U
        'х' => 'x', // U+0445 CYRILLIC SMALL LETTER HA
        'ѡ' => 'w', // U+0461 CYRILLIC SMALL LETTER OMEGA
        'α' => 'a', // U+03B1 GREEK SMALL LETTER ALPHA
        'ε' => 'e', // U+03B5 GREEK SMALL LETTER EPSILON
        'ι' => 'i', // U+03B9 GREEK SMALL LETTER IOTA
        'κ' => 'k', // U+03BA GREEK SMALL LETTER KAPPA
        'ν' => 'v', // U+03BD GREEK SMALL LETTER NU
        'ο' => 'o', // U+03BF GREEK SMALL LETTER OMICRON
        'ρ' => 'p', // U+03C1 GREEK SMALL LETTER RHO
        'τ' => 't', // U+03C4 GREEK SMALL LETTER TAU
        'υ' => 'u', // U+03C5 GREEK SMALL LETTER UPSILON
        other => other,
    }
}

/// Normalize a candidate-supplied JSON key for counsel-assertion matching:
/// Unicode NFKD (fully decomposes fullwidth/compatibility forms AND
/// canonically-composed accented letters into base-letter + combining marks,
/// WITHOUT recomposing them - unlike NFKC, which recomposes a canonical
/// pair such as U+0075 U+0308 back into the precomposed U+00FC 'u' and so
/// never exposes the bare ASCII base letter for the alphanumeric filter
/// below), Unicode lowercase, confusable fold, then squash to ASCII
/// alphanumerics only. That final filter now does double duty: it both
/// strips separators (`_`, `-`, spaces, zero-width joiners) AND strips the
/// leftover combining diacritical marks NFKD exposed, so any precomposed
/// Latin letter with a canonical decomposition (grave/acute/diaeresis/tilde/
/// circumflex/ring/cedilla/etc. - e.g. `co\u{FC}nsel_fto` -> `counselfto`)
/// folds to its bare ASCII base letter instead of the letter being silently
/// DELETED (verify V-B01: U+00FC 'u-diaeresis' had no NFKC *compatibility*
/// decomposition, only a *canonical* one NFKC recomposes away, so it fell
/// through fold_confusable's hand-picked Cyrillic/Greek table and was
/// dropped whole by the old ascii-alphanumeric filter, breaking the
/// `counsel` substring match). Letters with NO canonical or compatibility
/// decomposition at all (genuinely distinct glyphs, e.g. Cyrillic/Greek
/// homoglyphs) still rely on the explicit `fold_confusable` table.
fn normalized_key_skeleton(key: &str) -> String {
    use unicode_normalization::UnicodeNormalization;
    key.nfkd()
        .flat_map(char::to_lowercase)
        .map(fold_confusable)
        .filter(char::is_ascii_alphanumeric)
        .collect()
}

/// True when a single normalized key encodes a candidate-supplied counsel/FTO
/// sign-off assertion: either an exact canonical name, or any two of the three
/// semantic token classes {counsel party, freedom-to-operate, sign-off or
/// clearance}. Examples caught: `signed_by_counsel`, `Signed_By_Counsel`,
/// `counsel_fto`, `counsel_signoff`, `fto_cleared_by_counsel`,
/// `fto_clearance`, and unicode-homoglyph spellings of any of these.
fn key_asserts_counsel_signoff(key: &str) -> bool {
    let skeleton = normalized_key_skeleton(key);
    if COUNSEL_ASSERTION_CANONICAL_KEYS.contains(&skeleton.as_str()) {
        return true;
    }
    let counsel_party = ["counsel", "attorney", "lawyer"]
        .iter()
        .any(|token| skeleton.contains(token));
    let freedom_to_operate =
        skeleton.contains("fto") || skeleton.contains("freedomtooperate");
    let sign_off = ["sign", "clear", "approv", "grant", "confirm", "attest"]
        .iter()
        .any(|token| skeleton.contains(token));
    u8::from(counsel_party) + u8::from(freedom_to_operate) + u8::from(sign_off) >= 2
}

/// Reference-monitor scan over the WHOLE candidate value (Anderson 1980
/// complete mediation; Saltzer & Schroeder 1975): flag a counsel-signoff
/// assertion keyed under ANY container type (object, array, string, bool,
/// number, null) at ANY nesting depth. Matching is on normalized key names,
/// so top-level placement, deeper nesting, key-case variants, alternate key
/// names, semantically-equivalent fields, non-object containers, and
/// unicode-homoglyph keys are all mediated.
fn counsel_signoff_assertion_present(value: &Value) -> bool {
    match value {
        Value::Object(map) => map.iter().any(|(key, child)| {
            key_asserts_counsel_signoff(key) || counsel_signoff_assertion_present(child)
        }),
        Value::Array(items) => items.iter().any(counsel_signoff_assertion_present),
        _ => false,
    }
}

fn evaluate_ip_fto_guard(candidate: &CandidateEnvelope) -> ModuleResult {
    let boolean_assertion_supplied = counsel_signoff_assertion_present(candidate.value());
    let landscape = embedded_json(PATENT_LANDSCAPE);
    let family_count = landscape
        .get("families")
        .and_then(Value::as_array)
        .map_or(0, Vec::len);
    let sweep_count = landscape
        .get("cpc_ipc_sweeps")
        .and_then(Value::as_array)
        .map_or(0, Vec::len);
    // Primary KPI value path (docs/mission.md, docs/capability-profile.json
    // kpis[0]): `metrics.unresolved_technical_categories` - the number of
    // technical claim-chart categories surfaced by the landscape screen that
    // remain unresolved and require qualified counsel review. This module can
    // never resolve a category itself (resolution would be a legal
    // conclusion), so a category counts as unresolved unless the checked
    // landscape explicitly records `not_fto: false`. Fail-closed nullability:
    // an absent or empty category census yields null, never 0 - a zero would
    // implicitly assert "nothing left for counsel", which is a clearance-type
    // claim this module is forbidden to make (repair R-B01 for
    // evidence/audit/metric-schema-parity-v1).
    let unresolved_technical_categories = landscape
        .get("claim_chart_categories")
        .and_then(Value::as_array)
        .map(|categories| {
            categories
                .iter()
                .filter(|category| category.get("not_fto").and_then(Value::as_bool) != Some(false))
                .count()
        })
        .filter(|count| *count > 0);
    let mut result = base_result("SCORED", Some(0.0), "technical_ip_landscape");
    result.metrics.extend(BTreeMap::from([
        ("fto_status".into(), json!("FTO NOT PERFORMED")),
        ("legal_advice".into(), Value::Bool(false)),
        (
            "boolean_counsel_assertion_ignored".into(),
            Value::Bool(boolean_assertion_supplied),
        ),
        ("public_family_count".into(), json!(family_count)),
        ("classification_sweep_count".into(), json!(sweep_count)),
        (
            "unresolved_technical_categories".into(),
            unresolved_technical_categories.map_or(Value::Null, |count| json!(count)),
        ),
    ]));
    result.gates.extend(BTreeMap::from([
        (
            "technical_landscape_present".into(),
            Value::Bool(family_count != 0 && sweep_count != 0),
        ),
        ("fto_legal_closure".into(), Value::Bool(false)),
    ]));
    result
        .explanations
        .push("Technical patent screening is not legal advice. FTO NOT PERFORMED.".into());
    bind_artifacts(&mut result, &[(PATENT_LANDSCAPE_PATH, PATENT_LANDSCAPE)]);
    result
}

fn evaluate_report_packager() -> ModuleResult {
    let generated_document_count = REPORT_ARTIFACTS
        .iter()
        .filter(|(_, bytes)| !bytes.is_empty())
        .count();
    let mut result = base_result("INSUFFICIENT_INPUT", None, "report_package");
    result.metrics.extend(BTreeMap::from([
        (
            "generated_document_count".into(),
            json!(generated_document_count),
        ),
        ("signed_report_package_present".into(), Value::Bool(false)),
    ]));
    result.gates.extend(BTreeMap::from([
        ("score_envelopes_valid".into(), Value::Bool(false)),
        ("authority_lock_present".into(), Value::Bool(false)),
        ("banned_claim_lint_pass".into(), Value::Bool(false)),
        ("signed_report_package_present".into(), Value::Bool(false)),
    ]));
    result
        .missing_inputs
        .push("registry-verified score envelopes and a signed deterministic report package".into());
    result.explanations.push(
        "Human deliverables remain downstream of sealed score envelopes and authority locks."
            .into(),
    );
    bind_artifacts(&mut result, &REPORT_ARTIFACTS);
    result
}

fn evaluate_redteam_audit() -> ModuleResult {
    let diagnostic = deterministic_control_diagnostic(REDTEAM_AUDIT);
    let passed = diagnostic.is_ok();
    let mut result = base_result(
        if passed { "SCORED" } else { "FAILED_GATES" },
        Some(if passed { 1.0 } else { 0.0 }),
        "deterministic_policy_redteam",
    );
    result
        .gates
        .insert("redteam_acceptance".into(), Value::Bool(passed));
    match diagnostic {
        Ok(diagnostic) => {
            result.metrics.insert(
                "deterministic_control_diagnostic".into(),
                serde_json::to_value(diagnostic).expect("diagnostic serializes"),
            );
            result.explanations.push(
                "The locked deterministic policy corpus rejected all 30,000 negative states without granting authority."
                    .into(),
            );
        }
        Err(error) => {
            result.missing_inputs.push(error.clone());
            result.explanations.push(error);
        }
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use amphora_core::Capability;

    fn formulation_candidate() -> CandidateEnvelope {
        CandidateEnvelope::from_value(json!({
            "candidate_id": "formula-1",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"resin": 1.0}, "part_B": {"hardener": 1.0}}
        }))
        .expect("valid formulation candidate")
    }

    fn evidence_candidate() -> CandidateEnvelope {
        CandidateEnvelope::from_value(json!({
            "candidate_id": "evidence-1",
            "candidate_type": "evidence_package",
            "evidence_refs": {
                "evidence_package": {
                    "candidate_id": "evidence-1",
                    "lab_package_signature": {
                        "schema": "amphora.cryptographic-signature-evidence.v1",
                        "algorithm": "ED25519",
                        "signature": "ab".repeat(64),
                        "verification_receipt": {"status": "VERIFIED"}
                    }
                }
            }
        }))
        .expect("valid evidence candidate")
    }

    fn context() -> ExecutionContext {
        ExecutionContext {
            run_id: "test-run".into(),
            deterministic_seed: 42,
            lineage: Value::Null,
        }
    }

    #[test]
    fn constructor_rejects_unsupported_ids_and_descriptors_are_non_engine() {
        assert!(AssuranceCapability::new("unknown-module").is_err());
        for module_id in SUPPORTED_MODULE_IDS {
            let capability = AssuranceCapability::new(module_id).expect("supported module");
            assert!(!capability.descriptor().ranking_eligible);
            assert_eq!(capability.descriptor().solver_use_ceiling, "DISABLED");
            assert!(!capability.descriptor().non_blocking_claim_locks.is_empty());
        }
    }

    #[test]
    fn candidate_types_are_enforced() {
        let capability = AssuranceCapability::new(SOURCE_LEDGER).unwrap();
        let error = capability
            .evaluate(
                &formulation_candidate(),
                &FeatureSnapshot::default(),
                &context(),
            )
            .unwrap_err();
        assert!(matches!(error, CapabilityError::CandidateType));
    }

    #[test]
    fn every_assurance_result_has_an_empty_objective_vector() {
        for module_id in SUPPORTED_MODULE_IDS {
            let capability = AssuranceCapability::new(module_id).unwrap();
            let candidate = if capability.descriptor().candidate_types == ["formulation"] {
                formulation_candidate()
            } else {
                evidence_candidate()
            };
            let result = capability
                .evaluate(&candidate, &FeatureSnapshot::default(), &context())
                .unwrap();
            assert!(result.objective_values.is_empty(), "{module_id}");
        }
    }

    #[test]
    fn results_are_deterministic_and_cannot_supply_registry_fields() {
        let capability = AssuranceCapability::new(IP_FTO_GUARD).unwrap();
        let candidate = formulation_candidate();
        let first = capability
            .evaluate(
                &candidate,
                &FeatureSnapshot::default(),
                &ExecutionContext {
                    run_id: "first-run".into(),
                    deterministic_seed: 1,
                    lineage: json!({"wall_clock": "excluded"}),
                },
            )
            .unwrap();
        let second = capability
            .evaluate(
                &candidate,
                &FeatureSnapshot::default(),
                &ExecutionContext {
                    run_id: "second-run".into(),
                    deterministic_seed: u64::MAX,
                    lineage: json!({"wall_clock": "different"}),
                },
            )
            .unwrap();
        let first = serde_json::to_value(first).unwrap();
        let second = serde_json::to_value(second).unwrap();
        assert_eq!(first, second);
        for registry_field in [
            "module_id",
            "authority_tier",
            "claim_locks",
            "usable_by_optimizer",
        ] {
            assert!(first.get(registry_field).is_none(), "{registry_field}");
        }
    }

    #[test]
    fn fto_guard_never_reports_legal_closure() {
        let capability = AssuranceCapability::new(IP_FTO_GUARD).unwrap();
        let result = capability
            .evaluate(
                &formulation_candidate(),
                &FeatureSnapshot::default(),
                &context(),
            )
            .unwrap();
        assert_eq!(result.metrics["fto_status"], json!("FTO NOT PERFORMED"));
        assert_eq!(result.metrics["legal_advice"], Value::Bool(false));
        assert_eq!(result.gates["fto_legal_closure"], Value::Bool(false));
        assert!(result.objective_values.is_empty());
    }

    #[test]
    fn candidate_supplied_signature_shape_fails_closed() {
        let capability = AssuranceCapability::new(EVIDENCE_INTAKE).unwrap();
        let result = capability
            .evaluate(
                &evidence_candidate(),
                &FeatureSnapshot::default(),
                &context(),
            )
            .unwrap();
        assert_eq!(result.status, "FAILED_GATES");
        assert_eq!(
            result.gates["host_verified_signature_receipt"],
            Value::Bool(false)
        );
        assert_eq!(
            result.gates["evidence_package_accepted"],
            Value::Bool(false)
        );
    }

    #[test]
    fn correctly_bound_host_receipt_can_accept_evidence() {
        let candidate = evidence_candidate();
        let package = &candidate.value()["evidence_refs"]["evidence_package"];
        let package_sha256 = stable_hash(package);
        let mut features = FeatureSnapshot::default();
        features.values.insert(
            HOST_VERIFIED_RECEIPT_FEATURE.into(),
            json!({
                "schema": HOST_VERIFIED_RECEIPT_SCHEMA,
                "accepted": true,
                "signature_verified": true,
                "revocation_checked": true,
                "fresh": true,
                "signature_algorithm": "Ed25519",
                "trust_store_status": "TRUSTED",
                "candidate_id": candidate.candidate_id(),
                "candidate_contract_hash_v1": candidate.contract_hash_v1(),
                "package_sha256": package_sha256,
                "verifier_id": "host-trust-kernel"
            }),
        );

        let result = AssuranceCapability::new(EVIDENCE_INTAKE)
            .unwrap()
            .evaluate(&candidate, &features, &context())
            .unwrap();
        assert_eq!(result.status, "SCORED");
        assert_eq!(result.gates["evidence_package_accepted"], Value::Bool(true));
        assert!(result.objective_values.is_empty());
    }

    #[test]
    fn current_source_and_known_answer_gates_remain_failed() {
        let source = AssuranceCapability::new(SOURCE_LEDGER)
            .unwrap()
            .evaluate(
                &evidence_candidate(),
                &FeatureSnapshot::default(),
                &context(),
            )
            .unwrap();
        assert_eq!(source.status, "FAILED_GATES");
        assert_eq!(
            source.gates["load_bearing_two_source_or_waiver"],
            Value::Bool(false)
        );

        let known = AssuranceCapability::new(KNOWN_ANSWERS)
            .unwrap()
            .evaluate(
                &formulation_candidate(),
                &FeatureSnapshot::default(),
                &context(),
            )
            .unwrap();
        assert_eq!(known.status, "FAILED_GATES");
        assert_eq!(known.gates["known_answer_audit_passed"], Value::Bool(false));
    }

    #[test]
    fn cro_v2_packet_is_candidate_formula_signed_and_non_executable() {
        let balance = EquivalentBalanceV1 {
            schema: amphora_formulation_capabilities::EQUIVALENT_BALANCE_SCHEMA.into(),
            resin_facts_sha256: "a".repeat(64),
            hardener_facts_sha256: "b".repeat(64),
            resin_structure_sha256: "c".repeat(64),
            hardener_structure_sha256: "d".repeat(64),
            eew_g_per_eq: 100.0,
            ahew_g_per_eq: 25.0,
            resin_mass_g: 100.0,
            hardener_mass_g: 25.0,
            epoxide_equivalents: 1.0,
            amine_hydrogen_equivalents: 1.0,
            theoretical_hardener_phr: 25.0,
            equivalent_ratio: 1.0,
            total_mass_g: 125.0,
            unit_provenance: BTreeMap::from([("mass".into(), "g".into())]),
            authority_ceiling: "AUDIT_ONLY".into(),
            candidate_property_overrides_accepted: false,
            ranking_eligible: false,
        };
        let candidate = json!({"resin":"c", "hardener":"d"});
        let mut packet =
            CroProtocolPackageV2::draft("campaign", &candidate, balance, "BLIND-001".into())
                .unwrap();
        let key = SigningKey::from_bytes(&[91; 32]);
        let mut trust = TrustStore::default();
        trust
            .insert("packet-signer", key.verifying_key().to_bytes())
            .unwrap();
        packet.sign("packet-signer", &key).unwrap();
        assert_eq!(packet.verify_signature(&trust).unwrap(), "packet-signer");
        assert_eq!(packet.candidate_sha256, stable_hash(&candidate));
        assert!(!packet.execution_authorized);
        assert!(!packet.ranking_eligible);
        let mut forged = packet.clone();
        forged.execution_authorized = true;
        assert!(forged.validate().is_err());
    }
}
