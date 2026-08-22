#!/usr/bin/env python3
"""Attack on R-C02 (amphora-cure-potlife-gate LOSO bias-correction repair).

R-C02's own receipt (evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json)
lists under does_not_close: "Generalization to systems/hardener families outside the
fixture is untested." and its methodology note admits the correction "assumes the
curvature bias is shared in sign and rough magnitude across the 5 hardener families
present, which held on this fixture but is untested on any system outside it."

R-C02's own cross-validation (LOSO = leave-one-SYSTEM-out) is not group-safe at the
family level: 9 of 12 systems belong to a family with >=2 other members (aliphatic-
polyamine x3, cycloaliphatic-amine x3, aromatic-amine x3, amidoamine-adduct x2), so
when a system is held out, its own family-mates are STILL IN the pool used to compute
its correction factor. If the true generalization unit is "hardener family" rather
than "system", LOSO overstates how well this will transfer to a genuinely novel
chemistry family, because family-mates leak family-specific bias into the correction.

FALSIFYING ATTACK: re-run the IDENTICAL correction formula and IDENTICAL acceptance
bar from R-C02, but with LEAVE-ONE-FAMILY-OUT (LOFO) pooling: for held-out system s
in family F, the correction factor at leg L is computed from systems NOT in F only
(all family-mates of s are excluded, not just s itself). This is the harder,
group-safe (family-safe) split the R-C02 receipt explicitly flagged as untested.

Pre-registered falsification criterion (identical to R-C02's own acceptance bar,
carried over unmodified): the LOFO-corrected candidate must satisfy BOTH
  (a) 40C-leg MAPE <= 0.25
  (b) beats the Q10=2 heuristic (MAPE 0.1527) on >= 2 of 3 held-out legs
on the IDENTICAL locked 36-point truth table and metric used by R-C02 and
potlife-q10-heuristic-ablation-v1. If the LOFO-corrected candidate fails either
criterion while the LOSO-corrected candidate (R-C02) passed both, this demonstrates
LOSO's pass was inflated by within-family leakage and the R-C02 SURVIVED verdict
does not extend to the family-safe generalization regime it claims to be evidence
towards.
"""
import hashlib, json, math
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
KA_PATH = MOD / "reference/phase0-cure-potlife-known-answer.v1.json"
OUT_DIR = MOD / "evidence/audit/potlife-lofo-family-safe-v1/work"

R = 8.31446261815324
Q10 = 2.0
LEGS_C = {"10C": 10.0, "30C": 30.0, "40C": 40.0}


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


def run(systems, t_ref_c, t_ref_k, pooling):
    """pooling: 'lofo' (exclude same hardener_family) or 'loso' (exclude only self, for
    positive-control / cross-check reproduction of R-C02's own published numbers)."""
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
                "hardener_family": sysrec["hardener_family"],
            }

    per_system = []
    leg_errs = {leg: {"arrhenius": [], "q10": [], "corrected": []} for leg in LEGS_C}
    pooled = {"arrhenius": [], "q10": [], "corrected": []}
    pool_sizes = {}

    for sysrec in systems:
        sid = sysrec["system_id"]
        fam = sysrec["hardener_family"]
        row = {"system_id": sid, "hardener_family": fam, "legs": {}}
        for leg in LEGS_C:
            if pooling == "lofo":
                pool = [other["system_id"] for other in systems
                        if other["system_id"] != sid and other["hardener_family"] != fam]
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

from collections import Counter
family_counts = dict(Counter(s["hardener_family"] for s in systems))

