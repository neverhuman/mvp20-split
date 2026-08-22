# corr-rate-conformal-domain-shift-v1 — FALSIFICATION ATTACK (CLAIM_REFUTED)

**Date:** 2026-08-02 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**
**Module:** amphora-barrier-corrosion-score (PRE_PHASE_0, UNVALIDATED)

## What this is
A falsification attack on the strongest standing trust-anchored claim in the
module: `corr-rate-conformal-v1`'s "distribution-free marginal coverage"
result (phase0-evaluator-signed, 2026-07-29, coverage 0.9047@0.90 and
0.8103@0.80, Mondrian marine stratum 0.875, hostile-null-robust).

## The attack
Split conformal's *only* formal guarantee is exchangeability between
calibration and test residuals (Vovk-Gammerman-Shafer 2005; Lei et al 2018
JASA 113(523):1094). The prior receipt tested exactly one partition of its
held-out (non-train) rows into cal/test: a material-bucket-parity split, under
which cal and test are approximately-representative subsamples of the *same*
environment mixture — approximately exchangeable by construction. Its own
Mondrian marine-stratum check (0.875) drew cal_marine and test_marine from
that *same* material-bucket partition, so it never actually broke
exchangeability.

This attack re-partitions the **identical held-out rows** (same train
materials, same base model fit) by **environment domain** instead:
marine/chloride vs not — exactly the axis the prior receipt itself calls
"the in-scope coating context." Two directions tested:
- **Forward:** calibrate on non-marine rows (n=2773), deploy on marine rows (n=1043)
- **Reverse:** calibrate on marine rows (n=1043), deploy on non-marine rows (n=2773)

This models a realistic deployment risk for this module: intervals calibrated
on whatever corrosion data happens to be at hand, then applied specifically to
the marine anti-corrosion coating use case (or vice versa) — a genuine
covariate shift between calibration and test, not merely a resample.

## Result: CLAIM_REFUTED
- **Forward** (cal=nonmarine, test=marine): 0.90-target coverage = 0.9223
  (PASS, p=0.994 one-sided binomial); 0.80-target coverage = 0.7862 (misses
  nominally but p=0.141, not significant).
- **Reverse** (cal=marine, test=nonmarine): 0.90-target coverage = **0.8763**,
  **one-sided exact binomial p = 3.1×10⁻⁵ — significantly below the 0.90
  target** (n=2773, n_covered=2430). 0.80-target coverage = 0.8078 (PASS).
- `any_direction_significantly_undercovers_at_0.05 = true`.

The receipt's "distribution-free marginal coverage... delivers... at the 0.90
and 0.80 targets" framing, read as a robustness property surviving any
reasonable group-safe partition (which is how the hostile-null section frames
it — "the guarantee needs only exchangeability, not base-learner skill"),
does **not** survive a partition that breaks exchangeability via environment
domain shift. Calibrating on marine/chloride data and deploying on the
broader (non-marine) environment population significantly undercovers.

## What this does NOT show
- Does not show the *original* corr-rate-conformal-v1 receipt's own reported
  numbers (0.9047@0.90, 0.8103@0.80, computed on ITS OWN material-bucket
  partition) are wrong — those are correctly computed for that specific split.
- Does not establish a coating-barrier ranking model; scope ceiling unchanged
  (bare-metal/alloy substrate corrosion only).
- Does not modify the manifest (66/11 untouched) or flip scientific_readiness.

## Practical implication (for future work on this module)
Any downstream use of corr-rate-conformal-v1's intervals must recalibrate
on data drawn from the SAME environment distribution as the deployment target
(e.g., marine-only calibration for marine deployment), or use covariate-shift
weighted conformal (Tibshirani et al 2019) — a plain material-safe split is
**not sufficient** to guarantee coverage transfers across environment domains.

## Reproducibility
- OMP_NUM_THREADS=1, fixed seed, no timestamp, floats round(.,6), stdlib-only
  exact log-space binomial test (no scipy dependency in the signed artifact).
  Two runs → canonical SHA-256
  `3ec7fd5e632909b14f8f70c8e27bad5241d7b10193164047d808c034b053fa0f`
  (byte-identical). **TWO_REPLAY_GATE=PASS.**
  harness_sha256 `382dd05855890a3105d0cc085d2b7f8dc0a088cf9e0a29123fb185aef205ae14`.
- DSSE Ed25519 signed with trust-anchored Phase-0 evaluator key
  `phase0-evaluator-3ef6b35c...`, **AUDIT_ONLY** (promotes_authority=false,
  modifies_manifest=false; scientific_readiness stays UNVALIDATED; manifest
  66/11 untouched). eval + reviewer key ids both derive the pinned trust
  store. envelope_sha256 `6cfa98626ac5f9e3dce9f2a1011a4d46ab6542c642d11492d787cc1d9366c3fb`.

## Files
- `domain_shift_conformal.py` — deterministic falsification benchmark
- `result.{runA,runB,canonical}.json` — two runs + canonical
- `sign_domain_shift.py` — DSSE signer (AUDIT_ONLY)
- `corr-rate-conformal-domain-shift-receipt.v1.dsse.json` — signed receipt
