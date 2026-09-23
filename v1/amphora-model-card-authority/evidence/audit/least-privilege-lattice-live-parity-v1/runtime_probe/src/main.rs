//! LIVE Rust differential probe for amphora-model-card-authority
//! least-privilege-lattice-live-parity-v1.
//!
//! Extends live-runtime-envelope-parity-v1 (which only exercised the
//! amphora-model-card-authority module row) to ALL 29 canonical modules in
//! module-manifest.json. Calls the REAL runtime (amphora-engine
//! `NativeRegistry` + `EnginePool::score_campaign_modules`) with a single
//! fixed formulation candidate requested against every canonical module_id
//! in one campaign-traversal call, and emits the REAL envelope authority
//! fields the live registry computed for each. No re-implementation: this
//! is the same `NativeRegistry::envelope` code path used in production for
//! every module. Deterministic stdout (serde_json BTreeMap => sorted keys).
//! No randomness, no clock, no filesystem writes.

use amphora_engine::{EnginePool, NativeRegistry};
use serde_json::{json, Map, Value};
use std::io::{self, Read};

const ROOT: &str = "/home/ubuntu/amphora/build/mvp20-split";
const NO_EVIDENCE_ROOT: &str = "/tmp/amphora-mca-lattice-live-parity-no-evidence-root";

const CANONICAL_MODULES: [&str; 29] = [
    "amphora-barrier-corrosion-score",
    "amphora-candidate-contract",
    "amphora-cro-protocol-packager",
    "amphora-cure-potlife-gate",
    "amphora-design-rule-score",
    "amphora-envelope-gates",
    "amphora-evidence-intake-validator",
    "amphora-formulation-arithmetic",
    "amphora-formulation-universe",
    "amphora-ingredient-library",
    "amphora-ip-fto-guard",
    "amphora-known-answer-benchmarks",
    "amphora-model-card-authority",
    "amphora-molecule-design-gate",
    "amphora-molecule-generator",
    "amphora-molecule-novelty",
    "amphora-molecule-property",
    "amphora-molecule-role-ranker",
    "amphora-optimizer-orchestrator",
    "amphora-process-qc-twin",
    "amphora-public-corrosion-benchmark",
    "amphora-redteam-audit",
    "amphora-report-packager",
    "amphora-run-provenance",
    "amphora-solvency-score",
    "amphora-source-ledger",
    "amphora-sourceability-ehs",
    "amphora-tolerance-robustness",
    "amphora-viscosity-score",
];

fn main() {
    let mut raw = String::new();
    io::stdin().read_to_string(&mut raw).expect("read corpus");
    let corpus: Value = serde_json::from_str(&raw).expect("parse corpus");
    let candidate = &corpus["candidate"];
    let seed = corpus["seed"].as_u64().unwrap_or(0);
    let run_id = corpus["run_id"].as_str().unwrap_or("mca-lattice-live");

    let registry = NativeRegistry::global().expect("live registry");
    let module_count = registry.module_count();

    let mut descriptors = Map::new();
    for module_id in CANONICAL_MODULES.iter() {
        let capability = registry.resolve(module_id).expect("resolve canonical module");
        let d = capability.descriptor();
        descriptors.insert(
            (*module_id).to_string(),
            json!({
                "project": d.project,
                "authority_ceiling": d.authority_ceiling,
                "solver_use_ceiling": d.solver_use_ceiling,
                "model_readiness_ceiling": d.model_readiness_ceiling,
                "ranking_eligible": d.ranking_eligible,
                "candidate_types": d.candidate_types,
                "non_blocking_claim_locks": d.non_blocking_claim_locks,
                "readiness": d.readiness,
            }),
        );
    }

    let pool = EnginePool::with_evidence_root(ROOT, NO_EVIDENCE_ROOT, 1).expect("engine pool");
    let module_ids: Vec<&str> = CANONICAL_MODULES.to_vec();
    let outcome = match pool.score_campaign_modules(candidate, seed, run_id, &module_ids) {
        Ok(result) => {
            let envelopes = result["score_envelopes"].as_array().cloned().unwrap_or_default();
            let mut by_module = Map::new();
            for env in envelopes.iter() {
                let module_id = env.get("module_id").and_then(Value::as_str).unwrap_or("").to_string();
                let authority_subset = json!({
                    "status": env["status"],
                    "authority_tier": env["authority_tier"],
                    "score_semantics": env["score_semantics"],
                    "usable_by_optimizer": env["usable_by_optimizer"],
                    "model_card": {
                        "model_authority": env["metrics"]["model_card"]["model_authority"],
                        "solver_use": env["metrics"]["model_card"]["solver_use"],
                        "model_readiness_status": env["metrics"]["model_card"]["model_readiness_status"],
                        "can_optimize": env["metrics"]["model_card"]["can_optimize"],
                        "current_pass": env["metrics"]["model_card"]["current_pass"],
                        "product_claim_ready": env["metrics"]["model_card"]["product_claim_ready"],
                        "scientific_applicability": env["metrics"]["model_card"]["scientific_applicability"],
                    },
                    "authority_receipt": {
                        "granted_level": env["metrics"]["authority_receipt"]["granted_level"],
                        "ranking_eligible": env["metrics"]["authority_receipt"]["ranking_eligible"],
                        "registry_owned": env["metrics"]["authority_receipt"]["registry_owned"],
                    },
                });
                by_module.insert(module_id, authority_subset);
            }
            json!({
                "ok": true,
                "envelope_count": envelopes.len(),
                "provenance_manifest_sha256":
                    result["provenance"]["source_hashes"]["module-manifest.json"],
                "by_module": by_module,
            })
        }
        Err(error) => json!({ "ok": false, "error_display": error.to_string() }),
    };

    let output = json!({
        "schema": "amphora.model-card-authority.least-privilege-lattice-live-ground-truth.v1",
        "module_count": module_count,
        "canonical_modules_probed": CANONICAL_MODULES.len(),
        "descriptors": descriptors,
        "campaign_outcome": outcome,
    });
    println!("{}", serde_json::to_string(&output).expect("serialize"));
}
