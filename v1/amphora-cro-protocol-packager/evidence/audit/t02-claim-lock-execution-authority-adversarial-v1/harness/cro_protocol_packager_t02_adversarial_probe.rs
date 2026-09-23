//! T-02 / T2-02 adversarial probe for amphora-cro-protocol-packager.
//!
//! Live-runtime attack against the REAL compiled CroProtocolPackageV2 (draft,
//! validate, sign, verify_signature) in amphora-assurance-capabilities/src/lib.rs.
//! Not a Python re-implementation of the check logic.
//!
//! Attack surface (campaign item T-02 + founder directive T2-02, section A.1):
//!   (a) execution_authorized -> true
//!   (b) strip AND null each of the 8 REQUIRED_CRO_CLAIM_LOCKS in turn
//!   (c) mutate a signed CroProtocolPackageV2 by one byte (DSSE payload bytes)
//!   (d) inject a packet-authored performance/decision threshold
//! plus an 8-alternate-encoding injection harness (same taxonomy as the
//! amphora-candidate-contract T-01 eight-vector-facts-injection probe) run
//! against BOTH the claim-lock path (claim_locks map) and the
//! execution_authority_locked path (execution_authorized scalar).

use std::collections::BTreeMap;

use amphora_assurance_capabilities::{CroProtocolPackageV2, CRO_PROTOCOL_PACKAGE_V2_SCHEMA};
use amphora_core::TrustStore;
use amphora_formulation_capabilities::{EquivalentBalanceV1, EQUIVALENT_BALANCE_SCHEMA};
use base64::engine::general_purpose::STANDARD as B64;
use base64::Engine;
use ed25519_dalek::SigningKey;
use serde_json::{json, Value};

const REQUIRED_CRO_CLAIM_LOCKS: [&str; 8] = [
    "NO_EXECUTION_AUTHORITY",
    "NO_PROCUREMENT_AUTHORITY",
    "NO_SAFETY_CLAIM",
    "NO_SYNTHESIS_CLAIM",
    "NO_PERFORMANCE_CLAIM",
    "NO_QUALIFICATION_CLAIM",
    "NO_RANKING_AUTHORITY",
    "UNMADE_DIGITAL_PROPOSAL",
];

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

fn baseline_packet() -> CroProtocolPackageV2 {
    let candidate = json!({"resin": "DGEBA", "hardener": "TETA"});
    CroProtocolPackageV2::draft(
        "t02-probe-campaign",
        &candidate,
        balance(100.0, 25.0),
        "BLIND-T02-000".into(),
    )
    .expect("baseline draft")
}

fn signed_baseline() -> (CroProtocolPackageV2, TrustStore, &'static str) {
    let mut p = baseline_packet();
    let key = SigningKey::from_bytes(&[201; 32]);
    let mut trust = TrustStore::default();
    trust
        .insert("t02-signer", key.verifying_key().to_bytes())
        .unwrap();
    p.sign("t02-signer", &key).unwrap();
    (p, trust, "t02-signer")
}

