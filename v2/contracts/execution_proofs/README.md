# Accepted execution proof transport

- Owner: BP-08.03/B2.03b.ii; version0.1.0, verified 2026-10-06 14:40:30; 32 scoped checks, production module line/branch coverage100%.
- Design: [Representation and fitness](../../docs/Architecture/Campaigns/Representation_Fitness.md#producer-backed-synthetic-reuse).

AcceptedToolExecution groups an original prepared invocation, canonical accepted completion and worker identity. It exposes reviewed tool binding, original Artifact inputs, exact accepted output and attempt/fence provenance. The authority label is accepted_execution: historical evidence only, never a lease, permission to execute/reuse, source access or scientific verdict.

Core/Runtime public DTOs are the only dependencies. Runtime owns authorization, joins and cross-record consistency; consumers must read this from the authenticated owner and independently check expected pins/current Artifact access. Shape validation alone cannot authenticate a caller-supplied proof. Existing Runtime contracts remain unchanged. Wire tests own shape/parity; Runtime execution_proofs tests own database/API authority and identity binding.
