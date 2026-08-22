#!/usr/bin/env python3
"""DR-STD-MAP fire-2 audit + repair.

Attack: an independent 5th-limb checker over the FIRE-1 signed mapping table
that the fire-1 4-limb checker never ran -- cross-row consistency between a
row's own stated evidentiary confidence ("page unreachable", "paywalled",
"pattern inference only", "not independently confirmed") and its
integrity_gap boolean. Fire-1's own convention (applied to CSN EN ISO 9227,
UNE-EN ISO 9227, UNE-EN ISO 12944, NP EN ISO 12944, NP EN ISO 9227) was:
weak/unreachable/pattern-only evidence => integrity_gap=true. GOST Р
56752-2015 carried textually identical weak-evidence language
("WebSearch-surfaced only ... both direct WebFetch attempts ... failed ...
NOT independently page-confirmed ... disclosed as a lower-confidence
mapping") but was signed with integrity_gap=false -- an internal
self-consistency defect in the SIGNED fire-1 artifact, undetected by any of
fire-1's 4 limbs (checked: census completeness, required-fields-or-gap,
scope-consistency, sourced-mapping -- none compare a row's own confidence
language against its gap flag).

This is a genuine, real (not planted) defect -> CLAIM_REFUTED. No positive
control is required for a refutation (only required for SURVIVED verdicts),
but the checker's specificity is still demonstrated: it fires exactly once
against the real fire-1 table (GOST row only) and fires zero times against
the fire-2 corrected table once that row is fixed with real fresh evidence.

This fire also closes 2 of fire-1's STATE.json open_items via fresh,
title/scope-level-only WebSearch (no acquisition):
  - KS D 9502 <-> ISO 9227 relationship (was: unresolved, integrity_gap=true)
  - CSN EN ISO 3001 / PN EN ISO 3001 census-gap row (was: one merged
    "unmapped_never_searched" row covering both designations)
"""
import base64
import copy
import hashlib
import json
import re
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
LEDGERS = MOD / "evidence/ledgers"
ITEM = MOD / "evidence/phase0/repairs/DR-STD-MAP"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T170001-3732775-ad6a5dd6f225"
PRIOR_FIRE_ID = "20260810T160002-3096524-741041e674fd"
RUN_ID = f"DR-STD-MAP-fire2-{FIRE_ID}"
DATE = "2026-08-10"

REFUTATION_CRITERION = (
    "Any ledger entry measured under a non-ASTM/ISO standard lacks a named "
    "closest equivalent, stated methodological deltas, and a comparability "
    "rating, or a mapped pair misstates a delta that the two standards' own "
    "texts contradict."
)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


# ---------------------------------------------------------------------------
# 0. Load fire-1's signed artifact and verify we are auditing the ACTUAL
#    signed table (sha256 must match what fire-1's DSSE receipt declared).
# ---------------------------------------------------------------------------
fire1_receipt_path = DONE / "dr-std-map-receipt.v1.dsse.json"
fire1_receipt = json.loads(fire1_receipt_path.read_bytes())
fire1_payload = json.loads(base64.b64decode(fire1_receipt["signature"]["payload"]))
fire1_mapping_table_sha_declared = fire1_payload["artifact_hashes"]["mapping-table.v1.json"]

v1_path = WORK / "mapping-table.v1.json"
v1_bytes = v1_path.read_bytes()
v1_sha_actual = sha(v1_bytes)
assert v1_sha_actual == fire1_mapping_table_sha_declared, (
    "mapping-table.v1.json has changed since fire-1 signed it -- "
    f"declared {fire1_mapping_table_sha_declared} actual {v1_sha_actual}"
)
v1 = json.loads(v1_bytes)

WEAK_EVIDENCE_MARKERS = [
    "not independently", "page-confirmed", "page unreachable", "paywall",
    "captcha", "connection refused", "pattern inference", "not separately searched",
    "no free scope text", "not independently confirmed", "lower-confidence",
    "lower confidence", "unconfirmed_no_equivalence_found",
]


def is_weak_evidence(row):
    txt = (str(row.get("astm_iso_equiv", "")) + " " +
           str(row.get("methodological_deltas", "")) + " " +
           str(row.get("comparability_rating", ""))).lower()
    return any(m in txt for m in WEAK_EVIDENCE_MARKERS)


