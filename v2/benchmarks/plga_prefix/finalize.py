#!/usr/bin/env python3
"""Descriptive inference/figures for all locked comparisons; no model selection."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ORDER = ["persistence", "linear", "higuchi", "first_order", "amphora_pareto", "rf", "hist_gradient_boosting", "rf_amphora"]
LABELS = dict(zip(ORDER, ["Persistence", "Linear", "Higuchi", "First order", "Pareto forecast", "RF", "Boosting", "RF + Amphora"]))

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p, d): Path(p).write_text(json.dumps(d, indent=2, allow_nan=False) + "\n")

def summarize(a, name, destination):
    curve = pd.read_csv(a / "full/curve_metrics.csv")
    by_curve = curve.groupby(["formulation", "group", "model"]).mae_pp.mean().unstack("model")[ORDER]
    group = by_curve.reset_index().groupby("group")
    sums = group[ORDER].sum().to_numpy(); sizes = group.size().to_numpy()
    indices = np.random.default_rng(20261017).integers(0, len(sizes), size=(2000, len(sizes)))
    boot = sums[indices].sum(axis=1) / sizes[indices].sum(axis=1)[:, None]
    means = by_curve.mean().to_numpy(); lo, hi = np.quantile(boot, [.025, .975], axis=0)
    table = pd.DataFrame({"model": ORDER, "mae_pp": means, "ci95_low_pp": lo, "ci95_high_pp": hi})
    table.to_csv(destination / (name + "_metrics_ci.csv"), index=False)
    difference = boot[:, ORDER.index("rf_amphora")] - boot[:, ORDER.index("rf")]
    observed_difference = means[ORDER.index("rf_amphora")] - means[ORDER.index("rf")]
    record = {"analysis": name, "unique_formulations": len(by_curve), "clusters": len(sizes), "repeated_folds": 15,
              "rf_amphora_minus_rf_pp": float(observed_difference), "ci95_pp": np.quantile(difference, [.025, .975]).tolist(),
              "bootstrap_unit": "joint drug/publication component" if name == "joint" else "drug component",
              "bootstrap_resamples": 2000, "interpretation": "Conditional on this corpus and locked repeated CV; not an external-population or prospective coverage guarantee"}
    dump(destination / (name + "_paired_comparison.json"), record)
    curve.groupby(["repeat", "model"]).mae_pp.mean().unstack("model")[ORDER].to_csv(destination / (name + "_repeat_metrics.csv"))
    return table, record, by_curve

def save(fig, folder, stem):
    fig.savefig(folder / (stem + ".png"), dpi=200, bbox_inches="tight")
    fig.savefig(folder / (stem + ".svg"), bbox_inches="tight")
    plt.close(fig)

def finalize(a, joint, code):
    report = a / "report"; report.mkdir(exist_ok=False)
    ptab, primary, curves = summarize(a, "primary", report)
    jtab, sensitivity, _ = summarize(joint, "joint", report)
    assert sha(a / "pilot/predictions.csv") == sha(a / "rerun/predictions.csv")
    checks = pd.read_csv(a / "full/leakage_checks.csv")
    joint_checks = pd.read_csv(joint / "full/leakage_checks.csv")
    assert len(checks) == 960 and len(joint_checks) == 960
    assert checks.future_tail_invariance.all() and joint_checks.future_tail_invariance.all()
    assert checks.prefix_positive_control.all() and joint_checks.prefix_positive_control.all()
    primary_predictions = pd.read_csv(a / "full/predictions.csv")
    joint_predictions = pd.read_csv(joint / "full/predictions.csv")
    assert len(primary_predictions) == len(joint_predictions) == 3910 * 3 * 8
    assert primary_predictions.groupby(["repeat", "model"]).formulation.nunique().eq(320).all()
    assert joint_predictions.groupby(["repeat", "model"]).formulation.nunique().eq(320).all()
    pilot = pd.read_csv(a / "pilot/predictions.csv")
    first = primary_predictions[(primary_predictions["repeat"] == 0) & (primary_predictions.fold == 0)]
    sort = ["formulation", "model", "time_day"]
    assert np.allclose(pilot.sort_values(sort).predicted_release, first.sort_values(sort).predicted_release, rtol=0, atol=0)
    validation = {"pilot_rerun_predictions_byte_identical": True, "pilot_equals_first_full_fold": True,
                  "held_out_tail_invariance_passes": len(checks) + len(joint_checks), "prefix_positive_controls_pass": True,
                  "all_predeclared_models_retained": ORDER, "primary_prediction_rows": len(primary_predictions),
                  "joint_prediction_rows": len(joint_predictions), "model_failures_after_repair": 0,
                  "initial_unscored_failure_retained": "failed-pilot-01.log", "joint_split_disjointness": json.loads((joint / "group_disjointness.json").read_text())}
    dump(report / "verification.json", validation)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.3), sharex=True)
    for ax, table, title in zip(axes, [ptab, jtab], ["Locked primary: drug-held-out", "Sensitivity: drug + DOI blocked"]):
        colors = ["#15847b" if n == "rf_amphora" else "#536f85" if n == "rf" else "#a4afb7" for n in ORDER]
        ax.barh(np.arange(8), table.mae_pp, color=colors, height=.65)
        ax.errorbar(table.mae_pp, np.arange(8), xerr=np.vstack([table.mae_pp-table.ci95_low_pp, table.ci95_high_pp-table.mae_pp]), fmt="none", ecolor="#253746", capsize=2, lw=1)
        ax.set_yticks(np.arange(8), [LABELS[x] for x in ORDER]); ax.invert_yaxis()
        ax.set_title(title, fontsize=11); ax.set_xlabel("Curve-balanced tail MAE (percentage points)")
        ax.grid(axis="x", alpha=.18); ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("First-three-recorded-point PLGA release forecasting", fontsize=14, y=1.02)
    fig.text(.5, -.02, "320 formulations; 3 × 5 grouped folds; 95% cluster-bootstrap intervals. Lower is better.", ha="center", fontsize=9)
    fig.tight_layout(); save(fig, report, "benchmark_comparison")

    fig, ax = plt.subplots(figsize=(5.3, 5))
    ax.scatter(curves.rf, curves.rf_amphora, s=18, alpha=.5, color="#15847b")
    upper = max(curves.rf.max(), curves.rf_amphora.max()) * 1.03
    ax.plot([0, upper], [0, upper], "--", color="#7f8c95", lw=1)
    ax.set(xlabel="RF per-formulation MAE (pp)", ylabel="RF + Amphora per-formulation MAE (pp)", title="Paired formulation errors: primary analysis", xlim=(0, upper), ylim=(0, upper))
    ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); save(fig, report, "paired_errors")

    observations = pd.read_csv(a / "normalized_observations.csv")
    chosen = sorted(primary_predictions.formulation.unique())[:6]
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.5))
    for ax, form in zip(axes.flat, chosen):
        obs = observations[observations["Formulation Index"] == form].sort_values("Time")
        ax.plot(obs.Time, 100 * obs.Release, ".-", color="#263640", lw=.8, label="Recorded release")
        ax.scatter(obs.Time.iloc[:3], 100*obs.Release.iloc[:3], s=40, facecolor="white", edgecolor="black", zorder=5, label="Visible prefix")
        for name, color in [("rf", "#536f85"), ("rf_amphora", "#15847b"), ("hist_gradient_boosting", "#ba7941")]:
            pred = primary_predictions[(primary_predictions.formulation == form) & (primary_predictions["repeat"] == 0) & (primary_predictions.model == name)].sort_values("time_day")
            ax.plot(pred.time_day, 100*pred.predicted_release, color=color, lw=1.1, label=LABELS[name])
        ax.axvline(obs.Time.iloc[2], color="grey", ls=":", lw=.9)
        ax.set(title="Formulation %d" % form, xlabel="Time (days)", ylabel="Release (%)", ylim=(-3, 103))
        ax.spines[["top", "right"]].set_visible(False)
    axes.flat[0].legend(fontsize=7, loc="best")
    fig.suptitle("Examples chosen by formulation ID, before considering prediction quality", fontsize=12)
    fig.tight_layout(); save(fig, report, "example_profiles")

    audit = json.loads((a / "cohort_audit.json").read_text())
    records = json.loads((a / "raw/mendeley_metadata.json").read_text())
    timings = {"primary": json.loads((a / "full/run_record.json").read_text()), "joint": json.loads((joint / "full/run_record.json").read_text())}
    dump(report / "timing_summary.json", timings)
    exclusions = pd.read_csv(a / "excluded_observations.csv")
    dump(report / "exclusion_breakdown.json", {"negative_time": int((exclusions.Time < 0).sum()), "release_below_tolerance": int((exclusions.Release < -.02).sum()), "release_above_tolerance": int((exclusions.Release > 1.02).sum()), "excluded_profiles": pd.read_csv(a / "excluded_profiles.csv").to_dict("records")})
    def tab(table):
        return "\n".join("| %s | %.2f | %.2f–%.2f |" % (LABELS[r.model], r.mae_pp, r.ci95_low_pp, r.ci95_high_pp) for r in table.itertuples())
    p_diff = primary["rf_amphora_minus_rf_pp"]; j_diff = sensitivity["rf_amphora_minus_rf_pp"]
    note = f"""# First-paper results draft: auditable prefix-conditioned PLGA release forecasting

