---
{"audit_date": "2026-07-17", "authority_ceiling": "RULE_CITED", "candidate_types": ["formulation"], "capability_profile": "capability-profile.json", "consumers": [], "dependencies": ["amphora-candidate-contract", "amphora-source-ledger"], "evidence_inventory": "../../config/module-evidence-inventory.json", "lane": "formulation", "module_id": "amphora-ingredient-library", "operational_readiness": "GATED", "phase": "PRE_PHASE_0", "schema": "amphora.module-mission.v1", "scientific_readiness": "UNVALIDATED", "solver_use_ceiling": "AUDIT_ONLY"}
---

# amphora-ingredient-library mission

## Decision and falsifiable hypothesis

This module supports the decision of whether all positive-mass ingredients have cited constants for the requested calculation. Its falsifiable hypothesis is that a provenance-locked catalog can fail closed on every missing active ingredient constant.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-formulation-capabilities/src/lib.rs` with SHA-256 `8b7612325bff9830da1eebd1dc6ba4af411205581ce388c45fdc6be5356edde0`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-formulation-capabilities/src/lib.rs` — SHA-256 `8b7612325bff9830da1eebd1dc6ba4af411205581ce388c45fdc6be5356edde0`

Operational state is `GATED`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-ingredient-library/reference/mvp20/data/corrosion_series.json` — SHA-256 `ef5cf7b4af77dbb74aa2c9ae112fed56e9132b9bcb0265065c8490b15aebdfde`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-ingredient-library/reference/mvp20/data/cure_verification_set.json` — SHA-256 `884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-ingredient-library/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-formulation-capabilities/tests/ingredient_library_phase0_kpi.rs`
drives the deterministic `ingredient_library` runtime (via
`FormulationCapability::new(descriptor)`) across 6 formulation-candidate
scenarios: simple 1+1 (dgeba+polyamide); multi-ingredient 5+2 with
pigment/extender/additive/solvent; adversarial cited_ingredients
injection with CAS RNs and asserted_grade; adversarial
ingredient_grade_declarations injection with grade/lot/method/currentness;
mixed zero-mass placeholder entries; and missing part_B (recipe abstention
path). It emits a byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`06229682503e25a26da0391dac29c4f44e8ad46948c4b9ad77f76101b109fc1e`). This
citation was corrected on 2026-08-03 by repair R-A01 after the signed
`evidence/audit/phase0-mission-evidence-parity-v1` audit refuted the
previously cited stale result hash (preserved verbatim inside that receipt
and inside the R-A01 done-receipt); two fresh independent re-executions of
the Rust Phase-0 harness reproduce `result.v1.json` byte-identically at the
SHA-256 cited above. The Phase-0 KPI receipt formerly cited at
`evidence/phase0/kpis/ingredient-library-ledger-quarantine-kpi.v1.json` is
not present in the live tree: it was superseded with reason
`STALE_UNSIGNED_PREPARATION_REISSUE` and survives only under
`evidence/superseded/supersession-6aba291aa333b4c3ae40d584ebe0fe2955e6949a33cb2506a5e7113021fff1c1/phase0/kpis/ingredient-library-ledger-quarantine-kpi.v1.json`;
see `evidence/phase0/repairs/R-A01/done/` for the signed supersession trail.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `runtime_status_insufficient_input_rate` observed **1.0** (6/6 - runtime returns INSUFFICIENT_INPUT because rights-cleared ingredient ledger is required to lift quarantine) — **PASSED** (floor 1.0)
- `evidence_scope_pinned_ingredient_ledger_diagnostic_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `recipe_present_gate_matches_candidate_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `ingredient_ledger_lookup_attempted_false_on_recipe_body_and_absent_on_abstention_rate` observed **1.0** (6/6 - no ledger query ever attempted) — **PASSED** (floor 1.0)
- `rights_cleared_ingredient_ledger_available_false_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `active_mass_property_coverage_null_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `all_candidate_ingredients_cited_gate_false_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `active_mass_property_coverage_at_least_95pct_gate_false_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `observed_ingredient_ids_match_expected_lexicographic_rate` observed **1.0** (6/6 - BTreeSet union bit-exact) — **PASSED** (floor 1.0)
- `missing_input_names_grade_lot_method_currentness_rate` observed **1.0** (5/5) — **PASSED** (floor 1.0)
- `explanation_disclaims_unresolved_legacy_ledger_rate` observed **1.0** (5/5) — **PASSED** (floor 1.0)
- `authority_envelope_preservation_rate` observed **1.0** (6/6) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (6/6) — reported observationally.

CAS Registry Number methodology (ANSI/NISO Z39.7); IUPAC International
Chemical Identifier (InChI, IUPAC 2007) + InChIKey; IUPAC Nomenclature
of Organic Chemistry (Recommendations 2013); TSCA Chemical Data
Reporting Rule (40 CFR Part 711); EU Regulation (EC) 1272/2008 CLP;
ISO/IEC 11179 metadata registries; ISO 8000 data quality; OECD SIDS
Manual (2004); Anderson 1980 reference-monitor. The runtime reproduces
the ingredient-ledger-quarantine boundary at 100% correctness across 6
independent candidate scenarios. Adversary-supplied cited_ingredients
with CAS RNs, ingredient_grade_declarations with grade/lot/method/
currentness_date, and adversary_claimed_ledger_coverage are all
defensively refused - the runtime never queries any ledger and never
elevates a candidate-supplied CAS RN or grade declaration into
master-data authority. Every one of the 23 standard red-team attack
axes declared in `evidence/phase0/benchmark/benchmark-lock.v1.json` is
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
`operational_readiness: GATED` in the front-matter are preserved.

### Known contradictions

- The local ingredient catalog contains sourced and approximate values with unresolved rights/currentness and cannot qualify a commercial grade.
- Deterministic ID-observation correctness under owned test scenarios does not establish that a lifted (Phase-1) ledger-lookup would be correct; Phase-1 requires a rights-cleared immutable ingredient fact ledger keyed by CAS RN (or InChIKey) with per-lot grade/method/currentness traceable to supplier CoAs.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.ingredient_count`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-ingredient-library-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.ingredient_count`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `RULE_CITED` and solver-use ceiling is `AUDIT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **active ingredient coverage** at `metrics.ingredient_count`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Current supplier TDS/SDS/CoA records with grade, rights, and issuer binding

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-formulation-capabilities/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Ignore zero-mass ingredients and reject unknown load-bearing records.
