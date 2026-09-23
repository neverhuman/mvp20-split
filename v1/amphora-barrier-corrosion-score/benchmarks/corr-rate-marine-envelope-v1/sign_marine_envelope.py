#!/usr/bin/env python3
"""DSSE-Ed25519-sign the corr-rate-marine-envelope-v1 AUDIT_ONLY falsification
receipt for amphora-barrier-corrosion-score. AUDIT_ONLY: signs an audit
receipt under the module's benchmarks/ dir; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED / PRE_PHASE_0), does NOT modify the
portfolio manifest, any locked dataset, or any signed Phase-0 KPI (this
receipt attacks corr-rate-family-safe-qspr-kpi.v1.dsse.json's implicit
domain-generalization reading but does not edit that KPI file -- a
refutation of the SAFE READING adds nuance via the retraction index, it
does not delete or rewrite the prior receipt)."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-barrier-corrosion-score/benchmarks/corr-rate-marine-envelope-v1"
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
harness_sha = sha((BENCH / "corr_rate_marine_envelope.py").read_bytes())

assert res["verdict"] == "CLAIM_REFUTED"

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
    "schema": "amphora.barrier-corrosion-score.corr-rate-marine-envelope-receipt.v1",
    "module": "amphora-barrier-corrosion-score",
    "benchmark": "corr-rate-marine-envelope-v1",
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
        "family, 5-fold) HistGBM R2=0.132087), which had already survived "
        "two prior attacks that varied only the CV grouping axis (raw "
        "material string, then metallurgical family, then true "
        "leave-one-family-out, corr-rate-family-lofo-v1, family-weighted "
        "mean R2=0.015964). This attack escalates to a new, previously "
        "untested axis: the ENVIRONMENT domain the module actually exists "
        "to serve. docs/mission.md states the module's applicability "
        "domain is 'solvent-borne two-component epoxy-amine marine-coating "
        "R&D', yet no prior receipt ever held out true seawater/marine-"
        "immersion rows as a domain-shift test."),
    "attacks_claim": res["attacks_claim"],
    "attack_description": res["attack_description"],
    "refutation_criterion": res["refutation_criterion"],
    "dataset": res["dataset"],
    "cohort": res["cohort"],
    "results": res["results"],
    "data_integrity_finding_marine_atmospheric_conflation": res["data_integrity_finding_marine_atmospheric_conflation"],
    "verdict": res["verdict"],
    "scope_honesty": res["scope_honesty"],
    "honest_interpretation": (
        "Training the identical HistGBM QSPR (same feature engineering, "
        "hyperparameters, seed=0) on all 7,096 non-marine classified rows "
        "and evaluating on all 186 true seawater/marine-immersion rows "
        "(8 of 17 metallurgical families, all also present in training) "
        "gives R2=-0.450740 -- the model is WORSE than predicting the "
        "marine test-set mean. This holds even under a patched feature "
        "set that removes a co-discovered data-integrity defect (the "
        "deployed env_features() marine flag conflates atmospheric "
        "exposure with seawater immersion: 313 of 499 rows with "
        "marine_feature==1 in the classified cohort, 62.7%, are actually "
        "atmospheric-exposure rows, not seawater; patched R2=-0.358497, "
        "still deeply negative). 6 of 8 marine families score R2<=0 "
        "individually, two catastrophically (carbon_steel_cast_iron "
        "R2=-16.03, n=38; lead R2=-5.15, n=18). Even the naive family-mean "
        "baseline computed from non-marine training data has negative R2 "
        "(-0.637) on the marine test set, confirming the marine "
        "corrosion-rate distribution genuinely differs from the "
        "non-marine training distribution this model was built on -- this "
        "is a real domain shift, not a modeling artifact. The pre-"
        "registered refutation criterion (marine-envelope R2<=0.0 OR "
        "error-reduction-vs-best-baseline<=0.0) is met on criterion (a) "
        "alone. This refutes the SAFE READING of the promoted family-safe "
        "KPI and its LOFO-survived nuance as supporting this module's own "
        "declared marine applicability domain: the QSPR model, as "
        "currently trained, has never demonstrated -- and here "
        "demonstrably fails -- to generalize to genuine seawater/marine-"
        "immersion corrosion, which is the entire reason "
        "amphora-barrier-corrosion-score exists. Scope ceiling is "
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
ptype = "application/vnd.amphora.barrier-corrosion-marine-envelope+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "corr-rate-marine-envelope-receipt.v1.dsse.json"
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
