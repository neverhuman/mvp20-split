# Detached jobs running on this machine (started 2026-07-24 ~21:20 UTC)

1. **bigsoldb-v1 benchmark** — `amphora-solvency-score/benchmarks/bigsoldb-v1/`
   - `run.log` shows fold progress; final KPIs land in `evaluation_receipt.json`
     (written incrementally after each of 3 splits: leave_solute_out,
     leave_solvent_out, grouped_random_in_domain).
   - Verify reproducibility: re-run
     `.venv/bin/python amphora-solvency-score/benchmarks/bigsoldb-v1/run_benchmark.py`
     — seed 20260724 is fixed; fold assignment hashes in the receipt must match.
   - Chain: curate.py → featurize.py → run_benchmark.py; receipts at each stage
     bind SHA-256 of inputs/outputs. Raw data: `artifacts/bigsoldb-v2/`
     (BigSolDB 2.1, Zenodo 18552681, CC-BY-4.0, MD5-verified).

2. **RDKit C++ 2026.03.2 pinned build** — log `rdkit_build.log`, prefix
   `~/opt/amphora-rdkit-2026.03.2`. On success the script prints the three
   exports; then:
   `export RDKIT_INCLUDE_DIR=$HOME/opt/amphora-rdkit-2026.03.2/include/rdkit`
   `export RDKIT_LIB_DIR=$HOME/opt/amphora-rdkit-2026.03.2/lib`
   `export BOOST_INCLUDE_DIR=$HOME/opt/amphora-rdkit-2026.03.2/include`
   `PATH=$HOME/.cargo/bin:$PATH cargo test --workspace --locked --features rdkit`
   (macOS note: use DYLD paths/rpath, not LD_LIBRARY_PATH, if runtime loading fails.)

Context and findings: `reports/redteam-phase0-audit-2026-07-24/README.md`.
