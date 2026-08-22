"""Bit-identity tests: amphora_benchkit.quadrature (batched stacked-solve)
vs the ORIGINAL loop quadrature `conditional_arls` of the estparam
memory-detector audit, on its own uw_nodes grid."""
import numpy as np
import pytest

from amphora_benchkit import linalg as klin
from amphora_benchkit import quadrature as kq
from amphora_benchkit.origins import load_origin

from conftest import ESTPARAM
from test_linalg import ORIGIN_NAMES


@pytest.fixture(scope="module")
def origin():
    return load_origin(ESTPARAM, ORIGIN_NAMES)


def test_stacked_solve_equals_single_solve():
    """One batched np.linalg.solve over a (K, N, N) stack is bit-identical to
    K individual vector solves (the LAPACK dgesv per-slice guarantee the
    whole module rests on)."""
    rng = np.random.default_rng(42)
    K, N = 9, 51
    Rs = rng.uniform(0, 1.0 / N, size=(K, N, N))
    batched = kq._stacked_solve_ones(Rs)
    for t in range(K):
        single = np.linalg.solve(np.eye(N) - Rs[t], np.ones(N))
        assert batched[t].tobytes() == single.tobytes()


def test_ewma_batch_bit_identity_vs_scalar(origin):
    u, W = origin["uw_nodes"](20, 6, 6)
    d = np.array([abs(ui) / wj for wj in W for ui in u])
    s = np.array([1.0 / wj for wj in W for ui in u])
    batch = kq.ewma_arl_batch(d, s, chunk=7)  # chunk crosses batch boundaries
    for t in range(d.size):
        assert batch[t] == klin.ewma_arl(d[t], s[t])
        assert batch[t] == origin["ewma_arl"](d[t], s[t])


def test_cusum_twoside_batch_bit_identity_vs_scalar(origin):
    u, W = origin["uw_nodes"](20, 4, 4)
    d = np.array([abs(ui) / wj for wj in W for ui in u])
    s = np.array([1.0 / wj for wj in W for ui in u])
    batch = kq.cusum_arl_twoside_batch(d, s, chunk=5)
    for t in range(d.size):
        assert batch[t] == origin["cusum_arl_twoside"](d[t], s[t])


def test_conditional_arls_bit_identity(origin):
    """Full-surface contract: kit conditional_arls_fast == ORIGINAL
    conditional_arls byte-for-byte on all three chart grids (m=20, 16x16
    nodes -- includes the round-12 memo-cache semantics)."""
    u, W = origin["uw_nodes"](20, 16, 16)
    ref = origin["conditional_arls"](u, W)
    fast = kq.conditional_arls_fast(u, W)
    for chart in ("shewhart", "ewma", "cusum"):
        assert ref[chart].tobytes() == fast[chart].tobytes()
