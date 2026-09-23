//! DoE known-answer fixture citation-fidelity audit for
//! `amphora-formulation-universe` (ROTATION fire, no campaign item;
//! fire_id 20260817T050001-3280050-bf83a9be45cd).
//!
//! Attacks a claim distinct from T-06 (2026-08-06, duplicate-factor-collapse
//! + index-identity-instability in the live primitive) and kpi-claim-
//! currency-v1 (2026-08-15, staleness of the signed KPI register): whether
//! the Phase-0 known-answer fixture's citations to Montgomery 2017 and
//! Wicks/Jones/Pappas 2007 actually correspond to the design each entry
//! claims to be, and whether `validate_formulation_universe` is even
//! capable of validating the design types it is claimed to cover.
//!
//! `validate_formulation_universe` computes ONLY the plain Cartesian product
//! of declared per-axis value arrays. It has no generator / defining-
//! relation / aliasing logic, and it never reads a `design_type` field at
//! all. So any fixture entry labeled a genuine fractional factorial
//! (2^(k-p), 0<p<k) must, by construction, encode 2^(k-p) axis
//! combinations -- not the full 2^k -- or the runtime never actually
//! exercised cardinality accounting for a real fractional design, contrary
//! to `docs/mission.md`'s claim that "the runtime reproduces every one of
//! the 10 published DoE examples' cardinality counts at u64 bit precision."

use std::fs;
use std::path::PathBuf;

use amphora_formulation_capabilities::validate_formulation_universe;
use serde_json::{json, Map, Value};

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crate has a parent workspace")
        .to_path_buf()
}

fn fixture_path() -> PathBuf {
    workspace_root().join(
        "amphora-formulation-universe/reference/phase0-formulation-universe-known-answer.v1.json",
    )
}

fn read_fixture() -> Value {
    let bytes = fs::read(fixture_path()).expect("fixture readable");
    serde_json::from_slice(&bytes).expect("fixture is JSON")
}

fn build_candidate(axes: &Value, infeasible: Option<&Value>) -> Value {
    let mut universe = Map::new();
    universe.insert("axes".into(), axes.clone());
    if let Some(indices) = infeasible {
        universe.insert("infeasible_indices".into(), indices.clone());
    }
    json!({"context": {"formulation_universe": universe}})
}

/// Parse a "2^(k-p)" pattern out of a string (universe_id / nominal_source).
/// Returns Some((k, p)) if a literal numeric k-p pair is present.
fn parse_2kp(s: &str) -> Option<(u32, u32)> {
    let start = s.find("2^(")?;
    let rest = &s[start + 3..];
    let close = rest.find(')')?;
    let inner = &rest[..close];
    let mut parts = inner.split('-');
    let k: u32 = parts.next()?.trim().parse().ok()?;
    let p: u32 = parts.next()?.trim().parse().ok()?;
    Some((k, p))
}

#[test]
fn doe_fixture_positive_control_parser_reads_well_formed_labels() {
    // POSITIVE CONTROL for the parser itself: a well-formed literal k-p
    // pair must parse, and a non-numeric template ("k-p") must not, so a
    // clean verdict below cannot be dismissed as a parser that never fires
    // or that fires on everything indiscriminately.
    assert_eq!(parse_2kp("2^(5-1)-half-fraction-screening"), Some((5, 1)));
    assert_eq!(parse_2kp("2^(k-p)_fractional_factorial"), None);
    assert_eq!(parse_2kp("2^k_full_factorial"), None);
}

