"""Batched stacked-solve ARL quadrature.

ORIGINAL (loop, replaced -- the slow quadrature case):
  amphora-process-qc-twin/evidence/audit/
    estparam-memory-detector-arl-degradation-v1/run_memory_estparam_arl.py
      `conditional_arls(u, W)` -- a Python double loop over the nu x nw
      equal-probability (U, W) grid, one np.linalg.solve of a 201x201 EWMA
      chain plus four 100/200-state CUSUM solves per UNIQUE node (thousands
      of small sequential dense solves per baseline m; the dominant cost of
      the memory-detector ARL fires).

KIT: build the transition matrices for ALL nodes at once (broadcast ndtr) and
solve them as a stacked (K, N, N) batch with ONE np.linalg.solve call per
chunk. LAPACK dgesv runs per 2D slice of the stack, so each slice's solution
is bit-identical to the original's individual solve (asserted in tests).

DETERMINISM: `conditional_arls_fast` replicates the original's semantics
EXACTLY, including its round-to-12-decimals (d_eff, s_eff) memo cache with
first-occurrence-wins representative values and the (j outer, i inner)
iteration order; tests/test_quadrature.py asserts .tobytes() equality of all
three output grids against the AST-extracted original.

Chunking does not affect bit-identity: every node's matrix build is
elementwise and every solve is per-slice. Two empirical facts (measured on
xbabe2, 128 cores) drive the driver design:
  * LARGE stacks are memory-bandwidth pathological (a 128x201x202 ndtr/solve
    working set falls out of cache and runs ~4x SLOWER than the scalar loop);
    small chunks (~8 nodes) are optimal;
  * the small chunks are embarrassingly parallel and remain bit-identical
    under a ThreadPoolExecutor (each chunk written to a disjoint output
    slice); ~16 threads saturate. Process pools catastrophically oversubscribe
    OpenBLAS (measured 50x slower) -- do not use them here.
"""
import math
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy.special import ndtr

from .linalg import (LAM_DEFAULT, L_EWMA_DEFAULT, N_EWMA_DEFAULT,
                     K_CUSUM_DEFAULT, H_CUSUM_DEFAULT, N_CUSUM_DEFAULT,
                     L_SHEW_DEFAULT)

__all__ = [
    "shewhart_arl_batch", "ewma_arl_batch",
    "cusum_arl_oneside_mc_batch", "cusum_arl_oneside_batch",
    "cusum_arl_twoside_batch", "conditional_arls_fast",
]


DEFAULT_CHUNK = 8
DEFAULT_WORKERS = 16


def _stacked_solve_ones(Rs):
    """Solve (I - R_k) x_k = 1 for a stack Rs of shape (K, N, N); returns
    (K, N). Uses a single batched np.linalg.solve call."""
    K, N, _ = Rs.shape
    A = np.eye(N)[None, :, :] - Rs
    b = np.ones((K, N, 1))
    return np.linalg.solve(A, b)[:, :, 0]


def _run_chunked(fill, n, chunk, workers):
    """Run fill(lo, hi, out) over [0, n) in `chunk`-sized segments, in a
    thread pool. Each segment writes a disjoint out slice, so parallel
    execution is bit-identical to sequential."""
    out = np.empty(n)
    segs = [(lo, min(lo + chunk, n)) for lo in range(0, max(n, 1), chunk)] if n else []
    if workers and workers > 1 and len(segs) > 1:
        with ThreadPoolExecutor(min(workers, len(segs))) as ex:
            list(ex.map(lambda seg: fill(seg[0], seg[1], out), segs))
    else:
        for lo, hi in segs:
            fill(lo, hi, out)
    return out


def shewhart_arl_batch(deltas, ss, L=L_SHEW_DEFAULT):
    """Elementwise-vectorized Shewhart ARL (same scalar ops as the original)."""
    deltas = np.asarray(deltas, dtype=float)
    ss = np.asarray(ss, dtype=float)
    p = ndtr((-L - deltas) / ss) + (1.0 - ndtr((L - deltas) / ss))
    return 1.0 / p


