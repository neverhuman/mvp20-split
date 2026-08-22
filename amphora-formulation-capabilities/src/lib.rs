#![forbid(unsafe_code)]

use amphora_core::{
    stable_hash, CandidateEnvelope, Capability, CapabilityError, ExecutionContext, FeatureSnapshot,
    ModelArtifactV1, ModuleDescriptor, ModuleResult, VerifiedFormulationModelInputV2,
    VerifiedModelInputV1,
};
use amphora_cure_potlife_gate::{
    BenchmarkReceiptV1 as CureBenchmarkReceiptV1, EvidenceReviewReceiptV1,
};
use serde_json::{json, Map, Value};
use std::collections::{BTreeMap, BTreeSet};

/// A single immutable, time-ordered process observation.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ProcessQcObservationV1 {
    pub batch_id: String,
    pub sequence: u64,
    pub value: f64,
}

/// Baseline and monitoring observations for one QC variable.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ProcessQcSeriesV1 {
    pub variable: String,
    pub baseline: Vec<ProcessQcObservationV1>,
    pub monitoring: Vec<ProcessQcObservationV1>,
    pub specification_lower: Option<f64>,
    pub specification_upper: Option<f64>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
pub struct SpcAuditResultV1 {
    pub variable: String,
    pub baseline_mean: f64,
    pub baseline_sigma: f64,
    pub shewhart_alerts: Vec<String>,
    pub ewma_alerts: Vec<String>,
    pub cusum_alerts: Vec<String>,
    pub specification_failures: Vec<String>,
    pub detector_status: String,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ProcessQcAuditShellV1 {
    pub schema: String,
    pub baseline_observation_count: u64,
    pub stable_monitoring_count: u64,
    pub shifted_monitoring_count: u64,
    pub false_positive_alert_count: u64,
    pub missed_deviation_detector_count: u64,
    pub detector_alert_counts: BTreeMap<String, u64>,
    pub malformed_missingness_rejected: bool,
    pub reordered_time_rejected: bool,
    pub specification_control_separation_passed: bool,
    pub fixture_sha256: String,
    pub authority_ceiling: String,
    pub batch_release_authorized: bool,
    pub manufacturing_qualification_authorized: bool,
}

/// Frozen Individuals/moving-range Shewhart, EWMA (lambda=.2, L=3), and
/// standardized two-sided CUSUM (k=.5, h=5). This function is deliberately
/// independent of specification limits and never emits release authority.
pub fn audit_process_qc(series: &ProcessQcSeriesV1) -> Result<SpcAuditResultV1, String> {
    if series.variable.trim().is_empty() || series.baseline.len() < 20 {
        return Err("at least 20 baseline observations are required".into());
    }
    let valid = |o: &ProcessQcObservationV1| o.value.is_finite() && !o.batch_id.is_empty();
    if series
        .baseline
        .iter()
        .chain(series.monitoring.iter())
        .any(|o| !valid(o))
    {
        return Err("observations must be finite and identified".into());
    }
    if series
        .specification_lower
        .into_iter()
        .chain(series.specification_upper)
        .any(|limit| !limit.is_finite())
        || matches!((series.specification_lower, series.specification_upper), (Some(lower), Some(upper)) if lower > upper)
    {
        return Err("specification limits must be finite and ordered".into());
    }
    if series
        .baseline
        .windows(2)
        .any(|w| w[0].sequence >= w[1].sequence)
        || series
            .monitoring
            .windows(2)
            .any(|w| w[0].sequence >= w[1].sequence)
        || series
            .baseline
            .last()
            .map(|o| {
                o.sequence
                    >= series
                        .monitoring
                        .first()
                        .map(|m| m.sequence)
                        .unwrap_or(u64::MAX)
            })
            .unwrap_or(false)
    {
        return Err("observations must be strictly time ordered".into());
    }
    let mean = series.baseline.iter().map(|o| o.value).sum::<f64>() / series.baseline.len() as f64;
    let var = series
        .baseline
        .iter()
        .map(|o| (o.value - mean).powi(2))
        .sum::<f64>()
        / (series.baseline.len() - 1) as f64;
    let sigma = var.sqrt();
    if !sigma.is_finite() || sigma <= 0.0 {
        return Err("baseline variation must be nonzero".into());
    }
    let upper = mean + 3.0 * sigma;
    let lower = mean - 3.0 * sigma;
    let mut shewhart_alerts = Vec::new();
    let mut ewma_alerts = Vec::new();
    let mut cusum_alerts = Vec::new();
    let mut specification_failures = Vec::new();
    let mut ewma = mean;
    let mut cp = 0.0;
    let mut cm = 0.0;
    for o in &series.monitoring {
        if o.value < lower || o.value > upper {
            shewhart_alerts.push(o.batch_id.clone());
        }
        ewma = 0.2 * o.value + 0.8 * ewma;
        let t = (o.sequence.saturating_sub(series.baseline.len() as u64) + 1) as f64;
        let lim = 3.0 * sigma * (0.2 / 1.8 * (1.0 - 0.8_f64.powf(2.0 * t))).sqrt();
        if (ewma - mean).abs() > lim {
            ewma_alerts.push(o.batch_id.clone());
        }
        let z = (o.value - mean) / sigma;
        cp = (cp + z - 0.5).max(0.0);
        cm = (cm - z - 0.5).max(0.0);
        if cp > 5.0 || cm > 5.0 {
            cusum_alerts.push(o.batch_id.clone());
            cp = 0.0;
            cm = 0.0;
        }
        if series.specification_lower.is_some_and(|v| o.value < v)
            || series.specification_upper.is_some_and(|v| o.value > v)
        {
            specification_failures.push(o.batch_id.clone());
        }
    }
    Ok(SpcAuditResultV1 {
        variable: series.variable.clone(),
        baseline_mean: mean,
        baseline_sigma: sigma,
        shewhart_alerts,
        ewma_alerts,
        cusum_alerts,
        specification_failures,
        detector_status: "AUDIT_ONLY".into(),
    })
}

/// Deterministic owned-fixture audit of the SPC shell. This exercises false
/// positives, a known shift, malformed missingness, time ordering, and the
/// separation between control limits and specification limits. It grants no
/// release or manufacturing authority.
pub fn process_qc_audit_shell() -> Result<ProcessQcAuditShellV1, String> {
    let observation = |prefix: &str, sequence: u64, value: f64| ProcessQcObservationV1 {
        batch_id: format!("{prefix}-{sequence:03}"),
        sequence,
        value,
    };
    let baseline = (1..=30)
        .map(|sequence| {
            let offset = ((sequence - 1) % 5) as f64 - 2.0;
            observation("baseline", sequence, 100.0 + offset * 0.1)
        })
        .collect::<Vec<_>>();
    let stable = (31..=50)
        .map(|sequence| {
            let offset = ((sequence - 31) % 5) as f64 - 2.0;
            observation("stable", sequence, 100.0 + offset * 0.1)
        })
        .collect::<Vec<_>>();
    let shifted = (31..=40)
        .map(|sequence| observation("shifted", sequence, 101.0))
        .collect::<Vec<_>>();
    let fixture = json!({
        "baseline": baseline,
        "stable": stable,
        "shifted": shifted,
        "detectors": {"shewhart_sigma": 3.0, "ewma_lambda": 0.2, "ewma_l": 3.0, "cusum_k": 0.5, "cusum_h": 5.0},
    });
    let baseline: Vec<ProcessQcObservationV1> =
        serde_json::from_value(fixture["baseline"].clone()).map_err(|error| error.to_string())?;
    let stable: Vec<ProcessQcObservationV1> =
        serde_json::from_value(fixture["stable"].clone()).map_err(|error| error.to_string())?;
    let shifted: Vec<ProcessQcObservationV1> =
        serde_json::from_value(fixture["shifted"].clone()).map_err(|error| error.to_string())?;
    let stable_audit = audit_process_qc(&ProcessQcSeriesV1 {
        variable: "owned-stable-fixture".into(),
        baseline: baseline.clone(),
        monitoring: stable,
        specification_lower: Some(99.0),
        specification_upper: Some(101.0),
    })?;
    let shifted_audit = audit_process_qc(&ProcessQcSeriesV1 {
        variable: "owned-shift-fixture".into(),
        baseline: baseline.clone(),
        monitoring: shifted,
        specification_lower: Some(90.0),
        specification_upper: Some(110.0),
    })?;
    let false_positive_alert_count = stable_audit.shewhart_alerts.len()
        + stable_audit.ewma_alerts.len()
        + stable_audit.cusum_alerts.len();
    let detector_alert_counts = BTreeMap::from([
        ("CUSUM".into(), shifted_audit.cusum_alerts.len() as u64),
        ("EWMA".into(), shifted_audit.ewma_alerts.len() as u64),
        (
            "SHEWHART".into(),
            shifted_audit.shewhart_alerts.len() as u64,
        ),
    ]);
    let missed_deviation_detector_count = detector_alert_counts
        .values()
        .filter(|count| **count == 0)
        .count() as u64;
    let malformed_missingness_rejected = audit_process_qc(&ProcessQcSeriesV1 {
        variable: "owned-missingness-fixture".into(),
        baseline: baseline.clone(),
        monitoring: vec![observation("missing", 31, f64::NAN)],
        specification_lower: None,
        specification_upper: None,
    })
    .is_err();
    let mut reordered = baseline.clone();
    reordered.swap(0, 1);
    let reordered_time_rejected = audit_process_qc(&ProcessQcSeriesV1 {
        variable: "owned-reordered-fixture".into(),
        baseline: reordered,
        monitoring: vec![observation("monitor", 31, 100.0)],
        specification_lower: None,
        specification_upper: None,
    })
    .is_err();
    let specification_only = audit_process_qc(&ProcessQcSeriesV1 {
        variable: "owned-specification-fixture".into(),
        baseline,
        monitoring: vec![observation("specification", 31, 100.26)],
        specification_lower: Some(99.75),
        specification_upper: Some(100.25),
    })?;
    let specification_control_separation_passed = specification_only.specification_failures.len()
        == 1
        && specification_only.shewhart_alerts.is_empty()
        && specification_only.ewma_alerts.is_empty()
        && specification_only.cusum_alerts.is_empty();
    if false_positive_alert_count != 0
        || missed_deviation_detector_count != 0
        || !malformed_missingness_rejected
        || !reordered_time_rejected
        || !specification_control_separation_passed
    {
        return Err("deterministic process-QC audit shell failed a mandatory control".into());
    }
    Ok(ProcessQcAuditShellV1 {
        schema: "amphora.process-qc-audit-shell.v1".into(),
        baseline_observation_count: 30,
        stable_monitoring_count: 20,
        shifted_monitoring_count: 10,
        false_positive_alert_count: false_positive_alert_count as u64,
        missed_deviation_detector_count,
        detector_alert_counts,
        malformed_missingness_rejected,
        reordered_time_rejected,
        specification_control_separation_passed,
        fixture_sha256: stable_hash(&fixture),
        authority_ceiling: "AUDIT_ONLY".into(),
        batch_release_authorized: false,
        manufacturing_qualification_authorized: false,
    })
}

pub const INGREDIENT_LIBRARY_ID: &str = "amphora-ingredient-library";
pub const FORMULATION_ARITHMETIC_ID: &str = "amphora-formulation-arithmetic";
pub const ENVELOPE_GATES_ID: &str = "amphora-envelope-gates";
pub const FORMULATION_UNIVERSE_ID: &str = "amphora-formulation-universe";
pub const DESIGN_RULE_SCORE_ID: &str = "amphora-design-rule-score";
pub const PUBLIC_CORROSION_BENCHMARK_ID: &str = "amphora-public-corrosion-benchmark";
pub const CURE_POTLIFE_GATE_ID: &str = "amphora-cure-potlife-gate";
pub const VISCOSITY_SCORE_ID: &str = "amphora-viscosity-score";
pub const BARRIER_CORROSION_SCORE_ID: &str = "amphora-barrier-corrosion-score";
pub const SOLVENCY_SCORE_ID: &str = "amphora-solvency-score";
pub const TOLERANCE_ROBUSTNESS_ID: &str = "amphora-tolerance-robustness";
pub const PROCESS_QC_TWIN_ID: &str = "amphora-process-qc-twin";

pub const EQUIVALENT_BALANCE_SCHEMA: &str = "amphora.equivalent-balance.v1";

/// Structure-derived epoxy/amine equivalent balance.
///
/// This record can only be constructed from host-normalized `MoleculeFactsV1`
/// values. Candidate JSON is deliberately not accepted by this API.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EquivalentBalanceV1 {
    pub schema: String,
    pub resin_facts_sha256: String,
    pub hardener_facts_sha256: String,
    pub resin_structure_sha256: String,
    pub hardener_structure_sha256: String,
    pub eew_g_per_eq: f64,
    pub ahew_g_per_eq: f64,
    pub resin_mass_g: f64,
    pub hardener_mass_g: f64,
    pub epoxide_equivalents: f64,
    pub amine_hydrogen_equivalents: f64,
    pub theoretical_hardener_phr: f64,
    pub equivalent_ratio: f64,
    pub total_mass_g: f64,
    pub unit_provenance: BTreeMap<String, String>,
    pub authority_ceiling: String,
    pub candidate_property_overrides_accepted: bool,
    pub ranking_eligible: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum EquivalentBalanceError {
    #[error("molecule facts are not from the exact pinned RDKit backend")]
    Toolkit,
    #[error("resin molecule has no oxirane equivalents")]
    NoOxirane,
    #[error("hardener molecule has no reactive amine-hydrogen equivalents")]
    NoReactiveAmineHydrogen,
    #[error("mass and equivalent ratio must be finite and positive")]
    InvalidQuantity,
    #[error("molecule facts contain a nonfinite or nonpositive molecular weight")]
    InvalidMolecularWeight,
}

impl EquivalentBalanceV1 {
    pub fn from_host_facts(
        resin: &amphora_rdkit_ffi::MoleculeFactsV1,
        hardener: &amphora_rdkit_ffi::MoleculeFactsV1,
        resin_mass_g: f64,
        equivalent_ratio: f64,
    ) -> Result<Self, EquivalentBalanceError> {
        use amphora_rdkit_ffi::{REACTIVE_ONTOLOGY_VERSION, REQUIRED_RDKIT_VERSION};

        for facts in [resin, hardener] {
            if facts.schema != "amphora.molecule-facts.v1"
                || facts.ontology_version != REACTIVE_ONTOLOGY_VERSION
                || facts.toolkit_provenance.required_version != REQUIRED_RDKIT_VERSION
                || facts.toolkit_provenance.detected_version != REQUIRED_RDKIT_VERSION
                || !facts.toolkit_provenance.exact_version_match
            {
                return Err(EquivalentBalanceError::Toolkit);
            }
            if !facts.average_molecular_weight_g_mol.is_finite()
                || facts.average_molecular_weight_g_mol <= 0.0
            {
                return Err(EquivalentBalanceError::InvalidMolecularWeight);
            }
        }
        if resin.oxirane_ring_count == 0 {
            return Err(EquivalentBalanceError::NoOxirane);
        }
        if hardener.reactive_amine_hydrogen_count == 0 {
            return Err(EquivalentBalanceError::NoReactiveAmineHydrogen);
        }
        if !resin_mass_g.is_finite()
            || resin_mass_g <= 0.0
            || !equivalent_ratio.is_finite()
            || equivalent_ratio <= 0.0
        {
            return Err(EquivalentBalanceError::InvalidQuantity);
        }

        let eew_g_per_eq =
            resin.average_molecular_weight_g_mol / f64::from(resin.oxirane_ring_count);
        let ahew_g_per_eq = hardener.average_molecular_weight_g_mol
            / f64::from(hardener.reactive_amine_hydrogen_count);
        let epoxide_equivalents = resin_mass_g / eew_g_per_eq;
        let amine_hydrogen_equivalents = epoxide_equivalents / equivalent_ratio;
        let hardener_mass_g = amine_hydrogen_equivalents * ahew_g_per_eq;
        let theoretical_hardener_phr = hardener_mass_g * 100.0 / resin_mass_g;
        let total_mass_g = resin_mass_g + hardener_mass_g;
        if [
            eew_g_per_eq,
            ahew_g_per_eq,
            epoxide_equivalents,
            amine_hydrogen_equivalents,
            hardener_mass_g,
            theoretical_hardener_phr,
            total_mass_g,
        ]
        .iter()
        .any(|value| !value.is_finite() || *value <= 0.0)
        {
            return Err(EquivalentBalanceError::InvalidQuantity);
        }

        let resin_value = serde_json::to_value(resin).expect("molecule facts serialize");
        let hardener_value = serde_json::to_value(hardener).expect("molecule facts serialize");
        Ok(Self {
            schema: EQUIVALENT_BALANCE_SCHEMA.into(),
            resin_facts_sha256: stable_hash(&resin_value),
            hardener_facts_sha256: stable_hash(&hardener_value),
            resin_structure_sha256: resin.canonical_structure_sha256.clone(),
            hardener_structure_sha256: hardener.canonical_structure_sha256.clone(),
            eew_g_per_eq,
            ahew_g_per_eq,
            resin_mass_g,
            hardener_mass_g,
            epoxide_equivalents,
            amine_hydrogen_equivalents,
            theoretical_hardener_phr,
            equivalent_ratio,
            total_mass_g,
            unit_provenance: BTreeMap::from([
                ("mass".into(), "g".into()),
                (
                    "molecular_weight".into(),
                    "g/mol from MoleculeFactsV1".into(),
                ),
                ("equivalent_weight".into(), "g/eq structure-derived".into()),
                ("phr".into(), "g hardener per 100 g resin".into()),
            ]),
            authority_ceiling: "AUDIT_ONLY".into(),
            candidate_property_overrides_accepted: false,
            ranking_eligible: false,
        })
    }

