//! amphora-model-card-authority :: T-07 authority-escalation-under-alternate-encodings-v1
//!
//! LIVE Rust differential probe. Links the REAL runtime crate amphora-core and
//! calls its real public entry points against hand-crafted `engine-result.v1`
//! -shaped JSON documents carrying a single amphora-model-card-authority score
//! envelope:
//!   - `amphora_core::rank_candidates` (site B) -- the raw-JSON ingestion
//!     boundary. This is the function any attacker-controlled or corrupted
//!     upstream (a spoofed engine-result.v1 document) actually crosses.
//!     Internally it calls the private `optimizer_envelopes` extractor
//!     (JSON-pointer + `.as_bool()`/`.as_str()` typed reads) then the public
//!     `authorize_optimizer_request` reference monitor.
//!   - `amphora_core::authorize_optimizer_request` (site A) -- called directly
//!     on typed `OptimizerEnvelopeV1` structs for the subset of encodings that
//!     are type-compatible, to recover the exact rejection reason string.
//!
//! Claim under attack (amphora-model-card-authority non_blocking_claim_locks):
//!   authority_registry_is_binding, failed_cards_cannot_rank.
//!
//! Attack shape: 6 authority-escalation cases (a card attempting to rank, or
//! claiming authority above its EVIDENCE_ONLY/DISABLED ceiling), each replayed
//! under >=3 alternate JSON encodings of the SAME semantic escalation attempt
//! (canonical-typed, stringly-typed, numerically-typed, duplicate-key,
//! nested/wrapped, misplaced-path, case-variant, whitespace-padded,
//! homoglyph) plus a nested-override nesting-depth variant. This is NOT a
//! re-run of least-privilege-authority-parity-v1 (which only ever mutated one
//! canonical field at a time with the field's native type) or
//! authority-lattice-completeness-v1 (which enumerated the status/ceiling
//! domain, not JSON encodings of an escalation attempt).
//!
//! Every case starts from a MAXIMALLY-COMPLIANT hypothetical
//! amphora-model-card-authority envelope (all 10
//! REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS satisfied, ranking_eligible=false,
//! usable_by_optimizer=false, authority_tier=EVIDENCE_ONLY [its real
//! manifest ceiling], solver_use_ceiling=DISABLED, objective_values={}) so
//! that the baseline case is proven `feasible=true` first -- this rules out a
//! vacuous "everything is always blocked regardless of input" harness, which
//! would make the escalation cases uninformative. Each case then mutates
//! EXACTLY one authority-relevant field, under each encoding, and re-checks.
//!
//! Emits one JSON record per (case, encoding) to stdout, plus a final summary
//! record. No randomness, no clock, no filesystem writes, no network.

use amphora_core::{
    authorize_optimizer_request, quarantined_optimizer_policy, rank_candidates, KpiProfile,
    OptimizerAuthorizationRequestV1, OptimizerEnvelopeV1,
};
use serde_json::{json, Value};
use std::io::{self, Write};

const MODULE: &str = "amphora-model-card-authority";

// amphora-core/src/phase0.rs REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS, transcribed
// (not re-exported at crate root; matches the constant used by
// quarantined_optimizer_policy()).
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

fn clean_locks() -> Value {
    let mut map = serde_json::Map::new();
    for lock in LOCKS {
        map.insert(lock.to_string(), json!(true));
    }
    Value::Object(map)
}

/// A maximally-compliant hypothetical amphora-model-card-authority envelope,
/// in the raw `score_envelopes[]` shape `rank_candidates` actually ingests.
/// authority_tier/solver_use here are the module's REAL manifest ceilings
/// (EVIDENCE_ONLY / DISABLED); everything else is the most permissive legal
/// value. This is the baseline every case mutates from.
fn baseline_envelope() -> Value {
    json!({
        "module_id": MODULE,
        "status": "SCORED",
        "authority_tier": "EVIDENCE_ONLY",
        "metrics": {
            "solver_use": "DISABLED",
            "authority_receipt": {"ranking_eligible": false}
        },
        "usable_by_optimizer": false,
        "objective_values": {},
        "gates": {},
        "claim_locks": clean_locks(),
    })
}

