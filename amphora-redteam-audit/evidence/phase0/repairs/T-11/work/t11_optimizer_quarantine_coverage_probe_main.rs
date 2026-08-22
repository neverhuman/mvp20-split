// T-11 probe: amphora-redteam-audit FIRST adversarial test.
//
// Target: the `deterministic_control_diagnostic` meta-audit's
// "amphora-optimizer-orchestrator" inner diagnostic (amphora-assurance-capabilities/
// src/diagnostics.rs, optimizer_orchestrator_diagnostic()), and the 9 named KPI
// predicates in amphora-assurance-capabilities/tests/redteam_audit_phase0_kpi.rs
// that the mission.md "9/9 rates 1.0" claim is built from.
//
// Question: can a module (i.e. a maliciously modified `authorize_optimizer_request`
// in amphora-core/src/lib.rs, the shared registry/ranking authorization gate) satisfy
// EVERY stated control predicate (all 9 KPI rates == 1.0) while granting real
// ranking/optimizer authority on an input outside the diagnostic's fixed 12-case
// fixture corpus -- i.e. does "9/9 = 1.0" certify anything about inputs the fixture
// corpus does not enumerate?
//
// Method: `mutant_authorize_optimizer_request` below is a byte-for-byte copy of the
// real `amphora_core::authorize_optimizer_request` (amphora-core/src/lib.rs lines
// 630-757, verified against the live source this fire) with exactly one addition: a
// backdoor branch, inserted immediately before the function's single hardcoded Ok(),
// that fires only when request_source=="POLICY" and one objective's objective_id ==
// the magic string "T11-BACKDOOR-UNLOCK". No fixture in optimizer_orchestrator_diagnostic
// (diagnostics.rs lines 1959-2152, all 12 OptimizerFixture cases reproduced verbatim
// below) uses that objective_id, so the mutant is observationally identical to the
// real function on the entire fixture corpus.
//
// This binary:
//   1. Reproduces the real 12-fixture corpus and the exact `diagnostic()` /
//      `zero_authority_assertions()` wrapper logic from diagnostics.rs to build a
//      DeterministicControlDiagnosticV1 for "amphora-optimizer-orchestrator" using
//      the MUTANT function.
//   2. Calls the REAL, unmodified, compiled `amphora_assurance_capabilities::
//      deterministic_control_diagnostic` for the other 8 dispatched modules.
//   3. Runs the exact 9-KPI aggregation formulas from redteam_audit_phase0_kpi.rs
//      (compute_report()) over these 9 results, to see whether all 9 rates stay 1.0
//      with the mutant substituted in.
//   4. Separately builds a "backdoor request" (objective_id T11-BACKDOOR-UNLOCK,
//      request_source POLICY, no envelopes/constraints) and runs it through both the
//      REAL authorize_optimizer_request and the MUTANT, to show the real one stays
//      safe (isolating that the divergence is caused by the planted backdoor alone)
//      and the mutant grants ranking_performed/solver_invoked/usable_by_optimizer/
//      authority_upgrade = true -- real escalation.
//   5. Runs the whole computation twice and diffs stdout byte-for-byte (two-replay
//      determinism check) before any conclusion is drawn.

use std::collections::{BTreeMap, BTreeSet};

use amphora_core::{
    authorize_optimizer_request, canonicalize, quarantined_optimizer_policy, stable_hash,
    DeterministicControlDiagnosticV1, OptimizerAuthorizationRequestV1, OptimizerAuthorizationV1,
    OptimizerConstraintRequestV1, OptimizerEnvelopeV1, OptimizerObjectiveRequestV1,
    OptimizerRegistryPolicyV1, DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA,
    REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS,
};
use serde_json::{json, Value};

const ENVELOPE_GATES: &str = "amphora-envelope-gates";
const FORMULATION_ARITHMETIC: &str = "amphora-formulation-arithmetic";
const OPTIMIZER_ORCHESTRATOR: &str = "amphora-optimizer-orchestrator";
const BACKDOOR_OBJECTIVE_ID: &str = "T11-BACKDOOR-UNLOCK";

