#![forbid(unsafe_code)]

use amphora_core::{
    stable_hash, CandidateEnvelope, ConfidenceIntervalV1, FeatureSnapshot, ModuleResult,
    VerifiedFormulationModelInputV2,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

pub const MODULE_ID: &str = "amphora-solvency-score";
pub const HOST_FEATURE_KEY: &str = "verified_formulation_model.amphora-solvency-score";
pub const OBSERVATION_SCHEMA: &str = "amphora.solvency-observation.v1";
pub const OBSERVATION_BUNDLE_SCHEMA: &str = "amphora.solvency-observation-bundle.v1";
pub const DATASET_SCHEMA: &str = "amphora.solvency-dataset.v1";
pub const SPLIT_SCHEMA: &str = "amphora.solvency-split.v1";
pub const BENCHMARK_LOCK_SCHEMA: &str = "amphora.solvency-benchmark-lock.v1";
pub const PARAMETER_ARTIFACT_SCHEMA: &str = "amphora.solvency-parameter-artifact.v1";
pub const PARAMETER_ARTIFACT_V2_SCHEMA: &str = "amphora.solvency-parameter-artifact.v2";
pub const MODEL_ARTIFACT_SCHEMA: &str = "amphora.solvency-model-artifact.v1";
pub const PREDICTION_SCHEMA: &str = "amphora.solvency-prediction.v1";
pub const INDEPENDENT_REVIEW_SCHEMA: &str = "amphora.solvency-independent-review.v1";
pub const BENCHMARK_RECEIPT_SCHEMA: &str = "amphora.solvency-benchmark-receipt.v1";
pub const RESIDUAL_MODEL_L2: f64 = 1.0;
pub const RESIDUAL_MODEL_SEED: u64 = 20_260_717;
const EPSILON: f64 = 1e-7;

#[derive(Debug, Error, PartialEq)]
pub enum SolvencyError {
    #[error("unexpected schema or module identity")]
    Identity,
    #[error("required field is empty: {0}")]
    Empty(&'static str),
    #[error("invalid SHA-256: {0}")]
    Hash(&'static str),
    #[error("non-finite or out-of-range value: {0}")]
    Range(&'static str),
    #[error("parameter rights are not eligible")]
    Rights,
    #[error("incomplete pair matrix")]
    PairMatrix,
    #[error("commercial mixture identity is ambiguous or positive-mass components were excluded")]
    AmbiguousComposition,
    #[error("dataset, split, lock, or parameter parent mismatch")]
    Parent,
    #[error("split leaks a blend or solvent family")]
    Leakage,
    #[error("tangent-plane minimization did not converge")]
    NonConvergent,
    #[error("observation is outside the artifact applicability domain")]
    OutOfDomain,
    #[error("JSON contract error: {0}")]
    Json(String),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct OligomerFractionV1 {
    pub degree_of_polymerization: f64,
    pub mole_fraction_0_1: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CarrierComponentV1 {
    pub component_id: String,
    pub structure_sha256: String,
    pub role: String,
    pub lot_id: String,
    pub identity_status: String,
    pub volume_fraction_0_1: f64,
    pub molar_volume_cm3_mol_at_reference: f64,
    pub molar_volume_temperature_coefficient_per_k: f64,
    pub segment_count: f64,
    pub oligomer_distribution: Vec<OligomerFractionV1>,
}

impl CarrierComponentV1 {
    fn validate(&self) -> Result<(), SolvencyError> {
        for (field, value) in [
            ("component_id", self.component_id.as_str()),
            ("role", self.role.as_str()),
            ("lot_id", self.lot_id.as_str()),
        ] {
            require_text(field, value)?;
        }
        require_hash("structure_sha256", &self.structure_sha256)?;
        if self.identity_status != "EXACT"
            || !finite_between(self.volume_fraction_0_1, 0.0, 1.0)
            || !finite_positive(self.molar_volume_cm3_mol_at_reference)
            || !self.molar_volume_temperature_coefficient_per_k.is_finite()
            || !finite_positive(self.segment_count)
        {
            return Err(SolvencyError::AmbiguousComposition);
        }
        if self.role == "RESIN" {
            if self.oligomer_distribution.is_empty()
                || self.oligomer_distribution.iter().any(|row| {
                    !finite_positive(row.degree_of_polymerization)
                        || !finite_between(row.mole_fraction_0_1, 0.0, 1.0)
                })
                || (self
                    .oligomer_distribution
                    .iter()
                    .map(|row| row.mole_fraction_0_1)
                    .sum::<f64>()
                    - 1.0)
                    .abs()
                    > 1e-6
            {
                return Err(SolvencyError::Range("resin oligomer distribution"));
            }
        } else if !self.oligomer_distribution.is_empty() {
            return Err(SolvencyError::Range("non-resin oligomer distribution"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct SolvencyObservationV1 {
    pub schema: String,
    pub module_id: String,
    pub observation_id: String,
    pub candidate_id: String,
    pub blend_id: String,
    pub solvent_family_group: String,
    pub resin_grade: String,
    pub resin_lot: String,
    pub preparation_id: String,
    pub replicate_id: String,
    pub temperature_c: f64,
    pub components: Vec<CarrierComponentV1>,
    pub excluded_positive_mass_components: Vec<String>,
    pub microscopy_single_phase_1h: Option<bool>,
    pub microscopy_single_phase_24h: Option<bool>,
    pub turbidity_ntu_1h: Option<f64>,
    pub turbidity_ntu_24h: Option<f64>,
    pub method_id: String,
    pub raw_file_hashes: BTreeMap<String, String>,
    pub rights_receipt_sha256: String,
    pub rights_eligible: bool,
}

impl SolvencyObservationV1 {
    pub fn validate_conditions(&self) -> Result<(), SolvencyError> {
        require_identity(&self.schema, OBSERVATION_SCHEMA, &self.module_id)?;
        for (field, value) in [
            ("observation_id", self.observation_id.as_str()),
            ("candidate_id", self.candidate_id.as_str()),
            ("blend_id", self.blend_id.as_str()),
            ("solvent_family_group", self.solvent_family_group.as_str()),
            ("resin_grade", self.resin_grade.as_str()),
            ("resin_lot", self.resin_lot.as_str()),
            ("preparation_id", self.preparation_id.as_str()),
            ("replicate_id", self.replicate_id.as_str()),
            ("method_id", self.method_id.as_str()),
        ] {
            require_text(field, value)?;
        }
        require_hash("rights_receipt_sha256", &self.rights_receipt_sha256)?;
        validate_hash_map(&self.raw_file_hashes)?;
        if !self.rights_eligible {
            return Err(SolvencyError::Rights);
        }
        if !self.excluded_positive_mass_components.is_empty() || self.components.len() < 2 {
            return Err(SolvencyError::AmbiguousComposition);
        }
        if !finite_between(self.temperature_c, -20.0, 100.0) {
            return Err(SolvencyError::Range("temperature_c"));
        }
        let mut ids = BTreeSet::new();
        let mut total = 0.0;
        let mut resin = false;
        for component in &self.components {
            component.validate()?;
            if !ids.insert(component.component_id.as_str()) {
                return Err(SolvencyError::AmbiguousComposition);
            }
            total += component.volume_fraction_0_1;
            resin |= component.role == "RESIN";
        }
        if (total - 1.0).abs() > 1e-6 || !resin {
            return Err(SolvencyError::Range("component volume fractions/resin"));
        }
        Ok(())
    }

    pub fn validate_measured(&self) -> Result<(), SolvencyError> {
        self.validate_conditions()?;
        if self.microscopy_single_phase_1h.is_none()
            || self.microscopy_single_phase_24h.is_none()
            || self
                .turbidity_ntu_1h
                .is_none_or(|value| !value.is_finite() || value < 0.0)
            || self
                .turbidity_ntu_24h
                .is_none_or(|value| !value.is_finite() || value < 0.0)
        {
            return Err(SolvencyError::Range(
                "paired microscopy/turbidity endpoints",
            ));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("observation serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PairCoefficientV1 {
    pub component_a: String,
    pub component_b: String,
    pub a: f64,
    pub b_kelvin: f64,
    pub redlich_kister: f64,
    pub covariance: [[f64; 3]; 3],
}

impl PairCoefficientV1 {
    fn validate(&self) -> Result<(), SolvencyError> {
        require_text("pair.component_a", &self.component_a)?;
        require_text("pair.component_b", &self.component_b)?;
        if self.component_a >= self.component_b
            || [self.a, self.b_kelvin, self.redlich_kister]
                .iter()
                .any(|value| !value.is_finite())
            || self
                .covariance
                .iter()
                .flatten()
                .any(|value| !value.is_finite())
            || !symmetric_positive_semidefinite_3x3(&self.covariance)
        {
            return Err(SolvencyError::Range("pair coefficient"));
        }
        Ok(())
    }

    fn chi(&self, temperature_k: f64, phi_a: f64, phi_b: f64, sigma: f64) -> f64 {
        let standard_error = (self.covariance[0][0]
            + self.covariance[1][1] / temperature_k.powi(2)
            + self.covariance[2][2] * (phi_a - phi_b).powi(2))
        .max(0.0)
        .sqrt();
        self.a
            + self.b_kelvin / temperature_k
            + self.redlich_kister * (phi_a - phi_b)
            + sigma * standard_error
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct SolvencyParameterArtifactV1 {
    pub schema: String,
    pub module_id: String,
    pub parameter_id: String,
    pub component_structure_hashes: BTreeMap<String, String>,
    pub component_roles: BTreeMap<String, String>,
    pub resin_oligomer_distributions: BTreeMap<String, Vec<OligomerFractionV1>>,
    pub pair_coefficients: Vec<PairCoefficientV1>,
    pub temperature_bounds_c: [f64; 2],
    pub composition_floor_0_1: f64,
    pub generator_versions: BTreeMap<String, String>,
    pub parent_hashes: BTreeMap<String, String>,
    pub rights_receipt_hashes: Vec<String>,
    pub rights_eligible: bool,
    pub quantum_generator_license_resolved: bool,
}

impl SolvencyParameterArtifactV1 {
    pub fn validate(&self) -> Result<(), SolvencyError> {
        require_identity(&self.schema, PARAMETER_ARTIFACT_SCHEMA, &self.module_id)?;
        require_text("parameter_id", &self.parameter_id)?;
        if !self.rights_eligible || !self.quantum_generator_license_resolved {
            return Err(SolvencyError::Rights);
        }
        if self.component_structure_hashes.len() < 2
            || self.component_structure_hashes.len() != self.component_roles.len()
            || self.temperature_bounds_c[0] > self.temperature_bounds_c[1]
            || self
                .temperature_bounds_c
                .iter()
                .any(|value| !value.is_finite())
            || !finite_between(self.composition_floor_0_1, 0.0, 0.1)
            || self.generator_versions.is_empty()
        {
            return Err(SolvencyError::Range("parameter artifact"));
        }
        for hash in self
            .component_structure_hashes
            .values()
            .chain(self.parent_hashes.values())
            .chain(self.rights_receipt_hashes.iter())
        {
            require_hash("parameter parent hash", hash)?;
        }
        for (grade, distribution) in &self.resin_oligomer_distributions {
            require_text("resin grade", grade)?;
            if distribution.is_empty()
                || (distribution
                    .iter()
                    .map(|row| row.mole_fraction_0_1)
                    .sum::<f64>()
                    - 1.0)
                    .abs()
                    > 1e-6
            {
                return Err(SolvencyError::Range("artifact oligomer distribution"));
            }
        }
        let ids: Vec<_> = self.component_structure_hashes.keys().collect();
        let expected = ids.len() * (ids.len() - 1) / 2;
        let mut seen = BTreeSet::new();
        for pair in &self.pair_coefficients {
            pair.validate()?;
            if !self
                .component_structure_hashes
                .contains_key(&pair.component_a)
                || !self
                    .component_structure_hashes
                    .contains_key(&pair.component_b)
                || !seen.insert((pair.component_a.as_str(), pair.component_b.as_str()))
            {
                return Err(SolvencyError::PairMatrix);
            }
        }
        if seen.len() != expected {
            return Err(SolvencyError::PairMatrix);
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("parameters serialize"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ComponentParameterV2 {
    pub component_id: String,
    pub structure_sha256: String,
    pub role: String,
    pub lot_id: String,
    pub parameter_origin: String,
    pub identity_calibration_sha256: String,
    pub resin_grade: Option<String>,
    pub measured_oligomer_distribution: Vec<OligomerFractionV1>,
    pub sec_gpc_calibration_sha256: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct AdmissibleComponentSetV2 {
    pub set_id: String,
    pub component_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct SolvencyParameterArtifactV2 {
    pub schema: String,
    pub module_id: String,
    pub parameter_id: String,
    pub components: BTreeMap<String, ComponentParameterV2>,
    pub admissible_component_sets: Vec<AdmissibleComponentSetV2>,
    pub admissible_component_sets_sha256: String,
    pub pair_coefficients: Vec<PairCoefficientV1>,
    pub pair_calibration_hashes: BTreeMap<String, String>,
    pub temperature_bounds_c: [f64; 2],
    pub composition_floor_0_1: f64,
    pub parent_hashes: BTreeMap<String, String>,
    pub rights_receipt_hashes: Vec<String>,
    pub rights_eligible: bool,
}

impl SolvencyParameterArtifactV2 {
    pub fn validate(&self) -> Result<(), SolvencyError> {
        require_identity(&self.schema, PARAMETER_ARTIFACT_V2_SCHEMA, &self.module_id)?;
        require_text("parameter_id", &self.parameter_id)?;
        require_hash(
            "admissible_component_sets_sha256",
            &self.admissible_component_sets_sha256,
        )?;
        if stable_hash(
            &serde_json::to_value(&self.admissible_component_sets)
                .map_err(|error| SolvencyError::Json(error.to_string()))?,
        ) != self.admissible_component_sets_sha256
            || !self.rights_eligible
            || self.components.len() < 2
            || self.admissible_component_sets.is_empty()
            || self.temperature_bounds_c[0] > self.temperature_bounds_c[1]
            || self
                .temperature_bounds_c
                .iter()
                .any(|value| !value.is_finite())
            || !finite_between(self.composition_floor_0_1, 0.0, 0.1)
        {
            return Err(SolvencyError::Range("parameter artifact v2"));
        }
        for hash in self
            .parent_hashes
            .values()
            .chain(self.rights_receipt_hashes.iter())
        {
            require_hash("parameter parent hash", hash)?;
        }
        for (id, component) in &self.components {
            if id != &component.component_id {
                return Err(SolvencyError::Parent);
            }
            for (field, value) in [
                ("component_id", component.component_id.as_str()),
                ("component_role", component.role.as_str()),
                ("component_lot", component.lot_id.as_str()),
                ("parameter_origin", component.parameter_origin.as_str()),
            ] {
                require_text(field, value)?;
            }
            require_hash("component_structure", &component.structure_sha256)?;
            require_hash(
                "identity_calibration_sha256",
                &component.identity_calibration_sha256,
            )?;
            if component.role == "RESIN" {
                if component.resin_grade.as_deref().is_none_or(str::is_empty)
                    || component.measured_oligomer_distribution.is_empty()
                    || component.sec_gpc_calibration_sha256.as_deref().is_none()
                    || component
                        .sec_gpc_calibration_sha256
                        .as_deref()
                        .is_some_and(|hash| {
                            require_hash("sec_gpc_calibration_sha256", hash).is_err()
                        })
                    || component.measured_oligomer_distribution.iter().any(|row| {
                        !finite_positive(row.degree_of_polymerization)
                            || !finite_between(row.mole_fraction_0_1, 0.0, 1.0)
                    })
                    || (component
                        .measured_oligomer_distribution
                        .iter()
                        .map(|row| row.mole_fraction_0_1)
                        .sum::<f64>()
                        - 1.0)
                        .abs()
                        > 1e-6
                {
                    return Err(SolvencyError::Range("measured resin distribution"));
                }
            } else if component.resin_grade.is_some()
                || !component.measured_oligomer_distribution.is_empty()
                || component.sec_gpc_calibration_sha256.is_some()
            {
                return Err(SolvencyError::Range("non-resin distribution"));
            }
        }

        let mut set_ids = BTreeSet::new();
        let mut expected_pairs = BTreeSet::<(String, String)>::new();
        for set in &self.admissible_component_sets {
            require_text("admissible_set_id", &set.set_id)?;
            if !set_ids.insert(set.set_id.as_str()) || set.component_ids.len() < 2 {
                return Err(SolvencyError::PairMatrix);
            }
            let mut components = set.component_ids.clone();
            components.sort();
            components.dedup();
            if components != set.component_ids
                || components
                    .iter()
                    .any(|id| !self.components.contains_key(id))
            {
                return Err(SolvencyError::PairMatrix);
            }
            for i in 0..components.len() {
                for j in (i + 1)..components.len() {
                    expected_pairs.insert((components[i].clone(), components[j].clone()));
                }
            }
        }
        let mut observed_pairs = BTreeSet::new();
        for pair in &self.pair_coefficients {
            pair.validate()?;
            let key = (pair.component_a.clone(), pair.component_b.clone());
            let calibration_key = format!("{}|{}", pair.component_a, pair.component_b);
            if !expected_pairs.contains(&key)
                || !observed_pairs.insert(key)
                || self
                    .pair_calibration_hashes
                    .get(&calibration_key)
                    .is_none_or(|hash| require_hash("pair calibration hash", hash).is_err())
            {
                return Err(SolvencyError::PairMatrix);
            }
        }
        let expected_calibrations: BTreeSet<_> = expected_pairs
            .iter()
            .map(|(a, b)| format!("{a}|{b}"))
            .collect();
        if observed_pairs != expected_pairs
            || self
                .pair_calibration_hashes
                .keys()
                .cloned()
                .collect::<BTreeSet<_>>()
                != expected_calibrations
        {
            return Err(SolvencyError::PairMatrix);
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("parameters serialize"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct SolvencyDatasetV1 {
    pub schema: String,
    pub module_id: String,
    pub dataset_id: String,
    pub parameter_artifact: SolvencyParameterArtifactV1,
    pub observations: Vec<SolvencyObservationV1>,
}

impl SolvencyDatasetV1 {
    pub fn validate(&self) -> Result<(), SolvencyError> {
        require_identity(&self.schema, DATASET_SCHEMA, &self.module_id)?;
        require_text("dataset_id", &self.dataset_id)?;
        self.parameter_artifact.validate()?;
        if self.observations.is_empty() {
            return Err(SolvencyError::Empty("observations"));
        }
        let mut ids = BTreeSet::new();
        for observation in &self.observations {
            observation.validate_measured()?;
            validate_observation_against_parameters(observation, &self.parameter_artifact)?;
            if !ids.insert(&observation.observation_id) {
                return Err(SolvencyError::Parent);
            }
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("dataset serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SplitAssignmentV1 {
    pub observation_id: String,
    pub blend_id: String,
    pub solvent_family_group: String,
    pub resin_lot_group: String,
    pub split: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SolvencySplitV1 {
    pub schema: String,
    pub module_id: String,
    pub split_id: String,
    pub dataset_sha256: String,
    pub assignments: Vec<SplitAssignmentV1>,
}

impl SolvencySplitV1 {
    pub fn validate(&self, dataset: Option<&SolvencyDatasetV1>) -> Result<(), SolvencyError> {
        require_identity(&self.schema, SPLIT_SCHEMA, &self.module_id)?;
        require_text("split_id", &self.split_id)?;
        require_hash("dataset_sha256", &self.dataset_sha256)?;
        let mut observations = BTreeSet::new();
        let mut blend_folds: BTreeMap<&str, &str> = BTreeMap::new();
        let mut family_folds: BTreeMap<&str, &str> = BTreeMap::new();
        for row in &self.assignments {
            for (field, value) in [
                ("observation_id", row.observation_id.as_str()),
                ("blend_id", row.blend_id.as_str()),
                ("solvent_family_group", row.solvent_family_group.as_str()),
                ("resin_lot_group", row.resin_lot_group.as_str()),
                ("split", row.split.as_str()),
            ] {
                require_text(field, value)?;
            }
            if !observations.insert(row.observation_id.as_str())
                || insert_fold(&mut blend_folds, &row.blend_id, &row.split)
                || insert_fold(&mut family_folds, &row.solvent_family_group, &row.split)
            {
                return Err(SolvencyError::Leakage);
            }
        }
        if let Some(dataset) = dataset {
            dataset.validate()?;
            if dataset.identity_hash() != self.dataset_sha256
                || observations.len() != dataset.observations.len()
                || dataset
                    .observations
                    .iter()
                    .any(|row| !observations.contains(row.observation_id.as_str()))
            {
                return Err(SolvencyError::Parent);
            }
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("split serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct SolvencyBenchmarkLockV1 {
    pub schema: String,
    pub module_id: String,
    pub benchmark_id: String,
    pub dataset_sha256: String,
    pub split_sha256: String,
    pub baselines: Vec<String>,
    pub hostile_nulls: Vec<String>,
    pub thresholds: BTreeMap<String, f64>,
    pub immutable: bool,
}

impl SolvencyBenchmarkLockV1 {
    pub fn validate(&self) -> Result<(), SolvencyError> {
        require_identity(&self.schema, BENCHMARK_LOCK_SCHEMA, &self.module_id)?;
        require_text("benchmark_id", &self.benchmark_id)?;
        require_hash("dataset_sha256", &self.dataset_sha256)?;
        require_hash("split_sha256", &self.split_sha256)?;
        for baseline in [
            "HSP_RED",
            "CONSTANT_CHI_FLORY_HUGGINS",
            "UNIFAC_FV",
            "RAW_OPENCOSMO",
        ] {
            if !self.baselines.iter().any(|value| value == baseline) {
                return Err(SolvencyError::Range("benchmark baselines"));
            }
        }
        if !self.immutable
            || self.hostile_nulls.is_empty()
            || self.thresholds.values().any(|value| !value.is_finite())
        {
            return Err(SolvencyError::Range("benchmark lock"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("lock serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct OutOfFoldPredictionV1 {
    pub observation_id: String,
    pub cluster_id: String,
    pub site_id: String,
    pub subgroup: String,
    pub observed_compatible: bool,
    pub predicted_compatible_probability: f64,
    pub baseline_compatible_probability: f64,
}

impl OutOfFoldPredictionV1 {
    fn validate(&self) -> Result<(), SolvencyError> {
        for (field, value) in [
            ("observation_id", self.observation_id.as_str()),
            ("cluster_id", self.cluster_id.as_str()),
            ("site_id", self.site_id.as_str()),
            ("subgroup", self.subgroup.as_str()),
        ] {
            require_text(field, value)?;
        }
        if !finite_between(self.predicted_compatible_probability, 0.0, 1.0)
            || !finite_between(self.baseline_compatible_probability, 0.0, 1.0)
        {
            return Err(SolvencyError::Range("out-of-fold probability"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct BenchmarkMetricsV1 {
    pub group_held_out_auroc: f64,
    pub clustered_bootstrap_auroc_lower_95: f64,
    pub brier_score: f64,
    pub expected_calibration_error: f64,
    pub incompatible_sensitivity: f64,
    pub high_confidence_false_compatible_rate: f64,
    pub minimum_subgroup_incompatible_sensitivity: f64,
    pub baseline_auroc: f64,
    pub theory_auroc_lift: f64,
    pub theory_auroc_lift_lower_95: f64,
    pub baseline_brier_score: f64,
    pub theory_brier_degradation: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct BenchmarkGateStatusV1 {
    pub auroc_at_least_0_80: bool,
    pub auroc_lower_at_least_0_70: bool,
    pub brier_at_most_0_15: bool,
    pub ece_at_most_0_10: bool,
    pub incompatible_sensitivity_at_least_0_90: bool,
    pub false_compatible_rate_at_most_0_10: bool,
    pub every_subgroup_sensitivity_at_least_0_75: bool,
    pub theory_auroc_lift_at_least_0_03: bool,
    pub theory_lift_lower_positive: bool,
    pub brier_degradation_at_most_0_01: bool,
    pub both_verifier_sites_non_reversing: bool,
}

impl BenchmarkGateStatusV1 {
    pub fn passed(&self) -> bool {
        self.auroc_at_least_0_80
            && self.auroc_lower_at_least_0_70
            && self.brier_at_most_0_15
            && self.ece_at_most_0_10
            && self.incompatible_sensitivity_at_least_0_90
            && self.false_compatible_rate_at_most_0_10
            && self.every_subgroup_sensitivity_at_least_0_75
            && self.theory_auroc_lift_at_least_0_03
            && self.theory_lift_lower_positive
            && self.brier_degradation_at_most_0_01
            && self.both_verifier_sites_non_reversing
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct BenchmarkReceiptV1 {
    pub schema: String,
    pub module_id: String,
    pub receipt_id: String,
    pub model_artifact_sha256: String,
    pub dataset_sha256: String,
    pub split_sha256: String,
    pub benchmark_lock_sha256: String,
    pub raw_file_manifest_sha256: String,
    pub prediction_hashes: BTreeMap<String, String>,
    pub metrics: BenchmarkMetricsV1,
    pub gate_status: BenchmarkGateStatusV1,
    pub estimator: String,
    pub l2_penalty: f64,
    pub seed: u64,
    pub passed: bool,
}

impl BenchmarkReceiptV1 {
    pub fn validate(&self) -> Result<(), SolvencyError> {
        require_identity(&self.schema, BENCHMARK_RECEIPT_SCHEMA, &self.module_id)?;
        require_text("receipt_id", &self.receipt_id)?;
        for (field, hash) in [
            ("model_artifact_sha256", self.model_artifact_sha256.as_str()),
            ("dataset_sha256", self.dataset_sha256.as_str()),
            ("split_sha256", self.split_sha256.as_str()),
            ("benchmark_lock_sha256", self.benchmark_lock_sha256.as_str()),
            (
                "raw_file_manifest_sha256",
                self.raw_file_manifest_sha256.as_str(),
            ),
        ] {
            require_hash(field, hash)?;
        }
        validate_hash_map(&self.prediction_hashes)?;
        if serde_json::to_value(&self.metrics)
            .expect("metrics serialize")
            .as_object()
            .expect("metrics are an object")
            .values()
            .any(|value| value.as_f64().is_none_or(|value| !value.is_finite()))
            || self.estimator != "STANDARDIZED_RIDGE_LOGISTIC"
            || self.l2_penalty != RESIDUAL_MODEL_L2
            || self.seed != RESIDUAL_MODEL_SEED
            || self.passed != self.gate_status.passed()
        {
            return Err(SolvencyError::Range("benchmark receipt"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("receipt serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct SolvencyModelArtifactV1 {
    pub schema: String,
    pub module_id: String,
    pub model_id: String,
    pub dataset_sha256: String,
    pub split_sha256: String,
    pub benchmark_lock_sha256: String,
    pub parameter_artifact_sha256: String,
    pub parameter_artifact: SolvencyParameterArtifactV1,
    pub classification_tpd_cutoff_rt: f64,
    pub temperature_bounds_c: [f64; 2],
    pub component_fraction_bounds: BTreeMap<String, [f64; 2]>,
    pub promotion_dataset_complete: bool,
    pub authority: String,
}

impl SolvencyModelArtifactV1 {
    pub fn validate(&self) -> Result<(), SolvencyError> {
        require_identity(&self.schema, MODEL_ARTIFACT_SCHEMA, &self.module_id)?;
        require_text("model_id", &self.model_id)?;
        for (field, hash) in [
            ("dataset_sha256", self.dataset_sha256.as_str()),
            ("split_sha256", self.split_sha256.as_str()),
            ("benchmark_lock_sha256", self.benchmark_lock_sha256.as_str()),
            (
                "parameter_artifact_sha256",
                self.parameter_artifact_sha256.as_str(),
            ),
        ] {
            require_hash(field, hash)?;
        }
        self.parameter_artifact.validate()?;
        if self.parameter_artifact.identity_hash() != self.parameter_artifact_sha256
            || !self.classification_tpd_cutoff_rt.is_finite()
            || self.temperature_bounds_c[0] > self.temperature_bounds_c[1]
            || self.authority != "SHADOW"
            || self.component_fraction_bounds.values().any(|range| {
                range[0] > range[1] || range.iter().any(|value| !finite_between(*value, 0.0, 1.0))
            })
        {
            return Err(SolvencyError::Range("model artifact"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ObservationBundleV1 {
    pub schema: String,
    pub module_id: String,
    pub candidate_id: String,
    pub observation: SolvencyObservationV1,
}

impl ObservationBundleV1 {
    pub fn validate(&self) -> Result<(), SolvencyError> {
        require_identity(&self.schema, OBSERVATION_BUNDLE_SCHEMA, &self.module_id)?;
        require_text("candidate_id", &self.candidate_id)?;
        self.observation.validate_conditions()?;
        if self.observation.candidate_id != self.candidate_id {
            return Err(SolvencyError::Parent);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct SolvencyPredictionV1 {
    pub schema: String,
    pub module_id: String,
    pub candidate_id: String,
    pub authority: String,
    pub min_tpd_rt: Option<f64>,
    pub minimum_hessian_eigenvalue: Option<f64>,
    pub parameter_interval_min_tpd_rt: Option<ConfidenceIntervalV1>,
    pub computed_single_phase_fraction: Option<f64>,
    pub numeric_compatibility_prediction: Option<f64>,
    pub converged: bool,
    pub in_applicability_domain: bool,
    pub abstention_reasons: Vec<String>,
}

impl SolvencyPredictionV1 {
    fn abstain(candidate_id: &str, reason: impl Into<String>) -> Self {
        Self {
            schema: PREDICTION_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            candidate_id: candidate_id.into(),
            authority: "SHADOW".into(),
            min_tpd_rt: None,
            minimum_hessian_eigenvalue: None,
            parameter_interval_min_tpd_rt: None,
            computed_single_phase_fraction: None,
            numeric_compatibility_prediction: None,
            converged: false,
            in_applicability_domain: false,
            abstention_reasons: vec![reason.into()],
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct IndependentReviewV1 {
    pub schema: String,
    pub module_id: String,
    pub review_id: String,
    pub model_artifact_sha256: String,
    pub benchmark_receipt_sha256: String,
    pub reviewer_independent: bool,
    pub code_license_reviewed: bool,
    pub generator_license_reviewed: bool,
    pub limitations_accepted: bool,
}

impl IndependentReviewV1 {
    pub fn validate(&self) -> Result<(), SolvencyError> {
        require_identity(&self.schema, INDEPENDENT_REVIEW_SCHEMA, &self.module_id)?;
        require_text("review_id", &self.review_id)?;
        require_hash("model_artifact_sha256", &self.model_artifact_sha256)?;
        require_hash("benchmark_receipt_sha256", &self.benchmark_receipt_sha256)?;
        if !self.reviewer_independent
            || !self.code_license_reviewed
            || !self.generator_license_reviewed
            || !self.limitations_accepted
        {
            return Err(SolvencyError::Rights);
        }
        Ok(())
    }
}

pub fn evaluate_locked_benchmark(
    lock: &SolvencyBenchmarkLockV1,
    dataset: &SolvencyDatasetV1,
    split: &SolvencySplitV1,
    artifact: &SolvencyModelArtifactV1,
    raw_file_hashes: &BTreeMap<String, String>,
    predictions: &[OutOfFoldPredictionV1],
) -> Result<BenchmarkReceiptV1, SolvencyError> {
    dataset.validate()?;
    split.validate(Some(dataset))?;
    lock.validate()?;
    artifact.validate()?;
    validate_hash_map(raw_file_hashes)?;
    if lock.dataset_sha256 != dataset.identity_hash()
        || lock.split_sha256 != split.identity_hash()
        || artifact.dataset_sha256 != dataset.identity_hash()
        || artifact.split_sha256 != split.identity_hash()
        || artifact.benchmark_lock_sha256 != lock.identity_hash()
        || predictions.is_empty()
    {
        return Err(SolvencyError::Parent);
    }
    let expected: BTreeSet<_> = split
        .assignments
        .iter()
        .filter(|row| row.split != "FIT")
        .map(|row| row.observation_id.as_str())
        .collect();
    let mut observed = BTreeSet::new();
    for row in predictions {
        row.validate()?;
        if !expected.contains(row.observation_id.as_str())
            || !observed.insert(row.observation_id.as_str())
        {
            return Err(SolvencyError::Leakage);
        }
    }
    if observed != expected {
        return Err(SolvencyError::Parent);
    }
    let auroc = auc_score(predictions, false)?;
    let baseline_auroc = auc_score(predictions, true)?;
    let (auroc_lower, lift_lower) = clustered_auroc_lower_bounds(predictions)?;
    let count = predictions.len() as f64;
    let brier = predictions
        .iter()
        .map(|row| {
            let observed = if row.observed_compatible { 1.0 } else { 0.0 };
            (row.predicted_compatible_probability - observed).powi(2)
        })
        .sum::<f64>()
        / count;
    let baseline_brier = predictions
        .iter()
        .map(|row| {
            let observed = if row.observed_compatible { 1.0 } else { 0.0 };
            (row.baseline_compatible_probability - observed).powi(2)
        })
        .sum::<f64>()
        / count;
    let incompatible: Vec<_> = predictions
        .iter()
        .filter(|row| !row.observed_compatible)
        .collect();
    if incompatible.is_empty() {
        return Err(SolvencyError::Empty("incompatible observations"));
    }
    let sensitivity = incompatible
        .iter()
        .filter(|row| row.predicted_compatible_probability < 0.5)
        .count() as f64
        / incompatible.len() as f64;
    let high_confidence: Vec<_> = predictions
        .iter()
        .filter(|row| row.predicted_compatible_probability >= 0.90)
        .collect();
    let false_compatible_rate = if high_confidence.is_empty() {
        0.0
    } else {
        high_confidence
            .iter()
            .filter(|row| !row.observed_compatible)
            .count() as f64
            / high_confidence.len() as f64
    };
    let mut subgroup_sensitivity = BTreeMap::<&str, (usize, usize)>::new();
    for row in &incompatible {
        let entry = subgroup_sensitivity
            .entry(row.subgroup.as_str())
            .or_default();
        entry.1 += 1;
        entry.0 += usize::from(row.predicted_compatible_probability < 0.5);
    }
    let minimum_subgroup_sensitivity = subgroup_sensitivity
        .values()
        .map(|(correct, total)| *correct as f64 / *total as f64)
        .fold(1.0, f64::min);
    let ece = expected_calibration_error(predictions);
    let lift = auroc - baseline_auroc;
    let brier_degradation = brier - baseline_brier;
    let verifier_sites: BTreeSet<_> = predictions
        .iter()
        .filter(|row| !row.site_id.starts_with("PRIMARY"))
        .map(|row| row.site_id.as_str())
        .collect();
    let verifiers_non_reversing = verifier_sites.len() >= 2
        && verifier_sites.iter().all(|site| {
            let rows: Vec<_> = predictions
                .iter()
                .filter(|row| row.site_id == *site)
                .cloned()
                .collect();
            match (auc_score(&rows, false), auc_score(&rows, true)) {
                (Ok(theory), Ok(baseline)) => theory >= baseline,
                _ => false,
            }
        });
    let metrics = BenchmarkMetricsV1 {
        group_held_out_auroc: auroc,
        clustered_bootstrap_auroc_lower_95: auroc_lower,
        brier_score: brier,
        expected_calibration_error: ece,
        incompatible_sensitivity: sensitivity,
        high_confidence_false_compatible_rate: false_compatible_rate,
        minimum_subgroup_incompatible_sensitivity: minimum_subgroup_sensitivity,
        baseline_auroc,
        theory_auroc_lift: lift,
        theory_auroc_lift_lower_95: lift_lower,
        baseline_brier_score: baseline_brier,
        theory_brier_degradation: brier_degradation,
    };
    let gate_status = BenchmarkGateStatusV1 {
        auroc_at_least_0_80: auroc >= 0.80,
        auroc_lower_at_least_0_70: auroc_lower >= 0.70,
        brier_at_most_0_15: brier <= 0.15,
        ece_at_most_0_10: ece <= 0.10,
        incompatible_sensitivity_at_least_0_90: sensitivity >= 0.90,
        false_compatible_rate_at_most_0_10: false_compatible_rate <= 0.10,
        every_subgroup_sensitivity_at_least_0_75: minimum_subgroup_sensitivity >= 0.75,
        theory_auroc_lift_at_least_0_03: lift >= 0.03,
        theory_lift_lower_positive: lift_lower > 0.0,
        brier_degradation_at_most_0_01: brier_degradation <= 0.01,
        both_verifier_sites_non_reversing: verifiers_non_reversing,
    };
    let prediction_hashes: BTreeMap<_, _> = predictions
        .iter()
        .map(|row| {
            (
                row.observation_id.clone(),
                stable_hash(&serde_json::to_value(row).expect("prediction serializes")),
            )
        })
        .collect();
    let raw_manifest = serde_json::to_value(raw_file_hashes)
        .map_err(|error| SolvencyError::Json(error.to_string()))?;
    let seed = json!({
        "model": stable_hash(&serde_json::to_value(artifact).expect("artifact serializes")),
        "predictions": prediction_hashes,
    });
    let mut receipt = BenchmarkReceiptV1 {
        schema: BENCHMARK_RECEIPT_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        receipt_id: format!("solvency-benchmark-{}", &stable_hash(&seed)[..16]),
        model_artifact_sha256: stable_hash(
            &serde_json::to_value(artifact).expect("artifact serializes"),
        ),
        dataset_sha256: dataset.identity_hash(),
        split_sha256: split.identity_hash(),
        benchmark_lock_sha256: lock.identity_hash(),
        raw_file_manifest_sha256: stable_hash(&raw_manifest),
        prediction_hashes,
        metrics,
        gate_status,
        estimator: "STANDARDIZED_RIDGE_LOGISTIC".into(),
        l2_penalty: RESIDUAL_MODEL_L2,
        seed: RESIDUAL_MODEL_SEED,
        passed: false,
    };
    receipt.passed = receipt.gate_status.passed();
    receipt.validate()?;
    Ok(receipt)
}

pub fn gibbs_mix_rt(
    fractions: &[f64],
    segment_counts: &[f64],
    pairs: &[PairCoefficientV1],
    component_ids: &[String],
    temperature_k: f64,
    sigma: f64,
) -> Result<f64, SolvencyError> {
    if fractions.len() < 2
        || fractions.len() != segment_counts.len()
        || fractions.len() != component_ids.len()
        || !finite_positive(temperature_k)
        || fractions
            .iter()
            .any(|value| !value.is_finite() || *value <= 0.0 || *value >= 1.0)
        || segment_counts.iter().any(|value| !finite_positive(*value))
        || (fractions.iter().sum::<f64>() - 1.0).abs() > 1e-6
    {
        return Err(SolvencyError::Range("Gibbs inputs"));
    }
    let mut value = fractions
        .iter()
        .zip(segment_counts)
        .map(|(phi, count)| phi / count * phi.ln())
        .sum::<f64>();
    for i in 0..fractions.len() {
        for j in (i + 1)..fractions.len() {
            let pair = find_pair(pairs, &component_ids[i], &component_ids[j])?;
            value += pair.chi(temperature_k, fractions[i], fractions[j], sigma)
                * fractions[i]
                * fractions[j];
        }
    }
    Ok(value)
}

pub fn minimum_hessian_eigenvalue(
    fractions: &[f64],
    segment_counts: &[f64],
    pairs: &[PairCoefficientV1],
    component_ids: &[String],
    temperature_k: f64,
    sigma: f64,
) -> Result<f64, SolvencyError> {
    if fractions.len() == 2 {
        let phi = fractions[0];
        let h = 1e-4_f64.min(0.25 * phi.min(1.0 - phi));
        if h <= 0.0 {
            return Err(SolvencyError::Range("Hessian composition"));
        }
        let eval = |x: f64| {
            gibbs_mix_rt(
                &[x, 1.0 - x],
                segment_counts,
                pairs,
                component_ids,
                temperature_k,
                sigma,
            )
        };
        return Ok((eval(phi + h)? - 2.0 * eval(phi)? + eval(phi - h)?) / h.powi(2));
    }
    let dimension = fractions.len() - 1;
    let h = 1e-4;
    let base: Vec<_> = fractions[..dimension].to_vec();
    let evaluate = |independent: &[f64]| {
        let last = 1.0 - independent.iter().sum::<f64>();
        let mut all = independent.to_vec();
        all.push(last);
        gibbs_mix_rt(
            &all,
            segment_counts,
            pairs,
            component_ids,
            temperature_k,
            sigma,
        )
    };
    let center = evaluate(&base)?;
    let mut hessian = vec![vec![0.0; dimension]; dimension];
    for i in 0..dimension {
        let mut plus = base.clone();
        let mut minus = base.clone();
        plus[i] += h;
        minus[i] -= h;
        hessian[i][i] = (evaluate(&plus)? - 2.0 * center + evaluate(&minus)?) / h.powi(2);
        for j in (i + 1)..dimension {
            let mut pp = base.clone();
            let mut pm = base.clone();
            let mut mp = base.clone();
            let mut mm = base.clone();
            pp[i] += h;
            pp[j] += h;
            pm[i] += h;
            pm[j] -= h;
            mp[i] -= h;
            mp[j] += h;
            mm[i] -= h;
            mm[j] -= h;
            let value = (evaluate(&pp)? - evaluate(&pm)? - evaluate(&mp)? + evaluate(&mm)?)
                / (4.0 * h.powi(2));
            hessian[i][j] = value;
            hessian[j][i] = value;
        }
    }
    Ok(jacobi_min_eigenvalue(hessian))
}

pub fn tangent_plane_minimum_rt(
    feed: &[f64],
    segment_counts: &[f64],
    pairs: &[PairCoefficientV1],
    component_ids: &[String],
    temperature_k: f64,
    sigma: f64,
) -> Result<f64, SolvencyError> {
    let n = feed.len();
    let feed_g = gibbs_mix_rt(
        feed,
        segment_counts,
        pairs,
        component_ids,
        temperature_k,
        sigma,
    )?;
    let feed_gradient = simplex_gradient(
        feed,
        segment_counts,
        pairs,
        component_ids,
        temperature_k,
        sigma,
    )?;
    let tpd = |trial: &[f64]| -> Result<f64, SolvencyError> {
        Ok(gibbs_mix_rt(
            trial,
            segment_counts,
            pairs,
            component_ids,
            temperature_k,
            sigma,
        )? - feed_g
            - trial
                .iter()
                .zip(feed)
                .take(n - 1)
                .enumerate()
                .map(|(index, (trial, feed))| feed_gradient[index] * (trial - feed))
                .sum::<f64>())
    };
    let mut minimum = 0.0;
    if n == 2 {
        for index in 1..1_000 {
            let phi = index as f64 / 1_000.0;
            minimum = f64::min(minimum, tpd(&[phi, 1.0 - phi])?);
        }
        return Ok(minimum);
    }
    let mut converged = false;
    for start in deterministic_starts(n) {
        let mut point = start;
        let mut previous = tpd(&point)?;
        for iteration in 0..300 {
            let gradient = numerical_tpd_gradient(&point, &tpd)?;
            let step = 0.08 / (1.0 + iteration as f64 * 0.02);
            let mut next: Vec<_> = point
                .iter()
                .zip(&gradient)
                .map(|(value, gradient)| value - step * gradient)
                .collect();
            project_simplex_interior(&mut next);
            let value = tpd(&next)?;
            if (previous - value).abs() < 1e-10 {
                converged = true;
                point = next;
                break;
            }
            if value <= previous {
                point = next;
                previous = value;
            }
        }
        minimum = minimum.min(tpd(&point)?);
    }
    if converged {
        Ok(minimum)
    } else {
        Err(SolvencyError::NonConvergent)
    }
}

pub fn fit_model(
    dataset: &SolvencyDatasetV1,
    split: &SolvencySplitV1,
    lock: &SolvencyBenchmarkLockV1,
) -> Result<SolvencyModelArtifactV1, SolvencyError> {
    dataset.validate()?;
    split.validate(Some(dataset))?;
    lock.validate()?;
    if lock.dataset_sha256 != dataset.identity_hash() || lock.split_sha256 != split.identity_hash()
    {
        return Err(SolvencyError::Parent);
    }
    let fit_ids: BTreeSet<_> = split
        .assignments
        .iter()
        .filter(|row| row.split == "FIT")
        .map(|row| row.observation_id.as_str())
        .collect();
    let training: Vec<_> = dataset
        .observations
        .iter()
        .filter(|row| fit_ids.contains(row.observation_id.as_str()))
        .collect();
    if training.is_empty() {
        return Err(SolvencyError::Empty("FIT observations"));
    }
    let mut fraction_bounds: BTreeMap<String, [f64; 2]> = BTreeMap::new();
    for component_id in dataset.parameter_artifact.component_structure_hashes.keys() {
        let values: Vec<_> = training
            .iter()
            .filter_map(|row| {
                row.components
                    .iter()
                    .find(|component| &component.component_id == component_id)
                    .map(|component| component.volume_fraction_0_1)
            })
            .collect();
        if values.len() != training.len() {
            return Err(SolvencyError::PairMatrix);
        }
        fraction_bounds.insert(
            component_id.clone(),
            [
                values.iter().copied().fold(f64::INFINITY, f64::min),
                values.iter().copied().fold(f64::NEG_INFINITY, f64::max),
            ],
        );
    }
    let unique_blends = training
        .iter()
        .map(|row| row.blend_id.as_str())
        .collect::<BTreeSet<_>>()
        .len();
    let family_groups = training
        .iter()
        .map(|row| row.solvent_family_group.as_str())
        .collect::<BTreeSet<_>>()
        .len();
    let resin_groups = training
        .iter()
        .map(|row| (row.resin_grade.as_str(), row.resin_lot.as_str()))
        .collect::<BTreeSet<_>>()
        .len();
    let temperatures = training
        .iter()
        .map(|row| row.temperature_c.round() as i64)
        .collect::<BTreeSet<_>>();
    let promotion_dataset_complete = unique_blends >= 96
        && family_groups >= 4
        && resin_groups >= 3
        && [10_i64, 25, 40]
            .iter()
            .all(|temperature| temperatures.contains(temperature));
    let parameter_hash = dataset.parameter_artifact.identity_hash();
    let seed = json!({
        "dataset": dataset.identity_hash(),
        "split": split.identity_hash(),
        "lock": lock.identity_hash(),
        "parameters": parameter_hash,
    });
    let artifact = SolvencyModelArtifactV1 {
        schema: MODEL_ARTIFACT_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        model_id: format!("carrier-solvency-{}", &stable_hash(&seed)[..16]),
        dataset_sha256: dataset.identity_hash(),
        split_sha256: split.identity_hash(),
        benchmark_lock_sha256: lock.identity_hash(),
        parameter_artifact_sha256: parameter_hash,
        parameter_artifact: dataset.parameter_artifact.clone(),
        classification_tpd_cutoff_rt: 0.0,
        temperature_bounds_c: dataset.parameter_artifact.temperature_bounds_c,
        component_fraction_bounds: fraction_bounds,
        promotion_dataset_complete,
        authority: "SHADOW".into(),
    };
    artifact.validate()?;
    Ok(artifact)
}

pub fn predict(
    artifact: &SolvencyModelArtifactV1,
    observation: &SolvencyObservationV1,
) -> Result<SolvencyPredictionV1, SolvencyError> {
    artifact.validate()?;
    observation.validate_conditions()?;
    validate_observation_against_parameters(observation, &artifact.parameter_artifact)?;
    if !in_domain(observation, artifact) {
        return Ok(SolvencyPredictionV1::abstain(
            &observation.candidate_id,
            "temperature, composition, component, resin distribution, or structure is outside the locked domain",
        ));
    }
    let mut components = observation.components.clone();
    components.sort_by(|left, right| left.component_id.cmp(&right.component_id));
    let fractions: Vec<_> = components
        .iter()
        .map(|row| row.volume_fraction_0_1)
        .collect();
    let counts: Vec<_> = components.iter().map(effective_segment_count).collect();
    let ids: Vec<_> = components
        .iter()
        .map(|row| row.component_id.clone())
        .collect();
    let temperature_k = observation.temperature_c + 273.15;
    let mut tpds = Vec::new();
    for sigma in [-1.645, 0.0, 1.645] {
        tpds.push(tangent_plane_minimum_rt(
            &fractions,
            &counts,
            &artifact.parameter_artifact.pair_coefficients,
            &ids,
            temperature_k,
            sigma,
        )?);
    }
    let center = tpds[1];
    let hessian = minimum_hessian_eigenvalue(
        &fractions,
        &counts,
        &artifact.parameter_artifact.pair_coefficients,
        &ids,
        temperature_k,
        0.0,
    )?;
    let stable_count = tpds
        .iter()
        .filter(|value| **value >= artifact.classification_tpd_cutoff_rt && hessian >= -1e-6)
        .count();
    Ok(SolvencyPredictionV1 {
        schema: PREDICTION_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        candidate_id: observation.candidate_id.clone(),
        authority: "SHADOW".into(),
        min_tpd_rt: Some(center),
        minimum_hessian_eigenvalue: Some(hessian),
        parameter_interval_min_tpd_rt: Some(ConfidenceIntervalV1 {
            lower: tpds.iter().copied().fold(f64::INFINITY, f64::min),
            upper: tpds.iter().copied().fold(f64::NEG_INFINITY, f64::max),
            confidence: 0.9,
            method: "PAIR_COVARIANCE_DETERMINISTIC_SIGMA_POINTS".into(),
        }),
        computed_single_phase_fraction: Some(stable_count as f64 / tpds.len() as f64),
        numeric_compatibility_prediction: None,
        converged: true,
        in_applicability_domain: true,
        abstention_reasons: Vec::new(),
    })
}

pub fn evaluate(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> ModuleResult {
    let abstain = |reason: String| {
        let prediction = SolvencyPredictionV1::abstain(candidate.candidate_id(), reason.clone());
        result_from_prediction(candidate, &prediction, Some(reason))
    };
    let Some(value) = features.values.get(HOST_FEATURE_KEY) else {
        return abstain(format!(
            "missing host FeatureSnapshot key {HOST_FEATURE_KEY}"
        ));
    };
    let binding: VerifiedFormulationModelInputV2 = match serde_json::from_value(value.clone()) {
        Ok(value) => value,
        Err(error) => return abstain(format!("invalid host binding JSON: {error}")),
    };
    if let Err(error) =
        binding.validate_candidate(candidate.candidate_id(), candidate.contract_hash_v1())
    {
        return abstain(error.to_string());
    }
    if binding.module_id != MODULE_ID {
        return abstain("module identity is invalid".into());
    }
    let receipt: BenchmarkReceiptV1 =
        match serde_json::from_value(binding.evaluation_receipt.clone()) {
            Ok(value) => value,
            Err(error) => return abstain(format!("invalid benchmark receipt: {error}")),
        };
    if let Err(error) = receipt.validate() {
        return abstain(error.to_string());
    }
    let review: IndependentReviewV1 =
        match serde_json::from_value(binding.independent_review_receipt.clone()) {
            Ok(value) => value,
            Err(error) => return abstain(format!("invalid independent review: {error}")),
        };
    if let Err(error) = review.validate() {
        return abstain(error.to_string());
    }
    if !receipt.passed
        || review.model_artifact_sha256 != binding.model_artifact_sha256
        || review.benchmark_receipt_sha256 != binding.evaluation_receipt_sha256
    {
        return abstain("benchmark or independent-review binding is invalid".into());
    }
    let artifact: SolvencyModelArtifactV1 = match serde_json::from_value(binding.model_artifact) {
        Ok(value) => value,
        Err(error) => return abstain(format!("invalid model artifact: {error}")),
    };
    let bundle: ObservationBundleV1 = match serde_json::from_value(binding.observation_bundle) {
        Ok(value) => value,
        Err(error) => return abstain(format!("invalid observation bundle: {error}")),
    };
    if let Err(error) = bundle.validate() {
        return abstain(error.to_string());
    }
    match predict(&artifact, &bundle.observation) {
        Ok(prediction) => result_from_prediction(candidate, &prediction, None),
        Err(error) => abstain(error.to_string()),
    }
}

fn result_from_prediction(
    candidate: &CandidateEnvelope,
    prediction: &SolvencyPredictionV1,
    reason: Option<String>,
) -> ModuleResult {
    let available = prediction.min_tpd_rt.is_some();
    ModuleResult {
        status: if available { "NO_AUTHORITY".into() } else { "INSUFFICIENT_INPUT".into() },
        score_0_1: None,
        objective_values: BTreeMap::new(),
        metrics: BTreeMap::from([
            ("candidate_contract_hash_v1".into(), json!(candidate.contract_hash_v1())),
            ("ranking_quarantine".into(), Value::Bool(true)),
            ("scientific_applicability".into(), json!(if available { "UNPIGMENTED_CARRIER_SUBMIXTURE_ONLY" } else { "UNVALIDATED" })),
            ("min_tpd_rt".into(), json!(prediction.min_tpd_rt)),
            ("minimum_hessian_eigenvalue".into(), json!(prediction.minimum_hessian_eigenvalue)),
            ("computed_single_phase_fraction".into(), json!(prediction.computed_single_phase_fraction)),
            ("numeric_compatibility_prediction".into(), Value::Null),
            ("prediction".into(), serde_json::to_value(prediction).expect("prediction serializes")),
        ]),
        gates: BTreeMap::from([
            ("host_verified_artifact_and_receipt".into(), Value::Bool(available)),
            ("in_applicability_domain".into(), Value::Bool(prediction.in_applicability_domain)),
            ("constraint_only".into(), Value::Bool(true)),
        ]),
        uncertainty: BTreeMap::from([(
            "min_tpd_parameter_90".into(),
            json!(prediction.parameter_interval_min_tpd_rt),
        )]),
        missing_inputs: reason.into_iter().collect(),
        explanations: vec!["The deterministic phase-stability result applies only to the unpigmented liquid carrier/resin submixture; the reported fraction is not a compatibility probability.".into()],
        source_refs: vec![
            "https://doi.org/10.1063/1.1723621".into(),
            "https://doi.org/10.1016/0378-3812(82)85001-2".into(),
            "https://doi.org/10.1016/j.fluid.2022.113472".into(),
        ],
        evidence_scope: "UNPIGMENTED_CARRIER_SOLVENCY_SHADOW_ONLY".into(),
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ContractKind {
    Observation,
    Dataset,
    Split,
    BenchmarkLock,
    ParameterArtifact,
    ParameterArtifactV2,
    ModelArtifact,
    Prediction,
    IndependentReview,
    BenchmarkReceipt,
}

pub fn preflight(kind: ContractKind, value: Value) -> Result<(String, String), SolvencyError> {
    match kind {
        ContractKind::Observation => {
            let contract: SolvencyObservationV1 = decode(value)?;
            contract.validate_conditions()?;
            Ok((contract.schema, contract.observation_id))
        }
        ContractKind::Dataset => {
            let contract: SolvencyDatasetV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.dataset_id))
        }
        ContractKind::Split => {
            let contract: SolvencySplitV1 = decode(value)?;
            contract.validate(None)?;
            Ok((contract.schema, contract.split_id))
        }
        ContractKind::BenchmarkLock => {
            let contract: SolvencyBenchmarkLockV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.benchmark_id))
        }
        ContractKind::ParameterArtifact => {
            let contract: SolvencyParameterArtifactV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.parameter_id))
        }
        ContractKind::ParameterArtifactV2 => {
            let contract: SolvencyParameterArtifactV2 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.parameter_id))
        }
        ContractKind::ModelArtifact => {
            let contract: SolvencyModelArtifactV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.model_id))
        }
        ContractKind::Prediction => {
            let contract: SolvencyPredictionV1 = decode(value)?;
            if contract.schema != PREDICTION_SCHEMA || contract.module_id != MODULE_ID {
                return Err(SolvencyError::Identity);
            }
            Ok((contract.schema, contract.candidate_id))
        }
        ContractKind::IndependentReview => {
            let contract: IndependentReviewV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.review_id))
        }
        ContractKind::BenchmarkReceipt => {
            let contract: BenchmarkReceiptV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.receipt_id))
        }
    }
}

fn validate_observation_against_parameters(
    observation: &SolvencyObservationV1,
    parameters: &SolvencyParameterArtifactV1,
) -> Result<(), SolvencyError> {
    let observed: BTreeSet<_> = observation
        .components
        .iter()
        .map(|row| row.component_id.as_str())
        .collect();
    let parameterized: BTreeSet<_> = parameters
        .component_structure_hashes
        .keys()
        .map(String::as_str)
        .collect();
    if observed != parameterized {
        return Err(SolvencyError::PairMatrix);
    }
    for component in &observation.components {
        if parameters
            .component_structure_hashes
            .get(&component.component_id)
            != Some(&component.structure_sha256)
            || parameters.component_roles.get(&component.component_id) != Some(&component.role)
        {
            return Err(SolvencyError::Parent);
        }
        if component.role == "RESIN"
            && parameters
                .resin_oligomer_distributions
                .get(&observation.resin_grade)
                != Some(&component.oligomer_distribution)
        {
            return Err(SolvencyError::Parent);
        }
    }
    Ok(())
}

fn in_domain(observation: &SolvencyObservationV1, artifact: &SolvencyModelArtifactV1) -> bool {
    observation.temperature_c >= artifact.temperature_bounds_c[0]
        && observation.temperature_c <= artifact.temperature_bounds_c[1]
        && observation.components.iter().all(|component| {
            artifact
                .component_fraction_bounds
                .get(&component.component_id)
                .is_some_and(|range| {
                    component.volume_fraction_0_1 >= range[0]
                        && component.volume_fraction_0_1 <= range[1]
                })
        })
}

fn effective_segment_count(component: &CarrierComponentV1) -> f64 {
    if component.role == "RESIN" {
        component
            .oligomer_distribution
            .iter()
            .map(|row| row.degree_of_polymerization * row.mole_fraction_0_1)
            .sum()
    } else {
        component.segment_count
    }
}

fn find_pair<'a>(
    pairs: &'a [PairCoefficientV1],
    left: &str,
    right: &str,
) -> Result<&'a PairCoefficientV1, SolvencyError> {
    let (a, b) = if left < right {
        (left, right)
    } else {
        (right, left)
    };
    pairs
        .iter()
        .find(|pair| pair.component_a == a && pair.component_b == b)
        .ok_or(SolvencyError::PairMatrix)
}

fn simplex_gradient(
    fractions: &[f64],
    segment_counts: &[f64],
    pairs: &[PairCoefficientV1],
    component_ids: &[String],
    temperature_k: f64,
    sigma: f64,
) -> Result<Vec<f64>, SolvencyError> {
    let mut gradient = Vec::with_capacity(fractions.len() - 1);
    for index in 0..fractions.len() - 1 {
        let h = EPSILON.min(0.25 * fractions[index].min(fractions[fractions.len() - 1]));
        if h <= 0.0 {
            return Err(SolvencyError::Range("gradient composition"));
        }
        let mut plus = fractions.to_vec();
        let mut minus = fractions.to_vec();
        plus[index] += h;
        plus[fractions.len() - 1] -= h;
        minus[index] -= h;
        minus[fractions.len() - 1] += h;
        gradient.push(
            (gibbs_mix_rt(
                &plus,
                segment_counts,
                pairs,
                component_ids,
                temperature_k,
                sigma,
            )? - gibbs_mix_rt(
                &minus,
                segment_counts,
                pairs,
                component_ids,
                temperature_k,
                sigma,
            )?) / (2.0 * h),
        );
    }
    Ok(gradient)
}

fn deterministic_starts(n: usize) -> Vec<Vec<f64>> {
    let mut starts = vec![vec![1.0 / n as f64; n]];
    for major in 0..n {
        let mut point = vec![0.1 / (n - 1) as f64; n];
        point[major] = 0.9;
        starts.push(point);
    }
    starts
}

fn numerical_tpd_gradient<F>(point: &[f64], function: &F) -> Result<Vec<f64>, SolvencyError>
where
    F: Fn(&[f64]) -> Result<f64, SolvencyError>,
{
    let mut gradient = vec![0.0; point.len()];
    for index in 0..point.len() {
        let other = (index + 1) % point.len();
        let h = 1e-6_f64.min(0.25 * point[index].min(point[other]));
        let mut plus = point.to_vec();
        let mut minus = point.to_vec();
        plus[index] += h;
        plus[other] -= h;
        minus[index] -= h;
        minus[other] += h;
        gradient[index] = (function(&plus)? - function(&minus)?) / (2.0 * h);
    }
    let mean = gradient.iter().sum::<f64>() / gradient.len() as f64;
    for value in &mut gradient {
        *value -= mean;
    }
    Ok(gradient)
}

fn project_simplex_interior(values: &mut [f64]) {
    for value in values.iter_mut() {
        *value = value.max(1e-6);
    }
    let total = values.iter().sum::<f64>();
    for value in values.iter_mut() {
        *value /= total;
    }
}

fn jacobi_min_eigenvalue(mut matrix: Vec<Vec<f64>>) -> f64 {
    let n = matrix.len();
    for _ in 0..50 * n * n {
        let mut p = 0;
        let mut q = 0;
        let mut maximum = 0.0;
        for (i, row) in matrix.iter().enumerate() {
            for (j, value) in row.iter().enumerate().skip(i + 1) {
                if value.abs() > maximum {
                    maximum = value.abs();
                    p = i;
                    q = j;
                }
            }
        }
        if maximum < 1e-10 {
            break;
        }
        let angle = 0.5 * (2.0 * matrix[p][q]).atan2(matrix[q][q] - matrix[p][p]);
        let (sin, cos) = angle.sin_cos();
        let app =
            cos * cos * matrix[p][p] - 2.0 * sin * cos * matrix[p][q] + sin * sin * matrix[q][q];
        let aqq =
            sin * sin * matrix[p][p] + 2.0 * sin * cos * matrix[p][q] + cos * cos * matrix[q][q];
        for k in (0..n).filter(|index| *index != p && *index != q) {
            let akp = matrix[k][p];
            let akq = matrix[k][q];
            matrix[k][p] = cos * akp - sin * akq;
            matrix[p][k] = matrix[k][p];
            matrix[k][q] = sin * akp + cos * akq;
            matrix[q][k] = matrix[k][q];
        }
        matrix[p][p] = app;
        matrix[q][q] = aqq;
        matrix[p][q] = 0.0;
        matrix[q][p] = 0.0;
    }
    (0..n)
        .map(|index| matrix[index][index])
        .fold(f64::INFINITY, f64::min)
}

fn insert_fold<'a>(map: &mut BTreeMap<&'a str, &'a str>, key: &'a str, fold: &'a str) -> bool {
    map.insert(key, fold)
        .is_some_and(|existing| existing != fold)
}

fn symmetric_positive_semidefinite_3x3(matrix: &[[f64; 3]; 3]) -> bool {
    let tolerance = 1e-10;
    if (0..3).any(|i| {
        matrix[i][i] < -tolerance || (0..3).any(|j| (matrix[i][j] - matrix[j][i]).abs() > tolerance)
    }) {
        return false;
    }
    for i in 0..3 {
        for j in (i + 1)..3 {
            if matrix[i][i] * matrix[j][j] - matrix[i][j].powi(2) < -tolerance {
                return false;
            }
        }
    }
    let determinant = matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
    determinant >= -tolerance
}

fn auc_score(rows: &[OutOfFoldPredictionV1], baseline: bool) -> Result<f64, SolvencyError> {
    let compatible: Vec<_> = rows.iter().filter(|row| row.observed_compatible).collect();
    let incompatible: Vec<_> = rows.iter().filter(|row| !row.observed_compatible).collect();
    if compatible.is_empty() || incompatible.is_empty() {
        return Err(SolvencyError::Empty("both compatibility classes"));
    }
    let score = |row: &OutOfFoldPredictionV1| {
        if baseline {
            row.baseline_compatible_probability
        } else {
            row.predicted_compatible_probability
        }
    };
    let mut wins = 0.0;
    for positive in &compatible {
        for negative in &incompatible {
            wins += match score(positive).total_cmp(&score(negative)) {
                std::cmp::Ordering::Greater => 1.0,
                std::cmp::Ordering::Equal => 0.5,
                std::cmp::Ordering::Less => 0.0,
            };
        }
    }
    Ok(wins / (compatible.len() * incompatible.len()) as f64)
}

fn expected_calibration_error(rows: &[OutOfFoldPredictionV1]) -> f64 {
    let mut weighted = 0.0;
    for bin in 0..10 {
        let lower = bin as f64 / 10.0;
        let upper = (bin + 1) as f64 / 10.0;
        let members: Vec<_> = rows
            .iter()
            .filter(|row| {
                row.predicted_compatible_probability >= lower
                    && (row.predicted_compatible_probability < upper
                        || bin == 9 && row.predicted_compatible_probability == 1.0)
            })
            .collect();
        if members.is_empty() {
            continue;
        }
        let confidence = members
            .iter()
            .map(|row| row.predicted_compatible_probability)
            .sum::<f64>()
            / members.len() as f64;
        let frequency = members.iter().filter(|row| row.observed_compatible).count() as f64
            / members.len() as f64;
        weighted += members.len() as f64 / rows.len() as f64 * (confidence - frequency).abs();
    }
    weighted
}

fn clustered_auroc_lower_bounds(
    rows: &[OutOfFoldPredictionV1],
) -> Result<(f64, f64), SolvencyError> {
    let mut clusters = BTreeMap::<&str, Vec<&OutOfFoldPredictionV1>>::new();
    for row in rows {
        clusters
            .entry(row.cluster_id.as_str())
            .or_default()
            .push(row);
    }
    if clusters.len() < 2 {
        let theory = auc_score(rows, false)?;
        return Ok((theory, theory - auc_score(rows, true)?));
    }
    let clusters: Vec<_> = clusters.values().collect();
    let mut state = RESIDUAL_MODEL_SEED;
    let mut aucs = Vec::with_capacity(10_000);
    let mut lifts = Vec::with_capacity(10_000);
    for _ in 0..10_000 {
        let mut sampled = Vec::new();
        for _ in 0..clusters.len() {
            state = state
                .wrapping_mul(6_364_136_223_846_793_005)
                .wrapping_add(1_442_695_040_888_963_407);
            sampled.extend(
                clusters[(state as usize) % clusters.len()]
                    .iter()
                    .map(|row| (*row).clone()),
            );
        }
        if let (Ok(theory), Ok(baseline)) = (auc_score(&sampled, false), auc_score(&sampled, true))
        {
            aucs.push(theory);
            lifts.push(theory - baseline);
        }
    }
    if aucs.len() < 250 {
        return Err(SolvencyError::Empty("class-balanced bootstrap replicates"));
    }
    aucs.sort_by(f64::total_cmp);
    lifts.sort_by(f64::total_cmp);
    let index = ((aucs.len() - 1) as f64 * 0.025).floor() as usize;
    Ok((aucs[index], lifts[index]))
}

fn decode<T: for<'de> Deserialize<'de>>(value: Value) -> Result<T, SolvencyError> {
    serde_json::from_value(value).map_err(|error| SolvencyError::Json(error.to_string()))
}

fn require_identity(schema: &str, expected: &str, module: &str) -> Result<(), SolvencyError> {
    if schema == expected && module == MODULE_ID {
        Ok(())
    } else {
        Err(SolvencyError::Identity)
    }
}

fn require_text(field: &'static str, value: &str) -> Result<(), SolvencyError> {
    if value.trim().is_empty() {
        Err(SolvencyError::Empty(field))
    } else {
        Ok(())
    }
}

fn require_hash(field: &'static str, value: &str) -> Result<(), SolvencyError> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(SolvencyError::Hash(field))
    }
}

fn validate_hash_map(values: &BTreeMap<String, String>) -> Result<(), SolvencyError> {
    if values.is_empty() {
        return Err(SolvencyError::Empty("raw_file_hashes"));
    }
    for (path, hash) in values {
        require_text("raw file path", path)?;
        require_hash("raw file hash", hash)?;
    }
    Ok(())
}

fn finite_positive(value: f64) -> bool {
    value.is_finite() && value > 0.0
}

fn finite_between(value: f64, lower: f64, upper: f64) -> bool {
    value.is_finite() && value >= lower && value <= upper
}

/// Hansen distance squared between a solvent and a polymer point in
/// (delta_d, delta_p, delta_h) MPa^0.5 space. Formula
/// `Ra^2 = 4*(dD_s - dD_p)^2 + (dP_s - dP_p)^2 + (dH_s - dH_p)^2` is Hansen's
/// three-parameter solubility distance. Fails closed on non-finite or
/// negative Hansen parameters; those are unphysical for real solubility
/// parameters and reject candidate-supplied garbage.
pub fn hansen_ra_squared(
    solvent_dd: f64,
    solvent_dp: f64,
    solvent_dh: f64,
    polymer_dd: f64,
    polymer_dp: f64,
    polymer_dh: f64,
) -> Option<f64> {
    let inputs = [solvent_dd, solvent_dp, solvent_dh, polymer_dd, polymer_dp, polymer_dh];
    if inputs.iter().any(|value| !value.is_finite() || *value < 0.0) {
        return None;
    }
    let dd = solvent_dd - polymer_dd;
    let dp = solvent_dp - polymer_dp;
    let dh = solvent_dh - polymer_dh;
    let ra_squared = 4.0 * dd * dd + dp * dp + dh * dh;
    ra_squared.is_finite().then_some(ra_squared)
}

/// Hansen relative energy difference (RED) between a solvent point and a
/// polymer's Hansen sphere of interaction radius `polymer_r`. RED < 1
/// means the pair is predicted compatible (inside the sphere); RED > 1
/// means predicted incompatible (outside). Fails closed on non-finite or
/// non-positive radius.
pub fn hansen_red(
    solvent_dd: f64,
    solvent_dp: f64,
    solvent_dh: f64,
    polymer_dd: f64,
    polymer_dp: f64,
    polymer_dh: f64,
    polymer_r: f64,
) -> Option<f64> {
    if !polymer_r.is_finite() || polymer_r <= 0.0 {
        return None;
    }
    let ra_squared =
        hansen_ra_squared(solvent_dd, solvent_dp, solvent_dh, polymer_dd, polymer_dp, polymer_dh)?;
    let ra = ra_squared.sqrt();
    let red = ra / polymer_r;
    red.is_finite().then_some(red)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pair(chi: f64) -> PairCoefficientV1 {
        PairCoefficientV1 {
            component_a: "a".into(),
            component_b: "b".into(),
            a: chi,
            b_kelvin: 0.0,
            redlich_kister: 0.0,
            covariance: [[0.0; 3]; 3],
        }
    }

    fn parameter_artifact(covariance: f64) -> SolvencyParameterArtifactV1 {
        SolvencyParameterArtifactV1 {
            schema: PARAMETER_ARTIFACT_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            parameter_id: "parameters-1".into(),
            component_structure_hashes: BTreeMap::from([
                ("resin".into(), "a".repeat(64)),
                ("solvent".into(), "b".repeat(64)),
            ]),
            component_roles: BTreeMap::from([
                ("resin".into(), "RESIN".into()),
                ("solvent".into(), "SOLVENT".into()),
            ]),
            resin_oligomer_distributions: BTreeMap::from([(
                "resin-grade-1".into(),
                vec![OligomerFractionV1 {
                    degree_of_polymerization: 10.0,
                    mole_fraction_0_1: 1.0,
                }],
            )]),
            pair_coefficients: vec![PairCoefficientV1 {
                component_a: "resin".into(),
                component_b: "solvent".into(),
                a: 3.0,
                b_kelvin: 0.0,
                redlich_kister: 0.0,
                covariance: [[covariance, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            }],
            temperature_bounds_c: [10.0, 40.0],
            composition_floor_0_1: 1e-6,
            generator_versions: BTreeMap::from([("parameterizer".into(), "test-v1".into())]),
            parent_hashes: BTreeMap::from([("source".into(), "c".repeat(64))]),
            rights_receipt_hashes: vec!["d".repeat(64)],
            rights_eligible: true,
            quantum_generator_license_resolved: true,
        }
    }

    fn measured_observation() -> SolvencyObservationV1 {
        SolvencyObservationV1 {
            schema: OBSERVATION_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            observation_id: "obs-1".into(),
            candidate_id: "candidate-1".into(),
            blend_id: "blend-1".into(),
            solvent_family_group: "ketone".into(),
            resin_grade: "resin-grade-1".into(),
            resin_lot: "resin-lot-1".into(),
            preparation_id: "preparation-1".into(),
            replicate_id: "replicate-1".into(),
            temperature_c: 25.0,
            components: vec![
                CarrierComponentV1 {
                    component_id: "resin".into(),
                    structure_sha256: "a".repeat(64),
                    role: "RESIN".into(),
                    lot_id: "resin-lot-1".into(),
                    identity_status: "EXACT".into(),
                    volume_fraction_0_1: 0.5,
                    molar_volume_cm3_mol_at_reference: 200.0,
                    molar_volume_temperature_coefficient_per_k: 0.001,
                    segment_count: 10.0,
                    oligomer_distribution: vec![OligomerFractionV1 {
                        degree_of_polymerization: 10.0,
                        mole_fraction_0_1: 1.0,
                    }],
                },
                CarrierComponentV1 {
                    component_id: "solvent".into(),
                    structure_sha256: "b".repeat(64),
                    role: "SOLVENT".into(),
                    lot_id: "solvent-lot-1".into(),
                    identity_status: "EXACT".into(),
                    volume_fraction_0_1: 0.5,
                    molar_volume_cm3_mol_at_reference: 75.0,
                    molar_volume_temperature_coefficient_per_k: 0.001,
                    segment_count: 1.0,
                    oligomer_distribution: Vec::new(),
                },
            ],
            excluded_positive_mass_components: Vec::new(),
            microscopy_single_phase_1h: Some(false),
            microscopy_single_phase_24h: Some(false),
            turbidity_ntu_1h: Some(100.0),
            turbidity_ntu_24h: Some(150.0),
            method_id: "MICROSCOPY_TURBIDITY_PAIRED".into(),
            raw_file_hashes: BTreeMap::from([("blend.csv".into(), "e".repeat(64))]),
            rights_receipt_sha256: "f".repeat(64),
            rights_eligible: true,
        }
    }

    #[test]
    fn test_flory_huggins_binary_critical_case_is_known() {
        let eigen = minimum_hessian_eigenvalue(
            &[0.5, 0.5],
            &[1.0, 1.0],
            &[pair(2.0)],
            &["a".into(), "b".into()],
            298.15,
            0.0,
        )
        .unwrap();
        assert!(eigen.abs() < 1e-5, "{eigen}");
    }

    #[test]
    fn test_tpd_is_permutation_invariant_and_detects_instability() {
        let ids = vec!["a".into(), "b".into()];
        let forward =
            tangent_plane_minimum_rt(&[0.5, 0.5], &[1.0, 1.0], &[pair(3.0)], &ids, 298.15, 0.0)
                .unwrap();
        let mut reverse_pair = pair(3.0);
        reverse_pair.component_a = "a".into();
        reverse_pair.component_b = "b".into();
        let reverse = tangent_plane_minimum_rt(
            &[0.5, 0.5],
            &[1.0, 1.0],
            &[reverse_pair],
            &["b".into(), "a".into()],
            298.15,
            0.0,
        )
        .unwrap();
        assert!(forward < 0.0);
        assert!((forward - reverse).abs() < 1e-12);
    }

    #[test]
    fn test_conservation_and_unknown_fields_fail_closed() {
        assert!(gibbs_mix_rt(
            &[0.4, 0.5],
            &[1.0, 1.0],
            &[pair(1.0)],
            &["a".into(), "b".into()],
            298.15,
            0.0,
        )
        .is_err());
        let error = serde_json::from_value::<OligomerFractionV1>(json!({
            "degree_of_polymerization": 2.0,
            "mole_fraction_0_1": 1.0,
            "compatibility_probability": 1.0
        }))
        .unwrap_err();
        assert!(error.to_string().contains("unknown field"));
    }

    #[test]
    fn test_parameter_matrix_fit_prediction_and_uncertainty_are_bound() {
        let observation = measured_observation();
        let parameters = parameter_artifact(0.25);
        let dataset = SolvencyDatasetV1 {
            schema: DATASET_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            dataset_id: "dataset-1".into(),
            parameter_artifact: parameters.clone(),
            observations: vec![observation.clone()],
        };
        let split = SolvencySplitV1 {
            schema: SPLIT_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            split_id: "split-1".into(),
            dataset_sha256: dataset.identity_hash(),
            assignments: vec![SplitAssignmentV1 {
                observation_id: observation.observation_id.clone(),
                blend_id: observation.blend_id.clone(),
                solvent_family_group: observation.solvent_family_group.clone(),
                resin_lot_group: observation.resin_lot.clone(),
                split: "FIT".into(),
            }],
        };
        let lock = SolvencyBenchmarkLockV1 {
            schema: BENCHMARK_LOCK_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            benchmark_id: "benchmark-1".into(),
            dataset_sha256: dataset.identity_hash(),
            split_sha256: split.identity_hash(),
            baselines: vec![
                "HSP_RED".into(),
                "CONSTANT_CHI_FLORY_HUGGINS".into(),
                "UNIFAC_FV".into(),
                "RAW_OPENCOSMO".into(),
            ],
            hostile_nulls: vec!["PAIR_SHUFFLE".into()],
            thresholds: BTreeMap::new(),
            immutable: true,
        };
        let first = fit_model(&dataset, &split, &lock).unwrap();
        let second = fit_model(&dataset, &split, &lock).unwrap();
        assert_eq!(first, second);
        assert!(!first.promotion_dataset_complete);

        let prediction = predict(&first, &observation).unwrap();
        let interval = prediction.parameter_interval_min_tpd_rt.unwrap();
        assert!(interval.lower < interval.upper);
        assert!(prediction.min_tpd_rt.is_some());
        assert!(prediction.minimum_hessian_eigenvalue.is_some());
        assert!(prediction.computed_single_phase_fraction.is_some());
        assert!(prediction.numeric_compatibility_prediction.is_none());

        let mut incomplete = parameters;
        incomplete.pair_coefficients.clear();
        assert_eq!(incomplete.validate(), Err(SolvencyError::PairMatrix));
    }

    #[test]
    fn parameter_v2_requires_only_admissible_pairs_and_psd_covariance() {
        let resin_distribution = vec![OligomerFractionV1 {
            degree_of_polymerization: 2.0,
            mole_fraction_0_1: 1.0,
        }];
        let component = |id: &str, role: &str| ComponentParameterV2 {
            component_id: id.into(),
            structure_sha256: "a".repeat(64),
            role: role.into(),
            lot_id: format!("lot-{id}"),
            parameter_origin: "OWNED_PAIR_CALIBRATION".into(),
            identity_calibration_sha256: "a".repeat(64),
            resin_grade: (role == "RESIN").then(|| "DGEBA-828".into()),
            measured_oligomer_distribution: if role == "RESIN" {
                resin_distribution.clone()
            } else {
                Vec::new()
            },
            sec_gpc_calibration_sha256: (role == "RESIN").then(|| "b".repeat(64)),
        };
        let sets = vec![
            AdmissibleComponentSetV2 {
                set_id: "resin-aromatic".into(),
                component_ids: vec!["R".into(), "S".into()],
            },
            AdmissibleComponentSetV2 {
                set_id: "resin-ketone".into(),
                component_ids: vec!["R".into(), "T".into()],
            },
        ];
        let coefficient = |solvent: &str| PairCoefficientV1 {
            component_a: "R".into(),
            component_b: solvent.into(),
            a: 0.1,
            b_kelvin: 1.0,
            redlich_kister: 0.0,
            covariance: [[0.1, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]],
        };
        let mut artifact = SolvencyParameterArtifactV2 {
            schema: PARAMETER_ARTIFACT_V2_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            parameter_id: "parameters-v2".into(),
            components: BTreeMap::from([
                ("R".into(), component("R", "RESIN")),
                ("S".into(), component("S", "SOLVENT")),
                ("T".into(), component("T", "SOLVENT")),
            ]),
            admissible_component_sets_sha256: stable_hash(&serde_json::to_value(&sets).unwrap()),
            admissible_component_sets: sets,
            pair_coefficients: vec![coefficient("S"), coefficient("T")],
            pair_calibration_hashes: BTreeMap::from([
                ("R|S".into(), "c".repeat(64)),
                ("R|T".into(), "d".repeat(64)),
            ]),
            temperature_bounds_c: [10.0, 40.0],
            composition_floor_0_1: 0.001,
            parent_hashes: BTreeMap::from([("campaign".into(), "e".repeat(64))]),
            rights_receipt_hashes: vec!["f".repeat(64)],
            rights_eligible: true,
        };
        artifact.validate().unwrap();
        artifact.pair_coefficients.pop();
        assert_eq!(artifact.validate(), Err(SolvencyError::PairMatrix));

        let mut pair = coefficient("S");
        pair.covariance[0][1] = 2.0;
        assert_eq!(
            pair.validate(),
            Err(SolvencyError::Range("pair coefficient"))
        );
    }

    // -------------------------------------------------------------------
    // Phase-0 Hansen Solubility Parameter (HSP) red-team tests
    // -------------------------------------------------------------------

    #[test]
    fn hansen_ra_squared_is_deterministic_and_symmetric_in_input_pairing() {
        // Toluene vs DGEBA-epoxy (representative in-domain pair).
        let first = hansen_ra_squared(18.0, 1.4, 2.0, 17.4, 10.5, 7.0).unwrap();
        let second = hansen_ra_squared(18.0, 1.4, 2.0, 17.4, 10.5, 7.0).unwrap();
        assert_eq!(first.to_bits(), second.to_bits());
        // Symmetric under swapping "solvent" and "polymer" coordinates.
        let swapped = hansen_ra_squared(17.4, 10.5, 7.0, 18.0, 1.4, 2.0).unwrap();
        assert_eq!(first.to_bits(), swapped.to_bits());
    }

    #[test]
    fn hansen_red_flags_incompatible_when_ra_exceeds_polymer_radius() {
        // n-hexane vs. Nylon 66: distant in HSP space, small R (5.1) — expect RED > 1.
        let red = hansen_red(14.9, 0.0, 0.0, 17.4, 9.9, 14.6, 5.1).unwrap();
        assert!(red > 1.0, "hexane/nylon RED {red} should exceed 1.0");
        // Toluene vs. polystyrene: in-sphere (large R 12.7), expect RED < 1.
        let red_ps = hansen_red(18.0, 1.4, 2.0, 21.3, 5.8, 4.3, 12.7).unwrap();
        assert!(red_ps < 1.0, "toluene/PS RED {red_ps} should be under 1.0");
    }

    #[test]
    fn hansen_calculation_rejects_non_finite_inputs() {
        assert!(hansen_ra_squared(f64::NAN, 1.4, 2.0, 17.4, 10.5, 7.0).is_none());
        assert!(hansen_ra_squared(18.0, 1.4, f64::INFINITY, 17.4, 10.5, 7.0).is_none());
        assert!(hansen_red(18.0, 1.4, 2.0, 17.4, 10.5, 7.0, f64::NAN).is_none());
        assert!(hansen_red(18.0, 1.4, 2.0, 17.4, 10.5, 7.0, f64::INFINITY).is_none());
    }

    #[test]
    fn hansen_calculation_rejects_negative_hansen_parameters() {
        assert!(hansen_ra_squared(-1.0, 1.4, 2.0, 17.4, 10.5, 7.0).is_none());
        assert!(hansen_ra_squared(18.0, -0.001, 2.0, 17.4, 10.5, 7.0).is_none());
        assert!(hansen_ra_squared(18.0, 1.4, 2.0, 17.4, 10.5, -3.0).is_none());
    }

    #[test]
    fn hansen_red_rejects_zero_or_negative_interaction_radius() {
        assert!(hansen_red(18.0, 1.4, 2.0, 17.4, 10.5, 7.0, 0.0).is_none());
        assert!(hansen_red(18.0, 1.4, 2.0, 17.4, 10.5, 7.0, -9.0).is_none());
    }

    #[test]
    fn hansen_red_zero_at_identity_and_grows_with_distance() {
        // Identity: solvent HSP == polymer HSP → Ra=0, RED=0.
        let identity = hansen_red(17.4, 10.5, 7.0, 17.4, 10.5, 7.0, 9.0).unwrap();
        assert!(identity.abs() < 1e-12, "identity RED must be ~0, got {identity}");
        // Small perturbation → small but positive RED.
        let near = hansen_red(17.5, 10.5, 7.0, 17.4, 10.5, 7.0, 9.0).unwrap();
        assert!(near > 0.0 && near < 1.0);
        // Large perturbation → large RED.
        let far = hansen_red(14.9, 0.0, 0.0, 21.3, 5.8, 4.3, 12.7).unwrap();
        assert!(far > 0.0);
    }
}
