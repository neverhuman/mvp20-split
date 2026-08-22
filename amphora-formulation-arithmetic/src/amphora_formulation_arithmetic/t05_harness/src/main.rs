// T-05 / T2-05 adversarial harness for amphora-formulation-arithmetic.
//
// Drives the LIVE amphora-formulation-capabilities::EquivalentBalanceV1
// implementation (the mission.md-declared "live checked implementation" of
// this module) with inverted ratios, non-finite inputs, zero-group operands,
// role-inversion on dual-role molecules, and a candidate-supplied-constant
// injection attempt. Prints one canonical JSON report to stdout.
//
// This binary is a read-only probe: it does not modify any file in the repo.
// It links the real Rust structs/functions, not a re-implementation, so its
// observations are ground truth, not a simulation.

use amphora_formulation_capabilities::{EquivalentBalanceError, EquivalentBalanceV1};
use amphora_rdkit_ffi::{
    MoleculeFactsV1, ReactiveFlagsV1, ToolkitProvenanceV1, REACTIVE_ONTOLOGY_VERSION,
    REQUIRED_RDKIT_VERSION,
};
use serde_json::{json, Value};

fn genuine_facts(structure: &str, mass: f64, oxirane: u32, amine_h: u32) -> MoleculeFactsV1 {
    MoleculeFactsV1 {
        schema: "amphora.molecule-facts.v1".into(),
        canonical_isomeric_smiles: structure.into(),
        structure_identity: format!("smiles-sha256:{structure}"),
        canonical_structure_sha256: format!("sha256-of:{structure}"),
        formula: "C2H4".into(),
        average_molecular_weight_g_mol: mass,
        oxirane_ring_count: oxirane,
        reactive_amine_hydrogen_count: amine_h,
        reactive_flags: ReactiveFlagsV1 {
            has_oxirane: oxirane > 0,
            has_reactive_amine_hydrogen: amine_h > 0,
            dual_role: oxirane > 0 && amine_h > 0,
        },
        ontology_version: REACTIVE_ONTOLOGY_VERSION.into(),
        toolkit_provenance: ToolkitProvenanceV1 {
            toolkit: "RDKit C++".into(),
            required_version: REQUIRED_RDKIT_VERSION.into(),
            detected_version: REQUIRED_RDKIT_VERSION.into(),
            exact_version_match: true,
        },
    }
}

fn result_to_json(r: &Result<EquivalentBalanceV1, EquivalentBalanceError>) -> Value {
    match r {
        Ok(b) => json!({
            "outcome": "OK_SCALAR_RETURNED",
            "eew_g_per_eq": b.eew_g_per_eq,
            "ahew_g_per_eq": b.ahew_g_per_eq,
            "epoxide_equivalents_n_e": b.epoxide_equivalents,
            "amine_hydrogen_equivalents": b.amine_hydrogen_equivalents,
            "hardener_mass_g": b.hardener_mass_g,
            "theoretical_hardener_phr": b.theoretical_hardener_phr,
            "total_mass_g": b.total_mass_g,
            "candidate_property_overrides_accepted_flag": b.candidate_property_overrides_accepted,
        }),
        Err(e) => json!({
            "outcome": "ERR_FAILED_CLOSED",
            "error_variant": format!("{e:?}"),
        }),
    }
}

/// Independent front-door recompute of phr and n_e from the *returned*
/// struct's own host-derived fields only (no reuse of the function's
/// internal call graph), per directive: "check phr = 100*m_h/m_r and
/// n_e = m_r/EEW recompute from host facts only."
fn front_door_recompute_matches(b: &EquivalentBalanceV1) -> Value {
    let n_e_recompute = b.resin_mass_g / b.eew_g_per_eq;
    let phr_recompute = 100.0 * b.hardener_mass_g / b.resin_mass_g;
    json!({
        "n_e_recompute_from_resin_mass_and_eew": n_e_recompute,
        "n_e_matches_struct_epoxide_equivalents": n_e_recompute == b.epoxide_equivalents,
        "phr_recompute_from_masses": phr_recompute,
        "phr_matches_struct_theoretical_hardener_phr": phr_recompute == b.theoretical_hardener_phr,
    })
}

