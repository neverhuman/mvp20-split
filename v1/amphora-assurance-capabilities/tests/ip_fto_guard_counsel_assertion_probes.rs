//! Repair R-B01 regression suite for `amphora-ip-fto-guard`.
//!
//! Locks in the two fixes demanded by the refuting AUDIT_ONLY receipts:
//!
//! 1. `evidence/audit/counsel-assertion-detection-completeness-v1` (verdict
//!    REFUTED): the pre-repair counsel-assertion lock was a single
//!    literal-path presence check
//!    (`evidence_refs.counsel_fto.signed_by_counsel`) and produced a 100%
//!    false-negative rate (8/8) against alternate encodings. Each of the 8
//!    adversarial probe encodings from that audit (scenario ids A1..A8) is
//!    reproduced here as a checked test and MUST now be detected
//!    (`boolean_counsel_assertion_ignored=true`) while every safety
//!    invariant stays pinned (`fto_status='FTO NOT PERFORMED'`,
//!    `legal_advice=false`, `fto_legal_closure=false`).
//!
//! 2. `evidence/audit/metric-schema-parity-v1` (verdict CLAIM_REFUTED): the
//!    declared PRIMARY KPI value path
//!    `metrics.unresolved_technical_categories` was populated by nothing.
//!    The runtime now populates it from the embedded claim-chart category
//!    census; this suite asserts it against an independent recompute from
//!    the on-disk fixture.
//!
//! NOTE on provenance: the original audit probe harness lived at
//! /tmp/ip_fto_probe (main.rs sha256
//! 15218060d5afac43b7a7bdcc9532ee7b1e4c4e369248b4ecd25d3b46152229c8d) and is
//! no longer on disk; the probe candidates below are reconstructed from the
//! signed audit receipt's scenario ids and per-scenario encoding-class
//! descriptions (top-level key, array-typed container, one-level-deeper
//! nesting, key-case variant, alternate key name, semantically-equivalent
//! alternate field, string-typed container, unicode-homoglyph key).
//!
//! 3. Repair W-ASSUR1 regression: `evidence/phase0/repairs/V-B01` (verdict
//!    REFUTED) independently adversarially verified R-B01 with 5 NOVEL
//!    encodings beyond A1..A8 and found 2 of them (V1, V2) still evaded
//!    detection - both used U+00FC (LATIN SMALL LETTER U WITH DIAERESIS) in
//!    place of plain 'u'. Root cause: `normalized_key_skeleton` ran NFKC
//!    (which recomposes the canonical decomposition of U+00FC back into
//!    U+00FC) then filtered to ASCII alphanumerics, so U+00FC was silently
//!    DROPPED rather than folded to 'u', breaking the `counsel` substring
//!    match. Fixed by decomposing with NFKD instead (no recomposition), so
//!    the leftover combining diaeresis mark is stripped by the existing
//!    ASCII filter and the bare base letter 'u' survives. V1..V5 below (the
//!    exact scenario ids and candidate JSON bodies from the V-B01 verify
//!    receipt's probe harness) are reproduced here as checked regression
//!    tests: V1 and V2 (previously-evading) MUST now be detected; V3, V4, V5
//!    (already detected pre-fix per V-B01) MUST remain detected.

use std::fs;
use std::path::PathBuf;

use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot, ModuleResult};
use serde_json::{json, Value};

const IP_FTO_GUARD: &str = "amphora-ip-fto-guard";

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "repair-r-b01-counsel-assertion-probes".into(),
        deterministic_seed: 20260803,
        lineage: Value::Null,
    }
}

fn evaluate(candidate: Value) -> ModuleResult {
    let candidate = CandidateEnvelope::from_value(candidate).expect("candidate parses");
    AssuranceCapability::new(IP_FTO_GUARD)
        .expect("capability constructs")
        .evaluate(&candidate, &FeatureSnapshot::default(), &context())
        .expect("evaluate ok")
}

