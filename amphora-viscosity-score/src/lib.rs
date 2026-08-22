#![forbid(unsafe_code)]

use amphora_core::{
    stable_hash, CandidateEnvelope, ConfidenceIntervalV1, FeatureSnapshot, ModuleResult,
    VerifiedFormulationModelInputV2,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

pub const MODULE_ID: &str = "amphora-viscosity-score";
pub const HOST_FEATURE_KEY: &str = "verified_formulation_model.amphora-viscosity-score";
pub const OBSERVATION_SCHEMA: &str = "amphora.viscosity-observation.v1";
pub const OBSERVATION_BUNDLE_SCHEMA: &str = "amphora.viscosity-observation-bundle.v1";
pub const DATASET_SCHEMA: &str = "amphora.viscosity-dataset.v1";
pub const SPLIT_SCHEMA: &str = "amphora.viscosity-split.v1";
pub const BENCHMARK_LOCK_SCHEMA: &str = "amphora.viscosity-benchmark-lock.v1";
pub const MODEL_ARTIFACT_SCHEMA: &str = "amphora.viscosity-model-artifact.v1";
pub const PREDICTION_SCHEMA: &str = "amphora.viscosity-prediction.v1";
pub const INDEPENDENT_REVIEW_SCHEMA: &str = "amphora.viscosity-independent-review.v1";
pub const SCREEN_OBSERVATION_SCHEMA: &str = "amphora.rheology-screen-observation.v1";
pub const CHARACTERIZATION_SCHEMA: &str = "amphora.rheology-characterization.v1";
pub const BENCHMARK_RECEIPT_SCHEMA: &str = "amphora.viscosity-benchmark-receipt.v1";
pub const RESIDUAL_MODEL_L2: f64 = 1.0;
pub const RESIDUAL_MODEL_SEED: u64 = 20_260_717;
pub const GAS_CONSTANT_J_MOL_K: f64 = 8.314_462_618_153_24;

#[derive(Debug, Error, PartialEq)]
pub enum ViscosityError {
    #[error("unexpected schema or module identity")]
    Identity,
    #[error("required field is empty: {0}")]
    Empty(&'static str),
    #[error("invalid SHA-256: {0}")]
    Hash(&'static str),
    #[error("non-finite or out-of-range value: {0}")]
    Range(&'static str),
    #[error("rights are not eligible for derivative use")]
    Rights,
    #[error("dataset and split identities do not match")]
    Parent,
    #[error("split leaks a formulation across folds")]
    Leakage,
    #[error("observation is outside the artifact applicability domain")]
    OutOfDomain,
    #[error("host evidence binding is missing or invalid: {0}")]
    HostBinding(String),
    #[error("unsupported contract kind for this module")]
    UnsupportedKind,
    #[error("JSON contract error: {0}")]
    Json(String),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct LiquidComponentV1 {
    pub ingredient_id: String,
    pub lot_id: String,
    pub mass_fraction_0_1: f64,
    pub viscosity_pa_s_at_reference: f64,
    pub reference_temperature_c: f64,
    pub activation_energy_j_mol: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PigmentComponentV1 {
    pub ingredient_id: String,
    pub lot_id: String,
    pub volume_fraction_0_1: f64,
    pub morphology: Option<String>,
    pub oil_absorption_g_per_100g: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct RheologyAdditiveV1 {
    pub ingredient_id: String,
    pub lot_id: String,
    pub loading_mass_fraction_0_1: f64,
    pub activation_protocol: String,
}

/// Composition-only record available before rheology is measured. The strict
/// field list is the feature firewall for screening: yield stress, flow-fit
/// parameters, KU, sag, and measured viscosity cannot be deserialized here.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct RheologyScreenObservationV1 {
    pub schema: String,
    pub module_id: String,
    pub observation_id: String,
    pub candidate_id: String,
    pub formulation_id: String,
    pub formulation_family: String,
    pub preparation_id: String,
    pub ingredients: BTreeMap<String, String>,
    pub liquids: Vec<LiquidComponentV1>,
    pub pigments: Vec<PigmentComponentV1>,
    pub rheology_additives: Vec<RheologyAdditiveV1>,
    pub density_kg_m3: f64,
    pub solids_volume_fraction_0_1: f64,
    pub pvc_fraction_0_1: f64,
    pub cpvc_fraction_0_1: f64,
    pub pot_age_h: f64,
    pub temperature_c: f64,
    pub wet_film_thickness_mil: f64,
    pub application_geometry: String,
    pub process_protocol: String,
    pub rights_receipt_sha256: String,
    pub rights_eligible: bool,
}

impl RheologyScreenObservationV1 {
    pub fn validate(&self) -> Result<(), ViscosityError> {
        require_identity(&self.schema, SCREEN_OBSERVATION_SCHEMA, &self.module_id)?;
        for (field, value) in [
            ("observation_id", self.observation_id.as_str()),
            ("candidate_id", self.candidate_id.as_str()),
            ("formulation_id", self.formulation_id.as_str()),
            ("formulation_family", self.formulation_family.as_str()),
            ("preparation_id", self.preparation_id.as_str()),
            ("application_geometry", self.application_geometry.as_str()),
            ("process_protocol", self.process_protocol.as_str()),
        ] {
            require_text(field, value)?;
        }
        require_hash("rights_receipt_sha256", &self.rights_receipt_sha256)?;
        if !self.rights_eligible || self.ingredients.is_empty() || self.liquids.is_empty() {
            return Err(ViscosityError::Rights);
        }
        if self.ingredients.values().any(|lot| lot.trim().is_empty())
            || !finite_positive(self.density_kg_m3)
            || !finite_positive(self.wet_film_thickness_mil)
            || !finite_between(self.solids_volume_fraction_0_1, 0.0, 1.0)
            || !finite_between(self.pvc_fraction_0_1, 0.0, 1.0)
            || !finite_between(self.cpvc_fraction_0_1, 0.0, 1.0)
            || self.pvc_fraction_0_1 > self.cpvc_fraction_0_1
            || !finite_between(self.temperature_c, -20.0, 80.0)
            || !self.pot_age_h.is_finite()
            || self.pot_age_h < 0.0
        {
            return Err(ViscosityError::Range("screen conditions"));
        }
        let liquid_total = self.liquids.iter().try_fold(0.0, |sum, row| {
            require_text("liquid.ingredient_id", &row.ingredient_id)?;
            require_text("liquid.lot_id", &row.lot_id)?;
            if !finite_between(row.mass_fraction_0_1, 0.0, 1.0)
                || !finite_positive(row.viscosity_pa_s_at_reference)
                || !finite_between(row.reference_temperature_c, -50.0, 100.0)
                || !finite_positive(row.activation_energy_j_mol)
            {
                return Err(ViscosityError::Range("liquid properties"));
            }
            Ok(sum + row.mass_fraction_0_1)
        })?;
        if (liquid_total - 1.0).abs() > 1e-6 {
            return Err(ViscosityError::Range("liquid mass fractions"));
        }
        for pigment in &self.pigments {
            require_text("pigment.ingredient_id", &pigment.ingredient_id)?;
            require_text("pigment.lot_id", &pigment.lot_id)?;
            if !finite_between(pigment.volume_fraction_0_1, 0.0, 1.0)
                || pigment.morphology.as_deref().is_none_or(str::is_empty)
                    && pigment
                        .oil_absorption_g_per_100g
                        .is_none_or(|value| !finite_positive(value))
            {
                return Err(ViscosityError::Range("pigment properties"));
            }
        }
        for additive in &self.rheology_additives {
            require_text("additive.ingredient_id", &additive.ingredient_id)?;
            require_text("additive.lot_id", &additive.lot_id)?;
            require_text(
                "additive.activation_protocol",
                &additive.activation_protocol,
            )?;
            if !finite_between(additive.loading_mass_fraction_0_1, 0.0, 1.0) {
                return Err(ViscosityError::Range("additive loading"));
            }
        }
        Ok(())
    }
}

/// Post-measurement record for physics consistency and characterization only.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct RheologyCharacterizationV1 {
    pub schema: String,
    pub module_id: String,
    pub screen: RheologyScreenObservationV1,
    pub replicate_id: String,
    pub instrument_id: String,
    pub calibration_id: String,
    pub pre_shear_s_inv: f64,
    pub pre_shear_duration_s: f64,
    pub shear_rate_s_inv: f64,
    pub maximum_packing_fraction_0_1: f64,
    pub intrinsic_viscosity: f64,
    pub yield_stress_pa: f64,
    pub consistency_pa_s_n: f64,
    pub flow_index_n: f64,
    pub measured_apparent_viscosity_pa_s: f64,
    pub measured_ku: f64,
    pub measured_sag_index_mil: f64,
    pub sag_unsafe: bool,
    pub raw_file_hashes: BTreeMap<String, String>,
}

impl RheologyCharacterizationV1 {
    pub fn validate(&self) -> Result<(), ViscosityError> {
        require_identity(&self.schema, CHARACTERIZATION_SCHEMA, &self.module_id)?;
        self.screen.validate()?;
        for (field, value) in [
            ("replicate_id", self.replicate_id.as_str()),
            ("instrument_id", self.instrument_id.as_str()),
            ("calibration_id", self.calibration_id.as_str()),
        ] {
            require_text(field, value)?;
        }
        validate_hash_map(&self.raw_file_hashes)?;
        if [
            self.pre_shear_s_inv,
            self.pre_shear_duration_s,
            self.shear_rate_s_inv,
            self.maximum_packing_fraction_0_1,
            self.intrinsic_viscosity,
            self.consistency_pa_s_n,
            self.flow_index_n,
            self.measured_apparent_viscosity_pa_s,
            self.measured_ku,
            self.measured_sag_index_mil,
        ]
        .iter()
        .any(|value| !finite_positive(*value))
            || !self.yield_stress_pa.is_finite()
            || self.yield_stress_pa < 0.0
            || self.screen.pvc_fraction_0_1 >= self.maximum_packing_fraction_0_1
        {
            return Err(ViscosityError::Range("characterization"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct RheologyObservationV1 {
    pub schema: String,
    pub module_id: String,
    pub observation_id: String,
    pub candidate_id: String,
    pub formulation_id: String,
    pub formulation_family: String,
    pub preparation_id: String,
    pub replicate_id: String,
    pub ingredients: BTreeMap<String, String>,
    pub liquids: Vec<LiquidComponentV1>,
    pub pigments: Vec<PigmentComponentV1>,
    pub rheology_additives: Vec<RheologyAdditiveV1>,
    pub density_kg_m3: f64,
    pub solids_volume_fraction_0_1: f64,
    pub pvc_fraction_0_1: f64,
    pub maximum_packing_fraction_0_1: f64,
    pub intrinsic_viscosity: f64,
    pub yield_stress_pa: f64,
    pub consistency_pa_s_n: f64,
    pub flow_index_n: f64,
    pub pre_shear_s_inv: f64,
    pub pre_shear_duration_s: f64,
    pub pot_age_h: f64,
    pub temperature_c: f64,
    pub shear_rate_s_inv: f64,
    pub wet_film_thickness_mil: f64,
    pub application_angle_deg_from_horizontal: f64,
    pub instrument_id: String,
    pub calibration_id: String,
    pub ku_method: String,
    pub sag_method: String,
    pub measured_apparent_viscosity_pa_s: Option<f64>,
    pub measured_ku: Option<f64>,
    pub measured_sag_index_mil: Option<f64>,
    pub sag_unsafe: Option<bool>,
    pub raw_file_hashes: BTreeMap<String, String>,
    pub rights_receipt_sha256: String,
    pub rights_eligible: bool,
}

impl RheologyObservationV1 {
    pub fn validate_conditions(&self) -> Result<(), ViscosityError> {
        require_identity(&self.schema, OBSERVATION_SCHEMA, &self.module_id)?;
        for (field, value) in [
            ("observation_id", self.observation_id.as_str()),
            ("candidate_id", self.candidate_id.as_str()),
            ("formulation_id", self.formulation_id.as_str()),
            ("formulation_family", self.formulation_family.as_str()),
            ("preparation_id", self.preparation_id.as_str()),
            ("replicate_id", self.replicate_id.as_str()),
            ("instrument_id", self.instrument_id.as_str()),
            ("calibration_id", self.calibration_id.as_str()),
            ("ku_method", self.ku_method.as_str()),
            ("sag_method", self.sag_method.as_str()),
        ] {
            require_text(field, value)?;
        }
        if self.ku_method != "ASTM_D562" || self.sag_method != "ASTM_D4400" {
            return Err(ViscosityError::Range("measurement method"));
        }
        require_hash("rights_receipt_sha256", &self.rights_receipt_sha256)?;
        if !self.rights_eligible {
            return Err(ViscosityError::Rights);
        }
        validate_hash_map(&self.raw_file_hashes)?;
        if self.ingredients.is_empty()
            || self.ingredients.values().any(|lot| lot.trim().is_empty())
            || self.liquids.is_empty()
        {
            return Err(ViscosityError::Empty("exact ingredients/lots"));
        }
        let liquid_total = self.liquids.iter().try_fold(0.0, |sum, row| {
            require_text("liquid.ingredient_id", &row.ingredient_id)?;
            require_text("liquid.lot_id", &row.lot_id)?;
            if !finite_between(row.mass_fraction_0_1, 0.0, 1.0)
                || !finite_positive(row.viscosity_pa_s_at_reference)
                || !finite_between(row.reference_temperature_c, -50.0, 100.0)
                || !finite_positive(row.activation_energy_j_mol)
            {
                return Err(ViscosityError::Range("liquid properties"));
            }
            Ok(sum + row.mass_fraction_0_1)
        })?;
        if (liquid_total - 1.0).abs() > 1e-6 {
            return Err(ViscosityError::Range("liquid mass fractions"));
        }
        for row in &self.pigments {
            require_text("pigment.ingredient_id", &row.ingredient_id)?;
            require_text("pigment.lot_id", &row.lot_id)?;
            if !finite_between(row.volume_fraction_0_1, 0.0, 1.0)
                || row.morphology.as_deref().is_none_or(str::is_empty)
                    && row
                        .oil_absorption_g_per_100g
                        .is_none_or(|value| !finite_positive(value))
            {
                return Err(ViscosityError::Range("pigment morphology/oil absorption"));
            }
        }
        for row in &self.rheology_additives {
            require_text("rheology_additive.ingredient_id", &row.ingredient_id)?;
            require_text("rheology_additive.lot_id", &row.lot_id)?;
            require_text(
                "rheology_additive.activation_protocol",
                &row.activation_protocol,
            )?;
            if !finite_between(row.loading_mass_fraction_0_1, 0.0, 1.0) {
                return Err(ViscosityError::Range("rheology additive loading"));
            }
        }
        for (field, value) in [
            ("density_kg_m3", self.density_kg_m3),
            (
                "maximum_packing_fraction_0_1",
                self.maximum_packing_fraction_0_1,
            ),
            ("intrinsic_viscosity", self.intrinsic_viscosity),
            ("consistency_pa_s_n", self.consistency_pa_s_n),
            ("flow_index_n", self.flow_index_n),
            ("pre_shear_s_inv", self.pre_shear_s_inv),
            ("pre_shear_duration_s", self.pre_shear_duration_s),
            ("shear_rate_s_inv", self.shear_rate_s_inv),
            ("wet_film_thickness_mil", self.wet_film_thickness_mil),
        ] {
            if !finite_positive(value) {
                return Err(ViscosityError::Range(field));
            }
        }
        if !finite_between(self.solids_volume_fraction_0_1, 0.0, 1.0)
            || !finite_between(self.pvc_fraction_0_1, 0.0, 1.0)
            || self.pvc_fraction_0_1 >= self.maximum_packing_fraction_0_1
            || !self.yield_stress_pa.is_finite()
            || self.yield_stress_pa < 0.0
            || !self.pot_age_h.is_finite()
            || self.pot_age_h < 0.0
            || !finite_between(self.temperature_c, -20.0, 80.0)
            || !finite_between(self.application_angle_deg_from_horizontal, 0.0, 90.0)
        {
            return Err(ViscosityError::Range("rheology conditions"));
        }
        Ok(())
    }

    pub fn validate_measured(&self) -> Result<(), ViscosityError> {
        self.validate_conditions()?;
        for (field, value) in [
            (
                "measured_apparent_viscosity_pa_s",
                self.measured_apparent_viscosity_pa_s,
            ),
            ("measured_ku", self.measured_ku),
            ("measured_sag_index_mil", self.measured_sag_index_mil),
        ] {
            if value.is_none_or(|value| !finite_positive(value)) {
                return Err(ViscosityError::Range(field));
            }
        }
        if self.sag_unsafe.is_none() {
            return Err(ViscosityError::Empty("sag_unsafe"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("observation serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ObservationBundleV1 {
    pub schema: String,
    pub module_id: String,
    pub candidate_id: String,
    pub observations: Vec<RheologyObservationV1>,
}

impl ObservationBundleV1 {
    pub fn validate(&self) -> Result<(), ViscosityError> {
        require_identity(&self.schema, OBSERVATION_BUNDLE_SCHEMA, &self.module_id)?;
        require_text("candidate_id", &self.candidate_id)?;
        if self.observations.len() != 1 {
            return Err(ViscosityError::Range("one candidate observation required"));
        }
        self.observations[0].validate_conditions()?;
        if self.observations[0].candidate_id != self.candidate_id {
            return Err(ViscosityError::Parent);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ViscosityDatasetV1 {
    pub schema: String,
    pub module_id: String,
    pub dataset_id: String,
    pub observations: Vec<RheologyObservationV1>,
}

impl ViscosityDatasetV1 {
    pub fn validate(&self) -> Result<(), ViscosityError> {
        require_identity(&self.schema, DATASET_SCHEMA, &self.module_id)?;
        require_text("dataset_id", &self.dataset_id)?;
        if self.observations.is_empty() {
            return Err(ViscosityError::Empty("observations"));
        }
        let mut ids = BTreeSet::new();
        for observation in &self.observations {
            observation.validate_measured()?;
            if !ids.insert(&observation.observation_id) {
                return Err(ViscosityError::Parent);
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
    pub formulation_id: String,
    pub family: String,
    pub temperature_group: String,
    pub split: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ViscositySplitV1 {
    pub schema: String,
    pub module_id: String,
    pub split_id: String,
    pub dataset_sha256: String,
    pub assignments: Vec<SplitAssignmentV1>,
}

impl ViscositySplitV1 {
    pub fn validate(&self, dataset: Option<&ViscosityDatasetV1>) -> Result<(), ViscosityError> {
        require_identity(&self.schema, SPLIT_SCHEMA, &self.module_id)?;
        require_text("split_id", &self.split_id)?;
        require_hash("dataset_sha256", &self.dataset_sha256)?;
        let mut observations = BTreeSet::new();
        let mut formulation_folds: BTreeMap<&str, &str> = BTreeMap::new();
        for row in &self.assignments {
            for (field, value) in [
                ("observation_id", row.observation_id.as_str()),
                ("formulation_id", row.formulation_id.as_str()),
                ("family", row.family.as_str()),
                ("temperature_group", row.temperature_group.as_str()),
                ("split", row.split.as_str()),
            ] {
                require_text(field, value)?;
            }
            if !observations.insert(row.observation_id.as_str()) {
                return Err(ViscosityError::Parent);
            }
            if formulation_folds
                .insert(&row.formulation_id, &row.split)
                .is_some_and(|existing| existing != row.split)
            {
                return Err(ViscosityError::Leakage);
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
                return Err(ViscosityError::Parent);
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
pub struct ViscosityBenchmarkLockV1 {
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

impl ViscosityBenchmarkLockV1 {
    pub fn validate(&self) -> Result<(), ViscosityError> {
        require_identity(&self.schema, BENCHMARK_LOCK_SCHEMA, &self.module_id)?;
        require_text("benchmark_id", &self.benchmark_id)?;
        require_hash("dataset_sha256", &self.dataset_sha256)?;
        require_hash("split_sha256", &self.split_sha256)?;
        let expected_baselines = [
            "family-temperature-median",
            "composition-ridge",
            "nearest-family",
            "ideal-liquid-crowding",
            "no-yield",
            "majority-class",
        ];
        if !self.immutable
            || expected_baselines
                .iter()
                .any(|expected| !self.baselines.iter().any(|value| value == expected))
            || self.hostile_nulls.is_empty()
            || self.thresholds.values().any(|value| !value.is_finite())
        {
            return Err(ViscosityError::Range("benchmark lock"));
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
    pub observed_apparent_viscosity_pa_s: f64,
    pub predicted_apparent_viscosity_pa_s: f64,
    pub composition_baseline_apparent_viscosity_pa_s: f64,
    pub apparent_viscosity_interval_90: [f64; 2],
    pub observed_ku: f64,
    pub predicted_ku: f64,
    pub composition_baseline_ku: f64,
    pub ku_interval_90: [f64; 2],
    pub observed_sag_index_mil: f64,
    pub predicted_sag_index_mil: f64,
    pub composition_baseline_sag_index_mil: f64,
    pub sag_interval_90: [f64; 2],
    pub observed_sag_unsafe: bool,
    pub predicted_sag_unsafe: bool,
    pub composition_baseline_sag_unsafe: bool,
    pub unsafe_boundary_case: bool,
}

impl OutOfFoldPredictionV1 {
    fn validate(&self) -> Result<(), ViscosityError> {
        for (field, value) in [
            ("observation_id", self.observation_id.as_str()),
            ("cluster_id", self.cluster_id.as_str()),
            ("site_id", self.site_id.as_str()),
        ] {
            require_text(field, value)?;
        }
        if [
            self.observed_apparent_viscosity_pa_s,
            self.predicted_apparent_viscosity_pa_s,
            self.composition_baseline_apparent_viscosity_pa_s,
            self.observed_ku,
            self.predicted_ku,
            self.composition_baseline_ku,
            self.observed_sag_index_mil,
            self.predicted_sag_index_mil,
            self.composition_baseline_sag_index_mil,
        ]
        .iter()
        .any(|value| !finite_positive(*value))
            || [
                self.apparent_viscosity_interval_90,
                self.ku_interval_90,
                self.sag_interval_90,
            ]
            .iter()
            .any(|interval| {
                interval.iter().any(|value| !value.is_finite()) || interval[0] > interval[1]
            })
        {
            return Err(ViscosityError::Range("out-of-fold prediction"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct BenchmarkMetricsV1 {
    pub apparent_viscosity_log_mae: f64,
    pub ku_mae: f64,
    pub sag_index_mae_mil: f64,
    pub sag_balanced_accuracy: f64,
    pub unsafe_boundary_sensitivity: f64,
    pub interval_90_coverage: f64,
    pub composition_baseline_ku_mae: f64,
    pub theory_ku_mae_improvement: f64,
    pub theory_ku_improvement_lower_95: f64,
    pub composition_baseline_sag_balanced_accuracy: f64,
    pub theory_sag_balanced_accuracy_improvement: f64,
    pub theory_sag_improvement_lower_95: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct BenchmarkGateStatusV1 {
    pub log_viscosity_mae_at_most_ln_1_25: bool,
    pub ku_mae_at_most_5: bool,
    pub sag_mae_at_most_2_mil: bool,
    pub sag_balanced_accuracy_at_least_0_80: bool,
    pub unsafe_boundary_sensitivity_at_least_0_90: bool,
    pub interval_coverage_0_85_to_0_95: bool,
    pub ku_improvement_at_least_1: bool,
    pub sag_improvement_at_least_0_05: bool,
    pub paired_improvement_lower_bounds_positive: bool,
    pub both_verifier_sites_non_reversing: bool,
}

impl BenchmarkGateStatusV1 {
    pub fn passed(&self) -> bool {
        self.log_viscosity_mae_at_most_ln_1_25
            && self.ku_mae_at_most_5
            && self.sag_mae_at_most_2_mil
            && self.sag_balanced_accuracy_at_least_0_80
            && self.unsafe_boundary_sensitivity_at_least_0_90
            && self.interval_coverage_0_85_to_0_95
            && self.ku_improvement_at_least_1
            && self.sag_improvement_at_least_0_05
            && self.paired_improvement_lower_bounds_positive
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
    pub fn validate(&self) -> Result<(), ViscosityError> {
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
        let metrics = &self.metrics;
        if [
            metrics.apparent_viscosity_log_mae,
            metrics.ku_mae,
            metrics.sag_index_mae_mil,
            metrics.sag_balanced_accuracy,
            metrics.unsafe_boundary_sensitivity,
            metrics.interval_90_coverage,
            metrics.composition_baseline_ku_mae,
            metrics.theory_ku_mae_improvement,
            metrics.theory_ku_improvement_lower_95,
            metrics.composition_baseline_sag_balanced_accuracy,
            metrics.theory_sag_balanced_accuracy_improvement,
            metrics.theory_sag_improvement_lower_95,
        ]
        .iter()
        .any(|value| !value.is_finite())
            || self.estimator != "STANDARDIZED_RIDGE_LOGISTIC"
            || self.l2_penalty != RESIDUAL_MODEL_L2
            || self.seed != RESIDUAL_MODEL_SEED
            || self.passed != self.gate_status.passed()
        {
            return Err(ViscosityError::Range("benchmark receipt"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("receipt serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ApplicabilityDomainV1 {
    pub ingredient_lots: BTreeMap<String, Vec<String>>,
    pub temperature_c: [f64; 2],
    pub shear_rate_s_inv: [f64; 2],
    pub pot_age_h: [f64; 2],
    pub wet_film_thickness_mil: [f64; 2],
    pub methods: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ViscosityModelArtifactV1 {
    pub schema: String,
    pub module_id: String,
    pub model_id: String,
    pub dataset_sha256: String,
    pub split_sha256: String,
    pub benchmark_lock_sha256: String,
    pub theory: Vec<String>,
    pub log_viscosity_offset: f64,
    pub ku_intercept: f64,
    pub ku_log_viscosity_slope: f64,
    pub sag_intercept_mil: f64,
    pub sag_margin_slope_mil_per_pa: f64,
    pub residual_scales: BTreeMap<String, f64>,
    pub applicability_domain: ApplicabilityDomainV1,
    pub training_observation_hashes: BTreeMap<String, String>,
    pub rights_receipt_hashes: Vec<String>,
    pub promotion_dataset_complete: bool,
    pub authority: String,
}

impl ViscosityModelArtifactV1 {
    pub fn validate(&self) -> Result<(), ViscosityError> {
        require_identity(&self.schema, MODEL_ARTIFACT_SCHEMA, &self.module_id)?;
        require_text("model_id", &self.model_id)?;
        for (field, hash) in [
            ("dataset_sha256", self.dataset_sha256.as_str()),
            ("split_sha256", self.split_sha256.as_str()),
            ("benchmark_lock_sha256", self.benchmark_lock_sha256.as_str()),
        ] {
            require_hash(field, hash)?;
        }
        if self.theory
            != [
                "GRUNBERG_NISSAN_ARRHENIUS",
                "KRIEGER_DOUGHERTY",
                "HERSCHEL_BULKLEY",
                "GRAVITY_YIELD_SAG",
                "SEPARATE_ASTMD562_HEAD",
                "SEPARATE_ASTMD4400_HEAD",
            ]
            || [
                self.log_viscosity_offset,
                self.ku_intercept,
                self.ku_log_viscosity_slope,
                self.sag_intercept_mil,
                self.sag_margin_slope_mil_per_pa,
            ]
            .iter()
            .any(|value| !value.is_finite())
            || self
                .residual_scales
                .values()
                .any(|value| !value.is_finite() || *value < 0.0)
            || self.authority != "SHADOW"
        {
            return Err(ViscosityError::Range("model artifact"));
        }
        validate_ranges(&self.applicability_domain)?;
        for hash in self
            .training_observation_hashes
            .values()
            .chain(self.rights_receipt_hashes.iter())
        {
            require_hash("artifact parent hash", hash)?;
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ViscosityPredictionV1 {
    pub schema: String,
    pub module_id: String,
    pub candidate_id: String,
    pub authority: String,
    pub exact_ku_prediction: Option<f64>,
    pub computed_apparent_viscosity_pa_s: Option<f64>,
    pub estimated_ku: Option<f64>,
    pub estimated_sag_index_mil: Option<f64>,
    pub apparent_viscosity_interval: Option<ConfidenceIntervalV1>,
    pub ku_interval: Option<ConfidenceIntervalV1>,
    pub sag_interval: Option<ConfidenceIntervalV1>,
    pub sag_threshold_pass: Option<bool>,
    pub in_applicability_domain: bool,
    pub abstention_reasons: Vec<String>,
}

impl ViscosityPredictionV1 {
    fn abstain(candidate_id: &str, reason: impl Into<String>) -> Self {
        Self {
            schema: PREDICTION_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            candidate_id: candidate_id.into(),
            authority: "SHADOW".into(),
            exact_ku_prediction: None,
            computed_apparent_viscosity_pa_s: None,
            estimated_ku: None,
            estimated_sag_index_mil: None,
            apparent_viscosity_interval: None,
            ku_interval: None,
            sag_interval: None,
            sag_threshold_pass: None,
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
    pub methods_accepted: bool,
    pub limitations_accepted: bool,
}

impl IndependentReviewV1 {
    pub fn validate(&self) -> Result<(), ViscosityError> {
        require_identity(&self.schema, INDEPENDENT_REVIEW_SCHEMA, &self.module_id)?;
        require_text("review_id", &self.review_id)?;
        require_hash("model_artifact_sha256", &self.model_artifact_sha256)?;
        require_hash("benchmark_receipt_sha256", &self.benchmark_receipt_sha256)?;
        if !self.reviewer_independent || !self.methods_accepted || !self.limitations_accepted {
            return Err(ViscosityError::Range("independent review"));
        }
        Ok(())
    }
}

pub fn evaluate_locked_benchmark(
    lock: &ViscosityBenchmarkLockV1,
    dataset: &ViscosityDatasetV1,
    split: &ViscositySplitV1,
    artifact: &ViscosityModelArtifactV1,
    raw_file_hashes: &BTreeMap<String, String>,
    predictions: &[OutOfFoldPredictionV1],
) -> Result<BenchmarkReceiptV1, ViscosityError> {
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
        return Err(ViscosityError::Parent);
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
            return Err(ViscosityError::Leakage);
        }
    }
    if observed != expected {
        return Err(ViscosityError::Parent);
    }

    let count = predictions.len() as f64;
    let log_mae = predictions
        .iter()
        .map(|row| {
            (row.predicted_apparent_viscosity_pa_s.ln() - row.observed_apparent_viscosity_pa_s.ln())
                .abs()
        })
        .sum::<f64>()
        / count;
    let ku_mae = predictions
        .iter()
        .map(|row| (row.predicted_ku - row.observed_ku).abs())
        .sum::<f64>()
        / count;
    let baseline_ku_mae = predictions
        .iter()
        .map(|row| (row.composition_baseline_ku - row.observed_ku).abs())
        .sum::<f64>()
        / count;
    let sag_mae = predictions
        .iter()
        .map(|row| (row.predicted_sag_index_mil - row.observed_sag_index_mil).abs())
        .sum::<f64>()
        / count;
    let sag_accuracy = balanced_accuracy(
        predictions
            .iter()
            .map(|row| (row.observed_sag_unsafe, row.predicted_sag_unsafe)),
    )?;
    let baseline_sag_accuracy = balanced_accuracy(
        predictions
            .iter()
            .map(|row| (row.observed_sag_unsafe, row.composition_baseline_sag_unsafe)),
    )?;
    let boundary: Vec<_> = predictions
        .iter()
        .filter(|row| row.unsafe_boundary_case && row.observed_sag_unsafe)
        .collect();
    if boundary.is_empty() {
        return Err(ViscosityError::Empty("unsafe boundary cases"));
    }
    let unsafe_sensitivity = boundary
        .iter()
        .filter(|row| row.predicted_sag_unsafe)
        .count() as f64
        / boundary.len() as f64;
    let covered = predictions
        .iter()
        .map(|row| {
            usize::from(interval_contains(
                row.apparent_viscosity_interval_90,
                row.observed_apparent_viscosity_pa_s,
            )) + usize::from(interval_contains(row.ku_interval_90, row.observed_ku))
                + usize::from(interval_contains(
                    row.sag_interval_90,
                    row.observed_sag_index_mil,
                ))
        })
        .sum::<usize>();
    let coverage = covered as f64 / (3 * predictions.len()) as f64;
    let ku_improvements: Vec<_> = predictions
        .iter()
        .map(|row| {
            (
                row.cluster_id.as_str(),
                (row.composition_baseline_ku - row.observed_ku).abs()
                    - (row.predicted_ku - row.observed_ku).abs(),
            )
        })
        .collect();
    let sag_improvements: Vec<_> = predictions
        .iter()
        .map(|row| {
            (
                row.cluster_id.as_str(),
                if row.predicted_sag_unsafe == row.observed_sag_unsafe {
                    1.0
                } else {
                    0.0
                } - if row.composition_baseline_sag_unsafe == row.observed_sag_unsafe {
                    1.0
                } else {
                    0.0
                },
            )
        })
        .collect();
    let ku_improvement = baseline_ku_mae - ku_mae;
    let sag_improvement = sag_accuracy - baseline_sag_accuracy;
    let ku_lower = paired_cluster_bootstrap_lower(&ku_improvements)?;
    let sag_lower = paired_cluster_bootstrap_lower(&sag_improvements)?;

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
                .collect();
            let ku = rows
                .iter()
                .map(|row| {
                    (row.composition_baseline_ku - row.observed_ku).abs()
                        - (row.predicted_ku - row.observed_ku).abs()
                })
                .sum::<f64>()
                / rows.len() as f64;
            let sag = rows
                .iter()
                .map(|row| {
                    (if row.predicted_sag_unsafe == row.observed_sag_unsafe {
                        1.0
                    } else {
                        0.0
                    }) - if row.composition_baseline_sag_unsafe == row.observed_sag_unsafe {
                        1.0
                    } else {
                        0.0
                    }
                })
                .sum::<f64>()
                / rows.len() as f64;
            ku >= 0.0 && sag >= 0.0
        });
    let metrics = BenchmarkMetricsV1 {
        apparent_viscosity_log_mae: log_mae,
        ku_mae,
        sag_index_mae_mil: sag_mae,
        sag_balanced_accuracy: sag_accuracy,
        unsafe_boundary_sensitivity: unsafe_sensitivity,
        interval_90_coverage: coverage,
        composition_baseline_ku_mae: baseline_ku_mae,
        theory_ku_mae_improvement: ku_improvement,
        theory_ku_improvement_lower_95: ku_lower,
        composition_baseline_sag_balanced_accuracy: baseline_sag_accuracy,
        theory_sag_balanced_accuracy_improvement: sag_improvement,
        theory_sag_improvement_lower_95: sag_lower,
    };
    let gate_status = BenchmarkGateStatusV1 {
        log_viscosity_mae_at_most_ln_1_25: log_mae <= 1.25_f64.ln(),
        ku_mae_at_most_5: ku_mae <= 5.0,
        sag_mae_at_most_2_mil: sag_mae <= 2.0,
        sag_balanced_accuracy_at_least_0_80: sag_accuracy >= 0.80,
        unsafe_boundary_sensitivity_at_least_0_90: unsafe_sensitivity >= 0.90,
        interval_coverage_0_85_to_0_95: (0.85..=0.95).contains(&coverage),
        ku_improvement_at_least_1: ku_improvement >= 1.0,
        sag_improvement_at_least_0_05: sag_improvement >= 0.05,
        paired_improvement_lower_bounds_positive: ku_lower > 0.0 && sag_lower > 0.0,
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
        .map_err(|error| ViscosityError::Json(error.to_string()))?;
    let seed = json!({
        "model": stable_hash(&serde_json::to_value(artifact).expect("artifact serializes")),
        "predictions": prediction_hashes,
    });
    let mut receipt = BenchmarkReceiptV1 {
        schema: BENCHMARK_RECEIPT_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        receipt_id: format!("viscosity-benchmark-{}", &stable_hash(&seed)[..16]),
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

pub fn arrhenius_viscosity(
    viscosity_pa_s_at_reference: f64,
    reference_temperature_c: f64,
    temperature_c: f64,
    activation_energy_j_mol: f64,
) -> Result<f64, ViscosityError> {
    if !finite_positive(viscosity_pa_s_at_reference)
        || !finite_positive(activation_energy_j_mol)
        || !finite_between(reference_temperature_c, -273.14, 500.0)
        || !finite_between(temperature_c, -273.14, 500.0)
    {
        return Err(ViscosityError::Range("Arrhenius viscosity"));
    }
    let reference_k = reference_temperature_c + 273.15;
    let temperature_k = temperature_c + 273.15;
    let value = viscosity_pa_s_at_reference
        * (activation_energy_j_mol / GAS_CONSTANT_J_MOL_K
            * (1.0 / temperature_k - 1.0 / reference_k))
            .exp();
    finite_positive(value)
        .then_some(value)
        .ok_or(ViscosityError::Range("Arrhenius viscosity"))
}

pub fn grunberg_nissan_mix(
    fractions: &[f64],
    viscosities_pa_s: &[f64],
    interactions: &[Vec<f64>],
) -> Result<f64, ViscosityError> {
    let n = fractions.len();
    if n == 0
        || viscosities_pa_s.len() != n
        || interactions.len() != n
        || interactions.iter().any(|row| row.len() != n)
        || fractions
            .iter()
            .any(|value| !finite_between(*value, 0.0, 1.0))
        || viscosities_pa_s
            .iter()
            .any(|value| !finite_positive(*value))
        || interactions
            .iter()
            .flatten()
            .any(|value| !value.is_finite())
        || (fractions.iter().sum::<f64>() - 1.0).abs() > 1e-6
    {
        return Err(ViscosityError::Range("Grunberg-Nissan inputs"));
    }
    let mut log_viscosity = fractions
        .iter()
        .zip(viscosities_pa_s)
        .map(|(fraction, viscosity)| fraction * viscosity.ln())
        .sum::<f64>();
    for i in 0..n {
        for j in (i + 1)..n {
            log_viscosity += fractions[i] * fractions[j] * interactions[i][j];
        }
    }
    Ok(log_viscosity.exp())
}

pub fn krieger_dougherty(
    liquid_viscosity_pa_s: f64,
    pigment_volume_fraction: f64,
    maximum_packing_fraction: f64,
    intrinsic_viscosity: f64,
) -> Result<f64, ViscosityError> {
    if !finite_positive(liquid_viscosity_pa_s)
        || !finite_between(pigment_volume_fraction, 0.0, 1.0)
        || !finite_between(maximum_packing_fraction, 0.0, 1.0)
        || pigment_volume_fraction >= maximum_packing_fraction
        || !finite_positive(intrinsic_viscosity)
    {
        return Err(ViscosityError::Range("Krieger-Dougherty inputs"));
    }
    Ok(liquid_viscosity_pa_s
        * (1.0 - pigment_volume_fraction / maximum_packing_fraction)
            .powf(-intrinsic_viscosity * maximum_packing_fraction))
}

pub fn herschel_bulkley_apparent_viscosity(
    yield_stress_pa: f64,
    consistency_pa_s_n: f64,
    flow_index_n: f64,
    shear_rate_s_inv: f64,
) -> Result<f64, ViscosityError> {
    if !yield_stress_pa.is_finite()
        || yield_stress_pa < 0.0
        || !finite_positive(consistency_pa_s_n)
        || !finite_positive(flow_index_n)
        || !finite_positive(shear_rate_s_inv)
    {
        return Err(ViscosityError::Range("Herschel-Bulkley inputs"));
    }
    Ok(yield_stress_pa / shear_rate_s_inv
        + consistency_pa_s_n * shear_rate_s_inv.powf(flow_index_n - 1.0))
}

pub fn sag_stress_pa(
    density_kg_m3: f64,
    wet_film_thickness_mil: f64,
    application_angle_deg_from_horizontal: f64,
) -> Result<f64, ViscosityError> {
    if !finite_positive(density_kg_m3)
        || !finite_positive(wet_film_thickness_mil)
        || !finite_between(application_angle_deg_from_horizontal, 0.0, 90.0)
    {
        return Err(ViscosityError::Range("sag threshold inputs"));
    }
    let thickness_m = wet_film_thickness_mil * 25.4e-6;
    Ok(density_kg_m3
        * 9.806_65
        * thickness_m
        * application_angle_deg_from_horizontal.to_radians().sin())
}

pub fn theory_apparent_viscosity(
    observation: &RheologyObservationV1,
) -> Result<f64, ViscosityError> {
    observation.validate_conditions()?;
    let fractions: Vec<_> = observation
        .liquids
        .iter()
        .map(|row| row.mass_fraction_0_1)
        .collect();
    let viscosities = observation
        .liquids
        .iter()
        .map(|row| {
            arrhenius_viscosity(
                row.viscosity_pa_s_at_reference,
                row.reference_temperature_c,
                observation.temperature_c,
                row.activation_energy_j_mol,
            )
        })
        .collect::<Result<Vec<_>, _>>()?;
    let interactions = vec![vec![0.0; fractions.len()]; fractions.len()];
    let liquid = grunberg_nissan_mix(&fractions, &viscosities, &interactions)?;
    let pigment_fraction = observation
        .pigments
        .iter()
        .map(|row| row.volume_fraction_0_1)
        .sum();
    let crowded = krieger_dougherty(
        liquid,
        pigment_fraction,
        observation.maximum_packing_fraction_0_1,
        observation.intrinsic_viscosity,
    )?;
    let yield_flow = herschel_bulkley_apparent_viscosity(
        observation.yield_stress_pa,
        observation.consistency_pa_s_n,
        observation.flow_index_n,
        observation.shear_rate_s_inv,
    )?;
    Ok(crowded + yield_flow)
}

pub fn fit_model(
    dataset: &ViscosityDatasetV1,
    split: &ViscositySplitV1,
    lock: &ViscosityBenchmarkLockV1,
) -> Result<ViscosityModelArtifactV1, ViscosityError> {
    dataset.validate()?;
    split.validate(Some(dataset))?;
    lock.validate()?;
    if lock.dataset_sha256 != dataset.identity_hash() || lock.split_sha256 != split.identity_hash()
    {
        return Err(ViscosityError::Parent);
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
        return Err(ViscosityError::Empty("FIT observations"));
    }
    let theory: Vec<_> = training
        .iter()
        .map(|row| theory_apparent_viscosity(row))
        .collect::<Result<_, _>>()?;
    let log_offsets: Vec<_> = training
        .iter()
        .zip(&theory)
        .map(|(row, predicted)| {
            row.measured_apparent_viscosity_pa_s
                .expect("measured validated")
                .ln()
                - predicted.ln()
        })
        .collect();
    let log_viscosity_offset = median(&log_offsets);
    let corrected_logs: Vec<_> = theory
        .iter()
        .map(|value| value.ln() + log_viscosity_offset)
        .collect();
    let ku: Vec<_> = training
        .iter()
        .map(|row| row.measured_ku.expect("measured validated"))
        .collect();
    let (ku_intercept, ku_log_viscosity_slope) = linear_fit(&corrected_logs, &ku);
    let margins: Vec<_> = training
        .iter()
        .map(|row| {
            Ok(row.yield_stress_pa
                - sag_stress_pa(
                    row.density_kg_m3,
                    row.wet_film_thickness_mil,
                    row.application_angle_deg_from_horizontal,
                )?)
        })
        .collect::<Result<_, ViscosityError>>()?;
    let sag: Vec<_> = training
        .iter()
        .map(|row| row.measured_sag_index_mil.expect("measured validated"))
        .collect();
    let (sag_intercept_mil, sag_margin_slope_mil_per_pa) = linear_fit(&margins, &sag);
    let viscosity_residuals: Vec<_> = training
        .iter()
        .zip(&theory)
        .map(|(row, predicted)| {
            (row.measured_apparent_viscosity_pa_s
                .expect("measured validated")
                .ln()
                - (predicted.ln() + log_viscosity_offset))
                .abs()
        })
        .collect();
    let ku_residuals: Vec<_> = corrected_logs
        .iter()
        .zip(&ku)
        .map(|(x, y)| (y - (ku_intercept + ku_log_viscosity_slope * x)).abs())
        .collect();
    let sag_residuals: Vec<_> = margins
        .iter()
        .zip(&sag)
        .map(|(x, y)| (y - (sag_intercept_mil + sag_margin_slope_mil_per_pa * x)).abs())
        .collect();
    let formulation_count = training
        .iter()
        .map(|row| row.formulation_id.as_str())
        .collect::<BTreeSet<_>>()
        .len();
    let family_count = training
        .iter()
        .map(|row| row.formulation_family.as_str())
        .collect::<BTreeSet<_>>()
        .len();
    let temperatures: BTreeSet<_> = training
        .iter()
        .map(|row| (row.temperature_c * 10.0).round() as i64)
        .collect();
    let promotion_dataset_complete = formulation_count >= 30
        && family_count >= 3
        && [183_i64, 228, 350]
            .iter()
            .all(|temperature| temperatures.contains(temperature));
    let artifact_seed = json!({
        "dataset": dataset.identity_hash(),
        "split": split.identity_hash(),
        "lock": lock.identity_hash(),
        "offset": log_viscosity_offset,
    });
    let artifact = ViscosityModelArtifactV1 {
        schema: MODEL_ARTIFACT_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        model_id: format!("viscosity-rheology-{}", &stable_hash(&artifact_seed)[..16]),
        dataset_sha256: dataset.identity_hash(),
        split_sha256: split.identity_hash(),
        benchmark_lock_sha256: lock.identity_hash(),
        theory: vec![
            "GRUNBERG_NISSAN_ARRHENIUS".into(),
            "KRIEGER_DOUGHERTY".into(),
            "HERSCHEL_BULKLEY".into(),
            "GRAVITY_YIELD_SAG".into(),
            "SEPARATE_ASTMD562_HEAD".into(),
            "SEPARATE_ASTMD4400_HEAD".into(),
        ],
        log_viscosity_offset,
        ku_intercept,
        ku_log_viscosity_slope,
        sag_intercept_mil,
        sag_margin_slope_mil_per_pa,
        residual_scales: BTreeMap::from([
            ("log_viscosity".into(), quantile90(&viscosity_residuals)),
            ("ku".into(), quantile90(&ku_residuals)),
            ("sag_mil".into(), quantile90(&sag_residuals)),
        ]),
        applicability_domain: build_domain(&training),
        training_observation_hashes: training
            .iter()
            .map(|row| (row.observation_id.clone(), row.identity_hash()))
            .collect(),
        rights_receipt_hashes: training
            .iter()
            .map(|row| row.rights_receipt_sha256.clone())
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect(),
        promotion_dataset_complete,
        authority: "SHADOW".into(),
    };
    artifact.validate()?;
    Ok(artifact)
}

pub fn predict(
    artifact: &ViscosityModelArtifactV1,
    observation: &RheologyObservationV1,
) -> Result<ViscosityPredictionV1, ViscosityError> {
    artifact.validate()?;
    observation.validate_conditions()?;
    if !in_domain(observation, &artifact.applicability_domain) {
        return Ok(ViscosityPredictionV1::abstain(
            &observation.candidate_id,
            "conditions, methods, ingredients, or lots are outside the locked domain",
        ));
    }
    let apparent = theory_apparent_viscosity(observation)? * artifact.log_viscosity_offset.exp();
    let estimated_ku = artifact.ku_intercept + artifact.ku_log_viscosity_slope * apparent.ln();
    let sag_stress = sag_stress_pa(
        observation.density_kg_m3,
        observation.wet_film_thickness_mil,
        observation.application_angle_deg_from_horizontal,
    )?;
    let margin = observation.yield_stress_pa - sag_stress;
    let estimated_sag = artifact.sag_intercept_mil + artifact.sag_margin_slope_mil_per_pa * margin;
    if [apparent, estimated_ku, estimated_sag]
        .iter()
        .any(|value| !value.is_finite())
    {
        return Ok(ViscosityPredictionV1::abstain(
            &observation.candidate_id,
            "non-finite model result",
        ));
    }
    let log_width = artifact.residual_scales["log_viscosity"];
    let ku_width = artifact.residual_scales["ku"];
    let sag_width = artifact.residual_scales["sag_mil"];
    Ok(ViscosityPredictionV1 {
        schema: PREDICTION_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        candidate_id: observation.candidate_id.clone(),
        authority: "SHADOW".into(),
        exact_ku_prediction: None,
        computed_apparent_viscosity_pa_s: Some(apparent),
        estimated_ku: Some(estimated_ku),
        estimated_sag_index_mil: Some(estimated_sag),
        apparent_viscosity_interval: Some(interval(
            apparent * (-log_width).exp(),
            apparent * log_width.exp(),
            "LOCKED_RESIDUAL_90",
        )),
        ku_interval: Some(interval(
            estimated_ku - ku_width,
            estimated_ku + ku_width,
            "LOCKED_RESIDUAL_90",
        )),
        sag_interval: Some(interval(
            estimated_sag - sag_width,
            estimated_sag + sag_width,
            "LOCKED_RESIDUAL_90",
        )),
        sag_threshold_pass: Some(observation.yield_stress_pa >= sag_stress),
        in_applicability_domain: true,
        abstention_reasons: Vec::new(),
    })
}

pub fn evaluate(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> ModuleResult {
    let abstain = |reason: String| {
        let prediction = ViscosityPredictionV1::abstain(candidate.candidate_id(), reason.clone());
        result_from_prediction(candidate, &prediction, Some(reason))
    };
    let Some(value) = features.values.get(HOST_FEATURE_KEY) else {
        return abstain(format!(
            "missing host FeatureSnapshot key {HOST_FEATURE_KEY}"
        ));
    };
    let binding: VerifiedFormulationModelInputV2 = match serde_json::from_value(value.clone()) {
        Ok(binding) => binding,
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
    let artifact: ViscosityModelArtifactV1 = match serde_json::from_value(binding.model_artifact) {
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
    match predict(&artifact, &bundle.observations[0]) {
        Ok(prediction) => result_from_prediction(candidate, &prediction, None),
        Err(error) => abstain(error.to_string()),
    }
}

fn result_from_prediction(
    candidate: &CandidateEnvelope,
    prediction: &ViscosityPredictionV1,
    reason: Option<String>,
) -> ModuleResult {
    let available = prediction.computed_apparent_viscosity_pa_s.is_some();
    let dft = candidate
        .value()
        .pointer("/formulation/application/dft_mil")
        .and_then(Value::as_f64);
    let temperature = candidate
        .value()
        .pointer("/formulation/application/temperature_C")
        .and_then(Value::as_f64);
    let application_method = candidate
        .value()
        .pointer("/formulation/process/application_method")
        .and_then(Value::as_str);
    let pot_age = candidate
        .value()
        .pointer("/formulation/process/pot_age_h")
        .and_then(Value::as_f64);
    let mut missing_inputs: Vec<String> = reason.into_iter().collect();
    if !available {
        for (field, absent) in [
            ("formulation.application.dft_mil", dft.is_none()),
            (
                "formulation.application.temperature_C",
                temperature.is_none(),
            ),
            (
                "formulation.process.application_method",
                application_method.is_none(),
            ),
            ("formulation.process.pot_age_h", pot_age.is_none()),
        ] {
            if absent {
                missing_inputs.push(field.into());
            }
        }
    }
    ModuleResult {
        status: if available {
            "NO_AUTHORITY".into()
        } else {
            "INSUFFICIENT_INPUT".into()
        },
        score_0_1: None,
        objective_values: BTreeMap::new(),
        metrics: BTreeMap::from([
            ("candidate_contract_hash_v1".into(), json!(candidate.contract_hash_v1())),
            ("ranking_quarantine".into(), Value::Bool(true)),
            ("scientific_applicability".into(), json!(if available { "IN_LOCKED_SHADOW_DOMAIN" } else { "UNVALIDATED" })),
            ("exact_ku_prediction".into(), Value::Null),
            ("class_anchor_ku_proxy".into(), Value::Null),
            ("declared_conditions".into(), json!({
                "dft_mil": dft,
                "temperature_C": temperature,
                "application_method": application_method,
                "pot_age_h": pot_age,
            })),
            ("computed_apparent_viscosity_pa_s".into(), json!(prediction.computed_apparent_viscosity_pa_s)),
            ("estimated_ku".into(), json!(prediction.estimated_ku)),
            ("estimated_sag_index_mil".into(), json!(prediction.estimated_sag_index_mil)),
            ("prediction".into(), serde_json::to_value(prediction).expect("prediction serializes")),
        ]),
        gates: BTreeMap::from([
            ("host_verified_artifact_and_receipt".into(), Value::Bool(available)),
            ("in_applicability_domain".into(), Value::Bool(prediction.in_applicability_domain)),
            ("solver_use_disabled".into(), Value::Bool(true)),
        ]),
        uncertainty: BTreeMap::from([
            ("apparent_viscosity_90".into(), json!(prediction.apparent_viscosity_interval)),
            ("ku_90".into(), json!(prediction.ku_interval)),
            ("sag_90".into(), json!(prediction.sag_interval)),
        ]),
        missing_inputs,
        explanations: vec!["Theory-constrained SHADOW computation; KU and D4400 sag use separate measured heads and never become ranking objectives.".into()],
        source_refs: vec![
            "https://doi.org/10.1038/164799b0".into(),
            "https://doi.org/10.1122/1.548848".into(),
            "https://store.astm.org/d0562-10r23.html".into(),
            "https://store.astm.org/d4400-18.html".into(),
        ],
        evidence_scope: "VISCOSITY_RHEOLOGY_SHADOW_ONLY".into(),
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ContractKind {
    Observation,
    ScreenObservation,
    Characterization,
    Dataset,
    Split,
    BenchmarkLock,
    ModelArtifact,
    Prediction,
    IndependentReview,
    BenchmarkReceipt,
}

pub fn preflight(kind: ContractKind, value: Value) -> Result<(String, String), ViscosityError> {
    match kind {
        ContractKind::Observation => {
            let contract: RheologyObservationV1 = decode(value)?;
            contract.validate_conditions()?;
            Ok((contract.schema, contract.observation_id))
        }
        ContractKind::ScreenObservation => {
            let contract: RheologyScreenObservationV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.observation_id))
        }
        ContractKind::Characterization => {
            let contract: RheologyCharacterizationV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.screen.observation_id))
        }
        ContractKind::Dataset => {
            let contract: ViscosityDatasetV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.dataset_id))
        }
        ContractKind::Split => {
            let contract: ViscositySplitV1 = decode(value)?;
            contract.validate(None)?;
            Ok((contract.schema, contract.split_id))
        }
        ContractKind::BenchmarkLock => {
            let contract: ViscosityBenchmarkLockV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.benchmark_id))
        }
        ContractKind::ModelArtifact => {
            let contract: ViscosityModelArtifactV1 = decode(value)?;
            contract.validate()?;
            Ok((contract.schema, contract.model_id))
        }
        ContractKind::Prediction => {
            let contract: ViscosityPredictionV1 = decode(value)?;
            if contract.schema != PREDICTION_SCHEMA || contract.module_id != MODULE_ID {
                return Err(ViscosityError::Identity);
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

fn interval_contains(interval: [f64; 2], value: f64) -> bool {
    value >= interval[0] && value <= interval[1]
}

fn balanced_accuracy(values: impl Iterator<Item = (bool, bool)>) -> Result<f64, ViscosityError> {
    let mut positive = [0_usize; 2];
    let mut negative = [0_usize; 2];
    for (observed, predicted) in values {
        let bucket = if observed {
            &mut positive
        } else {
            &mut negative
        };
        bucket[1] += 1;
        if observed == predicted {
            bucket[0] += 1;
        }
    }
    if positive[1] == 0 || negative[1] == 0 {
        return Err(ViscosityError::Empty("both sag classes"));
    }
    Ok(0.5 * (positive[0] as f64 / positive[1] as f64 + negative[0] as f64 / negative[1] as f64))
}

fn paired_cluster_bootstrap_lower(values: &[(&str, f64)]) -> Result<f64, ViscosityError> {
    let mut by_cluster = BTreeMap::<&str, Vec<f64>>::new();
    for (cluster, value) in values {
        if !value.is_finite() {
            return Err(ViscosityError::Range("paired improvement"));
        }
        by_cluster.entry(cluster).or_default().push(*value);
    }
    if by_cluster.is_empty() {
        return Err(ViscosityError::Empty("independent clusters"));
    }
    let cluster_means: Vec<_> = by_cluster
        .values()
        .map(|rows| rows.iter().sum::<f64>() / rows.len() as f64)
        .collect();
    if cluster_means.len() == 1 {
        return Ok(cluster_means[0]);
    }
    let mut state = RESIDUAL_MODEL_SEED;
    let mut replicates = Vec::with_capacity(10_000);
    for _ in 0..10_000 {
        let mut total = 0.0;
        for _ in 0..cluster_means.len() {
            state = state
                .wrapping_mul(6_364_136_223_846_793_005)
                .wrapping_add(1_442_695_040_888_963_407);
            total += cluster_means[(state as usize) % cluster_means.len()];
        }
        replicates.push(total / cluster_means.len() as f64);
    }
    replicates.sort_by(f64::total_cmp);
    Ok(replicates[249])
}

fn decode<T: for<'de> Deserialize<'de>>(value: Value) -> Result<T, ViscosityError> {
    serde_json::from_value(value).map_err(|error| ViscosityError::Json(error.to_string()))
}

fn build_domain(training: &[&RheologyObservationV1]) -> ApplicabilityDomainV1 {
    let range = |values: Vec<f64>| {
        [
            values.iter().copied().fold(f64::INFINITY, f64::min),
            values.iter().copied().fold(f64::NEG_INFINITY, f64::max),
        ]
    };
    let mut ingredient_lots: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for row in training {
        for (ingredient, lot) in &row.ingredients {
            ingredient_lots
                .entry(ingredient.clone())
                .or_default()
                .insert(lot.clone());
        }
    }
    ApplicabilityDomainV1 {
        ingredient_lots: ingredient_lots
            .into_iter()
            .map(|(key, values)| (key, values.into_iter().collect()))
            .collect(),
        temperature_c: range(training.iter().map(|row| row.temperature_c).collect()),
        shear_rate_s_inv: range(training.iter().map(|row| row.shear_rate_s_inv).collect()),
        pot_age_h: range(training.iter().map(|row| row.pot_age_h).collect()),
        wet_film_thickness_mil: range(
            training
                .iter()
                .map(|row| row.wet_film_thickness_mil)
                .collect(),
        ),
        methods: vec!["ASTM_D562".into(), "ASTM_D4400".into()],
    }
}

fn validate_ranges(domain: &ApplicabilityDomainV1) -> Result<(), ViscosityError> {
    if domain.ingredient_lots.is_empty()
        || [
            domain.temperature_c,
            domain.shear_rate_s_inv,
            domain.pot_age_h,
            domain.wet_film_thickness_mil,
        ]
        .iter()
        .any(|range| range.iter().any(|value| !value.is_finite()) || range[0] > range[1])
        || !domain.methods.iter().any(|method| method == "ASTM_D562")
        || !domain.methods.iter().any(|method| method == "ASTM_D4400")
    {
        return Err(ViscosityError::Range("applicability domain"));
    }
    Ok(())
}

fn in_domain(row: &RheologyObservationV1, domain: &ApplicabilityDomainV1) -> bool {
    let range_contains = |range: [f64; 2], value: f64| value >= range[0] && value <= range[1];
    row.ingredients.len() == domain.ingredient_lots.len()
        && row.ingredients.iter().all(|(ingredient, lot)| {
            domain
                .ingredient_lots
                .get(ingredient)
                .is_some_and(|lots| lots.contains(lot))
        })
        && range_contains(domain.temperature_c, row.temperature_c)
        && range_contains(domain.shear_rate_s_inv, row.shear_rate_s_inv)
        && range_contains(domain.pot_age_h, row.pot_age_h)
        && range_contains(domain.wet_film_thickness_mil, row.wet_film_thickness_mil)
        && domain.methods.contains(&row.ku_method)
        && domain.methods.contains(&row.sag_method)
}

fn interval(lower: f64, upper: f64, method: &str) -> ConfidenceIntervalV1 {
    ConfidenceIntervalV1 {
        lower,
        upper,
        confidence: 0.9,
        method: method.into(),
    }
}

fn linear_fit(x: &[f64], y: &[f64]) -> (f64, f64) {
    let x_mean = x.iter().sum::<f64>() / x.len() as f64;
    let y_mean = y.iter().sum::<f64>() / y.len() as f64;
    let denominator = x.iter().map(|value| (value - x_mean).powi(2)).sum::<f64>();
    let slope = if denominator <= f64::EPSILON {
        0.0
    } else {
        x.iter()
            .zip(y)
            .map(|(left, right)| (left - x_mean) * (right - y_mean))
            .sum::<f64>()
            / denominator
    };
    (y_mean - slope * x_mean, slope)
}

fn median(values: &[f64]) -> f64 {
    let mut values = values.to_vec();
    values.sort_by(f64::total_cmp);
    if values.len().is_multiple_of(2) {
        (values[values.len() / 2 - 1] + values[values.len() / 2]) / 2.0
    } else {
        values[values.len() / 2]
    }
}

fn quantile90(values: &[f64]) -> f64 {
    let mut values = values.to_vec();
    values.sort_by(f64::total_cmp);
    values[((values.len() - 1) as f64 * 0.9).ceil() as usize]
}

fn require_identity(schema: &str, expected: &str, module: &str) -> Result<(), ViscosityError> {
    if schema == expected && module == MODULE_ID {
        Ok(())
    } else {
        Err(ViscosityError::Identity)
    }
}

fn require_text(field: &'static str, value: &str) -> Result<(), ViscosityError> {
    if value.trim().is_empty() {
        Err(ViscosityError::Empty(field))
    } else {
        Ok(())
    }
}

fn require_hash(field: &'static str, value: &str) -> Result<(), ViscosityError> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(ViscosityError::Hash(field))
    }
}

fn validate_hash_map(values: &BTreeMap<String, String>) -> Result<(), ViscosityError> {
    if values.is_empty() {
        return Err(ViscosityError::Empty("raw_file_hashes"));
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

    fn measured_observation() -> RheologyObservationV1 {
        RheologyObservationV1 {
            schema: OBSERVATION_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            observation_id: "obs-1".into(),
            candidate_id: "candidate-1".into(),
            formulation_id: "formulation-1".into(),
            formulation_family: "family-1".into(),
            preparation_id: "preparation-1".into(),
            replicate_id: "replicate-1".into(),
            ingredients: BTreeMap::from([
                ("liquid-1".into(), "lot-liquid-1".into()),
                ("pigment-1".into(), "lot-pigment-1".into()),
            ]),
            liquids: vec![LiquidComponentV1 {
                ingredient_id: "liquid-1".into(),
                lot_id: "lot-liquid-1".into(),
                mass_fraction_0_1: 1.0,
                viscosity_pa_s_at_reference: 0.8,
                reference_temperature_c: 22.8,
                activation_energy_j_mol: 30_000.0,
            }],
            pigments: vec![PigmentComponentV1 {
                ingredient_id: "pigment-1".into(),
                lot_id: "lot-pigment-1".into(),
                volume_fraction_0_1: 0.2,
                morphology: Some("ACICULAR".into()),
                oil_absorption_g_per_100g: None,
            }],
            rheology_additives: vec![RheologyAdditiveV1 {
                ingredient_id: "rheology-1".into(),
                lot_id: "lot-rheology-1".into(),
                loading_mass_fraction_0_1: 0.01,
                activation_protocol: "LOCKED_HIGH_SHEAR".into(),
            }],
            density_kg_m3: 1_200.0,
            solids_volume_fraction_0_1: 0.5,
            pvc_fraction_0_1: 0.2,
            maximum_packing_fraction_0_1: 0.64,
            intrinsic_viscosity: 2.5,
            yield_stress_pa: 12.0,
            consistency_pa_s_n: 2.0,
            flow_index_n: 0.7,
            pre_shear_s_inv: 100.0,
            pre_shear_duration_s: 60.0,
            pot_age_h: 1.0,
            temperature_c: 22.8,
            shear_rate_s_inv: 10.0,
            wet_film_thickness_mil: 10.0,
            application_angle_deg_from_horizontal: 90.0,
            instrument_id: "rheometer-1".into(),
            calibration_id: "calibration-1".into(),
            ku_method: "ASTM_D562".into(),
            sag_method: "ASTM_D4400".into(),
            measured_apparent_viscosity_pa_s: Some(6.0),
            measured_ku: Some(95.0),
            measured_sag_index_mil: Some(8.0),
            sag_unsafe: Some(false),
            raw_file_hashes: BTreeMap::from([("flow.csv".into(), "a".repeat(64))]),
            rights_receipt_sha256: "b".repeat(64),
            rights_eligible: true,
        }
    }

    #[test]
    fn test_known_answers_cover_mixing_temperature_crowding_yield_and_sag() {
        let mixed =
            grunberg_nissan_mix(&[0.5, 0.5], &[1.0, 4.0], &[vec![0.0, 0.0], vec![0.0, 0.0]])
                .unwrap();
        assert!((mixed - 2.0).abs() < 1e-12);
        let cold = arrhenius_viscosity(1.0, 25.0, 10.0, 30_000.0).unwrap();
        assert!(cold > 1.0);
        assert!((krieger_dougherty(1.0, 0.0, 0.64, 2.5).unwrap() - 1.0).abs() < 1e-12);
        assert!(
            (herschel_bulkley_apparent_viscosity(10.0, 2.0, 1.0, 5.0).unwrap() - 4.0).abs() < 1e-12
        );
        let stress = sag_stress_pa(1_000.0, 10.0, 90.0).unwrap();
        assert!((stress - 2.490_889_1).abs() < 1e-6);
    }

    #[test]
    fn test_malformed_and_non_finite_inputs_fail_closed() {
        assert!(grunberg_nissan_mix(&[1.0], &[f64::NAN], &[vec![0.0]]).is_err());
        assert!(krieger_dougherty(1.0, 0.64, 0.64, 2.5).is_err());
        assert!(sag_stress_pa(1_000.0, -1.0, 90.0).is_err());
    }

    #[test]
    fn test_unknown_fields_are_rejected() {
        let error = serde_json::from_value::<LiquidComponentV1>(json!({
            "ingredient_id":"a", "lot_id":"l", "mass_fraction_0_1":1.0,
            "viscosity_pa_s_at_reference":1.0, "reference_temperature_c":25.0,
            "activation_energy_j_mol":30000.0, "forged_validation":true
        }))
        .unwrap_err();
        assert!(error.to_string().contains("unknown field"));
    }

    #[test]
    fn screen_contract_rejects_measured_outcome_features() {
        let mut screen = json!({
            "schema": SCREEN_OBSERVATION_SCHEMA,
            "module_id": MODULE_ID,
            "observation_id": "screen-1",
            "candidate_id": "candidate-1",
            "formulation_id": "formula-1",
            "formulation_family": "DGEBA_POLYAMIDE",
            "preparation_id": "prep-1",
            "ingredients": {"resin": "lot-1"},
            "liquids": [{
                "ingredient_id": "solvent", "lot_id": "lot-2",
                "mass_fraction_0_1": 1.0, "viscosity_pa_s_at_reference": 0.01,
                "reference_temperature_c": 25.0, "activation_energy_j_mol": 10000.0
            }],
            "pigments": [],
            "rheology_additives": [],
            "density_kg_m3": 1200.0,
            "solids_volume_fraction_0_1": 0.6,
            "pvc_fraction_0_1": 0.2,
            "cpvc_fraction_0_1": 0.5,
            "pot_age_h": 0.0,
            "temperature_c": 25.0,
            "wet_film_thickness_mil": 6.0,
            "application_geometry": "VERTICAL_PANEL",
            "process_protocol": "LOCKED_MIX_V1",
            "rights_receipt_sha256": "a".repeat(64),
            "rights_eligible": true
        });
        serde_json::from_value::<RheologyScreenObservationV1>(screen.clone())
            .unwrap()
            .validate()
            .unwrap();
        screen["measured_ku"] = json!(95.0);
        let error = serde_json::from_value::<RheologyScreenObservationV1>(screen).unwrap_err();
        assert!(error.to_string().contains("unknown field"));
    }

    #[test]
    fn test_fit_replays_deterministically_and_ood_abstains() {
        let observation = measured_observation();
        let dataset = ViscosityDatasetV1 {
            schema: DATASET_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            dataset_id: "dataset-1".into(),
            observations: vec![observation.clone()],
        };
        let split = ViscositySplitV1 {
            schema: SPLIT_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            split_id: "split-1".into(),
            dataset_sha256: dataset.identity_hash(),
            assignments: vec![SplitAssignmentV1 {
                observation_id: observation.observation_id.clone(),
                formulation_id: observation.formulation_id.clone(),
                family: observation.formulation_family.clone(),
                temperature_group: "22.8C".into(),
                split: "FIT".into(),
            }],
        };
        let lock = ViscosityBenchmarkLockV1 {
            schema: BENCHMARK_LOCK_SCHEMA.into(),
            module_id: MODULE_ID.into(),
            benchmark_id: "benchmark-1".into(),
            dataset_sha256: dataset.identity_hash(),
            split_sha256: split.identity_hash(),
            baselines: vec![
                "family-temperature-median".into(),
                "composition-ridge".into(),
                "nearest-family".into(),
                "ideal-liquid-crowding".into(),
                "no-yield".into(),
                "majority-class".into(),
            ],
            hostile_nulls: vec!["SHUFFLE".into()],
            thresholds: BTreeMap::new(),
            immutable: true,
        };
        let first = fit_model(&dataset, &split, &lock).unwrap();
        let second = fit_model(&dataset, &split, &lock).unwrap();
        assert_eq!(first, second);
        assert!(!first.promotion_dataset_complete);

        let prediction = predict(&first, &observation).unwrap();
        assert!(prediction.computed_apparent_viscosity_pa_s.is_some());
        assert!(prediction.estimated_ku.is_some());
        assert!(prediction.estimated_sag_index_mil.is_some());
        assert!(prediction.exact_ku_prediction.is_none());
        assert!(prediction.apparent_viscosity_interval.is_some());

        let mut outside = observation;
        outside.temperature_c = 35.0;
        let abstention = predict(&first, &outside).unwrap();
        assert!(!abstention.in_applicability_domain);
        assert!(abstention.computed_apparent_viscosity_pa_s.is_none());
        assert!(!abstention.abstention_reasons.is_empty());
    }

    // -----------------------------------------------------------------
    // Phase-0 Arrhenius pure-solvent red-team tests
    // -----------------------------------------------------------------

    #[test]
    fn arrhenius_viscosity_rejects_non_finite_inputs() {
        for bad in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            assert!(arrhenius_viscosity(bad, 25.0, 40.0, 10000.0).is_err(),
                "non-finite reference viscosity {bad} must reject");
            assert!(arrhenius_viscosity(0.5e-3, bad, 40.0, 10000.0).is_err(),
                "non-finite reference temperature {bad} must reject");
            assert!(arrhenius_viscosity(0.5e-3, 25.0, bad, 10000.0).is_err(),
                "non-finite test temperature {bad} must reject");
            assert!(arrhenius_viscosity(0.5e-3, 25.0, 40.0, bad).is_err(),
                "non-finite activation energy {bad} must reject");
        }
    }

    #[test]
    fn arrhenius_viscosity_rejects_negative_or_zero_viscosity_and_ea() {
        assert!(arrhenius_viscosity(0.0, 25.0, 40.0, 10000.0).is_err());
        assert!(arrhenius_viscosity(-0.5e-3, 25.0, 40.0, 10000.0).is_err());
        assert!(arrhenius_viscosity(0.5e-3, 25.0, 40.0, 0.0).is_err());
        assert!(arrhenius_viscosity(0.5e-3, 25.0, 40.0, -1000.0).is_err());
    }

    #[test]
    fn arrhenius_viscosity_rejects_temperatures_outside_physical_range() {
        // Absolute zero is -273.15 °C; the check window is [-273.14, 500.0].
        assert!(arrhenius_viscosity(0.5e-3, -300.0, 40.0, 10000.0).is_err(),
            "T_ref below absolute zero must reject");
        assert!(arrhenius_viscosity(0.5e-3, 25.0, -273.20, 10000.0).is_err(),
            "T below absolute zero must reject");
        assert!(arrhenius_viscosity(0.5e-3, 25.0, 700.0, 10000.0).is_err(),
            "T above 500°C (superheated-steam regime, outside Newtonian assumption) must reject");
        assert!(arrhenius_viscosity(0.5e-3, 600.0, 40.0, 10000.0).is_err(),
            "T_ref above 500°C must reject");
    }

    #[test]
    fn arrhenius_viscosity_is_byte_deterministic_across_replays() {
        let first = arrhenius_viscosity(0.560e-3, 25.0, 40.0, 8873.3).unwrap();
        let second = arrhenius_viscosity(0.560e-3, 25.0, 40.0, 8873.3).unwrap();
        assert_eq!(first.to_bits(), second.to_bits());
    }

    #[test]
    fn arrhenius_viscosity_reduces_to_reference_at_reference_temperature() {
        // exp(0) = 1 exactly for finite inputs; identity is byte-exact.
        for &(eta, t) in &[
            (0.560e-3_f64, 25.0_f64),
            (1.074e-3, 25.0),
            (0.294e-3, 25.0),
            (2.038e-3, 40.0),
        ] {
            let out = arrhenius_viscosity(eta, t, t, 10_000.0).unwrap();
            assert_eq!(out.to_bits(), eta.to_bits(),
                "identity T=T_ref should return exactly eta_ref");
        }
    }

    #[test]
    fn arrhenius_viscosity_monotone_decreases_with_temperature_for_positive_ea() {
        // For any solvent with Ea > 0, warming reduces viscosity.
        let cold = arrhenius_viscosity(0.560e-3, 25.0, 20.0, 8873.3).unwrap();
        let ref_ = arrhenius_viscosity(0.560e-3, 25.0, 25.0, 8873.3).unwrap();
        let warm = arrhenius_viscosity(0.560e-3, 25.0, 40.0, 8873.3).unwrap();
        let hot = arrhenius_viscosity(0.560e-3, 25.0, 60.0, 8873.3).unwrap();
        assert!(cold > ref_ && ref_ > warm && warm > hot,
            "positive Ea ⇒ viscosity monotone decreases with T: {cold} > {ref_} > {warm} > {hot}");
    }
}
