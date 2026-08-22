#!/usr/bin/env python3
"""DSSE-Ed25519-sign the T-03 first-adversarial-attack receipt for
amphora-envelope-gates. AUDIT_ONLY. Does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the manifest, KPI, or benchmark-lock.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
ITEM = MOD / "evidence/phase0/repairs/T-03"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_PATH = "docs/directives/2026-08-05-closing-the-open-portfolio.md"
DIRECTIVE_SHA256 = "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d"
DIRECTIVE_OBLIGATION = "T2-03"
REFUTATION_CRITERION = "Any invalid or boundary-gaming input yields a PASS or a non-abstaining scalar."


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


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

harness_sha = sha((WORK / "t03_fuzz_grid.py").read_bytes())
oracle_sha = sha((MOD / "benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py").read_bytes())
kpi_sha = sha((MOD / "evidence/phase0/kpis/envelope-gates-constraint-envelope-kpi.v1.json").read_bytes())
fixture_sha = sha((MOD / "reference/phase0-envelope-gates-known-answer.v1.json").read_bytes())
mission_sha = sha((MOD / "docs/mission.md").read_bytes())

slipped = [r for r in diag["results"] if r["slipped_through"]]
nonabstain = [r for r in diag["results"] if r["non_abstaining_scalar_on_invalid_input"]]

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

body_obj = {
    "schema": "amphora.envelope-gates.t03-first-adversarial-attack-receipt.v1",
    "study_id": "T-03-metamorphic-boundary-fuzz",
    "module": "amphora-envelope-gates",
    "authority": "AUDIT_ONLY",
    "campaign_item_id": "T-03",
    "verdict": "CLAIM_REFUTED",
    "claim_under_attack": {
        "receipt_path": "amphora-envelope-gates/docs/mission.md",
        "claim_text": "amphora-envelope-gates has never received an adversarial verdict; its "
                       "constructive SIGNED_RECEIPT-era receipts are untested claims.",
        "specific_target": "The 4 fail-closed metrics in "
                            "evidence/phase0/kpis/envelope-gates-constraint-envelope-kpi.v1.json "
                            "that carry a 'probe_sample_size' (not a real fixture 'sample_size'): "
                            "envelope_policy_substitution_fail_closed_rate (7), "
                            "trusted_feature_substitution_fail_closed_rate (5), "
                            "envelope_bound_inversion_fail_closed_rate (3), "
                            "candidate_gate_pass_injection_ignore_rate (2) -- all claimed "
                            "observed=1.0/passed=true with zero of those specific probes "
                            "(e.g. the KPI's own claimed 'lower=NaN, upper=Infinity ... All "
                            "return Err' case) ever executed by the module's own oracle before "
                            "this fire.",
    },
    "attack_description": (
        "Metamorphic boundary-fuzz grid: 4 boundary classes (inclusive-bound off-by-one at "
        "1 ULP, inverted envelope min>max, NaN/Inf bounds, unit-scale substitution) x 4 "
        "fail-closed metrics = 16 primary grid cells, plus 1 KPI-claim-verification cell and "
        "1 static source-inspection cell (18 total), executed directly against the real, "
        "unmodified evaluate_gate() function imported (not reimplemented) from "
        "benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py. Also executes the "
        "founder directive's excursion-invariance / value-free-bypass probe: attach +/-inf "
        "bounds to a real, registered policy and observe whether the resulting margin becomes "
        "value-free (PASS regardless of candidate magnitude)."
    ),
    "directive_path": DIRECTIVE_PATH,
    "directive_sha256": DIRECTIVE_SHA256,
    "directive_obligation": DIRECTIVE_OBLIGATION,
    "refutation_criterion_verbatim": REFUTATION_CRITERION,
    "refutation_criterion_observation_occurred": True,
    "refutation_criterion_discussion": (
        "The observation named by the founder's pre-committed criterion DID occur, 6 times "
        "out of 18 cells: 5 cells returned verdict=PASS on an invalid or boundary-gaming input "
        "(a forged/unregistered policy, or +/-inf bounds on either a forged or the REAL "
        "registered TETA policy, or a NaN-corrupted trusted feature value silently masked by "
        "Python min()'s non-total order over NaN), and 1 cell returned a non-abstaining scalar "
        "(binding_margin=NaN) on an invalid NaN-bound input instead of abstaining (REJECT). "
        "This directly falsifies the done_criterion's 'hard-constraint fail-closed on all "
        "invalid inputs' and 'abstention on undecidable cases, never silent pass' requirements."
    ),
    "founder_done_criteria_verbatim": (
        "Hard-constraint fail-closed on all invalid inputs; inclusive margins enforced "
        "deterministically; abstention on undecidable cases, never silent pass."
    ),
    "founder_done_criteria_met": False,
    "n_grid_cells": diag["n_cells"],
    "n_slipped_through": diag["n_slipped_through"],
    "n_non_abstaining_scalar_on_invalid_input": diag["n_non_abstaining_scalar_on_invalid_input"],
    "slipped_cases_quoted_verbatim": slipped,
    "non_abstaining_scalar_cases_quoted_verbatim": nonabstain,
    "full_per_case_result_table": diag["results"],
    "positive_control": diag["positive_control"],
    "root_causes": [
        "evaluate_gate() never checks math.isfinite() on lower_inclusive/upper_inclusive: "
        "'float(lo) > float(hi)' is False whenever either bound is NaN or when both are "
        "infinite with the same sign ordering, so -inf/+inf bounds are accepted as a "
        "legitimate, wide-open envelope (value-free bypass) rather than rejected as "
        "boundary-gaming input.",
        "evaluate_gate() never checks math.isfinite() on the candidate feature value either: "
        "a NaN feature value produces a NaN per-constraint margin that Python's min() (not a "
        "total order over NaN) can silently drop from the overall binding-margin reduction "
        "depending on iteration order, producing verdict=PASS with a real, finite (correct-"
        "looking) margin that hides the corrupted constraint entirely.",
        "evaluate_gate() implements NO policy_id / registry / provenance check between a "
        "supplied 'policy' dict and any real, approved envelope -- the KPI's own stated "
        "'policy_trust_rule' (policy.fixture_only AND allow_synthetic_fixture flags) is "
        "documented in the KPI but never implemented or checked by the oracle that KPI cites "
        "as its evidence. Any object shaped {authoritative != True, constraints: [...]} is "
        "accepted regardless of provenance.",
        "The KPI's 4 'probe_sample_size' fail-closed metrics (7/5/3/2 probes) assert specific "
        "named probes (e.g. NaN lower bound, Infinity upper bound) that this fire found were "
        "never actually executed by the only oracle code that exists in this module -- the "
        "oracle's own G5 tamper battery runs only 1-2 probes per axis, not the 7/5/3/2 the KPI "
        "claims.",
    ],
    "scope_and_limits": {
        "tested_artifact": "the CPython AUDIT_ONLY oracle (evaluate_gate() in "
                           "run_envelope_gates.py), which is an independent, non-runtime "
                           "re-derivation -- NOT the shipped Rust runtime "
                           "(amphora-formulation-capabilities). This receipt makes no claim "
                           "about whether the Rust runtime's evaluate_envelope_policy shares "
                           "these defects; it establishes only that the CPython oracle this "
                           "module signs receipts against does, and that the KPI's fail-closed "
                           "floor claims for that oracle were unsized/unexecuted before this "
                           "fire.",
        "no_promotion": True, "no_manifest_edit": True, "no_kpi_edit": True,
        "no_scientific_readiness_flip": True,
    },
    "provenance": {
        "harness_path": "amphora-envelope-gates/evidence/phase0/repairs/T-03/work/t03_fuzz_grid.py",
        "harness_sha256": harness_sha,
        "oracle_under_test_path": "amphora-envelope-gates/benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py",
        "oracle_under_test_sha256": oracle_sha,
        "kpi_examined_path": "amphora-envelope-gates/evidence/phase0/kpis/envelope-gates-constraint-envelope-kpi.v1.json",
        "kpi_examined_sha256": kpi_sha,
        "known_answer_fixture_sha256": fixture_sha,
        "mission_md_sha256_at_attack_time": mission_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "independent full re-run of t03_fuzz_grid.py (no randomness, no "
                         "wall-clock reads) against the unmodified evaluate_gate() import",
        "seed": "n/a -- deterministic arithmetic grid, no stochastic seed",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-item receipt under evidence/phase0/repairs/T-03/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.envelope-gates-t03-adversarial-attack+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payloadType": ptype, "payload": base64.standard_b64encode(body).decode(),
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}

DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "t03-adversarial-attack-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", diag_sha)
print("n_slipped_through", diag["n_slipped_through"])
print("n_non_abstaining_scalar", diag["n_non_abstaining_scalar_on_invalid_input"])
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
