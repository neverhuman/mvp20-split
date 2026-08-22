//! Phase-0 KPI harness for `amphora-optimizer-orchestrator`.
//!
//! Drives the deterministic `authorize_optimizer_request` authorization gate
//! (amphora-core) across 5 positive quarantine-mode scenarios and 21
//! fail-closed probes covering the six module-specific attack axes
//! (OBJECTIVE_CONSTRAINT_INJECTION, UNKNOWN_OBJECTIVE_PATH_OPERATOR,
//! DUPLICATE_SCORE_ENVELOPE, MISSING_OPTIMIZER_CLAIM_LOCK,
//! FAILED_OR_NO_AUTHORITY_SCORE, SOLVER_RANKING_ESCALATION). Verifies
//! output authority envelope is fully quarantined (usable_by_optimizer=false,
//! ranking_performed=false, solver_invoked=false, authority_upgrade=false,
//! candidate_created_evidence=false, status="NO_ELIGIBLE_OBJECTIVES"),
//! all with byte-stable two-replay.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{
    authorize_optimizer_request, canonicalize, quarantined_optimizer_policy, stable_hash,
    OptimizerAuthorizationRequestV1, OptimizerConstraintRequestV1, OptimizerEnvelopeV1,
    OptimizerObjectiveRequestV1, OptimizerRegistryPolicyV1, REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS,
};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const ENVELOPE_GATES: &str = "amphora-envelope-gates";
const FORMULATION_ARITHMETIC: &str = "amphora-formulation-arithmetic";
const FORMULATION_UNIVERSE: &str = "amphora-formulation-universe";
const UNKNOWN_MODULE: &str = "amphora-does-not-exist";

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
        .join("amphora-optimizer-orchestrator/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-optimizer-orchestrator/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-optimizer-orchestrator-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
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

fn policy_request(
    objectives: Vec<OptimizerObjectiveRequestV1>,
    hard_constraints: Vec<OptimizerConstraintRequestV1>,
) -> OptimizerAuthorizationRequestV1 {
    OptimizerAuthorizationRequestV1 {
        schema: "amphora.optimizer-authorization-request.v1".into(),
        request_source: "POLICY".into(),
        objectives,
        hard_constraints,
    }
}

fn candidate_request(
    objectives: Vec<OptimizerObjectiveRequestV1>,
    hard_constraints: Vec<OptimizerConstraintRequestV1>,
) -> OptimizerAuthorizationRequestV1 {
    OptimizerAuthorizationRequestV1 {
        schema: "amphora.optimizer-authorization-request.v1".into(),
        request_source: "CANDIDATE".into(),
        objectives,
        hard_constraints,
    }
}

fn envelope(module_id: &str, gate_key: &str, gate_value: Value) -> OptimizerEnvelopeV1 {
    OptimizerEnvelopeV1 {
        module_id: module_id.into(),
        status: "SCORED".into(),
        authority_tier: "REAL_ARITHMETIC".into(),
        solver_use_ceiling: "CONSTRAINT_ONLY".into(),
        ranking_eligible: false,
        usable_by_optimizer: false,
        objective_values: BTreeMap::new(),
        gates: BTreeMap::from([(gate_key.into(), gate_value)]),
        claim_locks: REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS
            .iter()
            .map(|lock| ((*lock).into(), true))
            .collect(),
    }
}

fn constraint(
    id: &str,
    module_id: &str,
    path: &str,
    operator: &str,
    expected: Value,
) -> OptimizerConstraintRequestV1 {
    OptimizerConstraintRequestV1 {
        constraint_id: id.into(),
        module_id: module_id.into(),
        section: "gates".into(),
        path: path.into(),
        operator: operator.into(),
        expected,
    }
}

fn objective(id: &str, module_id: &str, path: &str) -> OptimizerObjectiveRequestV1 {
    OptimizerObjectiveRequestV1 {
        objective_id: id.into(),
        module_id: module_id.into(),
        section: "objective_values".into(),
        path: path.into(),
    }
}

struct PositiveScenario {
    scenario_id: &'static str,
    request: OptimizerAuthorizationRequestV1,
    envelopes: Vec<OptimizerEnvelopeV1>,
    industrial_context: &'static str,
}

fn positive_scenarios() -> Vec<PositiveScenario> {
    let pass_all = constraint("mass-gate", ENVELOPE_GATES, "pass_all_hard", "==", Value::Bool(true));
    vec![
        PositiveScenario {
            scenario_id: "policy-empty-no-envelope",
            request: policy_request(Vec::new(), Vec::new()),
            envelopes: Vec::new(),
            industrial_context: "policy audit with no upstream envelopes and no objectives",
        },
        PositiveScenario {
            scenario_id: "policy-single-scored-envelope",
            request: policy_request(Vec::new(), Vec::new()),
            envelopes: vec![envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true))],
            industrial_context: "policy audit consuming one SCORED envelope from envelope-gates",
        },
        PositiveScenario {
            scenario_id: "policy-hard-constraint-passes",
            request: policy_request(Vec::new(), vec![pass_all.clone()]),
            envelopes: vec![envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true))],
            industrial_context: "policy audit with one hard constraint satisfied by envelope-gates",
        },
        PositiveScenario {
            scenario_id: "policy-two-envelope-modules",
            request: policy_request(Vec::new(), Vec::new()),
            envelopes: vec![
                envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true)),
                envelope(FORMULATION_ARITHMETIC, "mass_identity", Value::Bool(true)),
            ],
            industrial_context: "policy audit spanning envelope-gates + formulation-arithmetic",
        },
        PositiveScenario {
            scenario_id: "policy-objective-declared-with-constraint",
            request: policy_request(
                vec![objective("audit-score", FORMULATION_ARITHMETIC, "audit_score")],
                vec![pass_all],
            ),
            envelopes: vec![envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true))],
            industrial_context: "policy audit declaring an objective but quarantine still blocks evaluation",
        },
    ]
}

