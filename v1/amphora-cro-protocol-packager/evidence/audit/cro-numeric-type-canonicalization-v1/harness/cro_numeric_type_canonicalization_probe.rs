//! Numeric-type canonicalization probe for amphora-cro-protocol-packager.
//!
//! Live-runtime attack against the REAL compiled `CroProtocolPackageV2`
//! (draft, validate, sign, verify_signature) in
//! amphora-assurance-capabilities/src/lib.rs, plus the shared
//! `amphora_core::stable_hash`/`canonicalize` binding primitive both
//! `candidate_sha256` and `formula_sha256` are built from.
//!
//! Extends the 2026-07-28 `canonicalization-conformance-v1` audit (Python
//! diagnostic only, never run against the live Rust runtime, explicitly
//! flagged "does not itself re-serialize the runtime's formula_sha256"). That
//! audit found the module's binding canonicalization scheme is NOT RFC-8785
//! JCS conformant: integer-valued float numbers (110.0) and true integers
//! (110) hash differently. This probe (a) confirms that gap is real on the
//! LIVE compiled runtime, not merely a Python re-implementation, and (b)
//! precisely locates which of the module's two content bindings actually
//! carries the live vulnerability: `candidate_binding` (raw arbitrary
//! `serde_json::Value` from the producer) is exposed; `equivalent_balance`
//! (a strongly-typed `EquivalentBalanceV1` struct with `f64` fields) is not,
//! because serde deserializes any JSON number lexical form into the same
//! `f64` before it is ever re-serialized.
//!
//! Falsifiable hypothesis under attack (docs/mission.md): "candidate and
//! formula binding prevents ambiguous or nonnumeric lab packets."

use std::collections::BTreeMap;

use amphora_assurance_capabilities::{CroProtocolPackageV2, CRO_PROTOCOL_PACKAGE_V2_SCHEMA};
use amphora_core::{stable_hash, TrustStore};
use amphora_formulation_capabilities::{EquivalentBalanceV1, EQUIVALENT_BALANCE_SCHEMA};
use ed25519_dalek::SigningKey;
use serde_json::{json, Value};

fn balance(resin_mass_g: f64, hardener_mass_g: f64) -> EquivalentBalanceV1 {
    let ratio = resin_mass_g / hardener_mass_g;
    EquivalentBalanceV1 {
        schema: EQUIVALENT_BALANCE_SCHEMA.into(),
        resin_facts_sha256: "a".repeat(64),
        hardener_facts_sha256: "b".repeat(64),
        resin_structure_sha256: "c".repeat(64),
        hardener_structure_sha256: "d".repeat(64),
        eew_g_per_eq: 100.0,
        ahew_g_per_eq: 100.0 / ratio,
        resin_mass_g,
        hardener_mass_g,
        epoxide_equivalents: resin_mass_g / 100.0,
        amine_hydrogen_equivalents: resin_mass_g / 100.0,
        theoretical_hardener_phr: hardener_mass_g * 100.0 / resin_mass_g,
        equivalent_ratio: 1.0,
        total_mass_g: resin_mass_g + hardener_mass_g,
        unit_provenance: BTreeMap::from([
            ("mass".into(), "g".into()),
            ("equivalent_weight".into(), "g/eq structure-derived".into()),
        ]),
        authority_ceiling: "AUDIT_ONLY".into(),
        candidate_property_overrides_accepted: false,
        ranking_eligible: false,
    }
}

