# Retraction / Supersession Index — amphora-tolerance-robustness

Created 2026-08-03 (operator, closing the R-A00 canary finding: this module had 2
REFUTED ledger verdicts and no index).

Amended 2026-08-05 (W-TOL1, closing the portfolio-wide V1-RESOLVE sweep's two
NOT_RESOLVED findings against this index: a literal `PENDING` token with no
referent on the OpenPoly Tg row, and a superseded-by cell on the RadonPy row
that named a real, DSSE-verified receipt covering a different, narrower claim
(label admissibility) than the one this row is attached to (conformal
coverage). Both rows are rewritten below to state plainly that no repair has
landed and to name the campaign item (R-C01) that owns the gap, per
V1-RESOLVE's own resolution rule: an honest "no repair yet, queued as R-C01"
is a resolved row; a bare PENDING or a mismatched referent is not. See
amphora-tolerance-robustness/evidence/phase0/repairs/W-TOL1/done/ for the
signed repair receipt.)

Amended 2026-08-11 (R-C01 fire 2/5, DONE): the OpenPoly Tg row's scaffold-safe
coverage gap is repaired. A training-conditional PAC-corrected split-conformal
rank (Vovk 2012), reusing eps=0.05/delta=0.05 verbatim from this module's own
already-signed training-conditional-pac-tolerance-openpoly-tg-v1 receipt, was
re-run against the IDENTICAL pinned 60-seed scaffold-disjoint Monte Carlo
protocol (same script sha256 96be585e27428a1f9bec0a7e2c078f9488711df5515790bc24ac35ac97cf0e09,
same seeds 0-59) and raised mean scaffold-safe coverage from the refuted 0.8746
to 0.9073, clearing this item's pre-registered 0.90 acceptance bar. Two prior
approaches were tried and rejected this same fire before the accepted one:
Mondrian conformal stratified by a fixed Butina scaffold-cluster taxonomy
degenerated to the unrepaired baseline (0.8746 unchanged -- the corpus's 64
unique scaffolds are too imbalanced, with 2 scaffolds covering 73.6% of the
443-molecule corpus, for any cluster to clear a non-outcome-tuned minimum-size
fallback floor), and a naive PAC eps=0.10 (matching the acceptance floor
directly rather than reusing an existing derivation) scored worse than
baseline (0.8364) and was discarded. See
amphora-tolerance-robustness/evidence/phase0/repairs/R-C01/done/ for the
signed repair receipt and its full per-seed table; per-seed worst-case
coverage remains unguaranteed (18/60 seeds still individually below 0.90,
driven by the same two dominant scaffolds) -- only the pre-registered MEAN
criterion is closed.

Amended 2026-08-15 (rotation fire, AUDIT_ONLY): re-applied this module's own
bootstrap-CI + fraction-below-floor methodology (the same apparatus that
refuted the original 0.9683 claim on 2026-08-03) to the R-C01 repair's
accepted 60-seed evidence itself. The repair's mean point estimate (0.9073)
is arithmetically >= 0.90, but a 95% bootstrap CI on that same evidence is
[0.8811, 0.9303] and 27.6% of resamples fall below 0.90 -- the "pass" is not
statistically robust. See the new bullet under the OpenPoly Tg row below and
evidence/audit/r-c01-mean-robustness-bootstrap-v1/ for the signed receipt.
This amendment does not modify, retract, or delete the R-C01 done receipt.

