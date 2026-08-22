use amphora_core::stable_hash;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

pub const POT_LIFE_TRACK_ID: &str = "coating-pot-life-physics-v1";
pub const MODULE_ID: &str = "amphora-cure-potlife-gate";
pub const POT_LIFE_RUN_SCHEMA: &str = "amphora.pot-life-run.v1";
pub const POT_LIFE_MODEL_ARTIFACT_SCHEMA: &str = "amphora.pot-life-model-artifact.v1";
pub const POT_LIFE_PREDICTION_SCHEMA: &str = "amphora.pot-life-prediction.v1";
pub const POT_LIFE_PROTOCOL_SCHEMA: &str = "amphora.pot-life-protocol.v1";
pub const POT_LIFE_BENCHMARK_LOCK_SCHEMA: &str = "amphora.pot-life-benchmark-lock.v1";
pub const BENCHMARK_RECEIPT_SCHEMA: &str = "amphora.pot-life-benchmark-receipt.v1";
pub const EVIDENCE_REVIEW_RECEIPT_SCHEMA: &str = "amphora.pot-life-evidence-review-receipt.v1";
pub const INDEPENDENT_REVIEW_SCHEMA: &str = "amphora.pot-life-independent-review.v1";
pub const EXPERT_PACKET_SCHEMA: &str = "amphora.pot-life-expert-packet.v1";

