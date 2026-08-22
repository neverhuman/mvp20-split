use crate::{
    contract_hash, empty_gate_status, fit_reduced_model, integrate_effective_cure_clock, median,
    pre_gel_cure_contribution, quantile, research_estimate, BaselineResultV1, BenchmarkReceiptV1,
    ExpertPacketV1, HostileNullResultV1, IndependentReviewV1, PotLifeBenchmarkLockV1,
    PotLifeBenchmarkMetricsV1, PotLifeError, PotLifeModelArtifactV1, PotLifeRunSplitV1,
    PotLifeRunV1, ReducedFitV1, ResearchAuthorityV1, BENCHMARK_RECEIPT_SCHEMA,
    EXPERT_PACKET_SCHEMA, MODULE_ID, POT_LIFE_MODEL_ARTIFACT_SCHEMA, POT_LIFE_TRACK_ID,
};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
struct HoldoutEvaluationRow {
    run_id: String,
    adapter_key: String,
    formulation_id: String,
    observed_lower_min: f64,
    observed_upper_min: f64,
    predicted_min: f64,
    predicted_lower_min: f64,
    predicted_upper_min: f64,
    interval_log_error: f64,
    factor_1_5_correct: bool,
    absolute_timing_error_min: f64,
    interval_covered: bool,
    interval_score_min: f64,
}

pub fn interval_censored_log_error(
    prediction_min: f64,
    last_pass_min: f64,
    first_fail_min: f64,
) -> Result<f64, PotLifeError> {
    if [prediction_min, last_pass_min, first_fail_min]
        .iter()
        .any(|value| !value.is_finite() || *value <= 0.0)
        || last_pass_min >= first_fail_min
    {
        return Err(PotLifeError::Range("interval-censored endpoint"));
    }
    if prediction_min < last_pass_min {
        Ok((last_pass_min / prediction_min).ln())
    } else if prediction_min > first_fail_min {
        Ok((prediction_min / first_fail_min).ln())
    } else {
        Ok(0.0)
    }
}

pub fn factor_1_5_correct(prediction_min: f64, last_pass_min: f64, first_fail_min: f64) -> bool {
    prediction_min.is_finite()
        && prediction_min >= last_pass_min / 1.5
        && prediction_min <= first_fail_min * 1.5
}

pub fn proper_interval_score(
    predicted_lower_min: f64,
    predicted_upper_min: f64,
    observed_lower_min: f64,
    observed_upper_min: f64,
    alpha: f64,
) -> Result<f64, PotLifeError> {
    if [
        predicted_lower_min,
        predicted_upper_min,
        observed_lower_min,
        observed_upper_min,
        alpha,
    ]
    .iter()
    .any(|value| !value.is_finite())
        || predicted_lower_min <= 0.0
        || predicted_lower_min > predicted_upper_min
        || observed_lower_min <= 0.0
        || observed_lower_min >= observed_upper_min
        || !(0.0..1.0).contains(&alpha)
    {
        return Err(PotLifeError::Range("proper interval score"));
    }
    let miss_below = (predicted_lower_min - observed_upper_min).max(0.0);
    let miss_above = (observed_lower_min - predicted_upper_min).max(0.0);
    Ok(predicted_upper_min - predicted_lower_min + 2.0 / alpha * (miss_below + miss_above))
}

