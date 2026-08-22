#!/usr/bin/env python3
"""DSSE-Ed25519-sign the B2 done-receipt (schema-era two-writer repair).

AUDIT_ONLY. Does not promote authority, does not flip scientific_readiness, does
not modify any signed receipt, movement event, locked fixture, benchmark lock,
manifest, or mission front-matter. Replicates the signing ceremony of
amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py
(pae / load_seed / payloadType / attestation keys / two-replay gate) and
self-verifies the rebuilt PAE against the Ed25519 public key.
"""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
REPAIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/B2"
WORK = REPAIR / "work"
DONE = REPAIR / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["counts"]["derived_phase0_count"] == 9
assert diag["writers"]["module_harness_writers_still_targeting_shipped_evidence"] == []

acceptance_log = WORK / "acceptance-2026-08-04.log"
acceptance_sha = sha(acceptance_log.read_bytes())
diagnostic_harness_sha = sha((WORK / "b2_diagnostic.py").read_bytes())
regen_harness_sha = sha((WORK / "regen_runtime_results.py").read_bytes())
phase0_rs_sha = sha((ROOT / "amphora-cli/src/phase0.rs").read_bytes())

git_status_results = subprocess.run(
    ["git", "status", "--porcelain", "--", "*/evidence/phase0/benchmark/result.v1.json"],
    cwd=ROOT, capture_output=True, text=True).stdout.strip()

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
rev_pin = rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id")

destroyed = [r["module_id"] for r in diag["modules"] if r["binding_matches"] is False]
phase0 = [r["module_id"] for r in diag["modules"] if r["derived_phase"] == "PHASE_0"]

