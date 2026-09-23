// live-capability-dispatch-wiring-v1: amphora-envelope-gates audit.
//
// T-03 (2026-08-05), kpi-claim-currency-v1 (2026-08-15), and
// rust-runtime-boundary-fuzz-v1 (2026-08-17) all attacked and characterized
// `amphora_formulation_capabilities::evaluate_envelope_policy` -- the last of
// these linked the real, compiled, unmodified function directly via a
// standalone harness and found it correctly fails closed on 23/23
// invalid/boundary probes. Its own scope_and_limits section flagged an open
// question it explicitly did NOT trace: "whether a candidate-authored
// boolean is merged with this function's result anywhere downstream in
// amphora-engine."
//
// This fire traces that. Reading amphora-formulation-capabilities/src/lib.rs
// shows `evaluate_envelope_policy` is called from exactly one non-test,
// non-diagnostic site: the `envelope_gates(candidate)` function, which is
// the function actually wired into `FormulationCapability::evaluate()` for
// ENVELOPE_GATES_ID -- the real dispatch path amphora-engine uses to score
// every live formulation candidate. That call site is:
//
//     let gate = evaluate_envelope_policy(None, None, false)...
//
// hardcoded, ignoring the candidate entirely. Worse: `envelope_gates`
// receives only `candidate: &CandidateEnvelope` in its signature -- the
// `features: &FeatureSnapshot` argument that IS available in `evaluate()`'s
// scope (and IS forwarded to sibling capabilities like
// `public_corrosion_benchmark(candidate, features)`) is never passed to
// `envelope_gates` at all. There is no code path in this workspace by which
// a real EnvelopePolicyV1 or TrustedArithmeticSnapshotV1 constructed from
// live candidate/feature data ever reaches `evaluate_envelope_policy` outside
// of tests, diagnostics, and this audit harness.
//
// This harness proves that empirically, not just by reading source: it runs
// every one of the module's own 50 locked known-answer test cases (the same
// fixture mission.md's "Current benchmark result" cites) through BOTH paths:
//   (a) evaluate_envelope_policy(Some(&real_policy), Some(&real_snapshot), true)
//       -- the direct call, confirmed fail-closed and correct by prior fires
//   (b) FormulationCapability::new(...).evaluate(&candidate, &features, &ctx)
//       for ENVELOPE_GATES_ID -- the actual live dispatch amphora-engine calls
// where the (b) candidate is built from the same test case's part_A/part_B
// masses so a human reading both outputs is looking at the "same" chemistry.

use amphora_core::{
    CandidateEnvelope, Capability, ExecutionContext, FeatureSnapshot, ModuleDescriptor,
};
use amphora_formulation_capabilities::{
    evaluate_envelope_policy, EnvelopePolicyV1, FormulationCapability, TrustedArithmeticSnapshotV1,
    ENVELOPE_GATES_ID,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;

const FIXTURE_PATH: &str = "/home/ubuntu/amphora/build/mvp20-split/amphora-envelope-gates/reference/phase0-envelope-gates-known-answer.v1.json";
const LIB_RS_PATH: &str =
    "/home/ubuntu/amphora/build/mvp20-split/amphora-formulation-capabilities/src/lib.rs";

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

fn descriptor() -> &'static ModuleDescriptor {
    Box::leak(Box::new(ModuleDescriptor {
        project: ENVELOPE_GATES_ID.into(),
        authority_ceiling: "LIMITED_SANITY".into(),
        solver_use_ceiling: "DISABLED".into(),
        model_readiness_ceiling: "NOT_PROVEN".into(),
        ranking_eligible: false,
        candidate_types: vec!["formulation".into()],
        non_blocking_claim_locks: Vec::new(),
        readiness: "PRE_PHASE_0".into(),
    }))
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "live-capability-dispatch-wiring-v1".into(),
        deterministic_seed: 42,
        lineage: Value::Null,
    }
}

fn empty_features() -> FeatureSnapshot {
    FeatureSnapshot {
        values: BTreeMap::new(),
    }
}

fn candidate_for(case_id: &str, part_a_g: f64, part_b_g: f64) -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": format!("live-wiring-probe-{case_id}"),
        "candidate_type": "formulation",
        "formulation": {
            "part_A": {"resin": part_a_g},
            "part_B": {"hardener": part_b_g},
            "application": {"dft_mil": 5.0, "temperature_C": 25.0},
        }
    }))
    .expect("valid formulation candidate")
}

