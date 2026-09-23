#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-evidence-intake-validator
receipt-authority-derivability-freshness-v1 AUDIT_ONLY receipt.
Signs under evidence/audit/; does NOT promote authority, flip
scientific_readiness (stays NOT_APPLICABLE), or modify the portfolio manifest
(66 receipts / 11 modules), any locked dataset, the Phase-0 KPI, or the
benchmark-lock."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-evidence-intake-validator"
SLUG = "receipt-authority-derivability-freshness-v1"
EV = MOD / "evidence/audit" / SLUG
BM = MOD / "benchmarks" / SLUG
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"
SHIPPED_RESULT = MOD / "evidence/phase0/benchmark/result.v1.json"
PRIOR = {
    "host-receipt-oracle-parity-v1/eiv_oracle.py":
        MOD / "evidence/audit/host-receipt-oracle-parity-v1/eiv_oracle.py",
    "predicate-completeness-v1/predicate-completeness-receipt.v1.dsse.json":
        MOD / "evidence/audit/predicate-completeness-v1/predicate-completeness-receipt.v1.dsse.json",
    "canonicalization-invariance-tamper-v1/canonicalization-invariance-tamper-receipt.v1.dsse.json":
        MOD / "evidence/audit/canonicalization-invariance-tamper-v1/canonicalization-invariance-tamper-receipt.v1.dsse.json",
}

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

harness_sha = sha((BM / "run_authority_derivability.py").read_bytes())
benchmark_lock_sha = sha(BLOCK.read_bytes())
shipped_result_sha = sha(SHIPPED_RESULT.read_bytes())
prior_sha = {k: sha(p.read_bytes()) for k, p in PRIOR.items()}

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

g1 = diag["g1_conjunct_authority_partition"]
g2 = diag["g2_authoring_forgeability_h0"]
g3 = diag["g3_temporal_freshness_semantics"]
g4 = diag["g4_adversary_class_power"]
g5 = diag["g5_conservative_repair"]

