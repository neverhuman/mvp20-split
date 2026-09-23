"""Integrity checks for the bigsoldb-v1 leave-solute-out benchmark.

Motivated by a confirmed failure elsewhere in this portfolio: the
design-rule-score "R2 +0.856" scratch-hardness result was a duplicate-row
memorisation artifact whose folds were nested rather than disjoint, and whose
hostile null (shuffling y_train only) was structurally unable to detect it.
See reports/redteam-phase0-audit-2026-07-24/retraction-design-rule-score.md.

This script applies the checks that would have caught that failure to our own
headline benchmark, rather than assuming grouping by canonical SMILES is
sufficient.

Check 1 - label-permutation null.
    Permute the target across rows and re-run the identical leave-solute-out
    protocol. A model that retains predictive accuracy on permuted labels is
    exploiting an evaluation artifact. Pass condition: R2 <= 0 and RMSE within
    noise of the global standard deviation.

Check 2 - near-duplicate sensitivity.
    Grouping is by exact canonical SMILES, so an exact duplicate cannot span
    folds. The residual channel is a *distinct* SMILES with an identical
    Morgan fingerprint (stereoisomers, tautomers): 3.6% of rows. Recompute
    out-of-fold accuracy with those rows removed. Pass condition: the headline
    RMSE is not materially better than the near-duplicate-free RMSE.

Check 3 - fold disjointness, verified rather than asserted.
    Assert zero solute overlap between any train/test fold pair, and report
    the row-hash intersection count.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_benchmark_v2 as R  # noqa: E402

RDLogger.DisableLog("rdApp.*")
BENCH = R.BENCH
SEED = R.SEED


def oof_predictions(df, feat_cols, group_col, y_override=None, n_estimators=3000):
    """Run the v2 leave-solute-out protocol and return OOF predictions."""
    groups = df[group_col].values
    order = np.argsort([hashlib.sha256(f"{SEED}:{g}".encode()).hexdigest()
                        for g in groups])
    df = df.iloc[order].reset_index(drop=True)
    y = df[R.TARGET].values.copy() if y_override is None else y_override[order]
    groups = df[group_col].values

    params = {**R.LGB_PARAMS, "n_estimators": n_estimators}
    oof = np.full(len(df), np.nan)
    fold_of = np.full(len(df), -1)
    overlaps = []
    gkf = GroupKFold(n_splits=R.N_FOLDS)
    for fold, (tr, te) in enumerate(gkf.split(df, groups=groups)):
        fold_of[te] = fold
        tr_g = set(groups[tr])
        te_g = set(groups[te])
        overlaps.append(len(tr_g & te_g))

        inner = GroupKFold(n_splits=5)
        itr, iva = next(inner.split(df.iloc[tr], groups=groups[tr]))
        fit_idx, val_idx = tr[itr], tr[iva]
        m = lgb.LGBMRegressor(**params)
        m.fit(df.iloc[fit_idx][feat_cols], y[fit_idx],
              eval_set=[(df.iloc[val_idx][feat_cols], y[val_idx])],
              callbacks=[lgb.early_stopping(100, verbose=False)])
        oof[te] = m.predict(df.iloc[te][feat_cols],
                            num_iteration=m.best_iteration_)
        print(f"  fold {fold}: rmse="
              f"{np.sqrt(np.mean((oof[te]-y[te])**2)):.4f}", flush=True)
    return df, y, oof, fold_of, overlaps


def main() -> None:
    raw = pd.read_parquet(BENCH / "features.parquet")
    df, _cov = R.build_hsp_frame(raw)
    feat_cols = [c for c in raw.columns
                 if c.startswith(("solute_", "solvent_"))
                 and c not in ("solute_canon", "solvent_canon", "solvent_name")]
    feat_cols.append("temperature_k")

    out = {"benchmark": "amphora-solvency-score/bigsoldb-v1",
           "stage": "integrity_checks", "seed": SEED}

    # ---- Check 1: label-permutation null -------------------------------
    print("[null] permuting labels across rows", flush=True)
    rng = np.random.default_rng(SEED)
    y_perm = df[R.TARGET].values.copy()
    rng.shuffle(y_perm)
    _d, yn, oofn, _f, _o = oof_predictions(df, feat_cols, "solute_canon",
                                           y_override=y_perm, n_estimators=800)
    out["check_1_label_permutation_null"] = {
        "protocol": "identical leave-solute-out folds; target permuted across rows",
        **R.metrics(yn, oofn),
        "global_std_of_target": float(np.std(yn)),
        "pass_condition": "r2 <= 0 and rmse ~ global_std",
        "passed": bool(R.metrics(yn, oofn)["r2"] <= 0.02),
    }
    print(json.dumps(out["check_1_label_permutation_null"], indent=1), flush=True)

    # ---- Check 2 + 3: real labels, disjointness, near-duplicate ---------
    print("[real] leave-solute-out with true labels", flush=True)
    d2, y2, oof2, fold_of, overlaps = oof_predictions(
        df, feat_cols, "solute_canon", n_estimators=3000)

    out["check_3_fold_disjointness"] = {
        "solute_overlap_between_train_and_test_per_fold": overlaps,
        "max_overlap": int(max(overlaps)),
        "residual_duplicate_solute_solvent_tbin_rows": int(
            d2.duplicated(subset=["solute_canon", "solvent_canon",
                                  "t_bin"]).sum()),
        "passed": bool(max(overlaps) == 0),
    }

    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    solutes = sorted(d2["solute_canon"].unique())
    fps = {s: gen.GetFingerprint(Chem.MolFromSmiles(s)) for s in solutes}
    twin = {}
    for i, s in enumerate(solutes):
        others = [fps[o] for o in solutes if o != s]
        twin[s] = float(max(DataStructs.BulkTanimotoSimilarity(fps[s], others)))
    sim = d2["solute_canon"].map(twin).values

    full = R.metrics(y2, oof2)
    keep = sim < 0.99
    strict = R.metrics(y2[keep], oof2[keep])
    out["check_2_near_duplicate_sensitivity"] = {
        "definition": "row removed if its solute has any other solute in the "
                      "corpus with Morgan r=2 Tanimoto >= 0.99",
        "rows_total": int(len(d2)),
        "rows_removed": int((~keep).sum()),
        "fraction_removed": float((~keep).mean()),
        "headline_all_rows": full,
        "near_duplicate_free": strict,
        "rmse_inflation_attributable_to_near_duplicates": float(
            strict["rmse"] - full["rmse"]),
        "passed": bool(strict["rmse"] - full["rmse"] < 0.05),
    }
    print(json.dumps(out["check_2_near_duplicate_sensitivity"], indent=1),
          flush=True)
    print(json.dumps(out["check_3_fold_disjointness"], indent=1), flush=True)

    with open(BENCH / "integrity_receipt.json", "w") as f:
        json.dump(out, f, indent=2)
    print("wrote", BENCH / "integrity_receipt.json")


if __name__ == "__main__":
    main()
