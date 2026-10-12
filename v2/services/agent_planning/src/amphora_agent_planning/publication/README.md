# Planning trace publication boundary

- Status: trace publication and actual Data replacement/recovery are verified under BP-07.02/B1. Planning0.26 shared-driver extraction passed39 focused cases and705 isolated tests/35 process stages.
- Owner: Planning trace publication and provenance; Data owns Artifact bytes, current processing authorization and derived-upload acceptance. Knowledge/Research own scientific acceptance.
- State: planning_0007 trace-publication history; later result publication uses separate planning_0010 tables. The current database now includes planning0011; never run Planning<=0.28 migrators.
- Evidence: [actual trace publication](../../../../../docs/Audits/Evidence/BP-07-Extraction/Actual_Publication.json). Detailed historical checkpoint counts belong to the owning BP-07 plan/history.

## Responsibilities and exclusions

PublicationIdentity binds original actor, exact owned trace, publication ID and trusted publisher configuration ID. PublicationJournal loads the exact stored task/trace and persists immutable prepared trace bytes, reviewed provenance and bounded upload events. TracePublisher coordinates fresh source review and public Data SDK effects. PublicationTransport supplies bounded local HTTP. This module does not accept scientific claims, run models, repin campaigns or own generic result payloads; result_publication owns feedback/answer preparation and its separate journal.

PublishedCandidate is the shared pure binding of observed typed output, byte-reviewed sources and finalized interpretation payload/receipt. It rechecks receipt, task/observation and attribution before exposing candidate parsing/grounding. It acquires no Knowledge or Research facts: graph ProposalInputs adds KnowledgeContext; Research validation adds QuestionContext. Hand-constructed values are not proof of stored origin or peer contact.

## Trace payload and ancestry

TraceArtifact.reviewed binds exact trace/task/request/actor/context, source bundle and pinned prompt bytes. It verifies all declared source/conversion traces and includes every consumed objective, prompt, policy, model configuration, selected context, source raw Artifact and conversion output. Inputs are unique exact references in stable Artifact-ID order, same scope, capped128; missing, foreign, conflicting or unreviewed inputs fail. Canonical trace body is at most1MiB and retains interpretation_only/profile_only metadata for successful and failed attempts.

extraction-trace-v1.schema.json is the trusted packaged content profile, pinned by exact LF byte hash as planning.extraction-trace-content/v1. It differs from public exported schema URN identity. Callers cannot install validators. The transformation descriptor binds interpretation profile and exact task/trace/observation hashes. Historical reconstruction uses stored metadata; it never grants continuing processing rights. New preparation reviews source bytes, and Data rechecks current ancestry permission at new begin/finalize.

## Immutable state and replacement

planning_0007 stores SELECT/INSERT-only intents, payloads and events. Separate control columns own holder, fence, expiry and position with scoped update grants. PublicationStore uses stable scoped locks and DB-clock leases1..300s; TracePublisher requests120s. No peer/provider I/O occurs under SQL. Prepare reconstructs exact owned facts and binds review metadata before committing payload plus initial event. Every transition checks lease/fence/expected position, including the final position write so late expiry rolls back event/payload effects.

Read requires read_attempts and the original actor. It takes a short owner lock for consistent multi-query reconstruction, rebuilds payload from original trace/task and canonical Artifact/source/conversion metadata, then replays at most64 contiguous digest-checked events. Source bytes are not duplicated in publication storage. Changed ID/content/publisher/schema bindings conflict; old bytes and timestamps remain unchanged. New execution requires record_attempts plus read_attempts and matching client actor/scope.

## SDK coordination and shared driver

TracePublisher registers intent, returns terminal finalized/rejected history without fresh input or peer calls, acquires/re-reads under its lease, reviews sources outside SQL if no payload exists, then drives upload. driver.py contains the bounded upload loop shared with ResultPublisher; it owns no preparation rules, schema, journal table or persisted event format. TracePublisher._drive delegates to it. The extraction changes no trace identities, body/event/command bytes or limits.

Begin/finalize use receipt-first SDK recovery with original command IDs and canonical bytes. Only the invocation committing streaming intent may perform its one PUT. Recovered streaming intent is uncertain even if the process stopped before sending; retain abandonment and choose a distinct next upload. Uncertain finalize or derivation lookup stays finalizing and reconciles the original command; no abandonment/re-streaming is allowed there. A verified Data rejection becomes immutable history. An unavailable/denied receipt lookup never fabricates rejection or success.

One invocation drives at most10 transitions; lifetime upload attempts are capped8 and events64. A failed PUT exits that invocation rather than immediately exhausting all successors. Receipt checks bind upload/content/declaration, stream upload identity and final Artifact/derivation to exact original command identity/hash. Guard checks precede effects, but remote effects may outlive a lease; this is bounded reconciliation, not network exactly-once. Release ignores only expected publication_lease_lost; other persistence failures remain visible.

## Transport and processing policy

PublicationTransport permits only the closed GET receipt/derivation, POST derived-begin/finalize and PUT content routes. Initial deployment permits explicit127.0.0.1 HTTP with port, without redirects/proxies/implicit retries. Each exchange has a5s wall-clock deadline covering headers/body/writes,1MiB outbound and256KiB reply bounds. Success requires JSON media and strict duplicate/nonfinite rejection. SDK receipt recovery has at most3 rounds; errors expose safe codes.

Current process-rights denial gates new effects. HTTP403 alone cannot establish whether Data committed a rejection; only exact receipt observation resolves that. An observed terminal rejection remains rejected after regrant. A separately identified future publication may proceed after reauthorization. Previously finalized history stays byte-exact without new source processing.

## Owned verification and limits

Tests/publication separates pure values/records, actual PostgreSQL journal/fence tests, bounded transport and SDK workflow tests with scripted Data. Both publication and result_publication workflow tests protect the shared driver. Trace acceptance already exercised actual installed Data source/conversion provenance, matched content/ancestry, rights denial/regrant, Data restart and abrupt os._exit73 after preparation/stream intent/streamed/remote-finalize boundaries. Only uncertain streaming chooses a successor; remote-finalize recovery returns the original Artifact. Test leases expire naturally; production default remains120s.

This proves synthetic software ownership/recovery, not provider quality, machine power loss or Knowledge acceptance. dev/verify_planning_publication.py records the earlier actual-owner proof, but its old version pins must be updated before reuse; do not run incompatible retained migrators. Result publication's actual Data integration is a distinct later gate and cannot inherit this trace-only evidence.

PublishedHistory in origin.py owns the same-owner exact task/trace/observation/prior/finalized-interpretation loader shared by result and owner-handoff histories. Each wrapper restores its own selection and supplies its error-code prefix. This refactoring changes no trace/result bytes or source processing behavior; historical loads do not contact peers.

Planning0.82: the pure upload transition machine uses identity.scope; existing trace/result identity getters return their unchanged original trace scope. Canonical identity, command bytes, hashes and transition rules are unchanged. Capture publication can use this machine without inventing an extraction trace.

UI-01.08/P2.3c.1: PublicationTransport keeps application/json-only media by default;
a closed DeclarationTransport subclass adds text/plain for reviewed configuration.
Closed routes, wall-clock/byte bounds and strict JSON responses are unchanged.
Pure upload transitions/driver are reused by curation_declaration without relabeling
its payload as a trace or model capture. New journal/identity/event profile is separate.
