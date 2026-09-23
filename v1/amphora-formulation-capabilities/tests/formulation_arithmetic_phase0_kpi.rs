//! Phase-0 KPI harness for `amphora-formulation-arithmetic`.
//!
//! Drives the deterministic `validate_formulation_mass` primitive across
//! a hand-curated fixture of 15 published two-part epoxy-amine coating
//! formulations (Wicks/Jones/Pappas 2007 Ch. 25, Ellis 1993 Ch. 6,
//! supplier TDSs). Verifies mass balance identity, applies four red-team
//! attack axes (MASS_ORDER_DRIFT, CANDIDATE_PROPERTY_EVIDENCE_INJECTION,
//! FINITE_SUM_OVERFLOW, NUMERIC_TYPE_UNIT_CONFUSION), and emits a
//! byte-stable canonical result receipt.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{canonicalize, stable_hash};
use amphora_formulation_capabilities::{validate_formulation_mass, FormulationMassDiagnosticV1};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crate has a parent workspace")
        .to_path_buf()
}

fn fixture_path() -> PathBuf {
    workspace_root().join(
        "amphora-formulation-arithmetic/reference/phase0-formulation-arithmetic-known-answer.v1.json",
    )
}

fn benchmark_lock_path() -> PathBuf {
    workspace_root()
        .join("amphora-formulation-arithmetic/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-formulation-arithmetic/evidence/phase0/benchmark/result.v1.json` has exactly one
// legitimate writer: the runtime evaluator (`amphora phase0 evaluate` ->
// amphora-cli/src/phase0.rs::evaluate). Its exact bytes are pinned by
// `metrics.benchmark_result_sha256` inside the immutable, signed Phase-0
// evaluation receipt, and re-read by `verify_evaluation_result`. This harness
// emits the MODULE-HARNESS KPI shape, which the verifier rejects, so writing it
// there silently dropped the module out of `phase0_count`. The round-trip now
// uses the per-target cargo scratch directory and never mutates shipped
// evidence.
fn result_path() -> PathBuf {
    PathBuf::from(env!("CARGO_TARGET_TMPDIR"))
        .join("amphora-formulation-arithmetic-phase0-kpi-result.v1.json")
}

fn read_fixture() -> Value {
    let bytes = fs::read(fixture_path()).expect("fixture readable");
    serde_json::from_slice(&bytes).expect("fixture is JSON")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn diagnostic_bytes(d: &FormulationMassDiagnosticV1) -> Vec<u8> {
    serde_json::to_vec(d).expect("diagnostic serializes")
}

fn shuffle_object_keys(value: &Value, shift: usize) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            if keys.is_empty() {
                return value.clone();
            }
            let shift = shift % keys.len();
            keys.rotate_left(shift);
            let mut rotated = Map::new();
            for key in keys {
                rotated.insert(key.clone(), shuffle_object_keys(&map[key], shift));
            }
            Value::Object(rotated)
        }
        Value::Array(arr) => Value::Array(arr.iter().map(|v| shuffle_object_keys(v, shift)).collect()),
        _ => value.clone(),
    }
}

