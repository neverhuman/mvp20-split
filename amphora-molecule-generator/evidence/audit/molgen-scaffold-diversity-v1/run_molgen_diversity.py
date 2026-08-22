#!/usr/bin/env python3
"""AUDIT_ONLY diagnostic: chemical-space DIVERSITY characterization of the
amphora-molecule-generator deterministic-grammar accepted-proposal set.

Closes the third canonical generation-quality pillar (diversity / chemical-
space coverage) that the two prior molecule-generator receipts did NOT close
(they closed yield, feasibility, and structural novelty).

Baselines (all published, non-circular):
  * Bemis & Murcko 1996, J. Med. Chem. 39(15):2887-2893, DOI 10.1021/jm9602928
    -- molecular framework / scaffold decomposition.
  * Polykovskiy et al. 2020, Front. Pharmacol. 11:565644 (MOSES) -- internal
    diversity IntDiv_p and scaffold-count generation metrics.
  * Rogers & Hahn 2010, J. Chem. Inf. Model. 50(5):742-754 -- Morgan/ECFP
    circular fingerprints (radius 2, 2048 bits).
  * Bajusz, Racz & Heberger 2015, J. Cheminform. 7:20 -- Tanimoto is the
    appropriate similarity coefficient for binary fingerprints.
  * Efron 1979, Ann. Statist. 7(1):1-26 -- bootstrap confidence intervals.

Non-circular: the molecule SMILES are read directly from the hash-locked prior
grammar receipt diagnostic; scaffolds and fingerprints are re-derived here by
RDKit; no prior yield/feasibility number is used as an input to any metric.

AUDIT_ONLY: does not promote authority, does not flip scientific_readiness,
does not modify the manifest, locked datasets, or any signed Phase-0 KPI.
"""
import hashlib
import itertools
import json
import random
from pathlib import Path

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-molecule-generator"
GRAMMAR_DIAG = (MODULE / "evidence/audit/molgen-deterministic-grammar-yield-v1"
                / "diagnostic.canonical.json")
OUT = MODULE / "evidence/audit/molgen-scaffold-diversity-v1" / "diagnostic.canonical.json"

FP_RADIUS = 2
FP_NBITS = 2048
BOOT_SEED = 20260729
BOOT_N = 20000


def sha(b):
    return hashlib.sha256(b).hexdigest()


def morgan(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, FP_RADIUS, nBits=FP_NBITS)
    return mol, fp


def murcko_real(mol):
    """Bemis-Murcko real scaffold canonical SMILES ('' if acyclic)."""
    scaf = MurckoScaffold.GetScaffoldForMol(mol)
    return Chem.MolToSmiles(scaf) if scaf.GetNumAtoms() > 0 else ""


def murcko_generic(mol):
    """Bemis-Murcko generic framework (atoms->C, bonds->single); '' if acyclic."""
    scaf = MurckoScaffold.GetScaffoldForMol(mol)
    if scaf.GetNumAtoms() == 0:
        return ""
    try:
        gen = MurckoScaffold.MakeScaffoldGeneric(scaf)
        return Chem.MolToSmiles(gen)
    except Exception:
        # fall back to the real scaffold if genericization cannot sanitize
        return Chem.MolToSmiles(scaf)


def mean_pairwise_tanimoto(fps):
    """Mean Tanimoto over distinct unordered pairs i<j."""
    n = len(fps)
    tot = 0.0
    cnt = 0
    for i, j in itertools.combinations(range(n), 2):
        tot += DataStructs.TanimotoSimilarity(fps[i], fps[j])
        cnt += 1
    return tot / cnt, cnt


def mean_pairwise_tanimoto_p(fps, p):
    n = len(fps)
    tot = 0.0
    cnt = 0
    for i, j in itertools.combinations(range(n), 2):
        t = DataStructs.TanimotoSimilarity(fps[i], fps[j])
        tot += t ** p
        cnt += 1
    return tot / cnt


def intdiv_p(fps, p):
    """MOSES internal diversity IntDiv_p over distinct pairs.
    IntDiv_p = 1 - (mean_{i<j} T(i,j)^p)^(1/p)."""
    m = mean_pairwise_tanimoto_p(fps, p)
    return 1.0 - m ** (1.0 / p)


