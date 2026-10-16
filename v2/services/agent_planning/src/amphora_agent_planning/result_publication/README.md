# Planning result publication

- Status: payloads and durable storage verified; BP-07.02/B2.03b.ii.b SDK workflow verified; concrete input preparation/diagnostic production and actual Data integration verified under b.ii.c; sibling owner_handoff supplies verified owner reconciliation.
- Package: Planning0.27 preparation/producer verified; public Planning0.7 unchanged. Applied planning0010 adds result selection/preparation/events/control. The current retained database also includes planning0011: never run Planning<=0.28 migrators. Earlier migration bytes are unchanged.
- Design: [owner handoff](../../../../../docs/Build%20Plans/BP-07/Completed/BP-07.02%20Owner%20handoff%20and%20accepted%20replay.md).

## Responsibility and authority

This module prepares exact diagnostic-feedback and candidate-answer Artifact values and owns their separate SQL selection/preparation/event history. It owns their deterministic result slot and content/configuration binding. Trace publication stays in publication; extraction/repair owns observations and diagnostics, research_proposals owns answer validation, Data owns bytes/rights and Research/Knowledge own acceptance. Payload and identity values have no I/O. The store/journal use only Planning-owned SQL; workflow now coordinates the public Data SDK through the shared upload driver; the concrete diagnostic producer supplies repair inputs without making model calls.

ResultArtifact.feedback revalidates RepairFeedback against the exact task/observation/prior trace and finalized interpretation. Its body is unchanged diagnostic_only feedback, using the separately pinned publication-compatible feedback schema. ResultArtifact.answer reconstructs PublishedCandidate, reruns ResearchProposalValidator against the exact selected QuestionContext and selects one surviving local answer. Missing, duplicate or withheld answers cannot be invented. AnswerRecord retains proposal_only and quotation_and_structure_only, exact question/method/context, model attribution, grounding, task/candidate hashes and interpretation reference. It does not prove scientific truth, sufficiency or a registered question.

## Payload and ancestry invariants

Both paths reconstruct the trace from observed history, verify the finalized upload/derivation receipt through existing command checks and recheck TraceArtifact against reviewed source facts. Inputs contain all interpretation inputs plus the interpretation Artifact itself. Artifact IDs are deduplicated only when exact references agree, remain scope-bound, sort deterministically, and fail rather than truncate above128. Result bodies are capped256KiB. The transformation fingerprint binds result kind and exact task/trace/body hashes. Underlying source bodies are not copied beyond the defined attributed answer/diagnostic content.

candidate-answer-v1.schema.json is a packaged, LF-pinned closed content profile without external references or root $id, identified by planning.candidate-answer-content/v1 and its exact byte digest. It is distinct from public endpoint DTO schema exports. A deployed Data owner must explicitly configure this trusted profile; callers cannot install schemas by sending a reference.

## Stable result identity

ResultIdentity.bind requires read_attempts and record_attempts for the exact scope. Feedback has the single diagnostics slot per actor/trace; answers use their validated local ID. The stable publication_id hashes the actor/trace/kind/local slot. Content and publisher configuration are bound separately into immutable identity bytes and command hashes, so changing them retains the same slot and conflicts in the journal. The stable ID alone is not permission to dispatch a new command.

Read-only restore checks exact actor/scope, canonical encoding, content/profile and local slot without requiring a write grant. Existing pure PublicationAttempt upload transitions and receipt checks accept this compatible identity interface; the result format separates command identities from trace publication. Trace-specific event formats and historical command bytes are unchanged. Journal reconstruction must rebuild these values from owned facts before external effects; directly constructing a dataclass is not trusted proof.

## Remaining implementation and replacement gates

Pure preparation does not prove the history came from owned storage, source processing permission remains current, or a remote Artifact exists. b.ii.a storage, lease/fence and preparation reconstruction are verified. b.ii.b bounded SDK upload/recovery is verified. b.ii.c current-rights preparation, diagnostic producer and actual Data integration are verified. b.iii adds durable owner submissions and receipt binding. c proves combined actual-owner behavior. The concrete repair producer is implemented and verified under b.ii.c.

Tests are owned by tests/result_publication. They cover exact feedback preservation, attributed answer/schema, complete ancestry, slot/config/content conflict, permission and scope, noncanonical stored identities, unavailable answers, forged receipts/observations and unchanged upload transition semantics. Scripted finalized receipts are value-level proof only. dev/verify_planning.py checks schema packaging and reruns the isolated owner/contract and existing process-replacement suite.


## Verified b.ii.a storage

