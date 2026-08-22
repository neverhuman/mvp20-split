# RETRACTION INDEX - amphora-molecule-property

Append-only index of superseded claims. Entries record what was retracted/superseded, by what, and when. Original artifacts are never modified or deleted.

## R-A11 - anchored signature-identity re-issue (2026-08-03)

Scope note: SIGNATURE IDENTITY ONLY is superseded. The scientific content of the original receipt is NOT retracted; it carries forward unchanged (re-verified byte-intact) under the anchored re-issue.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| The DSSE signature identity of `amphora-molecule-property/benchmarks/phys-ml-stack-comparison-c8-fire2-clean-subset-v1/c8_fire2_dielectric_clean_subset_receipt.v1.json` (keyid `local-9028773f49591193`) is a trust-anchored Phase-0 evaluator identity resolvable in `config/phase0-trust-store.v1.json` | `amphora-molecule-property/benchmarks/phys-ml-stack-comparison-c8-fire2-clean-subset-v1/c8_fire2_dielectric_clean_subset_receipt.v1.json` (its own signature/signing_key block records the defective identity; strict trust-store lookup fails) | `amphora-molecule-property/benchmarks/phys-ml-stack-comparison-c8-fire2-clean-subset-v1/c8_fire2_dielectric_clean_subset_receipt.v1.anchored-reissue.v1.json` (anchored re-issue, keyid `phase0-evaluator-3ef6b35...`; repair_item R-A11, repair_mode interactive-2026-08-03) | 2026-08-03 |

## R-A09 - definitive per-KPI status index (2026-08-03)

Scope note: STATUS ANNOTATION ONLY. No KPI file is modified, deleted, or scientifically re-derived here. This section supersedes the unannotated presentation of the 21-file KPI surface (all files dated 2026-07-23) by recording, per KPI, the verdict state established by the module's signed refutation/retraction receipts (C7 fires 1-3, C8 fires 1-3, W2 fires 1-3, W3, W7, W8 - 12 falsification-ledger entries). Full evidence citations with sha256 pins, re-attack reproductions, and rationale per row are embedded in the signed index receipt: `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` (payload_canonical_sha256 `39babe8f08f3d02e6714ddfa412c6932c4197adda3d6ed2d3839e6f6d738f1bc`).

Status counts: STANDS 10 / STANDS-WITHIN-CORPUS-ONLY 7 / REFUTED 2 / RETRACTED 2 (21 live KPI files; +1 pre-existing superseded KPI in appendix).

