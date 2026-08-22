#!/usr/bin/env python3
"""W2: physical-admissibility audit across 4 in-tree corpora.

Reads directly from the shared normalized data lake
(feedback/v2/normalized/*.jsonl.gz) that amphora-molecule-property's
manifests point to, applies one independently-justified physical
constraint per corpus, and reports n_total / n_admissible / pct.
"""
import gzip, json, math, statistics
from pathlib import Path

LAKE = Path("/home/ubuntu/amphora/build/mvp20-split/feedback/v2/normalized")


def read_jsonl_gz(name):
    path = LAKE / name
    rows = []
    with gzip.open(path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return path, rows


def to_float(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        if s == "":
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


results = {}

# ---------------------------------------------------------------
# Corpus 1: OpenPoly properties -- Tg < Tm (Boyer-Beaman rule)
# ---------------------------------------------------------------
path, rows = read_jsonl_gz("openpoly_properties.jsonl.gz")
n_total = len(rows)
n_both_present = 0
n_admissible = 0
violations = []
for r in rows:
    rf = r.get("raw_fields", {})
    tg = to_float(rf.get("Tg (K)"))
    tm = to_float(rf.get("Tm (K)"))
    if tg is None or tm is None:
        continue
    n_both_present += 1
    if tg < tm:
        n_admissible += 1
    else:
        violations.append({
            "canonical_identity": r.get("canonical_identity"),
            "name": rf.get("Name"),
            "record_id": r.get("record_id"),
            "Tg_K": tg,
            "Tm_K": tm,
        })
results["openpoly_properties"] = {
    "acquisition_unit_id": "openpoly_properties",
    "raw_file_sha256": rows[0]["raw_file_sha256"] if rows else None,
    "lake_path": str(path.relative_to(LAKE.parents[1])),
    "n_total_rows": n_total,
    "n_rows_with_both_Tg_and_Tm": n_both_present,
    "n_admissible": n_admissible,
    "n_inadmissible": n_both_present - n_admissible,
    "pct_admissible_of_evaluable": (n_admissible / n_both_present) if n_both_present else None,
    "constraint": "Tg (K) < Tm (K), strict",
    "constraint_citation": "Boyer, R.F., Rubber Chem. Technol. 36, 1303 (1963); Van Krevelen & Te Nijenhuis, 'Properties of Polymers', 4th ed., Elsevier 2009, ISBN 978-0-08-054819-7, Ch.6 (Tg/Tm ratio bounded in [0.5,0.8], i.e. Tg<Tm always for any real semicrystalline/amorphous polymer -- Tg is a kinetic freezing transition of the amorphous phase that occurs strictly below the true first-order crystalline melting transition).",
    "violations_sample": violations[:10],
    "n_violations_total": len(violations),
}

# ---------------------------------------------------------------
# Corpus 2: BigSolDB solubility -- mole fraction must be in (0,1)
# ---------------------------------------------------------------
path, rows = read_jsonl_gz("bigsoldb_solubility.jsonl.gz")
n_total = len(rows)
n_evaluable = 0
n_admissible = 0
violations = []
consistency_checked = 0
consistency_ok = 0
for r in rows:
    cond = r.get("conditions", {})
    xf = to_float(cond.get("solubility_mole_fraction"))
    molL = to_float(cond.get("solubility_mol_l"))
    val_number = r.get("value_number")
    if xf is not None:
        n_evaluable += 1
        if 0.0 < xf < 1.0:
            n_admissible += 1
        else:
            violations.append({
                "record_id": r.get("record_id"),
                "canonical_identity": r.get("canonical_identity"),
                "solvent": cond.get("Solvent"),
                "mole_fraction": xf,
                "temperature_K": cond.get("Temperature_K"),
            })
    # secondary diagnostic: internal log10 consistency (not part of admissible/pct gate)
    if molL is not None and molL > 0 and val_number is not None:
        consistency_checked += 1
        if abs(math.log10(molL) - float(val_number)) < 1e-6:
            consistency_ok += 1

# duplicate-contradictory-measurement check at identical (solute, solvent, T)
by_key = {}
for r in rows:
    cond = r.get("conditions", {})
    key = (r.get("canonical_identity"), cond.get("Solvent"), cond.get("Temperature_K"))
    by_key.setdefault(key, []).append(r.get("value_number"))
n_dup_groups = 0
n_dup_contradictory = 0
CONTRADICTION_LOG_S_THRESHOLD = 0.3  # >0.3 log10 units (~2x) at identical (solute,solvent,T) -- inconsistent replicate
for key, vals in by_key.items():
    vals = [v for v in vals if v is not None]
    if len(vals) < 2:
        continue
    n_dup_groups += 1
    if max(vals) - min(vals) > CONTRADICTION_LOG_S_THRESHOLD:
        n_dup_contradictory += 1

results["bigsoldb_solubility"] = {
    "acquisition_unit_id": "bigsoldb_solubility",
    "raw_file_sha256": rows[0]["raw_file_sha256"] if rows else None,
    "lake_path": str(path.relative_to(LAKE.parents[1])),
    "n_total_rows": n_total,
    "n_rows_with_mole_fraction": n_evaluable,
    "n_admissible": n_admissible,
    "n_inadmissible": n_evaluable - n_admissible,
    "pct_admissible_of_evaluable": (n_admissible / n_evaluable) if n_evaluable else None,
    "constraint": "0 < solubility_mole_fraction < 1, strict (a mole fraction is n_solute/(n_solute+n_solvent), a probability-like quantity bounded on the open unit interval by definition)",
    "constraint_citation": "IUPAC Gold Book, 'amount fraction, mole fraction' (doi:10.1351/goldbook.A00296); definitional, not model-dependent.",
    "violations_sample": violations[:10],
    "n_violations_total": len(violations),
    "secondary_diagnostic_internal_log10_consistency": {
        "note": "NOT part of the admissible/pct gate above -- reported separately as a data-integrity cross-check.",
        "n_checked": consistency_checked,
        "n_consistent_within_1e-6": consistency_ok,
        "pct_consistent": (consistency_ok / consistency_checked) if consistency_checked else None,
    },
    "duplicate_contradictory_measurement_check": {
        "key": "(canonical_identity=solute SMILES-derived id, Solvent, Temperature_K)",
        "n_groups_with_ge2_measurements": n_dup_groups,
        "contradiction_threshold_log10_units": CONTRADICTION_LOG_S_THRESHOLD,
        "n_groups_contradictory": n_dup_contradictory,
        "pct_contradictory_of_duplicate_groups": (n_dup_contradictory / n_dup_groups) if n_dup_groups else None,
    },
}

# ---------------------------------------------------------------
# Corpus 3: BigSolDB density -- organic-liquid physical density band
# ---------------------------------------------------------------
path, rows = read_jsonl_gz("bigsoldb_density.jsonl.gz")
n_total = len(rows)
n_admissible = 0
violations = []
LO, HI = 0.6, 3.4  # g/cm^3
for r in rows:
    v = r.get("value_number")
    v = to_float(v)
    if v is None:
        continue
    if LO <= v <= HI:
        n_admissible += 1
    else:
        violations.append({
            "record_id": r.get("record_id"),
            "solvent": r.get("conditions", {}).get("Solvent") or r.get("raw_fields", {}).get("Solvent"),
            "density_g_cm3": v,
            "temperature_K": r.get("conditions", {}).get("Temperature_K"),
        })
n_evaluable = sum(1 for r in rows if to_float(r.get("value_number")) is not None)
results["bigsoldb_density"] = {
    "acquisition_unit_id": "bigsoldb_density",
    "raw_file_sha256": rows[0]["raw_file_sha256"] if rows else None,
    "lake_path": str(path.relative_to(LAKE.parents[1])),
    "n_total_rows": n_total,
    "n_rows_evaluable": n_evaluable,
    "n_admissible": n_admissible,
    "n_inadmissible": n_evaluable - n_admissible,
    "pct_admissible_of_evaluable": (n_admissible / n_evaluable) if n_evaluable else None,
    "constraint": f"{LO} g/cm^3 <= liquid density <= {HI} g/cm^3 at near-ambient conditions",
    "constraint_citation": "CRC Handbook of Chemistry and Physics, 104th ed. (2023), ISBN 978-1-032-63111-2, Section 'Physical Constants of Organic Compounds' -- common liquid organic solvents span from n-pentane (0.626 g/cm^3) to dense halogenated liquids such as diiodomethane (3.325 g/cm^3); densities outside this band indicate either a unit/transcription error or a non-liquid/non-organic-solvent entry.",
    "violations_sample": violations[:10],
    "n_violations_total": len(violations),
}

# ---------------------------------------------------------------
# Corpus 4: RadonPy/polyomics_small_molecules -- Frohlich inequality
# (generalizes the C8-fire prior finding, at 26x the row count) plus
# refractive-index lower bound n>=1.
# ---------------------------------------------------------------
path, rows = read_jsonl_gz("polyomics_small_molecules.jsonl.gz")
n_total = len(rows)
n_evaluable_frohlich = 0
n_admissible_frohlich = 0
violations_frohlich = []
n_evaluable_n = 0
n_admissible_n = 0
violations_n = []
for r in rows:
    rf = r.get("raw_fields", {})
    eps = to_float(rf.get("static_dielectric_const"))
    n = to_float(rf.get("refractive_index"))
    if n is not None:
        n_evaluable_n += 1
        if n >= 1.0:
            n_admissible_n += 1
        else:
            violations_n.append({"record_id": r.get("record_id"), "UUID": rf.get("UUID"), "n": n})
    if eps is not None and n is not None and n > 0:
        n_evaluable_frohlich += 1
        if eps >= n * n:
            n_admissible_frohlich += 1
        else:
            violations_frohlich.append({
                "record_id": r.get("record_id"),
                "UUID": rf.get("UUID"),
                "eps_static": eps,
                "n": n,
                "n_squared": n * n,
            })
results["polyomics_small_molecules"] = {
    "acquisition_unit_id": "polyomics_small_molecules",
    "raw_file_sha256": rows[0]["raw_file_sha256"] if rows else None,
    "lake_path": str(path.relative_to(LAKE.parents[1])),
    "n_total_rows": n_total,
    "constraint_A": {
        "name": "eps_static >= n_refractive^2 (Frohlich inequality)",
        "n_rows_evaluable": n_evaluable_frohlich,
        "n_admissible": n_admissible_frohlich,
        "n_inadmissible": n_evaluable_frohlich - n_admissible_frohlich,
        "pct_admissible_of_evaluable": (n_admissible_frohlich / n_evaluable_frohlich) if n_evaluable_frohlich else None,
        "constraint_citation": "Frohlich, H., 'Theory of Dielectrics', Oxford University Press, 1949, Ch.2 -- static permittivity eps_static(omega->0) sums electronic+ionic+orientational polarization and must be >= the optical/electronic-only permittivity eps_inf=n^2 (Maxwell relation) for any passive linear dielectric.",
        "violations_sample": violations_frohlich[:10],
        "n_violations_total": len(violations_frohlich),
        "note": "This is the SAME constraint applied to radonpy_pi1070 (1077 rows, C8 fires 1-3, 113/1075=10.5% admissible). polyomics_small_molecules is the larger raw RadonPy simulation-output corpus (28159 rows) that PI1070 was curated from; this generalizes the prior finding to see whether it is an artifact of the 1070-row curation or persists at full scale.",
    },
    "constraint_B": {
        "name": "refractive_index >= 1",
        "n_rows_evaluable": n_evaluable_n,
        "n_admissible": n_admissible_n,
        "n_inadmissible": n_evaluable_n - n_admissible_n,
        "pct_admissible_of_evaluable": (n_admissible_n / n_evaluable_n) if n_evaluable_n else None,
        "constraint_citation": "Lorentz-Lorenz theory (H.A. Lorentz 1880; L. Lorenz 1880); for any condensed-phase dielectric medium in the normal (non-anomalous) dispersion regime at optical frequencies, refractive index relative to vacuum n>=1 by definition of phase velocity v=c/n<=c.",
        "violations_sample": violations_n[:10],
        "n_violations_total": len(violations_n),
    },
}

out = {
    "corpora_audited": list(results.keys()),
    "n_corpora": len(results),
    "results": results,
}
Path("/tmp/w2_corpus_audit_raw_results.json").write_text(json.dumps(out, indent=2, sort_keys=True, default=str))
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("violations_sample",)} for k, v in results.items()}, indent=2, default=str))