#[test]
fn t02_adversarial_probe() {
    let mut probes: Vec<Value> = Vec::new();
    let mut n_slipped_through = 0_usize;

    // ---------------------------------------------------------------
    // (a) execution_authorized -> true
    // ---------------------------------------------------------------
    {
        let mut p = baseline_packet();
        p.execution_authorized = true;
        let validate_err = p.validate().is_err();
        if !validate_err {
            n_slipped_through += 1;
        }
        probes.push(json!({
            "group": "directive_a_execution_authorized_true",
            "probe": "execution_authorized_flipped_true",
            "path": "execution_authority_locked",
            "fail_closed": validate_err,
        }));
    }

    // ---------------------------------------------------------------
    // (b) strip AND null each of the 8 required claim locks, in turn
    // ---------------------------------------------------------------
    for lock in REQUIRED_CRO_CLAIM_LOCKS {
        // strip (remove key entirely)
        let mut p = baseline_packet();
        p.claim_locks.remove(lock);
        let ok = p.validate().is_err();
        if !ok {
            n_slipped_through += 1;
        }
        probes.push(json!({
            "group": "directive_b_strip_or_null_claim_locks",
            "probe": format!("stripped_{lock}"),
            "path": "claim_lock",
            "lock": lock,
            "mutation": "removed_from_map",
            "fail_closed": ok,
        }));

        // null (set value false)
        let mut p = baseline_packet();
        p.claim_locks.insert(lock.into(), false);
        let ok = p.validate().is_err();
        if !ok {
            n_slipped_through += 1;
        }
        probes.push(json!({
            "group": "directive_b_strip_or_null_claim_locks",
            "probe": format!("nulled_{lock}"),
            "path": "claim_lock",
            "lock": lock,
            "mutation": "value_set_false",
            "fail_closed": ok,
        }));
    }

    // ---------------------------------------------------------------
    // (c) mutate a signed CroProtocolPackageV2 by one byte
    //     (flip one bit inside the DSSE payload bytes -- the exact bytes
    //     verify_dsse Ed25519-verifies and CroProtocolPackageV2::verify_signature
    //     re-derives from the current struct via unsigned_bytes())
    // ---------------------------------------------------------------
    {
        let (mut p, trust, _signer) = signed_baseline();
        // sanity: unmutated signed packet verifies
        let control_ok = p.verify_signature(&trust).is_ok();

        let sig = p.signature.clone().expect("signed");
        let mut payload_bytes = B64.decode(sig.payload.as_bytes()).expect("valid b64 payload");
        payload_bytes[0] ^= 0x01; // flip one bit -> one byte differs
        let mut tampered_sig = sig.clone();
        tampered_sig.payload = B64.encode(payload_bytes);
        p.signature = Some(tampered_sig);

        let verify_err = p.verify_signature(&trust).is_err();
        if !verify_err {
            n_slipped_through += 1;
        }
        probes.push(json!({
            "group": "directive_c_one_byte_mutation",
            "probe": "signed_packet_payload_one_byte_flip",
            "path": "signature",
            "control_unmutated_signature_verifies": control_ok,
            "fail_closed": verify_err,
        }));
    }

    // ---------------------------------------------------------------
    // (d) inject a packet-authored performance/decision threshold
    //     with a format-valid but content-UNDERIVED protocol_lock_sha256
    // ---------------------------------------------------------------
    {
        let mut p = baseline_packet();
        p.locked_numeric_thresholds
            .insert("attacker_pass_fail_yield_strength_min_mpa".into(), 9999.0);
        // 64 lowercase hex chars, format-valid, but NOT the hash of anything --
        // arbitrary attacker-chosen "lock" value never derived from the
        // threshold content it claims to bind.
        p.protocol_lock_sha256 = Some("a".repeat(64));
        // A real packet author (or an attacker holding the signing key)
        // recomputes packet_id after finalizing content, exactly as
        // CroProtocolPackageV2::draft() itself does -- packet_id is a
        // self-consistency hash over the packet's own content, not an
        // external authorization check, so recomputing it is not a defense
        // by itself.
        p.packet_id = p.computed_packet_id().expect("recompute packet_id");

        let validate_ok = p.validate().is_ok();
        let key = SigningKey::from_bytes(&[202; 32]);
        let mut trust = TrustStore::default();
        trust
            .insert("t02-threshold-signer", key.verifying_key().to_bytes())
            .unwrap();
        let sign_ok = p.sign("t02-threshold-signer", &key).is_ok();
        let verify_ok = sign_ok && p.verify_signature(&trust).is_ok();

        let accepted = validate_ok && sign_ok && verify_ok;
        if accepted {
            n_slipped_through += 1;
        }

        // Control: same construction, but with protocol_lock_sha256 left
        // absent while locked_numeric_thresholds is non-empty -- this MUST
        // be rejected by validate()'s Binding arm, proving the harness can
        // detect a genuine binding-shape defect and isn't just vacuously
        // green.
        let mut p_ctrl = baseline_packet();
        p_ctrl
            .locked_numeric_thresholds
            .insert("attacker_pass_fail_yield_strength_min_mpa".into(), 9999.0);
        p_ctrl.protocol_lock_sha256 = None;
        p_ctrl.packet_id = p_ctrl.computed_packet_id().expect("recompute packet_id");
        let ctrl_validate_ok = p_ctrl.validate().is_ok();

        probes.push(json!({
            "group": "directive_d_packet_authored_threshold",
            "probe": "attacker_threshold_with_undereived_protocol_lock_hash",
            "path": "locked_numeric_thresholds/protocol_lock_sha256",
            "injected_threshold_key": "attacker_pass_fail_yield_strength_min_mpa",
            "injected_threshold_value": 9999.0,
            "protocol_lock_sha256_used": "a".repeat(64),
            "protocol_lock_sha256_is_content_derived": false,
            "packet_id_recomputed_after_mutation": true,
            "validate_ok": validate_ok,
            "sign_ok": sign_ok,
            "verify_signature_ok": verify_ok,
            "packet_authored_threshold_accepted": accepted,
            "fail_closed": !accepted,
            "positive_control_missing_lock_hash_rejected": !ctrl_validate_ok,
        }));
    }

    // ---------------------------------------------------------------
    // 8-alternate-encoding injection harness, run against BOTH the
    // claim-lock path and the execution_authority_locked path.
    // ---------------------------------------------------------------
    let base_value = || serde_json::to_value(baseline_packet()).unwrap();

    struct Vector {
        id: &'static str,
        description: &'static str,
        apply_claim: fn(Value) -> Value,
        apply_exec: fn(Value) -> Value,
    }

    fn obj_insert(mut v: Value, key: &str, val: Value) -> Value {
        v.as_object_mut().unwrap().insert(key.into(), val);
        v
    }

    let vectors: Vec<Vector> = vec![
        Vector {
            id: "V1_top_level_key",
            description: "add a rogue top-level sibling key alongside the real field",
            apply_claim: |v| obj_insert(v, "claim_locks_override", json!({"NO_EXECUTION_AUTHORITY": false})),
            apply_exec: |v| obj_insert(v, "execution_authorized_override", json!(true)),
        },
        Vector {
            id: "V2_array_container",
            description: "wrap the target value in an array container",
            apply_claim: |mut v| {
                v["claim_locks"] = json!([{"NO_EXECUTION_AUTHORITY": false}]);
                v
            },
            apply_exec: |mut v| {
                v["execution_authorized"] = json!([true]);
                v
            },
        },
        Vector {
            id: "V3_deep_nesting",
            description: "bury an override several levels deep in an opaque sibling value",
            apply_claim: |v| obj_insert(
                v,
                "candidate_binding_shadow",
                json!({"a": {"b": {"c": {"claim_locks": {"NO_EXECUTION_AUTHORITY": false}}}}}),
            ),
            apply_exec: |v| obj_insert(
                v,
                "candidate_binding_shadow",
                json!({"a": {"b": {"c": {"execution_authorized": true}}}}),
            ),
        },
        Vector {
            id: "V4_key_case_variant",
            description: "lower/mixed-case spelling of the real key",
            apply_claim: |mut v| {
                v["claim_locks"]
                    .as_object_mut()
                    .unwrap()
                    .remove("NO_EXECUTION_AUTHORITY");
                v["claim_locks"]
                    .as_object_mut()
                    .unwrap()
                    .insert("no_execution_authority".into(), json!(true));
                v
            },
            apply_exec: |v| obj_insert(v, "Execution_Authorized", json!(true)),
        },
        Vector {
            id: "V5_alternate_key_name",
            description: "a differently-named synonym key",
            apply_claim: |mut v| {
                v["claim_locks"]
                    .as_object_mut()
                    .unwrap()
                    .remove("NO_EXECUTION_AUTHORITY");
                v["claim_locks"]
                    .as_object_mut()
                    .unwrap()
                    .insert("EXECUTION_AUTHORITY_GRANTED".into(), json!(true));
                v
            },
            apply_exec: |v| obj_insert(v, "execution_granted", json!(true)),
        },
        Vector {
            id: "V6_semantic_alt_field",
            description: "a semantically-equivalent alternate field name",
            apply_claim: |v| obj_insert(v, "no_execution_authority_confirmed", json!(true)),
            apply_exec: |v| obj_insert(v, "authorized", json!(true)),
        },
        Vector {
            id: "V7_string_container",
            description: "encode the target value as a JSON string blob instead of its native type",
            apply_claim: |mut v| {
                v["claim_locks"] = json!(
                    "{\"NO_EXECUTION_AUTHORITY\":false,\"NO_PROCUREMENT_AUTHORITY\":true,\"NO_SAFETY_CLAIM\":true,\"NO_SYNTHESIS_CLAIM\":true,\"NO_PERFORMANCE_CLAIM\":true,\"NO_QUALIFICATION_CLAIM\":true,\"NO_RANKING_AUTHORITY\":true,\"UNMADE_DIGITAL_PROPOSAL\":true}"
                );
                v
            },
            apply_exec: |mut v| {
                v["execution_authorized"] = json!("true");
                v
            },
        },
        Vector {
            id: "V8_unicode_homoglyph_key",
            description: "Unicode-homoglyph spelling of the real key (Greek Omicron for Latin O)",
            apply_claim: |mut v| {
                v["claim_locks"]
                    .as_object_mut()
                    .unwrap()
                    .remove("NO_EXECUTION_AUTHORITY");
                // "N\u{039F}_EXECUTI\u{039F}N_AUTH\u{039F}RITY" -- Greek capital omicron (Ο) swapped for Latin O
                v["claim_locks"]
                    .as_object_mut()
                    .unwrap()
                    .insert("N\u{039F}_EXECUTI\u{039F}N_AUTH\u{039F}RITY".into(), json!(true));
                v
            },
            apply_exec: |v| obj_insert(v, "executi\u{039F}n_authorized", json!(true)),
        },
    ];

    let mut n_evaded = 0_usize;
    let mut n_detected_leak = 0_usize;
    let mut encoding_table: Vec<Value> = Vec::new();

    for vector in &vectors {
        for (path_name, apply) in [
            ("claim_lock", vector.apply_claim),
            ("execution_authority_locked", vector.apply_exec),
        ] {
            let mutated = apply(base_value());
            let parsed: Result<CroProtocolPackageV2, _> =
                serde_json::from_value(mutated.clone());
            let (deserialize_ok, leaked) = match parsed {
                Err(_) => (false, false),
                Ok(pkt) => {
                    let bad_state = pkt.execution_authorized
                        || REQUIRED_CRO_CLAIM_LOCKS
                            .iter()
                            .any(|l| pkt.claim_locks.get(*l) != Some(&true))
                        || pkt.claim_locks.values().any(|v| !v);
                    let validate_ok = pkt.validate().is_ok();
                    // "leaked" = a bad-state packet that ALSO passes validate() --
                    // i.e. the poisoned value actually reached and survived the
                    // typed enforcement gate.
                    (true, bad_state && validate_ok)
                }
            };
            let evaded = !leaked;
            if evaded {
                n_evaded += 1;
            } else {
                n_detected_leak += 1;
                n_slipped_through += 1;
            }
            encoding_table.push(json!({
                "vector_id": vector.id,
                "description": vector.description,
                "path": path_name,
                "deserialize_ok": deserialize_ok,
                "leak_detected": leaked,
                "result": if evaded {
                    "EVADED (poisoned encoding never produced a valid, bad-state CroProtocolPackageV2)"
                } else {
                    "DETECTED_LEAK (poisoned encoding produced a bad-state package that PASSED validate() -- CLAIM_REFUTED trigger)"
                },
            }));
        }
    }

    let schema_sanity = CroProtocolPackageV2::draft(
        "sanity",
        &json!({"x": 1}),
        balance(50.0, 12.5),
        "BLIND-SANITY".into(),
    )
    .map(|p| p.schema == CRO_PROTOCOL_PACKAGE_V2_SCHEMA)
    .unwrap_or(false);

    let report = json!({
        "schema_sanity_draft_ok": schema_sanity,
        "n_directive_probes": probes.len(),
        "n_encoding_vectors": vectors.len(),
        "n_encoding_path_combinations": encoding_table.len(),
        "n_evaded": n_evaded,
        "n_detected_leak": n_detected_leak,
        "n_slipped_through_total": n_slipped_through,
        "directive_probes": probes,
        "encoding_table": encoding_table,
    });

    println!("PROBE_JSON_BEGIN");
    println!("{}", serde_json::to_string(&report).unwrap());
    println!("PROBE_JSON_END");
}
