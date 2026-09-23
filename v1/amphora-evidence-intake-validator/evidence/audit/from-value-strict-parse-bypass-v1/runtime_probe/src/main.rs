//! LIVE Rust differential probe: does `CandidateEnvelope::from_value` (the
//! constructor used by the real scoring entrypoint `amphora-engine::execute`,
//! which is what feeds `evaluate_evidence_intake`/`host_receipt_valid`) carry
//! the same structural protections as `CandidateEnvelope::from_bytes` /
//! `parse_json_strict` (duplicate-key rejection, MAX_JSON_DEPTH, MAX_COLLECTION_ENTRIES)?
//!
//! Links the real amphora-core crate. No randomness, no clock, no filesystem
//! writes. Emits one deterministic JSON object to stdout.

use amphora_core::{canonicalize, parse_json_strict, stable_hash, CandidateEnvelope, MAX_JSON_DEPTH};
use serde_json::{json, Value};

fn sha256_hex(bytes: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    let mut d = Sha256::new();
    d.update(bytes);
    format!("{:x}", d.finalize())
}

fn evidence_candidate(id: &str, payload: Value) -> Value {
    json!({
        "candidate_id": id,
        "candidate_type": "evidence_package",
        "evidence_refs": { "evidence_package": payload },
    })
}

fn deep_array(depth: usize) -> String {
    format!("{}0{}", "[".repeat(depth), "]".repeat(depth))
}

