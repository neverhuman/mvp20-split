# RETRACTION INDEX - amphora-ip-fto-guard

Refuted claims and the receipts that supersede them. Original artifacts are never rewritten.

## R-A13 - family-26 EP2653485A2 claim chart (2026-08-03)

| claim | refuted-by receipt | superseded-by | date |
|---|---|---|---|
| patent_landscape.json family-26 EP2653485A2 independent claim chart asserted elements "polyurea topcoat" (fabricated) and "low VOC coating system" (unsupported) against claim 1 | amphora-ip-fto-guard/evidence/audit/claim-chart-provenance-v1/claim-chart-provenance-receipt.v1.dsse.json | amphora-ip-fto-guard/evidence/phase0/repairs/R-A13/done/claim-chart-supersede-repair.R-A13.v1.dsse.json | 2026-08-03 |

Note: fixture bytes untouched (sha256 52ada09074f435d515a8286e57b1d31da40fcbe3d0ec4f79a9be754e5cce63dc); the corrected chart lives in the superseding receipt payload. 54 of 60 landscape rows remain audited only by CPC/IPC screen; claim-level follow-up queued as cron campaign item. Ledger line 56 ts erratum embedded in the same receipt (ledger not modified).

## R-B01 - pointer: runtime repairs recorded in amphora-assurance-capabilities (2026-08-03)

| claim | refuted-by receipt | superseded-by | date |
|---|---|---|---|
| metrics.unresolved_technical_categories is populated by the live checked runtime | amphora-ip-fto-guard/evidence/audit/metric-schema-parity-v1/metric-schema-parity-receipt.v1.dsse.json | amphora-assurance-capabilities/evidence/phase0/repairs/R-B01/done/repair-receipt.R-B01.v1.dsse.json | 2026-08-03 |
| boolean_counsel_assertion_ignored is a general reference monitor (pre-repair: 8/8 false negatives vs alternate encodings) | amphora-ip-fto-guard/evidence/audit/counsel-assertion-detection-completeness-v1/counsel-assertion-detection-completeness-receipt.v1.dsse.json | amphora-assurance-capabilities/evidence/phase0/repairs/R-B01/done/repair-receipt.R-B01.v1.dsse.json | 2026-08-03 |

Pointer note: this module has no src/ of its own - the live runtime is the shared crate amphora-assurance-capabilities (evaluate_ip_fto_guard in src/lib.rs), so the R-B01 signed done-receipt, work artifacts, and full retraction section live at amphora-assurance-capabilities/evidence/phase0/repairs/R-B01/ and amphora-assurance-capabilities/evidence/phase0/kpis/RETRACTION-INDEX.md. Re-attack result: 8/8 audit probe encodings now detected, 0 safety breaches, primary KPI populated (unresolved_technical_categories=75), cargo green.

## PIN-01 - stale docs/mission.md + docs/capability-profile.json source-hash pins (2026-08-16)

| claim | refuted-by receipt | superseded-by | date |
|---|---|---|---|
| docs/mission.md's and docs/capability-profile.json's checked-in SHA-256 pins for amphora-assurance-capabilities/src/lib.rs (c0b2540f...) and for evidence/phase0/benchmark/result.v1.json (bbd8a967...) currently identify the real live files | amphora-ip-fto-guard/evidence/audit/pinned-source-hash-integrity-v1/pinned-source-hash-integrity-receipt.v1.dsse.json | amphora-ip-fto-guard/evidence/audit/pinned-source-hash-integrity-v1/pinned-source-hash-integrity-receipt.v1.dsse.json | 2026-08-16 |

