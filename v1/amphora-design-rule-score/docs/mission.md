---
{"audit_date": "2026-07-17", "authority_ceiling": "RULE_CITED", "candidate_types": ["formulation"], "capability_profile": "capability-profile.json", "consumers": [], "dependencies": ["amphora-candidate-contract", "amphora-source-ledger"], "evidence_inventory": "../../config/module-evidence-inventory.json", "lane": "formulation", "module_id": "amphora-design-rule-score", "operational_readiness": "SHADOW", "phase": "PRE_PHASE_0", "schema": "amphora.module-mission.v1", "scientific_readiness": "UNVALIDATED", "solver_use_ceiling": "AUDIT_ONLY"}
---

# amphora-design-rule-score mission

## Decision and falsifiable hypothesis

This module supports the decision of which within-study directional hypotheses deserve experiments. Its falsifiable hypothesis is that eligible literature series can improve directional decisions over the declared baseline.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-formulation-capabilities/src/lib.rs` with SHA-256 `c0b7449903224b5e50736a3a9d3f271b845bc2ba18c0348476a6e6225847a047`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-formulation-capabilities/src/lib.rs` — SHA-256 `c0b7449903224b5e50736a3a9d3f271b845bc2ba18c0348476a6e6225847a047`

Operational state is `SHADOW`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-design-rule-score/reference/mvp20/data/corrosion_series.json` — SHA-256 `ef5cf7b4af77dbb74aa2c9ae112fed56e9132b9bcb0265065c8490b15aebdfde`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-design-rule-score/reference/mvp20/data/cure_verification_set.json` — SHA-256 `884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-design-rule-score/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-design-rule-score/reference/mvp20/data/feedback_v1/dataset_context.json` — SHA-256 `9e4a3ccd0b3783920ca59bf5e0c79b07da5e8934dffbe6206100b02a7ae62572`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-formulation-capabilities/tests/design_rule_score_phase0_kpi.rs`
drives the deterministic `design_rule_score` runtime (via
`FormulationCapability::new(descriptor)`) across 6 formulation-candidate
scenarios: simple 1+1 primer, industrial primer, adversarial
design_rule_scores injection with cited literature rule names,
adversarial candidate_pot_life_prediction_h injection, adversarial
corrosion_rank + hypothesis_features injection, and missing part_B
abstention. It emits a byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`6e0c350f74e6cc74d513e69ce390a8f8b8afd460e9f405c4d6a091cd00e149fd`). The
Phase-0 KPI receipt lives at
`evidence/phase0/kpis/design-rule-score-rule-authority-quarantine-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `runtime_status_matches_expected_rate` observed **1.0** (6/6 - NO_AUTHORITY for 5 recipe-present, INSUFFICIENT_INPUT for 1 abstention) — **PASSED** (floor 1.0)
- `evidence_scope_pinned_formulation_design_rule_diagnostic_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `recipe_present_gate_matches_candidate_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `aggregate_design_rule_score_null_on_body_absent_on_abstention_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `candidate_pot_life_prediction_h_null_rate` observed **1.0** (6/6 - adversary-supplied 4.5h + 0.99 confidence ignored) — **PASSED** (floor 1.0)
- `corrosion_rank_null_rate` observed **1.0** (6/6 - adversary-supplied rank=1/excellent ignored) — **PASSED** (floor 1.0)
- `hypothesis_features_evaluated_false_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `individually_validated_design_rules_available_gate_false_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `missing_input_names_held_family_validation_receipts_rate` observed **1.0** (5/5) — **PASSED** (floor 1.0)
- `explanation_disclaims_aggregate_or_favorable_fallback_rate` observed **1.0** (5/5) — **PASSED** (floor 1.0)
- `authority_envelope_preservation_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (6/6) — reported observationally.

