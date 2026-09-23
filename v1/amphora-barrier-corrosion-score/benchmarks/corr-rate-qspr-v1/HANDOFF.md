# corr-rate-qspr-v1 — barrier-corrosion substrate corrosion-rate diagnostic

**Date:** 2026-07-25 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**

## What this is
An independent, fully in-tree, **two-replay byte-stable** leave-material-out
corrosion-rate QSPR on the NIST CORR-DATA database (rights_class
`DERIVATIVE_ALLOWED`). It scientifically executes the
`SCIENTIFIC_BENCHMARK_NOT_EXECUTED` benchmark for `amphora-barrier-corrosion-score`.

## Headline (honest KPI)
- Target: `log10(corrosion_rate_mm_per_year)`, n=7,699 rows, 612 materials, 155 environments.
- **Leave-material-out (GroupKFold, group=material) HistGBM: R²=0.316, RMSE=1.036 log units**,
  cluster-bootstrap 95% CI [0.989, 1.076].
- Beats best naive baseline (global/env/material mean) by **5.5%** RMSE.
- Environment-safe (leave-environment-out) R²=0.112.
- **Leakage indicator**: random-5fold R²=0.460 → random CV overstates skill by
  ΔR²=0.145 vs group-safe. Random CV is the wrong metric for this problem.
- Alloy composition coverage 70% (nominal wt% for the high-count families;
  HistGBM handles missing composition natively).

## Reproducibility
- Two independent full runs → canonical SHA-256 `e3bea4fc…` (byte-identical). **TWO_REPLAY_GATE=PASS.**
- DSSE Ed25519 signed with repo **LOCAL_DEVELOPMENT_AUDIT_ONLY** key
  `local-9028773f…` — **NOT** trust-anchored in `config/phase0-trust-store.v1.json`.
  `SIGNATURE_VERIFY=PASS`.

## What it does NOT do (authority ceilings held)
- Does **NOT** close `EVALUATION_SIGNATURE_ABSENT` (needs trust-anchored
  phase0-evaluator key + independent review — a governance ceremony, not a build fix).
- Does **NOT** flip the decision report to PHASE_0. Not touched.
- **Scope honesty:** this is *bare metal/alloy substrate* corrosion, not organic
  epoxy-amine **coating-barrier** performance. Marine environments (Seawater, NaCl,
  atmospheric) are present, but no coating-barrier ranking authority is created.

## Red-team finding on prior work
The three in-tree receipts `corr_data_corrosion_rate_qspr_model{,_v3_env_features,
_material_safe_v2}.v1.json`:
- are signed with `toolkit-reviewer-cbe8c0fd…` — **NOT** trust-anchored (self-attested);
- carry **no** two-replay gate;
- reference a raw object `80d8f4d2…` whose **builder scripts are absent** from the tree
  (not reproducible on this host);
- their headline (material-safe GBM R²≈0.41) is **directionally reproduced** here from
  raw data with a simpler, disclosed feature set and a different sklearn (R²=0.316).
Those receipts were **NOT modified**. This diagnostic is the reproducible artifact of record.

## Files
- `corr_rate_qspr.py` — self-contained deterministic benchmark
- `diagnostic.{runA,runB,canonical}.json` — two independent runs + canonical
- `sign_corr.py`, `inhouse_benchmark_receipt.v1.dsse.json` — signing + signed receipt
