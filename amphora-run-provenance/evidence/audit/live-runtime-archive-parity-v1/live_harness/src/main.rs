//! LIVE differential harness for amphora-run-provenance
//! (evidence/audit/live-runtime-archive-parity-v1).
//!
//! FIRST harness in this module that executes the real Rust runtime instead of
//! re-deriving it: links amphora-core and calls the real public entry points
//! `RunArchive::create/append/snapshot/final_state` and `verify_run`.
//!
//! Emits a single deterministic JSON document on stdout containing, for every
//! scenario and probe, the live archive file bytes (UTF-8 strings) and the
//! observed `verify_run` outcome (Ok(root_hash) or the `RunArchiveError`
//! variant NAME only — never a tempdir path), so two executions in different
//! scratch directories are byte-identical and an independent CPython oracle
//! can re-derive every hash from the live bytes.
//!
//! AUDIT_ONLY: writes only under the scratch directory passed as argv[1];
//! does not touch the workspace, the portfolio manifest, any locked dataset,
//! or a signed Phase-0 KPI.

use amphora_core::{stable_hash, verify_run, RunArchive, RunArchiveError};
use serde_json::{json, Map, Value};
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

/// verify_run outcome as (variant-or-"Ok", Option<root_hash>).
fn verify_outcome(path: &Path) -> (String, Option<String>) {
    match verify_run(path) {
        Ok(root) => ("Ok".to_string(), Some(root)),
        Err(e) => (variant(&e).to_string(), None),
    }
}

/// Exact shipped Phase-0 KPI construction (run_provenance_phase0_kpi.rs):
/// alternating score/gate events, candidate-{i:03}, generation i/5,
/// payload {index, 100.0 + i*0.1}, final state sealed_at_ms = created + n.
fn build_archive(
    base: &Path,
    run_id: &str,
    campaign: &str,
    created_at_ms: u64,
    events: u64,
) -> PathBuf {
    let manifest = json!({
        "run_id": run_id,
        "schema": "amphora.tui-manifest.v1",
        "campaign": campaign,
        "created_at_ms": created_at_ms,
    });
    let mut archive = RunArchive::create(base, run_id, &manifest).expect("create archive");
    for i in 0..events {
        archive
            .append(
                if i % 2 == 0 { "score" } else { "gate" },
                Some(format!("candidate-{i:03}")),
                (i / 5) as u32,
                json!({"index": i, "value": 100.0 + i as f64 * 0.1}),
            )
            .expect("append event");
    }
    let final_state = json!({
        "sealed_at_ms": created_at_ms + events,
        "candidate_count": events,
        "outcome": "PHASE0_KPI_COMPLETE",
    });
    archive.final_state(&final_state).expect("final state");
    base.join(run_id)
}

/// Fresh 3-event probe archive with a probe-unique run_id.
fn fresh(base: &Path, probe_id: &str) -> PathBuf {
    build_archive(
        base,
        &format!("probe-{probe_id}"),
        "live-runtime-archive-parity-v1",
        20260731,
        3,
    )
}

/// All archive files (sorted by name) as UTF-8 strings.
fn emit_files(path: &Path) -> Value {
    let mut names: Vec<String> = fs::read_dir(path)
        .expect("read_dir")
        .map(|e| e.expect("dir entry").file_name().to_string_lossy().into_owned())
        .collect();
    names.sort();
    let mut m = Map::new();
    for name in names {
        m.insert(
            name.clone(),
            Value::String(fs::read_to_string(path.join(&name)).expect("read file")),
        );
    }
    Value::Object(m)
}

fn edit_events(path: &Path, f: impl Fn(Vec<String>) -> Vec<String>) {
    let s = fs::read_to_string(path.join("events.jsonl")).expect("read events");
    let lines: Vec<String> = s.lines().map(|l| l.to_string()).collect();
    let mut out = f(lines).join("\n");
    out.push('\n');
    fs::write(path.join("events.jsonl"), out).expect("write events");
}

/// Replicates amphora-core write_new_json byte format (to_vec_pretty + '\n')
/// for the hand-constructed G4 archives, minus the create_new requirement.
fn write_pretty(path: &Path, value: &Value) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("serialize");
    bytes.push(b'\n');
    fs::write(path, bytes).expect("write pretty");
}

