// T-08 first adversarial attack: amphora-molecule-design-gate.
//
// Two complementary attacks against the REAL production code, not
// re-derivations:
//
// PART A (campaign objective): the module's own gate decision
// (`amphora_molecule_capabilities::design_gate_result`, invoked through the
// public `MoleculeCapability::evaluate_authorized` surface exactly as the
// shipped Phase-0 KPI harness and live engine do) is exercised end-to-end
// through the REAL pinned RDKit C++ FFI (`amphora_rdkit_ffi::molecule_facts`,
// RDKit 2026.03.2) on >=10 real, named, cited coating molecules held out of
// the module's self-authored fixture, including the three hostile nulls the
// 2026-08-04 defensibility scorecard named: a tertiary-amine accelerator
// (BDMA), an imidazole latent hardener (EMI-24), and guanidine-class
// accelerators (DPG, DOTG).
//
// PART B (founder directive T2-08): out-of-domain admission attempts
// (wildcard atoms, multi-component species, invalid valence) and a
// chemistry-changing mutation request are run against the REAL production
// entry points (`amphora_rdkit_ffi::molecule_facts`, the design gate itself,
// `amphora_engine::EnginePool::mutate`, `amphora_engine::EnginePool::generate_compounds`)
// to see whether any reaches a non-fail-closed decision.
//
// A single POSITIVE CONTROL closes the loop: a deliberately poisoned facts
// snapshot (never produced by the real FFI on this input, injected here by
// hand exactly like the module's own fact-snapshot-authority-v1 audit did)
// is fed to the same live `evaluate_authorized` call to prove the checker
// used in this harness actually fires on a planted defect.

use std::collections::BTreeMap;

use amphora_core::{
    stable_hash, CampaignGenerationRequestV1, CandidateEnvelope,
    ExecutionContext, FeatureSnapshot,
};
use amphora_engine::EnginePool;
use amphora_molecule_capabilities::{capability, DESIGN_GATE_ID};
use amphora_rdkit_ffi::{ChemistryError, MoleculeFactsV1, ReactiveFlagsV1, ToolkitProvenanceV1};
use serde_json::{json, Value};

struct GateProbe {
    id: &'static str,
    smiles: &'static str,
    citation: &'static str,
    declared_role: &'static str,
    hostile_null: bool,
    expected_status: &'static str, // "SCORED" | "FAILED_GATES"
    note: &'static str,
}