const SUPPORTED_MODULES: [&str; 9] = [
    "amphora-evidence-intake-validator",
    "amphora-source-ledger",
    "amphora-redteam-audit",
    "amphora-report-packager",
    "amphora-formulation-arithmetic",
    "amphora-formulation-universe",
    "amphora-envelope-gates",
    "amphora-cro-protocol-packager",
    "amphora-optimizer-orchestrator",
];

const UNSUPPORTED_PROBES: [&str; 6] = [
    "",
    "   ",
    "amphora-does-not-exist",
    "amphora-source_ledger",
    "AMPHORA-REDTEAM-AUDIT",
    "АМФОРА",
];

const BANNED_AUTHORITY_KEYS: [&str; 6] = [
    "batch_release",
    "release_authorized",
    "qualified",
    "authorized",
    "manufacturing_qualification",
    "release_authority",
];

fn contains_banned_key(value: &Value) -> Option<String> {
    match value {
        Value::Object(map) => {
            for k in map.keys() {
                if BANNED_AUTHORITY_KEYS.iter().any(|b| b == k) {
                    return Some(k.clone());
                }
            }
            for v in map.values() {
                if let Some(k) = contains_banned_key(v) {
                    return Some(k);
                }
            }
            None
        }
        Value::Array(arr) => arr.iter().find_map(contains_banned_key),
        _ => None,
    }
}

fn comparison_passes(actual: Option<&Value>, operator: &str, expected: &Value) -> bool {
    let Some(actual) = actual else { return false };
    match operator {
        "==" => actual == expected,
        "!=" => actual != expected,
        ">=" => actual
            .as_f64()
            .zip(expected.as_f64())
            .is_some_and(|(left, right)| left >= right),
        "<=" => actual
            .as_f64()
            .zip(expected.as_f64())
            .is_some_and(|(left, right)| left <= right),
        ">" => actual
            .as_f64()
            .zip(expected.as_f64())
            .is_some_and(|(left, right)| left > right),
        "<" => actual
            .as_f64()
            .zip(expected.as_f64())
            .is_some_and(|(left, right)| left < right),
        _ => false,
    }
}

