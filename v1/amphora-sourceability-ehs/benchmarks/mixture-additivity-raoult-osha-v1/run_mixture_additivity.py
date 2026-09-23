#!/usr/bin/env python3
"""Blend-resolved inhalation-hazard additivity for amphora-sourceability-ehs.

THEORY-AXIS contribution (option B). Every prior receipt in this module scores a
SINGLE substance:

  * benchmarks/vapor-hazard-ratio-v1     VHR = C_sat(25C)/OEL          [Popendorf 2006]
  * benchmarks/antoine-vp-crosscheck-v1  Antoine-vs-PubChem VP concordance
  * benchmarks/vhr-temperature-envelope-v1  VHR(T) over 15-40 C        [Antoine 1888]

But a marine 2K epoxy-amine coating is never thinned with one solvent. It is
thinned with a BLEND, and the blend is specified to the formulator/applicator by
MASS fraction (or by volume), while the physics that sets headspace composition
is driven by MOLE fraction:

    Raoult (1887)   p_i = x_i * gamma_i * P_i^0(T)      (gamma_i = 1 ideal)
    Dalton (1801)   P_total = sum_i p_i ; ppm_i = p_i/P_atm * 1e6
    OSHA 1910.1000(d)(2)(i)   E_m = sum_i C_i / L_i , hazardous when E_m > 1

Composing the three gives the saturated-headspace Mixture Hazard Index

    MHI_sat(blend, T) = sum_i x_i * gamma_i * VHR_i(T)

i.e. the module's existing pure-component VHR is exactly the gamma=1, x_i=1
special case, and the blend index is a MOLE-fraction-weighted sum of it. MHI is
directly actionable: it is the fold-dilution of saturated headspace required to
reach the OSHA additive mixture limit E_m = 1.

Three prescreen questions no single-substance receipt can answer:

  (1) EXACTNESS. Does the composed Raoult/Dalton/OSHA chain reduce EXACTLY to
      sum_i x_i VHR_i? (identity gate; must be exact to f64 round-off, not
      "approximately")
  (2) H0_MASS_SURROGATE: "weighting the pure-component VHRs by the mass
      fractions printed on the thinner spec is an adequate surrogate for the
      mole-fraction-correct blend index." Molar masses across this panel span
      32.04 (methanol) to 106.17 (xylene) g/mol -- a 3.3x spread -- so mass
      weighting is NOT mole weighting, and the error has a sign.
  (3) H0_PURE_WORST_ACTOR: "the constituent with the highest pure-component VHR
      is the dominant contributor to the blend's inhalation hazard." A trace
      fast solvent can be the pure-component worst actor yet contribute little;
      conversely a bulk solvent can dominate. Where the answer flips we solve
      the DOMINANCE-CROSSOVER mass fraction in closed form -- the trace-solvent
      wt% above which the minor component takes over the blend hazard -- and
      report how it moves across the 15-40 C application envelope.

Closed-form crossover for a binary bulk B / trace T pair:
    x_T VHR_T = x_B VHR_B  with x_i ~ w_i/M_i
    =>  w_T* = r/(1+r),  r = (M_T * VHR_B) / (M_B * VHR_T)

INTEGRITY GUARDS (load-bearing, fail-closed):
  * Only the six solvents whose Antoine sets already passed the +/-15%
    PubChem concordance gate in antoine-vp-crosscheck-v1 are admitted. A blend
    naming any other solvent is ABSTAINED (BLEND_CONTAINS_NON_ADMITTED_SOLVENT),
    never silently dropped or renormalised.
  * Blend mass fractions must sum to 1 within 1e-9 or the blend is REJECTED
    (BLEND_FRACTIONS_NOT_NORMALISED). A deliberately mis-normalised probe blend
    proves the guard fires.
  * Molar masses are RE-DERIVED from SMILES with RDKit, not transcribed, and
    each is cross-checked against its declared molecular formula. A wrong
    formula fails closed.
  * IDEALITY IS DECLARED, NOT ASSUMED AWAY. Raoult with gamma=1 is exact only
    for ideal solutions; alcohol + aromatic blends show positive deviation
    (gamma_alcohol > 1), so the ideal MHI is a LOWER bound for those blends. We
    do NOT invent activity coefficients. Instead we invert the question and
    report gamma_crit -- the activity coefficient each non-dominant constituent
    would need in order to overtake the dominant contributor. gamma_crit is a
    pure ratio of already-pinned quantities; no new constant is introduced, and
    it states exactly how much non-ideality the dominance call can absorb.

BLEND COMPOSITIONS are illustrative rights-clean scenarios constructed to span
the marine-thinner design space (aromatic-rich, fast/ketone, anti-blush alcohol,
wash-solvent carryover). They are NOT vendor formulations and encode no
supplier-proprietary information.

RIGHTS-CLEAN: OEL denominators = OSHA 29 CFR 1910.1000 Table Z-1 and the mixture
rule at 1910.1000(d)(2)(i) (U.S. federal regulation, public domain). Antoine
coefficients and PubChem VP are published physical facts. Molar masses derived
from structure via RDKit. ACGIH TLVs (copyrighted) are not used.

EVIDENCE_ONLY. Ranks and apportions intrinsic saturated-headspace inhalation
hazard for solvent BLENDS to prioritise engineering ventilation and to flag when
a trace constituent governs. Does NOT establish OSHA compliance, control
banding, respirator selection, procurement approval, or regulatory closure.
Deterministic; no learned parameters; no RNG. Two-replay byte-stability gated.
Signed AUDIT_ONLY with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (NOT
trust-anchored). Does not promote the module.

Primary sources:
  Raoult, F.-M. (1887) 'Loi generale des tensions de vapeur des dissolvants',
    Comptes Rendus de l'Academie des Sciences 104: 1430-1433.
  Dalton, J. (1802) 'Experimental Essays on the Constitution of Mixed Gases',
    Memoirs of the Literary and Philosophical Society of Manchester 5: 535-602.
  OSHA 29 CFR 1910.1000(d)(2)(i) (additive mixture rule) and Table Z-1
    (8-hr TWA permissible exposure limits); U.S. federal regulation, public domain.
  Popendorf, W. (2006) Industrial Hygiene Control of Airborne Chemical Hazards,
    CRC Press, ISBN 978-0-8247-2719-2, Ch. 3 (Vapor Hazard Ratio).
  Antoine, C. (1888) Comptes Rendus 107: 681, 778, 836.
  Dean, J.A. (ed.) (1999) Lange's Handbook of Chemistry, 15th ed., McGraw-Hill,
    Table 5.28 (Antoine constants). ISBN 978-0-07-016384-3.
  IUPAC (2021) Standard Atomic Weights, Pure Appl. Chem. 93(12):1571 (via RDKit
    periodic table, used to re-derive molar masses from structure).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
BENCH = MOD / "benchmarks" / "mixture-additivity-raoult-osha-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

ATM_MMHG = 760.0
T_REF = 25.0
T_GRID = [15.0, 25.0, 40.0]          # envelope endpoints + bench reference
FRACTION_TOL = 1e-9
EXACTNESS_TOL = 1e-9

# --- Admitted panel: identical solvents / PELs / Antoine sets to
#     benchmarks/vhr-temperature-envelope-v1 (each already within +/-15% of the
#     pinned PubChem VP at 25 C in benchmarks/antoine-vp-crosscheck-v1).
#     (SMILES, declared formula, PubChem CID, OSHA Z-1 PEL ppm, Z-1 name, A, B, C, use)
PANEL = {
    "methanol":       ("CO",            "CH4O",  887,  200, "Methyl alcohol",
                       8.08097, 1582.271, 239.726, "wash / equipment-flush solvent"),
    "mek_2_butanone": ("CCC(C)=O",      "C4H8O", 6569, 200, "2-Butanone (MEK)",
                       6.97421, 1209.600, 216.000, "fast solvent / viscosity cutter"),
    "toluene":        ("Cc1ccccc1",     "C7H8",  1140, 200, "Toluene",
                       6.95464, 1344.800, 219.480, "aromatic diluent"),
    "ethylbenzene":   ("CCc1ccccc1",    "C8H10", 7500, 100, "Ethylbenzene",
                       6.95719, 1424.255, 213.206, "aromatic diluent (xylene co-constituent)"),
    "m_xylene":       ("Cc1cccc(C)c1",  "C8H10", 7929, 100, "Xylenes",
                       7.00908, 1462.266, 215.105, "primary aromatic coating solvent"),
    "n_butanol":      ("CCCCO",         "C4H10O", 263, 100, "Butyl alcohol",
                       7.47680, 1362.390, 178.770, "slow alcohol / flow / anti-blush"),
}

# --- Illustrative marine-thinner composition scenarios, BY MASS FRACTION
#     (the way a thinner spec is written). Not vendor formulations.
BLENDS = {
    "aromatic_thinner_xylene_butanol": {
        "note": "conventional aromatic epoxy thinner with anti-blush alcohol",
        "mass_fractions": {"m_xylene": 0.80, "n_butanol": 0.20},
    },
    "fast_thinner_mek_aromatic": {
        "note": "ketone-boosted fast thinner for cold-weather application",
        "mass_fractions": {"mek_2_butanone": 0.40, "m_xylene": 0.35, "toluene": 0.25},
    },
    "aromatic_100_surrogate": {
        "note": "aromatic-hydrocarbon-blend surrogate (xylene isomer + ethylbenzene + toluene)",
        "mass_fractions": {"m_xylene": 0.60, "ethylbenzene": 0.25, "toluene": 0.15},
    },
    "anti_blush_alcohol_rich": {
        "note": "alcohol-rich package for humid tropical amine cure (blush control)",
        "mass_fractions": {"n_butanol": 0.50, "m_xylene": 0.35, "methanol": 0.15},
    },
    "wash_carryover_methanol_1pct": {
        "note": "aromatic thinner with 1 wt% residual methanol equipment-wash carryover",
        "mass_fractions": {"m_xylene": 0.97, "n_butanol": 0.02, "methanol": 0.01},
    },
    "wash_carryover_methanol_3pct": {
        "note": "aromatic thinner with 3 wt% residual methanol equipment-wash carryover",
        "mass_fractions": {"m_xylene": 0.95, "n_butanol": 0.02, "methanol": 0.03},
    },
    "wash_carryover_methanol_6pct": {
        "note": "aromatic thinner with 6 wt% residual methanol equipment-wash carryover",
        "mass_fractions": {"m_xylene": 0.92, "n_butanol": 0.02, "methanol": 0.06},
    },
}

# --- Carryover series used to EMPIRICALLY BRACKET the closed-form crossover.
#     Pairwise dominance between two constituents of a blend is independent of
#     the other constituents: contribution_i/contribution_j = (w_i/M_i)VHR_i /
#     (w_j/M_j)VHR_j, and the common mole-normalisation cancels. So with the
#     third component (n_butanol) held at a fixed 2 wt%, methanol overtakes
#     m_xylene at exactly  w* = (1 - w_fixed) / (1 + rho),
#     rho = (VHR_methanol/M_methanol) / (VHR_m_xylene/M_m_xylene).
CARRYOVER_SERIES = {
    "trace_solvent": "methanol",
    "bulk_solvent": "m_xylene",
    "fixed_other": {"n_butanol": 0.02},
    "blend_ids": ["wash_carryover_methanol_1pct",
                  "wash_carryover_methanol_3pct",
                  "wash_carryover_methanol_6pct"],
}

# --- Fail-closed probes.
PROBE_UNNORMALISED = {
    "blend_id": "probe_fractions_sum_0p90",
    "mass_fractions": {"m_xylene": 0.70, "n_butanol": 0.20},
    "reason_code": "BLEND_FRACTIONS_NOT_NORMALISED",
    "explanation": ("Mass fractions sum to 0.90, not 1.0. A silent renormalisation would "
                    "invent 10 wt% of unspecified material; the guard rejects the blend instead."),
}
PROBE_NON_ADMITTED = {
    "blend_id": "probe_contains_mibk",
    "mass_fractions": {"m_xylene": 0.60, "mibk": 0.40},
    "reason_code": "BLEND_CONTAINS_NON_ADMITTED_SOLVENT",
    "explanation": ("MIBK (4-methyl-2-pentanone) has no rights-clean Antoine set admitted by the "
                    "+/-15% PubChem concordance gate, so its partial pressure cannot be propagated. "
                    "The whole blend is abstained rather than scored on a 60% subset."),
}
PROBE_BAD_FORMULA = {
    "solvent": "m_xylene",
    "smiles": "Cc1cccc(C)c1",
    "declared_formula_corrupted": "C9H12",
    "reason_code": "MOLAR_MASS_FORMULA_MISMATCH",
    "explanation": ("A corrupted declared formula (C9H12 for m-xylene, true C8H10) must be caught by "
                    "the RDKit structure-vs-formula cross-check before its molar mass can enter a "
                    "mole-fraction conversion."),
}

REFERENCES = [
    "Raoult, F.-M. (1887) 'Loi generale des tensions de vapeur des dissolvants', Comptes Rendus de l'Academie des Sciences 104: 1430-1433 (partial pressure proportional to mole fraction).",
    "Dalton, J. (1802) 'Experimental Essays on the Constitution of Mixed Gases', Memoirs of the Literary and Philosophical Society of Manchester 5: 535-602 (additivity of partial pressures).",
    "OSHA 29 CFR 1910.1000(d)(2)(i) (additive mixture exposure rule E_m = sum C_i/L_i) and Table Z-1 (8-hr TWA permissible exposure limits); U.S. federal regulation, public domain.",
    "Popendorf, W. (2006) Industrial Hygiene Control of Airborne Chemical Hazards, CRC Press, ISBN 978-0-8247-2719-2, Ch. 3 (Vapor Hazard Ratio; the single-substance gamma=1, x=1 special case of the index composed here).",
    "Antoine, C. (1888) 'Tensions des vapeurs; nouvelle relation entre les tensions et les temperatures', Comptes Rendus de l'Academie des Sciences 107: 681-684, 778-780, 836-837.",
    "Dean, J.A. (ed.) (1999) Lange's Handbook of Chemistry, 15th ed., McGraw-Hill, Table 5.28 (Antoine vapour-pressure constants). ISBN 978-0-07-016384-3.",
    "IUPAC (2021) 'Standard Atomic Weights of the Elements 2021', Pure and Applied Chemistry 93(12): 1571-1582 (atomic weights underlying the RDKit-derived molar masses).",
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def pae(t: str, body: bytes) -> bytes:
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


def antoine_vp(A, B, C, t):
    return 10.0 ** (A - B / (C + t))


def molar_mass(smiles, declared_formula):
    """Re-derive molar mass from structure; cross-check declared formula."""
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return None, None, False
    formula = rdMolDescriptors.CalcMolFormula(m)
    return Descriptors.MolWt(m), formula, formula == declared_formula


def vhr_pure(name, t):
    _, _, _, pel, _, A, B, C, _ = PANEL[name]
    vp = antoine_vp(A, B, C, t)
    return (vp / ATM_MMHG) * 1e6 / pel, vp


def compute():
    # ---- (0) molar masses re-derived from structure -------------------------
    mw = {}
    mw_records = []
    for name, (smi, formula, cid, pel, z1, A, B, C, use) in PANEL.items():
        m, got, ok = molar_mass(smi, formula)
        mw[name] = m
        mw_records.append({
            "solvent": name,
            "smiles": smi,
            "pubchem_cid": cid,
            "declared_formula": formula,
            "rdkit_formula": got,
            "formula_match": ok,
            "molar_mass_g_per_mol": round(m, 5) if m is not None else None,
            "source": "re-derived from SMILES via RDKit periodic table (IUPAC 2021 standard atomic weights)",
        })

    # corrupted-formula probe
    _, got_bad, ok_bad = molar_mass(PROBE_BAD_FORMULA["smiles"],
                                    PROBE_BAD_FORMULA["declared_formula_corrupted"])
    formula_probe = dict(PROBE_BAD_FORMULA)
    formula_probe["rdkit_formula"] = got_bad
    formula_probe["rejected_by_formula_gate"] = not ok_bad

    # ---- (1) pure-component VHR(T) table -----------------------------------
    pure = {}
    for name in PANEL:
        pure[name] = {}
        for t in T_GRID:
            v, vp = vhr_pure(name, t)
            pure[name][str(t)] = {"vapor_pressure_mmHg": round(vp, 5),
                                  "vhr_pure": round(v, 4)}

    # ---- (2) blend evaluation ----------------------------------------------
    blends_out = []
    exactness_errs = []
    for bid, spec in BLENDS.items():
        w = spec["mass_fractions"]
        wsum = sum(w.values())
        if abs(wsum - 1.0) > FRACTION_TOL:
            blends_out.append({"blend_id": bid, "admitted": False,
                               "reason_code": "BLEND_FRACTIONS_NOT_NORMALISED",
                               "mass_fraction_sum": wsum})
            continue
        if any(k not in PANEL for k in w):
            blends_out.append({"blend_id": bid, "admitted": False,
                               "reason_code": "BLEND_CONTAINS_NON_ADMITTED_SOLVENT"})
            continue

        # mass -> mole fraction
        moles = {k: w[k] / mw[k] for k in w}
        ntot = sum(moles.values())
        x = {k: moles[k] / ntot for k in w}

        per_T = {}
        for t in T_GRID:
            # (a) direct Raoult + Dalton + OSHA chain
            partials = {k: x[k] * antoine_vp(*PANEL[k][5:8], t) for k in w}
            ppm = {k: partials[k] / ATM_MMHG * 1e6 for k in w}
            contrib_direct = {k: ppm[k] / PANEL[k][3] for k in w}
            mhi_direct = sum(contrib_direct.values())

            # (b) reduced identity sum_i x_i * VHR_i
            contrib_reduced = {k: x[k] * vhr_pure(k, t)[0] for k in w}
            mhi_reduced = sum(contrib_reduced.values())
            err = abs(mhi_direct - mhi_reduced)
            exactness_errs.append(err)

            # (c) naive mass-fraction surrogate
            mhi_mass = sum(w[k] * vhr_pure(k, t)[0] for k in w)
            rel_err_mass = (mhi_mass - mhi_reduced) / mhi_reduced

            # dominance
            dom = max(w, key=lambda k: (contrib_reduced[k], k))
            pure_worst = max(w, key=lambda k: (vhr_pure(k, t)[0], k))
            dom_mass = max(w, key=lambda k: (w[k] * vhr_pure(k, t)[0], k))

            # gamma_crit: activity coefficient each non-dominant constituent
            # would need to overtake the dominant contributor (others ideal)
            gcrit = {k: round(contrib_reduced[dom] / contrib_reduced[k], 4)
                     for k in w if k != dom}

            shares_exact = {k: contrib_reduced[k] / mhi_reduced for k in w}
            shares = {k: round(v, 6) for k, v in shares_exact.items()}
            per_T[str(t)] = {
                "partial_pressures_mmHg": {k: round(v, 6) for k, v in partials.items()},
                "headspace_ppm": {k: round(v, 3) for k, v in ppm.items()},
                "contribution_direct": {k: round(v, 6) for k, v in contrib_direct.items()},
                "contribution_reduced_xVHR": {k: round(v, 6) for k, v in contrib_reduced.items()},
                "identity_abs_error": err,
                "mhi_mole_weighted": round(mhi_reduced, 6),
                "mhi_mass_weighted_naive": round(mhi_mass, 6),
                "mass_surrogate_relative_error": round(rel_err_mass, 6),
                "required_dilution_fold_to_Em_1": round(mhi_reduced, 3),
                "contribution_shares": shares,
                "contribution_share_closure_error": abs(sum(shares_exact.values()) - 1.0),
                "dominant_contributor": dom,
                "dominant_contributor_share": shares[dom],
                "pure_component_worst_actor": pure_worst,
                "pure_worst_actor_is_dominant": dom == pure_worst,
                "mass_weighted_dominant_contributor": dom_mass,
                "mass_surrogate_preserves_dominant": dom_mass == dom,
                "gamma_crit_to_overtake_dominant": gcrit,
                "min_gamma_crit": min(gcrit.values()) if gcrit else None,
            }

        doms = [per_T[str(t)]["dominant_contributor"] for t in T_GRID]
        blends_out.append({
            "blend_id": bid,
            "admitted": True,
            "note": spec["note"],
            "mass_fractions": w,
            "molar_masses_g_per_mol": {k: round(mw[k], 5) for k in w},
            "mole_fractions": {k: round(x[k], 6) for k in w},
            "mole_fraction_sum_closure_error": abs(sum(x.values()) - 1.0),
            "max_abs_mass_minus_mole_fraction": round(max(abs(w[k] - x[k]) for k in w), 6),
            "per_temperature": per_T,
            "dominant_contributor_by_T": {str(t): d for t, d in zip(T_GRID, doms)},
            "dominant_contributor_temperature_invariant": len(set(doms)) == 1,
        })

    admitted = [b for b in blends_out if b["admitted"]]

    # ---- (3) fail-closed blend probes ---------------------------------------
    p1 = dict(PROBE_UNNORMALISED)
    s1_sum = sum(p1["mass_fractions"].values())
    p1["mass_fraction_sum"] = s1_sum
    p1["rejected_by_normalisation_gate"] = abs(s1_sum - 1.0) > FRACTION_TOL
    p2 = dict(PROBE_NON_ADMITTED)
    p2["rejected_by_admission_gate"] = any(k not in PANEL for k in p2["mass_fractions"])

    # ---- (4) binary dominance-crossover mass fractions -----------------------
    # For a bulk solvent B and a trace solvent T, the mass fraction of T above
    # which T becomes the dominant contributor:  w* = r/(1+r),
    # r = (M_T * VHR_B) / (M_B * VHR_T).
    crossovers = []
    for bulk in ("m_xylene", "toluene"):
        for trace in ("methanol", "mek_2_butanone", "n_butanol", "ethylbenzene"):
            if trace == bulk:
                continue
            row = {"bulk_solvent": bulk, "trace_solvent": trace}
            for t in T_GRID:
                vb = vhr_pure(bulk, t)[0]
                vt = vhr_pure(trace, t)[0]
                r = (mw[trace] * vb) / (mw[bulk] * vt)
                wstar = r / (1.0 + r)
                row[f"crossover_mass_fraction_{int(t)}C"] = round(wstar, 6)
            lo = row[f"crossover_mass_fraction_{int(T_GRID[0])}C"]
            hi = row[f"crossover_mass_fraction_{int(T_GRID[-1])}C"]
            row["crossover_shift_15_to_40C"] = round(hi - lo, 6)
            row["trace_dominates_below_5wt_pct"] = min(lo, hi) < 0.05
            crossovers.append(row)
    crossovers.sort(key=lambda r: (r["bulk_solvent"], r["trace_solvent"]))

    # ---- (4b) empirical bracketing of the closed-form crossover -------------
    trace = CARRYOVER_SERIES["trace_solvent"]
    bulk = CARRYOVER_SERIES["bulk_solvent"]
    w_fixed = sum(CARRYOVER_SERIES["fixed_other"].values())
    series_rows = []
    for t in T_GRID:
        rho = (vhr_pure(trace, t)[0] / mw[trace]) / (vhr_pure(bulk, t)[0] / mw[bulk])
        w_star = (1.0 - w_fixed) / (1.0 + rho)
        obs = []
        for bid in CARRYOVER_SERIES["blend_ids"]:
            b = next(z for z in admitted if z["blend_id"] == bid)
            p = b["per_temperature"][str(t)]
            trace_dominates_bulk = (p["contribution_reduced_xVHR"][trace]
                                    > p["contribution_reduced_xVHR"][bulk])
            obs.append({"blend_id": bid,
                        "trace_mass_fraction": b["mass_fractions"][trace],
                        "trace_outranks_bulk": trace_dominates_bulk})
        below = [o["trace_mass_fraction"] for o in obs if not o["trace_outranks_bulk"]]
        above = [o["trace_mass_fraction"] for o in obs if o["trace_outranks_bulk"]]
        bracket_lo = max(below) if below else None
        bracket_hi = min(above) if above else None
        bracketed = (bracket_lo is not None and bracket_hi is not None
                     and bracket_lo < w_star < bracket_hi)
        series_rows.append({
            "temperature_C": t,
            "rho_trace_over_bulk": round(rho, 6),
            "predicted_crossover_mass_fraction": round(w_star, 6),
            "observed": obs,
            "observed_bracket_low": bracket_lo,
            "observed_bracket_high": bracket_hi,
            "prediction_inside_observed_bracket": bracketed,
        })
    crossover_validation = {
        "trace_solvent": trace,
        "bulk_solvent": bulk,
        "fixed_other_mass_fraction": w_fixed,
        "closed_form": "w* = (1 - w_fixed)/(1 + rho); rho = (VHR_trace/M_trace)/(VHR_bulk/M_bulk)",
        "rationale": ("Pairwise dominance between two constituents is invariant to the rest of the blend "
                      "because the mole-fraction normalisation cancels in the contribution ratio, so the "
                      "closed form is exact for this ternary series, not an approximation."),
        "per_temperature": series_rows,
        "bracketed_at_all_temperatures": all(r["prediction_inside_observed_bracket"] for r in series_rows),
    }

    # ---- (5) aggregate hypotheses -------------------------------------------
    n_pure_worst_holds = sum(
        1 for b in admitted if b["per_temperature"][str(T_REF)]["pure_worst_actor_is_dominant"])
    n_mass_pres_dom = sum(
        1 for b in admitted if b["per_temperature"][str(T_REF)]["mass_surrogate_preserves_dominant"])
    mass_errs = [abs(b["per_temperature"][str(t)]["mass_surrogate_relative_error"])
                 for b in admitted for t in T_GRID]
    max_mass_err = max(mass_errs) if mass_errs else None
    signed_errs = [b["per_temperature"][str(T_REF)]["mass_surrogate_relative_error"]
                   for b in admitted]
    worst_mass_blend = max(
        admitted, key=lambda b: abs(b["per_temperature"][str(T_REF)]["mass_surrogate_relative_error"]))
    flips = [b["blend_id"] for b in admitted
             if not b["per_temperature"][str(T_REF)]["pure_worst_actor_is_dominant"]]
    min_gcrit_overall = min(
        (b["per_temperature"][str(T_REF)]["min_gamma_crit"] for b in admitted
         if b["per_temperature"][str(T_REF)]["min_gamma_crit"] is not None), default=None)

    h0_mass = {
        "hypothesis": "H0_MASS_SURROGATE: mass-fraction weighting of pure-component VHRs is an adequate surrogate for the mole-fraction-correct Raoult blend index.",
        "adequacy_criterion_relative_error": 0.05,
        "max_abs_relative_error_over_blends_and_T": round(max_mass_err, 6),
        "worst_blend": worst_mass_blend["blend_id"],
        "sign_of_error_all_negative": all(e < 0 for e in signed_errs),
        "sign_of_error_all_positive": all(e > 0 for e in signed_errs),
        "verdict": "REFUTED" if max_mass_err > 0.05 else "NOT_REFUTED",
        "interpretation": None,   # filled below
    }
    if h0_mass["verdict"] == "REFUTED":
        direction = ("UNDER-states" if all(e < 0 for e in signed_errs)
                     else "OVER-states" if all(e > 0 for e in signed_errs)
                     else "mis-states, with a blend-dependent SIGN,")
        h0_mass["interpretation"] = (
            f"Refuted. Reading a thinner spec's mass fractions as if they were mole fractions "
            f"{direction} the saturated-headspace mixture hazard index by up to "
            f"{round(100*max_mass_err, 2)}% across the 15-40 C envelope. Mechanism: the panel's molar "
            f"masses span 32.04-106.17 g/mol (3.31x), so on conversion to mole fractions the LIGHTER "
            f"constituents are up-weighted and the heavier ones down-weighted. The sign of the resulting "
            f"error therefore depends on whether a blend's light constituent is more hazardous than its "
            f"heavy one: in methanol- and MEK-bearing blends the light constituent carries the higher "
            f"VHR and mass weighting UNDER-states the index (worst case "
            f"{round(100 * min(signed_errs), 2)}%), whereas in the xylene/n-butanol thinner the lighter "
            f"alcohol is the LESS hazardous constituent and mass weighting OVER-states it "
            f"({round(100 * max(signed_errs), 2)}%). A single directional correction factor is therefore "
            f"not available; the mole-fraction conversion has to be done.")
    else:
        h0_mass["interpretation"] = (
            f"Not refuted at the 5% adequacy criterion; max relative error "
            f"{round(100 * max_mass_err, 2)}% over all blends and temperatures.")

    h0_worst = {
        "hypothesis": "H0_PURE_WORST_ACTOR: the constituent with the highest pure-component VHR is the dominant contributor to the blend's inhalation hazard.",
        "n_blends": len(admitted),
        "n_holds_at_25C": n_pure_worst_holds,
        "blends_where_violated": flips,
        "verdict": "REFUTED" if flips else "NOT_REFUTED",
        "interpretation": (
            "Refuted on at least one realistic blend: the pure-component worst actor is NOT always the "
            "dominant blend contributor, because contribution scales with mole fraction. A trace "
            "high-volatility solvent can be the single worst substance on the shelf and still be a minor "
            "contributor below its dominance-crossover mass fraction -- and can take over above it. "
            "Single-substance VHR prescreening therefore mis-assigns the ventilation-priority target for "
            "blends near the crossover." if flips else
            "Not refuted on this blend set: in every scenario the pure-component worst actor also "
            "dominated the blend index, so single-substance prescreening happened to identify the right "
            "ventilation target -- but only because no constituent sat near its dominance crossover."),
    }

    diag = {
        "method": "raoult_dalton_osha_mixture_additivity_inhalation_prescreen",
        "formula": ("MHI_sat(blend,T) = sum_i x_i*gamma_i*VHR_i(T); x_i from mass fractions via "
                    "x_i=(w_i/M_i)/sum_j(w_j/M_j); VHR_i(T)=(P_i^0(T)/760)*1e6/PEL_i; gamma_i=1 (ideal, declared)"),
        "temperature_grid_C": T_GRID,
        "reference_temperature_C": T_REF,
        "ideality_declaration": ("Raoult's law is applied with gamma_i = 1. For alcohol + aromatic blends "
                                 "positive deviation (gamma_alcohol > 1) is expected, so the ideal MHI is a "
                                 "LOWER bound for those blends. No activity coefficients are invented; the "
                                 "dominance calls are instead stress-tested by reporting gamma_crit."),
        "n_solvents_admitted": len(PANEL),
        "n_blends_defined": len(BLENDS),
        "n_blends_admitted": len(admitted),
        "molar_mass_records": mw_records,
        "pure_component_vhr_by_T": pure,
        "blends": blends_out,
        "binary_dominance_crossovers": crossovers,
        "crossover_empirical_validation": crossover_validation,
        "probe_unnormalised_blend": p1,
        "probe_non_admitted_solvent": p2,
        "probe_corrupted_formula": formula_probe,
        "aggregate": {
            "max_identity_abs_error": max(exactness_errs) if exactness_errs else None,
            "identity_exact": (max(exactness_errs) if exactness_errs else 0.0) <= EXACTNESS_TOL,
            "h0_mass_surrogate": h0_mass,
            "h0_pure_worst_actor": h0_worst,
            "n_blends_mass_surrogate_preserves_dominant_at_25C": n_mass_pres_dom,
            "min_gamma_crit_at_25C": min_gcrit_overall,
            "n_crossover_pairs": len(crossovers),
            "n_crossovers_below_5wt_pct": sum(1 for r in crossovers if r["trace_dominates_below_5wt_pct"]),
            "crossover_prediction_bracketed_at_all_T": crossover_validation["bracketed_at_all_temperatures"],
            "crossover_predicted_mass_fraction_25C": next(
                r["predicted_crossover_mass_fraction"] for r in crossover_validation["per_temperature"]
                if r["temperature_C"] == T_REF),
            "finding": ("Composing Raoult (1887), Dalton (1802) and the OSHA additive mixture rule reduces "
                        "EXACTLY to a mole-fraction-weighted sum of the module's existing pure-component "
                        "VHRs, which supplies the blend-level index the single-substance receipts lacked. "
                        "Two operational consequences follow. (i) Thinner specs are written in mass "
                        "fractions; using them directly as weights mis-states the blend hazard index "
                        "because the panel's molar masses span 3.3x. (ii) The dominant contributor is set "
                        "by mole fraction times VHR, not by VHR alone, so a trace fast solvent has a "
                        "closed-form dominance-crossover mass fraction above which it governs the "
                        "ventilation requirement -- for methanol carried over into an aromatic thinner "
                        "that crossover sits at a few weight percent."),
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
    (BENCH / "run_mixture_additivity.py").write_bytes(Path(__file__).read_bytes())
    harness_sha = sha(Path(__file__).read_bytes())

    agg = diag["aggregate"]
    admitted = [b for b in diag["blends"] if b["admitted"]]

    gates = []

    def gate(gid, observed, passed, floor, note):
        gates.append({"gate_id": gid, "observed": observed, "passed": bool(passed),
                      "floor": floor, "note": note})

    gate("blends_admitted_at_least_5", diag["n_blends_admitted"],
         diag["n_blends_admitted"] >= 5, 5,
         "at least 5 rights-clean marine-thinner composition scenarios are evaluated")
    gate("raoult_dalton_osha_identity_exact", agg["max_identity_abs_error"],
         agg["identity_exact"], EXACTNESS_TOL,
         "direct Raoult/Dalton/OSHA chain equals the reduced sum_i x_i*VHR_i identity to f64 round-off")
    gate("molar_masses_rederived_formula_checked", len(diag["molar_mass_records"]),
         all(r["formula_match"] for r in diag["molar_mass_records"]),
         len(diag["molar_mass_records"]),
         "every molar mass is re-derived from SMILES by RDKit and matches its declared molecular formula")
    gate("mole_fractions_sum_to_one",
         max(b["mole_fraction_sum_closure_error"] for b in admitted),
         all(b["mole_fraction_sum_closure_error"] <= 1e-12 for b in admitted), 1e-12,
         "mass->mole conversion is closed to f64 round-off (unrounded mole fractions sum to 1) for every blend")
    gate("contribution_shares_sum_to_one",
         max(b["per_temperature"][str(t)]["contribution_share_closure_error"]
             for b in admitted for t in diag["temperature_grid_C"]),
         all(b["per_temperature"][str(t)]["contribution_share_closure_error"] <= 1e-12
             for b in admitted for t in diag["temperature_grid_C"]), 1e-12,
         "per-constituent hazard shares partition the blend index to f64 round-off at every temperature")
    gate("mass_vs_mole_fraction_divergence_material",
         max(b["max_abs_mass_minus_mole_fraction"] for b in admitted),
         max(b["max_abs_mass_minus_mole_fraction"] for b in admitted) > 0.01, 0.01,
         "mass and mole fractions differ materially (>1 percentage point) in at least one blend, so the surrogate question is not vacuous")
    gate("h0_mass_surrogate_adjudicated", agg["h0_mass_surrogate"]["verdict"],
         agg["h0_mass_surrogate"]["verdict"] in ("REFUTED", "NOT_REFUTED"), "adjudicated",
         "H0_MASS_SURROGATE is adjudicated against a pre-declared 5% adequacy criterion")
    gate("h0_pure_worst_actor_adjudicated", agg["h0_pure_worst_actor"]["verdict"],
         agg["h0_pure_worst_actor"]["verdict"] in ("REFUTED", "NOT_REFUTED"), "adjudicated",
         "H0_PURE_WORST_ACTOR is adjudicated on the admitted blend set")
    gate("dominance_crossovers_computed", agg["n_crossover_pairs"],
         agg["n_crossover_pairs"] >= 6, 6,
         "closed-form binary dominance-crossover mass fractions are reported for at least 6 bulk/trace pairs")
    cv = diag["crossover_empirical_validation"]
    gate("closed_form_crossover_empirically_bracketed",
         [{"T": r["temperature_C"], "predicted": r["predicted_crossover_mass_fraction"],
           "bracket": [r["observed_bracket_low"], r["observed_bracket_high"]]}
          for r in cv["per_temperature"]],
         cv["bracketed_at_all_temperatures"], True,
         "the closed-form methanol-in-xylene dominance crossover falls strictly inside the observed "
         "flip bracket of the 1/3/6 wt% carryover series at every temperature -- the crossover is "
         "verified against independently computed blends, not merely asserted")
    gate("both_h0_worst_actor_outcomes_present",
         [len([b for b in admitted if b["per_temperature"][str(T_REF)]["pure_worst_actor_is_dominant"]]),
          len([b for b in admitted if not b["per_temperature"][str(T_REF)]["pure_worst_actor_is_dominant"]])],
         any(b["per_temperature"][str(T_REF)]["pure_worst_actor_is_dominant"] for b in admitted)
         and any(not b["per_temperature"][str(T_REF)]["pure_worst_actor_is_dominant"] for b in admitted),
         True,
         "the blend set contains blends on both sides of H0_PURE_WORST_ACTOR, so the refutation is not an artefact of a one-sided scenario choice")
    gate("gamma_crit_reported_no_invented_activity_coeffs", agg["min_gamma_crit_at_25C"],
         agg["min_gamma_crit_at_25C"] is not None, "non-null",
         "non-ideality sensitivity is expressed as gamma_crit (a ratio of pinned quantities); no activity coefficient is fabricated")
    gate("unnormalised_blend_rejected", diag["probe_unnormalised_blend"]["rejected_by_normalisation_gate"],
         diag["probe_unnormalised_blend"]["rejected_by_normalisation_gate"] is True, True,
         "a blend whose mass fractions sum to 0.90 is rejected, not silently renormalised")
    gate("non_admitted_solvent_blend_rejected", diag["probe_non_admitted_solvent"]["rejected_by_admission_gate"],
         diag["probe_non_admitted_solvent"]["rejected_by_admission_gate"] is True, True,
         "a blend containing a solvent with no admitted Antoine set is abstained whole, not scored on a subset")
    gate("corrupted_formula_rejected", diag["probe_corrupted_formula"]["rejected_by_formula_gate"],
         diag["probe_corrupted_formula"]["rejected_by_formula_gate"] is True, True,
         "a corrupted declared molecular formula is caught before its molar mass can enter a mole-fraction conversion")
    gate("two_replay_byte_stable", 1.0, s1 == s2, 1.0,
         "diagnostic canonical SHA identical across two replays")

    n_pass = sum(1 for g in gates if g["passed"])
    n_def = len(gates)

    kpis = {
        "method": diag["method"],
        "formula": diag["formula"],
        "temperature_grid_C": diag["temperature_grid_C"],
        "ideality_declaration": diag["ideality_declaration"],
        "n_solvents_admitted": diag["n_solvents_admitted"],
        "n_blends_defined": diag["n_blends_defined"],
        "n_blends_admitted": diag["n_blends_admitted"],
        "molar_mass_records": diag["molar_mass_records"],
        "pure_component_vhr_by_T": diag["pure_component_vhr_by_T"],
        "blends": diag["blends"],
        "binary_dominance_crossovers": diag["binary_dominance_crossovers"],
        "crossover_empirical_validation": diag["crossover_empirical_validation"],
        "probe_unnormalised_blend": diag["probe_unnormalised_blend"],
        "probe_non_admitted_solvent": diag["probe_non_admitted_solvent"],
        "probe_corrupted_formula": diag["probe_corrupted_formula"],
        "aggregate": diag["aggregate"],
        "blend_composition_provenance": (
            "Blend mass fractions are illustrative rights-clean scenarios constructed to span the marine "
            "2K epoxy-amine thinner design space (aromatic-rich, ketone-boosted fast, alcohol-rich "
            "anti-blush, wash-solvent carryover). They are NOT vendor formulations and encode no "
            "supplier-proprietary composition. The physical conclusions (identity exactness, mass-vs-mole "
            "surrogate error, closed-form dominance crossover) are properties of the solvents' molar "
            "masses, vapour pressures and PELs, not of the illustrative fractions."),
        "pel_denominator_source": (
            "OSHA 29 CFR 1910.1000 Table Z-1 (8-hour TWA permissible exposure limits) with the additive "
            "mixture rule at 1910.1000(d)(2)(i); U.S. federal regulation, public domain"),
        "theory_references": REFERENCES,
        "relationship_to_prior_receipts": (
            "First BLEND-level receipt in the module. benchmarks/vapor-hazard-ratio-v1 (Popendorf 2006) "
            "scores single substances at 25 C; benchmarks/vhr-temperature-envelope-v1 propagates those "
            "single substances over 15-40 C with the Antoine sets validated in "
            "benchmarks/antoine-vp-crosscheck-v1. This benchmark composes Raoult (1887) + Dalton (1802) + "
            "the OSHA additive mixture rule on top of exactly those pinned VHR(T) values and shows the "
            "chain reduces exactly to sum_i x_i*VHR_i -- so the prior receipts are recovered as the "
            "x_i=1 special case. It then adjudicates two hypotheses the single-substance receipts could "
            "not pose: whether mass-fraction weighting is an adequate surrogate for mole-fraction "
            "weighting, and whether the pure-component worst actor is the dominant blend contributor."),
        "receipt_meta": {
            "sci_pipeline_module": "amphora-sourceability-ehs/benchmarks/mixture-additivity-raoult-osha-v1/run_mixture_additivity.py",
            "sci_pipeline_seed": 0,
            "harness_sha256": harness_sha,
            "diagnostic_canonical_sha256": diag_sha,
            "rdkit_version": __import__("rdkit").__version__,
            "data_extraction_method": (
                "Antoine coefficients and OSHA Table Z-1 PELs carried over unchanged from the module's "
                "already-signed vhr-temperature-envelope-v1 receipt; molar masses re-derived from SMILES "
                "via RDKit and cross-checked against declared molecular formulae. No LLM-authored "
                "constants, no fitted parameters, no RNG."),
        },
        "authority_ceiling_note": (
            "EVIDENCE_ONLY quantitative BLEND-level inhalation-hazard PRESCREEN. Apportions intrinsic "
            "saturated-headspace hazard among a thinner blend's constituents to target engineering "
            "ventilation and to flag trace constituents that govern. Assumes ideal-solution Raoult "
            "behaviour (declared, with gamma_crit sensitivity reported) and saturated headspace, which is "
            "a bounding rather than a realised exposure. Does NOT establish OSHA compliance, exposure "
            "assessment, control banding, respirator selection, procurement approval, or regulatory "
            "closure."),
    }
    receipt_id = "mixture-additivity-raoult-osha-inhalation-prescreen-" + sha(canon(kpis))
    body_obj = {
        "kpis": kpis,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "human_review_performed": False,
        "module_id": "amphora-sourceability-ehs",
        "receipt_id": receipt_id,
        "reviewer_key_id": PUB["key_id"],
        "reviewer_public_key_hex": PUB["public_key_hex"],
        "schema": "amphora.mixture-additivity-raoult-osha-inhalation-prescreen.v1",
    }
    ptype = "application/vnd.amphora.mixture-additivity-raoult-osha-inhalation-prescreen.v1+json"
    signed, body_sha = sign_receipt(body_obj, ptype)
    receipt_path = MOD / "reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json"
    receipt_path.write_bytes(canon(signed))

    kpi_obj = {
        "kpi_id": "mixture-additivity-raoult-osha-inhalation-prescreen-kpi.v1",
        "schema": "amphora.phase0-kpi.v1",
        "module_id": "amphora-sourceability-ehs",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "EVIDENCE_ONLY",
        "solver_use_ceiling": "DISABLED",
        "promotes_authority": False,
        "capability": "blend-resolved quantitative vapour-inhalation-hazard prescreen (Raoult/Dalton/OSHA mixture index with per-constituent apportionment and closed-form dominance crossover)",
        "theory": "Raoult 1887 + Dalton 1802 + OSHA 29 CFR 1910.1000(d)(2)(i) additive mixture rule composed over Popendorf 2006 VHR(T) from Antoine 1888 coefficients; molar masses from IUPAC 2021 weights via RDKit",
        "population": "6 illustrative marine 2K epoxy-amine thinner composition scenarios over the 6-solvent rights-clean-Antoine panel, at 15/25/40 C",
        "split_methodology": "N/A (deterministic physical/regulatory computation; no train/test, no fitted parameters)",
        "n_deterministic_gates_defined": n_def,
        "n_deterministic_gates_passed": n_pass,
        "phase0_deterministic_gates_passed": gates,
        "observed_kpi_summary": {
            "n_blends_admitted": diag["n_blends_admitted"],
            "max_identity_abs_error": agg["max_identity_abs_error"],
            "identity_exact": agg["identity_exact"],
            "h0_mass_surrogate_verdict": agg["h0_mass_surrogate"]["verdict"],
            "max_mass_surrogate_relative_error": agg["h0_mass_surrogate"]["max_abs_relative_error_over_blends_and_T"],
            "h0_pure_worst_actor_verdict": agg["h0_pure_worst_actor"]["verdict"],
            "blends_where_pure_worst_actor_not_dominant": agg["h0_pure_worst_actor"]["blends_where_violated"],
            "n_crossovers_below_5wt_pct": agg["n_crossovers_below_5wt_pct"],
            "crossover_predicted_mass_fraction_25C": agg["crossover_predicted_mass_fraction_25C"],
            "crossover_prediction_bracketed_at_all_T": agg["crossover_prediction_bracketed_at_all_T"],
            "min_gamma_crit_at_25C": agg["min_gamma_crit_at_25C"],
        },
        "scientific_receipt_id": receipt_id,
        "scientific_receipt_path": "amphora-sourceability-ehs/reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json",
        "scientific_receipt_body_sha256": body_sha,
        "reviewer_key_id": PUB["key_id"],
        "reviewer_public_key_hex": PUB["public_key_hex"],
        "claim_locks": {
            "authority_ceiling": "EVIDENCE_ONLY",
            "not_compliance_determination": True,
            "not_exposure_assessment": True,
            "not_procurement_approval": True,
            "not_respirator_selection": True,
            "ideal_solution_assumption_declared": True,
            "rights_clean_inputs_only": True,
        },
        "awaiting": "PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER human dual-identity signatures (governance; absent on this cron host)",
    }
    kpi_ptype = "application/vnd.amphora.phase0-kpi.v1+json"
    kpi_signed, kpi_body_sha = sign_receipt(kpi_obj, kpi_ptype)
    kpi_path = MOD / "evidence/phase0/kpis/mixture-additivity-raoult-osha-inhalation-prescreen-kpi.v1.json"
    kpi_path.write_bytes(canon(kpi_signed))

    print("=== Raoult/Dalton/OSHA blend inhalation-hazard additivity ===")
    print(f"gates: {n_pass}/{n_def} passed")
    for g in gates:
        print(f"  [{'PASS' if g['passed'] else 'FAIL'}] {g['gate_id']}: {g['observed']}")
    print("--- blends @25 C ---")
    for b in admitted:
        p = b["per_temperature"][str(T_REF)]
        print(f"  {b['blend_id']:34s} MHI={p['mhi_mole_weighted']:9.1f} "
              f"mass_naive={p['mhi_mass_weighted_naive']:9.1f} "
              f"relerr={p['mass_surrogate_relative_error']:+.4f} "
              f"dom={p['dominant_contributor']:14s}({p['dominant_contributor_share']:.3f}) "
              f"pure_worst={p['pure_component_worst_actor']:14s} "
              f"holds={p['pure_worst_actor_is_dominant']} gcrit_min={p['min_gamma_crit']}")
    print("--- binary dominance crossovers (trace wt fraction) ---")
    for r in diag["binary_dominance_crossovers"]:
        print(f"  bulk={r['bulk_solvent']:10s} trace={r['trace_solvent']:14s} "
              f"w*15C={r['crossover_mass_fraction_15C']:.4f} w*25C={r['crossover_mass_fraction_25C']:.4f} "
              f"w*40C={r['crossover_mass_fraction_40C']:.4f} shift={r['crossover_shift_15_to_40C']:+.4f}")
    print("--- closed-form crossover vs observed flip bracket (methanol in m-xylene) ---")
    for r in diag["crossover_empirical_validation"]["per_temperature"]:
        print(f"  T={r['temperature_C']:.0f}C predicted w*={r['predicted_crossover_mass_fraction']:.5f} "
              f"observed bracket=({r['observed_bracket_low']}, {r['observed_bracket_high']}) "
              f"inside={r['prediction_inside_observed_bracket']}")
    print(f"H0_MASS_SURROGATE   : {agg['h0_mass_surrogate']['verdict']} "
          f"(max relerr {agg['h0_mass_surrogate']['max_abs_relative_error_over_blends_and_T']})")
    print(f"H0_PURE_WORST_ACTOR : {agg['h0_pure_worst_actor']['verdict']} "
          f"violated={agg['h0_pure_worst_actor']['blends_where_violated']}")
    print(f"identity_max_abs_error={agg['max_identity_abs_error']}")
    print("RECEIPT", receipt_path)
    print("RECEIPT_BODY_SHA256", body_sha)
    print("RECEIPT_ID", receipt_id)
    print("KPI", kpi_path)
    print("KPI_BODY_SHA256", kpi_body_sha)
    print("N_PASS", n_pass, "N_DEF", n_def)


if __name__ == "__main__":
    main()
