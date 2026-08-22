# Scientific benchmark registry

This package is the shared, dependency-free contract layer for the 90-day
model portfolio. It records dataset/model manifests, validates grouped locked
partitions, computes pre-registered metrics, creates immutable audit receipts,
and enforces the first-90-day authority ceiling.

Use `rtk cargo test --workspace --locked` for the native replacement.
`science` script):

```text
science benchmark ingest --dataset-id cure-90d --source raw.csv \
  --retrieval-date 2026-07-11 --measurement-standard "ASTM D1640" \
  --output manifest.json
science benchmark validate --manifest manifest.json --rows rows.json \
  --source-root raw-data/
science audit leakage --track corrosion --rows rows.json
science audit standards
science receipt verify --receipt receipt.json
science portfolio report
science portfolio score --candidate candidate.json --out portfolio_score.json \
  --detail-dir portfolio_details/
```

`portfolio score` normalizes a formulation once, runs the 11 registered track
adapters in constraint-first shadow mode, and validates the complete in-memory
artifact set before writing the portfolio manifest, per-track score envelopes,
and detailed model receipts.

All promotion calls are fail-closed at `R&D_RANKING_READY`; product-claim
authority is not grantable by this package during the first 90 days.
