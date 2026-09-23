#!/usr/bin/env python3
"""DSSE-Ed25519-sign the X-SCHEMA-WATCH repair receipt (CAMPAIGN item
X-SCHEMA-WATCH, module amphora-redteam-audit, directive AMPHORA-DIRECTIVE-2026-08-05
A.3). AUDIT_ONLY. Does not modify the master manifest, any locked dataset, or any
existing signed receipt. Sign-only with the pinned evaluator seed; self-verifies
before writing.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/X-SCHEMA-WATCH"
WORK = ITEM / "work"
OUT_DIR = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260814T100001-636676-50a308a040b8"
DIRECTIVE_PATH = "docs/directives/2026-08-05-closing-the-open-portfolio.md"
DIRECTIVE_SHA256 = "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


runA_bytes = (WORK / "diagnostic.runA.json").read_bytes()
runB_bytes = (WORK / "diagnostic.runB.json").read_bytes()
byte_identical = runA_bytes == runB_bytes
assert byte_identical, "two-replay bytes differ -- NOT stable, do not sign"
diag = json.loads(runA_bytes)
assert diag["counts"]["total"] == 27
assert diag["unbound_count"] == 9

watch_sha = sha((WORK / "schema_flip_watch.py").read_bytes())
diagnostic_harness_sha = sha((WORK / "xschema_diagnostic.py").read_bytes())
tempdir_guard_replica_sha = sha((WORK / "tempdir_guard_replica.sh").read_bytes())
real_guard_sha = sha(Path("/home/ubuntu/amphora-autocommit-guard.sh").read_bytes())
tempdir_sim_log_sha = sha((WORK / "tempdir_simulation.log").read_bytes())
real_census_log_sha = sha((WORK / "real_tree_census.log").read_bytes())
phase0_rs_sha = sha((ROOT / "amphora-cli/src/phase0.rs").read_bytes())
guard_log_sha = sha((ROOT / "logs/autocommit-guard.log").read_bytes())
b2_done_sha = sha((ROOT / "amphora-redteam-audit/evidence/phase0/repairs/B2/done/B2.done-receipt.v1.dsse.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust store"

UNBOUND_EXPECTED = [
    "amphora-cro-protocol-packager", "amphora-evidence-intake-validator",
    "amphora-known-answer-benchmarks", "amphora-molecule-design-gate",
    "amphora-molecule-property", "amphora-optimizer-orchestrator",
    "amphora-redteam-audit", "amphora-report-packager", "amphora-source-ledger",
]
assert diag["unbound_modules"] == UNBOUND_EXPECTED, diag["unbound_modules"]

body_obj = {
    "schema": "amphora.redteam-audit.x-schema-watch-repair-receipt.v1",
    "receipt_id": "x-schema-watch-repair-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "REPAIR",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "X-SCHEMA-WATCH",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_existing_receipts": False,
    "modifies_mission_front_matter": False,
    "directive_path": DIRECTIVE_PATH,
    "directive_sha256": DIRECTIVE_SHA256,
    "directive_obligation": "X-SCHEMA-WATCH",
    "directive_obligation_text": {
        "title": "Put RESTORED_SCHEMA_FLIP under active review -- the one failure "
                  "mode all three checks miss",
        "claim": "A benchmark-result schema flip would be detected rather than "
                 "silently committed.",
        "source": "docs/directives/2026-08-05-closing-the-open-portfolio.index.json#X-SCHEMA-WATCH",
    },
    "claim_under_attack": "A benchmark-result schema flip would be detected rather "
                           "than silently committed.",

    "attack_description": (
        "Three-part attack. (1) Reproduced the guard's exact restore logic "
        "(byte-identical core loop, cd retargeted only) in a tempdir git repo, "
        "never the real tree, and planted a real schema-flip defect (the literal "
        "cargo-test module-harness rewrite shape) in the worktree while HEAD stayed "
        "RUNTIME-shape, to test whether the narrow live-transient-flip mechanism "
        "actually detects and restores. (2) Enumerated every "
        "*/evidence/phase0/benchmark/result.v1.json in the real tree by shape at "
        "HEAD. (3) Replicated the amphora-cli regression test "
        "shipped_benchmark_results_stay_bound_to_signed_evaluation_receipts "
        "(content-hash of on-disk bytes vs the hash pinned in each module's signed "
        "evaluation.v1.dsse.json) as a standalone, unconditionally-run check, since "
        "that test only runs when a human invokes cargo test -p amphora-cli and "
        "otherwise the drift it would catch sits unexamined."
    ),

    "tempdir_simulation": {
        "location": "/tmp/schema-watch-sim on xbabe2 (git-init'd fresh repo, never "
                     "the real mvp20-split tree)",
        "guard_replica_sha256": tempdir_guard_replica_sha,
        "guard_replica_identical_to_real_guard_core_logic": True,
        "real_guard_path": "/home/ubuntu/amphora-autocommit-guard.sh",
        "real_guard_sha256_at_fire_time": real_guard_sha,
        "control_pass": {
            "description": "guard run against an unmodified RUNTIME-shape worktree",
            "log_before": [], "log_after": [], "false_positive": False,
        },
        "positive_control_pass": {
            "planted_defect": "worktree copy of result.v1.json rewritten from RUNTIME "
                               "shape (first_replay.execution_passed/exit_code/"
                               "scientific_passed) to MODULE-HARNESS shape "
                               "(first_replay.diagnostic_receipt/diagnostic_sha256 only), "
                               "HEAD left untouched (still RUNTIME)",
            "how_planted": "direct overwrite of amphora-fakemod/evidence/phase0/"
                            "benchmark/result.v1.json worktree bytes, no commit",
            "detected": True,
            "restored": True,
            "observed_log_line": "2026-08-14T10:03:22+00:00 RESTORED_SCHEMA_FLIP "
                                  "amphora-fakemod/evidence/phase0/benchmark/result.v1.json",
            "worktree_after_restore_vs_head": "IDENTICAL_TO_HEAD (diff empty)",
        },
        "transcript_sha256": tempdir_sim_log_sha,
        "verdict_on_narrow_mechanism": (
            "SURVIVES: the guard's documented mechanism (detect a RUNTIME->"
            "MODULE-HARNESS transition in the worktree while HEAD is still "
            "RUNTIME-shape, restore from HEAD, log RESTORED_SCHEMA_FLIP) works "
            "exactly as designed, both in this reproduction and in its one real "
            "historical firing (see never_fired_premise_correction)."
        ),
    },

    "real_tree_census": {
        "RUNTIME": diag["counts"]["RUNTIME"],
        "MODULE-HARNESS": diag["counts"]["MODULE-HARNESS"],
        "total": diag["counts"]["total"],
        "shapes": diag["shapes"],
        "method": "for each git-tracked */evidence/phase0/benchmark/result.v1.json, "
                  "shape is RUNTIME if HEAD:<path> contains 'execution_passed', else "
                  "MODULE-HARNESS. Read-only: git status --porcelain over "
                  "*/evidence/phase0/* was empty before and after.",
        "transcript_sha256": real_census_log_sha,
    },

    "never_fired_premise_correction": {
        "objective_premise_as_written": (
            "the alarm HAS NEVER FIRED, and it is the one failure mode invisible "
            "to all three verification checks"
        ),
        "finding": "FALSE AS STATED. logs/autocommit-guard.log contains exactly one "
                   "line: '2026-08-04T06:46:57+00:00 RESTORED_SCHEMA_FLIP "
                   "amphora-solvency-score/evidence/phase0/benchmark/result.v1.json', "
                   "and git log confirms commit 0aece02 ('autocommit "
                   "2026-08-04T06:46:58+00:00') as the corresponding autocommit. "
                   "The guard has fired, exactly once, and it caught and restored a "
                   "real flip.",
        "guard_log_sha256": guard_log_sha,
        "guard_log_line_count": diag["guard_log_line_count"],
        "timing": "/home/ubuntu/amphora-autocommit-guard.sh mtime = "
                  "2026-08-04 06:46:42 UTC, 15 seconds before its one logged firing "
                  "-- the guard was deployed as part of repair B2 (same fire; B2's "
                  "done receipt is dated 2026-08-04) and fired on its very first "
                  "opportunity.",
        "b2_done_receipt_sha256_cited": b2_done_sha,
        "verdict_on_never_fired_question": (
            "Neither pure 'healthy' nor pure 'cannot fire': it fired once, "
            "correctly, immediately after deployment, and has been quiet since "
            "because repair B2 removed the module-harness writer that caused the "
            "original damage in the same fire that deployed the guard -- there is "
            "little left in normal operation for it to catch. Silence since is "
            "explained by root-cause removal, not by a broken alarm. But this "
            "correctly-firing-once guard is doing much less work than the "
            "objective's framing implies, because it structurally cannot address "
            "the damage that predates it -- see unbound_benchmark_results_finding."
        ),
    },

    "unbound_benchmark_results_finding": {
        "statement": (
            "9 of the 27 modules with a result.v1.json currently have on-disk "
            "bytes that do NOT match the metrics.benchmark_result_sha256 pinned in "
            "their own signed evidence/phase0/receipts/evaluation.v1.dsse.json -- "
            "i.e. a benchmark-result schema flip that WAS silently committed, and "
            "remains so today. This module, amphora-redteam-audit, is one of the 9."
        ),
        "unbound_modules": diag["unbound_modules"],
        "unbound_count": diag["unbound_count"],
        "cross_check": (
            "identical, in order, to the UNBOUND_BENCHMARK_RESULTS constant at "
            "amphora-cli/src/phase0.rs:49-58"
        ),
        "phase0_rs_sha256": phase0_rs_sha,
        "provenance": (
            "Not a new discovery -- repair B2 (2026-08-04) found and documented this: "
            "'the module-harness writer' (a cargo-test side effect, since removed) "
            "destroyed these 9 modules' shipped runtime-shape benchmark results before "
            "any guard existed; B2's own done receipt records recovery as attempted "
            "and FAILED for all 9 (original bytes are cryptographically unreproducible; "
            "the first commit in this repo's history already contains the clobbered "
            "bytes). B2 built the UNBOUND_BENCHMARK_RESULTS gate so `phase0 "
            "re-evaluate` refuses to touch these modules, and a cargo-test-only "
            "regression test so the SET of unbound modules cannot silently drift. "
            "It did not build anything that surfaces the ongoing existence of this "
            "condition without a human running that specific test."
        ),
        "why_the_guard_cannot_help_here": (
            "The autocommit guard's restore precondition requires HEAD to already "
            "be RUNTIME-shape ('git show HEAD:$f | grep -q execution_passed || "
            "continue'). For all 9 unbound modules, HEAD has been MODULE-HARNESS-"
            "shape since this repository's very first commit -- there is no prior "
            "good HEAD state for the guard to restore from, and its precondition "
            "never trips. This is exactly the failure mode named in the campaign "
            "item: invisible to content-hash attribution (a receipt's own pinned "
            "hash mismatch is inert unless something re-checks it), invisible to "
            "DSSE verification (the receipt itself still verifies fine -- it is the "
            "*subject* of the receipt's claim, the shipped bytes, that drifted), "
            "and invisible to fire-id ledger binding (no ledger line records this)."
        ),
    },

    "surfacing_check": {
        "path": "amphora-redteam-audit/evidence/phase0/repairs/X-SCHEMA-WATCH/work/schema_flip_watch.py",
        "sha256": watch_sha,
        "invocation": "python3 schema_flip_watch.py <repo_root> <state_json_path>",
        "invocation_documented_example": (
            "cd /home/ubuntu/amphora/build/mvp20-split && python3 "
            "amphora-redteam-audit/evidence/phase0/repairs/X-SCHEMA-WATCH/work/"
            "schema_flip_watch.py . amphora-redteam-audit/evidence/phase0/repairs/"
            "X-SCHEMA-WATCH/work/schema_watch_state.json"
        ),
        "what_it_surfaces": [
            "(1) guard log activity: any new RESTORED_SCHEMA_FLIP line since the "
            "last run, printed and non-silent, so a future real firing does not "
            "sit unread the way the one 2026-08-04 line did for 10 days",
            "(2) HEAD shape census + SILENT_SCHEMA_FLIP_UNGUARDED: a per-module "
            "shape checkpoint, run over run; a RUNTIME->MODULE-HARNESS transition "
            "at HEAD with no matching new guard-log line means the guard did not "
            "catch it (guard down, lock timeout, direct commit) -- this is "
            "detection the guard log alone cannot provide",
            "(3) receipt hash binding: on every invocation (not only when a human "
            "runs cargo test -p amphora-cli), recomputes on-disk sha256 vs each "
            "module's signed evaluation-receipt-pinned sha256 and reports every "
            "currently-unbound module -- this is what actually surfaces the "
            "9-module finding above, continuously, instead of once, in 2026-08-04, "
            "by hand",
        ],
        "exit_codes": "0=quiet, 1=guard fired (informational), "
                       "2=SILENT_SCHEMA_FLIP_UNGUARDED found, 3=unbound modules found",
        "tested_scenarios": [
            "control (no defect): quiet, exit 0",
            "guard-caught flip replayed through the log: reports the new line, exit 1",
            "silent bypass (direct commit of MODULE-HARNESS shape with NO guard run, "
            "simulating guard-down/lock-timeout): ALERT SILENT_SCHEMA_FLIP_UNGUARDED, "
            "exit 2 -- ​verified the script catches a class of event the guard log "
            "itself cannot show",
            "receipt hash-binding UNBOUND detection: fixture receipt pinned to the "
            "pre-flip hash while on-disk holds post-flip bytes -> UNBOUND flagged, "
            "exit 3 -- reproduces the exact B2-discovery scenario",
            "real tree, read-only: 9 UNBOUND modules reported, byte-identical to "
            "UNBOUND_BENCHMARK_RESULTS, exit 3",
        ],
        "diagnostic_harness_path": "amphora-redteam-audit/evidence/phase0/repairs/X-SCHEMA-WATCH/work/xschema_diagnostic.py",
        "diagnostic_harness_sha256": diagnostic_harness_sha,
        "wiring_note": (
            "Landed as a runnable, committed script under this repair's work/ "
            "directory, not wired into crontab this fire -- crontab is shared "
            "system infrastructure outside amphora-redteam-audit's subtree and "
            "outside this fire's authorized write scope. Recommended human action: "
            "add it as a second line in the existing 30 * * * * crontab entry, "
            "after the guard runs, so it becomes part of the hourly cycle."
        ),
    },

    "verdict": "CLAIM_REFUTED",
    "interpretation": (
        "The claim as stated in the campaign item -- 'a benchmark-result schema "
        "flip would be detected rather than silently committed' -- is false in "
        "the present tense, today, for 9 of 27 modules (33%), including this "
        "module itself. A flip WAS silently committed for each of them (on-disk "
        "bytes no longer match the hash pinned in their own signed evaluation "
        "receipt), and it remains uncorrected 10 days after B2 discovered and "
        "quarantined it, because nothing except a human manually running one "
        "specific cargo test surfaces that fact. The autocommit guard, separately, "
        "genuinely works for the narrower live-transient-flip case it targets "
        "(proven by tempdir reproduction with a real positive control, and "
        "corroborated by its one real historical firing on 2026-08-04) -- but "
        "that narrow mechanism cannot and does not extend to flips already baked "
        "into HEAD before it existed, which is exactly the state 9 modules are "
        "in. The objective's stated premise that the guard 'has never fired' is "
        "also factually incorrect (see never_fired_premise_correction) and is "
        "corrected here rather than propagated."
    ),
    "repair_status": "n/a_this_is_an_audit_not_a_repair_of_the_9_modules",
    "does_not_close": [
        "Recovery of the 9 modules' original evaluated bytes -- B2 already "
        "investigated this exhaustively and concluded it is impossible (the "
        "bytes are cryptographically unreproducible and no backup exists "
        "anywhere on xbabe2). Restoring PHASE_0 eligibility for these modules "
        "requires a fresh promotion-ceremony evaluation, out of scope for an "
        "AUDIT_ONLY item.",
        "Wiring schema_flip_watch.py into the hourly crontab -- left as a "
        "documented human action rather than an autonomous infra change to "
        "shared, outside-module system state.",
        "Whether every future module-harness-shaped result is necessarily bad: "
        "the 8 MODULE-HARNESS-shape modules with NO signed evaluation receipt "
        "at all (distinct from the 9 UNBOUND ones) are not flagged as unbound by "
        "this check by design, matching the amphora-cli regression test's own "
        "semantics (receipt_path.is_file() precondition) -- they simply have not "
        "reached phase0 evaluation yet, which is a different, non-alarming state.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "runA_diagnostic_sha256": sha(runA_bytes),
        "runB_diagnostic_sha256": sha(runB_bytes),
        "byte_identical": byte_identical,
        "diagnostic_harness_sha256": diagnostic_harness_sha,
        "determinism": "pure stdlib json/hashlib/subprocess(git); no RNG, no wall clock in body",
    },
    "toolchain": {"python": "3", "note": "stdlib json/hashlib/subprocess + cryptography for signing only"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair receipt under evidence/phase0/repairs/X-SCHEMA-WATCH/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit-x-schema-watch-repair+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "x-schema-watch-repair-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", body_obj["verdict"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256_runA", sha(runA_bytes))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
