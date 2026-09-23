# C8 fire 3 of 4 — FINAL consolidated phys/ML/stack comparison receipt

Reconciles C8 fire 1 (`phys-ml-stack-comparison-c8-v1/`, built all four
property triplets, found the RadonPy dielectric ground-truth label defect)
and fire 2 (`phys-ml-stack-comparison-c8-fire2-clean-subset-v1/`, escalated
that finding to a zero-contamination retrain showing no {physics, ML, stack}
arm beats a mean baseline on the physically valid subset).

This fire performs **no new computation**. It reconciles both prior receipts
(cited by sha256) into one consolidated, DSSE-signed, two-replay byte-stable
receipt that is the actual founder-report-citable deliverable for C8:

- `density`, `tg`, `refractive_index`: carried forward verbatim from fire 1
  (real, receipt-backed {physics, ML, stack} triplets).
- `dielectric_constant`: **rewritten**. Fire 1's naive-looking positive
  triplet is replaced by fire 2's honest zero-contamination finding —
  `NO_COMPETENT_MODEL` — plus the full label-integrity audit trail and the
  contaminated-population numbers, explicitly marked NOT CITABLE.

Top-level `verdict: CLAIM_REFUTED` — the claim under attack ("a founder-facing
per-property physics-vs-ML-vs-stack comparison can be built entirely from
receipt-backed numbers, no illustrative placeholders") survives for 3/4
properties but is refuted in its strong form: dielectric constant cannot be
filled with a competent positive point estimate from current receipt-backed
data. The only honest way to fill that cell is the quantified negative result
recorded here — which itself satisfies "no illustrative placeholders."

`founder_f8_panel_row_text` in the receipt gives the exact strings a report
generator should cite per property, including the mandatory dielectric
caveat.

Recommends `campaign_item_status=done` — the C8 done_criterion (one
consolidated signed receipt covering all four properties) is met.

Files:
- `c8_fire3_sign_receipt.py` — reconciliation + DSSE signing script (reads
  fire 1 and fire 2 receipts, no new experiments)
- `c8_fire3_final_consolidated_receipt.v1.json` — the signed receipt
- `receipt_body.canonical.json` / `receipt_body.runB.json` — two-replay gate
  inputs (byte-identical, sha256 `6dfe71e0723b387facf83bd61eff8bcb104a6f1430201d69e5b5cb4944bcb33b`)
