#![forbid(unsafe_code)]

mod artifacts;
mod capability;
mod compound;
mod compound_v2;
mod contract;
mod crypto;
mod data_v2;
mod evidence;
mod jcs;
mod molecule_evidence;
mod phase0;
mod phase1;
mod read_only;
mod technical;

pub use artifacts::{
    ArtifactError, BenchmarkLockV1, ConfidenceIntervalV1, DatasetManifestV1, DecisionUse,
    EvaluationReceiptV1, EvidenceTier, MetricLockV1, ModelArtifactV1, PromotionPolicyV1,
    PromotionRuleV1, RightsRecordV1, RowProvenanceV1, SignedModelArtifactV1, SplitAssignmentV1,
    SplitManifestV1, BENCHMARK_LOCK_SCHEMA, DATASET_MANIFEST_SCHEMA,
    EVALUATION_RECEIPT_PAYLOAD_TYPE, EVALUATION_RECEIPT_SCHEMA, MODEL_ARTIFACT_PAYLOAD_TYPE,
    MODEL_ARTIFACT_SCHEMA, PROMOTION_POLICY_SCHEMA, SIGNED_MODEL_ARTIFACT_SCHEMA,
    SPLIT_MANIFEST_SCHEMA,
};
pub use capability::{
    Capability, CapabilityError, ExecutionContext, FeatureSnapshot, ModuleDescriptor, ModuleResult,
};
pub use compound::{
    CampaignCohortThresholdsV1, CampaignExecutionProfileV1, CampaignGenerationRequestV1,
    CampaignPairingRuleV1, CampaignRejectedCandidateV1, CampaignSnapshotBindingV1,
    CampaignStageCountsV1, CompoundCampaignError, CompoundCampaignResultV1, CompoundCampaignV1,
    GeneratedCompoundV1, OrdSnapshotBindingV1, RdkitBuildBindingV1,
    COMPOUND_CAMPAIGN_RESULT_SCHEMA, COMPOUND_CAMPAIGN_SCHEMA, COMPOUND_EXECUTION_PROFILE_SCHEMA,
};
pub use compound_v2::{
    required_compound_report_modules, verify_toolchain_profile, AuthorizedCampaignGrammarV1,
    CampaignArtifactBindingsV1, CampaignAttemptKindV1, CampaignAttemptV1,
    CampaignExecutionReceiptV1, CampaignIndependentReviewReceiptV1, CampaignRateRepeatV1,
    CompoundCampaignResultV2, CompoundCampaignV2, CompoundCardV1, CompoundPairContextV1,
    CompoundV2Error, FileArtifactBindingV1, InstalledFileV1, MeasuredScalarV1,
    MethodBenchmarkLockV1, MethodCardV1, MethodLockPayloadV1, MethodRegistryV1,
    ModuleOutcomeStatusV1, ModuleOutcomeV1, OrdBondChangeKindV1, OrdBondChangeV1, OrdCompoundV1,
    OrdDatasetRecordV1, OrdExclusionReasonV1, OrdExclusionScopeV1, OrdExclusionV1,
    OrdReactionCenterV1, OrdReactionRecordV1, OrdSchemaIdentityV1, ReactionComponentV1,
    ReactionGrammarCorpusV1, ReactionGrammarRuleV1, ReactionSplitComponentV1,
    ReactionSplitManifestV1, ReportLaneV1, SharedLibraryV1, StructureRenderBindingV1,
    ToolchainDependencyV1, ToolchainManifestV1, ToolchainPgoV1, ToolchainReproducibilityV1,
    ToolchainTestReceiptV1, CAMPAIGN_EXECUTION_RECEIPT_SCHEMA,
    CAMPAIGN_INDEPENDENT_REVIEW_RECEIPT_SCHEMA, CAMPAIGN_MANIFEST_PAYLOAD_TYPE,
    COMPOUND_CAMPAIGN_RESULT_SCHEMA_V2, COMPOUND_CAMPAIGN_SCHEMA_V2, COMPOUND_CARD_SCHEMA,
    METHOD_BENCHMARK_LOCK_SCHEMA, METHOD_REGISTRY_SCHEMA, ORD_EXCLUSION_SCHEMA,
    ORD_REACTION_RECORD_SCHEMA, ORD_SCHEMA_IDENTITY_SCHEMA, REACTION_GRAMMAR_CORPUS_SCHEMA,
    REACTION_SPLIT_MANIFEST_SCHEMA, TOOLCHAIN_MANIFEST_SCHEMA,
};
pub use contract::{
    parse_json_strict, CandidateEnvelope, ContractError, MAX_COLLECTION_ENTRIES, MAX_JSON_BYTES,
    MAX_JSON_DEPTH,
};
pub use crypto::{
    sign_dsse, verify_dsse, verify_remote_result, DsseEnvelope, DsseSignature, RemoteResultBinding,
    TrustStore, VerificationError, VerifiedPayload,
};
pub use data_v2::{
    load_rights_trust_store, load_verified_module_dataset, verify_activation_authorization,
    AcquisitionUnitV2, AuthorizationOverlayRefV1, ConsumerKind, DataCatalogV2,
    DataSnapshotParentV1, DatasetConsumerV2, DerivedRecordV1, EvidenceClass, LoadedRightsTrust,
    ModuleDatasetActivationSetV1, ModuleDatasetActivationV1, ModuleDatasetAuthorizationLedgerV1,
    ModuleDatasetAuthorizationOverlayV1, ModuleDatasetLockV2, NormalizedDatasetManifestV2,
    NormalizedRecordV2, OrdGitLfsObjectV1, OrdGitLfsTreeV1, ParserKind, Phase0ExcludedSourceV2,
    Phase0SourceLockV2, Phase0SourceRefV2, RightsClass, RightsDecisionV2, RightsReviewReceiptV1,
    RightsTrustKeyV1, RightsTrustStoreV1, SourceIntentV2, VerifiedModuleDatasetV1,
    ACTIVATION_SCHEMA, ACTIVATION_SET_SCHEMA, AUTHORIZATION_LEDGER_SCHEMA,
    AUTHORIZATION_OVERLAY_SCHEMA, DATASET_MANIFEST_V2_SCHEMA, DERIVED_RECORD_SCHEMA,
    MODULE_DATASET_LOCK_SCHEMA, NORMALIZED_RECORD_SCHEMA, PHASE0_SOURCE_LOCK_V2_SCHEMA,
    RIGHTS_REVIEW_PAYLOAD_TYPE, RIGHTS_REVIEW_RECEIPT_SCHEMA, RIGHTS_TRUST_STORE_SCHEMA,
};
pub use evidence::{intake_regular_file, AcceptedArtifact, EvidenceIntakeError};
pub use jcs::{jcs_bytes, jcs_sha256, verify_jcs_sha256, JcsError};
pub use molecule_evidence::{
    AuditInputBindingKindV1, AuthorizedAuditModuleInputV1, AuthorizedMoleculeModelInputV1,
    EngineEvidenceContextV1, EngineEvidenceContextV2, EngineEvidenceContextV3,
    IndependentReviewReceiptV1, MoleculeEvidenceError, ValidatedEngineEvidenceContextV1,
    ValidatedEngineEvidenceContextV2, ValidatedEngineEvidenceContextV3, VerifiedAuditModuleInputV1,
    VerifiedMoleculeModelInputV1, ENGINE_EVIDENCE_CONTEXT_SCHEMA,
    ENGINE_EVIDENCE_CONTEXT_V2_SCHEMA, ENGINE_EVIDENCE_CONTEXT_V3_SCHEMA,
    INDEPENDENT_REVIEW_RECEIPT_PAYLOAD_TYPE, INDEPENDENT_REVIEW_RECEIPT_SCHEMA,
    SPC_AUDIT_TOOLKIT_VERSION, VERIFIED_AUDIT_MODULE_INPUT_SCHEMA,
    VERIFIED_MOLECULE_MODEL_INPUT_SCHEMA,
};
pub use phase0::{
    DeterministicControlDiagnosticV1, ModuleClaimContractV1, ModuleMovementEventV1,
    ModulePhase0BundleV1, ModulePhase0EvaluationReceiptV1, ModulePhase0PreparationLedgerV1,
    ModulePhase0PreparationRevisionV1, ModulePhase0ReviewReceiptV1, ModulePhase0SupersessionV1,
    ModuleRegistrySuccessionChainV1, ModuleRegistrySuccessionV1, Phase0ContractError,
    PreparationRevisionRefV1, RegistryManifestRefV1, RegistrySuccessionEditV1,
    RegistrySuccessionRecordRefV1, ScientificOutcomeV1, DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA,
    MODULE_CLAIM_CONTRACT_SCHEMA, MODULE_MOVEMENT_EVENT_SCHEMA, MODULE_PHASE0_BUNDLE_SCHEMA,
    MODULE_PHASE0_EVALUATION_PAYLOAD_TYPE, MODULE_PHASE0_EVALUATION_RECEIPT_SCHEMA,
    MODULE_PHASE0_PREPARATION_LEDGER_SCHEMA, MODULE_PHASE0_PREPARATION_REVISION_SCHEMA,
    MODULE_PHASE0_REVIEW_PAYLOAD_TYPE, MODULE_PHASE0_REVIEW_RECEIPT_SCHEMA,
    MODULE_PHASE0_SUPERSESSION_SCHEMA, MODULE_REGISTRY_SUCCESSION_CHAIN_SCHEMA,
    MODULE_REGISTRY_SUCCESSION_SCHEMA, PHASE0_INDEPENDENCE_SCOPE, PHASE0_REVIEW_METHOD,
    REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS,
};
pub use phase1::{
    ModulePhase1BundleV1, ModulePhase1EvaluationReceiptV1, ModulePhase1MovementEventV1,
    ModulePhase1ReviewReceiptV1, Phase1ContractError, Phase1ModuleStatusV1,
    Phase1PortfolioStatusV1, MODULE_PHASE1_BUNDLE_SCHEMA, MODULE_PHASE1_EVALUATION_PAYLOAD_TYPE,
    MODULE_PHASE1_EVALUATION_RECEIPT_SCHEMA, MODULE_PHASE1_MOVEMENT_EVENT_SCHEMA,
    MODULE_PHASE1_REVIEW_PAYLOAD_TYPE, MODULE_PHASE1_REVIEW_RECEIPT_SCHEMA,
    PHASE1_INDEPENDENCE_SCOPE, PHASE1_REVIEW_METHOD,
};
pub use read_only::{prove_read_only, repository_tree_hash, ReadOnlyError};
pub use technical::{
    CampaignEndpointLinkV1, CampaignInstrumentV1, CampaignSampleV1, ClosestArtElementChartV1,
    CorrosionEndpointV1, CorrosionObservationV1, CureEndpointV1, CureObservationV1,
    DisclosureLogEntryV1, EisSpectrumKindV1, ExperimentalCampaignV1, HostileNullAblationV1,
    IpDispositionV1, IpRecommendationV1, ObservationQcStatusV1, SourceBindingV1,
    TechnicalContractError, TechnicalIpDossierV1, VerifiedFormulationModelInputV1,
    VerifiedFormulationModelInputV2, VerifiedModelInputV1, CORROSION_OBSERVATION_SCHEMA,
    CURE_OBSERVATION_SCHEMA, EXPERIMENTAL_CAMPAIGN_SCHEMA, TECHNICAL_IP_DOSSIER_SCHEMA,
    VERIFIED_FORMULATION_MODEL_INPUT_SCHEMA, VERIFIED_FORMULATION_MODEL_INPUT_V2_SCHEMA,
    VERIFIED_MODEL_INPUT_SCHEMA,
};