selection/history load original actor-owned task/observation/trace and exact finalized interpretation before result registration. store/journal own result-specific selection, preparation and event history with separate DB-clock control. prepared stores bounded historical review/question witnesses alongside exact payload/manifest and verifies their digests, original owned facts and complete ancestry during read-only replay. events uses a distinct planning-result-publication-event.v1 encoding with the existing pure upload transition semantics. This storage passes54 focused tests531 statements36 branches100%,684 installed cases and32 process/replay stages across two installations; the SDK result workflow is verified, and the concrete diagnostic producer/actual Data integration are also verified. b.ii is100%.

Storage checkpoint evidence: [Result_Storage.json](../../../../../docs/Audits/Evidence/BP-07-Extraction/Result_Storage.json). Four result-specific stages use scripted receipts; actual Data publication has separate b.ii.c evidence below.


## Verified b.ii.b SDK workflow

ResultPublisher validates client actor/scope, registers the exact owned selection before effects, and returns finalized/rejected history without preparation or peer calls. It acquires a120-second DB-clock lease, re-reads, and loads owned history in a short transaction. Its configured preparer receives that history plus selection outside SQL and returns ResultInputs (reviewed sources, optional selected questions/feedback), never arbitrary result body bytes or acceptance. Journal.prepare rebuilds and binds those values against exact owned facts before upload. ResultPreparer supplies the concrete current-processing boundary; the earlier scripted preparation tests prove coordination only.

publication/driver.py now owns the unchanged bounded Data SDK upload loop used by both TracePublisher and ResultPublisher. It owns no SQL schema, source preparation or journal format. Each journal supplies its own fences and event records. Only the worker committing streaming intent sends PUT; recovered streaming uses a distinct successor, uncertain finalize reconciles the original command, and terminal rejection remains immutable. Eight lifetime uploads,64 events and10 drive transitions per call remain bounded. ResultPublisher ignores only expected result_lease_lost during release and exposes other persistence failures.

Tests/result_publication/test_workflow.py covers actual owner storage/SDK with scripted Data/preparation, including dropped replies, input failures, finalization uncertainty, terminal replay, unexpected release failure and no transactions spanning peer calls. Trace workflow tests protect the extracted loop's prior behavior. The installed result_workflow_probe uses three fresh processes and persisted scripted Data receipt state; it does not prove real Data or abrupt process death.

Verified 2026-10-04 11:19:18:39 focused cases243.14s; result workflow39 statements4 branches100%, shared driver/trace/result104 statements24 branches96.88%.705 isolated tests314.97s and35 process/replay stages across two installations. [Workflow evidence](../../../../../docs/Audits/Evidence/BP-07-Extraction/Result_Workflow.json). Shared driver transition ceiling/loop edge and one trace-wrapper defensive line remain uncovered; no actual Data result-integration claim.

## Verified b.ii.c preparation and diagnostic producer

ResultPreparer performs current source and interpretation processing outside SQL under one shared20-second budget, verifies exact interpretation bytes, and reads only the selected Research questions and pinned Knowledge context needed for diagnostics. Answer preparation has no graph dependency. ResultJournal remains the authority for owned origins and first immutable prepared payload; historical recovery does not rerun this preparer.

DiagnosticPolicy reconstructs the exact observed trace and uses the existing graph/Research validators. It requests repair for structural withheld items or unavailable structured output, retaining prior bytes and useful items. Model-reported uncertainty, weak science and unavailable selected owner records alone do not justify more model calls. Missing Knowledge transport/context can coexist with independent Research diagnostics; inconsistent owner facts still fail binding. Terminal abstention/policy rejection yields NoRepairNeeded. Feedback limits remain256 findings/paths and256KiB; no silent truncation.

DiagnosticProducer is a principal-bound configured RepairChain producer. It treats the supplied step as a trace selector, reloads owned history, publishes a stable interpretation and result slot, and returns exact RepairInputs. NoRepairNeeded returns None; publication rejection/uncertainty preserves existing state and surfaces RepairInputUnavailable. It does not execute providers or override family budgets. No-repair is a local outcome, not a persisted scientific acceptance decision. Owner reconciliation outcomes belong to sibling owner_handoff; they do not create a fresh repair budget.

Verified24 focused cases14.73s cover110 statements24 branches98.51%; preparation/producer100%, one terminal DiagnosticPolicy guard is outside this instrumentation.720 isolated tests317.56s/35 process stages plus9 subsequent installed guard cases5.71s. Actual Data proof spans7 Planning workers/2 hosts: denial/regrant, lost committed PUT reply, distinct successor upload after owner restart, terminal no-read replay under withdrawal, bounded repair production and proposal-only answer publication. Provider and graph profile are synthetic; combined actual Research/Knowledge remains c. [Producer evidence](../../../../../docs/Audits/Evidence/BP-07-Extraction/Result_Producer.json).
Planning0.82 exposes ResultIdentity.scope as the original trace scope for the shared pure upload state machine; identity/command bytes remain unchanged. The stale-fence test now starts its deliberate one-second expiry after payload preparation, preserving the expiry oracle under instrumentation. Production lease checks are unchanged.
