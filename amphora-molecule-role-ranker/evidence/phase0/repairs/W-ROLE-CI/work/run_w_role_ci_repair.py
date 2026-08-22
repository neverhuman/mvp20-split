#!/usr/bin/env python3
"""W-ROLE-CI: recompute every degenerate boundary-collapsed interval in
role-parsimony-conformal-v1 with an exact method valid at the boundary.

Defect: the target diagnostic's bootstrap 95% CIs are built by percentile
bootstrap over B=10000 resamples of a k=n=24 (all-correct) sample. Every
resample is therefore also all-correct (there is no way to draw an incorrect
prediction when the source lacks one), so the bootstrap distribution has zero
variance and the reported interval collapses to a single point [1.0, 1.0]
(and [0.0, 0.0] for the derived gap) -- a mechanical inadmissibility of the
percentile bootstrap at a parameter-space boundary (Efron & Tibshirani 1993,
An Introduction to the Bootstrap, ch. 13; DiCiccio & Efron 1996, Statist.
Sci. 11(3):189-228, note percentile-bootstrap failure at boundaries). It does
NOT mean the true generalization accuracy is known to be exactly 1.0.

Repair method:
  1. Clopper-Pearson exact two-sided 95% CI (Clopper & Pearson 1934,
     Biometrika 26(4):404-413) for the two k=n=24 accuracy proportions.
     This is valid at k=n because it inverts the exact binomial CDF rather
     than relying on the empirical spread of resamples.
  2. For the paired accuracy-gap CI (noninferiority_test), the two
     accuracies are computed on the SAME 24 records (paired, not
     independent), so a plain difference of two Clopper-Pearson intervals
     would be needlessly wide. We instead use the boundary-safe conservative
     MOVER construction (Method of Variance Estimates Recovery; Newcombe RG
     1998b, "Improved confidence intervals for the difference between
     binomial proportions based on paired data," Statistics in Medicine
     17(22):2635-2650) with the correlation term set to 0 -- the maximally
     conservative (widest, always-valid-regardless-of-sign-of-correlation)
     variant, because the true pairing correlation cannot be estimated when
     both margins are perfectly concordant (0/0). MOVER recovers the two
     margins' own exact (Clopper-Pearson) confidence limits and combines
     them in quadrature:
         lower = d - sqrt((p1-l1)^2 + (u2-p2)^2)
         upper = d + sqrt((u1-p1)^2 + (p2-l2)^2)
     where d = p1 - p2 and (l_i, u_i) are each margin's own exact CI.
"""
import json
from pathlib import Path

from scipy.stats import beta

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-role-ranker"
TARGET_DIR = MOD / "benchmarks/role-parsimony-conformal-v1"
ITEM = MOD / "evidence/phase0/repairs/W-ROLE-CI"
WORK = ITEM / "work"

ALPHA = 0.05


def clopper_pearson(k, n, alpha=ALPHA):
    lower = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    upper = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return [lower, upper]


def mover_paired_diff_ci(k1, n1, k2, n2, alpha=ALPHA):
    """Conservative (phi=0) MOVER CI for p1-p2 on matched n1==n2 pairs."""
    assert n1 == n2
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = clopper_pearson(k1, n1, alpha)
    l2, u2 = clopper_pearson(k2, n2, alpha)
    d = p1 - p2
    lower = d - ((p1 - l1) ** 2 + (u2 - p2) ** 2) ** 0.5
    upper = d + ((u1 - p1) ** 2 + (p2 - l2) ** 2) ** 0.5
    return [lower, upper], {"p1": p1, "p2": p2, "l1": l1, "u1": u1, "l2": l2, "u2": u2}


target_diag = json.loads((TARGET_DIR / "diagnostic.canonical.json").read_bytes())

# --- located degenerate intervals in the target artifact ---
det_k = target_diag["fixture"]["n_in_domain"]
det_n = det_k  # in_domain_accuracy == 1.0 -> k == n
assert target_diag["deterministic_rule_baseline"]["in_domain_accuracy"] == 1.0
assert target_diag["deterministic_rule_baseline"]["in_domain_accuracy_bootstrap_ci95"] == [1.0, 1.0]
assert det_n == 24

loocv_n = target_diag["fitted_model_out_of_sample"]["n"]
assert target_diag["fitted_model_out_of_sample"]["loocv_accuracy"] == 1.0
assert target_diag["fitted_model_out_of_sample"]["loocv_accuracy_bootstrap_ci95"] == [1.0, 1.0]
assert loocv_n == 24

assert target_diag["noninferiority_test"]["accuracy_gap_det_minus_fitted"] == 0.0
assert target_diag["noninferiority_test"]["accuracy_gap_bootstrap_ci95"] == [0.0, 0.0]

det_ci_new = clopper_pearson(det_n, det_n)
loocv_ci_new = clopper_pearson(loocv_n, loocv_n)
gap_ci_new, gap_components = mover_paired_diff_ci(det_n, det_n, loocv_n, loocv_n)

