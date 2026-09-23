"""Vectorized (cluster) bootstrap resampling.

Adopted + generalized from the in-tree vectorized reference implementations
(prior perf fire) and the loop originals they replace:

  VECTORIZED reference (adopted):
    amphora-design-rule-score/benchmarks/alt-reinforcement-law-v1/run_altlaw.py
      `idx = rng.integers(0, n, size=(B, n))` + `boot_r2` (axis=1 reductions)
    (same pattern in guth-gold-physical-baseline-v1/run_baseline.py and
     split-integrity-dedup-v1/run_split_integrity.py)

  LOOP originals replaced (bit-identity contracts in tests/test_bootstrap.py):
    amphora-solvency-score/benchmarks/bigsoldb-v1/run_benchmark_v2.py
      `cluster_bootstrap_ci`, `paired_bootstrap_delta`
    amphora-public-corrosion-benchmark/evidence/audit/
      nist-baseline-fold-significance-v1/run_fold_significance.py
      `cluster_bootstrap_ci` (fold-level mean bootstrap)

DETERMINISM: every function here is tested BIT-IDENTICAL to the original it
replaces (same RNG stream, same accumulation order/reduction tree). The key
facts making that possible:
  * one `rng.integers(0, n, size=(B, n))` call consumes the identical RNG
    stream as B sequential `rng.integers(0, n, size=n)` calls (row-major
    fill), for np.random.Generator and np.random.RandomState alike;
  * `arr2d.mean(axis=1)` / `.sum(axis=1)` on a C-contiguous array applies the
    same pairwise-summation reduction per row as `np.mean` on each row alone;
  * for variable-size cluster resamples the kit gathers the exact
    concatenated element order of the original before reducing.
"""
import numpy as np

__all__ = [
    "bootstrap_indices", "boot_r2_dist", "percentile_ci",
    "cluster_bootstrap_mean_dist", "cluster_bootstrap_mean_ci",
    "cluster_bootstrap_rmse_ci", "paired_cluster_bootstrap_delta",
]


def bootstrap_indices(rng, n, B):
    """(B, n) uniform row-resample index matrix in ONE RNG call.

    Bit-compatible with B sequential size-n draws from the same generator
    state (asserted in tests). Accepts np.random.Generator (uses .integers,
    as run_altlaw.py does) or np.random.RandomState (uses .randint, as the
    NIST fold-significance original does)."""
    if isinstance(rng, np.random.RandomState):
        return rng.randint(0, n, size=(B, n))
    return rng.integers(0, n, size=(B, n))


def boot_r2_dist(y, pred, idx):
    """Bootstrap R^2 distribution, vectorized over replicates.

    ORIGINAL: run_altlaw.py::boot_r2 (verbatim generalization; that code is
    itself the vectorized ~50x reference adopted by this kit).
    Returns shape (B,) float64; bit-identical to the original."""
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    yb = y[idx]
    pb = pred[idx]
    ybar = yb.mean(axis=1, keepdims=True)
    ss_res = ((yb - pb) ** 2).sum(axis=1)
    ss_tot = ((yb - ybar) ** 2).sum(axis=1)
    return 1.0 - ss_res / ss_tot


def percentile_ci(v, lo=2.5, hi=97.5):
    """[lo, hi] percentile CI as floats (run_altlaw.py::ci)."""
    l, h = np.percentile(v, [lo, hi])
    return [float(l), float(h)]


def cluster_bootstrap_mean_dist(values, n_boot=20000, seed=0):
    """Bootstrap distribution of the mean of `values`, fully vectorized.

    ORIGINAL (loop, replaced): nist-baseline-fold-significance-v1/
    run_fold_significance.py::cluster_bootstrap_ci -- RandomState(seed),
    n_boot sequential randint draws, one .mean() per replicate.
    Bit-identical: same RandomState stream (single (n_boot, n) draw), same
    per-row pairwise mean reduction."""
    rng = np.random.RandomState(seed)
    arr = np.array(values)
    n = len(arr)
    idx = rng.randint(0, n, size=(n_boot, n))
    return arr[idx].mean(axis=1)