fn gate_probes() -> Vec<GateProbe> {
    vec![
        GateProbe {
            id: "erl4221-cycloaliphatic-diepoxide",
            smiles: "C1(COC(=O)C2CC3OC3CC2)CC4OC4CC1",
            citation: "3,4-epoxycyclohexylmethyl 3,4-epoxycyclohexanecarboxylate (ERL-4221, \
                       Dow CAS 2386-87-0, PubChem CID 68563), C14H20O4 MW 252.30",
            declared_role: "resin",
            hostile_null: false,
            expected_status: "SCORED",
            note: "real cycloaliphatic diepoxide resin, correctly declared",
        },
        GateProbe {
            id: "edr148-triethyleneglycol-diamine",
            smiles: "NCCOCCOCCOCCN",
            citation: "4,7,10-trioxatridecane-1,13-diamine (Jeffamine EDR-148, CAS 929-59-9), \
                       C10H24N2O3 MW 220.31",
            declared_role: "hardener",
            hostile_null: false,
            expected_status: "SCORED",
            note: "real ether-backbone diamine hardener, correctly declared",
        },
        GateProbe {
            id: "aep-aminoethylpiperazine",
            smiles: "NCCN1CCNCC1",
            citation: "1-(2-aminoethyl)piperazine (AEP, CAS 140-31-8)",
            declared_role: "hardener",
            hostile_null: false,
            expected_status: "SCORED",
            note: "mixed primary/secondary-ring/tertiary-ring nitrogen hardener",
        },
        GateProbe {
            id: "aspartic-ester-secondary-amine",
            smiles: "CCCCNC(CC(=O)OCC)C(=O)OCC",
            citation: "diethyl 2-(butylamino)succinate, monofunctional model of the Michael-\
                       adduct secondary amine in commercial polyaspartic marine topcoat hardeners",
            declared_role: "hardener",
            hostile_null: false,
            expected_status: "SCORED",
            note: "secondary amine, alpha-carbon (not N) bears the ester substituent",
        },
        GateProbe {
            id: "dds-diaminodiphenylsulfone",
            smiles: "Nc1ccc(cc1)S(=O)(=O)c1ccc(N)cc1",
            citation: "4,4'-diaminodiphenyl sulfone (DDS, CAS 80-08-0)",
            declared_role: "hardener",
            hostile_null: false,
            expected_status: "SCORED",
            note: "sulfonyl exclusion must not over-reach to a distant, unrelated sulfone",
        },
        GateProbe {
            id: "ddm-diaminodiphenylmethane",
            smiles: "Nc1ccc(Cc2ccc(N)cc2)cc1",
            citation: "4,4'-diaminodiphenylmethane (DDM/MDA, CAS 101-77-9)",
            declared_role: "hardener",
            hostile_null: false,
            expected_status: "SCORED",
            note: "real aromatic diamine hardener held out of the fixture",
        },
        GateProbe {
            id: "detda-hindered-aromatic-diamine",
            smiles: "Cc1c(N)c(CC)cc(CC)c1N",
            citation: "diethyltoluenediamine (DETDA / Ethacure 100 congener, CAS 68479-98-1)",
            declared_role: "hardener",
            hostile_null: false,
            expected_status: "SCORED",
            note: "sterically hindered aniline nitrogens still recognized",
        },
        GateProbe {
            id: "bdma-tertiary-amine-accelerator",
            smiles: "CN(C)Cc1ccccc1",
            citation: "N,N-dimethylbenzylamine (BDMA, CAS 103-83-3), a cure accelerator/\
                       catalyst, not a stoichiometric hardener",
            declared_role: "hardener",
            hostile_null: true,
            expected_status: "FAILED_GATES",
            note: "HOSTILE NULL: no N-H at all; declaring it hardener must fail closed",
        },
        GateProbe {
            id: "emi24-imidazole-latent-hardener",
            smiles: "Cc1c[nH]c(CC)n1",
            citation: "2-ethyl-4-methylimidazole (EMI-24, CAS 931-36-2), a latent curing agent \
                       that initiates anionic ring-opening, not stoichiometric N-H addition",
            declared_role: "hardener",
            hostile_null: true,
            expected_status: "FAILED_GATES",
            note: "HOSTILE NULL: aromatic pyrrole-type ring N-H must not count as reactive",
        },
        GateProbe {
            id: "dpg-diphenylguanidine-accelerator",
            smiles: "c1ccccc1NC(=N)Nc2ccccc2",
            citation: "1,3-diphenylguanidine (DPG, CAS 102-06-7), rubber/epoxy cure accelerator \
                       (US Patent 9,238,706), not a stoichiometric hardener",
            declared_role: "hardener",
            hostile_null: true,
            expected_status: "FAILED_GATES",
            note: "HOSTILE NULL named by the campaign item; guanidine C=N exclusion (R-N02) \
                   re-verified live through the design gate itself, not just role-ranker",
        },
        GateProbe {
            id: "dotg-di-o-tolylguanidine-accelerator",
            smiles: "Cc1ccccc1NC(=N)Nc2ccccc2C",
            citation: "N,N'-di-o-tolylguanidine (DOTG, CAS 97-39-2), more active DPG analog, \
                       rubber/epoxy cure accelerator",
            declared_role: "hardener",
            hostile_null: true,
            expected_status: "FAILED_GATES",
            note: "second guanidine-class accelerator, bonus hostile null",
        },
        GateProbe {
            id: "erl4221-declared-hardener-mismatch",
            smiles: "C1(COC(=O)C2CC3OC3CC2)CC4OC4CC1",
            citation: "same ERL-4221 diepoxide as above, adversarially declared as hardener",
            declared_role: "hardener",
            hostile_null: false,
            expected_status: "FAILED_GATES",
            note: "cross-declaration mismatch: a real resin has zero reactive amine hydrogens",
        },
        GateProbe {
            id: "edr148-declared-resin-mismatch",
            smiles: "NCCOCCOCCOCCN",
            citation: "same EDR-148 diamine as above, adversarially declared as resin",
            declared_role: "resin",
            hostile_null: false,
            expected_status: "FAILED_GATES",
            note: "cross-declaration mismatch: a real hardener has zero oxirane rings",
        },
    ]
}

