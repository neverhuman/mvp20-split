#!/usr/bin/env python3
"""Temperature-resolved Vapor Hazard Ratio (VHR-T) envelope for amphora-sourceability-ehs.

THEORY-AXIS contribution (option B). The module's existing VHR prescreen
(benchmarks/vapor-hazard-ratio-v1) evaluates intrinsic vapour-inhalation hazard
at a single bench temperature (25 C):

    VHR = C_sat(ppm) / OEL(ppm),  C_sat = (P_vap@25C / 760) * 1e6   [Popendorf 2006]

But solvent-borne 2K epoxy-amine marine coatings are frequently applied and cured
inside warm, poorly-ventilated compartments (ballast tanks, cargo holds, void
spaces) and in tropical ambient conditions. Saturated headspace concentration is
governed by vapour pressure, which rises steeply with temperature (Clausius-
Clapeyron / Antoine). A 25 C snapshot therefore UNDER-states the realistic
inhalation hazard, and different solvents amplify at different rates (set by their
Antoine B coefficient ~ enthalpy of vaporisation). A rank order that looks settled
at 25 C can re-order or cross a screening-band boundary at application temperature.

This benchmark extends the VHR into a temperature ENVELOPE (15-40 C, a physically
grounded marine application/confined-space band) using published Antoine
coefficients to propagate C_sat(T), then asks three prescreen-actionable
questions the 25 C VHR cannot answer:

  (1) AMPLIFICATION: how many-fold does each solvent's inhalation hazard grow
      from 15 C to 40 C?  VHR(40)/VHR(15).
  (2) BAND MIGRATION: does any solvent cross a screening-band boundary
      (e.g. MODERATE -> HIGH) inside the envelope, and at what temperature?
  (3) RANK STABILITY: does the ventilation-priority order and worst-actor call
      survive the temperature sweep (Spearman rho of 25 C vs 40 C ranking)?

    Antoine (mmHg / degC form):  log10( P_vap[mmHg] ) = A - B / (C + t[degC])

INTEGRITY GUARDS (load-bearing, fail-closed):
  * Only Antoine sets whose 25 C VP AGREES with the module's pinned PubChem VP to
    within +/-15% (the same independent-source concordance gate already used in
    benchmarks/antoine-vp-crosscheck-v1) are admitted. A discordant set is
    rejected (VP_SOURCE_DISCORDANT), not silently used.
  * Solvents with no confident rights-clean Antoine set are ABSTAINED
    (NO_RIGHTS_CLEAN_ANTOINE_SET); we do NOT fabricate coefficients to fill the
    envelope. They remain covered only by the 25 C PubChem VHR.
  * The saturated-ppm identity C_sat = P_vap/760*1e6 is only valid below boiling;
    a gate asserts P_vap(T) < atmospheric across the whole envelope so no
    solvent is extrapolated through its boiling point.

RIGHTS-CLEAN: OEL denominators = OSHA 29 CFR 1910.1000 Table Z-1 (U.S. federal
regulation, public domain). Antoine coefficients and PubChem VP are published
physical facts, each bound to its substance. ACGIH TLVs (copyrighted) are not used.

EVIDENCE_ONLY. Ranks and temperature-profiles intrinsic vapour-inhalation hazard
to prioritise engineering ventilation for warm confined-space application. Does
NOT establish OSHA compliance, control banding, respirator selection, procurement
approval, or regulatory closure. Deterministic; no learned parameters; no RNG.
Two-replay byte-stability gated. Signed AUDIT_ONLY with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (NOT trust-anchored). Does not promote the module.

Primary sources:
  Popendorf, W. (2006) Industrial Hygiene Control of Airborne Chemical Hazards,
    CRC Press, ISBN 978-0-8247-2719-2, Ch. 3 (Vapor Hazard Ratio).
  Antoine, C. (1888) Comptes Rendus 107:681,778,836 (vapour-pressure equation).
  Clausius, R. (1850); Clapeyron, E. (1834) (temperature dependence of VP).
  Dean, J.A. (ed.) (1999) Lange's Handbook of Chemistry, 15th ed., McGraw-Hill,
    Table 5.28 (Antoine constants). ISBN 978-0-07-016384-3.
  OSHA 29 CFR 1910.1000 Table Z-1 (permissible exposure limits; public domain).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
BENCH = MOD / "benchmarks" / "vhr-temperature-envelope-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

ATM_MMHG = 760.0
T_REF = 25.0
CONCORDANCE_TOL = 0.15  # +/-15% Antoine-vs-PubChem 25 C agreement gate
# Marine confined-space / tropical application-temperature envelope.
T_GRID = [15.0, 20.0, 25.0, 30.0, 35.0, 40.0]

# --- VHR panel: PubChem VP@25C numerator + OSHA Table Z-1 PEL denominator,
#     identical to vapor-hazard-ratio-v1 / antoine-vp-crosscheck-v1.
#     (name, PubChem CID, VP_pubchem mmHg@25C, OSHA PEL 8h TWA ppm, Z-1 name, use)
PANEL = {
    "methanol":        (887,   127.0, 200, "Methyl alcohol",   "thinner / co-solvent"),
    "mek_2_butanone":  (6569,  90.6,  200, "2-Butanone (MEK)", "fast solvent / viscosity cutter"),
    "toluene":         (1140,  28.4,  200, "Toluene",          "aromatic diluent"),
    "ethylbenzene":    (7500,  9.6,   100, "Ethylbenzene",     "aromatic diluent (xylene co-constituent)"),
    "m_xylene":        (7929,  8.3,   100, "Xylenes",          "primary aromatic coating solvent"),
    "n_butanol":       (263,   6.7,   100, "Butyl alcohol",    "slow alcohol / flow / anti-blush"),
}

# --- Rights-clean Antoine coefficients (mmHg/degC form), transcribed from the
#     public Antoine compilation (CRC / Lange's Table 5.28), each validated to
#     the pinned PubChem VP at 25 C in antoine-vp-crosscheck-v1. Validity ranges
#     comfortably span the 15-40 C envelope. (A, B, C, citation, valid_lo, valid_hi)
ANTOINE = {
    "methanol":       (8.08097, 1582.271, 239.726, "CRC/Lange Antoine (methanol)",     15.0, 84.0),
    "mek_2_butanone": (6.97421, 1209.600, 216.000, "CRC/Lange Antoine (2-butanone/MEK)", -10.0, 80.0),
    "toluene":        (6.95464, 1344.800, 219.480, "CRC/Lange Antoine (toluene)",       6.0, 137.0),
    "ethylbenzene":   (6.95719, 1424.255, 213.206, "CRC/Lange Antoine (ethylbenzene)",  0.0, 130.0),
    "m_xylene":       (7.00908, 1462.266, 215.105, "CRC/Lange Antoine (m-xylene)",      0.0, 135.0),
    "n_butanol":      (7.47680, 1362.390, 178.770, "CRC/Lange Antoine (1-butanol)",    15.0, 131.0),
}

# --- Solvents in the module's VHR panel that get NO temperature envelope: no
#     confident rights-clean Antoine set was transcribed, so we abstain rather
#     than fabricate constants to extrapolate through temperature.
NO_ANTOINE = {
    "mibk":            "No confident rights-clean Antoine set for 4-methyl-2-pentanone; temperature envelope abstained.",
    "cyclohexanone":   "No confident rights-clean Antoine set for cyclohexanone; temperature envelope abstained.",
    "n_butyl_acetate": "No confident rights-clean Antoine set for n-butyl acetate; temperature envelope abstained.",
}

# --- Fail-closed probe: a corrupted Antoine set (toluene B inflated +200) whose
#     25 C VP disagrees with PubChem by far more than +/-15%. The concordance
#     gate MUST reject it, proving the guard is load-bearing before any
#     temperature extrapolation is trusted.
DISCORDANT_PROBE = {
    "solvent": "toluene_corrupted_antoine",
    "base_solvent": "toluene",
    "coeff": (6.95464, 1544.800, 219.480),
    "reason_code": "VP_SOURCE_DISCORDANT",
    "explanation": ("Corrupted Antoine set (toluene B inflated +200) yields a 25 C VP that disagrees "
                    "with the pinned PubChem VP by more than +/-15%. Rejected by the concordance gate "
                    "before it can seed a temperature envelope."),
}

BAND_THRESHOLDS = [
    (100.0, "HIGH_INHALATION_HAZARD_ENGINEERING_VENTILATION_REQUIRED"),
    (10.0,  "MODERATE_INHALATION_HAZARD_VENTILATION_RECOMMENDED"),
    (1.0,   "LOW_INHALATION_HAZARD_GENERAL_VENTILATION"),
    (0.0,   "MINIMAL_SATURATED_HEADSPACE_BELOW_OEL"),
]

REFERENCES = [
    "Popendorf, W. (2006) Industrial Hygiene Control of Airborne Chemical Hazards, CRC Press, ISBN 978-0-8247-2719-2, Ch. 3 (Vapor Hazard Ratio metric extended here to a temperature envelope).",
    "Antoine, C. (1888) 'Tensions des vapeurs; nouvelle relation entre les tensions et les temperatures', Comptes Rendus de l'Academie des Sciences 107: 681-684, 778-780, 836-837.",
    "Clausius, R. (1850) Ann. Phys. 155:500; Clapeyron, E. (1834) J. Ecole Polytech. 14:153 (temperature dependence of saturated vapour pressure).",
    "Dean, J.A. (ed.) (1999) Lange's Handbook of Chemistry, 15th ed., McGraw-Hill, Table 5.28 (Antoine vapour-pressure constants). ISBN 978-0-07-016384-3.",
    "OSHA 29 CFR 1910.1000 Table Z-1 (permissible exposure limits, 8-hr TWA; U.S. federal regulation, public domain).",
    "PubChem (https://pubchem.ncbi.nlm.nih.gov) experimental vapour-pressure records at 25 C (independent-source concordance anchor).",
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def pae(t: str, body: bytes) -> bytes:
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


def antoine_vp(A, B, C, t):
    return 10.0 ** (A - B / (C + t))


def band(vhr):
    for thr, label in BAND_THRESHOLDS:
        if vhr >= thr:
            return label
    return BAND_THRESHOLDS[-1][1]


def band_rank(label):
    # ordinal severity for band-migration detection (higher = more hazardous)
    order = {b: len(BAND_THRESHOLDS) - 1 - i for i, (_, b) in enumerate(BAND_THRESHOLDS)}
    return order[label]


def band_crossing_temp(A, B, C, pel, threshold_vhr):
    """Exact temperature at which VHR crosses `threshold_vhr`, solving the
    Antoine relation in closed form. VHR = (10^(A-B/(C+t))/760)*1e6 / pel.
    Set == threshold: 10^(A-B/(C+t)) = threshold*pel*760/1e6 => solve for t."""
    p_target = threshold_vhr * pel * ATM_MMHG / 1e6  # required VP in mmHg
    # A - B/(C+t) = log10(p_target) => C+t = B/(A - log10(p_target))
    import math
    denom = A - math.log10(p_target)
    if denom <= 0:
        return None
    t = B / denom - C
    return round(t, 3)


def spearman_rho(order_a, order_b):
    # order_* : list of solvent names in ranked order (rank 1 = worst).
    ra = {s: i + 1 for i, s in enumerate(order_a)}
    rb = {s: i + 1 for i, s in enumerate(order_b)}
    keys = list(ra.keys())
    n = len(keys)
    d2 = sum((ra[k] - rb[k]) ** 2 for k in keys)
    return round(1.0 - 6.0 * d2 / (n * (n * n - 1)), 6)


def compute():
    admitted = []      # solvent cards that pass the concordance gate
    concordance = []   # per-solvent Antoine-vs-PubChem 25 C agreement record
    boiling_flags = []

    for name, (cid, vp_pc, pel, z1, use) in PANEL.items():
        if name not in ANTOINE:
            continue
        A, B, C, cite, vlo, vhi = ANTOINE[name]
        vp25_antoine = antoine_vp(A, B, C, T_REF)
        rel_err = abs(vp25_antoine - vp_pc) / vp_pc
        concordant = rel_err <= CONCORDANCE_TOL
        concordance.append({
            "solvent": name,
            "vp_pubchem_mmHg_25C": round(vp_pc, 4),
            "vp_antoine_mmHg_25C": round(vp25_antoine, 4),
            "relative_error": round(rel_err, 5),
            "tolerance": CONCORDANCE_TOL,
            "concordant": concordant,
            "reason_code": None if concordant else "VP_SOURCE_DISCORDANT",
        })
        if not concordant:
            continue

        profile = []
        for t in T_GRID:
            vp = antoine_vp(A, B, C, t)
            c_sat = (vp / ATM_MMHG) * 1e6
            vhr = c_sat / pel
            profile.append({
                "temperature_C": t,
                "vapor_pressure_mmHg": round(vp, 4),
                "saturated_vapor_conc_ppm": round(c_sat, 2),
                "vapor_hazard_ratio": round(vhr, 3),
                "screening_band": band(vhr),
                "below_boiling": vp < ATM_MMHG,
            })
        for p in profile:
            if not p["below_boiling"]:
                boiling_flags.append({"solvent": name, "temperature_C": p["temperature_C"]})

        vhr_lo = profile[0]["vapor_hazard_ratio"]     # 15 C
        vhr_hi = profile[-1]["vapor_hazard_ratio"]    # 40 C
        amplification = vhr_hi / vhr_lo

        # monotonic VP increasing in T?
        monotonic = all(profile[i]["vapor_pressure_mmHg"] < profile[i + 1]["vapor_pressure_mmHg"]
                        for i in range(len(profile) - 1))

        # band migration inside envelope
        bands_seen = [p["screening_band"] for p in profile]
        migrates = len(set(bands_seen)) > 1
        crossings = []
        if migrates:
            for thr, label in BAND_THRESHOLDS:
                if thr <= 0:
                    continue
                lo_below = vhr_lo < thr
                hi_above = vhr_hi >= thr
                if lo_below and hi_above:
                    tcross = band_crossing_temp(A, B, C, pel, thr)
                    crossings.append({
                        "crosses_into_band": label,
                        "vhr_threshold": thr,
                        "crossing_temperature_C": tcross,
                        "within_envelope": (tcross is not None and T_GRID[0] <= tcross <= T_GRID[-1]),
                    })

        admitted.append({
            "solvent": name,
            "cas_pubchem_cid": cid,
            "coating_use": use,
            "osha_pel_8h_twa_ppm": pel,
            "osha_pel_table_z1_name": z1,
            "antoine_coeffs": {"A": A, "B": B, "C": C, "citation": cite,
                               "valid_range_C": [vlo, vhi]},
            "vp_source_note": f"PubChem CID {cid} anchors 25 C; Antoine propagates T (rel_err {round(rel_err,5)} <= {CONCORDANCE_TOL})",
            "temperature_profile": profile,
            "vhr_15C": vhr_lo,
            "vhr_25C": next(p["vapor_hazard_ratio"] for p in profile if p["temperature_C"] == 25.0),
            "vhr_40C": vhr_hi,
            "amplification_15to40": round(amplification, 3),
            "vp_monotonic_in_T": monotonic,
            "band_migrates_in_envelope": migrates,
            "band_crossings": crossings,
        })

    # rank by 25 C and by 40 C VHR (worst first); deterministic name tie-break
    order_25 = [c["solvent"] for c in sorted(admitted, key=lambda c: (-c["vhr_25C"], c["solvent"]))]
    order_40 = [c["solvent"] for c in sorted(admitted, key=lambda c: (-c["vhr_40C"], c["solvent"]))]
    rho_25_40 = spearman_rho(order_25, order_40) if len(admitted) >= 2 else None

    # worst-actor at each grid temperature
    worst_by_T = {}
    for i, t in enumerate(T_GRID):
        w = max(admitted, key=lambda c: (c["temperature_profile"][i]["vapor_hazard_ratio"], c["solvent"]))
        worst_by_T[str(t)] = w["solvent"]
    worst_invariant = len(set(worst_by_T.values())) == 1

    # discordant probe evaluation
    A, B, C = DISCORDANT_PROBE["coeff"]
    base = PANEL[DISCORDANT_PROBE["base_solvent"]]
    vp_bad = antoine_vp(A, B, C, T_REF)
    rel_bad = abs(vp_bad - base[1]) / base[1]
    probe_result = dict(DISCORDANT_PROBE)
    probe_result["vp_antoine_mmHg_25C"] = round(vp_bad, 4)
    probe_result["vp_pubchem_mmHg_25C"] = base[1]
    probe_result["relative_error"] = round(rel_bad, 5)
    probe_result["rejected_by_concordance_gate"] = rel_bad > CONCORDANCE_TOL

    migrators = [c["solvent"] for c in admitted if c["band_migrates_in_envelope"]]
    max_amp = max(admitted, key=lambda c: c["amplification_15to40"]) if admitted else None
    min_amp = min(admitted, key=lambda c: c["amplification_15to40"]) if admitted else None

    diag = {
        "method": "vapor_hazard_ratio_temperature_envelope",
        "formula": "VHR(T) = C_sat(T)/OEL ; C_sat(T)=(P_vap(T)/760)*1e6 ; log10 P_vap(T)=A-B/(C+t)",
        "temperature_grid_C": T_GRID,
        "reference_temperature_C": T_REF,
        "concordance_tolerance": CONCORDANCE_TOL,
        "n_panel": len(PANEL),
        "n_admitted": len(admitted),
        "concordance_records": concordance,
        "solvent_envelopes": admitted,
        "no_antoine_abstained": NO_ANTOINE,
        "discordant_probe": probe_result,
        "aggregate": {
            "worst_actor_by_temperature": worst_by_T,
            "worst_actor_temperature_invariant": worst_invariant,
            "spearman_rho_25C_vs_40C_ranking": rho_25_40,
            "rank_order_25C": order_25,
            "rank_order_40C": order_40,
            "band_migrators_in_envelope": migrators,
            "n_band_migrators": len(migrators),
            "max_amplification_solvent": max_amp["solvent"] if max_amp else None,
            "max_amplification_15to40": max_amp["amplification_15to40"] if max_amp else None,
            "min_amplification_solvent": min_amp["solvent"] if min_amp else None,
            "min_amplification_15to40": min_amp["amplification_15to40"] if min_amp else None,
            "boiling_violations": boiling_flags,
            "finding": ("Saturated-headspace inhalation hazard is strongly temperature-dependent: over the "
                        "15-40 C marine confined-space envelope every admitted solvent's VHR amplifies "
                        "several-fold, and slow alcohols that read MODERATE at 25 C can cross into the HIGH "
                        "engineering-ventilation band at application temperature. A single 25 C VHR "
                        "under-states confined-space inhalation hazard."),
        },
    }
    return diag


def sign_receipt(body_obj: dict, ptype: str):
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
    d1 = compute()
    d2 = compute()
    s1, s2 = sha(canon(d1)), sha(canon(d2))
    assert s1 == s2, f"two-replay diagnostic mismatch {s1} != {s2}"
    diag = d1
    diag_sha = s1

    BENCH.mkdir(parents=True, exist_ok=True)
    (BENCH / "diagnostic.canonical.json").write_bytes(canon(diag))
    (BENCH / "run_vhr_temperature_envelope.py").write_bytes(Path(__file__).read_bytes())
    harness_sha = sha(Path(__file__).read_bytes())

    agg = diag["aggregate"]

    gates = []
    def gate(gid, observed, passed, floor, note):
        gates.append({"gate_id": gid, "observed": observed, "passed": bool(passed),
                      "floor": floor, "note": note})

    gate("panel_admitted_at_least_5", diag["n_admitted"],
         diag["n_admitted"] >= 5, 5, "at least 5 rights-clean Antoine sets pass the 25 C concordance gate")
    gate("all_admitted_concordant_15pct", diag["n_admitted"],
         all(c["concordant"] for c in diag["concordance_records"]
             if c["solvent"] in {a["solvent"] for a in diag["solvent_envelopes"]}),
         diag["n_admitted"], "every admitted Antoine set agrees with pinned PubChem VP within +/-15% at 25 C")
    gate("vp_monotonic_increasing_in_T", diag["n_admitted"],
         all(a["vp_monotonic_in_T"] for a in diag["solvent_envelopes"]),
         diag["n_admitted"], "Antoine VP is strictly increasing with temperature for every solvent (Clausius-Clapeyron sanity)")
    gate("no_boiling_within_envelope", len(agg["boiling_violations"]),
         len(agg["boiling_violations"]) == 0, 0,
         "P_vap(T) < 1 atm across 15-40 C for all solvents => saturated-ppm identity valid, no extrapolation through boiling")
    gate("vhr_amplifies_with_temperature", diag["n_admitted"],
         all(a["amplification_15to40"] > 1.0 for a in diag["solvent_envelopes"]),
         diag["n_admitted"], "every solvent's inhalation hazard grows from 15 C to 40 C (VHR(40)>VHR(15))")
    gate("band_migration_detected", agg["n_band_migrators"],
         agg["n_band_migrators"] >= 1, 1,
         "at least one solvent crosses a screening-band boundary inside the envelope (25 C snapshot would miss it)")
    gate("band_crossing_temperature_computed", agg["n_band_migrators"],
         all(any(x["crossing_temperature_C"] is not None for x in a["band_crossings"])
             for a in diag["solvent_envelopes"] if a["band_migrates_in_envelope"]),
         agg["n_band_migrators"], "each migrating solvent has a closed-form Antoine band-crossing temperature")
    gate("rank_stability_quantified", agg["spearman_rho_25C_vs_40C_ranking"],
         agg["spearman_rho_25C_vs_40C_ranking"] is not None, "non-null",
         "Spearman rho of 25 C vs 40 C ventilation-priority ranking is reported")
    gate("worst_actor_temperature_invariant", agg["worst_actor_temperature_invariant"],
         agg["worst_actor_temperature_invariant"] is True, True,
         "the single worst inhalation-hazard actor is the same at every grid temperature (robust top-priority call)")
    gate("no_antoine_solvents_abstain", len(diag["no_antoine_abstained"]),
         len(diag["no_antoine_abstained"]) >= 3, 3,
         "solvents lacking a rights-clean Antoine set are abstained, not fabricated, in the temperature envelope")
    gate("discordant_probe_rejected", diag["discordant_probe"]["rejected_by_concordance_gate"],
         diag["discordant_probe"]["rejected_by_concordance_gate"] is True, True,
         "corrupted Antoine set is rejected by the concordance gate (guard is load-bearing)")
    gate("two_replay_byte_stable", 1.0, s1 == s2, 1.0, "diagnostic canonical SHA identical across two replays")

    n_pass = sum(1 for g in gates if g["passed"])
    n_def = len(gates)

    kpis = {
        "method": diag["method"],
        "formula": diag["formula"],
        "temperature_grid_C": diag["temperature_grid_C"],
        "n_panel": diag["n_panel"],
        "n_admitted": diag["n_admitted"],
        "concordance_records": diag["concordance_records"],
        "solvent_envelopes": diag["solvent_envelopes"],
        "no_antoine_abstained": diag["no_antoine_abstained"],
        "discordant_probe": diag["discordant_probe"],
        "aggregate": diag["aggregate"],
        "pel_denominator_source": "OSHA 29 CFR 1910.1000 Table Z-1 (8-hour TWA permissible exposure limit; U.S. federal regulation, public domain)",
        "theory_references": REFERENCES,
        "relationship_to_prior_receipts": (
            "Extends benchmarks/vapor-hazard-ratio-v1 (25 C VHR, Popendorf 2006) from a single "
            "temperature to a 15-40 C application envelope, reusing the Antoine coefficients validated "
            "in benchmarks/antoine-vp-crosscheck-v1 (each within +/-15% of pinned PubChem VP at 25 C). "
            "New physical finding: inhalation hazard is strongly temperature-dependent and 25 C VHR "
            "under-states confined-space marine application hazard."),
        "receipt_meta": {
            "sci_pipeline_module": "amphora-sourceability-ehs/benchmarks/vhr-temperature-envelope-v1/run_vhr_temperature_envelope.py",
            "sci_pipeline_seed": 0,
            "harness_sha256": harness_sha,
            "diagnostic_canonical_sha256": diag_sha,
            "data_extraction_method": ("Antoine coefficients hand-transcribed from public CRC/Lange compilation "
                                       "(each bound to its substance and validated to PubChem VP at 25 C); OEL from "
                                       "OSHA Table Z-1. No LLM-authored constants, no learned parameters, no RNG."),
        },
        "authority_ceiling_note": ("EVIDENCE_ONLY quantitative temperature-resolved inhalation-hazard PRESCREEN. "
                                   "Profiles intrinsic vapour-inhalation hazard across the marine confined-space "
                                   "application-temperature envelope to prioritise engineering ventilation. Does NOT "
                                   "establish OSHA compliance, control banding, respirator selection, procurement "
                                   "approval, or regulatory closure. Complements the module's 25 C VHR and qualitative "
                                   "GHS/CLP prescreens."),
    }
    receipt_id = "vhr-temperature-envelope-inhalation-prescreen-" + sha(canon(kpis))
    body_obj = {
        "kpis": kpis,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "human_review_performed": False,
        "module_id": "amphora-sourceability-ehs",
        "receipt_id": receipt_id,
        "reviewer_key_id": PUB["key_id"],
        "reviewer_public_key_hex": PUB["public_key_hex"],
        "schema": "amphora.vhr-temperature-envelope-inhalation-prescreen.v1",
    }
    ptype = "application/vnd.amphora.vhr-temperature-envelope-inhalation-prescreen.v1+json"
    signed, body_sha = sign_receipt(body_obj, ptype)
    receipt_path = MOD / "reference/mvp20/data/vhr_temperature_envelope_inhalation_prescreen_receipt.v1.json"
    receipt_path.write_bytes(canon(signed))

    kpi_obj = {
        "kpi_id": "vhr-temperature-envelope-inhalation-prescreen-kpi.v1",
        "schema": "amphora.phase0-kpi.v1",
        "module_id": "amphora-sourceability-ehs",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "EVIDENCE_ONLY",
        "solver_use_ceiling": "DISABLED",
        "promotes_authority": False,
        "capability": "temperature-resolved quantitative vapour-inhalation-hazard prescreen (VHR-T envelope)",
        "theory": "Popendorf 2006 VHR extended over T via Antoine 1888 / Clausius-Clapeyron; OSHA Table Z-1 PEL denominator; PubChem-anchored VP",
        "population": "6-solvent rights-clean-Antoine subset of the module's marine 2K epoxy-amine solvent panel, over 15-40 C",
        "split_methodology": "N/A (deterministic physical/regulatory computation; no train/test, no fitted parameters)",
        "n_deterministic_gates_defined": n_def,
        "n_deterministic_gates_passed": n_pass,
        "phase0_deterministic_gates_passed": gates,
        "observed_kpi_summary": {
            "n_admitted": diag["n_admitted"],
            "worst_actor_temperature_invariant": agg["worst_actor_temperature_invariant"],
            "spearman_rho_25C_vs_40C_ranking": agg["spearman_rho_25C_vs_40C_ranking"],
            "n_band_migrators": agg["n_band_migrators"],
            "band_migrators": agg["band_migrators_in_envelope"],
            "max_amplification_solvent": agg["max_amplification_solvent"],
            "max_amplification_15to40": agg["max_amplification_15to40"],
            "min_amplification_15to40": agg["min_amplification_15to40"],
        },
        "scientific_receipt_id": receipt_id,
        "scientific_receipt_path": "amphora-sourceability-ehs/reference/mvp20/data/vhr_temperature_envelope_inhalation_prescreen_receipt.v1.json",
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
    kpi_path = MOD / "evidence/phase0/kpis/vhr-temperature-envelope-inhalation-prescreen-kpi.v1.json"
    kpi_path.write_bytes(canon(kpi_signed))

    print("=== VHR temperature envelope (15-40 C) ===")
    print(f"gates: {n_pass}/{n_def} passed")
    for g in gates:
        print(f"  [{'PASS' if g['passed'] else 'FAIL'}] {g['gate_id']}: {g['observed']}")
    print("--- amplification VHR(40)/VHR(15) & band migration ---")
    for a in diag["solvent_envelopes"]:
        cr = ""
        if a["band_crossings"]:
            for x in a["band_crossings"]:
                cr += f"  ->{x['crosses_into_band'][:8]}@{x['crossing_temperature_C']}C"
        print(f"  {a['solvent']:16s} VHR15={a['vhr_15C']:8.1f} VHR25={a['vhr_25C']:8.1f} "
              f"VHR40={a['vhr_40C']:8.1f}  x{a['amplification_15to40']:.2f}{cr}")
    print(f"worst_actor_invariant={agg['worst_actor_temperature_invariant']} "
          f"rho(25vs40)={agg['spearman_rho_25C_vs_40C_ranking']} "
          f"migrators={agg['band_migrators_in_envelope']}")
    print(f"discordant_probe_rejected={diag['discordant_probe']['rejected_by_concordance_gate']} "
          f"(rel_err={diag['discordant_probe']['relative_error']})")
    print("RECEIPT", receipt_path)
    print("RECEIPT_BODY_SHA256", body_sha)
    print("RECEIPT_ID", receipt_id)
    print("KPI", kpi_path)
    print("KPI_BODY_SHA256", kpi_body_sha)
    print("N_PASS", n_pass, "N_DEF", n_def)


if __name__ == "__main__":
    main()
