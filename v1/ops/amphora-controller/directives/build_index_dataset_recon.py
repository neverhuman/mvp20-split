#!/usr/bin/env python3
"""Build the machine index for AMPHORA-DIRECTIVE-2026-08-09
(Dataset Reconnaissance, Multilingual Literature & Candidate Formulation).

Unlike the 2026-08-05 directive, this document is objectives-and-constraints
prose with NO machine-parseable obligation table, so every obligation below is
authored here -- and every authored record carries a `source_heading` that MUST
exist verbatim in the live .md, or the build dies. That is the honesty device:
an obligation cannot cite a section the document does not have. (The 2026-08-05
builder's docstring CLAIMED this assert and did not implement it -- the
CORRECTIONS.md defect class. This one demonstrably does: fabricate a heading
and run the build.)

Statuses are then derived from the live campaign via reconcile.py, never
hand-asserted. Usage:  python3 build_index_dataset_recon.py
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reconcile import reconcile, validate  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MD_LOCAL = os.environ.get(
    "AMPHORA_DIRECTIVE_SOURCE",
    "/home/ubuntu/Dataset_Reconnaissance_and_Multilingual_Literature_Directive.md")
XB2_MD = "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
OUT = os.path.join(HERE, "2026-08-09-dataset-recon.index.json")
CAMPAIGN = os.environ.get("AMPHORA_CAMPAIGN_PATH", "/home/ubuntu/amphora-cron/campaign.json")
DIRECTIVE_ID = "AMPHORA-DIRECTIVE-2026-08-09"
RECON = "amphora-dataset-recon"
CRO = "amphora-cro-protocol-packager"
ENVELOPE_SRC = "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json"


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


MD_TEXT = open(MD_LOCAL, encoding="utf-8").read()
MD_SHA = sha(MD_LOCAL)

# The document's real headings; every obligation must anchor to one.
def O(id, section, source_heading, owner, module, title, done_criteria,
      attack=None, refutation_criterion=None, max_fires=None,
      unblock_condition=None, origin="founder-directive", note=None):
    assert source_heading in MD_TEXT, \
        "FABRICATED source_heading for %s: %r not in %s" % (id, source_heading, MD_LOCAL)
    o = {"id": id, "section": section, "source_heading": source_heading,
         "owner": owner, "module": module, "title": title,
         "done_criteria": done_criteria, "origin": origin,
         "campaign_items": [], "status": "to-file"}
    if attack: o["attack"] = attack
    if refutation_criterion: o["refutation_criterion"] = refutation_criterion
    if max_fires: o["max_fires"] = max_fires
    if unblock_condition: o["unblock_condition"] = unblock_condition
    if note: o["note"] = note
    return o


LANG = [
    ("ZH", "Chinese",  "CNKI/Wanfang-class indexes, GB/T standards annexes, CAS institute archives"),
    ("JA", "Japanese", "J-STAGE, NIMS/PoLyInfo-class national materials databases, JIS test-data annexes"),
    ("DE", "German",   "DIN annexes, Fraunhofer/DECHEMA archives, German-language coatings journals"),
    ("RU", "Russian",  "eLIBRARY/RSCI, GOST test-data annexes, institute report archives"),
    ("KO", "Korean",   "KCI, KS standards annexes, KRICT-class institute archives"),
    ("FR", "French",   "NF standards annexes, HAL/theses.fr, French-language corrosion literature"),
    ("IBERIAN", "Spanish and Portuguese", "SciELO-class regional indexes, national theses repositories"),
    ("CEE", "Polish and Czech", "national journal indexes and polytechnic theses repositories"),
    ("EU", "Dutch and Italian", "national repositories and coatings-institute archives"),
]

RECON_RULES = ("RECON-MODE rules apply (see prompt): read-to-evaluate ONLY -- no downloads, no "
               "dataset caching, no scraping loops; native-script citations preserved beside any "
               "romanization; translation-confidence rated, never silently accepted; units as "
               "published with conversions shown; every credited artifact is a DSSE receipt "
               "content-binding the ledger lines it appended.")

obligations = [
    # ----------------------------------------------------------- meta / probe
    O("PROBE-WEB", "meta", "## 4. Multilingual Scope (binding)", "LOOP", RECON,
      "Probe: what web reconnaissance can a headless fire actually do?",
      "Signed receipt reporting the fire's usable tool inventory (WebSearch/WebFetch/raw HTTP), "
      "one native-script query round-trip (Chinese or Japanese) with the native query string and "
      "a result sample quoted, and an explicit no-acquisition attestation. This receipt is the "
      "factual basis on which the DR-LANG items run full or degraded.",
      attack="Attempt each candidate access path in turn and record exactly what worked, what was "
             "refused, and what was unavailable, with the evidence inline.",
      refutation_criterion="The receipt claims a tool or access path that the transcript does not "
      "show being exercised, or omits one that was.",
      max_fires=2, origin="operator-derived",
      note="Operator-derived: the directive mandates multilingual search; nothing in the loop had "
           "ever verified the tooling exists headless. Not founder text."),

    # ------------------------------------------------------------- Mandate A
    O("DR-RUBRIC", "S6+S2", "## 6. Dataset Evaluation Dimensions (floor, not ceiling)", "LOOP", RECON,
      "Publish the evaluation rubric; prove it deterministic",
      "Signed rubric artifact covering at least the six mandated dimensions (gap fit, provenance & "
      "measurement quality, rights clarity, uniqueness, integrity risk, acquisition cost & "
      "friction), each with a scoring rule a second party could apply; byte-stable two-replay of "
      "the ranking over a frozen candidate snapshot. " + RECON_RULES,
      attack="Re-run the published rubric over the same frozen snapshot and attack determinism; "
             "then mutate one scored attribute in a snapshot copy (e.g. flip a license) and attack "
             "whether the rank moves as the rubric says it must.",
      refutation_criterion="Re-running the published rubric over the same frozen candidate snapshot "
      "yields a different ranking or verdict for any candidate, or any of the six mandated "
      "dimensions has no scoring rule a second party could apply.",
      max_fires=2),

    O("DR-GAP", "S3", "## 3. Gap-Derived Targeting", "LOOP", RECON,
      "Consolidate the gap register the search is anchored to",
      "Signed gap register in which every row states the four mandated facts: what measurement or "
      "label class is missing, at what minimum n, under what measurement standard, and what a "
      "qualifying dataset would have to contain. Sources: every open data-acquisition-queue ask, "
      "every Pre-Tier-0 promotion blocker naming a dataset, every lab-in-the-loop spec referencing "
      "an external corpus, and every MODELED/ASSUMED recipe element already published at the "
      "register's snapshot date. The recipe-gap coupling is circular by design: folding "
      "CF-TIER's later deltas into the register is DR-FRESH's run-2 obligation, not this "
      "item's -- module serialization means this register closes before CF-TIER exists. "
      + RECON_RULES,
      attack="Audit the register against its own declared sources: delete a known queue-derived gap "
             "from a copy and attack whether the completeness check fires; hunt for a queue ask, "
             "promotion blocker, or lab-spec corpus reference absent from the register.",
      refutation_criterion="Any gap row lacks one of the four mandated statements, or a data ask "
      "live in the queue at the register's snapshot date, a promotion blocker naming a "
      "dataset, or a MODELED or ASSUMED recipe element published before that snapshot is "
      "absent from the register.",
      max_fires=3),
] + [
    O("DR-LANG-%s" % code, "S4", "## 4. Multilingual Scope (binding)", "LOOP", RECON,
      "Native-language reconnaissance: %s literature" % name,
      "Dataset-ledger entries and search-record lines for the %s literature communities (%s and "
      "wherever the research leads), queried in native practitioner terminology -- not translated "
      "English keywords. Every entry carries the native-script citation, license as published, "
      "standard mapping, translation confidence, and the gap or recipe element it serves. An empty "
      "result for a gap is a valid, reportable answer. Previously-supplied candidates in these "
      "languages must be independently rediscovered or their absence explained. " % (name, repos)
      + RECON_RULES,
      attack="Spot-check the ledger and search record against the live sources: re-resolve "
             "citations, re-fetch license pages, compare recorded queries against what a "
             "practitioner would write, and check rediscovery recall against the known candidate "
             "list; corrupt one citation in a ledger copy and attack whether the audit fires.",
      refutation_criterion="A spot-check finds a claimed-searched repository with no recorded query "
      "and result sample, a native-language query that is a literal English translation, a cited "
      "source whose recorded license text differs from its live license page, a native-script "
      "citation that fails to resolve, or a previously-supplied candidate in this language that "
      "the fresh search neither rediscovered nor explained.",
      max_fires=2)
    for code, name, repos in LANG
] + [
    O("DR-STD-MAP", "S4", "## 4. Multilingual Scope (binding)", "LOOP", RECON,
      "Map foreign measurement standards to ASTM/ISO with comparability ratings",
      "Signed mapping table covering every non-ASTM/ISO standard cited by any ledger entry (GB/T, "
      "JIS, DIN, GOST, KS, NF classes at minimum): closest equivalent named, known methodological "
      "deltas stated, comparability rated. An unmapped standard in the ledger is an integrity gap "
      "and must be declared as one. " + RECON_RULES,
      attack="Cross-check mappings against the standards' own scopes; swap one mapping in a copy "
             "(assert a salt-spray protocol equals a viscosity method) and attack whether the "
             "audit rejects it.",
      refutation_criterion="Any ledger entry measured under a non-ASTM/ISO standard lacks a named "
      "closest equivalent, stated methodological deltas, and a comparability rating, or a mapped "
      "pair misstates a delta that the two standards' own texts contradict.",
      max_fires=2),

    O("DR-DISP", "S8B+S2", "## 8. Required Deliverables (complete set)", "LOOP", RECON,
      "Disposition Ledger: every candidate gets exactly one verdict",
      "First deliverable: a sha256-pinned candidate-intake manifest enumerating every "
      "previously-furnished source (each source named inside the 14 data-acquisition-queue lines, "
      "the six B-ASK asks R-D01..R-D06, and U-MLIP's Orb reference) -- 'every candidate' is only "
      "checkable against a closed input set. Then: every manifest candidate and every "
      "engine-discovered candidate receives exactly one of RECOMMENDED, CONDITIONAL (blocker named "
      "and routed to a human action), or REJECTED (specific disqualifying finding). 'Not selected' "
      "without a reason is not a permitted state. A RECOMMENDED entry with an empty serves field "
      "is a defect. Byte-stable replay over the same snapshot. " + RECON_RULES,
      attack="Remove one queue-derived candidate's verdict from a copy and attack whether the "
             "every-candidate check fires; hunt for a manifest candidate with zero or two "
             "verdicts, and for a RECOMMENDED entry serving nothing.",
      refutation_criterion="Any candidate in the pinned intake manifest or any engine-discovered "
      "candidate lacks exactly one verdict of RECOMMENDED, CONDITIONAL or REJECTED with a stated "
      "reason, or a RECOMMENDED entry has an empty serves field, or the disposition replay over "
      "the same snapshot is not byte-stable.",
      max_fires=3),

    O("DR-COVERAGE", "S8C", "## 8. Required Deliverables (complete set)", "LOOP", RECON,
      "Coverage Map: no gap left blank",
      "Signed gap-by-gap (and, once CF-TIER exists, recipe-element-by-element) map in which every "
      "row carries exactly one of: the best RECOMMENDED source, the best CONDITIONAL source, or an "
      "explicit conversion into a commissioned-measurement candidate for the lab-in-the-loop "
      "program. An empty search result converts; it never pads and never disappears. " + RECON_RULES,
      attack="Blank one gap's row in a copy and attack whether the map-completeness check fires; "
             "cross-check that every named source exists in the Dataset Ledger.",
      refutation_criterion="Any register gap or MODELED or ASSUMED recipe element has neither a "
      "best recommended source, a best conditional source, nor an explicit "
      "commissioned-measurement conversion, or names a source absent from the Dataset Ledger.",
      max_fires=2),

    O("DR-SEARCH-RECORD", "S8D+S4", "## 8. Required Deliverables (complete set)", "LOOP", RECON,
      "Search Record: auditable, extendable, language-list honest",
      "Signed assembly of the search record: rubric used, language communities and repository "
      "classes searched with the native-language query forms, AND the considered-and-excluded "
      "decision for language communities beyond the twelve named -- the directive says the list "
      "extends wherever research indicates activity, so the named twelve must never silently "
      "become a ceiling. Sufficient for a human to audit what was and was not looked at, and for "
      "the next run to extend rather than repeat. " + RECON_RULES,
      attack="Strip one repository's query log from a copy and attack whether the audit detects a "
             "ledger entry with no matching search provenance; check the extension decisions "
             "exist and are reasoned.",
      refutation_criterion="The record omits a language community or repository class that any "
      "ledger entry's own provenance shows was used, omits the native-language query forms, or "
      "omits the considered-and-excluded decision for language communities beyond the twelve named.",
      max_fires=2),

    O("DR-ANNEX", "S9", "## 9. Discovery Annex (separate, quarantined)", "LOOP", RECON,
      "Discovery Annex: quarantine holds",
      "Signed check that the annex exists (superior chemistries, alternative feedstocks, adjacent "
      "systems and adjacent-problem sources are REPORTED, not suppressed) and that the quarantine "
      "is airtight: no annex entry appears in the primary Dataset Ledger or primary recipe, and no "
      "primary-recipe element cites annex evidence. " + RECON_RULES,
      attack="Copy one annex chemistry into a primary-BOM copy and attack whether the disjointness "
             "check fires; grep the primary artifacts for annex identifiers.",
      refutation_criterion="Any annex entry also appears in the primary Dataset Ledger or the "
      "primary recipe, or any primary-recipe element cites an annex entry as its evidence, or a "
      "non-envelope-conforming chemistry appears outside the annex.",
      max_fires=2),

    O("DR-FRESH", "S10", "## 10. Cadence & Freshness", "LOOP", RECON,
      "Freshness: every run diffs against the last",
      "Every ledger carries snapshot_date, run_id and an explicit diff block against the prior run "
      "(new sources, changed licenses, superseded datasets, tier movements) -- run 1 must state "
      "'first run — no prior ledger' explicitly, which is itself checkable. No recommendation or "
      "recipe element is ever silently carried forward: re-verified or re-flagged. " + RECON_RULES,
      attack="Carry one stale entry forward unmarked in a copy and attack whether the diff check "
             "fires; verify run 1's explicit first-run declaration exists.",
      refutation_criterion="Any run's ledger lacks a snapshot date and an explicit diff block "
      "against the prior run or an explicit first-run declaration, or any prior recommendation "
      "appears unchanged without a re-verified or re-flagged mark, or run 2's register fails to "
      "fold in CF-TIER's MODELED and ASSUMED elements (DR-GAP's declared second pass).",
      max_fires=2, unblock_condition="Second sweep scheduled (run 2); run 1 satisfies only the "
      "first-run declaration, which DR-LANG receipts carry.",
      note="Filed blocked until a second sweep exists to diff against; the obligation is declared "
           "now so coverage accounting sees it."),

    # ------------------------------------------------------------- Mandate B
    O("CF-ARITH", "S7", "## 7. Candidate Formulation Package (Mandate B deliverable — floor, not ceiling)",
      "LOOP", "amphora-formulation-arithmetic",
      "Envelope arithmetic: the recipe lands its numbers, shown not asserted",
      "Signed artifact showing the mass balance and EEW/AHEW stoichiometry by which the candidate "
      "formulation lands the 1:1 volume mix ratio, 65±2%% volume solids, ≤340 g/L VOC, pot-life "
      "and DFT targets -- every envelope number cited by path+sha256 to %s, never restated "
      "freehand (thresholds are never relaxed, so the charter file is the only permitted source "
      "of them). Independent re-computation must reproduce the shown arithmetic." % ENVELOPE_SRC,
      attack="Re-derive the arithmetic independently; perturb one ingredient density in a BOM copy "
             "and attack whether the re-computation breaches a target and the check fires; diff "
             "every envelope constant against the charter file.",
      refutation_criterion="The shown mass-balance and stoichiometry, independently re-computed, "
      "fails to land the 1:1 volume mix, 65±2% volume solids, or ≤340 g/L VOC targets as cited "
      "from the charter, or any envelope number in the blueprint differs from that file.",
      max_fires=2),

    O("CF-BOM", "S7", "## 7. Candidate Formulation Package (Mandate B deliverable — floor, not ceiling)",
      "LOOP", CRO,
      "Formulation & BOM: every raw material, function, loading, source, tier",
      "Signed blueprint section: every raw material in both components (resin, curative, solvents, "
      "pigments, extenders, additives) with function, target % by weight, key grade/spec "
      "attributes, at least one candidate commercial source with the domestic-sourcing preference "
      "flagged, and an evidence tier on every numeric claim. Chemistry stays inside the two-"
      "component epoxy-polyamide solvent-borne envelope; superior non-conforming ideas go to the "
      "Discovery Annex.",
      attack="Delete one BOM line's EEW citation in a copy and attack whether the completeness "
             "check fires; hunt for an uncited or untiered numeric claim; check envelope "
             "conformance of every ingredient class.",
      refutation_criterion="Any BOM line lacks function, target weight percent, grade or spec "
      "attributes, or a candidate commercial source, or any numeric claim about an ingredient is "
      "uncited and untiered.",
      max_fires=3),

    O("CF-PROC", "S7", "## 7. Candidate Formulation Package (Mandate B deliverable — floor, not ceiling)",
      "LOOP", CRO,
      "Mixing, induction, application and bench-scale process",
      "Signed blueprint section: component A/B preparation, induction behavior, thinning limits, "
      "application parameters against the envelope's WFT/coverage/cure schedule, and the "
      "bench-scale mix/dispersion sequence with scale-sensitive steps flagged for the later pilot "
      "path.",
      attack="Remove the induction-time parameter from a copy and attack whether the envelope "
             "crosswalk fires; walk the envelope's application table and hunt for an uncovered "
             "parameter.",
      refutation_criterion="The mixing, induction and application section or the bench-scale "
      "sequence omits a parameter the envelope's WFT, coverage or cure schedule requires, or a "
      "scale-sensitive step is unflagged.",
      max_fires=2),

    O("CF-TIER", "S7+S1", "## 7. Candidate Formulation Package (Mandate B deliverable — floor, not ceiling)",
      "LOOP", CRO,
      "Per-element evidence tiers: the crosswalk that couples recipe and ledger",
      "Every ingredient choice, loading level and process parameter tagged MEASURED (cited primary "
      "data) / MODELED (method named) / ASSUMED (rationale stated), each with a confidence rating; "
      "every MODELED/ASSUMED element cross-references the Dataset Ledger entry or commissioned "
      "measurement that would harden it. This crosswalk is mandatory -- it is how the recipe and "
      "the ledger justify each other, and its gap deltas feed DR-GAP's second pass. Hidden "
      "uncertainty is a violation; declared uncertainty is the deliverable working as intended.",
      attack="Strip one element's cross-reference in a copy and attack whether the crosswalk check "
             "fires; hunt for an untagged element or a tag with no confidence rating.",
      refutation_criterion="Any ingredient choice, loading or process parameter lacks a MEASURED, "
      "MODELED or ASSUMED tag with a confidence rating, or any MODELED or ASSUMED element fails "
      "to cross-reference a resolving Dataset Ledger entry or commissioned measurement.",
      max_fires=2),

    O("CF-ALT", "S7", "## 7. Candidate Formulation Package (Mandate B deliverable — floor, not ceiling)",
      "LOOP", CRO,
      "Alternates: the lab tests a decision, not a guess",
      "Wherever evidence cannot distinguish candidate ingredients (two curatives, two thinner "
      "systems), the blueprint ships the primary plus ranked alternates with the discriminating "
      "experiment named.",
      attack="Merge two curative alternates into one unexplained pick in a copy and attack whether "
             "the check fires; hunt for an evidence-indistinguishable pair shipped without a "
             "discriminating experiment.",
      refutation_criterion="Any pair of evidence-indistinguishable candidates ships without ranked "
      "alternates and a named discriminating experiment.",
      max_fires=2),

    O("CF-TEST", "S7", "## 7. Candidate Formulation Package (Mandate B deliverable — floor, not ceiling)",
      "LOOP", CRO,
      "Pre-registered test plan and the data-capture template",
      "Signed protocol qualifying the system against the envelope and the relevant "
      "MIL-DTL-24441-class requirements, conforming to the portfolio's common transfer path: "
      "methods and standards named, acceptance thresholds and kill criteria locked before any "
      "measurement, splits declared, uncertainty quantified (not point-only) -- PLUS the "
      "candidate-bound data-capture template (measurements, conditions, deviations, outcomes, "
      "units specified) so bench results flow back to fine-tune the engine.",
      attack="Delete one kill criterion from a copy and attack whether the pre-registration "
             "completeness check fires; verify the capture template binds to the candidate and "
             "specifies units on every field.",
      refutation_criterion="The test plan lacks named methods and standards, pre-locked acceptance "
      "thresholds and kill criteria, declared splits, quantified uncertainty, or the "
      "candidate-bound unit-specified data-capture template.",
      max_fires=2),

    O("CF-RISK", "S7", "## 7. Candidate Formulation Package (Mandate B deliverable — floor, not ceiling)",
      "LOOP", CRO,
      "Known failure modes, application limits, mitigations",
      "Signed blueprint section: pinholing/wetting/film-build and pot-life risks specific to this "
      "recipe, the application-limit parameters most likely to be exceeded, and their mitigations. "
      "An element the engine cannot defend is reported as such with its resolving experiment -- an "
      "honest hole is compliant; a confident-looking guess is not.",
      attack="Drop the pot-life mitigation from a copy and attack whether the check fires; hunt "
             "for a named risk with no exceeded-parameter or no mitigation.",
      refutation_criterion="No failure-mode entry exists for pinholing, wetting, film-build or "
      "pot-life, or a named risk lacks the application-limit parameter most likely exceeded and "
      "its mitigation.",
      max_fires=2),

    O("CF-PACKET", "S7+S5", "## 5. Fixed Constraints (binding)", "LOOP", CRO,
      "Final assembly through CroProtocolPackageV2, locks intact",
      "The complete package assembled through the portfolio's CRO-packet path "
      "(CroProtocolPackageV2): execution_authorized false, all eight claim locks true, status "
      "frozen at DRAFT_FOR_CRO_FEASIBILITY_REVIEW, protocol_lock_sha256 recomputing from the "
      "packet's own canonical locked_numeric_thresholds (computed_protocol_lock_sha256), the "
      "packet citing every blueprint artifact by path+sha256 so the thresholds are content-bound "
      "to the blueprint they came from, full-detail chemistry marked LOCKED-INTERNAL, AUDIT-ONLY framing on every "
      "rendering. The packet is a draft for CRO feasibility review; only the human transfer path "
      "may execute it.",
      attack="Mutate one byte of the packet, set execution_authorized true, strip a claim lock, "
             "and attack whether the Rust validator rejects each (the same machinery T-02 used); "
             "verify the lock hash re-derives from the packet's canonical locked thresholds and "
             "that the cited blueprint sha256s match the blueprint files.",
      refutation_criterion="The assembled package validates with execution_authorized true, a "
      "claim lock stripped, a status other than DRAFT_FOR_CRO_FEASIBILITY_REVIEW, a "
      "protocol_lock_sha256 that does not recompute from the packet's own canonical locked "
      "numeric thresholds, or a cited blueprint sha256 that does not match the blueprint file.",
      max_fires=2),

    O("DR-D2-COVERAGE", "meta", "## 8. Required Deliverables (complete set)", "LOOP", RECON,
      "Sign the obligation-coverage table for THIS directive",
      "Signed receipt carrying the full obligation-coverage table for AMPHORA-DIRECTIVE-2026-08-09 "
      "(UNMAPPED and ORPHAN lists reported even when empty, directive cited by path+sha256, and a "
      "spot-check of >=3 closed obligations read from their actual receipts) -- so progress "
      "against this directive is signed evidence, not an assertion in a chat log.",
      attack="Cross-check the table against the live index and campaign; plant a fabricated "
             "closed flag in a copy and attack whether the spot-check catches it.",
      refutation_criterion="The coverage table omits an obligation present in the index, reports a "
      "closed status its underlying receipts do not support, or fails to report the UNMAPPED and "
      "ORPHAN lists.",
      max_fires=2, origin="operator-derived",
      note="Mirror of D-COVERAGE for the second directive. Not founder text."),

    # -------------------------------------------------- human and lab spine
    O("DR-RIGHTS", "S5+S8B", "## 5. Fixed Constraints (binding)", "HUMAN", None,
      "Counsel review of every CONDITIONAL disposition",
      "Every CONDITIONAL entry in the Disposition Ledger receives a counsel verdict on its named "
      "blocker (license ambiguity resolved by reading, not optimism); rights-before-enthusiasm is "
      "a human step by the directive's own authority ceiling.",
      unblock_condition="First CONDITIONAL dispositions exist (DR-DISP under way)."),
    O("DR-ACQ", "S5", "## 5. Fixed Constraints (binding)", "HUMAN", None,
      "Execute the next human action on RECOMMENDED entries",
      "The engine never acquires: each RECOMMENDED ledger entry names the exact next human action "
      "(request, license, transcription) and a human performs it. This obligation tracks that "
      "queue so the ledger's output is connected to motion.",
      unblock_condition="First RECOMMENDED entries exist in the Dataset Ledger."),
    O("CF-EXEC-REVIEW", "S5+S7", "## 5. Fixed Constraints (binding)", "HUMAN", None,
      "CRO feasibility review of the candidate package",
      "The draft packet (execution_authorized: false) goes through rights and safety review and "
      "CRO feasibility review on the human transfer path. No loop artifact authorizes execution.",
      unblock_condition="CF-PACKET assembled and validated."),
    O("CF-LAB-EXEC", "S1+S10", "## 1. Mandate (twin, coupled)", "LAB", CRO,
      "Bench execution and candidate-bound data return",
      "The wet lab mixes, applies and tests the recipe per CF-TEST's pre-registered protocol and "
      "returns results in the capture template under the portfolio's transfer path (two distinct "
      "signatures, candidate-bound); returned data moves recipe elements from MODELED/ASSUMED to "
      "MEASURED per Section 10, feeding the engine's next revision.",
      unblock_condition="CF-EXEC-REVIEW cleared and a counterparty contracted (B-COUNTERPARTIES)."),
]

reconcile(obligations, CAMPAIGN, DIRECTIVE_ID)
validate(obligations)

index = {
    "schema": "amphora.directive-index.v1",
    "directive": {
        "directive_id": DIRECTIVE_ID,
        "title": "Dataset Reconnaissance, Multilingual Literature & Candidate Formulation Directive",
        "prepared": "2026-08-09",
        "version": "v2 (template-first; adds the Candidate Formulation mandate)",
        "framing": "AUDIT-ONLY / EVIDENCE-ONLY: discovery, recommendation, and draft formulation "
                   "only — no acquisition, no execution authorization. Rights review and lab "
                   "execution remain human steps.",
        "host": "xbabe2",
        "root": os.environ.get("AMPHORA_TARGET_ROOT", "/home/ubuntu/amphora/build/mvp20-split"),
        "md_path": XB2_MD,
        "md_sha256": MD_SHA,
        "source_on_xbabe1": MD_LOCAL,
        # The directive's own reuse note (v2 header + closing): swap these two
        # parameters and Sections 1-2, 4, 6-10 are the standing scaffold for the
        # next partner program. Structural, so the swap is a parameter change.
        "template_parameters": {
            "envelope_source": ENVELOPE_SRC,
            "gap_inventory_sources": [
                os.environ.get("AMPHORA_QUEUE_PATH",
                               "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl"),
                "module promotion blockers (Pre-Tier-0)",
                "AMPHORA-DIRECTIVE-2026-08-05 Section C lab specifications",
                "CF-TIER MODELED/ASSUMED recipe elements (second pass)",
            ],
        },
    },
    "owner_classes": {
        "LOOP": "Autonomous — the lane fleet executes these.",
        "HUMAN": "Governance/rights — the loop is FORBIDDEN from executing these; it files and tracks them only.",
        "LAB": "Wet-lab execution — requires contracted counterparties and signed candidate-bound returns.",
    },
    "obligations": obligations,
}
with open(OUT, "w") as fh:
    json.dump(index, fh, indent=2, ensure_ascii=False)
json.load(open(OUT))

import collections
print("obligations:", len(obligations))
print("  by owner :", dict(collections.Counter(o["owner"] for o in obligations)))
print("  by status:", dict(collections.Counter(o["status"] for o in obligations)))
print("md_sha256 :", MD_SHA)
print("wrote", OUT)