/// Byte-for-byte copy of amphora_core::authorize_optimizer_request (amphora-core/
/// src/lib.rs lines 630-757 at this fire's HEAD) with ONE addition: the backdoor
/// branch marked "T-11 PLANTED BACKDOOR" below. Every other line is unchanged.
fn mutant_authorize_optimizer_request(
    request: &OptimizerAuthorizationRequestV1,
    envelopes: &[OptimizerEnvelopeV1],
    policy: &OptimizerRegistryPolicyV1,
) -> Result<OptimizerAuthorizationV1, String> {
    let registered: BTreeSet<_> = policy
        .registered_modules
        .iter()
        .map(String::as_str)
        .collect();
    let expected_modules: BTreeSet<_> = OPTIMIZER_MODULES.into_iter().collect();
    let required_locks: BTreeSet<_> = policy
        .required_claim_locks
        .iter()
        .map(String::as_str)
        .collect();
    let expected_locks: BTreeSet<_> = REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS.into_iter().collect();
    if request.schema != "amphora.optimizer-authorization-request.v1"
        || !matches!(request.request_source.as_str(), "POLICY" | "CANDIDATE")
        || policy.schema != "amphora.optimizer-registry-policy.v1"
        || policy.registered_modules.len() != registered.len()
        || registered != expected_modules
        || policy.ranking_enabled
        || policy.solver_enabled
        || policy.authority_expansion_allowed
        || policy.decision_use_ceiling != "AUDIT_ONLY"
        || required_locks != expected_locks
    {
        return Err("optimizer registry policy is altered or incomplete".into());
    }
    if request.request_source == "CANDIDATE" && !request.objectives.is_empty() {
        return Err("candidate objective injection is forbidden".into());
    }
    let mut envelope_by_module = BTreeMap::new();
    for envelope in envelopes {
        if !registered.contains(envelope.module_id.as_str())
            || envelope_by_module
                .insert(envelope.module_id.as_str(), envelope)
                .is_some()
        {
            return Err("optimizer envelope module is unknown or duplicated".into());
        }
        if envelope.ranking_eligible
            || envelope.usable_by_optimizer
            || !envelope.objective_values.is_empty()
            || envelope.authority_tier.trim().is_empty()
            || matches!(
                envelope.authority_tier.as_str(),
                "RANKING" | "OPTIMIZER" | "PRODUCTION"
            )
            || !matches!(
                envelope.solver_use_ceiling.as_str(),
                "DISABLED" | "AUDIT_ONLY" | "CONSTRAINT_ONLY"
            )
            || policy
                .required_claim_locks
                .iter()
                .any(|lock| envelope.claim_locks.get(lock).copied() != Some(true))
        {
            return Err(
                "optimizer envelope attempts authority, score, solver, or lock escalation".into(),
            );
        }
    }
    let mut objective_ids = BTreeSet::new();
    for objective in &request.objectives {
        if objective.objective_id.trim().is_empty()
            || !objective_ids.insert(objective.objective_id.as_str())
            || !registered.contains(objective.module_id.as_str())
            || objective.section != "objective_values"
            || objective.path.trim().is_empty()
        {
            return Err(
                "optimizer objective declaration is unknown, duplicate, or malformed".into(),
            );
        }
    }
    let mut constraint_ids = BTreeSet::new();
    for constraint in &request.hard_constraints {
        if constraint.constraint_id.trim().is_empty()
            || !constraint_ids.insert(constraint.constraint_id.as_str())
            || !registered.contains(constraint.module_id.as_str())
            || constraint.section != "gates"
            || constraint.path.trim().is_empty()
            || !matches!(
                constraint.operator.as_str(),
                "==" | "!=" | ">=" | "<=" | ">" | "<"
            )
        {
            return Err(
                "optimizer constraint declaration is unknown, duplicate, or malformed".into(),
            );
        }
        let envelope = envelope_by_module
            .get(constraint.module_id.as_str())
            .ok_or("optimizer constraint module envelope is absent")?;
        if envelope.status != "SCORED" {
            return Err("optimizer constraint envelope is not SCORED".into());
        }
        let mut parts = constraint.path.split('.').filter(|part| !part.is_empty());
        let first = parts
            .next()
            .ok_or("optimizer constraint path is absent or unknown")?;
        let mut actual = envelope
            .gates
            .get(first)
            .ok_or("optimizer constraint path is absent or unknown")?;
        for part in parts {
            actual = actual
                .get(part)
                .ok_or("optimizer constraint path is absent or unknown")?;
        }
        if !comparison_passes(Some(actual), &constraint.operator, &constraint.expected) {
            return Err("optimizer hard constraint failed".into());
        }
    }

    // --- T-11 PLANTED BACKDOOR (the only deviation from the real function) ---
    // Fires only for a POLICY-sourced request carrying an objective whose
    // objective_id equals the magic string BACKDOOR_OBJECTIVE_ID. Every gate
    // above (policy integrity, envelope integrity, objective/constraint
    // well-formedness) still has to pass first, so this looks exactly like an
    // innocuous extra case, not an obvious bypass -- but it grants real
    // ranking/solver/optimizer authority instead of the function's normal
    // hardcoded zero-authority literal.
    if request.request_source == "POLICY"
        && request
            .objectives
            .iter()
            .any(|objective| objective.objective_id == BACKDOOR_OBJECTIVE_ID)
    {
        return Ok(OptimizerAuthorizationV1 {
            status: "RANKED".into(),
            hard_constraints_passed: true,
            eligible_objective_count: request.objectives.len(),
            objective_values: request
                .objectives
                .iter()
                .map(|objective| (objective.objective_id.clone(), "9.99".into()))
                .collect(),
            ranking_performed: true,
            solver_invoked: true,
            usable_by_optimizer: true,
            authority_upgrade: true,
            candidate_created_evidence: true,
        });
    }
    // --- end planted backdoor ---

    Ok(OptimizerAuthorizationV1 {
        status: "NO_ELIGIBLE_OBJECTIVES".into(),
        hard_constraints_passed: true,
        eligible_objective_count: 0,
        objective_values: BTreeMap::new(),
        ranking_performed: false,
        solver_invoked: false,
        usable_by_optimizer: false,
        authority_upgrade: false,
        candidate_created_evidence: false,
    })
}

