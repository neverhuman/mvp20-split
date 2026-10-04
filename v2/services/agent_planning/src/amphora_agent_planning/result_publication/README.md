# Planning result publication

- Status: payloads and durable storage verified; BP-07.02/B2.03b.ii.b SDK workflow verified; concrete input preparation/diagnostic production and actual Data integration remain b.ii.c.
- Package: Planning0.26 workflow verified; public Planning0.7 unchanged. Applied planning0010 adds result selection/preparation/events/control. Never run <=0.24 migrators afterward; prior0001..0009 unchanged.
- Design: [owner handoff](../../../../../docs/Build%20Plans/BP-07/BP-07.02%20Owner%20handoff%20and%20accepted%20replay.md).

## Responsibility and authority

This module prepares exact diagnostic-feedback and candidate-answer Artifact values and owns their separate SQL selection/preparation/event history. It owns their deterministic result slot and content/configuration binding. Trace publication stays in publication; extraction/repair owns observations and diagnostics, research_proposals owns answer validation, Data owns bytes/rights and Research/Knowledge own acceptance. Payload and identity values have no I/O. The store/journal use only Planning-owned SQL; workflow now coordinates the public Data SDK through the shared upload driver; no model call or concrete automatic diagnostic producer is implemented here.

ResultArtifact.feedback revalidates RepairFeedback against the exact task/observation/prior trace and finalized interpretation. Its body is unchanged diagnostic_only feedback, using the separately pinned publication-compatible feedback schema. ResultArtifact.answer reconstructs PublishedCandidate, reruns ResearchProposalValidator against the exact selected QuestionContext and selects one surviving local answer. Missing, duplicate or withheld answers cannot be invented. AnswerRecord retains proposal_only and quotation_and_structure_only, exact question/method/context, model attribution, grounding, task/candidate hashes and interpretation reference. It does not prove scientific truth, sufficiency or a registered question.

## Payload and ancestry invariants

Both paths reconstruct the trace from observed history, verify the finalized upload/derivation receipt through existing command checks and recheck TraceArtifact against reviewed source facts. Inputs contain all interpretation inputs plus the interpretation Artifact itself. Artifact IDs are deduplicated only when exact references agree, remain scope-bound, sort deterministically, and fail rather than truncate above128. Result bodies are capped256KiB. The transformation fingerprint binds result kind and exact task/trace/body hashes. Underlying source bodies are not copied beyond the defined attributed answer/diagnostic content.

candidate-answer-v1.schema.json is a packaged, LF-pinned closed content profile without external references or root $id, identified by planning.candidate-answer-content/v1 and its exact byte digest. It is distinct from public endpoint DTO schema exports. A deployed Data owner must explicitly configure this trusted profile; callers cannot install schemas by sending a reference.

## Stable result identity

ResultIdentity.bind requires read_attempts and record_attempts for the exact scope. Feedback has the single diagnostics slot per actor/trace; answers use their validated local ID. The stable publication_id hashes the actor/trace/kind/local slot. Content and publisher configuration are bound separately into immutable identity bytes and command hashes, so changing them retains the same slot and conflicts in the journal. The stable ID alone is not permission to dispatch a new command.

Read-only restore checks exact actor/scope, canonical encoding, content/profile and local slot without requiring a write grant. Existing pure PublicationAttempt upload transitions and receipt checks accept this compatible identity interface; the result format separates command identities from trace publication. Trace-specific event formats and historical command bytes are unchanged. Journal reconstruction must rebuild these values from owned facts before external effects; directly constructing a dataclass is not trusted proof.

## Remaining implementation and replacement gates

Pure preparation does not prove the history came from owned storage, source processing permission remains current, or a remote Artifact exists. b.ii.a storage, lease/fence and preparation reconstruction are verified. b.ii.b bounded SDK upload/recovery is verified. b.ii.c still supplies the concrete current-rights input preparation/diagnostic producer and actual Data integration. b.iii adds durable owner submissions and receipt binding. c proves combined actual-owner behavior. The configured repair producer remains unimplemented until b.ii.

Tests are owned by tests/result_publication. They cover exact feedback preservation, attributed answer/schema, complete ancestry, slot/config/content conflict, permission and scope, noncanonical stored identities, unavailable answers, forged receipts/observations and unchanged upload transition semantics. Scripted finalized receipts are value-level proof only. dev/verify_planning.py checks schema packaging and reruns the isolated owner/contract and existing process-replacement suite.


## Verified b.ii.a storage

selection/history load original actor-owned task/observation/trace and exact finalized interpretation before result registration. store/journal own result-specific selection, preparation and event history with separate DB-clock control. prepared stores bounded historical review/question witnesses alongside exact payload/manifest and verifies their digests, original owned facts and complete ancestry during read-only replay. events uses a distinct planning-result-publication-event.v1 encoding with the existing pure upload transition semantics. This storage passes54 focused tests531 statements36 branches100%,684 installed cases and32 process/replay stages across two installations; the SDK result workflow is verified, and the concrete diagnostic producer/actual Data integration remain absent. b.ii is66.67% (storage/workflow complete; concrete producer/actual Data pending).

Storage checkpoint evidence: [Result_Storage.json](../../../../../docs/Audits/Evidence/BP-07-Extraction/Result_Storage.json). Four result-specific stages use scripted receipts; actual Data publication remains b.ii.c.


## Verified b.ii.b SDK workflow

ResultPublisher validates client actor/scope, registers the exact owned selection before effects, and returns finalized/rejected history without preparation or peer calls. It acquires a120-second DB-clock lease, re-reads, and loads owned history in a short transaction. Its configured preparer receives that history plus selection outside SQL and returns ResultInputs (reviewed sources, optional selected questions/feedback), never arbitrary result body bytes or acceptance. Journal.prepare rebuilds and binds those values against exact owned facts before upload. The concrete production preparer/current processing reads are still b.ii.c; scripted preparation only proves coordination.

publication/driver.py now owns the unchanged bounded Data SDK upload loop used by both TracePublisher and ResultPublisher. It owns no SQL schema, source preparation or journal format. Each journal supplies its own fences and event records. Only the worker committing streaming intent sends PUT; recovered streaming uses a distinct successor, uncertain finalize reconciles the original command, and terminal rejection remains immutable. Eight lifetime uploads,64 events and10 drive transitions per call remain bounded. ResultPublisher ignores only expected result_lease_lost during release and exposes other persistence failures.

Tests/result_publication/test_workflow.py covers actual owner storage/SDK with scripted Data/preparation, including dropped replies, input failures, finalization uncertainty, terminal replay, unexpected release failure and no transactions spanning peer calls. Trace workflow tests protect the extracted loop's prior behavior. The installed result_workflow_probe uses three fresh processes and persisted scripted Data receipt state; it does not prove real Data or abrupt process death.

Verified 2026-10-04 11:19:18:39 focused cases243.14s; result workflow39 statements4 branches100%, shared driver/trace/result104 statements24 branches96.88%.705 isolated tests314.97s and35 process/replay stages across two installations. [Workflow evidence](../../../../../docs/Audits/Evidence/BP-07-Extraction/Result_Workflow.json). Shared driver transition ceiling/loop edge and one trace-wrapper defensive line remain uncovered; no actual Data result-integration claim.
