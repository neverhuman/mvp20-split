#!/usr/bin/env python3
"""B3 prose repair: replace stale claims in amphora-molecule-property/docs/mission.md
with the corrected position, citing the refuting receipt inline.

Front-matter (the JSON between the leading --- fences) is NEVER touched; this script
asserts byte-identity of the front-matter before and after.
Each (old, new) pair must match EXACTLY ONCE or the script aborts without writing.
"""
import hashlib
import os
import sys

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
MISSION = os.path.join(ROOT, "amphora-molecule-property/docs/mission.md")

W3 = "evidence/audit/dielectric-retraction-v1/dielectric-retraction-superseding-kpi-receipt.v1.dsse.json"
C8F3 = "benchmarks/phys-ml-stack-comparison-c8-v3-final/c8_fire3_final_consolidated_receipt.v1.json"
C8F2 = "benchmarks/phys-ml-stack-comparison-c8-fire2-clean-subset-v1/c8_fire2_dielectric_clean_subset_receipt.v1.json"
C7 = "benchmarks/tg-density-external-validity-c7-v3-final/c7_final_tg_density_external_validity_verdict_receipt.v1.json"
W7 = "evidence/audit/multitarget-macro-bisection-external-validity-w7-v1/multitarget-macro-bisection-external-validity-receipt.v1.dsse.json"
W8 = "evidence/audit/vk-ridge-ygi-admissibility-w8-v1/vk-ridge-ygi-admissibility-audit-receipt.v1.dsse.json"
IDX = "evidence/phase0/kpis/RETRACTION-INDEX.md"

PAIRS = []


def P(old, new):
    PAIRS.append((old, new))


# ---------------------------------------------------------------- S-A: conformal AD forward-looking sentence now answered by C7
P(
    """optimizer, or product-performance authority; interval boundaries are
marginal not conditional; Phase-1 would require wet-lab Tg validation
on formulations sampled from the tested AD interior and a cross-
dataset transfer test to an independent experimental epoxy Tg dataset.
""",
    """optimizer, or product-performance authority; interval boundaries are
marginal not conditional; Phase-1 would require wet-lab Tg validation
on formulations sampled from the tested AD interior and a cross-
dataset transfer test to an independent experimental epoxy Tg dataset.

CORRECTED SCOPE (C7). That cross-dataset transfer test has since been run and
FAILED. Training on OpenPoly experimental Tg and cold-predicting Polyuniverse
Epoxy MD Tg degrades MAE 6.66x; the reverse direction degrades 16.60x; both
directions are anti-predictive (R2 -92.94 and -6.80, worse than a
predict-the-training-median null) because the two corpora occupy non-overlapping
Tg ranges (medians 346.3 K vs 117.8 K) and a bagged-tree RF cannot extrapolate
past its training-label range. Verdict CLAIM_REFUTED, receipt
`""" + C7 + """`.
These coverage and applicability-domain numbers therefore hold within the
Polyuniverse Epoxy computed corpus only; cross-corpus transfer is refuted.
`""" + IDX + """`
records this KPI as STANDS-WITHIN-CORPUS-ONLY.
""",
)

# ---------------------------------------------------------------- S-B: named-baseline head-to-head claim scope
P(
    """supervised-ML only — no physical group-contribution (Van Krevelen,
Bicerano) baseline is included, which would be a Phase-1 extension. It
grants no batch-release, manufacturing-qualification, optimizer, or
product-performance authority.
""",
    """supervised-ML only — no physical group-contribution (Van Krevelen,
Bicerano) baseline is included, which would be a Phase-1 extension. It
grants no batch-release, manufacturing-qualification, optimizer, or
product-performance authority. Within RadonPy/Polyuniverse chemotype only;
cross-corpus transfer of any Tg model in this module is refuted, see
`""" + C7 + """`;
status STANDS-WITHIN-CORPUS-ONLY in `""" + IDX + """`.
""",
)

