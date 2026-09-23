//! LIVE Rust differential probe for the amphora-report-packager
//! diagnostic / evaluation / mediation surface.
//!
//! Executes the REAL runtime:
//!   * amphora_assurance_capabilities::deterministic_control_diagnostic
//!     ("amphora-report-packager") -- the shipped known-answer fixture plus the
//!     five compiled-in adversarial mutants, with the real Ed25519 verifier,
//!     the real NFKC banned-claim lint, and the real stable_hash canonicaliser
//!     executing (not being read as source bytes);
//!   * AssuranceCapability::new + Capability::evaluate -- the Phase-0 KPI
//!     decision path (signed-deliverable quarantine), under two distinct
//!     ExecutionContexts to witness run_id/seed/lineage invariance live;
//!   * the candidate-type mediation and unsupported-module deny paths.
//!
//! Emits ONE deterministic JSON object to stdout (serde_json's BTreeMap object
//! model yields sorted keys). No randomness, no clock, no filesystem writes,
//! no input: every byte of output derives from compile-time-embedded runtime
//! state. This is NOT a re-implementation of the runtime logic.

use amphora_assurance_capabilities::{deterministic_control_diagnostic, AssuranceCapability};
use amphora_core::{Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot};
use serde_json::{json, Value};

const MODULE: &str = "amphora-report-packager";

fn evidence_candidate() -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": "live-parity-evidence-1",
        "candidate_type": "evidence_package",
        "evidence_refs": {
            "evidence_package": {
                "candidate_id": "live-parity-evidence-1",
                "lab_package_signature": {
                    "schema": "amphora.cryptographic-signature-evidence.v1",
                    "algorithm": "ED25519",
                    "signature": "ab".repeat(64),
                    "verification_receipt": {"status": "VERIFIED"}
                }
            }
        }
    }))
    .expect("valid evidence candidate")
}

fn formulation_candidate() -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": "live-parity-formula-1",
        "candidate_type": "formulation",
        "formulation": {"part_A": {"resin": 1.0}, "part_B": {"hardener": 1.0}}
    }))
    .expect("valid formulation candidate")
}

fn context(run_id: &str, seed: u64, lineage: Value) -> ExecutionContext {
    ExecutionContext {
        run_id: run_id.into(),
        deterministic_seed: seed,
        lineage,
    }
}

fn outcome<T: serde::Serialize, E: std::fmt::Display>(result: &Result<T, E>) -> Value {
    match result {
        Ok(value) => json!({
            "is_err": false,
            "value": serde_json::to_value(value).expect("runtime value serializes"),
        }),
        Err(error) => json!({ "is_err": true, "display": error.to_string() }),
    }
}

fn main() {
    // A. Live deterministic-control diagnostic (fixture + 5 mutants).
    let diagnostic = deterministic_control_diagnostic(MODULE);

    // B. Live capability resolution + descriptor projection.
    let capability = AssuranceCapability::new(MODULE).expect("resolve target module");
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

    // C. Live KPI evaluation under two deliberately different contexts.
    let run_a = capability.evaluate(
        &evidence_candidate(),
        &FeatureSnapshot::default(),
        &context("live-parity-run-a", 1, json!({"wall_clock": "excluded"})),
    );
    let run_b = capability.evaluate(
        &evidence_candidate(),
        &FeatureSnapshot::default(),
        &context("live-parity-run-b", u64::MAX, json!({"wall_clock": "different"})),
    );
    let context_invariant = match (&run_a, &run_b) {
        (Ok(a), Ok(b)) => {
            serde_json::to_value(a).expect("result serializes")
                == serde_json::to_value(b).expect("result serializes")
        }
        _ => false,
    };

    // D. Live mediation / deny paths.
    let wrong_type = capability.evaluate(
        &formulation_candidate(),
        &FeatureSnapshot::default(),
        &context("live-parity-wrong-type", 42, Value::Null),
    );
    let unknown = AssuranceCapability::new("unknown-module").map(|_| ());
    let padded = AssuranceCapability::new(" amphora-report-packager").map(|_| ());
    let empty = AssuranceCapability::new("").map(|_| ());

    let output = json!({
        "schema": "amphora.report-packager.live-runtime-probe-output.v1",
        "module_id": MODULE,
        "diagnostic": outcome(&diagnostic),
        "descriptor": descriptor_json,
        "evaluate": {
            "run_a": outcome(&run_a),
            "run_b": outcome(&run_b),
            "context_invariant": context_invariant,
        },
        "mediation": {
            "wrong_candidate_type": outcome(&wrong_type),
            "unknown_module": outcome(&unknown),
            "whitespace_module": outcome(&padded),
            "empty_module": outcome(&empty),
        },
    });
    println!(
        "{}",
        serde_json::to_string(&output).expect("probe output serializes")
    );
}
