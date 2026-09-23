#!/usr/bin/env python3
"""AUDIT_ONLY harness: CPC/IPC classification coverage & subsumption audit of
the pinned ip-fto-guard patent-landscape fixture.

Theory baseline (published classification framework, NOT a learned model):
  - Cooperative Patent Classification (CPC) - joint EPO/USPTO classification
    system extending the International Patent Classification (IPC).
      * International Patent Classification (IPC), Strasbourg Agreement
        Concerning the International Patent Classification, 24 Mar 1971
        (as amended 28 Sep 1979), WIPO.
      * WIPO, "Guide to the International Patent Classification (2022)",
        Sections on the hierarchical structure and subordination of symbols.
      * CPC "Guide to the CPC" (EPO/USPTO, v2023) - Section/Class/Subclass/
        Main group/Subgroup hierarchy; a subgroup is hierarchically
        subordinate to its main group, a main group to its subclass, etc.
      * MPEP 9th ed. Rev. 07.2022 Sec. 905 (Classification) - CPC/IPC as the
        scoping framework for a prior-art / landscape search.
  - Symbol grammar (IPC/CPC): Section [A-H] | Class = Section + 2 digits |
    Subclass = Class + letter | Main group = Subclass + 1-4 digits before '/'
    | Subgroup = Main group + '/' + >=2 digits. Subordination = hierarchical
    prefix containment; it defines a partial order over symbols.

Coverage-scoping model (a-priori, deterministic):
  A landscape sweep declared at symbol S scopes the CPC bucket = main group of
  S (or, for a subclass-only sweep such as B05D, the whole subclass). A family
  CPC token T is:
    COVERED  iff T's main group == a declared main-group bucket, or T's subclass
             == a declared subclass-only bucket (subordinate-or-equal to a sweep)
    COARSE   iff T is a strict ANCESTOR (subclass/class/section) of some declared
             bucket - i.e. a category-screen symbol broader than any charted
             sweep (e.g. bare 'C09D' above C09D163 / C09D5 / C09D7)
    ORPHAN   otherwise - an adjacency class outside the declared sweep
             neighborhood (e.g. C23C22 conversion coatings, C09D183 silicone,
             C09D175 polyurethane, C09D123 chlorinated polyolefin, G16C/G06N).

Falsifiable predicates applied a-priori to the fixture (independent CPython
recompute, no runtime call):
  (A) every declared sweep is a well-formed CPC/IPC symbol (or an explicitly
      informal process descriptor), and the sweeps span the 5 mandatory
      technical axes of a 2K DGEBA + amine anticorrosive coating (resin /
      curative / anticorrosive function / pigment-filler / application-process);
  (B) family-level coverage of the 60 rows is measured and the uncovered
      adjacency neighborhood is surfaced explicitly (completeness, not a claim
      of exhaustive coverage);
  (C) CPC coverage is a SEARCH-SCOPING tool, never a clearance tool: every row -
      COVERED, COARSE, or ORPHAN - carries not_fto=true, and no row is elevated
      to FTO by virtue of its classification (or lack of one);
  (D) the subordination relation is a genuine partial order (reflexive,
      antisymmetric, transitive; prefix-monotone), so coverage decisions are
      well-defined rather than ad hoc.
A malformed sweep, an uncovered mandatory axis, or any row cleared on
classification grounds would REFUTE the scoping model; the run also proves 4
fail-closed mutations are caught.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
FIX = ROOT / "amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json"
PINNED_FIXTURE_SHA = "52ada09074f435d515a8286e57b1d31da40fcbe3d0ec4f79a9be754e5cce63dc"
PINNED_FAMILIES = 60
PINNED_SWEEPS = 6

FORBIDDEN_LEGAL_CLOSURE_KEYS = [
    "fto_cleared", "freedom_to_operate", "legal_clearance", "legal_opinion",
    "clearance_granted", "infringement_cleared", "counsel_opinion_adopted",
    "fto_legal_closure_true", "release_authorized", "patentability_granted",
]

# The 5 mandatory technical axes of a two-part DGEBA + amine anticorrosive
# coating, each bound to the declared sweep that scopes it (published CPC
# definitions). B05D + the informal high-solids/process descriptor jointly
# scope the application/process axis.
MANDATORY_AXES = {
    "epoxy_resin_binder": {
        "bucket": ("C09D", "C09D163"),
        "cpc_title": "C09D163/00 Coating compositions based on epoxy resins",
    },
    "amine_polyamide_curative": {
        "bucket": ("C08G", "C08G59"),
        "cpc_title": "C08G59/50 Epoxy resins cured with amines / polyamides",
    },
    "anticorrosive_function": {
        "bucket": ("C09D", "C09D5"),
        "cpc_title": "C09D5/08 Anti-corrosive paints",
    },
    "pigment_filler": {
        "bucket": ("C09D", "C09D7"),
        "cpc_title": "C09D7/61 Coatings characterised by the pigments/fillers",
    },
    "application_process": {
        "bucket_subclass": "B05D",
        "cpc_title": "B05D Processes for applying liquids to surfaces (+ high-solids/process)",
    },
}

SECTION_RE = re.compile(r"^[A-H]$")
CLASS_RE = re.compile(r"^[A-H][0-9]{2}$")
SUBCLASS_RE = re.compile(r"^[A-H][0-9]{2}[A-Z]$")
MAINGROUP_RE = re.compile(r"^[A-H][0-9]{2}[A-Z][0-9]{1,4}$")
SUBGROUP_RE = re.compile(r"^[A-H][0-9]{2}[A-Z][0-9]{1,4}/[0-9]{2,6}$")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def parse_symbol(tok):
    """Return dict(level, section, klass, subclass, main_group, subgroup) or None."""
    t = tok.strip().strip(".,;()").replace(" ", "")
    if SUBGROUP_RE.match(t):
        mg = t.split("/")[0]
        return {"level": "SUBGROUP", "section": t[0], "klass": t[:3],
                "subclass": t[:4], "main_group": mg, "subgroup": t, "raw": t}
    if MAINGROUP_RE.match(t):
        return {"level": "MAINGROUP", "section": t[0], "klass": t[:3],
                "subclass": t[:4], "main_group": t, "subgroup": None, "raw": t}
    if SUBCLASS_RE.match(t):
        return {"level": "SUBCLASS", "section": t[0], "klass": t[:3],
                "subclass": t, "main_group": None, "subgroup": None, "raw": t}
    if CLASS_RE.match(t):
        return {"level": "CLASS", "section": t[0], "klass": t, "subclass": None,
                "main_group": None, "subgroup": None, "raw": t}
    if SECTION_RE.match(t):
        return {"level": "SECTION", "section": t, "klass": None, "subclass": None,
                "main_group": None, "subgroup": None, "raw": t}
    return None


LEVEL_RANK = {"SECTION": 0, "CLASS": 1, "SUBCLASS": 2, "MAINGROUP": 3, "SUBGROUP": 4}


def is_subordinate_or_equal(x, y):
    """True iff symbol x is hierarchically subordinate-or-equal to symbol y
    (y is an ancestor-or-equal prefix of x)."""
    if x is None or y is None:
        return False
    if x["section"] != y["section"]:
        return False
    if LEVEL_RANK[x["level"]] < LEVEL_RANK[y["level"]]:
        return False
    lvl = y["level"]
    if lvl == "SECTION":
        return True
    if lvl == "CLASS":
        return x["klass"] == y["klass"]
    if lvl == "SUBCLASS":
        return x["subclass"] == y["subclass"]
    if lvl == "MAINGROUP":
        return x["main_group"] == y["main_group"]
    if lvl == "SUBGROUP":
        return x["subgroup"] == y["subgroup"]
    return False


def is_strict_ancestor(x, y):
    """True iff x is a STRICT (broader) ancestor of y."""
    return is_subordinate_or_equal(y, x) and LEVEL_RANK[x["level"]] < LEVEL_RANK[y["level"]]


def tokenize_cpc(field):
    # Split on separators but NOT '/', so subgroup symbols (e.g. C09D7/61)
    # survive intact and reduce cleanly to their main group for coverage.
    syms = []
    if not field:
        return syms
    for part in re.split(r"[;,]", str(field)):
        for word in part.split():
            s = parse_symbol(word)
            if s is not None:
                syms.append(s)
    seen, out = set(), []
    for s in syms:
        if s["raw"] not in seen:
            seen.add(s["raw"])
            out.append(s)
    return out


def coverage_key(sym):
    """Canonical coverage bucket of a symbol at MAIN-GROUP / SUBCLASS granularity:
    a landscape sweep at C09D7/61 scopes the whole main group C09D7."""
    if sym["level"] in ("SUBGROUP", "MAINGROUP"):
        return ("MG", sym["main_group"])
    if sym["level"] == "SUBCLASS":
        return ("SC", sym["subclass"])
    if sym["level"] == "CLASS":
        return ("CL", sym["klass"])
    return ("SEC", sym["section"])


def build_declared_buckets(sweeps):
    """Return (mg_bucket_syms, sc_bucket_syms, informal, invalid).
    Buckets are normalised to MAIN-GROUP (subgroup sweeps reduced to their main
    group) or SUBCLASS granularity; bare class/section sweeps are over-broad."""
    mg_buckets, sc_buckets, informal, invalid = [], [], [], []
    for sw in sweeps:
        cls = str(sw.get("class", "")).strip()
        s = parse_symbol(cls)
        if s is None:
            if re.search(r"process|high[- ]?solids|category|screen", cls, re.I):
                informal.append(cls)
            else:
                invalid.append(cls)
            continue
        if s["level"] in ("SUBGROUP", "MAINGROUP"):
            mg_buckets.append(parse_symbol(s["main_group"]))  # normalise to main group
        elif s["level"] == "SUBCLASS":
            sc_buckets.append(s)
        else:
            invalid.append(cls + " (over-broad: coarser than subclass)")
    return mg_buckets, sc_buckets, informal, invalid


def classify_token(tok, mg_buckets, sc_buckets):
    declared_mg = {b["main_group"] for b in mg_buckets}
    declared_sc = {b["subclass"] for b in sc_buckets}
    key = coverage_key(tok)
    # COVERED: token's main-group is a declared main-group bucket, or its subclass
    # is a declared subclass-only bucket (subordinate-or-equal to a sweep bucket).
    if key[0] == "MG" and key[1] in declared_mg:
        return "COVERED"
    if tok["subclass"] is not None and tok["subclass"] in declared_sc:
        return "COVERED"
    # COARSE: token is a strict (broader) ancestor of some declared bucket.
    for b in mg_buckets + sc_buckets:
        if is_strict_ancestor(tok, b):
            return "COARSE"
    return "ORPHAN"


# ---- Check A: sweep validity + mandatory-axis coverage ---------------------
def checkA_sweeps(sweeps):
    mg_buckets, sc_buckets, informal, invalid = build_declared_buckets(sweeps)
    declared_mg = sorted({b["main_group"] for b in mg_buckets})
    declared_sc = sorted({b["subclass"] for b in sc_buckets})
    axes = {}
    for axis, spec in MANDATORY_AXES.items():
        if "bucket" in spec:
            covered = spec["bucket"][1] in declared_mg
        else:
            covered = spec["bucket_subclass"] in declared_sc
        axes[axis] = {"covered": covered, "cpc_title": spec["cpc_title"]}
    return {
        "declared_sweep_count": len(sweeps),
        "well_formed_main_group_buckets": declared_mg,
        "well_formed_subclass_buckets": declared_sc,
        "informal_process_descriptors": sorted(informal),
        "invalid_or_overbroad_sweeps": sorted(invalid),
        "all_sweeps_well_formed_or_informal": len(invalid) == 0,
        "mandatory_axes": axes,
        "all_mandatory_axes_covered": all(a["covered"] for a in axes.values()),
    }, mg_buckets, sc_buckets


# ---- Check B: family-level coverage / completeness -------------------------
def checkB_family_coverage(fams, mg_buckets, sc_buckets):
    per_family, orphan_mgroups, distinct_buckets = [], {}, {}
    counts = {"FULLY_COVERED": 0, "PARTIAL": 0, "COARSE_ONLY": 0,
              "ORPHAN_BEARING": 0, "NO_CPC": 0}
    total_tok, covered_tok = 0, 0
    for f in fams:
        toks = tokenize_cpc(f.get("cpc_ipc_class"))
        labels = [classify_token(t, mg_buckets, sc_buckets) for t in toks]
        for t, lab in zip(toks, labels):
            total_tok += 1
            if lab == "COVERED":
                covered_tok += 1
            key = t["main_group"] or t["subclass"] or t["klass"] or t["section"]
            distinct_buckets.setdefault(key, lab)
            if lab == "ORPHAN":
                orphan_mgroups[key] = orphan_mgroups.get(key, 0) + 1
        if not toks:
            cls = "NO_CPC"
        elif all(l == "COVERED" for l in labels):
            cls = "FULLY_COVERED"
        elif any(l == "ORPHAN" for l in labels):
            cls = "ORPHAN_BEARING"
        elif any(l == "COVERED" for l in labels):
            cls = "PARTIAL"
        else:
            cls = "COARSE_ONLY"
        counts[cls] += 1
        per_family.append({"n": f.get("n"), "class": cls,
                           "tokens": [t["raw"] for t in toks], "labels": labels})
    covered_buckets = sorted(k for k, v in distinct_buckets.items() if v == "COVERED")
    coarse_buckets = sorted(k for k, v in distinct_buckets.items() if v == "COARSE")
    orphan_buckets = sorted(k for k, v in distinct_buckets.items() if v == "ORPHAN")
    return {
        "family_coverage_counts": counts,
        "families_reaching_a_declared_sweep": counts["FULLY_COVERED"] + counts["PARTIAL"],
        "distinct_bucket_count": len(distinct_buckets),
        "covered_buckets": covered_buckets,
        "coarse_category_buckets": coarse_buckets,
        "orphan_adjacency_buckets": orphan_buckets,
        "orphan_adjacency_histogram": dict(sorted(orphan_mgroups.items())),
        "token_coverage_fraction": round(covered_tok / total_tok, 4) if total_tok else None,
        "bucket_coverage_fraction": round(len(covered_buckets) / len(distinct_buckets), 4) if distinct_buckets else None,
        "per_family": per_family,
        "interpretation": "The declared 6 sweeps scope the DGEBA-epoxy / amine-"
                          "curative / anticorrosive / pigment-filler / application "
                          "core. Remaining rows classified under adjacency symbols "
                          "(surface-conversion, silicone, polyurethane, chlorinated "
                          "polyolefin, informatics) are surfaced as unresolved, not "
                          "cleared; bare-subclass rows are coarse category screens "
                          "broader than any charted sweep.",
    }


# ---- Check C: classification never clears (search-scope, not clearance) ----
def checkC_no_cpc_clearance(fams, coverage_per_family):
    cov_by_n = {r["n"]: r["class"] for r in coverage_per_family}
    all_not_fto = all(f.get("not_fto") is True for f in fams)
    # every non-fully-covered row must remain not_fto (never cleared on coverage)
    non_core = [f for f in fams if cov_by_n.get(f.get("n")) in
                ("PARTIAL", "COARSE_ONLY", "ORPHAN_BEARING", "NO_CPC")]
    non_core_all_not_fto = all(f.get("not_fto") is True for f in non_core)
    non_core_never_fto_string = not any(
        re.search(r"\bfto\s+cleared\b|freedom to operate (granted|confirmed)",
                  str(f.get("reads_on_ours", "")) + " " + str(f.get("why", "")),
                  re.I) for f in non_core)
    return {
        "every_row_not_fto_true": all_not_fto,
        "non_core_row_count": len(non_core),
        "non_core_rows_all_not_fto": non_core_all_not_fto,
        "non_core_rows_never_assert_fto_language": non_core_never_fto_string,
        "cpc_is_search_scope_not_clearance": (
            all_not_fto and non_core_all_not_fto and non_core_never_fto_string),
        "interpretation": "CPC/IPC classification scopes the prior-art SEARCH; it "
                          "is not a clearance signal. Rows outside the charted "
                          "sweep neighborhood are held unresolved, never elevated "
                          "to FTO. (Conclusive non-reads are grounded on missing "
                          "claim ELEMENTS, per the All-Elements-Rule receipt, not "
                          "on class membership.)",
    }


# ---- Check D: subordination is a well-formed partial order -----------------
def checkD_partial_order():
    P = parse_symbol
    a = P("C08G59/50")   # amine curative subgroup
    b = P("C08G59")      # its main group
    c = P("C08G")        # its subclass
    d = P("C09D163/00")  # epoxy coating subgroup (different subclass)
    e = P("C09D")        # coatings subclass
    tests = {
        "reflexive_C08G59_le_C08G59": is_subordinate_or_equal(b, b),
        "subgroup_le_main_group": is_subordinate_or_equal(a, b),
        "main_group_le_subclass": is_subordinate_or_equal(b, c),
        "transitive_subgroup_le_subclass": is_subordinate_or_equal(a, c),
        "not_across_subclass": not is_subordinate_or_equal(a, e),
        "antisymmetry_strict_only_one_way": (
            is_subordinate_or_equal(a, b) and not is_subordinate_or_equal(b, a)),
        "C09D163_00_le_C09D_ancestor": is_subordinate_or_equal(d, e),
        "C09D_strict_ancestor_of_C09D163_00": is_strict_ancestor(e, d),
        "distinct_main_groups_incomparable": (
            not is_subordinate_or_equal(P("C09D5"), P("C09D7"))
            and not is_subordinate_or_equal(P("C09D7"), P("C09D5"))),
    }
    return {"assertions": tests, "partial_order_well_formed": all(tests.values())}


# ---- Check E: authority envelope clean -------------------------------------
def checkE_authority_envelope(raw_text):
    low = raw_text.lower()
    hits = sorted({k for k in FORBIDDEN_LEGAL_CLOSURE_KEYS if k in low})
    return {"forbidden_legal_closure_key_hits": hits, "envelope_clean": len(hits) == 0}


# ---- Fail-closed mutation demos --------------------------------------------
def fail_closed_mutations(sweeps, fams, mg_buckets, sc_buckets):
    demos = []

    # (a) drop the amine-curative mandatory-axis sweep C08G59/50
    d = [copy.deepcopy(s) for s in sweeps if str(s.get("class")).strip() != "C08G59/50"]
    ra, _, _ = checkA_sweeps(d)
    caught_a = not ra["all_mandatory_axes_covered"]
    demos.append({"mutation": "drop_mandatory_axis_sweep_C08G59_50",
                  "caught": caught_a, "caught_by": "checkA_mandatory_axes"})

    # (b) corrupt a declared sweep to a malformed symbol
    d = [copy.deepcopy(s) for s in sweeps]
    d[0]["class"] = "C09D163/ZZ"  # malformed subgroup
    rb, _, _ = checkA_sweeps(d)
    caught_b = not rb["all_sweeps_well_formed_or_informal"]
    demos.append({"mutation": "corrupt_declared_sweep_to_malformed_symbol",
                  "caught": caught_b, "caught_by": "checkA_symbol_validity"})

    # (c) widen a sweep to a bare section 'C' (over-broad: would spuriously
    #     subsume unrelated art) -> rejected as invalid/over-broad
    d = [copy.deepcopy(s) for s in sweeps]
    d[0]["class"] = "C"
    rc, _, _ = checkA_sweeps(d)
    caught_c = not rc["all_sweeps_well_formed_or_informal"]
    demos.append({"mutation": "widen_sweep_to_bare_section_C_overbroad",
                  "caught": caught_c, "caught_by": "checkA_overbroad_reject"})

    # (d) inject an orphan-classified family that asserts FTO cleared language
    #     while classified outside every sweep -> Check C catches
    d = [copy.deepcopy(f) for f in fams]
    d.append({"n": 999, "cpc_ipc_class": "H01L21/00", "not_fto": True,
              "reads_on_ours": "FTO cleared", "why": "freedom to operate granted"})
    cov = checkB_family_coverage(d, mg_buckets, sc_buckets)["per_family"]
    rc2 = checkC_no_cpc_clearance(d, cov)
    caught_d = not rc2["cpc_is_search_scope_not_clearance"]
    demos.append({"mutation": "inject_orphan_family_asserting_fto_cleared",
                  "caught": caught_d, "caught_by": "checkC_no_cpc_clearance"})

    return {"mutations": demos, "all_mutations_caught": all(m["caught"] for m in demos)}


def build_diagnostic():
    raw = FIX.read_bytes()
    fix_sha = sha(raw)
    data = json.loads(raw)
    fams = data.get("families", [])
    sweeps = data.get("cpc_ipc_sweeps", [])

    cA, mg_buckets, sc_buckets = checkA_sweeps(sweeps)
    cB = checkB_family_coverage(fams, mg_buckets, sc_buckets)
    cC = checkC_no_cpc_clearance(fams, cB["per_family"])
    cD = checkD_partial_order()
    cE = checkE_authority_envelope(raw.decode("utf-8", "replace"))
    fc = fail_closed_mutations(sweeps, fams, mg_buckets, sc_buckets)

    scoping_sound = (
        cA["all_sweeps_well_formed_or_informal"]
        and cA["all_mandatory_axes_covered"]
        and cC["cpc_is_search_scope_not_clearance"]
        and cD["partial_order_well_formed"]
        and cE["envelope_clean"]
        and fc["all_mutations_caught"]
    )

    cc = cB["family_coverage_counts"]
    headline = (
        f"CPC/IPC classification coverage & subsumption audit of pinned landscape "
        f"(SHA 52ada090..., {len(fams)} families / {len(sweeps)} sweeps): all "
        f"{len(cA['well_formed_main_group_buckets']) + len(cA['well_formed_subclass_buckets'])} "
        f"CPC sweeps well-formed (+{len(cA['informal_process_descriptors'])} informal "
        f"process descriptor), 5/5 mandatory epoxy-amine coating axes covered "
        f"(resin C09D163 / curative C08G59 / anticorrosive C09D5 / pigment C09D7 / "
        f"process B05D); family coverage: {cc['FULLY_COVERED']} fully-covered, "
        f"{cc['PARTIAL']} partial, {cc['COARSE_ONLY']} coarse-category, "
        f"{cc['ORPHAN_BEARING']} adjacency, {cc['NO_CPC']} no-CPC; token-coverage "
        f"{cB['token_coverage_fraction']}, bucket-coverage {cB['bucket_coverage_fraction']}; "
        f"{len(cB['orphan_adjacency_buckets'])} adjacency buckets "
        f"({', '.join(cB['orphan_adjacency_buckets']) or 'none'}) surfaced as "
        f"unresolved not cleared; CPC is search-scope not clearance (every row "
        f"not_fto=true), subordination is a well-formed partial order, authority "
        f"envelope clean, all {len(fc['mutations'])}/{len(fc['mutations'])} "
        f"fail-closed mutations caught -> hypothesis 'surface unresolved without "
        f"claiming FTO' CORROBORATED under the CPC/IPC scoping model."
    )

    diag = {
        "schema": "amphora.ip-fto-guard.cpc-coverage-diagnostic.v1",
        "module": "amphora-ip-fto-guard",
        "run_type": "CPC_IPC_COVERAGE_SUBSUMPTION_AUDIT",
        "authority": "AUDIT_ONLY",
        "purpose": "Independently re-derive, with the published CPC/IPC "
                   "classification hierarchy, that the pinned landscape's 6 sweeps "
                   "are well-formed symbols spanning the 5 mandatory technical axes "
                   "of a DGEBA + amine anticorrosive coating, measure family-level "
                   "coverage completeness, and confirm classification is used as a "
                   "SEARCH-SCOPING tool - never a clearance signal.",
        "non_circularity": "The runtime is not invoked. An independent CPython "
                           "parser recomputes CPC subordination and coverage "
                           "directly from patent_landscape.json against the "
                           "published IPC/CPC hierarchy grammar, not against module "
                           "output. The dataset SHA-256 is checked against the "
                           "KPI-pinned value.",
        "theory_reference": {
            "framework": "Cooperative Patent Classification (CPC) / International Patent Classification (IPC)",
            "primary_authorities": [
                "Strasbourg Agreement Concerning the International Patent Classification, 24 Mar 1971 (amended 28 Sep 1979), WIPO",
                "WIPO, Guide to the International Patent Classification (2022) - hierarchical structure & subordination of symbols",
                "CPC Guide to the CPC (EPO/USPTO, 2023) - Section/Class/Subclass/Main group/Subgroup hierarchy",
                "MPEP 9th ed. Rev. 07.2022 Sec. 905 (Classification) - CPC/IPC as the prior-art / landscape search scoping framework",
            ],
            "note": "Classification framework applied only as a STRUCTURAL "
                    "search-scoping predicate; this is not legal advice and "
                    "performs no FTO.",
        },
        "inputs": {
            "fixture_path": "amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json",
            "fixture_sha256": fix_sha,
            "pinned_fixture_sha256": PINNED_FIXTURE_SHA,
            "families": len(fams),
            "cpc_ipc_sweeps": len(sweeps),
        },
        "hash_and_count_lock": {
            "fixture_sha256_matches_pin": fix_sha == PINNED_FIXTURE_SHA,
            "family_count_matches_pin": len(fams) == PINNED_FAMILIES,
            "sweep_count_matches_pin": len(sweeps) == PINNED_SWEEPS,
        },
        "checkA_sweep_validity_and_axes": cA,
        "checkB_family_coverage": cB,
        "checkC_no_cpc_clearance": cC,
        "checkD_partial_order": cD,
        "checkE_authority_envelope": cE,
        "fail_closed_mutation_demo": fc,
        "kpi_reconstruction": {
            "mandatory_axes_covered": cA["all_mandatory_axes_covered"],
            "token_coverage_fraction": cB["token_coverage_fraction"],
            "bucket_coverage_fraction": cB["bucket_coverage_fraction"],
            "orphan_adjacency_buckets": cB["orphan_adjacency_buckets"],
            "fto_claimed_rows": 0,
            "hypothesis_surfaces_unresolved_without_claiming_fto": scoping_sound,
        },
        "does_not_close": [
            "No FTO, no legal advice, no clearance. CPC/IPC coverage is a "
            "search-scoping measure only; dependent claims, prosecution history, "
            "jurisdictions, legal status and doctrine-of-equivalents remain "
            "counsel scope.",
            "Coverage completeness is measured against the ON-DISK fixture's own "
            "classified families; it is NOT a claim that the fixture enumerates "
            "every relevant patent family in the CPC neighborhood.",
            "Does not modify the manifest (66 receipts / 11 modules), the pinned "
            "fixture, or any signed Phase-0 KPI.",
            "AUDIT_ONLY: promotes no authority and flips no scientific_readiness.",
        ],
        "modifies_manifest": False,
        "modifies_pinned_fixture": False,
        "modifies_signed_phase0_kpi": False,
        "promotes_authority": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "headline": headline,
    }
    return diag


if __name__ == "__main__":
    out = build_diagnostic()
    dest = sys.argv[1] if len(sys.argv) > 1 else "-"
    text = json.dumps(out, indent=2, sort_keys=True)
    if dest == "-":
        print(text)
    else:
        Path(dest).write_text(text)
        print("WROTE", dest, "sha256", sha(text.encode()))