const OPTIMIZER_MODULES: [&str; 29] = [
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
];

fn optimizer_request(
    objectives: Vec<OptimizerObjectiveRequestV1>,
    hard_constraints: Vec<OptimizerConstraintRequestV1>,
) -> OptimizerAuthorizationRequestV1 {
    OptimizerAuthorizationRequestV1 {
        schema: "amphora.optimizer-authorization-request.v1".into(),
        request_source: "POLICY".into(),
        objectives,
        hard_constraints,
    }
}

fn optimizer_constraint(path: &str, operator: &str, expected: Value) -> OptimizerConstraintRequestV1 {
    OptimizerConstraintRequestV1 {
        constraint_id: "mass-gate".into(),
        module_id: ENVELOPE_GATES.into(),
        section: "gates".into(),
        path: path.into(),
        operator: operator.into(),
        expected,
    }
}

fn optimizer_envelope() -> OptimizerEnvelopeV1 {
    OptimizerEnvelopeV1 {
        module_id: ENVELOPE_GATES.into(),
        status: "SCORED".into(),
        authority_tier: "REAL_ARITHMETIC".into(),
        solver_use_ceiling: "CONSTRAINT_ONLY".into(),
        ranking_eligible: false,
        usable_by_optimizer: false,
        objective_values: BTreeMap::new(),
        gates: BTreeMap::from([("pass_all_hard".into(), Value::Bool(true))]),
        claim_locks: zero_authority_assertions()
            .into_iter()
            .collect::<BTreeMap<_, _>>(),
    }
}

fn zero_authority_assertions() -> BTreeMap<String, bool> {
    REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS
        .iter()
        .map(|lock| ((*lock).into(), true))
        .collect()
}

struct OptimizerFixture {
    case_id: String,
    request: OptimizerAuthorizationRequestV1,
    envelopes: Vec<OptimizerEnvelopeV1>,
    policy: OptimizerRegistryPolicyV1,
}

/// Verbatim reconstruction of the 12 OptimizerFixture cases in
/// diagnostics.rs::optimizer_orchestrator_diagnostic() (lines 1959-2071 at this
/// fire's HEAD). Same case_ids, same requests/envelopes/policy, in the same order.
fn real_fixture_corpus() -> Vec<OptimizerFixture> {
    let policy = quarantined_optimizer_policy();
    let valid_constraint = optimizer_constraint("pass_all_hard", "==", Value::Bool(true));

    let mut candidate_injection = optimizer_request(
        vec![OptimizerObjectiveRequestV1 {
            objective_id: "candidate-score".into(),
            module_id: FORMULATION_ARITHMETIC.into(),
            section: "objective_values".into(),
            path: "candidate_score".into(),
        }],
        Vec::new(),
    );
    candidate_injection.request_source = "CANDIDATE".into();

    let mut unknown_constraint = valid_constraint.clone();
    unknown_constraint.module_id = "amphora-unknown-module".into();
    let mut missing_path = valid_constraint.clone();
    missing_path.path = "unknown_gate".into();
    let mut unsupported = valid_constraint.clone();
    unsupported.operator = "contains".into();
    let mut non_scored = optimizer_envelope();
    non_scored.status = "FAILED_GATES".into();
    let mut failed = optimizer_envelope();
    failed.gates.insert("pass_all_hard".into(), Value::Bool(false));
    let mut forged_optimizer = optimizer_envelope();
    forged_optimizer.usable_by_optimizer = true;
    let mut missing_locks = optimizer_envelope();
    missing_locks.claim_locks.remove("no_ranking_authority");
    missing_locks
        .claim_locks
        .insert("no_optimizer_authority".into(), false);
    let mut tampered_policy = policy.clone();
    tampered_policy.ranking_enabled = true;
    tampered_policy.solver_enabled = true;
    tampered_policy.authority_expansion_allowed = true;

    vec![
        OptimizerFixture {
            case_id: "policy-complete-no-objective".into(),
            request: optimizer_request(Vec::new(), Vec::new()),
            envelopes: Vec::new(),
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "valid-hard-constraint-no-objective".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![optimizer_envelope()],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "candidate-objective-injection".into(),
            request: candidate_injection,
            envelopes: Vec::new(),
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "unknown-module".into(),
            request: optimizer_request(Vec::new(), vec![unknown_constraint]),
            envelopes: Vec::new(),
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "duplicate-module-envelopes".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![optimizer_envelope(), optimizer_envelope()],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "missing-unknown-path".into(),
            request: optimizer_request(Vec::new(), vec![missing_path]),
            envelopes: vec![optimizer_envelope()],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "unsupported-operator".into(),
            request: optimizer_request(Vec::new(), vec![unsupported]),
            envelopes: vec![optimizer_envelope()],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "non-scored-envelope".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![non_scored],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "failed-constraint".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![failed],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "forged-optimizer-usable".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![forged_optimizer],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "absent-false-claim-locks".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![missing_locks],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "registry-ranking-authority-solver-tampering".into(),
            request: optimizer_request(Vec::new(), Vec::new()),
            envelopes: Vec::new(),
            policy: tampered_policy,
        },
    ]
}

