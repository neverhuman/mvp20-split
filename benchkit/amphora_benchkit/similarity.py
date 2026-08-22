"""RDKit BulkTanimotoSimilarity wrappers (replacing per-pair Python loops).

ORIGINALS (per-pair loops, replaced -- bit-identity contracts in
tests/test_similarity.py):
  amphora-molecule-generator/evidence/audit/molgen-scaffold-diversity-v1/
    run_molgen_diversity.py::mean_pairwise_tanimoto, mean_pairwise_tanimoto_p,
    bootstrap_ci_intdiv1 (its precomputed pairwise T matrix)
  amphora-molecule-novelty/evidence/audit/conformal-anomaly-detection-v1/
    run_novelty_conformal.py::nn_similarity (same loop shape in the other
    molecule-novelty audits)

DETERMINISM: DataStructs.BulkTanimotoSimilarity(fp, fps) evaluates the same
RDKit C++ Tanimoto per pair as DataStructs.TanimotoSimilarity(fp, f) one at a
time, so the per-pair doubles are identical; the kit preserves the ORIGINAL
accumulation order (lexicographic i<j pairs, scalar Python `tot += t`), so
running means are bit-identical, and max() over identical doubles is exact.

rdkit is imported lazily so the package imports fine in environments without
it (functions raise ImportError on use).
"""
import numpy as np

__all__ = [
    "bulk_tanimoto", "mean_pairwise_tanimoto", "mean_pairwise_tanimoto_p",
    "pairwise_tanimoto_matrix", "nn_max_tanimoto",
]


def _datastructs():
    from rdkit import DataStructs
    return DataStructs


def bulk_tanimoto(fp, fps):
    """List of Tanimoto(fp, f) for f in fps, via one C++ bulk call."""
    return _datastructs().BulkTanimotoSimilarity(fp, list(fps))


def mean_pairwise_tanimoto(fps):
    """(mean Tanimoto over distinct unordered pairs i<j, n_pairs).

    Bit-identical to run_molgen_diversity.py::mean_pairwise_tanimoto: the
    bulk rows enumerate pairs in the same lexicographic order and the scalar
    accumulation `tot += t` is preserved."""
    DataStructs = _datastructs()
    n = len(fps)
    tot = 0.0
    cnt = 0
    for i in range(n - 1):
        row = DataStructs.BulkTanimotoSimilarity(fps[i], fps[i + 1:])
        for t in row:
            tot += t
        cnt += len(row)
    return tot / cnt, cnt


def mean_pairwise_tanimoto_p(fps, p):
    """Mean of Tanimoto^p over distinct pairs; bit-identical to the original
    mean_pairwise_tanimoto_p (same pair order, same `tot += t ** p`)."""
    DataStructs = _datastructs()
    n = len(fps)
    tot = 0.0
    cnt = 0
    for i in range(n - 1):
        row = DataStructs.BulkTanimotoSimilarity(fps[i], fps[i + 1:])
        for t in row:
            tot += t ** p
            cnt += 1
    return tot / cnt


def pairwise_tanimoto_matrix(fps):
    """(n, n) float64 symmetric Tanimoto matrix with unit diagonal.

    Value-identical to the `T` matrix precomputed inside the original
    bootstrap_ci_intdiv1 (there a list-of-lists), built from bulk rows."""
    DataStructs = _datastructs()
    n = len(fps)
    T = np.ones((n, n))
    for i in range(n - 1):
        row = np.asarray(DataStructs.BulkTanimotoSimilarity(fps[i], fps[i + 1:]))
        T[i, i + 1:] = row
        T[i + 1:, i] = row
    return T


def nn_max_tanimoto(test_fp, ref_fps, skip_idx=None):
    """max Tanimoto of test_fp against ref_fps (optionally leaving one out).

    Bit-identical to run_novelty_conformal.py::nn_similarity: that loop
    starts at best=0.0 and only takes strict improvements, i.e. it returns
    max(0.0, max(sims)) -- exact for identical doubles."""
    DataStructs = _datastructs()
    if skip_idx is None:
        fps = list(ref_fps)
    else:
        fps = [f for j, f in enumerate(ref_fps) if j != skip_idx]
    if not fps:
        return 0.0
    m = max(DataStructs.BulkTanimotoSimilarity(test_fp, fps))
    return m if m > 0.0 else 0.0
