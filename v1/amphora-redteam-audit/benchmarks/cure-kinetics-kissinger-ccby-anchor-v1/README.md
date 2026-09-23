# CC-BY cure-kinetics Kissinger anchor — rights-clean, in-scope, signed

**Date:** 2026-07-25 · **Host:** canonical tree only (`ssh xbabe2:/home/ubuntu/amphora/build/mvp20-split`)
**Authority:** AUDIT_ONLY. Promotes nothing. No existing receipt or manifest changed (still 66 / 11).
**Target module:** `amphora-cure-potlife-gate` (the strongest SECOND science candidate).

## Why this exists — the real wall is DATA RIGHTS, not science or signatures
`amphora-cure-potlife-gate/evidence/phase0/sources/source-lock.v2.json` shows
`rights_gate_passed: false` and `eligible_sources: []`. Every in-tree cure source
(`config/program/cure-sources.v1.json`) is a **QUARANTINED vendor TDS** with
`eligible_for_derivatives:false` and `chemistry_complete_rows:0`. So the module's
"all six gates pass" KPI is computed on **rights-quarantined** data.

> **Correction to the record:** the prior `redteam-cure-potlife-2026-07-25` memo
> stated cure-potlife is "blocked ONLY by the two trust-anchored signatures … not a
> data … gap." That is **overstated**. Signatures are a *second* gate; the *first*,
> currently-failing gate is `rights_gate_passed=false` with **zero eligible rows**.
> Do not tell founders cure-potlife is "Phase-0-ready awaiting only signatures."

This artifact takes the first concrete step across that wall: it acquires a
**genuinely rights-clean, in-scope, provenance-complete** cure-kinetics dataset and
validates a first-principles estimator on it.

## Data (CC-BY-4.0, DERIVATIVE_ALLOWED)
Lascano, Quiles-Carrillo, Balart, Boronat, Montanes. *Kinetic Analysis of the Curing
of a Partially Biobased Epoxy Resin Using Dynamic DSC.* Polymers 2019, 11(3), 391.
doi:10.3390/polym11030391 (PMC6473346). DGEBA-based epoxy (Resoltech 1070 ECO) +
cycloaliphatic amine **IPDA** (Resoltech 1074 ECO; active = 3-aminomethyl-3,5,5-
trimethylcyclohexylamine). Raw `(heating_rate β, peak temperature Tp)` from Table 3.
In-scope: two-part epoxy-amine, marine anti-corrosion cure physics.

## Theory — Kissinger (Anal. Chem. 1957, 29, 1702)
`ln(β/Tp²) = −Ea/(R·Tp) + ln(A·R/Ea)`. OLS of `ln(β/Tp²)` vs `1/Tp` → `Ea = −R·slope`.

## Result (recomputed on host, two-replay byte-identical)
| quantity | value |
|---|---|
| Kissinger Ea (recomputed from raw peaks) | **57.261 kJ/mol** |
| Paper's reported Kissinger Ea | 57.3 ± 3.1 kJ/mol |
| absolute recovery error | **0.039 kJ/mol** |
| Kissinger-plot R² | **0.9938** |
| regression SE of Ea (independent) | 3.20 kJ/mol (paper: 3.1) |
| iso-conversional envelope (KAS/FWO/Starink) | 59.8 / 62.8 / 60.0 kJ/mol |
| **all 8 pre-registered gates** | **PASS** |

**Non-circularity:** the estimator consumes ONLY the raw `(β, Tp)` peaks; the paper's
Ea values are read as validation targets, never as inputs. Recovering both the value
(57.26 vs 57.3) and the uncertainty (3.20 vs 3.1) from the peaks is genuine method
fidelity. Kissinger sits at the low edge of the iso-conversional envelope, exactly as
physics predicts (peak-only Kissinger underestimates conversion-averaged Ea).

**Honest limitations:** single formulation, single lab; leave-one-heating-rate-out
spread is 10.1 kJ/mol (n=4 endpoint leverage — reported, not hard-gated); this is the
DSC **reaction** Ea, which is higher than the gel/**pot-life** apparent Ea the
cure-potlife KPI ultimately needs.

## What it does / does not do
- **Does:** establish the first rights-clean, in-scope kinetics anchor (cycloaliphatic-
  amine class) with full CC-BY provenance + a signed, two-replay-gated receipt.
- **Does NOT:** promote cure-potlife; flip `rights_gate_passed` (that needs the source
  ingested through the module source-ledger under a signed rights receipt); sign a
  trust-anchored phase0 receipt; assert wet-lab measurement or superiority.

## Artifacts (this dir)
- `dataset.ccby.json` — raw CC-BY data + full rights provenance (sha in receipt)
- `cure_kinetics_kissinger_audit.py` — deterministic estimator + gates
- `diagnostic.canonical.json` == `diagnostic.runB.json`, sha `766020e0…` (two-replay PASS)
- `replay_receipt.v1.dsse.json` — DSSE Ed25519, key `local-9028773f…`
  (LOCAL_DEVELOPMENT_AUDIT_ONLY, **not** trust-anchored), SIGNATURE_VERIFY = PASS

## Founder one-liner
"We broke ground on the cure-potlife data-rights wall: a CC-BY, in-scope DGEBA+IPDA
DSC dataset now reproduces the published Kissinger activation energy to 0.04 kJ/mol
(R²=0.994) under a signed, two-replay-gated receipt — the first rights-clean kinetics
anchor for that module. Full promotion still needs the source ledgered under a rights
receipt plus the dual-signature ceremony."
