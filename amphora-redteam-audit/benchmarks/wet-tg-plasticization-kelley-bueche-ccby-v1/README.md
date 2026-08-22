# wet-tg-plasticization-kelley-bueche-ccby-v1 (AUDIT_ONLY)

**Gap opened:** water-plasticization of the cured barrier film — the wet (water-saturated)
glass-transition temperature. Seawater absorbed by a marine epoxy lowers the network Tg,
softening the film and accelerating osmotic blistering / cathodic disbondment. This is the
#1 marine barrier-degradation mechanism and was **not modelled anywhere** in the 66-receipt
portfolio: every prior Tg receipt is *dry*-network Tg.

## What this increment does
- **Theory:** Fox (1956, mass-fraction) and Kelley–Bueche (1961, free-volume) polymer–diluent
  Tg models, with absorbed water as the plasticizing diluent; literature water Tg (glassy 136 K,
  liquid-like 277 K). No parameter is fitted to the measured wet Tg.
- **Data (rights-clean, in-scope):** Gibhardt, Buggisch, Meyer, Fiedler, *Front. Mater.*
  9:826076 (2022), **CC-BY-4.0**. Two-part amine-cured DGEBA infusion resin
  (RIMR 135 = DGEBA+HDDGE; RIMH 137 = polyoxypropylene diamine + IPDA). Text-stated:
  dry Tg **89.4 °C**, equilibrium uptake **~3.0 wt%**, water-saturated Tg **61.5–66.5 °C**
  → measured depression **22.9–27.9 °C** at 3 wt% water.

## Result (honest, non-circular)
- **DIRECTION_VALIDATED:** every engine predicts the correct Tg *drop*.
- **PARAMETER_FREE_MAGNITUDE_REFUTED:** the best naive prediction (Fox, glassy water)
  gives only **17.3 °C** depression vs the measured **22.9–27.9 °C** — naive a-priori
  under-predicts by ~1.5×–8×. The Tg_water that Fox *would* need is **~103 K**, below even
  the glassy-water convention: absorbed water plasticizes this amine-epoxy **more strongly**
  than a generic free-volume diluent (H-bond-network disruption / bound & clustered water).
- **Trustworthy output = the empirical plasticization slope ≈ 8.5 °C per wt% water**
  (measured band 7.6–9.3), consistent with the literature 5–10 °C/wt% range. Marine wet-Tg
  risk must be assessed with this empirical coefficient, **not** the naive Fox/KB magnitude.

## Non-circularity
Parameter-free predictions consume only (dry Tg, water mass fraction, literature Tg_water,
densities). The measured wet Tg is never an input — the refutation is genuine.

## Authority ceiling
AUDIT_ONLY. Promotes nothing; signs no trust-anchored phase0 receipt; modifies none of the
66 signed receipts or the manifest; Phase-0 count unchanged (10). Phase-0 remains a
**governance** state — re-verified this run: all 29 benchmark-locks carry
`scientific_success_required_for_phase0=false`, 0/29 modules `scientific_readiness=VALIDATED`.

## Files
- `wet_tg_plasticization_audit.py` — deterministic harness (embeds all inputs)
- `diagnostic.canonical.json` / `diagnostic.runB.json` — two-replay, byte-identical
- `replay_receipt.v1.dsse.json` — DSSE Ed25519, local AUDIT_ONLY key
