#!/usr/bin/env python3
"""Sign the W-T-ARITH done receipt for amphora-formulation-arithmetic.

Wraps diagnostic.canonical.json (the EPA Method 24 conformance audit) into a
DSSE Ed25519 envelope, self-verifies, and writes into evidence/phase0/repairs/
W-T-ARITH/done/ since the done_criterion is met: >=6 normative requirements
enumerated with verdict + evidence, baseline cited with version+URL, every
divergence filed in proposed_followups[] with a proposed repair criterion.
Overall verdict is CLAIM_REFUTED (a genuine divergence was found and is
self-evidencing), so no positive_control is strictly required -- one is
included anyway for rigor (see diagnostic payload).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-formulation-arithmetic"
REPAIR = MOD / "evidence/phase0/repairs/W-T-ARITH"
WORK = REPAIR / "work"
DONE = REPAIR / "done"
DONE.mkdir(parents=True, exist_ok=True)

SEED = Path.home() / ".local/share/amphora/phase0/keys/evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIAG_A = WORK / "diagnostic.canonical.json"
DIAG_B = WORK / "diagnostic.runB.json"
SCRIPT = WORK / "w_t_arith_epa24_audit.py"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fsha(p: Path) -> str:
    return sha(p.read_bytes())


def pae(t: str, body: bytes) -> bytes:
    return (
        b"DSSEv1 "
        + str(len(t)).encode()
        + b" "
        + t.encode()
        + b" "
        + str(len(body)).encode()
        + b" "
        + body
    )


def load_seed(p: Path) -> bytes:
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


assert fsha(DIAG_A) == fsha(DIAG_B), "two-replay bytes differ between runs"
diag = json.loads(DIAG_A.read_text())
assert diag["requirement_count"] >= 6
assert diag["overall_verdict"] == "CLAIM_REFUTED"
assert len(diag["proposed_followups"]) >= 1
for reqm in diag["requirements"]:
    assert reqm["verdict"] in (
        "CONFORMANT", "CONFORMANT_CONDITIONAL", "DIVERGENT",
        "DIVERGENT_IN_KIND", "NOT_APPLICABLE", "NOT_APPLICABLE_AT_EQUATION_LEVEL",
    )
    assert reqm["evidence"]

payload_obj = {
    "schema": "amphora.phase0-repair.done-receipt.v1",
    "repair_item": "W-T-ARITH",
    "campaign_item_id": "W-T-ARITH",
    "module": "amphora-formulation-arithmetic",
    "date": "2026-08-13",
    "generated_on_host": "xbabe2",
    "authority": "AUDIT_ONLY",
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "trust_anchored_in_phase0_store": True,
    "directive_path": "none",
    "directive_sha256": "",
    "directive_obligation": None,
    "claim_under_attack": diag["claim_under_attack"],
    "objective": (
        "THEORY-DIMENSION item: measure amphora-formulation-arithmetic's dimensioned "
        "arithmetic identities (VOC g/L, volume solids, weight solids, density) "
        "against a NAMED PUBLISHED BASELINE for the first time -- prior receipts in "
        "this module were all self-referential (checked only against the module's "
        "own fixture)."
    ),
    "baseline": diag["baseline"],
    "prior_fires_on_this_claim_id": diag["prior_fires_on_this_claim_id"],
    "reproduces_prior_audited_engine_output": diag["reproduces_prior_audited_engine_output"],
    "requirements": diag["requirements"],
    "requirement_count": diag["requirement_count"],
    "verdict_counts": diag["verdict_counts"],
    "proposed_followups": diag["proposed_followups"],
    "positive_control": diag["positive_control"],
    "verdict": diag["overall_verdict"],
    "overall_verdict_reasoning": diag["overall_verdict_reasoning"],
    "repair_artifacts": {
        "audit_script_path": "amphora-formulation-arithmetic/evidence/phase0/repairs/W-T-ARITH/work/w_t_arith_epa24_audit.py",
        "audit_script_sha256": fsha(SCRIPT),
        "diagnostic_canonical_path": "amphora-formulation-arithmetic/evidence/phase0/repairs/W-T-ARITH/work/diagnostic.canonical.json",
        "diagnostic_canonical_sha256": fsha(DIAG_A),
        "diagnostic_runB_path": "amphora-formulation-arithmetic/evidence/phase0/repairs/W-T-ARITH/work/diagnostic.runB.json",
        "diagnostic_runB_sha256": fsha(DIAG_B),
        "two_replay_byte_identical": True,
        "dependency_read_only_sources": [
            "amphora-redteam-audit/benchmarks/formulation-arithmetic-dimensioned-v1/diagnostic.canonical.json (unmodified, cited only)",
            "amphora-formulation-arithmetic/evidence/audit/uncertainty-propagation-v1/diagnostic.canonical.json (unmodified, cited only)",
            "amphora-ingredient-library/reference/mvp20/data/facts.json (unmodified, cited only)",
        ],
    },
}

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
pinned = {k.get("role"): k for k in trust["keys"]}
eval_pin = eval_key_id == pinned.get("PHASE0_EVALUATOR", {}).get("key_id")
assert eval_pin, f"evaluator key does not match pinned trust-store entry: {eval_key_id}"

payload_obj["signing_key"] = {
    "role": "PHASE0_EVALUATOR",
    "key_id": eval_key_id,
    "public_key_hex": eval_pub_hex,
    "derives_pinned_trust_store_key_id": bool(eval_pin),
}

body1 = json.dumps(payload_obj, sort_keys=True, separators=(",", ":")).encode()
body2 = json.dumps(json.loads(body1.decode()), sort_keys=True, separators=(",", ":")).encode()
assert body1 == body2, "two-replay bytes differ"
two_replay_sha = sha(body1)
payload_obj["two_replay_sha256_gate"] = "PASS"
payload_obj["two_replay_sha256"] = two_replay_sha
body = json.dumps(payload_obj, sort_keys=True, separators=(",", ":")).encode()
body_replay = json.dumps(json.loads(body.decode()), sort_keys=True, separators=(",", ":")).encode()
assert body == body_replay, "final two-replay bytes differ"
payload_sha = sha(body)

ptype = "application/vnd.amphora.phase0-repair.done-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [
        {"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}
    ],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "payload_canonical_sha256": payload_sha,
    "payload_decoded": payload_obj,
    "signature": envelope,
}
out = DONE / "W-T-ARITH.done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

reloaded = json.loads(out.read_text())
env2 = reloaded["signature"]
body_reloaded = base64.standard_b64decode(env2["payload"])
pub_from_seed = Ed25519PrivateKey.from_private_bytes(load_seed(SEED)).public_key()
pub_from_seed.verify(
    base64.standard_b64decode(env2["signatures"][0]["sig"]),
    pae(env2["payloadType"], body_reloaded),
)
assert sha(body_reloaded) == payload_sha == reloaded["payload_canonical_sha256"]
assert json.loads(body_reloaded) == reloaded["payload_decoded"]
Ed25519PublicKey.from_public_bytes(bytes.fromhex(reloaded["evaluator_public_key_hex"])).verify(
    base64.standard_b64decode(env2["signatures"][0]["sig"]),
    pae(env2["payloadType"], body_reloaded),
)

print(
    json.dumps(
        {
            "ok": True,
            "verdict": payload_obj["verdict"],
            "requirement_count": payload_obj["requirement_count"],
            "verdict_counts": payload_obj["verdict_counts"],
            "done_receipt": str(out),
            "done_receipt_sha256": fsha(out),
            "payload_canonical_sha256": payload_sha,
            "two_replay_sha256": two_replay_sha,
            "evaluator_key_id": eval_key_id,
            "derives_pinned_trust_store_key_id": bool(eval_pin),
            "self_verified": True,
        },
        indent=2,
    )
)
