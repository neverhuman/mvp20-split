# Accepted producer evidence

- Owner: BP-08.03/B2.03b.ii; Runtime0.64/runtime0028, verified 2026-10-06 14:40:30; 32 scoped checks, production module line/branch coverage100%.
- Design: [Representation and fitness](../../../../../docs/Architecture/Campaigns/Representation_Fitness.md#producer-backed-synthetic-reuse).

This focused Runtime module exposes the original prepared invocation, exact canonical successful completion and settled worker attempt as AcceptedToolExecution. It joins only Runtime-owned records in a read-only repeatable-read transaction. ProducerSnapshot enforces activation/invocation/attempt/fence and Artifact scope coherence. There is no new table, migration, state transition, lease, dispatch, source-byte read, cache permission or scientific judgment.

With existing inspection hosting configured, GET /v1/runs/{run}/completions/{completion}/producer requires both read and inspect_receipts in the authenticated tenant/project. Pending, noncanonical, failed or absent producers return404; scoped/grant denial uses existing403 behavior. Inconsistent producer data fails closed503. Successful responses disable caches. Original command bodies, random claim command IDs and lease timestamps/credentials are not needed by consumers.

Consumers must authenticate this owner response and independently verify their expected capability/schema/input/output identities and current Data access. The DTO alone does not prove its origin. A later worker revocation or unrelated run progress does not rewrite accepted historical evidence. Research's current reuse policy remains separately responsible for whether that evidence is eligible for a new action.

Tests/execution_proofs owns actual PostgreSQL joins, public API authorization, historical persistence and pure inconsistent-record negatives. Test scripted Artifact reservations are a separate tier from actual worker/Data/Research acceptance. Replacement must preserve the public schema and immutable provenance rather than rediscover a mutable latest invocation.
