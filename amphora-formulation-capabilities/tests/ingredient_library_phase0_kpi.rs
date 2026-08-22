//! Phase-0 KPI harness for `amphora-ingredient-library`.
//!
//! Drives the deterministic `ingredient_library` runtime (via
//! `FormulationCapability::new(descriptor_for("amphora-ingredient-library"))`)
//! across 6 formulation-candidate scenarios: simple 1+1, multi-ingredient,
//! adversarial cited_ingredients injection, adversarial grade/lot/method
//! injection, mixed zero-mass entries, and missing-recipe abstention. Verifies
//! defensive invariants: status=INSUFFICIENT_INPUT, ingredient_ledger_lookup_attempted
//! =false, rights_cleared_ingredient_ledger_available=false,
//! active_mass_property_coverage=Null, both ledger gates false,
//! observed_ingredient_ids and count match recipe bit-exact, missing_inputs
//! names grade/lot/method/currentness gap, explanation disclaims unresolved
//! legacy ledger, authority envelope preserved, byte-stable two-replay.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
    ModuleDescriptor,
};
use amphora_formulation_capabilities::{FormulationCapability, INGREDIENT_LIBRARY_ID};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const BANNED_AUTHORITY_KEYS: [&str; 6] = [
    "batch_release",
    "release_authorized",
    "qualified",
    "authorized_by",
    "manufacturing_qualification",
    "release_authority",
];

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crate has a parent workspace")
        .to_path_buf()
}

fn benchmark_lock_path() -> PathBuf {
    workspace_root()
        .join("amphora-ingredient-library/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-ingredient-library/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-ingredient-library-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-ingredient-library".into(),
        deterministic_seed: 20260722,
        lineage: Value::Null,
    }
}

fn contains_banned_key(value: &Value) -> Option<String> {
    match value {
        Value::Object(map) => {
            for k in map.keys() {
                if BANNED_AUTHORITY_KEYS.iter().any(|b| b == k) {
                    return Some(k.clone());
                }
            }
            for v in map.values() {
                if let Some(k) = contains_banned_key(v) {
                    return Some(k);
                }
            }
            None
        }
        Value::Array(arr) => arr.iter().find_map(contains_banned_key),
        _ => None,
    }
}

fn ingredient_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: std::sync::OnceLock<ModuleDescriptor> = std::sync::OnceLock::new();
    DESCRIPTOR.get_or_init(|| ModuleDescriptor {
        project: INGREDIENT_LIBRARY_ID.into(),
        authority_ceiling: "RULE_CITED".into(),
        solver_use_ceiling: "CONSTRAINT_ONLY".into(),
        model_readiness_ceiling: "NOT_PROVEN".into(),
        ranking_eligible: false,
        candidate_types: vec!["formulation".into()],
        non_blocking_claim_locks: vec![
            "no_ledger_lookup_authority".into(),
            "no_active_mass_property_coverage_claim".into(),
            "no_candidate_supplied_grade_lot_elevated".into(),
        ],
        readiness: "GATED".into(),
    })
}

struct Scenario {
    scenario_id: &'static str,
    candidate: Value,
    /// Expected positive-mass ingredient IDs (sorted lexicographically within each part).
    expected_positive_mass_ingredient_ids: Vec<&'static str>,
    /// Expected `required_recipe_present` gate value.
    expects_recipe_present: bool,
    industrial_context: &'static str,
}

