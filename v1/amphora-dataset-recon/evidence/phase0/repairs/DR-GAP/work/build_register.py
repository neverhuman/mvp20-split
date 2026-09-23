#!/usr/bin/env python3
"""Build the DR-GAP gap register (amphora-dataset-recon campaign item DR-GAP).

Consolidates, from the portfolio's own declared sources at snapshot date
2026-08-10, every row of a gap register in which each row states the four
mandated facts (directive Section 3): what measurement or label class is
missing, at what minimum n, under what measurement standard, and what a
qualifying dataset would have to contain.

Sources (per the item's objective, verbatim categories):
  1. every open data-acquisition-queue ask (data-acquisition-queue.jsonl on xbabe1)
  2. every Pre-Tier-0 module whose promotion blocker names a missing dataset
     or measurement class (mission.md 'External dependency or delay' bullets,
     cross-referenced with the module's locked promotion-gate target, for
     every module at phase == PRE_PHASE_0)
  3. every lab-in-the-loop experiment specification referencing an external
     corpus, comparator, or label source (collapsed into row 2 for this
     snapshot: no distinct Candidate-Formulation/lab-spec document exists yet
     anywhere in the tree -- confirmed by a full-tree search this fire -- so
     each Pre-Tier-0 module's own locked promotion-gate target IS its only
     currently-published lab-in-the-loop spec; this collapse is declared, not
     silent)
  4. every MODELED/ASSUMED recipe element already published at the snapshot
     date (NONE: no Candidate Formulation Package / recipe blueprint exists
     anywhere in the tree at this snapshot -- CF-TIER has not run yet, and per
     the item's own text this register closes before CF-TIER exists; declared
     as an explicit empty-set finding, not silent omission)

No acquisition: this script reads only files already resident inside
mvp20-split (module mission.md prose, the xbabe1 queue snapshot copied in as
an internal-not-external artifact) and a local copy of the queue file. No web
call, download, or external fetch is made by this script.
"""
import hashlib
import json
import re
from pathlib import Path

ITEM = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-dataset-recon/evidence/phase0/repairs/DR-GAP")
WORK = ITEM / "work"
QUEUE_SNAPSHOT = WORK / "data-acquisition-queue.snapshot.jsonl"
SNAPSHOT_DATE = "2026-08-10"


def sha(b):
    return hashlib.sha256(b).hexdigest()


STANDARD_RE = re.compile(
    r"\bASTM\s?[A-Z]?\d+[A-Za-z0-9\-]*|\bISO\s?\d+[A-Za-z0-9\-]*|\bGB/?T\s?\d+|"
    r"\bJIS\s?[A-Z]?\s?\d+|\bDIN\s?\d+|\bD\d{3,4}\b"
)


def extract_standards(text):
    found = sorted(set(m.group(0) for m in STANDARD_RE.finditer(text)))
    return found


# ---------------------------------------------------------------------------
# Source 1: data-acquisition-queue.jsonl (14 lines, read verbatim)
# ---------------------------------------------------------------------------
queue_lines = [l for l in QUEUE_SNAPSHOT.read_text().splitlines() if l.strip()]
assert len(queue_lines) == 14, f"expected 14 queue lines, found {len(queue_lines)}"
queue_snapshot_sha256 = sha(QUEUE_SNAPSHOT.read_bytes())

queue_rows = []
for i, line in enumerate(queue_lines, start=1):
    entry = json.loads(line)
    line_sha = sha(line.encode())
    gap_text = entry.get("gap", "")
    standards = extract_standards(gap_text)
    license_text = entry.get("license", "NOT_SPECIFIED_IN_SOURCE")
    if standards:
        measurement_standard = (
            "Named in source gap text: " + "; ".join(standards) +
            f" | source license/rights context: {license_text}"
        )
    else:
        measurement_standard = (
            "NO_FORMAL_MEASUREMENT_STANDARD_NAMED_IN_SOURCE_GAP_TEXT "
            f"| source license/rights context: {license_text}"
        )
    est = entry.get("estimated_records", "NOT_SPECIFIED_IN_SOURCE")
    row = {
        "row_id": f"Q{i:02d}",
        "source_type": "data_acquisition_queue_ask",
        "module": entry.get("module", "NOT_SPECIFIED_IN_SOURCE"),
        "missing_measurement_or_label_class": gap_text,
        "minimum_n": str(est),
        "measurement_standard": measurement_standard,
        "qualifying_dataset_requirements": (
            f"candidate_source: {entry.get('candidate_source', 'NOT_SPECIFIED_IN_SOURCE')} "
            f"| next_action: {entry.get('next_action', 'NOT_SPECIFIED_IN_SOURCE')} "
            f"| license_verified: {entry.get('license_verified', 'NOT_SPECIFIED_IN_SOURCE')} "
            f"| url_or_doi: {entry.get('url_or_doi', 'NOT_SPECIFIED_IN_SOURCE')}"
        ),
        "source_ref": {
            "path": "data-acquisition-queue.jsonl (xbabe1, mirrored read-only into this item's work/ as data-acquisition-queue.snapshot.jsonl)",
            "queue_line_index_1based": i,
            "queue_line_sha256": line_sha,
        },
        "snapshot_date": SNAPSHOT_DATE,
    }
    queue_rows.append(row)

