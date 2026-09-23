// Adversarial-refusal-mischaracterization probe (amphora-molecule-generator).
//
// Claim under attack (docs/mission.md "Honest current state"):
//   "Adversary-supplied adversary_proposals list, adversary_declared_proposal
//   _count, and candidate_declared availability booleans are all defensively
//   refused."
// and the Phase-0 KPI harness's own scenario framing
// (amphora-molecule-capabilities/tests/molecule_generator_phase0_kpi.rs,
// scenarios 3-4): "runtime must NOT elevate proposal_count or
// generation_status" / "runtime must NOT elevate any of them" -- language
// that implies active validation logic inspects and rejects these fields.
//
// This harness drives the REAL production generator_result() (via
// capability(GENERATOR_ID).evaluate()) with the SAME 5 KPI scenarios plus a
// sixth MEGA-adversarial candidate carrying grossly malformed/oversized
// adversarial fields, and diffs the decision-relevant output (everything
// except the input-identity-derived fields candidate_contract_hash_v1,
// original_bytes_sha256, lineage_diagnostic.parent_candidate_id) across all
// six. If "defensively refused" describes real validation logic, the
// adversarial scenarios should exercise a code path a clean baseline does
// not. If the claim is a mischaracterization of an input-independent stub,
// every decision-relevant field will be byte-identical across all six,
// including the mega-adversarial one, regardless of how extreme its
// declared fields are.

use std::collections::BTreeMap;

use amphora_core::{Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot};
use amphora_molecule_capabilities::{capability, GENERATOR_ID};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

fn sha(b: &[u8]) -> String {
    let mut d = Sha256::new();
    d.update(b);
    format!("{:x}", d.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "molgen-w2-adversarial-refusal-probe".into(),
        deterministic_seed: 20260819,
        lineage: Value::Null,
    }
}

/// Strip input-identity-derived fields so what remains is exactly the
/// DECISION surface: status, evidence_scope, gates, missing_inputs,
/// explanations, uncertainty, score, objective_values, source_refs, and all
/// metrics except the three identity/byte-hash fields.
fn decision_relevant(out_json: &Value) -> Value {
    let mut v = out_json.clone();
    if let Some(metrics) = v.get_mut("metrics").and_then(Value::as_object_mut) {
        metrics.remove("candidate_contract_hash_v1");
        metrics.remove("original_bytes_sha256");
        if let Some(lineage) = metrics
            .get_mut("lineage_diagnostic")
            .and_then(Value::as_object_mut)
        {
            lineage.remove("parent_candidate_id");
        }
    }
    v
}

struct Case {
    id: &'static str,
    candidate: Value,
}

fn cases() -> Vec<Case> {
    vec![
        Case {
            id: "S1_baseline_oxirane",
            candidate: json!({
                "candidate_id": "generator-resin-oxirane",
                "candidate_type": "molecule",
                "molecule": {"smiles": "C1OC1", "declared_role": "resin"}
            }),
        },
        Case {
            id: "S2_baseline_hardener_amine",
            candidate: json!({
                "candidate_id": "generator-hardener-amine",
                "candidate_type": "molecule",
                "molecule": {"smiles": "NCCN", "declared_role": "hardener"}
            }),
        },
        Case {
            id: "S3_adversarial_proposals_injection",
            candidate: json!({
                "candidate_id": "generator-adversarial-proposals",
                "candidate_type": "molecule",
                "molecule": {
                    "smiles": "c1ccccc1O",
                    "declared_role": "resin",
                    "adversary_proposals": [
                        {"smiles": "C1OC1", "confidence": 0.99},
                        {"smiles": "CC(=O)O", "confidence": 0.95}
                    ],
                    "adversary_declared_proposal_count": 2,
                    "adversary_declared_generation_status": "SCORED"
                }
            }),
        },
        Case {
            id: "S4_adversarial_rdkit_grammar_declarations",
            candidate: json!({
                "candidate_id": "generator-adversarial-rdkit",
                "candidate_type": "molecule",
                "molecule": {
                    "smiles": "CC(C)C",
                    "declared_role": "resin",
                    "candidate_declared_pinned_rdkit_available": true,
                    "candidate_declared_locked_reaction_grammar_available": true,
                    "candidate_declared_rights_cleared_corpus_available": true
                }
            }),
        },
        Case {
            id: "S5_baseline_methane",
            candidate: json!({
                "candidate_id": "generator-no-molecule",
                "candidate_type": "molecule",
                "molecule": {"smiles": "C"}
            }),
        },
        Case {
            id: "S6_MEGA_adversarial_extreme",
            candidate: json!({
                "candidate_id": "generator-mega-adversarial",
                "candidate_type": "molecule",
                "molecule": {
                    "smiles": "NCCN",
                    "declared_role": "hardener",
                    "adversary_proposals": (0..500).map(|i| json!({"smiles": "C1OC1", "confidence": 1.0, "idx": i})).collect::<Vec<_>>(),
                    "adversary_declared_proposal_count": 999999999_i64,
                    "adversary_declared_generation_status": "SCORED",
                    "adversary_declared_status": "SCORED",
                    "adversary_declared_evidence_scope": "FULL_PRODUCTION",
                    "candidate_declared_pinned_rdkit_available": true,
                    "candidate_declared_locked_reaction_grammar_available": true,
                    "candidate_declared_rights_cleared_corpus_available": true,
                    "candidate_declared_generation_authorized": true,
                    "candidate_declared_deterministic_lineage_recorded": true,
                    "gates": {"generation_authorized": true, "deterministic_lineage_recorded": true},
                    "missing_inputs": [],
                    "uncertainty": {"scope": "none -- fully validated"},
                }
            }),
        },
    ]
}