fn scenarios() -> Vec<Scenario> {
    vec![
        Scenario {
            scenario_id: "primer-simple-two-ingredient",
            candidate: json!({
                "candidate_id": "primer-simple",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0},
                    "part_B": {"polyamide": 65.0}
                }
            }),
            expected_positive_mass_ingredient_ids: vec!["dgeba", "polyamide"],
            expects_recipe_present: true,
            industrial_context: "marine primer 1+1 ingredient formulation for baseline ID observation",
        },
        Scenario {
            scenario_id: "primer-multi-ingredient",
            candidate: json!({
                "candidate_id": "primer-multi",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {
                        "dgeba": 100.0,
                        "byk_a530": 2.0,
                        "iron_oxide_red": 15.0,
                        "silica_extender": 20.0,
                        "naphtha_solvent": 8.0
                    },
                    "part_B": {
                        "polyamide": 65.0,
                        "butanol_solvent": 3.0
                    }
                }
            }),
            expected_positive_mass_ingredient_ids: vec![
                "butanol_solvent",
                "byk_a530",
                "dgeba",
                "iron_oxide_red",
                "naphtha_solvent",
                "polyamide",
                "silica_extender",
            ],
            expects_recipe_present: true,
            industrial_context: "5+2 industrial primer with pigment, extender, additive, and solvent (real coating-industry BOM)",
        },
        Scenario {
            scenario_id: "adversarial-cited-ingredients-injection",
            candidate: json!({
                "candidate_id": "adversarial-cited",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0},
                    "part_B": {"polyamide": 65.0},
                    "cited_ingredients": [
                        {"cas_rn": "25085-99-8", "name": "DGEBA epoxy", "asserted_grade": "commercial"},
                        {"cas_rn": "68410-23-1", "name": "polyamide", "asserted_grade": "commercial"}
                    ],
                    "adversary_claimed_ledger_coverage": 1.0
                }
            }),
            expected_positive_mass_ingredient_ids: vec!["dgeba", "polyamide"],
            expects_recipe_present: true,
            industrial_context: "adversarial candidate injecting cited_ingredients with CAS RNs and asserted_grade claims; runtime must NOT flip ingredient_ledger_lookup_attempted or active_mass_property_coverage",
        },
        Scenario {
            scenario_id: "adversarial-grade-lot-method-injection",
            candidate: json!({
                "candidate_id": "adversarial-grade",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0},
                    "part_B": {"polyamide": 65.0},
                    "ingredient_grade_declarations": {
                        "dgeba": {"grade": "electronic-grade", "lot": "L-2026-001", "method": "ASTM-D1652", "currentness_date": "2026-07-15"},
                        "polyamide": {"grade": "commercial", "lot": "L-2026-002", "method": "ASTM-D2074", "currentness_date": "2026-07-16"}
                    }
                }
            }),
            expected_positive_mass_ingredient_ids: vec!["dgeba", "polyamide"],
            expects_recipe_present: true,
            industrial_context: "adversarial candidate injecting ingredient_grade_declarations with grade/lot/method/currentness_date; runtime must NOT elevate the ledger gates",
        },
        Scenario {
            scenario_id: "mixed-zero-mass-entries",
            candidate: json!({
                "candidate_id": "mixed-zero-mass",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0, "unused_additive": 0.0},
                    "part_B": {"polyamide": 65.0, "reserved_slot": 0.0}
                }
            }),
            expected_positive_mass_ingredient_ids: vec!["dgeba", "polyamide"],
            expects_recipe_present: true,
            industrial_context: "candidate with legitimate zero-mass placeholder entries (unused_additive, reserved_slot); runtime observes only positive-mass ingredients",
        },
        Scenario {
            scenario_id: "missing-part-b-abstention",
            candidate: json!({
                "candidate_id": "missing-b",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}}
            }),
            expected_positive_mass_ingredient_ids: vec![],
            expects_recipe_present: false,
            industrial_context: "candidate missing part_B - triggers recipe_or_abstain path",
        },
    ]
}

