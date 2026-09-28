# Embedding and Retrieval Contracts

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Data_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#embedding-and-representation-layer)

## Owned Contract

Profiles pin modality/task, encoder revision, tokenizer, preprocessing, chunking, truncation, pooling, instructions, dimensions, numeric format, normalization and metric. Query/document roles and supported pairings are explicit. Vectors retain source revisions/spans or structured input and generation lineage.

Reuse through content/profile-addressed artifacts subject to rights and compatibility. Identical content retains distinct provenance and permissions. Equal dimensions do not imply compatibility. Text, molecular, sequence and graph spaces stay distinct unless a versioned evaluated alignment/pairing permits comparison. Cross-space fusion/reranking is explicit.

## Boundary and Flow

Embedding tools execute through Campaigns/Capabilities. Data owns profiles and index snapshots; Knowledge owns assertion meaning. Indexes derive from eligible corpus/profile snapshots with current access enforcement. Retain query/filter/ranking policies and selected revisions.

## Invariants and Verification

Vectors/indexes are derivatives, not authoritative knowledge. Corrections invalidate dependent representations. Build migrations separately, reconcile intervening changes and publish atomically. Retain rollback and provider reproducibility limits. Verify reusable artifacts, concurrent generation, profile rejection, retrieval quality and revocation even for historical snapshots.

## Component and Object Design

| Proposed component | Owned records and behavior |
|---|---|
| Representation-profile registry | Immutable encoder/preprocessing/task compatibility contracts |
| Encoding coordinator | Batch jobs, result-affecting cache keys and generation receipts |
| Vector artifact catalog | Source/profile lineage, vectors and authorized reuse bindings |
| Index generation manager | Corpus/profile snapshot manifests, build checkpoints and publication |
| Retrieval broker | Eligible query/index pairing, filtering, fusion/reranking and consumption receipt |

Profile identity includes task-role instructions and preprocessing, not just model name/dimensions. A vector key is derived from the exact encoded representation, profile and any declared context. Graph embeddings include projection revision; sequence embeddings include normalization/modification choices. Artifact reuse does not merge source permissions.

## Index Publication and Retrieval

Build a candidate index against a pinned corpus manifest. Evaluate quality, verify profile compatibility, reconcile source/rights updates and atomically switch the published index reference. Existing runs may retain the old snapshot for reproducibility, but current access revocation still applies. A retrieval response returns vector/source identities, ranking configuration, scores, omissions and exact index/profile versions.

Use coarse eligibility filters before search where supported and authoritative authorization before exposing results or fetching content. Backend limitations cannot justify leaking unauthorized snippets, counts or identifiers. Multi-space fusion must not compare raw similarity scores as though calibrated equally.

## Failure and Boundary Example

A provider changes an embedding model behind an unchanged alias. New generation cannot be assumed compatible with the old index; quarantine or separate the profile until evaluated. Retained vectors can preserve historical retrieval where permitted, while exact re-encoding may be unavailable. Duplicate concurrent generation publishes one reusable artifact with attempt lineage.

## Design Basis and Open Decisions

The embedding section of Product Requirements is the authority. Remaining decisions: encoder families, index backend, quality fixtures, chunking strategy and migration thresholds. No single vector space or similarity threshold is selected by this architecture.

User-provided reference (`2026-09-22 20:46:34`): JARVIS uses Qdrant and can supply an implementation reference when vector integration is planned. Qdrant is a candidate derived retrieval backend, not a selected dependency or replacement for authoritative PostgreSQL state. Review that integration when scoped and authorized; preserve the profile, rights, publication and replay contracts above.
