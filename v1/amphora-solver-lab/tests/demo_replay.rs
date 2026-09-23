//! Two-replay byte-stability of the demo diagnostics: (a) two fresh
//! in-process replays must serialize to identical bytes; (b) the shipped
//! evidence pair (diagnostic.canonical.json vs diagnostic.runB.json), which
//! was produced by two independent process invocations, must be
//! byte-identical.

use amphora_solver_lab::demos;
use std::path::Path;

const DEMO_DIRS: [(&str, &str); 3] = [
    ("p1", "p1-voc-min-solvent-blend"),
    ("p3", "p3-hazard-constrained-hardener-selection"),
    ("p4", "p4-2to4-full-factorial-screen"),
];

#[test]
fn fresh_two_replay_is_byte_identical() {
    for (demo, _) in DEMO_DIRS {
        let a = demos::run(demo).unwrap_or_else(|e| panic!("demo {demo} run A failed: {e}"));
        let b = demos::run(demo).unwrap_or_else(|e| panic!("demo {demo} run B failed: {e}"));
        assert_eq!(a, b, "demo {demo}: two fresh replays must be byte-identical");
        assert!(!a.is_empty());
    }
}

#[test]
fn shipped_evidence_pairs_are_byte_identical() {
    let base = Path::new(env!("CARGO_MANIFEST_DIR")).join("evidence/phase0/demos");
    for (demo, dir) in DEMO_DIRS {
        let canonical = base.join(dir).join("diagnostic.canonical.json");
        let run_b = base.join(dir).join("diagnostic.runB.json");
        let ca = std::fs::read(&canonical)
            .unwrap_or_else(|e| panic!("demo {demo}: missing shipped {}: {e}", canonical.display()));
        let cb = std::fs::read(&run_b)
            .unwrap_or_else(|e| panic!("demo {demo}: missing shipped {}: {e}", run_b.display()));
        assert_eq!(
            ca, cb,
            "demo {demo}: shipped canonical and runB diagnostics must be byte-identical"
        );
    }
}

#[test]
fn diagnostics_carry_bounded_authority() {
    for (demo, _) in DEMO_DIRS {
        let bytes = demos::run(demo).unwrap_or_else(|e| panic!("demo {demo} failed: {e}"));
        let v: serde_json::Value = serde_json::from_slice(&bytes).expect("valid json");
        assert_eq!(v["authority"].as_str(), Some("AUDIT_ONLY"), "demo {demo}");
        assert_eq!(
            v["claim_locks"]["promotes_authority"].as_bool(),
            Some(false),
            "demo {demo}"
        );
        assert_eq!(
            v["claim_locks"]["modifies_manifest"].as_bool(),
            Some(false),
            "demo {demo}"
        );
        assert!(v["sources"].as_array().map(|a| !a.is_empty()).unwrap_or(false), "demo {demo} must cite sources");
        for s in v["sources"].as_array().unwrap() {
            let sha = s["sha256"].as_str().unwrap_or_default();
            assert_eq!(sha.len(), 64, "demo {demo}: source sha256 must be recorded");
        }
    }
}