    pub fn validate_against(
        &self,
        resin: &amphora_rdkit_ffi::MoleculeFactsV1,
        hardener: &amphora_rdkit_ffi::MoleculeFactsV1,
    ) -> Result<(), EquivalentBalanceError> {
        let expected =
            Self::from_host_facts(resin, hardener, self.resin_mass_g, self.equivalent_ratio)?;
        if self != &expected {
            return Err(EquivalentBalanceError::InvalidQuantity);
        }
        Ok(())
    }
}

pub const HOST_VERIFIED_RECEIPT_FEATURE: &str = "evidence_intake.host_verified_receipt";
pub const HOST_VERIFIED_RECEIPT_SCHEMA: &str = "amphora.host-verified-evidence-receipt.v1";
pub const PROCESS_QC_RECEIPT_SCOPE: &str = "process_qc";
pub const VERIFIED_MODEL_FEATURE_PREFIX: &str = "verified_model_artifact.";

pub const SUPPORTED_MODULE_IDS: [&str; 12] = [
    INGREDIENT_LIBRARY_ID,
    FORMULATION_ARITHMETIC_ID,
    ENVELOPE_GATES_ID,
    FORMULATION_UNIVERSE_ID,
    DESIGN_RULE_SCORE_ID,
    PUBLIC_CORROSION_BENCHMARK_ID,
    CURE_POTLIFE_GATE_ID,
    VISCOSITY_SCORE_ID,
    BARRIER_CORROSION_SCORE_ID,
    SOLVENCY_SCORE_ID,
    TOLERANCE_ROBUSTNESS_ID,
    PROCESS_QC_TWIN_ID,
];

#[derive(Debug, Clone, Copy)]
pub struct FormulationCapability {
    descriptor: &'static ModuleDescriptor,
}

impl FormulationCapability {
    pub fn new(descriptor: &'static ModuleDescriptor) -> Result<Self, CapabilityError> {
        if !Self::supports(&descriptor.project) {
            return Err(CapabilityError::InvalidInput(format!(
                "unsupported formulation capability module ID: {}",
                descriptor.project
            )));
        }
        Ok(Self { descriptor })
    }

    pub fn supports(module_id: &str) -> bool {
        SUPPORTED_MODULE_IDS.contains(&module_id)
    }
}

impl Capability for FormulationCapability {
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
            INGREDIENT_LIBRARY_ID => ingredient_library(candidate),
            FORMULATION_ARITHMETIC_ID => formulation_arithmetic(candidate),
            ENVELOPE_GATES_ID => envelope_gates(candidate),
            FORMULATION_UNIVERSE_ID => formulation_universe(candidate),
            DESIGN_RULE_SCORE_ID => design_rule_score(candidate),
            PUBLIC_CORROSION_BENCHMARK_ID => Ok(public_corrosion_benchmark(candidate, features)),
            CURE_POTLIFE_GATE_ID => Ok(cure_potlife_gate(candidate, features)),
            VISCOSITY_SCORE_ID => Ok(amphora_viscosity_score::evaluate(candidate, features)),
            BARRIER_CORROSION_SCORE_ID => Ok(amphora_barrier_corrosion_score::evaluate(
                candidate, features,
            )),
            SOLVENCY_SCORE_ID => Ok(amphora_solvency_score::evaluate(candidate, features)),
            TOLERANCE_ROBUSTNESS_ID => tolerance_robustness(candidate),
            PROCESS_QC_TWIN_ID => Ok(process_qc_twin(candidate, features)),
            unknown => Err(CapabilityError::InvalidInput(format!(
                "unsupported formulation capability descriptor: {unknown}"
            ))),
        }?;

        debug_assert!(result.objective_values.is_empty());
        debug_assert!(result.score_0_1.is_none());
        Ok(result)
    }
}

