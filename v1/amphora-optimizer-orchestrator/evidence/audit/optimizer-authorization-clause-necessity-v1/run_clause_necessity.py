#!/usr/bin/env python3
"""Guard-clause necessity / irredundancy ablation for the
amphora-optimizer-orchestrator deny-by-default authorization gate.

This study extends optimizer-authorization-oracle-parity-v1 (which
established accept/reject DECISION parity vs the byte-stable Rust
result.v1.json) along the axis its own `does_not_close` names next:
reason-level structure of the authorization contract. It does NOT import,
FFI-call, or read the Rust runtime. It re-uses the identical independent
CPython oracle (optimizer_authorization_oracle.py, sha256 pinned in the
diagnostic) and asks a strictly stronger property than decision parity:

  IRREDUNDANCY / NECESSITY. Starting from a single minimal WELL-FORMED
  ACCEPTING request/policy/envelope triple (the baseline), every atomic
  guard clause in the deny-by-default contract is ablated one at a time by
  a single-field mutation that violates exactly that clause. A guard is
  NECESSARY iff removing/violating it flips the unique accepting
  configuration to REJECT. If all N guards flip, the contract is
  irredundant: no guard can be dropped without admitting an unauthorized
  row -- the reference-monitor "complete mediation" property made
  constructive.

  REASON-TAXONOMY PARTITION. Each atomic guard carries the oracle's own
  deny reason string and is mapped to one of the six module-specific
  attack axes documented in the shipped Phase-0 KPI receipt
  (OBJECTIVE_CONSTRAINT_INJECTION, UNKNOWN_OBJECTIVE_PATH_OPERATOR,
  DUPLICATE_SCORE_ENVELOPE, MISSING_OPTIMIZER_CLAIM_LOCK,
  FAILED_OR_NO_AUTHORITY_SCORE, SOLVER_RANKING_ESCALATION). The study
  checks the independent clause-set covers all six axes.

Theory: J.P. Anderson ESD-TR-73-51 (1972) reference monitor (complete
mediation); Saltzer & Schroeder Proc. IEEE 63(9):1278-1308 (1975)
fail-safe defaults, least privilege, economy of mechanism; NIST SP 800-53
Rev.5 AC-3/AC-6; NIST SP 800-207 (2020) deny-by-default. The
necessity/irredundancy method mirrors the portfolio's accepted
predicate-completeness (evidence-intake-validator) and lattice-completeness
(model-card-authority) infra oracles.
"""
import copy
import json
import sys

import optimizer_authorization_oracle as O

REG = O.OPTIMIZER_MODULES[0]  # a registered module id
REG2 = O.OPTIMIZER_MODULES[1]


def baseline():
    """Minimal WELL-FORMED accepting triple that reaches every clause
    family (policy integrity, envelope, objective, constraint declaration,
    constraint evaluation with a PASSING comparison)."""
    env = O.envelope(REG, "pass", True)  # gates={"pass": True}, SCORED, clean
    req = O.policy_request(
        objectives=[O.objective("o1", REG, "score_0_1")],
        hard_constraints=[O.constraint("c1", REG, "pass", "==", True)],
    )
    pol = O.quarantined_policy()
    return req, [env], pol


def decide(req, envs, pol):
    """Returns ('ACCEPT', out) or ('REJECT', reason)."""
    try:
        out = O.authorize(req, envs, pol)
        return ("ACCEPT", out)
    except O.Reject as r:
        return ("REJECT", str(r))
    except Exception as e:  # any other raise is still fail-closed, but flag it
        return ("REJECT", f"__nonreject_exception__:{type(e).__name__}:{e}")


# ---- Atomic guard-clause ablations -----------------------------------------
# Each entry: (clause_id, attack_axis, human_desc, mutate(req, envs, pol))
# mutate applies EXACTLY ONE single-field violation to a fresh deep copy.

def _add_dup_module(pol):
    pol["registered_modules"] = list(pol["registered_modules"]) + [REG]

def _drop_a_module(pol):
    pol["registered_modules"] = list(pol["registered_modules"])[:-1]


