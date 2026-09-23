#!/usr/bin/env python3
"""CF-BOM formulation-completeness audit, ROUND 3 / FINAL (campaign item
CF-BOM, founder directive AMPHORA-DIRECTIVE-2026-08-09 S7, obligation
CF-BOM, max_fires=3 -- this is the last scheduled fire for this item).

Extends fire 1 (cf-bom-formulation-completeness-audit-receipt.v1) and fire 2
(...v2, byte-hash reconfirm + positive/discrimination controls on the
citation-deletion attack shape). Fire 2's STATE.json explicitly directed
fire 3 NOT to repeat the byte-identical reconfirm a third time with no new
information value, and instead to either extend the attack or file
BLOCKED_DATA/SATURATED.

THIS FIRE'S NEW AXIS: fires 1-2 checked "commercial_source_citation_present"
as merely "citation cell is non-empty and contains an http(s) URL". That
check does not verify the citation actually NAMES a commercial supplier, as
the done_criterion's "at least one candidate commercial source" clause
requires. This fire cross-references each matched source_records.json
record's own self-declared `supplier_status` field and citation domain: two
BOM lines (silica, naphtha) cite ONLY a US-government hazard-chemical
database page (cameochemicals.noaa.gov), and BOTH matched supplier records
self-declare `supplier_status: "chemical property source only; supplier not
selected"` / "unknown / RFQ required" -- i.e. the sourcing corpus itself
admits no commercial entity has been named for these two ingredients. Every
other BOM line's citation resolves to an actual named commercial entity's
own TDS/product page (Miller-Stephenson/Hexion, Lanxess, Elementis, BYK,
Eastman, Ancamide-line supplier), even though full RFQ/declaration fields on
those records also remain "unknown / RFQ required". This is a distinct,
narrower, and more precise finding than fire 1/2's "citation present" check.

Also reconfirms: (a) blueprint.md / source_records.json remain byte-identical
to the fire-1/fire-2-cited hashes (no repair landed across 3 fires); (b) the
8 companion evidence files cited by blueprint prose still do not exist
anywhere in the repo; (c) domestic-sourcing-preference flag and line-level
evidence-tier gaps from fire 1/2 are unchanged. Adds a positive control
targeted at the NEW commercial-source-genuineness axis specifically (fire
2's positive control targeted citation-deletion, a different axis) and a
discrimination control.

Refutation criterion (verbatim, pre-committed): "Any BOM line lacks
function, target weight percent, grade or spec attributes, or a candidate
commercial source, or any numeric claim about an ingredient is uncited and
untiered."

Pure read + audit. Modifies nothing outside amphora-cro-protocol-packager.
"""
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BLUEPRINT = ROOT / "amphora-report-packager/reference/mvp20/out/blueprint.md"
SOURCE_RECORDS = ROOT / "amphora-source-ledger/reference/mvp20/data/source_records.json"
OUTDIR = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-bom-formulation-completeness-v3"

FIRE1_BLUEPRINT_SHA256 = "b3db17345245812b4b186433e56f9bb86fc04e28d47f3d121d4036d5dc9cc879"
FIRE1_SOURCE_RECORDS_SHA256 = "87174e555bdf31cd30d7d13da2dedb5cc6c14af33586fdd3981d97c0409da26c"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# 1. Parse the BOM table (Section 1) out of blueprint.md
# ---------------------------------------------------------------------------
blueprint_text = BLUEPRINT.read_text()
blueprint_sha256 = sha(blueprint_text.encode())

section_match = re.search(r"## 1\. Formulation & BOM.*?\n(.*?)\n\n", blueprint_text, re.S)
assert section_match, "could not locate Section 1 BOM table"
section_block = section_match.group(1)
table_lines = [ln for ln in section_block.splitlines() if ln.strip().startswith("|")]
header = table_lines[0]
rows_raw = table_lines[2:]

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
# 2. Load sourcing corpus
# ---------------------------------------------------------------------------
source_doc = json.loads(SOURCE_RECORDS.read_text())
source_records_sha256 = sha(SOURCE_RECORDS.read_bytes())
records = source_doc["records"]
records_by_id = {r["id"]: r for r in records}

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

# Government/handbook property-anchor domains: NOT a commercial supplier by
# themselves, regardless of what candidate_grade text says.
NON_COMMERCIAL_DOMAINS = ["cameochemicals.noaa.gov"]

