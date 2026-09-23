#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-C04 fire-3/3 (FINAL permitted fire)
final-disposition checkpoint.
AUDIT_ONLY / repair-checkpoint: does NOT supersede the FFW-vs-ML KPI
(acceptance was not met -- still rights-blocked), does NOT edit any
existing signed receipt, docs/mission.md (already carries the correct
rights caveat from R-A03/fire 2), or the 66-receipt master manifest,
does NOT open the quarantined Polyverse row-level CSV or its normalized
form. Confirms fire 2's BLOCKED_RIGHTS finding is still current, and
records that the item's honest re-scope hatch (available this fire per
STATE.json, since len(fires) >= max_fires-1) was evaluated and found
not soundly executable -- so it was not invoked, rather than fabricating
an interval. This is the item's 3rd of 3 permitted fires; campaign_item
disposition is terminal BLOCKED pending human counsel review.
"""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"
EV = MOD / "evidence/phase0/repairs/R-C04/attempts/final-disposition-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260812T060001-1024222-7ef99baa4e81"
FIRE1_CKPT = MOD / "evidence/phase0/repairs/R-C04/attempts/cluster-bootstrap-data-audit-v1/cluster-bootstrap-data-audit-v1-receipt.v1.dsse.json"
FIRE2_CKPT = MOD / "evidence/phase0/repairs/R-C04/attempts/rights-boundary-audit-v1/rights-boundary-audit-v1-receipt.v1.dsse.json"


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


canon = (EV / "diagnostic.canonical.json").read_bytes()
runB = (EV / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["rights_recheck"]["unresolved"] is True
assert diag["freshness_scan"]["hits"] == []
assert diag["positive_control"]["detected"] is True

# independent 3rd confirmatory replay into a temp path
third = EV / "diagnostic.runC.tmp.json"
subprocess.run(["python3", str(EV / "run_final_disposition_audit.py")],
               check=True, cwd=str(EV), stdout=open(third, "wb"))
third_sha = sha(third.read_bytes())
third.unlink()
assert third_sha == diag_sha, f"3rd replay FAIL {third_sha} != {diag_sha}"

harness_sha = sha((EV / "run_final_disposition_audit.py").read_bytes())
fire1_ckpt_sha256 = sha(FIRE1_CKPT.read_bytes())
fire2_ckpt_sha256 = sha(FIRE2_CKPT.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text()) if TRUST.exists() else {"keys": []}
tbr = {k.get("role"): k for k in trust.get("keys", [])}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.viscosity-score.r-c04-final-disposition-checkpoint.v1",
    "receipt_id": "final-disposition-v1",
    "campaign_item_id": "R-C04",
    "module_id": "amphora-viscosity-score",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "mode": "CAMPAIGN",
    "fire_id": FIRE_ID,
    "fire_number_of_max": "3 of 3",
    "date": "2026-08-12",
    "scientific_success_required_for_phase0": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_mission_md": False,
    "modifies_signed_phase0_kpi": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "derives_from_quarantined_row_data": False,
    "repair_status": "terminal_blocked_max_fires_exhausted",
    "verdict": "BLOCKED_RIGHTS",
    "objective_under_repair": (
        "R-C04: pre-registered cluster bootstrap (resample the 13 test "
        "polymers with replacement, B=5000, seed=0) of the R2 difference "
        "(FFW_B3 - ML_B4) on the identical seed-0 partition from the KPI, "
        "verified via the conformal_receipt_sha256 cross-link. Report the "
        "CI and supersede the FFW KPI with an honest restatement at "
        "whatever strength the interval supports."
    ),
    "claim_under_attack": (
        "amphora-viscosity-score/evidence/phase0/kpis/"
        "polyverse-melt-viscosity-fox-flory-whitten-physical-baseline-vs-ml-"
        "kpi.v1.json :: headline finding 'best_physical_ffw_baseline_beats_"
        "ml_r2_documented' (physical B3 R^2=+0.5972 beats ML B4 R^2=+0.4536 "
        "by +0.1436)."
    ),
    "attack": (
        "Final-disposition audit for the 3rd and last permitted fire on "
        "this repair item. Two parts, both re-derived from bytes already "
        "on disk or their metadata: (1) re-ran fire 1's per-row/"
        "per-polymer array scan (targets length 13 or 194) across the "
        "fixed 9-file FFW-vs-ML signed lineage fire 1 enumerated, to "
        "confirm no missing array has landed since; ran a positive "
        "control by planting a decoy 13-element list into an in-memory "
        "copy of the KPI and confirming the same scanner detects it, so "
        "a clean scan cannot be mistaken for a broken one. (2) Evaluated "
        "the 'honest re-scope hatch' this fire's STATE.json flagged as "
        "available (an analytic, non-resampling small-sample interval "
        "for the R2 gap computed purely from published aggregate "
        "r2/mae/rmse/pearson_r and n=13): tested the only candidate "
        "method that needs no per-row data (Olkin & Finn 1995 asymptotic "
        "R^2 variance formula) against the actual published numbers and "
        "found it breaks on this claim in three independent ways -- see "
        "rescope_hatch_feasibility in the diagnostic. Re-read the "
        "Polyverse melt-viscosity rights.json directly to confirm "
        "decision.decision_receipt is still null (counsel review still "
        "pending, unchanged since fire 2)."
    ),
    "freshness_result": diag["freshness_scan"],
    "rights_recheck": diag["rights_recheck"],
    "rescope_hatch_evaluation": diag["rescope_hatch_feasibility"],
    "why_rescope_hatch_not_invoked": (
        "The item's done_criterion opens a re-scope hatch on this final "
        "fire ONLY as an honest option, not an obligation -- and this "
        "fire's own predecessor STATE.json framed the candidate re-scope "
        "explicitly as something to attempt 'IF' it can be done "
        "honestly. It cannot: every analytically tractable shortcut "
        "either (a) uses n=194 rows and silently drops the "
        "clustering the pre-registered method exists to respect -- "
        "SE=0.0434 on the row-level Olkin-Finn formula, an order of "
        "magnitude tighter than what 13 independent clusters could "
        "support, which is exactly the anti-conservative failure mode "
        "this campaign's governance text calls out by name (2026-08-05: "
        "'a deliberately weak attack ... licensed a survival'); (b) "
        "relabels n=13 into the same formula without recomputing from "
        "actual per-cluster values, which is a plug-in, not a "
        "derivation, and produces a number (SE=0.1081) with no "
        "defensible sampling-distribution meaning; or (c) is undefined "
        "for B4 because HistGBM's fitted-parameter count was never "
        "persisted as an integer ('many (histogram GBM leaves)'), so "
        "degrees-of-freedom cannot even be computed at n=13. Reporting "
        "any of these three numbers as 'the CI, honestly re-scoped' "
        "would itself be exactly the fabricated-attack failure mode "
        "this campaign's rules forbid: a number engineered to look like "
        "it satisfies the acceptance criterion without carrying the "
        "statistical grounding the criterion requires. An honest "
        "re-scope must still be a SOUND method with reduced power, not "
        "an unsound method dressed as one -- this claim has no sound "
        "candidate available without either the rights-cleared per-row "
        "arrays or a persisted per-cluster breakdown, neither of which "
        "exists."
    ),
    "positive_control": {
        "planted_defect": diag["positive_control"]["planted_defect"],
        "how_planted": diag["positive_control"]["how_planted"],
        "detected": diag["positive_control"]["detected"],
        "evidence": diag["positive_control"]["evidence"],
        "note": (
            "This is a BLOCKED verdict, which the item does not require "
            "a positive control for (that requirement is specific to "
            "CLAIM_SURVIVED verdicts). Included anyway to prove the "
            "freshness scan that reported zero real hits is not a "
            "silently-broken scan."
        ),
    },
    "supersedes": None,
    "supersedes_note": (
        "Nothing is superseded. Fire 2's BLOCKED_RIGHTS finding "
        "(fire_id 20260812T050001-574491-f43fd01f90c2) is confirmed "
        "still current, not corrected -- this receipt is additive: it "
        "closes out the item's 3rd and final permitted fire with a "
        "terminal disposition, not a correction to fire 1 or fire 2."
    ),
    "human_action_needed": (
        "Unchanged from fire 2: counsel review of the Georgia Tech "
        "Research Corporation General Public Use License Agreement "
        "governing the Polyverse melt-viscosity dataset "
        "(amphora-viscosity-score/reference/mvp20/quarantine/feedback_v2/"
        "exclusions/polyverse_melt_viscosity-3cd923b4d67399f9.rights.json, "
        "rights_decision_id rights_polyverse_melt_viscosity, "
        "decision.decision_receipt still null as of this fire), "
        "specifically whether producing ONE additional narrow "
        "derivative -- signed per-row/per-polymer actual-vs-predicted "
        "arrays for the SAME already-fit and already-disclosed B3/B4 "
        "models, used only to compute an uncertainty interval around an "
        "already-published aggregate statistic -- falls inside or "
        "outside the 'physically quarantine all derivatives' basis. "
        "This item has now exhausted its 3 permitted campaign fires "
        "without that clearance; it cannot make further progress "
        "without either (1) counsel clearing the narrow derivative "
        "above, or (2) a human deciding to accept the "
        "'physics>=ML, underpowered' restatement without the "
        "pre-registered quantified interval (a decision this cron does "
        "not have authority to make, since the item's own acceptance "
        "criterion requires the numeric interval, not just a qualitative "
        "restatement)."
    ),
    "does_not_close": [
        "Does not modify the FFW KPI, the FFW scientific receipt, the "
        "conformal+AD KPI or receipt, docs/mission.md, or the "
        "66-receipt master manifest.",
        "Does not edit, delete, or modify fire 1's or fire 2's "
        "checkpoint receipts or the data-acquisition-queue.jsonl lines "
        "they mirrored -- all remain byte-identical.",
        "Does not open, parse, or derive any value from the underlying "
        "quarantined Polyverse melt-viscosity row-level CSV or its "
        "quarantine/normalized/*.jsonl.gz form -- reads only already-"
        "signed lineage JSON and rights metadata field values.",
        "Does not compute, report, or imply any numeric confidence "
        "interval for the R2(B3)-R2(B4) gap -- the whole point of this "
        "receipt is that no sound one is currently derivable.",
        "Does not resolve the CONTEXT_ONLY/promotion_eligible=false "
        "rights question -- that remains the pending human/counsel "
        "action, now with 0 of 3 fires remaining on this item.",
    ],
    "provenance": {
        "harness_sha256": {"run_final_disposition_audit.py": harness_sha},
        "prior_checkpoints_referenced": {
            "fire1_cluster_bootstrap_data_audit_v1_sha256": fire1_ckpt_sha256,
            "fire2_rights_boundary_audit_v1_sha256": fire2_ckpt_sha256,
        },
    },
    "reproducibility": {
        "byte_identical": True,
        "two_replay_sha256_gate": "PASS",
        "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "third_replay_sha256": third_sha,
        "determinism": (
            "pure-python re-derivation from already-in-tree, already-"
            "hashed JSON files (a fixed 9-file lineage list, not a live "
            "directory walk, so it stays deterministic even while other "
            "concurrent lanes write unrelated receipts elsewhere in the "
            "shared module tree this hour); no RNG, no network, no "
            "wall-clock reads at run time."
        ),
    },
    "signing_key": {
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "role": "PHASE0_EVALUATOR",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": eval_pin,
        "used_for": "AUDIT_ONLY R-C04 checkpoint receipt under evidence/phase0/repairs/R-C04/attempts/",
    },
    "reviewer_reference": {
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "role": "PHASE0_INTERNAL_REVIEWER",
        "derives_pinned_trust_store_key_id": rev_pin,
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-r-c04-final-disposition-checkpoint+json"
sig = eval_sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": {
        "payload": base64.standard_b64encode(body).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": eval_key_id, "sig": sig_b64}],
    },
}
out = EV / "final-disposition-v1-receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
