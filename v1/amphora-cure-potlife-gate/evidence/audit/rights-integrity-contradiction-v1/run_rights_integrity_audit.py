"""Rights-integrity contradiction audit for amphora-cure-potlife-gate.

AUDIT_ONLY red-team science artifact. Promotes nothing, signs no phase0
evaluation/review receipt, modifies no existing receipt, manifest, KPI, or
source-lock. Runs on the canonical host (xbabe2) only.

CAMPAIGN ITEM C5, ATTACK (B) -- RIGHTS INTEGRITY
--------------------------------------------------
Claim under attack (second half): "the KPI's 'all gates pass' verdict is
well-founded" (amphora-cure-potlife-gate/evidence/phase0/kpis/
cure-potlife-arrhenius-kpi.v1.json).

This script reads (never modifies) the module's own rights-governance chain
and its signed KPI, and reports whether the "gates pass" framing honestly
represents the rights state. It performs NO computation on any quarantined
source content -- it reads only the rights METADATA files (source-lock,
dataset-manifest, source census), never the quarantined payload bytes
themselves, and the KPI/fixture JSON already on disk.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"

SOURCE_LOCK = MOD / "evidence/phase0/sources/source-lock.v2.json"
DATASET_MANIFEST = MOD / "evidence/phase0/dataset/dataset-manifest.v1.json"
CURE_SOURCES = ROOT / "config/program/cure-sources.v1.json"
KPI = MOD / "evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"
FIXTURE = MOD / "reference/phase0-cure-potlife-known-answer.v1.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main():
    sl_bytes = SOURCE_LOCK.read_bytes()
    sl = json.loads(sl_bytes)
    dm_bytes = DATASET_MANIFEST.read_bytes()
    dm = json.loads(dm_bytes)
    cs_bytes = CURE_SOURCES.read_bytes()
    cs = json.loads(cs_bytes)
    kpi_bytes = KPI.read_bytes()
    kpi = json.loads(kpi_bytes)
    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes)

    # --- fact 1: the module's own rights gate ---
    rights_gate_passed = sl["rights_gate_passed"]
    eligible_sources = sl["eligible_sources"]
    excluded_sources = sl["excluded_sources"]

    # --- fact 2: dataset manifest agrees ---
    dm_rights_gate_passed = dm["rights_gate_passed"]
    dm_scientific_success_asserted = dm["scientific_success_asserted"]

    # --- fact 3: the module's own source census: every in-tree cure TDS source
    # is quarantined with an explicit "do not benchmark" restriction ---
    census_sources = cs["sources"]
    n_census = len(census_sources)
    n_quarantined = sum(1 for s in census_sources if s["rights_status"] == "QUARANTINED")
    n_no_derivatives = sum(1 for s in census_sources if s["eligible_for_derivatives"] is False)
    do_not_benchmark_restriction_present = any(
        "Do not train or benchmark" in r
        for s in census_sources for r in s.get("restrictions", []))

    # --- fact 4: traceability -- does the KPI's dataset actually rest on
    # numbers pulled from named vendor TDS documents? ---
    fixture_sha_observed = sha(fixture_bytes)
    fixture_sha_claimed_by_kpi = kpi["dataset_fixture_sha256"]
    fixture_hash_matches_kpi = (fixture_sha_observed == fixture_sha_claimed_by_kpi)

    tds_named_sources = sorted({
        s["pot_life_source"] for s in fixture["systems"]
    })
    n_systems_pot_life_from_named_tds = sum(
        1 for s in fixture["systems"] if "TDS" in s["pot_life_source"])

    fixture_self_asserted_rights = fixture["rights"]
    fixture_appears_in_eligible_sources = any(
        "phase0-cure-potlife-known-answer" in str(e) for e in eligible_sources)
    fixture_appears_in_excluded_sources = any(
        "phase0-cure-potlife-known-answer" in str(e.get("module_relative_path", ""))
        for e in excluded_sources)

    # --- fact 5: does the KPI itself claim gates pass? ---
    kpi_declares_deterministic_gates_passed = kpi["phase0_deterministic_gates_passed"]
    kpi_all_metric_passed_flags = [m["passed"] for m in kpi["metrics"]]
    kpi_all_metrics_pass = all(kpi_all_metric_passed_flags)

    # --- the contradiction, stated plainly ---
    contradiction_present = bool(
        (rights_gate_passed is False)
        and (len(eligible_sources) == 0)
        and (n_quarantined == n_census)
        and (n_no_derivatives == n_census)
        and (kpi_declares_deterministic_gates_passed is True)
        and kpi_all_metrics_pass
    )

    self_assertion_ungoverned = bool(
        (not fixture_appears_in_eligible_sources)
        and (not fixture_appears_in_excluded_sources)
        and fixture_self_asserted_rights.get("status") == "ACCEPTED"
        and fixture_self_asserted_rights.get("eligible_for_derivatives") is True
        and n_systems_pot_life_from_named_tds > 0
    )

    diag = {
        "schema": "amphora.cure-potlife-gate.rights-integrity-contradiction.diagnostic.v1",
        "authority": "AUDIT_ONLY",
        "target_module": "amphora-cure-potlife-gate",
        "campaign_item_id": "C5",
        "claim_under_attack": {
            "receipt_path": "amphora-cure-potlife-gate/evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json",
            "claim_text": "the KPI's 'all gates pass' verdict is well-founded",
        },
        "method": (
            "Reads only rights-metadata files (source-lock, dataset-manifest, "
            "source census) and the KPI/known-answer-fixture JSON already on "
            "disk. Opens, parses, or derives from NO quarantined source payload "
            "content."
        ),
        "facts": {
            "source_lock": {
                "path": "amphora-cure-potlife-gate/evidence/phase0/sources/source-lock.v2.json",
                "sha256": sha(sl_bytes),
                "rights_gate_passed": rights_gate_passed,
                "n_eligible_sources": len(eligible_sources),
                "n_excluded_sources": len(excluded_sources),
            },
            "dataset_manifest": {
                "path": "amphora-cure-potlife-gate/evidence/phase0/dataset/dataset-manifest.v1.json",
                "sha256": sha(dm_bytes),
                "rights_gate_passed": dm_rights_gate_passed,
                "scientific_success_asserted": dm_scientific_success_asserted,
                "dataset_kind": dm["dataset_kind"],
            },
            "source_census": {
                "path": "config/program/cure-sources.v1.json",
                "sha256": sha(cs_bytes),
                "n_sources": n_census,
                "n_quarantined": n_quarantined,
                "n_eligible_for_derivatives_false": n_no_derivatives,
                "do_not_benchmark_restriction_present": do_not_benchmark_restriction_present,
                "source_ids": [s["source_id"] for s in census_sources],
            },
            "kpi": {
                "path": "amphora-cure-potlife-gate/evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json",
                "sha256": sha(kpi_bytes),
                "phase0_deterministic_gates_passed": kpi_declares_deterministic_gates_passed,
                "all_6_metrics_passed": kpi_all_metrics_pass,
                "dataset_fixture_sha256_field": fixture_sha_claimed_by_kpi,
            },
            "known_answer_fixture": {
                "path": "amphora-cure-potlife-gate/reference/phase0-cure-potlife-known-answer.v1.json",
                "sha256_observed": fixture_sha_observed,
                "matches_kpi_dataset_fixture_sha256": fixture_hash_matches_kpi,
                "self_asserted_rights_block": fixture_self_asserted_rights,
                "n_systems_with_pot_life_value_sourced_from_named_vendor_tds": n_systems_pot_life_from_named_tds,
                "n_systems_total": len(fixture["systems"]),
                "named_tds_sources_cited": tds_named_sources,
                "appears_in_source_lock_eligible_sources": fixture_appears_in_eligible_sources,
                "appears_in_source_lock_excluded_sources": fixture_appears_in_excluded_sources,
            },
        },
        "findings": {
            "contradiction_present": contradiction_present,
            "contradiction_statement": (
                "The module's own source-lock declares rights_gate_passed=false "
                "with ZERO eligible_sources, and its own source census marks "
                "100% (3/3) of in-tree cure TDS sources QUARANTINED / "
                "eligible_for_derivatives=false with an explicit restriction "
                "'Do not train or benchmark until derivative-use eligibility is "
                "established'. Yet the signed Arrhenius KPI declares "
                "phase0_deterministic_gates_passed=true and all 6 of its metrics "
                "passed=true -- i.e. the module WAS benchmarked, on a dataset "
                "whose pot-life values for all 12/12 systems are sourced from "
                "named vendor TDS documents (Dow, Huntsman, Air Products, "
                "Momentive, Mitsubishi)."
            ),
            "self_assertion_ungoverned": self_assertion_ungoverned,
            "self_assertion_statement": (
                "The KPI's dataset_fixture_sha256 field points, byte-for-byte, at "
                "reference/phase0-cure-potlife-known-answer.v1.json. That file "
                "carries its OWN in-file 'rights' block self-declaring "
                "license=CC0-1.0, eligible_for_derivatives=true, status=ACCEPTED "
                "-- a bare assertion with NO signed rights receipt, and the file "
                "appears in NEITHER source-lock.v2.json's eligible_sources (empty) "
                "NOR its excluded_sources list. It sits outside the rights-gate "
                "accounting entirely while its component numbers are drawn "
                "directly from named vendor TDS documents -- the exact category "
                "of material the module's own source census quarantines "
                "elsewhere in the same tree."
            ),
            "well_founded_verdict": (
                "REFUTED" if (contradiction_present or self_assertion_ungoverned) else "SURVIVED"
            ),
            "what_is_true": (
                "The DETERMINISTIC PHYSICS gates (MAPE ceilings, applicability-domain "
                "fail-closed, authority-lock preservation) genuinely do pass -- this is "
                "NOT a claim that the arithmetic or physics is fabricated. Those gates "
                "are computed correctly on the numbers as given."
            ),
            "what_is_false": (
                "The framing that 'all gates pass' therefore means the KPI is a "
                "well-founded, rights-clean Phase-0 artifact. The RIGHTS gate -- a "
                "precondition the module's own source-lock and source census both "
                "gate on -- is failing with zero ledgered eligible sources, on a "
                "dataset whose provenance numbers were never ingested through the "
                "module's own rights pipeline."
            ),
        },
        "does_not_close": [
            "does NOT claim the physics/arithmetic in the KPI is wrong",
            "does NOT flip rights_gate_passed (requires each source ingested "
            "through amphora-source-ledger under a signed rights receipt -- a "
            "human step)",
            "does NOT promote amphora-cure-potlife-gate to PHASE_0",
            "does NOT modify source-lock.v2.json, dataset-manifest.v1.json, "
            "cure-sources.v1.json, the known-answer fixture, the signed KPI, "
            "the manifest, or any prior receipt",
            "does NOT open, parse, or derive from any quarantined source's "
            "payload content -- rights metadata only",
        ],
    }
    return diag


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
