//! LIVE Rust probe for amphora-optimizer-orchestrator's RANKING-BOUNDARY
//! FEASIBILITY SCOPE.
//!
//! `RankedCandidate.feasible` is the only field `rank_candidates`'s own
//! `candidates.sort_by` comparator uses beyond the (always-false) `ranked`
//! flag: `right.ranked.cmp(&left.ranked).then_with(|| right.feasible.cmp(&left.feasible))...`.
//! An operator reading the module's own mission.md ("the emitted envelope,
//! adapter, manifest, model receipt/card, portfolio policy, and Rust
//! ranking boundary must all agree. The most restrictive policy controls.")
//! reasonably expects `feasible` to reflect whether a candidate's score
//! envelopes actually passed scoring.
//!
//! `authorize_optimizer_request`'s per-envelope `status != "SCORED"` check
//! (amphora-core/src/lib.rs, inside the `hard_constraints` loop) only fires
//! for a module named by a declared `HardConstraint`. It never inspects the
//! `status` of any OTHER envelope in the batch, including ones the SAME
//! shipped profile displays to the user via `display_kpis`.
//!
//! This probe links the real amphora-core crate and reads the REAL shipped
//! profile at config/kpis/molecule-demo.json verbatim (sha256 recorded, not
//! copied/retyped) to ask a concrete, non-hypothetical question: for THIS
//! shipped profile -- whose one declared hard_constraint names only
//! amphora-molecule-design-gate while display_kpis also names
//! amphora-molecule-property and amphora-molecule-novelty -- does a
//! candidate whose amphora-molecule-property envelope carries
//! status="FAILED_GATES" (a real, already-computed gate failure) still
//! receive feasible=true and rank ahead of a candidate whose declared
//! hard-constraint module genuinely failed?
//!
//! Three synthetic candidates, real rank_candidates() call, real sort:
//!   A ("zzz-genuine-pass-A"):     design-gate PASSES, property SCORED, novelty SCORED.
//!   B ("mmm-genuine-fail-declared-B"): design-gate FAILS (the one declared constraint), property SCORED, novelty SCORED.
//!   C ("aaa-hidden-fail-undeclared-C"): design-gate PASSES, property FAILED_GATES (undeclared), novelty SCORED.
//!
//! Deterministic: no randomness, no clock, no network. Reads exactly one
//! file from disk (the shipped profile) whose sha256 is recorded so the
//! read is auditable, not asserted.

use amphora_core::{rank_candidates, KpiProfile};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::io::{self, Write};
use std::path::PathBuf;

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

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
/// both authorize_optimizer_request (via optimizer_envelopes) and
/// rank_candidates's display_kpis resolver read.
fn envelope(module_id: &str, status: &str, gates: Value, metrics_extra: Value) -> Value {
    let mut metrics = json!({
        "solver_use": "AUDIT_ONLY",
        "authority_receipt": {"ranking_eligible": false},
    });
    if let (Some(base), Some(extra)) = (metrics.as_object_mut(), metrics_extra.as_object()) {
        for (k, v) in extra {
            base.insert(k.clone(), v.clone());
        }
    }
    json!({
        "module_id": module_id,
        "status": status,
        "authority_tier": "REAL_ARITHMETIC",
        "metrics": metrics,
        "usable_by_optimizer": false,
        "objective_values": {},
        "gates": gates,
        "claim_locks": locks(),
    })
}

fn candidate_doc(candidate_id: &str, design_gate_pass: bool, property_status: &str) -> Value {
    let design_gate = envelope(
        "amphora-molecule-design-gate",
        "SCORED",
        json!({"pass_all_hard": design_gate_pass}),
        json!({"gate_reasons": []}),
    );
    let property = envelope(
        "amphora-molecule-property",
        property_status,
        json!({}),
        json!({}),
    );
    let novelty = envelope(
        "amphora-molecule-novelty",
        "SCORED",
        json!({}),
        json!({"max_similarity": 0.12, "novelty_band": "NOVEL"}),
    );
    json!({
        "candidate": {"candidate_id": candidate_id},
        "score_envelopes": [design_gate, property, novelty],
    })
}