# ---------------------------------------------------------------------------
# Source 2+3 (collapsed, declared): Pre-Tier-0 (phase == PRE_PHASE_0) module
# promotion blockers, each paired with its own locked promotion-gate target
# text as the only currently-published lab-in-the-loop spec for that module.
# Extracted by direct read of each module's docs/mission.md
# "## KPI register and promotion gates" section this fire.
# ---------------------------------------------------------------------------
PROMOTION_BLOCKERS = [
    {
        "module": "amphora-barrier-corrosion-score",
        "primary_kpi": "blinded Kendall tau at metrics.barrier_index",
        "locked_target": (
            "Blinded four-track independent-panel comparison with Kendall tau >= 0.5 "
            "and superiority over solids-only and PVC-only hostile nulls; Phase 2 "
            "repeats with separate material lots and a separate laboratory."
        ),
        "external_dependency": "Independent blinded corrosion panels and four-track comparison data",
        "minimum_n": "NOT_SPECIFIED_IN_SOURCE (qualitative target only: a blinded four-track panel; no numeric minimum panel/system count is stated in mission.md)",
    },
    {
        "module": "amphora-cure-potlife-gate",
        "primary_kpi": "within-1.5x rate at metrics.unseen_benchmark",
        "locked_target": (
            "At least 10 genuinely external complete rows with no family/source "
            "overlap, at least 80% within 1.5x, and at least 10-point baseline lift; "
            "promotion also requires multi-temperature CRO batches."
        ),
        "external_dependency": (
            "Genuinely external complete gel-time rows and multi-temperature CRO "
            "batches; thirty-six independently mixed, owned coating pot-life runs "
            "plus packet-bound independent review"
        ),
        "minimum_n": "10 genuinely external complete gel-time rows (no family/source overlap) plus 36 independently mixed owned coating pot-life CRO runs",
    },
    {
        "module": "amphora-design-rule-score",
        "primary_kpi": "held-study directional accuracy at metrics.directional_score",
        "locked_target": (
            "Zero silent acceptance of malformed, unsupported, or unauthorized "
            "inputs before Phase 0; locked module-specific benchmark required for "
            "Phase 1."
        ),
        "external_dependency": "Eligible primary-study series with locked extraction and subgroup identifiers",
        "minimum_n": "NOT_SPECIFIED_IN_SOURCE (no numeric minimum study/series count stated in mission.md for the Phase-1 locked benchmark)",
    },
    {
        "module": "amphora-ingredient-library",
        "primary_kpi": "active ingredient coverage at metrics.ingredient_count",
        "locked_target": (
            "Zero silent acceptance of malformed, unsupported, or unauthorized "
            "inputs before Phase 0; locked module-specific benchmark required for "
            "Phase 1."
        ),
        "external_dependency": "Current supplier TDS/SDS/CoA records with grade, rights, and issuer binding",
        "minimum_n": "NOT_SPECIFIED_IN_SOURCE (no numeric minimum record count stated in mission.md)",
    },
    {
        "module": "amphora-ip-fto-guard",
        "primary_kpi": "unresolved category coverage at metrics.unresolved_technical_categories",
        "locked_target": (
            "Zero silent acceptance of malformed, unsupported, or unauthorized "
            "inputs before Phase 0; locked module-specific benchmark required for "
            "Phase 1."
        ),
        "external_dependency": "Qualified patent counsel, current jurisdictional search, and claim charts",
        "minimum_n": "NOT_SPECIFIED_IN_SOURCE; NOTE this blocker is predominantly a counsel/legal-service dependency, not a pure dataset -- included per the directive's literal 'promotion blocker names a missing dataset or measurement class' test because 'current jurisdictional search' and 'claim charts' are themselves label/measurement classes (patent-landscape records), flagged here rather than silently dropped",
    },
    {
        "module": "amphora-molecule-generator",
        "primary_kpi": "chemical validity at metrics.generated_count",
        "locked_target": (
            "At least 99% validity, 95% uniqueness, deterministic lineage, "
            "scaffold-held-out controls, and expert/synthesis-feasibility "
            "noninferiority before prospective closed-loop superiority is tested."
        ),
        "external_dependency": "Scaffold-held-out benchmark, expert review, and synthesis-feasibility controls",
        "minimum_n": "NOT_SPECIFIED_IN_SOURCE as a row/sample count; rate targets only (>=99% validity, >=95% uniqueness) with no stated denominator size",
    },
    {
        "module": "amphora-molecule-novelty",
        "primary_kpi": "novelty score at objective_values.novelty_score",
        "locked_target": (
            "Zero silent acceptance of malformed, unsupported, or unauthorized "
            "inputs before Phase 0; locked module-specific benchmark required for "
            "Phase 1."
        ),
        "external_dependency": "Frozen owned comparison corpus plus patent and synthesis review",
        "minimum_n": "NOT_SPECIFIED_IN_SOURCE (no numeric minimum corpus size stated in mission.md)",
    },
    {
        "module": "amphora-molecule-property",
        "primary_kpi": "known-answer accuracy at metrics.property_results",
        "locked_target": (
            "Zero silent acceptance of malformed, unsupported, or unauthorized "
            "inputs before Phase 0; locked module-specific benchmark required for "
            "Phase 1."
        ),
        "external_dependency": "Independent defined-molecule controls and measured commercial-grade EEW/AHEW",
        "minimum_n": "NOT_SPECIFIED_IN_SOURCE at the mission-level gate (module-internal KPIs elsewhere in this module do carry numeric n, e.g. the AHEW TDS asks in Q01, but the headline Phase-1 promotion gate itself states no numeric minimum)",
    },
    {
        "module": "amphora-molecule-role-ranker",
        "primary_kpi": "role-fit benchmark pass at objective_values.role_fit",
        "locked_target": (
            "Zero silent acceptance of malformed, unsupported, or unauthorized "
            "inputs before Phase 0; locked module-specific benchmark required for "
            "Phase 1."
        ),
        "external_dependency": "Independent expert role labels and candidate-bound grade evidence",
        "minimum_n": "NOT_SPECIFIED_IN_SOURCE (no numeric minimum label count stated in mission.md)",
    },
    {
        "module": "amphora-public-corrosion-benchmark",
        "primary_kpi": "paired baseline lift at metrics.unseen_benchmark",
        "locked_target": (
            "At least 30 independent systems, including 10 locked external "
            "systems; at least 10 percentage-point baseline lift with paired 95% "
            "confidence lower bound above zero."
        ),
        "external_dependency": "At least 30 independent systems including 10 locked external systems",
        "minimum_n": "30 independent coating systems, of which at least 10 must be locked external systems",
    },
    {
        "module": "amphora-viscosity-score",
        "primary_kpi": "external KU MAE at metrics.class_anchor_ku_proxy",
        "locked_target": (
            "At least 30 formulations across families and three temperatures; "
            "external KU MAE <= 5 KU and sag balanced accuracy >= 0.80."
        ),
        "external_dependency": "At least 30 measured formulations across families and three temperatures",
        "minimum_n": "30 formulations x 3 temperatures = 90 measured Krebs-Unit viscosity readings minimum",
    },
    {
        "module": "amphora-sourceability-ehs",
        "primary_kpi": "evidence question accuracy at gates.sourceability_status",
        "locked_target": (
            "Zero silent acceptance of malformed, unsupported, or unauthorized "
            "inputs before Phase 0; locked module-specific benchmark required for "
            "Phase 1."
        ),
        "external_dependency": "Current candidate- and issuer-bound supplier declarations and lot evidence",
        "minimum_n": "NOT_SPECIFIED_IN_SOURCE (no numeric minimum declaration/lot count stated in mission.md)",
    },
]