fn formulation() -> Value {
    json!({"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}})
}

/// The safety invariants the refuting audit verified stayed intact in all
/// scenarios; they must STILL hold with the broadened detection.
fn assert_safety_invariants(result: &ModuleResult) {
    assert_eq!(
        result.metrics.get("fto_status"),
        Some(&json!("FTO NOT PERFORMED")),
        "fto_status must stay pinned"
    );
    assert_eq!(
        result.metrics.get("legal_advice"),
        Some(&json!(false)),
        "legal_advice must stay false"
    );
    assert_eq!(
        result.gates.get("fto_legal_closure"),
        Some(&json!(false)),
        "fto_legal_closure gate must stay false"
    );
    assert_eq!(result.status, "SCORED");
    assert!(result.objective_values.is_empty());
}

fn assert_detected(scenario_id: &str, candidate: Value) {
    let result = evaluate(candidate);
    assert_eq!(
        result.metrics.get("boolean_counsel_assertion_ignored"),
        Some(&json!(true)),
        "{scenario_id}: counsel-signoff assertion must be detected and recorded as ignored"
    );
    assert_safety_invariants(&result);
}

// --- the 8 adversarial encodings from the refuting audit -------------------

#[test]
fn a1_top_level_key_is_detected() {
    assert_detected(
        "A1-top-level-key",
        json!({
            "candidate_id": "probe-a1",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "signed_by_counsel": true
        }),
    );
}

#[test]
fn a2_counsel_fto_array_container_is_detected() {
    assert_detected(
        "A2-counsel-fto-array",
        json!({
            "candidate_id": "probe-a2",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "evidence_refs": {"counsel_fto": [{"signed_by_counsel": true}]}
        }),
    );
}

#[test]
fn a3_nested_one_level_deeper_is_detected() {
    assert_detected(
        "A3-nested-one-level-deeper",
        json!({
            "candidate_id": "probe-a3",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "evidence_refs": {"legal": {"counsel_fto": {"signed_by_counsel": true}}}
        }),
    );
}

#[test]
fn a4_case_variant_key_is_detected() {
    assert_detected(
        "A4-case-variant-key",
        json!({
            "candidate_id": "probe-a4",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "evidence_refs": {"Counsel_FTO": {"Signed_By_Counsel": true}}
        }),
    );
}

#[test]
fn a5_alternate_path_name_is_detected() {
    assert_detected(
        "A5-alternate-path-name",
        json!({
            "candidate_id": "probe-a5",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "evidence_refs": {"counsel_signoff": {"granted": true}}
        }),
    );
}

#[test]
fn a6_semantic_alt_claim_key_is_detected() {
    assert_detected(
        "A6-semantic-alt-claim-key",
        json!({
            "candidate_id": "probe-a6",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "evidence_refs": {"fto_cleared_by_counsel": true}
        }),
    );
}

#[test]
fn a7_counsel_fto_string_container_is_detected() {
    assert_detected(
        "A7-counsel-fto-string",
        json!({
            "candidate_id": "probe-a7",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "evidence_refs": {"counsel_fto": "signed off by outside counsel 2026-07-01"}
        }),
    );
}

#[test]
fn a8_unicode_confusable_key_is_detected() {
    // "ѕigned_by_counѕel" spelled with U+0455 CYRILLIC SMALL LETTER DZE,
    // placed at top level so only the homoglyph fold can catch it.
    assert_detected(
        "A8-unicode-confusable-key",
        json!({
            "candidate_id": "probe-a8",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "\u{0455}igned_by_coun\u{0455}el": true
        }),
    );
}

// --- V-B01 novel encodings (repair W-ASSUR1) --------------------------------

#[test]
fn v1_uncovered_homoglyph_deletion_signedbycounsel_is_detected() {
    // "signed_by_co\u{FC}nsel" (U+00FC LATIN SMALL LETTER U WITH DIAERESIS in
    // place of 'u'). Pre-fix: NFKC recomposed U+00FC and it was absent from
    // fold_confusable's table, so it was silently DROPPED, leaving skeleton
    // "signedbyconsel" (missing the 'u'), which does not contain "counsel"
    // -> UNDETECTED. Post-fix (NFKD, no recomposition): decomposes to
    // 'u' + combining diaeresis, the mark is stripped by the ascii filter,
    // skeleton is "signedbycounsel" -> DETECTED.
    assert_detected(
        "V1-uncovered-homoglyph-deletion-signedbycounsel",
        json!({
            "candidate_id": "vb01-v1",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "evidence_refs": {"signed_by_co\u{FC}nsel": true}
        }),
    );
}

#[test]
fn v2_uncovered_homoglyph_deletion_counselfto_is_detected() {
    // Same deletion class applied to the OTHER canonical key:
    // "co\u{FC}nsel_fto" -> post-fix skeleton "counselfto" (exact canonical
    // name) -> DETECTED.
    assert_detected(
        "V2-uncovered-homoglyph-deletion-counselfto",
        json!({
            "candidate_id": "vb01-v2",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "evidence_refs": {"co\u{FC}nsel_fto": {"cleared": true}}
        }),
    );
}

#[test]
fn v3_zero_width_joiner_in_key_is_detected() {
    // ZWJ (U+200D) inside the key; already detected pre-fix (non-alphanumeric
    // is simply filtered out regardless of the decomposition/confusable
    // step) - regression-locked here so the fix does not regress it.
    assert_detected(
        "V3-zero-width-joiner-in-key",
        json!({
            "candidate_id": "vb01-v3",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "evidence_refs": {"sign\u{200D}ed_by_coun\u{200D}sel": true}
        }),
    );
}

#[test]
fn v4_deeply_nested_array_of_objects_alias_is_detected() {
    // "counsel_signoff" semantic-alt key buried several levels deep inside
    // an array of unrelated sibling objects; already detected pre-fix
    // (recursion has no depth/shape gap) - regression-locked here.
    assert_detected(
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
    );
}

#[test]
fn v5_fullwidth_unicode_escape_key_is_detected() {
    // U+FF55 FULLWIDTH LATIN SMALL LETTER U in place of ASCII 'u'; fullwidth
    // forms have an NFKC *and* NFKD compatibility decomposition to their
    // ASCII counterpart, so this was already detected pre-fix and remains
    // detected under NFKD - regression-locked here as a distinct mechanism
    // from V1/V2's non-recomposing canonical-decomposition fix.
    assert_detected(
        "V5-fullwidth-unicode-escape-key",
        json!({
            "candidate_id": "vb01-v5",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "signed_by_co\u{FF55}nsel": true
        }),
    );
}

// --- controls ---------------------------------------------------------------

#[test]
fn control_exact_path_true_is_still_detected() {
    assert_detected(
        "control-exact-path-true",
        json!({
            "candidate_id": "probe-control",
            "candidate_type": "formulation",
            "formulation": formulation(),
            "evidence_refs": {"counsel_fto": {"signed_by_counsel": true}}
        }),
    );
}

#[test]
fn clean_candidate_is_not_flagged() {
    let result = evaluate(json!({
        "candidate_id": "probe-clean-negative",
        "candidate_type": "formulation",
        "formulation": formulation(),
        "evidence_refs": {"lab_receipts": {"session_id": "irrelevant-lab-receipt"}}
    }));
    assert_eq!(
        result.metrics.get("boolean_counsel_assertion_ignored"),
        Some(&json!(false)),
        "clean candidate with unrelated evidence_refs must not be flagged"
    );
    assert_safety_invariants(&result);
}

// --- primary KPI value path (metric-schema-parity-v1 repair) ----------------

#[test]
fn primary_kpi_value_path_is_populated_and_matches_fixture_recompute() {
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("workspace root")
        .join("amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json");
    let landscape: Value =
        serde_json::from_slice(&fs::read(fixture_path).expect("fixture readable"))
            .expect("fixture JSON");
    let expected_unresolved = landscape["claim_chart_categories"]
        .as_array()
        .expect("claim_chart_categories array")
        .iter()
        .filter(|category| category["not_fto"].as_bool() != Some(false))
        .count();
    assert!(expected_unresolved > 0, "fixture census must be non-empty");

    let result = evaluate(json!({
        "candidate_id": "primary-kpi-population",
        "candidate_type": "formulation",
        "formulation": formulation()
    }));
    assert_eq!(
        result.metrics.get("unresolved_technical_categories"),
        Some(&json!(expected_unresolved)),
        "declared primary KPI value path must be populated by the live runtime and match the independent fixture recompute"
    );
    assert_safety_invariants(&result);
}
