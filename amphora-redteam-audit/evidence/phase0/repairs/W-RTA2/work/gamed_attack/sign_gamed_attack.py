#!/usr/bin/env python3
"""W-RTA2 DEMONSTRATION artifact -- signs the GAMED attack receipt with the
real pinned PHASE0_EVALUATOR key, exactly as a real receipt would be
signed, to prove the key alone cannot distinguish a genuine falsification
attempt from a criterion engineered never to fire. This envelope is
written to work/gamed_attack/ (NOT done/, NOT attempts/) and is never
declared as a real portfolio artifact and never referenced by a real
ledger line -- it exists only so the mechanical verifier can be run
against it for real, empirically, rather than simulated.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/W-RTA2/work/gamed_attack"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


runA_bytes = (WORK / "diagnostic.runA.json").read_bytes()
runB_bytes = (WORK / "diagnostic.runB.json").read_bytes()
byte_identical = runA_bytes == runB_bytes
assert byte_identical, "two-replay bytes differ -- do not sign"
diag = json.loads(runA_bytes)

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

# This body_obj is DELIBERATELY styled to look exactly like a real,
# well-formed FALSIFICATION_ATTACK receipt -- that is the point of the
# demonstration: nothing about its shape distinguishes it from a receipt
# with real information value.
body_obj = {
    "schema": "amphora.redteam-audit.w-rta2-gamed-attack-demo-receipt.v1",
    "receipt_id": "w-rta2-gamed-attack-demonstration-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "demonstration_only": True,
    "not_a_real_portfolio_verdict": True,
    "do_not_treat_as_claim_evidence_for": diag["target_claim"]["module"],
    "module": "amphora-redteam-audit",
    "campaign_item_id": "W-RTA2",
    "purpose": (
        "Fixture for W-RTA2: a well-formed attack receipt, signed with "
        "the real pinned PHASE0_EVALUATOR key, whose named refutation "
        "criterion is algebraically incapable of firing. Used to test "
        "empirically (not by argument) whether lib/remote_verify.py's "
        "mechanical checks (mode=donecheck, mode=verify) accept it."
    ),
    "claim_under_attack": diag["target_claim"],
    "attack_label": diag["attack_label"],
    "attack_description": diag["attack_description"],
    "refutation_criterion": (
        "predicted EEW(n) becomes negative, NaN, or infinite for some "
        "n in an extended sweep 0..1e12"
    ),
    "sweep_n_values": diag["sweep_n_values"],
    "rows": diag["rows"],
    "refutation_criterion_fired_on_any_row": diag["refutation_criterion_fired_on_any_row"],
    "verdict": diag["verdict_this_gamed_attack_would_claim"],
    "verdict_reasoning": (
        "Swept n across ten values spanning nine orders of magnitude "
        "beyond the physical domain and the predicted EEW never left "
        "positive, finite range, so the refutation criterion did not "
        "fire; the claim CLAIM_SURVIVED this attack."
    ),
    "why_this_verdict_is_worthless": diag["why_criterion_cannot_fire"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "runA_diagnostic_sha256": sha(runA_bytes),
        "runB_diagnostic_sha256": sha(runB_bytes),
        "byte_identical": True,
        "harness_path": "amphora-redteam-audit/evidence/phase0/repairs/W-RTA2/work/gamed_attack/run_gamed_attack.py",
        "harness_sha256": sha((WORK / "run_gamed_attack.py").read_bytes()),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY demonstration fixture for W-RTA2, signed "
                     "with the real key to test mechanical acceptance -- "
                     "NOT a real claim verdict.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit-w-rta2-gamed-attack-demo+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope,
           "WARNING": "DEMONSTRATION FIXTURE ONLY -- see demonstration_only=true in payload. "
                      "NOT a real falsification verdict against the DGEBA EEW claim. "
                      "Built for campaign item W-RTA2. Do not cite as evidence."}

out = WORK / "gamed-attack-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict_claimed_by_gamed_receipt", body_obj["verdict"])
print("evaluator_key_id", eval_key_id)
print("signature_self_verified", True)
print("envelope_sha256", sha(out.read_bytes()))
