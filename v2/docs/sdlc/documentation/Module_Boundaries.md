# Module contracts and replacement

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.


## Purpose and handoff

| Element | Meaning |
|---|---|
| Why it exists | Allow safe use and independent replacement without relying on implementation knowledge. |
| Inputs | Owned behavior, consumers, public contracts, state and failure semantics. |
| Output | A source-adjacent replacement contract using the linked module template. |
| Completion test | Another implementer can identify required behavior, prohibited coupling and acceptance/cutover obligations. |

## Replacement boundary

Module replacement is an expected development pattern. The source-adjacent module README is the current implementation-boundary contract for a fresh rebuild, with canonical schemas and acceptance fixtures linked rather than duplicated. Before replacement, confirm that public behavior, consumers, state ownership, failure semantics and compatibility/cutover expectations are captured using the module template. Reimplement internals freely within that boundary; intentional boundary changes require versioned contracts, consumer impact and migration evidence. Do not discard authoritative data or restart from incompatible checkpoints merely because code is being replaced. Initial-profile cutovers occur between campaigns. Closed plans stay closed: use a bounded successor plan for substantive replacement and its scoped drift audit for closeout.

## Required module coverage

Each meaningful code module needs a nearby README defining responsibilities, non-responsibilities, interfaces, reads/writes, dependencies, state/runtime/privacy/scientific boundaries, verification and audit hooks. Update it when those boundaries change.

Use the [module README template](../templates/Module%20README%20Template.md). Small helpers may share a focused parent contract. Documentation folder indexes are navigation, not replacement contracts.
