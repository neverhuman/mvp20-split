# Rights Review Request — USBR ST-19168 Inhibitive Coating System Dataset

**Module:** amphora-barrier-corrosion-score
**Prepared:** 2026-07-31 (automated cron, AUDIT_ONLY authority — this is a request, not a decision)
**Status:** PENDING_HUMAN_RIGHTS_REVIEW

## What the human needs to do

1. File a USBR RISE data-use confirmation request (or equivalent written confirmation) for
   **catalog item 4640 / item 11562** (`https://data.usbr.gov/catalog/4640/item/11562`),
   asking the Bureau of Reclamation to confirm that the ST-19168 inhibitive-coating-system
   dataset is a U.S. Federal Government work in the public domain under **17 U.S.C. §105**,
   and that derivative/reuse of the underlying table data (not just the published summary)
   is permitted.
2. On confirmation, update `reference/eis/source-landscape.v1.json` entry `usbr-st-19168`:
   flip `license` from `USBR_RIGHTS_REVIEW_REQUIRED` to the confirmed license string, and
   `rights_status` from `ACQUIRED_UNTOUCHED_QUARANTINED_PENDING_RIGHTS_REVIEW` to
   `DERIVATIVE_ALLOWED` (or the equivalent), setting `eligible_for_derivatives: true`.
3. Only after that flip may any module code open, parse, or extract numeric rows from the
   quarantined file. This cron has not opened it and will not until the flip is made.

This is expected to be a **confirmation ask, not a licensing ask**: two other USBR RISE
datasets from the same publishing agency (data.usbr.gov, project 21019, catalog item 8048)
are already queued and license-cleared on identical grounds (US Federal Government work,
public domain, 17 U.S.C. §105) — see `data-acquisition-queue.jsonl` entries dated 2026-07,
module `amphora-public-corrosion-benchmark`. ST-19168 is the same publisher, the same
`data.usbr.gov` RISE catalog, and the same USBR EIS/coatings research program; there is no
known reason its rights basis would differ, but this has not yet been confirmed in writing
for this specific catalog item and must not be assumed.

## What the dataset contains

- **File:** `amphora-barrier-corrosion-score/reference/eis/st-19168/raw/19168_inhibitive_coating_system_data.xlsx`
- **SHA-256:** `9e34fccc83fa7b9d7f3cb21c0076ff34f30266cae5d11df02d6d00c72e9d44e1`
- **Source:** `https://data.usbr.gov/catalog/4640/item/11562` (US Bureau of Reclamation, RISE)
- **Content (per catalog metadata only — file itself unopened):** ten inhibitive coating
  systems, acquired 2026-07-17, currently quarantined with
  `license: USBR_RIGHTS_REVIEW_REQUIRED`, `rights_status:
  ACQUIRED_UNTOUCHED_QUARANTINED_PENDING_RIGHTS_REVIEW`, `eligible_for_derivatives: false`
  in `reference/eis/source-landscape.v1.json`.
- This cron has verified only the file's SHA-256 (a bytes-level integrity check). No sheet,
  cell, or row has been opened, parsed, or read. Nothing about the dataset's actual numeric
  content is asserted anywhere in this package.

## What it unlocks

`amphora-barrier-corrosion-score/reference/mvp20/data/corrosion_series.json` (schema
`mvp20.corrosion_series.v4`) defines the module's `strict_validation_bar`:

> `>=3 strictly in-class, open table-read epoxy-amine/polyamide ordered side-by-side
> numeric series; still not met`

Current state: `strict_literature_count: 2`, series = `["asperti2024", "zhu2022"]`,
`literature_bar_status: "literature bar not met"`, `predictive_model_status: "FAILED - no
predictive corrosion model justified"`.

A rights-cleared, table-read extraction of ST-19168 (ten independently reported coating
systems, i.e. potentially several strictly-in-class ordered series once screened against the
module's `required_series_fields`) is the most direct path on disk today to a **third**
in-class series — the specific count needed to cross the literature bar for the first time.
Crossing that bar does not by itself validate a predictive model, but it is the named
precondition (`literature_bar_status`) for the module's first defensible coating-barrier
literature validation. No other asset currently on disk or in the acquisition queue is this
close to closing the gap; the other two USBR asks (frequency-resolved EIS raw sweeps, and an
erratum request) extend a *different* dataset (USBR-21019, `amphora-public-corrosion-benchmark`)
and do not touch the literature-bar count.

## Non-actions taken by this cron

- The quarantined xlsx was **not** opened, parsed, unzipped, or read beyond a SHA-256 hash
  of its raw bytes (an integrity check, not content access).
- No `source-landscape.v1.json` field was edited (rights fields remain
  `USBR_RIGHTS_REVIEW_REQUIRED` / `ACQUIRED_UNTOUCHED_QUARANTINED_PENDING_RIGHTS_REVIEW` /
  `eligible_for_derivatives: false`, unchanged).
- No claim about ST-19168's numeric content, coating systems, or results is made anywhere in
  this package.
