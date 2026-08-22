# amphora-cure-potlife-gate

This module now owns two deliberately separate tracks:

- the existing gel-time CRO-priority benchmark, whose behavior and commands are unchanged; and
- `coating-pot-life-physics-v1`, an owned-data, shadow-only research track for the first loss of a locked airless-spray property.

CLI:

```bash
rtk cargo run --release --locked -- data acquire --module amphora-cure-potlife-gate
rtk cargo run --release --locked -- data build --module amphora-cure-potlife-gate
rtk cargo run --release --locked -- benchmark lock --module amphora-cure-potlife-gate
rtk cargo run --release --locked -- benchmark run --locked --module amphora-cure-potlife-gate
```

Gel time, pot life, dry-hard time, through-cure, and DSC conversion are distinct
endpoints. Primary gel-time rows require Bis-A/DGEBA resin identity, hardener
family, mix ratio, temperature, test mass, method, and explicit derivative-use
eligibility. Current supplier rows are quarantined, leaving zero strict eligible
rows.

The native capability consumes only host-verified model artifacts. It abstains
for missing conditions, blocked rights, incomparable methods, or out-of-domain
inputs. A verified in-domain result may prioritize a measured gel-time CRO test;
`candidate_pot_life_prediction_h` remains null and no ranking authority is
created.

## Coating pot-life physics track

The pot-life clock starts at initial mixing. The application endpoint is
interval-censored between the last complete spray-check pass and the first
failure. Viscosity doubling is retained as a separate proxy, and KU is never
doubled arithmetically. Equivalent-viscosity doubling requires the instrument's
certified mapping; otherwise only a locked KU threshold is reported.

The workflow is intentionally fail-closed:

```bash
rtk cargo run --locked -- pot-life preflight \
  --kind scale-qualification \
  --input scale-qualification.json

rtk cargo run --locked -- pot-life protocol \
  --qualification scale-qualification.json \
  --source-ledger amphora-cure-potlife-gate/reference/pot-life/source-landscape.v1.json \
  --generated-on YYYY-MM-DD \
  --mixing-method LOCKED_METHOD

rtk cargo run --locked -- pot-life ingest --run owned-run.json

rtk cargo run --locked -- pot-life lock \
  --protocol protocol.json \
  --runs-dir .amphora/pot-life/runs

rtk cargo run --locked -- pot-life evaluate \
  --lock benchmark-lock.json \
  --runs-dir .amphora/pot-life/runs \
  --source-ledger amphora-cure-potlife-gate/reference/pot-life/source-landscape.v1.json \
  --prior-art-chart amphora-cure-potlife-gate/reference/pot-life/source-landscape.v1.json \
  --workers 2
```

`pot-life preflight` also accepts `run`, `protocol`, `benchmark-lock`,
`model-artifact`, `prediction`, `independent-review`, and `expert-packet`.
Run preflight verifies every declared raw-file hash relative to the input file,
or relative to `--raw-base-dir` when supplied. Success is an unsigned JSON
report; preflight never writes `.amphora` state, artifacts, identities, or
receipts. Intentionally incomplete scale-qualification and independent-review
starting points are in `templates/` and fail preflight until completed.

Protocol generation requires a completed non-reactive sprayer-demand
qualification and a distinct facility-approved second geometry. It creates 36
planned independent mixes: 24 fit rows at 65/95 °F and twelve sealed 73 °F
holdouts. Ingestion verifies the declared raw-file hashes. Locking verifies all
36 run contracts and rejects batch/day/mix/timepoint leakage. Evaluation replays
with 1, 2, and 8 workers, writes a signed shadow receipt, and seals—but does not
send—the blinded expert packet.

No non-null shadow prediction is contract-valid until every locked acceptance
gate and a packet-bound independent review pass. Other formulations, commercial
grades, geometries, masses, or spray configurations are out of domain. The
model is a research hypothesis, not a safety, qualification, superiority,
novelty, patentability, or FTO conclusion. `FTO NOT PERFORMED`.
