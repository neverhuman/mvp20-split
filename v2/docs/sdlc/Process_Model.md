# How the development process fits together

The SDLC turns a requested outcome into an implemented, evidenced and supportable change while preserving ownership and authority. Its records let another person or agent resume and assess the work without relying on the previous session's memory. A folder of rules is not sufficient: every process needs a purpose, declared inputs, a usable output and a decision or completion condition.

## Flow and handoffs

| Stage | Consumes | Produces | Question resolved |
|---|---|---|---|
| Frame the outcome | User intent, requirements, constraints and current capability | Bounded outcome, acceptance conditions and explicit exclusions | What are we trying to deliver and why? |
| Select and prepare work | Outcome, dependencies and current tracker | Eligible task, owner, reviewed contract/design and verification approach | Can this work start, and what would prove it? |
| Implement | Owned contracts, current source and declared task | Reviewable change, affected-consumer/state impact and updated module contract | What behavior changed and who is affected? |
| Verify | Acceptance conditions, candidate change and appropriate environment | Reproducible results, failures, limits and unresolved gates | Which promises are actually demonstrated? |
| Review and disposition | Candidate, evidence and contract/architecture comparison | Recorded acceptance, blocking findings or owned follow-ups | Is the declared transition justified? |
| Release or hand off | Accepted candidate, compatibility/state handling and existing authorization | Identified release or exact resume package; applicable operational observations | What version can be used, or how does work continue? |
| Close and learn | Required exits, audit disposition and remaining obligations | Closed tracker, repaired navigation and explicitly assigned successors | Is this bounded commitment finished, and what remains elsewhere? |

These are responsibilities, not seven mandatory meetings or new approval gates. A small reversible change can satisfy them in one short task/evidence record. A contract, stateful service or scientific capability needs the evidence its existing gates require. Do not impose deployment on a documentation-only change or treat a code commit as a deployment.

## Minimum meaning of a process page

Each owning page states what failure it prevents, what inputs it needs, what output another step consumes and how to judge completion. Procedures and templates follow that explanation. Cross-cutting invariants live with their authority; examples and commands must not silently become new product requirements.

## Traceability without duplicate ledgers

Link **requested outcome → owned requirement/design → deliverable/acceptance condition → implementation boundary → verification evidence → disposition**. The plan's acceptance table carries these links at the useful delivery level; no separate universal database or per-file bureaucracy is required.

Use [tracker design](planning/Tracker_Design.md) for the information model and [plan execution](planning/Plan_Execution.md) for operating discipline. Module READMEs describe the current implementation contract; Architecture describes system design; audits record comparisons; Restore points to the exact current work. Repeating the same status in several places without a clear owner increases ambiguity rather than continuity.

## Process documentation versus enforcement

A documented rule is an obligation, not proof that a tool enforces it. Identify existing enforcement and its limits. Current examples include dependency-boundary checks, schema publication checks, registered test scopes and independent-install probes. Hosted CI, automatic handoff reconciliation and dependency-pin consistency enforcement must not be described as implemented merely because the workflow calls for them.

If a process fails in practice, retain the failure, determine whether the cause is unclear guidance, missing enforcement or noncompliance, then fix that specific boundary. Measure improvement through less rework, faster reliable resumption and fewer incorrect claims; additional document count is not a success metric.
