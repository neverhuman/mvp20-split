#!/usr/bin/env python3
"""DSSE-Ed25519-sign the three amphora-solver-lab AUDIT_ONLY demo receipts.

Replicates the portfolio signing conventions of
amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py:
PAE, evaluator seed, payloadType, attestation keys (authority AUDIT_ONLY,
promotes_authority: false), a two-replay byte-stability gate on the demo
diagnostics, trust-store key-id pinning and post-write self-verification
(rebuild PAE, verify, key id must start with phase0-evaluator-3ef6b35).

Signs under amphora-solver-lab/evidence/phase0/demos/; does NOT promote
authority, flip scientific_readiness, or modify the portfolio manifest, any
locked dataset, any Phase-0 KPI, or any benchmark-lock.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-solver-lab"
DEMOS = MOD / "evidence/phase0/demos"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
PINS = MOD / "pins/source_pins.v1.json"
REQUIRED_KEYID_PREFIX = "phase0-evaluator-3ef6b35"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pae(t: str, body: bytes) -> bytes:
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p: Path) -> bytes:
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


DEMO_SPECS = [
    {
        "demo_id": "p1-voc-min-solvent-blend",
        "receipt_basename": "p1-voc-min-solvent-blend-receipt.v1.dsse.json",
        "payload_type": "application/vnd.amphora.solver-lab.demo-p1-voc-min-solvent-blend+json",
        "schema": "amphora.solver-lab.demo-p1-voc-min-solvent-blend-receipt.v1",
        "claim": (
            "P1 VOC-minimizing solvent blend, solved three ways (exhaustive 0.05 "
            "simplex-grid DoE, deterministic projected gradient, seeded NSGA-II) "
            "with cross-method agreement gates, over sha256-pinned "
            "ingredient-library facts only. Constraints: volume solids in "
            "[63,67]%, Hansen RED vs the DGEBA sphere <= 1, minimum flash point "
            ">= 38 C on the blend support, VOC <= 340 g/L. The optimum and the "
            "full VOC-vs-RED Pareto slice are recorded in the embedded "
            "diagnostic; the flash gate excludes 4 of 6 characterized solvents "
            "and the volume-solids upper bound is active at the optimum. "
            "AUDIT_ONLY: real optimization capability, zero granted authority."),
    },
    {
        "demo_id": "p3-hazard-constrained-hardener-selection",
        "receipt_basename": "p3-hazard-constrained-hardener-selection-receipt.v1.dsse.json",
        "payload_type": "application/vnd.amphora.solver-lab.demo-p3-hazard-constrained-hardener-selection+json",
        "schema": "amphora.solver-lab.demo-p3-hazard-constrained-hardener-selection-receipt.v1",
        "claim": (
            "P3 hazard-constrained hardener selection (maximize predicted Tg "
            "s.t. no H317, no H351, AD-Tanimoto >= 0.30, chi_water >= 2.0) over "
            "the sha256-pinned GHS/CLP hazard KPI and coating-candidate "
            "design-card KPI. The feasible set is EMPTY and is reported as such "
            "with named per-candidate blocking constraints (pareto_status "
            "BLOCKED); constraints were not softened to manufacture a winner. "
            "The receipt carries an explicit caveat for the pending R-N01 "
            "CID-attribution correction and a supersession scan that forces "
            "re-derivation once the superseding hazard-card receipt lands. "
            "AUDIT_ONLY: honest infeasibility is the demonstrated capability."),
    },
    {
        "demo_id": "p4-2to4-full-factorial-screen",
        "receipt_basename": "p4-2to4-full-factorial-screen-receipt.v1.dsse.json",
        "payload_type": "application/vnd.amphora.solver-lab.demo-p4-2to4-full-factorial-screen+json",
        "schema": "amphora.solver-lab.demo-p4-2to4-full-factorial-screen-receipt.v1",
        "claim": (
            "P4 2^4 full-factorial DoE screen (resin DGEBA/DGEBF x hardener "
            "IPDA/TETA x solvent toluene/MEK x pigment TiO2/carbon-black, 16 "
            "cells from the CC0-1.0 formulation-universe fixture) with "
            "mass-balance, envelope-gate and GHS constraints applied per cell "
            "from sha256-pinned sources. The solved/infeasible partition and "
            "per-cell reasons are recorded in the embedded diagnostic; missing "
            "envelope policies are treated fail-closed. AUDIT_ONLY: the "
            "partition is audit evidence, not a release decision."),
    },
]


def main() -> None:
    eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
    eval_pub = eval_sk.public_key().public_bytes_raw()
    eval_pub_hex = eval_pub.hex()
    eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

    trust = json.loads(TRUST.read_text())
    pinned = {k.get("role"): k for k in trust["keys"]}
    pinned_eval = pinned.get("PHASE0_EVALUATOR", {}).get("key_id")
    assert eval_key_id == pinned_eval, (
        f"signing key {eval_key_id} does not derive the trust-store pinned "
        f"PHASE0_EVALUATOR key id {pinned_eval}; refusing to sign")
    assert eval_key_id.startswith(REQUIRED_KEYID_PREFIX), eval_key_id

    pins_sha = sha(PINS.read_bytes())

    for spec in DEMO_SPECS:
        demo_dir = DEMOS / spec["demo_id"]
        canon = (demo_dir / "diagnostic.canonical.json").read_bytes()
        run_b = (demo_dir / "diagnostic.runB.json").read_bytes()
        assert canon == run_b, f"{spec['demo_id']}: two-replay bytes differ; refusing to sign"
        diag_sha = sha(canon)
        diag = json.loads(canon)
        assert diag["authority"] == "AUDIT_ONLY", spec["demo_id"]
        assert diag["claim_locks"]["promotes_authority"] is False
        assert diag["claim_locks"]["modifies_manifest"] is False
        for src in diag["sources"]:
            assert len(src["sha256"]) == 64, "every oracle source must be sha-cited"

        body_obj = {
            "schema": spec["schema"],
            "receipt_id": spec["demo_id"],
            "module_id": "amphora-solver-lab",
            "authority": "AUDIT_ONLY",
            "authority_ceiling": "EVIDENCE_ONLY",
            "phase": "PRE_PHASE_0",
            "scientific_success_required_for_phase0": False,
            "date": diag["date"],
            "generated_on_host": diag["generated_on_host"],
            "promotes_authority": False,
            "flips_scientific_readiness": False,
            "human_review_performed": False,
            "organizational_independence_asserted": False,
            "modifies_manifest": False,
            "modifies_locked_dataset": False,
            "modifies_signed_phase0_kpi": False,
            "modifies_benchmark_lock": False,
            "grants_solver_authority": False,
            "grants_ranking_authority": False,
            "authority_posture": (
                "capability real, authority AUDIT_ONLY, promotion requires "
                "human ceremony"),
            "claim": spec["claim"],
            "pareto_status": diag["pareto_status"],
            "sources": diag["sources"],
            "source_pins_file_sha256": pins_sha,
            "diagnostic": diag,
            "reproducibility": {
                "two_replay_sha256_gate": "PASS",
                "canonical_diagnostic_sha256": diag_sha,
                "runB_diagnostic_sha256": sha(run_b),
                "byte_identical": canon == run_b,
                "replay_method": (
                    "the solver_lab_demo binary was invoked twice as "
                    "independent processes (diagnostic.canonical.json, "
                    "diagnostic.runB.json); determinism is by construction "
                    "(f64 only, ordered reductions, pinned splitmix64 seeds, "
                    "BTreeMap-backed JSON) and the bytes must be identical "
                    "for this receipt to exist"),
            },
            "signing_key": {
                "role": "PHASE0_EVALUATOR",
                "key_id": eval_key_id,
                "public_key_hex": eval_pub_hex,
                "used_for": "AUDIT_ONLY demo receipt under evidence/phase0/demos/",
                "signs_phase0_evaluation_or_review": False,
                "derives_pinned_trust_store_key_id": True,
            },
        }
        body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
        ptype = spec["payload_type"]
        sig = eval_sk.sign(pae(ptype, body))
        envelope = {
            "payload": base64.standard_b64encode(body).decode(),
            "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}],
        }
        receipt = {
            "evaluator_key_id": eval_key_id,
            "evaluator_public_key_hex": eval_pub_hex,
            "signature": envelope,
        }
        out = demo_dir / spec["receipt_basename"]
        out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

        # Self-verify from the written bytes: rebuild PAE, verify, pin keyid.
        reread = json.loads(out.read_text())
        env2 = reread["signature"]
        assert env2["signatures"][0]["keyid"].startswith(REQUIRED_KEYID_PREFIX)
        Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(reread["evaluator_public_key_hex"])).verify(
            base64.standard_b64decode(env2["signatures"][0]["sig"]),
            pae(env2["payloadType"], base64.standard_b64decode(env2["payload"])))

        print("WROTE", out)
        print("  demo_id", spec["demo_id"])
        print("  two_replay_sha256", diag_sha)
        print("  receipt_sha256", sha(out.read_bytes()))
        print("  keyid", eval_key_id)
        print("  self_verified", True)


if __name__ == "__main__":
    main()