fn base_result(candidate: &CandidateEnvelope, status: &str, evidence_scope: &str) -> ModuleResult {
    ModuleResult {
        status: status.into(),
        score_0_1: None,
        objective_values: BTreeMap::new(),
        metrics: BTreeMap::from([
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
        ]),
        gates: BTreeMap::new(),
        uncertainty: BTreeMap::new(),
        missing_inputs: Vec::new(),
        explanations: Vec::new(),
        source_refs: Vec::new(),
        evidence_scope: evidence_scope.into(),
    }
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct FormulationMassDiagnosticV1 {
    pub status: String,
    pub part_a_mass_g: Option<f64>,
    pub part_b_mass_g: Option<f64>,
    pub total_mass_g: Option<f64>,
    pub positive_mass_ingredient_ids: Vec<String>,
    pub ignored_zero_mass_entries: Vec<String>,
    pub ignored_candidate_fields: Vec<String>,
    pub arithmetic_scope: String,
    pub scientific_readiness: String,
    pub objective_values: BTreeMap<String, f64>,
    pub ranking_eligible: bool,
    pub usable_by_optimizer: bool,
    pub candidate_created_evidence: bool,
    pub authority_upgrade: bool,
    pub unresolved_legacy_data_accessed: bool,
}

/// Deterministic mass-only validation shared by runtime execution and Phase-0 diagnostics.
/// Candidate-supplied scientific properties are recorded as ignored and are never evaluated.
pub fn validate_formulation_mass(candidate: &Value) -> Result<FormulationMassDiagnosticV1, String> {
    let ignored_candidate_fields = ignored_formulation_claims(candidate);
    let recipe = match observe_recipe_value(candidate).map_err(|error| error.to_string())? {
        RecipeState::Observed(recipe) => recipe,
        RecipeState::Missing(_) => {
            return Ok(FormulationMassDiagnosticV1 {
                status: "ABSTAIN".into(),
                part_a_mass_g: None,
                part_b_mass_g: None,
                total_mass_g: None,
                positive_mass_ingredient_ids: Vec::new(),
                ignored_zero_mass_entries: Vec::new(),
                ignored_candidate_fields,
                arithmetic_scope: "MASS_ONLY".into(),
                scientific_readiness: "UNVALIDATED".into(),
                objective_values: BTreeMap::new(),
                ranking_eligible: false,
                usable_by_optimizer: false,
                candidate_created_evidence: false,
                authority_upgrade: false,
                unresolved_legacy_data_accessed: false,
            })
        }
    };
    Ok(FormulationMassDiagnosticV1 {
        status: "UNVALIDATED".into(),
        part_a_mass_g: Some(recipe.part_a_mass_g()),
        part_b_mass_g: Some(recipe.part_b_mass_g()),
        total_mass_g: Some(recipe.total_mass_g()),
        positive_mass_ingredient_ids: recipe.ingredient_ids(),
        ignored_zero_mass_entries: recipe.ignored_zero_mass_entries,
        ignored_candidate_fields,
        arithmetic_scope: "MASS_ONLY".into(),
        scientific_readiness: "UNVALIDATED".into(),
        objective_values: BTreeMap::new(),
        ranking_eligible: false,
        usable_by_optimizer: false,
        candidate_created_evidence: false,
        authority_upgrade: false,
        unresolved_legacy_data_accessed: false,
    })
}

fn ignored_formulation_claims(candidate: &Value) -> Vec<String> {
    const IGNORED: [&str; 8] = [
        "density",
        "eew",
        "ahew",
        "nonvolatile",
        "oil_absorption",
        "performance",
        "evidence",
        "feasibility",
    ];
    let mut observed = BTreeSet::new();
    for object in [
        candidate.as_object(),
        candidate.get("formulation").and_then(Value::as_object),
        candidate.get("candidate_claims").and_then(Value::as_object),
        candidate
            .pointer("/context/formulation_universe/claims")
            .and_then(Value::as_object),
    ]
    .into_iter()
    .flatten()
    {
        for field in IGNORED {
            if object.get(field).is_some_and(|value| !value.is_null()) {
                observed.insert(field.to_owned());
            }
        }
    }
    observed.into_iter().collect()
}

pub const MAX_FORMULATION_UNIVERSE_CARDINALITY: u64 = 10_000;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct FormulationUniverseAccountingV1 {
    pub status: String,
    pub axis_cardinalities: BTreeMap<String, usize>,
    pub cartesian_total: Option<u64>,
    pub solved_candidate_count: Option<u64>,
    pub infeasible_candidate_count: Option<u64>,
    pub feasibility_basis: String,
    pub candidate_feasibility_claims_ignored: bool,
    pub scientific_readiness: String,
    pub objective_values: BTreeMap<String, u64>,
    pub ranking_eligible: bool,
    pub usable_by_optimizer: bool,
    pub candidate_created_evidence: bool,
    pub authority_upgrade: bool,
    pub unresolved_legacy_data_accessed: bool,
}

/// Exact declarative Cartesian accounting. "Solved" means only total minus the
/// declared infeasible index set; it never means experimental or optimizer success.
pub fn validate_formulation_universe(
    candidate: &Value,
) -> Result<FormulationUniverseAccountingV1, String> {
    let axes_value = candidate.pointer("/context/formulation_universe/axes");
    let claims_ignored = candidate
        .pointer("/context/formulation_universe/claims")
        .is_some();
    let Some(axes_value) = axes_value else {
        if candidate
            .pointer("/context/formulation_universe/infeasible_indices")
            .is_some()
        {
            return Err("infeasible indices require registered axes".into());
        }
        return Ok(FormulationUniverseAccountingV1 {
            status: "ABSTAIN".into(),
            axis_cardinalities: BTreeMap::new(),
            cartesian_total: None,
            solved_candidate_count: None,
            infeasible_candidate_count: None,
            feasibility_basis: "DECLARATIVE_ACCOUNTING_ONLY".into(),
            candidate_feasibility_claims_ignored: claims_ignored,
            scientific_readiness: "UNVALIDATED".into(),
            objective_values: BTreeMap::new(),
            ranking_eligible: false,
            usable_by_optimizer: false,
            candidate_created_evidence: false,
            authority_upgrade: false,
            unresolved_legacy_data_accessed: false,
        });
    };
    let axes = axes_value
        .as_object()
        .ok_or("formulation universe axes must be an object")?;
    if axes.is_empty() {
        return Err("formulation universe axes must not be empty".into());
    }
    let mut cardinalities = BTreeMap::new();
    let mut total = 1_u64;
    for (axis, values) in axes {
        let values = values
            .as_array()
            .ok_or_else(|| format!("formulation universe axis {axis} must be an array"))?;
        if values.is_empty() {
            return Err(format!(
                "formulation universe axis {axis} must not be empty"
            ));
        }
        let unique: BTreeSet<_> = values.iter().map(stable_hash).collect();
        if unique.len() != values.len() {
            return Err(format!(
                "formulation universe axis {axis} contains canonical duplicates"
            ));
        }
        total = total
            .checked_mul(values.len() as u64)
            .filter(|product| *product <= MAX_FORMULATION_UNIVERSE_CARDINALITY)
            .ok_or("formulation universe cardinality overflow")?;
        cardinalities.insert(axis.clone(), values.len());
    }
    let mut infeasible = BTreeSet::new();
    if let Some(indices) = candidate.pointer("/context/formulation_universe/infeasible_indices") {
        let indices = indices
            .as_array()
            .ok_or("formulation universe infeasible indices must be an array")?;
        for value in indices {
            let index = value
                .as_u64()
                .ok_or("formulation universe infeasible indices must be unsigned integers")?;
            if index >= total || !infeasible.insert(index) {
                return Err(format!(
                    "formulation universe infeasible index {index} is duplicate or out of range"
                ));
            }
        }
    }
    let infeasible_count = infeasible.len() as u64;
    Ok(FormulationUniverseAccountingV1 {
        status: "UNVALIDATED".into(),
        axis_cardinalities: cardinalities,
        cartesian_total: Some(total),
        solved_candidate_count: Some(total - infeasible_count),
        infeasible_candidate_count: Some(infeasible_count),
        feasibility_basis: "DECLARATIVE_ACCOUNTING_ONLY".into(),
        candidate_feasibility_claims_ignored: claims_ignored,
        scientific_readiness: "UNVALIDATED".into(),
        objective_values: BTreeMap::new(),
        ranking_eligible: false,
        usable_by_optimizer: false,
        candidate_created_evidence: false,
        authority_upgrade: false,
        unresolved_legacy_data_accessed: false,
    })
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EnvelopeConstraintV1 {
    pub constraint_id: String,
    pub feature_path: String,
    pub unit: String,
    pub lower_inclusive: f64,
    pub upper_inclusive: f64,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EnvelopePolicyV1 {
    pub schema: String,
    pub policy_id: String,
    pub fixture_only: bool,
    pub authoritative: bool,
    pub constraints: Vec<EnvelopeConstraintV1>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct DimensionedFeatureV1 {
    pub value: f64,
    pub unit: String,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct TrustedArithmeticSnapshotV1 {
    pub schema: String,
    pub trusted: bool,
    pub values: BTreeMap<String, DimensionedFeatureV1>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EnvelopeGateResultV1 {
    pub status: String,
    pub pass_all_hard: bool,
    pub margins: BTreeMap<String, f64>,
    pub fixture_validator_arithmetic_only: bool,
    pub wet_lab_evidence_created: bool,
    pub qualification_evidence_created: bool,
    pub release_evidence_created: bool,
    pub product_evidence_created: bool,
    pub objective_values: BTreeMap<String, f64>,
    pub ranking_eligible: bool,
    pub usable_by_optimizer: bool,
    pub authority_upgrade: bool,
}

/// Evaluates trusted dimensioned features against a trusted policy. Synthetic,
/// explicitly non-authoritative policies are accepted only for locked fixtures.
pub fn evaluate_envelope_policy(
    policy: Option<&EnvelopePolicyV1>,
    snapshot: Option<&TrustedArithmeticSnapshotV1>,
    allow_synthetic_fixture: bool,
) -> Result<EnvelopeGateResultV1, String> {
    let Some(policy) = policy else {
        return Ok(abstaining_envelope_result());
    };
    let Some(snapshot) = snapshot else {
        return Ok(abstaining_envelope_result());
    };
    let policy_trusted = policy.authoritative
        || (allow_synthetic_fixture && policy.fixture_only && !policy.authoritative);
    if policy.schema != "amphora.synthetic-envelope-policy.v1"
        || policy.policy_id.trim().is_empty()
        || !policy_trusted
        || snapshot.schema != "amphora.trusted-arithmetic-snapshot.v1"
        || !snapshot.trusted
    {
        return Ok(abstaining_envelope_result());
    }
    if policy.constraints.is_empty() {
        return Err("envelope policy constraints must not be empty".into());
    }
    let known_features = BTreeSet::from(["mass.part_A_g", "mass.part_B_g", "mass.total_g"]);
    let mut seen = BTreeSet::new();
    let mut margins = BTreeMap::new();
    let mut passed = true;
    for constraint in &policy.constraints {
        if constraint.constraint_id.trim().is_empty()
            || !seen.insert(constraint.constraint_id.as_str())
        {
            return Err("envelope policy contains duplicate constraints".into());
        }
        if !known_features.contains(constraint.feature_path.as_str()) {
            return Err(format!(
                "unknown envelope feature path {}",
                constraint.feature_path
            ));
        }
        if !constraint.lower_inclusive.is_finite()
            || !constraint.upper_inclusive.is_finite()
            || constraint.lower_inclusive > constraint.upper_inclusive
        {
            return Err("envelope policy contains inverted or non-finite bounds".into());
        }
        let feature = snapshot
            .values
            .get(&constraint.feature_path)
            .ok_or_else(|| format!("trusted feature {} is absent", constraint.feature_path))?;
        if !feature.value.is_finite() || feature.unit != constraint.unit {
            return Err(format!(
                "unit mismatch for envelope feature {}",
                constraint.feature_path
            ));
        }
        let margin = (feature.value - constraint.lower_inclusive)
            .min(constraint.upper_inclusive - feature.value);
        passed &= margin >= 0.0;
        margins.insert(constraint.constraint_id.clone(), margin);
    }
    Ok(EnvelopeGateResultV1 {
        status: if passed {
            "UNVALIDATED"
        } else {
            "FAILED_GATES"
        }
        .into(),
        pass_all_hard: passed,
        margins,
        fixture_validator_arithmetic_only: allow_synthetic_fixture,
        wet_lab_evidence_created: false,
        qualification_evidence_created: false,
        release_evidence_created: false,
        product_evidence_created: false,
        objective_values: BTreeMap::new(),
        ranking_eligible: false,
        usable_by_optimizer: false,
        authority_upgrade: false,
    })
}

fn abstaining_envelope_result() -> EnvelopeGateResultV1 {
    EnvelopeGateResultV1 {
        status: "ABSTAIN".into(),
        pass_all_hard: false,
        margins: BTreeMap::new(),
        fixture_validator_arithmetic_only: false,
        wet_lab_evidence_created: false,
        qualification_evidence_created: false,
        release_evidence_created: false,
        product_evidence_created: false,
        objective_values: BTreeMap::new(),
        ranking_eligible: false,
        usable_by_optimizer: false,
        authority_upgrade: false,
    }
}

#[derive(Debug)]
struct RecipeObservation {
    part_a: BTreeMap<String, f64>,
    part_b: BTreeMap<String, f64>,
    ignored_zero_mass_entries: Vec<String>,
}

impl RecipeObservation {
    fn part_a_mass_g(&self) -> f64 {
        self.part_a.values().copied().sum()
    }

    fn part_b_mass_g(&self) -> f64 {
        self.part_b.values().copied().sum()
    }

    fn total_mass_g(&self) -> f64 {
        self.part_a_mass_g() + self.part_b_mass_g()
    }

    fn ingredient_ids(&self) -> Vec<String> {
        self.part_a
            .keys()
            .chain(self.part_b.keys())
            .cloned()
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect()
    }
}

enum RecipeState {
    Observed(RecipeObservation),
    Missing(Vec<String>),
}

fn observe_recipe(candidate: &CandidateEnvelope) -> Result<RecipeState, CapabilityError> {
    observe_recipe_value(candidate.value())
}

fn observe_recipe_value(candidate: &Value) -> Result<RecipeState, CapabilityError> {
    let formulation = candidate
        .get("formulation")
        .and_then(Value::as_object)
        .ok_or_else(|| CapabilityError::InvalidInput("formulation must be an object".into()))?;
    let recipe = match formulation.get("recipe") {
        Some(Value::Object(recipe)) => recipe,
        Some(_) => {
            return Err(CapabilityError::InvalidInput(
                "formulation.recipe must be an object".into(),
            ))
        }
        None => formulation,
    };

    let Some(part_a) = aliased_part(recipe, "part_A", "part_a")? else {
        return Ok(RecipeState::Missing(vec!["formulation.part_A".into()]));
    };
    let Some(part_b) = aliased_part(recipe, "part_B", "part_b")? else {
        return Ok(RecipeState::Missing(vec!["formulation.part_B".into()]));
    };

    let mut ignored_zero_mass_entries = Vec::new();
    let part_a = observe_part(part_a, "part_A", &mut ignored_zero_mass_entries)?;
    let part_b = observe_part(part_b, "part_B", &mut ignored_zero_mass_entries)?;
    let mut missing = Vec::new();
    if part_a.is_empty() {
        missing.push("positive-mass formulation.part_A".into());
    }
    if part_b.is_empty() {
        missing.push("positive-mass formulation.part_B".into());
    }
    if !missing.is_empty() {
        return Ok(RecipeState::Missing(missing));
    }

    let observation = RecipeObservation {
        part_a,
        part_b,
        ignored_zero_mass_entries,
    };
    if !observation.total_mass_g().is_finite() {
        return Err(CapabilityError::InvalidInput(
            "formulation mass sum is not finite".into(),
        ));
    }
    Ok(RecipeState::Observed(observation))
}

fn aliased_part<'a>(
    recipe: &'a Map<String, Value>,
    canonical: &str,
    legacy: &str,
) -> Result<Option<&'a Map<String, Value>>, CapabilityError> {
    if recipe.contains_key(canonical) && recipe.contains_key(legacy) {
        return Err(CapabilityError::InvalidInput(format!(
            "recipe cannot declare both {canonical} and {legacy}"
        )));
    }
    match recipe.get(canonical).or_else(|| recipe.get(legacy)) {
        Some(Value::Object(part)) => Ok(Some(part)),
        Some(_) => Err(CapabilityError::InvalidInput(format!(
            "formulation.{canonical} must be an object"
        ))),
        None => Ok(None),
    }
}

fn observe_part(
    part: &Map<String, Value>,
    part_name: &str,
    ignored_zero_mass_entries: &mut Vec<String>,
) -> Result<BTreeMap<String, f64>, CapabilityError> {
    let mut observed = BTreeMap::new();
    for (ingredient_key, value) in part {
        let mass = ingredient_mass(ingredient_key, value)?;
        if mass < 0.0 {
            return Err(CapabilityError::InvalidInput(format!(
                "negative ingredient mass at {part_name}.{ingredient_key}"
            )));
        }
        if mass == 0.0 {
            ignored_zero_mass_entries.push(format!("{part_name}.{ingredient_key}"));
        } else {
            observed.insert(ingredient_key.clone(), mass);
        }
    }
    Ok(observed)
}

fn ingredient_mass(ingredient_key: &str, value: &Value) -> Result<f64, CapabilityError> {
    let value = if let Some(object) = value.as_object() {
        if let Some(declared_id) = object.get("ingredient_id") {
            if declared_id.as_str() != Some(ingredient_key) {
                return Err(CapabilityError::InvalidInput(format!(
                    "ingredient_id does not match recipe key {ingredient_key}"
                )));
            }
        }
        object.get("mass_g").ok_or_else(|| {
            CapabilityError::InvalidInput(format!(
                "canonical ingredient {ingredient_key} is missing mass_g"
            ))
        })?
    } else {
        value
    };
    value
        .as_f64()
        .filter(|mass| mass.is_finite())
        .ok_or_else(|| {
            CapabilityError::InvalidInput(format!(
                "ingredient mass for {ingredient_key} must be finite numeric"
            ))
        })
}

fn recipe_or_abstain(
    candidate: &CandidateEnvelope,
    evidence_scope: &str,
) -> Result<Result<RecipeObservation, ModuleResult>, CapabilityError> {
    match observe_recipe(candidate)? {
        RecipeState::Observed(recipe) => Ok(Ok(recipe)),
        RecipeState::Missing(missing) => {
            let mut result = base_result(candidate, "INSUFFICIENT_INPUT", evidence_scope);
            result
                .metrics
                .insert("recipe_observation_available".into(), Value::Bool(false));
            result
                .gates
                .insert("required_recipe_present".into(), Value::Bool(false));
            result.missing_inputs = missing;
            result.explanations.push(
                "The diagnostic recipe view requires positive-mass observations in both parts."
                    .into(),
            );
            Ok(Err(result))
        }
    }
}

fn add_recipe_metrics(result: &mut ModuleResult, recipe: &RecipeObservation) {
    result.metrics.extend(BTreeMap::from([
        ("recipe_observation_available".into(), Value::Bool(true)),
        (
            "candidate_normalization_owned_here".into(),
            Value::Bool(false),
        ),
        (
            "positive_mass_ingredient_ids".into(),
            json!(recipe.ingredient_ids()),
        ),
        (
            "positive_mass_ingredient_count".into(),
            json!(recipe.ingredient_ids().len()),
        ),
        (
            "ignored_zero_mass_entries".into(),
            json!(recipe.ignored_zero_mass_entries),
        ),
    ]));
    result
        .gates
        .insert("required_recipe_present".into(), Value::Bool(true));
}

fn ingredient_library(candidate: &CandidateEnvelope) -> Result<ModuleResult, CapabilityError> {
    let recipe = match recipe_or_abstain(candidate, "ingredient_ledger_diagnostic")? {
        Ok(recipe) => recipe,
        Err(result) => return Ok(result),
    };
    let mut result = base_result(
        candidate,
        "INSUFFICIENT_INPUT",
        "ingredient_ledger_diagnostic",
    );
    add_recipe_metrics(&mut result, &recipe);
    result.metrics.extend(BTreeMap::from([
        (
            "ingredient_ledger_lookup_attempted".into(),
            Value::Bool(false),
        ),
        (
            "rights_cleared_ingredient_ledger_available".into(),
            Value::Bool(false),
        ),
        ("active_mass_property_coverage".into(), Value::Null),
    ]));
    result.gates.extend(BTreeMap::from([
        ("all_candidate_ingredients_cited".into(), Value::Bool(false)),
        (
            "active_mass_property_coverage_at_least_95pct".into(),
            Value::Bool(false),
        ),
    ]));
    result.missing_inputs.push(
        "rights-cleared immutable ingredient fact ledger with grade, lot, method, and currentness"
            .into(),
    );
    result.explanations.push(
        "Ingredient IDs are observed deterministically, but the unresolved legacy fact ledger is not queried."
            .into(),
    );
    Ok(result)
}

fn formulation_arithmetic(candidate: &CandidateEnvelope) -> Result<ModuleResult, CapabilityError> {
    let diagnostic =
        validate_formulation_mass(candidate.value()).map_err(CapabilityError::InvalidInput)?;
    if diagnostic.status == "ABSTAIN" {
        let mut result = base_result(
            candidate,
            "INSUFFICIENT_INPUT",
            "formulation_mass_balance_diagnostic",
        );
        result
            .gates
            .insert("required_recipe_present".into(), Value::Bool(false));
        result
            .missing_inputs
            .push("positive-mass observations in both formulation parts".into());
        return Ok(result);
    }
    let mut result = base_result(
        candidate,
        "INSUFFICIENT_INPUT",
        "formulation_mass_balance_diagnostic",
    );
    result.metrics.extend(BTreeMap::from([
        ("recipe_observation_available".into(), Value::Bool(true)),
        (
            "candidate_normalization_owned_here".into(),
            Value::Bool(false),
        ),
        (
            "positive_mass_ingredient_ids".into(),
            json!(diagnostic.positive_mass_ingredient_ids),
        ),
        (
            "positive_mass_ingredient_count".into(),
            json!(diagnostic.positive_mass_ingredient_ids.len()),
        ),
        (
            "ignored_zero_mass_entries".into(),
            json!(diagnostic.ignored_zero_mass_entries),
        ),
        (
            "ignored_candidate_fields".into(),
            json!(diagnostic.ignored_candidate_fields),
        ),
    ]));
    result.metrics.insert(
        "mass_balance".into(),
        json!({
            "part_A": {"value": diagnostic.part_a_mass_g, "unit": "g"},
            "part_B": {"value": diagnostic.part_b_mass_g, "unit": "g"},
            "total": {"value": diagnostic.total_mass_g, "unit": "g"},
            "summation_order": "ingredient_id_lexicographic_within_part",
        }),
    );
    result.metrics.extend(BTreeMap::from([
        ("arithmetic_scope".into(), Value::String("MASS_ONLY".into())),
        (
            "dimensioned_property_arithmetic_available".into(),
            Value::Bool(false),
        ),
    ]));
    result.gates.extend(BTreeMap::from([
        ("mass_balance_computed".into(), Value::Bool(true)),
        (
            "scientific_applicability_established".into(),
            Value::Bool(false),
        ),
    ]));
    result
        .missing_inputs
        .push("rights-cleared density, nonvolatile, EEW, AHEW, and oil-absorption facts".into());
    result.explanations.push(
        "Only dimensioned mass-balance diagnostics are emitted; no scientific objective or applicability is inferred."
            .into(),
    );
    Ok(result)
}

fn envelope_gates(candidate: &CandidateEnvelope) -> Result<ModuleResult, CapabilityError> {
    let recipe = match recipe_or_abstain(candidate, "formulation_envelope_diagnostic")? {
        Ok(recipe) => recipe,
        Err(result) => return Ok(result),
    };
    let mut result = base_result(
        candidate,
        "INSUFFICIENT_INPUT",
        "formulation_envelope_diagnostic",
    );
    let gate =
        evaluate_envelope_policy(None, None, false).map_err(CapabilityError::InvalidInput)?;
    add_recipe_metrics(&mut result, &recipe);
    let dft = declared_dft(candidate);
    result.metrics.insert(
        "declared_dft_mil".into(),
        dft.map_or(Value::Null, |value| json!(value)),
    );
    result.gates.extend(BTreeMap::from([
        ("declared_positive_dft".into(), Value::Bool(dft.is_some())),
        (
            "envelope_evaluated".into(),
            Value::Bool(gate.status != "ABSTAIN"),
        ),
        ("pass_all_hard".into(), Value::Bool(gate.pass_all_hard)),
    ]));
    if dft.is_none() {
        result
            .missing_inputs
            .push("formulation.application.dft_mil".into());
    }
    result
        .missing_inputs
        .push("rights-cleared arithmetic FeatureSnapshot".into());
    result.explanations.push(
        "The declared envelope is not evaluated without trusted dimensioned arithmetic; no 5 mil default is used."
            .into(),
    );
    Ok(result)
}

fn formulation_universe(candidate: &CandidateEnvelope) -> Result<ModuleResult, CapabilityError> {
    let recipe = match recipe_or_abstain(candidate, "formulation_universe_diagnostic")? {
        Ok(recipe) => recipe,
        Err(result) => return Ok(result),
    };
    let accounting =
        validate_formulation_universe(candidate.value()).map_err(CapabilityError::InvalidInput)?;
    let registered = accounting.cartesian_total.is_some();
    let mut result = base_result(
        candidate,
        if registered {
            "SCORED"
        } else {
            "INSUFFICIENT_INPUT"
        },
        "formulation_universe_diagnostic",
    );
    add_recipe_metrics(&mut result, &recipe);
    result.metrics.extend(BTreeMap::from([
        (
            "registered_axis_cardinalities".into(),
            serde_json::to_value(&accounting.axis_cardinalities)
                .expect("axis cardinalities serialize"),
        ),
        (
            "registered_cartesian_total".into(),
            accounting.cartesian_total.map_or(Value::Null, Value::from),
        ),
        (
            "cartesian_total".into(),
            accounting.cartesian_total.map_or(Value::Null, Value::from),
        ),
        (
            "solved_candidate_count".into(),
            accounting
                .solved_candidate_count
                .map_or(Value::Null, Value::from),
        ),
        (
            "infeasible_candidate_count".into(),
            accounting
                .infeasible_candidate_count
                .map_or(Value::Null, Value::from),
        ),
        ("enumeration_attempted".into(), Value::Bool(registered)),
        (
            "feasibility_basis".into(),
            Value::String(accounting.feasibility_basis),
        ),
        (
            "candidate_feasibility_claims_ignored".into(),
            Value::Bool(accounting.candidate_feasibility_claims_ignored),
        ),
    ]));
    result.gates.extend(BTreeMap::from([
        (
            "deterministic_axis_order_registered".into(),
            Value::Bool(registered),
        ),
        (
            "solved_plus_infeasible_equals_total".into(),
            Value::Bool(accounting.cartesian_total.is_some_and(|total| {
                accounting.solved_candidate_count.unwrap_or(0)
                    + accounting.infeasible_candidate_count.unwrap_or(0)
                    == total
            })),
        ),
    ]));
    if !registered {
        result
            .missing_inputs
            .push("context.formulation_universe.axes".into());
    }
    result.explanations.push(
        "Cartesian accounting is deterministic and constraint-only; declared infeasibility does not establish scientific performance."
            .into(),
    );
    Ok(result)
}

fn design_rule_score(candidate: &CandidateEnvelope) -> Result<ModuleResult, CapabilityError> {
    let recipe = match recipe_or_abstain(candidate, "formulation_design_rule_diagnostic")? {
        Ok(recipe) => recipe,
        Err(result) => return Ok(result),
    };
    let mut result = base_result(
        candidate,
        "NO_AUTHORITY",
        "formulation_design_rule_diagnostic",
    );
    add_recipe_metrics(&mut result, &recipe);
    result.metrics.extend(BTreeMap::from([
        ("aggregate_design_rule_score".into(), Value::Null),
        ("candidate_pot_life_prediction_h".into(), Value::Null),
        ("corrosion_rank".into(), Value::Null),
        ("hypothesis_features_evaluated".into(), Value::Bool(false)),
    ]));
    result.gates.insert(
        "individually_validated_design_rules_available".into(),
        Value::Bool(false),
    );
    result
        .missing_inputs
        .push("rights-cleared facts and locked held-family design-rule validation receipts".into());
    result.explanations.push(
        "No aggregate or favorable fallback is emitted from unresolved rule and precedent inputs."
            .into(),
    );
    Ok(result)
}

fn public_corrosion_benchmark(
    candidate: &CandidateEnvelope,
    features: &FeatureSnapshot,
) -> ModuleResult {
    let verified = verified_model_input(features, PUBLIC_CORROSION_BENCHMARK_ID);
    if let Ok(model) = verified {
        let mut result = base_result(
            candidate,
            "NO_AUTHORITY",
            "verified_public_corrosion_benchmark_artifact",
        );
        result.metrics.extend(BTreeMap::from([
            (
                "artifact_rights_status".into(),
                Value::String("ACCEPTED".into()),
            ),
            ("artifact_access_attempted".into(), Value::Bool(true)),
            ("candidate_corrosion_validation".into(), Value::Bool(false)),
            (
                "benchmark_score".into(),
                model
                    .benchmark_metrics
                    .get("balanced_accuracy")
                    .cloned()
                    .unwrap_or(Value::Null),
            ),
            (
                "verified_model_id".into(),
                Value::String(model.model_artifact.model_id.clone()),
            ),
            (
                "verified_model_artifact_sha256".into(),
                Value::String(model.model_artifact_sha256.clone()),
            ),
        ]));
        result.gates.extend(BTreeMap::from([
            (
                "rights_cleared_benchmark_manifest".into(),
                Value::Bool(true),
            ),
            ("verified_model_artifact".into(), Value::Bool(true)),
            ("owned_candidate_evidence".into(), Value::Bool(false)),
            ("promotion_gate_passed".into(), Value::Bool(false)),
        ]));
        result
            .source_refs
            .extend(model.model_artifact.parent_hashes.keys().cloned());
        result.explanations.push(
            "The verified artifact supplies public benchmark diagnostics only; it cannot validate or rank the candidate."
                .into(),
        );
        return result;
    }
    let mut result = base_result(
        candidate,
        "INSUFFICIENT_INPUT",
        "public_corrosion_benchmark_diagnostic",
    );
    result.metrics.extend(BTreeMap::from([
        (
            "artifact_rights_status".into(),
            Value::String("UNRESOLVED".into()),
        ),
        ("artifact_access_attempted".into(), Value::Bool(false)),
        ("candidate_corrosion_validation".into(), Value::Bool(false)),
        ("benchmark_score".into(), Value::Null),
    ]));
    result.gates.extend(BTreeMap::from([
        (
            "rights_cleared_benchmark_manifest".into(),
            Value::Bool(false),
        ),
        ("owned_candidate_evidence".into(), Value::Bool(false)),
        ("promotion_gate_passed".into(), Value::Bool(false)),
        ("verified_model_artifact".into(), Value::Bool(false)),
    ]));
    result
        .missing_inputs
        .push("rights-cleared hash-bound public benchmark and derived-artifact manifest".into());
    result.explanations.push(
        "Unresolved-rights public and derived artifacts are not opened, scored, or applied to the candidate."
            .into(),
    );
    result
}

fn cure_potlife_gate(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> ModuleResult {
    let model = match verified_cure_model_input(features, candidate) {
        Ok(model) => model,
        Err(reason) => {
            let mut result = base_result(candidate, "FAILED_GATES", "cure_potlife_model_card");
            result.metrics.extend(BTreeMap::from([
                ("verdict".into(), Value::String("FAIL".into())),
                ("candidate_pot_life_prediction_h".into(), Value::Null),
                ("candidate_gel_time_prediction_min".into(), Value::Null),
                (
                    "benchmark_artifact_rights_status".into(),
                    Value::String("UNRESOLVED".into()),
                ),
            ]));
            result.gates.extend(BTreeMap::from([
                ("pre_registered_bar_passed".into(), Value::Bool(false)),
                ("week_1_ku_map_required".into(), Value::Bool(true)),
                (
                    "candidate_specific_prediction_available".into(),
                    Value::Bool(false),
                ),
                ("verified_model_artifact".into(), Value::Bool(false)),
            ]));
            result.missing_inputs.push(reason);
            result.explanations.push(
                "The cure model remains failed and cannot emit a candidate-specific gel-time CRO priority diagnostic."
                    .into(),
            );
            return result;
        }
    };
    let conditions = match cure_conditions(candidate) {
        Ok(conditions) => conditions,
        Err(missing) => {
            let mut result =
                base_result(candidate, "INSUFFICIENT_INPUT", "cure_potlife_model_card");
            add_verified_cure_artifact_metrics(&mut result, &model);
            result
                .metrics
                .insert("candidate_pot_life_prediction_h".into(), Value::Null);
            result
                .metrics
                .insert("candidate_gel_time_prediction_min".into(), Value::Null);
            result.gates.insert(
                "candidate_specific_prediction_available".into(),
                Value::Bool(false),
            );
            result
                .gates
                .insert("in_applicability_domain".into(), Value::Bool(false));
            result.missing_inputs = missing;
            result.explanations.push(
                "The verified gel-time model abstains because all measured conditions are required and no defaults are inferred."
                    .into(),
            );
            return result;
        }
    };
    if !cure_conditions_in_domain(&conditions, &model) {
        let mut result = base_result(candidate, "INSUFFICIENT_INPUT", "cure_potlife_model_card");
        add_verified_cure_artifact_metrics(&mut result, &model);
        result
            .metrics
            .insert("candidate_pot_life_prediction_h".into(), Value::Null);
        result
            .metrics
            .insert("candidate_gel_time_prediction_min".into(), Value::Null);
        result.gates.insert(
            "candidate_specific_prediction_available".into(),
            Value::Bool(false),
        );
        result
            .gates
            .insert("in_applicability_domain".into(), Value::Bool(false));
        result.missing_inputs.push(
            "candidate conditions are method-incomparable or outside the verified model applicability domain"
                .into(),
        );
        result
            .explanations
            .push("The verified model abstained out of domain.".into());
        return result;
    }
    let prediction = match evaluate_cure_model(&conditions, &model) {
        Some(prediction) => prediction,
        None => {
            let mut result =
                base_result(candidate, "INSUFFICIENT_INPUT", "cure_potlife_model_card");
            add_verified_cure_artifact_metrics(&mut result, &model);
            result
                .metrics
                .insert("candidate_pot_life_prediction_h".into(), Value::Null);
            result
                .metrics
                .insert("candidate_gel_time_prediction_min".into(), Value::Null);
            result.gates.insert(
                "candidate_specific_prediction_available".into(),
                Value::Bool(false),
            );
            result
                .missing_inputs
                .push("unsupported or non-finite verified model transformation".into());
            return result;
        }
    };
    let mut result = base_result(candidate, "NO_AUTHORITY", "verified_cro_test_priority_gate");
    add_verified_cure_artifact_metrics(&mut result, &model);
    result.metrics.extend(BTreeMap::from([
        (
            "verdict".into(),
            Value::String("CRO_TEST_PRIORITY_ONLY".into()),
        ),
        ("candidate_pot_life_prediction_h".into(), Value::Null),
        (
            "candidate_gel_time_prediction_min".into(),
            json!(prediction),
        ),
        (
            "cro_test_priority".into(),
            Value::String(
                if prediction <= 120.0 {
                    "HIGH"
                } else {
                    "STANDARD"
                }
                .into(),
            ),
        ),
        (
            "benchmark_artifact_rights_status".into(),
            Value::String("ACCEPTED".into()),
        ),
    ]));
    result.gates.extend(BTreeMap::from([
        (
            "pre_registered_bar_passed".into(),
            Value::Bool(model.receipt.passed),
        ),
        ("week_1_ku_map_required".into(), Value::Bool(true)),
        (
            "candidate_specific_prediction_available".into(),
            Value::Bool(true),
        ),
        ("in_applicability_domain".into(), Value::Bool(true)),
        ("verified_model_artifact".into(), Value::Bool(true)),
    ]));
    result.explanations.push(
        "The output prioritizes a measured gel-time CRO test. It is not coating pot life and has no ranking or release authority."
            .into(),
    );
    result
}

fn verified_model_input(
    features: &FeatureSnapshot,
    module_id: &str,
) -> Result<VerifiedModelInputV1, String> {
    let key = format!("{VERIFIED_MODEL_FEATURE_PREFIX}{module_id}");
    let value = features.values.get(&key).ok_or_else(|| {
        format!("missing host-verified model artifact in FeatureSnapshot key {key}")
    })?;
    let model: VerifiedModelInputV1 = serde_json::from_value(value.clone())
        .map_err(|error| format!("invalid verified model artifact: {error}"))?;
    model
        .validate()
        .map_err(|error| format!("invalid verified model binding: {error}"))?;
    if model.module_id != module_id {
        return Err("verified model module identity mismatch".into());
    }
    if !model.rights_eligible {
        return Err("verified model parent rights are blocked".into());
    }
    if !model.method_comparable {
        return Err("verified model methods are incomparable".into());
    }
    Ok(model)
}

struct VerifiedCureModelInput {
    model_artifact_sha256: String,
    model_artifact: ModelArtifactV1,
    receipt: CureBenchmarkReceiptV1,
}

fn verified_cure_model_input(
    features: &FeatureSnapshot,
    candidate: &CandidateEnvelope,
) -> Result<VerifiedCureModelInput, String> {
    let key = format!("{VERIFIED_MODEL_FEATURE_PREFIX}{CURE_POTLIFE_GATE_ID}");
    let value = features.values.get(&key).ok_or_else(|| {
        format!("missing V2 host-verified cure model in FeatureSnapshot key {key}")
    })?;
    let binding: VerifiedFormulationModelInputV2 = serde_json::from_value(value.clone())
        .map_err(|error| format!("invalid V2 cure binding: {error}"))?;
    binding
        .validate_candidate(candidate.candidate_id(), candidate.contract_hash_v1())
        .map_err(|error| format!("invalid V2 cure binding: {error}"))?;
    if binding.module_id != CURE_POTLIFE_GATE_ID {
        return Err("verified cure model module identity mismatch".into());
    }
    let receipt: CureBenchmarkReceiptV1 =
        serde_json::from_value(binding.evaluation_receipt.clone())
            .map_err(|error| format!("invalid cure benchmark receipt: {error}"))?;
    receipt
        .validate()
        .map_err(|error| format!("invalid cure benchmark receipt: {error}"))?;
    let review: EvidenceReviewReceiptV1 =
        serde_json::from_value(binding.independent_review_receipt.clone())
            .map_err(|error| format!("invalid cure review receipt: {error}"))?;
    review
        .validate()
        .map_err(|error| format!("invalid cure review receipt: {error}"))?;
    if !receipt.passed
        || review.model_artifact_sha256 != binding.model_artifact_sha256
        || review.benchmark_receipt_sha256 != binding.evaluation_receipt_sha256
    {
        return Err("cure benchmark or review receipt did not authorize the model".into());
    }
    let model_artifact: ModelArtifactV1 = serde_json::from_value(binding.model_artifact)
        .map_err(|error| format!("invalid cure model artifact: {error}"))?;
    model_artifact
        .validate()
        .map_err(|error| format!("invalid cure model artifact: {error}"))?;
    Ok(VerifiedCureModelInput {
        model_artifact_sha256: binding.model_artifact_sha256,
        model_artifact,
        receipt,
    })
}

struct CureConditions<'a> {
    resin_family: &'a str,
    hardener_family: &'a str,
    mix_ratio_phr: f64,
    temperature_c: f64,
    test_mass_g: f64,
    method: &'a str,
}

fn cure_conditions(candidate: &CandidateEnvelope) -> Result<CureConditions<'_>, Vec<String>> {
    let root = candidate
        .value()
        .pointer("/context/cure_measurement_conditions");
    let mut missing = Vec::new();
    let resin_family = root
        .and_then(|value| value.get("resin_family"))
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty());
    let hardener_family = root
        .and_then(|value| value.get("hardener_family"))
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty());
    let mix_ratio_phr = root
        .and_then(|value| value.get("mix_ratio_phr"))
        .and_then(Value::as_f64)
        .filter(|value| value.is_finite() && *value > 0.0);
    let temperature_c = root
        .and_then(|value| value.get("temperature_C"))
        .and_then(Value::as_f64)
        .filter(|value| value.is_finite());
    let test_mass_g = root
        .and_then(|value| value.get("test_mass_g"))
        .and_then(Value::as_f64)
        .filter(|value| value.is_finite() && *value > 0.0);
    let method = root
        .and_then(|value| value.get("method"))
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty());
    for (name, absent) in [
        ("resin_family", resin_family.is_none()),
        ("hardener_family", hardener_family.is_none()),
        ("mix_ratio_phr", mix_ratio_phr.is_none()),
        ("temperature_C", temperature_c.is_none()),
        ("test_mass_g", test_mass_g.is_none()),
        ("method", method.is_none()),
    ] {
        if absent {
            missing.push(format!("context.cure_measurement_conditions.{name}"));
        }
    }
    if !missing.is_empty() {
        return Err(missing);
    }
    Ok(CureConditions {
        resin_family: resin_family.expect("checked"),
        hardener_family: hardener_family.expect("checked"),
        mix_ratio_phr: mix_ratio_phr.expect("checked"),
        temperature_c: temperature_c.expect("checked"),
        test_mass_g: test_mass_g.expect("checked"),
        method: method.expect("checked"),
    })
}

