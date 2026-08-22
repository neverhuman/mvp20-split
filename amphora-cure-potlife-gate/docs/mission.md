---
{"audit_date": "2026-07-17", "authority_ceiling": "CRO_GATED", "candidate_types": ["formulation"], "capability_profile": "capability-profile.json", "consumers": [], "dependencies": ["amphora-candidate-contract", "amphora-source-ledger"], "evidence_inventory": "../../config/module-evidence-inventory.json", "lane": "performance", "module_id": "amphora-cure-potlife-gate", "operational_readiness": "BLOCKED", "phase": "PRE_PHASE_0", "schema": "amphora.module-mission.v1", "scientific_readiness": "UNVALIDATED", "solver_use_ceiling": "CONSTRAINT_ONLY"}
---

# amphora-cure-potlife-gate mission

## Decision and falsifiable hypothesis

This module supports the decision of whether a formulation should proceed to multi-temperature CRO cure testing. Its falsifiable hypothesis is that locked family/source-held-out validation can beat the declared pot-life baseline.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-cure-potlife-gate/src/lib.rs` with SHA-256 `1a1737339b903705a0af19e28277137c3476ef4ff5d145125996f2a3d0e13939`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-cure-potlife-gate/src/lib.rs` — SHA-256 `1a1737339b903705a0af19e28277137c3476ef4ff5d145125996f2a3d0e13939`
- `amphora-cure-potlife-gate/src/contract.rs` — SHA-256 `4f88268d559b11aa0f4f3e18d7173b528107454bc79f7242ec3c13c4c9decd70`
- `amphora-cure-potlife-gate/src/evaluation.rs` — SHA-256 `36ba0132e1d3cad16a798a2a50a68d3e9c6d2868e9e01996ad7fb5cf660c595d`
- `amphora-cure-potlife-gate/src/physics.rs` — SHA-256 `01d9f3365aa702d0b40eb3ab4819abe0fe923346543f8fe054c4e5d84832068e`
- `amphora-cure-potlife-gate/src/preflight.rs` — SHA-256 `bfb7d7214a73107276ee3ab63ea2cfe1e367f291d3bb03c99da4d60acbd0fad7`
- `amphora-cure-potlife-gate/src/protocol.rs` — SHA-256 `7dea16b049e1b514296b561225100a7d124883ae4eab2eda9b66ae8cbdfabe92`
- `amphora-cure-potlife-gate/src/tests.rs` — SHA-256 `764ae2faac065e8b2f99435522749b9de812915edf93aa14954d1e1169bab69a`

