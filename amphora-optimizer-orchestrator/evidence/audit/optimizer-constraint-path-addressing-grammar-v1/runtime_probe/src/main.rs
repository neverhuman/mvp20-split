//! LIVE Rust differential probe for the amphora-optimizer-orchestrator
//! constraint/display PATH-ADDRESSING surface.
//!
//! Executes the REAL runtime, linked as a library:
//!   site A -- `amphora_core::authorize_optimizer_request`
//!             (constraint path resolution inside the reference monitor)
//!   site B -- `amphora_core::rank_candidates`
//!             (display-KPI path resolution via the private `envelope_value`)
//! Both sites implement the same declared dotted `section`+`path` grammar.
//! This probe is NOT a re-implementation and contains no copy of either
//! resolver: site A is identified purely black-box by equality probing, and
//! site B returns its resolved value verbatim in `display_kpis`.
//!
//! Emits one deterministic JSON object per case, in corpus order, to stdout.
//! No randomness, no clock, no filesystem writes, no network.

use amphora_core::{
    authorize_optimizer_request, quarantined_optimizer_policy, rank_candidates, KpiProfile,
    OptimizerAuthorizationRequestV1, OptimizerEnvelopeV1,
};
use serde_json::{json, Value};
use std::io::{self, Read, Write};

const MODULE: &str = "amphora-envelope-gates";
const LOCKS: [&str; 10] = [
    "no_ranking_authority",
    "no_optimizer_authority",
    "no_release_authority",
    "no_qualification_authority",
    "no_patentability_authority",
    "fto_not_performed",
    "no_procurement_authority",
    "no_regulatory_authority",
    "no_safety_authority",
    "no_product_performance_authority",
];

fn locks() -> Value {
    let mut map = serde_json::Map::new();
    for lock in LOCKS {
        map.insert(lock.to_string(), json!(true));
    }
    Value::Object(map)
}

/// Envelope document in the shape site A consumes (OptimizerEnvelopeV1).
fn site_a_envelope(gates: &Value) -> Value {
    json!({
        "module_id": MODULE,
        "status": "SCORED",
        "authority_tier": "REAL_ARITHMETIC",
        "solver_use_ceiling": "CONSTRAINT_ONLY",
        "ranking_eligible": false,
        "usable_by_optimizer": false,
        "objective_values": {},
        "gates": gates,
        "claim_locks": locks(),
    })
}

/// Result document in the shape site B consumes (raw score envelope).
fn site_b_result(gates: &Value) -> Value {
    json!({
        "candidate": {"candidate_id": "c1"},
        "score_envelopes": [{
            "module_id": MODULE,
            "status": "SCORED",
            "authority_tier": "REAL_ARITHMETIC",
            "metrics": {
                "solver_use": "CONSTRAINT_ONLY",
                "authority_receipt": {"ranking_eligible": false},
            },
            "usable_by_optimizer": false,
            "objective_values": {},
            "gates": gates,
            "claim_locks": locks(),
        }],
    })
}

fn display_profile(path: &str) -> KpiProfile {
    serde_json::from_value(json!({
        "schema": "amphora.dashboard-kpi-profile.v1",
        "profile_id": "path-addressing-probe",
        "objectives": [],
        "hard_constraints": [],
        "display_kpis": [{
            "id": "d1",
            "module_id": MODULE,
            "section": "gates",
            "path": path,
            "label": "probe",
            "unit": "probe",
            "direction": "context",
        }],
    }))
    .expect("display profile")
}

fn constraint_request(path: &str, expected: &Value) -> Value {
    json!({
        "schema": "amphora.optimizer-authorization-request.v1",
        "request_source": "POLICY",
        "objectives": [],
        "hard_constraints": [{
            "constraint_id": "c1",
            "module_id": MODULE,
            "section": "gates",
            "path": path,
            "operator": "==",
            "expected": expected,
        }],
    })
}

/// Runs site A once and returns (verdict, reason, quarantine_ok).
fn site_a_call(gates: &Value, path: &str, expected: &Value) -> (String, Value, Value) {
    let envelopes: Vec<OptimizerEnvelopeV1> =
        match serde_json::from_value(json!([site_a_envelope(gates)])) {
            Ok(value) => value,
            Err(error) => {
                return (
                    "ENVELOPE_PARSE_REJECT".into(),
                    json!(error.to_string()),
                    Value::Null,
                )
            }
        };
    let request: OptimizerAuthorizationRequestV1 =
        match serde_json::from_value(constraint_request(path, expected)) {
            Ok(value) => value,
            Err(error) => {
                return (
                    "REQUEST_PARSE_REJECT".into(),
                    json!(error.to_string()),
                    Value::Null,
                )
            }
        };
    // ---- LIVE RUNTIME CALL (site A) ----
    match authorize_optimizer_request(&request, &envelopes, &quarantined_optimizer_policy()) {
        Ok(auth) => {
            let quarantine_ok = auth.status == "NO_ELIGIBLE_OBJECTIVES"
                && auth.hard_constraints_passed
                && auth.eligible_objective_count == 0
                && auth.objective_values.is_empty()
                && !auth.ranking_performed
                && !auth.solver_invoked
                && !auth.usable_by_optimizer
                && !auth.authority_upgrade
                && !auth.candidate_created_evidence;
            ("ACCEPT".into(), Value::Null, json!(quarantine_ok))
        }
        Err(reason) => ("REJECT".into(), json!(reason), Value::Null),
    }
}