fn main() {
    let mut report = serde_json::Map::new();

    // ---- G0: sanity replay of amphora-core's own committed unit-test facts ----
    let dup_key = br#"{"candidate_id":"x","candidate_id":"y","candidate_type":"evidence_package","evidence_refs":{"evidence_package":{}}}"#;
    let g0_dup_rejected = parse_json_strict(dup_key).is_err();

    let deep = deep_array(MAX_JSON_DEPTH + 1);
    let g0_depth_rejected = parse_json_strict(deep.as_bytes()).is_err();

    let compact =
        br#"{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"}}"#.to_vec();
    let spaced =
        br#"{ "molecule":{"smiles":"C"}, "candidate_type":"molecule", "candidate_id":"x" }"#
            .to_vec();
    let env_compact = CandidateEnvelope::from_bytes(&compact).expect("compact parses");
    let env_spaced = CandidateEnvelope::from_bytes(&spaced).expect("spaced parses");
    let g0_contract_hash_invariant =
        env_compact.contract_hash_v1() == env_spaced.contract_hash_v1();
    let g0_original_bytes_hash_sensitive =
        env_compact.original_bytes_sha256() != env_spaced.original_bytes_sha256();

    let g0_pass = g0_dup_rejected
        && g0_depth_rejected
        && g0_contract_hash_invariant
        && g0_original_bytes_hash_sensitive;

    // ---- G1: original_bytes_sha256 vs contract_hash_v1 coincidence on the
    //          from_value() constructor over a diverse corpus ----
    let corpus: Vec<(&str, Value)> = vec![
        (
            "phase0-kpi-primer-lab",
            evidence_candidate(
                "phase0-kpi-primer-lab",
                json!({"measurement": "baseline primer lab", "value": 12.4, "unit": "mil"}),
            ),
        ),
        (
            "marine-salt-spray-iso9227",
            evidence_candidate(
                "marine-salt-spray-iso9227",
                json!({"standard": "ISO 9227", "hours": 720, "creep_mm": 1.3}),
            ),
        ),
        (
            "pull-off-adhesion-iso4624",
            evidence_candidate(
                "pull-off-adhesion-iso4624",
                json!({"standard": "ISO 4624", "mpa": 4.9, "failure_mode": "adhesive"}),
            ),
        ),
        (
            "dft-magnetic-gauge-iso2808",
            evidence_candidate(
                "dft-magnetic-gauge-iso2808",
                json!({"standard": "ISO 2808", "microns": [180, 195, 201]}),
            ),
        ),
        (
            "nested-mixed-types",
            evidence_candidate(
                "nested-mixed-types",
                json!({"z": 1, "a": {"nested": [1,2,3], "flag": true, "n": null}, "m": "text"}),
            ),
        ),
    ];

    let mut g1_rows = Vec::new();
    let mut g1_coincidences = 0usize;
    for (id, value) in &corpus {
        let env = CandidateEnvelope::from_value(value.clone()).expect("from_value builds");
        let coincide = env.original_bytes_sha256() == env.contract_hash_v1();
        if coincide {
            g1_coincidences += 1;
        }
        g1_rows.push(json!({
            "candidate_id": id,
            "contract_hash_v1": env.contract_hash_v1(),
            "original_bytes_sha256": env.original_bytes_sha256(),
            "coincide": coincide,
        }));
    }
    let g1_n = corpus.len();
    let g1_pass = g1_coincidences == g1_n;

    // Same corpus, but this time serialize each Value with a DELIBERATELY
    // non-canonical key order + extra whitespace, feed through from_bytes, and
    // confirm original_bytes_sha256 genuinely diverges from contract_hash_v1
    // there -- proving the two-hash separation is real and load-bearing on the
    // from_bytes path, and ONLY collapses on from_value.
    let mut g1b_rows = Vec::new();
    let mut g1b_divergences = 0usize;
    for (id, value) in &corpus {
        let reordered = format!(
            "{{ \"evidence_refs\": {}, \"candidate_type\": \"evidence_package\",  \"candidate_id\": {} }}",
            serde_json::to_string_pretty(&value["evidence_refs"]).unwrap(),
            serde_json::to_string(&value["candidate_id"]).unwrap(),
        );
        let env_b = CandidateEnvelope::from_bytes(reordered.as_bytes())
            .expect("reordered still strict-parses");
        let diverges = env_b.original_bytes_sha256() != env_b.contract_hash_v1();
        if diverges {
            g1b_divergences += 1;
        }
        g1b_rows.push(json!({
            "candidate_id": id,
            "diverges_on_from_bytes": diverges,
        }));
    }
    let g1b_pass = g1b_divergences == g1_n;

    // ---- G2: MAX_JSON_DEPTH / MAX_COLLECTION_ENTRIES budget bypass via from_value ----
    let bomb_depth = MAX_JSON_DEPTH + 40;
    let bomb_text = deep_array(bomb_depth);
    let bomb_evidence_bytes =
        format!(r#"{{"candidate_id":"depth-bomb","candidate_type":"evidence_package","evidence_refs":{{"evidence_package":{{"payload":{bomb_text}}}}}}}"#);
    let g2_from_bytes_rejects_depth_bomb =
        parse_json_strict(bomb_evidence_bytes.as_bytes()).is_err();

    // Same content, but the caller already holds a `Value` (as amphora-engine's
    // execute() always does -- see static citation) via an ordinary,
    // budget-free parse.
    let bomb_value: Value =
        serde_json::from_str(&bomb_evidence_bytes).expect("plain serde_json has no depth cap");
    let g2_from_value_accepts_depth_bomb =
        CandidateEnvelope::from_value(bomb_value.clone()).is_ok();

    let big_n = 150_000usize;
    let big_array: Vec<Value> = (0..big_n).map(Value::from).collect();
    let big_value = evidence_candidate("entry-bomb", json!({"rows": big_array}));
    let big_bytes = serde_json::to_vec(&big_value).unwrap();
    let g2_from_bytes_rejects_entry_bomb = parse_json_strict(&big_bytes).is_err();
    let g2_from_value_accepts_entry_bomb =
        CandidateEnvelope::from_value(big_value.clone()).is_ok();

    let g2_pass = g2_from_bytes_rejects_depth_bomb
        && g2_from_value_accepts_depth_bomb
        && g2_from_bytes_rejects_entry_bomb
        && g2_from_value_accepts_entry_bomb;

    // Confirm the accepted depth-bomb/entry-bomb envelopes produce ordinary,
    // well-formed canonical hashes (i.e. they are not merely "Ok but inert" --
    // they carry a real package_sha256-shaped binding an evaluator would use).
    let bomb_env = CandidateEnvelope::from_value(bomb_value).ok();
    let big_env = CandidateEnvelope::from_value(big_value).ok();
    let g2_bomb_hash_len_64 = bomb_env
        .as_ref()
        .map(|e| e.contract_hash_v1().len() == 64)
        .unwrap_or(false);
    let g2_big_hash_len_64 = big_env
        .as_ref()
        .map(|e| e.contract_hash_v1().len() == 64)
        .unwrap_or(false);

    // ---- cross-check: canonicalize+stable_hash directly, confirming the
    //      from_value original_bytes_sha256 identity is a mathematical fact
    //      (sha256(canonical bytes) computed twice), not an artifact of this probe ----
    let sample = &corpus[0].1;
    let direct_stable_hash = stable_hash(sample);
    let direct_canonical_bytes = serde_json::to_vec(&canonicalize(sample)).unwrap();
    let direct_sha_of_canonical = sha256_hex(&direct_canonical_bytes);
    let g_math_identity_confirmed = direct_stable_hash == direct_sha_of_canonical;

    report.insert("schema".into(), json!("amphora.evidence-intake-validator.from-value-strict-parse-bypass-probe.v1"));
    report.insert("live_rust".into(), json!(true));
    report.insert("crate_under_test".into(), json!("amphora-core"));
    report.insert(
        "gates".into(),
        json!({
            "g0_sanity_replay_of_shipped_unit_tests": g0_pass,
            "g1_from_value_original_bytes_hash_always_coincides_with_contract_hash": g1_pass,
            "g1b_from_bytes_original_bytes_hash_genuinely_diverges": g1b_pass,
            "g2_from_value_bypasses_depth_and_entry_budget": g2_pass,
        }),
    );
    report.insert(
        "results".into(),
        json!({
            "g0_dup_key_rejected_by_parse_json_strict": g0_dup_rejected,
            "g0_depth_rejected_by_parse_json_strict": g0_depth_rejected,
            "g0_contract_hash_v1_invariant_across_reencoding": g0_contract_hash_invariant,
            "g0_original_bytes_sha256_sensitive_to_reencoding_on_from_bytes": g0_original_bytes_hash_sensitive,
            "g1_corpus_n": g1_n,
            "g1_coincidences": g1_coincidences,
            "g1_rows": g1_rows,
            "g1b_divergences": g1b_divergences,
            "g1b_rows": g1b_rows,
            "max_json_depth": MAX_JSON_DEPTH,
            "bomb_depth_probed": bomb_depth,
            "g2_from_bytes_rejects_depth_bomb": g2_from_bytes_rejects_depth_bomb,
            "g2_from_value_accepts_depth_bomb": g2_from_value_accepts_depth_bomb,
            "big_array_entries_probed": big_n,
            "g2_from_bytes_rejects_entry_bomb": g2_from_bytes_rejects_entry_bomb,
            "g2_from_value_accepts_entry_bomb": g2_from_value_accepts_entry_bomb,
            "g2_bomb_hash_len_64": g2_bomb_hash_len_64,
            "g2_big_hash_len_64": g2_big_hash_len_64,
            "math_identity_confirmed": g_math_identity_confirmed,
        }),
    );
    report.insert(
        "all_gates_passed".into(),
        json!(g0_pass && g1_pass && g1b_pass && g2_pass && g_math_identity_confirmed),
    );

    println!("{}", serde_json::to_string(&Value::Object(report)).unwrap());
}