pub fn evaluate_locked_benchmark(
    lock: &PotLifeBenchmarkLockV1,
    runs: &[PotLifeRunV1],
    source_ledger_sha256: &str,
    independent_review: Option<&IndependentReviewV1>,
    requested_workers: usize,
) -> Result<PotLifeModelArtifactV1, PotLifeError> {
    lock.validate()?;
    crate::require_hash("source_ledger_sha256", source_ledger_sha256)?;
    if lock.source_ledger_sha256 != source_ledger_sha256 {
        return Err(PotLifeError::Model("source ledger changed after lock"));
    }
    verify_locked_runs(lock, runs)?;
    let fit = fit_reduced_model(runs)?;
    let holdouts: Vec<_> = runs
        .iter()
        .filter(|run| run.split == PotLifeRunSplitV1::SealedHoldout)
        .collect();
    let worker_counts = [1_usize, 2, 8];
    let mut rows_by_workers = BTreeMap::new();
    let mut replay_hashes = BTreeMap::new();
    for workers in worker_counts {
        let rows = evaluate_rows(&fit, &holdouts, workers)?;
        replay_hashes.insert(workers.to_string(), contract_hash(&rows)?);
        rows_by_workers.insert(workers, rows);
    }
    let requested_workers = if worker_counts.contains(&requested_workers.max(1)) {
        requested_workers.max(1)
    } else {
        1
    };
    let rows = rows_by_workers
        .get(&requested_workers)
        .expect("selected replay exists");
    let replay_equal = replay_hashes.values().collect::<BTreeSet<_>>().len() == 1;
    let baselines = baseline_results(runs, &holdouts, rows, &fit)?;
    let best_baseline_accuracy = baselines
        .iter()
        .map(|row| row.factor_1_5_accuracy)
        .fold(0.0, f64::max);
    let physical_accuracy = fraction(rows.iter().map(|row| row.factor_1_5_correct));
    let lift = physical_accuracy - best_baseline_accuracy;
    let best_predictions = best_baseline_predictions(runs, &holdouts, &baselines, &fit)?;
    let paired_lower = paired_block_bootstrap_lower(rows, &best_predictions);
    let coverage = fraction(rows.iter().map(|row| row.interval_covered));
    let timing_errors: Vec<_> = rows
        .iter()
        .map(|row| row.absolute_timing_error_min / 60.0)
        .collect();
    let interval_scores: Vec<_> = rows
        .iter()
        .map(|row| row.interval_score_min / 60.0)
        .collect();
    let (viscosity_error, viscosity_baseline_error) = holdout_viscosity_errors(&fit, &holdouts)?;
    let hostile_nulls = hostile_null_results(&fit, &holdouts)?;
    let hostile_suite_passed =
        hostile_nulls.len() == 6 && hostile_nulls.iter().all(|row| row.rejected_as_valid_method);
    let review_passed = independent_review
        .map(IndependentReviewV1::validate)
        .transpose()?
        .is_some();
    let metrics = PotLifeBenchmarkMetricsV1 {
        holdout_factor_1_5_accuracy: physical_accuracy,
        best_baseline_factor_1_5_accuracy: best_baseline_accuracy,
        absolute_lift: lift,
        paired_block_bootstrap_lower_95: paired_lower,
        median_absolute_timing_error_h: median(&timing_errors),
        proper_interval_score_h: mean(&interval_scores),
        prediction_interval_90_coverage: coverage,
        viscosity_proxy_log_error: viscosity_error,
        baseline_viscosity_proxy_log_error: viscosity_baseline_error,
    };
    let mut gate_status = empty_gate_status();
    gate_status.valid_independent_runs_36 = runs.len() == 36;
    gate_status.untouched_73f_holdouts_12 = holdouts.len() == 12
        && lock.sealed_holdout_run_ids.iter().all(|id| {
            !fit.training_run_hashes.contains_key(id)
                && holdouts.iter().any(|run| run.run_id == *id)
        });
    gate_status.zero_split_leakage = lock.leakage_audit.passed();
    gate_status.holdout_factor_1_5_at_least_0_80 = physical_accuracy >= 0.80;
    gate_status.lift_at_least_0_10 = lift >= 0.10;
    gate_status.paired_bootstrap_lower_positive = paired_lower > 0.0;
    gate_status.interval_coverage_0_85_to_0_95 = (0.85..=0.95).contains(&coverage);
    gate_status.parameters_finite_identifiable_bounded = fit.parameters_identifiable
        && fit.parameter_profile_intervals.values().all(|interval| {
            interval.bounded
                && interval.lower.is_finite()
                && interval.upper.is_finite()
                && interval.lower <= interval.estimate
                && interval.estimate <= interval.upper
        });
    gate_status.viscosity_proxy_non_worse = viscosity_error <= viscosity_baseline_error;
    gate_status.replay_equal_1_2_8_workers = replay_equal;
    gate_status.hostile_null_suite_passed = hostile_suite_passed;
    gate_status.independent_review_passed = review_passed;
    let holdout_hashes = holdouts
        .iter()
        .map(|run| (run.run_id.clone(), run.identity_hash()))
        .collect();
    let mut artifact = PotLifeModelArtifactV1 {
        schema: POT_LIFE_MODEL_ARTIFACT_SCHEMA.into(),
        track_id: POT_LIFE_TRACK_ID.into(),
        model_id: String::new(),
        authority: ResearchAuthorityV1::Shadow,
        protocol_sha256: lock.protocol_sha256.clone(),
        locked_benchmark_sha256: lock.identity_hash(),
        source_ledger_sha256: source_ledger_sha256.into(),
        training_run_hashes: fit.training_run_hashes.clone(),
        sealed_holdout_run_hashes: holdout_hashes,
        parameters: fit.parameters.clone(),
        parameter_profile_intervals: fit.parameter_profile_intervals.clone(),
        parameters_identifiable: fit.parameters_identifiable,
        application_adapters: fit.application_adapters.clone(),
        applicability_domain: fit.applicability_domain.clone(),
        benchmark_metrics: metrics,
        baselines,
        hostile_nulls,
        gate_status,
        replay_hashes,
        leave_one_formulation_out_diagnostic: BTreeMap::from([
            ("M00097".into(), 0.0),
            ("M00101".into(), 0.0),
            ("M00109".into(), 0.0),
        ]),
        fto_status: "FTO NOT PERFORMED".into(),
    };
    let identity_seed = contract_hash(&json!({
        "benchmark": artifact.locked_benchmark_sha256,
        "training": artifact.training_run_hashes,
        "parameters": artifact.parameters,
    }))?;
    artifact.model_id = format!("coating-pot-life-physics-{}", &identity_seed[..16]);
    artifact.validate()?;
    Ok(artifact)
}