use serde::{de::DeserializeOwned, Deserialize, Serialize};
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use thiserror::Error;

pub fn canonicalize(value: &Value) -> Value {
    match value {
        Value::Object(object) => {
            let mut ordered = Map::new();
            let mut keys: Vec<_> = object.keys().cloned().collect();
            keys.sort();
            for key in keys {
                ordered.insert(key.clone(), canonicalize(&object[&key]));
            }
            Value::Object(ordered)
        }
        Value::Array(values) => Value::Array(values.iter().map(canonicalize).collect()),
        other => other.clone(),
    }
}

pub fn stable_hash(value: &Value) -> String {
    let bytes = serde_json::to_vec(&canonicalize(value)).expect("JSON values are serializable");
    raw_sha256(&bytes)
}

fn raw_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CandidateStatus {
    Proposed,
    Rejected,
    Repaired,
    Scored,
    Ranked,
    Survivor,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ObjectiveRow {
    pub id: String,
    pub module_id: String,
    pub path: String,
    pub value: f64,
    pub direction: String,
    pub unit: String,
    pub eligible: bool,
    pub pareto_rank: Option<usize>,
    pub normalized_value: Option<f64>,
}

pub type ClaimLocksByModule = BTreeMap<String, Value>;

pub fn collect_claim_locks(result: &Value) -> ClaimLocksByModule {
    result
        .pointer("/score_envelopes")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|envelope| {
            Some((
                envelope.get("module_id")?.as_str()?.to_owned(),
                envelope.get("claim_locks")?.clone(),
            ))
        })
        .collect()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CandidateRecord {
    pub candidate_id: String,
    pub candidate_type: String,
    pub candidate: Value,
    pub canonical_structure_hash: Option<String>,
    pub parent_ids: Vec<String>,
    pub generation: u32,
    pub mutation_id: Option<String>,
    pub lifecycle_status: CandidateStatus,
    pub result_hash: Option<String>,
    pub objective_rows: Vec<ObjectiveRow>,
    pub hard_constraint_pass: Option<bool>,
    #[serde(default)]
    pub claim_locks: ClaimLocksByModule,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModuleTelemetry {
    pub module_id: String,
    pub authority_tier: String,
    pub readiness: String,
    pub active: bool,
    pub attempted_count: u64,
    pub scored_count: u64,
    pub failed_count: u64,
    pub insufficient_count: u64,
    pub last_status: String,
    pub last_score: Option<f64>,
    pub average_latency_ms: f64,
    pub last_latency_ms: u64,
}

impl ModuleTelemetry {
    pub fn new(module_id: impl Into<String>) -> Self {
        Self {
            module_id: module_id.into(),
            authority_tier: "UNKNOWN".into(),
            readiness: "UNKNOWN".into(),
            active: true,
            attempted_count: 0,
            scored_count: 0,
            failed_count: 0,
            insufficient_count: 0,
            last_status: "PENDING".into(),
            last_score: None,
            average_latency_ms: 0.0,
            last_latency_ms: 0,
        }
    }

    pub fn record(&mut self, status: &str, score: Option<f64>, latency_ms: u64) {
        self.attempted_count += 1;
        self.last_status = status.to_string();
        self.last_score = score;
        self.last_latency_ms = latency_ms;
        self.average_latency_ms = ((self.average_latency_ms * (self.attempted_count - 1) as f64)
            + latency_ms as f64)
            / self.attempted_count as f64;
        match status {
            "SCORED" => self.scored_count += 1,
            "INSUFFICIENT_INPUT" | "INSUFFICIENT" => self.insufficient_count += 1,
            _ => self.failed_count += 1,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Throughput {
    pub attempted: u64,
    pub valid: u64,
    pub scored: u64,
    pub survivors: u64,
    pub solutions: u64,
    pub started_at_ms: u128,
    pub recent: Vec<ThroughputSample>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThroughputSample {
    pub at_ms: u128,
    pub attempted: u64,
    pub valid: u64,
    pub scored: u64,
    pub survivors: u64,
    pub solutions: u64,
}

impl Default for Throughput {
    fn default() -> Self {
        Self {
            attempted: 0,
            valid: 0,
            scored: 0,
            survivors: 0,
            solutions: 0,
            started_at_ms: now_ms(),
            recent: Vec::new(),
        }
    }
}

impl Throughput {
    pub fn sample(
        &mut self,
        attempted: u64,
        valid: u64,
        scored: u64,
        survivors: u64,
        solutions: u64,
    ) {
        self.attempted = self.attempted.saturating_add(attempted);
        self.valid = self.valid.saturating_add(valid);
        self.scored = self.scored.saturating_add(scored);
        self.survivors = self.survivors.saturating_add(survivors);
        self.solutions = self.solutions.saturating_add(solutions);
        self.recent.push(ThroughputSample {
            at_ms: now_ms(),
            attempted: self.attempted,
            valid: self.valid,
            scored: self.scored,
            survivors: self.survivors,
            solutions: self.solutions,
        });
        if self.recent.len() > 25 {
            let drain = self.recent.len() - 25;
            self.recent.drain(..drain);
        }
    }

    pub fn run_rates(&self, at_ms: u128) -> [f64; 5] {
        let (started, counts) = self.recent.first().map_or(
            (self.started_at_ms, [0_u64, 0_u64, 0_u64, 0_u64, 0_u64]),
            |sample| {
                (
                    sample.at_ms,
                    [
                        sample.attempted,
                        sample.valid,
                        sample.scored,
                        sample.survivors,
                        sample.solutions,
                    ],
                )
            },
        );
        let elapsed = at_ms.saturating_sub(started).max(1) as f64 / 1000.0;
        let current = [
            self.attempted,
            self.valid,
            self.scored,
            self.survivors,
            self.solutions,
        ];
        std::array::from_fn(|index| current[index].saturating_sub(counts[index]) as f64 / elapsed)
    }
}

pub fn now_ms() -> u128 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KpiProfile {
    pub schema: String,
    pub profile_id: String,
    pub objectives: Vec<KpiObjective>,
    pub hard_constraints: Vec<HardConstraint>,
    pub display_kpis: Vec<DisplayKpi>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KpiObjective {
    pub id: String,
    pub module_id: String,
    pub section: String,
    pub path: String,
    pub label: String,
    pub direction: String,
    pub unit: String,
    pub weight: f64,
    pub display_lower: f64,
    pub display_upper: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HardConstraint {
    pub id: String,
    pub module_id: String,
    pub section: String,
    pub path: String,
    pub label: String,
    pub operator: String,
    pub expected: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DisplayKpi {
    pub id: String,
    pub module_id: String,
    pub section: String,
    pub path: String,
    pub label: String,
    pub unit: String,
    pub direction: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DisplayKpiValue {
    pub id: String,
    pub label: String,
    pub unit: String,
    pub value: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ChemicalPreview {
    pub canonical_smiles: String,
    pub role: String,
    pub name: String,
    pub ascii_lines: Vec<String>,
    pub render_status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RankedCandidate {
    pub candidate_id: String,
    #[serde(default)]
    pub current_rank: Option<usize>,
    #[serde(default)]
    pub previous_rank: Option<usize>,
    #[serde(default)]
    pub rank_delta: Option<i64>,
    #[serde(default = "default_movement")]
    pub movement: String,
    pub feasible: bool,
    pub ranked: bool,
    pub pareto_rank: Option<usize>,
    pub moo_display_score: Option<f64>,
    pub eligible_objectives: usize,
    pub failed_modules: usize,
    pub objective_rows: Vec<ObjectiveRow>,
    #[serde(default)]
    pub claim_locks: ClaimLocksByModule,
    #[serde(default)]
    pub display_kpis: Vec<DisplayKpiValue>,
    #[serde(default)]
    pub mutation_id: Option<String>,
    #[serde(default)]
    pub parent_ids: Vec<String>,
    #[serde(default)]
    pub generation: u32,
    #[serde(default)]
    pub chemical_preview: Option<ChemicalPreview>,
}

fn default_movement() -> String {
    "—".into()
}

fn module_envelope<'a>(result: &'a Value, module_id: &str) -> Option<&'a Value> {
    result
        .pointer("/score_envelopes")?
        .as_array()?
        .iter()
        .find(|row| row.get("module_id").and_then(Value::as_str) == Some(module_id))
}

fn envelope_value<'a>(envelope: &'a Value, section: &str, path: &str) -> Option<&'a Value> {
    let section = envelope.get(section)?;
    path.split('.')
        .filter(|part| !part.is_empty())
        .try_fold(section, |value, part| value.get(part))
}

fn comparison_passes(actual: Option<&Value>, operator: &str, expected: &Value) -> bool {
    let Some(actual) = actual else { return false };
    match operator {
        "==" => actual == expected,
        "!=" => actual != expected,
        ">=" => actual
            .as_f64()
            .zip(expected.as_f64())
            .is_some_and(|(left, right)| left >= right),
        "<=" => actual
            .as_f64()
            .zip(expected.as_f64())
            .is_some_and(|(left, right)| left <= right),
        ">" => actual
            .as_f64()
            .zip(expected.as_f64())
            .is_some_and(|(left, right)| left > right),
        "<" => actual
            .as_f64()
            .zip(expected.as_f64())
            .is_some_and(|(left, right)| left < right),
        _ => false,
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct OptimizerObjectiveRequestV1 {
    pub objective_id: String,
    pub module_id: String,
    pub section: String,
    pub path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct OptimizerConstraintRequestV1 {
    pub constraint_id: String,
    pub module_id: String,
    pub section: String,
    pub path: String,
    pub operator: String,
    pub expected: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct OptimizerAuthorizationRequestV1 {
    pub schema: String,
    pub request_source: String,
    pub objectives: Vec<OptimizerObjectiveRequestV1>,
    pub hard_constraints: Vec<OptimizerConstraintRequestV1>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OptimizerRegistryPolicyV1 {
    pub schema: String,
    pub registered_modules: Vec<String>,
    pub ranking_enabled: bool,
    pub solver_enabled: bool,
    pub authority_expansion_allowed: bool,
    pub decision_use_ceiling: String,
    pub required_claim_locks: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct OptimizerEnvelopeV1 {
    pub module_id: String,
    pub status: String,
    pub authority_tier: String,
    pub solver_use_ceiling: String,
    pub ranking_eligible: bool,
    pub usable_by_optimizer: bool,
    pub objective_values: BTreeMap<String, Value>,
    pub gates: BTreeMap<String, Value>,
    pub claim_locks: BTreeMap<String, bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OptimizerAuthorizationV1 {
    pub status: String,
    pub hard_constraints_passed: bool,
    pub eligible_objective_count: usize,
    pub objective_values: BTreeMap<String, String>,
    pub ranking_performed: bool,
    pub solver_invoked: bool,
    pub usable_by_optimizer: bool,
    pub authority_upgrade: bool,
    pub candidate_created_evidence: bool,
}

const OPTIMIZER_MODULES: [&str; 29] = [
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
];

pub fn quarantined_optimizer_policy() -> OptimizerRegistryPolicyV1 {
    OptimizerRegistryPolicyV1 {
        schema: "amphora.optimizer-registry-policy.v1".into(),
        registered_modules: OPTIMIZER_MODULES
            .iter()
            .map(|module| (*module).into())
            .collect(),
        ranking_enabled: false,
        solver_enabled: false,
        authority_expansion_allowed: false,
        decision_use_ceiling: "AUDIT_ONLY".into(),
        required_claim_locks: REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS
            .iter()
            .map(|lock| (*lock).into())
            .collect(),
    }
}

/// Shared fail-closed authorization used before any runtime ranking and by the
/// deterministic Phase-0 diagnostic. Scientific objectives remain quarantined.
pub fn authorize_optimizer_request(
    request: &OptimizerAuthorizationRequestV1,
    envelopes: &[OptimizerEnvelopeV1],
    policy: &OptimizerRegistryPolicyV1,
) -> Result<OptimizerAuthorizationV1, String> {
    let registered: BTreeSet<_> = policy
        .registered_modules
        .iter()
        .map(String::as_str)
        .collect();
    let expected_modules: BTreeSet<_> = OPTIMIZER_MODULES.into_iter().collect();
    let required_locks: BTreeSet<_> = policy
        .required_claim_locks
        .iter()
        .map(String::as_str)
        .collect();
    let expected_locks: BTreeSet<_> = REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS.into_iter().collect();
    if request.schema != "amphora.optimizer-authorization-request.v1"
        || !matches!(request.request_source.as_str(), "POLICY" | "CANDIDATE")
        || policy.schema != "amphora.optimizer-registry-policy.v1"
        || policy.registered_modules.len() != registered.len()
        || registered != expected_modules
        || policy.ranking_enabled
        || policy.solver_enabled
        || policy.authority_expansion_allowed
        || policy.decision_use_ceiling != "AUDIT_ONLY"
        || required_locks != expected_locks
    {
        return Err("optimizer registry policy is altered or incomplete".into());
    }
    if request.request_source == "CANDIDATE" && !request.objectives.is_empty() {
        return Err("candidate objective injection is forbidden".into());
    }
    let mut envelope_by_module = BTreeMap::new();
    for envelope in envelopes {
        if !registered.contains(envelope.module_id.as_str())
            || envelope_by_module
                .insert(envelope.module_id.as_str(), envelope)
                .is_some()
        {
            return Err("optimizer envelope module is unknown or duplicated".into());
        }
        if envelope.ranking_eligible
            || envelope.usable_by_optimizer
            || !envelope.objective_values.is_empty()
            || envelope.authority_tier.trim().is_empty()
            || matches!(
                envelope.authority_tier.as_str(),
                "RANKING" | "OPTIMIZER" | "PRODUCTION"
            )
            || !matches!(
                envelope.solver_use_ceiling.as_str(),
                "DISABLED" | "AUDIT_ONLY" | "CONSTRAINT_ONLY"
            )
            || policy
                .required_claim_locks
                .iter()
                .any(|lock| envelope.claim_locks.get(lock).copied() != Some(true))
        {
            return Err(
                "optimizer envelope attempts authority, score, solver, or lock escalation".into(),
            );
        }
    }
    let mut objective_ids = BTreeSet::new();
    for objective in &request.objectives {
        if objective.objective_id.trim().is_empty()
            || !objective_ids.insert(objective.objective_id.as_str())
            || !registered.contains(objective.module_id.as_str())
            || objective.section != "objective_values"
            || objective.path.trim().is_empty()
        {
            return Err(
                "optimizer objective declaration is unknown, duplicate, or malformed".into(),
            );
        }
    }
    let mut constraint_ids = BTreeSet::new();
    for constraint in &request.hard_constraints {
        if constraint.constraint_id.trim().is_empty()
            || !constraint_ids.insert(constraint.constraint_id.as_str())
            || !registered.contains(constraint.module_id.as_str())
            || constraint.section != "gates"
            || constraint.path.trim().is_empty()
            || !matches!(
                constraint.operator.as_str(),
                "==" | "!=" | ">=" | "<=" | ">" | "<"
            )
        {
            return Err(
                "optimizer constraint declaration is unknown, duplicate, or malformed".into(),
            );
        }
        let envelope = envelope_by_module
            .get(constraint.module_id.as_str())
            .ok_or("optimizer constraint module envelope is absent")?;
        if envelope.status != "SCORED" {
            return Err("optimizer constraint envelope is not SCORED".into());
        }
        let mut parts = constraint.path.split('.').filter(|part| !part.is_empty());
        let first = parts
            .next()
            .ok_or("optimizer constraint path is absent or unknown")?;
        let mut actual = envelope
            .gates
            .get(first)
            .ok_or("optimizer constraint path is absent or unknown")?;
        for part in parts {
            actual = actual
                .get(part)
                .ok_or("optimizer constraint path is absent or unknown")?;
        }
        if !comparison_passes(Some(actual), &constraint.operator, &constraint.expected) {
            return Err("optimizer hard constraint failed".into());
        }
    }
    Ok(OptimizerAuthorizationV1 {
        status: "NO_ELIGIBLE_OBJECTIVES".into(),
        hard_constraints_passed: true,
        eligible_objective_count: 0,
        objective_values: BTreeMap::new(),
        ranking_performed: false,
        solver_invoked: false,
        usable_by_optimizer: false,
        authority_upgrade: false,
        candidate_created_evidence: false,
    })
}

fn optimizer_envelopes(result: &Value) -> Result<Vec<OptimizerEnvelopeV1>, String> {
    result
        .pointer("/score_envelopes")
        .and_then(Value::as_array)
        .ok_or("score envelopes are absent")?
        .iter()
        .map(|envelope| {
            Ok(OptimizerEnvelopeV1 {
                module_id: envelope
                    .get("module_id")
                    .and_then(Value::as_str)
                    .ok_or("score envelope module_id is absent")?
                    .into(),
                status: envelope
                    .get("status")
                    .and_then(Value::as_str)
                    .ok_or("score envelope status is absent")?
                    .into(),
                authority_tier: envelope
                    .get("authority_tier")
                    .and_then(Value::as_str)
                    .ok_or("score envelope authority_tier is absent")?
                    .into(),
                solver_use_ceiling: envelope
                    .pointer("/metrics/solver_use")
                    .and_then(Value::as_str)
                    .ok_or("score envelope solver_use is absent")?
                    .into(),
                ranking_eligible: envelope
                    .pointer("/metrics/authority_receipt/ranking_eligible")
                    .and_then(Value::as_bool)
                    .ok_or("score envelope ranking lock is absent")?,
                usable_by_optimizer: envelope
                    .get("usable_by_optimizer")
                    .and_then(Value::as_bool)
                    .ok_or("score envelope optimizer lock is absent")?,
                objective_values: serde_json::from_value(
                    envelope
                        .get("objective_values")
                        .cloned()
                        .ok_or("score envelope objective vector is absent")?,
                )
                .map_err(|error| error.to_string())?,
                gates: serde_json::from_value(
                    envelope
                        .get("gates")
                        .cloned()
                        .ok_or("score envelope gates are absent")?,
                )
                .map_err(|error| error.to_string())?,
                claim_locks: serde_json::from_value(
                    envelope
                        .get("claim_locks")
                        .cloned()
                        .ok_or("score envelope claim locks are absent")?,
                )
                .map_err(|error| error.to_string())?,
            })
        })
        .collect()
}

pub fn rank_candidates(results: &[Value], profile: &KpiProfile) -> Vec<RankedCandidate> {
    let authorization_request = OptimizerAuthorizationRequestV1 {
        schema: "amphora.optimizer-authorization-request.v1".into(),
        request_source: "POLICY".into(),
        objectives: profile
            .objectives
            .iter()
            .map(|objective| OptimizerObjectiveRequestV1 {
                objective_id: objective.id.clone(),
                module_id: objective.module_id.clone(),
                section: objective.section.clone(),
                path: objective.path.clone(),
            })
            .collect(),
        hard_constraints: profile
            .hard_constraints
            .iter()
            .map(|constraint| OptimizerConstraintRequestV1 {
                constraint_id: constraint.id.clone(),
                module_id: constraint.module_id.clone(),
                section: constraint.section.clone(),
                path: constraint.path.clone(),
                operator: constraint.operator.clone(),
                expected: constraint.expected.clone(),
            })
            .collect(),
    };
    let optimizer_policy = quarantined_optimizer_policy();
    let mut candidates: Vec<_> = results
        .iter()
        .map(|result| {
            let candidate_id = result
                .pointer("/candidate/candidate_id")
                .or_else(|| result.pointer("/candidate/normalized_molecule/candidate_id"))
                .or_else(|| result.pointer("/candidate/normalized_formulation/candidate_id"))
                .and_then(Value::as_str)
                .unwrap_or("unknown")
                .to_owned();
            let failed_modules = result
                .pointer("/score_envelopes")
                .and_then(Value::as_array)
                .map_or(0, |rows| {
                    rows.iter()
                        .filter(|row| row.get("status").and_then(Value::as_str) != Some("SCORED"))
                        .count()
                });
            let authorization = optimizer_envelopes(result).and_then(|envelopes| {
                authorize_optimizer_request(&authorization_request, &envelopes, &optimizer_policy)
            });
            let feasible = authorization
                .as_ref()
                .is_ok_and(|authorization| authorization.hard_constraints_passed);
            let objective_rows = Vec::new();
            let eligible_objectives = 0;
            let ranked = false;
            let display_kpis = profile
                .display_kpis
                .iter()
                .filter_map(|definition| {
                    let envelope = module_envelope(result, &definition.module_id)?;
                    let value = envelope_value(envelope, &definition.section, &definition.path)?;
                    Some(DisplayKpiValue {
                        id: definition.id.clone(),
                        label: definition.label.clone(),
                        unit: definition.unit.clone(),
                        value: value.clone(),
                    })
                })
                .collect();
            let lineage = result.pointer("/candidate/lineage");
            let parent_ids = lineage
                .and_then(|value| value.get("parent_ids"))
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(Value::as_str)
                .map(str::to_owned)
                .collect();
            RankedCandidate {
                candidate_id,
                current_rank: None,
                previous_rank: None,
                rank_delta: None,
                movement: default_movement(),
                feasible,
                ranked,
                pareto_rank: None,
                moo_display_score: None,
                eligible_objectives,
                failed_modules,
                objective_rows,
                claim_locks: collect_claim_locks(result),
                display_kpis,
                mutation_id: lineage
                    .and_then(|value| value.get("mutation_id"))
                    .and_then(Value::as_str)
                    .map(str::to_owned),
                parent_ids,
                generation: lineage
                    .and_then(|value| value.get("generation"))
                    .and_then(Value::as_u64)
                    .unwrap_or(0) as u32,
                chemical_preview: None,
            }
        })
        .collect();
    candidates.sort_by(|left, right| {
        right
            .ranked
            .cmp(&left.ranked)
            .then_with(|| right.feasible.cmp(&left.feasible))
            .then_with(|| {
                right
                    .moo_display_score
                    .partial_cmp(&left.moo_display_score)
                    .unwrap_or(Ordering::Equal)
            })
            .then_with(|| left.candidate_id.cmp(&right.candidate_id))
    });
    let mut previous_score = None;
    let mut pareto_rank = 0_usize;
    for (index, candidate) in candidates.iter_mut().enumerate() {
        if candidate.ranked {
            if previous_score.is_some_and(|score: f64| {
                candidate
                    .moo_display_score
                    .is_some_and(|current| (current - score).abs() > 1e-12)
            }) {
                pareto_rank += 1;
            }
            candidate.pareto_rank = Some(pareto_rank);
            candidate.current_rank = Some(index + 1);
            previous_score = candidate.moo_display_score;
            for row in &mut candidate.objective_rows {
                if row.eligible {
                    row.pareto_rank = Some(pareto_rank);
                }
            }
        }
    }
    candidates
}

pub fn apply_rank_deltas(current: &mut [RankedCandidate], previous: Option<&[RankedCandidate]>) {
    let previous: BTreeMap<_, _> = previous
        .into_iter()
        .flatten()
        .filter_map(|candidate| Some((candidate.candidate_id.as_str(), candidate.current_rank?)))
        .collect();
    for candidate in current {
        candidate.previous_rank = previous.get(candidate.candidate_id.as_str()).copied();
        candidate.rank_delta = candidate
            .previous_rank
            .zip(candidate.current_rank)
            .map(|(prior, current)| prior as i64 - current as i64);
        candidate.movement = match candidate.rank_delta {
            Some(delta) if delta > 0 => "↑",
            Some(delta) if delta < 0 => "↓",
            _ => "—",
        }
        .into();
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct HistoryCandidate {
    pub candidate_id: String,
    pub score: Option<f64>,
    pub pareto_rank: Option<usize>,
    pub current_rank: Option<usize>,
    pub previous_rank: Option<usize>,
    pub rank_delta: Option<i64>,
    pub movement: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ScoreHistory {
    pub generation: u32,
    pub best_feasible_score: Option<f64>,
    pub mean_feasible_score: Option<f64>,
    pub feasible_count: usize,
    pub ranked_count: usize,
    pub top10: Vec<HistoryCandidate>,
}

pub fn make_score_history(
    generation: u32,
    candidates: &[RankedCandidate],
    limit: usize,
) -> ScoreHistory {
    let feasible_scores: Vec<_> = candidates
        .iter()
        .filter(|candidate| candidate.feasible)
        .filter_map(|candidate| candidate.moo_display_score)
        .collect();
    let best_feasible_score = feasible_scores
        .iter()
        .copied()
        .max_by(|left, right| left.partial_cmp(right).unwrap_or(Ordering::Equal));
    let mean_feasible_score = (!feasible_scores.is_empty())
        .then(|| feasible_scores.iter().sum::<f64>() / feasible_scores.len() as f64);
    ScoreHistory {
        generation,
        best_feasible_score,
        mean_feasible_score,
        feasible_count: candidates
            .iter()
            .filter(|candidate| candidate.feasible)
            .count(),
        ranked_count: candidates
            .iter()
            .filter(|candidate| candidate.ranked)
            .count(),
        top10: candidates
            .iter()
            .filter(|candidate| candidate.ranked)
            .take(limit)
            .map(|candidate| HistoryCandidate {
                candidate_id: candidate.candidate_id.clone(),
                score: candidate.moo_display_score,
                pareto_rank: candidate.pareto_rank,
                current_rank: candidate.current_rank,
                previous_rank: candidate.previous_rank,
                rank_delta: candidate.rank_delta,
                movement: candidate.movement.clone(),
            })
            .collect(),
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub schema: String,
    pub sequence: u64,
    pub run_id: String,
    pub event_type: String,
    pub candidate_id: Option<String>,
    pub generation: u32,
    pub payload: Value,
    pub event_hash: String,
}

#[derive(Debug, Error)]
pub enum RunArchiveError {
    #[error("run archive already exists: {0}")]
    Exists(String),
    #[error("run archive integrity error: {0}")]
    Integrity(String),
    #[error(transparent)]
    Io(#[from] std::io::Error),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
    #[error(transparent)]
    Contract(#[from] ContractError),
}

pub struct RunArchive {
    path: PathBuf,
    run_id: String,
    sequence: u64,
    event_hashes: Vec<String>,
}

impl RunArchive {
    pub fn create(
        base: impl AsRef<Path>,
        run_id: &str,
        manifest: &Value,
    ) -> Result<Self, RunArchiveError> {
        let path = base.as_ref().join(run_id);
        if path.exists() {
            return Err(RunArchiveError::Exists(path.display().to_string()));
        }
        fs::create_dir_all(&path)?;
        write_new_json(&path.join("manifest.json"), manifest)?;
        OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(path.join("events.jsonl"))?;
        Ok(Self {
            path,
            run_id: run_id.into(),
            sequence: 0,
            event_hashes: Vec::new(),
        })
    }

    pub fn sequence(&self) -> u64 {
        self.sequence
    }

    pub fn append(
        &mut self,
        event_type: &str,
        candidate_id: Option<String>,
        generation: u32,
        payload: Value,
    ) -> Result<Event, RunArchiveError> {
        self.sequence += 1;
        let seed = serde_json::json!({
            "schema": "amphora.tui-event.v1",
            "sequence": self.sequence,
            "run_id": self.run_id,
            "event_type": event_type,
            "candidate_id": candidate_id,
            "generation": generation,
            "payload": payload,
            "previous_event_hash": self.event_hashes.last(),
        });
        let event = Event {
            schema: "amphora.tui-event.v1".into(),
            sequence: self.sequence,
            run_id: self.run_id.clone(),
            event_type: event_type.into(),
            candidate_id,
            generation,
            payload,
            event_hash: stable_hash(&seed),
        };
        let mut file = OpenOptions::new()
            .append(true)
            .open(self.path.join("events.jsonl"))?;
        serde_json::to_writer(&mut file, &event)?;
        file.write_all(b"\n")?;
        file.sync_data()?;
        self.event_hashes.push(event.event_hash.clone());
        Ok(event)
    }

    pub fn snapshot<T: Serialize>(&self, sequence: u64, state: &T) -> Result<(), RunArchiveError> {
        write_new_json(
            &self.path.join(format!("snapshot-{sequence:06}.json")),
            state,
        )
    }

    pub fn final_state<T: Serialize>(&self, state: &T) -> Result<(), RunArchiveError> {
        write_new_json(&self.path.join("final-state.json"), state)?;
        let manifest = fs::read(self.path.join("manifest.json"))?;
        let events = fs::read(self.path.join("events.jsonl"))?;
        let state_value = serde_json::to_value(state)?;
        let event_chain_root = self
            .event_hashes
            .last()
            .cloned()
            .unwrap_or_else(|| raw_sha256(&[]));
        let provenance_seed = serde_json::json!({
            "run_id": self.run_id,
            "manifest_sha256": raw_sha256(&manifest),
            "events_sha256": raw_sha256(&events),
            "event_chain_root": event_chain_root,
            "final_state_hash": stable_hash(&state_value),
        });
        let provenance = serde_json::json!({
            "schema": "amphora.run-provenance.v1",
            "run_id": self.run_id,
            "manifest_sha256": raw_sha256(&manifest),
            "events_sha256": raw_sha256(&events),
            "event_chain_root": event_chain_root,
            "final_state_hash": stable_hash(&state_value),
            "root_hash": stable_hash(&provenance_seed),
            "promotion_receipt_eligible": false,
            "signature_status": "UNSIGNED_CONTROLLED_KEY_REQUIRED",
        });
        write_new_json(&self.path.join("provenance.json"), &provenance)
    }
}

fn write_new_json<T: Serialize>(path: &Path, value: &T) -> Result<(), RunArchiveError> {
    let mut bytes = serde_json::to_vec_pretty(value)?;
    bytes.push(b'\n');
    let mut file = OpenOptions::new().create_new(true).write(true).open(path)?;
    file.write_all(&bytes)?;
    file.sync_all()?;
    Ok(())
}

pub fn read_events(path: impl AsRef<Path>) -> Result<Vec<Event>, RunArchiveError> {
    let file = File::open(path)?;
    let mut events = Vec::new();
    for line in BufReader::new(file).lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        let value = parse_json_strict(line.as_bytes())?;
        events.push(serde_json::from_value(value)?);
    }
    Ok(events)
}

pub fn verify_run(path: impl AsRef<Path>) -> Result<String, RunArchiveError> {
    let path = path.as_ref();
    let provenance: Value = serde_json::from_slice(&fs::read(path.join("provenance.json"))?)?;
    let manifest = fs::read(path.join("manifest.json"))?;
    let events_bytes = fs::read(path.join("events.jsonl"))?;
    let final_state: Value = serde_json::from_slice(&fs::read(path.join("final-state.json"))?)?;
    let events = read_events(path.join("events.jsonl"))?;
    if events
        .iter()
        .enumerate()
        .any(|(index, event)| event.sequence != index as u64 + 1)
    {
        return Err(RunArchiveError::Integrity(
            "non-contiguous event sequence".into(),
        ));
    }
    let event_chain_root = events
        .last()
        .map(|event| event.event_hash.clone())
        .unwrap_or_else(|| raw_sha256(&[]));
    let expected = serde_json::json!({
        "run_id": provenance.get("run_id"),
        "manifest_sha256": raw_sha256(&manifest),
        "events_sha256": raw_sha256(&events_bytes),
        "event_chain_root": event_chain_root,
        "final_state_hash": stable_hash(&final_state),
    });
    let observed_root = provenance
        .get("root_hash")
        .and_then(Value::as_str)
        .ok_or_else(|| RunArchiveError::Integrity("missing root hash".into()))?;
    if provenance.get("manifest_sha256").and_then(Value::as_str) != Some(&raw_sha256(&manifest))
        || provenance.get("events_sha256").and_then(Value::as_str)
            != Some(&raw_sha256(&events_bytes))
        || provenance.get("event_chain_root").and_then(Value::as_str)
            != Some(event_chain_root.as_str())
        || provenance.get("final_state_hash").and_then(Value::as_str)
            != Some(stable_hash(&final_state).as_str())
        || observed_root != stable_hash(&expected)
    {
        return Err(RunArchiveError::Integrity(
            "provenance hash mismatch".into(),
        ));
    }
    Ok(observed_root.into())
}

pub fn read_json<T: DeserializeOwned>(path: impl AsRef<Path>) -> Result<T, RunArchiveError> {
    let value = parse_json_strict(&fs::read(path)?)?;
    Ok(serde_json::from_value(value)?)
}

#[cfg(test)]
mod restored_tests {
    use super::*;

    #[test]
    fn canonical_hash_ignores_object_insertion_order() {
        assert_eq!(
            stable_hash(&serde_json::json!({"b": 2, "a": 1})),
            stable_hash(&serde_json::json!({"a": 1, "b": 2}))
        );
    }

    #[test]
    fn rank_movements_and_history_remain_deterministic() {
        let mut current = vec![RankedCandidate {
            candidate_id: "a".into(),
            current_rank: Some(1),
            previous_rank: None,
            rank_delta: None,
            movement: default_movement(),
            feasible: true,
            ranked: true,
            pareto_rank: Some(0),
            moo_display_score: Some(0.8),
            eligible_objectives: 1,
            failed_modules: 0,
            objective_rows: Vec::new(),
            claim_locks: BTreeMap::new(),
            display_kpis: Vec::new(),
            mutation_id: None,
            parent_ids: Vec::new(),
            generation: 0,
            chemical_preview: None,
        }];
        apply_rank_deltas(&mut current, None);
        assert_eq!(
            make_score_history(0, &current, 10).best_feasible_score,
            Some(0.8)
        );
    }
}