# ---------------------------------------------------------------- S-C: VK physics-vs-ML claim scope
P(
    """Claim scope: this KPI documents ML value-add over a **simplified 18-group
Van Krevelen physical baseline** on Polyuniverse Epoxy 1M chemistry
only. It does NOT claim ML beats the full Bicerano 40-group table
(which would need Phase-1 implementation), nor a chemistry-aware graph
neural network baseline (polyBERT, Chemprop). It grants no batch-release,
manufacturing-qualification, optimizer, or product-performance authority.
""",
    """Claim scope: this KPI documents ML value-add over a **simplified 18-group
Van Krevelen physical baseline** on Polyuniverse Epoxy 1M chemistry
only. It does NOT claim ML beats the full Bicerano 40-group table
(which would need Phase-1 implementation), nor a chemistry-aware graph
neural network baseline (polyBERT, Chemprop). It grants no batch-release,
manufacturing-qualification, optimizer, or product-performance authority.
Within Polyuniverse Epoxy chemotype only; cross-corpus transfer refuted, see
`""" + C7 + """`;
status STANDS-WITHIN-CORPUS-ONLY in `""" + IDX + """`.
""",
)

# ---------------------------------------------------------------- S1: VK Ridge 807 headline
P(
    """**MAJOR POSITIVE FINDING**: Ridge Y_gi fit BEATS the published-values baseline by **32.6 K** on held-out scaffold-safe test polymers, reaching Bicerano-level accuracy.
""",
    """**AGGREGATE-MAE FINDING — the structural claim built on it is REFUTED (W8, below)**: Ridge Y_gi fit BEATS the published-values baseline by **32.6 K** on held-out scaffold-safe test polymers, reaching Bicerano-level *aggregate* MAE. That is an aggregate-error statement within the Polyuniverse Epoxy MD-simulated corpus and nothing more: it does NOT establish that the fitted 24-group table is physically correct. The physical-admissibility audit
`""" + W8 + """`
(W8, verdict `REFUTED`) shows 2 of 24 fitted coefficients are sign-reversed against a published table in which 0/24 values are negative. `""" + IDX + """` records this KPI as REFUTED.
""",
)

# ---------------------------------------------------------------- S2: 24-group structure confirmed
P(
    """1. **The 24-group STRUCTURE is CONFIRMED CORRECT at scale**: Train MAE 22.6 K, Test MAE 22.0 K — the 0.6 K generalization gap is negligible. Ridge-fitted Y_gi values robustly generalize to unseen scaffold-safe test polymers.
""",
    """1. **CORRECTED — "the 24-group STRUCTURE is CONFIRMED CORRECT at scale" is REFUTED**: the aggregate fit numbers stand as measured (Train MAE 22.6 K, Test MAE 22.0 K, 0.6 K train/test gap, so the fitted values do interpolate to unseen scaffold-safe test polymers *within this corpus*), but structural correctness does not follow from aggregate MAE. Per
`""" + W8 + """`
(W8, verdict `REFUTED`, pre-registered criterion ">=1 of 24 fitted Y_gi has sign opposite to its published (100% positive) counterpart"), 2 of 24 fitted Y_gi are SIGN-REVERSED: `vinyl_CH2` fitted **-3125.15** vs published **+2000** K.g/mol, and `nitrile` fitted **-2843.55** vs published **+5500** K.g/mol. The receipt's own words: "This is not a magnitude disagreement ... it is a directional physical contradiction that falsifies the claim that the fit 'confirms the 24-group STRUCTURE is correct.'"
""",
)

