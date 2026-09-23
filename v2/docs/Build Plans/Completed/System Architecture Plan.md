# System Architecture Plan

## Canonical Execution Tracker

- Status: complete
- Last refreshed: `2026-09-22 20:30:31` (America/Chicago)
- Owner: system-design workstream
- Scope: proposed deployable system, graph execution model, durable-state design and complete research-loop protocol; documentation only
- Parent: bounded successor to completed architecture-detail work; [Master Build Tracker](../Master%20Build%20Tracker.md)
- Overall completion: 100% (three equally weighted design-delivery phases complete)
- Current task: Phase 3 / S3 — review execution/failure scenarios and reconcile architecture
- Next task: none in this closed scope; implementation planning and technical acceptance remain separate
- Blockers: none; user confirmed single server with separate workers and remote scientific tools
- Active exception: none
- Acceptance: architecture proposal only; no runtime implementation or production-readiness claim
- Pre-activation audit: `2026-09-22 20:24:54`; ready; preserves prior plans as closed, addresses missing system-level decisions rather than repeating service descriptions

| Phase | Completion | Prerequisite | Deliverable | Exit evidence |
|---|---:|---|---|---|
| 1 / complete | 100% | User feedback and existing contracts | Identify concrete system questions and inherited assumptions | Process topology, graph execution semantics, authoritative state and feedback transaction boundaries identified |
| 2 / complete | 100% | Phase 1 | System overview and five focused construction documents | Process topology, typed graph machine, transactional records, commands/source boundaries and complete loop specified |
| 3 / complete | 100% | Phase 2 | Scenario review and scoped drift audit | Paper failure/feedback scenarios and hierarchy/link checks passed; no runtime tests claimed |

## Scope Guard

The eight existing domains describe functional responsibility. This plan must supply system construction: process placement, synchronous/asynchronous interfaces, graph compiler/interpreter semantics, transaction boundaries, storage/projections and failure recovery. Label proposed choices; distinguish technology facts from unmeasured capacity claims. Do not activate runtime builds or import historical stack decisions implicitly.

## Closeout

[Closeout audit](../../Audits/System_Architecture_Closeout.md) records the concrete decisions, paper scenarios, validation and limits. User-selected deployment is single server with separate workers and remote scientific tools. Remaining construction choices are proposals; no implementation readiness is claimed.
