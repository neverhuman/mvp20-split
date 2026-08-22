#!/usr/bin/env python3
"""W14: null-baseline audit of polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-kpi.v1.json

Claim under attack: gate "ml_beats_van_krevelen_physical_baseline_on_MAE" (ML MAE 39.12 C
vs VK MAE 109.08 C, "beats by 70.0 C") and gate "ml_MAE_less_than_50C_across_5_external_candidates"
whose note frames MAE<50C as "useful engineering Tg prediction" -- on the SAME 5 canonical
DGEBA epoxy-amine candidates (IPDA/m-XDA/DDS/TETA/DETA, published Tg from May 1988 Ch.6).

The receipt never computes a structure-blind constant-value NULL baseline for this 5-candidate
external validation (every other MAE gate in sibling KPIs across this module carries an explicit
NULL-median/mean comparison; this one does not). Both the ML model AND the VK physical baseline
produce near-degenerate near-constant predictions on these 5 candidates (ML range 99.5-122.9 C,
spread=23.4C; VK range 251.4-252.0 C, spread=0.6C -- VK is a near-pure +250C offset, a bug
already disclosed elsewhere in this module's own van-krevelen-tg-external-validation KPI).
"ML beats VK" could simply mean VK's known offset-bug is much worse than any constant predictor,
telling us nothing about real ML skill.

Pre-registered refutation criterion (fixed BEFORE computing the null):
  The claim that ML MAE=39.12C on this 5-candidate set demonstrates real predictive skill
  (as opposed to an artifact of comparison against an unusually bad physics baseline) is
  REFUTED if EITHER:
    (a) a trivial constant-value baseline -- predicting the FULL Polyuniverse Epoxy 1M raw
        population mean Tg (deg C, unit-corrected per this module's own prior disclosure) for
        all 5 candidates, using ZERO molecular/structural information -- achieves MAE <= ML's
        observed MAE (39.11947866164949 C); OR
    (b) the same trivial constant-value baseline beats ML MAE using the population MEDIAN
        instead of MEAN.
  Both use only the pinned Epoxy_1M_p.csv (sha256 9f1f5c593463b9c26a026948901e37b4db545d17f05d5cd80baca5c3e14e0c45,
  independently verified byte-identical) -- no re-derivation of the ML model or its scaffold-safe
  train split is needed; this attacks whether the COMPARISON is meaningful, not whether the ML
  model was correctly trained.
"""
import csv, hashlib, json, statistics

CSV_PATH = "/home/ubuntu/amphora/build/mvp20-split/feedback/v1/external_data/polyuniverse_epoxy/raw/Epoxy_1M_p.csv"

def file_sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

csv_sha256 = file_sha256(CSV_PATH)
assert csv_sha256 == "9f1f5c593463b9c26a026948901e37b4db545d17f05d5cd80baca5c3e14e0c45", csv_sha256

