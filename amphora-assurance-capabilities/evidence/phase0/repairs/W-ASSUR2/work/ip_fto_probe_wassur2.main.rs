//! W-ASSUR2: attack the repaired (NFKD-based) confusable detector in
//! `amphora-assurance-capabilities::key_asserts_counsel_signoff` beyond the
//! 13 known probes (A1..A8 original + V1..V5 from V-B01/W-ASSUR1), across
//! five confusable families named by the campaign item, PLUS a legitimate-key
//! false-positive control set. Drives the real compiled
//! `AssuranceCapability::evaluate` code path (not a re-implementation).
//!
//! Families:
//!   CG  - Cyrillic/Greek lookalikes NOT in the hand-picked fold_confusable
//!         table (the table only covers a small whitelist; TR39 confusables
//!         go far beyond it).
//!   MA  - Unicode Mathematical Alphanumeric Symbols (bold/italic/
//!         double-struck/fraktur/monospace variants of Latin letters).
//!   FW  - Fullwidth forms.
//!   ZB  - Zero-width joiners/non-joiners and bidi control characters
//!         embedded mid-key.
//!   CM  - Combining marks applied directly to already-ASCII base letters
//!         (not part of any NFKD decomposition).
//!   FP  - Legitimate (non-attack) keys, some with genuine non-ASCII content,
//!         used to measure the false-positive rate of the broad 2-of-3
//!         semantic-token heuristic.

use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot};
use serde_json::{json, Value};

