//! Repair R-B01 re-attack harness: re-runs the counsel-assertion
//! detection-completeness probe table from the refuting AUDIT_ONLY receipt
//! amphora-ip-fto-guard/evidence/audit/counsel-assertion-detection-completeness-v1
//! against the REPAIRED compiled runtime (real
//! AssuranceCapability::new + Capability::evaluate code path, not a
//! re-implementation). Probe candidates reconstructed from the signed audit
//! receipt's scenario ids and encoding-class descriptions (original
//! /tmp/ip_fto_probe harness is no longer on disk).

use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot};
use serde_json::{json, Value};

fn formulation() -> Value {
    json!({"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}})
}

fn scenarios() -> Vec<(&'static str, Value)> {
    vec![
        (
            "control-exact-path-true",
            json!({
                "candidate_id": "probe-control",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"counsel_fto": {"signed_by_counsel": true}}
            }),
        ),
        (
            "A1-top-level-key",
            json!({
                "candidate_id": "probe-a1",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "signed_by_counsel": true
            }),
        ),
        (
            "A2-counsel-fto-array",
            json!({
                "candidate_id": "probe-a2",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"counsel_fto": [{"signed_by_counsel": true}]}
            }),
        ),
        (
            "A3-nested-one-level-deeper",
            json!({
                "candidate_id": "probe-a3",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"legal": {"counsel_fto": {"signed_by_counsel": true}}}
            }),
        ),
        (
            "A4-case-variant-key",
            json!({
                "candidate_id": "probe-a4",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"Counsel_FTO": {"Signed_By_Counsel": true}}
            }),
        ),
        (
            "A5-alternate-path-name",
            json!({
                "candidate_id": "probe-a5",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"counsel_signoff": {"granted": true}}
            }),
        ),
        (
            "A6-semantic-alt-claim-key",
            json!({
                "candidate_id": "probe-a6",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"fto_cleared_by_counsel": true}
            }),
        ),
        (
            "A7-counsel-fto-string",
            json!({
                "candidate_id": "probe-a7",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"counsel_fto": "signed off by outside counsel 2026-07-01"}
            }),
        ),
        (
            "A8-unicode-confusable-key",
            json!({
                "candidate_id": "probe-a8",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "\u{0455}igned_by_coun\u{0455}el": true
            }),
        ),
    ]
}

fn main() {
    let cap = AssuranceCapability::new("amphora-ip-fto-guard").expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = ExecutionContext {
        run_id: "repair-r-b01-reattack".into(),
        deterministic_seed: 20260803,
        lineage: Value::Null,
    };
    let mut records = Vec::new();
    for (scenario_id, candidate) in scenarios() {
        let envelope = CandidateEnvelope::from_value(candidate).expect("candidate parses");
        let out = cap.evaluate(&envelope, &features, &ctx).expect("evaluate ok");
        let out = serde_json::to_value(&out).expect("serializes");
        records.push(json!({
            "scenario_id": scenario_id,
            "metrics": out.get("metrics"),
            "gates": out.get("gates"),
            "status": out.get("status"),
        }));
    }
    let output = json!({"records": records});
    println!("{}", serde_json::to_string_pretty(&output).expect("prints"));
}
