//! Phase-0 KPI harness for `amphora-ip-fto-guard`.
//!
//! Drives the deterministic `evaluate_ip_fto_guard` runtime (exposed via
//! AssuranceCapability::new("amphora-ip-fto-guard")) which loads the
//! compile-time-embedded `patent_landscape.json` (60 patent families + 6
//! CPC/IPC classification sweeps), records ANY candidate-supplied
//! counsel-signoff assertion (recursive normalized-key reference-monitor
//! scan since repair R-B01 — not just the single literal path
//! `evidence_refs.counsel_fto.signed_by_counsel`) as
//! `boolean_counsel_assertion_ignored=true` (defensive lock — the runtime
//! never treats a candidate's claim as legal opinion), populates the
//! declared primary KPI value path `metrics.unresolved_technical_categories`
//! from the embedded claim-chart category census, and pins
//! `fto_status='FTO NOT PERFORMED'`, `legal_advice=false`, and
//! `fto_legal_closure=false` on every path. Phase-0 KPI verifies these
//! invariants across 5 candidate scenarios plus 3 fail-closed probes,
//! with byte-stable two-replay.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const IP_FTO_GUARD: &str = "amphora-ip-fto-guard";

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
        .join("amphora-ip-fto-guard/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

fn patent_landscape_path() -> PathBuf {
    workspace_root().join("amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-ip-fto-guard/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-ip-fto-guard-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-ip-fto-guard".into(),
        deterministic_seed: 20260722,
        lineage: Value::Null,
    }
}

fn wrong_type_candidate() -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": "evidence-probe",
        "candidate_type": "evidence_package",
        "evidence_refs": {"evidence_package": {}}
    }))
    .expect("valid evidence candidate")
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

struct Scenario {
    scenario_id: &'static str,
    candidate: Value,
    /// Expected `boolean_counsel_assertion_ignored` value.
    /// True iff the candidate supplies ANY counsel-signoff assertion key at
    /// any depth (canonical names such as `signed_by_counsel`/`counsel_fto`
    /// or a normalized-key semantic match), under any container type.
    expects_boolean_assertion_ignored: bool,
    industrial_context: &'static str,
}

fn scenarios() -> Vec<Scenario> {
    vec![
        Scenario {
            scenario_id: "baseline-primer-no-counsel-ref",
            candidate: json!({
                "candidate_id": "primer-baseline",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}}
            }),
            expects_boolean_assertion_ignored: false,
            industrial_context: "solvent-borne two-pack epoxy-polyamide primer with no candidate-supplied counsel evidence reference",
        },
        Scenario {
            scenario_id: "primer-with-forged-signed-by-counsel-true",
            candidate: json!({
                "candidate_id": "primer-forged-counsel-true",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}},
                "evidence_refs": {
                    "counsel_fto": {
                        "signed_by_counsel": true,
                        "signer_role": "adversary-claiming-to-be-counsel"
                    }
                }
            }),
            expects_boolean_assertion_ignored: true,
            industrial_context: "adversarial candidate injecting signed_by_counsel=true field; runtime must record boolean_counsel_assertion_ignored=true and never elevate the claim",
        },
        Scenario {
            scenario_id: "primer-with-signed-by-counsel-false",
            candidate: json!({
                "candidate_id": "primer-explicit-false",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}},
                "evidence_refs": {
                    "counsel_fto": {
                        "signed_by_counsel": false
                    }
                }
            }),
            expects_boolean_assertion_ignored: true,
            industrial_context: "candidate supplies explicit signed_by_counsel=false; runtime still records the injection attempt and ignores it (presence, not value, triggers the lock)",
        },
        Scenario {
            scenario_id: "topcoat-with-evidence-refs-no-counsel-key",
            candidate: json!({
                "candidate_id": "topcoat-adhesion-primer",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgebf": 120.0}, "part_B": {"amidoamine": 40.0}},
                "evidence_refs": {"lab_receipts": {"session_id": "irrelevant-lab-receipt"}}
            }),
            expects_boolean_assertion_ignored: false,
            industrial_context: "industrial-maintenance topcoat with unrelated evidence_refs.lab_receipts; no counsel_fto path present",
        },
        Scenario {
            scenario_id: "flooring-with-counsel-object-missing-boolean",
            candidate: json!({
                "candidate_id": "flooring-nested-counsel-noop",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgebf": 150.0}, "part_B": {"polyamide": 50.0}},
                "evidence_refs": {
                    "counsel_fto": {
                        "prose_summary": "Counsel review pending",
                        "attorney_notes": "not signed"
                    }
                }
            }),
            expects_boolean_assertion_ignored: true,
            industrial_context: "candidate has evidence_refs.counsel_fto object but omits the signed_by_counsel key; since repair R-B01 the canonical counsel_fto container itself is a recorded counsel-assertion injection (broader detection = stronger fail-closed lock)",
        },
    ]
}

