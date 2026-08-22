use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const MODULE_ID: &str = "amphora-sourceability-ehs";

fn sha256_hex(bytes: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(bytes);
    format!("{:x}", h.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "ehs-redchem-probe".into(),
        deterministic_seed: 20260816,
        lineage: Value::Null,
    }
}

/// Every content-level red-team-dossier axis
/// (`docs/mission.md` "Red-team dossier" section) that the module's own
/// checked test suite (`amphora-assurance-capabilities/tests/sourceability_ehs_phase0_kpi.rs`)
/// does NOT exercise. Dispatch-layer axes (wrong candidate_type, unknown
/// module_id, whitespace module_id) are already covered there and are
/// deliberately excluded here to avoid re-testing what already passes.
fn adversarial_cases() -> Vec<(&'static str, Value)> {
    vec![
        (
            "baseline_known_good",
            json!({
                "candidate_id": "primer-baseline",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}}
            }),
        ),
        (
            "malformed_chemistry_nonexistent_ingredient_id",
            json!({
                "candidate_id": "redchem-malformed-chemistry",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"not_a_real_ingredient_xyz123": 100.0}, "part_B": {"also_fake": 40.0}}
            }),
        ),
        (
            "mixture_dot_separated_smiles_fragment",
            json!({
                "candidate_id": "redchem-mixture-fragment",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0},
                    "part_B": {"polyamide": 65.0},
                    "smiles_fragment_hint": "CC1=CC=CC=C1.NCCN.[Na+].[Cl-]"
                }
            }),
        ),
        (
            "polymer_repeat_unit_notation",
            json!({
                "candidate_id": "redchem-polymer-repeat-unit",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba_oligomer": 100.0},
                    "part_B": {"polyamide": 65.0},
                    "polymer_repeat_unit_hint": "*OCC(O)COC1=CC=C(C=C1)C(C)(C)C1=CC=C(C=C1)OCC(O)CO*",
                    "degree_of_polymerization_n": 9999999
                }
            }),
        ),
        (
            "unit_ambiguity_conflicting_mass_units",
            json!({
                "candidate_id": "redchem-unit-ambiguity",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": {"mass_g": 100.0, "mass_lb": 100.0}},
                    "part_B": {"polyamide": {"mass_g": 65.0, "mass_kg": 65.0}}
                }
            }),
        ),
        (
            "zero_mass_ingredient",
            json!({
                "candidate_id": "redchem-zero-mass",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 0.0}, "part_B": {"polyamide": 0.0}}
            }),
        ),
        (
            "negative_mass_ingredient",
            json!({
                "candidate_id": "redchem-negative-mass",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": -100.0}, "part_B": {"polyamide": -65.0}}
            }),
        ),
        (
            "out_of_domain_non_coating_formulation",
            json!({
                "candidate_id": "redchem-out-of-domain",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"olive_oil": 100.0}, "part_B": {"vinegar": 65.0}}
            }),
        ),
        (
            "group_source_time_leakage_spoofed_split_group",
            json!({
                "candidate_id": "redchem-leakage",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}},
                "split_group": "TRAIN_FOLD_0",
                "source_id": "v5_epoch30_public_bom_sourceability_manifest.json#0"
            }),
        ),
        (
            "mutated_source_hash_reference",
            json!({
                "candidate_id": "redchem-mutated-source",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}},
                "evidence_refs": {
                    "cited_source": {
                        "path": "amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/epa_comptox.html",
                        "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
                    }
                }
            }),
        ),
        (
            "computed_value_mislabeled_as_measured",
            json!({
                "candidate_id": "redchem-computed-as-measured",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}},
                "evidence_refs": {
                    "eew": {"value": 182.5, "measured": true, "provenance": "computed_group_contribution"}
                }
            }),
        ),
        (
            "spoofed_identity_colliding_candidate_id",
            json!({
                "candidate_id": "primer-baseline",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgebf": 999.0}, "part_B": {"amidoamine": 1.0}}
            }),
        ),
        (
            "stripped_unknown_claim_locks",
            json!({
                "candidate_id": "redchem-claim-locks",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}},
                "claim_locks": {"totally_unrecognised_lock_xyz": false}
            }),
        ),
        (
            "authority_escalation_batch_release",
            json!({
                "candidate_id": "redchem-authority-escalation",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}},
                "evidence_refs": {"procurement": {"batch_release": true, "qualified": true}}
            }),
        ),
    ]
}

fn run() -> Value {
    let cap = AssuranceCapability::new(MODULE_ID).expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = context();

    let cases = adversarial_cases();
    let mut per_case = Vec::new();
    let mut baseline_result_json: Option<Value> = None;

    for (case_id, candidate_value) in &cases {
        let candidate = CandidateEnvelope::from_value(candidate_value.clone())
            .expect("candidate structurally parses (all cases are valid JSON + valid candidate_type/payload shape)");
        let outcome = cap.evaluate(&candidate, &features, &ctx);
        let (ok, result_json, error_msg) = match outcome {
            Ok(result) => (true, Some(serde_json::to_value(&result).unwrap()), None),
            Err(e) => (false, None, Some(e.to_string())),
        };

        if *case_id == "baseline_known_good" {
            baseline_result_json = result_json.clone();
        }

        let identical_to_baseline = match (&result_json, &baseline_result_json) {
            (Some(r), Some(b)) => r == b,
            _ => false,
        };

        let remains_explicit_evidence_gap = result_json.as_ref().map(|r| {
            r.get("status") == Some(&json!("FAILED_GATES"))
                && r.pointer("/gates/procurement_ready") == Some(&json!(false))
                && r.pointer("/gates/exact_grade_source_present") == Some(&json!(false))
                && r.pointer("/gates/current_document_present") == Some(&json!(false))
                && r.pointer("/gates/signed_declaration_present") == Some(&json!(false))
                && r.pointer("/metrics/sourceability_status") == Some(&json!("UNRESOLVED"))
        }).unwrap_or(false);

        per_case.push(json!({
            "case_id": case_id,
            "evaluate_ok": ok,
            "error": error_msg,
            "remains_explicit_evidence_gap": remains_explicit_evidence_gap,
            "byte_identical_to_baseline_result": identical_to_baseline,
            "result": result_json,
        }));
    }

    let n_cases = per_case.len();
    let n_ok = per_case.iter().filter(|c| c["evaluate_ok"] == json!(true)).count();
    let n_identical_to_baseline = per_case
        .iter()
        .filter(|c| c["byte_identical_to_baseline_result"] == json!(true))
        .count();
    let n_remains_gap = per_case
        .iter()
        .filter(|c| c["remains_explicit_evidence_gap"] == json!(true))
        .count();

    json!({
        "schema": "amphora.sourceability-ehs.audit.ehs-redchem.diagnostic.v1",
        "module_id": MODULE_ID,
        "n_cases": n_cases,
        "n_evaluate_ok": n_ok,
        "n_byte_identical_to_baseline": n_identical_to_baseline,
        "n_remains_explicit_evidence_gap": n_remains_gap,
        "all_content_variants_ok_and_byte_identical_to_baseline": n_ok == n_cases && n_identical_to_baseline == n_cases,
        "all_remain_explicit_evidence_gap": n_remains_gap == n_cases,
        "per_case": per_case,
    })
}

fn main() {
    let report = run();
    let bytes = serde_json::to_vec_pretty(&report).unwrap();
    println!("{}", String::from_utf8(bytes.clone()).unwrap());
    eprintln!("sha256={}", sha256_hex(&bytes));
}