fn main() {
    let mut cases: Vec<Value> = Vec::new();

    // ---- Baseline sanity: genuine host facts, valid inputs ----
    let resin = genuine_facts("C1OC1c1ccc(cc1)C1OC1", 340.0, 2, 0); // DGEBA-like
    let hardener = genuine_facts("NCCNCCN", 103.0, 0, 5); // DETA-like
    let baseline = EquivalentBalanceV1::from_host_facts(&resin, &hardener, 100.0, 1.0);
    let baseline_recompute = if let Ok(b) = &baseline {
        front_door_recompute_matches(b)
    } else {
        json!(null)
    };
    cases.push(json!({
        "case_id": "BASELINE_VALID",
        "description": "genuine host facts, finite positive mass and ratio",
        "result": result_to_json(&baseline),
        "front_door_recompute": baseline_recompute,
    }));

    // ---- Axis: non-finite / invalid-quantity inputs ----
    let non_finite_mass = [f64::NAN, f64::INFINITY, f64::NEG_INFINITY, 0.0, -1.0];
    for (i, m) in non_finite_mass.iter().enumerate() {
        let r = EquivalentBalanceV1::from_host_facts(&resin, &hardener, *m, 1.0);
        cases.push(json!({
            "case_id": format!("NON_FINITE_MASS_{i}"),
            "description": format!("resin_mass_g = {m:?}"),
            "result": result_to_json(&r),
            "expected": "ERR_FAILED_CLOSED (InvalidQuantity)",
            "matches_expected": matches!(r, Err(EquivalentBalanceError::InvalidQuantity)),
        }));
    }
    let non_finite_ratio = [f64::NAN, f64::INFINITY, f64::NEG_INFINITY, 0.0, -1.0, -0.0001];
    for (i, ratio) in non_finite_ratio.iter().enumerate() {
        let r = EquivalentBalanceV1::from_host_facts(&resin, &hardener, 100.0, *ratio);
        cases.push(json!({
            "case_id": format!("NON_FINITE_OR_NONPOSITIVE_RATIO_{i}"),
            "description": format!("equivalent_ratio = {ratio:?}"),
            "result": result_to_json(&r),
            "expected": "ERR_FAILED_CLOSED (InvalidQuantity)",
            "matches_expected": matches!(r, Err(EquivalentBalanceError::InvalidQuantity)),
        }));
    }

    // ---- Axis: zero-group operands ----
    let no_oxirane = genuine_facts("CC", 20.0, 0, 0);
    let r = EquivalentBalanceV1::from_host_facts(&no_oxirane, &hardener, 100.0, 1.0);
    cases.push(json!({
        "case_id": "ZERO_GROUP_RESIN_NO_OXIRANE",
        "description": "resin has oxirane_ring_count = 0",
        "result": result_to_json(&r),
        "expected": "ERR_FAILED_CLOSED (NoOxirane)",
        "matches_expected": matches!(r, Err(EquivalentBalanceError::NoOxirane)),
    }));
    let no_amine_h = genuine_facts("CC", 20.0, 0, 0);
    let r = EquivalentBalanceV1::from_host_facts(&resin, &no_amine_h, 100.0, 1.0);
    cases.push(json!({
        "case_id": "ZERO_GROUP_HARDENER_NO_AMINE_H",
        "description": "hardener has reactive_amine_hydrogen_count = 0",
        "result": result_to_json(&r),
        "expected": "ERR_FAILED_CLOSED (NoReactiveAmineHydrogen)",
        "matches_expected": matches!(r, Err(EquivalentBalanceError::NoReactiveAmineHydrogen)),
    }));
    let both_zero = genuine_facts("CC", 20.0, 0, 0);
    let r = EquivalentBalanceV1::from_host_facts(&both_zero, &both_zero, 100.0, 1.0);
    cases.push(json!({
        "case_id": "ZERO_GROUP_BOTH",
        "description": "both molecules zero-group (no oxirane, no amine H)",
        "result": result_to_json(&r),
        "expected": "ERR_FAILED_CLOSED (NoOxirane, checked first)",
        "matches_expected": matches!(r, Err(EquivalentBalanceError::NoOxirane)),
    }));

    // ---- Axis: inverted ratio (reciprocal) — expected to be ACCEPTED,
    // since equivalent_ratio is a free positive stoichiometry parameter with
    // no independently-knowable "correct direction" inside pure arithmetic;
    // rejecting it would itself be a bug. Recorded to show behavior, not to
    // claim a defect. ----
    let ratio_normal = EquivalentBalanceV1::from_host_facts(&resin, &hardener, 100.0, 2.0);
    let ratio_reciprocal = EquivalentBalanceV1::from_host_facts(&resin, &hardener, 100.0, 0.5);
    let distinct = match (&ratio_normal, &ratio_reciprocal) {
        (Ok(a), Ok(b)) => a.theoretical_hardener_phr != b.theoretical_hardener_phr,
        _ => false,
    };
    cases.push(json!({
        "case_id": "INVERTED_RATIO_RECIPROCAL",
        "description": "ratio=2.0 vs its reciprocal ratio=0.5: both are finite positive scalars with no way for pure arithmetic to know which the caller 'meant'",
        "result_ratio_2_0": result_to_json(&ratio_normal),
        "result_ratio_0_5_reciprocal": result_to_json(&ratio_reciprocal),
        "both_accepted_as_distinct_valid_scalars": distinct,
        "note": "this is correct, intended behavior: equivalent_ratio is a caller-chosen stoichiometry input, not a value the function can validate the direction of. NOT counted as a refutation on its own.",
    }));

    // ---- Axis: role inversion on structurally ambiguous (dual-role)
    // molecules — the only kind of 'inversion' this function COULD in
    // principle detect and reject, since dual-role facts satisfy the
    // has-oxirane / has-amine-H checks for EITHER argument position. ----
    let dual_a = genuine_facts("C1OC1CCN", 150.0, 1, 2); // amphoteric: epoxide AND amine-H
    let dual_b = genuine_facts("C1OC1CCCN", 164.0, 1, 3); // amphoteric, different molecule
    let role_ab = EquivalentBalanceV1::from_host_facts(&dual_a, &dual_b, 100.0, 1.0);
    let role_ba = EquivalentBalanceV1::from_host_facts(&dual_b, &dual_a, 100.0, 1.0);
    let both_roles_accepted = role_ab.is_ok() && role_ba.is_ok();
    let produce_different_scalars = match (&role_ab, &role_ba) {
        (Ok(x), Ok(y)) => x.theoretical_hardener_phr != y.theoretical_hardener_phr,
        _ => false,
    };
    cases.push(json!({
        "case_id": "ROLE_INVERSION_DUAL_ROLE_MOLECULES",
        "description": "two structurally-amphoteric (dual_role=true) molecules, called as from_host_facts(A,B,..) then from_host_facts(B,A,..): the function has no check beyond raw group-count presence, so an inverted resin/hardener role assignment is silently accepted for ambiguous inputs rather than flagged",
        "result_A_as_resin_B_as_hardener": result_to_json(&role_ab),
        "result_B_as_resin_A_as_hardener_role_inverted": result_to_json(&role_ba),
        "both_role_assignments_accepted_ok": both_roles_accepted,
        "produce_different_scalars_silently": produce_different_scalars,
    }));

    // ---- CORE ATTACK: candidate-supplied constant injection. ----
    // MoleculeFactsV1 is a plain `pub` struct with `#[derive(Deserialize)]`
    // and no cryptographic/host-attestation field (no signature, no hash
    // chain back to an actual RDKit invocation). The ONLY gate inside
    // from_host_facts is a string/bool equality check against constants
    // (REACTIVE_ONTOLOGY_VERSION, REQUIRED_RDKIT_VERSION) that are public
    // and trivially reproducible by anyone. A fabricated fact record that
    // copies those public strings passes the gate and its
    // average_molecular_weight_g_mol / oxirane_ring_count / amine-H count —
    // none of which were ever computed by RDKit — flow straight into the
    // balance.
    let fabricated_json = json!({
        "schema": "amphora.molecule-facts.v1",
        "canonical_isomeric_smiles": "NOT_A_REAL_MOLECULE",
        "structure_identity": "smiles-sha256:NOT_A_REAL_MOLECULE",
        "canonical_structure_sha256": "sha256-of:NOT_A_REAL_MOLECULE",
        "formula": "C0H0",
        "average_molecular_weight_g_mol": 1.0,
        "oxirane_ring_count": 999,
        "reactive_amine_hydrogen_count": 0,
        "reactive_flags": {
            "has_oxirane": true,
            "has_reactive_amine_hydrogen": false,
            "dual_role": false
        },
        "ontology_version": REACTIVE_ONTOLOGY_VERSION,
        "toolkit_provenance": {
            "toolkit": "RDKit C++",
            "required_version": REQUIRED_RDKIT_VERSION,
            "detected_version": REQUIRED_RDKIT_VERSION,
            "exact_version_match": true
        }
    });
    let fabricated_str = serde_json::to_string(&fabricated_json).unwrap();
    let fabricated: MoleculeFactsV1 = serde_json::from_str(&fabricated_str)
        .expect("fabricated JSON deserializes cleanly into MoleculeFactsV1 — no provenance field rejects it");
    let attack_result = EquivalentBalanceV1::from_host_facts(&fabricated, &hardener, 100.0, 1.0);
    let injected_constant_entered_balance = match &attack_result {
        Ok(b) => b.eew_g_per_eq == 1.0 / 999.0,
        Err(_) => false,
    };
    cases.push(json!({
        "case_id": "CANDIDATE_SUPPLIED_CONSTANT_INJECTION",
        "description": "hand-fabricated MoleculeFactsV1 (never touched RDKit; average_molecular_weight_g_mol=1.0, oxirane_ring_count=999 chosen arbitrarily) deserialized from raw JSON using only the two PUBLIC constants REACTIVE_ONTOLOGY_VERSION and REQUIRED_RDKIT_VERSION, then passed as the resin argument to from_host_facts",
        "fabricated_json_deserialized_ok": true,
        "fabricated_facts_sha256_marker": "not_computed_by_any_toolkit",
        "result": result_to_json(&attack_result),
        "fabricated_eew_g_per_eq_expected_if_accepted": 1.0 / 999.0,
        "REFUTATION_OBSERVATION_injected_constant_entered_balance": injected_constant_entered_balance,
    }));

    // Also show the negative control: a fabricated fact record whose
    // toolkit_provenance strings do NOT match is correctly rejected — proving
    // the ontology/toolkit string check is real, just not sufficient to
    // establish genuine RDKit provenance (any attacker who reads the two
    // public constants defeats it).
    let mut wrong_toolkit_json = fabricated_json.clone();
    wrong_toolkit_json["toolkit_provenance"]["detected_version"] = json!("9999.99.9");
    let wrong_toolkit: MoleculeFactsV1 =
        serde_json::from_str(&serde_json::to_string(&wrong_toolkit_json).unwrap()).unwrap();
    let r = EquivalentBalanceV1::from_host_facts(&wrong_toolkit, &hardener, 100.0, 1.0);
    cases.push(json!({
        "case_id": "NEGATIVE_CONTROL_WRONG_TOOLKIT_STRING",
        "description": "same fabrication, but detected_version does not match the pinned public constant — this IS correctly rejected, showing the string-equality gate is real and this is not a trivially-broken function, only an insufficiently-authenticated one",
        "result": result_to_json(&r),
        "expected": "ERR_FAILED_CLOSED (Toolkit)",
        "matches_expected": matches!(r, Err(EquivalentBalanceError::Toolkit)),
    }));

    let refutation_criterion_text = "Any candidate-supplied constant enters the balance, or an inverted/non-finite case returns a scalar instead of failing closed.";
    let all_non_finite_and_zero_group_failed_closed = cases
        .iter()
        .filter(|c| {
            let id = c["case_id"].as_str().unwrap_or("");
            id.starts_with("NON_FINITE_") || id.starts_with("ZERO_GROUP_")
        })
        .all(|c| c["matches_expected"].as_bool().unwrap_or(false));

    let report = json!({
        "schema": "amphora.formulation-arithmetic.t05-equivalent-balance-attack.v1",
        "module": "amphora-formulation-arithmetic",
        "target_function": "amphora_formulation_capabilities::EquivalentBalanceV1::from_host_facts",
        "target_source_path": "amphora-formulation-capabilities/src/lib.rs",
        "directive_ref": {
            "doc": "AMPHORA-DIRECTIVE-2026-08-05",
            "section": "A.1",
            "item_id": "T2-05"
        },
        "refutation_criterion_verbatim": refutation_criterion_text,
        "refutation_observation_occurred": injected_constant_entered_balance,
        "non_finite_and_zero_group_axes_all_failed_closed": all_non_finite_and_zero_group_failed_closed,
        "cases": cases,
        "verdict": if injected_constant_entered_balance { "CLAIM_REFUTED" } else { "CLAIM_SURVIVED_PENDING_POSITIVE_CONTROL" },
    });
    println!("{}", serde_json::to_string_pretty(&report).unwrap());
}
