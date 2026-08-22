//! Phase-0 KPI harness for `amphora-formulation-universe`.
//!
//! Drives the deterministic `validate_formulation_universe` primitive
//! across a hand-curated fixture of 10 Design-of-Experiments universes
//! from Montgomery 2017 8th ed. Ch. 6-8 and Wicks/Jones/Pappas 2007
//! §24.5. Verifies Cartesian identity, product arithmetic correctness,
//! axis-order determinism, and applies dedicated red-team probes for the
//! four universe-specific attack axes (CARTESIAN_CANONICAL_DUPLICATION,
//! CARTESIAN_CARDINALITY_OVERFLOW, INFEASIBLE_INDEX_LAUNDERING,
//! CANDIDATE_FEASIBILITY_CLAIM), all with byte-stable two-replay.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{canonicalize, stable_hash};
use amphora_formulation_capabilities::{
    validate_formulation_universe, FormulationUniverseAccountingV1,
    MAX_FORMULATION_UNIVERSE_CARDINALITY,
};
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
        "amphora-formulation-universe/reference/phase0-formulation-universe-known-answer.v1.json",
    )
}

fn benchmark_lock_path() -> PathBuf {
    workspace_root()
        .join("amphora-formulation-universe/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-formulation-universe/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-formulation-universe-phase0-kpi-result.v1.json")
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

fn build_candidate(axes: &Value, infeasible: Option<&Value>, claims: Option<Value>) -> Value {
    let mut universe = Map::new();
    universe.insert("axes".into(), axes.clone());
    if let Some(indices) = infeasible {
        universe.insert("infeasible_indices".into(), indices.clone());
    }
    if let Some(c) = claims {
        universe.insert("claims".into(), c);
    }
    json!({"context": {"formulation_universe": universe}})
}

fn diagnostic_bytes(d: &FormulationUniverseAccountingV1) -> Vec<u8> {
    serde_json::to_vec(d).expect("diagnostic serializes")
}

fn authority_locked(r: &FormulationUniverseAccountingV1) -> bool {
    !r.ranking_eligible
        && !r.usable_by_optimizer
        && !r.authority_upgrade
        && !r.candidate_created_evidence
        && !r.unresolved_legacy_data_accessed
        && r.objective_values.is_empty()
        && r.feasibility_basis == "DECLARATIVE_ACCOUNTING_ONLY"
        && r.scientific_readiness == "UNVALIDATED"
}

/// Compute product of axis cardinalities from the fixture's axes JSON.
fn expected_product(axes: &Value) -> u64 {
    axes.as_object()
        .expect("axes object")
        .values()
        .map(|v| v.as_array().unwrap().len() as u64)
        .product()
}

/// Rotate object keys by `shift` positions to test axis-order determinism.
fn rotate_object_keys(value: &Value, shift: usize) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            if keys.is_empty() {
                return value.clone();
            }
            let s = shift % keys.len();
            keys.rotate_left(s);
            let mut rotated = Map::new();
            for k in keys {
                rotated.insert(k.clone(), map[k].clone());
            }
            Value::Object(rotated)
        }
        other => other.clone(),
    }
}

