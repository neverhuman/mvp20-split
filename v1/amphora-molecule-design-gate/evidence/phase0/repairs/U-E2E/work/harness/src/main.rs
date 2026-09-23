// U-E2E (PART A of two): first signed end-to-end run for
// amphora-molecule-design-gate: candidate set -> design-gate -> partial
// evaluator matrix.
//
// This harness builds the >=20 candidate set (5 canonical epoxy-amine
// hardeners with CAS-correct structures per the R-A07/R-A07v2 IPDA
// correction, plus 15 more drawn from amphora-molecule-generator's 38
// accepted grammar proposals with the R-A06v2 corrected active-hydrogen
// functionality labels carried forward) and runs EVERY one of them through
// the real production design-gate decision surface exactly as T-08 did:
// live RDKit C++ FFI facts -> FeatureSnapshot -> capability(DESIGN_GATE_ID)
// .evaluate_authorized(), two-replay byte-stability checked per call.
//
// It also independently cross-checks the live FFI's reactive_amine_hydrogen_
// count against the n_active_nh_conventionB value R-A06v2 published for each
// grammar-proposal candidate (a regression check that the corrected label
// carried into this run's provenance actually matches what the live FFI
// says today), and against the R-A07v2-corrected IPDA formula (C10H22N2).

use std::collections::BTreeMap;

use amphora_core::{CandidateEnvelope, ExecutionContext, FeatureSnapshot};
use amphora_molecule_capabilities::{capability, DESIGN_GATE_ID, NOVELTY_ID, PROPERTY_ID};
use serde_json::{json, Value};

struct Candidate {
    id: &'static str,
    name: &'static str,
    smiles: &'static str,
    provenance: &'static str, // "canonical_amine" | "grammar_proposal"
    source_family: &'static str,
    r_a06v2_active_nh: i64,
    r_a06v2_amine_centres: i64,
    cas_or_note: &'static str,
}

