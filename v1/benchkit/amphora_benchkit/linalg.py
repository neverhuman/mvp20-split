"""Markov-chain ARL computation via np.linalg.solve.

ORIGINAL (adopted, np.linalg.solve based -- the ~1000x-vs-hand-rolled sibling):
  amphora-process-qc-twin/evidence/audit/
    estparam-memory-detector-arl-degradation-v1/run_memory_estparam_arl.py
      `shewhart_arl`, `ewma_arl`, `cusum_arl_oneside_mc`,
      `cusum_arl_oneside` (Richardson), `cusum_arl_twoside`
  (same solve pattern in mr-memory-detector-arl-degradation-v1)

REPLACED (hand-rolled O(N^3) pure-Python Gauss-Jordan with partial pivoting):
  amphora-process-qc-twin/evidence/audit/
    spc-arl-characterization-v1/run_arl_characterization.py::ewma_arl

DETERMINISM: kit functions are tested BIT-IDENTICAL to the adopted originals
(tests/test_linalg.py runs the original file's own code via AST extraction on
its own (d_eff, s_eff) quadrature nodes). The hand-rolled Gauss-Jordan is NOT
bit-identical to LAPACK dgesv (different elimination arithmetic order); the
cross-check against it is reported as a relative-error diagnostic in the
speedup measurement, exactly as the original characterization script itself
cross-validates methods by relative error.

Default chart designs are the live in-tree designs:
  EWMA lam=0.20, L=3.0, N=201 states; CUSUM k=0.5, h=5.0, N=100 states/arm;
  Shewhart L=3.0.
"""
import math

import numpy as np
from scipy.special import ndtr

__all__ = [
    "markov_arl", "shewhart_arl", "ewma_arl",
    "cusum_arl_oneside_mc", "cusum_arl_oneside", "cusum_arl_twoside",
]

LAM_DEFAULT = 0.20
L_EWMA_DEFAULT = 3.0
N_EWMA_DEFAULT = 201
K_CUSUM_DEFAULT = 0.5
H_CUSUM_DEFAULT = 5.0
N_CUSUM_DEFAULT = 100
L_SHEW_DEFAULT = 3.0


def markov_arl(R):
    """ARL vector of an absorbing Markov chart: solves (I - R) arl = 1.

    R: (N, N) sub-stochastic transient transition matrix. This is the core
    np.linalg.solve primitive the adopted original uses in place of the
    hand-rolled Gauss-Jordan elimination."""
    R = np.asarray(R, dtype=float)
    N = R.shape[0]
    return np.linalg.solve(np.eye(N) - R, np.ones(N))


def shewhart_arl(delta, s=1.0, L=L_SHEW_DEFAULT):
    """Alarm when |Y| > L, Y ~ N(delta, s^2). Verbatim from the original."""
    p = ndtr((-L - delta) / s) + (1.0 - ndtr((L - delta) / s))
    return 1.0 / p


def ewma_arl(delta, s=1.0, lam=LAM_DEFAULT, L=L_EWMA_DEFAULT, N=N_EWMA_DEFAULT):
    """Brook-Evans Markov-chain EWMA ARL, z0 = 0 (centre state), N odd.

    Verbatim generalization of the adopted original (constants -> kwargs)."""
    H = L * math.sqrt(lam / (2.0 - lam))
    w = 2.0 * H / N
    mids = -H + (np.arange(N) + 0.5) * w
    edges = -H + np.arange(N + 1) * w
    base = (1.0 - lam) * mids                       # (N,)
    x = (edges[None, :] - base[:, None]) / lam      # (N, N+1)
    cdf = ndtr((x - delta) / s)
    R = cdf[:, 1:] - cdf[:, :-1]
    arl = np.linalg.solve(np.eye(N) - R, np.ones(N))
    return float(arl[N // 2])


def cusum_arl_oneside_mc(delta, s=1.0, k=K_CUSUM_DEFAULT, h=H_CUSUM_DEFAULT,
                         N=N_CUSUM_DEFAULT):
    """One-sided CUSUM Brook-Evans chain with reflection at zero, C0 = 0.

    Verbatim generalization of the adopted original."""
    w = h / N
    mids = (np.arange(N) + 0.5) * w
    edges = np.arange(N + 1) * w
    x = edges[None, :] - mids[:, None] + k          # (N, N+1)
    cdf = ndtr((x - delta) / s)
    R = cdf[:, 1:] - cdf[:, :-1]
    R[:, 0] = cdf[:, 1]                             # reflection at zero
    arl = np.linalg.solve(np.eye(N) - R, np.ones(N))
    return float(arl[0])


def cusum_arl_oneside(delta, s=1.0, k=K_CUSUM_DEFAULT, h=H_CUSUM_DEFAULT,
                      N=N_CUSUM_DEFAULT):
    """Richardson-extrapolated one-sided CUSUM ARL: 2*ARL(2N) - ARL(N)."""
    a1 = cusum_arl_oneside_mc(delta, s, k, h, N)
    a2 = cusum_arl_oneside_mc(delta, s, k, h, 2 * N)
    return 2.0 * a2 - a1


def cusum_arl_twoside(delta, s=1.0, k=K_CUSUM_DEFAULT, h=H_CUSUM_DEFAULT,
                      N=N_CUSUM_DEFAULT):
    """Lucas & Crosier 1982: 1/ARL = 1/ARL+ + 1/ARL-."""
    a_up = cusum_arl_oneside(delta, s, k, h, N)
    a_dn = cusum_arl_oneside(-delta, s, k, h, N)
    return 1.0 / (1.0 / a_up + 1.0 / a_dn)
