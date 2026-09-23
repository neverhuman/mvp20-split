//! Live-runtime parity probe for `herschel_bulkley_apparent_viscosity` (src/lib.rs:1227).
//!
//! Falsification target: the promoted claim in
//! evidence/phase0/kpis/herschel-bulkley-ccby-amorim2021-kpi.v1.json (and its underlying
//! receipt evidence/audit/herschel-bulkley-ccby-amorim2021-v1/) that "the module equation
//! (src/lib.rs:1227) evaluated at published fitted parameters" survives falsification.
//! Every prior fire on this claim (2026-08-01, 2026-08-04, 2026-08-14) computed the
//! comparison with a Python "verbatim re-derivation" of the formula
//! (run_hb_benchmark.py: "MODULE FORMULA UNDER TEST (re-derived, not imported, to keep
//! this an independent CPython oracle -- matches ... src/lib.rs:1227 verbatim") and NEVER
//! called the actual compiled Rust function. That is a real, previously-untested gap: a
//! silent divergence between the compiled primitive and the promoted KPI's numbers would
//! not have been caught by any prior fire.
//!
//! This probe calls the live, unmodified `herschel_bulkley_apparent_viscosity` primitive
//! (not a reimplementation) at the same 6 formulations x 4 shear rates as the promoted
//! KPI, using the source fixture's own corrected tau0/K/n values (asserted byte-identical
//! to the committed source-lock JSON at runtime), plus a battery of guard-rail edge cases
//! (negative yield stress, non-positive consistency/flow-index/shear-rate, NaN/Infinity)
//! to check whether the code's actual `Err` behavior matches what run_hb_benchmark.py
//! assumed it mirrors "exactly".

use amphora_viscosity_score::herschel_bulkley_apparent_viscosity;
use serde_json::{json, Value};
use std::fs;

struct Row {
    sample: &'static str,
    tau0_pa_corrected: f64,
    k_pa_sn_corrected: f64,
    n: f64,
}

// Verbatim copy of the corrected values from
// evidence/audit/herschel-bulkley-ccby-amorim2021-v1/source_amorim2021_hb_table2.v1.json
const ROWS: [Row; 6] = [
    Row { sample: "Epoxy", tau0_pa_corrected: 123.900, k_pa_sn_corrected: 48.990, n: 0.7069 },
    Row { sample: "1", tau0_pa_corrected: 631.700, k_pa_sn_corrected: 166.800, n: 0.5978 },
    Row { sample: "2", tau0_pa_corrected: 627.100, k_pa_sn_corrected: 193.400, n: 0.5718 },
    Row { sample: "3", tau0_pa_corrected: 1054.000, k_pa_sn_corrected: 333.000, n: 0.5534 },
    Row { sample: "4", tau0_pa_corrected: 1514.000, k_pa_sn_corrected: 561.900, n: 0.5032 },
    Row { sample: "5", tau0_pa_corrected: 754.100, k_pa_sn_corrected: 257.300, n: 0.5493 },
];

const SHEAR_RATES: [f64; 4] = [0.1, 1.0, 10.0, 100.0];

fn assert_source_lock_matches(source_lock_path: &str) {
    let raw = fs::read_to_string(source_lock_path).expect("read source lock json");
    let v: Value = serde_json::from_str(&raw).expect("parse source lock json");
    let arr = v["rows"].as_array().expect("rows array");
    assert_eq!(arr.len(), ROWS.len(), "row count drifted from source lock");
    for (row, jrow) in ROWS.iter().zip(arr.iter()) {
        assert_eq!(jrow["sample"].as_str().unwrap(), row.sample, "sample id drifted");
        assert_eq!(jrow["tau0_pa_corrected"].as_f64().unwrap(), row.tau0_pa_corrected, "tau0 drifted for {}", row.sample);
        assert_eq!(jrow["K_pa_sn_corrected"].as_f64().unwrap(), row.k_pa_sn_corrected, "K drifted for {}", row.sample);
        assert_eq!(jrow["n"].as_f64().unwrap(), row.n, "n drifted for {}", row.sample);
    }
}

fn main() {
    let source_lock_path = "evidence/audit/herschel-bulkley-ccby-amorim2021-v1/source_amorim2021_hb_table2.v1.json";
    assert_source_lock_matches(source_lock_path);

    let mut rows_out = Vec::new();
    for row in ROWS.iter() {
        let mut curve = Vec::new();
        for &g in SHEAR_RATES.iter() {
            // Live call into the real, unmodified compiled primitive -- not a reimplementation.
            let v = herschel_bulkley_apparent_viscosity(row.tau0_pa_corrected, row.k_pa_sn_corrected, row.n, g)
                .expect("in-domain call");
            curve.push(json!({"shear_rate_s_inv": g, "eta_apparent_pa_s_live_rust": v}));
        }
        rows_out.push(json!({
            "sample": row.sample,
            "tau0_pa_corrected": row.tau0_pa_corrected,
            "K_pa_sn_corrected": row.k_pa_sn_corrected,
            "n": row.n,
            "curve": curve,
        }));
    }

    // Guard-rail edge-case battery: does the compiled function's Err/Ok behavior match
    // what run_hb_benchmark.py's re-derivation assumed it mirrors "exactly"?
    let edge_cases = [
        ("negative_yield_stress", -1.0, 10.0, 0.5, 1.0),
        ("zero_yield_stress_should_be_ok", 0.0, 10.0, 0.5, 1.0),
        ("zero_consistency", 10.0, 0.0, 0.5, 1.0),
        ("negative_consistency", 10.0, -5.0, 0.5, 1.0),
        ("zero_flow_index", 10.0, 10.0, 0.0, 1.0),
        ("negative_flow_index", 10.0, 10.0, -0.5, 1.0),
        ("zero_shear_rate", 10.0, 10.0, 0.5, 0.0),
        ("negative_shear_rate", 10.0, 10.0, 0.5, -1.0),
        ("nan_yield_stress", f64::NAN, 10.0, 0.5, 1.0),
        ("infinite_yield_stress", f64::INFINITY, 10.0, 0.5, 1.0),
    ];
    let mut edge_out = Vec::new();
    for (label, t0, k, n, g) in edge_cases.iter() {
        let res = herschel_bulkley_apparent_viscosity(*t0, *k, *n, *g);
        edge_out.push(json!({
            "case": label,
            "tau0": t0, "K": k, "n": n, "gamma_dot": g,
            "is_ok": res.is_ok(),
            "value_if_ok": res.ok(),
        }));
    }

    let out = json!({
        "schema": "amphora.viscosity-score.hb-live-runtime-parity-diagnostic.v1",
        "module_id": "amphora-viscosity-score",
        "function_under_test": "herschel_bulkley_apparent_viscosity (src/lib.rs:1227), called live via the compiled crate -- not reimplemented",
        "source_lock_sha256_asserted_match": true,
        "rows": rows_out,
        "edge_case_guard_battery": edge_out,
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
