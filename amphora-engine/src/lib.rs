#![forbid(unsafe_code)]

use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{
    stable_hash, AuditInputBindingKindV1, AuthorizedAuditModuleInputV1,
    AuthorizedMoleculeModelInputV1, CampaignGenerationRequestV1, CandidateEnvelope, Capability,
    CapabilityError, EngineEvidenceContextV1, EngineEvidenceContextV3, ExecutionContext,
    FeatureSnapshot, ModuleDescriptor, ModuleResult, TrustStore, ValidatedEngineEvidenceContextV1,
    ValidatedEngineEvidenceContextV3,
};
use amphora_formulation_capabilities::FormulationCapability;
use amphora_molecule_capabilities::{
    generate_authorized, GeneratedMoleculeProposalV1, MoleculeCapability, GENERATOR_ID,
};
use amphora_rdkit_ffi::{backend_status, molecule_facts};
use anyhow::{anyhow, Context, Result};
use rayon::{ThreadPool, ThreadPoolBuilder};
use serde::Deserialize;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::Path;
use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::sync::{Arc, Mutex, OnceLock};
use std::time::Instant;
use thiserror::Error;

const MANIFEST_BYTES: &[u8] = include_bytes!("../../module-manifest.json");
const MODULE_VERSION: &str = "0.1.0-rust";
const EVIDENCE_CONTEXT_FILE: &str = "engine-evidence-context.v1.json";
const TRUST_STORE_FILE: &str = "trust-store.v1.json";
const TRUST_STORE_SCHEMA: &str = "amphora.trust-store.v1";

