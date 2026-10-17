# Audits and closeout

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.

Process lives here. Completed audit records stay in [docs/Audits](../../Audits/); unresolved drift and documentation debt keep their existing dashboards. Pre-activation coherence review follows [plan execution](../planning/Plan_Execution.md); it earns no implementation credit.


## Purpose and handoff

| Element | Meaning |
|---|---|
| Why it exists | Determine whether the declared plan/design/implementation boundary agrees with evidence. |
| Inputs | Bounded claim set, reviewed revision, relevant architecture/contracts and independent observations. |
| Output | Findings with evidence, blocking classification, owner and disposition. |
| Completion test | Every in-scope claim is assessed; acceptance-invalidating findings block the relevant closeout, with follow-ups explicitly owned. |

## Closeout drift audit

At each plan completion, perform a component-scoped architecture drift audit **after implementation/acceptance gates and before archival**. This also applies to a completed child implementation plan; a parent closeout verifies integration without repeating unchanged child audits.

1. Bound the audit to components and directly affected contracts identified by the plan's change/evidence record.
2. Compare architecture claims, module READMEs, source, applicable generated inventories and acceptance evidence. Check ownership, schemas/APIs, state/lifecycle, side effects, privacy, configuration and runtime boundaries.
3. Record timestamp, reviewed revision or working-tree scope, findings, verification and disposition using the [audit template](../templates/Plan%20Audit%20Template.md). Repair in-scope discrepancies; acceptance-invalidating drift blocks closeout. Assign explicitly nonblocking findings to an owner/successor with evidence.
4. Update the drift dashboard; aligned entries with no follow-up go into history. Preserve final percentages and gate evidence. Keep parent trackers in `Build Plans/Completed/` and child/supporting records in `Build Plans/<family>/Completed/`; repair all inbound and outbound links, and update MBT, plan index and Restore in the same closeout.

Closed and monitoring-only plans stay out of active tables. Regressions or new scope use successors, not reopened old plans. Do not retroactively audit every historical v1 plan. An acceptance-blocking finding cannot be renamed follow-on scope to permit archival.
