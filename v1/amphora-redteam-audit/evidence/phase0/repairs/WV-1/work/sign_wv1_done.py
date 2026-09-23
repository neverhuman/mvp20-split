#!/usr/bin/env python3
"""DSSE-Ed25519-sign the WV-1 done-receipt (governed re-evaluation path).

AUDIT_ONLY. Does not promote authority, does not flip scientific_readiness, does
not modify any signed receipt, movement event, locked fixture, benchmark lock,
manifest, or mission front-matter. No real re-evaluation was executed: this
receipt documents a tool plus proof that it refuses correctly.

Replicates the signing ceremony of
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
REPAIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/WV-1"
WORK = REPAIR / "work"
DRY = WORK / "dry-run"
DONE = REPAIR / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

MODULES = [
    "amphora-cro-protocol-packager",
    "amphora-evidence-intake-validator",
    "amphora-known-answer-benchmarks",
    "amphora-molecule-design-gate",
    "amphora-molecule-property",
    "amphora-optimizer-orchestrator",
    "amphora-redteam-audit",
    "amphora-report-packager",
    "amphora-source-ledger",
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fsha(p):
    return sha(Path(p).read_bytes())


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


# ---------------------------------------------------------------- dry-run table
rows = []
for module in MODULES:
    out = DRY / f"{module}.json"
    err = DRY / f"{module}.err"
    text = out.read_text().strip() if out.is_file() else ""
    stderr = err.read_text().strip() if err.is_file() else ""
    if text:
        plan = json.loads(text)
        rows.append({
            "module_id": module,
            "dry_run_planned": True,
            "prior_evaluation_receipt_sha256": plan["prior_evaluation_receipt_sha256"],
            "prior_independent_review_receipt_sha256": plan["prior_independent_review_receipt_sha256"],
            "pinned_benchmark_result_sha256": plan["pinned_benchmark_result_sha256"],
            "actual_benchmark_result_sha256": plan["prior_benchmark_result_sha256"],
            "binding_broken": plan["binding_broken"],
            "new_benchmark_result_sha256": plan["new_benchmark_result_sha256"],
            "new_evaluation_receipt_sha256": plan["new_evaluation_receipt_sha256"],
            "new_evaluation_phase0_eligible": plan["new_evaluation_phase0_eligible"],
            "new_evaluation_failed_gates": plan["new_evaluation_failed_gates"],
            "files_that_would_move": [m["from"] for m in plan["files_that_move"]],
            "archive_root": plan["archive_root"],
            "archived_movement_event_ids": plan["archived_movement_event_ids"],
            "blocking_refusals": plan["blocking_refusals"],
            "would_proceed": plan["would_proceed"],
        })
    else:
        rows.append({
            "module_id": module,
            "dry_run_planned": False,
            "refusal": stderr,
        })

controls = {}
for label, name in [("intact_binding", "NEGATIVE-CONTROL-amphora-solvency-score"),
                    ("repository_local_key", "NEGATIVE-CONTROL-repo-local-key")]:
    err = (DRY / f"{name}.err")
    out = (DRY / f"{name}.json")
    controls[label] = {
        "refused": not out.read_text().strip() if out.is_file() else True,
        "stderr": err.read_text().strip() if err.is_file() else "",
    }

# ---------------------------------------------------------------- count facts
before = json.loads((WORK / "decision-report-before.json").read_text())
before_phase0 = sorted(m["module_id"] for m in before["modules"] if m["phase"] == "PHASE_0")
after = json.loads((ROOT / "config/program/phase0-decision-report.v2.json").read_text())
after_phase0 = sorted(m["module_id"] for m in after["modules"] if m["phase"] == "PHASE_0")
verifier = json.loads((WORK / "portfolio-status-after.json").read_text())
verifier_phase0 = sorted(r["module_id"] for r in verifier["modules"] if r["phase"] == "PHASE_0")

COUNTS = {
    "question": "config/program/phase0-decision-report.v2.json reported phase0_count 10 while the verifier derives 9.",
    "authoritative": "the verifier",
    "why": (
        "phase0_count is not an independent fact. amphora-cli/src/phase0.rs::regenerate_report "
        "calls portfolio_status(), which calls verify_module_with_replay() for all 29 modules and "
        "writes the result to config/program/phase0-decision-report.v2.json. The report is a "
        "GENERATED artifact - control.rs::phase0_generated_file names it explicitly - and it is "
        "rewritten only when a mutating Phase-0 command runs (prepare / reissue / evaluate / "
        "review / promote / status --all --write-report). The B2 harness clobber changed shipped "
        "evidence WITHOUT going through any of those commands, so the report was never refreshed "
        "and kept describing a portfolio state that no longer existed on disk."),
    "stale_by_exactly_one_module": "amphora-molecule-design-gate",
    "explanation": (
        "The report still listed amphora-molecule-design-gate as PHASE_0. Its shipped "
        "evidence/phase0/benchmark/result.v1.json no longer hashes to the "
        "metrics.benchmark_result_sha256 pinned in its own signed evaluation receipt "
        "(pinned 3fd72f0fa08ae6e306a6718f0a618cab4abc876add5fd06521ac0022d0857761, actual "
        "8873baa3d050984dbf58fadd8d78a12f03c586e436a1c243a268ff0c93945964), so "
        "verify_evaluation_result correctly returns EVALUATION_RESULT_MISMATCH and the module "
        "derives PRE_PHASE_0. The last report regeneration happened after 8 of the 9 modules had "
        "been clobbered but before amphora-molecule-design-gate was."),
    "honest_number": 9,
    "honest_pre_phase0": 20,
    "report_phase0_before": before["phase0_count"],
    "report_phase0_modules_before": before_phase0,
    "report_phase0_after": after["phase0_count"],
    "report_phase0_modules_after": after_phase0,
    "verifier_phase0": verifier["phase0_count"],
    "verifier_phase0_modules": verifier_phase0,
    "report_now_agrees_with_verifier": after["phase0_count"] == verifier["phase0_count"] and after_phase0 == verifier_phase0,
    "already_pinned_at_9_by": "amphora-cli/src/phase0.rs::tests::source_ledger_historical_movement_and_status_are_read_only (asserts phase0_count 9, pre_phase0_count 20) - the test was already honest; the generated artifact was not",
    "fix": (
        "the stale artifact was regenerated through its own generator, "
        "`portfolio phase0 status --all --write-report`, which rewrote "
        "config/program/phase0-decision-report.v2.json, "
        "config/program/portfolio-progress-dashboard.v1.json, "
        "config/program/data-activation-promotion-trajectory.v2.json and "
        "feedback/v2/reports/portfolio-status.txt from the live verifier. No count was edited by "
        "hand and no verifier was relaxed."),
    "stale_artifact_sha256_before": {
        "config/program/phase0-decision-report.v2.json": fsha(WORK / "decision-report-before.json"),
        "config/program/data-activation-promotion-trajectory.v2.json": fsha(WORK / "trajectory-before.json"),
        "feedback/v2/reports/portfolio-status.txt": fsha(WORK / "portfolio-status-before.txt"),
    },
    "artifact_sha256_after": {
        "config/program/phase0-decision-report.v2.json": fsha(ROOT / "config/program/phase0-decision-report.v2.json"),
        "config/program/data-activation-promotion-trajectory.v2.json": fsha(ROOT / "config/program/data-activation-promotion-trajectory.v2.json"),
        "feedback/v2/reports/portfolio-status.txt": fsha(ROOT / "feedback/v2/reports/portfolio-status.txt"),
    },
    "not_a_lowered_bar": (
        "The count fell from a stale 10 to an honest 9 because the verifier is correctly refusing a "
        "module whose evaluated benchmark bytes no longer match its signed receipt. Repairing that "
        "binding through the WV-1 path (and then `promote`) is the only way to raise it again."),
}

acceptance_log = WORK / "acceptance-2026-08-04.log"
acceptance = json.loads((WORK / "acceptance-summary.json").read_text())

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

EXACT_COMMAND = json.loads((WORK / "exact-human-command.json").read_text())
phase0_rs_sha = fsha(ROOT / "amphora-cli/src/phase0.rs")

TOOL = {
    "command": "portfolio phase0 re-evaluate --module <M> --reason <text> --as-of <YYYY-MM-DDTHH:MM:SSZ> --evaluation-key <external key> --review <signed review path> [--dry-run]",
    "implemented_in": "amphora-cli/src/phase0.rs",
    "entry_points": [
        "Phase0Command::ReEvaluate (clap subcommand, name = \"re-evaluate\")",
        "plan_re_evaluation() - every refusal, computed before any mutation",
        "re_evaluate_dry_run() - dispatched inside prove_read_only()",
        "re_evaluate() - the single governed mutation, backup + rollback",
        "archive_superseded_evidence() - the archive+supersede move set",
        "compose_evaluation() - the shared, write-free computation of the replacement bytes",
        "evaluate_signed() - the single legitimate writer of benchmark/result.v1.json",
    ],
    "single_writer_preserved": (
        "evaluate() previously resolved the evaluator identity from the environment and then "
        "wrote the evidence inline. It now resolves the identity and delegates to "
        "evaluate_signed(), which holds the only write_json_immutable call for "
        "evidence/phase0/benchmark/result.v1.json. re_evaluate() calls the same "
        "evaluate_signed(); no second writer was introduced. The write-free half was factored "
        "into compose_evaluation(), so a dry run predicts byte-for-byte what the real run writes."),
    "archive_layout": {
        "root": "<module>/evidence/phase0/superseded/<sha256-of-prior-evaluation-receipt>/",
        "contents": [
            "evaluation.v1.dsse.json (prior, byte-identical)",
            "independent-review.v1.dsse.json (prior, when one exists)",
            "result.v1.json (prior, byte-identical)",
            "movement/events/<event>.json (prior, when one exists)",
            "movement/ledger.v1.json (prior, when a movement event exists)",
            "reevaluation-supersession-note.v1.json",
        ],
        "note_schema": "amphora.module-phase0-reevaluation-supersession.v1",
        "note_records": [
            "module_id, caller-supplied as_of, caller-supplied reason",
            "prior evaluation receipt / review receipt / benchmark result sha256s",
            "the pinned-vs-actual benchmark_result_sha256 mismatch that justifies the repair",
            "the replacement receipt / result / review sha256s and both key ids",
            "archived_artifacts map, authority_transferred=false, promotes_authority=false",
        ],
        "determinism": "the note embeds no clock reading; --as-of is supplied by the caller and validated to a fixed shape",
    },
    "movement_event_handling": {
        "why": (
            "a movement event binds evaluation_receipt_hash. A replacement receipt therefore "
            "invalidates the prior movement claim, and verify_module_with_replay hard-bails "
            "(\"movement event binding or filename is invalid\") rather than merely failing a "
            "gate - which would break portfolio status for all 29 modules."),
        "what": "the prior movement event and ledger are superseded into the same archive and the ledger is reset to zero events",
        "result": "the module lands at PRE_PHASE_0 / promotable and its phase must be re-derived by the existing `phase0 promote` command; the repair never mints a movement event",
    },
    "rollback": "the module tree is copied to .phase0-reevaluate-backup-<module>-<prior-sha> before the first mutation and restored (and the decision report regenerated) if any step fails",
    "files_changed": {"amphora-cli/src/phase0.rs": phase0_rs_sha},
}

REFUSALS = [
    {
        "property": "can only ever repair a KNOWN-BROKEN binding",
        "enforced_by": "require_repairable_binding(): refuses every module outside UNBOUND_BENCHMARK_RESULTS",
        "second_dynamic_check": "plan_re_evaluation() refuses again if the shipped result still hashes to the pinned metrics.benchmark_result_sha256, so healthy evidence is unreachable even if the static list ever drifted",
        "test": "phase0::tests::re_evaluate_refuses_every_module_with_an_intact_binding",
        "negative_control": "NEGATIVE-CONTROL-amphora-solvency-score",
    },
    {
        "property": "dual identity - both a fresh evaluation signature and a fresh independent-review signature",
        "enforced_by": (
            "clap makes --evaluation-key and --review mandatory; load_supplied_review() refuses an "
            "unsigned review and any review whose evaluator and reviewer identities coincide "
            "(ModulePhase0ReviewReceiptV1::validate -> SameSigner); plan_re_evaluation() additionally "
            "requires the reviewer key to hold PHASE0_INTERNAL_REVIEWER in the trust store, the review "
            "signature to verify, the review to name this module, to be bound to the supplied evaluator "
            "identity, and to have accepted the module"),
        "test": "phase0::tests::re_evaluate_refuses_a_single_signature",
    },
    {
        "property": "signing keys still come from outside the repository",
        "enforced_by": "load_evaluation_identity() calls the unchanged load_signing_key(), which refuses repository-local keys, symlinks, and non-0600/0700 modes; the review receipt must also be supplied from outside the repository",
        "test": "phase0::tests::re_evaluate_refuses_a_repository_local_signing_key",
        "negative_control": "NEGATIVE-CONTROL-repo-local-key",
    },
    {
        "property": "the fresh review must bind the receipt this run will write",
        "enforced_by": "plan_re_evaluation() computes the replacement receipt sha256 before any mutation and lists REVIEW_NOT_BOUND_TO_NEW_EVALUATION_RECEIPT as a blocking refusal; re_evaluate() bails on any blocking refusal before touching a single artifact",
        "observed": "all 8 dry runs that could be planned reported exactly this refusal, because the on-disk reviews bind the superseded receipts",
    },
    {
        "property": "a repair may not land a module in a failing state",
        "enforced_by": "RE_EVALUATION_WOULD_NOT_BE_PHASE0_ELIGIBLE is a blocking refusal",
    },
    {
        "property": "--dry-run writes nothing",
        "enforced_by": "the dry-run dispatch is wrapped in amphora_core::prove_read_only(), and archive_superseded_evidence() is a pure computation when apply == false",
        "test": "phase0::tests::re_evaluate_dry_run_moves_nothing",
    },
    {
        "property": "no existing guard was weakened",
        "detail": (
            "evaluate() still bails on an existing receipt; reissue() still refuses after any "
            "evaluation, review, or movement history; verify_evaluation_result, "
            "verify_module_with_replay, the REVIEW_BINDING_MISMATCH check, load_signing_key's "
            "repo-local refusal and the regression guard "
            "shipped_benchmark_results_stay_bound_to_signed_evaluation_receipts are unchanged. "
            "UNBOUND_BENCHMARK_RESULTS moved from the test module to module scope so that the "
            "guard and the repair path read the same list and cannot drift apart."),
    },
]

body_obj = {
    "schema": "amphora.phase0-repair.done-receipt.v1",
    "repair_item": "WV-1",
    "repair_title": "governed Phase-0 re-evaluation path (build the tool; do not run the ceremony)",
    "repair_mode": "interactive-2026-08-04",
    "module": "amphora-redteam-audit",
    "receipt_location_note": (
        "amphora-cli has no evidence/ tree, so this receipt is filed under "
        "amphora-redteam-audit/evidence/phase0/repairs/WV-1/done/ as instructed. "
        "The engineering change itself is in amphora-cli/src/phase0.rs."),
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
    "executed_a_real_re_evaluation": False,
    "trust_anchored_in_phase0_store": bool(eval_pin),
    "tool": TOOL,
    "refusal_properties": REFUSALS,
    "negative_controls": controls,
    "per_module_dry_run": rows,
    "amphora_molecule_property_finding": {
        "question": "amphora-molecule-property has no independent-review receipt and no movement event, so verify_module_with_replay/verify_evaluation_result take the live re-execution branch. Can re-evaluate help it at all?",
        "answer": "Yes - and it is the only one of the nine whose binding is broken twice over - but the repair is not a pure repair, and its dry run cannot be planned today.",
        "why_its_binding_is_doubly_broken": (
            "verify_evaluation_result checks metrics.benchmark_result_sha256 against the shipped "
            "bytes for every module. For a module with neither a review receipt nor a movement "
            "event it ALSO re-executes the locked benchmark and compares the live diagnostic with "
            "first_replay.diagnostic_receipt. amphora-molecule-property fails both: pinned "
            "fc5a505c7e88c931842abaaebe0d4b2373f1d580c9b7b1ff2523a46a0a25c923 vs actual "
            "d04b516c806f452556ccdc91250d6ee2474f09565ac1656a88cbf13776716f90, and the shipped "
            "bytes are the MODULE-HARNESS shape, which carries no comparable diagnostic."),
        "what_a_repair_would_do": (
            "re-evaluate regenerates both from one live evaluation, so both checks pass at once. "
            "Once the mandatory fresh review is imported, review_exists becomes true and the live "
            "branch is skipped, so the repaired binding is as durable as the other eight - it no "
            "longer re-breaks when module-manifest.json or config/benchmark-lock.v1.json "
            "legitimately change."),
        "honest_caveats": [
            "it has nothing to supersede on the review side: no independent-review receipt and no movement event exist, so the archive holds only the prior evaluation receipt and the prior benchmark result",
            "because the tool demands dual identity, repairing it necessarily grants it its FIRST independent review - a state change beyond repair. Its phase does not change (PRE_PHASE_0 before and after), but it becomes promotable, which it never was",
            "there is no smaller governed option: the tool will not, and should not, rewrite evidence on one signature",
        ],
        "why_no_dry_run_numbers": (
            "the dry run refuses before it can compute the replacement hashes, because no review "
            "receipt exists for this module anywhere. Supplying another module's review reproduces "
            "the cross-module refusal recorded in the table. No review was fabricated: signing a "
            "review receipt asserting independent_reimplementation_passed would be a false "
            "attestation. A human obtains the real one in the step-1 rehearsal, exactly as for the "
            "other eight, and only then can this module be planned."),
        "chicken_and_egg_note": (
            "amphora-phase0-reviewer refuses to review a module whose recorded benchmark does not "
            "reproduce (verify_recorded_benchmark), so no fresh review can be obtained against the "
            "broken authoritative tree. That is precisely why the ceremony rehearses in a scratch "
            "copy: the replacement receipt is deterministic, so the reviewer can verify and sign it "
            "there, and the authoritative tree is touched exactly once."),
    },
    "count_reconciliation": COUNTS,
    "exact_human_command": EXACT_COMMAND,
    "acceptance": acceptance,
    "clean_git_status_proof": {
        "claim": "no shipped Phase-0 benchmark result was touched by this repair",
        "method": "git status --porcelain on the pathspec */evidence/phase0/benchmark/result.v1.json",
        "git_status_porcelain_on_pathspec": git_status_results,
        "git_status_is_clean": git_status_results == "",
    },
    "provenance": {
        "amphora_cli_phase0_rs_sha256": phase0_rs_sha,
        "dry_run_output_sha256": {p.name: fsha(p) for p in sorted(DRY.iterdir())},
        "acceptance_log_sha256": fsha(acceptance_log) if acceptance_log.is_file() else None,
        "dry_run_execution_notes": [
            "the sweep ran with the binary built from this source; amphora-source-ledger was "
            "re-run afterwards (dry-run/RECHECK-amphora-source-ledger.json) and reproduced its "
            "sweep output byte-for-byte",
            "amphora-evidence-intake-validator's first attempt aborted with ReadOnlyError because "
            "another agent wrote into the repository during its four-minute window; the tool was "
            "right to refuse, and the retry recorded here succeeded. Its --reason text drops one "
            "apostrophe relative to the other eight (shell quoting); --reason feeds only the "
            "supersession note prose and no hash",
            "the concurrent-writer sensitivity is a property of prove_read_only, not of this tool",
            "the same property applies to the acceptance run: "
            "phase0::tests::source_ledger_historical_movement_and_status_are_read_only hashes the "
            "whole worktree, so the acceptance log must be written OUTSIDE the repository and "
            "copied in afterwards. A first attempt that redirected the log straight into "
            "repairs/WV-1/work/ failed that test on its own growing bytes - the test was right, "
            "and the log is now produced at /home/ubuntu/wv1-acceptance-2026-08-04.log and copied "
            "in after the run",
        ],
        "external_review_copies_used_for_the_dry_run": (
            "the dry run needs a signed review only to reach the plan; the 8 modules that have one "
            "were given a copy of their own on-disk review at /home/ubuntu/wv1-dryrun-reviews/ "
            "(outside the repository, as the tool requires). Every one of them was refused with "
            "REVIEW_NOT_BOUND_TO_NEW_EVALUATION_RECEIPT, which is the correct answer."),
    },
    "does_not_establish": [
        "does not establish that any module with a broken binding is scientifically invalid",
        "does not establish any product performance, qualification, or superiority claim",
        "does not re-promote or demote anything; phase is derived, never asserted",
        "does not assert that a re-evaluation has been performed - none has",
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
out = DONE / "WV-1.done-receipt.v1.dsse.json"
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
assert reloaded["payload_decoded"]["executed_a_real_re_evaluation"] is False

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("payload_canonical_sha256", sha(body))
print("receipt_sha256", fsha(out))
print("SELF_VERIFY_ED25519 True")
print("keyid_prefix_ok True")