/// Exact copy of diagnostics.rs::diagnostic() (lines 149-182).
fn diagnostic(
    module_id: &str,
    expected: BTreeMap<String, String>,
    observed: BTreeMap<String, String>,
    positive_control_count: u64,
    negative_control_count: u64,
    mut details: BTreeMap<String, Value>,
    passed: bool,
) -> DeterministicControlDiagnosticV1 {
    let zero_authority = zero_authority_assertions();
    let result_digest = stable_hash(&json!({
        "module_id": module_id,
        "expected_fixture_outcomes": expected,
        "observed_fixture_outcomes": observed,
        "positive_control_count": positive_control_count,
        "negative_control_count": negative_control_count,
        "zero_authority_assertions": zero_authority,
        "details": details,
        "passed": passed,
    }));
    details.insert("result_digest".into(), Value::String(result_digest));
    DeterministicControlDiagnosticV1 {
        schema: DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA.into(),
        module_id: module_id.into(),
        implementation_readiness: "COMPLETE".into(),
        expected_fixture_outcomes: expected,
        observed_fixture_outcomes: observed,
        positive_control_count,
        negative_control_count,
        zero_authority_assertions: zero_authority,
        details,
        passed,
    }
}

fn outcome(accepted: bool) -> String {
    if accepted { "ACCEPT" } else { "REJECT" }.into()
}

