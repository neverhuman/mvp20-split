#!/usr/bin/env python3
"""Runner for amphora-report-packager live-runtime-diagnostic-parity-v1.

Builds the standalone live Rust probe (offline, scratch CARGO_TARGET_DIR --
nothing is written inside the workspace), executes it twice (ground-truth
two-replay byte gate), computes the independent CPython oracle predictions,
compares them section by section (differential testing, McKeeman 1998), and
emits a deterministic diagnostic JSON to argv[1].  No clocks, no randomness:
every diagnostic byte derives from checked-in file bytes and probe stdout.
AUDIT_ONLY: promotes nothing, edits no manifest, touches no locked artifact.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import report_packager_live_oracle as oracle

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-report-packager/evidence/audit/live-runtime-diagnostic-parity-v1"
PROBE_DIR = BENCH / "runtime_probe"
TARGET = Path("/tmp/amphora-report-packager-live-probe-target")
CARGO = "/home/ubuntu/.cargo/bin/cargo"
MODULE = "amphora-report-packager"
STUDY = "amphora-report-packager-live-runtime-diagnostic-parity-v1"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def build_probe() -> None:
    env = dict(os.environ, CARGO_TARGET_DIR=str(TARGET))
    subprocess.run(
        [CARGO, "build", "--release", "--offline", "--quiet"],
        cwd=PROBE_DIR,
        env=env,
        check=True,
    )


def run_probe() -> bytes:
    out = subprocess.run(
        [str(TARGET / "release/report-packager-live-diagnostic-probe")],
        cwd=PROBE_DIR,
        stdout=subprocess.PIPE,
        check=True,
    )
    return out.stdout


def main() -> None:
    out_path = Path(sys.argv[1])
    build_probe()
    gt_a = run_probe()
    gt_b = run_probe()
    g0_two_replay = gt_a == gt_b
    (BENCH / "runtime_ground_truth.v1.json").write_bytes(gt_a)
    live = json.loads(gt_a)
    pred = oracle.predictions()

    # G1 -- live deterministic-control diagnostic parity, byte-for-byte on the
    # canonical encoding, including the runtime-internal result_digest.
    live_diag = live["diagnostic"]
    diag_ok = not live_diag["is_err"]
    live_diag_value = live_diag.get("value", {})
    pred_diag = pred["diagnostic"]
    g1 = {
        "live_diagnostic_is_ok": diag_ok,
        "live_passed": bool(live_diag_value.get("passed", False)),
        "predicted_passed": pred_diag["passed"],
        "canonical_parity_byte_exact": canon(live_diag_value) == canon(pred_diag),
        "result_digest_live": live_diag_value.get("details", {}).get("result_digest"),
        "result_digest_predicted": pred_diag["details"]["result_digest"],
        "result_digest_match": live_diag_value.get("details", {}).get("result_digest")
        == pred_diag["details"]["result_digest"],
        "observed_equals_expected_live": live_diag_value.get(
            "expected_fixture_outcomes"
        )
        == live_diag_value.get("observed_fixture_outcomes"),
        "positive_control_count": live_diag_value.get("positive_control_count"),
        "negative_control_count": live_diag_value.get("negative_control_count"),
        "fixture_sha256_live": live_diag_value.get("details", {}).get(
            "fixture_sha256"
        ),
        "fixture_sha256_from_disk": pred_diag["details"]["fixture_sha256"],
        "fixture_sha256_match": live_diag_value.get("details", {}).get(
            "fixture_sha256"
        )
        == pred_diag["details"]["fixture_sha256"],
        "outcome_labels": sorted(pred_diag["expected_fixture_outcomes"].keys()),
    }
    g1_pass = (
        g1["live_diagnostic_is_ok"]
        and g1["live_passed"]
        and g1["predicted_passed"]
        and g1["canonical_parity_byte_exact"]
        and g1["result_digest_match"]
        and g1["observed_equals_expected_live"]
        and g1["positive_control_count"] == 1
        and g1["negative_control_count"] == 5
        and g1["fixture_sha256_match"]
    )

    # G2 -- live KPI evaluation parity + execution-context invariance.
    ev = live["evaluate"]
    run_a, run_b = ev["run_a"], ev["run_b"]
    a_ok = not run_a["is_err"]
    b_ok = not run_b["is_err"]
    pred_result = pred["module_result"]
    g2 = {
        "run_a_is_ok": a_ok,
        "run_b_is_ok": b_ok,
        "canonical_parity_byte_exact": a_ok
        and canon(run_a["value"]) == canon(pred_result),
        "context_invariant_live": bool(ev["context_invariant"]),
        "context_invariant_recheck": a_ok
        and b_ok
        and canon(run_a["value"]) == canon(run_b["value"]),
        "status_live": run_a.get("value", {}).get("status"),
        "status_predicted": pred_result["status"],
        "generated_document_count_live": run_a.get("value", {})
        .get("metrics", {})
        .get("generated_document_count"),
        "generated_document_count_predicted": pred_result["metrics"][
            "generated_document_count"
        ],
        "release_gates_all_false_live": a_ok
        and all(v is False for v in run_a["value"]["gates"].values())
        and len(run_a["value"]["gates"]) == 4,
        "artifact_hash_parity": a_ok
        and run_a["value"]["metrics"].get("artifact_hashes")
        == pred_result["metrics"]["artifact_hashes"],
        "objective_values_empty_live": a_ok
        and run_a["value"].get("objective_values") == {},
    }
    g2_pass = (
        g2["run_a_is_ok"]
        and g2["run_b_is_ok"]
        and g2["canonical_parity_byte_exact"]
        and g2["context_invariant_live"]
        and g2["context_invariant_recheck"]
        and g2["release_gates_all_false_live"]
        and g2["artifact_hash_parity"]
        and g2["objective_values_empty_live"]
    )

    # G3 -- live mediation / deny-path parity (fail-safe defaults,
    # Saltzer-Schroeder 1975; complete mediation, Anderson 1972).
    med = live["mediation"]
    pred_med = pred["mediation"]
    g3_cases = {
        case: {
            "live_is_err": med[case]["is_err"],
            "display_live": med[case].get("display"),
            "display_predicted": pred_med[case]["display"],
            "match": med[case]["is_err"]
            and med[case].get("display") == pred_med[case]["display"],
        }
        for case in sorted(pred_med.keys())
    }
    g3 = {
        "cases": g3_cases,
        "deny_paths_tested": len(g3_cases),
        "deny_paths_fail_closed_with_display_parity": sum(
            1 for c in g3_cases.values() if c["match"]
        ),
    }
    g3_pass = all(c["match"] for c in g3_cases.values())

    # G4 -- live descriptor projection parity vs mission-governed constants.
    g4 = {
        "descriptor_live": live["descriptor"],
        "descriptor_predicted": pred["descriptor"],
        "canonical_parity_byte_exact": canon(live["descriptor"])
        == canon(pred["descriptor"]),
        "authority_ceiling_evidence_only": live["descriptor"].get(
            "authority_ceiling"
        )
        == "EVIDENCE_ONLY",
        "ranking_eligible_false": live["descriptor"].get("ranking_eligible")
        is False,
        "solver_use_ceiling_disabled": live["descriptor"].get("solver_use_ceiling")
        == "DISABLED",
    }
    g4_pass = (
        g4["canonical_parity_byte_exact"]
        and g4["authority_ceiling_evidence_only"]
        and g4["ranking_eligible_false"]
        and g4["solver_use_ceiling_disabled"]
    )

    gates = {
        "g0_two_replay_byte_stability": g0_two_replay,
        "g1_live_diagnostic_oracle_parity": g1_pass,
        "g2_live_evaluation_oracle_parity": g2_pass,
        "g3_live_mediation_fail_closed": g3_pass,
        "g4_descriptor_projection_parity": g4_pass,
    }
    gates["all_pass"] = all(gates.values())

    diagnostic = {
        "schema": "amphora.report-packager.live-runtime-diagnostic-parity-diagnostic.v1",
        "study_id": STUDY,
        "run_type": "live_rust_runtime_vs_independent_cpython_oracle",
        "module": MODULE,
        "purpose": (
            "First LIVE Rust harness for amphora-report-packager: execute the "
            "compiled runtime's public diagnostic, evaluation, and mediation "
            "surfaces and require byte parity with an independent CPython "
            "oracle derived only from primary artifact bytes and published "
            "primitives."
        ),
        "hypothesis": (
            "H0 (falsifiable): the COMPILED runtime disagrees with the audited "
            "source semantics on at least one of: the 6-control diagnostic "
            "battery (1 ACCEPT / 5 REJECT with live Ed25519 + NFKC + "
            "stable_hash), the internal result_digest, the quarantined "
            "INSUFFICIENT_INPUT KPI result, execution-context invariance, the "
            "4 mediation deny paths, or the descriptor projection. Any "
            "disagreement falsifies the three prior STATIC receipts' implicit "
            "assumption that source bytes = executed behavior."
        ),
        "theory_reference": (
            "Differential testing (McKeeman, Digital Tech. J. 10(1), 1998); "
            "N-version discrepancy detection (Avizienis & Chen, COMPSAC 1977); "
            "complete mediation / reference monitor (Anderson, ESD-TR-73-51, "
            "1972); fail-safe defaults (Saltzer & Schroeder, Proc. IEEE 63(9), "
            "1975); Ed25519 (RFC 8032, 2017); Unicode NFKC (UAX #15); SHA-256 "
            "(FIPS 180-4)."
        ),
        "non_circularity": (
            "The probe links and executes the real Rust runtime and contains "
            "no decision logic; the oracle is pure CPython, shares no code "
            "with the runtime, never reads probe output, and re-derives every "
            "prediction from primary artifact bytes plus independent "
            "implementations of SHA-256, Ed25519, NFKC, and the JSON "
            "canonicaliser. Comparison happens only here, in the runner."
        ),
        "closes": (
            "The live-execution gap: all three prior receipts for this module "
            "audited SOURCE BYTES only and explicitly disclaimed any "
            "dependency on the live Rust runtime; none demonstrated that the "
            "compiled binary actually rejects the forged signature, the "
            "envelope mismatch, the stripped lock, or the NFKC-obfuscated "
            "banned claim, or that the KPI path actually quarantines."
        ),
        "does_not_close": (
            "Does not promote authority, does not flip scientific_readiness, "
            "does not test hostile inputs beyond the runtime's compiled-in "
            "mutant battery and the four mediation deny paths (the acceptance "
            "predicate is not publicly parameterizable), and does not make "
            "the module's scientific claim externally validated."
        ),
        "runtime_source_anchors": {
            "assurance_lib_rs_sha256": sha(
                (ROOT / "amphora-assurance-capabilities/src/lib.rs").read_bytes()
            ),
            "assurance_diagnostics_rs_sha256": sha(
                (
                    ROOT / "amphora-assurance-capabilities/src/diagnostics.rs"
                ).read_bytes()
            ),
            "core_capability_rs_sha256": sha(
                (ROOT / "amphora-core/src/capability.rs").read_bytes()
            ),
            "core_phase0_rs_sha256": sha(
                (ROOT / "amphora-core/src/phase0.rs").read_bytes()
            ),
            "probe_main_rs_sha256": sha(
                (PROBE_DIR / "src/main.rs").read_bytes()
            ),
            "probe_cargo_toml_sha256": sha(
                (PROBE_DIR / "Cargo.toml").read_bytes()
            ),
            "fixture_sha256": pred["diagnostic"]["details"]["fixture_sha256"],
        },
        "ground_truth": {
            "probe_stdout_sha256_run_a": sha(gt_a),
            "probe_stdout_sha256_run_b": sha(gt_b),
            "probe_output_path": "runtime_ground_truth.v1.json",
        },
        "g1_live_diagnostic": g1,
        "g2_live_evaluation": g2,
        "g3_live_mediation": g3,
        "g4_descriptor_projection": g4,
        "gates": gates,
        "verdict": (
            "H0 REFUTED: live runtime == independent oracle byte-for-byte on "
            "all compared surfaces; source-equals-behavior gap closed for the "
            "diagnostic, KPI, mediation, and descriptor surfaces."
            if gates["all_pass"]
            else "H0 NOT REFUTED: at least one live surface diverges from the "
            "independent oracle; see failing gate."
        ),
    }
    out_path.write_text(
        json.dumps(diagnostic, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    )
    print("gates", json.dumps(gates))
    print("wrote", out_path)


if __name__ == "__main__":
    main()