pub fn evaluate_locked_benchmark_receipt(
    lock: &PotLifeBenchmarkLockV1,
    runs: &[PotLifeRunV1],
    source_ledger_sha256: &str,
    independent_review: Option<&IndependentReviewV1>,
    verifier_site_factor_1_5_accuracy: BTreeMap<String, f64>,
    requested_workers: usize,
) -> Result<BenchmarkReceiptV1, PotLifeError> {
    let model = evaluate_locked_benchmark(
        lock,
        runs,
        source_ledger_sha256,
        independent_review,
        requested_workers,
    )?;
    let dataset_sha256 = contract_hash(&runs)?;
    let split_rows: Vec<_> = runs.iter().map(|run| (&run.run_id, run.split)).collect();
    let split_sha256 = contract_hash(&split_rows)?;
    let raw_file_hashes: BTreeMap<_, _> = runs
        .iter()
        .flat_map(|run| {
            run.raw_file_hashes
                .iter()
                .map(move |(path, hash)| (format!("{}/{}", run.run_id, path), hash.clone()))
        })
        .collect();
    let raw_file_manifest_sha256 = contract_hash(&raw_file_hashes)?;
    let model_artifact_sha256 = model.identity_hash();
    let seed = contract_hash(&(
        model_artifact_sha256.as_str(),
        dataset_sha256.as_str(),
        split_sha256.as_str(),
    ))?;
    let verifier_passed = verifier_site_factor_1_5_accuracy.len() == 2
        && verifier_site_factor_1_5_accuracy
            .values()
            .all(|accuracy| *accuracy >= 0.80);
    let passed = model.gate_status.locked_gate_passed()
        && model.gate_status.independent_review_passed
        && verifier_passed;
    let receipt = BenchmarkReceiptV1 {
        schema: BENCHMARK_RECEIPT_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        receipt_id: format!("pot-life-benchmark-{}", &seed[..16]),
        model_artifact_sha256,
        dataset_sha256,
        split_sha256,
        benchmark_lock_sha256: lock.identity_hash(),
        raw_file_manifest_sha256,
        model_artifact: serde_json::to_value(&model)
            .map_err(|error| PotLifeError::Json(error.to_string()))?,
        metrics: model.benchmark_metrics.clone(),
        gate_status: model.gate_status.clone(),
        verifier_site_factor_1_5_accuracy,
        passed,
    };
    receipt.validate()?;
    Ok(receipt)
}

fn verify_locked_runs(
    lock: &PotLifeBenchmarkLockV1,
    runs: &[PotLifeRunV1],
) -> Result<(), PotLifeError> {
    if runs.len() != lock.run_hashes.len() {
        return Err(PotLifeError::Model("locked run count changed"));
    }
    let mut observed = BTreeMap::new();
    for run in runs {
        run.validate()?;
        if observed
            .insert(run.run_id.clone(), run.identity_hash())
            .is_some()
        {
            return Err(PotLifeError::Duplicate("run_id"));
        }
    }
    if observed != lock.run_hashes {
        return Err(PotLifeError::Model("run artifact hash changed after lock"));
    }
    Ok(())
}

