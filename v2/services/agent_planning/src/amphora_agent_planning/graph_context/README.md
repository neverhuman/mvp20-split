# Pinned graph records

Owner: Agent Planning; shared pure graph policy used by extraction and campaign context. Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md). No Knowledge implementation import, I/O, SQL, graph acceptance or scientific promotion.

GraphPins validates exact graph/head/vocabulary/policy identities. PinnedGraphContext validates and retains canonical profile/snapshot bytes: normalized vocabulary digest, scoped snapshot/head/content hash, structural policy and vocabulary binding. Limits remain256KiB profile and16MiB snapshot. GraphFacts indexes exact entity/assertion revisions, endpoint references, aliases and retractions; malformed identities and alias cycles fail. verify_change separately verifies accepted-change content digest and its resulting pinned head. Genesis profile discovery does not reserve a graph.

Historical records remain available through the index. The explicit entity/assertion edit checks reject stale, merged or retracted edit targets; campaign reading does not invoke those checks as a scientific quality filter. No latest-head lookup, implicit rebase, trust score or current rights lease is introduced.

The extraction KnowledgeContext adapter keeps its predecessor task fingerprint, operation-schema and genesis rules. Its public imports remain compatible. Three literal predecessor vectors under tests/graph_context pin exact extraction task, profile, snapshot and prompt bytes; proposals/knowledge_access/extraction tests retain their behavioral regression ownership. Campaign-specific selection and error outcomes live in campaign_knowledge_access. Replacement must preserve these byte identities and bounds or explicitly version the affected profile. This module has no durable state or migration.
