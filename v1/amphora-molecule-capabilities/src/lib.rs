#![forbid(unsafe_code)]

use amphora_core::{
    stable_hash, AuditInputBindingKindV1, AuthorizedAuditModuleInputV1,
    AuthorizedMoleculeModelInputV1, CandidateEnvelope, Capability, CapabilityError,
    ExecutionContext, FeatureSnapshot, ModuleDescriptor, ModuleResult,
};
use amphora_rdkit_ffi::{
    execute_reaction, fingerprint_tanimoto, molecule_facts, morgan_fingerprint, MoleculeFactsV1,
    MorganFingerprintV1, REQUIRED_RDKIT_VERSION,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::sync::LazyLock;

pub const GENERATOR_ID: &str = "amphora-molecule-generator";
pub const ROLE_RANKER_ID: &str = "amphora-molecule-role-ranker";
pub const NOVELTY_ID: &str = "amphora-molecule-novelty";
pub const PROPERTY_ID: &str = "amphora-molecule-property";
pub const DESIGN_GATE_ID: &str = "amphora-molecule-design-gate";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ReactionGrammarV1 {
    pub grammar_id: String,
    pub reaction_family: String,
    pub reaction_smarts: String,
    pub source_reaction_ids: Vec<String>,
    pub source_dataset_ids: Vec<String>,
    pub applicability_constraints: BTreeMap<String, Value>,
    pub grammar_sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct GenerationRequestV1 {
    pub parent_structure: String,
    pub reaction_family: String,
    pub deterministic_seed: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct GeneratedMoleculeProposalV1 {
    pub parent_structure_sha256: String,
    pub product_structure: String,
    pub product_structure_sha256: String,
    pub reaction_template_sha256: String,
    pub grammar_sha256: String,
    pub reaction_family: String,
    pub requested_role: String,
    pub source_reaction_ids: Vec<String>,
    pub source_dataset_ids: Vec<String>,
    pub bemis_murcko_scaffold: String,
    pub scaffold_sha256: String,
    pub molecule_facts: MoleculeFactsV1,
    pub deterministic_seed: u64,
    pub lineage: String,
    pub applicability: String,
    pub unmade: bool,
    pub solver_use: String,
}

#[derive(Debug, thiserror::Error)]
pub enum GenerationError {
    #[error("generator runtime grant is absent or bound to different input")]
    Authorization,
    #[error("authorized grammar artifact is invalid or does not contain the requested family")]
    Grammar,
    #[error("generation request is outside grammar applicability")]
    Applicability,
    #[error("pinned chemistry backend rejected generation: {0}")]
    Chemistry(String),
    #[error("generator artifact JSON: {0}")]
    Json(#[from] serde_json::Error),
}

impl ReactionGrammarV1 {
    pub fn validate(&self) -> Result<(), GenerationError> {
        let mut unsigned = self.clone();
        unsigned.grammar_sha256.clear();
        if self.grammar_id.trim().is_empty()
            || self.reaction_family.trim().is_empty()
            || self.reaction_smarts.trim().is_empty()
            || self.source_reaction_ids.is_empty()
            || self.source_dataset_ids.is_empty()
            || self
                .source_reaction_ids
                .iter()
                .chain(&self.source_dataset_ids)
                .any(|id| id.trim().is_empty())
            || self.applicability_constraints.is_empty()
            || self.grammar_sha256 != stable_hash(&serde_json::to_value(unsigned)?)
        {
            return Err(GenerationError::Grammar);
        }
        Ok(())
    }
}

/// Execute only grammar embedded in a verified host runtime grant.
pub fn generate_authorized(
    request_id: &str,
    parent_structures: &[String],
    requested_role: &str,
    reaction_family: &str,
    deterministic_seed: u64,
    authorization: &AuthorizedAuditModuleInputV1,
) -> Result<Vec<GeneratedMoleculeProposalV1>, GenerationError> {
    if request_id.trim().is_empty()
        || parent_structures.is_empty()
        || !matches!(requested_role, "resin" | "hardener")
        || reaction_family.trim().is_empty()
    {
        return Err(GenerationError::Applicability);
    }
    let parent_facts = parent_structures
        .iter()
        .map(|structure| {
            molecule_facts(structure).map_err(|error| GenerationError::Chemistry(error.to_string()))
        })
        .collect::<Result<Vec<_>, _>>()?;
    let request_value = json!({
        "request_id": request_id,
        "parent_structures": parent_structures,
        "requested_role": requested_role,
        "reaction_family": reaction_family,
        "deterministic_seed": deterministic_seed,
    });
    let parent_facts_value = serde_json::to_value(&parent_facts)?;
    if !authorization.validate_binding(
        GENERATOR_ID,
        request_id,
        &stable_hash(&request_value),
        AuditInputBindingKindV1::MoleculeFacts,
        &stable_hash(&parent_facts_value),
    ) {
        return Err(GenerationError::Authorization);
    }
    let entries = authorization
        .module_artifact()
        .get("reaction_grammars")
        .and_then(Value::as_array)
        .ok_or(GenerationError::Grammar)?;
    let grammar = entries
        .iter()
        .map(|entry| serde_json::from_value::<ReactionGrammarV1>(entry.clone()))
        .collect::<Result<Vec<_>, _>>()?
        .into_iter()
        .find(|entry| entry.reaction_family == reaction_family)
        .ok_or(GenerationError::Grammar)?;
    grammar.validate()?;
    if grammar
        .applicability_constraints
        .get("reactant_count")
        .and_then(Value::as_u64)
        != Some(parent_structures.len() as u64)
    {
        return Err(GenerationError::Applicability);
    }
    let reaction_template_sha256 = stable_hash(&Value::String(grammar.reaction_smarts.clone()));
    let mut proposals = execute_reaction(&grammar.reaction_smarts, parent_structures)
        .map_err(|error| GenerationError::Chemistry(error.to_string()))?
        .into_iter()
        .map(|product| {
            let facts = molecule_facts(&product)
                .map_err(|error| GenerationError::Chemistry(error.to_string()))?;
            let fingerprint = morgan_fingerprint(&product)
                .map_err(|error| GenerationError::Chemistry(error.to_string()))?;
            let applicable = match requested_role {
                "resin" => facts.oxirane_ring_count > 0,
                "hardener" => facts.reactive_amine_hydrogen_count > 0,
                _ => false,
            };
            if !applicable {
                return Err(GenerationError::Applicability);
            }
            Ok(GeneratedMoleculeProposalV1 {
                parent_structure_sha256: stable_hash(&parent_facts_value),
                product_structure: facts.canonical_isomeric_smiles.clone(),
                product_structure_sha256: facts.canonical_structure_sha256.clone(),
                reaction_template_sha256: reaction_template_sha256.clone(),
                grammar_sha256: grammar.grammar_sha256.clone(),
                reaction_family: grammar.reaction_family.clone(),
                requested_role: requested_role.into(),
                source_reaction_ids: grammar.source_reaction_ids.clone(),
                source_dataset_ids: grammar.source_dataset_ids.clone(),
                bemis_murcko_scaffold: fingerprint.bemis_murcko_scaffold.clone(),
                scaffold_sha256: stable_hash(&Value::String(fingerprint.bemis_murcko_scaffold)),
                molecule_facts: facts,
                deterministic_seed,
                lineage: stable_hash(&json!({
                    "request": request_value,
                    "grammar_sha256": grammar.grammar_sha256,
                    "product": product,
                })),
                applicability: "ROLE_APPROPRIATE_REACTIVE_GROUP_ONLY".into(),
                unmade: true,
                solver_use: "AUDIT_ONLY".into(),
            })
        })
        .collect::<Result<Vec<_>, GenerationError>>()?;
    proposals.sort_by(|left, right| {
        left.product_structure_sha256
            .cmp(&right.product_structure_sha256)
    });
    proposals
        .dedup_by(|left, right| left.product_structure_sha256 == right.product_structure_sha256);
    if proposals.is_empty() {
        return Err(GenerationError::Chemistry(
            "reaction produced no unique applicable products".into(),
        ));
    }
    Ok(proposals)
}
const NOVELTY_CORPUS_BYTES: &[u8] =
    include_bytes!("../../amphora-molecule-novelty/reference/novelty-corpus.v1.json");

static GENERATOR_DESCRIPTOR: LazyLock<ModuleDescriptor> = LazyLock::new(|| ModuleDescriptor {
    project: GENERATOR_ID.into(),
    authority_ceiling: "LOCKED_INTERNAL".into(),
    solver_use_ceiling: "AUDIT_ONLY".into(),
    model_readiness_ceiling: "MODEL_READINESS_ONLY".into(),
    ranking_eligible: false,
    candidate_types: vec!["molecule".into()],
    non_blocking_claim_locks: vec![
        "feedback_v1_polymer_corpus_context_only".into(),
        "generated_molecules_unmade_unvalidated".into(),
        "not_a_compliant_recommendation".into(),
    ],
    readiness: "LOCKED_INTERNAL".into(),
});

static ROLE_RANKER_DESCRIPTOR: LazyLock<ModuleDescriptor> = LazyLock::new(|| ModuleDescriptor {
    project: ROLE_RANKER_ID.into(),
    authority_ceiling: "LIMITED_SANITY".into(),
    solver_use_ceiling: "AUDIT_ONLY".into(),
    model_readiness_ceiling: "NOT_PROVEN".into(),
    ranking_eligible: false,
    candidate_types: vec!["molecule".into()],
    non_blocking_claim_locks: vec![
        "ambiguous_role_is_audit_only".into(),
        "candidate_role_evidence_is_not_self_authorizing".into(),
        "commercial_product_values_not_upgraded_from_defined_monomer".into(),
        "defined_structure_does_not_establish_liquid_state".into(),
        "feedback_v1_polymer_corpus_context_only".into(),
        "no_polyamide_marine_or_approval_claim_from_smiles_or_text".into(),
        "role_rank_is_not_qualification_or_procurement_authority".into(),
    ],
    readiness: "PRE_PHASE_0".into(),
});

static NOVELTY_DESCRIPTOR: LazyLock<ModuleDescriptor> = LazyLock::new(|| ModuleDescriptor {
    project: NOVELTY_ID.into(),
    authority_ceiling: "LIMITED_SANITY".into(),
    solver_use_ceiling: "AUDIT_ONLY".into(),
    model_readiness_ceiling: "NOT_PROVEN".into(),
    ranking_eligible: false,
    candidate_types: vec!["molecule".into()],
    non_blocking_claim_locks: vec![
        "corpus_distance_is_not_synthesis_feasibility".into(),
        "frontier_requires_experimental_validation".into(),
        "novelty_is_not_patentability_or_desirability".into(),
        "novelty_is_not_performance".into(),
    ],
    readiness: "LOCKED_INTERNAL".into(),
});

static PROPERTY_DESCRIPTOR: LazyLock<ModuleDescriptor> = LazyLock::new(|| ModuleDescriptor {
    project: PROPERTY_ID.into(),
    authority_ceiling: "REAL_ARITHMETIC".into(),
    solver_use_ceiling: "DISABLED".into(),
    model_readiness_ceiling: "MODEL_READINESS_ONLY".into(),
    ranking_eligible: false,
    candidate_types: vec!["molecule".into()],
    non_blocking_claim_locks: vec![
        "benchmark_required_for_optimizer_use".into(),
        "commercial_product_values_not_upgraded_from_defined_monomer".into(),
        "estimated_density_not_authoritative".into(),
    ],
    readiness: "PRE_PHASE_0".into(),
});

static DESIGN_GATE_DESCRIPTOR: LazyLock<ModuleDescriptor> = LazyLock::new(|| ModuleDescriptor {
    project: DESIGN_GATE_ID.into(),
    authority_ceiling: "REAL_ARITHMETIC".into(),
    solver_use_ceiling: "CONSTRAINT_ONLY".into(),
    model_readiness_ceiling: "MODEL_READINESS_ONLY".into(),
    ranking_eligible: false,
    candidate_types: vec!["molecule".into()],
    non_blocking_claim_locks: vec![
        "does_not_establish_ehs_safety".into(),
        "does_not_establish_procurement".into(),
        "does_not_establish_product_performance".into(),
        "does_not_establish_qualification".into(),
        "does_not_establish_synthesis_feasibility".into(),
    ],
    readiness: "PRE_PHASE_0".into(),
});

#[derive(Debug, Clone, Copy)]
pub struct MoleculeCapability {
    pub descriptor: &'static ModuleDescriptor,
}

impl MoleculeCapability {
    pub const fn new(descriptor: &'static ModuleDescriptor) -> Self {
        Self { descriptor }
    }

    pub fn evaluate_authorized(
        &self,
        candidate: &CandidateEnvelope,
        features: &FeatureSnapshot,
        context: &ExecutionContext,
        authorization: Option<&AuthorizedMoleculeModelInputV1>,
    ) -> Result<ModuleResult, CapabilityError> {
        if candidate.candidate_type() != "molecule" {
            return Err(CapabilityError::CandidateType);
        }

        match self.descriptor.project.as_str() {
            GENERATOR_ID => Ok(generator_result(candidate, context)),
            ROLE_RANKER_ID => Ok(role_ranker_result(candidate, features, authorization)),
            NOVELTY_ID => Ok(novelty_result(candidate, features)),
            PROPERTY_ID => Ok(property_result(candidate, features)),
            DESIGN_GATE_ID => Ok(design_gate_result(candidate, features)),
            unknown => Err(CapabilityError::InvalidInput(format!(
                "unknown molecular capability descriptor: {unknown}"
            ))),
        }
    }
}

pub fn descriptors() -> [&'static ModuleDescriptor; 5] {
    [
        &GENERATOR_DESCRIPTOR,
        &ROLE_RANKER_DESCRIPTOR,
        &NOVELTY_DESCRIPTOR,
        &PROPERTY_DESCRIPTOR,
        &DESIGN_GATE_DESCRIPTOR,
    ]
}

pub fn capabilities() -> Vec<MoleculeCapability> {
    descriptors()
        .into_iter()
        .map(MoleculeCapability::new)
        .collect()
}

pub fn capability(module_id: &str) -> Option<MoleculeCapability> {
    descriptors()
        .into_iter()
        .find(|descriptor| descriptor.project == module_id)
        .map(MoleculeCapability::new)
}

impl Capability for MoleculeCapability {
    fn descriptor(&self) -> &'static ModuleDescriptor {
        self.descriptor
    }

    fn evaluate(
        &self,
        candidate: &CandidateEnvelope,
        features: &FeatureSnapshot,
        context: &ExecutionContext,
    ) -> Result<ModuleResult, CapabilityError> {
        self.evaluate_authorized(candidate, features, context, None)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ObviousStructureIssue {
    Missing,
    Empty,
    Fragment,
    WildcardOrQuery,
}

fn molecule(candidate: &CandidateEnvelope) -> Option<&Map<String, Value>> {
    candidate.value().get("molecule")?.as_object()
}

fn structure_text(candidate: &CandidateEnvelope) -> Result<&str, ObviousStructureIssue> {
    let molecule = molecule(candidate).ok_or(ObviousStructureIssue::Missing)?;
    let structure = molecule
        .get("canonical_smiles")
        .or_else(|| molecule.get("smiles"))
        .and_then(Value::as_str)
        .ok_or(ObviousStructureIssue::Missing)?;
    let structure = structure.trim();
    if structure.is_empty() {
        return Err(ObviousStructureIssue::Empty);
    }
    if structure.contains('.') {
        return Err(ObviousStructureIssue::Fragment);
    }
    if structure.contains('*') || structure.contains('~') {
        return Err(ObviousStructureIssue::WildcardOrQuery);
    }
    Ok(structure)
}

fn declared_role(candidate: &CandidateEnvelope) -> Option<&str> {
    let molecule = molecule(candidate)?;
    molecule
        .get("declared_role")
        .or_else(|| molecule.get("role"))
        .and_then(Value::as_str)
}

fn normalized_facts(features: &FeatureSnapshot) -> Option<MoleculeFactsV1> {
    features
        .values
        .get("molecule_facts_v1")
        .cloned()
        .and_then(|value| serde_json::from_value(value).ok())
}

fn normalization_error(features: &FeatureSnapshot) -> Option<&str> {
    features
        .values
        .get("molecule_normalization_error")
        .and_then(Value::as_str)
}

fn measured_only_product(candidate: &CandidateEnvelope) -> bool {
    let Some(molecule) = molecule(candidate) else {
        return false;
    };
    molecule.get("commercial_product").and_then(Value::as_bool) == Some(true)
        || molecule.get("polydisperse").and_then(Value::as_bool) == Some(true)
        || molecule.get("source_status").and_then(Value::as_str) == Some("MEASURED_PRODUCT_ONLY")
        || molecule.get("structure_authority").and_then(Value::as_str) == Some("MEASURED_ONLY")
}

fn base_metrics(candidate: &CandidateEnvelope) -> BTreeMap<String, Value> {
    BTreeMap::from([
        (
            "candidate_contract_hash_v1".into(),
            Value::String(candidate.contract_hash_v1().into()),
        ),
        (
            "original_bytes_sha256".into(),
            Value::String(candidate.original_bytes_sha256().into()),
        ),
        ("ranking_quarantine".into(), Value::Bool(true)),
        (
            "scientific_applicability".into(),
            Value::String("UNVALIDATED".into()),
        ),
    ])
}

fn generator_result(candidate: &CandidateEnvelope, context: &ExecutionContext) -> ModuleResult {
    let mut metrics = base_metrics(candidate);
    metrics.extend([
        (
            "generation_status".into(),
            Value::String("LOCKED_INTERNAL".into()),
        ),
        ("proposal_count".into(), json!(0)),
        (
            "lineage_diagnostic".into(),
            json!({
                "deterministic_seed": context.deterministic_seed,
                "parent_candidate_id": candidate.candidate_id(),
                "run_id": context.run_id,
            }),
        ),
        ("pinned_rdkit_available".into(), Value::Bool(false)),
        (
            "locked_reaction_grammar_available".into(),
            Value::Bool(false),
        ),
        ("rights_cleared_corpus_available".into(), Value::Bool(false)),
    ]);
    ModuleResult {
        status: "INSUFFICIENT_INPUT".into(),
        score_0_1: None,
        objective_values: BTreeMap::new(),
        metrics,
        gates: BTreeMap::from([
            ("deterministic_lineage_recorded".into(), Value::Bool(true)),
            ("generation_authorized".into(), Value::Bool(false)),
        ]),
        uncertainty: BTreeMap::from([(
            "scope".into(),
            Value::String("No molecular proposals were generated or evaluated.".into()),
        )]),
        missing_inputs: vec![
            "pinned RDKit C++ 2026.03.2 boundary".into(),
            "locked atom-mapped reaction grammar".into(),
            "rights-cleared generation evidence".into(),
        ],
        explanations: vec![
            "Generation remains a deterministic roadmap lineage diagnostic; it emits no leads or ranking objective."
                .into(),
        ],
        source_refs: Vec::new(),
        evidence_scope: "ROADMAP_DIAGNOSTIC_ONLY".into(),
    }
}

fn role_ranker_result(
    candidate: &CandidateEnvelope,
    features: &FeatureSnapshot,
    authorization: Option<&AuthorizedMoleculeModelInputV1>,
) -> ModuleResult {
    let mut metrics = base_metrics(candidate);
    metrics.insert("favorable_missing_defaults_used".into(), Value::Bool(false));

    let role = declared_role(candidate);
    metrics.insert(
        "declared_role".into(),
        role.map_or(Value::Null, |value| Value::String(value.into())),
    );
    let role_valid = matches!(role, Some("resin" | "hardener"));
    let Some(facts) = normalized_facts(features) else {
        metrics.insert("role_fit_status".into(), Value::String("ABSTAINED".into()));
        if let Some(error) = normalization_error(features) {
            metrics.insert("normalization_error".into(), Value::String(error.into()));
        }
        let mut missing_inputs = vec!["pinned RDKit C++ 2026.03.2 property result".into()];
        if !role_valid {
            missing_inputs.insert(0, "molecule.role must be resin or hardener".into());
        }
        return ModuleResult {
            status: "INSUFFICIENT_INPUT".into(),
            score_0_1: None,
            objective_values: BTreeMap::new(),
            metrics,
            gates: BTreeMap::from([
                ("explicit_supported_role".into(), Value::Bool(role_valid)),
                ("role_ranking_authorized".into(), Value::Bool(false)),
            ]),
            uncertainty: BTreeMap::from([(
                "missingness".into(),
                Value::String("Missing or rejected host-normalized chemistry causes abstention.".into()),
            )]),
            missing_inputs,
            explanations: vec![
                "Role ranking consumes host-normalized MoleculeFactsV1 only; candidate-supplied facts are ignored."
                    .into(),
            ],
            source_refs: Vec::new(),
            evidence_scope: "MOLECULE_ROLE_AUDIT_ONLY".into(),
        };
    };

    let inferred_role = inferred_role(&facts);
    let ambiguous = matches!(inferred_role, "ambiguous" | "out_of_domain");
    let declared_matches = role.is_some_and(|declared| declared == inferred_role);
    let facts_value = serde_json::to_value(&facts).expect("facts serialize");
    let facts_sha256 = stable_hash(&facts_value);
    let authorized_model = authorization.filter(|authorization| {
        authorization.validate_binding(
            ROLE_RANKER_ID,
            candidate.candidate_id(),
            candidate.contract_hash_v1(),
            &facts_sha256,
        ) && role_model_in_domain(authorization.applicability_domain(), role, &facts)
    });
    let role_fit = authorized_model.and_then(|authorization| {
        role_probability(authorization.model_artifact(), &facts).map(|resin_probability| {
            if role == Some("resin") {
                resin_probability
            } else {
                1.0 - resin_probability
            }
        })
    });
    let objective_authorized = role_valid && !ambiguous && role_fit.is_some();
    metrics.insert(
        "role_fit_status".into(),
        Value::String(
            if ambiguous {
                "ABSTAINED_AMBIGUOUS_OR_OUT_OF_DOMAIN"
            } else if objective_authorized {
                "PHASE_1_RECEIPT_AUTHORIZED"
            } else {
                "AUDIT_ONLY"
            }
            .into(),
        ),
    );
    metrics.insert(
        "role_tracks".into(),
        json!({
            "inferred": {
                "role": inferred_role,
                "audit_only": true,
                "source": "host_normalized_reactive_flags"
            },
            "declared": {
                "role": role,
                "supported": role_valid,
                "matches_inferred": declared_matches,
                "phase_1_receipt_live": authorized_model.is_some(),
                "objective_authorized": objective_authorized
            }
        }),
    );
    metrics.insert("molecule_facts_v1".into(), facts_value);
    metrics.insert(
        "commercial_product_claim_locked".into(),
        Value::Bool(measured_only_product(candidate)),
    );
    if let Some(authorization) = authorized_model {
        let (model_signer, evaluation_signer, review_signer) = authorization.signer_ids();
        metrics.extend(BTreeMap::from([
            (
                "evidence_context_sha256".into(),
                Value::String(authorization.evidence_context_sha256().into()),
            ),
            (
                "evidence_package_sha256".into(),
                Value::String(authorization.evidence_package_sha256().into()),
            ),
            (
                "independent_signer_ids".into(),
                json!({
                    "model": model_signer,
                    "evaluation": evaluation_signer,
                    "review": review_signer,
                }),
            ),
        ]));
    }
    let objective_values = if let Some(role_fit) = role_fit.filter(|_| objective_authorized) {
        BTreeMap::from([("role_fit".into(), json!(role_fit))])
    } else {
        BTreeMap::new()
    };
    let missing_inputs = if objective_authorized {
        Vec::new()
    } else if ambiguous {
        vec!["unambiguous in-domain molecule role".into()]
    } else if !role_valid {
        vec!["explicit molecule.role of resin or hardener".into()]
    } else {
        vec!["current identity-bound Phase-1 role-ranker receipt".into()]
    };

    ModuleResult {
        status: if ambiguous { "INSUFFICIENT_INPUT" } else { "SCORED" }.into(),
        score_0_1: None,
        objective_values,
        metrics,
        gates: BTreeMap::from([
            ("explicit_supported_role".into(), Value::Bool(role_valid)),
            ("unambiguous_in_domain_role".into(), Value::Bool(!ambiguous)),
            (
                "live_phase_1_receipt".into(),
                Value::Bool(authorized_model.is_some()),
            ),
            ("role_ranking_authorized".into(), Value::Bool(objective_authorized)),
        ]),
        uncertainty: BTreeMap::from([(
            "scope".into(),
            Value::String("Structural role classification is not coating qualification, safety, procurement, or performance evidence.".into()),
        )]),
        missing_inputs,
        explanations: vec![
            "Both inferred and declared role tracks are retained for audit; only EnginePool's content-, signature-, policy-, candidate-, and MoleculeFacts-bound authorization can populate role_fit."
                .into(),
        ],
        source_refs: Vec::new(),
        evidence_scope: "MOLECULE_ROLE_AUDIT_ONLY".into(),
    }
}

fn inferred_role(facts: &MoleculeFactsV1) -> &'static str {
    match (
        facts.reactive_flags.has_oxirane,
        facts.reactive_flags.has_reactive_amine_hydrogen,
    ) {
        (true, false) => "resin",
        (false, true) => "hardener",
        (true, true) => "ambiguous",
        (false, false) => "out_of_domain",
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NoveltyCorpusV1 {
    pub schema: String,
    pub corpus_id: String,
    pub toolkit_version: String,
    pub morgan_radius: u32,
    pub fingerprint_bits: u32,
    pub use_chirality: bool,
    pub structure_set_sha256: String,
    pub rights_sha256: String,
    pub rights: NoveltyRightsV1,
    pub entries: Vec<NoveltyCorpusEntryV1>,
    pub authority: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NoveltyRightsV1 {
    pub source_id: String,
    pub license: String,
    pub source_url: String,
    pub status: String,
    pub eligible_for_derivatives: bool,
    pub scope: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NoveltyCorpusEntryV1 {
    pub structure_id: String,
    pub canonical_isomeric_smiles: String,
    pub canonical_structure_sha256: String,
}

impl NoveltyCorpusV1 {
    pub fn validate(&self) -> Result<(), String> {
        if self.schema != "amphora.novelty-corpus.v1"
            || self.corpus_id.trim().is_empty()
            || self.toolkit_version != REQUIRED_RDKIT_VERSION
            || self.morgan_radius != 2
            || self.fingerprint_bits != 2048
            || !self.use_chirality
            || self.entries.is_empty()
            || !self.rights.eligible_for_derivatives
            || self.rights.status != "ACCEPTED"
            || self.rights.license.trim().is_empty()
            || self.rights.source_url.trim().is_empty()
        {
            return Err("novelty corpus identity, rights, or fingerprint policy is invalid".into());
        }
        let entries = serde_json::to_value(&self.entries).map_err(|error| error.to_string())?;
        let rights = serde_json::to_value(&self.rights).map_err(|error| error.to_string())?;
        if stable_hash(&entries) != self.structure_set_sha256
            || stable_hash(&rights) != self.rights_sha256
        {
            return Err("novelty corpus content hash is stale".into());
        }
        let mut ids = BTreeSet::new();
        for entry in &self.entries {
            if entry.structure_id.trim().is_empty()
                || entry.canonical_isomeric_smiles.trim().is_empty()
                || !is_sha256(&entry.canonical_structure_sha256)
                || !ids.insert(entry.structure_id.as_str())
            {
                return Err("novelty corpus entry is malformed or duplicated".into());
            }
        }
        if self
            .authority
            .get("optimizer_authority")
            .and_then(Value::as_bool)
            != Some(false)
            || self
                .authority
                .get("synthesis_authority")
                .and_then(Value::as_bool)
                != Some(false)
            || self
                .authority
                .get("scientific_readiness")
                .and_then(Value::as_str)
                != Some("LOCKED_INTERNAL")
        {
            return Err("novelty corpus authority lock is missing".into());
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("novelty corpus serializes"))
    }
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn novelty_corpus() -> Result<&'static NoveltyCorpusV1, String> {
    static CORPUS: LazyLock<Result<NoveltyCorpusV1, String>> = LazyLock::new(|| {
        let value = amphora_core::parse_json_strict(NOVELTY_CORPUS_BYTES)
            .map_err(|error| error.to_string())?;
        let corpus: NoveltyCorpusV1 =
            serde_json::from_value(value).map_err(|error| error.to_string())?;
        corpus.validate()?;
        Ok(corpus)
    });
    CORPUS.as_ref().map_err(Clone::clone)
}

fn role_model_in_domain(
    domain: &Value,
    declared_role: Option<&str>,
    facts: &MoleculeFactsV1,
) -> bool {
    let role_allowed = domain
        .get("allowed_roles")
        .and_then(Value::as_array)
        .is_some_and(|roles| roles.iter().any(|role| role.as_str() == declared_role));
    let molecular_weight_allowed = domain.get("molecular_weight_g_mol").is_none_or(|range| {
        range
            .get("min")
            .and_then(Value::as_f64)
            .is_some_and(|min| facts.average_molecular_weight_g_mol >= min)
            && range
                .get("max")
                .and_then(Value::as_f64)
                .is_some_and(|max| facts.average_molecular_weight_g_mol <= max)
    });
    role_allowed
        && molecular_weight_allowed
        && domain.get("exclude_dual_role").and_then(Value::as_bool) == Some(true)
        && !facts.reactive_flags.dual_role
}

fn role_probability(model: &Value, facts: &MoleculeFactsV1) -> Option<f64> {
    let features = model.get("feature_order")?.as_array()?;
    let coefficients = model.get("coefficients")?.as_array()?;
    let means = model.pointer("/standardization/means")?.as_object()?;
    let scales = model.pointer("/standardization/scales")?.as_object()?;
    if features.len() != coefficients.len() || features.is_empty() {
        return None;
    }
    let mut linear = 0.0;
    for (feature, coefficient) in features.iter().zip(coefficients) {
        let feature = feature.as_str()?;
        let coefficient = coefficient.as_f64()?;
        let raw = match feature {
            "intercept" => 1.0,
            "molecular_weight_g_mol" => facts.average_molecular_weight_g_mol,
            "oxirane_ring_count" => f64::from(facts.oxirane_ring_count),
            "reactive_amine_hydrogen_count" => f64::from(facts.reactive_amine_hydrogen_count),
            "has_oxirane" => {
                if facts.reactive_flags.has_oxirane {
                    1.0
                } else {
                    0.0
                }
            }
            "has_reactive_amine_hydrogen" => {
                if facts.reactive_flags.has_reactive_amine_hydrogen {
                    1.0
                } else {
                    0.0
                }
            }
            _ => return None,
        };
        let standardized = if feature == "intercept" {
            raw
        } else {
            let mean = means.get(feature)?.as_f64()?;
            let scale = scales.get(feature)?.as_f64()?;
            if !scale.is_finite() || scale <= 0.0 {
                return None;
            }
            (raw - mean) / scale
        };
        linear += coefficient * standardized;
    }
    if !linear.is_finite() {
        return None;
    }
    let probability = if linear >= 0.0 {
        1.0 / (1.0 + (-linear).exp())
    } else {
        let exponential = linear.exp();
        exponential / (1.0 + exponential)
    };
    probability.is_finite().then_some(probability)
}

fn novelty_result(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> ModuleResult {
    let mut metrics = base_metrics(candidate);
    if let (Some(facts), Ok(corpus)) = (normalized_facts(features), novelty_corpus()) {
        if let Ok(candidate_fingerprint) = morgan_fingerprint(&facts.canonical_isomeric_smiles) {
            if let Ok(comparison) = compare_novelty_corpus(&candidate_fingerprint, corpus) {
                metrics.extend(BTreeMap::from([
                    (
                        "novelty_status".into(),
                        Value::String("LOCKED_INTERNAL_AUDIT".into()),
                    ),
                    ("corpus_lookup_attempted".into(), Value::Bool(true)),
                    ("rights_cleared_corpus_available".into(), Value::Bool(true)),
                    (
                        "novelty_score".into(),
                        json!(1.0 - comparison.maximum_similarity),
                    ),
                    (
                        "scaffold_aware_distance".into(),
                        json!(1.0 - comparison.maximum_scaffold_similarity),
                    ),
                    (
                        "maximum_tanimoto_similarity".into(),
                        json!(comparison.maximum_similarity),
                    ),
                    (
                        "nearest_structure_id".into(),
                        Value::String(comparison.nearest_structure_id),
                    ),
                    (
                        "exact_structure_match".into(),
                        Value::Bool(comparison.exact_structure_match),
                    ),
                    (
                        "candidate_fingerprint".into(),
                        serde_json::to_value(&candidate_fingerprint)
                            .expect("fingerprint serializes"),
                    ),
                    (
                        "novelty_corpus_sha256".into(),
                        Value::String(corpus.identity_hash()),
                    ),
                    (
                        "novelty_corpus_structure_set_sha256".into(),
                        Value::String(corpus.structure_set_sha256.clone()),
                    ),
                    (
                        "novelty_corpus_rights_sha256".into(),
                        Value::String(corpus.rights_sha256.clone()),
                    ),
                ]));
                return ModuleResult {
                    status: "SCORED".into(),
                    score_0_1: None,
                    objective_values: BTreeMap::new(),
                    metrics,
                    gates: BTreeMap::from([
                        ("corpus_lookup_complete".into(), Value::Bool(true)),
                        (
                            "novelty_constraint_authorized".into(),
                            Value::Bool(true),
                        ),
                        ("optimizer_authority".into(), Value::Bool(false)),
                        ("synthesis_authority".into(), Value::Bool(false)),
                    ]),
                    uncertainty: BTreeMap::from([(
                        "scope".into(),
                        Value::String("Distance is relative only to the frozen Phase-0 control corpus; it is not patent novelty, desirability, synthesis feasibility, or performance.".into()),
                    )]),
                    missing_inputs: Vec::new(),
                    explanations: vec![
                        "The host uses exact-version chiral Morgan radius-2/Tanimoto and Bemis-Murcko scaffold fingerprints as an audit constraint only."
                            .into(),
                    ],
                    source_refs: vec![format!(
                        "{}#{}",
                        corpus.corpus_id,
                        corpus.identity_hash()
                    )],
                    evidence_scope: "MOLECULE_NOVELTY_AUDIT_CONSTRAINT_ONLY".into(),
                };
            }
        }
    }
    metrics.extend([
        ("novelty_status".into(), Value::String("ABSTAINED".into())),
        ("corpus_lookup_attempted".into(), Value::Bool(false)),
        ("rights_cleared_corpus_available".into(), Value::Bool(false)),
    ]);
    let structure_present = structure_text(candidate).is_ok();
    metrics.insert(
        "structure_input_present".into(),
        Value::Bool(structure_present),
    );
    let mut missing_inputs = vec![
        "pinned RDKit C++ 2026.03.2 fingerprint implementation".into(),
        "rights-cleared deduplicated corpus".into(),
        "locked exact-retrieval and top-k recall receipt".into(),
    ];
    if !structure_present {
        missing_inputs.insert(
            0,
            "valid defined single-component molecule structure".into(),
        );
    }

    ModuleResult {
        status: "INSUFFICIENT_INPUT".into(),
        score_0_1: None,
        objective_values: BTreeMap::new(),
        metrics,
        gates: BTreeMap::from([
            ("corpus_lookup_complete".into(), Value::Bool(false)),
            ("novelty_constraint_authorized".into(), Value::Bool(false)),
        ]),
        uncertainty: BTreeMap::from([(
            "scope".into(),
            Value::String("No corpus distance, patentability, desirability, or performance inference.".into()),
        )]),
        missing_inputs,
        explanations: vec![
            "Novelty abstains without a rights-cleared frozen corpus and locked retrieval benchmark."
                .into(),
        ],
        source_refs: Vec::new(),
        evidence_scope: "MOLECULE_NOVELTY_AUDIT_ONLY".into(),
    }
}

struct NoveltyComparison {
    maximum_similarity: f64,
    maximum_scaffold_similarity: f64,
    nearest_structure_id: String,
    exact_structure_match: bool,
}

fn compare_novelty_corpus(
    candidate: &MorganFingerprintV1,
    corpus: &NoveltyCorpusV1,
) -> Result<NoveltyComparison, String> {
    let mut maximum_similarity = -1.0_f64;
    let mut maximum_scaffold_similarity = -1.0_f64;
    let mut nearest_structure_id = String::new();
    let mut exact_structure_match = false;
    for entry in &corpus.entries {
        let reference = morgan_fingerprint(&entry.canonical_isomeric_smiles)
            .map_err(|error| error.to_string())?;
        if reference.canonical_structure_sha256 != entry.canonical_structure_sha256 {
            return Err(format!(
                "novelty corpus structure hash mismatch for {}",
                entry.structure_id
            ));
        }
        let similarity = fingerprint_tanimoto(&candidate.on_bits, &reference.on_bits)
            .ok_or_else(|| "invalid Morgan fingerprint".to_owned())?;
        let scaffold_similarity = if candidate.bemis_murcko_scaffold.is_empty()
            && reference.bemis_murcko_scaffold.is_empty()
        {
            1.0
        } else if candidate.bemis_murcko_scaffold.is_empty()
            || reference.bemis_murcko_scaffold.is_empty()
        {
            0.0
        } else {
            fingerprint_tanimoto(&candidate.scaffold_on_bits, &reference.scaffold_on_bits)
                .ok_or_else(|| "invalid scaffold fingerprint".to_owned())?
        };
        if similarity > maximum_similarity {
            maximum_similarity = similarity;
            nearest_structure_id = entry.structure_id.clone();
        }
        maximum_scaffold_similarity = maximum_scaffold_similarity.max(scaffold_similarity);
        exact_structure_match |=
            candidate.canonical_structure_sha256 == entry.canonical_structure_sha256;
    }
    if !(0.0..=1.0).contains(&maximum_similarity)
        || !(0.0..=1.0).contains(&maximum_scaffold_similarity)
    {
        return Err("novelty comparison produced an invalid similarity".into());
    }
    Ok(NoveltyComparison {
        maximum_similarity,
        maximum_scaffold_similarity,
        nearest_structure_id,
        exact_structure_match,
    })
}

fn property_result(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> ModuleResult {
    let mut metrics = base_metrics(candidate);
    let structure = structure_text(candidate);
    if let Some(facts) = normalized_facts(features) {
        let eew = (facts.oxirane_ring_count > 0)
            .then(|| facts.average_molecular_weight_g_mol / f64::from(facts.oxirane_ring_count));
        let ahew = (facts.reactive_amine_hydrogen_count > 0).then(|| {
            facts.average_molecular_weight_g_mol / f64::from(facts.reactive_amine_hydrogen_count)
        });
        let product_locked = measured_only_product(candidate);
        metrics.extend([
            ("canonical_property_available".into(), Value::Bool(true)),
            (
                "authoritative_property_available".into(),
                Value::Bool(!product_locked),
            ),
            ("pinned_rdkit_available".into(), Value::Bool(true)),
            (
                "property_results".into(),
                json!({
                    "schema": "amphora.molecule-property-results.v1",
                    "canonical_isomeric_smiles": facts.canonical_isomeric_smiles,
                    "structure_identity": facts.structure_identity,
                    "canonical_structure_sha256": facts.canonical_structure_sha256,
                    "formula": facts.formula,
                    "molecular_weight_g_mol": facts.average_molecular_weight_g_mol,
                    "reactive_group_counts": {
                        "oxirane_rings": facts.oxirane_ring_count,
                        "reactive_amine_hydrogens": facts.reactive_amine_hydrogen_count
                    },
                    "eew_g_per_eq": eew,
                    "ahew_g_per_eq": ahew,
                    "functionality": {
                        "epoxide": facts.oxirane_ring_count,
                        "amine_hydrogen": facts.reactive_amine_hydrogen_count
                    },
                    "reactive_flags": facts.reactive_flags,
                    "ontology_version": facts.ontology_version,
                    "toolkit_provenance": facts.toolkit_provenance,
                    "authority_scope": if product_locked { "DEFINED_STRUCTURE_ONLY_NOT_COMMERCIAL_PRODUCT" } else { "DEFINED_SINGLE_COMPONENT_STRUCTURE" },
                    "commercial_product_claim_locked": product_locked
                }),
            ),
        ]);
        return ModuleResult {
            status: "SCORED".into(),
            score_0_1: None,
            objective_values: BTreeMap::new(),
            metrics,
            gates: BTreeMap::from([
                ("authoritative_exact_properties".into(), Value::Bool(!product_locked)),
                ("reactive_ontology_locked".into(), Value::Bool(true)),
                ("defined_single_component".into(), Value::Bool(true)),
            ]),
            uncertainty: BTreeMap::from([(
                "scope".into(),
                Value::String("Deterministic structure facts only; no commercial-grade, safety, synthesis, or coating-performance inference.".into()),
            )]),
            missing_inputs: if product_locked {
                vec!["measured commercial-product EEW/AHEW record".into()]
            } else {
                Vec::new()
            },
            explanations: vec![
                "EEW is molecular weight divided by oxirane count; AHEW is molecular weight divided by ontology-approved reactive amine N-H equivalents."
                    .into(),
            ],
            source_refs: Vec::new(),
            evidence_scope: "DETERMINISTIC_MOLECULE_CONSTRAINT_AND_AUDIT".into(),
        };
    }
    metrics.extend([
        ("canonical_property_available".into(), Value::Bool(false)),
        (
            "authoritative_property_available".into(),
            Value::Bool(false),
        ),
        ("pinned_rdkit_available".into(), Value::Bool(false)),
    ]);
    if let Some(error) = normalization_error(features) {
        metrics.insert("normalization_error".into(), Value::String(error.into()));
    }
    match structure {
        Ok(value) => {
            metrics.insert("structure_input_length".into(), json!(value.len()));
            metrics.insert("obvious_structure_issue".into(), Value::Null);
        }
        Err(issue) => {
            metrics.insert("obvious_structure_issue".into(), issue_value(issue));
        }
    }
    let mut missing_inputs = vec![
        "pinned RDKit C++ 2026.03.2 structure normalization".into(),
        "locked reactive-group ontology".into(),
    ];
    if structure.is_err() {
        missing_inputs.insert(
            0,
            "valid defined single-component molecule structure".into(),
        );
    }

    ModuleResult {
        status: "INSUFFICIENT_INPUT".into(),
        score_0_1: None,
        objective_values: BTreeMap::new(),
        metrics,
        gates: BTreeMap::from([
            ("authoritative_exact_properties".into(), Value::Bool(false)),
            ("reactive_ontology_locked".into(), Value::Bool(false)),
        ]),
        uncertainty: BTreeMap::from([(
            "scope".into(),
            Value::String("Input hashes only; no canonical or authoritative molecular property.".into()),
        )]),
        missing_inputs,
        explanations: vec![
            "Molecule-property evaluation fails closed until the pinned chemistry boundary and locked ontology are available."
                .into(),
        ],
        source_refs: Vec::new(),
        evidence_scope: "MOLECULE_PROPERTY_INPUT_DIAGNOSTIC_ONLY".into(),
    }
}

fn design_gate_result(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> ModuleResult {
    let mut metrics = base_metrics(candidate);
    let structure = structure_text(candidate);
    let role = declared_role(candidate);
    let role_valid = matches!(role, Some("resin" | "hardener"));

    if let Some(facts) = normalized_facts(features) {
        let role_appropriate = match role {
            Some("resin") => facts.oxirane_ring_count > 0,
            Some("hardener") => facts.reactive_amine_hydrogen_count > 0,
            _ => false,
        };
        let passed = role_valid && role_appropriate;
        let reason = if !role_valid {
            "missing_or_unsupported_role"
        } else if !role_appropriate {
            "missing_role_appropriate_reactive_group"
        } else {
            "supported_single_component_with_role_appropriate_reactivity"
        };
        metrics.extend([
            ("gate_reason".into(), Value::String(reason.into())),
            ("pinned_rdkit_available".into(), Value::Bool(true)),
            (
                "locked_reactive_ontology_available".into(),
                Value::Bool(true),
            ),
            (
                "molecule_facts_v1".into(),
                serde_json::to_value(&facts).expect("facts serialize"),
            ),
            ("structural_applicability_only".into(), Value::Bool(true)),
        ]);
        return ModuleResult {
            status: if passed { "SCORED" } else { "FAILED_GATES" }.into(),
            score_0_1: None,
            objective_values: BTreeMap::new(),
            metrics,
            gates: BTreeMap::from([
                ("explicit_role".into(), Value::Bool(role_valid)),
                ("pass_all_hard".into(), Value::Bool(passed)),
                ("role_appropriate_reactivity".into(), Value::Bool(role_appropriate)),
                ("valid_single_component".into(), Value::Bool(true)),
            ]),
            uncertainty: BTreeMap::from([(
                "scope".into(),
                Value::String("Pass establishes structural applicability only, not safety, synthesis feasibility, availability, qualification, or performance.".into()),
            )]),
            missing_inputs: if passed {
                Vec::new()
            } else if !role_valid {
                vec!["molecule.role must be resin or hardener".into()]
            } else {
                vec!["role-appropriate reactive group".into()]
            },
            explanations: vec![
                "The hard gate accepts only a host-normalized single-component structure with an explicit role and matching reactive group."
                    .into(),
            ],
            source_refs: Vec::new(),
            evidence_scope: "MOLECULE_STRUCTURAL_APPLICABILITY_ONLY".into(),
        };
    }

    let reason = match structure {
        Err(issue) => issue_value(issue),
        Ok(_) if !role_valid => Value::String("missing_or_unsupported_role".into()),
        Ok(_) => {
            Value::String("positive_applicability_unavailable_without_rdkit_and_ontology".into())
        }
    };
    metrics.extend([
        ("gate_reason".into(), reason),
        ("pinned_rdkit_available".into(), Value::Bool(false)),
        (
            "locked_reactive_ontology_available".into(),
            Value::Bool(false),
        ),
    ]);
    if let Some(error) = normalization_error(features) {
        metrics.insert("normalization_error".into(), Value::String(error.into()));
    }

    let obvious_structure_valid = structure.is_ok();
    let mut missing_inputs = vec![
        "pinned RDKit C++ 2026.03.2 structure evaluation".into(),
        "locked reactive-group ontology and design-gate receipt".into(),
    ];
    if let Err(issue) = structure {
        missing_inputs.insert(
            0,
            format!(
                "valid defined single-component molecule structure ({})",
                issue_name(issue)
            ),
        );
    }
    if !role_valid {
        missing_inputs.insert(0, "molecule.role must be resin or hardener".into());
    }
    ModuleResult {
        status: "FAILED_GATES".into(),
        score_0_1: None,
        objective_values: BTreeMap::new(),
        metrics,
        gates: BTreeMap::from([
            ("explicit_role".into(), Value::Bool(role_valid)),
            ("pass_all_hard".into(), Value::Bool(false)),
            (
                "role_appropriate_reactivity".into(),
                Value::Bool(false),
            ),
            (
                "valid_single_component".into(),
                Value::Bool(obvious_structure_valid),
            ),
        ]),
        uncertainty: BTreeMap::from([(
            "scope".into(),
            Value::String("Negative lexical checks only; positive chemical applicability is unavailable.".into()),
        )]),
        missing_inputs,
        explanations: vec![
            "The design gate may reject obvious malformed inputs but cannot positively pass applicability without RDKit and the locked ontology."
                .into(),
        ],
        source_refs: Vec::new(),
        evidence_scope: "MOLECULE_STRUCTURAL_REJECTION_ONLY".into(),
    }
}

fn issue_value(issue: ObviousStructureIssue) -> Value {
    Value::String(issue_name(issue).into())
}

fn issue_name(issue: ObviousStructureIssue) -> &'static str {
    match issue {
        ObviousStructureIssue::Missing => "missing_structure",
        ObviousStructureIssue::Empty => "empty_structure",
        ObviousStructureIssue::Fragment => "multi_fragment_structure",
        ObviousStructureIssue::WildcardOrQuery => "wildcard_or_query_structure",
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use amphora_rdkit_ffi::{
        ReactiveFlagsV1, ToolkitProvenanceV1, REACTIVE_ONTOLOGY_VERSION, REQUIRED_RDKIT_VERSION,
    };

    fn candidate(structure: Option<&str>, role: Option<&str>) -> CandidateEnvelope {
        let mut molecule = Map::new();
        if let Some(structure) = structure {
            molecule.insert("smiles".into(), Value::String(structure.into()));
        }
        if let Some(role) = role {
            molecule.insert("role".into(), Value::String(role.into()));
        }
        CandidateEnvelope::from_value(json!({
            "candidate_id": "molecular-test",
            "candidate_type": "molecule",
            "molecule": molecule,
        }))
        .expect("valid molecule candidate envelope")
    }

    fn context() -> ExecutionContext {
        ExecutionContext {
            run_id: "test-run".into(),
            deterministic_seed: 42,
            lineage: Value::Null,
        }
    }

    fn evaluate(module_id: &str, candidate: &CandidateEnvelope) -> ModuleResult {
        evaluate_with_features(module_id, candidate, &FeatureSnapshot::default())
    }

    fn evaluate_with_features(
        module_id: &str,
        candidate: &CandidateEnvelope,
        features: &FeatureSnapshot,
    ) -> ModuleResult {
        capability(module_id)
            .expect("known molecular capability")
            .evaluate(candidate, features, &context())
            .expect("molecular capability evaluates")
    }

    fn facts(
        formula: &str,
        molecular_weight: f64,
        oxirane_count: u32,
        reactive_amine_hydrogens: u32,
    ) -> MoleculeFactsV1 {
        MoleculeFactsV1 {
            schema: "amphora.molecule-facts.v1".into(),
            canonical_isomeric_smiles: "host-canonical".into(),
            structure_identity: "smiles-sha256:test".into(),
            canonical_structure_sha256: "a".repeat(64),
            formula: formula.into(),
            average_molecular_weight_g_mol: molecular_weight,
            oxirane_ring_count: oxirane_count,
            reactive_amine_hydrogen_count: reactive_amine_hydrogens,
            reactive_flags: ReactiveFlagsV1 {
                has_oxirane: oxirane_count > 0,
                has_reactive_amine_hydrogen: reactive_amine_hydrogens > 0,
                dual_role: oxirane_count > 0 && reactive_amine_hydrogens > 0,
            },
            ontology_version: REACTIVE_ONTOLOGY_VERSION.into(),
            toolkit_provenance: ToolkitProvenanceV1 {
                toolkit: "RDKit C++".into(),
                required_version: REQUIRED_RDKIT_VERSION.into(),
                detected_version: REQUIRED_RDKIT_VERSION.into(),
                exact_version_match: true,
            },
        }
    }

    fn facts_features(facts: MoleculeFactsV1) -> FeatureSnapshot {
        FeatureSnapshot {
            values: BTreeMap::from([(
                "molecule_facts_v1".into(),
                serde_json::to_value(facts).unwrap(),
            )]),
        }
    }

    #[test]
    fn every_molecular_capability_is_quarantined_and_objective_empty() {
        let candidate = candidate(Some("C1OC1"), Some("resin"));
        for capability in capabilities() {
            assert!(!capability.descriptor().ranking_eligible);
            let result = capability
                .evaluate(&candidate, &FeatureSnapshot::default(), &context())
                .unwrap();
            assert_eq!(result.score_0_1, None);
            assert!(result.objective_values.is_empty());
            assert_eq!(result.metrics["ranking_quarantine"], Value::Bool(true));
        }
    }

    #[test]
    fn role_ranker_abstains_for_missing_and_wrong_roles() {
        for role in [None, Some("coating")] {
            let result = evaluate(ROLE_RANKER_ID, &candidate(Some("NCCN"), role));
            assert_eq!(result.status, "INSUFFICIENT_INPUT");
            assert_eq!(result.metrics["role_fit_status"], "ABSTAINED");
            assert_eq!(result.gates["explicit_supported_role"], false);
            assert!(result
                .missing_inputs
                .iter()
                .any(|item| item.contains("molecule.role")));
        }
    }

    #[test]
    fn design_gate_rejects_obvious_bad_structures_and_roles() {
        let cases = [
            (None, Some("resin"), "missing_structure"),
            (Some(""), Some("resin"), "empty_structure"),
            (Some("CC.O"), Some("resin"), "multi_fragment_structure"),
            (Some("C*CC"), Some("resin"), "wildcard_or_query_structure"),
            (Some("C~C"), Some("resin"), "wildcard_or_query_structure"),
            (Some("C1OC1"), None, "missing_or_unsupported_role"),
            (
                Some("C1OC1"),
                Some("coating"),
                "missing_or_unsupported_role",
            ),
        ];
        for (structure, role, reason) in cases {
            let result = evaluate(DESIGN_GATE_ID, &candidate(structure, role));
            assert_eq!(result.status, "FAILED_GATES");
            assert_eq!(result.gates["pass_all_hard"], false);
            assert_eq!(result.metrics["gate_reason"], reason);
        }
    }

    #[test]
    fn design_gate_never_positively_passes_without_rdkit_and_ontology() {
        let result = evaluate(DESIGN_GATE_ID, &candidate(Some("C1OC1"), Some("resin")));
        assert_eq!(result.status, "FAILED_GATES");
        assert_eq!(result.gates["valid_single_component"], true);
        assert_eq!(result.gates["pass_all_hard"], false);
        assert_eq!(result.gates["role_appropriate_reactivity"], false);
        assert_eq!(
            result.metrics["gate_reason"],
            "positive_applicability_unavailable_without_rdkit_and_ontology"
        );
    }

    #[test]
    fn property_emits_hash_diagnostics_without_properties() {
        let candidate = candidate(Some("C1OC1"), Some("resin"));
        let result = evaluate(PROPERTY_ID, &candidate);
        assert_eq!(result.status, "INSUFFICIENT_INPUT");
        assert_eq!(result.metrics["canonical_property_available"], false);
        assert_eq!(result.metrics["authoritative_property_available"], false);
        assert_eq!(
            result.metrics["candidate_contract_hash_v1"],
            candidate.contract_hash_v1()
        );
        assert!(result.objective_values.is_empty());
    }

    #[test]
    fn property_publishes_exact_equivalent_weights_under_property_results() {
        let candidate = candidate(Some("C1OC1"), Some("resin"));
        let features = facts_features(facts("C15H16O2", 340.42, 2, 0));
        let result = evaluate_with_features(PROPERTY_ID, &candidate, &features);
        assert_eq!(result.status, "SCORED");
        assert_eq!(
            result.metrics["property_results"]["eew_g_per_eq"],
            json!(170.21)
        );
        assert_eq!(
            result.metrics["property_results"]["ahew_g_per_eq"],
            Value::Null
        );
        assert_eq!(
            result.metrics["property_results"]["ontology_version"],
            REACTIVE_ONTOLOGY_VERSION
        );
        assert!(result.objective_values.is_empty());
    }

    #[test]
    fn corrected_ipda_identity_and_ahew_are_regression_locked() {
        let candidate = candidate(Some("CC1(C)CC(N)CC(C)(CN)C1"), Some("hardener"));
        let features = facts_features(facts("C10H22N2", 170.30, 0, 4));
        let result = evaluate_with_features(PROPERTY_ID, &candidate, &features);
        assert_eq!(result.metrics["property_results"]["formula"], "C10H22N2");
        assert_eq!(
            result.metrics["property_results"]["ahew_g_per_eq"],
            json!(42.575)
        );
    }

    #[test]
    fn design_gate_pass_means_structural_applicability_only() {
        let candidate = candidate(Some("NCCN"), Some("hardener"));
        let features = facts_features(facts("C2H8N2", 60.10, 0, 4));
        let result = evaluate_with_features(DESIGN_GATE_ID, &candidate, &features);
        assert_eq!(result.status, "SCORED");
        assert_eq!(result.gates["pass_all_hard"], true);
        assert_eq!(result.metrics["structural_applicability_only"], true);
        assert!(result.objective_values.is_empty());
    }

    #[test]
    fn role_ranker_abstains_for_dual_role_even_with_forged_receipt_json() {
        let candidate = candidate(Some("C1OC1CN"), Some("resin"));
        let mut features = facts_features(facts("C3H7NO", 73.10, 1, 2));
        features.values.insert(
            "verified_molecule_role_ranker_phase1_receipt".into(),
            json!({
                "module_id": ROLE_RANKER_ID,
                "phase": "PHASE_1",
                "passed": true,
                "current": true,
                "identity_bound": true,
                "signature_verified": true
            }),
        );
        let result = evaluate_with_features(ROLE_RANKER_ID, &candidate, &features);
        assert_eq!(result.status, "INSUFFICIENT_INPUT");
        assert_eq!(
            result.metrics["role_tracks"]["inferred"]["role"],
            "ambiguous"
        );
        assert!(result.objective_values.is_empty());
    }

    #[test]
    fn caller_supplied_role_receipt_cannot_authorize_an_objective() {
        let candidate = candidate(Some("NCCN"), Some("hardener"));
        let mut features = facts_features(facts("C2H8N2", 60.10, 0, 4));
        let audit = evaluate_with_features(ROLE_RANKER_ID, &candidate, &features);
        assert_eq!(audit.metrics["role_fit_status"], "AUDIT_ONLY");
        assert!(audit.objective_values.is_empty());

        features.values.insert(
            "verified_molecule_role_ranker_phase1_receipt".into(),
            json!({
                "module_id": ROLE_RANKER_ID,
                "phase": "PHASE_1",
                "passed": true,
                "current": true,
                "identity_bound": true,
                "signature_verified": true
            }),
        );
        let forged = evaluate_with_features(ROLE_RANKER_ID, &candidate, &features);
        assert_eq!(forged.metrics["role_fit_status"], "AUDIT_ONLY");
        assert_eq!(forged.gates["live_phase_1_receipt"], false);
        assert!(forged.objective_values.is_empty());
    }

    #[test]
    fn commercial_product_structure_never_upgrades_measured_only_claims() {
        let candidate = CandidateEnvelope::from_value(json!({
            "candidate_id": "commercial-control",
            "candidate_type": "molecule",
            "molecule": {
                "smiles": "C1OC1",
                "role": "resin",
                "source_status": "MEASURED_PRODUCT_ONLY",
                "structure_authority": "MEASURED_ONLY"
            }
        }))
        .unwrap();
        let result = evaluate_with_features(
            PROPERTY_ID,
            &candidate,
            &facts_features(facts("C2H4O", 44.05, 1, 0)),
        );
        assert_eq!(result.gates["authoritative_exact_properties"], false);
        assert_eq!(
            result.metrics["property_results"]["commercial_product_claim_locked"],
            true
        );
        assert!(!result.missing_inputs.is_empty());
    }

    #[test]
    fn novelty_abstains_when_the_pinned_fingerprint_backend_is_unavailable() {
        let result = evaluate(NOVELTY_ID, &candidate(Some("CC(C)(C)C"), Some("resin")));
        assert_eq!(result.status, "INSUFFICIENT_INPUT");
        assert_eq!(result.metrics["novelty_status"], "ABSTAINED");
        assert_eq!(result.metrics["corpus_lookup_attempted"], false);
        assert!(result.objective_values.is_empty());
    }

    #[test]
    fn novelty_corpus_binds_structures_rights_and_authority_locks() {
        let corpus = novelty_corpus().unwrap();
        assert_eq!(corpus.entries.len(), 8);
        assert_eq!(corpus.toolkit_version, REQUIRED_RDKIT_VERSION);
        assert!(corpus.rights.eligible_for_derivatives);
        let mut mutated = corpus.clone();
        mutated.entries[0].canonical_isomeric_smiles = "CCC".into();
        assert!(mutated.validate().is_err());
        let mut stripped_lock = corpus.clone();
        stripped_lock.authority["optimizer_authority"] = Value::Bool(true);
        assert!(stripped_lock.validate().is_err());
    }

    #[cfg(feature = "rdkit")]
    #[test]
    fn novelty_exact_match_is_deterministic_audit_only() {
        let candidate = candidate(Some("C1OC1"), Some("resin"));
        let facts = amphora_rdkit_ffi::molecule_facts("C1OC1").unwrap();
        let fingerprint = morgan_fingerprint(&facts.canonical_isomeric_smiles).unwrap();
        compare_novelty_corpus(&fingerprint, novelty_corpus().unwrap()).unwrap();
        let features = facts_features(facts);
        let first = evaluate_with_features(NOVELTY_ID, &candidate, &features);
        let second = evaluate_with_features(NOVELTY_ID, &candidate, &features);
        assert_eq!(first.status, "SCORED");
        assert_eq!(first.metrics["novelty_score"], json!(0.0));
        assert_eq!(first.metrics["exact_structure_match"], true);
        assert_eq!(first.gates["optimizer_authority"], false);
        assert!(first.objective_values.is_empty());
        assert_eq!(
            serde_json::to_vec(&first).unwrap(),
            serde_json::to_vec(&second).unwrap()
        );
    }

    #[test]
    fn generator_emits_lineage_but_no_proposals() {
        let result = evaluate(GENERATOR_ID, &candidate(Some("C1OC1"), Some("resin")));
        assert_eq!(result.status, "INSUFFICIENT_INPUT");
        assert_eq!(result.metrics["proposal_count"], 0);
        assert_eq!(
            result.metrics["lineage_diagnostic"]["parent_candidate_id"],
            "molecular-test"
        );
        assert!(result.objective_values.is_empty());
    }

    #[test]
    fn results_are_byte_deterministic_and_cannot_supply_identity_or_locks() {
        let candidate = candidate(Some("C1OC1"), Some("resin"));
        for capability in capabilities() {
            let first = capability
                .evaluate(&candidate, &FeatureSnapshot::default(), &context())
                .unwrap();
            let second = capability
                .evaluate(&candidate, &FeatureSnapshot::default(), &context())
                .unwrap();
            let first_bytes = serde_json::to_vec(&first).unwrap();
            assert_eq!(first_bytes, serde_json::to_vec(&second).unwrap());

            let value: Value = serde_json::from_slice(&first_bytes).unwrap();
            assert!(value.get("module_id").is_none());
            assert!(value.get("authority_tier").is_none());
            assert!(value.get("claim_locks").is_none());
            assert!(value.get("usable_by_optimizer").is_none());
        }
    }

    #[test]
    fn novelty_abstain_is_byte_deterministic_across_replays() {
        let candidate = candidate(Some("CC(C)(C)C"), Some("resin"));
        let first = evaluate(NOVELTY_ID, &candidate);
        let second = evaluate(NOVELTY_ID, &candidate);
        assert_eq!(first.status, "INSUFFICIENT_INPUT");
        assert_eq!(first.metrics["novelty_status"], "ABSTAINED");
        assert_eq!(
            serde_json::to_vec(&first).unwrap(),
            serde_json::to_vec(&second).unwrap(),
        );
    }

    #[test]
    fn novelty_abstains_on_markush_or_mixture_smiles_input() {
        for candidate_smiles in ["CC.CCO", "[R1]CC[R2]", "CC(*)CC"] {
            let candidate = candidate(Some(candidate_smiles), Some("resin"));
            let result = evaluate(NOVELTY_ID, &candidate);
            assert_eq!(result.status, "INSUFFICIENT_INPUT");
            assert_eq!(result.metrics["novelty_status"], "ABSTAINED");
            assert!(result.objective_values.is_empty());
            assert_eq!(result.gates["novelty_constraint_authorized"], false);
        }
    }

    #[test]
    fn novelty_ignores_candidate_supplied_authority_or_score_fields() {
        let candidate = CandidateEnvelope::from_value(json!({
            "candidate_id": "molecular-test",
            "candidate_type": "molecule",
            "molecule": {
                "smiles": "C1OC1",
                "role": "resin",
                "novelty_score": 0.99,
                "optimizer_authority": true,
                "synthesis_authority": true,
                "patent_novelty": "GRANTED",
            },
        }))
        .expect("valid molecule candidate envelope");
        let result = evaluate(NOVELTY_ID, &candidate);
        assert!(result.objective_values.is_empty());
        assert_eq!(result.gates["novelty_constraint_authorized"], false);
        let bytes = serde_json::to_vec(&result).unwrap();
        let round_trip: Value = serde_json::from_slice(&bytes).unwrap();
        assert!(round_trip.pointer("/metrics/patent_novelty").is_none());
        assert!(!round_trip
            .pointer("/gates/optimizer_authority")
            .and_then(Value::as_bool)
            .unwrap_or(false));
    }

    #[test]
    fn novelty_corpus_rejects_forged_rights_or_stripped_locks() {
        let base = novelty_corpus().unwrap();

        let mut forged_status = base.clone();
        forged_status.rights.status = "REJECTED".into();
        assert!(forged_status.validate().is_err());

        let mut forged_derivatives = base.clone();
        forged_derivatives.rights.eligible_for_derivatives = false;
        assert!(forged_derivatives.validate().is_err());

        let mut stripped_synthesis = base.clone();
        if let Value::Object(ref mut authority) = stripped_synthesis.authority {
            authority.remove("synthesis_authority");
        }
        assert!(stripped_synthesis.validate().is_err());

        let mut stripped_scientific = base.clone();
        if let Value::Object(ref mut authority) = stripped_scientific.authority {
            authority.remove("scientific_readiness");
        }
        assert!(stripped_scientific.validate().is_err());

        let mut wrong_scientific = base.clone();
        if let Value::Object(ref mut authority) = wrong_scientific.authority {
            authority.insert(
                "scientific_readiness".into(),
                Value::String("INDEPENDENTLY_VALIDATED".into()),
            );
        }
        assert!(wrong_scientific.validate().is_err());
    }

    #[test]
    fn novelty_corpus_rejects_stale_content_or_rights_hashes() {
        let base = novelty_corpus().unwrap();

        let mut stale_structure_set = base.clone();
        stale_structure_set.structure_set_sha256 = "0".repeat(64);
        assert!(stale_structure_set.validate().is_err());

        let mut stale_rights_hash = base.clone();
        stale_rights_hash.rights_sha256 = "0".repeat(64);
        assert!(stale_rights_hash.validate().is_err());
    }

    #[test]
    fn novelty_corpus_rejects_toolkit_or_fingerprint_policy_drift() {
        let base = novelty_corpus().unwrap();

        let mut older_toolkit = base.clone();
        older_toolkit.toolkit_version = "2025.09.1".into();
        assert!(older_toolkit.validate().is_err());

        let mut wider_radius = base.clone();
        wider_radius.morgan_radius = 3;
        assert!(wider_radius.validate().is_err());

        let mut smaller_bits = base.clone();
        smaller_bits.fingerprint_bits = 1024;
        assert!(smaller_bits.validate().is_err());

        let mut ignore_chirality = base.clone();
        ignore_chirality.use_chirality = false;
        assert!(ignore_chirality.validate().is_err());
    }

    #[test]
    fn novelty_corpus_rejects_duplicate_or_malformed_entries() {
        let base = novelty_corpus().unwrap();

        let mut empty_entries = base.clone();
        empty_entries.entries.clear();
        assert!(empty_entries.validate().is_err());

        let mut duplicate_ids = base.clone();
        if duplicate_ids.entries.len() >= 2 {
            let first_id = duplicate_ids.entries[0].structure_id.clone();
            duplicate_ids.entries[1].structure_id = first_id;
        }
        assert!(duplicate_ids.validate().is_err());

        let mut bad_hash = base.clone();
        bad_hash.entries[0].canonical_structure_sha256 = "not-a-sha256".into();
        assert!(bad_hash.validate().is_err());
    }

    fn property_result_number(result: &ModuleResult, path: &str) -> Option<f64> {
        result.metrics.get("property_results")?.pointer(path)?.as_f64()
    }

    #[test]
    fn property_exact_implementation_locked_against_dgeba_deta_ipda() {
        let tolerance = 0.5_f64;

        let dgeba_candidate = candidate(
            Some("C(C1=CC=C(OCC2CO2)C=C1)(C)(C)C1=CC=C(OCC2CO2)C=C1"),
            Some("resin"),
        );
        let dgeba = evaluate_with_features(
            PROPERTY_ID,
            &dgeba_candidate,
            &facts_features(facts("C21H24O4", 340.42, 2, 0)),
        );
        assert_eq!(dgeba.status, "SCORED");
        let dgeba_eew = property_result_number(&dgeba, "/eew_g_per_eq").expect("EEW present");
        assert!((dgeba_eew - 170.2).abs() < tolerance, "DGEBA EEW {} outside tolerance", dgeba_eew);
        assert_eq!(
            dgeba.metrics["property_results"]["ahew_g_per_eq"],
            Value::Null
        );

        let deta_candidate = candidate(Some("NCCNCCN"), Some("hardener"));
        let deta = evaluate_with_features(
            PROPERTY_ID,
            &deta_candidate,
            &facts_features(facts("C4H13N3", 103.17, 0, 5)),
        );
        assert_eq!(deta.status, "SCORED");
        let deta_ahew = property_result_number(&deta, "/ahew_g_per_eq").expect("AHEW present");
        assert!((deta_ahew - 20.6).abs() < tolerance, "DETA AHEW {} outside tolerance", deta_ahew);
        assert_eq!(
            deta.metrics["property_results"]["eew_g_per_eq"],
            Value::Null
        );

        let ipda_candidate = candidate(Some("CC1(C)CC(N)CC(C)(CN)C1"), Some("hardener"));
        let ipda = evaluate_with_features(
            PROPERTY_ID,
            &ipda_candidate,
            &facts_features(facts("C10H22N2", 170.30, 0, 4)),
        );
        assert_eq!(ipda.status, "SCORED");
        assert_eq!(ipda.metrics["property_results"]["formula"], "C10H22N2");
        let ipda_ahew = property_result_number(&ipda, "/ahew_g_per_eq").expect("AHEW present");
        assert!((ipda_ahew - 42.6).abs() < tolerance, "IPDA AHEW {} outside tolerance", ipda_ahew);
    }

    #[test]
    fn property_monodisperse_hit_rate_meets_kpi_tolerance() {
        let monodisperse: Vec<(&str, u32, u32, f64, f64)> = vec![
            ("DGEBA-PUBCHEM", 2, 0, 340.42, 170.2),
            ("DGEBA-SUPPLIER", 2, 0, 340.42, 170.2),
            ("DGEBA-ASTM", 2, 0, 340.42, 170.2),
            ("DETA-TITRATION", 0, 5, 103.17, 20.6),
            ("IPDA-SUPPLIER", 0, 4, 170.30, 42.6),
            ("HMDA-PUBCHEM", 0, 4, 116.21, 29.1),
        ];
        let tolerance_g_per_eq = 6.0_f64;
        let mut hit_count = 0_usize;
        let mut total_abs_error = 0.0_f64;
        for (label, oxirane, active_nh, mw, expected) in &monodisperse {
            let features = facts_features(facts("C_H_N_", *mw, *oxirane, *active_nh));
            let smiles = if *oxirane > 0 { "C1OC1" } else { "NCCN" };
            let role = if *oxirane > 0 { "resin" } else { "hardener" };
            let candidate = candidate(Some(smiles), Some(role));
            let result = evaluate_with_features(PROPERTY_ID, &candidate, &features);
            let path = if *oxirane > 0 { "/eew_g_per_eq" } else { "/ahew_g_per_eq" };
            let observed = property_result_number(&result, path)
                .unwrap_or_else(|| panic!("no observation for {label}"));
            let abs_error = (observed - expected).abs();
            total_abs_error += abs_error;
            if abs_error < tolerance_g_per_eq {
                hit_count += 1;
            }
        }
        assert_eq!(
            hit_count,
            monodisperse.len(),
            "monodisperse tolerance hit rate below 1.0"
        );
        let mae = total_abs_error / monodisperse.len() as f64;
        assert!(mae < tolerance_g_per_eq, "monodisperse MAE {mae} exceeds threshold");
    }

    #[test]
    fn property_negative_controls_are_fail_closed_deterministically() {
        let parseable_no_reactive_groups: Vec<(&str, &str, f64)> = vec![
            ("acetamide-N-is-not-active", "CC(=O)N", 59.07),
            ("ethanol-has-no-reactive-groups", "CCO", 46.07),
        ];
        for (label, smiles, mw) in parseable_no_reactive_groups {
            let cand = candidate(Some(smiles), Some("hardener"));
            let features = facts_features(facts("C_H_N_O_", mw, 0, 0));
            let result = evaluate_with_features(PROPERTY_ID, &cand, &features);
            assert_eq!(
                result.metrics["property_results"]["eew_g_per_eq"],
                Value::Null,
                "{label} produced non-null EEW",
            );
            assert_eq!(
                result.metrics["property_results"]["ahew_g_per_eq"],
                Value::Null,
                "{label} produced non-null AHEW",
            );
        }

        for (label, smiles) in [
            ("invalid-smiles", "invalid"),
            ("multi-fragment-mixture", "CC.O"),
            ("polymer-wildcard-repeat", "[*]CC[*]"),
        ] {
            let cand = candidate(Some(smiles), Some("resin"));
            let result = evaluate(PROPERTY_ID, &cand);
            assert_eq!(result.status, "INSUFFICIENT_INPUT", "{label} should abstain");
            assert_eq!(
                result.gates["authoritative_exact_properties"], false,
                "{label} must not authoritatively score",
            );
            assert!(
                result.objective_values.is_empty(),
                "{label} must not emit objectives",
            );
        }
    }

    #[test]
    fn property_technical_grade_lower_bound_locks_commercial_claim() {
        for lower_bound in [180.0_f64, 185.0, 190.0] {
            let candidate = CandidateEnvelope::from_value(json!({
                "candidate_id": format!("technical-dgeba-{}", lower_bound as u32),
                "candidate_type": "molecule",
                "molecule": {
                    "smiles": "C(C1=CC=C(OCC2CO2)C=C1)(C)(C)C1=CC=C(OCC2CO2)C=C1",
                    "role": "resin",
                    "source_status": "MEASURED_PRODUCT_ONLY",
                    "structure_authority": "MEASURED_ONLY"
                }
            }))
            .expect("valid technical-grade candidate");
            let result = evaluate_with_features(
                PROPERTY_ID,
                &candidate,
                &facts_features(facts("C21H24O4", 340.42, 2, 0)),
            );
            assert_eq!(result.gates["authoritative_exact_properties"], false);
            assert_eq!(
                result.metrics["property_results"]["commercial_product_claim_locked"],
                true,
            );
            let defined_eew = property_result_number(&result, "/eew_g_per_eq")
                .expect("defined-structure EEW still emitted for audit");
            assert!(
                defined_eew < lower_bound,
                "defined-structure EEW {defined_eew} must be below supplier lower bound {lower_bound}",
            );
        }
    }

    #[test]
    fn property_zero_functional_group_count_never_divides() {
        let candidate = candidate(Some("CCCC"), Some("hardener"));
        let features = facts_features(facts("C4H10", 58.12, 0, 0));
        let result = evaluate_with_features(PROPERTY_ID, &candidate, &features);
        assert_eq!(result.status, "SCORED");
        assert_eq!(
            result.metrics["property_results"]["eew_g_per_eq"],
            Value::Null
        );
        assert_eq!(
            result.metrics["property_results"]["ahew_g_per_eq"],
            Value::Null
        );
        let bytes = serde_json::to_vec(&result).expect("serializes");
        let text = std::str::from_utf8(&bytes).expect("utf-8");
        assert!(
            !text.contains("NaN") && !text.contains("Infinity") && !text.contains("-Infinity"),
            "output must not contain non-finite tokens",
        );
    }

    #[test]
    fn property_result_is_byte_deterministic_across_replays() {
        let candidate = candidate(Some("CC1(C)CC(N)CC(C)(CN)C1"), Some("hardener"));
        let features = facts_features(facts("C10H22N2", 170.30, 0, 4));
        let first = evaluate_with_features(PROPERTY_ID, &candidate, &features);
        let second = evaluate_with_features(PROPERTY_ID, &candidate, &features);
        assert_eq!(
            serde_json::to_vec(&first).unwrap(),
            serde_json::to_vec(&second).unwrap(),
        );
    }

    #[test]
    fn property_ignores_candidate_supplied_authority_fields() {
        let candidate = CandidateEnvelope::from_value(json!({
            "candidate_id": "property-authority-escalation",
            "candidate_type": "molecule",
            "molecule": {
                "smiles": "NCCN",
                "role": "hardener",
                "eew_g_per_eq": 9999.0,
                "ahew_g_per_eq": 0.001,
                "authoritative_exact_properties": true,
                "commercial_product_claim_locked": false,
            }
        }))
        .expect("valid candidate envelope");
        let features = facts_features(facts("C2H8N2", 60.10, 0, 4));
        let result = evaluate_with_features(PROPERTY_ID, &candidate, &features);
        let observed_ahew = property_result_number(&result, "/ahew_g_per_eq")
            .expect("AHEW present");
        assert!(
            (observed_ahew - 15.025).abs() < 0.05,
            "AHEW {observed_ahew} should be mw/nh, not the candidate-supplied 0.001",
        );
        assert_ne!(
            result.metrics["property_results"]["eew_g_per_eq"],
            json!(9999.0),
        );
    }

    fn role_model_artifact() -> Value {
        json!({
            "schema": "amphora.molecule-role-logistic-regression.v1",
            "feature_order": ["intercept", "molecular_weight_g_mol", "oxirane_ring_count", "reactive_amine_hydrogen_count", "has_oxirane", "has_reactive_amine_hydrogen"],
            "coefficients": [0.0398277, 0.112292, 0.609159, -0.821644, 0.986325, -0.986325],
            "standardization": {
                "means": {"molecular_weight_g_mol": 164.035, "oxirane_ring_count": 0.875, "reactive_amine_hydrogen_count": 2.25, "has_oxirane": 0.5, "has_reactive_amine_hydrogen": 0.5},
                "scales": {"molecular_weight_g_mol": 84.8282, "oxirane_ring_count": 1.09211, "reactive_amine_hydrogen_count": 2.41954, "has_oxirane": 0.5, "has_reactive_amine_hydrogen": 0.5}
            }
        })
    }

    #[test]
    fn role_ranker_out_of_domain_structure_yields_abstained_audit_only() {
        let candidate = candidate(Some("CCCC"), Some("resin"));
        let features = facts_features(facts("C4H10", 58.12, 0, 0));
        let result = evaluate_with_features(ROLE_RANKER_ID, &candidate, &features);
        assert_eq!(result.status, "INSUFFICIENT_INPUT");
        assert_eq!(
            result.metrics["role_fit_status"],
            "ABSTAINED_AMBIGUOUS_OR_OUT_OF_DOMAIN"
        );
        assert_eq!(result.metrics["role_tracks"]["inferred"]["role"], "out_of_domain");
        assert!(result.objective_values.is_empty());
        assert_eq!(result.gates["role_ranking_authorized"], false);
    }

    /// R-N02 regression guard THROUGH THE REAL RDKit FFI: guanidine-class
    /// cure accelerators / latent hardeners (DPG CAS 102-06-7, DOTG CAS
    /// 97-39-2, guanidine CAS 113-00-8, dicyandiamide/DICY CAS 461-58-5,
    /// biguanide CAS 461-71-2 -- the exact probe molecules of the two
    /// 2026-08-03 refuting receipts amine-nh-guanidine-conjugation-gap-v1 and
    /// role-guanidine-accelerator-domain-probe-v1) must derive
    /// reactive_amine_hydrogen_count == 0 from the production bridge and fail
    /// closed to out_of_domain, exactly like the module's prior hostile nulls
    /// (BDMA, EMI-24). Categorical classification only: whether guanidine
    /// N-H is exactly 0 in a quantitative AHEW sense stays explicitly open.
    #[cfg(feature = "rdkit")]
    #[test]
    fn role_ranker_fails_closed_on_guanidine_class_accelerators_via_real_ffi() {
        let guanidine_class = [
            ("dpg-diphenylguanidine-accelerator", "c1ccccc1NC(=N)Nc2ccccc2"),
            (
                "dotg-di-o-tolylguanidine-accelerator",
                "Cc1ccccc1NC(=N)Nc2ccccc2C",
            ),
            ("guanidine", "NC(=N)N"),
            ("dicyandiamide", "NC(=NC#N)N"),
            ("biguanide", "NC(=N)NC(=N)N"),
        ];
        for (id, smiles) in guanidine_class {
            let facts = amphora_rdkit_ffi::molecule_facts(smiles).unwrap();
            assert_eq!(facts.oxirane_ring_count, 0, "{id}");
            assert_eq!(facts.reactive_amine_hydrogen_count, 0, "{id}");
            assert_eq!(inferred_role(&facts), "out_of_domain", "{id}");

            let candidate = candidate(Some(smiles), Some("hardener"));
            let result =
                evaluate_with_features(ROLE_RANKER_ID, &candidate, &facts_features(facts));
            assert_eq!(result.status, "INSUFFICIENT_INPUT", "{id}");
            assert_eq!(
                result.metrics["role_fit_status"],
                "ABSTAINED_AMBIGUOUS_OR_OUT_OF_DOMAIN",
                "{id}"
            );
            assert_eq!(
                result.metrics["role_tracks"]["inferred"]["role"],
                "out_of_domain",
                "{id}"
            );
            assert!(result.objective_values.is_empty(), "{id}");
            assert_eq!(result.gates["role_ranking_authorized"], false, "{id}");
        }
    }

    #[test]
    fn role_ranker_result_is_byte_deterministic_across_replays() {
        let candidate = candidate(Some("NCCN"), Some("hardener"));
        let features = facts_features(facts("C2H8N2", 60.10, 0, 4));
        let first = evaluate_with_features(ROLE_RANKER_ID, &candidate, &features);
        let second = evaluate_with_features(ROLE_RANKER_ID, &candidate, &features);
        assert_eq!(
            serde_json::to_vec(&first).unwrap(),
            serde_json::to_vec(&second).unwrap(),
        );
    }

    #[test]
    fn role_probability_rejects_nan_or_inf_coefficients() {
        let facts = facts("C4H13N3", 103.17, 0, 5);
        let mut malformed = role_model_artifact();
        malformed["coefficients"][1] = json!(f64::NAN);
        assert!(role_probability(&malformed, &facts).is_none());

        let mut infinity = role_model_artifact();
        infinity["coefficients"][0] = json!(f64::INFINITY);
        assert!(role_probability(&infinity, &facts).is_none());
    }

    #[test]
    fn role_probability_rejects_mismatched_feature_and_coefficient_counts() {
        let facts = facts("C4H13N3", 103.17, 0, 5);
        let mut short = role_model_artifact();
        short["coefficients"] = json!([0.1, 0.2, 0.3]);
        assert!(role_probability(&short, &facts).is_none());

        let mut long = role_model_artifact();
        long["coefficients"] = json!([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]);
        assert!(role_probability(&long, &facts).is_none());

        let mut empty = role_model_artifact();
        empty["feature_order"] = json!([]);
        empty["coefficients"] = json!([]);
        assert!(role_probability(&empty, &facts).is_none());
    }

    #[test]
    fn role_probability_rejects_nonpositive_or_missing_scales() {
        let facts = facts("C4H13N3", 103.17, 0, 5);
        let mut zero_scale = role_model_artifact();
        zero_scale["standardization"]["scales"]["molecular_weight_g_mol"] = json!(0.0);
        assert!(role_probability(&zero_scale, &facts).is_none());

        let mut negative_scale = role_model_artifact();
        negative_scale["standardization"]["scales"]["has_oxirane"] = json!(-1.0);
        assert!(role_probability(&negative_scale, &facts).is_none());
    }

    #[test]
    fn role_probability_saturates_correctly_on_pure_resin_and_pure_hardener() {
        let resin_facts = facts("C21H24O4", 340.42, 2, 0);
        let hardener_facts = facts("C4H13N3", 103.17, 0, 5);
        let resin_probability = role_probability(&role_model_artifact(), &resin_facts).unwrap();
        let hardener_probability = role_probability(&role_model_artifact(), &hardener_facts).unwrap();
        assert!(resin_probability > 0.9, "resin probability {resin_probability} should saturate above 0.9");
        assert!(hardener_probability < 0.1, "hardener probability {hardener_probability} should be below 0.1");
    }

    #[test]
    fn role_ranker_ignores_candidate_supplied_role_fit_score() {
        let candidate = CandidateEnvelope::from_value(json!({
            "candidate_id": "role-authority-escalation",
            "candidate_type": "molecule",
            "molecule": {
                "smiles": "NCCN",
                "role": "hardener",
                "role_fit": 0.99,
                "role_ranking_authorized": true,
                "phase1_receipt": {"passed": true, "signature_verified": true}
            }
        }))
        .expect("valid candidate envelope");
        let features = facts_features(facts("C2H8N2", 60.10, 0, 4));
        let result = evaluate_with_features(ROLE_RANKER_ID, &candidate, &features);
        assert!(result.objective_values.is_empty());
        assert_eq!(result.gates["role_ranking_authorized"], false);
        assert_eq!(result.gates["live_phase_1_receipt"], false);
        assert_eq!(result.metrics["role_fit_status"], "AUDIT_ONLY");
    }

    #[test]
    fn role_model_in_domain_rejects_dual_role_or_out_of_range_mw() {
        let domain = json!({
            "allowed_roles": ["resin", "hardener"],
            "molecular_weight_g_mol": {"min": 40.0, "max": 1000.0},
            "exclude_dual_role": true
        });
        // In-domain resin passes.
        let ok = role_model_in_domain(&domain, Some("resin"), &facts("C21H24O4", 340.42, 2, 0));
        assert!(ok);
        // Dual-role molecule rejected even though role/MW are OK.
        let dual = role_model_in_domain(&domain, Some("resin"), &facts("C3H7NO", 73.09, 1, 2));
        assert!(!dual);
        // Out-of-range MW rejected.
        let too_light = role_model_in_domain(&domain, Some("hardener"), &facts("H2O", 18.02, 0, 2));
        assert!(!too_light);
        let too_heavy = role_model_in_domain(&domain, Some("resin"), &facts("Cxxx", 1500.0, 2, 0));
        assert!(!too_heavy);
        // Domain without exclude_dual_role: also rejected (must be true).
        let mut permissive = domain.clone();
        permissive["exclude_dual_role"] = json!(false);
        let permissive_result = role_model_in_domain(&permissive, Some("resin"), &facts("C21H24O4", 340.42, 2, 0));
        assert!(!permissive_result, "role model requires exclude_dual_role=true policy");
    }

    // -------------------------------------------------------------------
    // Phase-0 amphora-molecule-design-gate red-team tests
    // -------------------------------------------------------------------

    #[test]
    fn design_gate_reason_is_specific_when_role_is_missing_or_unsupported() {
        // Case 1: role=None with valid single-component structure → reason names the role failure.
        let no_role = evaluate(DESIGN_GATE_ID, &candidate(Some("C1OC1"), None));
        assert_eq!(no_role.status, "FAILED_GATES");
        assert_eq!(no_role.metrics["gate_reason"], "missing_or_unsupported_role");
        assert_eq!(no_role.gates["explicit_role"], false);
        // Case 2: role="coating" (unsupported) → same reason.
        let unsupp = evaluate(DESIGN_GATE_ID, &candidate(Some("C1OC1"), Some("coating")));
        assert_eq!(unsupp.metrics["gate_reason"], "missing_or_unsupported_role");
        assert_eq!(unsupp.gates["explicit_role"], false);
        // Case 3: role="additive" (also unsupported).
        let additive = evaluate(DESIGN_GATE_ID, &candidate(Some("NCCN"), Some("additive")));
        assert_eq!(additive.metrics["gate_reason"], "missing_or_unsupported_role");
    }

    #[test]
    fn design_gate_reason_is_specific_when_role_appropriate_reactive_group_is_missing() {
        // role=resin declared but no oxirane in facts.
        let candidate_resin = candidate(Some("CCO"), Some("resin"));
        let facts_no_oxirane = facts("C2H6O", 46.07, 0, 0);
        let r = evaluate_with_features(DESIGN_GATE_ID, &candidate_resin, &facts_features(facts_no_oxirane));
        assert_eq!(r.metrics["gate_reason"], "missing_role_appropriate_reactive_group");
        assert_eq!(r.gates["role_appropriate_reactivity"], false);
        assert_eq!(r.gates["pass_all_hard"], false);
        assert_eq!(r.gates["explicit_role"], true);
        // role=hardener declared but no amine hydrogens in facts.
        let candidate_hardener = candidate(Some("CCCC"), Some("hardener"));
        let facts_no_amine_h = facts("C4H10", 58.12, 0, 0);
        let r2 = evaluate_with_features(DESIGN_GATE_ID, &candidate_hardener, &facts_features(facts_no_amine_h));
        assert_eq!(r2.metrics["gate_reason"], "missing_role_appropriate_reactive_group");
        assert_eq!(r2.gates["role_appropriate_reactivity"], false);
    }

    #[test]
    fn design_gate_reason_captures_specific_lexical_issue_categories() {
        // Empty SMILES → "empty_structure".
        let empty = evaluate(DESIGN_GATE_ID, &candidate(Some(""), Some("resin")));
        assert_eq!(empty.metrics["gate_reason"], "empty_structure");
        assert_eq!(empty.gates["valid_single_component"], false);
        assert_eq!(empty.gates["pass_all_hard"], false);
        // Multi-fragment (mixture) → "multi_fragment_structure".
        let mix = evaluate(DESIGN_GATE_ID, &candidate(Some("CC.O"), Some("resin")));
        assert_eq!(mix.metrics["gate_reason"], "multi_fragment_structure");
        assert_eq!(mix.gates["valid_single_component"], false);
        // Wildcard '*' → "wildcard_or_query_structure".
        let star = evaluate(DESIGN_GATE_ID, &candidate(Some("C*CC"), Some("hardener")));
        assert_eq!(star.metrics["gate_reason"], "wildcard_or_query_structure");
        assert_eq!(star.gates["valid_single_component"], false);
        // Wildcard '~' → same category.
        let tilde = evaluate(DESIGN_GATE_ID, &candidate(Some("C~C"), Some("hardener")));
        assert_eq!(tilde.metrics["gate_reason"], "wildcard_or_query_structure");
        // Missing structure entirely → issue name takes precedence over role check
        // per the runtime's match order (Err(issue) branch before Ok if !role_valid).
        let no_structure = evaluate(DESIGN_GATE_ID, &candidate(None, None));
        assert_eq!(no_structure.metrics["gate_reason"], "missing_structure");
    }

    #[test]
    fn design_gate_passes_dual_functional_when_declared_role_has_matching_group() {
        // Glycidyl amine (NCC1CO1) has BOTH oxirane and reactive amine H.
        // Declared as resin → passes because oxirane_ring_count > 0.
        let candidate_resin = candidate(Some("NCC1CO1"), Some("resin"));
        let dual_facts = facts("C3H7NO", 73.09, 1, 2);
        let r_res = evaluate_with_features(DESIGN_GATE_ID, &candidate_resin, &facts_features(dual_facts.clone()));
        assert_eq!(r_res.status, "SCORED");
        assert_eq!(r_res.gates["pass_all_hard"], true);
        assert_eq!(r_res.gates["role_appropriate_reactivity"], true);
        assert_eq!(r_res.metrics["gate_reason"], "supported_single_component_with_role_appropriate_reactivity");
        // Same molecule declared as hardener → also passes because reactive_amine_hydrogen_count > 0.
        let candidate_hardener = candidate(Some("NCC1CO1"), Some("hardener"));
        let r_hard = evaluate_with_features(DESIGN_GATE_ID, &candidate_hardener, &facts_features(dual_facts));
        assert_eq!(r_hard.status, "SCORED");
        assert_eq!(r_hard.gates["pass_all_hard"], true);
    }

    #[test]
    fn design_gate_never_upgrades_authority() {
        // SCORED path (valid resin).
        let resin_cand = candidate(Some("C1OC1"), Some("resin"));
        let resin_facts = facts("C2H4O", 44.05, 1, 0);
        let scored = evaluate_with_features(DESIGN_GATE_ID, &resin_cand, &facts_features(resin_facts));
        assert_eq!(scored.status, "SCORED");
        assert_eq!(scored.evidence_scope, "MOLECULE_STRUCTURAL_APPLICABILITY_ONLY");
        assert_eq!(scored.metrics["structural_applicability_only"], Value::Bool(true));
        assert!(scored.score_0_1.is_none());
        assert!(scored.objective_values.is_empty());
        // FAILED_GATES path (no facts, valid role, valid structure).
        let no_facts = evaluate(DESIGN_GATE_ID, &candidate(Some("C1OC1"), Some("resin")));
        assert_eq!(no_facts.status, "FAILED_GATES");
        assert_eq!(no_facts.evidence_scope, "MOLECULE_STRUCTURAL_REJECTION_ONLY");
        assert!(no_facts.score_0_1.is_none());
        assert!(no_facts.objective_values.is_empty());
        // FAILED_GATES path (malformed structure).
        let malformed = evaluate(DESIGN_GATE_ID, &candidate(Some("C*C"), Some("resin")));
        assert_eq!(malformed.status, "FAILED_GATES");
        assert_eq!(malformed.evidence_scope, "MOLECULE_STRUCTURAL_REJECTION_ONLY");
    }

    #[test]
    fn design_gate_is_byte_deterministic_across_replays() {
        // With facts.
        let cand = candidate(Some("C1OC1"), Some("resin"));
        let f = facts_features(facts("C2H4O", 44.05, 1, 0));
        let first = evaluate_with_features(DESIGN_GATE_ID, &cand, &f);
        let second = evaluate_with_features(DESIGN_GATE_ID, &cand, &f);
        assert_eq!(
            serde_json::to_vec(&first).unwrap(),
            serde_json::to_vec(&second).unwrap(),
        );
        // Without facts (lexical path).
        let no_facts_1 = evaluate(DESIGN_GATE_ID, &candidate(Some("CC.O"), Some("resin")));
        let no_facts_2 = evaluate(DESIGN_GATE_ID, &candidate(Some("CC.O"), Some("resin")));
        assert_eq!(
            serde_json::to_vec(&no_facts_1).unwrap(),
            serde_json::to_vec(&no_facts_2).unwrap(),
        );
    }
}
