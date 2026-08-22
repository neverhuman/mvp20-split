use crate::{
    contract_hash, require_hash, require_hash_map, require_schema, require_text, require_track,
    AirlessSpraySetupV1, ContainerGeometryV1, PotLifeError, PotLifeRunSplitV1, PotLifeRunV1,
    POT_LIFE_BENCHMARK_LOCK_SCHEMA, POT_LIFE_PROTOCOL_SCHEMA, POT_LIFE_TRACK_ID,
};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub const PROTOCOL_QUALIFICATION_SCHEMA: &str = "amphora.pot-life-scale-qualification.v1";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeScaleQualificationV1 {
    pub schema: String,
    pub qualification_id: String,
    pub performed_with_non_reactive_fluid: bool,
    pub qualification_fluid_sha256: String,
    pub sprayer_dead_volume_demand_g: f64,
    pub test_card_demand_g: f64,
    pub maximum_facility_approved_fill_g: f64,
    pub primary_geometry: ContainerGeometryV1,
    pub second_geometry: ContainerGeometryV1,
    pub distinct_geometry_confirmed_safe: bool,
    pub airless_spray_setup: AirlessSpraySetupV1,
    pub calibration_ids: BTreeMap<String, String>,
}

impl PotLifeScaleQualificationV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_schema(&self.schema, PROTOCOL_QUALIFICATION_SCHEMA)?;
        require_text("qualification_id", &self.qualification_id)?;
        require_hash(
            "qualification_fluid_sha256",
            &self.qualification_fluid_sha256,
        )?;
        self.primary_geometry.validate()?;
        self.second_geometry.validate()?;
        self.airless_spray_setup.validate()?;
        if !self.performed_with_non_reactive_fluid
            || !self.distinct_geometry_confirmed_safe
            || self.primary_geometry.identity_hash() == self.second_geometry.identity_hash()
            || [
                self.sprayer_dead_volume_demand_g,
                self.test_card_demand_g,
                self.maximum_facility_approved_fill_g,
            ]
            .iter()
            .any(|value| !value.is_finite() || *value <= 0.0)
        {
            return Err(PotLifeError::Range("scale qualification"));
        }
        let primary = self.primary_mixed_mass_g();
        if self.maximum_facility_approved_fill_g <= primary || self.second_mixed_mass_g() <= primary
        {
            return Err(PotLifeError::Range("distinct safe second fill"));
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
        Ok(())
    }

    pub fn primary_mixed_mass_g(&self) -> f64 {
        1.2 * (self.sprayer_dead_volume_demand_g + self.test_card_demand_g)
    }

    pub fn second_mixed_mass_g(&self) -> f64 {
        (2.0 * self.primary_mixed_mass_g()).min(self.maximum_facility_approved_fill_g)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeProtocolLocksV1 {
    pub mix_ratio_by_volume: String,
    pub induction_time_min: f64,
    pub mixing_method: String,
    pub no_thinning: bool,
    pub target_relative_humidity_pct: f64,
    pub relative_humidity_tolerance_pct: f64,
    pub material_temperature_recording: String,
    pub pot_life_clock_start: String,
    pub stormer_schedule: String,
    pub spray_check_schedule: String,
    pub application_endpoint: String,
    pub airless_spray_setup: AirlessSpraySetupV1,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PlannedPotLifeRunV1 {
    pub run_id: String,
    pub formulation_id: String,
    pub target_temperature_f: u16,
    pub replicate: u8,
    pub geometry_id: String,
    pub geometry_sha256: String,
    pub mixed_mass_g: f64,
    pub split: PotLifeRunSplitV1,
    pub sealed_until_locked_evaluation: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeProtocolV1 {
    pub schema: String,
    pub track_id: String,
    pub protocol_id: String,
    pub generated_on: String,
    pub scale_qualification_sha256: String,
    pub source_ledger_sha256: String,
    pub primary_mixed_mass_g: f64,
    pub second_mixed_mass_g: f64,
    pub primary_geometry: ContainerGeometryV1,
    pub second_geometry: ContainerGeometryV1,
    pub locks: PotLifeProtocolLocksV1,
    pub planned_runs: Vec<PlannedPotLifeRunV1>,
    pub reactive_safety_authority: String,
}

impl PotLifeProtocolV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_schema(&self.schema, POT_LIFE_PROTOCOL_SCHEMA)?;
        require_track(&self.track_id)?;
        require_text("protocol_id", &self.protocol_id)?;
        require_text("generated_on", &self.generated_on)?;
        require_hash(
            "scale_qualification_sha256",
            &self.scale_qualification_sha256,
        )?;
        require_hash("source_ledger_sha256", &self.source_ledger_sha256)?;
        self.primary_geometry.validate()?;
        self.second_geometry.validate()?;
        self.locks.airless_spray_setup.validate()?;
        if self.primary_geometry.identity_hash() == self.second_geometry.identity_hash()
            || !self.primary_mixed_mass_g.is_finite()
            || !self.second_mixed_mass_g.is_finite()
            || self.primary_mixed_mass_g <= 0.0
            || self.second_mixed_mass_g <= self.primary_mixed_mass_g
            || self.locks.mix_ratio_by_volume != "1:1"
            || (self.locks.induction_time_min - 30.0).abs() > 1e-9
            || !self.locks.no_thinning
            || self.locks.pot_life_clock_start != "INITIAL_MIXING"
            || self.locks.application_endpoint != "AIRLESS_SPRAY_FIRST_PROPERTY_FAILURE"
        {
            return Err(PotLifeError::Range("protocol locks"));
        }
        require_text("mixing_method", &self.locks.mixing_method)?;
        require_text(
            "material_temperature_recording",
            &self.locks.material_temperature_recording,
        )?;
        if self.reactive_safety_authority
            != "TRAINED_PERSONNEL_UNDER_EXISTING_FACILITY_PROCEDURES_ONLY"
        {
            return Err(PotLifeError::Range("reactive_safety_authority"));
        }
        validate_run_plan(&self.planned_runs, self)?;
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        contract_hash(self).expect("protocol serializes")
    }
}

pub fn generate_protocol(
    qualification: &PotLifeScaleQualificationV1,
    generated_on: &str,
    source_ledger_sha256: &str,
    mixing_method: &str,
) -> Result<PotLifeProtocolV1, PotLifeError> {
    qualification.validate()?;
    require_text("generated_on", generated_on)?;
    require_hash("source_ledger_sha256", source_ledger_sha256)?;
    require_text("mixing_method", mixing_method)?;
    let qualification_hash = contract_hash(qualification)?;
    let mut planned_runs = Vec::with_capacity(36);
    for formulation in ["M00097", "M00101", "M00109"] {
        for temperature in [65_u16, 73, 95] {
            for replicate in 1_u8..=3 {
                planned_runs.push(planned_run(
                    formulation,
                    temperature,
                    replicate,
                    &qualification.primary_geometry,
                    qualification.primary_mixed_mass_g(),
                    "G1",
                ));
            }
        }
    }
    for temperature in [65_u16, 73, 95] {
        for replicate in 1_u8..=3 {
            planned_runs.push(planned_run(
                "M00097",
                temperature,
                replicate,
                &qualification.second_geometry,
                qualification.second_mixed_mass_g(),
                "G2",
            ));
        }
    }
    planned_runs.sort_by(|left, right| left.run_id.cmp(&right.run_id));
    let protocol_id = format!("pot-life-protocol-{}", &qualification_hash[..16]);
    let protocol = PotLifeProtocolV1 {
        schema: POT_LIFE_PROTOCOL_SCHEMA.into(),
        track_id: POT_LIFE_TRACK_ID.into(),
        protocol_id,
        generated_on: generated_on.into(),
        scale_qualification_sha256: qualification_hash,
        source_ledger_sha256: source_ledger_sha256.into(),
        primary_mixed_mass_g: qualification.primary_mixed_mass_g(),
        second_mixed_mass_g: qualification.second_mixed_mass_g(),
        primary_geometry: qualification.primary_geometry.clone(),
        second_geometry: qualification.second_geometry.clone(),
        locks: PotLifeProtocolLocksV1 {
            mix_ratio_by_volume: "1:1".into(),
            induction_time_min: 30.0,
            mixing_method: mixing_method.into(),
            no_thinning: true,
            target_relative_humidity_pct: 50.0,
            relative_humidity_tolerance_pct: 5.0,
            material_temperature_recording: "CONTINUOUS_LOGGER_SERIES".into(),
            pot_life_clock_start: "INITIAL_MIXING".into(),
            stormer_schedule: "0,10,20,30_MIN_THEN_15_MIN;_5_MIN_AFTER_EQUIVALENT_VISCOSITY_1.5X"
                .into(),
            spray_check_schedule: "30_MIN;_10_MIN_AFTER_EQUIVALENT_VISCOSITY_1.5X".into(),
            application_endpoint: "AIRLESS_SPRAY_FIRST_PROPERTY_FAILURE".into(),
            airless_spray_setup: qualification.airless_spray_setup.clone(),
        },
        planned_runs,
        reactive_safety_authority: "TRAINED_PERSONNEL_UNDER_EXISTING_FACILITY_PROCEDURES_ONLY"
            .into(),
    };
    protocol.validate()?;
    Ok(protocol)
}

fn planned_run(
    formulation_id: &str,
    temperature: u16,
    replicate: u8,
    geometry: &ContainerGeometryV1,
    mixed_mass_g: f64,
    geometry_label: &str,
) -> PlannedPotLifeRunV1 {
    PlannedPotLifeRunV1 {
        run_id: format!("PL-{formulation_id}-{geometry_label}-{temperature}F-R{replicate}"),
        formulation_id: formulation_id.into(),
        target_temperature_f: temperature,
        replicate,
        geometry_id: geometry.geometry_id.clone(),
        geometry_sha256: geometry.identity_hash(),
        mixed_mass_g,
        split: if temperature == 73 {
            PotLifeRunSplitV1::SealedHoldout
        } else {
            PotLifeRunSplitV1::Fit
        },
        sealed_until_locked_evaluation: temperature == 73,
    }
}

fn validate_run_plan(
    rows: &[PlannedPotLifeRunV1],
    protocol: &PotLifeProtocolV1,
) -> Result<(), PotLifeError> {
    if rows.len() != 36 {
        return Err(PotLifeError::Range("planned_runs must contain 36 rows"));
    }
    let mut ids = BTreeSet::new();
    let mut design = BTreeSet::new();
    let holdouts = rows
        .iter()
        .filter(|row| row.split == PotLifeRunSplitV1::SealedHoldout)
        .count();
    for row in rows {
        if !ids.insert(&row.run_id)
            || !design.insert((
                row.formulation_id.as_str(),
                row.target_temperature_f,
                row.replicate,
                row.geometry_id.as_str(),
            ))
            || !crate::is_sha256(&row.geometry_sha256)
            || !row.mixed_mass_g.is_finite()
            || row.mixed_mass_g <= 0.0
            || (row.target_temperature_f == 73) != row.sealed_until_locked_evaluation
        {
            return Err(PotLifeError::Duplicate("planned run identity"));
        }
        let is_second = row.geometry_sha256 == protocol.second_geometry.identity_hash();
        if is_second && row.formulation_id != "M00097" {
            return Err(PotLifeError::Range("second geometry formulation"));
        }
    }
    if holdouts != 12 {
        return Err(PotLifeError::Range("sealed holdout count"));
    }
    Ok(())
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SplitLeakageAuditV1 {
    pub run_ids_disjoint: bool,
    pub independent_mix_ids_disjoint: bool,
    pub batch_ids_disjoint: bool,
    pub run_days_disjoint: bool,
    pub timepoint_identities_disjoint: bool,
    pub holdout_endpoint_statistics_excluded_from_fit: bool,
}

impl SplitLeakageAuditV1 {
    pub fn passed(&self) -> bool {
        self.run_ids_disjoint
            && self.independent_mix_ids_disjoint
            && self.batch_ids_disjoint
            && self.run_days_disjoint
            && self.timepoint_identities_disjoint
            && self.holdout_endpoint_statistics_excluded_from_fit
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeBenchmarkThresholdsV1 {
    pub minimum_valid_runs: usize,
    pub required_sealed_holdouts: usize,
    pub factor_1_5_accuracy_min: f64,
    pub absolute_lift_min: f64,
    pub paired_bootstrap_lower_min: f64,
    pub interval_coverage_min: f64,
    pub interval_coverage_max: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PotLifeBenchmarkLockV1 {
    pub schema: String,
    pub track_id: String,
    pub benchmark_id: String,
    pub protocol_sha256: String,
    pub source_ledger_sha256: String,
    pub run_hashes: BTreeMap<String, String>,
    pub fit_run_ids: Vec<String>,
    pub sealed_holdout_run_ids: Vec<String>,
    pub leakage_audit: SplitLeakageAuditV1,
    pub baselines: Vec<String>,
    pub hostile_nulls: Vec<String>,
    pub primary_metric: String,
    pub interval_error_rule: String,
    pub bootstrap_method: String,
    pub thresholds: PotLifeBenchmarkThresholdsV1,
    pub endpoint: String,
}

impl PotLifeBenchmarkLockV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_schema(&self.schema, POT_LIFE_BENCHMARK_LOCK_SCHEMA)?;
        require_track(&self.track_id)?;
        require_text("benchmark_id", &self.benchmark_id)?;
        require_hash("protocol_sha256", &self.protocol_sha256)?;
        require_hash("source_ledger_sha256", &self.source_ledger_sha256)?;
        require_hash_map("run_hashes", &self.run_hashes, true)?;
        if self.run_hashes.len() != 36
            || self.fit_run_ids.len() != 24
            || self.sealed_holdout_run_ids.len() != 12
            || !self.leakage_audit.passed()
            || self.endpoint != "AIRLESS_SPRAY_FIRST_PROPERTY_FAILURE"
            || self.primary_metric != "INTERVAL_CENSORED_LOG_TIME_DISTANCE"
        {
            return Err(PotLifeError::Range("benchmark lock"));
        }
        let fit: BTreeSet<_> = self.fit_run_ids.iter().collect();
        let holdout: BTreeSet<_> = self.sealed_holdout_run_ids.iter().collect();
        if fit.len() != self.fit_run_ids.len()
            || holdout.len() != self.sealed_holdout_run_ids.len()
            || !fit.is_disjoint(&holdout)
            || fit
                .union(&holdout)
                .any(|run_id| !self.run_hashes.contains_key(*run_id))
        {
            return Err(PotLifeError::Duplicate("benchmark split identity"));
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        contract_hash(self).expect("benchmark lock serializes")
    }
}

pub fn lock_benchmark(
    protocol: &PotLifeProtocolV1,
    runs: &[PotLifeRunV1],
) -> Result<PotLifeBenchmarkLockV1, PotLifeError> {
    protocol.validate()?;
    if runs.len() != 36 {
        return Err(PotLifeError::Range("valid independent run count"));
    }
    let protocol_hash = protocol.identity_hash();
    let expected: BTreeMap<_, _> = protocol
        .planned_runs
        .iter()
        .map(|row| (row.run_id.as_str(), row))
        .collect();
    let mut run_hashes = BTreeMap::new();
    let mut fit_run_ids = Vec::new();
    let mut holdout_run_ids = Vec::new();
    for run in runs {
        run.validate()?;
        let plan = expected
            .get(run.run_id.as_str())
            .ok_or(PotLifeError::Range("run absent from protocol"))?;
        if run.protocol_sha256 != protocol_hash
            || run.formulation_id != plan.formulation_id
            || run.target_temperature_f != plan.target_temperature_f
            || run.replicate != plan.replicate
            || run.geometry_hash() != plan.geometry_sha256
            || (run.mixed_mass_g - plan.mixed_mass_g).abs() > 1e-6
            || run.spray_setup != protocol.locks.airless_spray_setup
        {
            return Err(PotLifeError::Range("run does not match locked protocol"));
        }
        if run_hashes
            .insert(run.run_id.clone(), run.identity_hash())
            .is_some()
        {
            return Err(PotLifeError::Duplicate("run_id"));
        }
        match run.split {
            PotLifeRunSplitV1::Fit => fit_run_ids.push(run.run_id.clone()),
            PotLifeRunSplitV1::SealedHoldout => holdout_run_ids.push(run.run_id.clone()),
        }
    }
    if run_hashes
        .keys()
        .map(String::as_str)
        .collect::<BTreeSet<_>>()
        != expected.keys().copied().collect::<BTreeSet<_>>()
    {
        return Err(PotLifeError::Range("protocol run completeness"));
    }
    fit_run_ids.sort();
    holdout_run_ids.sort();
    let leakage_audit = split_leakage_audit(runs);
    if !leakage_audit.passed() {
        return Err(PotLifeError::Range("split leakage"));
    }
    let benchmark_id = format!("pot-life-locked-{}", &contract_hash(&run_hashes)?[..16]);
    let lock = PotLifeBenchmarkLockV1 {
        schema: POT_LIFE_BENCHMARK_LOCK_SCHEMA.into(),
        track_id: POT_LIFE_TRACK_ID.into(),
        benchmark_id,
        protocol_sha256: protocol_hash,
        source_ledger_sha256: protocol.source_ledger_sha256.clone(),
        run_hashes,
        fit_run_ids,
        sealed_holdout_run_ids: holdout_run_ids,
        leakage_audit,
        baselines: vec![
            "OVERALL_MEDIAN".into(),
            "FORMULATION_MEDIAN".into(),
            "DIRECT_ARRHENIUS_TIME_TO_EVENT".into(),
            "MONOTONE_TIME_TEMPERATURE_SPLINE".into(),
            "CURRENT_NULL_IMPLEMENTATION".into(),
        ],
        hostile_nulls: vec![
            "SHUFFLED_FORMULATION_LABELS".into(),
            "TIME_REVERSAL".into(),
            "AMBIENT_FOR_MATERIAL_TEMPERATURE".into(),
            "ERASED_GEOMETRY".into(),
            "LEAKED_REPLICATES".into(),
            "GEL_TIME_RELABELLING".into(),
        ],
        primary_metric: "INTERVAL_CENSORED_LOG_TIME_DISTANCE".into(),
        interval_error_rule: "ZERO_INSIDE_LAST_PASS_FIRST_FAIL;_LOG_DISTANCE_OUTSIDE".into(),
        bootstrap_method: "PAIRED_BLOCK_BOOTSTRAP_BY_FORMULATION_GEOMETRY_SEED_9514".into(),
        thresholds: PotLifeBenchmarkThresholdsV1 {
            minimum_valid_runs: 36,
            required_sealed_holdouts: 12,
            factor_1_5_accuracy_min: 0.80,
            absolute_lift_min: 0.10,
            paired_bootstrap_lower_min: 0.0,
            interval_coverage_min: 0.85,
            interval_coverage_max: 0.95,
        },
        endpoint: "AIRLESS_SPRAY_FIRST_PROPERTY_FAILURE".into(),
    };
    lock.validate()?;
    Ok(lock)
}

pub fn split_leakage_audit(runs: &[PotLifeRunV1]) -> SplitLeakageAuditV1 {
    fn disjoint_by<F>(runs: &[PotLifeRunV1], field: F) -> bool
    where
        F: Fn(&PotLifeRunV1) -> &str,
    {
        let fit: BTreeSet<_> = runs
            .iter()
            .filter(|run| run.split == PotLifeRunSplitV1::Fit)
            .map(&field)
            .collect();
        let holdout: BTreeSet<_> = runs
            .iter()
            .filter(|run| run.split == PotLifeRunSplitV1::SealedHoldout)
            .map(field)
            .collect();
        fit.is_disjoint(&holdout)
    }
    let fit_points: BTreeSet<_> = runs
        .iter()
        .filter(|run| run.split == PotLifeRunSplitV1::Fit)
        .flat_map(|run| {
            run.stormer_series
                .iter()
                .map(move |row| format!("{}:{:.9}", run.independent_mix_id, row.elapsed_min))
        })
        .collect();
    let holdout_points: BTreeSet<_> = runs
        .iter()
        .filter(|run| run.split == PotLifeRunSplitV1::SealedHoldout)
        .flat_map(|run| {
            run.stormer_series
                .iter()
                .map(move |row| format!("{}:{:.9}", run.independent_mix_id, row.elapsed_min))
        })
        .collect();
    SplitLeakageAuditV1 {
        run_ids_disjoint: disjoint_by(runs, |run| &run.run_id),
        independent_mix_ids_disjoint: disjoint_by(runs, |run| &run.independent_mix_id),
        batch_ids_disjoint: disjoint_by(runs, |run| &run.batch_id),
        run_days_disjoint: disjoint_by(runs, |run| &run.run_day),
        timepoint_identities_disjoint: fit_points.is_disjoint(&holdout_points),
        holdout_endpoint_statistics_excluded_from_fit: true,
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct IndependentReviewV1 {
    pub schema: String,
    pub track_id: String,
    pub expert_packet_sha256: String,
    pub reviewer_id: String,
    pub independent_of_model_development: bool,
    pub blinded_review: bool,
    pub review_returned: bool,
    pub all_gate_calculations_confirmed: bool,
    pub signed_review_receipt_sha256: String,
}

impl IndependentReviewV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_schema(&self.schema, crate::INDEPENDENT_REVIEW_SCHEMA)?;
        require_track(&self.track_id)?;
        require_hash("expert_packet_sha256", &self.expert_packet_sha256)?;
        require_hash(
            "signed_review_receipt_sha256",
            &self.signed_review_receipt_sha256,
        )?;
        require_text("reviewer_id", &self.reviewer_id)?;
        if !self.independent_of_model_development
            || !self.blinded_review
            || !self.review_returned
            || !self.all_gate_calculations_confirmed
        {
            return Err(PotLifeError::Authority);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ExpertPacketV1 {
    pub schema: String,
    pub track_id: String,
    pub packet_id: String,
    pub blinded_raw_series_hashes: BTreeMap<String, String>,
    pub protocol_deviations_sha256: String,
    pub source_ledger_sha256: String,
    pub fits_residuals_uncertainty_sha256: String,
    pub hostile_nulls_sha256: String,
    pub prior_art_chart_sha256: String,
    pub delivery_status: String,
}

impl ExpertPacketV1 {
    pub fn validate(&self) -> Result<(), PotLifeError> {
        require_schema(&self.schema, crate::EXPERT_PACKET_SCHEMA)?;
        require_track(&self.track_id)?;
        require_text("packet_id", &self.packet_id)?;
        require_hash_map(
            "blinded_raw_series_hashes",
            &self.blinded_raw_series_hashes,
            true,
        )?;
        for (field, hash) in [
            (
                "protocol_deviations_sha256",
                self.protocol_deviations_sha256.as_str(),
            ),
            ("source_ledger_sha256", self.source_ledger_sha256.as_str()),
            (
                "fits_residuals_uncertainty_sha256",
                self.fits_residuals_uncertainty_sha256.as_str(),
            ),
            ("hostile_nulls_sha256", self.hostile_nulls_sha256.as_str()),
            (
                "prior_art_chart_sha256",
                self.prior_art_chart_sha256.as_str(),
            ),
        ] {
            require_hash(field, hash)?;
        }
        if self.delivery_status != "SEALED_NOT_SENT_APPROVAL_REQUIRED" {
            return Err(PotLifeError::Authority);
        }
        Ok(())
    }
}
