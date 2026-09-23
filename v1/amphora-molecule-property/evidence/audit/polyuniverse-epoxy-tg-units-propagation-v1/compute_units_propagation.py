#!/usr/bin/env python3
"""
W12 (ROTATION, amphora-molecule-property): units-correction propagation-completeness
audit for the Polyuniverse Epoxy Tg 'K'-vs-'degC' labeling error.

Prints one canonical JSON object to stdout. No randomness, no wall-clock, no
network. Deterministic given the fixed on-disk inputs.
"""
import csv
import hashlib
import json
import re
import statistics
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-property"
CSV_PATH = ROOT / "feedback/v1/external_data/polyuniverse_epoxy/raw/Epoxy_1M_p.csv"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# Step 1: independently re-derive the raw Tg column distribution from the
# pinned CSV (the same file every Polyuniverse-Epoxy-Tg KPI in this module
# cites via dataset_fixture_sha256 / input_csv_sha256).
# ---------------------------------------------------------------------------
csv_bytes = CSV_PATH.read_bytes()
csv_sha256 = sha(csv_bytes)

tg_vals = []
with open(CSV_PATH, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            tg_vals.append(float(row["Tg"]))
        except (KeyError, ValueError):
            continue

n_total = len(tg_vals)
tg_min = min(tg_vals)
tg_max = max(tg_vals)
tg_mean = statistics.mean(tg_vals)
tg_std = statistics.pstdev(tg_vals)
tg_median = statistics.median(tg_vals)

n_negative = sum(1 for v in tg_vals if v < 0.0)
n_below_140 = sum(1 for v in tg_vals if v < 140.0)  # below PDMS, the lowest-Tg common polymer
n_below_200 = sum(1 for v in tg_vals if v < 200.0)
n_at_or_above_300 = sum(1 for v in tg_vals if v >= 300.0)  # room temperature, K

example_negative = next((v for v in tg_vals if v < 0.0), None)

literal_kelvin_admissibility = {
    "rule_1_absolute_zero": {
        "statement": "T[K] >= 0 always, by definition of the Kelvin scale (no exception, no domain assumption required)",
        "n_violations": n_negative,
        "example_violation_value": example_negative,
        "violated": n_negative > 0,
    },
    "rule_2_room_temperature_sanity": {
        "statement": (
            "A cured epoxy-amine MARINE COATING network is designed to be a rigid "
            "glassy solid at ambient service temperature; essentially all real "
            "cured epoxy-amine Tg values in the literature this module already "
            "cites (May 1988 Ch.6; this module's own OpenPoly experimental Tg "
            "corpus, range [146,589] K) sit at or above ~300 K"
        ),
        "n_rows": n_total,
        "n_at_or_above_300K": n_at_or_above_300,
        "fraction_at_or_above_300K": n_at_or_above_300 / n_total,
        "violated": n_at_or_above_300 == 0,
    },
    "rule_3_below_lowest_known_polymer_Tg": {
        "statement": (
            "PDMS (polydimethylsiloxane), one of the most flexible common "
            "polymers known, has Tg ~146-150 K (Mark, J.E. ed. 2007, Physical "
            "Properties of Polymers Handbook, 2nd ed., Springer, Ch.19 Table "
            "19.1) -- among the lowest Tg of any widely-characterized polymer. "
            "A rigid, aromatic, densely-crosslinked epoxy-amine thermoset "
            "network should not read BELOW this floor."
        ),
        "n_rows": n_total,
        "n_below_140K": n_below_140,
        "fraction_below_140K": n_below_140 / n_total,
        "violated": (n_below_140 / n_total) > 0.5,
    },
}

# ---------------------------------------------------------------------------
# Step 2: cross-check against the ALREADY-DISCLOSED in-tree correction
# receipt's own claim ("n=10k sample gives mean 118, range [28, 219]; 74% >
# 100") using the SAME seed=0 / first-N-rows convention this module's other
# receipts use for reproducible sampling of this fixture. This is NOT the
# falsifying check -- it is supporting corroboration that the disclosed
# correction (Tg is really degC) is internally consistent with the raw file.
# ---------------------------------------------------------------------------
sample10k = tg_vals[:10000]
corroboration = {
    "n": len(sample10k),
    "mean": statistics.mean(sample10k),
    "min": min(sample10k),
    "max": max(sample10k),
    "fraction_above_100": sum(1 for v in sample10k if v > 100.0) / len(sample10k),
    "note": (
        "Compare to the disclosed correction receipt's own reported n=10k "
        "sample stats (mean 118, range [28,219], 74%>100) in "
        "polyuniverse_epoxy_tg_external_validation_5_canonical_epoxy_amines_"
        "receipt.v1.json / docs/mission.md 'CRITICAL HONEST FINDING -- units "
        "disclosure'. This audit takes the first 10,000 CSV rows in file "
        "order (deterministic, no RNG) rather than reproducing an undisclosed "
        "sampling method; approximate agreement corroborates that the raw "
        "column is on a degC-like scale, not K."
    ),
}

# ---------------------------------------------------------------------------
# Step 3: scan every Phase-0 KPI file that references "Polyuniverse Epoxy"
# for evidence it has (a) the corrected unit label, or (b) an explicit
# claim_lock / disclosure pointer to the correction. Classify each.
# ---------------------------------------------------------------------------
KPI_DIR = MOD / "evidence/phase0/kpis"
PINNED_CSV_SHA256 = csv_sha256  # 9f1f5c59... -- the raw mislabeled-Tg-column file
all_kpi_files = sorted(p.name for p in KPI_DIR.glob("*.json") if p.name != "RETRACTION-INDEX.md")

CORRECTION_MARKERS = [
    "not K",
    "not_K",
    "units_are_C_not_K",
    "unit interpretation",
    "units disclosure",
    "°C, not K",
]


def classify(fname):
    """In-scope = the KPI's own JSON directly pins dataset_fixture_sha256 (or
    input_csv_sha256) to the raw Epoxy_1M_p.csv fixture -- i.e. it presents
    a number computed straight from that file's mislabeled Tg column, not
    merely a downstream cross-reference to another receipt's hash or an
    unrelated dataset that happens to mention 'Polyuniverse Epoxy' in prose
    (e.g. a Phase-1 forward-pointer)."""
    path = KPI_DIR / fname
    raw = path.read_text()
    d = json.loads(raw)
    pinned = None
    for k in ("dataset_fixture_sha256", "input_csv_sha256", "input_csv_hash"):
        if d.get(k) == PINNED_CSV_SHA256:
            pinned = k
            break
    in_scope = pinned is not None
    claim_locks = d.get("claim_locks", {}) or {}
    lock_hit = [k for k in claim_locks if "unit" in k.lower() and ("c_not_k" in k.lower() or "not_k" in k.lower())]
    text_hit = [m for m in CORRECTION_MARKERS if m in raw]
    corrected = bool(lock_hit or text_hit)
    return {
        "file": fname,
        "sha256": sha(path.read_bytes()),
        "directly_pins_raw_mislabeled_csv_fixture": in_scope,
        "pinning_field": pinned,
        "correction_claim_lock_hit": lock_hit,
        "correction_text_marker_hit": text_hit,
        "classified_corrected": corrected,
    }


audit_rows = [classify(f) for f in all_kpi_files]

# In-scope for the propagation check = KPIs whose OWN JSON directly pins the
# raw mislabeled-Tg-column CSV as their dataset_fixture_sha256 / input_csv_sha256
# (unambiguous shared provenance to the defect -- not a text/regex heuristic).
in_scope = [r for r in audit_rows if r["directly_pins_raw_mislabeled_csv_fixture"]]
non_compliant = [r for r in in_scope if not r["classified_corrected"]]
compliant = [r for r in in_scope if r["classified_corrected"]]

# ---------------------------------------------------------------------------
# Step 4: positive-control-style discriminating-power check (not required for
# a REFUTED verdict, included anyway): does the detector correctly recognize
# a KNOWN-corrected KPI as corrected, rather than flagging everything?
# ---------------------------------------------------------------------------
known_corrected_file = "coating-candidate-design-card-5-canonical-epoxy-amines-kpi.v1.json"
known_corrected_row = next((r for r in audit_rows if r["file"] == known_corrected_file), None)
detector_discriminates = bool(known_corrected_row and known_corrected_row["classified_corrected"])

result = {
    "claim_under_attack": {
        "description": (
            "The module's Polyuniverse-Epoxy-Tg-family Phase-0 KPI receipts "
            "consistently and correctly label the underlying MD-simulated Tg "
            "target's physical units, OR any correction to a prior mislabel "
            "has been propagated to every consuming KPI surface per this "
            "module's own supersede-never-rewrite / RETRACTION-INDEX "
            "discipline (established precedent: W3, 2026-08-02, dielectric-"
            "retraction propagation, verdict REFUTED)."
        ),
        "primary_kpi_path": "amphora-molecule-property/evidence/phase0/kpis/polyuniverse-epoxy-tg-conformal-coverage-and-applicability-domain-kpi.v1.json",
        "primary_kpi_target_claim": "marginal_conformal_coverage_at_alpha_010_meets_target observed 0.9049 (target >=0.90), 10,279 scaffold-safe held-out test polymers, population described as 'MD-simulated Tg (K)'",
    },
    "dataset_fixture": {
        "path": "feedback/v1/external_data/polyuniverse_epoxy/raw/Epoxy_1M_p.csv",
        "sha256": csv_sha256,
        "matches_kpi_pinned_dataset_fixture_sha256_9f1f5c59": csv_sha256 == "9f1f5c593463b9c26a026948901e37b4db545d17f05d5cd80baca5c3e14e0c45",
    },
    "raw_tg_column_full_corpus_stats": {
        "n": n_total,
        "min": tg_min,
        "max": tg_max,
        "mean": tg_mean,
        "median": tg_median,
        "std": tg_std,
    },
    "literal_kelvin_admissibility": literal_kelvin_admissibility,
    "corroboration_of_disclosed_correction": corroboration,
    "propagation_audit": {
        "files_scanned": len(audit_rows),
        "rows": audit_rows,
        "in_scope_presents_absolute_value": len(in_scope),
        "compliant_count": len(compliant),
        "non_compliant_count": len(non_compliant),
        "non_compliant_files": [r["file"] for r in non_compliant],
        "compliant_files": [r["file"] for r in compliant],
    },
    "detector_discriminating_power_check": {
        "probe_file": known_corrected_file,
        "expected": "classified_corrected == True (this KPI carries an explicit units claim_lock)",
        "observed_classified_corrected": bool(known_corrected_row["classified_corrected"]) if known_corrected_row else None,
        "detector_discriminates": detector_discriminates,
    },
    "falsifying_check": {
        "pre_registered_refute_criterion": (
            "If any Phase-0 KPI receipt under evidence/phase0/kpis/ presents "
            "an absolute Polyuniverse-Epoxy-Tg numeric value (y_stats mean/"
            "min/max, RMSE/MAE in 'K', or a raw group-contribution physical-"
            "baseline prediction) WITHOUT either the corrected degC unit "
            "label or an explicit claim_lock/text pointer to the known "
            "K-vs-degC correction, the propagation-completeness claim is "
            "REFUTED for that file."
        ),
        "refuted": len(non_compliant) > 0,
        "n_non_compliant": len(non_compliant),
    },
}

print(json.dumps(result, indent=2, sort_keys=True))