fn main() {
    let fixture_bytes = fs::read(FIXTURE_PATH).expect("read fixture");
    let fixture_sha256 = sha256_hex(&fixture_bytes);
    let fixture: Value = serde_json::from_slice(&fixture_bytes).expect("parse fixture");
    let lib_rs_bytes = fs::read(LIB_RS_PATH).expect("read real runtime source");
    let lib_rs_sha256 = sha256_hex(&lib_rs_bytes);
    let lib_rs_text = String::from_utf8_lossy(&lib_rs_bytes);
    let hardcoded_call_present = lib_rs_text
        .contains("evaluate_envelope_policy(None, None, false)");
    let envelope_gates_receives_features = lib_rs_text
        .contains("fn envelope_gates(candidate: &CandidateEnvelope, features: &FeatureSnapshot");

    let envelopes = fixture["envelopes"].as_array().expect("envelopes array");
    let cap = FormulationCapability::new(descriptor()).expect("supported capability");
    let features = empty_features();
    let ctx = context();

    let mut per_case = Vec::new();
    let mut n_cases = 0usize;
    let mut direct_pass_true = 0usize;
    let mut live_pass_true = 0usize;
    let mut live_envelope_evaluated_true = 0usize;
    let mut mismatches = 0usize;

    for envelope in envelopes {
        let envelope_id = envelope["envelope_id"].as_str().unwrap_or("").to_string();
        let policy: EnvelopePolicyV1 =
            serde_json::from_value(envelope["policy"].clone()).expect("valid policy");
        let test_cases = envelope["test_cases"].as_array().expect("test_cases array");
        for case in test_cases {
            n_cases += 1;
            let case_id = case["case_id"].as_str().unwrap_or("").to_string();
            let subgroup = case["subgroup"].as_str().unwrap_or("").to_string();
            let expected_pass_all_hard = case["expected_pass_all_hard"].as_bool().unwrap_or(false);
            let snapshot: TrustedArithmeticSnapshotV1 =
                serde_json::from_value(case["snapshot"].clone()).expect("valid snapshot");

            let direct = evaluate_envelope_policy(Some(&policy), Some(&snapshot), true)
                .expect("direct call succeeds on a valid fixture case");
            if direct.pass_all_hard {
                direct_pass_true += 1;
            }
            let direct_matches_fixture_label = direct.pass_all_hard == expected_pass_all_hard;

            let part_a_g = case["snapshot"]["values"]["mass.part_A_g"]["value"]
                .as_f64()
                .unwrap_or(f64::NAN);
            let part_b_g = case["snapshot"]["values"]["mass.part_B_g"]["value"]
                .as_f64()
                .unwrap_or(f64::NAN);
            let candidate = candidate_for(&case_id, part_a_g, part_b_g);
            let live = cap
                .evaluate(&candidate, &features, &ctx)
                .expect("live capability dispatch evaluates without error");
            let live_pass_all_hard = live.gates.get("pass_all_hard").cloned();
            let live_envelope_evaluated = live.gates.get("envelope_evaluated").cloned();
            if live_pass_all_hard == Some(Value::Bool(true)) {
                live_pass_true += 1;
            }
            if live_envelope_evaluated == Some(Value::Bool(true)) {
                live_envelope_evaluated_true += 1;
            }
            let live_reports_ground_truth =
                live_pass_all_hard == Some(Value::Bool(direct.pass_all_hard));
            if !live_reports_ground_truth {
                mismatches += 1;
            }

            per_case.push(json!({
                "envelope_id": envelope_id,
                "case_id": case_id,
                "subgroup": subgroup,
                "expected_pass_all_hard_per_fixture_label": expected_pass_all_hard,
                "direct_evaluate_envelope_policy_pass_all_hard": direct.pass_all_hard,
                "direct_matches_fixture_label": direct_matches_fixture_label,
                "live_dispatch_status": live.status,
                "live_dispatch_gates_pass_all_hard": live_pass_all_hard,
                "live_dispatch_gates_envelope_evaluated": live_envelope_evaluated,
                "live_dispatch_missing_inputs": live.missing_inputs,
                "live_reports_ground_truth_pass_all_hard": live_reports_ground_truth,
            }));
        }
    }

    let out = json!({
        "study_id": "live-capability-dispatch-wiring-v1",
        "fixture_path": "amphora-envelope-gates/reference/phase0-envelope-gates-known-answer.v1.json",
        "fixture_sha256": fixture_sha256,
        "real_runtime_path": "amphora-formulation-capabilities/src/lib.rs",
        "real_runtime_sha256_at_test_time": lib_rs_sha256,
        "source_evidence": {
            "hardcoded_none_none_false_call_present": hardcoded_call_present,
            "envelope_gates_dispatch_fn_receives_features_param": envelope_gates_receives_features,
        },
        "n_cases": n_cases,
        "direct_evaluate_envelope_policy_pass_true_count": direct_pass_true,
        "live_dispatch_pass_all_hard_true_count": live_pass_true,
        "live_dispatch_envelope_evaluated_true_count": live_envelope_evaluated_true,
        "cases_where_live_dispatch_disagrees_with_ground_truth": mismatches,
        "per_case": per_case,
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