blocker_rows = []
for i, b in enumerate(PROMOTION_BLOCKERS, start=1):
    row = {
        "row_id": f"B{i:02d}",
        "source_type": "pre_tier0_promotion_blocker+lab_in_the_loop_spec",
        "source_type_note": (
            "Collapsed: this module's own locked promotion-gate target text is the "
            "only lab-in-the-loop experiment specification referencing an external "
            "corpus/comparator/label source currently published anywhere in the tree "
            "for this module (verified by a full-tree search this fire for a distinct "
            "test-plan/protocol document; none found outside mission.md and the "
            "generic evidence/phase0/promotion/policy.v1.json gate-name lists, which "
            "carry no dataset-specific content)."
        ),
        "module": b["module"],
        "missing_measurement_or_label_class": (
            f"primary KPI: {b['primary_kpi']}. external dependency/delay stated in "
            f"mission.md: {b['external_dependency']}."
        ),
        "minimum_n": b["minimum_n"],
        "measurement_standard": (
            f"locked promotion-gate target (mission.md '## KPI register and "
            f"promotion gates'): {b['locked_target']} | split discipline stated "
            f"module-wide: group/time/source-safe splits, computed values labeled "
            f"computed, candidate evidence kept separate from public context, "
            f"subgroup reporting and calibrated intervals required wherever the "
            f"locked KPI is empirical."
        ),
        "qualifying_dataset_requirements": (
            f"Must satisfy the locked target verbatim: {b['locked_target']} Must be "
            f"genuinely external (no family/source overlap with training/reference "
            f"data already held), group/time/source-safe split-compatible, and "
            f"either a named-standard/expert-CRO/primary-literature/simple-physical/"
            f"hostile-null baseline comparator per the module's stated promotion "
            f"discipline, or the raw measurement rows a comparator would be built from."
        ),
        "source_ref": {
            "path": f"{b['module']}/docs/mission.md, section '## KPI register and promotion gates'",
            "phase_at_snapshot": "PRE_PHASE_0",
            "operational_readiness_field": "read directly from mission.md front-matter this fire",
        },
        "snapshot_date": SNAPSHOT_DATE,
    }
    blocker_rows.append(row)