fn cure_conditions_in_domain(
    conditions: &CureConditions<'_>,
    model: &VerifiedCureModelInput,
) -> bool {
    let domain = &model.model_artifact.applicability_domain;
    domain.get("endpoint").and_then(Value::as_str) == Some("GEL_TIME")
        && domain_array_contains(domain, "resin_families", conditions.resin_family)
        && domain_array_contains(domain, "hardener_families", conditions.hardener_family)
        && domain_array_contains(domain, "methods", conditions.method)
        && domain_range_contains(domain, "mix_ratio_phr", conditions.mix_ratio_phr)
        && domain_range_contains(domain, "temperature_C", conditions.temperature_c)
        && domain_range_contains(domain, "test_mass_g", conditions.test_mass_g)
}

fn domain_array_contains(domain: &Value, key: &str, expected: &str) -> bool {
    domain
        .get(key)
        .and_then(Value::as_array)
        .is_some_and(|values| values.iter().any(|value| value.as_str() == Some(expected)))
}

fn domain_range_contains(domain: &Value, key: &str, expected: f64) -> bool {
    domain.get(key).is_some_and(|range| {
        range
            .get("min")
            .and_then(Value::as_f64)
            .is_some_and(|min| expected >= min)
            && range
                .get("max")
                .and_then(Value::as_f64)
                .is_some_and(|max| expected <= max)
    })
}

fn evaluate_cure_model(
    conditions: &CureConditions<'_>,
    model: &VerifiedCureModelInput,
) -> Option<f64> {
    let mut linear = 0.0;
    for (feature, coefficient) in model
        .model_artifact
        .feature_order
        .iter()
        .zip(&model.model_artifact.coefficients)
    {
        let value = match feature.as_str() {
            "intercept" => 1.0,
            "mix_ratio_phr" => conditions.mix_ratio_phr,
            "temperature_C" => conditions.temperature_c,
            "test_mass_g" => conditions.test_mass_g,
            _ => return None,
        };
        linear += value * coefficient;
    }
    let prediction = if model
        .model_artifact
        .transformations
        .iter()
        .any(|transform| transform == "EXP_OUTPUT_MIN")
    {
        linear.exp()
    } else {
        linear
    };
    (prediction.is_finite() && prediction > 0.0).then_some(prediction)
}

