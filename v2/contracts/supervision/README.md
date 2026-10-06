# Supervisor public contracts

Package0.4 adds AdmitSupervisedGraph and explicit numeric-v2 graph.admit_supervised parser. The command pins an exact policy digest; original graph admission parsers remain closed. No admission execution is granted by this DTO.

Version0.3 adds explicit CheckpointRequest/Snapshot (schema_version2), InvokeCheckpoint and MaterializationCheckpoint. planning.supervision.request.v2 has its own parse_checkpoint_command; the original parser remains closed. Wire shape declares fields; Runtime alone verifies retained plan, scalar eligibility and acceptance.536 published schemas preserve528 predecessor bytes. tests/test_checkpoints.py pins exact request/command fixtures; journal frames remain private Runtime fixtures.


Version0.2.0. Runtime owns decision authority; Planning owns context/provider attempts and accounting. This independent package composes existing public Core, Graph Runtime and Planning records without a reverse dependency from Graph Runtime to Planning. No provider SDK, persistence, domain algorithm, credential or endpoint belongs here.

SupervisionSnapshot transports original cut, bounded concrete targets, selected node views/state/output hashes and separate footprint/read-set digests. SupervisionRequest groups Runtime decision/checkpoint/policy identity, that snapshot, original Planning request/digest, absolute Unix-millisecond deadline and bounded lineage. DTO validation does not verify hashes, stored membership, current scope/grants, admitted policy or budgets. Runtime supervision_requests owns projection and cross-record binding; the accepting owner must rederive current state.

Planning decision_scope remains its reviewed declaration digest. It is not either Runtime snapshot digest. Request identity is the scoped Planning engagement; provider attempt ordinal remains separate. Initial lineage has ordinal1 with null parent/root; successors have both digests and ordinal2..16. Cross-record consistency and actual ancestry are separate domain/storage checks. No model may supply accepted execution state through these records.

Tests live under tests/. Strict scalar/tuple/extra-field boundaries, negative wire fixtures and schema preservation are required. Existing profiles remain unchanged. The request slice remains unchanged; B1.02b adds separate responses, cancellation, decision readbacks and recording receipts plus explicit numeric-v2 command parsers. 42 public wire cases cover136 statements/6 branches100%;129 combined Runtime cases and78 boundary/legacy command cases pass. HTTP hosting remains B1.04. Independent combined public-boundary acceptance passed B1.02c:265 initial/105 replacement cases.


B1.02a verification:62 scoped request/wire/Runtime-scope/publication cases pass;520 schema files include10 additive files for five supervisor roots and preserve all510 predecessor files. Hash pins and literal original Planning0.69 request bytes live under tests/fixtures. DTO shape alone intentionally accepts a syntactically valid but false digest; Runtime binding tests prove rejection against the original owned footprint/request.


SupervisionResponse carries an immutable response_id, original decision/request binding, TaskProviderObservation and optional capture Artifact. CancelSupervision carries a distinct cancellation_id and original request binding. Neither can carry an accepted decision. SupervisionCommandReceipt distinguishes pending/rejected/recorded; exact commit references remain separate from SupervisionDecision readbacks. New readbacks describe pending or reasoned terminal dispositions and typed effective-input/retained-proposal/continue effects; DTOs do not implement these transitions.

parse_supervision_command recognizes only planning.supervision.request, runtime.supervision.respond and runtime.supervision.cancel with explicit amphora-command-v2 and existing bounded command encoding. It checks family/payload scope and request delivery actor; handlers must authenticate and enforce all owner policy. Old Runtime/DraftCommandReceipt types and parsers remain unchanged. Runtime supervision_responses owns actual cross-record/capture/receipt validation.


B1.02b publishes four additional roots/eight files:528 schema files preserve all520 predecessors. New command parsers explicitly require numericv2 even though the shared encoder preserves legacy fallback. Three literal command byte/hash vectors and four unchanged Planning0.69 observation vectors bind compatibility. Independent combined package acceptance passed B1.02c; seven byte-sensitive fixture vectors remain exact under Git checkout filters with core.autocrlf=true, enforced by .gitattributes. No provider/SQL/decision effect is claimed.


Supervision0.5 adds checkpoint-decision/v1. Pending checkpoints, model-accepted outcomes, deterministic fallback and run cancellation are distinct records. Model effects require request/response digests; pre-request fallback does not fabricate them. Materialization fields use exact graph ScalarValue and selection identity. Existing decision/request/response records remain unchanged. Runtime owner construction and acceptance remain separate gates.

Version0.6 adds CheckpointContext, an explicitly versioned published context Artifact profile with concrete occurrence, exact scalar values/digests/permissions, recipe/policy/budget references and potential-call allowances. It is data, never a call grant or accepted result. Future proposals are retained_only. Runtime domain objects bind original state; Planning processing rights and prompt trust remain separate.544 schema files preserve all542 predecessors (context_predecessor_schema_pins.json).

Version0.7 adds separate checkpoint_context_content_schema_bytes()/checkpoint_context_content_schema() for Artifact validation with local JSON pointers and no $id. The exported checkpoint_context_schema() and all544 published schema bytes are unchanged. Consumers must pin the chosen profile; identical DTO semantics do not make schema digests interchangeable. Data validator behavior remains unchanged.

Version0.8 adds CheckpointExecutionReport with closed stop reasons, original Runtime/Planning identity, and up to16 attempt references/statuses/observation hashes. Zero-call stops carry no fake observation or usage. Owner projection and later durable issuance fences establish authority; this DTO does not authorize fallback or repair.546 schemas preserve544 predecessor files, pinned in execution_predecessor_schema_pins.json. Existing commands and receipts are unchanged.

Version0.9 adds separate CheckpointRepairContext/CheckpointRepairFeedback and an explicit local-reference content schema. Bounded diagnostic metadata names parent/report/disposition/response hashes and reasons; no raw capture or new authority. Original CheckpointContext remains closed and byte-identical.548 published schemas preserve546 predecessor files. Data deployments must admit the exact new content profile explicitly.