fn compute_report() -> Value {
    // Independent recompute of family + sweep counts from the on-disk fixture.
    let landscape_bytes = fs::read(patent_landscape_path()).expect("patent_landscape readable");
    let landscape: Value =
        serde_json::from_slice(&landscape_bytes).expect("patent_landscape JSON");
    let harness_families = landscape["families"]
        .as_array()
        .map(Vec::len)
        .unwrap_or(0);
    let harness_sweeps = landscape["cpc_ipc_sweeps"]
        .as_array()
        .map(Vec::len)
        .unwrap_or(0);
    let fixture_pinned_ok = harness_families == 60 && harness_sweeps == 6;
    // Independent recompute of the declared primary KPI value
    // (metrics.unresolved_technical_categories): claim-chart categories that
    // remain unresolved for counsel review, i.e. every category not
    // explicitly recorded as `not_fto: false` by the checked fixture.
    let harness_unresolved = landscape["claim_chart_categories"]
        .as_array()
        .map(|categories| {
            categories
                .iter()
                .filter(|category| category["not_fto"].as_bool() != Some(false))
                .count()
        })
        .unwrap_or(0);

    let cap = AssuranceCapability::new(IP_FTO_GUARD).expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = context();
    let scenarios = scenarios();
    let n_scenarios = scenarios.len();

    let mut per_scenario: Vec<Value> = Vec::new();

    let mut status_scored_pass = 0_usize;
    let mut fto_status_pass = 0_usize;
    let mut legal_advice_false_pass = 0_usize;
    let mut fto_legal_closure_false_pass = 0_usize;
    let mut landscape_present_pass = 0_usize;
    let mut public_family_count_pass = 0_usize;
    let mut classification_sweep_pass = 0_usize;
    let mut counsel_assertion_correct_pass = 0_usize;
    let mut unresolved_categories_pass = 0_usize;
    let mut explanation_disclaims_pass = 0_usize;
    let mut envelope_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;

    for scenario in &scenarios {
        let candidate = CandidateEnvelope::from_value(scenario.candidate.clone())
            .expect("candidate parses");
        let out = cap
            .evaluate(&candidate, &features, &ctx)
            .expect("evaluate ok");

        // Runtime status is SCORED (not FAILED_GATES) even though fto_legal_closure=false;
        // this is the design — "SCORED" here means the technical screen was executed.
        let status_ok = out.status == "SCORED";
        if status_ok {
            status_scored_pass += 1;
        }

        let fto_status_ok =
            out.metrics.get("fto_status").and_then(Value::as_str) == Some("FTO NOT PERFORMED");
        if fto_status_ok {
            fto_status_pass += 1;
        }
        let legal_advice_ok = out.metrics.get("legal_advice") == Some(&json!(false));
        if legal_advice_ok {
            legal_advice_false_pass += 1;
        }
        let fto_legal_closure_ok = out.gates.get("fto_legal_closure") == Some(&json!(false));
        if fto_legal_closure_ok {
            fto_legal_closure_false_pass += 1;
        }
        let landscape_ok = out.gates.get("technical_landscape_present") == Some(&json!(true));
        if landscape_ok {
            landscape_present_pass += 1;
        }
        let family_ok = out.metrics.get("public_family_count") == Some(&json!(60));
        if family_ok {
            public_family_count_pass += 1;
        }
        let sweep_ok = out.metrics.get("classification_sweep_count") == Some(&json!(6));
        if sweep_ok {
            classification_sweep_pass += 1;
        }
        let counsel_observed = out
            .metrics
            .get("boolean_counsel_assertion_ignored")
            .and_then(Value::as_bool)
            .unwrap_or(false);
        let counsel_ok = counsel_observed == scenario.expects_boolean_assertion_ignored;
        if counsel_ok {
            counsel_assertion_correct_pass += 1;
        }
        // Primary KPI value path is populated by the runtime and matches the
        // harness's independent recompute from the on-disk fixture.
        let unresolved_ok = harness_unresolved > 0
            && out.metrics.get("unresolved_technical_categories")
                == Some(&json!(harness_unresolved));
        if unresolved_ok {
            unresolved_categories_pass += 1;
        }

        // Explanation must disclaim legal advice.
        let explanation_ok = out
            .explanations
            .iter()
            .any(|e| e.contains("not legal advice") && e.contains("FTO NOT PERFORMED"));
        if explanation_ok {
            explanation_disclaims_pass += 1;
        }

        // Authority envelope preservation.
        let out_json = serde_json::to_value(&out).expect("serializes");
        let envelope_ok = contains_banned_key(&out_json).is_none();
        if envelope_ok {
            envelope_pass += 1;
        }

        // Byte-stable two-replay.
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
            "fto_status": out.metrics.get("fto_status"),
            "legal_advice": out.metrics.get("legal_advice"),
            "boolean_counsel_assertion_ignored_observed": counsel_observed,
            "boolean_counsel_assertion_ignored_expected": scenario.expects_boolean_assertion_ignored,
            "public_family_count": out.metrics.get("public_family_count"),
            "classification_sweep_count": out.metrics.get("classification_sweep_count"),
            "technical_landscape_present_gate": out.gates.get("technical_landscape_present"),
            "fto_legal_closure_gate": out.gates.get("fto_legal_closure"),
            "status_is_scored": status_ok,
            "fto_status_pinned_to_never_performed": fto_status_ok,
            "legal_advice_false": legal_advice_ok,
            "fto_legal_closure_false": fto_legal_closure_ok,
            "technical_landscape_present_true": landscape_ok,
            "family_count_60": family_ok,
            "sweep_count_6": sweep_ok,
            "counsel_assertion_ignored_matches_expected": counsel_ok,
            "unresolved_technical_categories": out.metrics.get("unresolved_technical_categories"),
            "unresolved_technical_categories_matches_recompute": unresolved_ok,
            "explanation_disclaims_legal_advice": explanation_ok,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = n_scenarios.max(1) as f64;

    // Fail-closed probes.
    let mut fail_closed_pass = 0_usize;
    let mut fail_probes: Vec<Value> = Vec::new();

    // Probe A: wrong candidate_type.
    let wrong = wrong_type_candidate();
    let is_err = cap.evaluate(&wrong, &features, &ctx).is_err();
    if is_err {
        fail_closed_pass += 1;
    }
    fail_probes.push(json!({"probe": "candidate_type_evidence_package_rejected", "fail_closed": is_err}));

    // Probe B: unknown module_id.
    let unknown = AssuranceCapability::new("amphora-does-not-exist").is_err();
    if unknown {
        fail_closed_pass += 1;
    }
    fail_probes.push(json!({"probe": "unknown_module_id_rejected", "fail_closed": unknown}));

    // Probe C: whitespace module_id.
    let ws = AssuranceCapability::new("   ").is_err();
    if ws {
        fail_closed_pass += 1;
    }
    fail_probes.push(json!({"probe": "whitespace_module_id_rejected", "fail_closed": ws}));

    let fail_total = fail_probes.len();
    let fail_rate = fail_closed_pass as f64 / fail_total.max(1) as f64;

    let kpi = json!({
        "patent_landscape_pinned_60_families_and_6_sweeps_rate": {
            "observed": if fixture_pinned_ok { 1.0 } else { 0.0 },
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 1,
            "passed": fixture_pinned_ok,
        },
        "runtime_status_scored_rate": {
            "observed": status_scored_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": status_scored_pass as f64 / n >= 1.0,
        },
        "fto_status_pinned_to_never_performed_rate": {
            "observed": fto_status_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": fto_status_pass as f64 / n >= 1.0,
        },
        "legal_advice_false_rate": {
            "observed": legal_advice_false_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": legal_advice_false_pass as f64 / n >= 1.0,
        },
        "fto_legal_closure_gate_false_rate": {
            "observed": fto_legal_closure_false_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": fto_legal_closure_false_pass as f64 / n >= 1.0,
        },
        "technical_landscape_present_gate_true_rate": {
            "observed": landscape_present_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": landscape_present_pass as f64 / n >= 1.0,
        },
        "runtime_family_and_sweep_counts_match_fixture_rate": {
            "observed": (public_family_count_pass + classification_sweep_pass) as f64
                / (2.0 * n),
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 2 * n_scenarios,
            "passed": public_family_count_pass == n_scenarios
                && classification_sweep_pass == n_scenarios,
        },
        "boolean_counsel_assertion_ignored_correctness_rate": {
            "observed": counsel_assertion_correct_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": counsel_assertion_correct_pass as f64 / n >= 1.0,
        },
        "unresolved_technical_categories_populated_rate": {
            "observed": unresolved_categories_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "note": "declared primary KPI value path metrics.unresolved_technical_categories is populated by the live runtime and equals the harness's independent claim-chart-category recompute from the on-disk fixture",
            "passed": unresolved_categories_pass as f64 / n >= 1.0,
        },
        "explanation_disclaims_legal_advice_rate": {
            "observed": explanation_disclaims_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": explanation_disclaims_pass as f64 / n >= 1.0,
        },
        "authority_envelope_preservation_rate": {
            "observed": envelope_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": envelope_pass as f64 / n >= 1.0,
        },
        "unsupported_input_fail_closed_rate": {
            "observed": fail_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": fail_total,
            "probes": fail_probes,
            "passed": fail_rate >= 1.0,
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_pass as f64 / n,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "note": "observational; evaluate_ip_fto_guard invoked twice per candidate produces byte-identical ModuleResult",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let dataset_sha256 = file_sha256(&landscape_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-ip-fto-guard",
        "kpi": kpi.clone(),
        "records": per_scenario.clone(),
        "passed": kpi["patent_landscape_pinned_60_families_and_6_sweeps_rate"]["passed"] == json!(true)
            && kpi["runtime_status_scored_rate"]["passed"] == json!(true)
            && kpi["fto_status_pinned_to_never_performed_rate"]["passed"] == json!(true)
            && kpi["legal_advice_false_rate"]["passed"] == json!(true)
            && kpi["fto_legal_closure_gate_false_rate"]["passed"] == json!(true)
            && kpi["technical_landscape_present_gate_true_rate"]["passed"] == json!(true)
            && kpi["runtime_family_and_sweep_counts_match_fixture_rate"]["passed"] == json!(true)
            && kpi["boolean_counsel_assertion_ignored_correctness_rate"]["passed"] == json!(true)
            && kpi["unresolved_technical_categories_populated_rate"]["passed"] == json!(true)
            && kpi["explanation_disclaims_legal_advice_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true)
            && kpi["unsupported_input_fail_closed_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-ip-fto-guard"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-ip-fto-guard-phase0-technical-landscape-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("SHA-256 of amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json - 60 patent families + 6 CPC/IPC classification sweeps, embedded at compile time by evaluate_ip_fto_guard. Any landscape drift changes this hash and the KPI recompute detects it."),
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
fn ip_fto_guard_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "patent_landscape_pinned_60_families_and_6_sweeps_rate",
        "runtime_status_scored_rate",
        "fto_status_pinned_to_never_performed_rate",
        "legal_advice_false_rate",
        "fto_legal_closure_gate_false_rate",
        "technical_landscape_present_gate_true_rate",
        "runtime_family_and_sweep_counts_match_fixture_rate",
        "boolean_counsel_assertion_ignored_correctness_rate",
        "unresolved_technical_categories_populated_rate",
        "explanation_disclaims_legal_advice_rate",
        "authority_envelope_preservation_rate",
        "unsupported_input_fail_closed_rate",
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