fn add_verified_cure_artifact_metrics(result: &mut ModuleResult, model: &VerifiedCureModelInput) {
    result.metrics.extend(BTreeMap::from([
        (
            "verified_model_id".into(),
            Value::String(model.model_artifact.model_id.clone()),
        ),
        (
            "verified_model_artifact_sha256".into(),
            Value::String(model.model_artifact_sha256.clone()),
        ),
        (
            "benchmark_artifact_rights_status".into(),
            Value::String("ACCEPTED".into()),
        ),
    ]));
    result
        .gates
        .insert("verified_model_artifact".into(), Value::Bool(true));
    result
        .source_refs
        .extend(model.model_artifact.parent_hashes.keys().cloned());
}

fn tolerance_robustness(candidate: &CandidateEnvelope) -> Result<ModuleResult, CapabilityError> {
    let recipe = match recipe_or_abstain(candidate, "formulation_robustness_diagnostic")? {
        Ok(recipe) => recipe,
        Err(result) => return Ok(result),
    };
    let dft = declared_dft(candidate);
    let mut result = base_result(
        candidate,
        "INSUFFICIENT_INPUT",
        "formulation_robustness_diagnostic",
    );
    add_recipe_metrics(&mut result, &recipe);
    result.metrics.extend(BTreeMap::from([
        (
            "declared_dft_mil".into(),
            dft.map_or(Value::Null, |value| json!(value)),
        ),
        ("simulation_run".into(), Value::Bool(false)),
        ("robust".into(), Value::Null),
        (
            "perturbation_distribution_status".into(),
            Value::String("EMPIRICAL_COVARIANCE_REQUIRED".into()),
        ),
    ]));
    result.gates.extend(BTreeMap::from([
        ("declared_positive_dft".into(), Value::Bool(dft.is_some())),
        (
            "empirical_uncertainty_calibrated".into(),
            Value::Bool(false),
        ),
        ("promotion_gate_passed".into(), Value::Bool(false)),
    ]));
    if dft.is_none() {
        result
            .missing_inputs
            .push("formulation.application.dft_mil".into());
    }
    result
        .missing_inputs
        .push("CoA- and lot-derived joint uncertainty distribution and covariance".into());
    result.explanations.push(
        "The arbitrary independent legacy bands are not executed or treated as experimental evidence."
            .into(),
    );
    Ok(result)
}

