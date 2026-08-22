#!/usr/bin/env python3
"""V1-RESOLVE: merge the mechanical sweep (exists/verifies) with a read-and-judge
'covers_the_claim' pass performed by reading the actual decoded payload of every
distinct DSSE-verified superseding artifact (not just trusting RETRACTION-INDEX.md
prose). Judgments are hand-authored below from that read (see
work/payload_summaries.txt for the extracted payload excerpts this was judged
against). Produces one row per RETRACTION-INDEX.md row: module | claim | refuted-by
| superseded-by | exists | verifies | covers_the_claim | row_verdict.
"""
import json
import sys

ROOT = "/home/ubuntu/amphora/build/mvp20-split"

# Per-distinct-target judgment, keyed by the resolved repo-relative path.
# Every one of these was read via work/payload_summaries.txt: each target's
# DSSE payload `supersedes[].reason` (or equivalent) directly and specifically
# names the claim it corrects, with a concrete before/after or corrected value.
COVERS_TRUE = {
    "amphora-assurance-capabilities/evidence/phase0/repairs/R-B01/done/repair-receipt.R-B01.v1.dsse.json":
        "Payload supersedes[] names both refuted receipts by path+sha256 and states the concrete code fix (unresolved_technical_categories now populated; recursive NFKC counsel-assertion scan) with a re-attack recall of 1.0 (was 0.0).",
    "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-B02/done/barrier-index-repair-receipt.v1.dsse.json":
        "Payload names the refuted receipt, states barrier_index now has a Some(..) path in src/lib.rs, and explicitly scopes to the structural finding only (leaves W1's statistical-infeasibility findings in force) -- matches the row's claim text exactly.",
    "amphora-cure-potlife-gate/evidence/phase0/repairs/R-A02/done/R-A02-repair-receipt.v1.dsse.json":
        "Payload quotes the exact refuted mission.md sentence, cites both refuting receipts' per-leg MAPE numbers, and records the qualified replacement prose + front-matter-untouched sha256 pair.",
    "amphora-design-rule-score/benchmarks/guth-gold-physical-baseline-v1/physical_baseline_receipt.v1.anchored-reissue.v1.json":
        "Signature-identity-only reissue; payload's supersedes.reason states scientific content unchanged, re-verified byte-intact against the pre-repair sha256 -- matches the narrow claim (signature identity only).",
    "amphora-ingredient-library/evidence/phase0/repairs/R-A01/done/repair-R-A01-done-receipt.v1.dsse.json":
        "Payload covers both rows: mission/KPI sha256 correction (quotes old+new hashes) and the solid_type1_epoxy EEW band correction (383.5-667.8 -> 450.0-550.0 g/eq) with an explicit re-attack (4/4 probes now rejected).",
    "amphora-ip-fto-guard/evidence/phase0/repairs/R-A13/done/claim-chart-supersede-repair.R-A13.v1.dsse.json":
        "Payload names the fabricated 'polyurea topcoat' / unsupported 'low VOC' elements against the hash-pinned EP2653485A2 text and supplies the corrected chart; scope is explicitly narrowed to family 26 only.",
    "amphora-known-answer-benchmarks/evidence/phase0/repairs/R-A05/done/R-A05.done-receipt.v1.dsse.json":
        "Payload reproduces the exact refuting recompute (42.4165, matches TDS 42.5 to 0.0835pp) and explicitly states VERIFIED_PASS / 6/6 pass-rate are unaffected -- matches the row's narrow reference-value-only claim.",
    "amphora-molecule-generator/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json":
        "Payload republishes both corrected numbers (Clopper-Pearson [0.9075,1.0000]; 29/38 not 38/38) with derivations, and a third row (scaffold diversity) is corrected with the family-resolved IntDiv_1 numbers -- all three row claims matched.",
    "amphora-molecule-generator/evidence/phase0/repairs/R-A06v2/done/molgen-r-a06v2-functionality-convention-repair-receipt.v1.dsse.json":
        "Payload states the precise convention error (amine_sites==2 nitrogen-atom count vs active_NH==2 active-hydrogen count), re-derives via two independent RDKit paths against in-tree ground truth, and explicitly carries forward (does not re-dispute) R-A06's other two corrections -- matches the row's claim.",
    "amphora-molecule-novelty/evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json":
        "Payload covers both rows: dedup (443->350, DDS 0/4 not 1/4) and IPDA structural identity (C9H20N2 not C10H22N2, NN recomputed 0.1667) with the numeric result stated to survive both corrections.",
    "amphora-molecule-novelty/evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json":
        "Payload states precisely what R-A07 missed (IPDA fix applied in only 1 of 4 fingerprint families), republishes the complete four-family table, and discloses the one additional flip cell (atompair_2048/IPDA/a0.01) by name -- matches the row's claim.",
    "amphora-molecule-property/benchmarks/phys-ml-stack-comparison-c8-fire2-clean-subset-v1/c8_fire2_dielectric_clean_subset_receipt.v1.anchored-reissue.v1.json":
        "Signature-identity-only reissue; payload's supersedes.reason states scientific content unchanged, re-verified byte-intact -- matches the narrow claim.",
    "amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json":
        "Schema is a mission-prose-retraction-sweep; index text quotes all 20 before/after prose pairs by line number against the specific refuting receipts (dielectric-retraction-v1, C7 final, W8, C8-fire3) -- each of the 9 B3 rows maps to a named repair id (S1-S17) inside this one receipt.",
    "amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json":
        "Payload is itself a full per-KPI status table (21 files, STANDS/STANDS-WITHIN-CORPUS-ONLY/REFUTED/RETRACTED, each row citing its own refuting receipt or 'none') -- directly and individually addresses every one of the 19 R-A09 rows it's cited from.",
    "amphora-molecule-property/evidence/phase0/repairs/R-N02/done/rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json":
        "Payload states the corrected values (guanidine/DICY/biguanide n_active_nh 4->0, AHEW undefined) adopted verbatim from the refuting receipt's own prototype, and is explicitly coordinated (sha256-cited) with the sibling rdkit-ffi and role-ranker repairs.",
    "amphora-molecule-role-ranker/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json":
        "Payload names both wrong-key-signed receipts by sha256, states the specific defect (LOCAL_DEVELOPMENT_AUDIT_ONLY key, verified_new_signed=0), and reinstates under the pinned key with byte-exact reproduction -- matches both rows.",
    "amphora-molecule-role-ranker/evidence/phase0/repairs/R-N02/done/rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json":
        "Payload states the corrected values (DPG/DOTG reactive_amine_hydrogen_count 3->0, role hardener->out_of_domain) matching the refuting receipt's own expected_role on 2/2 probes.",
    "amphora-public-corrosion-benchmark/evidence/phase0/repairs/R-A08/done/audit-verdicts-consolidated-kpi.v2.dsse.json":
        "Payload states the precise staleness defect (4 of then-6 receipts indexed, omitting the very audit refuting the headline) and re-enumerates all 8 signed receipts at build time with per-receipt signature verification.",
    "amphora-public-corrosion-benchmark/evidence/phase0/repairs/R-A08/done/nist-corr-data-marine-steel-corrosion-baseline-kpi.v2.dsse.json":
        "Payload cites the exact refuting numbers (honest reimpl Ridge 0.5888/null 0.6736 vs pinned 0.6331/0.6806; 17/30 folds, CI crosses zero) and corrects the ridge-beats-null claim surface accordingly.",
    "amphora-public-corrosion-benchmark/evidence/phase0/repairs/R-N03/done/audit-verdicts-consolidated-kpi.v3.dsse.json":
        "Payload explains this is a currency (not refutation) supersession of the v2 index, re-enumerates all signed receipts, and points to the v3 KPI carrying the consolidated honest claim -- matches the row.",
    "amphora-public-corrosion-benchmark/evidence/phase0/repairs/R-N03/done/nist-corr-data-marine-steel-corrosion-baseline-kpi.v3.dsse.json":
        "Payload cites the exact LOMO-CV extrapolation numbers (pooled MAE 1.0728 vs null 0.8106, improvement -0.2622 log10, worst case Carbon/alloy steels +0.6587) and states the consolidated honest claim: no defensible lift, in-domain or extrapolative.",
    "amphora-rdkit-ffi/evidence/phase0/repairs/R-N02/done/rn02-rdkit-ffi-coordinated-cn-fix-repair-receipt.v1.dsse.json":
        "Payload states the corrected FFI return value (count_reactive_amine_hydrogens 3->0 for DPG/DOTG) matching the refuting receipt's expected_role on 2/2 probes; coordinated with the sibling molecule-property/role-ranker repairs by sha256.",
    "amphora-solvency-score/evidence/phase0/repairs/R-A10/done/r-a10-prose-consistency-w7-disclosure-repair-receipt.v1.dsse.json":
        "Payload quotes the pre-repair sha256, records a preserved byte-exact pre-repair snapshot, and states the front-matter-authoritative founder ruling for the third row (no refuting receipt needed for that one, consistent with the index's own 'no refuting receipt -- FOUNDER RULING' annotation).",
    "amphora-solvency-score/evidence/phase0/repairs/R-B03/done/flory-hansen-corrected-instrument-repair-receipt.v1.dsse.json":
        "Payload cites the exact refuting numbers (delta_p to 5.155e9 / 5.33e17 MPa^0.5 vs [9.6,59.875] envelope, denominator-collapse mechanism) and supplies a committed, unit-tested replacement instrument with an explicit envelope gate.",
    "amphora-sourceability-ehs/evidence/phase0/repairs/R-A04/done/r-a04-osha-table-z2-attribution-correction-receipt.v1.dsse.json":
        "Payload covers all 3 rows individually (one supersedes[] entry per affected receipt), each naming the exact wrong table cited and the correct Z-2 TWA/ceiling/peak values, with 'numerics unaffected' stated per-entry.",
    "amphora-sourceability-ehs/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json":
        "Payload names all 4 wrong-key-signed artifacts by sha256 and the specific defect, matching the row set exactly.",
    "amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/attempts/r-n01-fire1-ghs-clp-cid-attribution-audit-rebank-receipt.v1.dsse.json":
        "Scope-correct: the row's claim is signature-validity of the ORIGINAL audit only (not the hazard-card fix, which is a separate row -> done/fire2). Payload independently re-derives the same CID finding from a fresh PubChem fetch and signs under the pinned key -- matches the row's narrow claim. Filed in attempts/ per repair-mode rules because the fuller correction was deferred to fire 2, which is itself correctly cited by the other rows.",
    "amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json":
        "Payload states the CAS-correct CIDs (17857, 15133), the corrected H-statement sets, and the headline gate change (m-XDA H334 falls) with an explicit 0/5 mismatch re-attack.",
    "amphora-viscosity-score/evidence/phase0/repairs/R-A03/done/r-a03-disclosure-repair-receipt.v1.dsse.json":
        "Payload lists each superseded presentation by path+sha256 with the specific rights-disclosure defect (no CONTEXT_ONLY caveat / no interval disclosure) and the corrected prose that was added.",
}

