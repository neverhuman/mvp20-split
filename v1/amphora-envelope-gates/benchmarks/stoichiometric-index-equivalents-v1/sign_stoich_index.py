#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-envelope-gates stoichiometric-index-equivalents-v1
AUDIT_ONLY receipt. Signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays NOT_APPLICABLE), does NOT modify the portfolio manifest
(66 receipts / 11 modules), any locked dataset, the Phase-0 KPI, or the benchmark-lock.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
EV = MOD / "evidence/audit/stoichiometric-index-equivalents-v1"
BM = MOD / "benchmarks/stoichiometric-index-equivalents-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"
FX = MOD / "reference/phase0-envelope-gates-known-answer.v1.json"
PRIOR = MOD / "benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py"


def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]


canon = (EV / "diagnostic.canonical.json").read_bytes()
runB = (EV / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["all_gates_passed"] is True, "gates not all passed"

harness_sha = sha((BM / "run_stoich_index.py").read_bytes())
prior_oracle_sha = sha(PRIOR.read_bytes())
benchmark_lock_sha = sha(BLOCK.read_bytes())
fixture_sha = sha(FX.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

g = diag["gates"]
mc = diag["metrology_constants"]
body_obj = {
    "schema": "amphora.envelope-gates.stoichiometric-index-equivalents-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-envelope-gates",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_benchmark_lock": False,
    "claim": diag["headline"], "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "fixture": diag["fixture"],
    "metrology_constants": mc,
    "ahew_derivation": diag["ahew_derivation"],
    "data_gap": diag["data_gap"],
    "results": {
        "all_gates_passed": diag["all_gates_passed"],
        "n_envelopes": g["G2_index_excursion_invariance"]["n_envelopes"],
        "n_hardeners_first_principles_ahew_in_band": g["G1_first_principles_ahew_in_band"]["n_in_band"],
        "index_excursion_amine_rich_pct": mc["index_excursion_amine_rich_pct"],
        "index_excursion_amine_lean_pct": mc["index_excursion_amine_lean_pct"],
        "mass_only_gum_rss_pct": mc["mass_only_gum_rss_pct"],
        "combined_gum_rss_pct": mc["combined_gum_rss_pct"],
        "combined_strictly_exceeds_mass_only": g["G3_gum_equivalent_weight_extension"]["strict"],
        "n_envelopes_index_excursion_invariant": g["G2_index_excursion_invariance"]["n_invariant"],
        "n_envelopes_with_index_gate_gap": g["G4_stoichiometric_index_gate_gap"]["n_gap_exhibited"],
        "index_tamper_probes_total": g["G5_index_tamper_battery_fail_closed"]["n_probes"],
        "index_tamper_probes_fail_closed": g["G5_index_tamper_battery_fail_closed"]["n_fail_closed"],
    },
    "gates": g,
    "acceptance_bar_floors": diag["acceptance_bar_floors"],
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "provenance": {
        "module_benchmark_lock_sha256": benchmark_lock_sha,
        "known_answer_fixture_sha256": fixture_sha,
        "harness_sha256": {"run_stoich_index.py": harness_sha},
        "reused_oracle_sha256": {"constraint-envelope-oracle-v1/run_envelope_gates.py": prior_oracle_sha},
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "independent full pipeline: reload KAT fixture bytes, "
                         "derive AHEW from IUPAC-2021 atomic weights + active-H "
                         "count, compute the equivalents stoichiometric index and "
                         "its EEW/AHEW-invariant interval excursion, the GUM "
                         "combined uncertainty with equivalent-weight terms, "
                         "corner-PASS under the shipped oracle, and the index "
                         "tamper battery",
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
ptype = "application/vnd.amphora.envelope-gates-stoichiometric-index-equivalents+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / "stoichiometric-index-equivalents-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
