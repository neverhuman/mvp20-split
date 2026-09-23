# amphora-molecule-property

Score exact EEW/AHEW and a non-authoritative density estimate from defined,
single-component structures. The versioned benchmark is
`reference/mvp20/data/eew_ahew_benchmark.v1.json`; commercial polydisperse
products remain measured-only.

CLI (from the repository root; requires the omitted datasets — see
[`../BUILD.md`](../BUILD.md)):

```bash
cargo run --release -- inspect \
  --candidate amphora-candidate-contract/fixtures/formulation_candidate.json --headless
```
Exact results are published under `metrics.property_results` and remain
deterministic constraints and audit evidence, not optimizer objectives.
Commercial and polydisperse grades require measured product values.

Evidence workflow:

```bash
cargo run --release -- data verify --module amphora-molecule-property
cargo run --release -- data build --module amphora-molecule-property
cargo run --release -- benchmark lock --module amphora-molecule-property
cargo run --release -- benchmark run --locked --module amphora-molecule-property
cargo run --release -- benchmark replay --module amphora-molecule-property
```
