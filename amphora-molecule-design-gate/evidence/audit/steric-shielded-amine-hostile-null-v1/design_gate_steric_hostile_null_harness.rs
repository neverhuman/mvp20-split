// steric-shielded-amine-hostile-null-v1: ROTATION-mode adversarial attack on
// amphora-molecule-design-gate's live production gate.
//
// Claim under attack: evidence/phase0/kpis/design-gate-structural-applicability-kpi.v1.json
// ("Structural applicability for role X iff the molecule carries reactive
// group Y ... every supplier TDS embeds the same accept/reject filter before
// quoting mix ratios") and mission.md's primary KPI ("negative-control
// rejection ... Zero silent acceptance of malformed, unsupported, or
// unauthorized inputs").
//
// Mechanism gap tested: amphora-rdkit-ffi/src/bridge.cc::count_reactive_amine_hydrogens
// excludes a neighbor N only if that neighbor is a carbonyl carbon, sulfonyl
// sulfur, or (non-cyanamide) amidine/guanidine carbon. It has NO clause for
// steric shielding. The 2,2,6,6-tetramethylpiperidine motif that underlies
// every commercial Hindered Amine Light Stabilizer (HALS) is a formally
// neutral, non-aromatic, non-conjugated secondary amine with one N-H --
// passes every existing exclusion clause -- yet the four methyl groups
// flanking the ring nitrogen sterically block approach to an electrophile
// (this is literally why 2,2,6,6-tetramethylpiperidine derivatives are used
// to synthesize the persistent TEMPO nitroxide radical rather than behaving
// as ordinary secondary-amine nucleophiles: Gugumus, "Possible mechanisms of
// light stabilisation in polyolefins by HALS", Polym. Degrad. Stab. 40(2)
// 167-215 (1993); Rabek, "Polymer Photodegradation" Ch. 3 (1995)). No
// supplier TDS for a HALS product (e.g. BASF Tinuvin 770, CAS 52829-07-9,
// bis(2,2,6,6-tetramethyl-4-piperidyl) sebacate) publishes an amine value or
// AHEW, or markets it as an epoxy hardener; it is sold exclusively as a UV
// light stabilizer, commonly post-added to marine topcoats at 0.5-2 wt%.
//
// This is the SAME class of over-admission already found and partially
// fixed for electronic effects (R-N02 guanidine/amidine exclusion,
// evidence/audit/nitrogen-nucleophilicity-authenticity-v1 protonation/
// sulfonyl/carbonyl clauses) but is a DIFFERENT physical mechanism (steric,
// not electronic) that neither the shipped rule nor the proposed 6-clause
// refined predicate from nitrogen-nucleophilicity-authenticity-v1 addresses
// (that audit's README explicitly scopes out only alpha-heteroatom amines
// and delocalized amidine/guanidine N-H -- sterics is not mentioned).

use std::collections::BTreeMap;

use amphora_core::{CandidateEnvelope, ExecutionContext, FeatureSnapshot};
use amphora_molecule_capabilities::{capability, DESIGN_GATE_ID};
use serde_json::{json, Value};

struct Probe {
    id: &'static str,
    smiles: &'static str,
    citation: &'static str,
    declared_role: &'static str,
    hostile_null: bool,
    mechanistic_expectation: &'static str,
    note: &'static str,
}

