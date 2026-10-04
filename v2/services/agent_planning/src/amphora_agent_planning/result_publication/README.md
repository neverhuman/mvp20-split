# Planning result publication

- Status: BP-07.02/B2.03b.i verified 2026-10-04 10:22:31;24 focused cases134 statements/6 branches100%,654 installed tests and28 process/replay stages across two installs.
- Package: Planning0.24; public Planning0.7 and planning0001..0009 unchanged.
- Design: [owner handoff](../../../../../docs/Build%20Plans/BP-07/BP-07.02%20Owner%20handoff%20and%20accepted%20replay.md).

## Responsibility and authority

This module prepares exact diagnostic-feedback and candidate-answer Artifact values. It owns their deterministic result slot and content/configuration binding. Trace publication stays in publication; extraction/repair owns observations and diagnostics, research_proposals owns answer validation, Data owns bytes/rights and Research/Knowledge own acceptance. Current pure objects have no SQL, network, provider calls or durable publication effect.

ResultArtifact.feedback revalidates RepairFeedback against the exact task/observation/prior trace and finalized interpretation. Its body is unchanged diagnostic_only feedback, using the separately pinned publication-compatible feedback schema. ResultArtifact.answer reconstructs PublishedCandidate, reruns ResearchProposalValidator against the exact selected QuestionContext and selects one surviving local answer. Missing, duplicate or withheld answers cannot be invented. AnswerRecord retains proposal_only and quotation_and_structure_only, exact question/method/context, model attribution, grounding, task/candidate hashes and interpretation reference. It does not prove scientific truth, sufficiency or a registered question.

## Payload and ancestry invariants

Both paths reconstruct the trace from observed history, verify the finalized upload/derivation receipt through existing command checks and recheck TraceArtifact against reviewed source facts. Inputs contain all interpretation inputs plus the interpretation Artifact itself. Artifact IDs are deduplicated only when exact references agree, remain scope-bound, sort deterministically, and fail rather than truncate above128. Result bodies are capped256KiB. The transformation fingerprint binds result kind and exact task/trace/body hashes. Underlying source bodies are not copied beyond the defined attributed answer/diagnostic content.

candidate-answer-v1.schema.json is a packaged, LF-pinned closed content profile without external references or root $id, identified by planning.candidate-answer-content/v1 and its exact byte digest. It is distinct from public endpoint DTO schema exports. A deployed Data owner must explicitly configure this trusted profile; callers cannot install schemas by sending a reference.

## Stable result identity

ResultIdentity.bind requires read_attempts and record_attempts for the exact scope. Feedback has the single diagnostics slot per actor/trace; answers use their validated local ID. The stable publication_id hashes the actor/trace/kind/local slot. Content and publisher configuration are bound separately into immutable identity bytes and command hashes, so changing them retains the same slot and must conflict in the future journal. The stable ID alone is not permission to dispatch a new command.

Read-only restore checks exact actor/scope, canonical encoding, content/profile and local slot without requiring a write grant. Existing pure PublicationAttempt upload transitions and receipt checks accept this compatible identity interface; the result format separates command identities from trace publication. Trace-specific event formats and historical command bytes are unchanged. Journal reconstruction must rebuild these values from owned facts before external effects; directly constructing a dataclass is not trusted proof.

## Remaining implementation and replacement gates

Pure preparation does not prove the history came from owned storage, source processing permission remains current, or a remote Artifact exists. b.ii must supply owner-local intent/payload/event storage, leases/fences, fresh public rights reads and bounded upload/recovery before this becomes a production publisher. b.iii adds durable owner submissions and receipt binding. c proves combined actual-owner behavior. The configured repair producer remains unimplemented until b.ii.

Tests are owned by tests/result_publication. They cover exact feedback preservation, attributed answer/schema, complete ancestry, slot/config/content conflict, permission and scope, noncanonical stored identities, unavailable answers, forged receipts/observations and unchanged upload transition semantics. Scripted finalized receipts are value-level proof only. dev/verify_planning.py checks schema packaging and reruns the isolated owner/contract and existing process-replacement suite.