Finding: the lib.rs pin (c0b2540f...) never matched ANY commit across the file's full git-tracked history (4 commits, 2026-08-03..2026-08-11); it was already flagged 'already stale before this repair' in the 2026-08-03 R-B01 repair receipt's own  field, with a maintainer follow-up recorded in amphora-assurance-capabilities/evidence/phase0/kpis/RETRACTION-INDEX.md that sat unactioned for 13 days. The result.v1.json pin (bbd8a967...) was the pre-R-B01 value; the file was regenerated to a6cb423d... by R-B01 itself on 2026-08-03 and the prose was never updated to match. Independently confirmed: evaluate_ip_fto_guard's own function body is byte-identical across the entire tracked git history and the live working tree (the two later lib.rs drifts were unrelated edits elsewhere in the shared crate - CroProtocolPackageV2 blueprint-citation logic - not a change to ip-fto-guard's tested behavior), so this is a documentation-pin integrity defect, not an undisclosed behavior change. Repair: docs/mission.md (2 lib.rs occurrences + 1 result.v1.json occurrence) and docs/capability-profile.json (evidence_inventory.implementation.sha256 + evidence_inventory.tests[0].sha256) corrected in the same fire to the live values (lib.rs -> 0fe122cc7434bdad38fc90a812c2c2fc10d431b0ba30fbac179a8bcef0c84f7d; result.v1.json -> a6cb423d8858421e4b0e8c96de063da7eaaa97916a1da71523ffaae2788b6a77). Not fixed (out of this module's subtree, flagged as followup): config/module-evidence-inventory.json repeats the same stale c0b2540f... pin across multiple modules sharing amphora-assurance-capabilities/src/lib.rs.

## PIN-01 - stale docs/mission.md + docs/capability-profile.json source-hash pins (2026-08-16)

| claim | refuted-by receipt | superseded-by | date |
|---|---|---|---|
| docs/mission.md's and docs/capability-profile.json's checked-in SHA-256 pins for amphora-assurance-capabilities/src/lib.rs (c0b2540f...) and for evidence/phase0/benchmark/result.v1.json (bbd8a967...) currently identify the real live files | amphora-ip-fto-guard/evidence/audit/pinned-source-hash-integrity-v1/pinned-source-hash-integrity-receipt.v1.dsse.json | amphora-ip-fto-guard/evidence/audit/pinned-source-hash-integrity-v1/pinned-source-hash-integrity-receipt.v1.dsse.json | 2026-08-16 |

Finding: the lib.rs pin (c0b2540f...) never matched ANY commit across the file's full git-tracked history (4 commits, 2026-08-03..2026-08-11); it was already flagged "already stale before this repair" in the 2026-08-03 R-B01 repair receipt's own `known_stale_prose_pins_not_modified` field, with a maintainer follow-up recorded in amphora-assurance-capabilities/evidence/phase0/kpis/RETRACTION-INDEX.md that sat unactioned for 13 days. The result.v1.json pin (bbd8a967...) was the pre-R-B01 value; the file was regenerated to a6cb423d... by R-B01 itself on 2026-08-03 and the prose was never updated to match. Independently confirmed: evaluate_ip_fto_guard's own function body is byte-identical across the entire tracked git history and the live working tree (the two later lib.rs drifts were unrelated edits elsewhere in the shared crate - CroProtocolPackageV2 blueprint-citation logic - not a change to ip-fto-guard's tested behavior), so this is a documentation-pin integrity defect, not an undisclosed behavior change. Repair: docs/mission.md (2 lib.rs occurrences + 1 result.v1.json occurrence) and docs/capability-profile.json (evidence_inventory.implementation.sha256 + evidence_inventory.tests[0].sha256) corrected in the same fire to the live values (lib.rs -> 0fe122cc7434bdad38fc90a812c2c2fc10d431b0ba30fbac179a8bcef0c84f7d; result.v1.json -> a6cb423d8858421e4b0e8c96de063da7eaaa97916a1da71523ffaae2788b6a77). Not fixed (out of this module's subtree, flagged as followup): config/module-evidence-inventory.json repeats the same stale c0b2540f... pin across multiple modules sharing amphora-assurance-capabilities/src/lib.rs.

## PIN-02 - stale benchmark_result_sha256 pin inside the KPI receipt itself (2026-08-17)

| claim | refuted-by receipt | superseded-by | date |
|---|---|---|---|
| evidence/phase0/kpis/ip-fto-guard-technical-landscape-kpi.v1.json's checked-in benchmark_result_sha256 pin (bbd8a9675d78bb65d1dfee9209b441bb5cb3ec4c28e2871cf8febf0f7168eec3) currently identifies the real live evidence/phase0/benchmark/result.v1.json file | amphora-ip-fto-guard/evidence/audit/kpi-benchmark-pin-integrity-v1/kpi-benchmark-pin-integrity-receipt.v1.dsse.json | amphora-ip-fto-guard/evidence/audit/kpi-benchmark-pin-integrity-v1/kpi-benchmark-pin-integrity-receipt.v1.dsse.json | 2026-08-17 |

Finding: the KPI receipt file that docs/mission.md names as "The Phase-0 KPI receipt" (still unsigned, awaiting PHASE0_EVALUATOR/PHASE0_INTERNAL_REVIEWER per its own `awaiting` field) carried the exact same stale pre-R-B01 benchmark_result_sha256 value that the 2026-08-16 PIN-01 audit already found and fixed in docs/mission.md and docs/capability-profile.json. PIN-01's own receipt scoped itself to those two files only and did not enumerate this KPI file, so the stale pin survived undetected for a further 24 hours. `benchmark_lock_sha256` and `dataset_fixture_sha256` inside the same KPI file were independently checked and both remain correctly pinned -- this was a single-field defect. Repair: `benchmark_result_sha256` corrected from `bbd8a9675d78bb65d1dfee9209b441bb5cb3ec4c28e2871cf8febf0f7168eec3` to `a6cb423d8858421e4b0e8c96de063da7eaaa97916a1da71523ffaae2788b6a77` in the same fire. KPI file sha256 before=7c768c8dca4a5b2fe16f995b65ae9153ef8a27232e5d7036943a22fc6b9570ba, after=c9638d304f5346e5e0aa9d0870292cffe519f4f8e49d7dcd5784429644a2b8d2.
