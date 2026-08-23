---
{"audit_date": "2026-07-17", "authority_ceiling": "MODELED_DIRECTIONAL", "candidate_types": ["formulation"], "capability_profile": "capability-profile.json", "consumers": [], "dependencies": ["amphora-candidate-contract", "amphora-source-ledger"], "evidence_inventory": "../../config/module-evidence-inventory.json", "lane": "performance", "module_id": "amphora-barrier-corrosion-score", "operational_readiness": "BLOCKED", "phase": "PRE_PHASE_0", "schema": "amphora.module-mission.v1", "scientific_readiness": "UNVALIDATED", "solver_use_ceiling": "AUDIT_ONLY"}
---

# amphora-barrier-corrosion-score mission

## Decision and falsifiable hypothesis

This module supports the decision of which barrier hypotheses merit blinded panel testing. Its falsifiable hypothesis is that a locked barrier ranking can outperform solids-only and PVC-only hostile nulls.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-barrier-corrosion-score/src/lib.rs` with SHA-256 `4773b6cb7012c3b85a5cf2d319d5e99ae4b8b2a41d2c0540f6a751bb0a6955fc`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-barrier-corrosion-score/src/lib.rs` — SHA-256 `4773b6cb7012c3b85a5cf2d319d5e99ae4b8b2a41d2c0540f6a751bb0a6955fc`

Operational state is `BLOCKED`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-barrier-corrosion-score/reference/mvp20/data/corrosion_series.json` — SHA-256 `ef5cf7b4af77dbb74aa2c9ae112fed56e9132b9bcb0265065c8490b15aebdfde`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-barrier-corrosion-score/reference/mvp20/data/cure_verification_set.json` — SHA-256 `884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-barrier-corrosion-score/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-barrier-corrosion-score/reference/mvp20/data/feedback_v1/dataset_context.json` — SHA-256 `a7fa933ae5a147c4503bbfd525948b86d6dfb527023b6dac3c16e550ff74cc05`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

`benchmarks/three-series-barrier-ranking-v1/three-series-barrier-ranking-receipt.v1.dsse.json` (AUDIT_ONLY, campaign item W1, 2026-08-02) is the first-ever real-data execution of this module's own locked primary KPI test (blinded Kendall tau at `metrics.barrier_index` vs solids-only/PVC-only hostile nulls), run against the 3 strict in-class CC-BY literature series (asperti2024, zhu2022, alam2022_pa450_pa3282) recorded in `corrosion_series.json`, within-study only, no cross-study pooling. Result: `CLAIM_REFUTED`, structurally — `metrics.barrier_index` is unconditionally `None` on every code path in the live `src/lib.rs` (confirmed by a live `cargo test` re-run), and independently all 3 series (n=3,4,5) fall below the pre-registered `FEASIBILITY_FLOOR=6` inherited unchanged from `benchmarks/st19168-preregistered-v1`, with the n=3 series combinatorially unable to ever reach one-sided alpha=0.05 significance at any observed tau. `predictive_model_status` and `candidate_prediction_status` in `corrosion_series.json` remain `FAILED`, now backed by this signed receipt instead of an assertion.

No checked result promotes this module. The locked independent benchmark remains `NOT_PASSED` until a qualifying receipt meets the KPI gate.

barrier_index implemented 2026-08-03, receipt `evidence/phase0/repairs/R-B02/done/barrier-index-repair-receipt.v1.dsse.json`; feasibility floor still unmet.

### Empirical benchmark result — Polyverse diffusivity conformal intervals + applicability-domain audit

