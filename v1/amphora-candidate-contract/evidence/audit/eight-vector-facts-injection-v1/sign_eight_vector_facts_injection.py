#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-candidate-contract eight-vector
facts-injection AUDIT_ONLY receipt (campaign item T-01 / directive T2-01).

Signs the byte-stable two-replay diagnostic with the on-host Phase-0
evaluator Ed25519 seed. AUDIT_ONLY: produces a signed audit receipt under
evidence/audit/ (and a copy into evidence/phase0/repairs/T-01/done/ per the
item's structured done_check), does NOT sign a phase0 evaluation/review,
does NOT promote authority, does NOT modify the manifest, mission.md, or
any signed Phase-0 KPI. The derived key_id is cross-checked against the
pinned trust store as an integrity assertion only.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-candidate-contract/evidence/audit/eight-vector-facts-injection-v1"
DONE_DIR = ROOT / "amphora-candidate-contract/evidence/phase0/repairs/T-01/done"
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
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_eight_vector_facts_injection.py").read_bytes())

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
    "schema": "amphora.candidate-contract.eight-vector-facts-injection-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-candidate-contract",
    "campaign_item_id": diag["campaign_item_id"],
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_or_capability_profile": False,
    "axis": diag["axis"],
    "claim_under_attack": diag["claim_under_attack"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observed": diag["refutation_criterion_observed"],
    "refutation_criterion_statement": diag["refutation_criterion_statement"],
    "directive_ref": diag["directive_ref"],
    "directive_path": diag["directive_path"],
    "directive_sha256": diag["directive_sha256"],
    "directive_sha256_verified_now": diag["directive_sha256_verified_now"],
    "directive_obligation": diag["directive_obligation"],
    "founder_directive_done_criteria_verbatim": diag["founder_directive_done_criteria_verbatim"],
    "founder_directive_done_criteria_met": diag["founder_directive_done_criteria_met"],
    "theory_reference": diag["theory_reference"],
    "non_circularity": diag["non_circularity"],
    "results": {
        "n_vectors": diag["n_vectors"],
        "n_evaded": diag["n_evaded"],
        "n_detected_leak": diag["n_detected_leak"],
        "all_property_results_byte_identical_across_all_8_vectors_and_control": diag[
            "all_property_results_byte_identical_across_all_8_vectors_and_control"
        ],
        "all_vectors_had_raw_untyped_echo_hits": diag["all_vectors_had_raw_untyped_echo_hits"],
        "two_replay_byte_identical_probe": diag["two_replay_byte_identical"],
    },
    "per_vector_table": diag["per_vector_table"],
    "positive_control": diag["positive_control"],
    "equivalent_balance_analysis": diag["equivalent_balance_analysis"],
    "source_hashes": diag["source_hashes"],
    "control_clean_molecule_facts_v1": diag["control_clean_molecule_facts_v1"],
    "control_clean_property_results": diag["control_clean_property_results"],
    "finding": diag["headline"],
    "verdict": diag["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "harness_main_rs_sha256": diag["harness_main_rs_sha256"],
        "probe_stdout_sha256": diag["probe_stdout_sha256"],
    },
    "does_not_close": diag["does_not_close"],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/ and evidence/phase0/repairs/T-01/done/",
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
ptype = "application/vnd.amphora.candidate-contract-eight-vector-facts-injection+json"
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

out = BENCH / "eight-vector-facts-injection-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

DONE_DIR.mkdir(parents=True, exist_ok=True)
done_out = DONE_DIR / "eight-vector-facts-injection-receipt.v1.dsse.json"
done_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
pk.verify(base64.standard_b64decode(json.loads(done_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(done_out.read_text())["signature"]["payload"])))

print("WROTE", out)
print("WROTE", done_out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