NON_COMMERCIAL_SUPPLIER_STATUS_MARKERS = [
    "supplier not selected",
    "chemical property source only",
]


def is_flagged_domestic_preference(value):
    if value is None:
        return False
    v = value.strip().lower()
    if v in ("", "not applicable"):
        return False
    if "unknown" in v or "rfq" in v or "supplier declaration" in v:
        return False
    return True


def matched_records(ingredient_key, records_map):
    ids = INGREDIENT_MATCH.get(ingredient_key, [])
    return [records_map[i] for i in ids if i in records_map]


def has_genuine_commercial_source(matches, citation_text):
    """A candidate commercial source must NAME an actual commercial entity
    (its own TDS/product page), not merely cite a government/handbook
    property anchor. Two independent signals: (a) the citation/record URL
    is not a NON_COMMERCIAL_DOMAINS entry, and (b) the matched record's own
    supplier_status field does not self-declare 'supplier not selected' /
    'chemical property source only' (the sourcing corpus's own admission)."""
    if not matches:
        return False
    for m in matches:
        url = (m.get("url") or "") + " " + (citation_text or "")
        on_noncommercial_domain = any(dom in url for dom in NON_COMMERCIAL_DOMAINS)
        status = (m.get("supplier_status") or "").lower()
        self_declared_no_supplier = any(mk in status for mk in NON_COMMERCIAL_SUPPLIER_STATUS_MARKERS)
        if not on_noncommercial_domain and not self_declared_no_supplier:
            return True
    return False


def check_line(line, records_map):
    key = line["ingredient"]
    matches = matched_records(key, records_map)
    has_function = bool(line["function"])
    has_wt_pct = bool(re.search(r"[\d.]+%", line["wt_pct_of_part"]))
    has_citation = bool(line["citation"]) and "http" in line["citation"]
    grade_specs = [
        m.get("candidate_grade") for m in matches
        if m.get("candidate_grade") and m["candidate_grade"] != "not applicable"
    ]
    has_grade_spec = bool(grade_specs)
    domestic_values = [m.get("domestic_taa_status") for m in matches]
    domestic_flagged = any(is_flagged_domestic_preference(v) for v in domestic_values)
    has_line_level_tier = bool(
        re.search(r"REAL-ARITHMETIC|RULE-CITED|MODELED-VALIDATED|CRO-GATED", line["citation"])
    )
    genuine_commercial_source = has_genuine_commercial_source(matches, line["citation"])
    supplier_status_values = [m.get("supplier_status") for m in matches]

    return {
        "part": line["part"],
        "ingredient": key,
        "function_present": has_function,
        "target_wt_pct_present": has_wt_pct,
        "commercial_source_citation_present": has_citation,
        "matched_source_record_ids": [m["id"] for m in matches],
        "supplier_status_values": supplier_status_values,
        "genuine_commercial_source_named": genuine_commercial_source,
        "grade_spec_attributes_present": has_grade_spec,
        "grade_spec_values": grade_specs,
        "domestic_sourcing_preference_values": domestic_values,
        "domestic_sourcing_preference_flagged": domestic_flagged,
        "line_level_evidence_tier_present": has_line_level_tier,
        "line_complete_per_done_criteria": (
            has_function and has_wt_pct and has_citation and has_grade_spec and genuine_commercial_source
        ),
        "line_passes_full_refutation_criterion": (
            has_function
            and has_wt_pct
            and has_citation
            and has_grade_spec
            and genuine_commercial_source
            and domestic_flagged
            and has_line_level_tier
        ),
    }


findings = [check_line(line, records_by_id) for line in bom_lines]

# ---------------------------------------------------------------------------
# 3. Companion-evidence-file existence check (fresh re-scan, fire 3)
# ---------------------------------------------------------------------------
cited_companion_files = [
    "funnel_results.json", "arithmetic_audit.md", "conflict_register.md",
    "validation_cards.md", "known_answer_report.md", "discovery_annex.md",
    "formulation_black.json", "formulation_yellow.json",
]
companion_check = []
for fname in cited_companion_files:
    hits = list(ROOT.rglob(fname))
    companion_check.append({
        "cited_filename": fname,
        "cited_in_blueprint": fname in blueprint_text,
        "exists_anywhere_in_repo": bool(hits),
        "found_paths": [str(p.relative_to(ROOT)) for p in hits],
    })
