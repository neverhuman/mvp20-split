//! LIVE differential probe: does the amphora-model-card-authority KPI's own
//! claim -- "every candidate enters through the strict candidate-contract
//! front door exactly as a hostile caller would exercise it" (docstring in
//! live-runtime-envelope-parity-v1/run_live_parity.py) -- actually hold?
//!
//! Links the REAL amphora-core (amphora_core::parse_json_strict, the strict
//! duplicate-JSON-key-rejecting deserializer that is the actual byte-level
//! front door at CandidateEnvelope::from_bytes) and the REAL amphora-engine
//! (EnginePool::score_campaign_modules, the function the KPI's own probe
//! calls). No re-implementation of either.
//!
//! Fixed raw bytes below encode ONE JSON object with the key
//! "candidate_type" written TWICE: first "evidence_package", then
//! "formulation". This is not disguised whitespace or homoglyphs -- it is a
//! syntactically duplicate object key, which RFC 8259 leaves
//! implementation-defined and which amphora_core::contract::StrictSeed
//! exists specifically to reject ("duplicate JSON key: {key}").
//!
//! No randomness, no clock, no filesystem writes.

use amphora_engine::EnginePool;
use serde_json::{json, Value};

const ROOT: &str = "/home/ubuntu/amphora/build/mvp20-split";
const NO_EVIDENCE_ROOT: &str = "/tmp/amphora-mca-dupkey-probe-no-evidence-root";
const MODULE: &str = "amphora-model-card-authority";

// One JSON object, "candidate_type" present twice: "evidence_package" then
// "formulation". Both payload shapes ("evidence_refs" and "formulation")
// are present so the probe is not confounded by an incidental
// payload-mismatch error unrelated to the duplicate-key question.
const DUP_KEY_CANDIDATE: &[u8] = br#"{
  "candidate_id": "mca-dupkey-front-door-probe",
  "candidate_type": "evidence_package",
  "candidate_type": "formulation",
  "evidence_refs": {},
  "formulation": {
    "recipe": {
      "part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}},
      "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}
    },
    "basis": "mass_g_per_batch",
    "batch_mass_g": 137.13,
    "ingredient_catalog_version": "facts.v2",
    "application": {"dft_mil": 5.0, "temperature_C": 25.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared"},
    "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}
  }
}"#;

fn canon(v: &Value) -> String {
    serde_json::to_string(v).expect("canon")
}

fn run_once() -> Value {
    // Path 1: the REAL strict byte-level front door
    // (CandidateEnvelope::from_bytes goes through this exact function).
    let strict_result = match amphora_core::parse_json_strict(DUP_KEY_CANDIDATE) {
        Ok(value) => json!({"is_err": false, "accepted_candidate_type": value.get("candidate_type").cloned()}),
        Err(error) => json!({"is_err": true, "display": error.to_string()}),
    };

    // Path 2: what the KPI's own run_live_parity.py / runtime_probe/src/main.rs
    // actually do -- serde_json's default (lenient) parse, last-key-wins,
    // silently, then handed straight to EnginePool::score_campaign_modules
    // via CandidateEnvelope::from_value (which never calls parse_json_strict).
    let lenient_value: Value =
        serde_json::from_slice(DUP_KEY_CANDIDATE).expect("lenient parse always succeeds");
    let which_won = lenient_value.get("candidate_type").cloned();

    let pool = EnginePool::with_evidence_root(ROOT, NO_EVIDENCE_ROOT, 1).expect("engine pool");
    let outcome = match pool.score_campaign_modules(&lenient_value, 0, "mca-dupkey-A", &[MODULE]) {
        Ok(result) => json!({
            "ok": true,
            "envelope": result["score_envelopes"][0],
        }),
        Err(error) => json!({"ok": false, "error_display": error.to_string()}),
    };

    json!({
        "schema": "amphora.model-card-authority.candidate-strict-parse-front-door-diagnostic.v1",
        "raw_bytes_sha256": {
            "note": "same fixed bytes fed to both paths",
        },
        "path1_real_strict_front_door_parse_json_strict": strict_result,
        "path2_kpi_methodology_lenient_parse_then_score_campaign_modules": {
            "lenient_parse_which_candidate_type_won": which_won,
            "score_campaign_modules_outcome": outcome,
        },
    })
}

fn main() {
    let out = run_once();
    println!("{}", canon(&out));
}
