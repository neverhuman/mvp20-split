#!/usr/bin/env python3
"""DSSE-Ed25519-sign the corr-rate-family-lofo-v1 AUDIT_ONLY falsification
receipt for amphora-barrier-corrosion-score. AUDIT_ONLY: signs an audit
receipt under the module's benchmarks/ dir; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED / PRE_PHASE_0), does NOT modify the
portfolio manifest, any locked dataset, or any signed Phase-0 KPI (this
receipt attacks corr-rate-family-safe-qspr-kpi.v1.dsse.json but does not
edit it -- a survival adds nuance, it does not supersede)."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-barrier-corrosion-score/benchmarks/corr-rate-family-lofo-v1"
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


canon = (BENCH / "result.runA.json").read_bytes()
runA = (BENCH / "result.runA.json").read_bytes()
runB = (BENCH / "result.runB.json").read_bytes()
assert canon == runA == runB, "two-replay bytes differ"
canon_sha = sha(canon)
res = json.loads(canon)
harness_sha = sha((BENCH / "corr_rate_family_lofo.py").read_bytes())
pc = json.loads((BENCH / "positive_control.json").read_bytes())
pc_sha = sha((BENCH / "positive_control.json").read_bytes())
pc_harness_sha = sha((BENCH / "corr_rate_family_lofo_positive_control.py").read_bytes())

assert pc["detected"] is True, "positive control must show detected=True to license a survival"
assert res["verdict"] == "CLAIM_SURVIVED"

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
    "schema": "amphora.barrier-corrosion-score.corr-rate-family-lofo-receipt.v1",
    "module": "amphora-barrier-corrosion-score",
    "benchmark": "corr-rate-family-lofo-v1",
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
        "standing claim: evidence/phase0/kpis/corr-rate-family-safe-qspr-"
        "kpi.v1.dsse.json (GroupKFold(group=metallurgical_family, 5-fold) "
        "HistGBM R2=0.132087 on NIST CORR-DATA, n=7282, 17 families), "
        "promoted 2026-08-04 (campaign item V1-KPI-BARR) as 'the module's "
        "strongest rights-clean empirical claim'. The KPI's own 5-fold "
        "GroupKFold(family) split naturally isolates the 2 largest of 17 "
        "families (stainless_steel n=1976, nickel_alloy n=1888, 53.1% of "
        "the classified cohort) into solo folds and packs the other 15 "
        "into only 3 folds, so its reported R2 is sample-weighted (per-row) "
        "and dominated by whichever families are large -- not a fair test "
        "of the capability string's own claim, 'Leave-metallurgical-"
        "family-out ... generalization estimate.'"),
    "attacks_claim": res["attacks_claim"],
    "attack_description": res["attack_description"],
    "refutation_criterion": res["refutation_criterion"],
    "min_eligible_n_test": res["min_eligible_n_test"],
    "dataset": res["dataset"],
    "cohort": res["cohort"],
    "results": res["results"],
    "comparison_to_promoted_kpi": res["comparison_to_promoted_kpi"],
    "verdict": res["verdict"],
    "scope_honesty": res["scope_honesty"],
    "honest_interpretation": (
        "True 17-way Leave-One-Family-Out gives a family-weighted "
        "(unweighted per family) mean R2 of 0.015964 -- essentially "
        "noise-level -- versus the promoted KPI's sample-weighted "
        "R2=0.132087. 11 of 15 eligible families (n_test>=20) score "
        "R2>0, a bare majority (73.3%), so the pre-registered refutation "
        "criterion (family-weighted mean R2<=0 OR majority of eligible "
        "families R2<=0) is NOT met and the claim SURVIVES -- but only "
        "just. Four sizeable families generalize badly when genuinely "
        "held out: titanium (n=658, R2=-0.0257), tantalum_niobium "
        "(n=266, R2=-0.6616), zinc (n=60, R2=-0.799), magnesium (n=57, "
        "R2=-0.7081). The two families the KPI's own 5-fold split "
        "happened to isolate cleanly (stainless_steel, nickel_alloy, "
        "53.1% of rows) are also the two families that generalize best "
        "(R2=0.166, R2=0.118) and are what keep the sample-weighted "
        "number and the family-weighted mean both nominally positive. "
        "This does not refute the KPI's pre-registered gate, but it does "
        "refute the SAFE reading of 'R2=0.132 means the model generalizes "
        "to novel metallurgical families' -- it generalizes reliably to "
        "the 2 dominant chemistries in the dataset and unreliably or not "
        "at all to roughly a quarter of the smaller/rarer ones. This "
        "nuance is not present anywhere in the promoted KPI's payload."
    ),
    "positive_control": {
        "planted_defect": pc["planted_defect"],
        "how_planted": pc["how_planted"],
        "detected": pc["detected"],
        "evidence": (
            "Real input: family_weighted_mean_r2=%.6f, %d/%d eligible "
            "families R2>0, majority_positive=%s, refuted=%s (matches "
            "the main run, not refuted). Hostile-null-shuffled-label "
            "copy of the identical input: family_weighted_mean_r2=%.6f, "
            "%d/%d eligible families R2>0, majority_positive=%s, "
            "refuted=%s. The attack correctly failed to refute on the "
            "real (partially-generalizing) input and correctly refuted "
            "on the planted-defect (fully noise) input." % (
                pc["real_input"]["family_weighted_mean_r2"],
                pc["real_input"]["n_eligible_positive"], pc["real_input"]["n_eligible"],
                pc["real_input"]["majority_positive"], pc["real_input"]["refuted"],
                pc["defect_input"]["family_weighted_mean_r2"],
                pc["defect_input"]["n_eligible_positive"], pc["defect_input"]["n_eligible"],
                pc["defect_input"]["majority_positive"], pc["defect_input"]["refuted"],
            )
        ),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_result_sha256": canon_sha,
        "runA_result_sha256": sha(runA),
        "runB_result_sha256": sha(runB),
        "byte_identical": canon == runA == runB,
        "harness_sha256": harness_sha,
        "positive_control_harness_sha256": pc_harness_sha,
        "positive_control_output_sha256": pc_sha,
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
ptype = "application/vnd.amphora.barrier-corrosion-family-lofo+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "corr-rate-family-lofo-receipt.v1.dsse.json"
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