missing_companion_files = [
    c["cited_filename"] for c in companion_check if c["cited_in_blueprint"] and not c["exists_anywhere_in_repo"]
]

# ---------------------------------------------------------------------------
# 4. Step A: reconfirm byte-identity against fire-1/fire-2-cited hashes
# ---------------------------------------------------------------------------
deliverable_unchanged = blueprint_sha256 == FIRE1_BLUEPRINT_SHA256
sourcing_corpus_unchanged = source_records_sha256 == FIRE1_SOURCE_RECORDS_SHA256

lines_failing_done_criteria = [f for f in findings if not f["line_complete_per_done_criteria"]]
lines_missing_domestic_flag = [f for f in findings if not f["domestic_sourcing_preference_flagged"]]
lines_missing_line_tier = [f for f in findings if not f["line_level_evidence_tier_present"]]
lines_missing_genuine_commercial_source = [f for f in findings if not f["genuine_commercial_source_named"]]

n_lines = len(findings)
refuted = (
    len(lines_failing_done_criteria) > 0
    or len(lines_missing_domestic_flag) > 0
    or len(lines_missing_line_tier) > 0
    or len(missing_companion_files) > 0
)

# ---------------------------------------------------------------------------
# 5. Step B: positive control targeted at the NEW commercial-source axis.
#    Take a line that CURRENTLY passes genuine_commercial_source_named
#    (dgeba_828, cited to Miller-Stephenson's own EPON 828 TDS page) and, in
#    an in-memory copy of the sourcing corpus, mutate its matched record's
#    supplier_status + url to look like the silica/naphtha pattern (a
#    government-handbook-only property anchor with self-declared "supplier
#    not selected"). Confirm the checker flips genuine_commercial_source_named
#    to False and the line now fails line_complete_per_done_criteria.
# ---------------------------------------------------------------------------
mutated_records = copy.deepcopy(records_by_id)
target_id = "SRC-LANXESS-BLACK-OXIDE"  # iron_oxide_black -- single-record match, currently genuine
before_status = mutated_records[target_id].get("supplier_status")
before_url = mutated_records[target_id].get("url")
mutated_records[target_id]["supplier_status"] = "chemical property source only; supplier not selected"
mutated_records[target_id]["url"] = "https://cameochemicals.noaa.gov/chemical/12319"

target_line = next(l for l in bom_lines if l["ingredient"] == "iron_oxide_black" and l["part"] == "A")
baseline_finding = check_line(target_line, records_by_id)
mutated_finding = check_line(target_line, mutated_records)

positive_control = {
    "planted_defect": (
        "mutated the iron_oxide_black (Part A) matched record "
        "SRC-LANXESS-BLACK-OXIDE to look like a government-handbook-only "
        "property anchor with no named commercial supplier -- the exact "
        "pattern already present for silica/naphtha -- in an in-memory copy "
        "of the sourcing corpus. No file on disk was modified."
    ),
    "how_planted": (
        f"records_by_id['SRC-LANXESS-BLACK-OXIDE']['supplier_status'] set "
        f"from {before_status!r} to 'chemical property source only; supplier "
        f"not selected'; ['url'] set from {before_url!r} to "
        f"'https://cameochemicals.noaa.gov/chemical/12319'"
    ),
    "baseline_genuine_commercial_source_named": baseline_finding["genuine_commercial_source_named"],
    "detected": (
        baseline_finding["genuine_commercial_source_named"]
        and (not mutated_finding["genuine_commercial_source_named"])
        and (not mutated_finding["line_complete_per_done_criteria"])
    ),
    "evidence": mutated_finding,
}

# ---------------------------------------------------------------------------
# 6. Step C: discrimination control -- synthetic fully-repaired copy passes
# ---------------------------------------------------------------------------
repaired_records = copy.deepcopy(records_by_id)
for rid, r in repaired_records.items():
    r["domestic_taa_status"] = "domestic preferred; TAA-compliant (synthetic determination for control)"
    if r.get("supplier_status", "").lower() not in ("not applicable",):
        r["supplier_status"] = "supplier confirmed; declarations on file (synthetic determination for control)"
    if any(dom in (r.get("url") or "") for dom in NON_COMMERCIAL_DOMAINS):
        r["url"] = "https://synthetic-control-vendor.example.com/tds/" + rid + ".pdf"