const CANONICAL_MODULES: [&str; 29] = [
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

const MOLECULE_SCORE_MODULES: [&str; 4] = [
    "amphora-molecule-property",
    "amphora-molecule-role-ranker",
    "amphora-molecule-novelty",
    "amphora-molecule-design-gate",
];

const FORMULATION_SCORE_MODULES: [&str; 9] = [
    "amphora-formulation-arithmetic",
    "amphora-solvency-score",
    "amphora-viscosity-score",
    "amphora-cure-potlife-gate",
    "amphora-public-corrosion-benchmark",
    "amphora-tolerance-robustness",
    "amphora-process-qc-twin",
    "amphora-sourceability-ehs",
    "amphora-design-rule-score",
];

const EVIDENCE_SCORE_MODULES: [&str; 6] = [
    "amphora-evidence-intake-validator",
    "amphora-source-ledger",
    "amphora-optimizer-orchestrator",
    "amphora-redteam-audit",
    "amphora-report-packager",
    "amphora-run-provenance",
];

#[derive(Debug, Clone, Deserialize)]
struct Manifest {
    schema: String,
    policy: ManifestPolicy,
    modules: Vec<ManifestRow>,
}

#[derive(Debug, Clone, Deserialize)]
struct ManifestPolicy {
    normalization_owner: String,
    authority_resolution: String,
    rust_final_ranking_enforcement: bool,
    unknown_module_policy: String,
    unknown_true_claim_lock_policy: String,
    product_claim_ready: bool,
    #[serde(default)]
    mandatory_claim_locks: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
struct ManifestRow {
    project: String,
    authority_ceiling: String,
    solver_use_ceiling: String,
    model_readiness_ceiling: String,
    ranking_eligible: bool,
    candidate_types: Vec<String>,
    #[serde(default)]
    non_blocking_claim_locks: Vec<String>,
    readiness: String,
}

impl ManifestRow {
    fn descriptor(&self) -> ModuleDescriptor {
        ModuleDescriptor {
            project: self.project.clone(),
            authority_ceiling: self.authority_ceiling.clone(),
            solver_use_ceiling: self.solver_use_ceiling.clone(),
            model_readiness_ceiling: self.model_readiness_ceiling.clone(),
            ranking_eligible: self.ranking_eligible,
            candidate_types: self.candidate_types.clone(),
            non_blocking_claim_locks: self.non_blocking_claim_locks.clone(),
            readiness: self.readiness.clone(),
        }
    }
}

#[derive(Debug, Error)]
pub enum RegistryError {
    #[error("native registry manifest is invalid: {0}")]
    Manifest(String),
    #[error("native capability construction failed: {0}")]
    Capability(String),
    #[error("unknown native capability {0}")]
    UnknownModule(String),
}

struct Entry {
    capability: Box<dyn Capability>,
}

pub struct NativeRegistry {
    manifest_value: Value,
    manifest: Manifest,
    entries: BTreeMap<String, Entry>,
}

impl NativeRegistry {
    pub fn global() -> Result<&'static Self, RegistryError> {
        static REGISTRY: OnceLock<Result<NativeRegistry, RegistryError>> = OnceLock::new();
        match REGISTRY.get_or_init(Self::build) {
            Ok(registry) => Ok(registry),
            Err(error) => Err(RegistryError::Manifest(error.to_string())),
        }
    }

    fn build() -> Result<Self, RegistryError> {
        let manifest_value = amphora_core::parse_json_strict(MANIFEST_BYTES)
            .map_err(|error| RegistryError::Manifest(error.to_string()))?;
        let manifest: Manifest = serde_json::from_value(manifest_value.clone())
            .map_err(|error| RegistryError::Manifest(error.to_string()))?;
        validate_manifest(&manifest)?;
        let mut entries = BTreeMap::new();
        for row in &manifest.modules {
            let descriptor: &'static ModuleDescriptor = Box::leak(Box::new(row.descriptor()));
            let capability = capability_for(descriptor)?;
            if entries
                .insert(row.project.clone(), Entry { capability })
                .is_some()
            {
                return Err(RegistryError::Manifest(format!(
                    "duplicate module {}",
                    row.project
                )));
            }
        }
        Ok(Self {
            manifest_value,
            manifest,
            entries,
        })
    }

    pub fn module_count(&self) -> usize {
        self.entries.len()
    }

    pub fn resolve(&self, module_id: &str) -> Result<&dyn Capability, RegistryError> {
        self.entries
            .get(module_id)
            .map(|entry| entry.capability.as_ref())
            .ok_or_else(|| RegistryError::UnknownModule(module_id.to_owned()))
    }

    pub fn report(&self, lane: &str) -> Result<Value, RegistryError> {
        let active = active_modules(lane)?;
        let mut report = self.manifest_value.clone();
        report["schema"] = Value::String("amphora.module-manifest.v1".into());
        report["module_count"] = json!(self.module_count());
        report["registered_modules"] = json!(self.module_count());
        report["active_lane"] = Value::String(lane.into());
        report["active_submodels"] = serde_json::to_value(active).expect("module ids serialize");
        report["active_module_count"] = json!(active.len());
        report["implementation"] = Value::String("native-rust".into());
        Ok(report)
    }

    fn score_modules(&self, candidate_type: &str) -> Result<Vec<&dyn Capability>, RegistryError> {
        active_modules(candidate_type)?
            .iter()
            .map(|module_id| self.resolve(module_id))
            .collect()
    }

    fn mandatory_locks(&self) -> &[String] {
        &self.manifest.policy.mandatory_claim_locks
    }

    fn envelope(
        &self,
        capability: &dyn Capability,
        candidate: &CandidateEnvelope,
        result: ModuleResult,
    ) -> Value {
        let descriptor = capability.descriptor();
        let mut locks = Map::new();
        for lock in descriptor
            .non_blocking_claim_locks
            .iter()
            .chain(self.mandatory_locks())
        {
            locks.insert(lock.clone(), Value::Bool(true));
        }
        let status = if matches!(
            result.status.as_str(),
            "SCORED" | "FAILED_GATES" | "INSUFFICIENT_INPUT" | "NO_AUTHORITY" | "ERROR"
        ) {
            result.status
        } else {
            "ERROR".into()
        };
        let score = result
            .score_0_1
            .filter(|value| value.is_finite() && (0.0..=1.0).contains(value));
        let semantics = match status.as_str() {
            "FAILED_GATES" => "AUDIT_CONSTRAINT",
            "INSUFFICIENT_INPUT" => "INSUFFICIENT_INPUT",
            "NO_AUTHORITY" => "NO_AUTHORITY",
            "ERROR" => "ERROR",
            _ if descriptor.authority_ceiling == "ROADMAP" => "ROADMAP",
            _ if descriptor.solver_use_ceiling == "DISABLED" => "EVIDENCE_ONLY",
            _ => "AUDIT_CONSTRAINT",
        };
        let mut metrics = result.metrics;
        metrics.insert(
            "model_card".into(),
            json!({
                "model_id": format!("{}.native-quarantine.v1", descriptor.project),
                "model_authority": descriptor.authority_ceiling,
                "solver_use": descriptor.solver_use_ceiling,
                "model_readiness_status": descriptor.model_readiness_ceiling,
                "can_optimize": false,
                "current_pass": status == "SCORED",
                "product_claim_ready": false,
                "scientific_applicability": "UNVALIDATED",
            }),
        );
        metrics.insert("solver_use".into(), json!(descriptor.solver_use_ceiling));
        metrics.insert(
            "model_readiness_status".into(),
            json!(descriptor.model_readiness_ceiling),
        );
        metrics.insert(
            "authority_receipt".into(),
            json!({
                "granted_level": descriptor.model_readiness_ceiling,
                "ranking_eligible": false,
                "registry_owned": true,
            }),
        );
        json!({
            "module_id": descriptor.project,
            "module_version": MODULE_VERSION,
            "candidate_id": candidate.candidate_id(),
            "status": status,
            "authority_tier": descriptor.authority_ceiling,
            "score_0_1": score,
            "objective_values": result.objective_values,
            "metrics": metrics,
            "gates": result.gates,
            "uncertainty": result.uncertainty,
            "claim_locks": locks,
            "missing_inputs": result.missing_inputs,
            "explanations": result.explanations,
            "source_refs": result.source_refs,
            "usable_by_optimizer": false,
            "evidence_scope": result.evidence_scope,
            "score_semantics": semantics,
            "schema_version": "amphora.score-envelope.v1",
        })
    }
}

fn validate_manifest(manifest: &Manifest) -> Result<(), RegistryError> {
    let policy = &manifest.policy;
    if manifest.schema != "amphora.module-manifest.v2"
        || policy.normalization_owner != "amphora-candidate-contract"
        || policy.authority_resolution != "minimum_privilege"
        || !policy.rust_final_ranking_enforcement
        || policy.unknown_module_policy != "REJECT"
        || policy.unknown_true_claim_lock_policy != "BLOCK"
        || policy.product_claim_ready
    {
        return Err(RegistryError::Manifest(
            "trust policy is not fail-closed".into(),
        ));
    }
    if policy.mandatory_claim_locks.is_empty() {
        return Err(RegistryError::Manifest(
            "mandatory pre-Phase-0 locks are absent".into(),
        ));
    }
    let expected: BTreeSet<_> = CANONICAL_MODULES.into_iter().collect();
    let actual: BTreeSet<_> = manifest
        .modules
        .iter()
        .map(|row| row.project.as_str())
        .collect();
    if manifest.modules.len() != 29 || actual != expected {
        return Err(RegistryError::Manifest(
            "registry must contain exactly the 29 canonical module identities".into(),
        ));
    }
    if manifest.modules.iter().any(|row| row.ranking_eligible) {
        return Err(RegistryError::Manifest(
            "pre-Phase-0 registry cannot contain ranking-eligible modules".into(),
        ));
    }
    Ok(())
}

fn active_modules(lane: &str) -> Result<&'static [&'static str], RegistryError> {
    match lane {
        "molecule" => Ok(&MOLECULE_SCORE_MODULES),
        "formulation" => Ok(&FORMULATION_SCORE_MODULES),
        "evidence_package" | "evidence" | "infrastructure" => Ok(&EVIDENCE_SCORE_MODULES),
        _ => Err(RegistryError::Manifest(format!("unknown lane {lane}"))),
    }
}

fn capability_for(
    descriptor: &'static ModuleDescriptor,
) -> Result<Box<dyn Capability>, RegistryError> {
    if [
        "amphora-molecule-generator",
        "amphora-molecule-role-ranker",
        "amphora-molecule-novelty",
        "amphora-molecule-property",
        "amphora-molecule-design-gate",
    ]
    .contains(&descriptor.project.as_str())
    {
        return Ok(Box::new(MoleculeCapability::new(descriptor)));
    }
    if FormulationCapability::supports(&descriptor.project) {
        return FormulationCapability::new(descriptor)
            .map(|capability| Box::new(capability) as Box<dyn Capability>)
            .map_err(|error| RegistryError::Capability(error.to_string()));
    }
    if amphora_assurance_capabilities::SUPPORTED_MODULE_IDS.contains(&descriptor.project.as_str()) {
        return AssuranceCapability::from_descriptor(descriptor)
            .map(|capability| Box::new(capability) as Box<dyn Capability>)
            .map_err(|error| RegistryError::Capability(error.to_string()));
    }
    TrustCapability::new(descriptor)
        .map(|capability| Box::new(capability) as Box<dyn Capability>)
        .map_err(|error| RegistryError::Capability(error.to_string()))
}

struct TrustCapability {
    descriptor: &'static ModuleDescriptor,
}

