// design-gate-oxirane-steric-hostile-null-v1: ROTATION-mode adversarial attack
// on amphora-molecule-design-gate's live production gate.
//
// Claim under attack: evidence/phase0/kpis/design-gate-structural-applicability-kpi.v1.json
// ("Structural applicability for role X iff the molecule carries reactive
// group Y ... every supplier TDS embeds the same accept/reject filter before
// quoting mix ratios") and mission.md's primary KPI ("negative-control
// rejection ... Zero silent acceptance of malformed, unsupported, or
// unauthorized inputs").
//
// Mechanism gap tested: amphora-rdkit-ffi/src/bridge.cc::count_oxirane_rings
// counts ANY three-membered ring of one oxygen (degree 2, formal charge 0)
// bonded by two single bonds to two carbons that are themselves singly
// bonded to each other. It has NO substitution/steric term at all -- unlike
// count_reactive_amine_hydrogens (which, after R-N02 and
// nitrogen-nucleophilicity-authenticity-v1, carries four electronic
// exclusion clauses), the oxirane counter carries ZERO exclusion clauses of
// any kind. This is the resin-side twin of the amine-side gap already found
// and REFUTED twice (nitrogen-nucleophilicity-authenticity-v1, electronic;
// steric-shielded-amine-hostile-null-v1, steric) but on the OTHER declared
// role and a DIFFERENT physical mechanism: steric hindrance to nucleophilic
// ring-opening by an amine curing agent, not to N-H counting.
//
// This module's own theory anchor (mission.md, Wicks/Jones/Pappas 2007
// Sec.15.2-15.4) grounds resin admissibility in glycidyl-ether epoxy-amine
// cure chemistry: a terminal epoxide carbon bearing at most the glycidyl
// -CH2-O-R substituent, sterically open to backside (SN2-type) nucleophilic
// attack by a primary/secondary amine. Nucleophilic epoxide ring-opening
// rate is well documented to fall sharply as substitution at the epoxide
// carbons increases -- steric hindrance to backside approach is the same
// mechanism (not merely an analogy) that underlies SN2 rate retardation
// generally, and is discussed specifically for epoxides in Parker, R. E.;
// Isaacs, N. S. "Mechanisms of Epoxide Reactions." Chem. Rev. 1959, 59(4),
// 737-799, DOI 10.1021/cr50028a006 (Sec. III: structure-reactivity for
// nucleophilic ring-opening; tetrasubstituted epoxides are the slowest class
// under basic/neutral nucleophilic conditions because no carbon is left
// sterically or electronically accessible to backside attack). No supplier
// TDS lists a fully- or highly-substituted small-molecule epoxide lacking
// the glycidyl -CH2-O- motif as a two-part epoxy-amine coating resin; these
// are sold exclusively as synthesis reagents / intermediates.
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
            id: "tetramethyloxirane-hostile-null",
            smiles: "CC1(C)C(C)(C)O1",
            citation: "2,2,3,3-tetramethyloxirane (tetramethylethylene oxide, CAS 5076-20-0), \
                       C6H12O MW 100.16 -- commercially available synthesis reagent \
                       (Sigma-Aldrich), never sold or classified by any supplier as a coatings \
                       epoxy resin. Both oxirane carbons are fully substituted (quaternary, \
                       zero ring C-H), sterically blocking the backside nucleophilic approach \
                       an amine curing agent needs to open the ring (Parker & Isaacs 1959, \
                       Chem. Rev. 59(4):737-799, DOI 10.1021/cr50028a006, Sec. III)",
            declared_role: "resin",
            hostile_null: true,
            mechanistic_expectation: "FAILED_GATES",
            note: "steric-shielding hostile null on the RESIN side: a formally valid oxirane \
                   ring (O degree-2, both ring bonds single, no charge) that passes every \
                   existing clause in count_oxirane_rings (there are none besides ring \
                   topology) but has no accessible epoxide carbon for amine ring-opening -- \
                   categorically unlike the glycidyl-ether motif this module's own theory \
                   anchor requires",
        },
        Probe {
            id: "trimethyloxirane-gradation-null",
            smiles: "CC1(C)C(C)O1",
            citation: "2,2,3-trimethyloxirane (2,3-epoxy-2-methylbutane, CAS 5076-19-7), \
                       C5H10O MW 86.13 -- commercially available synthesis reagent, never sold \
                       or classified as a coatings epoxy resin. One epoxide carbon is fully \
                       substituted (quaternary), the other trisubstituted (one ring C-H) -- \
                       intermediate steric case between the tetrasubstituted probe above and \
                       the unhindered glycidyl-ether control below",
            declared_role: "resin",
            hostile_null: true,
            mechanistic_expectation: "FAILED_GATES",
            note: "second, independent hostile null at a different substitution grade, showing \
                   the gap is a substitution-blind continuum, not one pathological molecule",
        },
        Probe {
            id: "phenyl-glycidyl-ether-resin-control",
            smiles: "c1ccc(cc1)OCC1CO1",
            citation: "phenyl glycidyl ether (PGE, CAS 122-60-1), C9H10O2 MW 150.17 -- real, \
                       commercially marketed epoxy reactive diluent used in coating \
                       formulations; unhindered terminal glycidyl epoxide carbon (CH2, only \
                       the -O-Ar substituent) matching the theory anchor's glycidyl-ether motif",
            declared_role: "resin",
            hostile_null: false,
            mechanistic_expectation: "SCORED",
            note: "positive comparator: a genuine, unhindered glycidyl-ether resin SHOULD be \
                   admitted; if the gate cannot distinguish this from the fully-hindered probes \
                   above despite the drastic difference in real nucleophilic ring-opening rate, \
                   the gate is using bare oxirane-ring topology as a complete proxy for \
                   resin-appropriate reactivity with no steric term",
        },
        Probe {
            id: "oxetane-ring-size-specificity-control",
            smiles: "C1COC1",
            citation: "oxetane (CAS 503-30-0), C3H6O MW 58.08 -- four-membered cyclic ether, \
                       structurally adjacent to but distinct from a three-membered oxirane",
            declared_role: "resin",
            hostile_null: false,
            mechanistic_expectation: "FAILED_GATES",
            note: "internal specificity control: confirms the PRE-EXISTING ring-size clause \
                   in count_oxirane_rings still correctly rejects a non-oxirane cyclic ether -- \
                   isolates that the finding under test is substitution-blindness WITHIN valid \
                   3-membered rings, not a wholesale failure of ring detection",
        },
    ]
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "design-gate-oxirane-steric-hostile-null-v1".into(),
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
                "note": "GATE ADMITTED A STERICALLY-HINDERED / NON-GLYCIDYL-ETHER CANDIDATE AS role_appropriate_reactivity == true",
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
        "schema": "amphora.design-gate-oxirane-steric-hostile-null.v1",
        "run_id": "design-gate-oxirane-steric-hostile-null-v1",
        "backend_status": format!("{backend_status:?}"),
        "n_probes": results.len(),
        "n_matches_mechanistic_expectation": n_pass,
        "n_refutations": refutations.len(),
        "results": results,
        "refutations": refutations,
    });
    println!("{}", serde_json::to_string_pretty(&output).expect("serialize output"));
}