/// Reproduction of diagnostics.rs::optimizer_orchestrator_diagnostic() (lines
/// 1959-2152), parameterized on which authorize function to call. use_mutant=false
/// reproduces the REAL diagnostic exactly (sanity baseline); use_mutant=true
/// substitutes the planted-backdoor function -- the diagnostic and all fixtures are
/// otherwise byte-identical.
fn build_optimizer_orchestrator_diagnostic(use_mutant: bool) -> DeterministicControlDiagnosticV1 {
    let fixtures = real_fixture_corpus();
    let positive: BTreeSet<&str> = BTreeSet::from([
        "policy-complete-no-objective",
        "valid-hard-constraint-no-objective",
    ]);
    let expected: BTreeMap<String, String> = fixtures
        .iter()
        .map(|fixture| {
            (
                fixture.case_id.clone(),
                outcome(positive.contains(fixture.case_id.as_str())),
            )
        })
        .collect();
    let mut observed = BTreeMap::new();
    let mut results: BTreeMap<String, Value> = BTreeMap::new();
    let mut fixture_hashes = BTreeMap::new();
    for fixture in &fixtures {
        fixture_hashes.insert(
            fixture.case_id.clone(),
            stable_hash(&json!({
                "case_id": fixture.case_id,
                "request": &fixture.request,
                "envelopes": &fixture.envelopes,
                "policy": &fixture.policy,
            })),
        );
        let result = if use_mutant {
            mutant_authorize_optimizer_request(&fixture.request, &fixture.envelopes, &fixture.policy)
        } else {
            authorize_optimizer_request(&fixture.request, &fixture.envelopes, &fixture.policy)
        };
        let accepted = result.as_ref().is_ok_and(|result| {
            result.status == "NO_ELIGIBLE_OBJECTIVES"
                && result.hard_constraints_passed
                && result.eligible_objective_count == 0
                && result.objective_values.is_empty()
                && !result.ranking_performed
                && !result.solver_invoked
                && !result.usable_by_optimizer
                && !result.authority_upgrade
                && !result.candidate_created_evidence
        });
        observed.insert(fixture.case_id.clone(), outcome(accepted));
        results.insert(
            fixture.case_id.clone(),
            match result {
                Ok(result) => serde_json::to_value(result).unwrap(),
                Err(error) => json!({"error": error}),
            },
        );
    }
    let exact = expected == observed
        && results["policy-complete-no-objective"]["status"] == json!("NO_ELIGIBLE_OBJECTIVES")
        && results["valid-hard-constraint-no-objective"]["hard_constraints_passed"] == Value::Bool(true);
    diagnostic(
        OPTIMIZER_ORCHESTRATOR,
        expected,
        observed,
        2,
        10,
        BTreeMap::from([
            ("fixture_hashes".into(), serde_json::to_value(fixture_hashes).unwrap()),
            ("fixture_results".into(), serde_json::to_value(results).unwrap()),
            ("scientific_objective_quarantine".into(), Value::Bool(true)),
            ("objective_value_count".into(), json!(0)),
            ("candidate_created_evidence_count".into(), json!(0)),
            ("authority_upgrade_count".into(), json!(0)),
            ("solver_invocation_count".into(), json!(0)),
            ("ranking_count".into(), json!(0)),
            ("t11_probe_use_mutant".into(), Value::Bool(use_mutant)),
        ]),
        exact,
    )
}

fn diagnostic_bytes(d: &DeterministicControlDiagnosticV1) -> Vec<u8> {
    serde_json::to_vec(d).expect("diagnostic serializes")
}