impl TrustCapability {
    const IDS: [&'static str; 4] = [
        "amphora-candidate-contract",
        "amphora-model-card-authority",
        "amphora-optimizer-orchestrator",
        "amphora-run-provenance",
    ];

    fn new(descriptor: &'static ModuleDescriptor) -> Result<Self, CapabilityError> {
        if Self::IDS.contains(&descriptor.project.as_str()) {
            Ok(Self { descriptor })
        } else {
            Err(CapabilityError::InvalidInput(format!(
                "unsupported trust capability {}",
                descriptor.project
            )))
        }
    }
}

impl Capability for TrustCapability {
    fn descriptor(&self) -> &'static ModuleDescriptor {
        self.descriptor
    }

    fn evaluate(
        &self,
        candidate: &CandidateEnvelope,
        _features: &FeatureSnapshot,
        _context: &ExecutionContext,
    ) -> Result<ModuleResult, CapabilityError> {
        if !self
            .descriptor
            .candidate_types
            .iter()
            .any(|kind| kind == candidate.candidate_type())
        {
            return Err(CapabilityError::CandidateType);
        }
        let result = match self.descriptor.project.as_str() {
            "amphora-candidate-contract" => ModuleResult {
                status: "SCORED".into(),
                score_0_1: Some(1.0),
                objective_values: BTreeMap::new(),
                metrics: BTreeMap::from([
                    (
                        "contract_hash_v1".into(),
                        json!(candidate.contract_hash_v1()),
                    ),
                    (
                        "original_bytes_sha256".into(),
                        json!(candidate.original_bytes_sha256()),
                    ),
                ]),
                gates: BTreeMap::from([("candidate_schema_valid".into(), Value::Bool(true))]),
                uncertainty: BTreeMap::new(),
                missing_inputs: Vec::new(),
                explanations: vec!["Strict v1 candidate parsing passed.".into()],
                source_refs: Vec::new(),
                evidence_scope: "CONTRACT_VALIDATION_ONLY".into(),
            },
            "amphora-run-provenance" => ModuleResult {
                status: "SCORED".into(),
                score_0_1: None,
                objective_values: BTreeMap::new(),
                metrics: BTreeMap::from([(
                    "candidate_contract_hash".into(),
                    json!(candidate.contract_hash_v1()),
                )]),
                gates: BTreeMap::new(),
                uncertainty: BTreeMap::new(),
                missing_inputs: Vec::new(),
                explanations: vec!["Candidate input is bound into native provenance.".into()],
                source_refs: Vec::new(),
                evidence_scope: "ATTESTATION_ONLY".into(),
            },
            "amphora-optimizer-orchestrator" => {
                let mut result = ModuleResult::quarantined(
                    "No scientific objective has passed its locked external gate.",
                );
                result.status = "FAILED_GATES".into();
                result.gates.insert(
                    "complete_authorized_objective_vector".into(),
                    Value::Bool(false),
                );
                result
            }
            _ => ModuleResult::quarantined(
                "Model cards do not authorize any scientific ranking objective.",
            ),
        };
        Ok(result)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ScoreProgress {
    pub completed: usize,
    pub total: usize,
    pub succeeded: bool,
}

pub struct EnginePool {
    registry: &'static NativeRegistry,
    pool: ThreadPool,
    next_request: AtomicU64,
    evidence: EngineEvidenceState,
}

struct EngineEvidenceState {
    context: Option<ValidatedEngineEvidenceContextV1>,
    phase0_context: Option<ValidatedEngineEvidenceContextV3>,
    context_sha256: String,
    source_hashes: BTreeMap<String, String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct TrustStoreFileV1 {
    schema: String,
    keys: Vec<TrustStoreKeyV1>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct TrustStoreKeyV1 {
    key_id: String,
    algorithm: String,
    public_key_hex: String,
    status: String,
}

type ScoreSlot = Option<Result<(Value, u64)>>;
type SharedScoreOutput = Arc<Mutex<Vec<ScoreSlot>>>;

impl EnginePool {
    pub fn new(root: impl AsRef<Path>, workers: usize) -> Result<Self> {
        let evidence_root = root.as_ref().join(".amphora/evidence");
        Self::with_evidence_root(root, evidence_root, workers)
    }

    pub fn with_evidence_root(
        _root: impl AsRef<Path>,
        evidence_root: impl AsRef<Path>,
        workers: usize,
    ) -> Result<Self> {
        let registry = NativeRegistry::global().map_err(|error| anyhow!(error))?;
        let evidence = load_engine_evidence(evidence_root.as_ref())?;
        let pool = ThreadPoolBuilder::new()
            .num_threads(workers.max(1))
            .thread_name(|index| format!("amphora-native-{index}"))
            .build()?;
        Ok(Self {
            registry,
            pool,
            next_request: AtomicU64::new(0),
            evidence,
        })
    }

    pub fn evidence_context_sha256(&self) -> &str {
        &self.evidence.context_sha256
    }

    pub fn registry(&self, lane: &str) -> Result<Value> {
        self.registry.report(lane).map_err(Into::into)
    }

    pub fn mutate(&self, candidate: &Value, seed: u64, lineage: Value) -> Result<Value> {
        CandidateEnvelope::from_value(candidate.clone())?;
        let mut output = candidate.clone();
        let mutation_id = &stable_hash(&json!({
            "candidate": candidate,
            "seed": seed,
            "lineage": lineage,
            "generator": "native-quarantined-no-structure-change-v1",
        }))[..12];
        let base = candidate
            .get("candidate_id")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("candidate_id missing"))?;
        output["candidate_id"] = Value::String(format!("{base}-m{mutation_id}"));
        output["lineage"] = json!({
            "parent_ids": lineage.get("parent_ids").cloned().unwrap_or_else(|| json!([base])),
            "generation": lineage.get("generation").and_then(Value::as_u64).unwrap_or(0),
            "mutation_id": mutation_id,
            "generation_status": "QUARANTINED_NO_STRUCTURE_CHANGE",
        });
        Ok(output)
    }

    pub fn generate_compounds(
        &self,
        request: &CampaignGenerationRequestV1,
        deterministic_seed: u64,
    ) -> Result<Vec<GeneratedMoleculeProposalV1>> {
        let parent_facts = request
            .parent_structures
            .iter()
            .map(|structure| molecule_facts(structure).map_err(anyhow::Error::from))
            .collect::<Result<Vec<_>>>()?;
        let request_value = json!({
            "request_id": request.request_id,
            "parent_structures": request.parent_structures,
            "requested_role": request.requested_role,
            "reaction_family": request.reaction_family,
            "deterministic_seed": deterministic_seed,
        });
        let parent_facts_value = serde_json::to_value(parent_facts)?;
        let authorization = self
            .evidence
            .authorize_runtime_grant(
                GENERATOR_ID,
                &request.request_id,
                &stable_hash(&request_value),
                AuditInputBindingKindV1::MoleculeFacts,
                &stable_hash(&parent_facts_value),
            )
            .ok_or_else(|| anyhow!("verified sparse Phase-0 generator runtime grant is absent"))?;
        generate_authorized(
            &request.request_id,
            &request.parent_structures,
            &request.requested_role,
            &request.reaction_family,
            deterministic_seed,
            &authorization,
        )
        .map_err(Into::into)
    }

    pub fn repair(&self, candidate: &Value, _lane: &str) -> Result<Value> {
        CandidateEnvelope::from_value(candidate.clone())?;
        Ok(candidate.clone())
    }

    pub fn score(
        &self,
        candidate: &Value,
        seed: u64,
        lineage: Value,
        run_id: &str,
    ) -> Result<(Value, u64)> {
        let started = Instant::now();
        let result = execute(
            self.registry,
            &self.evidence,
            candidate,
            seed,
            lineage,
            run_id,
            None,
        )?;
        Ok((result, started.elapsed().as_millis() as u64))
    }

    /// Evaluate an explicit non-ranking campaign traversal. The registry still
    /// enforces candidate-type compatibility and every envelope remains
    /// unusable by the optimizer.
    pub fn score_campaign_modules(
        &self,
        candidate: &Value,
        seed: u64,
        run_id: &str,
        module_ids: &[&str],
    ) -> Result<Value> {
        execute(
            self.registry,
            &self.evidence,
            candidate,
            seed,
            json!({"campaign_traversal": true}),
            run_id,
            Some(module_ids),
        )
    }

    pub fn score_many(
        &self,
        requests: Vec<(Value, u64, Value, String)>,
    ) -> Vec<Result<(Value, u64)>> {
        self.score_many_with_progress(requests, |_| {})
    }

    pub fn score_many_with_progress<F>(
        &self,
        requests: Vec<(Value, u64, Value, String)>,
        on_progress: F,
    ) -> Vec<Result<(Value, u64)>>
    where
        F: Fn(ScoreProgress) + Sync,
    {
        let total = requests.len();
        let completed = AtomicUsize::new(0);
        let output: SharedScoreOutput = Arc::new(Mutex::new((0..total).map(|_| None).collect()));
        self.pool.scope(|scope| {
            for (index, (candidate, seed, lineage, run_id)) in requests.into_iter().enumerate() {
                let output = Arc::clone(&output);
                let on_progress = &on_progress;
                let completed = &completed;
                scope.spawn(move |_| {
                    let result = self.score(&candidate, seed, lineage, &run_id);
                    let succeeded = result.is_ok();
                    output.lock().expect("score output lock poisoned")[index] = Some(result);
                    on_progress(ScoreProgress {
                        completed: completed.fetch_add(1, Ordering::Relaxed) + 1,
                        total,
                        succeeded,
                    });
                });
            }
        });
        Arc::try_unwrap(output)
            .expect("native scoring tasks still retain output")
            .into_inner()
            .expect("score output lock poisoned")
            .into_iter()
            .map(|row| row.expect("native scoring task did not return"))
            .collect()
    }

    pub fn next_request_id(&self) -> u64 {
        self.next_request.fetch_add(1, Ordering::Relaxed) + 1
    }
}

fn execute(
    registry: &NativeRegistry,
    evidence: &EngineEvidenceState,
    candidate_value: &Value,
    seed: u64,
    lineage: Value,
    run_id: &str,
    requested_modules: Option<&[&str]>,
) -> Result<Value> {
    let candidate = CandidateEnvelope::from_value(candidate_value.clone())?;
    let normalized = normalized_candidate(&candidate)?;
    let mut feature_values = BTreeMap::from([
        (
            "chemistry_backend".into(),
            serde_json::to_value(backend_status()).expect("backend status serializes"),
        ),
        (
            "rights_cleared_scientific_corpus".into(),
            Value::Bool(false),
        ),
    ]);
    if let Some(facts) = normalized.pointer("/normalization/molecule_facts_v1") {
        feature_values.insert("molecule_facts_v1".into(), facts.clone());
    }
    if let Some(error) = normalized
        .pointer("/normalization/error")
        .and_then(Value::as_str)
    {
        feature_values.insert(
            "molecule_normalization_error".into(),
            Value::String(error.into()),
        );
    }
    let features = FeatureSnapshot {
        values: feature_values,
    };
    let context = ExecutionContext {
        run_id: run_id.into(),
        deterministic_seed: seed,
        lineage: lineage.clone(),
    };
    let mut envelopes = Vec::new();
    let capabilities = if let Some(module_ids) = requested_modules {
        module_ids
            .iter()
            .map(|module_id| registry.resolve(module_id))
            .collect::<Result<Vec<_>, _>>()?
    } else {
        registry.score_modules(candidate.candidate_type())?
    };
    for capability in capabilities {
        let authorization = normalized
            .pointer("/normalization/molecule_facts_v1")
            .and_then(|facts| {
                evidence.authorize_molecule_model(
                    capability.descriptor().project.as_str(),
                    candidate.candidate_id(),
                    candidate.contract_hash_v1(),
                    &stable_hash(facts),
                )
            });
        let evaluated = if candidate.candidate_type() == "molecule"
            && matches!(
                capability.descriptor().project.as_str(),
                "amphora-molecule-generator"
                    | "amphora-molecule-property"
                    | "amphora-molecule-role-ranker"
                    | "amphora-molecule-novelty"
                    | "amphora-molecule-design-gate"
            ) {
            MoleculeCapability::new(capability.descriptor()).evaluate_authorized(
                &candidate,
                &features,
                &context,
                authorization.as_ref(),
            )
        } else {
            capability.evaluate(&candidate, &features, &context)
        };
        let result = match evaluated {
            Ok(result) => result,
            Err(error) => ModuleResult {
                status: "ERROR".into(),
                score_0_1: None,
                objective_values: BTreeMap::new(),
                metrics: BTreeMap::new(),
                gates: BTreeMap::new(),
                uncertainty: BTreeMap::new(),
                missing_inputs: vec![error.to_string()],
                explanations: vec!["Native capability failed closed.".into()],
                source_refs: Vec::new(),
                evidence_scope: "NO_AUTHORITY".into(),
            },
        };
        envelopes.push(registry.envelope(capability, &candidate, result));
    }
    let classified = classify(&candidate, &envelopes);
    let input_hash = candidate.contract_hash_v1();
    let manifest_hash = raw_sha256(MANIFEST_BYTES);
    let module_versions: Map<String, Value> = envelopes
        .iter()
        .filter_map(|row| {
            Some((
                row.get("module_id")?.as_str()?.to_owned(),
                row.get("module_version")?.clone(),
            ))
        })
        .collect();
    let candidate_payload = if candidate.candidate_type() == "molecule" {
        json!({
            "candidate_id": candidate.candidate_id(),
            "candidate_type": candidate.candidate_type(),
            "normalized_molecule": normalized,
            "normalized_formulation": null,
            "chemical_preview": null,
        })
    } else {
        json!({
            "candidate_id": candidate.candidate_id(),
            "candidate_type": candidate.candidate_type(),
            "normalized_molecule": null,
            "normalized_formulation": normalized,
            "chemical_preview": null,
        })
    };
    let replay_id = stable_hash(&json!({
        "candidate_contract_hash_v1": input_hash,
        "deterministic_seed": seed,
        "registry_manifest_sha256": manifest_hash,
        "evidence_context_sha256": evidence.context_sha256,
        "execution_profile": "audited-deterministic-native-rust",
    }));
    let model_hashes: Map<String, Value> = envelopes
        .iter()
        .filter_map(|envelope| {
            Some((
                envelope.get("module_id")?.as_str()?.to_owned(),
                envelope
                    .pointer("/metrics/evidence_package_sha256")?
                    .clone(),
            ))
        })
        .collect();
    let mut source_hashes = Map::from_iter([(
        "module-manifest.json".into(),
        Value::String(manifest_hash.clone()),
    )]);
    source_hashes.extend(
        evidence
            .source_hashes
            .iter()
            .map(|(name, hash)| (name.clone(), Value::String(hash.clone()))),
    );
    let mut result = json!({
        "schema": "amphora.engine-result.v1",
        "run_id": run_id,
        "candidate": candidate_payload,
        "score_envelopes": envelopes,
        "optimization": {
            "objectives": [],
            "constraints": classified.constraints,
            "evidence_gaps": classified.evidence_gaps,
            "pareto_status": classified.pareto_status,
        },
        "cost": {
            "status": "MISSING",
            "value": null,
            "currency": null,
            "basis": null,
            "source_refs": [],
            "reason": "No candidate- and grade-bound current cost evidence was accepted."
        },
        "evidence_gaps": classified.evidence_gaps,
        "blocked_claims": classified.blocked_claims,
        "lineage": {
            "parent_ids": lineage.get("parent_ids").cloned().unwrap_or_else(|| json!([])),
            "generation": lineage.get("generation").and_then(Value::as_u64).unwrap_or(0),
            "mutation_id": lineage.get("mutation_id").cloned().unwrap_or(Value::Null),
        },
        "provenance": {
            "input_hash": input_hash,
            "original_bytes_sha256": candidate.original_bytes_sha256(),
            "module_versions": module_versions,
            "model_hashes": model_hashes,
            "source_hashes": source_hashes,
            "evidence_context_sha256": evidence.context_sha256,
            "deterministic_replay_id": replay_id,
            "deterministic_seed": seed,
            "execution_profile": "audited-deterministic-native-rust",
            "result_hash": null,
        },
    });
    result["provenance"]["result_hash"] = Value::String(stable_hash(&result));
    Ok(result)
}

fn load_engine_evidence(evidence_root: &Path) -> Result<EngineEvidenceState> {
    let missing_hash = stable_hash(&json!({
        "schema": "amphora.engine-evidence-context-state.v1",
        "status": "MISSING",
    }));
    if !evidence_root.exists() {
        return Ok(EngineEvidenceState {
            context: None,
            phase0_context: None,
            context_sha256: missing_hash,
            source_hashes: BTreeMap::new(),
        });
    }
    let root_metadata = fs::symlink_metadata(evidence_root)?;
    if root_metadata.file_type().is_symlink() || !root_metadata.is_dir() {
        return Err(anyhow!(
            "configured evidence root must be a non-symlink directory"
        ));
    }
    let context_path = evidence_root.join(EVIDENCE_CONTEXT_FILE);
    if !context_path.exists() {
        return Ok(EngineEvidenceState {
            context: None,
            phase0_context: None,
            context_sha256: missing_hash,
            source_hashes: BTreeMap::new(),
        });
    }
    let trust_path = evidence_root.join(TRUST_STORE_FILE);
    let context_bytes = read_host_owned_file(&context_path)?;
    let trust_bytes = read_host_owned_file(&trust_path)?;
    let context_value = amphora_core::parse_json_strict(&context_bytes)?;
    let trust_value = amphora_core::parse_json_strict(&trust_bytes)?;
    let trust_file: TrustStoreFileV1 = serde_json::from_value(trust_value)?;
    let trust_store = build_trust_store(trust_file)?;
    let schema = context_value
        .get("schema")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("engine evidence context schema is absent"))?;
    let (context, phase0_context, context_sha256) = match schema {
        amphora_core::ENGINE_EVIDENCE_CONTEXT_SCHEMA => {
            let context: EngineEvidenceContextV1 = serde_json::from_value(context_value)?;
            let validated = context.verify(
                &trust_store,
                &raw_sha256(MANIFEST_BYTES),
                amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION,
            )?;
            let hash = validated.context_sha256().to_owned();
            (Some(validated), None, hash)
        }
        amphora_core::ENGINE_EVIDENCE_CONTEXT_V3_SCHEMA => {
            let context: EngineEvidenceContextV3 = serde_json::from_value(context_value)?;
            let validated = context.verify(
                &trust_store,
                &raw_sha256(MANIFEST_BYTES),
                amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION,
            )?;
            let hash = validated.context_sha256().to_owned();
            (None, Some(validated), hash)
        }
        other => {
            return Err(anyhow!(
                "unsupported engine evidence context schema: {other}"
            ))
        }
    };
    Ok(EngineEvidenceState {
        context,
        phase0_context,
        context_sha256,
        source_hashes: BTreeMap::from([
            (
                format!("evidence/{EVIDENCE_CONTEXT_FILE}"),
                raw_sha256(&context_bytes),
            ),
            (
                format!("evidence/{TRUST_STORE_FILE}"),
                raw_sha256(&trust_bytes),
            ),
        ]),
    })
}

impl EngineEvidenceState {
    fn authorize_molecule_model(
        &self,
        module_id: &str,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
        molecule_facts_sha256: &str,
    ) -> Option<AuthorizedMoleculeModelInputV1> {
        self.context
            .as_ref()
            .and_then(|context| {
                context.authorize(
                    module_id,
                    candidate_id,
                    candidate_contract_hash_v1,
                    molecule_facts_sha256,
                )
            })
            .or_else(|| {
                self.phase0_context.as_ref()?.authorize_molecule_model(
                    module_id,
                    candidate_id,
                    candidate_contract_hash_v1,
                    molecule_facts_sha256,
                )
            })
    }

    fn authorize_runtime_grant(
        &self,
        module_id: &str,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
        binding_kind: AuditInputBindingKindV1,
        normalized_input_sha256: &str,
    ) -> Option<AuthorizedAuditModuleInputV1> {
        self.phase0_context.as_ref()?.authorize_runtime_grant(
            module_id,
            candidate_id,
            candidate_contract_hash_v1,
            binding_kind,
            normalized_input_sha256,
        )
    }
}

fn read_host_owned_file(path: &Path) -> Result<Vec<u8>> {
    let metadata = fs::symlink_metadata(path)
        .with_context(|| format!("reading host evidence metadata {}", path.display()))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err(anyhow!(
            "host evidence must be a non-symlink regular file: {}",
            path.display()
        ));
    }
    fs::read(path).with_context(|| format!("reading host evidence {}", path.display()))
}