fn main() {
    // Read the REAL shipped profile from disk, verbatim.
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let profile_path = manifest_dir.join("../../../../../config/kpis/molecule-demo.json");
    let profile_bytes = std::fs::read(&profile_path)
        .unwrap_or_else(|error| panic!("failed to read shipped profile {profile_path:?}: {error}"));
    let profile_sha256 = sha256_hex(&profile_bytes);
    let profile: KpiProfile =
        serde_json::from_slice(&profile_bytes).expect("shipped profile deserializes as KpiProfile");
    let hard_constraint_modules: Vec<String> = profile
        .hard_constraints
        .iter()
        .map(|c| c.module_id.clone())
        .collect();
    let display_kpi_modules: Vec<String> = {
        let mut mods: Vec<String> = profile
            .display_kpis
            .iter()
            .map(|d| d.module_id.clone())
            .collect();
        mods.sort();
        mods.dedup();
        mods
    };

    let doc_a = candidate_doc("zzz-genuine-pass-A", true, "SCORED");
    let doc_b = candidate_doc("mmm-genuine-fail-declared-B", false, "SCORED");
    let doc_c = candidate_doc("aaa-hidden-fail-undeclared-C", true, "FAILED_GATES");

    let ranked = rank_candidates(&[doc_a, doc_b, doc_c], &profile);

    let by_id = |id: &str| ranked.iter().find(|c| c.candidate_id == id).unwrap();
    let a = by_id("zzz-genuine-pass-A");
    let b = by_id("mmm-genuine-fail-declared-B");
    let c = by_id("aaa-hidden-fail-undeclared-C");

    let final_order: Vec<Value> = ranked
        .iter()
        .map(|cand| {
            json!({
                "candidate_id": cand.candidate_id,
                "feasible": cand.feasible,
                "ranked": cand.ranked,
                "failed_modules": cand.failed_modules,
                "eligible_objectives": cand.eligible_objectives,
                "current_rank": cand.current_rank,
            })
        })
        .collect();

    let index_of = |id: &str| ranked.iter().position(|cand| cand.candidate_id == id).unwrap();
    let hidden_fail_ranks_at_or_above_declared_fail = index_of("aaa-hidden-fail-undeclared-C")
        < index_of("mmm-genuine-fail-declared-B");
    let hidden_fail_feasible_matches_genuine_pass = c.feasible == a.feasible && c.feasible;
    let hidden_fail_visible_via_failed_modules_only = c.failed_modules > a.failed_modules;
    let declared_mechanism_works = !b.feasible; // positive control: the ONE declared constraint DOES demote when it fails

    let divergence_observed = hidden_fail_ranks_at_or_above_declared_fail
        && hidden_fail_feasible_matches_genuine_pass
        && hidden_fail_visible_via_failed_modules_only
        && declared_mechanism_works;

    let out = json!({
        "probe": "optimizer-ranking-boundary-feasibility-scope-v1",
        "shipped_profile_path": "config/kpis/molecule-demo.json",
        "shipped_profile_sha256": profile_sha256,
        "shipped_profile_id": profile.profile_id,
        "hard_constraint_modules": hard_constraint_modules,
        "display_kpi_modules": display_kpi_modules,
        "display_kpi_modules_not_hard_constrained": display_kpi_modules
            .iter()
            .filter(|m| !hard_constraint_modules.contains(m))
            .cloned()
            .collect::<Vec<_>>(),
        "candidates": {
            "A_genuine_pass": {"feasible": a.feasible, "failed_modules": a.failed_modules, "ranked": a.ranked},
            "B_genuine_fail_declared": {"feasible": b.feasible, "failed_modules": b.failed_modules, "ranked": b.ranked},
            "C_hidden_fail_undeclared": {"feasible": c.feasible, "failed_modules": c.failed_modules, "ranked": c.ranked},
        },
        "final_sorted_order": final_order,
        "declared_mechanism_works_as_positive_control": declared_mechanism_works,
        "hidden_fail_ranks_at_or_above_declared_fail": hidden_fail_ranks_at_or_above_declared_fail,
        "hidden_fail_feasible_matches_genuine_pass": hidden_fail_feasible_matches_genuine_pass,
        "hidden_fail_visible_via_failed_modules_only": hidden_fail_visible_via_failed_modules_only,
        "divergence_observed": divergence_observed,
    });
    io::stdout()
        .write_all(serde_json::to_string_pretty(&out).unwrap().as_bytes())
        .unwrap();
    println!();
}
