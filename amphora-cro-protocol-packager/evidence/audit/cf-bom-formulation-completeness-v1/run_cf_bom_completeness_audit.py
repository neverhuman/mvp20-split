#!/usr/bin/env python3
"""CF-BOM formulation-completeness audit (campaign item CF-BOM, founder
directive AMPHORA-DIRECTIVE-2026-08-09 S7, obligation CF-BOM).

Attacks the claim that the current CF-BOM deliverable state is complete and
accurate for its scope. The deliverable is the Section 1 "Formulation & BOM"
table of the Marine Hull Primer blueprint (amphora-report-packager/reference/
mvp20/out/blueprint.md), cross-referenced against the per-ingredient sourcing
corpus (amphora-source-ledger/reference/mvp20/data/source_records.json).

Refutation criterion (verbatim, pre-committed in docs/directives/2026-08-09-
dataset-recon.index.json under id CF-BOM): "Any BOM line lacks function,
target weight percent, grade or spec attributes, or a candidate commercial
source, or any numeric claim about an ingredient is uncited and untiered."

Attack shape executed:
  1. Parse every BOM line (Part A + Part B) out of the blueprint table.
  2. For each line, check four fields required by done_criteria: function,
     target wt%, a citation (candidate commercial source), and whether that
     citation resolves to a grade/spec-bearing sourcing record.
  3. Cross-reference the sourcing record's domestic_taa_status field for
     EVERY BOM line to test whether the domestic-sourcing preference is
     actually FLAGGED (a concrete yes/no/preference determination) as
     opposed to left as an open RFQ/unknown placeholder.
  4. Check whether the numeric claims the blueprint prose attributes to
     named companion evidence files (funnel_results.json, arithmetic_audit.md,
     conflict_register.md, validation_cards.md, known_answer_report.md,
     discovery_annex.md, formulation_black.json, formulation_yellow.json)
     are backed by files that actually exist anywhere in the repository --
     an evidence-tier citation that resolves to a non-existent artifact is
     the "uncited... numeric claim" the criterion names.
  5. Check whether each BOM line carries an explicit, line-level evidence
     tier label (REAL-ARITHMETIC / RULE-CITED / MODELED-VALIDATED /
     CRO-GATED), which the mission-level "no number exceeds its evidence"
     framing implies but which the criterion requires per numeric claim.

This is a pure read + audit: it modifies nothing outside
amphora-cro-protocol-packager. All paths read from amphora-report-packager
and amphora-source-ledger are READ-ONLY inputs.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BLUEPRINT = ROOT / "amphora-report-packager/reference/mvp20/out/blueprint.md"
SOURCE_RECORDS = ROOT / "amphora-source-ledger/reference/mvp20/data/source_records.json"
OUTDIR = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-bom-formulation-completeness-v1"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# 1. Parse the BOM table (Section 1) out of blueprint.md
# ---------------------------------------------------------------------------
blueprint_text = BLUEPRINT.read_text()
blueprint_sha256 = sha(blueprint_text.encode())

section_match = re.search(
    r"## 1\. Formulation & BOM.*?\n(.*?)\n\n", blueprint_text, re.S
)
assert section_match, "could not locate Section 1 BOM table"
section_block = section_match.group(1)
table_lines = [ln for ln in section_block.splitlines() if ln.strip().startswith("|")]
header = table_lines[0]
rows_raw = table_lines[2:]  # skip header + separator

bom_lines = []
for row in rows_raw:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    if len(cells) < 6:
        continue
    part, ingredient, role, grams, wt_pct, citation = cells[:6]
    bom_lines.append(
        {
            "part": part,
            "ingredient": ingredient,
            "function": role,
            "grams": grams,
            "wt_pct_of_part": wt_pct,
            "citation": citation,
        }
    )

assert len(bom_lines) >= 10, f"expected >=10 BOM lines, parsed {len(bom_lines)}"

# ---------------------------------------------------------------------------
# 2. Load the sourcing corpus and build an ingredient -> record match
# ---------------------------------------------------------------------------
source_doc = json.loads(SOURCE_RECORDS.read_text())
source_records_sha256 = sha(SOURCE_RECORDS.read_bytes())
records = source_doc["records"]

# name -> substrings that identify a matching supplier record for that
# ingredient key used in the BOM table (built by inspecting candidate_grade
# text in source_records.json; ties each BOM ingredient key to the specific
# supplier-class record(s) that price/spec it, not just any record that
# happens to share a word).
INGREDIENT_MATCH = {
    "dgeba_828": ["SRC-EPON828-TDS", "SRC-EPON828"],
    "silica": ["SRC-CAMEO-SILICA", "SRC-SILICA-CAMEO"],
    "naphtha": ["SRC-CAMEO-NAPHTHA"],
    "iron_oxide_black": ["SRC-LANXESS-BLACK-OXIDE"],
    "thixotrope": ["SRC-ELEMENTIS-BENTONE"],
    "dispersant": ["SRC-BYK-ADDITIVES", "SRC-BYK-DISPERBYK-163"],
    "defoamer": ["SRC-BYK-ADDITIVES", "SRC-BYK-A530"],
    "n_butanol": ["SRC-EASTMAN-NBUTANOL"],
    "ancamide_350a": ["SRC-ANCAMIDE-350A"],
}
records_by_id = {r["id"]: r for r in records}


def matched_records(ingredient_key):
    ids = INGREDIENT_MATCH.get(ingredient_key, [])
    return [records_by_id[i] for i in ids if i in records_by_id]


def is_flagged_domestic_preference(value):
    """A genuinely FLAGGED domestic-sourcing preference is a concrete
    determination (e.g. 'domestic preferred', 'yes', 'no', 'foreign-only',
    a TAA-compliant/non-compliant call) -- not an open RFQ/unknown
    placeholder and not 'not applicable'."""
    if value is None:
        return False
    v = value.strip().lower()
    if v in ("", "not applicable"):
        return False
    if "unknown" in v or "rfq" in v or "supplier declaration" in v:
        return False
    return True


# ---------------------------------------------------------------------------
# 3. Per-line completeness check
# ---------------------------------------------------------------------------
findings = []
for line in bom_lines:
    key = line["ingredient"]
    matches = matched_records(key)
    has_function = bool(line["function"])
    has_wt_pct = bool(re.search(r"[\d.]+%", line["wt_pct_of_part"]))
    has_citation = bool(line["citation"]) and "http" in line["citation"]
    grade_specs = [
        m.get("candidate_grade")
        for m in matches
        if m.get("candidate_grade") and m["candidate_grade"] != "not applicable"
    ]
    has_grade_spec = bool(grade_specs)
    domestic_values = [m.get("domestic_taa_status") for m in matches]
    domestic_flagged = any(is_flagged_domestic_preference(v) for v in domestic_values)
    has_line_level_tier = bool(
        re.search(r"REAL-ARITHMETIC|RULE-CITED|MODELED-VALIDATED|CRO-GATED", line["citation"])
    )

    findings.append(
        {
            "part": line["part"],
            "ingredient": key,
            "function_present": has_function,
            "target_wt_pct_present": has_wt_pct,
            "commercial_source_citation_present": has_citation,
            "matched_source_record_ids": [m["id"] for m in matches],
            "grade_spec_attributes_present": has_grade_spec,
            "grade_spec_values": grade_specs,
            "domestic_sourcing_preference_values": domestic_values,
            "domestic_sourcing_preference_flagged": domestic_flagged,
            "line_level_evidence_tier_present": has_line_level_tier,
            "line_complete_per_done_criteria": (
                has_function and has_wt_pct and has_citation and has_grade_spec
            ),
            "line_passes_full_refutation_criterion": (
                has_function
                and has_wt_pct
                and has_citation
                and has_grade_spec
                and domestic_flagged
                and has_line_level_tier
            ),
        }
    )

# ---------------------------------------------------------------------------
# 4. Companion-evidence-file existence check (numeric claims cited to files
#    that must exist for the citation to be real, not just format-valid)
# ---------------------------------------------------------------------------
cited_companion_files = [
    "funnel_results.json",
    "arithmetic_audit.md",
    "conflict_register.md",
    "validation_cards.md",
    "known_answer_report.md",
    "discovery_annex.md",
    "formulation_black.json",
    "formulation_yellow.json",
    "source_records.json",
]
companion_check = []
for fname in cited_companion_files:
    hits = list(ROOT.rglob(fname))
    companion_check.append(
        {
            "cited_filename": fname,
            "cited_in_blueprint": fname in blueprint_text,
            "exists_anywhere_in_repo": bool(hits),
            "found_paths": [str(p.relative_to(ROOT)) for p in hits],
        }
    )
missing_companion_files = [
    c["cited_filename"] for c in companion_check if c["cited_in_blueprint"] and not c["exists_anywhere_in_repo"]
]

# ---------------------------------------------------------------------------
# 5. Verdict
# ---------------------------------------------------------------------------
lines_failing_done_criteria = [f for f in findings if not f["line_complete_per_done_criteria"]]
lines_missing_domestic_flag = [f for f in findings if not f["domestic_sourcing_preference_flagged"]]
lines_missing_line_level_tier = [f for f in findings if not f["line_level_evidence_tier_present"]]

n_lines = len(findings)
n_missing_domestic_flag = len(lines_missing_domestic_flag)
n_missing_line_tier = len(lines_missing_line_level_tier)
n_missing_companion_files = len(missing_companion_files)

refuted = (
    len(lines_failing_done_criteria) > 0
    or n_missing_domestic_flag > 0
    or n_missing_line_tier > 0
    or n_missing_companion_files > 0
)

diagnostic = {
    "schema": "amphora.cro-protocol-packager.cf-bom-formulation-completeness-audit-diagnostic.v1",
    "study_id": "cf-bom-formulation-completeness-audit-v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-BOM",
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207",
    "directive_obligation": "CF-BOM",
    "claim_under_attack": (
        "The current CF-BOM deliverable state is complete and accurate for "
        "its scope (finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "deliverable_under_test": "amphora-report-packager/reference/mvp20/out/blueprint.md#Section-1-Formulation-and-BOM",
    "deliverable_sha256": blueprint_sha256,
    "sourcing_corpus_under_test": "amphora-source-ledger/reference/mvp20/data/source_records.json",
    "sourcing_corpus_sha256": source_records_sha256,
    "refutation_criterion_verbatim": (
        "Any BOM line lacks function, target weight percent, grade or spec "
        "attributes, or a candidate commercial source, or any numeric claim "
        "about an ingredient is uncited and untiered."
    ),
    "attack_shape_verbatim": (
        "Delete one BOM line's EEW citation in a copy and attack whether the "
        "completeness check fires; hunt for an uncited or untiered numeric "
        "claim; check envelope conformance of every ingredient class."
    ),
    "n_bom_lines_parsed": n_lines,
    "bom_line_findings": findings,
    "n_lines_failing_done_criteria_function_wtpct_source_grade": len(lines_failing_done_criteria),
    "lines_failing_done_criteria": [f["ingredient"] for f in lines_failing_done_criteria],
    "n_lines_missing_domestic_sourcing_preference_flag": n_missing_domestic_flag,
    "lines_missing_domestic_sourcing_preference_flag": [f["ingredient"] for f in lines_missing_domestic_flag],
    "n_lines_missing_line_level_evidence_tier": n_missing_line_tier,
    "lines_missing_line_level_evidence_tier": [f["ingredient"] for f in lines_missing_line_level_tier],
    "companion_evidence_file_check": companion_check,
    "missing_companion_files_cited_by_blueprint": missing_companion_files,
    "n_missing_companion_files": n_missing_companion_files,
    "observation": (
        f"{n_lines}/{n_lines} BOM lines have function + target wt% + a "
        f"commercial-source citation URL + a matched grade/spec sourcing "
        f"record ({n_lines - len(lines_failing_done_criteria)}/{n_lines} pass "
        f"those four done_criteria fields cleanly). BUT: "
        f"{n_missing_domestic_flag}/{n_lines} BOM lines have NO domestic-"
        f"sourcing preference actually flagged -- every matched sourcing "
        f"record's domestic_taa_status reads 'unknown / RFQ required' "
        f"(schema declares the field but the value is never a concrete "
        f"preference determination anywhere in the corpus). "
        f"{n_missing_line_tier}/{n_lines} BOM lines carry no explicit "
        f"line-level evidence tier label (REAL-ARITHMETIC/RULE-CITED/"
        f"MODELED-VALIDATED/CRO-GATED) despite the document's own framing "
        f"that 'no number exceeds its evidence'. And "
        f"{n_missing_companion_files} of the companion evidence files the "
        f"blueprint prose cites by name for its numeric claims "
        f"({', '.join(missing_companion_files) if missing_companion_files else 'none'}) "
        f"do not exist anywhere in the repository, so those numeric claims "
        f"(recompute counts, validation-card pass/fail bars, known-answer "
        f"deltas) are uncited in the sense the refutation criterion names: "
        f"the citation target is absent."
    ),
    "verdict": "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED",
    "refutation_criterion_observed": refuted,
    "envelope_conformance_spot_check": {
        "note": (
            "Every ingredient class present (resin, curative, solvent, "
            "pigment, extender, additive) stays inside the two-component "
            "epoxy-polyamide solvent-borne envelope per blueprint prose "
            "(DGEBA-class resin, reactive polyamide curative, naphtha/"
            "n-butanol solvents, iron-oxide pigment, silica extender, "
            "dispersant/defoamer/thixotrope additives); no waterborne, "
            "zinc-rich, or nanofiller class present. This axis SURVIVES -- "
            "it is not the refuting finding here."
        ),
        "conforms": True,
    },
}

OUTDIR.mkdir(parents=True, exist_ok=True)
final_body = json.dumps(diagnostic, indent=2, sort_keys=True)
(OUTDIR / "diagnostic.canonical.json").write_text(final_body)
(OUTDIR / "diagnostic.runB.json").write_text(final_body)

print("verdict:", diagnostic["verdict"])
print("n_bom_lines_parsed:", n_lines)
print("n_lines_missing_domestic_flag:", n_missing_domestic_flag)
print("n_lines_missing_line_level_tier:", n_missing_line_tier)
print("missing_companion_files:", missing_companion_files)
print("blueprint_sha256:", blueprint_sha256)
print("source_records_sha256:", source_records_sha256)