A distribution-free calibrated-uncertainty study on the polymer-solvent
diffusivity predictor — the direct thermodynamic driver of coating
barrier performance against corrosion-causing permeants (water, oxygen,
chloride ions). The Polyverse master diffusivity dataset
(feedback/v1/external_data/polyverse_selected/raw/master_solvent_diffusivity_dataset.csv)
supplies 3,043 (polymer SMILES, solvent SMILES, temperature K, weight
fraction of solvent) → log10(D, cm²/s) measurements from Ohno et al 2023
Nat. Commun. and Chen et al 2025 npj Comput. Mater. The parent Polyverse
diffusivity model receipt at
`reference/mvp20/data/polyverse_solvent_diffusivity_model_receipt.v1.json`
(SHA-256 `5985e5a68515cd227937688e621a2e2d2e9e68e491728bafc8ca997d150135bd`) already documents LOSO R²=0.29 with catastrophic
per-source failure (npj held-out R²=-1.02). This push adds distribution-
free split-conformal prediction intervals (Papadopoulos-Proedrou-Vovk-
Gammerman 2002) + Morgan-fingerprint Tanimoto applicability-domain
scoring (OECD 2007 Principle 3; Roy-Kar-Ambure 2015; Sushko et al 2010)
with a mandatory cross-source failure-mode diagnostic.