def audit_gap_consistency(rows, label):
    """Independent 5th-limb checker: fire-1's own established convention is
    weak/unreachable/pattern-only evidentiary language => integrity_gap=true.
    Flag any row that states weak evidence but is NOT declared a gap."""
    violations = []
    for r in rows:
        # explicit non-applicable rows (abolished/accreditation-standard/
        # excluded-false-positive) are not equivalence claims at all --
        # exclude them from this limb, matching how limb-3 of fire-1's own
        # checker excludes N/A/NOT_FOUND markers.
        rating = str(r.get("comparability_rating", ""))
        if rating.startswith("not_applicable") or rating.startswith("excluded_"):
            continue
        if is_weak_evidence(r) and not r.get("integrity_gap"):
            violations.append({
                "limb": 5,
                "rule": "gap_flag_consistency_with_own_stated_evidence",
                "detail": (
                    f"{r['standard_id']}: comparability_rating/astm_iso_equiv/"
                    f"methodological_deltas text states weak/unreachable/"
                    f"pattern-inference-only evidence (same evidentiary class as "
                    f"rows this campaign DID flag integrity_gap=true), but this "
                    f"row is signed with integrity_gap=false -- inconsistent "
                    f"application of the table's own gap-declaration convention"
                ),
            })
    return {
        "label": label,
        "row_count": len(rows),
        "violation_count": len(violations),
        "violations": violations,
        "refutation_criterion_fired": len(violations) > 0,
    }


runA_v1 = audit_gap_consistency(v1["rows"], "fire1_signed_deliverable")
runB_v1 = audit_gap_consistency(v1["rows"], "fire1_signed_deliverable")
assert sha(canon(runA_v1)) == sha(canon(runB_v1)), "two-replay byte-stability gate FAILED on v1 audit"
assert runA_v1["refutation_criterion_fired"] is True, (
    "expected the audit to fire against the real fire-1 deliverable -- it did not; "
    "cannot license a refutation without an observed violation"
)
assert runA_v1["violation_count"] == 1, (
    f"expected exactly 1 violation (GOST Р 56752-2015) -- got {runA_v1['violation_count']}: "
    f"{runA_v1['violations']}"
)
assert "GOST" in runA_v1["violations"][0]["detail"] and "56752" in runA_v1["violations"][0]["detail"]

(WORK / "diagnostic.fire2.auditA.json").write_bytes(canon(runA_v1))
(WORK / "diagnostic.fire2.auditB.json").write_bytes(canon(runB_v1))

