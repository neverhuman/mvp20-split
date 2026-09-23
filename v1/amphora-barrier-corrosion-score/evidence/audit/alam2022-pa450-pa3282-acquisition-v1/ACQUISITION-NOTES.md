# C4 acquisition notes: alam2022_pa450_pa3282

**Campaign item:** C4 -- Third in-class EIS series hunt (literature bar 2/3)
**Claim attacked:** `corrosion_series.json` `systematic_search_ledger` exhaustiveness -- "no third
strictly in-class, open table-read, rights-clean epoxy-amine EIS ladder exists in the accessible
literature."
**Verdict: CLAIM_REFUTED.** A third series was found and hash-locked.

## What was found

Alam, Samad, Seikh, Mohammed, Al-Zahrani, Sherif. "Development and Characterization of PA 450 and
PA 3282 Epoxy Coatings as Anti-Corrosion Materials for Offshore Applications." *Materials (Basel)*
15(7):2562 (2022). DOI 10.3390/ma15072562. PMCID PMC8999854. PMID 35407894.

- **In-class:** DGEBA epoxy resin + polyaminoamine adduct (Aradur 450 BD, "PA-450") and
  polyamidoamine adduct (Aradur 3282 BD, "PA-3282") hardeners -- epoxy-polyamide, offshore/marine
  application, mild steel substrate.
- **Table-read:** Table 5 (PA-450 / E-series) and Table 6 (PA-3282 / F-series) report open numeric
  EIS equivalent-circuit fit parameters (RS, Q1, RP1, Q2, RP2) at 1h/7d/14d/21d/30d for three
  hardener-stoichiometry formulations per series (E-0/E-1/E-2 and F-0/F-1/F-2).
- **Ordered side-by-side ladder:** hardener stoichiometric ratio, with a non-monotonic (mid-point
  optimum) ranking claim made by the source authors and independently reproduced by both the
  E-series and F-series sub-ladders in the extracted data.
- **Rights-clean:** CC-BY-4.0, license text captured from two independent sources (PMC full-text
  HTML mirror and the Europe PMC `fullTextXML` REST endpoint), in full agreement. No retraction,
  erratum, or correction notice found.

This was **not** previously in `corrosion_series.json`'s 23-record set and was **not** surfaced by
the prior five-topic `systematic_search_ledger` sweep (epoxy-polyamide binder class; zinc phosphate
inhibitors; MIO/Al lamellar pigments/PVC-CPVC; EIS/salt-spray/disbonding/adhesion; shelf
stability). The prior ledger's exhaustiveness claim is therefore refuted.

## Search performed this fire

5 targeted queries against MDPI Coatings/Materials/Polymers, ACS Omega/AuthorChoice, RSC open
access, and Scientific Reports/Nature Comms coatings literature (2020-2026 window), ~33 records
screened. 5 near-misses were identified and rejected with reasons (see the
`systematic_search_ledger` entry appended to `corrosion_series.json` for the full list); notably
one candidate (PMC10173445, ACS Omega imidazolium-ionic-liquid epoxy hardener) was excluded
because it is a **retracted** article.

## Honest limitation (residual data ask, not a rights ask)

The numeric transcription of Table 5/Table 6 was produced by a single automated full-text read of
the PMC mirror (direct MDPI fetch returned HTTP 403 to automated access). It was **not**
independently double-keyed against the primary PDF by a second extraction pass. Internal-consistency
checks passed (all 30 CPE dispersion exponents fall in the physically valid [0,1] range; both
sub-ladders independently reproduce the authors' stated qualitative conclusion), but this is not a
substitute for manual verification. Filed as a residual data-quality ask in the signed receipt and
in the xbabe1 acquisition queue -- this is a same-asset spot-check ask, not a new rights-review ask
(license is already confirmed CC-BY-4.0 from two independent sources).

## What changed on disk

- `amphora-barrier-corrosion-score/reference/mvp20/data/literature_extractions/alam2022_pa450_pa3282.json`
  (new) -- full 2-hardener x 3-formulation x 5-timepoint extraction, hash-locked.
- `amphora-barrier-corrosion-score/reference/mvp20/data/corrosion_series.json` (updated) --
  +1 `systematic_search_ledger` entry, +1 `series` entry, `strict_literature_count` 2 -> 3,
  `strict_literature_series` +alam2022_pa450_pa3282, `literature_bar_status` not-met -> met,
  `honest_assessment` updated. This is a module data file, not the protected portfolio manifest
  and not a `mission.md`; no protected file was touched.
- `evidence/audit/alam2022-pa450-pa3282-acquisition-v1/acquisition-receipt.v1.dsse.json` (new,
  DSSE Ed25519-signed, AUDIT_ONLY, two-replay byte-stable).

## What did NOT change

`predictive_model_status` and `candidate_prediction_status` in `corrosion_series.json` remain
`FAILED` -- meeting the literature-count bar closes the search-exhaustiveness gap only; it does not
by itself justify a predictive corrosion model, since the module still has no own wet-lab candidate
panels. No manifest, mission.md, or Phase-0 KPI was touched or promoted.
