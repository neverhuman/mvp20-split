# amphora-optimizer-orchestrator

Evolution/AI multi-objective engine that consumes ScoreEnvelopes.

CLI (from the repository root; requires the omitted datasets — see
[`../BUILD.md`](../BUILD.md)):

```bash
cargo run --release -- inspect \
  --candidate amphora-candidate-contract/fixtures/formulation_candidate.json --headless
```
Predictive `ScoreEnvelope` inputs remain constraint-only unless their compact
model summary declares `solver_use: R&D_OBJECTIVE`, is `IN_DOMAIN`, and carries
a valid central `R&D_RANKING_READY` authority receipt. Safety constraints may
set `conservative_bound: auto`; minimum constraints then use `lower_95`, maximum
constraints use `upper_95`, and intervals crossing the threshold fail closed as
`INCONCLUSIVE` constraint evaluations. Deterministic authority tiers retain
their existing behavior. A request containing declared hard constraints can run
as a constraint-only screen without manufacturing an optimization objective.
