# potlife-kpi-envelope-disclosure-gap-v1

AUDIT_ONLY. Attacks the standing `docs/mission.md` claim: "the Arrhenius
model reproduces published epoxy-amine pot-life temperature-scaling to
under 15% error across a 30-degree temperature range (10°C to 40°C)",
which frames the signed `held_out_temperature_extrapolation_mape` KPI
metric (PASSED, ceiling 0.25, observed 0.156 -- but evaluated only at
the interior 30°C leg).

Recomputing the identical reference-anchor Arrhenius rule at the other
held-out leg present in the same locked fixture (40°C) gives MAPE =
25.12%, which breaches both the mission.md 15% figure and the KPI's own
`held_out_temperature_extrapolation_mape_ceiling` (25%). The bias is
unidirectional in 12/12 systems (systematic under-prediction of pot life
as temperature rises), not sampling noise.

This exact 40°C ceiling breach was already computed and signed on
2026-07-27 in the sibling receipt
`evidence/audit/potlife-arrhenius-curvature-mechanism-v1/...dsse.json`
(`results.legs_breaching_kpi_ceiling == ["40C"]`), but `docs/mission.md`
and the signed KPI (both dated 2026-07-21, i.e. predating that
disclosure) were never amended afterward to qualify or retract the
blanket 15%-across-the-envelope claim. This receipt formalizes that
disclosure gap as a REFUTED verdict on the standing prose claim, using
only already-accepted, SHA-256-pinned evidence already in the module
(no new data, no rights exposure).

Does not modify mission.md, the signed KPI, the locked fixture, or any
prior receipt. Flags mission.md/KPI framing for human correction:
either drop the blanket "across 10°C-40°C" language or add a per-leg
40°C caveat, and consider whether `held_out_temperature_extrapolation_mape`
should be redefined to test the full envelope boundary rather than one
interior point.