# Raw Tg column: already established elsewhere in this module (critical_units_disclosure
# in the KPI under attack itself) to be in degrees C, not K. Read literally, no re-interpretation.
tg_values = []
with open(CSV_PATH, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        v = row.get("Tg")
        if v is None or v == "":
            continue
        try:
            tg_values.append(float(v))
        except ValueError:
            continue

n_total = len(tg_values)
pop_mean_C = statistics.fmean(tg_values)
pop_median_C = statistics.median(tg_values)
pop_stdev_C = statistics.pstdev(tg_values)
pop_min_C = min(tg_values)
pop_max_C = max(tg_values)

# Verbatim per-candidate published Tg (deg C) and ML predictions, transcribed from the
# scientific receipt under attack: reference/mvp20/data/polyuniverse_epoxy_tg_external_validation_5_canonical_epoxy_amines_receipt.v1.json
CANDIDATES = [
    {"name": "IPDA (isophorone diamine)", "published_Tg_C": 158, "ml_prediction_C": 122.88322948806938, "vk_prediction_C": 251.37649079043467},
    {"name": "m-XDA (m-xylylenediamine)", "published_Tg_C": 100, "ml_prediction_C": 104.33531743154543, "vk_prediction_C": 251.8610330726768},
    {"name": "DDS (4,4'-diaminodiphenyl sulfone)", "published_Tg_C": 220, "ml_prediction_C": 99.542817508103, "vk_prediction_C": 252.03999823347363},
    {"name": "TETA (triethylenetetramine)", "published_Tg_C": 120, "ml_prediction_C": 99.67876988426288, "vk_prediction_C": 251.52674265447737},
    {"name": "DETA (diethylenetriamine)", "published_Tg_C": 115, "ml_prediction_C": 99.63310724286275, "vk_prediction_C": 251.58480391714835},
]

def mae(preds, actuals):
    return sum(abs(p - a) for p, a in zip(preds, actuals)) / len(actuals)

def rmse(preds, actuals):
    return (sum((p - a) ** 2 for p, a in zip(preds, actuals)) / len(actuals)) ** 0.5

actuals = [c["published_Tg_C"] for c in CANDIDATES]
ml_preds = [c["ml_prediction_C"] for c in CANDIDATES]
vk_preds = [c["vk_prediction_C"] for c in CANDIDATES]

ml_MAE_reproduced = mae(ml_preds, actuals)
vk_MAE_reproduced = mae(vk_preds, actuals)

# reproduce receipt's own headline numbers as a sanity/fidelity check
assert abs(ml_MAE_reproduced - 39.11947866164949) < 1e-6, ml_MAE_reproduced
assert abs(vk_MAE_reproduced - 109.07781373364219) < 1e-6, vk_MAE_reproduced

# NULL baselines: constant prediction, zero structural information
null_mean_preds = [pop_mean_C] * 5
null_median_preds = [pop_median_C] * 5
null_mean_MAE = mae(null_mean_preds, actuals)
null_mean_RMSE = rmse(null_mean_preds, actuals)
null_median_MAE = mae(null_median_preds, actuals)
null_median_RMSE = rmse(null_median_preds, actuals)

# secondary robustness check: leave-one-out mean of the OTHER 4 published actuals
# (uses only the 5-candidate test set itself, no population leakage in either direction)
loo_preds = []
for i in range(5):
    others = [actuals[j] for j in range(5) if j != i]
    loo_preds.append(statistics.fmean(others))
loo_MAE = mae(loo_preds, actuals)
loo_RMSE = rmse(loo_preds, actuals)

# ML per-candidate prediction spread (degeneracy check)
ml_spread_C = max(ml_preds) - min(ml_preds)
vk_spread_C = max(vk_preds) - min(vk_preds)
actual_spread_C = max(actuals) - min(actuals)

refute_a = null_mean_MAE <= ml_MAE_reproduced
refute_b = null_median_MAE <= ml_MAE_reproduced
refuted = bool(refute_a or refute_b)

result = {
    "attack_id": "W14-null-baseline-5-canonical-epoxy-amines-tg",
    "csv_sha256_verified": csv_sha256,
    "n_total_polyuniverse_rows": n_total,
    "population_Tg_C_stats": {
        "mean": pop_mean_C,
        "median": pop_median_C,
        "stdev": pop_stdev_C,
        "min": pop_min_C,
        "max": pop_max_C,
    },
    "reproduced_receipt_headline": {
        "ml_MAE_C": ml_MAE_reproduced,
        "vk_MAE_C": vk_MAE_reproduced,
        "ml_beats_vk_by_C": vk_MAE_reproduced - ml_MAE_reproduced,
        "fidelity_check": "byte-exact match to receipt's own ml_MAE_C=39.11947866164949 and vk_MAE_C=109.07781373364219",
    },
    "prediction_degeneracy": {
        "ml_prediction_spread_C": ml_spread_C,
        "vk_prediction_spread_C": vk_spread_C,
        "actual_published_Tg_spread_C": actual_spread_C,
        "note": "VK spread of 0.6C across 5 structurally distinct amines confirms the near-pure +250C-offset degenerate-output bug already disclosed in this module's van-krevelen-tg-external-validation-15-canonical-homopolymers-kpi.v1.json. ML spread of 23.4C is also narrow relative to the actual 120C spread of published values (100-220C).",
    },
    "null_baselines": {
        "constant_population_mean": {
            "predicted_value_C": pop_mean_C,
            "MAE_C": null_mean_MAE,
            "RMSE_C": null_mean_RMSE,
            "beats_ml": null_mean_MAE < ml_MAE_reproduced,
            "beats_ml_or_ties": null_mean_MAE <= ml_MAE_reproduced,
        },
        "constant_population_median": {
            "predicted_value_C": pop_median_C,
            "MAE_C": null_median_MAE,
            "RMSE_C": null_median_RMSE,
            "beats_ml": null_median_MAE < ml_MAE_reproduced,
            "beats_ml_or_ties": null_median_MAE <= ml_MAE_reproduced,
        },
        "leave_one_out_mean_of_other_4_actuals": {
            "MAE_C": loo_MAE,
            "RMSE_C": loo_RMSE,
            "beats_ml": loo_MAE < ml_MAE_reproduced,
            "note": "Non-circular internal control using only the 5-candidate test set itself; NOT the primary refutation criterion (population-mean/median are), reported for robustness.",
        },
    },
    "pre_registered_refutation_criterion": {
        "criterion_a": "constant_population_mean.MAE_C <= ml_MAE_reproduced",
        "criterion_a_fired": refute_a,
        "criterion_b": "constant_population_median.MAE_C <= ml_MAE_reproduced",
        "criterion_b_fired": refute_b,
    },
    "verdict": "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED",
    "per_candidate": [
        {**c, "null_mean_pred_C": pop_mean_C, "null_mean_abs_err_C": abs(pop_mean_C - c["published_Tg_C"])}
        for c in CANDIDATES
    ],
}

print(json.dumps(result, indent=2))

import sys
out_path = sys.argv[1] if len(sys.argv) > 1 else None
if out_path:
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
