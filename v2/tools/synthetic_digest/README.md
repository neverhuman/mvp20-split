# Synthetic digest evaluator

- Owner: BP-08.03/B2.03b.ii; version0.1.0; verified 2026-10-06 14:45:50; 54 scoped checks. Tool kernel/adapter/capability/profile coverage100%; CLI tested in subprocess, not counted in parent coverage.
- Architecture: [Representation and fitness](../../docs/Architecture/Campaigns/Representation_Fitness.md#synthetic-evaluation-oracle).

This independent pure tool accepts evaluation-identity.input and emits synthetic-evaluation.receipt. Its sole score is the unsigned integer encoded by the first six hex digits of a declared canonical SHA256 (0..16777215). It enforces its exact bound image/release, method/applicability/uncertainty profiles, purpose, single objective, scopes and declared required context. It does not authenticate canonicalization, read source Artifacts, resolve material/eligibility, authorize reuse, fit a model or claim any scientific measurement. Context may affect reuse even when it cannot affect this deliberately synthetic number.

DigestEvaluation owns parsing, bounded input and score mapping; boundary DTOs carry records. Inputs are <=262144 bytes, strict UTF8 JSON without duplicate keys/nonfinite constants. Descriptor binds once per adapter; rebinding another image fails. SDK0.2 owns public Runtime/Data calls and completion acceptance. No private owner imports, state, network beyond SDK worker, migration or hidden iteration. Failures map to a safe invalid_synthetic_digest_input reason; no source contents are logged. Descriptor egress is deny and authority is synthetic_only.

CLI: compute --image-sha256 DIGEST (stdin/stdout JSON), describe --image-sha256 DIGEST, schema --direction input|output, profiles, worker --config PATH. Worker is one invocation. Environment credentials belong in the external worker configuration, never this package. Public metadata supports Registry discovery; an image recipe is not evidence of a built/qualified image.

Tests/kernel owns independent golden vectors, pin/context rejection, exact input provenance and malformed-byte handling; tests/capability owns descriptor/schema/CLI/adapter behavior. Replacement must preserve deterministic output, exact published schemas and pins; actual Runtime/Data/Research reuse and independent Linux image qualification remain later acceptance gates. No LLM calls or paid provider dependencies.

Image qualification 2026-10-06 15:29:16: [Representation images](../../docs/Audits/Evidence/BP-08-Search/Representation_Images.json) records actualLinuxamd64 digest,offlineCLI golden/schema/nonroot/peer-isolation checks. This does not claim target-host or scientific qualification; actual Registry/image-matched replacement remains V1.02.