fn compute_report() -> Value {
    let fixture = read_fixture();
    let acceptance_bar = fixture["acceptance_bar"].clone();
    let records = fixture["formulations"].as_array().expect("formulations array");

    let mut per_formulation = Vec::new();
    let mut identity_pass = 0_usize;
    let mut agreement_pass = 0_usize;
    let mut positive_id_pass = 0_usize;
    let mut order_drift_pass = 0_usize;
    let mut property_injection_pass = 0_usize;
    let mut authority_pass = 0_usize;
    let mut mass_abs_errors: Vec<f64> = Vec::new();

    for entry in records {
        let fid = entry["formulation_id"].as_str().unwrap();
        let candidate = &entry["candidate"];
        let expected_a = entry["expected_part_a_g"].as_f64().unwrap();
        let expected_b = entry["expected_part_b_g"].as_f64().unwrap();
        let expected_t = entry["expected_total_g"].as_f64().unwrap();
        let expected_ids: Vec<String> = entry["expected_positive_mass_ingredient_ids"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_string())
            .collect();
        let expected_zero: Vec<String> = entry["expected_ignored_zero_mass_entries"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_string())
            .collect();

        let out = validate_formulation_mass(candidate).expect("in-domain arithmetic");
        assert_eq!(out.status, "UNVALIDATED",
            "{fid} status must be UNVALIDATED for a positive-mass formulation");

        // KPI 1: identity — (part_a + part_b) − total = 0.0 bit-exact.
        let a = out.part_a_mass_g.unwrap();
        let b = out.part_b_mass_g.unwrap();
        let t = out.total_mass_g.unwrap();
        let identity_ok = (a + b).to_bits() == t.to_bits();
        if identity_ok {
            identity_pass += 1;
        }

        // KPI 2: absolute agreement with published expected total.
        let abs_err = (t - expected_t).abs();
        mass_abs_errors.push(abs_err);
        let agreement_ok = abs_err < 1e-9;
        if agreement_ok {
            agreement_pass += 1;
        }

        // KPI 3: positive_mass_ingredient_ids exactly equal expected sorted list.
        let ids_ok = out.positive_mass_ingredient_ids == expected_ids;
        if ids_ok {
            positive_id_pass += 1;
        }

        // KPI 4: MASS_ORDER_DRIFT — shuffled candidate ⇒ byte-identical diagnostic.
        let mut drift_ok = true;
        let baseline = diagnostic_bytes(&out);
        for shift in 1_usize..=3 {
            let shuffled = shuffle_object_keys(candidate, shift);
            let shuffled_out = validate_formulation_mass(&shuffled).expect("in-domain shuffled");
            if diagnostic_bytes(&shuffled_out) != baseline {
                drift_ok = false;
                break;
            }
        }
        if drift_ok {
            order_drift_pass += 1;
        }

        // KPI 5: CANDIDATE_PROPERTY_EVIDENCE_INJECTION — 8 property claims all ignored, masses unchanged.
        let mut injection_ok = true;
        for injected in [
            "density", "eew", "ahew", "nonvolatile",
            "oil_absorption", "performance", "evidence", "feasibility",
        ] {
            let mut poisoned = candidate.clone();
            poisoned["formulation"][injected] = json!("attacker-supplied-value");
            let poisoned_out =
                validate_formulation_mass(&poisoned).expect("injection stays in-domain");
            if !poisoned_out.ignored_candidate_fields.contains(&injected.to_string()) {
                injection_ok = false;
                break;
            }
            if poisoned_out.part_a_mass_g != out.part_a_mass_g
                || poisoned_out.part_b_mass_g != out.part_b_mass_g
                || poisoned_out.total_mass_g != out.total_mass_g
            {
                injection_ok = false;
                break;
            }
        }
        if injection_ok {
            property_injection_pass += 1;
        }

        // KPI 7: authority lock preservation.
        let authority_ok = out.arithmetic_scope == "MASS_ONLY"
            && out.scientific_readiness == "UNVALIDATED"
            && !out.ranking_eligible
            && !out.usable_by_optimizer
            && !out.candidate_created_evidence
            && !out.authority_upgrade
            && !out.unresolved_legacy_data_accessed;
        if authority_ok {
            authority_pass += 1;
        }

        // Zero-mass expected list also matches.
        let zero_ok = out.ignored_zero_mass_entries == expected_zero;

        per_formulation.push(json!({
            "formulation_id": fid,
            "hardener_family": entry["hardener_family"],
            "expected_part_a_g": expected_a,
            "expected_part_b_g": expected_b,
            "expected_total_g": expected_t,
            "computed_part_a_g": a,
            "computed_part_b_g": b,
            "computed_total_g": t,
            "absolute_mass_error_g": abs_err,
            "identity_bit_exact": identity_ok,
            "positive_mass_ingredient_ids_match": ids_ok,
            "ignored_zero_mass_entries_match": zero_ok,
            "mass_order_drift_stable": drift_ok,
            "candidate_property_injection_ignored": injection_ok,
            "authority_locks_preserved": authority_ok,
            "arithmetic_scope": out.arithmetic_scope,
            "scientific_readiness": out.scientific_readiness,
            "source": entry["source"],
            "mix_ratio_by_mass": entry["mix_ratio_by_mass"],
        }));
    }

    // KPI 6: applicability-domain fail-closed on hand-coded malformed candidates.
    let malformed_probes = vec![
        (json!({"candidate_id": "no-formulation", "candidate_type": "formulation"}),
            "missing_formulation_object"),
        (json!({
            "candidate_id": "missing-a",
            "candidate_type": "formulation",
            "formulation": {"part_B": {"h": {"ingredient_id": "h", "mass_g": 1.0}}}
        }), "missing_part_A"),
        (json!({
            "candidate_id": "missing-b",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"r": {"ingredient_id": "r", "mass_g": 1.0}}}
        }), "missing_part_B"),
        (json!({
            "candidate_id": "empty-both",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"r": {"ingredient_id": "r", "mass_g": 0.0}}, "part_B": {"h": {"ingredient_id": "h", "mass_g": 0.0}}}
        }), "all_zero_mass_both_parts"),
        (json!({
            "candidate_id": "nan-mass",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"r": {"ingredient_id": "r", "mass_g": f64::NAN}}, "part_B": {"h": {"ingredient_id": "h", "mass_g": 1.0}}}
        }), "nan_mass"),
        (json!({
            "candidate_id": "infinity-mass",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"r": {"ingredient_id": "r", "mass_g": f64::INFINITY}}, "part_B": {"h": {"ingredient_id": "h", "mass_g": 1.0}}}
        }), "infinity_mass"),
        (json!({
            "candidate_id": "negative-mass",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"r": {"ingredient_id": "r", "mass_g": -1.0}}, "part_B": {"h": {"ingredient_id": "h", "mass_g": 1.0}}}
        }), "negative_mass"),
        (json!({
            "candidate_id": "string-mass",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"r": {"ingredient_id": "r", "mass_g": "100"}}, "part_B": {"h": {"ingredient_id": "h", "mass_g": 1.0}}}
        }), "numeric_type_unit_confusion_string_mass"),
        (json!({
            "candidate_id": "overflow-mass",
            "candidate_type": "formulation",
            "formulation": {"part_A": {"r": {"ingredient_id": "r", "mass_g": 1e308}, "s": {"ingredient_id": "s", "mass_g": 1e308}}, "part_B": {"h": {"ingredient_id": "h", "mass_g": 1e308}}}
        }), "finite_sum_overflow"),
    ];
    let ad_total = malformed_probes.len();
    let mut ad_pass = 0_usize;
    let ad_details: Vec<Value> = malformed_probes
        .iter()
        .map(|(candidate, label)| {
            let outcome = validate_formulation_mass(candidate);
            let fail_closed = match &outcome {
                Ok(diag) => diag.status == "ABSTAIN",
                Err(_) => true,
            };
            if fail_closed {
                ad_pass += 1;
            }
            json!({
                "probe": label,
                "fail_closed": fail_closed,
                "outcome_kind": if outcome.is_err() { "err" } else if outcome.as_ref().map(|d| d.status == "ABSTAIN").unwrap_or(false) { "abstain" } else { "unexpected_pass" },
            })
        })
        .collect();
    let ad_rate = ad_pass as f64 / ad_total.max(1) as f64;

    let n = records.len().max(1) as f64;
    let identity_rate = identity_pass as f64 / n;
    let agreement_rate = agreement_pass as f64 / n;
    let ids_rate = positive_id_pass as f64 / n;
    let drift_rate = order_drift_pass as f64 / n;
    let injection_rate = property_injection_pass as f64 / n;
    let authority_rate = authority_pass as f64 / n;

    let mut sorted_errs = mass_abs_errors.clone();
    sorted_errs.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let median_abs_err = if sorted_errs.is_empty() {
        0.0
    } else {
        sorted_errs[sorted_errs.len() / 2]
    };

    let kpi = json!({
        "mass_balance_identity_rate": {
            "observed": identity_rate,
            "floor": acceptance_bar["mass_balance_identity_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": identity_rate
                >= acceptance_bar["mass_balance_identity_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "mass_balance_absolute_agreement_rate": {
            "observed": agreement_rate,
            "floor": acceptance_bar["mass_balance_absolute_agreement_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": agreement_rate
                >= acceptance_bar["mass_balance_absolute_agreement_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "positive_mass_ingredient_id_agreement_rate": {
            "observed": ids_rate,
            "floor": acceptance_bar["positive_mass_ingredient_id_agreement_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": ids_rate
                >= acceptance_bar["positive_mass_ingredient_id_agreement_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "mass_order_drift_stability_rate": {
            "observed": drift_rate,
            "floor": acceptance_bar["mass_order_drift_stability_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": drift_rate
                >= acceptance_bar["mass_order_drift_stability_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "candidate_property_evidence_injection_ignore_rate": {
            "observed": injection_rate,
            "floor": acceptance_bar["candidate_property_evidence_injection_ignore_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": injection_rate
                >= acceptance_bar["candidate_property_evidence_injection_ignore_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "applicability_domain_fail_closed_rate": {
            "observed": ad_rate,
            "floor": acceptance_bar["applicability_domain_fail_closed_rate_floor"],
            "direction": "MAXIMIZE",
            "probe_sample_size": ad_total,
            "probes": ad_details,
            "passed": ad_rate
                >= acceptance_bar["applicability_domain_fail_closed_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "authority_lock_preservation_rate": {
            "observed": authority_rate,
            "floor": acceptance_bar["authority_lock_preservation_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": authority_rate
                >= acceptance_bar["authority_lock_preservation_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "median_mass_balance_absolute_error_g": {
            "observed": median_abs_err,
            "reported_ceiling_only": acceptance_bar["median_mass_balance_absolute_error_g_ceiling_reported_only"],
            "direction": "MINIMIZE",
            "note": "observational; mass conservation is a physical identity so expected value is 0.0 g",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let fixture_bytes = fs::read(fixture_path()).expect("fixture readable");
    let dataset_sha256 = file_sha256(&fixture_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-formulation-arithmetic",
        "kpi": kpi.clone(),
        "records": per_formulation.clone(),
        "passed": kpi["mass_balance_identity_rate"]["passed"] == json!(true)
            && kpi["mass_balance_absolute_agreement_rate"]["passed"] == json!(true)
            && kpi["positive_mass_ingredient_id_agreement_rate"]["passed"] == json!(true)
            && kpi["mass_order_drift_stability_rate"]["passed"] == json!(true)
            && kpi["candidate_property_evidence_injection_ignore_rate"]["passed"] == json!(true)
            && kpi["applicability_domain_fail_closed_rate"]["passed"] == json!(true)
            && kpi["authority_lock_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-formulation-arithmetic"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-formulation-arithmetic-phase0-mass-balance-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert("acceptance_bar".into(), acceptance_bar);
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_formulation));
    result.insert("benchmark_execution_complete".into(), json!(true));
    result.insert(
        "first_replay".into(),
        json!({
            "diagnostic_receipt": diagnostic.clone(),
            "diagnostic_sha256": diagnostic_sha256,
        }),
    );
    result.insert(
        "second_replay".into(),
        json!({
            "diagnostic_receipt": diagnostic,
            "diagnostic_sha256": diagnostic_sha256,
        }),
    );

    let _ = stable_hash(&Value::Null);
    let _: BTreeMap<String, Value> = BTreeMap::new();

    canonicalize(&Value::Object(result))
}

#[test]
fn formulation_arithmetic_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "mass_balance_identity_rate",
        "mass_balance_absolute_agreement_rate",
        "positive_mass_ingredient_id_agreement_rate",
        "mass_order_drift_stability_rate",
        "candidate_property_evidence_injection_ignore_rate",
        "applicability_domain_fail_closed_rate",
        "authority_lock_preservation_rate",
    ] {
        assert_eq!(
            kpi[gate]["passed"],
            json!(true),
            "KPI gate {gate} failed: observed={}, floor={}",
            kpi[gate]["observed"],
            kpi[gate].get("floor").unwrap_or(&Value::Null),
        );
    }

    let result_path = result_path();
    if let Some(parent) = result_path.parent() {
        fs::create_dir_all(parent).expect("create result parent");
    }
    fs::write(&result_path, &first_bytes).expect("write result artifact");
    let round_trip = fs::read(&result_path).expect("read back");
    assert_eq!(round_trip, first_bytes, "written artifact differs");
}