This is a retrospective computational benchmark on literature-digitized in vitro release data, executed on xbabe1. It is not a new laboratory experiment, clinical/ocular validation, established superiority claim, or estimate of development savings.

## Main finding

An existing Amphora mathematical component—the verbatim constrained Pareto ranking module—was reused to select simple kinetic forecasts from information available in the first three recorded points. Its prefix-only mean forecast, spread and front size were added to a fixed random forest. The predeclared primary comparison changed curve-balanced tail MAE by **{p_diff:.2f} percentage points** (RF + Amphora minus RF; negative favors augmentation; conditional 95% drug-cluster bootstrap interval {primary['ci95_pp'][0]:.2f} to {primary['ci95_pp'][1]:.2f}). The unchanged pipeline's stricter joint drug/publication sensitivity gave **{j_diff:.2f} pp** (95% joint-cluster interval {sensitivity['ci95_pp'][0]:.2f} to {sensitivity['ci95_pp'][1]:.2f}). This is evidence for this specific feature adapter and corpus, not a general superiority result for Amphora. The standalone Pareto forecast is retained below and did not outperform the stronger learned baselines.

## Cohort and information boundary

One archive only: Bao et al.'s PLGA corpus, using derivative tables pinned to Git commit 605cd707c47a4379212193560cd332d7a2d973fd. Of 321 formulations/4,913 rows, {audit['eligible_formulations']} formulations and {audit['eligible_timepoints']} valid distinct-time measurements remain; {audit['tail_timepoints']} suffix targets are scored per repeat. The locked rules excluded {audit['invalid_observations']} invalid records, averaged {audit['duplicate_time_rows_collapsed']} duplicate-time rows and excluded {audit['excluded_profiles']} formulation with fewer than five valid times. Every exclusion is retained.

