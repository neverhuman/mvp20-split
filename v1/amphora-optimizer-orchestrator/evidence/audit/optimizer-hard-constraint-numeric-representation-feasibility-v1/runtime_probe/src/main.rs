//! LIVE Rust probe for amphora-optimizer-orchestrator's HARD-CONSTRAINT
//! NUMERIC-REPRESENTATION FEASIBILITY defect, escalated to the actual
//! `RankedCandidate.feasible` field that `rank_candidates`'s own sort
//! consumes.
//!
//! Prior study `optimizer-authorization-numeric-comparison-conformance-v1`
//! (2026-08-1x) characterized `amphora_core::comparison_passes`'s `==`/`!=`
//! arms against a locked literal corpus and found finding F2
//! (`rfc8259_value_equality_representation_invariance`) REFUTED: serde_json
//! `Value` equality is representation-sensitive (JSON `110` and `110.0` are
//! NOT `==` as `Value`s even though they denote the same real number), with
//! 48 equality divergences vs exact RFC 8259 value semantics. That study's
//! own `does_not_close` explicitly scoped itself to `authorize_optimizer_request`
//! called in isolation, stating the quarantine invariant "holds on all
//! accepts" only because `hard_constraints_passed`/`ranking_performed`/etc.
//! are hardcoded on `Ok`, and never exercised the ONE non-hardcoded field
//! `rank_candidates`'s own sort comparator actually reads: `feasible`.
//!
//! This probe closes that gap. It links the real amphora-core crate and
//! calls the real public `rank_candidates(&docs, &profile)` -- no
//! reimplementation of `comparison_passes`, `authorize_optimizer_request`,
//! `optimizer_envelopes`, or the sort comparator -- over a KpiProfile that
//! declares one numeric hard_constraint (operator `!=`, expected `110.0`,
//! a JSON float literal) against three candidates whose SCORED envelope
//! carries the gate value in different JSON literal forms:
//!
//!   D ("ddd-int-repr-defect"):    gates.flagged_batch_code = 110   (int)
//!   E ("eee-float-repr-control"): gates.flagged_batch_code = 110.0 (float, matches expected's literal form)
//!   F ("fff-true-pass-control"):  gates.flagged_batch_code = 200   (int, genuinely different value)
//!
//! D and E denote the IDENTICAL real number (110). A correct `!=110.0`
//! hard constraint must treat them identically: since actual == expected
//! mathematically, `!=` must evaluate false and BOTH should be denied
//! (feasible=false). F is a genuinely different value and must be admitted
//! (feasible=true).
//!
//! Deterministic: no randomness, no clock, no network, no filesystem reads
//! (the corpus is inline so the two-replay gate is trivially byte-stable).

use amphora_core::{rank_candidates, HardConstraint, KpiProfile};
use serde_json::{json, Value};