Amended 2026-08-16 (rotation fire, AUDIT_ONLY): extended the pinned N=60
scaffold-disjoint Monte Carlo protocol -- previously applied only to the
Ridge-base split-conformal claim -- to its never-before-scaffold-tested
sibling, split-conformal-on-rf-ml-openpoly-tg-kpi.v1.json (RandomForestRegressor
base predictor, Morgan512+log10MW features, empirical_coverage_95_pi 0.9663 on
a single random seed=0 split). Same corpus (openpoly Tg, sha256
8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3), same F1/F2/F3
pre-registered criteria, same 0.90 floor / 0.25 breach threshold. Result: mean
scaffold-safe coverage collapses to 0.8621 (worse than the Ridge case's 0.8746),
min single-draw coverage 0.4693, 33/60 draws (55%) breach the 0.90 floor, 95%
bootstrap CI [0.8330, 0.8888] excludes 0.95. All three falsification criteria
fire (F1 Wilcoxon p=1.03e-9, F2 0.55>0.25, F3 CI excludes nominal). See the new
row below and evidence/audit/rf-ml-scaffold-monte-carlo-conformal-openpoly-tg-v1/
for the signed receipt. Does not modify or delete the RF-ML KPI file itself.

## OpenPoly Tg split-conformal coverage 0.9683 (split-conformal-prediction-openpoly-tg-kpi.v1.json)
- refuted-by: evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/repeated-scaffold-monte-carlo-conformal-openpoly-tg-receipt.v1.dsse.json (2026-08-03; mean scaffold-safe coverage 0.8746 over 60 draws, CI [0.8497,0.8974] excludes 0.95; also takes down the jackknife+/CV+, Mondrian, normalized-adaptive and training-conditional-PAC cousins as robustness evidence)
- superseded-by: amphora-tolerance-robustness/evidence/phase0/repairs/R-C01/done/r-c01-pac-corrected-scaffold-repair-done-receipt.v1.dsse.json (2026-08-11, R-C01 fire 2/5; PAC-corrected scaffold-safe mean coverage 0.9073 >= 0.90 acceptance bar, over the SAME 60-seed protocol as the refuting receipt above). The random-split 0.9683 marginal coverage number in split-conformal-prediction-openpoly-tg-kpi.v1.json is untouched and still stands for exchangeable (random) splits; this supersession concerns scaffold-disjoint (deployment-shift) coverage only, and only the MEAN across 60 draws -- 18/60 individual seeds still fall below the 0.90 floor (see the done receipt's per-seed table).
- **robustness-refuted-by** (2026-08-15): evidence/audit/r-c01-mean-robustness-bootstrap-v1/r-c01-mean-robustness-bootstrap-audit-receipt.v1.dsse.json. Applied the identical bootstrap-CI + fraction-below-floor apparatus this module used to refute the original 0.9683 claim to the R-C01 repair's OWN accepted 60-seed evidence (no re-simulation, values read verbatim from the done receipt's per_seed_table): 95% bootstrap percentile CI on the mean is [0.8811, 0.9303] -- it does NOT exclude sub-0.90 values -- and 27.6% of 100,000 bootstrap resamples of that identical evidence fall below the 0.90 acceptance floor. Does not overturn the literal point-estimate inequality (0.9073 >= 0.90 remains arithmetically true) or delete/supersede the R-C01 done receipt; establishes instead that the MEAN-clears-bar acceptance, as currently evidenced, is not statistically distinguishable from a fail. R-C01 should be read as repair_status "in_progress" pending either a CI-aware acceptance criterion or more scaffolds/seeds to narrow the interval.

Amended 2026-08-18 (rotation fire, AUDIT_ONLY): extended the pinned N=60
scaffold-disjoint Monte Carlo protocol to the third and last never-before-
scaffold-tested split-conformal sibling, conformalized-quantile-regression-
openpoly-tg-kpi.v1.json (CQR, two GradientBoostingRegressor quantile models
alpha=0.025/0.975, Morgan512+log10MW features, empirical_coverage_95_pi
1.0000 on a single random seed=0 60/20/20 split). Same corpus (openpoly Tg,
sha256 8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3),
same F1/F2/F3 pre-registered criteria, same 0.90 floor / 0.25 breach
threshold, same 60/40 scaffold-disjoint test-fraction logic as the Ridge and
RF-ML attacks. Result: mean scaffold-safe coverage collapses to 0.8842 (from
random-split coverage_random_mean 0.9676), min single-draw coverage 0.5495,
27/60 draws (45%) breach the 0.90 floor, 95% bootstrap CI [0.8596, 0.9065]
excludes 0.95. All three falsification criteria fire (F1 Wilcoxon
p=7.85e-9, F2 0.45>0.25, F3 CI excludes nominal). Two-replay byte-stability
gate PASS (script sha256 recorded in the receipt's provenance block). See
the new row below and
evidence/audit/cqr-scaffold-monte-carlo-conformal-openpoly-tg-v1/ for the
signed receipt. Does not modify or delete the CQR KPI file itself. All
three split-conformal base-predictor siblings sharing this corpus (Ridge,
RF-ML, CQR) are now scaffold-tested and refuted.

## OpenPoly Tg RF-ML split-conformal coverage 0.9663 (split-conformal-on-rf-ml-openpoly-tg-kpi.v1.json)
- refuted-by (2026-08-16): evidence/audit/rf-ml-scaffold-monte-carlo-conformal-openpoly-tg-v1/rf-ml-scaffold-monte-carlo-conformal-openpoly-tg-receipt.v1.dsse.json. Pinned N=60 scaffold-disjoint Monte Carlo protocol (same protocol as the Ridge-base row above) applied to the RF-ML base predictor: mean scaffold-safe coverage 0.8621 (vs the KPI's random-split 0.9663), 95% bootstrap CI [0.8330,0.8888] excludes 0.95 nominal, 33/60 draws (55%) below the 0.90 floor, min single-draw coverage 0.4693. All three pre-registered falsification tests (F1 paired Wilcoxon p=1.03e-9, F2 fraction-below-floor 0.55>0.25, F3 bootstrap-CI-excludes-nominal) fire. The random-split 0.9663 marginal coverage number in split-conformal-on-rf-ml-openpoly-tg-kpi.v1.json is untouched and still stands for exchangeable (random) splits; this concerns scaffold-disjoint (deployment-shift) coverage only. The claimed advantage over the Ridge-base conformal wrapper (tighter PI width, "base-predictor-agnostic" coverage) does not extend to scaffold shift -- the RF-ML wrapper collapses at least as badly as its Ridge sibling.
- superseded-by: NONE YET. Unrepaired.

## OpenPoly Tg CQR split-conformal coverage 1.0000 (conformalized-quantile-regression-openpoly-tg-kpi.v1.json)
- refuted-by (2026-08-18): evidence/audit/cqr-scaffold-monte-carlo-conformal-openpoly-tg-v1/cqr-scaffold-monte-carlo-conformal-openpoly-tg-receipt.v1.dsse.json. Pinned N=60 scaffold-disjoint Monte Carlo protocol (same protocol as the Ridge-base and RF-ML rows above) applied to the CQR base predictor (two GradientBoostingRegressor quantile models, alpha=0.025/0.975): mean scaffold-safe coverage 0.8842 (vs the KPI's random-split empirical_coverage_95_pi 1.0000 / this attack's own random-split mean 0.9676), 95% bootstrap CI [0.8596,0.9065] excludes 0.95 nominal, 27/60 draws (45%) below the 0.90 floor, min single-draw coverage 0.5495. All three pre-registered falsification tests (F1 paired Wilcoxon p=7.85e-9, F2 fraction-below-floor 0.45>0.25, F3 bootstrap-CI-excludes-nominal) fire. The random-split 1.0000 marginal coverage number in conformalized-quantile-regression-openpoly-tg-kpi.v1.json is untouched and still stands for exchangeable (random) splits; this concerns scaffold-disjoint (deployment-shift) coverage only. CQR's over-coverage under random splits does not translate into robustness under scaffold shift -- adaptivity (input-dependent PI width) does not confer scaffold-shift robustness any more than the fixed-width Ridge or RF-ML wrappers did.
- superseded-by: NONE YET. Unrepaired.

## RadonPy eps_r conformal coverage (mixed-openpoly-radonpy-dielectric-conformal-kpi.v1.json, coverage claim)
- refuted-by: evidence/audit/conformal-coverage-attack-v1/conformal-coverage-attack-receipt.v1.dsse.json (2026-08-02, W5; admissible-subset coverage 0.6923, Wilson CI [0.5573,0.8009] excludes 0.95 — apparent 0.9558 propped up by 89.5% physically-inadmissible labels)
- superseded-by: NONE YET for this claim's own conformal COVERAGE number (0.9558). The amphora-molecule-property dielectric retraction chain (evidence/audit/dielectric-retraction-v1/, logs/claims-requiring-retraction.jsonl) exists and DSSE-verifies, but refutes LABEL ADMISSIBILITY of RadonPy data, not this row's coverage number -- does not resolve this row. No receipt anywhere republishes a corrected admissibility-stratified coverage figure. Tracked as open item R-C01 (admissibility-stratified coverage recomputation); until it lands, 0.9558 stays refuted and unrepaired (W-TOL1, 2026-08-05).

## Note
The mechanical conformal guarantee under exchangeability (random splits) is intact;
what fell is coverage under scaffold/deployment shift. The bootstrap-PI honest
negative (0.2511 vs 0.95 nominal) was self-reported by this module and stands.