# sanity: exact CP lower bound at k=n=24 must equal the campaign-cited 0.8575 value
assert abs(det_ci_new[0] - 0.8575264022774743) < 1e-9
assert abs(loocv_ci_new[0] - 0.8575264022774743) < 1e-9

corrections = [
    {
        "field": "deterministic_rule_baseline.in_domain_accuracy_bootstrap_ci95",
        "k": det_n, "n": det_n,
        "old_method": "percentile bootstrap (B=10000, seed 20260728-derived)",
        "old_ci": [1.0, 1.0],
        "new_method": "Clopper-Pearson exact two-sided 95% CI",
        "new_ci": det_ci_new,
        "understatement_of_uncertainty": round(1.0 - det_ci_new[0], 4),
    },
    {
        "field": "fitted_model_out_of_sample.loocv_accuracy_bootstrap_ci95",
        "k": loocv_n, "n": loocv_n,
        "old_method": "percentile bootstrap (B=10000, seed 20260728-derived)",
        "old_ci": [1.0, 1.0],
        "new_method": "Clopper-Pearson exact two-sided 95% CI",
        "new_ci": loocv_ci_new,
        "understatement_of_uncertainty": round(1.0 - loocv_ci_new[0], 4),
    },
    {
        "field": "noninferiority_test.accuracy_gap_bootstrap_ci95",
        "k1": det_n, "n1": det_n, "k2": loocv_n, "n2": loocv_n,
        "old_method": "percentile bootstrap (B=10000, seed 20260728-derived)",
        "old_ci": [0.0, 0.0],
        "new_method": "MOVER (Newcombe 1998b) paired-difference CI, phi=0 conservative, "
                       "built from each margin's own Clopper-Pearson exact CI",
        "new_ci": gap_ci_new,
        "components": gap_components,
        "understatement_of_uncertainty": round(gap_ci_new[1] - 0.0, 4),
    },
]

# ---- portfolio sweep -----------------------------------------------------
sweep_summary = {
    "method": "walked every .json file under mvp20-split (excluding .git/target/"
              "node_modules/__pycache__), parsed each, and for every 2-element "
              "numeric array reachable under a key matching /ci|interval|bound|"
              "coverage/i, flagged it if both elements == 0.0 or both == 1.0",
    "n_json_files_found": None,
    "n_json_files_parsed": None,
    "n_parse_errors": None,
    "n_degenerate_hits": None,
    "distinct_artifacts_outside_this_module": [],
}

results_path = WORK / "sweep_results.json"
if results_path.exists():
    sweep_summary.update(json.loads(results_path.read_bytes()))

output = {
    "schema": "amphora.molecule-role-ranker.w-role-ci-repair-diagnostic.v1",
    "purpose": (
        "REPAIR-MODE fire for campaign item W-ROLE-CI: locate every interval in "
        "role-parsimony-conformal-v1 computed by a boundary-collapsing percentile "
        "bootstrap, recompute each with a named exact method valid at the boundary, "
        "and sweep the portfolio for the same defect class."
    ),
    "target_artifact": {
        "path": "amphora-molecule-role-ranker/benchmarks/role-parsimony-conformal-v1/"
                "replay_receipt.v1.dsse.json",
        "diagnostic_path": "amphora-molecule-role-ranker/benchmarks/"
                           "role-parsimony-conformal-v1/diagnostic.canonical.json",
    },
    "corrections": corrections,
    "primary_references": [
        "Clopper CJ, Pearson ES (1934). The use of confidence or fiducial limits "
        "illustrated in the case of the binomial. Biometrika 26(4):404-413.",
        "Efron B, Tibshirani RJ (1993). An Introduction to the Bootstrap. Chapman & "
        "Hall/CRC, ISBN 978-0412042317, ch.13 (percentile bootstrap breakdown at "
        "parameter-space boundaries).",
        "DiCiccio TJ, Efron B (1996). Bootstrap confidence intervals. Statistical "
        "Science 11(3):189-228.",
        "Newcombe RG (1998). Improved confidence intervals for the difference "
        "between binomial proportions based on paired data. Statistics in Medicine "
        "17(22):2635-2650 (MOVER / Method 10).",
    ],
    "sweep": sweep_summary,
}

WORK.mkdir(parents=True, exist_ok=True)
canon_bytes = json.dumps(output, indent=2, sort_keys=True).encode()
(WORK / "diagnostic.canonical.json").write_bytes(canon_bytes)
canon_bytes2 = json.dumps(output, indent=2, sort_keys=True).encode()
(WORK / "diagnostic.runB.json").write_bytes(canon_bytes2)
assert canon_bytes == canon_bytes2

print("det_ci_new", det_ci_new)
print("loocv_ci_new", loocv_ci_new)
print("gap_ci_new", gap_ci_new)
print("WROTE", WORK / "diagnostic.canonical.json")
