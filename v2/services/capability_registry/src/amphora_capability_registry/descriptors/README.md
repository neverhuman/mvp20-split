# Release Descriptor Identity

`ReleaseIdentity` separates semantic capability/release/contract key from the exact image digest. `SchemaIdentity` and `PortSchemas` retain typed input/output/checkpoint pins. `ReleaseDocument` owns normalized immutable metadata bytes, their digest, lock projection/verification and immutable-registration comparison. DTOs only validate/serialize public boundaries.

Canonical profile `amphora-tool-release-v1` hashes sorted compact ASCII-escaped UTF-8 JSON containing `{profile, descriptor}` after strict ReleaseDescriptor normalization, with all defaults explicit, no trailing newline and no nonfinite numbers. Array order is retained. This profile differs from source bytes, schema publication and command encoding; its digest pins all declared metadata, not merely the image or port hashes. Cross-language producers must pass the published canonical fixture before claiming compatibility.

`verify_lock` compares the entire projected LockEntry, including capability/release/image/contract, descriptor hash and every port/checkpoint schema. `require_identical_registration` first checks semantic identity, then both digest and actual canonical bytes; a digest-only comparison cannot replace stored content. The future registry transaction owns persistence/concurrency and scope authorization; this pure boundary neither registers a release nor grants runtime/scientific authority.

Wire fixtures live in `contracts/fixtures/v1/tool_releases.json`; owner tests live in `tests/descriptors/`. Semantic validation and selection policy are described below; registration/deployment storage and routing remain .02. No URLs, credentials, replica addresses or health observations belong in immutable campaign LockEntry. Replacements preserve the profile and full comparison semantics, or explicitly version their public consumers.

## Semantic Validation and Selection

`DescriptorValidator` reports bounded consistency findings for duplicate declarations, empty purpose/output/applicability/examples, invalid units and contradictory checkpoint writer/read compatibility. It performs no I/O and does not infer scientific suitability from schema shape.

`CapabilityNeed` owns exact port/schema/representation/unit requirements. `ResourceAllowance` owns finite host architecture/OS/per-invocation limits. `PermissionPolicy` permits only pure effects in the current profile and compares declared egress with an explicit host allowlist. `EvaluationPolicy` hashes its scope, resource and permission values plus a named rule/scientific profile; stale/different policies are distinguishable. Declared egress concerns additional scientific/provider destinations; authenticated runtime/artifact control-plane endpoints remain separately configured adapter dependencies, never caller-selected descriptor URLs. These checks describe eligibility, not actual network sandbox enforcement or runtime grants.

`SyntheticScientificPolicy` only labels declared synthetic-test use eligible. Real contexts remain ineligible and evidence-proposal methods unreviewed; a healthy process cannot change this. There is no implicit scientific review, evidence adoption or human approval loop.

`CapacityObservation` binds scope and exact descriptor hash, explicit aware timestamps and a maximum 300-second lifetime. Missing, future, expired, mismatched or inconsistent observations remain unknown; no healthy replica or no free slots is unavailable. Capacity is a supplied owner observation at this stage; .02 must produce it from authenticated deployment inventory. It is not inferred by probing arbitrary caller URLs.

`SelectionEvaluation` groups the four assessments and observed time window, projecting to the additive EligibilityDecision root. Candidate requires valid structure, eligible synthetic use, permitted/compatible policy and currently available capacity. The three B1 observations remain unchanged; admission is separate so permission/resource denial cannot masquerade as a scientific or health judgment. This result cannot register, dispatch, renew an attempt or authorize an external effect. Every live execution still uses runtime authority.

Tests measure the whole owner source, with identity, structure, independent scientific/capacity outcomes, policy digest, incompatible ports/resources/egress and bounded freshness cases. Remaining uncovered constructor/diagnostic combinations and an independent golden failure corpus are the current B3 verification gate; there is no durable registry state to recover in .01.