def ewma_arl_batch(deltas, ss, lam=LAM_DEFAULT, L=L_EWMA_DEFAULT,
                   N=N_EWMA_DEFAULT, chunk=DEFAULT_CHUNK,
                   workers=DEFAULT_WORKERS):
    """EWMA ARL for arrays of (delta, s) nodes via stacked solves in
    thread-parallel small chunks.

    Bit-identical per element to linalg.ewma_arl (and hence to the original)."""
    deltas = np.asarray(deltas, dtype=float).ravel()
    ss = np.asarray(ss, dtype=float).ravel()
    H = L * math.sqrt(lam / (2.0 - lam))
    w = 2.0 * H / N
    mids = -H + (np.arange(N) + 0.5) * w
    edges = -H + np.arange(N + 1) * w
    base = (1.0 - lam) * mids
    x = (edges[None, :] - base[:, None]) / lam      # (N, N+1), node-independent

    def fill(lo, hi, out):
        d = deltas[lo:hi]
        s = ss[lo:hi]
        cdf = ndtr((x[None, :, :] - d[:, None, None]) / s[:, None, None])
        Rs = cdf[:, :, 1:] - cdf[:, :, :-1]
        out[lo:hi] = _stacked_solve_ones(Rs)[:, N // 2]

    return _run_chunked(fill, deltas.size, chunk, workers)


def cusum_arl_oneside_mc_batch(deltas, ss, k=K_CUSUM_DEFAULT,
                               h=H_CUSUM_DEFAULT, N=N_CUSUM_DEFAULT,
                               chunk=DEFAULT_CHUNK, workers=DEFAULT_WORKERS):
    """One-sided CUSUM chain ARL for arrays of (delta, s) nodes."""
    deltas = np.asarray(deltas, dtype=float).ravel()
    ss = np.asarray(ss, dtype=float).ravel()
    w = h / N
    mids = (np.arange(N) + 0.5) * w
    edges = np.arange(N + 1) * w
    x = edges[None, :] - mids[:, None] + k          # (N, N+1)

    def fill(lo, hi, out):
        d = deltas[lo:hi]
        s = ss[lo:hi]
        cdf = ndtr((x[None, :, :] - d[:, None, None]) / s[:, None, None])
        Rs = cdf[:, :, 1:] - cdf[:, :, :-1]
        Rs[:, :, 0] = cdf[:, :, 1]                  # reflection at zero
        out[lo:hi] = _stacked_solve_ones(Rs)[:, 0]

    return _run_chunked(fill, deltas.size, chunk, workers)


def cusum_arl_oneside_batch(deltas, ss, k=K_CUSUM_DEFAULT, h=H_CUSUM_DEFAULT,
                            N=N_CUSUM_DEFAULT, chunk=DEFAULT_CHUNK,
                            workers=DEFAULT_WORKERS):
    """Richardson 2*ARL(2N) - ARL(N), elementwise identical to the original."""
    a1 = cusum_arl_oneside_mc_batch(deltas, ss, k, h, N, chunk, workers)
    a2 = cusum_arl_oneside_mc_batch(deltas, ss, k, h, 2 * N, chunk, workers)
    return 2.0 * a2 - a1


def cusum_arl_twoside_batch(deltas, ss, k=K_CUSUM_DEFAULT, h=H_CUSUM_DEFAULT,
                            N=N_CUSUM_DEFAULT, chunk=DEFAULT_CHUNK,
                            workers=DEFAULT_WORKERS):
    """Lucas-Crosier two-sided combination, elementwise identical."""
    deltas = np.asarray(deltas, dtype=float).ravel()
    ss = np.asarray(ss, dtype=float).ravel()
    a_up = cusum_arl_oneside_batch(deltas, ss, k, h, N, chunk, workers)
    a_dn = cusum_arl_oneside_batch(-deltas, ss, k, h, N, chunk, workers)
    return 1.0 / (1.0 / a_up + 1.0 / a_dn)


def conditional_arls_fast(u, W, lam=LAM_DEFAULT, L_ewma=L_EWMA_DEFAULT,
                          N_ewma=N_EWMA_DEFAULT, k=K_CUSUM_DEFAULT,
                          h=H_CUSUM_DEFAULT, N_cusum=N_CUSUM_DEFAULT,
                          L_shew=L_SHEW_DEFAULT, chunk=DEFAULT_CHUNK,
                          workers=DEFAULT_WORKERS):
    """Batched drop-in replacement for the original `conditional_arls(u, W)`.

    Replicates: d_eff = abs(u[i]) / W[j], s_eff = 1.0 / W[j] computed as the
    SAME Python scalars in the SAME (j outer, i inner) order; the
    round(.,12)-keyed memo cache with first-occurrence representative values;
    output dict of three (nu, nw) grids. Only the per-unique-node chart
    evaluations are batched (stacked solves)."""
    u = np.asarray(u, dtype=float)
    W = np.asarray(W, dtype=float)
    nu, nw = u.size, W.size
    key_order = []            # unique keys, first-occurrence order
    key_rep = {}              # key -> (d_eff, s_eff) first-occurrence scalars
    node_key = {}             # (i, j) -> key
    for j in range(nw):
        s_eff = 1.0 / W[j]
        for i in range(nu):
            d_eff = abs(u[i]) / W[j]
            kk = (round(d_eff, 12), round(s_eff, 12))
            if kk not in key_rep:
                key_rep[kk] = (d_eff, s_eff)
                key_order.append(kk)
            node_key[(i, j)] = kk
    d_arr = np.array([key_rep[kk][0] for kk in key_order])
    s_arr = np.array([key_rep[kk][1] for kk in key_order])
    sh = shewhart_arl_batch(d_arr, s_arr, L=L_shew)
    ew = ewma_arl_batch(d_arr, s_arr, lam=lam, L=L_ewma, N=N_ewma,
                        chunk=chunk, workers=workers)
    cu = cusum_arl_twoside_batch(d_arr, s_arr, k=k, h=h, N=N_cusum,
                                 chunk=chunk, workers=workers)
    pos = {kk: t for t, kk in enumerate(key_order)}
    out = {c: np.zeros((nu, nw)) for c in ("shewhart", "ewma", "cusum")}
    for j in range(nw):
        for i in range(nu):
            t = pos[node_key[(i, j)]]
            out["shewhart"][i, j] = sh[t]
            out["ewma"][i, j] = ew[t]
            out["cusum"][i, j] = cu[t]
    return out