#[test]
fn doe_fixture_citation_fidelity_audit() {
    let fixture = read_fixture();
    let universes = fixture["universes"].as_array().expect("universes array");
    assert_eq!(
        universes.len(),
        10,
        "fixture must have exactly 10 universes as documented in docs/mission.md"
    );

    let mut mismatches = Vec::new();
    let mut fractional_entries_examined = 0;

    for u in universes {
        let axes = &u["axes"];
        let expected_total = u["expected_cartesian_total"]
            .as_u64()
            .expect("expected_cartesian_total");
        let universe_id = u["universe_id"].as_str().unwrap_or_default();
        let design_type = u["design_type"].as_str().unwrap_or_default();
        let nominal_source = u["nominal_source"].as_str().unwrap_or_default();

        // Baseline sanity (already covered by the existing KPI; re-derived
        // independently here, not the novel probe): the fixture's own
        // declared total matches a raw product of its axis cardinalities,
        // and the LIVE runtime returns that same raw product given exactly
        // this universe's axes.
        let raw_product: u64 = axes
            .as_object()
            .unwrap()
            .values()
            .map(|v| v.as_array().unwrap().len() as u64)
            .product();
        assert_eq!(
            raw_product, expected_total,
            "fixture arithmetic must be internally consistent for {universe_id}"
        );

        let infeasible = u.get("infeasible_indices");
        let candidate = build_candidate(axes, infeasible);
        let out = validate_formulation_universe(&candidate).expect("fixture universe must validate");
        assert_eq!(out.cartesian_total, Some(raw_product));

        // THE NOVEL PROBE: does this entry's own citation (universe_id /
        // nominal_source) describe a genuine fractional factorial 2^(k-p),
        // and if so does expected_total actually equal 2^(k-p) rather than
        // the full 2^k the runtime can only ever compute?
        if design_type.contains("fractional") {
            fractional_entries_examined += 1;
            let (k, p) = parse_2kp(universe_id)
                .or_else(|| parse_2kp(nominal_source))
                .expect("a fractional-factorial entry must name its (k,p) in universe_id or nominal_source");
            assert!(p >= 1 && p < k, "fractional design must have 0<p<k");
            let genuine_fraction_total = 2u64.pow(k - p);
            let full_total = 2u64.pow(k);
            if expected_total != genuine_fraction_total {
                mismatches.push(json!({
                    "universe_id": universe_id,
                    "design_type": design_type,
                    "nominal_source": nominal_source,
                    "claimed_k": k,
                    "claimed_p": p,
                    "genuine_fraction_total_2_pow_k_minus_p": genuine_fraction_total,
                    "full_unfractionated_total_2_pow_k": full_total,
                    "expected_cartesian_total_in_fixture": expected_total,
                    "runtime_returned_cartesian_total": out.cartesian_total,
                    "finding": "fixture/citation claims a 2^(k-p) fractional-factorial design but expected_cartesian_total equals the FULL 2^k space, not the fraction; the live runtime returns that same full total, confirming validate_formulation_universe has no generator/defining-relation/aliasing logic and cannot represent or verify a genuine fractional design",
                }));
            }
        }
    }

    assert!(
        fractional_entries_examined >= 1,
        "fixture must contain at least one fractional-factorial-labeled entry to test"
    );

    eprintln!(
        "DOE_CITATION_FIDELITY_MISMATCHES={}",
        serde_json::to_string(&mismatches).unwrap()
    );
    eprintln!(
        "DOE_CITATION_FIDELITY_FRACTIONAL_ENTRIES_EXAMINED={fractional_entries_examined}"
    );

    assert!(
        !mismatches.is_empty(),
        "expected to find at least one citation/value mismatch (this assertion documents \
         the finding; if it ever fails because the fixture was corrected, that is a real \
         repair and this test should be revisited)"
    );
}

#[test]
fn doe_fixture_design_type_field_is_never_consumed_by_runtime() {
    // Confirms design_type is decorative-only: feeding the SAME axes with a
    // DIFFERENT (even self-contradictory) design_type label produces an
    // IDENTICAL accounting result, because validate_formulation_universe
    // never reads /context/formulation_universe/design_type at all.
    let axes = json!({
        "a": ["x", "y"],
        "b": ["p", "q"],
        "c": ["m", "n"],
        "d": ["r", "s"],
        "e": ["t", "u"],
    });
    let mut universe_labeled_fractional = Map::new();
    universe_labeled_fractional.insert("axes".into(), axes.clone());
    universe_labeled_fractional.insert("design_type".into(), json!("2^(5-1)_fractional_factorial"));
    let cand_fractional = json!({"context": {"formulation_universe": universe_labeled_fractional}});

    let mut universe_labeled_full = Map::new();
    universe_labeled_full.insert("axes".into(), axes.clone());
    universe_labeled_full.insert("design_type".into(), json!("2^k_full_factorial"));
    let cand_full = json!({"context": {"formulation_universe": universe_labeled_full}});

    let out_fractional = validate_formulation_universe(&cand_fractional).expect("must validate");
    let out_full = validate_formulation_universe(&cand_full).expect("must validate");

    assert_eq!(out_fractional.cartesian_total, Some(32));
    assert_eq!(out_full.cartesian_total, Some(32));
    assert_eq!(
        serde_json::to_vec(&out_fractional).unwrap(),
        serde_json::to_vec(&out_full).unwrap(),
        "design_type must be provably unread by the runtime: labeling the SAME \
         5-binary-axis universe a half-fraction vs a full factorial must not change \
         the accounting output"
    );
}
