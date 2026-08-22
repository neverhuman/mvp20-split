//! Scale adversarial harness for amphora-run-provenance (T-13 / T2-13).
//!
//! Links the REAL amphora_core crate and calls the REAL public verify_run
//! against copies of REAL in-tree run archives found under .amphora/runs/
//! (not the n=3 synthetic tempdir fixture the shipped Phase-0 KPI uses).
//!
//! For every archive, runs the 4 required tamper probes -- truncated chain
//! (mid-point removal), reordered links, substituted intermediate hash,
//! replayed archive (verbatim + spliced divergence) -- each in a NAIVE
//! variant (provenance.json left untouched, byte-level mismatch expected to
//! be caught) and a FORGED variant (provenance.json recomputed with the
//! REAL amphora_core::stable_hash / raw SHA-256 so the tampered archive is
//! internally self-consistent -- this is "root-hash recompute that
//! reconciles a forged history").
//!
//! AUDIT_ONLY: only ever writes under the scratch directory passed as
//! argv[1]; never mutates the real archives under argv[2] (opened read-only).

use amphora_core::{stable_hash, verify_run, RunArchiveError};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::{Path, PathBuf};

fn raw_sha256(bytes: &[u8]) -> String {
    let mut d = Sha256::new();
    d.update(bytes);
    format!("{:x}", d.finalize())
}

fn variant(e: &RunArchiveError) -> &'static str {
    match e {
        RunArchiveError::Exists(_) => "Exists",
        RunArchiveError::Integrity(_) => "Integrity",
        RunArchiveError::Io(_) => "Io",
        RunArchiveError::Json(_) => "Json",
        RunArchiveError::Contract(_) => "Contract",
    }
}

fn verify_outcome(path: &Path) -> (String, Option<String>) {
    match verify_run(path) {
        Ok(root) => ("Ok".to_string(), Some(root)),
        Err(e) => (variant(&e).to_string(), None),
    }
}

fn read_lines(path: &Path) -> Vec<String> {
    fs::read_to_string(path)
        .unwrap_or_default()
        .lines()
        .map(|l| l.to_string())
        .collect()
}

fn write_lines(path: &Path, lines: &[String]) {
    let mut out = lines.join("\n");
    if !lines.is_empty() {
        out.push('\n');
    }
    fs::write(path, out).expect("write events");
}

fn last_event_hash(lines: &[String]) -> String {
    match lines.last() {
        Some(l) => {
            let v: Value = serde_json::from_str(l).expect("parse last event");
            v.get("event_hash")
                .and_then(Value::as_str)
                .expect("event_hash field")
                .to_string()
        }
        None => raw_sha256(&[]),
    }
}

fn set_sequence(line: &str, seq: u64) -> String {
    let mut v: Value = serde_json::from_str(line).expect("parse event line");
    v["sequence"] = json!(seq);
    serde_json::to_string(&v).expect("reser event line")
}

fn set_event_hash(line: &str, hash: &str) -> String {
    let mut v: Value = serde_json::from_str(line).expect("parse event line");
    v["event_hash"] = json!(hash);
    serde_json::to_string(&v).expect("reser event line")
}

/// The exact provenance.json construction from amphora_core::RunArchive::final_state,
/// applied to arbitrary (possibly tampered) manifest/events/final-state bytes so a
/// forger can "reconcile" a tampered archive into internal self-consistency.
fn compute_provenance(
    run_id: &str,
    manifest_bytes: &[u8],
    events_bytes: &[u8],
    final_state_value: &Value,
) -> Value {
    let events_str = String::from_utf8_lossy(events_bytes).to_string();
    let lines: Vec<String> = events_str.lines().map(|l| l.to_string()).collect();
    let event_chain_root = last_event_hash(&lines);
    let manifest_sha256 = raw_sha256(manifest_bytes);
    let events_sha256 = raw_sha256(events_bytes);
    let final_state_hash = stable_hash(final_state_value);
    let seed = json!({
        "run_id": run_id,
        "manifest_sha256": manifest_sha256,
        "events_sha256": events_sha256,
        "event_chain_root": event_chain_root,
        "final_state_hash": final_state_hash,
    });
    json!({
        "schema": "amphora.run-provenance.v1",
        "run_id": run_id,
        "manifest_sha256": manifest_sha256,
        "events_sha256": events_sha256,
        "event_chain_root": event_chain_root,
        "final_state_hash": final_state_hash,
        "root_hash": stable_hash(&seed),
        "promotion_receipt_eligible": false,
        "signature_status": "UNSIGNED_CONTROLLED_KEY_REQUIRED",
    })
}

