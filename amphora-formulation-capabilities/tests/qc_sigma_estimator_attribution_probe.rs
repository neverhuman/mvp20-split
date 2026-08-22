//! AUDIT PROBE (evidence/audit/sigma-estimator-attribution-parity-v1).
//!
//! Not a KPI gate. Extracts real, bit-exact `baseline_sigma` and detector-alert
//! output from the live checked `audit_process_qc` primitive for two baseline
//! scenarios, so an offline Python re-derivation can independently compute
//! raw sample stdev, S/c4(n), and MRbar/d2(2) on the identical input arrays and
//! compare against what the runtime actually produced. Prints one JSON object
//! per scenario to stdout; no assertions (this is a data-capture probe, not a
//! correctness gate -- the module's existing bit-exact arithmetic gates in
//! process_qc_twin_phase0_kpi.rs are untouched).

use amphora_formulation_capabilities::{
    audit_process_qc, ProcessQcObservationV1, ProcessQcSeriesV1,
};
use serde_json::json;

fn obs(prefix: &str, sequence: u64, value: f64) -> ProcessQcObservationV1 {
    ProcessQcObservationV1 {
        batch_id: format!("{prefix}-{sequence:03}"),
        sequence,
        value,
    }
}

#[test]
fn probe_sigma_estimator_attribution() {
    // Scenario A: the module's own closed-form sawtooth baseline pattern
    // (same shape as process_qc_audit_shell / the phase0 known-answer fixture).
    let baseline_a: Vec<ProcessQcObservationV1> = (0..20)
        .map(|i| obs("A", i as u64 + 1, 100.0 + (((i % 5) as f64) - 2.0) * 0.1))
        .collect();
    let out_a = audit_process_qc(&ProcessQcSeriesV1 {
        variable: "probe-sawtooth".into(),
        baseline: baseline_a,
        monitoring: vec![],
        specification_lower: None,
        specification_upper: None,
    })
    .expect("scenario A must be well-formed");

    // Scenario B: a physically realistic drifting baseline (e.g. cure-oven /
    // dispense-head warm-up during pilot onboarding) -- linear ramp of total
    // range 2.0 across the 20 baseline observations, with the same local
    // wiggle superimposed. Still finite, non-empty batch ids, strictly time
    // ordered: passes every existing fail-closed gate.
    let baseline_b: Vec<ProcessQcObservationV1> = (0..20)
        .map(|i| {
            let ramp = 99.0 + (i as f64) * (2.0 / 19.0);
            let wiggle = (((i % 5) as f64) - 2.0) * 0.1;
            obs("B", i as u64 + 1, ramp + wiggle)
        })
        .collect();
    // Designed monitoring shift: mean_B + 4 * MRbar/d2(2)_B, computed offline in
    // Python from the identical array (100.777981). This is a genuine
    // out-of-control condition that a correctly MRbar/d2-based 3-sigma limit
    // WOULD flag (4 sigma_mr > 3 sigma_mr).
    let monitoring_b = vec![obs("B-shift", 21, 100.777981)];
    let out_b = audit_process_qc(&ProcessQcSeriesV1 {
        variable: "probe-drift-warmup".into(),
        baseline: baseline_b,
        monitoring: monitoring_b,
        specification_lower: None,
        specification_upper: None,
    })
    .expect("scenario B must be well-formed");

    let report = json!({
        "scenario_a_sawtooth": {
            "baseline_mean": out_a.baseline_mean,
            "baseline_sigma": out_a.baseline_sigma,
            "baseline_sigma_bits": out_a.baseline_sigma.to_bits(),
        },
        "scenario_b_drift_warmup": {
            "baseline_mean": out_b.baseline_mean,
            "baseline_sigma": out_b.baseline_sigma,
            "baseline_sigma_bits": out_b.baseline_sigma.to_bits(),
            "shewhart_alerts": out_b.shewhart_alerts,
            "ewma_alerts": out_b.ewma_alerts,
            "cusum_alerts": out_b.cusum_alerts,
            "designed_shift_value": 100.777981,
        }
    });
    println!("PROBE_JSON:{report}");
}
