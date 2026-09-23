# RETRACTION INDEX

## R-A12 reinstatement of launcher-discarded fires (interactive-2026-08-03)

Retracted claim: the two receipts below carry a portfolio-valid DSSE signature. They were in fact
signed with the unanchored LOCAL_DEVELOPMENT_AUDIT_ONLY key `local-9028773f49591193`, so the
launcher verifier discarded both fires (verified_new_signed=0, verdicts downgraded to UNKNOWN).
The SCIENCE of both receipts was re-executed and reproduced the committed canonical diagnostics
byte-exact; the original SURVIVED verdicts are reinstated under the pinned PHASE0_EVALUATOR key.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `benchmarks/role-live-runtime-domain-probe-v1/replay_receipt.v1.dsse.json` (sha256 `00a14694...`) is signed under a trust-anchored Phase-0 key; fire 20260802T150002-1413344-9b251899480d SURVIVED verdict is portfolio-verifiable as signed | amphora-molecule-role-ranker/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json (documents the wrong-key defect; local-dev signature verified, pinned-key verification fails) | amphora-molecule-role-ranker/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json (anchored re-issue; SURVIVED verdict reinstated, re-attack byte-exact) | 2026-08-03 |
| `benchmarks/role-reactivity-ratio-substitution-effect-v1/replay_receipt.v1.dsse.json` (sha256 `1ccc3b6c...`) is signed under a trust-anchored Phase-0 key; fire 20260803T030002-168451-6ef0580e79cf SURVIVED verdict is portfolio-verifiable as signed | amphora-molecule-role-ranker/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json (documents the wrong-key defect) | amphora-molecule-role-ranker/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json (anchored re-issue; SURVIVED verdict reinstated, re-attack byte-exact) | 2026-08-03 |

Original receipts left byte-intact in place (supersede-never-rewrite); before/after sha256 recorded in the batch receipt payload.

## R-N02 - coordinated C=N (amidine/guanidine) categorical fix (interactive-2026-08-03)

