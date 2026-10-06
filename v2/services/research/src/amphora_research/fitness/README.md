# Research fitness and reuse boundary

- Owner: BP-08.03/B2.01b; Research0.36.0, pure identity verified 2026-10-06 13:46:49.
- Design: [Representation and fitness](../../../../../docs/Architecture/Campaigns/Representation_Fitness.md).

EvaluationKey owns declared evaluation identity. It reconstructs grouped public DTOs, requires coherent source/context/material scopes and exact representation policy, verifies the permitted source encoding schema, unique ordered objectives with nonblank units, exact required named context and explicitly required material state. Conflicting references under one Artifact id reject. It has no I/O, source resolution, table, cache lookup or tool imports.

The key's canonical sorted compact UTF-8 JSON includes the full representation claim excluding its source Artifact, the complete evaluation policy and exact material/named context. Required context names and context entries normalize by name; objective order does not. Canonical representation, scope, kind, semantic/equivalence policy, purpose, evaluator release/image, method/applicability/synthesis/uncertainty policy and objective units/directions all remain significant. Original representation source is retained separately in output, never overwritten by an equivalent encoding.

`same_declared_identity` compares exact normalized bytes. `to_wire` emits identity_only plus component and aggregate SHA-256 fingerprints. It does not authenticate the canonicalization claim or reviewed configuration and does not authorize scientific reuse. Real producer/owner proof, current Data rights, eligibility and complete fitness assembly remain B2.02/.03. Missing required metadata rejects; optional absence is permitted only when the explicit policy allows it.

Tests/fitness/reuse owns independent equivalence/non-equivalence, required context and provenance cases. Pure success is not public service or persistence evidence. Replacement must preserve the versioned canonical profile and complete identity inputs, or explicitly version them. Existing interpretation/eligibility/synthesis modules retain their scientific policy authority.

Verification: 60 scoped checks passed in55.56s including public schema compatibility and service/test ownership. Combined DTO/domain coverage118statements/20branches100%; pure identity only. No SQL or public reuse route was exercised or added.
