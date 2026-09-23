use amphora_solver_lab::oracle::{sha256_hex, OracleError, SourceOracle};
use std::fs;
use std::path::PathBuf;

fn temp_root(tag: &str) -> PathBuf {
    let dir = std::env::temp_dir().join(format!(
        "amphora-solver-lab-oracle-test-{}-{}",
        std::process::id(),
        tag
    ));
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(dir.join("data")).expect("mkdir");
    dir
}

fn write_pins(root: &PathBuf, sha: &str) -> PathBuf {
    let pins_path = root.join("pins.json");
    let pins = serde_json::json!({
        "schema": "amphora.solver-lab.source-pins.v1",
        "pins": [
            {"logical_id": "probe", "rel_path": "data/probe.json", "sha256": sha}
        ]
    });
    fs::write(&pins_path, serde_json::to_vec_pretty(&pins).unwrap()).expect("write pins");
    pins_path
}

#[test]
fn pinned_source_reads_and_records_provenance() {
    let root = temp_root("ok");
    let body = br#"{"value": 42.0}"#;
    fs::write(root.join("data/probe.json"), body).unwrap();
    let pins_path = write_pins(&root, &sha256_hex(body));
    let oracle = SourceOracle::from_pins_file(root.clone(), &pins_path).expect("pins load");
    let reading = oracle.read("probe").expect("pinned read must succeed");
    assert_eq!(reading.rel_path, "data/probe.json");
    assert_eq!(reading.sha256, sha256_hex(body));
    assert_eq!(reading.value["value"].as_f64(), Some(42.0));
    let _ = fs::remove_dir_all(&root);
}

#[test]
fn tampered_source_is_refused() {
    let root = temp_root("tamper");
    let body = br#"{"value": 42.0}"#;
    fs::write(root.join("data/probe.json"), body).unwrap();
    let pins_path = write_pins(&root, &sha256_hex(body));
    let oracle = SourceOracle::from_pins_file(root.clone(), &pins_path).expect("pins load");

    // Tamper: a one-character semantic mutation after pinning.
    fs::write(root.join("data/probe.json"), br#"{"value": 43.0}"#).unwrap();
    let err = oracle.read("probe").expect_err("tampered source must be refused");
    match err {
        OracleError::PinMismatch { .. } => {}
        other => panic!("expected PinMismatch, got {other:?}"),
    }
    let _ = fs::remove_dir_all(&root);
}

#[test]
fn unpinned_logical_id_is_refused() {
    let root = temp_root("unpinned");
    let body = br#"{}"#;
    fs::write(root.join("data/probe.json"), body).unwrap();
    let pins_path = write_pins(&root, &sha256_hex(body));
    let oracle = SourceOracle::from_pins_file(root.clone(), &pins_path).expect("pins load");
    let err = oracle.read("not_registered").expect_err("unpinned id must be refused");
    match err {
        OracleError::NoSuchPin(id) => assert_eq!(id, "not_registered"),
        other => panic!("expected NoSuchPin, got {other:?}"),
    }
    let _ = fs::remove_dir_all(&root);
}

#[test]
fn live_tree_pins_all_verify() {
    // The crate's own pins file must verify against the live tree: every
    // pinned source readable, sha-matched, and parseable. This is the same
    // path the demos take; a mismatch here means a pinned upstream artifact
    // changed and the demos would (correctly) refuse to run.
    let oracle = SourceOracle::pinned_default().expect("crate pins load");
    let pins = oracle.pin_list();
    assert_eq!(pins.len(), 7, "expected 7 pinned sources");
    for pin in pins {
        let reading = oracle
            .read(&pin.logical_id)
            .unwrap_or_else(|e| panic!("pinned source {} failed: {e}", pin.logical_id));
        assert_eq!(reading.sha256, pin.sha256);
    }
}