fn build_trust_store(file: TrustStoreFileV1) -> Result<TrustStore> {
    if file.schema != TRUST_STORE_SCHEMA || file.keys.is_empty() {
        return Err(anyhow!(
            "host evidence trust store is empty or has the wrong schema"
        ));
    }
    let mut trust_store = TrustStore::default();
    let mut key_ids = BTreeSet::new();
    for key in file.keys {
        if key.key_id.trim().is_empty()
            || key.algorithm != "Ed25519"
            || !matches!(key.status.as_str(), "TRUSTED" | "REVOKED")
            || !key_ids.insert(key.key_id.clone())
        {
            return Err(anyhow!(
                "invalid or duplicate host evidence trust-store key"
            ));
        }
        let bytes = decode_hex_32(&key.public_key_hex)?;
        trust_store.insert(key.key_id.clone(), bytes)?;
        if key.status == "REVOKED" {
            trust_store.revoke(key.key_id);
        }
    }
    Ok(trust_store)
}

fn decode_hex_32(value: &str) -> Result<[u8; 32]> {
    if value.len() != 64 {
        return Err(anyhow!("Ed25519 public key must be 32-byte lowercase hex"));
    }
    let mut bytes = [0_u8; 32];
    for (index, pair) in value.as_bytes().chunks_exact(2).enumerate() {
        let text = std::str::from_utf8(pair)?;
        if text
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
        {
            return Err(anyhow!("Ed25519 public key must be lowercase hex"));
        }
        bytes[index] = u8::from_str_radix(text, 16)?;
    }
    Ok(bytes)
}

