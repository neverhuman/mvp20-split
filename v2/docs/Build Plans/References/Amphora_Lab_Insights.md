# Amphora Lab Reference Insights

- Last reviewed: `2026-09-25 13:50:38` (America/Chicago).
- Status: design inputs incorporated into queued plans; no code extraction or runtime validation.
- Source: `Z:\Amphora_ALB\amphora_lab-main`, reviewed read-only at the user's request.
- Relationship: complements the [existing evolutionary reuse baseline](../../Architecture/Evolutionary_Code_Reuse_Baseline.md); does not replace it or change runtime architecture.

## Disposition and Owning Plans

| Insight | Useful contribution and limit | Implementation/acceptance owner |
|---|---|---|
| Processing-sensitive material identity | Processing events, morphology and polymer distributions make existing context-sensitive identity requirements concrete; schemas alone do not validate chemistry | [BP-06.04](../BP-06/BP-06.04%20Laboratory%20returns%20and%20candidate%20eligibility.md), [BP-08.03](../BP-08/BP-08.03%20Representation%20and%20fitness%20boundaries.md) |
| Question -> claim -> method/context -> answer | JSONL records seed research-question/evidence-gap examples; answer text and validation level are not scientific ground truth | [BP-06.01](../BP-06/Completed/BP-06.01%20Source%20and%20evidence%20contracts.md), [BP-06.02](../BP-06/Completed/BP-06.02%20Typed%20graph%20authoring%20and%20replay.md), [BP-06.03](../BP-06/Completed/BP-06.03%20Reasoning%20and%20domain%20receipts.md), [BP-07.03](../BP-07/BP-07.03%20Campaign%20proposals%20and%20context.md) |
| Conversion/interpretation trace | Original input, transform chain, missing fields and inference hints become immutable scoped trace artifacts; separate from database schema migration | BP-06.01 and [BP-07.02](../BP-07/BP-07.02%20Reliable%20text%20decomposition.md) |
| Named scientific graph views | Lineage, material/property history and experiment/model views seed bounded public projections; queries need scope/revision/pagination controls | [BP-05.02](../BP-05/Completed/BP-05.02%20Graph%20inspection%20and%20navigation.md), [BP-06.06](../BP-06/BP-06.06%20Feedback%20integration%20and%20closeout.md) |
| Polymer-specific vocabulary | Sequence rules, tacticity, branching/end groups and distribution fields inform optional adapters; unknowns must not silently inherit defaults | BP-08.03; biological/numeric contracts stay independent |
| Extraction provenance and readiness | Select schemas/fixtures only after exact-source/dependency/license review; no new executable optimizer established | [BP-08.01](../BP-08/BP-08.01%20Reuse%20and%20search%20contracts.md) |

These are refinements to existing queued B1/B2/B3 deliveries, not a parallel implementation plan. V1 acceptance in each touched child includes the added required cases. All touched children remain 0%; existing delivery denominators stay unchanged. BP-02.03/A2 remains the implementation return point.

## Authority and Dependency Boundaries

Research owns question/criteria/evidence-need and tested material/sample meaning. Knowledge owns accepted assertions, contradictions and replay. Data owns raw artifacts and ingestion traces; Agent Planning owns extraction attempts and proposals. Public trace references link these histories without a shared mutable aggregate or cross-owner database writes.

BP-06.01 introduces the question and conversion contracts; .02 retains their links through graph replay; .03 evaluates evidence sufficiency; .04 binds actual sample/material state; .06 proves the integrated path and actual Studio views. BP-05.02 may use labeled knowledge/lab fixtures until .06, while shipping only views backed by available services. BP-07 consumes the resulting contracts for grounded extraction and gap-driven proposals. BP-08 consumes material-state/equivalence context for representation and fitness isolation.

The reference's top-level Lab object, direct mutable graph ingestion, generic confidence values and placeholder methods are not adoption candidates for execution authority. Existing CQRS/repository/configuration concepts largely duplicate our current design. No Neo4j deployment or graph-store selection follows from the Cypher examples.

## Observed Limits

Static review found 26 empty non-`__init__` Python files among 219 source Python files, including optimizer/validation/benchmark placeholders. Pipeline dispatch and RAG answers include placeholders; material validation returns an empty result and compliance can return unconditional success. Imports targeting missing modules were also observed. Historical readiness/test claims in that repository were not independently reproduced. QAV files are small structural examples, not a reviewed evaluation corpus.

Before any extraction, recheck source identity, relevant license attribution, actual behavior, dependency isolation and independent tests. Preserve synthetic fixture labeling; do not promote example answers, inferred defaults or stub success into scientific evidence. No source was copied into an implementation package during this incorporation.

## Source Pins

Absolute links locate the reviewed external checkout; it is not vendored or required to run v2. Hashes pin reviewed bytes for future comparison. Do not interpret matching bytes as behavioral validation.

| Source | SHA-256 |
|---|---|
| [Processing history](Z:/Amphora_ALB/amphora_lab-main/src/amphora_labs/domain/models/polymers/structure/processing_history.py) | `f91ed3737d38b3d57deaebe5730bdf5586e9a3d5a1504ba48a1b0d00fa2d462a` |
| [Polymer chain](Z:/Amphora_ALB/amphora_lab-main/src/amphora_labs/domain/models/polymers/materials/polymer_chain.py) | `b217102fca56b27f7af7a84bfa4b34a847d3bb1be387f0e31628d913310c3385` |
| [Question/answer examples](Z:/Amphora_ALB/amphora_lab-main/qavs/moses.0.1.0.jsonl) | `0f1c6d1143633d6b113e8f45b0ab1ef4dc1d917cd94fe8abe2cda7f5f51076f8` |
| [Conversion trace](Z:/Amphora_ALB/amphora_lab-main/src/amphora_labs/domain/models/trace/migration.py) | `54c0f5c2ae1809ea17a22786300d32c84e6ae6c83473d46e448acabe63f0af31` |
| [Experiment view](Z:/Amphora_ALB/amphora_lab-main/src/amphora_labs/views/templates/experiment_analysis.cypher) | `6868b59f37cce81660535111c2d0c4081f47c87a54fa5a54f6e89f9ee391c10a` |
| [Lineage view](Z:/Amphora_ALB/amphora_lab-main/src/amphora_labs/views/templates/lineage.cypher) | `9bae436a5500c55aa5f6d9ec3d67c30ee095dfda6e38dda1f4f40217eeb474f7` |