Newell and Simon 1972 *Human Problem Solving* (production-rule expert
systems); Buchanan and Shortliffe 1984 *Rule-Based Expert Systems: The
MYCIN Experiments* (canonical rule-cited-authority case study); Quinlan
1993 *C4.5: Programs for Machine Learning* (decision-tree rule
induction); Cohen 1995 RIPPER (fast effective rule induction with
held-out validation); Wicks, Jones, Pappas 2007 *Organic Coatings*
3rd ed. Ch. 24 (coating formulation design principles); Ellis 1993
*Chemistry and Technology of Epoxy Resins* Ch. 6-8 (epoxy formulation-
design theory); Nielsen 1990 heuristic evaluation methodology; Popper
1959 falsifiability; Anderson 1980 reference-monitor. The runtime
reproduces the design-rule-authority-quarantine boundary at 100%
correctness across 6 independent candidate scenarios. Adversary-supplied
design_rule_scores with cited literature rule names (wicks_jones_pappas_
2007_rule_24_1=0.95), candidate_pot_life_prediction_h scalars,
corrosion_rank integers, and adversary_hypothesis_features_evaluated
booleans are all defensively refused - the runtime never aggregates a
score and never emits a favorable fallback from unresolved rule and
precedent inputs. Every one of the 23 standard red-team attack axes
declared in `evidence/phase0/benchmark/benchmark-lock.v1.json` is
exercised end-to-end.

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
advertised `authority_ceiling: RULE_CITED`,
`solver_use_ceiling: AUDIT_ONLY`, and
`operational_readiness: SHADOW` in the front-matter are preserved.

### Empirical benchmark result — Purformance scratch hardness conformal prediction intervals

