#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V-B03 independent verify of R-B03 (campaign item
V-B03, fire 20260805T010001-1386032-c5c06054b58e). AUDIT_ONLY verify
receipt under evidence/phase0/repairs/V-B03/. Does not modify the
portfolio manifest or any previously-signed Phase-0 KPI/receipt. Uses the
pinned PHASE0_EVALUATOR key.
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-solvency-score"
BENCH = MOD / "benchmarks/vb03-independent-verify-v1"
REPAIR_DIR = MOD / "evidence/phase0/repairs/V-B03"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260805T010001-1386032-c5c06054b58e"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes())


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


def main():
    runA = json.loads((BENCH / "diagnostic.runA.json").read_bytes())
    runB = json.loads((BENCH / "diagnostic.runB.json").read_bytes())
    canon_bytes = json.dumps(runA, sort_keys=True, separators=(",", ":")).encode()
    runB_canon_bytes = json.dumps(runB, sort_keys=True, separators=(",", ":")).encode()
    byte_identical = canon_bytes == runB_canon_bytes
    canon_sha = sha(canon_bytes)
    diag = runA

    harness_sha = sha((BENCH / "run_vb03_verify.py").read_bytes())
    attack_a_sha = sha((BENCH / "independent_rederivation_boundary_collision.py").read_bytes())
    attack_c_sha = sha((BENCH / "fresh_omg_sample_200_seed999999.py").read_bytes())

    eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
    eval_pub = eval_sk.public_key().public_bytes_raw()
    eval_pub_hex = eval_pub.hex()
    eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
    rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
    rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
    rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust["keys"]}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
    assert eval_pin, "evaluator key_id does not match pinned trust store"
    assert byte_identical, "two-replay bytes differ -- NOT stable, do not sign"
    assert diag["verdict"] == "CLAIM_SURVIVED"

    rb03_path = MOD / "evidence/phase0/repairs/R-B03/done/flory-hansen-corrected-instrument-repair-receipt.v1.dsse.json"
    instrument_path = MOD / "benchmarks/flory-hansen-corrected-v1/compute_group_contribution.py"
    test_path = MOD / "benchmarks/flory-hansen-corrected-v1/test_compute_group_contribution.py"

    body_obj = {
        "schema": "amphora.solvency-score.vb03-independent-verify-receipt.v1",
        "receipt_id": "vb03-independent-verify-v1",
        "authority": "AUDIT_ONLY",
        "run_type": "VERIFY",
        "module_id": "amphora-solvency-score",
        "verify_item": "V-B03",
        "repair_under_test": "R-B03",
        "campaign_item_id": "V-B03",
        "fire_id": FIRE_ID,
        "verify_mode": "campaign-2026-08-05",
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "modifies_manifest": False,
        "modifies_existing_receipts": False,
        "claim": (
            "INDEPENDENT VERIFY of interactive repair R-B03. R-B03 done receipt "
            "found present and unmodified (instrument sha256 "
            f"{diag['instrument_sha256_verified_unchanged']} byte-identical to the "
            "sha the R-B03 receipt itself declares). Did not write R-B03; attacked "
            "it fresh with 4 escalated, genuinely-falsifying probes beyond the "
            "repair's own self-check: (A) hand-typed independent re-derivation of "
            "Fedors delta_total for all 4 Hansen 2007 Table A.1 anchors from the "
            "published group table, cross-checked against both the instrument and "
            "the handbook reference values (not merely re-running the instrument's "
            "own ANCHORS dict); (B) 20,000-trial randomized adversarial search "
            "(fresh seed 20260805, never used by R-B03) over pathological "
            "negative-volume group combinations hunting for a volume-floor-gate "
            "bypass or an envelope-gate leak; (C) a genuinely fresh OMG sample "
            "(seed=999999 vs R-B03's seed=0; only 4/200 molecules overlap R-B03's "
            "own 2500-molecule sample), with independent corpus-hash "
            "re-verification against the rights manifest lock and an atom-level "
            "ground-truth audit of every REJECTED_UNCOVERED_FRAGMENT reason string "
            "(not just trusting the reported reason); (D) 8 hand-built SMILES "
            "engineered to stress the documented first-match-wins greedy "
            "group-claiming priority order (amide/ester/amine, thioether/aromatic-S, "
            "isocyanate/amide, guanidine-like multi-nitrogen collisions)."
        ),
        "verdict": "CLAIM_SURVIVED",
        "verdict_summary": (
            "None of the 4 escalated attacks produced their pre-declared refuting "
            "observation. All 10 of R-B03's own unit tests re-run and pass. Anchor "
            "re-derivation matches the instrument bitwise and the Hansen 2007 "
            "handbook within documented tolerance for all 4 anchors (worst case "
            "water 14.18% rel err vs 15% tolerance). 20,000 adversarial group "
            "combinations: zero volume-floor bypasses, zero envelope leaks. Fresh "
            "200-molecule OMG draw (different seed, near-zero sample overlap): zero "
            "out-of-envelope returns, exact accounting identity, and the one "
            "candidate reason-string anomaly the atom-level audit flagged traced "
            "on manual RDKit inspection to a genuine, correctly-rejected coverage "
            "gap (an aromatic-ring exocyclic lactone/ketone oxygen, e.g. in "
            "chromone/coumarin/pyranone-type rings, that no SMARTS group in the "
            "declared table claims -- gate (a) worked exactly as designed: REJECTED, "
            "never silently zero-filled). Greedy-claim collision stress: all 8 "
            "cases assign groups consistent with documented priority and correct "
            "chemistry; guanidine/isocyanate carbons fall through to the generic "
            "sp2 Fedors approximation (in-envelope) while Hansen correctly declines "
            "via vk_constants_unavailable rather than guessing."
        ),
        "reattack_re_run_original_unit_tests": {
            "command": "python3 -m pytest test_compute_group_contribution.py -v",
            "test_file_sha256": sha_file(test_path),
            "result": "10 passed",
        },
        "diagnostic": diag,
        "reproducibility": {
            "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
            "canonical_diagnostic_sha256": canon_sha,
            "runA_diagnostic_sha256": sha_file(BENCH / "diagnostic.runA.json"),
            "runB_diagnostic_sha256": sha_file(BENCH / "diagnostic.runB.json"),
            "byte_identical": byte_identical,
            "harness_sha256": harness_sha,
            "attack_a_script_sha256": attack_a_sha,
            "attack_c_script_sha256": attack_c_sha,
            "determinism": "seeds: attack A none (closed-form), attack B seed=20260805, attack C seed=999999; rdkit 2026.03.2",
        },
        "supersedes": None,
        "provenance_of_repair_under_test": {
            "path": str(rb03_path.relative_to(ROOT)),
            "sha256": sha_file(rb03_path),
            "instrument_path": str(instrument_path.relative_to(ROOT)),
            "instrument_sha256": sha_file(instrument_path),
            "instrument_sha256_matches_rb03_receipt_declared": (
                sha_file(instrument_path) ==
                "4fbf6c0c5ea222b3e3c5e2be1826c642d3bfeb04650684ae0644dd8275f65fa9"),
        },
        "does_not_close": [
            "extending the group table to the ~16-20% uncovered OMG chemistry "
            "(sulfones, Si, B, P, azo/N-oxide, and now also aromatic-ring "
            "exocyclic carbonyl O found in this fire's fresh sample)",
            "W7b ML-vs-physics comparison (already closed separately by V1-SOLV)",
            "human / independent review",
            "any change to scientific_success_required_for_phase0 or manifest counts",
        ],
        "toolchain": {"python": "3", "rdkit": "2026.03.2"},
        "signing_key": {
            "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
            "used_for": "AUDIT_ONLY verify done receipt under evidence/phase0/repairs/V-B03/",
            "signs_phase0_evaluation_or_review": False,
            "derives_pinned_trust_store_key_id": bool(eval_pin),
        },
        "reviewer_reference": {
            "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
            "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
            "note": "Reviewer key referenced for provenance only; no independent human review performed.",
        },
    }

    body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
    ptype = "application/vnd.amphora.solvency-score-vb03-independent-verify-receipt+json"
    sig = eval_sk.sign(pae(ptype, body))
    envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
                "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
    receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
               "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

    dest_dir_name = sys.argv[1] if len(sys.argv) > 1 else "attempts"
    out_dir = REPAIR_DIR / dest_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "vb03-independent-verify-receipt.v1.dsse.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

    Ed25519PublicKey.from_public_bytes(eval_pub).verify(
        base64.standard_b64decode(envelope["signatures"][0]["sig"]),
        pae(ptype, base64.standard_b64decode(envelope["payload"])))

    print("WROTE", out)
    print("verdict", diag["verdict"])
    print("evaluator_key_id", eval_key_id)
    print("eval_derives_pinned_trust_key", eval_pin)
    print("two_replay_sha256", canon_sha)
    print("envelope_sha256", sha_file(out))
    print("signature_verified", True)


if __name__ == "__main__":
    main()
