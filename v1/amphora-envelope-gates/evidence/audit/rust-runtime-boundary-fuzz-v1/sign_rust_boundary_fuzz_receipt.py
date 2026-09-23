#!/usr/bin/env python3
"""DSSE-Ed25519-sign the rust-runtime-boundary-fuzz-v1 receipt for
amphora-envelope-gates. AUDIT_ONLY. Does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the manifest, KPI, benchmark-lock, or
mission.md.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
ITEM = MOD / "evidence/audit/rust-runtime-boundary-fuzz-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260817T020001-1658651-c0ad9be3f969"

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

canon = (ITEM / "diagnostic.canonical.json").read_bytes()
runB = (ITEM / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

harness_src_sha = sha((ITEM / "harness/src/main.rs").read_bytes())
harness_cargo_sha = sha((ITEM / "harness/Cargo.toml").read_bytes())
real_lib_rs_sha = diag["real_runtime"]["src_sha256"]
t03_receipt_sha = sha((MOD / "evidence/phase0/repairs/T-03/done/t03-adversarial-attack-receipt.v1.dsse.json").read_bytes())
kpi_currency_receipt_sha = sha((MOD / "evidence/audit/kpi-claim-currency-v1/kpi-claim-currency-receipt.v1.dsse.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

body_obj = {
    "schema": "amphora.envelope-gates.rust-runtime-boundary-fuzz-receipt.v1",
    "study_id": "rust-runtime-boundary-fuzz-v1",
    "module": "amphora-envelope-gates",
    "authority": "AUDIT_ONLY",
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "verdict": "CLAIM_SURVIVED",
    "claim_under_attack": {
        "receipt_path": "amphora-envelope-gates/docs/mission.md",
        "claim_text": (
            "mission.md's 'Honest current state' names "
            "amphora-formulation-capabilities/src/lib.rs as the live checked "
            "implementation and its 'Current benchmark result' section asserts "
            "envelope_bound_inversion_fail_closed_rate=1.0 (3/3: lower>upper, "
            "lower=NaN, upper=Infinity all Err), "
            "trusted_feature_substitution_fail_closed_rate=1.0 (5/5, including "
            "non-finite snapshot value), envelope_policy_substitution_fail_closed_rate=1.0 "
            "and inclusive_boundary_correctness_rate=1.0 for the SHIPPED RUST "
            "evaluate_envelope_policy -- i.e. that the actual production code "
            "(not the retired Python oracle) is fail-closed on invalid/boundary "
            "envelope inputs."
        ),
        "distinguishing_note": (
            "T-03 (2026-08-05, CLAIM_REFUTED) and kpi-claim-currency-v1 "
            "(2026-08-15, CLAIM_REFUTED) both attacked and refuted the retired "
            "CPython oracle at benchmarks/constraint-envelope-oracle-v1/"
            "run_envelope_gates.py (imported as evaluate_gate()), finding real "
            "NaN/Infinity value-free-bypass slips. Both receipts explicitly "
            "recorded in their own scope_and_limits that they did NOT test 'the "
            "shipped Rust runtime (amphora-formulation-capabilities)'. This fire "
            "closes that named gap: it links the REAL, compiled, unmodified "
            "amphora_formulation_capabilities::evaluate_envelope_policy (not a "
            "reimplementation, not the Python oracle) via a standalone harness "
            "crate and re-runs T-03's boundary-fuzz grid plus the KPI's own 3 "
            "named sub-probes directly against it."
        ),
    },
    "attack_description": (
        "Standalone Rust crate (evidence/audit/rust-runtime-boundary-fuzz-v1/harness, "
        "own [workspace] root, path-dependency on the real "
        "amphora-formulation-capabilities crate) links and calls the compiled, "
        "unmodified evaluate_envelope_policy() directly -- not the retired Python "
        "oracle, not a reimplementation. 23 probes: the KPI's 3 named sub-probes "
        "(lower>upper, lower=NaN, upper=Infinity), T-03's confirmed slip classes "
        "reproduced against Rust (both-bounds-infinite value-free bypass, "
        "degenerate +Inf/+Inf, NaN/Infinite trusted feature values, unit-label "
        "mismatch, duplicate constraint_ids, unknown feature_path, empty "
        "constraints, non-authoritative-without-synthetic-flag, wrong schema, "
        "missing trusted feature), plus new combined-defect probes not run by "
        "any prior fire (all-three-constraints-inverted-simultaneously, a "
        "second/non-first constraint carrying the NaN bound or NaN value to "
        "confirm the per-constraint loop does not short-circuit after the first "
        "check, a zero-width envelope, and extreme finite bounds near f64::MAX "
        "to rule out overflow-to-infinity producing a false accept), plus 1-ULP "
        "inclusive-boundary probes (bit-exact 0.0 margin at the boundary, FAIL "
        "one ULP outside it)."
    ),
    "directive_ref": None,
    "refutation_criterion_verbatim": (
        "If the compiled, unmodified amphora_formulation_capabilities::"
        "evaluate_envelope_policy returns a non-abstaining PASS or FAIL scalar "
        "(instead of Err) on any invalid/boundary-gaming input in this probe set "
        "(non-finite or inverted bounds, non-finite trusted feature value, "
        "unit-label mismatch, duplicate/unknown/empty constraints), or returns "
        "Err/ABSTAIN where the fixture's expected behavior is a value-bearing "
        "PASS/FAIL, the mission.md claim that the SHIPPED RUST runtime is "
        "fail-closed on these axes is refuted."
    ),
    "refutation_criterion_observation_occurred": False,
    "observed_result": {
        "n_probes": diag["n_probes"],
        "n_fired_as_expected": diag["n_fired_as_expected"],
        "all_real_fail_closed_as_expected": diag["all_real_fail_closed_as_expected"],
        "per_probe": diag["probes"],
        "detail": (
            "23/23 probes fired as expected against the real, compiled "
            "evaluate_envelope_policy. Every non-finite-bound, inverted-bound, "
            "non-finite-feature-value, unit-mismatch, duplicate/unknown/empty "
            "constraint, and non-authoritative/wrong-schema probe returned Err "
            "or ABSTAIN as required; every valid boundary and mid-range probe "
            "returned the correct value-bearing PASS/FAIL with bit-exact margins "
            "at the inclusive boundary. None of the specific slips T-03 confirmed "
            "in the retired Python oracle (value-free +/-Infinity bypass, silent "
            "NaN feature acceptance) reproduce against the shipped Rust code: the "
            "Rust function's explicit `!lower.is_finite() || !upper.is_finite() "
            "|| lower > upper` and `!feature.value.is_finite()` guards (absent "
            "from the Python oracle) close exactly the holes T-03 found."
        ),
    },
    "positive_control": diag["positive_control"],
    "scope_and_limits": {
        "tested_artifact": (
            "the shipped Rust runtime amphora_formulation_capabilities::"
            "evaluate_envelope_policy, compiled and linked unmodified via a "
            "standalone path-dependency harness crate -- the exact artifact "
            "T-03 and kpi-claim-currency-v1 both named as untested."
        ),
        "not_tested": (
            "candidate_gate_pass_injection_ignore_rate is structurally not "
            "reachable through this function: evaluate_envelope_policy's public "
            "signature (policy, snapshot, allow_synthetic_fixture) accepts no "
            "candidate-authored pass_all_hard input at all, so injection at this "
            "call site is not merely fail-closed but architecturally impossible; "
            "this fire did not trace whether a candidate-authored boolean is "
            "merged with this function's result anywhere downstream in "
            "amphora-engine, which is out of this module's tree. Also not "
            "re-litigated: the still-open KPI-register currency gap "
            "(envelope-gates-constraint-envelope-kpi.v1.json remains stale per "
            "kpi-claim-currency-v1, unretracted) and the matching-but-mislabeled "
            "unit-scale gap T-03 already characterized as a documentation/label "
            "limit, not a hard slip -- neither is re-tested here."
        ),
        "no_promotion": True, "no_manifest_edit": True, "no_kpi_edit": True,
        "no_mission_md_edit": True, "no_scientific_readiness_flip": True,
        "remediation_needed": (
            "None for the Rust runtime itself -- it survives. The still-open "
            "remediation from prior fires stands: correct or retract the stale "
            "Python-oracle-sourced KPI register entries, or point them at this "
            "Rust harness's probe set instead."
        ),
    },
    "provenance": {
        "harness_crate_path": "amphora-envelope-gates/evidence/audit/rust-runtime-boundary-fuzz-v1/harness",
        "harness_main_rs_path": "amphora-envelope-gates/evidence/audit/rust-runtime-boundary-fuzz-v1/harness/src/main.rs",
        "harness_main_rs_sha256": harness_src_sha,
        "harness_cargo_toml_sha256": harness_cargo_sha,
        "real_runtime_path": "amphora-formulation-capabilities/src/lib.rs",
        "real_runtime_sha256_at_test_time": real_lib_rs_sha,
        "real_runtime_function": "amphora_formulation_capabilities::evaluate_envelope_policy",
        "build_command": "cargo build --release (workspace-isolated harness crate, path dependency)",
        "run_command": "ENVGATE_LIBRS_SHA256=<sha256> ./target/release/envgate-rust-boundary-fuzz-harness",
        "t03_receipt_path": "amphora-envelope-gates/evidence/phase0/repairs/T-03/done/t03-adversarial-attack-receipt.v1.dsse.json",
        "t03_receipt_sha256": t03_receipt_sha,
        "kpi_currency_receipt_path": "amphora-envelope-gates/evidence/audit/kpi-claim-currency-v1/kpi-claim-currency-receipt.v1.dsse.json",
        "kpi_currency_receipt_sha256": kpi_currency_receipt_sha,
        "note_on_mission_md_hash_drift": (
            "mission.md's own cited SHA-256 for amphora-formulation-capabilities/"
            "src/lib.rs (8b7612325bff9830da1eebd1dc6ba4af411205581ce388c45fdc6be5356edde0) "
            "does not match this file's live sha256sum at test time "
            f"({real_lib_rs_sha}), i.e. the file has changed since mission.md's "
            "hash-pin was last written (plausibly by unrelated concurrent work in "
            "amphora-formulation-capabilities, a different module this fire does "
            "not own). This fire tested the file AS IT ACTUALLY STANDS right now "
            "and records its true sha256 above; it does not correct mission.md's "
            "stale pin, which is a currency gap for a future fire, analogous to "
            "kpi-claim-currency-v1's finding but on the hash-pin rather than the "
            "KPI register."
        ),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": (
            "independent full re-run of the compiled harness binary twice "
            "(no randomness, no wall-clock reads, deterministic probe grid) "
            "against the unmodified evaluate_envelope_policy import"
        ),
        "seed": "n/a -- deterministic, no stochastic seed",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY ad-hoc audit receipt under evidence/audit/rust-runtime-boundary-fuzz-v1/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.envelope-gates-rust-runtime-boundary-fuzz+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payloadType": ptype, "payload": base64.standard_b64encode(body).decode(),
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}

out = ITEM / "rust-runtime-boundary-fuzz-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", diag_sha)
print("all_real_fail_closed_as_expected", diag["all_real_fail_closed_as_expected"])
print("positive_control_defect_detected", diag["positive_control"]["defect_detected"])
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
