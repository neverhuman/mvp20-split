//! AUDIT_ONLY live-runtime differential harness for
//! amphora-molecule-design-gate :: fact-snapshot-authority-v1.
//!
//! Drives the LIVE Rust design-gate capability (the same
//! `design_gate_result` surface the shipped Phase-0 KPI harness
//! `tests/design_gate_phase0_kpi.rs` exercises) over an externally supplied
//! probe file. Three snapshot modes:
//!   null                    -> empty FeatureSnapshot (facts absent)
//!   {"mode":"synth", ...}   -> MoleculeFactsV1 synthesized from 4-field
//!                              fixture-style facts, byte-for-byte the same
//!                              construction as the shipped KPI harness's
//!                              `synth_facts` (copied below)
//!   {"mode":"verbatim",...} -> the given JSON value is inserted untouched as
//!                              features.values["molecule_facts_v1"]
//!
//! Each probe is evaluated twice; per-probe byte stability is recorded.
//! Output is a single JSON object keyed by probe_id (BTreeMap => sorted,
//! deterministic bytes). No file under the module tree is written.

use std::collections::BTreeMap;
use std::{env, fs, process};

use amphora_core::{stable_hash, CandidateEnvelope, ExecutionContext, FeatureSnapshot};
use amphora_molecule_capabilities::{capability, DESIGN_GATE_ID};
use amphora_rdkit_ffi::{
    MoleculeFactsV1, ReactiveFlagsV1, ToolkitProvenanceV1, REACTIVE_ONTOLOGY_VERSION,
    REQUIRED_RDKIT_VERSION,
};
use serde_json::{json, Value};

/// Copied verbatim (logic-identical) from the shipped Phase-0 KPI harness
/// `amphora-molecule-capabilities/tests/design_gate_phase0_kpi.rs::synth_facts`
/// so hostile probes travel exactly the pathway the shipped KPI uses.
fn synth_facts(record_facts: &Value, canonical_smiles: &str) -> MoleculeFactsV1 {
    let mw = record_facts["average_molecular_weight_g_mol"]
        .as_f64()
        .unwrap_or(0.0);
    let ox = record_facts["oxirane_ring_count"].as_u64().unwrap_or(0) as u32;
    let nh = record_facts["reactive_amine_hydrogen_count"]
        .as_u64()
        .unwrap_or(0) as u32;
    let has_oxirane = ox > 0;
    let has_reactive_amine_hydrogen = nh > 0;
    let dual_role = has_oxirane && has_reactive_amine_hydrogen;
    MoleculeFactsV1 {
        schema: "amphora.molecule-facts.v1".into(),
        canonical_isomeric_smiles: canonical_smiles.into(),
        structure_identity: format!("smiles-sha256:{}", stable_hash(&json!(canonical_smiles))),
        canonical_structure_sha256: stable_hash(&json!(canonical_smiles)),
        formula: record_facts["formula"].as_str().unwrap_or("C_H_N_O_").into(),
        average_molecular_weight_g_mol: mw,
        oxirane_ring_count: ox,
        reactive_amine_hydrogen_count: nh,
        reactive_flags: ReactiveFlagsV1 {
            has_oxirane,
            has_reactive_amine_hydrogen,
            dual_role,
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

fn features_from_snapshot(snapshot: &Value) -> FeatureSnapshot {
    if snapshot.is_null() {
        return FeatureSnapshot {
            values: BTreeMap::new(),
        };
    }
    let facts_value = match snapshot["mode"].as_str() {
        Some("synth") => {
            let canonical = snapshot["canonical_smiles"]
                .as_str()
                .unwrap_or("canonical-placeholder");
            serde_json::to_value(synth_facts(&snapshot["facts"], canonical))
                .expect("facts serialize")
        }
        Some("verbatim") => snapshot["value"].clone(),
        other => {
            eprintln!("unknown snapshot mode: {other:?}");
            process::exit(2);
        }
    };
    FeatureSnapshot {
        values: BTreeMap::from([("molecule_facts_v1".to_string(), facts_value)]),
    }
}

fn main() {
    let probes_path = env::args().nth(1).expect("usage: harness <probes.json>");
    let probes: Value =
        serde_json::from_slice(&fs::read(&probes_path).expect("probes readable"))
            .expect("probes parse");
    let cap = capability(DESIGN_GATE_ID).expect("design-gate capability registered");
    let context = ExecutionContext {
        run_id: "fact-snapshot-authority-v1".into(),
        deterministic_seed: 0,
        lineage: Value::Null,
    };

    let mut out: BTreeMap<String, Value> = BTreeMap::new();
    for probe in probes["probes"].as_array().expect("probes array") {
        let probe_id = probe["probe_id"].as_str().expect("probe_id").to_string();
        let candidate = match CandidateEnvelope::from_value(probe["candidate"].clone()) {
            Ok(candidate) => candidate,
            Err(error) => {
                out.insert(probe_id, json!({ "envelope_error": error.to_string() }));
                continue;
            }
        };
        let features = features_from_snapshot(&probe["snapshot"]);
        let first = cap.evaluate_authorized(&candidate, &features, &context, None);
        let second = cap.evaluate_authorized(&candidate, &features, &context, None);
        let entry = match (first, second) {
            (Ok(first), Ok(second)) => {
                let byte_stable = serde_json::to_vec(&first).expect("result serializes")
                    == serde_json::to_vec(&second).expect("result serializes");
                json!({
                    "result": serde_json::to_value(&first).expect("result serializes"),
                    "per_probe_two_replay_byte_stable": byte_stable,
                })
            }
            (Err(error), _) | (_, Err(error)) => {
                json!({ "capability_error": error.to_string() })
            }
        };
        out.insert(probe_id, entry);
    }
    print!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "schema": "amphora.molecule-design-gate.fact-snapshot-authority.live-run.v1",
            "runtime": "amphora-molecule-capabilities (live Rust, default features, no rdkit backend)",
            "entry_point": "MoleculeCapability::evaluate_authorized -> design_gate_result",
            "results": out,
        }))
        .expect("output serializes")
    );
}