fn formulation() -> Value {
    json!({"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}})
}

fn scenarios() -> Vec<(&'static str, &'static str, Value)> {
    vec![
        // ---- sanity controls (unchanged behavior expected) ----
        (
            "control-clean-negative",
            "control",
            json!({
                "candidate_id": "wassur2-clean",
                "candidate_type": "formulation",
                "formulation": formulation(),
            }),
        ),
        (
            "control-known-good-A8-cyrillic-dze",
            "control",
            json!({
                "candidate_id": "wassur2-a8",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "\u{0455}igned_by_coun\u{0455}el": true
            }),
        ),
        // ================= CG: Cyrillic/Greek lookalikes beyond the table =================
        // Real TR39 confusables NOT in fold_confusable's whitelist:
        //   U+03B7 GREEK SMALL LETTER ETA (eta) -> looks like Latin 'n'
        //   U+0433 CYRILLIC SMALL LETTER GHE (ge) -> looks like Latin 'r'
        //   U+0442 CYRILLIC SMALL LETTER TE (te)  -> looks like Latin 't'
        (
            "CG1-eta-for-n-in-signed",
            "CG",
            json!({
                "candidate_id": "wassur2-cg1",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"counsel_sig\u{03B7}ed_off": true}
            }),
        ),
        (
            "CG2-ghe-for-r-in-cleared-with-fto",
            "CG",
            json!({
                "candidate_id": "wassur2-cg2",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"fto_clea\u{0433}ed": true}
            }),
        ),
        (
            "CG3-ghe-for-r-in-attorney-with-fto",
            "CG",
            json!({
                "candidate_id": "wassur2-cg3",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"atto\u{0433}ney_fto": true}
            }),
        ),
        (
            "CG4-te-for-t-in-attest-with-counsel",
            "CG",
            json!({
                "candidate_id": "wassur2-cg4",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"counsel_a\u{0442}\u{0442}est": true}
            }),
        ),
        // uncorrupted baselines (should be detected) to prove the corruption,
        // not mere presence of "fto"/"counsel", is what causes the CG evasions
        (
            "CG-baseline-fto-cleared-uncorrupted",
            "CG-baseline",
            json!({
                "candidate_id": "wassur2-cg-base1",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"fto_cleared": true}
            }),
        ),
        (
            "CG-baseline-attorney-fto-uncorrupted",
            "CG-baseline",
            json!({
                "candidate_id": "wassur2-cg-base2",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"attorney_fto": true}
            }),
        ),
        // ================= MA: Mathematical Alphanumeric Symbols =================
        (
            "MA1-bold-signed-by-counsel",
            "MA",
            json!({
                "candidate_id": "wassur2-ma1",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "\u{1D42C}\u{1D422}\u{1D420}\u{1D427}\u{1D41E}\u{1D41D}_\u{1D41B}\u{1D432}_\u{1D41C}\u{1D428}\u{1D42E}\u{1D427}\u{1D42C}\u{1D41E}\u{1D425}": true
            }),
        ),
        (
            "MA2-italic-counsel-fto",
            "MA",
            json!({
                "candidate_id": "wassur2-ma2",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"\u{1D450}\u{1D45C}\u{1D462}\u{1D45B}\u{1D460}\u{1D452}\u{1D459}_\u{1D453}\u{1D461}\u{1D45C}": true}
            }),
        ),
        (
            "MA3-double-struck-counsel-fto",
            "MA",
            json!({
                "candidate_id": "wassur2-ma3",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"\u{1D554}\u{1D560}\u{1D566}\u{1D55F}\u{1D564}\u{1D556}\u{1D55D}_\u{1D557}\u{1D565}\u{1D560}": true}
            }),
        ),
        (
            "MA4-monospace-signed-by-counsel",
            "MA",
            json!({
                "candidate_id": "wassur2-ma4",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "\u{1D69C}\u{1D692}\u{1D690}\u{1D697}\u{1D68E}\u{1D68D}_\u{1D68B}\u{1D6A2}_\u{1D68C}\u{1D698}\u{1D69E}\u{1D697}\u{1D69C}\u{1D68E}\u{1D695}": true
            }),
        ),
        // ================= FW: Fullwidth forms =================
        (
            "FW1-fullwidth-signed-by-counsel",
            "FW",
            json!({
                "candidate_id": "wassur2-fw1",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "\u{FF53}\u{FF49}\u{FF47}\u{FF4E}\u{FF45}\u{FF44}\u{FF3F}\u{FF42}\u{FF59}\u{FF3F}\u{FF43}\u{FF4F}\u{FF55}\u{FF4E}\u{FF53}\u{FF45}\u{FF4C}": true
            }),
        ),
        (
            "FW2-fullwidth-counsel-fto-mixedcase",
            "FW",
            json!({
                "candidate_id": "wassur2-fw2",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"\u{FF23}\u{FF4F}\u{FF55}\u{FF4E}\u{FF53}\u{FF45}\u{FF4C}\u{FF3F}\u{FF26}\u{FF34}\u{FF2F}": true}
            }),
        ),
        // ================= ZB: zero-width / bidi controls =================
        (
            "ZB1-zwnj-mid-key",
            "ZB",
            json!({
                "candidate_id": "wassur2-zb1",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"sig\u{200C}ned_by_coun\u{200C}sel": true}
            }),
        ),
        (
            "ZB2-rlo-pdf-wrap",
            "ZB",
            json!({
                "candidate_id": "wassur2-zb2",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"\u{202E}signed_by_counsel\u{202C}": true}
            }),
        ),
        (
            "ZB3-lri-pdi-isolate-split",
            "ZB",
            json!({
                "candidate_id": "wassur2-zb3",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"counsel\u{2066}_fto\u{2069}": true}
            }),
        ),
        // ================= CM: combining marks not part of NFKD decomposition =================
        (
            "CM1-standalone-combining-acute-on-s",
            "CM",
            json!({
                "candidate_id": "wassur2-cm1",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"s\u{0301}igned_by_counsel": true}
            }),
        ),
        (
            "CM2-zalgo-heavy-combining-stack",
            "CM",
            json!({
                "candidate_id": "wassur2-cm2",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "evidence_refs": {"s\u{0316}i\u{0317}g\u{0318}n\u{0319}e\u{0301}d_by_coun\u{0301}sel": true}
            }),
        ),
        // ================= FP: legitimate-key false-positive control set =================
        (
            "FP01-batch-id",
            "FP",
            json!({
                "candidate_id": "wassur2-fp01",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "batch_id": "B-2026-0731"
            }),
        ),
        (
            "FP02-supplier-french-accent",
            "FP",
            json!({
                "candidate_id": "wassur2-fp02",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "fournisseur_soci\u{00E9}t\u{00E9}_ref": "SOC-4471"
            }),
        ),
        (
            "FP03-viscosity-degree-symbol",
            "FP",
            json!({
                "candidate_id": "wassur2-fp03",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "viscosity_cP_25\u{00B0}C": 850.0
            }),
        ),
        (
            "FP04-attorney-docket-number-only",
            "FP",
            json!({
                "candidate_id": "wassur2-fp04",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "attorney_docket_number": "AMPH-2026-0142"
            }),
        ),
        (
            "FP05-clearance-height",
            "FP",
            json!({
                "candidate_id": "wassur2-fp05",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "clearance_height_mm": 12.5
            }),
        ),
        (
            "FP06-grant-funding-source",
            "FP",
            json!({
                "candidate_id": "wassur2-fp06",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "grant_funding_source": "internal R&D budget"
            }),
        ),
        (
            "FP07-confirmation-email",
            "FP",
            json!({
                "candidate_id": "wassur2-fp07",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "confirmation_email_address": "lab@amphora.bio"
            }),
        ),
        (
            "FP08-counsel-office-address",
            "FP",
            json!({
                "candidate_id": "wassur2-fp08",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "counsel_office_address": "1 Legal Plaza"
            }),
        ),
        (
            "FP09-facade-coating-thickness-nonascii",
            "FP",
            json!({
                "candidate_id": "wassur2-fp09",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "fa\u{00E7}ade_coating_thickness_\u{03BC}m": 45.0
            }),
        ),
        (
            "FP10-naive-bayes-confidence-nonascii",
            "FP",
            json!({
                "candidate_id": "wassur2-fp10",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "na\u{00EF}ve_bayes_confidence_score": 0.87
            }),
        ),
        (
            "FP11-fto-search-vendor-name",
            "FP",
            json!({
                "candidate_id": "wassur2-fp11",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "fto_search_vendor_name": "Acme Patent Search Co."
            }),
        ),
        (
            "FP12-counsel-review-confirmation-id-boundary",
            "FP",
            json!({
                "candidate_id": "wassur2-fp12",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "counsel_review_confirmation_id": "REV-88231"
            }),
        ),
        (
            "FP13-attorney-confirmed-meeting-time-boundary",
            "FP",
            json!({
                "candidate_id": "wassur2-fp13",
                "candidate_type": "formulation",
                "formulation": formulation(),
                "attorney_confirmed_meeting_time": "2026-08-10T14:00:00Z"
            }),
        ),
    ]
}