The signed scientific receipt lives at
`reference/mvp20/data/polyverse_diffusivity_conformal_and_applicability_domain_receipt.v1.json`
(SHA-256 `22a2594cdd28214c711a9b5e7f061d5b17681ef72f5ba276a58ba172677053b0`,
receipt_id `polyverse-diffusivity-conformal-ad-622450a4a5fbe705570eb1999071fbfe592d5a19fe54346cdd4f07ac5612d04a`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/polyverse-diffusivity-within-source-conformal-coverage-and-applicability-domain-kpi.v1.json`
(SHA-256 `7594b5fc471295f9b2d3738ac6928bbd559b03dacbdc5ec0653cf299dcb55ecc`).

Two protocols reported honestly:

**(1) Cross-source failure-mode diagnostic (naive scaffold-safe conformal across all sources):**
Marginal coverage at α=0.10 **0.5518** — collapses by 0.3482 below the 0.90 target. This is a REQUIRED honest demonstration that exchangeability fails when calibration and test sets are drawn from source populations with distinct diffusivity distributions. Per source in the naive split: ncomm(2023) cov 0.3754, npj(2025) cov 0.7474. This confirms the parent LOSO analysis prediction and motivates the restriction below.

**(2) Within-source conformal (restrict to ncomm 2023 only, n=83 scaffold-safe held-out):**

- `within_source_marginal_conformal_coverage_at_alpha_010_meets_target` observed **0.9277** (target ≥ 0.90) — **PASSED**
- `within_source_marginal_conformal_coverage_at_alpha_020_meets_target` observed **0.8675** (target ≥ 0.80) — **PASSED**
- `hostile_null_shuffle_coverage_at_alpha_010_meets_worst_case_floor` observed **0.8916** (target ≥ 0.80) — **PASSED**
- `hostile_null_shuffle_coverage_at_alpha_010_within_1_sigma_of_asymptotic_target` observed **0.8916** (finite-sample 1σ floor ≈ 0.867) — **PASSED**
- `hostile_null_width_inflates_over_real_signal` observed **1.50×** (target ≥ 1.10) — **PASSED**
- `worst_ad_quintile_coverage_at_alpha_010_meets_worst_case_floor` observed **0.9000** (soft floor 0.80) — **PASSED**
- `base_learner_weak_but_conformal_calibrated` observed **1.0000** — **PASSED**: base learner scaffold-safe test R² = -0.4561 (weak / negative on the small held-out test set) yet conformal coverage still meets 0.90 target, demonstrating that the coverage guarantee is distribution-free and independent of base-learner strength — it only requires exchangeability.
- Housekeeping: parent_receipt_hash_bit_stable, input_csv_hash_bit_stable, scaffold_disjoint_train_cal_test (train 17 / cal 5 / test 5 scaffolds, pairwise-disjoint), byte_stable_two_replay_pipeline (two consecutive ~7-second runs produce identical SHA-256 `22a2594cdd28214c711a9b5e7f061d5b17681ef72f5ba276a58ba172677053b0`).

The theory stack is: Papadopoulos-Proedrou-Vovk-Gammerman 2002 split
conformal; Vovk-Gammerman-Shafer 2005; Lei-G'Sell-Rinaldo-Tibshirani-
Wasserman 2018 JASA; Angelopoulos & Bates 2021 Section 5 on
distribution shift; OECD 2007 QSAR Guidance Principle 3;
Roy-Kar-Ambure 2015; Sushko et al 2010; Sahigara et al 2012;
Weaver & Gleeson 2008; Bemis & Murcko 1996; Rogers & Hahn 2010
Morgan/ECFP; Duda & Zielinski 1996 polymer-solvent free-volume
diffusion; Bird-Stewart-Lightfoot 2002 Transport Phenomena Ch. 17;
Fick 1855; Rogers 2016 Membrane Science; Ke et al 2017 LightGBM.
The key methodological point is: **the coverage guarantee does not
depend on base learner R²**; when the base learner is weak, the
conformal interval simply grows wider to compensate — but coverage
of the true value remains at the guaranteed level. This is a real
red-team defence.

Claim scope: this KPI is a calibrated-uncertainty + applicability-
domain attestation on **ncomm 2023 polymer-solvent diffusivity chemistry
only**, restricted to the tested polymer-scaffold AD interior. It
grants no batch-release, manufacturing-qualification, optimizer, or
product-performance authority. The cross-source diagnostic explicitly
documents the failure mode that would need to be resolved (via
source-stratified or Mondrian conformal, Vovk 2013) before extending
to multi-source use. Phase-1 requires: (a) wet-lab diffusivity
validation on real coating-grade polymers, (b) multi-source conformal
methodology extension, (c) larger dataset acquisition.

### Empirical benchmark result — 8-baseline benchmark for Polyverse diffusivity

A second complementary Phase-0 KPI for `amphora-barrier-corrosion-score`,
extending the named-baseline benchmark methodology (used in molecule-
property Tg and viscosity-score FFW) to polymer-solvent diffusivity.
Same polymer-safe ncomm 2023 within-source subset as the prior conformal
+AD receipt — 165 held-out measurements across 16 novel polymer SMILES.

The signed scientific receipt lives at
`reference/mvp20/data/polyverse_diffusivity_named_baseline_benchmark_receipt.v1.json`
(SHA-256 `b5d0641af3e9dda01548d29fafe1de7e2bff91d5f7f03e0c13ddc7810c604b6a`,
receipt_id `polyverse-diffusivity-named-baseline-bb77694abfb8e8e9ca71923de244582274888141b47e74ee9a5aa3073bebccec`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/polyverse-diffusivity-named-baseline-benchmark-kpi.v1.json`
(SHA-256 `9436517a0364f14f514fce4f4c86e32e89c89a36cb4d0b09b76dc513d396267a`).

**8-baseline ranking on polymer-safe test (n=165):**

| Baseline | Test R² | RMSE |
|---|---:|---:|
| B6_full_HistGBM_parent | +0.2688 | 1.734 |
| B2_T_and_wf_linear | +0.0623 | 1.964 |
| B0_constant_mean | -0.0037 | 2.032 |
| B1_arrhenius_T_only_linear | -0.0478 | 2.076 |
| B3_Vrentas_Duda_like_log_size_T_and_wf | -0.0607 | 2.089 |
| B4_morgan_only_ridge | -0.0643 | 2.092 |
| B7_hostile_null_HistGBM_y_shuffled | -0.1498 | 2.175 |
| B5_descriptor_only_HistGBM | -0.3581 | 2.363 |

Observed Phase-0 KPI outcomes (11/11 gates PASSED; `phase0_deterministic_gates_passed: true`):

- `full_ml_r2_beats_constant_baseline` gap **++0.2724** — **PASSED**
- `full_ml_r2_beats_arrhenius_T_only_baseline` gap **++0.3166** — **PASSED** (Arrhenius alone underperforms constant here — T range in ncomm 2023 too narrow for exp(E_a/RT) to dominate)
- `full_ml_r2_beats_vrentas_duda_like_physical_baseline` gap **++0.3295** — **PASSED** (simplified free-volume physical baseline R² -0.0607 fails; full Vrentas-Duda 1977 model with van der Waals volumes is Phase-1 scope)
- `full_ml_r2_beats_morgan_only_ridge_baseline` gap **++0.3330** — **PASSED**
- `full_ml_r2_beats_hostile_null_y_shuffled` gap **++0.4186** — **PASSED** (confirms real signal learned)
- `hostile_null_r2_within_2_sigma_of_constant_permissive` — **PASSED** (permissive floor for small n=165)
- `ml_beats_every_baseline_except_itself` — **PASSED** (full HistGBM ranks first across all 8 baselines)
- `n_baselines_evaluated_at_least_6` observed **8** — **PASSED**
- Housekeeping: parent_receipt_hash_bit_stable, conformal_receipt_hash_bit_stable, input_csv_hash_bit_stable, byte_stable_two_replay_pipeline

**HONEST INTERPRETATION**. On the polymer-safe ncomm 2023 within-source
test set (n=165, 16 novel polymer SMILES held out), the full ML HistGBM
achieves R² = +0.2688 while every other baseline is at or below R² = +0.06.
The simplified Vrentas-Duda-like physical baseline (log D ~ 1/T + wf +
log Mw, 4 fitted parameters) fails with R² = -0.0607 — the free-volume
physics with simplified parameters cannot capture the observed diffusivity
variance. Full ML wins across the board but the absolute R² of 0.27
is modest — reflecting the difficulty of polymer-safe diffusivity
generalization documented in the prior conformal+AD receipt (which
found polymer-safe test R² of 0.45 on a slightly different partition;
here 0.27 with n=16 test polymers vs the earlier 5 test scaffolds).

The theory stack: Arrhenius 1889; Stokes 1851 / Einstein 1905;
Vrentas & Duda 1977 J. Polym. Sci. Polym. Phys. 15: 403-416; Ferry 1980
Ch. 12; Fick 1855; Rogers & Hahn 2010 Morgan/ECFP; Hoerl & Kennard 1970
Ridge; Ke et al 2017 LightGBM.

Claim scope: this KPI documents ML value-add over 7 named non-ML
baselines including a simplified physical free-volume baseline on
Polyverse diffusivity ncomm 2023 within-source subset. Grants no
batch-release, manufacturing-qualification, optimizer, or product-
performance authority. Phase-1 explicitly flags: full Vrentas-Duda 1977
free-volume model with van der Waals volumes and fitting parameters;
chemistry-aware graph neural network baseline; wet-lab diffusivity
validation on ≥15 novel-chemistry polymers at multiple T and wf.


### Empirical benchmark result — corrosion-rate QSPR, metallurgical-family-safe (promoted to KPI, campaign item V1-KPI-BARR)

`benchmarks/corr-rate-family-safe-v1/corr-rate-family-safe-receipt.v1.dsse.json`
(AUDIT_ONLY, 2026-08-03) is a falsification attack on `corr-rate-qspr-v1`'s
leave-material-out headline (`GroupKFold(group=material)`, HistGBM
R²=0.316). `GroupKFold(group=material)` never separates near-duplicate
alloy-name aliases of the same metallurgical family (e.g. 316/316L/316LN/
316Ti; Hastelloy-C-276/Alloy-C-276/Inco-C-276), so it can overstate
generalization. Re-running the identical feature engineering, HistGBM
hyperparameters, seed, and metrics with the group axis changed to
metallurgical **family** (17 families; ASM Handbook Vol.3; Sedriks 1996;
Uhlig-Revie 2008) on the identical classified subset (n=7,282, 94.58%
coverage) gives: material-safe R²=0.3555, family-safe R²=0.1321 — a 62.8%
relative reduction, confirming meaningful within-family alias leakage.
Verdict `CLAIM_SURVIVED`: the pre-registered refutation bar (R²<=0 or losing
to the best naive baseline) was not met — family-safe R² stays positive and
still beats the best naive baseline on RMSE by 7.05%.

Campaign item **V1-KPI-BARR** (2026-08-04) promoted this result into
`evidence/phase0/kpis/corr-rate-family-safe-qspr-kpi.v1.dsse.json`
(DSSE-signed) with the leakage indicator stated explicitly (r2_drop,
62.8% relative reduction, and the weakest of 5 folds at R²≈0, which is
disclosed but does not itself breach the pre-registered criterion). This
is the module's strongest **rights-clean** empirical claim: NIST CORR-DATA
(Dow Chemical Co.) is `DERIVATIVE_ALLOWED` with `rights_gate_passed=true`
and `independently_reviewed=true` in `source-lock.v2.json`, unlike the
module's other two Phase-0 KPIs, which both rest on the Polyverse
solvent-diffusivity dataset (portfolio data-rights map: `CONTEXT_ONLY` /
quarantined pending human rights review). Before promotion, the source
receipt's Ed25519 signature was independently re-verified and the exact
harness (`corr_rate_family_safe.py`, same SHA-256, seed=0) was re-run from
scratch, reproducing a byte-identical canonical result hash to the
original two-replay-gated receipt — the claim was re-attacked, not just
copied forward.

Scope ceiling unchanged from `corr-rate-qspr-v1`: bare-metal/alloy
substrate corrosion (NIST CORR-DATA), NOT organic-coating barrier
performance. No candidate/coating superiority claim; no batch-release,
manufacturing-qualification, optimizer, or product-performance authority.


### Falsification attack — corrosion-rate QSPR family-safe KPI under true leave-one-family-out (SURVIVED, narrow)

`benchmarks/corr-rate-family-lofo-v1/corr-rate-family-lofo-receipt.v1.dsse.json`
(AUDIT_ONLY, ROTATION-mode, 2026-08-14) attacks the promoted
`corr-rate-family-safe-qspr-kpi.v1.dsse.json` (GroupKFold(group=
metallurgical_family, 5-fold) HistGBM R2=0.132087, called above "the
module's strongest rights-clean empirical claim"). That KPI's own 5-fold
split naturally isolates the 2 largest of 17 families (stainless_steel
n=1976, nickel_alloy n=1888, 53.1% of the classified cohort) into solo
folds and packs the other 15 into only 3 folds, so its R2 is a
sample-weighted (per-row) statistic dominated by whichever families are
large — not a fair test of a "generalizes across families" claim.

This re-runs the identical feature engineering, HistGBM hyperparameters,
and seed with true Leave-One-Family-Out (17 folds, one family held out
at a time) and reports the family-weighted (unweighted-per-family) mean
R2 alongside the sample-weighted OOF statistic. Pre-registered refutation
criterion: REFUTED if family-weighted mean R2 (over the 15 families with
n_test>=20; chromium n=6 and molybdenum n=2 excluded as statistically
unreliable) is <=0, OR if a majority of those families individually score
R2<=0. Result: family-weighted mean R2 = **0.015964** — a collapse from
the KPI's sample-weighted 0.132087, and essentially noise-level — with 11
of 15 eligible families (73.3%, a bare majority) scoring R2>0. The
criterion is **not met**, so the claim survives, but only just. Four
sizeable families generalize badly under genuine leave-out: titanium
(n=658, R2=-0.0257), tantalum_niobium (n=266, R2=-0.6616), zinc (n=60,
R2=-0.799), magnesium (n=57, R2=-0.7081). The two families the KPI's own
5-fold split happened to isolate cleanly are also the two that generalize
best (R2=0.166, R2=0.118) and are what keep both the sample-weighted and
family-weighted numbers positive. Positive control: an identical LOFO run
on a fully label-shuffled (hostile-null) copy of the same input correctly
triggers the refutation criterion (family-weighted mean R2=-0.0501,
majority non-positive), confirming the criterion is capable of firing.

Honest reading: `corr-rate-family-safe-qspr-kpi.v1.dsse.json`'s R2=0.132
should NOT be read as "generalizes to novel metallurgical families" in
general — it reflects reliable generalization to the two dominant
chemistries in the NIST CORR-DATA cohort (stainless steels, nickel
alloys) and unreliable-to-negative generalization to roughly a quarter of
the smaller/rarer families. This nuance is not present in the promoted
KPI's payload and should accompany any citation of that R2 number.

- **X-COV-CPVC (2026-08-15, `evidence/phase0/repairs/X-COV-CPVC/done/X-COV-CPVC.done-receipt.v1.dsse.json`): CLAIM_REFUTED.**
  `coverage-spreading-v1` (signed 2026-07-29, `COVERAGE_SPREADING_ENGINE_READY__KNOWN_ANSWER_BATTERY_PASS__1604_ANCHOR_EXACT`) computes wet-film-thickness/theoretical-coverage from a void-free closure identity (`WFT * VS_frac == DFT` exactly) with zero PVC/CPVC awareness -- none of its 9 known-answer cases or scope notes mention pigment loading. Its own sibling receipt `reduced-pvc-porosity-v1` (signed two days later, 2026-07-31) had already established that above the Bierwagen CPVC a real dry film's volume is amplified by `LAMBDA = PVC/CPVC` versus void-free packing, and named an iron-oxide-red anti-corrosion primer at PVC 0.50 (CPVC 0.4183, `LAMBDA` 1.1953) as its own worked in-domain example -- but that finding was never propagated back into `coverage-spreading-v1` as a repair or disclosed scope boundary. This fire independently reimplemented both engines from their published source, reproduced both receipts' point estimates bit-exact, and composed them: applying `coverage-spreading-v1`'s own signed WFT prescription (190.30 um) to this in-domain porous primer at its own declared 127 um DFT target yields an actual film build of 151.79 um, a +19.53% overshoot (and a -16.33% dry-film-density error) -- about 19.5x the receipt's own `at_nominal_dft` calibrated 95% interval half-width. A below-CPVC control case (PVC 0.35) showed exactly 0.0% divergence, confirming the bias is the CPVC/porosity effect and not a reimplementation artifact. `coverage-spreading-v1` is READY only for the undisclosed below-CPVC subset of the module's declared applicability domain. See the done receipt for the full composition, reproduction checks, and proposed_followups.

- **X-COV-CPVC (2026-08-15, `evidence/phase0/repairs/X-COV-CPVC/done/X-COV-CPVC.done-receipt.v1.dsse.json`): CLAIM_REFUTED.**
  `coverage-spreading-v1` (signed 2026-07-29, `COVERAGE_SPREADING_ENGINE_READY__KNOWN_ANSWER_BATTERY_PASS__1604_ANCHOR_EXACT`) computes wet-film-thickness/theoretical-coverage from a void-free closure identity (`WFT * VS_frac == DFT` exactly) with zero PVC/CPVC awareness -- none of its 9 known-answer cases or scope notes mention pigment loading. Its own sibling receipt `reduced-pvc-porosity-v1` (signed two days later, 2026-07-31) had already established that above the Bierwagen CPVC a real dry film's volume is amplified by `LAMBDA = PVC/CPVC` versus void-free packing, and named an iron-oxide-red anti-corrosion primer at PVC 0.50 (CPVC 0.4183, `LAMBDA` 1.1953) as its own worked in-domain example -- but that finding was never propagated back into `coverage-spreading-v1` as a repair or disclosed scope boundary. This fire independently reimplemented both engines from their published source, reproduced both receipts' point estimates bit-exact, and composed them: applying `coverage-spreading-v1`'s own signed WFT prescription (190.30 um) to this in-domain porous primer at its own declared 127 um DFT target yields an actual film build of 151.79 um, a +19.53% overshoot (and a -16.33% dry-film-density error) -- about 19.5x the receipt's own `at_nominal_dft` calibrated 95% interval half-width. A below-CPVC control case (PVC 0.35) showed exactly 0.0% divergence, confirming the bias is the CPVC/porosity effect and not a reimplementation artifact. `coverage-spreading-v1` is READY only for the undisclosed below-CPVC subset of the module's declared applicability domain. See the done receipt for the full composition, reproduction checks, and proposed_followups.

- **X-COV-CPVC (2026-08-15, `evidence/phase0/repairs/X-COV-CPVC/done/X-COV-CPVC.done-receipt.v1.dsse.json`): CLAIM_REFUTED.**
  `coverage-spreading-v1` (signed 2026-07-29, `COVERAGE_SPREADING_ENGINE_READY__KNOWN_ANSWER_BATTERY_PASS__1604_ANCHOR_EXACT`) computes wet-film-thickness/theoretical-coverage from a void-free closure identity (`WFT * VS_frac == DFT` exactly) with zero PVC/CPVC awareness -- none of its 9 known-answer cases or scope notes mention pigment loading. Its own sibling receipt `reduced-pvc-porosity-v1` (signed two days later, 2026-07-31) had already established that above the Bierwagen CPVC a real dry film's volume is amplified by `LAMBDA = PVC/CPVC` versus void-free packing, and named an iron-oxide-red anti-corrosion primer at PVC 0.50 (CPVC 0.4183, `LAMBDA` 1.1953) as its own worked in-domain example -- but that finding was never propagated back into `coverage-spreading-v1` as a repair or disclosed scope boundary. This fire independently reimplemented both engines from their published source, reproduced both receipts' point estimates bit-exact, and composed them: applying `coverage-spreading-v1`'s own signed WFT prescription (190.30 um) to this in-domain porous primer at its own declared 127 um DFT target yields an actual film build of 151.79 um, a +19.53% overshoot (and a -16.33% dry-film-density error) -- about 19.5x the receipt's own `at_nominal_dft` calibrated 95% interval half-width. A below-CPVC control case (PVC 0.35) showed exactly 0.0% divergence, confirming the bias is the CPVC/porosity effect and not a reimplementation artifact. `coverage-spreading-v1` is READY only for the undisclosed below-CPVC subset of the module's declared applicability domain. See the done receipt for the full composition, reproduction checks, and proposed_followups.

### Falsification attack — Polyverse diffusivity conformal coverage under temperature-regime shift (SURVIVED)

`benchmarks/polyverse-diffusivity-temperature-shift-v1/polyverse-diffusivity-temperature-shift-receipt.v1.dsse.json`
(AUDIT_ONLY, 2026-08-02) attacks the within-source conformal-coverage and
AD-interior-reliability claims of the receipt above. The receipt's
applicability-domain (AD) score is purely structural
(Morgan-fingerprint Tanimoto to nearest training polymer scaffold) and
does not encode temperature or weight fraction. This attack trains and
calibrates split-conformal ONLY on the bulk T<=308K regime of ncomm(2023)
and evaluates on the held-out T>308K regime (293-413K full range; a
realistic elevated-temperature coating-service extrapolation), paired
against a matched-T control across 10 independent scaffold-partition
seeds, refitting the model each time.

Pre-declared refutation criterion: a one-sided paired t-test (alpha=0.05)
that shifted-regime coverage is significantly lower than the matched-T
control's coverage, for either the full shifted set or the
AD-flagged-in-domain subset of it. Observed: mean shifted coverage 0.8899
vs mean matched-T control coverage 0.9121 (paired t=-1.084, p=0.1532,
not significant); AD-flagged-in-domain subset mean 0.8918 vs control
(t=-0.852, p=0.2081, not significant). The matched-T control itself
swings from 0.7768 to 1.0000 across seeds, showing this n=424 / ~10-49
scaffold-per-arm benchmark is underpowered to detect anything but a
large covariate-shift effect — an honest power caveat, not a clean pass.
Verdict: `CLAIM_SURVIVED`. The attack was genuinely capable of
falsifying (a stable, seed-independent coverage collapse under T-shift
would have been detected); none was observed at this sample size.

### Known contradictions

- The checked implementation is a directional barrier proxy; no blinded independent panel ranking establishes candidate corrosion performance.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.barrier_index`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-barrier-corrosion-score-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.barrier_index`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `MODELED_DIRECTIONAL` and solver-use ceiling is `AUDIT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **blinded Kendall tau** at `metrics.barrier_index`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Blinded four-track independent-panel comparison with Kendall tau >= 0.5 and superiority over solids-only and PVC-only hostile nulls; Phase 2 repeats with separate material lots and a separate laboratory.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Independent blinded corrosion panels and four-track comparison data

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-barrier-corrosion-score/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Recover a synthetic full circuit while rejecting short spectra and field/lab method substitution.
