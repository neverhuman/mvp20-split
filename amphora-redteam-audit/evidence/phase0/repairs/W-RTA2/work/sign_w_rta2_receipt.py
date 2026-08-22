#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit W-RTA2 survival-bar
gameability audit (CAMPAIGN item W-RTA2). AUDIT_ONLY: signs the audit
receipt under evidence/phase0/repairs/W-RTA2/done/. Real empirical test of
lib/remote_verify.py (copied read-only, unmodified) against a signed
demonstration attack constructed in work/gamed_attack/. Uses the pinned
PHASE0_EVALUATOR key.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/W-RTA2/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/W-RTA2/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
FIRE_ID = "20260805T120001-2000833-f054d4a9684d"


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
assert byte_identical, "two-replay bytes differ -- NOT stable, do not sign"
diag = json.loads(runA_bytes)
canon_sha = sha(runA_bytes)

harness_sha = sha((WORK / "run_w_rta2_audit.py").read_bytes())
gamed_harness_sha = sha((WORK / "gamed_attack/run_gamed_attack.py").read_bytes())
gamed_receipt_sha = sha((WORK / "gamed_attack/gamed-attack-receipt.v1.dsse.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

verdict = diag["verdict"]

body_obj = {
    "schema": "amphora.redteam-audit.w-rta2-survival-bar-gameability-receipt.v1",
    "receipt_id": "w-rta2-survival-bar-gameability-audit-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "W-RTA2",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_other_module_files": False,
    "claim_under_attack": diag["claim_under_attack"],
    "method": diag["method"],
    "gamed_attack": diag["gamed_attack"],
    "empirical_mechanical_check_results": diag["empirical_mechanical_check_results"],
    "verdict": verdict,
    "verdict_target": diag["verdict_target"],
    "bar_is_mechanically_enforced": diag["bar_is_mechanically_enforced"],
    "verdict_reasoning": diag["verdict_reasoning"],
    "proposed_mechanical_fix": diag["proposed_mechanical_fix"],
    "does_not_close": diag["does_not_close"],
    "interpretation": (
        "CLAIM_REFUTED against the prompt's own claim that the survival "
        "bar is enforceable rather than merely aspirational. A well-formed "
        "FALSIFICATION_ATTACK receipt was built against a real, robust, "
        "in-scope claim (DGEBA oligomer EEW linear series), with a "
        "refutation criterion chosen so it is algebraically incapable of "
        "firing (predicted EEW cannot go negative/NaN/infinite for any "
        "n>=0 under an affine model with two strictly positive "
        "coefficients), signed with the real pinned evaluator key exactly "
        "as a genuine receipt would be. The launcher's actual, unmodified "
        "verification code was then run against it for real: "
        "mode=donecheck (which decides campaign_item_status='done') "
        "returned pass=true; mode=verify (which decides whether a fire's "
        "artifacts are credited) returned check='OK', "
        "verified_new_signed=1, signing_violations_in_module=0, "
        "ledger_has_fire_id=true, with the gamed path in 'credited' and "
        "not in 'rejected'. Neither mode inspects the semantic content of "
        "attack_description, refutation_criterion, or verdict_reasoning. "
        "The bar is therefore enforced entirely by prose, trusting the "
        "agent's self-report and the hope a later audit fire reads the "
        "payload critically -- not by anything lib/remote_verify.py "
        "checks. A concrete mechanical fix is proposed: require a "
        "mutation-testing-style positive_control on every CLAIM_SURVIVED "
        "FALSIFICATION_ATTACK receipt, mechanically re-executed by the "
        "verifier against a corrupted mutant of the target claim, so a "
        "criterion that cannot kill any mutant is rejected by code "
        "execution rather than trusted by prose."
    ),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "canonical_diagnostic_sha256": canon_sha,
        "runA_diagnostic_sha256": sha(runA_bytes),
        "runB_diagnostic_sha256": sha(runB_bytes),
        "byte_identical": byte_identical,
        "harness_sha256": harness_sha,
        "harness_path": "amphora-redteam-audit/evidence/phase0/repairs/W-RTA2/work/run_w_rta2_audit.py",
        "gamed_attack_harness_sha256": gamed_harness_sha,
        "gamed_attack_harness_path": "amphora-redteam-audit/evidence/phase0/repairs/W-RTA2/work/gamed_attack/run_gamed_attack.py",
        "gamed_attack_receipt_sha256": gamed_receipt_sha,
        "gamed_attack_receipt_path": "amphora-redteam-audit/evidence/phase0/repairs/W-RTA2/work/gamed_attack/gamed-attack-receipt.v1.dsse.json",
        "remote_verify_script_used": "lib/remote_verify.py copied read-only and unmodified from xbabe1 to /tmp on xbabe2 for this test run; not part of this receipt's artifact set",
        "determinism": diag["determinism"]["note"],
    },
    "toolchain": {"python": "3", "note": "stdlib json/hashlib/base64/glob/os/subprocess + cryptography.hazmat Ed25519"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/repairs/W-RTA2/done/",
        "signs_phase0_evaluation_or_review": False,
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit-w-rta2-survival-bar-gameability-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "w-rta2-survival-bar-gameability-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", verdict)
print("bar_is_mechanically_enforced", diag["bar_is_mechanically_enforced"])
print("evaluator_key_id", eval_key_id)
print("two_replay_sha256", canon_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
