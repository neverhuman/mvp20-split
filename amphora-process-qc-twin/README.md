# amphora-process-qc-twin

Fail-closed process/QC/SPC evidence service. It can flag an evidence package,
but it never authorizes batch release.

Legacy SPC records (`values`, specification `limits`, and `control_status`)
remain accepted input and remain `NOT_PROVEN`. Pilot detector evidence also
requires `baseline_batches` and `current_batches` for every QC variable. Each
observation carries a unique `batch_id`, numeric `sequence` and `value`, plus
`instrument_id`, `calibration_id`, `operator_id`, and a `raw_file_sha256`.
`raw_file_path` is also required so the digest remains traceable to its source.
Baseline observations must set `declared_in_control: true`, contain at least
20 strictly prior batches, and have nonzero variation. This supports the
planned 30-batch pilot while reserving later batches for time-ordered checks.

Eligible history is evaluated with frozen Shewhart 3-sigma, EWMA
(`lambda=0.2`, `L=3`), and standardized CUSUM (`k=0.5`, `h=5`) detectors.
Specification limits remain separate from control limits. Optional explicit
control limits are accepted only when their batch IDs, baseline hash, method,
and recomputed values bind to the exact supplied baseline.

CLI:

```bash
rtk cargo run --release -- inspect --candidate candidate.json --headless
```

Library API:

```python
from amphora_process_qc_twin.score import score
```