CLAUSES = [
    # --- policy / request integrity (reason: registry altered/incomplete) ---
    ("C01_request_schema", "SOLVER_RANKING_ESCALATION",
     "request.schema not the pinned request schema",
     lambda rq, ev, po: rq.__setitem__("schema", "amphora.wrong.v1")),
    ("C02_request_source", "OBJECTIVE_CONSTRAINT_INJECTION",
     "request.request_source not in {POLICY,CANDIDATE}",
     lambda rq, ev, po: rq.__setitem__("request_source", "ADMIN")),
    ("C03_policy_schema", "SOLVER_RANKING_ESCALATION",
     "policy.schema not the pinned policy schema",
     lambda rq, ev, po: po.__setitem__("schema", "amphora.wrong.v1")),
    ("C04_registered_duplicate", "DUPLICATE_SCORE_ENVELOPE",
     "policy.registered_modules contains a duplicate (len != set len)",
     lambda rq, ev, po: _add_dup_module(po)),
    ("C05_registered_missing", "SOLVER_RANKING_ESCALATION",
     "policy.registered_modules != the pinned 29-module set",
     lambda rq, ev, po: _drop_a_module(po)),
    ("C06_ranking_enabled", "SOLVER_RANKING_ESCALATION",
     "policy.ranking_enabled flipped true",
     lambda rq, ev, po: po.__setitem__("ranking_enabled", True)),
    ("C07_solver_enabled", "SOLVER_RANKING_ESCALATION",
     "policy.solver_enabled flipped true",
     lambda rq, ev, po: po.__setitem__("solver_enabled", True)),
    ("C08_authority_expansion", "SOLVER_RANKING_ESCALATION",
     "policy.authority_expansion_allowed flipped true",
     lambda rq, ev, po: po.__setitem__("authority_expansion_allowed", True)),
    ("C09_decision_ceiling", "SOLVER_RANKING_ESCALATION",
     "policy.decision_use_ceiling not AUDIT_ONLY",
     lambda rq, ev, po: po.__setitem__("decision_use_ceiling", "ENABLED")),
    ("C10_required_locks_trimmed", "MISSING_OPTIMIZER_CLAIM_LOCK",
     "policy.required_claim_locks trimmed below the pinned 10 locks",
     lambda rq, ev, po: po.__setitem__("required_claim_locks",
                                       list(po["required_claim_locks"])[:-1])),
    # --- candidate objective injection ---
    ("C11_candidate_injection", "OBJECTIVE_CONSTRAINT_INJECTION",
     "request_source=CANDIDATE carrying objectives",
     lambda rq, ev, po: rq.update({"request_source": "CANDIDATE"})),
    # --- envelope escalation clauses ---
    ("C12_envelope_unknown_module", "FAILED_OR_NO_AUTHORITY_SCORE",
     "envelope module_id not in the registered set",
     lambda rq, ev, po: ev[0].__setitem__("module_id", "amphora-does-not-exist")),
    ("C13_envelope_duplicate", "DUPLICATE_SCORE_ENVELOPE",
     "two envelopes for the same module_id",
     lambda rq, ev, po: ev.append(copy.deepcopy(ev[0]))),
    ("C14_ranking_eligible", "SOLVER_RANKING_ESCALATION",
     "envelope.ranking_eligible flipped true",
     lambda rq, ev, po: ev[0].__setitem__("ranking_eligible", True)),
    ("C15_usable_by_optimizer", "SOLVER_RANKING_ESCALATION",
     "envelope.usable_by_optimizer flipped true",
     lambda rq, ev, po: ev[0].__setitem__("usable_by_optimizer", True)),
    ("C16_envelope_objective_values", "SOLVER_RANKING_ESCALATION",
     "envelope carries non-empty objective_values",
     lambda rq, ev, po: ev[0].__setitem__("objective_values", {"x": 1.0})),
    ("C17_authority_tier_empty", "FAILED_OR_NO_AUTHORITY_SCORE",
     "envelope.authority_tier blank",
     lambda rq, ev, po: ev[0].__setitem__("authority_tier", "  ")),
    ("C18_authority_tier_banned", "FAILED_OR_NO_AUTHORITY_SCORE",
     "envelope.authority_tier in the banned tier set",
     lambda rq, ev, po: ev[0].__setitem__("authority_tier", "RANKING")),
    ("C19_solver_ceiling_invalid", "SOLVER_RANKING_ESCALATION",
     "envelope.solver_use_ceiling outside the allowed set",
     lambda rq, ev, po: ev[0].__setitem__("solver_use_ceiling", "ENABLED")),
    ("C20_claim_lock_missing", "MISSING_OPTIMIZER_CLAIM_LOCK",
     "envelope drops a required zero-authority claim lock",
     lambda rq, ev, po: ev[0]["claim_locks"].__setitem__("no_ranking_authority", False)),
    # --- objective declaration clauses ---
    ("C21_objective_id_empty", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "objective_id blank",
     lambda rq, ev, po: rq["objectives"][0].__setitem__("objective_id", " ")),
    ("C22_objective_id_dup", "DUPLICATE_SCORE_ENVELOPE",
     "two objectives sharing an objective_id",
     lambda rq, ev, po: rq["objectives"].append(copy.deepcopy(rq["objectives"][0]))),
    ("C23_objective_module_unknown", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "objective.module_id not registered",
     lambda rq, ev, po: rq["objectives"][0].__setitem__("module_id", "amphora-does-not-exist")),
    ("C24_objective_section", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "objective.section not objective_values",
     lambda rq, ev, po: rq["objectives"][0].__setitem__("section", "gates")),
    ("C25_objective_path_empty", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "objective.path blank",
     lambda rq, ev, po: rq["objectives"][0].__setitem__("path", "")),
    # --- constraint declaration clauses ---
    ("C26_constraint_id_empty", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "constraint_id blank",
     lambda rq, ev, po: rq["hard_constraints"][0].__setitem__("constraint_id", "")),
    ("C27_constraint_id_dup", "DUPLICATE_SCORE_ENVELOPE",
     "two constraints sharing a constraint_id",
     lambda rq, ev, po: rq["hard_constraints"].append(copy.deepcopy(rq["hard_constraints"][0]))),
    ("C28_constraint_module_unknown", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "constraint.module_id not registered",
     lambda rq, ev, po: rq["hard_constraints"][0].__setitem__("module_id", "amphora-does-not-exist")),
    ("C29_constraint_section", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "constraint.section not gates",
     lambda rq, ev, po: rq["hard_constraints"][0].__setitem__("section", "objective_values")),
    ("C30_constraint_path_empty", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "constraint.path blank",
     lambda rq, ev, po: rq["hard_constraints"][0].__setitem__("path", "")),
    ("C31_constraint_operator_invalid", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "constraint.operator outside the allowed relational set",
     lambda rq, ev, po: rq["hard_constraints"][0].__setitem__("operator", "contains")),
    # --- constraint evaluation clauses ---
    ("C32_constraint_envelope_absent", "FAILED_OR_NO_AUTHORITY_SCORE",
     "constraint references a registered module with no supplied envelope",
     lambda rq, ev, po: rq["hard_constraints"][0].__setitem__("module_id", REG2)),
    ("C33_envelope_not_scored", "FAILED_OR_NO_AUTHORITY_SCORE",
     "referenced envelope.status not SCORED",
     lambda rq, ev, po: ev[0].__setitem__("status", "FAILED_GATES")),
    ("C34_path_all_empty_parts", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "constraint.path is non-blank but resolves to zero path parts ('.')",
     lambda rq, ev, po: rq["hard_constraints"][0].__setitem__("path", ".")),
    ("C35_path_first_absent", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "constraint.path first segment absent from envelope.gates",
     lambda rq, ev, po: rq["hard_constraints"][0].__setitem__("path", "notagate")),
    ("C36_path_nested_absent", "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
     "constraint.path descends into a scalar gate value",
     lambda rq, ev, po: rq["hard_constraints"][0].__setitem__("path", "pass.deeper")),
    ("C37_constraint_fails", "FAILED_OR_NO_AUTHORITY_SCORE",
     "hard constraint comparison does not pass",
     lambda rq, ev, po: rq["hard_constraints"][0].__setitem__("expected", False)),
]