# ---------------------------------------------------------------------------
# 1. Fresh WebSearch evidence this fire (title/scope-level only, no
#    acquisition) closing 3 open items from fire-1's STATE.json.
# ---------------------------------------------------------------------------
FRESH_QUERIES = [
    {
        "language": "ru",
        "purpose": (
            "re-attempt GOST Р 56752-2015 <-> ISO 3001 confirmation after "
            "fire-1's direct WebFetch attempts against docs.cntd.ru/allgosts.ru "
            "failed (connection refused / CAPTCHA); also serves as this fire's "
            "own audit finding that the row was signed integrity_gap=false "
            "despite fire-1's own text disclosing it as unconfirmed"
        ),
        "query": "ГОСТ Р 56752-2015 эпоксидное число ISO 3001",
        "query_gloss_en": "GOST R 56752-2015 epoxy number ISO 3001",
        "tool": "WebSearch",
        "result_count": 5,
        "result_evidence_quote": (
            "ГОСТ Р 56752-2015 (ИСО 3001:1999) "
            "Смолы и соединения "
            "эпоксидные. Методы "
            "определения массовой "
            "доли эпоксидных групп "
            "и эпоксидного эквивалента "
            "-- the standard's own official title (docs.cntd.ru document 1200128340) "
            "carries '(ИСО 3001:1999)' directly in its designation, "
            "confirming direct ISO 3001:1999 adoption at the title/metadata level "
            "(introduced 2017-01-01). This is stronger evidence than fire-1 had "
            "(which relied on WebSearch-summary-only, having failed to WebFetch "
            "either source page)."
        ),
    },
    {
        "language": "ko",
        "purpose": (
            "resolve fire-1's open item: KS D 9502 <-> KS D ISO 9227:2005 "
            "relationship, previously an unresolved integrity_gap"
        ),
        "query": "KS D 9502 한국표준 규격 내용",
        "query_gloss_en": "KS D 9502 Korean Industrial Standard content",
        "tool": "WebSearch",
        "result_count": 10,
        "result_evidence_quote": (
            "KS D 9502 염수 분무 시험방법 (중성, "
            "아세트산 및 캐스분무 시험) -- neutral, "
            "acetic-acid and CASS salt-spray test method; kssn.net listing states "
            "it 'corresponds to ISO 9227:2006(MOD)' (latest KS D 9502 edition "
            "confirmed 2024-04-08 on kats.go.kr / standard.go.kr). This is a "
            "SEPARATE MOD-adoption vintage (2006) from the campaign's already-"
            "confirmed 'KS D ISO 9227:2005' disposition-ledger row (2005 "
            "vintage) -- both are genuine, distinct Korean designations that "
            "MOD-adopt different ISO 9227 editions; not a duplicate citation of "
            "the same document."
        ),
    },
    {
        "language": "cs",
        "purpose": (
            "close the merged census-gap row 'CSN EN ISO 3001 / PN-EN ISO 3001' "
            "(fire-1: unmapped_never_searched) for the Czech half"
        ),
        "query": "ČSN EN ISO 3001 epoxidová hodnota norma",
        "query_gloss_en": "CSN EN ISO 3001 epoxy value standard",
        "tool": "WebSearch",
        "result_count": 10,
        "result_evidence_quote": (
            "ČSN EN ISO 3001 - Plasty - Epoxidové sloučeniny - Stanovení "
            "epoxidového ekvivalentu (technickenormy.cz): 'prescribes a method "
            "for determining the epoxy equivalent ... this norm is a Czech "
            "version of the European standard EN ISO 3001:1999' -- direct "
            "national EN-ISO adoption, same pattern as DIN/NF/NEN/UNI EN ISO "
            "3001 rows already confirmed in fire-1. PN-EN ISO 3001 (Polish) "
            "was NOT searched this fire and remains an honest, declared "
            "integrity gap."
        ),
    },
]

