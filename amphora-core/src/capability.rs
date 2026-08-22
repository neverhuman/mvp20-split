use crate::CandidateEnvelope;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;
use thiserror::Error;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ModuleDescriptor {
    pub project: String,
    pub authority_ceiling: String,
    pub solver_use_ceiling: String,
    pub model_readiness_ceiling: String,
    pub ranking_eligible: bool,
    #[serde(default)]
    pub candidate_types: Vec<String>,
    #[serde(default)]
    pub non_blocking_claim_locks: Vec<String>,
    pub readiness: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct FeatureSnapshot {
    #[serde(default)]
    pub values: BTreeMap<String, Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionContext {
    pub run_id: String,
    pub deterministic_seed: u64,
    #[serde(default)]
    pub lineage: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModuleResult {
    pub status: String,
    pub score_0_1: Option<f64>,
    #[serde(default)]
    pub objective_values: BTreeMap<String, Value>,
    #[serde(default)]
    pub metrics: BTreeMap<String, Value>,
    #[serde(default)]
    pub gates: BTreeMap<String, Value>,
    #[serde(default)]
    pub uncertainty: BTreeMap<String, Value>,
    #[serde(default)]
    pub missing_inputs: Vec<String>,
    #[serde(default)]
    pub explanations: Vec<String>,
    #[serde(default)]
    pub source_refs: Vec<String>,
    pub evidence_scope: String,
}

impl ModuleResult {
    pub fn quarantined(reason: impl Into<String>) -> Self {
        let reason = reason.into();
        Self {
            status: "INSUFFICIENT_INPUT".into(),
            score_0_1: None,
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
            missing_inputs: vec![reason.clone()],
            explanations: vec![reason],
            source_refs: Vec::new(),
            evidence_scope: "COMPUTATIONAL_DIAGNOSTIC_ONLY".into(),
        }
    }
}

#[derive(Debug, Error)]
pub enum CapabilityError {
    #[error("candidate type is not accepted by this capability")]
    CandidateType,
    #[error("capability input is invalid: {0}")]
    InvalidInput(String),
    #[error("capability is quarantined: {0}")]
    Quarantined(String),
}

pub trait Capability: Send + Sync {
    fn descriptor(&self) -> &'static ModuleDescriptor;

    fn evaluate(
        &self,
        candidate: &CandidateEnvelope,
        features: &FeatureSnapshot,
        context: &ExecutionContext,
    ) -> Result<ModuleResult, CapabilityError>;
}
