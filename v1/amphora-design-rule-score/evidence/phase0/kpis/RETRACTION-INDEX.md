# RETRACTION INDEX - amphora-design-rule-score

Append-only index of superseded claims. Entries record what was retracted/superseded, by what, and when. Original artifacts are never modified or deleted.

## R-A11 - anchored signature-identity re-issue (2026-08-03)

Scope note: SIGNATURE IDENTITY ONLY is superseded. The scientific content of the original receipt is NOT retracted; it carries forward unchanged (re-verified byte-intact) under the anchored re-issue.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| The DSSE signature identity of `amphora-design-rule-score/benchmarks/guth-gold-physical-baseline-v1/physical_baseline_receipt.v1.json` (keyid `phase0-evaluator-audit-3ef6b35cdbbfea74a96a5c9b98a515d5`) is a trust-anchored Phase-0 evaluator identity resolvable in `config/phase0-trust-store.v1.json` | `amphora-design-rule-score/benchmarks/guth-gold-physical-baseline-v1/physical_baseline_receipt.v1.json` (its own signature/signing_key block records the defective identity; strict trust-store lookup fails) | `amphora-design-rule-score/benchmarks/guth-gold-physical-baseline-v1/physical_baseline_receipt.v1.anchored-reissue.v1.json` (anchored re-issue, keyid `phase0-evaluator-3ef6b35...`; repair_item R-A11, repair_mode interactive-2026-08-03) | 2026-08-03 |

## W-D-DESIGN - repair-done receipt re-issue with extended sweep (2026-08-13)

Scope note: v1 is NOT retracted or deleted; its scientific content (12 named sources, 2 qualifying finds) carries forward byte-intact. v2 extends the sweep to 13 named sources + 5 additional repository-class searches (Dryad, OSF, GitHub, Materials Data Facility/NOMAD, Data-in-Brief-targeted Mendeley Data) and explicitly resolves the campaign-item-status ambiguity the launcher flagged (`done_rejected: outcome=BLOCKED_DATA done_check=pass`) by recording campaign_item_status=done alongside the BLOCKED_DATA outcome, per the item's own done_criterion.

| claim | superseded receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-design-rule-score/evidence/phase0/repairs/W-D-DESIGN/done/w-d-design-done-receipt.v1.dsse.json` (12-source sweep, done_criterion_met=true, no explicit campaign_item_status declared) | `amphora-design-rule-score/evidence/phase0/repairs/W-D-DESIGN/done/w-d-design-done-receipt.v1.dsse.json` (sha256 aa44371a4bccbab03bff2ce886d113bc818f78261511c6d33d09ef5bd83b5598) | `amphora-design-rule-score/evidence/phase0/repairs/W-D-DESIGN/done/w-d-design-done-receipt.v2.dsse.json` (13-source sweep, campaign_item_status_recommendation=done; fire_id 20260813T020001-2126520-6a7df36eb7b9) | 2026-08-13 |
