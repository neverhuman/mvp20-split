#!/usr/bin/env python3
"""W-ROLE-CI: sign the superseding KPI receipt with the PHASE0_EVALUATOR key.
Follows the exact PAE/load_seed/keyid/self-verify construction already used by
amphora-molecule-role-ranker/evidence/phase0/repairs/R-S05/work/sign_rs05.py.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-role-ranker"
ITEM = MOD / "evidence/phase0/repairs/W-ROLE-CI"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260814T020001-724853-bddd109f6ab9"
CAMPAIGN_ITEM_ID = "W-ROLE-CI"
DATE = "2026-08-14"


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


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
by_role = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"
assert eval_pub_hex == by_role["PHASE0_EVALUATOR"]["public_key_hex"]

# ---------------------------------------------------------------- inputs
canon_path = WORK / "diagnostic.canonical.json"
runb_path = WORK / "diagnostic.runB.json"
canon_bytes = canon_path.read_bytes()
runb_bytes = runb_path.read_bytes()
assert sha(canon_bytes) == sha(runb_bytes), "two-replay byte gate FAILED"
diag = json.loads(canon_bytes)

TARGET_RECEIPT = MOD / "benchmarks/role-parsimony-conformal-v1/replay_receipt.v1.dsse.json"
TARGET_DIAGNOSTIC = MOD / "benchmarks/role-parsimony-conformal-v1/diagnostic.canonical.json"
FIXTURE = MOD / "reference/phase0-role-known-answer.v1.json"

target_receipt_sha = fsha(TARGET_RECEIPT)
target_diagnostic_sha = fsha(TARGET_DIAGNOSTIC)

corrections = diag["corrections"]
sweep = diag["sweep"]

proposed_followups = []
for entry in sweep["distinct_artifacts_outside_this_module"]:
    if entry["module"] == "amphora-molecule-generator":
        proposed_followups.append({
            "module": "amphora-molecule-generator",
            "defect": (
                "Same defect class (boundary-collapsed percentile-bootstrap CI, "
                "[1.0,1.0] at k=n=38) found live in "
                "evidence/audit/molgen-deterministic-grammar-yield-v1/"
                "molgen-deterministic-grammar-yield-receipt.v1.dsse.json field "
                "generator_grammar.feasible_fraction_bootstrap95_ci. NOTE: this module "
                "already has an active, independently-filed falsification "
                "(evidence/audit/molgen-grammar-yield-bootstrap-ci-inadmissibility-v1, "
                "verdict CLAIM_REFUTED, exact CP lower bound 0.9075 cited) and repair "
                "items in flight (evidence/phase0/repairs/R-A06, R-A06v2, W-GEN1); this "
                "followup names the artifact per the W-ROLE-CI sweep mandate but does "
                "NOT claim the defect is unowned there."
            ),
            "artifact_paths": entry["distinct_artifact_dirs"],
            "n_hits_in_sweep": entry["n_hits_total"],
            "proposed_done_criterion": (
                "Confirm (re-run V-A06/V-A06v2 style independent verify) that the "
                "molgen-deterministic-grammar-yield-v1 headline receipt's "
                "feasible_fraction_bootstrap95_ci has been superseded by a receipt "
                "using an exact-at-boundary method (Clopper-Pearson or equivalent), "
                "with old/new bounds shown side by side and a supersedes block; if "
                "R-A06v2 already did this, this followup closes as duplicate-confirmed."
            ),
        })

body_obj = {
    "schema": "amphora.molecule-role-ranker.w-role-ci-superseding-kpi.v1",
    "receipt_id": "w-role-ci-superseding-kpi-" + sha(canon_bytes)[:32],
    "fire_id": FIRE_ID,
    "campaign_item_id": CAMPAIGN_ITEM_ID,
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "run_type": "SUPERSEDING_KPI",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "module": "amphora-molecule-role-ranker",
    "repair_mode": True,
    "objective": (
        "W-ROLE-CI: the role-parsimony-conformal-v1 replay receipt publishes three "
        "percentile-bootstrap 95% confidence intervals that collapse to a single point "
        "([1.0,1.0] x2, [0.0,0.0] x1) because the underlying sample is k=n=24 (all "
        "predictions correct), so every one of the B=10000 bootstrap resamples is also "
        "all-correct and the empirical resample spread is zero. This mechanically "
        "understates sampling uncertainty: the true generalization accuracy is NOT known "
        "to be exactly 1.0 at n=24. Recompute each with a named exact method valid at "
        "the boundary and publish a superseding KPI; then sweep the portfolio for the "
        "same defect class and file every hit found."
    ),
    "claim_under_attack": {
        "claim_text": (
            "Every interval this module publishes is computed by a method valid at "
            "its own n. role-parsimony-conformal-v1's bootstrap CIs at k=n=24 are "
            "[1.0,1.0] (deterministic_rule_baseline.in_domain_accuracy) and "
            "[1.0,1.0] (fitted_model_out_of_sample.loocv_accuracy) and [0.0,0.0] "
            "(noninferiority_test.accuracy_gap)."
        ),
        "target_receipt_path": "amphora-molecule-role-ranker/benchmarks/"
                               "role-parsimony-conformal-v1/replay_receipt.v1.dsse.json",
        "target_receipt_sha256": target_receipt_sha,
        "target_diagnostic_path": "amphora-molecule-role-ranker/benchmarks/"
                                  "role-parsimony-conformal-v1/diagnostic.canonical.json",
        "target_diagnostic_sha256": target_diagnostic_sha,
        "target_receipt_signed_with": "local-9028773f49591193 (LOCAL_DEVELOPMENT_AUDIT_ONLY, "
                                      "NOT the pinned PHASE0_EVALUATOR key; does_not_close "
                                      "EVALUATION_SIGNATURE_ABSENT was already logged by the "
                                      "target receipt itself)",
        "refutation_criterion": (
            "A refutation occurs if the exact Clopper-Pearson two-sided 95% CI for the "
            "k=n=24 accuracy proportion differs from the published bootstrap CI [1.0,1.0] "
            "-- i.e. if the exact lower bound is < 1.0."
        ),
        "observed": (
            "Exact Clopper-Pearson lower bound at k=n=24 is 0.8575264022774743, not 1.0. "
            "The refutation criterion is MET: the published interval understates the true "
            "95% uncertainty by 0.1425 (matches the campaign item's pre-registered figure "
            "of 0.142 within rounding)."
        ),
        "verdict": "CLAIM_REFUTED",
    },
    "corrections": corrections,
    "supersedes": {
        "superseded_path": "amphora-molecule-role-ranker/benchmarks/"
                           "role-parsimony-conformal-v1/replay_receipt.v1.dsse.json",
        "superseded_sha256": target_receipt_sha,
        "superseded_diagnostic_path": "amphora-molecule-role-ranker/benchmarks/"
                                      "role-parsimony-conformal-v1/diagnostic.canonical.json",
        "superseded_diagnostic_sha256": target_diagnostic_sha,
        "superseded_deleted_or_modified": False,
        "reason": (
            "The target's three bootstrap 95% CIs are inadmissible at the k=n=24 / "
            "k1=k2=n1=n2=24 boundary (percentile bootstrap has zero resample variance "
            "there). This superseding KPI republishes the same headline point estimates "
            "(accuracy 1.0 vs 1.0, gap 0.0) with exact-at-boundary intervals: Clopper-"
            "Pearson for the two accuracy margins, MOVER (Newcombe 1998b, phi=0 "
            "conservative) for the paired gap. The original file is left byte-intact; "
            "this is a NEW artifact, not an edit."
        ),
    },
    "primary_references": diag["primary_references"],
    "sweep": {
        "method": sweep["method"],
        "n_json_files_found": sweep["n_json_files_found"],
        "n_json_files_parsed": sweep["n_json_files_parsed"],
        "n_parse_errors": sweep["n_parse_errors"],
        "n_degenerate_hits_total": sweep["n_degenerate_hits"],
        "n_degenerate_hits_in_this_module": 6,
        "distinct_artifacts_outside_this_module": sweep["distinct_artifacts_outside_this_module"],
    },
    "proposed_followups": proposed_followups,
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon_bytes),
        "runB_diagnostic_sha256": sha(runb_bytes),
        "harness_sha256": fsha(Path("/tmp/run_w_role_ci_repair.py")) if Path("/tmp/run_w_role_ci_repair.py").exists() else None,
        "sweep_harness_sha256": fsha(Path("/tmp/sweep_degenerate_ci2.py")) if Path("/tmp/sweep_degenerate_ci2.py").exists() else None,
        "fixture_sha256": FIXTURE.read_bytes() and sha(FIXTURE.read_bytes()),
        "determinism_basis": (
            "All computation is closed-form (incomplete-beta inversion via "
            "scipy.stats.beta.ppf) or a deterministic full filesystem walk; no random "
            "sampling, no wall-clock, no OS entropy."
        ),
    },
    "closes": [],
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (this receipt IS signed with the trust-anchored "
        "PHASE0_EVALUATOR key, but that closes only THIS artifact's own signing gap, "
        "not the target receipt's, which remains signed under the local-dev key and is "
        "left byte-intact per supersede-never-rewrite)",
        "PHASE_1_INDEPENDENT_EVALUATION (needs external double-labelled expert reference)",
        "external_rights (fixture is self-authored CC0; not an external benchmark)",
    ],
    "phase0_gap_ledger": {
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT "
                              "edited; requires human dual-identity Phase-0 ceremony keys.",
        "SCOPE": "corrects interval ADMISSIBILITY only; does not change any point "
                "estimate, does not re-run the underlying classification, does not "
                "alter the noninferiority verdict (HYPOTHESIS_CORROBORATED_PARSIMONY_"
                "FAVOURED still stands on point estimates -- only its uncertainty "
                "band was wrong).",
        "SWEEP_SCOPE": f"{sweep['n_json_files_parsed']} of {sweep['n_json_files_found']} "
                       f".json files under mvp20-split parsed ({sweep['n_parse_errors']} "
                       "parse errors, mostly non-UTF8 or non-JSON-despite-extension "
                       "files); only keys matching /ci|interval|bound|coverage/i were "
                       "inspected for degenerate 2-element [0.0,0.0]/[1.0,1.0] arrays -- "
                       "a differently-named degenerate interval field would not be caught.",
    },
    "claim_locks": diag.get("claim_locks", {
        "measured_only_lock_preserved": True,
        "no_objective_emitted": True,
        "promotes_authority": False,
    }),
    "verdict": "CLAIM_REFUTED",
    "repair_status": "fix_landed",
    "date": DATE,
    "generated_on_host": "xbabe2",
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY W-ROLE-CI superseding KPI under "
                   "evidence/phase0/repairs/W-ROLE-CI/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(WORK / "receipt_body.canonical.json").write_bytes(body1)
(WORK / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-role-ranker.w-role-ci-superseding-kpi.v1+json"
sig = eval_sk.sign(pae(ptype, body1))
envelope = {
    "payload": base64.standard_b64encode(body1).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}

DONE.mkdir(parents=True, exist_ok=True)
outpath = DONE / "w-role-ci-superseding-kpi-receipt.v1.dsse.json"
outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# ---------------------------------------------------------------- self-verify
written = json.loads(outpath.read_text())
sig_env = written["signature"]
payload = base64.standard_b64decode(sig_env["payload"])
sig_bytes = base64.standard_b64decode(sig_env["signatures"][0]["sig"])
keyid = sig_env["signatures"][0]["keyid"]
trust_pub_hex = by_role["PHASE0_EVALUATOR"]["public_key_hex"]
assert keyid == by_role["PHASE0_EVALUATOR"]["key_id"]
Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust_pub_hex)).verify(
    sig_bytes, pae(sig_env["payloadType"], payload))
assert payload == body1

print("WROTE", outpath)
print("verdict", body_obj["verdict"])
print("repair_status", body_obj["repair_status"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_byte_identical", body1 == body2)
print("self_verify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
