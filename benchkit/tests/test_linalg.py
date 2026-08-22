"""Bit-identity tests: amphora_benchkit.linalg vs the ORIGINAL adopted
np.linalg.solve ARL implementations (estparam-memory-detector), on the
original's own (d_eff, s_eff) quadrature nodes."""
import numpy as np
import pytest

from amphora_benchkit import linalg as kit
from amphora_benchkit.origins import load_origin

from conftest import ESTPARAM

ORIGIN_NAMES = {
    "LAM", "L_EWMA", "K_CUSUM", "H_CUSUM", "L_SHEW",
    "N_EWMA_STATES", "N_CUSUM_STATES", "BASELINES", "NU_GRID", "NW_GRID",
    "BATCH_WINDOW", "FA_BUDGET",
    "c4", "shewhart_arl", "ewma_arl", "cusum_arl_oneside_mc",
    "cusum_arl_oneside", "cusum_arl_twoside", "uw_nodes", "conditional_arls",
}


@pytest.fixture(scope="module")
def origin():
    return load_origin(ESTPARAM, ORIGIN_NAMES)


@pytest.fixture(scope="module")
def nodes(origin):
    """(d_eff, s_eff) pairs from the original's own uw_nodes reduction,
    m=20 (the first live baseline), 8x8 grid."""
    u, W = origin["uw_nodes"](20, 8, 8)
    pairs = []
    for j in range(W.size):
        s_eff = 1.0 / W[j]
        for i in range(u.size):
            pairs.append((abs(u[i]) / W[j], s_eff))
    return pairs


def test_defaults_match_original_constants(origin):
    assert kit.LAM_DEFAULT == origin["LAM"]
    assert kit.L_EWMA_DEFAULT == origin["L_EWMA"]
    assert kit.N_EWMA_DEFAULT == origin["N_EWMA_STATES"]
    assert kit.K_CUSUM_DEFAULT == origin["K_CUSUM"]
    assert kit.H_CUSUM_DEFAULT == origin["H_CUSUM"]
    assert kit.N_CUSUM_DEFAULT == origin["N_CUSUM_STATES"]
    assert kit.L_SHEW_DEFAULT == origin["L_SHEW"]


def test_shewhart_bit_identity(origin, nodes):
    for d, s in nodes:
        assert kit.shewhart_arl(d, s) == origin["shewhart_arl"](d, s)


def test_ewma_bit_identity(origin, nodes):
    for d, s in nodes[::4]:
        assert kit.ewma_arl(d, s) == origin["ewma_arl"](d, s)


def test_cusum_twoside_bit_identity(origin, nodes):
    for d, s in nodes[::8]:
        assert kit.cusum_arl_twoside(d, s) == origin["cusum_arl_twoside"](d, s)


def test_markov_arl_matches_inline_solve():
    """markov_arl(R) is exactly the solve the original performs inline."""
    rng = np.random.default_rng(0)
    N = 37
    R = rng.uniform(0, 1.0 / N, size=(N, N))
    expected = np.linalg.solve(np.eye(N) - R, np.ones(N))
    assert kit.markov_arl(R).tobytes() == expected.tobytes()