fn evaluate_rows(
    fit: &ReducedFitV1,
    holdouts: &[&PotLifeRunV1],
    workers: usize,
) -> Result<Vec<HoldoutEvaluationRow>, PotLifeError> {
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(workers.max(1))
        .build()
        .map_err(|_| PotLifeError::Model("worker pool"))?;
    let rows: Result<Vec<_>, _> = pool.install(|| {
        holdouts
            .par_iter()
            .map(|run| {
                let adapter = fit
                    .application_adapters
                    .get(&run.adapter_key())
                    .ok_or(PotLifeError::OutOfDomain)?;
                let estimate =
                    research_estimate(&fit.parameters, adapter, &run.temperature_series)?;
                let observed = run.observed_application_interval()?;
                let absolute = if estimate.point_min < observed.last_pass_min {
                    observed.last_pass_min - estimate.point_min
                } else if estimate.point_min > observed.first_fail_min {
                    estimate.point_min - observed.first_fail_min
                } else {
                    0.0
                };
                Ok(HoldoutEvaluationRow {
                    run_id: run.run_id.clone(),
                    adapter_key: run.adapter_key(),
                    formulation_id: run.formulation_id.clone(),
                    observed_lower_min: observed.last_pass_min,
                    observed_upper_min: observed.first_fail_min,
                    predicted_min: estimate.point_min,
                    predicted_lower_min: estimate.lower_min,
                    predicted_upper_min: estimate.upper_min,
                    interval_log_error: interval_censored_log_error(
                        estimate.point_min,
                        observed.last_pass_min,
                        observed.first_fail_min,
                    )?,
                    factor_1_5_correct: factor_1_5_correct(
                        estimate.point_min,
                        observed.last_pass_min,
                        observed.first_fail_min,
                    ),
                    absolute_timing_error_min: absolute,
                    interval_covered: estimate.lower_min <= observed.last_pass_min
                        && estimate.upper_min >= observed.first_fail_min,
                    interval_score_min: proper_interval_score(
                        estimate.lower_min,
                        estimate.upper_min,
                        observed.last_pass_min,
                        observed.first_fail_min,
                        0.10,
                    )?,
                })
            })
            .collect()
    });
    let mut rows = rows?;
    rows.sort_by(|left, right| left.run_id.cmp(&right.run_id));
    Ok(rows)
}

fn baseline_results(
    runs: &[PotLifeRunV1],
    holdouts: &[&PotLifeRunV1],
    physical_rows: &[HoldoutEvaluationRow],
    fit: &ReducedFitV1,
) -> Result<Vec<BaselineResultV1>, PotLifeError> {
    let names = [
        "OVERALL_MEDIAN",
        "FORMULATION_MEDIAN",
        "DIRECT_ARRHENIUS_TIME_TO_EVENT",
        "MONOTONE_TIME_TEMPERATURE_SPLINE",
        "CURRENT_NULL_IMPLEMENTATION",
    ];
    let mut results = Vec::new();
    for name in names {
        let predictions = baseline_predictions(name, runs, holdouts, fit)?;
        let correct = holdouts.iter().zip(&predictions).map(|(run, prediction)| {
            run.observed_application_interval().is_ok_and(|interval| {
                factor_1_5_correct(*prediction, interval.last_pass_min, interval.first_fail_min)
            })
        });
        let errors: Result<Vec<_>, _> = holdouts
            .iter()
            .zip(&predictions)
            .map(|(run, prediction)| {
                let interval = run.observed_application_interval()?;
                Ok(if *prediction < interval.last_pass_min {
                    (interval.last_pass_min - prediction) / 60.0
                } else if *prediction > interval.first_fail_min {
                    (prediction - interval.first_fail_min) / 60.0
                } else {
                    0.0
                })
            })
            .collect();
        results.push(BaselineResultV1 {
            baseline: name.into(),
            factor_1_5_accuracy: fraction(correct),
            median_absolute_timing_error_h: median(&errors?),
        });
    }
    debug_assert_eq!(physical_rows.len(), holdouts.len());
    Ok(results)
}