/// Runs site B once and returns (resolved, value, feasible, failed_modules).
///
/// NOTE: the profile driving site B declares NO hard constraints, so
/// `feasible` here reports the verdict of a constraint-free authorization,
/// not an endorsement of the envelope.
fn site_b_call(result: &Value, path: &str) -> (bool, Value, bool, usize) {
    // ---- LIVE RUNTIME CALL (site B) ----
    let ranked = rank_candidates(std::slice::from_ref(result), &display_profile(path));
    let candidate = ranked.first().expect("one ranked candidate");
    let failed = candidate.failed_modules;
    match candidate.display_kpis.first() {
        Some(kpi) => (true, kpi.value.clone(), candidate.feasible, failed),
        None => (false, Value::Null, candidate.feasible, failed),
    }
}

fn main() {
    let mut raw = String::new();
    io::stdin().read_to_string(&mut raw).expect("read corpus");
    let corpus: Value = serde_json::from_str(&raw).expect("parse corpus");
    let fixtures = corpus["fixtures"].as_array().expect("fixtures").clone();
    let paths = corpus["paths"].as_array().expect("paths").clone();
    let probes = corpus["probe_values"].as_array().expect("probes").clone();

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());

    for fixture in &fixtures {
        let fid = fixture["fixture_id"].as_str().unwrap();
        let gates = &fixture["gates"];
        let result = site_b_result(gates);

        for path in &paths {
            let pid = path["path_id"].as_str().unwrap();
            let text = path["text"].as_str().unwrap();

            // ---- site A: black-box equality sweep -----------------------
            for probe in &probes {
                let vid = probe["probe_id"].as_str().unwrap();
                let (verdict, reason, quarantine_ok) = site_a_call(gates, text, &probe["value"]);
                let record = json!({
                    "site": "A",
                    "case_id": format!("A|{fid}|{pid}|{vid}"),
                    "fixture_id": fid,
                    "path_id": pid,
                    "probe_id": vid,
                    "verdict": verdict,
                    "reason": reason,
                    "quarantine_ok": quarantine_ok,
                });
                writeln!(out, "{}", serde_json::to_string(&record).unwrap()).unwrap();
            }

            // ---- site B: direct read-back -------------------------------
            let (resolved, value, feasible, failed_modules) = site_b_call(&result, text);
            let record = json!({
                "site": "B",
                "case_id": format!("B|{fid}|{pid}"),
                "fixture_id": fid,
                "path_id": pid,
                "resolved": resolved,
                "value": value,
                "feasible": feasible,
                "failed_modules": failed_modules,
            });
            writeln!(out, "{}", serde_json::to_string(&record).unwrap()).unwrap();
        }
    }

    // ---- site M: mediation completeness -----------------------------------
    // Does display-side path resolution happen for envelopes that the
    // reference monitor refuses? Each variant mutates exactly one admission
    // field of an otherwise-clean envelope carrying gates {"alpha":1001,...}.
    let base_gates = fixtures[0]["gates"].clone();
    let mediation: Vec<(&str, &str, Value)> = vec![
        ("M1_ranking_eligible", "ranking_eligible", json!(true)),
        ("M2_usable_by_optimizer", "usable_by_optimizer", json!(true)),
        ("M3_objective_values", "objective_values", json!({"o": 1})),
        ("M4_authority_tier_RANKING", "authority_tier", json!("RANKING")),
        ("M5_solver_ceiling_ENABLED", "solver_use_ceiling", json!("ENABLED")),
        ("M6_claim_lock_dropped", "claim_locks", json!({"no_ranking_authority": true})),
        ("M7_status_not_scored", "status", json!("FAILED")),
    ];
    for (variant, field, value) in &mediation {
        // site A envelope with the single mutation applied
        let mut env_a = site_a_envelope(&base_gates);
        env_a[*field] = value.clone();
        let parsed_a: Result<Vec<OptimizerEnvelopeV1>, _> = serde_json::from_value(json!([env_a]));
        let request: OptimizerAuthorizationRequestV1 =
            serde_json::from_value(constraint_request("alpha", &json!(1001))).unwrap();
        let (a_verdict, a_reason) = match parsed_a {
            Err(error) => ("ENVELOPE_PARSE_REJECT".to_string(), json!(error.to_string())),
            Ok(envs) => {
                match authorize_optimizer_request(&request, &envs, &quarantined_optimizer_policy())
                {
                    Ok(_) => ("ACCEPT".to_string(), Value::Null),
                    Err(reason) => ("REJECT".to_string(), json!(reason)),
                }
            }
        };

        // site B result document with the corresponding mutation applied
        let mut result_b = site_b_result(&base_gates);
        let envelope_b = &mut result_b["score_envelopes"][0];
        match *field {
            "solver_use_ceiling" => envelope_b["metrics"]["solver_use"] = value.clone(),
            "ranking_eligible" => {
                envelope_b["metrics"]["authority_receipt"]["ranking_eligible"] = value.clone()
            }
            other => envelope_b[other] = value.clone(),
        }
        let (b_resolved, b_value, b_feasible, b_failed) = site_b_call(&result_b, "alpha");

        let record = json!({
            "site": "M",
            "case_id": format!("M|{variant}"),
            "variant": variant,
            "mutated_field": field,
            "site_a_verdict": a_verdict,
            "site_a_reason": a_reason,
            "site_b_resolved": b_resolved,
            "site_b_value": b_value,
            "site_b_feasible": b_feasible,
            "site_b_failed_modules": b_failed,
        });
        writeln!(out, "{}", serde_json::to_string(&record).unwrap()).unwrap();
    }

    out.flush().unwrap();
}
