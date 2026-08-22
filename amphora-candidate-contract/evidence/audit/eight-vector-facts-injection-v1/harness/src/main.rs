use amphora_engine::EnginePool;
use serde_json::{json, Value};
use std::collections::BTreeSet;

const REAL_SMILES: &str = "C1OC1"; // oxirane: real MW ~44.05, oxirane_ring_count=1, amine_H=0

const POISON_MW: f64 = 999999.0;
const POISON_EEW: f64 = 888888.0;
const POISON_AHEW: f64 = 777777.0;
const POISON_OXIRANE: u64 = 4242;
const POISON_AMINE: u64 = 4343;
const POISON_SHA: &str = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef";
const POISON_SMILES: &str = "POISONED-SMILES-C99Z-NOT-REAL";
const POISON_IDENTITY: &str = "POISONED-IDENTITY-C99Z-NOT-REAL";
const POISON_FORMULA: &str = "POISONED-FORMULA-C99Z";
const POISON_ONTOLOGY: &str = "POISONED-ONTOLOGY-C99Z";

fn poisoned_facts_obj() -> Value {
    json!({
        "schema": "amphora.molecule-facts.v1",
        "canonical_isomeric_smiles": POISON_SMILES,
        "structure_identity": POISON_IDENTITY,
        "canonical_structure_sha256": POISON_SHA,
        "formula": POISON_FORMULA,
        "average_molecular_weight_g_mol": POISON_MW,
        "oxirane_ring_count": POISON_OXIRANE,
        "reactive_amine_hydrogen_count": POISON_AMINE,
        "reactive_flags": {"has_oxirane": true, "has_reactive_amine_hydrogen": true, "dual_role": true},
        "ontology_version": POISON_ONTOLOGY,
        "toolkit_provenance": {
            "toolkit": "RDKit C++",
            "required_version": "2026.03.2",
            "detected_version": "2026.03.2",
            "exact_version_match": true
        }
    })
}

