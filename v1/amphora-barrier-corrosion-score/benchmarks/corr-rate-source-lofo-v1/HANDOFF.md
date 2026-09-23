# corr-rate-source-lofo-v1 — FALSIFICATION ATTACK (CLAIM_REFUTED)

**Date:** 2026-08-18 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**
**Module:** amphora-barrier-corrosion-score (PRE_PHASE_0, UNVALIDATED)

## What this is
A ROTATION-mode falsification attack on this module's strongest currently
standing rights-clean claim: `evidence/phase0/kpis/corr-rate-family-safe-
qspr-kpi.v1.dsse.json` (GroupKFold(group=metallurgical_family, 5-fold)
HistGBM R2=0.132087). Prior attacks varied the CV **grouping axis** (raw
material string -> metallurgical family -> true leave-one-family-out,
`corr-rate-family-lofo-v1`, SURVIVED) and the **environment axis**
(`corr-rate-marine-envelope-v1`, REFUTED) and a **feature-integrity fix**
of that co-discovered defect (`corr-rate-feature-integrity-v1`, SURVIVED).
None ever varied the **data-provenance axis**: NIST CORR-DATA is a
compilation of 220 distinct original literature sources (corrosion
handbooks, alloy-vendor bulletins, individual journal papers spanning
decades of differing testing methodology, specimen prep, and
author-specific rating-to-rate conversion). Because most sources are
family-specialized (e.g. Climax Molybdenum reports mostly molybdenum/
nickel alloys), family-safe and family-LOFO splits cannot detect a model
that has merely learned a source's own reporting convention rather than a
transferable structure-composition-environment relationship.

## The attack
True Leave-One-Source-Out: `GroupKFold(n_splits=n_sources)` with
`groups=source_text`, one of 213 sources (in the classified n=7282, 17-
family cohort) held out per fold, identical feature engineering, HistGBM
hyperparameters, and seed=0 copied verbatim from `corr-rate-family-safe-
v1`/`corr-rate-family-lofo-v1`.

## Pre-registered refutation criterion
REFUTED if EITHER (a) source-count-weighted (unweighted-per-source) mean
LOSO R2 over sources with n_test>=20 <= 0.0, OR (b) a majority (>50%) of
those eligible sources individually score LOSO R2 <= 0.0. SURVIVES if the
source-weighted mean R2 > 0 AND a majority of eligible sources
individually score R2 > 0, even if reduced relative to the family-safe/
LOFO numbers.

## Result: CLAIM_REFUTED (criterion (b))
- 83 eligible sources (n_test>=20 rows; 130 smaller sources excluded).
- Only 22/83 (26.5%) score individual LOSO R2 > 0; 61/83 (73.5%) score
  R2 <= 0 — a clear majority nonpositive, well past the 50% bar.
- `majority_of_eligible_sources_positive = false` -> criterion (b) met.
- Sample-weighted OOF R2 = 0.18711 (HIGHER than the promoted KPI's
  0.132087) — this number alone would look like a survival, but it is
  dominated by the largest sources, the same "sample-weighted hides
  sub-group failure" pattern `corr-rate-family-lofo-v1` already exposed
  one level up (at the family level); the source-weighted view is the
  pre-registered criterion and it fails clearly.

## Data-integrity note (does not change the verdict)
One eligible source (n_test=33, "Metals Handbook, Ninth Edition, Vol 13,
Corrosion, ASM International, Metals Park, OH, 1987, p 796") reports
zero within-fold label variance (`ss_tot==0`), making its own R2
mathematically undefined (NaN); the harness's `rnd()` canonicalizer
renders NaN as JSON `null`, so `source_weighted_mean_r2` is reported as
`null` rather than a NaN-poisoned numeric mean. The verdict is unaffected:
`refuted = (source_weighted_mean_r2 <= 0.0) or (not majority_positive)`,
and `NaN <= 0.0` is `False` in IEEE-754/Python, so `refuted` resolves
entirely on criterion (b), which does not depend on this source.

## Honest interpretation
Refutes the SAFE READING of the promoted family-safe KPI (and its
family-LOFO- and feature-integrity-survived nuances) as evidence the QSPR
model has learned a transferable structure-composition-environment ->
corrosion-rate relationship: for roughly three-quarters of the
independent literature sources making up NIST CORR-DATA, the model's
learned structure does not transfer to a novel source's own testing
methodology and reporting convention — even though it reliably beats the
global-mean baseline on a per-row sample-weighted basis. Does not retract
the promoted KPI's own pre-registered 5-fold gate (never about
cross-source provenance specifically) — adds a load-bearing nuance any
citation for out-of-source transfer must carry. Scope ceiling unchanged:
bare-metal/alloy substrate corrosion (NIST CORR-DATA), not organic-coating
barrier performance; no product-performance authority either way.

## Reproducibility
- stdlib+numpy+sklearn, `OMP_NUM_THREADS=1`, fixed seed=0, floats rounded
  to 6 decimals. Two runs (2026-08-16, runA/runB) -> canonical SHA-256
  `3c14d15a3e29d33f6152120cbab10d1d7b962fbb6a20fcaa619b5d931efc138d`
  (byte-identical). TWO_REPLAY_GATE=PASS. Underlying dataset
  (`feedback/v1/derived/nist_corr_reference.json`, mtime 2026-07-10)
  unchanged since these runs — no re-run needed for freshness.
- harness_sha256
  `30eea2cfcc0f5ddd5ba45291b05d5d4e30dd360881f68c5445f5cf722b070e20`.
- DSSE Ed25519 signed with trust-anchored Phase-0 evaluator key
  `phase0-evaluator-3ef6b35c...`, **AUDIT_ONLY** (promotes_authority=false,
  modifies_manifest=false; scientific_readiness stays UNVALIDATED).
  INDEPENDENT_VERIFY=PASS. envelope_sha256 `d8f5f9087b980236e081206febb8dc48e6843ffaf60c31bc9a8ca12b225b18e3`.
- No positive control required or run: refutations do not need one (the
  campaign protocol requires positive controls only to license
  CLAIM_SURVIVED); `corr_rate_source_lofo_positive_control.py`
  (hostile-null full label-shuffle) is retained alongside for a future
  repair fire to use if a repaired version of this claim is re-attacked
  and needs to license a survival.

## Files
- corr_rate_source_lofo.py — deterministic benchmark
- corr_rate_source_lofo_positive_control.py — hostile-null harness (not
  run this fire; retained for future repair re-attacks)
- result.{runA,runB}.json — two runs (byte-identical, produced 2026-08-16)
- sign_source_lofo.py — DSSE signer (AUDIT_ONLY)
- corr-rate-source-lofo-receipt.v1.dsse.json — signed receipt