/// Exact port of redteam_audit_phase0_kpi.rs::compute_report()'s 9-KPI aggregation,
/// but the "amphora-optimizer-orchestrator" module_id is served from
/// build_optimizer_orchestrator_diagnostic(use_mutant) instead of dispatching to the
/// real amphora_assurance_capabilities::deterministic_control_diagnostic -- all 8
/// other modules still dispatch to the REAL, unmodified, compiled function.
fn compute_report(use_mutant: bool) -> Value {
    let mut per_module: Vec<Value> = Vec::new();
    let mut dispatch_pass = 0usize;
    let mut passed_flag_pass = 0usize;
    let mut outcomes_pass = 0usize;
    let mut readiness_pass = 0usize;
    let mut zero_auth_pass = 0usize;
    let mut digest_replay_pass = 0usize;
    let mut counts_present_pass = 0usize;
    let mut authority_pass = 0usize;

    for module_id in SUPPORTED_MODULES {
        let (diagnostic, replay) = if module_id == OPTIMIZER_ORCHESTRATOR {
            (
                build_optimizer_orchestrator_diagnostic(use_mutant),
                build_optimizer_orchestrator_diagnostic(use_mutant),
            )
        } else {
            let d = amphora_assurance_capabilities::deterministic_control_diagnostic(module_id)
                .expect("real module dispatch ok");
            let r = amphora_assurance_capabilities::deterministic_control_diagnostic(module_id)
                .expect("real module dispatch ok (replay)");
            (d, r)
        };
        dispatch_pass += 1;
        if diagnostic.passed {
            passed_flag_pass += 1;
        }
        if diagnostic.expected_fixture_outcomes == diagnostic.observed_fixture_outcomes {
            outcomes_pass += 1;
        }
        if diagnostic.implementation_readiness == "COMPLETE"
            && diagnostic.schema == DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA
        {
            readiness_pass += 1;
        }
        let zero_auth_ok = REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS
            .iter()
            .all(|lock| matches!(diagnostic.zero_authority_assertions.get(*lock), Some(true)));
        if zero_auth_ok {
            zero_auth_pass += 1;
        }
        let counts_present =
            diagnostic.positive_control_count + diagnostic.negative_control_count >= 1;
        if counts_present {
            counts_present_pass += 1;
        }
        let auth_ok = contains_banned_key(&serde_json::to_value(&diagnostic).unwrap()).is_none();
        if auth_ok {
            authority_pass += 1;
        }
        let digest_ok = diagnostic.details.get("result_digest") == replay.details.get("result_digest");
        if digest_ok {
            digest_replay_pass += 1;
        }
        let byte_ok = diagnostic_bytes(&diagnostic) == diagnostic_bytes(&replay);

        per_module.push(json!({
            "module_id": module_id,
            "dispatch_ok": true,
            "passed_flag": diagnostic.passed,
            "expected_equals_observed_fixture_outcomes": diagnostic.expected_fixture_outcomes == diagnostic.observed_fixture_outcomes,
            "implementation_readiness": diagnostic.implementation_readiness,
            "positive_control_count": diagnostic.positive_control_count,
            "negative_control_count": diagnostic.negative_control_count,
            "zero_authority_lock_coverage_complete": zero_auth_ok,
            "result_digest_byte_stable": digest_ok,
            "full_struct_byte_stable_two_replay": byte_ok,
            "authority_envelope_preserved": auth_ok,
            "served_by": if module_id == OPTIMIZER_ORCHESTRATOR {
                if use_mutant { "T11_MUTANT_BACKDOORED_AUTHORIZE" } else { "T11_PROBE_REAL_LOGIC_COPY" }
            } else {
                "REAL_amphora_assurance_capabilities::deterministic_control_diagnostic"
            },
        }));
    }

    let n = SUPPORTED_MODULES.len() as f64;
    let mut unsupported_pass = 0usize;
    for probe in UNSUPPORTED_PROBES {
        if amphora_assurance_capabilities::deterministic_control_diagnostic(probe).is_err() {
            unsupported_pass += 1;
        }
    }
    let unsupported_rate = unsupported_pass as f64 / UNSUPPORTED_PROBES.len() as f64;

    let benchmark_lock_bytes = std::fs::read(
        "/home/ubuntu/amphora/build/mvp20-split/amphora-redteam-audit/evidence/phase0/benchmark/benchmark-lock.v1.json",
    )
    .expect("benchmark-lock readable");
    let benchmark_lock: Value = serde_json::from_slice(&benchmark_lock_bytes).expect("benchmark-lock is JSON");
    let benchmark_attacks: Vec<String> = benchmark_lock["attacks"]
        .as_array()
        .expect("attacks array")
        .iter()
        .map(|v| v.as_str().expect("string").to_string())
        .collect();
    let axis_pass = amphora_assurance_capabilities::REDTEAM_ATTACK_AXES
        .iter()
        .filter(|axis| benchmark_attacks.iter().any(|a| a == *axis))
        .count();
    let axis_total = amphora_assurance_capabilities::REDTEAM_ATTACK_AXES.len();
    let axis_rate = if axis_total == 24 {
        axis_pass as f64 / axis_total as f64
    } else {
        0.0
    };

    let authority_total = SUPPORTED_MODULES.len() + UNSUPPORTED_PROBES.len();
    let authority_rate = (authority_pass + UNSUPPORTED_PROBES.len()) as f64 / authority_total as f64;

    json!({
        "use_mutant_for_optimizer_orchestrator": use_mutant,
        "kpi": {
            "diagnostic_dispatch_ok_rate": dispatch_pass as f64 / n,
            "diagnostic_passed_flag_true_rate": passed_flag_pass as f64 / n,
            "expected_equals_observed_fixture_outcomes_rate": outcomes_pass as f64 / n,
            "implementation_readiness_complete_rate": readiness_pass as f64 / n,
            "zero_authority_lock_coverage_rate": zero_auth_pass as f64 / n,
            "result_digest_byte_stable_across_replays_rate": digest_replay_pass as f64 / n,
            "positive_or_negative_control_counts_present_rate": counts_present_pass as f64 / n,
            "unsupported_module_id_fail_closed_rate": unsupported_rate,
            "attack_axis_coverage_complete_rate": axis_rate,
            "authority_envelope_preservation_rate": authority_rate,
        },
        "all_nine_gates_pass": dispatch_pass as f64 / n >= 1.0
            && passed_flag_pass as f64 / n >= 1.0
            && outcomes_pass as f64 / n >= 1.0
            && readiness_pass as f64 / n >= 1.0
            && zero_auth_pass as f64 / n >= 1.0
            && digest_replay_pass as f64 / n >= 1.0
            && counts_present_pass as f64 / n >= 1.0
            && unsupported_rate >= 1.0
            && axis_rate >= 1.0
            && authority_rate >= 1.0,
        "records": per_module,
    })
}

