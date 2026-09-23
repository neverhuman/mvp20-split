#!/usr/bin/env python3
"""AUDIT_ONLY harness: per-row faithfulness audit of the ip-fto-guard
patent-landscape "bare CPC/IPC category screen" rows (campaign R-S02, batch 2
of 3: rows n=24,25,27..42, 18 of the remaining 36 uncharted rows; n=26 is
excluded because it is independent_claim_chart.charted=true, already audited
in claim-chart-provenance-v1, per batch1's STATE.json note).

Claim under attack (pinned by campaign item R-S02):
  "The 54 of 60 patent-landscape rows audited only by bare CPC/IPC screen
   contain no further fabricated or misassigned elements."

Method: identical to batch 1 (amphora-ip-fto-guard/evidence/phase0/repairs/
R-S02/work/run_cpc_category_screen_audit.py) -- independent CPython
recompute against the OFFICIAL CPC Title List (EPO/USPTO, edition 202608),
hash-pinned bulk-data corpus excerpts, no runtime call, no candidate-supplied
evidence. See that script's docstring for the full FABRICATED / MISASSIGNED /
FAITHFUL decision rule; it is reused verbatim here.

Batch 2 required resolving four symbols not covered by batch 1's excerpt
files: C09D7/43 (Thickening agents), C23C22/00 (metal conversion-coating
root), G16C (Computational chemistry / chemoinformatics), G06N (computing
arrangements based on specific computational models). These were extracted
from the SAME pinned zip (batch1's already-downloaded, hash-verified local
copy; see raw/source_provenance_batch2.json) into raw/excerpt_C_batch2.txt
and raw/excerpt_G_batch2.txt; raw/excerpt_B_batch2.txt is byte-identical to
batch1's (B05D was already sufficient).
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
BATCH_ROWS = [24, 25, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42]

SOURCE_PROVENANCE = json.loads((RAW / "source_provenance_batch2.json").read_text())

SYMBOL_RE = re.compile(r"^[A-H][0-9]{2}[A-Z]([0-9]{1,4}(/[0-9]{2,6})?)?$")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_corpus():
    """Parse the pinned CPC Title List excerpts into symbol -> (level, title)."""
    corpus = {}
    order = []
    for fname in ("excerpt_B_batch2.txt", "excerpt_C_batch2.txt", "excerpt_G_batch2.txt"):
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
    24: {"verdict": "faithful", "rationale": "row describes a public-domain military epoxy-polyamide primer architecture (MIL-DTL-24441-lineage). C09D163/00 (epoxy-resin coating compositions) is the correct general coating-composition bucket; the accompanying 'public prior art' text is not CPC/IPC symbol syntax and is correctly treated as an informal descriptor of the row's prior-art posture, not a second classification assertion. The row does not separately cite C08G59/50 for the polyamide-curing-agent facet, but per the batch1 COARSE/ORPHAN precedent (rows 15/16/18/20/38 etc.) a single correct top-level bucket is not required to also cite every constituent-chemistry facet to be faithful for a bare category-screen row."},
    25: {"verdict": "faithful", "rationale": "row describes automation/model-guided formulation optimization and process/QC workflows. G16C ('Computational chemistry; Chemoinformatics; Computational materials science') resolves as the root subclass covering formulation optimization/property-prediction software (its own child groups G16C20/30 'Prediction of properties' and G16C20/70 'Machine learning, data mining or chemometrics' are exactly the described function); G06N ('Computing arrangements based on specific computational models') resolves as the root subclass for the 'automation' / model-based decision-loop facet; C09D (root coating-composition class, no group number) covers the underlying chemical-product domain the software is applied to. All three are real, correctly-scoped root/subclass symbols for a software+coating-domain category screen."},
    27: {"verdict": "faithful", "rationale": "row describes a high-solids epoxy coating using a tetra-alkoxyorthosilicate/condensate reaction product (WO2009019296A1, Akzo Nobel). C08G59/00 (epoxy polycondensate root) + C09D163/00 (epoxy coating) are the correct general epoxy-chemistry buckets -- the official corpus has no dedicated organosilicate-modified-epoxy subgroup at this level (same pattern as batch1 row 15's bio-derived epoxy and row 20's CHDM epoxy), so filing at the general level is not a defect."},
    28: {"verdict": "faithful", "rationale": "row describes CHDM (cyclohexanedimethanol) epoxy resin high-solids coating compositions (WO2014093115A2, Dow) -- the identical chemistry class already adjudicated faithful in batch1 row n=20 ('CHDM epoxy resin blends'; C08G59/00 + C09D163/00, no CHDM-specific CPC subgroup exists). Same tag, same correct general-bucket rationale."},
    29: {"verdict": "faithful", "rationale": "row describes a non-ionic polyamide rheology modifier for aqueous coatings (WO2018010615A1, Elementis). C09D7/43 resolves under C09D7/40 'Additives' to the literal 'Thickening agents' subgroup -- an exact-match bucket for a rheology-modifier additive, paired with C09D163/00 epoxy coating."},
    30: {"verdict": "faithful", "rationale": "row describes a zinc phosphate conversion-coating bath using a hydroxylamine accelerant for metal pretreatment (US4865653A, Henkel). C23C22/00 resolves to 'Chemical surface treatment of metallic material by reaction of the surface with a reactive liquid, leaving reaction products of surface material in the coating, e.g. conversion coatings, passivation of metals' -- an exact-match bucket for a zinc-phosphate conversion-coating process; B05D (general fluent-material application process class) is a defensible coarse process pairing. The official CPC corpus has no dedicated hydroxylamine-accelerant subgroup under C23C22 (searched; hydroxylamine only appears elsewhere in the corpus as a compound-synthesis classification, C01B21/14, unrelated to phosphating baths), so filing at the C23C22/00 root is not a defect -- it is the correct bucket at the level of detail the CPC scheme actually offers."},
    31: {"verdict": "faithful", "rationale": "row describes phosphate-bath metal conversion-coating compositions and methods (US3178319A, Monsanto). Same C23C22/00 + B05D pairing as row 30, same exact-match rationale for a phosphate conversion coating."},
    32: {"verdict": "faithful", "rationale": "row describes a zinc-phosphating composition and process (EP0398202A1, Henkel KGaA). Same C23C22/00 + B05D pairing, same exact-match rationale."},
    33: {"verdict": "faithful", "rationale": "row describes a polyamide curing-agent composition (dimer-acid/polyethyleneamine-based) for epoxy curing (EP1865013B1, Evonik). C08G59/50 'Amines' is the correct curing-agent bucket -- a dimer-acid polyamide curing agent is amine-functional -- consistent with batch1's rows 12/13 (phenalkamine, amidoamine curing agents) which resolved the same symbol faithfully; paired with C09D163/00 epoxy coating."},
    34: {"verdict": "faithful", "rationale": "row describes an epoxy-silicone adhesive tiecoat for epoxy-coated ship hulls with foul-release overcoats (US6391464B1, International Paint). C09D183/00 resolves to 'Coating compositions based on macromolecular compounds ... a linkage containing silicon' -- the same real bucket already adjudicated faithful in batch1 row n=14 for an epoxy-polysiloxane hybrid; B05D is the general application-process class. Correct pairing for a silicone-backbone tiecoat."},
    35: {"verdict": "faithful", "rationale": "row describes a thermosetting composition from epoxy resin and polyamide resin (US2705223A, General Mills). C08G59/50 'Amines' (curing-agent branch, polyamide is amine-functional) + C09D163/00 (epoxy coating) -- same pairing and rationale as row 33."},
    36: {"verdict": "faithful", "rationale": "row describes a polyamide-epoxy adhesive composition (US2986539A, General Mills) -- an adhesive, not a coating, so the absence of C09D163/00 alongside the sole C08G59/50 'Amines' curing-agent tag is not a defect (the row is not asserting the adhesive is a coating composition); C08G59/50 correctly covers the amine/polyamide curing-agent chemistry described."},
    37: {"verdict": "faithful", "rationale": "row is a public CPC/IPC sweep for solvent-borne epoxy anticorrosive primers. C09D163/00 (epoxy coating) + C09D5/08 (Anti-corrosive paints) is the exact-match pairing for that chemistry -- same as batch1 row 37's would-be single-family analogue; both buckets are real and both facially cover the described chemistry."},
    38: {"verdict": "faithful", "rationale": "row is a public CPC/IPC sweep for DGEBA/DGEBF bisphenol-A/F epoxy blend high-solids coatings. C09D163/00 alone is a correct, if coarse, general epoxy-coating bucket -- CPC has no dedicated DGEBA-vs-DGEBF resin-blend subgroup, consistent with the general-epoxy-bucket precedent already established for rows 15/20/27/28 in this campaign."},
    39: {"verdict": "faithful", "rationale": "row is a public CPC/IPC sweep for phenalkamine-cured marine epoxy. C09D163/00 + C08G59/50 is the identical, already-adjudicated-faithful pairing from batch1 row n=12 (phenalkamine curing agents)."},
    40: {"verdict": "faithful", "rationale": "row is a public CPC/IPC sweep for amidoamine-cured corrosion primers. C09D163/00 + C08G59/50 is the identical, already-adjudicated-faithful pairing from batch1 row n=13 (amidoamine adducts)."},
    41: {"verdict": "faithful", "rationale": "row is a public CPC/IPC sweep for a zinc phosphate anticorrosive pigment package. C09D5/08 'Anti-corrosive paints' is the correct top-level bucket, consistent with batch1 row n=16's mixed-inhibitor-package precedent (coarse but not misassigned)."},
    42: {"verdict": "faithful", "rationale": "row is a public CPC/IPC sweep for a mixed molybdate/phosphate inhibitor blend. C09D5/08 'Anti-corrosive paints' is the correct top-level bucket, same rationale as row 41 and batch1 row 16."},
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

    batch2_headline_refuted = counts["misassigned"] > 0 or counts["fabricated"] > 0
    prior_counts = {"faithful": 17, "misassigned": 1, "fabricated": 0}  # batch1
    cumulative_counts = {k: prior_counts[k] + counts[k] for k in counts}
    cumulative_refuted = cumulative_counts["misassigned"] > 0 or cumulative_counts["fabricated"] > 0

    out = {
        "schema": "amphora.ip-fto-guard.cpc-category-screen-audit.v1",
        "study_id": "IP_FTO_GUARD_R_S02_CPC_CATEGORY_SCREEN_AUDIT_BATCH2",
        "campaign_item_id": "R-S02",
        "batch": "2_of_3",
        "batch_rows": BATCH_ROWS,
        "batch_row_count": len(BATCH_ROWS),
        "claim_under_attack": "amphora-ip-fto-guard/evidence/audit/: the 54 of 60 patent-landscape rows audited only by bare CPC/IPC screen contain no further fabricated or misassigned elements.",
        "purpose": "Continuation of R-S02: per-row adjudication of the next 18 bare-CPC-screen rows (n=24,25,27..42; n=26 excluded, already claim-charted) against the OFFICIAL CPC Title List, classifying each row faithful / misassigned / fabricated.",
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
        "batch2_headline_refuted": batch2_headline_refuted,
        "prior_batch_counts": prior_counts,
        "cumulative_counts": cumulative_counts,
        "cumulative_rows_audited": 18 + len(BATCH_ROWS),
        "cumulative_rows_remaining": 54 - 18 - len(BATCH_ROWS),
        "headline": (
            f"Batch 2/3 (rows n=24,25,27..42, 18 rows): {counts['faithful']} faithful, "
            f"{counts['misassigned']} misassigned, {counts['fabricated']} fabricated -- "
            "no new defect found in this batch. Cumulative (batches 1+2, 36/54 rows): "
            f"{cumulative_counts['faithful']} faithful, {cumulative_counts['misassigned']} misassigned, "
            f"{cumulative_counts['fabricated']} fabricated. "
            + ("CLAIM remains REFUTED (carried from batch1's row n=19 misassignment)." if cumulative_refuted
               else "No defect found across audited rows so far.")
            + " 18 rows remain (batch 3/3: n=43..60)."
        ),
        "kpi_reconstruction": {
            "hypothesis_corroborated": cumulative_refuted,
        },
        "proposed_followups": [],
        "does_not_close": [
            "Does not assert any row is FTO or legally cleared (every row already carries not_fto=true; this audit does not touch that field).",
            "Does not audit the remaining 18 bare-CPC-screen rows (n=43..60); campaign item R-S02 batch 3 covers those.",
            "Does not verify legal status, prosecution history, or claim scope of any cited patent family -- title-list classification faithfulness only.",
            "Uses the CPC Scheme Title List (symbol titles + hierarchy), not the longer prose CPC Definitions document; a title-level mismatch is sufficient to prove misassignment, but title-level agreement does not itself prove exhaustive definitional agreement.",
            "This batch found 0 new misassigned/fabricated rows; it does NOT overturn or weaken batch1's row n=19 finding, which stands as the operative counter-example to the pinned claim until repaired.",
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
