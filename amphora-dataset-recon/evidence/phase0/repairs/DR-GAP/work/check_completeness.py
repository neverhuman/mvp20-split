#!/usr/bin/env python3
"""Independent completeness checker for the DR-GAP gap register.

Attack shape (per the DR-GAP campaign item): re-derive, from scratch and
without importing build_register.py, the set of sources the register claims
to cover, and test whether the register's own refutation criterion fires.

refutation_criterion (restated verbatim from the campaign item):
"Any gap row lacks one of the four mandated statements, or a data ask live in
the queue at the register's snapshot date, a promotion blocker naming a
dataset, or a MODELED or ASSUMED recipe element published before that
snapshot is absent from the register."

This script is run three times over three different inputs:
  1. the real gap-register.v1.json                       -> must NOT fire
  2. a copy with one queue-derived row deleted            -> MUST fire (positive control A)
  3. a copy with one mandated fact blanked on another row -> MUST fire (positive control B)
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MISSION_GLOB = "amphora-*/docs/mission.md"
MANDATED_FACT_KEYS = [
    "missing_measurement_or_label_class",
    "minimum_n",
    "measurement_standard",
    "qualifying_dataset_requirements",
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def independent_queue_line_shas():
    """Re-read the queue snapshot independently; return set of line sha256."""
    p = ROOT / "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/data-acquisition-queue.snapshot.jsonl"
    lines = [l for l in p.read_text().splitlines() if l.strip()]
    return {sha(l.encode()) for l in lines}, len(lines)


def independent_pre_tier0_modules():
    """Re-derive Pre-Tier-0 module set from scratch by re-parsing every
    mission.md front-matter JSON line directly (no reuse of build_register.py
    logic or its hardcoded PROMOTION_BLOCKERS list)."""
    found = set()
    for f in sorted(ROOT.glob(MISSION_GLOB)):
        text = f.read_text()
        # front-matter is the first '{...}' line
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("{") and '"phase"' in line:
                try:
                    fm = json.loads(line)
                except Exception:
                    continue
                if fm.get("phase") == "PRE_PHASE_0":
                    mod_id = fm.get("module_id") or f.parent.parent.name
                    found.add(mod_id)
                break
    return found


def check(register, label):
    fired_reasons = []

    # (a) every mandated fact present and non-empty on every row
    for row in register["rows"]:
        for k in MANDATED_FACT_KEYS:
            v = row.get(k)
            if not isinstance(v, str) or not v.strip():
                fired_reasons.append(
                    f"row {row.get('row_id', '?')} missing/empty mandated fact '{k}'"
                )

    # (b) every independently-derived queue line is represented
    queue_shas, queue_n = independent_queue_line_shas()
    register_queue_shas = {
        r["source_ref"]["queue_line_sha256"]
        for r in register["rows"]
        if r.get("source_type") == "data_acquisition_queue_ask"
    }
    missing_queue = queue_shas - register_queue_shas
    for m in sorted(missing_queue):
        fired_reasons.append(f"queue line sha256={m[:16]}... absent from register")

    # (c) every independently-derived Pre-Tier-0 module is represented
    pre_tier0 = independent_pre_tier0_modules()
    register_blocker_modules = {
        r["module"]
        for r in register["rows"]
        if r.get("source_type") == "pre_tier0_promotion_blocker+lab_in_the_loop_spec"
    }
    missing_modules = pre_tier0 - register_blocker_modules
    for m in sorted(missing_modules):
        fired_reasons.append(f"Pre-Tier-0 module '{m}' promotion blocker absent from register")

    # (d) MODELED/ASSUMED recipe-element category present (even if empty-set)
    mare = register.get("modeled_assumed_recipe_elements")
    if not mare or "attestation" not in mare:
        fired_reasons.append("MODELED/ASSUMED recipe-element category (row R01) absent or malformed")

    fired = len(fired_reasons) > 0
    result = {
        "label": label,
        "refutation_criterion_fired": fired,
        "reasons": fired_reasons,
        "independent_queue_line_count": queue_n,
        "independent_pre_tier0_module_count": len(pre_tier0),
        "independent_pre_tier0_modules": sorted(pre_tier0),
        "register_total_rows": len(register["rows"]),
    }
    return result


def load(p):
    return json.loads(Path(p).read_text())


def main():
    real_path = ROOT / "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/gap-register.v1.json"
    real = load(real_path)
    real_result = check(real, "REAL_REGISTER")

    # --- positive control A: delete one queue-derived row ---
    mutA = json.loads(json.dumps(real))  # deep copy
    victim = next(r for r in mutA["rows"] if r["row_id"] == "Q07")
    mutA["rows"] = [r for r in mutA["rows"] if r["row_id"] != "Q07"]
    mutA_path = ROOT / "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/gap-register.mutantA_deleted_row.v1.json"
    mutA_path.write_text(json.dumps(mutA, indent=2, sort_keys=True))
    mutA_result = check(mutA, "MUTANT_A_DELETED_ROW_Q07")

    # --- positive control B: blank one mandated fact on another row ---
    mutB = json.loads(json.dumps(real))
    for r in mutB["rows"]:
        if r["row_id"] == "B05":
            r["qualifying_dataset_requirements"] = ""
    mutB_path = ROOT / "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/gap-register.mutantB_blanked_fact.v1.json"
    mutB_path.write_text(json.dumps(mutB, indent=2, sort_keys=True))
    mutB_result = check(mutB, "MUTANT_B_BLANKED_FACT_B05")

    out = {
        "schema": "amphora.dataset-recon.dr-gap-completeness-diagnostic.v1",
        "refutation_criterion_verbatim": (
            "Any gap row lacks one of the four mandated statements, or a data ask "
            "live in the queue at the register's snapshot date, a promotion "
            "blocker naming a dataset, or a MODELED or ASSUMED recipe element "
            "published before that snapshot is absent from the register."
        ),
        "real_register": real_result,
        "mutant_a_deleted_row": mutA_result,
        "mutant_b_blanked_fact": mutB_result,
        "real_register_sha256": sha(real_path.read_bytes()),
        "mutant_a_sha256": sha(mutA_path.read_bytes()),
        "mutant_b_sha256": sha(mutB_path.read_bytes()),
        "deleted_row_victim_row_id": victim["row_id"],
        "deleted_row_victim_module": victim["module"],
    }
    print(json.dumps(out, indent=2, sort_keys=True))

    # sanity assertions -- fail loudly if the checker is vacuous
    assert real_result["refutation_criterion_fired"] is False, "REAL register unexpectedly fired -- true refutation, not a checker bug"
    assert mutA_result["refutation_criterion_fired"] is True, "positive control A did NOT fire -- checker is vacuous"
    assert mutB_result["refutation_criterion_fired"] is True, "positive control B did NOT fire -- checker is vacuous"
    return out


if __name__ == "__main__":
    result = main()
    diag_path = ROOT / "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/diagnostic.canonical.json"
    diag_path.write_text(json.dumps(result, indent=2, sort_keys=True))
    print("WROTE", diag_path, file=sys.stderr)
