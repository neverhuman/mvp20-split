#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard CPC/IPC coverage AUDIT_ONLY receipt.

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
BENCH = ROOT / "amphora-ip-fto-guard/evidence/audit/cpc-coverage-v1"
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
harness_sha = sha((BENCH / "run_cpc_coverage.py").read_bytes())

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

cA = diag["checkA_sweep_validity_and_axes"]
cB = diag["checkB_family_coverage"]
cC = diag["checkC_no_cpc_clearance"]
cD = diag["checkD_partial_order"]
cE = diag["checkE_authority_envelope"]
fc = diag["fail_closed_mutation_demo"]

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.ip-fto-guard.cpc-coverage-receipt.v1",
    "study_id": "IP_FTO_GUARD_CPC_IPC_COVERAGE_V1",
    "authority": "AUDIT_ONLY",
    "run_type": "CPC_IPC_COVERAGE_SUBSUMPTION_AUDIT",
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
    "results": {
        "all_sweeps_well_formed_or_informal": cA["all_sweeps_well_formed_or_informal"],
        "all_mandatory_axes_covered": cA["all_mandatory_axes_covered"],
        "well_formed_main_group_buckets": cA["well_formed_main_group_buckets"],
        "well_formed_subclass_buckets": cA["well_formed_subclass_buckets"],
        "informal_process_descriptors": cA["informal_process_descriptors"],
        "family_coverage_counts": cB["family_coverage_counts"],
        "families_reaching_a_declared_sweep": cB["families_reaching_a_declared_sweep"],
        "token_coverage_fraction": cB["token_coverage_fraction"],
        "bucket_coverage_fraction": cB["bucket_coverage_fraction"],
        "covered_buckets": cB["covered_buckets"],
        "coarse_category_buckets": cB["coarse_category_buckets"],
        "orphan_adjacency_buckets": cB["orphan_adjacency_buckets"],
        "orphan_adjacency_histogram": cB["orphan_adjacency_histogram"],
        "cpc_is_search_scope_not_clearance": cC["cpc_is_search_scope_not_clearance"],
        "every_row_not_fto_true": cC["every_row_not_fto_true"],
        "partial_order_well_formed": cD["partial_order_well_formed"],
        "authority_envelope_clean": cE["envelope_clean"],
        "forbidden_legal_closure_key_hits": len(cE["forbidden_legal_closure_key_hits"]),
        "hypothesis_corroborated": diag["kpi_reconstruction"]["hypothesis_surfaces_unresolved_without_claiming_fto"],
        "all_fail_closed_mutations_caught": fc["all_mutations_caught"],
    },
    "checkA_sweep_validity_and_axes": cA,
    "checkB_family_coverage_summary": {k: cB[k] for k in [
        "family_coverage_counts", "families_reaching_a_declared_sweep",
        "distinct_bucket_count", "covered_buckets", "coarse_category_buckets",
        "orphan_adjacency_buckets", "orphan_adjacency_histogram",
        "token_coverage_fraction", "bucket_coverage_fraction", "interpretation"]},
    "checkC_no_cpc_clearance": cC,
    "checkD_partial_order": cD,
    "fail_closed_mutation_demo": fc,
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
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
ptype = "application/vnd.amphora.ip-fto-guard-cpc-coverage+json"
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

out = BENCH / "cpc-coverage-receipt.v1.dsse.json"
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
