# amphora-tolerance-robustness

Input-tolerance Monte Carlo robustness.

CLI (from the repository root; requires the omitted datasets — see
[`../BUILD.md`](../BUILD.md)):

```bash
cargo run --release -- inspect \
  --candidate amphora-candidate-contract/fixtures/formulation_candidate.json --headless
```
The score envelope includes `metrics.simulation_benchmark`, which aggregates
the registered five-seed, 200-draw tolerance suite. It is explicitly an
`UNSEEN_PERTURBATION_SIMULATION`, not unseen experimental-data validation.
Exact pass counts, normalized gate margins, and the nominal baseline are in
`metrics.simulation_benchmark`; the bounded universe harness is
Use `cargo test --workspace --locked` for the native replacement.
