# Bounded diagnostics and probes

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.

Use small discriminating probes, preserve failed evidence and isolate contaminated state. A provider failure report is an observation, not a proven cause. The case below is historical local evidence, not a claim about current provider behavior.

## Development debugging patterns

- Remove temporary test containers after their verification completes (owner instruction, 2026-10-14). Do not leave stopped test containers accumulating. Distinguish temporary fixtures from the active demo and explicitly retained recovery state; preserve user data and volumes unless their removal is authorized. Test workflows must include owned-container cleanup.
- Prefer iterative deconstruction when a rich behavior fails and the intended approach is still valuable. Start from the smallest known-good shape, add one meaningful component at a time, and keep passing components instead of reverting to a weaker design by default.
- Make component probes reusable when they expose a real system failure mode. A good probe should name each variant, keep the production route or boundary intact when possible, isolate rendered inputs independently, and record enough prompt/shape/telemetry markers to explain both passes and failures.
- Restart or reset stateful runtimes between isolated model-failure probes when a failed run can poison later evidence. Treat contaminated follow-on failures as invalid until the runtime has been reset and the variant is rerun.
- When a component breaks, repair that component or insertion path rather than removing the whole context category. Preserve the non-breaking prefix as the next accepted baseline and validate the repair with the same additive ladder before activation.

## Provider schema isolation example

Specific observed failure (2026-10-12, UI-01.08e): on the pinned OpenAI Responses
model `gpt-5.4-mini-2026-03-17`, a tiny strict schema with numeric bounds
`minimum: -1e100` and `maximum: 1e100` reproduced HTTP200
`incomplete/max_output_tokens`, empty output and explicit zero token usage.
Removing only those bounds from `NumberConstant.value` let the full generation
schema succeed. Planning0.133.0 introduces v6/fit.v8 to omit these two bounds only
from provider generation; local numeric range and finite-value validation remain
unchanged. Prior profiles and all eight retained request replays remain unchanged.
This isolates a triggering schema fragment, not the provider's internal cause or
exact failing threshold. Schema-probe success does not qualify full campaign
generation. Diagnose such failures through bounded isolation before increasing
budgets or weakening contracts; the reported truncation reason alone is not proof
of token exhaustion.