# Rows whose superseded-by target does NOT (yet) cover the specific claim, even
# though the cited path(s) exist on disk. Keyed by (module, claim substring).
COVERS_FALSE = {
    ("amphora-tolerance-robustness", "OpenPoly Tg split-conformal coverage"):
        "superseded_by cell is the literal token 'PENDING' -- the item's own repair queue (R-C01) has not landed. exists=False by definition; nothing to verify or judge.",
    ("amphora-tolerance-robustness", "RadonPy eps_r conformal coverage"):
        "Cited targets (amphora-molecule-property/evidence/audit/dielectric-retraction-v1/, logs/claims-requiring-retraction.jsonl) exist and the dielectric-retraction-v1 receipt DSSE-verifies, but its own claim_under_attack (read directly: 'Dielectric-constant ML results ... rest on admissible labels', verdict CLAIM_REFUTED) addresses LABEL ADMISSIBILITY of the underlying RadonPy data -- a different, narrower claim than this row's own claim (conformal COVERAGE = 0.9558 vs the Wilson-CI-excludes-0.95 finding). The row's own text admits this: 'coverage under admissibility stratification queued within R-C01 scope'. No signed artifact anywhere in the portfolio currently republishes a corrected coverage number for this KPI. covers_the_claim=NO.",
}


