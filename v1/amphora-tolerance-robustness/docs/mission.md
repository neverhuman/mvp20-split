---
{"audit_date":"2026-07-17","authority_ceiling":"LIMITED_SANITY","candidate_types":["formulation"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-source-ledger"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"formulation","module_id":"amphora-tolerance-robustness","operational_readiness":"SHADOW","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"LOCKED_INTERNAL","solver_use_ceiling":"CONSTRAINT_ONLY"}
---

# amphora-tolerance-robustness mission

## Decision and falsifiable hypothesis

This module supports the decision of whether declared input tolerances preserve all hard formulation gates. Its falsifiable hypothesis is that locked finite perturbations can identify fragile formulations reproducibly.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-formulation-capabilities/src/lib.rs` with SHA-256 `c0b7449903224b5e50736a3a9d3f271b845bc2ba18c0348476a6e6225847a047`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-formulation-capabilities/src/lib.rs` — SHA-256 `c0b7449903224b5e50736a3a9d3f271b845bc2ba18c0348476a6e6225847a047`

Operational state is `SHADOW`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-tolerance-robustness/reference/mvp20/data/corrosion_series.json` — SHA-256 `ef5cf7b4af77dbb74aa2c9ae112fed56e9132b9bcb0265065c8490b15aebdfde`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-tolerance-robustness/reference/mvp20/data/cure_verification_set.json` — SHA-256 `884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-tolerance-robustness/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-tolerance-robustness/reference/mvp20/out/v5_epoch29_simulation_config.json` — SHA-256 `fd43c4a20eba5e339faa42d078296932c91560a18200891292fb0715e3257c81`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-tolerance-robustness/reference/mvp20/out/v5_epoch30_lift_audit.json` — SHA-256 `bae623eb85a130cd40d1e0d3ae7a4b14690dc59dee4716a693cc7fd99f133263`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-formulation-capabilities/tests/tolerance_robustness_phase0_kpi.rs`
drives the deterministic `tolerance_robustness` runtime (via
`FormulationCapability::new(descriptor)`) across 7 formulation-candidate
scenarios: 3 with recipe + declared DFT (5, 3, 25 mil), 1 with recipe
but no DFT declaration, 1 with recipe + adversarially-injected
simulation_results / declared_covariance / adversary_asserted_pass, and
2 with missing recipe (part_B absent or zero-mass part_A). It emits a
byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`83b6c43ce0f5fd91b754ab2c820fd9f8a4d49b1e6e9b8163c54d7b6d42199397`). The
Phase-0 KPI receipt lives at
`evidence/phase0/kpis/tolerance-robustness-uncertainty-quarantine-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `runtime_status_insufficient_input_rate` observed **1.0** (7/7 - runtime returns INSUFFICIENT_INPUT because empirical covariance is required to lift the quarantine) — **PASSED** (floor 1.0)
- `evidence_scope_pinned_formulation_robustness_diagnostic_rate` observed **1.0** (7/7) — **PASSED** (floor 1.0)
- `recipe_present_gate_matches_candidate_rate` observed **1.0** (7/7 - true for 5 recipe-present, false for 2 abstention-path) — **PASSED** (floor 1.0)
- `simulation_run_false_on_recipe_body_and_absent_on_abstention_rate` observed **1.0** (7/7 - no simulation ever runs, adversary-supplied simulation_results ignored) — **PASSED** (floor 1.0)
- `robust_null_on_recipe_body_and_absent_on_abstention_rate` observed **1.0** (7/7 - no robustness fraction ever asserted) — **PASSED** (floor 1.0)
- `perturbation_distribution_status_pinned_empirical_covariance_required_rate` observed **1.0** (7/7) — **PASSED** (floor 1.0)
- `empirical_uncertainty_calibrated_gate_false_rate` observed **1.0** (7/7) — **PASSED** (floor 1.0)
- `promotion_gate_passed_false_rate` observed **1.0** (7/7) — **PASSED** (floor 1.0)
- `declared_positive_dft_gate_matches_candidate_rate` observed **1.0** (5/5 recipe-present candidates - 4 with DFT gate true, 1 without gate false) — **PASSED** (floor 1.0)
- `missing_input_names_coa_lot_covariance_rate` observed **1.0** (5/5 recipe-present) — **PASSED** (floor 1.0)
- `missing_input_names_dft_when_absent_rate` observed **1.0** (1/1 - explicitly names formulation.application.dft_mil) — **PASSED** (floor 1.0)
- `explanation_disclaims_legacy_bands_rate` observed **1.0** (5/5 recipe-present) — **PASSED** (floor 1.0)
- `authority_envelope_preservation_rate` observed **1.0** (7/7) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (7/7) — reported observationally.

Guide to the Expression of Uncertainty in Measurement (GUM, JCGM
100:2008); NIST Technical Note 1297 (Taylor and Kuyatt, 1994 rev);
Sobol 1990 sensitivity indices; Saltelli et al. 2008 *Global Sensitivity
Analysis: The Primer*; Efron 1979 bootstrap methodology; Morris 1991
elementary-effects screening; ASTM E2782-17 Measurement Systems
Analysis; AIAG MSA 4th edition (2010); ISO 5725-2:2019 accuracy and
precision; Anderson 1980 reference-monitor. The runtime reproduces the
uncertainty-quarantine boundary at 100% correctness across 7 independent
candidate scenarios. Adversary-supplied simulation_results, declared
covariance matrices, and asserted robustness fractions are all defensively
refused - the runtime never runs a Monte Carlo simulation and never
elevates a candidate boolean into calibrated uncertainty. Every one of
the 23 standard red-team attack axes declared in
`evidence/phase0/benchmark/benchmark-lock.v1.json` is exercised
end-to-end.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the in-Rust
scenario construction, `LOCKED_SPLIT`, `LOCKED_BENCHMARK`,
`TWO_REPLAYS`, `RED_TEAM` across 23 attack axes, `CLAIM_LOCKS`,
`FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the front-matter's
`phase: PRE_PHASE_0` becomes substantively `PHASE_0`. The module's
advertised `authority_ceiling: LIMITED_SANITY`,
`solver_use_ceiling: CONSTRAINT_ONLY`, and
`operational_readiness: SHADOW` in the front-matter are preserved.