fn main() {
    let cap = AssuranceCapability::new("amphora-ip-fto-guard").expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = ExecutionContext {
        run_id: "wassur2-attack".into(),
        deterministic_seed: 20260809,
        lineage: Value::Null,
    };
    let mut records = Vec::new();
    for (scenario_id, family, candidate) in scenarios() {
        let envelope = CandidateEnvelope::from_value(candidate).expect("candidate parses");
        let out = cap.evaluate(&envelope, &features, &ctx).expect("evaluate ok");
        let out = serde_json::to_value(&out).expect("serializes");
        let ignored = out
            .get("metrics")
            .and_then(|m| m.get("boolean_counsel_assertion_ignored"))
            .cloned()
            .unwrap_or(Value::Null);
        let detected = ignored == json!(true);
        // Expectations:
        //  - control-clean-negative: expect NOT detected
        //  - control-known-good-A8: expect detected
        //  - CG-baseline-*: uncorrupted assertions, expect detected
        //  - CG/MA/FW/ZB/CM (attack probes): these ARE attempted assertions,
        //    so "evaded" = not detected = evasion (bad)
        //  - FP*: legitimate non-assertion keys, expect NOT detected;
        //    "false_positive" = detected = true (bad)
        let is_fp_family = family == "FP";
        let is_control_negative = scenario_id == "control-clean-negative";
        let expect_detected = !is_fp_family && !is_control_negative;
        let evaded = expect_detected && !detected;
        let false_positive = is_fp_family && detected;
        records.push(json!({
            "scenario_id": scenario_id,
            "family": family,
            "metrics": out.get("metrics"),
            "gates": out.get("gates"),
            "status": out.get("status"),
            "boolean_counsel_assertion_ignored": ignored,
            "detected": detected,
            "expect_detected": expect_detected,
            "evaded": evaded,
            "false_positive": false_positive,
        }));
    }
    let output = json!({"records": records});
    println!("{}", serde_json::to_string_pretty(&output).expect("prints"));
}