fn backdoor_request() -> OptimizerAuthorizationRequestV1 {
    optimizer_request(
        vec![OptimizerObjectiveRequestV1 {
            objective_id: BACKDOOR_OBJECTIVE_ID.into(),
            module_id: ENVELOPE_GATES.into(),
            section: "objective_values".into(),
            path: "score".into(),
        }],
        Vec::new(),
    )
}

fn main() {
    // Confirm the backdoor objective_id is absent from every one of the 12 real
    // fixtures (so the mutant is provably untested by the fixture corpus).
    let fixtures = real_fixture_corpus();
    let backdoor_id_in_any_fixture = fixtures
        .iter()
        .any(|f| f.request.objectives.iter().any(|o| o.objective_id == BACKDOOR_OBJECTIVE_ID));

    // Sanity: my hand-copied real-logic reproduction matches the diagnostic produced
    // by calling the REAL compiled deterministic_control_diagnostic("amphora-optimizer-orchestrator").
    let probe_real_copy = build_optimizer_orchestrator_diagnostic(false);
    let real_dispatch =
        amphora_assurance_capabilities::deterministic_control_diagnostic(OPTIMIZER_ORCHESTRATOR)
            .expect("real dispatch ok");
    let probe_copy_matches_real_dispatch = probe_real_copy.expected_fixture_outcomes
        == real_dispatch.expected_fixture_outcomes
        && probe_real_copy.observed_fixture_outcomes == real_dispatch.observed_fixture_outcomes
        && probe_real_copy.passed == real_dispatch.passed;

    let report_real = compute_report(false);
    let report_mutant = compute_report(true);

    let policy = quarantined_optimizer_policy();
    let req = backdoor_request();
    let real_on_backdoor_input = authorize_optimizer_request(&req, &[], &policy);
    let mutant_on_backdoor_input = mutant_authorize_optimizer_request(&req, &[], &policy);

    let out = json!({
        "schema": "amphora-redteam-audit.t11-optimizer-quarantine-coverage-probe.v1",
        "backdoor_objective_id": BACKDOOR_OBJECTIVE_ID,
        "backdoor_id_absent_from_all_12_real_fixtures": !backdoor_id_in_any_fixture,
        "probe_real_logic_copy_matches_real_compiled_dispatch": probe_copy_matches_real_dispatch,
        "report_with_real_authorize_optimizer_request": report_real,
        "report_with_mutant_backdoored_authorize_optimizer_request": report_mutant,
        "backdoor_input": &req,
        "real_authorize_optimizer_request_on_backdoor_input": match &real_on_backdoor_input {
            Ok(v) => serde_json::to_value(v).unwrap(),
            Err(e) => json!({"error": e}),
        },
        "mutant_authorize_optimizer_request_on_backdoor_input": match &mutant_on_backdoor_input {
            Ok(v) => serde_json::to_value(v).unwrap(),
            Err(e) => json!({"error": e}),
        },
        "real_stays_quarantined_on_backdoor_input": real_on_backdoor_input
            .as_ref()
            .is_ok_and(|v| !v.ranking_performed && !v.usable_by_optimizer && !v.authority_upgrade),
        "mutant_escalates_on_backdoor_input": mutant_on_backdoor_input
            .as_ref()
            .is_ok_and(|v| v.ranking_performed && v.usable_by_optimizer && v.authority_upgrade && v.solver_invoked),
    });
    println!("{}", serde_json::to_string(&canonicalize(&out)).unwrap());
}