fn vector_payloads() -> Vec<(&'static str, &'static str, Value)> {
    let facts = poisoned_facts_obj();
    vec![
        (
            "V1_top_level_key",
            "attacker-supplied MW/EEW/AHEW/group-count/identity/whole-facts-struct as top-level sibling keys of candidate_id/candidate_type",
            json!({
                "candidate_id": "atk-v1-top-level",
                "candidate_type": "molecule",
                "molecule": {"smiles": REAL_SMILES},
                "average_molecular_weight_g_mol": POISON_MW,
                "eew_g_per_eq": POISON_EEW,
                "ahew_g_per_eq": POISON_AHEW,
                "oxirane_ring_count": POISON_OXIRANE,
                "reactive_amine_hydrogen_count": POISON_AMINE,
                "canonical_structure_sha256": POISON_SHA,
                "canonical_isomeric_smiles": POISON_SMILES,
                "structure_identity": POISON_IDENTITY,
                "molecule_facts_v1": facts.clone(),
                "normalization": {
                    "status": "NORMALIZED",
                    "molecule_facts_v1": facts.clone(),
                    "canonical_structure_hash": POISON_SHA,
                    "error": null,
                    "required_toolkit": "RDKit C++ 2026.03.2",
                    "structure_policy": "attacker-forged-should-be-overwritten"
                }
            }),
        ),
        (
            "V2_array_container",
            "attacker-supplied facts wrapped in JSON arrays at molecule.facts, top-level molecule_facts_v1, evidence_refs, and a synthetic equivalents array",
            json!({
                "candidate_id": "atk-v2-array",
                "candidate_type": "molecule",
                "molecule": {"smiles": REAL_SMILES, "facts": [facts.clone()]},
                "molecule_facts_v1": [facts.clone()],
                "evidence_refs": [{"molecule_facts_v1": facts.clone(), "eew_g_per_eq": POISON_EEW}],
                "equivalents": [{"eew_g_per_eq": POISON_EEW, "ahew_g_per_eq": POISON_AHEW, "canonical_structure_sha256": POISON_SHA}]
            }),
        ),
        (
            "V3_deep_nesting",
            "attacker-supplied facts nested 4-5 levels deep under molecule.provenance.host.facts and meta.a.b.c.d",
            json!({
                "candidate_id": "atk-v3-deep",
                "candidate_type": "molecule",
                "molecule": {
                    "smiles": REAL_SMILES,
                    "provenance": {"host": {"facts": {
                        "average_molecular_weight_g_mol": POISON_MW,
                        "oxirane_ring_count": POISON_OXIRANE
                    }}},
                    "normalization": {"molecule_facts_v1": facts.clone()}
                },
                "meta": {"a": {"b": {"c": {"d": {
                    "canonical_structure_sha256": POISON_SHA,
                    "eew_g_per_eq": POISON_EEW,
                    "ahew_g_per_eq": POISON_AHEW
                }}}}}
            }),
        ),
        (
            "V4_key_case_variant",
            "attacker-supplied facts using PascalCase/UPPERCASE variants of the real snake_case field names",
            json!({
                "candidate_id": "atk-v4-case",
                "candidate_type": "molecule",
                "molecule": {"smiles": REAL_SMILES},
                "Average_Molecular_Weight_G_Mol": POISON_MW,
                "EEW_G_PER_EQ": POISON_EEW,
                "Ahew_G_Per_Eq": POISON_AHEW,
                "Canonical_Structure_Sha256": POISON_SHA,
                "MOLECULE_FACTS_V1": facts.clone(),
                "Oxirane_Ring_Count": POISON_OXIRANE
            }),
        ),
        (
            "V5_alternate_key_name",
            "attacker-supplied facts under plausible alternate/abbreviated key names (mw, eew, ahew, group_count, structure_hash, identity)",
            json!({
                "candidate_id": "atk-v5-altkey",
                "candidate_type": "molecule",
                "molecule": {"smiles": REAL_SMILES, "mw": POISON_MW, "eew": POISON_EEW, "ahew": POISON_AHEW, "group_count": POISON_OXIRANE},
                "molecular_weight": POISON_MW,
                "epoxy_equiv_wt": POISON_EEW,
                "amine_h_equiv_wt": POISON_AHEW,
                "structure_hash": POISON_SHA,
                "identity": POISON_IDENTITY
            }),
        ),
        (
            "V6_semantic_alt_field",
            "attacker-supplied facts under semantically-equivalent alternate field names (declared/cro_measured/trusted/verified/counsel_confirmed prefixes)",
            json!({
                "candidate_id": "atk-v6-semalt",
                "candidate_type": "molecule",
                "molecule": {"smiles": REAL_SMILES},
                "declared_molecular_weight_g_mol": POISON_MW,
                "cro_measured_molecular_weight_g_mol": POISON_MW,
                "trusted_eew_g_per_eq": POISON_EEW,
                "trusted_ahew_g_per_eq": POISON_AHEW,
                "functional_group_count": POISON_OXIRANE,
                "verified_canonical_structure_sha256": POISON_SHA,
                "counsel_confirmed_structure_identity": POISON_IDENTITY
            }),
        ),
        (
            "V7_string_container",
            "attacker-supplied facts re-typed as JSON strings instead of native number/object types, including the whole forged struct serialized as one string blob",
            json!({
                "candidate_id": "atk-v7-string",
                "candidate_type": "molecule",
                "molecule": {"smiles": REAL_SMILES},
                "average_molecular_weight_g_mol": POISON_MW.to_string(),
                "eew_g_per_eq": POISON_EEW.to_string(),
                "ahew_g_per_eq": POISON_AHEW.to_string(),
                "oxirane_ring_count": POISON_OXIRANE.to_string(),
                "canonical_structure_sha256": POISON_SHA,
                "molecule_facts_v1": serde_json::to_string(&facts).unwrap()
            }),
        ),
        (
            "V8_unicode_homoglyph_key",
            "attacker-supplied facts under keys using Cyrillic homoglyph characters (U+0430 a, U+0435 e, U+043E o, U+0441 c) substituted for visually-identical Latin letters",
            json!({
                "candidate_id": "atk-v8-homoglyph",
                "candidate_type": "molecule",
                "molecule": {"smiles": REAL_SMILES},
                "\u{0430}verage_molecular_weight_g_mol": POISON_MW,
                "eew_g_per_\u{0435}q": POISON_EEW,
                "ahew_g_per_\u{0435}q": POISON_AHEW,
                "canoni\u{0441}al_structure_sha256": POISON_SHA,
                "m\u{043E}lecule_facts_v1": facts.clone()
            }),
        ),
    ]
}

