# Knowledge Wire Contracts

Version0.7.0 adds CorrectReasoningReceipt and SelectReasoningReceipt for reference-only source correction and explicit selection. Shared ReceiptCorrectionView returns the exact reference plus record. Existing publication and reasoning schemas remain unchanged; owner policy and persistence are outside DTOs.

- Package: amphora-contracts-knowledge0.7.2; BP-06.02/B1 contract boundary implemented.
- Design: [Knowledge authoring](../../docs/Architecture/Knowledge/Authoring.md); [activation decisions](../../docs/Audits/BP-06.02_Activation.md).

Public imports describe scoped graph/entity/assertion identities, a pinned predicate vocabulary, source grounding, exact Research question/need links, discriminated typed edits, proposals, structural acceptance decisions and immutable snapshots. Dependencies are public Core0.1.0, Evidence0.5.7 and Research0.8.0 plus Pydantic. No service implementation, database, I/O, agent or scientific policy belongs here.

The six edits are add_entity, add_assertion, correct_assertion, retract_assertion, merge_entities and revise_entity_context. Corrections name an exact prior assertion revision and a replacement; context edits name an exact prior entity revision. Merge records retain both identities. Shape validity alone does not verify a predecessor, endpoint, alias cycle, ontology membership, scope equality, payload existence or source meaning. The Knowledge owner must enforce those checks and authenticate every operation.

GraphChangeProposal carries the observed complete head (null for genesis), requested pinned vocabulary/policy, explanatory text, source grounding and bounded edits. AcceptedGraphChange is a separate owner-issued record with actor, observed public references, acceptance time, log position and resulting snapshot. Its authority is exactly structural_only. Reported claims, hypotheses and unresolved statements remain distinct; scientifically accepted posture is deliberately unavailable in this initial profile. Research declarations and answer-proposal references do not grant acceptance or artifact access.

GraphChangeDecision separates accepted heads from rejected/conflicting findings through a discriminator. Receipt hashes, matching scope/IDs, graph-head consistency and acceptance authority require owner verification; callers cannot turn a valid DTO into a committed receipt. New wire surfaces do not change existing runtime command profiles or canonical command bytes.

DomainGraphContent carries complete immutable entity/assertion history plus aliases and retractions. The owner canonicalizes ordered semantic collections and hashes content, excluding incidental build timestamps. Snapshot references hold that digest; accepted-change references hash accepted content separately, avoiding self-referential hashes. A head binds both snapshot and accepted log position. These are format rules to be verified by the Knowledge owner, not behavior implemented by the DTO package.

Collections, strings and integer revisions are bounded; models are strict/frozen and forbid extra fields and nonfinite numbers. Cross-record rules belong to focused owner domain objects. Module-local tests own public shape and JSON Schema parity, with synthetic examples under tests/fixtures. Generated published schemas and predecessor-byte preservation are checked by dev tooling. Independent contract installation proves serialization only; service evidence separately verifies transactional replay, peer validation and replacement.

Version0.5.0 adds ReasoningRuleSet, ReasoningRequest, ReasoningResult and ReasoningStatus. Configured profiles bind ground signed rules and bounded budgets to exact graph/context; a request carries only a pinned rule-set reference, snapshot, context, subject, purpose and bounded targets. Results carry original assertion references and derivation steps, with explicit complete/incomplete and supported/contradicted/unknown states. Authority is always synthetic_logical_entailment. Status binds actor/request to null pending, evaluated with a server-issued reference observation, or terminal failed. Shape validation never establishes profile hashes, peer rights, scientific authority, durable acceptance or Runtime delivery.

62 owned contract tests pass.272 published schemas preserve all264 predecessor bytes, including authoring, profile discovery and rebuild roots. Public Research dependencies remain one-way; downstream Research assessment will pin the immutable Knowledge artifact instead of importing this DTO package back. [Boundary evidence](../../docs/Audits/Evidence/BP-06-Knowledge/Reasoning_Boundary.json) records the current compatibility proof.

BP-06.03/B1 contracts0.6.0 add ReasoningPublicationRequest/Status and a self-contained reasoning-result payload schema profile. Requests select stored results without caller-provided observations/receipt authority. Publication can carry an abstained DomainReceipt; published does not imply accepted science. Data derivation metadata and generic Runtime receipts are reused through public contract dependencies, with no peer implementation or dependency cycle. Four new schema files preserve all282 predecessor schema bytes.75 contract tests pass; owner state/policy/HTTP remain in Knowledge.

BP-06.03/B1.06 compatibility patch: dependency pins now consume additive Research contracts0.3.0 (Evidence0.5.1/Knowledge contracts0.6.1 where applicable). Existing public schema bytes and owner behavior are unchanged; earlier installed/recovery evidence remains tied to its recorded versions.

BP-06.03/B1.07 compatibility patch: exact pins now consume Research contracts0.4.0 and corresponding Evidence0.5.2/Knowledge contracts0.6.2. The only added wire root is Research synthetic evidence; peer behavior and all294 predecessor schema bytes remain unchanged.

B1.10 compatibility patch updates exact Research0.5.0 contract dependency closure; no owner behavior, migration or existing schema changes.

Compatibility0.7.1 updates exact Evidence/Research pins only; all published Knowledge schemas remain unchanged.

Compatibility0.7.2 updates exact Research/Evidence dependencies only; Knowledge schemas remain unchanged.
