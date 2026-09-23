#!/usr/bin/env python3
"""DSSE-Ed25519-sign the doe-fixture-citation-fidelity-v1 receipt for
amphora-formulation-universe. AUDIT_ONLY. Does NOT promote authority, does
NOT flip scientific_readiness, does NOT modify the manifest, KPI, fixture,
mission.md, or the live Rust engine (adds one new test file only).
"""
import base64
import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-formulation-universe"
ITEM = MOD / "evidence/audit/doe-fixture-citation-fidelity-v1"
CAP = ROOT / "amphora-formulation-capabilities"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260817T050001-3280050-bf83a9be45cd"


def sha(b):
    return hashlib.sha256(b).hexdigest()


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


canon = (ITEM / "diagnostic.canonical.json").read_bytes()
runB = (ITEM / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
mismatches = diag["parsed"]["doe_citation_fidelity_mismatches"]
assert len(mismatches) == 1
mismatch = mismatches[0]

test_file_sha = sha(
    (CAP / "tests/formulation_universe_doe_citation_fidelity_v1.rs").read_bytes()
)
harness_sha = sha((ITEM / "run_doe_citation_fidelity.py").read_bytes())
fixture_sha = sha(
    (MOD / "reference/phase0-formulation-universe-known-answer.v1.json").read_bytes()
)
lib_rs_sha = sha((CAP / "src/lib.rs").read_bytes())
mission_sha = sha((MOD / "docs/mission.md").read_bytes())
kpi_sha = sha(
    (MOD / "evidence/phase0/kpis/formulation-universe-cartesian-accounting-kpi.v1.json").read_bytes()
)

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

body_obj = {
    "schema": "amphora.formulation-universe.doe-citation-fidelity-receipt.v1",
    "study_id": "doe-fixture-citation-fidelity-v1",
    "module": "amphora-formulation-universe",
    "authority": "AUDIT_ONLY",
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "verdict": "CLAIM_REFUTED",
    "claim_under_attack": {
        "artifact_path": "amphora-formulation-universe/docs/mission.md",
        "artifact_sha256_at_test_time": mission_sha,
        "claim_text": "\"The runtime reproduces every one of the 10 published "
            "DoE examples' cardinality counts at u64 bit precision\" -- "
            "docs/mission.md, Current benchmark result section, describing "
            "the fixture at reference/phase0-formulation-universe-known-"
            "answer.v1.json (SHA-256 cb3cdb8bd40ebfeadd929ab42fed7df4596375aa"
            "1d00b24242755479676029b3, cited identically in mission.md and "
            "independently re-hashed here) as spanning \"10 Design-of-"
            "Experiments universes from Montgomery 2017 8th ed. Ch. 5-8 and "
            "Wicks/Jones/Pappas 2007 §24.5 ... cartesian totals 8-32\", "
            "which underlies the signed cartesian_product_arithmetic_"
            "correctness_rate and cartesian_identity_correctness_rate KPI "
            "metrics in evidence/phase0/kpis/formulation-universe-cartesian-"
            "accounting-kpi.v1.json (both observed=1.0, 10/10).",
        "distinguishing_note": "T-06 (2026-08-06, CLAIM_REFUTED) and "
            "kpi-claim-currency-v1 (2026-08-15, CLAIM_REFUTED) both attacked "
            "the validate_formulation_universe primitive directly (duplicate-"
            "factor-collapse, index-identity instability, and staleness of "
            "the signed KPI register after that finding). Neither examined "
            "whether the fixture's own citations to the named textbook "
            "designs are faithful, or whether the runtime can represent the "
            "design taxonomy the fixture claims to cover. This fire attacks "
            "that different target and is not a repeat.",
    },
    "attack_description": (
        "Independent Rust test file "
        "amphora-formulation-capabilities/tests/"
        "formulation_universe_doe_citation_fidelity_v1.rs (3 tests) added "
        "against the live, unmodified runtime. Test 1 (positive control): "
        "confirms a literal '2^(k-p)' numeric pattern parses correctly and "
        "the non-numeric template 'k-p' does not, proving the detector is "
        "neither blind nor indiscriminate. Test 2 (the novel probe): for "
        "each of the 10 fixture universes, re-derives the raw Cartesian "
        "product of axis cardinalities from generic (textbook-independent) "
        "combinatorics, confirms it matches the fixture's own "
        "expected_cartesian_total (baseline sanity, already covered by the "
        "existing KPI), confirms the live validate_formulation_universe "
        "returns that same product given exactly the universe's axes, and "
        "then for the one entry whose design_type names a fractional "
        "factorial, independently computes the genuine 2^(k-p) run count "
        "implied by its own citation and compares it against the fixture's "
        "expected_cartesian_total. Test 3: feeds one 5-binary-axis universe "
        "under two contradictory design_type labels and confirms the "
        "runtime's output is byte-identical either way, proving design_type "
        "is never read by validate_formulation_universe (confirmed also by "
        "direct source inspection of amphora-formulation-capabilities/src/"
        "lib.rs)."
    ),
    "directive_ref": None,
    "refutation_criterion_verbatim": (
        "If any of the 10 fixture entries' expected_cartesian_total does not "
        "equal the run count genuinely implied by its own design_type/"
        "nominal_source citation (specifically: a design_type naming a "
        "2^(k-p) fractional factorial must encode 2^(k-p) combinations, not "
        "the full 2^k), then docs/mission.md's claim that 'the runtime "
        "reproduces every one of the 10 published DoE examples' cardinality "
        "counts' is false for that entry, and the module's Phase-0 KPI "
        "register's claimed coverage of a genuine fractional-factorial "
        "design axis is unearned."
    ),
    "refutation_criterion_observation_occurred": True,
    "observed_result": {
        "fractional_entries_examined": diag["parsed"]["fractional_entries_examined"],
        "mismatches_found": len(mismatches),
        "mismatch": mismatch,
        "other_9_entries_citation_consistent": True,
        "design_type_field_read_by_runtime": False,
        "detail": (
            "Fixture entry '2^(5-1)-half-fraction-screening' cites "
            "'Montgomery 2017 8th ed. §8.2 (2^(5-1) half-fraction)' and "
            "labels design_type '2^(k-p)_fractional_factorial' with claimed "
            "(k,p)=(5,1), implying a genuine run count of 2^(5-1)=16. Its "
            "own expected_cartesian_total is 32 -- the FULL 2^5 space, not "
            "the fraction -- and its own industrial_context field admits "
            "'Enumerating the full 2^5 space; downstream design selects "
            "half-fraction.' The live runtime, given exactly this "
            "universe's axes, also returns cartesian_total=32, matching the "
            "fixture. validate_formulation_universe has no generator / "
            "defining-relation / aliasing logic and never reads a "
            "design_type field at all (test 3 proves this operationally; "
            "source inspection confirms it structurally), so it could not "
            "have validated a genuine fractional design's cardinality even "
            "if the fixture had encoded one. The other 9 entries' "
            "citations were re-checked by the same harness and are "
            "internally consistent."
        ),
    },
    "scope_and_limits": {
        "tested_artifact": "the live, unmodified Rust runtime "
            "(amphora-formulation-capabilities::validate_formulation_universe) "
            "via a new independent test file, and the phase0-formulation-"
            "universe-known-answer.v1.json fixture cited by docs/mission.md "
            "and evidence/phase0/kpis/formulation-universe-cartesian-"
            "accounting-kpi.v1.json.",
        "no_promotion": True, "no_manifest_edit": True, "no_kpi_edit": True,
        "no_mission_md_edit": True, "no_scientific_readiness_flip": True,
        "no_live_rust_engine_edit": True, "no_fixture_edit": True,
        "remediation_needed": "Human/future-fire action: either (a) correct "
            "the fixture entry's citation to describe what it actually "
            "computes (a full 2^5 factorial, not a 2^(5-1) half-fraction), "
            "replacing it with a design the runtime CAN faithfully "
            "represent, or (b) if genuine fractional-factorial cardinality "
            "accounting is required by the module's mission, extend "
            "validate_formulation_universe with generator/defining-relation "
            "logic and re-derive the fixture and KPI from a passing re-run. "
            "Neither requires manifest/human ceremony since this KPI is "
            "AUDIT_ONLY / scientific_readiness NOT_APPLICABLE.",
    },
    "provenance": {
        "test_file_path": "amphora-formulation-capabilities/tests/"
            "formulation_universe_doe_citation_fidelity_v1.rs",
        "test_file_sha256": test_file_sha,
        "harness_path": "amphora-formulation-universe/evidence/audit/"
            "doe-fixture-citation-fidelity-v1/run_doe_citation_fidelity.py",
        "harness_sha256": harness_sha,
        "lib_rs_under_test_path": "amphora-formulation-capabilities/src/lib.rs",
        "lib_rs_under_test_sha256": lib_rs_sha,
        "fixture_path": "amphora-formulation-universe/reference/"
            "phase0-formulation-universe-known-answer.v1.json",
        "fixture_sha256": fixture_sha,
        "mission_md_path": "amphora-formulation-universe/docs/mission.md",
        "mission_md_sha256": mission_sha,
        "kpi_json_path": "amphora-formulation-universe/evidence/phase0/kpis/"
            "formulation-universe-cartesian-accounting-kpi.v1.json",
        "kpi_json_sha256": kpi_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "two independent, back-to-back invocations of "
            "`cargo test --workspace --locked -p amphora-formulation-"
            "capabilities --test formulation_universe_doe_citation_"
            "fidelity_v1 -- --nocapture` against the live, unmodified "
            "runtime; parsed by run_doe_citation_fidelity.py into "
            "deterministic diagnostics (raw stdout/stderr captured "
            "separately as run1.out.txt/run1.err.txt and run2.out.txt/"
            "run2.err.txt; only wall-clock build/test timing in the raw "
            "captures differs, never load-bearing).",
        "seed": "n/a -- deterministic, no stochastic seed",
        "cargo_test_command": diag["command"],
        "test_result": diag["parsed"]["test_result_status"],
        "tests_passed": diag["parsed"]["passed"],
        "tests_failed": diag["parsed"]["failed"],
        "individual_tests": diag["parsed"]["individual_tests"],
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY ad-hoc audit receipt under "
            "evidence/audit/doe-fixture-citation-fidelity-v1/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.formulation-universe-doe-citation-fidelity+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payloadType": ptype, "payload": base64.standard_b64encode(body).decode(),
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}

out = ITEM / "doe-citation-fidelity-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", diag_sha)
print("mismatches_found", len(mismatches))
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