fn poison_hits(value: &Value, path: String, out: &mut Vec<String>) {
    match value {
        Value::Object(map) => {
            for (k, v) in map {
                poison_hits(v, format!("{path}/{k}"), out);
            }
        }
        Value::Array(items) => {
            for (i, v) in items.iter().enumerate() {
                poison_hits(v, format!("{path}/{i}"), out);
            }
        }
        Value::Number(n) => {
            if let Some(f) = n.as_f64() {
                if (f - POISON_MW).abs() < 1e-6 {
                    out.push(format!("{path} == POISON_MW ({f})"));
                }
                if (f - POISON_EEW).abs() < 1e-6 {
                    out.push(format!("{path} == POISON_EEW ({f})"));
                }
                if (f - POISON_AHEW).abs() < 1e-6 {
                    out.push(format!("{path} == POISON_AHEW ({f})"));
                }
                if (f - POISON_OXIRANE as f64).abs() < 1e-9 {
                    out.push(format!("{path} == POISON_OXIRANE ({f})"));
                }
                if (f - POISON_AMINE as f64).abs() < 1e-9 {
                    out.push(format!("{path} == POISON_AMINE ({f})"));
                }
            }
        }
        Value::String(s) => {
            for (name, needle) in [
                ("POISON_SHA", POISON_SHA),
                ("POISON_SMILES", POISON_SMILES),
                ("POISON_IDENTITY", POISON_IDENTITY),
                ("POISON_FORMULA", POISON_FORMULA),
                ("POISON_ONTOLOGY", POISON_ONTOLOGY),
            ] {
                if s.contains(needle) {
                    out.push(format!("{path} contains {name} (\"{s}\")"));
                }
            }
        }
        _ => {}
    }
}

/// Deliberately-vulnerable mock consumer used ONLY as a positive control for
/// this harness's own detection logic. It simulates what a buggy candidate-
/// contract implementation would do: naively copy candidate-supplied
/// "average_molecular_weight_g_mol" straight into a property-results-shaped
/// output, bypassing host RDKit recomputation entirely.
fn naive_vulnerable_mock_consumer(candidate: &Value) -> Value {
    let leaked_mw = candidate
        .get("average_molecular_weight_g_mol")
        .cloned()
        .unwrap_or(Value::Null);
    json!({
        "property_results": {
            "molecular_weight_g_mol": leaked_mw
        }
    })
}

