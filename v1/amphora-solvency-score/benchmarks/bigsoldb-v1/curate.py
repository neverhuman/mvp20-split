"""BigSolDB 2.1 curation for the Amphora solvency Phase-0 locked benchmark.

Real data: BigSolDB 2.1 (Zenodo record 18552681, CC-BY-4.0).
Citation: Krasnov et al., Sci Data 12 (2025), doi:10.1038/s41597-025-05559-8.
Raw file MD5 (verified against Zenodo manifest): c0875f6feaf5b063557ede5541c09647

Curation policy (fail-closed):
  - drop rows with missing LogS(mol/L) target
  - RDKit-sanitize + canonicalize solute and solvent SMILES; rows that fail are
    REJECTED (counted, never imputed)
  - collapse replicate (solute, solvent, T-bin) measurements to the median;
    replicate spread is retained as an empirical noise estimate
  - temperature must parse and lie in the dataset's stated 243-426 K range
Outputs: curated parquet + JSON curation receipt with row-level accounting.
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
import rdkit

RDLogger.DisableLog("rdApp.*")

RAW = Path("artifacts/bigsoldb-v2/BigSolDBv2.1.csv")
OUT_DIR = Path("amphora-solvency-score/benchmarks/bigsoldb-v1")
TARGET = "LogS(mol/L)"
T_MIN, T_MAX = 243.0, 426.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canon(smiles: str):
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol)


def main() -> None:
    raw_sha = sha256(RAW)
    df = pd.read_csv(RAW)
    n_raw = len(df)

    reject = {}

    m = df[TARGET].notna()
    reject["missing_target"] = int((~m).sum())
    df = df[m].copy()

    m = df["Temperature_K"].between(T_MIN, T_MAX)
    reject["temperature_out_of_range"] = int((~m).sum())
    df = df[m].copy()

    for col, out in (("SMILES_Solute", "solute_canon"), ("SMILES_Solvent", "solvent_canon")):
        uniq = {s: canon(s) for s in df[col].unique()}
        df[out] = df[col].map(uniq)
    bad = df["solute_canon"].isna() | df["solvent_canon"].isna()
    reject["rdkit_sanitization_failure"] = int(bad.sum())
    df = df[~bad].copy()

    # replicate collapse: same solute, solvent, and temperature rounded to 1 K
    df["t_bin"] = df["Temperature_K"].round(0)
    grp = df.groupby(["solute_canon", "solvent_canon", "t_bin"], sort=False)
    rep_spread = grp[TARGET].std(ddof=1).dropna()
    curated = grp.agg(
        temperature_k=("Temperature_K", "median"),
        logs=(TARGET, "median"),
        n_replicates=(TARGET, "size"),
        n_sources=("Source", "nunique"),
        solvent_name=("Solvent", "first"),
    ).reset_index()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    curated_path = OUT_DIR / "curated.parquet"
    curated.to_parquet(curated_path, index=False)

    receipt = {
        "benchmark": "amphora-solvency-score/bigsoldb-v1",
        "stage": "curation",
        "raw_file": str(RAW),
        "raw_sha256": raw_sha,
        "raw_rows": n_raw,
        "rights": {
            "license": "CC-BY-4.0",
            "source": "https://zenodo.org/records/18552681",
            "citation": "Krasnov et al., Sci Data 12 (2025), doi:10.1038/s41597-025-05559-8",
        },
        "rejects": reject,
        "curated_rows": int(len(curated)),
        "unique_solutes": int(curated["solute_canon"].nunique()),
        "unique_solvents": int(curated["solvent_canon"].nunique()),
        "replicate_groups_with_spread": int(len(rep_spread)),
        "replicate_logs_std_median": float(rep_spread.median()),
        "replicate_logs_std_p90": float(rep_spread.quantile(0.9)),
        "curated_sha256": sha256(curated_path),
        "versions": {
            "python": sys.version.split()[0],
            "rdkit": rdkit.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
    }
    with open(OUT_DIR / "curation_receipt.json", "w") as f:
        json.dump(receipt, f, indent=2)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