fn process_qc_twin(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> ModuleResult {
    let process_qc = candidate.value().pointer("/evidence_refs/process_qc");
    let package_sha256 = process_qc.map(stable_hash);
    let host_verified = package_sha256
        .as_deref()
        .is_some_and(|hash| process_qc_receipt_valid(candidate, features, hash));
    let candidate_release_assertion_present = process_qc.is_some_and(|value| {
        value.get("release_status").is_some()
            || value.get("accepted_evidence_package_id").is_some()
            || value.get("accepted").is_some()
            || value.get("evidence_package_valid").is_some()
    });

    let mut result = base_result(
        candidate,
        if host_verified {
            "NO_AUTHORITY"
        } else {
            "FAILED_GATES"
        },
        "process_qc_batch_evidence",
    );
    result.metrics.extend(BTreeMap::from([
        (
            "candidate_release_assertion_present".into(),
            Value::Bool(candidate_release_assertion_present),
        ),
        (
            "candidate_release_assertion_trusted".into(),
            Value::Bool(false),
        ),
        (
            "host_verified_process_qc_receipt".into(),
            Value::Bool(host_verified),
        ),
        ("detector_status".into(), Value::String("NOT_PROVEN".into())),
    ]));
    if let Some(package_sha256) = package_sha256 {
        result.metrics.insert(
            "process_qc_payload_sha256".into(),
            Value::String(package_sha256),
        );
    }
    if host_verified {
        if let Some(series) = process_qc.and_then(|payload| payload.get("series")) {
            match serde_json::from_value::<Vec<ProcessQcSeriesV1>>(series.clone())
                .map_err(|error| format!("invalid process-QC series contract: {error}"))
                .and_then(|series| {
                    if series.is_empty() {
                        return Err("process-QC series list is empty".into());
                    }
                    series
                        .iter()
                        .map(audit_process_qc)
                        .collect::<Result<Vec<_>, _>>()
                }) {
                Ok(audits) => {
                    let control_alert_count = audits
                        .iter()
                        .map(|audit| {
                            audit.shewhart_alerts.len()
                                + audit.ewma_alerts.len()
                                + audit.cusum_alerts.len()
                        })
                        .sum::<usize>();
                    let specification_failure_count = audits
                        .iter()
                        .map(|audit| audit.specification_failures.len())
                        .sum::<usize>();
                    result.metrics.insert(
                        "spc_audits".into(),
                        serde_json::to_value(&audits).expect("SPC audit result serializes"),
                    );
                    result.metrics.insert(
                        "control_chart_alert_count".into(),
                        json!(control_alert_count),
                    );
                    result.metrics.insert(
                        "specification_failure_count".into(),
                        json!(specification_failure_count),
                    );
                    result
                        .metrics
                        .insert("detector_status".into(), Value::String("AUDIT_ONLY".into()));
                    result.explanations.push(
                        "Shewhart, EWMA, and CUSUM alerts are diagnostic. Specification failures are reported separately; neither authorizes release."
                            .into(),
                    );
                }
                Err(error) => {
                    result.status = "FAILED_GATES".into();
                    result.metrics.insert(
                        "detector_status".into(),
                        Value::String("INVALID_INPUT".into()),
                    );
                    result
                        .missing_inputs
                        .push(format!("valid time-ordered process-QC series: {error}"));
                }
            }
        }
    }
    result.gates.extend(BTreeMap::from([
        (
            "host_verified_signature_receipt".into(),
            Value::Bool(host_verified),
        ),
        (
            "candidate_supplied_release_authority".into(),
            Value::Bool(false),
        ),
        (
            "prospective_30_batch_pilot_passed".into(),
            Value::Bool(false),
        ),
        ("batch_release_authority".into(), Value::Bool(false)),
    ]));
    if process_qc.is_none() {
        result
            .missing_inputs
            .push("evidence_refs.process_qc".into());
    }
    if !host_verified {
        result.missing_inputs.push(format!(
            "candidate- and payload-bound host receipt in FeatureSnapshot key {HOST_VERIFIED_RECEIPT_FEATURE}"
        ));
    }
    result.missing_inputs.push(
        "30 prospective batches meeting recall, false-alarm, and zero-false-release bars".into(),
    );
    result.explanations.push(
        "Candidate-supplied acceptance and release assertions are ignored; only a host-verified receipt can admit QC evidence for diagnostics."
            .into(),
    );
    result
}

fn process_qc_receipt_valid(
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

    receipt.get("schema").and_then(Value::as_str) == Some(HOST_VERIFIED_RECEIPT_SCHEMA)
        && receipt.get("evidence_scope").and_then(Value::as_str) == Some(PROCESS_QC_RECEIPT_SCOPE)
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

fn declared_dft(candidate: &CandidateEnvelope) -> Option<f64> {
    numeric_pointer(candidate, "/formulation/application/dft_mil")
        .or_else(|| numeric_pointer(candidate, "/context/dft_basis_mil"))
        .filter(|value| *value > 0.0)
}

fn numeric_pointer(candidate: &CandidateEnvelope, pointer: &str) -> Option<f64> {
    candidate
        .value()
        .pointer(pointer)
        .and_then(Value::as_f64)
        .filter(|value| value.is_finite())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn descriptor(module_id: &str) -> &'static ModuleDescriptor {
        Box::leak(Box::new(ModuleDescriptor {
            project: module_id.into(),
            authority_ceiling: "LIMITED_SANITY".into(),
            solver_use_ceiling: "DISABLED".into(),
            model_readiness_ceiling: "NOT_PROVEN".into(),
            ranking_eligible: false,
            candidate_types: vec!["formulation".into()],
            non_blocking_claim_locks: vec!["test_lock".into()],
            readiness: "PRE_PHASE_0".into(),
        }))
    }

    fn candidate(extra_formulation: Value, evidence_refs: Value) -> CandidateEnvelope {
        CandidateEnvelope::from_value(json!({
            "candidate_id": "formulation-test",
            "candidate_type": "formulation",
            "formulation": extra_formulation,
            "evidence_refs": evidence_refs,
        }))
        .expect("valid formulation candidate")
    }

    fn basic_candidate() -> CandidateEnvelope {
        candidate(
            json!({
                "part_A": {"resin": 100.0, "pigment": 10.0},
                "part_B": {"hardener": 40.0},
                "application": {"dft_mil": 5.0, "temperature_C": 25.0},
                "process": {"application_method": "airless_spray", "pot_age_h": 0.0},
            }),
            json!({}),
        )
    }

    fn context() -> ExecutionContext {
        ExecutionContext {
            run_id: "test-run".into(),
            deterministic_seed: 42,
            lineage: Value::Null,
        }
    }

    fn evaluate(
        module_id: &str,
        candidate: &CandidateEnvelope,
        features: &FeatureSnapshot,
    ) -> ModuleResult {
        FormulationCapability::new(descriptor(module_id))
            .expect("supported capability")
            .evaluate(candidate, features, &context())
            .expect("capability evaluates")
    }

    fn verified_model_features(module_id: &str) -> FeatureSnapshot {
        let artifact = amphora_core::ModelArtifactV1 {
            schema: amphora_core::MODEL_ARTIFACT_SCHEMA.into(),
            model_id: format!("{module_id}.test-model"),
            feature_order: vec!["intercept".into(), "mix_ratio_phr".into()],
            transformations: Vec::new(),
            coefficients: vec![30.0, 1.0],
            calibration: BTreeMap::new(),
            applicability_domain: json!({
                "endpoint": "GEL_TIME",
                "resin_families": ["DGEBA"],
                "hardener_families": ["POLYAMIDE"],
                "methods": ["ASTM_D2471"],
                "mix_ratio_phr": {"min": 30.0, "max": 80.0},
                "temperature_C": {"min": 20.0, "max": 30.0},
                "test_mass_g": {"min": 50.0, "max": 150.0}
            }),
            parent_hashes: BTreeMap::from([("dataset".into(), "a".repeat(64))]),
        };
        let artifact_sha256 = stable_hash(&serde_json::to_value(&artifact).unwrap());
        FeatureSnapshot {
            values: BTreeMap::from([(
                format!("{VERIFIED_MODEL_FEATURE_PREFIX}{module_id}"),
                serde_json::to_value(VerifiedModelInputV1 {
                    schema: amphora_core::VERIFIED_MODEL_INPUT_SCHEMA.into(),
                    module_id: module_id.into(),
                    accepted: true,
                    signature_verified: true,
                    artifact_hash_verified: true,
                    rights_eligible: true,
                    method_comparable: true,
                    model_artifact_sha256: artifact_sha256,
                    model_artifact: artifact,
                    benchmark_metrics: BTreeMap::from([
                        ("balanced_accuracy".into(), json!(0.81)),
                        ("phase_1_gates_passed".into(), Value::Bool(true)),
                    ]),
                })
                .unwrap(),
            )]),
        }
    }

    #[test]
    fn supports_exactly_the_twelve_audited_modules() {
        assert_eq!(SUPPORTED_MODULE_IDS.len(), 12);
        for module_id in SUPPORTED_MODULE_IDS {
            assert!(FormulationCapability::supports(module_id));
        }
        assert!(!FormulationCapability::supports(
            "amphora-molecule-property"
        ));
    }

    #[test]
    fn every_result_is_objective_empty_and_quarantined() {
        let candidate = basic_candidate();
        for module_id in SUPPORTED_MODULE_IDS {
            let result = evaluate(module_id, &candidate, &FeatureSnapshot::default());
            assert!(result.objective_values.is_empty());
            assert_eq!(result.score_0_1, None);
            assert_eq!(result.metrics["ranking_quarantine"], true);
            assert_eq!(result.metrics["scientific_applicability"], "UNVALIDATED");
        }
    }

    #[test]
    fn zero_mass_entries_are_diagnostic_only_and_do_not_change_mass_balance() {
        let baseline = basic_candidate();
        let with_zero = candidate(
            json!({
                "part_A": {"resin": 100.0, "pigment": 10.0, "unknown_zero": 0.0},
                "part_B": {"hardener": 40.0, "zero_solvent": 0.0},
            }),
            json!({}),
        );
        let baseline = evaluate(
            FORMULATION_ARITHMETIC_ID,
            &baseline,
            &FeatureSnapshot::default(),
        );
        let with_zero = evaluate(
            FORMULATION_ARITHMETIC_ID,
            &with_zero,
            &FeatureSnapshot::default(),
        );
        assert_eq!(
            baseline.metrics["mass_balance"],
            with_zero.metrics["mass_balance"]
        );
        assert_eq!(
            baseline.metrics["positive_mass_ingredient_ids"],
            with_zero.metrics["positive_mass_ingredient_ids"]
        );
        assert_eq!(
            with_zero.metrics["ignored_zero_mass_entries"],
            json!(["part_A.unknown_zero", "part_B.zero_solvent"])
        );
    }

    #[test]
    fn cure_is_failed_gates_and_never_scored() {
        let result = evaluate(
            CURE_POTLIFE_GATE_ID,
            &basic_candidate(),
            &FeatureSnapshot::default(),
        );
        assert_eq!(result.status, "FAILED_GATES");
        assert_eq!(result.gates["pre_registered_bar_passed"], false);
        assert_eq!(
            result.metrics["candidate_pot_life_prediction_h"],
            Value::Null
        );
        assert_eq!(result.score_0_1, None);
    }

    #[test]
    fn unresolved_public_data_is_not_opened_or_scored() {
        let result = evaluate(
            PUBLIC_CORROSION_BENCHMARK_ID,
            &basic_candidate(),
            &FeatureSnapshot::default(),
        );
        assert_eq!(result.status, "INSUFFICIENT_INPUT");
        assert_eq!(result.metrics["artifact_rights_status"], "UNRESOLVED");
        assert_eq!(result.metrics["artifact_access_attempted"], false);
        assert_eq!(result.metrics["benchmark_score"], Value::Null);
        assert_eq!(result.gates["promotion_gate_passed"], false);
    }

    #[test]
    fn verified_corrosion_artifact_is_consumed_without_candidate_authority() {
        let result = evaluate(
            PUBLIC_CORROSION_BENCHMARK_ID,
            &basic_candidate(),
            &verified_model_features(PUBLIC_CORROSION_BENCHMARK_ID),
        );
        assert_eq!(result.metrics["artifact_rights_status"], "ACCEPTED");
        assert_eq!(result.metrics["benchmark_score"], 0.81);
        assert_eq!(result.metrics["candidate_corrosion_validation"], false);
        assert_eq!(result.gates["verified_model_artifact"], true);
        assert_eq!(result.score_0_1, None);
    }

    #[test]
    fn v1_cure_artifact_is_diagnostic_replay_only() {
        let candidate = CandidateEnvelope::from_value(json!({
            "candidate_id": "cure-conditions",
            "candidate_type": "formulation",
            "formulation": {
                "part_A": {"resin": 100.0},
                "part_B": {"hardener": 50.0}
            },
            "context": {
                "cure_measurement_conditions": {
                    "resin_family": "DGEBA",
                    "hardener_family": "POLYAMIDE",
                    "mix_ratio_phr": 50.0,
                    "temperature_C": 25.0,
                    "test_mass_g": 100.0,
                    "method": "ASTM_D2471"
                }
            }
        }))
        .unwrap();
        let result = evaluate(
            CURE_POTLIFE_GATE_ID,
            &candidate,
            &verified_model_features(CURE_POTLIFE_GATE_ID),
        );
        assert_eq!(
            result.metrics["candidate_gel_time_prediction_min"],
            Value::Null
        );
        assert_eq!(
            result.metrics["candidate_pot_life_prediction_h"],
            Value::Null
        );
        assert_eq!(result.status, "FAILED_GATES");
        assert_eq!(result.gates["verified_model_artifact"], false);
        assert_eq!(result.score_0_1, None);
    }

    #[test]
    fn v1_cure_artifact_cannot_reach_domain_evaluation() {
        let candidate = CandidateEnvelope::from_value(json!({
            "candidate_id": "cure-ood",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"resin": 100.0}, "part_B": {"hardener": 50.0}},
            "context": {"cure_measurement_conditions": {
                "resin_family": "DGEBA", "hardener_family": "POLYAMIDE",
                "mix_ratio_phr": 50.0, "temperature_C": 80.0,
                "test_mass_g": 100.0, "method": "ASTM_D2471"
            }}
        }))
        .unwrap();
        let result = evaluate(
            CURE_POTLIFE_GATE_ID,
            &candidate,
            &verified_model_features(CURE_POTLIFE_GATE_ID),
        );
        assert_eq!(result.status, "FAILED_GATES");
        assert_eq!(
            result.metrics["candidate_gel_time_prediction_min"],
            Value::Null
        );
        assert_eq!(result.gates["verified_model_artifact"], false);
    }

    #[test]
    fn candidate_supplied_qc_release_is_ignored_without_host_receipt() {
        let candidate = candidate(
            json!({
                "part_A": {"resin": 100.0},
                "part_B": {"hardener": 40.0},
            }),
            json!({
                "process_qc": {
                    "accepted": true,
                    "accepted_evidence_package_id": "candidate-supplied",
                    "evidence_package_valid": true,
                    "release_status": "released"
                }
            }),
        );
        let result = evaluate(PROCESS_QC_TWIN_ID, &candidate, &FeatureSnapshot::default());
        assert_eq!(result.status, "FAILED_GATES");
        assert_eq!(result.metrics["candidate_release_assertion_present"], true);
        assert_eq!(result.metrics["candidate_release_assertion_trusted"], false);
        assert_eq!(result.gates["host_verified_signature_receipt"], false);
        assert_eq!(result.gates["batch_release_authority"], false);
    }

    #[test]
    fn valid_host_qc_receipt_admits_diagnostics_but_never_release_authority() {
        let candidate = candidate(
            json!({
                "part_A": {"resin": 100.0},
                "part_B": {"hardener": 40.0},
            }),
            json!({
                "process_qc": {
                    "accepted_evidence_package_id": "candidate-supplied",
                    "release_status": "released"
                }
            }),
        );
        let process_qc = candidate
            .value()
            .pointer("/evidence_refs/process_qc")
            .unwrap();
        let mut features = FeatureSnapshot::default();
        features.values.insert(
            HOST_VERIFIED_RECEIPT_FEATURE.into(),
            json!({
                "schema": HOST_VERIFIED_RECEIPT_SCHEMA,
                "evidence_scope": PROCESS_QC_RECEIPT_SCOPE,
                "accepted": true,
                "signature_verified": true,
                "revocation_checked": true,
                "fresh": true,
                "signature_algorithm": "Ed25519",
                "trust_store_status": "TRUSTED",
                "candidate_id": candidate.candidate_id(),
                "candidate_contract_hash_v1": candidate.contract_hash_v1(),
                "package_sha256": stable_hash(process_qc),
                "verifier_id": "host-evidence-intake",
            }),
        );
        let result = evaluate(PROCESS_QC_TWIN_ID, &candidate, &features);
        assert_eq!(result.status, "NO_AUTHORITY");
        assert_eq!(result.gates["host_verified_signature_receipt"], true);
        assert_eq!(result.gates["batch_release_authority"], false);
        assert!(result.objective_values.is_empty());
    }

    #[test]
    fn runtime_emits_all_three_spc_detectors_separate_from_specifications() {
        let baseline = (0_u64..20)
            .map(|index| {
                json!({
                    "batch_id": format!("baseline-{index}"),
                    "sequence": index + 1,
                    "value": 10.0 + if index % 2 == 0 { -0.2 } else { 0.2 }
                })
            })
            .collect::<Vec<_>>();
        let candidate = candidate(
            json!({"part_A": {"resin": 100.0}, "part_B": {"hardener": 40.0}}),
            json!({
                "process_qc": {
                    "series": [{
                        "variable": "viscosity",
                        "baseline": baseline,
                        "monitoring": [
                            {"batch_id": "monitor-1", "sequence": 21, "value": 10.0},
                            {"batch_id": "monitor-2", "sequence": 22, "value": 14.0}
                        ],
                        "specification_lower": 9.0,
                        "specification_upper": 12.0
                    }]
                }
            }),
        );
        let process_qc = candidate
            .value()
            .pointer("/evidence_refs/process_qc")
            .unwrap();
        let mut features = FeatureSnapshot::default();
        features.values.insert(
            HOST_VERIFIED_RECEIPT_FEATURE.into(),
            json!({
                "schema": HOST_VERIFIED_RECEIPT_SCHEMA,
                "evidence_scope": PROCESS_QC_RECEIPT_SCOPE,
                "accepted": true,
                "signature_verified": true,
                "revocation_checked": true,
                "fresh": true,
                "signature_algorithm": "Ed25519",
                "trust_store_status": "TRUSTED",
                "candidate_id": candidate.candidate_id(),
                "candidate_contract_hash_v1": candidate.contract_hash_v1(),
                "package_sha256": stable_hash(process_qc),
                "verifier_id": "host-evidence-intake"
            }),
        );
        let result = evaluate(PROCESS_QC_TWIN_ID, &candidate, &features);
        let audit = &result.metrics["spc_audits"][0];
        assert_eq!(result.metrics["detector_status"], "AUDIT_ONLY");
        assert_eq!(audit["shewhart_alerts"][0], "monitor-2");
        assert!(audit["ewma_alerts"].as_array().is_some());
        assert!(audit["cusum_alerts"].as_array().is_some());
        assert_eq!(audit["specification_failures"][0], "monitor-2");
        assert_eq!(result.gates["batch_release_authority"], false);
        assert!(result.objective_values.is_empty());
    }

    #[test]
    fn process_qc_rejects_reordered_batches_and_baseline_contamination() {
        let mut baseline = (0_u64..20)
            .map(|index| ProcessQcObservationV1 {
                batch_id: format!("baseline-{index}"),
                sequence: index + 1,
                value: 10.0 + index as f64 / 100.0,
            })
            .collect::<Vec<_>>();
        baseline.swap(18, 19);
        let series = ProcessQcSeriesV1 {
            variable: "viscosity".into(),
            baseline,
            monitoring: vec![ProcessQcObservationV1 {
                batch_id: "monitor-1".into(),
                sequence: 21,
                value: 10.0,
            }],
            specification_lower: None,
            specification_upper: None,
        };
        assert_eq!(
            audit_process_qc(&series).unwrap_err(),
            "observations must be strictly time ordered"
        );
    }

    #[test]
    fn process_qc_audit_shell_is_reproducible_and_has_zero_authority() {
        let first = process_qc_audit_shell().unwrap();
        let second = process_qc_audit_shell().unwrap();
        assert_eq!(
            serde_json::to_vec(&first).unwrap(),
            serde_json::to_vec(&second).unwrap()
        );
        assert_eq!(first.false_positive_alert_count, 0);
        assert_eq!(first.missed_deviation_detector_count, 0);
        assert!(first.detector_alert_counts.values().all(|count| *count > 0));
        assert!(first.malformed_missingness_rejected);
        assert!(first.reordered_time_rejected);
        assert!(first.specification_control_separation_passed);
        assert_eq!(first.authority_ceiling, "AUDIT_ONLY");
        assert!(!first.batch_release_authorized);
        assert!(!first.manufacturing_qualification_authorized);
    }

    fn stable_baseline(n: u64) -> Vec<ProcessQcObservationV1> {
        (1..=n)
            .map(|s| ProcessQcObservationV1 {
                batch_id: format!("baseline-{s:03}"),
                sequence: s,
                value: 100.0 + ((s as i64 - 1).rem_euclid(5) - 2) as f64 * 0.1,
            })
            .collect()
    }

    fn stable_monitoring(start: u64, n: u64) -> Vec<ProcessQcObservationV1> {
        (start..start + n)
            .map(|s| ProcessQcObservationV1 {
                batch_id: format!("monitor-{s:03}"),
                sequence: s,
                value: 100.0 + ((s as i64 - start as i64).rem_euclid(5) - 2) as f64 * 0.1,
            })
            .collect()
    }

    #[test]
    fn process_qc_time_leakage_duplicate_baseline_sequence_rejects() {
        let mut baseline = stable_baseline(20);
        baseline[6].sequence = baseline[5].sequence;
        let series = ProcessQcSeriesV1 {
            variable: "leakage-baseline".into(),
            baseline,
            monitoring: stable_monitoring(21, 20),
            specification_lower: None,
            specification_upper: None,
        };
        assert_eq!(
            audit_process_qc(&series).unwrap_err(),
            "observations must be strictly time ordered"
        );
    }

    #[test]
    fn process_qc_time_leakage_duplicate_monitoring_sequence_rejects() {
        let mut monitoring = stable_monitoring(21, 20);
        monitoring[6].sequence = monitoring[5].sequence;
        let series = ProcessQcSeriesV1 {
            variable: "leakage-monitoring".into(),
            baseline: stable_baseline(20),
            monitoring,
            specification_lower: None,
            specification_upper: None,
        };
        assert_eq!(
            audit_process_qc(&series).unwrap_err(),
            "observations must be strictly time ordered"
        );
    }

    #[test]
    fn process_qc_baseline_contamination_when_baseline_last_equals_monitoring_first_rejects() {
        let baseline = stable_baseline(20);
        let monitoring = vec![
            ProcessQcObservationV1 {
                batch_id: "monitor-020".into(),
                sequence: 20,
                value: 100.0,
            },
            ProcessQcObservationV1 {
                batch_id: "monitor-021".into(),
                sequence: 21,
                value: 100.0,
            },
        ];
        let series = ProcessQcSeriesV1 {
            variable: "contamination-boundary".into(),
            baseline,
            monitoring,
            specification_lower: None,
            specification_upper: None,
        };
        assert_eq!(
            audit_process_qc(&series).unwrap_err(),
            "observations must be strictly time ordered"
        );
    }

    #[test]
    fn process_qc_baseline_contamination_when_monitoring_first_below_baseline_last_rejects() {
        let baseline = stable_baseline(20);
        let monitoring = vec![
            ProcessQcObservationV1 {
                batch_id: "monitor-015".into(),
                sequence: 15,
                value: 100.0,
            },
            ProcessQcObservationV1 {
                batch_id: "monitor-016".into(),
                sequence: 16,
                value: 100.0,
            },
        ];
        let series = ProcessQcSeriesV1 {
            variable: "contamination-below".into(),
            baseline,
            monitoring,
            specification_lower: None,
            specification_upper: None,
        };
        assert_eq!(
            audit_process_qc(&series).unwrap_err(),
            "observations must be strictly time ordered"
        );
    }

    #[test]
    fn process_qc_reordered_batches_within_monitoring_rejects() {
        let mut monitoring = stable_monitoring(21, 20);
        monitoring.swap(5, 6);
        let series = ProcessQcSeriesV1 {
            variable: "reordered-monitoring".into(),
            baseline: stable_baseline(20),
            monitoring,
            specification_lower: None,
            specification_upper: None,
        };
        assert_eq!(
            audit_process_qc(&series).unwrap_err(),
            "observations must be strictly time ordered"
        );
    }

    #[test]
    fn process_qc_specification_and_control_channels_are_decoupled() {
        // (a) Stable baseline + stable monitoring + TIGHT spec:
        //     spec failures present, ALL control channels empty.
        let series_a = ProcessQcSeriesV1 {
            variable: "spec-only-fail".into(),
            baseline: stable_baseline(20),
            monitoring: stable_monitoring(21, 20),
            specification_lower: Some(99.9),
            specification_upper: Some(100.1),
        };
        let out_a = audit_process_qc(&series_a).unwrap();
        assert!(
            !out_a.specification_failures.is_empty(),
            "tight spec must produce specification_failures"
        );
        assert!(
            out_a.shewhart_alerts.is_empty(),
            "stable monitoring must not trigger Shewhart"
        );
        assert!(
            out_a.ewma_alerts.is_empty(),
            "stable monitoring must not trigger EWMA"
        );
        assert!(
            out_a.cusum_alerts.is_empty(),
            "stable monitoring must not trigger CUSUM"
        );

        // (b) Stable baseline + shifted monitoring (constant well above UCL) +
        //     WIDE spec: control alerts present, spec failures empty.
        let baseline = stable_baseline(20);
        // baseline sigma > 0.14, so 100.5 is more than 3 sigma above mean 100.
        let monitoring: Vec<ProcessQcObservationV1> = (21..41)
            .map(|s| ProcessQcObservationV1 {
                batch_id: format!("monitor-{s:03}"),
                sequence: s,
                value: 100.6,
            })
            .collect();
        let series_b = ProcessQcSeriesV1 {
            variable: "control-only-fail".into(),
            baseline,
            monitoring,
            specification_lower: Some(95.0),
            specification_upper: Some(105.0),
        };
        let out_b = audit_process_qc(&series_b).unwrap();
        assert!(
            out_b.specification_failures.is_empty(),
            "wide spec must not produce specification_failures"
        );
        assert!(
            !out_b.shewhart_alerts.is_empty(),
            "shifted monitoring must trigger Shewhart"
        );
    }

    #[test]
    fn process_qc_output_never_contains_release_or_qualification_authority() {
        let scenarios: Vec<ProcessQcSeriesV1> = vec![
            ProcessQcSeriesV1 {
                variable: "stable".into(),
                baseline: stable_baseline(20),
                monitoring: stable_monitoring(21, 20),
                specification_lower: Some(99.0),
                specification_upper: Some(101.0),
            },
            ProcessQcSeriesV1 {
                variable: "shifted".into(),
                baseline: stable_baseline(20),
                monitoring: (21..41)
                    .map(|s| ProcessQcObservationV1 {
                        batch_id: format!("monitor-{s:03}"),
                        sequence: s,
                        value: 100.6,
                    })
                    .collect(),
                specification_lower: None,
                specification_upper: None,
            },
        ];
        for series in scenarios {
            let out = audit_process_qc(&series).unwrap();
            assert_eq!(out.detector_status, "AUDIT_ONLY");
            let out_json = serde_json::to_value(&out).unwrap();
            for banned in [
                "batch_release",
                "release_authorized",
                "qualified",
                "authorized",
                "manufacturing_qualification",
                "release_authority",
            ] {
                assert!(
                    !contains_key_recursively(&out_json, banned),
                    "SpcAuditResultV1 must not contain key {banned}"
                );
            }
        }
    }

    fn contains_key_recursively(value: &Value, key: &str) -> bool {
        match value {
            Value::Object(map) => {
                if map.contains_key(key) {
                    return true;
                }
                map.values().any(|v| contains_key_recursively(v, key))
            }
            Value::Array(arr) => arr.iter().any(|v| contains_key_recursively(v, key)),
            _ => false,
        }
    }

    #[test]
    fn missing_conditions_abstain_without_defaults() {
        let candidate = candidate(
            json!({
                "part_A": {"resin": 100.0},
                "part_B": {"hardener": 40.0},
            }),
            json!({}),
        );
        let result = evaluate(VISCOSITY_SCORE_ID, &candidate, &FeatureSnapshot::default());
        assert_eq!(result.status, "INSUFFICIENT_INPUT");
        assert_eq!(
            result.metrics["declared_conditions"]["dft_mil"],
            Value::Null
        );
        assert!(result
            .missing_inputs
            .contains(&"formulation.application.temperature_C".into()));
    }

    #[test]
    fn declarative_universe_reconciles_without_fixed_cardinalities() {
        let candidate = CandidateEnvelope::from_value(json!({
            "candidate_id": "universe-test",
            "candidate_type": "formulation",
            "formulation": {
                "part_A": {"resin": 100.0},
                "part_B": {"hardener": 40.0}
            },
            "context": {
                "formulation_universe": {
                    "axes": {
                        "resin": ["r1", "r2", "r3"],
                        "hardener": ["h1", "h2"],
                        "ratio": [0.8, 1.0]
                    },
                    "infeasible_indices": [1, 7]
                }
            }
        }))
        .unwrap();
        let result = evaluate(
            FORMULATION_UNIVERSE_ID,
            &candidate,
            &FeatureSnapshot::default(),
        );
        assert_eq!(result.status, "SCORED");
        assert_eq!(result.metrics["cartesian_total"], 12);
        assert_eq!(result.metrics["solved_candidate_count"], 10);
        assert_eq!(result.metrics["infeasible_candidate_count"], 2);
        assert_eq!(result.gates["solved_plus_infeasible_equals_total"], true);
    }

    #[test]
    fn serialized_results_cannot_supply_identity_authority_or_locks() {
        let candidate = basic_candidate();
        for module_id in SUPPORTED_MODULE_IDS {
            let first = evaluate(module_id, &candidate, &FeatureSnapshot::default());
            let second = evaluate(module_id, &candidate, &FeatureSnapshot::default());
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
    fn equivalent_balance_uses_only_host_molecule_facts_and_rejects_zero_groups() {
        use amphora_rdkit_ffi::{
            MoleculeFactsV1, ReactiveFlagsV1, ToolkitProvenanceV1, REACTIVE_ONTOLOGY_VERSION,
            REQUIRED_RDKIT_VERSION,
        };
        let facts = |structure: &str, mass: f64, oxirane: u32, amine_h: u32| MoleculeFactsV1 {
            schema: "amphora.molecule-facts.v1".into(),
            canonical_isomeric_smiles: structure.into(),
            structure_identity: format!("smiles-sha256:{structure}"),
            canonical_structure_sha256: stable_hash(&Value::String(structure.into())),
            formula: "C2H4".into(),
            average_molecular_weight_g_mol: mass,
            oxirane_ring_count: oxirane,
            reactive_amine_hydrogen_count: amine_h,
            reactive_flags: ReactiveFlagsV1 {
                has_oxirane: oxirane > 0,
                has_reactive_amine_hydrogen: amine_h > 0,
                dual_role: oxirane > 0 && amine_h > 0,
            },
            ontology_version: REACTIVE_ONTOLOGY_VERSION.into(),
            toolkit_provenance: ToolkitProvenanceV1 {
                toolkit: "RDKit C++".into(),
                required_version: REQUIRED_RDKIT_VERSION.into(),
                detected_version: REQUIRED_RDKIT_VERSION.into(),
                exact_version_match: true,
            },
        };
        let resin = facts("C1OC1", 200.0, 2, 0);
        let hardener = facts("NCCN", 100.0, 0, 4);
        let balance = EquivalentBalanceV1::from_host_facts(&resin, &hardener, 100.0, 1.0).unwrap();
        assert_eq!(balance.eew_g_per_eq, 100.0);
        assert_eq!(balance.ahew_g_per_eq, 25.0);
        assert_eq!(balance.hardener_mass_g, 25.0);
        assert_eq!(balance.theoretical_hardener_phr, 25.0);
        assert!(!balance.candidate_property_overrides_accepted);
        assert!(!balance.ranking_eligible);
        assert!(matches!(
            EquivalentBalanceV1::from_host_facts(&facts("CC", 20.0, 0, 0), &hardener, 100.0, 1.0),
            Err(EquivalentBalanceError::NoOxirane)
        ));
        assert!(matches!(
            EquivalentBalanceV1::from_host_facts(&resin, &facts("CC", 20.0, 0, 0), 100.0, 1.0),
            Err(EquivalentBalanceError::NoReactiveAmineHydrogen)
        ));
    }

    // ---------------------------------------------------------------
    // Phase-0 formulation-arithmetic red-team tests
    // ---------------------------------------------------------------

    fn simple_candidate(part_a: Value, part_b: Value) -> Value {
        json!({
            "candidate_id": "test-arithmetic",
            "candidate_type": "formulation",
            "formulation": {"part_A": part_a, "part_B": part_b}
        })
    }

    #[test]
    fn validate_formulation_mass_ignores_candidate_supplied_property_claims() {
        // Same recipe with and without injected property claims → same computed masses.
        let base = simple_candidate(
            json!({"dgeba-resin": {"ingredient_id": "dgeba-resin", "mass_g": 100.0}}),
            json!({"teta-hardener": {"ingredient_id": "teta-hardener", "mass_g": 12.0}}),
        );
        let clean = validate_formulation_mass(&base).unwrap();
        assert!(clean.ignored_candidate_fields.is_empty());
        for injected_field in [
            "density", "eew", "ahew", "nonvolatile",
            "oil_absorption", "performance", "evidence", "feasibility",
        ] {
            let mut poisoned = base.clone();
            poisoned["formulation"][injected_field] = json!("attacker-supplied-value");
            let out = validate_formulation_mass(&poisoned).unwrap();
            assert!(out.ignored_candidate_fields.contains(&injected_field.to_string()),
                "{injected_field} not recorded as ignored");
            // Masses must be unchanged.
            assert_eq!(out.part_a_mass_g, clean.part_a_mass_g);
            assert_eq!(out.part_b_mass_g, clean.part_b_mass_g);
            assert_eq!(out.total_mass_g, clean.total_mass_g);
        }
    }

    #[test]
    fn validate_formulation_mass_is_ingredient_order_stable() {
        // Same ingredients in two different orderings → byte-identical diagnostic.
        let a1 = json!({
            "dgeba-resin": {"ingredient_id": "dgeba-resin", "mass_g": 100.0},
            "solvent-mek": {"ingredient_id": "solvent-mek", "mass_g": 30.0},
            "titanium-dioxide-pigment": {"ingredient_id": "titanium-dioxide-pigment", "mass_g": 60.0}
        });
        let a2 = json!({
            "titanium-dioxide-pigment": {"ingredient_id": "titanium-dioxide-pigment", "mass_g": 60.0},
            "solvent-mek": {"ingredient_id": "solvent-mek", "mass_g": 30.0},
            "dgeba-resin": {"ingredient_id": "dgeba-resin", "mass_g": 100.0}
        });
        let b = json!({"teta-hardener": {"ingredient_id": "teta-hardener", "mass_g": 12.0}});
        let d1 = validate_formulation_mass(&simple_candidate(a1, b.clone())).unwrap();
        let d2 = validate_formulation_mass(&simple_candidate(a2, b)).unwrap();
        assert_eq!(serde_json::to_vec(&d1).unwrap(), serde_json::to_vec(&d2).unwrap());
    }

    #[test]
    fn validate_formulation_mass_records_zero_mass_ingredients_separately_from_positive() {
        let candidate = simple_candidate(
            json!({
                "dgeba-resin": {"ingredient_id": "dgeba-resin", "mass_g": 100.0},
                "additive-defoamer": {"ingredient_id": "additive-defoamer", "mass_g": 0.0}
            }),
            json!({"teta-hardener": {"ingredient_id": "teta-hardener", "mass_g": 12.0}}),
        );
        let out = validate_formulation_mass(&candidate).unwrap();
        assert!(out.positive_mass_ingredient_ids.contains(&"dgeba-resin".to_string()));
        assert!(out.positive_mass_ingredient_ids.contains(&"teta-hardener".to_string()));
        assert!(!out.positive_mass_ingredient_ids.contains(&"additive-defoamer".to_string()));
        assert!(out.ignored_zero_mass_entries.contains(&"part_A.additive-defoamer".to_string()));
        assert_eq!(out.part_a_mass_g.unwrap(), 100.0);
        assert_eq!(out.total_mass_g.unwrap(), 112.0);
    }

    #[test]
    fn validate_formulation_mass_rejects_non_finite_or_negative_masses() {
        // NaN
        let nan_c = simple_candidate(
            json!({"dgeba-resin": {"ingredient_id": "dgeba-resin", "mass_g": f64::NAN}}),
            json!({"teta-hardener": {"ingredient_id": "teta-hardener", "mass_g": 12.0}}),
        );
        assert!(validate_formulation_mass(&nan_c).is_err(),
            "NaN mass must reject");
        // Infinity
        let inf_c = simple_candidate(
            json!({"dgeba-resin": {"ingredient_id": "dgeba-resin", "mass_g": f64::INFINITY}}),
            json!({"teta-hardener": {"ingredient_id": "teta-hardener", "mass_g": 12.0}}),
        );
        assert!(validate_formulation_mass(&inf_c).is_err(),
            "Infinity mass must reject");
        // Negative
        let neg_c = simple_candidate(
            json!({"dgeba-resin": {"ingredient_id": "dgeba-resin", "mass_g": -1.0}}),
            json!({"teta-hardener": {"ingredient_id": "teta-hardener", "mass_g": 12.0}}),
        );
        assert!(validate_formulation_mass(&neg_c).is_err(),
            "negative mass must reject");
    }

    #[test]
    fn validate_formulation_mass_abstains_when_either_part_is_missing() {
        // Missing part_B
        let missing_b = json!({
            "candidate_id": "test-missing-b",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"dgeba-resin": {"ingredient_id": "dgeba-resin", "mass_g": 100.0}}}
        });
        let out = validate_formulation_mass(&missing_b).unwrap();
        assert_eq!(out.status, "ABSTAIN");
        assert!(out.part_a_mass_g.is_none() && out.part_b_mass_g.is_none() && out.total_mass_g.is_none());
        // Missing part_A
        let missing_a = json!({
            "candidate_id": "test-missing-a",
            "candidate_type": "formulation",
            "formulation": {"part_B": {"teta-hardener": {"ingredient_id": "teta-hardener", "mass_g": 12.0}}}
        });
        let out2 = validate_formulation_mass(&missing_a).unwrap();
        assert_eq!(out2.status, "ABSTAIN");
        // All-zero-mass parts
        let all_zero = simple_candidate(
            json!({"a": {"ingredient_id": "a", "mass_g": 0.0}}),
            json!({"b": {"ingredient_id": "b", "mass_g": 0.0}}),
        );
        let out3 = validate_formulation_mass(&all_zero).unwrap();
        assert_eq!(out3.status, "ABSTAIN");
    }

    #[test]
    fn validate_formulation_mass_conservation_identity_holds_bit_exactly() {
        // 100 + 12 = 112 exactly in f64 (all rational, no rounding).
        let candidate = simple_candidate(
            json!({"dgeba-resin": {"ingredient_id": "dgeba-resin", "mass_g": 100.0}}),
            json!({"teta-hardener": {"ingredient_id": "teta-hardener", "mass_g": 12.0}}),
        );
        let out = validate_formulation_mass(&candidate).unwrap();
        let a = out.part_a_mass_g.unwrap();
        let b = out.part_b_mass_g.unwrap();
        let t = out.total_mass_g.unwrap();
        // Bit-exact conservation.
        assert_eq!((a + b).to_bits(), t.to_bits(),
            "part_A + part_B must equal total_mass_g at f64 bit precision");
        assert_eq!(t.to_bits(), 112.0_f64.to_bits());
    }

    #[test]
    fn validate_formulation_mass_never_upgrades_authority() {
        // Standard positive-mass candidate.
        let candidate = simple_candidate(
            json!({"dgeba-resin": {"ingredient_id": "dgeba-resin", "mass_g": 100.0}}),
            json!({"teta-hardener": {"ingredient_id": "teta-hardener", "mass_g": 12.0}}),
        );
        let out = validate_formulation_mass(&candidate).unwrap();
        // No authority upgrades regardless of successful arithmetic.
        assert_eq!(out.arithmetic_scope, "MASS_ONLY");
        assert_eq!(out.scientific_readiness, "UNVALIDATED");
        assert!(!out.ranking_eligible);
        assert!(!out.usable_by_optimizer);
        assert!(!out.candidate_created_evidence);
        assert!(!out.authority_upgrade);
        assert!(!out.unresolved_legacy_data_accessed);
        assert!(out.objective_values.is_empty());
        // Abstaining path preserves the same authority locks.
        let missing = json!({
            "candidate_id": "test-abstain",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"a": {"ingredient_id": "a", "mass_g": 1.0}}}
        });
        let out2 = validate_formulation_mass(&missing).unwrap();
        assert_eq!(out2.status, "ABSTAIN");
        assert_eq!(out2.arithmetic_scope, "MASS_ONLY");
        assert!(!out2.ranking_eligible);
        assert!(!out2.usable_by_optimizer);
        assert!(!out2.authority_upgrade);
    }

    // ---------------------------------------------------------------
    // Phase-0 envelope-gates red-team tests
    // ---------------------------------------------------------------

    fn constraint(id: &str, path: &str, lo: f64, hi: f64) -> EnvelopeConstraintV1 {
        EnvelopeConstraintV1 {
            constraint_id: id.into(),
            feature_path: path.into(),
            unit: "g".into(),
            lower_inclusive: lo,
            upper_inclusive: hi,
        }
    }

    fn policy_v1(constraints: Vec<EnvelopeConstraintV1>) -> EnvelopePolicyV1 {
        EnvelopePolicyV1 {
            schema: "amphora.synthetic-envelope-policy.v1".into(),
            policy_id: "test-policy".into(),
            fixture_only: true,
            authoritative: false,
            constraints,
        }
    }

    fn snapshot_v1(a: f64, b: f64, total: f64) -> TrustedArithmeticSnapshotV1 {
        let mut values = BTreeMap::new();
        values.insert(
            "mass.part_A_g".into(),
            DimensionedFeatureV1 { value: a, unit: "g".into() },
        );
        values.insert(
            "mass.part_B_g".into(),
            DimensionedFeatureV1 { value: b, unit: "g".into() },
        );
        values.insert(
            "mass.total_g".into(),
            DimensionedFeatureV1 { value: total, unit: "g".into() },
        );
        TrustedArithmeticSnapshotV1 {
            schema: "amphora.trusted-arithmetic-snapshot.v1".into(),
            trusted: true,
            values,
        }
    }

    fn assert_authority_locked(r: &EnvelopeGateResultV1) {
        assert!(!r.ranking_eligible);
        assert!(!r.usable_by_optimizer);
        assert!(!r.authority_upgrade);
        assert!(!r.wet_lab_evidence_created);
        assert!(!r.qualification_evidence_created);
        assert!(!r.release_evidence_created);
        assert!(!r.product_evidence_created);
        assert!(r.objective_values.is_empty());
    }

    #[test]
    fn evaluate_envelope_policy_abstains_on_missing_policy_or_snapshot() {
        let policy = policy_v1(vec![constraint("c1", "mass.part_A_g", 100.0, 200.0)]);
        let snap = snapshot_v1(150.0, 20.0, 170.0);
        // No policy → ABSTAIN.
        let r1 = evaluate_envelope_policy(None, Some(&snap), true).unwrap();
        assert_eq!(r1.status, "ABSTAIN");
        assert!(!r1.pass_all_hard);
        assert_authority_locked(&r1);
        // No snapshot → ABSTAIN.
        let r2 = evaluate_envelope_policy(Some(&policy), None, true).unwrap();
        assert_eq!(r2.status, "ABSTAIN");
        assert!(!r2.pass_all_hard);
        assert_authority_locked(&r2);
    }

    #[test]
    fn evaluate_envelope_policy_abstains_on_wrong_policy_schema_or_empty_policy_id() {
        let snap = snapshot_v1(150.0, 20.0, 170.0);
        // Wrong schema.
        let mut bad_schema = policy_v1(vec![constraint("c1", "mass.part_A_g", 100.0, 200.0)]);
        bad_schema.schema = "amphora.other-policy.v1".into();
        let r = evaluate_envelope_policy(Some(&bad_schema), Some(&snap), true).unwrap();
        assert_eq!(r.status, "ABSTAIN");
        assert_authority_locked(&r);
        // Empty policy_id.
        let mut empty_id = policy_v1(vec![constraint("c1", "mass.part_A_g", 100.0, 200.0)]);
        empty_id.policy_id = "   ".into();
        let r2 = evaluate_envelope_policy(Some(&empty_id), Some(&snap), true).unwrap();
        assert_eq!(r2.status, "ABSTAIN");
    }

    #[test]
    fn evaluate_envelope_policy_abstains_on_untrusted_snapshot() {
        let policy = policy_v1(vec![constraint("c1", "mass.part_A_g", 100.0, 200.0)]);
        // snapshot.trusted = false.
        let mut untrusted = snapshot_v1(150.0, 20.0, 170.0);
        untrusted.trusted = false;
        let r = evaluate_envelope_policy(Some(&policy), Some(&untrusted), true).unwrap();
        assert_eq!(r.status, "ABSTAIN");
        assert_authority_locked(&r);
        // Wrong snapshot schema.
        let mut bad_schema = snapshot_v1(150.0, 20.0, 170.0);
        bad_schema.schema = "amphora.other-snapshot.v1".into();
        let r2 = evaluate_envelope_policy(Some(&policy), Some(&bad_schema), true).unwrap();
        assert_eq!(r2.status, "ABSTAIN");
    }

    #[test]
    fn evaluate_envelope_policy_abstains_on_non_authoritative_without_synthetic_flag() {
        // fixture_only=true, authoritative=false, allow_synthetic_fixture=false → ABSTAIN.
        let policy = policy_v1(vec![constraint("c1", "mass.part_A_g", 100.0, 200.0)]);
        let snap = snapshot_v1(150.0, 20.0, 170.0);
        let r = evaluate_envelope_policy(Some(&policy), Some(&snap), false).unwrap();
        assert_eq!(r.status, "ABSTAIN");
        assert_authority_locked(&r);
    }

    #[test]
    fn evaluate_envelope_policy_errors_on_empty_or_duplicate_constraints() {
        let snap = snapshot_v1(150.0, 20.0, 170.0);
        // Empty constraints → Err.
        let empty = policy_v1(vec![]);
        assert!(evaluate_envelope_policy(Some(&empty), Some(&snap), true).is_err());
        // Duplicate constraint_id → Err.
        let dup = policy_v1(vec![
            constraint("c1", "mass.part_A_g", 100.0, 200.0),
            constraint("c1", "mass.part_B_g", 10.0, 30.0),
        ]);
        assert!(evaluate_envelope_policy(Some(&dup), Some(&snap), true).is_err());
        // Empty constraint_id → Err (duplicate check inserts and fails on empty when repeated OR rejects immediately).
        let empty_cid = policy_v1(vec![constraint("   ", "mass.part_A_g", 100.0, 200.0)]);
        assert!(evaluate_envelope_policy(Some(&empty_cid), Some(&snap), true).is_err());
    }

    #[test]
    fn evaluate_envelope_policy_errors_on_unknown_feature_path() {
        // The runtime whitelist admits only mass.part_A_g / mass.part_B_g / mass.total_g.
        let policy = policy_v1(vec![constraint("c1", "volume.total_ml", 100.0, 200.0)]);
        let snap = snapshot_v1(150.0, 20.0, 170.0);
        assert!(evaluate_envelope_policy(Some(&policy), Some(&snap), true).is_err());

        let mixed = policy_v1(vec![
            constraint("c1", "mass.part_A_g", 100.0, 200.0),
            constraint("c2", "voc.g_per_l", 0.0, 250.0),
        ]);
        assert!(evaluate_envelope_policy(Some(&mixed), Some(&snap), true).is_err());
    }

    #[test]
    fn evaluate_envelope_policy_errors_on_inverted_or_non_finite_bounds() {
        let snap = snapshot_v1(150.0, 20.0, 170.0);
        // Inverted.
        let inverted = policy_v1(vec![constraint("c1", "mass.part_A_g", 200.0, 100.0)]);
        assert!(evaluate_envelope_policy(Some(&inverted), Some(&snap), true).is_err());
        // Non-finite lower.
        let nan_low = policy_v1(vec![constraint("c1", "mass.part_A_g", f64::NAN, 200.0)]);
        assert!(evaluate_envelope_policy(Some(&nan_low), Some(&snap), true).is_err());
        // Non-finite upper.
        let inf_high = policy_v1(vec![constraint("c1", "mass.part_A_g", 100.0, f64::INFINITY)]);
        assert!(evaluate_envelope_policy(Some(&inf_high), Some(&snap), true).is_err());
    }

    #[test]
    fn evaluate_envelope_policy_errors_on_missing_feature_or_unit_mismatch() {
        let policy = policy_v1(vec![
            constraint("c1", "mass.part_A_g", 100.0, 200.0),
            constraint("c2", "mass.part_B_g", 10.0, 30.0),
            constraint("c3", "mass.total_g", 110.0, 230.0),
        ]);
        // Snapshot missing mass.part_B_g.
        let mut missing_feat = snapshot_v1(150.0, 20.0, 170.0);
        missing_feat.values.remove("mass.part_B_g");
        assert!(evaluate_envelope_policy(Some(&policy), Some(&missing_feat), true).is_err());
        // Unit mismatch: constraint says "g", snapshot says "kg".
        let mut mismatch = snapshot_v1(150.0, 20.0, 170.0);
        mismatch.values.insert(
            "mass.part_A_g".into(),
            DimensionedFeatureV1 { value: 150.0, unit: "kg".into() },
        );
        assert!(evaluate_envelope_policy(Some(&policy), Some(&mismatch), true).is_err());
        // Non-finite snapshot value.
        let mut nan_val = snapshot_v1(f64::NAN, 20.0, 170.0);
        nan_val.values.insert(
            "mass.part_A_g".into(),
            DimensionedFeatureV1 { value: f64::NAN, unit: "g".into() },
        );
        assert!(evaluate_envelope_policy(Some(&policy), Some(&nan_val), true).is_err());
    }

    #[test]
    fn evaluate_envelope_policy_boundary_pass_is_bit_exact_and_authority_stays_locked() {
        // Snapshot at exactly lower_inclusive → margin should be 0.0 bit-exact.
        let policy = policy_v1(vec![
            constraint("c_a", "mass.part_A_g", 100.0, 200.0),
            constraint("c_b", "mass.part_B_g", 10.0, 30.0),
            constraint("c_t", "mass.total_g", 110.0, 230.0),
        ]);
        let snap_lo = snapshot_v1(100.0, 20.0, 120.0);
        let r_lo = evaluate_envelope_policy(Some(&policy), Some(&snap_lo), true).unwrap();
        assert_eq!(r_lo.status, "UNVALIDATED");
        assert!(r_lo.pass_all_hard, "at-lower must pass under inclusive bound");
        // Confirm the bit-exact zero margin on c_a.
        let margin_a = r_lo.margins.get("c_a").copied().expect("c_a margin present");
        assert_eq!(margin_a.to_bits(), 0.0_f64.to_bits(),
            "at-lower part_A margin must be exactly 0.0 (INCLUSIVE_BOUNDARY_DRIFT)");
        assert_authority_locked(&r_lo);

        // Snapshot at exactly upper_inclusive → margin should also be 0.0.
        let snap_hi = snapshot_v1(200.0, 20.0, 220.0);
        let r_hi = evaluate_envelope_policy(Some(&policy), Some(&snap_hi), true).unwrap();
        assert!(r_hi.pass_all_hard);
        let margin_a_hi = r_hi.margins.get("c_a").copied().expect("c_a margin present");
        assert_eq!(margin_a_hi.to_bits(), 0.0_f64.to_bits(),
            "at-upper part_A margin must be exactly 0.0 (INCLUSIVE_BOUNDARY_DRIFT)");
        assert_authority_locked(&r_hi);

        // Just below lower → must fail.
        let snap_below = snapshot_v1(99.9, 20.0, 119.9);
        let r_below = evaluate_envelope_policy(Some(&policy), Some(&snap_below), true).unwrap();
        assert_eq!(r_below.status, "FAILED_GATES");
        assert!(!r_below.pass_all_hard);
        assert_authority_locked(&r_below);
    }

    // ---------------------------------------------------------------
    // Phase-0 formulation-universe (Cartesian accounting) red-team tests
    // ---------------------------------------------------------------

    fn universe_candidate(axes: Value, infeasible: Option<Value>, claims: Option<Value>) -> Value {
        let mut universe = Map::new();
        universe.insert("axes".into(), axes);
        if let Some(indices) = infeasible {
            universe.insert("infeasible_indices".into(), indices);
        }
        if let Some(c) = claims {
            universe.insert("claims".into(), c);
        }
        json!({"context": {"formulation_universe": universe}})
    }

    #[test]
    fn validate_formulation_universe_abstains_when_no_axes_registered() {
        let no_context = json!({});
        let r = validate_formulation_universe(&no_context).unwrap();
        assert_eq!(r.status, "ABSTAIN");
        assert!(r.cartesian_total.is_none());
        assert!(r.solved_candidate_count.is_none());
        assert!(r.infeasible_candidate_count.is_none());
        assert!(!r.candidate_feasibility_claims_ignored);
        assert!(!r.ranking_eligible);
        assert!(!r.usable_by_optimizer);
        assert!(!r.authority_upgrade);
        assert!(r.objective_values.is_empty());
        // With a claims field but no axes → still ABSTAIN, but claims_ignored=true.
        let claims_only = universe_candidate(json!({}), None, Some(json!({"solved": 99})));
        // Empty axes should still error since axes exist but are empty.
        let empty_axes_result = validate_formulation_universe(&claims_only);
        assert!(empty_axes_result.is_err());
    }

    #[test]
    fn validate_formulation_universe_errors_on_empty_axes_or_empty_axis_values() {
        // Empty axes object.
        let empty = universe_candidate(json!({}), None, None);
        assert!(validate_formulation_universe(&empty).is_err());
        // An axis with empty values array.
        let empty_values = universe_candidate(json!({"resin": []}), None, None);
        assert!(validate_formulation_universe(&empty_values).is_err());
        // Axes not an object.
        let not_object = json!({
            "context": {"formulation_universe": {"axes": ["not-an-object"]}}
        });
        assert!(validate_formulation_universe(&not_object).is_err());
    }

    #[test]
    fn validate_formulation_universe_rejects_canonical_duplicate_axis_entries() {
        // Literal string duplicate.
        let dup_string = universe_candidate(
            json!({"resin": ["DGEBA", "DGEBA"]}),
            None,
            None,
        );
        assert!(validate_formulation_universe(&dup_string).is_err());
        // Integer duplicate.
        let dup_int = universe_candidate(json!({"level": [1, 1]}), None, None);
        assert!(validate_formulation_universe(&dup_int).is_err());
        // Canonically-equal objects with different key insertion orders — stable_hash catches this.
        let dup_canonical = universe_candidate(
            json!({"pair": [{"a": 1, "b": 2}, {"b": 2, "a": 1}]}),
            None,
            None,
        );
        assert!(validate_formulation_universe(&dup_canonical).is_err(),
            "canonically-equal objects must be detected as CARTESIAN_CANONICAL_DUPLICATION");
    }

    #[test]
    fn validate_formulation_universe_rejects_cartesian_cardinality_overflow() {
        // 12 × 12 × 12 = 1728 (OK); 20 × 20 × 20 = 8000 (OK); 30 × 30 × 30 = 27000 (over MAX 10000).
        let over_max = universe_candidate(
            json!({
                "a": (0..30).collect::<Vec<_>>(),
                "b": (0..30).collect::<Vec<_>>(),
                "c": (0..30).collect::<Vec<_>>(),
            }),
            None,
            None,
        );
        assert!(validate_formulation_universe(&over_max).is_err());
        // Just under the ceiling: 10 × 10 × 10 = 1000 passes.
        let under_max = universe_candidate(
            json!({
                "a": (0..10).collect::<Vec<_>>(),
                "b": (0..10).collect::<Vec<_>>(),
                "c": (0..10).collect::<Vec<_>>(),
            }),
            None,
            None,
        );
        let ok = validate_formulation_universe(&under_max).unwrap();
        assert_eq!(ok.cartesian_total, Some(1000));
    }

    #[test]
    fn validate_formulation_universe_rejects_infeasible_indices_out_of_range_or_duplicated() {
        // Total = 4. Index equal to total is out-of-range.
        let idx_at_total = universe_candidate(
            json!({"a": [1, 2], "b": [3, 4]}),
            Some(json!([4])),
            None,
        );
        assert!(validate_formulation_universe(&idx_at_total).is_err());
        // Index far beyond total.
        let idx_over = universe_candidate(
            json!({"a": [1, 2], "b": [3, 4]}),
            Some(json!([100])),
            None,
        );
        assert!(validate_formulation_universe(&idx_over).is_err());
        // Duplicate index.
        let idx_dup = universe_candidate(
            json!({"a": [1, 2], "b": [3, 4]}),
            Some(json!([1, 1])),
            None,
        );
        assert!(validate_formulation_universe(&idx_dup).is_err());
        // Negative index (non-u64).
        let idx_neg = universe_candidate(
            json!({"a": [1, 2], "b": [3, 4]}),
            Some(json!([-1])),
            None,
        );
        assert!(validate_formulation_universe(&idx_neg).is_err());
        // Float index (non-u64).
        let idx_float = universe_candidate(
            json!({"a": [1, 2], "b": [3, 4]}),
            Some(json!([1.5])),
            None,
        );
        assert!(validate_formulation_universe(&idx_float).is_err());
        // Infeasible indices without registered axes.
        let no_axes = json!({
            "context": {
                "formulation_universe": {
                    "infeasible_indices": [0]
                }
            }
        });
        assert!(validate_formulation_universe(&no_axes).is_err());
    }

    #[test]
    fn validate_formulation_universe_ignores_candidate_feasibility_claims_and_computes_counts_deterministically() {
        let axes = json!({"a": [1, 2, 3], "b": [4, 5]});
        // Baseline: no claims.
        let base = universe_candidate(axes.clone(), Some(json!([0, 3])), None);
        let base_out = validate_formulation_universe(&base).unwrap();
        assert!(!base_out.candidate_feasibility_claims_ignored);
        assert_eq!(base_out.cartesian_total, Some(6));
        assert_eq!(base_out.solved_candidate_count, Some(4));
        assert_eq!(base_out.infeasible_candidate_count, Some(2));
        // Now inject bogus claims — output counts must be unchanged.
        let poisoned = universe_candidate(
            axes.clone(),
            Some(json!([0, 3])),
            Some(json!({
                "solved_candidate_count": 99999,
                "infeasible_candidate_count": 0,
                "authority_upgrade": true,
                "ranking_eligible": true,
                "objective_values": {"forged": 0.99},
            })),
        );
        let poisoned_out = validate_formulation_universe(&poisoned).unwrap();
        assert!(poisoned_out.candidate_feasibility_claims_ignored,
            "claims field presence must set candidate_feasibility_claims_ignored=true");
        assert_eq!(poisoned_out.cartesian_total, base_out.cartesian_total);
        assert_eq!(poisoned_out.solved_candidate_count, base_out.solved_candidate_count);
        assert_eq!(poisoned_out.infeasible_candidate_count, base_out.infeasible_candidate_count);
        assert!(!poisoned_out.authority_upgrade);
        assert!(!poisoned_out.ranking_eligible);
        assert!(!poisoned_out.usable_by_optimizer);
        assert!(poisoned_out.objective_values.is_empty());
    }

    #[test]
    fn validate_formulation_universe_authority_envelope_stays_locked_across_all_paths() {
        // Success path.
        let ok = validate_formulation_universe(
            &universe_candidate(json!({"a": [1, 2]}), None, None),
        )
        .unwrap();
        assert_eq!(ok.status, "UNVALIDATED");
        assert_eq!(ok.scientific_readiness, "UNVALIDATED");
        assert_eq!(ok.feasibility_basis, "DECLARATIVE_ACCOUNTING_ONLY");
        assert!(!ok.ranking_eligible);
        assert!(!ok.usable_by_optimizer);
        assert!(!ok.authority_upgrade);
        assert!(!ok.unresolved_legacy_data_accessed);
        assert!(!ok.candidate_created_evidence);
        assert!(ok.objective_values.is_empty());
        // Abstain path.
        let ab = validate_formulation_universe(&json!({})).unwrap();
        assert_eq!(ab.status, "ABSTAIN");
        assert_eq!(ab.feasibility_basis, "DECLARATIVE_ACCOUNTING_ONLY");
        assert!(!ab.ranking_eligible);
        assert!(!ab.usable_by_optimizer);
        assert!(!ab.authority_upgrade);
        assert!(ab.objective_values.is_empty());
    }

    #[test]
    fn validate_formulation_universe_axis_order_produces_byte_identical_output() {
        // Two candidates with the same axis content but different key insertion order.
        let candidate_ab = universe_candidate(
            json!({"axis_a": [1, 2], "axis_b": [3, 4, 5]}),
            Some(json!([2])),
            None,
        );
        let candidate_ba = universe_candidate(
            json!({"axis_b": [3, 4, 5], "axis_a": [1, 2]}),
            Some(json!([2])),
            None,
        );
        let out_ab = validate_formulation_universe(&candidate_ab).unwrap();
        let out_ba = validate_formulation_universe(&candidate_ba).unwrap();
        assert_eq!(serde_json::to_vec(&out_ab).unwrap(), serde_json::to_vec(&out_ba).unwrap(),
            "axis-name insertion order must not affect byte-identical output");
    }
}
