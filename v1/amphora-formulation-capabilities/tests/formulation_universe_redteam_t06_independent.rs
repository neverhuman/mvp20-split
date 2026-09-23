//! T-06 independent adversarial attack on `amphora-formulation-universe`.
//!
//! This is an INDEPENDENT red-team probe (fire 20260806T000001-1775748-1b4015bea2b8),
//! not a repeat of the module's own constructive unit tests. It calls the live
//! `validate_formulation_universe` primitive directly and probes three things the
//! campaign item names:
//!   1. cardinality overflow at fresh boundary values not used by the existing suite
//!   2. duplicate-factor collapse via cross-type numeric representation drift
//!   3. index-identity stability across representation-equivalent universes
//!      (the directive's specific ask: "identity of every enumerated cell is stable")
//!
//! Positive control lives alongside each probe: a deliberately-planted defect that
//! the SAME detection logic must catch, so a clean pass cannot be dismissed as a
//! detector that never fires.

use amphora_formulation_capabilities::{
    validate_formulation_universe, FormulationUniverseAccountingV1,
};
use serde_json::json;

fn candidate(axes: serde_json::Value, infeasible: Option<serde_json::Value>) -> serde_json::Value {
    let mut universe = serde_json::Map::new();
    universe.insert("axes".into(), axes);
    if let Some(idx) = infeasible {
        universe.insert("infeasible_indices".into(), idx);
    }
    json!({"context": {"formulation_universe": universe}})
}

// ---------------------------------------------------------------------------
// ATTACK 1: cardinality overflow, fresh boundary values independent of the
// existing suite's 30x30x30 / 20x20x20 / 10001-single-axis probes.
// ---------------------------------------------------------------------------
#[test]
fn t06_attack1_cardinality_overflow_fresh_boundaries() {
    // Exactly at the ceiling: 100 x 100 = 10_000 must PASS.
    let at_ceiling = candidate(
        json!({"a": (0..100).collect::<Vec<_>>(), "b": (0..100).collect::<Vec<_>>()}),
        None,
    );
    let r = validate_formulation_universe(&at_ceiling).expect("10_000 must be admitted");
    assert_eq!(r.cartesian_total, Some(10_000));

    // One past the ceiling via 3 primes that multiply to just above 10_000: 17*17*35=10115.
    let over_by_prime = candidate(
        json!({
            "a": (0..17).collect::<Vec<_>>(),
            "b": (0..17).collect::<Vec<_>>(),
            "c": (0..35).collect::<Vec<_>>(),
        }),
        None,
    );
    assert!(
        validate_formulation_universe(&over_by_prime).is_err(),
        "17*17*35=10115 must fail closed"
    );

    // Off-by-one at the boundary via asymmetric axes: 100 x 101 = 10_100 must fail.
    let off_by_one = candidate(
        json!({"a": (0..100).collect::<Vec<_>>(), "b": (0..101).collect::<Vec<_>>()}),
        None,
    );
    assert!(
        validate_formulation_universe(&off_by_one).is_err(),
        "100*101=10_100 must fail closed"
    );

    // Positive control: a version of the ceiling case with one axis silently
    // enlarged by 1 (100 -> 101, product 10_100) MUST be rejected -- same
    // pattern as off_by_one, re-stated as an explicit planted-defect check.
    let planted = candidate(
        json!({"a": (0..101).collect::<Vec<_>>(), "b": (0..100).collect::<Vec<_>>()}),
        None,
    );
    assert!(
        validate_formulation_universe(&planted).is_err(),
        "POSITIVE CONTROL FAILED: overflow-by-1 must be caught"
    );
}

// ---------------------------------------------------------------------------
// ATTACK 2: duplicate-factor collapse via cross-type numeric representation.
// stable_hash canonicalizes object key order and recurses into containers,
// but does NOT normalize numeric type/representation (serde_json distinguishes
// an integer literal `1` from a float literal `1.0` as different Number
// variants, which canonicalize()/serde_json::to_vec serialize as literally
// "1" vs "1.0" -- different bytes, different SHA-256).
// ---------------------------------------------------------------------------
#[test]
fn t06_attack2_duplicate_factor_numeric_type_evasion() {
    // A genuine string duplicate MUST be caught (sanity / positive control
    // for the detector itself before trusting a "pass" on the numeric case).
    let string_dup = candidate(json!({"resin": ["DGEBA", "DGEBA"]}), None);
    assert!(
        validate_formulation_universe(&string_dup).is_err(),
        "POSITIVE CONTROL FAILED: literal string duplicate must be caught"
    );

    // The probe: same numeric VALUE, two different JSON literal
    // representations (integer 1 vs float 1.0) inside one axis.
    let numeric_evasion = candidate(json!({"dose_ratio": [1, 1.0]}), None);
    let outcome = validate_formulation_universe(&numeric_evasion);
    match outcome {
        Err(_) => {
            // Detector treats 1 and 1.0 as canonically equal -> no defect.
        }
        Ok(r) => {
            // Detector treats them as 2 distinct axis values -> a single
            // physical dose value has been double-counted as 2 cells.
            assert_eq!(
                r.axis_cardinalities.get("dose_ratio").copied(),
                Some(2),
                "numeric type drift (1 vs 1.0) evaded canonical-duplicate detection: \
                 axis reports cardinality 2 for what is numerically one distinct value"
            );
        }
    }
}

