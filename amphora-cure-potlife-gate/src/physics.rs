use crate::{
    contract_hash, ApplicationAdapterV1, ParameterIntervalV1, PotLifeApplicabilityDomainV1,
    PotLifeCompositionV1, PotLifeEndpointV1, PotLifeError, PotLifeGateStatusV1,
    PotLifeModelArtifactV1, PotLifePredictionV1, PotLifeRunSplitV1, PotLifeRunV1,
    ReducedPhysicalParametersV1, ResearchAuthorityV1, TemperatureObservationV1, ViscosityProxyV1,
    POT_LIFE_PREDICTION_SCHEMA, POT_LIFE_TRACK_ID,
};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub const GAS_CONSTANT_J_MOL_K: f64 = 8.314_462_618_153_24;
pub const REFERENCE_TEMPERATURE_K: f64 = 295.927_777_777_777_75; // 73 °F
const EA_LOWER_J_MOL: f64 = 20_000.0;
const EA_UPPER_J_MOL: f64 = 120_000.0;

pub fn fahrenheit_to_kelvin(temperature_f: f64) -> Result<f64, PotLifeError> {
    if !temperature_f.is_finite() {
        return Err(PotLifeError::Range("temperature_f"));
    }
    let kelvin = (temperature_f - 32.0) * 5.0 / 9.0 + 273.15;
    if kelvin <= 0.0 {
        Err(PotLifeError::Range("temperature_f"))
    } else {
        Ok(kelvin)
    }
}

pub fn celsius_to_kelvin(temperature_c: f64) -> Result<f64, PotLifeError> {
    if !temperature_c.is_finite() || temperature_c <= -273.15 {
        Err(PotLifeError::Range("temperature_c"))
    } else {
        Ok(temperature_c + 273.15)
    }
}

pub fn effective_cure_rate(
    temperature_k: f64,
    activation_energy_j_mol: f64,
    reference_temperature_k: f64,
) -> Result<f64, PotLifeError> {
    if [
        temperature_k,
        activation_energy_j_mol,
        reference_temperature_k,
    ]
    .iter()
    .any(|value| !value.is_finite() || *value <= 0.0)
    {
        return Err(PotLifeError::Range("effective cure rate"));
    }
    let rate = (-activation_energy_j_mol / GAS_CONSTANT_J_MOL_K
        * (1.0 / temperature_k - 1.0 / reference_temperature_k))
        .exp();
    if rate.is_finite() && rate > 0.0 {
        Ok(rate)
    } else {
        Err(PotLifeError::Range("effective cure rate"))
    }
}

pub fn integrate_effective_cure_clock(
    series: &[TemperatureObservationV1],
    elapsed_min: f64,
    activation_energy_j_mol: f64,
    reference_temperature_k: f64,
) -> Result<f64, PotLifeError> {
    validate_temperature_input(series, elapsed_min)?;
    if elapsed_min == 0.0 {
        return Ok(0.0);
    }
    let mut clock = 0.0;
    for pair in series.windows(2) {
        if pair[0].elapsed_min >= elapsed_min {
            break;
        }
        let segment_end = pair[1].elapsed_min.min(elapsed_min);
        let fraction =
            (segment_end - pair[0].elapsed_min) / (pair[1].elapsed_min - pair[0].elapsed_min);
        let end_temperature_c = pair[0].material_temperature_c
            + fraction * (pair[1].material_temperature_c - pair[0].material_temperature_c);
        let start_rate = effective_cure_rate(
            celsius_to_kelvin(pair[0].material_temperature_c)?,
            activation_energy_j_mol,
            reference_temperature_k,
        )?;
        let end_rate = effective_cure_rate(
            celsius_to_kelvin(end_temperature_c)?,
            activation_energy_j_mol,
            reference_temperature_k,
        )?;
        clock += 0.5 * (start_rate + end_rate) * (segment_end - pair[0].elapsed_min);
        if segment_end == elapsed_min {
            break;
        }
    }
    Ok(clock)
}