import re

# "same R-A10 receipt" / "same R-B03 receipt (...)" style ditto-references within
# a single table: no literal path token in the cell, but unambiguously referring
# to the first row's already-resolved target in the same section. Resolved by
# hand by reading the surrounding table text (not a mechanical path match).
DITTO_TARGET = {
    "R-A10": "amphora-solvency-score/evidence/phase0/repairs/R-A10/done/r-a10-prose-consistency-w7-disclosure-repair-receipt.v1.dsse.json",
    "R-B03": "amphora-solvency-score/evidence/phase0/repairs/R-B03/done/flory-hansen-corrected-instrument-repair-receipt.v1.dsse.json",
}


def main():
    diag = json.load(open(sys.argv[1]))
    out_rows = []
    n_pass = 0
    n_fail = 0
    n_na = 0
    fail_rows = []
    for module, info in diag["modules"].items():
        for r in info["rows"]:
            exists = r["superseded_by_exists"]
            verifies = r["superseded_by_verifies"]
            ditto_target = None
            if not r["superseded_by_paths_cited"] and not r["literal_pending"]:
                m = re.search(r"\bsame\s+(R-[A-Z0-9]+)\b", r["superseded_by_cell"])
                if m and m.group(1) in DITTO_TARGET:
                    ditto_target = DITTO_TARGET[m.group(1)]
                    exists = True
                    verifies = True
            # historical/pre-existing-supersession rows explicitly marked
            # refuted-by "n/a" carry no falsification claim to cover.
            if re.match(r"^n/a\b", r["refuted_by_cell"].strip(), re.I):
                out_rows.append({
                    "module": module, "index_path": r["index_path"],
                    "claim": r["claim_excerpt"], "refuted_by": r["refuted_by_cell"],
                    "superseded_by": r["superseded_by_cell"], "exists": exists,
                    "verifies": verifies, "covers_the_claim": None,
                    "covers_rationale": "refuted-by is explicitly 'n/a' (pre-existing/housekeeping supersession note, predates the live falsification surface) -- no claim-under-attack to judge coverage against.",
                    "row_verdict": "NOT_APPLICABLE",
                })
                n_na += 1
                continue
            # covers-the-claim judgment
            covers = None
            covers_rationale = None
            if ditto_target:
                covers = True
                covers_rationale = ("ditto reference to the same-table row's target ("
                                     + ditto_target + "); " + COVERS_TRUE[ditto_target])
            elif r["literal_pending"]:
                covers = False
                covers_rationale = COVERS_FALSE.get(
                    (module, r["claim_excerpt"][:35]),
                    "literal PENDING token in superseded-by cell.")
            else:
                fk = None
                for k in r["superseded_by_resolved_keys"]:
                    tgt = diag["distinct_superseded_by_targets"].get(k, {})
                    rp = tgt.get("resolved_path")
                    if rp:
                        rel = rp.split("mvp20-split/", 1)[-1]
                        if rel in COVERS_TRUE:
                            fk = rel
                            break
                if fk:
                    covers = True
                    covers_rationale = COVERS_TRUE[fk]
                else:
                    # check hand-curated NO list by (module, claim-prefix)
                    hit = None
                    for (m2, cprefix), rationale in COVERS_FALSE.items():
                        if m2 == module and r["claim_excerpt"].startswith(cprefix):
                            hit = rationale
                            break
                    if hit:
                        covers = False
                        covers_rationale = hit
                    else:
                        # non-DSSE-only supporting doc (e.g. mission.md prose,
                        # superseded fixture pointer) with no distinct
                        # DSSE-verified companion in COVERS_TRUE for this row
                        covers = None
                        covers_rationale = "no distinct DSSE-signed target judged for this row's superseded-by cell; see superseded_by_cell text."

            row_verdict = "RESOLVED" if (exists and verifies and covers is True) else "NOT_RESOLVED"
            if row_verdict == "RESOLVED":
                n_pass += 1
            else:
                n_fail += 1
                fail_rows.append({
                    "module": module, "claim_excerpt": r["claim_excerpt"],
                    "exists": exists, "verifies": verifies, "covers": covers,
                    "reason": covers_rationale,
                })
            out_rows.append({
                "module": module,
                "index_path": r["index_path"],
                "claim": r["claim_excerpt"],
                "refuted_by": r["refuted_by_cell"],
                "superseded_by": r["superseded_by_cell"],
                "exists": exists,
                "verifies": verifies,
                "covers_the_claim": covers,
                "covers_rationale": covers_rationale,
                "row_verdict": row_verdict,
            })

    result = {
        "n_rows": len(out_rows),
        "n_resolved": n_pass,
        "n_not_resolved": n_fail,
        "n_not_applicable": n_na,
        "not_resolved_rows": fail_rows,
        "resolution_table": out_rows,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
