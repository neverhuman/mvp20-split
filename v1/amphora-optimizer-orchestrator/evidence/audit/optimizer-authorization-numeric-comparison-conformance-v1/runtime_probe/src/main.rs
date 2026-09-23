//! LIVE Rust differential probe for the amphora-optimizer-orchestrator
//! hard-constraint numeric comparison surface.
//!
//! Executes the REAL runtime (`amphora_core::authorize_optimizer_request`,
//! amphora-core/src/lib.rs) over the locked JSON-text literal corpus. Every
//! numeric literal enters through the RFC 8259 front door (serde_json parse of
//! the envelope / request documents), so parser reachability is exercised
//! exactly as a hostile POLICY- or CANDIDATE-sourced request would exercise it.
//!
//! Emits one deterministic JSON object per case, in corpus order, to stdout.
//! No randomness, no clock, no filesystem writes.

use amphora_core::{
    authorize_optimizer_request, quarantined_optimizer_policy, OptimizerAuthorizationRequestV1,
    OptimizerEnvelopeV1,
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

fn locks_json() -> String {
    let mut s = String::from("{");
    for (i, l) in LOCKS.iter().enumerate() {
        if i > 0 {
            s.push(',');
        }
        s.push_str(&format!("\"{l}\":true"));
    }
    s.push('}');
    s
}

fn main() {
    let mut raw = String::new();
    io::stdin().read_to_string(&mut raw).expect("read corpus");
    let corpus: Value = serde_json::from_str(&raw).expect("parse corpus");
    let literals = corpus["literals"].as_array().expect("literals").clone();
    let operators = corpus["operators"].as_array().expect("operators").clone();
    let locks = locks_json();

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());

    for gate in &literals {
        let gid = gate["id"].as_str().unwrap();
        let gtext = gate["text"].as_str().unwrap();
        // Envelope document: the gate value arrives as raw JSON text.
        let env_doc = format!(
            "[{{\"module_id\":\"{MODULE}\",\"status\":\"SCORED\",\
             \"authority_tier\":\"REAL_ARITHMETIC\",\
             \"solver_use_ceiling\":\"CONSTRAINT_ONLY\",\
             \"ranking_eligible\":false,\"usable_by_optimizer\":false,\
             \"objective_values\":{{}},\"gates\":{{\"g\":{gtext}}},\
             \"claim_locks\":{locks}}}]"
        );
        let envelopes: Option<Vec<OptimizerEnvelopeV1>> = serde_json::from_str(&env_doc).ok();

        for expected in &literals {
            let eid = expected["id"].as_str().unwrap();
            let etext = expected["text"].as_str().unwrap();
            for op in &operators {
                let opv = op.as_str().unwrap();
                let case_id = format!("{gid}|{eid}|{opv}");
                let req_doc = format!(
                    "{{\"schema\":\"amphora.optimizer-authorization-request.v1\",\
                     \"request_source\":\"POLICY\",\"objectives\":[],\
                     \"hard_constraints\":[{{\"constraint_id\":\"c1\",\
                     \"module_id\":\"{MODULE}\",\"section\":\"gates\",\"path\":\"g\",\
                     \"operator\":\"{opv}\",\"expected\":{etext}}}]}}"
                );
                let request: Option<OptimizerAuthorizationRequestV1> =
                    serde_json::from_str(&req_doc).ok();

                let rec = match (&envelopes, &request) {
                    (None, None) => json!({
                        "case_id": case_id, "verdict": "PARSE_REJECT",
                        "parse_reject_site": "BOTH", "reason": Value::Null,
                        "quarantine_ok": Value::Null}),
                    (None, Some(_)) => json!({
                        "case_id": case_id, "verdict": "PARSE_REJECT",
                        "parse_reject_site": "ENVELOPE_GATE_VALUE", "reason": Value::Null,
                        "quarantine_ok": Value::Null}),
                    (Some(_), None) => json!({
                        "case_id": case_id, "verdict": "PARSE_REJECT",
                        "parse_reject_site": "CONSTRAINT_EXPECTED_VALUE", "reason": Value::Null,
                        "quarantine_ok": Value::Null}),
                    (Some(envs), Some(req)) => {
                        // ---- LIVE RUNTIME CALL ----
                        match authorize_optimizer_request(req, envs, &quarantined_optimizer_policy())
                        {
                            Ok(auth) => {
                                let q = auth.status == "NO_ELIGIBLE_OBJECTIVES"
                                    && auth.hard_constraints_passed
                                    && auth.eligible_objective_count == 0
                                    && auth.objective_values.is_empty()
                                    && !auth.ranking_performed
                                    && !auth.solver_invoked
                                    && !auth.usable_by_optimizer
                                    && !auth.authority_upgrade
                                    && !auth.candidate_created_evidence;
                                json!({"case_id": case_id, "verdict": "ACCEPT",
                                       "parse_reject_site": Value::Null,
                                       "reason": Value::Null, "quarantine_ok": q})
                            }
                            Err(reason) => json!({"case_id": case_id, "verdict": "REJECT",
                                                  "parse_reject_site": Value::Null,
                                                  "reason": reason, "quarantine_ok": Value::Null}),
                        }
                    }
                };
                writeln!(out, "{}", serde_json::to_string(&rec).unwrap()).unwrap();
            }
        }
    }
    out.flush().unwrap();
}