# ---------------------------------------------------------------- S3: under-determination resolved
P(
    """2. **The prior "under-determination" hypothesis is RESOLVED**: With n_train = 807 polymers (vs prior n=15), the calibration system is now over-determined; the LOO-CV catastrophe (MAE jumped from 33 K to 121 K on n=15) does not occur here.
""",
    """2. **CORRECTED — "the prior under-determination hypothesis is RESOLVED" holds only for common-support groups**: n_train = 807 does remove the n=15 LOO-CV catastrophe (MAE 33 K -> 121 K) for groups carried by most training polymers, but it does NOT resolve under-determination for rare ones. Both sign-flipped coefficients sit in the bottom third of training support (`vinyl_CH2` n_train=31, rank 7/24; `nitrile` n_train=124, rank 9/24) and the Spearman correlation between n_train and |ratio_fitted_over_published - 1| across all 24 groups is **-0.523** (more support, less deviation) — the same under-determination mechanism the 15-polymer receipt diagnosed. W8 states the claim lock `prior_ridge_receipt_under_determination_hypothesis_now_resolved` "is therefore false for the rare-group coefficients". Resolution must be scope-limited to groups with n_train of roughly 500 or more. Receipt:
`""" + W8 + """`.
""",
)

# ---------------------------------------------------------------- S4: chemistry-plausible
P(
    """4. **Fitted Y_gi values are chemistry-plausible**: Ratios cluster around published values for high-frequency groups; deviations for low-frequency groups reflect finite-sample noise, not structural mismatch.
""",
    """4. **CORRECTED — fitted Y_gi values are NOT uniformly chemistry-plausible**: ratios do cluster around published values for high-frequency (high-support) groups, but **13 of 24 (54%)** deviate by more than 50% in magnitude from published, and **2 of 24 are physically inadmissible** — negative Y_gi in a theory whose own published table asserts every group makes a positive contribution to Tg. The low-support deviations therefore are not benign finite-sample noise; they include outright sign reversals. Receipt:
`""" + W8 + """`
(W8, verdict `REFUTED`).
""",
)

# ---------------------------------------------------------------- S5: VK Ridge portfolio implication
P(
    """**Portfolio implication**: For Phase-1, this receipt proves that a 24-group Van Krevelen calibration can achieve Bicerano-level MAE with adequate training data. The next Phase-1 gate must acquire 100+ EXPERIMENTAL polymer Tg values (Bicerano 2002 database, POLY-DB) to re-run this calibration on the target experimental context.
""",
    """**Portfolio implication (CORRECTED)**: this receipt shows a 24-group Van Krevelen calibration can reach Bicerano-level *aggregate* MAE on MD-simulated Polyuniverse Epoxy data given adequate training data. It does NOT prove the group structure is correct, and unconstrained Ridge is shown to produce physically inadmissible (negative) coefficients wherever group support is thin. Phase-1 must therefore (a) constrain the fit to non-negative Y_gi, matching the published theory's positivity requirement, or acquire enough polymers containing the under-supported groups (`vinyl_CH2` n=31, `nitrile` n=124) to determine them, and (b) acquire 100+ EXPERIMENTAL polymer Tg values (Bicerano 2002 database, POLY-DB) to re-run this calibration on the target experimental context. Refuting receipt:
`""" + W8 + """`.
""",
)

# ---------------------------------------------------------------- S6: VK Ridge claim scope
P(
    """Claim scope: this KPI documents Ridge Y_gi calibration on n=807
MD-simulated Polyuniverse Epoxy polymers reaching Bicerano-level test
MAE. Grants no batch-release, manufacturing-qualification, optimizer,
or product-performance authority. Fitted Y_gi values are calibrated for
the MD-simulated context of Polyuniverse Epoxy; published Y_gi remain
correct for experimental-Tg applications.""",
    """Claim scope: this KPI documents Ridge Y_gi calibration on n=807
MD-simulated Polyuniverse Epoxy polymers reaching Bicerano-level test
MAE. Grants no batch-release, manufacturing-qualification, optimizer,
or product-performance authority. Fitted Y_gi values are calibrated for
the MD-simulated context of Polyuniverse Epoxy; published Y_gi remain
correct for experimental-Tg applications. The KPI's own claim locks
`24_group_structure_confirmed_correct_at_scale` and
`prior_ridge_receipt_under_determination_hypothesis_now_resolved` are REFUTED
as stated and must be read as scope-limited to groups with n_train of roughly
500 or more, per
`""" + W8 + """`.""",
)