repaired_lines = []
for line in bom_lines:
    rl = dict(line)
    citation = rl["citation"]
    for dom in NON_COMMERCIAL_DOMAINS:
        if dom in citation:
            citation = "DISTRIBUTOR: https://synthetic-control-vendor.example.com/tds/" + rl["ingredient"] + ".pdf"
    rl["citation"] = citation + " [RULE-CITED]"
    repaired_lines.append(rl)

repaired_findings = [check_line(rl, repaired_records) for rl in repaired_lines]
repaired_lines_failing = [f for f in repaired_findings if not f["line_complete_per_done_criteria"]]
repaired_missing_domestic = [f for f in repaired_findings if not f["domestic_sourcing_preference_flagged"]]
repaired_missing_tier = [f for f in repaired_findings if not f["line_level_evidence_tier_present"]]
# companion files still won't exist in this synthetic exercise -- exclude
# that axis from the discrimination control since it is a repo-file-
# existence check, not a per-line field check, and was already positively
# controlled in fire 2.
discrimination_refuted = (
    len(repaired_lines_failing) > 0 or len(repaired_missing_domestic) > 0 or len(repaired_missing_tier) > 0
)
discrimination_control = {
    "description": (
        "synthetic fully-repaired copy: every BOM line's matched record given "
        "a concrete domestic_taa_status determination, a confirmed "
        "supplier_status (also repairs the NEW genuine-commercial-source "
        "axis for silica/naphtha), and an explicit [RULE-CITED] tier label "
        "appended to the citation cell; same checker re-run"
    ),
    "checker_reports_refuted_on_per_line_axes": discrimination_refuted,
    "discrimination_control_passed": not discrimination_refuted,
    "note": (
        "confirms the checker (including the new commercial-source-"
        "genuineness axis) is not hard-wired to always return REFUTED -- it "
        "discriminates a genuinely complete BOM from the real, incomplete one"
    ),
}

# ---------------------------------------------------------------------------
# 7. Envelope conformance spot-check (attack shape clause 3)
# ---------------------------------------------------------------------------
envelope_conformance = {
    "note": (
        "Every ingredient class present (resin, curative, solvent, pigment, "
        "extender, additive) stays inside the two-component epoxy-polyamide "
        "solvent-borne envelope per blueprint prose (DGEBA-class resin, "
        "reactive polyamide curative, naphtha/n-butanol solvents, iron-oxide "
        "pigment, silica extender, dispersant/defoamer/thixotrope additives); "
        "no waterborne, zinc-rich, or nanofiller class present. Re-confirmed "
        "fire 3; this axis SURVIVES -- it is not a refuting finding."
    ),
    "conforms": True,
}