fn write_pretty(path: &Path, value: &Value) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("serialize");
    bytes.push(b'\n');
    fs::write(path, bytes).expect("write pretty");
}

fn copy_file_if_exists(src_dir: &Path, dst_dir: &Path, name: &str) -> bool {
    let src = src_dir.join(name);
    if src.exists() {
        fs::copy(&src, dst_dir.join(name)).expect("copy file");
        true
    } else {
        false
    }
}

fn run_id_from_manifest(manifest_bytes: &[u8], fallback: &str) -> String {
    serde_json::from_slice::<Value>(manifest_bytes)
        .ok()
        .and_then(|v| v.get("run_id").and_then(Value::as_str).map(String::from))
        .unwrap_or_else(|| fallback.to_string())
}

/// Build a baseline scratch copy of a real archive: copies manifest/events/final-state
/// verbatim, and either copies the real provenance.json (if present) or synthesizes
/// one from the real bytes using the shipped formula (compute_provenance), so
/// verify_run can be exercised on archives that never called final_state().
fn build_baseline(archive_dir: &Path, out_dir: &Path) -> (String, &'static str) {
    fs::create_dir_all(out_dir).expect("mkdir baseline");
    let has_manifest = copy_file_if_exists(archive_dir, out_dir, "manifest.json");
    let has_events = copy_file_if_exists(archive_dir, out_dir, "events.jsonl");
    let has_final = copy_file_if_exists(archive_dir, out_dir, "final-state.json");
    assert!(has_manifest && has_events && has_final, "incomplete real archive");
    let had_real_provenance = copy_file_if_exists(archive_dir, out_dir, "provenance.json");
    if had_real_provenance {
        let prov: Value =
            serde_json::from_slice(&fs::read(out_dir.join("provenance.json")).unwrap()).unwrap();
        let run_id = prov
            .get("run_id")
            .and_then(Value::as_str)
            .unwrap_or("unknown")
            .to_string();
        (run_id, "real")
    } else {
        let manifest_bytes = fs::read(out_dir.join("manifest.json")).unwrap();
        let events_bytes = fs::read(out_dir.join("events.jsonl")).unwrap();
        let final_state: Value =
            serde_json::from_slice(&fs::read(out_dir.join("final-state.json")).unwrap()).unwrap();
        let dir_name = archive_dir.file_name().unwrap().to_string_lossy().to_string();
        let run_id = run_id_from_manifest(&manifest_bytes, &dir_name);
        let provenance = compute_provenance(&run_id, &manifest_bytes, &events_bytes, &final_state);
        write_pretty(&out_dir.join("provenance.json"), &provenance);
        (run_id, "synthesized_from_real_bytes_via_shipped_final_state_formula")
    }
}

fn copy_baseline_to(src: &Path, dst: &Path) {
    fs::create_dir_all(dst).expect("mkdir probe dir");
    for name in ["manifest.json", "events.jsonl", "final-state.json", "provenance.json"] {
        fs::copy(src.join(name), dst.join(name)).expect("copy baseline file");
    }
}

struct ProbeResult {
    probe: &'static str,
    variant: &'static str,
    n_events_before: usize,
    detail: String,
    result: String,
    root_hash: Option<String>,
}