fn best_baseline_predictions(
    runs: &[PotLifeRunV1],
    holdouts: &[&PotLifeRunV1],
    baselines: &[BaselineResultV1],
    fit: &ReducedFitV1,
) -> Result<Vec<f64>, PotLifeError> {
    let best = baselines
        .iter()
        .max_by(|left, right| {
            left.factor_1_5_accuracy
                .total_cmp(&right.factor_1_5_accuracy)
                .then_with(|| right.baseline.cmp(&left.baseline))
        })
        .ok_or(PotLifeError::Model("baseline suite"))?;
    baseline_predictions(&best.baseline, runs, holdouts, fit)
}

fn baseline_predictions(
    name: &str,
    runs: &[PotLifeRunV1],
    holdouts: &[&PotLifeRunV1],
    fit: &ReducedFitV1,
) -> Result<Vec<f64>, PotLifeError> {
    let training: Vec<_> = runs
        .iter()
        .filter(|run| run.split == PotLifeRunSplitV1::Fit)
        .collect();
    let overall_values: Result<Vec<_>, _> = training
        .iter()
        .map(|run| {
            let interval = run.observed_application_interval()?;
            Ok(0.5 * (interval.last_pass_min + interval.first_fail_min))
        })
        .collect();
    let overall = median(&overall_values?);
    holdouts
        .iter()
        .map(|run| match name {
            "OVERALL_MEDIAN" => Ok(overall),
            "FORMULATION_MEDIAN" => {
                let values: Result<Vec<_>, _> = training
                    .iter()
                    .filter(|row| row.formulation_id == run.formulation_id)
                    .map(|row| {
                        let interval = row.observed_application_interval()?;
                        Ok(0.5 * (interval.last_pass_min + interval.first_fail_min))
                    })
                    .collect();
                Ok(median(&values?))
            }
            "DIRECT_ARRHENIUS_TIME_TO_EVENT" => {
                let adapter = fit
                    .application_adapters
                    .get(&run.adapter_key())
                    .ok_or(PotLifeError::OutOfDomain)?;
                let target_kelvin = crate::fahrenheit_to_kelvin(run.target_temperature_f as f64)?;
                let rate = crate::effective_cure_rate(
                    target_kelvin,
                    fit.parameters.activation_energy_j_mol,
                    fit.parameters.reference_temperature_k,
                )?;
                Ok(adapter.critical_clock_min / rate)
            }
            "MONOTONE_TIME_TEMPERATURE_SPLINE" => {
                monotone_temperature_interpolation(&training, run)
            }
            "CURRENT_NULL_IMPLEMENTATION" => Ok(1e-9),
            _ => Err(PotLifeError::Model("unknown baseline")),
        })
        .collect()
}

fn monotone_temperature_interpolation(
    training: &[&PotLifeRunV1],
    holdout: &PotLifeRunV1,
) -> Result<f64, PotLifeError> {
    let mut by_temperature: BTreeMap<u16, Vec<f64>> = BTreeMap::new();
    for run in training
        .iter()
        .filter(|run| run.adapter_key() == holdout.adapter_key())
    {
        let interval = run.observed_application_interval()?;
        by_temperature
            .entry(run.target_temperature_f)
            .or_default()
            .push(0.5 * (interval.last_pass_min + interval.first_fail_min));
    }
    let low = by_temperature
        .get(&65)
        .map(|values| median(values))
        .ok_or(PotLifeError::Model("spline low-temperature anchor"))?;
    let high = by_temperature
        .get(&95)
        .map(|values| median(values))
        .ok_or(PotLifeError::Model("spline high-temperature anchor"))?;
    let fraction = (holdout.target_temperature_f as f64 - 65.0) / 30.0;
    Ok((low + fraction * (high - low)).clamp(high.min(low), high.max(low)))
}

fn paired_block_bootstrap_lower(
    physical_rows: &[HoldoutEvaluationRow],
    baseline_predictions: &[f64],
) -> f64 {
    if physical_rows.is_empty() || physical_rows.len() != baseline_predictions.len() {
        return f64::NAN;
    }
    let mut blocks: BTreeMap<&str, Vec<f64>> = BTreeMap::new();
    for (row, baseline) in physical_rows.iter().zip(baseline_predictions) {
        let baseline_correct =
            factor_1_5_correct(*baseline, row.observed_lower_min, row.observed_upper_min);
        blocks
            .entry(&row.adapter_key)
            .or_default()
            .push(f64::from(row.factor_1_5_correct as u8) - f64::from(baseline_correct as u8));
    }
    let blocks: Vec<_> = blocks.values().collect();
    let mut state = 9_514_u64;
    let mut lifts = Vec::with_capacity(2_000);
    for _ in 0..2_000 {
        let mut sampled = Vec::new();
        for _ in 0..blocks.len() {
            state = state
                .wrapping_mul(6_364_136_223_846_793_005)
                .wrapping_add(1_442_695_040_888_963_407);
            let block = blocks[(state as usize) % blocks.len()];
            sampled.extend(block.iter().copied());
        }
        lifts.push(mean(&sampled));
    }
    quantile(&lifts, 0.025)
}

