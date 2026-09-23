# network-tg-feasibility-v2 — expanded-data red-team CORRECTION (2026-07-25)

**Authority:** AUDIT_ONLY. Promotes nothing. Modifies none of the 66 signed
receipts, the manifest, or the signed `network-tg-feasibility-v1` audit. All work
on the canonical host (`xbabe2:/home/ubuntu/amphora/build/mvp20-split`).

## What this is
A red-team **correction** of the network-Tg feasibility claim for marine-coating
DGEBA + amine thermosets (target: `amphora-molecule-property` glass-transition
capability). v1 established the correct *qualitative* physics but, on only n=5
single-source cited Tg, reported optimistic numbers (ring-fraction Pearson
r=+0.69, LOO MAE ~24–29 °C) and framed the gap as "one rights-clean dataset away
from a KPI."

This run **genuinely acquires** additional rights-clean, individually-cited
experimental Tg from **3 independent sources** and re-tests the model.

## Data acquired this run (every value read from the actual source page)
- **S1** — C.A. May (ed.), *Epoxy Resins Chemistry & Technology* 2nd ed. 1988,
  Ch.6 (the v1 source; individual numeric facts, CC0 precedent). n=5: IPDA 158,
  m-XDA 100, DDS 220, TETA 120, DETA 115 °C.
- **S2** — *Polymers* 2024, 16(1), 67, doi:10.3390/polym16010067 (PMC10780492),
  **CC BY 4.0**; DSC 10 °C/min N₂, pristine (pre-UV), molar epoxy:NH₂ = 2:1
  (stoichiometric). n=3: DDS 200, 1,3-bis(aminomethyl)cyclohexane 97,
  octamethylenediamine 94 °C.
- **S3** — Savonnet et al. 2018, *ACS Sus. Chem. Eng.* 6 / arXiv:1911.08960,
  Table 1; DGEBA/DDS 204 °C. (MDVA, DMAN, TetraGEDVA systems **excluded** —
  no clear Tg / crude impaired stoichiometry / non-DGEBA epoxy.)

Result: **n=5 single-source → n=9 measurements / 7 unique systems / 4 amine
classes**, with **DGEBA/DDS triangulated across 3 independent labs (200/204/220 °C,
std 8.6 °C, range 20 °C)** — the inter-lab Tg floor now *measured*, not assumed.

## Finding (the correction)
Tested on the expanded, chemically-diverse, independent data, the v1 structure-only
physics model is **refuted**:

| model (structure-only, non-circular) | LOO MAE | vs baselines |
|---|---|---|
| ring-atom fraction | **40.5 °C** | worse than NULL |
| crosslink density + ring | 62.3 °C | worse |
| crosslink + ring + rotatable | 97.4 °C | worse |
| **NULL (predict mean Tg)** | **31.8 °C** | — |
| incumbent polyuniverse ML (signed receipt) | 39.1 °C | — |
| raw Van Krevelen (signed receipt) | 109.1 °C | — |

The best structure-only model (LOO 40.5 °C) is **worse than a trivial mean-Tg
baseline (31.8 °C)** and does **not** beat the incumbent ML (39.1 °C); it beats
only raw Van Krevelen. Leave-one-**source**-out generalization is 42.2 °C.

**Why it fails (from the data, not asserted):**
- **DDS** (aromatic-in-backbone) arom 0.71 → Tg 208; **m-XDA** (aromatic but
  CH₂-linked/pendant) arom 0.60 → Tg 100. Near-identical aromatic fraction,
  **108 °C apart** → whole-molecule aromatic/ring fraction can't tell backbone-rigid
  from pendant-rigid.
- **IPDA** ring 0.5 → 158; **1,3-BAC** ring 0.6 → 97 → ring fraction *anti-*predicts
  (IPDA rigidity is gem-dimethyl steric, not ring count; cyclohexane is a flexible
  chair).
- Crosslink density correlates **negatively** (r=−0.35): the highest-crosslink
  aliphatic polyamines (TETA/DETA) are only mid-Tg.

The v1 "r=+0.69" was a small-sample artifact of 5 homogeneous systems (ring
correlation falls to +0.46 on n=7).

## Verdict
`PRE_PHASE_0` — **network-Tg is FURTHER from Phase-0 than v1 implied.** A
trustworthy KPI needs a *topological backbone-rigidity-between-crosslinks*
descriptor (rigid-fragment fraction on the junction-to-junction path), validated on
n≥12 rights-clean systems. That is the concrete next step; it is not claimed here.
**Do not present the v1 headline to founders.**

## Files
- `network_tg_expanded_audit.py` — harness (rdkit, numpy). SHA in receipt.
- `diagnostic.canonical.json` / `diagnostic.runB.json` — byte-identical
  (`c4fe7cb3…`), two-replay gate PASS.
- `replay_receipt.v1.dsse.json` — DSSE Ed25519, signed with the
  LOCAL_DEVELOPMENT_AUDIT_ONLY key `local-9028773f…` (NOT a trust-anchored phase0
  key); signature verifies.
