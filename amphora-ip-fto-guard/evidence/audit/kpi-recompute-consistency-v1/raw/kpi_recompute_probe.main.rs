//! IP-FTO-GUARD KPI-recompute-consistency probe.
//!
//! Independently re-invokes the REAL compiled runtime
//! (AssuranceCapability::new("amphora-ip-fto-guard") + Capability::evaluate,
//! the same code path R-B01's own reattack harness used) across several
//! distinct candidate shapes, and records metrics.unresolved_technical_categories
//! as actually emitted. This is compared out-of-band (see run_kpi_recompute_consistency.py)
//! against the two independent STATIC reconstructions of that same metric name
//! computed directly from the pinned fixture: (a) count of claim_chart_categories
//! entries with not_fto==true [what the live runtime actually uses], and
//! (b) count of families rows with reads_on_ours == "UNCLEAR / not FTO"
//! [what landscape-integrity-v1 / all-elements-rule-v1 / cpc-coverage-v1 assert
//! as "unresolved_technical_categories_recomputed"].

use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot};
use serde_json::{json, Value};

fn candidates() -> Vec<(&'static str, Value)> {
    vec![
        (
            "baseline-envelope65-like",
            json!({
                "candidate_id": "kpi-probe-baseline",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba_828": 100.0}, "part_B": {"ancamide_350a": 37.13}}
            }),
        ),
        (
            "counsel-signed-true",
            json!({
                "candidate_id": "kpi-probe-counsel-true",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba_828": 100.0}, "part_B": {"ancamide_350a": 37.13}},
                "evidence_refs": {"counsel_fto": {"signed_by_counsel": true}}
            }),
        ),
        (
            "counsel-signed-false",
            json!({
                "candidate_id": "kpi-probe-counsel-false",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba_828": 100.0}, "part_B": {"ancamide_350a": 37.13}},
                "evidence_refs": {"counsel_fto": {"signed_by_counsel": false}}
            }),
        ),
        (
            "unrelated-evidence-refs",
            json!({
                "candidate_id": "kpi-probe-unrelated",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba_828": 100.0}, "part_B": {"ancamide_350a": 37.13}},
                "evidence_refs": {"msds": {"sha256": "deadbeef"}}
            }),
        ),
    ]
}

fn main() {
    let cap = AssuranceCapability::new("amphora-ip-fto-guard").expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = ExecutionContext {
        run_id: "kpi-recompute-consistency-probe".into(),
        deterministic_seed: 20260816,
        lineage: Value::Null,
    };
    let mut records = Vec::new();
    for (scenario_id, candidate) in candidates() {
        let envelope = CandidateEnvelope::from_value(candidate).expect("candidate parses");
        let out = cap.evaluate(&envelope, &features, &ctx).expect("evaluate ok");
        let out = serde_json::to_value(&out).expect("serializes");
        records.push(json!({
            "scenario_id": scenario_id,
            "metrics": out.get("metrics"),
            "gates": out.get("gates"),
        }));
    }
    let output = json!({"records": records});
    println!("{}", serde_json::to_string_pretty(&output).expect("prints"));
}
