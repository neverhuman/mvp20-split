#!/usr/bin/env python3
"""R-C01 fire-2: DSSE-Ed25519-sign the DONE repair receipt for campaign item
R-C01 (amphora-tolerance-robustness). Acceptance criterion IS met this fire
(mean coverage_scaffold_safe_pac_repaired = 0.9073 >= 0.90 over the identical
pinned 60-seed scaffold-disjoint Monte Carlo protocol). Supersedes the
refuted split-conformal-prediction-openpoly-tg-kpi.v1.json coverage claim for
purposes of THIS repair item; does not rewrite or delete it.

Replicates the PAE / load_seed / payloadType / two-replay-gate / self-verify
construction used across this repo's sign_*.py scripts.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-tolerance-robustness"
REPAIR = MOD / "evidence/phase0/repairs/R-C01"
WORK = REPAIR / "work"
DONE = REPAIR / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
DATE = "2026-08-11"
FIRE_ID = "20260811T230001-2065209-f2dd3c8baffd"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes())


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


canon_bytes = (WORK / "pac_repair.canonical.json").read_bytes()
runB_bytes = (WORK / "pac_repair.runB.json").read_bytes()
assert canon_bytes == runB_bytes, "two-replay bytes differ"
pac_result = json.loads(canon_bytes)
pac_result_sha = sha(canon_bytes)
assert pac_result["acceptance"]["met"] is True, "refusing to write a done receipt: acceptance not met"

mondrian_diag_path = WORK / "mondrian_diagnostic.canonical.json"

superseded_kpi = MOD / "evidence/phase0/kpis/split-conformal-prediction-openpoly-tg-kpi.v1.json"
refuting_receipt = MOD / "evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/repeated-scaffold-monte-carlo-conformal-openpoly-tg-receipt.v1.dsse.json"
fire1_checkpoint = REPAIR / "attempts/r-c01-fire1-repair-checkpoint-receipt.v1.dsse.json"
pinned_attack_script = MOD / "evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/run_repeated_scaffold_conformal.py"
pac_source_script = MOD / "evidence/audit/training-conditional-pac-tolerance-openpoly-tg-v1/run_trainingcond_openpoly.py"

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
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

body_obj = {
    "schema": "amphora.tolerance-robustness.r-c01-repair-done.v1",
    "study_id": "amphora-tolerance-robustness-r-c01-pac-corrected-scaffold-repair-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "REPAIR done receipt, campaign item R-C01: scaffold-aware conformal repair of the OpenPoly Tg split-conformal marginal-coverage claim, re-attacked with the pinned 60-seed scaffold-disjoint Monte Carlo protocol",
    "module": "amphora-tolerance-robustness",
    "campaign_item_id": "R-C01",
    "fire_id": FIRE_ID,
    "date": DATE,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "resolution": "repair",
    "verdict": "CLAIM_SURVIVED",
    "repair_status": "fix_landed_survived",
    "claim_under_attack": pac_result["acceptance"]["criterion"],
    "acceptance_criterion": {
        "text": "mean coverage_scaffold_safe over the IDENTICAL 60-seed scaffold-disjoint MC protocol from the refuting receipt (same seeds, same splits, same attack script sha256) >= 0.90; calibration method may change, MC seeds/splits may never change.",
        "threshold": 0.90,
        "observed_mean": pac_result["acceptance"]["observed_mean"],
        "met": pac_result["acceptance"]["met"],
    },
    "repair_method": {
        "name": "Training-conditional PAC-corrected split-conformal rank (Vovk 2012)",
        "summary": (
            "Replaces the ordinary finite-sample split-conformal rank ceil((n_cal+1)(1-alpha)) "
            "with the smallest rank k' such that P_cal[true coverage >= 1-eps] >= 1-delta "
            "(Beta(k', n_cal+1-k') law, Vovk 2012), using eps=0.05, delta=0.05 REUSED "
            "VERBATIM AND UNCHANGED from this module's own already-signed prior receipt "
            "training-conditional-pac-tolerance-openpoly-tg-v1 (no new hyperparameter invented "
            "for this campaign item). Applied per-seed to the pinned scaffold-disjoint "
            "calibration set (n_cal ranges 7-133 across the 60 seeds); rank inflation is largest "
            "exactly where the scaffold-block assignment leaves the smallest, most volatile "
            "calibration pools."
        ),
        "pac_corrected_rank_source": {
            "path": str(pac_source_script.relative_to(ROOT)),
            "sha256": sha_file(pac_source_script),
            "function_reused": "pac_corrected_rank(n, eps, delta)",
            "modified": False,
        },
        "reused_parameters": {"PAC_EPS": 0.05, "PAC_DELTA": 0.05},
    },
    "rejected_alternatives_this_fire": pac_result["repair_attempts_this_fire"],
    "prior_fire_attempts": {
        "fire1_ledger_recorded": "weighted conformal (Tibshirani 2019, DEGENERATE), simplified scaffold CV+ (0.8825), correct Barber 2021 CV+ (0.8619) -- all insufficient",
        "fire1_checkpoint_receipt": {
            "path": str(fire1_checkpoint.relative_to(ROOT)),
            "sha256": sha_file(fire1_checkpoint),
        },
    },
    "scaffold_imbalance_diagnostic": pac_result["scaffold_imbalance_diagnostic"],
    "summary_stats": pac_result["summary_stats"],
    "per_seed_table": pac_result["draws"],
    "positive_control": pac_result["positive_control"],
    "pinned_attack": {
        "path": str(pinned_attack_script.relative_to(ROOT)),
        "sha256": sha_file(pinned_attack_script),
        "seeds": "0..59",
        "modified": False,
        "note": "Split logic duplicated verbatim (not imported) in the repair script; verified byte-identical baseline reproduction: mean coverage_scaffold_safe_baseline = 0.8745741048157474, matching the fire-1/original-attack recorded value exactly.",
    },
    "supersedes": {
        "superseded_path": str(superseded_kpi.relative_to(ROOT)),
        "superseded_sha256": sha_file(superseded_kpi),
        "superseded_deleted_or_modified": False,
        "reason": (
            "This receipt does not overwrite or delete split-conformal-prediction-openpoly-tg-kpi.v1.json; "
            "its 0.9683 marginal (random-split) coverage number is unaffected and stands for random splits. "
            "It DOES supersede, for scaffold-disjoint (deployment-realistic) coverage purposes, the refuted "
            "value of 0.8746 mean scaffold-safe coverage recorded in the refuting receipt below: the "
            "PAC-corrected calibration in this receipt restores mean scaffold-safe coverage to 0.9073, "
            "clearing this campaign item's pre-registered 0.90 acceptance bar."
        ),
    },
    "refuted_by": {
        "path": str(refuting_receipt.relative_to(ROOT)),
        "sha256": sha_file(refuting_receipt),
        "claim": "mean scaffold-safe coverage 0.8746 over 60 draws, CI [0.8497,0.8974] excludes 0.95",
    },
    "does_not_close": [
        "Per-seed worst-case coverage is NOT guaranteed >= 0.90: 18/60 seeds still individually fall below the 0.90 floor (min 0.5566), always the same extreme-scaffold-skew seeds (the 255-molecule and 71-molecule dominant scaffolds). This receipt closes the MEAN acceptance criterion only, as pre-registered; it does not claim per-seed / worst-case / training-conditional coverage at the individual-draw level.",
        "The random-split 0.9683 marginal coverage number in split-conformal-prediction-openpoly-tg-kpi.v1.json is untouched; this receipt only concerns scaffold-disjoint (deployment-shift) coverage.",
        "Grants no batch-release, manufacturing-qualification, optimizer, product-performance, or regulatory authority. AUDIT_ONLY.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_result_sha256": pac_result_sha,
        "runB_result_sha256": sha(runB_bytes),
        "byte_identical": canon_bytes == runB_bytes,
        "repair_script": "run_pac_corrected_scaffold_repair.py",
        "repair_script_sha256": sha_file(WORK / "run_pac_corrected_scaffold_repair.py"),
        "numpy": "1.26.4", "scipy": "1.16.3", "sklearn": "1.7.2", "pandas": "2.1.4", "rdkit": "2026.03.2",
    },
    "theory_references": pac_result["theory_references"],
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair done receipt under evidence/phase0/repairs/R-C01/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.tolerance-robustness-r-c01-repair-done+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "r-c01-pac-corrected-scaffold-repair-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("pac_result_sha256", pac_result_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
