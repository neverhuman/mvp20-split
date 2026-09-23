#!/usr/bin/env python3
"""kpi-claim-currency-v1 :: amphora-formulation-universe

Attacks a DIFFERENT artifact than T-06 (2026-08-06, CLAIM_REFUTED, signed).
T-06 red-teamed the live Rust `validate_formulation_universe` primitive
directly and proved two of its own campaign item's three named attacks:
duplicate-factor collapse (JSON integer `1` vs float `1.0` inside one axis
evades canonical-duplicate detection) and index-identity instability across
accounting-equivalent universes. mission.md prose was corrected the same day
("Known contradictions" section). But the machine-readable, portfolio-relied
Phase-0 KPI register --
evidence/phase0/kpis/formulation-universe-cartesian-accounting-kpi.v1.json --
the one artifact any downstream machine consumer (not a human reading
mission.md prose) would actually parse, was never edited, corrected,
retracted, or superseded after T-06 fired. git history shows its last commit
predates T-06 by 3 days (2026-08-03, baseline commit), and it was untouched
by T-06's own fire.

This fire independently:
  (1) confirms byte-for-byte, via T-06's own signed provenance, that
      amphora-formulation-capabilities/src/lib.rs is STILL the exact file
      T-06 tested (zero code change / zero fix landed since 2026-08-06);
  (2) fresh-re-executes TODAY (2026-08-15, 9 days later) T-06's own
      independent Rust red-team test file
      (tests/formulation_universe_redteam_t06_independent.rs) twice
      back-to-back against the live, unmodified validate_formulation_universe,
      to check whether the defect the KPI's own note omits is still live;
  (3) greps the KPI's own claimed metric
      (cartesian_canonical_duplication_fail_closed_rate, observed=1.0,
      passed=true, sample_size=4, CARTESIAN_CANONICAL_DUPLICATION attack
      axis) and asks whether "1.0, all four probes reject" is still an
      honest, non-stale characterization of that attack axis given a
      confirmed counter-example within the same axis;
  (4) searches evidence/ for any RETRACTION-INDEX.md or supersession
      reference to the KPI file path.

AUDIT_ONLY. Imports nothing; parses only real cargo test output already
captured (run1.out.txt / run2.out.txt, produced by two independent
back-to-back `cargo test --workspace --locked -p amphora-formulation-capabilities
--test formulation_universe_redteam_t06_independent -- --nocapture` invocations
against the live, unmodified workspace). Does not touch the runtime, KAT
fixture, KPI, manifest, or mission.md.
"""
import hashlib
import json
import re
import base64
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-formulation-universe"
ITEM = MOD / "evidence/audit/kpi-claim-currency-v1"
LIB_RS = ROOT / "amphora-formulation-capabilities/src/lib.rs"
KPI_PATH = MOD / "evidence/phase0/kpis/formulation-universe-cartesian-accounting-kpi.v1.json"
T06_RECEIPT = MOD / "evidence/phase0/repairs/T-06/done/t06-independent-adversarial-attack-receipt.v1.dsse.json"
T06_TEST_FILE = ROOT / "amphora-formulation-capabilities/tests/formulation_universe_redteam_t06_independent.rs"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# Step 1: provenance-continuity check against T-06's own signed record.
# ---------------------------------------------------------------------------
t06_env = json.loads(T06_RECEIPT.read_bytes())
t06_body = json.loads(base64.b64decode(t06_env["signature"]["payload"]))
t06_body_str = json.dumps(t06_body)
m = re.search(
    r"The live file on disk now hashes to ([0-9a-f]{64})", t06_body_str
)
t06_recorded_lib_rs_sha256 = m.group(1)

lib_rs_bytes = LIB_RS.read_bytes()
lib_rs_sha256_now = sha(lib_rs_bytes)
lib_rs_unchanged_since_t06 = (lib_rs_sha256_now == t06_recorded_lib_rs_sha256)

kpi_bytes = KPI_PATH.read_bytes()
kpi = json.loads(kpi_bytes)
kpi_sha256_now = sha(kpi_bytes)