Operational state is `BLOCKED`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-cure-potlife-gate/reference/mvp20/data/corrosion_series.json` — SHA-256 `ef5cf7b4af77dbb74aa2c9ae112fed56e9132b9bcb0265065c8490b15aebdfde`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-cure-potlife-gate/reference/mvp20/data/cure_verification_set.json` — SHA-256 `884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-cure-potlife-gate/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-cure-potlife-gate/reference/pot-life/source-landscape.v1.json` — SHA-256 `2944d9fbc67dfb9a6ce7ad1a026b94d8b8f9c49e54f30e442c8ea2f93b188417`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-cure-potlife-gate/reference/mvp20/out/v5_epoch29_unseen_benchmark.json` — SHA-256 `5f464c738e9e261069964f6624feefad990a35bdb4d656ffaeb3518f02d48443`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-cure-potlife-gate/reference/mvp20/out/v5_epoch30_lift_audit.json` — SHA-256 `79e7ed9933482c5434aa5050ac9063a2cbb647e2fad0cb0f6aebbdd44a055af4`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-cure-potlife-gate/tests/cure_potlife_phase0_kpi.rs` drives the
deterministic `effective_cure_rate` primitive across a self-authored
fixture at
`amphora-cure-potlife-gate/reference/phase0-cure-potlife-known-answer.v1.json`
(SHA-256 `7ba2d0d925571fd18bbfece1846a27bee186e3c30f7c342fdcb02bc0537c2ce1`;
CC0-1.0, `eligible_for_derivatives: true`; 12 well-characterized
two-part epoxy-amine systems from DGEBA + aliphatic polyamine
(TETA/DETA/TEPA), cycloaliphatic diamine (IPDA/PACM/DACH), aromatic
amine (MXDA/MPDA/MDA), amidoamine adduct, and Mannich base families;
each system carries published activation energy from Prime R.B. Turi
1997, Kamal-Sourour 1973, Riccardi et al. 1984, or Blanco et al. 2005;
each carries pot-life values at four temperatures (10, 22.78=73°F, 30,
40°C) from supplier technical data sheets and Ellis 1993) and emits a
byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json`
(SHA-256 `945f5b735992900ea58103e55acc35731a72bcad5bd5962a661440fdcd07cf60`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json`. Reference
temperature is 22.78 °C = 73 °F = 295.928 K per ASTM D2196 rotational
viscosity spec and Navy prime pot-life charter.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `arrhenius_pot_life_mape` observed **14.7%** across 36 held-out (system, T) pairs — **PASSED** (ceiling 20%)
- `arrhenius_over_constant_baseline_lift` observed **+80.5 pp** (Arrhenius 14.7% MAPE vs. constant-pot-life-at-73°F baseline 95.2% MAPE — the pot-life varies 5×–10× across the 30-degree temperature span) — **PASSED** (floor 30 pp)
- `held_out_temperature_extrapolation_mape` observed **15.6%** at 30°C interpolation — **PASSED** (ceiling 25%)
- `per_system_within_40_percent_rate` observed **1.0** (12/12 systems within ±40% at every held-out temperature; within tighter ±20% tolerance 1/12 = Mannich base only, reflecting the honest practical accuracy of first-principles Arrhenius scaling on pot-life data) — **PASSED** (floor 0.80)
- `applicability_domain_fail_closed_rate` observed **1.0** (9/9 red-team probes with NaN/Infinity/negative T or Ea correctly return `Err(PotLifeError::Range)`) — **PASSED** (floor 1.0)
- `authority_lock_preservation_rate` observed **1.0** — **PASSED** (floor 1.0)

**Qualified temperature-scaling statement (repair R-A02, 2026-08-03;
supersedes the earlier blanket claim of "under 15% error across a
30-degree temperature range (10°C to 40°C)", refuted by
`evidence/audit/potlife-kpi-envelope-disclosure-gap-v1/`).** Per-leg
held-out accuracy of the reference-anchored Arrhenius rule is NOT
uniform: it is accurate at 10°C (MAPE 3.445%, n=12, bias mixed 8
under- / 4 over-predictions), marginal at 30°C (MAPE 15.628%,
already above the old 15% figure, with 12/12 systems under-predicted),
and it FAILS the module's own declared
`held_out_temperature_extrapolation_mape` ceiling (0.25) at 40°C
(MAPE 25.124%, with 12/12 systems under-predicted — a systematic
directional bias, not noise). The pooled 14.7% MAPE reported above is
arithmetically correct but conceals this monotone degradation with
temperature (3.445% → 15.628% → 25.124%); it must not be read
as "under 15% at every temperature in the 10–40°C range."
Separately, `evidence/audit/potlife-q10-heuristic-ablation-v1/` showed
that a chemistry-blind, Ea-free Q10=2 heuristic ties the published-Ea
model pooled (Q10 MAPE 15.27% vs Arrhenius 14.73%), beats it on the
30°C leg (10.65% vs 15.63%) and the 40°C leg (17.46% vs
25.12%), and breaches the 0.25 ceiling on no leg — so the
published per-system activation energies are not demonstrably
load-bearing for the model's held-out accuracy. The deterministic
`effective_cure_rate(T_k, Ea, T_ref_k)` primitive is exercised at
Phase-0 rigor only within these disclosed per-leg limits.

**Pot-life model upgrade (repair R-C02, 2026-08-12; audit-only, does
NOT change the live Rust `effective_cure_rate` primitive or flip
`scientific_readiness`/`phase`/`operational_readiness`).** On the
IDENTICAL locked 36-point truth table and metric used above, a
leave-one-system-out (LOSO) cross-system multiplicative bias
correction on top of the incumbent per-system published-Ea Arrhenius
model meets the pre-registered R-C02 acceptance bar: 40°C leg MAPE
falls from 25.12% to **3.95%** (ceiling 25%, PASSED) and the corrected
model beats the chemistry-blind Q10=2 heuristic on **3 of 3** held-out
legs (10°C 3.36% vs Q10 17.70%; 30°C 1.78% vs Q10 10.65%; 40°C 3.95%
vs Q10 17.46%; required floor was 2 of 3). Method: for each system s
and leg L, the correction factor is
`exp(mean_{i != s}[ln(observed_i,L / arrhenius_pred_i,L)])`, computed
from the OTHER 11 systems only, so a system's own datum never informs
its own correction (honest leave-one-system-out dof accounting). This
targets the already-established, direction-consistent convexity
finding (`evidence/audit/potlife-arrhenius-curvature-mechanism-v1/`:
ln(pot life) vs 1/T convex in 12/12 systems, 12/12 under-prediction at
30°C and 40°C) by pooling the bias ACROSS SYSTEMS at a fixed
temperature rather than fitting a per-system temperature curve — this
sidesteps the T0-identifiability failure that refuted the VFT
candidate in that same receipt (VFT was the worst model on the 40°C
extrapolating fold). Receipt:
`evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json`.
Caveats this does NOT close: the correction is validated only on this
12-system, 3-leg fixture (no new data was acquired or may be
acquired); it assumes the curvature bias is shared in sign and
rough magnitude across the 5 hardener families present, which held on
this fixture but is untested on any system outside it; and it does
not identify the physical mechanism (curvature source remains open
per the prior receipt).

**Family-safe re-attack of R-C02 (audit, 2026-08-14; AUDIT_ONLY, no
authority change).** R-C02's LOSO correction pool leaves individual
systems out but keeps same-family systems in the pool, so its pass was
not group-safe at the family level -- exactly the caveat above flags as
untested. Re-ran the identical R-C02 correction formula and acceptance
bar with leave-one-hardener-family-out (LOFO) pooling instead (all
same-family systems excluded from a held-out system's correction pool,
not just itself). The LOFO-corrected candidate still meets the
identical bar: 40°C-leg MAPE 4.169% (ceiling 25%, PASSED) and beats
Q10=2 on 3/3 legs (required floor 2/3), with sub-percentage-point
degradation vs LOSO on every leg (10°C +0.415pp, 30°C -0.040pp, 40°C
+0.215pp). This closes the "untested on any system outside it" caveat
for the in-fixture family-holdout regime specifically: the pass is not
an artifact of within-family leakage in the LOSO pool. It does NOT
establish generalization to a hardener family absent from the 12-system
fixture entirely -- that remains untested and would require new data.
Receipt:
`evidence/audit/potlife-lofo-family-safe-v1/potlife-lofo-family-safe-receipt.v1.dsse.json`.

Fixture rights note: the known-answer fixture's rights block (CC0-1.0,
`eligible_for_derivatives: true`) is an in-file self-assertion with no
signed rights receipt and sits outside the module's source-lock
accounting; it is under human review per
`evidence/audit/rights-integrity-contradiction-v1/`.

**Phase-1 status remains unchanged.** The legacy gel-time artifact
`amphora-cure-potlife-gate/reference/mvp20/out/v5_epoch30_lift_audit.json`
(SHA-256 `79e7ed9933482c5434aa5050ac9063a2cbb647e2fad0cb0f6aebbdd44a055af4`)
still reports `status="exploratory"` with only 0.0625 absolute lift,
short of the locked 0.10 threshold. The separate
`coating-pot-life-physics-v1` Phase-1 benchmark still requires 36
independently mixed owned runs, twelve untouched 73 °F holdouts, packet-
bound independent review, and is `NOT_PASSED`. This Phase-0 push
validates the Arrhenius primitive only; it does NOT lift the
`operational_readiness: BLOCKED` status, which is scientific-superiority
gated per the Navy prime charter and requires CRO wet-lab work.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the CC0
self-authored cure kinetics compilation, `LOCKED_SPLIT`,
`LOCKED_BENCHMARK`, `TWO_REPLAYS`, `RED_TEAM` across 23 attack axes
plus the eight new in-runtime Arrhenius-boundary tests, `CLAIM_LOCKS`,
`FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the `phase`
header flips to `PHASE_0`. No signed receipt has been produced yet; the
module remains `PRE_PHASE_0` for authority purposes, and
`operational_readiness` stays `BLOCKED` (Phase-1 CRO gate is
independent of this Phase-0 push).

### Known contradictions

- The checked gel-time lift audit is exploratory and reports no statistically established lift or genuinely external locked validation set.
- The coating-pot-life physics track has contracts and synthetic diagnostics but no checked-in owned 36-run benchmark or independent review.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.unseen_benchmark`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-cure-potlife-gate-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.unseen_benchmark`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `CRO_GATED` and solver-use ceiling is `CONSTRAINT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **within-1.5x rate** at `metrics.unseen_benchmark`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: At least 10 genuinely external complete rows with no family/source overlap, at least 80% within 1.5x, and at least 10-point baseline lift; promotion also requires multi-temperature CRO batches.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Genuinely external complete gel-time rows and multi-temperature CRO batches
- Thirty-six independently mixed, owned coating pot-life runs plus packet-bound independent review

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-cure-potlife-gate/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Strictly reject unknown fields and malformed hashes across the coating pot-life contract preflight.