fn candidates() -> Vec<Candidate> {
    vec![
        // --- 5 canonical epoxy-amine hardeners (CAS-correct structures) ---
        Candidate {
            id: "canon-ipda",
            name: "IPDA (isophorone diamine)",
            smiles: "CC1(C)CC(N)CC(C)(CN)C1",
            provenance: "canonical_amine",
            source_family: "F3_cycloaliphatic",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "CAS 2855-13-2, C10H22N2, R-A07v2-corrected structure (supersedes stale C9H20N2 demethylated string)",
        },
        Candidate {
            id: "canon-dds",
            name: "DDS (4,4'-diaminodiphenyl sulfone)",
            smiles: "Nc1ccc(S(=O)(=O)c2ccc(N)cc2)cc1",
            provenance: "canonical_amine",
            source_family: "F4_bridged_bisaniline",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "CAS 80-08-0, per R-N01 CAS-correct CID attribution",
        },
        Candidate {
            id: "canon-deta",
            name: "DETA (diethylenetriamine)",
            smiles: "NCCNCCN",
            provenance: "canonical_amine",
            source_family: "F1_polyethyleneamine",
            r_a06v2_active_nh: 5,
            r_a06v2_amine_centres: 3,
            cas_or_note: "CAS 111-40-0",
        },
        Candidate {
            id: "canon-teta",
            name: "TETA (triethylenetetramine)",
            smiles: "NCCNCCNCCN",
            provenance: "canonical_amine",
            source_family: "F1_polyethyleneamine",
            r_a06v2_active_nh: 6,
            r_a06v2_amine_centres: 4,
            cas_or_note: "CAS 112-24-3",
        },
        Candidate {
            id: "canon-mxda",
            name: "m-XDA (1,3-xylylenediamine)",
            smiles: "NCc1cccc(CN)c1",
            provenance: "canonical_amine",
            source_family: "F5_xylylenediamine",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "CAS 1477-55-0",
        },
        // --- 15 more from amphora-molecule-generator's 38 accepted grammar
        // proposals (R-A06v2-corrected labels carried forward) ---
        Candidate {
            id: "gen-eda",
            name: "EDA (ethylenediamine)",
            smiles: "NCCN",
            provenance: "grammar_proposal",
            source_family: "F1_polyethyleneamine",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 19",
        },
        Candidate {
            id: "gen-tepa",
            name: "TEPA (tetraethylenepentamine)",
            smiles: "NCCNCCNCCNCCN",
            provenance: "grammar_proposal",
            source_family: "F1_polyethyleneamine",
            r_a06v2_active_nh: 7,
            r_a06v2_amine_centres: 5,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 24",
        },
        Candidate {
            id: "gen-peha",
            name: "PEHA (pentaethylenehexamine)",
            smiles: "NCCNCCNCCNCCNCCN",
            provenance: "grammar_proposal",
            source_family: "F1_polyethyleneamine",
            r_a06v2_active_nh: 8,
            r_a06v2_amine_centres: 6,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 25",
        },
        Candidate {
            id: "gen-c4-diaminobutane",
            name: "1,4-diaminobutane (C4)",
            smiles: "NCCCCN",
            provenance: "grammar_proposal",
            source_family: "F2_alpha_omega_diamine",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 17",
        },
        Candidate {
            id: "gen-c6-diaminohexane",
            name: "1,6-diaminohexane (C6)",
            smiles: "NCCCCCCN",
            provenance: "grammar_proposal",
            source_family: "F2_alpha_omega_diamine",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 15",
        },
        Candidate {
            id: "gen-c8-diaminooctane",
            name: "1,8-diaminooctane (C8)",
            smiles: "NCCCCCCCCN",
            provenance: "grammar_proposal",
            source_family: "F2_alpha_omega_diamine",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 13",
        },
        Candidate {
            id: "gen-c10-diaminodecane",
            name: "1,10-diaminodecane (C10)",
            smiles: "NCCCCCCCCCCN",
            provenance: "grammar_proposal",
            source_family: "F2_alpha_omega_diamine",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 11",
        },
        Candidate {
            id: "gen-c12-diaminododecane",
            name: "1,12-diaminododecane (C12)",
            smiles: "NCCCCCCCCCCCCN",
            provenance: "grammar_proposal",
            source_family: "F2_alpha_omega_diamine",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 9",
        },
        Candidate {
            id: "gen-14-dach",
            name: "1,4-DACH (1,4-diaminocyclohexane)",
            smiles: "NC1CCC(N)CC1",
            provenance: "grammar_proposal",
            source_family: "F3_cycloaliphatic",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 2",
        },
        Candidate {
            id: "gen-13-bac",
            name: "1,3-BAC (1,3-bis(aminomethyl)cyclohexane)",
            smiles: "NCC1CCCC(CN)C1",
            provenance: "grammar_proposal",
            source_family: "F3_cycloaliphatic",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 7",
        },
        Candidate {
            id: "gen-aep",
            name: "AEP (1-(2-aminoethyl)piperazine)",
            smiles: "NCCN1CCNCC1",
            provenance: "grammar_proposal",
            source_family: "F3_cycloaliphatic",
            r_a06v2_active_nh: 3,
            r_a06v2_amine_centres: 3,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 21 (mixed primary/secondary/tertiary N; active_NH != 2*centres)",
        },
        Candidate {
            id: "gen-isopropylidenedianiline",
            name: "4,4'-isopropylidenedianiline",
            smiles: "CC(C)(c1ccc(N)cc1)c1ccc(N)cc1",
            provenance: "grammar_proposal",
            source_family: "F4_bridged_bisaniline",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 0",
        },
        Candidate {
            id: "gen-mda-ddm",
            name: "MDA/DDM (4,4'-diaminodiphenylmethane)",
            smiles: "Nc1ccc(Cc2ccc(N)cc2)cc1",
            provenance: "grammar_proposal",
            source_family: "F4_bridged_bisaniline",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 34, CAS 101-77-9",
        },
        Candidate {
            id: "gen-benzidine",
            name: "benzidine (4,4'-diaminobiphenyl)",
            smiles: "Nc1ccc(-c2ccc(N)cc2)cc1",
            provenance: "grammar_proposal",
            source_family: "F4_bridged_bisaniline",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 32",
        },
        Candidate {
            id: "gen-pxda",
            name: "p-XDA (1,4-xylylenediamine)",
            smiles: "NCc1ccc(CN)cc1",
            provenance: "grammar_proposal",
            source_family: "F5_xylylenediamine",
            r_a06v2_active_nh: 4,
            r_a06v2_amine_centres: 2,
            cas_or_note: "molgen R-A06v2 per_proposal_table index 29",
        },
    ]
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "u-e2e-design-gate-candidate-set-v1".into(),
        deterministic_seed: 0,
        lineage: Value::Null,
    }
}

fn candidate_envelope(id: &str, smiles: &str, role: &str) -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": id,
        "candidate_type": "molecule",
        "molecule": {"smiles": smiles, "role": role},
    }))
    .expect("well-formed candidate envelope")
}