Scope note: GENERALIZATION INFERENCE ONLY is retracted. The flagship KPI's
`structural_inference_agreement_rate` = 1.0 ARITHMETIC STANDS and the KPI file is unmodified: the sha-locked
39-record fixture contains no amidine/guanidine record, so no fixture record was ever mis-scored by this bug -
independently re-verified under R-N02 by re-deriving all 39 records through the REAL production RDKit FFI both
pre- and post-fix (byte-identical, and 39/39 agreeing with the fixture's own recorded facts). What was refuted
is the inference that the deterministic role rule fails closed on real out-of-domain accelerator chemotypes
generally. The guanidine chemotype is now handled: `bridge.cc::count_reactive_amine_hydrogens` excludes N-H on
an amidine/guanidine carbon (C=N), so DPG and DOTG derive count 0 and fail closed to `out_of_domain`. New
regression tests through the real FFI: `amphora-molecule-capabilities/src/lib.rs::role_ranker_fails_closed_on_guanidine_class_accelerators_via_real_ffi`
and `amphora-rdkit-ffi/src/lib.rs::pinned_native_backend_excludes_guanidine_class_amine_hydrogens` (DPG, DOTG,
guanidine, DICY, biguanide). The original refuting attack, re-run UNMODIFIED, now returns
HYPOTHESIS_CORROBORATED (2/2 probes pass, 0 disagreements); the earlier live-runtime hostile-null probe still
passes 9/9. The sha-locked fixture was NOT edited; `reference/phase0-role-known-answer.v2.json` was created
alongside with the 39 v1 records byte-identical plus the 5 guanidine-class `out_of_domain` records the
refuting receipts' follow-ups asked for (evidence only; the signed KPI remains bound to v1). Quantitative question EXPLICITLY LEFT OPEN: whether guanidine/amidine N-H is exactly 0 in an AHEW / equivalent-weight sense is a mechanistic nucleophilicity question that R-N02 does NOT close (both refuting receipts scoped themselves the same way). R-N02 repairs CATEGORICAL CLASSIFICATION ONLY.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| The generalization inference from `amphora-molecule-role-ranker/evidence/phase0/kpis/role-classification-kpi.v1.json` (sha256 `88689040...`, `structural_inference_agreement_rate` 1.0) plus the prior `role-live-runtime-domain-probe-v1` SURVIVED verdict: that the deterministic role rule fails closed on real out-of-domain accelerator/catalyst chemotypes generally | `amphora-molecule-role-ranker/benchmarks/role-guanidine-accelerator-domain-probe-v1/replay_receipt.v1.dsse.json` (sha256 `414a68af...`, verdict CLAIM_REFUTED; DPG CAS 102-06-7 and DOTG CAS 97-39-2 classified `hardener` with `reactive_amine_hydrogen_count` 3 through the real FFI) | `amphora-molecule-role-ranker/evidence/phase0/repairs/R-N02/done/rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json` (sha256 `2edb3eab0bdec5447eed48753c4f202e7b3c8492e218172bd1aec7bce53eb1a8`) - coordinated with `amphora-rdkit-ffi/evidence/phase0/repairs/R-N02/done/rn02-rdkit-ffi-coordinated-cn-fix-repair-receipt.v1.dsse.json` (sha256 `07e00ec5f7bd9a172ac4da3d26e239d8699045d04a3eff4806434c779b022fbe`) and `amphora-molecule-property/evidence/phase0/repairs/R-N02/done/rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json` (sha256 `bdd71b4044c6f4975e8fa6c9754251567c9f394264a24a1880d40065186737f3`) | 2026-08-03 |

Original receipts and the sha-locked fixture left byte-intact in place (supersede-never-rewrite); before/after
sha256 of every signed artifact in scope recorded in the R-N02 done-receipt payloads.

## W-ROLE-CI - degenerate boundary-collapsed bootstrap CIs in role-parsimony-conformal-v1 (cron-2026-08-14)

Retracted claim: `role-parsimony-conformal-v1/replay_receipt.v1.dsse.json` (signed under the
unanchored `local-9028773f49591193` LOCAL_DEVELOPMENT_AUDIT_ONLY key, not the pinned
PHASE0_EVALUATOR key) published three percentile-bootstrap 95% confidence intervals that
collapse to a single point because the source sample is k=n=24 (all-correct): `[1.0, 1.0]` for
`deterministic_rule_baseline.in_domain_accuracy_bootstrap_ci95`, `[1.0, 1.0]` for
`fitted_model_out_of_sample.loocv_accuracy_bootstrap_ci95`, and `[0.0, 0.0]` for
`noninferiority_test.accuracy_gap_bootstrap_ci95`. The exact Clopper-Pearson two-sided 95% lower
bound at k=n=24 is 0.8575264022774743, not 1.0 -- the published interval understated 95%
uncertainty by 0.1425. Point estimates (accuracy 1.0 vs 1.0, gap 0.0) and the
`HYPOTHESIS_CORROBORATED_PARSIMONY_FAVOURED` noninferiority verdict are UNCHANGED; only the
interval admissibility was wrong.

Repair: Clopper-Pearson exact CI (Clopper & Pearson 1934) for both accuracy margins; MOVER
(Newcombe 1998b, phi=0 conservative variant) paired-difference CI for the gap, built from each
margin's own Clopper-Pearson limits since correlation is inestimable at full concordance (0/0).
Portfolio sweep (7170/7176 .json files parsed, 6 non-JSON/parse errors) for the same defect class
found one further live instance outside this module, already under active repair there
(`amphora-molecule-generator` R-A06/R-A06v2/W-GEN1) -- named, not duplicated.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-molecule-role-ranker/benchmarks/role-parsimony-conformal-v1/replay_receipt.v1.dsse.json` (sha256 `1fe0e84b7d50663e31e2a4b8ee5d881dffce378d931c0779444e67d1e87624fb`) bootstrap CIs at k=n=24 | this same superseding receipt documents and refutes the interval-admissibility claim in place | `amphora-molecule-role-ranker/evidence/phase0/repairs/W-ROLE-CI/done/w-role-ci-superseding-kpi-receipt.v1.dsse.json` | 2026-08-14 |

Original receipt and diagnostic left byte-intact in place (supersede-never-rewrite); before/after
bounds and full method justification recorded in the W-ROLE-CI done-receipt payload.
