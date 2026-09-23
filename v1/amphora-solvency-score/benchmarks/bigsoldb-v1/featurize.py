"""Featurization for the bigsoldb-v1 solvency benchmark.

RDKit 2D physchem descriptors for solute and solvent + temperature.
Descriptor choice follows published practice on this dataset family
(fixed-descriptor models are at parity with learned GNN representations for
organic solubility; Attia et al., Nat. Commun. 2025, doi:10.1038/s41467-025-62717-7).
Descriptors are computed once per unique canonical SMILES and cached; any
molecule whose descriptor vector contains NaN/inf is rejected (fail-closed).
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors

RDLogger.DisableLog("rdApp.*")

BENCH = Path("amphora-solvency-score/benchmarks/bigsoldb-v1")

# Exclude descriptors that are constant-prone/IPC-unstable; keep a stable,
# versioned list recorded in the receipt.
EXCLUDE = {"Ipc"}
DESCRIPTORS = [(n, f) for n, f in Descriptors.descList if n not in EXCLUDE]


def desc_vector(smiles: str):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    vals = []
    for _, fn in DESCRIPTORS:
        try:
            vals.append(float(fn(mol)))
        except Exception:
            return None
    v = np.asarray(vals, dtype=np.float64)
    if not np.all(np.isfinite(v)):
        return None
    return v


def main() -> None:
    df = pd.read_parquet(BENCH / "curated.parquet")
    names = [n for n, _ in DESCRIPTORS]

    tables = {}
    rejected = {}
    for role, col in (("solute", "solute_canon"), ("solvent", "solvent_canon")):
        uniq = sorted(df[col].unique())
        rows, bad = [], []
        for s in uniq:
            v = desc_vector(s)
            if v is None:
                bad.append(s)
            else:
                rows.append((s, v))
        mat = pd.DataFrame([r[1] for r in rows], columns=[f"{role}_{n}" for n in names])
        mat.insert(0, col, [r[0] for r in rows])
        tables[role] = mat
        rejected[role] = bad

    feat = df.merge(tables["solute"], on="solute_canon", how="inner").merge(
        tables["solvent"], on="solvent_canon", how="inner"
    )
    n_dropped = len(df) - len(feat)

    out = BENCH / "features.parquet"
    feat.to_parquet(out, index=False)

    receipt = {
        "stage": "featurization",
        "descriptor_set": "rdkit.Chem.Descriptors.descList minus " + ",".join(sorted(EXCLUDE)),
        "n_descriptors_per_molecule": len(DESCRIPTORS),
        "descriptor_names_sha256": hashlib.sha256(",".join(names).encode()).hexdigest(),
        "rows_in": int(len(df)),
        "rows_out": int(len(feat)),
        "rows_dropped_failed_descriptors": int(n_dropped),
        "rejected_molecules": rejected,
        "features_sha256": hashlib.sha256(open(out, "rb").read()).hexdigest(),
        "python": sys.version.split()[0],
    }
    with open(BENCH / "featurization_receipt.json", "w") as f:
        json.dump(receipt, f, indent=2)
    print(json.dumps({k: receipt[k] for k in receipt if k != "rejected_molecules"}, indent=2))
    print("rejected:", {k: len(v) for k, v in rejected.items()})


if __name__ == "__main__":
    main()