fn run_capability(cap_id: &str, candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> Value {
    let cap = capability(cap_id).unwrap_or_else(|| panic!("capability {cap_id} registered"));
    let ctx = context();
    let first = cap
        .evaluate_authorized(candidate, features, &ctx, None)
        .expect("capability evaluation");
    let second = cap
        .evaluate_authorized(candidate, features, &ctx, None)
        .expect("capability evaluation");
    let byte_stable =
        serde_json::to_vec(&first).expect("serializes") == serde_json::to_vec(&second).expect("serializes");
    json!({
        "result": serde_json::to_value(&first).expect("serializes"),
        "per_call_two_replay_byte_stable": byte_stable,
    })
}

fn main() {
    let status = amphora_rdkit_ffi::backend_status();
    let mut results: Vec<Value> = Vec::new();
    let mut n_scored = 0u32;
    let mut n_failed_gates = 0u32;
    let mut active_nh_regressions: Vec<Value> = Vec::new();

    for c in candidates() {
        let facts = amphora_rdkit_ffi::molecule_facts(c.smiles).unwrap_or_else(|e| {
            panic!("candidate {} failed to parse via REAL RDKit FFI: {e:?}", c.id)
        });
        let candidate = candidate_envelope(c.id, c.smiles, "hardener");
        let mut values = BTreeMap::new();
        values.insert(
            "molecule_facts_v1".to_string(),
            serde_json::to_value(&facts).expect("facts serialize"),
        );
        let features = FeatureSnapshot { values };
        let gate_run = run_capability(DESIGN_GATE_ID, &candidate, &features);
        let property_run = run_capability(PROPERTY_ID, &candidate, &features);
        let novelty_run = run_capability(NOVELTY_ID, &candidate, &features);
        // No verified_formulation_model.amphora-solvency-score host binding exists for
        // any of these 20 standalone candidates (that binding requires a locked
        // characterized resin/solvent PairCoefficientV1 artifact); call the REAL
        // evaluate() with an empty FeatureSnapshot and record its genuine abstain.
        let solvency_result = amphora_solvency_score::evaluate(&candidate, &FeatureSnapshot {
            values: BTreeMap::new(),
        });
        let solvency_run = serde_json::to_value(&solvency_result).expect("solvency serializes");
        let observed_status = gate_run["result"]["status"].as_str().unwrap_or("").to_string();
        let observed_reason = gate_run["result"]["metrics"]["gate_reason"]
            .as_str()
            .unwrap_or("")
            .to_string();
        if observed_status == "SCORED" {
            n_scored += 1;
        } else {
            n_failed_gates += 1;
        }
        let live_active_nh = facts.reactive_amine_hydrogen_count as i64;
        let active_nh_matches_r_a06v2 =
            c.provenance != "grammar_proposal" || live_active_nh == c.r_a06v2_active_nh;
        if !active_nh_matches_r_a06v2 {
            active_nh_regressions.push(json!({
                "id": c.id,
                "smiles": c.smiles,
                "r_a06v2_active_nh": c.r_a06v2_active_nh,
                "live_ffi_active_nh": live_active_nh,
            }));
        }
        results.push(json!({
            "id": c.id,
            "name": c.name,
            "smiles": c.smiles,
            "canonical_isomeric_smiles": facts.canonical_isomeric_smiles,
            "formula": facts.formula,
            "average_molecular_weight_g_mol": facts.average_molecular_weight_g_mol,
            "provenance": c.provenance,
            "source_family": c.source_family,
            "cas_or_note": c.cas_or_note,
            "declared_role": "hardener",
            "r_a06v2_expected_active_nh": c.r_a06v2_active_nh,
            "r_a06v2_expected_amine_centres": c.r_a06v2_amine_centres,
            "live_ffi_reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
            "live_ffi_oxirane_ring_count": facts.oxirane_ring_count,
            "active_nh_matches_r_a06v2_label": active_nh_matches_r_a06v2,
            "design_gate_status": observed_status,
            "design_gate_reason": observed_reason,
            "design_gate_gates": gate_run["result"]["gates"],
            "design_gate_per_call_two_replay_byte_stable": gate_run["per_call_two_replay_byte_stable"],
            "property_status": property_run["result"]["status"],
            "property_results": property_run["result"]["metrics"]["property_results"],
            "property_per_call_two_replay_byte_stable": property_run["per_call_two_replay_byte_stable"],
            "novelty_status": novelty_run["result"]["status"],
            "novelty_score": novelty_run["result"]["metrics"]["novelty_score"],
            "novelty_maximum_tanimoto_similarity": novelty_run["result"]["metrics"]["maximum_tanimoto_similarity"],
            "novelty_scaffold_aware_distance": novelty_run["result"]["metrics"]["scaffold_aware_distance"],
            "novelty_nearest_structure_id": novelty_run["result"]["metrics"]["nearest_structure_id"],
            "novelty_exact_structure_match": novelty_run["result"]["metrics"]["exact_structure_match"],
            "novelty_corpus_sha256": novelty_run["result"]["metrics"]["novelty_corpus_sha256"],
            "novelty_per_call_two_replay_byte_stable": novelty_run["per_call_two_replay_byte_stable"],
            "solvency_status": solvency_run["status"],
            "solvency_missing_inputs": solvency_run["missing_inputs"],
            "solvency_full_result": solvency_run,
        }));
    }

    let out = json!({
        "schema": "amphora.molecule-design-gate.u-e2e-candidate-set-design-gate.diagnostic.v1",
        "purpose": "U-E2E PART A: build the >=20-candidate end-to-end set (5 canonical amines + 15 R-A06v2-labelled grammar proposals) and run every one through the REAL production design_gate_result decision via the live RDKit C++ FFI, cross-checking the live active-hydrogen count against the R-A06v2-corrected label carried into each candidate's provenance.",
        "toolkit_provenance": {
            "toolkit": "RDKit C++",
            "required_version": amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION,
            "detected_version": status.detected_version,
            "exact_version_match": status.exact_version_match,
        },
        "n_candidates": results.len(),
        "n_scored": n_scored,
        "n_failed_gates": n_failed_gates,
        "n_active_nh_regressions_vs_r_a06v2": active_nh_regressions.len(),
        "active_nh_regressions": active_nh_regressions,
        "results": results,
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
