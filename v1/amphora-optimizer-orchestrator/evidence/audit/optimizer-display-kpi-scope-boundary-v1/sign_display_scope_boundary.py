#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-optimizer-orchestrator
optimizer-display-kpi-scope-boundary-v1 AUDIT_ONLY receipt.

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
BENCH = ROOT / "amphora-optimizer-orchestrator/evidence/audit/optimizer-display-kpi-scope-boundary-v1"
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
assert diag["both_cases_diverge"] is True, "expected divergence not observed"
main_rs_sha = sha((BENCH / "runtime_probe/src/main.rs").read_bytes())
core_lib_sha = sha((ROOT / "amphora-core/src/lib.rs").read_bytes())

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
    "schema": "amphora.optimizer-orchestrator.display-kpi-scope-boundary-receipt.v1",
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
            "docs/mission.md: 'All 29 registered modules of "
            "`quarantined_optimizer_policy` are in scope' and 'every one of "
            "the 6 module-specific attack axes ... is exercised end-to-end "
            "by 26 dedicated fail-closed probes', combined with the "
            "reference-monitor 'complete mediation' framing in evidence/"
            "phase0/kpis/optimizer-orchestrator-authorization-kpi.v1.json "
            "(theory field) -- read together, these assert that "
            "authorize_optimizer_request (the sole cited reference-monitor "
            "entry point) is the boundary through which the registered-"
            "module/SCORED-status scope of this module's outputs is "
            "enforced."
        ),
        "receipt_path": "amphora-optimizer-orchestrator/evidence/phase0/kpis/optimizer-orchestrator-authorization-kpi.v1.json",
        "mission_path": "amphora-optimizer-orchestrator/docs/mission.md",
    },
    "prior_finding_relationship": (
        "Escalates W-T-OPT (2026-08-13, evidence/phase0/repairs/W-T-OPT/done/), "
        "which found the display_kpis path (site B) reads the same protected "
        "object class as authorize_optimizer_request (site A) without ever "
        "calling site A, but scoped its demonstrated example to a REGISTERED "
        "module and explicitly declined to test whether the leak crosses the "
        "registered_modules allowlist itself, filing that as proposed_followup "
        "PF-1 rather than testing it. This receipt tests exactly that gap "
        "live: an envelope whose module_id is NOT one of the 29 registered "
        "modules at all, plus a second case where the module IS registered "
        "but status != SCORED (FAILED_GATES). Neither case was covered by "
        "W-T-OPT's cited example (amphora-molecule-property, SCORED) or by "
        "optimizer-constraint-path-addressing-grammar-v1 (which is a path-"
        "grammar/injectivity study on the constraint side, not a module-"
        "registration or status-boundary study on the display side)."
    ),
    "attack_type": "live differential probe: rank_candidates display_kpis surface vs authorize_optimizer_request reference monitor, over module-registration and envelope-status boundaries",
    "method": (
        "Standalone Rust binary (runtime_probe/) linking the real amphora-core "
        "crate as a library, calling the two real public entry points "
        "authorize_optimizer_request (site A) and rank_candidates (site B) on "
        "the identical synthetic score-envelope data, in two cases: (1) an "
        "envelope whose module_id is outside all 29 OPTIMIZER_MODULES; (2) an "
        "envelope whose module_id IS registered but whose status is "
        "'FAILED_GATES' rather than 'SCORED'. In both cases the envelope "
        "carries a unique marker string in objective_values.secret_metric, "
        "and a display_kpis profile entry names exactly that module_id/path. "
        "No re-implementation of either resolver: site A is called directly "
        "on the OptimizerEnvelopeV1 struct; site B's resolved value is "
        "reported verbatim from the live RankedCandidate.display_kpis output."
    ),
    "non_circularity": (
        "The Rust probe imports amphora_core's public functions and structs "
        "only (authorize_optimizer_request, rank_candidates, KpiProfile, "
        "OptimizerEnvelopeV1, OptimizerAuthorizationRequestV1, "
        "quarantined_optimizer_policy); it contains no copy or "
        "reimplementation of module_envelope, envelope_value, or the "
        "authorize_optimizer_request guard-clause logic. The divergence is "
        "observed, not asserted from source reading alone."
    ),
    "results": {
        "both_cases_diverge": diag["both_cases_diverge"],
        "registered_modules_count": diag["registered_modules_count"],
        "cases": diag["cases"],
    },
    "refutation_criterion": (
        "The claim under attack (module scope is bounded to the 29 "
        "registered modules and to SCORED envelopes, with authorize_"
        "optimizer_request as the enforcing boundary) is REFUTED if any "
        "case shows site A (authorize_optimizer_request) rejecting an "
        "envelope while site B (rank_candidates' display_kpis) discloses "
        "that same envelope's marker value verbatim in its output -- i.e. "
        "'divergence_A_rejects_B_discloses' == true for a case whose module "
        "is either unregistered or non-SCORED. It SURVIVES if both sites "
        "agree (either both accept or both reject) in every case tested."
    ),
    "observed_result": (
        "Both cases diverge. Case 1 (module_id entirely outside the 29 "
        "registered OPTIMIZER_MODULES, status SCORED): site A rejects with "
        "'optimizer envelope module is unknown or duplicated'; site B's "
        "rank_candidates display_kpis output discloses the marker "
        "'UNREGISTERED_LEAK_9f3a1c' verbatim. Case 2 (module_id IS one of "
        "the 29, status FAILED_GATES not SCORED): site A rejects with "
        "'optimizer envelope attempts authority, score, solver, or lock "
        "escalation'; site B discloses 'FAILEDGATES_LEAK_7c1d44' verbatim. "
        "In both cases site_b_ranking_performed=false and "
        "site_b_eligible_objectives=0, so ranking/solver authority itself is "
        "NOT escalated -- the divergence is a scope/confidentiality boundary "
        "bypass, not a ranking-authority bypass. This means "
        "'all 29 registered modules ... are in scope' is false as a "
        "description of the display_kpis output surface: an envelope for a "
        "module never named anywhere in the 29-module registry can still "
        "have its objective_values surfaced through this module's own "
        "RankedCandidate output, and a module whose gates already failed "
        "(non-SCORED) can have its objective_values surfaced as if scoring "
        "had succeeded."
    ),
    "claim_verdict": "CLAIM_REFUTED",
    "does_not_close": [
        "Does not demonstrate that any shipped KPI profile (config/kpis/molecule-demo.json) currently declares a display_kpis entry naming an unregistered module or a non-SCORED-status module; the exposure is contract-level (the runtime accepts and discloses it), matching the same caveat already recorded by the sibling optimizer-constraint-path-addressing-grammar-v1 receipt for its own grammar finding.",
        "Does not show ranking_performed, eligible_objectives, solver_invoked, or usable_by_optimizer can be flipped by this path; those remain hardcoded false/0 in rank_candidates regardless of display_kpis content, so this is a confidentiality/scope-boundary finding, not a ranking- or solver-authority escalation.",
        "Does not repair the gap; PF-1 from W-T-OPT (2026-08-13) already proposed two alternative repair shapes (dedicated mediated read function with its own attack axis, or explicit out-of-scope documentation) and this receipt does not choose between them.",
        "Does not modify docs/mission.md, the KPI receipt, the master manifest, or any locked dataset.",
    ],
    "provenance": {
        "runtime_probe_main_rs_sha256": main_rs_sha,
        "amphora_core_lib_rs_sha256": core_lib_sha,
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
ptype = "application/vnd.amphora.optimizer-orchestrator-display-kpi-scope-boundary+json"
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
out = BENCH / "optimizer-display-kpi-scope-boundary-receipt.v1.dsse.json"
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
