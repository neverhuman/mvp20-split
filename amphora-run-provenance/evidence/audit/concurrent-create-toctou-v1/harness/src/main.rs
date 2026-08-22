// LIVE differential/race harness for amphora-run-provenance
// (evidence/audit/concurrent-create-toctou-v1).
//
// Claim under attack: the shipped Phase-0 KPI
// (evidence/phase0/kpis/run-provenance-hash-chain-integrity-kpi.v1.json)
// metric "duplicate_archive_create_rejected_via_exists_rate" (observed 1.0,
// sample_size 3, passed true) plus its fitted_or_physical_model_artifact
// prediction_rule step (1): "verify base/run_id does not already exist
// (else Exists)" -- i.e. RunArchive::create categorically rejects a
// duplicate run_id via RunArchiveError::Exists.
//
// That KPI's own probe is SEQUENTIAL: create() is called once, then called
// again against the same already-fully-formed archive. This harness instead
// calls the real RunArchive::create with the SAME run_id from many OS
// threads simultaneously (Barrier-synchronized), which is the situation the
// module's own consumer (amphora-cli/src/main.rs run subcommand, invoked by
// concurrently-issued production requests) is actually exposed to.
//
// Read from amphora-core/src/lib.rs:
//   RunArchive::create(base, run_id, manifest):
//     1. path = base.join(run_id)
//     2. if path.exists() { return Err(Exists) }      <- TOCTOU check
//     3. fs::create_dir_all(&path)?                    <- tolerant of races
//        (std create_dir_all treats "already a directory" as success)
//     4. OpenOptions::new().create_new(true).open(manifest.json)?
//        <- THIS is the real atomic guard (O_CREAT|O_EXCL); on a race the
//        loser gets io::ErrorKind::AlreadyExists, which the #[from] impl
//        maps to RunArchiveError::Io, NOT RunArchiveError::Exists.
//
// Prediction: under a genuine simultaneous race, losing threads will return
// RunArchiveError::Io (not Exists), refuting the KPI's categorical "(else
// Exists)" prediction rule and the "_via_exists" metric name/claim.
use amphora_core::{RunArchive, RunArchiveError};
use serde_json::json;
use std::path::PathBuf;
use std::sync::{Arc, Barrier};
use std::thread;

const N_THREADS: usize = 8;
const N_TRIALS: usize = 40;

#[derive(Default, Debug, Clone, serde::Serialize)]
struct TrialOutcome {
    trial: usize,
    ok_count: usize,
    exists_count: usize,
    io_count: usize,
    other_count: usize,
    variants: Vec<String>,
}

fn classify(e: &RunArchiveError) -> &'static str {
    match e {
        RunArchiveError::Exists(_) => "Exists",
        RunArchiveError::Io(_) => "Io",
        RunArchiveError::Integrity(_) => "Integrity",
        RunArchiveError::Json(_) => "Json",
        RunArchiveError::Contract(_) => "Contract",
    }
}

fn run_race_trial(trial: usize, base: &PathBuf, run_id: &str) -> TrialOutcome {
    std::fs::create_dir_all(base).unwrap();
    let barrier = Arc::new(Barrier::new(N_THREADS));
    let mut handles = Vec::new();
    for _t in 0..N_THREADS {
        let barrier = Arc::clone(&barrier);
        let base = base.clone();
        let run_id = run_id.to_string();
        handles.push(thread::spawn(move || {
            let manifest = json!({
                "schema": "amphora.run-manifest.v1",
                "run_id": run_id,
            });
            barrier.wait();
            RunArchive::create(&base, &run_id, &manifest)
        }));
    }
    let mut outcome = TrialOutcome {
        trial,
        ..Default::default()
    };
    for h in handles {
        match h.join().unwrap() {
            Ok(_archive) => {
                outcome.ok_count += 1;
                outcome.variants.push("Ok".to_string());
            }
            Err(e) => {
                let v = classify(&e);
                outcome.variants.push(v.to_string());
                match v {
                    "Exists" => outcome.exists_count += 1,
                    "Io" => outcome.io_count += 1,
                    _ => outcome.other_count += 1,
                }
            }
        }
    }
    // Thread win/loss identity and OS scheduling order are inherently
    // non-deterministic; sort so the emitted diagnostic depends only on the
    // deterministic MULTISET of outcomes per trial (the quantity the
    // two-replay byte-stability gate is asserting over), not on which
    // specific thread happened to win the race.
    outcome.variants.sort();
    outcome
}