def bootstrap_ci_intdiv1(fps, seed, n_boot):
    """Percentile bootstrap 95% CI for IntDiv_1 (resample molecules)."""
    rng = random.Random(seed)
    n = len(fps)
    # precompute full pairwise Tanimoto matrix once
    T = [[0.0] * n for _ in range(n)]
    for i in range(n):
        T[i][i] = 1.0
        for j in range(i + 1, n):
            t = DataStructs.TanimotoSimilarity(fps[i], fps[j])
            T[i][j] = T[j][i] = t
    vals = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        tot = 0.0
        cnt = 0
        for a in range(n):
            for b in range(a + 1, n):
                tot += T[idx[a]][idx[b]]
                cnt += 1
        if cnt == 0:
            continue
        vals.append(1.0 - tot / cnt)
    vals.sort()
    lo = vals[int(0.025 * len(vals))]
    hi = vals[int(0.975 * len(vals))]
    return round(lo, 6), round(hi, 6)


# ---- provenance: read molecules from the hash-locked prior grammar receipt ----
grammar_bytes = GRAMMAR_DIAG.read_bytes()
grammar_sha = sha(grammar_bytes)
grammar_diag = json.loads(grammar_bytes)
accepted = grammar_diag["accepted_proposals"]

records = []
fps = []
for a in accepted:
    smi = a["canonical_smiles"]
    mol, fp = morgan(smi)
    assert mol is not None, f"unparseable SMILES from prior receipt: {smi}"
    real = murcko_real(mol)
    gen = murcko_generic(mol)
    records.append({
        "name": a["name"],
        "family": a["family"],
        "canonical_smiles": smi,
        "n_rings": Chem.rdMolDescriptors.CalcNumRings(mol),
        "murcko_real_scaffold": real,
        "murcko_generic_framework": gen,
        "acyclic": (real == ""),
    })
    fps.append(fp)

N = len(records)

# ---- Bemis-Murcko scaffold diversity ----
real_scaffolds = [r["murcko_real_scaffold"] for r in records if not r["acyclic"]]
gen_frameworks = [r["murcko_generic_framework"] for r in records if not r["acyclic"]]
n_acyclic = sum(1 for r in records if r["acyclic"])
n_ring = N - n_acyclic
uniq_real = sorted(set(real_scaffolds))
uniq_gen = sorted(set(gen_frameworks))

# per-family framework spread
fam_frameworks = {}
for r in records:
    fam_frameworks.setdefault(r["family"], set())
    if not r["acyclic"]:
        fam_frameworks[r["family"]].add(r["murcko_generic_framework"])
fam_table = {f: {"n_members": sum(1 for r in records if r["family"] == f),
                 "n_unique_generic_frameworks": len(fams),
                 "n_acyclic": sum(1 for r in records if r["family"] == f and r["acyclic"])}
             for f, fams in fam_frameworks.items()}

# ---- internal diversity ----
mean_tan, n_pairs = mean_pairwise_tanimoto(fps)
intdiv1 = intdiv_p(fps, 1)
intdiv2 = intdiv_p(fps, 2)
ci_lo, ci_hi = bootstrap_ci_intdiv1(fps, BOOT_SEED, BOOT_N)

# ---- metric self-tests (known answers) ----
self_tests = {}
# T1: identical molecules -> mean pairwise Tanimoto == 1, IntDiv1 == 0
_, fpb = morgan("c1ccccc1")
mt_id, _ = mean_pairwise_tanimoto([fpb, fpb, fpb])
self_tests["identical_set_intdiv1_is_zero"] = (abs((1.0 - mt_id)) < 1e-12)
# T2: Tanimoto self-similarity == 1 and symmetry
_, fx = morgan("CCO")
_, fy = morgan("CCN")
txx = DataStructs.TanimotoSimilarity(fx, fx)
txy = DataStructs.TanimotoSimilarity(fx, fy)
tyx = DataStructs.TanimotoSimilarity(fy, fx)
self_tests["tanimoto_self_is_one"] = (abs(txx - 1.0) < 1e-12)
self_tests["tanimoto_symmetric"] = (abs(txy - tyx) < 1e-12)
self_tests["tanimoto_in_unit_interval"] = (0.0 <= txy <= 1.0)
# T3: Bemis-Murcko known answer: toluene -> benzene framework
mtol = Chem.MolFromSmiles("Cc1ccccc1")
self_tests["murcko_toluene_is_benzene"] = (murcko_real(mtol) == Chem.CanonSmiles("c1ccccc1"))
# T4: acyclic alkane -> empty Murcko scaffold
mhex = Chem.MolFromSmiles("CCCCCC")
self_tests["murcko_acyclic_is_empty"] = (murcko_real(mhex) == "")
# T5: IntDiv2 <= IntDiv1 (power-mean inequality; higher p penalizes matches more)
self_tests["intdiv2_le_intdiv1"] = (intdiv2 <= intdiv1 + 1e-9)
self_tests_all_pass = all(self_tests.values())

