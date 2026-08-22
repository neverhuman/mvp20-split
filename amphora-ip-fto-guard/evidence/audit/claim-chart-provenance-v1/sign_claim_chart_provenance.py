#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard claim-chart-provenance AUDIT_ONLY receipt.

Signs the byte-stable two-replay diagnostic with the on-host Phase-0 evaluator
Ed25519 seed. AUDIT_ONLY: produces a signed audit receipt under evidence/audit/,
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
modify the manifest (still 66 receipts / 11 modules), the pinned patent-landscape
fixture, or any signed Phase-0 KPI. The derived key_id is cross-checked against
the pinned trust store as an integrity assertion only.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-ip-fto-guard/evidence/audit/claim-chart-provenance-v1"
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


# --- two-replay gate --------------------------------------------------------
canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_claim_chart_provenance.py").read_bytes())

# --- derive public keys / key_ids from on-host seeds ------------------------
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

res = diag["results"]
fc = diag["fail_closed_mutation_demo"]

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.ip-fto-guard.claim-chart-provenance-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-ip-fto-guard",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "claim": diag["headline"],
    "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "inputs": diag["inputs"],
    "hash_and_count_lock": diag["hash_and_count_lock"],
    "charted_rows_audited": diag["charted_rows_audited"],
    "charted_row_count": diag["charted_row_count"],
    "results": {
        "pass_count": res["pass_count"],
        "fail_count": res["fail_count"],
        "fail_rows": res["fail_rows"],
        "provenance_fidelity_rate": res["provenance_fidelity_rate"],
        "per_row_status": [{"n": r["n"], "doc_read": r["doc_read"], "status": r["status"],
                             "unsupported_elements": r["unsupported_elements"],
                             "raw_snapshot_sha256_matches_pin": r["raw_snapshot_sha256_matches_pin"]}
                            for r in diag["results"]["rows"]],
    },
    "row_26_defect_detail": next(
        (r for r in diag["results"]["rows"] if r["n"] == 26), None
    ),
    "fail_closed_mutation_demo": fc,
    "finding": diag["finding"],
    "verdict": "CLAIM_REFUTED" if res["fail_count"] > 0 else "CLAIM_SURVIVED",
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "raw_snapshots_hash_pinned": True,
    },
    "does_not_close": diag["does_not_close"],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
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
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.ip-fto-guard-claim-chart-provenance+json"
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

out = BENCH / "claim-chart-provenance-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify ------------------------------------------------------------
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
print("verdict", body_obj["verdict"])
print("signature_verified", True)