def cluster_bootstrap_mean_ci(values, n_boot=20000, seed=0):
    """(lo, hi, boot_mean) exactly as the NIST original returns them."""
    boots = cluster_bootstrap_mean_dist(values, n_boot=n_boot, seed=seed)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(lo), float(hi), float(boots.mean())


def _group_arrays(y, p, groups, extra=None):
    """Replicate the original's pandas groupby("g") grouping: keys sorted,
    intra-group row order preserved."""
    import pandas as pd
    cols = {"y": y, "p": p, "g": groups}
    if extra is not None:
        cols["b"] = extra
    df = pd.DataFrame(cols)
    out = []
    for g, s in df.groupby("g"):
        row = (s["y"].values, s["p"].values) if extra is None else \
              (s["y"].values, s["p"].values, s["b"].values)
        out.append(row)
    return out


def cluster_bootstrap_rmse_ci(y, p, groups, n_boot=1000, seed=0):
    """95% cluster-bootstrap CI for RMSE (resampling whole groups).

    ORIGINAL (loop, replaced): bigsoldb-v1/run_benchmark_v2.py::
    cluster_bootstrap_ci. Bit-identical: single rng.choice((n_boot, G)) draw
    (same PCG64 stream as G-sized draws in a loop), per-replicate gather of
    the exact concatenated element order, then the same np.sqrt(np.mean(.))."""
    rng = np.random.default_rng(seed)
    by_g = _group_arrays(y, p, groups)
    G = len(by_g)
    picks = rng.choice(G, size=(n_boot, G), replace=True)
    # precompute per-group squared errors once (elementwise == original's
    # post-concatenation (ps - ys)**2)
    err2 = [np.asarray((pg - yg), dtype=float) ** 2 for yg, pg in by_g]
    vals = np.empty(n_boot)
    for b in range(n_boot):
        e = np.concatenate([err2[i] for i in picks[b]])
        vals[b] = float(np.sqrt(np.mean(e)))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def paired_cluster_bootstrap_delta(y, p_a, p_b, groups, n_boot=1000, seed=0):
    """Paired cluster bootstrap of RMSE(b) - RMSE(a); returns the original's
    summary dict (rmse_delta_mean / rmse_delta_ci95 / frac_bootstrap_favouring_model).

    ORIGINAL (loop, replaced): bigsoldb-v1/run_benchmark_v2.py::
    paired_bootstrap_delta (note: original seeds with seed + 1; caller passes
    the SAME seed as the original call site and we add 1 here, as it does).
    Bit-identical by the same argument as cluster_bootstrap_rmse_ci."""
    rng = np.random.default_rng(seed + 1)
    by_g = _group_arrays(y, p_a, groups, extra=p_b)
    G = len(by_g)
    picks = rng.choice(G, size=(n_boot, G), replace=True)
    err2_a = [np.asarray((ag - yg), dtype=float) ** 2 for yg, ag, _ in by_g]
    err2_b = [np.asarray((bg - yg), dtype=float) ** 2 for yg, _, bg in by_g]
    deltas = np.empty(n_boot)
    for i in range(n_boot):
        ea = np.concatenate([err2_a[j] for j in picks[i]])
        eb = np.concatenate([err2_b[j] for j in picks[i]])
        ra_ = np.sqrt(np.mean(ea))
        rb_ = np.sqrt(np.mean(eb))
        deltas[i] = float(rb_ - ra_)
    return {
        "rmse_delta_mean": float(deltas.mean()),
        "rmse_delta_ci95": [float(np.percentile(deltas, 2.5)),
                            float(np.percentile(deltas, 97.5))],
        "frac_bootstrap_favouring_model": float(np.mean(deltas > 0)),
    }
