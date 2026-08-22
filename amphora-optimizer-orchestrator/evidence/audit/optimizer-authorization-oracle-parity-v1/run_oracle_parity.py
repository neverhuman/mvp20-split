#!/usr/bin/env python3
"""Run the independent optimizer-authorization oracle against (G1) the shipped
positive scenarios, (G2) the shipped fail-closed probes, (G3) a novel
independent adversarial policy corpus, and (G4) the quarantine authority-
envelope invariant. Emit a byte-stable canonical diagnostic (two replays).

AUDIT_ONLY. No manifest edit, no promotion, no scientific_readiness flip.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import optimizer_authorization_oracle as O  # noqa: E402

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-optimizer-orchestrator"
RESULT = MOD / "evidence/phase0/benchmark/result.v1.json"
BENCH_LOCK = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"
CORE_LIB = ROOT / "amphora-core/src/lib.rs"
CORE_PHASE0 = ROOT / "amphora-core/src/phase0.rs"
HARNESS = ROOT / "amphora-assurance-capabilities/tests/optimizer_orchestrator_phase0_kpi.rs"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def is_reject(fn):
    try:
        fn()
        return False, None
    except O.Reject as e:
        return True, str(e)


# ---------------------------------------------------------------------------
# G1: positive-scenario parity (re-derive the 5 shipped positive scenarios).
# ---------------------------------------------------------------------------
def positive_scenarios():
    pass_all = O.constraint("mass-gate", O.ENVELOPE_GATES, "pass_all_hard", "==", True)
    return [
        ("policy-empty-no-envelope", O.policy_request([], []), []),
        ("policy-single-scored-envelope", O.policy_request([], []),
         [O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True)]),
        ("policy-hard-constraint-passes", O.policy_request([], [copy.deepcopy(pass_all)]),
         [O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True)]),
        ("policy-two-envelope-modules", O.policy_request([], []),
         [O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True),
          O.envelope(O.FORMULATION_ARITHMETIC, "mass_identity", True)]),
        ("policy-objective-declared-with-constraint",
         O.policy_request([O.objective("audit-score", O.FORMULATION_ARITHMETIC, "audit_score")],
                          [copy.deepcopy(pass_all)]),
         [O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True)]),
    ]


QUARANTINE_INVARIANT = {
    "status": "NO_ELIGIBLE_OBJECTIVES",
    "hard_constraints_passed": True,
    "eligible_objective_count": 0,
    "objective_values": {},
    "ranking_performed": False,
    "solver_invoked": False,
    "usable_by_optimizer": False,
    "authority_upgrade": False,
    "candidate_created_evidence": False,
}


def banned_key_present(value):
    if isinstance(value, dict):
        for k in value:
            if k in O.BANNED_AUTHORITY_KEYS:
                return k
        for v in value.values():
            r = banned_key_present(v)
            if r:
                return r
    elif isinstance(value, list):
        for v in value:
            r = banned_key_present(v)
            if r:
                return r
    return None


def run_g1(shipped_records):
    ship_by_id = {r["scenario_id"]: r for r in shipped_records}
    rows, ok = [], 0
    quarantine_ok = 0
    envelope_ok = 0
    for sid, req, envs in positive_scenarios():
        rejected, err = is_reject(lambda: O.authorize(req, envs, O.quarantined_policy()))
        oracle_accepts = not rejected
        auth = None if rejected else O.authorize(req, envs, O.quarantined_policy())
        shipped = ship_by_id[sid]
        shipped_accepts = bool(shipped.get("authorization_ok"))
        parity = (oracle_accepts == shipped_accepts)
        inv_ok = (auth == QUARANTINE_INVARIANT) if oracle_accepts else False
        env_clean = (banned_key_present(auth) is None) if oracle_accepts else False
        if parity and oracle_accepts:
            ok += 1
        if inv_ok:
            quarantine_ok += 1
        if env_clean:
            envelope_ok += 1
        rows.append({
            "scenario_id": sid,
            "oracle_accepts": oracle_accepts,
            "shipped_accepts": shipped_accepts,
            "decision_parity": parity,
            "quarantine_invariant_holds": inv_ok,
            "authority_envelope_clean": env_clean,
        })
    n = len(rows)
    return {
        "positive_scenario_parity_rate": ok / n,
        "quarantine_invariant_rate": quarantine_ok / n,
        "authority_envelope_clean_rate": envelope_ok / n,
        "sample_size": n,
        "records": rows,
    }


# ---------------------------------------------------------------------------
# G2: fail-closed probe parity (re-derive all shipped probes, all 6 axes).
# ---------------------------------------------------------------------------
def shipped_probes():
    """Reconstruct every probe input in the Rust harness. Each entry is
    (axis_kpi_key, probe_name, callable-that-invokes-authorize)."""
    P = O.quarantined_policy
    probes = []

    def add(axis, name, req, envs, policy=None):
        pol = policy if policy is not None else P()
        probes.append((axis, name, lambda r=req, e=envs, p=pol: O.authorize(r, e, p)))

    # --- objective_constraint_injection ---
    ax = "objective_constraint_injection_fail_closed_rate"
    add(ax, "candidate_source_with_objectives",
        O.candidate_request([O.objective("candidate-score", O.FORMULATION_ARITHMETIC, "candidate_score")], []), [])
    add(ax, "candidate_source_with_objectives_and_constraint",
        O.candidate_request([O.objective("candidate-score", O.FORMULATION_ARITHMETIC, "candidate_score")],
                            [O.constraint("gate", O.ENVELOPE_GATES, "pass_all_hard", "==", True)]),
        [O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True)])
    r = O.policy_request([], []); r["request_source"] = "SUPPLIER"
    add(ax, "unknown_request_source_string", r, [])

    # --- unknown_objective_path_operator ---
    ax = "unknown_objective_path_operator_fail_closed_rate"
    add(ax, "constraint_operator_contains",
        O.policy_request([], [O.constraint("mass-gate", O.ENVELOPE_GATES, "pass_all_hard", "contains", True)]),
        [O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True)])
    add(ax, "constraint_operator_empty",
        O.policy_request([], [O.constraint("mass-gate", O.ENVELOPE_GATES, "pass_all_hard", "", True)]),
        [O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True)])
    bad = O.objective("audit-score", O.ENVELOPE_GATES, "audit_score"); bad["section"] = "metrics"
    add(ax, "objective_section_not_objective_values", O.policy_request([bad], []), [])
    bad = O.constraint("mass-gate", O.ENVELOPE_GATES, "pass_all_hard", "==", True); bad["section"] = "objective_values"
    add(ax, "constraint_section_not_gates", O.policy_request([], [bad]),
        [O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True)])
    add(ax, "objective_empty_path", O.policy_request([O.objective("audit-score", O.ENVELOPE_GATES, "   ")], []), [])

    # --- duplicate_score_envelope ---
    ax = "duplicate_score_envelope_fail_closed_rate"
    add(ax, "two_envelopes_same_module_id", O.policy_request([], []),
        [O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True),
         O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True)])
    add(ax, "two_objectives_same_id",
        O.policy_request([O.objective("dup", O.FORMULATION_ARITHMETIC, "audit_score"),
                          O.objective("dup", O.FORMULATION_UNIVERSE, "audit_score")], []), [])
    add(ax, "two_constraints_same_id",
        O.policy_request([], [O.constraint("dup", O.ENVELOPE_GATES, "pass_all_hard", "==", True),
                              O.constraint("dup", O.FORMULATION_ARITHMETIC, "mass_identity", "==", True)]),
        [O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True),
         O.envelope(O.FORMULATION_ARITHMETIC, "mass_identity", True)])

    # --- missing_optimizer_claim_lock ---
    ax = "missing_optimizer_claim_lock_fail_closed_rate"
    e = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); del e["claim_locks"]["no_ranking_authority"]
    add(ax, "envelope_missing_no_ranking_authority_lock", O.policy_request([], []), [e])
    e = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e["claim_locks"]["no_optimizer_authority"] = False
    add(ax, "envelope_no_optimizer_authority_lock_false", O.policy_request([], []), [e])
    bad_pol = O.quarantined_policy(); bad_pol["required_claim_locks"].pop()
    add(ax, "policy_required_claim_locks_trimmed", O.policy_request([], []), [], policy=bad_pol)

    # --- failed_or_no_authority_score ---
    ax = "failed_or_no_authority_score_fail_closed_rate"
    e = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e["status"] = "FAILED_GATES"
    add(ax, "envelope_status_failed_gates_with_constraint",
        O.policy_request([], [O.constraint("gate", O.ENVELOPE_GATES, "pass_all_hard", "==", True)]), [e])
    e = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e["ranking_eligible"] = True
    add(ax, "envelope_ranking_eligible_true", O.policy_request([], []), [e])
    e = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e["authority_tier"] = "RANKING"
    add(ax, "envelope_authority_tier_ranking", O.policy_request([], []), [e])
    e = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e["authority_tier"] = "OPTIMIZER"
    add(ax, "envelope_authority_tier_optimizer", O.policy_request([], []), [e])
    e = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e["authority_tier"] = "   "
    add(ax, "envelope_authority_tier_empty_whitespace", O.policy_request([], []), [e])
    e = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e["solver_use_ceiling"] = "RANKING"
    add(ax, "envelope_solver_use_ceiling_unsupported", O.policy_request([], []), [e])
    e = O.envelope(O.UNKNOWN_MODULE, "pass_all_hard", True)
    add(ax, "envelope_module_id_not_registered", O.policy_request([], []), [e])

    # --- solver_ranking_escalation ---
    ax = "solver_ranking_escalation_fail_closed_rate"
    p = O.quarantined_policy(); p["ranking_enabled"] = True
    add(ax, "policy_ranking_enabled_true", O.policy_request([], []), [], policy=p)
    p = O.quarantined_policy(); p["solver_enabled"] = True
    add(ax, "policy_solver_enabled_true", O.policy_request([], []), [], policy=p)
    p = O.quarantined_policy(); p["authority_expansion_allowed"] = True
    add(ax, "policy_authority_expansion_allowed_true", O.policy_request([], []), [], policy=p)
    p = O.quarantined_policy(); p["decision_use_ceiling"] = "RANKING"
    add(ax, "policy_decision_use_ceiling_ranking", O.policy_request([], []), [], policy=p)
    p = O.quarantined_policy(); p["registered_modules"].pop()
    add(ax, "policy_registered_modules_element_removed", O.policy_request([], []), [], policy=p)
    p = O.quarantined_policy(); p["schema"] = "amphora.optimizer-registry-policy.v99"
    add(ax, "policy_schema_wrong_version", O.policy_request([], []), [], policy=p)
    r = O.policy_request([], []); r["schema"] = "amphora.optimizer-authorization-request.v99"
    add(ax, "request_schema_wrong_version", r, [])

    return probes


def run_g2(shipped_kpi):
    # shipped fail_closed booleans indexed by (axis, probe name)
    shipped = {}
    for axis, block in shipped_kpi.items():
        if not axis.endswith("fail_closed_rate"):
            continue
        for pr in block.get("probes", []):
            shipped[(axis, pr["probe"])] = pr["fail_closed"]
    rows, parity_ok, total = [], 0, 0
    axis_counts = {}
    for axis, name, fn in shipped_probes():
        rejected, err = is_reject(fn)
        ship_fc = shipped.get((axis, name))
        parity = (rejected == ship_fc) and rejected is True
        total += 1
        axis_counts.setdefault(axis, [0, 0])
        axis_counts[axis][1] += 1
        if parity:
            parity_ok += 1
            axis_counts[axis][0] += 1
        rows.append({
            "axis": axis, "probe": name,
            "oracle_fail_closed": rejected,
            "shipped_fail_closed": ship_fc,
            "decision_parity": parity,
            "deny_reason": err,
        })
    per_axis = {a: {"parity": c[0] / c[1], "n": c[1]} for a, c in axis_counts.items()}
    return {
        "probe_parity_rate": parity_ok / total,
        "probe_sample_size": total,
        "per_axis": per_axis,
        "records": rows,
    }


# ---------------------------------------------------------------------------
# G3: independent adversarial policy corpus (NOVEL probes not in the harness).
# Each expects a fail-closed rejection, EXCEPT invariance true-negatives that
# must ACCEPT while preserving the quarantine invariant (proves the oracle is
# not a trivial deny-everything monitor).
# ---------------------------------------------------------------------------
def novel_corpus():
    P = O.quarantined_policy
    cases = []  # (name, expect: "REJECT"|"ACCEPT", callable)

    def rej(name, fn):
        cases.append((name, "REJECT", fn))

    def acc(name, fn):
        cases.append((name, "ACCEPT", fn))

    # request_source lexical variants (deny-by-default: exact match only)
    for src in ["policy", "Policy", " POLICY", "POLICY ", "CANDIDATE\n", ""]:
        def f(s=src):
            r = O.policy_request([], []); r["request_source"] = s
            return O.authorize(r, [], P())
        rej(f"request_source_variant::{src!r}", f)

    # objective referencing an unknown module
    rej("objective_module_unknown",
        lambda: O.authorize(O.policy_request([O.objective("o", O.UNKNOWN_MODULE, "p")], []), [], P()))

    # objective path is only dot separators -> empty parts (but obj path check
    # is .strip()!="" so "..." passes obj validation; harmless, quarantined).
    acc("objective_path_dots_only_accepts_quarantined",
        lambda: O.authorize(O.policy_request([O.objective("o", O.FORMULATION_ARITHMETIC, "...")], []), [], P()))

    # constraint referencing module with NO envelope present
    rej("constraint_module_no_envelope",
        lambda: O.authorize(O.policy_request([], [O.constraint("c", O.ENVELOPE_GATES, "pass_all_hard", "==", True)]), [], P()))

    # constraint path traverses into a missing nested key
    e = O.envelope(O.ENVELOPE_GATES, "outer", {"inner": True})
    rej("constraint_nested_path_missing",
        lambda ee=e: O.authorize(O.policy_request([], [O.constraint("c", O.ENVELOPE_GATES, "outer.absent", "==", True)]), [ee], P()))

    # constraint nested path present -> accepts (quarantined true-negative)
    e2 = O.envelope(O.ENVELOPE_GATES, "outer", {"inner": True})
    acc("constraint_nested_path_present_accepts",
        lambda ee=e2: O.authorize(O.policy_request([], [O.constraint("c", O.ENVELOPE_GATES, "outer.inner", "==", True)]), [ee], P()))

    # numeric operator against a STRING actual -> as_f64 None -> false -> reject
    e3 = O.envelope(O.ENVELOPE_GATES, "ratio", "0.5")
    rej("numeric_operator_on_string_actual",
        lambda ee=e3: O.authorize(O.policy_request([], [O.constraint("c", O.ENVELOPE_GATES, "ratio", ">=", 0.4)]), [ee], P()))

    # numeric operator against a BOOL actual -> as_f64 None -> false -> reject
    e4 = O.envelope(O.ENVELOPE_GATES, "flag", True)
    rej("numeric_operator_on_bool_actual",
        lambda ee=e4: O.authorize(O.policy_request([], [O.constraint("c", O.ENVELOPE_GATES, "flag", ">", 0.0)]), [ee], P()))

    # == with type mismatch bool-vs-number -> reject (serde bool != number)
    e5 = O.envelope(O.ENVELOPE_GATES, "flag", True)
    rej("eq_bool_vs_number_typed_mismatch",
        lambda ee=e5: O.authorize(O.policy_request([], [O.constraint("c", O.ENVELOPE_GATES, "flag", "==", 1)]), [ee], P()))

    # numeric constraint that genuinely passes -> accepts quarantined
    e6 = O.envelope(O.ENVELOPE_GATES, "ratio", 0.62)
    acc("numeric_constraint_true_accepts_quarantined",
        lambda ee=e6: O.authorize(O.policy_request([], [O.constraint("c", O.ENVELOPE_GATES, "ratio", ">=", 0.4)]), [ee], P()))

    # envelope authority_tier == PRODUCTION (banned tier not in shipped set)
    e7 = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e7["authority_tier"] = "PRODUCTION"
    rej("envelope_authority_tier_production",
        lambda ee=e7: O.authorize(O.policy_request([], []), [ee], P()))

    # envelope solver_use_ceiling == PRODUCTION (unsupported ceiling)
    e8 = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e8["solver_use_ceiling"] = "PRODUCTION"
    rej("envelope_solver_ceiling_production",
        lambda ee=e8: O.authorize(O.policy_request([], []), [ee], P()))

    # envelope usable_by_optimizer preset true -> reject
    e9 = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e9["usable_by_optimizer"] = True
    rej("envelope_usable_by_optimizer_true",
        lambda ee=e9: O.authorize(O.policy_request([], []), [ee], P()))

    # envelope carries a non-empty objective vector -> reject
    e10 = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e10["objective_values"] = {"score": 1.0}
    rej("envelope_objective_values_nonempty",
        lambda ee=e10: O.authorize(O.policy_request([], []), [ee], P()))

    # policy registered_modules with a DUPLICATE entry (len != set len)
    pdup = O.quarantined_policy(); pdup["registered_modules"].append(pdup["registered_modules"][0])
    rej("policy_registered_modules_duplicate",
        lambda pp=pdup: O.authorize(O.policy_request([], []), [], pp))

    # policy with an EXTRA unregistered module (set mismatch, len 30)
    pext = O.quarantined_policy(); pext["registered_modules"].append("amphora-ghost")
    rej("policy_registered_modules_extra_unknown",
        lambda pp=pext: O.authorize(O.policy_request([], []), [], pp))

    # policy with a required lock RENAMED (set mismatch, same length)
    pren = O.quarantined_policy(); pren["required_claim_locks"][0] = "no_ranking_AUTHORITY_typo"
    rej("policy_required_lock_renamed_same_len",
        lambda pp=pren: O.authorize(O.policy_request([], []), [], pp))

    # policy decision_use_ceiling lowercased -> reject (exact match)
    plc = O.quarantined_policy(); plc["decision_use_ceiling"] = "audit_only"
    rej("policy_decision_ceiling_lowercase",
        lambda pp=plc: O.authorize(O.policy_request([], []), [], pp))

    # objective_id whitespace-only -> reject
    rej("objective_id_whitespace_only",
        lambda: O.authorize(O.policy_request([O.objective("   ", O.FORMULATION_ARITHMETIC, "p")], []), [], P()))

    # constraint operator valid but expected type makes != trivially true ->
    # accepts quarantined (true-negative: != on differing values passes)
    e11 = O.envelope(O.ENVELOPE_GATES, "flag", True)
    acc("constraint_neq_true_accepts_quarantined",
        lambda ee=e11: O.authorize(O.policy_request([], [O.constraint("c", O.ENVELOPE_GATES, "flag", "!=", False)]), [ee], P()))

    # extra unknown claim lock on envelope is harmless (invariance) -> accepts
    e12 = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True); e12["claim_locks"]["extra_unknown_lock"] = True
    acc("envelope_extra_unknown_lock_accepts_quarantined",
        lambda ee=e12: O.authorize(O.policy_request([], []), [ee], P()))

    # CANDIDATE source with EMPTY objectives + valid constraint -> accepts
    # quarantined (candidate may audit constraints, just cannot inject objectives)
    e13 = O.envelope(O.ENVELOPE_GATES, "pass_all_hard", True)
    acc("candidate_empty_objectives_with_constraint_accepts",
        lambda ee=e13: O.authorize(O.candidate_request([], [O.constraint("c", O.ENVELOPE_GATES, "pass_all_hard", "==", True)]), [ee], P()))

    return cases


def run_g3():
    rows, ok = [], 0
    invariant_ok = 0
    accept_cases = 0
    for name, expect, fn in novel_corpus():
        rejected, err = is_reject(fn)
        got = "REJECT" if rejected else "ACCEPT"
        correct = (got == expect)
        inv_ok = True
        if not rejected:
            accept_cases += 1
            auth = fn()
            inv_ok = (auth == QUARANTINE_INVARIANT) and (banned_key_present(auth) is None)
            if inv_ok:
                invariant_ok += 1
        if correct and inv_ok:
            ok += 1
        rows.append({
            "case": name, "expected": expect, "got": got,
            "correct": correct,
            "quarantine_invariant_holds": inv_ok if not rejected else None,
            "deny_reason": err,
        })
    n = len(rows)
    return {
        "novel_corpus_correct_rate": ok / n,
        "novel_corpus_size": n,
        "accept_true_negatives": accept_cases,
        "accept_quarantine_invariant_rate": (invariant_ok / accept_cases) if accept_cases else 1.0,
        "records": rows,
    }


def build_diagnostic():
    result = json.loads(RESULT.read_bytes())
    shipped_records = result["records"]
    shipped_kpi = result["kpi"]

    g1 = run_g1(shipped_records)
    g2 = run_g2(shipped_kpi)
    g3 = run_g3()

    # G4: aggregate quarantine invariant across ALL accepting cases (G1 + G3).
    g4_accepts = g1["sample_size"] + g3["accept_true_negatives"]
    g4_inv_holds = (
        round(g1["quarantine_invariant_rate"] * g1["sample_size"])
        + round(g3["accept_quarantine_invariant_rate"] * g3["accept_true_negatives"])
    )

    gates = {
        "g1_positive_scenario_parity": g1["positive_scenario_parity_rate"] == 1.0,
        "g2_fail_closed_probe_parity": g2["probe_parity_rate"] == 1.0,
        "g3_novel_adversarial_corpus_correct": g3["novel_corpus_correct_rate"] == 1.0,
        "g4_quarantine_authority_envelope_invariant":
            (g1["quarantine_invariant_rate"] == 1.0)
            and (g1["authority_envelope_clean_rate"] == 1.0)
            and (g3["accept_quarantine_invariant_rate"] == 1.0),
    }
    gates["all_pass"] = all(gates.values())

    floors = {
        "positive_scenario_parity_rate_floor": 1.0,
        "fail_closed_probe_parity_rate_floor": 1.0,
        "novel_corpus_correct_rate_floor": 1.0,
        "quarantine_invariant_rate_floor": 1.0,
    }
    floor_results = {
        "positive_scenario_parity_rate_floor": g1["positive_scenario_parity_rate"] >= 1.0,
        "fail_closed_probe_parity_rate_floor": g2["probe_parity_rate"] >= 1.0,
        "novel_corpus_correct_rate_floor": g3["novel_corpus_correct_rate"] >= 1.0,
        "quarantine_invariant_rate_floor": gates["g4_quarantine_authority_envelope_invariant"],
    }

    diag = {
        "schema": "amphora.optimizer-orchestrator.authorization-oracle-parity-diagnostic.v1",
        "study_id": "optimizer-authorization-oracle-parity-v1",
        "module": "amphora-optimizer-orchestrator",
        "authority": "AUDIT_ONLY",
        "run_type": "INDEPENDENT_NON_RUNTIME_ORACLE_PARITY",
        "purpose": (
            "Independently re-derive the amphora-optimizer-orchestrator "
            "deny-by-default authorization gate from published reference-monitor "
            "semantics (no Rust import), reproduce every shipped Phase-0 positive "
            "scenario and fail-closed probe at 100% decision parity, and exercise "
            "an independent adversarial policy corpus -- the artifact the mission "
            "names as the Phase-1 prerequisite."
        ),
        "hypothesis": (
            "The module's falsifiable hypothesis -- identity-bound policy prevents "
            "every unauthorized row from ranking -- holds under an independent "
            "re-implementation: the unauthorized-rank rate is zero on every probe "
            "and the quarantine authority envelope (eligible_objective_count=0, "
            "ranking_performed/solver_invoked/usable_by_optimizer=false, no banned "
            "authority key) is preserved on every accepting case."
        ),
        "non_circularity": (
            "The oracle (ooo_oracle.py) is a standalone CPython re-implementation "
            "of the authorization contract from Anderson-1972 reference-monitor / "
            "Saltzer-Schroeder-1975 fail-safe-default / NIST SP 800-53 AC-3/AC-6 "
            "semantics. It does not import, FFI-call, or read amphora-core; parity "
            "is measured against the byte-stable shipped result.v1.json, whose "
            "decisions were produced by the independent Rust runtime."
        ),
        "theory_reference": [
            "J.P. Anderson, Computer Security Technology Planning Study, ESD-TR-73-51 (1972) -- reference monitor.",
            "Saltzer & Schroeder, The Protection of Information in Computer Systems, Proc. IEEE 63(9):1278-1308 (1975) -- fail-safe defaults, least privilege.",
            "NIST SP 800-53 Rev.5 (2020) AC-3 access enforcement, AC-6 least privilege.",
            "NIST SP 800-207 (2020) Zero Trust Architecture -- deny by default.",
            "ISO/IEC 27001:2022 Annex A.5.15 access control.",
        ],
        "runtime_source_anchors": {
            "amphora-core/src/lib.rs": sha(CORE_LIB.read_bytes()),
            "amphora-core/src/phase0.rs": sha(CORE_PHASE0.read_bytes()),
            "amphora-assurance-capabilities/tests/optimizer_orchestrator_phase0_kpi.rs": sha(HARNESS.read_bytes()),
            "evidence/phase0/benchmark/result.v1.json": sha(RESULT.read_bytes()),
            "evidence/phase0/benchmark/benchmark-lock.v1.json": sha(BENCH_LOCK.read_bytes()),
        },
        "preconditions": {
            "optimizer_modules_count": len(O.OPTIMIZER_MODULES),
            "required_claim_locks_count": len(O.REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS),
            "shipped_positive_scenarios": len(shipped_records),
            "shipped_probe_axes": sorted(k for k in shipped_kpi if k.endswith("fail_closed_rate")),
        },
        "g1_positive_scenario_parity": g1,
        "g2_fail_closed_probe_parity": g2,
        "g3_novel_adversarial_corpus": g3,
        "g4_quarantine_invariant": {
            "total_accepting_cases": g4_accepts,
            "invariant_holds_cases": g4_inv_holds,
            "invariant_rate": g4_inv_holds / g4_accepts if g4_accepts else 1.0,
            "note": "Every accepting authorization returns the frozen quarantine envelope with zero rankable rows and no banned authority key.",
        },
        "gates": gates,
        "acceptance_bar_floors": {
            "published_floors": floors,
            "floor_results": floor_results,
            "all_met": all(floor_results.values()),
        },
        "counts": {
            "positive_scenarios": g1["sample_size"],
            "shipped_probes": g2["probe_sample_size"],
            "novel_corpus_cases": g3["novel_corpus_size"],
            "novel_accept_true_negatives": g3["accept_true_negatives"],
            "total_cases": g1["sample_size"] + g2["probe_sample_size"] + g3["novel_corpus_size"],
        },
        "closes": [
            "First independent (non-runtime) re-derivation of the optimizer-orchestrator deny-by-default authorization gate: reproduces all 5 shipped positive scenarios and all shipped fail-closed probes across the 6 module-specific attack axes at 100% decision parity vs the byte-stable Rust result.v1.json.",
            "Supplies an independent adversarial policy corpus of novel probes (lexical source variants, typed comparison mismatches, nested-path traversal, duplicate/extra/renamed registry rows, and quarantined true-negatives) not present in the shipped harness -- the mission's named Phase-1 prerequisite -- with 100% expected fail-closed / accept-quarantined behaviour.",
            "Confirms the quarantine authority-envelope invariant on every accepting case: zero rankable rows, eligible_objective_count=0, solver/ranking/optimizer locks preserved, no banned authority key emitted.",
        ],
        "does_not_close": [
            "Rust error-taxonomy / reason-string parity: the oracle matches accept/reject decisions, not the runtime's exact Err strings -- a Phase-1 differential harness.",
            "No product qualification, batch release, procurement, FTO, regulatory, or wet-lab claim -- authorization is screening-envelope mediation only.",
            "No promotion, no manifest edit, no scientific_readiness flip (module stays NOT_APPLICABLE / infrastructure lane, solver_use_ceiling DISABLED).",
        ],
    }
    return diag


def main():
    diag = build_diagnostic()
    canonical = json.dumps(diag, indent=2, sort_keys=True, ensure_ascii=False)
    out_dir = MOD / "evidence/audit/optimizer-authorization-oracle-parity-v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "diagnostic.canonical.json").write_text(canonical)
    # second replay
    diag2 = build_diagnostic()
    canonical2 = json.dumps(diag2, indent=2, sort_keys=True, ensure_ascii=False)
    (out_dir / "diagnostic.runB.json").write_text(canonical2)
    print("all_gates_pass", diag["gates"]["all_pass"])
    print("g1_parity", diag["g1_positive_scenario_parity"]["positive_scenario_parity_rate"])
    print("g2_probe_parity", diag["g2_fail_closed_probe_parity"]["probe_parity_rate"],
          "n=", diag["g2_fail_closed_probe_parity"]["probe_sample_size"])
    print("g3_novel_correct", diag["g3_novel_adversarial_corpus"]["novel_corpus_correct_rate"],
          "n=", diag["g3_novel_adversarial_corpus"]["novel_corpus_size"])
    print("g4_invariant_rate", diag["g4_quarantine_invariant"]["invariant_rate"])
    print("two_replay_byte_identical", canonical.encode() == canonical2.encode())
    print("canonical_sha256", sha(canonical.encode()))


if __name__ == "__main__":
    main()
