# Executable evaluation batch binding

Owner: Planning, BP-07.05/B1.02a. Pure boundary between independent evaluation labels and the existing physical-call runner. [Design](../../../../../docs/Build%20Plans/BP-07/BP-07.05%20Physical%20design.md).

`EvaluationBatch.prepare` requires trusted record_requests scope and exact case-to-request/policy maps. Original canonical RequestSnapshot hashes must match corpus input identities. Model/prompt, allowed Artifact set, accounting unit and request ceilings must match the frozen manifest. Context rights still require their owning service's authorization; a listed Artifact is not a processing grant.

Each repetition derives a stable engagement identity from protocol/scope/actor/case/ordinal and narrows the original request's max_attempts to1, preserving all other context. A failed measured response cannot trigger an unrecorded repair or retry. The complete batch's conservative token/accounting demands must fit the suite limits before any work; every demand also passes the existing reviewed BudgetPolicy. Batch identity pins all derived request and policy hashes. It does not include labels in provider inputs, reserve SQL budget, invoke a model or grant execution authority.

Domain objects group task identity, attempt binding and demand; no wide DTO constructor owns those rules. Source request/policy objects are revalidated and copied to immutable canonical bytes. Rebuild must preserve exact derived identities, no mutable caller references, all-case budget preflight and unchanged original request bytes. Durable registration is implemented here; evaluation_execution owns actual issuance/recovery and measured process evidence. Tests live under `tests/evaluation_batch`; pure fixtures do not establish real data rights or live evaluation.

## Durable suite registration

Planning0.91/planning0019 adds EvaluationJournal. Registration atomically retains exact original manifest/corpus/input/policy bytes under scoped suite identity, with advisory serialization and immutable SELECT/INSERT service privileges. It revalidates the entire batch and exact actor; same bytes replay, changed suite/batch conflicts. Reads require read_attempts and reconstruct with pure domain validation, never manufacturing a write grant. Missing scopes return None. Existing physical-attempt tables remain untouched by registration. No network or provider calls.

Original corpus bytes are retained by EvaluationProtocol because its manifest pins exact bytes. Batch preparation bounds retained request/policy/derived-request bytes to16MiB; original inputs also obey16MiB persisted bounds. Manifest1MiB/corpus4MiB bounds remain. Rebuild must preserve original registration bytes/timestamps and derived task identity. NEVER use Planning<=0.90 migrators against planning0019.

Verified `2026-10-06 03:43:09`:42 protocol/batch cases3.41s,12 boundary checks9.73s. Batch module137statements14branches100% measured. ActualSQL concurrent registration, immutable UPDATE/DELETE denial, exact restart/read replay, changed criteria, foreign scope/actor and no-attempt side effects covered. Physical runner and process-death evidence remain B1.02c/d.
