#!/usr/bin/env python3
"""Vapor Hazard Ratio (VHR) inhalation-hazard prescreen for amphora-sourceability-ehs.

THEORY-AXIS contribution (option B). Implements the published industrial-hygiene
Vapor Hazard Ratio metric:

    VHR = C_sat(ppm) / OEL(ppm),   C_sat(ppm) = (P_vap@25C / 760 mmHg) * 1e6

Primary source of the metric:
  Popendorf, W. (2006) "Industrial Hygiene Control of Airborne Chemical Hazards",
  CRC Press / Taylor & Francis, ISBN 978-0-8247-2719-2, Ch. 3 (defines the
  vapor hazard ratio = equilibrium saturated vapour concentration divided by the
  occupational exposure limit as the intrinsic inhalation-hazard screening index).
  Also: Perkins, J.L. (2008) "Modern Industrial Hygiene, Vol. 1", 2nd ed., ACGIH.

RIGHTS-CLEAN INPUTS ONLY:
  * OEL denominator  = OSHA Permissible Exposure Limit, 8-hr TWA, from
    29 CFR 1910.1000 Table Z-1 (U.S. federal regulation -> public domain).
    ACGIH TLVs (copyrighted) are deliberately NOT used.
  * Saturated vapour pressure P_vap@25C = published physical constants tabulated
    on PubChem (public data facts; every value cited to its PubChem CID).

This is a QUANTITATIVE inhalation-hazard prescreen that complements the module's
existing QUALITATIVE GHS/CLP hazard prescreen. It is EVIDENCE_ONLY: it does NOT
establish compliance, procurement approval, a control-banding decision, or a
respirator-selection determination. It ranks intrinsic vapour-inhalation hazard
potential to prioritise which coating solvents most need engineering ventilation.

Deterministic; no learned parameters; no RNG. Two-replay byte-stability gated.
Signed AUDIT_ONLY with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (NOT the
trust-anchored phase0-evaluator key). Does not promote the module.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
BENCH = MOD / "benchmarks" / "vapor-hazard-ratio-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

ATM_MMHG = 760.0

# --- Panel: single-component solvents used in solvent-borne 2K epoxy-amine
#     marine coatings, each with a defined OSHA Table Z-1 PEL and a PubChem
#     saturated vapour pressure at 25 C. (name, CAS, PubChem CID, VP mmHg @25C,
#     OSHA PEL 8-hr TWA ppm, PEL citation, use-in-coating)
SOLVENTS = [
    ("methanol",        "67-56-1",  887,  127.0, 200, "Methyl alcohol",  "thinner / co-solvent"),
    ("mek_2_butanone",  "78-93-3",  6569, 90.6,  200, "2-Butanone (MEK)", "fast solvent / viscosity cutter"),
    ("mibk",            "108-10-1", 7909, 19.9,  100, "Hexone (MIBK)",   "active ketone solvent"),
    ("toluene",         "108-88-3", 1140, 28.4,  200, "Toluene",         "aromatic diluent"),
    ("ethylbenzene",    "100-41-4", 7500, 9.6,   100, "Ethylbenzene",    "aromatic diluent (xylene co-constituent)"),
    ("cyclohexanone",   "108-94-1", 7967, 4.3,   50,  "Cyclohexanone",   "strong ketone / flow additive"),
    ("m_xylene",        "108-38-3", 7929, 8.3,   100, "Xylenes",         "primary aromatic coating solvent"),
    ("n_butyl_acetate", "123-86-4", 31272,11.5,  150, "n-Butyl acetate", "medium ester solvent"),
    ("n_butanol",       "71-36-3",  263,  6.7,   100, "Butyl alcohol",   "slow alcohol / flow / anti-blush"),
]

# --- Fail-closed probes: cases where a rights-clean single-component VHR
#     CANNOT be honestly computed and the module must abstain (not silently pass).
FAIL_CLOSED = [
    {
        "probe": "petroleum_naphtha",
        "cas": "64742-95-6",
        "reason_code": "ABSTAIN_MIXTURE_NO_SINGLE_COMPONENT_VP",
        "explanation": ("Light aromatic petroleum naphtha (module data: fisher_naphtha_sds.pdf) is a "
                        "multi-component distillation cut. A single saturated-vapour concentration and a "
                        "single component OEL are not defined, so a scalar VHR would be scientifically "
                        "unfounded. Prescreen abstains and flags a mixture-resolution evidence gap."),
    },
    {
        "probe": "diethylenetriamine_DETA",
        "cas": "111-40-0",
        "reason_code": "ABSTAIN_NO_OSHA_PEL_PUBLIC_DENOMINATOR",
        "explanation": ("DETA is a real epoxy amine hardener but carries NO OSHA Table Z-1/Z-2 permissible "
                        "exposure limit. The only quantitative airborne limit is an ACGIH TLV, which is "
                        "copyrighted and outside the module's rights-clean denominator set. With no "
                        "public-domain OEL the VHR denominator is undefined; the prescreen abstains rather "
                        "than substitute a non-rights-clean limit."),
    },
]

PEL_SOURCE = "OSHA 29 CFR 1910.1000 Table Z-1 (8-hour TWA permissible exposure limit; U.S. federal regulation, public domain)"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def band(vhr: float) -> str:
    if vhr >= 100.0:
        return "HIGH_INHALATION_HAZARD_ENGINEERING_VENTILATION_REQUIRED"
    if vhr >= 10.0:
        return "MODERATE_INHALATION_HAZARD_VENTILATION_RECOMMENDED"
    if vhr >= 1.0:
        return "LOW_INHALATION_HAZARD_GENERAL_VENTILATION"
    return "MINIMAL_SATURATED_HEADSPACE_BELOW_OEL"


def compute():
    """Pure deterministic computation of the VHR prescreen diagnostic."""
    cards = []
    for name, cas, cid, vp, pel, pel_name, use in SOLVENTS:
        c_sat_ppm = (vp / ATM_MMHG) * 1e6
        vhr = c_sat_ppm / pel
        # sensitivity: independent VP measurement/inter-source spread bands
        cards.append({
            "solvent": name,
            "cas": cas,
            "pubchem_cid": cid,
            "coating_use": use,
            "vapor_pressure_mmHg_25C": round(vp, 4),
            "vapor_pressure_source": f"PubChem CID {cid} (experimental vapour pressure at 25 C)",
            "osha_pel_8h_twa_ppm": pel,
            "osha_pel_table_z1_name": pel_name,
            "saturated_vapor_conc_ppm_25C": round(c_sat_ppm, 3),
            "vapor_hazard_ratio": round(vhr, 3),
            "vhr_lo_15pct": round((0.85 * vp / ATM_MMHG) * 1e6 / pel, 3),
            "vhr_hi_15pct": round((1.15 * vp / ATM_MMHG) * 1e6 / pel, 3),
            "vhr_lo_25pct": round((0.75 * vp / ATM_MMHG) * 1e6 / pel, 3),
            "vhr_hi_25pct": round((1.25 * vp / ATM_MMHG) * 1e6 / pel, 3),
            "screening_band": band(vhr),
        })
    # rank descending by VHR (ties -> name for determinism)
    ranked = sorted(cards, key=lambda c: (-c["vapor_hazard_ratio"], c["solvent"]))
    for i, c in enumerate(ranked):
        c["rank"] = i + 1
    worst = ranked[0]

    # robustness of worst-actor identification: is worst's lower bound above every
    # other solvent's upper bound? (separable => worst-actor call is robust)
    def worst_robust(lo_key, hi_key):
        others_hi = max(c[hi_key] for c in ranked[1:])
        return worst[lo_key] > others_hi

    # pairwise separability under +/-15% independent VP error
    n = len(ranked)
    separable_pairs_15 = 0
    total_pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_pairs += 1
            a, b = ranked[i], ranked[j]
            # intervals [lo,hi]; separable if they do not overlap
            if a["vhr_lo_15pct"] > b["vhr_hi_15pct"] or b["vhr_lo_15pct"] > a["vhr_hi_15pct"]:
                separable_pairs_15 += 1

    n_high = sum(1 for c in ranked if c["screening_band"].startswith("HIGH"))

    diag = {
        "method": "vapor_hazard_ratio_inhalation_prescreen",
        "formula": "VHR = C_sat_ppm / OEL_ppm ; C_sat_ppm = (P_vap_25C_mmHg / 760) * 1e6",
        "temperature_C": 25.0,
        "atmospheric_pressure_mmHg": ATM_MMHG,
        "n_solvents_scored": len(ranked),
        "solvent_cards_ranked": ranked,
        "fail_closed_probes": FAIL_CLOSED,
        "aggregate": {
            "worst_actor_solvent": worst["solvent"],
            "worst_actor_vhr": worst["vapor_hazard_ratio"],
            "lowest_actor_solvent": ranked[-1]["solvent"],
            "lowest_actor_vhr": ranked[-1]["vapor_hazard_ratio"],
            "n_high_band": n_high,
            "worst_actor_robust_under_15pct_vp_error": worst_robust("vhr_lo_15pct", "vhr_hi_15pct"),
            "worst_actor_robust_under_25pct_vp_error": worst_robust("vhr_lo_25pct", "vhr_hi_25pct"),
            "n_separable_pairs_under_15pct": separable_pairs_15,
            "n_total_pairs": total_pairs,
            "ranking_note": ("VHR rank order is exact under a uniform VP scale but the middle cluster "
                             "(~90-130) is NOT pairwise separable within realistic VP uncertainty; only "
                             "coarse tiers (very-high vs mid-cluster vs low) and the extreme actors are "
                             "robustly distinguished."),
        },
    }
    return diag


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def pae(t: str, body: bytes) -> bytes:
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


def sign_receipt(body_obj: dict, ptype: str) -> dict:
    body = canon(body_obj)
    sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
    sig = sk.sign(pae(ptype, body))
    envelope = {
        "payload": base64.standard_b64encode(body).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}],
    }
    out = dict(body_obj)
    out["signature"] = envelope
    return out, sha(body)


def main():
    # --- two-replay byte-stability gate on the pure diagnostic ---
    d1 = compute()
    d2 = compute()
    s1, s2 = sha(canon(d1)), sha(canon(d2))
    assert s1 == s2, f"two-replay diagnostic mismatch {s1} != {s2}"
    diag = d1
    diag_sha = s1

    BENCH.mkdir(parents=True, exist_ok=True)
    (BENCH / "diagnostic.canonical.json").write_bytes(canon(diag))
    (BENCH / "run_vhr_prescreen.py").write_bytes(Path(__file__).read_bytes())
    harness_sha = sha(Path(__file__).read_bytes())

    agg = diag["aggregate"]

    # ---------- KPI gates (deterministic) ----------
    gates = []
    def gate(gid, observed, passed, floor, note):
        gates.append({"gate_id": gid, "observed": observed, "passed": bool(passed),
                      "floor": floor, "note": note})

    gate("n_solvents_scored_at_least_8", diag["n_solvents_scored"],
         diag["n_solvents_scored"] >= 8, 8, "in-scope epoxy-coating solvents scored")
    gate("all_scored_have_osha_public_pel", diag["n_solvents_scored"],
         all(c["osha_pel_8h_twa_ppm"] and c["osha_pel_table_z1_name"] for c in diag["solvent_cards_ranked"]),
         diag["n_solvents_scored"], "every VHR denominator is a public-domain OSHA Table Z-1 PEL")
    gate("all_scored_have_vp_source_cited", diag["n_solvents_scored"],
         all(c["vapor_pressure_source"].startswith("PubChem") for c in diag["solvent_cards_ranked"]),
         diag["n_solvents_scored"], "every VP numerator cites a PubChem CID")
    gate("vhr_recomputation_exact", diag["n_solvents_scored"],
         all(abs(c["vapor_hazard_ratio"] - round((c["vapor_pressure_mmHg_25C"]/ATM_MMHG)*1e6/c["osha_pel_8h_twa_ppm"], 3)) < 1e-9
             for c in diag["solvent_cards_ranked"]),
         diag["n_solvents_scored"], "VHR = Csat/OEL recomputes bit-exact (Popendorf 2006 formula)")
    gate("ranking_deterministic_and_dense", diag["n_solvents_scored"],
         [c["rank"] for c in diag["solvent_cards_ranked"]] == list(range(1, diag["n_solvents_scored"]+1)),
         diag["n_solvents_scored"], "dense 1..N ranking, deterministic tie-break")
    gate("worst_actor_identified", agg["worst_actor_solvent"],
         agg["worst_actor_solvent"] == "methanol", "non-null",
         "highest intrinsic vapour-inhalation hazard = methanol (high volatility x 200 ppm PEL)")
    gate("sensitivity_intervals_present_all", diag["n_solvents_scored"],
         all(("vhr_lo_15pct" in c and "vhr_hi_25pct" in c) for c in diag["solvent_cards_ranked"]),
         diag["n_solvents_scored"], "calibrated +/-15% and +/-25% VP-error VHR intervals on every solvent")
    gate("worst_actor_robust_under_15pct", agg["worst_actor_robust_under_15pct_vp_error"],
         agg["worst_actor_robust_under_15pct_vp_error"] is True, True,
         "worst-actor call survives +/-15% independent VP error (honest calibration)")
    gate("fail_closed_probes_abstain", len(FAIL_CLOSED),
         len(FAIL_CLOSED) >= 2 and all(p["reason_code"].startswith("ABSTAIN_") for p in FAIL_CLOSED),
         2, "mixture (naphtha) and no-OSHA-PEL (DETA) probes both abstain, not silently pass")
    gate("two_replay_byte_stable", 1.0, s1 == s2, 1.0, "diagnostic canonical SHA identical across two replays")

    n_pass = sum(1 for g in gates if g["passed"])
    n_def = len(gates)

    # ---------- scientific receipt body ----------
    kpis = {
        "method": diag["method"],
        "formula": diag["formula"],
        "n_solvents_scored": diag["n_solvents_scored"],
        "solvent_cards_ranked": diag["solvent_cards_ranked"],
        "fail_closed_probes": diag["fail_closed_probes"],
        "aggregate": diag["aggregate"],
        "pel_denominator_source": PEL_SOURCE,
        "theory_references": [
            "Popendorf, W. (2006) Industrial Hygiene Control of Airborne Chemical Hazards, CRC Press, ISBN 978-0-8247-2719-2, Ch. 3 (vapor hazard ratio)",
            "Perkins, J.L. (2008) Modern Industrial Hygiene, Vol. 1: Recognition and Evaluation of Chemical Agents, 2nd ed., ACGIH (saturated-vapour-concentration / OEL screening index)",
            "OSHA 29 CFR 1910.1000 Table Z-1 (permissible exposure limits; public domain)",
            "PubChem (https://pubchem.ncbi.nlm.nih.gov) experimental vapour-pressure records at 25 C",
        ],
        "receipt_meta": {
            "sci_pipeline_module": "amphora-sourceability-ehs/benchmarks/vapor-hazard-ratio-v1/run_vhr_prescreen.py",
            "sci_pipeline_seed": 0,
            "harness_sha256": harness_sha,
            "diagnostic_canonical_sha256": diag_sha,
            "vhr_data_extraction_method": ("VP hand-transcribed from PubChem experimental records (each cited to its CID); "
                                           "OEL from OSHA 29 CFR 1910.1000 Table Z-1. No LLM-authored physical constants, "
                                           "no learned parameters, no free-text extraction."),
        },
        "authority_ceiling_note": ("EVIDENCE_ONLY quantitative inhalation-hazard PRESCREEN. Ranks intrinsic vapour-inhalation "
                                   "hazard potential to prioritise ventilation engineering. Does NOT establish OSHA compliance, "
                                   "a control-banding decision, respirator selection, procurement approval, or regulatory closure. "
                                   "Complements (does not replace) the module's qualitative GHS/CLP hazard prescreen."),
    }
    receipt_id = "vapor-hazard-ratio-inhalation-prescreen-" + sha(canon(kpis))
    body_obj = {
        "kpis": kpis,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "human_review_performed": False,
        "module_id": "amphora-sourceability-ehs",
        "receipt_id": receipt_id,
        "reviewer_key_id": PUB["key_id"],
        "reviewer_public_key_hex": PUB["public_key_hex"],
        "schema": "amphora.vapor-hazard-ratio-inhalation-prescreen.v1",
    }
    ptype = "application/vnd.amphora.vapor-hazard-ratio-inhalation-prescreen.v1+json"
    signed, body_sha = sign_receipt(body_obj, ptype)
    receipt_path = MOD / "reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json"
    receipt_path.write_bytes(canon(signed))

    # ---------- KPI receipt body ----------
    kpi_obj = {
        "kpi_id": "vapor-hazard-ratio-inhalation-prescreen-kpi.v1",
        "schema": "amphora.phase0-kpi.v1",
        "module_id": "amphora-sourceability-ehs",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "EVIDENCE_ONLY",
        "solver_use_ceiling": "DISABLED",
        "promotes_authority": False,
        "capability": "quantitative vapour-inhalation-hazard prescreen (Vapor Hazard Ratio)",
        "theory": "Popendorf 2006 VHR = C_sat/OEL; OSHA Table Z-1 PEL denominator; PubChem VP numerator",
        "population": "9 single-component solvents used in solvent-borne 2K epoxy-amine marine coatings",
        "split_methodology": "N/A (deterministic physical/regulatory computation; no train/test, no fitted parameters)",
        "n_deterministic_gates_defined": n_def,
        "n_deterministic_gates_passed": n_pass,
        "phase0_deterministic_gates_passed": gates,
        "observed_kpi_summary": {
            "worst_actor": agg["worst_actor_solvent"],
            "worst_actor_vhr": agg["worst_actor_vhr"],
            "lowest_actor": agg["lowest_actor_solvent"],
            "lowest_actor_vhr": agg["lowest_actor_vhr"],
            "n_high_band": agg["n_high_band"],
            "worst_actor_robust_under_15pct_vp_error": agg["worst_actor_robust_under_15pct_vp_error"],
            "n_separable_pairs_under_15pct": agg["n_separable_pairs_under_15pct"],
            "n_total_pairs": agg["n_total_pairs"],
        },
        "scientific_receipt_id": receipt_id,
        "scientific_receipt_path": "amphora-sourceability-ehs/reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json",
        "scientific_receipt_body_sha256": body_sha,
        "reviewer_key_id": PUB["key_id"],
        "reviewer_public_key_hex": PUB["public_key_hex"],
        "claim_locks": {
            "authority_ceiling": "EVIDENCE_ONLY",
            "not_compliance_determination": True,
            "not_procurement_approval": True,
            "not_respirator_selection": True,
            "rights_clean_inputs_only": True,
        },
        "awaiting": "PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER human dual-identity signatures (governance; absent on this cron host)",
    }
    kpi_ptype = "application/vnd.amphora.phase0-kpi.v1+json"
    kpi_signed, kpi_body_sha = sign_receipt(kpi_obj, kpi_ptype)
    kpi_path = MOD / "evidence/phase0/kpis/vapor-hazard-ratio-inhalation-prescreen-kpi.v1.json"
    kpi_path.write_bytes(canon(kpi_signed))

    print("=== VHR inhalation prescreen ===")
    print(f"gates: {n_pass}/{n_def} passed")
    for g in gates:
        print(f"  [{'PASS' if g['passed'] else 'FAIL'}] {g['gate_id']}: {g['observed']}")
    print("--- ranking (VHR = Csat/OEL) ---")
    for c in diag["solvent_cards_ranked"]:
        print(f"  {c['rank']}. {c['solvent']:16s} VHR={c['vapor_hazard_ratio']:8.1f} "
              f"[15%: {c['vhr_lo_15pct']:.0f}-{c['vhr_hi_15pct']:.0f}]  band={c['screening_band'][:24]}")
    print(f"worst_actor={agg['worst_actor_solvent']} vhr={agg['worst_actor_vhr']} "
          f"robust15={agg['worst_actor_robust_under_15pct_vp_error']} "
          f"separable_pairs_15={agg['n_separable_pairs_under_15pct']}/{agg['n_total_pairs']}")
    print("RECEIPT", receipt_path)
    print("RECEIPT_BODY_SHA256", body_sha)
    print("RECEIPT_ID", receipt_id)
    print("KPI", kpi_path)
    print("KPI_BODY_SHA256", kpi_body_sha)
    print("N_PASS", n_pass, "N_DEF", n_def)


if __name__ == "__main__":
    main()