| claim (KPI receipt) | status | refuted-by / retracted-by receipt path | superseded-by (index) | date |
|---|---|---|---|---|
| `openpoly-dielectric-constant-ml-baseline-kpi.v1.json` | STANDS | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `openpoly-experimental-tg-ml-baseline-kpi.v1.json` | STANDS-WITHIN-CORPUS-ONLY | amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final/c7_final_tg_density_external_validity_verdict_receipt.v1.json | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `openpoly-water-contact-angle-ml-baseline-kpi.v1.json` | STANDS | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `openpoly-water-uptake-ml-baseline-audit-kpi.v1.json` | STANDS | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `external-validation-dielectric-ml-openpoly-to-radonpy-kpi.v1.json` | RETRACTED | amphora-molecule-property/evidence/audit/dielectric-retraction-v1/dielectric-retraction-superseding-kpi-receipt.v1.dsse.json | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `mixed-openpoly-radonpy-dielectric-conformal-kpi.v1.json` | RETRACTED | amphora-molecule-property/evidence/audit/dielectric-retraction-v1/dielectric-retraction-superseding-kpi-receipt.v1.dsse.json | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `mixed-openpoly-radonpy-refractive-index-conformal-kpi.v1.json` | STANDS-WITHIN-CORPUS-ONLY | amphora-molecule-property/evidence/audit/multitarget-macro-bisection-external-validity-w7-v1/multitarget-macro-bisection-external-validity-receipt.v1.dsse.json | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `multi-target-ml-radonpy-4-properties-audit-kpi.v1.json` | REFUTED | amphora-molecule-property/evidence/audit/multitarget-macro-bisection-external-validity-w7-v1/multitarget-macro-bisection-external-validity-receipt.v1.dsse.json | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `radonpy-density-ml-vs-van-krevelen-physics-kpi.v1.json` | STANDS-WITHIN-CORPUS-ONLY | amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final/c7_final_tg_density_external_validity_verdict_receipt.v1.json | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `stacked-ml-van-krevelen-density-radonpy-kpi.v1.json` | STANDS-WITHIN-CORPUS-ONLY | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `polyuniverse-epoxy-tg-conformal-coverage-and-applicability-domain-kpi.v1.json` | STANDS-WITHIN-CORPUS-ONLY | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-kpi.v1.json` | STANDS | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `polyuniverse-epoxy-tg-named-baseline-benchmark-kpi.v1.json` | STANDS-WITHIN-CORPUS-ONLY | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `polyuniverse-epoxy-tg-van-krevelen-physical-baseline-vs-ml-kpi.v1.json` | STANDS-WITHIN-CORPUS-ONLY | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `van-krevelen-ridge-fit-on-1000-polyuniverse-polymers-kpi.v1.json` | REFUTED | amphora-molecule-property/evidence/audit/vk-ridge-ygi-admissibility-w8-v1/vk-ridge-ygi-admissibility-audit-receipt.v1.dsse.json | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `van-krevelen-ridge-retuned-Ygi-on-15-canonical-homopolymers-kpi.v1.json` | STANDS | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `van-krevelen-tg-corrected-formula-on-15-canonical-homopolymers-kpi.v1.json` | STANDS | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `van-krevelen-tg-external-validation-15-canonical-homopolymers-kpi.v1.json` | STANDS | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `van-krevelen-tg-LOO-rescaled-15-canonical-homopolymers-kpi.v1.json` | STANDS | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `external-validation-polyuniverse-ridge-on-openpoly-tg-kpi.v1.json` | STANDS | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `coating-candidate-design-card-5-canonical-epoxy-amines-kpi.v1.json` | STANDS | none - no refuting receipt targets this KPI (ledger grep pinned in index receipt) | `amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json` | 2026-08-03 |
| `property-eew-ahew-kpi.v1.json` (pre-existing supersession) | SUPERSEDED-PRE-EXISTING | n/a - superseded 2026-07-22, before the live surface existed | `amphora-molecule-property/evidence/superseded/supersession-1bac03f7ce37353693e21b5acf3d85626a34052d7154f55d724901e8ea687ff1/phase0/kpis/property-eew-ahew-kpi.v1.json` | 2026-08-03 |

Notes: RETRACTED = superseding retraction receipt `amphora-molecule-property/evidence/audit/dielectric-retraction-v1/dielectric-retraction-superseding-kpi-receipt.v1.dsse.json` (W3) plus machine-readable entries in `logs/claims-requiring-retraction.jsonl` (lines 1-2). STANDS-WITHIN-CORPUS-ONLY = within-corpus numbers stand as measured; cross-corpus/out-of-macro-chemotype transfer refuted (C7 final receipt for Tg+density, W7 for refractive index+thermal conductivity). Repair spec counted 22 KPI files; the live surface holds exactly 21 - see count_discrepancy_note in the index receipt.

## R-N02 - coordinated C=N (amidine/guanidine) categorical fix (interactive-2026-08-03)

Scope note: GENERALIZATION CLAIM ONLY is retracted. The amine-class receipt's arithmetic on its own 26
records is NOT retracted - all 26 (3 exact anchors + 6 monodisperse + 13 amine-class grid + 7 nonamine
controls + 1 hydroxyl probe) were re-derived pre- and post-fix and are byte-identical. The shipped rule
`n_active_amine_nh()` now excludes an N-H whose attached carbon bears a C=N double bond to another
nitrogen, symmetric with the pre-existing C=O/C=S amide exclusion; the extension was adopted verbatim from
the refuting receipt's own prototype ({"O","S"} -> {"O","S","N"}). The original refuting attack, re-run
UNMODIFIED, now returns SURVIVED. Quantitative question EXPLICITLY LEFT OPEN: whether guanidine/amidine N-H is exactly 0 in an AHEW / equivalent-weight sense is a mechanistic nucleophilicity question that R-N02 does NOT close (both refuting receipts scoped themselves the same way). R-N02 repairs CATEGORICAL CLASSIFICATION ONLY.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-molecule-property/benchmarks/amine-class-active-nh-robustness-v1/amine_class_active_nh_robustness_receipt.v1.json` (sha256 `74e2c759...`) generalizes its active-N-H structure rule to the amine-hardener structure class as a whole (`amine_grid_classification_accuracy` 1.0, `nonamine_fail_closed_rate` 1.0 beyond the 13 tested structures) - i.e. guanidine/amidine-class curing agents are correctly classified | `amphora-molecule-property/evidence/audit/amine-nh-guanidine-conjugation-gap-v1/amine-nh-guanidine-conjugation-gap-receipt.v1.dsse.json` (sha256 `59c447c0...`, verdict REFUTED; guanidine/DICY/biguanide counted 4/4/5 active N-H, yielding a confident finite theoretical AHEW e.g. DICY 21.02 g/eq) | `amphora-molecule-property/evidence/phase0/repairs/R-N02/done/rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json` (sha256 `bdd71b4044c6f4975e8fa6c9754251567c9f394264a24a1880d40065186737f3`) - coordinated with `amphora-rdkit-ffi/evidence/phase0/repairs/R-N02/done/rn02-rdkit-ffi-coordinated-cn-fix-repair-receipt.v1.dsse.json` (sha256 `07e00ec5f7bd9a172ac4da3d26e239d8699045d04a3eff4806434c779b022fbe`) and `amphora-molecule-role-ranker/evidence/phase0/repairs/R-N02/done/rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json` (sha256 `2edb3eab0bdec5447eed48753c4f202e7b3c8492e218172bd1aec7bce53eb1a8`) | 2026-08-03 |

Original receipts left byte-intact in place (supersede-never-rewrite); before/after sha256 of every signed
artifact in scope recorded in the R-N02 done-receipt payloads.

## R-B3 - mission prose retraction sweep (2026-08-04)

Scope note: PROSE SURFACE ONLY. This section supersedes narrative claims in `amphora-molecule-property/docs/mission.md` that contradicted this module's signed refutation/retraction receipts. The mission FRONT-MATTER (the JSON between the leading `---` fences) is byte-identical before and after the repair (sha256 `696de56f52698915dfda89d45a85010d2053f0ba03e108338096653ecc13be5c` both sides). No KPI receipt, signed artifact, locked fixture, benchmark lock, manifest, honesty/authority ceiling, or falsification-ledger entry is modified. 20 prose passages repaired; 21 stale strings re-attacked to zero occurrences. mission.md sha256 `d7488f02f94c3349f4a00e1201bd08f22a69ffdd475998ecefcbf58950105d89` -> `94fecbab755108b8f7be995bdebe63b4b99788a78e445e33c2f2a524e2ff648c`. Every old->new prose pair is quoted in full in the signed done-receipt: `amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json`.

