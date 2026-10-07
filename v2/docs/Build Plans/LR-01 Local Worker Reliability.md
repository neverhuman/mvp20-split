# LR-01 Local Worker Reliability

## Canonical tracker

- Last refreshed: `2026-10-07 10:52:01` (America/Chicago).

- Status: queued; not activated. Owner: Deployment/SDK transport diagnostics, with Runtime retaining acceptance authority.
- Completion: **0%**, 0/4 deliveries; Build0%, Acceptance0%.
- Prerequisite: BP-09 final handoff; activation audit and MBT priority selection.
- Current task: none. Next gate: R1 bounded reproduction specification.
- Scope: explain retained intermittent local worker failures and qualify a bounded repair.
- Blockers: no owner decision for existing local diagnostic scope; paid model calls are unnecessary.

## Evidence and boundary

BP-09.04 retained rebuilt-evaluator exit2 after12 completions and unchanged collector
exit3 after14. The latter still had lease/deadline time. A third15-invocation run
passed, as did750 read-only transport requests; neither proves repair. See
[reconstruction evidence](../Audits/Evidence/BP-09-Deployment/Evaluator_Reconstruction.json)
and [drift dashboard](../Audits/Architecture%20Drift.md). Preserve those histories.

R1: define bounded, no-model reproduction using actual worker writes, scoped public
attempt timing and payload-free transport diagnostics. State trials/time budget
before running; no indefinite retry-until-green or raw secret-bearing logs.

R2: isolate failure and implement the smallest owned repair with direct regression
tests. If it cannot be reproduced, retain unresolved status; do not invent a cause.
Any retry must preserve exact replay identity and Runtime fencing authority.

R3: run predeclared repeated actual-worker trials, including failed response/receipt
reconciliation and expiry boundaries. Report every trial, measured rate and limits.
Preserve successful and failed campaign/attempt history and drain proofs.

V1: qualify the changed owner independently, demonstrate unchanged public behavior,
update module README/coverage and scoped drift audit, then archive. No production
soak/HA guarantee follows from this bounded local qualification.

This successor does not reopen BP-09, change scientific eligibility, repin active
campaigns or authorize cluster deployment. Tests remain in each changed module's
owned folders; a shared transport bug is not authority to merge services.
