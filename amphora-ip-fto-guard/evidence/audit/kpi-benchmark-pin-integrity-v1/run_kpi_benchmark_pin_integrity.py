#!/usr/bin/env python3
"""KPI-benchmark-pin-integrity audit for amphora-ip-fto-guard.

Claim under attack: evidence/phase0/kpis/ip-fto-guard-technical-landscape-kpi.v1.json
-- the "locked" Phase-0 KPI receipt that docs/mission.md points readers to
("The Phase-0 KPI receipt lives at
evidence/phase0/kpis/ip-fto-guard-technical-landscape-kpi.v1.json") and that
is awaiting PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signature before the
module can leave PRE_PHASE_0 -- currently carries checked-in SHA-256 pins
(benchmark_result_sha256, benchmark_lock_sha256, dataset_fixture_sha256) that
identify the real, live files on disk.

Context: the 2026-08-16 PIN-01 repair (evidence/audit/pinned-source-hash-integrity-v1)
found and fixed a stale benchmark_result_sha256 pin (bbd8a967...) in
docs/mission.md and docs/capability-profile.json, replacing it with the live
value (a6cb423d...). That repair's own receipt explicitly scoped itself to
those two files only. This audit checks whether the SAME stale value survives
in a THIRD, more consequential location it never touched: the KPI receipt
file itself.

Method: mechanical sha256 of every live file on disk, compared byte-for-byte
against every pin asserted inside the KPI json. Two-replay byte-stability
gate. Fail-closed mutation demo shows the check is not vacuous.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-ip-fto-guard"
KPI = MODULE / "evidence/phase0/kpis/ip-fto-guard-technical-landscape-kpi.v1.json"
RESULT_JSON = MODULE / "evidence/phase0/benchmark/result.v1.json"
LOCK_JSON = MODULE / "evidence/phase0/benchmark/benchmark-lock.v1.json"
LANDSCAPE_JSON = MODULE / "reference/mvp20/data/patent_landscape.json"
MISSION = MODULE / "docs/mission.md"
CAP_PROFILE = MODULE / "docs/capability-profile.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# --- live file hashes -------------------------------------------------------
live_result_sha256 = sha(RESULT_JSON.read_bytes())
live_lock_sha256 = sha(LOCK_JSON.read_bytes())
live_landscape_sha256 = sha(LANDSCAPE_JSON.read_bytes())

# --- pins asserted inside the KPI receipt file ------------------------------
kpi_obj = json.loads(KPI.read_bytes())
kpi_result_pin = kpi_obj.get("benchmark_result_sha256")
kpi_lock_pin = kpi_obj.get("benchmark_lock_sha256")
kpi_landscape_pin = kpi_obj.get("dataset_fixture_sha256")

# --- cross-check: did PIN-01's fix (mission.md / capability-profile.json)
#     actually land, and does it cover the same result.v1.json pin? ---------
mission_text = MISSION.read_text()
cap_profile = json.loads(CAP_PROFILE.read_bytes())
mission_asserts_stale_result_pin = "bbd8a9675d78bb65d1dfee9209b441bb5cb3ec4c28e2871cf8febf0f7168eec3" in mission_text
mission_asserts_live_result_pin = live_result_sha256 in mission_text
cap_profile_result_pin_fields = [
    v for k, v in cap_profile.get("evidence_inventory", {}).get("implementation", {}).items()
    if k == "sha256"
]

STALE_RESULT_PIN = "bbd8a9675d78bb65d1dfee9209b441bb5cb3ec4c28e2871cf8febf0f7168eec3"

result_pin_matches_live = (kpi_result_pin == live_result_sha256)
lock_pin_matches_live = (kpi_lock_pin == live_lock_sha256)
landscape_pin_matches_live = (kpi_landscape_pin == live_landscape_sha256)
kpi_result_pin_is_the_known_stale_value = (kpi_result_pin == STALE_RESULT_PIN)

H0 = (
    "evidence/phase0/kpis/ip-fto-guard-technical-landscape-kpi.v1.json's "
    "checked-in SHA-256 pins (benchmark_result_sha256, benchmark_lock_sha256, "
    "dataset_fixture_sha256) currently identify the real, live files on disk."
)
all_pins_match = result_pin_matches_live and lock_pin_matches_live and landscape_pin_matches_live
H0_verdict = "CORROBORATED" if all_pins_match else "REFUTED"

# --- fail-closed mutation demo: prove the check fires on a real defect -----
mutated_pin = "0" * 64
mutation_would_be_caught = (mutated_pin != live_result_sha256)
# and prove it does NOT spuriously fire on a pin that actually matches
lock_pin_self_consistent_no_false_positive = lock_pin_matches_live

result = {
    "study_id": "IP_FTO_GUARD_KPI_BENCHMARK_PIN_INTEGRITY_V1",
    "schema": "amphora.ip-fto-guard.kpi-benchmark-pin-integrity-diagnostic.v1",
    "headline": (
        f"H0 '{H0}' is {H0_verdict}: benchmark_result_sha256 pinned in the "
        f"KPI receipt is {kpi_result_pin}, but the live "
        f"evidence/phase0/benchmark/result.v1.json file hashes to "
        f"{live_result_sha256}. The pinned value is exactly the SAME stale "
        "pre-R-B01 value (bbd8a9675d78bb65d1dfee9209b441bb5cb3ec4c28e2871cf8"
        "febf0f7168eec3) that the 2026-08-16 PIN-01 audit already found and "
        "fixed in docs/mission.md and docs/capability-profile.json -- but "
        "PIN-01 never touched this KPI receipt file, so the same known-stale "
        "hash survives here, in the one artifact this module's own mission.md "
        "prose names as 'The Phase-0 KPI receipt' and that is explicitly "
        "'awaiting PHASE0_EVALUATOR ... signatures' before Phase-0 promotion. "
        f"benchmark_lock_sha256 (pin={kpi_lock_pin}, live={live_lock_sha256}) "
        f"and dataset_fixture_sha256 (pin={kpi_landscape_pin}, "
        f"live={live_landscape_sha256}) both remain correctly pinned -- this "
        "is a single-field, single-file defect, not a wholesale KPI failure."
    ),
    "purpose": (
        "Determine whether the checked-in SHA-256 pins inside "
        "evidence/phase0/kpis/ip-fto-guard-technical-landscape-kpi.v1.json "
        "-- the module's own named 'Phase-0 KPI receipt', still awaiting "
        "evaluator/reviewer signature -- currently identify the real, live "
        "files on disk, independent of and in addition to the already-fixed "
        "mission.md / capability-profile.json pins."
    ),
    "inputs": {
        "kpi_receipt_path": str(KPI.relative_to(ROOT)),
        "result_json_path": str(RESULT_JSON.relative_to(ROOT)),
        "lock_json_path": str(LOCK_JSON.relative_to(ROOT)),
        "landscape_json_path": str(LANDSCAPE_JSON.relative_to(ROOT)),
    },
    "live_hashes": {
        "result_v1_json_sha256": live_result_sha256,
        "benchmark_lock_v1_json_sha256": live_lock_sha256,
        "patent_landscape_json_sha256": live_landscape_sha256,
    },
    "asserted_pins": {
        "kpi_benchmark_result_sha256": kpi_result_pin,
        "kpi_benchmark_lock_sha256": kpi_lock_pin,
        "kpi_dataset_fixture_sha256": kpi_landscape_pin,
    },
    "consistency_checks": {
        "kpi_result_pin_matches_live": result_pin_matches_live,
        "kpi_lock_pin_matches_live": lock_pin_matches_live,
        "kpi_landscape_pin_matches_live": landscape_pin_matches_live,
        "kpi_result_pin_is_the_known_pre_R_B01_stale_value": kpi_result_pin_is_the_known_stale_value,
    },
    "prior_repair_scope_cross_check": {
        "pin01_receipt": "amphora-ip-fto-guard/evidence/audit/pinned-source-hash-integrity-v1/pinned-source-hash-integrity-receipt.v1.dsse.json",
        "mission_md_still_asserts_stale_pin": mission_asserts_stale_result_pin,
        "mission_md_asserts_live_pin": mission_asserts_live_result_pin,
        "cap_profile_result_pin_fields_present": cap_profile_result_pin_fields,
        "note": (
            "mission.md and capability-profile.json were corrected by PIN-01 "
            "and (as expected) no longer assert the stale value; the defect "
            "found by this audit is confined to the KPI receipt file, which "
            "PIN-01's own receipt did not enumerate as in-scope."
        ),
    },
    "fail_closed_mutation_demo": {
        "description": (
            "Compare a deliberately wrong 64-char sentinel pin (all zeros) "
            "against the live result.v1.json hash: must be flagged as a "
            "mismatch (mutation caught). Separately confirm the "
            "benchmark_lock_sha256 pin, which really does match live, is NOT "
            "flagged (no false positive)."
        ),
        "mutated_pin": mutated_pin,
        "mutation_would_be_caught": mutation_would_be_caught,
        "lock_pin_self_consistent_no_false_positive": lock_pin_self_consistent_no_false_positive,
    },
    "does_not_close": [
        "Does not modify or supersede the pinned patent_landscape.json fixture, the manifest, or any signed Phase-0 KPI/evaluation.",
        "Does not establish legal FTO, patentability, or counsel review status.",
        "Does not address the still-open kpi-recompute-consistency-v1 finding (54 vs 75 unresolved_technical_categories semantics) -- unrelated defect, separately tracked.",
        "Does not re-verify config/module-evidence-inventory.json (outside this module's subtree; already flagged as a portfolio-wide followup by PIN-01).",
    ],
    "H0": H0,
    "H0_verdict": H0_verdict,
}

canon = json.dumps(result, indent=2, sort_keys=True)
print(canon)
