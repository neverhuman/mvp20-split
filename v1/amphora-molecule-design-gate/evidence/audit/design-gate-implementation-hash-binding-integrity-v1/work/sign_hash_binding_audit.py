#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-design-gate implementation
source-hash binding integrity audit.

AUDIT_ONLY. Produces a signed audit receipt under
evidence/audit/design-gate-implementation-hash-binding-integrity-v1/. Does
NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
flip scientific_readiness, does NOT modify the manifest, mission.md,
capability-profile.json, or any prior signed receipt.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-molecule-design-gate/evidence/audit/design-gate-implementation-hash-binding-integrity-v1"
WORK = ITEM / "work"
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


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((WORK / "run_hash_binding_audit.py").read_bytes())

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
    "schema": "amphora.molecule-design-gate.implementation-hash-binding-integrity-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "DATA_INTEGRITY_AUDIT",
    "module": "amphora-molecule-design-gate",
    "campaign_item_id": "",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_mission_or_capability_profile": False,
    "supersedes": None,
    "target_claim": diag["target_claim"],
    "refutation_criterion": diag["refutation_criterion"],
    "verdict": diag["verdict"],
    "headline": (
        "amphora-molecule-design-gate/docs/mission.md and docs/capability-"
        "profile.json both cite SHA-256 "
        "5968f518f199cf697d153018afdfee887e9b3ec0bee8a9c00dcc3c5a854ec861 as "
        "the 'live checked implementation' hash for amphora-molecule-"
        "capabilities/src/lib.rs. The actual current git-committed content of "
        "that file (working tree == HEAD blob == the very baseline commit "
        "907e753 that added mission.md/capability-profile.json/lib.rs "
        "together) hashes to "
        "258043a42c015587600da417a50170928b57f4f2eb2a0bfcee9b0ac14ada750c -- "
        "a full mismatch, not a formatting artifact (both are well-formed "
        "64-hex-char SHA-256 strings). This means the pinned hash has been "
        "wrong since at least the baseline snapshot commit, not that it just "
        "now drifted -- there was never a moment design-gate's own docs "
        "correctly bound the implementation they claim authority over. "
        "Independently cross-validated: an unrelated amphora-candidate-"
        "contract audit (eight-vector-facts-injection-v1) AND amphora-"
        "molecule-generator's own signed 2026-08-16 hash-binding-integrity "
        "receipt both recorded the SAME actual hash for the SAME file path "
        "from independent runs. capability-profile.json's own "
        "automatic_demotion list names 'source hash mutation' as a trigger, "
        "i.e. this module relies on exactly this binding for its own "
        "integrity story, and the binding does not verify. The identical "
        "stale hash is also cited by 4 other modules (generator, novelty, "
        "role-ranker, property) for the same shared file -- reported as "
        "context, not fixed here (out of this module's own-docs scope)."
    ),
    "measurements": diag["measurements"],
    "findings": diag["findings"],
    "context_other_modules_citing_identical_stale_hash_for_same_shared_file": (
        diag["context_other_modules_citing_identical_stale_hash_for_same_shared_file"]
    ),
    "does_not_close": diag["does_not_close"],
    "rights_posture": "No new data acquired; audits only already-committed, in-tree files and already-existing signed diagnostics from other modules. Manifest untouched.",
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "harness_command": "python3 run_hash_binding_audit.py > diagnostic.canonical.json",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/design-gate-implementation-hash-binding-integrity-v1/",
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
    "theory_reference": (
        "Basic hash-provenance / content-addressing integrity (SHA-256, "
        "FIPS 180-4); this module's own docs/capability-profile.json "
        "automatic_demotion criterion 'source hash mutation' (in-tree, "
        "self-declared)."
    ),
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-design-gate-implementation-hash-binding-integrity+json"
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

ITEM.mkdir(parents=True, exist_ok=True)
out = ITEM / "design-gate-implementation-hash-binding-integrity-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
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
print("verdict", body_obj["verdict"])
