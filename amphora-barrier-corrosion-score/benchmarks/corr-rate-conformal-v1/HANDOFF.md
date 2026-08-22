# corr-rate-conformal-v1 — group-safe calibrated intervals (split + Mondrian conformal)

**Date:** 2026-07-29 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**
**Module:** amphora-barrier-corrosion-score (PRE_PHASE_0, UNVALIDATED)

## What this is
The **first calibrated-interval receipt for the module on a RIGHTS-CLEAN dataset**.
Extends the point-estimate `corr-rate-qspr-v1` (HistGBM, cluster-bootstrap RMSE CI)
with distribution-free **per-prediction** calibrated intervals over NIST CORR-DATA
(rights_class `DERIVATIVE_ALLOWED`, "NIST public data"). Same features + HistGBM
config as corr-rate-qspr-v1. The only prior conformal work in the module was on the
**Polyverse diffusivity** data, which is `CONTEXT_ONLY` / rights-quarantined and is
**not scored** — this replaces it with a rights-clean equivalent.

## Methods (published)
- **Split (inductive) conformal** — Papadopoulos-Proedrou-Vovk-Gammerman 2002;
  Vovk-Gammerman-Shafer 2005; Lei et al 2018 JASA 113(523):1094.
- **Normalized / locally-adaptive** — Papadopoulos-Gammerman-Vovk 2008; Lei 2018 §5,
  score = |y−μ(x)|/σ(x) with a σ-model on train residuals.
- **Mondrian (category-conditional)** — Vovk et al 2003; Boström-Johansson 2021,
  Mach. Learn. 110:489.
- **GROUP-safe exchangeability**: train/cal/test partitioned by **MATERIAL**
  (leave-material-out; 366/123/123 alloys, pairwise-disjoint). corr-rate-qspr-v1
  showed random CV overstates skill by ΔR²≈0.145, so material-safe is the honest split.

## Headline (honest)
- Base μ-model group-safe single-split **test R²=0.258** (weak, as expected).
- **Fixed split conformal**: coverage **0.9047 @ target 0.90**; **0.8103 @ 0.80** — both PASS.
- **Normalized conformal @0.90**: coverage 0.9613, mean width 1.415× the fixed interval
  (adaptive but conservative here).
- **Mondrian marine/chloride**: marine stratum coverage **0.875** (below the 0.90 marginal,
  above the 0.80 soft floor) — an honest finding that the in-scope marine stratum
  slightly under-covers, motivating stratified intervals; "other" 0.911; worst 0.875 ≥ 0.80.
- **Mondrian magnitude tercile**: worst 0.900 (low 0.900 / mid 0.951 / high 0.915).
- **Hostile null (shuffled labels)**: broken learner R²=−0.06 yet coverage **0.9047 ≥ 0.90**
  while interval width **inflates 1.095×** — the red-team defence that the coverage
  guarantee needs only exchangeability, not base-learner skill.
- **All fail-closed checks PASS** (3× group-disjointness, 2× fixed-coverage targets,
  null coverage-holds, null width-inflates).

## Scope ceiling (held — same as corr-rate-qspr-v1)
Target is **bare metal/alloy SUBSTRATE** corrosion rate, **NOT** organic epoxy-amine
**COATING-barrier** performance. This is a calibrated *environmental-severity* uncertainty
model — an input to a barrier-corrosion score — and grants **no** coating-barrier,
batch-release, optimizer, or product-performance authority. Does not promote; does not
flip scientific_readiness; manifest 66 receipts / 11 modules untouched.

## Reproducibility
- OMP_NUM_THREADS=1, fixed seeds, no timestamp, floats round(.,6). Two runs →
  canonical SHA-256 `69d7eeda95f874584ee670515fa996b3d1d27298c4de29e333315227bdfbb2f5`
  (byte-identical). **TWO_REPLAY_GATE=PASS.** harness_sha256 `b968a89f…`.
- DSSE Ed25519 signed with trust-anchored Phase-0 evaluator key
  `phase0-evaluator-3ef6b35c…`, **AUDIT_ONLY** (promotes_authority=false,
  modifies_manifest=false). eval + reviewer key ids both derive the pinned trust store.
  INDEPENDENT_VERIFY=PASS. envelope_sha256 `86674a24…`.

## Files
- `corr_rate_conformal.py` — deterministic benchmark
- `result.{runA,runB,canonical}.json` — two runs + canonical
- `sign_conformal.py` — DSSE signer (AUDIT_ONLY)
- `corr-rate-conformal-receipt.v1.dsse.json` — signed receipt