Honest scope correction recorded here because it inverts part of the repair brief: the OpenPoly-only dielectric numbers advertised in mission.md (holdout MAE 0.4040 eps_r, holdout R2 +0.5649, LOSO-CV R2 +0.6591, n=295) were **not** retracted and are **not** treated as retracted. W3 dispositions `openpoly-dielectric-constant-ml-baseline-kpi.v1.json` (sha256 `cf94eb18...`) as `NOT_RETRACTED_LABELS_ADMISSIBLE` - OpenPoly's own dielectric column has 0/295 Frohlich violations, and the 89.5% label defect is isolated to RadonPy PI1070's MD fluctuation-formula route. What was stale, and what R-B3 repairs, is the module-/portfolio-LEVEL dielectric **capability** claim built on those within-corpus numbers, which contradicts C8 fire 3's consolidated `NO COMPETENT MODEL` founder-panel row and W3's `prior_numbers_withdrawn`. Falsely retracting a standing result would itself have been a receipt-contradicting edit.

Sweep completeness: the RETRACTED/REFUTED RadonPy-derived KPIs (`external-validation-dielectric-ml-openpoly-to-radonpy`, `mixed-openpoly-radonpy-dielectric-conformal`, `mixed-openpoly-radonpy-refractive-index-conformal`, `multi-target-ml-radonpy-4-properties-audit`, `radonpy-density-ml-vs-van-krevelen-physics`, `stacked-ml-van-krevelen-density-radonpy`) had **no prose surface at all** in the pre-repair mission.md - case-insensitive counts in that file were RadonPy 0, PI1070 0, refractive 0, "thermal conductivity" 0, density 0, multi-target 0, eps_static 0. Nothing to repair for those rows.

| claim (mission.md prose, pre-repair) | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| L885 / L887-889 / L956-959: dielectric section advertises "REAL POSITIVE lift", "Directly delivers the coating IP prediction capability for POLYMER DIELECTRIC CONSTANT", and "`amphora-molecule-property` can now offer polymer dielectric constant prediction with a defended MAE ~0.40 eps_r units ... Directly applicable to coating chemistry decisions for electrical-insulation applications" | `amphora-molecule-property/evidence/audit/dielectric-retraction-v1/dielectric-retraction-superseding-kpi-receipt.v1.dsse.json` (W3, `CLAIM_REFUTED`) and `amphora-molecule-property/benchmarks/phys-ml-stack-comparison-c8-v3-final/c8_fire3_final_consolidated_receipt.v1.json` (`founder_f8_panel_row_text.dielectric_constant` = "NO COMPETENT MODEL -- label integrity failure ...") | `amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json` (repairs S7, S8, S9, S10, S11) | 2026-08-04 |
| L905 "**MAJOR POSITIVE FINDING**" and L938-940 "**REAL predictive capability**" presented without corpus scope | `amphora-molecule-property/evidence/audit/dielectric-retraction-v1/dielectric-retraction-superseding-kpi-receipt.v1.dsse.json` (upholds the n=295 numbers ONLY "scoped explicitly to the OpenPoly literature population") | `amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json` (repairs S9, S10) | 2026-08-04 |
| L733 "**MAJOR POSITIVE FINDING**: Ridge Y_gi fit BEATS the published-values baseline by 32.6 K ... reaching Bicerano-level accuracy"; L771 "The 24-group STRUCTURE is CONFIRMED CORRECT at scale"; L773 "The prior 'under-determination' hypothesis is RESOLVED"; L777 "Fitted Y_gi values are chemistry-plausible ... not structural mismatch"; L779 "this receipt proves that a 24-group Van Krevelen calibration can achieve Bicerano-level MAE" | `amphora-molecule-property/evidence/audit/vk-ridge-ygi-admissibility-w8-v1/vk-ridge-ygi-admissibility-audit-receipt.v1.dsse.json` (W8, `REFUTED`: 2/24 fitted Y_gi sign-reversed - vinyl_CH2 -3125.15 vs published +2000, nitrile -2843.55 vs published +5500; 13/24 deviate >50%; Spearman rho -0.523 between n_train and deviation) | `amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json` (repairs S1, S2, S3, S4, S5, S6) | 2026-08-04 |
| L1102 "RESOLVES the Push #20 Phase-1 hypothesis about applicability domain"; L1108 "confirms the 24-group structure captures ordinal Tg signal"; L1126 "Confirms Push #20's Ridge Y_gi calibration has real generalization value" | `amphora-molecule-property/evidence/audit/vk-ridge-ygi-admissibility-w8-v1/vk-ridge-ygi-admissibility-audit-receipt.v1.dsse.json` (W8) - this section applies the very coefficient table W8 refutes; the KPI's own numbers stand (index status STANDS) but the structural re-assertion does not | `amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json` (repairs S12, S13, S14) | 2026-08-04 |
| L1195-1204 "ML strictly dominates the frozen physics-Ridge inference" / "**Portfolio priority**: ... the ML pipeline should be the primary predictor" / "**Positive R2 on rigorous LOSO-CV** confirms cross-scaffold generalization"; L1220 "Applicability domain restricted to the openpoly scaffold distribution." | `amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final/c7_final_tg_density_external_validity_verdict_receipt.v1.json` (C7 final, `CLAIM_REFUTED`: OpenPoly->Polyuniverse 6.66x degradation MAE 253.58 K R2 -92.94; reverse 16.60x MAE 231.65 K R2 -6.80; anti-predictive vs train-median null in both directions) | `amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json` (repairs S15, S17) | 2026-08-04 |
| L1206-1209 "**Portfolio-wide answer**: Combined with Push #23 (dielectric R2 +0.66) ... the `amphora-molecule-property` module now has a defended coating-IP Tg predictor" | `amphora-molecule-property/evidence/audit/dielectric-retraction-v1/dielectric-retraction-superseding-kpi-receipt.v1.dsse.json` + `amphora-molecule-property/benchmarks/phys-ml-stack-comparison-c8-v3-final/c8_fire3_final_consolidated_receipt.v1.json` + `amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final/c7_final_tg_density_external_validity_verdict_receipt.v1.json` | `amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json` (repair S16) | 2026-08-04 |
| L133-142 conformal/AD claim scope defers a "cross-dataset transfer test to an independent experimental epoxy Tg dataset" to Phase-1 as an open question | `amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final/c7_final_tg_density_external_validity_verdict_receipt.v1.json` (that test has since been run and FAILED) | `amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json` (repair S-A) | 2026-08-04 |
| L204-210 and L283-288 claim scopes for the named-baseline and Van-Krevelen-vs-ML Polyuniverse KPIs omit the STANDS-WITHIN-CORPUS-ONLY status recorded in section R-A09 above | `amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final/c7_final_tg_density_external_validity_verdict_receipt.v1.json` (governing cross-corpus refutation) plus section R-A09 of this index | `amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json` (repairs S-B, S-C) | 2026-08-04 |

