#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-generator scaffold-diversity
homolog-fingerprint-saturation falsification-attack AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED), does NOT modify the manifest,
any locked dataset, or the attacked molgen-scaffold-diversity-v1 receipt
(untouched, independent companion finding). The derived key_id is
cross-checked against the pinned trust store as an integrity assertion only.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-generator/evidence/audit/molgen-scaffold-diversity-homolog-fingerprint-saturation-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(path):
    raw = path.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_molgen_homolog_fingerprint_saturation.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_derives_pin = (rev_key_id == trust_by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": diag["schema"],
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-molecule-generator",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_attacked_receipt": False,
    "claim": (
        "amphora-molecule-generator/evidence/audit/molgen-scaffold-diversity-v1's "
        "hypothesis_evaluation verdict CORROBORATED_IN_AUDIT_INSTRUMENT ('accepted "
        "proposals span a diverse region of chemical space, not trivially inflated "
        "variants of a single scaffold', headline IntDiv_1=0.7681) is an aggregate "
        "artifact: F1_polyethyleneamine (n=8, 21.1% of the 38 accepted proposals) and "
        "F2_alpha_omega_diamine (n=10, 26.3%) are linear chain-length homologous "
        "series whose internal IntDiv_1 under the SAME Morgan/ECFP-r2/2048-Tanimoto "
        "instrument collapses to 0.1851 and 0.0870 respectively (mean pairwise "
        "Tanimoto 0.8149 and 0.9130), with 6/7 and 7/9 chain-length-adjacent neighbor "
        "pairs fingerprint-saturated at Tanimoto>=0.99 (TETA/TEPA/PEHA/k6/k7/k8 are "
        "pairwise indistinguishable at ECFP-r2/2048 resolution). Both families "
        "independently violate the a-priori family-resolution decision rule "
        "(IntDiv_1<=0.25 and >=50% adjacent saturation for any family >=15% of the "
        "set). The headline aggregate is driven entirely by cross-family contrast "
        "(homolog-bloc-vs-ring mean Tanimoto=0.1054); at family resolution 47.4% of "
        "the accepted set IS the trivially-inflated-variant pattern the hypothesis "
        "claims to rule out."
    ),
    "purpose": diag["purpose"],
    "attacked_claim": diag["attacked_claim"],
    "attacked_receipt_sha256": diag["attacked_receipt_sha256"],
    "source_diagnostic_sha256": diag["source_diagnostic_sha256"],
    "theory_reference": diag["theory_reference"],
    "falsification_criterion": diag["falsification_criterion"],
    "fingerprint": diag["fingerprint"],
    "results": {
        "n_molecules": diag["n_molecules"],
        "overall_intdiv1_recomputed": diag["overall_intdiv1_recomputed"],
        "overall_intdiv1_receipt_reported": diag["overall_intdiv1_receipt_reported"],
        "recomputation_matches_receipt": diag["recomputation_matches_receipt"],
        "per_family_intdiv1": diag["per_family_intdiv1"],
        "homolog_bloc": diag["homolog_bloc"],
        "adjacent_homolog_similarity": diag["adjacent_homolog_similarity"],
        "cross_bloc_homolog_vs_ring_mean_tanimoto": diag["cross_bloc_homolog_vs_ring_mean_tanimoto"],
        "instrument_self_tests": diag["instrument_self_tests"],
        "per_family_decision_rule_evaluation": diag["per_family_decision_rule_evaluation"],
        "verdict": diag["verdict"],
    },
    "hypothesis_evaluation": diag["hypothesis_evaluation"],
    "non_circularity": diag["non_circularity"],
    "rights_posture": diag["rights_posture"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
    },
    "does_not_close": diag["does_not_close"],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_derives_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-generator-molgen-scaffold-diversity-homolog-fingerprint-saturation+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}
out = BENCH / "molgen-scaffold-diversity-homolog-fingerprint-saturation-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("two_replay_sha256", diag_sha)
print("signature_verified", True)
print("verdict", diag["verdict"])
