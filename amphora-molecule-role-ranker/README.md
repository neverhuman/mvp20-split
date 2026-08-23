# amphora-molecule-role-ranker

Score a defined molecule against both resin and hardener role tracks for the
epoxy-polyamide marine-primer envelope. Exact EEW/AHEW and structure validity
come exclusively from `amphora-molecule-property`; commercial and
polydisperse products remain measured-only.

Both inferred and declared tracks are retained as audit output. Supplying
`resin` or `hardener` may populate `objective_values.role_fit` only when the
host has verified a current, identity-bound Phase-1 receipt. Ambiguous and
out-of-domain structures always abstain. The versioned legacy control set is
`reference/mvp20/data/role_fit_benchmark.v1.json`; it is not a blinded
expert-parity holdout.

CLI:

```bash
cargo run --release -- inspect --candidate amphora-candidate-contract/fixtures/molecule_candidate.json --headless
cargo run --release -- data verify --module amphora-molecule-role-ranker
cargo run --release -- data build --module amphora-molecule-role-ranker
cargo run --release -- benchmark lock --module amphora-molecule-role-ranker
cargo run --release -- benchmark run --locked --module amphora-molecule-role-ranker
cargo run --release -- benchmark replay --module amphora-molecule-role-ranker
```