# ---------------------------------------------------------------- S7: dielectric section heading
P(
    """### Empirical benchmark result — OpenPoly dielectric constant ML baseline (REAL POSITIVE lift, n=295)
""",
    """### Empirical benchmark result — OpenPoly dielectric constant ML baseline (within-OpenPoly-corpus lift, n=295; module-level dielectric position: NO COMPETENT MODEL)
""",
)

# ---------------------------------------------------------------- S8: dielectric capability-delivery lede
P(
    """Directly delivers the coating IP prediction capability for POLYMER DIELECTRIC
CONSTANT — a real electrical-insulation property directly relevant to marine
electrical enclosures, cable coatings, and dielectric layers.
""",
    """> **RETRACTION / SCOPE NOTICE — dielectric constant.** The module's portfolio-level
> dielectric-constant claim is RETRACTED. The authoritative module position is the
> consolidated founder-panel row, quoted verbatim from
> `""" + C8F3 + """`
> (`founder_f8_panel_row_text.dielectric_constant`):
>
> > "NO COMPETENT MODEL -- label integrity failure (89.5% of RadonPy ground-truth
> > violates eps_static>=n^2); on the n=113 physically-valid subset all of
> > {physics MAE 19.9 R2 -1.04, ML MAE 13.1 R2 -0.03, stack MAE 14.5 R2 -0.05}
> > fail to beat the test-set mean. Do not report a point estimate."
>
> The constraint is model-independent: eps_static >= eps_infinity = n_measured^2
> (Frohlich 1949 Ch.2 / Debye 1929). 962 of 1075 RadonPy PI1070
> `static_dielectric_const` rows violate it; only 113 rows (10.5%) are admissible.
> On that clean subset the zero-contamination retrain gives physics MAE 19.8875
> R2 -1.0405, ML MAE 13.0566 R2 -0.0263, stack MAE 14.5221 R2 -0.0482, and the
> paired-bootstrap 90% CI of (physics MAE - ML MAE) includes zero
> (`""" + C8F2 + """`).
>
> What SURVIVES is narrower than this section originally advertised. The superseding
> retraction receipt
> `""" + W3 + """`
> (campaign item W3, verdict `CLAIM_REFUTED`) dispositions THIS KPI —
> `evidence/phase0/kpis/openpoly-dielectric-constant-ml-baseline-kpi.v1.json`,
> SHA-256 `cf94eb185fb8fd882328987f6484f8698125157b749d39d660b711f4e068d139` —
> as `NOT_RETRACTED_LABELS_ADMISSIBLE`, because it trains and evaluates entirely on
> OpenPoly's own dielectric column, which the same audit found to have 0/295
> admissibility violations. Its numbers below therefore stand AS MEASURED **within the
> OpenPoly literature chemotype only**, and per that receipt "must not be read as
> evidence about RadonPy-derived dielectric predictions".
>
> The module's two other dielectric KPIs ARE retracted by the same receipt and by
> the repo-root `logs/claims-requiring-retraction.jsonl` lines 1-2:
> `evidence/phase0/kpis/external-validation-dielectric-ml-openpoly-to-radonpy-kpi.v1.json`
> (R2 0.0248 scored against the 89.5%-inadmissible target) and
> `evidence/phase0/kpis/mixed-openpoly-radonpy-dielectric-conformal-kpi.v1.json`
> (test R2 0.6991, RadonPy-slice R2 0.7001). Per W3 those numbers "are WITHDRAWN as evidence of genuine
> chemistry-to-dielectric-constant predictive skill ... and MUST NOT be cited in any
> founder-facing or KPI-surface summary as a positive result." See also
> `""" + IDX + """`
> (section R-A09: both KPIs RETRACTED, this one STANDS).

This section records a WITHIN-CORPUS ML baseline for POLYMER DIELECTRIC CONSTANT on the
OpenPoly literature corpus. It does NOT deliver a deployable coating-IP dielectric
prediction capability: every cross-corpus dielectric evaluation this module attempted has
been retracted, so applicability to marine electrical enclosures, cable coatings, or
dielectric layers is NOT established.
""",
)

