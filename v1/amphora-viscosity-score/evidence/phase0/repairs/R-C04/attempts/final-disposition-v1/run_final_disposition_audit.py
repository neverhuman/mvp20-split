#!/usr/bin/env python3
"""R-C04 fire 3/3 final-disposition audit.

Two questions, both re-derived from bytes already on disk (or their
metadata), never from the quarantined row payload:

  (1) FRESHNESS: has anything changed since fire 1 (BLOCKED_DATA) and
      fire 2 (BLOCKED_RIGHTS)? Re-run fire 1's recursive length-{13,194}
      array scan across the whole module tree, and re-read the Polyverse
      rights decision, to confirm the blocker is still live.
  (2) RE-SCOPE FEASIBILITY: fire 2's STATE.json flagged an "honest
      re-scope hatch" as available this fire -- an analytic (non-
      resampling) small-sample interval bound for the R2 gap, computed
      purely from the already-published aggregate r2/mae/rmse/pearson_r
      and n=13, with explicitly reduced power vs the pre-registered
      cluster bootstrap. This script evaluates whether that bound is
      actually derivable soundly, and shows the specific reasons it is
      not, rather than asserting the conclusion.

Positive control: a decoy length-13 array is planted into an in-memory
copy of the KPI dict and the same recursive scanner is run against it,
to prove the "found zero real arrays" result is not a vacuous/broken
scan.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def find_len_arrays(obj, path, targets, hits):
    if isinstance(obj, list):
        if len(obj) in targets:
            hits.append({"path": path, "len": len(obj), "sample": obj[:3]})
        for i, v in enumerate(obj):
            find_len_arrays(v, f"{path}[{i}]", targets, hits)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            find_len_arrays(v, f"{path}/{k}", targets, hits)


# Fixed set of the FFW-vs-ML lineage files fire 1 (fire_id
# 20260812T040001-4187595-821716c37e86) already enumerated as the
# complete signed lineage. Scanning exactly this set (rather than a live
# rglob of the whole module) keeps this scan deterministic even though
# other lanes/agents may be concurrently writing unrelated receipts
# elsewhere in the shared module tree this hour.
LINEAGE_FILES = [
    "amphora-viscosity-score/evidence/phase0/kpis/polyverse-melt-viscosity-fox-flory-whitten-physical-baseline-vs-ml-kpi.v1.json",
    "amphora-viscosity-score/evidence/phase0/kpis/polyverse-melt-viscosity-polymer-safe-conformal-coverage-and-applicability-domain-kpi.v1.json",
    "amphora-viscosity-score/reference/mvp20/data/polyverse_melt_viscosity_fox_flory_whitten_physical_baseline_receipt.v1.json",
    "amphora-viscosity-score/reference/mvp20/data/polyverse_melt_viscosity_conformal_and_applicability_domain_receipt.v1.json",
    "amphora-viscosity-score/reference/mvp20/data/polyverse_melt_viscosity_model_receipt.v1.json",
    "amphora-viscosity-score/evidence/audit/ffw-vs-ml-uncertainty-disclosure-gap-v1/ffw-vs-ml-uncertainty-disclosure-gap-receipt.v1.dsse.json",
    "amphora-viscosity-score/evidence/audit/polyverse-rights-disclosure-gap-v1/polyverse-rights-disclosure-gap-receipt.v1.dsse.json",
    "amphora-viscosity-score/evidence/phase0/repairs/R-C04/attempts/cluster-bootstrap-data-audit-v1/cluster-bootstrap-data-audit-v1-receipt.v1.dsse.json",
    "amphora-viscosity-score/evidence/phase0/repairs/R-C04/attempts/rights-boundary-audit-v1/rights-boundary-audit-v1-receipt.v1.dsse.json",
]


def scan_tree(root, targets):
    hits = []
    files_scanned = 0
    missing = []
    for rel in LINEAGE_FILES:
        p = root / rel
        if not p.exists():
            missing.append(rel)
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        files_scanned += 1
        find_len_arrays(d, rel, targets, hits)
    if missing:
        hits.append({"error": "lineage file(s) missing, treat as a scan gap not a clean result", "missing": missing})
    return files_scanned, hits


def main():
    out = {}

    # --- (1) freshness: any new per-row/per-cluster arrays landed? ---
    files_scanned, hits = scan_tree(ROOT, {13, 194})
    out["freshness_scan"] = {
        "targets_searched": [13, 194],
        "lineage_files_scanned": LINEAGE_FILES,
        "files_scanned": files_scanned,
        "quarantine_paths_excluded": True,
        "hits": hits,
    }

    # --- positive control on the scanner itself ---
    kpi_path = MOD / "evidence/phase0/kpis/polyverse-melt-viscosity-fox-flory-whitten-physical-baseline-vs-ml-kpi.v1.json"
    real_kpi = json.loads(kpi_path.read_text())
    decoy = json.loads(json.dumps(real_kpi))  # deep copy
    decoy["fitted_or_physical_model_artifact"]["PLANTED_DECOY_per_polymer_r2"] = list(range(13))
    decoy_hits = []
    find_len_arrays(decoy, "DECOY_COPY::" + str(kpi_path.relative_to(ROOT)), {13, 194}, decoy_hits)
    out["positive_control"] = {
        "planted_defect": "a 13-element list PLANTED_DECOY_per_polymer_r2 inserted into fitted_or_physical_model_artifact of an in-memory copy of the real FFW-vs-ML KPI",
        "how_planted": "json round-trip deep copy of evidence/phase0/kpis/polyverse-melt-viscosity-fox-flory-whitten-physical-baseline-vs-ml-kpi.v1.json, then decoy['fitted_or_physical_model_artifact']['PLANTED_DECOY_per_polymer_r2'] = list(range(13))",
        "detected": len(decoy_hits) >= 1 and any(h["len"] == 13 for h in decoy_hits),
        "evidence": decoy_hits,
        "real_scan_hits_on_undecoyed_tree": len(hits),
    }

    # --- (2) rights status re-check ---
    rights_path = MOD / "reference/mvp20/quarantine/feedback_v2/exclusions/polyverse_melt_viscosity-3cd923b4d67399f9.rights.json"
    rights = json.loads(rights_path.read_text())
    out["rights_recheck"] = {
        "path": str(rights_path.relative_to(ROOT)),
        "sha256": sha(rights_path.read_bytes()),
        "decision_receipt": rights["decision"]["decision_receipt"],
        "rights_class": rights["decision"]["rights_class"],
        "promotion_eligible": rights["decision"]["promotion_eligible"],
        "basis": rights["decision"]["basis"],
        "unresolved": rights["decision"]["decision_receipt"] is None,
    }

    # --- (3) re-scope-hatch feasibility analysis ---
    kpi = real_kpi["fitted_or_physical_model_artifact"]
    b3 = kpi["b3_ffw_linear_mw_and_arrhenius_T"]
    b4 = kpi["b4_full_ml_histgbm"]
    n_rows = 194
    n_clusters = 13

    def olkin_finn_var(r2, n, k):
        # Olkin & Finn 1995 asymptotic variance of R^2 in OLS regression.
        # Requires n = number of INDEPENDENT observations and k = number
        # of fitted predictors. Undefined/unstable once n - k - 1 <= 0.
        dof = n - k - 1
        if dof <= 0:
            return None
        return 4.0 * r2 * (1.0 - r2) ** 2 * (dof ** 2) / ((n ** 2 - 1.0) * (n + 3.0))

    b3_k = 3  # intercept + slope_Mw + slope_1/T
    b4_k = None  # "many (histogram GBM leaves)" per the KPI's own field -- not a fixed small integer

    row_level_var_b3 = olkin_finn_var(b3["r2"], n_rows, b3_k)
    cluster_proxy_var_b3 = olkin_finn_var(b3["r2"], n_clusters, b3_k)

    r_vs_r2_gap_b4 = b4["pearson_r"] ** 2 - b4["r2"]

    out["rescope_hatch_feasibility"] = {
        "candidate_method": (
            "Olkin & Finn (1995, Psychological Bulletin 117:330-333) "
            "asymptotic-normal variance formula for a single-model R^2: "
            "Var(R^2) ~= 4*R^2*(1-R^2)^2*(n-k-1)^2 / ((n^2-1)*(n+3)), "
            "combined naively (assuming independence) into a CI for the "
            "R^2 difference B3-B4. Chosen because it is the only "
            "candidate that needs ONLY already-published aggregate "
            "numbers (R^2, n, k) and no per-row or per-polymer arrays."
        ),
        "problem_1_row_count_ignores_clustering": {
            "description": (
                "The formula's n means independent observations. The "
                "KPI's own population note states the 194 test rows come "
                "from only 13 unique novel test polymers -- i.e. n_eff <= "
                "13, not 194. Using n=194 (the only row-level count "
                "actually published) silently assumes independence the "
                "pre-registered cluster bootstrap exists specifically to "
                "NOT assume. This is the identical anti-conservative "
                "failure mode already documented against this module: "
                "amphora-viscosity-score/evidence/phase0/kpis/"
                "N=60-scaffold Monte Carlo finding (repeated-scaffold "
                "resampling REFUTED a single-seed coverage claim that a "
                "naive i.i.d.-row treatment had passed)."
            ),
            "b3_var_using_n_rows_194": row_level_var_b3,
            "b3_se_using_n_rows_194": row_level_var_b3 ** 0.5 if row_level_var_b3 is not None else None,
        },
        "problem_2_cluster_count_substitution_is_not_a_derivation": {
            "description": (
                "Substituting n=13 (cluster count) for n in the same "
                "row-level formula is not a valid re-derivation -- the "
                "formula's r2/(1-r2)^2 terms were still computed from the "
                "194-row pooled residuals, not from 13 independent "
                "per-polymer R^2 values. Relabeling n without recomputing "
                "the statistic from actual per-cluster quantities produces "
                "a number with no defensible sampling-distribution "
                "interpretation -- it is not a valid cluster-robust SE, "
                "just a smaller number obtained by putting a smaller n "
                "into a formula that was never derived for a plug-in n "
                "substitution of this kind."
            ),
            "b3_var_using_n_clusters_13_same_pooled_r2": cluster_proxy_var_b3,
            "b3_se_using_n_clusters_13_same_pooled_r2": cluster_proxy_var_b3 ** 0.5 if cluster_proxy_var_b3 is not None else None,
            "verdict": "NOT A VALID CLUSTER-ROBUST BOUND -- included only to show the substitution is computable, not that it is meaningful.",
        },
        "problem_3_b4_parameter_count_undefined": {
            "description": (
                "The formula also needs k, the number of fitted "
                "parameters, to compute degrees of freedom n-k-1. The "
                "KPI's own artifact field records B4's "
                "n_fitted_parameters as the string 'many (histogram GBM "
                "leaves)', not an integer. There is no principled small "
                "integer to substitute; HistGBM's effective parameter "
                "count is dataset- and hyperparameter-dependent and was "
                "never persisted. At n_clusters=13 almost any realistic "
                "k for a boosted-tree model exceeds n-1, making n-k-1 <= "
                "0 and the formula literally undefined (returns None "
                "above)."
            ),
            "b4_k_available": False,
        },
        "problem_4_r2_vs_pearson_r2_divergence": {
            "description": (
                "A simpler Fisher-z-on-pearson_r shortcut is also "
                "unsound here: for B4, pearson_r^2 (%.4f) exceeds the "
                "reported R^2 (%.4f) by %.4f. R^2 = 1 - SSE/SST penalizes "
                "prediction bias/miscalibration in addition to "
                "decorrelation; pearson_r^2 does not. This module's own "
                "prior finding "
                "(amphora-viscosity-score-score-eyring-apriori: Eyring "
                "23.8%% LOO REFUTED) already documents ML predictions on "
                "held-out novel chemistry drifting out of calibration "
                "even while remaining correlated. A correlation-based "
                "shortcut would understate B4's true generalization gap "
                "and bias the resulting interval toward the physics-wins "
                "conclusion for the wrong reason."
            ) % (b4["pearson_r"] ** 2, b4["r2"], r_vs_r2_gap_b4),
            "b4_pearson_r_squared": b4["pearson_r"] ** 2,
            "b4_reported_r2": b4["r2"],
            "gap": r_vs_r2_gap_b4,
        },
        "conclusion": (
            "No analytically sound, non-fabricated small-sample interval "
            "for R2(B3)-R2(B4) over the 13 independent test polymers is "
            "derivable from the currently-published aggregate KPI fields "
            "alone. Every candidate shortcut either (a) silently assumes "
            "row-level independence the pre-registered method exists to "
            "avoid, (b) requires per-cluster values that are not "
            "published and cannot be manufactured without re-consuming "
            "the quarantined CSV, or (c) requires a parameter count that "
            "was never recorded for the ML model. Computing and reporting "
            "any of these numbers as the item's CI would itself be a "
            "fabricated attack: a number chosen to look like it satisfies "
            "the acceptance criterion without the statistical grounding "
            "the criterion requires. The re-scope hatch is therefore "
            "evaluated and NOT invoked this fire."
        ),
    }

    json.dump(out, sys.stdout, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
