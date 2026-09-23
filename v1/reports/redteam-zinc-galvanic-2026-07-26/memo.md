# Red-team memo — Phase-0 truth + zinc sacrificial axis opened (2026-07-26, final pre-founder run)

## 1. The "FULL Phase-0" claim is FALSE (re-refuted live)
Computed live from `module-manifest.json` this run:
- scientific_readiness histogram = **{UNVALIDATED: 29}** — **0 / 29 VALIDATED**.
- **0 / 29 ranking_eligible**.
- Master manifest steady at **66 receipts / 11 modules** (mtime 2026-07-24, untouched).

Phase-0 as reported by front-matter is a **governance state**, not validated science.
No module is autonomously promotable: promotion requires two trust-anchored human
phase-0 key signatures, which the LOCAL_DEVELOPMENT_AUDIT_ONLY key cannot supply.
Where real externally-validated science DOES exist (solvency BigSolDB group-safe
RMSE 0.877; ~18 molecule-property GC predictors validated on public NIST data,
MAPE 0.1–3%), the modules still read UNVALIDATED **only** because of that human-sig
gate — an organizational step, not a scientific deficiency. That is the honest
framing for the founder report.

## 2. New MECHANISM axis opened & signed: zinc-rich sacrificial (galvanic) protection
A prior cron run this hour had **computed but never signed** a genuinely new axis.
grep of all 66 receipts + prior AUDIT axes for zinc|galvan|percol|cathod|sacrific
= **ZERO hits**. Every prior axis models the BARRIER mechanism (transport/FFV/
tortuosity/permeance/uptake/adhesion/Tg/cure/CTE/formulation). Zinc-rich epoxy
primer **sacrificial cathodic protection** (SSPC-Paint 20 / ISO 12944-5) is the
single largest previously-missing marine anti-corrosion mechanism.

**Theory, zero fitted params** (public-domain constants only):
- Galvanic driving force dE0 = E0(Fe2+/Fe) − E0(Zn2+/Zn) = **0.3148 V > 0** ⇒ Zn protects Fe.
- Faraday anode capacity zF/M_Zn = **819.868 Ah/kg** (cited 820, +0.016%).
- Continuum percolation φc = 1 − exp(−η_c), η_c = 0.3418 (Rintoul-Torquato 1997) ⇒ **φc = 0.2895** ⇒ ~70.8 wt% Zn floor.
- wt↔vol identity invertible; cathodic-protection criterion −0.80 V vs Ag/AgCl (NACE SP0169 / ISO 15589).

**Known-answer battery 11/11 PASS** (6 Tier-A exact identities + 5 Tier-B consistency anchors).
**Reproducibility:** two-replay SHA gate PASS + independent 3rd replay, all byte-identical
`ed7f573e…`. **DSSE Ed25519 VERIFY = PASS** (key local-9028773f, AUDIT_ONLY).

## 3. Red-team caveat I attached to the receipt (do not overstate)
The per-candidate binary percolation label (e.g. 60 wt% ⇒ "BARRIER_ONLY_below_percolation")
is **model-sensitive**: overlapping-sphere φc=0.2895 is one estimate; real conductive-filler
onset can be lower (Scher-Zallen ~0.16; flake/lamellar zinc lower still via aspect ratio).
**DEFENDED:** thermodynamic feasibility, galvanic ordering, the 70.8 wt% floor sitting
below the 80–92 wt% marine spec window, and the exact areal-capacity arithmetic.
**NOT defended:** on/off sacrificial status at loadings near threshold (needs measured
film conductivity / galvanic current ⇒ measurement/data-rights blocked).

## 4. What this does NOT do
- Does NOT promote amphora-barrier-corrosion-score (or anything) to VALIDATED.
- Does NOT change the manifest (still 66 / 11).
- Does NOT modify the shipped Rust engine or any of the 66 signed receipts.

## Verdict
Honest completion of a prior half-finished run: a real, novel, fully-verified marine
sacrificial-protection engine signed AUDIT_ONLY. Ready for human phase-0 sign-off; the
percolation point-classifier needs measured conductivity data before it can be a
point-predictor rather than a screening floor.
