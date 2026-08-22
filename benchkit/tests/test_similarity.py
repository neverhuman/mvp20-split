"""Bit-identity tests: amphora_benchkit.similarity (BulkTanimotoSimilarity
wrappers) vs the ORIGINAL per-pair loops, on in-tree canonical fixtures
(molgen hash-locked accepted proposals; OpenPoly hash-pinned corpus)."""
import csv
import json

import numpy as np
import pytest

rdkit = pytest.importorskip("rdkit")

from amphora_benchkit import similarity as kit
from amphora_benchkit.origins import load_origin

from conftest import MOLGEN_DIV, NOVELTY, OPENPOLY_CSV


@pytest.fixture(scope="module")
def molgen():
    return load_origin(MOLGEN_DIV, {
        "ROOT", "MODULE", "GRAMMAR_DIAG", "FP_RADIUS", "FP_NBITS",
        "morgan", "mean_pairwise_tanimoto", "mean_pairwise_tanimoto_p",
        "intdiv_p", "bootstrap_ci_intdiv1"})


@pytest.fixture(scope="module")
def molgen_fps(molgen):
    diag = json.loads(molgen["GRAMMAR_DIAG"].read_bytes())
    fps = []
    for a in diag["accepted_proposals"]:
        mol, fp = molgen["morgan"](a["canonical_smiles"])
        assert mol is not None
        fps.append(fp)
    return fps


@pytest.fixture(scope="module")
def novelty():
    return load_origin(NOVELTY, {
        "CSV", "CSV_SHA_EXPECTED", "has", "cap", "make_fp", "nn_similarity"})


@pytest.fixture(scope="module")
def corpus_fps(novelty):
    """First 120 fps built exactly as the novelty audit builds its corpus."""
    from rdkit import Chem
    rows = list(csv.DictReader(open(novelty["CSV"])))
    fps = []
    for r in rows:
        if not novelty["has"](r.get("Tg (K)")):
            continue
        m = Chem.MolFromSmiles(novelty["cap"](r["PSMILES"]))
        if m is None:
            continue
        fps.append(novelty["make_fp"](m, "morgan_r2_2048"))
        if len(fps) >= 120:
            break
    return fps


def test_mean_pairwise_bit_identity(molgen, molgen_fps):
    mean_o, cnt_o = molgen["mean_pairwise_tanimoto"](molgen_fps)
    mean_k, cnt_k = kit.mean_pairwise_tanimoto(molgen_fps)
    assert (mean_o, cnt_o) == (mean_k, cnt_k)


def test_mean_pairwise_p_and_intdiv_bit_identity(molgen, molgen_fps):
    for p in (1, 2):
        assert (molgen["mean_pairwise_tanimoto_p"](molgen_fps, p)
                == kit.mean_pairwise_tanimoto_p(molgen_fps, p))


def test_pairwise_matrix_value_identity(molgen_fps):
    from rdkit import DataStructs
    fps = molgen_fps[:40]
    n = len(fps)
    T = [[0.0] * n for _ in range(n)]
    for i in range(n):
        T[i][i] = 1.0
        for j in range(i + 1, n):
            t = DataStructs.TanimotoSimilarity(fps[i], fps[j])
            T[i][j] = T[j][i] = t
    M = kit.pairwise_tanimoto_matrix(fps)
    assert np.array(T).tobytes() == M.tobytes()


def test_nn_max_bit_identity(novelty, corpus_fps):
    ref = corpus_fps[:100]
    tests = corpus_fps[100:120]
    for fp in tests:
        assert novelty["nn_similarity"](fp, ref) == kit.nn_max_tanimoto(fp, ref)
    # leave-one-out path (the calibration loop of the original)
    for i in range(10):
        assert (novelty["nn_similarity"](ref[i], ref, skip_idx=i)
                == kit.nn_max_tanimoto(ref[i], ref, skip_idx=i))
