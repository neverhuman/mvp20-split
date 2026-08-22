#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-optimizer-orchestrator
optimizer-ranking-boundary-feasibility-scope-v1 AUDIT_ONLY receipt.

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
BENCH = ROOT / "amphora-optimizer-orchestrator/evidence/audit/optimizer-ranking-boundary-feasibility-scope-v1"
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
profile_bytes = (ROOT / "config/kpis/molecule-demo.json").read_bytes()
profile_sha_independent = sha(profile_bytes)
assert profile_sha_independent == diag["shipped_profile_sha256"], "shipped profile sha mismatch"

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
    "schema": "amphora.optimizer-orchestrator.ranking-boundary-feasibility-scope-receipt.v1",
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
            "docs/mission.md: 'Across the portfolio, the emitted envelope, "
            "adapter, manifest, model receipt/card, portfolio policy, and "
            "Rust ranking boundary must all agree. The most restrictive "
            "policy controls.' Read against rank_candidates's own sort "
            "comparator (right.ranked.cmp(&left.ranked).then_with(|| "
            "right.feasible.cmp(&left.feasible))...), this asserts that "
            "RankedCandidate.feasible -- the one non-hardcoded field the "
            "ranking boundary's own sort actually orders candidates by -- "
            "reflects the most restrictive real gate outcome across a "
            "candidate's score envelopes, not merely the subset of modules "
            "a KPI profile happens to name in hard_constraints."
        ),
        "receipt_path": "amphora-optimizer-orchestrator/evidence/phase0/kpis/optimizer-orchestrator-authorization-kpi.v1.json",
        "mission_path": "amphora-optimizer-orchestrator/docs/mission.md",
    },
    "prior_finding_relationship": (
        "Same root cause as optimizer-constraint-path-addressing-grammar-v1's "
        "mediation_completeness=INCOMPLETE finding (2026-07-31), which noted "
        "under fixture M7 that 'with no constraint declared, a FAILED "
        "envelope is surfaced AND reported feasible' but scoped that "
        "observation to a synthetic 'display-only profile that declares NO "
        "hard constraints' and explicitly flagged it 'must not be read as "
        "an endorsement of the mutated envelope' -- i.e. deliberately left "
        "open whether this occurs against the ACTUAL shipped profile and "
        "whether it changes the ACTUAL sort order rank_candidates emits. "
        "It is also adjacent to W-T-OPT (2026-08-13) and "
        "optimizer-display-kpi-scope-boundary-v1 (2026-08-15), both of "
        "which scoped their findings to the confidentiality/display surface "
        "and explicitly stated ranking_performed/eligible_objectives/"
        "solver_invoked/usable_by_optimizer are not affected -- neither "
        "receipt examined `feasible`, the field rank_candidates's own sort "
        "actually consumes. This receipt closes that gap: it reads the "
        "REAL shipped config/kpis/molecule-demo.json from disk (sha256 "
        "recorded, not retyped) rather than a synthetic profile, and reports "
        "the REAL post-sort order rank_candidates returns, not just a "
        "resolved value."
    ),
    "attack_type": (
        "live differential probe: rank_candidates's feasible field and its "
        "own internal sort_by comparator, exercised against the shipped "
        "molecule-demo.json KPI profile with three synthetic candidates "
        "(genuine pass, genuine declared-constraint failure as positive "
        "control, and a hidden failure in a module the profile displays via "
        "display_kpis but never names in hard_constraints)"
    ),
    "method": (
        "Standalone Rust binary (runtime_probe/) linking the real "
        "amphora-core crate as a library. Reads config/kpis/molecule-demo.json "
        "from disk verbatim (sha256 cross-checked independently by this sign "
        "script) and deserializes it as the real KpiProfile type -- no "
        "retyped copy. Builds three candidate result documents differing "
        "only in amphora-molecule-design-gate.gates.pass_all_hard (the SOLE "
        "declared hard_constraint) and amphora-molecule-property.status "
        "(displayed via display_kpis, never named by any hard_constraint). "
        "Calls the real public rank_candidates(&docs, &profile) once and "
        "reports the RankedCandidate.feasible, .failed_modules, and the "
        "function's own already-sorted output order verbatim. No "
        "re-implementation of rank_candidates, authorize_optimizer_request, "
        "optimizer_envelopes, or the sort comparator."
    ),
    "non_circularity": (
        "The probe imports amphora_core's public rank_candidates and "
        "KpiProfile only. It contains no copy of the sort_by comparator, "
        "optimizer_envelopes, authorize_optimizer_request, or the "
        "hard_constraints status check. The final_sorted_order in the "
        "results below is candidates.iter() over rank_candidates's own "
        "return value, unmodified."
    ),
    "results": {
        "shipped_profile_sha256": diag["shipped_profile_sha256"],
        "shipped_profile_id": diag["shipped_profile_id"],
        "hard_constraint_modules": diag["hard_constraint_modules"],
        "display_kpi_modules_not_hard_constrained": diag["display_kpi_modules_not_hard_constrained"],
        "candidates": diag["candidates"],
        "final_sorted_order": diag["final_sorted_order"],
        "declared_mechanism_works_as_positive_control": diag["declared_mechanism_works_as_positive_control"],
        "hidden_fail_ranks_at_or_above_declared_fail": diag["hidden_fail_ranks_at_or_above_declared_fail"],
        "hidden_fail_feasible_matches_genuine_pass": diag["hidden_fail_feasible_matches_genuine_pass"],
        "hidden_fail_visible_via_failed_modules_only": diag["hidden_fail_visible_via_failed_modules_only"],
        "divergence_observed": diag["divergence_observed"],
    },
    "refutation_criterion": (
        "The claim under attack (the Rust ranking boundary's feasible field "
        "reflects the most restrictive real gate outcome, and the shipped "
        "profile keeps `the most restrictive policy controls`) is REFUTED if, "
        "against the ACTUAL shipped config/kpis/molecule-demo.json profile: "
        "(a) a candidate whose declared hard_constraint module genuinely "
        "fails is correctly demoted (feasible=false) -- the positive "
        "control, proving the mechanism is capable of demoting when it is "
        "wired up -- AND (b) a second candidate whose declared "
        "hard_constraint module passes but whose amphora-molecule-property "
        "envelope (displayed via display_kpis, never named by any "
        "hard_constraint) carries status='FAILED_GATES' nonetheless receives "
        "feasible=true identical to a fully-passing candidate, AND sorts at "
        "or above the genuinely-failing candidate in rank_candidates's own "
        "returned order, AND the failure is visible only through the "
        "separate failed_modules counter that the sort ignores. It SURVIVES "
        "if the hidden-failure candidate is demoted or sorts below the "
        "declared failure."
    ),
    "observed_result": (
        "All four refutation conditions were observed live against the real "
        "shipped profile (sha256 " + diag["shipped_profile_sha256"] + ", "
        "profile_id '" + diag["shipped_profile_id"] + "'), whose single "
        "hard_constraint names only amphora-molecule-design-gate while "
        "display_kpis also names amphora-molecule-property and "
        "amphora-molecule-novelty -- neither of the latter two is ever named "
        "by a hard_constraint in this shipped profile. Candidate B (genuine, "
        "declared design-gate failure) is correctly demoted: feasible=false "
        "(positive control confirms the mechanism works when wired up). "
        "Candidate C (design-gate passes; amphora-molecule-property.status="
        "FAILED_GATES, undeclared) receives feasible=true, identical to "
        "fully-passing candidate A, and rank_candidates's own sort places C "
        "FIRST in the final order -- strictly ahead of both A and the "
        "correctly-demoted B -- because feasible ties with A (both true) and "
        "the candidate_id tiebreak favors C. C.failed_modules=1 correctly "
        "counts the property-module failure, proving the runtime does have "
        "the information; the sort simply never consults it. This falsifies "
        "'the most restrictive policy controls' as a description of the "
        "Rust ranking boundary against the shipped profile: the ranking "
        "boundary's own sort output is controlled only by whichever module "
        "a profile author happens to name in hard_constraints, not by the "
        "most restrictive real gate outcome across the candidate's score "
        "envelopes."
    ),
    "claim_verdict": "CLAIM_REFUTED",
    "does_not_close": [
        "Does not show ranking_performed, eligible_objectives, solver_invoked, "
        "usable_by_optimizer, or authority_upgrade can be flipped by this "
        "path; those remain hardcoded false/0 in rank_candidates regardless "
        "of feasible or display_kpis content, so this is a candidate-"
        "ordering/display-priority finding, not a ranking- or "
        "solver-AUTHORITY escalation under the module's own AUDIT_ONLY "
        "solver_use_ceiling.",
        "Does not demonstrate that any real (non-synthetic) candidate has "
        "ever actually reached rank_candidates with a FAILED_GATES "
        "amphora-molecule-property envelope in production; the exposure "
        "demonstrated here is that the shipped profile's declared scope "
        "(1 hard_constraint module vs 3 display_kpi modules) makes that "
        "outcome reachable by construction, not that it has occurred.",
        "Does not repair the gap or propose which of authorize_optimizer_"
        "request's checks should be widened (declare hard_constraints for "
        "every display_kpi module vs. change rank_candidates to fold "
        "failed_modules into feasible vs. document the scope explicitly).",
        "Does not modify docs/mission.md, the KPI receipt, the master "
        "manifest, or any locked dataset.",
    ],
    "provenance": {
        "runtime_probe_main_rs_sha256": main_rs_sha,
        "amphora_core_lib_rs_sha256": core_lib_sha,
        "shipped_profile_sha256_independent_check": profile_sha_independent,
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
ptype = "application/vnd.amphora.optimizer-orchestrator-ranking-boundary-feasibility-scope+json"
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
out = BENCH / "optimizer-ranking-boundary-feasibility-scope-receipt.v1.dsse.json"
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
