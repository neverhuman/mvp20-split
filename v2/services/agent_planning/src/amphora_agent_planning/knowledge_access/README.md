# Planning public Knowledge reads

- Status: BP-07.02/B2.01c verified within synthetic read-only acceptance scope.
- Owner: Agent Planning. Knowledge alone owns graph state and acceptance.
- Scope: exact pinned profile/snapshot/change reads and bounded prompt preparation; no graph writes, SQL, implicit rebase or automatic retries.

KnowledgeTransport requires an explicit authenticated127.0.0.1 HTTP endpoint. Its closed POST routes are graph-profiles/read, graph-snapshots/read and graph-changes/read. One KnowledgeReadWindow bounds the whole review to15 seconds,3 calls and the sum of256KiB profile,16MiB snapshot and1MiB accepted-change limits. A timer closes a socket whose headers/body keep trickling past the wall-clock deadline. Malformed JSON, duplicate keys, nonfinite values, foreign DTO shapes, redirects, non-JSON replies and overflow cannot supply authority. Errors contain stable reason codes rather than peer bodies or credentials.

KnowledgeReader rebinds the extraction task, reads the exact public profile and historical snapshot/accepted change, checks accepted content digest and its resulting head, then constructs immutable KnowledgeContext. Every selected entity/assertion revision must exist in the pinned snapshot. Candidate validation separately decides whether a selected revision is stale for an edit. There is no mutable-head lookup or automatic pin change; Knowledge's eventual proposal CAS remains final authority. Genesis profile discovery reserves nothing.

All network calls run outside Planning SQL. No rights lease, graph acceptance, live model reliability or scientific validity follows from these reads. Tests belong under tests/knowledge_access; scripted loopback cases must remain distinct from actual installed owner proof.

## Grounded graph packet

GraphPrompt.render takes the already reviewed source/prompt bundle and exact KnowledgeContext. It preserves the predecessor source-only PromptTemplate.render bytes, adding a separately identified planning-grounded-extraction-input.v1 packet. The packet contains the exact digest-checked draft/operation schemas, canonical vocabulary/profile, selected entity/assertion records, required endpoint/alias dependencies, selected retraction markers and a context fingerprint. It does not silently include the entire graph or change selected identities. Owner labels, assertion text and source text remain JSON data separate from pinned instructions.

Graph data is capped at1MiB and the full packet at8MiB, with explicit errors instead of truncation. This is graph-aware prompt preparation, not a complete live provider request: applicability/objective/model-policy Artifacts remain explicit references unless already part of source data. Actual context-body assembly, tokenizer/window fit and provider egress belong to the later live adapter integration and evaluation gates. No model is called here.

Replacement must preserve all exact pins, schema fingerprints, body/header deadlines, no-retry behavior, controlled error codes and separation of observations from acceptance. No migration or durable state is introduced. The installed-owner probe seeds synthetic accepted records only inside a separately installed Knowledge process; Planning workers use public HTTP only. It proves historical origin/read compatibility across a new head and owner restart, not real source rights or acceptance of Planning-generated proposals.

Verified 2026-10-04 06:45:26:513 regression plus2 additional prompt cases;32 focused cases at176 statements28 branches96%;497 independent tests20 process stages. Actual proof8 isolated Planning workers/2 Knowledge hosts/2 owner-local fixture processes, with retained PostgreSQL and Data/Research offline. Defensive transport expiry/closed-socket and alternate empty-body/alias branches remain uncovered.

Verified 2026-10-04 07:31:11:70 focused cases,212 shared/read statements28 branches98%;560 regression and542 independent tests. Actual public read proofs passed with8 isolated Planning workers and2 owner hosts per owner. Remaining coverage gaps are defensive socket cleanup and alternate empty-read paths. No migration or scientific acceptance claim.