#[test]
fn cro_numeric_type_canonicalization_probe() {
    assert_eq!(CRO_PROTOCOL_PACKAGE_V2_SCHEMA, "amphora.cro-protocol-package.v2");

    // --- Axis A: candidate_binding (raw Value) --------------------------
    // Two candidates describing the IDENTICAL real formulation charge (110 g
    // resin), differing ONLY in whether the producer's JSON encoder emitted
    // that number as a lexical integer or a lexical float. Both are
    // semantically the same physical quantity; a real producer's choice of
    // "110" vs "110.0" depends only on incidental serializer/arithmetic
    // history (e.g. Python `json.dumps(110)` after integer math vs
    // `json.dumps(110.0)` after float math), not on the candidate itself.
    let candidate_int = json!({
        "candidate_id": "primer-dgeba-teta-numcanon",
        "candidate_type": "formulation",
        "resin": "DGEBA",
        "hardener": "TETA",
        "declared_resin_charge_g": 110,
    });
    let candidate_float = json!({
        "candidate_id": "primer-dgeba-teta-numcanon",
        "candidate_type": "formulation",
        "resin": "DGEBA",
        "hardener": "TETA",
        "declared_resin_charge_g": 110.0,
    });
    assert_ne!(candidate_int, candidate_float, "fixture sanity: literals must differ in Value repr");

    let campaign_id = "campaign-numeric-canon-probe";
    let blinding = "BLIND-NUMCANON-SHARED";
    let bal = balance(110.0, 25.0);

    let mut pkt_int = CroProtocolPackageV2::draft(campaign_id, &candidate_int, bal.clone(), blinding.into())
        .expect("draft() must succeed on int-encoded candidate");
    let mut pkt_float = CroProtocolPackageV2::draft(campaign_id, &candidate_float, bal.clone(), blinding.into())
        .expect("draft() must succeed on float-encoded candidate");

    let draft_int_ok = true;
    let draft_float_ok = true;

    let candidate_sha256_int = pkt_int.candidate_sha256.clone();
    let candidate_sha256_float = pkt_float.candidate_sha256.clone();
    let candidate_sha256_diverges = candidate_sha256_int != candidate_sha256_float;

    let packet_id_int = pkt_int.packet_id.clone();
    let packet_id_float = pkt_float.packet_id.clone();
    let packet_id_diverges = packet_id_int != packet_id_float;

    // Independent recompute, bypassing the packet's own stored fields
    // entirely (defends against a struct-caching false positive).
    let recomputed_int = stable_hash(&candidate_int);
    let recomputed_float = stable_hash(&candidate_float);
    assert_eq!(recomputed_int, candidate_sha256_int);
    assert_eq!(recomputed_float, candidate_sha256_float);

    // Both packets must independently pass the REAL fail-closed validate(),
    // sign(), verify_signature() pipeline -- i.e. nothing in the existing
    // 18-probe fail-closed battery (T-02/W-CRO1 included) catches this.
    let validate_int_ok = pkt_int.validate().is_ok();
    let validate_float_ok = pkt_float.validate().is_ok();

    let key_int = SigningKey::from_bytes(&[91u8; 32]);
    let key_float = SigningKey::from_bytes(&[92u8; 32]);
    let mut trust = TrustStore::default();
    trust.insert("numcanon-signer-int", key_int.verifying_key().to_bytes()).unwrap();
    trust.insert("numcanon-signer-float", key_float.verifying_key().to_bytes()).unwrap();
    pkt_int.sign("numcanon-signer-int", &key_int).expect("sign() must succeed on int-encoded candidate packet");
    pkt_float.sign("numcanon-signer-float", &key_float).expect("sign() must succeed on float-encoded candidate packet");
    let verify_int_ok = pkt_int.verify_signature(&trust).is_ok();
    let verify_float_ok = pkt_float.verify_signature(&trust).is_ok();

    // --- Axis B: formula binding (typed EquivalentBalanceV1) — scoping ---
    // Same int-vs-float ambiguity attempted at the JSON-text level, but fed
    // through serde deserialization into the strongly-typed f64 field before
    // stable_hash ever sees it, to confirm this path is NOT vulnerable (it
    // is fully bounded, not merely untested).
    let text_int = r#"{
        "schema": "SCHEMA_PLACEHOLDER",
        "resin_facts_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "hardener_facts_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "resin_structure_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "hardener_structure_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "eew_g_per_eq": 100,
        "ahew_g_per_eq": 100,
        "resin_mass_g": 110,
        "hardener_mass_g": 25,
        "epoxide_equivalents": 1,
        "amine_hydrogen_equivalents": 1,
        "theoretical_hardener_phr": 22,
        "equivalent_ratio": 1,
        "total_mass_g": 135,
        "unit_provenance": {"mass": "g", "equivalent_weight": "g/eq structure-derived"},
        "authority_ceiling": "AUDIT_ONLY",
        "candidate_property_overrides_accepted": false,
        "ranking_eligible": false
    }"#
    .replace("SCHEMA_PLACEHOLDER", EQUIVALENT_BALANCE_SCHEMA);
    let text_float = r#"{
        "schema": "SCHEMA_PLACEHOLDER",
        "resin_facts_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "hardener_facts_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "resin_structure_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "hardener_structure_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "eew_g_per_eq": 100.0,
        "ahew_g_per_eq": 100.0,
        "resin_mass_g": 110.0,
        "hardener_mass_g": 25.0,
        "epoxide_equivalents": 1.0,
        "amine_hydrogen_equivalents": 1.0,
        "theoretical_hardener_phr": 22.0,
        "equivalent_ratio": 1.0,
        "total_mass_g": 135.0,
        "unit_provenance": {"mass": "g", "equivalent_weight": "g/eq structure-derived"},
        "authority_ceiling": "AUDIT_ONLY",
        "candidate_property_overrides_accepted": false,
        "ranking_eligible": false
    }"#
    .replace("SCHEMA_PLACEHOLDER", EQUIVALENT_BALANCE_SCHEMA);

    let bal_from_int: EquivalentBalanceV1 =
        serde_json::from_str(&text_int).expect("int-literal balance text must deserialize");
    let bal_from_float: EquivalentBalanceV1 =
        serde_json::from_str(&text_float).expect("float-literal balance text must deserialize");
    let formula_sha256_from_int = stable_hash(&serde_json::to_value(&bal_from_int).unwrap());
    let formula_sha256_from_float = stable_hash(&serde_json::to_value(&bal_from_float).unwrap());
    let formula_binding_immune = formula_sha256_from_int == formula_sha256_from_float;

    // --- Refutation criterion ------------------------------------------
    // The module's falsifiable hypothesis (docs/mission.md) is that
    // "candidate and formula binding prevents ambiguous or nonnumeric lab
    // packets." Refuted if two byte-different-but-semantically-identical
    // candidate encodings of the SAME real formulation produce two
    // different candidate_sha256 / packet_id values, each of which
    // independently validates, signs, and verifies -- i.e. two live,
    // fully-authenticated CRO packets exist for one real candidate.
    let refutation_criterion_observed = candidate_sha256_diverges
        && packet_id_diverges
        && validate_int_ok
        && validate_float_ok
        && verify_int_ok
        && verify_float_ok;
    let verdict = if refutation_criterion_observed {
        "CLAIM_REFUTED"
    } else {
        "CLAIM_SURVIVED"
    };

    let report = json!({
        "study_id": "cro-numeric-type-canonicalization-v1",
        "schema_under_test": CRO_PROTOCOL_PACKAGE_V2_SCHEMA,
        "draft_int_ok": draft_int_ok,
        "draft_float_ok": draft_float_ok,
        "candidate_sha256_int": candidate_sha256_int,
        "candidate_sha256_float": candidate_sha256_float,
        "candidate_sha256_diverges": candidate_sha256_diverges,
        "packet_id_int": packet_id_int,
        "packet_id_float": packet_id_float,
        "packet_id_diverges": packet_id_diverges,
        "independent_recompute_matches_stored": true,
        "validate_int_ok": validate_int_ok,
        "validate_float_ok": validate_float_ok,
        "verify_int_ok": verify_int_ok,
        "verify_float_ok": verify_float_ok,
        "formula_sha256_from_int": formula_sha256_from_int,
        "formula_sha256_from_float": formula_sha256_from_float,
        "formula_binding_immune_to_numeric_type": formula_binding_immune,
        "refutation_criterion_verbatim": "candidate and formula binding prevents ambiguous or nonnumeric lab packets",
        "refutation_criterion_observed": refutation_criterion_observed,
        "verdict": verdict,
    });

    println!("PROBE_JSON_BEGIN");
    println!("{}", serde_json::to_string(&report).unwrap());
    println!("PROBE_JSON_END");

    assert!(candidate_sha256_diverges, "expected candidate_sha256 to diverge on numeric-type encoding");
    assert!(validate_int_ok && validate_float_ok, "expected both packets to independently validate");
    assert!(verify_int_ok && verify_float_ok, "expected both packets to independently sign+verify");
    assert!(formula_binding_immune, "expected typed formula binding to be immune (scoping check)");
}