fn raw_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn normalized_candidate(candidate: &CandidateEnvelope) -> Result<Value> {
    let mut output = candidate.value().clone();
    output["input_kind"] = Value::String(candidate.candidate_type().into());
    output["input_hash"] = Value::String(candidate.contract_hash_v1().into());
    output["original_bytes_sha256"] = Value::String(candidate.original_bytes_sha256().into());
    match candidate.candidate_type() {
        "molecule" => {
            normalize_molecule(&mut output);
        }
        "formulation" => normalize_formulation(&mut output)?,
        _ => {}
    }
    Ok(output)
}

fn normalize_molecule(candidate: &mut Value) {
    let input = candidate
        .get("molecule")
        .and_then(Value::as_object)
        .and_then(|molecule| {
            molecule
                .get("smiles")
                .or_else(|| molecule.get("canonical_smiles"))
        })
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty());
    let Some(input) = input else {
        candidate["normalization"] = json!({
            "status": "REJECTED",
            "required_toolkit": "RDKit C++ 2026.03.2",
            "molecule_facts_v1": null,
            "canonical_structure_hash": null,
            "error": "missing or empty SMILES input",
            "structure_policy": "host-owned normalization; candidate-supplied facts ignored",
        });
        return;
    };
    match molecule_facts(input) {
        Ok(facts) => {
            let canonical_structure_hash = facts.canonical_structure_sha256.clone();
            candidate["normalization"] = json!({
                "status": "NORMALIZED",
                "required_toolkit": "RDKit C++ 2026.03.2",
                "canonical_structure_hash": canonical_structure_hash,
                "molecule_facts_v1": facts,
                "error": null,
                "structure_policy": "host-owned normalization; candidate-supplied facts ignored",
            });
        }
        Err(error) => {
            candidate["normalization"] = json!({
                "status": "REJECTED_OR_BACKEND_UNAVAILABLE",
                "required_toolkit": "RDKit C++ 2026.03.2",
                "molecule_facts_v1": null,
                "canonical_structure_hash": null,
                "error": error.to_string(),
                "structure_policy": "host-owned normalization; candidate-supplied facts ignored",
            });
        }
    }
}