Units are days and fractional release. The prefix is the first three **recorded** points, commonly including time zero; this does not mean three new lab assays. Prefix end time median is {audit['prefix_end_day_quantiles'][2]:.2f} days (IQR {audit['prefix_end_day_quantiles'][1]:.2f}–{audit['prefix_end_day_quantiles'][3]:.2f}; range {audit['prefix_end_day_quantiles'][0]:.3f}–{audit['prefix_end_day_quantiles'][4]:.2f}). Thus this is an observation-budget benchmark, not a universal fixed-day early-prediction claim. Query timestamps are supplied explicitly. No final duration, final release, whole-curve interpolation or full-curve normalization enters a predictor.

All models use the same allowed information; kinetics use a subset. RF/boosting see ten pre-release material descriptors, formulation method and prefix/query features. The augmented RF receives only deterministic functions of the same prefix. Median imputation and one-hot category fitting occur within each training fold. Training suffix rows receive weights summing to one per formulation. Hyperparameters are fixed; no model search or test-driven tuning was performed.

## Locked primary results

The primary protocol was locked before scores. Three fixed shuffled five-fold partitions keep all formulation timepoints, shared drug SMILES and descriptor aliases together: 88 drug blocks. Every formulation is scored once per repeat. The primary metric averages absolute errors first within each formulation's observed suffix and then across formulations. Intervals resample drug blocks after averaging each formulation's three repeated-CV errors; they are conditional on this corpus/locked analysis and do not establish study-independent generalization.

| Model | MAE (pp) | 95% conditional cluster interval |
|---|---:|---:|
{tab(ptab)}

## Stronger publication-aware sensitivity

The official version-2 formulation table was downloaded and verified against its publisher SHA-256. Formulation IDs, drug SMILES and loading values align to the derivatives. All 321 rows have DOI identifiers (113 distinct publications). After the primary scores, a separately declared exploratory sensitivity connected formulations sharing either primary drug identity **or** DOI: 78 blocks, largest 59 formulations. Its protocol/splits were locked before sensitivity scores. No drug block or publication DOI crosses any of its 15 splits; no pipeline/hyperparameter changes were made. It does not replace the primary result.

| Model | MAE (pp) | 95% conditional joint-cluster interval |
|---|---:|---:|
{tab(jtab)}

## Verification and retained evidence

The independent pilot rerun is byte-identical (prediction SHA-256 `{sha(a/'pilot/predictions.csv')}`). Its predictions also match the first full fold exactly. Across both full analyses, **1,920 held-out-curve checks** passed: perturbing only future release labels with fitted models fixed changes neither features nor predictions. Prefix perturbation positive controls change the features. All 16 model/analysis combinations are retained; there are no failed models after the deterministic implementation repair.

