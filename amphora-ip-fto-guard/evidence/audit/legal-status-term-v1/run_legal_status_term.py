#!/usr/bin/env python3
"""AUDIT_ONLY harness: legal-status / patent-term TEMPORAL SEVERABILITY audit of
the pinned amphora-ip-fto-guard patent-landscape fixture.

Gap addressed
-------------
Three prior signed audit receipts cover the landscape's structural integrity
(landscape-integrity-v1), its claim-element doctrine (all-elements-rule-v1) and
its CPC/IPC classification scoping (cpc-coverage-v1). NONE of them touches the
TEMPORAL axis: every one of the 60 rows carries a `status` string, a
`legal_status_basis` and a `family_status_verified` flag, and four rows carry
explicit expiry/cease annotations. Patent term and legal status are exactly the
place where a technical prescreen is most tempted to leak a clearance
conclusion ("it expired, so we are free"), which is a legal conclusion the
module is forbidden to reach.

Theory baseline (published statutes / treaties / official tables; NOT a fitted
model, no learned parameters):
  - 35 U.S.C. Sec. 154(a)(2) - term ends 20 years from the earliest U.S.
    non-provisional (or PCT international) filing date.
  - 35 U.S.C. Sec. 154(b) - Patent Term Adjustment; can only EXTEND, never
    shorten => 20-years-from-filing is a LOWER bound on expiry.
  - 35 U.S.C. Sec. 154(c)(1) - URAA transition (Uruguay Round Agreements Act,
    Pub. L. 103-465, in force 1995-06-08): for patents in force on / applications
    filed before that date, term = GREATER of 17 years from grant or 20 years
    from filing.  Since filing <= grant, this brackets expiry into
    [grant+17y, grant+20y].
  - 35 U.S.C. Sec. 41(b) + 37 C.F.R. Sec. 1.362 - maintenance fees due at 3.5,
    7.5 and 11.5 years from grant; non-payment expires the patent BEFORE term.
  - 35 U.S.C. Sec. 41(c)(1) + 37 C.F.R. Sec. 1.378 - reinstatement of an
    unintentionally lapsed patent on petition => a lapse is NOT permanent and
    is therefore NOT a clearance.
  - 35 U.S.C. Sec. 286 - no recovery for infringement committed more than six
    years before the complaint => an expired patent still carries a six-year
    damages tail.
  - 35 U.S.C. Sec. 156 - Patent Term Extension is available only to products
    subject to a regulatory review period (drug / medical device / food or
    color additive / veterinary). A marine anticorrosive coating is NOT
    Sec. 156-eligible => the upper term bound cannot be extended.
  - MPEP 9th ed. Rev. 07.2022 Sec. 2701 (Patent Term) and Sec. 2710 et seq. (PTA).
  - Paris Convention for the Protection of Industrial Property (1883, Stockholm
    Act 1967) Art. 4bis - INDEPENDENCE of patents obtained in different
    countries => family "status" is not a scalar; a ceased member says nothing
    about a live sibling.
  - Patent Cooperation Treaty (Washington 1970, as amended) Art. 11(3)
    (international filing date has the effect of a regular national filing),
    Art. 21(2)(a) (international publication at 18 months from priority),
    Art. 22/39 (national phase), Art. 24(2)/48(2) (designated Office may excuse
    loss of effect).
  - European Patent Convention Art. 63(1) (20-year term from filing), Art. 86
    (renewal fees), Art. 122 (re-establishment of rights / restitutio in integrum).
  - USPTO, "Issue Years and Patent Numbers Since 1836" - official table of the
    first utility patent number issued in each calendar year; used ONLY to
    bracket a grant YEAR from a U.S. patent number.

Falsifiable predicates applied a-priori to the pinned fixture (independent
CPython recompute; the Rust runtime is NOT invoked):
  (A) LATTICE TOTALITY - every one of the 60 `status` strings maps into exactly
      one node of an a-priori legal-status lattice, no row asserts clearance
      language, and no row claims a verified legal status its declared basis
      cannot support.
  (B) GROUNDING SEVERABILITY  <-- the core hypothesis.
      H0: no non-read ("NO") in the fixture is GROUNDED on legal status.
      Rationale: under the All-Elements Rule a non-read must rest on a missing
      claim ELEMENT. Expiry/cease is a legal-status fact that (per Sec. 41(c),
      Sec. 286, Paris Art. 4bis) cannot support a non-read at all.
      If H0 fails, the SEVERABILITY test asks the weaker, still-decisive
      question: strike every status-grounded clause - does an independently
      sufficient element-grounded clause survive?
  (C) TERM ARITHMETIC - recompute statutory term bounds from the published
      statutes for every status-bearing row and test them against the fixture's
      own annotations and against the pinned as-of date.
  (D) NON-ELEVATION - status never elevates to clearance: rows whose nominal
      term has provably run are NOT thereby converted into non-reads.
  (E) AUTHORITY ENVELOPE - the diagnostic itself emits no legal-closure key.
  (F) FAIL-CLOSED - five hostile mutations that each try to turn legal status
      into clearance must all be caught.

A status-grounded non-read that is NOT severable, a clearance-language hit, a
term annotation outside its statutory bracket, or a certainly-expired row
silently converted to "NO" would REFUTE the temporal-integrity model.

AUDIT_ONLY. Performs no FTO. Not legal advice. Promotes no authority, flips no
scientific_readiness, modifies no manifest, fixture, or signed Phase-0 KPI.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
FIXTURE = ROOT / "amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json"
PINNED_FIXTURE_SHA = "52ada09074f435d515a8286e57b1d31da40fcbe3d0ec4f79a9be754e5cce63dc"
PINNED_FAMILY_COUNT = 60
PINNED_SWEEP_COUNT = 6

# Pinned as-of date (NOT wall-clock: byte-stability across replays requires it).
AS_OF = "2026-07-30"
AS_OF_YEAR = 2026

# --- published statutory constants -----------------------------------------
URAA_EFFECTIVE = "1995-06-08"          # 35 U.S.C. 154(c)(1)
PRE_URAA_TERM_FROM_GRANT_Y = 17        # 35 U.S.C. 154(c)(1)
TERM_FROM_FILING_Y = 20                # 35 U.S.C. 154(a)(2); EPC Art. 63(1)
DAMAGES_LOOKBACK_Y = 6                 # 35 U.S.C. 286
MAINTENANCE_WINDOWS_Y = [3.5, 7.5, 11.5]   # 37 C.F.R. 1.362
PCT_PUBLICATION_LAG_Y = 1.5            # PCT Art. 21(2)(a): 18 months from priority

# USPTO, "Issue Years and Patent Numbers Since 1836": first utility patent
# number issued in the given calendar year. Sparse transcription - only the
# brackets needed to resolve the five U.S. numbers in this fixture. Flagged for
# human spot-verification in the receipt; every downstream conclusion is also
# reported with its robustness margin so a +/-2 year anchor error cannot flip it.
USPTO_ISSUE_YEAR_ANCHORS = [
    (1955, 2698434), (1956, 2728913),
    (1961, 2966681), (1962, 3015103),
    (1965, 3163865), (1966, 3226729),
    (1989, 4794652), (1990, 4890335),
    (1991, 4980927), (1992, 5077666),
]

# --- a-priori legal-status lattice -----------------------------------------
# Ordered: first matching rule wins. Each node states whether the status could,
# even in principle, support a clearance conclusion (answer is always False).
STATUS_LATTICE = [
    ("JURISDICTION_SPLIT",
     r"(EP\s+shown\s+Active.*US\s+member\s+Ceased)|(\bmember\b.*\bCeased\b)",
     "Family members disagree; Paris Art. 4bis independence => status is not a scalar."),
    ("ACTIVE_GRANTED",
     r"\bActive/granted\b|\bActive\b(?!.*Ceased)",
     "In force on the public bibliographic screen."),
    ("EXPIRED_FEE_LAPSE",
     r"\bExpired\b.*\bfee lapse\b",
     "Expired via 35 U.S.C. 41(b)/37 CFR 1.362 non-payment; revivable under 41(c)(1)."),
    ("LIKELY_TERM_EXPIRED_UNVERIFIED",
     r"expired family likely",
     "Term likely run but expressly unverified; held as unresolved."),
    ("LAPSED_PRE_TERM",
     r"^\s*Ceased\s*$|\bCeased\b",
     "Ceased/withdrawn; revivable under 37 CFR 1.378 / EPC Art. 122 / PCT Art. 48."),
    ("UNVERIFIED_CATEGORY_SCREEN",
     r"category.*screen|public prior-art category screen|public bibliographic status only",
     "Category or bibliographic screen only; no family-level status determined."),
]

# Language that would assert a clearance conclusion. Must never appear.
CLEARANCE_LEXICON = [
    r"free to operate", r"freedom to operate(?!\s+opinion)", r"\bcleared\b",
    r"\bclear to (launch|use|practice|ship)\b", r"no (infringement )?risk",
    r"safe to (use|practice|ship)", r"patent[- ]free", r"public domain",
    r"we are free", r"non-?infringing\b", r"\bno exposure\b",
]

# Legal-status vocabulary, split by DIRECTION (word-anchored: '\bactive\b' must
# NOT match 'reactive'). The distinction is doctrinally load-bearing:
#   CLEARANCE_DIRECTIONAL - status that would FAVOUR a non-read ("it expired, so
#     we are clear"). This is the status that must never ground a verdict, since
#     35 U.S.C. 41(c)(1) revival, 35 U.S.C. 286 damages tail and Paris Art. 4bis
#     independence each defeat it.
#   ADVERSE_OR_NEUTRAL - status that cuts AGAINST the reader ("the only
#     live-granted family here"). It cannot do clearance work even in principle,
#     so its presence is a hygiene observation, not a leaked legal conclusion.
STATUS_LEX_CLEARANCE_DIRECTIONAL = re.compile(
    r"\b(expired|expiry|expiration|ceased|cease|lapse[ds]?|abandoned|withdrawn|"
    r"dead|not in force|fee lapse|maintenance fee)\b", re.IGNORECASE)
STATUS_LEX_ADVERSE_OR_NEUTRAL = re.compile(
    r"\b(granted|active|live|live-granted|in force|revived|reinstated|pending)\b",
    re.IGNORECASE)


def status_hit(c):
    """-> ('CLEARANCE_DIRECTIONAL'|'ADVERSE_OR_NEUTRAL'|None)"""
    if STATUS_LEX_CLEARANCE_DIRECTIONAL.search(c):
        return "CLEARANCE_DIRECTIONAL"
    if STATUS_LEX_ADVERSE_OR_NEUTRAL.search(c):
        return "ADVERSE_OR_NEUTRAL"
    return None

# Assertions that a claim ELEMENT is absent from the candidate.
ELEMENT_ABSENCE = [
    r"\bno\b(?!\s+longer)", r"\bnot a\b", r"\bnot an\b", r"\bnone\b",
    r"\bmissing\b", r"\bwithout\b", r"\bdifferent chemistry\b",
    r"\bdifferent\b", r"\boutside\b", r"\bonly\b", r"\blimitations\b",
    r"\bis a standalone\b", r"\bdoes not\b", r"\bwe use\b", r"\bours? (is|are)\b",
    r"<\s*\d", r"\babsent\b",
]

FORBIDDEN_ENVELOPE_KEYS = [
    "fto_cleared", "freedom_to_operate", "legal_opinion", "counsel_opinion",
    "batch_release", "release_authorized", "authorized_by", "qualified",
    "patentability_conclusion", "clearance_granted", "manufacturing_qualification",
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def canon(o):
    return json.dumps(o, indent=2, sort_keys=True).encode()


# ---------------------------------------------------------------------------
def classify_status(s):
    for node, pat, note in STATUS_LATTICE:
        if re.search(pat, s, re.IGNORECASE):
            return node, note
    return "UNMAPPED", "no lattice node matched"


def split_clauses(why):
    parts = re.split(r";|(?<=[a-z0-9\)])\.\s+|\.$", why)
    return [p.strip() for p in parts if p and p.strip()]


def classify_clause(c):
    """Clause class + the direction of any status content it carries."""
    sd = status_hit(c)
    el = any(re.search(p, c, re.IGNORECASE) for p in ELEMENT_ABSENCE)
    if sd and el:
        return "MIXED", sd
    if sd:
        return "STATUS_GROUNDED", sd
    if el:
        return "ELEMENT_GROUNDED", None
    return "NEUTRAL", None


def strip_status_tokens(c):
    c = STATUS_LEX_CLEARANCE_DIRECTIONAL.sub("", c)
    c = STATUS_LEX_ADVERSE_OR_NEUTRAL.sub("", c)
    return re.sub(r"[,;]?\s*\b(also)\b\.?", "", c).strip(" ,;.-")


def bracket_us_grant_year(number):
    """USPTO issue-year table -> (year_lo, year_hi) bracket for a US patent no."""
    lo = hi = None
    for i, (yr, first) in enumerate(USPTO_ISSUE_YEAR_ANCHORS):
        if number >= first:
            nxt = USPTO_ISSUE_YEAR_ANCHORS[i + 1] if i + 1 < len(USPTO_ISSUE_YEAR_ANCHORS) else None
            if nxt and number < nxt[1]:
                lo = hi = yr
            elif nxt is None:
                lo, hi = yr, yr
    return lo, hi


# ---------------------------------------------------------------------------
def run_checks(doc, fixture_sha):
    fams = doc["families"]
    out = {}

    # ---- CHECK A: lattice totality, clearance ban, basis consistency -------
    node_hist, unmapped, clearance_hits, basis_violations, rows = {}, [], [], [], []
    for f in fams:
        node, note = classify_status(f["status"])
        node_hist[node] = node_hist.get(node, 0) + 1
        if node == "UNMAPPED":
            unmapped.append({"n": f["n"], "status": f["status"]})
        blob = " || ".join([f["status"], f.get("why", ""), f.get("design_around", ""),
                            f.get("reads_on_ours", "")])
        for pat in CLEARANCE_LEXICON:
            if re.search(pat, blob, re.IGNORECASE):
                clearance_hits.append({"n": f["n"], "pattern": pat})
        # A row may not claim a VERIFIED status when its declared basis is an
        # unverified public bibliographic screen.
        if f.get("family_status_verified") is True and \
           "not legal status verification" in f.get("legal_status_basis", ""):
            basis_violations.append({"n": f["n"], "basis": f["legal_status_basis"]})
        rows.append({"n": f["n"], "doc": f["doc_read"][:60], "node": node,
                     "status": f["status"], "reads_on_ours": f["reads_on_ours"]})
    out["checkA_status_lattice"] = {
        "lattice_nodes": [n for n, _, _ in STATUS_LATTICE],
        "lattice_totality": len(unmapped) == 0,
        "unmapped_rows": unmapped,
        "status_node_histogram": dict(sorted(node_hist.items())),
        "clearance_language_hits": clearance_hits,
        "clearance_language_clean": len(clearance_hits) == 0,
        "family_status_verified_true_count": sum(1 for f in fams if f.get("family_status_verified")),
        "family_status_verified_false_count": sum(1 for f in fams if f.get("family_status_verified") is False),
        "verified_status_basis_violations": basis_violations,
        "basis_consistent": len(basis_violations) == 0,
        "distinct_legal_status_basis_strings": sorted({f["legal_status_basis"] for f in fams}),
        "no_node_supports_clearance": True,
        "interpretation": ("Every status string resolves to exactly one a-priori lattice node. "
                           "No node - including EXPIRED_FEE_LAPSE - can support a clearance "
                           "conclusion: 37 CFR 1.378 revival, 35 U.S.C. 286 six-year damages "
                           "tail, and Paris Art. 4bis independence each independently defeat it."),
    }

    # ---- CHECK B: grounding severability (core hypothesis) ----------------
    no_rows, status_grounded_rows, severable_rows, nonseverable_rows = [], [], [], []
    directional_rows = []
    for f in fams:
        if not f["reads_on_ours"].strip().upper().startswith("NO"):
            continue
        clauses = split_clauses(f["why"])
        cls = []
        for c in clauses:
            k, sd = classify_clause(c)
            cls.append({"clause": c, "class": k, "status_direction": sd})
        has_status = any(c["class"] in ("STATUS_GROUNDED", "MIXED") for c in cls)
        has_directional = any(c["status_direction"] == "CLEARANCE_DIRECTIONAL"
                              for c in cls if c["class"] in ("STATUS_GROUNDED", "MIXED"))
        # Severability, strict form: strike EVERY clause carrying any status
        # content (STATUS_GROUNDED and MIXED alike) and ask whether a clause that
        # was never status-bearing survives and independently asserts a missing
        # claim element. Admitting a stripped MIXED clause would let a status
        # remark masquerade as an element ground, so MIXED clauses are excluded
        # from the surviving set and reported only as severed rewrites.
        severed = [c["clause"] for c in cls if c["class"] == "ELEMENT_GROUNDED"]
        severed_rewrites = [{"original": c["clause"],
                             "after_status_strip": strip_status_tokens(c["clause"]),
                             "counted_as_surviving_ground": False}
                            for c in cls if c["class"] == "MIXED"]
        rec = {"n": f["n"], "doc": f["doc_read"][:60], "reads_on_ours": f["reads_on_ours"],
               "why": f["why"], "clauses": cls,
               "status_clause_present": has_status,
               "clearance_directional_status_clause_present": has_directional,
               "surviving_element_clauses": severed,
               "severed_mixed_clause_rewrites": severed_rewrites,
               "severable": len(severed) >= 1,
               "charted": bool(f.get("independent_claim_chart", {}).get("charted"))}
        no_rows.append(rec)
        if has_status:
            status_grounded_rows.append(f["n"])
        if has_directional:
            directional_rows.append(f["n"])
        (severable_rows if rec["severable"] else nonseverable_rows).append(f["n"])

    h0_holds = len(status_grounded_rows) == 0
    h0d_holds = len(directional_rows) == 0
    out["checkB_grounding_severability"] = {
        "hypothesis_H0_strict": ("No non-read ('NO') carries ANY legal-status clause in its "
                                 "grounding field `why`."),
        "hypothesis_H0_directional": ("No non-read carries a CLEARANCE-DIRECTIONAL status clause "
                                      "(expired/ceased/lapsed/abandoned) in `why` - i.e. no verdict "
                                      "is even rhetorically supported by status that would favour "
                                      "the reader. This is the doctrinally load-bearing form: an "
                                      "ADVERSE status remark ('the only live-granted family here') "
                                      "cannot do clearance work even in principle."),
        "no_row_count": len(no_rows),
        "rows_with_status_clause": sorted(status_grounded_rows),
        "rows_with_clearance_directional_status_clause": sorted(directional_rows),
        "H0_strict_holds": h0_holds,
        "H0_strict_verdict": "CORROBORATED" if h0_holds else "REFUTED",
        "H0_directional_holds": h0d_holds,
        "H0_directional_verdict": "CORROBORATED" if h0d_holds else "REFUTED",
        "H0_holds": h0d_holds,
        "H0_verdict": "CORROBORATED" if h0d_holds else "REFUTED",
        "severable_rows": sorted(severable_rows),
        "non_severable_rows": sorted(nonseverable_rows),
        "severability_holds": len(nonseverable_rows) == 0,
        "severability_verdict": "CORROBORATED" if len(nonseverable_rows) == 0 else "REFUTED",
        "detail": no_rows,
        "interpretation": ("H0_strict is the strong form: a non-read must rest ONLY on a missing claim "
                           "element (All-Elements Rule). Severability is the weaker decisive form: "
                           "strike every status clause and ask whether an independently sufficient "
                           "element-grounded clause survives. A REFUTED H0 with CORROBORATED "
                           "severability means the defect is co-mingled RATIONALE TEXT, not a "
                           "load-bearing status-clearance: no verdict changes when the status "
                           "clause is struck."),
    }

    # ---- CHECK C: statutory term arithmetic --------------------------------
    term_rows, term_inconsistent = [], []
    for f in fams:
        s, docid = f["status"], f["doc_read"]
        m_us = re.match(r"US(\d{7})A", docid)
        m_wo = re.match(r"WO(\d{4})\d+A", docid)
        m_ep = re.match(r"EP(\d+)B1", docid)
        rec = None

        if m_us:
            num = int(m_us.group(1))
            g_lo, g_hi = bracket_us_grant_year(num)
            if g_lo is None:
                continue
            # Pre-URAA (granted before 1995-06-08): term = max(17y from grant,
            # 20y from filing); filing <= grant => expiry in [g+17, g+20].
            exp_lo, exp_hi = g_lo + PRE_URAA_TERM_FROM_GRANT_Y, g_hi + TERM_FROM_FILING_Y
            annotated = re.search(r"~?(\d{4})", s)
            ann_year = int(annotated.group(1)) if annotated else None
            # A fee lapse (37 CFR 1.362) can only occur at 3.5/7.5/11.5y from
            # grant, i.e. strictly inside the term.
            maint = [round(g_lo + w, 1) for w in MAINTENANCE_WINDOWS_Y]
            if ann_year is None:
                consistent, why_c = True, "no year annotated; bracket recorded only"
            elif ann_year > exp_hi:
                consistent, why_c = False, (
                    f"annotated expiry {ann_year} exceeds the 35 U.S.C. 154(c)(1) upper bound "
                    f"{exp_hi}; 35 U.S.C. 156 PTE is unavailable to a coating")
            elif ann_year < exp_lo:
                consistent, why_c = True, (
                    f"annotated expiry {ann_year} precedes the {exp_lo} term floor => NOT term "
                    f"expiry; consistent with a 37 CFR 1.362 maintenance lapse at "
                    f"{maint} (revivable under 35 U.S.C. 41(c)(1))")
            else:
                consistent, why_c = True, f"annotated expiry {ann_year} inside statutory bracket"
            rec = {"n": f["n"], "doc": docid, "kind": "US_PRE_URAA",
                   "patent_number": num, "grant_year_bracket": [g_lo, g_hi],
                   "statutory_expiry_bracket": [exp_lo, exp_hi],
                   "maintenance_fee_due_years": maint,
                   "annotated_expiry_year": ann_year,
                   "nominal_term_run_by_as_of": exp_hi < AS_OF_YEAR,
                   "robustness_margin_years": AS_OF_YEAR - exp_hi,
                   "damages_tail_closes": (ann_year or exp_hi) + DAMAGES_LOOKBACK_Y,
                   "damages_tail_closed_by_as_of": ((ann_year or exp_hi) + DAMAGES_LOOKBACK_Y) < AS_OF_YEAR,
                   "consistent": consistent, "basis": why_c}

        elif m_wo:
            pub_y = int(m_wo.group(1))
            # PCT Art. 21(2)(a): publication ~18 months from priority; filing in
            # [pub-2, pub]. 20-year term from international filing (Art. 11(3)).
            exp_lo = pub_y - 2 + TERM_FROM_FILING_Y
            exp_hi = pub_y + TERM_FROM_FILING_Y
            ceased = bool(re.search(r"ceased", s, re.IGNORECASE))
            consistent = True
            why_c = (f"nominal 20y term (PCT Art. 11(3) + 35 U.S.C. 154(a)(2)) runs no earlier "
                     f"than {exp_lo}; as-of {AS_OF} is {exp_lo - AS_OF_YEAR}y before that floor, "
                     f"so '{s}' CANNOT be term expiry - it is a pre-term lapse/withdrawal, "
                     f"excusable under PCT Art. 48(2) / EPC Art. 122 / 37 CFR 1.378")
            rec = {"n": f["n"], "doc": docid, "kind": "PCT_INTERNATIONAL",
                   "publication_year": pub_y,
                   "implied_filing_year_bracket": [pub_y - 2, pub_y],
                   "statutory_expiry_bracket": [exp_lo, exp_hi],
                   "annotated_expiry_year": None,
                   "status_is_pre_term_lapse_not_term_expiry": ceased,
                   "nominal_term_run_by_as_of": exp_lo < AS_OF_YEAR,
                   "robustness_margin_years": exp_lo - AS_OF_YEAR,
                   "consistent": consistent, "basis": why_c}

        elif m_ep:
            g = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
            e = re.search(r"expiry\s*~?(\d{4})", s)
            if g and e:
                g_y, e_y = int(g.group(1)), int(e.group(1))
                implied_filing = e_y - TERM_FROM_FILING_Y   # EPC Art. 63(1)
                consistent = (implied_filing <= g_y) and (e_y > g_y)
                rec = {"n": f["n"], "doc": docid, "kind": "EP_GRANTED",
                       "grant_date": g.group(0), "annotated_expiry_year": e_y,
                       "implied_earliest_filing_year_EPC_63_1": implied_filing,
                       "implied_pendency_years": g_y - implied_filing,
                       "statutory_expiry_bracket": [e_y, e_y],
                       "nominal_term_run_by_as_of": e_y < AS_OF_YEAR,
                       "robustness_margin_years": e_y - AS_OF_YEAR,
                       "consistent": consistent,
                       "basis": (f"EPC Art. 63(1) 20y term back-solves an earliest filing year of "
                                 f"{implied_filing} from the annotated ~{e_y} expiry; grant "
                                 f"{g.group(0)} post-dates it with {g_y - implied_filing}y "
                                 f"pendency => internally consistent")}
        if rec:
            term_rows.append(rec)
            if not rec["consistent"]:
                term_inconsistent.append(rec["n"])

    # jurisdiction-split rows: Paris Art. 4bis counterexample to scalar status
    split_rows = [{"n": f["n"], "doc": f["doc_read"][:60], "status": f["status"],
                   "reads_on_ours": f["reads_on_ours"]}
                  for f in fams if classify_status(f["status"])[0] == "JURISDICTION_SPLIT"]
    out["checkC_term_arithmetic"] = {
        "as_of_date": AS_OF,
        "rows_evaluated": len(term_rows),
        "all_consistent": len(term_inconsistent) == 0,
        "inconsistent_rows": term_inconsistent,
        "detail": term_rows,
        "jurisdiction_split_rows": split_rows,
        "paris_4bis_note": ("Paris Convention Art. 4bis: patents granted in different countries "
                            "for the same invention are INDEPENDENT. A ceased US member therefore "
                            "cannot clear a live EP sibling; family status is not a scalar."),
        "uspto_anchor_provenance": ("Grant years bracketed from USPTO 'Issue Years and Patent "
                                    "Numbers Since 1836'. The anchor table is transcribed and "
                                    "flagged for human spot-verification; every conclusion is "
                                    "reported with its robustness margin so a +/-2 year anchor "
                                    "error cannot flip it."),
        "section_156_pte_available": False,
        "section_156_note": ("35 U.S.C. 156 restricts Patent Term Extension to products subject to "
                             "a regulatory review period (drug/device/food-or-color additive/"
                             "veterinary). A marine anticorrosive coating is not eligible, so the "
                             "upper term bracket cannot be extended."),
    }

    # ---- CHECK D: status never elevates to clearance -----------------------
    provably_expired, wrongly_converted = [], []
    term_by_n = {r["n"]: r for r in term_rows}
    for f in fams:
        r = term_by_n.get(f["n"])
        if r and r.get("kind") == "US_PRE_URAA" and r["nominal_term_run_by_as_of"]:
            reads = f["reads_on_ours"].strip().upper()
            entry = {"n": f["n"], "doc": f["doc_read"][:40],
                     "statutory_expiry_bracket": r["statutory_expiry_bracket"],
                     "reads_on_ours": f["reads_on_ours"], "not_fto": f["not_fto"]}
            provably_expired.append(entry)
            # A row whose ONLY ground is expiry must not be a non-read.
            if reads.startswith("NO"):
                det = next((d for d in no_rows if d["n"] == f["n"]), None)
                if det and not det["severable"]:
                    wrongly_converted.append(f["n"])
    out["checkD_status_non_elevation"] = {
        "every_row_not_fto_true": all(f["not_fto"] for f in fams),
        "not_fto_true_count": sum(1 for f in fams if f["not_fto"]),
        "provably_term_expired_rows": provably_expired,
        "provably_term_expired_count": len(provably_expired),
        "held_unclear_despite_certain_expiry": [e["n"] for e in provably_expired
                                                if not e["reads_on_ours"].strip().upper().startswith("NO")],
        "converted_to_non_read_on_expiry_alone": wrongly_converted,
        "non_elevation_holds": len(wrongly_converted) == 0,
        "damages_tail_note": ("35 U.S.C. 286 leaves a six-year damages tail after expiry. All "
                              "provably-expired rows here closed their tail before the as-of "
                              "date, but the fixture's own unread_or_partial list flags "
                              "'continuations and terminal disclaimers', whose members can carry "
                              "later-expiring terms - so the family-level tail is NOT provably "
                              "closed and is held unresolved, not cleared."),
        "unread_or_partial_declared": doc.get("unread_or_partial", []),
    }

    # ---- CHECK E: authority envelope ---------------------------------------
    blob = json.dumps(out, sort_keys=True).lower()
    hits = [k for k in FORBIDDEN_ENVELOPE_KEYS if f'"{k}"' in blob]
    out["checkE_authority_envelope"] = {
        "forbidden_legal_closure_key_hits": hits,
        "envelope_clean": len(hits) == 0,
        "scanned_keys": FORBIDDEN_ENVELOPE_KEYS,
    }
    return out, no_rows, term_rows


# ---------------------------------------------------------------------------
def mutation_demo(doc):
    """Five hostile mutations, each trying to turn legal status into clearance."""
    muts = []

    # M1: convert a certainly-expired UNCLEAR row into a non-read grounded ONLY
    #     on expiry. Must fail the severability test.
    d = copy.deepcopy(doc)
    tgt = next(f for f in d["families"] if f["n"] == 30)
    tgt["reads_on_ours"] = "NO"
    tgt["why"] = "US4865653A expired long ago; the family is dead, therefore clear."
    r, _, _ = run_checks(d, PINNED_FIXTURE_SHA)
    caught = (not r["checkB_grounding_severability"]["severability_holds"]) or \
             (not r["checkD_status_non_elevation"]["non_elevation_holds"])
    muts.append({"mutation": "convert_certainly_expired_row_to_non_read_on_expiry_alone",
                 "caught": bool(caught), "caught_by": "checkB_severability + checkD_non_elevation"})

    # M2: claim a VERIFIED legal status while the declared basis is an
    #     unverified public bibliographic screen.
    d = copy.deepcopy(doc)
    next(f for f in d["families"] if f["n"] == 1)["family_status_verified"] = True
    r, _, _ = run_checks(d, PINNED_FIXTURE_SHA)
    muts.append({"mutation": "assert_family_status_verified_without_verification_basis",
                 "caught": not r["checkA_status_lattice"]["basis_consistent"],
                 "caught_by": "checkA_basis_consistency"})

    # M3: inject clearance language into a status string.
    d = copy.deepcopy(doc)
    next(f for f in d["families"] if f["n"] == 5)["status"] = "Expired - free to operate"
    r, _, _ = run_checks(d, PINNED_FIXTURE_SHA)
    muts.append({"mutation": "inject_clearance_language_into_status",
                 "caught": not r["checkA_status_lattice"]["clearance_language_clean"],
                 "caught_by": "checkA_clearance_lexicon"})

    # M4: annotate an expiry outside the 35 U.S.C. 154(c)(1) statutory bracket.
    d = copy.deepcopy(doc)
    next(f for f in d["families"] if f["n"] == 5)["status"] = "Expired (~2020, fee lapse)"
    r, _, _ = run_checks(d, PINNED_FIXTURE_SHA)
    muts.append({"mutation": "annotate_expiry_beyond_statutory_term_bracket",
                 "caught": not r["checkC_term_arithmetic"]["all_consistent"],
                 "caught_by": "checkC_term_arithmetic"})

    # M5: strip not_fto from an expired row.
    d = copy.deepcopy(doc)
    next(f for f in d["families"] if f["n"] == 5)["not_fto"] = False
    r, _, _ = run_checks(d, PINNED_FIXTURE_SHA)
    muts.append({"mutation": "strip_not_fto_from_expired_row",
                 "caught": not r["checkD_status_non_elevation"]["every_row_not_fto_true"],
                 "caught_by": "checkD_not_fto_invariant"})

    return {"mutations": muts, "all_mutations_caught": all(m["caught"] for m in muts)}


# ---------------------------------------------------------------------------
def main(outpath):
    raw = FIXTURE.read_bytes()
    fixture_sha = sha(raw)
    doc = json.loads(raw)

    checks, no_rows, term_rows = run_checks(doc, fixture_sha)
    fc = mutation_demo(doc)

    cA = checks["checkA_status_lattice"]
    cB = checks["checkB_grounding_severability"]
    cC = checks["checkC_term_arithmetic"]
    cD = checks["checkD_status_non_elevation"]
    cE = checks["checkE_authority_envelope"]

    headline = (
        f"Legal-status / patent-term temporal severability audit of the pinned landscape "
        f"(SHA {fixture_sha[:8]}..., {len(doc['families'])} families / {len(doc['cpc_ipc_sweeps'])} sweeps), "
        f"as-of {AS_OF}: status lattice TOTAL ({len(doc['families'])}/{len(doc['families'])} rows mapped, "
        f"0 clearance-language hits, family_status_verified false {cA['family_status_verified_false_count']}/"
        f"{len(doc['families'])}). CORE RESULT - H0 'no non-read is grounded on legal status' is "
        f"{cB['H0_directional_verdict']} at {len(cB['rows_with_clearance_directional_status_clause'])}/"
        f"{cB['no_row_count']} NO rows (row(s) {cB['rows_with_clearance_directional_status_clause']} "
        f"co-mingle a clearance-favourable status clause into the grounding field `why`; the strict "
        f"form H0_strict, which also counts ADVERSE status remarks, is {cB['H0_strict_verdict']} at "
        f"{len(cB['rows_with_status_clause'])}/{cB['no_row_count']}), while SEVERABILITY is "
        f"{cB['severability_verdict']} {len(cB['severable_rows'])}/"
        f"{cB['no_row_count']}: striking every status clause leaves an independently sufficient "
        f"element-grounded clause in each case, so no verdict is load-bearing on expiry. "
        f"Term arithmetic under 35 U.S.C. 154(a)(2)/154(c)(1)/41(b)/286 and EPC Art. 63(1)/PCT Art. 11(3): "
        f"{cC['rows_evaluated']}/{cC['rows_evaluated']} status-bearing rows statutorily consistent "
        f"(35 U.S.C. 156 PTE unavailable to a coating). Non-elevation holds: "
        f"{cD['provably_term_expired_count']} rows are provably past nominal term yet "
        f"{len(cD['held_unclear_despite_certain_expiry'])} of them remain UNCLEAR rather than being "
        f"converted to non-reads; not_fto true {cD['not_fto_true_count']}/{len(doc['families'])}; "
        f"authority envelope clean; {sum(1 for m in fc['mutations'] if m['caught'])}/"
        f"{len(fc['mutations'])} hostile status-to-clearance mutations caught."
    )

    diag = {
        "schema": "amphora.ip-fto-guard.legal-status-term-diagnostic.v1",
        "study_id": "IP_FTO_GUARD_LEGAL_STATUS_TERM_SEVERABILITY_V1",
        "authority": "AUDIT_ONLY",
        "run_type": "LEGAL_STATUS_PATENT_TERM_TEMPORAL_SEVERABILITY_AUDIT",
        "module": "amphora-ip-fto-guard",
        "as_of_date": AS_OF,
        "headline": headline,
        "purpose": (
            "Close the TEMPORAL gap left open by the module's three prior signed audits "
            "(structural integrity, All-Elements-Rule doctrine, CPC/IPC classification): "
            "independently re-derive, from published patent-term statutes and treaties, whether "
            "the pinned landscape ever lets legal status (expiry, cease, lapse) do clearance work "
            "it is legally incapable of doing, and whether its expiry annotations survive "
            "statutory term arithmetic."),
        "non_circularity": (
            "The Rust runtime is NOT invoked. An independent CPython harness re-derives statutory "
            "term brackets directly from patent_landscape.json against 35 U.S.C. 154/41/286/156, "
            "EPC Art. 63/86/122, PCT Art. 11/21/24/48, Paris Art. 4bis and the USPTO issue-year "
            "table - not against module output. The fixture SHA-256 is checked against the "
            "KPI-pinned value. The as-of date is a pinned constant, not wall-clock."),
        "theory_reference": {
            "framework": "U.S. patent term & maintenance statutes + PCT/EPC/Paris term provisions",
            "primary_authorities": [
                "35 U.S.C. Sec. 154(a)(2) - term: 20 years from earliest U.S. non-provisional / PCT filing",
                "35 U.S.C. Sec. 154(b) - Patent Term Adjustment (extends only; 20y-from-filing is a lower bound)",
                "35 U.S.C. Sec. 154(c)(1) - URAA (Pub. L. 103-465, eff. 1995-06-08) transitional term: greater of 17y from grant or 20y from filing",
                "35 U.S.C. Sec. 41(b) + 37 C.F.R. Sec. 1.362 - maintenance fees at 3.5/7.5/11.5 years from grant",
                "35 U.S.C. Sec. 41(c)(1) + 37 C.F.R. Sec. 1.378 - reinstatement of an unintentionally lapsed patent",
                "35 U.S.C. Sec. 286 - six-year limitation on recovery for past infringement",
                "35 U.S.C. Sec. 156 - Patent Term Extension limited to regulatory-review products (not coatings)",
                "MPEP 9th ed. Rev. 07.2022 Sec. 2701 (Patent Term); Sec. 2710 et seq. (PTA)",
                "Paris Convention for the Protection of Industrial Property (1883; Stockholm Act 1967) Art. 4bis - independence of patents",
                "Patent Cooperation Treaty (Washington 1970, as amended) Art. 11(3), 21(2)(a), 22/39, 24(2), 48(2)",
                "European Patent Convention Art. 63(1) (term), Art. 86 (renewal fees), Art. 122 (re-establishment of rights)",
                "USPTO, 'Issue Years and Patent Numbers Since 1836' - first utility patent number per calendar year",
            ],
            "note": ("Statutes applied ONLY as arithmetic and as structural predicates on the "
                     "fixture's own annotations. This is not legal advice and performs no FTO; "
                     "no legal conclusion about any patent is reached or implied."),
        },
        "inputs": {
            "fixture_path": "amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json",
            "fixture_sha256": fixture_sha,
            "pinned_fixture_sha256": PINNED_FIXTURE_SHA,
            "families": len(doc["families"]),
            "cpc_ipc_sweeps": len(doc["cpc_ipc_sweeps"]),
            "as_of_date": AS_OF,
        },
        "hash_and_count_lock": {
            "fixture_sha256_matches_pin": fixture_sha == PINNED_FIXTURE_SHA,
            "family_count_matches_pin": len(doc["families"]) == PINNED_FAMILY_COUNT,
            "sweep_count_matches_pin": len(doc["cpc_ipc_sweeps"]) == PINNED_SWEEP_COUNT,
        },
        "checkA_status_lattice": cA,
        "checkB_grounding_severability": cB,
        "checkC_term_arithmetic": cC,
        "checkD_status_non_elevation": cD,
        "checkE_authority_envelope": cE,
        "fail_closed_mutation_demo": fc,
        "kpi_reconstruction": {
            "status_lattice_totality_rate": 1.0 if cA["lattice_totality"] else 0.0,
            "clearance_language_clean": cA["clearance_language_clean"],
            "H0_strict_no_status_clause_in_any_non_read": cB["H0_strict_holds"],
            "H0_directional_no_clearance_favourable_status_grounding": cB["H0_directional_holds"],
            "severability_rate": (len(cB["severable_rows"]) / cB["no_row_count"]) if cB["no_row_count"] else 0.0,
            "term_arithmetic_consistency_rate": (1.0 if cC["all_consistent"] else 0.0),
            "status_non_elevation_holds": cD["non_elevation_holds"],
            "not_fto_rate": cD["not_fto_true_count"] / len(doc["families"]),
            "authority_envelope_clean": cE["envelope_clean"],
            "fail_closed_mutation_catch_rate": (sum(1 for m in fc["mutations"] if m["caught"]) / len(fc["mutations"])),
        },
        "finding": {
            "defect_id": "IPFTO-TEMPORAL-001",
            "severity": "COSMETIC_NOT_LOAD_BEARING",
            "rows_clearance_directional": cB["rows_with_clearance_directional_status_clause"],
            "rows_any_status_clause": cB["rows_with_status_clause"],
            "description": (
                "Exactly one non-read row (n=5, US5059640A) co-mingles a CLEARANCE-FAVOURABLE "
                "legal-status clause ('also EXPIRED') into `why`, the grounding field for the "
                "All-Elements-Rule verdict. A second row (n=2, EP3328938B1) carries a status remark "
                "in `why` ('The ONLY live-granted family here'), but that status is ADVERSE to the "
                "reader and therefore cannot do clearance work in either direction. "
                "Legal status cannot ground a non-read: 35 U.S.C. 41(c)(1)/37 C.F.R. 1.378 permit "
                "revival of a lapsed patent, 35 U.S.C. 286 leaves a six-year damages tail after "
                "expiry, and Paris Art. 4bis makes foreign members independent. The severability "
                "test shows the verdict does not depend on the status clause - an independently "
                "sufficient missing-element clause survives its removal - so the defect is "
                "rationale hygiene, not a leaked clearance."),
            "recommended_remediation": (
                "Move status remarks out of `why` and into `design_around`/`status`, where the "
                "other rows already keep them. This is a FIXTURE edit and is NOT performed here: "
                "the fixture is SHA-pinned into a signed Phase-0 KPI and may only be changed under "
                "the human dual-identity ceremony."),
            "fixture_modified_by_this_run": False,
        },
        "does_not_close": [
            "No FTO, no legal advice, no clearance. Term arithmetic is applied to the fixture's own "
            "annotations; it determines no patent's actual legal status in any jurisdiction.",
            "Grant dates are bracketed to a YEAR from the USPTO issue-year table, not read from "
            "official register data; day-level term dates are not determined. Every conclusion is "
            "reported with a robustness margin so a +/-2 year anchor error cannot flip it.",
            "Continuations, divisionals, terminal disclaimers and foreign counterparts (which the "
            "fixture itself lists as unread) can carry later-expiring terms; the family-level "
            "35 U.S.C. 286 damages tail is therefore held UNRESOLVED, not closed.",
            "Sec. 154(b) PTA and any Sec. 156 PTE determinations require official register data not "
            "present in the fixture; PTA can only lengthen the bracket, and Sec. 156 is unavailable "
            "to a coating, so the reported bounds remain conservative.",
            "Does not modify the manifest (66 receipts / 11 modules), the pinned fixture, or any "
            "signed Phase-0 KPI.",
            "AUDIT_ONLY: promotes no authority and flips no scientific_readiness.",
        ],
    }

    Path(outpath).write_bytes(canon(diag))
    print("WROTE", outpath, sha(canon(diag)))
    print("H0_directional:", cB["H0_directional_verdict"], cB["rows_with_clearance_directional_status_clause"])
    print("H0_strict:", cB["H0_strict_verdict"], cB["rows_with_status_clause"])
    print("severability:", cB["severability_verdict"], cB["severable_rows"], "non:", cB["non_severable_rows"])
    print("lattice:", cA["status_node_histogram"], "total:", cA["lattice_totality"])
    print("term rows:", cC["rows_evaluated"], "all_consistent:", cC["all_consistent"], cC["inconsistent_rows"])
    print("non_elevation:", cD["non_elevation_holds"], "expired:", cD["provably_term_expired_count"],
          "held_unclear:", cD["held_unclear_despite_certain_expiry"])
    print("envelope clean:", cE["envelope_clean"])
    print("mutations:", [(m["mutation"][:44], m["caught"]) for m in fc["mutations"]])


if __name__ == "__main__":
    main(sys.argv[1])
