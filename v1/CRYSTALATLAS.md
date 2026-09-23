# Nomad CrystalAtlas sprint

CrystalAtlas is an additive feature bank and execution layer. The existing
449-column baseline and Crystal360 360-column artifacts are read-only inputs.
Atlas builds one exact 12 Å periodic-neighbour cache per structure and registers
formula, units, normalization, invariance, and provenance for every descriptor.

Build the public-only matrix (the test labels are never read):

```bash
.venv-crystal360/bin/python run_nomad_crystal_atlas.py build --jobs 112
```

The build refuses train/test drift, constants, exact duplicates, and fewer than
8,000 validated descriptors. `atlas_definitions.json`, `quality_report.json`,
and `build_manifest.json` are the audit records. The optional CUDA environment
for model workers is pinned in `requirements-crystal-atlas.lock`; on the two
hosts it is expected to provide CatBoost 1.2.10, XGBoost 2.1.4, and LightGBM
4.6.0.

Probe exclusive GPU leases before starting workers:

```bash
.venv-crystal360/bin/python run_nomad_crystal_atlas.py gpu-check local xbabe1
.venv-crystal360/bin/python run_nomad_crystal_atlas.py sprint --enqueue
```

`nomad_crystal360.sprint` provides an append-only queue, one-retry work
stealing, environment/matrix/job cache keys, public-bundle validation,
7,200-second deadlines, and an immutable freeze manifest. GPU model helpers in
`nomad_crystal360.models` hard-select CUDA and do not silently fall back to CPU.

Feature selection uses only public training labels and anonymous-prototype
folds. A private grade must be performed by the owner-controlled evaluator once
the frozen submission is handed off; the repository never tunes from or reads
that grade.

The target-specific CatBoost feature-importance bake-off that combines Atlas
with precomputed Hyperion cell-matrix and embedding columns is documented in
[`docs/atlas-hyperion-bakeoff.md`](docs/atlas-hyperion-bakeoff.md). Its labeled
test score is a separate one-shot operation after predictions are frozen.
