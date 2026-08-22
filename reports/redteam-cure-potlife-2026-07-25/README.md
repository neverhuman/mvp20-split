# Red-team memo — cure-potlife Arrhenius Phase-0 verification (2026-07-25)

**Author:** hourly red-team cron (xbabe1 → xbabe2, canonical tree only)
**Scope:** coating IP — two-part DGEBA + amine, marine anti-corrosion.
**Authority:** AUDIT_ONLY. Promotes nothing. No existing receipt or manifest changed
(manifest still 66 receipts / 11 modules).

## Question asked
"I do NOT believe you that we actually have FULL phase 0." Correct to be skeptical.

## Honest Phase-0 state (verified on canonical host this run)
- **Defensible Phase-0 = 10**: 9 infrastructure/trust-kernel/deterministic-control
  modules **+ amphora-solvency-score** (first SCIENCE module).
- Solvency promotion is real and intact: `evaluation.v1.dsse.json`
  (`phase0_eligible:true, scientific_outcome:PASSED, failed_gates:[]`, evaluator =
  trust-anchored `phase0-evaluator-3ef6b35c`) + `independent-review.v1.dsse.json`
  (`accepted_for_phase0:true`, reviewer = `phase0-internal-reviewer-47233af1`);
  bundle_hash `250df360…` == on-disk result (binding intact).
- The signed **count-integrity-v1** audit (03:10) that reported "9, zero science"
  **predates** solvency's 05:28 promotion — do not present its "zero science" as current.
- **Caveat for the report:** `config/program/phase0-decision-report.v2.json` still shows
  `reported_phase0_count: null / EXECUTION_INCOMPLETE`. Regenerate it to reflect the
  true 10 before founder use. The "16" figure remains stale — do NOT use it.
- The 7 previously-"drifted" PHASE_0 badges (cro-protocol-packager,
  evidence-intake-validator, known-answer-benchmarks, optimizer-orchestrator,
  redteam-audit, report-packager, source-ledger) remain failing re-verification and
  are NOT in the 10.

## This run's contribution — cure-potlife-gate is the strong SECOND science candidate
Independently red-teamed its Phase-0 Arrhenius pot-life KPI. Real theory
(Arrhenius 1889 rate-constant scaling), real data (CC0 compilation from Prime/Turi
1997, Kamal-Sourour 1973, Riccardi 1984, Blanco 2005 + supplier TDS), 12 DGEBA+amine
systems at 10/22.78/30/40 °C.

**All six acceptance gates pass** (independently recomputed on a code path disjoint
from the Rust benchmark, matching to <1e-6):
- arrhenius pot-life MAPE **0.1473** (≤0.20)
- lift over no-temperature baseline **0.805** absolute pp (≥0.30)
- held-out 30 °C extrapolation MAPE **0.1563** (≤0.25)
- per-system within ±40% **12/12** (≥0.80)
- applicability-domain fail-closed 9/9; authority-lock preservation 1.0

**NON-CIRCULARITY proven (the key red-team result):** the pot-life-derived apparent
activation energy is systematically **0.884×** the independently-cited calorimetric Ea
(stdev 0.029) with linear Arrhenius R² ≈ 0.99 (< 1.0). Had the pot-life curve been
synthesized from the cited Ea, the ratio would be exactly 1.000 with R² = 1.0000.
→ The two source classes (academic DSC Ea vs supplier pot-life TDS) are genuinely
independent and agree to ~15% MAPE. This is real cross-source validation, not a
tautology. (Physically consistent: gel/pot-life apparent Ea < overall reaction Ea.)

## Honest limitations (state these to founders)
- Data is a literature/TDS **compilation**, not Amphora wet-lab measurement.
- Accuracy is **directional / order-of-magnitude**: only 1/12 systems within ±20%
  (the passing bar is the looser ±40%).
- "lift" in the KPI = absolute MAPE difference (0.805 pp), not relative (0.845); both
  clear the 0.30 floor.
- Doc-vs-execution nit: KPI documents T_ref = 295.928 K but code uses 73 °F exactly
  (295.9278 K). ~1e-5 impact; cosmetic.

## Why NOT promoted this run (deliberate, honest)
cure-potlife is technically Phase-0-**ready** (gates pass, bindings intact, Rust+Python
two-replay reproduces). It is blocked ONLY by the two trust-anchored signatures
(PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER). Those service keys are intentionally
not in-repo; this cron holds only the LOCAL_DEVELOPMENT_AUDIT_ONLY key. A single
identity signing both roles would violate `required_independence_scope =
CODE_PATH_AND_SIGNING_IDENTITY`. Promotion is a **governance ceremony**, not a science,
data, or key-custody gap. Post-promotion ceiling stays CRO_GATED / CONSTRAINT_ONLY;
Phase-1 remains BLOCKED (36 owned independently-mixed CRO runs pending).

## Signed artifact
`amphora-redteam-audit/benchmarks/cure-potlife-arrhenius-verification-v1/`
- `cure_potlife_arrhenius_verification_audit.py` (independent harness)
- `diagnostic.canonical.json` == `diagnostic.runB.json`, sha
  `3b7eadb1401d27346389adb16b9698e90523a1cfc74e5866a14b8366fc3ae758` (two-replay PASS)
- `replay_receipt.v1.dsse.json` — DSSE Ed25519, key `local-9028773f…`, SIGNATURE_VALID,
  envelope sha `c4ac5db0ede3122cd9fb668fcf1e0145e9d8716c0c717c71b82d226946334871`

## Recommendation to founders
Present **10 defensible Phase-0 (9 infra + solvency)**, with cure-potlife-gate as a
scientifically-verified SECOND science module awaiting only the dual-signature
ceremony. Regenerate the decision report (currently null/incomplete) before the pack.
