# Embedding and Retrieval Contracts

- Design status: profile/source bindings, index/query authority, optional APIs and installed HTTP/process recovery verified; independent closeout verified; scientific acceptance remains separately scoped
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-10-03 19:49:51` (America/Chicago)
- Parent: [Domain overview](Data_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#embedding-and-representation-layer)

## Owned Contract

Profiles pin modality/task, encoder revision, tokenizer, preprocessing, chunking, truncation, pooling, instructions, dimensions, numeric format, normalization and metric. Query/document roles and supported pairings are explicit. Vectors retain source revisions/spans or structured input and generation lineage.

Reuse through content/profile-addressed artifacts subject to rights and compatibility. Identical content retains distinct provenance and permissions. Equal dimensions do not imply compatibility. Text, molecular, sequence and graph spaces stay distinct unless a versioned evaluated alignment/pairing permits comparison. Cross-space fusion/reranking is explicit.

## Boundary and Flow

Embedding tools execute through Campaigns/Capabilities. Data owns profiles and index snapshots; Knowledge owns assertion meaning. Indexes derive from eligible corpus/profile snapshots with current access enforcement. Retain query/filter/ranking policies and selected revisions.

## Invariants and Verification

Vectors/indexes are derivatives, not authoritative knowledge. Scientific corrections create superseding bindings and replacement generations for later campaign selection; active campaign pins and historical records remain unchanged. Invalid encoding and current rights revocation are separate new-use gates. Build migrations separately, reconcile intervening changes and publish atomically. Retain rollback and provider reproducibility limits. Verify reusable artifacts, concurrent generation, profile rejection, retrieval quality and revocation even for historical snapshots.

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

Build a candidate index against a pinned corpus manifest. Verify exact content/profile compatibility and current rights, then atomically publish against the expected prior head. Record scientific quality and applicability separately; weak or unknown evidence does not by itself veto valid exploratory retrieval. Profile relevance evaluation governs later scientific use claims, not a requirement that one campaign be scientifically complete. Existing runs may retain the old snapshot for reproducibility, but current access revocation still applies. A retrieval response returns vector/source identities, ranking configuration, scores and exact index/profile versions. Unauthorized omissions expose no identities or counts; the initial bounded response has no omission-count field.

Use coarse eligibility filters before search where supported and authoritative authorization before exposing results or fetching content. Backend limitations cannot justify leaking unauthorized snippets, counts or identifiers. Multi-space fusion must not compare raw similarity scores as though calibrated equally.

## Failure and Boundary Example

A provider changes an embedding model behind an unchanged alias. New generation cannot be assumed compatible with the old index; quarantine or separate the profile until evaluated. Retained vectors can preserve historical retrieval where permitted, while exact re-encoding may be unavailable. Duplicate concurrent generation publishes one reusable artifact with attempt lineage.

## Design Basis and Open Decisions

The embedding section of Product Requirements is the authority. Remaining scientific/deployment decisions: encoder families, relevance fixtures, chunking strategy, migration thresholds and production backend deployment. The bounded software implementation uses an explicitly configured local Qdrant1.19.1 fixture and a synthetic byte-histogram encoder. No single vector space or similarity threshold is selected by this architecture.

User-provided reference (`2026-09-22 20:46:34`): JARVIS uses Qdrant and can supply an implementation reference when vector integration is planned. The subsequent BP-06.05 implementation selects pinned Qdrant for the local software proof; PostgreSQL retains authoritative publication/history. This is not a production deployment decision. No further external JARVIS access is required or implied.

Implementation boundary: [Data module](../../../services/data_artifacts/src/amphora_data_artifacts/representations/README.md) and [canonical plan](../../Build%20Plans/BP-06/Completed/BP-06.05%20Representation%20reuse%20and%20retrieval.md) distinguish verified synthetic reuse, source rights, actual index/retrieval and public HTTP/process recovery from pending scientific validation. The scoped B2.02 adapter target is an isolated local Qdrant fixture, not a deployed production index.