Original mission.md bytes are preserved as a pre-repair snapshot at `amphora-molecule-property/evidence/phase0/repairs/B3/work/mission.md.before` (supersede-never-rewrite); the exact patch harness and the re-attack harness are checked in beside it.

### R-B3 amendment (same repair session, 2026-08-04)

Two citation-hygiene amendments were applied to the repaired mission.md prose after the 20-pair patch, both inside repair S8 and both recorded in the signed done-receipt under `target_file.amendments_after_the_20_pair_patch`: (A1) `logs/claims-requiring-retraction.jsonl` disambiguated to "the repo-root `logs/claims-requiring-retraction.jsonl`" because mission.md cites module-relative paths and there is no `amphora-molecule-property/logs/`; (A2) the two RETRACTED dielectric KPIs, first named by bare filename, expanded to `evidence/phase0/kpis/external-validation-dielectric-ml-openpoly-to-radonpy-kpi.v1.json` and `evidence/phase0/kpis/mixed-openpoly-radonpy-dielectric-conformal-kpi.v1.json` so that every inline citation resolves on disk. Final mission.md sha256 is `49ee7f1900948ccd9cc890ecdd7c1f52669bd218ba9ff6a4bc8538f7784145d7` (the `94fecbab...` value quoted in the R-B3 header above is the intermediate post-20-pair-patch hash). Front-matter remains byte-identical at `696de56f52698915dfda89d45a85010d2053f0ba03e108338096653ecc13be5c` through all three steps; the stale-string re-attack still returns 0 occurrences.

## W-PROP1 - VK Ridge KPI claim locks scope-limited by data-derived training-support threshold (2026-08-05)

