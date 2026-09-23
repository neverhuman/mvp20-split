#!/usr/bin/env python3
"""Z-EHS-VANLAAR: independent non-ideality audit of the mixture-additivity-raoult-osha
ideal-solution (gamma=1) blend-dominance claim in amphora-sourceability-ehs.

CLAIM UNDER ATTACK:
  amphora-sourceability-ehs/evidence/phase0/kpis/mixture-additivity-raoult-osha-inhalation-prescreen-kpi.v1.json
  amphora-sourceability-ehs/reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json
  -- specifically: dominant_contributor = m_xylene (not methanol) for the
  wash_carryover_methanol_1pct and wash_carryover_methanol_3pct blends, and the
  closed-form dominance-crossover mass fraction (3.7171 wt% methanol @ 25C,
  "bracketed at all T" 15-40C). Both rest on Raoult gamma_i=1 (ideal solution),
  declared by the receipt itself as an assumption, together with a reported
  gamma_crit sensitivity metric (the activity coefficient a non-dominant
  constituent needs to overtake the dominant one) that the receipt's own text
  explicitly invites checking against real data ("states exactly how much
  non-ideality the dominance call can absorb").

THIS AUDIT supplies a real, independently-sourced (not fabricated, not fitted
to this module's own outputs) activity coefficient for methanol in an aromatic
hydrocarbon solvent, via the standard van Laar (1910) two-parameter model
inverted from a single PUBLISHED azeotropic VLE data point, and checks it
against the module's own reported gamma_crit thresholds at the module's own
blend compositions.

PRIMARY SOURCE (methanol-toluene azeotrope):
  Burke, D. E.; Williams, G. C.; Plank, C. A. (1964) "Vapor-Liquid Equilibria
    for the Methanol-Toluene System." J. Chem. Eng. Data 9(2): 212-214.
    DOI 10.1021/je60021a018.
  Azeotrope datum (x_methanol = 0.887 mole fraction, T = 337.02 K, P = 101.3 kPa)
  as reported and re-cited in:
  He, S.; Fan, W.; Huang, H.; Gao, J.; Xu, D.; Ma, Y.; Zhang, L.; Wang, Y. (2021)
    "Separation of the Azeotropic Mixture Methanol and Toluene Using Extractive
    Distillation: Entrainer Determination, Vapor-Liquid Equilibrium Measurement,
    and Modeling." ACS Omega 6(50): 34736-34743. DOI 10.1021/acsomega.1c05164.
    Open access (PMC8697408).

PROXY CAVEAT (declared, not hidden): the module's carryover blends contain
m-xylene, not toluene. A direct methanol + o-xylene VLE dataset with fitted
Van Laar/Wilson parameters exists in the literature (Costa Lopez, J.; Garvin,
A.; Espana, F. J. (1995) "Vapor-Liquid Equilibrium Data for Methanol, Ethanol,
Methyl Acetate, Ethyl Acetate, and o-Xylene at 101.3 kPa." J. Chem. Eng. Data
40(5): 1067-1071. DOI 10.1021/je00021a008) but full text was unobtainable
during this fire (pubs.acs.org WebFetch -> HTTP 403; OSTI.gov mirror socket
error). Toluene and m-xylene are both simple monocyclic alkylbenzenes of
closely comparable polarity (Hildebrand solubility parameters approximately
18.2 and 18.0 MPa^0.5 respectively); the physical mechanism of the positive
deviation (disruption of methanol self-association by a non-polar aromatic
diluent) is the same for both, and m-xylene's activity coefficient for dilute
methanol is expected to be the same order of magnitude as toluene's, not
smaller. This is used here as a bounding proxy for a falsification check, not
asserted as a system-specific replacement value.

METHOD:
  1. Re-derive molar masses from SMILES via RDKit (independent of the module's
     own molar-mass cache), cross-checked against declared formula.
  2. Re-derive mole fractions of the three wash_carryover_methanol_{1,3,6}pct
     blends from their published mass fractions (independent of the module's
     diagnostic).
  3. Fit the van Laar A12/A21 parameters from the single published
     methanol-toluene azeotrope point (standard closed-form inversion; the
     model, van Laar 1910, is public and citable; the fit uses ONLY the
     published azeotrope T/x/P, nothing from this module).
  4. Evaluate gamma_methanol(x_methanol) at the ACTUAL methanol mole fraction
     in each carryover blend, at each T in the module's own 15/25/40C envelope
     (van Laar's excess-Gibbs-energy parameters are treated as T-independent
     over this narrow window, the model's standard limitation, declared).
  5. Recompute each blend's per-constituent MHI_sat contribution with
     gamma_methanol = the van-Laar value (others held at gamma=1, exactly
     mirroring the isolation the module's OWN gamma_crit computation uses --
     "the activity coefficient each non-dominant constituent would need...
     (others ideal)"), and compare gamma_methanol to the module's own reported
     gamma_crit for that blend/T to see whether the dominance call flips.
  6. Two-replay byte-stability gate on the resulting diagnostic.
"""
import base64
import hashlib
import json
import math
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"

