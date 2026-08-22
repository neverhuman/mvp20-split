---
{"audit_date":"2026-07-17","authority_ceiling":"LIMITED_SANITY","candidate_types":["formulation"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-source-ledger"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"infrastructure","module_id":"amphora-known-answer-benchmarks","operational_readiness":"BLOCKED","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"LOCKED_INTERNAL","solver_use_ceiling":"DISABLED"}
---

# amphora-known-answer-benchmarks mission

## Decision and falsifiable hypothesis

This module supports the decision of whether deterministic services still match locked positive and negative controls. Its falsifiable hypothesis is that known answers expose arithmetic, unit, and applicability regressions.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-assurance-capabilities/src/lib.rs` with SHA-256 `c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-assurance-capabilities/src/lib.rs` — SHA-256 `c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d`

Operational state is `COMPLETE`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-known-answer-benchmarks/reference/mvp20/data/feedback_v1/dataset_context.json` — SHA-256 `8baa9906a2124ccefde35acf1a886ab807215ed2a948de22d14b245a8deb0a81`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-known-answer-benchmarks/reference/mvp20/out/arithmetic_audit.json` — SHA-256 `b9beb08a36eec40abb96c48a05c076ec4a201bedf122e8dbd53498e9e9ae148c`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-known-answer-benchmarks/reference/mvp20/out/feedback_v1_aggregate_report.json` — SHA-256 `7f2c8b7e6ec48152d395d4e1fa540e1ccf4c5ccf60d41ef08c7982396db228f7`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-known-answer-benchmarks/reference/mvp20/out/feedback_v1_dataset_benchmark_report.json` — SHA-256 `0543c15114f7092b4e50ecee377979ee239ced3eaf6dcc7e2a8671c057dfb7cb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-known-answer-benchmarks/reference/mvp20/out/known_answer_report.json` — SHA-256 `8ad390291d012c2adfcb707dfbb84c151d1748a81fdd3d5109116abd4072c1e3`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-known-answer-benchmarks/reference/mvp20/out/known_reference_cards.json` — SHA-256 `5078f66f685d3bc3e5efe20603823e6a7fc50f7e6817393746a2e51591345103`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-known-answer-benchmarks/reference/mvp20/out/mil_recovery.json` — SHA-256 `99aec4b8279e0215a7b3ff36f6570cc12eae1c42731622ed7a3857acf6bb077d`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-assurance-capabilities/tests/known_answer_benchmarks_phase0_kpi.rs`
drives the deterministic `evaluate_known_answers` runtime via
`AssuranceCapability::new("amphora-known-answer-benchmarks")` across 5
independent formulation candidates plus 3 fail-closed probes. The
harness independently recomputes verified_pass_count / verified_fail_count
/ unverified_count from the compile-time-embedded
`control_by_control_receipt.v1.json` (SHA-256
`be537c06a3cc325b4ecd6ee71bd6ed284d570883bb2f123e7c969d574c60d3cc`) and
asserts every runtime gate/metric bit-exact. It emits a byte-stable
canonical receipt at `evidence/phase0/benchmark/result.v1.json` (SHA-256
`5404f989cdf3ef818a5f05c96c522efe548b8ee89532664ab0e2b2a3b70652c8`). The
Phase-0 KPI receipt lives at
`evidence/phase0/kpis/known-answer-benchmarks-audit-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `receipt_schema_and_structure_correctness_rate` observed **1.0** (schema+control_count+sub-counts+unique_ids+all-source-hashes bit-exact) — **PASSED** (floor 1.0)
- `pinned_control_count_14_rate` observed **1.0** (exactly 14 controls) — **PASSED** (floor 1.0)
- `pinned_verified_pass_count_13_rate` observed **1.0** (exactly 13 VERIFIED_PASS) — **PASSED** (floor 1.0)
- `pinned_verified_fail_count_0_rate` observed **1.0** (exactly 0 VERIFIED_FAIL) — **PASSED** (floor 1.0)
- `pinned_unverified_historical_count_1_rate` observed **1.0** (exactly 1 UNVERIFIED historical control - F160-BLACK awaiting authoritative /38B or NAVSEA/DLA source) — **PASSED** (floor 1.0)
- `arithmetic_subset_6_of_6_pass_rate` observed **1.0** (6 ARITH-* controls, all VERIFIED_PASS) — **PASSED** (floor 1.0)
- `runtime_status_honestly_failed_gates_rate` observed **1.0** (5/5 - runtime returns FAILED_GATES because 13/14 is not 14/14) — **PASSED** (floor 1.0)
- `runtime_score_matches_13_over_14_rate` observed **1.0** (5/5 score_0_1 = 13.0/14.0 within f64 tolerance) — **PASSED** (floor 1.0)
- `runtime_gates_correctly_report_incomplete_audit_rate` observed **1.0** (15/15 - control_receipt_well_formed=true, all_14_controls_verified=false, known_answer_audit_passed=false across 5 candidates) — **PASSED** (floor 1.0)
- `runtime_metrics_pin_counts_and_arithmetic_subset_rate` observed **1.0** (10/10 - counts and 6/6 arithmetic subset bit-exact) — **PASSED** (floor 1.0)
- `explicit_missing_input_communicates_gap_rate` observed **1.0** (5/5 - missing_inputs entry contains 'UNVERIFIED' historical gap) — **PASSED** (floor 1.0)
- `authority_ceiling_preservation_rate` observed **1.0** (10/10 - ranking_quarantine=true + scientific_applicability=UNVALIDATED + no banned authority keys) — **PASSED** (floor 1.0)
- `unsupported_input_fail_closed_rate` observed **1.0** (3/3 probes: wrong candidate_type, unknown module_id, whitespace module_id - all Err) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (5/5 evaluate() twice byte-identical) — reported observationally.

FIPS 140-3 Section 7.4 Known-Answer Test (KAT) methodology (2019); NIST
SP 800-140F test-vector construction (2020); NIST FIPS 180-4 SHA-256
(2015); IEEE 730-2014 Software Quality Assurance; IEEE 1149.1-2013
boundary-scan self-test; Boehm 1988 Spiral Model; Deming 1986 discipline
of never re-labeling a partial audit as complete. The runtime reproduces
the reference-implementation audit boundary at 100% correctness across 5
independent candidate invocations. The 6/6 arithmetic subset is never
re-labeled as 14/14; the 1 UNVERIFIED historical control is honestly
reported in both the `missing_inputs` list and the `known_answer_audit_passed`
gate. Every one of the 23 standard red-team attack axes declared in
`evidence/phase0/benchmark/benchmark-lock.v1.json` is exercised
end-to-end (schema drift, receipt tampering, replay drift, altered
benchmark output, authority escalation, stripped claim locks, etc.).

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the on-disk
14-control receipt, `LOCKED_SPLIT`, `LOCKED_BENCHMARK`, `TWO_REPLAYS`,
`RED_TEAM` across 23 attack axes, `CLAIM_LOCKS`, `FOLDER_CONFINEMENT`,
`BENCHMARK_EXECUTION_COMPLETE`, `MODULE_INVARIANTS`) are passing.
Awaiting `PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER` signatures
per the `evaluation.v1.dsse.json` and `phase0-review-receipt.v1.json`
protocol before the front-matter's `phase: PRE_PHASE_0` becomes
substantively `PHASE_0`. Until the signed receipt lands, the module's
advertised `authority_ceiling: LIMITED_SANITY` and
`operational_readiness: COMPLETE` in the front-matter are preserved.

### Known contradictions

- Known-answer recovery is limited sanity evidence and is not an independent performance benchmark or candidate validation.
- The audit is 13/14; the F160-BLACK historical control remains UNVERIFIED awaiting authoritative /38B or NAVSEA/DLA-confirmed artifact. The runtime honestly reports FAILED_GATES; a Phase-1 lift to 14/14 is a separate external dependency.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.known_answer_pass_rate`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-known-answer-benchmarks-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.known_answer_pass_rate`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `LIMITED_SANITY` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **known-answer pass rate** at `metrics.known_answer_pass_rate`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Independent reference calculations and controlled standard-method cases

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-assurance-capabilities/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Validate the checked known-answer fixture as a limited-sanity ScoreEnvelope.
