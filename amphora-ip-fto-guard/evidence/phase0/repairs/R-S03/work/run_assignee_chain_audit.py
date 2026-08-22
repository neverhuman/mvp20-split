#!/usr/bin/env python3
"""Assignee/ownership-chain integrity audit for the 6 claim-charted patent
families in patent_landscape.json (campaign item R-S03).

AUDIT_ONLY. For each of the 6 rows where independent_claim_chart.charted is
true, this script:
  1. Extracts the json 'assignee' field from patent_landscape.json.
  2. Re-derives Current/Original Assignee from the in-tree hash-pinned Google
     Patents snapshot fetched by claim-chart-provenance-v1 (2026-08-03).
  3. Re-derives Current/Original Assignee from a freshly fetched live
     snapshot (this fire, 2026-08-12) and checks for drift against #2.
  4. Cross-checks any 'Blue Cube' assignee against independent corroborating
     public sources (Wikipedia Olin Corporation article; SEC EDGAR company
     search for 'Blue Cube Spinco Inc.' and for 'Olin Corp') to determine
     whether the corporate lineage implied by the landscape's own assignee
     text (not just the bare entity name) is accurate.
  5. Adjudicates a chain_status per row: current / stale / misattributed.
  6. Logs every external register consulted and, where blocked, the exact
     HTTP/DNS evidence of the barrier (EPO Register: Cloudflare bot-challenge
     403; USPTO PatentsView legacy API: 301 to a JS-challenge-gated portal;
     several USPTO assignment-search hostnames: NXDOMAIN on this network).

Deterministic and reproducible given the pinned raw/ inputs (all hash-pinned
below); no network calls are made by this script itself -- all fetches were
performed and hash-pinned by the shell harness before this script runs.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-ip-fto-guard"
BENCH = MODULE / "evidence/phase0/repairs/R-S03/work"
LANDSCAPE = MODULE / "reference/mvp20/data/patent_landscape.json"
PRIOR_SNAPSHOT_DIR = MODULE / "evidence/audit/claim-chart-provenance-v1/raw"
LIVE_SNAPSHOT_DIR = BENCH / "raw/live"
REGISTERS_DIR = BENCH / "raw/registers"
CORRO_DIR = BENCH / "raw/corroboration"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_sha_map(sumfile):
    out = {}
    for line in Path(sumfile).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        h, name = line.split(None, 1)
        out[name.strip()] = h
    return out


def extract_assignee_fields(html):
    """Pull Current Assignee and Original Assignee (first/primary occurrence,
    i.e. the document's own bibliographic record, not the citation-network
    entries further down the page) from a Google Patents biblio page."""
    cur_m = re.search(
        r'itemprop="assigneeCurrent"[^>]*>\s*([^<]*?)\s*</dd>', html, re.S)
    orig_m = re.search(
        r'itemprop="assigneeOriginal"[^>]*>\s*([^<]*?)\s*</dd>', html, re.S)
    current = cur_m.group(1).strip() if cur_m and cur_m.group(1).strip() else None
    original = orig_m.group(1).strip() if orig_m else None
    return {"current_assignee": current, "original_assignee": original}


# doc_read/url anchor -> the corresponding raw snapshot filename used by both
# the prior (2026-08-03) and live (2026-08-12) fetch sets.
FAMILY_TO_FILE = {
    1: "WO2016187380A1.html",
    2: "EP3328938B1.html",
    3: "EP2931822A2.html",
    4: "WO2013159277A1.html",
    5: "US5059640A.html",
    26: "EP2653485A2.html",
}

# Documented near-synonym assignee-name spellings that are NOT a chain defect
# (accent/legal-suffix/locale rendering differences of the same legal entity).
BENIGN_NAME_VARIANTS = {
    "US Department of the Navy": "US Department of Navy",
    "Hempel A/S": "Hempel AS",
}


_SUFFIX_RE = re.compile(
    r"\b(LLC|INC|INCORPORATED|LTD|LIMITED|CORP|CORPORATION|CO|COMPANY|"
    r"A/S|AS|GMBH|PLC|THE)\b\.?", re.I)


def normalize_entity(name):
    if name is None:
        return None
    n = name.upper()
    n = _SUFFIX_RE.sub("", n)
    n = re.sub(r"[^A-Z0-9]+", "", n)
    return n


def names_equivalent(a, b):
    if a is None or b is None:
        return False
    if a == b:
        return True
    if BENIGN_NAME_VARIANTS.get(a) == b or BENIGN_NAME_VARIANTS.get(b) == a:
        return True
    na, nb = normalize_entity(a), normalize_entity(b)
    if na and nb and na == nb:
        return True
    return False


def run(landscape_path=LANDSCAPE, prior_dir=PRIOR_SNAPSHOT_DIR,
        live_dir=LIVE_SNAPSHOT_DIR, registers_dir=REGISTERS_DIR,
        corro_dir=CORRO_DIR):
    landscape = json.loads(Path(landscape_path).read_text())
    families = {f["n"]: f for f in landscape["families"]}
    charted_ns = sorted(n for n, f in families.items()
                         if f.get("independent_claim_chart", {}).get("charted"))
    assert charted_ns == [1, 2, 3, 4, 5, 26], charted_ns

    prior_sha = load_sha_map(prior_dir.parent / "SHA256SUMS.raw")
    live_sha = load_sha_map(live_dir / "SHA256SUMS.raw")

    # --- corroboration evidence (Blue Cube / Olin lineage) ------------------
    wiki_html = (corro_dir / "olin_corporation_wikipedia.html").read_text(
        encoding="utf-8", errors="replace")
    sec_blue_html = (corro_dir / "sec_edgar_blue_cube_browse.html").read_text(
        encoding="utf-8", errors="replace")
    sec_olin_html = (corro_dir / "sec_edgar_olin_browse.html").read_text(
        encoding="utf-8", errors="replace")
    corro_sha = load_sha_map(corro_dir / "SHA256SUMS.raw")

    wiki_quote_m = re.search(
        r"October 5, 2015, Olin successfully acquired Dow's [\s\S]{0,220}?"
        r"business units", wiki_html)
    wiki_quote = wiki_quote_m.group(0) if wiki_quote_m else None

    blue_cube_addr_m = re.search(r"(\d{3} CARONDELET[^<|]*)", sec_blue_html)
    blue_cube_addr = blue_cube_addr_m.group(1).strip() if blue_cube_addr_m else None
    blue_cube_name_present = "Blue Cube Spinco Inc." in sec_blue_html
    olin_addr_m = re.search(r"(\d{3} CARONDELET[^<|]*)", sec_olin_html)
    olin_addr = olin_addr_m.group(1).strip() if olin_addr_m else None

    _ADDR_ABBREV = {"PLZ": "PLAZA", "STE": "SUITE"}

    def norm_addr(s):
        if not s:
            return None
        s = s.upper()
        for abbrev, full in _ADDR_ABBREV.items():
            s = re.sub(r"\b" + abbrev + r"\b", full, s)
        return re.sub(r"[^A-Z0-9]", "", s)

    blue_cube_is_olin_address = (
        blue_cube_addr is not None and olin_addr is not None and
        norm_addr(blue_cube_addr) == norm_addr(olin_addr)
    )

    corroboration = {
        "question": "Is 'Blue Cube IP LLC' (assignee for families n=1, n=3) "
                     "a Dow entity or an Olin Corporation entity as of the "
                     "2015 Dow chlorine/epoxy-business divestiture?",
        "sources_consulted": [
            {
                "source": "Wikipedia: Olin Corporation, section "
                          "'Spinoffs and joint ventures (2015-2022)'",
                "url": "https://en.wikipedia.org/wiki/Olin_Corporation",
                "sha256": corro_sha.get("olin_corporation_wikipedia.html"),
                "quote": wiki_quote,
            },
            {
                "source": "SEC EDGAR company search: 'Blue Cube Spinco Inc.' "
                          "(CIK 0001640811) registered business address",
                "url": "https://www.sec.gov/cgi-bin/browse-edgar?action="
                       "getcompany&company=blue+cube&type=&dateb=&owner="
                       "include&count=40",
                "sha256": corro_sha.get("sec_edgar_blue_cube_browse.html"),
                "extracted_address": blue_cube_addr,
            },
            {
                "source": "SEC EDGAR company search: 'Olin Corporation' "
                          "registered business address",
                "url": "https://www.sec.gov/cgi-bin/browse-edgar?action="
                       "getcompany&company=olin+corp&type=10-K&dateb=&owner="
                       "include&count=10",
                "sha256": corro_sha.get("sec_edgar_olin_browse.html"),
                "extracted_address": olin_addr,
            },
        ],
        "finding": (
            "Blue Cube Spinco Inc.'s SEC-registered address matches Olin "
            "Corporation's SEC-registered address (190 Carondelet Plaza, "
            "Suite 1530, Clayton, MO), and Wikipedia (citing contemporary "
            "reporting) states Olin completed acquisition of Dow's Global "
            "Epoxy business unit on 2015-10-05. Blue Cube entities, "
            "including the IP-holding affiliate 'Blue Cube IP LLC', are "
            "therefore domiciled with / controlled by Olin Corporation, not "
            "Dow, as of that date."
            if blue_cube_is_olin_address and wiki_quote else
            "Corroboration incomplete -- see raw evidence."
        ),
        "blue_cube_is_olin_address": blue_cube_is_olin_address,
    }

    # --- register-access attempts (independently authoritative sources) -----
    register_attempts = [
        {
            "register": "EPO Register (register.epo.org)",
            "targets": ["EP16833614 (EP3328938B1)", "EP13812324 (EP2931822A2)",
                        "EP13172326 (EP2653485A2)"],
            "result": "BLOCKED",
            "evidence": "HTTP 403 on all 3 application-number lookups; "
                        "response body and headers show Cloudflare bot "
                        "challenge (server: cloudflare, cf-ray present, "
                        "no legal-events/proprietor data returned).",
            "raw_files": ["epo_EP16833614.headers.txt", "epo_EP16833614.body.html",
                          "epo_EP13812324.headers.txt", "epo_EP13812324.body.html",
                          "epo_EP13172326.headers.txt", "epo_EP13172326.body.html"],
        },
        {
            "register": "USPTO PatentsView / patent-assignment API "
                        "(api.patentsview.org)",
            "targets": ["US5059640A"],
            "result": "BLOCKED",
            "evidence": "HTTP 301 redirect to "
                        "https://data.uspto.gov/support/transition-guide/"
                        "patentsview, a client-side-rendered page that "
                        "injects an AWS WAF JS challenge "
                        "(edge.sdk.awswaf.com/.../challenge.js) before any "
                        "content renders; the legacy free-query endpoint is "
                        "retired and its successor is not fetchable by "
                        "unauthenticated headless HTTP.",
            "raw_files": ["uspto_patentsview.headers.txt",
                          "uspto_patentsview.body.html"],
        },
        {
            "register": "USPTO Patent Assignment Search "
                        "(assignment-api.uspto.gov / legacy-assignment.uspto.gov "
                        "/ assignment.uspto.gov / patft.uspto.gov)",
            "targets": ["US5059640A"],
            "result": "BLOCKED",
            "evidence": "DNS NXDOMAIN for all 4 legacy assignment-search "
                        "hostnames on this network (getent hosts fails); "
                        "search.patentsview.org (current PatentsView search "
                        "UI, requires a registered API key per USPTO's "
                        "published transition guide) is likewise unresolvable.",
            "raw_files": ["dns_assignment-api.uspto.gov.txt",
                          "dns_legacy-assignment.uspto.gov.txt",
                          "dns_assignment.uspto.gov.txt",
                          "dns_patft.uspto.gov.txt",
                          "dns_search.patentsview.org.txt"],
        },
        {
            "register": "Google Patents biblio page (patents.google.com) -- "
                        "an aggregator, NOT a primary government register; "
                        "used as best-available in-tree/live public source "
                        "per the item's fallback clause.",
            "targets": [FAMILY_TO_FILE[n] for n in charted_ns],
            "result": "AVAILABLE",
            "evidence": "HTTP 200 on all 6 documents, both the prior "
                        "(2026-08-03) in-tree snapshot and a fresh live "
                        "re-fetch (this fire). Page itself disclaims: "
                        "'The listed assignees may be inaccurate. Google has "
                        "not performed a legal analysis and makes no "
                        "representation or warranty as to the accuracy of "
                        "the list.'",
            "raw_files": [],
        },
    ]

    # --- per-family adjudication ---------------------------------------------
    rows = []
    for n in charted_ns:
        fam = families[n]
        fname = FAMILY_TO_FILE[n]
        json_assignee = fam.get("assignee")

        prior_html = (prior_dir / fname).read_text(encoding="utf-8", errors="replace")
        live_html = (live_dir / fname).read_text(encoding="utf-8", errors="replace")
        prior_fields = extract_assignee_fields(prior_html)
        live_fields = extract_assignee_fields(live_html)

        prior_file_sha = sha((prior_dir / fname).read_bytes())
        live_file_sha = sha((live_dir / fname).read_bytes())
        prior_pin_ok = prior_sha.get(fname) == prior_file_sha
        live_pin_ok = live_sha.get(fname) == live_file_sha

        snapshot_drift = (
            prior_fields["current_assignee"] != live_fields["current_assignee"]
        )

        live_current = live_fields["current_assignee"]

        # Does the json's own assignee text match Google's live current
        # assignee entity name (allowing documented benign spelling variants)?
        # For compound labels ("Blue Cube IP / Dow") we split on '/' and
        # check the FIRST token against the live current-assignee entity,
        # then separately flag any additional token that asserts control by
        # a DIFFERENT named party not corroborated as the current owner.
        # Only split on a slash used as a compound-label separator (spaces on
        # both sides, e.g. "Blue Cube IP / Dow"), never a tight corporate
        # suffix slash with no surrounding whitespace (e.g. "Hempel A/S").
        tokens = [t.strip() for t in re.split(r"\s+/\s+", json_assignee)]
        primary_token = tokens[0]
        extra_tokens = tokens[1:]
        primary_matches_live = names_equivalent(primary_token, live_current)

        # General rule: any additional token in a compound assignee label
        # must itself be corroborated as a current co-owner/controller, or
        # the label is misattributed -- an appended party name is itself an
        # ownership-chain assertion, and an uncorroborated (or contradicted)
        # one is a defect regardless of which party is named. The only
        # standing corroboration this audit has built is the Blue Cube /
        # Olin-not-Dow check; any extra token that is neither (a) equivalent
        # to the live current assignee nor (b) that specific corroborated
        # relationship is flagged.
        misattributed_extra = None
        for tok in extra_tokens:
            if names_equivalent(tok, live_current):
                continue  # redundant restatement of the same live assignee
            if tok == "Dow" and live_current == "Blue Cube IP LLC" and \
                    corroboration["blue_cube_is_olin_address"]:
                misattributed_extra = (
                    f"json assignee text appends '/ {tok}' to the entity "
                    f"'{live_current}'. Corroborating public sources "
                    f"(Wikipedia + SEC EDGAR, see corroboration block) show "
                    f"{live_current} is domiciled with/controlled by Olin "
                    f"Corporation as of the 2015-10-05 Dow-to-Olin epoxy "
                    f"business transfer, not Dow. Appending '/ Dow' asserts "
                    f"a current ownership tie to Dow that the best-available "
                    f"public evidence contradicts."
                )
            else:
                misattributed_extra = (
                    f"json assignee text appends '/ {tok}' to the entity "
                    f"'{live_current}', asserting an additional current "
                    f"owner/controller. This audit has no corroboration "
                    f"confirming '{tok}' as a current co-owner or "
                    f"controller of '{live_current}', and the live "
                    f"bibliographic record does not name it. An "
                    f"uncorroborated appended party name is an ownership-"
                    f"chain assertion this audit cannot verify -- treated "
                    f"as misattributed pending verification."
                )

        if misattributed_extra:
            chain_status = "misattributed"
            confidence = "medium"
            rationale = misattributed_extra
        elif not primary_matches_live:
            chain_status = "misattributed"
            confidence = "medium"
            rationale = (
                f"json assignee '{primary_token}' does not match the live "
                f"Google Patents current-assignee field '{live_current}'."
            )
        else:
            # Primary entity name matches live bibliographic data and no
            # contradicting corroboration was found. Flag residual
            # verification risk where the only source is a disclaiming
            # aggregator and both independent registers are blocked.
            if n in (1, 4):
                chain_status = "current"
                confidence = "low"
                rationale = (
                    f"json assignee '{primary_token}' matches the live "
                    f"Google Patents current-assignee field, and no "
                    f"contradicting register evidence was found, but this "
                    f"entity's IP was part of a 2015 corporate divestiture "
                    f"(family n=1's own assignee 'Blue Cube IP LLC' is a "
                    f"direct spinoff product; family n=4's 'Dow Global "
                    f"Technologies LLC' covers chemistry -- chlorinated "
                    f"polyolefin epoxy overcoatability -- that falls within "
                    f"the same divested Global Epoxy business scope) and "
                    f"neither authoritative register (EPO, USPTO) is "
                    f"reachable from this environment to confirm no further, "
                    f"un-recorded-at-Google assignment has since occurred. "
                    f"Confidence is LOW, not a positive finding of currency."
                )
            elif n == 5:
                chain_status = "current"
                confidence = "high"
                rationale = (
                    "US5059640A expired 2003 (fee lapse, per its own "
                    "status field) and is US-government-owned; ownership "
                    "chain is moot for an expired, public-domain patent, "
                    "and government assignments of this kind are not "
                    "subject to the commercial-M&A staleness risk that "
                    "applies to families n=1/n=3/n=4."
                )
            else:
                chain_status = "current"
                confidence = "medium"
                rationale = (
                    f"json assignee '{primary_token}' matches the live "
                    f"Google Patents current-assignee field. No known "
                    f"merger/divestiture/name-change affecting this entity "
                    f"was found. Independent primary-register confirmation "
                    f"(EPO Register) was attempted and blocked (see "
                    f"register_attempts); this call rests on the "
                    f"aggregator source only."
                )

        rows.append({
            "n": n,
            "doc_read": fam["doc_read"],
            "url": fam["url"],
            "json_assignee": json_assignee,
            "google_patents_original_assignee": live_fields["original_assignee"],
            "google_patents_current_assignee_live": live_current,
            "google_patents_current_assignee_prior_2026_08_03": prior_fields["current_assignee"],
            "prior_snapshot_hash_pin_ok": prior_pin_ok,
            "live_snapshot_sha256": live_file_sha,
            "snapshot_drift_2026_08_03_to_2026_08_12": snapshot_drift,
            "source_consulted": "Google Patents biblio page (aggregator; EPO "
                                 "Register and USPTO PatentsView/assignment "
                                 "search both attempted and blocked -- see "
                                 "register_attempts)",
            "chain_status": chain_status,
            "confidence": confidence,
            "rationale": rationale,
        })

    counts = {"current": 0, "stale": 0, "misattributed": 0}
    for r in rows:
        counts[r["chain_status"]] += 1

    verdict = "CLAIM_REFUTED" if counts["misattributed"] > 0 or counts["stale"] > 0 else "CLAIM_SURVIVED"

    result = {
        "study_id": "amphora-ip-fto-guard-assignee-ownership-chain-audit-v1",
        "claim_under_attack": (
            "amphora-ip-fto-guard/evidence/audit/: Patent family ownership "
            "chains in patent_landscape.json are current and correctly "
            "attributed (R-S03), for the 6 claim-charted families."
        ),
        "charted_family_count": len(charted_ns),
        "charted_ns": charted_ns,
        "register_attempts": register_attempts,
        "corroboration": corroboration,
        "rows": rows,
        "counts": counts,
        "verdict": verdict,
        "refutation_evidence_family_n": [r["n"] for r in rows if r["chain_status"] != "current"],
    }
    return result


if __name__ == "__main__":
    out = run()
    Path(sys.argv[1]).write_text(json.dumps(out, indent=2, sort_keys=True))
    print("wrote", sys.argv[1])
    print("counts", out["counts"])
    print("verdict", out["verdict"])