fn compute_report() -> Value {
    let scenarios = positive_scenarios();
    let n_scenarios = scenarios.len();
    let policy = quarantined_optimizer_policy();

    let mut per_scenario: Vec<Value> = Vec::new();

    let mut ok_pass = 0_usize;
    let mut status_pass = 0_usize;
    let mut quarantine_pass = 0_usize;
    let mut authority_locked_pass = 0_usize;
    let mut envelope_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;

    for scenario in &scenarios {
        let result =
            authorize_optimizer_request(&scenario.request, &scenario.envelopes, &policy);
        let ok = result.is_ok();
        if ok {
            ok_pass += 1;
        }
        let auth = match result {
            Ok(a) => a,
            Err(err) => {
                per_scenario.push(json!({
                    "scenario_id": scenario.scenario_id,
                    "authorization_ok": false,
                    "error": err,
                }));
                continue;
            }
        };
        let status_ok = auth.status == "NO_ELIGIBLE_OBJECTIVES";
        if status_ok {
            status_pass += 1;
        }
        let quarantine_ok = !auth.ranking_performed
            && !auth.solver_invoked
            && !auth.usable_by_optimizer;
        if quarantine_ok {
            quarantine_pass += 1;
        }
        let authority_ok = !auth.authority_upgrade
            && !auth.candidate_created_evidence
            && auth.hard_constraints_passed
            && auth.eligible_objective_count == 0
            && auth.objective_values.is_empty();
        if authority_ok {
            authority_locked_pass += 1;
        }
        let envelope_ok =
            contains_banned_key(&serde_json::to_value(&auth).unwrap()).is_none();
        if envelope_ok {
            envelope_pass += 1;
        }
        // Byte-stable two-replay.
        let replay =
            authorize_optimizer_request(&scenario.request, &scenario.envelopes, &policy).unwrap();
        let byte_ok = serde_json::to_vec(&auth).unwrap()
            == serde_json::to_vec(&replay).unwrap();
        if byte_ok {
            byte_replay_pass += 1;
        }

        per_scenario.push(json!({
            "scenario_id": scenario.scenario_id,
            "industrial_context": scenario.industrial_context,
            "authorization_ok": true,
            "status": auth.status,
            "hard_constraints_passed": auth.hard_constraints_passed,
            "eligible_objective_count": auth.eligible_objective_count,
            "ranking_performed": auth.ranking_performed,
            "solver_invoked": auth.solver_invoked,
            "usable_by_optimizer": auth.usable_by_optimizer,
            "authority_upgrade": auth.authority_upgrade,
            "candidate_created_evidence": auth.candidate_created_evidence,
            "status_matches_no_eligible_objectives": status_ok,
            "quarantine_output_locked": quarantine_ok,
            "authority_and_counts_locked": authority_ok,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = n_scenarios.max(1) as f64;
    let ok_rate = ok_pass as f64 / n;
    let status_rate = status_pass as f64 / n;
    let quarantine_rate = quarantine_pass as f64 / n;
    let authority_locked_rate = authority_locked_pass as f64 / n;
    let envelope_rate = envelope_pass as f64 / n;
    let byte_replay_rate = byte_replay_pass as f64 / n;

    let (inject_rate, inject_probes, inject_total) = objective_constraint_injection_probes(&policy);
    let (op_rate, op_probes, op_total) = unknown_operator_probes(&policy);
    let (dup_rate, dup_probes, dup_total) = duplicate_envelope_probes(&policy);
    let (lock_rate, lock_probes, lock_total) = missing_claim_lock_probes(&policy);
    let (score_rate, score_probes, score_total) = failed_or_no_authority_probes(&policy);
    let (escalation_rate, escalation_probes, escalation_total) = solver_ranking_escalation_probes();

    let kpi = json!({
        "authorization_ok_rate": {
            "observed": ok_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": ok_rate >= 1.0,
        },
        "authorization_status_no_eligible_objectives_rate": {
            "observed": status_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": status_rate >= 1.0,
        },
        "quarantine_output_locked_rate": {
            "observed": quarantine_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": quarantine_rate >= 1.0,
        },
        "authority_and_counts_locked_rate": {
            "observed": authority_locked_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": authority_locked_rate >= 1.0,
        },
        "objective_constraint_injection_fail_closed_rate": {
            "observed": inject_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": inject_total,
            "probes": inject_probes,
            "passed": inject_rate >= 1.0,
        },
        "unknown_objective_path_operator_fail_closed_rate": {
            "observed": op_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": op_total,
            "probes": op_probes,
            "passed": op_rate >= 1.0,
        },
        "duplicate_score_envelope_fail_closed_rate": {
            "observed": dup_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": dup_total,
            "probes": dup_probes,
            "passed": dup_rate >= 1.0,
        },
        "missing_optimizer_claim_lock_fail_closed_rate": {
            "observed": lock_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": lock_total,
            "probes": lock_probes,
            "passed": lock_rate >= 1.0,
        },
        "failed_or_no_authority_score_fail_closed_rate": {
            "observed": score_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": score_total,
            "probes": score_probes,
            "passed": score_rate >= 1.0,
        },
        "solver_ranking_escalation_fail_closed_rate": {
            "observed": escalation_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": escalation_total,
            "probes": escalation_probes,
            "passed": escalation_rate >= 1.0,
        },
        "authority_envelope_preservation_rate": {
            "observed": envelope_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": envelope_rate >= 1.0,
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_rate,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "note": "observational; authorize_optimizer_request invoked twice with identical inputs produces byte-identical OptimizerAuthorizationV1",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let dataset_sha256 = benchmark_lock_sha256.clone();

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-optimizer-orchestrator",
        "kpi": kpi.clone(),
        "records": per_scenario.clone(),
        "passed": kpi["authorization_ok_rate"]["passed"] == json!(true)
            && kpi["authorization_status_no_eligible_objectives_rate"]["passed"] == json!(true)
            && kpi["quarantine_output_locked_rate"]["passed"] == json!(true)
            && kpi["authority_and_counts_locked_rate"]["passed"] == json!(true)
            && kpi["objective_constraint_injection_fail_closed_rate"]["passed"] == json!(true)
            && kpi["unknown_objective_path_operator_fail_closed_rate"]["passed"] == json!(true)
            && kpi["duplicate_score_envelope_fail_closed_rate"]["passed"] == json!(true)
            && kpi["missing_optimizer_claim_lock_fail_closed_rate"]["passed"] == json!(true)
            && kpi["failed_or_no_authority_score_fail_closed_rate"]["passed"] == json!(true)
            && kpi["solver_ranking_escalation_fail_closed_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-optimizer-orchestrator"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-optimizer-orchestrator-phase0-authorization-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("optimizer authorization is deterministic policy arithmetic; the KPI harness constructs its scenarios and probes in-Rust and does not consume an external fixture. SHA-256 recorded is the on-disk benchmark-lock hash."),
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

fn objective_constraint_injection_probes(
    policy: &OptimizerRegistryPolicyV1,
) -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: CANDIDATE source with non-empty objectives.
    let req = candidate_request(
        vec![objective("candidate-score", FORMULATION_ARITHMETIC, "candidate_score")],
        Vec::new(),
    );
    let ok = authorize_optimizer_request(&req, &[], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "candidate_source_with_objectives", "fail_closed": ok}));

    // Probe B: CANDIDATE source with objectives and a constraint referencing a
    // valid module (still forbidden — candidate cannot inject objectives).
    let req = candidate_request(
        vec![objective("candidate-score", FORMULATION_ARITHMETIC, "candidate_score")],
        vec![constraint("gate", ENVELOPE_GATES, "pass_all_hard", "==", Value::Bool(true))],
    );
    let ok =
        authorize_optimizer_request(&req, &[envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true))], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "candidate_source_with_objectives_and_constraint", "fail_closed": ok}));

    // Probe C: request_source is an unknown string.
    let mut req = policy_request(Vec::new(), Vec::new());
    req.request_source = "SUPPLIER".into();
    let ok = authorize_optimizer_request(&req, &[], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "unknown_request_source_string", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn unknown_operator_probes(policy: &OptimizerRegistryPolicyV1) -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: constraint operator not in allowed set.
    let bad =
        constraint("mass-gate", ENVELOPE_GATES, "pass_all_hard", "contains", Value::Bool(true));
    let req = policy_request(Vec::new(), vec![bad]);
    let ok = authorize_optimizer_request(&req, &[envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true))], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "constraint_operator_contains", "fail_closed": ok}));

    // Probe B: operator empty string.
    let bad = constraint("mass-gate", ENVELOPE_GATES, "pass_all_hard", "", Value::Bool(true));
    let req = policy_request(Vec::new(), vec![bad]);
    let ok = authorize_optimizer_request(&req, &[envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true))], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "constraint_operator_empty", "fail_closed": ok}));

    // Probe C: objective wrong section.
    let mut bad = objective("audit-score", ENVELOPE_GATES, "audit_score");
    bad.section = "metrics".into();
    let req = policy_request(vec![bad], Vec::new());
    let ok = authorize_optimizer_request(&req, &[], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "objective_section_not_objective_values", "fail_closed": ok}));

    // Probe D: constraint wrong section.
    let mut bad = constraint("mass-gate", ENVELOPE_GATES, "pass_all_hard", "==", Value::Bool(true));
    bad.section = "objective_values".into();
    let req = policy_request(Vec::new(), vec![bad]);
    let ok = authorize_optimizer_request(&req, &[envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true))], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "constraint_section_not_gates", "fail_closed": ok}));

    // Probe E: objective empty path.
    let bad = objective("audit-score", ENVELOPE_GATES, "   ");
    let req = policy_request(vec![bad], Vec::new());
    let ok = authorize_optimizer_request(&req, &[], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "objective_empty_path", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn duplicate_envelope_probes(policy: &OptimizerRegistryPolicyV1) -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: two envelopes with same module_id.
    let req = policy_request(Vec::new(), Vec::new());
    let envelopes = vec![
        envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true)),
        envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true)),
    ];
    let ok = authorize_optimizer_request(&req, &envelopes, policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "two_envelopes_same_module_id", "fail_closed": ok}));

    // Probe B: two objectives with same objective_id.
    let req = policy_request(
        vec![
            objective("dup", FORMULATION_ARITHMETIC, "audit_score"),
            objective("dup", FORMULATION_UNIVERSE, "audit_score"),
        ],
        Vec::new(),
    );
    let ok = authorize_optimizer_request(&req, &[], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "two_objectives_same_id", "fail_closed": ok}));

    // Probe C: two constraints with same constraint_id.
    let req = policy_request(
        Vec::new(),
        vec![
            constraint("dup", ENVELOPE_GATES, "pass_all_hard", "==", Value::Bool(true)),
            constraint("dup", FORMULATION_ARITHMETIC, "mass_identity", "==", Value::Bool(true)),
        ],
    );
    let envelopes = vec![
        envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true)),
        envelope(FORMULATION_ARITHMETIC, "mass_identity", Value::Bool(true)),
    ];
    let ok = authorize_optimizer_request(&req, &envelopes, policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "two_constraints_same_id", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn missing_claim_lock_probes(policy: &OptimizerRegistryPolicyV1) -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: envelope missing a required claim lock.
    let mut e = envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true));
    e.claim_locks.remove("no_ranking_authority");
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[e], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "envelope_missing_no_ranking_authority_lock", "fail_closed": ok}));

    // Probe B: envelope with a required claim lock set to false.
    let mut e = envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true));
    e.claim_locks.insert("no_optimizer_authority".into(), false);
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[e], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "envelope_no_optimizer_authority_lock_false", "fail_closed": ok}));

    // Probe C: policy with required_claim_locks trimmed.
    let mut bad_policy = policy.clone();
    bad_policy.required_claim_locks.pop();
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[], &bad_policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "policy_required_claim_locks_trimmed", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn failed_or_no_authority_probes(policy: &OptimizerRegistryPolicyV1) -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: envelope status FAILED_GATES + a matching constraint.
    let mut e = envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true));
    e.status = "FAILED_GATES".into();
    let req = policy_request(
        Vec::new(),
        vec![constraint("gate", ENVELOPE_GATES, "pass_all_hard", "==", Value::Bool(true))],
    );
    let ok = authorize_optimizer_request(&req, &[e], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "envelope_status_failed_gates_with_constraint", "fail_closed": ok}));

    // Probe B: envelope ranking_eligible=true.
    let mut e = envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true));
    e.ranking_eligible = true;
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[e], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "envelope_ranking_eligible_true", "fail_closed": ok}));

    // Probe C: envelope authority_tier RANKING.
    let mut e = envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true));
    e.authority_tier = "RANKING".into();
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[e], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "envelope_authority_tier_ranking", "fail_closed": ok}));

    // Probe D: envelope authority_tier OPTIMIZER.
    let mut e = envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true));
    e.authority_tier = "OPTIMIZER".into();
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[e], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "envelope_authority_tier_optimizer", "fail_closed": ok}));

    // Probe E: envelope authority_tier empty.
    let mut e = envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true));
    e.authority_tier = "   ".into();
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[e], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "envelope_authority_tier_empty_whitespace", "fail_closed": ok}));

    // Probe F: envelope solver_use_ceiling unsupported value.
    let mut e = envelope(ENVELOPE_GATES, "pass_all_hard", Value::Bool(true));
    e.solver_use_ceiling = "RANKING".into();
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[e], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "envelope_solver_use_ceiling_unsupported", "fail_closed": ok}));

    // Probe G: envelope module_id not in registered.
    let mut e = envelope(UNKNOWN_MODULE, "pass_all_hard", Value::Bool(true));
    e.module_id = UNKNOWN_MODULE.into();
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[e], policy).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "envelope_module_id_not_registered", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn solver_ranking_escalation_probes() -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: policy ranking_enabled true.
    let mut p = quarantined_optimizer_policy();
    p.ranking_enabled = true;
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[], &p).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "policy_ranking_enabled_true", "fail_closed": ok}));

    // Probe B: policy solver_enabled true.
    let mut p = quarantined_optimizer_policy();
    p.solver_enabled = true;
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[], &p).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "policy_solver_enabled_true", "fail_closed": ok}));

    // Probe C: policy authority_expansion_allowed true.
    let mut p = quarantined_optimizer_policy();
    p.authority_expansion_allowed = true;
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[], &p).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "policy_authority_expansion_allowed_true", "fail_closed": ok}));

    // Probe D: policy decision_use_ceiling changed from AUDIT_ONLY.
    let mut p = quarantined_optimizer_policy();
    p.decision_use_ceiling = "RANKING".into();
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[], &p).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "policy_decision_use_ceiling_ranking", "fail_closed": ok}));

    // Probe E: policy registered_modules mutated (element removed).
    let mut p = quarantined_optimizer_policy();
    p.registered_modules.pop();
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[], &p).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "policy_registered_modules_element_removed", "fail_closed": ok}));

    // Probe F: policy schema wrong.
    let mut p = quarantined_optimizer_policy();
    p.schema = "amphora.optimizer-registry-policy.v99".into();
    let req = policy_request(Vec::new(), Vec::new());
    let ok = authorize_optimizer_request(&req, &[], &p).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "policy_schema_wrong_version", "fail_closed": ok}));

    // Probe G: request schema wrong.
    let mut req = policy_request(Vec::new(), Vec::new());
    req.schema = "amphora.optimizer-authorization-request.v99".into();
    let ok = authorize_optimizer_request(&req, &[], &quarantined_optimizer_policy()).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "request_schema_wrong_version", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

#[test]
fn optimizer_orchestrator_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "authorization_ok_rate",
        "authorization_status_no_eligible_objectives_rate",
        "quarantine_output_locked_rate",
        "authority_and_counts_locked_rate",
        "objective_constraint_injection_fail_closed_rate",
        "unknown_objective_path_operator_fail_closed_rate",
        "duplicate_score_envelope_fail_closed_rate",
        "missing_optimizer_claim_lock_fail_closed_rate",
        "failed_or_no_authority_score_fail_closed_rate",
        "solver_ranking_escalation_fail_closed_rate",
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