fn main() {
    let scratch = PathBuf::from(std::env::args().nth(1).expect("usage: harness <scratch> <archives_root>"));
    let archives_root = PathBuf::from(std::env::args().nth(2).expect("usage: harness <scratch> <archives_root>"));
    fs::create_dir_all(&scratch).expect("scratch dir");

    let mut archive_dirs: Vec<PathBuf> = fs::read_dir(&archives_root)
        .expect("read archives_root")
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.is_dir())
        .collect();
    archive_dirs.sort();

    let mut per_archive: Vec<Value> = Vec::new();
    let mut skipped: Vec<Value> = Vec::new();
    let mut baselines: Vec<(String, PathBuf, usize)> = Vec::new(); // (archive_id, baseline_dir, n_events)

    for archive_dir in &archive_dirs {
        let archive_id = archive_dir.file_name().unwrap().to_string_lossy().to_string();
        let required_present = ["manifest.json", "events.jsonl", "final-state.json"]
            .iter()
            .all(|n| archive_dir.join(n).exists());
        if !required_present {
            skipped.push(json!({
                "archive_id": archive_id,
                "reason": "missing one of manifest.json/events.jsonl/final-state.json; not a completed RunArchive"
            }));
            continue;
        }
        let baseline_dir = scratch.join(&archive_id).join("baseline");
        let (run_id, provenance_source) = build_baseline(archive_dir, &baseline_dir);
        let (baseline_result, baseline_root) = verify_outcome(&baseline_dir);
        let lines = read_lines(&baseline_dir.join("events.jsonl"));
        let n_events = lines.len();
        baselines.push((archive_id.clone(), baseline_dir.clone(), n_events));

        let mut probes: Vec<ProbeResult> = Vec::new();

        // ---- Probe 1: TRUNCATED CHAIN (mid-point removal) ----
        if n_events >= 2 {
            let mid = n_events / 2;
            let mut truncated: Vec<String> = lines.clone();
            let removed = truncated.remove(mid);
            // renumber remaining lines to close the sequence gap (forces the
            // detector to rely on hash-chain semantics, not the trivial gap check)
            let renumbered: Vec<String> = truncated
                .iter()
                .enumerate()
                .map(|(i, l)| set_sequence(l, (i + 1) as u64))
                .collect();

            // naive: renumbered events, provenance untouched (still describes original bytes)
            let naive_dir = scratch.join(&archive_id).join("probe_truncate_naive");
            copy_baseline_to(&baseline_dir, &naive_dir);
            write_lines(&naive_dir.join("events.jsonl"), &renumbered);
            let (r, h) = verify_outcome(&naive_dir);
            probes.push(ProbeResult {
                probe: "truncated_chain",
                variant: "naive_provenance_untouched",
                n_events_before: n_events,
                detail: format!(
                    "removed event at mid-index {mid} (sequence {}), renumbered remaining {} events 1..N, provenance.json left describing the ORIGINAL bytes",
                    mid + 1, renumbered.len()
                ),
                result: r,
                root_hash: h,
            });

            // forged: recompute provenance from the truncated+renumbered bytes
            let forged_dir = scratch.join(&archive_id).join("probe_truncate_forged");
            copy_baseline_to(&baseline_dir, &forged_dir);
            write_lines(&forged_dir.join("events.jsonl"), &renumbered);
            let manifest_bytes = fs::read(forged_dir.join("manifest.json")).unwrap();
            let events_bytes = fs::read(forged_dir.join("events.jsonl")).unwrap();
            let final_state: Value =
                serde_json::from_slice(&fs::read(forged_dir.join("final-state.json")).unwrap()).unwrap();
            let forged_prov = compute_provenance(&run_id, &manifest_bytes, &events_bytes, &final_state);
            write_pretty(&forged_dir.join("provenance.json"), &forged_prov);
            let (r2, h2) = verify_outcome(&forged_dir);
            probes.push(ProbeResult {
                probe: "truncated_chain",
                variant: "forged_root_hash_recompute_reconciled",
                n_events_before: n_events,
                detail: format!(
                    "same mid-chain removal (dropped original sequence {}, content_snippet={:?}) but provenance.json RECOMPUTED with the real stable_hash/raw_sha256 formula against the truncated bytes",
                    mid + 1,
                    &removed.chars().take(80).collect::<String>()
                ),
                result: r2,
                root_hash: h2,
            });
        }

        // ---- Probe 2: REORDERED LINKS (swap two adjacent middle events) ----
        if n_events >= 3 {
            let i = (n_events - 1) / 2; // never the last index
            let j = i + 1.min(n_events - 1 - i).max(1);
            let j = if j >= n_events { i.saturating_sub(1) } else { j };
            let mut swapped = lines.clone();
            swapped.swap(i, j);
            let renumbered: Vec<String> = swapped
                .iter()
                .enumerate()
                .map(|(idx, l)| set_sequence(l, (idx + 1) as u64))
                .collect();

            let naive_dir = scratch.join(&archive_id).join("probe_reorder_naive");
            copy_baseline_to(&baseline_dir, &naive_dir);
            write_lines(&naive_dir.join("events.jsonl"), &renumbered);
            let (r, h) = verify_outcome(&naive_dir);
            probes.push(ProbeResult {
                probe: "reordered_links",
                variant: "naive_provenance_untouched",
                n_events_before: n_events,
                detail: format!("swapped events at positions {i} and {j} (0-indexed), renumbered sequence 1..N, provenance.json left describing original bytes"),
                result: r,
                root_hash: h,
            });

            let forged_dir = scratch.join(&archive_id).join("probe_reorder_forged");
            copy_baseline_to(&baseline_dir, &forged_dir);
            write_lines(&forged_dir.join("events.jsonl"), &renumbered);
            let manifest_bytes = fs::read(forged_dir.join("manifest.json")).unwrap();
            let events_bytes = fs::read(forged_dir.join("events.jsonl")).unwrap();
            let final_state: Value =
                serde_json::from_slice(&fs::read(forged_dir.join("final-state.json")).unwrap()).unwrap();
            let forged_prov = compute_provenance(&run_id, &manifest_bytes, &events_bytes, &final_state);
            write_pretty(&forged_dir.join("provenance.json"), &forged_prov);
            let (r2, h2) = verify_outcome(&forged_dir);
            probes.push(ProbeResult {
                probe: "reordered_links",
                variant: "forged_root_hash_recompute_reconciled",
                n_events_before: n_events,
                detail: format!("same swap of positions {i} and {j}, but provenance.json RECOMPUTED against the reordered bytes"),
                result: r2,
                root_hash: h2,
            });
        }

        // ---- Probe 3: SUBSTITUTED INTERMEDIATE HASH ----
        if n_events >= 2 {
            let mid = n_events / 2 - if n_events / 2 == n_events - 1 { 1 } else { 0 };
            let mid = mid.min(n_events - 2).max(0); // guarantee NOT the last event
            let original_hash = {
                let v: Value = serde_json::from_str(&lines[mid]).unwrap();
                v.get("event_hash").and_then(Value::as_str).unwrap().to_string()
            };
            let garbage_hash = raw_sha256(format!("SUBSTITUTED-{archive_id}-{mid}").as_bytes());
            let mut mutated = lines.clone();
            mutated[mid] = set_event_hash(&mutated[mid], &garbage_hash);

            let naive_dir = scratch.join(&archive_id).join("probe_subst_naive");
            copy_baseline_to(&baseline_dir, &naive_dir);
            write_lines(&naive_dir.join("events.jsonl"), &mutated);
            let (r, h) = verify_outcome(&naive_dir);
            probes.push(ProbeResult {
                probe: "substituted_intermediate_hash",
                variant: "naive_provenance_untouched",
                n_events_before: n_events,
                detail: format!(
                    "event_hash of interior event index {mid} (sequence {}) replaced {original_hash} -> {garbage_hash}; not the last event, so provenance.event_chain_root is untouched by construction; provenance.json left describing original bytes",
                    mid + 1
                ),
                result: r,
                root_hash: h,
            });

            let forged_dir = scratch.join(&archive_id).join("probe_subst_forged");
            copy_baseline_to(&baseline_dir, &forged_dir);
            write_lines(&forged_dir.join("events.jsonl"), &mutated);
            let manifest_bytes = fs::read(forged_dir.join("manifest.json")).unwrap();
            let events_bytes = fs::read(forged_dir.join("events.jsonl")).unwrap();
            let final_state: Value =
                serde_json::from_slice(&fs::read(forged_dir.join("final-state.json")).unwrap()).unwrap();
            let forged_prov = compute_provenance(&run_id, &manifest_bytes, &events_bytes, &final_state);
            write_pretty(&forged_dir.join("provenance.json"), &forged_prov);
            let (r2, h2) = verify_outcome(&forged_dir);
            probes.push(ProbeResult {
                probe: "substituted_intermediate_hash",
                variant: "forged_root_hash_recompute_reconciled",
                n_events_before: n_events,
                detail: format!(
                    "same interior event_hash substitution at index {mid} (sequence {}), provenance.json RECOMPUTED (events_sha256 + root_hash) against the mutated bytes; event_chain_root unchanged since the mutated event was not last",
                    mid + 1
                ),
                result: r2,
                root_hash: h2,
            });
        }

        // ---- Probe 4: REPLAYED ARCHIVE (verbatim byte replay into a new run slot) ----
        {
            let replay_dir = scratch.join(&archive_id).join("probe_replay_verbatim");
            copy_baseline_to(&baseline_dir, &replay_dir);
            let (r, h) = verify_outcome(&replay_dir);
            probes.push(ProbeResult {
                probe: "replayed_archive",
                variant: "verbatim_byte_replay_new_directory",
                n_events_before: n_events,
                detail: format!(
                    "entire archive (manifest/events/final-state/provenance) copied byte-for-byte from {archive_id} into a differently-named scratch directory, simulating replay of this run's complete archive into a new run slot; verify_run(path) never compares its own directory name to provenance.run_id or to any event's embedded run_id"
                ),
                result: r,
                root_hash: h,
            });
        }

        per_archive.push(json!({
            "archive_id": archive_id,
            "run_id": run_id,
            "provenance_source": provenance_source,
            "n_events": n_events,
            "baseline_verify_result": baseline_result,
            "baseline_root_hash": baseline_root,
            "probes": probes.iter().map(|p| json!({
                "probe": p.probe,
                "variant": p.variant,
                "n_events_before_tamper": p.n_events_before,
                "detail": p.detail,
                "verify_result": p.result,
                "verify_root_hash": p.root_hash,
            })).collect::<Vec<_>>(),
        }));
    }

    // ---- Cross-archive splice divergence probe ("diverge a replay input/output pair") ----
    // For consecutive pairs of archives with >=1 event each, splice archive B's
    // events.jsonl into archive A's manifest/final-state shell, reforge provenance,
    // and verify: does a genuinely FOREIGN event history (different run_id embedded
    // in every event line) get accepted when bolted onto a different run's shell?
    let mut divergence_probes: Vec<Value> = Vec::new();
    let eligible: Vec<&(String, PathBuf, usize)> = baselines.iter().filter(|(_, _, n)| *n >= 1).collect();
    for pair in eligible.chunks(2) {
        if pair.len() != 2 {
            continue;
        }
        let (a_id, a_dir, _) = pair[0];
        let (b_id, b_dir, _) = pair[1];
        let splice_dir = scratch.join(format!("splice_{a_id}_with_{b_id}"));
        copy_baseline_to(a_dir, &splice_dir);
        let b_events = fs::read(b_dir.join("events.jsonl")).unwrap();
        fs::write(splice_dir.join("events.jsonl"), &b_events).expect("splice events");
        let a_run_id = {
            let v: Value = serde_json::from_slice(&fs::read(a_dir.join("provenance.json")).unwrap()).unwrap();
            v.get("run_id").and_then(Value::as_str).unwrap_or("unknown").to_string()
        };
        let manifest_bytes = fs::read(splice_dir.join("manifest.json")).unwrap();
        let final_state: Value =
            serde_json::from_slice(&fs::read(splice_dir.join("final-state.json")).unwrap()).unwrap();
        let forged_prov = compute_provenance(&a_run_id, &manifest_bytes, &b_events, &final_state);
        write_pretty(&splice_dir.join("provenance.json"), &forged_prov);
        let (r, h) = verify_outcome(&splice_dir);
        divergence_probes.push(json!({
            "probe": "replay_divergence_spliced_input_output",
            "host_archive": a_id,
            "foreign_events_from_archive": b_id,
            "detail": format!("archive {a_id}'s manifest.json+final-state.json kept as-is; its events.jsonl REPLACED with archive {b_id}'s complete (foreign) event stream -- each foreign event line still carries run_id={b_id} internally; provenance.json RECOMPUTED to reconcile against the spliced bytes"),
            "verify_result": r,
            "verify_root_hash": h,
        }));
    }

    let n_archives_tested = per_archive.len();
    let mut probe_counts: std::collections::BTreeMap<String, (u64, u64, u64)> = std::collections::BTreeMap::new(); // (n, n_ok, n_err)
    for a in &per_archive {
        for p in a["probes"].as_array().unwrap() {
            let key = format!("{}::{}", p["probe"].as_str().unwrap(), p["variant"].as_str().unwrap());
            let entry = probe_counts.entry(key).or_insert((0, 0, 0));
            entry.0 += 1;
            if p["verify_result"] == "Ok" {
                entry.1 += 1;
            } else {
                entry.2 += 1;
            }
        }
    }
    let mut divergence_ok = 0u64;
    let mut divergence_n = 0u64;
    for d in &divergence_probes {
        divergence_n += 1;
        if d["verify_result"] == "Ok" {
            divergence_ok += 1;
        }
    }

    let summary: Vec<Value> = probe_counts
        .iter()
        .map(|(k, (n, ok, err))| json!({"probe_variant": k, "n": n, "verify_ok_count": ok, "verify_err_count": err}))
        .collect();

    let out = json!({
        "schema": "amphora.run-provenance.real-archive-tamper-scale-harness-output.v1",
        "harness": "rp-real-archive-tamper-harness v1: links amphora-core; calls the real verify_run against copies of REAL in-tree run archives under .amphora/runs/",
        "archives_root": archives_root.to_string_lossy(),
        "n_archives_found": archive_dirs.len(),
        "n_archives_tested": n_archives_tested,
        "skipped_archives": skipped,
        "probe_variant_summary": summary,
        "divergence_probe_summary": {"n": divergence_n, "verify_ok_count": divergence_ok},
        "per_archive": per_archive,
        "divergence_probes": divergence_probes,
    });
    println!("{}", serde_json::to_string(&out).expect("serialize output"));
}
