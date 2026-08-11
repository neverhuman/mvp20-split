//! T-13 regression: verify_run must recompute the interior event-hash chain and
//! bind run identity to the archive directory, so a self-consistent forgery or a
//! verbatim cross-directory replay can no longer verify. These lock in the fix
//! that the standalone real-archive-tamper harness proves at scale; this suite
//! runs under `cargo test --workspace`.

use amphora_core::{verify_run, RunArchive, RunArchiveError};
use serde_json::json;
use std::fs;
use std::path::{Path, PathBuf};

fn scratch(tag: &str) -> PathBuf {
    let base = std::env::temp_dir().join(format!(
        "amphora-t13-{tag}-{}-{}",
        std::process::id(),
        tag.len()
    ));
    let _ = fs::remove_dir_all(&base);
    fs::create_dir_all(&base).unwrap();
    base
}

/// Build a genuine run (dir name == run_id) with a real, correctly-chained
/// event log, exactly as the production path writes one.
fn build_genuine(base: &Path, run_id: &str) -> PathBuf {
    let manifest = json!({"schema": "amphora.module-manifest.v1", "modules": []});
    let mut archive = RunArchive::create(base, run_id, &manifest).unwrap();
    archive
        .append("run_started", None, 0, json!({"population": 2}))
        .unwrap();
    archive
        .append(
            "candidate_proposed",
            Some("cand-1".into()),
            0,
            json!({"candidate_id": "cand-1"}),
        )
        .unwrap();
    archive
        .append("run_finished", None, 0, json!({"survivors": 1}))
        .unwrap();
    archive
        .final_state(&json!({"records": [], "candidates": []}))
        .unwrap();
    base.join(run_id)
}

#[test]
fn genuine_run_verifies() {
    let base = scratch("genuine");
    let path = build_genuine(&base, "run-genuine-1");
    assert!(verify_run(&path).is_ok(), "a genuine run must verify");
}

#[test]
fn tampered_payload_without_rehash_is_rejected() {
    let base = scratch("tamper");
    let path = build_genuine(&base, "run-tamper-1");
    // Flip a byte in an event payload but leave its stored event_hash intact:
    // the old verify trusted the stored hash; the new one recomputes and catches it.
    let events = fs::read_to_string(path.join("events.jsonl")).unwrap();
    let tampered = events.replace("\"population\":2", "\"population\":999");
    assert_ne!(events, tampered, "probe must actually change a payload");
    fs::write(path.join("events.jsonl"), tampered).unwrap();
    assert!(
        matches!(verify_run(&path), Err(RunArchiveError::Integrity(_))),
        "a payload edit that leaves the stored event_hash must be rejected"
    );
}

#[test]
fn verbatim_replay_into_foreign_directory_is_rejected() {
    let base = scratch("replay");
    let path = build_genuine(&base, "run-original");
    // Copy the entire genuine archive verbatim into a differently-named dir.
    let foreign = base.join("run-victim");
    fs::create_dir_all(&foreign).unwrap();
    for name in ["manifest.json", "events.jsonl", "final-state.json", "provenance.json"] {
        fs::copy(path.join(name), foreign.join(name)).unwrap();
    }
    // Same bytes, verifies at its own identity...
    assert!(verify_run(&path).is_ok());
    // ...but not when replayed under a directory whose name is not its run_id.
    assert!(
        matches!(verify_run(&foreign), Err(RunArchiveError::Integrity(_))),
        "a verbatim archive replayed under a foreign directory must be rejected"
    );
}