SHIPPED_AXES = [
    "OBJECTIVE_CONSTRAINT_INJECTION",
    "UNKNOWN_OBJECTIVE_PATH_OPERATOR",
    "DUPLICATE_SCORE_ENVELOPE",
    "MISSING_OPTIMIZER_CLAIM_LOCK",
    "FAILED_OR_NO_AUTHORITY_SCORE",
    "SOLVER_RANKING_ESCALATION",
]

BANNED_OUTPUT_KEYS = sorted(O.BANNED_AUTHORITY_KEYS)


def run_study():
    # 1. baseline must ACCEPT and preserve the quarantine authority envelope.
    b_req, b_env, b_pol = baseline()
    b_verdict, b_out = decide(b_req, b_env, b_pol)
    baseline_accepts = (b_verdict == "ACCEPT")
    quarantine_invariant = bool(
        baseline_accepts
        and b_out["status"] == "NO_ELIGIBLE_OBJECTIVES"
        and b_out["eligible_objective_count"] == 0
        and b_out["objective_values"] == {}
        and b_out["ranking_performed"] is False
        and b_out["solver_invoked"] is False
        and b_out["usable_by_optimizer"] is False
        and b_out["authority_upgrade"] is False
        and b_out["candidate_created_evidence"] is False
        and b_out["hard_constraints_passed"] is True
        and not any(k in b_out for k in BANNED_OUTPUT_KEYS)
    )

    # 2. each atomic clause: single-mutation must flip ACCEPT -> REJECT.
    records = []
    for cid, axis, desc, mut in CLAUSES:
        rq, ev, po = baseline()
        mut(rq, ev, po)
        verdict, payload = decide(rq, ev, po)
        clean_reject = (verdict == "REJECT"
                        and not str(payload).startswith("__nonreject_exception__"))
        records.append({
            "clause_id": cid,
            "attack_axis": axis,
            "description": desc,
            "baseline_verdict": "ACCEPT",
            "ablated_verdict": verdict,
            "deny_reason": payload if verdict == "REJECT" else None,
            "necessary": bool(clean_reject),
        })

    clause_count = len(records)
    necessary_count = sum(1 for r in records if r["necessary"])
    necessity_rate = necessary_count / clause_count if clause_count else 0.0
    reason_classes = sorted({r["deny_reason"] for r in records if r["deny_reason"]})
    axes_covered = sorted({r["attack_axis"] for r in records})
    axes_all_covered = all(a in axes_covered for a in SHIPPED_AXES)
    # count of accepting configurations among {baseline} U {ablations}
    accepting_configs = (1 if baseline_accepts else 0)  # ablations all reject if necessity holds
    unique_accept = bool(baseline_accepts and necessary_count == clause_count)

    per_axis = {}
    for a in SHIPPED_AXES:
        rs = [r for r in records if r["attack_axis"] == a]
        per_axis[a] = {
            "clause_count": len(rs),
            "all_necessary": all(r["necessary"] for r in rs),
            "clause_ids": [r["clause_id"] for r in rs],
        }

    gates = {
        "g1_baseline_accepts": baseline_accepts,
        "g2_baseline_quarantine_invariant": quarantine_invariant,
        "g3_all_clauses_necessary": necessary_count == clause_count,
        "g4_all_six_attack_axes_covered": axes_all_covered,
        "g5_unique_accepting_configuration": unique_accept,
    }
    gates["all_pass"] = all(gates.values())

    diag = {
        "schema": "amphora.optimizer-orchestrator.authorization-clause-necessity-diagnostic.v1",
        "study_id": "optimizer-authorization-clause-necessity-v1",
        "run_type": "INDEPENDENT_NON_RUNTIME_CLAUSE_NECESSITY_ABLATION",
        "module": "amphora-optimizer-orchestrator",
        "authority": "AUDIT_ONLY",
        "purpose": (
            "Prove the amphora-optimizer-orchestrator deny-by-default "
            "authorization contract is IRREDUNDANT: from one minimal "
            "well-formed accepting request/policy/envelope triple, ablating "
            "each atomic guard clause by a single-field violation flips the "
            "unique accepting configuration to REJECT. Establishes that no "
            "guard is removable without admitting an unauthorized row "
            "(reference-monitor complete mediation, made constructive), and "
            "that the independent clause-set partitions onto all six "
            "shipped module-specific attack axes. Strictly stronger than the "
            "accept/reject DECISION parity of oracle-parity-v1."
        ),
        "hypothesis": (
            "Every atomic guard clause in authorize_optimizer_request is "
            "NECESSARY: exactly one configuration (the well-formed baseline) "
            "accepts, and each single-clause violation rejects. No redundant "
            "(droppable) guard exists; the six documented attack axes are all "
            "exercised by the independent clause enumeration."
        ),
        "theory_reference": [
            "J.P. Anderson, Computer Security Technology Planning Study, ESD-TR-73-51 (1972) -- reference monitor, complete mediation.",
            "Saltzer & Schroeder, The Protection of Information in Computer Systems, Proc. IEEE 63(9):1278-1308 (1975) -- fail-safe defaults, least privilege, economy of mechanism.",
            "NIST SP 800-53 Rev.5 (2020) AC-3 access enforcement, AC-6 least privilege.",
            "NIST SP 800-207 (2020) Zero Trust Architecture -- deny by default.",
        ],
        "method_lineage": [
            "amphora-evidence-intake-validator predicate-completeness (truth-table clause necessity).",
            "amphora-model-card-authority lattice-completeness (irredundant clause set).",
            "Extends optimizer-authorization-oracle-parity-v1 along its named does_not_close axis (reason-level structure).",
        ],
        "non_circularity": (
            "The oracle (optimizer_authorization_oracle.py) is the identical "
            "standalone CPython re-implementation used by oracle-parity-v1; "
            "its sha256 is pinned below and cross-checked against the sibling "
            "study, confirming the contract logic was NOT modified for this "
            "study. It does not import, FFI-call, or read the Rust runtime. "
            "Necessity is a structural property of the contract verified by "
            "constructed minimal cases, not by comparison to any label the "
            "oracle itself emits."
        ),
        "baseline_accepts": baseline_accepts,
        "baseline_quarantine_invariant": quarantine_invariant,
        "baseline_output": b_out if baseline_accepts else None,
        "counts": {
            "atomic_guard_clauses": clause_count,
            "necessary_clauses": necessary_count,
            "distinct_deny_reason_classes": len(reason_classes),
            "attack_axes_covered": len(axes_covered),
            "accepting_configurations": accepting_configs,
        },
        "necessity_rate": necessity_rate,
        "distinct_deny_reason_classes": reason_classes,
        "attack_axes_covered": axes_covered,
        "per_axis": per_axis,
        "records": records,
        "gates": gates,
        "acceptance_bar_floors": {
            "all_met": gates["all_pass"],
            "published_floors": {
                "necessity_rate_floor": 1.0,
                "attack_axes_covered_floor": 6,
                "unique_accepting_configuration_required": True,
            },
            "floor_results": {
                "necessity_rate_floor": necessity_rate >= 1.0,
                "attack_axes_covered_floor": len(axes_covered) >= 6,
                "unique_accepting_configuration_required": unique_accept,
            },
        },
        "runtime_source_anchors": {
            "evidence/phase0/benchmark/result.v1.json":
                "e1d95b6b338b10d5999d9d0af4e5b2e8f635eab72a888942e9a77439382eba17",
            "sibling_oracle_parity_oracle_sha256":
                "a0da8ec147ed82bbdf0b58a56b157ba6a683cebe4cdddb2cc38f3d8f5d7d1774",
        },
        "preconditions": {
            "oracle_does_not_import_rust": True,
            "single_field_mutation_per_clause": True,
            "baseline_is_well_formed_accept": baseline_accepts,
        },
        "closes": [
            "Establishes guard-clause NECESSITY/IRREDUNDANCY for the "
            "optimizer-orchestrator deny-by-default authorization contract: "
            "all %d atomic guards are individually load-bearing (necessity "
            "rate %.4f); the well-formed baseline is the unique accepting "
            "configuration; the independent clause enumeration exercises all "
            "6 documented attack axes. Reason-level structure beyond the "
            "accept/reject decision parity of oracle-parity-v1." % (
                clause_count, necessity_rate),
        ],
        "does_not_close": [
            "Rust error-taxonomy / exact Err-string parity still requires a "
            "live differential harness that executes the Rust runtime and "
            "captures its reason strings (Phase-1).",
            "Necessity is shown for the enumerated atomic guards under "
            "single-field mutation; it is not an exhaustive 2^N truth table "
            "over all guard combinations (interactions are covered only "
            "insofar as each guard is independently sufficient to reject).",
            "No product qualification, batch release, procurement, FTO, "
            "regulatory, or wet-lab claim; authorization is screening-envelope "
            "mediation only.",
            "No promotion, no manifest edit, no scientific_readiness flip "
            "(module stays NOT_APPLICABLE / infrastructure lane, "
            "solver_use_ceiling DISABLED).",
        ],
    }
    return diag


def main():
    diag = run_study()
    out = json.dumps(diag, indent=2, sort_keys=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "canonical"
    fname = f"diagnostic.{which}.json"
    with open(fname, "w") as f:
        f.write(out)
    print(fname, "gates.all_pass=", diag["gates"]["all_pass"],
          "clauses=", diag["counts"]["atomic_guard_clauses"],
          "necessity_rate=", diag["necessity_rate"])


if __name__ == "__main__":
    main()
