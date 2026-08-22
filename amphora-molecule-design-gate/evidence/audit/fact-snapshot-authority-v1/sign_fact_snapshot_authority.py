#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-design-gate
fact-snapshot-authority-v1 AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest (66 receipts /
11 modules), module-manifest.json, any locked dataset, the design-gate fixture,
the live Rust runtime, or a signed Phase-0 KPI. Derived key_id cross-checked vs
pinned trust store."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / ("amphora-molecule-design-gate/evidence/audit/"
                "fact-snapshot-authority-v1")
FIX = ROOT / "amphora-molecule-design-gate/reference/phase0-design-gate-known-answer.v1.json"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

HARNESS_MAIN = BENCH / "live_harness/src/main.rs"
HARNESS_CARGO = BENCH / "live_harness/Cargo.toml"
PROBE_GEN = BENCH / "make_probes.py"
ORACLE = BENCH / "analyze.py"
PROBES = BENCH / "probes.v1.json"


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
assert canon == runB, "two-replay diagnostic bytes differ"
live_canon = (BENCH / "live-run.canonical.json").read_bytes()
live_runB = (BENCH / "live-run.runB.json").read_bytes()
assert live_canon == live_runB, "two-replay live-run bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

assert diag["gates"]["all_pass"] is True, "refusing to sign: not all gates passed"
assert diag["counts"]["n_oracle_mismatches"] == 0, "refusing to sign: oracle mismatch"

harness_sha = sha(HARNESS_MAIN.read_bytes())
cargo_sha = sha(HARNESS_CARGO.read_bytes())
probe_gen_sha = sha(PROBE_GEN.read_bytes())
oracle_sha = sha(ORACLE.read_bytes())
probes_sha = sha(PROBES.read_bytes())
fixture_sha = sha(FIX.read_bytes())
live_sha = sha(live_canon)

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
assert eval_pin, "evaluator key_id does not derive pinned trust-store id"

g = diag["gates"]

body_obj = {
    "schema": ("amphora.molecule-design-gate."
               "fact-snapshot-authority-receipt.v1"),
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
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "results": {
        "all_gates_passed": g["all_pass"],
        "oracle_matches_live_all_probes": g["oracle_matches_live_all_probes"],
        "n_probes": diag["counts"]["n_probes"],
        "n_oracle_mismatches": diag["counts"]["n_oracle_mismatches"],
        "counts": diag["counts"],
        "gates": diag["gates"],
        "g1_snapshot_authorship_pass": g["g1_snapshot_authorship_inert_structure_scores"],
        "g2_lexical_ladder_bypass_pass": g["g2_lexical_ladder_bypassed_when_snapshot_present"],
        "g3_binding_inertness_pass": g["g3_structure_identity_binding_inert_to_gate"],
        "g4_serde_sole_wall_pass": g["g4_serde_contract_is_sole_admission_wall"],
        "g5_count_insensitivity_pass": g["g5_count_insensitive_above_presence_threshold"],
        "g6_decision_grid_pass": g["g6_role_reactivity_decision_grid_exact"],
    },
    "gates": diag["gates"],
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "live_harness_main_sha256": harness_sha,
        "live_harness_cargo_sha256": cargo_sha,
        "live_harness_path": ("evidence/audit/fact-snapshot-authority-v1/"
                              "live_harness/src/main.rs"),
        "probe_generator_sha256": probe_gen_sha,
        "probe_generator_path": ("evidence/audit/fact-snapshot-authority-v1/"
                                 "make_probes.py"),
        "analysis_oracle_sha256": oracle_sha,
        "analysis_oracle_path": ("evidence/audit/fact-snapshot-authority-v1/"
                                 "analyze.py"),
        "probes_sha256": probes_sha,
        "probes_path": "evidence/audit/fact-snapshot-authority-v1/probes.v1.json",
        "live_run_sha256": live_sha,
        "live_run_path": ("evidence/audit/fact-snapshot-authority-v1/"
                          "live-run.canonical.json"),
        "dataset_fixture_sha256": fixture_sha,
        "dataset_fixture_path": "reference/phase0-design-gate-known-answer.v1.json",
        "prior_receipts": [
            "evidence/audit/rdkit-structural-facts-parity-v1",
            "evidence/audit/smiles-representation-invariance-v1",
            "evidence/audit/nitrogen-nucleophilicity-authenticity-v1",
        ],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "diagnostic_byte_identical": canon == runB,
        "canonical_live_run_sha256": sha(live_canon),
        "runB_live_run_sha256": sha(live_runB),
        "live_run_byte_identical": live_canon == live_runB,
        "analysis_oracle_sha256": oracle_sha,
        "live_harness_main_sha256": harness_sha,
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
         "fact-snapshot-authority+json")
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
out = BENCH / "fact-snapshot-authority-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_diag_sha256", diag_sha)
print("two_replay_live_sha256", live_sha)
print("fixture_sha256", fixture_sha)
print("oracle_sha256", oracle_sha)
print("harness_sha256", harness_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
