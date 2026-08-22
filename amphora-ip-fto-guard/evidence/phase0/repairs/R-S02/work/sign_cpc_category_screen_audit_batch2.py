#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard R-S02 CPC category-screen audit,
batch 2/3 (rows n=24,25,27..42). AUDIT_ONLY checkpoint receipt into
attempts/ -- the R-S02 done_criterion requires all 54 rows verdicted before
a done/ receipt is filed; this fire covers 18 more (36/54 total), so it
lands in attempts/ regardless of the (still cumulatively REFUTED, carried
from batch1) verdict.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-ip-fto-guard/evidence/phase0/repairs/R-S02"
WORK = ITEM / "work"
ATTEMPTS = ITEM / "attempts"
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
canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((WORK / "run_cpc_category_screen_audit_batch2.py").read_bytes())
state = json.loads((WORK / "STATE.json").read_text())

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

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.ip-fto-guard.r-s02-cpc-category-screen-audit-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "CPC_CATEGORY_SCREEN_PER_ROW_ADJUDICATION_AUDIT",
    "module": "amphora-ip-fto-guard",
    "campaign_item_id": "R-S02",
    "batch": diag["batch"],
    "repair_status": "in_progress",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "supersedes": None,
    "claim_under_attack": diag["claim_under_attack"],
    "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "source_provenance": diag["source_provenance"],
    "fixture": diag["fixture"],
    "batch_rows": diag["batch_rows"],
    "rows": diag["rows"],
    "counts": diag["counts"],
    "prior_batch_counts": diag["prior_batch_counts"],
    "cumulative_counts": diag["cumulative_counts"],
    "cumulative_rows_audited": diag["cumulative_rows_audited"],
    "cumulative_rows_remaining": diag["cumulative_rows_remaining"],
    "cumulative_state": state,
    "headline": diag["headline"],
    "verdict": "CLAIM_REFUTED",
    "verdict_rationale": (
        "This batch (rows n=24,25,27..42, 18 rows) found 0 new fabricated/"
        "misassigned rows -- all 18 CPC/IPC assignments resolve to real, "
        "official CPC Title List symbols whose scope faithfully covers each "
        "row's own described chemistry (including two symbols requiring "
        "fresh corpus excerpts this batch: C09D7/43 'Thickening agents' for "
        "a rheology modifier, and C23C22/00 for zinc-phosphate conversion "
        "coatings). The pinned universal claim over all 54 rows, however, "
        "remains REFUTED: batch 1 already produced a genuine counter-example "
        "(row n=19, C08G59/50 'Amines' misassigned to an epoxide-side "
        "reactive-diluent family) and one counter-example is sufficient to "
        "refute a universal claim regardless of how many subsequent rows "
        "check out clean. The campaign continues to batch 3/3 (n=43..60) to "
        "complete the full 54-row audit per the R-S02 done_criterion, which "
        "requires every row to receive a verdict before a done/ receipt is "
        "filed -- 'done' (all rows verdicted) is independent of the claim's "
        "truth value (already false)."
    ),
    "proposed_followups": diag["proposed_followups"],
    "does_not_close": diag["does_not_close"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY checkpoint receipt under evidence/phase0/repairs/R-S02/attempts/",
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
ptype = "application/vnd.amphora.ip-fto-guard-r-s02-cpc-category-screen-audit+json"
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

ATTEMPTS.mkdir(parents=True, exist_ok=True)
out = ATTEMPTS / "cpc-category-screen-audit-batch2.R-S02.v1.dsse.json"
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
print("signature_verified", True)