# ---------------------------------------------------------------------------
# Source 4: MODELED/ASSUMED recipe elements -- explicit empty-set finding
# ---------------------------------------------------------------------------
modeled_assumed_recipe_elements = {
    "row_id": "R01",
    "source_type": "modeled_or_assumed_recipe_element",
    "finding": "EMPTY_SET",
    "attestation": (
        "A full-tree search of mvp20-split this fire (excluding .venv/ and target/ "
        "build artifacts) for any Candidate Formulation Package, recipe blueprint, "
        "bill-of-materials, or per-element evidence-tier crosswalk (Section 7 of "
        "AMPHORA-DIRECTIVE-2026-08-09) found none: no file anywhere in the tree "
        "carries a MODELED or ASSUMED per-element evidence tier tag outside this "
        "module's own audit/diagnostic fixtures. Mandate B (Candidate Formulation) "
        "has not run yet for this directive. This is consistent with, and confirms, "
        "the item's own stated module-serialization design: 'folding CF-TIER's "
        "later deltas into the register is DR-FRESH's run-2 obligation, not this "
        "item's -- module serialization means this register closes before CF-TIER "
        "exists.' Per directive rule 7 (RECON MODE) and Section 2, an empty result "
        "is a valid and reportable answer, not silent padding: there are zero "
        "MODELED/ASSUMED recipe elements published at this register's snapshot "
        "date to fold in, and this row states that explicitly rather than omitting "
        "the category."
    ),
    "search_method": (
        "grep -rl for tier/evidence-tier MODELED|ASSUMED markers plus a filename "
        "sweep for recipe/formulation-package/candidate-formulation/BOM-named "
        "files across the whole mvp20-split tree, run this fire; zero qualifying "
        "hits outside build tooling/dependency noise (ase/ turbomole test fixtures, "
        "sboms/ package metadata, unrelated to this portfolio)."
    ),
    "snapshot_date": SNAPSHOT_DATE,
}

all_rows = queue_rows + blocker_rows

register = {
    "schema": "amphora.dataset-recon.gap-register.v1",
    "campaign_item_id": "DR-GAP",
    "module": "amphora-dataset-recon",
    "framing": "AUDIT-ONLY",
    "snapshot_date": SNAPSHOT_DATE,
    "methodology": {
        "source_categories": [
            "every open data-acquisition-queue ask (data-acquisition-queue.jsonl on xbabe1, snapshot sha256 below)",
            "every Pre-Tier-0 (phase == PRE_PHASE_0) module whose promotion blocker names a missing dataset or measurement class (mission.md 'External dependency or delay' bullets)",
            "every lab-in-the-loop experiment specification referencing an external corpus, comparator, or label source (collapsed into the promotion-blocker rows this snapshot: no distinct spec document exists yet, declared not silent)",
            "every MODELED/ASSUMED recipe element already published at the snapshot date (empty set this snapshot, declared as row R01)",
        ],
        "pre_tier_0_definition_used": "phase == 'PRE_PHASE_0' as read verbatim from each module's docs/mission.md front-matter JSON, enumerated across all 29 amphora-* modules this fire",
        "pre_tier_0_modules_found": [b["module"] for b in PROMOTION_BLOCKERS],
        "pre_tier_0_modules_count": len(PROMOTION_BLOCKERS),
        "queue_asks_count": len(queue_rows),
        "queue_snapshot_sha256": queue_snapshot_sha256,
        "queue_snapshot_line_count": len(queue_lines),
        "modeled_assumed_recipe_elements_count": 0,
        "total_gap_rows": len(all_rows),
    },
    "rows": all_rows,
    "modeled_assumed_recipe_elements": modeled_assumed_recipe_elements,
}

out = WORK / "gap-register.v1.json"
out.write_text(json.dumps(register, indent=2, sort_keys=True))
print("WROTE", out)
print("total_gap_rows", len(all_rows))
print("register_sha256", sha(out.read_bytes()))
