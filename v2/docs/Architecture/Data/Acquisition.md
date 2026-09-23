# Sources and Artifact Acquisition

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Data_Architecture.md)
- Requirement source: [Product Requirements](../Product_Requirements.md#data-sources-and-campaign-acquisition)

## Owned Contract

Sources have versioned identities, supported formats/operations, access references, scope, rights, refresh and retention rules. Campaign bindings select source revisions, queries and expected representations. Reviewed tools acquire/prepare documents, tables, molecular structures, sequences, images, instrument traces and external feeds.

Artifacts retain hashes, source/query receipts, connector/transform versions, quality and lineage. Evidence bundles pin member revisions. Retain payloads where permitted; provider or licensing limits must expose replay loss. Hashes alone cannot reconstruct content.

## Boundary and Flow

Campaigns schedules acquisition/recovery; Capabilities owns connectors; Platform supplies credentials/storage. Data owns artifact identity, not scientific acceptance. Research owns lab matching/interpretation; Knowledge owns claims. Provider/user text is untrusted data, not runtime instructions.

## Invariants and Verification

Import success never promotes evidence. Handle empty, partial, stale, incompatible, denied and unavailable inputs explicitly. Verify representation/units, duplicates, exact queries, access and deletion impact. Refresh is a new acquisition; historical replay must not silently call a changing provider.

## Component and Object Design

| Proposed component | Owned records and behavior |
|---|---|
| Source registry | Source identity/revision, operations, formats and scope associations |
| Binding resolver | Campaign-specific source/query selection and policy defaults |
| Acquisition ledger | Logical acquisitions, attempts, cursors/windows and provider receipts |
| Preparation chain | Typed parse/normalize/join/quality transformations with artifact lineage |
| Artifact catalog | Content identity, immutable metadata revisions and access/retention references |

Domain/product/project associations improve discovery but grant no access. Source bindings resolve defaults explicitly and become part of the run's input snapshot. Secrets are external references. Store the provider's version/cursor and the exact query/selection used, not merely the endpoint URL.

## Acquisition Transaction

Resolve authorized source/binding -> record acquisition attempt -> obtain payload -> validate/retain raw artifact -> run declared transformations -> commit artifact references and quality disposition. Large objects may upload before metadata commit; only committed references are visible as usable results. Orphan provisional uploads need an explicit retention/cleanup policy.

An artifact's scientific review is separate from content-addressed deduplication. The same bytes can arrive through different source rights and contexts; retain each provenance binding. Refresh produces a new source/result revision even when the provider returns identical content.

## Failure and Boundary Example

A paginated API changes between pages. If no stable snapshot/token exists, record the acquisition consistency limitation and do not label the merged dataset reproducible. Partial results carry completeness metadata. Connector retries obey source limits and total campaign budget; denied access is not resolved by a broader credential silently.

## Design Basis and Open Decisions

[Data Sources and Acquisition](../Data_Sources_and_Acquisition.md) defines source/binding/artifact contracts. Remaining decisions: selected connectors, snapshot guarantees, artifact storage implementation and cleanup schedules. Each adapter's validation and rights constraints must be independent of its transport success.