fn normalize_formulation(candidate: &mut Value) -> Result<()> {
    let formulation = candidate
        .get("formulation")
        .and_then(Value::as_object)
        .ok_or_else(|| anyhow!("formulation payload must be an object"))?;
    let recipe = formulation
        .get("recipe")
        .and_then(Value::as_object)
        .unwrap_or(formulation);
    let mut normalized_recipe = Map::new();
    for part_name in ["part_A", "part_B"] {
        let part = recipe
            .get(part_name)
            .and_then(Value::as_object)
            .ok_or_else(|| anyhow!("formulation requires {part_name}"))?;
        let mut normalized_part = Map::new();
        for (key, value) in part {
            let (ingredient_id, mass) = if let Some(mass) = value.as_f64() {
                (key.clone(), mass)
            } else {
                let row = value
                    .as_object()
                    .ok_or_else(|| anyhow!("recipe entry {part_name}.{key} is invalid"))?;
                let id = row
                    .get("ingredient_id")
                    .and_then(Value::as_str)
                    .unwrap_or(key)
                    .to_owned();
                let mass = row
                    .get("mass_g")
                    .and_then(Value::as_f64)
                    .ok_or_else(|| anyhow!("recipe entry {part_name}.{key} lacks mass_g"))?;
                (id, mass)
            };
            if !mass.is_finite() || mass < 0.0 {
                return Err(anyhow!("recipe mass {part_name}.{key} is invalid"));
            }
            if mass > 0.0 {
                normalized_part.insert(
                    ingredient_id.clone(),
                    json!({"ingredient_id": ingredient_id, "mass_g": mass}),
                );
            }
        }
        normalized_recipe.insert(part_name.into(), Value::Object(normalized_part));
    }
    let basis = formulation
        .get("basis")
        .cloned()
        .unwrap_or_else(|| Value::String("mass_g".into()));
    let formula_payload = json!({"recipe": normalized_recipe, "basis": basis});
    candidate["normalized_recipe"] = formula_payload.clone();
    candidate["formula_hash"] = Value::String(stable_hash(&formula_payload));
    Ok(())
}

