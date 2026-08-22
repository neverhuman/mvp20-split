#!/usr/bin/env python3
"""
R-S04: tightest-margin solvent-pair VHR band-assignment stress test under the
quantified Antoine-vs-Clausius-Clapeyron+Watson(1943) VP method bias.

Attacks: amphora-sourceability-ehs/reference/mvp20/data/vhr_temperature_envelope_crossmethod_audit_receipt.v1.json
claim_text: "The +5-11% systematic VP bias between Antoine and Clausius-Clapeyron+Watson
methods does not change any VHR band assignment for a tighter-margin solvent panel."

Method: pull the pinned 9-solvent 25C VHR panel (vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json,
n_solvents_scored=9), rank by VHR, enumerate the 8 consecutive-rank pairs, take the 5
with the smallest relative separation (VHR_higher/VHR_lower - 1). Pull the empirically
quantified CC+Watson bias envelope [BIAS_MIN, BIAS_MAX] verbatim from the SIGNED
crossmethod-audit receipt's ccwatson_crossmethod_rows (18 rows, 3 solvents x 6 grid
temperatures) -- min/max observed relative_deviation, NOT re-derived or re-estimated.

Apply the bias to each pair in the single most-adversarial admissible combination given
the bias is uniformly VP-positive-signed (CC+Watson always predicts higher VP than
Antoine in every observed row): BIAS_MAX to the lower-VHR member (pushes it up the
most), BIAS_MIN to the higher-VHR member (pushes it up the least). This is the
combination most likely to (a) reverse the pair's rank order or (b) cross either
member's HIGH/MODERATE/LOW screening-band boundary -- the two things the campaign item
and the pinned claim ask about. No LLM-authored constants, no RNG.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"

PANEL_RECEIPT = MOD / "reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json"
CROSSMETHOD_RECEIPT = MOD / "reference/mvp20/data/vhr_temperature_envelope_crossmethod_audit_receipt.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def band(vhr):
    if vhr >= 100.0:
        return "HIGH_INHALATION_HAZARD_ENGINEERING_VENTILATION_REQUIRED"
    if vhr >= 10.0:
        return "MODERATE_INHALATION_HAZARD_VENTILATION_RECOMMENDED"
    if vhr >= 1.0:
        return "LOW_INHALATION_HAZARD_GENERAL_VENTILATION"
    return "MINIMAL_SATURATED_HEADSPACE_BELOW_OEL"


def load_panel(receipt_bytes):
    d = json.loads(receipt_bytes)
    cards = d["kpis"]["solvent_cards_ranked"]
    return {c["solvent"]: dict(c) for c in cards}


def load_bias_envelope(receipt_bytes):
    d = json.loads(receipt_bytes)
    rows = d["kpis"]["ccwatson_crossmethod_rows"]
    devs = [r["relative_deviation"] for r in rows]
    return min(devs), max(devs), len(rows)


def compute_panel_and_pairs(panel):
    ranked = sorted(panel.values(), key=lambda c: (-c["vapor_hazard_ratio"], c["solvent"]))
    for i, c in enumerate(ranked):
        c["rank"] = i + 1
    pairs = []
    for i in range(len(ranked) - 1):
        hi, lo = ranked[i], ranked[i + 1]
        sep = hi["vapor_hazard_ratio"] / lo["vapor_hazard_ratio"] - 1.0
        pairs.append({
            "higher_vhr_solvent": hi["solvent"], "higher_vhr": hi["vapor_hazard_ratio"], "higher_band": hi["screening_band"],
            "lower_vhr_solvent": lo["solvent"], "lower_vhr": lo["vapor_hazard_ratio"], "lower_band": lo["screening_band"],
            "relative_separation": sep,
            "crosses_band_boundary_at_baseline": hi["screening_band"] != lo["screening_band"],
        })
    return ranked, pairs


def apply_worst_case_bias(pair, bias_min, bias_max):
    lo_biased = pair["lower_vhr"] * (1.0 + bias_max)
    hi_biased = pair["higher_vhr"] * (1.0 + bias_min)
    rank_order_flips = lo_biased > hi_biased
    lo_band_biased = band(lo_biased)
    hi_band_biased = band(hi_biased)
    band_assignment_flips = (lo_band_biased != pair["lower_band"]) or (hi_band_biased != pair["higher_band"])
    return {
        **pair,
        "lower_vhr_worstcase_biased": round(lo_biased, 4),
        "higher_vhr_worstcase_biased": round(hi_biased, 4),
        "lower_band_worstcase_biased": lo_band_biased,
        "higher_band_worstcase_biased": hi_band_biased,
        "rank_order_flips_under_worstcase_bias": rank_order_flips,
        "band_assignment_flips_under_worstcase_bias": band_assignment_flips,
    }


def rank_flip_threshold(bias_min, bias_max):
    # smallest relative separation S=(hi/lo - 1) at which lo*(1+bias_max) >= hi*(1+bias_min)
    # becomes possible for SOME pair.
    return (1.0 + bias_max) / (1.0 + bias_min) - 1.0


def band_flip_threshold_for_solvent(vhr, boundary=100.0):
    if vhr >= boundary:
        return None
    return boundary / vhr - 1.0


def run(panel_bytes, crossmethod_bytes, mutation_label="real"):
    panel = load_panel(panel_bytes)
    bias_min, bias_max, n_bias_rows = load_bias_envelope(crossmethod_bytes)
    ranked, pairs = compute_panel_and_pairs(panel)
    pairs_sorted = sorted(pairs, key=lambda p: p["relative_separation"])
    tightest5 = pairs_sorted[:5]
    evaluated = [apply_worst_case_bias(p, bias_min, bias_max) for p in tightest5]
    any_band_flip = any(e["band_assignment_flips_under_worstcase_bias"] for e in evaluated)
    any_rank_flip = any(e["rank_order_flips_under_worstcase_bias"] for e in evaluated)

    worst_actor = ranked[0]
    second = ranked[1]
    worst_actor_margin = worst_actor["vapor_hazard_ratio"] / second["vapor_hazard_ratio"] - 1.0
    worst_actor_flips = (second["vapor_hazard_ratio"] * (1.0 + bias_max)) >= (worst_actor["vapor_hazard_ratio"] * (1.0 + bias_min))

    rf_threshold = rank_flip_threshold(bias_min, bias_max)

    below100 = [c for c in ranked if c["vapor_hazard_ratio"] < 100.0]
    band_flip_thresholds = {}
    if below100:
        top_below = max(below100, key=lambda c: c["vapor_hazard_ratio"])
        thr = band_flip_threshold_for_solvent(top_below["vapor_hazard_ratio"])
        band_flip_thresholds[top_below["solvent"]] = {
            "baseline_vhr": top_below["vapor_hazard_ratio"],
            "bias_needed_to_cross_HIGH_boundary": round(thr, 5) if thr is not None else None,
            "quantified_bias_max_available": round(bias_max, 5),
            "margin_bias_points_short_of_flip": round((thr - bias_max), 5) if thr is not None else None,
        }

    return {
        "mutation_label": mutation_label,
        "n_panel": len(ranked),
        "bias_envelope": {
            "bias_min": bias_min, "bias_max": bias_max, "n_source_rows": n_bias_rows,
            "source_receipt": "amphora-sourceability-ehs/reference/mvp20/data/vhr_temperature_envelope_crossmethod_audit_receipt.v1.json#/kpis/ccwatson_crossmethod_rows",
        },
        "ranked_panel": [
            {"rank": c["rank"], "solvent": c["solvent"], "vapor_hazard_ratio": c["vapor_hazard_ratio"], "screening_band": c["screening_band"]}
            for c in ranked
        ],
        "all_8_adjacent_pairs_by_separation": sorted(
            [{"pair": f'{p["higher_vhr_solvent"]}/{p["lower_vhr_solvent"]}', "relative_separation": round(p["relative_separation"], 4)} for p in pairs],
            key=lambda x: x["relative_separation"],
        ),
        "tightest_5_pairs_evaluated": evaluated,
        "any_band_assignment_flip": any_band_flip,
        "any_rank_order_flip_within_band": any_rank_flip,
        "rank_order_flip_threshold_relative_separation": round(rf_threshold, 5),
        "band_assignment_flip_thresholds": band_flip_thresholds,
        "worst_actor": worst_actor["solvent"],
        "worst_actor_margin_over_second_place": round(worst_actor_margin, 4),
        "worst_actor_call_flips_under_worstcase_bias": worst_actor_flips,
    }


if __name__ == "__main__":
    panel_bytes = PANEL_RECEIPT.read_bytes()
    crossmethod_bytes = CROSSMETHOD_RECEIPT.read_bytes()

    real = run(panel_bytes, crossmethod_bytes, "real_unmutated_panel")

    # ---- positive control -----------------------------------------------------
    # Plant a defect in n_butanol's input VP (the sole HIGH/MODERATE boundary-
    # adjacent solvent in the panel) that shrinks its margin to the 100-line just
    # enough that the SAME worst-case-bias test must detect a band-assignment flip
    # it correctly does NOT detect on the real, unmutated panel.
    panel_obj = json.loads(panel_bytes)
    mutated = json.loads(json.dumps(panel_obj))
    for c in mutated["kpis"]["solvent_cards_ranked"]:
        if c["solvent"] == "n_butanol":
            # real VP=6.7 mmHg -> VHR=88.158 (MODERATE). Planted VP=6.992 mmHg
            # (+4.36%, a single-solvent transcription-scale VP error) -> VHR=92.0,
            # still baseline-MODERATE (band label unchanged at baseline) but now
            # within reach of the 100-line under the quantified bias
            # (92.0 * 1.11042 = 102.16 >= 100).
            c["vapor_pressure_mmHg_25C"] = 6.992
            c["vapor_hazard_ratio"] = round((6.992 / 760.0) * 1e6 / c["osha_pel_8h_twa_ppm"], 3)
            c["screening_band"] = band(c["vapor_hazard_ratio"])
    mutated_bytes = json.dumps(mutated).encode()
    planted = run(mutated_bytes, crossmethod_bytes, "planted_n_butanol_vp_defect")

    out = {
        "real": real,
        "positive_control": {
            "planted_defect": "n_butanol vapor_pressure_mmHg_25C mutated from the receipt's real 6.7 mmHg to 6.992 mmHg (+4.36%), a single-solvent transcription-scale VP error.",
            "how_planted": "In-memory deep copy of vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json with solvent_cards_ranked[n_butanol].vapor_pressure_mmHg_25C changed 6.7 -> 6.992; vapor_hazard_ratio (88.158 -> 92.0) and screening_band recomputed from the mutated VP using the identical VHR formula and band() thresholds as the real run. The on-disk receipt was NOT modified.",
            "detected": planted["any_band_assignment_flip"] is True,
            "evidence": planted,
        },
    }
    print(json.dumps(out, indent=2, sort_keys=True))
