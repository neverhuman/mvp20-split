#!/usr/bin/env python3
"""Independent (non-runtime) re-derivation oracle for the
amphora-optimizer-orchestrator deny-by-default authorization gate.

This module does NOT import, link, or invoke the Rust runtime
(amphora-core::authorize_optimizer_request). It re-implements the
reference-monitor authorization contract from first principles, from the
published semantics only:

  Reference-monitor / deny-by-default authorization:
    - J.P. Anderson, "Computer Security Technology Planning Study",
      ESD-TR-73-51 (1972) -- the reference monitor concept: complete
      mediation, tamper-proof, verifiable.
    - Saltzer & Schroeder, "The Protection of Information in Computer
      Systems", Proc. IEEE 63(9):1278-1308 (1975) -- fail-safe defaults
      & least privilege: the default is lack of access.
    - NIST SP 800-53 Rev.5 AC-3 (access enforcement), AC-6 (least
      privilege); NIST SP 800-207 (Zero Trust) -- deny by default.
    - ISO/IEC 27001:2022 Annex A.5.15 (access control).

The optimizer's falsifiable hypothesis (docs/mission.md): "identity-bound
policy can prevent every unauthorized row from ranking." The primary KPI
is the UNAUTHORIZED-RANK RATE, whose locked target is ZERO silent
acceptance of malformed/unsupported/unauthorized inputs, and whose
quarantine invariant is that no row is ever rankable
(ranking_performed=false, solver_invoked=false, usable_by_optimizer=false,
eligible_objective_count=0) regardless of input.

The oracle is used to (a) re-derive every shipped positive scenario and
fail-closed probe in the Rust Phase-0 harness and check 100% decision
parity against the byte-stable shipped result.v1.json, and (b) exercise
an INDEPENDENT adversarial policy corpus (novel probes not present in the
shipped harness) -- the exact artifact the mission names as the Phase-1
prerequisite ("an independent adversarial policy corpus").
"""

# ---- Published contract constants (re-declared independently) --------------

OPTIMIZER_MODULES = [
    "amphora-barrier-corrosion-score",
    "amphora-candidate-contract",
    "amphora-cro-protocol-packager",
    "amphora-cure-potlife-gate",
    "amphora-design-rule-score",
    "amphora-envelope-gates",
    "amphora-evidence-intake-validator",
    "amphora-formulation-arithmetic",
    "amphora-formulation-universe",
    "amphora-ingredient-library",
    "amphora-ip-fto-guard",
    "amphora-known-answer-benchmarks",
    "amphora-model-card-authority",
    "amphora-molecule-design-gate",
    "amphora-molecule-generator",
    "amphora-molecule-novelty",
    "amphora-molecule-property",
    "amphora-molecule-role-ranker",
    "amphora-optimizer-orchestrator",
    "amphora-process-qc-twin",
    "amphora-public-corrosion-benchmark",
    "amphora-redteam-audit",
    "amphora-report-packager",
    "amphora-run-provenance",
    "amphora-solvency-score",
    "amphora-source-ledger",
    "amphora-sourceability-ehs",
    "amphora-tolerance-robustness",
    "amphora-viscosity-score",
]  # 29 modules

REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS = [
    "no_ranking_authority",
    "no_optimizer_authority",
    "no_release_authority",
    "no_qualification_authority",
    "no_patentability_authority",
    "fto_not_performed",
    "no_procurement_authority",
    "no_regulatory_authority",
    "no_safety_authority",
    "no_product_performance_authority",
]  # 10 locks

BANNED_AUTHORITY_KEYS = {
    "batch_release",
    "release_authorized",
    "qualified",
    "authorized_by",
    "manufacturing_qualification",
    "release_authority",
}

REQUEST_SCHEMA = "amphora.optimizer-authorization-request.v1"
POLICY_SCHEMA = "amphora.optimizer-registry-policy.v1"
ALLOWED_SOURCES = ("POLICY", "CANDIDATE")
ALLOWED_OPERATORS = ("==", "!=", ">=", "<=", ">", "<")
ALLOWED_SOLVER_CEILINGS = ("DISABLED", "AUDIT_ONLY", "CONSTRAINT_ONLY")
BANNED_AUTHORITY_TIERS = ("RANKING", "OPTIMIZER", "PRODUCTION")


class Reject(Exception):
    """Fail-closed rejection carrying the deny reason."""


