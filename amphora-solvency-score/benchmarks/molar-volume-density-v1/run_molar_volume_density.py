"""Experimental validation of amphora-solvency-score's Fedors/Van-Krevelen molar
-volume engine against measured liquid densities (BigSolDB v2.0, CC-BY-4.0).

WHY THIS EXISTS
---------------
Every Hansen/Hildebrand solubility-parameter estimate the solvency module makes
for an unmeasured molecule divides by a group-contribution *molar volume* V:

        delta_D = sum(F_di)/V ,  delta_P = .../V ,  delta_H = sqrt(sum E_hi / V)

That V is computed by `hvk_hsp()` in this module's own `hsp.py` using Fedors'
1974 additive volume increments (R.F. Fedors, "A method for estimating both the
solubility parameters and molar volumes of liquids", Polym. Eng. Sci. 14 (1974)
147-154; also Van Krevelen & Te Nijenhuis, *Properties of Polymers* 4th ed.,
Sec. 7.2). The module's existing known-answer test (`validate_hvk`) only checks
the *HSP components* against tabulated HSP -- it never checks V itself against
an independent experimental observable. So the denominator of the whole HSP
engine has never been validated against real data.

This harness closes exactly that gap. For each coating-relevant solvent it takes
the module's OWN engine output V, forms the predicted liquid density

        rho_pred = MW / V          (MW from RDKit 2026.03.2, V from Fedors)

and compares it to the *measured* density at 298.15 K from BigSolDB v2.0
(Krasnov et al., Sci. Data 12 (2025), doi:10.1038/s41597-025-05559-8; CC-BY-4.0;
in-tree, rights DERIVATIVE_ALLOWED as bigsoldb_density-02226420...). Fedors'
increments are FIXED 1974 constants -- they are not fit to BigSolDB -- so this is
a genuine out-of-sample validation of prior theory, with zero train/test leakage.

HONESTY / AUTHORITY
-------------------
- AUDIT_ONLY. Validates the science engine; does NOT promote any module and does
  NOT close EVALUATION_SIGNATURE_ABSENT (trust-anchored key absent on host).
- Fail-closed: a solvent is scored only if (a) it maps to an in-tree rights-clean
  SMILES, (b) the engine returns a molar volume (it abstains on water/inorganics
  and unsupported elements), and (c) an experimental density at 298.15 K exists
  or can be bracket-interpolated within [283.15, 313.15] K. Everything else is
  recorded and excluded, never imputed.
- Deterministic, timing-free canonical output for a two-replay SHA-256 gate.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors

RDLogger.DisableLog("rdApp.*")

ROOT = Path(__file__).resolve().parents[3]
BENCH = Path(__file__).resolve().parent
HSP_DIR = ROOT / "amphora-solvency-score" / "benchmarks" / "bigsoldb-v1"
sys.path.insert(0, str(HSP_DIR))
import hsp  # noqa: E402  the module engine under test

DENSITY_CSV = ROOT / "feedback/v1/external_data/bigsoldb_v2/raw/BigSolDBv2.0_densities.csv"
EXPECT_DENSITY_SHA = "02226420d9fb3294cb32211dac7f6ff7fa067511924afdb9f1893af1e334aac6"
EXPECT_HSP_SHA = None  # filled at runtime and recorded (engine version pin)

T_REF = 298.15
T_WINDOW = (283.15, 313.15)  # bracket-interpolation window around T_REF

# BigSolDB solvent name -> key in hsp.PUBLISHED_SOLVENT_HSP. Every SMILES is
# reused verbatim from the module's in-tree rights-clean table; no new structure
# is introduced here. Names that cannot be mapped are reported UNMAPPED.
NAME_TO_HSP_KEY = {
    "1,2-dichloroethane": "1,2-dichloroethane",
    "1,4-dioxane": "1,4-dioxane",
    "2-Butanone": "2-butanone",
    "2-butoxyethanol": "2-butoxyethanol",
    "2-ethoxyethanol": "2-ethoxyethanol",
    "2-methoxyethanol": "2-methoxyethanol",
    "2-propoxyethanol": "2-propoxyethanol",
    "Benzene": "benzene",
    "Chlorobenzene": "chlorobenzene",
    "Cyclohexane": "cyclohexane",
    "Cyclohexanone": "cyclohexanone",
    "Dichloromethane": "dichloromethane",
    "Isobutyl acetate": "isobutyl acetate",
    "Methanol": "methanol",
    "Methyl Acetate": "methyl acetate",
    "Toluene": "toluene",
    "Water": "water",
    "acetic acid": "acetic acid",
    "acetone": "acetone",
    "acetonitrile": "acetonitrile",
    "anisole": "anisole",
    "chloroform": "chloroform",
    "cyclopentanone": "cyclopentanone",
    "diethyl ether": "diethyl ether",
    "dimethyl carbonate": "dimethyl carbonate",
    "dmac": "N,N-dimethylacetamide",
    "dmf": "N,N-dimethylformamide",
    "dmso": "dimethyl sulfoxide",
    "ethanol": "ethanol",
    "ethyl acetate": "ethyl acetate",
    "ethyl formate": "ethyl formate",
    "ethylbenzene": "ethylbenzene",
    "ethylene glycol": "ethylene glycol",
    "formamide": "formamide",
    "formic acid": "formic acid",
    "gamma-butyrolactone": "gamma-butyrolactone",
    "isobutanol": "2-methyl-1-propanol",
    "isopentanol": "3-methyl-1-butanol",
    "isopropanol": "2-propanol",
    "isopropyl acetate": "isopropyl acetate",
    "m-xylene": "m-xylene",
    "mibk": "4-methyl-2-pentanone",
    "mtbe": "methyl tert-butyl ether",
    "n-Dodecane": "n-dodecane",
    "n-Heptane": "n-heptane",
    "n-Hexane": "n-hexane",
    "n-Octane": "n-octane",
    "n-butanol": "1-butanol",
    "n-butyl acetate": "butyl acetate",
    "n-butyric acid": "n-butyric acid",
    "n-decanol": "1-decanol",
    "n-heptanol": "1-heptanol",
    "n-hexanol": "1-hexanol",
    "n-nonanol": "1-nonanol",
    "n-octanol": "1-octanol",
    "n-pentane": "n-pentane",
    "n-pentanol": "1-pentanol",
    "n-pentyl acetate": "n-pentyl acetate",
    "n-propanol": "1-propanol",
    "n-propyl acetate": "propyl acetate",
    "nmp": "N-methyl-2-pyrrolidone",
    "o-xylene": "o-xylene",
    "p-xylene": "p-xylene",
    "propionic acid": "propionic acid",
    "propylene glycol": "1,2-propanediol",
    "sec-Butanol": "2-butanol",
    "tert-butanol": "tert-butanol",
    "tetrachloromethane": "carbon tetrachloride",
    "thf": "tetrahydrofuran",
    "transcutol": "diethylene glycol monoethyl ether",
}


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse_decimal(s):
    """Parse a numeric cell that may use ',' or '.' as the decimal mark
    (BigSolDB v2.0 densities mix both). Fail loud on genuine ambiguity rather
    than guess a thousands separator."""
    s = s.strip()
    if "," in s and "." in s:
        raise ValueError(f"ambiguous decimal cell {s!r}")
    if "," in s:
        s = s.replace(",", ".")
    return float(s)


def experimental_density_at_ref(temps_densities):
    """Return (rho, mode) at 298.15 K, or None. Exact match preferred; else
    linear interpolation between the nearest points that bracket T_REF, both
    inside T_WINDOW. Fail-closed otherwise."""
    pts = sorted(temps_densities)  # list of (T, rho)
    for t, rho in pts:
        if abs(t - T_REF) < 1e-6:
            return (rho, "exact")
    below = [(t, r) for t, r in pts if t < T_REF and t >= T_WINDOW[0]]
    above = [(t, r) for t, r in pts if t > T_REF and t <= T_WINDOW[1]]
    if below and above:
        t0, r0 = below[-1]
        t1, r1 = above[0]
        rho = r0 + (r1 - r0) * (T_REF - t0) / (t1 - t0)
        return (rho, "interp")
    return None


def load_experimental():
    raw = DENSITY_CSV.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECT_DENSITY_SHA:
        print(f"FATAL density hash drift {sha} != {EXPECT_DENSITY_SHA}", file=sys.stderr)
        sys.exit(2)
    by_solvent = {}
    for row in csv.DictReader(DENSITY_CSV.open()):
        s = row["Solvent"]
        t = parse_decimal(row["Temperature_K"])
        rho = parse_decimal(row["Density_g/cm^3"])
        by_solvent.setdefault(s, []).append((t, rho))
    return by_solvent, sha


def main():
    hsp_sha = sha_file(HSP_DIR / "hsp.py")
    by_solvent, density_sha = load_experimental()

    scored = []          # solvents with pred + exp density
    excluded = []        # everything abstained/rejected, with reason

    for solvent in sorted(by_solvent):
        key = NAME_TO_HSP_KEY.get(solvent)
        if key is None:
            excluded.append({"solvent": solvent, "reason": "UNMAPPED_NAME"})
            continue
        entry = hsp.PUBLISHED_SOLVENT_HSP.get(key)
        if entry is None:
            excluded.append({"solvent": solvent, "reason": "SMILES_KEY_ABSENT", "key": key})
            continue
        smiles = entry[0]
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            excluded.append({"solvent": solvent, "reason": "SMILES_PARSE_FAIL", "smiles": smiles})
            continue
        est = hsp.hvk_hsp(smiles)  # (dD, dP, dH, V) or None -- engine under test
        if est is None:
            excluded.append({"solvent": solvent, "reason": "ENGINE_ABSTAINED",
                             "smiles": Chem.MolToSmiles(mol)})
            continue
        V = est[3]
        mw = Descriptors.MolWt(mol)
        rho_pred = mw / V
        exp = experimental_density_at_ref(by_solvent[solvent])
        if exp is None:
            excluded.append({"solvent": solvent, "reason": "NO_DENSITY_NEAR_298K",
                             "smiles": Chem.MolToSmiles(mol)})
            continue
        rho_exp, mode = exp
        err = rho_pred - rho_exp
        scored.append({
            "solvent": solvent,
            "canonical_smiles": Chem.MolToSmiles(mol),
            "mw_g_per_mol": round(mw, 3),
            "fedors_molar_volume_cm3_per_mol": round(V, 3),
            "rho_pred_g_per_cm3": round(rho_pred, 5),
            "rho_exp_g_per_cm3": round(rho_exp, 5),
            "exp_mode": mode,
            "abs_err_g_per_cm3": round(abs(err), 5),
            "signed_err_g_per_cm3": round(err, 5),
            "rel_err_pct": round(100.0 * abs(err) / rho_exp, 4),
            "signed_rel_err_pct": round(100.0 * err / rho_exp, 4),
        })

    scored.sort(key=lambda r: r["solvent"])
    n = len(scored)
    aerr = [r["abs_err_g_per_cm3"] for r in scored]
    serr = [r["signed_err_g_per_cm3"] for r in scored]
    rel = [r["rel_err_pct"] for r in scored]
    xp = [r["rho_pred_g_per_cm3"] for r in scored]
    xe = [r["rho_exp_g_per_cm3"] for r in scored]

    def mean(v):
        return sum(v) / len(v)

    def median(v):
        s = sorted(v)
        m = len(s) // 2
        return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2.0

    def pearson(a, b):
        ma, mb = mean(a), mean(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        da = sum((x - ma) ** 2 for x in a) ** 0.5
        db = sum((y - mb) ** 2 for y in b) ** 0.5
        return num / (da * db)

    n_organic = sum(1 for s in by_solvent if NAME_TO_HSP_KEY.get(s) not in (None, "water"))
    summary = {
        "n_solvents_scored": n,
        "n_organic_candidate_solvents": n_organic,
        "coverage_fraction_of_organic": round(n / n_organic, 4),
        "density_mae_g_per_cm3": round(mean(aerr), 5),
        "density_rmse_g_per_cm3": round((mean([e * e for e in aerr])) ** 0.5, 5),
        "density_median_abs_err_g_per_cm3": round(median(aerr), 5),
        "mean_abs_rel_err_pct": round(mean(rel), 4),
        "median_abs_rel_err_pct": round(median(rel), 4),
        "max_abs_rel_err_pct": round(max(rel), 4),
        "signed_mean_err_g_per_cm3": round(mean(serr), 5),
        "signed_mean_rel_err_pct": round(mean([r["signed_rel_err_pct"] for r in scored]), 4),
        "pearson_r_pred_vs_exp": round(pearson(xp, xe), 5),
    }

    # Acceptance bars grounded in the documented accuracy of the Fedors method
    # for organic-liquid molar volumes (~few % typical; Fedors 1974). Reported
    # truthfully whatever the outcome.
    bars = {
        "mean_abs_rel_err_pct_le": 6.0,
        "median_abs_rel_err_pct_le": 5.0,
        "pearson_r_ge": 0.90,
        "coverage_fraction_of_organic_ge": 0.85,
    }
    gates = {
        "mean_abs_rel_err_pct": summary["mean_abs_rel_err_pct"] <= bars["mean_abs_rel_err_pct_le"],
        "median_abs_rel_err_pct": summary["median_abs_rel_err_pct"] <= bars["median_abs_rel_err_pct_le"],
        "pearson_r": summary["pearson_r_pred_vs_exp"] >= bars["pearson_r_ge"],
        "coverage": summary["coverage_fraction_of_organic"] >= bars["coverage_fraction_of_organic_ge"],
    }
    acceptance_bar_passed = all(gates.values())

    diag = {
        "schema": "amphora.solvency-score.molar-volume-density-v1-diagnostic.v1",
        "benchmark": "amphora-solvency-score/molar-volume-density-v1",
        "run_type": "SCIENCE_VALIDATION_REPLAY",
        "authority": "AUDIT_ONLY",
        "engine": {
            "name": "Fedors 1974 additive molar volume via Hoftyzer-Van Krevelen "
                    "group decomposition (amphora-solvency-score hsp.hvk_hsp)",
            "engine_file": "amphora-solvency-score/benchmarks/bigsoldb-v1/hsp.py",
            "engine_file_sha256": hsp_sha,
            "rdkit_version": Chem.rdBase.rdkitVersion,
            "prediction": "rho_pred = MW / V_Fedors  (MW from RDKit, V from module engine)",
            "leakage": "none -- Fedors group increments are fixed 1974 constants, "
                       "not fit to BigSolDB; strict out-of-sample validation of prior theory",
        },
        "reference_data": {
            "dataset": "BigSolDB v2.0 densities (Krasnov et al., Sci. Data 12 (2025), "
                       "doi:10.1038/s41597-025-05559-8)",
            "file": "feedback/v1/external_data/bigsoldb_v2/raw/BigSolDBv2.0_densities.csv",
            "file_sha256": density_sha,
            "license": "CC-BY-4.0",
            "rights_class": "DERIVATIVE_ALLOWED",
            "rights_decision_id": "bigsoldb_density-02226420d9fb3294 (amphora-ingredient-library)",
            "temperature_reference_K": T_REF,
            "temperature_interpolation_window_K": list(T_WINDOW),
        },
        "acceptance_bar": bars,
        "gates": gates,
        "benchmark_acceptance_bar_passed": acceptance_bar_passed,
        "summary": summary,
        "scored_solvents": scored,
        "excluded": sorted(excluded, key=lambda r: r["solvent"]),
        "closes": [
            "First experimental validation of the molar-volume denominator V that "
            "underlies every HSP/solubility-parameter estimate amphora-solvency-score "
            "makes for unmeasured molecules -- validated against measured liquid "
            "densities of coating-relevant solvents, out-of-sample, zero leakage."
        ],
        "does_not_close": [
            "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0-evaluator private key absent on host; governance step)",
            "Does NOT promote amphora-solvency-score to Phase-0 (audit-only signature)",
            "Does NOT validate the delta_P/delta_H polar terms against experiment (this run validates V only)",
            "Does NOT extend to polymer repeat units / thermoset network V (solvents only here)",
        ],
        "claim_locks": {
            "scope": "marine anti-corrosion two-part epoxy-amine coating solvents only",
            "no_candidate_or_product_claim": True,
            "no_superiority_claim": True,
            "diagnostic_only": True,
        },
    }
    return diag


if __name__ == "__main__":
    diag = main()
    out = BENCH / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")
    body = json.dumps(diag, indent=2, sort_keys=True)
    out.write_text(body)
    print("WROTE", out)
    print("diagnostic_sha256", hashlib.sha256(body.encode()).hexdigest())
    s = diag["summary"]
    print(f"scored={s['n_solvents_scored']}/{s['n_organic_candidate_solvents']} "
          f"MARE={s['mean_abs_rel_err_pct']}% medARE={s['median_abs_rel_err_pct']}% "
          f"MAE={s['density_mae_g_per_cm3']} r={s['pearson_r_pred_vs_exp']} "
          f"bar_passed={diag['benchmark_acceptance_bar_passed']}")
