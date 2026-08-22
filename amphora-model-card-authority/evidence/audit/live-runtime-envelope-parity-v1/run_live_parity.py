#!/usr/bin/env python3
"""Runner for amphora-model-card-authority live-runtime-envelope-parity-v1.

Builds the standalone live Rust probe (offline, scratch CARGO_TARGET_DIR —
nothing is written inside the workspace), executes it twice over the locked
corpus (ground-truth two-replay byte gate), computes the independent CPython
oracle predictions, and emits a deterministic diagnostic JSON to argv[1].
No clocks, no randomness: every diagnostic byte derives from checked-in file
bytes and probe stdout.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import mca_live_oracle as oracle

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-model-card-authority/evidence/audit/live-runtime-envelope-parity-v1"
PROBE_DIR = BENCH / "runtime_probe"
CORPUS = BENCH / "live_corpus.v1.json"
TARGET = Path("/tmp/amphora-mca-live-probe-target")
CARGO = "/home/ubuntu/.cargo/bin/cargo"
MODULE = "amphora-model-card-authority"

MISSION_LIB_RS_PIN = "6b007d7d9d0acd453aac5e7c300ab16fb9a7253337c722cc4cffe0be23db62b4"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()


def build_probe() -> None:
    env = dict(os.environ, CARGO_TARGET_DIR=str(TARGET))
    subprocess.run([CARGO, "build", "--release", "--offline", "--quiet"],
                   cwd=PROBE_DIR, env=env, check=True)


def run_probe() -> bytes:
    out = subprocess.run([str(TARGET / "release/mca-live-runtime-probe")],
                         cwd=PROBE_DIR, input=CORPUS.read_bytes(),
                         stdout=subprocess.PIPE, check=True)
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

    # G1 — registry identity parity: live descriptor is exactly the manifest
    # row projection; 29 modules; module absent from every default lane.
    desc_live = canon_bytes(live["descriptor"])
    desc_pred = canon_bytes(pred["descriptor"])
    lanes = {
        lane: {
            "live_active_contains_module":
                live["lanes"][lane]["active_contains_module"],
            "predicted": pred["registry"]["lane_active_contains_module"][lane],
            "match": live["lanes"][lane]["active_contains_module"]
                == pred["registry"]["lane_active_contains_module"][lane],
            "report_schema_match": live["lanes"][lane]["schema"]
                == pred["registry"]["report_schema"],
            "implementation_match": live["lanes"][lane]["implementation"]
                == pred["registry"]["implementation"],
        }
        for lane in ("molecule", "formulation", "infrastructure")
    }
    g1 = {
        "descriptor_canonical_sha256_live": sha(desc_live),
        "descriptor_canonical_sha256_predicted": sha(desc_pred),
        "descriptor_byte_parity": desc_live == desc_pred,
        "module_count_live": live["module_count"],
        "module_count_predicted": pred["registry"]["module_count"],
        "module_count_match":
            live["module_count"] == pred["registry"]["module_count"],
        "default_lane_reachability": lanes,
        "no_default_lane_reaches_module":
            all(row["match"] and not row["live_active_contains_module"]
                for row in lanes.values()),
        "all_pass": (desc_live == desc_pred
                     and live["module_count"] == pred["registry"]["module_count"]
                     and all(row["match"] and row["report_schema_match"]
                             and row["implementation_match"]
                             for row in lanes.values())),
    }

    # G2 — live envelope byte parity: canonical JSON of the envelope the
    # compiled runtime emitted equals the oracle prediction, byte for byte.
    g2_cases = {}
    for case_id, predicted_env in pred["envelopes"].items():
        case_live = live["cases"][case_id]
        live_env = case_live.get("envelope")
        live_c = canon_bytes(live_env)
        pred_c = canon_bytes(predicted_env)
        g2_cases[case_id] = {
            "live_ok": case_live["ok"],
            "envelope_count": case_live.get("envelope_count"),
            "live_envelope_canonical_sha256": sha(live_c),
            "predicted_envelope_canonical_sha256": sha(pred_c),
            "byte_parity": live_c == pred_c,
            "status": live_env.get("status") if live_env else None,
            "score_semantics": live_env.get("score_semantics") if live_env else None,
        }
    g2 = {
        "cases": g2_cases,
        "envelope_fields_per_case": len(next(iter(pred["envelopes"].values()))),
        "all_pass": all(row["byte_parity"] and row["live_ok"]
                        and row["envelope_count"] == 1
                        for row in g2_cases.values()),
    }

    # G3 — module-owned error-taxonomy byte parity (exact Display strings).
    e = pred["errors"]
    ru = live["registry_errors"]["resolve_unknown_module"]
    rl = live["registry_errors"]["report_unknown_lane"]
    x2 = live["cases"]["X2_unknown_campaign_module"]
    e1 = live["cases"]["E1_evidence_package_wrong_type"]["envelope"]
    g3_rows = {
        "resolve_unknown_module": {
            "is_err": ru["is_err"],
            "live": ru.get("display"),
            "predicted": e["resolve_unknown_module"],
            "byte_parity": ru.get("display") == e["resolve_unknown_module"],
        },
        "report_unknown_lane": {
            "is_err": rl["is_err"],
            "live": rl.get("display"),
            "predicted": e["report_unknown_lane"],
            "byte_parity": rl.get("display") == e["report_unknown_lane"],
        },
        "unknown_campaign_module": {
            "is_err": not x2["ok"],
            "live": x2.get("error_display"),
            "predicted": e["unknown_campaign_module"],
            "byte_parity": x2.get("error_display") == e["unknown_campaign_module"],
        },
        "candidate_type_error_missing_inputs": {
            "is_err": e1["status"] == "ERROR",
            "live": e1["missing_inputs"],
            "predicted": [e["candidate_type_error"]],
            "byte_parity": e1["missing_inputs"] == [e["candidate_type_error"]],
        },
    }
    g3 = {
        "rows": g3_rows,
        "all_pass": all(row["is_err"] and row["byte_parity"]
                        for row in g3_rows.values()),
    }

    # G4 — authority is seed/run_id invariant: identical candidate under a
    # different deterministic seed and run identity yields byte-identical
    # authority envelope (no covert channel from execution identity to grant).
    f1 = canon_bytes(live["cases"]["F1_valid_formulation_seed0"]["envelope"])
    f2 = canon_bytes(
        live["cases"]["F2_same_candidate_new_seed_new_runid"]["envelope"])
    g4 = {
        "f1_canonical_sha256": sha(f1),
        "f2_canonical_sha256": sha(f2),
        "seeds": [0, 20260731],
        "byte_identical": f1 == f2,
        "all_pass": f1 == f2,
    }

    # G5 — fail-safe defaults (Saltzer-Schroeder 1975): malformed input is
    # rejected before any envelope exists; every emitted envelope withholds
    # optimizer use and ranking eligibility and pins all claim locks; the
    # runtime's embedded manifest hash equals the on-disk manifest bytes.
    x1 = live["cases"]["X1_malformed_missing_payload"]
    manifest_disk_sha = sha((ROOT / "module-manifest.json").read_bytes())
    envelope_rows = {}
    expected_locks = oracle.predicted_claim_locks(*oracle.load_manifest())
    for case_id in pred["envelopes"]:
        env = live["cases"][case_id]["envelope"]
        envelope_rows[case_id] = {
            "usable_by_optimizer_false": env["usable_by_optimizer"] is False,
            "authority_receipt_ranking_eligible_false":
                env["metrics"]["authority_receipt"]["ranking_eligible"] is False,
            "granted_level": env["metrics"]["authority_receipt"]["granted_level"],
            "claim_locks_complete": env["claim_locks"] == expected_locks,
            "runtime_manifest_sha256_matches_disk":
                live["cases"][case_id]["provenance_manifest_sha256"]
                == manifest_disk_sha,
        }
    g5 = {
        "x1_malformed_fail_closed": {
            "is_err": not x1["ok"],
            "error_display_recorded_not_predicted": x1.get("error_display"),
        },
        "claim_lock_count": len(expected_locks),
        "envelopes": envelope_rows,
        "module_manifest_sha256_disk": manifest_disk_sha,
        "all_pass": (not x1["ok"]) and all(
            row["usable_by_optimizer_false"]
            and row["authority_receipt_ranking_eligible_false"]
            and row["claim_locks_complete"]
            and row["runtime_manifest_sha256_matches_disk"]
            for row in envelope_rows.values()),
    }

    gates = {
        "g0_probe_two_replay_ground_truth": g0_two_replay,
        "g1_registry_identity_parity": g1["all_pass"],
        "g2_live_envelope_byte_parity": g2["all_pass"],
        "g3_error_taxonomy_byte_parity": g3["all_pass"],
        "g4_seed_runid_invariance": g4["all_pass"],
        "g5_fail_closed_no_grant": g5["all_pass"],
    }
    gates["all_pass"] = all(gates.values())

    engine_lib = (ROOT / "amphora-engine/src/lib.rs").read_bytes()
    diagnostic = {
        "schema": "amphora.model-card-authority.live-runtime-envelope-parity-diagnostic.v1",
        "study_id": "amphora-model-card-authority-live-runtime-envelope-parity-v1",
        "run_type": "live_rust_differential_audit",
        "module": MODULE,
        "purpose": (
            "First LIVE compiled-Rust differential harness for the model-card "
            "authority surface: the real amphora-engine registry and scoring "
            "front door are executed over a locked corpus and compared, "
            "canonical-JSON byte for byte, against an independent CPython "
            "oracle predicting the full authority envelope, the module-owned "
            "error-taxonomy Display strings, and registry identity from the "
            "manifest plus published minimum-privilege spec."),
        "hypothesis": (
            "H0 (audited claim): the live runtime envelope for the module is "
            "exactly the least-privilege quarantine predicted from the "
            "manifest row — INSUFFICIENT_INPUT semantics, granted level "
            "clamped to model_readiness_ceiling, ranking withheld, all claim "
            "locks pinned — for in-domain candidates; exact fail-closed "
            "taxonomy for out-of-domain, malformed, and unknown-module "
            "inputs; and the grant is invariant to seed and run identity."),
        "non_circularity": (
            "The oracle is pure CPython with zero Rust linkage and predicts "
            "envelope bytes from module-manifest.json plus the published "
            "spec; ground truth is stdout of a separately compiled binary "
            "linking the real amphora-engine crate (path dependency, no "
            "logic copied). Agreement is a cross-implementation check in the "
            "sense of McKeeman 1998, not a self-comparison."),
        "theory_reference": [
            "Saltzer & Schroeder 1975, Proc. IEEE 63(9), DOI 10.1109/PROC.1975.9939 — least privilege, fail-safe defaults",
            "McKeeman 1998, Digital Technical Journal 10(1):100-107 — differential testing",
            "Denning 1976, CACM 19(5), DOI 10.1145/360051.360056 — lattice model of secure information flow (carried from authority-lattice-completeness-v1)",
        ],
        "runtime_source_anchors": {
            "amphora-engine/src/lib.rs_sha256": sha(engine_lib),
            "mission_doc_pin_sha256": MISSION_LIB_RS_PIN,
            "mission_doc_pin_current": sha(engine_lib) == MISSION_LIB_RS_PIN,
            "note": (
                "docs/mission.md pins the 2026-07-17 audit-date lib.rs hash; "
                "the crate has since changed, so the pin is stale. This "
                "receipt anchors the hash actually compiled into the probe."),
            "amphora-core/src/capability.rs_sha256":
                sha((ROOT / "amphora-core/src/capability.rs").read_bytes()),
            "module-manifest.json_sha256": sha((ROOT / "module-manifest.json").read_bytes()),
        },
        "preconditions": {
            "probe_built_offline": True,
            "cargo_target_dir_outside_workspace": str(TARGET),
            "evidence_root_absent_by_design": True,
        },
        "counts": {
            "corpus_cases": len(json.loads(CORPUS.read_bytes())["cases"]),
            "envelope_byte_parity_cases": len(g2_cases),
            "envelope_fields_per_case": g2["envelope_fields_per_case"],
            "error_taxonomy_rows": len(g3_rows),
            "lane_reachability_rows": len(lanes),
            "claim_locks_per_envelope": len(expected_locks),
            "canonical_modules": live["module_count"],
        },
        "gates": gates,
        "g1_registry_identity_parity": g1,
        "g2_live_envelope_byte_parity": g2,
        "g3_error_taxonomy_byte_parity": g3,
        "g4_seed_runid_invariance": g4,
        "g5_fail_closed_no_grant": g5,
        "closes": (
            "First live compiled-Rust differential evidence for "
            "amphora-model-card-authority: the shipped native runtime's "
            "authority envelope, module-owned error taxonomy, and registry "
            "identity match the independent CPython minimum-privilege oracle "
            "canonical-JSON byte for byte, the authority grant is seed/run-id "
            "invariant, and malformed/unknown/out-of-domain inputs fail "
            "closed — closing the live-runtime gap named in the "
            "least-privilege-authority-parity-v1 receipt at AUDIT_ONLY level."),
        "does_not_close": (
            "Candidate-contract parse-error Display strings are recorded but "
            "owned and audited by amphora-candidate-contract; no scientific, "
            "product, or legal authority is asserted; Phase-0/Phase-1 "
            "promotion still requires the human dual-identity ceremony and a "
            "locked independent benchmark."),
        "provenance": {
            "corpus_sha256": sha(CORPUS.read_bytes()),
            "oracle_sha256": sha((BENCH / "mca_live_oracle.py").read_bytes()),
            "runner_sha256": sha((BENCH / "run_live_parity.py").read_bytes()),
            "probe_cargo_toml_sha256": sha((PROBE_DIR / "Cargo.toml").read_bytes()),
            "probe_main_rs_sha256": sha((PROBE_DIR / "src/main.rs").read_bytes()),
            "ground_truth_sha256": sha(gt_a),
            "ground_truth_runB_sha256": sha(gt_b),
        },
    }
    out_path.write_text(json.dumps(diagnostic, indent=1, sort_keys=True))
    print(f"WROTE {out_path}")
    print(f"all_pass {gates['all_pass']}")
    for name, value in gates.items():
        print(f"  {name}: {value}")


if __name__ == "__main__":
    main()