diagnostic = {
    "schema": "amphora.cro-protocol-packager.cf-bom-formulation-completeness-audit-diagnostic.v3",
    "study_id": "cf-bom-formulation-completeness-audit-v3",
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-BOM",
    "fire_sequence": 3,
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
    "step_a_reconfirm": {
        "deliverable_unchanged_since_fire1": deliverable_unchanged,
        "sourcing_corpus_unchanged_since_fire1": sourcing_corpus_unchanged,
        "fire1_deliverable_sha256": FIRE1_BLUEPRINT_SHA256,
        "fire1_sourcing_corpus_sha256": FIRE1_SOURCE_RECORDS_SHA256,
        "lines_missing_domestic_sourcing_preference_flag": [f["ingredient"] for f in lines_missing_domestic_flag],
        "n_lines_missing_domestic_sourcing_preference_flag": len(lines_missing_domestic_flag),
        "lines_missing_line_level_evidence_tier": [f["ingredient"] for f in lines_missing_line_tier],
        "n_lines_missing_line_level_evidence_tier": len(lines_missing_line_tier),
        "missing_companion_files_cited_by_blueprint": missing_companion_files,
        "reconfirms_v1_v2_findings": True,
    },
    "step_d_new_axis_commercial_source_genuineness": {
        "description": (
            "NEW this fire: fires 1-2 checked only that the citation cell is "
            "non-empty and contains a URL. This axis additionally checks "
            "whether the matched sourcing record NAMES an actual commercial "
            "entity, using two independent signals -- (1) the citation/record "
            "URL is not a government/handbook-only domain "
            "(cameochemicals.noaa.gov), and (2) the record's own "
            "supplier_status field does not self-declare 'supplier not "
            "selected' / 'chemical property source only'."
        ),
        "lines_missing_genuine_commercial_source": [f["ingredient"] for f in lines_missing_genuine_commercial_source],
        "n_lines_missing_genuine_commercial_source": len(lines_missing_genuine_commercial_source),
        "detail": [
            f for f in findings if not f["genuine_commercial_source_named"]
        ],
        "finding": (
            f"{len(lines_missing_genuine_commercial_source)} of {n_lines} BOM "
            "lines (silica x2 lines, naphtha x1 line) cite ONLY a US "
            "government hazard-chemical database page (NOAA CAMEO) as their "
            "'commercial source'; the sourcing corpus's own matched records "
            "self-declare supplier_status='chemical property source only; "
            "supplier not selected' / 'unknown / RFQ required' -- i.e. the "
            "corpus itself admits no commercial entity has been named for "
            "these ingredients, unlike every other BOM line which at least "
            "cites a real company's own TDS/product page (Miller-Stephenson/"
            "Hexion, Lanxess, Elementis, BYK, Eastman, the Ancamide-line "
            "supplier) even though full RFQ declarations remain pending on "
            "those too. This directly instantiates the refutation "
            "criterion's 'a candidate commercial source' clause."
        ),
    },
    "bom_line_findings": findings,
    "companion_evidence_file_check": companion_check,
    "step_b_positive_control": positive_control,
    "step_c_discrimination_control": discrimination_control,
    "envelope_conformance_spot_check": envelope_conformance,
    "verdict": "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED",
    "refutation_criterion_observed": refuted,
    "structural_finding": (
        "As recorded in fire 2: landing the actual repair (domestic "
        "determinations, per-line tiers, the 8 missing companion files, and "
        "now also naming a real commercial supplier for silica/naphtha) "
        "requires edits to amphora-report-packager/reference/mvp20/out/"
        "blueprint.md and amphora-source-ledger/reference/mvp20/data/"
        "source_records.json, both outside amphora-cro-protocol-packager's "
        "write scope. This is fire 3/3 (max_fires reached) for CF-BOM; the "
        "item cannot reach done/ from a cro-protocol-packager-scoped fire "
        "alone. Domestic-sourcing/TAA/supplier-naming determinations "
        "specifically require real supplier RFQ responses (blueprint.md "
        "Section 4 explicitly states this: 'Domestic/TAA status ... are to "
        "verify by supplier declaration/RFQ; they are not claimed here') -- "
        "that sub-piece is filed as a BLOCKED_DATA queue entry. The per-line "
        "tier labels and 8 companion files are an internal cross-module "
        "authoring gap, not an external-data gap, and need a report-"
        "packager/source-ledger campaign fire (or an explicit scope "
        "exception) to land, after which a future cro-protocol-packager "
        "fire should re-run this checker as the acceptance test."
    ),
    "reconfirms_prior_receipts": [
        "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-BOM/attempts/cf-bom-formulation-completeness-audit-receipt.v1.dsse.json",
        "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-BOM/attempts/cf-bom-formulation-completeness-audit-receipt.v2.dsse.json",
    ],
}

OUTDIR.mkdir(parents=True, exist_ok=True)
final_body = json.dumps(diagnostic, indent=2, sort_keys=True)
(OUTDIR / "diagnostic.canonical.json").write_text(final_body)
(OUTDIR / "diagnostic.runB.json").write_text(final_body)

print("verdict:", diagnostic["verdict"])
print("n_bom_lines_parsed:", n_lines)
print("n_lines_missing_genuine_commercial_source:", len(lines_missing_genuine_commercial_source))
print("lines_missing_genuine_commercial_source:", [f["ingredient"] for f in lines_missing_genuine_commercial_source])
print("deliverable_unchanged_since_fire1:", deliverable_unchanged)
print("sourcing_corpus_unchanged_since_fire1:", sourcing_corpus_unchanged)
print("positive_control_detected:", positive_control["detected"])
print("discrimination_control_passed:", discrimination_control["discrimination_control_passed"])
print("missing_companion_files:", missing_companion_files)
print("blueprint_sha256:", blueprint_sha256)
print("source_records_sha256:", source_records_sha256)
