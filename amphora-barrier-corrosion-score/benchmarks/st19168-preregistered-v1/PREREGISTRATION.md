# st19168-preregistered-v1 — pre-registered, frozen analysis plan for the ST-19168 unlock

**Module:** amphora-barrier-corrosion-score · **Authority:** AUDIT_ONLY · **Status:** FROZEN, PRE-DATA
**Campaign item:** C3 · **Prepared:** 2026-07-31 (automated cron)

## Why this exists

`amphora-barrier-corrosion-score`'s locked KPI (`docs/mission.md`, "KPI register and
promotion gates") is:

> Primary KPI: blinded Kendall tau at `metrics.barrier_index`. Locked target: Blinded
> four-track independent-panel comparison with Kendall tau >= 0.5 and superiority over
> solids-only and PVC-only hostile nulls.

ST-19168 (`reference/eis/st-19168/raw/19168_inhibitive_coating_system_data.xlsx`, USBR
RISE catalog 4640/item 11562) is a 10-coating-system EIS |Z| + rust-creep dataset,
rights-quarantined pending human review (`evidence/audit/st-19168-rights-review-v1/`,
campaign item C2, filed 2026-07-31). It is the closest on-disk candidate to a real,
independently-measured, in-class corroborating check of the locked KPI's structure —
NOT a substitute for the full blinded four-track panel study, which remains the actual
Phase-1 gate, but a smaller, honestly-scoped rehearsal of the same statistical question
on real measured endpoints (EIS |Z| and rust creep) instead of blinded panel scores.

