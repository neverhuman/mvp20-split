#!/usr/bin/env python3
"""Deterministic rights-disclosure-gap audit for amphora-viscosity-score.

WHY THIS EXISTS
---------------
This module's own docs/mission.md carries two headline "Empirical benchmark
result" sections (Polyverse melt-viscosity polymer-safe conformal intervals +
applicability-domain audit; Fox-Flory-Whitten physical scaling law vs ML) plus
the parent "5-fold source-safe GBM R^2 = 0.944" claim they build on. All three
are computed directly from the Polyverse melt-viscosity dataset
(acquisition_unit_id polyverse_melt_viscosity).

This module's OWN rights ledger
(reference/mvp20/quarantine/feedback_v2/exclusions/
polyverse_melt_viscosity-3cd923b4d67399f9.rights.json) already classes that
dataset rights_class=CONTEXT_ONLY, promotion_eligible=false, with an explicit
basis: "Custom license requires counsel; physically quarantine all
derivatives." (Georgia Tech Research Corporation General Public Use License
Agreement). The acquisition manifest independently marks quarantined=true.
A prior sibling-module audit (amphora-redteam-audit/benchmarks/
rights-integrity-v1) already found and hash-locked that 2 of these 3 receipts
self-declare no CONTEXT_ONLY rights caveat internally and classified them as
POSITIVE_CAPABILITY overclaims at the portfolio level.

This harness asks a narrower, module-owned question that the sibling audit
does NOT answer: has amphora-viscosity-score's OWN docs/mission.md -- the
document a human or downstream agent reads to learn this module's honest
current state -- ever been amended to disclose the CONTEXT_ONLY/
promotion_eligible=false status of the data underlying its two headline
"Empirical benchmark result" sections? It reads only on-disk facts, modifies
nothing, promotes nothing, and produces byte-identical output across replays
(no RNG, no network, no wall-clock reads).
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"

RIGHTS_EXCLUSION = (MOD / "reference/mvp20/quarantine/feedback_v2/exclusions/"
                    "polyverse_melt_viscosity-3cd923b4d67399f9.rights.json")
ACQUISITION_RECEIPT = MOD / "reference/mvp20/manifests/polyverse_melt_viscosity.acquisition-receipt.json"
DATASET_MANIFEST = MOD / "reference/mvp20/manifests/polyverse_melt_viscosity.json"
PORTFOLIO_RIGHTS_REPORT = ROOT / "feedback/v2/reports/rights-report.json"
MASTER_MANIFEST = (ROOT / "amphora-molecule-property/reference/mvp20/data/"
                   "amphora_coating_scientific_receipts_manifest.v1.json")
SIBLING_AUDIT = ROOT / "amphora-redteam-audit/benchmarks/rights-integrity-v1/diagnostic.canonical.json"
MISSION = MOD / "docs/mission.md"

RECEIPTS = [
    MOD / "reference/mvp20/data/polyverse_melt_viscosity_model_receipt.v1.json",
    MOD / "reference/mvp20/data/polyverse_melt_viscosity_conformal_and_applicability_domain_receipt.v1.json",
    MOD / "reference/mvp20/data/polyverse_melt_viscosity_fox_flory_whitten_physical_baseline_receipt.v1.json",
]

CAVEAT_STRINGS = ["context_only", "context only", "georgia tech", "promotion_eligible", "quarantine"]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def has_any(blob_lower, needles):
    return [n for n in needles if n in blob_lower]


def main(out_path):
    rights_bytes = RIGHTS_EXCLUSION.read_bytes()
    rights = json.loads(rights_bytes)
    decision = rights["decision"]

    acq_bytes = ACQUISITION_RECEIPT.read_bytes()
    acq = json.loads(acq_bytes)

    manifest_bytes = DATASET_MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)

    portfolio_rights_bytes = PORTFOLIO_RIGHTS_REPORT.read_bytes()
    portfolio_rights = json.loads(portfolio_rights_bytes)
    portfolio_decision = next(
        d for d in portfolio_rights["decisions"]
        if d["acquisition_unit_id"] == "polyverse_melt_viscosity")

    master_manifest_bytes = MASTER_MANIFEST.read_bytes()
    master_manifest = json.loads(master_manifest_bytes)
    idx_by_path = {r["relative_path"]: r for r in master_manifest["kpis"]["index_of_receipts"]}

    sibling_bytes = SIBLING_AUDIT.read_bytes()

    mission_bytes = MISSION.read_bytes()
    mission_lower = mission_bytes.decode("utf-8", errors="replace").lower()
    mission_caveat_hits = has_any(mission_lower, CAVEAT_STRINGS)
    mission_headline_present = (
        "empirical benchmark result" in mission_lower
        and "fox-flory-whitten" in mission_lower
        and "polyverse melt viscosity" in mission_lower
    )

    receipt_checks = []
    for p in RECEIPTS:
        rel = str(p.relative_to(ROOT))
        b = p.read_bytes()
        file_sha = sha(b)
        blob_lower = b.decode("utf-8", errors="replace").lower()
        self_declares = bool(has_any(blob_lower, ["context_only", "context only", "georgia tech"]))
        manifest_entry = idx_by_path.get(rel)
        receipt_checks.append({
            "relative_path": rel,
            "receipt_file_sha256": file_sha,
            "self_declares_context_only_rights": self_declares,
            "indexed_in_master_manifest": manifest_entry is not None,
            "master_manifest_hash_matches_disk": (
                manifest_entry is not None
                and manifest_entry.get("receipt_sha256") == file_sha
            ),
        })

    n_receipts_no_disclosure = sum(
        1 for r in receipt_checks if not r["self_declares_context_only_rights"])
    n_receipts_indexed_clean = sum(
        1 for r in receipt_checks
        if r["indexed_in_master_manifest"] and r["master_manifest_hash_matches_disk"])

    module_rights_class_context_only = decision["rights_class"] == "CONTEXT_ONLY"
    module_promotion_ineligible = decision["promotion_eligible"] is False
    portfolio_confirms = (
        portfolio_decision["rights_class"] == "CONTEXT_ONLY"
        and portfolio_decision["promotion_eligible"] is False
    )
    dataset_quarantined = manifest.get("quarantined") is True and acq.get("quarantined") is True

    # The claim under attack SURVIVES iff mission.md discloses the rights
    # posture of the data underlying its own headline results, OR the
    # underlying rights decision is not actually CONTEXT_ONLY/ineligible.
    disclosure_gap_confirmed = (
        module_rights_class_context_only
        and module_promotion_ineligible
        and portfolio_confirms
        and dataset_quarantined
        and mission_headline_present
        and len(mission_caveat_hits) == 0
        and n_receipts_no_disclosure == len(RECEIPTS)
        and n_receipts_indexed_clean == len(RECEIPTS)
    )

    diagnostic = {
        "schema": "amphora.viscosity-score.polyverse-rights-disclosure-gap-diagnostic.v1",
        "module_id": "amphora-viscosity-score",
        "claim_under_attack": (
            "amphora-viscosity-score/docs/mission.md standing prose: the "
            "'Empirical benchmark result' sections for Polyverse melt-"
            "viscosity polymer-safe conformal intervals + applicability-"
            "domain audit, and Fox-Flory-Whitten physical baseline vs ML "
            "(building on the parent 5-fold source-safe GBM R^2=0.944 "
            "claim), are presented as this module's honest current Phase-0 "
            "empirical state with no rights caveat, implying the underlying "
            "data is a lawful basis for a scored/derivative KPI."
        ),
        "refutation_criterion": (
            "The claim SURVIVES if mission.md's headline sections disclose "
            "that the underlying Polyverse melt-viscosity dataset is "
            "rights_class=CONTEXT_ONLY / promotion_eligible=false, OR if the "
            "module's own rights ledger in fact permits derivative use. It "
            "is REFUTED if the module's own rights ledger already records "
            "CONTEXT_ONLY + promotion_eligible=false + quarantined=true for "
            "this exact dataset, the portfolio rights-report.json "
            "independently confirms the same, all three headline receipts "
            "are indexed byte-identical in the 66-receipt master manifest "
            "with zero internal rights self-declaration, and mission.md's "
            "headline prose contains none of the caveat markers "
            f"{CAVEAT_STRINGS}."
        ),
        "inputs": {
            "module_rights_exclusion_decision": {
                "path": str(RIGHTS_EXCLUSION.relative_to(ROOT)),
                "sha256": sha(rights_bytes),
                "rights_class": decision["rights_class"],
                "promotion_eligible": decision["promotion_eligible"],
                "basis": decision["basis"],
                "license": decision["license"],
            },
            "acquisition_receipt": {
                "path": str(ACQUISITION_RECEIPT.relative_to(ROOT)),
                "sha256": sha(acq_bytes),
                "quarantined": acq.get("quarantined"),
                "rights_decision_id": acq.get("rights_decision_id"),
            },
            "dataset_manifest": {
                "path": str(DATASET_MANIFEST.relative_to(ROOT)),
                "sha256": sha(manifest_bytes),
                "quarantined": manifest.get("quarantined"),
                "rights_class": manifest.get("rights_class"),
            },
            "portfolio_rights_report": {
                "path": str(PORTFOLIO_RIGHTS_REPORT.relative_to(ROOT)),
                "sha256": sha(portfolio_rights_bytes),
                "polyverse_melt_viscosity_decision": portfolio_decision,
            },
            "master_manifest": {
                "path": str(MASTER_MANIFEST.relative_to(ROOT)),
                "sha256": sha(master_manifest_bytes),
                "n_receipts_indexed_total": master_manifest["kpis"].get("n_receipts")
                    if isinstance(master_manifest["kpis"].get("n_receipts"), int) else None,
            },
            "sibling_portfolio_audit_cited_not_modified": {
                "path": str(SIBLING_AUDIT.relative_to(ROOT)),
                "sha256": sha(sibling_bytes),
                "note": (
                    "Prior cross-module audit already classified 2 of these "
                    "3 receipts POSITIVE_CAPABILITY and 1 COMPARISON, and "
                    "already found self_declares_context_only_rights=false "
                    "for all 3, at the portfolio level. This receipt does "
                    "not repeat that audit; it establishes the narrower, "
                    "module-owned finding that amphora-viscosity-score's "
                    "own mission.md was never amended in response."
                ),
            },
            "mission_md": {
                "path": str(MISSION.relative_to(ROOT)),
                "sha256": sha(mission_bytes),
                "headline_results_present": mission_headline_present,
                "caveat_strings_checked": CAVEAT_STRINGS,
                "caveat_strings_found": mission_caveat_hits,
            },
        },
        "receipt_checks": receipt_checks,
        "results": {
            "module_rights_class_context_only": module_rights_class_context_only,
            "module_promotion_ineligible": module_promotion_ineligible,
            "portfolio_rights_report_confirms": portfolio_confirms,
            "dataset_marked_quarantined_in_tree": dataset_quarantined,
            "mission_md_headline_present": mission_headline_present,
            "mission_md_discloses_rights_caveat": len(mission_caveat_hits) > 0,
            "n_receipts_checked": len(RECEIPTS),
            "n_receipts_with_no_internal_rights_disclosure": n_receipts_no_disclosure,
            "n_receipts_indexed_byte_clean_in_master_manifest": n_receipts_indexed_clean,
        },
        "disclosure_gap_confirmed": disclosure_gap_confirmed,
        "verdict": "REFUTED" if disclosure_gap_confirmed else "SURVIVED",
        "does_not_close": (
            "Does not modify docs/mission.md, the three Polyverse receipts, "
            "the 66-receipt master manifest, the portfolio rights-report.json, "
            "or the sibling amphora-redteam-audit diagnostic. Does not open, "
            "parse, or derive any scientific value from the underlying "
            "quarantined Polyverse row-level data -- only rights-ledger "
            "metadata (rights.json / acquisition-receipt.json / manifest.json "
            "quarantine flags) and already-signed receipt/manifest bytes were "
            "read. Does not resolve the CONTEXT_ONLY/promotion_eligible=false "
            "rights question -- that remains a human legal/counsel action per "
            "the module's own rights-exclusion decision. Does not assert the "
            "underlying physics/ML findings (R^2=0.944, conformal coverage "
            "0.897, FFW-beats-ML) are numerically wrong; it asserts they are "
            "not admissible, undisclosed Phase-0 evidence while the rights "
            "question is open."
        ),
    }
    out = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
    Path(out_path).write_bytes(out)
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent / "diagnostic.canonical.json"))