Scope note: PER-GROUP CLAIM-LOCK SCOPING ONLY. The unscoped claim ("24-group structure confirmed correct
at scale") remains REFUTED per W8 above and R-A09's REFUTED status entry - it is NOT reinstated. This
section records a superseding KPI that restricts the surviving structural-correctness claim to only the
groups whose per-group training support (`n_train_polymers_with_group`, already stored in the shipped
KPI's own `fitted_Ygi_comparison` table) clears a threshold derived directly from that same table's
sign-admissibility boundary: T = 1 + max(n_train among groups whose fitted Y_gi is not sign-consistent
with its published counterpart) = 1 + 124 (`nitrile`) = 125. This is NOT the "roughly 500" placeholder
B3 had left in mission.md - it is the tightest boundary actually observed in the data, and mission.md's
placeholder language is replaced with it in the same fire. Any n_train value from 125 through 154
(the next-observed value, `carbonyl`) yields the identical 15-in/9-excluded partition, so the exact choice
within that empirical gap is immaterial.

15 in-scope groups (n_train >= 125, all sign-consistent with published): `CH2`, `CH3`, `CH`, `C_quat`,
`vinyl_CH`, `aromatic_C_H`, `aromatic_C_sub`, `ether_O`, `hydroxyl`, `carbonyl`, `amide`, `primary_amine`,
`secondary_amine`, `tertiary_amine`, `epoxide`.

9 excluded groups (n_train < 125, structural-correctness claim NOT made): `vinyl_CH2` (n=31, W8 sign-flip),
`nitrile` (n=124, W8 sign-flip), `F` (n=32), `Cl` (n=4), `Br` (n=16), `sulfone` (n=15), `sulfide` (n=1),
`ester` (n=18), `Si_O` (n=0, fitted coefficient identically 0.0/undetermined).

Honesty caveat carried forward, not hidden: sign-consistency is not the same as small magnitude error - 6
of the 15 in-scope groups (`CH2`, `vinyl_CH`, `aromatic_C_H`, `aromatic_C_sub`, `amide`, `secondary_amine`)
still deviate >50% in magnitude from published values, exactly as the original KPI already disclosed as
expected aggregate calibration drift.

Re-attack: the original W8 pre-registered refute criterion (">=1 of [scope] fitted Y_gi has sign opposite
to its published counterpart") was re-applied, restricted to the 15 in-scope groups only. Result: 0 sign
flips found -> the re-scoped claim SURVIVES. W8's own script (`compute_vk_ygi_admissibility.py`, sha256
`6c8d492103de337e9c245438ae29c2031aee2a0118c5843b2b47495bfad89c3f`) was also re-executed byte-for-byte
unmodified this fire to reconfirm the unscoped refutation is still current (2/24 sign flips, unchanged).

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-molecule-property/evidence/phase0/kpis/van-krevelen-ridge-fit-on-1000-polyuniverse-polymers-kpi.v1.json` claim_locks `24_group_structure_confirmed_correct_at_scale` / `prior_ridge_receipt_under_determination_hypothesis_now_resolved`, asserted for the full unscoped 24-group table | `amphora-molecule-property/evidence/audit/vk-ridge-ygi-admissibility-w8-v1/vk-ridge-ygi-admissibility-audit-receipt.v1.dsse.json` (W8, verdict REFUTED) | `amphora-molecule-property/evidence/phase0/repairs/W-PROP1/done/van-krevelen-ridge-scope-limited-superseding-kpi.v1.dsse.json` (W-PROP1, verdict CLAIM_SURVIVED for the 15-group re-scoped claim only) | 2026-08-05 |

Original ridge-fit KPI and W8 audit receipt left byte-intact in place (supersede-never-rewrite).


## R-C03 deliverable 1 - group-safe macro-bisection headline supersedes random-split headline (2026-08-12)

Scope note: HEADLINE PRESENTATION ONLY for this deliverable. The underlying model artifacts are
unchanged; no retraining performed. This section records that
`multi-target-ml-radonpy-4-properties-audit-kpi.v1.json`'s random-60/20/20-split R2/MAE numbers
(already recorded REFUTED in R-A09 above) are now formally superseded by a receipt that publishes
the macro-bisection group-safe-split numbers as the headline for density, refractive_index and
thermal_conductivity, with the random-split numbers demoted to a labeled within-corpus-reference-only
section. `static_dielectric_const` is excluded from the group-safe headline entirely (its defect is
label admissibility under Frohlich eps_static>=n^2, not split methodology - already RETRACTED
upstream by the W2/C8/W3 chain). Currency of the two source refutations (W7, C7 fire 2) was
reconfirmed live this fire by byte-identical re-execution of both compute scripts. A fidelity check
(does the assembled headline table exactly reproduce every number it cites from its sources?) passed
0/8 mismatches on the real table and correctly detected a deliberately planted +0.05 g/cm3
transcription defect in a corrupted copy (positive control).

This is deliverable 1 of 3 for campaign item R-C03 (multi-fire repair). Deliverables 2 (applicability-
domain gate on Tg/density predictors) and 3 (constrained non-negative VK Ridge refit) remain open.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-molecule-property/evidence/phase0/kpis/multi-target-ml-radonpy-4-properties-audit-kpi.v1.json` random-60/20/20-split headline R2/MAE numbers (refractive_index R2=0.893, thermal_conductivity R2=0.542, density R2=0.747, static_dielectric_const R2=0.389) presented without applicability-domain scope | `amphora-molecule-property/evidence/audit/multitarget-macro-bisection-external-validity-w7-v1/multitarget-macro-bisection-external-validity-receipt.v1.dsse.json` (W7) + `amphora-molecule-property/benchmarks/density-butina-cluster-external-validity-c7-v2/c7_density_macro_bisection_external_validity_receipt.v1.json` (C7 fire 2) | `amphora-molecule-property/evidence/phase0/repairs/R-C03/attempts/rc03-d1-group-safe-headline-superseding-kpi.v1.dsse.json` (R-C03 deliverable 1, verdict CLAIM_SURVIVED for the headline-fidelity claim; original random-split generalization claim remains REFUTED) | 2026-08-12 |

Original multi-target KPI, W7 receipt, and C7 fire 2 receipt left byte-intact in place (supersede-never-rewrite).


## R-C03 - consolidated group-safe headline + AD gate + constrained NNLS VK refit (2026-08-12)

Three deliverables across three fires (2026-08-12), consolidated in one done receipt:
`amphora-molecule-property/evidence/phase0/repairs/R-C03/done/rc03-consolidated-done-receipt.v1.dsse.json`.

| claim / KPI | refuted-by | superseded-by | date |
|---|---|---|---|
| `multi-target-ml-radonpy-4-properties-audit-kpi.v1.json` random-split headline (refractive_index R2=+0.893, thermal_conductivity R2=+0.542) | `amphora-molecule-property/evidence/audit/multitarget-macro-bisection-external-validity-w7-v1/multitarget-macro-bisection-external-validity-receipt.v1.dsse.json` | `amphora-molecule-property/evidence/phase0/repairs/R-C03/attempts/rc03-d1-group-safe-headline-superseding-kpi.v1.dsse.json` (d1) + this consolidated receipt | 2026-08-12 |
| `van-krevelen-ridge-fit-on-1000-polyuniverse-polymers-kpi.v1.json` unconstrained 24-group Ridge (2/24 sign-reversed per W8; W-PROP1 already excluded-not-refit at n_train>=125) | `amphora-molecule-property/evidence/audit/vk-ridge-ygi-admissibility-w8-v1/vk-ridge-ygi-admissibility-audit-receipt.v1.dsse.json` | `amphora-molecule-property/evidence/phase0/repairs/R-C03/attempts/rc03-d3-constrained-nnls-vk-refit.v1.dsse.json` (d3, NNLS refit, n_train>=500, 0 sign flips by construction, test MAE 21.35 K) + this consolidated receipt | 2026-08-12 |
| Tg/density predictors lacked an applicability-domain gate (C7 failing legs would silently emit predictions) | `amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final/c7_final_tg_density_external_validity_verdict_receipt.v1.json` | `amphora-molecule-property/evidence/phase0/repairs/R-C03/attempts/rc03-d2-ad-gate-tg-density-demonstration.v1.dsse.json` (d2, AD gate demonstration, >=90% abstention / >=90% coverage on all 4 legs) + this consolidated receipt | 2026-08-12 |

Original KPIs and all prior W8/W-PROP1/W7/C7 receipts left byte-intact in place (supersede-never-rewrite).


## U-DATA fire 2 - citation-provenance correction on the domain-widening search record (2026-08-12)

Scope note: ONE CITATION, INSIDE ONE SEARCH-RECORD ENTRY, IS CORRECTED. Nothing else in the fire-1
done receipt is retracted. Fire 1's entry n=3 (DDM/MDA, acquisition-queue.jsonl line 5 as originally
filed) cited its license as "Zenodo REST API record metadata.license field returned {'id':
'cc-by-4.0'}" for DOI 10.31142/ijtsrd15748. Fire 2 live-refetched that DOI and proved the citation
false: 10.31142 is the IJTSRD (International Journal of Trend in Scientific Research and Development)
DOI registrant prefix, not Zenodo's (10.5281); the DOI resolves only to ijtsrd.com, never to
zenodo.org; and the Zenodo record id apparently implied by the DOI's trailing digits (15748) is an
unrelated 2014 robotics paper ("A Modified Biogeography Based Optimization (BBO) Algorithm...")
licensed cc-zero, not cc-by-4.0. Entries n=1 (Mendeley, DETA match), n=2, n=4, n=5 (genuine
10.5281/zenodo.* DOIs) were independently re-verified live this fire and found correct -- the defect
is isolated to entry n=3, not systemic across the 17-source sweep. The TRUE source (ijtsrd.com itself)
independently confirms the SAME underlying license grant (CC BY 4.0), so the QUALIFYING_RECOMMENDED
disposition is preserved -- but for the right, source-traceable reason.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-molecule-property/evidence/phase0/repairs/U-DATA/done/u-data-domain-widening-search-record-kpi.v1.dsse.json` (sha256 `99d8fe491918c3ea073d1417c55794c416cbc0293c81968c2e16b4179284faec`) entry n=3's citation "Zenodo REST API record metadata.license field returned {'id': 'cc-by-4.0'}" for DOI 10.31142/ijtsrd15748 | self-refuted by live re-fetch this fire (`amphora-molecule-property/evidence/phase0/repairs/U-DATA/done/u-data-fire2-citation-provenance-correction-kpi.v1.dsse.json`, `checks.doi_10.31142_ijtsrd15748_resolution` + `checks.zenodo_record_15748_live_requery`: DOI resolves to ijtsrd.com not zenodo.org; live Zenodo record 15748 is an unrelated paper licensed cc-zero) | `amphora-molecule-property/evidence/phase0/repairs/U-DATA/done/u-data-fire2-citation-provenance-correction-kpi.v1.dsse.json` (U-DATA fire 2, verdict CLAIM_REFUTED for the narrower citation-provenance claim; corrected entry n=3 carries a live-refetched ijtsrd.com quote, disposition unchanged at QUALIFYING_RECOMMENDED) | 2026-08-12 |

Original fire-1 done receipt and the original acquisition-queue.jsonl line left byte-intact in place
(supersede-never-rewrite); the corrected acquisition-queue entry was appended, not edited, citing the
superseded line's sha256 (`a3af40924acd3ab2f6b8253b251437af193c0d1d28011ff99b7df0d414b3019f`).

## U-DATA fire 3 - structural-identity provenance correction on qualifying_finds[0] (2026-08-12)

Scope note: only qualifying_finds[0]'s structural-overlap FRAMING is superseded (from an
unqualified "computed via RDKit... this fire" certainty claim to an honestly-caveated
TRADE_NAME_INFERENCE_NOT_SOURCE_VERIFIED disposition). The underlying identity claim (Epikure
3223 = DETA) is NOT shown false and is not retracted -- independent corroboration (PubChem CID
8111 canonical DETA; an independent distributor's "unmodified aliphatic amine" description)
still favors it on balance. Fire 1's other 16 search_record entries, qualifying_finds[1]
(MDA/DDM), the 4 proposed_followups, the overall BLOCKED_DATA verdict, and fire 2's separate
entry n=3 citation correction are untouched.

Fire 1's qualifying_finds[0] asserted "EXACT structural identity (Tanimoto=1.0000) to the
canonical amine DETA... computed via RDKit Morgan r=2/2048-bit, this fire" for the Mendeley
10.17632/bypjxzm3fn.1 dataset's curing agent, "Epikure 3223". Fire 3 live-refetched the PRIMARY
source fire 1 had already cited for its license quote (PMC12528924) and found it describes the
curing agent, verbatim, as "a multifunctional amine resin hardener derived from
diethylenetriamine, with the commercial brand name of Epikure 3223" -- language in tension with
a bare exact-identity claim, and never read, quoted, or reconciled by fire 1 despite appearing on
the same page fire 1 already had open. Fire 1's own field name for the SMILES used
("amine_smiles_public_chemistry_not_extracted_from_paywalled_data") independently confirms no
structure was ever extracted from the source. An independent distributor page (silmid.com, live
this fire) separately describes the product as "an unmodified aliphatic amine", so the two
independent sources disagree with each other -- an ambiguity fire 1 neither investigated nor
disclosed before presenting a settled-sounding computation.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-molecule-property/evidence/phase0/repairs/U-DATA/done/u-data-domain-widening-search-record-kpi.v1.dsse.json` (sha256 `99d8fe491918c3ea073d1417c55794c416cbc0293c81968c2e16b4179284faec`) qualifying_finds[0].structural_overlap "EXACT structural identity (Tanimoto=1.0000)... computed via RDKit Morgan r=2/2048-bit, this fire" | self-refuted by live re-fetch this fire (`amphora-molecule-property/evidence/phase0/repairs/U-DATA/done/u-data-fire3-structural-identity-provenance-correction-kpi.v1.dsse.json`, `checks.primary_source_pmc12528924_live_refetch` + `checks.independent_distributor_silmid_live_refetch`: primary source calls the material "derived from diethylenetriamine"; independent distributor calls it "unmodified"; no SMILES ever extracted from either) | `amphora-molecule-property/evidence/phase0/repairs/U-DATA/done/u-data-fire3-structural-identity-provenance-correction-kpi.v1.dsse.json` (U-DATA fire 3, verdict CLAIM_REFUTED for the narrower structural-provenance claim; corrected finding carries confidence TRADE_NAME_INFERENCE_NOT_SOURCE_VERIFIED and an SDS-based resolution path, disposition unchanged at QUALIFYING_RECOMMENDED) | 2026-08-12 |

