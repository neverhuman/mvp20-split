# Red-team: rights-integrity of the "66 signed receipts" — 2026-07-25 (hourly cron, xbabe1→xbabe2)

All work on `ssh xbabe2:/home/ubuntu/amphora/build/mvp20-split`. No existing
signed receipt modified. No front-matter promoted. xbabe1 tree untouched.
Every number below is emitted by a deterministic, two-replay-gated, DSSE-signed
harness — not asserted in prose.

## 0. Verdict

We do **not** have full Phase 0 — this run corroborates the three prior audits
(defensible Phase-0 count is ~9 infra/trust modules; **zero** science modules
have a positive-outcome Phase 0; trust-store gap and absent trust-anchored
signing keys remain governance blockers). This run adds one **new, previously
unreported** integrity finding that directly bears on the founder headline.

## 1. New finding — 8 of the 66 signed receipts score KPIs on CONTEXT_ONLY data

The tree's own rights ledger of record, `feedback/v2/reports/rights-report.json`
(schema `amphora.rights-decision.v2`), classes every `polyverse_*` acquisition
unit as **`CONTEXT_ONLY`** under the *Georgia Tech Research Corporation General
Public Use License Agreement* — a distinct class from the `DERIVATIVE_ALLOWED`
sources (bigsoldb, openpoly, radonpy, NIST corr-data, omg, polyomics, point2)
that legitimately back scored models. `CONTEXT_ONLY` means usable as context,
**not** as the basis of a derivative scored KPI. The program already knows this:
`config/program/{viscosity,solvency,eis-corrosion}-sources.v1.json` label these
sources `MIXED_CONTEXT_ONLY`.

Applying that ledger to every manifest-indexed receipt (harness output, verbatim):

- **8** of the 66 signed receipts derive a scored KPI from `polyverse_*` data.
- **8/8** carry **no** rights-class self-declaration anywhere in the receipt.
- **3** present a **POSITIVE capability KPI** a founder would read as a
  validated, scoring-eligible result:
  - `amphora-solvency-score` — polyverse **CED** predictor, "R²=0.625"
  - `amphora-viscosity-score` — polyverse **melt-viscosity** QSPR, "R²=0.944"
  - `amphora-viscosity-score` — polyverse melt-viscosity **conformal PASSED**
- The other 5 are honest negatives/diagnostics or physics-vs-ML comparisons
  (e.g. diffusivity "R²=0.293, random 0.911 leakage indicator"; sorption
  "R²=-0.078 honest leakage") — still built on CONTEXT_ONLY data, but not
  overclaiming.
- All 8 manifest hashes **match disk** — this is a rights problem, not a
  staleness problem (unlike the 7 stale-hash receipts found in run 2).

Implicated modules — all three are `PRE_PHASE_0`, so nothing here retroactively
breaks a promotion; it undermines the *science-coverage narrative*:
`amphora-solvency-score`, `amphora-viscosity-score`,
`amphora-barrier-corrosion-score`.

## 2. Why this is the highest-value finding available this run

The science portfolio is otherwise saturated with real, rights-clean receipts
(Tg, density, dielectric, RI, CTE, water uptake, contact angle, EEW/AHEW,
Fedors molar-volume, NIST corrosion, BigSolDB solvency). Adding a marginal new
receipt on saturated ground would be padding — the exact behaviour the founder
distrusts. The real remaining gaps are **not** missing science; they are:

1. **Governance** — absent trust-anchored evaluator/reviewer keys →
   `EVALUATION_SIGNATURE_ABSENT` cannot be cleared; `operational_readiness:
   SHADOW` forces `scientific_outcome: FAILED`.
2. **Rights** — this finding: three modules' *only* current scored KPIs rest on
   CONTEXT_ONLY data, and there is **no rights-clean in-tree substitute** for
   melt-viscosity / solvent-diffusivity / sorption measurements (consistent with
   the standing note that viscosity KU/sag needs purchased ASTM data). CED can
   in principle be re-derived rights-clean via the already-validated Fedors/HvK
   engine, but no *independent* in-tree observable for δ exists (RadonPy has no
   CED/solubility column; BigSolDB has densities only — already used for the
   molar-volume validation), so a clean CED **validation** receipt is not
   honestly achievable this run.

## 3. Recommendation for the founder report

Report the headline as **58 rights-clean-scored + 8 context-only-scored**, not a
flat "66 signed receipts". For the three implicated modules, either (a)
re-acquire the underlying measurements under a `DERIVATIVE_ALLOWED` licence, or
(b) re-scope those receipts as CONTEXT_ONLY diagnostics and annotate the manifest
KPI summaries. Do not present polyverse CED/melt-viscosity KPIs as
scoring-eligible capabilities.

## 4. Evidence (signed, this run)

- Harness: `amphora-redteam-audit/benchmarks/rights-integrity-v1/rights_integrity_audit.py`
- Canonical diagnostic SHA-256 (two-replay PASS, run A == run B):
  `130707cd8c1884807995e2f745fa1dffd6aa707badfec0b39972e94fb9b3023d`
- Signed receipt: `amphora-redteam-audit/benchmarks/rights-integrity-v1/replay_receipt.v1.dsse.json`
  - body SHA-256 `2848d544944cd95d0d62d17973e727201ac857a4b5b4db3e2d4feb7f2375cdff`
  - envelope SHA-256 `861320314422bbb613cba3074dc061fd1fbe3d86617787cc66e9d33b95f8d828`
  - `SIGNATURE_VERIFY=PASS`, key `local-9028773f49591193` (LOCAL_DEVELOPMENT_AUDIT_ONLY;
    explicitly not a trust-anchored phase0 key)
- Modifies none of the 66 signed receipts; promotes nothing; clears no gate.
