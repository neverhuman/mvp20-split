# PLGA review evidence and fresh-clone reproduction

Start with [Outside review](../../OUTSIDE_REVIEW.md). This directory publishes compact **derived curve-error metrics**, recorded verification receipts, public source pins and scripts. It contains no original time/release observations, formulation descriptors, SMILES, model pickles, private reports, credentials or private file links.

## Model-free checks

From the repository root:

```sh
python3 docs/review/plga/verify_evidence.py
```

This standard-library check verifies six content hashes, all 16 pilot and 12 stage-2 aggregate result cells, cohort/group consistency and recorded replay receipts. It fits no models. To independently recompute the four pilot intervals, ten stage-2 intervals, centered-bootstrap values and ten-comparison Holm correction:

```sh
python3.12 -m venv /tmp/amphora-metric-review
/tmp/amphora-metric-review/bin/pip install -r docs/review/plga/requirements.txt
/tmp/amphora-metric-review/bin/python docs/review/plga/verify_evidence.py --bootstrap
```

The only extra dependency for this arithmetic check is NumPy 1.26.4. The result is recorded in `evidence/bootstrap_verification.json`; a receipt is not a substitute for running the check independently. No network access or raw dataset is needed after cloning for either verification tier.

## Source data and full model reproduction

Use Linux and Python 3.12. The scientific package versions are pinned in the benchmark modules. The commands below are explicit opt-in training commands; **do not confuse them with the model-free checks above**. This publication did not start new model runs.

```sh
python3.12 -m venv /tmp/amphora-model-review
/tmp/amphora-model-review/bin/pip install \
  -r v2/benchmarks/plga_prefix/requirements.environment.lock \
  -r v2/benchmarks/plga_strengthening/requirements.lock
PY=/tmp/amphora-model-review/bin/python
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
WORK="$(mktemp -d /tmp/amphora-model-review.XXXXXX)/run"
"$PY" docs/review/plga/prepare_reproduction.py --work "$WORK" --download
```

`--download` acquires exactly three public checksum-pinned XLSX files from the sources in [SOURCE_DATA.json](evidence/SOURCE_DATA.json): two processed files from an immutable GitHub derivative revision and the official version-2 Mendeley formulation table. Dataset DOI: [10.17632/zzvtdrcy76.2](https://doi.org/10.17632/zzvtdrcy76.2), CC BY 4.0. Read [NOTICE.md](NOTICE.md). Alternatively, manually download those exact files and replace `--download` with `--source-cache /absolute/path/to/the/three/files`. The setup verifies sizes and SHA-256 before use and never writes raw data inside the repository.

The setup copies the original benchmark modules from immutable commits `9e4d4afb444d683761078d2a3bbaa151a3d6177c` and `dfac76aebc18dcf8b2e021c016f53aaa6b14bd3f` into the new external work directory. Use a full clone containing those commits. It reconstructs publication/drug mapping and all frozen splits, verifies their exact hashes, and prepares prefix receipts. **It fits no global models.** Keeping source copies external also prevents the original prepare entry point from rewriting tracked dependency-lock files in the checkout.

Run the original full pilot analyses:

```sh
"$PY" docs/review/plga/run_with_limits.py -- \
  "$PY" "$WORK/code/plga_prefix/benchmark.py" full \
  --artifacts "$WORK/plga-prefix-20261017-artifacts"
"$PY" docs/review/plga/run_with_limits.py -- \
  "$PY" "$WORK/code/plga_prefix/joint/joint_sensitivity.py" full \
  --artifacts "$WORK/plga-prefix-20261017-joint-artifacts"
```

Run the frozen stage-2 matrix and its full fresh-process replay:

```sh
STAGE="$WORK/plga-strengthening-20261017-artifacts"
for pass in main replay; do
  for learner in rf lightgbm; do
    "$PY" docs/review/plga/run_with_limits.py -- \
      "$PY" "$WORK/code/plga_strengthening/campaign.py" run \
      --artifacts "$STAGE" --learner "$learner" --run "$pass"
  done
done
"$PY" "$WORK/code/plga_strengthening/campaign.py" summarize --artifacts "$STAGE"
"$PY" "$WORK/code/plga_strengthening/audit/independent_audit.py" --artifacts "$STAGE"
"$PY" "$WORK/code/plga_strengthening/audit/feature_replay.py" --artifacts "$STAGE"
"$PY" docs/review/plga/verify_reproduction.py --work "$WORK"
```

The portable wrapper selects an allowed logical CPU (or accepts `--cpu N`), keeps scientific threads at one, adds nice 10, caps address space at 4 GiB, CPU time at 1,800 s, and wall time at 2,400 s per learner process. Commands above run sequentially; at most two such processes may be run concurrently on distinct allowed CPUs to match the original concurrency bound. `--plan` prints the selected limits/command and executes no benchmark. It avoids assuming the original host's CPU IDs 113/114 exist elsewhere. Scientific model/protocol code and grids are unchanged.

Stage 2 has 780 learner fits plus 780 for replay. The full pilot commands add the two original 15-fold analyses. Original stage-2 main process times were about 649 s for RF and 54 s for LightGBM; timings are hardware/toolchain dependent. Exact prediction bytes were established on the recorded environment; a mismatch on another system must be reported rather than silently relaxed. The comparator checks 22 retained output files against their recorded hashes. Generated artifacts always stay in `WORK`, not Git.

## Evidence inventory and boundaries

| File | Published content |
|---|---|
| `evidence_summary.json` | Audited cohort, prefix timing, grouping, all scores, all planned contrasts and inference labels |
| `pilot_formulation_losses.csv` | 5,120 derived per-formulation losses, averaged across repeats, for the two pilot analyses |
| `stage2_formulation_losses.csv` | 3,840 derived per-formulation losses across six arms and two learners |
| `replay_receipts.json` | Recorded pilot/stage-2 output hashes and equality receipts, with no full prediction rows |
| `provenance.json` | Original commits, protocol/code/split hashes, chronological locks, runtime/software and source artifact hashes |
| `SOURCE_DATA.json` | Public download URLs, file sizes, pinned checksums, dataset DOI/version and license attribution |
| `MANIFEST.json` | Sizes and SHA-256 of the six substantive evidence files |
| `bootstrap_verification.json` | Result of the model-free independent arithmetic check |
| `setup_selftest.json` | Cached-input preparation test, three matching split hashes, zero global model fits |

Original measurement tables, all individual timepoint predictions and the private full evidence reports are **not** in the repository. Download original source data and regenerate predictions with the explicit commands above. The curve-loss tables support independent verification of the reported aggregate/paired statistics; they do not independently prove that training excluded every held-out label. That boundary is supported by inspectable frozen source, split/feature checks and full model reproduction.

This is retrospective in-vitro PLGA evidence. Stage 2 remains post-pilot internal validation on a development-exposed corpus; all ten planned 95% intervals include zero and no contrast survives Holm correction. No external/prospective ocular panel, independent assay replicate study, clinical validation, patent-novelty finding or quantified development saving was performed. Published research code/evidence does not establish the readiness of every other Amphora module.
