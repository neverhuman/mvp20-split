---
{"audit_date":"2026-07-17","authority_ceiling":"EVIDENCE_ONLY","candidate_types":["evidence_package"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-model-card-authority"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"infrastructure","module_id":"amphora-optimizer-orchestrator","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"DISABLED"}
---

# amphora-optimizer-orchestrator mission

## Decision and falsifiable hypothesis

This module supports the decision of which centrally authorized objectives and constraints may reach Pareto selection. Its falsifiable hypothesis is that identity-bound policy can prevent every unauthorized row from ranking.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-engine/src/lib.rs` with SHA-256 `6b007d7d9d0acd453aac5e7c300ab16fb9a7253337c722cc4cffe0be23db62b4`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-engine/src/lib.rs` — SHA-256 `6b007d7d9d0acd453aac5e7c300ab16fb9a7253337c722cc4cffe0be23db62b4`
- `amphora-core/src/lib.rs` — SHA-256 `20fa48ab7e758ec7ff5c562cceb426466193a73597f66a708f5455bbc440ad86`
- `amphora-assurance-capabilities/src/diagnostics.rs` — SHA-256 `bab349d7039ab3d323c3313f3edc6680932278842d6e0512d9d929dbccaf987a`

Operational state is `SHADOW`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- None discovered. No checked-in dataset, output artifact, or non-README fixture was discovered for this module.

No checked-in dataset, output artifact, or non-README fixture was discovered for this module. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-assurance-capabilities/tests/optimizer_orchestrator_phase0_kpi.rs`
drives the deterministic `authorize_optimizer_request` gate
(`amphora-core/src/lib.rs`) across 5 positive-control scenarios and 26
fail-closed probes distributed across the six module-specific attack
axes (OBJECTIVE_CONSTRAINT_INJECTION, UNKNOWN_OBJECTIVE_PATH_OPERATOR,
DUPLICATE_SCORE_ENVELOPE, MISSING_OPTIMIZER_CLAIM_LOCK,
FAILED_OR_NO_AUTHORITY_SCORE, SOLVER_RANKING_ESCALATION). All 29
registered modules of `quarantined_optimizer_policy` are in scope. The
harness emits a byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`e1d95b6b338b10d5999d9d0af4e5b2e8f635eab72a888942e9a77439382eba17`). The
Phase-0 KPI receipt lives at
`evidence/phase0/kpis/optimizer-orchestrator-authorization-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `authorization_ok_rate` observed **1.0** (5/5 positive-control scenarios return Ok) — **PASSED** (floor 1.0)
- `authorization_status_no_eligible_objectives_rate` observed **1.0** (5/5 OptimizerAuthorizationV1.status == 'NO_ELIGIBLE_OBJECTIVES' bit-exact) — **PASSED** (floor 1.0)
- `quarantine_output_locked_rate` observed **1.0** (5/5 ranking_performed=false, solver_invoked=false, usable_by_optimizer=false) — **PASSED** (floor 1.0)
- `authority_and_counts_locked_rate` observed **1.0** (5/5 authority_upgrade=false, candidate_created_evidence=false, hard_constraints_passed=true, eligible_objective_count=0, objective_values empty) — **PASSED** (floor 1.0)
- `objective_constraint_injection_fail_closed_rate` observed **1.0** (3/3 probes: candidate-source with objectives, candidate-source with objectives+constraint, unknown request_source string - all Err) — **PASSED** (floor 1.0)
- `unknown_objective_path_operator_fail_closed_rate` observed **1.0** (5/5 probes: operator 'contains', operator empty, objective section not objective_values, constraint section not gates, objective empty path - all Err) — **PASSED** (floor 1.0)
- `duplicate_score_envelope_fail_closed_rate` observed **1.0** (3/3 probes: two envelopes same module_id, two objectives same id, two constraints same id - all Err) — **PASSED** (floor 1.0)
- `missing_optimizer_claim_lock_fail_closed_rate` observed **1.0** (3/3 probes: envelope missing no_ranking_authority, envelope no_optimizer_authority=false, policy required_claim_locks trimmed - all Err) — **PASSED** (floor 1.0)
- `failed_or_no_authority_score_fail_closed_rate` observed **1.0** (7/7 probes: envelope FAILED_GATES with matching constraint, ranking_eligible=true, authority_tier RANKING/OPTIMIZER/empty, solver_use_ceiling unsupported, module_id not in registered - all Err) — **PASSED** (floor 1.0)
- `solver_ranking_escalation_fail_closed_rate` observed **1.0** (7/7 probes: policy ranking_enabled/solver_enabled/authority_expansion_allowed=true, decision_use_ceiling not AUDIT_ONLY, registered_modules mutated, request/policy schema wrong - all Err) — **PASSED** (floor 1.0)
- `authority_envelope_preservation_rate` observed **1.0** (5/5 serialized OptimizerAuthorizationV1 payloads contain no batch_release/qualified/authorized_by/manufacturing_qualification/release_authority key) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (5/5 authorize_optimizer_request twice byte-identical) — reported observationally.

Constrained-optimization authorization stack (Karush 1939 / Kuhn-Tucker
1951 KKT conditions; Nemhauser & Wolsey 1988 Integer & Combinatorial
Optimization; Boyd & Vandenberghe 2004 Convex Optimization; Bertsekas
1999 Nonlinear Programming) combined with reference-monitor policy
enforcement (Anderson 1980; ISO/IEC 27001:2022 Annex A.5.15; NIST SP
800-53 Rev. 5 AC-3 & AC-6; NIST SP 800-207 Zero Trust; OWASP ASVS 4.0
V4/V13). The runtime reproduces the deny-by-default authorization
boundary at 100% correctness and every one of the 6 module-specific
attack axes declared in `evidence/phase0/benchmark/benchmark-lock.v1.json`
is exercised end-to-end by 26 dedicated fail-closed probes.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the
in-Rust policy-arithmetic construction, `LOCKED_SPLIT`,
`LOCKED_BENCHMARK`, `TWO_REPLAYS`, `RED_TEAM` across 29 attack axes,
`CLAIM_LOCKS`, `FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the front-matter's
`phase: PRE_PHASE_0` becomes substantively `PHASE_0`. Until the signed
receipt lands, the module's advertised `operational_readiness: SHADOW`
and `solver_use_ceiling: DISABLED` in the front-matter are preserved.

### Known contradictions

- Dependency-aware ranking can enforce authority but cannot repair unvalidated scientific objectives or create missing evidence.
- Deterministic authorization correctness under owned test scenarios does not establish that an unlocked ranking or solver invocation would remain correct; Phase-1 promotion beyond AUDIT_ONLY solver ceiling requires an independent adversarial policy corpus.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `evidence_package` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `objective_values.pareto_ready_rows`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-optimizer-orchestrator-example", "candidate_type": "evidence_package", "evidence_refs": {"evidence_package": {}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `objective_values.pareto_ready_rows`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **unauthorized rank rate** at `objective_values.pareto_ready_rows`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Centrally authorized validated objectives and Rust/Python decision parity fixtures

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-engine/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Reject unknown modules, blocked locks, and unauthorized objective escalation.