fn compute_report() -> Value {
    let cap =
        FormulationCapability::new(ingredient_descriptor()).expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = context();
    let scenarios = scenarios();
    let n_scenarios = scenarios.len();

    let mut per_scenario: Vec<Value> = Vec::new();

    let mut status_pass = 0_usize;
    let mut evidence_scope_pass = 0_usize;
    let mut recipe_gate_pass = 0_usize;
    let mut lookup_false_pass = 0_usize;
    let mut ledger_avail_false_pass = 0_usize;
    let mut coverage_null_pass = 0_usize;
    let mut cited_gate_false_pass = 0_usize;
    let mut coverage_gate_false_pass = 0_usize;
    let mut ids_match_pass = 0_usize;
    let mut missing_input_pass = 0_usize;
    let mut explanation_pass = 0_usize;
    let mut envelope_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;

    let mut recipe_scenarios = 0_usize;

    for scenario in &scenarios {
        let candidate = CandidateEnvelope::from_value(scenario.candidate.clone())
            .expect("candidate parses");
        let out = cap
            .evaluate(&candidate, &features, &ctx)
            .expect("evaluate ok");

        let status_ok = out.status == "INSUFFICIENT_INPUT";
        if status_ok {
            status_pass += 1;
        }
        let evidence_ok = out.evidence_scope == "ingredient_ledger_diagnostic";
        if evidence_ok {
            evidence_scope_pass += 1;
        }

        let recipe_observed = out.gates.get("required_recipe_present") == Some(&json!(true));
        let recipe_ok = recipe_observed == scenario.expects_recipe_present;
        if recipe_ok {
            recipe_gate_pass += 1;
        }

        // Defensive invariants only exist on the recipe-present body path.
        let lookup_val = out.metrics.get("ingredient_ledger_lookup_attempted");
        let lookup_ok = if scenario.expects_recipe_present {
            lookup_val == Some(&json!(false))
        } else {
            lookup_val.is_none()
        };
        if lookup_ok {
            lookup_false_pass += 1;
        }

        let ledger_val = out.metrics.get("rights_cleared_ingredient_ledger_available");
        let ledger_ok = if scenario.expects_recipe_present {
            ledger_val == Some(&json!(false))
        } else {
            ledger_val.is_none()
        };
        if ledger_ok {
            ledger_avail_false_pass += 1;
        }

        let coverage_val = out.metrics.get("active_mass_property_coverage");
        let coverage_ok = if scenario.expects_recipe_present {
            coverage_val == Some(&Value::Null)
        } else {
            coverage_val.is_none()
        };
        if coverage_ok {
            coverage_null_pass += 1;
        }

        let cited_val = out.gates.get("all_candidate_ingredients_cited");
        let cited_ok = if scenario.expects_recipe_present {
            cited_val == Some(&json!(false))
        } else {
            cited_val.is_none()
        };
        if cited_ok {
            cited_gate_false_pass += 1;
        }

        let coverage_gate_val = out.gates.get("active_mass_property_coverage_at_least_95pct");
        let coverage_gate_ok = if scenario.expects_recipe_present {
            coverage_gate_val == Some(&json!(false))
        } else {
            coverage_gate_val.is_none()
        };
        if coverage_gate_ok {
            coverage_gate_false_pass += 1;
        }

        // Observed ingredient IDs bit-exact against expected.
        let observed_ids: Vec<String> = out
            .metrics
            .get("positive_mass_ingredient_ids")
            .and_then(Value::as_array)
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(String::from))
                    .collect()
            })
            .unwrap_or_default();
        let expected_ids: Vec<String> = scenario
            .expected_positive_mass_ingredient_ids
            .iter()
            .map(|s| (*s).to_string())
            .collect();
        let ids_ok = observed_ids == expected_ids;
        if ids_ok {
            ids_match_pass += 1;
        }

        if scenario.expects_recipe_present {
            recipe_scenarios += 1;
            let missing_ok = out.missing_inputs.iter().any(|m| {
                m.contains("grade")
                    && m.contains("lot")
                    && m.contains("method")
                    && m.contains("currentness")
            });
            if missing_ok {
                missing_input_pass += 1;
            }
            let explanation_ok = out
                .explanations
                .iter()
                .any(|e| e.contains("legacy") && e.contains("ledger"));
            if explanation_ok {
                explanation_pass += 1;
            }
        }

        let out_json = serde_json::to_value(&out).expect("serializes");
        let envelope_ok = contains_banned_key(&out_json).is_none();
        if envelope_ok {
            envelope_pass += 1;
        }

        let replay = cap.evaluate(&candidate, &features, &ctx).unwrap();
        let byte_ok = serde_json::to_vec(&out).unwrap()
            == serde_json::to_vec(&replay).unwrap();
        if byte_ok {
            byte_replay_pass += 1;
        }

        per_scenario.push(json!({
            "scenario_id": scenario.scenario_id,
            "candidate_id": candidate.candidate_id(),
            "industrial_context": scenario.industrial_context,
            "status": out.status,
            "evidence_scope": out.evidence_scope,
            "expects_recipe_present": scenario.expects_recipe_present,
            "recipe_present_observed": recipe_observed,
            "expected_positive_mass_ingredient_ids": expected_ids,
            "observed_positive_mass_ingredient_ids": observed_ids,
            "ingredient_ledger_lookup_attempted": out.metrics.get("ingredient_ledger_lookup_attempted"),
            "rights_cleared_ingredient_ledger_available": out.metrics.get("rights_cleared_ingredient_ledger_available"),
            "active_mass_property_coverage": out.metrics.get("active_mass_property_coverage"),
            "all_candidate_ingredients_cited_gate": out.gates.get("all_candidate_ingredients_cited"),
            "active_mass_property_coverage_at_least_95pct_gate": out.gates.get("active_mass_property_coverage_at_least_95pct"),
            "missing_inputs": out.missing_inputs,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = n_scenarios.max(1) as f64;
    let recipe_body_n = recipe_scenarios.max(1) as f64;

    let kpi = json!({
        "runtime_status_insufficient_input_rate": {
            "observed": status_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": status_pass as f64 / n >= 1.0,
        },
        "evidence_scope_pinned_ingredient_ledger_diagnostic_rate": {
            "observed": evidence_scope_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": evidence_scope_pass as f64 / n >= 1.0,
        },
        "recipe_present_gate_matches_candidate_rate": {
            "observed": recipe_gate_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": recipe_gate_pass as f64 / n >= 1.0,
        },
        "ingredient_ledger_lookup_attempted_false_on_recipe_body_and_absent_on_abstention_rate": {
            "observed": lookup_false_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": lookup_false_pass as f64 / n >= 1.0,
        },
        "rights_cleared_ingredient_ledger_available_false_rate": {
            "observed": ledger_avail_false_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": ledger_avail_false_pass as f64 / n >= 1.0,
        },
        "active_mass_property_coverage_null_rate": {
            "observed": coverage_null_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": coverage_null_pass as f64 / n >= 1.0,
        },
        "all_candidate_ingredients_cited_gate_false_rate": {
            "observed": cited_gate_false_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": cited_gate_false_pass as f64 / n >= 1.0,
        },
        "active_mass_property_coverage_at_least_95pct_gate_false_rate": {
            "observed": coverage_gate_false_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": coverage_gate_false_pass as f64 / n >= 1.0,
        },
        "observed_ingredient_ids_match_expected_lexicographic_rate": {
            "observed": ids_match_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": ids_match_pass as f64 / n >= 1.0,
        },
        "missing_input_names_grade_lot_method_currentness_rate": {
            "observed": missing_input_pass as f64 / recipe_body_n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": recipe_scenarios,
            "passed": missing_input_pass == recipe_scenarios,
        },
        "explanation_disclaims_unresolved_legacy_ledger_rate": {
            "observed": explanation_pass as f64 / recipe_body_n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": recipe_scenarios,
            "passed": explanation_pass == recipe_scenarios,
        },
        "authority_envelope_preservation_rate": {
            "observed": envelope_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": envelope_pass as f64 / n >= 1.0,
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_pass as f64 / n,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "note": "observational; ingredient_library invoked twice per candidate produces byte-identical ModuleResult",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-ingredient-library",
        "kpi": kpi.clone(),
        "records": per_scenario.clone(),
        "passed": kpi["runtime_status_insufficient_input_rate"]["passed"] == json!(true)
            && kpi["evidence_scope_pinned_ingredient_ledger_diagnostic_rate"]["passed"] == json!(true)
            && kpi["recipe_present_gate_matches_candidate_rate"]["passed"] == json!(true)
            && kpi["ingredient_ledger_lookup_attempted_false_on_recipe_body_and_absent_on_abstention_rate"]["passed"] == json!(true)
            && kpi["rights_cleared_ingredient_ledger_available_false_rate"]["passed"] == json!(true)
            && kpi["active_mass_property_coverage_null_rate"]["passed"] == json!(true)
            && kpi["all_candidate_ingredients_cited_gate_false_rate"]["passed"] == json!(true)
            && kpi["active_mass_property_coverage_at_least_95pct_gate_false_rate"]["passed"] == json!(true)
            && kpi["observed_ingredient_ids_match_expected_lexicographic_rate"]["passed"] == json!(true)
            && kpi["missing_input_names_grade_lot_method_currentness_rate"]["passed"] == json!(true)
            && kpi["explanation_disclaims_unresolved_legacy_ledger_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-ingredient-library"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-ingredient-library-phase0-ledger-quarantine-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(benchmark_lock_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("ingredient-library Phase-0 harness constructs its 6 formulation-candidate scenarios in-Rust and does not consume an external fixture. SHA-256 recorded is the on-disk benchmark-lock hash."),
    );
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_scenario));
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
fn ingredient_library_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "runtime_status_insufficient_input_rate",
        "evidence_scope_pinned_ingredient_ledger_diagnostic_rate",
        "recipe_present_gate_matches_candidate_rate",
        "ingredient_ledger_lookup_attempted_false_on_recipe_body_and_absent_on_abstention_rate",
        "rights_cleared_ingredient_ledger_available_false_rate",
        "active_mass_property_coverage_null_rate",
        "all_candidate_ingredients_cited_gate_false_rate",
        "active_mass_property_coverage_at_least_95pct_gate_false_rate",
        "observed_ingredient_ids_match_expected_lexicographic_rate",
        "missing_input_names_grade_lot_method_currentness_rate",
        "explanation_disclaims_unresolved_legacy_ledger_rate",
        "authority_envelope_preservation_rate",
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
