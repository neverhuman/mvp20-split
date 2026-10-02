# Knowledge reasoning publication

- Status: B1 request/result/input values and additive wire contracts implemented; store, HTTP and orchestration pending.
- Owner: Knowledge; [implementation design](../../../../../docs/Build%20Plans/BP-06/BP-06.03%20Publication%20and%20receipt%20design.md).
- Architecture: [Knowledge](../../../../../docs/Architecture/Knowledge/Knowledge_Architecture.md).

`PublicationRequestDocument` authenticates the publish_reasoning grant, pins the original actor and exact graph/reasoning request, and rejects pending/failed/mismatched reasoning results. The new public request only selects a stored result; it cannot supply result bytes, inputs, purpose or receipt outcomes. Public status distinguishes pending, failed (including possible prior external effects) and published; publication may contain an abstained logical receipt and is never itself scientific acceptance.

`ReasoningArtifact` converts the exact owner result and a fresh owner-issued ReferenceValidation into bounded immutable canonical bytes, ContentDescriptor and DerivationDeclaration. It requires exact context/subject/source-raw references, unique same-scope inputs and deterministic input ordering. Complete expanded trace/context coverage is established by the owner reviewer, not inferred from a caller's list. The future workflow must obtain that review itself, including for historical pre0.9 results. Content is bounded16 MiB and input count128. The method digest binds the signed-ground-Horn algorithm profile and exact rule-set reference; Data verifies identity/rights, not the claimed algorithm's scientific validity.

Contracts0.6.0 provide a self-contained reasoning-result payload schema profile for Data's trusted configuration. Its identifier/digest is distinct from the existing schema-export URN envelope; the actual result shape and all prior public schema bytes remain unchanged. The profile contains no URI/base override or external reference. Deployment must explicitly install the pinned schema; a publication request cannot install a validator.

No database tables, upload calls, owner receipt policy or HTTP publication routes exist yet in this module. Applied Knowledge migrations0001..0003 remain immutable. The next layer owns a forward migration, durable attempts/leases, receipt-first recovery and bounded uncertain streams under the linked design. Runtime owns retention and execution acceptance; Research owns scientific sufficiency. No peer implementation imports or SQL are permitted.

Tests belong to `tests/publication`; run `dev/run_tests.py --module knowledge --area publication --coverage`. Pure value/contract tests do not establish durable publication, failure recovery or independent replacement. Module replacement must preserve exact scoped bindings, canonical payload/profile hashes, input completeness and explicit uncertainty.

Verification checkpoint:11 pure owner tests and75 contracts plus14 dev tests pass. Payload module coverage56/60 statements and13/16 branches; unexercised paths are SQL key projection, failed/mismatched stored decisions and the16 MiB size guard. Durable state/failure and installed-owner acceptance remain required before claiming publication.
