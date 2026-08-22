# potlife-gel-tfs-source-stratification-v1 — pooled "directional concordance HOLDS" is not panel-uniform

**AUDIT_ONLY red-team science increment. Promotes nothing. Flips no rights gate.**
Signed with the AUDIT_ONLY use of the `PHASE0_EVALUATOR` seed key (pinned in
`config/phase0-trust-store.v1.json`), NOT as a phase0 evaluation/review signature.

## Claim under attack

`amphora-cure-potlife-gate/evidence/audit/potlife-gel-tfs-crossendpoint-v1/potlife-gel-tfs-crossendpoint-receipt.v1.dsse.json`
headline: "...directional concordance (Spearman rho=0.5667572791, permutation
p=0.001799910004) HOLDS -- quantifying the dataset's standing honesty
disclosure that bulk gel maps application endpoints directionally, not
absolutely." This is stated as a single pooled result over the full locked
n=25 `cure_verification_set.json` panel, with no stratum-level disclosure.

## Pre-registered falsification criterion

The pooled claim is REFUTED (as stated, without stratification disclosure) if
any provenance stratum *inherent to the locked dataset's own row schema*
(n>=5) shows two-sided permutation p > 0.05 for the same gel_h-vs-tfs_h
relationship.

## Attack and result

The locked dataset carries a `phr` field per row. It is populated for the
first 16 systems and `null` for the trailing 9 (`ancamide_2424` through
`ancamide_260tn`) — a contiguous tail block, not a scattered/invented split.
This is the dataset's own fingerprint of a second, less-complete source table
folded into the nominal n=25.

Stratifying on `phr` presence:

- **with phr (n=16):** Spearman rho=0.7428, permutation p=0.0013 — strongly significant.
- **without phr (n=9):** Spearman rho=0.2204, permutation p=0.5729 — **not
  significant**; statistically indistinguishable from zero concordance.

Criterion met → **VERDICT: REFUTED.** ~36% of the panel (9/25 systems) that
the prior receipt's pooled headline folds into "HOLDS" carries no detectable
gel↔TFS directional relationship at the module's own p<0.05 threshold.

## What is true / what is false

- **True:** the pooled arithmetic in the prior receipt is exactly reproduced
  here (rho=0.5667572791 matches to 6 decimal places); duplicate-row removal
  (G2: one exact duplicate pair, `ancamide_2634`/`ancamide_2482`) and
  worst-case leave-one-out (G3: dropping `ancamide_2426`) do NOT independently
  break the pooled significance — both checks were run and both survived.
- **False:** that the panel supports directional concordance uniformly. It
  does not; the significance is concentrated entirely in the 16-row
  with-phr stratum and absent in the 9-row without-phr stratum.

## What this does NOT do

Does not claim the pooled arithmetic in the prior receipt is wrong; does not
identify *why* the without-phr rows lack concordance (measurement noise vs a
different supplier-guide edition vs undisclosed chemistry differences are all
consistent with the row schema as given); does not flip
`rights_gate_passed`; does not promote `amphora-cure-potlife-gate` to
PHASE_0; does not modify the locked dataset, the prior signed
gel-tfs-crossendpoint receipt, the signed Arrhenius KPI, or the manifest;
opens, parses, or derives from no quarantined source's payload content
(the locked verification dataset was already used, AUDIT_ONLY, by the prior
signed receipt this attacks).

## Files

- `run_source_stratification.py` — deterministic stratification audit harness
- `diagnostic.canonical.json` == `diagnostic.runB.json` (two-replay PASS)
- `potlife-gel-tfs-source-stratification-receipt.v1.dsse.json` — DSSE Ed25519, AUDIT_ONLY use of `PHASE0_EVALUATOR` key
- `sign_source_stratification.py` — signing + self-verification

## Reproduce

    python3 run_source_stratification.py   # diagnostic
    python3 sign_source_stratification.py  # DSSE Ed25519, AUDIT_ONLY