struct ProbeOut {
    probe_id: &'static str,
    surface: &'static str,
    mutation: &'static str,
    result: String,
    root_hash: Option<String>,
    files: Option<Value>,
}

impl ProbeOut {
    fn to_value(&self) -> Value {
        let mut m = Map::new();
        m.insert("probe_id".into(), json!(self.probe_id));
        m.insert("surface".into(), json!(self.surface));
        m.insert("mutation".into(), json!(self.mutation));
        m.insert("result".into(), json!(self.result));
        m.insert("root_hash".into(), json!(self.root_hash));
        if let Some(f) = &self.files {
            m.insert("files".into(), f.clone());
        }
        Value::Object(m)
    }
}

/// G4: hand-constructed archive whose interior Haber-Stornetta event_hash
/// fields are garbage (never derived from the event seed), but whose
/// provenance file is arithmetically consistent with the recorded bytes.
/// `consistent_chain_root` selects whether provenance.event_chain_root equals
/// the last RECORDED (garbage) event_hash.
fn forged_interior_chain(base: &Path, run_id: &str, consistent_chain_root: bool) -> ProbeOut {
    let dir = base.join(run_id);
    fs::create_dir_all(&dir).expect("mkdir forged");
    let manifest = json!({
        "run_id": run_id,
        "schema": "amphora.tui-manifest.v1",
        "campaign": "live-runtime-archive-parity-v1",
        "created_at_ms": 20260731_u64,
    });
    write_pretty(&dir.join("manifest.json"), &manifest);
    let h1 = "deadbeef".repeat(8);
    let h2 = "cafebabe".repeat(8);
    let e1 = format!(
        "{{\"schema\":\"amphora.tui-event.v1\",\"sequence\":1,\"run_id\":\"{run_id}\",\
         \"event_type\":\"score\",\"candidate_id\":\"candidate-000\",\"generation\":0,\
         \"payload\":{{\"index\":0,\"value\":100.0}},\"event_hash\":\"{h1}\"}}"
    );
    let e2 = format!(
        "{{\"schema\":\"amphora.tui-event.v1\",\"sequence\":2,\"run_id\":\"{run_id}\",\
         \"event_type\":\"gate\",\"candidate_id\":null,\"generation\":0,\
         \"payload\":{{\"index\":1,\"value\":100.1}},\"event_hash\":\"{h2}\"}}"
    );
    let events_bytes = format!("{e1}\n{e2}\n");
    fs::write(dir.join("events.jsonl"), &events_bytes).expect("write forged events");
    let final_state = json!({"outcome": "G4_FORGED", "sealed_at_ms": 20260731_u64});
    write_pretty(&dir.join("final-state.json"), &final_state);
    let chain_root = if consistent_chain_root {
        h2.clone()
    } else {
        raw_sha256(&[])
    };
    let manifest_bytes = fs::read(dir.join("manifest.json")).expect("read forged manifest");
    let seed = json!({
        "run_id": run_id,
        "manifest_sha256": raw_sha256(&manifest_bytes),
        "events_sha256": raw_sha256(events_bytes.as_bytes()),
        "event_chain_root": chain_root,
        "final_state_hash": stable_hash(&final_state),
    });
    let provenance = json!({
        "schema": "amphora.run-provenance.v1",
        "run_id": run_id,
        "manifest_sha256": raw_sha256(&manifest_bytes),
        "events_sha256": raw_sha256(events_bytes.as_bytes()),
        "event_chain_root": if consistent_chain_root { h2.clone() } else { raw_sha256(&[]) },
        "final_state_hash": stable_hash(&final_state),
        "root_hash": stable_hash(&seed),
        "promotion_receipt_eligible": false,
        "signature_status": "UNSIGNED_CONTROLLED_KEY_REQUIRED",
    });
    write_pretty(&dir.join("provenance.json"), &provenance);
    let (result, root_hash) = verify_outcome(&dir);
    ProbeOut {
        probe_id: if consistent_chain_root {
            "forged-interior-chain-consistent-root"
        } else {
            "forged-chain-root-mismatch"
        },
        surface: "events.jsonl interior event_hash fields",
        mutation: if consistent_chain_root {
            "hand-built archive: garbage 64-hex event_hash values never derived from the \
             Haber-Stornetta seed; provenance arithmetically consistent with recorded bytes \
             and recorded (garbage) chain root"
        } else {
            "same garbage interior chain, but provenance.event_chain_root set to \
             raw_sha256(empty) which mismatches the last recorded event_hash"
        },
        result,
        root_hash,
        files: Some(emit_files(&dir)),
    }
}