The first unscored attempt stopped because parallel RF summation was not bitwise deterministic. It was retained, and RF threading was changed to one before any valid fold score was reported; split/model hyperparameters stayed fixed. The protocol amendment and both locks are included. Full scientific comparisons took {timings['primary']['seconds']:.1f} seconds primary and {timings['joint']['seconds']:.1f} seconds sensitivity. Peak measured process RSS: {timings['primary']['peak_rss_mib']:.1f} and {timings['joint']['peak_rss_mib']:.1f} MiB. Jobs were pinned to two CPUs, nice 10, 4-GiB address-space and 1,800-CPU-second limits. No GPU, paid provider, dependency installation, service launch, push or publication was used.

## Interpretation and next experiment

The useful result is a small, source-traceable adapter with measured held-out behavior: Amphora's reviewed numerical selection module can contribute physics-shaped prefix features to a drug-release baseline, while preserving all candidate decisions and failures. The absolute forecast errors remain material, and the pure selector is not itself a validated PLGA model. The literature corpus also conditions which formulations were originally published/curated; digitization noise, sparse sampling and synthetic time-zero values can affect conclusions.

Before a manuscript's stronger generalization claims, freeze this adapter and collect a genuinely external/new-study PLGA panel with prespecified sampling at fixed days, assay conditions, a baseline-first hypothesis, and laboratory replicate uncertainty. Test both a fixed-day prefix and the recorded-point budget separately. This checks prospective usefulness without changing the retained retrospective analysis. A scientist should review the data inclusion and endpoint definitions before submission.

## Sources and attribution

- Bao, Z., Kim, J., Kwok, C., Le Devedec, F. & Allen, C. (2025). *A dataset on formulation parameters and characteristics of drug-loaded PLGA microparticles*. Scientific Data 12, 364. https://doi.org/10.1038/s41597-025-04621-9
- Official data version 2: https://doi.org/10.17632/zzvtdrcy76.2 ; CC BY 4.0, verified in archived publisher metadata. https://creativecommons.org/licenses/by/4.0/
- Derivative data credit: mdsamad001, *Drug_Release_Dynamics_Prediction*, pinned Git commit 605cd707c47a4379212193560cd332d7a2d973fd. Both raw XLSX tables and exact hashes/URLs are retained. We wrote an independent benchmark, not that repository's training pipeline. Changes: exclusion/duplicate-time rules, group construction, prefix-only representations and models are documented above; no source endorsement is implied.
- Amphora source: https://github.com/neverhuman/mvp20-split/tree/afe121c0c59b69646052ada00bd20c75bf5753d8 ; `v2/tools/evolution_search/src/amphora_evolution_search/ranking.py`, SHA-256 `f80ca634f97f47876329d6418ce7a852a20a8844cc4b5eec1a4900e4c219304f`. Original license and provenance accompany the verbatim module. No coating/ocular/biological efficacy model was imported.
"""
    (report / "FIRST_PAPER_RESULTS.md").write_text(note)
    dump(report / "results.json", {"primary": primary, "joint": sensitivity, "verification": validation, "timing": timings})
    # Portable bundle excludes the environment and cache; raw public data included with attribution.
    bundle = a.parent / "plga-prefix-20261017-evidence"; bundle.mkdir(exist_ok=False)
    shutil.copytree(code, bundle / "code", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for source, target in [(a, bundle / "primary"), (joint, bundle / "joint")]:
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("env", "raw") if source == joint else shutil.ignore_patterns("env"))
    (bundle / "README.md").write_text("# Amphora PLGA prefix benchmark evidence\n\nStart with primary/report/FIRST_PAPER_RESULTS.md and primary/report/benchmark_comparison.png.\n\nCode is in code/. Primary and joint locks, all splits, predictions, selection receipts, exclusions, timings, failure record and 95% cluster intervals are retained. Public source bytes/license metadata are in primary/raw/. The joint analysis reuses the same raw files.\n\nReproduce with Python 3.12.3 and code/requirements.lock in a new isolated environment. See code/REPRODUCE.md for commands. SHA256SUMS.json covers every supplied file except itself. No credentials or environment directory are included.\n")
    manifest = {str(p.relative_to(bundle)): sha(p) for p in sorted(bundle.rglob("*")) if p.is_file()}
    dump(bundle / "SHA256SUMS.json", manifest)
    archive = bundle.with_suffix(".tar.gz")
    with tarfile.open(archive, "w:gz") as tar: tar.add(bundle, arcname=bundle.name)
    emit = {"primary": primary, "joint": sensitivity, "verification": validation, "bundle": str(bundle), "archive": str(archive), "archive_sha256": sha(archive), "archive_bytes": archive.stat().st_size}
    dump(a.parent / "plga-prefix-20261017-delivery.json", emit)
    print(json.dumps(emit), flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--primary", type=Path, required=True); ap.add_argument("--joint", type=Path, required=True); ap.add_argument("--code", type=Path, required=True)
    args = ap.parse_args(); finalize(args.primary, args.joint, args.code)
