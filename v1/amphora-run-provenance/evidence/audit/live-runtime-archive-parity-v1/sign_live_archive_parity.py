#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-run-provenance
live-runtime-archive-parity-v1 AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT change the shipped scheme or the pinned
signature_status/promotion_receipt_eligible, does NOT modify the portfolio
manifest (66 receipts / 11 modules), the module-manifest.json, any locked
dataset, or a signed Phase-0 KPI. The H0c erratum against the 2026
hash-chain-oracle-parity-v1 receipt is RECORDED here; the original receipt is
left byte-untouched. Derived key_id cross-checked vs the pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / ("amphora-run-provenance/evidence/audit/"
                "live-runtime-archive-parity-v1")
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
oracle_sha = sha((BENCH / "live_archive_parity_oracle.py").read_bytes())
harness_main_sha = sha((BENCH / "live_harness/src/main.rs").read_bytes())
harness_toml_sha = sha((BENCH / "live_harness/Cargo.toml").read_bytes())
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

c = diag["counts"]
body_obj = {
    "schema": "amphora.run-provenance.live-runtime-archive-parity-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-run-provenance",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_prior_audit_receipts": False,
    "changes_shipped_scheme": False,
    "runs_live_rust_runtime": True,
    "claim": diag["closes"],
    "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "toolchain": diag["toolchain"],
    "preconditions": diag["preconditions"],
    "results": {
        "all_gates_passed": diag["gates"]["all_pass"],
        "gates": diag["gates"],
        "counts": c,
        "live_scenarios_verified": c["g1_scenarios"],
        "live_field_parity": f"{c['g1_field_parity_pass']}/{c['g1_field_parity_checks']}",
        "live_interior_chain_bit_exact":
            f"{c['g1_interior_chain_events_bit_exact']}/{c['g1_interior_chain_events_recomputed']}",
        "legacy_receipt_differential":
            f"{c['g1b_differential_pass']}/{c['g1b_differential_checks']}",
        "taxonomy_probes_as_predicted":
            f"{c['g2_predicted_equals_observed']}/{c['g2_probes']}",
        "error_variants_covered_live": c["g2_error_variants_covered"],
        "strict_parse_wall_surfaces":
            f"{c['g3_strict_parse_wall_surfaces']}/{c['g3_surfaces']}",
        "parser_differentials_vs_rfc8785": c["g3_parser_differentials_demonstrated"],
        "forged_interior_chain_live_verify": diag["g4_interior_chain"][
            "live_verify_result_on_forged_interior_chain"],
        "forged_interior_mismatches_detected_by_oracle":
            c["g4_forged_interior_mismatches_detected_by_oracle"],
        "surface_binding_matrix":
            diag["g3_surface_binding_matrix"]["predicted_from_source"],
    },
    "verdict": diag["verdict"],
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "erratum_against_prior_receipt": {
        "receipt": "hash-chain-oracle-parity-v1 (2026, signed)",
        "affected_claim": "byte-format fidelity of its Python RunArchive mirror ('faithfully mirroring the Rust byte formats') and the example manifest_sha256/events_sha256/root_hash values of its G1 archives",
        "unaffected_claims": "hash-chain arithmetic, canonicalize/stable_hash parity, G0 shipped-anchor reproduction, tamper fail-closed logic, event-level hashes and value-bound fields (all reproduced bit-exact by the live runtime)",
        "root_cause": "mirror wrote Python-dict insertion-order JSON where the live runtime serializes serde_json Values key-sorted (BTreeMap): manifest.json bytes and payload sub-Values inside event lines",
        "evidence": "27/27 differential checks: live runtime rebuilt identical content; value-bound fields match the receipt bit-exact; re-serializing live content in the mirror's insertion orders reproduces every divergent hash exactly",
        "action": "original receipt left untouched; superseding live ground truth recorded here",
    },
    "phase1_requirement_derived": (
        "Phase-1 hardening derived from live ground truth: (a) verify the "
        "interior Haber-Stornetta event_hash linkage at verify time "
        "(Crosby-Wallach 2009 full-link verification) -- currently attested, "
        "not re-verified (H0b); (b) close the 4/5-surface strict-parse gap: "
        "parse manifest/final-state/provenance/snapshots with "
        "parse_json_strict or bind their raw bytes, eliminating the 2 "
        "demonstrated RFC 8785 parser differentials and the snapshot blind "
        "spot (H0a); (c) any future re-derivation mirror must be anchored to "
        "live-runtime bytes, not self-consistency (H0c lesson); plus the "
        "controlled-key signing pipeline already receipted in "
        "anchor-necessity-reforge-resistance-v1."),
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
        "harness_main_rs_sha256": harness_main_sha,
        "harness_cargo_toml_sha256": harness_toml_sha,
        "live_output_sha256": diag["preconditions"]["live_output_sha256"],
        "sibling_parity_receipt_sha256":
            diag["runtime_source_anchors"]["sibling_parity_receipt_sha256"],
        "sibling_merkle_receipt_sha256":
            diag["runtime_source_anchors"]["sibling_merkle_receipt_sha256"],
        "sibling_anchor_necessity_receipt_sha256":
            diag["runtime_source_anchors"]["sibling_anchor_necessity_receipt_sha256"],
        "shipped_kpi_sha256": diag["runtime_source_anchors"]["shipped_kpi_sha256"],
        "amphora_core_lib_rs_sha256":
            diag["runtime_source_anchors"]["amphora_core_lib_rs_sha256"],
        "amphora_core_contract_rs_sha256":
            diag["runtime_source_anchors"]["amphora_core_contract_rs_sha256"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_sha256": oracle_sha,
        "determinism_basis": ("no wall-clock, no RNG; the live harness is run "
                              "twice in different scratch directories and must "
                              "emit byte-identical output (only error-variant "
                              "NAMES recorded, never tempdir paths); the "
                              "diagnostic is then built independently from "
                              "each run and must be byte-identical; Ed25519 "
                              "signatures are deterministic per RFC 8032"),
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
        "note": ("Reviewer key referenced for provenance only; no independent "
                 "human review performed.")},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = ("application/vnd.amphora.run-provenance-"
         "live-runtime-archive-parity+json")
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(),
            "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id,
           "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "live-runtime-archive-parity-receipt.v1.dsse.json"
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