fn site_b_result(envelope: &Value) -> Value {
    json!({
        "candidate": {"candidate_id": "probe-candidate"},
        "score_envelopes": [envelope],
    })
}

fn empty_profile() -> KpiProfile {
    serde_json::from_value(json!({
        "schema": "amphora.dashboard-kpi-profile.v1",
        "profile_id": "t07-mca-authority-escalation-probe",
        "objectives": [],
        "hard_constraints": [],
        "display_kpis": [],
    }))
    .expect("empty profile")
}

/// site B: LIVE runtime call through the raw-JSON ingestion boundary.
fn site_b_feasible(envelope: &Value) -> bool {
    let result = site_b_result(envelope);
    let ranked = rank_candidates(std::slice::from_ref(&result), &empty_profile());
    let candidate = ranked.first().expect("one ranked candidate");
    assert!(
        !candidate.ranked,
        "structural invariant broken: `ranked` must be a hardcoded-false constant \
         in amphora_core::rank_candidates regardless of input -- this probe's own \
         premise (failed_cards_cannot_rank is enforced by `ranked` never being set) \
         would be void if this ever fired"
    );
    candidate.feasible
}

/// site A: LIVE runtime call through the typed reference-monitor entry point,
/// used only for the type-compatible canonical encoding of each case (it
/// recovers the exact rejection reason string; type-incompatible encodings
/// cannot even construct an `OptimizerEnvelopeV1` and are covered by site B).
fn site_a_verdict(envelope: &Value) -> (String, Value) {
    let envelopes: Vec<OptimizerEnvelopeV1> = match serde_json::from_value(json!([{
        "module_id": envelope["module_id"],
        "status": envelope["status"],
        "authority_tier": envelope["authority_tier"],
        "solver_use_ceiling": envelope["metrics"]["solver_use"],
        "ranking_eligible": envelope["metrics"]["authority_receipt"]["ranking_eligible"],
        "usable_by_optimizer": envelope["usable_by_optimizer"],
        "objective_values": envelope["objective_values"],
        "gates": envelope["gates"],
        "claim_locks": envelope["claim_locks"],
    }])) {
        Ok(value) => value,
        Err(error) => return ("ENVELOPE_TYPE_REJECT".into(), json!(error.to_string())),
    };
    let request: OptimizerAuthorizationRequestV1 = serde_json::from_value(json!({
        "schema": "amphora.optimizer-authorization-request.v1",
        "request_source": "POLICY",
        "objectives": [],
        "hard_constraints": [],
    }))
    .expect("request");
    match authorize_optimizer_request(&request, &envelopes, &quarantined_optimizer_policy()) {
        Ok(_) => ("ACCEPT".into(), Value::Null),
        Err(reason) => ("REJECT".into(), json!(reason)),
    }
}

struct Encoding {
    id: &'static str,
    describe: &'static str,
    apply: fn(Value) -> Value,
}

struct Case {
    id: &'static str,
    field: &'static str,
    refutation_criterion: &'static str,
    encodings: Vec<Encoding>,
}

fn set_ptr(mut env: Value, path: &str, value: Value) -> Value {
    *env.pointer_mut(path).expect("pointer exists") = value;
    env
}