fn main() -> anyhow::Result<()> {
    let pool = EnginePool::new("/tmp/cc_probe_nonexistent_root", 1)?;

    // Clean control candidate: same real structure, zero injected keys.
    let control = json!({
        "candidate_id": "control-clean",
        "candidate_type": "molecule",
        "molecule": {"smiles": REAL_SMILES}
    });
    let control_result = pool.score_campaign_modules(
        &control,
        1,
        "cc-probe-control",
        &["amphora-molecule-property"],
    )?;
    let control_property = control_result["score_envelopes"]
        .as_array()
        .and_then(|rows| rows.iter().find(|r| r["module_id"] == "amphora-molecule-property"))
        .cloned()
        .unwrap_or(Value::Null);
    let control_property_results = control_property
        .pointer("/metrics/property_results")
        .cloned()
        .unwrap_or(Value::Null);
    let control_molecule_facts_v1 = control_result
        .pointer("/candidate/normalized_molecule/normalization/molecule_facts_v1")
        .cloned()
        .unwrap_or(Value::Null);

    let mut records = Vec::new();
    let mut byte_identical_property_results = BTreeSet::new();
    byte_identical_property_results.insert(serde_json::to_string(&control_property_results)?);

    for (vector_id, description, candidate) in vector_payloads() {
        let result = pool.score_campaign_modules(
            &candidate,
            1,
            &format!("cc-probe-{vector_id}"),
            &["amphora-molecule-property"],
        );
        let (status, property_results, whole_result_value, error) = match &result {
            Ok(v) => {
                let property = v["score_envelopes"]
                    .as_array()
                    .and_then(|rows| rows.iter().find(|r| r["module_id"] == "amphora-molecule-property"))
                    .cloned()
                    .unwrap_or(Value::Null);
                let pr = property
                    .pointer("/metrics/property_results")
                    .cloned()
                    .unwrap_or(Value::Null);
                ("ACCEPTED".to_string(), pr, v.clone(), None)
            }
            Err(e) => (
                "REJECTED".to_string(),
                Value::Null,
                Value::Null,
                Some(e.to_string()),
            ),
        };

        // Broad scan: the ENTIRE engine result, including the raw untyped
        // candidate echo-back at /candidate/normalized_molecule/* (this is
        // documented passthrough of the original candidate JSON for audit
        // purposes -- amphora-molecule-capabilities/src/lib.rs's
        // structure_text()/molecule() helpers, and every capability's
        // FeatureSnapshot, never read that subtree for facts). Included for
        // full disclosure, not as the decisive check.
        let mut hits_anywhere = Vec::new();
        if !whole_result_value.is_null() {
            poison_hits(&whole_result_value, String::new(), &mut hits_anywhere);
        }

        // Decisive scan #1: the actual typed host-normalization field the
        // runtime feeds to every molecule capability via FeatureSnapshot.
        let molecule_facts_v1 = whole_result_value
            .pointer("/candidate/normalized_molecule/normalization/molecule_facts_v1")
            .cloned()
            .unwrap_or(Value::Null);
        let mut typed_facts_hits = Vec::new();
        if !molecule_facts_v1.is_null() {
            poison_hits(&molecule_facts_v1, String::new(), &mut typed_facts_hits);
        }
        let molecule_facts_v1_matches_control =
            !molecule_facts_v1.is_null() && molecule_facts_v1 == control_molecule_facts_v1;

        // Decisive scan #2: the property capability's scored output, which
        // is built exclusively from the struct above (amphora-molecule-
        // capabilities/src/lib.rs property_result()/normalized_facts()).
        let mut typed_property_hits = Vec::new();
        if !property_results.is_null() {
            poison_hits(&property_results, String::new(), &mut typed_property_hits);
        }
        let property_results_matches_control = !property_results.is_null()
            && property_results == control_property_results;
        if !property_results.is_null() {
            byte_identical_property_results
                .insert(serde_json::to_string(&property_results)?);
        }
        let typed_field_leak =
            !typed_facts_hits.is_empty() || !typed_property_hits.is_empty();

        records.push(json!({
            "vector_id": vector_id,
            "description": description,
            "candidate_payload": candidate,
            "engine_call_status": status,
            "engine_call_error": error,
            "observed_property_results": property_results,
            "observed_molecule_facts_v1": molecule_facts_v1,
            "property_results_byte_identical_to_clean_control": property_results_matches_control,
            "molecule_facts_v1_byte_identical_to_clean_control": molecule_facts_v1_matches_control,
            "typed_field_poison_hits": {
                "in_molecule_facts_v1": typed_facts_hits,
                "in_property_results": typed_property_hits,
            },
            "typed_field_leak": typed_field_leak,
            "raw_untyped_candidate_echo_poison_hits_anywhere_in_whole_result": hits_anywhere,
            "raw_untyped_echo_hit_count": hits_anywhere.len(),
        }));
    }

    let any_typed_field_leak = records.iter().any(|r| r["typed_field_leak"] == json!(true));
    let all_property_results_byte_identical = byte_identical_property_results.len() == 1;
    let all_vectors_had_raw_echo_hits = records
        .iter()
        .all(|r| r["raw_untyped_echo_hit_count"].as_u64().unwrap_or(0) > 0);

    // --- positive control: deliberately-vulnerable mock consumer ----------
    let pc_candidate = json!({
        "candidate_id": "positive-control-mock",
        "candidate_type": "molecule",
        "molecule": {"smiles": REAL_SMILES},
        "average_molecular_weight_g_mol": POISON_MW
    });
    let mock_output = naive_vulnerable_mock_consumer(&pc_candidate);
    let mut mock_hits = Vec::new();
    poison_hits(&mock_output, String::new(), &mut mock_hits);
    let positive_control = json!({
        "planted_defect": "a mock consumer that naively copies candidate-supplied 'average_molecular_weight_g_mol' straight into a property_results-shaped output, bypassing host RDKit recomputation (the exact defect class this harness exists to catch)",
        "how_planted": "naive_vulnerable_mock_consumer() in this probe's own source reads candidate[\"average_molecular_weight_g_mol\"] (POISON_MW = 999999.0) and echoes it verbatim into output.property_results.molecular_weight_g_mol, instead of calling the real host RDKit molecule_facts() pipeline",
        "detected": !mock_hits.is_empty(),
        "evidence": format!("poison_hits() on the mock's own output: {mock_hits:?}"),
    });

    let out = json!({
        "schema": "amphora.candidate-contract.eight-vector-injection-probe.v1",
        "real_smiles_used": REAL_SMILES,
        "poison_constants": {
            "average_molecular_weight_g_mol": POISON_MW,
            "eew_g_per_eq": POISON_EEW,
            "ahew_g_per_eq": POISON_AHEW,
            "oxirane_ring_count": POISON_OXIRANE,
            "reactive_amine_hydrogen_count": POISON_AMINE,
            "canonical_structure_sha256": POISON_SHA,
            "canonical_isomeric_smiles": POISON_SMILES,
            "structure_identity": POISON_IDENTITY,
        },
        "control_clean_property_results": control_property_results,
        "control_clean_molecule_facts_v1": control_molecule_facts_v1,
        "vectors": records,
        "n_vectors": 8,
        "n_typed_field_leaks": records.iter().filter(|r| r["typed_field_leak"] == json!(true)).count(),
        "any_typed_field_leak": any_typed_field_leak,
        "all_property_results_byte_identical_across_all_8_vectors_and_control": all_property_results_byte_identical,
        "distinct_property_results_byte_forms_observed": byte_identical_property_results.len(),
        "all_vectors_had_raw_untyped_echo_hits": all_vectors_had_raw_echo_hits,
        "interpretation": "raw_untyped_candidate_echo_poison_hits are the attacker's payload surviving verbatim in the documented raw-candidate-echo passthrough at /candidate/normalized_molecule/* (original input preserved for audit; never read by any Capability::evaluate() as facts -- see amphora-molecule-capabilities normalized_facts(), which reads only features.values['molecule_facts_v1'], itself populated only from /normalization/molecule_facts_v1, a key amphora-engine's normalize_molecule() unconditionally overwrites). typed_field_leak is the decisive check: whether the poison reached molecule_facts_v1 (the host-normalized struct) or property_results (the scored capability output built exclusively from it).",
        "positive_control": positive_control,
    });
    println!("{}", serde_json::to_string_pretty(&out)?);
    Ok(())
}