body_obj = {
    "schema": "amphora.phase0-repair.done-receipt.v1",
    "repair_item": "B2",
    "repair_mode": "interactive-2026-08-04",
    "module": "amphora-redteam-audit",
    "receipt_location_note": (
        "amphora-cli has no evidence/ tree, so this receipt is filed under "
        "amphora-redteam-audit/evidence/phase0/repairs/B2/done/ as instructed. "
        "The engineering change itself is in amphora-cli/src/phase0.rs and in 27 "
        "per-module Phase-0 KPI integration tests across 8 crates."),
    "date": "2026-08-04",
    "generated_on_host": "xbabe2",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_benchmark_lock": False,
    "modifies_existing_receipts": False,
    "modifies_mission_front_matter": False,
    "trust_anchored_in_phase0_store": bool(eval_pin),

    "defect": diag["defect"],

    "writers": {
        "runtime_authority_writer": {
            "file": "amphora-cli/src/phase0.rs",
            "function": "evaluate",
            "call": "write_json_immutable(phase0_dir.join(\"benchmark/result.v1.json\"), &result)",
            "shape": ("RUNTIME: {schema, module_id, bundle_sha256, first_replay, "
                      "second_replay, replay_identical, benchmark_execution_complete, "
                      "legacy_local_receipt_authority, scientific_outcome}; "
                      "first_replay/second_replay come from execute_locked_benchmark() "
                      "and carry execution_passed, exit_code, scientific_passed, "
                      "diagnostic_receipt, diagnostic_sha256, stderr_sha256"),
            "binding": ("the exact bytes are hashed into the immutable signed evaluation "
                        "receipt as metrics.benchmark_result_sha256 and re-checked by "
                        "verify_evaluation_result(); this is why an overwrite is fatal"),
            "covers_modules": 19,
            "covers_modules_note": "every module that holds evidence/phase0/receipts/evaluation.v1.dsse.json",
        },
        "module_harness_writers": {
            "count": diag["writers"]["module_harness_writer_count"],
            "files": [r["file"] for r in diag["writers"]["module_harness_writers"]],
            "call": 'fs::write(&result_path, &first_bytes).expect("write result artifact")',
            "shape": ("MODULE_HARNESS: {module_id, benchmark_id, benchmark_lock_sha256, "
                      "dataset_fixture_sha256, kpi, records, benchmark_execution_complete, "
                      "first_replay{diagnostic_receipt, diagnostic_sha256}, second_replay}; "
                      "no first_replay.execution_passed and no "
                      "diagnostic_receipt.metrics.details"),
            "covers_modules": 27,
        },
        "verifier_path_that_rejects_the_harness_shape": [
            "amphora-cli/src/phase0.rs::verify_module_with_replay",
            "amphora-cli/src/phase0.rs::verify_evaluation_result",
            "amphora-cli/src/phase0.rs::verify_deterministic_diagnostic",
            "amphora-cli/src/phase0.rs::benchmark_execution_complete",
        ],
    },

    "fix": {
        "option_chosen": "(a) module harnesses stop writing the shared evidence path",
        "change": ("All 27 per-module Phase-0 KPI integration tests now round-trip their "
                   "byte-stability artifact through env!(\"CARGO_TARGET_TMPDIR\") "
                   "(target/tmp/<module>-phase0-kpi-result.v1.json). Two-replay "
                   "byte-stability semantics are unchanged: each test still serializes "
                   "the report twice, asserts the two serializations are byte-identical, "
                   "writes, and asserts the read-back bytes are identical."),
        "option_b_rejected_because": (
            "The harness cannot emit the RUNTIME envelope honestly. The envelope is not "
            "merely a shape: verify_evaluation_result requires the file to hash to the "
            "value already pinned in the immutable signed evaluation receipt. Only the "
            "evaluator that produced those bytes can reproduce them, so any harness-"
            "written RUNTIME envelope would either fail the hash gate or be a forgery."),
        "verifier_not_weakened": True,
        "verifier_hardened_by": (
            "new governance test amphora-cli/src/phase0.rs::tests::"
            "shipped_benchmark_results_stay_bound_to_signed_evaluation_receipts, which "
            "recomputes, for every module holding a signed evaluation receipt, whether "
            "the shipped benchmark result still hashes to the pinned "
            "metrics.benchmark_result_sha256, and fails if that set changes in either "
            "direction"),
        "files_changed": {
            "amphora-cli/src/phase0.rs": phase0_rs_sha,
            "per_module_kpi_tests_changed": diag["writers"]["module_harness_writer_count"],
        },
    },

    "collateral_damage_found": {
        "statement": (
            "The harness writer did not merely produce a rejected shape - it destroyed "
            "the evaluated bytes for 9 modules that had already been evaluated under the "
            "authority path. Those bytes are pinned by signed receipts and are not "
            "recoverable from this repository."),
        "modules_with_destroyed_evaluated_bytes": destroyed,
        "recovery_attempted": True,
        "recovery_method": (
            "Faithful CPython re-derivation of execute_locked_benchmark() + the evaluate() "
            "result envelope + write_json_immutable canonicalization "
            "(to_vec_pretty(canonicalize(value)) + b'\\n'), re-run against the live "
            "`benchmark run --locked --all` output."),
        "recovery_method_validated_on_control": {
            "module": "amphora-solvency-score",
            "regenerated_sha256_equals_pinned_sha256": True,
            "meaning": ("the re-derivation is byte-faithful, so the failures below are a "
                        "genuine loss of the evaluated bytes, not a defect in the "
                        "recovery method"),
        },
        "recovery_result": "FAILED for all 9 modules",
        "recovery_failure_cause": (
            "The recorded diagnostics were produced under an earlier "
            "config/benchmark-lock.v1.json and module-manifest.json "
            "(e.g. 940ee9ad.../25b7b7f0... vs the current 43de2cbf.../571813ee...), so "
            "the live locked diagnostic no longer reproduces the evaluated bytes. This "
            "drift is legitimate and is tolerated by the verifier for already-promoted "
            "modules, but it makes byte recovery impossible."),
        "searched_for_backups": [
            "whole-tree find for */evidence/phase0/benchmark/result.v1.json outside "
            "mvp20-split on xbabe2: none",
            "git history of the mvp20-split repository: the first commit already "
            "contains the clobbered bytes",
            "module-local evidence/phase0/raw/objects and evidence/phase0/review/"
            "packet.v1.json: no embedded copy",
            "veox investor package tarballs: contain no Phase-0 benchmark results",
        ],
        "no_synthesis_performed": (
            "No attempt was made to synthesize bytes to hit the pinned hashes. Restoring "
            "these modules to PHASE_0 requires a fresh evaluation through the authority "
            "path, which is a promotion ceremony and is out of scope for this repair."),
    },

    "portfolio_count_reconciliation": {
        "previous_pinned_assertion": 16,
        "previous_assertion_location": ("amphora-cli/src/phase0.rs::tests::"
                                        "source_ledger_historical_movement_and_status_are_read_only"),
        "previous_assertion_status": "STALE - described a portfolio state destroyed before this repair",
        "honest_derived_phase0_count": diag["counts"]["derived_phase0_count"],
        "honest_derived_pre_phase0_count": diag["counts"]["derived_pre_phase0_count"],
        "count_derived_two_independent_ways": {
            "amphora-cli verifier (portfolio phase0 status --all)": 9,
            "independent CPython re-derivation (work/b2_diagnostic.py)": diag["counts"]["derived_phase0_count"],
            "agree": True,
        },
        "count_if_destroyed_bindings_were_restored": 17,
        "new_pinned_assertion": 9,
        "new_pinned_pre_phase0_assertion": 20,
        "phase0_modules": phase0,
        "per_module_reasons": [
            {"module_id": r["module_id"], "phase": r["derived_phase"], "reason": r["derived_reason"]}
            for r in diag["modules"]
        ],
        "not_a_lowered_bar": (
            "The verifier was not relaxed. The count fell because the verifier is "
            "correctly refusing modules whose evaluated benchmark bytes no longer match "
            "their signed receipt."),
    },

    "acceptance": {
        "command": ("RDKIT_INCLUDE_DIR/RDKIT_LIB_DIR/BOOST_INCLUDE_DIR/LD_LIBRARY_PATH from "
                    "/home/ubuntu/.local/share/amphora/rdkit-2026.03.2; "
                    "flock -w 300 .cron.lock ~/.cargo/bin/cargo test --workspace --locked "
                    "--features rdkit"),
        "toolchain": "1.96.0 (rust-toolchain.toml)",
        "exit_code": 0,
        "suites": 62,
        "tests_passed": 372,
        "tests_failed": 0,
        "tests_ignored": 0,
        "log_sha256": acceptance_sha,
    },

    "clean_git_status_proof": {
        "claim": ("running the full acceptance suite no longer mutates any shipped "
                  "Phase-0 benchmark result"),
        "method": ("sha256sum of all 27 */evidence/phase0/benchmark/result.v1.json captured "
                   "before the run and compared after, plus git status --porcelain on the "
                   "same pathspec"),
        "sha256_diff_before_vs_after": "IDENTICAL",
        "git_status_porcelain_on_pathspec": git_status_results,
        "git_status_is_clean": git_status_results == "",
    },

    "provenance": {
        "harness_sha256": {
            "work/b2_diagnostic.py": diagnostic_harness_sha,
            "work/regen_runtime_results.py": regen_harness_sha,
        },
        "amphora_cli_phase0_rs_sha256": phase0_rs_sha,
        "acceptance_log_sha256": acceptance_sha,
    },

    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "two_replay_sha256": diag_sha,
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": ("work/b2_diagnostic.py re-derives both writers, the per-module "
                          "shipped-bytes-vs-signed-receipt binding, and the honest Phase-0 "
                          "phase for all 29 modules from the tree alone, with no clock and "
                          "no environment input"),
    },

    "does_not_establish": [
        "does not establish that the 8 promoted modules with destroyed benchmark bytes "
        "are scientifically invalid - only that their Phase-0 evidence binding is broken",
        "does not establish any product performance, qualification, or superiority claim",
        "does not re-promote or demote anything; phase is derived, never asserted",
    ],

    "follow_up_required": [
        "amphora-cro-protocol-packager, amphora-evidence-intake-validator, "
        "amphora-known-answer-benchmarks, amphora-molecule-design-gate, "
        "amphora-optimizer-orchestrator, amphora-redteam-audit, amphora-report-packager, "
        "amphora-source-ledger each need a fresh authority-path evaluation (reissue -> "
        "evaluate -> independent review -> movement) before they can derive PHASE_0 again; "
        "their existing signed evaluation receipts must not be deleted",
        "amphora-molecule-property has a destroyed binding too but was never independently "
        "reviewed, so its phase is unaffected",
        "/home/ubuntu/amphora-autocommit-guard.sh restores RUNTIME-shape flips; with this "
        "repair in place no flip should ever occur again, so any RESTORED_SCHEMA_FLIP line "
        "in logs/autocommit-guard.log after 2026-08-04 indicates a new writer regression",
    ],

    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair done-receipt under evidence/phase0/repairs/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.phase0-repair.done-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "payload_canonical_sha256": sha(body),
    "payload_decoded": body_obj,
    "signature": envelope,
}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "B2.done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# SELF-VERIFY: rebuild PAE from the envelope, verify Ed25519, assert keyid prefix.
reloaded = json.loads(out.read_text())
env2 = reloaded["signature"]
body2 = base64.standard_b64decode(env2["payload"])
pae2 = pae(env2["payloadType"], body2)
Ed25519PublicKey.from_public_bytes(bytes.fromhex(reloaded["evaluator_public_key_hex"])).verify(
    base64.standard_b64decode(env2["signatures"][0]["sig"]), pae2)
assert env2["signatures"][0]["keyid"].startswith("phase0-evaluator-3ef6b35"), env2["signatures"][0]["keyid"]
assert sha(body2) == reloaded["payload_canonical_sha256"]
assert json.loads(body2) == reloaded["payload_decoded"]
assert reloaded["payload_decoded"]["promotes_authority"] is False

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("payload_canonical_sha256", sha(body))
print("receipt_sha256", sha(out.read_bytes()))
print("SELF_VERIFY_ED25519 True")
print("keyid_prefix_ok True")
