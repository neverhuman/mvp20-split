// AUDIT_ONLY live-runtime probe for amphora-optimizer-orchestrator (T-09).
// Calls the REAL compiled amphora_core::authorize_optimizer_request (not a
// re-implementation) via a standalone binary with path deps only.
use amphora_core::{
    authorize_optimizer_request, quarantined_optimizer_policy, OptimizerAuthorizationRequestV1,
    OptimizerAuthorizationV1, OptimizerConstraintRequestV1, OptimizerEnvelopeV1,
    OptimizerObjectiveRequestV1, OptimizerRegistryPolicyV1,
};
use serde_json::{json, Value};
use std::collections::BTreeMap;

fn reached_forbidden_path(out: &OptimizerAuthorizationV1) -> bool {
    out.eligible_objective_count > 0
        || out.ranking_performed
        || out.solver_invoked
        || out.usable_by_optimizer
        || out.authority_upgrade
        || out.candidate_created_evidence
        || !out.objective_values.is_empty()
}

fn envelope_for(module_id: &str, policy: &OptimizerRegistryPolicyV1, gates: BTreeMap<String, Value>) -> OptimizerEnvelopeV1 {
    let mut claim_locks = BTreeMap::new();
    for lock in &policy.required_claim_locks {
        claim_locks.insert(lock.clone(), true);
    }
    OptimizerEnvelopeV1 {
        module_id: module_id.into(),
        status: "SCORED".into(),
        authority_tier: "EVIDENCE_ONLY".into(),
        solver_use_ceiling: "AUDIT_ONLY".into(),
        ranking_eligible: false,
        usable_by_optimizer: false,
        objective_values: BTreeMap::new(),
        gates,
        claim_locks,
    }
}

fn run_encoding(case_id: &str, description: &str, raw_json: &str, policy: &OptimizerRegistryPolicyV1, envelopes: &[OptimizerEnvelopeV1]) -> Value {
    let parsed: Result<OptimizerAuthorizationRequestV1, _> = serde_json::from_str(raw_json);
    match parsed {
        Err(e) => json!({
            "case_id": case_id,
            "description": description,
            "raw_json": raw_json,
            "parse_ok": false,
            "parse_error": e.to_string(),
            "authorize_ok": null,
            "authorize_error": null,
            "reached_forbidden_path": false,
            "blocked": true,
            "blocked_at": "serde_deserialization",
        }),
        Ok(req) => {
            let result = authorize_optimizer_request(&req, envelopes, policy);
            match result {
                Err(e) => json!({
                    "case_id": case_id,
                    "description": description,
                    "raw_json": raw_json,
                    "parse_ok": true,
                    "parse_error": null,
                    "authorize_ok": false,
                    "authorize_error": e,
                    "reached_forbidden_path": false,
                    "blocked": true,
                    "blocked_at": "authorize_optimizer_request",
                }),
                Ok(out) => {
                    let rfp = reached_forbidden_path(&out);
                    json!({
                        "case_id": case_id,
                        "description": description,
                        "raw_json": raw_json,
                        "parse_ok": true,
                        "parse_error": null,
                        "authorize_ok": true,
                        "authorize_error": null,
                        "output": {
                            "status": out.status,
                            "eligible_objective_count": out.eligible_objective_count,
                            "ranking_performed": out.ranking_performed,
                            "solver_invoked": out.solver_invoked,
                            "usable_by_optimizer": out.usable_by_optimizer,
                            "authority_upgrade": out.authority_upgrade,
                            "candidate_created_evidence": out.candidate_created_evidence,
                            "objective_values_len": out.objective_values.len(),
                        },
                        "reached_forbidden_path": rfp,
                        "blocked": !rfp,
                        "blocked_at": if rfp { "NONE_REACHED_FORBIDDEN_PATH" } else { "authorize_optimizer_request_output_locked" },
                    })
                }
            }
        }
    }
}

// Mutant surrogate: NOT part of the shipped module. A deliberately-defective
// copy used ONLY as a positive control, to prove the classifier above (and
// this probe) actually detects escalation when the property under test is
// violated. Two defects planted relative to the real authorize_optimizer_request:
//  (1) the CANDIDATE-objective-injection check is removed;
//  (2) eligible_objective_count/objective_values/ranking_performed/usable_by_optimizer
//      are computed FROM the request instead of being hardcoded locked constants.
fn mutant_authorize_with_defect(req: &OptimizerAuthorizationRequestV1) -> Result<OptimizerAuthorizationV1, String> {
    // defect (1): the real function's first content check here is
    //   `if request.request_source == "CANDIDATE" && !request.objectives.is_empty() { return Err(..) }`
    // -- intentionally NOT reproduced.
    let mut objective_values = BTreeMap::new();
    for o in &req.objectives {
        objective_values.insert(o.objective_id.clone(), "MUTANT_ESCALATED".to_string());
    }
    let eligible = req.objectives.len();
    Ok(OptimizerAuthorizationV1 {
        status: if eligible > 0 { "MUTANT_RANKED".into() } else { "NO_ELIGIBLE_OBJECTIVES".into() },
        hard_constraints_passed: true,
        eligible_objective_count: eligible, // defect (2)
        objective_values,                    // defect (2)
        ranking_performed: eligible > 0,     // defect (2)
        solver_invoked: false,
        usable_by_optimizer: eligible > 0,   // defect (2)
        authority_upgrade: false,
        candidate_created_evidence: false,
    })
}