fn main() {
    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());

    // ---- baseline sanity: the harness must be capable of feasible=true ----
    let baseline = baseline_envelope();
    let baseline_feasible_b = site_b_feasible(&baseline);
    let (baseline_verdict_a, baseline_reason_a) = site_a_verdict(&baseline);
    writeln!(
        out,
        "{}",
        serde_json::to_string(&json!({
            "record": "BASELINE",
            "site_b_feasible": baseline_feasible_b,
            "site_a_verdict": baseline_verdict_a,
            "site_a_reason": baseline_reason_a,
            "purpose": "proves the harness can reach feasible=true / ACCEPT when \
                        the card is genuinely compliant, so the escalation cases \
                        below are a real discriminator, not a vacuous always-block",
        }))
        .unwrap()
    );

    let cases: Vec<Case> = vec![
        Case {
            id: "C1_ranking_eligible_true",
            field: "/metrics/authority_receipt/ranking_eligible",
            refutation_criterion:
                "site_b_feasible becomes true (or site_a ACCEPTs) for ANY encoding \
                 while ranking_eligible is semantically true at this pointer",
            encodings: vec![
                Encoding { id: "bool_direct", describe: "canonical JSON boolean true",
                    apply: |e| set_ptr(e, "/metrics/authority_receipt/ranking_eligible", json!(true)) },
                Encoding { id: "string_typed", describe: "JSON string \"true\" instead of boolean",
                    apply: |e| set_ptr(e, "/metrics/authority_receipt/ranking_eligible", json!("true")) },
                Encoding { id: "int_typed", describe: "JSON number 1 instead of boolean",
                    apply: |e| set_ptr(e, "/metrics/authority_receipt/ranking_eligible", json!(1)) },
                Encoding { id: "nested_object_wrapper", describe: "object {value:true} instead of a bare boolean at the exact pointer",
                    apply: |e| set_ptr(e, "/metrics/authority_receipt/ranking_eligible", json!({"value": true, "override": true})) },
            ],
        },
        Case {
            id: "C2_usable_by_optimizer_true",
            field: "/usable_by_optimizer",
            refutation_criterion:
                "site_b_feasible becomes true for ANY encoding while \
                 usable_by_optimizer is semantically true (top-level) or a \
                 misplaced nested copy is honored in its place",
            encodings: vec![
                Encoding { id: "bool_direct", describe: "canonical JSON boolean true",
                    apply: |e| set_ptr(e, "/usable_by_optimizer", json!(true)) },
                Encoding { id: "string_typed", describe: "JSON string \"true\"",
                    apply: |e| set_ptr(e, "/usable_by_optimizer", json!("true")) },
                Encoding { id: "int_typed", describe: "JSON number 1",
                    apply: |e| set_ptr(e, "/usable_by_optimizer", json!(1)) },
                Encoding { id: "misplaced_nested_override", describe: "top-level stays false; a decoy copy is nested at /metrics/usable_by_optimizer=true",
                    apply: |e| { let mut e = e; e["metrics"]["usable_by_optimizer"] = json!(true); e } },
            ],
        },
        Case {
            id: "C3_authority_tier_above_ceiling",
            field: "/authority_tier",
            refutation_criterion:
                "site_b_feasible becomes true for ANY encoding whose string \
                 visually or semantically claims a forbidden RANKING/OPTIMIZER/\
                 PRODUCTION tier -- including near-miss encodings the exact-match \
                 denylist does not cover byte-for-byte",
            encodings: vec![
                Encoding { id: "direct_forbidden", describe: "canonical forbidden tier string \"RANKING\"",
                    apply: |e| set_ptr(e, "/authority_tier", json!("RANKING")) },
                Encoding { id: "lowercase_variant", describe: "case-folded \"ranking\"",
                    apply: |e| set_ptr(e, "/authority_tier", json!("ranking")) },
                Encoding { id: "whitespace_padded", describe: "trailing-space padded \"RANKING \"",
                    apply: |e| set_ptr(e, "/authority_tier", json!("RANKING ")) },
                Encoding { id: "cyrillic_homoglyph", describe: "Latin I -> Cyrillic \u{0406} homoglyph \"RANK\u{0406}NG\" (byte-distinct, visually identical)",
                    apply: |e| set_ptr(e, "/authority_tier", json!("RANK\u{0406}NG")) },
            ],
        },
        Case {
            id: "C4_solver_use_ceiling_enabled",
            field: "/metrics/solver_use",
            refutation_criterion:
                "site_b_feasible becomes true for ANY encoding claiming a \
                 solver_use_ceiling outside the {DISABLED,AUDIT_ONLY,\
                 CONSTRAINT_ONLY} allowlist",
            encodings: vec![
                Encoding { id: "direct_enabled", describe: "canonical out-of-allowlist \"ENABLED\"",
                    apply: |e| set_ptr(e, "/metrics/solver_use", json!("ENABLED")) },
                Encoding { id: "lowercase_variant", describe: "case-folded \"enabled\"",
                    apply: |e| set_ptr(e, "/metrics/solver_use", json!("enabled")) },
                Encoding { id: "whitespace_padded", describe: "leading-space padded \" DISABLED\" (attempts to pass as allowlisted by substring)",
                    apply: |e| set_ptr(e, "/metrics/solver_use", json!(" DISABLED")) },
                Encoding { id: "unicode_homoglyph", describe: "Cyrillic-substituted lookalike of an allowlisted value \"D\u{0406}SABLED\"",
                    apply: |e| set_ptr(e, "/metrics/solver_use", json!("D\u{0406}SABLED")) },
            ],
        },
        Case {
            id: "C5_claim_lock_spoofed_incomplete",
            field: "/claim_locks/no_ranking_authority",
            refutation_criterion:
                "site_b_feasible becomes true for ANY encoding in which a \
                 required zero-authority claim lock is absent, falsy, or \
                 present only as a differently-typed truthy value",
            encodings: vec![
                Encoding { id: "dropped_key", describe: "required lock key removed entirely from claim_locks",
                    apply: |e| { let mut e = e; e["claim_locks"].as_object_mut().unwrap().remove("no_ranking_authority"); e } },
                Encoding { id: "string_typed_true", describe: "lock value encoded as JSON string \"true\" not boolean",
                    apply: |e| set_ptr(e, "/claim_locks/no_ranking_authority", json!("true")) },
                Encoding { id: "int_typed_true", describe: "lock value encoded as JSON number 1",
                    apply: |e| set_ptr(e, "/claim_locks/no_ranking_authority", json!(1)) },
                Encoding { id: "nested_wrapper", describe: "lock value wrapped as {granted:true} object instead of a bare boolean",
                    apply: |e| set_ptr(e, "/claim_locks/no_ranking_authority", json!({"granted": true})) },
            ],
        },
        Case {
            id: "C6_objective_values_claimed",
            field: "/objective_values",
            refutation_criterion:
                "site_b_feasible becomes true while the card supplies a \
                 non-empty objective_values map under any key/type encoding",
            encodings: vec![
                Encoding { id: "numeric_direct", describe: "direct numeric objective {score:0.9}",
                    apply: |e| set_ptr(e, "/objective_values", json!({"score": 0.9})) },
                Encoding { id: "string_valued", describe: "string-valued objective {score:\"0.9\"}",
                    apply: |e| set_ptr(e, "/objective_values", json!({"score": "0.9"})) },
                Encoding { id: "null_valued_key_present", describe: "null-valued but key present {score:null}",
                    apply: |e| set_ptr(e, "/objective_values", json!({"score": null})) },
                Encoding { id: "wrong_key_name_sibling", describe: "value smuggled under sibling key \"objectives\" (wrong name) while objective_values itself is left empty -- tests whether ANY reader is fooled by the near-miss key",
                    apply: |e| { let mut e = e; e["objectives"] = json!({"score": 0.9}); e } },
            ],
        },
    ];

    let mut total = 0usize;
    let mut escalations_slipped_through = Vec::new();

    for case in &cases {
        for encoding in &case.encodings {
            total += 1;
            let mutated = (encoding.apply)(baseline_envelope());
            let feasible_b = site_b_feasible(&mutated);
            let (verdict_a, reason_a) = site_a_verdict(&mutated);
            let blocked = !feasible_b && verdict_a != "ACCEPT";
            if feasible_b || verdict_a == "ACCEPT" {
                escalations_slipped_through.push(json!({
                    "case_id": case.id,
                    "encoding_id": encoding.id,
                    "site_b_feasible": feasible_b,
                    "site_a_verdict": verdict_a.clone(),
                }));
            }
            writeln!(
                out,
                "{}",
                serde_json::to_string(&json!({
                    "record": "CASE",
                    "case_id": case.id,
                    "field_pointer": case.field,
                    "encoding_id": encoding.id,
                    "encoding_description": encoding.describe,
                    "refutation_criterion": case.refutation_criterion,
                    "mutated_envelope": mutated,
                    "site_b_feasible": feasible_b,
                    "site_a_verdict": verdict_a,
                    "site_a_reason": reason_a,
                    "result": if blocked { "BLOCKED" } else { "ESCALATED" },
                }))
                .unwrap()
            );
        }
    }

    // ---- positive control: a deliberately weakened re-implementation -----
    // Planted defect: this "mutant" checker drops the ranking_eligible AND
    // usable_by_optimizer disjuncts from the real authorize_optimizer_request
    // guard (amphora-core/src/lib.rs, the `if envelope.ranking_eligible || ...`
    // clause), keeping only the objective_values/authority_tier/solver_use/
    // claim_lock checks. It is NOT part of amphora-core; it exists solely to
    // prove this probe's checking methodology is capable of detecting the
    // defect it exists to catch. Run against C1's canonical bool-true
    // encoding (real ranking_eligible=true).
    fn mutant_naive_check(envelope: &Value) -> &'static str {
        let objective_values_empty = envelope["objective_values"]
            .as_object()
            .map(|m| m.is_empty())
            .unwrap_or(false);
        let tier = envelope["authority_tier"].as_str().unwrap_or("");
        let forbidden_tier = matches!(tier, "RANKING" | "OPTIMIZER" | "PRODUCTION");
        let solver = envelope["metrics"]["solver_use"].as_str().unwrap_or("");
        let solver_ok = matches!(solver, "DISABLED" | "AUDIT_ONLY" | "CONSTRAINT_ONLY");
        let locks_ok = LOCKS.iter().all(|lock| {
            envelope["claim_locks"]
                .get(lock)
                .and_then(Value::as_bool)
                == Some(true)
        });
        // DEFECT: ranking_eligible / usable_by_optimizer are never consulted.
        if objective_values_empty && !forbidden_tier && solver_ok && locks_ok {
            "ACCEPT"
        } else {
            "REJECT"
        }
    }
    let planted_defect_input = set_ptr(
        baseline_envelope(),
        "/metrics/authority_receipt/ranking_eligible",
        json!(true),
    );
    let real_verdict_b = site_b_feasible(&planted_defect_input);
    let (real_verdict_a, real_reason_a) = site_a_verdict(&planted_defect_input);
    let mutant_verdict = mutant_naive_check(&planted_defect_input);
    let positive_control = json!({
        "record": "POSITIVE_CONTROL",
        "planted_defect": "mutant_naive_check() omits the ranking_eligible / \
            usable_by_optimizer disjuncts that amphora-core's real \
            authorize_optimizer_request (amphora-engine dependency amphora-core \
            src/lib.rs, the `if envelope.ranking_eligible || envelope.usable_by_optimizer \
            || ...` guard) enforces",
        "how_planted": "wrote a second, deliberately weaker checker (mutant_naive_check, \
            defined in this probe file, no shared code with amphora-core) that \
            evaluates objective_values/authority_tier/solver_use/claim_locks but \
            never reads ranking_eligible or usable_by_optimizer, then ran it on \
            the SAME input used for case C1's bool_direct encoding \
            (/metrics/authority_receipt/ranking_eligible mutated true, everything \
            else left at the compliant baseline)",
        "input": planted_defect_input,
        "real_amphora_core_site_b_feasible": real_verdict_b,
        "real_amphora_core_site_a_verdict": real_verdict_a,
        "real_amphora_core_site_a_reason": real_reason_a,
        "mutant_naive_check_verdict": mutant_verdict,
        "detected": real_verdict_b == false && real_verdict_a != "ACCEPT" && mutant_verdict == "ACCEPT",
        "evidence": "on the identical escalated input, the mutant (planted-defect) \
            checker returns ACCEPT while the real amphora_core::rank_candidates / \
            authorize_optimizer_request returns feasible=false / REJECT -- proving \
            this harness's check is capable of firing on a ranking_eligible \
            escalation when the guard that catches it is actually absent, i.e. the \
            absence of an ESCALATED result above is not an artifact of a harness \
            that can never detect anything",
    });
    writeln!(out, "{}", serde_json::to_string(&positive_control).unwrap()).unwrap();

    writeln!(
        out,
        "{}",
        serde_json::to_string(&json!({
            "record": "SUMMARY",
            "total_case_encoding_combinations": total,
            "cases": cases.len(),
            "min_encodings_per_case": cases.iter().map(|c| c.encodings.len()).min(),
            "escalations_slipped_through": escalations_slipped_through,
            "all_blocked": escalations_slipped_through.is_empty(),
        }))
        .unwrap()
    );

    out.flush().unwrap();
}