struct Classified {
    constraints: Vec<Value>,
    evidence_gaps: Vec<Value>,
    blocked_claims: Vec<Value>,
    pareto_status: String,
}

fn classify(candidate: &CandidateEnvelope, envelopes: &[Value]) -> Classified {
    let mut constraints = Vec::new();
    let mut evidence_gaps = Vec::new();
    let mut blocked_claims = Vec::new();
    for envelope in envelopes {
        let module_id = envelope
            .get("module_id")
            .and_then(Value::as_str)
            .unwrap_or("unknown");
        if envelope.get("status").and_then(Value::as_str) != Some("SCORED") {
            let reason = envelope
                .get("missing_inputs")
                .and_then(Value::as_array)
                .and_then(|rows| rows.first())
                .and_then(Value::as_str)
                .unwrap_or("capability did not pass its locked gate");
            constraints.push(json!({
                "module_id": module_id,
                "status": envelope.get("status").cloned().unwrap_or(Value::Null),
                "reason": reason,
                "eligible": false,
            }));
            evidence_gaps.push(json!({
                "module_id": module_id,
                "status": envelope.get("status").cloned().unwrap_or(Value::Null),
                "reason": reason,
            }));
        }
        if let Some(locks) = envelope.get("claim_locks").and_then(Value::as_object) {
            for (lock, value) in locks {
                if value == &Value::Bool(true) {
                    blocked_claims.push(json!({"module_id": module_id, "claim_lock": lock}));
                }
            }
        }
    }
    let declarations = candidate
        .value()
        .pointer("/context/optimization_request/hard_constraints")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    let mut hard_failed = false;
    for declaration in declarations {
        let module_id = declaration
            .get("module_id")
            .and_then(Value::as_str)
            .unwrap_or_default();
        let path = declaration
            .get("path")
            .and_then(Value::as_str)
            .unwrap_or_default();
        let section = declaration
            .get("section")
            .and_then(Value::as_str)
            .unwrap_or("gates");
        let envelope = envelopes
            .iter()
            .find(|row| row.get("module_id").and_then(Value::as_str) == Some(module_id));
        let actual = envelope
            .and_then(|row| lookup(row.get(section)?, path))
            .cloned();
        let expected = declaration.get("expected").cloned().unwrap_or(Value::Null);
        let passed = envelope
            .and_then(|row| row.get("status"))
            .and_then(Value::as_str)
            == Some("SCORED")
            && actual.as_ref().is_some_and(|actual| {
                compare(
                    actual,
                    declaration
                        .get("operator")
                        .and_then(Value::as_str)
                        .unwrap_or("=="),
                    &expected,
                )
            });
        hard_failed |= !passed;
        constraints.push(json!({
            "module_id": module_id,
            "path": path,
            "actual": actual,
            "expected": expected,
            "passed": passed,
            "hard": true,
            "reason": if passed { Value::Null } else { Value::String("locked deterministic gate did not pass".into()) },
        }));
    }
    Classified {
        constraints,
        evidence_gaps,
        blocked_claims,
        pareto_status: if hard_failed {
            "BLOCKED".into()
        } else {
            "NO_ELIGIBLE_OBJECTIVES".into()
        },
    }
}

fn lookup<'a>(mut value: &'a Value, path: &str) -> Option<&'a Value> {
    for part in path.split('.').filter(|part| !part.is_empty()) {
        value = value.get(part)?;
    }
    Some(value)
}

fn compare(actual: &Value, operator: &str, expected: &Value) -> bool {
    match operator {
        "==" => actual == expected,
        "!=" => actual != expected,
        ">=" => numbers(actual, expected).is_some_and(|(left, right)| left >= right),
        "<=" => numbers(actual, expected).is_some_and(|(left, right)| left <= right),
        ">" => numbers(actual, expected).is_some_and(|(left, right)| left > right),
        "<" => numbers(actual, expected).is_some_and(|(left, right)| left < right),
        _ => false,
    }
}

