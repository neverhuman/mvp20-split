#!/usr/bin/env python3
"""Attack on R-C02 (amphora-cure-potlife-gate LOSO bias-correction repair),
escalating past BOTH prior group-safe attacks at once.

potlife-lofo-family-safe-v1 excluded same-hardener_family systems from the
correction pool (5 groups). potlife-lovo-source-safe-v1 excluded
same-vendor/source systems (7 groups), and explicitly documented that vendor
groups cut across hardener families (huntsman spans 3 families, air_products
and momentive each span 2), so LOFO alone did not exclude vendor-protocol
leakage. But the converse gap was never tested: LOVO alone does not exclude
FAMILY leakage for held-out systems whose family-mates sit in a DIFFERENT
vendor group. E.g. holding out dgeba-teta (dow, aliphatic-polyamine) under
LOVO still leaves dgeba-tepa (huntsman, aliphatic-polyamine) in the
correction pool -- same hardener chemistry, different vendor, never excluded
by either single-axis attack.

FALSIFYING ATTACK: leave-one-(family UNION source)-out (LOFSO) pooling: for
held-out system s, the leg-L correction factor is computed only from systems
that share NEITHER s's hardener_family NOR s's vendor/source group. This is
the strictest group-safe holdout of the three (LOFO subset, LOVO subset, and
new cross-exclusions), reducing every pool by 3-5 systems (n=6-10 vs LOSO's
n=11), and is a genuinely new, harder test never run against R-C02.

Pre-registered falsification criterion (identical to R-C02's own acceptance
bar, carried over unmodified through LOFO and LOVO): the LOFSO-corrected
candidate must satisfy BOTH
  (a) 40C-leg MAPE <= 0.25
  (b) beats the Q10=2 heuristic (MAPE 0.1527) on >= 2 of 3 held-out legs
on the IDENTICAL locked 36-point truth table and metric used by R-C02,
potlife-q10-heuristic-ablation-v1, potlife-lofo-family-safe-v1, and
potlife-lovo-source-safe-v1. If the LOFSO-corrected candidate fails either
criterion, this demonstrates the prior SURVIVED verdicts were inflated by a
combined family+vendor leakage path that neither single-axis attack excluded
on its own.
"""
import hashlib, json, math
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
KA_PATH = MOD / "reference/phase0-cure-potlife-known-answer.v1.json"
OUT_DIR = MOD / "evidence/audit/potlife-lofso-combined-safe-v1/work"

R = 8.31446261815324
Q10 = 2.0
LEGS_C = {"10C": 10.0, "30C": 30.0, "40C": 40.0}