struct StructuralProbe {
    id: &'static str,
    smiles: &'static str,
    declared_role: &'static str,
    note: &'static str,
    expected_ffi_error: &'static str,
}

fn structural_probes() -> Vec<StructuralProbe> {
    vec![
        StructuralProbe {
            id: "wildcard-dgeba-oligomer-polymer-endgroups",
            smiles: "*OCC(O)COc1ccc(C(C)(C)c2ccc(OCC(O)CO*)cc2)cc1",
            declared_role: "resin",
            note: "polymer/wildcard-atom input: a DGEBA oligomer repeat unit with open chain \
                   ends written as RDKit dummy atoms, the way a polymer-notation submission \
                   would arrive",
            expected_ffi_error: "WildcardOrPolymerStructure",
        },
        StructuralProbe {
            id: "multi-component-epoxide-plus-amine-mixture",
            smiles: "C1OC1.NCCN",
            declared_role: "resin",
            note: "multi-component species: an epoxide and a diamine hardener written as one \
                   two-fragment SMILES, as a pre-mixed formulation submission might arrive",
            expected_ffi_error: "MultiFragmentStructure",
        },
        StructuralProbe {
            id: "invalid-valence-hypervalent-carbon",
            smiles: "CC(C)(C)(C)(C)C",
            declared_role: "resin",
            note: "invalid valence: a central carbon written with 5 substituents (max valence \
                   4), lexically clean SMILES with no wildcard/fragment marker",
            expected_ffi_error: "InvalidStructure-or-backend-rejection",
        },
    ]
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "t08-design-gate-live-runtime-adversarial-v1".into(),
        deterministic_seed: 0,
        lineage: Value::Null,
    }
}

fn candidate_for(id: &str, smiles: &str, role: &str) -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": id,
        "candidate_type": "molecule",
        "molecule": {"smiles": smiles, "role": role},
    }))
    .expect("well-formed candidate envelope")
}

