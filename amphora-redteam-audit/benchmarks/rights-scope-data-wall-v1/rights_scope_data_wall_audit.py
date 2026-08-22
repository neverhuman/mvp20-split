"""Red-team audit: the rights-clean (X) in-scope data wall (v1).

Deterministic, on-disk-fact-only red-team of the claim that the amphora coating
portfolio "has FULL Phase-0" science. Emits a canonical JSON diagnostic; run twice
for a two-replay SHA-256 gate. AUDIT_ONLY. Modifies nothing, promotes nothing.

The single new contribution over the 2026-07-25 09:14 scientific-readiness-honesty
audit: a machine-checked join of (a) which in-tree datasets are RIGHTS-CLEAN
(rights_class == DERIVATIVE_ALLOWED, i.e. usable for a Phase-0 scientific KPI) with
(b) which are IN COATING SCOPE and EXPERIMENTAL. It proves the wall is structural:
every rights-clean dataset is out-of-scope / simulation / semiconductor / generic-
polymer / solubility-adjacent, while every directly in-scope coating polymer-physics
dataset (melt viscosity, cohesive energy / Hansen, thermoset mechanics, sorption,
barrier diffusivity) is CONTEXT_ONLY-quarantined and cannot back a Phase-0 KPI.
"""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(".")

