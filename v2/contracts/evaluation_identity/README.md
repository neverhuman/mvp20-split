# Declared evaluation identity contracts

- Owner: BP-08.03/B2.01b; version0.1.0, verified 2026-10-06 13:46:49.
- Design: [Representation and fitness](../../docs/Architecture/Campaigns/Representation_Fitness.md#declared-evaluation-identity).

This package transports grouped representation, evaluator/method, objective, synthesis/applicability and material/context pins. EvaluationIdentity explicitly carries identity_only authority. It is neither a cached value nor a permission, producer receipt, canonicalization proof, eligibility decision or scientific verdict. Existing research, search, candidate and embedding schemas remain unchanged.

Required nullable material state remains explicit. Finite bounds and closed/extra-forbidden schemas provide transport validation; Research domain objects own matching scope, complete required context, unique axes/names, profile coherence and canonical identity. A caller-supplied policy/reference is not reviewed merely because it validates. No implementation or storage is imported; dependencies are public Core/Tools/Research contracts and Pydantic.

The key excludes only original representation Artifact identity after retaining its provenance separately. Intended identity includes scope, canonical representation claim, semantic/equivalence policies and every evaluation/context pin. Context name order may normalize; ordered objective axes must not. Consumers must resolve original source/provenance and current access, plus Research eligibility, before reuse. Module tests own shape/parity; Research fitness tests own actual identity semantics. Schema import coverage is not policy coverage.

Verification: 60 scoped checks passed in55.56s including public schema compatibility and service/test ownership. Combined DTO/domain coverage118statements/20branches100%; pure identity only. No SQL or public reuse route was exercised or added.
