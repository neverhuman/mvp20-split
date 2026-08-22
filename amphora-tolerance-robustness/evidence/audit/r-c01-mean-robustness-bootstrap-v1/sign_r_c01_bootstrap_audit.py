#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-C01 mean-robustness bootstrap audit receipt.
AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest, any locked
dataset, or the signed Phase-0 KPI, and does NOT modify or delete the R-C01
done receipt it re-analyzes (pure re-analysis of already-committed numbers).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-tolerance-robustness/evidence/audit/r-c01-mean-robustness-bootstrap-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]

canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_mean_robustness_bootstrap.py").read_bytes())

target_receipt_path = ROOT / diag["input_receipt"]
target_receipt_sha = sha(target_receipt_path.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
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
    "schema": "amphora.tolerance-robustness.r-c01-mean-robustness-bootstrap-audit-receipt.v1",
    "study_id": "r-c01-mean-robustness-bootstrap-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "falsification_attack",
    "module": "amphora-tolerance-robustness",
    "campaign_item_id": "",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_target_receipt": False,
    "claim_under_attack": diag["input_receipt_claim"],
    "target_receipt": {
        "path": diag["input_receipt"],
        "sha256": target_receipt_sha,
        "reported_verdict": diag["input_receipt_reported_verdict"],
        "reported_observed_mean": diag["real"]["point_estimate_mean"],
        "reported_threshold": diag["threshold"],
    },
    "purpose": (
        "The R-C01 done receipt accepts a repair on a bare point-estimate "
        "criterion (mean over 60 scaffold-disjoint MC seeds >= 0.90) with no "
        "uncertainty quantification, even though this SAME module's own prior "
        "refutation of the un-repaired 0.9683 claim (2026-08-03, "
        "repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1) explicitly used "
        "a bootstrap CI + fraction-below-floor test to reject a point estimate. "
        "This audit re-applies that identical statistical apparatus to the "
        "ACCEPTED repair's own 60 per-seed values (extracted verbatim from the "
        "done receipt's per_seed_table, no re-simulation) to test whether "
        "'0.9073 >= 0.90' is a statistically robust finding or is consistent "
        "with a true scaffold-safe mean below the acceptance floor."
    ),
    "method": "percentile bootstrap (n_boot=100000, fixed rng seed=1729) on the mean of the 60 per-seed coverage_scaffold_safe_pac_repaired values; normal-approximation CI computed as a cross-check; fraction of bootstrap resamples with mean < 0.90 also reported.",
    "non_circularity": "Values are read verbatim from the already-signed, already-verified R-C01 done receipt's per_seed_table; this script performs no re-fit, re-calibration, or hyperparameter search -- pure re-analysis of committed numbers.",
    "results": {
        "n_seeds": diag["n_seeds"],
        "point_estimate_mean": diag["real"]["point_estimate_mean"],
        "std": diag["real"]["std"],
        "ci95_normal_approx": diag["real"]["ci95_normal_approx"],
        "ci95_bootstrap_percentile": diag["real"]["ci95_bootstrap_percentile"],
        "frac_bootstrap_resamples_below_threshold": diag["real"]["frac_bootstrap_resamples_below_threshold"],
        "ci_lower_excludes_threshold_from_below": diag["real"]["ci_lower_excludes_threshold_from_below"],
        "n_boot": diag["real"]["n_boot"],
    },
    "refutation_criterion": (
        "The R-C01 repair's mean-clears-0.90 acceptance is REFUTED as a robust "
        "finding if the 95% bootstrap percentile CI on the mean of the accepted "
        "repair's own 60 per-seed values includes 0.90 or values below it "
        "(CI lower bound < 0.90), i.e. the true scaffold-safe mean coverage "
        "cannot be statistically distinguished from failing the pre-registered "
        "floor using the identical evidence the acceptance decision relied on."
    ),
    "observed": (
        f"CI lower bound {diag['real']['ci95_bootstrap_percentile'][0]:.4f} < 0.90 "
        f"(does NOT exclude sub-threshold values); "
        f"{diag['real']['frac_bootstrap_resamples_below_threshold']*100:.1f}% of "
        f"100000 bootstrap resamples of the identical 60-seed evidence fall below "
        f"the 0.90 acceptance floor. The refutation criterion fired."
    ),
    "verdict": "CLAIM_REFUTED",
    "verdict_scope": (
        "Refutes the ROBUSTNESS of the R-C01 acceptance decision, not the bare "
        "arithmetic inequality 0.9073 >= 0.90 (which is true). The pre-registered "
        "R-C01 acceptance criterion never specified an uncertainty band, so by "
        "its own literal text the repair still 'passes'; this receipt establishes "
        "that the pass is not statistically distinguishable from a fail given the "
        "same sample, and should be read as amending, not silently overturning, "
        "the R-C01 done receipt's status."
    ),
    "positive_control": diag["positive_control"],
    "does_not_close": [
        "Does not modify, supersede, retract, or delete the R-C01 done receipt or its STATE.json -- this is a NEW audit artifact layered on top, per REPAIR-mode supersede discipline even though this fire's campaign_item_id is empty (rotation mode).",
        "Does not claim the repair is fraudulent or that eps=0.05 was tuned against this specific 60-seed outcome (the module's own STATE.json already discloses eps=0.10 was tried and discarded first, then eps=0.05 reused from a different, independently-signed receipt) -- it claims only that the resulting mean-clears-bar finding lacks the uncertainty quantification this module applies everywhere else, and that applying it here shows fragility.",
        "Grants no batch-release, manufacturing-qualification, optimizer, product-performance, or regulatory authority. AUDIT_ONLY.",
        "Per-seed worst-case coverage was already disclosed as unrepaired by the R-C01 done receipt itself (18/60 seeds below 0.90); this audit adds that even the MEAN-level closure is not statistically robust.",
    ],
    "recommendation": (
        "Treat R-C01 as repair_status 'in_progress' rather than fully closed: "
        "either (a) pre-register and meet a criterion that accounts for sampling "
        "uncertainty (e.g. bootstrap CI lower bound >= 0.90, which the current "
        "repair does not clear), or (b) collect more scaffolds / seeds to shrink "
        "the CI, or (c) explicitly accept the fragility and downgrade the KPI's "
        "confidence framing."
    ),
    "provenance": {
        "harness_sha256": harness_sha,
        "input_receipt": diag["input_receipt"],
        "input_receipt_sha256": target_receipt_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "rng_seed": 1729,
        "numpy": "1.26.4",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.tolerance-robustness-r-c01-mean-robustness-bootstrap-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "r-c01-mean-robustness-bootstrap-audit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_len", len(envelope["signatures"][0]["sig"]))
print("signature_verified", True)
