---
{"audit_date":"2026-07-17","authority_ceiling":"REAL_ARITHMETIC","candidate_types":["formulation"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-source-ledger"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"formulation","module_id":"amphora-formulation-universe","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"AUDIT_ONLY"}
---

# amphora-formulation-universe mission

## Decision and falsifiable hypothesis

This module supports the decision of whether a declared formulation search space has been completely accounted. Its falsifiable hypothesis is that Cartesian enumeration can report every solved and infeasible combination without silent loss.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-formulation-capabilities/src/lib.rs` with SHA-256 `c0b7449903224b5e50736a3a9d3f271b845bc2ba18c0348476a6e6225847a047`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-formulation-capabilities/src/lib.rs` — SHA-256 `c0b7449903224b5e50736a3a9d3f271b845bc2ba18c0348476a6e6225847a047`
- `amphora-assurance-capabilities/src/diagnostics.rs` — SHA-256 `4ec366110c523f30e285dd3cbca08fd199f28edb06560897cf7e17e7abe7dd89`

Operational state is `GATED`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-formulation-universe/reference/mvp20/data/corrosion_series.json` — SHA-256 `ef5cf7b4af77dbb74aa2c9ae112fed56e9132b9bcb0265065c8490b15aebdfde`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-formulation-universe/reference/mvp20/data/cure_verification_set.json` — SHA-256 `884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-formulation-universe/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-formulation-capabilities/tests/formulation_universe_phase0_kpi.rs`
drives the deterministic `validate_formulation_universe` primitive across
a self-authored fixture at
`amphora-formulation-universe/reference/phase0-formulation-universe-known-answer.v1.json`
(SHA-256 `cb3cdb8bd40ebfeadd929ab42fed7df4596375aa1d00b24242755479676029b3`;
CC0-1.0, `eligible_for_derivatives: true`; 10 Design-of-Experiments
universes from Montgomery 2017 8th ed. Ch. 5-8 and Wicks/Jones/Pappas
2007 §24.5; cartesian totals 8-32, with 0-5 declared-infeasible cells
per universe) and emits a byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`d10f3abedeff79333c06005489c59170a65f2d5682bbc2795e95f26be0ba08e8`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/formulation-universe-cartesian-accounting-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `cartesian_identity_correctness_rate` observed **1.0** (10/10; solved + infeasible = cartesian_total at u64 bit precision) — **PASSED** (floor 1.0)
- `cartesian_product_arithmetic_correctness_rate` observed **1.0** (10/10; cartesian_total = Π axis_cardinalities matches Python-side reference exactly) — **PASSED** (floor 1.0)
- `axis_order_determinism_rate` observed **1.0** (10/10; three axis-key rotations per universe all produce byte-identical FormulationUniverseAccountingV1 via BTreeMap ordering) — **PASSED** (floor 1.0)
- `candidate_feasibility_claim_ignore_rate` observed **1.0** (10/10; injected `claims` object with bogus `solved_count=99999`, `authority_upgrade=true`, forged `objective_values` all recorded as ignored with counts unchanged — CANDIDATE_FEASIBILITY_CLAIM axis) — **PASSED** (floor 1.0)
- `cartesian_cardinality_overflow_fail_closed_rate` observed **1.0** (3/3 overflow probes: 30×30×30, 200×200, single axis of 10001 — CARTESIAN_CARDINALITY_OVERFLOW axis) — **PASSED** (floor 1.0)
- `infeasible_index_laundering_fail_closed_rate` observed **1.0** (6/6 probes: index==total, index>>total, duplicate index, negative non-u64, float, infeasible-without-axes — INFEASIBLE_INDEX_LAUNDERING axis) — **PASSED** (floor 1.0)
- `cartesian_canonical_duplication_fail_closed_rate` observed **1.0** (4/4 probes: literal duplicate, integer duplicate, null duplicate, canonically-equal objects with different key insertion order defeated by `amphora_core::stable_hash` — CARTESIAN_CANONICAL_DUPLICATION axis) — **PASSED** (floor 1.0)
- `authority_lock_preservation_rate` observed **1.0** (10/10 preserve `ranking_eligible=false`, `usable_by_optimizer=false`, `authority_upgrade=false`, `objective_values={}`, `feasibility_basis == "DECLARATIVE_ACCOUNTING_ONLY"`) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (10/10) — reported observationally.
- `cartesian_cardinality_range` observed: min = 8 (2^3 full factorial), max = 32 (labeled "2^(5-1) half-fraction" but see 2026-08-17 Known contradictions entry: this is actually the full un-fractionated 2^5 space, 32, not the genuine 2^(5-1)=16-run half-fraction its citation names), ceiling = 10 000.

Cartesian search-space accounting via Design-of-Experiments enumeration
is 90 years of established industrial mathematics (Fisher 1935;
Montgomery 2017 8th ed. Ch. 5-8). The runtime reproduces every one of
the 10 published DoE examples' cardinality counts at u64 bit precision
and correctly rejects every one of the 13 red-team probes across the
four universe-specific attack axes. Every one of the 27 red-team attack
axes declared in `evidence/phase0/benchmark/benchmark-lock.v1.json` —
including the four universe-specific axes
(CARTESIAN_CANONICAL_DUPLICATION, CARTESIAN_CARDINALITY_OVERFLOW,
INFEASIBLE_INDEX_LAUNDERING, CANDIDATE_FEASIBILITY_CLAIM) — is exercised
end-to-end in the integration test or in the seven new red-team unit
tests in `amphora-formulation-capabilities/src/lib.rs`.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the CC0
self-authored DoE compilation, `LOCKED_SPLIT`, `LOCKED_BENCHMARK`,
`TWO_REPLAYS`, `RED_TEAM` across 27 attack axes, `CLAIM_LOCKS`,
`FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the `phase` header
flips to `PHASE_0`. No signed receipt has been produced yet; the module
remains `PRE_PHASE_0` for authority purposes, and
`operational_readiness` stays `GATED`.

### Known contradictions

- Cartesian accounting establishes enumerated and infeasible counts, not empirical superiority of any solved formulation.
- 2026-08-06 (fire 20260806T000001-1775748-1b4015bea2b8, campaign item T-06, first adversarial verdict this module has ever received): CLAIM_REFUTED. An independent live-Rust probe against validate_formulation_universe found (1) duplicate-factor collapse evasion -- a single physical axis value re-expressed as JSON integer `1` vs float `1.0` is NOT detected as a canonical duplicate and inflates axis_cardinalities / cartesian_total; and (2) index-identity instability -- two accounting-equivalent (byte-identical FormulationUniverseAccountingV1 output) representations of the same universe, differing only in one axis value array's order, decode the SAME declared infeasible_indices entry to two DIFFERENT physical formulations under the module's own documented mixed-radix unranking (evidence/audit/mixed-radix-bijection-v1). This falsifies the founder directive T2-06 done-criterion 'identity of every enumerated cell is stable.' Cardinality overflow fail-closed behavior SURVIVED fresh boundary probes. No downstream artifact was found presenting a cardinality count as a feasibility claim. Signed receipt: evidence/phase0/repairs/T-06/done/t06-independent-adversarial-attack-receipt.v1.dsse.json.
- 2026-08-15 (fire 20260815T110001-1563621-999baa0fa684, ROTATION, no campaign item): CLAIM_REFUTED. An independent governance-currency audit found the machine-readable KPI register `evidence/phase0/kpis/formulation-universe-cartesian-accounting-kpi.v1.json` was never corrected after the 2026-08-06 T-06 finding above (last touched 2026-08-03, three days before T-06): both named T-06 defects were confirmed still live 9 days later, with no RETRACTION-INDEX.md entry or supersession reference anywhere under `evidence/`. Signed receipt: evidence/audit/kpi-claim-currency-v1/kpi-claim-currency-receipt.v1.dsse.json.
- 2026-08-17 (fire 20260817T050001-3280050-bf83a9be45cd, ROTATION, no campaign item): CLAIM_REFUTED. The claim below this line ("the runtime reproduces every one of the 10 published DoE examples' cardinality counts") is false for at least 1 of the 10: fixture entry `2^(5-1)-half-fraction-screening` cites Montgomery 2017 §8.2's 2^(5-1) half-fraction design (genuinely 2^(5-1)=16 runs) but its own `expected_cartesian_total` is 32 -- the FULL, un-fractionated 2^5 space -- and its own `industrial_context` field admits this ("Enumerating the full 2^5 space; downstream design selects half-fraction"). validate_formulation_universe has no generator/defining-relation/aliasing logic and never reads a `design_type` field at all, so it is architecturally incapable of validating a genuine fractional-factorial design's cardinality regardless of what any fixture entry claims. The other 9 fixture entries' citations were independently re-checked and are internally consistent. Signed receipt: evidence/audit/doe-fixture-citation-fidelity-v1/doe-citation-fidelity-receipt.v1.dsse.json.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.cartesian_total`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-formulation-universe-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.cartesian_total`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `REAL_ARITHMETIC` and solver-use ceiling is `AUDIT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **accounting equality** at `metrics.cartesian_total`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Locked design-space specification and empirical evaluation of selected formulations

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-formulation-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Require a formulation and reconcile total, solved, and infeasible Cartesian counts.