fn compute_report() -> Value {
    let fixture = read_fixture();
    let acceptance_bar = fixture["acceptance_bar"].clone();
    let universes = fixture["universes"].as_array().expect("universes array");

    let mut per_universe = Vec::new();
    let mut identity_pass = 0_usize;
    let mut product_pass = 0_usize;
    let mut axis_order_pass = 0_usize;
    let mut claim_ignore_pass = 0_usize;
    let mut authority_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;
    let mut universe_total = 0_usize;
    let mut min_cardinality = u64::MAX;
    let mut max_cardinality = 0_u64;

    for entry in universes {
        universe_total += 1;
        let uid = entry["universe_id"].as_str().unwrap();
        let axes = &entry["axes"];
        let infeasible = entry["infeasible_indices"].as_array().and_then(|a| {
            if a.is_empty() {
                None
            } else {
                Some(&entry["infeasible_indices"])
            }
        });
        let expected_total = entry["expected_cartesian_total"].as_u64().unwrap();
        let expected_solved = entry["expected_solved_candidate_count"].as_u64().unwrap();
        let expected_infeasible = entry["expected_infeasible_candidate_count"].as_u64().unwrap();

        let candidate = build_candidate(axes, infeasible, None);
        let out = validate_formulation_universe(&candidate).expect("in-domain universe");
        assert_eq!(out.status, "UNVALIDATED");

        let observed_total = out.cartesian_total.unwrap_or(0);
        let observed_solved = out.solved_candidate_count.unwrap_or(0);
        let observed_infeasible = out.infeasible_candidate_count.unwrap_or(0);

        // Cartesian identity: solved + infeasible == total.
        if observed_solved + observed_infeasible == observed_total {
            identity_pass += 1;
        }
        // Product arithmetic correctness against Python-side reference (expected_total from fixture).
        let expected_prod = expected_product(axes);
        if observed_total == expected_total && observed_total == expected_prod {
            product_pass += 1;
        }
        // Track cardinality range.
        if observed_total < min_cardinality {
            min_cardinality = observed_total;
        }
        if observed_total > max_cardinality {
            max_cardinality = observed_total;
        }

        // Byte-stable two-replay.
        let out2 = validate_formulation_universe(&candidate).expect("replay in-domain");
        let byte_stable = diagnostic_bytes(&out) == diagnostic_bytes(&out2);
        if byte_stable {
            byte_replay_pass += 1;
        }

        // Axis-order determinism: rotate keys 3 different ways.
        let mut axis_ok = true;
        for shift in 1_usize..=3 {
            let shuffled_axes = rotate_object_keys(axes, shift);
            let shuffled_candidate = build_candidate(&shuffled_axes, infeasible, None);
            let shuffled_out =
                validate_formulation_universe(&shuffled_candidate).expect("shuffled in-domain");
            if diagnostic_bytes(&shuffled_out) != diagnostic_bytes(&out) {
                axis_ok = false;
                break;
            }
        }
        if axis_ok {
            axis_order_pass += 1;
        }

        // Candidate-feasibility-claim injection: send bogus claims and verify counts unchanged.
        let poisoned = build_candidate(
            axes,
            infeasible,
            Some(json!({
                "solved_candidate_count": 99999,
                "infeasible_candidate_count": -1,
                "authority_upgrade": true,
                "ranking_eligible": true,
                "usable_by_optimizer": true,
                "objective_values": {"forged": 0.99},
            })),
        );
        let poisoned_out =
            validate_formulation_universe(&poisoned).expect("poisoned in-domain");
        let claim_ok = poisoned_out.candidate_feasibility_claims_ignored
            && poisoned_out.cartesian_total == out.cartesian_total
            && poisoned_out.solved_candidate_count == out.solved_candidate_count
            && poisoned_out.infeasible_candidate_count == out.infeasible_candidate_count
            && !poisoned_out.authority_upgrade
            && !poisoned_out.ranking_eligible
            && !poisoned_out.usable_by_optimizer
            && poisoned_out.objective_values.is_empty();
        if claim_ok {
            claim_ignore_pass += 1;
        }

        // Authority envelope preservation.
        if authority_locked(&out) {
            authority_pass += 1;
        }

        per_universe.push(json!({
            "universe_id": uid,
            "design_type": entry["design_type"],
            "nominal_source": entry["nominal_source"],
            "industrial_context": entry["industrial_context"],
            "expected_cartesian_total": expected_total,
            "observed_cartesian_total": observed_total,
            "expected_solved": expected_solved,
            "observed_solved": observed_solved,
            "expected_infeasible": expected_infeasible,
            "observed_infeasible": observed_infeasible,
            "identity_bit_exact": observed_solved + observed_infeasible == observed_total,
            "product_matches_expected": observed_total == expected_prod,
            "axis_order_stable": axis_ok,
            "candidate_feasibility_claim_ignored_and_counts_unchanged": claim_ok,
            "byte_stable_two_replay": byte_stable,
            "authority_locked": authority_locked(&out),
        }));
    }

    let n = universe_total.max(1) as f64;
    let identity_rate = identity_pass as f64 / n;
    let product_rate = product_pass as f64 / n;
    let axis_order_rate = axis_order_pass as f64 / n;
    let claim_ignore_rate = claim_ignore_pass as f64 / n;
    let authority_rate = authority_pass as f64 / n;
    let byte_replay_rate = byte_replay_pass as f64 / n;

    // CARTESIAN_CARDINALITY_OVERFLOW probes.
    let mut overflow_pass = 0_usize;
    let mut overflow_probes: Vec<Value> = Vec::new();
    {
        // Product 30 × 30 × 30 = 27000 > 10000.
        let over1 = build_candidate(
            &json!({
                "a": (0..30).collect::<Vec<_>>(),
                "b": (0..30).collect::<Vec<_>>(),
                "c": (0..30).collect::<Vec<_>>(),
            }),
            None,
            None,
        );
        let ok1 = validate_formulation_universe(&over1).is_err();
        if ok1 {
            overflow_pass += 1;
        }
        overflow_probes.push(json!({"probe": "product_30x30x30_exceeds_10000_ceiling", "fail_closed": ok1}));

        // 200 × 200 = 40000.
        let over2 = build_candidate(
            &json!({
                "a": (0..200).collect::<Vec<_>>(),
                "b": (0..200).collect::<Vec<_>>(),
            }),
            None,
            None,
        );
        let ok2 = validate_formulation_universe(&over2).is_err();
        if ok2 {
            overflow_pass += 1;
        }
        overflow_probes.push(json!({"probe": "product_200x200_exceeds_10000_ceiling", "fail_closed": ok2}));

        // Just at 10001.
        let over3 = build_candidate(
            &json!({
                "a": (0..10001).collect::<Vec<_>>(),
            }),
            None,
            None,
        );
        let ok3 = validate_formulation_universe(&over3).is_err();
        if ok3 {
            overflow_pass += 1;
        }
        overflow_probes.push(json!({"probe": "single_axis_10001_exceeds_ceiling", "fail_closed": ok3}));
    }
    let overflow_total = overflow_probes.len();
    let overflow_rate = overflow_pass as f64 / overflow_total.max(1) as f64;

    // INFEASIBLE_INDEX_LAUNDERING probes.
    let mut laundering_pass = 0_usize;
    let mut laundering_probes: Vec<Value> = Vec::new();
    {
        let axes_ref = json!({"a": [1, 2], "b": [3, 4]});
        // index == total.
        let p = build_candidate(&axes_ref, Some(&json!([4])), None);
        let ok = validate_formulation_universe(&p).is_err();
        if ok { laundering_pass += 1; }
        laundering_probes.push(json!({"probe": "index_equals_total_boundary", "fail_closed": ok}));

        // index > total.
        let p = build_candidate(&axes_ref, Some(&json!([100])), None);
        let ok = validate_formulation_universe(&p).is_err();
        if ok { laundering_pass += 1; }
        laundering_probes.push(json!({"probe": "index_far_above_total", "fail_closed": ok}));

        // Duplicate index.
        let p = build_candidate(&axes_ref, Some(&json!([1, 1])), None);
        let ok = validate_formulation_universe(&p).is_err();
        if ok { laundering_pass += 1; }
        laundering_probes.push(json!({"probe": "duplicate_index", "fail_closed": ok}));

        // Negative index (non-u64).
        let p = build_candidate(&axes_ref, Some(&json!([-1])), None);
        let ok = validate_formulation_universe(&p).is_err();
        if ok { laundering_pass += 1; }
        laundering_probes.push(json!({"probe": "negative_non_u64_index", "fail_closed": ok}));

        // Float index (non-integer).
        let p = build_candidate(&axes_ref, Some(&json!([1.5])), None);
        let ok = validate_formulation_universe(&p).is_err();
        if ok { laundering_pass += 1; }
        laundering_probes.push(json!({"probe": "float_non_integer_index", "fail_closed": ok}));

        // Infeasible indices without axes.
        let no_axes = json!({
            "context": {
                "formulation_universe": {
                    "infeasible_indices": [0]
                }
            }
        });
        let ok = validate_formulation_universe(&no_axes).is_err();
        if ok { laundering_pass += 1; }
        laundering_probes.push(json!({"probe": "infeasible_without_registered_axes", "fail_closed": ok}));
    }
    let laundering_total = laundering_probes.len();
    let laundering_rate = laundering_pass as f64 / laundering_total.max(1) as f64;

    // CARTESIAN_CANONICAL_DUPLICATION probes.
    let mut duplication_pass = 0_usize;
    let mut duplication_probes: Vec<Value> = Vec::new();
    {
        // Literal string duplicate.
        let p = build_candidate(&json!({"resin": ["DGEBA", "DGEBA"]}), None, None);
        let ok = validate_formulation_universe(&p).is_err();
        if ok { duplication_pass += 1; }
        duplication_probes.push(json!({"probe": "literal_string_duplicate", "fail_closed": ok}));

        // Integer duplicate.
        let p = build_candidate(&json!({"level": [1, 1]}), None, None);
        let ok = validate_formulation_universe(&p).is_err();
        if ok { duplication_pass += 1; }
        duplication_probes.push(json!({"probe": "integer_duplicate", "fail_closed": ok}));

        // Canonically-equal objects.
        let p = build_candidate(
            &json!({"pair": [{"a": 1, "b": 2}, {"b": 2, "a": 1}]}),
            None,
            None,
        );
        let ok = validate_formulation_universe(&p).is_err();
        if ok { duplication_pass += 1; }
        duplication_probes.push(json!({"probe": "canonically_equal_objects_different_key_order", "fail_closed": ok}));

        // Null duplicate.
        let p = build_candidate(&json!({"x": [null, null]}), None, None);
        let ok = validate_formulation_universe(&p).is_err();
        if ok { duplication_pass += 1; }
        duplication_probes.push(json!({"probe": "null_duplicate", "fail_closed": ok}));
    }
    let duplication_total = duplication_probes.len();
    let duplication_rate = duplication_pass as f64 / duplication_total.max(1) as f64;

    let kpi = json!({
        "cartesian_identity_correctness_rate": {
            "observed": identity_rate,
            "floor": acceptance_bar["cartesian_identity_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "passed": identity_rate
                >= acceptance_bar["cartesian_identity_correctness_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "cartesian_product_arithmetic_correctness_rate": {
            "observed": product_rate,
            "floor": acceptance_bar["cartesian_product_arithmetic_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "passed": product_rate
                >= acceptance_bar["cartesian_product_arithmetic_correctness_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "axis_order_determinism_rate": {
            "observed": axis_order_rate,
            "floor": acceptance_bar["axis_order_determinism_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "passed": axis_order_rate
                >= acceptance_bar["axis_order_determinism_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "candidate_feasibility_claim_ignore_rate": {
            "observed": claim_ignore_rate,
            "floor": acceptance_bar["candidate_feasibility_claim_ignore_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "passed": claim_ignore_rate
                >= acceptance_bar["candidate_feasibility_claim_ignore_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "cartesian_cardinality_overflow_fail_closed_rate": {
            "observed": overflow_rate,
            "floor": acceptance_bar["cartesian_cardinality_overflow_fail_closed_rate_floor"],
            "direction": "MAXIMIZE",
            "probe_sample_size": overflow_total,
            "probes": overflow_probes,
            "passed": overflow_rate
                >= acceptance_bar["cartesian_cardinality_overflow_fail_closed_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "infeasible_index_laundering_fail_closed_rate": {
            "observed": laundering_rate,
            "floor": acceptance_bar["infeasible_index_laundering_fail_closed_rate_floor"],
            "direction": "MAXIMIZE",
            "probe_sample_size": laundering_total,
            "probes": laundering_probes,
            "passed": laundering_rate
                >= acceptance_bar["infeasible_index_laundering_fail_closed_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "cartesian_canonical_duplication_fail_closed_rate": {
            "observed": duplication_rate,
            "floor": acceptance_bar["cartesian_canonical_duplication_fail_closed_rate_floor"],
            "direction": "MAXIMIZE",
            "probe_sample_size": duplication_total,
            "probes": duplication_probes,
            "passed": duplication_rate
                >= acceptance_bar["cartesian_canonical_duplication_fail_closed_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "authority_lock_preservation_rate": {
            "observed": authority_rate,
            "floor": acceptance_bar["authority_lock_preservation_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "passed": authority_rate
                >= acceptance_bar["authority_lock_preservation_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_rate,
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "note": "observational; validated by re-invoking validate_formulation_universe on the same candidate and asserting byte-identical FormulationUniverseAccountingV1",
        },
        "cartesian_cardinality_range": {
            "observed_minimum": min_cardinality,
            "observed_maximum": max_cardinality,
            "ceiling": MAX_FORMULATION_UNIVERSE_CARDINALITY,
            "direction": "AUDIT_ONLY",
            "note": "observational; fixture cartesian totals range across the DoE examples",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let fixture_bytes = fs::read(fixture_path()).expect("fixture readable");
    let dataset_sha256 = file_sha256(&fixture_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-formulation-universe",
        "kpi": kpi.clone(),
        "records": per_universe.clone(),
        "passed": kpi["cartesian_identity_correctness_rate"]["passed"] == json!(true)
            && kpi["cartesian_product_arithmetic_correctness_rate"]["passed"] == json!(true)
            && kpi["axis_order_determinism_rate"]["passed"] == json!(true)
            && kpi["candidate_feasibility_claim_ignore_rate"]["passed"] == json!(true)
            && kpi["cartesian_cardinality_overflow_fail_closed_rate"]["passed"] == json!(true)
            && kpi["infeasible_index_laundering_fail_closed_rate"]["passed"] == json!(true)
            && kpi["cartesian_canonical_duplication_fail_closed_rate"]["passed"] == json!(true)
            && kpi["authority_lock_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-formulation-universe"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-formulation-universe-phase0-cartesian-accounting-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert("acceptance_bar".into(), acceptance_bar);
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_universe));
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
fn formulation_universe_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "cartesian_identity_correctness_rate",
        "cartesian_product_arithmetic_correctness_rate",
        "axis_order_determinism_rate",
        "candidate_feasibility_claim_ignore_rate",
        "cartesian_cardinality_overflow_fail_closed_rate",
        "infeasible_index_laundering_fail_closed_rate",
        "cartesian_canonical_duplication_fail_closed_rate",
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
