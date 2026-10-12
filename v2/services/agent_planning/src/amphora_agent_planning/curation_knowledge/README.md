# Curation Knowledge context reads

UI-01.08/P2.3b.2. Architecture: ../../../../../docs/Architecture/Agents/Planning.md.
CurationKnowledgeReader reads up to8 exact heads from original byte-owned intent.
It uses only public Knowledge profile/snapshot/accepted-change reads through the
existing authenticated bounded transport. No private peer imports, SQL, provider
calls, graph writes, newest-head lookup or processing-grant claims.

Each head has at most3 calls/15seconds/18087936bytes; one30second deadline covers
the collection, including each head verification. Packet assembly performs its own bounded replay validation. Original head/change/snapshot digests and
profile bindings must match. Whole heads with at most256 entity revisions and256
assertion revisions are selected in retained order. Larger or oversized graphs
become explicit gaps; no first-N slice masquerades as a complete graph. Aliases,
retractions and weak science remain original data, not a reason to reject context.

KnowledgeContext retains exactly one result for each original selected head,
including denial/unavailable/invalid/expired/too-large gaps. Successful heads use
existing selected-graph projections; a required curation_knowledge summary records
all original heads, policy, status and technical read accounting. Required graph
slices may still exceed the model input cap and fail preparation explicitly.
No transport failure is fabricated into an empty successful graph.

Replacement tests: tests/curation_knowledge. Existing profile/digest/record rules
remain in graph_context; public transport limits remain in knowledge_access.
Retained-summary validation cross-checks original intent, exact head coverage and
matching available projections; recomputed payload hashes cannot omit a selection.
Actual owner deployment and worker/preparation linkage remain later P2.3 gates.
