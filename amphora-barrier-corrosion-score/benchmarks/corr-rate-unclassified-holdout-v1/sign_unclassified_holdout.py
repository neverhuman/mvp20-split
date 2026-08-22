#!/usr/bin/env python3
"""DSSE-Ed25519-sign the corr-rate-unclassified-holdout-v1 AUDIT_ONLY
falsification receipt for amphora-barrier-corrosion-score. AUDIT_ONLY: signs
an audit receipt under the module's benchmarks/ dir; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED / PRE_PHASE_0), does NOT modify the
portfolio manifest, any locked dataset, or any signed Phase-0 KPI (this
receipt attacks corr-rate-family-safe-qspr-kpi.v1.dsse.json but does not
edit that KPI file)."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-barrier-corrosion-score/benchmarks/corr-rate-unclassified-holdout-v1"
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
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (BENCH / "result.canonical.json").read_bytes()
runA = (BENCH / "result.runA.json").read_bytes()
runB = (BENCH / "result.runB.json").read_bytes()
assert canon == runA == runB, "two-replay bytes differ"
canon_sha = sha(canon)
res = json.loads(canon)
harness_sha = sha((BENCH / "corr_rate_unclassified_holdout.py").read_bytes())

assert res["verdict"] == "CLAIM_SURVIVED"
assert res["positive_control"]["detected"] is True, "positive control did not fire -- cannot license a survival"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.barrier-corrosion-score.corr-rate-unclassified-holdout-receipt.v1",
    "module": "amphora-barrier-corrosion-score",
    "benchmark": "corr-rate-unclassified-holdout-v1",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "purpose": (
        "ROTATION-mode falsification attack on this module's strongest "
        "standing rights-clean claim: evidence/phase0/kpis/corr-rate-"
        "family-safe-qspr-kpi.v1.dsse.json (GroupKFold(group=metallurgical_"
        "family, 5-fold) HistGBM R2=0.132087). Prior attacks varied the CV "
        "grouping axis (material string -> metallurgical family -> true "
        "leave-one-family-out -> leave-one-source-out) or the environment "
        "axis (marine domain shift). This attack escalates to a "
        "previously untested axis: the classifier's own declared coverage "
        "gap. The KPI receipt's own payload lists, verbatim, an 'awaiting' "
        "Phase-1 item -- 'extend metallurgical-family taxonomy beyond the "
        "94.58% keyword/regex classifier coverage (417 unclassified rows "
        "excluded)' -- and every prior receipt in this module (family-"
        "safe, family-lofo, marine-envelope, feature-integrity, source-"
        "lofo) restricts to the classified_subset before drawing any "
        "train/test split, so those 417 rows have never been scored by "
        "anything. This benchmark fits the identical model on all 7,282 "
        "classified rows (the deployed-equivalent full fit) and scores it "
        "on exactly that never-scored population."),
    "attacks_claim": res["attacks_claim"],
    "attack_description": res["attack_description"],
    "refutation_criterion": res["refutation_criterion"],
    "dataset": res["dataset"],
    "cohort": res["cohort"],
    "results": res["results"],
    "positive_control": res["positive_control"],
    "verdict": res["verdict"],
    "scope_honesty": res["scope_honesty"],
    "honest_interpretation": (
        "Fit on all 7,282 classified rows (identical feature engineering/"
        "HistGBM hyperparameters/seed=0 as corr-rate-family-safe-v1) and "
        "scored on the 417-row unclassified holdout, the model achieves "
        "R2=0.244000 and beats the global-mean-of-train baseline on RMSE "
        "by 16.440851 pct. Both pre-registered refutation legs (r2<=0, "
        "error_reduction<=0) are cleanly missed, so this genuinely "
        "untested axis SURVIVES -- and R2 on this out-of-taxonomy holdout "
        "is actually HIGHER than the promoted family-safe GroupKFold R2 "
        "(0.132087) and the family-LOFO family-weighted mean (0.015964), "
        "suggesting the classifier's blind spot is not concentrated on "
        "chemically unusual, hard-to-predict materials -- the composition "
        "and environment features the model actually uses generalize "
        "across the classifier's family/no-family boundary about as well "
        "as they do within it. This does not, by itself, resolve the two "
        "still-standing, still-unrepaired REFUTED verdicts against this "
        "same KPI (corr-rate-marine-envelope-v1: environment domain shift "
        "to true seawater rows, R2=-0.450740; corr-rate-source-lofo-v1: "
        "leave-one-source-out, 61/83=73.5 pct of eligible sources R2<=0) "
        "-- it closes off ONE possible additional failure mode (out-of-"
        "taxonomy material extrapolation) without touching those two open "
        "refutations, which remain in force and unsuperseded in "
        "evidence/phase0/kpis/RETRACTION-INDEX.md as of this fire. The "
        "positive control (full label-shuffle of the same 417-row test "
        "targets, same predictions) correctly triggers the refutation "
        f"criterion (shuffled R2={res['positive_control']['evidence']['shuffled_r2']:.6f}), "
        "confirming this harness can "
        "actually detect degenerate performance on this exact population/"
        "model/metric and did not survive merely because the criterion "
        "was unreachable. Scope ceiling unchanged: bare-metal/alloy "
        "substrate corrosion (NIST CORR-DATA), not organic-coating "
        "barrier performance; no product-performance authority."
    ),
    "open_unrepaired_refutations_against_same_kpi": {
        "corr-rate-marine-envelope-v1": "environment domain shift (train=non-marine, test=true-seawater), R2=-0.450740, CLAIM_REFUTED 2026-08-15, no repair item opened",
        "corr-rate-source-lofo-v1": "leave-one-source-out (220 sources, 83 eligible), 61/83=73.5pct eligible sources R2<=0, CLAIM_REFUTED 2026-08-18, no repair item opened",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_result_sha256": canon_sha,
        "runA_result_sha256": sha(runA),
        "runB_result_sha256": sha(runB),
        "byte_identical": canon == runA == runB,
        "harness_sha256": harness_sha,
        "determinism": res["determinism"],
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under amphora-barrier-corrosion-score/benchmarks/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.barrier-corrosion-unclassified-holdout+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "corr-rate-unclassified-holdout-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_canonical_sha256", canon_sha)
print("harness_sha256", harness_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
