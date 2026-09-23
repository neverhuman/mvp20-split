#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-design-gate
nitrogen-nucleophilicity-authenticity-v1 AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest (66 receipts /
11 modules), module-manifest.json, any locked dataset, the design-gate fixture,
or a signed Phase-0 KPI. Derived key_id cross-checked vs pinned trust store."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / ("amphora-molecule-design-gate/evidence/audit/"
                "nitrogen-nucleophilicity-authenticity-v1")
FIX = ROOT / "amphora-molecule-design-gate/reference/phase0-design-gate-known-answer.v1.json"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
ORACLE = BENCH / "design_gate_nucleophilicity_oracle.py"


def sha(b):
    return hashlib.sha256(b).hexdigest()


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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
oracle_sha = sha(ORACLE.read_bytes())
fixture_sha = sha(FIX.read_bytes())

assert diag["gates"]["all_pass"] is True, "refusing to sign: not all gates passed"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw()
rev_pub_hex = rev_pub.hex()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

g = diag["gates"]
h = diag["g2_g3_g7_hostile_probes"]
lad = diag["g2b_protonation_monotonicity"]

body_obj = {
    "schema": ("amphora.molecule-design-gate."
               "nitrogen-nucleophilicity-authenticity-receipt.v1"),
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "REAL_ARITHMETIC",
    "run_type": diag["run_type"],
    "module": "amphora-molecule-design-gate",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_design_gate_fixture": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_live_rust_runtime": False,
    "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "non_circularity": diag["non_circularity"],
    "adversarial_relevance": diag["adversarial_relevance"],
    "defect_disclosure": diag["defect_disclosure"],
    "theory_reference": diag["theory_reference"],
    "clause_set": diag["clause_set"],
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "rdkit_version": diag["rdkit_version"],
    "results": {
        "all_gates_passed": g["all_pass"],
        "corpus_non_regression": {
            "baseline_reproduces_shipped_facts_and_labels":
                g["g0_baseline_reproduces_shipped_semantics"],
            "refined_reproduces_shipped_facts_and_labels":
                g["g1_refined_non_regressive_on_corpus"],
            "n_fact_bearing_records": diag["counts"]["corpus_fact_bearing_records"],
            "n_gate_records": diag["counts"]["corpus_total_gate_records"],
        },
        "hostile_probes": {
            "n_probes": h["n"],
            "n_mechanism_classes": diag["counts"]["hostile_mechanism_classes"],
            "n_refined_matches_expectation": h["n_refined_matches_expectation"],
            "n_baseline_peratom_matches_expectation":
                h["n_baseline_peratom_matches_expectation"],
            "n_baseline_smarts_matches_expectation":
                h["n_baseline_smarts_matches_expectation"],
            "n_baseline_over_admitting": h["n_baseline_over_admitting"],
            "total_baseline_over_admission_excess_H":
                h["total_baseline_over_admission_excess_H"],
            "n_gate_level_evasions_closed": h["n_baseline_gate_evasions"],
            "evaded_probe_ids": h["evaded_probe_ids"],
            "n_baseline_method_divergences": h["n_baseline_method_divergences"],
            "divergent_probe_ids": h["divergent_probe_ids"],
        },
        "protonation_monotonicity": {
            "n_ladders": lad["n_ladders"],
            "n_rungs": lad["n_rungs_total"],
            "hardeners": [x["hardener"] for x in lad["records"]],
            "refined_series": {x["hardener"]: x["refined_series"] for x in lad["records"]},
            "baseline_series": {x["hardener"]: x["baseline_series"] for x in lad["records"]},
            "all_refined_strictly_decreasing": lad["all_refined_strictly_decreasing"],
            "all_baseline_strictly_increasing": lad["all_baseline_strictly_increasing"],
            "verdict": lad["verdict"],
        },
        "clause_necessity": {
            "n_clauses": diag["counts"]["clauses"],
            "n_new_clauses": diag["counts"]["new_clauses"],
            "all_necessary": g["g4_clause_set_irredundant"],
            "readmitted_per_dropped_clause": {
                r["dropped_clause"]: r["n_hostile_readmitted"]
                for r in diag["g4_clause_necessity_ablation"]["records"]},
        },
        "clause_inertness_on_shipped_corpus": {
            "all_inert": g["g5_clauses_inert_on_shipped_corpus"],
            "n_corpus_records_changed_per_dropped_clause": {
                r["dropped_clause"]: r["n_corpus_records_changed"]
                for r in diag["g5_clause_inertness_on_corpus"]["records"]},
        },
        "positive_controls": {
            "n": diag["counts"]["positive_controls"],
            "all_match_hand_derived_and_gate_accept":
                g["g6_positive_controls_not_over_strict"],
            "per_control": {
                p["probe_id"]: {
                    "expected_amineH": p["hand_derived_expected_amineH"],
                    "refined_amineH": p["refined_amineH"],
                    "molecular_weight_g_mol": p["molecular_weight_g_mol"],
                    "implied_ahew_g_per_eq": p["implied_ahew_g_per_eq"],
                } for p in diag["g6_positive_controls"]["records"]},
        },
        "salt_forms_fail_closed_lexically": g["salt_forms_fail_closed_lexically"],
        "counts": diag["counts"],
    },
    "gates": diag["gates"],
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "oracle_sha256": oracle_sha,
        "oracle_path": ("evidence/audit/nitrogen-nucleophilicity-authenticity-v1/"
                        "design_gate_nucleophilicity_oracle.py"),
        "dataset_fixture_sha256": fixture_sha,
        "dataset_fixture_path": "reference/phase0-design-gate-known-answer.v1.json",
        "prior_receipts": [
            "evidence/audit/rdkit-structural-facts-parity-v1",
            "evidence/audit/smiles-representation-invariance-v1",
        ],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_sha256": oracle_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": ("Reviewer key referenced for provenance only; no independent "
                 "human review performed."),
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = ("application/vnd.amphora.molecule-design-gate-"
         "nitrogen-nucleophilicity-authenticity+json")
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id,
                    "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}
out = BENCH / "nitrogen-nucleophilicity-authenticity-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("fixture_sha256", fixture_sha)
print("oracle_sha256", oracle_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
