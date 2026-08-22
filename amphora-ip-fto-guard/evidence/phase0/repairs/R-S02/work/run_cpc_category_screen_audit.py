#!/usr/bin/env python3
"""AUDIT_ONLY harness: per-row faithfulness audit of the ip-fto-guard
patent-landscape "bare CPC/IPC category screen" rows (campaign R-S02, batch 1
of 3: rows n=6..23, 18 of the 54 uncharted rows).

Claim under attack (pinned by campaign item R-S02):
  "The 54 of 60 patent-landscape rows audited only by bare CPC/IPC screen
   contain no further fabricated or misassigned elements."

Method (independent CPython recompute, no runtime call, no candidate-supplied
evidence):
  1. Pull the row's asserted cpc_ipc_class token(s) and its own claim1_gist /
     key_elements straight from the pinned patent_landscape.json fixture.
  2. Resolve each token against the OFFICIAL CPC Title List bulk data (EPO/
     USPTO Cooperative Patent Classification, edition 202608), NOT from
     memory or a hand-typed title: existence, level, title text, and the full
     ancestor chain (root section -> leaf symbol) are all reconstructed
     mechanically from the pinned, hash-verified corpus excerpt in raw/.
        FABRICATED  <=> the cited token does not resolve to any real symbol
                          in the official corpus (or the row implies definition
                          text the corpus does not contain).
        MISASSIGNED <=> the token is real, but its official scope (title +
                          ancestor chain) does not cover the chemistry the row
                          itself describes in claim1_gist/key_elements -- i.e.
                          a real CPC bucket was picked, but the wrong one.
        FAITHFUL    <=> the token is real and its official scope plausibly
                          covers the row's own described chemistry (bare
                          category-screen rows are allowed to be coarse/broad;
                          coarseness alone is not a defect, per the precedent
                          COARSE/ORPHAN treatment in cpc-coverage-v1).
  3. Judgment calls (does the real scope match the described chemistry) are
     recorded per-row with an explicit rationale citing the resolved title
     chain; this is the same textual-comparison method
     claim-chart-provenance-v1 used against Google Patents claim-1 text,
     applied here against CPC Title List text instead.

A token that fails to resolve, or a row whose own description is at odds with
its resolved definition chain, is a genuine counter-example to the pinned
claim and REFUTES it (a universal claim over 54 rows needs exactly one
counter-example). Two-replay byte-stability gate: this script is
deterministic (static data, no randomness, no clock) so canonical and runB
executions are byte-identical by construction.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
FIX = ROOT / "amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json"
WORK = ROOT / "amphora-ip-fto-guard/evidence/phase0/repairs/R-S02/work"
RAW = WORK / "raw"
PINNED_FIXTURE_SHA = "52ada09074f435d515a8286e57b1d31da40fcbe3d0ec4f79a9be754e5cce63dc"
BATCH_ROWS = list(range(6, 24))  # n=6..23 inclusive, 18 rows

SOURCE_PROVENANCE = json.loads((RAW / "source_provenance.json").read_text())

SYMBOL_RE = re.compile(r"^[A-H][0-9]{2}[A-Z]([0-9]{1,4}(/[0-9]{2,6})?)?$")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_corpus():
    """Parse the pinned CPC Title List excerpts into symbol -> (level, title)."""
    corpus = {}
    order = []
    for fname in ("excerpt_B_batch1.txt", "excerpt_C_batch1.txt", "excerpt_G_batch1.txt"):
        path = RAW / fname
        observed_sha = sha(path.read_bytes())
        expected_sha = SOURCE_PROVENANCE["excerpt_files"][f"raw/{fname}"]
        assert observed_sha == expected_sha, f"{fname} tampered: {observed_sha} != {expected_sha}"
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            assert len(parts) == 3, f"malformed corpus line: {line!r}"
            sym, level, title = parts
            corpus[sym] = {"level": int(level) if level.strip() else 0, "title": title}
            order.append(sym)
    return corpus, order


def ancestor_chain(symbol, corpus, order):
    """Reconstruct root->leaf ancestor chain for `symbol` by walking the
    pinned corpus's own document order and indent levels (the CPC Title List
    file is itself hierarchically ordered; a line's ancestors are the nearest
    preceding lines with strictly lower indent level)."""
    if symbol not in corpus:
        return None
    idx = order.index(symbol)
    target_level = corpus[symbol]["level"]
    chain = [(symbol, corpus[symbol]["title"])]
    cur_level = target_level
    for prev_sym in reversed(order[:idx]):
        prev_level = corpus[prev_sym]["level"]
        if prev_level < cur_level:
            chain.append((prev_sym, corpus[prev_sym]["title"]))
            cur_level = prev_level
            if cur_level == 0:
                break
    chain.reverse()
    return chain


def resolve_token(token, corpus, order):
    """A row's cpc_ipc_class field may be a single symbol, a ';'-joined list,
    or an explicit informal descriptor (e.g. 'public prior art'). Returns a
    list of per-symbol resolution dicts."""
    out = []
    for raw_sym in [t.strip() for t in token.split(";")]:
        if not raw_sym:
            continue
        if not SYMBOL_RE.match(raw_sym):
            out.append({
                "cited": raw_sym,
                "is_cpc_symbol_syntax": False,
                "resolved": False,
                "note": "not CPC/IPC symbol syntax; treated as an informal descriptor, not a classification assertion",
            })
            continue
        chain = ancestor_chain(raw_sym, corpus, order)
        if chain is None:
            out.append({
                "cited": raw_sym,
                "is_cpc_symbol_syntax": True,
                "resolved": False,
                "note": "well-formed CPC/IPC syntax but NOT FOUND in the official CPC Title List corpus -- fabricated symbol",
            })
            continue
        out.append({
            "cited": raw_sym,
            "is_cpc_symbol_syntax": True,
            "resolved": True,
            "title_chain": [f"{s}: {t}" for s, t in chain],
            "leaf_title": corpus[raw_sym]["title"],
        })
    return out


# ---------------------------------------------------------------------------
# Per-row adjudication (rationale is expert judgment; the resolved title
# chain each rationale cites is mechanically pulled from the pinned corpus
# above, not hand-typed here).
# ---------------------------------------------------------------------------
ADJUDICATION = {
    6: {"verdict": "faithful", "rationale": "row describes a waterborne epoxy dispersion anticorrosive package; C09D163/00 (epoxy-resin coating compositions) + C09D5/08 (anti-corrosive paints) both facially cover an epoxy-based anticorrosive coating regardless of solvent/waterborne architecture -- correct top-level buckets for a category screen."},
    7: {"verdict": "faithful", "rationale": "row describes high-loading metallic zinc dust / cathodic-protection primer; C09D5/10 resolves under C09D5/08 (Anti-corrosive paints) to the literal 'containing metal dust' subgroup -- an exact-match bucket for zinc-dust primer chemistry."},
    8: {"verdict": "faithful", "rationale": "row describes graphene/graphene-oxide barrier fillers; C09D7/61 resolves to 'inorganic' under the non-macromolecular-additive branch (C09D7/60, subordinate to C09D7/40 Additives). Carbon-allotrope fillers (carbon black, graphite, graphene) are conventionally bucketed as inorganic non-macromolecular pigment/filler material in this CPC branch rather than under organic (C09D7/63) or macromolecular (C09D7/65) siblings -- a defensible, if coarse, category-screen choice, paired correctly with C09D5/08 anti-corrosive."},
    9: {"verdict": "faithful", "rationale": "row describes layered silicate/nanoclay (montmorillonite-type mineral filler); C09D7/61 'inorganic' additive bucket is an exact match for a mineral clay filler."},
    10: {"verdict": "faithful", "rationale": "row describes encapsulated healing agents/inhibitors, i.e. polymeric microcapsule shells; C09D7/65 resolves to 'macromolecular' under the same non-macromolecular/macromolecular additive split -- correct bucket for a polymer-shell encapsulation technology, paired with C09D5/08 anti-corrosive."},
    11: {"verdict": "faithful", "rationale": "row describes reversible-bond (vitrimer-type) self-healing epoxy matrices; C08G59/00 (epoxy polycondensate/curing-chemistry root group) + C09D163/00 (epoxy coating) both facially cover a modified epoxy-network curing chemistry."},
    12: {"verdict": "faithful", "rationale": "row describes phenalkamine/phenolic-amine curing agents; C08G59/50 resolves under C08G59/40 'characterised by the curing agents used' to the literal 'Amines' subgroup -- exact match for an amine-curing-agent family, paired with C09D163/00 epoxy coating."},
    13: {"verdict": "faithful", "rationale": "row describes amidoamine adducts / modified amine curing packages; C08G59/50 'Amines' (curing-agent branch) is an exact-match bucket."},
    14: {"verdict": "faithful", "rationale": "row describes epoxy-polysiloxane hybrid coatings; C09D183/00 resolves to 'Coating compositions based on macromolecular compounds ... a linkage containing silicon' -- the real CPC bucket for silicone-backbone coating chemistry -- paired with C09D163/00 epoxy; jointly matches a hybrid epoxy/silicone description."},
    15: {"verdict": "faithful", "rationale": "row describes bio-derived epoxy resin coatings; C08G59/00 (epoxy polycondensate root) + C09D163/00 (epoxy coating) are the correct general buckets -- CPC has no dedicated 'bio-derived' epoxy subgroup at this level, so a bio-based epoxy family is properly filed at the general epoxy-chemistry buckets, not a defect."},
    16: {"verdict": "faithful", "rationale": "row describes mixed phosphate/molybdate/organic-salt corrosion-inhibitor packages; C09D5/08 'Anti-corrosive paints' is the correct top-level bucket (coarse but not misassigned -- inhibitor-package rows are not required to also cite the pigment/filler branch to be faithful)."},
    17: {"verdict": "faithful", "rationale": "row describes coatings with embedded/responsive corrosion indicators; C09D5/08 anti-corrosive + G01N ('Investigating or analysing materials by determining their chemical or physical properties') is a defensible adjacency bucket for a sensing/indicator-function coating used for landscape search-scoping -- G01N is not asserted as an FTO-relevant classification, only a search-scope adjacency (row carries not_fto=true)."},
    18: {"verdict": "faithful", "rationale": "row describes process windows/batch order/dispersion QC for high-solids epoxy application; B05D ('Processes for applying fluent materials to surfaces') + C09D (root coating-composition class) are the correct general process/composition buckets."},
    19: {"verdict": "misassigned", "rationale": "row describes 'reactive diluent packages for lowering VOC in epoxy coatings'. Reactive diluents in 2-part epoxy chemistry are low-viscosity EPOXIDE-side monomers (mono-/di-glycidyl ethers) blended into the resin to cut viscosity/VOC while still curing into the network -- they are not amine curing agents. The row is tagged C08G59/50, which resolves under C08G59/40 'characterised by the curing agents used' to the literal 'Amines' subgroup: a curing-agent bucket, not an epoxide-diluent bucket. The official corpus's own C08G59/20 branch ('characterised by the epoxy compounds used') contains C08G59/36 'together with mono-epoxy compounds' -- literally the reactive-diluent-with-polyepoxide bucket -- which the row does not cite. This is a real misassignment: a real CPC symbol was picked, but the wrong branch of the same subclass, one whose own official title (curing-agent Amines) contradicts the row's stated chemistry (an epoxide-side diluent, not an amine)."},
    20: {"verdict": "faithful", "rationale": "row describes CHDM (cyclohexanedimethanol) epoxy resin blends; C08G59/00 (epoxy polycondensate root) + C09D163/00 (epoxy coating) are the correct general epoxy-chemistry buckets -- CPC has no CHDM-specific subgroup, so filing at the general level is not a defect."},
    21: {"verdict": "faithful", "rationale": "row describes chlorinated-polyolefin overcoatability/tie-coat packages; C09D123/28 resolves under C09D123/26 'modified by chemical after-treatment' (itself under C09D123/00 'homopolymers or copolymers of unsaturated aliphatic hydrocarbons ... one carbon-to-carbon double bond') to the literal 'by reaction with halogens or compounds containing halogen' subgroup -- an exact-match bucket for chlorinated polyolefin coating chemistry."},
    22: {"verdict": "faithful", "rationale": "row describes micaceous iron oxide (MIO) lamellar barrier pigment, a mineral/inorganic pigment; C09D7/61 'inorganic' additive bucket is an exact match, paired with C09D5/08 anti-corrosive."},
    23: {"verdict": "faithful", "rationale": "row describes surface-treated silica fillers, an inorganic mineral filler; C09D7/61 'inorganic' additive bucket is an exact match."},
}


def main():
    fixture_bytes = FIX.read_bytes()
    fixture_sha = sha(fixture_bytes)
    landscape = json.loads(fixture_bytes)
    families = {f["n"]: f for f in landscape["families"]}

    corpus, order = load_corpus()

    rows_out = []
    counts = {"faithful": 0, "misassigned": 0, "fabricated": 0}
    for n in BATCH_ROWS:
        fam = families[n]
        assert not fam.get("independent_claim_chart", {}).get("charted"), f"row {n} is claim-charted, not a bare CPC screen row"
        token_field = fam.get("cpc_ipc_class") or fam.get("cpc_ipc_category") or ""
        resolutions = resolve_token(token_field, corpus, order)

        any_fabricated = any(
            r["is_cpc_symbol_syntax"] and not r["resolved"] for r in resolutions
        )
        adj = ADJUDICATION.get(n)
        assert adj is not None, f"no adjudication recorded for row {n}"
        verdict = "fabricated" if any_fabricated else adj["verdict"]
        counts[verdict] += 1

        rows_out.append({
            "n": n,
            "doc_read": fam.get("doc_read"),
            "assignee": fam.get("assignee"),
            "claim1_gist": fam.get("claim1_gist"),
            "key_elements": fam.get("key_elements"),
            "cited_cpc_ipc_class": token_field,
            "resolved_tokens": resolutions,
            "verdict": verdict,
            "rationale": adj["rationale"],
        })

    headline_refuted = counts["misassigned"] > 0 or counts["fabricated"] > 0

    out = {
        "schema": "amphora.ip-fto-guard.cpc-category-screen-audit.v1",
        "study_id": "IP_FTO_GUARD_R_S02_CPC_CATEGORY_SCREEN_AUDIT_BATCH1",
        "campaign_item_id": "R-S02",
        "batch": "1_of_3",
        "batch_rows": BATCH_ROWS,
        "batch_row_count": len(BATCH_ROWS),
        "claim_under_attack": "amphora-ip-fto-guard/evidence/audit/: the 54 of 60 patent-landscape rows audited only by bare CPC/IPC screen contain no further fabricated or misassigned elements.",
        "purpose": "Per-row adjudication of each bare-CPC-screen row's cpc_ipc_class assignment against the OFFICIAL CPC Title List (not memory, not the prior cpc-coverage-v1 subsumption model), classifying each row faithful / misassigned / fabricated.",
        "non_circularity": "Real-world published classification corpus (EPO/USPTO CPC Title List, edition 202608), hash-pinned bulk-data download, independent of the fixture under audit and independent of any prior ip-fto-guard receipt.",
        "theory_reference": "Cooperative Patent Classification (CPC), joint EPO/USPTO scheme extending IPC (Strasbourg Agreement 1971, as amended); Guide to the CPC (EPO/USPTO); CPC Title List bulk data edition 202608.",
        "source_provenance": SOURCE_PROVENANCE,
        "fixture": {
            "path": "amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json",
            "observed_sha256": fixture_sha,
            "pinned_sha256_matches_cpc_coverage_v1": fixture_sha == PINNED_FIXTURE_SHA,
        },
        "rows": rows_out,
        "counts": counts,
        "cumulative_after_this_batch": {
            "rows_audited_total": len(BATCH_ROWS),
            "rows_remaining": 54 - len(BATCH_ROWS),
        },
        "headline": (
            f"Batch 1/3 (rows n=6..23, 18 rows): {counts['faithful']} faithful, "
            f"{counts['misassigned']} misassigned, {counts['fabricated']} fabricated. "
            + ("CLAIM REFUTED: at least one row's CPC assignment is misassigned or fabricated." if headline_refuted
               else "No defect found in this batch (claim not yet fully audited -- 36 rows remain).")
        ),
        "kpi_reconstruction": {
            "hypothesis_corroborated": headline_refuted,
        },
        "proposed_followups": [
            {
                "module": "amphora-ip-fto-guard",
                "defect": "patent_landscape.json family n=19 ('reactive diluent packages for lowering VOC in epoxy coatings') is tagged cpc_ipc_class='C08G59/50; C09D163/00'. C08G59/50 resolves to the CPC 'Amines' curing-agent subgroup (under C08G59/40 'characterised by the curing agents used'), which contradicts the row's own described chemistry (an epoxide-side reactive-diluent additive, not an amine curing agent). The correct bucket per the official CPC Title List is under C08G59/20 'characterised by the epoxy compounds used', specifically C08G59/36 'together with mono-epoxy compounds'.",
                "proposed_done_criterion": "Correct family n=19's cpc_ipc_class (and cpc_ipc_category) field from 'C08G59/50; C09D163/00' to 'C08G59/36; C09D163/00' (or equivalent correct epoxy-compound-branch symbol), via a superseding patch (never rewrite in place) signed and cross-referenced in the module's RETRACTION-INDEX.md, with a re-verification that no other row shares the same C08G59/50-for-a-diluent-package error pattern.",
            }
        ],
        "does_not_close": [
            "Does not assert any row is FTO or legally cleared (every row already carries not_fto=true; this audit does not touch that field).",
            "Does not audit the remaining 36 bare-CPC-screen rows (n=24..25, 27..60); campaign item R-S02 batches 2 and 3 cover those.",
            "Does not verify legal status, prosecution history, or claim scope of any cited patent family -- title-list classification faithfulness only.",
            "Uses the CPC Scheme Title List (symbol titles + hierarchy), not the longer prose CPC Definitions document; a title-level mismatch is sufficient to prove misassignment, but title-level agreement does not itself prove exhaustive definitional agreement.",
        ],
    }
    return out


if __name__ == "__main__":
    result = main()
    canonical = json.dumps(result, indent=2, sort_keys=True)
    target = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    (WORK / target).write_text(canonical)
    print("WROTE", WORK / target)
    print("sha256", sha(canonical.encode()))
    print("headline:", result["headline"])