ATM_MMHG = 760.0
T_GRID = [15.0, 25.0, 40.0]
KPA_TO_MMHG = 7.500616827

# --- pinned physical constants, IDENTICAL to the module's own Antoine sets
#     (benchmarks/mixture-additivity-raoult-osha-v1/run_mixture_additivity.py
#     PANEL), re-used here as public physical facts, not re-derived from the
#     module's outputs.
PANEL = {
    "methanol":  dict(smiles="CO", formula="CH4O", pel=200,
                       A=8.08097, B=1582.271, C=239.726),
    "mek_2_butanone": dict(smiles="CCC(C)=O", formula="C4H8O", pel=200,
                       A=6.97421, B=1209.600, C=216.000),
    "toluene":   dict(smiles="Cc1ccccc1", formula="C7H8", pel=200,
                       A=6.95464, B=1344.800, C=219.480),
    "m_xylene":  dict(smiles="Cc1cccc(C)c1", formula="C8H10", pel=100,
                       A=7.00908, B=1462.266, C=215.105),
    "n_butanol": dict(smiles="CCCCO", formula="C4H10O", pel=100,
                       A=7.47680, B=1362.390, C=178.770),
}

# --- claim-under-attack blend compositions, transcribed verbatim from
#     benchmarks/mixture-additivity-raoult-osha-v1/run_mixture_additivity.py
#     BLENDS (mass fractions, the same public illustrative scenarios).
BLENDS = {
    "wash_carryover_methanol_1pct": {"m_xylene": 0.97, "n_butanol": 0.02, "methanol": 0.01},
    "wash_carryover_methanol_3pct": {"m_xylene": 0.95, "n_butanol": 0.02, "methanol": 0.03},
    "wash_carryover_methanol_6pct": {"m_xylene": 0.92, "n_butanol": 0.02, "methanol": 0.06},
}