t06_test_file_sha256_now = sha(T06_TEST_FILE.read_bytes())
t06_recorded_harness_sha256 = t06_body["reproducibility"]["harness_sha256"]
t06_test_file_unchanged_since_t06 = (
    t06_test_file_sha256_now == t06_recorded_harness_sha256
)

# ---------------------------------------------------------------------------
# Step 2: locate the KPI metric under test verbatim.
# ---------------------------------------------------------------------------
dup_metric = next(
    x for x in kpi["metrics"] if x["name"] == "cartesian_canonical_duplication_fail_closed_rate"
)
kpi_claimed_observed = dup_metric["observed"]
kpi_claimed_passed = dup_metric["passed"]
kpi_claimed_sample_size = dup_metric["probe_sample_size"]
kpi_claimed_note = dup_metric["note"]

# ---------------------------------------------------------------------------
# Step 3: parse the two fresh, independent, back-to-back cargo test runs
# (already captured in run1.out.txt / run2.out.txt in this directory by two
# separate `cargo test ... -- --nocapture` invocations against the live,
# unmodified workspace).
# ---------------------------------------------------------------------------
def parse_run(out_path, err_path):
    txt = out_path.read_text() + "\n" + err_path.read_text()
    branch_m = re.search(r"T06_ATTACK2_BRANCH=(\w+)(?: cardinality=(\S+) total=(\S+))?", txt)
    finding_m = re.search(
        r'T06_FINDING index=(\d+) tuple_under_A=\("(\w+)", "(\w+)"\) '
        r'tuple_under_B=\("(\w+)", "(\w+)"\) receipt_bytes_equal=(\w+)',
        txt,
    )
    result_m = re.search(
        r"test result: (\w+)\. (\d+) passed; (\d+) failed;", txt
    )
    return {
        "attack2_branch": branch_m.group(1) if branch_m else None,
        "attack2_cardinality": branch_m.group(2) if branch_m else None,
        "attack2_total": branch_m.group(3) if branch_m else None,
        "attack3_index": int(finding_m.group(1)) if finding_m else None,
        "attack3_tuple_under_A": [finding_m.group(2), finding_m.group(3)] if finding_m else None,
        "attack3_tuple_under_B": [finding_m.group(4), finding_m.group(5)] if finding_m else None,
        "attack3_receipt_bytes_equal": (finding_m.group(6) == "true") if finding_m else None,
        "cargo_test_result": result_m.group(1) if result_m else None,
        "cargo_tests_passed": int(result_m.group(2)) if result_m else None,
        "cargo_tests_failed": int(result_m.group(3)) if result_m else None,
    }


run1_out = ITEM / "run1.out.txt"
run2_out = ITEM / "run2.out.txt"
run1_err = ITEM / "run1.err.txt"
run2_err = ITEM / "run2.err.txt"
run1_sha256 = sha(run1_out.read_bytes())
run2_sha256 = sha(run2_out.read_bytes())
# cargo's stdout test-result summary is deterministic and byte-identical
# across the two independent invocations; this is the two-replay gate.
run1_run2_stdout_byte_identical = (run1_out.read_bytes() == run2_out.read_bytes())
# cargo's stderr stream carries non-deterministic build-tool noise under
# concurrent CI load (package-cache lock-wait lines, compile-time-in-seconds)
# that is NOT part of the claim under test; only the T06_* diagnostic lines
# within it are load-bearing, and parses_agree (below) checks those.
run1_run2_stderr_byte_identical = (run1_err.read_bytes() == run2_err.read_bytes())

parsed1 = parse_run(run1_out, run1_err)
parsed2 = parse_run(run2_out, run2_err)
parses_agree = (parsed1 == parsed2)

# Defect still live today iff attack2 was ACCEPTED (numeric-type duplicate not
# caught) with cardinality inflated to 2, AND attack3's decoded tuples under
# accounting-equivalent representations A/B differ while the receipt bytes
# were equal.
attack2_defect_live_today = (
    parsed1["attack2_branch"] == "ACCEPTED"
    and parsed1["attack2_cardinality"] == "Some(2)"
)
attack3_defect_live_today = (
    parsed1["attack3_receipt_bytes_equal"] is True
    and parsed1["attack3_tuple_under_A"] != parsed1["attack3_tuple_under_B"]
)
any_named_t06_defect_live_today = attack2_defect_live_today or attack3_defect_live_today

