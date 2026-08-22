//! W-ASSUR1 re-attack + positive-control probe for
//! `amphora-assurance-capabilities`'s counsel-assertion detection.
//!
//! Runs the ORIGINAL 8 audit probes (A1..A8) plus V-B01's 5 novel probes
//! (V1..V5) plus the two controls through the real compiled
//! AssuranceCapability::evaluate code path (not a re-implementation). This
//! exact same binary source is built twice against two different path
//! dependencies:
//!   - against the REPAIRED in-tree crate (the real fix)
//!   - against a byte-verified copy of the PRE-fix crate (sha256
//!     f7df7055e0488289fdf2976a8a6a5f80d24eb07eab550a595dba6fa945cbe827,
//!     the exact defect V-B01 found), used ONLY as a positive control to
//!     prove this probe harness can detect a real defect of the kind it
//!     exists to catch.

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
                "candidate_id": "wassur1-control",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"counsel_fto": {"signed_by_counsel": true}}
            }),
        ),
        (
            "control-clean-negative",
            json!({
                "candidate_id": "wassur1-clean",
                "candidate_type": "formulation",
                "formulation": formulation(),
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
        (
            "V1-uncovered-homoglyph-deletion-signedbycounsel",
            json!({
                "candidate_id": "wassur1-v1",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"signed_by_co\u{FC}nsel": true}
            }),
        ),
        (
            "V2-uncovered-homoglyph-deletion-counselfto",
            json!({
                "candidate_id": "wassur1-v2",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"co\u{FC}nsel_fto": {"cleared": true}}
            }),
        ),
        (
            "V3-zero-width-joiner-in-key",
            json!({
                "candidate_id": "wassur1-v3",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"sign\u{200D}ed_by_coun\u{200D}sel": true}
            }),
        ),
        (
            "V4-deeply-nested-array-of-objects-alias",
            json!({
                "candidate_id": "wassur1-v4",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {
                    "documents": [
                        {"kind": "unrelated", "notes": "no assertion here"},
                        {"bundle": [
                            {"meta": {"irrelevant": true}},
                            {"legal_review": {"counsel_signoff": {"granted_by": "outside firm"}}}
                        ]}
                    ]
                }
            }),
        ),
        (
            "V5-fullwidth-unicode-escape-key",
            json!({
                "candidate_id": "wassur1-v5",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "signed_by_co\u{FF55}nsel": true
            }),
        ),
    ]
}

fn main() {
    let cap = AssuranceCapability::new("amphora-ip-fto-guard").expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = ExecutionContext {
        run_id: "wassur1-reattack".into(),
        deterministic_seed: 20260805,
        lineage: Value::Null,
    };
    let mut records = Vec::new();
    for (scenario_id, candidate) in scenarios() {
        let envelope = CandidateEnvelope::from_value(candidate).expect("candidate parses");
        let out = cap.evaluate(&envelope, &features, &ctx).expect("evaluate ok");
        let out = serde_json::to_value(&out).expect("serializes");
        let ignored = out
            .get("metrics")
            .and_then(|m| m.get("boolean_counsel_assertion_ignored"))
            .cloned()
            .unwrap_or(Value::Null);
        let is_novel = scenario_id.starts_with('V');
        let is_control_negative = scenario_id == "control-clean-negative";
        let expect_detected = !is_control_negative;
        let detected = ignored == json!(true);
        let slipped_through_undetected = expect_detected && !detected;
        records.push(json!({
            "scenario_id": scenario_id,
            "is_novel_probe": is_novel,
            "metrics": out.get("metrics"),
            "gates": out.get("gates"),
            "status": out.get("status"),
            "boolean_counsel_assertion_ignored": ignored,
            "slipped_through_undetected": slipped_through_undetected,
        }));
    }
    let output = json!({"records": records});
    println!("{}", serde_json::to_string_pretty(&output).expect("prints"));
}