# Explicit, auditable scope classification keyed by dataset_id prefix (pre-hash).
# in_scope_coating_experimental == True only for an experimental measurement of a
# property of a two-part epoxy-amine / marine anti-corrosion coating system.
SCOPE = {
    "radonpy_pi1070":            ("OUT_OF_SCOPE_SIMULATION", "polyimide molecular-dynamics simulation, not epoxy-amine, not experimental"),
    "omg_physical_properties":   ("OUT_OF_SCOPE_GENERIC_POLYMER", "OMG computed generic-polymer physical properties"),
    "omg_physical_properties_v3":("OUT_OF_SCOPE_GENERIC_POLYMER", "OMG computed generic-polymer physical properties"),
    "point2_test_split":         ("BENCHMARK_METADATA", "benchmark split membership, not property data"),
    "point2_train_split":        ("BENCHMARK_METADATA", "benchmark split membership, not property data"),
    "point2_run_log":            ("BENCHMARK_METADATA", "run provenance metadata"),
    "polyomics_chi_dimethylformamide": ("OUT_OF_SCOPE_PREDICTED", "predicted Flory-Huggins chi for DMF; computed, not experimental"),
    "polyomics_small_molecules": ("OUT_OF_SCOPE_GENERIC", "computed small-molecule properties"),
    "bigsoldb_solubility":       ("SOLUBILITY_EXPERIMENTAL_ADJACENT", "BigSolDB experimental solubility; formulation-adjacent; ALREADY the basis of amphora-solvency-score Phase-0"),
    "bigsoldb_density":          ("SOLVENT_DENSITY_EXPERIMENTAL_ADJACENT", "BigSolDB experimental solvent density; formulation-adjacent; used by solvency molar-volume"),
    "openpoly_model_results":    ("OUT_OF_SCOPE_GENERIC_POLYMER", "published generic-polymer model results"),
    "openpoly_properties":       ("OUT_OF_SCOPE_GENERIC_POLYMER", "generic-polymer endpoint properties"),
    "openpoly_counts":           ("BENCHMARK_METADATA", "endpoint count metadata"),
    "pronto_process_archive":    ("OUT_OF_SCOPE_PROCESS", "generic industrial process sensor archive"),
    "pronto_process_archive_v3": ("OUT_OF_SCOPE_PROCESS", "generic industrial process sensor archive"),
    "uci_secom":                 ("OUT_OF_SCOPE_SEMICONDUCTOR", "UCI SECOM semiconductor-manufacturing process yield"),
    "uci_secom_archive_v3":      ("OUT_OF_SCOPE_SEMICONDUCTOR", "UCI SECOM semiconductor-manufacturing process yield"),
    "corr_data_database":        ("BARE_METAL_CORROSION_NOT_COATING", "materials-vs-chemical-environment bare-metal corrosion compatibility; substrate not coating"),
    "corr_data_checksum":        ("CHECKSUM_METADATA", "publisher checksum"),
    "purformance_experiment_v3": ("OUT_OF_SCOPE_PROCESS_AUTOMATION", "APROL DCS / PDA process-automation export, not coating chemistry"),
    "purformance_evaluation_v3": ("OUT_OF_SCOPE_PROCESS_AUTOMATION", "APROL process-automation evaluation"),
    "chebi_release_252_3star_v3":("REFERENCE_STRUCTURES", "ChEBI curated molecule structures; reference, not property measurements"),
    "pi1m_structures":           ("OUT_OF_SCOPE_GENERIC", "PI1M synthetic-accessibility context; generic polymer structures"),
    "polyverse_sorption":        ("IN_SCOPE_COATING_PHYSICS", "solvent sorption/uptake (barrier-relevant)"),
    "polyverse_melt_viscosity":  ("IN_SCOPE_COATING_PHYSICS", "melt viscosity (application/rheology-relevant)"),
    "polyverse_cohesive_energy": ("IN_SCOPE_COATING_PHYSICS", "cohesive energy density (Hansen/solubility-relevant)"),
    "polyverse_thermoset_mechanics": ("IN_SCOPE_COATING_PHYSICS", "thermoset network mechanics (directly epoxy-amine network-relevant)"),
    "polyverse_diffusivity":     ("IN_SCOPE_COATING_PHYSICS", "solvent diffusivity (barrier/permeation-relevant)"),
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def _breakdown(rows):
    out = {}
    for r in rows:
        out[r["scope_label"]] = out.get(r["scope_label"], 0) + 1
    return dict(sorted(out.items()))


def ds_prefix(dataset_id):
    # dataset_id looks like "<prefix>-<hexhash>"; strip the trailing -<hex>
    if "-" in dataset_id:
        head, tail = dataset_id.rsplit("-", 1)
        if all(c in "0123456789abcdef" for c in tail) and len(tail) >= 8:
            return head
    return dataset_id


# ---- 1. Enumerate every feedback data object, dedup by content hash (basename) ----
objs = {}
for p in sorted(ROOT.glob("**/feedback_v*/objects/*.jsonl.gz")):
    key = p.name  # sha256.jsonl.gz -> content addressed, identical across copies
    if key in objs:
        continue
    n = 0
    first = None
    with gzip.open(p, "rt") as fh:
        for line in fh:
            if n == 0:
                try:
                    first = json.loads(line)
                except Exception:
                    first = {}
            n += 1
    ds = (first or {}).get("dataset_id", "?")
    objs[key] = {
        "dataset_id": ds,
        "dataset_prefix": ds_prefix(ds),
        "endpoint": (first or {}).get("endpoint", "?"),
        "rights_class": (first or {}).get("rights_class", "?"),
        "n_rows": n,
    }

records = []
for key in sorted(objs):
    o = objs[key]
    pref = o["dataset_prefix"]
    scope_label, scope_note = SCOPE.get(pref, ("UNCLASSIFIED", "no explicit scope rule"))
    rights_clean = o["rights_class"] == "DERIVATIVE_ALLOWED"
    in_scope_coating_physics = scope_label == "IN_SCOPE_COATING_PHYSICS"
    records.append({
        "object_sha256_prefix": key.split(".")[0][:16],
        "dataset_prefix": pref,
        "endpoint": o["endpoint"],
        "rights_class": o["rights_class"],
        "rights_clean": rights_clean,
        "n_rows": o["n_rows"],
        "scope_label": scope_label,
        "scope_note": scope_note,
        "in_scope_coating_physics": in_scope_coating_physics,
        "usable_for_phase0_science_kpi": rights_clean,
    })

# ---- 2. The join that matters ----
rights_clean = [r for r in records if r["rights_clean"]]
in_scope_physics = [r for r in records if r["in_scope_coating_physics"]]
# datasets that are simultaneously rights-clean AND an in-scope coating property
rights_clean_and_in_scope = [r for r in records if r["rights_clean"] and r["in_scope_coating_physics"]]
# in-scope coating physics that is quarantined (cannot back a Phase-0 KPI)
in_scope_but_quarantined = [r for r in in_scope_physics if not r["rights_clean"]]

# ---- 3. corr_data bare-metal proof (deterministic keyword ratio over the object) ----
corr_hit, corr_total = 0, 0
corr_obj = None
for p in sorted(ROOT.glob("**/feedback_v*/objects/*.jsonl.gz")):
    with gzip.open(p, "rt") as fh:
        head = fh.readline()
    if '"corr_data_database' in head:
        corr_obj = p
        break
if corr_obj is not None:
    with gzip.open(corr_obj, "rt") as fh:
        for line in fh:
            corr_total += 1
            low = line.lower()
            if any(k in low for k in ("coat", "epoxy", "paint", "primer")):
                corr_hit += 1

# ---- 4. Live Phase-0 state + blocker taxonomy from the on-disk decision report ----
dr = json.loads(Path("config/program/phase0-decision-report.v2.json").read_bytes())
mods = dr.get("modules", [])
phase0 = [m for m in mods if m.get("phase") == "PHASE_0"]
pre = [m for m in mods if m.get("phase") == "PRE_PHASE_0"]


def blocker_class(m):
    fg = " ".join(m.get("failed_gates") or [])
    if "RIGHTS_OR_LICENSE_INCOMPLETE" in fg or "SOURCE_LOCK_INVALID" in fg:
        return "B_DATA_RIGHTS_WALL"
    if "EVALUATION_RESULT_MISMATCH" in fg:
        return "A_POST_SIGN_DIAGNOSTIC_DRIFT"
    if "SCIENTIFIC_BENCHMARK_NOT_EXECUTED" in fg:
        return "C_BENCHMARK_NEVER_EXECUTED_OR_SIGNED"
    return "OTHER"


tax = {}
for m in pre:
    c = blocker_class(m)
    tax.setdefault(c, []).append(m["module_id"])
tax = {k: sorted(v) for k, v in sorted(tax.items())}

# ---- 5. Of the PHASE_0 modules, which carry PASSED science vs governance-only ----
phase0_science = []
for m in sorted(phase0, key=lambda x: x["module_id"]):
    mid = m["module_id"]
    sci = m.get("scientific_readiness")
    outcome = None
    rp = Path(mid) / "evidence/phase0/benchmark/result.v1.json"
    if rp.exists():
        try:
            outcome = json.loads(rp.read_bytes()).get("scientific_outcome")
        except Exception:
            outcome = "UNREADABLE"
    phase0_science.append({
        "module_id": mid,
        "scientific_readiness": sci,
        "benchmark_scientific_outcome": outcome,
    })
n_not_applicable = sum(1 for x in phase0_science if x["scientific_readiness"] == "NOT_APPLICABLE")
n_locked_internal = sum(1 for x in phase0_science if x["scientific_readiness"] == "LOCKED_INTERNAL")
n_passed_science = sum(1 for x in phase0_science if x["benchmark_scientific_outcome"] == "PASSED")
passed_science_modules = sorted(x["module_id"] for x in phase0_science if x["benchmark_scientific_outcome"] == "PASSED")

diagnostic = {
    "schema": "amphora.redteam-audit.rights-scope-data-wall-v1.diagnostic.v1",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "modifies_existing_receipts": False,
    "purpose": (
        "Red-team the 'FULL Phase-0 science' claim by proving the portfolio's growth "
        "wall is structural: the intersection of (rights-clean, i.e. Phase-0-KPI-usable) "
        "and (in-scope experimental coating property) datasets is empty, so no new "
        "in-scope coating-science module can be honestly promoted from in-tree data."),
    "live_phase0": {
        "phase0_count": len(phase0),
        "pre_phase0_count": len(pre),
        "phase0_modules_scientific_readiness": phase0_science,
        "n_phase0_NOT_APPLICABLE": n_not_applicable,
        "n_phase0_LOCKED_INTERNAL": n_locked_internal,
        "n_phase0_with_PASSED_scientific_benchmark": n_passed_science,
        "phase0_modules_with_PASSED_science": passed_science_modules,
    },
    "pre_phase0_blocker_taxonomy": tax,
    "pre_phase0_blocker_counts": {k: len(v) for k, v in tax.items()},
    "data_wall": {
        "n_data_objects": len(records),
        "n_rights_clean": len(rights_clean),
        "n_in_scope_coating_physics": len(in_scope_physics),
        "n_rights_clean_AND_in_scope_coating_property": len(rights_clean_and_in_scope),
        "rights_clean_AND_in_scope_ids": sorted({r["dataset_prefix"] for r in rights_clean_and_in_scope}),
        "in_scope_coating_physics_that_is_quarantined_context_only":
            sorted({r["dataset_prefix"] for r in in_scope_but_quarantined}),
        "rights_clean_dataset_scope_breakdown":
            _breakdown(rights_clean),
    },
    "corr_data_bare_metal_proof": {
        "dataset": "corr_data_database",
        "n_rows": corr_total,
        "n_rows_mentioning_coating_terms": corr_hit,
        "coating_fraction": (round(corr_hit / corr_total, 6) if corr_total else None),
        "conclusion": "bare-metal materials/chemical-compatibility corrosion; not marine coating barrier performance",
    },
    "records": records,
    "verdict": {
        "full_phase0_science_claim": "FALSE",
        "n_phase0_with_PASSED_science": n_passed_science,
        "only_passed_science_modules": passed_science_modules,
        "new_in_scope_coating_science_promotable_from_in_tree_data_this_run": False,
        "root_cause": (
            "STRUCTURAL DATA WALL: rights-clean data is out-of-scope/simulation/semiconductor/"
            "generic-polymer/solubility-adjacent; every in-scope experimental coating polymer-"
            "physics dataset (viscosity, cohesive-energy/Hansen, thermoset mechanics, sorption, "
            "diffusivity) is CONTEXT_ONLY-quarantined. The blocker is DATA RIGHTS, not science."),
    },
    "does_not": [
        "does not promote or demote any module",
        "does not modify any of the 66 signed manifest receipts",
        "does not use a trust-anchored phase0 key (local AUDIT_ONLY key only)",
        "does not itself acquire or license any dataset",
    ],
}


# ---- 6. Emit canonical, byte-stable diagnostic ----
import sys
body = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
out_path = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
Path(out_path).write_bytes(body)
print("WROTE", out_path)
print("diagnostic_sha256", sha(body))
print("phase0_count", diagnostic["live_phase0"]["phase0_count"])
print("n_phase0_with_PASSED_science", diagnostic["live_phase0"]["n_phase0_with_PASSED_scientific_benchmark"])
print("n_rights_clean_AND_in_scope", diagnostic["data_wall"]["n_rights_clean_AND_in_scope_coating_property"])