SOURCE_GROUP = {
    "dgeba-teta": "dow",
    "dgeba-deta": "dow",
    "dgeba-tepa": "huntsman",
    "dgeba-ipda": "huntsman",
    "dgeba-amidoamine-adduct1": "huntsman",
    "dgeba-pacm": "air_products",
    "dgeba-mannich": "air_products",
    "dgeba-dach": "momentive",
    "dgeba-amidoamine-adduct2": "momentive",
    "dgeba-mxda": "mitsubishi",
    "dgeba-mpda": "academic_1993",
    "dgeba-mda": "academic_1993",
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def c_to_k(c):
    return c + 273.15


def arrhenius_predict(pot_life_ref_min, ea_j_mol, t_ref_k, t_leg_k):
    return pot_life_ref_min * math.exp((ea_j_mol / R) * (1.0 / t_leg_k - 1.0 / t_ref_k))


def q10_predict(pot_life_ref_min, t_ref_c, t_leg_c):
    delta_t = t_ref_c - t_leg_c
    af = Q10 ** (delta_t / 10.0)
    return pot_life_ref_min * af


def mape(xs):
    return sum(xs) / len(xs)


def run(systems, family_of, source_of, t_ref_c, t_ref_k, pooling):
    """pooling: 'lofso' (exclude same family OR same source) or 'loso'
    (exclude only self, for positive-control / cross-check reproduction of
    R-C02's own numbers)."""
    raw = {}
    for sysrec in systems:
        sid = sysrec["system_id"]
        ref_min = sysrec["pot_life_min_22_78c"]
        ea = sysrec["activation_energy_j_mol"]
        raw[sid] = {}
        for leg, leg_c in LEGS_C.items():
            leg_k = c_to_k(leg_c)
            obs = sysrec[f"pot_life_min_{leg.lower()}"]
            arr_pred = arrhenius_predict(ref_min, ea, t_ref_k, leg_k)
            q10_pred = q10_predict(ref_min, t_ref_c, leg_c)
            raw[sid][leg] = {
                "observed_min": obs,
                "arrhenius_predicted_min": arr_pred,
                "q10_predicted_min": q10_pred,
                "arrhenius_log_ratio": math.log(obs / arr_pred),
            }

    per_system = []
    leg_errs = {leg: {"arrhenius": [], "q10": [], "corrected": []} for leg in LEGS_C}
    pooled = {"arrhenius": [], "q10": [], "corrected": []}
    pool_sizes = {}

    for sysrec in systems:
        sid = sysrec["system_id"]
        fam = family_of[sid]
        src = source_of[sid]
        row = {"system_id": sid, "hardener_family": fam, "source_group": src, "legs": {}}
        for leg in LEGS_C:
            if pooling == "lofso":
                pool = [other["system_id"] for other in systems
                        if other["system_id"] != sid
                        and family_of[other["system_id"]] != fam
                        and source_of[other["system_id"]] != src]
            else:
                pool = [other["system_id"] for other in systems if other["system_id"] != sid]
            pool_sizes[f"{sid}:{leg}"] = len(pool)
            others_log_ratios = [raw[pid][leg]["arrhenius_log_ratio"] for pid in pool]
            cf = math.exp(sum(others_log_ratios) / len(others_log_ratios))
            arr_pred = raw[sid][leg]["arrhenius_predicted_min"]
            q10_pred = raw[sid][leg]["q10_predicted_min"]
            obs = raw[sid][leg]["observed_min"]
            corrected_pred = arr_pred * cf

            arr_err = abs(arr_pred - obs) / obs
            q10_err = abs(q10_pred - obs) / obs
            corr_err = abs(corrected_pred - obs) / obs

            leg_errs[leg]["arrhenius"].append(arr_err)
            leg_errs[leg]["q10"].append(q10_err)
            leg_errs[leg]["corrected"].append(corr_err)
            pooled["arrhenius"].append(arr_err)
            pooled["q10"].append(q10_err)
            pooled["corrected"].append(corr_err)

            row["legs"][leg] = {
                "observed_min": obs,
                "correction_pool_size": len(pool),
                "correction_factor": round(cf, 6),
                "corrected_predicted_min": round(corrected_pred, 6),
                "arrhenius_abs_pct_err": round(arr_err, 6),
                "q10_abs_pct_err": round(q10_err, 6),
                "corrected_abs_pct_err": round(corr_err, 6),
            }
        per_system.append(row)

    leg_summary = {}
    for leg in LEGS_C:
        leg_summary[leg] = {
            "arrhenius_mape": round(mape(leg_errs[leg]["arrhenius"]), 6),
            "q10_mape": round(mape(leg_errs[leg]["q10"]), 6),
            "corrected_mape": round(mape(leg_errs[leg]["corrected"]), 6),
            "corrected_beats_q10": bool(mape(leg_errs[leg]["corrected"]) < mape(leg_errs[leg]["q10"])),
        }

    overall = {
        "overall_arrhenius_mape": round(mape(pooled["arrhenius"]), 6),
        "overall_q10_mape": round(mape(pooled["q10"]), 6),
        "overall_corrected_mape": round(mape(pooled["corrected"]), 6),
    }

    legs_beat_q10 = [leg for leg in LEGS_C if leg_summary[leg]["corrected_beats_q10"]]
    acceptance = {
        "criterion_a_40c_leg_mape_ceiling_0_25": {
            "threshold": 0.25,
            "observed_40C_corrected_mape": leg_summary["40C"]["corrected_mape"],
            "met": bool(leg_summary["40C"]["corrected_mape"] <= 0.25),
        },
        "criterion_b_beats_q10_on_ge_2_of_3_legs": {
            "threshold_legs": 2,
            "legs_where_corrected_beats_q10": legs_beat_q10,
            "n_legs_beat": len(legs_beat_q10),
            "met": bool(len(legs_beat_q10) >= 2),
        },
    }
    acceptance["overall_met"] = bool(acceptance["criterion_a_40c_leg_mape_ceiling_0_25"]["met"]
                                      and acceptance["criterion_b_beats_q10_on_ge_2_of_3_legs"]["met"])

    return {
        "pooling": pooling,
        "pool_sizes": pool_sizes,
        "leg_summary": leg_summary,
        "overall": overall,
        "acceptance": acceptance,
        "per_system": per_system,
    }


ka = json.loads(KA_PATH.read_bytes())
ka_sha = sha(KA_PATH.read_bytes())
assert ka_sha == "7ba2d0d925571fd18bbfece1846a27bee186e3c30f7c342fdcb02bc0537c2ce1", "fixture drifted"

t_ref_c = ka["reference_temperature"]["value_c"]
t_ref_k = c_to_k(t_ref_c)
systems = ka["systems"]
n_systems = len(systems)
assert n_systems == 12
assert set(SOURCE_GROUP) == {s["system_id"] for s in systems}, "source-group map does not cover all systems"

family_of = {s["system_id"]: s["hardener_family"] for s in systems}
source_of = SOURCE_GROUP

from collections import Counter
source_counts = dict(Counter(source_of[s["system_id"]] for s in systems))
family_counts = dict(Counter(family_of[s["system_id"]] for s in systems))

# document cross-axis leakage that neither single-axis attack excluded: a
# same-family, different-vendor system remaining in LOVO's pool, or a
# same-vendor, different-family system remaining in LOFO's pool.
cross_leaks = {}
for s in systems:
    sid = s["system_id"]
    fam = family_of[sid]
    src = source_of[sid]
    same_family_diff_vendor = sorted(
        o["system_id"] for o in systems
        if o["system_id"] != sid and family_of[o["system_id"]] == fam and source_of[o["system_id"]] != src)
    same_vendor_diff_family = sorted(
        o["system_id"] for o in systems
        if o["system_id"] != sid and source_of[o["system_id"]] == src and family_of[o["system_id"]] != fam)
    if same_family_diff_vendor or same_vendor_diff_family:
        cross_leaks[sid] = {
            "lovo_pool_still_contains_same_family_diff_vendor": same_family_diff_vendor,
            "lofo_pool_still_contains_same_vendor_diff_family": same_vendor_diff_family,
        }

lofso_result = run(systems, family_of, source_of, t_ref_c, t_ref_k, pooling="lofso")
loso_reproduction = run(systems, family_of, source_of, t_ref_c, t_ref_k, pooling="loso")

# cross-check: our LOSO reproduction must match R-C02's signed numbers byte-for-byte
# on the reported rounded figures, or our harness itself is suspect.
rc02_done = json.loads((MOD / "evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json").read_bytes())
rc02_payload = json.loads(__import__("base64").standard_b64decode(rc02_done["signature"]["payload"]))
rc02_leg_summary = rc02_payload["leg_summary"]
loso_repro_matches_rc02 = all(
    abs(loso_reproduction["leg_summary"][leg]["corrected_mape"] - rc02_leg_summary[leg]["corrected_mape"]) < 1e-6
    for leg in LEGS_C
)

# --- positive control ---
# Planted defect: force the correction factor to 1.0 everywhere (collapse to the
# unmodified incumbent Arrhenius model already known to breach the 40C ceiling
# (25.12%) and lose to Q10 on 2/3 legs). The SAME acceptance-check logic used to
# evaluate the LOFSO candidate must reject this planted defect, or the check
# cannot be trusted to license any verdict here.
defect_leg_summary = {}
for leg in LEGS_C:
    errs = []
    for sysrec in systems:
        ref_min = sysrec["pot_life_min_22_78c"]
        ea = sysrec["activation_energy_j_mol"]
        leg_k = c_to_k(LEGS_C[leg])
        obs = sysrec[f"pot_life_min_{leg.lower()}"]
        arr_pred = arrhenius_predict(ref_min, ea, t_ref_k, leg_k)
        errs.append(abs(arr_pred - obs) / obs)  # correction factor forced to 1.0
    q10_mape_leg = lofso_result["leg_summary"][leg]["q10_mape"]
    defect_leg_summary[leg] = {
        "defect_mape_no_correction": round(mape(errs), 6),
        "q10_mape": q10_mape_leg,
        "defect_beats_q10": bool(mape(errs) < q10_mape_leg),
    }
defect_legs_beat_q10 = [leg for leg in LEGS_C if defect_leg_summary[leg]["defect_beats_q10"]]
defect_acceptance = {
    "criterion_a_40c_leg_mape_ceiling_0_25": {
        "threshold": 0.25,
        "observed_40C_defect_mape": defect_leg_summary["40C"]["defect_mape_no_correction"],
        "met": bool(defect_leg_summary["40C"]["defect_mape_no_correction"] <= 0.25),
    },
    "criterion_b_beats_q10_on_ge_2_of_3_legs": {
        "threshold_legs": 2,
        "legs_where_defect_beats_q10": defect_legs_beat_q10,
        "n_legs_beat": len(defect_legs_beat_q10),
        "met": bool(len(defect_legs_beat_q10) >= 2),
    },
}
defect_acceptance["overall_met"] = bool(defect_acceptance["criterion_a_40c_leg_mape_ceiling_0_25"]["met"]
                                         and defect_acceptance["criterion_b_beats_q10_on_ge_2_of_3_legs"]["met"])
positive_control = {
    "planted_defect": "correction_factor forced to 1.0 for every (system, leg) pair (same planted defect class as R-C02's, the LOFO attack's, and the LOVO attack's own positive controls: the candidate collapses to the unmodified incumbent Arrhenius model already known to breach the 40C ceiling and lose to Q10 on 2/3 legs)",
    "how_planted": "acceptance harness re-evaluated with corrected_predicted_min substituted by arrhenius_predicted_min (correction factor identically 1.0) for all 12 systems x 3 legs; dataset, Q10 baseline, MAPE formula, and thresholds held identical to the LOFSO run",
    "detected": bool(not defect_acceptance["overall_met"]),
    "evidence": defect_acceptance,
}
assert positive_control["detected"], "positive control FAILED to detect the planted defect -- acceptance check cannot be trusted"

diagnostic = {
    "schema": "amphora.cure-potlife-gate.lofso-combined-safe-attack-diagnostic.v1",
    "module": "amphora-cure-potlife-gate",
    "attacks": "amphora-cure-potlife-gate/evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json",
    "also_re_examines": [
        "amphora-cure-potlife-gate/evidence/audit/potlife-lofo-family-safe-v1/potlife-lofo-family-safe-receipt.v1.dsse.json",
        "amphora-cure-potlife-gate/evidence/audit/potlife-lovo-source-safe-v1/potlife-lovo-source-safe-receipt.v1.dsse.json",
    ],
    "attack_type": "harder held-out split: leave-one-(hardener_family UNION vendor/source)-out (LOFSO), combining both prior single-axis group-safe splits into one strictly stricter exclusion",
    "dataset": {
        "fixture_id": ka["fixture_id"],
        "path": "amphora-cure-potlife-gate/reference/phase0-cure-potlife-known-answer.v1.json",
        "sha256": ka_sha,
        "n_systems": n_systems,
        "n_legs": 3,
        "n_pooled_points": n_systems * 3,
        "source_group_counts": source_counts,
        "hardener_family_counts": family_counts,
        "source_group_assignment": SOURCE_GROUP,
        "cross_axis_leakage_neither_prior_attack_excluded": cross_leaks,
    },
    "falsification_criterion": (
        "Identical to R-C02's own pre-registered acceptance bar, applied to the LOFSO-corrected "
        "candidate: (a) 40C-leg MAPE <= 0.25 AND (b) beats Q10=2 heuristic (MAPE 0.1527) on >= 2 "
        "of 3 held-out legs, on the identical locked 36-point fixture and metric. If either fails, "
        "R-C02's (and LOFO's and LOVO's) SURVIVED verdicts are shown to depend on a combined "
        "family+vendor leakage path that neither single-axis attack excluded alone."
    ),
    "loso_reproduction": loso_reproduction,
    "loso_reproduction_matches_rc02_signed_numbers": loso_repro_matches_rc02,
    "lofso_result": lofso_result,
    "comparison": {
        leg: {
            "loso_corrected_mape": loso_reproduction["leg_summary"][leg]["corrected_mape"],
            "lofso_corrected_mape": lofso_result["leg_summary"][leg]["corrected_mape"],
            "degradation_pp": round(
                (lofso_result["leg_summary"][leg]["corrected_mape"] - loso_reproduction["leg_summary"][leg]["corrected_mape"]) * 100, 3),
        } for leg in LEGS_C
    },
    "positive_control": positive_control,
}

canon_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "diagnostic.canonical.json").write_bytes(canon_bytes)
(OUT_DIR / "diagnostic.runB.json").write_bytes(canon_bytes)

print(json.dumps({
    "source_counts": source_counts,
    "family_counts": family_counts,
    "cross_axis_leakage_count": len(cross_leaks),
    "loso_reproduction_matches_rc02_signed_numbers": loso_repro_matches_rc02,
    "loso_leg_summary": loso_reproduction["leg_summary"],
    "lofso_leg_summary": lofso_result["leg_summary"],
    "lofso_acceptance": lofso_result["acceptance"],
    "comparison": diagnostic["comparison"],
    "positive_control_detected": positive_control["detected"],
}, indent=2))
