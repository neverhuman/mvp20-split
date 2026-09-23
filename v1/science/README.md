# science/ — RETIRED

This package was the shared, dependency-free contract layer for the 90-day model
portfolio: dataset/model manifests, grouped locked partition validation, pre-registered
metrics, immutable audit receipts, and the first-90-day authority ceiling.

**It was replaced by the Rust workspace and its CLI no longer exists in this repository.**
Do not go looking for a `science` executable. The acceptance path is now:

```bash
cargo test --workspace --locked
cargo run -p xtask -- audit
```

What survives here is one contract: `schemas/model-output.schema.json`, the model-output
schema the retired CLI emitted, kept because downstream artifacts still validate against it.

See [`../AMPHORA_RUST.md`](../AMPHORA_RUST.md) for the native system and
[`../BUILD.md`](../BUILD.md) for how to build it.

<details>
<summary>Historical: the retired CLI's command surface</summary>

Recorded for provenance. None of these commands exist any more.


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

`portfolio score` normalized a formulation once, ran the 11 registered track adapters in
constraint-first shadow mode, and validated the complete in-memory artifact set before
writing the portfolio manifest, per-track score envelopes, and detailed model receipts.

All promotion calls were fail-closed at `R&D_RANKING_READY`; product-claim authority was
not grantable by this package during the first 90 days.

</details>