# ---- fail-closed discrimination controls ----
# C1: collapsed set = 10 identical molecules -> IntDiv1 == 0 (metric detects zero diversity)
_, fdup = morgan("CC1(C)CC(N)CC(C)(CN)C1")  # IPDA
dup_set = [fdup] * 10
mt_dup, _ = mean_pairwise_tanimoto(dup_set)
control_collapsed_intdiv1 = round(1.0 - mt_dup, 6)
# C2: homologous acyclic diamine series -> generic-framework diversity collapses to 1 empty framework
homolog_smiles = [r["canonical_smiles"] for r in records
                  if r["family"] == "F2_alpha_omega_diamine"]
homolog_frameworks = set()
for s in homolog_smiles:
    m = Chem.MolFromSmiles(s)
    homolog_frameworks.add(murcko_generic(m))
control_homolog_unique_frameworks = len(homolog_frameworks)
control_homolog_n = len(homolog_smiles)
# discrimination: full-set IntDiv1 must be materially above the collapsed control
discrimination_ok = (intdiv1 - control_collapsed_intdiv1) > 0.20
homolog_collapse_ok = (control_homolog_unique_frameworks == 1)

diag = {
    "schema": "amphora.molecule-generator.scaffold-diversity-diagnostic.v1",
    "study_id": "molgen-scaffold-diversity-v1",
    "purpose": ("Characterize the chemical-space DIVERSITY (Bemis-Murcko scaffold "
                "spread + MOSES internal diversity IntDiv_p) of the deterministic-"
                "grammar accepted-proposal set; the third generation-quality pillar "
                "not closed by the prior yield/feasibility/novelty receipts."),
    "authority": "AUDIT_ONLY",
    "rdkit_version": Chem.rdBase.rdkitVersion,
    "fingerprint": {"type": "Morgan/ECFP", "radius": FP_RADIUS, "n_bits": FP_NBITS,
                    "tanimoto": "binary Tanimoto coefficient"},
    "provenance": {
        "molecules_sourced_from": str(GRAMMAR_DIAG.relative_to(ROOT)),
        "source_diagnostic_sha256": grammar_sha,
        "n_molecules": N,
        "non_circular": ("SMILES read verbatim from hash-locked prior receipt; "
                         "scaffolds and fingerprints independently re-derived; no "
                         "prior yield/feasibility metric used as an input."),
    },
    "scaffold_diversity_bemis_murcko": {
        "n_molecules": N,
        "n_acyclic_empty_framework": n_acyclic,
        "n_ring_containing": n_ring,
        "n_unique_real_scaffolds_ring_only": len(uniq_real),
        "n_unique_generic_frameworks_ring_only": len(uniq_gen),
        "scaffold_diversity_ring_only": round(len(uniq_gen) / n_ring, 6) if n_ring else None,
        "unique_generic_frameworks": uniq_gen,
        "per_family": fam_table,
        "interpretation": ("Grammar spans multiple distinct ring frameworks among "
                           "ring-containing families; the aliphatic homolog families "
                           "are diverse in chain length but share the empty framework, "
                           "so IntDiv (fingerprint) rather than scaffold count captures "
                           "their diversity."),
    },
    "internal_diversity_moses": {
        "n_distinct_pairs": n_pairs,
        "mean_pairwise_tanimoto": round(mean_tan, 6),
        "intdiv_1": round(intdiv1, 6),
        "intdiv_2": round(intdiv2, 6),
        "intdiv_1_bootstrap95_ci": [ci_lo, ci_hi],
        "bootstrap_seed": BOOT_SEED,
        "bootstrap_resamples": BOOT_N,
        "definition": "IntDiv_p = 1 - (mean_{i<j} Tanimoto(i,j)^p)^(1/p) (Polykovskiy 2020)",
    },
    "metric_self_tests": self_tests,
    "metric_self_tests_all_pass": self_tests_all_pass,
    "fail_closed_discrimination": {
        "collapsed_10_identical_intdiv1": control_collapsed_intdiv1,
        "collapsed_control_is_zero": (control_collapsed_intdiv1 == 0.0),
        "full_set_intdiv1": round(intdiv1, 6),
        "full_vs_collapsed_gap_exceeds_0p20": discrimination_ok,
        "homolog_series_n": control_homolog_n,
        "homolog_series_unique_generic_frameworks": control_homolog_unique_frameworks,
        "homolog_series_collapses_to_single_empty_framework": homolog_collapse_ok,
        "all_controls_pass": (control_collapsed_intdiv1 == 0.0 and discrimination_ok
                              and homolog_collapse_ok),
    },
    "per_molecule": records,
    "theory_reference": {
        "scaffold_framework": "Bemis & Murcko 1996 J. Med. Chem. 39(15):2887-2893 DOI 10.1021/jm9602928",
        "internal_diversity_and_scaffold_metrics": "Polykovskiy et al. 2020 Front. Pharmacol. 11:565644 (MOSES)",
        "fingerprint": "Rogers & Hahn 2010 J. Chem. Inf. Model. 50(5):742-754 (ECFP)",
        "similarity_coefficient": "Bajusz, Racz & Heberger 2015 J. Cheminform. 7:20 (Tanimoto)",
        "confidence_interval": "Efron 1979 Ann. Statist. 7(1):1-26 (bootstrap)",
        "toolkit": f"RDKit {Chem.rdBase.rdkitVersion} MurckoScaffold + Morgan fingerprints",
    },
    "hypothesis_evaluation": {
        "hypothesis": ("The deterministic grammar's accepted proposals span a "
                       "diverse region of chemical space (not trivially inflated "
                       "variants of a single scaffold)."),
        "verdict": "CORROBORATED_IN_AUDIT_INSTRUMENT" if (self_tests_all_pass and
                   intdiv1 > 0.5 and len(uniq_gen) >= 3) else "PARTIAL",
        "caveats": [
            "AUDIT_ONLY: module runtime stays LOCKED_INTERNAL; no proposals emitted.",
            "Diversity is measured over the fixed enumerated accepted set; it is not a "
            "prospective discovery-space-coverage claim.",
            "Bemis-Murcko scaffold count is defined only for ring-containing members; "
            "aliphatic homolog diversity is captured by IntDiv, not scaffold count.",
            "Fingerprint/Tanimoto diversity is a structural proxy, not a property- or "
            "performance-diversity guarantee.",
        ],
    },
    "rights_posture": {
        "input_smiles": "derived from prior AUDIT_ONLY grammar receipt (published scaffold families)",
        "methods": "all baselines are published literature; RDKit is BSD-licensed",
        "external_dataset_used": False,
    },
    "non_circularity": ("Molecules sourced from hash-locked prior receipt; diversity "
                        "metrics computed by an independent RDKit code path; self-tests "
                        "anchor each metric to a known answer; discrimination controls "
                        "show the metrics fail closed on collapsed/homologous inputs."),
    "closes": [],
    "does_not_close": [
        "Runtime remains LOCKED_INTERNAL; no proposal emission enabled.",
        "No Phase-0 promotion; scientific_readiness stays UNVALIDATED.",
        "Structural/fingerprint diversity is not a property, FTO, or wet-lab claim.",
        "Diversity does not assert per-member synthetic accessibility beyond the prior SA<6 gate.",
    ],
    "hash_and_count_lock": {
        "n_molecules": N,
        "source_diagnostic_sha256": grammar_sha,
        "n_unique_generic_frameworks_ring_only": len(uniq_gen),
    },
    "headline": (
        f"Chemical-space diversity of the {N} deterministic-grammar accepted hardener "
        f"proposals: MOSES IntDiv_1={intdiv1:.4f} (bootstrap95 [{ci_lo:.4f},{ci_hi:.4f}]), "
        f"IntDiv_2={intdiv2:.4f}, mean pairwise Tanimoto {mean_tan:.4f} over {n_pairs} pairs "
        f"(Morgan r{FP_RADIUS}/{FP_NBITS}); Bemis-Murcko yields {len(uniq_gen)} distinct generic "
        f"ring frameworks over {n_ring} ring-containing members ({n_acyclic} acyclic share the "
        f"empty framework); metric self-tests {sum(self_tests.values())}/{len(self_tests)} pass; "
        f"discrimination controls fail closed (10-identical IntDiv_1={control_collapsed_intdiv1}, "
        f"homolog series collapses to {control_homolog_unique_frameworks} framework)."
    ),
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(diag, indent=2, sort_keys=True))
print("WROTE", OUT)
print("diagnostic_sha256", sha(OUT.read_bytes()))
print("intdiv1", intdiv1, "intdiv2", intdiv2, "mean_tan", mean_tan)
print("uniq_generic_frameworks", len(uniq_gen), "acyclic", n_acyclic, "ring", n_ring)
print("self_tests_all_pass", self_tests_all_pass)
print("controls_all_pass", diag["fail_closed_discrimination"]["all_controls_pass"])
print("verdict", diag["hypothesis_evaluation"]["verdict"])
