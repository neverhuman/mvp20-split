// amphora-candidate-contract score-envelope-optimizer-admission-v1 : Oracle B (runtime).
//
// For every corpus case (one score envelope per file) this wraps the envelope into
// the exact shape the optimizer front door consumes -- {"score_envelopes": [env]} --
// and reports the compiled amphora-core admission verdict obtained through the
// PUBLIC rank_candidates entry point with an empty KPI profile (no objectives, no
// hard constraints, no display KPIs).  rank_candidates internally runs the private
// optimizer_envelopes extraction followed by authorize_optimizer_request; the
// resulting `feasible` flag is true if and only if BOTH succeeded, i.e. the
// envelope was admitted by the front door.
//
// Verdict-level oracle only: ADMIT / REJECT.  Reason-level taxonomy is not claimed.
// AUDIT_ONLY diagnostic harness; does not modify tree state.
use amphora_core::{rank_candidates, KpiProfile};
use serde_json::{json, Value};
use std::{collections::BTreeMap, fs};

fn empty_profile() -> KpiProfile {
    KpiProfile {
        schema: "amphora.kpi-profile.v1".into(),
        profile_id: "score-envelope-optimizer-admission-v1-empty".into(),
        objectives: Vec::new(),
        hard_constraints: Vec::new(),
        display_kpis: Vec::new(),
    }
}

fn main() {
    let dir = std::env::args().nth(1).expect("corpus dir arg");
    let profile = empty_profile();
    let mut out: BTreeMap<String, Value> = BTreeMap::new();
    let mut entries: Vec<_> = fs::read_dir(&dir)
        .expect("read corpus dir")
        .map(|e| e.unwrap().path())
        .collect();
    entries.sort();
    for path in entries {
        let name = path.file_name().unwrap().to_string_lossy().to_string();
        if name.starts_with('_') || !name.ends_with(".json") {
            continue;
        }
        let case_id = name.trim_end_matches(".json").to_string();
        let bytes = fs::read(&path).expect("read case");
        let envelope: Value = match serde_json::from_slice(&bytes) {
            Ok(v) => v,
            Err(_) => {
                out.insert(
                    case_id,
                    json!({"runtime_verdict": "REJECT", "detail": "parse_failure"}),
                );
                continue;
            }
        };
        let result = json!({
            "candidate": {"candidate_id": envelope.get("candidate_id").cloned()
                .unwrap_or(Value::String("unknown".into()))},
            "score_envelopes": [envelope],
        });
        // Two independent constructions of the same admission decision, to confirm the
        // runtime oracle is itself deterministic within a single process.
        let first = rank_candidates(std::slice::from_ref(&result), &profile);
        let second = rank_candidates(std::slice::from_ref(&result), &profile);
        let feasible = first.first().map(|c| c.feasible).unwrap_or(false);
        let feasible2 = second.first().map(|c| c.feasible).unwrap_or(false);
        let failed_modules = first.first().map(|c| c.failed_modules).unwrap_or(0);
        out.insert(
            case_id,
            json!({
                "runtime_verdict": if feasible { "ADMIT" } else { "REJECT" },
                "detail": {
                    "feasible": feasible,
                    "stable_within_process": feasible == feasible2,
                    "non_scored_module_count": failed_modules,
                },
            }),
        );
    }
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