**The entire point of pre-registering now, before rights are cleared:** once the human
flips ST-19168 to `eligible_for_derivatives: true`, the analysis must be provably the
SAME analysis that would have been run on any other 10-system draw — not one tuned after
seeing which systems look good. This document plus the hash-locked script
(`analyze_st19168_preregistered.py`, SHA-256 recorded in the signed receipt) is that
commitment device (Wagenmakers et al. 2012, "An Agenda for Purely Confirmatory
Research", Perspect. Psychol. Sci. 7(6):632-638, on the logic of pre-registration).

## Hypotheses (pinned to the locked KPI)

Population: the ST-19168 coating systems that, after unlock, have BOTH an EIS |Z| at
0.01 Hz endpoint and a rust-creep endpoint recorded (target n=10; the frozen script
accepts and honestly reports on whatever complete-case n materializes; n<6 fails closed
with no inference, since below that floor exact/asymptotic rank tests are not
meaningful).

- **Truth (primary):** `rust_creep_mm`, lower = better barrier. Truth score used in all
  tau computations is `-rust_creep_mm` so "higher truth score = better barrier",
  matching the sign convention of `locked_barrier_index`.
- **Truth (secondary, corroborating only, not gated):** `eis_log10_z_ohm_0p01hz`,
  higher = better barrier (Amirudin & Thierry 1995, Prog. Org. Coat. 26:1-28 convention
  used elsewhere in this module).
- **Predictor "locked":** `metrics.barrier_index` from a live `rtk cargo test` /
  candidate-contract run of `amphora-barrier-corrosion-score/src/lib.rs` against each
  system's declared formulation (input formulation fields, NOT the truth endpoints).
- **Predictor "solids-only null":** total solids volume %, the SAME hostile null
  already locked in `benchmarks/barrier-null-char-v1` — not a new null invented for
  this analysis.
- **Predictor "PVC-only null":** pigment volume concentration %, same provenance.

**H1a (primary):** `tau_b(locked, truth) > 0` (one-sided) AND `tau_b(locked, truth) >=
0.50`. This is a compound criterion — statistical significance is necessary but not
sufficient; the locked target is a magnitude floor, not just "detectably nonzero".

**H1b (superiority #1):** `tau_b(locked, truth) > tau_b(solids-only, truth)`, one-sided,
evaluated ONLY if H1a passes (fixed-sequence gatekeeping, see below).

**H1c (superiority #2):** `tau_b(locked, truth) > tau_b(pvc-only, truth)`, one-sided,
evaluated ONLY if H1b passes.

The module's locked target is the conjunction H1a AND H1b AND H1c. This mirrors the
mission.md phrasing ("tau >= 0.5 **and** superiority over solids-only **and** PVC-only
hostile nulls") exactly — no hypothesis is added or removed here.

## Statistical plan

| Element | Choice | Reference |
|---|---|---|
| Estimator | Kendall's tau-b (tie-robust) | Kendall 1938, Biometrika 30(1/2):81-93 |
| Primary test | One-sided exact permutation test of tau_b(locked,truth)>0 | Kendall & Gibbons 1990, ISBN 0-19-520837-4 |
| Primary cross-check | Independent from-scratch full-enumeration permutation (same estimator, separately coded) | non-circularity requirement below |
| Superiority test | Paired bootstrap of the SAME n systems, B=100,000, one-sided p = P(delta<=0) | Efron & Tibshirani 1993, ISBN 0-412-04231-2 |
| Superiority cross-check | Permutation test under the stricter null "truth independent of BOTH predictors" | secondary robustness only |
| Multiple-comparison handling | Fixed-sequence / hierarchical gatekeeping (H1a -> H1b -> H1c, each only tested if predecessor passes) | Maurer, Hothorn & Lehmacher 1995, Biom. J. 37:829; Bauer, Roehmel, Maurer & Hothorn 1998, Stat. Med. 17:2133 |
| alpha | 0.05, one-sided, at every step (controlled at the family level by gatekeeping, not per-step Bonferroni) | — |
| n | target 10; floor 6 (fail-closed below) | — |
| Sample-size / power reference formula | Bonett & Wright 2000, Psychometrika 65(1):23-28, DOI:10.1007/BF02294183 (same formula already used in `amphora-public-corrosion-benchmark/evidence/audit/eis-reproducibility-discrimination-power-v1/`) | — |

**Why fixed-sequence gatekeeping and not Bonferroni:** the locked KPI is written as a
conjunction (AND), not as three independent claims. A fixed-sequence procedure that
only spends alpha on H1b once H1a has already been confirmed, and only spends alpha on
H1c once H1b has already been confirmed, controls the family-wise Type-I error at
alpha=0.05 exactly — with NO power penalty relative to testing H1a alone. A blanket
Bonferroni correction (alpha/3 = 0.0167 per test) would be the wrong tool here: it
protects against testing three INDEPENDENT hypotheses and would spend power the
locked KPI's own AND-structure doesn't require us to spend. This is a genuine
methodological choice made BEFORE data, not a post-hoc power grab — it is recorded
here specifically so it cannot be second-guessed after real numbers are seen.

**Non-circularity:** the primary test is computed two independently-coded ways (scipy's
built-in exact method vs. a from-scratch full-enumeration permutation implemented in
`analyze_st19168_preregistered.py`'s `batch_tau_b` + `exact_or_mc_permutation_pvalue`)
and BOTH must be run and reported; if they materially disagree
(`cross_check_agreement=false` in the output), the receipt must say so and the result is
not trusted. Superiority tests are similarly double-checked (bootstrap + independent
permutation-based robustness statistic).

## Honest achievable power at n=10 (pre-registered, not discovered after data)

Using the Bonett & Wright (2000) Fisher-z sample-size approximation for a one-sided rank
correlation test at alpha=0.05:

```
n_required(r, power=0.80) = 3 + 1.06 * ((z_{1-alpha} + z_{power}) / atanh(r))^2
```

At the locked target `r = tau = 0.50`, one-sided alpha=0.05 (`z=1.645`), 80% power
(`z=0.8416`): **n_required ≈ 25 systems.** ST-19168 offers at most **10** — well below
this. Inverting the formula for n=10 gives an **asymptotic-approximation achieved power
of ≈ 41%** for the PRIMARY test alone (H1a) — i.e. even if the true population tau
between the locked ranking and rust-creep truth is exactly 0.50, a one-shot n=10 exact
test has a meaningfully-better-than-coin-flip but still well-under-80% chance of
reaching significance. This is honestly disclosed here BEFORE any real data is seen, and
is directly analogous to the `amphora-public-corrosion-benchmark`
`eis-reproducibility-discrimination-power-v1` finding that the cross-modality EIS<->
rust-creep rank needed ~90 systems at the observed effect size (sigma_R=1.026 decades,
r~0.30) — small-n underpowering is a recurring, honestly-disclosed structural property
of this portfolio's corrosion benchmarks, not unique to ST-19168.

The two SECONDARY superiority tests (H1b, H1c) compare two DEPENDENT rank-correlation
estimates computed on the same n=10 systems — they are structurally lower-powered still
than the primary test, because the quantity being estimated (a difference of two noisy
correlations) has larger sampling variance than either correlation alone. No published
closed-form n-for-power formula for dependent-tau differences at small n was located in
scope for this pre-registration; the empirical calibration below (repeated synthetic
draws, `calibration_result.canonical.json`) is offered instead as the honest,
simulation-grounded substitute, and the finding is reported exactly as observed —
including any instance in the calibration run where H1a passed but H1b or H1c did not,
which is expected and does not indicate a broken pipeline.

**Bottom line, stated plainly:** even if the real ST-19168 unlock delivers a barrier
ranking that is, in reality, exactly as good as the locked KPI's target (population
tau=0.50), a single n=10 pre-registered analysis has a meaningfully-less-than-even
chance of producing a full LOCKED_KPI_SUPPORTED_ALL_GATES_PASS verdict, and a materially
worse chance still of clearing both secondary superiority gates. A NOT_SUPPORTED result
on the real data would NOT by itself refute the locked KPI at the population level — it
would need to be interpreted through this pre-registered power statement, not treated as
a surprise. Conversely, if it clears all three gates despite this power ceiling, that IS
meaningful evidence, precisely because the bar was hard to clear by chance.

## Frozen script hash-lock commitment

The signed receipt for this pre-registration records `SHA256(analyze_st19168_preregistered.py)`
as it exists at signing time, BEFORE ST-19168 rights are cleared and before the script is
ever run against the real unlocked extraction. Any future execution against real data
MUST either (a) use a byte-identical copy of this file (verified by re-hashing before
the run), or (b) be disclosed as a POST-HOC AMENDMENT with an explicit diff against the
frozen version and a stated reason — matching the standard pre-registration deviation-
disclosure norm (Nosek, Ebersole, DeHaven & Mellor 2018, PNAS 115(11):2600-2606).

## What this pre-registration does NOT do

- It does not open, parse, or derive from the quarantined ST-19168 xlsx. All testing in
  this package uses synthetic shadow data with the same shape (10 systems x EIS |Z| +
  rust-creep + solids/PVC covariates), generated with pinned seeds, containing no
  information from the real file.
- It does not promote module authority, phase, or manifest state.
- It does not itself constitute the mission.md-locked primary KPI (the blinded
  four-track independent-panel comparison) — it is a smaller, honestly-scoped,
  ST-19168-specific corroborating rehearsal of the same statistical question, to be run
  the day rights clear.
- It does not assume the outcome. Both a supportive and a non-supportive real-data
  result are pre-specified as valid, interpretable outcomes above.

## Files in this package

- `PREREGISTRATION.md` — this document.
- `analyze_st19168_preregistered.py` — **the frozen, hash-locked analysis script.**
- `generate_shadow_data.py` — synthetic shadow-data generator (pinned seeds), used only
  for pre-unlock testing; NOT used on real data.
- `shadow_null.json`, `shadow_alt.json` — the two pinned-seed shadow datasets.
- `result_null.canonical.json`, `result_alt.canonical.json` (+ `.runA`/`.runB` copies) —
  frozen-script output on each shadow dataset, with two-replay byte-stability.
- `calibration_repeated_draws.py`, `calibration_result.canonical.json` — K-replicate
  Type-I-error and empirical-power calibration (see above).
- `sign_preregistration.py`, `preregistration-receipt.v1.dsse.json` — DSSE Ed25519
  AUDIT_ONLY signature binding the frozen script hash + all shadow-data/calibration
  results.
