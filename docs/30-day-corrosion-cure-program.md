# 30-day corrosion + cure phase-acceleration program

This implementation freezes and evaluates the corrosion and cure workstreams
without forcing promotion. Source censuses, split manifests, model families,
metrics, uncertainty methods, exclusions, and thresholds are immutable inputs to
module-specific benchmark locks under `config/program/` and
`config/benchmark-locks/`.

Run the evidence workflow with:

```bash
rtk cargo run --release --locked -- data acquire --module amphora-public-corrosion-benchmark
rtk cargo run --release --locked -- data build --module amphora-public-corrosion-benchmark
rtk cargo run --release --locked -- data verify --module amphora-public-corrosion-benchmark
rtk cargo run --release --locked -- benchmark lock --module amphora-public-corrosion-benchmark
rtk cargo run --release --locked -- benchmark run --locked --module amphora-public-corrosion-benchmark

rtk cargo run --release --locked -- data acquire --module amphora-cure-potlife-gate
rtk cargo run --release --locked -- data build --module amphora-cure-potlife-gate
rtk cargo run --release --locked -- data verify --module amphora-cure-potlife-gate
rtk cargo run --release --locked -- benchmark lock --module amphora-cure-potlife-gate
rtk cargo run --release --locked -- benchmark run --locked --module amphora-cure-potlife-gate

rtk cargo run --release --locked -- portfolio founder-update --modules corrosion,cure --verify-receipts --format markdown
rtk cargo run --release --locked -- portfolio ip-dossier --modules corrosion,cure
```

The founder command persists a hash-bound Markdown report, a sealed blinded
expert-review packet, a counsel-oriented technical IP dossier, and a signed
receipt. The review packet is marked `APPROVAL_REQUIRED_NOT_SENT`; sending it is
outside the command's authority.

Current outcome: both modules remain `PHASE_0 / AUDIT_ONLY`. Three planned USBR
cohorts are not acquired in this snapshot. All current cure vendor rows lack
explicit derivative-use eligibility and are quarantined. The existing audits do
not contain the complete locked model/hostile-null suite, calibration, continuous
endpoint comparison, or interval coverage. These are failed gates, not inferred
passes. Public evidence is capped at `SHADOW`; it cannot authorize production
ranking, product superiority, qualification, patentability, or FTO.

The IP search refresh is preliminary and recorded at
`config/program/ip-search-refresh.v1.json`. No locked technical differentiator is
established, so the dossier recommends no filing. `FTO NOT PERFORMED`.