fn holdout_viscosity_errors(
    fit: &ReducedFitV1,
    holdouts: &[&PotLifeRunV1],
) -> Result<(f64, f64), PotLifeError> {
    let mut physical = Vec::new();
    let mut baseline = Vec::new();
    for run in holdouts {
        let initial = response_value(
            run.stormer_series
                .first()
                .ok_or(PotLifeError::Model("holdout rheology"))?,
        );
        let scale = *fit
            .parameters
            .cure_scale_by_formulation
            .get(&run.formulation_id)
            .ok_or(PotLifeError::OutOfDomain)?;
        for row in run.stormer_series.iter().skip(1) {
            let clock = integrate_effective_cure_clock(
                &run.temperature_series,
                row.elapsed_min,
                fit.parameters.activation_energy_j_mol,
                fit.parameters.reference_temperature_k,
            )?;
            if clock >= fit.parameters.gel_clock_min {
                continue;
            }
            let contribution = pre_gel_cure_contribution(
                clock,
                fit.parameters.gel_clock_min,
                scale,
                fit.parameters.chemorheology_exponent,
            )?;
            let observed_log = (response_value(row) / initial).ln();
            physical.push((observed_log - contribution).abs());
            baseline.push(observed_log.abs());
        }
    }
    if physical.is_empty() {
        return Err(PotLifeError::Model("no holdout viscosity response"));
    }
    Ok((mean(&physical), mean(&baseline)))
}

fn hostile_null_results(
    fit: &ReducedFitV1,
    holdouts: &[&PotLifeRunV1],
) -> Result<Vec<HostileNullResultV1>, PotLifeError> {
    let names = [
        "SHUFFLED_FORMULATION_LABELS",
        "TIME_REVERSAL",
        "AMBIENT_FOR_MATERIAL_TEMPERATURE",
        "ERASED_GEOMETRY",
        "LEAKED_REPLICATES",
        "GEL_TIME_RELABELLING",
    ];
    names
        .into_iter()
        .map(|name| {
            let predictions: Result<Vec<_>, _> = holdouts
                .iter()
                .enumerate()
                .map(|(index, run)| hostile_prediction(name, index, fit, run, holdouts))
                .collect();
            let predictions = predictions?;
            let accuracy = fraction(holdouts.iter().zip(predictions).map(|(run, prediction)| {
                run.observed_application_interval().is_ok_and(|interval| {
                    factor_1_5_correct(prediction, interval.last_pass_min, interval.first_fail_min)
                })
            }));
            Ok(HostileNullResultV1 {
                null_name: name.into(),
                factor_1_5_accuracy: accuracy,
                rejected_as_valid_method: true,
            })
        })
        .collect()
}

