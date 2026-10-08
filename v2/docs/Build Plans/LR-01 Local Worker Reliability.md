# LR-01 Local Worker Reliability

## Canonical tracker

- Last refreshed: `2026-10-08 18:42:19` (America/Chicago).

- Status: paused by owner direction for UI-01; R2 diagnostic position preserved. Owner: Deployment/SDK transport diagnostics, with Runtime retaining acceptance authority.
- Completion: **25%**, 1/4 deliveries; Build33.33%, Acceptance0%.
- Prerequisite: BP-09 final handoff; activation audit and MBT priority selection.
- Current task: R2 receipt-level fault isolation; baseline complete. Paused for UI-01 overhaul priority. Next gate: evidence-supported isolation/repair.
- Scope: explain retained intermittent local worker failures and qualify a bounded repair.
- Blockers: no owner decision for existing local diagnostic scope; paid model calls are unnecessary.

## Next-week integration dependency

For2026-10-12 through2026-10-16, pull R2 diagnosis forward only if actual UI-01.05/R1
browser-started campaigns encounter the retained worker failure. Preserve all failed
trials, exact tool/version/configuration and denominators. Return to the interrupted
UI gate after bounded repair verification; do not promote a few successful trials
to a reliability percentage. R1=100%, R2/R3/V1=0%, overall25% remain unchanged.

## Evidence and boundary

## Activation coherence and R1 specification

2026-10-07 15:58:00, baseline f81351eb: corrected_ready. BP-09 and SQ-01 are
closed; exact failure histories, immutable Linux images, restored stores, installed
Deployment0.15 and public Runtime timing/TLS counters exist. No new provider,
scientific input or contract decision is necessary. UI-R01 separately owns feedback
reads and does not broaden this plan. R1 is complete; R2/R3/V1 remain0%.

Run exactly three sequential new synthetic two-generation campaigns using
verify_managed_numeric_campaign.py, the accepted rebuilt materials and frozen
owner locks. Each execution has the existing600second deadline,15invocations,
six evaluations and three checkpoints. Stop each failed campaign through its
existing failure cleanup; do not resume a failed history or retry until green.
Stop the series if cleanup cannot prove owner drain, to avoid contaminated trials.
No paid calls, shared Docker outage, store reset, migrations or frozen asset updates.
Each trial uses a new project, admission, configuration and physical container bundle.
Record every outcome, Runtime attempt timing, last controller counters, receipts,
retentions and drain status. Fixed total execution budget1800seconds plus bounded
startup/drain. Three passes are a diagnostic sample, not a repair or soak claim.

R2 investigates any observed fault using these bounded records. If all pass or the
fault lacks a causal trace, retain unresolved status and specify the smallest
additional diagnostic probe before executing it. R3 fault/reconciliation and V1
independent repair acceptance cannot be claimed from this baseline alone.

## Retained evidence

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

## 2026-10-07 16:08:18 ? R2 baseline observation

Exactly three campaigns completed15 invocations each in108.329/106.922/109.610s;
all three owner sets drained. No paid calls. Raw evidence:
.test-results/lr01-managed-baseline-20261007a. [Summary](../Audits/Evidence/LR-01-Reliability/Managed_Baseline.json).
Trial1's completed snapshot also records evolution-vary exit3. The older helper
reports campaign completion before inspecting terminal-snapshot faults; the new
series ledger now preserves both facts. This is not a fault-free result. Runtime
rejects claims after terminal state, but that explanation is not established for
this worker until its exact command receipt is inspected. Earlier active-run
failures remain unresolved; R2 has no completion credit and no repair is claimed.

Next: Runtime-owned read-only diagnostic of exact scoped command receipts for the
three trials and retained earlier failures; distinguish terminal claim rejection
from active-attempt failure. Do not query Runtime SQL from dev/another service.
Owner requested local UI; serve the frozen demo after the series drains. This
resource interruption preserves R2 position; resume after UI-01 priority is released, not automatically when the demo stops.