fn probes() -> Vec<Probe> {
    vec![
        Probe {
            id: "temp-2266-tetramethylpiperidine",
            smiles: "CC1(C)CCCC(C)(C)N1",
            citation: "2,2,6,6-tetramethylpiperidine (TEMP, CAS 768-66-1), C9H19N MW 141.25 -- \
                       parent scaffold of every commercial HALS; precursor to the TEMPO \
                       nitroxide radical precisely because the ring N-H is sterically shielded \
                       from ordinary nucleophilic chemistry by the four flanking methyls",
            declared_role: "hardener",
            hostile_null: true,
            mechanistic_expectation: "FAILED_GATES",
            note: "steric-shielding hostile null: formally neutral, non-aromatic, non-\
                   conjugated secondary amine N-H with no carbonyl/sulfonyl/amidine neighbor -- \
                   passes every existing shipped exclusion clause -- but is not a stoichiometric \
                   epoxy-amine nucleophile per HALS mechanism literature",
        },
        Probe {
            id: "tinuvin770-hals-diester",
            smiles: "O=C(OC1CC(C)(C)NC(C)(C)C1)CCCCCCCCC(=O)OC2CC(C)(C)NC(C)(C)C2",
            citation: "bis(2,2,6,6-tetramethyl-4-piperidyl) sebacate (Tinuvin 770, BASF, CAS \
                       52829-07-9), C28H52N2O4 MW 480.7 -- real commercial marine-topcoat UV \
                       light stabilizer, two free ring N-H HALS groups, never sold with an \
                       amine value / AHEW and never marketed as an epoxy hardener",
            declared_role: "hardener",
            hostile_null: true,
            mechanistic_expectation: "FAILED_GATES",
            note: "real named coating additive; commercial-grade steric-shielding hostile null",
        },
        Probe {
            id: "tinuvin292-hals-tertiary-control",
            smiles: "O=C(OC1CC(C)(C)N(C)C(C)(C)C1)CCCCCCCCC(=O)OC2CC(C)(C)N(C)C(C)(C)C2",
            citation: "bis(1,2,2,6,6-pentamethyl-4-piperidyl) sebacate (Tinuvin 292, BASF, CAS \
                       41556-26-7) -- N-methylated (tertiary amine) analog of Tinuvin 770",
            declared_role: "hardener",
            hostile_null: true,
            mechanistic_expectation: "FAILED_GATES",
            note: "internal control: tertiary amine, zero N-H, must fail via the PRE-EXISTING \
                   tertiary-amine exclusion (same mechanism already proven on BDMA in T-08) -- \
                   isolates that the failure mode under test is specific to the free-N-H HALS \
                   grade, not a generic HALS-vs-gate mismatch",
        },
        Probe {
            id: "piperidine-unhindered-secondary-amine-control",
            smiles: "C1CCNCC1",
            citation: "piperidine (CAS 110-89-4), C5H11N MW 85.15 -- unhindered secondary \
                       cyclic amine, structurally identical to the TEMP scaffold minus the four \
                       ring methyls",
            declared_role: "hardener",
            hostile_null: false,
            mechanistic_expectation: "SCORED",
            note: "positive comparator: an unhindered secondary amine SHOULD be admitted (it is \
                   a genuine nucleophile); if the gate cannot distinguish this from the TEMP \
                   probe above despite the drastic difference in real nucleophilicity, the gate \
                   is using N-H presence as a complete proxy for reactivity with no steric term",
        },
    ]
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "steric-shielded-amine-hostile-null-v1".into(),
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
    let backend_status = amphora_rdkit_ffi::backend_status();
    let mut results: Vec<Value> = Vec::new();
    let mut refutations: Vec<Value> = Vec::new();
    let mut n_pass = 0u32;

    for p in probes() {
        let facts = amphora_rdkit_ffi::molecule_facts(p.smiles)
            .unwrap_or_else(|e| panic!("probe {} failed to parse via REAL RDKit FFI: {e:?}", p.id));
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
        let matches_mechanistic_expectation = observed_status == p.mechanistic_expectation;
        if matches_mechanistic_expectation {
            n_pass += 1;
        } else {
            refutations.push(json!({
                "id": p.id,
                "smiles": p.smiles,
                "citation": p.citation,
                "declared_role": p.declared_role,
                "mechanistic_expectation": p.mechanistic_expectation,
                "observed_status": observed_status,
                "observed_gate_reason": observed_reason,
                "observed_oxirane_ring_count": facts.oxirane_ring_count,
                "observed_reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
                "note": "GATE ADMITTED A NON-NUCLEOPHILIC / STERICALLY-SHIELDED CANDIDATE AS role_appropriate_reactivity == true",
            }));
        }
        results.push(json!({
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
            "mechanistic_expectation": p.mechanistic_expectation,
            "observed_status": observed_status,
            "observed_gate_reason": observed_reason,
            "observed_role_appropriate_reactivity_gate": run["result"]["gates"]["role_appropriate_reactivity"],
            "per_call_two_replay_byte_stable": run["per_call_two_replay_byte_stable"],
            "matches_mechanistic_expectation": matches_mechanistic_expectation,
        }));
    }

    let output = json!({
        "schema": "amphora.design-gate-steric-shielded-amine-hostile-null.v1",
        "run_id": "steric-shielded-amine-hostile-null-v1",
        "backend_status": format!("{backend_status:?}"),
        "n_probes": results.len(),
        "n_matches_mechanistic_expectation": n_pass,
        "n_refutations": refutations.len(),
        "results": results,
        "refutations": refutations,
    });
    println!("{}", serde_json::to_string_pretty(&output).expect("serialize output"));
}
