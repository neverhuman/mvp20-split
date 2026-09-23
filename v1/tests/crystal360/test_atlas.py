from pathlib import Path
import time

import numpy as np
import pandas as pd
import pytest
from pymatgen.core import Lattice, Structure

from nomad_crystal360.atlas import NeighborCache, atlas_row
from nomad_crystal360.sprint import AppendOnlyQueue, Deadline, Job, cache_key


def toy():
    return Structure(Lattice.from_parameters(5.2, 5.8, 6.3, 82, 96, 73), ["Al", "Ga", "O", "O"],
                     [[.08,.11,.17],[.47,.39,.28],[.18,.31,.42],[.64,.19,.51]])


def test_cache_is_exact_pbc_and_atlas_is_translation_permutation_invariant():
    original=toy(); shifted=Structure(original.lattice,original.species,original.frac_coords+[.23,-.31,.44])
    order=[3,1,0,2]; permuted=Structure(original.lattice,[original.species[i] for i in order],original.frac_coords[order])
    a,_=atlas_row(original); b,_=atlas_row(shifted); c,_=atlas_row(permuted)
    for key in a:
        assert b[key] == pytest.approx(a[key], rel=3e-5, abs=3e-5) or (np.isnan(a[key]) and np.isnan(b[key]))
        assert c[key] == pytest.approx(a[key], rel=3e-5, abs=3e-5) or (np.isnan(a[key]) and np.isnan(c[key]))
    assert len(a) > 11000 and len(a) == len(set(a))


def test_neighbor_cache_reuses_one_cutoff_and_vectors_are_cartesian():
    cache=NeighborCache.from_structure(toy(), cutoff=12)
    assert cache.distances.size == cache.vectors.shape[0]
    assert np.all(cache.distances <= 12.000001)
    assert np.allclose(np.linalg.norm(cache.vectors,axis=1), cache.distances)


def test_append_only_queue_claim_and_retry(tmp_path: Path):
    q=AppendOnlyQueue(tmp_path/"jobs.jsonl"); job=Job("formation_energy_ev_natom",("family_pair",),0,1,200,"local")
    q.add([job]); claimed=q.claim("local"); assert claimed is not None and claimed.job_id
    q.finish(claimed,"local",{"score":.1}); assert q.claim("local") is None
    q.fail(claimed,"local","disconnect",retry=True); retry=q.claim("xbabe1"); assert retry is not None
    assert len((tmp_path/"jobs.jsonl").read_text().splitlines()) == 6


def test_deadline_and_cache_key_are_deterministic():
    d=Deadline.start(0); assert d.expired();
    job=Job("bandgap_energy_ev",("full",),1,7,200,"xbabe1")
    assert cache_key("env","matrix",job,{"depth":8}) == cache_key("env","matrix",job,{"depth":8})
