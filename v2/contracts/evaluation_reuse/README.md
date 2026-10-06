# Synthetic evaluation reuse transport

- Owner: BP-08.03/B2.03b.ii; version0.1.0; verified 2026-10-06 15:04:54;188scoped owner/wire/schema/regression checks;622schemas preserve608.

Reference-only ReuseRequest selects configured profile, source/target candidate and identity Artifacts, Runtime producer references and target eligibility/synthesis decisions. ReuseProjection retains all exact producer/representation/evaluation evidence, original source and target candidate, owner decisions, current consumed sources, scoped actor/id/digest and permitted/miss/ineligible result. A permitted result returns the original evaluation Artifact, never a new target observation. Authority is synthetic_reuse_decision.

These are DTOs only. Authenticated Research resolution, complete context policy and immutable persistence authorize a result; accepting caller-supplied projection JSON does not. All dependencies are versioned public contracts. Historical reads retain their original decision when source rights change; new qualifications recheck current rights. Compatibility tests freeze608 predecessor schema hashes; wire tests cover reference-only shape and narrow authority. No existing fitness schema changes.