Original fire-1 done receipt and the original acquisition-queue.jsonl line 58 left byte-intact in
place (supersede-never-rewrite); the corrected acquisition-queue entry was appended, not edited,
citing line 58's sha256 (`9c32bc479c79d1f524065fa1857450003741d061c4d0e9c337a4196c49ab05bf`).


## W12 - units-correction propagation-completeness audit (2026-08-16)

Scope note: NO NUMBER IS CHANGED. This entry does not retract any RMSE/MAE/coverage-width
magnitude (a Celsius delta equals a Kelvin delta, so those are unaffected by the underlying
label defect). It retracts the UNIT-LABEL/claim-discipline completeness of 4 sibling KPIs
that share the raw Polyuniverse Epoxy 1M CSV fixture (`dataset_fixture_sha256`
`9f1f5c593463b9c26a026948901e37b4db545d17f05d5cd80baca5c3e14e0c45`) with
`polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-kpi.v1.json`, the receipt
that already discovered and disclosed (prior to this fire) that the raw "Tg" column is in
degC, not K ("CRITICAL HONEST FINDING -- units disclosure", `docs/mission.md`). That
correction was never propagated to the 4 files below: none carries the units-correction
claim_lock or a corrected-unit text pointer, and no prior RETRACTION-INDEX entry recorded the
gap. Independently re-derived from the pinned raw CSV (byte-verified against each KPI's own
`dataset_fixture_sha256` pin, full n=1,000,000 rows): read literally as Kelvin, the raw column
is thermodynamically inadmissible (1 row Tg<0K; 0/1,000,000 rows reach 300K room temperature
for a coating meant to be a rigid solid there; 80.1% read below the lowest known common-polymer
Tg floor, PDMS ~146-150K). This finding follows the same propagation-completeness attack
pattern precedent W3 (2026-08-02, dielectric-retraction propagation) established for a
different label defect in this module.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-molecule-property/evidence/phase0/kpis/polyuniverse-epoxy-tg-conformal-coverage-and-applicability-domain-kpi.v1.json` (sha256 `447f5ca832054c0e606b89eb7dfdbd38db3f3a85377c299d982122a3316221e4`) population/capability text "MD-simulated Tg (K)" / `y_stats_K` field names, uncorrected | original units-error discovery: `amphora-molecule-property/evidence/phase0/kpis/polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-kpi.v1.json` (sha256 `94fba60037e20a4763d2881d8aa3efd46298e094eedd8a67216e58a2ea9d32f9`); propagation-gap identified by `amphora-molecule-property/evidence/audit/polyuniverse-epoxy-tg-units-propagation-v1/polyuniverse-epoxy-tg-units-propagation-audit-receipt.v1.dsse.json` (W12, `CLAIM_REFUTED`) | `amphora-molecule-property/evidence/audit/polyuniverse-epoxy-tg-units-propagation-v1/polyuniverse-epoxy-tg-units-propagation-audit-receipt.v1.dsse.json` | 2026-08-16 |
| `amphora-molecule-property/evidence/phase0/kpis/polyuniverse-epoxy-tg-named-baseline-benchmark-kpi.v1.json` (sha256 `74d534f3f2f17e8cc2ec5dc91b10cfa22a9e9d78f800d02d74e1eec5f83c26e2`) "y_stats: mean 119.5 K..." uncorrected | same as above | same as above | 2026-08-16 |
| `amphora-molecule-property/evidence/phase0/kpis/polyuniverse-epoxy-tg-van-krevelen-physical-baseline-vs-ml-kpi.v1.json` (sha256 `dcc4af575760d227bc34f29a7cbbea450f1a48d484d9e93c5fdb74296a3869d5`) RMSE/R2 table labeled "K", uncorrected | same as above | same as above | 2026-08-16 |
| `amphora-molecule-property/evidence/phase0/kpis/van-krevelen-ridge-fit-on-1000-polyuniverse-polymers-kpi.v1.json` (sha256 `ba24230c8d11e414f0779daf433a5afe6e375c0d594035db1341a545409cc979`) Tg target labeled "K", uncorrected (separately, this KPI's 24-group coefficient table is already REFUTED/superseded on the unrelated sign-reversal axis by W8/W-PROP1/R-C03 -- this entry adds a second, independent defect axis) | same as above | same as above | 2026-08-16 |

Original 4 KPI files left byte-intact in place (supersede-never-rewrite); no manifest or
signed-KPI file was edited by this fire.


## W13 - hydrophobic-classification majority-baseline audit (2026-08-18)

Scope note: ONLY the binary theta>90degC hydrophobic/hydrophilic CLASSIFICATION gate and its
mission.md narrative are retracted. The KPI's regression numbers (best_LOSO_result R2=+0.0781
beating NULL by 6.0% across 66 scaffold folds; the honestly-disclosed holdout MAE underperforming
NULL) are untouched and remain accurately characterized elsewhere in mission.md as a "MIXED
FINDING". The published confusion matrix (tp=1, fp=1, fn=10, tn=26, n=38) and accuracy
(0.7105263157894737) are independently re-derived from the scientific receipt's own
`held_out_test_records` and confirmed CORRECT, not fabricated -- the defect is in the
INTERPRETATION, not the arithmetic.

`hydrophobic_classification_accuracy_at_least_0_7` (floor=0.7, PASSED at 0.711) is the only gate
in this 10-gate KPI that lacks a baseline comparison; every MAE gate in the same file carries an
explicit NULL-median comparison. On this imbalanced 38-molecule test set (27 actually not
hydrophobic, 11 actually hydrophobic), the model's accuracy is bitwise-identical to a trivial
"always predict not-hydrophobic" majority-class rule (0.7105263157894737 == 0.7105263157894737),
balanced accuracy is 0.5269 (chance=0.5000), Matthews correlation is 0.1094, and a two-sided
Fisher exact test on the prediction-vs-actual table gives p=0.5007 -- the null hypothesis that
predictions are independent of true hydrophobicity CANNOT be rejected. Recall on the positive
(hydrophobic) class is 0.091 (1 of 11 correctly flagged). A self-check confirms the same checker
correctly detects real skill on a synthetic informative classifier (same n=38, same 11/27 base
rate, tp=8/fp=3/fn=3/tn=24: accuracy 0.842 clearly exceeds baseline, Fisher p=0.0004) -- so this
is not a vacuous attack. mission.md's SCIENTIFIC INTERPRETATION point 3 ("Hydrophobic-vs-
hydrophilic classification works: 71% accuracy on held-out test is a useful screening signal...")
overstates what the held-out evidence supports.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-molecule-property/evidence/phase0/kpis/openpoly-water-contact-angle-ml-baseline-kpi.v1.json` (sha256 `974e39c709a50296cda415bf61b75efa25fff8f7f8ef5e64b363ff123bd68965`) gate `hydrophobic_classification_accuracy_at_least_0_7` PASSED (0.711>=0.7) presented without baseline comparison, and `docs/mission.md` SCIENTIFIC INTERPRETATION point 3 "Hydrophobic-vs-hydrophilic classification works... a useful screening signal" | `amphora-molecule-property/evidence/audit/water-contact-angle-classification-majority-baseline-audit-v1/water-contact-angle-classification-majority-baseline-audit-receipt.v1.dsse.json` (W13, `CLAIM_REFUTED`) | same receipt (no repair/refit performed this fire; `docs/mission.md` prose corrected in the same fire to remove the unsupported "works" framing) | 2026-08-18 |