fn numbers(left: &Value, right: &Value) -> Option<(f64, f64)> {
    Some((left.as_f64()?, right.as_f64()?))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn missing_evidence() -> EngineEvidenceState {
        EngineEvidenceState {
            context: None,
            phase0_context: None,
            context_sha256: stable_hash(&json!({
                "schema": "amphora.engine-evidence-context-state.v1",
                "status": "MISSING",
            })),
            source_hashes: BTreeMap::new(),
        }
    }

    fn temporary_path(label: &str) -> PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!(
            "amphora-engine-{label}-{}-{nonce}",
            std::process::id()
        ))
    }

    fn molecule() -> Value {
        json!({
            "candidate_id": "x",
            "candidate_type": "molecule",
            "molecule": {"smiles": "C1OC1", "role": "resin"},
            "context": {"optimization_request": {"objective_list": [{"module_id": "amphora-molecule-novelty", "path": "novelty_score"}]}}
        })
    }

    #[test]
    fn registry_is_exact_and_has_no_ranking_capability() {
        let registry = NativeRegistry::global().unwrap();
        assert_eq!(registry.module_count(), 29);
        assert!(registry
            .manifest
            .modules
            .iter()
            .all(|module| !module.ranking_eligible));
        assert!(matches!(
            registry.resolve("scorer-supplied-identity"),
            Err(RegistryError::UnknownModule(_))
        ));
    }

    #[test]
    fn scientific_objectives_are_quarantined() {
        let registry = NativeRegistry::global().unwrap();
        let result = execute(
            registry,
            &missing_evidence(),
            &molecule(),
            42,
            json!({}),
            "run-test",
            None,
        )
        .unwrap();
        assert_eq!(
            result.pointer("/optimization/objectives"),
            Some(&Value::Array(Vec::new()))
        );
        assert_eq!(
            result.pointer("/optimization/pareto_status"),
            Some(&Value::String("NO_ELIGIBLE_OBJECTIVES".into()))
        );
        assert!(result["score_envelopes"]
            .as_array()
            .unwrap()
            .iter()
            .all(|row| row["usable_by_optimizer"] == Value::Bool(false)));
    }

    #[test]
    fn explicit_campaign_traversal_dispatches_each_capability_family() {
        let result = execute(
            NativeRegistry::global().unwrap(),
            &missing_evidence(),
            &molecule(),
            42,
            json!({}),
            "explicit-family-dispatch",
            Some(&["amphora-candidate-contract", "amphora-molecule-property"]),
        )
        .unwrap();
        let envelopes = result["score_envelopes"].as_array().unwrap();
        let contract = envelopes
            .iter()
            .find(|row| row["module_id"] == "amphora-candidate-contract")
            .unwrap();
        let property = envelopes
            .iter()
            .find(|row| row["module_id"] == "amphora-molecule-property")
            .unwrap();
        assert_eq!(contract["status"], "SCORED");
        assert_eq!(contract["score_0_1"], 1.0);
        assert_ne!(property["status"], "ERROR");
        assert!(envelopes
            .iter()
            .all(|row| row["usable_by_optimizer"] == Value::Bool(false)));
    }

    #[test]
    fn missing_evidence_context_is_stable_and_candidate_evidence_cannot_replace_it() {
        let evidence_root = temporary_path("missing-evidence");
        let pool = EnginePool::with_evidence_root(".", &evidence_root, 1).unwrap();
        let first_hash = pool.evidence_context_sha256().to_owned();
        let second = EnginePool::with_evidence_root(".", &evidence_root, 1).unwrap();
        assert_eq!(first_hash, second.evidence_context_sha256());

        let mut input = molecule();
        input["verified_molecule_role_ranker_phase1_receipt"] = json!({
            "signature_verified": true,
            "passed": true,
            "decision_use": "RANKING"
        });
        input["evidence_context"] = json!({
            "schema": "amphora.engine-evidence-context.v1",
            "molecule_models": {"amphora-molecule-role-ranker": {}}
        });
        let result = pool
            .score(&input, 42, json!({}), "candidate-evidence")
            .unwrap()
            .0;
        assert_eq!(result["provenance"]["evidence_context_sha256"], first_hash);
        assert!(result["optimization"]["objectives"]
            .as_array()
            .unwrap()
            .is_empty());
    }

    #[test]
    fn present_malformed_evidence_fails_engine_construction() {
        let evidence_root = temporary_path("malformed-evidence");
        fs::create_dir_all(&evidence_root).unwrap();
        fs::write(evidence_root.join(EVIDENCE_CONTEXT_FILE), b"{}").unwrap();
        fs::write(
            evidence_root.join(TRUST_STORE_FILE),
            br#"{"schema":"amphora.trust-store.v1","keys":[]}"#,
        )
        .unwrap();
        let error = EnginePool::with_evidence_root(".", &evidence_root, 1)
            .err()
            .expect("malformed evidence must fail")
            .to_string();
        assert!(error.contains("missing field") || error.contains("evidence"));
        fs::remove_dir_all(evidence_root).unwrap();
    }

    #[cfg(unix)]
    #[test]
    fn symlinked_evidence_root_is_rejected() {
        use std::os::unix::fs::symlink;

        let real_root = temporary_path("real-evidence");
        let linked_root = temporary_path("linked-evidence");
        fs::create_dir_all(&real_root).unwrap();
        symlink(&real_root, &linked_root).unwrap();
        let error = EnginePool::with_evidence_root(".", &linked_root, 1)
            .err()
            .expect("symlinked evidence root must fail")
            .to_string();
        assert!(error.contains("non-symlink directory"));
        fs::remove_file(linked_root).unwrap();
        fs::remove_dir_all(real_root).unwrap();
    }

    #[cfg(not(feature = "rdkit"))]
    #[test]
    fn host_normalization_ignores_candidate_supplied_facts_and_fails_closed() {
        let candidate = CandidateEnvelope::from_value(json!({
            "candidate_id": "untrusted-facts",
            "candidate_type": "molecule",
            "molecule": {
                "smiles": "C1OC1",
                "canonical_smiles": "not-trusted",
                "molecular_weight_g_mol": 1.0,
                "oxirane_ring_count": 99
            }
        }))
        .unwrap();
        let normalized = normalized_candidate(&candidate).unwrap();
        assert!(normalized
            .pointer("/normalization/molecule_facts_v1")
            .is_some_and(Value::is_null));
        assert!(normalized
            .pointer("/normalization/error")
            .and_then(Value::as_str)
            .is_some_and(|error| error.contains("pinned RDKit")));
        assert_eq!(
            normalized.pointer("/molecule/molecular_weight_g_mol"),
            Some(&json!(1.0))
        );
    }

    #[cfg(feature = "rdkit")]
    #[test]
    fn pinned_host_normalization_feeds_one_fact_record_to_molecule_modules() {
        let mut input = molecule();
        input["molecule"]["canonical_smiles"] = Value::String("candidate-value-is-ignored".into());
        input["molecule"]["molecular_weight_g_mol"] = json!(1.0);
        let result = execute(
            NativeRegistry::global().unwrap(),
            &missing_evidence(),
            &input,
            42,
            json!({}),
            "native-rdkit",
            None,
        )
        .unwrap();
        assert_eq!(
            result.pointer("/candidate/normalized_molecule/normalization/status"),
            Some(&Value::String("NORMALIZED".into()))
        );
        assert_ne!(
            result.pointer(
                "/candidate/normalized_molecule/normalization/molecule_facts_v1/canonical_isomeric_smiles"
            ),
            Some(&Value::String("candidate-value-is-ignored".into()))
        );
        let property = result["score_envelopes"]
            .as_array()
            .unwrap()
            .iter()
            .find(|row| row["module_id"] == "amphora-molecule-property")
            .unwrap();
        assert_eq!(property["status"], "SCORED");
        assert_eq!(
            property["metrics"]["property_results"]["reactive_group_counts"]["oxirane_rings"],
            1
        );
        assert!(property["objective_values"].as_object().unwrap().is_empty());
    }

    #[test]
    fn mutation_changes_lineage_only() {
        let pool = EnginePool::new(".", 2).unwrap();
        let input = molecule();
        let output = pool
            .mutate(&input, 42, json!({"parent_ids":["x"],"generation":1}))
            .unwrap();
        assert_eq!(input["molecule"], output["molecule"]);
        assert_ne!(input["candidate_id"], output["candidate_id"]);
        assert_eq!(
            output.pointer("/lineage/generation_status"),
            Some(&Value::String("QUARANTINED_NO_STRUCTURE_CHANGE".into()))
        );
    }

    #[test]
    fn scoring_is_equal_across_one_two_and_eight_workers() {
        let requests = vec![
            (molecule(), 42, json!({}), "worker-equality".into()),
            (molecule(), 43, json!({}), "worker-equality".into()),
        ];
        let hashes = [1, 2, 8]
            .into_iter()
            .map(|workers| {
                EnginePool::new(".", workers)
                    .unwrap()
                    .score_many(requests.clone())
                    .into_iter()
                    .map(|result| stable_hash(&result.unwrap().0))
                    .collect::<Vec<_>>()
            })
            .collect::<Vec<_>>();
        assert_eq!(hashes[0], hashes[1]);
        assert_eq!(hashes[0], hashes[2]);
    }
}