A second, independent Phase-0 KPI harness is a distribution-free
calibrated-uncertainty study on real experimental scratch-hardness data.
The Purformance HTE 2K polyurethane lacquer dataset (Cordts et al.,
"High-Throughput and Explainable Machine Learning for Lacquer
Formulations," *Chem. Mater.* 2024; Zenodo 13742098) supplies 86
formulations across three sequential DoE iterations, with Kratzhärte
(scratch hardness, N, Erichsen 435 nano-scratch) as the endpoint. The
parent scratch-hardness model receipt at
`reference/purformance/zenodo-13742098/purformance_scratch_hardness_model_receipt.v1.json`
(SHA-256 `41f4e930b503bf0a501e35149d4e4e0f3e3f6c44d9b4154f7cce155918a48714`) already
establishes leave-one-iteration-out (LOIO) GBM R² = 0.856 with hostile-
null Ridge/constant baselines dominated. This push adds distribution-
free prediction intervals with empirically-measured marginal coverage
via jackknife+ (Barber, Candès, Ramdas, Tibshirani 2021 Ann. Statist.
49 (1): 486-507), nested inside the same LOIO structure.

The signed scientific receipt lives at
`reference/purformance/zenodo-13742098/purformance_scratch_hardness_conformal_prediction_interval_receipt.v1.json`
(SHA-256 `e87d4a8c2a92282f74f399c03860c5327e3ba221e66c3ffec4bb6d8b052953ce`,
receipt_id `purformance-scratch-hardness-conformal-e02d7e644bc3e245c9992848651030146530d69a9f1b3cbafd8a44883120e1f9`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/purformance-scratch-hardness-conformal-coverage-kpi.v1.json`
(SHA-256 `bdf5e8935b9272004f9d0aeaa1c603567b8b7485273a5a892e52e23c618b353a`).

Observed Phase-0 KPI outcomes (all deterministic; two 200-second full-
pipeline replays produce byte-identical receipts):

- `marginal_conformal_coverage_at_alpha_010_meets_worst_case_floor` observed **0.953** (target ≥ 1 − 2α = 0.80) — **PASSED** (86/86 pooled held-out formulations)
- `marginal_conformal_coverage_at_alpha_010_meets_typical_target` observed **0.953** (target ≥ 1 − α = 0.90) — **PASSED**
- `marginal_conformal_coverage_at_alpha_020_meets_worst_case_floor` observed **0.919** (target ≥ 0.60) — **PASSED**
- `marginal_conformal_coverage_at_alpha_020_meets_typical_target` observed **0.919** (target ≥ 0.80) — **PASSED**
- `hostile_null_shuffle_coverage_at_alpha_010_meets_worst_case_floor` observed **0.884** (target ≥ 0.80 under np.random.default_rng(0) y-shuffle) — **PASSED** (falsifiability check on exchangeability)
- `hostile_null_width_inflates_over_real_signal` observed **1.758×** (target ≥ 1.10) — **PASSED** (base learner extracts real signal beyond the coverage guarantee)
- `worst_per_iteration_conformal_coverage_at_alpha_010_meets_conditional_floor` observed **0.882** (target ≥ 0.60; conditional coverage is not theoretically guaranteed but reported as early-warning) — **PASSED**
- `conformal_tighter_than_parametric_at_alpha_010` observational: parametric ±1.96·RMSE_train coverage is 0.733 (undercovers by ~17 pp), so distribution-free wider intervals (median 7.31 N vs parametric 1.04 N) are the correct methodology here.
- `parent_scratch_hardness_receipt_hash_bit_stable` observed **1.0** (parent receipt SHA-256 identical between the new conformal receipt and the on-disk parent)
- `input_zip_hash_bit_stable` observed **1.0** (Experiment.zip SHA-256 identical across parent, conformal, and this KPI receipt)
- `byte_stable_two_replay_pipeline` observed **1.0** (~774 HistGradientBoostingRegressor fits, ~200 s wall clock each, twice, produce byte-identical signed receipt)

The theory stack is: Barber, Candès, Ramdas, Tibshirani 2021 jackknife+
worst-case bound; Vovk, Gammerman, Shafer 2005 foundational conformal;
Papadopoulos, Proedrou, Vovk, Gammerman 2002 split conformal for
regression; Lei et al 2018 JASA distribution-free predictive inference;
Angelopoulos & Bates 2021 tutorial. The coverage guarantee is
distribution-free and holds under exchangeability alone; no
distributional assumption on the base learner is required. The
falsifiability check (hostile-null y-shuffle) empirically confirms
that the coverage guarantee is preserved under exchangeable label
perturbation, while the width inflates as expected — direct
quantitative evidence that the base learner has extracted signal
beyond the coverage guarantee alone.

Claim scope: this KPI is a calibrated-uncertainty attestation on
**Purformance HTE 2K-polyurethane lacquer chemistry only**, in the
normalized feature domain `[0,1]^4`. It grants no batch-release,
manufacturing-qualification, optimizer, or product-performance
authority; interval boundaries are marginal not conditional; Phase-1
would require independent wet-lab validation of the intervals on
formulations sampled near the interval boundaries.

### Empirical benchmark result — 7-baseline named-baseline benchmark for Purformance scratch hardness

A second complementary Phase-0 KPI for `amphora-design-rule-score`,
extending the named-baseline benchmark methodology (from molecule-property
Tg, viscosity-score FFW, solvency-score Hansen, barrier-corrosion-score
diffusivity) to real experimental coating scratch hardness data. Same
3-fold LOIO cross-validation as the parent scratch hardness receipt.

The signed scientific receipt lives at
`reference/purformance/zenodo-13742098/purformance_scratch_hardness_named_baseline_benchmark_receipt.v1.json`
(SHA-256 `dd7295340f40560c014936c1a70c2fd560ed2eccc31940ae349707617ed345d5`,
receipt_id `purformance-scratch-hardness-baseline-benchmark-7598bb5e127925e78e1a77392ed872c6b7ef725f4e882ddc518d777a9fabcb52`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/purformance-scratch-hardness-named-baseline-benchmark-kpi.v1.json`
(SHA-256 `6715c07360cdf89d3b69820d89b04e18f76e5b34d744a671d51772b3159c6c37`).

**7-baseline ranking on pooled LOIO CV (n=86 formulations across 3 iterations):**

| Baseline | Pooled LOIO R² | RMSE (N) |
|---|---:|---:|
| B5_HistGBM_full_parent_config | +0.8555 | 1.160 |
| B3_features_plus_interactions_ridge | +0.4682 | 2.225 |
| B4_ridge_alpha_1 | +0.3350 | 2.488 |
| B2_all_4_features_linear_regression | +0.3341 | 2.490 |
| B1_Vernetzung_crosslinking_only_linear | +0.0156 | 3.027 |
| B0_constant_mean | -0.0121 | 3.070 |
| B6_hostile_null_HistGBM_y_shuffled | -0.4167 | 3.632 |

Observed Phase-0 KPI outcomes (12/12 gates PASSED; `phase0_deterministic_gates_passed: true`):

- `full_ml_r2_beats_constant_baseline` gap **++0.8676** — **PASSED**
- `full_ml_r2_beats_vernetzung_only_physical_crosslinking_baseline` gap **++0.8400** — **PASSED** (ML dominates classical coating chemistry Rule 1)
- `full_ml_r2_beats_linear_all_features_baseline` gap **++0.5215** — **PASSED** (nonlinearity matters)
- `full_ml_r2_beats_ridge_polynomial_interactions_baseline` gap **++0.3874** — **PASSED** (even Ridge with 14 features including quadratics and pairwise interactions loses to ML)
- `full_ml_r2_beats_hostile_null_y_shuffled` gap **++1.2722** — **PASSED**
- `vernetzung_only_r2_at_least_as_good_as_constant` — **PASSED** (physical Rule 1 is directionally correct even if quantitatively insufficient)
- `hostile_null_r2_within_permissive_tolerance_of_constant` — **PASSED** (permissive floor for small n=86)
- `full_ml_beats_every_baseline_except_itself` — **PASSED** (HistGBM ranks first across all 7 baselines)
- `n_baselines_evaluated_at_least_6` observed **7** — **PASSED**
- Housekeeping: parent, conformal, input zip hash bit-stable, byte-stable two-replay

**HONEST INTERPRETATION**. Full HistGBM (R² = +0.8555, matching parent LOIO R² = 0.856 exactly) crushes every non-ML baseline. The classical coating chemistry Rule 1 baseline — "scratch hardness ~ crosslink density" per Wicks-Jones-Pappas 2007 Organic Coatings Ch. 24 — is directionally correct (Vernetzung-only R² = +0.0156 vs constant R² = -0.0121) but quantitatively insufficient. **HDI-IPDI ratio, matting agent, and pigment paste all contribute substantially** — you cannot reduce coating hardness to crosslinking density alone. Adding pairwise interactions (Ridge polynomial B3) helps significantly (R² 0.335 → 0.468) confirming multi-way interactions matter. But even Ridge with 14 quadratic-plus-interaction features cannot match ML's R² = 0.856 — meaning the coating-chemistry landscape has HIGHER-ORDER interactions that ML's tree ensemble captures.

The theory stack: Cordts, Sassmannshausen, Rendel, Klein, Reddemann,
Berge 2024 Chem. Mater. (Purformance dataset); Wicks, Jones, Pappas 2007
Organic Coatings 3rd ed. Ch. 24 (hardness ~ crosslink density);
Hastie-Tibshirani-Friedman 2009; Hoerl-Kennard 1970 Ridge;
Ke et al 2017 LightGBM; Erichsen 435 nano-scratch method.

Claim scope: this KPI documents ML value-add over 6 named non-ML
baselines including a physical crosslinking-density baseline on
Purformance HTE 2K polyurethane lacquer chemistry. Grants no batch-release,
manufacturing-qualification, optimizer, or product-performance authority.
Phase-1 explicitly flags: extended physical baselines using Tg × surface
energy × modulus product per full Wicks-Jones-Pappas theory; chemistry-
aware neural network baselines (polyBERT, Chemprop); additional
Purformance-style datasets to test cross-formulator generalization.

### Known contradictions

- Within-study directional literature rules do not establish cross-family formulation performance or candidate qualification.
- Deterministic no-authority correctness under owned test scenarios does not establish that a lifted (Phase-1) individually-validated design-rule score would be predictive; Phase-1 requires held-family validation receipts under group/time-safe splits following Quinlan/Cohen held-out validation methodology.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.directional_score`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-design-rule-score-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.directional_score`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `RULE_CITED` and solver-use ceiling is `AUDIT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **held-study directional accuracy** at `metrics.directional_score`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Eligible primary-study series with locked extraction and subgroup identifiers

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-formulation-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Ignore zero-mass ingredients and block literature-direction overclaim.
