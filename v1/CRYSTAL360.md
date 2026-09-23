# Nomad Crystal360

Crystal360 appends 360 physically interpretable periodic-crystal predictors to the
unchanged NOMAD 449-column baseline. The frozen schema contains every formula, unit,
neighbor rule, interpretation, training-only radial boundary, and deterministic reserve
replacement.

## Reproduce

Create the pinned project-local environment:

```bash
uv venv .venv-crystal360 --python 3.12
uv pip install --python .venv-crystal360/bin/python -r requirements-crystal360.lock
```

Build the matrices from the default `/home/ubuntu/nomad` dataset and baseline:

```bash
.venv-crystal360/bin/python build_nomad_crystal360.py --jobs 32
```

Run the registered benchmark:

```bash
.venv-crystal360/bin/python benchmark_nomad_crystal360.py --max-iter 120
```

Run focused value and invariance tests:

```bash
.venv-crystal360/bin/python -m pytest tests/crystal360 -q
```

## Leakage boundary

Radial shells and constant/duplicate replacements are fitted on training geometries only.
The schema and initial validated-column manifests are written before test structures are
transformed. Target-specific promotion uses only repeated training GroupKFold scores. The
labeled test set is read for scoring only after promoted views are frozen, and all such
scores are marked informational because that set has been reused historically.

## Outputs

`artifacts/nomad_crystal360/` contains standalone 360-column, combined 809-column, and
target-last 810-column CSV/Parquet matrices; exact-count additive family views; promoted
target-specific views; missingness, variance, duplicate, dependency, and hash audits; the
frozen schema; and full grouped-CV and informational-test benchmark results.