#[derive(Debug, Error, PartialEq)]
pub enum PotLifeError {
    #[error("unexpected schema {actual}; expected {expected}")]
    Schema {
        actual: String,
        expected: &'static str,
    },
    #[error("track must be coating-pot-life-physics-v1")]
    Track,
    #[error("required field is empty: {0}")]
    Empty(&'static str),
    #[error("invalid SHA-256 in {0}")]
    Hash(&'static str),
    #[error("non-finite or out-of-range field: {0}")]
    Range(&'static str),
    #[error("time series is not strictly ordered: {0}")]
    TimeOrder(&'static str),
    #[error("measurement schedule is invalid: {0}")]
    Schedule(&'static str),
    #[error("spray pass/fail declaration does not match the locked checklist")]
    SprayDeclaration,
    #[error("application pot life must be bounded by a last pass and first failure")]
    EndpointInterval,
    #[error("73 °F runs must be sealed holdouts and 65/95 °F runs must be fit rows")]
    Split,
    #[error("owned-run contract rejects non-owned or derivative-use-unreviewed evidence")]
    Rights,
    #[error("duplicate identity in {0}")]
    Duplicate(&'static str),
    #[error("reduced model contains an unsupported or unidentifiable parameter")]
    UnidentifiableParameter,
    #[error("model artifact is invalid: {0}")]
    Model(&'static str),
    #[error("application prediction has exceeded its authority")]
    Authority,
    #[error("request is outside the locked applicability domain")]
    OutOfDomain,
    #[error("JSON contract error: {0}")]
    Json(String),
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum PotLifeRunSplitV1 {
    Fit,
    SealedHoldout,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EvidenceOriginV1 {
    Owned,
    Public,
    Supplier,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum SprayFailurePropertyV1 {
    Pumpability,
    LockedPressure,
    FullFan30Seconds,
    WetFilmThickness,
    TipBlockage,
    Gel,
    Seed,
    PhaseSplit,
    AddedThinner,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum PotLifeEndpointV1 {
    AirlessSprayFirstPropertyFailure,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ResearchAuthorityV1 {
    Shadow,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct FunctionalityDistributionV1 {
    pub functionality: f64,
    pub mole_fraction_0_1: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeCompositionV1 {
    pub eew_g_per_eq: f64,
    pub ahew_g_per_eq: f64,
    pub epoxy_functionality: Option<Vec<FunctionalityDistributionV1>>,
    pub primary_amine_functionality: Option<Vec<FunctionalityDistributionV1>>,
    pub secondary_amine_functionality: Option<Vec<FunctionalityDistributionV1>>,
    pub epoxy_to_active_hydrogen_equivalent_ratio: f64,
    pub solids_mass_pct: f64,
    pub pvc_pct: f64,
    pub solvents_mass_fraction_0_1: BTreeMap<String, f64>,
    pub filler_mass_fraction_0_1: f64,
    pub catalyst_mass_fraction_0_1: f64,
    pub water_mass_fraction_0_1: f64,
    pub density_g_ml: f64,
    pub initial_rheology_method: String,
}

impl PotLifeCompositionV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        for value in [
            self.eew_g_per_eq,
            self.ahew_g_per_eq,
            self.epoxy_to_active_hydrogen_equivalent_ratio,
            self.density_g_ml,
        ] {
            if !value.is_finite() || value <= 0.0 {
                return Err(PotLifeError::Range("composition positive values"));
            }
        }
        for (field, value, upper) in [
            ("solids_mass_pct", self.solids_mass_pct, 100.0),
            ("pvc_pct", self.pvc_pct, 100.0),
            (
                "filler_mass_fraction_0_1",
                self.filler_mass_fraction_0_1,
                1.0,
            ),
            (
                "catalyst_mass_fraction_0_1",
                self.catalyst_mass_fraction_0_1,
                1.0,
            ),
            ("water_mass_fraction_0_1", self.water_mass_fraction_0_1, 1.0),
        ] {
            if !value.is_finite() || !(0.0..=upper).contains(&value) {
                return Err(PotLifeError::Range(field));
            }
        }
        if self.initial_rheology_method.trim().is_empty() {
            return Err(PotLifeError::Empty("initial_rheology_method"));
        }
        let solvent_total = self
            .solvents_mass_fraction_0_1
            .values()
            .try_fold(0.0, |sum, value| {
                (value.is_finite() && (0.0..=1.0).contains(value)).then_some(sum + value)
            })
            .ok_or(PotLifeError::Range("solvents_mass_fraction_0_1"))?;
        if solvent_total > 1.0 + 1e-9 {
            return Err(PotLifeError::Range("solvents_mass_fraction_0_1"));
        }
        for distribution in [
            &self.epoxy_functionality,
            &self.primary_amine_functionality,
            &self.secondary_amine_functionality,
        ]
        .into_iter()
        .flatten()
        {
            if distribution.is_empty()
                || distribution.iter().any(|row| {
                    !row.functionality.is_finite()
                        || row.functionality <= 0.0
                        || !row.mole_fraction_0_1.is_finite()
                        || !(0.0..=1.0).contains(&row.mole_fraction_0_1)
                })
                || (distribution
                    .iter()
                    .map(|row| row.mole_fraction_0_1)
                    .sum::<f64>()
                    - 1.0)
                    .abs()
                    > 1e-6
            {
                return Err(PotLifeError::Range("functionality distribution"));
            }
        }
        Ok(())
    }

    pub fn allows_flory_stockmayer_bounds(&self) -> bool {
        self.epoxy_functionality.is_some()
            && self.primary_amine_functionality.is_some()
            && self.secondary_amine_functionality.is_some()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ContainerGeometryV1 {
    pub geometry_id: String,
    pub shape: String,
    pub inside_diameter_mm: f64,
    pub fill_height_mm: f64,
    pub headspace_ml: f64,
    pub nominal_volume_ml: f64,
    pub lid_handling: String,
}

impl ContainerGeometryV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_text("geometry_id", &self.geometry_id)?;
        require_text("geometry.shape", &self.shape)?;
        require_text("geometry.lid_handling", &self.lid_handling)?;
        if [
            self.inside_diameter_mm,
            self.fill_height_mm,
            self.nominal_volume_ml,
        ]
        .iter()
        .any(|value| !value.is_finite() || *value <= 0.0)
            || !self.headspace_ml.is_finite()
            || self.headspace_ml < 0.0
        {
            return Err(PotLifeError::Range("container_geometry"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("geometry serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct AirlessSpraySetupV1 {
    pub setup_id: String,
    pub pump_id: String,
    pub tip_orifice_in: f64,
    pub tip_fan_width_in: f64,
    pub locked_pressure_psi: f64,
    pub hose_length_ft: f64,
    pub hose_inside_diameter_in: f64,
    pub filter_mesh: u32,
    pub locked_pass_count: u32,
    pub thinning_allowed: bool,
}

impl AirlessSpraySetupV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_text("spray_setup.setup_id", &self.setup_id)?;
        require_text("spray_setup.pump_id", &self.pump_id)?;
        if [
            self.tip_orifice_in,
            self.tip_fan_width_in,
            self.locked_pressure_psi,
            self.hose_length_ft,
            self.hose_inside_diameter_in,
        ]
        .iter()
        .any(|value| !value.is_finite() || *value <= 0.0)
            || self.filter_mesh == 0
            || self.locked_pass_count == 0
            || self.thinning_allowed
        {
            return Err(PotLifeError::Range("airless_spray_setup"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("spray setup serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct TemperatureObservationV1 {
    pub elapsed_min: f64,
    pub material_temperature_c: f64,
    pub ambient_temperature_c: f64,
    pub relative_humidity_pct: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct StormerObservationV1 {
    pub elapsed_min: f64,
    pub raw_response_ku: f64,
    pub raw_load_g: f64,
    pub equivalent_viscosity_mpa_s: Option<f64>,
    pub certified_mapping_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct SprayCheckV1 {
    pub elapsed_min: f64,
    pub stable_pumping: bool,
    pub locked_pressure_maintained: bool,
    pub stable_full_fan_30_s: bool,
    pub wft_mil: Vec<f64>,
    pub no_tip_blockage: bool,
    pub no_gel: bool,
    pub no_seed: bool,
    pub no_phase_split: bool,
    pub thinner_added: bool,
    pub pass: bool,
    pub first_failed_property: Option<SprayFailurePropertyV1>,
}

impl SprayCheckV1 {
    pub fn checklist_passes(&self) -> bool {
        self.stable_pumping
            && self.locked_pressure_maintained
            && self.stable_full_fan_30_s
            && !self.wft_mil.is_empty()
            && self
                .wft_mil
                .iter()
                .all(|value| value.is_finite() && (7.0..=9.0).contains(value))
            && self.no_tip_blockage
            && self.no_gel
            && self.no_seed
            && self.no_phase_split
            && !self.thinner_added
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeRunV1 {
    pub schema: String,
    pub track_id: String,
    pub run_id: String,
    pub protocol_sha256: String,
    pub formulation_id: String,
    pub formulation_hash: String,
    pub raw_material_lot_hashes: BTreeMap<String, String>,
    pub independent_mix_id: String,
    pub batch_id: String,
    pub run_day: String,
    pub replicate: u8,
    pub split: PotLifeRunSplitV1,
    pub target_temperature_f: u16,
    pub evidence_origin: EvidenceOriginV1,
    pub derivative_use_review_sha256: Option<String>,
    pub composition: PotLifeCompositionV1,
    pub mixed_mass_g: f64,
    pub mix_ratio_by_volume: String,
    pub induction_time_min: f64,
    pub geometry: ContainerGeometryV1,
    pub spray_setup: AirlessSpraySetupV1,
    pub operator_id: String,
    pub calibration_ids: BTreeMap<String, String>,
    pub mixing_history: Vec<String>,
    pub temperature_series: Vec<TemperatureObservationV1>,
    pub stormer_series: Vec<StormerObservationV1>,
    pub spray_checks: Vec<SprayCheckV1>,
    pub locked_ku_threshold: Option<f64>,
    #[serde(default)]
    pub deviations: Vec<String>,
    pub photographs_sha256: Vec<String>,
    pub raw_file_hashes: BTreeMap<String, String>,
}

impl PotLifeRunV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_schema(&self.schema, POT_LIFE_RUN_SCHEMA)?;
        require_track(&self.track_id)?;
        for (field, value) in [
            ("run_id", self.run_id.as_str()),
            ("formulation_id", self.formulation_id.as_str()),
            ("independent_mix_id", self.independent_mix_id.as_str()),
            ("batch_id", self.batch_id.as_str()),
            ("run_day", self.run_day.as_str()),
            ("operator_id", self.operator_id.as_str()),
        ] {
            require_text(field, value)?;
        }
        require_hash("protocol_sha256", &self.protocol_sha256)?;
        require_hash("formulation_hash", &self.formulation_hash)?;
        require_hash_map(
            "raw_material_lot_hashes",
            &self.raw_material_lot_hashes,
            true,
        )?;
        require_hash_map("raw_file_hashes", &self.raw_file_hashes, true)?;
        if self.photographs_sha256.is_empty()
            || self.photographs_sha256.iter().any(|hash| !is_sha256(hash))
        {
            return Err(PotLifeError::Hash("photographs_sha256"));
        }
        if self.evidence_origin != EvidenceOriginV1::Owned
            || self.derivative_use_review_sha256.is_some()
        {
            return Err(PotLifeError::Rights);
        }
        if !matches!(self.formulation_id.as_str(), "M00097" | "M00101" | "M00109")
            || !matches!(self.target_temperature_f, 65 | 73 | 95)
            || !(1..=3).contains(&self.replicate)
        {
            return Err(PotLifeError::Range("design assignment"));
        }
        let expected_split = if self.target_temperature_f == 73 {
            PotLifeRunSplitV1::SealedHoldout
        } else {
            PotLifeRunSplitV1::Fit
        };
        if self.split != expected_split {
            return Err(PotLifeError::Split);
        }
        self.composition.validate()?;
        self.geometry.validate()?;
        self.spray_setup.validate()?;
        if !self.mixed_mass_g.is_finite()
            || self.mixed_mass_g <= 0.0
            || self.mix_ratio_by_volume != "1:1"
            || (self.induction_time_min - 30.0).abs() > 1e-9
        {
            return Err(PotLifeError::Range("locked mixing conditions"));
        }
        for required in ["stormer", "temperature_logger", "sprayer_pressure"] {
            if self
                .calibration_ids
                .get(required)
                .is_none_or(|value| value.trim().is_empty())
            {
                return Err(PotLifeError::Empty("calibration_ids"));
            }
        }
        if self.mixing_history.is_empty()
            || self
                .mixing_history
                .iter()
                .any(|value| value.trim().is_empty())
        {
            return Err(PotLifeError::Empty("mixing_history"));
        }
        validate_temperature_series(&self.temperature_series)?;
        validate_stormer_series(&self.stormer_series, &self.calibration_ids)?;
        validate_spray_series(&self.spray_checks, self.viscosity_trigger_time_min())?;
        self.observed_application_interval()?;
        if self
            .locked_ku_threshold
            .is_some_and(|value| !value.is_finite() || value <= 0.0)
        {
            return Err(PotLifeError::Range("locked_ku_threshold"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("run serializes"))
    }

    pub fn geometry_hash(&self) -> String {
        self.geometry.identity_hash()
    }

    pub fn spray_setup_hash(&self) -> String {
        self.spray_setup.identity_hash()
    }

    pub fn adapter_key(&self) -> String {
        format!(
            "{}|{}|{}",
            self.formulation_id,
            self.geometry_hash(),
            self.spray_setup_hash()
        )
    }

    pub fn viscosity_trigger_time_min(&self) -> Option<f64> {
        let initial = self
            .stormer_series
            .first()
            .and_then(|row| row.equivalent_viscosity_mpa_s)?;
        self.stormer_series.iter().find_map(|row| {
            row.equivalent_viscosity_mpa_s
                .filter(|value| *value >= 1.5 * initial)
                .map(|_| row.elapsed_min)
        })
    }

    pub fn observed_application_interval(&self) -> Result<ObservedPotLifeIntervalV1, PotLifeError> {
        let failure_index = self
            .spray_checks
            .iter()
            .position(|row| !row.pass)
            .ok_or(PotLifeError::EndpointInterval)?;
        let last_pass = self.spray_checks[..failure_index]
            .iter()
            .rev()
            .find(|row| row.pass)
            .ok_or(PotLifeError::EndpointInterval)?;
        let first_fail = &self.spray_checks[failure_index];
        if first_fail.elapsed_min <= last_pass.elapsed_min {
            return Err(PotLifeError::EndpointInterval);
        }
        Ok(ObservedPotLifeIntervalV1 {
            last_pass_min: last_pass.elapsed_min,
            first_fail_min: first_fail.elapsed_min,
            failed_property: first_fail
                .first_failed_property
                .ok_or(PotLifeError::EndpointInterval)?,
        })
    }

    pub fn viscosity_proxy(&self) -> Option<ViscosityProxyV1> {
        let initial = self.stormer_series.first()?;
        if let Some(initial_viscosity) = initial.equivalent_viscosity_mpa_s {
            let threshold = 2.0 * initial_viscosity;
            let observed_time_h = self.stormer_series.iter().find_map(|row| {
                row.equivalent_viscosity_mpa_s
                    .filter(|value| *value >= threshold)
                    .map(|_| row.elapsed_min / 60.0)
            });
            return Some(ViscosityProxyV1 {
                kind: ViscosityProxyKindV1::EquivalentViscosityDoubling,
                threshold,
                unit: "mPa_s".into(),
                observed_or_predicted_time_h: observed_time_h,
                certified_mapping_id: initial.certified_mapping_id.clone(),
            });
        }
        self.locked_ku_threshold.map(|threshold| ViscosityProxyV1 {
            kind: ViscosityProxyKindV1::KuThresholdOnly,
            threshold,
            unit: "KU".into(),
            observed_or_predicted_time_h: self
                .stormer_series
                .iter()
                .find(|row| row.raw_response_ku >= threshold)
                .map(|row| row.elapsed_min / 60.0),
            certified_mapping_id: None,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ObservedPotLifeIntervalV1 {
    pub last_pass_min: f64,
    pub first_fail_min: f64,
    pub failed_property: SprayFailurePropertyV1,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ViscosityProxyKindV1 {
    EquivalentViscosityDoubling,
    KuThresholdOnly,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ViscosityProxyV1 {
    pub kind: ViscosityProxyKindV1,
    pub threshold: f64,
    pub unit: String,
    pub observed_or_predicted_time_h: Option<f64>,
    pub certified_mapping_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ParameterIntervalV1 {
    pub lower: f64,
    pub estimate: f64,
    pub upper: f64,
    pub confidence: f64,
    pub bounded: bool,
}

impl ParameterIntervalV1 {
    fn validate(&self) -> bool {
        [self.lower, self.estimate, self.upper, self.confidence]
            .iter()
            .all(|value| value.is_finite())
            && self.lower <= self.estimate
            && self.estimate <= self.upper
            && (0.0..=1.0).contains(&self.confidence)
            && self.bounded
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ReducedPhysicalParametersV1 {
    pub activation_energy_j_mol: f64,
    pub reference_temperature_k: f64,
    pub gel_clock_min: f64,
    pub chemorheology_exponent: f64,
    pub cure_scale_by_formulation: BTreeMap<String, f64>,
    pub primary_amine_rate_constant: Option<f64>,
    pub secondary_amine_rate_constant: Option<f64>,
    pub hydroxyl_autocatalysis_constant: Option<f64>,
    pub etherification_rate_constant: Option<f64>,
    pub diffusion_vitrification_parameter: Option<f64>,
    pub heat_transfer_coefficient: Option<f64>,
    pub evaporation_coefficient: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ApplicationAdapterV1 {
    pub adapter_key: String,
    pub formulation_id: String,
    pub geometry_sha256: String,
    pub spray_setup_sha256: String,
    pub mixed_mass_g: f64,
    pub critical_clock_min: f64,
    pub critical_clock_pi90_lower_min: f64,
    pub critical_clock_pi90_upper_min: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeApplicabilityDomainV1 {
    pub formulation_hashes: BTreeMap<String, String>,
    pub geometry_sha256: Vec<String>,
    pub spray_setup_sha256: Vec<String>,
    pub mixed_masses_g: Vec<f64>,
    pub chemistry_family: String,
    pub commercial_grade_scope: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeBenchmarkMetricsV1 {
    pub holdout_factor_1_5_accuracy: f64,
    pub best_baseline_factor_1_5_accuracy: f64,
    pub absolute_lift: f64,
    pub paired_block_bootstrap_lower_95: f64,
    pub median_absolute_timing_error_h: f64,
    pub proper_interval_score_h: f64,
    pub prediction_interval_90_coverage: f64,
    pub viscosity_proxy_log_error: f64,
    pub baseline_viscosity_proxy_log_error: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeGateStatusV1 {
    pub valid_independent_runs_36: bool,
    pub untouched_73f_holdouts_12: bool,
    pub zero_split_leakage: bool,
    pub holdout_factor_1_5_at_least_0_80: bool,
    pub lift_at_least_0_10: bool,
    pub paired_bootstrap_lower_positive: bool,
    pub interval_coverage_0_85_to_0_95: bool,
    pub parameters_finite_identifiable_bounded: bool,
    pub viscosity_proxy_non_worse: bool,
    pub replay_equal_1_2_8_workers: bool,
    pub hostile_null_suite_passed: bool,
    pub independent_review_passed: bool,
}

impl PotLifeGateStatusV1 {
    pub fn locked_gate_passed(&self) -> bool {
        self.valid_independent_runs_36
            && self.untouched_73f_holdouts_12
            && self.zero_split_leakage
            && self.holdout_factor_1_5_at_least_0_80
            && self.lift_at_least_0_10
            && self.paired_bootstrap_lower_positive
            && self.interval_coverage_0_85_to_0_95
            && self.parameters_finite_identifiable_bounded
            && self.viscosity_proxy_non_worse
            && self.replay_equal_1_2_8_workers
            && self.hostile_null_suite_passed
    }

    pub fn authorizes_non_null_shadow_prediction(&self) -> bool {
        self.locked_gate_passed() && self.independent_review_passed
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct BaselineResultV1 {
    pub baseline: String,
    pub factor_1_5_accuracy: f64,
    pub median_absolute_timing_error_h: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct HostileNullResultV1 {
    pub null_name: String,
    pub factor_1_5_accuracy: f64,
    pub rejected_as_valid_method: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeModelArtifactV1 {
    pub schema: String,
    pub track_id: String,
    pub model_id: String,
    pub authority: ResearchAuthorityV1,
    pub protocol_sha256: String,
    pub locked_benchmark_sha256: String,
    pub source_ledger_sha256: String,
    pub training_run_hashes: BTreeMap<String, String>,
    pub sealed_holdout_run_hashes: BTreeMap<String, String>,
    pub parameters: ReducedPhysicalParametersV1,
    pub parameter_profile_intervals: BTreeMap<String, ParameterIntervalV1>,
    pub parameters_identifiable: bool,
    pub application_adapters: BTreeMap<String, ApplicationAdapterV1>,
    pub applicability_domain: PotLifeApplicabilityDomainV1,
    pub benchmark_metrics: PotLifeBenchmarkMetricsV1,
    pub baselines: Vec<BaselineResultV1>,
    pub hostile_nulls: Vec<HostileNullResultV1>,
    pub gate_status: PotLifeGateStatusV1,
    pub replay_hashes: BTreeMap<String, String>,
    pub leave_one_formulation_out_diagnostic: BTreeMap<String, f64>,
    pub fto_status: String,
}

impl PotLifeModelArtifactV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_schema(&self.schema, POT_LIFE_MODEL_ARTIFACT_SCHEMA)?;
        require_track(&self.track_id)?;
        require_text("model_id", &self.model_id)?;
        for (field, hash) in [
            ("protocol_sha256", self.protocol_sha256.as_str()),
            (
                "locked_benchmark_sha256",
                self.locked_benchmark_sha256.as_str(),
            ),
            ("source_ledger_sha256", self.source_ledger_sha256.as_str()),
        ] {
            require_hash(field, hash)?;
        }
        require_hash_map("training_run_hashes", &self.training_run_hashes, true)?;
        require_hash_map(
            "sealed_holdout_run_hashes",
            &self.sealed_holdout_run_hashes,
            true,
        )?;
        if self
            .training_run_hashes
            .keys()
            .any(|id| self.sealed_holdout_run_hashes.contains_key(id))
        {
            return Err(PotLifeError::Model("run in both fit and holdout sets"));
        }
        let parameters = &self.parameters;
        if [
            parameters.activation_energy_j_mol,
            parameters.reference_temperature_k,
            parameters.gel_clock_min,
            parameters.chemorheology_exponent,
        ]
        .iter()
        .any(|value| !value.is_finite() || *value <= 0.0)
            || parameters
                .cure_scale_by_formulation
                .values()
                .any(|value| !value.is_finite() || *value < 0.0)
        {
            return Err(PotLifeError::Model("non-finite reduced parameter"));
        }
        if [
            parameters.primary_amine_rate_constant,
            parameters.secondary_amine_rate_constant,
            parameters.hydroxyl_autocatalysis_constant,
            parameters.etherification_rate_constant,
            parameters.diffusion_vitrification_parameter,
            parameters.heat_transfer_coefficient,
            parameters.evaporation_coefficient,
        ]
        .iter()
        .any(Option::is_some)
        {
            return Err(PotLifeError::UnidentifiableParameter);
        }
        if self.parameter_profile_intervals.is_empty()
            || self
                .parameter_profile_intervals
                .values()
                .any(|interval| !interval.validate())
        {
            return Err(PotLifeError::Model("invalid profile interval"));
        }
        if self.application_adapters.is_empty()
            || self.application_adapters.iter().any(|(key, row)| {
                key != &row.adapter_key
                    || !is_sha256(&row.geometry_sha256)
                    || !is_sha256(&row.spray_setup_sha256)
                    || !row.mixed_mass_g.is_finite()
                    || row.mixed_mass_g <= 0.0
                    || [
                        row.critical_clock_min,
                        row.critical_clock_pi90_lower_min,
                        row.critical_clock_pi90_upper_min,
                    ]
                    .iter()
                    .any(|value| !value.is_finite() || *value <= 0.0)
                    || row.critical_clock_pi90_lower_min > row.critical_clock_min
                    || row.critical_clock_min > row.critical_clock_pi90_upper_min
            })
        {
            return Err(PotLifeError::Model("invalid application adapter"));
        }
        require_hash_map(
            "applicability_domain.formulation_hashes",
            &self.applicability_domain.formulation_hashes,
            true,
        )?;
        if self.applicability_domain.geometry_sha256.is_empty()
            || self.applicability_domain.spray_setup_sha256.is_empty()
            || self
                .applicability_domain
                .geometry_sha256
                .iter()
                .chain(&self.applicability_domain.spray_setup_sha256)
                .any(|hash| !is_sha256(hash))
            || self.applicability_domain.mixed_masses_g.is_empty()
            || self
                .applicability_domain
                .mixed_masses_g
                .iter()
                .any(|mass| !mass.is_finite() || *mass <= 0.0)
            || self.applicability_domain.chemistry_family
                != "SOLVENT_BORNE_DGEBA_POLYAMIDE_MARINE_PRIMER"
        {
            return Err(PotLifeError::Model("invalid applicability domain"));
        }
        for value in [
            self.benchmark_metrics.holdout_factor_1_5_accuracy,
            self.benchmark_metrics.best_baseline_factor_1_5_accuracy,
            self.benchmark_metrics.prediction_interval_90_coverage,
        ] {
            if !value.is_finite() || !(0.0..=1.0).contains(&value) {
                return Err(PotLifeError::Model("invalid benchmark metric"));
            }
        }
        if self
            .replay_hashes
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>()
            != ["1", "2", "8"].into_iter().collect()
            || self.replay_hashes.values().any(|hash| !is_sha256(hash))
        {
            return Err(PotLifeError::Model("missing deterministic replay hash"));
        }
        if self.fto_status != "FTO NOT PERFORMED" {
            return Err(PotLifeError::Model("FTO status"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("model artifact serializes"))
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
    pub model_artifact: Value,
    pub metrics: PotLifeBenchmarkMetricsV1,
    pub gate_status: PotLifeGateStatusV1,
    pub verifier_site_factor_1_5_accuracy: BTreeMap<String, f64>,
    pub passed: bool,
}

impl BenchmarkReceiptV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_schema(&self.schema, BENCHMARK_RECEIPT_SCHEMA)?;
        if self.module_id != MODULE_ID {
            return Err(PotLifeError::Schema {
                actual: self.module_id.clone(),
                expected: MODULE_ID,
            });
        }
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
        let model_hash = stable_hash(&self.model_artifact);
        if model_hash != self.model_artifact_sha256
            || self
                .model_artifact
                .get("locked_benchmark_sha256")
                .or_else(|| {
                    self.model_artifact
                        .get("parent_hashes")
                        .and_then(|parents| parents.get("benchmark_lock"))
                })
                .and_then(Value::as_str)
                != Some(self.benchmark_lock_sha256.as_str())
            || self
                .verifier_site_factor_1_5_accuracy
                .values()
                .any(|value| !value.is_finite() || !(0.0..=1.0).contains(value))
        {
            return Err(PotLifeError::Model("benchmark receipt binding"));
        }
        let verifier_passed = self.verifier_site_factor_1_5_accuracy.len() == 2
            && self
                .verifier_site_factor_1_5_accuracy
                .values()
                .all(|accuracy| *accuracy >= 0.80);
        let expected = self.gate_status.locked_gate_passed()
            && self.gate_status.independent_review_passed
            && verifier_passed;
        if self.passed != expected {
            return Err(PotLifeError::Authority);
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        stable_hash(&serde_json::to_value(self).expect("receipt serializes"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct EvidenceReviewReceiptV1 {
    pub schema: String,
    pub module_id: String,
    pub review_id: String,
    pub model_artifact_sha256: String,
    pub benchmark_receipt_sha256: String,
    pub reviewer_independent: bool,
    pub applicability_limits_accepted: bool,
    pub prohibited_claims_accepted: bool,
    pub signed_review_receipt_sha256: String,
}

impl EvidenceReviewReceiptV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_schema(&self.schema, EVIDENCE_REVIEW_RECEIPT_SCHEMA)?;
        if self.module_id != MODULE_ID {
            return Err(PotLifeError::Schema {
                actual: self.module_id.clone(),
                expected: MODULE_ID,
            });
        }
        require_text("review_id", &self.review_id)?;
        for (field, hash) in [
            ("model_artifact_sha256", self.model_artifact_sha256.as_str()),
            (
                "benchmark_receipt_sha256",
                self.benchmark_receipt_sha256.as_str(),
            ),
            (
                "signed_review_receipt_sha256",
                self.signed_review_receipt_sha256.as_str(),
            ),
        ] {
            require_hash(field, hash)?;
        }
        if !self.reviewer_independent
            || !self.applicability_limits_accepted
            || !self.prohibited_claims_accepted
        {
            return Err(PotLifeError::Authority);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifePredictionV1 {
    pub schema: String,
    pub track_id: String,
    pub prediction_id: String,
    pub model_artifact_sha256: String,
    pub endpoint: PotLifeEndpointV1,
    pub authority: ResearchAuthorityV1,
    pub formulation_id: String,
    pub formulation_hash: String,
    pub geometry_sha256: String,
    pub spray_setup_sha256: String,
    pub mixed_mass_g: f64,
    pub in_applicability_domain: bool,
    pub locked_gate_passed: bool,
    pub independent_review_passed: bool,
    pub candidate_pot_life_prediction_h: Option<f64>,
    pub prediction_interval_90_h: Option<[f64; 2]>,
    pub viscosity_proxy: Option<ViscosityProxyV1>,
    #[serde(default)]
    pub abstention_reasons: Vec<String>,
}

impl PotLifePredictionV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_schema(&self.schema, POT_LIFE_PREDICTION_SCHEMA)?;
        require_track(&self.track_id)?;
        require_text("prediction_id", &self.prediction_id)?;
        require_text("formulation_id", &self.formulation_id)?;
        for (field, hash) in [
            ("model_artifact_sha256", self.model_artifact_sha256.as_str()),
            ("formulation_hash", self.formulation_hash.as_str()),
            ("geometry_sha256", self.geometry_sha256.as_str()),
            ("spray_setup_sha256", self.spray_setup_sha256.as_str()),
        ] {
            require_hash(field, hash)?;
        }
        let authorized = self.in_applicability_domain
            && self.locked_gate_passed
            && self.independent_review_passed;
        if !self.mixed_mass_g.is_finite() || self.mixed_mass_g <= 0.0 {
            return Err(PotLifeError::Range("mixed_mass_g"));
        }
        if self.candidate_pot_life_prediction_h.is_some() != authorized
            || self.prediction_interval_90_h.is_some() != authorized
        {
            return Err(PotLifeError::Authority);
        }
        if let (Some(value), Some(interval)) = (
            self.candidate_pot_life_prediction_h,
            self.prediction_interval_90_h,
        ) {
            if !value.is_finite()
                || value <= 0.0
                || interval
                    .iter()
                    .any(|bound| !bound.is_finite() || *bound <= 0.0)
                || interval[0] > value
                || value > interval[1]
            {
                return Err(PotLifeError::Range("prediction interval"));
            }
        }
        if !authorized && self.abstention_reasons.is_empty() {
            return Err(PotLifeError::Empty("abstention_reasons"));
        }
        Ok(())
    }
}

fn validate_temperature_series(series: &[TemperatureObservationV1]) -> Result<(), PotLifeError> {
    validate_times(
        "temperature_series",
        &series.iter().map(|row| row.elapsed_min).collect::<Vec<_>>(),
        true,
    )?;
    if series.iter().any(|row| {
        !row.material_temperature_c.is_finite()
            || !row.ambient_temperature_c.is_finite()
            || !row.relative_humidity_pct.is_finite()
            || !(0.0..=100.0).contains(&row.relative_humidity_pct)
            || row.material_temperature_c <= -273.15
            || row.ambient_temperature_c <= -273.15
    }) {
        return Err(PotLifeError::Range("temperature_series"));
    }
    Ok(())
}

fn validate_stormer_series(
    series: &[StormerObservationV1],
    calibration_ids: &BTreeMap<String, String>,
) -> Result<(), PotLifeError> {
    validate_times(
        "stormer_series",
        &series.iter().map(|row| row.elapsed_min).collect::<Vec<_>>(),
        true,
    )?;
    if series.len() < 5
        || series.iter().any(|row| {
            !row.raw_response_ku.is_finite()
                || row.raw_response_ku <= 0.0
                || !row.raw_load_g.is_finite()
                || row.raw_load_g <= 0.0
                || row
                    .equivalent_viscosity_mpa_s
                    .is_some_and(|value| !value.is_finite() || value <= 0.0)
        })
    {
        return Err(PotLifeError::Range("stormer_series"));
    }
    for (index, expected) in [0.0, 10.0, 20.0, 30.0].iter().enumerate() {
        if series
            .get(index)
            .is_none_or(|row| (row.elapsed_min - expected).abs() > 1e-9)
        {
            return Err(PotLifeError::Schedule("Stormer initial cadence"));
        }
    }
    let mapped = series[0].equivalent_viscosity_mpa_s.is_some();
    if series.iter().any(|row| {
        row.equivalent_viscosity_mpa_s.is_some() != mapped
            || row.certified_mapping_id.is_some() != mapped
    }) {
        return Err(PotLifeError::Schedule("mixed Stormer mapping basis"));
    }
    if mapped {
        let mapping = series[0]
            .certified_mapping_id
            .as_deref()
            .ok_or(PotLifeError::Empty("certified_mapping_id"))?;
        if series
            .iter()
            .any(|row| row.certified_mapping_id.as_deref() != Some(mapping))
            || calibration_ids.get("stormer_mapping").map(String::as_str) != Some(mapping)
        {
            return Err(PotLifeError::Schedule("certified Stormer mapping"));
        }
    }
    let trigger = if mapped {
        let initial = series[0]
            .equivalent_viscosity_mpa_s
            .expect("mapped series checked");
        series.iter().position(|row| {
            row.equivalent_viscosity_mpa_s
                .is_some_and(|value| value >= 1.5 * initial)
        })
    } else {
        None
    };
    for index in 4..series.len() {
        let expected_gap = if trigger.is_some_and(|trigger| index > trigger) {
            5.0
        } else {
            15.0
        };
        if (series[index].elapsed_min - series[index - 1].elapsed_min - expected_gap).abs() > 1e-9 {
            return Err(PotLifeError::Schedule("Stormer post-30-minute cadence"));
        }
    }
    Ok(())
}

fn validate_spray_series(
    series: &[SprayCheckV1],
    trigger_time_min: Option<f64>,
) -> Result<(), PotLifeError> {
    validate_times(
        "spray_checks",
        &series.iter().map(|row| row.elapsed_min).collect::<Vec<_>>(),
        true,
    )?;
    if series.len() < 2 {
        return Err(PotLifeError::EndpointInterval);
    }
    for row in series {
        if row.pass != row.checklist_passes()
            || (row.pass && row.first_failed_property.is_some())
            || (!row.pass && row.first_failed_property.is_none())
        {
            return Err(PotLifeError::SprayDeclaration);
        }
    }
    for pair in series.windows(2) {
        let expected_gap = if trigger_time_min.is_some_and(|trigger| pair[0].elapsed_min >= trigger)
        {
            10.0
        } else {
            30.0
        };
        if (pair[1].elapsed_min - pair[0].elapsed_min - expected_gap).abs() > 1e-9 {
            return Err(PotLifeError::Schedule("spray checklist cadence"));
        }
    }
    if series
        .iter()
        .position(|row| !row.pass)
        .is_some_and(|index| series[index + 1..].iter().any(|row| row.pass))
    {
        return Err(PotLifeError::EndpointInterval);
    }
    Ok(())
}

fn validate_times(
    field: &'static str,
    times: &[f64],
    require_zero: bool,
) -> Result<(), PotLifeError> {
    if times.is_empty()
        || times.iter().any(|time| !time.is_finite() || *time < 0.0)
        || (require_zero && times[0].abs() > 1e-9)
        || times.windows(2).any(|pair| pair[1] <= pair[0])
    {
        return Err(PotLifeError::TimeOrder(field));
    }
    Ok(())
}

pub(crate) fn require_schema(actual: &str, expected: &'static str) -> Result<(), PotLifeError> {
    if actual == expected {
        Ok(())
    } else {
        Err(PotLifeError::Schema {
            actual: actual.into(),
            expected,
        })
    }
}

pub(crate) fn require_track(track: &str) -> Result<(), PotLifeError> {
    if track == POT_LIFE_TRACK_ID {
        Ok(())
    } else {
        Err(PotLifeError::Track)
    }
}

pub(crate) fn require_text(field: &'static str, value: &str) -> Result<(), PotLifeError> {
    if value.trim().is_empty() {
        Err(PotLifeError::Empty(field))
    } else {
        Ok(())
    }
}

pub(crate) fn require_hash(field: &'static str, value: &str) -> Result<(), PotLifeError> {
    if is_sha256(value) {
        Ok(())
    } else {
        Err(PotLifeError::Hash(field))
    }
}

pub(crate) fn require_hash_map(
    field: &'static str,
    values: &BTreeMap<String, String>,
    require_nonempty: bool,
) -> Result<(), PotLifeError> {
    if (require_nonempty && values.is_empty())
        || values
            .iter()
            .any(|(key, hash)| key.trim().is_empty() || !is_sha256(hash))
    {
        Err(PotLifeError::Hash(field))
    } else {
        Ok(())
    }
}

pub fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

pub fn contract_hash<T: Serialize>(value: &T) -> Result<String, PotLifeError> {
    let value =
        serde_json::to_value(value).map_err(|error| PotLifeError::Json(error.to_string()))?;
    Ok(stable_hash(&value))
}

pub fn strict_from_value<T>(value: Value) -> Result<T, PotLifeError>
where
    T: for<'de> Deserialize<'de>,
{
    serde_json::from_value(value).map_err(|error| PotLifeError::Json(error.to_string()))
}
