# amphora-tolerance-robustness

Input-tolerance Monte Carlo robustness.

CLI:

```bash
rtk cargo run --release -- inspect --candidate candidate.json --headless
```

Library API:

```python
from amphora_tolerance_robustness.score import score
```

The score envelope includes `metrics.simulation_benchmark`, which aggregates
the registered five-seed, 200-draw tolerance suite. It is explicitly an
`UNSEEN_PERTURBATION_SIMULATION`, not unseen experimental-data validation.
Exact pass counts, normalized gate margins, and the nominal baseline are in
`metrics.simulation_benchmark`; the bounded universe harness is
Use `rtk cargo test --workspace --locked` for the native replacement.
