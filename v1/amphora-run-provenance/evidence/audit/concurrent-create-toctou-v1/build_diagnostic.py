#!/usr/bin/env python3
"""Deterministic (no wall-clock, no RNG) diagnostic builder for
amphora-run-provenance concurrent-create-toctou-v1.

Reads the two PINNED raw outputs of the live Rust race harness
(race_raw_output.v1.json, race_raw_output_replicate.v1.json -- two
independent live executions of rp-concurrent-create-toctou-harness against
the real amphora_core::RunArchive::create, each running 40 barrier-
synchronized 8-thread trials against a SHARED run_id plus a 40-trial
distinct-run_id control) and computes a pure summary over that fixed input.
The live race itself is genuinely non-deterministic (OS thread-scheduling
timing); THIS script is not -- it is a deterministic function of the two
pinned JSON files checked into this study directory, so running it twice
produces a byte-identical diagnostic (the two-replay gate below applies to
this summarization step, exactly as the module's precedent study
fixed-seed-replay-determinism-v1 pins its two source archives and computes
a deterministic diagnostic over them).
"""
import hashlib
import json
from pathlib import Path

STUDY = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-run-provenance/"
             "evidence/audit/concurrent-create-toctou-v1")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def summarize(raw):
    race = raw["race"]
    control = raw["control_distinct_run_ids"]
    per_trial = race["per_trial"]
    trials_exact_1ok_rest_io = sum(
        1 for t in per_trial
        if t["ok_count"] == 1 and t["exists_count"] == 0
        and t["io_count"] == raw["n_threads_per_trial"] - 1
    )
    trials_exact_1ok_rest_not_all_io = sum(
        1 for t in per_trial
        if t["ok_count"] == 1 and t["io_count"] < raw["n_threads_per_trial"] - 1
    )
    return {
        "n_threads_per_trial": raw["n_threads_per_trial"],
        "n_trials": raw["n_trials"],
        "race_total_ok": race["total_ok"],
        "race_total_exists_errors": race["total_exists_errors"],
        "race_total_io_errors": race["total_io_errors"],
        "race_total_other_errors": race["total_other_errors"],
        "race_trials_with_more_than_one_ok": race["trials_with_more_than_one_ok_result"],
        "race_trials_with_zero_ok": race["trials_with_zero_ok_result"],
        "race_trials_with_at_least_one_io_loser": race["trials_with_at_least_one_io_loser"],
        "race_trials_with_only_exists_losers": race["trials_with_only_exists_losers"],
        "race_trials_exact_1ok_allrest_io": trials_exact_1ok_rest_io,
        "race_trials_1ok_partial_io": trials_exact_1ok_rest_not_all_io,
        "control_total_ok": control["total_ok"],
        "control_total_exists_errors": control["total_exists_errors"],
        "control_total_io_errors": control["total_io_errors"],
        "control_total_other_errors": control["total_other_errors"],
        "control_no_archive_ever_lost_a_race_it_should_have_won": (
            control["total_ok"] == raw["n_threads_per_trial"] * raw["n_trials"]
            and control["total_exists_errors"] == 0
            and control["total_io_errors"] == 0
        ),
    }


runA = json.loads((STUDY / "race_raw_output.v1.json").read_bytes())
runB = json.loads((STUDY / "race_raw_output_replicate.v1.json").read_bytes())

sA = summarize(runA)
sB = summarize(runB)

losers_A = sA["race_total_exists_errors"] + sA["race_total_io_errors"] + sA["race_total_other_errors"]
losers_B = sB["race_total_exists_errors"] + sB["race_total_io_errors"] + sB["race_total_other_errors"]
io_fraction_A = sA["race_total_io_errors"] / losers_A if losers_A else None
io_fraction_B = sB["race_total_io_errors"] / losers_B if losers_B else None
exists_fraction_A = sA["race_total_exists_errors"] / losers_A if losers_A else None
exists_fraction_B = sB["race_total_exists_errors"] / losers_B if losers_B else None

diagnostic = {
    "schema": "amphora.run-provenance.concurrent-create-toctou.diagnostic.v1",
    "pinned_inputs": {
        "race_raw_output.v1.json": sha((STUDY / "race_raw_output.v1.json").read_bytes()),
        "race_raw_output_replicate.v1.json": sha((STUDY / "race_raw_output_replicate.v1.json").read_bytes()),
    },
    "independent_live_execution_A": sA,
    "independent_live_execution_B": sB,
    "cross_execution_agreement": {
        "both_executions_never_saw_more_than_one_winner_per_trial": (
            sA["race_trials_with_more_than_one_ok"] == 0
            and sB["race_trials_with_more_than_one_ok"] == 0
        ),
        "both_executions_never_saw_zero_winners_per_trial": (
            sA["race_trials_with_zero_ok"] == 0 and sB["race_trials_with_zero_ok"] == 0
        ),
        "both_executions_saw_io_losers_in_every_race_trial": (
            sA["race_trials_with_at_least_one_io_loser"] == sA["n_trials"]
            and sB["race_trials_with_at_least_one_io_loser"] == sB["n_trials"]
        ),
        "io_error_fraction_of_losers_A": io_fraction_A,
        "io_error_fraction_of_losers_B": io_fraction_B,
        "exists_error_fraction_of_losers_A": exists_fraction_A,
        "exists_error_fraction_of_losers_B": exists_fraction_B,
        "control_clean_in_both_executions": (
            sA["control_no_archive_ever_lost_a_race_it_should_have_won"]
            and sB["control_no_archive_ever_lost_a_race_it_should_have_won"]
        ),
    },
    "kpi_claim_under_test": {
        "kpi_path": "amphora-run-provenance/evidence/phase0/kpis/run-provenance-hash-chain-integrity-kpi.v1.json",
        "metric": "duplicate_archive_create_rejected_via_exists_rate",
        "metric_previously_observed": 1.0,
        "metric_previous_sample_size": 3,
        "metric_previous_probe_methodology": "sequential (single-threaded) duplicate RunArchive::create call against an already-fully-formed archive",
        "prediction_rule_step_1_verbatim": "verify base/run_id does not already exist (else Exists)",
    },
    "refutation_criterion": (
        "Under genuine concurrent (barrier-synchronized, same-run_id) "
        "RunArchive::create calls, any losing thread returns a "
        "RunArchiveError variant other than Exists -- i.e. the categorical "
        "'(else Exists)' prediction and the "
        "'duplicate_archive_create_rejected_via_exists' metric name do not "
        "hold under concurrency, only under the shipped fixture's "
        "sequential probe."
    ),
    "refutation_criterion_observed_execution_A": sA["race_total_io_errors"] > 0,
    "refutation_criterion_observed_execution_B": sB["race_total_io_errors"] > 0,
}

canon_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode() + b"\n"
(STUDY / "diagnostic.canonical.json").write_bytes(canon_bytes)
print("diagnostic_sha256", sha(canon_bytes))
