# Contract Packages

Independent Python packages expose public imports, versioned wire schemas and language-neutral fixtures. This directory is navigation, not a shared business-service module.

- [Core](core/README.md): immutable identity, scope, schema and artifact references.
- [Tools](tools/README.md): tool identity, ports, descriptor and invocation/completion protocol.
- [Campaigns](campaigns/README.md): separate validation-only wire-v1 and executable wire-v2 graph boundaries.
- `fixtures/v1/wire_cases.json`: shared positive/negative interchange fixtures.
- `schemas/v1/manifest.json`: generated schema artifact digests; regenerate with `dev/export_schemas.py`.

Each package owns a manifest and lockfile. Consumers import the package's public root, not `models` internals. Release packaging uses normal declared wheel dependencies; local uv path sources are only development resolution. Scientific applicability, permission, durable acceptance and execution are outside these DTOs. See [Contract Architecture](../docs/Architecture/System/Contract_Architecture.md).

BP-02 adds independently packaged [command encoding](commands/README.md), [runtime wire contracts](runtime/README.md) and [artifact wire contracts](artifacts/README.md). The generated manifest owns current schema counts and hashes. No live persistence authority is implied by schema validity.

BP-03.01 adds separate tool release descriptor, immutable lock, registration payload/receipt and independent eligibility-observation roots. Existing invocation/completion/descriptor roots stay unchanged. Canonical metadata and transport examples are split into `fixtures/v1/tool_releases.json` and `tool_release_messages.json`; registry-owned policy and persistence remain outside this package.

`schemas/v2/manifest.json` owns the new executable definition, plan/lock and activation-path schema digests. `dev/export_schemas.py` publishes/checks both bundles without rewriting wire-v1 identities.
