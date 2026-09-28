# Contract Packages

Independent Python packages expose public imports, versioned wire schemas and language-neutral fixtures. This directory is navigation, not a shared business-service module.

- [Core](core/README.md): immutable identity, scope, schema and artifact references.
- [Tools](tools/README.md): tool identity, ports, descriptor and invocation/completion protocol.
- [Campaigns](campaigns/README.md): initial structured graph definition language.
- `fixtures/v1/wire_cases.json`: shared positive/negative interchange fixtures.
- `schemas/v1/manifest.json`: generated schema artifact digests; regenerate with `dev/export_schemas.py`.

Each package owns a manifest and lockfile. Consumers import the package's public root, not `models` internals. Release packaging uses normal declared wheel dependencies; local uv path sources are only development resolution. Scientific applicability, permission, durable acceptance and execution are outside these DTOs. See [Contract Architecture](../docs/Architecture/System/Contract_Architecture.md).

BP-02.01 adds independently packaged [command encoding](commands/README.md), [runtime wire contracts](runtime/README.md) and [artifact wire contracts](artifacts/README.md). Publication now contains 52 input/output schemas. Existing 18 schema hashes are unchanged. No live persistence authority is implied.