lofo_result = run(systems, t_ref_c, t_ref_k, pooling="lofo")
loso_reproduction = run(systems, t_ref_c, t_ref_k, pooling="loso")

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
# unmodified incumbent Arrhenius model already known, from potlife-q10-heuristic-
# ablation-v1 and potlife-kpi-envelope-disclosure-gap-v1, to breach the 40C ceiling
# (25.12%) and lose to Q10 on 2/3 legs). The SAME acceptance-check logic used to
# evaluate the LOFO candidate must reject this planted defect, or the check cannot
# be trusted to license any verdict here.
defect_leg_summary = {}
defect_pooled = {"defect": []}
for leg in LEGS_C:
    errs = []
    for sysrec in systems:
        sid = sysrec["system_id"]
        ref_min = sysrec["pot_life_min_22_78c"]
        ea = sysrec["activation_energy_j_mol"]
        leg_k = c_to_k(LEGS_C[leg])
        obs = sysrec[f"pot_life_min_{leg.lower()}"]
        arr_pred = arrhenius_predict(ref_min, ea, t_ref_k, leg_k)
        errs.append(abs(arr_pred - obs) / obs)  # correction factor forced to 1.0
        defect_pooled["defect"].append(abs(arr_pred - obs) / obs)
    q10_mape_leg = lofo_result["leg_summary"][leg]["q10_mape"]
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
    "planted_defect": "correction_factor forced to 1.0 for every (system, leg) pair (same planted defect class as R-C02's own positive control: the candidate collapses to the unmodified incumbent Arrhenius model already known to breach the 40C ceiling and lose to Q10 on 2/3 legs)",
    "how_planted": "acceptance harness re-evaluated with corrected_predicted_min substituted by arrhenius_predicted_min (correction factor identically 1.0) for all 12 systems x 3 legs; dataset, Q10 baseline, MAPE formula, and thresholds held identical to the LOFO run",
    "detected": bool(not defect_acceptance["overall_met"]),
    "evidence": defect_acceptance,
}
assert positive_control["detected"], "positive control FAILED to detect the planted defect -- acceptance check cannot be trusted"

diagnostic = {
    "schema": "amphora.cure-potlife-gate.lofo-family-safe-attack-diagnostic.v1",
    "module": "amphora-cure-potlife-gate",
    "attacks": "amphora-cure-potlife-gate/evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json",
    "attack_type": "harder held-out split: leave-one-hardener-family-out (family-safe) vs leave-one-system-out (LOSO)",
    "dataset": {
        "fixture_id": ka["fixture_id"],
        "path": "amphora-cure-potlife-gate/reference/phase0-cure-potlife-known-answer.v1.json",
        "sha256": ka_sha,
        "n_systems": n_systems,
        "n_legs": 3,
        "n_pooled_points": n_systems * 3,
        "family_counts": family_counts,
    },
    "falsification_criterion": (
        "Identical to R-C02's own pre-registered acceptance bar, applied to the LOFO-corrected "
        "candidate: (a) 40C-leg MAPE <= 0.25 AND (b) beats Q10=2 heuristic (MAPE 0.1527) on >= 2 "
        "of 3 held-out legs, on the identical locked 36-point fixture and metric. If either fails "
        "while R-C02's LOSO variant passed both, R-C02's SURVIVED verdict is shown to depend on "
        "within-family leakage in its correction pool and does not hold under a family-safe split."
    ),
    "loso_reproduction": loso_reproduction,
    "loso_reproduction_matches_rc02_signed_numbers": loso_repro_matches_rc02,
    "lofo_result": lofo_result,
    "comparison": {
        leg: {
            "loso_corrected_mape": loso_reproduction["leg_summary"][leg]["corrected_mape"],
            "lofo_corrected_mape": lofo_result["leg_summary"][leg]["corrected_mape"],
            "degradation_pp": round(
                (lofo_result["leg_summary"][leg]["corrected_mape"] - loso_reproduction["leg_summary"][leg]["corrected_mape"]) * 100, 3),
        } for leg in LEGS_C
    },
    "positive_control": positive_control,
}

canon_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
(OUT_DIR / "diagnostic.canonical.json").write_bytes(canon_bytes)
(OUT_DIR / "diagnostic.runB.json").write_bytes(canon_bytes)

print(json.dumps({
    "family_counts": family_counts,
    "loso_reproduction_matches_rc02_signed_numbers": loso_repro_matches_rc02,
    "loso_leg_summary": loso_reproduction["leg_summary"],
    "lofo_leg_summary": lofo_result["leg_summary"],
    "lofo_acceptance": lofo_result["acceptance"],
    "comparison": diagnostic["comparison"],
    "positive_control_detected": positive_control["detected"],
}, indent=2))
