# Red-team memo — "full Phase 0" is false; new rights-clean cure-kinetics anchor signed

**Date:** 2026-07-25 (final cron pass before founder report) · **Host:** canonical `xbabe2:/home/ubuntu/amphora/build/mvp20-split`
**Authority:** AUDIT_ONLY. 66 signed receipts and the manifest are unchanged. xbabe1 tree untouched.

## 1. Verdict on "do we have full Phase 0" — NO
`config/program/phase0-decision-report.v2.json`: `status = EXECUTION_INCOMPLETE`,
`phase0_count = 10`, `pre_phase0_count = 19`, **`promotable = false` for all 29**.

Of the 10 PHASE_0: **9 are infrastructure / trust-kernel / deterministic-control**
(scientific_readiness `NOT_APPLICABLE`) and **1 is a real science module — solvency**
(`LOCKED_INTERNAL`, evaluation + independent review both trust-anchored-signed).
Every other science module — barrier-corrosion, cure-potlife, viscosity,
molecule-property/novelty/generator/role-ranker, design-rule, public-corrosion,
ingredient-library — is **PRE_PHASE_0 / UNVALIDATED**. The old "16" headline is stale
(7 of those badges fail re-verification today from post-signing benchmark drift).

**Honest headline: 10 Phase-0 = 9 infra + solvency. Solvency is the only validated
science capability. Not "full Phase 0."**

## 2. Correction to the record — cure-potlife is DATA-RIGHTS-blocked, not "awaiting only signatures"
The earlier `redteam-cure-potlife-2026-07-25` memo said cure-potlife is "blocked ONLY
by the two trust-anchored signatures … not a data … gap." **Re-verified on host this
run: that is overstated.**
`amphora-cure-potlife-gate/evidence/phase0/sources/source-lock.v2.json` →
`rights_gate_passed: false`, `eligible_sources: []`. All three cure sources in
`config/program/cure-sources.v1.json` are **QUARANTINED** vendor TDS
(`eligible_for_derivatives:false`, `chemistry_complete_rows:0`). The KPI's "6/6 gates
pass" is computed on **rights-quarantined** data. Founders must NOT be told
cure-potlife is "Phase-0-ready awaiting only signatures." The first failing gate is
**data rights**.

## 3. New this run — first rights-clean, in-scope cure-kinetics anchor (signed)
`amphora-redteam-audit/benchmarks/cure-kinetics-kissinger-ccby-anchor-v1/`

- **Data:** CC-BY-4.0, DERIVATIVE_ALLOWED — Lascano et al., *Polymers* 2019, 11(3), 391,
  doi:10.3390/polym11030391 (PMC6473346). DGEBA epoxy + cycloaliphatic amine **IPDA**.
  In-scope, full provenance (DOI, license, attribution, sha256).
- **Theory:** Kissinger (1957) `ln(β/Tp²) = −Ea/(R·Tp) + …`, `Ea = −R·slope`.
- **Result (recomputed on host, non-circular):** Kissinger **Ea = 57.261 kJ/mol** vs the
  paper's reported **57.3 ± 3.1** — recovery error **0.039 kJ/mol**, **R² = 0.9938**,
  independent regression SE **3.20** (paper 3.1). Sits at the low edge of the
  iso-conversional envelope (KAS/FWO/Starink 59.8–62.8) exactly as physics predicts.
- **8/8 pre-registered gates PASS**; two-replay SHA `766020e0…` byte-identical; DSSE
  Ed25519 signed (local audit key `local-9028773f…`, **not** trust-anchored),
  SIGNATURE_VERIFY = PASS.
- **Honest limits:** single formulation/lab; LOO(heating-rate) spread 10.1 kJ/mol (n=4
  endpoint leverage); this is the **reaction** Ea, higher than the gel/**pot-life**
  apparent Ea the KPI ultimately needs.

This is the first concrete step across the cure-potlife data-rights wall: it proves the
wall is "not yet acquired," not "does not exist," and that acquired open data
reproduces first-principles cure kinetics under a signed, replayable receipt.

## 4. What it deliberately does NOT do (authority ceilings sacred)
Does not promote cure-potlife; does not flip `rights_gate_passed` (needs the source
ingested through the module source-ledger under a signed rights receipt); does not sign
a trust-anchored phase0 receipt (dual-identity ceremony is above a cron's authority);
does not touch the 66 receipts/manifest.

## 5. Honest next steps to a real SECOND science Phase-0 (cure-potlife)
1. Ledger this CC-BY source through `amphora-source-ledger` with a signed rights receipt →
   flips `rights_gate_passed` toward true with real provenance.
2. Acquire ≥2 more rights-clean multi-temperature gel/pot-life series (open CC-BY DSC/
   rheology) so the pot-life gate rests on rights-clean rows, not quarantined TDS.
3. Run the dual-identity evaluate/review ceremony (keys present & verified) — a
   governance decision, not a science or key gap.
