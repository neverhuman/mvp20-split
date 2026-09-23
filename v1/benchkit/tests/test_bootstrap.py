"""Bit-identity tests: amphora_benchkit.bootstrap vs the ORIGINAL in-tree
implementations, executed verbatim via AST extraction, on in-tree canonical
fixtures. Equality is asserted at the byte/bit level (== / .tobytes()),
never approximate."""
import numpy as np

from amphora_benchkit import bootstrap as kit
from amphora_benchkit.origins import load_origin

from conftest import BIGSOLDB_V2, NIST_FOLD


def test_rng_stream_equivalence_generator():
    """One (B, n) draw == B sequential n-draws, np.random.Generator."""
    a = np.random.default_rng(123).integers(0, 57, size=(40, 57))
    rng = np.random.default_rng(123)
    b = np.stack([rng.integers(0, 57, size=57) for _ in range(40)])
    assert np.array_equal(a, b)
    assert np.array_equal(kit.bootstrap_indices(np.random.default_rng(123), 57, 40), a)


def test_rng_stream_equivalence_randomstate():
    """One (B, n) draw == B sequential n-draws, np.random.RandomState."""
    a = np.random.RandomState(7).randint(0, 30, size=(50, 30))
    rs = np.random.RandomState(7)
    b = np.stack([rs.randint(0, 30, size=30) for _ in range(50)])
    assert np.array_equal(a, b)
    assert np.array_equal(kit.bootstrap_indices(np.random.RandomState(7), 30, 50), a)


def test_rng_stream_equivalence_generator_choice():
    """One rng.choice((B, G)) == B sequential rng.choice(G) draws (the
    bigsoldb original's per-replicate pattern)."""
    G, B = 41, 200
    a = np.random.default_rng(20260724).choice(G, size=(B, G), replace=True)
    rng = np.random.default_rng(20260724)
    b = np.stack([rng.choice(G, size=G, replace=True) for _ in range(B)])
    assert np.array_equal(a, b)


def test_boot_r2_bit_identity_altlaw(altlaw_origin):
    """Kit boot_r2_dist == ORIGINAL run_altlaw.py boot_r2 (the adopted
    vectorized reference), on the canonical purformance Experiment.zip
    fixture, for the fit-free and linear LOIO arms."""
    o = altlaw_origin
    y, n, B, SEED = o["y"], o["n"], o["B"], o["SEED"]
    kidx = kit.bootstrap_indices(np.random.default_rng(SEED), n, B)
    assert np.array_equal(kidx, o["idx"])
    for arm in ("p_const", "p_lin4"):
        pred = o["loio"](o[arm])
        dist_o = o["boot_r2"](pred)
        dist_k = kit.boot_r2_dist(y, pred, kidx)
        assert dist_o.tobytes() == dist_k.tobytes()
        assert o["ci"](dist_o) == kit.percentile_ci(dist_k)


def test_cluster_bootstrap_mean_bit_identity(openpoly_tg):
    """Kit vectorized mean-bootstrap == ORIGINAL NIST fold-significance
    cluster_bootstrap_ci (loop) bit-for-bit. The original's own input CSV
    (/tmp scratch) no longer exists, so the input vector here is the first 30
    Tg values of the hash-pinned OpenPoly canonical CSV; the contract tested
    is exact replication of the original's RNG stream and reductions."""
    o = load_origin(NIST_FOLD, {"cluster_bootstrap_ci"})
    vals, _ = openpoly_tg
    arr = vals[:30]
    lo_o, hi_o, mean_o = o["cluster_bootstrap_ci"](arr, n_boot=20000, seed=0)
    lo_k, hi_k, mean_k = kit.cluster_bootstrap_mean_ci(arr, n_boot=20000, seed=0)
    assert (lo_o, hi_o, mean_o) == (lo_k, hi_k, mean_k)


def test_cluster_bootstrap_rmse_bit_identity(altlaw_origin):
    """Kit cluster_bootstrap_rmse_ci == ORIGINAL bigsoldb-v1
    run_benchmark_v2.py cluster_bootstrap_ci (loop) on the canonical
    purformance fixture (real 3-iteration cluster structure)."""
    o = load_origin(BIGSOLDB_V2, {"N_BOOT", "SEED", "cluster_bootstrap_ci",
                                  "paired_bootstrap_delta"})
    a = altlaw_origin
    y = a["y"]
    p = a["loio"](a["p_lin4"])
    groups = a["it"]
    ci_o = o["cluster_bootstrap_ci"](y, p, groups, n_boot=500, seed=o["SEED"])
    ci_k = kit.cluster_bootstrap_rmse_ci(y, p, groups, n_boot=500, seed=o["SEED"])
    assert ci_o == ci_k


def test_cluster_bootstrap_rmse_bit_identity_many_groups(altlaw_origin, openpoly_tg):
    """Same contract with many variable-name groups (one group per polymer
    name, includes duplicate names -> variable cluster sizes)."""
    o = load_origin(BIGSOLDB_V2, {"N_BOOT", "SEED", "cluster_bootstrap_ci"})
    vals, names = openpoly_tg
    y = vals[:200]
    p = np.full(y.size, float(np.median(vals)))
    groups = np.array(names[:200])
    ci_o = o["cluster_bootstrap_ci"](y, p, groups, n_boot=200, seed=11)
    ci_k = kit.cluster_bootstrap_rmse_ci(y, p, groups, n_boot=200, seed=11)
    assert ci_o == ci_k


def test_paired_cluster_bootstrap_delta_bit_identity(altlaw_origin):
    """Kit paired_cluster_bootstrap_delta == ORIGINAL paired_bootstrap_delta
    (full returned summary dict, exact float equality)."""
    o = load_origin(BIGSOLDB_V2, {"N_BOOT", "SEED", "paired_bootstrap_delta"})
    a = altlaw_origin
    y = a["y"]
    p_a = a["loio"](a["p_lin4"])
    p_b = a["loio"](a["p_const"])
    groups = a["it"]
    d_o = o["paired_bootstrap_delta"](y, p_a, p_b, groups, n_boot=500, seed=3)
    d_k = kit.paired_cluster_bootstrap_delta(y, p_a, p_b, groups, n_boot=500, seed=3)
    assert d_o == d_k
