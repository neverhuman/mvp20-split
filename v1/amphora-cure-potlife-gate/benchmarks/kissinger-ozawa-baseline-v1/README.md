# kissinger-ozawa-baseline-v1 — ported hardest-defensible baseline, honest head-to-head

**AUDIT_ONLY red-team science increment. Promotes nothing. Manifest stays untouched.**
Signed with the AUDIT_ONLY use of the `PHASE0_EVALUATOR` seed key (pinned in
`config/phase0-trust-store.v1.json`), NOT as a phase0 evaluation/review signature —
same pattern as the module's other `evidence/audit/*` receipts.

**Campaign item:** C5 ("Kissinger/Ozawa baseline port + rights-integrity note"), attack (A).

## Why this exists

The founder demanded the hardest defensible baseline for pot-life temperature
correction. It already exists, signed, in the frozen physics workshop:
`amphora-redteam-audit/benchmarks/cure-kinetics-kissinger-ccby-anchor-v1/`,
`cure-kinetics-kissinger-multisystem-ccby-v1/`, and
`cure-kinetics-isoconversional-crossmethod-ccby-v1/` — three independent
peak-based isoconversional estimators (Kissinger 1957, Ozawa-Flynn-Wall/Doyle,
Starink 2003) recovering activation energy `Ea` from genuinely rights-clean
(CC-BY-4.0), non-circular, raw `(heating_rate, peak_temperature)` DSC data. This
artifact **ports** that estimator + dataset (byte-identical copy, math
re-derived not re-fetched) into `amphora-cure-potlife-gate` and runs it
head-to-head against the currently-cited published-Ea Arrhenius approach.

## Claim under attack

`amphora-cure-potlife-gate/evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json`:
"Arrhenius with published Ea (MAPE 14.7%, lift 0.805 over constant-mean) is the
strongest defensible temperature-correction for pot-life."

## Falsification criterion (pre-registered)

REFUTED if any CC-BY-derived reaction-Ea (Kissinger / OFW-Doyle / Starink),
substituted into the *identical* Arrhenius pot-life formula for the one
chemistry-matched system, breaches the module's own pre-registered
`held_out_temperature_extrapolation_mape_ceiling=0.25` or per-point worst-case
0.40. SURVIVED if all three stay within both ceilings.

## Chemistry match

Only 1 of the 12 systems in the signed KPI has an exact chemistry match to a
CC-BY dataset: `dgeba-ipda` (fixture; Ea=62.0 kJ/mol, Blanco et al. Polymer
46:7989 (2005); pot-life source Huntsman Araldite GY 6010 + HY 2954 (IPDA) TDS)
vs `dgeba-ipda-lascano-polym11030391` (CC-BY; Lascano et al., Polymers 2019,
10.3390/polym11030391, PMC6473346, Resoltech 1074 ECO IPDA). Both are DGEBA +
isophorone diamine (cycloaliphatic). **Confound noted, not hidden:** different
manufacturers' commercial IPDA hardener packages — a generic chemistry match,
not proof of identical formulation/stoichiometry/catalyst.

## Result

| Ea source | Ea (kJ/mol) | held-out MAPE (10/30/40°C) | worst-case point |
|---|---|---|---|
| **current cited (Blanco 2005)** | 62.00 | **13.33%** | 21.01% |
| Kissinger (CC-BY, Lascano raw peaks) | 57.26 | 9.32% | 12.19% |
| Ozawa-Flynn-Wall/Doyle (CC-BY) | 60.30 | 10.77% | 17.95% |
| Starink (CC-BY) | 57.46 | 9.39% | 12.58% |

All three independently-reproducible reaction-Ea estimates stay comfortably
within the module's own ceilings (0.25 / 0.40) — **the attack did not breach
the falsification criterion. Verdict: `CLAIM_SURVIVED__NO_CEILING_BREACH`.**

## Honest, non-papered-over finding

All three alternative Ea sources *numerically outperform* the currently cited
literature Ea on this one held-out system (9.3–10.8% MAPE vs 13.3%). This does
NOT flip the aggregate 14.7%/36-point KPI (only 1/12 systems has an independent
cross-check; n=3 held-out points per Ea source is not statistically powered to
declare superiority) — but it is a real, reproducible observation and is
reported plainly rather than suppressed.

**Caveat-direction correction:** the campaign item's assumed caveat
("Kissinger recovers reaction Ea, higher than gel/pot-life Ea") is **reversed**
on this system — all three reaction-Ea estimates are 2.7–7.6% *lower* than the
cited pot-life Ea, not higher. Likely explanation: different commercial IPDA
hardener packages (see chemistry-match confound above), not a universal
violation of the reaction-Ea-vs-gel-Ea physics.

## Coverage gap (disclosed, not silently dropped)

Only 1 of 12 systems (8.3%) in the signed Arrhenius KPI has ANY
independently-reproducible, rights-clean raw-data Ea cross-check available
in-tree. The other 11 systems' Ea and TDS-sourced pot-life numbers remain
unverified against raw physical measurements.

## What this does NOT do

Does not recompute or change the signed KPI's 12-system/36-point aggregate
MAPE; does not establish statistical significance of the single-system MAPE
gap; does not promote `amphora-cure-potlife-gate` to PHASE_0; does not flip
`rights_gate_passed`; does not modify the signed Arrhenius KPI, the
known-answer fixture, the manifest, or any prior receipt.

## Files

- `dataset.multi.ccby.json` — byte-identical copy of the frozen CC-BY dataset (sha `f84076b5…`)
- `kissinger_ozawa_headtohead_audit.py` — deterministic ported estimator + head-to-head harness
- `diagnostic.canonical.json` == `diagnostic.runB.json` (two-replay PASS, sha `8799eec3…`)
- `kissinger-ozawa-baseline-headtohead-receipt.v1.dsse.json` — DSSE Ed25519, AUDIT_ONLY use of `PHASE0_EVALUATOR` key, SIGNATURE_VERIFY = PASS, key_id derives the pinned trust-store entry
- `sign_headtohead.py` — signing + self-verification

## Reproduce

    python3 kissinger_ozawa_headtohead_audit.py > /tmp/out.json   # diagnostic
    python3 sign_headtohead.py                                    # DSSE Ed25519, AUDIT_ONLY
