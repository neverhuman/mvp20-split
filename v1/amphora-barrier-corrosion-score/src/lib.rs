#![forbid(unsafe_code)]

use amphora_core::{
    stable_hash, CandidateEnvelope, ConfidenceIntervalV1, FeatureSnapshot, ModuleResult,
    VerifiedFormulationModelInputV2,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

pub const MODULE_ID: &str = "amphora-barrier-corrosion-score";
pub const HOST_FEATURE_KEY: &str = "verified_formulation_model.amphora-barrier-corrosion-score";
pub const OBSERVATION_SCHEMA: &str = "amphora.measured-eis-observation.v1";
pub const OBSERVATION_BUNDLE_SCHEMA: &str = "amphora.measured-eis-observation-bundle.v1";
pub const DATASET_SCHEMA: &str = "amphora.measured-eis-dataset.v1";
pub const SPLIT_SCHEMA: &str = "amphora.measured-eis-split.v1";
pub const BENCHMARK_LOCK_SCHEMA: &str = "amphora.measured-eis-benchmark-lock.v1";
pub const MODEL_ARTIFACT_SCHEMA: &str = "amphora.measured-eis-model-artifact.v1";
pub const PREDICTION_SCHEMA: &str = "amphora.measured-eis-prediction.v1";
pub const INDEPENDENT_REVIEW_SCHEMA: &str = "amphora.measured-eis-independent-review.v1";
pub const OBSERVATION_V2_SCHEMA: &str = "amphora.measured-eis-observation.v2";
pub const BENCHMARK_RECEIPT_SCHEMA: &str = "amphora.barrier-benchmark-receipt.v1";
pub const RESIDUAL_MODEL_L2: f64 = 1.0;
pub const RESIDUAL_MODEL_SEED: u64 = 20_260_717;

#[derive(Debug, Error, PartialEq)]
pub enum CorrosionError {
    #[error("unexpected schema or module identity")]
    Identity,
    #[error("required field is empty: {0}")]
    Empty(&'static str),
    #[error("invalid SHA-256: {0}")]
    Hash(&'static str),
    #[error("non-finite or out-of-range value: {0}")]
    Range(&'static str),
    #[error("rights are not eligible")]
    Rights,
    #[error("EIS method or spectrum declaration is not comparable")]
    Method,
    #[error("dataset, split, or benchmark parent mismatch")]
    Parent,
    #[error("source/study/system leakage detected")]
    Leakage,
    #[error("equivalent-circuit fit did not converge")]
    NonConvergent,
    #[error("observation is outside the artifact applicability domain")]
    OutOfDomain,
    #[error("JSON contract error: {0}")]
    Json(String),
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum SpectrumKindV1 {
    FullFrequencyResolved,
    SingleFrequencySummary,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EisPointV1 {
    pub frequency_hz: f64,
    pub real_ohm_cm2: f64,
    pub imaginary_ohm_cm2: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EisSummaryPointV1 {
    pub exposure_hours: f64,
    pub low_frequency_hz: f64,
    pub impedance_modulus_ohm_cm2: f64,
    pub phase_deg: f64,
    pub ocv_v: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EisObservationV1 {
    pub schema: String,
    pub module_id: String,
    pub observation_id: String,
    pub candidate_id: String,
    pub source_id: String,
    pub study_id: String,
    pub coating_system_id: String,
    pub coating_family: String,
    pub panel_id: String,
    pub replicate_id: String,
    pub protocol_id: String,
    pub method_class: String,
    pub cell_area_cm2: f64,
    pub dft_um: f64,
    pub substrate: String,
    pub temperature_c: f64,
    pub exposure_medium: String,
    pub exposure_hours: f64,
    pub spectrum_kind: SpectrumKindV1,
    pub spectrum: Vec<EisPointV1>,
    pub summaries: Vec<EisSummaryPointV1>,
    pub replicate_log_impedance_dispersion: f64,
    pub measured_rust_creep_mm: Option<f64>,
    pub measured_wet_adhesion_mpa: Option<f64>,
    pub raw_file_hashes: BTreeMap<String, String>,
    pub rights_receipt_sha256: String,
    pub rights_eligible: bool,
}

impl EisObservationV1 {
    pub fn validate_conditions(&self) -> Result<(), CorrosionError> {
        require_identity(&self.schema, OBSERVATION_SCHEMA, &self.module_id)?;
        for (field, value) in [
            ("observation_id", self.observation_id.as_str()),
            ("candidate_id", self.candidate_id.as_str()),
            ("source_id", self.source_id.as_str()),
            ("study_id", self.study_id.as_str()),
            ("coating_system_id", self.coating_system_id.as_str()),
            ("coating_family", self.coating_family.as_str()),
            ("panel_id", self.panel_id.as_str()),
            ("replicate_id", self.replicate_id.as_str()),
            ("protocol_id", self.protocol_id.as_str()),
            ("substrate", self.substrate.as_str()),
            ("exposure_medium", self.exposure_medium.as_str()),
        ] {
            require_text(field, value)?;
        }
        require_hash("rights_receipt_sha256", &self.rights_receipt_sha256)?;
        validate_hash_map(&self.raw_file_hashes)?;
        if !self.rights_eligible {
            return Err(CorrosionError::Rights);
        }
        if self.method_class != "LAB_EIS"
            || !finite_positive(self.cell_area_cm2)
            || !finite_positive(self.dft_um)
            || !finite_between(self.temperature_c, -10.0, 80.0)
            || !self.exposure_hours.is_finite()
            || self.exposure_hours < 0.0
            || !self.replicate_log_impedance_dispersion.is_finite()
            || self.replicate_log_impedance_dispersion < 0.0
        {
            return Err(CorrosionError::Method);
        }
        for summary in &self.summaries {
            if !summary.exposure_hours.is_finite()
                || summary.exposure_hours < 0.0
                || !finite_positive(summary.low_frequency_hz)
                || !finite_positive(summary.impedance_modulus_ohm_cm2)
                || !finite_between(summary.phase_deg, -180.0, 180.0)
                || !summary.ocv_v.is_finite()
            {
                return Err(CorrosionError::Range("EIS summary"));
            }
        }
        if self
            .summaries
            .windows(2)
            .any(|window| window[0].exposure_hours >= window[1].exposure_hours)
        {
            return Err(CorrosionError::Range("summary time ordering"));
        }
        match self.spectrum_kind {
            SpectrumKindV1::FullFrequencyResolved => {
                if self.spectrum.len() < 8
                    || self.spectrum.iter().any(|point| {
                        !finite_positive(point.frequency_hz)
                            || !point.real_ohm_cm2.is_finite()
                            || !point.imaginary_ohm_cm2.is_finite()
                    })
                    || self
                        .spectrum
                        .windows(2)
                        .any(|window| window[0].frequency_hz <= window[1].frequency_hz)
                {
                    return Err(CorrosionError::Method);
                }
            }
            SpectrumKindV1::SingleFrequencySummary => {
                if !self.spectrum.is_empty() || self.summaries.len() < 2 {
                    return Err(CorrosionError::Method);
                }
            }
        }
        Ok(())
    }

    pub fn validate_measured(&self) -> Result<(), CorrosionError> {
        self.validate_conditions()?;
        if self
            .measured_rust_creep_mm
            .is_none_or(|value| !value.is_finite() || value < 0.0)
            || self
                .measured_wet_adhesion_mpa
                .is_none_or(|value| !value.is_finite() || value < 0.0)
        {
            return Err(CorrosionError::Range("measured endpoints"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("observation serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EisObservationV2 {
    pub schema: String,
    pub module_id: String,
    pub observation: EisObservationV1,
    pub acquisition_amplitude_mv_rms: f64,
    pub frequency_high_hz: f64,
    pub frequency_low_hz: f64,
    pub points_per_decade: u32,
    pub stabilization_duration_min: f64,
    pub stabilization_ocv_drift_mv_per_min: f64,
    pub instrument_id: String,
    pub calibration_sha256: String,
    pub stationarity_checked: bool,
    pub stationary: bool,
    pub clipped: bool,
    pub dummy_cell_control_passed: bool,
    pub linear_kramers_kronig_residual_rms: f64,
    pub linear_kramers_kronig_residual_whiteness_passed: bool,
    pub linear_kramers_kronig_passed: bool,
}

impl EisObservationV2 {
    pub fn validate(&self) -> Result<(), CorrosionError> {
        require_identity(&self.schema, OBSERVATION_V2_SCHEMA, &self.module_id)?;
        self.observation.validate_conditions()?;
        require_text("instrument_id", &self.instrument_id)?;
        require_hash("calibration_sha256", &self.calibration_sha256)?;
        if self.observation.spectrum_kind != SpectrumKindV1::FullFrequencyResolved
            || !finite_between(self.acquisition_amplitude_mv_rms, 1.0, 10.0)
            || self.frequency_high_hz < 100_000.0
            || self.frequency_low_hz > 0.01
            || self.frequency_low_hz <= 0.0
            || self.points_per_decade < 10
            || !finite_positive(self.stabilization_duration_min)
            || !self.stabilization_ocv_drift_mv_per_min.is_finite()
            || self.stabilization_ocv_drift_mv_per_min.abs() > 1.0
            || !self.stationarity_checked
            || !self.stationary
            || self.clipped
            || !self.dummy_cell_control_passed
            || !self.linear_kramers_kronig_residual_rms.is_finite()
            || self.linear_kramers_kronig_residual_rms < 0.0
            || !self.linear_kramers_kronig_residual_whiteness_passed
            || !self.linear_kramers_kronig_passed
            || self
                .observation
                .spectrum
                .first()
                .is_none_or(|point| point.frequency_hz < self.frequency_high_hz)
            || self
                .observation
                .spectrum
                .last()
                .is_none_or(|point| point.frequency_hz > self.frequency_low_hz)
        {
            return Err(CorrosionError::Method);
        }
        let decades = (self.frequency_high_hz / self.frequency_low_hz).log10();
        let required_points = (decades * self.points_per_decade as f64).floor() as usize + 1;
        if self.observation.spectrum.len() < required_points {
            return Err(CorrosionError::Method);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CircuitFitDiagnosticsV2 {
    pub parameters: EquivalentCircuitParametersV1,
    pub start_count: u32,
    pub converged_start_count: u32,
    pub stable_topology: bool,
    pub maximum_parameter_coefficient_of_variation: f64,
    pub hessian_condition_number: f64,
}

impl CircuitFitDiagnosticsV2 {
    pub fn eligible_parameters(
        &self,
        observation: &EisObservationV2,
    ) -> Result<EquivalentCircuitParametersV1, CorrosionError> {
        observation.validate()?;
        self.parameters.validate()?;
        if self.start_count != 32
            || self.converged_start_count != 32
            || !self.stable_topology
            || !finite_between(self.maximum_parameter_coefficient_of_variation, 0.0, 0.50)
            || !finite_positive(self.hessian_condition_number)
            || self.hessian_condition_number > 1.0e8
        {
            return Err(CorrosionError::NonConvergent);
        }
        Ok(self.parameters)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EisDatasetV1 {
    pub schema: String,
    pub module_id: String,
    pub dataset_id: String,
    pub observations: Vec<EisObservationV1>,
}

impl EisDatasetV1 {
    pub fn validate(&self) -> Result<(), CorrosionError> {
        require_identity(&self.schema, DATASET_SCHEMA, &self.module_id)?;
        require_text("dataset_id", &self.dataset_id)?;
        if self.observations.is_empty() {
            return Err(CorrosionError::Empty("observations"));
        }
        let mut ids = BTreeSet::new();
        for observation in &self.observations {
            observation.validate_measured()?;
            if !ids.insert(&observation.observation_id) {
                return Err(CorrosionError::Parent);
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
    pub source_id: String,
    pub study_id: String,
    pub coating_system_id: String,
    pub split: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct EisSplitV1 {
    pub schema: String,
    pub module_id: String,
    pub split_id: String,
    pub dataset_sha256: String,
    pub assignments: Vec<SplitAssignmentV1>,
}

impl EisSplitV1 {
    pub fn validate(&self, dataset: Option<&EisDatasetV1>) -> Result<(), CorrosionError> {
        require_identity(&self.schema, SPLIT_SCHEMA, &self.module_id)?;
        require_text("split_id", &self.split_id)?;
        require_hash("dataset_sha256", &self.dataset_sha256)?;
        let mut observations = BTreeSet::new();
        let mut system_folds: BTreeMap<(&str, &str, &str), &str> = BTreeMap::new();
        for row in &self.assignments {
            for (field, value) in [
                ("observation_id", row.observation_id.as_str()),
                ("source_id", row.source_id.as_str()),
                ("study_id", row.study_id.as_str()),
                ("coating_system_id", row.coating_system_id.as_str()),
                ("split", row.split.as_str()),
            ] {
                require_text(field, value)?;
            }
            let key = (
                row.source_id.as_str(),
                row.study_id.as_str(),
                row.coating_system_id.as_str(),
            );
            if !observations.insert(row.observation_id.as_str())
                || system_folds
                    .insert(key, row.split.as_str())
                    .is_some_and(|existing| existing != row.split)
            {
                return Err(CorrosionError::Leakage);
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
                return Err(CorrosionError::Parent);
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
pub struct EisBenchmarkLockV1 {
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

impl EisBenchmarkLockV1 {
    pub fn validate(&self) -> Result<(), CorrosionError> {
        require_identity(&self.schema, BENCHMARK_LOCK_SCHEMA, &self.module_id)?;
        require_text("benchmark_id", &self.benchmark_id)?;
        require_hash("dataset_sha256", &self.dataset_sha256)?;
        require_hash("split_sha256", &self.split_sha256)?;
        for baseline in [
            "CURRENT_FULL_SPECTRUM",
            "LOW_FREQUENCY_IMPEDANCE",
            "SOLIDS_ONLY",
            "PVC_ONLY",
            "BLINDED_COATINGS_EXPERT",
        ] {
            if !self.baselines.iter().any(|value| value == baseline) {
                return Err(CorrosionError::Range("benchmark baselines"));
            }
        }
        for hostile in [
            "LEAKAGE",
            "SHUFFLE",
            "TIME_REVERSAL",
            "UNIT_AREA_MISMATCH",
            "CLIPPED_SPECTRUM",
            "FIELD_LAB_METHOD_MISMATCH",
        ] {
            if !self.hostile_nulls.iter().any(|value| value == hostile) {
                return Err(CorrosionError::Range("hostile nulls"));
            }
        }
        if !self.immutable || self.thresholds.values().any(|value| !value.is_finite()) {
            return Err(CorrosionError::Range("benchmark lock"));
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
    pub study_id: String,
    pub site_id: String,
    pub observed_barrier_order: f64,
    pub predicted_barrier_order: f64,
    pub baseline_barrier_order: f64,
    pub observed_failure: bool,
    pub predicted_failure_probability: f64,
    pub baseline_failure_probability: f64,
    pub observed_rust_creep_mm: f64,
    pub predicted_rust_creep_mm: f64,
    pub baseline_rust_creep_mm: f64,
    pub rust_creep_interval_90: [f64; 2],
    pub observed_wet_adhesion_mpa: f64,
    pub predicted_wet_adhesion_mpa: f64,
    pub baseline_wet_adhesion_mpa: f64,
    pub wet_adhesion_interval_90: [f64; 2],
}

impl OutOfFoldPredictionV1 {
    fn validate(&self) -> Result<(), CorrosionError> {
        for (field, value) in [
            ("observation_id", self.observation_id.as_str()),
            ("cluster_id", self.cluster_id.as_str()),
            ("study_id", self.study_id.as_str()),
            ("site_id", self.site_id.as_str()),
        ] {
            require_text(field, value)?;
        }
        if [
            self.observed_barrier_order,
            self.predicted_barrier_order,
            self.baseline_barrier_order,
            self.observed_rust_creep_mm,
            self.predicted_rust_creep_mm,
            self.baseline_rust_creep_mm,
            self.observed_wet_adhesion_mpa,
            self.predicted_wet_adhesion_mpa,
            self.baseline_wet_adhesion_mpa,
        ]
        .iter()
        .any(|value| !value.is_finite())
            || !finite_between(self.predicted_failure_probability, 0.0, 1.0)
            || !finite_between(self.baseline_failure_probability, 0.0, 1.0)
            || [self.rust_creep_interval_90, self.wet_adhesion_interval_90]
                .iter()
                .any(|interval| {
                    interval.iter().any(|value| !value.is_finite()) || interval[0] > interval[1]
                })
        {
            return Err(CorrosionError::Range("out-of-fold prediction"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct BenchmarkMetricsV1 {
    pub kendall_tau: f64,
    pub study_block_tau_lower_95: f64,
    pub classification_balanced_accuracy: f64,
    pub baseline_classification_balanced_accuracy: f64,
    pub classification_lift: f64,
    pub calibration_error: f64,
    pub interval_90_coverage: f64,
    pub rust_creep_mae_mm: f64,
    pub baseline_rust_creep_mae_mm: f64,
    pub wet_adhesion_mae_mpa: f64,
    pub baseline_wet_adhesion_mae_mpa: f64,
    pub baseline_kendall_tau: f64,
    pub delta_kendall_tau: f64,
    pub delta_kendall_tau_lower_95: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct BenchmarkGateStatusV1 {
    pub kendall_tau_at_least_0_50: bool,
    pub study_block_lower_positive: bool,
    pub classification_lift_at_least_0_10: bool,
    pub calibration_error_at_most_0_10: bool,
    pub interval_coverage_0_85_to_0_95: bool,
    pub rust_creep_error_non_worse: bool,
    pub wet_adhesion_error_non_worse: bool,
    pub delta_tau_at_least_0_10: bool,
    pub delta_tau_lower_positive: bool,
    pub both_verifier_sites_non_reversing: bool,
}

impl BenchmarkGateStatusV1 {
    pub fn passed(&self) -> bool {
        self.kendall_tau_at_least_0_50
            && self.study_block_lower_positive
            && self.classification_lift_at_least_0_10
            && self.calibration_error_at_most_0_10
            && self.interval_coverage_0_85_to_0_95
            && self.rust_creep_error_non_worse
            && self.wet_adhesion_error_non_worse
            && self.delta_tau_at_least_0_10
            && self.delta_tau_lower_positive
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
    pub fn validate(&self) -> Result<(), CorrosionError> {
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
            .expect("metrics object")
            .values()
            .any(|value| value.as_f64().is_none_or(|value| !value.is_finite()))
            || self.estimator != "STANDARDIZED_RIDGE_LOGISTIC"
            || self.l2_penalty != RESIDUAL_MODEL_L2
            || self.seed != RESIDUAL_MODEL_SEED
            || self.passed != self.gate_status.passed()
        {
            return Err(CorrosionError::Range("benchmark receipt"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("receipt serializes"))
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EquivalentCircuitParametersV1 {
    pub solution_resistance_ohm_cm2: f64,
    pub coating_resistance_ohm_cm2: f64,
    pub coating_q_s_n_ohm_inv_cm2: f64,
    pub coating_exponent: f64,
    pub charge_transfer_resistance_ohm_cm2: f64,
    pub double_layer_q_s_n_ohm_inv_cm2: f64,
    pub double_layer_exponent: f64,
}

impl EquivalentCircuitParametersV1 {
    fn validate(&self) -> Result<(), CorrosionError> {
        if !finite_positive(self.solution_resistance_ohm_cm2)
            || !finite_positive(self.coating_resistance_ohm_cm2)
            || !finite_positive(self.coating_q_s_n_ohm_inv_cm2)
            || !finite_between(self.coating_exponent, 0.4, 1.0)
            || !finite_positive(self.charge_transfer_resistance_ohm_cm2)
            || !finite_positive(self.double_layer_q_s_n_ohm_inv_cm2)
            || !finite_between(self.double_layer_exponent, 0.4, 1.0)
        {
            return Err(CorrosionError::Range("equivalent circuit parameters"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy)]
struct Complex {
    re: f64,
    im: f64,
}

impl Complex {
    fn add(self, other: Self) -> Self {
        Self {
            re: self.re + other.re,
            im: self.im + other.im,
        }
    }

    fn reciprocal(self) -> Self {
        let denominator = self.re * self.re + self.im * self.im;
        Self {
            re: self.re / denominator,
            im: -self.im / denominator,
        }
    }

    fn modulus(self) -> f64 {
        self.re.hypot(self.im)
    }

    fn phase(self) -> f64 {
        self.im.atan2(self.re)
    }
}

pub fn simulate_equivalent_circuit(
    parameters: EquivalentCircuitParametersV1,
    frequency_hz: f64,
) -> Result<(f64, f64), CorrosionError> {
    parameters.validate()?;
    if !finite_positive(frequency_hz) {
        return Err(CorrosionError::Range("frequency_hz"));
    }
    let omega = 2.0 * std::f64::consts::PI * frequency_hz;
    let parallel_cpe = |resistance: f64, q: f64, exponent: f64| {
        let magnitude = q * omega.powf(exponent);
        let angle = exponent * std::f64::consts::FRAC_PI_2;
        Complex {
            re: 1.0 / resistance + magnitude * angle.cos(),
            im: magnitude * angle.sin(),
        }
        .reciprocal()
    };
    let impedance = Complex {
        re: parameters.solution_resistance_ohm_cm2,
        im: 0.0,
    }
    .add(parallel_cpe(
        parameters.coating_resistance_ohm_cm2,
        parameters.coating_q_s_n_ohm_inv_cm2,
        parameters.coating_exponent,
    ))
    .add(parallel_cpe(
        parameters.charge_transfer_resistance_ohm_cm2,
        parameters.double_layer_q_s_n_ohm_inv_cm2,
        parameters.double_layer_exponent,
    ));
    Ok((impedance.re, impedance.im))
}

pub fn fit_equivalent_circuit(
    spectrum: &[EisPointV1],
) -> Result<EquivalentCircuitParametersV1, CorrosionError> {
    if spectrum.len() < 8 {
        return Err(CorrosionError::Method);
    }
    let minimum_real = spectrum
        .iter()
        .map(|row| row.real_ohm_cm2)
        .filter(|value| *value > 0.0)
        .fold(f64::INFINITY, f64::min);
    let low_modulus = spectrum
        .last()
        .map(|row| row.real_ohm_cm2.hypot(row.imaginary_ohm_cm2))
        .ok_or(CorrosionError::Method)?;
    if !finite_positive(minimum_real) || !finite_positive(low_modulus) {
        return Err(CorrosionError::Method);
    }
    let initial = [
        minimum_real.ln(),
        (0.55 * low_modulus).max(minimum_real).ln(),
        1e-7_f64.ln(),
        0.85,
        (0.4 * low_modulus).max(minimum_real).ln(),
        1e-5_f64.ln(),
        0.85,
    ];
    let decode = |values: [f64; 7]| EquivalentCircuitParametersV1 {
        solution_resistance_ohm_cm2: values[0].exp(),
        coating_resistance_ohm_cm2: values[1].exp(),
        coating_q_s_n_ohm_inv_cm2: values[2].exp(),
        coating_exponent: values[3].clamp(0.4, 1.0),
        charge_transfer_resistance_ohm_cm2: values[4].exp(),
        double_layer_q_s_n_ohm_inv_cm2: values[5].exp(),
        double_layer_exponent: values[6].clamp(0.4, 1.0),
    };
    let objective = |values: [f64; 7]| -> Result<f64, CorrosionError> {
        let parameters = decode(values);
        let mut loss = 0.0;
        for row in spectrum {
            let (real, imaginary) = simulate_equivalent_circuit(parameters, row.frequency_hz)?;
            let predicted = Complex {
                re: real,
                im: imaginary,
            };
            let observed = Complex {
                re: row.real_ohm_cm2,
                im: row.imaginary_ohm_cm2,
            };
            loss += (predicted.modulus().ln() - observed.modulus().ln()).powi(2)
                + 0.25 * (predicted.phase() - observed.phase()).powi(2);
        }
        Ok(loss / spectrum.len() as f64)
    };
    let mut best = initial;
    let mut best_loss = objective(best)?;
    let mut steps = [1.5, 1.5, 2.0, 0.1, 1.5, 2.0, 0.1];
    for _ in 0..100 {
        let mut improved = false;
        for parameter in 0..7 {
            for direction in [-1.0, 1.0] {
                let mut trial = best;
                trial[parameter] += direction * steps[parameter];
                let loss = objective(trial)?;
                if loss < best_loss {
                    best = trial;
                    best_loss = loss;
                    improved = true;
                }
            }
        }
        if !improved {
            for step in &mut steps {
                *step *= 0.65;
            }
        }
        if steps.iter().copied().fold(0.0_f64, f64::max) < 1e-4 {
            break;
        }
    }
    let fitted = decode(best);
    fitted.validate()?;
    if !best_loss.is_finite() || best_loss > 0.25 {
        Err(CorrosionError::NonConvergent)
    } else {
        Ok(fitted)
    }
}

pub fn theil_sen_slope(points: &[(f64, f64)]) -> Result<f64, CorrosionError> {
    if points.len() < 2 || points.iter().any(|(x, y)| !x.is_finite() || !y.is_finite()) {
        return Err(CorrosionError::Range("Theil-Sen points"));
    }
    let mut slopes = Vec::new();
    for i in 0..points.len() {
        for j in (i + 1)..points.len() {
            let delta = points[j].0 - points[i].0;
            if delta != 0.0 {
                slopes.push((points[j].1 - points[i].1) / delta);
            }
        }
    }
    if slopes.is_empty() {
        return Err(CorrosionError::Range("Theil-Sen points"));
    }
    slopes.sort_by(f64::total_cmp);
    Ok(if slopes.len() % 2 == 0 {
        (slopes[slopes.len() / 2 - 1] + slopes[slopes.len() / 2]) / 2.0
    } else {
        slopes[slopes.len() / 2]
    })
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ApplicabilityDomainV1 {
    pub coating_families: Vec<String>,
    pub substrates: Vec<String>,
    pub protocols: Vec<String>,
    pub temperature_c: [f64; 2],
    pub dft_um: [f64; 2],
    pub exposure_hours: [f64; 2],
    pub spectrum_kinds: Vec<SpectrumKindV1>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EisModelArtifactV1 {
    pub schema: String,
    pub module_id: String,
    pub model_id: String,
    pub dataset_sha256: String,
    pub split_sha256: String,
    pub benchmark_lock_sha256: String,
    pub feature_order: Vec<String>,
    pub rust_creep_coefficients: Vec<f64>,
    pub wet_adhesion_coefficients: Vec<f64>,
    pub residual_scales: BTreeMap<String, f64>,
    pub applicability_domain: ApplicabilityDomainV1,
    pub training_observation_hashes: BTreeMap<String, String>,
    pub promotion_dataset_complete: bool,
    pub authority: String,
}

impl EisModelArtifactV1 {
    pub fn validate(&self) -> Result<(), CorrosionError> {
        require_identity(&self.schema, MODEL_ARTIFACT_SCHEMA, &self.module_id)?;
        require_text("model_id", &self.model_id)?;
        for (field, hash) in [
            ("dataset_sha256", self.dataset_sha256.as_str()),
            ("split_sha256", self.split_sha256.as_str()),
            ("benchmark_lock_sha256", self.benchmark_lock_sha256.as_str()),
        ] {
            require_hash(field, hash)?;
        }
        if self.feature_order != feature_names()
            || self.rust_creep_coefficients.len() != self.feature_order.len()
            || self.wet_adhesion_coefficients.len() != self.feature_order.len()
            || self
                .rust_creep_coefficients
                .iter()
                .chain(&self.wet_adhesion_coefficients)
                .any(|value| !value.is_finite())
            || self
                .residual_scales
                .values()
                .any(|value| !value.is_finite() || *value < 0.0)
            || self.authority != "SHADOW"
        {
            return Err(CorrosionError::Range("model artifact"));
        }
        for hash in self.training_observation_hashes.values() {
            require_hash("training observation hash", hash)?;
        }
        validate_domain(&self.applicability_domain)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ObservationBundleV1 {
    pub schema: String,
    pub module_id: String,
    pub candidate_id: String,
    pub observation: EisObservationV1,
}

impl ObservationBundleV1 {
    pub fn validate(&self) -> Result<(), CorrosionError> {
        require_identity(&self.schema, OBSERVATION_BUNDLE_SCHEMA, &self.module_id)?;
        require_text("candidate_id", &self.candidate_id)?;
        self.observation.validate_conditions()?;
        if self.observation.candidate_id != self.candidate_id {
            return Err(CorrosionError::Parent);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EisPredictionV1 {
    pub schema: String,
    pub module_id: String,
    pub candidate_id: String,
    pub authority: String,
    pub estimated_rust_creep_mm: Option<f64>,
    pub estimated_wet_adhesion_mpa: Option<f64>,
    pub rust_creep_interval: Option<ConfidenceIntervalV1>,
    pub wet_adhesion_interval: Option<ConfidenceIntervalV1>,
    pub fitted_circuit: Option<EquivalentCircuitParametersV1>,
    pub circuit_fit_claimed: bool,
    pub barrier_index: Option<f64>,
    pub corrosion_rank: Option<f64>,
    pub in_applicability_domain: bool,
    pub abstention_reasons: Vec<String>,
}

impl EisPredictionV1 {
    fn abstain(candidate_id: &str, reason: impl Into<String>) -> Self {
        Self {
            schema: PREDICTION_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            candidate_id: candidate_id.into(),
            authority: "SHADOW".into(),
            estimated_rust_creep_mm: None,
            estimated_wet_adhesion_mpa: None,
            rust_creep_interval: None,
            wet_adhesion_interval: None,
            fitted_circuit: None,
            circuit_fit_claimed: false,
            barrier_index: None,
            corrosion_rank: None,
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
    pub external_systems_untouched: bool,
    pub endpoint_methods_accepted: bool,
    pub no_service_life_claim: bool,
    pub reviewer_independent: bool,
}

impl IndependentReviewV1 {
    pub fn validate(&self) -> Result<(), CorrosionError> {
        require_identity(&self.schema, INDEPENDENT_REVIEW_SCHEMA, &self.module_id)?;
        require_text("review_id", &self.review_id)?;
        require_hash("model_artifact_sha256", &self.model_artifact_sha256)?;
        require_hash("benchmark_receipt_sha256", &self.benchmark_receipt_sha256)?;
        if !self.external_systems_untouched
            || !self.endpoint_methods_accepted
            || !self.no_service_life_claim
            || !self.reviewer_independent
        {
            return Err(CorrosionError::Range("independent review"));
        }
        Ok(())
    }
}

pub fn evaluate_locked_benchmark(
    lock: &EisBenchmarkLockV1,
    dataset: &EisDatasetV1,
    split: &EisSplitV1,
    artifact: &EisModelArtifactV1,
    raw_file_hashes: &BTreeMap<String, String>,
    predictions: &[OutOfFoldPredictionV1],
) -> Result<BenchmarkReceiptV1, CorrosionError> {
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
        return Err(CorrosionError::Parent);
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
            return Err(CorrosionError::Leakage);
        }
    }
    if observed != expected {
        return Err(CorrosionError::Parent);
    }
    let tau = kendall_tau(predictions, false)?;
    let baseline_tau = kendall_tau(predictions, true)?;
    let (tau_lower, delta_lower) = study_block_tau_lower_bounds(predictions)?;
    let classification = balanced_accuracy(predictions, false)?;
    let baseline_classification = balanced_accuracy(predictions, true)?;
    let classification_lift = classification - baseline_classification;
    let calibration_error = expected_calibration_error(predictions);
    let coverage = predictions
        .iter()
        .map(|row| {
            usize::from(interval_contains(
                row.rust_creep_interval_90,
                row.observed_rust_creep_mm,
            )) + usize::from(interval_contains(
                row.wet_adhesion_interval_90,
                row.observed_wet_adhesion_mpa,
            ))
        })
        .sum::<usize>() as f64
        / (2 * predictions.len()) as f64;
    let mean_absolute_error =
        |prediction: fn(&OutOfFoldPredictionV1) -> f64,
         observed: fn(&OutOfFoldPredictionV1) -> f64| {
            predictions
                .iter()
                .map(|row| (prediction(row) - observed(row)).abs())
                .sum::<f64>()
                / predictions.len() as f64
        };
    let rust_mae = mean_absolute_error(
        |row| row.predicted_rust_creep_mm,
        |row| row.observed_rust_creep_mm,
    );
    let baseline_rust_mae = mean_absolute_error(
        |row| row.baseline_rust_creep_mm,
        |row| row.observed_rust_creep_mm,
    );
    let adhesion_mae = mean_absolute_error(
        |row| row.predicted_wet_adhesion_mpa,
        |row| row.observed_wet_adhesion_mpa,
    );
    let baseline_adhesion_mae = mean_absolute_error(
        |row| row.baseline_wet_adhesion_mpa,
        |row| row.observed_wet_adhesion_mpa,
    );
    let delta_tau = tau - baseline_tau;
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
            match (kendall_tau(&rows, false), kendall_tau(&rows, true)) {
                (Ok(theory), Ok(baseline)) => theory >= baseline,
                _ => false,
            }
        });
    let metrics = BenchmarkMetricsV1 {
        kendall_tau: tau,
        study_block_tau_lower_95: tau_lower,
        classification_balanced_accuracy: classification,
        baseline_classification_balanced_accuracy: baseline_classification,
        classification_lift,
        calibration_error,
        interval_90_coverage: coverage,
        rust_creep_mae_mm: rust_mae,
        baseline_rust_creep_mae_mm: baseline_rust_mae,
        wet_adhesion_mae_mpa: adhesion_mae,
        baseline_wet_adhesion_mae_mpa: baseline_adhesion_mae,
        baseline_kendall_tau: baseline_tau,
        delta_kendall_tau: delta_tau,
        delta_kendall_tau_lower_95: delta_lower,
    };
    let gate_status = BenchmarkGateStatusV1 {
        kendall_tau_at_least_0_50: tau >= 0.50,
        study_block_lower_positive: tau_lower > 0.0,
        classification_lift_at_least_0_10: classification_lift >= 0.10,
        calibration_error_at_most_0_10: calibration_error <= 0.10,
        interval_coverage_0_85_to_0_95: (0.85..=0.95).contains(&coverage),
        rust_creep_error_non_worse: rust_mae <= baseline_rust_mae,
        wet_adhesion_error_non_worse: adhesion_mae <= baseline_adhesion_mae,
        delta_tau_at_least_0_10: delta_tau >= 0.10,
        delta_tau_lower_positive: delta_lower > 0.0,
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
        .map_err(|error| CorrosionError::Json(error.to_string()))?;
    let seed = json!({
        "model": stable_hash(&serde_json::to_value(artifact).expect("artifact serializes")),
        "predictions": prediction_hashes,
    });
    let mut receipt = BenchmarkReceiptV1 {
        schema: BENCHMARK_RECEIPT_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        receipt_id: format!("barrier-benchmark-{}", &stable_hash(&seed)[..16]),
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

pub fn fit_model(
    dataset: &EisDatasetV1,
    split: &EisSplitV1,
    lock: &EisBenchmarkLockV1,
) -> Result<EisModelArtifactV1, CorrosionError> {
    dataset.validate()?;
    split.validate(Some(dataset))?;
    lock.validate()?;
    if lock.dataset_sha256 != dataset.identity_hash() || lock.split_sha256 != split.identity_hash()
    {
        return Err(CorrosionError::Parent);
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
    if training.len() < 2 {
        return Err(CorrosionError::Empty("at least two FIT observations"));
    }
    let features: Vec<_> = training
        .iter()
        .map(|row| endpoint_features(row))
        .collect::<Result<_, _>>()?;
    let rust: Vec<_> = training
        .iter()
        .map(|row| row.measured_rust_creep_mm.expect("measured validated"))
        .collect();
    let adhesion: Vec<_> = training
        .iter()
        .map(|row| row.measured_wet_adhesion_mpa.expect("measured validated"))
        .collect();
    let rust_coefficients = ridge_fit(&features, &rust, 1e-6)?;
    let adhesion_coefficients = ridge_fit(&features, &adhesion, 1e-6)?;
    let rust_residuals: Vec<_> = features
        .iter()
        .zip(&rust)
        .map(|(features, endpoint)| (endpoint - dot(features, &rust_coefficients)).abs())
        .collect();
    let adhesion_residuals: Vec<_> = features
        .iter()
        .zip(&adhesion)
        .map(|(features, endpoint)| (endpoint - dot(features, &adhesion_coefficients)).abs())
        .collect();
    let systems = training
        .iter()
        .map(|row| {
            (
                row.source_id.as_str(),
                row.study_id.as_str(),
                row.coating_system_id.as_str(),
            )
        })
        .collect::<BTreeSet<_>>()
        .len();
    let studies = training
        .iter()
        .map(|row| (row.source_id.as_str(), row.study_id.as_str()))
        .collect::<BTreeSet<_>>()
        .len();
    let external_systems = split
        .assignments
        .iter()
        .filter(|row| row.split == "EXTERNAL")
        .map(|row| {
            (
                row.source_id.as_str(),
                row.study_id.as_str(),
                row.coating_system_id.as_str(),
            )
        })
        .collect::<BTreeSet<_>>()
        .len();
    let minimum_panels = training
        .iter()
        .fold(
            BTreeMap::<(&str, i64), BTreeSet<&str>>::new(),
            |mut rows, row| {
                rows.entry((
                    row.coating_system_id.as_str(),
                    row.exposure_hours.round() as i64,
                ))
                .or_default()
                .insert(row.panel_id.as_str());
                rows
            },
        )
        .values()
        .map(BTreeSet::len)
        .min()
        .unwrap_or(0);
    let promotion_dataset_complete =
        systems >= 30 && studies >= 3 && external_systems >= 10 && minimum_panels >= 5;
    let seed = json!({
        "dataset": dataset.identity_hash(),
        "split": split.identity_hash(),
        "lock": lock.identity_hash(),
    });
    let artifact = EisModelArtifactV1 {
        schema: MODEL_ARTIFACT_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        model_id: format!("measured-eis-endpoints-{}", &stable_hash(&seed)[..16]),
        dataset_sha256: dataset.identity_hash(),
        split_sha256: split.identity_hash(),
        benchmark_lock_sha256: lock.identity_hash(),
        feature_order: feature_names(),
        rust_creep_coefficients: rust_coefficients,
        wet_adhesion_coefficients: adhesion_coefficients,
        residual_scales: BTreeMap::from([
            ("rust_creep_mm".into(), quantile90(&rust_residuals)),
            ("wet_adhesion_mpa".into(), quantile90(&adhesion_residuals)),
        ]),
        applicability_domain: build_domain(&training),
        training_observation_hashes: training
            .iter()
            .map(|row| (row.observation_id.clone(), row.identity_hash()))
            .collect(),
        promotion_dataset_complete,
        authority: "SHADOW".into(),
    };
    artifact.validate()?;
    Ok(artifact)
}

/// Standard EIS barrier metric: `log10(|Z| / (ohm*cm^2))` at the lowest
/// measured frequency of a full frequency-resolved spectrum. Convention:
/// the low-frequency impedance modulus tracks coating barrier integrity
/// (water uptake degrades coating capacitance/resistance; Brasher &
/// Kingsbury 1954, J. Appl. Chem. 4:62-72), so higher barrier_index means
/// better barrier. This is a direct reading of the measured spectrum, not
/// an equivalent-circuit claim, and therefore never implies
/// `circuit_fit_claimed`. Fail-closed by construction: returns `None` for
/// summary-only inputs (no full multi-frequency spectrum), degenerate
/// spectra (empty, single-point, non-finite or non-positive frequency or
/// impedance components, |Z| <= 0), and rights-ineligible observations.
/// `validate_conditions()` already enforces the rights gate and spectrum
/// shape upstream in `predict()`; the checks here are deliberately
/// re-applied so the helper fails closed even if called on its own.
fn barrier_index_from_spectrum(observation: &EisObservationV1) -> Option<f64> {
    if observation.spectrum_kind != SpectrumKindV1::FullFrequencyResolved
        || observation.spectrum.len() < 2
        || !observation.rights_eligible
    {
        return None;
    }
    // A validated full spectrum is strictly descending in frequency, so the
    // last point is the lowest measured frequency.
    let lowest = observation.spectrum.last()?;
    if !finite_positive(lowest.frequency_hz)
        || !lowest.real_ohm_cm2.is_finite()
        || !lowest.imaginary_ohm_cm2.is_finite()
    {
        return None;
    }
    let modulus = lowest.real_ohm_cm2.hypot(lowest.imaginary_ohm_cm2);
    if !finite_positive(modulus) {
        return None;
    }
    let barrier_index = modulus.log10();
    barrier_index.is_finite().then_some(barrier_index)
}

pub fn predict(
    artifact: &EisModelArtifactV1,
    observation: &EisObservationV1,
) -> Result<EisPredictionV1, CorrosionError> {
    artifact.validate()?;
    observation.validate_conditions()?;
    if !in_domain(observation, &artifact.applicability_domain) {
        return Ok(EisPredictionV1::abstain(
            &observation.candidate_id,
            "protocol, coating family, substrate, DFT, temperature, exposure, or spectrum kind is outside the locked domain",
        ));
    }
    // V1 spectra have no linear Kramers-Kronig, stationarity, or multi-start
    // identifiability receipt. They therefore fall back to low-frequency
    // diagnostics and may not support an equivalent-circuit claim.
    let fitted_circuit = None;
    let features = endpoint_features_with_circuit(observation, fitted_circuit)?;
    let rust = dot(&features, &artifact.rust_creep_coefficients).max(0.0);
    let adhesion = dot(&features, &artifact.wet_adhesion_coefficients).max(0.0);
    if !rust.is_finite() || !adhesion.is_finite() {
        return Ok(EisPredictionV1::abstain(
            &observation.candidate_id,
            "non-finite endpoint model result",
        ));
    }
    let rust_width = artifact.residual_scales["rust_creep_mm"];
    let adhesion_width = artifact.residual_scales["wet_adhesion_mpa"];
    // Locked-KPI primary value path (`metrics.barrier_index`): computed only
    // when this in-domain, rights-eligible observation carries a full
    // multi-frequency spectrum; otherwise stays None (fail-closed). See
    // `barrier_index_from_spectrum` for the Brasher-Kingsbury convention.
    let barrier_index = barrier_index_from_spectrum(observation);
    Ok(EisPredictionV1 {
        schema: PREDICTION_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        candidate_id: observation.candidate_id.clone(),
        authority: "SHADOW".into(),
        estimated_rust_creep_mm: Some(rust),
        estimated_wet_adhesion_mpa: Some(adhesion),
        rust_creep_interval: Some(interval((rust - rust_width).max(0.0), rust + rust_width)),
        wet_adhesion_interval: Some(interval(
            (adhesion - adhesion_width).max(0.0),
            adhesion + adhesion_width,
        )),
        fitted_circuit,
        circuit_fit_claimed: fitted_circuit.is_some(),
        barrier_index,
        corrosion_rank: None,
        in_applicability_domain: true,
        abstention_reasons: Vec::new(),
    })
}

pub fn evaluate(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> ModuleResult {
    let abstain = |reason: String| {
        let prediction = EisPredictionV1::abstain(candidate.candidate_id(), reason.clone());
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
    let artifact: EisModelArtifactV1 = match serde_json::from_value(binding.model_artifact) {
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
    prediction: &EisPredictionV1,
    reason: Option<String>,
) -> ModuleResult {
    let available = prediction.estimated_rust_creep_mm.is_some()
        && prediction.estimated_wet_adhesion_mpa.is_some();
    ModuleResult {
        status: if available { "NO_AUTHORITY".into() } else { "INSUFFICIENT_INPUT".into() },
        score_0_1: None,
        objective_values: BTreeMap::new(),
        metrics: BTreeMap::from([
            ("candidate_contract_hash_v1".into(), json!(candidate.contract_hash_v1())),
            ("ranking_quarantine".into(), Value::Bool(true)),
            ("scientific_applicability".into(), json!(if available { "MEASURED_EIS_ENDPOINT_SHADOW" } else { "UNVALIDATED" })),
            ("estimated_rust_creep_mm".into(), json!(prediction.estimated_rust_creep_mm)),
            ("estimated_wet_adhesion_mpa".into(), json!(prediction.estimated_wet_adhesion_mpa)),
            ("barrier_index".into(), json!(prediction.barrier_index)),
            ("corrosion_rank".into(), Value::Null),
            ("service_life".into(), Value::Null),
            ("prediction".into(), serde_json::to_value(prediction).expect("prediction serializes")),
        ]),
        gates: BTreeMap::from([
            ("host_verified_candidate_bound_eis".into(), Value::Bool(available)),
            ("in_applicability_domain".into(), Value::Bool(prediction.in_applicability_domain)),
            ("audit_only".into(), Value::Bool(true)),
        ]),
        uncertainty: BTreeMap::from([
            ("rust_creep_90".into(), json!(prediction.rust_creep_interval)),
            ("wet_adhesion_90".into(), json!(prediction.wet_adhesion_interval)),
        ]),
        missing_inputs: reason.into_iter().collect(),
        explanations: vec!["Endpoints are estimated only from candidate-bound measured EIS and declared lab conditions; a single-frequency summary never claims circuit fitting or service life.".into()],
        source_refs: vec![
            "https://data.usbr.gov/catalog/8048".into(),
            "https://www.mdpi.com/2079-6412/13/3/598".into(),
        ],
        evidence_scope: "MEASURED_EIS_ENDPOINT_SHADOW_ONLY".into(),
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ContractKind {
    Observation,
    ObservationV2,
    Dataset,
    Split,
    BenchmarkLock,
    ModelArtifact,
    Prediction,
    IndependentReview,
    BenchmarkReceipt,
}

pub fn preflight(kind: ContractKind, value: Value) -> Result<(String, String), CorrosionError> {
    match kind {
        ContractKind::Observation => {
            let contract: EisObservationV1 = decode(value)?;
            contract.validate_conditions()?;
            Ok((contract.schema, contract.observation_id))
        }
        ContractKind::ObservationV2 => {
            let contract: EisObservationV2 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.observation.observation_id))
        }
        ContractKind::Dataset => {
            let contract: EisDatasetV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.dataset_id))
        }
        ContractKind::Split => {
            let contract: EisSplitV1 = decode(value)?;
            contract.validate(None)?;
            Ok((contract.schema, contract.split_id))
        }
        ContractKind::BenchmarkLock => {
            let contract: EisBenchmarkLockV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.benchmark_id))
        }
        ContractKind::ModelArtifact => {
            let contract: EisModelArtifactV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.model_id))
        }
        ContractKind::Prediction => {
            let contract: EisPredictionV1 = decode(value)?;
            if contract.schema != PREDICTION_SCHEMA || contract.module_id != MODULE_ID {
                return Err(CorrosionError::Identity);
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

fn endpoint_features(observation: &EisObservationV1) -> Result<Vec<f64>, CorrosionError> {
    endpoint_features_with_circuit(observation, None)
}

fn endpoint_features_with_circuit(
    observation: &EisObservationV1,
    circuit: Option<EquivalentCircuitParametersV1>,
) -> Result<Vec<f64>, CorrosionError> {
    let latest_summary = observation.summaries.last();
    let (log_impedance, phase, ocv_stability, slope) = if observation.summaries.is_empty() {
        let lowest = observation.spectrum.last().ok_or(CorrosionError::Method)?;
        (
            lowest.real_ohm_cm2.hypot(lowest.imaginary_ohm_cm2).ln(),
            lowest
                .imaginary_ohm_cm2
                .atan2(lowest.real_ohm_cm2)
                .to_degrees(),
            0.0,
            0.0,
        )
    } else {
        let latest = latest_summary.expect("summary nonempty");
        let slope_points: Vec<_> = observation
            .summaries
            .iter()
            .map(|row| (row.exposure_hours, row.impedance_modulus_ohm_cm2.ln()))
            .collect();
        let min_ocv = observation
            .summaries
            .iter()
            .map(|row| row.ocv_v)
            .fold(f64::INFINITY, f64::min);
        let max_ocv = observation
            .summaries
            .iter()
            .map(|row| row.ocv_v)
            .fold(f64::NEG_INFINITY, f64::max);
        (
            latest.impedance_modulus_ohm_cm2.ln(),
            latest.phase_deg,
            max_ocv - min_ocv,
            theil_sen_slope(&slope_points)?,
        )
    };
    let circuit_log_resistance = circuit
        .map(|parameters| {
            (parameters.coating_resistance_ohm_cm2 + parameters.charge_transfer_resistance_ohm_cm2)
                .ln()
        })
        .unwrap_or(log_impedance);
    Ok(vec![
        1.0,
        circuit_log_resistance,
        phase / 180.0,
        slope,
        ocv_stability,
        observation.replicate_log_impedance_dispersion,
        (1.0 + observation.exposure_hours).ln(),
    ])
}

fn feature_names() -> Vec<String> {
    [
        "intercept",
        "log_resistance_feature",
        "phase_scaled",
        "theil_sen_log_impedance_slope",
        "ocv_range_v",
        "replicate_log_impedance_dispersion",
        "log1p_exposure_hours",
    ]
    .into_iter()
    .map(str::to_owned)
    .collect()
}

fn ridge_fit(x: &[Vec<f64>], y: &[f64], lambda: f64) -> Result<Vec<f64>, CorrosionError> {
    let dimension = x[0].len();
    let mut matrix = vec![vec![0.0; dimension]; dimension];
    let mut vector = vec![0.0; dimension];
    for (row, endpoint) in x.iter().zip(y) {
        for i in 0..dimension {
            vector[i] += row[i] * endpoint;
            for j in 0..dimension {
                matrix[i][j] += row[i] * row[j];
            }
        }
    }
    for (index, row) in matrix.iter_mut().enumerate().skip(1) {
        row[index] += lambda;
    }
    solve_linear(matrix, vector).ok_or(CorrosionError::NonConvergent)
}

fn solve_linear(mut matrix: Vec<Vec<f64>>, mut vector: Vec<f64>) -> Option<Vec<f64>> {
    let n = vector.len();
    for column in 0..n {
        let pivot = (column..n).max_by(|left, right| {
            matrix[*left][column]
                .abs()
                .total_cmp(&matrix[*right][column].abs())
        })?;
        if matrix[pivot][column].abs() < 1e-12 {
            return None;
        }
        matrix.swap(column, pivot);
        vector.swap(column, pivot);
        let scale = matrix[column][column];
        for value in &mut matrix[column][column..] {
            *value /= scale;
        }
        vector[column] /= scale;
        let pivot_row = matrix[column].clone();
        for row in 0..n {
            if row == column {
                continue;
            }
            let factor = matrix[row][column];
            for (value, pivot) in matrix[row][column..].iter_mut().zip(&pivot_row[column..]) {
                *value -= factor * pivot;
            }
            vector[row] -= factor * vector[column];
        }
    }
    Some(vector)
}

fn dot(left: &[f64], right: &[f64]) -> f64 {
    left.iter()
        .zip(right)
        .map(|(left, right)| left * right)
        .sum()
}

fn build_domain(training: &[&EisObservationV1]) -> ApplicabilityDomainV1 {
    let range = |values: Vec<f64>| {
        [
            values.iter().copied().fold(f64::INFINITY, f64::min),
            values.iter().copied().fold(f64::NEG_INFINITY, f64::max),
        ]
    };
    ApplicabilityDomainV1 {
        coating_families: sorted_unique(training.iter().map(|row| row.coating_family.clone())),
        substrates: sorted_unique(training.iter().map(|row| row.substrate.clone())),
        protocols: sorted_unique(training.iter().map(|row| row.protocol_id.clone())),
        temperature_c: range(training.iter().map(|row| row.temperature_c).collect()),
        dft_um: range(training.iter().map(|row| row.dft_um).collect()),
        exposure_hours: range(training.iter().map(|row| row.exposure_hours).collect()),
        spectrum_kinds: training
            .iter()
            .map(|row| row.spectrum_kind)
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect(),
    }
}

fn sorted_unique(values: impl Iterator<Item = String>) -> Vec<String> {
    values.collect::<BTreeSet<_>>().into_iter().collect()
}

fn validate_domain(domain: &ApplicabilityDomainV1) -> Result<(), CorrosionError> {
    if domain.coating_families.is_empty()
        || domain.substrates.is_empty()
        || domain.protocols.is_empty()
        || domain.spectrum_kinds.is_empty()
        || [domain.temperature_c, domain.dft_um, domain.exposure_hours]
            .iter()
            .any(|range| range[0] > range[1] || range.iter().any(|value| !value.is_finite()))
    {
        Err(CorrosionError::Range("applicability domain"))
    } else {
        Ok(())
    }
}

fn in_domain(observation: &EisObservationV1, domain: &ApplicabilityDomainV1) -> bool {
    let contains = |range: [f64; 2], value: f64| value >= range[0] && value <= range[1];
    domain
        .coating_families
        .contains(&observation.coating_family)
        && domain.substrates.contains(&observation.substrate)
        && domain.protocols.contains(&observation.protocol_id)
        && domain.spectrum_kinds.contains(&observation.spectrum_kind)
        && contains(domain.temperature_c, observation.temperature_c)
        && contains(domain.dft_um, observation.dft_um)
        && contains(domain.exposure_hours, observation.exposure_hours)
}

fn interval(lower: f64, upper: f64) -> ConfidenceIntervalV1 {
    ConfidenceIntervalV1 {
        lower,
        upper,
        confidence: 0.9,
        method: "LOCKED_SYSTEM_CLUSTER_RESIDUAL_90".into(),
    }
}

fn quantile90(values: &[f64]) -> f64 {
    let mut values = values.to_vec();
    values.sort_by(f64::total_cmp);
    values[((values.len() - 1) as f64 * 0.9).ceil() as usize]
}

fn interval_contains(interval: [f64; 2], value: f64) -> bool {
    value >= interval[0] && value <= interval[1]
}

fn kendall_tau(rows: &[OutOfFoldPredictionV1], baseline: bool) -> Result<f64, CorrosionError> {
    if rows.len() < 2 {
        return Err(CorrosionError::Empty("ranked systems"));
    }
    let predicted = |row: &OutOfFoldPredictionV1| {
        if baseline {
            row.baseline_barrier_order
        } else {
            row.predicted_barrier_order
        }
    };
    let mut concordant = 0.0_f64;
    let mut discordant = 0.0_f64;
    let mut observed_ties = 0.0_f64;
    let mut predicted_ties = 0.0_f64;
    for i in 0..rows.len() {
        for j in (i + 1)..rows.len() {
            let observed =
                (rows[i].observed_barrier_order - rows[j].observed_barrier_order).total_cmp(&0.0);
            let prediction = (predicted(&rows[i]) - predicted(&rows[j])).total_cmp(&0.0);
            match (observed, prediction) {
                (std::cmp::Ordering::Equal, std::cmp::Ordering::Equal) => {}
                (std::cmp::Ordering::Equal, _) => observed_ties += 1.0,
                (_, std::cmp::Ordering::Equal) => predicted_ties += 1.0,
                (left, right) if left == right => concordant += 1.0,
                _ => discordant += 1.0,
            }
        }
    }
    let denominator = ((concordant + discordant + observed_ties)
        * (concordant + discordant + predicted_ties))
        .sqrt();
    if denominator == 0.0 {
        Err(CorrosionError::Empty("non-tied rank pairs"))
    } else {
        Ok((concordant - discordant) / denominator)
    }
}

fn balanced_accuracy(
    rows: &[OutOfFoldPredictionV1],
    baseline: bool,
) -> Result<f64, CorrosionError> {
    let mut positive = [0_usize; 2];
    let mut negative = [0_usize; 2];
    for row in rows {
        let predicted = if baseline {
            row.baseline_failure_probability >= 0.5
        } else {
            row.predicted_failure_probability >= 0.5
        };
        let bucket = if row.observed_failure {
            &mut positive
        } else {
            &mut negative
        };
        bucket[1] += 1;
        bucket[0] += usize::from(predicted == row.observed_failure);
    }
    if positive[1] == 0 || negative[1] == 0 {
        return Err(CorrosionError::Empty("both failure classes"));
    }
    Ok(0.5 * (positive[0] as f64 / positive[1] as f64 + negative[0] as f64 / negative[1] as f64))
}

fn expected_calibration_error(rows: &[OutOfFoldPredictionV1]) -> f64 {
    let mut weighted = 0.0;
    for bin in 0..10 {
        let lower = bin as f64 / 10.0;
        let upper = (bin + 1) as f64 / 10.0;
        let members: Vec<_> = rows
            .iter()
            .filter(|row| {
                row.predicted_failure_probability >= lower
                    && (row.predicted_failure_probability < upper
                        || bin == 9 && row.predicted_failure_probability == 1.0)
            })
            .collect();
        if members.is_empty() {
            continue;
        }
        let confidence = members
            .iter()
            .map(|row| row.predicted_failure_probability)
            .sum::<f64>()
            / members.len() as f64;
        let frequency =
            members.iter().filter(|row| row.observed_failure).count() as f64 / members.len() as f64;
        weighted += members.len() as f64 / rows.len() as f64 * (confidence - frequency).abs();
    }
    weighted
}

fn study_block_tau_lower_bounds(
    rows: &[OutOfFoldPredictionV1],
) -> Result<(f64, f64), CorrosionError> {
    let mut studies = BTreeMap::<&str, Vec<&OutOfFoldPredictionV1>>::new();
    for row in rows {
        studies.entry(row.study_id.as_str()).or_default().push(row);
    }
    if studies.len() < 2 {
        let theory = kendall_tau(rows, false)?;
        return Ok((theory, theory - kendall_tau(rows, true)?));
    }
    let studies: Vec<_> = studies.values().collect();
    let mut state = RESIDUAL_MODEL_SEED;
    let mut taus = Vec::with_capacity(10_000);
    let mut deltas = Vec::with_capacity(10_000);
    for _ in 0..10_000 {
        let mut sampled = Vec::new();
        for _ in 0..studies.len() {
            state = state
                .wrapping_mul(6_364_136_223_846_793_005)
                .wrapping_add(1_442_695_040_888_963_407);
            sampled.extend(
                studies[(state as usize) % studies.len()]
                    .iter()
                    .map(|row| (*row).clone()),
            );
        }
        if let (Ok(theory), Ok(baseline)) =
            (kendall_tau(&sampled, false), kendall_tau(&sampled, true))
        {
            taus.push(theory);
            deltas.push(theory - baseline);
        }
    }
    if taus.len() < 250 {
        return Err(CorrosionError::Empty("rankable bootstrap replicates"));
    }
    taus.sort_by(f64::total_cmp);
    deltas.sort_by(f64::total_cmp);
    let index = ((taus.len() - 1) as f64 * 0.025).floor() as usize;
    Ok((taus[index], deltas[index]))
}

fn decode<T: for<'de> Deserialize<'de>>(value: Value) -> Result<T, CorrosionError> {
    serde_json::from_value(value).map_err(|error| CorrosionError::Json(error.to_string()))
}

fn require_identity(schema: &str, expected: &str, module: &str) -> Result<(), CorrosionError> {
    if schema == expected && module == MODULE_ID {
        Ok(())
    } else {
        Err(CorrosionError::Identity)
    }
}

fn require_text(field: &'static str, value: &str) -> Result<(), CorrosionError> {
    if value.trim().is_empty() {
        Err(CorrosionError::Empty(field))
    } else {
        Ok(())
    }
}

fn require_hash(field: &'static str, value: &str) -> Result<(), CorrosionError> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(CorrosionError::Hash(field))
    }
}

fn validate_hash_map(values: &BTreeMap<String, String>) -> Result<(), CorrosionError> {
    if values.is_empty() {
        return Err(CorrosionError::Empty("raw_file_hashes"));
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

#[cfg(test)]
mod tests {
    use super::*;

    fn measured_summary_observation(index: usize) -> EisObservationV1 {
        let scale = index as f64 + 1.0;
        EisObservationV1 {
            schema: OBSERVATION_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            observation_id: format!("obs-{index}"),
            candidate_id: format!("candidate-{index}"),
            source_id: "source-1".into(),
            study_id: "study-1".into(),
            coating_system_id: format!("system-{index}"),
            coating_family: "epoxy".into(),
            panel_id: format!("panel-{index}"),
            replicate_id: "replicate-1".into(),
            protocol_id: "protocol-1".into(),
            method_class: "LAB_EIS".into(),
            cell_area_cm2: 10.0,
            dft_um: 250.0,
            substrate: "steel".into(),
            temperature_c: 25.0,
            exposure_medium: "3.5% NaCl".into(),
            exposure_hours: 100.0,
            spectrum_kind: SpectrumKindV1::SingleFrequencySummary,
            spectrum: Vec::new(),
            summaries: vec![
                EisSummaryPointV1 {
                    exposure_hours: 0.0,
                    low_frequency_hz: 0.01,
                    impedance_modulus_ohm_cm2: 1.0e8 / scale,
                    phase_deg: -80.0,
                    ocv_v: -0.50,
                },
                EisSummaryPointV1 {
                    exposure_hours: 100.0,
                    low_frequency_hz: 0.01,
                    impedance_modulus_ohm_cm2: 5.0e7 / scale,
                    phase_deg: -70.0 + scale,
                    ocv_v: -0.50 - 0.01 * scale,
                },
            ],
            replicate_log_impedance_dispersion: 0.05 * scale,
            measured_rust_creep_mm: Some(0.5 * scale),
            measured_wet_adhesion_mpa: Some(8.0 / scale),
            raw_file_hashes: BTreeMap::from([(
                format!("system-{index}.xlsx"),
                format!("{index:x}").repeat(64),
            )]),
            rights_receipt_sha256: "a".repeat(64),
            rights_eligible: true,
        }
    }

    fn measured_full_spectrum_observation(index: usize) -> EisObservationV1 {
        let parameters = EquivalentCircuitParametersV1 {
            solution_resistance_ohm_cm2: 25.0,
            coating_resistance_ohm_cm2: 2.0e5,
            coating_q_s_n_ohm_inv_cm2: 1.0e-7,
            coating_exponent: 0.88,
            charge_transfer_resistance_ohm_cm2: 8.0e4,
            double_layer_q_s_n_ohm_inv_cm2: 1.0e-5,
            double_layer_exponent: 0.82,
        };
        let mut observation = measured_summary_observation(index);
        observation.spectrum_kind = SpectrumKindV1::FullFrequencyResolved;
        observation.summaries.clear();
        observation.spectrum = (0..16)
            .map(|step| 10_f64.powf(5.0 - step as f64 * 0.5))
            .map(|frequency_hz| {
                let (real_ohm_cm2, imaginary_ohm_cm2) =
                    simulate_equivalent_circuit(parameters, frequency_hz).unwrap();
                EisPointV1 {
                    frequency_hz,
                    real_ohm_cm2,
                    imaginary_ohm_cm2,
                }
            })
            .collect();
        observation
    }

    #[test]
    fn test_synthetic_equivalent_circuit_is_recovered() {
        let expected = EquivalentCircuitParametersV1 {
            solution_resistance_ohm_cm2: 25.0,
            coating_resistance_ohm_cm2: 2.0e5,
            coating_q_s_n_ohm_inv_cm2: 1.0e-7,
            coating_exponent: 0.88,
            charge_transfer_resistance_ohm_cm2: 8.0e4,
            double_layer_q_s_n_ohm_inv_cm2: 1.0e-5,
            double_layer_exponent: 0.82,
        };
        let spectrum: Vec<_> = (0..16)
            .map(|index| 10_f64.powf(5.0 - index as f64 * 0.5))
            .map(|frequency_hz| {
                let (real_ohm_cm2, imaginary_ohm_cm2) =
                    simulate_equivalent_circuit(expected, frequency_hz).unwrap();
                EisPointV1 {
                    frequency_hz,
                    real_ohm_cm2,
                    imaginary_ohm_cm2,
                }
            })
            .collect();
        let fitted = fit_equivalent_circuit(&spectrum).unwrap();
        let mean_relative_error = spectrum
            .iter()
            .map(|point| {
                let observed = point.real_ohm_cm2.hypot(point.imaginary_ohm_cm2);
                let (real, imaginary) =
                    simulate_equivalent_circuit(fitted, point.frequency_hz).unwrap();
                (real.hypot(imaginary) / observed - 1.0).abs()
            })
            .sum::<f64>()
            / spectrum.len() as f64;
        assert!(mean_relative_error < 0.05, "{mean_relative_error}");
    }

    #[test]
    fn test_theil_sen_slope_and_time_reversal_are_distinct() {
        let points = [(0.0, 10.0), (1.0, 9.0), (2.0, 8.0), (3.0, 7.0)];
        let forward = theil_sen_slope(&points).unwrap();
        let reversed: Vec<_> = points
            .iter()
            .map(|(time, value)| (3.0 - time, *value))
            .collect();
        let backward = theil_sen_slope(&reversed).unwrap();
        assert!(forward < 0.0);
        assert!(backward > 0.0);
    }

    #[test]
    fn test_short_or_field_spectrum_cannot_claim_circuit_fit() {
        assert!(fit_equivalent_circuit(&[]).is_err());
        let error = serde_json::from_value::<EisPointV1>(json!({
            "frequency_hz": 1.0,
            "real_ohm_cm2": 2.0,
            "imaginary_ohm_cm2": -1.0,
            "service_life_years": 20.0
        }))
        .unwrap_err();
        assert!(error.to_string().contains("unknown field"));
    }

    #[test]
    fn eis_v2_rejects_clipping_and_requires_all_identifiability_gates() {
        let parameters = EquivalentCircuitParametersV1 {
            solution_resistance_ohm_cm2: 25.0,
            coating_resistance_ohm_cm2: 2.0e5,
            coating_q_s_n_ohm_inv_cm2: 1.0e-7,
            coating_exponent: 0.88,
            charge_transfer_resistance_ohm_cm2: 8.0e4,
            double_layer_q_s_n_ohm_inv_cm2: 1.0e-5,
            double_layer_exponent: 0.82,
        };
        let spectrum: Vec<_> = (0..=70)
            .map(|index| 10_f64.powf(5.0 - index as f64 * 0.1))
            .map(|frequency_hz| {
                let (real_ohm_cm2, imaginary_ohm_cm2) =
                    simulate_equivalent_circuit(parameters, frequency_hz).unwrap();
                EisPointV1 {
                    frequency_hz,
                    real_ohm_cm2,
                    imaginary_ohm_cm2,
                }
            })
            .collect();
        let mut observation = measured_summary_observation(1);
        observation.spectrum_kind = SpectrumKindV1::FullFrequencyResolved;
        observation.spectrum = spectrum;
        observation.summaries.clear();
        let mut v2 = EisObservationV2 {
            schema: OBSERVATION_V2_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            observation,
            acquisition_amplitude_mv_rms: 10.0,
            frequency_high_hz: 100_000.0,
            frequency_low_hz: 0.01,
            points_per_decade: 10,
            stabilization_duration_min: 30.0,
            stabilization_ocv_drift_mv_per_min: 0.1,
            instrument_id: "eis-1".into(),
            calibration_sha256: "a".repeat(64),
            stationarity_checked: true,
            stationary: true,
            clipped: false,
            dummy_cell_control_passed: true,
            linear_kramers_kronig_residual_rms: 0.01,
            linear_kramers_kronig_residual_whiteness_passed: true,
            linear_kramers_kronig_passed: true,
        };
        v2.validate().unwrap();
        v2.clipped = true;
        assert_eq!(v2.validate(), Err(CorrosionError::Method));
        v2.clipped = false;
        let mut diagnostics = CircuitFitDiagnosticsV2 {
            parameters,
            start_count: 31,
            converged_start_count: 31,
            stable_topology: true,
            maximum_parameter_coefficient_of_variation: 0.2,
            hessian_condition_number: 1.0e6,
        };
        assert_eq!(
            diagnostics.eligible_parameters(&v2),
            Err(CorrosionError::NonConvergent)
        );
        diagnostics.start_count = 32;
        diagnostics.converged_start_count = 32;
        assert_eq!(diagnostics.eligible_parameters(&v2).unwrap(), parameters);
    }

    #[test]
    fn test_fit_keeps_endpoints_separate_and_summary_never_claims_circuit() {
        let observations = vec![
            measured_summary_observation(1),
            measured_summary_observation(2),
            measured_full_spectrum_observation(3),
        ];
        let dataset = EisDatasetV1 {
            schema: DATASET_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            dataset_id: "dataset-1".into(),
            observations: observations.clone(),
        };
        let split = EisSplitV1 {
            schema: SPLIT_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            split_id: "split-1".into(),
            dataset_sha256: dataset.identity_hash(),
            assignments: observations
                .iter()
                .map(|row| SplitAssignmentV1 {
                    observation_id: row.observation_id.clone(),
                    source_id: row.source_id.clone(),
                    study_id: row.study_id.clone(),
                    coating_system_id: row.coating_system_id.clone(),
                    split: "FIT".into(),
                })
                .collect(),
        };
        let lock = EisBenchmarkLockV1 {
            schema: BENCHMARK_LOCK_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            benchmark_id: "benchmark-1".into(),
            dataset_sha256: dataset.identity_hash(),
            split_sha256: split.identity_hash(),
            baselines: vec![
                "CURRENT_FULL_SPECTRUM".into(),
                "LOW_FREQUENCY_IMPEDANCE".into(),
                "SOLIDS_ONLY".into(),
                "PVC_ONLY".into(),
                "BLINDED_COATINGS_EXPERT".into(),
            ],
            hostile_nulls: vec![
                "LEAKAGE".into(),
                "SHUFFLE".into(),
                "TIME_REVERSAL".into(),
                "UNIT_AREA_MISMATCH".into(),
                "CLIPPED_SPECTRUM".into(),
                "FIELD_LAB_METHOD_MISMATCH".into(),
            ],
            thresholds: BTreeMap::new(),
            immutable: true,
        };
        let first = fit_model(&dataset, &split, &lock).unwrap();
        let second = fit_model(&dataset, &split, &lock).unwrap();
        assert_eq!(first, second);
        assert!(!first.promotion_dataset_complete);
        assert_ne!(
            first.rust_creep_coefficients,
            first.wet_adhesion_coefficients
        );

        let prediction = predict(&first, &observations[0]).unwrap();
        assert!(prediction.estimated_rust_creep_mm.is_some());
        assert!(prediction.estimated_wet_adhesion_mpa.is_some());
        assert!(prediction.rust_creep_interval.is_some());
        assert!(prediction.wet_adhesion_interval.is_some());
        assert!(!prediction.circuit_fit_claimed);
        assert!(prediction.fitted_circuit.is_none());
        // Summary-only input has an empty spectrum: barrier_index stays None
        // (fail-closed; no full multi-frequency spectrum to read).
        assert!(prediction.barrier_index.is_none());
        assert!(prediction.corrosion_rank.is_none());

        // Full multi-frequency reference input on the same fitted model:
        // barrier_index is Some, pinned to log10 |Z| at the lowest measured
        // frequency of the spectrum (Brasher-Kingsbury convention), and still
        // never an equivalent-circuit claim.
        let full_prediction = predict(&first, &observations[2]).unwrap();
        assert!(full_prediction.in_applicability_domain);
        assert!(!full_prediction.circuit_fit_claimed);
        assert!(full_prediction.fitted_circuit.is_none());
        let lowest = observations[2].spectrum.last().unwrap();
        let expected_barrier_index =
            lowest.real_ohm_cm2.hypot(lowest.imaginary_ohm_cm2).log10();
        assert_eq!(
            full_prediction.barrier_index,
            Some(expected_barrier_index)
        );
        let observed_barrier_index = full_prediction.barrier_index.unwrap();
        assert!(
            (5.0..6.0).contains(&observed_barrier_index),
            "{observed_barrier_index}"
        );

        let mut field = observations[0].clone();
        field.method_class = "FIELD_EIS".into();
        assert_eq!(field.validate_conditions(), Err(CorrosionError::Method));
    }

    #[test]
    fn test_barrier_index_fails_closed_on_degenerate_spectra() {
        // Summary-only observation: spectrum is empty -> None.
        let summary_only = measured_summary_observation(1);
        assert!(summary_only.spectrum.is_empty());
        assert_eq!(barrier_index_from_spectrum(&summary_only), None);

        // The remaining cases deliberately bypass validate_conditions() to
        // prove the helper fails closed on its own, not only behind the
        // upstream validation gates.
        let mut empty = measured_full_spectrum_observation(1);
        empty.spectrum.clear();
        assert_eq!(barrier_index_from_spectrum(&empty), None);

        let mut single_point = measured_full_spectrum_observation(1);
        single_point.spectrum.truncate(1);
        assert_eq!(barrier_index_from_spectrum(&single_point), None);

        let mut non_finite = measured_full_spectrum_observation(1);
        non_finite.spectrum.last_mut().unwrap().real_ohm_cm2 = f64::NAN;
        assert_eq!(barrier_index_from_spectrum(&non_finite), None);

        let mut zero_modulus = measured_full_spectrum_observation(1);
        {
            let last = zero_modulus.spectrum.last_mut().unwrap();
            last.real_ohm_cm2 = 0.0;
            last.imaginary_ohm_cm2 = 0.0;
        }
        assert_eq!(barrier_index_from_spectrum(&zero_modulus), None);

        let mut rights_ineligible = measured_full_spectrum_observation(1);
        rights_ineligible.rights_eligible = false;
        assert_eq!(barrier_index_from_spectrum(&rights_ineligible), None);

        // A well-formed full spectrum yields Some (sanity complement).
        let full = measured_full_spectrum_observation(1);
        assert!(barrier_index_from_spectrum(&full).is_some());
    }
}
