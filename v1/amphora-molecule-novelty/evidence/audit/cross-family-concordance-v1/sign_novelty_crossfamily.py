#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-novelty CROSS-DESCRIPTOR-FAMILY
concordance AUDIT_ONLY receipt. AUDIT_ONLY: signs under evidence/audit/; does
NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED), does NOT modify the manifest
(66 receipts / 11 modules), any locked dataset, or the signed Phase-0 novelty
KPI. Derived key_id cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT=Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH=ROOT/"amphora-molecule-novelty/evidence/audit/cross-family-concordance-v1"
SEED_DIR=Path.home()/".local/share/amphora/phase0/keys"
EVAL_SEED=SEED_DIR/"evaluator.ed25519.seed"
REVIEWER_SEED=SEED_DIR/"internal-reviewer.ed25519.seed"
TRUST=ROOT/"config/phase0-trust-store.v1.json"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t,body): return (b"DSSEv1 "+str(len(t)).encode()+b" "+t.encode()+b" "+str(len(body)).encode()+b" "+body)
def load_seed(p):
    raw=p.read_bytes().strip()
    if len(raw)==64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]

canon=(BENCH/"diagnostic.canonical.json").read_bytes()
runB=(BENCH/"diagnostic.runB.json").read_bytes()
assert canon==runB,"two-replay bytes differ"
diag_sha=sha(canon)
diag=json.loads(canon)
harness_sha=sha((BENCH/"run_novelty_crossfamily.py").read_bytes())

eval_sk=Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub=eval_sk.public_key().public_bytes_raw(); eval_pub_hex=eval_pub.hex()
eval_key_id=f"phase0-evaluator-{sha(eval_pub)}"
rev_sk=Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex=rev_sk.public_key().public_bytes_raw().hex()
rev_key_id=f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
eval_pin=rev_pin=False
if TRUST.exists():
    trust=json.loads(TRUST.read_text())
    tbr={k.get("role"):k for k in trust.get("keys",[])}
    eval_pin=(eval_key_id==tbr.get("PHASE0_EVALUATOR",{}).get("key_id"))
    rev_pin=(rev_key_id==tbr.get("PHASE0_INTERNAL_REVIEWER",{}).get("key_id"))

hyp=diag["hypothesis_evaluation"]; rob=diag["cross_family_robustness"]
kw=diag["kendall_w"]; fc=diag["fail_closed"]
body_obj={
 "schema":"amphora.molecule-novelty.cross-descriptor-family-concordance-receipt.v1",
 "study_id":diag["study_id"],
 "authority":"AUDIT_ONLY","run_type":"NOVELTY_CROSS_DESCRIPTOR_FAMILY_CONCORDANCE_AUDIT",
 "module":"amphora-molecule-novelty",
 "promotes_authority":False,"flips_scientific_readiness":False,
 "human_review_performed":False,"organizational_independence_asserted":False,
 "modifies_manifest":False,"modifies_locked_dataset":False,"modifies_signed_phase0_kpi":False,
 "claim":diag["headline"],"purpose":diag["purpose"],"non_circularity":diag["non_circularity"],
 "theory_reference":diag["theory_reference"],"rdkit_version":diag["rdkit_version"],
 "method":diag["method"],"families":diag["families"],"family_reference":diag["family_reference"],
 "alphas":diag["alphas"],"corpus":diag["corpus"],"candidates":diag["candidates"],
 "results":{
   "anchor_reproduces_signed_nn_exact":diag["anchor"]["morgan_r2_reproduces_signed_nn_exact"],
   "kendall_w":kw["W"],
   "n_unanimous_novel_of_5_a05":rob["n_unanimous_novel_a05"],
   "unanimous_novel_candidates_a05":rob["unanimous_novel_candidates_a05"],
   "family_dependent_candidates_a05":rob["family_dependent_candidates_a05"],
   "decoy_family_blind_spots_a05":rob["decoy_family_blind_spots_a05"],
   "all_fragments_nonnovel_in_all_families_a05":
     diag["discrimination_controls"]["all_fragments_nonnovel_in_all_families_a05"],
   "exact_duplicate_all_self_match":fc["exact_corpus_duplicate"]["all_self_match_1.0"],
   "bad_smiles_rejected":fc["bad_smiles_rejected"],
   "self_tests_all_pass":diag["self_tests_all_pass"],
   "hypothesis_verdict":hyp["verdict"]},
 "cross_family_robustness":rob,"kendall_w":kw,
 "per_family_candidate_eval":diag["per_family_candidate_eval"],
 "cross_family":diag["cross_family"],
 "positive_controls_decoys":diag["positive_controls_decoys"],
 "discrimination_controls":diag["discrimination_controls"],
 "fail_closed":fc,"self_tests":diag["self_tests"],
 "hypothesis_evaluation":hyp,
 "rights_posture":diag["rights_posture"],"closes":diag["closes"],
 "does_not_close":diag["does_not_close"],
 "reproducibility":{"two_replay_sha256_gate":"PASS","canonical_diagnostic_sha256":diag_sha,
   "runB_diagnostic_sha256":sha(runB),"byte_identical":canon==runB,"harness_sha256":harness_sha},
 "signing_key":{"role":"PHASE0_EVALUATOR","key_id":eval_key_id,"public_key_hex":eval_pub_hex,
   "used_for":"AUDIT_ONLY audit receipt under evidence/audit/","signs_phase0_evaluation_or_review":False,
   "derives_pinned_trust_store_key_id":bool(eval_pin)},
 "reviewer_reference":{"role":"PHASE0_INTERNAL_REVIEWER","key_id":rev_key_id,"public_key_hex":rev_pub_hex,
   "derives_pinned_trust_store_key_id":bool(rev_pin),"reviewer_signature_present":False,
   "note":"Reviewer key referenced for provenance only; no independent human review performed."},
}
body=json.dumps(body_obj,indent=2,sort_keys=True).encode()
ptype="application/vnd.amphora.molecule-novelty-cross-descriptor-family-concordance+json"
sig=eval_sk.sign(pae(ptype,body))
envelope={"payload":base64.standard_b64encode(body).decode(),"payloadType":ptype,
 "signatures":[{"keyid":eval_key_id,"sig":base64.standard_b64encode(sig).decode()}]}
receipt={"evaluator_key_id":eval_key_id,"evaluator_public_key_hex":eval_pub_hex,
 "reviewer_public_key_hex":rev_pub_hex,"signature":envelope}
out=BENCH/"cross-family-concordance-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt,indent=2,sort_keys=True))
pk=Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype,base64.standard_b64decode(envelope["payload"])))
print("WROTE",out)
print("evaluator_key_id",eval_key_id)
print("eval_derives_pinned_trust_key",eval_pin)
print("reviewer_derives_pinned_trust_key",rev_pin)
print("two_replay_sha256",diag_sha)
print("envelope_sha256",sha(out.read_bytes()))
print("signature_len",len(envelope["signatures"][0]["sig"]))
print("signature_verified",True)
