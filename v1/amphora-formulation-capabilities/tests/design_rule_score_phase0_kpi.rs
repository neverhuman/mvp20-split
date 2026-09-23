//! Phase-0 KPI harness for `amphora-design-rule-score`.
//!
//! Drives the deterministic `design_rule_score` runtime (via
//! `FormulationCapability::new(descriptor_for("amphora-design-rule-score"))`)
//! across 6 formulation-candidate scenarios: simple 1+1, multi-ingredient
//! primer, adversarial design_rule_scores injection, adversarial
//! aggregate_pot_life_h injection, adversarial corrosion_rank injection,
//! and missing recipe. Verifies defensive invariants: status=NO_AUTHORITY
//! (body path), aggregate_design_rule_score=Null,
//! candidate_pot_life_prediction_h=Null, corrosion_rank=Null,
//! hypothesis_features_evaluated=false,
//! individually_validated_design_rules_available=false, missing_inputs
//! names held-family validation receipts, explanation disclaims aggregate
//! or favorable fallback, byte-stable two-replay.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
    ModuleDescriptor,
};
use amphora_formulation_capabilities::{FormulationCapability, DESIGN_RULE_SCORE_ID};
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
        .join("amphora-design-rule-score/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-design-rule-score/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-design-rule-score-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-design-rule-score".into(),
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

fn design_rule_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: std::sync::OnceLock<ModuleDescriptor> = std::sync::OnceLock::new();
    DESCRIPTOR.get_or_init(|| ModuleDescriptor {
        project: DESIGN_RULE_SCORE_ID.into(),
        authority_ceiling: "RULE_CITED".into(),
        solver_use_ceiling: "CONSTRAINT_ONLY".into(),
        model_readiness_ceiling: "NOT_PROVEN".into(),
        ranking_eligible: false,
        candidate_types: vec!["formulation".into()],
        non_blocking_claim_locks: vec![
            "no_aggregate_design_rule_authority".into(),
            "no_candidate_supplied_score_elevated".into(),
            "no_favorable_fallback_emitted".into(),
        ],
        readiness: "GATED".into(),
    })
}

struct Scenario {
    scenario_id: &'static str,
    candidate: Value,
    /// True iff the recipe body path should run (positive-mass in both parts).
    expects_recipe_present: bool,
    /// Expected status: 'NO_AUTHORITY' for recipe-present, 'INSUFFICIENT_INPUT' for abstention.
    expected_status: &'static str,
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
            expects_recipe_present: true,
            expected_status: "NO_AUTHORITY",
            industrial_context: "marine primer baseline 1+1 recipe",
        },
        Scenario {
            scenario_id: "primer-multi-ingredient",
            candidate: json!({
                "candidate_id": "primer-multi",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0, "iron_oxide_red": 15.0, "silica_extender": 20.0},
                    "part_B": {"polyamide": 65.0, "butanol_solvent": 3.0}
                }
            }),
            expects_recipe_present: true,
            expected_status: "NO_AUTHORITY",
            industrial_context: "industrial primer with pigment/extender/solvent",
        },
        Scenario {
            scenario_id: "adversarial-design-rule-scores-injection",
            candidate: json!({
                "candidate_id": "adversarial-scores",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0},
                    "part_B": {"polyamide": 65.0},
                    "design_rule_scores": {
                        "wicks_jones_pappas_2007_rule_24_1": 0.95,
                        "ellis_1993_rule_6_2": 0.88,
                        "adversary_asserted_aggregate": 0.92
                    }
                }
            }),
            expects_recipe_present: true,
            expected_status: "NO_AUTHORITY",
            industrial_context: "adversarial candidate injecting design_rule_scores with cited literature rule names and asserted aggregate; runtime must NOT elevate aggregate_design_rule_score",
        },
        Scenario {
            scenario_id: "adversarial-pot-life-prediction-injection",
            candidate: json!({
                "candidate_id": "adversarial-pot-life",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0},
                    "part_B": {"polyamide": 65.0},
                    "candidate_pot_life_prediction_h": 4.5,
                    "candidate_pot_life_confidence": 0.99,
                    "candidate_pot_life_method": "adversary-declared-Arrhenius"
                }
            }),
            expects_recipe_present: true,
            expected_status: "NO_AUTHORITY",
            industrial_context: "adversarial candidate injecting candidate_pot_life_prediction_h=4.5 h with 0.99 confidence; runtime must NOT elevate candidate_pot_life_prediction_h",
        },
        Scenario {
            scenario_id: "adversarial-corrosion-rank-injection",
            candidate: json!({
                "candidate_id": "adversarial-corrosion",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0, "zinc_phosphate": 8.0},
                    "part_B": {"polyamide": 65.0},
                    "corrosion_rank": 1,
                    "asserted_corrosion_class": "excellent",
                    "adversary_hypothesis_features_evaluated": true
                }
            }),
            expects_recipe_present: true,
            expected_status: "NO_AUTHORITY",
            industrial_context: "adversarial candidate injecting corrosion_rank=1 (excellent) + asserted_corrosion_class + adversary_hypothesis_features_evaluated=true; runtime must NOT elevate corrosion_rank or hypothesis_features_evaluated",
        },
        Scenario {
            scenario_id: "missing-part-b-abstention",
            candidate: json!({
                "candidate_id": "missing-b",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}}
            }),
            expects_recipe_present: false,
            expected_status: "INSUFFICIENT_INPUT",
            industrial_context: "candidate missing part_B - triggers recipe_or_abstain path",
        },
    ]
}

