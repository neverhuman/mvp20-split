//! The three signed demos. Each returns a serde_json::Value diagnostic that
//! is deterministic by construction (BTreeMap-backed maps, ordered
//! reductions, pinned seeds) and is serialized by `run` to the exact bytes
//! that the two-replay gate and the DSSE signer operate on.

pub mod p1;
pub mod p3;
pub mod p4;

use crate::oracle::OracleReading;
use serde_json::{json, Value};

pub const DEMO_DATE: &str = "2026-08-03";
pub const DEMO_HOST: &str = "xbabe2";
pub const AUTHORITY: &str = "AUDIT_ONLY";

/// Claim locks stamped into every diagnostic this crate emits.
pub fn claim_locks() -> Value {
    json!({
        "promotes_authority": false,
        "modifies_manifest": false,
        "flips_scientific_readiness": false,
        "human_review_performed": false,
        "no_live_model_calls": true,
        "no_new_science": true,
        "no_solver_authority_granted": true,
        "no_ranking_authority_granted": true,
        "oracles_read_only_signed_tree_artifacts": true,
        "pre_phase_0_research_only": true
    })
}

pub fn sources_json(readings: &[&OracleReading]) -> Value {
    Value::Array(
        readings
            .iter()
            .map(|r| {
                json!({
                    "logical_id": r.logical_id,
                    "rel_path": r.rel_path,
                    "sha256": r.sha256,
                })
            })
            .collect(),
    )
}

/// Dispatch a demo by id and serialize its diagnostic to canonical bytes
/// (sorted-key pretty JSON + trailing newline). These are the bytes that
/// must be identical across two independent replays.
pub fn run(demo: &str) -> anyhow::Result<Vec<u8>> {
    let value = match demo {
        "p1" => p1::diagnostic()?,
        "p3" => p3::diagnostic()?,
        "p4" => p4::diagnostic()?,
        other => anyhow::bail!("unknown demo id '{other}' (expected p1|p3|p4)"),
    };
    let mut bytes = serde_json::to_vec_pretty(&value)?;
    bytes.push(b'\n');
    Ok(bytes)
}
