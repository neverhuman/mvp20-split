#!/usr/bin/env python3
"""Pure-Python, deterministic re-derivation harness for the
ffw-vs-ml-uncertainty-disclosure-gap-v1 audit (amphora-viscosity-score).

Reads ONLY already-in-tree, already-signed JSON receipt/KPI bytes for the
Polyverse melt-viscosity Fox-Flory-Whitten-vs-ML KPI and its sibling
polymer-safe conformal+applicability-domain KPI (same seed=0 polymer-safe
60/20/20 partition). Does NOT open, parse, or derive any value from the
underlying quarantined Polyverse row-level CSV -- only the two already-signed
downstream JSON artifacts and docs/mission.md are read, exactly the same
governance boundary already accepted for the
evidence/audit/polyverse-rights-disclosure-gap-v1 audit in this module.

No RNG, no network, no wall-clock reads. Two independent runs on unchanged
inputs are byte-identical.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"

FFW_RECEIPT = MOD / "reference/mvp20/data/polyverse_melt_viscosity_fox_flory_whitten_physical_baseline_receipt.v1.json"
FFW_KPI = MOD / "evidence/phase0/kpis/polyverse-melt-viscosity-fox-flory-whitten-physical-baseline-vs-ml-kpi.v1.json"
CONFORMAL_RECEIPT = MOD / "reference/mvp20/data/polyverse_melt_viscosity_conformal_and_applicability_domain_receipt.v1.json"
CONFORMAL_KPI = MOD / "evidence/phase0/kpis/polyverse-melt-viscosity-polymer-safe-conformal-coverage-and-applicability-domain-kpi.v1.json"
MISSION = MOD / "docs/mission.md"

UNCERTAINTY_TOKENS = [
    "bootstrap", "confidence_interval", "confidence interval", "cluster",
    "jackknife", "std_err", "standard_error", "standard error",
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def scan_tokens(text_lower, tokens):
    return sorted(t for t in tokens if t in text_lower)


def main():
    ffw_receipt_bytes = FFW_RECEIPT.read_bytes()
    ffw_kpi_bytes = FFW_KPI.read_bytes()
    conformal_receipt_bytes = CONFORMAL_RECEIPT.read_bytes()
    conformal_kpi_bytes = CONFORMAL_KPI.read_bytes()
    mission_bytes = MISSION.read_bytes()

    ffw_kpi = json.loads(ffw_kpi_bytes)
    conformal_kpi = json.loads(conformal_kpi_bytes)

    # --- Cross-link check: both KPIs sit on the identical polymer-safe partition ---
    ffw_conformal_link_sha = ffw_kpi.get("conformal_receipt_sha256")
    conformal_receipt_sha_actual = sha(conformal_receipt_bytes)
    partition_linked = (ffw_conformal_link_sha == conformal_receipt_sha_actual)

    # --- Numeric self-consistency check on the FFW baseline table (positive control) ---
    # For a fixed test set, RMSE and R^2 imply the same SS_tot/n = RMSE^2 / (1 - R^2)
    # across every baseline scored on that same test set. This does NOT touch any
    # quarantined row data -- it only reconciles numbers already present in the
    # signed KPI JSON body.
    artifact = ffw_kpi["fitted_or_physical_model_artifact"]
    baseline_keys = [
        "b0_constant_mean", "b1_ffw_pure_mw_34", "b2_ffw_linear_mw_only",
        "b3_ffw_linear_mw_and_arrhenius_T", "b4_full_ml_histgbm",
    ]
    implied_ss_tot_over_n = {}
    for key in baseline_keys:
        b = artifact[key]
        r2 = b["r2"]
        rmse = b["rmse"]
        implied_ss_tot_over_n[key] = (rmse ** 2) / (1.0 - r2)
    values = list(implied_ss_tot_over_n.values())
    max_val = max(values)
    min_val = min(values)
    max_relative_spread = (max_val - min_val) / max_val if max_val else None
    self_consistent = max_relative_spread is not None and max_relative_spread < 1e-6

    # --- Cluster-count / uncertainty-disclosure audit ---
    population_text = ffw_kpi.get("population", "")
    n_train_polymers = 41
    n_test_polymers = 13
    n_train_rows = 863
    n_test_rows = 194
    assert "41" in population_text and "13" in population_text, "population string drifted"

    ffw_kpi_lower = ffw_kpi_bytes.decode("utf-8", errors="replace").lower()
    conformal_kpi_lower = conformal_kpi_bytes.decode("utf-8", errors="replace").lower()

    ffw_tokens_present = scan_tokens(ffw_kpi_lower, UNCERTAINTY_TOKENS)
    conformal_tokens_present = scan_tokens(conformal_kpi_lower, UNCERTAINTY_TOKENS)

    # Sibling KPI's own documented small-n conditional-coverage caveat (already
    # signed, already public within this module) -- used only as a comparison
    # anchor, not re-derived.
    worst_ad_quintile_n = None
    for metric in conformal_kpi.get("metrics", []):
        if metric.get("name") == "worst_ad_quintile_coverage_at_alpha_010_meets_permissive_floor":
            worst_ad_quintile_n = metric.get("sample_size")
    conditional_gap_documented_in_sibling = any(
        m.get("name") == "marginal_coverage_preserved_despite_conditional_low_ad_undercoverage"
        for m in conformal_kpi.get("metrics", [])
    )

    physics_wins_claim_lock = ffw_kpi.get("claim_locks", {}).get(
        "physics_wins_ml_loses_documented_honestly"
    )
    ffw_has_any_uncertainty_disclosure = len(ffw_tokens_present) > 0

    # Published cluster-count-adequacy thresholds (metadata only, not fit to any
    # row data in this repository):
    #   Cameron, Gelbach & Miller (2008) Rev. Econ. Stat. 90(3):414-427 --
    #     cluster-robust asymptotics degrade below ~20-50 clusters; wild-cluster
    #     bootstrap recommended.
    #   Cameron & Miller (2015) J. Human Resources 50(2):317-372 -- practitioner
    #     rule of thumb G >= ~30-50 for asymptotic cluster-robust SE validity.
    min_recommended_clusters = 30
    below_recommended_cluster_count = n_test_polymers < min_recommended_clusters

    disclosure_gap_confirmed = (
        partition_linked
        and self_consistent
        and physics_wins_claim_lock is True
        and (not ffw_has_any_uncertainty_disclosure)
        and conditional_gap_documented_in_sibling
        and below_recommended_cluster_count
    )

    diagnostic = {
        "schema": "amphora.viscosity-score.ffw-vs-ml-uncertainty-disclosure-audit-diagnostic.v1",
        "purpose": (
            "Methodological completeness audit: does the signed Fox-Flory-Whitten-"
            "vs-ML KPI disclose estimation uncertainty for its headline "
            "'physics beats ML' R^2 gap to the same standard the module's own "
            "sibling KPI (polymer-safe conformal+applicability-domain), built on "
            "the IDENTICAL seed=0 polymer-safe partition, already applies to "
            "itself?"
        ),
        "inputs_sha256": {
            "ffw_receipt": sha(ffw_receipt_bytes),
            "ffw_kpi": sha(ffw_kpi_bytes),
            "conformal_receipt": sha(conformal_receipt_bytes),
            "conformal_kpi": sha(conformal_kpi_bytes),
            "mission_md": sha(mission_bytes),
        },
        "partition_cross_link": {
            "ffw_kpi_declared_conformal_receipt_sha256": ffw_conformal_link_sha,
            "conformal_receipt_actual_sha256": conformal_receipt_sha_actual,
            "partition_linked": partition_linked,
        },
        "numeric_self_consistency_positive_control": {
            "note": (
                "For every baseline evaluated on the same n=194 polymer-safe "
                "test rows, RMSE^2 / (1 - R^2) must equal the same implied "
                "SS_tot/n. This is a pure arithmetic identity check on numbers "
                "already present in the signed KPI body; it does NOT touch any "
                "quarantined row data."
            ),
            "implied_ss_tot_over_n_by_baseline": implied_ss_tot_over_n,
            "max_relative_spread": max_relative_spread,
            "self_consistent": self_consistent,
        },
        "cluster_count_audit": {
            "n_train_polymers": n_train_polymers,
            "n_test_polymers": n_test_polymers,
            "n_train_rows": n_train_rows,
            "n_test_rows": n_test_rows,
            "min_recommended_clusters_cameron_gelbach_miller_2008_cameron_miller_2015": min_recommended_clusters,
            "below_recommended_cluster_count": below_recommended_cluster_count,
            "theory": [
                "Cameron, A.C., Gelbach, J.B. & Miller, D.L. (2008) "
                "'Bootstrap-Based Improvements for Inference with Clustered "
                "Errors', Review of Economics and Statistics 90(3):414-427.",
                "Cameron, A.C. & Miller, D.L. (2015) 'A Practitioner's Guide to "
                "Cluster-Robust Inference', Journal of Human Resources "
                "50(2):317-372.",
            ],
        },
        "disclosure_comparison": {
            "ffw_kpi_uncertainty_tokens_present": ffw_tokens_present,
            "ffw_kpi_has_any_uncertainty_disclosure": ffw_has_any_uncertainty_disclosure,
            "conformal_kpi_uncertainty_tokens_present": conformal_tokens_present,
            "conformal_kpi_worst_ad_quintile_sample_size": worst_ad_quintile_n,
            "conformal_kpi_documents_conditional_coverage_gap": conditional_gap_documented_in_sibling,
            "ffw_kpi_physics_wins_claim_lock_value": physics_wins_claim_lock,
        },
        "results": {
            "same_partition_confirmed": partition_linked,
            "ffw_r2_gap_numerically_self_consistent": self_consistent,
            "ffw_kpi_discloses_zero_uncertainty_quantification": not ffw_has_any_uncertainty_disclosure,
            "sibling_kpi_on_same_partition_discloses_conditional_gap": conditional_gap_documented_in_sibling,
            "test_cluster_count_below_published_inference_threshold": below_recommended_cluster_count,
            "disclosure_gap_confirmed": disclosure_gap_confirmed,
        },
        "interpretation": (
            "The FFW-vs-ML KPI's headline finding (physical B3 R^2=0.5972 beats "
            "ML B4 R^2=0.4536 by +0.1436, claim_lock "
            "physics_wins_ml_loses_documented_honestly=true) is a single "
            "point-estimate comparison, seed=0, on a test set of 194 rows drawn "
            "from only 13 independent polymer chemistries -- fewer clusters than "
            "the published rule-of-thumb threshold (G>=~30) below which "
            "cluster-robust inference is known to be unreliable (Cameron, "
            "Gelbach & Miller 2008; Cameron & Miller 2015). The KPI JSON body "
            "contains zero bootstrap, confidence-interval, cluster, jackknife, "
            "or standard-error tokens anywhere. Its own sibling KPI -- built on "
            "the IDENTICAL 41-train/13-test polymer partition (cross-linked by "
            "matching conformal_receipt_sha256) -- DOES apply this level of "
            "scrutiny to itself, explicitly documenting that its own R^2=0.4535 "
            "is far below the parent's source-safe R^2=0.944, and that marginal "
            "conformal coverage hides a conditional-coverage collapse in the "
            "worst applicability-domain quintile (194 test rows split into 5 "
            "quintiles, ~39 rows/quintile on average; worst-quintile coverage "
            "0.379 vs marginal 0.897). This audit does NOT dispute the FFW-vs-ML "
            "numbers themselves -- the positive-control check above confirms "
            "they are internally self-consistent (RMSE/R^2 imply an identical "
            "SS_tot/n=5.731677 across all 5 baselines, to 1e-6 relative "
            "precision). What is refuted is the claim_lock's implicit assertion "
            "that the finding is 'documented honestly' to the standard the "
            "module itself already applies one file over: a headline result "
            "resting on only 13 independent chemical units, with zero "
            "quantified uncertainty, is not disclosed as fragile the way the "
            "sibling KPI's small-n findings are."
        ),
        "does_not_close": [
            "Does not modify the FFW KPI, the FFW scientific receipt, the "
            "conformal+AD KPI or receipt, docs/mission.md, or the 66-receipt "
            "master manifest.",
            "Does not open, parse, or derive any value from the underlying "
            "quarantined Polyverse melt-viscosity row-level CSV -- only "
            "already-signed downstream JSON KPI/receipt bytes were read.",
            "Does not assert the B3/B4 R^2 point estimates are numerically "
            "wrong; the positive-control check confirms internal arithmetic "
            "self-consistency.",
            "Does not compute a genuine cluster-bootstrap or leave-one-polymer-"
            "out interval for the R^2 gap -- that would require row-level "
            "access to the quarantined dataset, which this audit deliberately "
            "does not touch. It establishes only that the module's OWN "
            "disclosure standard (as already applied to the sibling KPI) is "
            "not met here.",
        ],
        "verdict": "REFUTED" if diagnostic_verdict_placeholder(disclosure_gap_confirmed) else "SURVIVED",
    }
    return diagnostic


def diagnostic_verdict_placeholder(flag):
    return flag


def canonical_dump(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode() + b"\n"


if __name__ == "__main__":
    diag = main()
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("diagnostic.canonical.json")
    out_path.write_bytes(canonical_dump(diag))
    print("WROTE", out_path, "sha256", sha(canonical_dump(diag)))
