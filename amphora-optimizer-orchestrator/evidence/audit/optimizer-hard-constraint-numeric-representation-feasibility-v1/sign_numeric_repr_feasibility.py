#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-optimizer-orchestrator
optimizer-hard-constraint-numeric-representation-feasibility-v1 AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest, module-
manifest.json, any locked dataset, or a signed Phase-0 KPI. Derived
key_id cross-checked vs the pinned Phase-0 trust store."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-optimizer-orchestrator/evidence/audit/optimizer-hard-constraint-numeric-representation-feasibility-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


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


canon = (BENCH / "runtime_probe/diagnostic.canonical.json").read_bytes()
runB = (BENCH / "runtime_probe/diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["divergence_observed"] is True, "expected divergence not observed"
main_rs_sha = sha((BENCH / "runtime_probe/src/main.rs").read_bytes())
core_lib_sha = sha((ROOT / "amphora-core/src/lib.rs").read_bytes())
prior_study_receipt = ROOT / "amphora-optimizer-orchestrator/evidence/audit/optimizer-authorization-numeric-comparison-conformance-v1/optimizer-authorization-numeric-comparison-conformance-receipt.v1.dsse.json"
prior_study_sha = sha(prior_study_receipt.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.optimizer-orchestrator.hard-constraint-numeric-representation-feasibility-receipt.v1",
    "module": "amphora-optimizer-orchestrator",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_rust_runtime": False,
    "directive_path": "none",
    "directive_sha256": "",
    "directive_obligation": "none",
    "claim_tested": {
        "claim_text": (
            "docs/mission.md 'Honest current state': the deterministic "
            "authorize_optimizer_request gate 'reproduces the deny-by-default "
            "authorization boundary at 100% correctness', and the Known "
            "Contradictions section's 'the emitted envelope, adapter, "
            "manifest, model receipt/card, portfolio policy, and Rust "
            "ranking boundary must all agree. The most restrictive policy "
            "controls.' Read against the ONE non-hardcoded field "
            "rank_candidates's own sort comparator consumes -- "
            "RankedCandidate.feasible -- this asserts feasible reflects the "
            "declared hard_constraint's real semantics (e.g. that a "
            "'!= 110.0' constraint denies any candidate whose gate value "
            "denotes the real number 110), independent of how that number "
            "happens to be spelled in the envelope's own JSON."
        ),
        "receipt_path": "amphora-optimizer-orchestrator/evidence/phase0/kpis/optimizer-orchestrator-authorization-kpi.v1.json",
        "mission_path": "amphora-optimizer-orchestrator/docs/mission.md",
    },
    "prior_finding_relationship": (
        "Direct escalation of optimizer-authorization-numeric-comparison-"
        "conformance-v1's own declared does_not_close scope (sha256 " + prior_study_sha + "). "
        "That study measured amphora_core::comparison_passes in isolation via "
        "authorize_optimizer_request, found finding F2 "
        "(rfc8259_value_equality_representation_invariance) REFUTED with 48 "
        "equality divergences vs exact RFC 8259 value semantics on a locked "
        "36x36x6 corpus, and explicitly judged this 'a CONSTRAINT-SCREEN "
        "semantics defect, not an authority escalation' because "
        "hard_constraints_passed/ranking_performed/etc. are hardcoded on "
        "Ok(_) regardless of which branch of comparison_passes fired -- i.e. "
        "it never traced the defect to the one field that is NOT hardcoded, "
        "RankedCandidate.feasible, nor called rank_candidates at all. This "
        "receipt closes exactly that gap with a live rank_candidates() call: "
        "it shows the F2 representation-variance defect flips the real "
        "feasible bit rank_candidates's own sort_by comparator consumes, "
        "for a candidate whose gate value denotes the identical excluded "
        "real number as a correctly-denied sibling candidate. Independently, "
        "this receipt is also adjacent to optimizer-ranking-boundary-"
        "feasibility-scope-v1 (2026-08-17, REFUTED, ledger-logged), which "
        "showed feasible ignores undeclared-module failures; this receipt "
        "shows a SEPARATE, distinct defect: feasible can be wrong even "
        "WITHIN the one module a profile author correctly declares as a "
        "hard_constraint, because the comparison operator itself is not "
        "representation-invariant."
    ),
    "attack_type": (
        "live differential probe: rank_candidates's feasible field over a "
        "synthetic-but-schema-valid KpiProfile (one numeric '!=' hard "
        "constraint, a documented capability of HardConstraint.operator and "
        ".expected) and three synthetic SCORED candidates whose sole "
        "declared-constraint gate value is spelled as JSON int 110, JSON "
        "float 110.0 (matching the constraint's own literal form), and JSON "
        "int 200 (genuinely different) respectively"
    ),
    "method": (
        "Standalone Rust binary (runtime_probe/) linking the real "
        "amphora-core crate as a library. Constructs the KpiProfile and "
        "three candidate result documents entirely from inline JSON literals "
        "(no disk I/O, so the two-replay gate is trivially byte-stable), "
        "deserializes the profile as the real KpiProfile/HardConstraint "
        "types, and calls the real public rank_candidates(&docs, &profile) "
        "once. Reports RankedCandidate.feasible, .failed_modules, and the "
        "function's own already-sorted output order verbatim."
    ),
    "non_circularity": (
        "The probe imports amphora_core's public rank_candidates, KpiProfile, "
        "and HardConstraint only. It contains no copy of comparison_passes, "
        "the sort_by comparator, optimizer_envelopes, or "
        "authorize_optimizer_request. final_sorted_order is candidates.iter() "
        "over rank_candidates's own return value, unmodified."
    ),
    "results": {
        "hard_constraint": diag["hard_constraint"],
        "candidates": diag["candidates"],
        "final_sorted_order": diag["final_sorted_order"],
        "representation_flips_feasible_for_identical_real_number": diag["representation_flips_feasible_for_identical_real_number"],
        "defect_wrongly_admits_excluded_value_as_feasible": diag["defect_wrongly_admits_excluded_value_as_feasible"],
        "true_pass_control_works": diag["true_pass_control_works"],
        "divergence_observed": diag["divergence_observed"],
    },
    "refutation_criterion": (
        "The claim under attack (RankedCandidate.feasible, the field "
        "rank_candidates's own sort actually consumes, correctly implements "
        "the declared hard_constraint's real-number semantics -- 'the most "
        "restrictive policy controls') is REFUTED if, against a real live "
        "rank_candidates() call with a schema-valid '!=110.0' hard "
        "constraint: (a) a control candidate whose gate value is spelled as "
        "the JSON float 110.0 (the same literal form as the constraint's "
        "own expected value) is correctly denied, feasible=false -- proving "
        "the mechanism CAN deny when representations match -- AND (b) a "
        "second candidate whose gate value denotes the SAME real number 110 "
        "but is spelled as the JSON integer 110 is instead admitted, "
        "feasible=true, identical to a genuinely-different-value control "
        "candidate (200) -- AND (c) the wrongly-admitted candidate sorts at "
        "or above the correctly-denied one in rank_candidates's own returned "
        "order. It SURVIVES if both representations are denied identically "
        "(true representation invariance) or if only the mathematically-"
        "excluded value's spelling that matches the constraint is denied and "
        "the other is also correctly denied by some other live mechanism."
    ),
    "observed_result": (
        "All three refutation conditions were observed live. Against the "
        "synthetic profile declaring hard_constraint "
        "'flagged_batch_code != 110.0' on amphora-molecule-property: "
        "candidate E (gate value spelled '110.0', JSON float, matching the "
        "constraint's own literal form) is correctly denied, feasible=false "
        "(positive control: the mechanism DOES deny when representations "
        "match). Candidate D (gate value spelled '110', JSON int -- the "
        "IDENTICAL real number 110) is instead admitted, feasible=true, "
        "byte-for-byte identical outcome to candidate F (gate value 200, "
        "genuinely different) -- proving the admission is not a coincidence "
        "of D's value but a direct artifact of its JSON literal spelling. "
        "In rank_candidates's own returned sort order, D and F both rank "
        "above E: [D(feasible=true), F(feasible=true), E(feasible=false)]. "
        "This falsifies 'the most restrictive policy controls' and the "
        "deny-by-default authorization boundary's claimed '100% correctness' "
        "as a description of feasible: a candidate correctly identified and "
        "denied under one JSON spelling of the exact same real number is "
        "silently admitted, and outranks that correctly-denied sibling, "
        "purely because a policy author or upstream module happened to emit "
        "the excluded gate value as an integer literal rather than a float "
        "literal -- a distinction RFC 8259 (the request/envelope wire "
        "format's own governing spec) does not make."
    ),
    "claim_verdict": "CLAIM_REFUTED",
    "does_not_close": [
        "Does not show ranking_performed, eligible_objectives, "
        "solver_invoked, usable_by_optimizer, or authority_upgrade can be "
        "flipped by this path; those remain hardcoded false/0 in "
        "rank_candidates regardless of feasible, so this is a "
        "candidate-ordering/feasibility-display defect, not a ranking- or "
        "solver-AUTHORITY escalation under the module's own AUDIT_ONLY "
        "solver_use_ceiling.",
        "Does not demonstrate that any shipped production KPI profile "
        "currently declares a numeric '==' or '!=' hard_constraint (the "
        "single shipped profile, config/kpis/molecule-demo.json, uses "
        "operator '==' against a boolean, which is representation-safe); "
        "the exposure demonstrated here is that the runtime and the "
        "HardConstraint schema make a numeric '!=' constraint reachable and "
        "silently wrong by construction, not that a currently-shipped "
        "profile already exploits it.",
        "Does not repair the defect or choose between the prior study's "
        "H01/H02/H03/H05 proposed hardeners (normalize numeric comparison to "
        "as_f64, canonicalize numeric admission at the front door, or "
        "restrict CANDIDATE-sourced constraints to the four ordering "
        "operators pending a fix).",
        "Does not modify docs/mission.md, the KPI receipt, the master "
        "manifest, or any locked dataset.",
    ],
    "provenance": {
        "runtime_probe_main_rs_sha256": main_rs_sha,
        "amphora_core_lib_rs_sha256": core_lib_sha,
        "prior_study_receipt_path": "amphora-optimizer-orchestrator/evidence/audit/optimizer-authorization-numeric-comparison-conformance-v1/optimizer-authorization-numeric-comparison-conformance-receipt.v1.dsse.json",
        "prior_study_receipt_sha256_independent_check": prior_study_sha,
        "workspace_membership": "standalone binary, [workspace] with no members -- not part of the mvp20-split cargo workspace",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
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
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.optimizer-orchestrator-hard-constraint-numeric-representation-feasibility+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}
out = BENCH / "optimizer-hard-constraint-numeric-representation-feasibility-receipt.v1.dsse.json"
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
