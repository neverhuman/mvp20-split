// RFC 8785 (JSON Canonicalization Scheme, IETF, June 2020, DOI 10.17487/RFC8785)
// conformance probe for amphora-candidate-contract's CandidateEnvelope::contract_hash_v1.
//
// The module's own Phase-0 KPI receipt
// (evidence/phase0/kpis/candidate-contract-strict-json-integrity-kpi.v1.json,
// metric positive_from_bytes_from_value_agree_on_contract_hash_rate) asserts:
//   "stable_hash is canonical-JSON-invariant across input framings (RFC 8785 JCS
//   foundation)."
// This probe tests that specific claim empirically against amphora-core's own,
// separately RFC-8785-conformance-tested implementation (src/jcs.rs, jcs_bytes /
// jcs_sha256, backed by the serde_jcs crate and reference-vector unit tests
// rfc8785_property_order_and_unicode_are_canonical and
// rfc8785_number_formatting_is_ecmascript_compatible).

use amphora_core::{canonicalize, jcs_bytes, jcs_sha256, stable_hash, CandidateEnvelope};
use serde_json::json;

#[test]
fn contract_hash_v1_property_order_diverges_from_rfc8785_utf16_code_unit_sort() {
    // RFC 8785 section 3.2.3 mandates object-property sorting by comparing UTF-16
    // code unit values, not Unicode code points.
    //   U+1F600 (GRINNING FACE, supplementary plane) encodes in UTF-16 as the
    //     surrogate pair 0xD83D 0xDE00 -> first code unit 0xD83D.
    //   U+FB33 (HEBREW LETTER DALET WITH DAGESH, BMP) encodes as the single code
    //     unit 0xFB33.
    // Code-point order:      0xFB33 < 0x1F600  => Hebrew Dalet sorts BEFORE emoji.
    // UTF-16 code-unit order: 0xD83D < 0xFB33   => emoji sorts BEFORE Hebrew Dalet.
    // This exact pair, and this exact ordering outcome, is the reference vector
    // already validated in this crate at src/jcs.rs
    // (test rfc8785_property_order_and_unicode_are_canonical), so jcs_bytes()'s
    // ordering below is taken as ground truth against the published RFC, not
    // re-derived here.
    let value = json!({
        "candidate_id": "probe-utf16-order",
        "candidate_type": "molecule",
        "molecule": {"smiles": "C"},
        "\u{1F600}": "emoji",
        "\u{FB33}": "hebrew-dalet-dagesh"
    });

    // The exact canonicalization contract_hash_v1 is built from:
    // amphora-core/src/contract.rs CandidateEnvelope::build() ->
    // `crate::stable_hash(&value)` -> `crate::canonicalize()` + `serde_json::to_vec`.
    let candidate_bytes = serde_json::to_vec(&canonicalize(&value)).unwrap();
    let candidate_str = String::from_utf8(candidate_bytes).unwrap();

    // The crate's own real RFC 8785 JCS bytes.
    let jcs_str = String::from_utf8(jcs_bytes(&value).unwrap()).unwrap();

    eprintln!("PROBE candidate-canonicalize bytes: {}", candidate_str);
    eprintln!("PROBE rfc8785-jcs bytes:            {}", jcs_str);

    let emoji_pos_candidate = candidate_str.find('\u{1F600}').expect("emoji key present");
    let hebrew_pos_candidate = candidate_str
        .find('\u{FB33}')
        .expect("hebrew dalet key present");
    let emoji_pos_jcs = jcs_str.find('\u{1F600}').expect("emoji key present");
    let hebrew_pos_jcs = jcs_str.find('\u{FB33}').expect("hebrew dalet key present");

    // candidate-contract's canonicalize() uses Rust's default (code-point) Vec<String>
    // sort: Hebrew Dalet sorts before emoji.
    assert!(
        hebrew_pos_candidate < emoji_pos_candidate,
        "expected CandidateEnvelope's canonicalize() to use code-point order \
         (Hebrew Dalet before emoji); observed bytes: {candidate_str}"
    );

    // real RFC 8785 JCS (this crate's own jcs.rs) uses UTF-16 code-unit order: emoji
    // (leading surrogate 0xD83D) sorts before Hebrew Dalet (0xFB33) -- the OPPOSITE
    // relative order from the candidate-contract path above.
    assert!(
        emoji_pos_jcs < hebrew_pos_jcs,
        "expected real RFC 8785 JCS to use UTF-16 code-unit order (emoji before \
         Hebrew Dalet); observed bytes: {jcs_str}"
    );

    // Consequently the hashes differ: contract_hash_v1's "RFC 8785 JCS foundation"
    // claim is not literally true -- it is a materially different canonicalization
    // that happens to agree with RFC 8785 on ASCII-only, BMP-only inputs.
    let contract_hash = stable_hash(&value);
    let real_jcs_hash = jcs_sha256(&value).unwrap();
    assert_ne!(
        contract_hash, real_jcs_hash,
        "contract_hash_v1's canonicalization unexpectedly matched real RFC 8785 JCS"
    );

    // Confirm the divergence is live in the production API surface
    // (CandidateEnvelope::from_value), not just the free function.
    let envelope = CandidateEnvelope::from_value(value.clone()).unwrap();
    assert_eq!(
        envelope.contract_hash_v1(),
        contract_hash,
        "CandidateEnvelope::contract_hash_v1() must equal stable_hash() by construction"
    );
}