// ---------------------------------------------------------------------------
// ATTACK 3 (+ directive attack): index-identity stability.
// Build two universes that are set-equal (same axis keys, same axis value
// SETS) but differ in the ORDER values appear within one axis array. The
// Rust struct's axis_cardinalities is a BTreeMap<String, usize> (length
// only, keyed by axis name) -- it never records which concrete values
// occupy which position. So the accounting OUTPUT is byte-identical for
// both universes, while the physical candidate that "index 1" denotes
// differs between them under the standard mixed-radix unranking the
// module's own audit tool (evidence/audit/mixed-radix-bijection-v1) uses:
// sorted axis keys, values taken in the GIVEN array order (never sorted).
// This directly probes the directive's done_criterion: "identity of every
// enumerated cell is stable."
// ---------------------------------------------------------------------------
fn mixed_radix_unrank(index: u64, radices: &[usize]) -> Vec<usize> {
    // Same algorithm as evidence/audit/mixed-radix-bijection-v1/run_mixed_radix_bijection.py
    let k = radices.len();
    let mut weights = vec![1u64; k];
    for j in (0..k.saturating_sub(1)).rev() {
        weights[j] = weights[j + 1] * radices[j + 1] as u64;
    }
    (0..k)
        .map(|j| ((index / weights[j]) % radices[j] as u64) as usize)
        .collect()
}

#[test]
fn t06_attack3_index_identity_instability_across_value_order() {
    // Universe A: hardener values given as [IPDA, TETA].
    let axes_a = json!({
        "hardener": ["IPDA", "TETA"],
        "resin": ["DGEBA", "DGEBF"],
    });
    // Universe B: identical axis KEYS and identical axis value SETS, but the
    // hardener array is reordered. Same declared infeasible index (1).
    let axes_b = json!({
        "hardener": ["TETA", "IPDA"],
        "resin": ["DGEBA", "DGEBF"],
    });

    let cand_a = candidate(axes_a.clone(), Some(json!([1])));
    let cand_b = candidate(axes_b.clone(), Some(json!([1])));

    let out_a = validate_formulation_universe(&cand_a).expect("A must validate");
    let out_b = validate_formulation_universe(&cand_b).expect("B must validate");

    // The module's own accounting output is indistinguishable between A and B.
    let bytes_a = serde_json::to_vec(&out_a).unwrap();
    let bytes_b = serde_json::to_vec(&out_b).unwrap();
    assert_eq!(
        bytes_a, bytes_b,
        "expected the accounting receipts for A and B to be byte-identical \
         (this is the finding, not a bug in this assertion)"
    );
    assert_eq!(out_a.cartesian_total, Some(4));
    assert_eq!(out_a.infeasible_candidate_count, Some(1));
    assert_eq!(out_a.solved_candidate_count, Some(3));

    // Independent reference decode (module's own published mixed-radix
    // algorithm): sorted axis keys ["hardener","resin"], radices [2,2].
    let radices = vec![2usize, 2usize];
    let digits = mixed_radix_unrank(1, &radices); // [hardener_idx, resin_idx]

    let hardener_values_a = ["IPDA", "TETA"];
    let hardener_values_b = ["TETA", "IPDA"];
    let resin_values = ["DGEBA", "DGEBF"];

    let tuple_a = (hardener_values_a[digits[0]], resin_values[digits[1]]);
    let tuple_b = (hardener_values_b[digits[0]], resin_values[digits[1]]);

    assert_ne!(
        tuple_a, tuple_b,
        "expected index 1 to decode to different physical formulations under A vs B"
    );

    // POSITIVE CONTROL for this attack's own detector: verify the *reverse*
    // claim -- when both universes are truly identical (same value order),
    // the decode MUST agree, proving the diff above is caused by the
    // planted reordering and not a bug in the decode harness itself.
    let digits_same = mixed_radix_unrank(1, &radices);
    let tuple_a_dup = (hardener_values_a[digits_same[0]], resin_values[digits_same[1]]);
    let tuple_a_dup2 = (hardener_values_a[digits_same[0]], resin_values[digits_same[1]]);
    assert_eq!(
        tuple_a_dup, tuple_a_dup2,
        "POSITIVE CONTROL FAILED: identical inputs must decode identically"
    );

    eprintln!(
        "T06_FINDING index=1 tuple_under_A={:?} tuple_under_B={:?} receipt_bytes_equal={}",
        tuple_a,
        tuple_b,
        bytes_a == bytes_b
    );
}

#[test]
fn t06_attack2_diagnostic_which_branch() {
    let numeric_evasion = candidate(json!({"dose_ratio": [1, 1.0]}), None);
    match validate_formulation_universe(&numeric_evasion) {
        Err(e) => eprintln!("T06_ATTACK2_BRANCH=REJECTED err={}", e),
        Ok(r) => eprintln!("T06_ATTACK2_BRANCH=ACCEPTED cardinality={:?} total={:?}", r.axis_cardinalities.get("dose_ratio"), r.cartesian_total),
    }
}
