# Amphora native Rust research system

The Cargo workspace owns strict contracts, the sealed 29-capability registry,
authority policy, native capability execution, scheduling, telemetry,
hash-chained run archives, replay, and the Ratatui dashboard. No scoring path
launches a subprocess. Scientific capabilities are pre-Phase-0 and emit no
Pareto-eligible objectives until their locked external gates pass.

```bash
cargo run --release -- demo
cargo run --release -- run --candidate candidate.json --headless --jsonl
cargo run --release -- replay --verify
cargo run -p xtask -- audit
```

Use `--population`, `--generations`, `--workers`, `--seed`, and
`--objective-profile` to configure a run. Generation remains available for
workflow diagnostics, but without the pinned RDKit C++ boundary it preserves
the structure and changes lineage only. The absence of chemistry normalization
or locked evidence fails closed; it never creates a fallback scientific score.

Build the exact native chemistry boundary from the release commit:

```bash
rtk bash tools/build-rdkit-2026.03.2.sh /absolute/install/prefix
export RDKIT_INCLUDE_DIR=/absolute/install/prefix/include/rdkit
export RDKIT_LIB_DIR=/absolute/install/prefix/lib
export BOOST_INCLUDE_DIR=/absolute/install/prefix/include
rtk cargo test --workspace --locked --features rdkit
```

The builder checks out commit
`42fe8c952589bb750e27ea7f259a50b36576bfa5` (`Release_2026_03_2`),
disables optional wrappers and non-vendored integrations, and verifies the
installed CMake package version before exposing the RDKit and Boost build
paths.

The v1 hash remains SHA-256 over compact recursively sorted-key UTF-8 JSON.
Input bytes are additionally hashed without changing that v1 identity. The
strict parser rejects duplicate keys, invalid UTF-8, non-finite numbers,
excessive depth, oversized requests, and excessive collections before typed
candidate validation.
