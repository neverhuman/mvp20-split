#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard legal-status / patent-term AUDIT_ONLY receipt.

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
BENCH = ROOT / "amphora-ip-fto-guard/evidence/audit/legal-status-term-v1"
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
harness_sha = sha((BENCH / "run_legal_status_term.py").read_bytes())

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

cA = diag["checkA_status_lattice"]
cB = diag["checkB_grounding_severability"]
cC = diag["checkC_term_arithmetic"]
cD = diag["checkD_status_non_elevation"]
cE = diag["checkE_authority_envelope"]
fc = diag["fail_closed_mutation_demo"]
kpi = diag["kpi_reconstruction"]

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.ip-fto-guard.legal-status-term-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-ip-fto-guard",
    "as_of_date": diag["as_of_date"],
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
    "results": {
        "status_lattice_totality": cA["lattice_totality"],
        "status_node_histogram": cA["status_node_histogram"],
        "unmapped_status_rows": cA["unmapped_rows"],
        "clearance_language_clean": cA["clearance_language_clean"],
        "clearance_language_hits": cA["clearance_language_hits"],
        "family_status_verified_false_count": cA["family_status_verified_false_count"],
        "verified_status_basis_consistent": cA["basis_consistent"],
        "no_row_count": cB["no_row_count"],
        "H0_strict_verdict": cB["H0_strict_verdict"],
        "rows_with_any_status_clause": cB["rows_with_status_clause"],
        "H0_directional_verdict": cB["H0_directional_verdict"],
        "rows_with_clearance_directional_status_clause": cB["rows_with_clearance_directional_status_clause"],
        "severability_verdict": cB["severability_verdict"],
        "severable_rows": cB["severable_rows"],
        "non_severable_rows": cB["non_severable_rows"],
        "term_rows_evaluated": cC["rows_evaluated"],
        "term_arithmetic_all_consistent": cC["all_consistent"],
        "term_inconsistent_rows": cC["inconsistent_rows"],
        "section_156_pte_available": cC["section_156_pte_available"],
        "provably_term_expired_count": cD["provably_term_expired_count"],
        "held_unclear_despite_certain_expiry": cD["held_unclear_despite_certain_expiry"],
        "converted_to_non_read_on_expiry_alone": cD["converted_to_non_read_on_expiry_alone"],
        "status_non_elevation_holds": cD["non_elevation_holds"],
        "not_fto_true_count": cD["not_fto_true_count"],
        "every_row_not_fto_true": cD["every_row_not_fto_true"],
        "authority_envelope_clean": cE["envelope_clean"],
        "forbidden_legal_closure_key_hits": len(cE["forbidden_legal_closure_key_hits"]),
        "all_fail_closed_mutations_caught": fc["all_mutations_caught"],
        "fail_closed_mutation_catch_rate": kpi["fail_closed_mutation_catch_rate"],
        "severability_rate": kpi["severability_rate"],
    },
    "checkA_status_lattice": cA,
    "checkB_grounding_severability": cB,
    "checkC_term_arithmetic": cC,
    "checkD_status_non_elevation": cD,
    "checkE_authority_envelope": cE,
    "fail_closed_mutation_demo": fc,
    "kpi_reconstruction": kpi,
    "finding": diag["finding"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "as_of_date_is_pinned_constant_not_wall_clock": True,
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
ptype = "application/vnd.amphora.ip-fto-guard-legal-status-term+json"
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

out = BENCH / "legal-status-term-receipt.v1.dsse.json"
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
