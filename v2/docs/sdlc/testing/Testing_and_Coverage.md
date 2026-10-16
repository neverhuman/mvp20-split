# Testing and coverage

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.

Select the owning behavior first. Read the [local verification runbook](../delivery/Local_Verification.md) for commands and [diagnostics](Diagnostics.md) for failure investigation. Documentation-only moves use link, content and scope checks; they do not require scientific or service restarts.

## Evidence tiers and exit gates

Verification must match the promised behavior: focused unit/contract checks, integration/recovery/concurrency checks where relevant, and actual user-path or scientific evaluation when the gate requires them. Compilation or a mocked success alone does not prove usable end-to-end behavior or scientific authority. Preserve failures and explicit validation limits; do not weaken tests to close a gate. Avoid repeated broad testing without a new change or unresolved concern.

## Module-owned verification

Tests belong beside the implementation under `<module>/tests/`, subdivided by behavior (for example `graph/`, `admission/`, `api/`). Shared test infrastructure lives in `dev`; shared wire examples may stay under `contracts/fixtures`. Cross-service integration and E2E suites must have explicit owners and separate folders/commands; do not use E2E as the default module feedback loop.

Register each module's source and test paths in `dev/test_scopes.json`. Keep test-to-behavior coverage mapping in its README, including negative/failure cases and known gaps. Run the changed module first, then affected consumers/integration gates. Record line **and branch** coverage for the selected source boundary alongside test results; percentages measure exercised code, not correctness or scientific validation. Contract schema declarations can report 100% from import alone; retain explicit valid/invalid interchange cases. Never infer coverage from test counts or silently claim full coverage from an aggregate percentage. Independent rewrites must preserve the owned contract tests or explicitly version changed behavior.

Canonical owning-plan trackers always carry numeric overall and per-phase completion. MBT mirrors those percentages for every in-flight plan at each meaningful checkpoint and before handoff/commit. Update scope/denominator when work changes; keep acceptance and readiness separate. Archive completed plans instead of leaving stale in-flight rows.