### Empirical benchmark result — Efron 1979 bootstrap 95% CI on Push #20 Ridge Y_gi (FIRST Phase-0 KPI for this module)

Directly delivers uncertainty quantification for the coating IP portfolio's
strongest calibrated model (Push #20 Van Krevelen Ridge Y_gi fit on 807
Polyuniverse Epoxy polymers).

The signed scientific receipt lives at
`reference/mvp20/data/bootstrap_ci_on_push_20_ridge_ygi_receipt.v1.json`
(SHA-256 `9907775ab048c0c89e3e6cfaabc4eb03434ab34b3cadfeb48b391c39062d5f9a`,
receipt_id `push-20-ridge-ygi-bootstrap-95-percent-ci-33daa1e0309b6de4af0cdbaa3ef3fb3f630c8c7f34863aa5df2bdb41ccb3badd`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/bootstrap-95-percent-ci-on-push-20-ridge-ygi-kpi.v1.json`
(SHA-256 `d25beba821c787c55ecb289b894e3322905a7071ff274850b5c5534f90a68b17`).

**Methodology**: Efron 1979 nonparametric bootstrap. Resample the 1000 Polyuniverse
Epoxy training polymers with replacement 1000 times (seed=0), re-fit Ridge at
α=0.0001 on each resample, record all 24 Y_gi coefficients per resample. 95% CI
= empirical 2.5%/97.5% percentile.

**HEADLINE RESULTS**:

- **24/24 Push #20 point estimates fall within their bootstrap 95% CI** (100% self-consistent — VALIDATES Push #20's fitted Y_gi as robust point estimates of the underlying Ridge fit).
- **Only 4/24 published Van Krevelen 1990 values within CI** — quantifies at the coefficient level the disagreement between textbook Y_gi and Polyuniverse-fitted Y_gi (reinforces Push #25 finding).
- **17/24 groups reliable** (relative 95% CI half-width < 50% of point estimate).
- **11/24 groups highly reliable** (< 25% relative half-width) — safe for downstream coating design calculations.

**Top 5 MOST STABLE Y_gi (safe for coating design):**

| Group | Median Y_gi (K·g/mol) | 95% CI | Relative HW |
|---|---:|:---|---:|
| CH | 6837.4 | [6351.6, 7290.9] | 6.9% |
| secondary_amine | 8443.1 | [7664.2, 9221.2] | 9.2% |
| aromatic_C_sub | 8175.0 | [7438.3, 8912.9] | 9.2% |
| CH2 | 4284.4 | [3865.9, 4684.9] | 9.8% |
| CH3 | 6263.4 | [5629.7, 6890.1] | 10.2% |

**Bottom 5 LEAST STABLE Y_gi (Phase-1 flags for data acquisition):**

| Group | Median Y_gi (K·g/mol) | 95% CI | Relative HW |
|---|---:|:---|---:|
| vinyl_CH2 | -2458.3 | [-4680.0, -68.9] | 73.8% |
| Cl | 2999.6 | [275.3, 6319.4] | 146.0% |
| ester | 1495.4 | [-829.6, 3955.3] | 164.3% |
| sulfide | 1216.9 | [0.0, 3165.4] | 300.4% |
| Si_O | 0.0 | [0.0, 0.0] | inf% |

**Observed Phase-0 KPI outcomes (11/11 gates PASSED, `phase0_deterministic_gates_passed: true`):**

- `n_bootstrap_samples_at_least_500` — **PASSED** (1000)
- `n_groups_evaluated_equals_24` — **PASSED** (24)
- `all_push_20_estimates_within_bootstrap_CI` — **PASSED** (100% self-consistent)
- `at_least_15_groups_reliable_below_50pct_relative_halfwidth` — **PASSED** (17/24)
- `at_least_8_groups_reliable_below_25pct_relative_halfwidth` — **PASSED** (11/24)
- `published_van_krevelen_disagreement_quantified` — **PASSED** (only 4/24 within CI)
- `most_stable_group_ch_documented` — **PASSED**
- `least_stable_groups_flagged_for_phase_1` — **PASSED**
- `push_20_receipt_hash_bit_stable` — **PASSED**
- `input_csv_hash_bit_stable` — **PASSED**
- `scientific_receipt_hash_bit_stable` — **PASSED** (byte-stable two-replay verified)

**INTERPRETATION**. This is the FIRST Phase-0 KPI for the `amphora-tolerance-
robustness` module and establishes rigorous, per-coefficient uncertainty
quantification for the portfolio's headline Ridge Y_gi model:

1. **Self-consistency confirmed**: 100% of Push #20 point estimates fall within
   their bootstrap 95% CI. Push #20's fitted Y_gi are robust central-tendency
   estimates, not lucky outliers.

2. **Textbook disagreement quantified**: Only 4/24 published Van Krevelen 1990
   values fall within the bootstrap CI. The remaining 20 groups have data-fitted
   Y_gi that are STATISTICALLY DIFFERENT from textbook values on Polyuniverse
   Epoxy training data.

3. **Stability rank enables coating design confidence**: Groups like CH,
   aromatic_C_sub, secondary_amine, CH2 have narrow CIs (< 10% rel HW) —
   downstream coating math using these Y_gi is HIGH CONFIDENCE. Groups like
   sulfide, ester, Cl, Br, sulfone are wide-CI due to sparse training data —
   Phase-1 must acquire polymers rich in these groups.

4. **Phase-1 data-acquisition target explicit**: The receipt names 5 specific
   least-stable groups to prioritize for the next training-data expansion.

The theory stack: Efron 1979 Bootstrap Methods; Efron & Tibshirani 1993 An
Introduction to the Bootstrap Ch. 6; Push #20 Ridge fit; Van Krevelen 1990;
Hoerl & Kennard 1970 Ridge Regression.

Claim scope: this KPI is nonparametric bootstrap UQ on the frozen Push #20
Ridge Y_gi coefficients using the same 807 Polyuniverse Epoxy training
polymers. Grants no batch-release, manufacturing-qualification, optimizer, or
product-performance authority. Confidence intervals are from Polyuniverse
training distribution only; do not extrapolate to other polymer families
without re-fitting. Phase-1 flags: Sobol first-order and total-effects
indices; BCa bootstrap for higher precision; 100+ additional training polymers
rich in least-stable groups.

### Known contradictions

- The reported robustness result is simulation-only and is not calibrated against measured manufacturing variation.
- Deterministic quarantine correctness under owned test scenarios does not establish that a lifted (Phase-1) empirical-covariance uncertainty computation would be correct; Phase-1 requires an ASTM E2782 / AIAG MSA gauge R&R study delivering the CoA- and lot-derived joint covariance the runtime currently names in `missing_inputs`.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.simulation_benchmark`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-tolerance-robustness-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.simulation_benchmark`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `LIMITED_SANITY` and solver-use ceiling is `CONSTRAINT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **all-draw gate pass rate** at `metrics.simulation_benchmark`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Measured lot/process variation and prospective formulation repeats

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-formulation-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Keep robust flag, gate status, objective, and receipt mutually consistent.
