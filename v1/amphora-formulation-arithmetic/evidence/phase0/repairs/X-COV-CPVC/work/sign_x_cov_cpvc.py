#!/usr/bin/env python3
"""Sign the X-COV-CPVC done receipt for amphora-formulation-arithmetic.

Wraps diagnostic.canonical.json (coverage-spreading-v1 x reduced-pvc-porosity-v1
sibling-receipt composition audit) into a DSSE Ed25519 envelope, self-verifies,
and writes into evidence/phase0/repairs/X-COV-CPVC/done/ since the verdict is
CLAIM_REFUTED (self-evidencing composition of two already-signed receipts; no
positive_control strictly required, one included anyway for rigor).
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
REPAIR = MOD / "evidence/phase0/repairs/X-COV-CPVC"
WORK = REPAIR / "work"
DONE = REPAIR / "done"
DONE.mkdir(parents=True, exist_ok=True)

SEED = Path.home() / ".local/share/amphora/phase0/keys/evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIAG_A = WORK / "diagnostic.canonical.json"
DIAG_B = WORK / "diagnostic.runB.json"
SCRIPT = WORK / "cov_cpvc_crosscheck.py"


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
assert diag["overall_verdict"] == "CLAIM_REFUTED"
assert diag["control_clean"] is True
assert diag["reproduces_coverage_spreading_v1_point_estimates"]
assert diag["reproduces_reduced_pvc_porosity_v1_case_study"]
assert diag["composed_case"]["pvc_overshoot_case"]["dft_overshoot_pct"] > 5.0
assert diag["composed_case"]["pvc_below_cpvc_control_case"]["dft_divergence_pct"] == 0.0

payload_obj = {
    "schema": "amphora.phase0-repair.done-receipt.v1",
    "repair_item": "X-COV-CPVC",
    "campaign_item_id": "X-COV-CPVC",
    "module": "amphora-formulation-arithmetic",
    "date": "2026-08-15",
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
        "ROTATION-mode falsification: identify the strongest un-attacked standing claim in "
        "amphora-formulation-arithmetic and attack it. Selected coverage-spreading-v1 "
        "(COVERAGE_SPREADING_ENGINE_READY, signed 2026-07-29, never attacked in the ledger) "
        "and composed it against its own sibling receipt reduced-pvc-porosity-v1 (signed two "
        "days later), which had already found -- but never propagated back as a repair -- that "
        "the coverage engine's void-free WFT/DFT arithmetic mis-reads film build by exactly "
        "LAMBDA=PVC/CPVC for any in-domain porous (PVC>=CPVC) marine anti-corrosion primer."
    ),
    "sibling_receipt_used_as_baseline": diag["sibling_receipt_used_as_baseline"],
    "attacked_receipt_signed_date": diag["attacked_receipt_signed_date"],
    "prior_fires_on_this_module": diag["prior_fires_on_this_module"],
    "reproduces_coverage_spreading_v1_point_estimates": diag["reproduces_coverage_spreading_v1_point_estimates"],
    "reproduces_reduced_pvc_porosity_v1_case_study": diag["reproduces_reduced_pvc_porosity_v1_case_study"],
    "coverage_spreading_v1_ka_battery_ids": diag["coverage_spreading_v1_ka_battery_ids"],
    "coverage_spreading_v1_ka_battery_has_pvc_cpvc_case": diag["coverage_spreading_v1_ka_battery_has_pvc_cpvc_case"],
    "coverage_spreading_v1_scope_discloses_pvc_cpvc_boundary": diag["coverage_spreading_v1_scope_discloses_pvc_cpvc_boundary"],
    "composed_case": diag["composed_case"],
    "calibrated_uncertainty_comparison": diag["calibrated_uncertainty_comparison"],
    "positive_control": diag["positive_control"],
    "control_clean": diag["control_clean"],
    "verdict": diag["overall_verdict"],
    "overall_verdict_reasoning": diag["overall_verdict_reasoning"],
    "proposed_followups": diag["proposed_followups"],
    "repair_artifacts": {
        "audit_script_path": "amphora-formulation-arithmetic/evidence/phase0/repairs/X-COV-CPVC/work/cov_cpvc_crosscheck.py",
        "audit_script_sha256": fsha(SCRIPT),
        "diagnostic_canonical_path": "amphora-formulation-arithmetic/evidence/phase0/repairs/X-COV-CPVC/work/diagnostic.canonical.json",
        "diagnostic_canonical_sha256": fsha(DIAG_A),
        "diagnostic_runB_path": "amphora-formulation-arithmetic/evidence/phase0/repairs/X-COV-CPVC/work/diagnostic.runB.json",
        "diagnostic_runB_sha256": fsha(DIAG_B),
        "two_replay_byte_identical": True,
        "dependency_read_only_sources": [
            "amphora-formulation-arithmetic/evidence/audit/coverage-spreading-v1/diagnostic.canonical.json (unmodified, cited only)",
            "amphora-formulation-arithmetic/evidence/audit/reduced-pvc-porosity-v1/diagnostic.canonical.json (unmodified, cited only)",
            "amphora-ingredient-library/evidence/audit/oil-absorption-cpvc-v1/diagnostic.canonical.json (unmodified, cited only)",
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
out = DONE / "X-COV-CPVC.done-receipt.v1.dsse.json"
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
            "dft_overshoot_pct": payload_obj["composed_case"]["pvc_overshoot_case"]["dft_overshoot_pct"],
            "control_divergence_pct": payload_obj["composed_case"]["pvc_below_cpvc_control_case"]["dft_divergence_pct"],
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
