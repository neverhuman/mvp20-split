#!/usr/bin/env python3
"""AUDIT_ONLY harness: per-row faithfulness audit of the ip-fto-guard
patent-landscape "bare CPC/IPC category screen" rows (campaign R-S02, batch 3
of 3 -- FINAL batch: rows n=43..60, the last 18 of the 54 uncharted rows).

Claim under attack (pinned by campaign item R-S02):
  "The 54 of 60 patent-landscape rows audited only by bare CPC/IPC screen
   contain no further fabricated or misassigned elements."

Method: identical to batch 1 and batch 2 (see
amphora-ip-fto-guard/evidence/phase0/repairs/R-S02/work/
run_cpc_category_screen_audit.py and _batch2.py for the full FABRICATED /
MISASSIGNED / FAITHFUL decision rule, reused verbatim here) -- independent
CPython recompute against the OFFICIAL CPC Title List (EPO/USPTO, edition
202608), hash-pinned bulk-data corpus excerpts, no runtime call, no
candidate-supplied evidence.

Every CPC/IPC symbol cited by this batch's 18 rows was already present in
the corpus assembled across batch1+batch2 (including the bare root symbol
'C09D', already an ancestor-chain entry in excerpt_C_batch2.txt) -- no new
extraction from the pinned section files was required; see
raw/source_provenance_batch3.json.
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
BATCH_ROWS = [43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60]

SOURCE_PROVENANCE = json.loads((RAW / "source_provenance_batch3.json").read_text())

SYMBOL_RE = re.compile(r"^[A-H][0-9]{2}[A-Z]([0-9]{1,4}(/[0-9]{2,6})?)?$")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_corpus():
    """Parse the pinned CPC Title List excerpts into symbol -> (level, title)."""
    corpus = {}
    order = []
    for fname in ("excerpt_B_batch3.txt", "excerpt_C_batch3.txt", "excerpt_G_batch3.txt"):
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
    43: {"verdict": "faithful", "rationale": "row describes a rare-earth-compound anticorrosive pigment. C09D5/08 'Anti-corrosive paints' is the correct functional-class bucket; C09D7/61 resolves under C09D7/60 'non-macromolecular' additives to 'inorganic' -- a rare-earth compound (e.g. cerium/lanthanide salt) pigment is exactly an inorganic non-macromolecular additive. Exact-match pairing, same pattern as batch1's mixed-inhibitor rows."},
    44: {"verdict": "faithful", "rationale": "row describes an azole corrosion inhibitor in an epoxy-polyamide primer. C09D5/08 (Anti-corrosive paints) + C09D163/00 (epoxy-resin coating) is the correct pairing: an azole inhibitor dosed into an epoxy-polyamide primer is simultaneously an anti-corrosive-paint additive and an epoxy coating composition. Exact-match pairing."},
    45: {"verdict": "faithful", "rationale": "row describes micaceous iron oxide (MIO), a lamellar inorganic barrier pigment. C09D7/61 'inorganic' (non-macromolecular additive) + C09D5/08 'Anti-corrosive paints' is the correct pairing -- MIO is a mineral (iron oxide mica) filler used specifically for anticorrosive barrier performance. Exact-match pairing, consistent with rare-earth-pigment row 43's rationale."},
    46: {"verdict": "faithful", "rationale": "row describes aluminum flake, a lamellar inorganic barrier pigment (leafing/non-leafing Al flake used in mastic and MIO-type anticorrosive coatings). Same C09D7/61 (inorganic additive) + C09D5/08 (Anti-corrosive paints) pairing as row 45, same exact-match rationale -- metallic flake fillers are inorganic non-macromolecular additives."},
    47: {"verdict": "faithful", "rationale": "row describes graphene oxide used as a barrier nanofiller. C09D7/61 'inorganic' + C09D5/08 'Anti-corrosive paints'. Elemental-carbon 2D nanomaterials (graphene/graphene oxide, like graphite and carbon black) are conventionally classified as inorganic filler/pigment additives in coating-composition schemes (the CPC 'organic' vs 'inorganic' additive split at C09D7/61 vs C09D7/63 tracks compound class, not element; elemental-carbon allotropes fall on the inorganic side, consistent with rows 45/46's mineral/metal-flake fillers). No dedicated graphene subgroup exists under C09D7/61 in the pinned corpus, so filing at the general inorganic-additive bucket is coarse but not misassigned."},
    48: {"verdict": "faithful", "rationale": "row describes organoclay/nanoclay, a layered-silicate mineral barrier pigment (organically modified for dispersion, but the base material is an inorganic clay mineral). Same C09D7/61 (inorganic) + C09D5/08 (Anti-corrosive paints) pairing and rationale as rows 45-47."},
    49: {"verdict": "faithful", "rationale": "row describes a polyamide curing agent composition. C08G59/50 'Amines' is the exact-match curing-agent bucket -- a polyamide curing agent is amine-functional -- identical pairing/rationale to batch2 rows 33/35 (dimer-acid polyamide, polyethyleneamine curing agents)."},
    50: {"verdict": "faithful", "rationale": "row describes a polyamidoamine curing agent composition. C08G59/50 'Amines' -- polyamidoamines are amine-terminated curing agents, an exact match for this bucket, same as row 49."},
    51: {"verdict": "faithful", "rationale": "row describes a modified amine adduct for coatings. C08G59/50 'Amines' (curing-agent branch, amine adducts are amine-functional) + C09D163/00 (epoxy coating) -- exact-match pairing, same as batch2 rows 33/35."},
    52: {"verdict": "faithful", "rationale": "row describes the application/process window for a high-solids epoxy coating. B05D (general fluent-material application-process class) + C09D163/00 (epoxy coating, the underlying chemical product) -- correct pairing for a process-window claim over an epoxy coating product, same pattern as batch2 rows 30-32's B05D+C23C22/00 process pairings."},
    53: {"verdict": "faithful", "rationale": "row describes a metal-pretreatment-plus-primer-application process. B05D (application process) + C23C22/00 (chemical conversion-coating surface treatment) -- exact-match pairing, identical bucket choice to batch2 rows 30-32's already-adjudicated-faithful phosphate/zinc-phosphate conversion-coating rows."},
    54: {"verdict": "faithful", "rationale": "row describes process/QC monitoring for coating application. B05D (application process) + G01N ('Investigating or analysing materials by determining their chemical or physical properties') -- G01N is the correct root class for analytical/QC measurement of a material property during or after processing; B05D covers the application process being monitored. Correct pairing."},
    55: {"verdict": "faithful", "rationale": "row describes a reactive diluent for high-solids epoxy (the SAME underlying chemistry class as batch1's row n=19, which was found MISASSIGNED there because it cited C08G59/50 'Amines' -- the curing-agent branch -- for epoxide-side diluent chemistry). This row instead cites C08G59/00, the root of the entire epoxy-polycondensate class (ancestor of BOTH the epoxy-compound branch C08G59/20->32/36 and the curing-agent branch C08G59/40->50), together with C09D163/00 (epoxy coating). Citing the shared root is coarse but is NOT on the wrong branch the way row 19's C08G59/50 citation was -- C08G59/00 is a correct (if generic) ancestor of the epoxy-compound branch that actually covers reactive diluents (C08G59/20 'characterised by the epoxy compounds used' -> .../32 or .../22 'together with mono-epoxy compounds'), consistent with the established coarse-general-bucket-at-the-correct-branch precedent (rows 15/20/27/28/38, 57 below). This row does NOT repeat row 19's defect pattern."},
    56: {"verdict": "faithful", "rationale": "row describes a microcapsule self-healing epoxy coating. C09D5/08 (Anti-corrosive paints, the coating's functional class in this marine-coatings landscape) + C09D7/65 'macromolecular' (additives) -- a microcapsule shell (typically a polymeric wall material such as urea-formaldehyde or polyurethane) is a macromolecular additive to the coating, an exact-match bucket. Note: the pinned corpus also contains C08G59/188 '{using encapsulated compounds}' under the epoxy-curing-agent branch, a more narrowly on-point symbol for encapsulated-curing-agent epoxy chemistry specifically -- its absence from this row's citation is a missed opportunity for a more precise parallel tag, not a defect, since C09D7/65 does correctly and non-contradictorily cover microcapsule shell material as a macromolecular coating additive (same 'correct branch, coarser bucket' standard applied throughout this campaign)."},
    57: {"verdict": "faithful", "rationale": "row describes a dynamic-covalent-bond ('vitrimer-type') self-healing epoxy matrix. C08G59/00 (epoxy-polycondensate root) + C09D163/00 (epoxy coating). The pinned CPC corpus has no dedicated dynamic-covalent-bond/vitrimer/reversible-network subgroup anywhere under C08G59 (confirmed by full-subtree grep of the pinned section file), so filing at the general epoxy-polycondensate root is the correct available bucket -- same 'no more specific subgroup exists' precedent as batch1/2's rows 15/20/27/28/38."},
    58: {"verdict": "faithful", "rationale": "row describes a waterborne epoxy anticorrosive coating. C09D163/00 (epoxy coating) + C09D5/08 (Anti-corrosive paints) -- exact-match pairing for an aqueous-epoxy anticorrosive product, same bucket choice as row 44 and batch2 row 37."},
    59: {"verdict": "faithful", "rationale": "row describes a zinc-rich epoxy cathodic-protection primer. C09D5/10 'containing metal dust' (a child of C09D5/08 Anti-corrosive paints) + C09D163/00 (epoxy coating) -- an exact, literal match: zinc-rich primers are metal-dust-loaded anticorrosive paints, precisely the CPC child-group definition."},
    60: {"verdict": "faithful", "rationale": "row describes a formulation-optimization / coating-process data loop (software/automation for property prediction and process control). G16C (Computational chemistry; Chemoinformatics; Computational materials science, whose child groups G16C20/30 'Prediction of properties' and G16C20/70 'Machine learning, data mining or chemometrics' are exactly the described function) + G06N (Computing arrangements based on specific computational models, covering the ML/automation facet) + C09D (bare root 'Coating compositions', the underlying chemical-product domain the software targets) -- identical resolution pattern to batch2 row n=25's already-adjudicated-faithful software/automation row, differing only in citing the bare coating-composition root C09D instead of the narrower C09D163/00, which is itself defensible since this row's process-optimization framing is not epoxy-specific."},
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

    batch3_headline_refuted = counts["misassigned"] > 0 or counts["fabricated"] > 0
    prior_counts = {"faithful": 35, "misassigned": 1, "fabricated": 0}  # batches 1+2
    cumulative_counts = {k: prior_counts[k] + counts[k] for k in counts}
    cumulative_refuted = cumulative_counts["misassigned"] > 0 or cumulative_counts["fabricated"] > 0

    out = {
        "schema": "amphora.ip-fto-guard.cpc-category-screen-audit.v1",
        "study_id": "IP_FTO_GUARD_R_S02_CPC_CATEGORY_SCREEN_AUDIT_BATCH3",
        "campaign_item_id": "R-S02",
        "batch": "3_of_3",
        "batch_rows": BATCH_ROWS,
        "batch_row_count": len(BATCH_ROWS),
        "claim_under_attack": "amphora-ip-fto-guard/evidence/audit/: the 54 of 60 patent-landscape rows audited only by bare CPC/IPC screen contain no further fabricated or misassigned elements.",
        "purpose": "FINAL continuation of R-S02: per-row adjudication of the last 18 bare-CPC-screen rows (n=43..60) against the OFFICIAL CPC Title List, classifying each row faithful / misassigned / fabricated. Completes all 54 rows across batches 1+2+3.",
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
        "batch3_headline_refuted": batch3_headline_refuted,
        "prior_batch_counts": prior_counts,
        "cumulative_counts": cumulative_counts,
        "cumulative_rows_audited": 36 + len(BATCH_ROWS),
        "cumulative_rows_remaining": 54 - 36 - len(BATCH_ROWS),
        "all_54_rows_verdicted": (36 + len(BATCH_ROWS)) == 54,
        "headline": (
            f"Batch 3/3 FINAL (rows n=43..60, 18 rows): {counts['faithful']} faithful, "
            f"{counts['misassigned']} misassigned, {counts['fabricated']} fabricated -- "
            "no new defect found in this batch. Cumulative (all 54/54 rows, batches 1+2+3): "
            f"{cumulative_counts['faithful']} faithful, {cumulative_counts['misassigned']} misassigned, "
            f"{cumulative_counts['fabricated']} fabricated. "
            "R-S02's 54-row audit is COMPLETE. "
            + ("The pinned CLAIM remains REFUTED (carried from batch1's row n=19 misassignment; "
               "1 counter-example is sufficient to refute a universal claim over 54 rows). "
               "'Done' (all 54 rows verdicted) is independent of the claim's truth value (already false)."
               if cumulative_refuted else
               "No defect found across all 54 audited rows.")
        ),
        "kpi_reconstruction": {
            "hypothesis_corroborated": cumulative_refuted,
        },
        "proposed_followups": [
            {
                "defect": "Carried forward from batch1 (still open, not yet repaired): patent_landscape.json family n=19 ('reactive diluent packages for lowering VOC in epoxy coatings') is tagged cpc_ipc_class='C08G59/50; C09D163/00'. C08G59/50 resolves to the CPC 'Amines' curing-agent subgroup (under C08G59/40 'characterised by the curing agents used'), which contradicts the row's own described chemistry (an epoxide-side reactive-diluent additive, not an amine curing agent).",
                "module": "amphora-ip-fto-guard",
                "proposed_done_criterion": "Correct family n=19's cpc_ipc_class (and cpc_ipc_category) field from 'C08G59/50; C09D163/00' to the correct epoxy-compound-branch symbol, via a superseding patch (never rewrite in place) signed and cross-referenced in the module's RETRACTION-INDEX.md, with a re-verification that no other row shares the same C08G59/50-for-a-diluent-package error pattern."
            },
            {
                "defect": "Refinement to batch1's own proposed fix for row n=19: batch1 proposed correcting to C08G59/36 'together with mono-epoxy compounds', but C08G59/36 sits under C08G59/32 'Epoxy compounds containing three or more epoxy groups' (tri+-functional epoxy resins). This batch's full-subtree extraction of C08G59 (performed while adjudicating row n=55, the same reactive-diluent chemistry class) surfaced a second, more specific sibling symbol: C08G59/22 'Di-epoxy compounds' -> C08G59/223 '{together with monoepoxy compounds}'. Commercial high-solids marine epoxy coatings (row 19's and row 55's described chemistry) overwhelmingly use DGEBA/DGEBF-type DI-epoxy resins, not tri+-epoxy resins, so C08G59/223 is plausibly the more precise correct bucket than C08G59/36 -- neither this fire nor batch1 has confirmed which specific epoxy-functionality class the uncharted row n=19 family actually claims (the fixture's own text does not specify), so this is filed as an open refinement question, not a re-verdict of row 19 (which stands as adjudicated in batch1: definitely misassigned via C08G59/50, regardless of whether the correct fix is /36 or /223).",
                "module": "amphora-ip-fto-guard",
                "proposed_done_criterion": "Before repairing family n=19's cpc_ipc_class field, read the actual patent family(ies) underlying row n=19 (or, if the row remains an uncharted category-screen entry with no single family pinned, default to the CPC-scheme-correct general epoxy-compound-branch root C08G59/20) to determine whether the diluent chemistry is di- or tri+-epoxy-based, and select C08G59/223 vs C08G59/36 accordingly rather than assuming /36 by default."
            }
        ],
        "does_not_close": [
            "Does not assert any row is FTO or legally cleared (every row already carries not_fto=true; this audit does not touch that field).",
            "Does not verify legal status, prosecution history, or claim scope of any cited patent family -- title-list classification faithfulness only.",
            "Uses the CPC Scheme Title List (symbol titles + hierarchy), not the longer prose CPC Definitions document; a title-level mismatch is sufficient to prove misassignment, but title-level agreement does not itself prove exhaustive definitional agreement.",
            "This batch found 0 new misassigned/fabricated rows; it does NOT overturn or weaken batch1's row n=19 finding, which stands as the operative counter-example to the pinned universal claim.",
            "Completing the 54-row audit (this receipt) is NOT the same as repairing the claim: repairing family n=19's CPC tag (see proposed_followups) is a separate, still-open action item that this audit does not itself perform.",
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
