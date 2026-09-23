#!/usr/bin/env python3
"""V1-SOLV (campaign): fair re-run of the ML-vs-classical-theory chi comparison
using the R-B03 corrected Fedors/Van-Krevelen group-contribution instrument
(benchmarks/flory-hansen-corrected-v1/compute_group_contribution.py) as the
physics arm, on the SAME OMG chi corpus and SAME 60/20/20 scaffold-safe split
methodology and SAME ML model family as the two W7-refuted KPIs:
  evidence/phase0/kpis/omg-chi-flory-huggins-physical-baseline-vs-ml-kpi.v1.json
  evidence/phase0/kpis/omg-chi-hansen-3component-physical-baseline-vs-ml-kpi.v1.json

R-B03 (2026-08-03) rebuilt the physics instrument with fail-closed coverage
gates but explicitly deferred this re-run ("W7b"). This script closes W7b.

Corpus / labels: identical to R-B03's run_omg_sample.py (same rights-checked
file, same SMILES column methyl_terminated_product, same 3 chi targets).

ML arm: identical model family + hyperparameters to the parent scientific
receipt reference/mvp20/data/omg_chi_parameter_model_receipt.v1.json (sha256
858db5b211f268b6239340e00cadde4dbd203c653276d7bdd456b1dbde0a0711):
  HistGradientBoostingRegressor(max_iter=500, learning_rate=0.05, max_depth=8,
  min_samples_leaf=25, l2_regularization=0.1), 528 features = 16 RDKit
  descriptors (MW, LogP, TPSA, HBA, HBD, RotB, AromRings, HeavyAtoms, NAtomsN,
  NAtomsO, NAtomsS, NAtomsHal, FCsp3, NumRings, AromHetero, AliphaticRings)
  + 512-bit Morgan fingerprint radius 2. rdkit 2026.03.2, sklearn 1.7.2
  (both version-pinned identical to the parent receipt).

Split: 60/20/20 scaffold-safe partition by unique Bemis-Murcko generic
scaffold, seed 0 (matches "split_methodology" of both refuted KPIs).

Deliberate scope reduction (documented, not hidden): this fire draws a
deterministic seed-0 sample of N_SAMPLE unique chi-labeled SMILES from the
265,721-molecule pool (same pool R-B03 sampled from), rather than the full
pool, to keep the ML fit + 528-feature extraction synchronous within a
single-hour cron budget. All accounting is honest at whatever scale is run.

Physics-arm accounting (fail-closed, never zero-filled): each test molecule
is RETURNED / ABSTAINED / REJECTED by the R-B03 instrument. R-squared for the
physics baselines (B1 pure, B2 rescaled) is computed ONLY over RETURNED test
molecules; abstained/rejected molecules are excluded and counted, never
imputed. B0 (constant) and B3 (ML) are reported both on the full test set
(matching the original KPIs' framing) AND on the physics-covered subset (for
a like-for-like head-to-head against the physics arm on the same molecules).
"""
import gzip
import hashlib
import json
import math
import random
import statistics
import sys
import time

sys.path.insert(0, "/home/ubuntu/amphora/build/mvp20-split/amphora-solvency-score/benchmarks/flory-hansen-corrected-v1")
import compute_group_contribution as gc  # noqa: E402

from rdkit import Chem, RDLogger  # noqa: E402
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors  # noqa: E402
from rdkit.Chem.Scaffolds import MurckoScaffold  # noqa: E402
from sklearn.ensemble import HistGradientBoostingRegressor  # noqa: E402
from sklearn.metrics import r2_score  # noqa: E402

RDLogger.DisableLog("rdApp.*")

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
CORPUS = ROOT + "/feedback/v3/normalized/omg_physical_properties_v3.jsonl.gz"
MANIFEST = ROOT + "/amphora-solvency-score/reference/mvp20/data/feedback_v3/manifests/omg_physical_properties_v3.json"
SEED = 0
N_SAMPLE = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
CHI_FIELDS = {
    "chloroform": "chi_parameter_chloroform_mean",
    "ethanol": "chi_parameter_ethanol_mean",
    "water": "chi_parameter_water_mean",
}
R_GAS = 8.314  # J/mol/K
T_REF = 298.15  # K