# --- published azeotrope datum used to fit van Laar (see module docstring).
AZEOTROPE = {"x_methanol": 0.887, "T_K": 337.02, "P_kPa": 101.3,
             "source": "Burke, Williams & Plank (1964) J. Chem. Eng. Data 9(2):212-214, "
                       "DOI 10.1021/je60021a018, as re-cited in He et al. (2021) ACS Omega "
                       "6(50):34736-34743, DOI 10.1021/acsomega.1c05164 (PMC8697408)"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def antoine_vp(A, B, C, t_c):
    return 10.0 ** (A - B / (C + t_c))


def molar_mass(smiles, declared_formula):
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return None, None, False
    formula = rdMolDescriptors.CalcMolFormula(m)
    return Descriptors.MolWt(m), formula, formula == declared_formula


def vhr_pure(name, t_c):
    p = PANEL[name]
    vp = antoine_vp(p["A"], p["B"], p["C"], t_c)
    return (vp / ATM_MMHG) * 1e6 / p["pel"], vp


def fit_van_laar_from_azeotrope():
    """Van Laar (1910) two-parameter fit from a single azeotropic (x,T,P) point.
    At an azeotrope x_i = y_i for every i, so gamma_i = P / P_i^sat(T) directly.
    Standard closed-form inversion (e.g. Smith, Van Ness & Abbott, 'Introduction
    to Chemical Engineering Thermodynamics'):
        A12 = ln(g1) * (1 + x2*ln(g2) / (x1*ln(g1)))^2
        A21 = ln(g2) * (1 + x1*ln(g1) / (x2*ln(g2)))^2
    """
    x1 = AZEOTROPE["x_methanol"]
    x2 = 1.0 - x1
    t_c = AZEOTROPE["T_K"] - 273.15
    p_mmhg = AZEOTROPE["P_kPa"] * KPA_TO_MMHG

    p1sat = antoine_vp(PANEL["methanol"]["A"], PANEL["methanol"]["B"], PANEL["methanol"]["C"], t_c)
    p2sat = antoine_vp(PANEL["toluene"]["A"], PANEL["toluene"]["B"], PANEL["toluene"]["C"], t_c)

    g1 = p_mmhg / p1sat
    g2 = p_mmhg / p2sat
    ln_g1, ln_g2 = math.log(g1), math.log(g2)

    A12 = ln_g1 * (1 + (x2 * ln_g2) / (x1 * ln_g1)) ** 2
    A21 = ln_g2 * (1 + (x1 * ln_g1) / (x2 * ln_g2)) ** 2

    return {
        "x1_methanol": x1, "x2_toluene": x2, "T_C": t_c, "P_mmHg": p_mmhg,
        "P1sat_methanol_mmHg": p1sat, "P2sat_toluene_mmHg": p2sat,
        "gamma1_at_azeotrope": g1, "gamma2_at_azeotrope": g2,
        "A12": A12, "A21": A21,
        "gamma1_infinite_dilution_methanol_in_toluene": math.exp(A12),
        "gamma2_infinite_dilution_toluene_in_methanol": math.exp(A21),
    }


def van_laar_gamma1(x1, A12, A21):
    x2 = 1.0 - x1
    if x1 <= 0:
        return math.exp(A12)
    return math.exp(A12 / (1 + (A12 * x1) / (A21 * x2)) ** 2)


def compute():
    vl = fit_van_laar_from_azeotrope()
    A12, A21 = vl["A12"], vl["A21"]

    mw_records = {}
    for name, spec in PANEL.items():
        m, got, ok = molar_mass(spec["smiles"], spec["formula"])
        mw_records[name] = {"molar_mass_g_per_mol": m, "rdkit_formula": got, "formula_match": ok}
        assert ok, f"formula mismatch for {name}"

    blends_out = {}
    any_flip = False
    for bid, w in BLENDS.items():
        moles = {k: w[k] / mw_records[k]["molar_mass_g_per_mol"] for k in w}
        ntot = sum(moles.values())
        x = {k: moles[k] / ntot for k in w}
        x_methanol = x["methanol"]
        g1_dilute = van_laar_gamma1(x_methanol, A12, A21)

        per_T = {}
        for t in T_GRID:
            # ideal (gamma=1) reduced contributions, matching the module's own
            # reduced identity sum_i x_i * VHR_i(T)
            contrib_ideal = {k: x[k] * vhr_pure(k, t)[0] for k in w}
            dom_ideal = max(w, key=lambda k: (contrib_ideal[k], k))
            gamma_crit_ideal = {k: round(contrib_ideal[dom_ideal] / contrib_ideal[k], 4)
                                 for k in w if k != dom_ideal}

            # non-ideal: methanol scaled by the van-Laar activity coefficient at
            # its ACTUAL mole fraction in this blend; other constituents held
            # at gamma=1 (mirrors the module's own gamma_crit isolation method).
            contrib_real = dict(contrib_ideal)
            contrib_real["methanol"] = x["methanol"] * g1_dilute * vhr_pure("methanol", t)[0]
            dom_real = max(w, key=lambda k: (contrib_real[k], k))

            gcrit_methanol_ideal_model = gamma_crit_ideal.get("methanol")
            flips = (dom_ideal != dom_real)
            any_flip = any_flip or flips

            per_T[str(t)] = {
                "contribution_ideal_gamma1": {k: round(v, 6) for k, v in contrib_ideal.items()},
                "dominant_contributor_ideal_gamma1": dom_ideal,
                "gamma_crit_methanol_to_overtake_dominant_per_module_definition": gcrit_methanol_ideal_model,
                "gamma_methanol_van_laar_at_this_x_and_T": round(g1_dilute, 4),
                "van_laar_exceeds_gamma_crit": (gcrit_methanol_ideal_model is not None
                                                  and g1_dilute > gcrit_methanol_ideal_model),
                "contribution_with_van_laar_methanol_gamma": {k: round(v, 6) for k, v in contrib_real.items()},
                "dominant_contributor_with_real_gamma": dom_real,
                "dominance_flips_under_real_gamma": flips,
            }

        blends_out[bid] = {
            "mass_fractions": w,
            "mole_fractions": {k: round(v, 6) for k, v in x.items()},
            "molar_masses_g_per_mol": {k: round(mw_records[k]["molar_mass_g_per_mol"], 5) for k in w},
            "per_temperature": per_T,
        }

    diag = {
        "schema": "amphora.sourceability-ehs.audit.z-ehs-vanlaar.diagnostic.v1",
        "module": "amphora-sourceability-ehs",
        "van_laar_fit_from_azeotrope": {k: round(v, 6) if isinstance(v, float) else v
                                         for k, v in vl.items()},
        "molar_mass_records": {k: {"molar_mass_g_per_mol": round(v["molar_mass_g_per_mol"], 5),
                                    "rdkit_formula": v["rdkit_formula"],
                                    "formula_match": v["formula_match"]}
                                for k, v in mw_records.items()},
        "blends": blends_out,
        "any_dominance_flip_under_van_laar_methanol_gamma": any_flip,
    }
    return diag


def main():
    diag1 = compute()
    diag2 = compute()
    b1, b2 = canon(diag1), canon(diag2)
    two_replay_byte_stable = sha(b1) == sha(b2)

    out_dir = MOD / "evidence/phase0/audits/Z-EHS-VANLAAR/work"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "diagnostic.canonical.json").write_bytes(json.dumps(diag1, indent=2, sort_keys=True).encode())
    (out_dir / "diagnostic.runB.json").write_bytes(json.dumps(diag2, indent=2, sort_keys=True).encode())

    print("two_replay_byte_stable", two_replay_byte_stable)
    print("any_dominance_flip_under_van_laar_methanol_gamma", diag1["any_dominance_flip_under_van_laar_methanol_gamma"])
    for bid, b in diag1["blends"].items():
        for t in ("15.0", "25.0", "40.0"):
            pt = b["per_temperature"][t]
            print(bid, t, "dom_ideal=", pt["dominant_contributor_ideal_gamma1"],
                  "dom_real=", pt["dominant_contributor_with_real_gamma"],
                  "gcrit=", pt["gamma_crit_methanol_to_overtake_dominant_per_module_definition"],
                  "gamma_vanlaar=", pt["gamma_methanol_van_laar_at_this_x_and_T"],
                  "flip=", pt["dominance_flips_under_real_gamma"])


if __name__ == "__main__":
    main()