# ---------------------------------------------------------------- S9: dielectric MAJOR POSITIVE FINDING
P(
    """**MAJOR POSITIVE FINDING**: Random Forest / HistGBM / Ridge on Morgan
""",
    """**WITHIN-CORPUS POSITIVE FINDING (OpenPoly n=295 only; see the retraction/scope notice
above)**: Random Forest / HistGBM / Ridge on Morgan
""",
)

# ---------------------------------------------------------------- S10: dielectric "REAL predictive capability"
P(
    """1. **REAL predictive capability**: MAE 0.4040 εr units means the model predicts
   dielectric constant within ~8.0% of the target range for held-out scaffold families.
   Pearson r = +0.773 indicates strong rank-correlation with published εr values.
""",
    """1. **Within-corpus predictive skill (OpenPoly chemotype only)**: MAE 0.4040 εr units
   means the model predicts dielectric constant within ~8.0% of the target range for
   held-out OpenPoly scaffold families. Pearson r = +0.773 indicates strong
   rank-correlation with published εr values. This is a within-corpus statement only —
   the module's only cross-corpus dielectric evaluations are RETRACTED and its
   module-level position is "NO COMPETENT MODEL -- label integrity failure", see
   `""" + W3 + """`.
""",
)

# ---------------------------------------------------------------- S11: dielectric portfolio implication (the headline stale claim)
P(
    """**Portfolio implication**: `amphora-molecule-property` can now offer polymer
dielectric constant prediction with a defended MAE ~0.40 εr units on Morgan-
fingerprint features. Directly applicable to coating chemistry decisions for
electrical-insulation applications.
""",
    """**Portfolio implication (CORRECTED — the original claim here is RETRACTED)**:
`amphora-molecule-property` CANNOT offer polymer dielectric constant prediction as a
portfolio capability. The authoritative module-level position, quoted verbatim from
`""" + C8F3 + """`
(`founder_f8_panel_row_text.dielectric_constant`), is: "NO COMPETENT MODEL -- label
integrity failure (89.5% of RadonPy ground-truth violates eps_static>=n^2); on the n=113
physically-valid subset all of {physics MAE 19.9 R2 -1.04, ML MAE 13.1 R2 -0.03, stack
MAE 14.5 R2 -0.05} fail to beat the test-set mean. Do not report a point estimate."
What remains citable is only the narrow measurement recorded above — MAE 0.4040 εr,
holdout R² +0.5649, LOSO-CV R² +0.6591 — **within the OpenPoly literature chemotype
only**, whose labels pass their own admissibility control (0/295 violations), per
`""" + W3 + """`
disposition `NOT_RETRACTED_LABELS_ADMISSIBLE`. Cross-corpus dielectric transfer is
retracted; applicability to electrical-insulation coating decisions is NOT established.
""",
)

# ---------------------------------------------------------------- S12: Push #20 external validation finding 1
P(
    """1. **Push #20 Ridge BEATS published Van Krevelen 1990 baseline by 20.9 K** (+22.9% relative) on an independent experimental dataset. The data-driven Y_gi calibration outperforms the textbook Y_gi even outside its MD-simulated training distribution — RESOLVES the Push #20 Phase-1 hypothesis about applicability domain.
""",
    """1. **Push #20 Ridge BEATS published Van Krevelen 1990 baseline by 20.9 K** (+22.9% relative) on an independent experimental dataset. The data-driven Y_gi calibration outperforms the textbook Y_gi even outside its MD-simulated training distribution. CORRECTED SCOPE: this is an aggregate-error comparison and does NOT vindicate the fitted 24-group table structurally — 2 of the 24 coefficients being applied here (`vinyl_CH2`, `nitrile`) are sign-reversed and physically inadmissible per
`""" + W8 + """`
(W8, verdict `REFUTED`), so "resolves the applicability-domain hypothesis" must be read as scope-limited to the well-supported groups.
""",
)

