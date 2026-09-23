//! Numeric validation for campaign item W-T-SOLV.
//!
//! Calls the REAL `amphora_solvency_score::hansen_ra_squared` /
//! `hansen_red` functions (not a reimplementation) against every
//! solvent x polymer pair in the module's own Hansen-2007-cited
//! known-answer fixture, and reports computed Ra / RED next to the
//! fixture's cited published HSP inputs and observed compatibility
//! (itself sourced to Hansen 2nd ed. Fig 5.1 / Table A.1 / A.2 and
//! supplier TDS solvency charts, per the fixture's own `sources` field).
use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_solvency_score::{hansen_ra_squared, hansen_red};
use serde_json::{json, Value};

fn fixture_path() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("reference/phase0-solvency-known-answer.v1.json")
}

fn hsp(value: &Value, key: &str) -> f64 {
    value[key].as_f64().expect("HSP number present")
}

fn main() {
    let bytes = fs::read(fixture_path()).expect("fixture readable");
    let fixture: Value = serde_json::from_slice(&bytes).expect("fixture is JSON");

    let mut polymers: BTreeMap<String, Value> = BTreeMap::new();
    for polymer in fixture["polymers"].as_array().unwrap() {
        polymers.insert(polymer["polymer_id"].as_str().unwrap().to_string(), polymer.clone());
    }
    let mut solvents: BTreeMap<String, Value> = BTreeMap::new();
    for solvent in fixture["solvents"].as_array().unwrap() {
        solvents.insert(solvent["solvent_id"].as_str().unwrap().to_string(), solvent.clone());
    }

    let mut rows: Vec<Value> = Vec::new();
    for pair in fixture["pairs"].as_array().unwrap() {
        let polymer_id = pair["polymer_id"].as_str().unwrap();
        let solvent_id = pair["solvent_id"].as_str().unwrap();
        let observed = pair["observed_compatible"].as_bool().unwrap();
        let polymer = &polymers[polymer_id];
        let solvent = &solvents[solvent_id];

        let s_dd = hsp(solvent, "delta_d_mpa_half");
        let s_dp = hsp(solvent, "delta_p_mpa_half");
        let s_dh = hsp(solvent, "delta_h_mpa_half");
        let p_dd = hsp(polymer, "delta_d_mpa_half");
        let p_dp = hsp(polymer, "delta_p_mpa_half");
        let p_dh = hsp(polymer, "delta_h_mpa_half");
        let p_r = hsp(polymer, "interaction_radius_r");

        let ra_squared = hansen_ra_squared(s_dd, s_dp, s_dh, p_dd, p_dp, p_dh)
            .expect("Ra^2 computable for in-domain fixture pair");
        let ra = ra_squared.sqrt();
        let red = hansen_red(s_dd, s_dp, s_dh, p_dd, p_dp, p_dh, p_r)
            .expect("RED computable for in-domain fixture pair");
        assert!((red - ra / p_r).abs() < 1e-12, "RED must equal Ra/R0 exactly");
        let predicted_compatible = red < 1.0;

        rows.push(json!({
            "pair_id": pair["pair_id"],
            "polymer_id": polymer_id,
            "solvent_id": solvent_id,
            "solvent_hsp_mpa_half": {"dd": s_dd, "dp": s_dp, "dh": s_dh},
            "solvent_hsp_source": solvent["sources"],
            "polymer_hsp_mpa_half": {"dd": p_dd, "dp": p_dp, "dh": p_dh, "r0": p_r},
            "polymer_hsp_source": polymer["sources"],
            "computed_ra_mpa_half": ra,
            "computed_red": red,
            "predicted_compatible_red_lt_1": predicted_compatible,
            "observed_compatible_published": observed,
            "observed_source": pair["sources"],
            "prediction_matches_published_label": predicted_compatible == observed,
        }));
    }

    let n = rows.len();
    let n_correct = rows.iter().filter(|r| r["prediction_matches_published_label"] == json!(true)).count();
    let n_polymers = polymers.len();
    let n_solvents = solvents.len();

    let report = json!({
        "schema": "amphora.solvency-score-hsp-numeric-validation.v1",
        "campaign_item_id": "W-T-SOLV",
        "function_under_test": ["amphora_solvency_score::hansen_ra_squared", "amphora_solvency_score::hansen_red"],
        "formula_cited": "Ra^2 = 4*(dD1-dD2)^2 + (dP1-dP2)^2 + (dH1-dH2)^2; RED = Ra/R0 (Hansen, Hansen Solubility Parameters: A User's Handbook, 2nd ed. 2007, ISBN 9780849372483)",
        "fixture_path": "amphora-solvency-score/reference/phase0-solvency-known-answer.v1.json",
        "n_pairs": n,
        "n_polymers": n_polymers,
        "n_solvents": n_solvents,
        "n_pairs_prediction_matches_published_label": n_correct,
        "classification_accuracy": n_correct as f64 / n as f64,
        "per_pair": rows,
    });
    println!("{}", serde_json::to_string_pretty(&report).unwrap());
}
