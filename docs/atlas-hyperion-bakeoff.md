# Atlas + Hyperion CatBoost bake-off

`run_atlas_hyperion_bakeoff.py` is the public-label-only runner for Atlas-only
or Atlas-plus-Hyperion feature-importance experiments. It keeps the historically reused
test labels outside the synchronized worker bundle and exposes the test score as
a separate, one-shot command after the submission is frozen.

## Hyperion input manifest

The manifest binds every input by SHA-256. Matrix paths are relative to the
manifest unless absolute. Supported matrix formats are NPY, NPZ, Parquet, and
CSV. The four required roles are `cellmat_train`, `cellmat_test`,
`embedding_train`, and `embedding_test`; common train-first aliases are also
accepted. The expected widths are 449 and 128.

Row order must be proved with an `id`/`row_id` column in every matrix, or with a
hashed sidecar shared by the two matrices for each split:

```json
{
  "files": {
    "cellmat_train": {
      "path": "cellmat_train.npy",
      "sha256": "..."
    },
    "cellmat_test": {
      "path": "cellmat_test.npy",
      "sha256": "..."
    },
    "embedding_train": {
      "path": "embedding_train.npy",
      "sha256": "..."
    },
    "embedding_test": {
      "path": "embedding_test.npy",
      "sha256": "..."
    },
    "cellmat_train_mean": {
      "path": "cellmat_train_mean.npy",
      "sha256": "...",
      "role": "cellmat_train_mean"
    }
  },
  "row_ids": {
    "train": {"path": "train_ids.csv", "sha256": "..."},
    "test": {"path": "test_ids.csv", "sha256": "..."}
  }
}
```

Every listed hash is checked. A file whose role or filename identifies it as a
mean must have exactly one row; it is recorded in the validation report but is
not added to the matrix. Hyperion columns must be finite and have positive
training variance. Exact duplicates of Atlas or earlier Hyperion columns are
removed and recorded.

## Run sequence

Use the pinned model environment (`requirements-crystal-atlas.lock`) on both
hosts. The local model interpreter defaults to `/usr/bin/python3`; the remote
interpreter defaults to `python3`.

```bash
.venv-crystal360/bin/python run_atlas_hyperion_bakeoff.py prepare --atlas-only

# Or include separately produced Hyperion matrices:
.venv-crystal360/bin/python run_atlas_hyperion_bakeoff.py prepare \
  --hyperion-manifest /path/to/hyperion/manifest.json

.venv-crystal360/bin/python run_atlas_hyperion_bakeoff.py validate

.venv-crystal360/bin/python run_atlas_hyperion_bakeoff.py run
```

The Atlas-only run stages the existing 2,400×9,969 and 600×9,969 matrices.
Its deterministic feature grid is `p0, p20, p40, p50, p60, p70, p75, p80,
p85, p90, p92.5, p95, p96, p97, p98, p98.5, p99, p99.25, p99.5`, resolved
to nested ranking prefixes from all 9,969 columns down to 50. The best three
two-fold percentile views are confirmed with five folds alongside the exact
809-column control; either the control or full `p0` view may be selected.

The run stages only the hashed public bundle and self-contained GPU worker on
`xbabe1`. Formation jobs prefer the local RTX 3090 and bandgap jobs prefer the
remote RTX 4090. Each host has a single-worker executor and an OS GPU lease. A
failed fit is retried once on the other GPU; there is no CPU fallback.

Progress is displayed with Rich when available and is always mirrored to
`progress.jsonl`. Individual results are cached using the public bundle, runner,
stable environment, model parameters, and job specification, so rerunning an
interrupted experiment is idempotent.

The frozen run contains the target rankings and top 100, fold-local rankings,
all six importance observations, screen and confirmation scores, source-family
representation at every evaluated cut, selected columns and Hyperion counts,
OOF/test fold predictions, submission, hashes, and model parameters.

Only after inspecting the freeze manifest, score the historically reused test
once:

```bash
.venv-crystal360/bin/python run_atlas_hyperion_bakeoff.py score-informational
```

This command uses exclusive creation of `informational_test_score.json`. It
refuses a second score and never edits the frozen selection manifest.
