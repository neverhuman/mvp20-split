#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-source-ledger
query-traceability-referential-integrity-v1 AUDIT_ONLY receipt. AUDIT_ONLY:
signs an audit receipt under evidence/audit/; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest (66 receipts /
11 modules), the module-manifest.json, any locked dataset, or a signed
Phase-0 KPI. Derived key_id cross-checked vs pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = (ROOT / "amphora-source-ledger/evidence/audit/"
         "query-traceability-referential-integrity-v1")
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b): return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["gates"]["all_pass"], "diagnostic gates did not all pass"
oracle_sha = sha(
    (BENCH / "source_ledger_query_traceability_oracle.py").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw()
rev_pub_hex = rev_pub.hex()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"

eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id ==
               tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

C = diag["counts"]
M = diag["derived_metrics"]

body_obj = {
    "schema": ("amphora.source-ledger."
               "query-traceability-referential-integrity-receipt.v1"),
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-source-ledger",
    "audit_date": diag["audit_date"],
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "runs_live_rust_runtime": False,
    "claim": diag["closes"],
    "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "preconditions": diag["preconditions"],
    "method_parameters": diag["method_parameters"],
    "results": {
        "all_gates_passed": diag["gates"]["all_pass"],
        "gates": diag["gates"],
        "counts": C,
        "derived_metrics": M,
        "derived_gates": diag["derived_gates"],
        # G0 anchor reproduction (pinned ledger hash + registry sizes)
        "anchors_reproduced": C["g0_anchors_matched"],
        "anchors_total": C["g0_anchors"],
        # G1 entity integrity (Codd 1970)
        "entity_integrity_holds":
            diag["derived_gates"]["entity_integrity_holds"],
        "duplicate_or_empty_keys": (
            C["g1_record_id_duplicates"] + C["g1_query_id_duplicates"]
            + C["g1_target_duplicates"] + C["g1_empty_keys"]),
        # G2 referential integrity (Date 1981)
        "referential_integrity_holds":
            diag["derived_gates"]["referential_integrity_holds"],
        "total_foreign_key_refs": C["g2_total_foreign_key_refs"],
        "dangling_refs": C["g2_dangling_refs"],
        # G3 record -> query traceability (H0a)
        "query_orphan_records": C["g3_query_orphan_records"],
        "records_total": C["g3_records"],
        "query_orphan_record_fraction": M["query_orphan_record_fraction"],
        "orphan_records_by_kind":
            diag["evidence"]["orphan_records_by_kind"],
        # G4 query load-bearing completeness (H0b)
        "record_orphan_queries": C["g4_record_orphan_queries"],
        "queries_total": C["g4_queries"],
        "orphan_query_register": diag["evidence"]["orphan_query_register"],
        # G5 target-linkage determinability (H0c)
        "targets_total": C["g5_targets"],
        "targets_syntactically_matched": C["g5_targets_syntactically_matched"],
        "target_key_defined_in_schema":
            diag["derived_gates"]["target_key_defined_in_schema"],
        "unmatched_targets": diag["evidence"]["unmatched_targets"],
        # G6 mutation / fail-closed probes
        "probes_killed": C["g6_probes_killed"],
        "probes_total": C["g6_probes"],
        "probe_register": diag["evidence"]["probe_register"],
        # headline
        "h0_refuted": diag["derived_gates"]["h0_refuted"],
        "orphan_record_register":
            diag["evidence"]["orphan_record_register"],
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase1_exit_criterion_impact": diag["phase1_exit_criterion_impact"],
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
        "ledger_sha256": diag["preconditions"]["ledger_sha256"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_sha256": oracle_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": ("Reviewer key referenced for provenance only; no "
                 "independent human review performed.")},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = ("application/vnd.amphora."
         "source-ledger-query-traceability-referential-integrity+json")
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(),
            "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id,
           "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex,
           "signature": envelope}
out = BENCH / "query-traceability-referential-integrity-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
