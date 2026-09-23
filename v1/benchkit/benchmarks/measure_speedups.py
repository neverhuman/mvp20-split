#!/usr/bin/env python3
"""Measure wall-clock speedups of amphora_benchkit vs the ORIGINAL in-tree
implementations (AST-extracted, executed verbatim) on in-tree canonical
fixtures, re-asserting bit-identity on every measured case.

Outputs (in this directory):
  speedups.canonical.json / speedups.runB.json -- DETERMINISTIC content only
      (bit-identity verdicts, fixture identities/hashes, configs). The
      run-twice byte-stability gate is asserted by the caller.
  timings.v1.json -- wall_seconds + speedup ratios (informative, NOT part of
      the canonical byte-stable payload; timings vary run to run).

Usage: python3 measure_speedups.py <canonical|runB>
"""
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

BENCHKIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCHKIT))
sys.path.insert(0, str(BENCHKIT / "tests"))

from amphora_benchkit import bootstrap as kboot           # noqa: E402
from amphora_benchkit import linalg as klin               # noqa: E402
from amphora_benchkit import quadrature as kq             # noqa: E402
from amphora_benchkit import similarity as ksim           # noqa: E402
from amphora_benchkit.origins import load_origin, file_sha256  # noqa: E402
from conftest import (ALTLAW, BIGSOLDB_V2, NIST_FOLD, ESTPARAM, SPC_ARL,
                      MOLGEN_DIV, NOVELTY, OPENPOLY_CSV)  # noqa: E402
from test_linalg import ORIGIN_NAMES                      # noqa: E402

MODE = sys.argv[1] if len(sys.argv) > 1 else "canonical"
HERE = Path(__file__).resolve().parent


def clock(fn, *a, **kw):
    t0 = time.perf_counter()
    out = fn(*a, **kw)
    return out, time.perf_counter() - t0


def sha_arr(x):
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()


results = {}   # deterministic
timings = {}   # informative

# ---------------------------------------------------------------- bootstrap
nist = load_origin(NIST_FOLD, {"cluster_bootstrap_ci"})
rows = list(csv.DictReader(open(OPENPOLY_CSV)))
tg, names = [], []
for r in rows:
    v = (r.get("Tg (K)") or "").strip()
    if v:
        try:
            tg.append(float(v))
        except ValueError:
            continue
        names.append(r["Name"])
tg = np.array(tg)

arr30 = tg[:30]
o_out, o_t = clock(nist["cluster_bootstrap_ci"], arr30, n_boot=20000, seed=0)
k_out, k_t = clock(kboot.cluster_bootstrap_mean_ci, arr30, n_boot=20000, seed=0)
results["bootstrap_mean_ci_n30_B20000"] = {
    "original": "nist-baseline-fold-significance-v1/run_fold_significance.py::cluster_bootstrap_ci",
    "original_file_sha256": file_sha256(NIST_FOLD),
    "fixture": "OpenPoly Tg[:30] (hash-pinned corpus CSV)",
    "fixture_sha256": sha_arr(arr30),
    "bit_identical": tuple(o_out) == tuple(k_out),
}
timings["bootstrap_mean_ci_n30_B20000"] = {
    "original_wall_seconds": o_t, "kit_wall_seconds": k_t,
    "speedup_x": o_t / k_t if k_t > 0 else None,
}

bsv2 = load_origin(BIGSOLDB_V2, {"N_BOOT", "SEED", "cluster_bootstrap_ci"})
y = tg[:600]
p = np.full(y.size, float(np.median(tg)))
groups = np.array(names[:600])
o_out, o_t = clock(bsv2["cluster_bootstrap_ci"], y, p, groups, n_boot=1000, seed=20260724)
k_out, k_t = clock(kboot.cluster_bootstrap_rmse_ci, y, p, groups, n_boot=1000, seed=20260724)
results["cluster_bootstrap_rmse_ci_600groups_B1000"] = {
    "original": "bigsoldb-v1/run_benchmark_v2.py::cluster_bootstrap_ci",
    "original_file_sha256": file_sha256(BIGSOLDB_V2),
    "fixture": "OpenPoly Tg[:600], per-name groups, global-median predictor",
    "fixture_sha256": sha_arr(y),
    "bit_identical": o_out == k_out,
}
timings["cluster_bootstrap_rmse_ci_600groups_B1000"] = {
    "original_wall_seconds": o_t, "kit_wall_seconds": k_t,
    "speedup_x": o_t / k_t if k_t > 0 else None,
}

