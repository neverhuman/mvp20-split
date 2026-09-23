#!/usr/bin/env python3
"""DSSE-Ed25519-sign the live-capability-dispatch-wiring-v1 receipt for
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
ITEM = MOD / "evidence/audit/live-capability-dispatch-wiring-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260818T200001-3337238-6111ed8b414f"

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
assert diag["n_cases"] == 50
assert diag["direct_evaluate_envelope_policy_pass_true_count"] == 30
assert diag["live_dispatch_pass_all_hard_true_count"] == 0
assert diag["live_dispatch_envelope_evaluated_true_count"] == 0
assert diag["cases_where_live_dispatch_disagrees_with_ground_truth"] == 30
assert diag["source_evidence"]["hardcoded_none_none_false_call_present"] is True
assert diag["source_evidence"]["envelope_gates_dispatch_fn_receives_features_param"] is False

harness_src_sha = sha((ITEM / "harness/src/main.rs").read_bytes())
harness_cargo_sha = sha((ITEM / "harness/Cargo.toml").read_bytes())
real_lib_rs_sha = diag["real_runtime_sha256_at_test_time"]
fixture_sha = diag["fixture_sha256"]

rust_boundary_fuzz_receipt_path = MOD / "evidence/audit/rust-runtime-boundary-fuzz-v1/rust-runtime-boundary-fuzz-receipt.v1.dsse.json"
rust_boundary_fuzz_receipt_sha = sha(rust_boundary_fuzz_receipt_path.read_bytes())
t03_receipt_path = MOD / "evidence/phase0/repairs/T-03/done/t03-adversarial-attack-receipt.v1.dsse.json"
t03_receipt_sha = sha(t03_receipt_path.read_bytes())
kpi_currency_receipt_path = MOD / "evidence/audit/kpi-claim-currency-v1/kpi-claim-currency-receipt.v1.dsse.json"
kpi_currency_receipt_sha = sha(kpi_currency_receipt_path.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

body_obj = {
    "schema": "amphora.envelope-gates.live-capability-dispatch-wiring-receipt.v1",
    "study_id": "live-capability-dispatch-wiring-v1",
    "module": "amphora-envelope-gates",
    "authority": "AUDIT_ONLY",
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "verdict": "CLAIM_REFUTED",
    "claim_under_attack": {
        "receipt_path": "amphora-envelope-gates/docs/mission.md",
        "claim_text": (
            "mission.md's 'Decision and falsifiable hypothesis' states this "
            "module 'supports the decision of whether deterministic "
            "formulation margins satisfy the declared screening envelope', "
            "and declares the Primary KPI as 'hard-gate consistency at "
            "gates.pass_all_hard'. The 'Current benchmark result' and "
            "'Honest current state' sections, plus the SURVIVED "
            "rust-runtime-boundary-fuzz-v1 receipt (2026-08-17), together "
            "assert that the shipped Rust runtime "
            "(amphora-formulation-capabilities) correctly and fail-closed-ly "
            "computes this pass_all_hard decision for real candidates -- i.e. "
            "that the live, production per-candidate envelope decision this "
            "module exists to support is actually being computed."
        ),
        "distinguishing_note": (
            "rust-runtime-boundary-fuzz-v1 (2026-08-17, CLAIM_SURVIVED) linked "
            "the real, compiled evaluate_envelope_policy() directly via its "
            "own standalone harness and confirmed the isolated function is "
            "fail-closed on 23/23 invalid/boundary probes. Its own "
            "scope_and_limits.not_tested explicitly flagged, unresolved: "
            "'this fire did not trace whether a candidate-authored boolean is "
            "merged with this function's result anywhere downstream in "
            "amphora-engine, which is out of this module's tree.' This fire "
            "traces exactly that -- not candidate-authored injection, but a "
            "more basic wiring question: does ANY real candidate's data ever "
            "reach evaluate_envelope_policy through the live production call "
            "path at all? It does not. evaluate_envelope_policy is called "
            "from exactly one non-test, non-diagnostic site in the entire "
            "workspace: envelope_gates(candidate), the function wired into "
            "FormulationCapability::evaluate() for ENVELOPE_GATES_ID -- the "
            "actual dispatch amphora-engine uses to score every live "
            "formulation candidate. That call site is hardcoded: "
            "`evaluate_envelope_policy(None, None, false)`, ignoring the "
            "candidate entirely. envelope_gates's own signature does not even "
            "receive the `features: &FeatureSnapshot` argument that sibling "
            "capabilities (e.g. public_corrosion_benchmark) do receive from "
            "the same evaluate() call. The isolated function's correctness, "
            "proven by rust-runtime-boundary-fuzz-v1, is real but "
            "unreachable by any live candidate."
        ),
    },
    "attack_description": (
        "Standalone Rust crate (evidence/audit/live-capability-dispatch-wiring-v1/"
        "harness, own [workspace] root, path dependencies on the real "
        "amphora-core and amphora-formulation-capabilities crates) runs all "
        "50 test cases from the module's own locked known-answer fixture "
        "(reference/phase0-envelope-gates-known-answer.v1.json, the same "
        "fixture mission.md's 'Current benchmark result' cites, SHA-256 "
        f"{fixture_sha}, matching mission.md's own cited hash) through TWO "
        "paths for direct comparison: (a) evaluate_envelope_policy(Some(&real"
        "_policy), Some(&real_snapshot), true) -- the direct call proven "
        "fail-closed and correct by rust-runtime-boundary-fuzz-v1 and used "
        "here purely as an independent ground-truth oracle; and (b) "
        "FormulationCapability::new(descriptor).evaluate(&candidate, "
        "&features, &context) for ENVELOPE_GATES_ID -- the ACTUAL live "
        "dispatch amphora-engine calls -- where the (b) candidate's "
        "formulation.part_A/part_B masses are built from the SAME test "
        "case's snapshot values as (a), so both paths score the same "
        "chemistry. The harness also greps the live real_runtime source at "
        "test time for the literal hardcoded call and for whether "
        "envelope_gates's signature receives a features parameter, as static "
        "corroboration of the dynamic result."
    ),
    "directive_ref": None,
    "refutation_criterion_verbatim": (
        "If the live, production capability-dispatch code path that "
        "amphora-engine actually calls for a real formulation candidate "
        "(FormulationCapability::evaluate for ENVELOPE_GATES_ID, i.e. the "
        "envelope_gates(candidate) function) reports gates.pass_all_hard and "
        "gates.envelope_evaluated as constants that do not vary with the "
        "candidate's actual formulation -- i.e. the live pass_all_hard value "
        "carries no information about whether the candidate's real masses "
        "satisfy any declared envelope, including cases the module's own "
        "locked 50-case known-answer fixture labels as genuinely PASS -- then "
        "the mission.md claim that this module's Primary KPI (hard-gate "
        "consistency at gates.pass_all_hard) reflects a real per-candidate "
        "constraint-envelope decision in the live runtime is refuted, "
        "regardless of how correct the isolated evaluate_envelope_policy "
        "function is in isolation."
    ),
    "refutation_criterion_observation_occurred": True,
    "observed_result": {
        "n_cases": diag["n_cases"],
        "direct_evaluate_envelope_policy_pass_true_count": diag["direct_evaluate_envelope_policy_pass_true_count"],
        "live_dispatch_pass_all_hard_true_count": diag["live_dispatch_pass_all_hard_true_count"],
        "live_dispatch_envelope_evaluated_true_count": diag["live_dispatch_envelope_evaluated_true_count"],
        "cases_where_live_dispatch_disagrees_with_ground_truth": diag["cases_where_live_dispatch_disagrees_with_ground_truth"],
        "source_evidence": diag["source_evidence"],
        "per_case": diag["per_case"],
        "detail": (
            "Across all 50 locked known-answer test cases (10 envelopes x 5 "
            "subgroups: NOMINAL, AT_LOWER_BOUNDARY, AT_UPPER_BOUNDARY, "
            "JUST_BELOW_LOWER, WILDLY_OUT), the direct evaluate_envelope_policy "
            "ground-truth call correctly reproduces mission.md's own cited "
            "figure of 30/50 genuinely in-envelope PASS cases (matching "
            "every fixture-declared expected_pass_all_hard label). The live "
            "FormulationCapability dispatch for ENVELOPE_GATES_ID -- the same "
            "code path amphora-engine actually calls to score a real "
            "candidate -- reports gates.pass_all_hard=false and "
            "gates.envelope_evaluated=false for all 50/50 cases without "
            "exception, including all 30 cases that are genuinely, "
            "correctly PASS. Every one of those 30 is therefore a live-path "
            "disagreement with ground truth: the module's Primary KPI as "
            "actually exposed to a real candidate carries zero discriminating "
            "information about whether the candidate satisfies its declared "
            "envelope. missing_inputs for every case names 'rights-cleared "
            "arithmetic FeatureSnapshot', but the recipe's part_A/part_B "
            "masses needed to build a TrustedArithmeticSnapshotV1 are already "
            "parsed and available inside envelope_gates() itself (used moments "
            "earlier for add_recipe_metrics) -- they are computed and then "
            "discarded rather than passed to evaluate_envelope_policy, whose "
            "call is a hardcoded (None, None, false) literal independent of "
            "the candidate. Source-grep corroborates dynamically observed "
            "behavior: hardcoded_none_none_false_call_present=true, "
            "envelope_gates_dispatch_fn_receives_features_param=false."
        ),
    },
    "positive_control": None,
    "scope_and_limits": {
        "tested_artifact": (
            "the live production dispatch path FormulationCapability::"
            "evaluate() -> envelope_gates(candidate) for ENVELOPE_GATES_ID, "
            "compiled and linked unmodified via a standalone path-dependency "
            "harness crate -- the exact untraced downstream-wiring question "
            "rust-runtime-boundary-fuzz-v1 named as out of its scope."
        ),
        "not_tested": (
            "Whether amphora-engine itself (outside this module's tree) ever "
            "constructs a real EnvelopePolicyV1 and passes it anywhere, or "
            "whether a future FeatureSnapshot-bearing caller could reach "
            "envelope_gates differently -- this fire traced only the current, "
            "actual call graph as it stands in the checked-in source. Also "
            "not re-litigated: T-03's already-refuted CPython oracle findings, "
            "the still-open KPI-register currency gap (kpi-claim-currency-v1, "
            "unretracted), and W-D-ENVGATE's fixture-nominal-vs-real-supplier-"
            "TDS sourcing gap -- none of those are re-tested here."
        ),
        "is_this_a_disclosed_limitation": (
            "No. grep across docs/mission.md for the literal explanation "
            "string embedded in envelope_gates()'s own output ('The declared "
            "envelope is not evaluated without trusted dimensioned "
            "arithmetic; no 5 mil default is used.') and for phrases like "
            "'hardcoded', 'None, None, false', 'never evaluated', or 'always "
            "abstain' returns zero matches. mission.md's prose (Decision and "
            "falsifiable hypothesis, Current benchmark result, Phase-0 "
            "readiness) describes a working per-candidate hard-gate decision "
            "without disclosing that the live dispatch never actually reaches "
            "that decision for any candidate."
        ),
        "no_promotion": True, "no_manifest_edit": True, "no_kpi_edit": True,
        "no_mission_md_edit": True, "no_scientific_readiness_flip": True,
        "remediation_needed": (
            "Wire envelope_gates(candidate) to actually construct a "
            "TrustedArithmeticSnapshotV1 from the recipe masses it already "
            "parses (part_a_mass_g/part_b_mass_g/total_mass_g) and pass a "
            "real, candidate-scoped EnvelopePolicyV1 (once a rights-cleared "
            "policy-registry source exists) to evaluate_envelope_policy, "
            "instead of the current hardcoded (None, None, false) call -- or, "
            "if no real envelope policy is available yet, disclose in "
            "mission.md that gates.pass_all_hard is a permanent constant in "
            "the live runtime rather than implying a working per-candidate "
            "decision."
        ),
    },
    "provenance": {
        "harness_crate_path": "amphora-envelope-gates/evidence/audit/live-capability-dispatch-wiring-v1/harness",
        "harness_main_rs_path": "amphora-envelope-gates/evidence/audit/live-capability-dispatch-wiring-v1/harness/src/main.rs",
        "harness_main_rs_sha256": harness_src_sha,
        "harness_cargo_toml_sha256": harness_cargo_sha,
        "real_runtime_path": "amphora-formulation-capabilities/src/lib.rs",
        "real_runtime_sha256_at_test_time": real_lib_rs_sha,
        "real_runtime_dispatch_function": "amphora_formulation_capabilities::envelope_gates (called from FormulationCapability::evaluate for ENVELOPE_GATES_ID)",
        "real_runtime_isolated_function": "amphora_formulation_capabilities::evaluate_envelope_policy",
        "fixture_path": "amphora-envelope-gates/reference/phase0-envelope-gates-known-answer.v1.json",
        "fixture_sha256": fixture_sha,
        "build_command": "cargo build --release (workspace-isolated harness crate, path dependencies)",
        "run_command": "./target/release/envgate-live-dispatch-wiring-harness",
        "rust_boundary_fuzz_receipt_path": "amphora-envelope-gates/evidence/audit/rust-runtime-boundary-fuzz-v1/rust-runtime-boundary-fuzz-receipt.v1.dsse.json",
        "rust_boundary_fuzz_receipt_sha256": rust_boundary_fuzz_receipt_sha,
        "t03_receipt_path": "amphora-envelope-gates/evidence/phase0/repairs/T-03/done/t03-adversarial-attack-receipt.v1.dsse.json",
        "t03_receipt_sha256": t03_receipt_sha,
        "kpi_currency_receipt_path": "amphora-envelope-gates/evidence/audit/kpi-claim-currency-v1/kpi-claim-currency-receipt.v1.dsse.json",
        "kpi_currency_receipt_sha256": kpi_currency_receipt_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": (
            "independent full re-run of the compiled harness binary twice "
            "(no randomness, no wall-clock reads, deterministic fixture-driven "
            "probe grid) against the unmodified FormulationCapability dispatch "
            "and evaluate_envelope_policy import"
        ),
        "seed": "n/a -- deterministic, no stochastic seed",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY ad-hoc audit receipt under evidence/audit/live-capability-dispatch-wiring-v1/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.envelope-gates-live-capability-dispatch-wiring+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payloadType": ptype, "payload": base64.standard_b64encode(body).decode(),
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}

out = ITEM / "live-capability-dispatch-wiring-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", diag_sha)
print("n_cases", diag["n_cases"])
print("direct_pass_true", diag["direct_evaluate_envelope_policy_pass_true_count"])
print("live_pass_true", diag["live_dispatch_pass_all_hard_true_count"])
print("mismatches", diag["cases_where_live_dispatch_disagrees_with_ground_truth"])
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
