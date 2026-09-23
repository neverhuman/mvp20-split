import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

BENCHKIT_DIR = Path(__file__).resolve().parents[1]
if str(BENCHKIT_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHKIT_DIR))

TREE = Path(os.environ.get("AMPHORA_ROOT", Path(__file__).resolve().parents[2])).resolve()

ALTLAW = TREE / "amphora-design-rule-score/benchmarks/alt-reinforcement-law-v1/run_altlaw.py"
BIGSOLDB_V2 = TREE / "amphora-solvency-score/benchmarks/bigsoldb-v1/run_benchmark_v2.py"
NIST_FOLD = TREE / ("amphora-public-corrosion-benchmark/evidence/audit/"
                    "nist-baseline-fold-significance-v1/run_fold_significance.py")
ESTPARAM = TREE / ("amphora-process-qc-twin/evidence/audit/"
                   "estparam-memory-detector-arl-degradation-v1/run_memory_estparam_arl.py")
SPC_ARL = TREE / ("amphora-process-qc-twin/evidence/audit/"
                  "spc-arl-characterization-v1/run_arl_characterization.py")
MOLGEN_DIV = TREE / ("amphora-molecule-generator/evidence/audit/"
                     "molgen-scaffold-diversity-v1/run_molgen_diversity.py")
NOVELTY = TREE / ("amphora-molecule-novelty/evidence/audit/"
                  "conformal-anomaly-detection-v1/run_novelty_conformal.py")
OPENPOLY_CSV = Path(__file__).resolve().parent / (
    "fixtures/openpoly/final_polymer_properties_fromliterature.csv"
)


def _omitted_dataset(path):
    manifest_path = TREE / "DATASETS.local.json"
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    relative = path.relative_to(TREE).as_posix()
    return next((item for item in manifest["omitted"] if item["path"] == relative), None)


def _require_local_dataset(path):
    if path.is_file():
        return
    entry = _omitted_dataset(path)
    if entry is None:
        pytest.fail(f"required test input is missing and not manifest-listed: {path}")
    pytest.skip(
        f"local dataset intentionally omitted: {entry['path']} "
        f"(sha256={entry['sha256']})"
    )


@pytest.fixture(scope="session")
def altlaw_origin():
    """AST-extracted altlaw benchmark state: canonical purformance fixture
    (Experiment.zip) + the ORIGINAL vectorized bootstrap objects."""
    from amphora_benchkit.origins import load_origin
    _require_local_dataset(
        TREE / "amphora-design-rule-score/reference/purformance/zenodo-13742098/Experiment.zip"
    )
    names = {"ROOT", "ZIP", "FEATS", "SEED", "B", "load", "X", "y", "it",
             "zip_sha", "V", "H", "M", "P", "ITER", "loio", "p_const",
             "p_lin4", "rng", "n", "idx", "boot_r2", "ci"}
    return load_origin(ALTLAW, names)


@pytest.fixture(scope="session")
def openpoly_tg():
    """Tg (K) column of the hash-pinned rights-clean OpenPoly corpus CSV
    (the conformal-anomaly-detection-v1 canonical fixture)."""
    import csv as _csv
    rows = list(_csv.DictReader(open(OPENPOLY_CSV)))
    vals, names = [], []
    for r in rows:
        v = (r.get("Tg (K)") or "").strip()
        if not v:
            continue
        try:
            vals.append(float(v))
        except ValueError:
            continue
        names.append(r["Name"])
    return np.array(vals), names
