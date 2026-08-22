# amphora-public-corrosion-benchmark

Rights-bound public corrosion/EIS benchmark ingestion and locked evaluation.

CLI:

```bash
rtk cargo run --release --locked -- data acquire --module amphora-public-corrosion-benchmark
rtk cargo run --release --locked -- data build --module amphora-public-corrosion-benchmark
rtk cargo run --release --locked -- benchmark lock --module amphora-public-corrosion-benchmark
rtk cargo run --release --locked -- benchmark run --locked --module amphora-public-corrosion-benchmark
rtk cargo run --release --locked -- benchmark replay --module amphora-public-corrosion-benchmark
```

The native contract treats existing USBR values as single-frequency
`|Z|@0.01 Hz` summaries. Kramers–Kronig and equivalent-circuit claims abstain
unless a source contains frequency-resolved real/imaginary spectra. Every
observation is bound to raw bytes, rights, method, units, conditions, split,
study, system, and replicate identity. Public rows remain benchmark-only and
cannot validate an Amphora candidate.

The current locked receipt fails Phase-1: six systems from one study, zero
untouched external systems, zero balanced-accuracy lift, and unavailable
calibration/continuous-endpoint/hostile-null results. Use
`rtk cargo test --workspace --locked` for contract and determinism checks.
