//! LIVE Rust differential probe for the amphora-model-card-authority
//! registry/envelope surface.
//!
//! Executes the REAL runtime (amphora-engine `NativeRegistry` +
//! `EnginePool::score_campaign_modules`) over a locked JSON corpus. Every
//! candidate enters through the strict candidate-contract front door exactly
//! as a hostile caller would exercise it. Emits one deterministic JSON object
//! to stdout (serde_json's BTreeMap object model yields sorted keys).
//! No randomness, no clock, no filesystem writes.

use amphora_engine::{EnginePool, NativeRegistry};
use serde_json::{json, Map, Value};
use std::io::{self, Read};

const MODULE: &str = "amphora-model-card-authority";
const ROOT: &str = "/home/ubuntu/amphora/build/mvp20-split";
// Deliberately nonexistent: the engine documents MISSING evidence-context
// state for an absent root; the probe must not fabricate evidence.
const NO_EVIDENCE_ROOT: &str = "/tmp/amphora-mca-live-parity-no-evidence-root";

fn lane_facts(registry: &NativeRegistry, lane: &str) -> Value {
    match registry.report(lane) {
        Ok(report) => {
            let active = report["active_submodels"]
                .as_array()
                .cloned()
                .unwrap_or_default();
            json!({
                "is_err": false,
                "schema": report["schema"],
                "module_count": report["module_count"],
                "registered_modules": report["registered_modules"],
                "active_module_count": report["active_module_count"],
                "implementation": report["implementation"],
                "active_contains_module": active.iter().any(|m| m == MODULE),
            })
        }
        Err(error) => json!({ "is_err": true, "display": error.to_string() }),
    }
}

fn main() {
    let mut raw = String::new();
    io::stdin().read_to_string(&mut raw).expect("read corpus");
    let corpus: Value = serde_json::from_str(&raw).expect("parse corpus");

    let registry = NativeRegistry::global().expect("live registry");
    let capability = registry.resolve(MODULE).expect("resolve target module");
    let descriptor = capability.descriptor();
    let descriptor_json = json!({
        "project": descriptor.project,
        "authority_ceiling": descriptor.authority_ceiling,
        "solver_use_ceiling": descriptor.solver_use_ceiling,
        "model_readiness_ceiling": descriptor.model_readiness_ceiling,
        "ranking_eligible": descriptor.ranking_eligible,
        "candidate_types": descriptor.candidate_types,
        "non_blocking_claim_locks": descriptor.non_blocking_claim_locks,
        "readiness": descriptor.readiness,
    });

    let unknown_module = corpus["registry_probes"]["unknown_module"]
        .as_str()
        .expect("unknown_module probe");
    let unknown_lane = corpus["registry_probes"]["unknown_lane"]
        .as_str()
        .expect("unknown_lane probe");
    let resolve_unknown = match registry.resolve(unknown_module) {
        Ok(_) => json!({ "is_err": false }),
        Err(error) => json!({ "is_err": true, "display": error.to_string() }),
    };

    let pool = EnginePool::with_evidence_root(ROOT, NO_EVIDENCE_ROOT, 1).expect("engine pool");

    let mut cases = Map::new();
    for (case_id, case) in corpus["cases"].as_object().expect("cases") {
        let seed = case["seed"].as_u64().unwrap_or(0);
        let run_id = case["run_id"].as_str().unwrap_or("mca-live");
        let module_id = case["module_id"].as_str().unwrap_or(MODULE);
        let candidate = &case["candidate"];
        let outcome = match pool.score_campaign_modules(candidate, seed, run_id, &[module_id]) {
            Ok(result) => json!({
                "ok": true,
                "envelope": result["score_envelopes"][0],
                "envelope_count": result["score_envelopes"].as_array().map(Vec::len),
                "provenance_manifest_sha256":
                    result["provenance"]["source_hashes"]["module-manifest.json"],
                "evidence_context_sha256": result["provenance"]["evidence_context_sha256"],
                "execution_profile": result["provenance"]["execution_profile"],
            }),
            Err(error) => json!({ "ok": false, "error_display": error.to_string() }),
        };
        cases.insert(case_id.clone(), outcome);
    }

    let output = json!({
        "schema": "amphora.model-card-authority.live-runtime-ground-truth.v1",
        "module_id": MODULE,
        "module_count": registry.module_count(),
        "descriptor": descriptor_json,
        "registry_errors": {
            "resolve_unknown_module": resolve_unknown,
            "report_unknown_lane": lane_facts(registry, unknown_lane),
        },
        "lanes": {
            "molecule": lane_facts(registry, "molecule"),
            "formulation": lane_facts(registry, "formulation"),
            "infrastructure": lane_facts(registry, "infrastructure"),
        },
        "cases": Value::Object(cases),
    });
    println!("{output}");
}
