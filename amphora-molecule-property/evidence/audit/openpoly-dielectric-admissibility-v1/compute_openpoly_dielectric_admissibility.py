#!/usr/bin/env python3
"""
ROTATION fire (amphora-molecule-property, no campaign item): physical-admissibility
audit of the OpenPoly dielectric-constant labels feeding
evidence/phase0/kpis/openpoly-dielectric-constant-ml-baseline-kpi.v1.json.

Claim under attack: this KPI's headline "REAL POSITIVE LIFT" claim (RandomForest
scaffold-safe holdout test MAE=0.4040 vs NULL 0.7027, +42.5%; LOSO-CV R2=+0.659),
which is a STANDS claim per RETRACTION-INDEX.md R-A09 ("none - no refuting receipt
targets this KPI") and has NEVER been targeted by any ledger-recorded attack
(grepped logs/falsification-ledger.jsonl module=amphora-molecule-property: zero
hits for this KPI id). This module's OWN established falsification methodology
(C8 fires 1-3, W2 fires 1-3: eps_static>=n^2 Frohlich/Maxwell physical-admissibility
audit) has so far only ever been applied to RadonPy-derived dielectric corpora
(PI1070, polyomics_small_molecules), where it found severe violations (89.5% and
39.2% respectively). It has never been applied to THIS KPI's own OpenPoly source
labels, despite W2's own receipt listing this exact KPI id in its
dependent_module_kpis for the (different) openpoly_properties Tg/Tm violation.

Novel opportunity this fire exploits: the raw OpenPoly CSV
(feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv,
sha256 8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3 -- the EXACT
dataset_fixture_sha256 pinned in the target KPI) carries a per-polymer physical
decomposition never before mined for admissibility: "Dielectric Constant Total",
"Dielectric Constant Electronic", "Dielectric Constant Ionic" (295/295 rows with
all three present), plus an independent "Refractive Index" column (148 rows).

Pre-registered refute criteria (set BEFORE computing anything below, mirroring
this module's established falsification methodology, same style as C8/W2/W8):
  R1. Ionic dielectric contribution physically must be >= 0 (Frohlich, H.,
      "Theory of Dielectrics", Oxford Univ. Press, 1949, Ch.2 -- static
      permittivity sums non-negative electronic + ionic/atomic + orientational
      polarization contributions; a negative ionic contribution is inadmissible
      for a passive linear dielectric).
  R2. Electronic dielectric contribution physically must be >= 1 (Maxwell
      relation eps_inf = n^2, and n>=1 by definition of phase velocity
      v=c/n<=c -- same citation basis as this module's own W2 corpus-
      admissibility-audit-receipt.v1.dsse.json Lorentz-Lorenz check).
  R3. Total must equal Electronic + Ionic within a 0.011 tolerance (the source
      CSV rounds each field independently to 2 decimals, so two independent
      roundings can compound to +/-0.01 by construction -- 0.011 is the
      physical tolerance plus float-representation epsilon, not a loosened
      bound). This additive decomposition is the Clausius-Mossotti / Frohlich
      polarization-mechanism split, and is explicitly cited in the TARGET
      KPI's OWN "theory" field ("Clausius-Mossotti 1879 relation").
  R4. Standalone Refractive Index (independent column, 148/295 rows) must be
      >= 1 (Lorentz-Lorenz, H.A. Lorentz 1880 / L. Lorenz 1880 -- identical
      citation basis W2 already used for RadonPy's refractive-index axis).
  If >=1 row violates ANY of R1-R4, the corpus is NOT physically admissible and
  the KPI's ground-truth labels inherit the same defect class already found to
  invalidate the RadonPy dielectric corpora (C8/W2), which would REFUTE the
  KPI's "REAL POSITIVE LIFT" claim as resting on admissible ground truth.
  If 0 rows violate all four checks, the claim SURVIVES this specific physical-
  admissibility attack (a genuinely falsifying attack that found real violations
  on the sibling RadonPy corpora, applied here for the first time to OpenPoly).
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
CSV_PATH = ROOT / "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
KPI_PATH = ROOT / "amphora-molecule-property/evidence/phase0/kpis/openpoly-dielectric-constant-ml-baseline-kpi.v1.json"

TOTAL_ADDITIVITY_TOL = 0.011


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fnum(x):
    if x is None:
        return None
    x = x.strip()
    if x == "":
        return None
    try:
        return float(x)
    except ValueError:
        return None


def load_rows(csv_bytes):
    import io
    text = csv_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def audit(rows):
    """Apply R1-R4 to a list of CSV row dicts. Returns diagnostic dict.
    Pure function of `rows` -- deterministic, no I/O, so it can be re-run
    verbatim against both the real CSV and a corrupted copy (positive control)."""
    diel_recs = []
    for row in rows:
        tot = fnum(row.get("Dielectric Constant Total"))
        elec = fnum(row.get("Dielectric Constant Electronic"))
        ion = fnum(row.get("Dielectric Constant Ionic"))
        if tot is None or elec is None or ion is None:
            continue
        diel_recs.append({"name": row.get("Name"), "total": tot, "electronic": elec, "ionic": ion})

    ri_recs = []
    for row in rows:
        ri = fnum(row.get("Refractive Index"))
        if ri is None:
            continue
        ri_recs.append({"name": row.get("Name"), "refractive_index": ri})

    r1_violations = [r for r in diel_recs if r["ionic"] < 0]
    r2_violations = [r for r in diel_recs if r["electronic"] < 1.0]
    r3_violations = [
        {**r, "abs_diff": abs(r["total"] - (r["electronic"] + r["ionic"]))}
        for r in diel_recs
        if abs(r["total"] - (r["electronic"] + r["ionic"])) > TOTAL_ADDITIVITY_TOL
    ]
    r4_violations = [r for r in ri_recs if r["refractive_index"] < 1.0]

    return {
        "n_dielectric_triplet_rows": len(diel_recs),
        "n_refractive_index_rows": len(ri_recs),
        "R1_ionic_non_negative": {
            "n_checked": len(diel_recs),
            "n_violations": len(r1_violations),
            "violations": r1_violations[:20],
            "passed": len(r1_violations) == 0,
        },
        "R2_electronic_geq_1": {
            "n_checked": len(diel_recs),
            "n_violations": len(r2_violations),
            "violations": r2_violations[:20],
            "passed": len(r2_violations) == 0,
        },
        "R3_total_equals_electronic_plus_ionic": {
            "n_checked": len(diel_recs),
            "n_violations": len(r3_violations),
            "tolerance": TOTAL_ADDITIVITY_TOL,
            "violations": r3_violations[:20],
            "passed": len(r3_violations) == 0,
        },
        "R4_refractive_index_geq_1": {
            "n_checked": len(ri_recs),
            "n_violations": len(r4_violations),
            "violations": r4_violations[:20],
            "passed": len(r4_violations) == 0,
        },
        "all_checks_passed": (
            len(r1_violations) == 0 and len(r2_violations) == 0
            and len(r3_violations) == 0 and len(r4_violations) == 0
        ),
    }


def corrupt_rows(rows):
    """Positive control: plant defects of the SAME KIND the audit exists to
    catch, on a COPY of the real rows, and confirm the detector fires.
    5 distinct defect types, one per class of physical/definitional bound
    this audit checks, planted on rows that were clean in the real data."""
    import copy
    rows = copy.deepcopy(rows)
    diel_idx = [i for i, r in enumerate(rows) if fnum(r.get("Dielectric Constant Total")) is not None]
    ri_idx = [i for i, r in enumerate(rows) if fnum(r.get("Refractive Index")) is not None]

    planted = []

    # Defect 1 (R1): flip ionic contribution negative on 3 rows.
    for i in diel_idx[:3]:
        before = rows[i]["Dielectric Constant Ionic"]
        rows[i]["Dielectric Constant Ionic"] = str(-abs(fnum(before)))
        planted.append({"row_name": rows[i]["Name"], "field": "Dielectric Constant Ionic",
                         "before": before, "after": rows[i]["Dielectric Constant Ionic"], "targets": "R1"})

    # Defect 2 (R2): set electronic contribution below 1 on 3 rows.
    for i in diel_idx[3:6]:
        before = rows[i]["Dielectric Constant Electronic"]
        rows[i]["Dielectric Constant Electronic"] = "0.5"
        planted.append({"row_name": rows[i]["Name"], "field": "Dielectric Constant Electronic",
                         "before": before, "after": "0.5", "targets": "R2"})

    # Defect 3 (R3): break additivity by a large delta (+5.0) on 3 rows.
    for i in diel_idx[6:9]:
        before = rows[i]["Dielectric Constant Total"]
        rows[i]["Dielectric Constant Total"] = str(fnum(before) + 5.0)
        planted.append({"row_name": rows[i]["Name"], "field": "Dielectric Constant Total",
                         "before": before, "after": rows[i]["Dielectric Constant Total"], "targets": "R3"})

    # Defect 4 (R4): set refractive index below 1 (physically impossible) on 3 rows.
    for i in ri_idx[:3]:
        before = rows[i]["Refractive Index"]
        rows[i]["Refractive Index"] = "0.8"
        planted.append({"row_name": rows[i]["Name"], "field": "Refractive Index",
                         "before": before, "after": "0.8", "targets": "R4"})

    return rows, planted


def main():
    csv_bytes = CSV_PATH.read_bytes()
    csv_sha256 = sha(csv_bytes)
    kpi_bytes = KPI_PATH.read_bytes()
    kpi = json.loads(kpi_bytes)

    rows = load_rows(csv_bytes)

    # Run 1 (real data)
    real_result_a = audit(rows)
    # Run 2 (byte-stability replay of the identical computation)
    real_result_b = audit(rows)
    real_two_replay_identical = json.dumps(real_result_a, sort_keys=True) == json.dumps(real_result_b, sort_keys=True)

    # Positive control: corrupted copy
    corrupted_rows, planted_defects = corrupt_rows(rows)
    corrupted_result = audit(corrupted_rows)

    # Per-planted-defect detection check: each planted defect must be caught
    # by its OWN targeted rule (R1/R2/R3/R4). Note the R1 (ionic->negative)
    # and R2 (electronic->0.5) defects mechanically ALSO break R3 additivity
    # for those same rows (only one component was mutated, not the total) --
    # that cross-triggering is physically correct, not double-counting, so
    # detection is checked per-defect (by name), not by requiring rule counts
    # to stay independent.
    rule_violation_names = {
        "R1": {v["name"] for v in corrupted_result["R1_ionic_non_negative"]["violations"]},
        "R2": {v["name"] for v in corrupted_result["R2_electronic_geq_1"]["violations"]},
        "R3": {v["name"] for v in corrupted_result["R3_total_equals_electronic_plus_ionic"]["violations"]},
        "R4": {v["name"] for v in corrupted_result["R4_refractive_index_geq_1"]["violations"]},
    }
    per_defect_detection = []
    for d in planted_defects:
        caught = d["row_name"] in rule_violation_names[d["targets"]]
        per_defect_detection.append({**d, "caught_by_targeted_rule": caught})
    observed_violations = {k: len(v) for k, v in rule_violation_names.items()}
    expected_violations = {"R1": 3, "R2": 3, "R3": 9, "R4": 3}  # R3=9: 3 own + 3 cross-triggered by R1 + 3 cross-triggered by R2
    positive_control_all_detected = (
        all(d["caught_by_targeted_rule"] for d in per_defect_detection)
        and observed_violations == expected_violations
    )

    diagnostic = {
        "claim_under_attack": {
            "kpi_path": "amphora-molecule-property/evidence/phase0/kpis/openpoly-dielectric-constant-ml-baseline-kpi.v1.json",
            "kpi_sha256": sha(kpi_bytes),
            "kpi_id": kpi["kpi_id"],
            "capability_text": kpi["capability"],
        },
        "dataset_fixture_sha256_observed": csv_sha256,
        "dataset_fixture_sha256_pinned_in_kpi": kpi["dataset_fixture_sha256"],
        "dataset_fixture_sha256_match": csv_sha256 == kpi["dataset_fixture_sha256"],
        "n_csv_rows_total": len(rows),
        "real_data_audit": real_result_a,
        "real_data_two_replay_byte_identical": real_two_replay_identical,
        "positive_control": {
            "planted_defects": planted_defects,
            "per_defect_detection": per_defect_detection,
            "corrupted_data_audit": corrupted_result,
            "expected_violations_per_rule": expected_violations,
            "observed_violations_per_rule": observed_violations,
            "all_planted_defects_detected": positive_control_all_detected,
        },
        "pre_registered_refute_criterion": (
            "If >=1 row violates R1 (ionic>=0), R2 (electronic>=1), R3 "
            "(total==electronic+ionic within 0.011), or R4 (refractive_index>=1) "
            "on the REAL data, the KPI's ground-truth dielectric labels are "
            "physically inadmissible and the claim is REFUTED. If 0 rows "
            "violate all four on real data AND the positive control (12 "
            "planted defects, 3 per rule) is fully detected on the corrupted "
            "copy, the claim SURVIVES this attack."
        ),
        "verdict": "SURVIVED" if (real_result_a["all_checks_passed"] and positive_control_all_detected) else "REFUTED",
    }
    return diagnostic


if __name__ == "__main__":
    diag = main()
    out_path = Path(__file__).parent / "diagnostic.out.json"
    out_path.write_text(json.dumps(diag, indent=2, sort_keys=True))
    print(json.dumps({k: v for k, v in diag.items() if k not in ("real_data_audit", "positive_control")}, indent=2))
    print("verdict:", diag["verdict"])