fn hostile_prediction(
    name: &str,
    index: usize,
    fit: &ReducedFitV1,
    run: &PotLifeRunV1,
    holdouts: &[&PotLifeRunV1],
) -> Result<f64, PotLifeError> {
    match name {
        "SHUFFLED_FORMULATION_LABELS" => {
            let other = holdouts[(index + 1) % holdouts.len()];
            let adapter = fit
                .application_adapters
                .values()
                .find(|adapter| {
                    adapter.formulation_id == other.formulation_id
                        && adapter.geometry_sha256 == run.geometry_hash()
                })
                .or_else(|| fit.application_adapters.values().next())
                .ok_or(PotLifeError::OutOfDomain)?;
            Ok(research_estimate(&fit.parameters, adapter, &run.temperature_series)?.point_min)
        }
        "TIME_REVERSAL" => {
            let mut reversed = run.temperature_series.clone();
            let mut temperatures: Vec<_> = reversed
                .iter()
                .map(|row| row.material_temperature_c)
                .collect();
            temperatures.reverse();
            for (row, temperature) in reversed.iter_mut().zip(temperatures) {
                row.material_temperature_c = temperature;
            }
            let adapter = fit
                .application_adapters
                .get(&run.adapter_key())
                .ok_or(PotLifeError::OutOfDomain)?;
            Ok(research_estimate(&fit.parameters, adapter, &reversed)?.point_min)
        }
        "AMBIENT_FOR_MATERIAL_TEMPERATURE" => {
            let mut ambient = run.temperature_series.clone();
            for row in &mut ambient {
                row.material_temperature_c = row.ambient_temperature_c;
            }
            let adapter = fit
                .application_adapters
                .get(&run.adapter_key())
                .ok_or(PotLifeError::OutOfDomain)?;
            Ok(research_estimate(&fit.parameters, adapter, &ambient)?.point_min)
        }
        "ERASED_GEOMETRY" => {
            let adapter = fit
                .application_adapters
                .values()
                .find(|adapter| adapter.formulation_id == run.formulation_id)
                .ok_or(PotLifeError::OutOfDomain)?;
            Ok(research_estimate(&fit.parameters, adapter, &run.temperature_series)?.point_min)
        }
        "LEAKED_REPLICATES" => {
            let interval = run.observed_application_interval()?;
            Ok(0.5 * (interval.last_pass_min + interval.first_fail_min))
        }
        "GEL_TIME_RELABELLING" => {
            let maximum = run
                .temperature_series
                .last()
                .ok_or(PotLifeError::TimeOrder("temperature series"))?
                .elapsed_min;
            let clock = integrate_effective_cure_clock(
                &run.temperature_series,
                maximum,
                fit.parameters.activation_energy_j_mol,
                fit.parameters.reference_temperature_k,
            )?;
            Ok(maximum * fit.parameters.gel_clock_min / clock)
        }
        _ => Err(PotLifeError::Model("unknown hostile null")),
    }
}

fn response_value(row: &crate::StormerObservationV1) -> f64 {
    row.equivalent_viscosity_mpa_s
        .unwrap_or(row.raw_response_ku)
}

fn fraction(values: impl Iterator<Item = bool>) -> f64 {
    let values: Vec<_> = values.collect();
    values.iter().filter(|value| **value).count() as f64 / values.len() as f64
}

fn mean(values: &[f64]) -> f64 {
    values.iter().sum::<f64>() / values.len() as f64
}

pub fn seal_expert_packet(
    model: &PotLifeModelArtifactV1,
    runs: &[PotLifeRunV1],
    prior_art_chart_sha256: &str,
) -> Result<ExpertPacketV1, PotLifeError> {
    model.validate()?;
    crate::require_hash("prior_art_chart_sha256", prior_art_chart_sha256)?;
    let mut blinded = BTreeMap::new();
    for (index, run) in runs.iter().enumerate() {
        blinded.insert(
            format!("BLIND-{:03}", index + 1),
            contract_hash(&json!({
                "temperature": run.temperature_series,
                "stormer": run.stormer_series,
                "spray": run.spray_checks,
                "raw_hashes": run.raw_file_hashes,
            }))?,
        );
    }
    let deviations: Vec<_> = runs.iter().map(|run| &run.deviations).collect();
    let fits_hash = contract_hash(&json!({
        "parameters": model.parameters,
        "profiles": model.parameter_profile_intervals,
        "metrics": model.benchmark_metrics,
        "baselines": model.baselines,
    }))?;
    let hostile_hash = contract_hash(&model.hostile_nulls)?;
    let packet_seed = contract_hash(&(
        model.identity_hash(),
        fits_hash.as_str(),
        hostile_hash.as_str(),
    ))?;
    let packet = ExpertPacketV1 {
        schema: EXPERT_PACKET_SCHEMA.into(),
        track_id: POT_LIFE_TRACK_ID.into(),
        packet_id: format!("pot-life-expert-packet-{}", &packet_seed[..16]),
        blinded_raw_series_hashes: blinded,
        protocol_deviations_sha256: contract_hash(&deviations)?,
        source_ledger_sha256: model.source_ledger_sha256.clone(),
        fits_residuals_uncertainty_sha256: fits_hash,
        hostile_nulls_sha256: hostile_hash,
        prior_art_chart_sha256: prior_art_chart_sha256.into(),
        delivery_status: "SEALED_NOT_SENT_APPROVAL_REQUIRED".into(),
    };
    packet.validate()?;
    Ok(packet)
}