Original KPI file and scientific receipt left byte-intact in place (supersede-never-rewrite); no
manifest or signed-KPI file was edited by this fire.


## W14 - null-baseline audit of the 5-canonical-epoxy-amines Tg external validation (2026-08-19)

Scope note: ONLY the "ML beats Van Krevelen physics" comparison and its "useful engineering Tg
prediction" framing are retracted. The applicability-domain gate (4/5 candidates correctly
flagged LOW-AD), the units-correction disclosure, and the raw per-candidate published/ML/VK
numbers are independently re-verified bit-for-bit and remain accurate and untouched.

`polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-kpi.v1.json` was the only KPI
in this module comparing ML against a physics baseline on n=5 canonical DGEBA epoxy-amine
hardeners (IPDA/m-XDA/DDS/TETA/DETA) without any structure-blind NULL comparison -- every sibling
MAE gate elsewhere in this module carries an explicit NULL-median/mean baseline. Independently
re-verified the pinned `Epoxy_1M_p.csv` (sha256
`9f1f5c593463b9c26a026948901e37b4db545d17f05d5cd80baca5c3e14e0c45`, full n=1,000,000 rows) and
reproduced the receipt's own headline numbers bit-for-bit (ML MAE=39.11947866164949 C, VK
MAE=109.07781373364219 C) before computing anything new. A trivial constant-value predictor that
always outputs the population mean Tg (118.1848 C, zero molecular/structural information) achieves
MAE=32.9630 C on the identical 5 candidates -- LOWER than the ML model's own MAE. The
population-median constant predictor (117.5982 C) achieves MAE=33.0804 C, also lower than ML. Both
pre-registered refutation criteria fired. Root cause: Van Krevelen's predictions span only 0.6 C
across 5 structurally distinct amines (a near-pure +250 C offset bug, independently documented in
`van-krevelen-tg-external-validation-15-canonical-homopolymers-kpi.v1.json`), so "ML beats VK by
70 C" mostly measures how broken VK's offset term is here, not real ML skill -- a structure-blind
constant predictor beats the ML model outright on this exact population.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-molecule-property/evidence/phase0/kpis/polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-kpi.v1.json` (sha256 `94fba60037e20a4763d2881d8aa3efd46298e094eedd8a67216e58a2ea9d32f9`) gates `ml_beats_van_krevelen_physical_baseline_on_MAE` (PASSED, +69.96C) and `ml_MAE_less_than_50C_across_5_external_candidates` (PASSED, note: "useful engineering Tg prediction"), and `docs/mission.md` "Empirical benchmark result -- external validation on 5 canonical DGEBA + industrial-amine coatings" section, presented without a null-baseline comparison | `amphora-molecule-property/evidence/audit/w14-null-baseline-5-canonical-epoxy-amines-tg-v1/w14-null-baseline-5-canonical-epoxy-amines-tg-receipt.v1.dsse.json` (W14, `CLAIM_REFUTED`) | same receipt (no repair/refit performed this fire; `docs/mission.md` prose corrected in the same fire to disclose the null-baseline finding) | 2026-08-19 |

Original KPI file and scientific receipt left byte-intact in place (supersede-never-rewrite); no
manifest or signed-KPI file was edited by this fire.