def _as_f64(v):
    """Mirror serde_json Value::as_f64: numbers -> float; bool/str/None -> None."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def comparison_passes(actual, operator, expected):
    if actual is None:
        return False
    if operator == "==":
        return _json_eq(actual, expected)
    if operator == "!=":
        return not _json_eq(actual, expected)
    la, lb = _as_f64(actual), _as_f64(expected)
    if la is None or lb is None:
        return False
    if operator == ">=":
        return la >= lb
    if operator == "<=":
        return la <= lb
    if operator == ">":
        return la > lb
    if operator == "<":
        return la < lb
    return False


def _json_eq(a, b):
    # serde_json equality: bool != number; numbers compared by value.
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    return a == b


def quarantined_policy():
    return {
        "schema": POLICY_SCHEMA,
        "registered_modules": list(OPTIMIZER_MODULES),
        "ranking_enabled": False,
        "solver_enabled": False,
        "authority_expansion_allowed": False,
        "decision_use_ceiling": "AUDIT_ONLY",
        "required_claim_locks": list(REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS),
    }


def authorize(request, envelopes, policy):
    """Independent re-derivation of authorize_optimizer_request.

    Returns the quarantined OptimizerAuthorizationV1 dict on success;
    raises Reject on any fail-closed condition."""
    registered = set(policy["registered_modules"])
    expected_modules = set(OPTIMIZER_MODULES)
    required_locks = set(policy["required_claim_locks"])
    expected_locks = set(REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS)

    if (
        request["schema"] != REQUEST_SCHEMA
        or request["request_source"] not in ALLOWED_SOURCES
        or policy["schema"] != POLICY_SCHEMA
        or len(policy["registered_modules"]) != len(registered)  # duplicate guard
        or registered != expected_modules
        or policy["ranking_enabled"]
        or policy["solver_enabled"]
        or policy["authority_expansion_allowed"]
        or policy["decision_use_ceiling"] != "AUDIT_ONLY"
        or required_locks != expected_locks
    ):
        raise Reject("optimizer registry policy is altered or incomplete")

    if request["request_source"] == "CANDIDATE" and request["objectives"]:
        raise Reject("candidate objective injection is forbidden")

    envelope_by_module = {}
    for env in envelopes:
        mid = env["module_id"]
        if mid not in registered or mid in envelope_by_module:
            raise Reject("optimizer envelope module is unknown or duplicated")
        envelope_by_module[mid] = env
        if (
            env["ranking_eligible"]
            or env["usable_by_optimizer"]
            or env["objective_values"]
            or env["authority_tier"].strip() == ""
            or env["authority_tier"] in BANNED_AUTHORITY_TIERS
            or env["solver_use_ceiling"] not in ALLOWED_SOLVER_CEILINGS
            or any(
                env["claim_locks"].get(lock) is not True
                for lock in policy["required_claim_locks"]
            )
        ):
            raise Reject(
                "optimizer envelope attempts authority, score, solver, or lock escalation"
            )

    objective_ids = set()
    for obj in request["objectives"]:
        oid = obj["objective_id"]
        if (
            oid.strip() == ""
            or oid in objective_ids
            or obj["module_id"] not in registered
            or obj["section"] != "objective_values"
            or obj["path"].strip() == ""
        ):
            raise Reject("optimizer objective declaration is unknown, duplicate, or malformed")
        objective_ids.add(oid)

    constraint_ids = set()
    for con in request["hard_constraints"]:
        cid = con["constraint_id"]
        if (
            cid.strip() == ""
            or cid in constraint_ids
            or con["module_id"] not in registered
            or con["section"] != "gates"
            or con["path"].strip() == ""
            or con["operator"] not in ALLOWED_OPERATORS
        ):
            raise Reject("optimizer constraint declaration is unknown, duplicate, or malformed")
        constraint_ids.add(cid)
        env = envelope_by_module.get(con["module_id"])
        if env is None:
            raise Reject("optimizer constraint module envelope is absent")
        if env["status"] != "SCORED":
            raise Reject("optimizer constraint envelope is not SCORED")
        parts = [p for p in con["path"].split(".") if p != ""]
        if not parts:
            raise Reject("optimizer constraint path is absent or unknown")
        first, rest = parts[0], parts[1:]
        if first not in env["gates"]:
            raise Reject("optimizer constraint path is absent or unknown")
        actual = env["gates"][first]
        for part in rest:
            if not isinstance(actual, dict) or part not in actual:
                raise Reject("optimizer constraint path is absent or unknown")
            actual = actual[part]
        if not comparison_passes(actual, con["operator"], con["expected"]):
            raise Reject("optimizer hard constraint failed")

    return {
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


# ---- Input builders mirroring the Rust harness helpers ---------------------

ENVELOPE_GATES = "amphora-envelope-gates"
FORMULATION_ARITHMETIC = "amphora-formulation-arithmetic"
FORMULATION_UNIVERSE = "amphora-formulation-universe"
UNKNOWN_MODULE = "amphora-does-not-exist"


def policy_request(objectives, hard_constraints):
    return {
        "schema": REQUEST_SCHEMA,
        "request_source": "POLICY",
        "objectives": objectives,
        "hard_constraints": hard_constraints,
    }


def candidate_request(objectives, hard_constraints):
    return {
        "schema": REQUEST_SCHEMA,
        "request_source": "CANDIDATE",
        "objectives": objectives,
        "hard_constraints": hard_constraints,
    }


def envelope(module_id, gate_key, gate_value):
    return {
        "module_id": module_id,
        "status": "SCORED",
        "authority_tier": "REAL_ARITHMETIC",
        "solver_use_ceiling": "CONSTRAINT_ONLY",
        "ranking_eligible": False,
        "usable_by_optimizer": False,
        "objective_values": {},
        "gates": {gate_key: gate_value},
        "claim_locks": {lock: True for lock in REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS},
    }


def constraint(cid, module_id, path, operator, expected):
    return {
        "constraint_id": cid,
        "module_id": module_id,
        "section": "gates",
        "path": path,
        "operator": operator,
        "expected": expected,
    }


def objective(oid, module_id, path):
    return {
        "objective_id": oid,
        "module_id": module_id,
        "section": "objective_values",
        "path": path,
    }
