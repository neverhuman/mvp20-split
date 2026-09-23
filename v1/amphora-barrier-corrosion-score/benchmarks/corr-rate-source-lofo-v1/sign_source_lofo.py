#!/usr/bin/env python3
"""DSSE-Ed25519-sign the corr-rate-source-lofo-v1 AUDIT_ONLY falsification
receipt for amphora-barrier-corrosion-score. AUDIT_ONLY: signs an audit
receipt under the module's benchmarks/ dir; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED / PRE_PHASE_0), does NOT modify the
portfolio manifest, any locked dataset, or any signed Phase-0 KPI (this
receipt attacks corr-rate-family-safe-qspr-kpi.v1.dsse.json's implicit
domain-generalization reading but does not edit that KPI file -- a
refutation of the SAFE READING adds nuance via a new benchmark receipt, it
does not delete or rewrite the prior receipt)."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-barrier-corrosion-score/benchmarks/corr-rate-source-lofo-v1"
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
harness_sha = sha((BENCH / "corr_rate_source_lofo.py").read_bytes())
pc_harness_sha = sha((BENCH / "corr_rate_source_lofo_positive_control.py").read_bytes())

assert res["verdict"] == "CLAIM_REFUTED"
assert res["results"]["majority_of_eligible_sources_positive"] is False
assert res["results"]["n_eligible_sources_r2_positive"] + res["results"]["n_eligible_sources_r2_nonpositive"] == res["results"]["eligible_sources_n_test_ge_min"]

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
    "schema": "amphora.barrier-corrosion-score.corr-rate-source-lofo-receipt.v1",
    "module": "amphora-barrier-corrosion-score",
    "benchmark": "corr-rate-source-lofo-v1",
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
        "family, 5-fold) HistGBM R2=0.132087), which has already survived "
        "attacks that varied the CV grouping axis (raw material string, "
        "metallurgical family, true leave-one-family-out) and been "
        "REFUTED-with-nuance on the ENVIRONMENT axis (corr-rate-marine-"
        "envelope-v1) and SURVIVED-with-nuance on a feature-integrity fix "
        "(corr-rate-feature-integrity-v1). This attack escalates to a "
        "previously untested axis: DATA PROVENANCE. NIST CORR-DATA is "
        "itself a compilation of 220 distinct original literature sources "
        "(corrosion handbooks, alloy-vendor bulletins, individual journal "
        "papers spanning decades of differing testing methodology, "
        "specimen prep, and author-specific rating-to-rate conversion). "
        "No prior receipt controlled for a model that has merely learned "
        "a source's own reporting convention rather than a transferable "
        "structure-composition-environment relationship, because most "
        "sources are family-specialized and family-safe/family-LOFO "
        "splits do not detect that confound."
    ),
    "attacks_claim": res["attacks_claim"],
    "attack_description": res["attack_description"],
    "refutation_criterion": res["refutation_criterion"],
    "min_eligible_n_test": res["min_eligible_n_test"],
    "dataset": res["dataset"],
    "cohort": res["cohort"],
    "model": res["model"],
    "results": res["results"],
    "comparison_to_promoted_kpi": res["comparison_to_promoted_kpi"],
    "verdict": res["verdict"],
    "scope_honesty": res["scope_honesty"],
    "data_integrity_note": (
        "One eligible source (n_test=33, 'Metals Handbook, Ninth Edition, "
        "Vol 13, Corrosion, ASM International, Metals Park, OH, 1987, p "
        "796') reports a corrosion-rate label with zero within-source "
        "variance in this fold (ss_tot==0), making its own R2 "
        "mathematically undefined (NaN); the harness's rnd() canonicalizer "
        "renders NaN as JSON null, so results.source_weighted_mean_r2 and "
        "comparison_to_promoted_kpi.loso_source_weighted_mean_r2 are "
        "reported as null rather than a poisoned numeric mean. This does "
        "NOT affect the verdict: the harness's own refuted computation is "
        "`(source_weighted_mean_r2 <= 0.0) or (not majority_positive)`, "
        "and NaN<=0.0 is False in IEEE-754/Python, so refuted resolves "
        "entirely on criterion (b) (majority_of_eligible_sources_positive "
        "is False), which is unambiguous and does not depend on the NaN "
        "source."
    ),
    "honest_interpretation": (
        "True Leave-One-Source-Out (GroupKFold, n_splits=213, one of the "
        "220 original literature sources held out per fold, identical "
        "feature engineering/HistGBM hyperparameters/seed=0 to the "
        "promoted KPI) on the same classified cohort (n=7282, 17 "
        "families) gives a sample-weighted OOF R2 of 0.18711 -- HIGHER "
        "than the promoted KPI's 0.132087 -- which by itself would look "
        "like a survival. But the pre-registered criterion for this "
        "attack was never the sample-weighted OOF number (that statistic "
        "is dominated by the largest sources, same failure mode the "
        "family-LOFO attack found for families); it was the SOURCE-"
        "weighted view: of the 83 eligible sources (n_test>=20, 130 "
        "smaller sources excluded), only 22 (26.5%) score R2>0 and 61 "
        "(73.5%) score R2<=0, so a clear majority of independent data-"
        "collection sources fail to generalize when genuinely held out. "
        "The pre-registered refutation criterion (source-weighted mean "
        "R2<=0.0 OR majority of eligible sources R2<=0) is met on "
        "criterion (b) alone, unambiguously (73.5% >> the 50% bar). This "
        "refutes the SAFE READING of the promoted family-safe KPI (and "
        "its family-LOFO- and feature-integrity-survived nuances) as "
        "evidence the QSPR model has learned a transferable structure-"
        "composition-environment -> corrosion-rate relationship: for "
        "roughly three-quarters of the independent literature sources "
        "that make up NIST CORR-DATA, what the model has actually learned "
        "does not transfer to a novel source's own testing methodology "
        "and reporting convention, even though it reliably beats the "
        "global-mean baseline on a per-row sample-weighted basis (the "
        "same 'dominated by the largest groups' pattern the family-LOFO "
        "attack already exposed at the family level, now confirmed one "
        "level deeper at the provenance level). Scope ceiling is "
        "otherwise unchanged: this is bare-metal/alloy substrate "
        "corrosion (NIST CORR-DATA), not organic-coating barrier "
        "performance, and grants no product-performance authority either "
        "way."
    ),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_result_sha256": canon_sha,
        "runA_result_sha256": sha(runA),
        "runB_result_sha256": sha(runB),
        "byte_identical": canon == runA == runB,
        "harness_sha256": harness_sha,
        "positive_control_harness_sha256": pc_harness_sha,
        "positive_control_note": (
            "Refutations do not require a positive control (the campaign "
            "protocol requires positive controls only to license a "
            "CLAIM_SURVIVED verdict); this attack's own harness-computed "
            "verdict is CLAIM_REFUTED. corr_rate_source_lofo_positive_"
            "control.py (hostile-null full label-shuffle) exists in this "
            "directory alongside the harness for use if a future repair "
            "fire re-attacks a repaired version of this claim and needs "
            "to license a survival."
        ),
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
ptype = "application/vnd.amphora.barrier-corrosion-source-lofo+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "corr-rate-source-lofo-receipt.v1.dsse.json"
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