fn main() {
    let scratch = PathBuf::from(
        std::env::args()
            .nth(1)
            .expect("usage: rp-live-harness <scratch-dir>"),
    );
    fs::create_dir_all(&scratch).expect("scratch dir");

    // ------------------------------------------------------------------
    // Positive scenarios — the 3 shipped Phase-0 KPI constructions plus a
    // unicode/float/snapshot stressor.
    // ------------------------------------------------------------------
    let mut scenarios = Vec::new();
    for (scenario_id, run_id, events) in [
        ("empty", "phase0-kpi-empty", 0_u64),
        ("small", "phase0-kpi-small", 3),
        ("complex", "phase0-kpi-complex", 12),
    ] {
        let path = build_archive(&scratch, run_id, "phase0-kpi-run-provenance", 20260722, events);
        let (result, root_hash) = verify_outcome(&path);
        scenarios.push(json!({
            "scenario_id": scenario_id,
            "run_id": run_id,
            "n_events": events,
            "verify_result": result,
            "verify_root_hash": root_hash,
            "files": emit_files(&path),
        }));
    }
    {
        // Unicode + adversarial-float + snapshot scenario (new construction).
        let run_id = "live-unicode-snapshot";
        let manifest = json!({
            "run_id": run_id,
            "schema": "amphora.tui-manifest.v1",
            "campaign": "live-runtime-archive-parity-v1",
            "created_at_ms": 20260731_u64,
        });
        let mut archive = RunArchive::create(&scratch, run_id, &manifest).expect("create unicode");
        archive
            .append(
                "score",
                Some("candidate-α".to_string()),
                0,
                json!({"note": "ε≥0.5°C", "x": 0.1_f64 + 0.2_f64, "y": 100.55_f64, "z": -0.0_f64}),
            )
            .expect("append unicode");
        archive
            .append("gate", None, 0, json!({"index": 1_u64, "value": 100.1_f64}))
            .expect("append second");
        archive
            .snapshot(1, &json!({"phase": "mid", "count": 1_u64}))
            .expect("snapshot");
        archive
            .final_state(&json!({
                "sealed_at_ms": 20260733_u64,
                "candidate_count": 2_u64,
                "outcome": "LIVE_PARITY_COMPLETE",
            }))
            .expect("final unicode");
        let path = scratch.join(run_id);
        let (result, root_hash) = verify_outcome(&path);
        scenarios.push(json!({
            "scenario_id": "unicode-float-snapshot",
            "run_id": run_id,
            "n_events": 2,
            "verify_result": result,
            "verify_root_hash": root_hash,
            "files": emit_files(&path),
        }));
    }
    // Legacy-mirror scenarios: the EXACT archive content of the signed 2026
    // hash-chain-oracle-parity-v1 G1 archives (pos-empty/small/complex), now
    // built by the LIVE runtime for the first time, so the byte-format
    // fidelity of that receipt's Python mirror is measurable against ground
    // truth.
    for (scenario_id, run_id, events) in [
        ("legacy-empty", "pos-empty", 0_u64),
        ("legacy-small", "pos-small", 3),
        ("legacy-complex", "pos-complex", 12),
    ] {
        let manifest = json!({
            "schema": "mvp20.run_manifest.v1",
            "run_id": run_id,
            "scope": "solvent-borne two-component epoxy-polyamide marine coating",
            "monte_carlo_seed": 2001_u64,
            "n_events_planned": events,
        });
        let mut archive = RunArchive::create(&scratch, run_id, &manifest).expect("create legacy");
        let types = ["PROPOSED", "SCORED", "RANKED", "GATED"];
        for i in 0..events {
            archive
                .append(
                    types[(i % 4) as usize],
                    Some(format!("cand-{i:03}")),
                    (i / 4) as u32,
                    json!({"idx": i, "note": "dgeba-amine", "delta": i * 3}),
                )
                .expect("append legacy");
        }
        let best = if events == 0 {
            Value::Null
        } else {
            Value::String(format!("cand-{:03}", events - 1))
        };
        let final_state = json!({
            "run_id": run_id,
            "status": "COMPLETE",
            "n_events": events,
            "best_candidate": best,
        });
        archive.final_state(&final_state).expect("final legacy");
        let path = scratch.join(run_id);
        let (result, root_hash) = verify_outcome(&path);
        scenarios.push(json!({
            "scenario_id": scenario_id,
            "run_id": run_id,
            "n_events": events,
            "verify_result": result,
            "verify_root_hash": root_hash,
            "files": emit_files(&path),
        }));
    }

    // ------------------------------------------------------------------
    // G2 taxonomy + G3 surface probes. Each probe mutates a FRESH archive.
    // ------------------------------------------------------------------
    let mut probes: Vec<ProbeOut> = Vec::new();

    // G2.1 Exists — duplicate create of the same run_id.
    {
        let _path = fresh(&scratch, "exists");
        let manifest = json!({"run_id": "probe-exists", "schema": "amphora.tui-manifest.v1"});
        let result = match RunArchive::create(&scratch, "probe-exists", &manifest) {
            Ok(_) => "Ok".to_string(),
            Err(e) => variant(&e).to_string(),
        };
        probes.push(ProbeOut {
            probe_id: "exists-duplicate-create",
            surface: "archive directory",
            mutation: "RunArchive::create called twice with the same run_id",
            result,
            root_hash: None,
            files: None,
        });
    }
    // G2.2 Integrity — non-contiguous sequence.
    {
        let path = fresh(&scratch, "seqgap");
        edit_events(&path, |mut lines| {
            lines[1] = lines[1].replacen("\"sequence\":2,", "\"sequence\":3,", 1);
            lines
        });
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "integrity-noncontiguous-sequence",
            surface: "events.jsonl",
            mutation: "second event renumbered sequence 2 -> 3",
            result,
            root_hash,
            files: None,
        });
    }
    // G2.3 Integrity — root_hash flipped.
    {
        let path = fresh(&scratch, "rootflip");
        let raw = fs::read_to_string(path.join("provenance.json")).expect("read prov");
        let v: Value = serde_json::from_str(&raw).expect("parse prov");
        let root = v["root_hash"].as_str().expect("root").to_string();
        let flipped = if root.starts_with('0') {
            format!("1{}", &root[1..])
        } else {
            format!("0{}", &root[1..])
        };
        fs::write(path.join("provenance.json"), raw.replacen(&root, &flipped, 1))
            .expect("write prov");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "integrity-root-hash-flip",
            surface: "provenance.json",
            mutation: "first hex char of root_hash flipped",
            result,
            root_hash,
            files: None,
        });
    }
    // G2.4 Integrity — root_hash key removed.
    {
        let path = fresh(&scratch, "rootmissing");
        let raw = fs::read_to_string(path.join("provenance.json")).expect("read prov");
        let mut v: Value = serde_json::from_str(&raw).expect("parse prov");
        v.as_object_mut().expect("object").remove("root_hash");
        fs::write(path.join("provenance.json"), serde_json::to_string(&v).expect("ser"))
            .expect("write prov");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "integrity-missing-root-hash",
            surface: "provenance.json",
            mutation: "root_hash key removed",
            result,
            root_hash,
            files: None,
        });
    }
    // G2.5 Integrity — manifest byte appended.
    {
        let path = fresh(&scratch, "manifestbyte");
        let mut bytes = fs::read(path.join("manifest.json")).expect("read manifest");
        bytes.push(b' ');
        fs::write(path.join("manifest.json"), bytes).expect("write manifest");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "integrity-manifest-byte-append",
            surface: "manifest.json",
            mutation: "single space byte appended",
            result,
            root_hash,
            files: None,
        });
    }
    // G2.6 Io — manifest.json deleted.
    {
        let path = fresh(&scratch, "iomanifest");
        fs::remove_file(path.join("manifest.json")).expect("rm manifest");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "io-missing-manifest",
            surface: "manifest.json",
            mutation: "file deleted",
            result,
            root_hash,
            files: None,
        });
    }
    // G2.7 Io — provenance.json deleted.
    {
        let path = fresh(&scratch, "ioprovenance");
        fs::remove_file(path.join("provenance.json")).expect("rm provenance");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "io-missing-provenance",
            surface: "provenance.json",
            mutation: "file deleted",
            result,
            root_hash,
            files: None,
        });
    }
    // G2.8 Json — malformed provenance.json.
    {
        let path = fresh(&scratch, "jsonprov");
        fs::write(path.join("provenance.json"), "{invalid").expect("write prov");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "json-malformed-provenance",
            surface: "provenance.json",
            mutation: "file replaced with '{invalid' (syntax error, lenient serde path)",
            result,
            root_hash,
            files: None,
        });
    }
    // G2.9 Json — event shape mismatch (strict parse OK, from_value fails).
    {
        let path = fresh(&scratch, "jsonshape");
        edit_events(&path, |mut lines| {
            lines[0] = lines[0].replacen("\"sequence\":1,", "\"sequence\":\"1\",", 1);
            lines
        });
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "json-event-shape-string-sequence",
            surface: "events.jsonl",
            mutation: "first event sequence changed from number 1 to string \"1\"",
            result,
            root_hash,
            files: None,
        });
    }
    // G2.10 Contract — duplicate JSON key in an event line (same value).
    {
        let path = fresh(&scratch, "dupkeyevent");
        edit_events(&path, |mut lines| {
            lines[0] = lines[0].replacen(
                "\"generation\":0,",
                "\"generation\":0,\"generation\":0,",
                1,
            );
            lines
        });
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "contract-duplicate-key-event",
            surface: "events.jsonl",
            mutation: "generation key duplicated with identical value (semantics-preserving under last-wins)",
            result,
            root_hash,
            files: None,
        });
    }
    // G2.11 Contract — truncated event line (strict parser wraps syntax errors).
    {
        let path = fresh(&scratch, "truncline");
        edit_events(&path, |mut lines| {
            lines[0] = "{\"schema\":".to_string();
            lines
        });
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "contract-truncated-event-line",
            surface: "events.jsonl",
            mutation: "first event line truncated to '{\"schema\":'",
            result,
            root_hash,
            files: None,
        });
    }

    // G3 — representation-malleability surface matrix.
    // G3.1 events.jsonl key reorder (parsed value identical).
    {
        let path = fresh(&scratch, "eventsreorder");
        edit_events(&path, |mut lines| {
            let v: Value = serde_json::from_str(&lines[0]).expect("parse event");
            lines[0] = serde_json::to_string(&v).expect("ser event");
            lines
        });
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "surface-events-key-reorder",
            surface: "events.jsonl",
            mutation: "first event re-serialized with sorted keys; parsed value identical",
            result,
            root_hash,
            files: None,
        });
    }
    // G3.2 final-state duplicate key, same value.
    {
        let path = fresh(&scratch, "fsdupkey");
        let v: Value =
            serde_json::from_str(&fs::read_to_string(path.join("final-state.json")).expect("read"))
                .expect("parse");
        let compact = serde_json::to_string(&v).expect("ser");
        let injected = format!(
            "{{\"outcome\":\"PHASE0_KPI_COMPLETE\",{}",
            &compact[1..]
        );
        fs::write(path.join("final-state.json"), injected).expect("write");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "surface-final-state-duplicate-key",
            surface: "final-state.json",
            mutation: "outcome key duplicated with identical value; last-wins parse value unchanged",
            result,
            root_hash,
            files: Some(emit_files(&path)),
        });
    }
    // G3.3 final-state reformat (compact).
    {
        let path = fresh(&scratch, "fsreformat");
        let v: Value =
            serde_json::from_str(&fs::read_to_string(path.join("final-state.json")).expect("read"))
                .expect("parse");
        fs::write(path.join("final-state.json"), serde_json::to_string(&v).expect("ser"))
            .expect("write");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "surface-final-state-reformat-compact",
            surface: "final-state.json",
            mutation: "pretty JSON rewritten compact; parsed value identical",
            result,
            root_hash,
            files: None,
        });
    }
    // G3.4 provenance duplicate root_hash shadow (decoy first, honest last).
    {
        let path = fresh(&scratch, "provshadow");
        let v: Value =
            serde_json::from_str(&fs::read_to_string(path.join("provenance.json")).expect("read"))
                .expect("parse");
        let compact = serde_json::to_string(&v).expect("ser");
        let decoy = "0".repeat(64);
        let injected = format!("{{\"root_hash\":\"{}\",{}", decoy, &compact[1..]);
        fs::write(path.join("provenance.json"), injected).expect("write");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "surface-provenance-duplicate-root-shadow",
            surface: "provenance.json",
            mutation: "decoy root_hash of 64 zeros inserted as FIRST key; honest root_hash later; lenient last-wins",
            result,
            root_hash,
            files: Some(emit_files(&path)),
        });
    }
    // G3.5 provenance reformat (compact).
    {
        let path = fresh(&scratch, "provreformat");
        let v: Value =
            serde_json::from_str(&fs::read_to_string(path.join("provenance.json")).expect("read"))
                .expect("parse");
        fs::write(path.join("provenance.json"), serde_json::to_string(&v).expect("ser"))
            .expect("write");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "surface-provenance-reformat-compact",
            surface: "provenance.json",
            mutation: "pretty JSON rewritten compact; parsed value identical",
            result,
            root_hash,
            files: None,
        });
    }
    // G3.6 manifest reformat (compact) — byte-bound, expected to fail closed.
    {
        let path = fresh(&scratch, "manifestreformat");
        let v: Value =
            serde_json::from_str(&fs::read_to_string(path.join("manifest.json")).expect("read"))
                .expect("parse");
        fs::write(path.join("manifest.json"), serde_json::to_string(&v).expect("ser"))
            .expect("write");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "surface-manifest-reformat-compact",
            surface: "manifest.json",
            mutation: "pretty JSON rewritten compact; parsed value identical",
            result,
            root_hash,
            files: None,
        });
    }
    // G3.7 snapshot tamper — snapshots are outside verify_run entirely.
    {
        let run_id = "probe-snapshottamper";
        let manifest = json!({
            "run_id": run_id,
            "schema": "amphora.tui-manifest.v1",
            "campaign": "live-runtime-archive-parity-v1",
            "created_at_ms": 20260731_u64,
        });
        let mut archive = RunArchive::create(&scratch, run_id, &manifest).expect("create snap");
        archive
            .append("score", Some("candidate-000".to_string()), 0, json!({"index": 0_u64}))
            .expect("append snap");
        archive.snapshot(1, &json!({"phase": "mid"})).expect("snapshot");
        archive
            .final_state(&json!({"outcome": "SNAP_DONE"}))
            .expect("final snap");
        let path = scratch.join(run_id);
        fs::write(path.join("snapshot-000001.json"), "{\"tampered\":true}\n").expect("tamper snap");
        let (result, root_hash) = verify_outcome(&path);
        probes.push(ProbeOut {
            probe_id: "surface-snapshot-tamper",
            surface: "snapshot-000001.json",
            mutation: "snapshot file replaced wholesale with {\"tampered\":true}",
            result,
            root_hash,
            files: None,
        });
    }

    // G4 — interior Haber-Stornetta chain verification.
    probes.push(forged_interior_chain(&scratch, "g4-forged-chain", true));
    probes.push(forged_interior_chain(&scratch, "g4-chain-root-mismatch", false));

    let out = json!({
        "schema": "amphora.run-provenance.live-harness-output.v1",
        "harness": "rp-live-harness v1: links amphora-core; calls real RunArchive::create/append/snapshot/final_state and verify_run",
        "scenarios": scenarios,
        "probes": probes.iter().map(ProbeOut::to_value).collect::<Vec<_>>(),
    });
    println!("{}", serde_json::to_string(&out).expect("serialize output"));
}
