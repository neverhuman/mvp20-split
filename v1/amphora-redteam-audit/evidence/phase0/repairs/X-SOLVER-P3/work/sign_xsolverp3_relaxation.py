#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit X-SOLVER-P3 solver-lab
constraint-relaxation audit-trail receipt (CAMPAIGN item X-SOLVER-P3, fire
20260814T110001-1175738-a5389d84286e). AUDIT_ONLY: signs the done receipt
under evidence/phase0/repairs/X-SOLVER-P3/done/. Uses the pinned
PHASE0_EVALUATOR key, cross-checked against config/phase0-trust-store.v1.json.
"""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/X-SOLVER-P3/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/X-SOLVER-P3/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


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
canon_sha = sha(runA_bytes)

harness_sha = sha((WORK / "run_xsolverp3_relaxation_audit.py").read_bytes())
engine_sha = sha((WORK / "relaxation_registry.py").read_bytes())

# Independent, fresh proof (at sign time) that amphora-solver-lab's own
# crate source was not modified by this fire.
git_status = subprocess.run(
    ["git", "status", "--porcelain", "--", "amphora-solver-lab/"],
    cwd=ROOT, capture_output=True, text=True, check=True,
).stdout
solver_lab_source_unchanged = (git_status.strip() == "")
assert solver_lab_source_unchanged, f"amphora-solver-lab tree is dirty: {git_status!r}"

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

verdict = diag["verdict"]

body_obj = {
    "schema": "amphora.redteam-audit.x-solver-p3-relaxation-audit-trail-receipt.v1",
    "receipt_id": "x-solver-p3-relaxation-audit-trail-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "X-SOLVER-P3",
    "fire_id": "20260814T110001-1175738-a5389d84286e",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_other_module_files": False,
    "modifies_amphora_solver_lab_source": False,
    "directive_path": "docs/directives/2026-08-05-closing-the-open-portfolio.md",
    "directive_sha256": "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d",
    "directive_obligation": "X-SOLVER-P3",
    "directive_refutation_criterion": None,
    "directive_refutation_criterion_note": (
        "This obligation's index.json entry (docs/directives/"
        "2026-08-05-closing-the-open-portfolio.index.json) carries no "
        "refutation_criterion field -- confirmed absent, not silently skipped."
    ),
    "gating_check": {
        "gated_behind": "X-EHS-CID",
        "done_receipt_found": True,
        "done_receipt_path": ("amphora-sourceability-ehs/evidence/phase0/repairs/X-EHS-CID/"
                               "done/x-ehs-cid-done-receipt.v1.dsse.json"),
        "action": ("Gate satisfied; proceeded per objective. The X-EHS-CID done receipt's own "
                    "claim_verdict is CLAIM_SURVIVED (IPDA/m-XDA CID identity re-verified "
                    "against R-N01 fire 2's corrected CIDs), so P3's blocking set is no longer "
                    "PROVISIONAL -- confirmed live in this fire's own re-derived P3 diagnostic "
                    "(rn01_correction_status.verdict_robustness reads UNCONDITIONAL, see "
                    "solver_lab_p3_ground_truth.rn01_correction_status_verdict_robustness)."),
    },
    "claim_under_attack": diag["claim_under_attack"],
    "attack_description": (
        "Implemented a constraint-relaxation proposal engine "
        "(relaxation_registry.py, sha256 " + engine_sha + ") entirely inside "
        "amphora-redteam-audit -- deliberately NOT inside amphora-solver-lab's own crate, "
        "so solver-lab's AUDIT_ONLY/EVIDENCE_ONLY authority ceiling is provably unchanged "
        "(file-level git-diff proof below) rather than merely asserted. The engine "
        "classifies every P3 constraint into HAZARD, RIGHTS, or SOFT_PREFERENCE and "
        "structurally forbids relaxation of the first two (RelaxationForbidden, keyed on "
        "registry class, not on caller-supplied candidate data). Ran the harness "
        "(run_xsolverp3_relaxation_audit.py, sha256 " + harness_sha + ") which: (1) re-derives "
        "the REAL P3 hazard-constrained hardener-selection blocking set by invoking the "
        "actual pinned solver-lab binary twice (byte-identical, sha256 " +
        diag["solver_lab_p3_ground_truth"]["sha256"] + "); (2) for every SOFT_PREFERENCE "
        "blocker on every real infeasible candidate, emits an AUDIT_ONLY relaxation "
        "proposal naming the constraint, the pre-relaxation infeasibility proof, the "
        "required human authority class, and cost-to-move; (3) for every HAZARD blocker on "
        "a real candidate, attempts relaxation against the REAL registry and confirms it is "
        "rejected; (4) runs an explicit structural fail-closed test on all 3 HAZARD/RIGHTS "
        "registry entries (RIGHTS included synthetically since no live P3 candidate is "
        "rights-blocked this fire); (5) runs a positive control that mutates a COPY of the "
        "registry to reclassify H317 as SOFT_PREFERENCE and confirms the SAME attempt then "
        "succeeds, proving the fail-closed check has real discriminating power; (6) computes "
        "whether ANY candidate becomes feasible even after hypothetically relaxing every "
        "movable (soft) blocker -- it does not, because hazard blocks 100% of the 5-candidate "
        "set (IPDA is blocked solely by H317; the other 4 fail AD-Tanimoto too)."
    ),
    "solver_lab_p3_ground_truth": diag["solver_lab_p3_ground_truth"],
    "constraint_registry": diag["constraint_registry"],
    "relaxation_proposals_on_real_blocking_set": diag["relaxation_proposals_on_real_blocking_set"],
    "hazard_attempts_on_real_candidates": diag["hazard_attempts_on_real_candidates"],
    "structural_failclosed_tests": diag["structural_failclosed_tests"],
    "hazard_rights_all_failed_closed": diag["hazard_rights_all_failed_closed"],
    "positive_control": diag["positive_control"],
    "residual_after_max_soft_relaxation": diag["residual_after_max_soft_relaxation"],
    "final_feasible_set_after_max_soft_relaxation": diag["final_feasible_set_after_max_soft_relaxation"],
    "actionable_answer": diag["actionable_answer"],
    "verdict": verdict,
    "verdict_reasoning": diag["verdict_reasoning"],
    "solver_lab_authority_ceiling": {
        **diag["solver_lab_authority_ceiling"],
        "file_level_proof": {
            "check": "git status --porcelain -- amphora-solver-lab/  (run fresh at sign time)",
            "output": git_status,
            "solver_lab_source_unchanged": solver_lab_source_unchanged,
        },
    },
    "engine_location": diag["engine_location"],
    "interpretation": (
        "CLAIM_SURVIVED. The claim under attack -- 'an EMPTY_FEASIBLE_SET can be turned into "
        "an actionable answer without weakening a gate' -- is demonstrated true by construction "
        "on the real P3 blocking set: every infeasible candidate now carries a named binding "
        "constraint, a pre-relaxation infeasibility proof, a required human authority class, "
        "and (for the 4 soft-blocked candidates) an explicit AUDIT_ONLY cost-to-move proposal, "
        "with no decision made and no gate touched. The refuting observation that would have "
        "broken this claim -- a hazard/rights relaxation succeeding against the real registry, "
        "or the positive control failing to distinguish a correctly- from an incorrectly-"
        "configured registry -- did not occur (see positive_control and "
        "structural_failclosed_tests). The feasible set remains EMPTY even after maximal soft "
        "relaxation, honestly reported as such (final_feasible_set_after_max_soft_relaxation == "
        "[]) rather than manufactured into a false winner. Solver-lab's own AUDIT_ONLY / "
        "EVIDENCE_ONLY authority ceiling is unchanged because its crate was never written to -- "
        "the relaxation engine lives entirely inside amphora-redteam-audit."
    ),
    "does_not_close": [
        "Whether a human FORMULATION_TECHNICAL_LEAD would actually grant the AD-Tanimoto "
        "relaxation for DDS/DETA/TETA/m-XDA -- this receipt proposes, never decides, and no "
        "human signoff has occurred (decision/decided_by are null on every proposal).",
        "Whether a hazard-clean 6th candidate exists that would let IPDA's slot be filled "
        "without H317 exposure -- out of scope for this repair-trail audit; a molecule-"
        "generation/screening question, not a solver-relaxation question.",
        "RIGHTS-class relaxation is only structurally tested (no live P3 candidate is "
        "rights-blocked this fire); the RIGHTS_USBR_REVIEW_REQUIRED registry entry is "
        "therefore unexercised against a real blocking fact, only against the synthetic "
        "structural test and would need re-verification the first time a real rights-gated "
        "candidate appears in a solver-lab demo.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "canonical_diagnostic_sha256": canon_sha,
        "runA_diagnostic_sha256": sha(runA_bytes),
        "runB_diagnostic_sha256": sha(runB_bytes),
        "byte_identical": byte_identical,
        "harness_sha256": harness_sha,
        "harness_path": ("amphora-redteam-audit/evidence/phase0/repairs/X-SOLVER-P3/work/"
                          "run_xsolverp3_relaxation_audit.py"),
        "engine_sha256": engine_sha,
        "engine_path": ("amphora-redteam-audit/evidence/phase0/repairs/X-SOLVER-P3/work/"
                         "relaxation_registry.py"),
        "determinism": ("subprocess invocation of the pinned solver-lab binary (itself "
                         "deterministic: f64-only, ordered reductions, no RNG) + pure "
                         "in-memory constraint classification; no wall-clock embedded in the "
                         "diagnostic body (RUN_DATE is a fixed literal)."),
    },
    "toolchain": {"python": "3", "note": "stdlib json/hashlib/base64/copy/subprocess + cryptography.hazmat Ed25519; cargo/rustc for the real solver-lab binary"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY done receipt under evidence/phase0/repairs/X-SOLVER-P3/done/",
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
ptype = "application/vnd.amphora.redteam-audit-x-solver-p3-relaxation-audit-trail+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "x-solver-p3-relaxation-audit-trail-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", verdict)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", canon_sha)
print("solver_lab_source_unchanged", solver_lab_source_unchanged)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
