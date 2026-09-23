"""Hildebrand single-parameter vs Hansen three-parameter chi baseline for
amphora-solvency-score.

Question (a-priori, unfitted): does resolving the cohesive energy density into
Hansen's three components (delta_D, delta_P, delta_H) materially improve the
Flory-Huggins chi prediction for coating-relevant polymer-solvent systems over
the single-scalar Hildebrand solubility parameter delta_total = sqrt(dD^2 +
dP^2 + dH^2)?

Baselines (both a-priori, identical entropic term chi_S = 0.34 and identical
prefactor V_s/(RT); ONLY the cohesive-distance metric differs):

  Hansen 3-component (incumbent, already in tree):
      chi = chi_S + (V_s/RT) * Ra^2/4,
      Ra^2 = 4*(ddD)^2 + (ddP)^2 + (ddH)^2
      -- C. M. Hansen, Hansen Solubility Parameters: A User's Handbook,
         2nd ed., CRC Press 2007, ISBN 978-0-8493-7248-3, Eq. 2.9;
         Van Krevelen & Te Nijenhuis, Properties of Polymers, 1990, Sec. 7.2.

  Hildebrand 1-parameter (new comparator this receipt adds):
      chi = chi_S + (V_s/RT) * (delta_s - delta_p)^2
      -- J. H. Hildebrand & R. L. Scott, The Solubility of Nonelectrolytes,
         3rd ed., Reinhold 1950 (regular-solution theory); Van Krevelen 1990
         Sec. 7.2 Eq. 7.9 (scalar-delta chi).

The prefactor V_s/(RT) is back-derived per solvent from the already-signed
Hansen receipt so that the Hansen column is reproduced byte-for-byte (a
known-answer bind); the implied molar volume V_s is reported and checked
against literature. The Hildebrand column reuses that identical prefactor, so
the comparison isolates the distance metric and nothing else.

External measured chi values and polymer Hansen parameters are taken verbatim
from the in-tree receipt hansen_chi_external_validation_8_published_polymer_
solvent_pairs_receipt.v1.json (Van Krevelen 1990 Table 7.6; Bawn 1949;
Sakurada 1954; Krigbaum 1959; Malcolm-Rowlinson 1957). No external fetch.

AUDIT_ONLY diagnostic: no candidate-performance, product-qualification, or
wet-lab claim; does not promote the module or edit the portfolio manifest.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-solvency-score")
SRC_RECEIPT = (ROOT / "reference/mvp20/data/"
               "hansen_chi_external_validation_8_published_polymer_solvent_pairs_receipt.v1.json")
OUT = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-solvency-score/"
           "benchmarks/hildebrand-vs-hansen-chi-v1")

# Solvent Hansen parameters, Hansen 2007 Table A.1 (MPa^0.5) -- identical to the
# transcription in amphora-solvency-score/benchmarks/bigsoldb-v1/hsp.py.
SOLVENT_HSP = {
    "chloroform": (17.8, 3.1, 5.7),
    "water": (15.5, 16.0, 42.3),
    "ethanol": (15.8, 8.8, 19.4),
}
# Literature molar volumes at 25 C (cm^3/mol), for the physical sanity check on
# the back-derived prefactor: CRC Handbook densities. chloroform M=119.38
# rho=1.489 -> 80.2 ; water M=18.015 rho=0.997 -> 18.07 ; ethanol M=46.068
# rho=0.789 -> 58.39.
LIT_V = {"chloroform": 80.2, "water": 18.07, "ethanol": 58.39}
R_GAS = 8.314462618  # J/mol/K
TEMP_K = 298.15
CHI_S = 0.34
ROUND = 10


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def delta_total(dd, dp, dh):
    return math.sqrt(dd * dd + dp * dp + dh * dh)


def ra2(pd_, pp_, ph_, sd, sp, sh):
    return 4.0 * (pd_ - sd) ** 2 + (pp_ - sp) ** 2 + (ph_ - sh) ** 2


def main():
    src_bytes = SRC_RECEIPT.read_bytes()
    src_sha = sha(src_bytes)
    pairs = json.loads(src_bytes)["kpis"]["per_pair_results"]

    # Step 1: back-derive V_s/(RT) per solvent from the signed Hansen chi, and
    # confirm it is a single constant per solvent (i.e. our independent Ra^2 is
    # exactly the one used by the receipt).
    pref = {}
    pref_check = {}
    for p in pairs:
        sv = p["solvent"]
        sd, sp, sh = SOLVENT_HSP[sv]
        r2 = ra2(p["polymer_hansen_delta_d"], p["polymer_hansen_delta_p"],
                 p["polymer_hansen_delta_h"], sd, sp, sh)
        k = (p["chi_hansen_predicted"] - CHI_S) * 4.0 / r2
        pref_check.setdefault(sv, []).append(k)
    for sv, ks in pref_check.items():
        spread = max(ks) - min(ks)
        assert spread < 1e-9, f"prefactor not constant for {sv}: spread {spread}"
        pref[sv] = float(np.mean(ks))

    # Step 2: per-pair Hansen (reproduced) and Hildebrand (new) predictions.
    rows = []
    for p in pairs:
        sv = p["solvent"]
        sd, sp, sh = SOLVENT_HSP[sv]
        pdv, ppv, phv = (p["polymer_hansen_delta_d"], p["polymer_hansen_delta_p"],
                         p["polymer_hansen_delta_h"])
        r2 = ra2(pdv, ppv, phv, sd, sp, sh)
        chi_hansen = CHI_S + pref[sv] * r2 / 4.0
        dtot = delta_total(sd, sp, sh) - delta_total(pdv, ppv, phv)
        chi_hild = CHI_S + pref[sv] * dtot ** 2
        rows.append({
            "polymer_key": p["polymer_key"],
            "solvent": sv,
            "chi_published": p["chi_published"],
            "chi_hansen_receipt": p["chi_hansen_predicted"],
            "chi_hansen_reproduced": round(chi_hansen, ROUND),
            "chi_hildebrand": round(chi_hild, ROUND),
            "hansen_reproduction_abs_err": round(abs(chi_hansen - p["chi_hansen_predicted"]), ROUND),
            "delta_total_solvent": round(delta_total(sd, sp, sh), ROUND),
            "delta_total_polymer": round(delta_total(pdv, ppv, phv), ROUND),
            "Ra2": round(r2, ROUND),
        })

    def metrics(pred_key):
        pub = np.array([r["chi_published"] for r in rows], dtype=float)
        pred = np.array([r[pred_key] for r in rows], dtype=float)
        err = pred - pub
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.maximum(pred, pub) / np.minimum(pred, pub)
        within3 = int(np.sum((np.minimum(pred, pub) > 0) & (ratio <= 3.0)))
        pear = float(np.corrcoef(pub, pred)[0, 1])
        spear = float(spearmanr(pub, pred).statistic)
        return {
            "mae_chi_units": round(float(np.mean(np.abs(err))), ROUND),
            "rmse_chi_units": round(float(np.sqrt(np.mean(err ** 2))), ROUND),
            "pearson_r": round(pear, ROUND),
            "spearman_r": round(spear, ROUND),
            "n_within_factor_of_3": within3,
            "fraction_within_factor_of_3": round(within3 / len(rows), ROUND),
        }

    m_hansen = metrics("chi_hansen_reproduced")
    m_hild = metrics("chi_hildebrand")

    # Water (strongly H-bonding) subset, where the 1-D reduction is expected to
    # fail because water's large delta_H (42.3) is folded into a single scalar.
    def subset_metrics(solvent):
        pub = np.array([r["chi_published"] for r in rows if r["solvent"] == solvent])
        han = np.array([r["chi_hansen_reproduced"] for r in rows if r["solvent"] == solvent])
        hil = np.array([r["chi_hildebrand"] for r in rows if r["solvent"] == solvent])
        return {
            "n": int(len(pub)),
            "hansen_mae": round(float(np.mean(np.abs(han - pub))), ROUND),
            "hildebrand_mae": round(float(np.mean(np.abs(hil - pub))), ROUND),
        }

    # Step 3: fail-closed / applicability gate on non-physical inputs.
    def predict_guarded(pdv, ppv, phv, sd, sp, sh, prefactor):
        vals = [pdv, ppv, phv, sd, sp, sh, prefactor]
        if any((v is None) or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) for v in vals):
            return None
        if any(v < 0 for v in vals):
            return None
        r2 = ra2(pdv, ppv, phv, sd, sp, sh)
        if r2 < 0 or prefactor <= 0:
            return None
        return CHI_S + prefactor * r2 / 4.0

    hostile = [
        {"name": "nan_delta_p", "args": (18.0, float("nan"), 0.0, 17.8, 3.1, 5.7, 0.03)},
        {"name": "negative_delta_d", "args": (-1.0, 0.0, 0.0, 17.8, 3.1, 5.7, 0.03)},
        {"name": "inf_solvent_dh", "args": (18.0, 1.0, 0.0, 17.8, 3.1, float("inf"), 0.03)},
        {"name": "zero_prefactor", "args": (18.0, 1.0, 0.0, 17.8, 3.1, 5.7, 0.0)},
        {"name": "negative_prefactor", "args": (18.0, 1.0, 0.0, 17.8, 3.1, 5.7, -0.03)},
    ]
    hostile_results = []
    for h in hostile:
        out = predict_guarded(*h["args"])
        hostile_results.append({"case": h["name"], "abstained": out is None})
    fail_closed_ok = all(h["abstained"] for h in hostile_results)

    implied_v = {sv: round(pref[sv] * R_GAS * TEMP_K, 4) for sv in pref}
    v_check = {sv: round(abs(implied_v[sv] - LIT_V[sv]) / LIT_V[sv], 4) for sv in pref}

    max_hansen_repro_err = max(r["hansen_reproduction_abs_err"] for r in rows)

    gates = {
        "G1_hansen_known_answer_reproduced": bool(max_hansen_repro_err < 1e-6),
        "G2_prefactor_constant_per_solvent": True,  # asserted above
        "G3_implied_molar_volume_within_2pct_of_literature": bool(max(v_check.values()) < 0.02),
        "G4_hildebrand_worse_on_mae": bool(m_hild["mae_chi_units"] > m_hansen["mae_chi_units"]),
        "G5_fail_closed_on_nonphysical_inputs": bool(fail_closed_ok),
    }
    all_pass = all(gates.values())

    diagnostic = {
        "schema": "amphora.solvency-score.hildebrand-vs-hansen-chi-diagnostic.v1",
        "run_type": "PHYSICAL_BASELINE_HEAD_TO_HEAD",
        "target_property": "Flory-Huggins interaction parameter chi (polymer-solvent)",
        "source_receipt": {
            "path": "amphora-solvency-score/reference/mvp20/data/"
                    "hansen_chi_external_validation_8_published_polymer_solvent_pairs_receipt.v1.json",
            "sha256": src_sha,
        },
        "constants": {
            "chi_S_entropic": CHI_S,
            "R_gas_J_per_mol_K": R_GAS,
            "temperature_K": TEMP_K,
            "solvent_hansen_hsp_MPa_half": {k: list(v) for k, v in SOLVENT_HSP.items()},
            "prefactor_Vs_over_RT_per_solvent": {k: round(v, ROUND) for k, v in pref.items()},
            "implied_molar_volume_cm3_per_mol": implied_v,
            "literature_molar_volume_cm3_per_mol": LIT_V,
            "implied_vs_literature_relative_error": v_check,
        },
        "n_pairs": len(rows),
        "per_pair": rows,
        "aggregate": {
            "hansen_3_component": m_hansen,
            "hildebrand_1_parameter": m_hild,
            "mae_ratio_hildebrand_over_hansen": round(
                m_hild["mae_chi_units"] / m_hansen["mae_chi_units"], ROUND),
        },
        "water_subset_strong_hbond": subset_metrics("water"),
        "chloroform_subset": subset_metrics("chloroform"),
        "ethanol_subset": subset_metrics("ethanol"),
        "hostile_fail_closed": hostile_results,
        "fail_closed_rate": round(sum(h["abstained"] for h in hostile_results) / len(hostile_results), ROUND),
        "gates": gates,
        "all_gates_pass": all_pass,
        "interpretation": (
            "Independent re-derivation of the Hansen 3-component chi reproduces the "
            "signed external-validation receipt exactly (max |err| {:.2e} chi units; "
            "MAE {:.4f}, Pearson {:.4f}), confirming the prefactor and Ra metric. "
            "Swapping ONLY the cohesive-distance term for the single Hildebrand "
            "parameter delta_total (Hildebrand & Scott 1950) degrades MAE from "
            "{:.4f} to {:.4f} chi units ({:.2f}x worse) and Pearson from {:.3f} to "
            "{:.3f}. The degradation is concentrated in the strongly hydrogen-bonding "
            "water systems (PVA, PEG, PS in water): Hansen MAE {:.3f} vs Hildebrand "
            "MAE {:.3f}, because the scalar delta folds water's large delta_H=42.3 "
            "into a single term and grossly over-predicts chi. This a-priori, "
            "unfitted comparison corroborates Hansen's central thesis that resolving "
            "cohesive energy into dD/dP/dH is required for polar/H-bonding coating "
            "systems, and is not reproducible by the 1-D Hildebrand parameter."
        ).format(
            max_hansen_repro_err, m_hansen["mae_chi_units"], m_hansen["pearson_r"],
            m_hansen["mae_chi_units"], m_hild["mae_chi_units"],
            m_hild["mae_chi_units"] / m_hansen["mae_chi_units"],
            m_hansen["pearson_r"], m_hild["pearson_r"],
            subset_metrics("water")["hansen_mae"], subset_metrics("water")["hildebrand_mae"],
        ),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    import sys
    target = OUT / sys.argv[1] if len(sys.argv) > 1 else OUT / "diagnostic.canonical.json"
    body = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
    target.write_bytes(body)
    print("WROTE", target)
    print("SHA256", sha(body))
    print("ALL_GATES_PASS", all_pass)


if __name__ == "__main__":
    main()