pub fn pre_gel_cure_contribution(
    effective_clock_min: f64,
    gel_clock_min: f64,
    positive_scale: f64,
    positive_exponent: f64,
) -> Result<f64, PotLifeError> {
    if [
        effective_clock_min,
        gel_clock_min,
        positive_scale,
        positive_exponent,
    ]
    .iter()
    .any(|value| !value.is_finite())
        || effective_clock_min < 0.0
        || gel_clock_min <= 0.0
        || positive_scale < 0.0
        || positive_exponent <= 0.0
        || effective_clock_min >= gel_clock_min
    {
        return Err(PotLifeError::Range("pre-gel cure contribution"));
    }
    Ok(positive_scale
        * (effective_clock_min / (gel_clock_min - effective_clock_min)).powf(positive_exponent))
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct FloryStockmayerBoundsV1 {
    pub lower_conversion_fraction: f64,
    pub upper_conversion_fraction: f64,
    pub assumption: String,
}

pub fn flory_stockmayer_bounds(
    composition: &PotLifeCompositionV1,
) -> Option<FloryStockmayerBoundsV1> {
    if !composition.allows_flory_stockmayer_bounds() {
        return None;
    }
    let mean = |rows: &Option<Vec<crate::FunctionalityDistributionV1>>| {
        rows.as_ref().map(|rows| {
            rows.iter()
                .map(|row| row.functionality * row.mole_fraction_0_1)
                .sum::<f64>()
        })
    };
    let epoxy = mean(&composition.epoxy_functionality)?;
    let primary = mean(&composition.primary_amine_functionality)?;
    let secondary = mean(&composition.secondary_amine_functionality)?;
    let amine = 0.5 * (primary + secondary);
    let denominator = ((epoxy - 1.0).max(0.0) * (amine - 1.0).max(0.0)).sqrt();
    if denominator <= 0.0 {
        return None;
    }
    let center = (1.0 / denominator).clamp(0.0, 1.0);
    Some(FloryStockmayerBoundsV1 {
        lower_conversion_fraction: (0.9 * center).clamp(0.0, 1.0),
        upper_conversion_fraction: (1.1 * center).clamp(0.0, 1.0),
        assumption: "IDEAL_RANDOM_BRANCHING_NO_INTRAMOLECULAR_CYCLES_BOUND_ONLY".into(),
    })
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ReducedFitV1 {
    pub parameters: ReducedPhysicalParametersV1,
    pub parameter_profile_intervals: BTreeMap<String, ParameterIntervalV1>,
    pub parameters_identifiable: bool,
    pub application_adapters: BTreeMap<String, ApplicationAdapterV1>,
    pub applicability_domain: PotLifeApplicabilityDomainV1,
    pub training_run_hashes: BTreeMap<String, String>,
    pub rheology_log_mae: f64,
    pub constant_rheology_baseline_log_mae: f64,
}

#[derive(Debug, Clone)]
struct CandidateFit {
    activation_energy_j_mol: f64,
    gel_clock_min: f64,
    loss: f64,
    scales: BTreeMap<String, f64>,
    rheology_log_mae: f64,
    baseline_log_mae: f64,
}

pub fn fit_reduced_model(runs: &[PotLifeRunV1]) -> Result<ReducedFitV1, PotLifeError> {
    let training: Vec<_> = runs
        .iter()
        .filter(|run| run.split == PotLifeRunSplitV1::Fit)
        .collect();
    let temperatures: BTreeSet<_> = training
        .iter()
        .map(|run| run.target_temperature_f)
        .collect();
    if temperatures.len() < 2 {
        return Err(PotLifeError::Model("activation energy is not identifiable"));
    }
    if training.len() < 4 {
        return Err(PotLifeError::Model("insufficient fit runs"));
    }
    for run in &training {
        run.validate()?;
    }
    ensure_consistent_formulations(&training)?;
    let energies: Vec<_> = (20..=120).map(|value| value as f64 * 1_000.0).collect();
    let candidates: Vec<_> = energies
        .par_iter()
        .filter_map(|energy| fit_at_energy(&training, *energy).ok())
        .collect();
    let best = candidates
        .iter()
        .min_by(|left, right| {
            left.loss.total_cmp(&right.loss).then_with(|| {
                left.activation_energy_j_mol
                    .total_cmp(&right.activation_energy_j_mol)
            })
        })
        .ok_or(PotLifeError::Model("no finite reduced fit"))?;
    let tolerance = (best.loss.abs() * 0.05).max(1e-8);
    let profile: Vec<_> = candidates
        .iter()
        .filter(|candidate| candidate.loss <= best.loss + tolerance)
        .collect();
    let ea_lower = profile
        .iter()
        .map(|candidate| candidate.activation_energy_j_mol)
        .fold(f64::INFINITY, f64::min);
    let ea_upper = profile
        .iter()
        .map(|candidate| candidate.activation_energy_j_mol)
        .fold(f64::NEG_INFINITY, f64::max);
    let gel_lower = profile
        .iter()
        .map(|candidate| candidate.gel_clock_min)
        .fold(f64::INFINITY, f64::min);
    let gel_upper = profile
        .iter()
        .map(|candidate| candidate.gel_clock_min)
        .fold(f64::NEG_INFINITY, f64::max);
    let identifiable = ea_lower > EA_LOWER_J_MOL
        && ea_upper < EA_UPPER_J_MOL
        && ea_upper - ea_lower <= 40_000.0
        && gel_lower.is_finite()
        && gel_upper.is_finite()
        && gel_upper / gel_lower <= 2.5;
    let intervals = BTreeMap::from([
        (
            "activation_energy_j_mol".into(),
            ParameterIntervalV1 {
                lower: ea_lower,
                estimate: best.activation_energy_j_mol,
                upper: ea_upper,
                confidence: 0.95,
                bounded: ea_lower >= EA_LOWER_J_MOL && ea_upper <= EA_UPPER_J_MOL,
            },
        ),
        (
            "gel_clock_min".into(),
            ParameterIntervalV1 {
                lower: gel_lower,
                estimate: best.gel_clock_min,
                upper: gel_upper,
                confidence: 0.95,
                bounded: gel_lower > 0.0 && gel_upper.is_finite(),
            },
        ),
    ]);
    let adapters = fit_application_adapters(&training, best.activation_energy_j_mol)?;
    let formulation_hashes = training.iter().fold(BTreeMap::new(), |mut rows, run| {
        rows.insert(run.formulation_id.clone(), run.formulation_hash.clone());
        rows
    });
    let geometry_sha256 = training
        .iter()
        .map(|run| run.geometry_hash())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let spray_setup_sha256 = training
        .iter()
        .map(|run| run.spray_setup_hash())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let mixed_masses_g = training
        .iter()
        .map(|run| FiniteMass(run.mixed_mass_g))
        .collect::<BTreeSet<FiniteMass>>()
        .into_iter()
        .map(|mass| mass.0)
        .collect();
    let training_run_hashes = training
        .iter()
        .map(|run| (run.run_id.clone(), run.identity_hash()))
        .collect();
    Ok(ReducedFitV1 {
        parameters: ReducedPhysicalParametersV1 {
            activation_energy_j_mol: best.activation_energy_j_mol,
            reference_temperature_k: REFERENCE_TEMPERATURE_K,
            gel_clock_min: best.gel_clock_min,
            chemorheology_exponent: 1.0,
            cure_scale_by_formulation: best.scales.clone(),
            primary_amine_rate_constant: None,
            secondary_amine_rate_constant: None,
            hydroxyl_autocatalysis_constant: None,
            etherification_rate_constant: None,
            diffusion_vitrification_parameter: None,
            heat_transfer_coefficient: None,
            evaporation_coefficient: None,
        },
        parameter_profile_intervals: intervals,
        parameters_identifiable: identifiable,
        application_adapters: adapters,
        applicability_domain: PotLifeApplicabilityDomainV1 {
            formulation_hashes,
            geometry_sha256,
            spray_setup_sha256,
            mixed_masses_g,
            chemistry_family: "SOLVENT_BORNE_DGEBA_POLYAMIDE_MARINE_PRIMER".into(),
            commercial_grade_scope: vec!["M00097".into(), "M00101".into(), "M00109".into()],
        },
        training_run_hashes,
        rheology_log_mae: best.rheology_log_mae,
        constant_rheology_baseline_log_mae: best.baseline_log_mae,
    })
}

fn fit_at_energy(
    training: &[&PotLifeRunV1],
    activation_energy_j_mol: f64,
) -> Result<CandidateFit, PotLifeError> {
    let mut clocked_responses = Vec::new();
    let mut max_clock: f64 = 0.0;
    for run in training {
        let initial = response_value(
            run.stormer_series
                .first()
                .ok_or(PotLifeError::Model("missing rheology response"))?,
        );
        for row in run.stormer_series.iter().skip(1) {
            let clock = integrate_effective_cure_clock(
                &run.temperature_series,
                row.elapsed_min,
                activation_energy_j_mol,
                REFERENCE_TEMPERATURE_K,
            )?;
            max_clock = max_clock.max(clock);
            let log_ratio = (response_value(row) / initial).ln();
            if log_ratio.is_finite() && log_ratio >= 0.0 {
                clocked_responses.push((run.formulation_id.as_str(), clock, log_ratio));
            }
        }
    }
    if clocked_responses.len() < training.len() * 2 || max_clock <= 0.0 {
        return Err(PotLifeError::Model(
            "insufficient monotone rheology response",
        ));
    }
    let event_loss = event_clock_loss(training, activation_energy_j_mol)?;
    let mut best: Option<CandidateFit> = None;
    for step in 0..=39 {
        let gel_clock = max_clock * (1.05 + step as f64 * 0.05);
        let (scales, mae, baseline_mae, mse) = fit_cure_scales(&clocked_responses, gel_clock)?;
        let loss = event_loss + mse;
        let candidate = CandidateFit {
            activation_energy_j_mol,
            gel_clock_min: gel_clock,
            loss,
            scales,
            rheology_log_mae: mae,
            baseline_log_mae: baseline_mae,
        };
        if best.as_ref().is_none_or(|current| {
            candidate
                .loss
                .total_cmp(&current.loss)
                .then_with(|| candidate.gel_clock_min.total_cmp(&current.gel_clock_min))
                .is_lt()
        }) {
            best = Some(candidate);
        }
    }
    best.ok_or(PotLifeError::Model("no chemorheology fit"))
}

fn response_value(row: &crate::StormerObservationV1) -> f64 {
    row.equivalent_viscosity_mpa_s
        .unwrap_or(row.raw_response_ku)
}

fn fit_cure_scales(
    responses: &[(&str, f64, f64)],
    gel_clock_min: f64,
) -> Result<(BTreeMap<String, f64>, f64, f64, f64), PotLifeError> {
    let formulations: BTreeSet<_> = responses.iter().map(|row| row.0).collect();
    let mut scales = BTreeMap::new();
    for formulation in formulations {
        let mut numerator = 0.0;
        let mut denominator = 0.0;
        for (_, clock, observed) in responses.iter().filter(|row| row.0 == formulation) {
            let basis = clock / (gel_clock_min - clock);
            numerator += basis * observed;
            denominator += basis * basis;
        }
        let scale = if denominator > 0.0 {
            (numerator / denominator).max(0.0)
        } else {
            0.0
        };
        scales.insert(formulation.into(), scale);
    }
    let mut absolute = Vec::with_capacity(responses.len());
    let mut squared = 0.0;
    let mut baseline = Vec::with_capacity(responses.len());
    for (formulation, clock, observed) in responses {
        let scale = scales
            .get(*formulation)
            .ok_or(PotLifeError::Model("missing formulation scale"))?;
        let predicted = scale * clock / (gel_clock_min - clock);
        let error = (observed - predicted).abs();
        absolute.push(error);
        baseline.push(observed.abs());
        squared += error * error;
    }
    Ok((
        scales,
        mean(&absolute),
        mean(&baseline),
        squared / responses.len() as f64,
    ))
}

fn event_clock_loss(
    training: &[&PotLifeRunV1],
    activation_energy_j_mol: f64,
) -> Result<f64, PotLifeError> {
    let mut groups: BTreeMap<String, Vec<f64>> = BTreeMap::new();
    for run in training {
        let interval = run.observed_application_interval()?;
        let midpoint = 0.5 * (interval.last_pass_min + interval.first_fail_min);
        let clock = integrate_effective_cure_clock(
            &run.temperature_series,
            midpoint,
            activation_energy_j_mol,
            REFERENCE_TEMPERATURE_K,
        )?;
        groups.entry(run.adapter_key()).or_default().push(clock);
    }
    let mut errors = Vec::new();
    for values in groups.values() {
        if values.len() < 2 {
            return Err(PotLifeError::Model("application adapter lacks replication"));
        }
        let center = median(values);
        errors.extend(values.iter().map(|value| (value / center).ln().powi(2)));
    }
    Ok(mean(&errors))
}

fn fit_application_adapters(
    training: &[&PotLifeRunV1],
    activation_energy_j_mol: f64,
) -> Result<BTreeMap<String, ApplicationAdapterV1>, PotLifeError> {
    let mut grouped: BTreeMap<String, Vec<(f64, f64, &PotLifeRunV1)>> = BTreeMap::new();
    for run in training {
        let interval = run.observed_application_interval()?;
        let lower = integrate_effective_cure_clock(
            &run.temperature_series,
            interval.last_pass_min,
            activation_energy_j_mol,
            REFERENCE_TEMPERATURE_K,
        )?;
        let upper = integrate_effective_cure_clock(
            &run.temperature_series,
            interval.first_fail_min,
            activation_energy_j_mol,
            REFERENCE_TEMPERATURE_K,
        )?;
        grouped
            .entry(run.adapter_key())
            .or_default()
            .push((lower, upper, run));
    }
    grouped
        .into_iter()
        .map(|(key, values)| {
            let midpoints: Vec<_> = values
                .iter()
                .map(|(lower, upper, _)| 0.5 * (lower + upper))
                .collect();
            let lower_values: Vec<_> = values.iter().map(|(lower, _, _)| *lower).collect();
            let upper_values: Vec<_> = values.iter().map(|(_, upper, _)| *upper).collect();
            let run = values[0].2;
            let row = ApplicationAdapterV1 {
                adapter_key: key.clone(),
                formulation_id: run.formulation_id.clone(),
                geometry_sha256: run.geometry_hash(),
                spray_setup_sha256: run.spray_setup_hash(),
                mixed_mass_g: run.mixed_mass_g,
                critical_clock_min: median(&midpoints),
                critical_clock_pi90_lower_min: quantile(&lower_values, 0.05),
                critical_clock_pi90_upper_min: quantile(&upper_values, 0.95),
            };
            Ok((key, row))
        })
        .collect()
}

fn ensure_consistent_formulations(training: &[&PotLifeRunV1]) -> Result<(), PotLifeError> {
    let mut hashes = BTreeMap::new();
    for run in training {
        if hashes
            .insert(run.formulation_id.as_str(), run.formulation_hash.as_str())
            .is_some_and(|previous| previous != run.formulation_hash)
        {
            return Err(PotLifeError::Model("formulation hash changed within grade"));
        }
    }
    Ok(())
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PredictionConditionsV1 {
    pub formulation_id: String,
    pub formulation_hash: String,
    pub geometry_sha256: String,
    pub spray_setup_sha256: String,
    pub mixed_mass_g: f64,
    pub expected_material_temperature_series: Vec<TemperatureObservationV1>,
    pub viscosity_proxy: Option<ViscosityProxyV1>,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) struct ResearchPotLifeEstimate {
    pub point_min: f64,
    pub lower_min: f64,
    pub upper_min: f64,
}

pub(crate) fn research_estimate(
    parameters: &ReducedPhysicalParametersV1,
    adapter: &ApplicationAdapterV1,
    temperature_series: &[TemperatureObservationV1],
) -> Result<ResearchPotLifeEstimate, PotLifeError> {
    Ok(ResearchPotLifeEstimate {
        point_min: invert_effective_clock(
            temperature_series,
            adapter.critical_clock_min,
            parameters.activation_energy_j_mol,
            parameters.reference_temperature_k,
        )?,
        lower_min: invert_effective_clock(
            temperature_series,
            adapter.critical_clock_pi90_lower_min,
            parameters.activation_energy_j_mol,
            parameters.reference_temperature_k,
        )?,
        upper_min: invert_effective_clock(
            temperature_series,
            adapter.critical_clock_pi90_upper_min,
            parameters.activation_energy_j_mol,
            parameters.reference_temperature_k,
        )?,
    })
}

pub fn predict_application_pot_life(
    model: &PotLifeModelArtifactV1,
    conditions: &PredictionConditionsV1,
) -> Result<PotLifePredictionV1, PotLifeError> {
    model.validate()?;
    let formulation_match = model
        .applicability_domain
        .formulation_hashes
        .get(&conditions.formulation_id)
        == Some(&conditions.formulation_hash);
    let geometry_match = model
        .applicability_domain
        .geometry_sha256
        .contains(&conditions.geometry_sha256);
    let spray_match = model
        .applicability_domain
        .spray_setup_sha256
        .contains(&conditions.spray_setup_sha256);
    let mass_match = model
        .applicability_domain
        .mixed_masses_g
        .iter()
        .any(|mass| (*mass - conditions.mixed_mass_g).abs() <= 1e-9);
    let adapter_key = format!(
        "{}|{}|{}",
        conditions.formulation_id, conditions.geometry_sha256, conditions.spray_setup_sha256
    );
    let adapter = model.application_adapters.get(&adapter_key);
    let adapter_mass_match = adapter
        .is_some_and(|adapter| (adapter.mixed_mass_g - conditions.mixed_mass_g).abs() <= 1e-9);
    let in_domain =
        formulation_match && geometry_match && spray_match && mass_match && adapter_mass_match;
    let authorized = in_domain && model.gate_status.authorizes_non_null_shadow_prediction();
    let estimate = if authorized {
        Some(research_estimate(
            &model.parameters,
            adapter.expect("in-domain adapter checked"),
            &conditions.expected_material_temperature_series,
        )?)
    } else {
        None
    };
    let mut abstentions = Vec::new();
    if !in_domain {
        abstentions.push("FORMULATION_MASS_GEOMETRY_OR_SPRAY_SETUP_OUT_OF_DOMAIN".into());
    }
    if !model.gate_status.locked_gate_passed() {
        abstentions.push("LOCKED_BENCHMARK_GATE_NOT_PASSED".into());
    }
    if !model.gate_status.independent_review_passed {
        abstentions.push("INDEPENDENT_REVIEW_NOT_RETURNED".into());
    }
    let model_hash = model.identity_hash();
    let prediction_seed = contract_hash(&(
        model_hash.as_str(),
        conditions.formulation_id.as_str(),
        conditions.geometry_sha256.as_str(),
        conditions.spray_setup_sha256.as_str(),
    ))?;
    let prediction = PotLifePredictionV1 {
        schema: POT_LIFE_PREDICTION_SCHEMA.into(),
        track_id: POT_LIFE_TRACK_ID.into(),
        prediction_id: format!("pot-life-prediction-{}", &prediction_seed[..16]),
        model_artifact_sha256: model_hash,
        endpoint: PotLifeEndpointV1::AirlessSprayFirstPropertyFailure,
        authority: ResearchAuthorityV1::Shadow,
        formulation_id: conditions.formulation_id.clone(),
        formulation_hash: conditions.formulation_hash.clone(),
        geometry_sha256: conditions.geometry_sha256.clone(),
        spray_setup_sha256: conditions.spray_setup_sha256.clone(),
        mixed_mass_g: conditions.mixed_mass_g,
        in_applicability_domain: in_domain,
        locked_gate_passed: model.gate_status.locked_gate_passed(),
        independent_review_passed: model.gate_status.independent_review_passed,
        candidate_pot_life_prediction_h: estimate.map(|row| row.point_min / 60.0),
        prediction_interval_90_h: estimate.map(|row| [row.lower_min / 60.0, row.upper_min / 60.0]),
        viscosity_proxy: conditions.viscosity_proxy.clone(),
        abstention_reasons: abstentions,
    };
    prediction.validate()?;
    Ok(prediction)
}

pub(crate) fn empty_gate_status() -> PotLifeGateStatusV1 {
    PotLifeGateStatusV1 {
        valid_independent_runs_36: false,
        untouched_73f_holdouts_12: false,
        zero_split_leakage: false,
        holdout_factor_1_5_at_least_0_80: false,
        lift_at_least_0_10: false,
        paired_bootstrap_lower_positive: false,
        interval_coverage_0_85_to_0_95: false,
        parameters_finite_identifiable_bounded: false,
        viscosity_proxy_non_worse: false,
        replay_equal_1_2_8_workers: false,
        hostile_null_suite_passed: false,
        independent_review_passed: false,
    }
}

fn invert_effective_clock(
    series: &[TemperatureObservationV1],
    target_clock_min: f64,
    activation_energy_j_mol: f64,
    reference_temperature_k: f64,
) -> Result<f64, PotLifeError> {
    if !target_clock_min.is_finite() || target_clock_min <= 0.0 {
        return Err(PotLifeError::Range("target effective clock"));
    }
    let maximum_time = series
        .last()
        .ok_or(PotLifeError::TimeOrder("temperature series"))?
        .elapsed_min;
    let maximum_clock = integrate_effective_cure_clock(
        series,
        maximum_time,
        activation_energy_j_mol,
        reference_temperature_k,
    )?;
    if maximum_clock < target_clock_min {
        return Err(PotLifeError::Range(
            "temperature horizon does not reach event",
        ));
    }
    let mut lower = 0.0;
    let mut upper = maximum_time;
    for _ in 0..64 {
        let middle = 0.5 * (lower + upper);
        let clock = integrate_effective_cure_clock(
            series,
            middle,
            activation_energy_j_mol,
            reference_temperature_k,
        )?;
        if clock < target_clock_min {
            lower = middle;
        } else {
            upper = middle;
        }
    }
    Ok(0.5 * (lower + upper))
}

fn validate_temperature_input(
    series: &[TemperatureObservationV1],
    elapsed_min: f64,
) -> Result<(), PotLifeError> {
    if !elapsed_min.is_finite()
        || elapsed_min < 0.0
        || series.len() < 2
        || series[0].elapsed_min.abs() > 1e-9
        || series.windows(2).any(|rows| {
            !rows[0].elapsed_min.is_finite()
                || rows[1].elapsed_min <= rows[0].elapsed_min
                || !rows[0].material_temperature_c.is_finite()
        })
        || series.last().is_none_or(|row| {
            elapsed_min > row.elapsed_min || !row.material_temperature_c.is_finite()
        })
    {
        return Err(PotLifeError::TimeOrder("temperature series"));
    }
    Ok(())
}

pub(crate) fn median(values: &[f64]) -> f64 {
    quantile(values, 0.5)
}

pub(crate) fn quantile(values: &[f64], probability: f64) -> f64 {
    let mut values = values.to_vec();
    values.sort_by(f64::total_cmp);
    if values.is_empty() {
        return f64::NAN;
    }
    let position = probability.clamp(0.0, 1.0) * (values.len() - 1) as f64;
    let lower = position.floor() as usize;
    let upper = position.ceil() as usize;
    let fraction = position - lower as f64;
    values[lower] + fraction * (values[upper] - values[lower])
}

fn mean(values: &[f64]) -> f64 {
    values.iter().sum::<f64>() / values.len() as f64
}

#[derive(Debug, Clone, Copy, PartialEq)]
struct FiniteMass(f64);

impl Eq for FiniteMass {}

impl PartialOrd for FiniteMass {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for FiniteMass {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.0.total_cmp(&other.0)
    }
}
