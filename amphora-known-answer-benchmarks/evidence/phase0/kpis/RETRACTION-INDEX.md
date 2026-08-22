# RETRACTION INDEX - amphora-known-answer-benchmarks

Append-only index of superseded claims. Entries record what was retracted/superseded, by what, and when. Original artifacts are never modified or deleted.

## R-A05 - volume-solids mass-basis conflation correction (2026-08-03)

Scope note: the REFERENCE 'actual' VALUE of one control is superseded. No VERIFIED_PASS/FAIL status flips; the 6/6 arithmetic pass-rate is numerically unchanged. Original artifacts are byte-intact.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| ARITH-A221-X70P1-VOLUME-SOLIDS 'actual' = 43.7% in `amphora-known-answer-benchmarks/reference/mvp20/out/control_by_control_receipt.v1.json` (sha256 `be537c06a3cc325b4ecd6ee71bd6ed284d570883bb2f123e7c969d574c60d3cc`; same value as `recomputed` in `reference/mvp20/out/arithmetic_audit.json` row id=A221-X70P1) is a correct independent recomputation from the cited Evonik Ancamide 221 EMEA TDS | `amphora-known-answer-benchmarks/evidence/audit/arith-volume-solids-mass-basis-conflation-v1/receipt.v1.dsse.json` (43.7 reproduces only via invalid mass-fraction weighting of volume-basis percentages; correct volume-weighted recompute = 42.4165) | `amphora-known-answer-benchmarks/evidence/phase0/repairs/R-A05/done/R-A05.done-receipt.v1.dsse.json` (corrected actual 42.4165, 4dp-matched to the refuting recompute; full 2/2 volume-solids sweep incl. A702B75P1 delta explanation; repair_item R-A05, repair_mode interactive-2026-08-03) | 2026-08-03 |
