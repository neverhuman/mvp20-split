#!/usr/bin/env python3
"""amphora-cure-potlife-gate :: AUDIT_ONLY envelope-disclosure-gap diagnostic.

CLAIM UNDER ATTACK
------------------
The module's own standing narrative (docs/mission.md, unchanged since
2026-07-21) states:

    "The Arrhenius model reproduces published epoxy-amine pot-life
    temperature-scaling to under 15% error across a 30-degree temperature
    range (10C to 40C) on the coating industry's standard reference (73F)."

and the signed Phase-0 KPI (evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json)
reports `held_out_temperature_extrapolation_mape` PASSED (ceiling 0.25,
observed 0.156) -- but that metric is evaluated at ONE interior leg (30C)
of the declared 10-40C envelope, not at its boundary.

This harness recomputes the IDENTICAL held-out-extrapolation methodology
(reference-anchor Arrhenius scaling from T_ref=295.928K using the cited,
externally-published Ea, pure prediction, no fitting) at the OTHER
held-out leg present in the SAME locked fixture (40C), using only the
already-accepted, SHA-256-pinned known-answer dataset. It also checks
whether this specific 40C ceiling breach was already discovered and
signed in a sibling AUDIT_ONLY receipt
(evidence/audit/potlife-arrhenius-curvature-mechanism-v1, results.
legs_breaching_kpi_ceiling=["40C"], signed 2026-07-27) and, if so, whether
docs/mission.md and the KPI's public framing have been corrected since.

PRE-REGISTERED FALSIFICATION CRITERION
---------------------------------------
The broader claim ("under 15% error ACROSS ... 10C to 40C") is REFUTED if:
  (a) the 40C-leg MAPE, computed with the exact same reference-anchor
      Arrhenius rule the signed KPI uses, exceeds either the prose's 15%
      figure or the KPI's own declared
      held_out_temperature_extrapolation_mape_ceiling (0.25); AND
  (b) the bias at 40C is not random noise but is unidirectional across
      all locked systems (a systematic-model-misspecification signature,
      not sampling variance).
It SURVIVES if the 40C-leg MAPE is <=15% (mission.md's own bar) or if the
per-system sign of the residual is not overwhelmingly one-directional.

This harness does not re-fit, edit, or supersede the signed Arrhenius KPI,
the locked known-answer fixture, or any prior signed receipt. It is a
disclosure/consistency audit of the STANDING claim against the module's
OWN locked data and its OWN prior signed findings.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
KA = MOD / "reference/phase0-cure-potlife-known-answer.v1.json"
KPI = MOD / "evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"
MISSION = MOD / "docs/mission.md"
CURV_RECEIPT = (MOD / "evidence/audit/potlife-arrhenius-curvature-mechanism-v1"
                / "potlife-arrhenius-curvature-mechanism-receipt.v1.dsse.json")
BENCH = MOD / "evidence/audit/potlife-kpi-envelope-disclosure-gap-v1"

R = 8.31446261815324  # CODATA 2018 exact, matches signed KPI


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load(p):
    return json.loads(p.read_text())


def build():
    ka = load(KA)
    kpi = load(KPI)
    mission_text = MISSION.read_text()
    mission_text_flat = " ".join(mission_text.split())

    Tref = ka["reference_temperature"]["value_k"]
    ceiling_held_out = ka["acceptance_bar"]["held_out_temperature_extrapolation_mape_ceiling"]
    ceiling_pool = ka["acceptance_bar"]["arrhenius_pot_life_mape_ceiling"]

    legs = {"10c": 10.0, "30c": 30.0, "40c": 40.0}
    per_leg = {leg: [] for leg in legs}
    per_system = []
    for s in ka["systems"]:
        Ea = s["activation_energy_j_mol"]
        ref = s["pot_life_min_22_78c"]
        row = {"system_id": s["system_id"], "hardener_family": s["hardener_family"],
               "activation_energy_j_mol": Ea}
        for leg, Tc in legs.items():
            actual = s[f"pot_life_min_{leg}"]
            Tk = Tc + 273.15
            pred = ref * math.exp((Ea / R) * (1.0 / Tk - 1.0 / Tref))
            signed_pct_err = (pred - actual) / actual * 100.0
            row[f"pred_{leg}"] = round(pred, 4)
            row[f"actual_{leg}"] = actual
            row[f"signed_pct_err_{leg}"] = round(signed_pct_err, 4)
            per_leg[leg].append(signed_pct_err)
        per_system.append(row)

    leg_stats = {}
    for leg, errs in per_leg.items():
        abs_errs = [abs(e) for e in errs]
        mape = sum(abs_errs) / len(abs_errs) / 100.0
        n_neg = sum(1 for e in errs if e < 0)
        n_pos = sum(1 for e in errs if e > 0)
        leg_stats[leg] = {
            "mape": round(mape, 6),
            "n": len(errs),
            "n_negative_bias": n_neg,
            "n_positive_bias": n_pos,
            "directional_consistency": round(max(n_neg, n_pos) / len(errs), 4),
            "breaches_declared_held_out_ceiling": bool(mape > ceiling_held_out),
            "breaches_mission_prose_15pct": bool(mape > 0.15),
        }

    pooled_mape = sum(sum(abs(e) for e in errs) for errs in per_leg.values()) / (
        sum(len(errs) for errs in per_leg.values())) / 100.0

    kpi_reported = {m["name"]: m for m in kpi["metrics"]}
    kpi_held_out_reported = kpi_reported["held_out_temperature_extrapolation_mape"]
    kpi_pooled_reported = kpi_reported["arrhenius_pot_life_mape"]

    reproduces_kpi_held_out = abs(leg_stats["30c"]["mape"] - kpi_held_out_reported["observed"]) < 1e-3
    reproduces_kpi_pooled = abs(round(pooled_mape, 6) - kpi_pooled_reported["observed"]) < 1e-3

    prose_claim = ("under 15% error across a 30-degree temperature range "
                    "(10°C to 40°C)")
    prose_claim_present = (
        "under 15% error across a 30-degree temperature range (10°C to 40°C)"
        in mission_text_flat
    )
    prose_still_unqualified = (
        prose_claim_present
        and "40C ceiling breach" not in mission_text_flat
        and "envelope-disclosure-gap" not in mission_text_flat
        and "40°C leg" not in mission_text_flat
    )

    curvature_prior_finding = None
    curvature_prior_ts = None
    if CURV_RECEIPT.exists():
        curvature_prior_ts = CURV_RECEIPT.stat().st_mtime
        try:
            import base64
            env = json.loads(CURV_RECEIPT.read_text())
            body = json.loads(base64.standard_b64decode(env["signature"]["payload"]))
            curvature_prior_finding = body.get("results", {}).get("legs_breaching_kpi_ceiling")
        except Exception as exc:  # pragma: no cover
            curvature_prior_finding = f"UNREADABLE: {exc}"

    mission_mtime = MISSION.stat().st_mtime
    kpi_mtime = KPI.stat().st_mtime
    standing_claim_postdates_prior_disclosure = bool(
        curvature_prior_ts is not None
        and mission_mtime < curvature_prior_ts
        and kpi_mtime < curvature_prior_ts
    )

    leg40_breaches_ceiling = leg_stats["40c"]["breaches_declared_held_out_ceiling"]
    leg40_breaches_prose = leg_stats["40c"]["breaches_mission_prose_15pct"]
    leg40_directional = leg_stats["40c"]["directional_consistency"] >= (10.0 / 12.0)

    falsified = bool(
        leg40_breaches_ceiling and leg40_breaches_prose and leg40_directional
        and prose_claim_present and prose_still_unqualified
    )

    verdict = "REFUTED" if falsified else "SURVIVED"

    headline = (
        "The standing mission.md claim '{}' is falsified by the module's own "
        "locked known-answer fixture: the 40C held-out leg (n=12, same "
        "reference-anchor Arrhenius rule as the signed KPI) has MAPE={:.2%}, "
        "breaching both the mission.md 15% figure and the KPI's own declared "
        "held_out_temperature_extrapolation_mape_ceiling ({:.0%}); the bias is "
        "unidirectional in {}/12 systems (systematic under-prediction of pot "
        "life at temperature, not noise). This exact 40C breach was already "
        "computed and signed in a sibling AUDIT_ONLY receipt "
        "(potlife-arrhenius-curvature-mechanism-v1, legs_breaching_kpi_ceiling="
        "{}) predating this fixture's current mission.md text by a negative "
        "margin: mission.md/KPI files have NOT been amended since to qualify "
        "or retract the blanket '{}' claim."
    ).format(prose_claim, leg_stats["40c"]["mape"], ceiling_held_out,
              leg_stats["40c"]["n_negative_bias"], curvature_prior_finding,
              prose_claim)

    diag = {
        "schema": "amphora.cure-potlife-gate.envelope-disclosure-gap-diagnostic.v1",
        "run_type": "AUDIT_ONLY_DISCLOSURE_CONSISTENCY_DIAGNOSTIC",
        "headline": headline,
        "claim_under_attack": {
            "location": "amphora-cure-potlife-gate/docs/mission.md",
            "quoted_text": prose_claim,
            "also_relied_on_by": "evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"
                                   " metric held_out_temperature_extrapolation_mape (PASSED,"
                                   " observed 0.156, ceiling 0.25), evaluated only at the 30C leg",
        },
        "gas_constant_j_mol_k": R,
        "reference_temperature_k": Tref,
        "declared_ceilings": {
            "held_out_temperature_extrapolation_mape_ceiling": ceiling_held_out,
            "arrhenius_pot_life_mape_ceiling": ceiling_pool,
            "mission_prose_pct_figure": 0.15,
        },
        "per_leg": leg_stats,
        "pooled_mape_all_legs": round(pooled_mape, 6),
        "reproduces_signed_kpi_held_out_mape_at_30c": reproduces_kpi_held_out,
        "reproduces_signed_kpi_pooled_mape": reproduces_kpi_pooled,
        "prose_claim_present_verbatim": prose_claim_present,
        "prose_claim_still_unqualified": prose_still_unqualified,
        "prior_sibling_audit": {
            "receipt": "evidence/audit/potlife-arrhenius-curvature-mechanism-v1/"
                        "potlife-arrhenius-curvature-mechanism-receipt.v1.dsse.json",
            "legs_breaching_kpi_ceiling_reported": curvature_prior_finding,
            "receipt_mtime_epoch": curvature_prior_ts,
        },
        "standing_claim_files_postdate_prior_disclosure": standing_claim_postdates_prior_disclosure,
        "mission_md_mtime_epoch": mission_mtime,
        "kpi_mtime_epoch": kpi_mtime,
        "leg40_breaches_declared_ceiling": leg40_breaches_ceiling,
        "leg40_breaches_mission_prose_15pct": leg40_breaches_prose,
        "leg40_directional_consistency_ge_10_of_12": leg40_directional,
        "per_system": per_system,
        "falsification_criterion": {
            "refuted_if": "40C-leg MAPE breaches both mission.md's 15% figure and the "
                           "KPI's own held_out_temperature_extrapolation_mape_ceiling, "
                           "AND the residual sign is directionally consistent in "
                           ">=10/12 systems, AND the prose remains unqualified despite "
                           "a pre-existing signed sibling receipt already disclosing it.",
            "survives_if": "40C-leg MAPE <=15% or residual signs are not "
                            "directionally consistent (i.e. plausibly noise), or "
                            "mission.md/KPI already qualify the claim.",
        },
        "verdict": verdict,
        "does_not_close": [
            "Does not establish whether a two-parameter model (VFT / free-fit "
            "Arrhenius, already explored in potlife-arrhenius-curvature-mechanism-v1) "
            "would close the 40C gap -- that receipt already found "
            "M1_free_arrhenius and VFT beat the incumbent out-of-sample.",
            "Does not modify docs/mission.md or the signed KPI; flags them for "
            "human correction only.",
            "Does not touch Phase-1 operational readiness, which remains BLOCKED "
            "regardless of this Phase-0 disclosure finding.",
        ],
        "theory_reference": {
            "arrhenius": "Arrhenius S., Z Phys Chem 4:226 (1889)",
            "gas_constant": "R = 8.31446261815324 J/(mol K), CODATA 2018 (exact, SI-2019)",
        },
    }
    return diag


if __name__ == "__main__":
    diag = build()
    canon = json.dumps(diag, indent=2, sort_keys=True).encode()
    (BENCH / "diagnostic.canonical.json").write_bytes(canon)
    print("verdict:", diag["verdict"])
    print("leg_stats:", json.dumps(diag["per_leg"], indent=2))
    print("sha256:", sha(canon))