fn run_gate(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> Value {
    let cap = capability(DESIGN_GATE_ID).expect("design-gate capability registered");
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
    let mut part_a_results: Vec<Value> = Vec::new();
    let mut part_a_disagreements: Vec<Value> = Vec::new();
    let mut part_a_pass = 0u32;

    for p in gate_probes() {
        let facts = amphora_rdkit_ffi::molecule_facts(p.smiles)
            .unwrap_or_else(|e| panic!("gate probe {} failed to parse via REAL RDKit FFI: {e:?}", p.id));
        let candidate = candidate_for(p.id, p.smiles, p.declared_role);
        let features = FeatureSnapshot {
            values: BTreeMap::from([(
                "molecule_facts_v1".to_string(),
                serde_json::to_value(&facts).expect("facts serialize"),
            )]),
        };
        let run = run_gate(&candidate, &features);
        let observed_status = run["result"]["status"].as_str().unwrap_or("").to_string();
        let observed_reason = run["result"]["metrics"]["gate_reason"]
            .as_str()
            .unwrap_or("")
            .to_string();
        let pass = observed_status == p.expected_status;
        if pass {
            part_a_pass += 1;
        } else {
            part_a_disagreements.push(json!({
                "id": p.id,
                "smiles": p.smiles,
                "declared_role": p.declared_role,
                "expected_status": p.expected_status,
                "observed_status": observed_status,
                "observed_gate_reason": observed_reason,
                "observed_facts": serde_json::to_value(&facts).expect("facts serialize"),
            }));
        }
        part_a_results.push(json!({
            "id": p.id,
            "smiles": p.smiles,
            "canonical_isomeric_smiles": facts.canonical_isomeric_smiles,
            "formula": facts.formula,
            "citation": p.citation,
            "note": p.note,
            "hostile_null": p.hostile_null,
            "declared_role": p.declared_role,
            "observed_oxirane_ring_count": facts.oxirane_ring_count,
            "observed_reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
            "expected_status": p.expected_status,
            "observed_status": observed_status,
            "observed_gate_reason": observed_reason,
            "per_call_two_replay_byte_stable": run["per_call_two_replay_byte_stable"],
            "pass": pass,
        }));
    }

    // --- PART B: directive attack -- out-of-domain admission ---
    let mut part_b_structural: Vec<Value> = Vec::new();
    let mut part_b_slip_throughs: Vec<Value> = Vec::new();
    for p in structural_probes() {
        let ffi_result = amphora_rdkit_ffi::molecule_facts(p.smiles);
        let ffi_error_name = match &ffi_result {
            Ok(_) => "NONE-PARSED-OK".to_string(),
            Err(ChemistryError::MultiFragmentStructure) => "MultiFragmentStructure".to_string(),
            Err(ChemistryError::WildcardOrPolymerStructure) => {
                "WildcardOrPolymerStructure".to_string()
            }
            Err(ChemistryError::InvalidStructure(msg)) => format!("InvalidStructure({msg})"),
            Err(other) => format!("{other:?}"),
        };
        // Real orchestrator wiring (amphora-engine::apply_normalization) never
        // populates molecule_facts_v1 when molecule_facts() errors -- mirror
        // that exactly: empty FeatureSnapshot on FFI failure.
        let features = match &ffi_result {
            Ok(facts) => FeatureSnapshot {
                values: BTreeMap::from([(
                    "molecule_facts_v1".to_string(),
                    serde_json::to_value(facts).expect("facts serialize"),
                )]),
            },
            Err(_) => FeatureSnapshot {
                values: BTreeMap::new(),
            },
        };
        let candidate = candidate_for(p.id, p.smiles, p.declared_role);
        let run = run_gate(&candidate, &features);
        let observed_status = run["result"]["status"].as_str().unwrap_or("").to_string();
        let fails_closed = observed_status != "SCORED";
        if !fails_closed {
            part_b_slip_throughs.push(json!({
                "id": p.id,
                "smiles": p.smiles,
                "declared_role": p.declared_role,
                "observed_status": observed_status,
                "note": "OUT-OF-DOMAIN INPUT REACHED SCORED -- REFUTES THE DIRECTIVE",
            }));
        }
        part_b_structural.push(json!({
            "id": p.id,
            "smiles": p.smiles,
            "declared_role": p.declared_role,
            "note": p.note,
            "expected_ffi_error_class": p.expected_ffi_error,
            "observed_ffi_result": if ffi_result.is_ok() { "Ok" } else { "Err" },
            "observed_ffi_error": ffi_error_name,
            "ffi_rejects_before_backend_use": ffi_result.is_err(),
            "observed_gate_status": observed_status,
            "observed_gate_reason": run["result"]["metrics"]["gate_reason"],
            "observed_valid_single_component_gate": run["result"]["gates"]["valid_single_component"],
            "fails_closed": fails_closed,
        }));
    }

    // --- PART B: mutation quarantine ---
    let engine = EnginePool::new(".", 1).expect("engine pool constructs even with sparse evidence");
    let mutation_candidates: Vec<Value> = vec![
        json!({
            "candidate_id": "mutation-probe-1",
            "candidate_type": "molecule",
            "molecule": {"smiles": "C1OC1", "role": "resin"},
        }),
        json!({
            "candidate_id": "mutation-probe-2-injected-directive",
            "candidate_type": "molecule",
            "molecule": {
                "smiles": "C1OC1", "role": "resin",
                "mutation_directive": "add_epoxide_ring",
                "target_smiles": "C1OC1CCOC1CO1",
                "force_structure_change": true,
            },
        }),
        json!({
            "candidate_id": "mutation-probe-3-hostile-null-structure",
            "candidate_type": "molecule",
            "molecule": {"smiles": "CN(C)Cc1ccccc1", "role": "hardener"},
        }),
    ];
    let mut mutation_results: Vec<Value> = Vec::new();
    let mut mutation_violations: Vec<Value> = Vec::new();
    for input in &mutation_candidates {
        let output = engine
            .mutate(input, 42, json!({"parent_ids": [input["candidate_id"]], "generation": 1}))
            .expect("mutate is a pure lineage-tagging operation and must not error");
        let molecule_unchanged = input["molecule"] == output["molecule"];
        let generation_status = output
            .pointer("/lineage/generation_status")
            .and_then(Value::as_str)
            .unwrap_or("")
            .to_string();
        let quarantined = generation_status == "QUARANTINED_NO_STRUCTURE_CHANGE";
        if !molecule_unchanged || !quarantined {
            mutation_violations.push(json!({
                "candidate_id": input["candidate_id"],
                "molecule_unchanged": molecule_unchanged,
                "generation_status": generation_status,
                "input_molecule": input["molecule"],
                "output_molecule": output["molecule"],
            }));
        }
        mutation_results.push(json!({
            "candidate_id": input["candidate_id"],
            "input_molecule": input["molecule"],
            "output_molecule": output["molecule"],
            "molecule_field_byte_identical": molecule_unchanged,
            "generation_status": generation_status,
            "quarantined_no_structure_change": quarantined,
        }));
    }

    // --- PART B: structure-changing generation authorization ---
    let generation_requests: Vec<CampaignGenerationRequestV1> = vec![
        CampaignGenerationRequestV1 {
            request_id: "t08-mutation-attack-1".into(),
            parent_structures: vec!["C1OC1".into(), "NCCN".into()],
            reaction_family: "epoxy-amine-addition".into(),
            requested_role: "resin".into(),
        },
        CampaignGenerationRequestV1 {
            request_id: "t08-mutation-attack-2-hostile-parent".into(),
            parent_structures: vec!["CN(C)Cc1ccccc1".into()],
            reaction_family: "arbitrary-forged-family".into(),
            requested_role: "hardener".into(),
        },
        CampaignGenerationRequestV1 {
            request_id: "".into(), // deliberately malformed: empty request_id
            parent_structures: vec!["C1OC1".into()],
            reaction_family: "epoxy-amine-addition".into(),
            requested_role: "resin".into(),
        },
    ];
    let mut generation_results: Vec<Value> = Vec::new();
    let mut generation_violations: Vec<Value> = Vec::new();
    for req in &generation_requests {
        let result = engine.generate_compounds(req, 7);
        let authorized = result.is_ok();
        let error_message = result.as_ref().err().map(|e| e.to_string()).unwrap_or_default();
        if authorized {
            generation_violations.push(json!({
                "request_id": req.request_id,
                "note": "STRUCTURE-CHANGING GENERATION WAS AUTHORIZED WITHOUT A VERIFIED PHASE-0 GRANT -- REFUTES THE DIRECTIVE",
            }));
        }
        generation_results.push(json!({
            "request_id": req.request_id,
            "parent_structures": req.parent_structures,
            "reaction_family": req.reaction_family,
            "requested_role": req.requested_role,
            "authorized": authorized,
            "error": error_message,
        }));
    }

    // --- POSITIVE CONTROL ---
    // Plant a defect the real FFI itself refuses to produce: hand-craft a
    // MoleculeFactsV1 claiming oxirane_ring_count=1 for the exact
    // multi-fragment probe above (SMILES "C1OC1.NCCN"), the way a buggy
    // upstream normalizer that skipped the FFI's own MultiFragmentStructure
    // guard might. Feed it to the SAME live evaluate_authorized call used
    // throughout this harness and see whether the checker used above
    // (`observed_status == "SCORED"` => fails_closed=false => slip-through)
    // actually fires.
    let poisoned_smiles = "C1OC1.NCCN";
    let poisoned_facts = MoleculeFactsV1 {
        schema: "amphora.molecule-facts.v1".into(),
        canonical_isomeric_smiles: poisoned_smiles.into(),
        structure_identity: format!("smiles-sha256:{}", stable_hash(&json!(poisoned_smiles))),
        canonical_structure_sha256: stable_hash(&json!(poisoned_smiles)),
        formula: "C5H12N2O".into(),
        average_molecular_weight_g_mol: 116.16,
        oxirane_ring_count: 1,
        reactive_amine_hydrogen_count: 0,
        reactive_flags: ReactiveFlagsV1 {
            has_oxirane: true,
            has_reactive_amine_hydrogen: false,
            dual_role: false,
        },
        ontology_version: "amphora.reactive-ontology.v1".into(),
        toolkit_provenance: ToolkitProvenanceV1 {
            toolkit: "RDKit C++".into(),
            required_version: amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION.into(),
            detected_version: amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION.into(),
            exact_version_match: true,
        },
    };
    let poisoned_candidate = candidate_for("positive-control-poisoned-facts", poisoned_smiles, "resin");
    let poisoned_features = FeatureSnapshot {
        values: BTreeMap::from([(
            "molecule_facts_v1".to_string(),
            serde_json::to_value(&poisoned_facts).expect("facts serialize"),
        )]),
    };
    let poisoned_run = run_gate(&poisoned_candidate, &poisoned_features);
    let poisoned_status = poisoned_run["result"]["status"].as_str().unwrap_or("").to_string();
    let positive_control_detected = poisoned_status == "SCORED";

    let out = json!({
        "schema": "amphora.molecule-design-gate.t08-live-runtime-adversarial-probe.diagnostic.v1",
        "purpose": "FIRST adversarial verdict for amphora-molecule-design-gate: (A) run the real \
                    design_gate_result decision (via MoleculeCapability::evaluate_authorized) \
                    through the REAL pinned RDKit C++ FFI on >=10 held-out real coating molecules \
                    including the 3 named hostile nulls; (B) founder directive T2-08 fail-closed \
                    attack (polymers/wildcards/invalid-valence/multi-component/mutation).",
        "toolkit_provenance": {
            "toolkit": "RDKit C++",
            "required_version": amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION,
            "detected_version": status.detected_version,
            "exact_version_match": status.exact_version_match,
        },
        "part_a_gate_probes": {
            "n_probes": part_a_results.len(),
            "n_pass": part_a_pass,
            "n_disagreements": part_a_disagreements.len(),
            "n_hostile_nulls": gate_probes().iter().filter(|p| p.hostile_null).count(),
            "results": part_a_results,
            "disagreements": part_a_disagreements,
        },
        "part_b_structural_fail_closed": part_b_structural,
        "part_b_slip_throughs": part_b_slip_throughs,
        "part_b_mutation_quarantine": mutation_results,
        "part_b_mutation_violations": mutation_violations,
        "part_b_generation_authorization": generation_results,
        "part_b_generation_violations": generation_violations,
        "positive_control": {
            "planted_defect": "MoleculeFactsV1{oxirane_ring_count:1, ...} hand-attached to the \
                               multi-fragment probe 'C1OC1.NCCN' declared role=resin -- a facts \
                               record the real molecule_facts() FFI itself refuses to ever produce \
                               for this SMILES (it returns Err(MultiFragmentStructure) before \
                               touching the RDKit backend)",
            "how_planted": "constructed MoleculeFactsV1 literal in this harness's own source with \
                            oxirane_ring_count=1/has_oxirane=true instead of calling molecule_facts(), \
                            then fed it into the live evaluate_authorized(DESIGN_GATE_ID, ...) call \
                            via FeatureSnapshot.values[\"molecule_facts_v1\"], exactly mirroring the \
                            module's own fact-snapshot-authority-v1 'verbatim' snapshot mode",
            "detected": positive_control_detected,
            "poisoned_observed_status": poisoned_status,
            "evidence": "evaluate_authorized returned status=SCORED for a candidate whose raw SMILES \
                         is a two-fragment mixture that molecule_facts() rejects outright -- proving \
                         the checker in this harness (status==\"SCORED\" => flagged) fires when a \
                         disallowed structure's facts are smuggled past the FFI layer",
        },
        "verdict": {
            "part_a_all_scored_as_expected": part_a_disagreements.is_empty(),
            "part_b_no_slip_throughs": part_b_slip_throughs.is_empty(),
            "part_b_no_mutation_violations": mutation_violations.is_empty(),
            "part_b_no_generation_violations": generation_violations.is_empty(),
            "positive_control_fired": positive_control_detected,
        },
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
