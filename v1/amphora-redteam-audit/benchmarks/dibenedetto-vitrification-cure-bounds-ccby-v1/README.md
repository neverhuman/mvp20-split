# dibenedetto-vitrification-cure-bounds-ccby-v1

**AUDIT_ONLY red-team science increment. Promotes nothing. Manifest stays 66/11.**

## What this is

The first **cured-network** axis the portfolio validates against real measured
data (all prior anchors were solvent-property or bulk cure-kinetics). A
rights-clean, **a-priori, zero-free-parameter, non-circular** physical-bounds
test for the isothermal degree-of-cure `alpha(T_cure)` of a two-part
**DGEBA + m-xylylenediamine (mXDA)** epoxy-amine network.

Every measured conversion is required to lie inside the theoretical window:

    alpha_gel  <=  alpha_measured  <=  alpha_vitrification(T_cure)

* **Lower bound - Flory-Stockmayer gel conversion** (structure only):
  `alpha_gel = 1/sqrt((f-1)(g-1))` with DGEBA `f=2`, primary diamine mXDA `g=4`
  -> `alpha_gel = 1/sqrt(3) = 0.577`. A sample with a measurable Tg must be past gel.
* **Upper bound - DiBenedetto vitrification ceiling**: isothermal cure freezes
  when the advancing `Tg(alpha)` reaches `T_cure`; the ceiling is the `alpha` solving
  `Tg(alpha)=T_cure`, computed from three **a-priori DGEBA-amine constants fixed from
  independent literature and NOT tuned** to the data (`Tg0=-20 C`, `lambda=0.40`,
  matched-material `Tg_inf=69.95 C`).

**Marine relevance:** the vitrification ceiling is exactly the physics that caps
achievable cure of a two-part epoxy applied at **low ambient temperature** - the
decisive question for a cold-climate marine coating.

## Data (CC-BY-4.0)

Terenzi et al., *Nanomaterials* **2023**, 13(6), 1064 - PMC10054629 -
DOI `10.3390/nano13061064`. Table 1: residual-enthalpy conversion `alpha` at 7
isothermal cure temperatures (40-100 C); matched-material Tg (8.5 wt% AuNP
composite, postcured 130 C).

## Result

All 7 gates pass; `window_coverage_fraction = 1.0` (7/7).
G1 above gel floor; G2 below vitrification ceiling; G3 within window;
G4 robust across a-priori box (Tg0 in [-25,-15], lambda in [0.35,0.45]);
G5 vitrification branch (40/50/60 C) is a strict upper bound;
G6 gel floor below every ceiling; G7 non-trivial window width.

## Verdict - honest scope

`PHYSICAL_BOUNDS_CONSISTENT_NOT_A_POINT_PREDICTOR`.

Necessary-condition bound test, **not** a validated point predictor of `alpha`
or `Tg`. At 40-60 C measured conversion sits ~0.13 **below** the vitrification
ceiling: kinetically limited (finite 24 h cure), so vitrification is respected
but not the binding constraint there.

### Red-team trap avoided (documented so a future run cannot repeat it)

Pairing the **neat-resin** Tg_inf (~111-121 C) with the **8.5 wt% AuNP composite**
`alpha(T_cure)` table manufactures a spuriously tight point-prediction
(MAE ~0.03 alpha). That material-mismatch artifact is **rejected**; matched-material
Tg_inf=69.95 C is used, correctly yielding an upper-bound (not point) result.

### To unlock a real Tg(alpha) point-predictor KPI

Need a matched-material dataset with **Tg at >=4 partial conversions** plus
`dCp0/dCp_inf`. Not yet rights-cleared in-tree.

## Founder-relevant headline

Independently re-parsed all module mission front-matter this run:
**17 modules labelled `PHASE_0` = 13 `NOT_APPLICABLE` + 4 `LOCKED_INTERNAL`
+ 0 `VALIDATED`; 12 modules `PRE_PHASE_0`.** "FULL Phase-0" is a **governance**
milestone, not validated science. The founder's skepticism is correct.

## Reproduce

    python3 dibenedetto_vitrification_audit.py      # -> diagnostic.out.json
    # two-replay: rerun, byte-identical SHA-256 = 4cb48c67...57fa8105
    python3 sign_dibenedetto.py                     # DSSE Ed25519, local AUDIT_ONLY key

Signed with `local-9028773f49591193` (`LOCAL_DEVELOPMENT_AUDIT_ONLY`, **not**
trust-anchored in the phase0 store). Promotes nothing; modifies no existing
receipt or the manifest.
