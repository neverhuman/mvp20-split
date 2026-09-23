#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-source-ledger dual-source-independence-common-cause-v1
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
flip scientific_readiness, does NOT modify the portfolio manifest (66 receipts /
11 modules), the module-manifest.json, any locked dataset, or a signed Phase-0
KPI. Derived key_id cross-checked vs pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-source-ledger/evidence/audit/dual-source-independence-common-cause-v1"
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
oracle_sha = sha((BENCH / "source_ledger_independence_oracle.py").read_bytes())
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
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

C = diag["counts"]
M = diag["derived_metrics"]

body_obj = {
    "schema": "amphora.source-ledger.dual-source-independence-common-cause-receipt.v1",
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
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "preconditions": diag["preconditions"],
    "method_parameters": diag["method_parameters"],
    "results": {
        "all_gates_passed": diag["gates"]["all_pass"],
        "gates": diag["gates"],
        "counts": C,
        "derived_metrics": M,
        "derived_gates": diag["derived_gates"],
        # G0 anchor reproduction vs the SIGNED Phase-0 KPI
        "anchors_reproduced": C["g0_anchors_matched"],
        "anchors_total": C["g0_anchors"],
        # G1 independent count parity vs shipped pinned constants
        "count_parity_matched": C["g1_count_checks_matched"],
        "count_parity_total": C["g1_count_checks"],
        # G1B predicate-scope anchoring in shipped Rust source
        "runtime_predicate_is_syntactic_only":
            diag["derived_gates"]["runtime_predicate_is_syntactic_only"],
        "independence_terms_absent_from_runtime":
            diag["evidence"]["g1b_predicate_scope"]["independence_terms_absent_from_runtime"],
        # G2 controlled-registry membership of corroborating sources
        "dual_sourced_constants": C["g2_dual_sourced_constants"],
        "second_source_is_controlled_record": C["g2_second_source_is_controlled_record"],
        "primary_source_is_controlled_record": C["g2_primary_source_is_controlled_record"],
        # G3 common-cause coupling (Fleming 1975 beta-factor)
        "mechanically_coupled_pairs": C["g3_mechanically_coupled_pairs"],
        "coupled_pairs_including_interpretive": C["g3_coupled_pairs_including_interpretive"],
        "conservative_lineage_misses": C["g3_conservative_lineage_misses"],
        "effective_independent_source_count_mechanical":
            M["effective_independent_source_count_mechanical"],
        "effective_independent_source_count_full":
            M["effective_independent_source_count_full"],
        "claimed_source_count": M["claimed_source_count"],
        # G4 PRISMA item-9 numeric checkability
        "second_numeric_read_fields_in_schema": C["g4_second_numeric_read_fields_in_schema"],
        "prisma_item9_duplicate_comparison_possible":
            diag["derived_gates"]["prisma_item9_duplicate_comparison_possible"],
        # G5 mutation / fail-closed probes
        "probes_as_specified": C["g5_probes_as_specified"],
        "probes_total": C["g5_probes"],
        "runtime_counts_a_coupled_source_as_dual":
            C["g5_runtime_counts_a_coupled_source_as_dual"],
        # headline
        "h0_holds_mechanical_only": C["h0_holds_mechanical_only"],
        "h0_holds_full": C["h0_holds_full"],
        "controlled_and_independent_mechanical": C["controlled_and_independent_mechanical"],
        "controlled_and_independent_full": C["controlled_and_independent_full"],
        "h0_refuted": diag["derived_gates"]["h0_refuted"],
        "per_constant_verdict": diag["evidence"]["per_constant_verdict"],
        "conservative_lineage_miss_register":
            diag["evidence"]["g3_conservative_lineage_misses"],
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase1_exit_criterion_impact": diag["phase1_exit_criterion_impact"],
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_sha256": oracle_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.source-ledger-dual-source-independence-common-cause+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "dual-source-independence-common-cause-receipt.v1.dsse.json"
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