fn main() {
    let cap = capability(GENERATOR_ID).expect("generator capability registered");
    let features = FeatureSnapshot::default();
    let ctx = context();

    let mut per_case: Vec<Value> = Vec::new();
    let mut decision_values: BTreeMap<&'static str, Value> = BTreeMap::new();

    for case in &cases() {
        let candidate =
            CandidateEnvelope::from_value(case.candidate.clone()).expect("candidate parses");
        let out = cap.evaluate(&candidate, &features, &ctx).expect("evaluate ok");
        let out_json = serde_json::to_value(&out).unwrap();
        let dr = decision_relevant(&out_json);
        decision_values.insert(case.id, dr.clone());
        per_case.push(json!({
            "case_id": case.id,
            "full_output": out_json,
            "decision_relevant_subset": dr,
        }));
    }

    // Pairwise-compare every case's decision-relevant subset against S1's.
    let baseline = decision_values.get("S1_baseline_oxirane").unwrap().clone();
    let mut all_identical_to_baseline = true;
    let mut diffs: Vec<Value> = Vec::new();
    for (id, v) in &decision_values {
        let identical = *v == baseline;
        if !identical {
            all_identical_to_baseline = false;
            diffs.push(json!({"case_id": id, "differs_from_baseline": true}));
        }
    }

    // Grep the production source for the six adversarial field names --
    // record the exact command + a literal file read so the diagnostic is
    // self-contained (not just an external claim).
    let lib_rs = std::fs::read_to_string(
        "/home/ubuntu/amphora/build/mvp20-split/amphora-molecule-capabilities/src/lib.rs",
    )
    .expect("lib.rs readable");
    let needles = [
        "adversary_proposals",
        "adversary_declared_proposal_count",
        "adversary_declared_generation_status",
        "candidate_declared_pinned_rdkit_available",
        "candidate_declared_locked_reaction_grammar_available",
        "candidate_declared_rights_cleared_corpus_available",
    ];
    let mut occurrences: BTreeMap<&str, usize> = BTreeMap::new();
    for n in &needles {
        occurrences.insert(n, lib_rs.matches(n).count());
    }
    let lib_rs_sha256 = sha(lib_rs.as_bytes());
    let total_occurrences: usize = occurrences.values().sum();

    let diagnostic = json!({
        "schema": "amphora.molecule-generator.molgen-adversarial-refusal-mischaracterization-diagnostic.v1",
        "module_id": "amphora-molecule-generator",
        "cases": per_case,
        "all_decision_relevant_outputs_identical_to_baseline": all_identical_to_baseline,
        "n_cases": decision_values.len(),
        "diffs": diffs,
        "adversarial_field_names_searched": needles,
        "adversarial_field_occurrences_in_lib_rs": occurrences,
        "adversarial_field_total_occurrences_in_lib_rs": total_occurrences,
        "lib_rs_sha256": lib_rs_sha256,
        "lib_rs_path": "amphora-molecule-capabilities/src/lib.rs",
    });

    println!("{}", serde_json::to_string_pretty(&Value::Object(match diagnostic {
        Value::Object(m) => m,
        _ => Map::new(),
    })).unwrap());
}