body_obj = {
    "schema": "amphora.evidence-intake-validator.receipt-authority-derivability-freshness-receipt.v1",
    "receipt_id": SLUG,
    "module_id": "amphora-evidence-intake-validator",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": diag["date"],
    "generated_on_host": "xbabe2",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_benchmark_lock": False,
    "modifies_shipped_runtime": False,
    "claim": (
        "TRUST-AUTHORITY certificate for the evidence-intake acceptance "
        "predicate. Three prior audits established WHAT the 11-conjunct "
        "predicate decides (decision parity, the exact 2^11 boolean structure, "
        "and byte-binding tamper completeness); none asked WHO SUPPLIES THE "
        "TRUTH of each accepting conjunct. Probing the predicate empirically "
        "over an 8-package epoxy-amine coating evidence corpus partitions the "
        "11 conjuncts into 3 CANDIDATE_DERIVED (candidate_id, "
        "candidate_contract_hash_v1, package_sha256 -- each flips ACCEPT->REJECT "
        "under all 56/56 cross-candidate value transplants), 7 CONSTANT_ASSERTED "
        "(schema, accepted, signature_verified, revocation_checked, fresh, "
        "signature_algorithm, trust_store_status -- exactly one accepting value, "
        "identical for every candidate and publicly known) and 1 UNCONSTRAINED "
        "(verifier_id: any non-empty string, including 'attacker-named-kernel'), "
        "giving candidate-binding fraction 3/11 = 0.2727 and attestation deficit "
        "8/11 = 0.7273. The predicate performs 2 SHA-256 operations and ZERO "
        "signature verifications, ZERO trust-store lookups and ZERO revocation "
        "lookups; no conjunct requires any key material. H0 -- 'an accepting "
        "host-verified receipt can only be produced by a party that actually "
        "verified an Ed25519 signature against a pinned trust store' -- is "
        "REFUTED: a zero-capability authoring emitter (no key, no verification, "
        "no trust-store access) mints accepting receipts for 64/64 "
        "adversary-authored marine-coating evidence packages at a cost of 2 "
        "SHA-256 each, and each forged receipt is BYTE-IDENTICAL to the honest "
        "receipt for the same candidate (0 bits of distinguishing information), "
        "so the deficit is not merely detectable-in-principle but provably "
        "undetectable by any function of the receipt. Temporally the decision is "
        "empty: 0 of 11 fields carry an issued_at / expiry / nonce / sequence "
        "binding, ACCEPT is invariant across all 12 probed epochs spanning 100 "
        "years, 100 independent honest re-issuances collapse to 1 distinct "
        "receipt hash (replay-distinguishing entropy 0 bits, replay window "
        "unbounded), and the receipt still accepts after the verifier key is "
        "revoked (revocation effect on decision 0.0) because "
        "revocation_checked/trust_store_status are emitter-asserted bits rather "
        "than looked-up state. Per-conjunct detection power is therefore "
        "adversary-class dependent, power vector [11, 3, 0] over A1 field-flip / "
        "A2 cross-candidate replay / A3 authoring emitter; all 14 shipped "
        "adversarial probes are A1 field-flips on a validly-constructed base "
        "receipt, so the shipped suite covers 14/14 of one class and 0 of the "
        "authoring class the deficit lives in. A conservative repair (Denning-"
        "Sacco 1981 timestamp+window, ISO/IEC 9798-1, RFC 8032 Ed25519, SLSA "
        "v1.0 verifier-side verification) adding issued_at + max_age_s + a "
        "trust-store-pinned verifier_signature (11 -> 14 fields, 0 -> 1 Ed25519 "
        "verify) is validated as strictly conservative: 8/8 honest corpus "
        "packages still accept, ALL 17 shipped decisions are preserved (3 accept "
        "/ 14 reject), A3 forgeries drop 64/64 -> 0/64, accepting epochs drop "
        "12/12 -> 5/12 with the acceptance-window boundary exact (accept at "
        "t0+86400 s, reject at t0+86401 s), re-issuance at 12 distinct times "
        "yields 12 distinct receipts, and both key revocation and an unpinned "
        "verifier_id now reject. The 3 shipped positive package_sha256 anchors "
        "and all 17 shipped runtime decisions are reproduced (G0), tying the "
        "certificate to the actually-shipped predicate."),
    "theory": diag["theory"],
    "live_authority_under_test": diag["live_authority_under_test"],
    "corpus": diag["corpus"],
    "results": {
        "all_gates_passed": diag["all_gates_passed"],
        "g0_anchors_matched": diag["g0_shipped_continuity"]["n_anchors_matched"],
        "g0_shipped_decision_parity": diag["g0_shipped_continuity"]["n_decision_parity"],
        "g0_shipped_records": diag["g0_shipped_continuity"]["n_shipped_records"],
        "g1_counts": g1["counts"],
        "g1_candidate_binding_fraction": g1["candidate_binding_fraction"],
        "g1_attestation_deficit_fraction": g1["attestation_deficit_fraction"],
        "g1_signature_verifications_by_predicate": g1["n_signature_verifications_performed_by_predicate"],
        "g1_trust_store_lookups_by_predicate": g1["n_trust_store_lookups_performed_by_predicate"],
        "g1_revocation_lookups_by_predicate": g1["n_revocation_list_lookups_performed_by_predicate"],
        "g1_conjuncts_requiring_key_material": g1["n_conjuncts_requiring_key_material"],
        "g2_h0_verdict": g2["h0_verdict"],
        "g2_forgeries_accepted": g2["n_forgeries_accepted"],
        "g2_forgery_attempts": g2["n_forgery_attempts"],
        "g2_forgery_success_rate": g2["forgery_success_rate"],
        "g2_forged_byte_identical_to_honest": g2["n_forged_receipts_byte_identical_to_honest_receipt"],
        "g2_distinguishing_information_bits": g2["distinguishing_information_bits"],
        "g3_temporal_binding_fields": g3["n_temporal_binding_fields_present"],
        "g3_epochs_probed": g3["n_epochs_probed"],
        "g3_epoch_span_years": g3["epoch_span_years"],
        "g3_distinct_decisions_across_epochs": g3["n_distinct_decisions_across_epochs"],
        "g3_distinct_receipts_over_100_reissuances": g3["n_distinct_receipt_hashes_over_reissuances"],
        "g3_accept_after_verifier_key_revoked": g3["accept_after_verifier_key_revoked"],
        "g3_valid_replay_window_s": g3["valid_replay_window_s"],
        "g4_predicate_power_vector_A1_A2_A3": g4["predicate_power_vector"],
        "g4_shipped_probes_in_A1": g4["shipped_probes_in_A1"],
        "g4_shipped_probes_in_A3": g4["shipped_probes_in_A3"],
        "g5_honest_path_accepts": g5["honest_path_accepts"],
        "g5_honest_path_n": g5["honest_path_n"],
        "g5_shipped_decisions_preserved": g5["shipped_decisions_preserved"],
        "g5_a3_forgeries_accepted_v1": g5["a3_forgeries_accepted_v1"],
        "g5_a3_forgeries_accepted_v2": g5["a3_forgeries_accepted_v2"],
        "g5_epochs_accepting_v1": g5["n_epochs_accepting_v1"],
        "g5_epochs_accepting_v2": g5["n_epochs_accepting_v2"],
        "g5_accept_at_window_boundary": g5["accept_at_window_boundary_t0_plus_max_age"],
        "g5_accept_one_second_past_expiry": g5["accept_one_second_past_expiry"],
        "g5_accept_after_revocation_v2": g5["accept_after_revocation_v2"],
        "g5_accept_with_unpinned_verifier_id_v2": g5["accept_with_unpinned_verifier_id_v2"],
        "g5_field_count_v1_v2": [g5["repair_spec"]["field_count_v1"],
                                 g5["repair_spec"]["field_count_v2"]],
        "g5_signature_verifications_v1_v2": [g5["repair_spec"]["signature_verifications_v1"],
                                             g5["repair_spec"]["signature_verifications_v2"]],
        "total_decisions_evaluated": diag["counts"]["total_decisions_evaluated"],
    },
    "gates": diag["gates"],
    "scope_note": diag["scope_note"],
    "closes": diag["closes"],
    "does_not_establish": diag["does_not_establish"],
    "provenance": {
        "harness_sha256": {"run_authority_derivability.py": harness_sha},
        "shipped_result_v1_sha256": shipped_result_sha,
        "benchmark_lock_sha256": benchmark_lock_sha,
        "reused_prior_artifacts_sha256": prior_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "determinism_note": (
            "No wall clock and no RNG: the temporal probes use a fixed synthetic "
            "epoch T0=1750000000 and the repair demo verifier key is derived "
            "deterministically as sha256(b'amphora-eiv-repair-demo-verifier-v1'); "
            "Ed25519 signatures are deterministic per RFC 8032."),
        "replay_method": (
            "independent CPython re-derivation: re-implement amphora-core "
            "canonicalize+stable_hash and host_receipt_valid, reproduce the 3 "
            "shipped package anchors and all 17 shipped decisions, then probe "
            "conjunct authority by 56 cross-candidate value transplants per "
            "field, 64 zero-capability authoring forgeries, 12-epoch / "
            "100-reissuance temporal probes, a 3-class adversary power table, "
            "and a signed timestamp-window repair predicate re-evaluated over "
            "the same shipped decision set"),
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
ptype = "application/vnd.amphora.evidence-intake-receipt-authority-derivability-freshness+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / "receipt-authority-derivability-freshness-receipt.v1.dsse.json"
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
