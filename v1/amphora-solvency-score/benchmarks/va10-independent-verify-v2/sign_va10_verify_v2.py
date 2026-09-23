#!/usr/bin/env python3
"""DSSE-Ed25519-sign the SECOND-PASS independent verify of R-A10 (campaign
item V-A10, this fire 20260805T140001-2900337-9002a94ffc39). This fire's
objective: the 13:00 V-A10 verify (fire 20260805T130001-2493531-73111bc80943)
succeeded and produced a valid signed receipt, but a launcher bug (unbound
variable) aborted post-processing so the item was never marked done. Per the
objective, do NOT redo the verification from scratch as new work product --
independently RE-VERIFY the 13:00 receipt's claims against live sources
(fresh checks, plus a real Ed25519 crypto re-verification of the DSSE chain
that the 13:00 pass did not perform) and land a NEW signed receipt.
AUDIT_ONLY. Uses the pinned PHASE0_EVALUATOR key.
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
BENCH = MOD / "benchmarks/va10-independent-verify-v2"
REPAIR_DIR = MOD / "evidence/phase0/repairs/V-A10"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260805T140001-2900337-9002a94ffc39"


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

    harness_sha = sha((BENCH / "run_va10_verify_v2.py").read_bytes())

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
    assert diag["real_input_all_passed"] is True
    assert diag["positive_control"]["detected"] is True
    assert diag["dsse_crypto_reverification"]["r_a10_done_receipt"]["passed"] is True
    assert diag["dsse_crypto_reverification"]["v_a10_first_pass_receipt"]["passed"] is True

    r_a10_done = MOD / "evidence/phase0/repairs/R-A10/done/r-a10-prose-consistency-w7-disclosure-repair-receipt.v1.dsse.json"
    v_a10_first = MOD / "evidence/phase0/repairs/V-A10/done/va10-independent-verify-receipt.v1.dsse.json"

    body_obj = {
        "schema": "amphora.solvency-score.va10-independent-verify-receipt.v2",
        "receipt_id": "va10-independent-verify-v2",
        "authority": "AUDIT_ONLY",
        "run_type": "VERIFY",
        "module_id": "amphora-solvency-score",
        "verify_item": "V-A10",
        "verify_pass": 2,
        "repair_under_test": "R-A10",
        "campaign_item_id": "V-A10",
        "fire_id": FIRE_ID,
        "verify_mode": "campaign-2026-08-05-second-pass",
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "modifies_manifest": False,
        "modifies_existing_receipts": False,
        "modifies_mission_md": False,
        "situation": (
            "A prior fire (20260805T130001-2493531-73111bc80943, 13:00) already independently "
            "verified R-A10 and produced a validly-signed receipt at "
            "evidence/phase0/repairs/V-A10/done/va10-independent-verify-receipt.v1.dsse.json with "
            "its ledger line appended. That fire's work was not defective -- a LAUNCHER bug (an "
            "unbound variable) aborted post-processing after success, so the campaign item was "
            "never marked done. This fire does NOT redo the verification from scratch as if nothing "
            "existed; it independently RE-VERIFIES the 13:00 receipt's own claims against live "
            "sources with a freshly-written checking harness (run_va10_verify_v2.py, distinct file "
            "from the 13:00 pass's run_va10_verify.py), and additionally performs a REAL Ed25519 "
            "cryptographic re-verification of the DSSE signature chain for both the R-A10 done "
            "receipt and the 13:00 V-A10 receipt against the pinned PHASE0_EVALUATOR trust-store "
            "key -- a check the 13:00 pass did not perform (it only hash-compared provenance blocks, "
            "never called Ed25519 verify on either upstream artifact)."
        ),
        "claim": (
            "INDEPENDENT VERIFY (second pass) of interactive repair R-A10 (mission prose consistency "
            "+ W7 disclosure repair) and of the 13:00 V-A10 verify receipt covering it. Re-derived "
            "all 4 pre-registered R-A10 acceptance items directly from live sources: (1) front-matter "
            "byte-identical pre/post repair; (2) prose phase/readiness tokens consistent with live "
            "front-matter, zero stale-token hits; (3) W7 void-disclosure banners' quoted "
            "ceiling/delta_p-max/delta_d-max/verdict cross-checked against the LIVE W7 audit receipt "
            "payload; (4) BigSolDB headline's quoted RMSE/CI/baseline/n/error-reduction figures "
            "cross-checked against the LIVE W6 hardened-validation receipt payload. Additionally "
            "cryptographically re-verified the DSSE Ed25519 signatures of the R-A10 done receipt and "
            "the 13:00 V-A10 receipt against the pinned trust-store key (both PASS). Swept all 6 of "
            "this module's current falsification-ledger entries (C1, W6, W7, V1-SOLV, V-B03, V-A10) "
            "against the full mission.md prose for contradiction -- the 6th entry is this module's own "
            "13:00 V-A10 line, which post-dates and was excluded from the 13:00 receipt's own 5-entry "
            "sweep (an artifact of sweep-before-self-append ordering, not a defect)."
        ),
        "verdict": diag["verdict"],
        "verdict_summary": (
            "All 4 R-A10 acceptance items independently re-confirmed against live sources with a "
            "freshly-written harness: front-matter byte-identical (sha256 "
            f"{diag['real_input_results'][0]['fm_current_sha256'][:16]}... == pre-repair snapshot); "
            "prose phase/readiness values match front-matter, 0 stale-token hits; W7 void banners' "
            "quoted numbers (ceiling 59.9 [receipt 59.875], FH delta_p max 5.2e9 [receipt "
            "5155043623.84], Hansen delta_d max 5.33e17 [receipt 5.33395e17], verdict CLAIM_REFUTED) "
            "match the live W7 receipt exactly; BigSolDB headline quotes both signed 0.8770 and "
            "W6-hardened 0.8742/1.1667/94,015/25.08% matching the live W6 receipt exactly. NEW: real "
            "Ed25519 signature verification of both the R-A10 done receipt and the 13:00 V-A10 "
            "receipt against the pinned PHASE0_EVALUATOR key -- both PASS (the 13:00 receipt did not "
            "perform this check on either artifact, only sha256 hash comparison). Ledger sweep: 6/6 "
            "current module ledger entries checked, 0 contradictions found. Positive control: two "
            "independently planted defects (front-matter phase field tamper; W7 ceiling tamper) both "
            "detected on mutated in-memory copies while the real live inputs pass clean. "
            "CLAIM_SURVIVED -- this second, independent pass does NOT contradict the 13:00 receipt; "
            "it corroborates it and closes the gap the 13:00 pass left open (no cryptographic "
            "signature re-verification)."
        ),
        "diagnostic": diag,
        "reproducibility": {
            "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
            "canonical_diagnostic_sha256": canon_sha,
            "runA_diagnostic_sha256": sha_file(BENCH / "diagnostic.runA.json"),
            "runB_diagnostic_sha256": sha_file(BENCH / "diagnostic.runB.json"),
            "byte_identical": byte_identical,
            "harness_sha256": harness_sha,
            "determinism": "fully deterministic, no RNG; string/JSON parsing, sha256, Ed25519 verify only",
        },
        "supersedes": None,
        "provenance_of_repair_under_test": {
            "path": str(r_a10_done.relative_to(ROOT)),
            "sha256": sha_file(r_a10_done),
        },
        "provenance_of_prior_verify_pass": {
            "path": str(v_a10_first.relative_to(ROOT)),
            "sha256": sha_file(v_a10_first),
            "fire_id": "20260805T130001-2493531-73111bc80943",
            "verdict": "CLAIM_SURVIVED",
            "note": "First-pass verify. Not redone from scratch; independently re-checked plus cryptographically re-verified by this fire.",
        },
        "does_not_close": [
            "human / independent review",
            "any change to scientific_success_required_for_phase0 or manifest counts",
            "the W7b follow-on scope beyond what V1-SOLV already closed",
        ],
        "toolchain": {"python": "3.12"},
        "signing_key": {
            "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
            "used_for": "AUDIT_ONLY second-pass verify done receipt under evidence/phase0/repairs/V-A10/",
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
    ptype = "application/vnd.amphora.solvency-score-va10-independent-verify-receipt-v2+json"
    sig = eval_sk.sign(pae(ptype, body))
    envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
                "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
    receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
               "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

    dest_dir_name = sys.argv[1] if len(sys.argv) > 1 else "attempts"
    out_dir = REPAIR_DIR / dest_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "va10-independent-verify-v2-receipt.v1.dsse.json"
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