fn run_control_trial(trial: usize, base: &PathBuf) -> TrialOutcome {
    std::fs::create_dir_all(base).unwrap();
    let barrier = Arc::new(Barrier::new(N_THREADS));
    let mut handles = Vec::new();
    for t in 0..N_THREADS {
        let barrier = Arc::clone(&barrier);
        let base = base.clone();
        let run_id = format!("control-run-{trial}-{t}");
        handles.push(thread::spawn(move || {
            let manifest = json!({
                "schema": "amphora.run-manifest.v1",
                "run_id": run_id,
            });
            barrier.wait();
            RunArchive::create(&base, &run_id, &manifest)
        }));
    }
    let mut outcome = TrialOutcome {
        trial,
        ..Default::default()
    };
    for h in handles {
        match h.join().unwrap() {
            Ok(_archive) => {
                outcome.ok_count += 1;
                outcome.variants.push("Ok".to_string());
            }
            Err(e) => {
                let v = classify(&e);
                outcome.variants.push(v.to_string());
                match v {
                    "Exists" => outcome.exists_count += 1,
                    "Io" => outcome.io_count += 1,
                    _ => outcome.other_count += 1,
                }
            }
        }
    }
    outcome.variants.sort();
    outcome
}

fn main() {
    let scratch_root = std::env::var("TOCTOU_SCRATCH")
        .unwrap_or_else(|_| "/tmp/rp_toctou_scratch".to_string());
    let _ = std::fs::remove_dir_all(&scratch_root);

    // G0 -- RACE: same run_id, N_THREADS simultaneous create() calls, over
    // N_TRIALS independent trials (fresh base dir each trial) to amplify the
    // race window across OS scheduling variance.
    let mut race_trials = Vec::new();
    for trial in 0..N_TRIALS {
        let base = PathBuf::from(format!("{scratch_root}/race/trial-{trial}"));
        race_trials.push(run_race_trial(trial, &base, "shared-collision-run-id"));
    }

    // G1 -- CONTROL: distinct run_ids per thread, same concurrency pattern.
    // Expect 0 errors of any kind -- proves the harness's threading/barrier
    // machinery is not itself the source of any observed error, and that
    // amphora-core's create() is not simply flaky under concurrency in
    // general (only under a genuine shared-key race).
    let mut control_trials = Vec::new();
    for trial in 0..N_TRIALS {
        let base = PathBuf::from(format!("{scratch_root}/control/trial-{trial}"));
        control_trials.push(run_control_trial(trial, &base));
    }

    let race_ok: usize = race_trials.iter().map(|t| t.ok_count).sum();
    let race_exists: usize = race_trials.iter().map(|t| t.exists_count).sum();
    let race_io: usize = race_trials.iter().map(|t| t.io_count).sum();
    let race_other: usize = race_trials.iter().map(|t| t.other_count).sum();

    let control_ok: usize = control_trials.iter().map(|t| t.ok_count).sum();
    let control_exists: usize = control_trials.iter().map(|t| t.exists_count).sum();
    let control_io: usize = control_trials.iter().map(|t| t.io_count).sum();
    let control_other: usize = control_trials.iter().map(|t| t.other_count).sum();

    let trials_with_multiple_ok = race_trials.iter().filter(|t| t.ok_count > 1).count();
    let trials_with_zero_ok = race_trials.iter().filter(|t| t.ok_count == 0).count();
    let trials_with_io_loser = race_trials.iter().filter(|t| t.io_count > 0).count();
    let trials_with_exists_loser = race_trials
        .iter()
        .filter(|t| t.exists_count > 0 && t.io_count == 0)
        .count();

    let out = json!({
        "schema": "amphora.run-provenance.concurrent-create-toctou.v1",
        "n_threads_per_trial": N_THREADS,
        "n_trials": N_TRIALS,
        "race": {
            "shared_run_id": "shared-collision-run-id",
            "total_ok": race_ok,
            "total_exists_errors": race_exists,
            "total_io_errors": race_io,
            "total_other_errors": race_other,
            "trials_with_more_than_one_ok_result": trials_with_multiple_ok,
            "trials_with_zero_ok_result": trials_with_zero_ok,
            "trials_with_at_least_one_io_loser": trials_with_io_loser,
            "trials_with_only_exists_losers": trials_with_exists_loser,
            "per_trial": race_trials,
        },
        "control_distinct_run_ids": {
            "total_ok": control_ok,
            "total_exists_errors": control_exists,
            "total_io_errors": control_io,
            "total_other_errors": control_other,
        },
        "kpi_claim_under_test": {
            "metric": "duplicate_archive_create_rejected_via_exists_rate",
            "kpi_path": "amphora-run-provenance/evidence/phase0/kpis/run-provenance-hash-chain-integrity-kpi.v1.json",
            "prediction_rule_step_1": "verify base/run_id does not already exist (else Exists)",
        },
        "refuted": trials_with_io_loser > 0,
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