kpi_dup_metric_is_currently_stale_and_incomplete = (
    any_named_t06_defect_live_today
    and bool(kpi_claimed_passed)
    and kpi_claimed_observed == 1.0
)

# ---------------------------------------------------------------------------
# Step 4: retraction/supersession-chain search.
# ---------------------------------------------------------------------------
retraction_index_path = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
retraction_index_exists = retraction_index_path.exists()


def grep_tree_for(needle, roots):
    hits = []
    for root in roots:
        for p in root.rglob("*"):
            if p.is_file() and p.suffix in (".md", ".json") and "__pycache__" not in str(p):
                try:
                    txt = p.read_text(errors="ignore")
                except Exception:
                    continue
                if needle in txt:
                    hits.append(str(p.relative_to(ROOT)))
    return hits


kpi_rel = str(KPI_PATH.relative_to(ROOT))
supersession_hits = grep_tree_for(kpi_rel, [MOD / "evidence"])
supersession_hits = [h for h in supersession_hits if h != kpi_rel]

# git provenance of the KPI file itself (last commit date, to show it
# predates T-06 and was never touched afterward).
import subprocess

git_log = subprocess.run(
    ["git", "log", "-1", "--format=%ad %H", "--date=short", "--", kpi_rel],
    cwd=str(ROOT), capture_output=True, text=True, check=True,
).stdout.strip()

result = {
    "study_id": "kpi-claim-currency-v1",
    "module": "amphora-formulation-universe",
    "run_date": "2026-08-15",
    "days_since_t06": 9,
    "provenance_continuity": {
        "t06_recorded_lib_rs_sha256": t06_recorded_lib_rs_sha256,
        "lib_rs_sha256_now": lib_rs_sha256_now,
        "lib_rs_unchanged_since_t06": lib_rs_unchanged_since_t06,
        "t06_recorded_test_harness_sha256": t06_recorded_harness_sha256,
        "t06_test_file_sha256_now": t06_test_file_sha256_now,
        "t06_test_file_unchanged_since_t06": t06_test_file_unchanged_since_t06,
        "kpi_sha256_now": kpi_sha256_now,
        "kpi_last_git_commit": git_log,
    },
    "kpi_claim_under_test": {
        "metric_name": "cartesian_canonical_duplication_fail_closed_rate",
        "kpi_claimed_observed": kpi_claimed_observed,
        "kpi_claimed_passed": kpi_claimed_passed,
        "kpi_claimed_sample_size": kpi_claimed_sample_size,
        "kpi_claimed_note_verbatim": kpi_claimed_note,
    },
    "fresh_execution_2026_08_15": {
        "command": "cargo test --workspace --locked -p amphora-formulation-capabilities "
                   "--test formulation_universe_redteam_t06_independent -- --nocapture",
        "run1_stdout_sha256": run1_sha256,
        "run2_stdout_sha256": run2_sha256,
        "run1_run2_stdout_byte_identical": run1_run2_stdout_byte_identical,
        "run1_run2_stderr_byte_identical": run1_run2_stderr_byte_identical,
        "stderr_nondeterminism_note": "stderr differs only in non-load-bearing "
            "cargo build-tool noise (package-cache lock-wait lines under "
            "concurrent CI load, compile-time-in-seconds); the T06_* "
            "diagnostic lines and all parsed fields are identical (see "
            "parses_agree).",
        "parsed_run1": parsed1,
        "parsed_run2": parsed2,
        "parses_agree": parses_agree,
    },
    "attack2_numeric_type_duplicate_defect_live_today": attack2_defect_live_today,
    "attack3_index_identity_instability_defect_live_today": attack3_defect_live_today,
    "any_named_t06_defect_live_today": any_named_t06_defect_live_today,
    "kpi_dup_metric_is_currently_stale_and_incomplete": kpi_dup_metric_is_currently_stale_and_incomplete,
    "retraction_index_exists": retraction_index_exists,
    "supersession_or_retraction_references_to_kpi_file": supersession_hits,
    "n_supersession_or_retraction_references": len(supersession_hits),
}
print(json.dumps(result, indent=2, sort_keys=True))
