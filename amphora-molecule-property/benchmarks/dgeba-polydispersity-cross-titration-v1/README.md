# dgeba-polydispersity-cross-titration-v1 (AUDIT_ONLY)

Module: `amphora-molecule-property`. Authority: **AUDIT_ONLY**. Promotes nothing.
Manifest untouched at 66 receipts / 11 modules.

## What this adds

The module already had two signed structural read-outs of the DGEBA advancement state `n`:

| receipt | relation |
|---|---|
| `dgeba-oligomer-eew-series-v1` | `EEW(n) = (M0 + n*Mr)/2 = 170.21 + 142.18 n` |
| `dgeba-oligomer-hydroxyl-value-v1` | `OHV(n) = 56100 n / (M0 + n*Mr)` |

Both were established on **pure single-n oligomers**. A real resin is never a pure
oligomer — it is a polydisperse mixture, and the module's shipped inference inverts a
measured commercial **EEW band into a number-average advancement `n_bar`**. Two things
had never been tested:

* **Q1 — invariance.** Is that inversion a property of the *mixture*, or only of a
  hypothetical single oligomer? Do two resins with the same `n_bar` but very different
  dispersity read the same EEW and the same OHV?
* **Q2 — robustness.** Commercial DGEBA carries non-ideal end groups (α-glycol ends from
  epoxide hydrolysis, chlorohydrin ends from residual bound chlorine; Lee & Neville 1967).
  Does the inversion survive them?

## Results

**G1 — cross-receipt parity + identity closure (PASS).** The four structural constants and
three OHV values already signed by the two prior receipts are re-derived independently and
match to ≤5e-4 (7/7 rows).

**G2 — polydispersity invariance: EXACT (PASS).** Every ideal linear DGEBA oligomer
contributes *exactly* 2 epoxide equivalents and *exactly* `n` hydroxyl equivalents, and mass
is additive, so both titrations are ratios of number-averages of quantities **linear in n**.
Both therefore depend on the distribution **only through its first moment `<n>`** — no
Jensen gap, no dispersity term. Verified on Flory-1936 most-probable, Poisson, and
adversarial bimodal (`n=0` with `n=8/12/40`) mixtures at three commercial advancement levels:
across a dispersity span of up to **6.77×** at matched `<n>`, the mixture EEW spread is
**exactly 0.000 g/eq** and every deviation from the single-oligomer formula and from the
shipped `n_bar` inversion is `<1e-9`. *The shipped inversion is a genuine mixture property —
strictly stronger than what the two prior receipts supported.*

**G3 — cross-titration identity, and H0 REFUTED.** Eliminating `<n>` between the two
titrations gives a **zero-parameter identity between two independent ASTM methods**:

```
OHV = A * (1 - E0/EEW),   A = 56100/Mr = 197.2874 mg KOH/g,   E0 = M0/2 = 170.2095 g/eq
```

Both constants are inherited from the prior signed receipts — nothing is fitted. It closes
on the pure-oligomer series to `<1e-12` mg KOH/g over `n=0..20`.

> **H0**: this identity is robust to realistic end-group defects (≤1% relative residual up
> to 5 mol% α-glycol / chlorohydrin ends). → **REFUTED.**

12 of 16 defect rows at ≥1 mol% breach the 1% bar, worst case **41.02%** relative. The
residual is strictly monotone in defect load, and zero-defect rows sit on the identity to
`<1e-9` (perfect specificity). The same defects bias the shipped `n_bar` inversion **upward
by up to 30.2% relative**. The residual is thus not noise — it is a zero-parameter
**detector** of non-ideal DGEBA.

**The breach is not uniform, and that is the second finding.** Relative detector power falls
**17.25×** from liquid to semisolid grade, because the defect hydroxyl rides on an
ever-larger ideal-backbone hydroxyl baseline:

| grade | `<n>` | ideal OHV (mg KOH/g) | rows breaching | residual per mol% glycol |
|---|---|---|---|---|
| liquid (Epon 828 / DER 331 class) | 0.13 | 19.33 | 8/8 | 9.79% |
| semisolid (Epon 1001F / DER 671 class) | 2.35 | 130.70 | 4/8 | 0.57% |

⇒ **A single fixed relative acceptance bar is NOT a valid QC rule across the DGEBA grade
range.**

**G4 — sensitivity and specificity (PASS).** Sensitivity `dΔ/dφ` = 1.99 (liquid) / 0.74
(semisolid) mg KOH/g per mol% α-glycol. Specificity 4/4: an ideal Flory resin is correctly
*not* flagged, while 20 mol% phenyl glycidyl ether diluent (+15.67%), 10 mol% free
bisphenol-A (+60.68%) and 5 mol% fully hydrolyzed DGEBA diol (+70.54%) are all correctly
flagged. The smallest refuting residual exceeds IUPAC-2021 atomic-weight uncertainty on the
identity constant by **15.1×** — the signal is chemical, not numerical.

## Ceiling / what this does NOT claim

The theorem and the identity are exact consequences of ideal linear DGEBA stoichiometry,
verified numerically rather than fitted. But they are validated against **synthetic**
distributions and **synthetic** defect loadings, **not** against measured ASTM D1652/D4274
pairs on real resin lots. The module holds no rights-clean paired-titration dataset, so the
detector's real-world false-positive rate is **UNMEASURED**, and the parametric detection
floors (0.9–7.9 mol% glycol, depending on grade and on an assumed 0.5–2% relative titration
precision) rest on **assumed** precisions chosen by this audit — **not** on quoted ASTM
repeatability statements. No exact EEW/OHV is asserted for any named commercial grade; no
product qualification, no cure-state claim. Live runtime stays `LOCKED_INTERNAL`;
`commercial_product_claim_locked=true` is unchanged.

## Reproduce

```sh
cd /home/ubuntu/amphora/build/mvp20-split
B=amphora-molecule-property/benchmarks/dgeba-polydispersity-cross-titration-v1
python3 $B/compute_dgeba_xtitration.py > /tmp/a.json
python3 $B/compute_dgeba_xtitration.py > /tmp/b.json
cmp /tmp/a.json /tmp/b.json          # two-replay byte-stability gate
python3 $B/sign_dgeba_xtitration.py  # DSSE PAE + Ed25519, AUDIT_ONLY key
```

Deterministic: closed-form distributions, no RNG, no timestamps, no network.

## Primary sources

* Flory, P. J., *J. Am. Chem. Soc.* **58**(10):1877–1885 (1936), doi:10.1021/ja01301a016 —
  most-probable distribution `x_n = (1-p) p^n`.
* Lee, H. & Neville, K., *Handbook of Epoxy Resins*, McGraw-Hill 1967 — DGEBA advancement
  series; hydrolysis and bound-chlorine end groups of epichlorohydrin-route resins.
* May, C. A. (ed.), *Epoxy Resins: Chemistry and Technology*, 2nd ed., Marcel Dekker 1988,
  ISBN 0-8247-7690-9.
* ASTM D1652 (epoxy equivalent weight by titration); ASTM D4274 (hydroxyl number, 56100
  factor).
* Prohaska et al., *Pure Appl. Chem.* **94**(5):573 (2022), doi:10.1515/pac-2019-0603 —
  IUPAC 2021 standard atomic weights.
