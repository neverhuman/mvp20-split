//! V-B01: independent adversarial verification of repair R-B01's
//! counsel-assertion detection (amphora-assurance-capabilities). Runs 4 NOVEL
//! encodings NOT among the original 8 audit probes (A1..A8) through the real
//! AssuranceCapability::evaluate code path (real compiled Rust runtime, not a
//! re-implementation). Also emits the control + primary-KPI check.

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
                "candidate_id": "vb01-control",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"counsel_fto": {"signed_by_counsel": true}}
            }),
        ),
        (
            "control-clean-negative",
            json!({
                "candidate_id": "vb01-clean",
                "candidate_type": "formulation",
                "formulation": formulation(),
            }),
        ),
        // V1: uncovered-homoglyph LETTER-DELETION. U+00FC (u with diaeresis,
        // "u") is NOT NFKC-decomposed to ASCII 'u' (it's a precomposed
        // canonical character, not a compatibility form) and is NOT in
        // fold_confusable's coverage list, so normalized_key_skeleton's
        // is_ascii_alphanumeric filter silently DELETES it rather than
        // substituting 'u'. "signed_by_co\u{FC}nsel" -> skeleton
        // "signedbyconsel": not the canonical name, does not contain
        // "counsel" (missing the u), so counsel_party=0; only sign_off=1.
        // Sum=1 < 2 -> predicted UNDETECTED.
        (
            "V1-uncovered-homoglyph-deletion-signedbycounsel",
            json!({
                "candidate_id": "vb01-v1",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"signed_by_co\u{FC}nsel": true}
            }),
        ),
        // V2: same deletion class applied to the OTHER canonical key,
        // "counsel_fto" -> "co\u{EB}nsel_fto" (e with diaeresis in place of
        // the 2nd 'e'... use u-diaeresis again on 'u' of "counsel" for
        // consistency across the word, keeping "fto" intact so this also
        // probes whether the >=2-of-3 rule saves it via fto+sign tokens
        // alone (it should not, since sign_off token is absent here).
        (
            "V2-uncovered-homoglyph-deletion-counselfto",
            json!({
                "candidate_id": "vb01-v2",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"co\u{FC}nsel_fto": {"cleared": true}}
            }),
        ),
        // V3: zero-width joiner INSIDE the key (explicitly named in the
        // objective). ZWJ (U+200D) is non-alphanumeric so it is simply
        // filtered out by normalized_key_skeleton regardless of the
        // confusable fold, leaving "signedbycounsel" intact -> predicted
        // DETECTED (confirms the filter step, not a break).
        (
            "V3-zero-width-joiner-in-key",
            json!({
                "candidate_id": "vb01-v3",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"sign\u{200D}ed_by_coun\u{200D}sel": true}
            }),
        ),
        // V4: nested array-of-objects alias, several levels deep, using the
        // semantic-alt key "counsel_signoff" (not one of the two exact
        // canonical names) buried inside an array of unrelated sibling
        // objects. Predicted DETECTED (recursion has no depth/shape gap).
        (
            "V4-deeply-nested-array-of-objects-alias",
            json!({
                "candidate_id": "vb01-v4",
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
        // V5: key expressed via a JSON \u unicode-escape sequence for the
        // FULLWIDTH form of a letter (U+FF55 FULLWIDTH LATIN SMALL LETTER U
        // in place of ASCII 'u'). Fullwidth forms DO have an NFKC
        // compatibility decomposition to their ASCII counterpart, so this
        // should normalize correctly -> predicted DETECTED (confirms NFKC
        // fullwidth handling, distinct mechanism from V1/V2's non-decomposing
        // diaeresis deletion).
        (
            "V5-fullwidth-unicode-escape-key",
            json!({
                "candidate_id": "vb01-v5",
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
        run_id: "vb01-verify-reattack".into(),
        deterministic_seed: 20260804,
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