sr_bytes_before = (LEDGERS / "search-record.v1.jsonl").read_bytes()
_sr_already_appended = any(
    json.loads(l).get("fire_id") == FIRE_ID
    for l in sr_bytes_before.decode("utf-8").splitlines() if l.strip()
)
sr_entry = {
    "date": DATE,
    "fire_id": FIRE_ID,
    "language_communities_touched": ["ru", "ko", "cs"],
    "purpose": [
        "DR-STD-MAP fire-2 (directive obligation DR-STD-MAP, AMPHORA-DIRECTIVE-2026-08-09 "
        "Section 4): audit fire-1's signed mapping table for internal gap-flag "
        "consistency, and close 3 of fire-1's STATE.json open_items with fresh "
        "title/scope-level-only WebSearch evidence (GOST R 56752-2015 re-confirmation, "
        "KS D 9502 <-> ISO 9227 resolution, CSN EN ISO 3001 confirmation)."
    ],
    "queries": FRESH_QUERIES,
    "no_acquisition_attestation": (
        "No dataset file, record set, table, standard full-text PDF, or bulk "
        "content was downloaded, cached, or scraped this fire. All 3 WebSearch "
        "calls returned ranked title/scope-level snippets only (standard "
        "designations, official titles, single scope sentences already "
        "published on standards-library index/store pages) -- never full "
        "standard text, never a bulk dataset. Nothing new landed on xbabe2 "
        "except this ledger line, the corrected mapping-table.v2.json, and "
        "signed receipts."
    ),
}
if not _sr_already_appended:
    with (LEDGERS / "search-record.v1.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(sr_entry, ensure_ascii=False) + "\n")
sr_bytes_after = (LEDGERS / "search-record.v1.jsonl").read_bytes()
if _sr_already_appended:
    appended_line_sha = sha(sr_bytes_after.splitlines()[-1] if not sr_bytes_after.endswith(b"\n")
                             else sr_bytes_after.rstrip(b"\n").split(b"\n")[-1])
else:
    appended_line_sha = sha(sr_bytes_after[len(sr_bytes_before):])

# ---------------------------------------------------------------------------
# 2. Build the corrected mapping-table.v2.json (supersede-never-rewrite:
#    v1 file is untouched; this is a brand-new file).
# ---------------------------------------------------------------------------
v2_rows = copy.deepcopy(v1["rows"])
gost_fix_note = (
    "FIRE-2 CORRECTION (supersedes fire-1 row of the same standard_id, "
    "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/done/"
    "dr-std-map-receipt.v1.dsse.json): fire-1 signed this row "
    "integrity_gap=false while its own methodological_deltas text disclosed "
    "'WebSearch-surfaced only ... NOT independently page-confirmed ... "
    "disclosed as a lower-confidence mapping' -- textually identical "
    "weak-evidence language to 5 other rows fire-1 correctly flagged "
    "integrity_gap=true (CSN EN ISO 9227, UNE-EN ISO 9227, UNE-EN ISO 12944, "
    "NP EN ISO 12944, NP EN ISO 9227). That was an internal "
    "gap-flag-consistency defect in the SIGNED fire-1 artifact -- detected "
    "this fire by an independent 5th-limb checker (fire-1's 4 limbs never "
    "compared a row's own confidence language to its gap flag). Fire-2 "
    "closes it with FRESH page-title-level evidence (docs.cntd.ru document "
    "1200128340's own official designation carries '(ИСО 3001:1999)' "
    "directly in the standard's title), which is independently sufficient "
    "to justify integrity_gap=false on its own merits -- the row is fixed, "
    "not merely re-labeled."
)
for r in v2_rows:
    if r["standard_id"].startswith("GOST Р 56752-2015"):
        r["astm_iso_equiv"] = (
            "ISO 3001:1999 -- CONFIRMED this fire via the standard's own official "
            "title/designation on docs.cntd.ru (document 1200128340): "
            "\"ГОСТ Р 56752-2015 (ИСО 3001:1999)\", "
            "i.e. the GOST designation itself carries the ISO number as a parenthetical "
            "in its formal title -- a direct-adoption marker confirmed at the "
            "official-designation level. (ISO 3001's own scope: determination of the "
            "epoxy equivalent.)"
        )
        r["comparability_rating"] = "iso_direct_adoption_confirmed_via_own_designation_title"
        r["integrity_gap"] = False
        r.pop("integrity_gap_reason", None)
        r["methodological_deltas"] = (
            "None stated -- direct adoption per the standard's own formal "
            "designation title."
        )
        r["fire2_correction_note"] = gost_fix_note
        r["source"] = {
            "kind": "fresh_websearch_fire2",
            "query": "ГОСТ Р 56752-2015 эпоксидное число ISO 3001",
            "fire_id": FIRE_ID,
        }
    elif r["standard_id"] == "KS D 9502":
        r["astm_iso_equiv"] = (
            "ISO 9227:2006(MOD) -- CONFIRMED this fire via kssn.net's own "
            "standard-detail listing ('대응국제표준: "
            "ISO 9227:2006(MOD)'). Method-class-comparable to ASTM B117. "
            "Distinct MOD-adoption vintage (2006) from the campaign's already-"
            "confirmed 'KS D ISO 9227:2005' row (2005 vintage) -- both are "
            "genuine Korean designations, not a duplicate. (ISO 9227's own "
            "scope: salt spray corrosion tests.)"
        )
        r["comparability_rating"] = "iso_direct_adoption_confirmed_mod_distinct_vintage"
        r["integrity_gap"] = False
        r.pop("integrity_gap_reason", None)
        r["methodological_deltas"] = (
            "MOD (modified) adoption per kssn.net's own stated designation; "
            "exact clause-level deltas not confirmed (no full text acquired, "
            "per no-acquisition discipline) -- same confidence tier as GOST "
            "34388-2018 and the KS D ISO 9227:2005 row above. Resolves fire-1's "
            "open STATE.json item: KS D 9502 and KS D ISO 9227:2005 are two "
            "distinct, genuine Korean designations MOD-adopting two different "
            "ISO 9227 editions (2006 vs 2005), not the same standard under two "
            "names and not a duplicate citation."
        )
        r["source"] = {
            "kind": "fresh_websearch_fire2",
            "query": "KS D 9502 한국표준 규격 내용",
            "fire_id": FIRE_ID,
        }

# split the merged CSN/PN EN ISO 3001 census-gap row into two rows
csn_pn_idx = next(i for i, r in enumerate(v2_rows)
                   if r["standard_id"] == "ČSN EN ISO 3001 / PN-EN ISO 3001")
old_row = v2_rows[csn_pn_idx]
csn_row = {
    "standard_class": "natl_en_iso",
    "standard_id": "ČSN EN ISO 3001",
    "published_standard": "ČSN EN ISO 3001 -- Plasty - Epoxidové sloučeniny - Stanovení epoxidového ekvivalentu",
    "astm_iso_equiv": (
        "ISO 3001:1999 -- CONFIRMED this fire via technickenormy.cz: "
        "'this norm is a Czech version of the European standard EN ISO "
        "3001:1999' -- direct national EN-ISO adoption, same pattern as the "
        "already-confirmed DIN/NF/NEN/UNI/NP EN ISO 3001 rows. (ISO 3001's "
        "own scope: determination of the epoxy equivalent.)"
    ),
    "comparability_rating": "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    "integrity_gap": False,
    "methodological_deltas": "None stated -- direct EN adoption, confirmed this fire.",
    "own_scope_category": ["EEW"],
    "source": {
        "kind": "fresh_websearch_fire2",
        "query": "ČSN EN ISO 3001 epoxidová hodnota norma",
        "fire_id": FIRE_ID,
    },
}
pn_row = {
    "standard_class": "natl_en_iso",
    "standard_id": "PN-EN ISO 3001",
    "published_standard": "PN-EN ISO 3001 (Polish national EN-ISO-adoption class; expected sibling of the confirmed DIN/NF/NEN/UNI/NP/CSN EN ISO 3001 rows)",
    "astm_iso_equiv": "NOT_SEARCHED this campaign in any language community.",
    "comparability_rating": "unmapped_never_searched",
    "integrity_gap": True,
    "integrity_gap_reason": (
        "Never independently searched in Polish or any other language "
        "community across this entire 9-language-fire campaign -- an honest, "
        "declared integrity gap per this item's own rule that an unmapped "
        "standard must be declared as one, not silently inferred from the "
        "CSN/DIN/NF/NEN/UNI/NP EN-ISO-adoption pattern."
    ),
    "own_scope_category": ["EEW"],
    "source": {
        "kind": "census_gap",
        "note": "split out of fire-1's merged 'ČSN EN ISO 3001 / PN-EN ISO 3001' row this fire; CSN half confirmed, PN half remains an open gap.",
    },
}
v2_rows[csn_pn_idx:csn_pn_idx + 1] = [csn_row, pn_row]

v2 = copy.deepcopy(v1)
v2["rows"] = v2_rows
v2["row_count"] = len(v2_rows)
v2["integrity_gap_count"] = sum(1 for r in v2_rows if r["integrity_gap"])
v2["fire_id"] = FIRE_ID
v2["date"] = DATE
v2["campaign_item_id"] = "DR-STD-MAP"
v2["supersedes"] = {
    "superseded_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v1.json",
    "superseded_sha256": v1_sha_actual,
    "superseded_deleted_or_modified": False,
    "reason": (
        "GOST Р 56752-2015 row's integrity_gap flag was inconsistent with its "
        "own stated evidentiary confidence (see audit violation above); "
        "KS D 9502 <-> ISO 9227 relationship was an unresolved open item; "
        "CSN/PN EN ISO 3001 merged census-gap row conflated a now-confirmable "
        "Czech half with a genuinely still-unsearched Polish half."
    ),
}

v2_bytes = canon(v2)
(WORK / "mapping-table.v2.json").write_bytes(v2_bytes)
v2_sha = sha(v2_bytes)

# Re-run the SAME 5th-limb audit against the corrected table -- specificity
# check: the checker should now fire ZERO times (not just always-fire).
runA_v2 = audit_gap_consistency(v2_rows, "fire2_corrected_deliverable")
runB_v2 = audit_gap_consistency(v2_rows, "fire2_corrected_deliverable")
assert sha(canon(runA_v2)) == sha(canon(runB_v2)), "two-replay byte-stability gate FAILED on v2 audit"
assert runA_v2["refutation_criterion_fired"] is False, (
    f"corrected table STILL has gap-consistency violations: {runA_v2['violations']}"
)
(WORK / "diagnostic.fire2.auditA_v2.json").write_bytes(canon(runA_v2))
(WORK / "diagnostic.fire2.auditB_v2.json").write_bytes(canon(runB_v2))

# ---------------------------------------------------------------------------
# 3. RETRACTION-INDEX.md
# ---------------------------------------------------------------------------
RETRACTION_PATH = ITEM / "done" / "RETRACTION-INDEX.md"
RETRACTION_PATH.parent.mkdir(parents=True, exist_ok=True)
retraction_line = (
    "| GOST Р 56752-2015 row signed integrity_gap=false in "
    "dr-std-map-receipt.v1.dsse.json (fire " + PRIOR_FIRE_ID + ") despite "
    "stating weak/unreachable evidentiary language identical to 5 rows "
    "correctly flagged integrity_gap=true | 5th-limb gap-flag-consistency "
    "audit, dr-std-map-fire2-receipt.v1.dsse.json (fire " + FIRE_ID + ") | "
    "mapping-table.v2.json (same receipt) | 2026-08-10 |\n"
)
header = (
    "# DR-STD-MAP retraction index\n\n"
    "Append-only. Never rewrite or delete a row.\n\n"
    "| claim | refuted-by | superseded-by | date |\n"
    "|---|---|---|---|\n"
)
if RETRACTION_PATH.exists():
    existing = RETRACTION_PATH.read_text(encoding="utf-8")
    if retraction_line not in existing:
        RETRACTION_PATH.write_text(existing + retraction_line, encoding="utf-8")
else:
    RETRACTION_PATH.write_text(header + retraction_line, encoding="utf-8")
retraction_bytes = RETRACTION_PATH.read_bytes()

# ---------------------------------------------------------------------------
# 4. Sign the fire-2 receipt.
# ---------------------------------------------------------------------------
directive_bytes = DIRECTIVE_MD.read_bytes()
directive_sha_actual = sha(directive_bytes)
assert directive_sha_actual == DIRECTIVE_SHA_EXPECTED, "directive md sha mismatch: %s" % directive_sha_actual

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

fire1_receipt_bytes = fire1_receipt_path.read_bytes()
fire1_receipt_sha = sha(fire1_receipt_bytes)

payload_obj = {
    "run_id": RUN_ID,
    "fire_id": FIRE_ID,
    "prior_fire_id": PRIOR_FIRE_ID,
    "date": DATE,
    "module": "amphora-dataset-recon",
    "campaign_item_id": "DR-STD-MAP",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "framing": "AUDIT-ONLY",
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": DIRECTIVE_SHA_EXPECTED,
    "directive_obligation": "DR-STD-MAP",
    "refutation_criterion_verbatim": REFUTATION_CRITERION,
    "refutation_criterion_restated_note": (
        "The literal criterion (missing a required field, OR a mapped pair "
        "misstating a delta the two standards' own texts contradict) is NOT "
        "the exact shape of what this fire found -- the GOST Р 56752-2015 "
        "row had all three required fields populated and did not misstate a "
        "delta contradicted by ISO 3001's own text. What this fire found is a "
        "violation of the item's own broader done_criterion/objective "
        "language ('An unmapped standard in the ledger is an integrity gap "
        "and must be declared as one') applied INCONSISTENTLY: this exact "
        "row's own stated evidence ('WebSearch-surfaced only ... NOT "
        "independently page-confirmed ... disclosed as a lower-confidence "
        "mapping') is textually identical to 5 other rows this same signed "
        "table correctly declared integrity_gap=true. An artifact that "
        "applies its own stated gap-declaration standard inconsistently to "
        "otherwise-identical evidence is not 'complete and accurate for its "
        "scope' as the item's claim asserts. Reporting CLAIM_REFUTED on this "
        "broader accuracy bar rather than silently declining to act, per "
        "this item's own anti-softening instruction and the precedent set by "
        "the DR-LANG-EU fire-2 spot-check (ts 2026-08-10T15:10:27Z, same "
        "module, same pattern of a real defect not literally matching the "
        "letter of a 5-clause criterion)."
    ),
    "refutation_criterion_observation": (
        "OCCURRED (on the broader accuracy bar, not the literal 4-limb "
        "criterion): fire-1's independent 5th-limb gap-flag-consistency audit, "
        "re-run twice for byte-stability against the ACTUAL signed "
        "mapping-table.v1.json (sha256 verified against the fire-1 DSSE "
        "receipt's own artifact_hashes declaration before auditing), found "
        "exactly 1 violation: GOST Р 56752-2015 signed integrity_gap=false "
        "while carrying the same weak-evidence language as 5 rows correctly "
        "flagged true. The same audit re-run against the fire-2 corrected "
        "table (mapping-table.v2.json) fires zero times, confirming the "
        "checker is specific (not an always-fire artifact) and that the fix "
        "actually resolves the flagged inconsistency."
    ),
    "attack": (
        "Independent 5th-limb checker over fire-1's SIGNED mapping table: "
        "cross-row consistency between a row's own stated evidentiary "
        "confidence language and its integrity_gap boolean, using the "
        "5 already-correctly-flagged rows (CSN EN ISO 9227, UNE-EN ISO 9227, "
        "UNE-EN ISO 12944, NP EN ISO 12944, NP EN ISO 9227) as the campaign's "
        "own precedent for what 'weak evidence' means. None of fire-1's 4 "
        "limbs (census completeness, required-fields-or-declared-gap, "
        "scope-consistency, sourced-mapping) perform this cross-row check."
    ),
    "verdict": "CLAIM_REFUTED",
    "fix_applied_this_fire": True,
    "repair_status": "fix_landed_and_reverified",
    "fresh_evidence_this_fire": {
        "gost_56752_2015": (
            "docs.cntd.ru document 1200128340's own official title carries "
            "'(ИСО 3001:1999)' directly in the GOST's formal designation -- "
            "resolved the row on its merits, independent of the consistency "
            "audit finding."
        ),
        "ks_d_9502": (
            "kssn.net standard-detail listing: KS D 9502 corresponds to "
            "ISO 9227:2006(MOD) -- distinct MOD-adoption vintage from the "
            "already-confirmed 'KS D ISO 9227:2005' row; resolves fire-1's "
            "open STATE.json item as two genuine distinct Korean designations, "
            "not a duplicate."
        ),
        "csn_en_iso_3001": (
            "technickenormy.cz: 'this norm is a Czech version of the European "
            "standard EN ISO 3001:1999' -- confirmed direct adoption, closing "
            "the Czech half of fire-1's merged CSN/PN census-gap row. The "
            "Polish half (PN-EN ISO 3001) remains honestly unsearched and is "
            "now its own explicit integrity_gap=true row."
        ),
    },
    "table_deltas": {
        "row_count_v1": v1["row_count"],
        "row_count_v2": v2["row_count"],
        "integrity_gap_count_v1": v1["integrity_gap_count"],
        "integrity_gap_count_v2": v2["integrity_gap_count"],
        "rows_reclassified_gap_true_to_false": ["KS D 9502"],
        "rows_evidence_strengthened_no_gap_flag_change": ["GOST Р 56752-2015 (was false, evidence now genuinely supports false)"],
        "rows_split": ["ČSN EN ISO 3001 / PN-EN ISO 3001 -> ČSN EN ISO 3001 (confirmed) + PN-EN ISO 3001 (new explicit gap)"],
    },
    "supersedes": v2["supersedes"],
    "artifact_hashes": {
        "mapping-table.v1.json (unchanged, audited in place)": v1_sha_actual,
        "mapping-table.v2.json": v2_sha,
        "diagnostic.fire2.auditA.json": sha((WORK / "diagnostic.fire2.auditA.json").read_bytes()),
        "diagnostic.fire2.auditB.json": sha((WORK / "diagnostic.fire2.auditB.json").read_bytes()),
        "diagnostic.fire2.auditA_v2.json": sha((WORK / "diagnostic.fire2.auditA_v2.json").read_bytes()),
        "diagnostic.fire2.auditB_v2.json": sha((WORK / "diagnostic.fire2.auditB_v2.json").read_bytes()),
        "search-record.v1.jsonl (appended line only)": appended_line_sha,
        "search-record.v1.jsonl (full file, after append)": sha(sr_bytes_after),
        "RETRACTION-INDEX.md (full file, after append)": sha(retraction_bytes),
        "prior_fire1_done_receipt (unchanged)": fire1_receipt_sha,
    },
    "artifact_paths": {
        "build_script": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/build_dr_std_map_fire2.py",
        "mapping_table_v1": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v1.json",
        "mapping_table_v2": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v2.json",
        "search_record": "amphora-dataset-recon/evidence/ledgers/search-record.v1.jsonl",
        "retraction_index": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/done/RETRACTION-INDEX.md",
    },
    "no_acquisition_attestation": (
        "No dataset file, record set, table, standard full-text PDF, or bulk "
        "content was downloaded, cached, or scraped this fire. 3 WebSearch "
        "calls returned ranked title/scope-level snippets only. Nothing new "
        "landed on xbabe2 except the search-record ledger line, "
        "mapping-table.v2.json, RETRACTION-INDEX.md, and this signed receipt."
    ),
    "confidentiality_attestation": (
        "No masked customer, CTO, or internal identity named anywhere in this "
        "receipt or its artifacts; all content is standards-body/public-"
        "literature role-class level."
    ),
    "open_items_remaining_for_a_future_fire": [
        "PN-EN ISO 3001 (Polish) never searched -- now its own explicit gap row.",
        "ČSN EN ISO 9227, UNE-EN ISO 9227, UNE-EN ISO 12944, NP EN ISO 12944, "
        "NP EN ISO 9227 remain honest pattern-inference-only integrity gaps "
        "(consistent with their own stated evidence -- this fire did not "
        "re-attempt those page-fetches).",
        "GB/T 6822/6748 and JIS K5551/5552/5553 ship-hull standards still have "
        "no confirmed ASTM/ISO equivalent across 9 language communities -- "
        "this campaign's own item notes SATURATED is now a defensible verdict "
        "for that specific sub-question if a future fire chooses to close it "
        "rather than search a 10th language.",
    ],
}

PAYLOAD_TYPE = "application/vnd.amphora.receipt+json"


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


payload_bytes = canon(payload_obj)
pae_bytes = pae(PAYLOAD_TYPE, payload_bytes)
sig = eval_sk.sign(pae_bytes)

# self-verify before declaring
pub = Ed25519PublicKey.from_public_bytes(eval_pub)
pub.verify(sig, pae_bytes)

envelope = {
    "payloadType": PAYLOAD_TYPE,
    "payload": base64.b64encode(payload_bytes).decode(),
    "signatures": [
        {"keyid": eval_key_id, "sig": base64.b64encode(sig).decode()}
    ],
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
}

DONE.mkdir(parents=True, exist_ok=True)
out_path = DONE / "dr-std-map-fire2-receipt.v1.dsse.json"
out_path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")

state_path = ITEM / "work" / "STATE.json"
state = json.loads(state_path.read_text())
if not any(f.get("fire_id") == FIRE_ID for f in state["fires"]):
    state["fires"].append({
        "fire_id": FIRE_ID,
        "date": DATE,
        "verdict": "CLAIM_REFUTED",
        "receipt": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/done/dr-std-map-fire2-receipt.v1.dsse.json",
        "row_count": v2["row_count"],
        "integrity_gap_rows": v2["integrity_gap_count"],
        "summary": (
            "Independent 5th-limb gap-flag-consistency audit found GOST Р "
            "56752-2015 signed integrity_gap=false in fire-1's table despite "
            "identical weak-evidence language to 5 rows correctly flagged true "
            "-- a real internal-consistency defect fire-1's 4 limbs never "
            "checked. Fixed with fresh evidence (docs.cntd.ru title-level "
            "confirmation), and closed 2 more open items (KS D 9502 = ISO "
            "9227:2006(MOD), distinct from the 2005-vintage row already "
            "confirmed; ČSN EN ISO 3001 confirmed, PN-EN ISO 3001 split out as "
            "its own honest gap). max_fires=2 reached for this item."
        ),
    })
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

print("OK")
print("v1_sha", v1_sha_actual)
print("v2_sha", v2_sha)
print("v1 row_count/gaps", v1["row_count"], v1["integrity_gap_count"])
print("v2 row_count/gaps", v2["row_count"], v2["integrity_gap_count"])
print("receipt", out_path)
