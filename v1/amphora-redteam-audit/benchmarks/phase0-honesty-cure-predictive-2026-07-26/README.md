# Red-team memo — "FULL Phase-0" claim + one honest new increment (2026-07-26)

**Authority:** AUDIT_ONLY. Promotes nothing. Modifies no existing receipt. Manifest
stays 66 receipts / 11 modules. Signed DSSE Ed25519, two-replay SHA-256 gate PASS.
Diagnostic SHA `ab123d5d...`, receipt SHA `9ac1a12e...`.

## 1. The founder is right — we do NOT have "full Phase-0" (validated science)

Live-reproduced this run directly from every amphora-*/docs/capability-profile.json:

| scientific_readiness | count | phase | count |
|---|---|---|---|
| VALIDATED | **0** | PHASE_0 | 17 |
| LOCKED_INTERNAL | 4 | PRE_PHASE_0 | 12 |
| NOT_APPLICABLE | 13 | | |
| UNVALIDATED | 12 | | |

**Zero of 29 modules carry scientific_readiness == VALIDATED.** The "17 PHASE_0"
figure is a *governance* lifecycle lock (folder-confinement, two-replay, signatures,
supersession) = 4 LOCKED_INTERNAL + 13 NOT_APPLICABLE. It is **not** a certificate of
externally-validated science. Report language should say "17 modules cleared the
Phase-0 *governance* gate; 0 are scientifically VALIDATED," not "full Phase-0."

## 2. Data-provenance re-verification (integrity hardening)

Re-read the CC-BY-4.0 full text of the two most load-bearing rights-clean datasets
from PubMed Central this run and checked every number against the signed in-tree
values — **both match exactly**:

- Lascano DGEBA+IPDA cure peaks (PMC6473346, Table 3) -> in-tree cure-kinetics dataset OK
- DGEBA+{DDS,1,3-BAC,C8DA} pristine Tg (PMC10780492) -> v3 network-Tg source S2 OK

The load-bearing rights-clean data is traceable and un-drifted.

## 3. One genuinely-new, non-circular KPI banked

The existing Kissinger anchors validate Ea *recovery* (a descriptive fit). They do
**not** test whether the recovered kinetics *predict a held-out observable*. Added:

- First-principles Kissinger on PMC-verified peaks: **Ea = 57.261 kJ/mol** vs reported
  57.3 (err 0.039, R2=0.994) — non-circular, reproduces the prior signed anchor.
- **Leave-one-heating-rate-out predictive peak-temperature forecast: MAE = 2.25 K,
  max 3.91 K** (refit Kissinger on 3 peaks, solve for the held-out beta's peak T). A real
  predicted-vs-measured observable. *Honestly labelled:* the 4 points are near-collinear,
  so this is a self-consistency floor, not a strong independent test.
- Method ordering Kissinger(57.3) < FWO reproduced from the peaks (at-peak FWO 60.3).

## 4. Why nothing bigger was honestly achievable this run

- **Network-Tg (highest-value gap):** blocked on n>=12 unique rights-clean
  stoichiometric-full-cure DGEBA+amine Tg systems; only 7 are page-verified. Crossing
  the count gate autonomously would require stitching heterogeneously-cured values from
  assorted sources — **gaming the gate**, and v2 already showed heterogeneous data
  *refutes* the structure-only model. **Declined and logged, not faked.**
- **Cure-potlife deployment KPI:** needs an independent *isothermal* gel-time/pot-life
  measurement to validate the Arrhenius extrapolation non-circularly. None in-tree.
- **Isoconversional Ea(alpha):** Lascano reports Ea(alpha) only as a figure; no tabulated
  T_alpha. Figure digitisation is not founder-grade. Blocked on data.
- **Adhesion / barrier-corrosion:** need rights-clean contact-angle / measured-EIS data
  (the data-rights wall). Blocked on data.
- **Solvent-property suite:** COMPLETE (a-priori Tb, dHvap, Pvap/VOC, flash/GHS, RI,
  surface tension, molar volume, Hildebrand delta, Hansen vector) — no open honest gap.

**Bottom line for the report:** the honest state is "strong governance + a broad,
non-circular a-priori *solvent*-property suite + one rights-clean cure-kinetics anchor
now with a predictive KPI; zero scientifically-VALIDATED modules." The binding
constraint on every remaining high-value coating property (Tg, pot-life, adhesion,
barrier) is **acquisition of rights-clean, in-scope, homogeneous measured data**, not
theory or method.