# Barton 1991 CRC Handbook of Solubility Parameters (same values the
# refuted receipts cited; solvent-side published constants, not the broken
# generator this repair replaces).
SOLVENT_HILDEBRAND = {
    "water": {"delta": 47.9, "V": 18.07},
    "ethanol": {"delta": 26.5, "V": 58.68},
    "chloroform": {"delta": 18.9, "V": 80.65},
}
# Hansen 2007 Handbook of Solubility Parameters, 2nd ed., Table A.1 (same
# handbook R-B03's anchors already cite for ethanol/water; chloroform value
# is the same handbook's standard tabulated entry).
SOLVENT_HANSEN = {
    "water": {"d": 15.5, "p": 16.0, "h": 42.3, "V": 18.07},
    "ethanol": {"d": 15.8, "p": 8.8, "h": 19.4, "V": 58.68},
    "chloroform": {"d": 17.8, "p": 3.1, "h": 5.7, "V": 80.65},
}

DESCRIPTOR_NAMES = [
    "MW", "LogP", "TPSA", "HBA", "HBD", "RotB", "AromRings", "HeavyAtoms",
    "NAtomsN", "NAtomsO", "NAtomsS", "NAtomsHal", "FCsp3", "NumRings",
    "AromHetero", "AliphaticRings",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def load_sample():
    man = json.load(open(MANIFEST))
    assert man["rights_class"] == "DERIVATIVE_ALLOWED", "rights lock not clean"
    assert man["quarantined"] is False, "corpus quarantined"
    corpus_sha = sha256_file(CORPUS)
    assert corpus_sha == man["normalized_sha256"], "corpus bytes do not match manifest lock"
    smi_to_chi = {}
    n_records = 0
    n_chi_records = 0
    with gzip.open(CORPUS, "rt") as f:
        for line in f:
            n_records += 1
            rec = json.loads(line)
            rf = rec.get("raw_fields") or {}
            smi = rf.get("methyl_terminated_product")
            if not smi:
                continue
            if not all(rf.get(v) not in (None, "") for v in CHI_FIELDS.values()):
                continue
            n_chi_records += 1
            if smi not in smi_to_chi:
                smi_to_chi[smi] = {
                    k: float(rf[v]) for k, v in CHI_FIELDS.items()
                }
    pool = sorted(smi_to_chi.keys())
    rng = random.Random(SEED)
    sample = rng.sample(pool, min(N_SAMPLE, len(pool)))
    prov = {
        "corpus_path": CORPUS,
        "corpus_sha256": corpus_sha,
        "manifest_rights_class": man["rights_class"],
        "manifest_quarantined": man["quarantined"],
        "dataset_id": man["dataset_id"],
        "n_records_streamed": n_records,
        "n_chi_records": n_chi_records,
        "n_unique_smiles_chi_labeled": len(pool),
        "seed": SEED,
        "n_sample": len(sample),
    }
    return prov, sample, smi_to_chi


def murcko_scaffold(smi):
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return None
    try:
        scaf = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaf) if scaf is not None else ""
    except Exception:
        return ""


def scaffold_safe_split(smiles_list, seed=0, fracs=(0.6, 0.2, 0.2)):
    groups = {}
    for smi in smiles_list:
        scaf = murcko_scaffold(smi) or "__NONE__:" + smi
        groups.setdefault(scaf, []).append(smi)
    scaf_keys = sorted(groups.keys())
    rng = random.Random(seed)
    rng.shuffle(scaf_keys)
    n_total = len(smiles_list)
    n_train_target = int(round(fracs[0] * n_total))
    n_val_target = int(round(fracs[1] * n_total))
    train, val, test = [], [], []
    for k in scaf_keys:
        members = groups[k]
        if len(train) < n_train_target:
            train.extend(members)
        elif len(val) < n_val_target:
            val.extend(members)
        else:
            test.extend(members)
    return train, val, test, len(groups)


def compute_descriptors(mol):
    fcsp3 = rdMolDescriptors.CalcFractionCSP3(mol)
    ri = mol.GetRingInfo()
    n_arom_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
    n_aliphatic_rings = rdMolDescriptors.CalcNumAliphaticRings(mol)
    n_arom_hetero = rdMolDescriptors.CalcNumAromaticHeterocycles(mol)
    halogens = {9, 17, 35, 53}
    n_n = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 7)
    n_o = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 8)
    n_s = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 16)
    n_hal = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() in halogens)
    return [
        Descriptors.MolWt(mol),
        Descriptors.MolLogP(mol),
        Descriptors.TPSA(mol),
        rdMolDescriptors.CalcNumHBA(mol),
        rdMolDescriptors.CalcNumHBD(mol),
        rdMolDescriptors.CalcNumRotatableBonds(mol),
        n_arom_rings,
        mol.GetNumHeavyAtoms(),
        n_n, n_o, n_s, n_hal,
        fcsp3,
        ri.NumRings(),
        n_arom_hetero,
        n_aliphatic_rings,
    ]