fn compute_report() -> Value {
    let cap =
        FormulationCapability::new(design_rule_descriptor()).expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = context();
    let scenarios = scenarios();
    let n_scenarios = scenarios.len();

    let mut per_scenario: Vec<Value> = Vec::new();

    let mut status_pass = 0_usize;
    let mut evidence_scope_pass = 0_usize;
    let mut recipe_gate_pass = 0_usize;
    let mut aggregate_null_pass = 0_usize;
    let mut pot_life_null_pass = 0_usize;
    let mut corrosion_rank_null_pass = 0_usize;
    let mut hypothesis_false_pass = 0_usize;
    let mut validated_gate_false_pass = 0_usize;
    let mut missing_input_pass = 0_usize;
    let mut explanation_pass = 0_usize;
    let mut envelope_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;

    let mut body_scenarios = 0_usize;

    for scenario in &scenarios {
        let candidate = CandidateEnvelope::from_value(scenario.candidate.clone())
            .expect("candidate parses");
        let out = cap
            .evaluate(&candidate, &features, &ctx)
            .expect("evaluate ok");

        let status_ok = out.status == scenario.expected_status;
        if status_ok {
            status_pass += 1;
        }
        let evidence_ok = out.evidence_scope == "formulation_design_rule_diagnostic";
        if evidence_ok {
            evidence_scope_pass += 1;
        }

        let recipe_observed = out.gates.get("required_recipe_present") == Some(&json!(true));
        let recipe_ok = recipe_observed == scenario.expects_recipe_present;
        if recipe_ok {
            recipe_gate_pass += 1;
        }

        // Defensive invariants only exist on the recipe-present body path.
        let aggregate_val = out.metrics.get("aggregate_design_rule_score");
        let aggregate_ok = if scenario.expects_recipe_present {
            aggregate_val == Some(&Value::Null)
        } else {
            aggregate_val.is_none()
        };
        if aggregate_ok {
            aggregate_null_pass += 1;
        }

        let pot_life_val = out.metrics.get("candidate_pot_life_prediction_h");
        let pot_life_ok = if scenario.expects_recipe_present {
            pot_life_val == Some(&Value::Null)
        } else {
            pot_life_val.is_none()
        };
        if pot_life_ok {
            pot_life_null_pass += 1;
        }

        let corrosion_val = out.metrics.get("corrosion_rank");
        let corrosion_ok = if scenario.expects_recipe_present {
            corrosion_val == Some(&Value::Null)
        } else {
            corrosion_val.is_none()
        };
        if corrosion_ok {
            corrosion_rank_null_pass += 1;
        }

        let hypothesis_val = out.metrics.get("hypothesis_features_evaluated");
        let hypothesis_ok = if scenario.expects_recipe_present {
            hypothesis_val == Some(&json!(false))
        } else {
            hypothesis_val.is_none()
        };
        if hypothesis_ok {
            hypothesis_false_pass += 1;
        }

        let validated_val = out.gates.get("individually_validated_design_rules_available");
        let validated_ok = if scenario.expects_recipe_present {
            validated_val == Some(&json!(false))
        } else {
            validated_val.is_none()
        };
        if validated_ok {
            validated_gate_false_pass += 1;
        }

        if scenario.expects_recipe_present {
            body_scenarios += 1;
            let missing_ok = out.missing_inputs.iter().any(|m| {
                m.contains("held-family") && m.contains("design-rule") && m.contains("validation")
            });
            if missing_ok {
                missing_input_pass += 1;
            }
            let explanation_ok = out
                .explanations
                .iter()
                .any(|e| {
                    (e.contains("aggregate") || e.contains("favorable"))
                        && e.contains("unresolved")
                });
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
            "expected_status": scenario.expected_status,
            "observed_status": out.status,
            "evidence_scope": out.evidence_scope,
            "expects_recipe_present": scenario.expects_recipe_present,
            "recipe_present_observed": recipe_observed,
            "aggregate_design_rule_score": out.metrics.get("aggregate_design_rule_score"),
            "candidate_pot_life_prediction_h": out.metrics.get("candidate_pot_life_prediction_h"),
            "corrosion_rank": out.metrics.get("corrosion_rank"),
            "hypothesis_features_evaluated": out.metrics.get("hypothesis_features_evaluated"),
            "individually_validated_design_rules_available_gate": out.gates.get("individually_validated_design_rules_available"),
            "missing_inputs": out.missing_inputs,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = n_scenarios.max(1) as f64;
    let body_n = body_scenarios.max(1) as f64;

    let kpi = json!({
        "runtime_status_matches_expected_rate": {
            "observed": status_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": status_pass as f64 / n >= 1.0,
        },
        "evidence_scope_pinned_formulation_design_rule_diagnostic_rate": {
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
        "aggregate_design_rule_score_null_on_body_absent_on_abstention_rate": {
            "observed": aggregate_null_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": aggregate_null_pass as f64 / n >= 1.0,
        },
        "candidate_pot_life_prediction_h_null_rate": {
            "observed": pot_life_null_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": pot_life_null_pass as f64 / n >= 1.0,
        },
        "corrosion_rank_null_rate": {
            "observed": corrosion_rank_null_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": corrosion_rank_null_pass as f64 / n >= 1.0,
        },
        "hypothesis_features_evaluated_false_rate": {
            "observed": hypothesis_false_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": hypothesis_false_pass as f64 / n >= 1.0,
        },
        "individually_validated_design_rules_available_gate_false_rate": {
            "observed": validated_gate_false_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": validated_gate_false_pass as f64 / n >= 1.0,
        },
        "missing_input_names_held_family_validation_receipts_rate": {
            "observed": missing_input_pass as f64 / body_n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": body_scenarios,
            "passed": missing_input_pass == body_scenarios,
        },
        "explanation_disclaims_aggregate_or_favorable_fallback_rate": {
            "observed": explanation_pass as f64 / body_n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": body_scenarios,
            "passed": explanation_pass == body_scenarios,
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
            "note": "observational; design_rule_score invoked twice per candidate produces byte-identical ModuleResult",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-design-rule-score",
        "kpi": kpi.clone(),
        "records": per_scenario.clone(),
        "passed": kpi["runtime_status_matches_expected_rate"]["passed"] == json!(true)
            && kpi["evidence_scope_pinned_formulation_design_rule_diagnostic_rate"]["passed"] == json!(true)
            && kpi["recipe_present_gate_matches_candidate_rate"]["passed"] == json!(true)
            && kpi["aggregate_design_rule_score_null_on_body_absent_on_abstention_rate"]["passed"] == json!(true)
            && kpi["candidate_pot_life_prediction_h_null_rate"]["passed"] == json!(true)
            && kpi["corrosion_rank_null_rate"]["passed"] == json!(true)
            && kpi["hypothesis_features_evaluated_false_rate"]["passed"] == json!(true)
            && kpi["individually_validated_design_rules_available_gate_false_rate"]["passed"] == json!(true)
            && kpi["missing_input_names_held_family_validation_receipts_rate"]["passed"] == json!(true)
            && kpi["explanation_disclaims_aggregate_or_favorable_fallback_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-design-rule-score"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-design-rule-score-phase0-rule-authority-quarantine-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(benchmark_lock_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("design-rule-score Phase-0 harness constructs its 6 formulation-candidate scenarios in-Rust and does not consume an external fixture. SHA-256 recorded is the on-disk benchmark-lock hash."),
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
fn design_rule_score_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "runtime_status_matches_expected_rate",
        "evidence_scope_pinned_formulation_design_rule_diagnostic_rate",
        "recipe_present_gate_matches_candidate_rate",
        "aggregate_design_rule_score_null_on_body_absent_on_abstention_rate",
        "candidate_pot_life_prediction_h_null_rate",
        "corrosion_rank_null_rate",
        "hypothesis_features_evaluated_false_rate",
        "individually_validated_design_rules_available_gate_false_rate",
        "missing_input_names_held_family_validation_receipts_rate",
        "explanation_disclaims_aggregate_or_favorable_fallback_rate",
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
