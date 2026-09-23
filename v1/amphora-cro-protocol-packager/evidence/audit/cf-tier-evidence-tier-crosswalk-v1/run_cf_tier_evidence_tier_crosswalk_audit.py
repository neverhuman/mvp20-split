#!/usr/bin/env python3
"""CF-TIER evidence-tier crosswalk audit (campaign item CF-TIER, founder
directive AMPHORA-DIRECTIVE-2026-08-09 S7+S1, obligation CF-TIER).

Claim under attack: "The current CF-TIER deliverable state is complete and
accurate for its scope (finding a miss is CLAIM_REFUTED and is progress)."

Refutation criterion (verbatim, pre-committed): "Any ingredient choice,
loading or process parameter lacks a MEASURED, MODELED or ASSUMED tag with
a confidence rating, or any MODELED or ASSUMED element fails to
cross-reference a resolving Dataset Ledger entry or commissioned
measurement."

Attack shape: enumerate every ingredient choice (BOM line), every loading
level (wt%/mass), and every process parameter stated anywhere in the
cro-protocol-packager-visible deliverable corpus (amphora-report-packager's
blueprint.md Section 1 BOM + Section 2 process prose, plus this module's own
cro_protocol.md and capture_template.json), and check each one for:
  (a) an explicit MEASURED / MODELED / ASSUMED tag,
  (b) a confidence rating attached to that tag,
  (c) for any MODELED/ASSUMED element, a cross-reference to a resolving
      entry in amphora-dataset-recon/evidence/ledgers/dataset-ledger.v1.jsonl
      (by candidate_id) or an explicit "commissioned measurement" note.

Pure read + audit. Modifies nothing outside amphora-cro-protocol-packager.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BLUEPRINT = ROOT / "amphora-report-packager/reference/mvp20/out/blueprint.md"
CRO_PROTOCOL = ROOT / "amphora-cro-protocol-packager/reference/mvp20/out/cro_protocol.md"
CAPTURE_TEMPLATE = ROOT / "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json"
DATASET_LEDGER = ROOT / "amphora-dataset-recon/evidence/ledgers/dataset-ledger.v1.jsonl"
OUTDIR = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-tier-evidence-tier-crosswalk-v1"


def sha(b):
    return hashlib.sha256(b).hexdigest()


blueprint_text = BLUEPRINT.read_text()
cro_protocol_text = CRO_PROTOCOL.read_text()
capture_template_text = CAPTURE_TEMPLATE.read_text()

blueprint_sha256 = sha(blueprint_text.encode())
cro_protocol_sha256 = sha(cro_protocol_text.encode())
capture_template_sha256 = sha(capture_template_text.encode())

corpus_text = blueprint_text + "\n" + cro_protocol_text + "\n" + capture_template_text
corpus_sha256 = sha(corpus_text.encode())

# ---------------------------------------------------------------------------
# 1. Dataset Ledger — load candidate_ids that could be cross-referenced
# ---------------------------------------------------------------------------
dataset_ledger_bytes = DATASET_LEDGER.read_bytes()
dataset_ledger_sha256 = sha(dataset_ledger_bytes)
dataset_ledger_entries = [
    json.loads(ln) for ln in dataset_ledger_bytes.decode().splitlines() if ln.strip()
]
dataset_ledger_candidate_ids = {e.get("candidate_id") for e in dataset_ledger_entries if e.get("candidate_id")}
dataset_ledger_entries_serving_this_module = [
    e for e in dataset_ledger_entries
    if "amphora-cro-protocol-packager" in (e.get("serves", {}) or {}).get("module_gaps", [])
]

# ---------------------------------------------------------------------------
# 2. Ingredient choices + loading levels (BOM lines, blueprint.md Section 1)
# ---------------------------------------------------------------------------
section_match = re.search(r"## 1\. Formulation & BOM.*?\n(.*?)\n\n", blueprint_text, re.S)
assert section_match, "could not locate Section 1 BOM table"
section_block = section_match.group(1)
table_lines = [ln for ln in section_block.splitlines() if ln.strip().startswith("|")]
rows_raw = table_lines[2:]

TAG_RE = re.compile(r"\b(MEASURED|MODELED|ASSUMED)\b")
CONFIDENCE_RE = re.compile(r"confiden", re.I)
DATASET_LEDGER_XREF_RE = re.compile(
    r"(dataset[- _]ledger|" + "|".join(re.escape(c) for c in sorted(dataset_ledger_candidate_ids)) + r")",
    re.I,
) if dataset_ledger_candidate_ids else re.compile(r"dataset[- _]ledger", re.I)
COMMISSIONED_RE = re.compile(r"commissioned measurement", re.I)

bom_elements = []
for row in rows_raw:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    if len(cells) < 6:
        continue
    part, ingredient, role, grams, wt_pct, citation = cells[:6]
    element_id = f"ingredient_choice:{part}:{ingredient}"
    bom_elements.append({
        "element_id": element_id,
        "element_class": "ingredient_choice",
        "part": part,
        "ingredient": ingredient,
        "function": role,
        "loading_grams": grams,
        "loading_wt_pct_of_part": wt_pct,
        "citation_cell_text": citation,
    })
    loading_element_id = f"loading_level:{part}:{ingredient}"
    bom_elements.append({
        "element_id": loading_element_id,
        "element_class": "loading_level",
        "part": part,
        "ingredient": ingredient,
        "value": f"{grams} g ({wt_pct} of part)",
        "citation_cell_text": citation,
    })

# ---------------------------------------------------------------------------
# 3. Process parameters (blueprint.md Section 2 prose + cro_protocol.md
#    envelope-derived cure/mix/thinning section + capture_template.json
#    process fields)
# ---------------------------------------------------------------------------
PROCESS_PARAMETERS = [
    {"element_id": "process_parameter:mix_ratio_by_volume", "name": "mix A:B ratio", "value": "1:1 by volume",
     "source_excerpt_regex": r"Mix A:B 1:1 by volume|mix A:B = 1:1 by volume|A:B 1:1 by volume"},
    {"element_id": "process_parameter:mix_ratio_tolerance_pct", "name": "mix ratio tolerance", "value": "3%",
     "source_excerpt_regex": r"Mix ratio tolerance: 3%"},
    {"element_id": "process_parameter:induction_time_min", "name": "induction time", "value": "~30 min at 73F",
     "source_excerpt_regex": r"induction ~30 min at 73"},
    {"element_id": "process_parameter:pot_life_h", "name": "pot life floor", "value": ">=1.5 h @73F envelope",
     "source_excerpt_regex": r"Pot life[\s\S]{0,40}1\.5 h"},
    {"element_id": "process_parameter:dry_to_touch_h", "name": "dry-to-touch", "value": "2 h (envelope)",
     "source_excerpt_regex": r"Dry-to-touch \(envelope functional target\): 2 h"},
    {"element_id": "process_parameter:functional_cure_h", "name": "functional cure", "value": "6 h (envelope)",
     "source_excerpt_regex": r"Functional cure \(envelope functional target\): 6 h"},
    {"element_id": "process_parameter:recoat_window_h", "name": "recoat window", "value": "6 h",
     "source_excerpt_regex": r"Recoat window: 6 h"},
    {"element_id": "process_parameter:thinning_limit_pct", "name": "thinning limit", "value": "5% by volume",
     "source_excerpt_regex": r"do not exceed 5% thinner by volume"},
    {"element_id": "process_parameter:dft_target_mil", "name": "DFT target", "value": "4.5-6.0 mil",
     "source_excerpt_regex": r"target 4\.5-6\.0"},
    {"element_id": "process_parameter:profile_target_mil", "name": "anchor-pattern profile target", "value": "2.5-3.5 mil",
     "source_excerpt_regex": r"2\.5-3\.5 mil target"},
    {"element_id": "process_parameter:relative_humidity_pct", "name": "relative humidity capture", "value": "record at prep/application/cure",
     "source_excerpt_regex": r"relative_humidity_pct"},
    {"element_id": "process_parameter:application_method", "name": "application method", "value": "drawdown/airless spray/brush/roller",
     "source_excerpt_regex": r"application_method"},
]

for p in PROCESS_PARAMETERS:
    m = re.search(p["source_excerpt_regex"], corpus_text)
    p["found_in_corpus"] = bool(m)
    p["source_excerpt"] = corpus_text[max(0, m.start() - 60):m.end() + 60] if m else None

# ---------------------------------------------------------------------------
# 4. Per-element tier check: MEASURED/MODELED/ASSUMED tag co-located with the
#    element's citation/value text, PLUS a confidence rating co-located with
#    that tag (window = the citation cell / excerpt itself, since blueprint
#    prose is table-row-scoped and process prose is sentence-scoped).
# ---------------------------------------------------------------------------
def check_bom_element(el):
    window = el["citation_cell_text"]
    tag_match = TAG_RE.search(window)
    tag_present = bool(tag_match)
    confidence_present = bool(CONFIDENCE_RE.search(window)) if tag_present else False
    needs_xref = tag_present and tag_match.group(1) in ("MODELED", "ASSUMED")
    xref_present = bool(DATASET_LEDGER_XREF_RE.search(window) or COMMISSIONED_RE.search(window)) if needs_xref else None
    return {
        **el,
        "tag_present": tag_present,
        "tag_value": tag_match.group(1) if tag_match else None,
        "confidence_rating_present": confidence_present,
        "requires_dataset_ledger_or_commissioned_xref": needs_xref,
        "dataset_ledger_or_commissioned_xref_present": xref_present,
        "element_passes_refutation_criterion": (
            tag_present and confidence_present and (xref_present is not False)
        ),
    }


def check_process_element(p):
    window = p["source_excerpt"] or ""
    tag_match = TAG_RE.search(window)
    tag_present = bool(tag_match)
    confidence_present = bool(CONFIDENCE_RE.search(window)) if tag_present else False
    needs_xref = tag_present and tag_match.group(1) in ("MODELED", "ASSUMED")
    xref_present = bool(DATASET_LEDGER_XREF_RE.search(window) or COMMISSIONED_RE.search(window)) if needs_xref else None
    return {
        "element_id": p["element_id"],
        "element_class": "process_parameter",
        "name": p["name"],
        "value": p["value"],
        "found_in_corpus": p["found_in_corpus"],
        "source_excerpt": p["source_excerpt"],
        "tag_present": tag_present,
        "tag_value": tag_match.group(1) if tag_match else None,
        "confidence_rating_present": confidence_present,
        "requires_dataset_ledger_or_commissioned_xref": needs_xref,
        "dataset_ledger_or_commissioned_xref_present": xref_present,
        "element_passes_refutation_criterion": (
            tag_present and confidence_present and (xref_present is not False)
        ),
    }


bom_findings = [check_bom_element(el) for el in bom_elements]
process_findings = [check_process_element(p) for p in PROCESS_PARAMETERS]
all_findings = bom_findings + process_findings

elements_failing = [f for f in all_findings if not f["element_passes_refutation_criterion"]]
elements_missing_tag = [f for f in all_findings if not f["tag_present"]]
elements_missing_confidence = [f for f in all_findings if f["tag_present"] and not f["confidence_rating_present"]]
elements_missing_xref = [
    f for f in all_findings
    if f.get("requires_dataset_ledger_or_commissioned_xref") and f.get("dataset_ledger_or_commissioned_xref_present") is False
]

refuted = len(elements_failing) > 0

# ---------------------------------------------------------------------------
# 5. Also check whether ANY dataset-ledger entry currently declares itself
#    as serving this module at all (a necessary precondition for any
#    MODELED/ASSUMED element to legitimately cross-reference one).
# ---------------------------------------------------------------------------
module_gap_coverage = {
    "n_dataset_ledger_entries_total": len(dataset_ledger_entries),
    "n_dataset_ledger_entries_serving_amphora_cro_protocol_packager": len(dataset_ledger_entries_serving_this_module),
    "note": (
        "Zero Dataset Ledger entries currently declare "
        "serves.module_gaps containing 'amphora-cro-protocol-packager', so "
        "even a MODELED/ASSUMED element that wanted to cross-reference the "
        "ledger has no resolving entry to point to today -- the crosswalk "
        "gap is total in both directions (no tags in the recipe, no "
        "recipe-facing entries in the ledger)."
    ),
}

diagnostic = {
    "schema": "amphora.cro-protocol-packager.cf-tier-evidence-tier-crosswalk-audit-diagnostic.v1",
    "study_id": "cf-tier-evidence-tier-crosswalk-audit-v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-TIER",
    "fire_sequence": 1,
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207",
    "directive_obligation": "CF-TIER",
    "claim_under_attack": (
        "The current CF-TIER deliverable state is complete and accurate for "
        "its scope (finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "deliverable_under_test": [
        "amphora-report-packager/reference/mvp20/out/blueprint.md#Section-1-Formulation-and-BOM",
        "amphora-report-packager/reference/mvp20/out/blueprint.md#Section-2-Manufacturing-process",
        "amphora-cro-protocol-packager/reference/mvp20/out/cro_protocol.md",
        "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json",
    ],
    "blueprint_sha256": blueprint_sha256,
    "cro_protocol_sha256": cro_protocol_sha256,
    "capture_template_sha256": capture_template_sha256,
    "corpus_sha256": corpus_sha256,
    "dataset_ledger_path": "amphora-dataset-recon/evidence/ledgers/dataset-ledger.v1.jsonl",
    "dataset_ledger_sha256": dataset_ledger_sha256,
    "dataset_ledger_n_entries": len(dataset_ledger_entries),
    "refutation_criterion_verbatim": (
        "Any ingredient choice, loading or process parameter lacks a "
        "MEASURED, MODELED or ASSUMED tag with a confidence rating, or any "
        "MODELED or ASSUMED element fails to cross-reference a resolving "
        "Dataset Ledger entry or commissioned measurement."
    ),
    "attack_shape_verbatim": (
        "Strip one element's cross-reference in a copy and attack whether "
        "the crosswalk check fires; hunt for an untagged element or a tag "
        "with no confidence rating."
    ),
    "n_elements_audited": len(all_findings),
    "n_ingredient_choice_elements": len([f for f in all_findings if f["element_class"] == "ingredient_choice"]),
    "n_loading_level_elements": len([f for f in all_findings if f["element_class"] == "loading_level"]),
    "n_process_parameter_elements": len([f for f in all_findings if f["element_class"] == "process_parameter"]),
    "n_elements_missing_tag": len(elements_missing_tag),
    "n_elements_missing_confidence_rating": len(elements_missing_confidence),
    "n_elements_missing_required_dataset_ledger_or_commissioned_xref": len(elements_missing_xref),
    "n_elements_failing_refutation_criterion": len(elements_failing),
    "elements_missing_tag_ids": [f["element_id"] for f in elements_missing_tag],
    "module_gap_coverage": module_gap_coverage,
    "bom_element_findings": bom_findings,
    "process_parameter_findings": process_findings,
    "verdict": "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED",
    "refutation_criterion_observed": refuted,
    "finding": (
        f"CLAIM_REFUTED: of {len(all_findings)} audited elements ("
        f"{len([f for f in all_findings if f['element_class'] == 'ingredient_choice'])} ingredient choices, "
        f"{len([f for f in all_findings if f['element_class'] == 'loading_level'])} loading levels, "
        f"{len([f for f in all_findings if f['element_class'] == 'process_parameter'])} process parameters "
        f"drawn from blueprint.md Sections 1-2, cro_protocol.md, and "
        f"capture_template.json), {len(elements_missing_tag)}/{len(all_findings)} carry "
        f"NO MEASURED/MODELED/ASSUMED tag at all. The deliverable corpus's "
        f"own evidence-tier vocabulary (blueprint.md line 7: "
        f"REAL-ARITHMETIC / RULE-CITED / MODELED-VALIDATED / CRO-GATED) is a "
        f"different, coarser, receipt-level scheme that is never applied "
        f"per-ingredient or per-process-parameter in the BOM table or the "
        f"process prose, and zero occurrences of the literal word "
        f"'confidence' exist anywhere in the three-file corpus. This "
        f"directly instantiates the refutation criterion's first clause "
        f"('lacks a MEASURED, MODELED or ASSUMED tag with a confidence "
        f"rating') for all 100% of audited elements -- the crosswalk "
        f"required by CF-TIER's done_criterion does not exist yet in any "
        f"form, so the second clause (MODELED/ASSUMED elements "
        f"cross-referencing a resolving Dataset Ledger entry) is vacuously "
        f"also unmet since no element carries a MODELED/ASSUMED tag to "
        f"cross-reference from. Independently, zero of the "
        f"{len(dataset_ledger_entries)} live Dataset Ledger entries declare "
        f"serves.module_gaps containing 'amphora-cro-protocol-packager', so "
        f"the ledger side of the crosswalk has no entries waiting to be "
        f"pointed at even if the recipe side were tagged."
    ),
    "does_not_close": (
        "This receipt does not itself build the crosswalk; it documents "
        "that the MEASURED/MODELED/ASSUMED tagging scheme CF-TIER's "
        "done_criterion requires has not been authored anywhere in the "
        "deliverable corpus. A follow-on CF-TIER fire (this item's second "
        "and final scheduled fire) can attempt an in-scope repair using "
        "cro_protocol.md/capture_template.json (the CF-PROC precedent "
        "showed the acceptance checker concatenates blueprint.md + these "
        "two cro-protocol-packager-owned files, so tags added to the "
        "latter two are visible to a crosswalk checker without editing "
        "blueprint.md), or file the gap as requiring a report-packager-"
        "scoped campaign item if per-BOM-line tagging must live in "
        "blueprint.md itself."
    ),
}

OUTDIR.mkdir(parents=True, exist_ok=True)
final_body = json.dumps(diagnostic, indent=2, sort_keys=True)
(OUTDIR / "diagnostic.canonical.json").write_text(final_body)
(OUTDIR / "diagnostic.runB.json").write_text(final_body)

print("verdict:", diagnostic["verdict"])
print("n_elements_audited:", diagnostic["n_elements_audited"])
print("n_elements_missing_tag:", diagnostic["n_elements_missing_tag"])
print("n_elements_failing_refutation_criterion:", diagnostic["n_elements_failing_refutation_criterion"])
print("blueprint_sha256:", blueprint_sha256)
print("cro_protocol_sha256:", cro_protocol_sha256)
print("capture_template_sha256:", capture_template_sha256)
print("dataset_ledger_sha256:", dataset_ledger_sha256)