# ---------------------------------------------------------------- S13: Push #20 external validation finding 4
P(
    """4. **Real rank correlation** (Pearson r = +0.264) confirms the 24-group structure captures ordinal Tg signal on experimental data — enough for coating-family screening even when absolute MAE is high.
""",
    """4. **Real rank correlation** (Pearson r = +0.264) shows the fitted 24-group table carries *some* ordinal Tg signal on experimental data. CORRECTED: it does not confirm the 24-group structure — that claim is REFUTED by
`""" + W8 + """`
— and r = +0.264 alongside MAE 70.42 K is a weak screening signal, not a predictor.
""",
)

# ---------------------------------------------------------------- S14: Push #20 external validation portfolio bullet
P(
    """- Confirms Push #20's Ridge Y_gi calibration has real generalization value.
""",
    """- Confirms Push #20's Ridge Y_gi calibration has aggregate-error generalization value on
  this dataset (MAE 70.42 K vs NULL median 71.39 K — a +1.0 K / +1.4% margin). CORRECTED:
  it does NOT vindicate the fitted 24-group table structurally; 2 of its 24 coefficients are
  sign-reversed and physically inadmissible, see
  `""" + W8 + """`.
""",
)

# ---------------------------------------------------------------- S15: OpenPoly Tg ML interpretation 1-3
P(
    """1. **ML delivers substantial lift over physics-Ridge on experimental Tg**: ML LOSO
   MAE 51.24 K vs physics-Ridge 70.42 K on SAME polymers = +27.2%
   relative improvement. Direct empirical answer to red-team: on this experimental
   data distribution, ML strictly dominates the frozen physics-Ridge inference.

2. **Portfolio priority**: For coating Tg prediction on experimental targets, the
   ML pipeline (Morgan fingerprints + Random Forest / HistGBM) should be the
   primary predictor; physics-Ridge remains useful as a fast rank-order signal.

3. **Positive R² on rigorous LOSO-CV** confirms cross-scaffold generalization.
""",
    """1. **ML delivers substantial lift over physics-Ridge on experimental Tg — within the
   OpenPoly corpus only**: ML LOSO MAE 51.24 K vs physics-Ridge 70.42 K on SAME polymers
   = +27.2% relative improvement. Direct empirical answer to red-team: on this
   experimental data distribution, ML dominates the frozen physics-Ridge inference.
   Within RadonPy/OpenPoly-corpus chemotype only; cross-corpus transfer is REFUTED, see
   `""" + C7 + """`
   (overall_verdict `CLAIM_REFUTED`).

2. **Portfolio priority (CORRECTED — scope-limited)**: within the OpenPoly
   experimental-Tg distribution the ML pipeline (Morgan fingerprints + Random Forest /
   HistGBM) outperforms physics-Ridge. This does NOT license it as a general coating Tg
   predictor. Trained on OpenPoly experimental Tg (n=443) and cold-applied to
   Polyuniverse Epoxy MD Tg it degrades **6.66x** (MAE 253.58 K, R² -92.94); in reverse
   it degrades **16.60x** (MAE 231.65 K, R² -6.80); both directions are WORSE than a
   predict-the-training-median null, i.e. anti-predictive, because the two corpora
   occupy non-overlapping label ranges. The module's honest applicability domain for
   this baseline is within-OpenPoly-corpus ONLY, and
   `""" + IDX + """`
   records the KPI as STANDS-WITHIN-CORPUS-ONLY. Same receipt as above.

3. **Positive R² on rigorous LOSO-CV** confirms cross-*scaffold* generalization inside
   the OpenPoly corpus. CORRECTED: it does not confirm cross-*corpus* generalization —
   that stronger claim was tested directly and refuted (C7, receipt cited above).
""",
)

