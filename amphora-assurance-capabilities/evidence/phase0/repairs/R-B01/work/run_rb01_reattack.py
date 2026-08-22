#!/usr/bin/env python3
"""Repair R-B01 re-attack diagnostic.

Re-runs, against the REPAIRED build, the checks from BOTH refuting
AUDIT_ONLY receipts:

(a) amphora-ip-fto-guard/evidence/audit/metric-schema-parity-v1
    - checkA: is metrics.unresolved_technical_categories inserted by the
      live evaluate_ip_fto_guard runtime? (regex over the extracted
      function body, same extraction doctrine as the audit)
    - checkB: repo Rust-source census for the target key
    - checkD: does the checked Phase-0 KPI test assert the target key?
    - checkE: is the target key present in the regenerated benchmark
      result artifact?

(b) amphora-ip-fto-guard/evidence/audit/counsel-assertion-detection-completeness-v1
    - the 8-adversarial-scenario probe table re-run through the REAL
      compiled runtime (standalone cargo bin /tmp/ip_fto_probe_rb01, path
      deps only), classified with the same predicates as the audit script
      (false negatives, safety invariants, banned authority keys).

Writes a canonical diagnostic JSON (two-replay byte gate applied by the
caller running this script twice and byte-comparing).
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
LIB_RS = ROOT / "amphora-assurance-capabilities/src/lib.rs"
KPI_TEST = ROOT / "amphora-assurance-capabilities/tests/ip_fto_guard_phase0_kpi.rs"
PROBES_TEST = (
    ROOT / "amphora-assurance-capabilities/tests/ip_fto_guard_counsel_assertion_probes.rs"
)
BENCH_RESULT = ROOT / "amphora-ip-fto-guard/evidence/phase0/benchmark/result.v1.json"
PROBE_DIR = Path("/tmp/ip_fto_probe_rb01")
TARGET_KEY = "unresolved_technical_categories"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


lib_text = LIB_RS.read_text()
lib_sha = sha(LIB_RS.read_bytes())

# --- (a) checkA: runtime metric-key extraction ------------------------------
fn_start = lib_text.index("fn evaluate_ip_fto_guard(")
next_fn = lib_text.index("\nfn ", fn_start + 1)
fn_body = lib_text[fn_start:next_fn]
inserted_metric_keys = sorted(
    set(re.findall(r'\(\s*"([a-z_0-9]+)"\.into\(\)', fn_body))
)
target_key_inserted_by_runtime = TARGET_KEY in inserted_metric_keys

# --- (a) checkB: repo Rust-source census ------------------------------------
grep = subprocess.run(
    ["bash", "-lc",
     f"grep -rln '{TARGET_KEY}' {ROOT} --include='*.rs' | grep -v '/target/' | sort"],
    capture_output=True, text=True,
)
rust_source_hits = [
    str(Path(p).relative_to(ROOT)) for p in grep.stdout.split() if p
]

# --- (a) checkD: checked KPI test asserts the target key --------------------
kpi_test_text = KPI_TEST.read_text()
target_key_asserted_by_checked_kpi_test = (
    TARGET_KEY in kpi_test_text
    and "unresolved_technical_categories_populated_rate" in kpi_test_text
)
probes_test_text = PROBES_TEST.read_text()
target_key_asserted_by_probe_test = TARGET_KEY in probes_test_text

# --- (a) checkE: regenerated benchmark result contains the target key -------
bench = json.loads(BENCH_RESULT.read_bytes())


def key_present(value, key):
    if isinstance(value, dict):
        return key in value or any(key_present(v, key) for v in value.values())
    if isinstance(value, list):
        return any(key_present(v, key) for v in value)
    return False


target_key_in_benchmark_result = key_present(bench, TARGET_KEY)
bench_kpi_gate = bench["kpi"]["unresolved_technical_categories_populated_rate"]

# --- (b) probe-table classification (same predicates as the audit) ----------
run1 = (PROBE_DIR / "output.json").read_bytes()
run2 = (PROBE_DIR / "output2.json").read_bytes()
assert run1 == run2, "live-runtime probe not byte-stable across replays"
probe_records = json.loads(run1)["records"]

BANNED_AUTHORITY_KEYS = {
    "batch_release", "release_authorized", "qualified", "authorized_by",
    "manufacturing_qualification", "release_authority",
}


def contains_banned_key(value):
    if isinstance(value, dict):
        for k, v in value.items():
            if k in BANNED_AUTHORITY_KEYS:
                return k
            found = contains_banned_key(v)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = contains_banned_key(item)
            if found:
                return found
    return None


records_out = []
false_negatives = 0
safety_breaches = 0
n_adversarial = 0
for r in probe_records:
    metrics = r.get("metrics", {})
    observed = metrics.get("boolean_counsel_assertion_ignored")
    is_control = r["scenario_id"] == "control-exact-path-true"
    if not is_control:
        n_adversarial += 1
    is_false_negative = (not is_control) and (observed is not True)
    if is_false_negative:
        false_negatives += 1
    fto_status_ok = metrics.get("fto_status") == "FTO NOT PERFORMED"
    legal_advice_ok = metrics.get("legal_advice") is False
    gates = r.get("gates", {})
    fto_legal_closure_ok = gates.get("fto_legal_closure") is False
    envelope_hit = contains_banned_key(r)
    safety_intact = (
        fto_status_ok and legal_advice_ok and fto_legal_closure_ok
        and envelope_hit is None
    )
    if not safety_intact:
        safety_breaches += 1
    records_out.append({
        "scenario_id": r["scenario_id"],
        "is_control": is_control,
        "boolean_counsel_assertion_ignored_observed": observed,
        "detected": observed is True,
        "false_negative": is_false_negative,
        "fto_status": metrics.get("fto_status"),
        "fto_status_pinned_ok": fto_status_ok,
        "legal_advice_false_ok": legal_advice_ok,
        "fto_legal_closure_false_ok": fto_legal_closure_ok,
        "authority_envelope_clean": envelope_hit is None,
        "safety_invariant_intact": safety_intact,
        "unresolved_technical_categories": metrics.get(TARGET_KEY),
    })

detection_recall_rate = (
    (n_adversarial - false_negatives) / n_adversarial if n_adversarial else None
)

# --- cargo test gate --------------------------------------------------------
cargo_out = Path("/tmp/rb01_cargo_test_output.txt").read_text()
cargo_green = (
    "0 failed" in cargo_out
    and "FAILED" not in cargo_out
    and cargo_out.count("test result: ok") == 12
)

diagnostic = {
    "schema": "amphora.assurance-capabilities.repair-r-b01-reattack-diagnostic.v1",
    "repair_item": "R-B01",
    "reattack_a_metric_schema_parity": {
        "lib_rs_sha256_now": lib_sha,
        "inserted_metric_keys_by_live_runtime": inserted_metric_keys,
        "target_key": TARGET_KEY,
        "target_key_inserted_by_runtime": target_key_inserted_by_runtime,
        "rust_source_hits": rust_source_hits,
        "rust_source_hit_count": len(rust_source_hits),
        "target_key_asserted_by_checked_kpi_test": target_key_asserted_by_checked_kpi_test,
        "target_key_asserted_by_probe_regression_test": target_key_asserted_by_probe_test,
        "target_key_present_anywhere_in_benchmark_result": target_key_in_benchmark_result,
        "benchmark_result_sha256_now": sha(BENCH_RESULT.read_bytes()),
        "benchmark_kpi_gate_unresolved_technical_categories_populated_rate": bench_kpi_gate,
    },
    "reattack_b_counsel_assertion_detection": {
        "harness": "/tmp/ip_fto_probe_rb01 (standalone cargo bin, path deps: amphora-core, amphora-assurance-capabilities)",
        "harness_main_rs_sha256": sha((PROBE_DIR / "src/main.rs").read_bytes()),
        "probe_stdout_sha256": sha(run1),
        "two_replay_byte_identical": run1 == run2,
        "n_adversarial_scenarios": n_adversarial,
        "n_false_negatives": false_negatives,
        "detection_recall_rate": detection_recall_rate,
        "n_safety_breaches": safety_breaches,
        "records": records_out,
    },
    "cargo_test": {
        "command": "~/.cargo/bin/cargo test --offline --locked -p amphora-assurance-capabilities",
        "green": cargo_green,
        "test_result_lines": [
            line for line in cargo_out.splitlines() if line.startswith("test result")
        ],
    },
    "acceptance": {
        "eight_of_eight_probes_detected": false_negatives == 0 and n_adversarial == 8,
        "control_positive_detected": any(
            r["is_control"] and r["detected"] for r in records_out
        ),
        "zero_safety_breaches": safety_breaches == 0,
        "primary_kpi_populated_by_runtime": target_key_inserted_by_runtime,
        "cargo_green": cargo_green,
    },
}

canonical = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
out_name = sys.argv[1]
Path(out_name).write_bytes(canonical)
print("wrote", out_name, "sha256", sha(canonical))
print("acceptance", json.dumps(diagnostic["acceptance"]))
