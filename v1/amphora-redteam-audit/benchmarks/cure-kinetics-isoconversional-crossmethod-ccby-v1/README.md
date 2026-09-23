# cure-kinetics-isoconversional-crossmethod-ccby-v1

**AUDIT_ONLY red-team science increment. Promotes nothing. Manifest stays 66/11.**
Signed with `local-9028773f49591193` (`LOCAL_DEVELOPMENT_AUDIT_ONLY`, **not**
trust-anchored in the phase0 store).

## Red-team headline (the founder's actual question)

Recomputed live from `module-manifest.json` this run
(`module_manifest_sha256` recorded in the receipt):

> **"FULL Phase-0" is FALSE. 0 of 29 modules have `scientific_readiness=VALIDATED`
> (histogram: `{UNVALIDATED: 29}`).**

Phase-0 here is a **governance** gate, not a validated-science milestone:
`scientific_success_required_for_phase0 = false`, and promotion is blocked on two
human trust-anchored signatures (`EVALUATOR_SIGNATURE`,
`INDEPENDENT_REVIEW_SIGNATURE`) with `local_development_keys_authorized = false`.
Even the strongest module (`amphora-solvency-score`) only *targets*
`LOCKED_INTERNAL`, not `VALIDATED`. **The founder's skepticism is correct — no
module is autonomously promotable, and none is scientifically VALIDATED today.**

## What this artifact adds (real, non-circular science)

The portfolio's cure-kinetics evidence rested on a **single** estimator
(Kissinger). A red-teamer's first objection is method dependence. This artifact
recovers the cure activation energy `Ea` from the SAME rights-clean raw DSC peaks
with **three independent peak-based isoconversional estimators** and quantifies
both their accuracy against a first-principles ground truth and their mutual
agreement on real epoxy-amine data.

| Method | Model | Ea from |
|---|---|---|
| Kissinger (1957) | `ln(β/Tp²) = C − Ea/(R·Tp)` | `−R·slope` |
| Ozawa–Flynn–Wall / Doyle (ASTM E698 basis) | `ln(β) = C − 1.0516·Ea/(R·Tp)` | `−R·slope/1.0516` |
| Starink (2003, most-accurate linear form) | `ln(β/Tp^1.92) = C − 1.0008·Ea/(R·Tp)` | `−R·slope/1.0008` |

## Data (all CC-BY-4.0, commercial + derivative use permitted)

Byte-identical reuse of the rights-clean multi-system table from
`cure-kinetics-kissinger-multisystem-ccby-v1` (`dataset_sha256`
`f84076b5…302846d8`). No source re-fetch, no transcription.

* **CORE (DGEBA + amine, in scope):** DGEBA+IPDA (Lascano, *Polymers* 2019,
  10.3390/polym11030391); DGEBA/BDGE+IPDA prepreg (*Materials* 2021,
  10.3390/ma14164673).
* **GENERALIZATION (non-DGEBA epoxy-amine, reported, excluded from core KPI):**
  multifunctional epoxy+DDS (*Molecules* 2026, 10.3390/molecules31040640).

## Results

**First-principles known answer** (synthetic first-order DSC peaks, ground-truth
`Ea = 60.0 kJ/mol`):

| Method | Recovered Ea | abs err |
|---|---|---|
| Kissinger | 60.000001 | 0.000001 |
| Starink | 60.100403 | 0.100403 |
| OFW/Doyle | 60.585829 | 0.585829 |

Kissinger is exact by construction; Starink recovers to <0.11 kJ/mol; OFW/Doyle
shows the expected small **positive** bias — reproducing the textbook accuracy
ordering **Starink > OFW/Doyle**, not a fitted result.

**Real epoxy-amine data** (three independent labs/DOIs):

| System | Kissinger | OFW | Starink | spread | reported Kiss. |
|---|---|---|---|---|---|
| DGEBA+IPDA | 57.26 | 60.30 | 57.46 | 3.04 | 57.3 |
| DGEBA/BDGE+IPDA | 68.55 | 71.86 | 68.78 | 3.31 | 69.95 |
| multifunc.+DDS *(gen)* | 63.66 | 68.18 | 63.93 | 4.53 | 64.69 |

All 9 gates pass (`CROSS_METHOD_ROBUST__KNOWN_ANSWER_PASS`): core cross-method
spread ≤ 3.31 kJ/mol, every fit R² ≥ 0.987, Kissinger reproduces each paper's
reported value to ≤ 2 kJ/mol, all Ea in the 40–90 kJ/mol amine-cured-epoxy band.
**The recovered cure Ea is a property of the data, not of one linear model.**

## Honest scope — what this does NOT do

- Does **not** promote `amphora-cure-potlife-gate` to PHASE_0 (needs two
  trust-anchored human signatures + each source ingested through the module
  source-ledger under a signed rights receipt to flip `rights_gate_passed`).
- Does **not** change the Phase-0 count or `n_receipts_indexed` (still 66/11).
- Peak (reaction) `Ea` ≠ gel/pot-life apparent `Ea`; isothermal ambient marine
  cure is water-catalysed vs non-isothermal DSC. This benchmark hardens the
  kinetics *basis*, it does not close the pot-life KPI.
- Asserts no Amphora wet-lab measurement, product qualification, or superiority.

## Reproduce

    python3 isoconversional_crossmethod_audit.py > /tmp/out.json   # diagnostic
    # two-replay: byte-identical SHA-256 = 5563a2d0…dad3d0ff
    python3 sign_crossmethod.py                                    # DSSE Ed25519, AUDIT_ONLY
    # receipt_body_sha256 = 01d6e8e9…aca1dfa5 ; DSSE_VERIFY = PASS