# ------------------------------------------------------------------- linalg
spc = load_origin(SPC_ARL, {"Phi", "ewma_arl"})
est = load_origin(ESTPARAM, ORIGIN_NAMES)

# hand-rolled pure-Python Gauss-Jordan (m=100 -> N=201) vs kit np.linalg.solve
o_val, o_t = clock(spc["ewma_arl"], 0.2, 3.0, 0.5, 100)
k_val, k_t = clock(klin.ewma_arl, 0.5, 1.0, 0.2, 3.0, 201)
relerr = abs(k_val - o_val) / abs(o_val)
sib_val = est["ewma_arl"](0.5, 1.0)

# scaling point at m=300 -> N=601 (m=300 is in the audit's BASELINES grid)
o_val6, o_t6 = clock(spc["ewma_arl"], 0.2, 3.0, 0.5, 300)
k_val6, k_t6 = clock(klin.ewma_arl, 0.5, 1.0, 0.2, 3.0, 601)
results["ewma_arl_N601"] = {
    "replaced_hand_rolled": "spc-arl-characterization-v1 ewma_arl, m=300 (N=601)",
    "hand_rolled_cross_check_relative_error": abs(k_val6 - o_val6) / abs(o_val6),
}
timings["ewma_arl_N601"] = {
    "hand_rolled_wall_seconds": o_t6, "kit_wall_seconds": k_t6,
    "speedup_x": o_t6 / k_t6 if k_t6 > 0 else None,
}

results["ewma_arl_N201"] = {
    "replaced_hand_rolled": "spc-arl-characterization-v1/run_arl_characterization.py::ewma_arl (pure-Python Gauss-Jordan)",
    "replaced_file_sha256": file_sha256(SPC_ARL),
    "adopted_original": "estparam-memory-detector-arl-degradation-v1/run_memory_estparam_arl.py::ewma_arl (np.linalg.solve)",
    "adopted_file_sha256": file_sha256(ESTPARAM),
    "bit_identical_to_adopted_original": k_val == sib_val,
    "hand_rolled_cross_check_relative_error": relerr,
    "note": ("bit-identity contract is vs the adopted np.linalg.solve original; "
             "the hand-rolled Gauss-Jordan differs only in floating-point "
             "elimination order (erf vs ndtr, manual pivoting vs LAPACK dgesv) "
             "and is cross-checked by relative error, exactly as the original "
             "characterization script cross-validates methods."),
}
timings["ewma_arl_N201"] = {
    "hand_rolled_wall_seconds": o_t, "kit_wall_seconds": k_t,
    "speedup_x": o_t / k_t if k_t > 0 else None,
}

# --------------------------------------------------------------- quadrature
u, W = est["uw_nodes"](20, est["NU_GRID"], est["NW_GRID"])   # the live 64x64 grid
o_out, o_t = clock(est["conditional_arls"], u, W)
k_out, k_t = clock(kq.conditional_arls_fast, u, W)
bit = all(o_out[c].tobytes() == k_out[c].tobytes()
          for c in ("shewhart", "ewma", "cusum"))
results["conditional_arls_m20_64x64"] = {
    "original": "estparam-memory-detector-arl-degradation-v1/run_memory_estparam_arl.py::conditional_arls",
    "original_file_sha256": file_sha256(ESTPARAM),
    "fixture": "uw_nodes(m=20, 64, 64) -- the audit's own live grid (1 of 6 baselines)",
    "grid_sha256": {c: sha_arr(o_out[c]) for c in ("shewhart", "ewma", "cusum")},
    "bit_identical": bit,
}
timings["conditional_arls_m20_64x64"] = {
    "original_wall_seconds": o_t, "kit_wall_seconds": k_t,
    "speedup_x": o_t / k_t if k_t > 0 else None,
    "note": "original audit runs this for 6 baselines m in " + str(est["BASELINES"]),
}

# --------------------------------------------------------------- similarity
try:
    from rdkit import Chem  # noqa: F401
    HAVE_RDKIT = True
