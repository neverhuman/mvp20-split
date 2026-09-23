#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V-A10 independent verify of R-A10 (campaign item
V-A10, fire 20260805T130001-2493531-73111bc80943). AUDIT_ONLY verify
receipt under evidence/phase0/repairs/V-A10/. Does not modify the
portfolio manifest, docs/mission.md, or any previously-signed Phase-0
KPI/receipt. Uses the pinned PHASE0_EVALUATOR key.
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
BENCH = MOD / "benchmarks/va10-independent-verify-v1"
REPAIR_DIR = MOD / "evidence/phase0/repairs/V-A10"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260805T130001-2493531-73111bc80943"


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

    harness_sha = sha((BENCH / "run_va10_verify.py").read_bytes())

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

    r_a10_done = MOD / "evidence/phase0/repairs/R-A10/done/r-a10-prose-consistency-w7-disclosure-repair-receipt.v1.dsse.json"

    body_obj = {
        "schema": "amphora.solvency-score.va10-independent-verify-receipt.v1",
        "receipt_id": "va10-independent-verify-v1",
        "authority": "AUDIT_ONLY",
        "run_type": "VERIFY",
        "module_id": "amphora-solvency-score",
        "verify_item": "V-A10",
        "repair_under_test": "R-A10",
        "campaign_item_id": "V-A10",
        "fire_id": FIRE_ID,
        "verify_mode": "campaign-2026-08-05",
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "modifies_manifest": False,
        "modifies_existing_receipts": False,
        "modifies_mission_md": False,
        "claim": (
            "INDEPENDENT VERIFY of interactive repair R-A10 (mission prose "
            "consistency + W7 disclosure repair). R-A10 done receipt found "
            "present at evidence/phase0/repairs/R-A10/done/ "
            f"(sha256 {diag['r_a10_done_receipt_sha256']}). Did not write "
            "R-A10; independently re-derived all 4 pre-registered verdict "
            "items from live sources rather than trusting R-A10's own "
            "self-report: (1) byte-compared docs/mission.md's front-matter "
            "JSON block against the preserved pre-repair snapshot at "
            "evidence/phase0/repairs/R-A10/work/mission.md.pre-R-A10; (2) "
            "parsed the live front-matter and grepped prose for both the "
            "correct phase/readiness tokens and stale contradictory tokens "
            "(Pre-Phase 0, PRE_PHASE_0, SHADOW, UNVALIDATED); (3) cross-"
            "checked the W7 void-disclosure banners' quoted ceiling/"
            "delta_p-max/delta_d-max/verdict against the LIVE W7 audit "
            "receipt payload (not against R-A10's own quoted numbers); (4) "
            "cross-checked the BigSolDB headline's quoted RMSE/CI/baseline/"
            "n/error-reduction figures against the LIVE W6 hardened-"
            "validation receipt payload. Then swept all 5 of this module's "
            "falsification-ledger entries (C1, W6, W7, V1-SOLV, V-B03) "
            "against the full mission.md prose for any further "
            "contradiction, including a post-R-A10 addition (the 2026-08-04 "
            "'V1-SOLV CLOSURE' notice, added by a later fire, not by R-A10) "
            "which this verify also checked for internal consistency."
        ),
        "verdict": diag["verdict"],
        "verdict_summary": (
            "All 4 R-A10 acceptance items independently confirmed against live "
            "sources: front-matter byte-identical pre/post repair; prose phase/"
            "readiness values match front-matter with zero stale-token hits; "
            "all 3 W7 void banners' quoted numbers (ceiling 59.9 [receipt "
            "59.875], FH delta_p max 5.2e9 [receipt 5155043623.84], Hansen "
            "delta_d max 5.33e17 [receipt 5.33395e17], verdict CLAIM_REFUTED) "
            "match the live W7 receipt exactly; the BigSolDB headline quotes "
            "both the signed 0.8770 (95% CI [0.8416,0.9154]) and the W6-"
            "hardened 0.8742 (95% CI [0.8405,0.9114], baseline 1.1667, "
            "n=94,015, 25.08% error reduction), all matching the live W6 "
            "receipt exactly. Ledger sweep: 5/5 module ledger entries checked "
            "against the full mission.md prose, 0 contradictions found (C1 "
            "has no prose surface to contradict; W6/W7/V1-SOLV are correctly "
            "disclosed; V-B03 has no standalone prose claim). CLAIM_SURVIVED."
        ),
        "reattack_re_run_original_repair_self_checks": {
            "note": (
                "R-A10 has no prior falsifying attack to re-run (it is a "
                "prose-consistency repair with no antecedent refutation "
                "receipt of its own); per objective this verify instead "
                "independently re-derives R-A10's 4 acceptance criteria from "
                "live sources rather than trusting R-A10's self-reported "
                "'reattack' block."
            ),
            "r_a10_self_reported_reattack_all_passed": True,
        },
        "diagnostic": diag,
        "reproducibility": {
            "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
            "canonical_diagnostic_sha256": canon_sha,
            "runA_diagnostic_sha256": sha_file(BENCH / "diagnostic.runA.json"),
            "runB_diagnostic_sha256": sha_file(BENCH / "diagnostic.runB.json"),
            "byte_identical": byte_identical,
            "harness_sha256": harness_sha,
            "determinism": "fully deterministic, no RNG; string/JSON parsing only",
        },
        "supersedes": None,
        "provenance_of_repair_under_test": {
            "path": str(r_a10_done.relative_to(ROOT)),
            "sha256": sha_file(r_a10_done),
        },
        "does_not_close": [
            "human / independent review",
            "any change to scientific_success_required_for_phase0 or manifest counts",
            "the W7b follow-on scope beyond what V1-SOLV already closed",
        ],
        "toolchain": {"python": "3.12"},
        "signing_key": {
            "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
            "used_for": "AUDIT_ONLY verify done receipt under evidence/phase0/repairs/V-A10/",
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
    ptype = "application/vnd.amphora.solvency-score-va10-independent-verify-receipt+json"
    sig = eval_sk.sign(pae(ptype, body))
    envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
                "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
    receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
               "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

    dest_dir_name = sys.argv[1] if len(sys.argv) > 1 else "attempts"
    out_dir = REPAIR_DIR / dest_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "va10-independent-verify-receipt.v1.dsse.json"
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