def featurize(smi, cache={}):
    if smi in cache:
        return cache[smi]
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        cache[smi] = None
        return None
    desc = compute_descriptors(mol)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=512)
    bits = [int(b) for b in fp.ToBitString()]
    vec = desc + bits
    cache[smi] = vec
    return vec


def r2_or_none(y_true, y_pred):
    if len(y_true) < 2:
        return None
    return float(r2_score(y_true, y_pred))


def pearson_or_none(a, b):
    if len(a) < 2 or statistics.pstdev(a) == 0 or statistics.pstdev(b) == 0:
        return None
    n = len(a)
    ma = sum(a) / n
    mb = sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va == 0 or vb == 0:
        return None
    return cov / math.sqrt(va * vb)


def fit_rescale(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sxx = sum((xi - mx) ** 2 for xi in x)
    if sxx == 0:
        return 0.0, my
    sxy = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    slope = sxy / sxx
    intercept = my - slope * mx
    return slope, intercept


def main(out_path):
    t0 = time.time()
    prov, sample, smi_to_chi = load_sample()

    train, val, test, n_scaffolds = scaffold_safe_split(sample, seed=SEED)
    split_prov = {
        "n_total": len(sample), "n_train": len(train), "n_val": len(val),
        "n_test": len(test), "n_scaffolds": n_scaffolds,
        "train_frac": len(train) / len(sample), "val_frac": len(val) / len(sample),
        "test_frac": len(test) / len(sample),
        "method": "scaffold-safe 60/20/20 by unique Bemis-Murcko generic scaffold, seed=0",
    }

    # physics arm: R-B03 corrected instrument, per molecule
    phys = {smi: gc.compute(smi) for smi in sample}

    def account(subset, method):
        c = {"RETURNED": 0, "ABSTAINED": 0, "REJECTED": 0}
        reasons = {}
        for smi in subset:
            s = phys[smi][method + "_status"]
            if s == gc.RETURNED:
                c["RETURNED"] += 1
            elif s.startswith("ABSTAINED"):
                c["ABSTAINED"] += 1
                reasons[s] = reasons.get(s, 0) + 1
            else:
                c["REJECTED"] += 1
                reasons[s] = reasons.get(s, 0) + 1
        c["reasons"] = reasons
        c["identity_returned_plus_abstained_plus_rejected"] = c["RETURNED"] + c["ABSTAINED"] + c["REJECTED"]
        c["identity_equals_n"] = c["identity_returned_plus_abstained_plus_rejected"] == len(subset)
        c["coverage_rate"] = c["RETURNED"] / len(subset) if subset else None
        return c

    accounting = {
        "fedors_train": account(train, "fedors"), "fedors_test": account(test, "fedors"),
        "hansen_train": account(train, "hansen"), "hansen_test": account(test, "hansen"),
    }

    # ML feature matrix (all sample molecules; ML arm does not require physics coverage)
    print("featurizing...", time.time() - t0, file=sys.stderr)
    X = {smi: featurize(smi) for smi in sample}
    bad = [smi for smi, v in X.items() if v is None]
    assert not bad, "rdkit failed to parse %d SMILES that passed the physics instrument's own parser" % len(bad)

    X_train = [X[s] for s in train]
    X_test = [X[s] for s in test]

    results = {"flory_huggins_hildebrand": {}, "hansen_3component": {}}

    for solvent in ("water", "ethanol", "chloroform"):
        y_train = [smi_to_chi[s][solvent] for s in train]
        y_test = [smi_to_chi[s][solvent] for s in test]

        print("training HistGBM", solvent, time.time() - t0, file=sys.stderr)
        model = HistGradientBoostingRegressor(
            max_iter=500, learning_rate=0.05, max_depth=8,
            min_samples_leaf=25, l2_regularization=0.1, random_state=SEED,
        )
        model.fit(X_train, y_train)
        pred_test_full = model.predict(X_test)
        ml_r2_full_test = r2_or_none(y_test, pred_test_full)

        train_mean = sum(y_train) / len(y_train)
        b0_full_test = r2_or_none(y_test, [train_mean] * len(y_test))

        # ---- Hildebrand/Flory-Huggins arm ----
        cov_test_idx = [i for i, s in enumerate(test) if phys[s]["fedors_status"] == gc.RETURNED]
        cov_train_idx = [i for i, s in enumerate(train) if phys[s]["fedors_status"] == gc.RETURNED]
        hild = {"solvent": solvent}
        hild["n_test_total"] = len(test)
        hild["n_test_covered"] = len(cov_test_idx)
        hild["coverage_rate_test"] = len(cov_test_idx) / len(test) if test else None
        if cov_test_idx:
            sp = SOLVENT_HILDEBRAND[solvent]
            fh_pred_test = [
                sp["V"] * (phys[test[i]]["values"]["fedors_delta_total"] - sp["delta"]) ** 2 / (R_GAS * T_REF) + 0.34
                for i in cov_test_idx
            ]
            y_cov_test = [y_test[i] for i in cov_test_idx]
            b0_cov = r2_or_none(y_cov_test, [train_mean] * len(y_cov_test))
            b1_r2 = r2_or_none(y_cov_test, fh_pred_test)
            b1_pearson = pearson_or_none(fh_pred_test, y_cov_test)
            fh_pred_train = [
                sp["V"] * (phys[train[i]]["values"]["fedors_delta_total"] - sp["delta"]) ** 2 / (R_GAS * T_REF) + 0.34
                for i in cov_train_idx
            ]
            y_cov_train = [y_train[i] for i in cov_train_idx]
            if len(cov_train_idx) >= 2:
                slope, intercept = fit_rescale(fh_pred_train, y_cov_train)
                b2_pred_test = [slope * v + intercept for v in fh_pred_test]
                b2_r2 = r2_or_none(y_cov_test, b2_pred_test)
            else:
                slope = intercept = None
                b2_r2 = None
            ml_pred_cov_test = [pred_test_full[i] for i in cov_test_idx]
            b3_r2_cov = r2_or_none(y_cov_test, ml_pred_cov_test)
            hild.update({
                "b0_constant_r2_on_covered": b0_cov,
                "b1_pure_r2": b1_r2, "b1_pure_pearson_r": b1_pearson,
                "b2_rescaled_r2": b2_r2, "b2_slope": slope, "b2_intercept": intercept,
                "b3_ml_r2_on_covered_subset": b3_r2_cov,
                "b3_ml_r2_on_full_test": ml_r2_full_test,
                "ml_beats_pure_gap": (b3_r2_cov - b1_r2) if (b3_r2_cov is not None and b1_r2 is not None) else None,
                "ml_beats_rescaled_gap": (b3_r2_cov - b2_r2) if (b3_r2_cov is not None and b2_r2 is not None) else None,
                "rescaled_beats_pure_gap": (b2_r2 - b1_r2) if (b2_r2 is not None and b1_r2 is not None) else None,
            })
        else:
            hild.update({"b0_constant_r2_on_covered": None, "b1_pure_r2": None,
                         "b2_rescaled_r2": None, "b3_ml_r2_on_covered_subset": None,
                         "b3_ml_r2_on_full_test": ml_r2_full_test})
        results["flory_huggins_hildebrand"][solvent] = hild

        # ---- Hansen 3-component arm ----
        cov_test_idx_h = [i for i, s in enumerate(test) if phys[s]["hansen_status"] == gc.RETURNED]
        cov_train_idx_h = [i for i, s in enumerate(train) if phys[s]["hansen_status"] == gc.RETURNED]
        hansen = {"solvent": solvent}
        hansen["n_test_total"] = len(test)
        hansen["n_test_covered"] = len(cov_test_idx_h)
        hansen["coverage_rate_test"] = len(cov_test_idx_h) / len(test) if test else None
        if cov_test_idx_h:
            sh = SOLVENT_HANSEN[solvent]

            def ra2(vals):
                return (4.0 * (vals["hansen_delta_d"] - sh["d"]) ** 2
                        + (vals["hansen_delta_p"] - sh["p"]) ** 2
                        + (vals["hansen_delta_h"] - sh["h"]) ** 2)

            hn_pred_test = [
                sh["V"] * ra2(phys[test[i]]["values"]) / 4.0 / (R_GAS * T_REF) + 0.34
                for i in cov_test_idx_h
            ]
            y_cov_test_h = [y_test[i] for i in cov_test_idx_h]
            b0_cov_h = r2_or_none(y_cov_test_h, [train_mean] * len(y_cov_test_h))
            b1_r2_h = r2_or_none(y_cov_test_h, hn_pred_test)
            b1_pearson_h = pearson_or_none(hn_pred_test, y_cov_test_h)
            hn_pred_train = [
                sh["V"] * ra2(phys[train[i]]["values"]) / 4.0 / (R_GAS * T_REF) + 0.34
                for i in cov_train_idx_h
            ]
            y_cov_train_h = [y_train[i] for i in cov_train_idx_h]
            if len(cov_train_idx_h) >= 2:
                slope_h, intercept_h = fit_rescale(hn_pred_train, y_cov_train_h)
                b2_pred_test_h = [slope_h * v + intercept_h for v in hn_pred_test]
                b2_r2_h = r2_or_none(y_cov_test_h, b2_pred_test_h)
            else:
                slope_h = intercept_h = None
                b2_r2_h = None
            ml_pred_cov_test_h = [pred_test_full[i] for i in cov_test_idx_h]
            b3_r2_cov_h = r2_or_none(y_cov_test_h, ml_pred_cov_test_h)
            hansen.update({
                "b0_constant_r2_on_covered": b0_cov_h,
                "b1_pure_r2": b1_r2_h, "b1_pure_pearson_r": b1_pearson_h,
                "b2_rescaled_r2": b2_r2_h, "b2_slope": slope_h, "b2_intercept": intercept_h,
                "b3_ml_r2_on_covered_subset": b3_r2_cov_h,
                "b3_ml_r2_on_full_test": ml_r2_full_test,
                "ml_beats_pure_gap": (b3_r2_cov_h - b1_r2_h) if (b3_r2_cov_h is not None and b1_r2_h is not None) else None,
                "ml_beats_rescaled_gap": (b3_r2_cov_h - b2_r2_h) if (b3_r2_cov_h is not None and b2_r2_h is not None) else None,
                "rescaled_beats_pure_gap": (b2_r2_h - b1_r2_h) if (b2_r2_h is not None and b1_r2_h is not None) else None,
            })
        else:
            hansen.update({"b0_constant_r2_on_covered": None, "b1_pure_r2": None,
                           "b2_rescaled_r2": None, "b3_ml_r2_on_covered_subset": None,
                           "b3_ml_r2_on_full_test": ml_r2_full_test})
        results["hansen_3component"][solvent] = hansen

    # admissibility spot-check: every physics value actually used is in-envelope
    out_of_envelope = []
    for smi, r in phys.items():
        for q, val in r["values"].items():
            lo = gc.ENVELOPE_MIN if q in ("fedors_delta_total", "hansen_delta_total", "hansen_delta_d") else 0.0
            if not (lo <= val <= gc.ENVELOPE_MAX):
                out_of_envelope.append({"smiles": smi, "q": q, "val": val})

    diag = {
        "schema": "amphora.solvency-score.ml-vs-physics-corrected-comparison-diagnostic.v1",
        "campaign_item_id": "V1-SOLV",
        "provenance": prov,
        "split": split_prov,
        "accounting": accounting,
        "out_of_envelope_returns": len(out_of_envelope),
        "descriptor_names": DESCRIPTOR_NAMES,
        "morgan_bits": 512, "morgan_radius": 2, "n_features": len(DESCRIPTOR_NAMES) + 512,
        "model_family": "HistGradientBoostingRegressor(max_iter=500, lr=0.05, depth=8, min_leaf=25, l2=0.1, random_state=0)",
        "solvent_hildebrand_barton1991": SOLVENT_HILDEBRAND,
        "solvent_hansen_2007_table_a1": SOLVENT_HANSEN,
        "reference_temperature_K": T_REF,
        "results": results,
    }
    assert not out_of_envelope, "out-of-envelope RETURNED value: %r" % out_of_envelope[:3]

    blob = canonical_json(diag).encode()
    with open(out_path, "wb") as f:
        f.write(blob)
    print(out_path, sha256_bytes(blob), "elapsed", time.time() - t0, file=sys.stderr)
    print(out_path, sha256_bytes(blob))


if __name__ == "__main__":
    main(sys.argv[2] if len(sys.argv) > 2 else "/tmp/ml_vs_physics_diag.json")