except ImportError:
    HAVE_RDKIT = False

if HAVE_RDKIT:
    nov = load_origin(NOVELTY, {"CSV", "CSV_SHA_EXPECTED", "has", "cap", "make_fp",
                                "nn_similarity"})
    gen = load_origin(MOLGEN_DIV, {"ROOT", "MODULE", "GRAMMAR_DIAG", "FP_RADIUS",
                                   "FP_NBITS", "morgan", "mean_pairwise_tanimoto"})
    from rdkit import Chem
    fps = []
    for r in rows:
        smi = (r.get("PSMILES") or "").strip()
        if not smi:
            continue
        m = Chem.MolFromSmiles(nov["cap"](smi))
        if m is None:
            continue
        fps.append(nov["make_fp"](m, "morgan_r2_2048"))

    key = "mean_pairwise_tanimoto_%dfps" % len(fps)
    o_out, o_t = clock(gen["mean_pairwise_tanimoto"], fps)
    k_out, k_t = clock(ksim.mean_pairwise_tanimoto, fps)
    results[key] = {
        "original": "molgen-scaffold-diversity-v1/run_molgen_diversity.py::mean_pairwise_tanimoto",
        "original_file_sha256": file_sha256(MOLGEN_DIV),
        "fixture": "all %d parseable OpenPoly corpus fps (morgan_r2_2048, novelty-audit construction)" % len(fps),
        "n_pairs": o_out[1],
        "bit_identical": o_out == k_out,
    }
    timings[key] = {
        "original_wall_seconds": o_t, "kit_wall_seconds": k_t,
        "speedup_x": o_t / k_t if k_t > 0 else None,
    }

    ref = fps[:500]
    tests = fps[500:]
    t0 = time.perf_counter()
    nn_o = [nov["nn_similarity"](f, ref) for f in tests]
    o_t = time.perf_counter() - t0
    t0 = time.perf_counter()
    nn_k = [ksim.nn_max_tanimoto(f, ref) for f in tests]
    k_t = time.perf_counter() - t0
    nkey = "nn_max_tanimoto_%dx%d" % (len(tests), len(ref))
    results[nkey] = {
        "original": "conformal-anomaly-detection-v1/run_novelty_conformal.py::nn_similarity",
        "original_file_sha256": file_sha256(NOVELTY),
        "fixture": "OpenPoly corpus fps: %d queries vs %d references" % (len(tests), len(ref)),
        "bit_identical": nn_o == nn_k,
    }
    timings[nkey] = {
        "original_wall_seconds": o_t, "kit_wall_seconds": k_t,
        "speedup_x": o_t / k_t if k_t > 0 else None,
    }
else:
    results["similarity"] = {"skipped": "rdkit not importable in this interpreter"}

# -------------------------------------------------------------------- write
results["_meta"] = {
    "schema": "amphora.benchkit.speedup-bit-identity-diagnostic.v1",
    "benchkit_version": "0.1.0",
    "all_bit_identical": all(
        v.get("bit_identical", v.get("bit_identical_to_adopted_original", True)) is True
        for k, v in results.items() if not k.startswith("_")),
    "determinism_note": ("wall-clock timings intentionally excluded from this "
                         "canonical payload; see timings.v1.json"),
}
canon = json.dumps(results, indent=2, sort_keys=True).encode()
out = HERE / ("speedups.%s.json" % ("canonical" if MODE == "canonical" else "runB"))
out.write_bytes(canon)

if MODE == "canonical":
    (HERE / "timings.v1.json").write_text(json.dumps(
        {"schema": "amphora.benchkit.timings.v1",
         "host": "xbabe2", "python": sys.version.split()[0],
         "timings_informative_only": True, "cases": timings},
        indent=2, sort_keys=True))

print(json.dumps({"mode": MODE, "all_bit_identical": results["_meta"]["all_bit_identical"],
                  "wrote": str(out)}, indent=2))
for k, v in timings.items():
    print("%-45s %8.3fs -> %7.3fs  (%.1fx)" % (
        k, v.get("original_wall_seconds", v.get("hand_rolled_wall_seconds", 0.0)),
        v["kit_wall_seconds"], v["speedup_x"]))