fn main() {
    let policy = quarantined_optimizer_policy();
    let empty_envelopes: Vec<OptimizerEnvelopeV1> = vec![];

    // ---- 8 alternate-encoding injection attempts (ported from
    // amphora-ip-fto-guard/evidence/audit/counsel-assertion-detection-completeness-v1),
    // each attempting to smuggle a live objective declaration into a CANDIDATE-sourced
    // request (the boundary the code explicitly forbids for objectives).
    let cases: Vec<(&str, &str, String)> = vec![
        (
            "1-top-level-key",
            "extra top-level key carrying the smuggled objective alongside a schema-valid empty objectives array",
            json!({
                "schema": "amphora.optimizer-authorization-request.v1",
                "request_source": "CANDIDATE",
                "objectives": [],
                "hard_constraints": [],
                "objectives_override": [{"objective_id":"smuggle-1","module_id":"amphora-optimizer-orchestrator","section":"objective_values","path":"score"}]
            }).to_string(),
        ),
        (
            "2-array-container",
            "objectives value wrapped in an extra array layer (array-of-array container)",
            json!({
                "schema": "amphora.optimizer-authorization-request.v1",
                "request_source": "CANDIDATE",
                "objectives": [[{"objective_id":"smuggle-2","module_id":"amphora-optimizer-orchestrator","section":"objective_values","path":"score"}]],
                "hard_constraints": []
            }).to_string(),
        ),
        (
            "3-deeper-nesting",
            "objective declaration nested one level deeper than the schema-valid array",
            json!({
                "schema": "amphora.optimizer-authorization-request.v1",
                "request_source": "CANDIDATE",
                "objectives": {"objectives": [{"objective_id":"smuggle-3","module_id":"amphora-optimizer-orchestrator","section":"objective_values","path":"score"}]},
                "hard_constraints": []
            }).to_string(),
        ),
        (
            "4-key-case-variant",
            "capitalized key variant 'Objectives' in place of required 'objectives'",
            json!({
                "schema": "amphora.optimizer-authorization-request.v1",
                "request_source": "CANDIDATE",
                "Objectives": [{"objective_id":"smuggle-4","module_id":"amphora-optimizer-orchestrator","section":"objective_values","path":"score"}],
                "hard_constraints": []
            }).to_string(),
        ),
        (
            "5-alternate-key-name",
            "semantically-equivalent alternate key name 'objective_list' in place of 'objectives'",
            json!({
                "schema": "amphora.optimizer-authorization-request.v1",
                "request_source": "CANDIDATE",
                "objective_list": [{"objective_id":"smuggle-5","module_id":"amphora-optimizer-orchestrator","section":"objective_values","path":"score"}],
                "hard_constraints": []
            }).to_string(),
        ),
        (
            "6-semantic-alt-field",
            "objective smuggled through the hard_constraints field by mislabeling section as objective_values",
            json!({
                "schema": "amphora.optimizer-authorization-request.v1",
                "request_source": "CANDIDATE",
                "objectives": [],
                "hard_constraints": [{"constraint_id":"smuggle-6","module_id":"amphora-optimizer-orchestrator","section":"objective_values","path":"score","operator":"==","expected":1.0}]
            }).to_string(),
        ),
        (
            "7-string-container",
            "objectives value provided as a JSON-encoded string instead of a real array",
            json!({
                "schema": "amphora.optimizer-authorization-request.v1",
                "request_source": "CANDIDATE",
                "objectives": "[{\"objective_id\":\"smuggle-7\",\"module_id\":\"amphora-optimizer-orchestrator\",\"section\":\"objective_values\",\"path\":\"score\"}]",
                "hard_constraints": []
            }).to_string(),
        ),
        (
            "8-unicode-homoglyph-key",
            "unicode-homoglyph key: Cyrillic 'о' (U+043E) substituted for Latin 'o' in 'objectives'",
            json!({
                "schema": "amphora.optimizer-authorization-request.v1",
                "request_source": "CANDIDATE",
                "\u{043E}bjectives": [{"objective_id":"smuggle-8","module_id":"amphora-optimizer-orchestrator","section":"objective_values","path":"score"}],
                "hard_constraints": []
            }).to_string(),
        ),
    ];

    let mut encoding_results = vec![];
    for (id, desc, raw) in &cases {
        encoding_results.push(run_encoding(id, desc, raw, &policy, &empty_envelopes));
    }

    // ---- positive control: real vs mutant on a directly-constructed
    // (JSON-parsing bypassed) CANDIDATE request carrying a live objective ----
    let candidate_direct_request = OptimizerAuthorizationRequestV1 {
        schema: "amphora.optimizer-authorization-request.v1".into(),
        request_source: "CANDIDATE".into(),
        objectives: vec![OptimizerObjectiveRequestV1 {
            objective_id: "direct-smuggle".into(),
            module_id: "amphora-optimizer-orchestrator".into(),
            section: "objective_values".into(),
            path: "score".into(),
        }],
        hard_constraints: vec![],
    };
    let real_on_defect_input = authorize_optimizer_request(&candidate_direct_request, &empty_envelopes, &policy);
    let mutant_on_defect_input = mutant_authorize_with_defect(&candidate_direct_request);

    let real_blocked = real_on_defect_input.is_err();
    let mutant_reached = match &mutant_on_defect_input {
        Ok(out) => reached_forbidden_path(out),
        Err(_) => false,
    };

    let positive_control = json!({
        "planted_defect": "CANDIDATE-objective-injection check removed AND eligible_objective_count/objective_values/ranking_performed/usable_by_optimizer computed from the request instead of hardcoded locked constants",
        "how_planted": "mutant_authorize_with_defect() in this probe's own source: (1) omits the `if request.request_source == \"CANDIDATE\" && !request.objectives.is_empty() { return Err(...) }` guard present in amphora-core/src/lib.rs authorize_optimizer_request; (2) sets eligible_objective_count = req.objectives.len(), ranking_performed = eligible>0, usable_by_optimizer = eligible>0, objective_values populated from req.objectives, instead of the real function's hardcoded 0/false/false/empty-map literals",
        "input": "identical directly-constructed OptimizerAuthorizationRequestV1: request_source=CANDIDATE, objectives=[{objective_id: direct-smuggle, module_id: amphora-optimizer-orchestrator, section: objective_values, path: score}]",
        "real_function_result": {
            "blocked": real_blocked,
            "error": real_on_defect_input.as_ref().err().cloned(),
        },
        "mutant_function_result": {
            "reached_forbidden_path": mutant_reached,
            "output": mutant_on_defect_input.as_ref().ok().map(|o| json!({
                "status": o.status, "eligible_objective_count": o.eligible_objective_count,
                "ranking_performed": o.ranking_performed, "usable_by_optimizer": o.usable_by_optimizer,
                "objective_values_len": o.objective_values.len(),
            })),
        },
        "detected": mutant_reached && real_blocked,
        "evidence": format!(
            "real authorize_optimizer_request() -> Err({:?}) [blocked]; mutant_authorize_with_defect() on the SAME input -> Ok(eligible_objective_count={}, ranking_performed={}, usable_by_optimizer={}) [forbidden path reached] -- the classifier used above (reached_forbidden_path) correctly distinguishes the two",
            real_on_defect_input.err(),
            mutant_on_defect_input.as_ref().map(|o| o.eligible_objective_count).unwrap_or(999),
            mutant_on_defect_input.as_ref().map(|o| o.ranking_performed).unwrap_or(false),
            mutant_on_defect_input.as_ref().map(|o| o.usable_by_optimizer).unwrap_or(false),
        ),
    });

    // ---- founder-directive T2-09 attack: rank/aggregate-score/composition ----
    let all_29_envelopes: Vec<OptimizerEnvelopeV1> = policy
        .registered_modules
        .iter()
        .map(|m| {
            let mut gates = BTreeMap::new();
            gates.insert("risk_flag".to_string(), json!(true));
            gates.insert("status".to_string(), json!("PASS"));
            envelope_for(m, &policy, gates)
        })
        .collect();

    // sweep: how many valid POLICY-sourced objectives, 0..=10, referencing real
    // registered modules, all schema-valid and non-duplicated
    let mut sweep = vec![];
    for n in [0usize, 1, 2, 3, 5, 10] {
        let objectives: Vec<OptimizerObjectiveRequestV1> = policy
            .registered_modules
            .iter()
            .take(n)
            .enumerate()
            .map(|(i, m)| OptimizerObjectiveRequestV1 {
                objective_id: format!("policy-obj-{i}"),
                module_id: m.clone(),
                section: "objective_values".into(),
                path: "score".into(),
            })
            .collect();
        let req = OptimizerAuthorizationRequestV1 {
            schema: "amphora.optimizer-authorization-request.v1".into(),
            request_source: "POLICY".into(),
            objectives,
            hard_constraints: vec![],
        };
        let result = authorize_optimizer_request(&req, &all_29_envelopes, &policy);
        let entry = match &result {
            Ok(out) => json!({
                "n_objectives_fed": n,
                "authorize_ok": true,
                "status": out.status,
                "eligible_objective_count": out.eligible_objective_count,
                "ranking_performed": out.ranking_performed,
                "solver_invoked": out.solver_invoked,
                "objective_values_len": out.objective_values.len(),
                "rank_or_score_produced": reached_forbidden_path(out),
            }),
            Err(e) => json!({"n_objectives_fed": n, "authorize_ok": false, "error": e}),
        };
        sweep.push(entry);
    }

    // mutually contradictory hard_constraints on the SAME envelope/path: one
    // requires risk_flag==true (matches real gate), the other requires
    // risk_flag==false (contradicts it) -- both reference amphora-candidate-contract.
    let contradictory_req = OptimizerAuthorizationRequestV1 {
        schema: "amphora.optimizer-authorization-request.v1".into(),
        request_source: "POLICY".into(),
        objectives: vec![],
        hard_constraints: vec![
            OptimizerConstraintRequestV1 {
                constraint_id: "c-consistent".into(),
                module_id: "amphora-candidate-contract".into(),
                section: "gates".into(),
                path: "risk_flag".into(),
                operator: "==".into(),
                expected: json!(true),
            },
            OptimizerConstraintRequestV1 {
                constraint_id: "c-contradictory".into(),
                module_id: "amphora-candidate-contract".into(),
                section: "gates".into(),
                path: "risk_flag".into(),
                operator: "==".into(),
                expected: json!(false),
            },
        ],
    };
    let contradictory_result = authorize_optimizer_request(&contradictory_req, &all_29_envelopes, &policy);

    // fully-consistent (both satisfiable) constraint set for comparison
    let consistent_req = OptimizerAuthorizationRequestV1 {
        schema: "amphora.optimizer-authorization-request.v1".into(),
        request_source: "POLICY".into(),
        objectives: vec![],
        hard_constraints: vec![
            OptimizerConstraintRequestV1 {
                constraint_id: "c-1".into(),
                module_id: "amphora-candidate-contract".into(),
                section: "gates".into(),
                path: "risk_flag".into(),
                operator: "==".into(),
                expected: json!(true),
            },
            OptimizerConstraintRequestV1 {
                constraint_id: "c-2".into(),
                module_id: "amphora-candidate-contract".into(),
                section: "gates".into(),
                path: "status".into(),
                operator: "==".into(),
                expected: json!("PASS"),
            },
        ],
    };
    let consistent_result = authorize_optimizer_request(&consistent_req, &all_29_envelopes, &policy);

    let directive_attack = json!({
        "type_has_no_rank_or_score_field": true,
        "type_evidence": "OptimizerAuthorizationV1 fields (amphora-core/src/lib.rs:566-577): status:String, hard_constraints_passed:bool, eligible_objective_count:usize, objective_values:BTreeMap<String,String>, ranking_performed:bool, solver_invoked:bool, usable_by_optimizer:bool, authority_upgrade:bool, candidate_created_evidence:bool -- no numeric rank/score field exists in the type signature at all; objective_values is BTreeMap<String,String> (string-valued), not a numeric score map",
        "n_registered_modules_fed": all_29_envelopes.len(),
        "objective_count_sweep": sweep,
        "contradictory_envelope_test": {
            "constraints": ["amphora-candidate-contract.gates.risk_flag == true", "amphora-candidate-contract.gates.risk_flag == false"],
            "actual_gate_value": true,
            "result": match &contradictory_result {
                Ok(_) => json!({"authorize_ok": true}),
                Err(e) => json!({"authorize_ok": false, "error": e}),
            },
            "composed_as_and_not_average": contradictory_result.is_err(),
            "interpretation": "the failing contradictory constraint short-circuits the whole request to Err on first mismatch (strict AND / fail-closed); there is no partial-credit, averaged, or percentage-pass output anywhere in the return type or the loop logic",
        },
        "consistent_constraints_control": match &consistent_result {
            Ok(out) => json!({"authorize_ok": true, "hard_constraints_passed": out.hard_constraints_passed, "status": out.status, "rank_or_score_produced": reached_forbidden_path(out)}),
            Err(e) => json!({"authorize_ok": false, "error": e}),
        },
    });

    let report = json!({
        "encoding_results": encoding_results,
        "positive_control": positive_control,
        "directive_attack": directive_attack,
    });
    println!("{}", serde_json::to_string_pretty(&report).unwrap());
}