fn locks() -> Value {
    let names = [
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
    let mut map = serde_json::Map::new();
    for name in names {
        map.insert(name.to_string(), json!(true));
    }
    Value::Object(map)
}

/// A zero-authority score envelope in the raw score_envelopes shape that
/// both `authorize_optimizer_request` (via `optimizer_envelopes`) and
/// `rank_candidates` read.
fn envelope(module_id: &str, gate_value_literal: Value) -> Value {
    json!({
        "module_id": module_id,
        "status": "SCORED",
        "authority_tier": "REAL_ARITHMETIC",
        "metrics": {
            "solver_use": "AUDIT_ONLY",
            "authority_receipt": {"ranking_eligible": false},
        },
        "usable_by_optimizer": false,
        "objective_values": {},
        "gates": {"flagged_batch_code": gate_value_literal},
        "claim_locks": locks(),
    })
}

fn candidate_doc(candidate_id: &str, gate_value_literal: Value) -> Value {
    json!({
        "candidate": {"candidate_id": candidate_id},
        "score_envelopes": [envelope("amphora-molecule-property", gate_value_literal)],
    })
}

fn main() {
    // Synthetic-but-schema-valid KpiProfile: one numeric hard_constraint,
    // operator `!=`, expected value entered as the JSON FLOAT literal
    // `110.0`. This is a documented capability of HardConstraint.operator
    // (one of the six allowed operators) and HardConstraint.expected
    // (arbitrary serde_json::Value) -- not a malformed or out-of-contract
    // request.
    let profile_doc = json!({
        "schema": "amphora.dashboard-kpi-profile.v1",
        "profile_id": "numeric-representation-feasibility-probe-v1",
        "objectives": [],
        "hard_constraints": [
            {
                "id": "not_flagged_batch_code",
                "module_id": "amphora-molecule-property",
                "section": "gates",
                "path": "flagged_batch_code",
                "label": "Excludes recalled/flagged batch code 110",
                "operator": "!=",
                "expected": 110.0
            }
        ],
        "display_kpis": []
    });
    let profile: KpiProfile =
        serde_json::from_value(profile_doc).expect("profile deserializes as KpiProfile");
    let expected_literal_is_float = matches!(
        profile.hard_constraints.first(),
        Some(HardConstraint { expected, .. }) if expected.is_f64() && !expected.is_i64()
    );

    let doc_d = candidate_doc("ddd-int-repr-defect", json!(110));
    let doc_e = candidate_doc("eee-float-repr-control", json!(110.0));
    let doc_f = candidate_doc("fff-true-pass-control", json!(200));

    let ranked = rank_candidates(&[doc_d, doc_e, doc_f], &profile);
    let by_id = |id: &str| ranked.iter().find(|c| c.candidate_id == id).unwrap();
    let d = by_id("ddd-int-repr-defect");
    let e = by_id("eee-float-repr-control");
    let f = by_id("fff-true-pass-control");

    let final_order: Vec<Value> = ranked
        .iter()
        .map(|cand| {
            json!({
                "candidate_id": cand.candidate_id,
                "feasible": cand.feasible,
                "ranked": cand.ranked,
                "failed_modules": cand.failed_modules,
            })
        })
        .collect();

    // D and E denote the identical real number (110). A representation-
    // invariant `!=110.0` constraint must treat them identically: both
    // must be denied (feasible=false), since 110 == 110.0 mathematically.
    let d_and_e_should_be_identical_and_denied = !d.feasible && !e.feasible;
    // Observed: does representation alone flip the outcome for the SAME
    // real-number gate value?
    let representation_flips_feasible = d.feasible != e.feasible;
    // Positive control: a genuinely different value (200) must be admitted.
    let true_pass_control_works = f.feasible;
    // Which side is exploitable: does the int-literal candidate (D) get
    // WRONGLY ADMITTED (feasible=true) despite denoting the excluded value?
    let defect_wrongly_admits_excluded_value = d.feasible && !e.feasible;

    let divergence_observed = representation_flips_feasible
        && defect_wrongly_admits_excluded_value
        && true_pass_control_works
        && expected_literal_is_float;

    let out = json!({
        "probe": "optimizer-hard-constraint-numeric-representation-feasibility-v1",
        "profile_id": profile.profile_id,
        "hard_constraint": {
            "operator": "!=",
            "expected_literal": "110.0",
            "expected_literal_is_float": expected_literal_is_float,
            "module_id": "amphora-molecule-property",
            "path": "flagged_batch_code"
        },
        "candidates": {
            "D_int_repr_defect": {"gate_literal": "110", "feasible": d.feasible, "failed_modules": d.failed_modules},
            "E_float_repr_control": {"gate_literal": "110.0", "feasible": e.feasible, "failed_modules": e.failed_modules},
            "F_true_pass_control": {"gate_literal": "200", "feasible": f.feasible, "failed_modules": f.failed_modules},
        },
        "final_sorted_order": final_order,
        "d_and_e_should_be_identical_and_denied_under_rfc8259_value_semantics": d_and_e_should_be_identical_and_denied,
        "representation_flips_feasible_for_identical_real_number": representation_flips_feasible,
        "defect_wrongly_admits_excluded_value_as_feasible": defect_wrongly_admits_excluded_value,
        "true_pass_control_works": true_pass_control_works,
        "divergence_observed": divergence_observed,
    });
    print!("{}", serde_json::to_string_pretty(&out).unwrap());
    println!();
}
