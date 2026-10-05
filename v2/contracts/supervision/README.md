# Supervisor public contracts

Version0.2.0. Runtime owns decision authority; Planning owns context/provider attempts and accounting. This independent package composes existing public Core, Graph Runtime and Planning records without a reverse dependency from Graph Runtime to Planning. No provider SDK, persistence, domain algorithm, credential or endpoint belongs here.

SupervisionSnapshot transports original cut, bounded concrete targets, selected node views/state/output hashes and separate footprint/read-set digests. SupervisionRequest groups Runtime decision/checkpoint/policy identity, that snapshot, original Planning request/digest, absolute Unix-millisecond deadline and bounded lineage. DTO validation does not verify hashes, stored membership, current scope/grants, admitted policy or budgets. Runtime supervision_requests owns projection and cross-record binding; the accepting owner must rederive current state.

Planning decision_scope remains its reviewed declaration digest. It is not either Runtime snapshot digest. Request identity is the scoped Planning engagement; provider attempt ordinal remains separate. Initial lineage has ordinal1 with null parent/root; successors have both digests and ordinal2..16. Cross-record consistency and actual ancestry are separate domain/storage checks. No model may supply accepted execution state through these records.

Tests live under tests/. Strict scalar/tuple/extra-field boundaries, negative wire fixtures and schema preservation are required. Existing profiles remain unchanged. The request slice remains unchanged; B1.02b adds separate responses, cancellation, decision readbacks and recording receipts plus explicit numeric-v2 command parsers. 42 public wire cases cover136 statements/6 branches100%;129 combined Runtime cases and78 boundary/legacy command cases pass. HTTP hosting remains B1.04. Independent combined public-boundary acceptance is B1.02c.


B1.02a verification:62 scoped request/wire/Runtime-scope/publication cases pass;520 schema files include10 additive files for five supervisor roots and preserve all510 predecessor files. Hash pins and literal original Planning0.69 request bytes live under tests/fixtures. DTO shape alone intentionally accepts a syntactically valid but false digest; Runtime binding tests prove rejection against the original owned footprint/request.


SupervisionResponse carries an immutable response_id, original decision/request binding, TaskProviderObservation and optional capture Artifact. CancelSupervision carries a distinct cancellation_id and original request binding. Neither can carry an accepted decision. SupervisionCommandReceipt distinguishes pending/rejected/recorded; exact commit references remain separate from SupervisionDecision readbacks. New readbacks describe pending or reasoned terminal dispositions and typed effective-input/retained-proposal/continue effects; DTOs do not implement these transitions.

parse_supervision_command recognizes only planning.supervision.request, runtime.supervision.respond and runtime.supervision.cancel with explicit amphora-command-v2 and existing bounded command encoding. It checks family/payload scope and request delivery actor; handlers must authenticate and enforce all owner policy. Old Runtime/DraftCommandReceipt types and parsers remain unchanged. Runtime supervision_responses owns actual cross-record/capture/receipt validation.


B1.02b publishes four additional roots/eight files:528 schema files preserve all520 predecessors. New command parsers explicitly require numericv2 even though the shared encoder preserves legacy fallback. Three literal command byte/hash vectors and four unchanged Planning0.69 observation vectors bind compatibility. Independent combined package acceptance remains B1.02c.
