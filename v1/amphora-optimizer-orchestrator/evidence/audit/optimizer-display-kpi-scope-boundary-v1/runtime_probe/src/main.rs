//! LIVE Rust differential probe for the amphora-optimizer-orchestrator
//! DISPLAY-KPI SCOPE BOUNDARY.
//!
//! The module's declared universe of scope is `OPTIMIZER_MODULES`, the 29
//! registered modules baked into `quarantined_optimizer_policy()`. Every
//! entry into ranking authority is required to pass through
//! `authorize_optimizer_request` (site A), which rejects (a) any envelope
//! whose `module_id` is outside the 29 registered modules, (b) any envelope
//! that carries non-empty `objective_values` at all (Phase-0 is
//! zero-authority: no scored objective data is admissible under any
//! registration), and (c) any envelope not `status == "SCORED"` when it is
//! named by a hard constraint.
//!
//! This probe asks: does the SECOND live output path that also reads
//! per-candidate score envelopes -- `rank_candidates`'s `display_kpis`
//! surface (site B) -- enforce that same registered-module / SCORED-status
//! boundary? It links the real runtime as a library and calls both real
//! public entry points on the same synthetic envelopes. No re-implementation
//! of either resolver; site B's resolved value is reported verbatim.
//!
//! Two hostile cases, each with a unique marker value baked into
//! `objective_values`:
//!   1. UNREGISTERED module: module_id is not one of the 29 in
//!      `OPTIMIZER_MODULES` at all -- entirely outside the policy's declared
//!      scope.
//!   2. NON-SCORED registered module: module_id IS one of the 29, but
//!      status == "FAILED_GATES", not "SCORED".
//!
//! For each case: site A (authorize_optimizer_request) is called on the
//! literal envelope and is expected to return Err (it always does for any
//! envelope with non-empty objective_values, by construction). Site B
//! (rank_candidates) is called on a result document carrying the same
//! envelope, with a display_kpis profile entry naming exactly that
//! module_id/objective_values path, and the resulting display_kpis value is
//! reported. If the marker value is present in site B's output, the leak is
//! observed live, not asserted.
//!
//! Deterministic: no randomness, no clock, no filesystem writes, no network.

use amphora_core::{
    authorize_optimizer_request, quarantined_optimizer_policy, rank_candidates, KpiProfile,
    OptimizerAuthorizationRequestV1, OptimizerEnvelopeV1,
};
use serde_json::{json, Value};
use std::io::{self, Write};

const REGISTERED_MODULE: &str = "amphora-molecule-property";
const UNREGISTERED_MODULE: &str = "amphora-not-a-registered-module-zz";

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

/// Envelope in the raw score_envelopes shape rank_candidates (site B) reads.
fn raw_envelope(module_id: &str, status: &str, marker: &str) -> Value {
    json!({
        "module_id": module_id,
        "status": status,
        "authority_tier": "REAL_ARITHMETIC",
        "metrics": {
            "solver_use": "AUDIT_ONLY",
            "authority_receipt": {"ranking_eligible": false},
        },
        "usable_by_optimizer": false,
        "objective_values": {"secret_metric": marker},
        "gates": {},
        "claim_locks": locks(),
    })
}

/// The same envelope in the OptimizerEnvelopeV1 shape site A (the reference
/// monitor) consumes directly.
fn site_a_envelope(module_id: &str, status: &str, marker: &str) -> OptimizerEnvelopeV1 {
    serde_json::from_value(json!({
        "module_id": module_id,
        "status": status,
        "authority_tier": "REAL_ARITHMETIC",
        "solver_use_ceiling": "AUDIT_ONLY",
        "ranking_eligible": false,
        "usable_by_optimizer": false,
        "objective_values": {"secret_metric": marker},
        "gates": {},
        "claim_locks": locks(),
    }))
    .expect("site A envelope")
}

fn policy_request() -> OptimizerAuthorizationRequestV1 {
    serde_json::from_value(json!({
        "schema": "amphora.optimizer-authorization-request.v1",
        "request_source": "POLICY",
        "objectives": [],
        "hard_constraints": [],
    }))
    .expect("policy request")
}

fn display_profile(module_id: &str) -> KpiProfile {
    serde_json::from_value(json!({
        "schema": "amphora.dashboard-kpi-profile.v1",
        "profile_id": "display-scope-boundary-probe",
        "objectives": [],
        "hard_constraints": [],
        "display_kpis": [{
            "id": "d1",
            "module_id": module_id,
            "section": "objective_values",
            "path": "secret_metric",
            "label": "probe",
            "unit": "probe",
            "direction": "context",
        }],
    }))
    .expect("display profile")
}

fn run_case(name: &str, module_id: &str, status: &str, marker: &str) -> Value {
    // Site A: the reference monitor, called directly on the envelope.
    let envelope = site_a_envelope(module_id, status, marker);
    let site_a_result = authorize_optimizer_request(
        &policy_request(),
        std::slice::from_ref(&envelope),
        &quarantined_optimizer_policy(),
    );
    let site_a_rejected = site_a_result.is_err();
    let site_a_err = site_a_result.err().unwrap_or_default();

    // Site B: rank_candidates, called on a result document carrying the raw
    // envelope, with a display_kpis definition naming the same module/path.
    let result_doc = json!({
        "candidate": {"candidate_id": "c-probe"},
        "score_envelopes": [raw_envelope(module_id, status, marker)],
    });
    let profile = display_profile(module_id);
    let ranked = rank_candidates(std::slice::from_ref(&result_doc), &profile);
    let candidate = &ranked[0];
    let site_b_value = candidate
        .display_kpis
        .first()
        .map(|kpi| kpi.value.clone());
    let site_b_leaked = site_b_value.as_ref().and_then(Value::as_str) == Some(marker);

    json!({
        "case": name,
        "module_id": module_id,
        "envelope_status": status,
        "module_is_registered": module_id != UNREGISTERED_MODULE,
        "marker": marker,
        "site_a_authorize_optimizer_request_rejected": site_a_rejected,
        "site_a_error": site_a_err,
        "site_b_rank_candidates_display_kpis_value": site_b_value,
        "site_b_leaked_marker_verbatim": site_b_leaked,
        "site_b_ranking_performed": candidate.ranked,
        "site_b_eligible_objectives": candidate.eligible_objectives,
        "site_b_feasible": candidate.feasible,
        "divergence_A_rejects_B_discloses": site_a_rejected && site_b_leaked,
    })
}

fn main() {
    let case1 = run_case(
        "unregistered_module_scored",
        UNREGISTERED_MODULE,
        "SCORED",
        "UNREGISTERED_LEAK_9f3a1c",
    );
    let case2 = run_case(
        "registered_module_failed_gates",
        REGISTERED_MODULE,
        "FAILED_GATES",
        "FAILEDGATES_LEAK_7c1d44",
    );
    let both_diverge = case1["divergence_A_rejects_B_discloses"] == json!(true)
        && case2["divergence_A_rejects_B_discloses"] == json!(true);
    let out = json!({
        "probe": "optimizer-display-kpi-scope-boundary-v1",
        "registered_modules_count": 29,
        "cases": [case1, case2],
        "both_cases_diverge": both_diverge,
    });
    io::stdout()
        .write_all(serde_json::to_string_pretty(&out).unwrap().as_bytes())
        .unwrap();
    println!();
}