# ---------------------------------------------------------------- S16: portfolio-wide answer citing dielectric R2 +0.66
P(
    """4. **Portfolio-wide answer**: Combined with Push #23 (dielectric R² +0.66), Push
   #24 (contact angle mixed), Push #25 (physics validation), and this push, the
   `amphora-molecule-property` module now has a defended coating-IP Tg predictor
   with published-reference MAE ≤ 50 K on ~59% of independent literature polymers.
""",
    """4. **Portfolio-wide answer (CORRECTED)**: Push #23's dielectric LOSO-CV R² +0.6591 may
   only be cited scoped to the OpenPoly literature chemotype. The module's
   portfolio-level dielectric position is "NO COMPETENT MODEL -- label integrity
   failure (89.5% of RadonPy ground-truth violates eps_static>=n^2)", per
   `""" + W3 + """`
   and `""" + C8F3 + """`.
   The Tg numbers in this section likewise hold **within the OpenPoly corpus only**
   (cross-corpus transfer REFUTED at 6.66x/16.60x degradation,
   `""" + C7 + """`).
   The module therefore has a within-OpenPoly-corpus Tg baseline with published-reference
   MAE <= 50 K on ~59% of that corpus — not a general defended coating-IP Tg predictor.
""",
)

# ---------------------------------------------------------------- S17: OpenPoly Tg ML claim scope
P(
    """Applicability domain restricted to the openpoly scaffold distribution. Phase-1
explicitly flags: extend to 1000+ experimental Tg polymers; add conformal
prediction UQ; Bicerano 40-group physics baseline head-to-head.""",
    """Applicability domain restricted to the openpoly scaffold distribution — and, per C7's
direct cross-corpus test, to the OpenPoly corpus itself: transfer to an independent Tg
corpus is REFUTED
(`""" + C7 + """`).
Phase-1 explicitly flags: extend to 1000+ experimental Tg polymers; add conformal
prediction UQ; Bicerano 40-group physics baseline head-to-head; and re-test transfer on a
corpus whose Tg range overlaps the training range.""",
)


def frontmatter(text):
    assert text.startswith("---\n"), "mission.md does not start with a --- fence"
    end = text.index("\n---\n", 3)
    return text[: end + len("\n---\n")]


def main():
    with open(MISSION, "r", encoding="utf-8") as fh:
        orig = fh.read()

    fm_before = frontmatter(orig)
    out = orig
    report = []
    for i, (old, new) in enumerate(PAIRS, 1):
        n = out.count(old)
        if n != 1:
            sys.stderr.write("PAIR %d matched %d times (expected 1):\n%r\n" % (i, n, old[:160]))
            sys.exit(2)
        out = out.replace(old, new, 1)
        report.append((i, hashlib.sha256(old.encode()).hexdigest()[:12],
                       hashlib.sha256(new.encode()).hexdigest()[:12]))

    fm_after = frontmatter(out)
    if fm_before != fm_after:
        sys.stderr.write("FRONT-MATTER CHANGED - aborting\n")
        sys.exit(3)

    with open(MISSION, "w", encoding="utf-8") as fh:
        fh.write(out)

    print("pairs_applied=%d" % len(PAIRS))
    print("frontmatter_sha256_before=%s" % hashlib.sha256(fm_before.encode()).hexdigest())
    print("frontmatter_sha256_after =%s" % hashlib.sha256(fm_after.encode()).hexdigest())
    print("mission_sha256_before=%s" % hashlib.sha256(orig.encode()).hexdigest())
    print("mission_sha256_after =%s" % hashlib.sha256(out.encode()).hexdigest())
    for i, a, b in report:
        print("pair %02d old=%s new=%s" % (i, a, b))


if __name__ == "__main__":
    main()
