# INTEGRITY FLAG — pre-existing receipt appears to contradict the "ST-19168 untouched" record

**Discovered:** 2026-07-31, during campaign item C3 (pre-registration for the ST-19168
unlock). **Severity:** requires human review. **Action taken by this cron:** none beyond
documenting the discrepancy; no file was modified, deleted, or superseded, and the
quarantined xlsx itself was not opened by this cron.

## What was found

`amphora-barrier-corrosion-score/docs/mission.md`, `docs/capability-profile.json`, and
today's C2 rights-review-request receipt
(`evidence/audit/st-19168-rights-review-v1/rights_review_request_receipt.v1.json`,
`opened_or_parsed_quarantined_asset: false`) all assert that the ST-19168 raw workbook
(`reference/eis/st-19168/raw/19168_inhibitive_coating_system_data.xlsx`, SHA-256
`9e34fccc83fa7b9d7f3cb21c0076ff34f30266cae5d11df02d6d00c72e9d44e1`, acquired
2026-07-17) remains **untouched** pending rights review.

However, a separate, already-committed and already-signed file exists at:

```
amphora-barrier-corrosion-score/reference/eis/st-19168/st19168_eis_rust_creep_correlation_receipt.v1.json
```

(file mtime 2026-07-22 17:51 UTC, i.e. 5 days after acquisition and 9 days before
today's rights-review-request). This file:

- Declares `"toolkit": {"name": "scipy+openpyxl", ...}` — `openpyxl` is an Excel-file
  reading library; it is required to read `.xlsx` bytes at all.
- Declares `"dataset_file": "reference/eis/st-19168/raw/19168_inhibitive_coating_system_data.xlsx"`
  and the SAME `dataset_file_sha256` as the quarantined asset.
- Contains a `raw_specimen_records` array with what appear to be REAL extracted numeric
  rows (specimen IDs like `ZP-1`, `Z-3(N/A)`, `O-2`; per-specimen `EIS_Z_ohms` values;
  six exposure-protocol rust-creep columns `BOR_cyclic`, `DI_immersion`, `FOG_cyclic`,
  `HAR_immersion`, `PRO_cyclic`, `QUV_cyclic`).
- Contains computed Pearson/Spearman correlations and permutation p-values per exposure
  protocol, derived from those extracted rows.
- Is itself DSSE-signed (`toolkit-reviewer-...` key).

This is only explicable if the quarantined xlsx WAS opened and parsed to produce this
file — directly contradicting the "untouched" assertion currently on record in
mission.md, capability-profile.json, and the C2 receipt (all three of which appear to be
unaware this file exists, since none reference or supersede it).

## What this cron did NOT do

- Did not open, re-parse, or extract further numbers from the quarantined xlsx itself.
- Did not use any number from the flagged receipt above (its raw_specimen_records were
  read only far enough to notice the schema — specimen IDs, column names — visible in
  this discovery step; no value from it was copied into, or used to calibrate, the
  synthetic shadow data or the frozen pre-registered analysis script produced under
  `benchmarks/st19168-preregistered-v1/` in this same fire).
- Did not delete, modify, or supersede the flagged receipt. Superseding a signed
  artifact is a judgment call this cron is not positioned to make unilaterally; it is
  left for human review.
- Did not edit `source-landscape.v1.json`, `mission.md`, or `capability-profile.json`.

## What a human needs to decide

1. Was this file produced by a fire that ran BEFORE the quarantine policy was actually
   understood/applied to this asset (i.e. a genuine process gap between acquisition on
   2026-07-17 and the first quarantine-aware fire), or is it a live violation that
   should have been caught earlier?
2. Should `reference/eis/st-19168/st19168_eis_rust_creep_correlation_receipt.v1.json` be
   moved to `evidence/superseded/` with a supersession record, pending the outcome of the
   C2 rights review? Its correlational findings (weak, non-significant Pearson/Spearman
   associations across all six exposure protocols, p>0.4 in every case) should not be
   treated as authoritative either way until its provenance is resolved.
3. Does this event require a broader audit of other modules' `reference/` and `evidence/`
   trees for similarly stale quarantine-adjacent artifacts predating current governance?

## Non-claim

This flag makes no claim about whether USBR RISE rights would in fact permit derivative
use of ST-19168 (that determination is exactly what the pending C2 rights review asks
for). It only flags that SOME numeric extraction already happened on disk, in a signed
artifact, before that determination was made or requested.
