# st19168-preregistered-v1 — pre-registered, frozen analysis plan for the ST-19168 unlock

**Date:** 2026-07-31 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**
**Module:** amphora-barrier-corrosion-score (PRE_PHASE_0, UNVALIDATED) · **Campaign item:** C3

## What this is

A pre-registered, hash-locked analysis plan for the day USBR clears rights on ST-19168
(campaign item C2, filed today). Per the campaign brief: (1) hypotheses pinned to
mission.md's locked KPI, (2) an exact statistical plan with honest achievable power at
n=10, (3) working analysis code tested end-to-end on synthetic shadow data (same shape,
pinned seeds, zero real-data content), (4) a hash-locked commitment to the frozen script
so any post-unlock run can be verified byte-for-byte against this pre-registration.

Full plan: see `PREREGISTRATION.md`. Frozen script: `analyze_st19168_preregistered.py`.

## The headline honest finding

The closed-form Bonett & Wright (2000) approximation says n=10 gives the PRIMARY test
(tau(locked,truth)>=0.5, significant) only ~41% power. A K=15-replicate Monte Carlo
calibration against synthetic data with the true population tau embedded at exactly the
locked target (0.50) empirically measured:

- **Primary gate (H1a) empirical power: 46.7%** (Clopper-Pearson 95% CI [21.3%, 73.4%])
  — closely matches the 41% closed-form number.
- **Full compound gate (H1a AND H1b AND H1c) empirical power: 0/15 = 0%** (95% CI
  [0%, 21.8%]) — in this calibration, NOT ONE of the 15 replicates where the true signal
  was exactly at the locked target reached the full LOCKED_KPI_SUPPORTED_ALL_GATES_PASS
  verdict. Even when H1a passed (7/15 draws), the solids-only superiority gate (H1b)
  failed in 6 of those 7 (the one time it passed, the pvc-only gate H1c then failed).

This is the single most important number in this package: **at n=10, the module's
locked KPI as currently written (a three-part AND across primary significance +
two dependent-correlation superiority tests) is very unlikely to be confirmable even
in the best realistic case where the true effect exactly equals the target.** This is
disclosed now, before any real ST-19168 number exists, specifically so a future
NOT_SUPPORTED result on the real 10-system unlock is not mistaken for evidence against
the underlying scientific hypothesis — see `PREREGISTRATION.md`'s honest power section
for the full interpretation guidance.

Type-I error control was separately verified: across 15 independent NULL draws (no true
signal), 0/15 falsely triggered the primary gate (95% CI [0%, 21.8%], consistent with
the nominal alpha=0.05 — not inflated).

## Package contents

- `PREREGISTRATION.md` — the frozen, human-readable analysis plan (hypotheses,
  estimator, exact-permutation test, fixed-sequence gatekeeping rationale, honest power
  section, hash-lock commitment language).
- `analyze_st19168_preregistered.py` — **the frozen, hash-locked analysis script.**
  Single vectorized `batch_tau_b` primitive used for the point estimate, the primary
  exact/MC permutation test, AND both superiority tests' bootstrap/permutation checks,
  so ties are handled identically everywhere. scipy's exact-method p-value is
  cross-checked against an independent from-scratch full-enumeration implementation on
  every run (`cross_check_agreement` field) — the two agreed exactly on both shadow runs.
- `generate_shadow_data.py` — synthetic shadow-data generator (pinned seeds 190168001 /
  190168002), rank-mixing copula calibrated offline to hit population tau~0.50 in the
  ALT arm. Contains no information derived from the real ST-19168 file (see
  `QUARANTINE-INTEGRITY-FLAG.md` for why that separation was deliberately maintained).
- `shadow_null.json`, `shadow_alt.json` — the two pinned-seed synthetic datasets (n=10
  each, matching the real unlock's expected shape: EIS |Z|, rust-creep, solids %, PVC %).
- `result_null.{runA,runB,canonical}.json`, `result_alt.{runA,runB,canonical}.json` —
  frozen-script output, two-replay byte-identical in both arms.
- `calibration_repeated_draws.py`, `calibration_result.canonical.json` — K=15-replicate
  Type-I-error and empirical-power calibration (imports and calls the frozen script's
  `run()` directly, no re-implementation).
- `sign_preregistration.py`, `preregistration-receipt.v1.dsse.json` — DSSE Ed25519
  AUDIT_ONLY signature binding the frozen script SHA-256 + all shadow/calibration results.
- `QUARANTINE-INTEGRITY-FLAG.md` — a SEPARATE finding surfaced while doing this work:
  an already-committed, already-signed file
  (`reference/eis/st-19168/st19168_eis_rust_creep_correlation_receipt.v1.json`, dated
  2026-07-22) appears to contain real extracted ST-19168 numbers (via `openpyxl`),
  contradicting the "untouched" status asserted by mission.md, capability-profile.json,
  and today's C2 rights-review-request receipt. This cron did not open the quarantined
  xlsx itself, did not use any number from that flagged file in this package's synthetic
  shadow data, and did not modify or supersede the flagged file — it is left for human
  review. See that file for full detail.

## Reproducibility

- Frozen script is deterministic given a fixed input file (fixed seeds throughout: no
  wall-clock entropy). `result_null` and `result_alt` are byte-identical across two
  independent runs (TWO_REPLAY_GATE=PASS both arms).
- DSSE Ed25519 signed with the Phase-0 evaluator key, **AUDIT_ONLY**
  (promotes_authority=false, modifies_manifest=false; scientific_readiness stays
  UNVALIDATED). eval + reviewer key ids checked against the pinned trust store.

## What this does NOT do

- Does not open, parse, or derive from the quarantined ST-19168 xlsx.
- Does not promote module authority, phase, or manifest state.
- Does not itself constitute the mission.md locked primary KPI (the blinded four-track
  independent-panel comparison) — it is a smaller, ST-19168-specific corroborating
  rehearsal, to be executed unmodified (hash-checked) the day rights clear.