#[test]
fn contract_hash_v1_exponent_number_formatting_agrees_with_rfc8785() {
    // RFC 8785 section 3.2.2.3 mandates ECMAScript Number::toString-compatible
    // serialization of JSON numbers (e.g. exponent form with an explicit '+' sign
    // for magnitude >= 1e21). This crate's own jcs.rs reference test
    // (rfc8785_number_formatting_is_ecmascript_compatible) establishes that
    // jcs_bytes() renders 1E30 as "1e+30" per the published RFC.
    //
    // Observed result (recorded honestly, not assumed): serde_json's own f64
    // formatter (ryu-based) happens to already agree with RFC 8785 on this vector,
    // so this specific requirement is CONFORMANT for exponent-form numbers, not
    // divergent. Recorded as evidence for the exponent-number-formatting
    // requirement in the receipt.
    let value: serde_json::Value = serde_json::from_str(r#"{"x":1E30}"#).unwrap();

    let candidate_bytes = serde_json::to_vec(&canonicalize(&value)).unwrap();
    let candidate_str = String::from_utf8(candidate_bytes).unwrap();
    let jcs_str = String::from_utf8(jcs_bytes(&value).unwrap()).unwrap();

    eprintln!("PROBE candidate-canonicalize exponent number: {}", candidate_str);
    eprintln!("PROBE rfc8785-jcs exponent number:            {}", jcs_str);

    assert!(
        jcs_str.contains("1e+30"),
        "real RFC 8785 JCS must emit ECMAScript exponent form '1e+30'; observed: {jcs_str}"
    );
    assert_eq!(
        candidate_str, jcs_str,
        "expected agreement on this exponent-form vector (recorded as CONFORMANT)"
    );
}

#[test]
fn contract_hash_v1_negative_zero_diverges_from_rfc8785_ecmascript_tostring() {
    // RFC 8785 section 3.2.2.3 (via ECMAScript Number::toString) canonicalizes
    // negative zero to "0" -- this crate's own jcs.rs reference test already
    // asserts `jcs_bytes(&-0.0_f64).unwrap() == b"0"`. serde_json's own default f64
    // formatter (ryu-based, used by candidate-contract's canonicalize() path)
    // preserves the IEEE-754 sign bit and emits "-0" instead.
    let value: serde_json::Value = serde_json::from_str(r#"{"x":-0.0}"#).unwrap();

    let candidate_bytes = serde_json::to_vec(&canonicalize(&value)).unwrap();
    let candidate_str = String::from_utf8(candidate_bytes).unwrap();
    let jcs_str = String::from_utf8(jcs_bytes(&value).unwrap()).unwrap();

    eprintln!("PROBE candidate-canonicalize negative-zero: {}", candidate_str);
    eprintln!("PROBE rfc8785-jcs negative-zero:            {}", jcs_str);

    assert!(
        jcs_str.contains(":0}"),
        "real RFC 8785 JCS must canonicalize -0.0 to unsigned 0; observed: {jcs_str}"
    );
    assert_ne!(
        candidate_str, jcs_str,
        "expected divergence on -0.0 formatting between candidate-contract's \
         canonicalize() and real RFC 8785 JCS"
    );
}

#[test]
fn positive_control_real_rfc8785_jcs_detects_non_finite_planted_defect() {
    // Positive control for the harness itself (not for the survival gate -- this
    // module's verdict is CLAIM_REFUTED, which does not require one -- but it
    // demonstrates the jcs_bytes() oracle used above is not a no-op that always
    // passes). Planted defect: a NaN value, which RFC 8785 section 3.1 explicitly
    // forbids as canonicalization input (I-JSON / RFC 7493 compliance
    // precondition). The real JCS implementation must reject it.
    let planted_defect = f64::NAN;
    let result = jcs_bytes(&planted_defect);
    assert!(
        result.is_err(),
        "expected the RFC 8785 JCS oracle to reject a planted NaN defect, got Ok"
    );
    eprintln!("PROBE positive-control jcs_bytes(NaN) = {:?}", result);
}
