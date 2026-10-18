# Reproduction

The delivered archive contains the exact public data, frozen primary and joint protocols, split assignments, all predictions, exclusions and provenance. No downloads or paid services are needed to use the supplied data. Python 3.12.3 was used. `requirements.environment.lock` records the full runtime dependency closure; `requirements.lock` preserves the original scientific-package pins.

Create a new isolated environment and install the locked packages from PyPI if they are not already available. This task used an isolated environment backed by pre-existing packages and installed nothing. Keep numerical-library threads at one. A two-CPU affinity and 4-GiB address-space cap were used.

From the unpacked evidence directory:

```bash
python3.12 -m venv /tmp/plga-reproduction-env
/tmp/plga-reproduction-env/bin/pip install -r code/requirements.environment.lock
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p /tmp/plga-reproduction/plga-prefix-20261017-artifacts
ln -s "$PWD/primary/raw" /tmp/plga-reproduction/plga-prefix-20261017-artifacts/raw
cp primary/sources.json primary/publication_mapping.csv /tmp/plga-reproduction/plga-prefix-20261017-artifacts/
/tmp/plga-reproduction-env/bin/python code/benchmark.py prepare --artifacts /tmp/plga-reproduction/plga-prefix-20261017-artifacts
/tmp/plga-reproduction-env/bin/python code/benchmark.py pilot --artifacts /tmp/plga-reproduction/plga-prefix-20261017-artifacts
/tmp/plga-reproduction-env/bin/python code/benchmark.py full --artifacts /tmp/plga-reproduction/plga-prefix-20261017-artifacts
/tmp/plga-reproduction-env/bin/python code/benchmark.py rerun --artifacts /tmp/plga-reproduction/plga-prefix-20261017-artifacts
mkdir -p /tmp/plga-reproduction/plga-prefix-20261017-joint-artifacts
ln -s "$PWD/primary/raw" /tmp/plga-reproduction/plga-prefix-20261017-joint-artifacts/raw
cp primary/sources.json primary/publication_mapping.csv /tmp/plga-reproduction/plga-prefix-20261017-joint-artifacts/
/tmp/plga-reproduction-env/bin/python code/joint/joint_sensitivity.py prepare --artifacts /tmp/plga-reproduction/plga-prefix-20261017-joint-artifacts
/tmp/plga-reproduction-env/bin/python code/joint/joint_sensitivity.py full --artifacts /tmp/plga-reproduction/plga-prefix-20261017-joint-artifacts
```

The new split CSV files should match the retained split hashes. On the recorded environment the pilot/rerun prediction SHA-256 is `902d88227237c990ac2ce366e0bb78580f8089e3c45bcd0488e7cd81dfc92b8a`. Compare the full prediction hashes with the retained run records. Hardware/library changes can affect floating-point results; report those changes rather than silently relaxing the exact-replay criterion.

`finalize.py` only aggregates the retained losses, performs the specified cluster bootstrap, renders figures and packages evidence. It does not fit or choose models. The joint adapter changes only grouping and verifies the exact primary implementation/module hashes. The original unscored failed run and documented single-thread correction are preserved.

All scripts operate on the separate benchmark directory and its artifact folders. They do not start Amphora services, read credentials, or push repositories. Raw datasets belong outside tracked source; do not commit them accidentally. See `FIRST_PAPER_RESULTS.md` for licensing, scope and the next experiment.
